# VMware Workstation/Fusion walkthrough

This walkthrough takes you from a fresh `pip install osimager` to an AlmaLinux 10.2 VM built with VMware Workstation (Linux/Windows) or VMware Fusion (macOS) on your own machine. Packer drives VMware through its `vmware-iso` builder. Afterwards the VM stays registered (`keep_registered`), and its files are in `<vms_path>/vmware/<name>/`. The default setup uses Packer's own address discovery, so it needs nothing from your network. A bridged variant is shown for VMs with a fixed LAN address.

The example builds `alma-10.2-x86_64`, which downloads its ISO from `repo.almalinux.org`, so you don't need to fetch anything by hand. The Alma spec inherits from the `rhel` spec, which lists `vmware` in its supported `platforms`.

## 1. Prerequisites

Install these on the machine that runs `mkosimage`:

| Requirement | Why |
|-------------|-----|
| VMware Workstation or VMware Fusion | Packer's `vmware-iso` builder drives it. |
| A desktop session, or the headless override below | The platform sets `headless: false`, so VMware opens a console window during the build. |
| Packer | OSImager generates a Packer build and runs `packer build`. |
| `mkisofs` on `PATH` | OSImager checks for exactly this name before every build that puts files on a CD (`cd_files`), as this one does. Packer uses it to put the kickstart file on a CD labelled `OEMDRV`. |

Check that the tools are present:

```bash
command -v vmrun packer mkisofs
```

Install the Packer plugins. `--init-plugins` installs the plugin named by every platform file's `plugin` key, plus the Ansible provisioner. For VMware that is `github.com/hashicorp/vmware`:

```bash
mkosimage --init-plugins
```

If you only want the two plugins this walkthrough needs:

```bash
packer plugins install github.com/hashicorp/vmware
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

VMware Workstation/Fusion needs no platform credentials. The Alma build reads one secret path, `images/linux`, with two keys:

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
  "platforms": ["vmware"],
  "defs": {
    "domain": "lab.example.com",
    "cidr": "192.168.1.0/24",
    "gateway": "192.168.1.1",
    "dns": {
      "servers": ["192.168.1.1"]
    },
    "ntp": {
      "servers": ["pool.ntp.org"]
    },
    "vms_path": "/vms"
  }
}
```

| Field | What it does |
|-------|--------------|
| `platforms` | Platforms this location can be used with. A target whose platform is not listed fails with `location lab does not support platform <platform>`. List several (`["vmware", "virtualbox", "qemu"]`) to share one location. |
| `defs.domain` | Appended to the VM name to form its FQDN: `myvm` → `myvm.lab.example.com`. The kickstart sets this as the hostname. |
| `defs.cidr` | Derives `subnet`, `prefix` and `netmask`. The netmask is used when the VM gets a static IP. |
| `defs.gateway` | Gateway for a static IP. If omitted, it is calculated from `cidr` as the second-to-last address in the subnet. |
| `defs.dns.servers` | `dns1`, `dns2`, … The kickstart uses `dns1` as the nameserver for a static IP. OSImager also queries these servers for the VM's FQDN when you don't give an IP (see below). |
| `defs.ntp.servers` | Expanded into `ntp1`, `ntp2`, … The Alma kickstart doesn't use them. Other specs (Debian, Ubuntu, SLES) do. |
| `defs.vms_path` | Base output directory. The VM goes to `<vms_path>/vmware/<name>/`. A relative path is taken relative to your home directory. |

**How the VM gets its address.** The common `ssh` spec sets Packer's `ssh_host` for VMware to `{{ .Host }}`, meaning Packer finds the guest's IP itself. The VM uses DHCP on the VMware network Packer gives it. That is how the example above works.

This changes if OSImager is given an address. That happens when you pass an IP on the command line, or when the VM's FQDN resolves through `dns.servers`. Then the kickstart configures that IP statically, and `ssh_host` becomes that IP. The VM must then be on a network where that address is valid and reachable from the host, which in practice means bridged.

### Bridged / headless variant

```json
{
  "platforms": ["vmware"],
  "defs": {
    "domain": "lab.example.com",
    "cidr": "192.168.1.0/24",
    "gateway": "192.168.1.1",
    "dns": {
      "servers": ["192.168.1.1"]
    },
    "ntp": {
      "servers": ["pool.ntp.org"]
    },
    "vms_path": "/vms"
  },
  "platform_specific": [
    {
      "platform": "vmware",
      "config": {
        "headless": true,
        "network": "bridged"
      }
    }
  ]
}
```

| Field | What it does |
|-------|--------------|
| `platform_specific[].platform` | Applies the block only when building for `vmware`. |
| `platform_specific[].config.headless` | Overrides the platform's `headless: false`, so no console window opens. Use it on a host without a desktop. |
| `platform_specific[].config.network` | Passed to Packer's `vmware-iso` builder: the VMware network type for the VM's NIC. `bridged` puts it on the host's LAN. |

Anything under `config` goes into the Packer builder as is, so any other `vmware-iso` option can be set here the same way.

With a bridged NIC, pass a free IP on your LAN:

```bash
mkosimage vmware/lab/alma-10.2-x86_64 myvm 192.168.1.52
```

Otherwise, give the FQDN an A record in the location's DNS servers.

## 5. Build

```bash
mkosimage vmware/lab/alma-10.2-x86_64 myvm
```

What happens:

1. OSImager merges `platforms/vmware.json`, your `lab` location and the `alma` → `rhel` → `linux` → `ssh` spec chain into one set of defs, then loads `images/linux` from your secrets.
2. Before running Packer, it checks that `packer` and `mkisofs` are on `PATH`. Unless the ISO is already in `iso_path`, it sends a HEAD request to the ISO URL, and stops if the result is a 404. It then generates `ks.cfg` from `files/rhel/kickstart_10.cfg` and the other kickstart parts into a temporary directory.
3. It writes the Packer build JSON to `<tmpdir>/myvm.json`, activates the Ansible 2.18 venv, prints the `packer build ...` command and runs it.
4. Packer downloads the ISO to `/iso/AlmaLinux-10.2-x86_64-dvd.iso`. On later builds OSImager finds it there and uses the local copy. Packer then creates the VM `myvm` with these settings:
    - guest type `rhel9-64` and EFI firmware
    - 8 vCPUs (2 sockets × 4 cores) and 4096 MB RAM
    - a 16384 MB SCSI disk on a `pvscsi` controller
    - a `vmxnet3` NIC

    These are the `rhel` 10.x defaults. The spec sets `cpu_sockets` to 2 for VMware only. Packer then attaches `ks.cfg` on an `OEMDRV` CD and boots. After 45 seconds it types the EFI boot command, which adds `inst.ks=hd:LABEL=OEMDRV:/ks.cfg`.
5. Anaconda installs unattended and reboots. Packer logs in over SSH as `root` (timeout 45 minutes) and runs the Ansible playbook `config.yml` against the VM. Packer then runs `/sbin/shutdown -P now`.
6. The temporary directory is removed, unless you passed `-k` or `-m DIR`.

Output: `/vms/vmware/myvm/`, containing `myvm.vmx` and the disk. The platform sets `skip_export` and `skip_compaction`, so no OVF is produced and the disk is not compacted.

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
mkosimage vmware/lab/alma-latest-x86_64 myvm
# alma-latest-x86_64 -> alma-10.2-x86_64
```

**Never download.** `--local` builds only from an ISO already in `iso_path`. With a `latest` target it picks the newest version that is present. If no version is present, it stops with `no local ISO found for any version of alma-latest-x86_64`.

```bash
mkosimage --local vmware/lab/alma-10.2-x86_64 myvm
mkosimage --local vmware/lab/alma-latest-x86_64 myvm
```

**Preview without building:**

```bash
mkosimage -u vmware/lab/alma-10.2-x86_64 myvm   # Packer build JSON
mkosimage -x vmware/lab/alma-10.2-x86_64 myvm   # resolved defs
mkosimage -n vmware/lab/alma-10.2-x86_64 myvm   # everything up to, not including, packer build
```

In the `-u` output of the default example, check `"ssh_host": "{{ .Host }}"`. If it shows an address instead, the FQDN resolved in DNS (see section 4). `-u` and `-x` don't check for `packer` or `mkisofs`. Those checks only run on a real build or `-n`.

To change sizing for one build: `-D cpu_sockets=1,memory=8192,boot_disk_size=40960`. With `cpu_sockets=1` that gives 4 vCPUs. To replace an existing output directory: `-f`.

## 6. Check it worked

```bash
ls /vms/vmware/myvm/
vmrun -T ws start /vms/vmware/myvm/myvm.vmx nogui      # Workstation
vmrun -T fusion start /vms/vmware/myvm/myvm.vmx nogui  # Fusion
vmrun list
```

You can also open `myvm.vmx` in the Workstation/Fusion GUI.

To log in, use `ssh root@<address>`. In the bridged variant the address is the IP you passed. With the default DHCP setup, read the address from the VM console (`ip addr`). The Alma 10 kickstart doesn't install VMware Tools (`open-vm-tools` isn't in its package list), so VMware's guest IP query has nothing to report.

## 7. Troubleshooting

| Symptom | Cause and fix |
|---------|---------------|
| `error: 'mkisofs' not found in PATH` | Install a package that provides a `mkisofs` command. OSImager checks for that exact name. |
| `error: 'packer' not found in PATH` | Install Packer, then run `mkosimage --init-plugins`. If Packer is somewhere else, run `mkosimage --set packer_cmd=/path/to/packer`. |
| `error: post-install requires Ansible 2.18` / `Create the venv with: mkvenv 2.18` | Run `mkvenv 2.18`, or build with `--skip`. |
| `error: Secrets file not found!` followed by `error: Your configuration uses secret references but credential_source 'config' is not configured.` | Create `~/.config/osimager/secrets` with an `images/linux` line (section 3). |
| `Error: location lab does not support platform vmware` | Add `"vmware"` to the location's `platforms`. |
| `error: ISO URL returned 404 (not found): ...` | The ISO has moved upstream. Pick another version from `mkosimage -a`. |
| Build fails to start the VM on a host without a display | The platform sets `headless: false`. Set `"headless": true` in a `vmware` `platform_specific` `config` block (bridged/headless variant above). |
| Packer waits for SSH until the 45-minute timeout | Check `ssh_host` with `-u`. If it is an IP (passed, or the FQDN's DNS record), the VM has that IP statically, and its NIC must be on a network where that address works, e.g. `"network": "bridged"`. Otherwise, use a name without a DNS record and no IP argument, so Packer discovers the DHCP address. |
| `no local ISO found for any version of alma-latest-x86_64` | You used `--local` with a `latest` target and no Alma ISO is in `iso_path` or the Packer cache. Drop `--local` to download. |
