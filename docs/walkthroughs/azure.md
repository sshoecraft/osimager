# Azure walkthrough

!!! warning "Not yet verified against a live account"
    This walkthrough was checked by generating the Packer configuration (`mkosimage -u`), not by running a build in Azure. If a step doesn't match what you see, please open an issue.

By the end of this page you will have a managed image in an Azure resource group, built from AlmaLinux 10 and configured by OSImager's Ansible post-install. You can also publish the same image as a version in an Azure Compute Gallery. An Azure build works differently from a hypervisor build. Nothing is installed from an ISO. Packer's `azure-arm` builder starts a VM from the AlmaLinux Marketplace image, configures it over SSH, and captures it. You don't need `iso_path`, nothing is downloaded, and the image never exists on your machine.

## 1. Prerequisites

**On the machine running OSImager**

- Packer, installed and on your `PATH` ([install instructions](https://developer.hashicorp.com/packer/install)).
- The Packer plugins. `mkosimage --init-plugins` installs the plugin for every platform, including `github.com/hashicorp/azure`, plus `github.com/hashicorp/ansible`:

    ```bash
    mkosimage --init-plugins
    ```

- No `mkisofs`. OSImager requires it only for builds that put an answer file on a CD (`cd_files`), and a cloud build has none.
- The Ansible venv the spec needs. AlmaLinux 10 needs Ansible 2.18:

    ```bash
    mkvenv 2.18        # or: mkvenv --all
    ```

    If you build with `--skip` (no post-install configuration), you don't need it.

**In Azure**

- A subscription, and a service principal with a client secret. OSImager passes `client_id`, `client_secret`, `tenant_id` and `subscription_id` to the builder. The build creates its own temporary resource group, so the plugin requires the service principal to have full access to the subscription. For example:

    ```bash
    az ad sp create-for-rbac --name osimager-packer --role Contributor \
      --scopes /subscriptions/<subscription-id>
    ```

    In the output, `appId` is the `client_id`, `password` is the `client_secret` and `tenant` is the `tenant_id`.

- A resource group for the finished images. The builder requires it to exist already:

    ```bash
    az group create --name rg-osimager-images --location eastus
    ```

- Nothing to set up for the network. `azure.json` names no virtual network, so the builder creates a temporary network and public IP inside the temporary resource group and connects to the VM directly on port 22. Your machine needs outbound SSH access to Azure public IPs.
- Optional: an Azure Compute Gallery, if you also want the image published as a gallery image version (step 3).

## 2. Global settings

Use the local secrets file:

```bash
mkosimage --set credential_source=config
```

`iso_path` plays no part in a cloud build. Leave it at whatever it is.

## 3. Credentials

An Azure build reads these secret paths:

| Path | Key | Used for | Needed |
|------|-----|----------|--------|
| `azure/<location>` | `client_id` | `client_id` | Yes |
| `azure/<location>` | `client_secret` | `client_secret` | Yes |
| `azure/<location>` | `tenant_id` | `tenant_id` | Yes |
| `azure/<location>` | `subscription_id` | `subscription_id` | Yes |
| `azure/<location>` | `gallery_subscription_id` | `shared_image_gallery_destination.subscription` | Only for a gallery |
| `azure/<location>` | `gallery_resource_group` | `shared_image_gallery_destination.resource_group` | Only for a gallery |
| `azure/<location>` | `gallery_name` | `shared_image_gallery_destination.gallery_name` | Only for a gallery |
| `azure/<location>` | `bastion_hostname` | `ssh_bastion_host` | Only through a bastion |
| `azure/<location>` | `bastion_username` | `ssh_bastion_username` | Only through a bastion |
| `azure/<location>` | `bastion_keyfile` | `ssh_bastion_private_key_file` (a path on this machine) | Only through a bastion |
| `images/linux` | `username` | `ssh_username`: the user Packer and Ansible log in as | Yes |
| `images/linux` | `password` | `ssh_password` | No, leave it out |

`<location>` is the location name in your build target. For `azure/azure-east/...` the path is `azure/azure-east`.

Create `~/.config/osimager/secrets`. This is the minimal form, a managed image only, with no gallery and no bastion:

```
images/linux username=packer
azure/azure-east client_id=<app-id> client_secret=<client-secret> tenant_id=<tenant-id> subscription_id=<subscription-id>
```

To also publish to a gallery, add the three gallery keys to the same line:

```
azure/azure-east client_id=<app-id> client_secret=<client-secret> tenant_id=<tenant-id> subscription_id=<subscription-id> gallery_subscription_id=<subscription-id> gallery_resource_group=<gallery-rg> gallery_name=<gallery-name>
```

Each key you leave out produces a warning such as `warning: secret not found: azure/azure-east/bastion_hostname` and is passed as an empty value. The builder ignores the gallery block when `gallery_name` is empty, and it uses no bastion when `bastion_hostname` is empty. Those warnings are expected.

About `images/linux`:

- **Don't use `root`.** The builder creates the user named in `ssh_username` on the VM. Its own default is `packer`, and the example uses the same name.
- **Leave the password out.** With no password, the builder generates temporary credentials for the build. OSImager prints `warning: secret not found: images/linux/password`, which is expected.

!!! note "If you also build hypervisor images"
    `images/linux` is shared by every Linux build. Hypervisor builds need `username=root` and a password, because the password goes into the kickstart. Keep the cloud setup in its own config directory and point `XDG_CONFIG_HOME` at it for cloud builds. OSImager then reads `$XDG_CONFIG_HOME/osimager/` (its `config.json`, `secrets` and `locations/`):

    ```bash
    mkdir -p ~/osimager-cloud/osimager/locations
    echo '{"credential_source": "config"}' > ~/osimager-cloud/osimager/config.json
    # put the secrets file and the location file from this page under ~/osimager-cloud/osimager/
    XDG_CONFIG_HOME=~/osimager-cloud mkosimage -u azure/azure-east/alma-10.2-x86_64 alma10-base
    ```

**Vault instead of the secrets file.** Store the same keys under the same paths, as described in [Credential Setup](../configuration/credential-setup.md):

```bash
vault secrets enable -path=azure -version=2 kv
vault kv put azure/azure-east client_id=<app-id> client_secret=<client-secret> \
  tenant_id=<tenant-id> subscription_id=<subscription-id>
```

OSImager resolves the `{{vault ...}}` references in the platform file itself, in Vault mode just as with the secrets file, and passes Packer only the values. Both modes read the same paths and keys, and a key you leave out produces the same `secret not found` warning and an empty value. This walkthrough was checked only with the secrets file.

## 4. Location file

Create `~/.config/osimager/locations/azure-east.json`:

```json
{
  "platforms": ["azure"],
  "defs": {
    "azure_location": "eastus",
    "azure_resource_group": "rg-osimager-images",
    "azure_replication_regions": ["eastus"]
  }
}
```

| Field | Goes to | What it does |
|-------|---------|--------------|
| `platforms` | | Must include `azure`. A target whose platform isn't listed fails with `location azure-east does not support platform ...`. |
| `defs.azure_location` | `location`, `temp_resource_group_name` | Region the build VM runs in and the managed image is created in. It is also part of the temporary resource group's name, `rg-packer-build-<name>-<azure_location>`. |
| `defs.azure_resource_group` | `managed_image_resource_group_name` | Existing resource group the managed image is saved to. |
| `defs.azure_replication_regions` | `shared_image_gallery_destination.replication_regions` | List of regions the gallery image version is replicated to. Only used with a gallery, but always set it: without it the build JSON carries an empty string where a list belongs. |
| `defs.vm_size` | `vm_size` | Optional. Build VM size. Defaults to `Standard_D2s_v3` (from `azure.json`). |
| `defs.image_version` | `image_version` | Optional. Marketplace image version. Defaults to `latest`. |

You don't set the base image here. `azure_image_publisher`, `azure_image_offer` and `azure_image_sku` come from the spec, which is loaded after the location, so a location value would be overwritten. To use a different base image for one build, use `-D` (for example `-D azure_image_sku=<sku>`).

Check the location before building:

```bash
mkosimage -x azure/azure-east/alma-10.2-x86_64 alma10-base
```

## 5. Build

```bash
mkosimage azure/azure-east/alma-10.2-x86_64 alma10-base
```

`alma10-base` is the image name. Without it, the name is the spec name (`alma-10.2-x86_64`).

What happens:

1. OSImager merges `azure.json`, your location and the AlmaLinux spec into a Packer build, fills in the secrets, and runs `packer build`. It prints `warning: removing empty value for: ssh_host` (cloud builds let Packer find the VM's address) and a `secret not found` warning for each optional key you left out. These are expected.
2. Packer creates the temporary resource group `rg-packer-build-alma10-base-eastus` and, inside it, a `Standard_D2s_v3` Linux VM from the Marketplace image `AlmaLinux` / `almalinux` / `10-gen2`, version `latest`.
3. It connects over SSH (through the bastion if you configured one) and runs the Ansible playbook (`config.yml`, with the spec's `specs/rhel/config_9.yml`) using `become`.
4. It removes the temporary SSH key from the VM (`ssh_clear_authorized_keys`), stops the VM, and captures it as the managed image `alma10-base` in `rg-osimager-images`.
5. If a gallery is configured, it publishes the image version `alma10-base` : `<YYYY.MM.DD>` to the gallery, replicated to `azure_replication_regions` with 2 replicas per region on `Standard_LRS` storage.
6. It deletes the temporary resource group and everything in it.

**Which base image each version uses** (from the AlmaLinux spec):

| Spec versions | `image_publisher` | `image_offer` | `image_sku` |
|---------------|-------------------|---------------|-------------|
| `alma-8.*` | `AlmaLinux` | `almalinux` | `8-gen2` |
| `alma-9.*` | `AlmaLinux` | `almalinux` | `9-gen2` |
| `alma-10.*` | `AlmaLinux` | `almalinux` | `10-gen2` |

The SKU names only the major version, and `image_version` is `latest`. `alma-10.0-x86_64`, `alma-10.1-x86_64` and `alma-10.2-x86_64` all start from the same image: the latest version of `10-gen2`. The minor version in the target doesn't pin an AlmaLinux point release. Build `x86_64` targets only. `azure.json` lists `aarch64`, but these SKUs are not aarch64 SKUs and the default VM size is x86.

**Picking the target.** `mkosimage -l` lists every spec, and cloud builds use the same names (`alma-10.2-x86_64`). `alma-latest-x86_64` works too:

```bash
mkosimage --latest | grep alma
#   alma-latest-x86_64                 alma-10.2-x86_64
mkosimage azure/azure-east/alma-latest-x86_64 alma10-base
```

Ignore the ISO column of `mkosimage -a`. A cloud build never downloads the ISO, and OSImager checks the ISO only for builders that use one, so a version whose `-a` entry is a local `file://` path works too. Don't use `--local` for cloud builds. It limits `-latest` to versions whose ISO is on disk.

Other specs with Azure base-image defs for at least some versions: `rhel`, `rocky`, `oel`, `centos`, `debian`, `ubuntu` and `sles`.

**Preview without building:**

```bash
mkosimage -u azure/azure-east/alma-10.2-x86_64 alma10-base   # the Packer JSON
mkosimage -n azure/azure-east/alma-10.2-x86_64 alma10-base   # everything except running packer
```

In the `-u` output, check `location`, `managed_image_resource_group_name`, `image_publisher`, `image_offer` and `image_sku`. Also check that `variables` shows your four service-principal values, `ssh-username` set to `packer`, and `gallery-name` empty unless you configured a gallery.

## 6. Check it worked

At the end, Packer prints the managed image's resource ID. In the portal, open **Images** and find `alma10-base` in `rg-osimager-images`. From the CLI:

```bash
az image show --resource-group rg-osimager-images --name alma10-base \
  --query '{name:name, location:location, state:provisioningState}' -o table
```

If you configured a gallery:

```bash
az sig image-version list --resource-group <gallery-rg> --gallery-name <gallery-name> \
  --gallery-image-definition alma10-base -o table
```

The temporary resource group `rg-packer-build-alma10-base-eastus` should be gone.

## 7. Troubleshooting

**`error: Secrets file not found!`** followed by `error: Your configuration uses secret references but credential_source 'config' is not configured.` The file `~/.config/osimager/secrets` (or `$XDG_CONFIG_HOME/osimager/secrets`) doesn't exist. Create it as shown in step 3.

**`error: Vault credentials not configured!`** `credential_source` is still `vault` (the default). Run `mkosimage --set credential_source=config`, or set `vault_addr` and `vault_token`.

**`warning: secret not found: azure/azure-east/client_id`** A required key is missing, or the path doesn't match the location name in your target. Warnings for the gallery and bastion keys are expected if you don't use them.

**`Error: location azure-east does not support platform aws`** The target's platform isn't in the location's `platforms` list.

**`Error loading file '.../locations/azure-east.toml': [Errno 2] No such file or directory`** No location file with that name exists. OSImager looks for `azure-east.json` first, then `azure-east.toml`.

**`spec alma-10.9-x86_64 not found`** No such version. List the valid names with `mkosimage -l`.

**`warning: removing empty value for: image_publisher`** (and `image_offer`, `image_sku`) That spec version has no Azure base image defined. `fedora` is one example. Pick a spec from the list in step 5.

**The Marketplace image is not found.** OSImager hasn't checked the spec's publisher, offer and SKU against Azure. List what's available and override for one build with `-D`:

```bash
az vm image list --location eastus --publisher AlmaLinux --all -o table
mkosimage -D azure_image_offer=<offer>,azure_image_sku=<sku> azure/azure-east/alma-10.2-x86_64 alma10-base
```

**`the managed image named alma10-base already exists in the resource group rg-osimager-images, use a different manage image name or use the -force option to automatically delete it.`** Use a different name, or pass `-f`. OSImager hands `-f` to Packer as `-force`.

**`a gallery image version for image name:version alma10-base:<YYYY.MM.DD> already exists in gallery ...`** The gallery version is the build date, so a second build with the same name on the same day collides. Use `-f`, or wait until the next day.

**`failed to get image "alma10-base" from image gallery ...`** The builder publishes a version into an existing gallery image definition named after the image, and it doesn't create the definition. Create it once:

```bash
az sig image-definition create --resource-group <gallery-rg> --gallery-name <gallery-name> \
  --gallery-image-definition alma10-base --publisher <your-org> --offer alma --sku 10 \
  --os-type Linux --hyper-v-generation V2
```

**`error: post-install requires Ansible 2.18`** Run `mkvenv 2.18`, or build with `--skip`.

**`error: 'packer' not found in PATH`** Install Packer (step 1).

**SSH times out, or authentication fails.** In the `-u` dump, check that `ssh-username` is not `root` and `ssh-password` is empty. If you use a bastion, check that `bastion_keyfile` is a path to a private key file on this machine. The SSH timeout is 45 minutes (`ssh_timeout` in the ssh spec).

## References

- Azure plugin, authentication: <https://developer.hashicorp.com/packer/integrations/hashicorp/azure>
- `azure-arm` builder options (`managed_image_*`, `shared_image_gallery_destination`, `temp_resource_group_name`, `ssh_bastion_*`): <https://developer.hashicorp.com/packer/integrations/hashicorp/azure/latest/components/builder/arm>
- Gallery validation and the `-force` handling quoted above: <https://github.com/hashicorp/packer-plugin-azure/tree/main/builder/azure/arm> (`config.go`, `builder.go`)
