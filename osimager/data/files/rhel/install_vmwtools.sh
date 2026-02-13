# Install vmware tools, if found on an attached CD
install_vmw_tools() {
    set -x
    done=0
    for d in cdrom sr0 sr1 sr2 sr3 hda hdb hdc hdd
    do
        if test -e /dev/$d; then
            mount /dev/$d /mnt || continue
            ls /mnt/
            arc=$(ls /mnt/VMwareTools* 2>/dev/null)
            if test -n "$arc"; then
                cd /tmp
                tar -zxf $arc
                cd vmware-tools-distrib && ./vmware-install.pl -f -d
                done=1
            fi
            umount /mnt
        fi
        test $done -eq 1 && break
    done
}
install_vmw_tools > /root/tools.log 2>&1

