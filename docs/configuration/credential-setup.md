# Credential Setup

OSImager needs credentials for two purposes:

1. **OS image credentials** — username/password for SSH or WinRM access during the build, and for setting the root/admin password in kickstart, preseed, and autounattend templates.
2. **Platform credentials** — server address, username, and password for remote platforms (vSphere, Proxmox, Azure, GCP, AWS).

Two credential backends are supported: a **local secrets file** (simplest) or **HashiCorp Vault** (enterprise).

## Config Mode (Local Secrets File)

### Setup

```bash
mkosimage --set credential_source=config
```

### Secrets File

Create `~/.config/osimager/secrets` with one entry per line:

```
# Format: path key=value key=value ...

# Image credentials (required for all builds)
images/linux username=root password=Ch@ng3m3
images/windows username=Administrator password=Ch@ng3m3

# vSphere credentials (one entry per location that uses vsphere)
# For "mkosimage vsphere/lab/..." the path is vsphere/lab
vsphere/lab server=vcenter.example.com username=administrator@vsphere.local password=Ch@ng3m3
vsphere/esx server=esxhost1.example.com username=root password=Ch@ng3m3

# Proxmox credentials (one entry per location that uses proxmox)
# For "mkosimage proxmox/pnet/..." the path is proxmox/pnet
proxmox/pnet server=proxmox.example.com username=root@pam password=Ch@ng3m3
```

Lines starting with `#` are comments. Blank lines are ignored.

### Path Structure

There are two types of secret paths:

**`images/<os>`** — OS credentials referenced by spec files. The `<os>` name matches what the spec's include chain uses:

- `images/linux` — used by all Linux distributions (RHEL, Debian, Ubuntu, SLES, etc.)
- `images/windows` — used by Windows and Windows Server

The username and password are used for:

- SSH/WinRM communicator access during the Packer build
- Setting the root/admin password in installer templates (kickstart `rootpw`, preseed `passwd/root-password`, etc.)
- Password hashes in installer configs via `5>images/linux:password<5` (SHA256) or `6>images/linux:password<6` (SHA512)

**`<platform>/<location>`** — Platform credentials referenced by platform JSON files. The path matches the `platform/location` portion of your build target:

```bash
mkosimage vsphere/lab/rhel-9.5-x86_64
#         ^^^^^^^^^^
#         looks up secrets at path: vsphere/lab
```

### How Secrets Are Referenced

In spec and platform JSON files, secrets are referenced two ways:

**Template markers** (in defs, files, config):
```
|>images/linux:username<|     → "root"
|>images/linux:password<|     → "Ch@ng3m3"
6>images/linux:password<6     → "$6$salt$hash..."  (SHA512 hash)
```

**Packer vault syntax** (in variables):
```json
"ssh-username": "{{vault `images/linux` `username`}}"
"ssh-password": "{{vault `images/linux` `password`}}"
```

When using config mode, `resolve_packer_vault_refs()` automatically replaces `{{vault ...}}` references with values from the secrets file before passing the JSON to Packer.

## Vault Mode (HashiCorp Vault)

### Setup

```bash
mkosimage --set credential_source=vault
mkosimage --set vault_addr=http://your-vault-server:8200
mkosimage --set vault_token=your-vault-token
```

### Vault Configuration

OSImager uses the **KV v2** secrets engine. Enable mount points for each path prefix:

```bash
vault secrets enable -path=images -version=2 kv
vault secrets enable -path=vsphere -version=2 kv
vault secrets enable -path=proxmox -version=2 kv
```

Store credentials:

```bash
# Image credentials
vault kv put images/linux username=root password=Ch@ng3m3
vault kv put images/windows username=Administrator password=Ch@ng3m3

# vSphere credentials
vault kv put vsphere/lab server=vcenter.example.com username=administrator@vsphere.local password=Ch@ng3m3

# Proxmox credentials
vault kv put proxmox/pnet server=proxmox.example.com username=root@pam password=Ch@ng3m3
```

### How Vault Mode Works

- OSImager connects using `hvac.Client(url=vault_addr, token=vault_token)`
- Verifies authentication with `vault.is_authenticated()`
- Reads secrets via `vault.secrets.kv.v2.read_secret_version()`
- Packer also accesses Vault directly using the `{{vault ...}}` template function (VAULT_ADDR and VAULT_TOKEN are passed as environment variables)

## Per-Platform Credential Requirements

Each platform that connects to remote infrastructure needs specific credentials:

### vSphere

| Key | Description |
|-----|-------------|
| `server` | vCenter or ESXi hostname |
| `username` | vSphere username (e.g., `administrator@vsphere.local`) |
| `password` | vSphere password |

Secret path: `vsphere/<location>` (e.g., `vsphere/lab`)

### Proxmox

| Key | Description |
|-----|-------------|
| `server` | Proxmox server hostname |
| `username` | Proxmox username (e.g., `root@pam`) |
| `password` | Proxmox password |

Secret path: `proxmox/<location>` (e.g., `proxmox/pnet`)

### Azure

| Key | Description |
|-----|-------------|
| `client_id` | Azure service principal client ID |
| `client_secret` | Azure service principal secret |
| `tenant_id` | Azure AD tenant ID |
| `subscription_id` | Azure subscription ID |
| `gallery_subscription_id` | Shared Image Gallery subscription |
| `gallery_resource_group` | Gallery resource group |
| `gallery_name` | Gallery name |
| `bastion_hostname` | Bastion host for SSH tunneling |
| `bastion_username` | Bastion username |
| `bastion_keyfile` | Bastion SSH key file path |

Secret path: `azure/<location>`

### GCP

| Key | Description |
|-----|-------------|
| `credentials_json` | Service account JSON key |
| `project_id` | GCP project ID |
| `service_account_email` | Service account email |
| `bastion_hostname` | Bastion host for SSH tunneling |
| `bastion_username` | Bastion username |
| `bastion_password` | Bastion password |

Secret path: `gcp/<location>`

### AWS

| Key | Description |
|-----|-------------|
| `access_key` | AWS access key ID |
| `secret_key` | AWS secret access key |

Secret path: `aws/<location>`

### Local Platforms

VirtualBox, VMware, QEMU, libvirt, Hyper-V, and XenServer run locally and do not require platform credentials. They only need the `images/<os>` credentials for SSH/WinRM access during the build.

## The `get_secret()` Method

The `get_secret(string)` method is the unified interface for credential retrieval. It accepts a `path:key` format:

- `images/linux:username` → returns the username value
- `images/linux:password` → returns the password value
- `vsphere/lab:server` → returns the vSphere server address

The method dispatches based on `credential_source`:

- **config mode**: looks up `self.secrets[path][key]`
- **vault mode**: calls `vault.secrets.kv.v2.read_secret_version()` with the appropriate mount point and path

## Switching Between Modes

```bash
# Switch to config mode
mkosimage --set credential_source=config

# Switch to vault mode
mkosimage --set credential_source=vault
mkosimage --set vault_addr=http://vault:8200
mkosimage --set vault_token=s.xxxxxxxx
```

Settings are persisted in `~/.config/osimager/osimager.conf`.
