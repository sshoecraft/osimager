# Proxmox VE walkthrough

This page takes you from a fresh `pip install osimager` to an AlmaLinux 10.2 VM installed on a Proxmox VE node. OSImager drives Packer's `proxmox-iso` builder through the Proxmox API: the VM is created on the node you name, its disk lives in a Proxmox storage pool, the installer runs unattended from a kickstart, Ansible configures the result, and the VM is left on the node under the name you gave it.

## 1. Prerequisites

### On the build machine

The build machine is wherever you run `mkosimage`. It needs:

- **Packer** on `PATH` (or wherever the `packer_cmd` setting points). Without it a build stops with:

    ```
    error: 'packer' not found in PATH
    ```

- **`mkisofs`** on `PATH`. Packer uses it to build the small CD that carries the kickstart. OSImager checks for a command with exactly that name; without it a build stops with:

    ```
    error: 'mkisofs' not found in PATH
    ```

- **The Packer plugins.** This installs the Ansible provisioner plugin plus the plugin each platform file names (for Proxmox, `github.com/hashicorp/proxmox`):

    ```bash
    mkosimage --init-plugins
    ```

- **The Ansible venv the spec needs.** The AlmaLinux 10 specs inherit `ansible_version: 2.18` from the RHEL 10 spec. Create it (or every venv the specs need):

    ```bash
    mkvenv 2.18
    # or
    mkvenv --all
    ```

    If you don't want post-install configuration at all, skip this and add `--skip` to the build command.

- **Network access to the Proxmox API** on port 8006 of the server you put in the secrets (step 3), and SSH access to the VM network, because Packer connects to the new VM over SSH.

### On the Proxmox side

- **An API login.** The platform authenticates with a username and password (`user@realm`, e.g. `root@pam`). It must be allowed to create, configure and start VMs on the node, allocate disks in the VM storage pool, and write ISO images into the ISO storage pool. TLS verification is off (`insecure_skip_tls_verify: true`), so a self-signed node certificate is fine.
- **An ISO storage pool** (`iso_storage_pool`) with content type *ISO image*. Two things land in it: the installer ISO (Proxmox downloads it there itself, see step 5) and the generated kickstart CD, which the plugin uploads.
- **A VM disk storage pool** (`vm_storage_pool`) for the 16 GB boot disk, e.g. `local-lvm`.
- **Bridge `vmbr0`.** `proxmox.json` attaches the VM's single virtio NIC to `vmbr0`. To use another bridge, see the override in step 4.
- **DHCP and DNS on that bridge's network.** The kickstart uses DHCP unless the VM's name resolves (see step 5). The node itself must also be able to reach the ISO download URL, because it is the node that downloads it.

## 2. Global settings

Two settings matter here. Both are global, saved in `~/.config/osimager/config.json`:

```bash
mkosimage --set credential_source=config --set iso_path=/iso
```

- `credential_source=config` reads secrets from the local file `~/.config/osimager/secrets`. Use `vault` instead if you keep them in HashiCorp Vault (step 3).
- `iso_path` is the directory **on the build machine** where ISOs live. It is global only: a location that sets `iso_path` gets this warning and the value is ignored:

    ```
    warning: location pve sets iso_path, which is ignored; iso_path is a global setting (mkosimage --set iso_path=...)
    ```

For Proxmox, `iso_path` is how OSImager decides whether an ISO is "already there" (step 5). That decision is only correct if `iso_path` is the same storage Proxmox uses for the ISO pool, for example an NFS export mounted on the build machine and also configured in Proxmox as the `iso` storage. For a directory or NFS storage, Proxmox keeps ISOs in `<storage path>/template/iso`, so point `iso_path` at that directory. If the two are not shared, leave the default and never use `--local` with Proxmox; every build then has the node download the ISO.

`--set` writes the file permanently. Run `mkosimage --show-config` to see what is in effect.

## 3. Credentials

A Proxmox build needs two secret entries:

| Path | Keys | Used for |
|------|------|----------|
| `images/linux` | `username`, `password` | SSH login during the build, and the root password written into the kickstart (`rootpw --iscrypted`, hashed from `password`) |
| `proxmox/<location>` | `server`, `username`, `password` | The Proxmox API: `https://<server>:8006/api2/json` |

`<location>` is the location name from the build target, so `proxmox/pve/...` reads `proxmox/pve`. The post-build rename (step 5) reads the same three keys.

With `credential_source=config`, add them to `~/.config/osimager/secrets`, one path per line:

```
images/linux username=root password=<password>
proxmox/pve server=pve1.example.com username=root@pam password=<password>
```

Values are split on whitespace, so a password cannot contain spaces.

With `credential_source=vault`, store the same keys in KV v2 mounts named `images` and `proxmox`:

```bash
vault kv put images/linux username=root password=<password>
vault kv put proxmox/pve server=pve1.example.com username=root@pam password=<password>
```

See [Credential Setup](../configuration/credential-setup.md) for the Vault settings.

## 4. Location file

Create `~/.config/osimager/locations/pve.json`. The file name is the location name used in the build target.

```json
{
  "platforms": ["proxmox"],
  "defs": {
    "domain": "lab.example.com",
    "cidr": "192.168.10.0/24",
    "gateway": "192.168.10.1",
    "dns": {
      "servers": ["192.168.10.1"],
      "search": ["lab.example.com"]
    },
    "ntp": {
      "servers": ["192.168.10.1"]
    },
    "proxmox_node": "pve1",
    "iso_storage_pool": "iso",
    "vm_storage_pool": "local-lvm"
  }
}
```

| Field | What it does |
|-------|--------------|
| `platforms` | Platforms this location may be used with. A target whose platform is not listed fails with `Error: location pve does not support platform <name>`. |
| `domain` | Appended to the VM name to form its FQDN (`myvm.lab.example.com`), which is set as the hostname in the kickstart. |
| `cidr` | The VM network. OSImager derives `subnet`, `prefix` and `netmask` from it; the netmask is used when the VM gets a static IP. |
| `gateway` | Gateway for a static IP. If omitted, it is computed as the second-to-last address of `cidr`. |
| `dns.servers` | Used to look up the VM's FQDN before the build (step 5). The first server is also the static-IP nameserver in the kickstart. |
| `dns.search`, `ntp.servers` | Become the `dns_search` and `ntp1`, `ntp2`, ... defs for the installer and Ansible. |
| `proxmox_node` | The Proxmox node the VM is created on (the builder's `node`). Also used by the post-build rename. |
| `iso_storage_pool` | Proxmox storage for the installer ISO and the kickstart CD. |
| `vm_storage_pool` | Proxmox storage for the VM's disk. |

Because this location only serves Proxmox, the Proxmox fields sit directly in `defs`. A location shared by several platforms puts them in a `platform_specific` block instead, as shown in [Location Setup](../configuration/location-setup.md#platform-specific-overrides).

A `platform_specific` block can also carry `config`, which overrides keys in the Packer builder. For example, to attach the VM to `vmbr1` instead of `vmbr0`, add this to the location:

```json
  "platform_specific": [
    {
      "platform": "proxmox",
      "config": {
        "network_adapters": [
          { "model": "virtio", "bridge": "vmbr1", "firewall": false }
        ]
      }
    }
  ]
```

The value replaces the whole `network_adapters` list, so give every field.

## 5. Build

Check what will be built before running anything. `-u` prints the complete Packer JSON with the secrets filled in and exits:

```bash
mkosimage -u proxmox/pve/alma-10.2-x86_64 myvm
```

Then build:

```bash
mkosimage proxmox/pve/alma-10.2-x86_64 myvm
```

`myvm` is the VM name. Leave it out and the VM is named after the spec (`alma-10.2-x86_64`). You can add a third argument, a static IP: `mkosimage proxmox/pve/alma-10.2-x86_64 myvm 192.168.10.50`.

### What happens

1. **Resolve.** OSImager merges the platform, the location and the spec chain (`alma` → `rhel` → `linux` → `ssh`) into one Packer build. The `rhel` spec lists `proxmox` among its platforms; the `linux` spec sets the Proxmox OS type to `l26`. The VM gets 1 socket × 4 cores, 4096 MB of memory and a 16384 MB virtio disk. The Proxmox platform pins firmware to BIOS (`seabios`), whatever the spec asks for.
2. **Look up the VM's address.** OSImager resolves `myvm.lab.example.com` against the location's DNS servers. If it resolves, or you passed an IP, the kickstart configures that address statically and Packer connects to it. Otherwise the kickstart uses DHCP.
3. **Check the ISO URL.** A HEAD request to the AlmaLinux download URL; a 404 stops the build here. Skipped when the ISO is already in `iso_path`.
4. **Generate the answer file.** The kickstart is written to a temporary directory as `ks.cfg`.
5. **Get the installer ISO into Proxmox.** OSImager checks whether `AlmaLinux-10.2-x86_64-dvd.iso` is already in `iso_path` on the build machine.
    - If it is (or you passed `--local`), the boot ISO is the existing Proxmox volume `iso:iso/AlmaLinux-10.2-x86_64-dvd.iso` (`<iso_storage_pool>:iso/<file>`), and nothing is downloaded.
    - If it is not, the boot ISO is the download URL with `iso_download_pve: true`: the Proxmox node downloads the ISO into `iso_storage_pool` itself. The build machine never downloads it.
6. **Build the kickstart CD.** Packer runs `mkisofs` to make a CD labelled `OEMDRV` containing `ks.cfg` and uploads it to `iso_storage_pool`.
7. **Create the VM** on `proxmox_node` with a temporary name, `packer-<12 hex digits>`. The installer ISO is on `ide2`, the kickstart CD on `ide3`, the disk is `virtio0` in `vm_storage_pool`, the NIC is virtio on `vmbr0`, and the QEMU guest agent is enabled.
8. **Type the boot command.** After 10 seconds Packer types, at the installer's boot menu, `inst.ks=hd:LABEL=OEMDRV:/ks.cfg inst.stage2=cdrom inst.geoloc=0 net.ifnames=0 biosdevname=0`.
9. **Install.** Anaconda reads the kickstart from the CD, installs the system (including `qemu-guest-agent`), sets the root password from `images/linux`, enables root SSH login with a password, and reboots.
10. **SSH.** With a static IP Packer connects to that IP. Without one, `ssh_host` is left empty and Packer asks the QEMU guest agent for the VM's address. Packer waits up to 45 minutes for SSH.
11. **Ansible.** Packer runs `config.yml` with the spec's `specs/rhel/config_9.yml`, from the Ansible 2.18 venv. `--skip` leaves this out.
12. **Stop.** OSImager sends no shutdown command for Proxmox (the platform sets `shutcmd: false`); stopping the VM is left to the Proxmox builder. Both CDs are detached (`unmount: true`).
13. **Rename.** After Packer exits successfully, OSImager's Proxmox post-build hook logs in to the API with the `proxmox/pve` secrets, finds the VM named `packer-<id>` on `proxmox_node`, and renames it to `myvm`.

### Picking a version

List what you can build and where each ISO comes from:

```bash
mkosimage -a | grep alma
```

```
  ...
  alma-10.1-x86_64               https://vault.almalinux.org/10.1/isos/x86_64/AlmaLinux-10.1-x86_64-dvd.iso
  alma-10.2-aarch64              https://repo.almalinux.org/almalinux/10.2/isos/aarch64/AlmaLinux-10.2-aarch64-dvd.iso
  alma-10.2-x86_64               https://repo.almalinux.org/almalinux/10.2/isos/x86_64/AlmaLinux-10.2-x86_64-dvd.iso
```

A local path in place of a URL means the ISO is already in `iso_path`.

To always build the newest AlmaLinux the specs know about, use the `latest` target. The resolution is printed first:

```bash
mkosimage proxmox/pve/alma-latest-x86_64 myvm
```

```
alma-latest-x86_64 -> alma-10.2-x86_64
```

### Building only from ISOs you already have

`--local` never downloads: it builds from the ISO that is already present and uses it as `<iso_storage_pool>:iso/<file>`.

```bash
mkosimage --local proxmox/pve/alma-10.2-x86_64 myvm
mkosimage --local proxmox/pve/alma-latest-x86_64 myvm
```

With `alma-latest-x86_64`, `--local` picks the newest version whose ISO is present. "Present" is checked on the build machine, so this only works if `iso_path` is the Proxmox ISO storage, as described in step 2.

### Previewing

```bash
mkosimage -u proxmox/pve/alma-10.2-x86_64 myvm   # Packer build JSON
mkosimage -x proxmox/pve/alma-10.2-x86_64 myvm   # every resolved def
mkosimage -n proxmox/pve/alma-10.2-x86_64 myvm   # generate everything, print the packer command, don't run it
```

In the `-u` output, check `node`, the `boot_iso` block (`iso_url` with `"iso_download_pve": "true"`, or `iso_file`), `storage_pool` under `disks`, and that the three `proxmox-*` variables hold your server and login. The warnings `removing empty value for: efi_config` (BIOS firmware) and `removing empty value for: ssh_host` (no static IP, so the guest agent supplies the address) are expected.

## 6. Check it worked

The build output ends with the post-build hook's lines:

```
proxmox_post_build: VM <vmid> renamed to 'myvm'
proxmox_post_build: done
```

In the Proxmox web UI the VM is listed under node `pve1` as `myvm`, with its disk in `local-lvm`. During the build it appears as `packer-<id>`; that name only remains if the rename step failed (see below).

## 7. Troubleshooting

**`warning: secret not found: proxmox/pve/server`** (and `username`, `password`)

There is no `proxmox/pve` entry in the secrets file, or its key names differ. The path must be `proxmox/<location name>`.

**`error: Secrets file not found!`**

`credential_source` is `config` but `~/.config/osimager/secrets` doesn't exist.

**`Error: location pve does not support platform proxmox`**

The location's `platforms` list doesn't include `proxmox`.

**`Error loading file '.../locations/pve.toml': [Errno 2] No such file or directory`**

No `pve.json` or `pve.toml` in `~/.config/osimager/locations/`. The location part of the target must match the file name.

**`error: ISO URL returned 404 (not found): <url>`**

The download URL in the spec no longer exists. Pick another version from `mkosimage -a`.

**`error: post-install requires Ansible 2.18`**

Run `mkvenv 2.18`, or build with `--skip`.

**The build hangs at "Waiting for SSH to become available"**

Without a static IP, Packer gets the VM's address from the QEMU guest agent. Check that the VM booted the installed system and that `qemu-guest-agent` is running in it; the AlmaLinux kickstart installs it. If the log shows `Using SSH communicator to connect: <no value>`, you are on OSImager older than 1.9.3, which set an unusable `ssh_host` for Proxmox; upgrade. Alternatively give the VM a DNS record in the location's DNS server, or pass an IP as the third argument, so Packer connects to a known address.

**Proxmox reports the ISO volume doesn't exist**

OSImager found the ISO in `iso_path` on the build machine (or you passed `--local`) and told Proxmox to use `<iso_storage_pool>:iso/<file>`, but that storage doesn't have it. This happens when `iso_path` is not the Proxmox ISO storage. Copy the ISO into the Proxmox ISO storage, or remove the local copy so the node downloads it.

**The VM is left named `packer-<id>`**

The rename runs only after Packer succeeds, and prints what went wrong: `proxmox_post_build: authentication failed: ...`, `proxmox_post_build: failed to list VMs: ...`, `proxmox_post_build: VM 'packer-<id>' not found on node pve1` or `proxmox_post_build: failed to rename VM <vmid>: ...`. Rename the VM by hand in the UI if needed.
