# Google Cloud walkthrough

!!! warning "Not yet verified against a live account"
    This walkthrough was checked by generating the Packer configuration (`mkosimage -u`), not by running a build in Google Cloud. If a step doesn't match what you see, please open an issue.

By the end of this page you will have a Compute Engine image in your Google Cloud project, built from AlmaLinux 10, configured by OSImager's Ansible post-install, and placed in the image family `alma-10`. A Google Cloud build works differently from a hypervisor build. Nothing is installed from an ISO. Packer's `googlecompute` builder starts a VM from the public AlmaLinux image family, configures it over SSH, and saves its disk as a new image. You don't need `iso_path`, nothing is downloaded, and the image never exists on your machine.

## 1. Prerequisites

**On the machine running OSImager**

- Packer, installed and on your `PATH` ([install instructions](https://developer.hashicorp.com/packer/install)).
- The Packer plugins. `mkosimage --init-plugins` installs the plugin for every platform, including `github.com/hashicorp/googlecompute`, plus `github.com/hashicorp/ansible`:

    ```bash
    mkosimage --init-plugins
    ```

- No `mkisofs`. OSImager requires it only for builds that put an answer file on a CD (`cd_files`), and a cloud build has none.
- The Ansible venv the spec needs. AlmaLinux 10 needs Ansible 2.18:

    ```bash
    mkvenv 2.18        # or: mkvenv --all
    ```

    If you build with `--skip` (no post-install configuration), you don't need it.
- Google Cloud credentials that Packer can find. Step 3 explains why these come from Application Default Credentials and not from the secrets file.

**In Google Cloud**

- A project with the Compute Engine API enabled.
- An identity for Packer with at least the **Compute Instance Admin (v1)** and **Service Account User** roles. That is either your own user account (through Application Default Credentials) or a service account with a JSON key. The plugin's documentation names these roles.
- A firewall rule that lets your machine reach the build VM on port 22. `gcp.json` names no network, so the VM uses the plugin's default network, `default`, and gets the network tag `packer`:

    ```bash
    gcloud compute firewall-rules create allow-packer-ssh --project <project-id> \
      --network default --allow tcp:22 --target-tags packer \
      --source-ranges <your-public-ip>/32
    ```

## 2. Global settings

Use the local secrets file:

```bash
mkosimage --set credential_source=config
```

`iso_path` plays no part in a cloud build. Leave it at whatever it is.

## 3. Credentials

A Google Cloud build reads these secret paths:

| Path | Key | Used for | Needed |
|------|-----|----------|--------|
| `gcp/<location>` | `project_id` | `project_id`: the project the VM and image are created in | Yes |
| `gcp/<location>` | `credentials_json` | `credentials_json`: the contents of a service-account key | No, see below |
| `gcp/<location>` | `service_account_email` | `service_account_email`: the service account attached to the build VM | No. Without it, the project's default compute service account is used |
| `gcp/<location>` | `bastion_hostname` | `ssh_bastion_host` | Only through a bastion |
| `gcp/<location>` | `bastion_username` | `ssh_bastion_username` | Only through a bastion |
| `gcp/<location>` | `bastion_password` | `ssh_bastion_password` | Only through a bastion |
| `images/linux` | `username` | `ssh_username`: the user Packer and Ansible log in as | Yes |
| `images/linux` | `password` | `ssh_password` | No, leave it out |

`<location>` is the location name in your build target. For `gcp/gcp-central/...` the path is `gcp/gcp-central`.

Create `~/.config/osimager/secrets`:

```
images/linux username=packer
gcp/gcp-central project_id=<project-id>
```

**Credentials come from Application Default Credentials.** The secrets file splits each line on whitespace and splits each value at the first `=`. A service-account key file is multi-line JSON with spaces in it, so it can't be stored as `credentials_json` there. Leave `credentials_json` out. OSImager prints `warning: secret not found: gcp/gcp-central/credentials_json` and passes an empty value, and the plugin then falls back to Application Default Credentials. Set those up one of two ways:

```bash
# your own user account
gcloud auth application-default login

# or a service-account key file
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

About `images/linux`:

- **Don't use `root`.** Root SSH access is disabled on many public images. The plugin creates the user named in `ssh_username`, with sudo access, through instance metadata. The example uses `packer`.
- **Leave the password out.** With no credentials given, the plugin generates a temporary SSH key pair. OSImager prints `warning: secret not found: images/linux/password`, which is expected.

Each optional key you leave out produces a similar `secret not found` warning and is passed as an empty value. An empty `bastion_hostname` means no bastion.

!!! note "If you also build hypervisor images"
    `images/linux` is shared by every Linux build. Hypervisor builds need `username=root` and a password, because the password goes into the kickstart. Keep the cloud setup in its own config directory and point `XDG_CONFIG_HOME` at it for cloud builds. OSImager then reads `$XDG_CONFIG_HOME/osimager/` (its `config.json`, `secrets` and `locations/`):

    ```bash
    mkdir -p ~/osimager-cloud/osimager/locations
    echo '{"credential_source": "config"}' > ~/osimager-cloud/osimager/config.json
    # put the secrets file and the location file from this page under ~/osimager-cloud/osimager/
    XDG_CONFIG_HOME=~/osimager-cloud mkosimage -u gcp/gcp-central/alma-10.2-x86_64 alma10-base
    ```

**Vault instead of the secrets file.** Store the same keys under the same paths, as described in [Credential Setup](../configuration/credential-setup.md). A Vault value can hold the whole key file:

```bash
vault secrets enable -path=gcp -version=2 kv
vault kv put gcp/gcp-central project_id=<project-id> credentials_json=@/path/to/key.json
```

OSImager resolves the `{{vault ...}}` references in the platform file itself, in Vault mode just as with the secrets file, and passes Packer only the values. Both modes read the same paths and keys, and a key you leave out produces the same `secret not found` warning and an empty value. This walkthrough was checked only with the secrets file.

## 4. Location file

Create `~/.config/osimager/locations/gcp-central.json`:

```json
{
  "platforms": ["gcp"],
  "defs": {
    "gcp_region": "us-central1",
    "gcp_zone": "us-central1-a"
  }
}
```

| Field | Goes to | What it does |
|-------|---------|--------------|
| `platforms` | | Must include `gcp`. A target whose platform isn't listed fails with `location gcp-central does not support platform ...`. |
| `defs.gcp_region` | `region`, `image_labels.img-region` | Region of the build. It is also recorded on the image as the label `img-region`. |
| `defs.gcp_zone` | `zone` | Zone the build VM runs in. It must be in `gcp_region`. |
| `defs.machine_type` | `machine_type` | Optional. Build VM type. Defaults to `n1-standard-2` (from `gcp.json`). |
| `defs.disk_type` | `disk_type` | Optional. Build disk type. Defaults to `pd-ssd`. |
| `defs.state_timeout` | `state_timeout` | Optional. How long Packer waits for the VM to change state. Defaults to `15m`. |

You don't set the source image here. `gcp_source_image_family`, `gcp_source_image_project_id` and `gcp_image_family` come from the spec, which is loaded after the location, so a location value would be overwritten. To change one for a build, use `-D` (for example `-D gcp_source_image_project_id=almalinux-cloud`).

Check the location before building:

```bash
mkosimage -x gcp/gcp-central/alma-10.2-x86_64 alma10-base
```

## 5. Build

```bash
mkosimage gcp/gcp-central/alma-10.2-x86_64 alma10-base
```

`alma10-base` is the image name, and on Google Cloud you have to give one. Resource names there may contain only lowercase letters, digits and hyphens. The default name is the spec name, `alma-10.2-x86_64`, which has a dot and an underscore. It would end up in both `instance_name` (`build-<name>`) and `image_name` (`<name>-<timestamp>`), and Google Cloud rejects both.

What happens:

1. OSImager merges `gcp.json`, your location and the AlmaLinux spec into a Packer build, fills in the secrets, and runs `packer build`. It prints `warning: removing empty value for: source_image_project_id` and `warning: removing empty value for: ssh_host`, plus the `secret not found` warnings for keys you left out. These are expected.
2. Packer finds the newest image in the family `almalinux-10`. The spec gives no source project, so the plugin searches your project first and then its built-in list of public image projects, which includes `almalinux-cloud`.
3. It creates the VM `build-alma10-base` (`n1-standard-2`, `pd-ssd`, tag `packer`) in `us-central1-a`, adds a temporary SSH key for `packer` through instance metadata, and connects over SSH (through the bastion if you configured one).
4. It runs the Ansible playbook (`config.yml`, with the spec's `specs/rhel/config_9.yml`) using `become`. On Google Cloud the playbook also runs `tasks/gcp_post.yml`. That file tries to install `google-compute-engine` and the Google Cloud Ops Agent, removes `google-osconfig-agent`, stops and disables `google-guest-agent`, and installs OSImager's `instance_configs.cfg.template`.
5. It removes the temporary SSH key (`ssh_clear_authorized_keys`), stops the VM, and creates the image `alma10-base-<timestamp>` in family `alma-10`, with the description `alma10-base Image` and the label `img-region=us-central1`.
6. It deletes the VM and its disk.

**Which base image each version uses** (from the AlmaLinux spec):

| Spec versions | `source_image_family` | Output `image_family` |
|---------------|-----------------------|-----------------------|
| `alma-8.*` | `almalinux-8` | `alma-8` |
| `alma-9.*` | `almalinux-9` | `alma-9` |
| `alma-10.*` | `almalinux-10` | `alma-10` |

An image family always resolves to its newest non-deprecated image. `alma-10.0-x86_64`, `alma-10.1-x86_64` and `alma-10.2-x86_64` all start from the same image, so the minor version in the target doesn't pin an AlmaLinux point release. Build `x86_64` targets only. `gcp.json` lists `aarch64`, but these families and the default `n1-standard-2` machine type are x86.

To name the source project explicitly instead of relying on the plugin's search list:

```bash
mkosimage -D gcp_source_image_project_id=almalinux-cloud gcp/gcp-central/alma-10.2-x86_64 alma10-base
```

**Picking the target.** `mkosimage -l` lists every spec, and cloud builds use the same names (`alma-10.2-x86_64`). `alma-latest-x86_64` works too:

```bash
mkosimage --latest | grep alma
#   alma-latest-x86_64                 alma-10.2-x86_64
mkosimage gcp/gcp-central/alma-latest-x86_64 alma10-base
```

Ignore the ISO column of `mkosimage -a`. A cloud build never downloads the ISO, and OSImager checks the ISO only for builders that use one, so a version whose `-a` entry is a local `file://` path works too. Don't use `--local` for cloud builds. It limits `-latest` to versions whose ISO is on disk.

Other specs with Google Cloud base-image defs for at least some versions: `rhel`, `rocky`, `oel`, `centos`, `debian`, `ubuntu`, `sles` and `fedora`.

**Preview without building:**

```bash
mkosimage -u gcp/gcp-central/alma-10.2-x86_64 alma10-base   # the Packer JSON
mkosimage -n gcp/gcp-central/alma-10.2-x86_64 alma10-base   # everything except running packer
```

In the `-u` output, check `zone`, `source_image_family`, `image_family`, `instance_name` and `image_name`. Also check that `variables` shows your `project-id`, `ssh-username` set to `packer`, and `gcp-creds` empty.

## 6. Check it worked

At the end, Packer prints the new image's name. In the console, open **Compute Engine → Images** and filter on family `alma-10`. From the CLI:

```bash
gcloud compute images list --project <project-id> --no-standard-images \
  --filter="family=alma-10"
gcloud compute images describe-from-family alma-10 --project <project-id>
```

To create a VM from the newest build, use the family: `--image-family alma-10 --image-project <project-id>`.

## 7. Troubleshooting

**`error: Secrets file not found!`** followed by `error: Your configuration uses secret references but credential_source 'config' is not configured.` The file `~/.config/osimager/secrets` (or `$XDG_CONFIG_HOME/osimager/secrets`) doesn't exist. Create it as shown in step 3.

**`error: Vault credentials not configured!`** `credential_source` is still `vault` (the default). Run `mkosimage --set credential_source=config`, or set `vault_addr` and `vault_token`.

**`warning: secret not found: gcp/gcp-central/project_id`** The project is missing, or the path doesn't match the location name in your target. Warnings for `credentials_json`, `service_account_email` and the bastion keys are expected if you don't use them.

**Packer can't find credentials.** `credentials_json` is empty, so the plugin uses Application Default Credentials. Run `gcloud auth application-default login`, or export `GOOGLE_APPLICATION_CREDENTIALS` in the shell you run `mkosimage` from.

**Packer rejects the instance or image name.** Pass an image name made of lowercase letters, digits and hyphens (step 5).

**`Error: location gcp-central does not support platform aws`** The target's platform isn't in the location's `platforms` list.

**`Error loading file '.../locations/gcp-central.toml': [Errno 2] No such file or directory`** No location file with that name exists. OSImager looks for `gcp-central.json` first, then `gcp-central.toml`.

**`spec alma-10.9-x86_64 not found`** No such version. List the valid names with `mkosimage -l`.

**The source image is not found.** Pass the project explicitly with `-D gcp_source_image_project_id=almalinux-cloud`, and check that the family exists: `gcloud compute images describe-from-family almalinux-10 --project almalinux-cloud`.

**`error: post-install requires Ansible 2.18`** Run `mkvenv 2.18`, or build with `--skip`.

**`error: 'packer' not found in PATH`** Install Packer (step 1).

**SSH times out.** Check the firewall rule from step 1: the VM carries the tag `packer` on the `default` network. In the `-u` dump, check that `ssh-username` is not `root`. The SSH timeout is 45 minutes (`ssh_timeout` in the ssh spec).

## References

- googlecompute plugin, authentication and required roles: <https://developer.hashicorp.com/packer/integrations/hashicorp/googlecompute>
- `googlecompute` builder options (`source_image_family`, `source_image_project_id`, `service_account_email`, `network`, gotchas): <https://developer.hashicorp.com/packer/integrations/hashicorp/googlecompute/latest/components/builder/googlecompute>
- Default public image projects searched for the source image: <https://github.com/hashicorp/packer-plugin-googlecompute/blob/main/lib/common/driver_gce.go>
- Compute Engine resource naming: <https://cloud.google.com/compute/docs/naming-resources>
