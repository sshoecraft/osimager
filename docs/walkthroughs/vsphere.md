# vSphere / ESXi walkthrough

This page takes you from a fresh `pip install osimager` to an AlmaLinux 10.2 VM installed on VMware ESXi, either a standalone host or a host managed by vCenter. OSImager drives Packer's `vsphere-iso` builder through the vSphere API: the VM is created on the host or cluster you name, its disk lives on a datastore, the installer runs unattended from a kickstart, Ansible configures the result, and the VM is left powered off under the name you gave it. It is not converted to a template.

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

- **The Packer plugins.** This installs the Ansible provisioner plugin plus the plugin each platform file names (for vSphere, `github.com/hashicorp/vsphere`):

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

- **Disk space in `iso_path`** for the installer ISO (about the size of a DVD), because on vSphere the build machine downloads it (step 5).
- **Network access** to the vCenter or ESXi API (HTTPS), to the ESXi host for the datastore upload, and to the VM network over SSH.

### On the vSphere side

- **A login** for vCenter (e.g. `administrator@vsphere.local`) or for the ESXi host directly (e.g. `root`). It must be able to create and configure VMs, upload files to the datastores, and power VMs on and off. TLS verification is off (`insecure_connection: true`), so self-signed certificates are fine.
- **A datastore for the VM** (`datastore`).
- **A datastore for ISOs** (`remote_cache_datastore`, optional). Packer uploads the installer ISO here. Without it the plugin uses its own default.
- **A port group** for the VM (`vm_network`, default `VM Network`). The VM gets one `vmxnet3` NIC on it.
- **DHCP and DNS on that network.** The kickstart uses DHCP unless the VM's name resolves (see step 5).
- **The VMware Tools ISO on the host.** `vsphere.json` attaches `[] /vmimages/tools-isoimages/linux.iso` from the ESXi host's own filesystem as a second CD.

## 2. Global settings

Two settings matter here. Both are global, saved in `~/.config/osimager/config.json`:

```bash
mkosimage --set credential_source=config --set iso_path=/iso
```

- `credential_source=config` reads secrets from the local file `~/.config/osimager/secrets`. Use `vault` instead if you keep them in HashiCorp Vault (step 3).
- `iso_path` is the directory **on the build machine** where ISOs live. Packer downloads the installer ISO to `<iso_path>/<file>`, and an ISO already there is used without downloading. `iso_path` is global only: a location that sets it gets this warning and the value is ignored:

    ```
    warning: location esx sets iso_path, which is ignored; iso_path is a global setting (mkosimage --set iso_path=...)
    ```

`--set` writes the file permanently. Run `mkosimage --show-config` to see what is in effect.

## 3. Credentials

A vSphere build needs two secret entries:

| Path | Keys | Used for |
|------|------|----------|
| `images/linux` | `username`, `password` | SSH login during the build, and the root password written into the kickstart (`rootpw --iscrypted`, hashed from `password`) |
| `vsphere/<location>` | `server`, `username`, `password` | The vSphere API: `server` is the vCenter or ESXi host name |

`<location>` is the location name from the build target, so `vsphere/esx/...` reads `vsphere/esx`.

With `credential_source=config`, add them to `~/.config/osimager/secrets`, one path per line:

```
images/linux username=root password=<password>

# standalone ESXi host
vsphere/esx server=esx1.example.com username=root password=<password>

# vCenter
vsphere/vc server=vcenter.example.com username=administrator@vsphere.local password=<password>
```

Values are split on whitespace, so a password cannot contain spaces.

With `credential_source=vault`, store the same keys in KV v2 mounts named `images` and `vsphere`:

```bash
vault kv put images/linux username=root password=<password>
vault kv put vsphere/esx server=esx1.example.com username=root password=<password>
```

See [Credential Setup](../configuration/credential-setup.md) for the Vault settings.

## 4. Location file

### Standalone ESXi host

Create `~/.config/osimager/locations/esx.json`. The file name is the location name used in the build target.

```json
{
  "platforms": ["vsphere"],
  "defs": {
    "domain": "lab.example.com",
    "cidr": "192.168.20.0/24",
    "gateway": "192.168.20.1",
    "dns": {
      "servers": ["192.168.20.1"],
      "search": ["lab.example.com"]
    },
    "ntp": {
      "servers": ["192.168.20.1"]
    }
  },
  "platform_specific": [
    {
      "platform": "vsphere",
      "defs": {
        "datacenter": "ha-datacenter",
        "esxi_host": "esx1.example.com",
        "datastore": "datastore1",
        "folder": "",
        "vm_network": "VM Network",
        "thin_disk": "true"
      },
      "config": {
        "remote_cache_datastore": "iso"
      }
    }
  ]
}
```

A standalone host has a single datacenter, `ha-datacenter`, and no cluster or folders.

### Host managed by vCenter

Create `~/.config/osimager/locations/vc.json`:

```json
{
  "platforms": ["vsphere"],
  "defs": {
    "domain": "lab.example.com",
    "cidr": "192.168.20.0/24",
    "gateway": "192.168.20.1",
    "dns": {
      "servers": ["192.168.20.1"],
      "search": ["lab.example.com"]
    },
    "ntp": {
      "servers": ["192.168.20.1"]
    }
  },
  "platform_specific": [
    {
      "platform": "vsphere",
      "defs": {
        "datacenter": "dc1",
        "cluster": "cluster1",
        "datastore": "datastore1",
        "folder": "osimager",
        "vm_network": "VM Network"
      },
      "config": {
        "remote_cache_datastore": "iso",
        "remote_cache_path": "isos"
      }
    }
  ]
}
```

Add `esxi_host` as well to pin the VM to one host in the cluster.

### Fields

| Field | Where | What it does |
|-------|-------|--------------|
| `platforms` | top level | Platforms this location may be used with. A target whose platform is not listed fails with `Error: location esx does not support platform <name>`. |
| `domain` | `defs` | Appended to the VM name to form its FQDN (`myvm.lab.example.com`), which is set as the hostname in the kickstart. |
| `cidr` | `defs` | The VM network. OSImager derives `subnet`, `prefix` and `netmask` from it; the netmask is used when the VM gets a static IP. |
| `gateway` | `defs` | Gateway for a static IP. If omitted, it is computed as the second-to-last address of `cidr`. |
| `dns.servers` | `defs` | Used to look up the VM's FQDN before the build (step 5). The first server is also the static-IP nameserver in the kickstart. |
| `dns.search`, `ntp.servers` | `defs` | Become the `dns_search` and `ntp1`, `ntp2`, ... defs for the installer and Ansible. |
| `datacenter` | `platform_specific` defs | The builder's `datacenter`. |
| `esxi_host` | `platform_specific` defs | The builder's `host`: the ESXi host the VM is created on. |
| `cluster` | `platform_specific` defs | The builder's `cluster`. Leave it out for a standalone host. |
| `datastore` | `platform_specific` defs | Datastore for the VM's files and disk. |
| `folder` | `platform_specific` defs | VM folder in vCenter. Empty or absent for a standalone host. |
| `vm_network` | `platform_specific` defs | Port group for the NIC. Defaults to `VM Network`. |
| `thin_disk` | `platform_specific` defs | Optional. `"true"` for a thin-provisioned disk. Defaults to `false` (thick), from `vsphere.json`. |
| `remote_cache_datastore` | `platform_specific` config | Datastore the installer ISO is uploaded to. |
| `remote_cache_path` | `platform_specific` config | Directory on that datastore. Defaults to `packer_cache/`. |

Keys under `defs` feed the `>>name<<` references in `vsphere.json`. Keys under `config` are copied into the Packer builder as they are. A def you leave out or set to `""` (here `cluster` and `folder` for the standalone host) is dropped from the builder with a harmless warning such as `warning: removing empty value for: cluster`.

## 5. Build

Check what will be built before running anything. `-u` prints the complete Packer JSON with the secrets filled in and exits:

```bash
mkosimage -u vsphere/esx/alma-10.2-x86_64 myvm
```

Then build:

```bash
mkosimage vsphere/esx/alma-10.2-x86_64 myvm
```

`myvm` is the VM name. Leave it out and the VM is named after the spec (`alma-10.2-x86_64`). You can add a third argument, a static IP: `mkosimage vsphere/esx/alma-10.2-x86_64 myvm 192.168.20.50`.

### What happens

1. **Resolve.** OSImager merges the platform, the location and the spec chain (`alma` → `rhel` → `linux` → `ssh`) into one Packer build. The `rhel` spec lists `vsphere` among its platforms and sets the guest OS type to `rhel9_64Guest`. The VM gets 4 vCPUs, 4096 MB of memory, EFI firmware, a `pvscsi` controller and a 16384 MB disk.
2. **Look up the VM's address.** OSImager resolves `myvm.lab.example.com` against the location's DNS servers. If it resolves, or you passed an IP, the kickstart configures that address statically and Packer connects to it. Otherwise the kickstart uses DHCP.
3. **Check the ISO URL.** A HEAD request to the AlmaLinux download URL; a 404 stops the build here. Skipped when the ISO is already in `iso_path`.
4. **Generate the answer file.** The kickstart is written to a temporary directory as `ks.cfg`.
5. **Get the installer ISO onto a datastore.** The ESXi host never downloads anything.
    - If `AlmaLinux-10.2-x86_64-dvd.iso` is already in `iso_path`, or you passed `--local`, Packer uses that file. Otherwise Packer downloads it from the URL to `<iso_path>/AlmaLinux-10.2-x86_64-dvd.iso` on the build machine.
    - Packer then uploads it to `[<remote_cache_datastore>] <remote_cache_path>/AlmaLinux-10.2-x86_64-dvd.iso` (`[iso] packer_cache/AlmaLinux-10.2-x86_64-dvd.iso` with the standalone example). If a file is already at that datastore path, the upload is skipped, so only the first build of a version pays for it.
6. **Build the kickstart CD.** Packer runs `mkisofs` to make a CD labelled `OEMDRV` containing `ks.cfg` and attaches it to the VM.
7. **Create the VM** named `myvm` on the host or cluster, in `datastore`, with a `vmxnet3` NIC on `vm_network`. Attached CDs: the installer ISO, the kickstart CD, and `[] /vmimages/tools-isoimages/linux.iso`.
8. **Type the boot command.** After 45 seconds Packer edits the installer's GRUB entry, appends `inst.ks=hd:LABEL=OEMDRV:/ks.cfg inst.stage2=cdrom inst.geoloc=0 net.ifnames=0 biosdevname=0` and boots it with Ctrl-X.
9. **Install.** Anaconda reads the kickstart from the CD, installs the system, sets the root password from `images/linux`, enables root SSH login with a password, and reboots.
10. **SSH.** With a static IP Packer connects to that IP. Without one, no `ssh_host` is set and the builder uses the IP address the guest reports to vSphere through VMware Tools. Packer waits up to 45 minutes for SSH.
11. **Ansible.** Packer runs `config.yml` with the spec's `specs/rhel/config_9.yml`, from the Ansible 2.18 venv. `--skip` leaves this out.
12. **Shut down.** Packer runs `/sbin/shutdown -P now` over SSH, waits for the VM to power off, and removes the CD-ROM drives (`remove_cdrom: true`). `convert_to_template` is `false`, so the result stays a VM. There is no post-build hook for vSphere.

!!! tip "Avoiding the download and the upload"
    The two copies in step 5 are both skipped when the ISO is already where each step looks. If the ISO datastore is an NFS export that the build machine also mounts, the file Packer uploads lands on the build machine's side of that export as well, at `<mount>/<remote_cache_path>/<file>`. What matters is the exact path: the upload is skipped only when the file exists at `[<remote_cache_datastore>] <remote_cache_path>/<file>`, and the download only when it exists at `<iso_path>/<file>`.

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
mkosimage vsphere/esx/alma-latest-x86_64 myvm
```

```
alma-latest-x86_64 -> alma-10.2-x86_64
```

### Building only from ISOs you already have

`--local` never downloads. Packer's `iso_url` becomes the local file, `<iso_path>/<file>`, which it still uploads to the datastore unless it is already there.

```bash
mkosimage --local vsphere/esx/alma-10.2-x86_64 myvm
mkosimage --local vsphere/esx/alma-latest-x86_64 myvm
```

With `alma-latest-x86_64`, `--local` picks the newest version whose ISO is present on the build machine.

### Previewing

```bash
mkosimage -u vsphere/esx/alma-10.2-x86_64 myvm   # Packer build JSON
mkosimage -x vsphere/esx/alma-10.2-x86_64 myvm   # every resolved def
mkosimage -n vsphere/esx/alma-10.2-x86_64 myvm   # generate everything, print the packer command, don't run it
```

In the `-u` output, check `datacenter`, `host` or `cluster`, `datastore`, `remote_cache_datastore`, `iso_url` and `iso_target_path`, `disk_thin_provisioned` (`false` unless the location sets `thin_disk`), and that the three `vsphere-*` variables hold your server and login. `warning: removing empty value for: ssh_host` is expected when the VM has no static IP, as are the same warnings for `cluster`/`folder` (standalone host) or `host` (vCenter without `esxi_host`).

## 6. Check it worked

In the vSphere Client (or the ESXi host client) the VM `myvm` is in datacenter `ha-datacenter` (or your vCenter datacenter and `folder`), stored on `datastore1`, powered off. The installer ISO stays on the ISO datastore for the next build.

## 7. Troubleshooting

**`warning: secret not found: vsphere/esx/server`** (and `username`, `password`)

There is no `vsphere/esx` entry in the secrets file, or its key names differ. The path must be `vsphere/<location name>`.

**`error: Secrets file not found!`**

`credential_source` is `config` but `~/.config/osimager/secrets` doesn't exist.

**`Error: location esx does not support platform vsphere`**

The location's `platforms` list doesn't include `vsphere`.

**`Error loading file '.../locations/esx.toml': [Errno 2] No such file or directory`**

No `esx.json` or `esx.toml` in `~/.config/osimager/locations/`. The location part of the target must match the file name.

**`error: ISO URL returned 404 (not found): <url>`**

The download URL in the spec no longer exists. Pick another version from `mkosimage -a`.

**`error: post-install requires Ansible 2.18`**

Run `mkvenv 2.18`, or build with `--skip`.

**The build hangs waiting for the VM's IP address or for SSH**

Without a static IP, the builder learns the VM's address only from VMware Tools running in the guest. Give the VM a DNS record in the location's DNS server, or pass an IP as the third argument, so the kickstart sets that address and Packer connects to it directly.

**Every build uploads the ISO again**

The upload is skipped only when the file already exists at `[<remote_cache_datastore>] <remote_cache_path>/<file>`. If `remote_cache_datastore` is not set, the plugin's default datastore is used; set it to a datastore that keeps the ISOs between builds.
