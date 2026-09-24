"""
Proxmox post-build script.

Renames the VM from the temporary build_id (packer-<uuid>) to the actual name.
Uses the Proxmox API.
"""

import json
import urllib.request
import urllib.parse
import ssl


def proxmox_api(base_url, method, path, headers, ctx, data=None):
    """Make a Proxmox API call and return the parsed response data."""
    if data:
        data = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(f"{base_url}{path}", data=data, headers=headers, method=method)
    resp = urllib.request.urlopen(req, context=ctx)
    return json.loads(resp.read()).get("data")


def run(osimager):
    node = osimager.defs.get("proxmox_node")
    build_id = osimager.build_id
    vm_name = osimager.defs.get("name")
    location_name = osimager.defs.get("location_name")

    # Get credentials from secrets (already resolved)
    server = osimager.get_secret(f"proxmox/{location_name}:server")
    username = osimager.get_secret(f"proxmox/{location_name}:username")
    password = osimager.get_secret(f"proxmox/{location_name}:password")

    if not all([node, build_id, server]):
        print("proxmox_post_build: missing node, build_id, or server -- skipping")
        return

    base_url = f"https://{server}:8006/api2/json"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # Authenticate
    try:
        auth = proxmox_api(base_url, "POST", "/access/ticket", {}, ctx,
                           {"username": username, "password": password})
        ticket = auth["ticket"]
        csrf = auth["CSRFPreventionToken"]
    except Exception as e:
        print(f"proxmox_post_build: authentication failed: {e}")
        return

    headers = {
        "Cookie": f"PVEAuthCookie={ticket}",
        "CSRFPreventionToken": csrf
    }

    # Find VM by build_id (unique temp name)
    try:
        vms = proxmox_api(base_url, "GET", f"/nodes/{node}/qemu", headers, ctx)
    except Exception as e:
        print(f"proxmox_post_build: failed to list VMs: {e}")
        return

    vmid = None
    for vm in vms:
        if vm.get("name") == build_id:
            vmid = vm["vmid"]
            break

    if vmid is None:
        print(f"proxmox_post_build: VM '{build_id}' not found on node {node}")
        return

    # Rename VM to actual name
    try:
        proxmox_api(base_url, "PUT", f"/nodes/{node}/qemu/{vmid}/config", headers, ctx,
                    {"name": vm_name})
        print(f"proxmox_post_build: VM {vmid} renamed to '{vm_name}'")
    except Exception as e:
        print(f"proxmox_post_build: failed to rename VM {vmid}: {e}")
        return

    print(f"proxmox_post_build: done")
