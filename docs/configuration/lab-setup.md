# Lab Network Setup

This guide covers setting up an isolated lab network on a Linux host so VMs built by OSImager can communicate with each other and the outside world. This works with both VirtualBox and VMware Workstation.

---

## Bridge and Tap Interface

The lab network uses a tap interface (`vbnet`) bridged to `br0` on the 192.168.120.0/24 subnet. The tap must be named `vbnet` because `vmnet` conflicts with VMware.

VirtualBox VMs connect directly to `vbnet`. The `tapthat` utility opens the tap connection and gives br0 carrier.

### Bridge Configuration

Create `/etc/network/interfaces.d/br0` (or add to `/etc/network/interfaces`):

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

If your `/etc/network/interfaces` doesn't already source the `interfaces.d` directory, add:

```
source /etc/network/interfaces.d/*
```

### Building and Installing tapthat

The `tapthat` utility is included in the `setup/` directory of the OSImager source. It opens the tap interface file descriptor, which gives vbnet carrier status and makes the bridge work.

```bash
cd setup/
make
sudo make install
```

This compiles `tapthat`, installs it to `/usr/local/sbin/`, copies the systemd service file, reloads systemd, and enables the service for boot.

---

## DNS and DHCP with dnsmasq

dnsmasq provides DNS and DHCP for the lab subnet, listening only on br0.

Create `/etc/dnsmasq.d/lab.conf`:

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

Key settings:

- `bind-interfaces` -- prevents dnsmasq from conflicting with systemd-resolved on port 53
- `local=/vm.localdomain/` -- makes dnsmasq authoritative for the lab domain so queries for AAAA/MX records don't get forwarded upstream and return errors
- `expand-hosts` -- appends `vm.localdomain` to short hostnames from `/etc/hosts`

dnsmasq automatically registers hostnames from DHCP leases in its DNS, so any VM that gets an IP via DHCP and sends a hostname will be resolvable without a manual entry.

### Host DNS Resolution (systemd-resolved)

On systems running systemd-resolved (Ubuntu 20.04+), you need to tell resolved to route the lab domain queries to dnsmasq.

Create `/etc/systemd/network/10-br0.network`:

```
[Match]
Name=br0

[Network]
DNS=192.168.120.1
Domains=vm.localdomain
KeepConfiguration=yes
```

Then restart networkd:

```bash
systemctl restart systemd-networkd
```

`KeepConfiguration=yes` is required -- without it, networkd will strip the static IP that ifupdown configured on br0.

This tells systemd-resolved to send any `vm.localdomain` queries to dnsmasq on 192.168.120.1, so the host can resolve lab VM hostnames.

### Static IPs

VMs with static IPs are defined in `/etc/hosts`. dnsmasq picks these up via `expand-hosts`:

```
192.168.120.1   vmgate.vm.localdomain vmgate
192.168.120.2   adserver.vm.localdomain adserver
192.168.120.3   esxhost.vm.localdomain esxhost
192.168.120.4   vcenter.vm.localdomain vcenter
```

---

## Internet Access for the Lab Network

The 192.168.120.0/24 subnet is not directly routable from your LAN. For VMs on the lab network to reach the internet, you need one of:

- **Static route on your gateway/router**: Add a route for 192.168.120.0/24 pointing to the host's LAN IP (e.g. 192.168.1.x). This is the cleanest approach.
- **IP masquerading on the host**: If you can't modify your router, set up iptables NAT on the host to masquerade traffic from 192.168.120.0/24 out the physical NIC.

Without one of these, VMs will be able to talk to each other and the host but won't have internet access.

---

## VMware Workstation Networking

VMware Workstation needs a vmnet configured on the 192.168.120.0/24 lab subnet so VMs can reach br0 and each other.

We do this by marking the vbnet tap interface created above as a bridge, and "soft-creating" vmnet2 as a vbnet bridge.

Edit `/etc/vmware/networking` and add these lines to define vmnet2 plus the bridge mapping at the end:

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

If your network doesn't support jumbo frames, remove the MTU 9000 line.

This bridges vmnet2 directly to the `vbnet` tap interface with no DHCP and no virtual adapter. dnsmasq on br0 handles DHCP and hands out the correct default route (192.168.120.1).

Any VM in VMware Workstation that needs to be on the lab network must have its network adapter set to "Custom: Specific virtual network" and select `/dev/vmnet2`.

### vmnet Device Permissions

If you are running VMware Workstation as a non-root user, the `/dev/vmnet*` device nodes must be world read/write.

VMware creates these device nodes directly, bypassing udev, so a udev rule won't work. Create a systemd service to set permissions after VMware starts:

`/etc/systemd/system/vmnet-permissions.service`:

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

```bash
systemctl daemon-reload
systemctl enable vmnet-permissions.service
```

---

## Infrastructure Servers

The core infra runs on a VMware Workstation instance installed on the local (Debian/Ubuntu) host. Any version of Workstation that supports Windows Server 2022 and ESXi 8.0U2 should work.

To build the adserver:

```bash
make adserver
```

Once the adserver is up, you'll need to enable the AD feature and create your domain. The "lab" location in osimager uses the adserver as DNS (for domain join) -- it needs to be running for the other builds to work.

To build the esxhost (if you want a vSphere env):

```bash
make esxhost
```

Once the host is up you can import vCenter into Workstation using the OVA. If you want to deploy on the nested ESXi server you can use the installer.
