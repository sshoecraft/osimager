
"lab" network configuration

I do this step so all of the vms can talk to each other and to the outside world.  This is done using a tap interface the machines connect to which is bridged to a bridge interface (must be called vbnet because vmnet cant be used with vmware): 

virtualbox can use vbnet ... the tapthat program opens the tap connection which places the br0 UP with CARRIER ... making all this work

MUST make then sudo make install for this to work

/etc/network/interfaces.d/br0: (or just place in /etc/network/interfaces)

```
auto br0
iface br0 inet static
	# Remove or change to 1500 if your network doesnt support jumbo frames
	mtu 9000
	pre-up ip tuntap add dev vbnet mode tap user root
	pre-up ip link set dev vbnet up
	pre-up ip link set dev vbnet mtu 9000
	pre-down ip link del dev vbnet
	bridge_ports vbnet
	address 192.168.120.1
	netmask 255.255.255.0
	bridge_stp off
	bridge_maxwait 0
```

Type make install to build & install tapthat into /usr/local/sbin.  It will also copy the systemctl service file to /etc/systemd/system and reload

I also run dnsmasq for the subnet but ONLY listen on the bridge

/etc/dnsmasq.d/lab.conf:

```
log-dhcp
log-queries
log-facility=/var/log/dnsmasq.log
server=192.168.120.1
interface=br0
bind-interfaces
no-dhcp-interface=eth0 lo
server=192.168.1.1
expand-hosts
domain-needed
domain=vm.localdomain
local=/vm.localdomain/
dhcp-range=192.168.120.100,192.168.120.200,3h
dhcp-option=option:router,192.168.120.1
dhcp-authoritative
dhcp-leasefile=/var/lib/misc/dnsmasq-lab.leases
# If you want to setup a PXE server you can do that here
#enable-tftp=br0
#tftp-root=/pxeimage
#dhcp-boot=pxelinux.0,boothost,192.168.120.1
```

On systems running systemd-resolved (Ubuntu 20.04+), you need to tell resolved to route the lab domain queries to dnsmasq. Create a networkd config for br0:

/etc/systemd/network/10-br0.network:

```
[Match]
Name=br0

[Network]
DNS=192.168.120.1
Domains=vm.localdomain
KeepConfiguration=yes
```

Then restart networkd:

	systemctl restart systemd-networkd

This tells systemd-resolved to send any `vm.localdomain` queries to dnsmasq on 192.168.120.1, so the host can resolve lab VM hostnames.

dnsmasq also automatically registers hostnames from DHCP leases in its DNS, so any VM that gets an IP via DHCP and sends a hostname will be resolvable without a manual entry. The /etc/hosts entries below are only needed for VMs with static IPs:

```
192.168.120.1   vmgate.vm.localdomain vmgate
192.168.120.2   adserver.vm.localdomain adserver
192.168.120.3   esxhost.vm.localdomain esxhost
192.168.120.4   vcenter.vm.localdomain vcenter

192.168.120.22  alma-9.vm.localdomain alma-9
192.168.120.19  rhel-6.vm.localdomain rhel-6
192.168.120.23  rhel-7.vm.localdomain rhel-7
192.168.120.24  rhel-8.vm.localdomain rhel-8
192.168.120.25  rhel-9.vm.localdomain rhel-9
192.168.120.37  ubuntu-18.vm.localdomain ubuntu-18
192.168.120.26  ubuntu-20.vm.localdomain ubuntu-20
192.168.120.27  ubuntu-22.vm.localdomain ubuntu-22
192.168.120.28  debian-11.vm.localdomain debian-11
192.168.120.29  debian-12.vm.localdomain debian-12
192.168.120.30  windows-12.vm.localdomain windows-12
192.168.120.31  windows-16.vm.localdomain windows-16
192.168.120.32  windows-19.vm.localdomain windows-19
192.168.120.33  windows-22.vm.localdomain windows-22
192.168.120.35  sles-12.vm.localdomain sles-12
192.168.120.36  sles-15.vm.localdomain sles-15
192.168.120.37  esxi-6.vm.localdomain esxi-6
192.168.120.38  esxi-7.vm.localdomain esxi-7
192.168.120.39  esxi-8.vm.localdomain esxi-8
```

## Internet Access for the Lab Network

The 192.168.120.0/24 subnet is not directly routable from your LAN. For VMs on the lab network to reach the internet, you need one of:

- **Static route on your gateway/router**: Add a route for 192.168.120.0/24 pointing to the host's LAN IP (e.g. 192.168.1.x). This is the cleanest approach.
- **IP masquerading on the host**: If you can't modify your router, set up iptables NAT on the host to masquerade traffic from 192.168.120.0/24 out the physical NIC.

Without one of these, VMs will be able to talk to each other and the host but won't have internet access.



## QEMU/KVM Setup

Install QEMU and libvirt:

```
sudo apt install qemu-system-x86 qemu-utils libvirt-daemon-system libvirt-clients
```

For hardware-accelerated builds, add your user to the `kvm` group:

```
sudo usermod -aG kvm $USER
```

Log out and back in for the group change to take effect. Without this, QEMU falls back to software emulation (`accelerator: none`) which is significantly slower.

### Networking

QEMU uses the `qemu-bridge-helper` to attach VMs to the lab bridge. Two things are needed:

1. Allow br0 in the bridge helper config:

```
sudo mkdir -p /etc/qemu
echo "allow br0" | sudo tee /etc/qemu/bridge.conf
```

2. Set the setuid bit on the bridge helper so non-root users can create tap interfaces:

```
sudo chmod u+s /usr/lib/qemu/qemu-bridge-helper
```

Then in your location config (`~/.config/osimager/locations/lab.json`), add a qemu platform_specific entry:

```json
{
  "platform": "qemu",
  "config": {
    "net_bridge": "br0"
  }
}
```

This tells Packer's QEMU builder to use bridged networking via br0 instead of the default user-mode (NAT) networking. The VM will get a DHCP address from dnsmasq on the 192.168.120.0/24 subnet, just like VirtualBox and VMware VMs.


## VMware Workstation Networking


VMware Workstation needs a vmnet configured on the 192.168.120.0/24 lab subnet so VMs can reach br0 and each other.

We do this by marking vbnet tap interface created above as a bridge, and "soft-creating" vmnet2 as a vbnet bridge

edit `/etc/vmware/networking` and add these lines to define vmnet2 plus the bridge mapping at the end:

```
... after the VNET_1 lines ...

answer VNET_2_DHCP no
answer VNET_2_MTU 9000
answer VNET_2_VIRTUAL_ADAPTER no

... after the VNET_8 lines ...

answer VNL_DEFAULT_BRIDGE_VNET -1
add_bridge_mapping <your primary network interface here> 0
add_bridge_mapping vbnet 2
```

If you're network doesnt support jumbo frames remove the MTU 9000 line.

This bridges vmnet2 directly to the `vbnet` tap interface with no DHCP and no virtual adapter. dnsmasq on br0 handles DHCP and hands out the correct default route (192.168.120.1).

VMs configured on vmnet2 will be on the 192.168.120.0/24 lab subnet.

NOTE: If you are running VMware Workstation as a non-root user, the `/dev/vmnet*` device nodes must be world read/write:

```
chmod 666 /dev/vmnet*
```

VMware creates these device nodes directly, bypassing udev, so a udev rule won't work. Create a systemd service to set permissions after VMware starts:

/etc/systemd/system/vmnet-permissions.service:

```
[Unit]
Description=Set vmnet device permissions
After=vmware.service
Requires=vmware.service

[Service]
Type=oneshot
ExecStart=/bin/bash -c "chmod 666 /dev/vmnet*"

[Install]
WantedBy=multi-user.target
```

Then enable it:

	systemctl daemon-reload
	systemctl enable vmnet-permissions.service



## Infra servers

IMPORTANT:  The core infra runs on a VMware Workstation instance installed on the local (debian/ubuntu) host
            I'm running workstation 17.6.2 ... but really any version which supports 2022 and ESXi 8.02 should work

To build the adserver:

	make adserver

Once the adserver is up, you'll need to enable the AD feature and create your domain (TODO: automate lab domain)
Note: The "lab" location in locations uses the adserver as DNS (for domain join) it needs to be running for the other builds to work

To build the esxhost (if you want a vsphere env):

	make esxhost

NOTE: Any VM in VMware Workstation that needs to be on the lab network must have its network adapter set to "Custom: Specific virtual network" and select `/dev/vmnet2`.

Once the host is up you can import vcenter into workstation ... use the OVA.  If you want to deploy on the nested ESXi server you can use the installer.

