"""
QEMU post-build script.

Generates a libvirt XML domain definition and registers the VM with virsh.
"""

import os
import shutil
import subprocess


def run(osimager):
    if not shutil.which('virsh'):
        if osimager.verbose:
            print("virsh not found, skipping libvirt VM registration")
        return

    name = osimager.defs.get('name', '')
    output_dir = osimager.config.get('output_directory', '')
    disk_path = os.path.join(output_dir, name)
    memory_mb = osimager.defs.get('memory', 2048)
    sockets = osimager.defs.get('cpu_sockets', 1)
    cores = osimager.defs.get('cpu_cores', 2)
    net_bridge = osimager.config.get('net_bridge', '')
    arch = osimager.defs.get('arch', 'x86_64')
    machine = 'pc' if arch == 'x86_64' else 'virt'

    # Build network interface XML
    if net_bridge:
        net_xml = f"""    <interface type='bridge'>
      <source bridge='{net_bridge}'/>
      <model type='virtio'/>
    </interface>"""
    else:
        net_xml = """    <interface type='user'>
      <model type='virtio'/>
    </interface>"""

    xml = f"""<domain type='kvm'>
  <name>{name}</name>
  <memory unit='MiB'>{memory_mb}</memory>
  <vcpu placement='static'>{int(sockets) * int(cores)}</vcpu>
  <cpu mode='host-passthrough'/>
  <os>
    <type arch='{arch}' machine='{machine}'>hvm</type>
    <boot dev='hd'/>
  </os>
  <devices>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2'/>
      <source file='{disk_path}'/>
      <target dev='vda' bus='virtio'/>
    </disk>
    <graphics type='vnc' port='-1' autoport='yes' listen='0.0.0.0'/>
{net_xml}
    <serial type='pty'/>
    <console type='pty'/>
  </devices>
</domain>
"""
    xml_path = os.path.join(output_dir, name + '.xml')
    with open(xml_path, 'w') as f:
        f.write(xml)

    # Resolve which libvirt instance to register the VM in. virsh is otherwise
    # called bare, which silently falls to libvirt's uid default and lands
    # unprivileged builds under qemu:///session. Precedence:
    #   1. libvirt_uri from defs (-D / spec / location / qemu.json platform default)
    #   2. LIBVIRT_DEFAULT_URI env var (fallback when unconfigured)
    #   3. uid default: root -> qemu:///system, otherwise qemu:///session
    uri = (str(osimager.defs.get('libvirt_uri', '')).strip()
           or os.environ.get('LIBVIRT_DEFAULT_URI', '').strip()
           or ('qemu:///system' if os.geteuid() == 0 else 'qemu:///session'))
    virsh = ['virsh', '--connect', uri]

    try:
        subprocess.run(virsh + ['undefine', name], capture_output=True, text=True)
        result = subprocess.run(virsh + ['define', xml_path], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"libvirt: VM '{name}' defined ({uri})")
        else:
            print(f"libvirt: failed to define VM: {result.stderr.strip()}")
    except Exception as e:
        print(f"libvirt: error: {e}")
