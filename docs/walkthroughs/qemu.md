# QEMU/KVM walkthrough

This walkthrough takes you from a fresh `pip install osimager` to an AlmaLinux 10.2 VM built with QEMU/KVM on your own machine. Packer runs QEMU directly, headless, with the VM's NIC on a Linux bridge on your LAN. The result is a qcow2 disk under `<vms_path>/qemu/<name>/`. If `virsh` is installed, the VM is also registered with libvirt so you can start it with `virsh start`.

The example builds `alma-10.2-x86_64`, which downloads its ISO from `repo.almalinux.org`, so you don't need to fetch anything by hand. The Alma spec inherits from the `rhel` spec, which lists `qemu` in its supported `platforms`.

## 1. Prerequisites

Install these on the machine that runs `mkosimage`:

| Requirement | Why |
|-------------|-----|
| QEMU (`qemu-system-x86_64`) | Packer's `qemu` builder runs it. |
| Write access to `/dev/kvm` | The platform picks `accelerator: kvm` and `cpu_model: host` only when `/dev/kvm` is writable by you. Otherwise it falls back to `accelerator: none` and `cpu_model: max` (software emulation, which is very slow). On most distributions this means being in the `kvm` group. |
| Packer | OSImager generates a Packer build and runs `packer build`. |
| `mkisofs` on `PATH` | OSImager checks for exactly this name before every build that puts files on a CD (`cd_files`), as this one does. Packer uses it to put the kickstart file on a CD labelled `OEMDRV`. |
| A Linux bridge (e.g. `br0`) | Packer must reach the VM over SSH at its own address (see [Location file](#4-location-file)). QEMU's bridge helper only attaches to bridges allowed in `/etc/qemu/bridge.conf`, e.g. a line `allow br0`. |
| `virsh` (libvirt client), optional | The qemu platform's `post_build` hook (`scripts/qemu_post_build.py`) registers the finished VM with libvirt. Without `virsh` on `PATH` it skips registration and the disk is still built. |

Check that the tools are present:

```bash
command -v qemu-system-x86_64 packer mkisofs virsh
ls -l /dev/kvm
```

Install the Packer plugins. `--init-plugins` installs the plugin named by every platform file's `plugin` key, plus the Ansible provisioner. For QEMU that is `github.com/hashicorp/qemu`:

```bash
mkosimage --init-plugins
```

If you only want the two plugins this walkthrough needs:

```bash
packer plugins install github.com/hashicorp/qemu
packer plugins install github.com/hashicorp/ansible
```

Create the Ansible venv for post-install configuration. Alma 10.x uses `ansible_version` `2.18` from the `rhel` spec. `ansible.json` says that needs `ansible-core` and Python 3.11 or newer:

```bash
mkvenv 2.18
```

`mkvenv` with no arguments shows which venvs the specs need and which are installed. `mkvenv --all` creates every one of them, including the old Python 2.7 ones, which need a Python 2.7 interpreter. To build without post-install configuration, skip the venv and pass `--skip` to `mkosimage`.

## 2. Global settings

Two settings matter here. Both are saved to `~/.config/osimager/config.json`.

```bash
mkosimage --set iso_path=/iso
mkosimage --set credential_source=config
```

- `iso_path` is a directory on this machine, and it is only a global setting. A location that sets it gets a warning (`warning: location <name> sets iso_path, which is ignored; ...`) and the value is ignored. Packer downloads the ISO into this directory (`iso_target_path` is `<iso_path>/<iso name>`), so it must exist and be writable by you:

    ```bash
    sudo mkdir -p /iso && sudo chown "$USER" /iso
    ```

- `credential_source` defaults to `vault`. `config` reads the local secrets file described next.

Check the result with `mkosimage --show-config`.

## 3. Credentials

QEMU needs no platform credentials. The Alma build reads one secret path, `images/linux`, with two keys:

| Reference | Where | Used for |
|-----------|-------|----------|
| `{{vault `images/linux` `username`}}` | `specs/linux/spec.json` → `ssh-username` | Packer's SSH login |
| `{{vault `images/linux` `password`}}` | `specs/linux/spec.json` → `ssh-password` | Packer's SSH login |
| `6>images/linux:password<6` | `files/rhel/kickstart_10.cfg` → `rootpw --iscrypted` | Root password in the installed system (SHA-512 hash) |

The kickstart sets only the root password, and its `%post` enables `PermitRootLogin yes`, so `username` must be `root`.

**Secrets file** (`credential_source=config`). Create `~/.config/osimager/secrets`:

```
images/linux username=root password=<password>
```

The format is one entry per line: a path, then `key=value` pairs separated by spaces. That means the password cannot contain a space. Lines starting with `#` are comments.

**Vault** (`credential_source=vault`). Use a KV v2 mount named `images`:

```bash
mkosimage --set credential_source=vault
mkosimage --set vault_addr=http://vault.example.com:8200 --set vault_token=<token>
vault secrets enable -path=images -version=2 kv
vault kv put images/linux username=root password=<password>
```

## 4. Location file

Create `~/.config/osimager/locations/lab.json`. The file name (`lab`) is the location name in the build target. A `.toml` file works too, and if both exist the JSON one wins.

```json
{
  "platforms": ["qemu"],
  "defs": {
    "domain": "lab.example.com",
    "cidr": "192.168.1.0/24",
    "gateway": "192.168.1.1",
    "dns": {
      "servers": ["192.168.1.1"],
      "search": ["lab.example.com"]
    },
    "ntp": {
      "servers": ["pool.ntp.org"]
    },
    "vms_path": "/vms"
  },
  "platform_specific": [
    {
      "platform": "qemu",
      "defs": {
        "libvirt_uri": "qemu:///system"
      },
      "config": {
        "net_bridge": "br0"
      }
    }
  ]
}
```

| Field | What it does |
|-------|--------------|
| `platforms` | Platforms this location can be used with. A target whose platform is not listed fails with `location lab does not support platform <platform>`. List several (`["qemu", "virtualbox", "vmware"]`) to share one location. |
| `defs.domain` | Appended to the VM name to form its FQDN: `myvm` → `myvm.lab.example.com`. The kickstart sets this as the hostname. |
| `defs.cidr` | Derives `subnet`, `prefix` and `netmask`. The netmask is used when the VM gets a static IP. |
| `defs.gateway` | Gateway for a static IP. If omitted, it is calculated from `cidr` as the second-to-last address in the subnet. |
| `defs.dns.servers` | `dns1`, `dns2`, … The kickstart uses `dns1` as the nameserver for a static IP. OSImager also queries these servers for the VM's FQDN when you don't give an IP (see below). |
| `defs.dns.search` | Joined into `dns_search`. It also sets the search list for that FQDN lookup. |
| `defs.ntp.servers` | Expanded into `ntp1`, `ntp2`, … The Alma kickstart doesn't use them. Other specs (Debian, Ubuntu, SLES) do. |
| `defs.vms_path` | Base output directory. The VM goes to `<vms_path>/qemu/<name>/`. A relative path is taken relative to your home directory. |
| `platform_specific[].platform` | Applies the block only when building for `qemu`. |
| `platform_specific[].defs.libvirt_uri` | Which libvirt instance the `post_build` hook registers the VM in. If it is empty (the platform default), the hook uses `LIBVIRT_DEFAULT_URI`, or else `qemu:///system` when running as root and `qemu:///session` otherwise. |
| `platform_specific[].config.net_bridge` | Passed to Packer's qemu builder. Puts the VM's NIC on this host bridge instead of QEMU user-mode networking. When it is set and you haven't written your own `qemuargs`, OSImager generates `-netdev bridge,...,br=<bridge>` and a `virtio-net` device with a random `52:54:00:xx:xx:xx` MAC for each build. The libvirt XML also attaches the VM to this bridge. |

**How the VM gets its address.** The common `ssh` spec sets Packer's `ssh_host` for qemu to the IP you give on the command line. If you give none, it uses the VM's FQDN. The kickstart chooses the network mode the same way:

- **IP on the command line** (`mkosimage qemu/lab/alma-10.2-x86_64 myvm 192.168.1.50`). The VM gets that static IP, with `netmask`, `gateway` and `dns1` from the location, and Packer connects to it.
- **No IP, and the FQDN resolves** through `dns.servers`. That address is used exactly as if you had passed it.
- **No IP, and the FQDN doesn't resolve.** The VM uses DHCP, and Packer connects to the FQDN. This only works if your DHCP server registers the hostname in DNS.

The simplest route is to pass a free IP on your bridge's subnet.

## 5. Build

```bash
mkosimage qemu/lab/alma-10.2-x86_64 myvm 192.168.1.50
```

What happens:

1. OSImager merges `platforms/qemu.json`, your `lab` location and the `alma` → `rhel` → `linux` → `ssh` spec chain into one set of defs, then loads `images/linux` from your secrets.
2. Before running Packer, it checks that `packer` and `mkisofs` are on `PATH`. Unless the ISO is already in `iso_path`, it sends a HEAD request to the ISO URL, and stops if the result is a 404. It then generates `ks.cfg` from `files/rhel/kickstart_10.cfg` and the other kickstart parts into a temporary directory.
3. It writes the Packer build JSON to `<tmpdir>/myvm.json`, activates the Ansible 2.18 venv, prints the `packer build ...` command and runs it.
4. Packer downloads the ISO to `/iso/AlmaLinux-10.2-x86_64-dvd.iso`. On later builds OSImager finds it there and uses the local copy. Packer then creates a 16384 MB qcow2 disk with 1 socket × 4 cores and 4096 MB RAM (the `rhel` 10.x defaults), attaches `ks.cfg` on an `OEMDRV` CD and boots. The qemu platform pins `firmware` to `bios`, so the spec's BIOS boot command is typed: `inst.ks=hd:LABEL=OEMDRV:/ks.cfg ...`.
5. Anaconda installs unattended and reboots. Packer logs in over SSH as `root` (timeout 45 minutes) and runs the Ansible playbook `config.yml` against the VM. Packer then runs `/sbin/shutdown -P now`.
6. If Packer succeeds, the `post_build` hook writes `/vms/qemu/myvm/myvm.xml` and runs `virsh --connect <uri> define` on it. It prints `libvirt: VM 'myvm' defined (qemu:///system)`.
7. The temporary directory is removed, unless you passed `-k` or `-m DIR`.

Output: `/vms/qemu/myvm/myvm` (qcow2 disk, no extension) and `/vms/qemu/myvm/myvm.xml`.

**Picking a version.** List what can be built right now:

```bash
mkosimage -a --arch x86_64 | grep alma
```

On a machine with no ISOs yet, only the versions with a download URL appear:

```
  alma-8.10-x86_64               https://repo.almalinux.org/almalinux/8.10/isos/x86_64/AlmaLinux-8.10-x86_64-dvd.iso
  alma-9.7-x86_64                https://vault.almalinux.org/9.7/isos/x86_64/AlmaLinux-9.7-x86_64-dvd.iso
  alma-9.8-x86_64                https://repo.almalinux.org/almalinux/9.8/isos/x86_64/AlmaLinux-9.8-x86_64-dvd.iso
  alma-10.1-x86_64               https://vault.almalinux.org/10.1/isos/x86_64/AlmaLinux-10.1-x86_64-dvd.iso
  alma-10.2-x86_64               https://repo.almalinux.org/almalinux/10.2/isos/x86_64/AlmaLinux-10.2-x86_64-dvd.iso
```

Other Alma versions are `file://` specs. They appear (with a local path) only once you've put their ISO in `iso_path`.

**Newest version.** Use `alma-latest-x86_64` instead of a version. OSImager prints the resolution and uses the real name from then on, including the default VM name:

```bash
mkosimage qemu/lab/alma-latest-x86_64 myvm 192.168.1.50
# alma-latest-x86_64 -> alma-10.2-x86_64
```

**Never download.** `--local` builds only from an ISO already in `iso_path`. With a `latest` target it picks the newest version that is present. If no version is present, it stops with `no local ISO found for any version of alma-latest-x86_64`.

```bash
mkosimage --local qemu/lab/alma-10.2-x86_64 myvm 192.168.1.50
mkosimage --local qemu/lab/alma-latest-x86_64 myvm 192.168.1.50
```

**Preview without building:**

```bash
mkosimage -u qemu/lab/alma-10.2-x86_64 myvm 192.168.1.50   # Packer build JSON
mkosimage -x qemu/lab/alma-10.2-x86_64 myvm 192.168.1.50   # resolved defs
mkosimage -n qemu/lab/alma-10.2-x86_64 myvm 192.168.1.50   # everything up to, not including, packer build
```

In the `-u` output, check `"accelerator": "kvm"`, `"net_bridge": "br0"`, `"ssh_host": "192.168.1.50"` and the generated `qemuargs`. The line `warning: removing empty value for: firmware` is expected: the platform's `firmware` key is empty and is dropped. `-u` and `-x` don't check for `packer` or `mkisofs`. Those checks only run on a real build or `-n`.

To change sizing for one build: `-D memory=8192,cpu_cores=8,boot_disk_size=40960`. To replace an existing output directory: `-f`.

## 6. Check it worked

With libvirt registration:

```bash
virsh --connect qemu:///system list --all
virsh --connect qemu:///system start myvm
ssh root@192.168.1.50
```

The generated domain uses machine type `pc`, `host-passthrough` CPU and a virtio disk, has VNC graphics on an auto-assigned port listening on `0.0.0.0`, and puts its NIC on `br0`. If you built as a normal user without `libvirt_uri`, the VM is under `qemu:///session` instead. Use `virsh --connect qemu:///session list --all`.

Without libvirt, check the disk:

```bash
qemu-img info /vms/qemu/myvm/myvm
```

## 7. Troubleshooting

| Symptom | Cause and fix |
|---------|---------------|
| `error: 'mkisofs' not found in PATH` | Install a package that provides a `mkisofs` command. OSImager checks for that exact name. |
| `error: 'packer' not found in PATH` | Install Packer, then run `mkosimage --init-plugins`. If Packer is somewhere else, run `mkosimage --set packer_cmd=/path/to/packer`. |
| `error: post-install requires Ansible 2.18` / `Create the venv with: mkvenv 2.18` | Run `mkvenv 2.18`, or build with `--skip`. |
| `error: Secrets file not found!` followed by `error: Your configuration uses secret references but credential_source 'config' is not configured.` | Create `~/.config/osimager/secrets` with an `images/linux` line (section 3). |
| `Error: location lab does not support platform qemu` | Add `"qemu"` to the location's `platforms`. |
| `error: ISO URL returned 404 (not found): ...` | The ISO has moved upstream. Pick another version from `mkosimage -a`. |
| Install is extremely slow; `-u` shows `"accelerator": "none"`, `"cpu_model": "max"` | `/dev/kvm` isn't writable by you, so QEMU runs without KVM. Add yourself to the group that owns `/dev/kvm` (usually `kvm`) and log in again. |
| Packer waits for SSH until the 45-minute timeout | Packer is connecting to `ssh_host`. Check it with `-u`. Without an IP argument it is the FQDN, which must resolve to the VM. Pass an IP instead. QEMU user-mode networking (no `net_bridge`) isn't reachable at the VM's own address, so keep `net_bridge` set. |
| QEMU fails to start with a bridge helper / `bridge.conf` access error | Allow the bridge in `/etc/qemu/bridge.conf` (`allow br0`). |
| Packer connects to an old IP from a previous build | OSImager gives every bridged build a new random MAC so Packer's address discovery can't match a stale ARP entry. It only does this when the build has no `qemuargs`. If you set `qemuargs` yourself, you must supply the network device and MAC too. |
| `libvirt: failed to define VM: ...` | Check that `libvirt_uri` points at the libvirt instance you can use. Under `qemu:///system`, libvirt's QEMU user must be able to read the disk under `vms_path`. |
| No VM in `virsh list --all` | `virsh` was not on `PATH` at build time (run with `-v` to see `virsh not found, skipping libvirt VM registration`). Or the VM went to the other URI: compare `qemu:///session` and `qemu:///system`. Registration only runs if Packer succeeded. |
| `no local ISO found for any version of alma-latest-x86_64` | You used `--local` with a `latest` target and no Alma ISO is in `iso_path` or the Packer cache. Drop `--local` to download. |
