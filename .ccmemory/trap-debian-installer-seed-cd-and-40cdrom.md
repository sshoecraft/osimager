---
name: trap-debian-installer-seed-cd-and-40cdrom
description: Debian d-i: early_command must mount the seed CD by label itself; the 40cdrom replacement must keep base-installer's /target/media/cdrom bind + apt c…
metadata:
  type: project
tags: [debian, preseed, d-i, apt-cdrom]
---

Debian preseed builds (debian.seed / debian_12.seed / debian_pre10.seed + debian.fix) — how the pieces fit, verified against the Debian 13.1 installer (apt-setup 0.198, base-installer 1.226):

- file-preseed.postinst runs `preseed preseed/file` then `preseed_command preseed/early_command` back to back. The seed comes from /media (mounted by a timed boot_command keystroke after ~50s); that keystroke can lose the race on a slow host. So early_command must not assume /media — it mounts the `cd_label` CD by label (blkid | grep LABEL=) itself. Never `|| true` the copy: a silent miss shows up much later as "apt configuration problem" or a DVD prompt, and the build just sits there (25-minute "slow" parallel builds were really both parked at that dialog).
- base-installer library.sh configure_apt(): bind-mounts /cdrom -> /target/media/cdrom, writes /target/etc/apt/apt.conf.d/00CDMountPoint and 00NoMountCDROM (NoMount, AutoDetect false), runs apt-cdrom add.
- Stock generators/40cdrom on a real CD drive REMOVES 00NoMountCDROM, unmounts /target/media/cdrom* and /cdrom, then lets apt-cdrom find a drive itself — with the seed CD as a second drive (sr1) this is what fails.
- debian.fix installs itself as post-base-installer.d/10debian-fix and replaces 40cdrom. The replacement has to rebuild configure_apt's state (bind + both conf files), not just sed sources.list, or pkgsel/tasksel asks for the DVD.
- finish-install 90base-installer removes 00NoMountCDROM at the end; 10apt-cdrom-setup keeps cdrom entries for a real CD.
- To read the real installer scripts: extract /install.amd/initrd.gz from the DVD ISO (xorriso -osirrox on -extract), and pool/main/a/apt-setup/*.udeb, pool/main/b/base-installer/*.udeb (dpkg-deb -x).
