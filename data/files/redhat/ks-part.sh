#
# Simple kickstart partitioning script
#

# uncomment this to provide a log during build
#exec > /tmp/ks-part.log 2>&1
#set -x

# You can tailor thse in your kickstart_pre
test -z "$ROOTFSTYPE" && ROOTFSTYPE=ext4
test -z "$ROOTSIZE" && ROOTSIZE=1
test -z "$ROOTGROW" && ROOTGROW=1
# Set to 0 for dynamic sizing based on memory size
test -z "$SWAPSIZE" && SWAPSIZE=0
test -z "$SWAPMAX" && SWAPMAX=4096
test -z "$BOOTFSTYPE" && BOOTFSTYPE=ext3
test -z "$BOOTSIZE" && BOOTSIZE=512
test -z "$EFISIZE" && EFISIZE=256
if grep Msft /proc/scsi/scsi >/dev/null 2>&1; then
    depmod > /dev/null 2>&1
    modprobe hv_storvsc
    sleep 5
    cd /sys/class/scsi_host
    for host in *
    do
        echo "Scanning /sys/class/scsi_host/${host}" > /root/hv.log 2>&1
        echo "- - -" > /sys/class/scsi_host/${host}/scan
    done
    sleep 15
fi
if [ -e /dev/vda ]; then
DRIVE=vda
elif [ -e /dev/sda ]; then
DRIVE=sda
elif [ -e /dev/hda ]; then
DRIVE=hda
elif [ -e /dev/md126 ]; then
DRIVE=md126
elif test -e /dev/nvme0n1; then
DRIVE=nvme0n1
else
echo "UNABLE TO FIND A SUITABLE DRIVE TO INSTALL ONTO!"
touch /tmp/ks-part.cfg
exit 1
fi

# Get the size of the selected disk
SECTORS=$(cat /sys/block/$DRIVE/size 2>/dev/null)
# XXX lol?
test -z "$SECTORS" && SECTORS=25165824
DISKSIZE=$((($SECTORS*512)/1048576))

# Dynamic swapsize calculation based on memory size
if test $SWAPSIZE -eq 0; then
    MEMSIZE=$(cat /proc/meminfo | grep ^MemTotal | while read a b c; do echo $b; done)
    calc_swap() {
        num=$(($(($MEMSIZE/1024))/4))
        test $num -eq 0 && num=1
        ORIG=$num
        A=$num
        C=1
        while [ $A -ne 1 ]; do A=$((A>>1)) C=$((C<<1)); done
        SWAPSIZE=$C
        NEXT=$((C<<1))
        DIFF1=$((ORIG-C))
        DIFF2=$((NEXT-ORIG))
        test "$DIFF1" -ge "$DIFF2" && SWAPSIZE=$NEXT
    }
    calc_swap
    while true
    do
        TOTAL=$(($ROOTSIZE+SWAPSIZE+BOOTSIZE+256))
        if test $TOTAL -gt $DISKSIZE; then
            SWAPSIZE=$((SWAPSIZE>>1))
            if test $SWAPSIZE -eq 0; then
                ROOTSIZE=$(($ROOTSIZE - 1024))
                calc_swap
            fi
        else
            break
        fi
    done
    test $SWAPSIZE -gt $SWAPMAX && SWAPSIZE=$SWAPMAX
fi
echo $ROOTSIZE $SWAPSIZE $BOOTSIZE > /tmp/sizes.txt

# Create the partitions (LVM,vgroot)
cat >/tmp/ks-part.cfg <<END_OF_PARTS_1
clearpart --drives=$DRIVE --all
zerombr
bootloader --location=mbr --driveorder=$DRIVE
END_OF_PARTS_1
# for large sector drives biosboot needs be below this
if test $DISKSIZE -gt 2096128; then
    echo part biosboot --fstype=biosboot --size=1 >> /tmp/ks-part.cfg
fi
cat >>/tmp/ks-part.cfg <<END_OF_PARTS_2
part /boot --ondisk $DRIVE --fstype $BOOTFSTYPE --size $BOOTSIZE
END_OF_PARTS_2
# EFI
if test -d /sys/firmware/efi; then
    echo "part /boot/efi --ondisk $DRIVE --fstype=efi --size=$EFISIZE" >> /tmp/ks-part.cfg
fi
cat >>/tmp/ks-part.cfg <<END_OF_PARTS_3
part pv.01 --ondisk $DRIVE --size 1 --grow
volgroup vgroot pv.01
END_OF_PARTS_3
test $ROOTGROW -eq 1 && ROOTGROWOPT="--grow"
echo "logvol / --vgname vgroot --fstype $ROOTFSTYPE --size $ROOTSIZE --name root $ROOTGROWOPT" >> /tmp/ks-part.cfg
echo "logvol swap --vgname vgroot --fstype swap --size $SWAPSIZE --name swap" >> /tmp/ks-part.cfg

cat /tmp/ks-part.cfg

