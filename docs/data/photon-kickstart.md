# Photon OS — JSON Kickstart Template

New installer template added in Phase 1 of the coverage roadmap. VMware Photon OS uses a
**JSON** kickstart (not the Anaconda text kickstart used by RHEL/Fedora).

## Files
- Template: `files/photon/kickstart.json`
- Spec: `specs/photon/spec.json` (dist `photon`, version `5.0`, x86_64 + aarch64)

## Mechanism
- The Photon installer reads its config from the `ks=` kernel boot parameter.
- osimager places `photon-kickstart.json` on a secondary CD (`cd_label: OEMDRV`, like ESXi) and
  the `boot_command` edits the GRUB kernel line to add
  `ks=cdrom:/photon-kickstart.json photon.media=cdrom insecure_installation=1`.
- ISO: `https://packages.broadcom.com/photon/5.0/GA/iso/photon-5.0-dde71ec57.<arch>.iso`
  (host moved from packages.vmware.com → packages.broadcom.com; build hash `dde71ec57` is the 5.0 GA).

## ks.json schema (key fields)
```
hostname, password{crypted,text}, disk, partitions[], packages[], network{type,...}, postinstall[]
```
- Password uses the sha512 hash marker `6>images/linux:password<6` (Photon `crypted:true`).
- `network.type` switches dhcp/static via an `E>...<E` expression on `>>ip<<`.

## ⚠ Needs build verification
- The exact `ks=cdrom:` path resolution from a SEPARATE OEMDRV CD (vs the boot ISO) is modeled on
  ESXi's behavior and not yet build-tested. If Photon won't read the config from the second CD,
  fall back to serving it via HTTP (`ks=<url>`) or baking it into the boot ISO.
- The GRUB `boot_command` edit sequence is best-effort and may need adjusting to Photon 5.0's menu.

## References
- Downloading: https://github.com/vmware/photon/wiki/Downloading-Photon-OS
- Kickstart: https://github.com/vmware/photon/blob/master/docs/photon_user/kickstart.md
