# Walkthroughs

Each walkthrough takes you from a fresh install to a built VM or image on one platform: what to install, which credentials to add, a complete location file, the build command, how to check the result, and what usually goes wrong.

| Where the VM runs | Walkthrough | Installs from |
|-------------------|-------------|---------------|
| Your machine, KVM | [QEMU/KVM](qemu.md) | ISO |
| Your machine | [VirtualBox](virtualbox.md) | ISO |
| Your machine | [VMware Workstation/Fusion](vmware.md) | ISO |
| A Proxmox VE node | [Proxmox VE](proxmox.md) | ISO |
| vCenter or ESXi | [vSphere/ESXi](vsphere.md) | ISO |
| AWS | [AWS](aws.md) | Base AMI |
| Azure | [Azure](azure.md) | Marketplace image |
| Google Cloud | [GCP](gcp.md) | Public image |

## What every walkthrough has in common

**The target.** A build is always `mkosimage PLATFORM/LOCATION/SPEC [NAME] [IP]`:

- `PLATFORM` is the builder: `qemu`, `virtualbox`, `vmware`, `proxmox`, `vsphere`, `aws`, `azure`, `gcp`.
- `LOCATION` is a file you write in `~/.config/osimager/locations/`. It describes one environment: network, DNS, and the platform-specific settings such as which Proxmox node or vSphere datastore to use.
- `SPEC` is `<dist>-<version>-<arch>`, for example `alma-10.2-x86_64`, or `<dist>-latest-<arch>` for the newest version the specs provide.

**Global settings** live in `~/.config/osimager/config.json` and are set with `mkosimage --set KEY=VALUE`. The ones that matter for a first build are `credential_source` (`vault` or `config`) and, for the hypervisor platforms, `iso_path`, the directory on your machine that holds installer ISOs. `iso_path` is never set in a location.

**Credentials** come from HashiCorp Vault or from the local `secrets` file, depending on `credential_source`. See [Credential Setup](../configuration/credential-setup.md); each walkthrough lists the exact keys its platform reads.

**Previewing.** Before building for real, `mkosimage -u PLATFORM/LOCATION/SPEC` prints the complete Packer configuration and `mkosimage -n ...` generates everything and prints the `packer build` command without running it. All options are in the [CLI Reference](../reference/cli-reference.md).
