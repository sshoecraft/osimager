# Getting Started

A quickstart walkthrough for building your first OS image with OSImager and VirtualBox.

**Prerequisites:** OSImager installed (`pip install osimager`), Packer, and mkisofs. See [Installation](installation.md) for details.

---

## Step 1: Create a Location

A location defines your build environment: network settings, DNS, NTP, and where VMs live on disk. (Where ISOs live is the global `iso_path` setting, see Step 4.)

Copy the quickstart template into your user config directory:

```bash
mkdir -p ~/.config/osimager/locations
cp "$(python3 -c "import osimager, os; print(os.path.join(os.path.dirname(osimager.__file__), 'data', 'examples', 'quickstart-location.toml'))")" \
   ~/.config/osimager/locations/local.toml
```

Edit `~/.config/osimager/locations/local.toml` to match your network:

```toml
platforms = ["virtualbox"]

[defs]
domain = "home.local"
gateway = "192.168.1.1"
cidr = "192.168.1.0/24"
vms_path = "/vms"

[defs.dns]
servers = ["192.168.1.1"]

[defs.ntp]
servers = ["pool.ntp.org"]
```

Field reference:

| Field | Description |
|-------|-------------|
| `platforms` | Hypervisors this location supports. Must match a platform name OSImager knows about (e.g. `virtualbox`, `vmware`, `vsphere`, `proxmox`). |
| `domain` | DNS domain suffix appended to hostnames to form FQDNs (e.g. `myvm.home.local`). |
| `gateway` | Default network gateway for built VMs. |
| `cidr` | Network CIDR. OSImager derives the subnet, prefix length, and netmask from this automatically. |
| `vms_path` | Directory where built VM images are stored. |
| `dns.servers` | List of DNS servers injected into kickstart/preseed/autoinst configs. |
| `ntp.servers` | List of NTP servers for time synchronization during and after install. |

---

## Step 2: Set Up Credentials

OS image builds need credentials for SSH access during the build and for setting the root/admin password in the installed OS.

Switch to local secrets mode:

```bash
mkosimage --set credential_source=config
```

Create `~/.config/osimager/secrets` with your credentials:

```
images/linux username=root password=YourPassword
images/windows username=Administrator password=YourPassword
```

The `images/linux` path is referenced by Linux spec files. During the build, OSImager uses these credentials for SSH access to the VM and injects them into kickstart/preseed templates to set the root password. The `images/windows` path works the same way for Windows builds via WinRM and Autounattend.xml.

For HashiCorp Vault integration instead of local secrets, see [Credential Setup](configuration/credential-setup.md).

---

## Step 3: Install Packer Plugins

```bash
mkosimage --init-plugins
```

This installs the Ansible provisioner plugin and all platform builder plugins (VirtualBox, VMware, vSphere, etc.). Plugins are read from each platform's configuration file.

---

## Step 4: List Available Specs

```bash
mkosimage --list
```

This prints every spec OSImager knows about, in version order. A `(*)` means the ISO is already in your `iso_path`:

```
Available specs:
  alma-9.6-x86_64
  alma-9.7-x86_64 (*)
  alma-9.8-x86_64
  alma-10.2-x86_64
  ...
```

To see only what you can build right now, use `-a`. Each line shows where the ISO comes from: a local path if it's present, otherwise the URL it would be downloaded from. `--local` shows just the ones already present.

```
  alma-9.7-x86_64                /iso/AlmaLinux-9.7-x86_64-dvd.iso
  alma-9.8-x86_64                https://repo.almalinux.org/almalinux/9.8/isos/x86_64/AlmaLinux-9.8-x86_64-dvd.iso
  ...
```

To see only the newest version of each dist, use `--latest`. It lists each `<dist>-latest-<arch>` target and the spec it currently resolves to:

```
Latest specs:
  alma-latest-x86_64                 alma-10.2-x86_64
  debian-latest-x86_64               debian-13.7-x86_64
  ...
```

You don't need to download ISOs by hand. When a spec's ISO entry is a URL, the build downloads the ISO into `iso_path` and reuses it from there on later builds. `iso_path` defaults to `/iso`; point it at a directory you can write to:

```bash
mkosimage --set iso_path=$HOME/iso
```

A few specs have no public download: their ISO entry is a local `file://` path, and `-a` lists them only once the ISO is present. For those, obtain the ISO and place it in `iso_path` yourself.

---

## Step 5: Build an Image

```bash
mkosimage virtualbox/local/alma-10.2-x86_64
```

The target format is `platform/location/spec`. OSImager:

1. Loads the `virtualbox` platform config (builder type, VM settings).
2. Loads the `local` location config (network, paths, DNS, NTP).
3. Loads the `alma-10.2-x86_64` spec (ISO, kickstart template, provisioners).
4. Merges all three into a unified defs dictionary.
5. Generates a kickstart file from the spec template with the merged values.
6. Produces a Packer build JSON and executes `packer build`.

To build the newest version of a dist without looking up its number, use the `latest` alias in place of the version:

```bash
mkosimage virtualbox/local/alma-latest-x86_64
```

The alias resolves to the highest version the spec provides for that architecture, and it does so before anything else runs. The build, the default instance name and the logs all use the real version (`alma-10.2-x86_64`). The alias is only as current as the spec, so a new upstream release needs a spec update before `latest` picks it up. With `--local` (or `local_only` set), `latest` means the newest version whose ISO is already in `iso_path`. If no version is local, the build stops with an error.

To give the VM a name:

```bash
mkosimage virtualbox/local/alma-10.2-x86_64 myvm
```

A third argument sets a static IP (`mkosimage virtualbox/local/alma-10.2-x86_64 myvm 192.168.1.100`), and a name whose FQDN resolves through `dns.servers` gets its DNS address the same way. With the VirtualBox NAT networking this quickstart uses, Packer then tries to reach that LAN address and can't, so leave the IP out and use a name with no DNS record. For a VM on your LAN, use the bridged setup in the [VirtualBox walkthrough](walkthroughs/virtualbox.md).

---

## Step 6: Explore

Inspect what OSImager will do before committing to a full build:

```bash
# Dry run -- shows the Packer command without executing it
mkosimage -n virtualbox/local/alma-10.2-x86_64

# Dump the resolved defs dictionary -- see all merged variables
mkosimage -x virtualbox/local/alma-10.2-x86_64

# Dump the Packer build JSON -- see exactly what gets sent to Packer
mkosimage -u virtualbox/local/alma-10.2-x86_64
```

These are useful for debugging location or spec issues, and for understanding how platform + location + spec configs merge together.

---

## Next Steps

- [Walkthroughs](walkthroughs/index.md) -- complete setups for QEMU, VirtualBox, VMware, Proxmox, vSphere, AWS, Azure and GCP
- [Location Setup](configuration/location-setup.md) -- multi-platform locations, vSphere/Proxmox network configs
- [Credential Setup](configuration/credential-setup.md) -- HashiCorp Vault integration
- [Platform Reference](reference/platform-reference.md) -- all 11 supported platforms and their options
- [Spec Reference](reference/spec-reference.md) -- spec file format, version ranges, template substitution
- [Supported Operating Systems](reference/supported-os.md) -- full list of distributions and versions
