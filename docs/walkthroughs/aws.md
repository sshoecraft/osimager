# AWS walkthrough

!!! warning "Not yet verified against a live account"
    This walkthrough was checked by generating the Packer configuration (`mkosimage -u`), not by running a build in AWS. If a step doesn't match what you see, please open an issue.

By the end of this page you will have an AMI in your AWS account, built from AlmaLinux 10 and configured by OSImager's Ansible post-install. An AWS build works differently from a hypervisor build. Nothing is installed from an ISO. Packer's `amazon-ebs` builder starts an EC2 instance from a published AlmaLinux AMI, configures it over SSH, and saves the result as a new AMI. You don't need `iso_path`, nothing is downloaded, and the image never exists on your machine.

## 1. Prerequisites

**On the machine running OSImager**

- Packer, installed and on your `PATH` ([install instructions](https://developer.hashicorp.com/packer/install)).
- The Packer plugins. `mkosimage --init-plugins` installs the plugin for every platform, including `github.com/hashicorp/amazon`, plus `github.com/hashicorp/ansible`:

    ```bash
    mkosimage --init-plugins
    ```

- No `mkisofs`. OSImager requires it only for builds that put an answer file on a CD (`cd_files`), and a cloud build has none.
- The Ansible venv the spec needs. AlmaLinux 10 needs Ansible 2.18:

    ```bash
    mkvenv 2.18        # or: mkvenv --all
    ```

    If you build with `--skip` (no post-install configuration), you don't need it.

**In AWS**

- An AWS account and an IAM user with an access key. The minimal permissions Packer needs are listed in the Amazon plugin's documentation (see the links at the end of this page). They cover creating and terminating instances, key pairs, security groups, volumes, snapshots and images: `ec2:RunInstances`, `ec2:TerminateInstances`, `ec2:CreateKeyPair`, `ec2:CreateSecurityGroup`, `ec2:AuthorizeSecurityGroupIngress`, `ec2:CreateImage`, `ec2:RegisterImage`, `ec2:CreateTags`, `ec2:Describe*` and the rest of that list.
- A VPC and a subnet in the region you'll build in. The build instance gets a public IP (`associate_public_ip_address` is `true` in `aws.json`), and Packer connects to that IP on port 22. The subnet therefore needs a route to an internet gateway, and your machine must be able to reach it.
- Nothing to configure for SSH access. Packer creates a temporary security group that allows SSH (from `0.0.0.0/0` by default) and a temporary key pair, and deletes both at the end of the build.

## 2. Global settings

Use the local secrets file:

```bash
mkosimage --set credential_source=config
```

`iso_path` plays no part in a cloud build. Leave it at whatever it is.

## 3. Credentials

An AWS build reads two secret paths:

| Path | Key | Used for |
|------|-----|----------|
| `aws/<location>` | `access_key` | `access_key` of the `amazon-ebs` builder |
| `aws/<location>` | `secret_key` | `secret_key` of the `amazon-ebs` builder |
| `images/linux` | `username` | `ssh_username`: the user Packer and Ansible log in as |
| `images/linux` | `password` | `ssh_password` |

`<location>` is the location name in your build target. For `aws/aws-east/...` the path is `aws/aws-east`.

Create `~/.config/osimager/secrets`:

```
images/linux username=ec2-user
aws/aws-east access_key=<access-key-id> secret_key=<secret-access-key>
```

The `images/linux` line is different from a hypervisor build, and it matters:

- **The username must be the AMI's default user.** For the AlmaLinux AMIs that is `ec2-user`, the user the temporary key is installed for. Don't use `root`.
- **Leave the password out.** The `amazon-ebs` builder only generates a temporary key pair when `ssh_password` is empty. With a password set, the instance launches with no key, and the password login fails. With the key missing, OSImager prints `warning: secret not found: images/linux/password` and passes an empty password. That warning is expected.

!!! note "If you also build hypervisor images"
    `images/linux` is shared by every Linux build. Hypervisor builds need `username=root` and a password, because the password goes into the kickstart. Keep the cloud setup in its own config directory and point `XDG_CONFIG_HOME` at it for cloud builds. OSImager then reads `$XDG_CONFIG_HOME/osimager/` (its `config.json`, `secrets` and `locations/`):

    ```bash
    mkdir -p ~/osimager-cloud/osimager/locations
    echo '{"credential_source": "config"}' > ~/osimager-cloud/osimager/config.json
    # put the secrets file and the location file from this page under ~/osimager-cloud/osimager/
    XDG_CONFIG_HOME=~/osimager-cloud mkosimage -u aws/aws-east/alma-10.2-x86_64 alma10-base
    ```

If you leave `access_key` and `secret_key` out of the `aws/aws-east` line, OSImager warns that the secret is not found and passes empty values. The Amazon plugin then looks for credentials in its usual places, in this order: the `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` environment variables, the shared credentials file (`~/.aws/credentials`), then an instance role.

**Vault instead of the secrets file.** Store the same keys under the same paths, as described in [Credential Setup](../configuration/credential-setup.md):

```bash
vault secrets enable -path=aws -version=2 kv
vault kv put aws/aws-east access_key=<access-key-id> secret_key=<secret-access-key>
vault kv put images/linux username=ec2-user
```

OSImager resolves the `{{vault ...}}` references in the platform file itself, in Vault mode just as with the secrets file, and passes Packer only the values. Both modes read the same paths and keys, and a key you leave out produces the same `secret not found` warning and an empty value. This walkthrough was checked only with the secrets file.

## 4. Location file

Create `~/.config/osimager/locations/aws-east.json`:

```json
{
  "platforms": ["aws"],
  "defs": {
    "aws_region": "us-east-1",
    "aws_vpc_id": "vpc-0123456789abcdef0",
    "aws_subnet_id": "subnet-0123456789abcdef0"
  }
}
```

| Field | Goes to | What it does |
|-------|---------|--------------|
| `platforms` | | Must include `aws`. A target whose platform isn't listed fails with `location aws-east does not support platform ...`. |
| `defs.aws_region` | `region` | Region the build instance runs in and the AMI is created in. |
| `defs.aws_vpc_id` | `vpc_id` | VPC for the build instance. |
| `defs.aws_subnet_id` | `subnet_id` | Subnet for the build instance. It needs a route to the internet, because Packer connects to the instance's public IP. |
| `defs.instance_type` | `instance_type` | Optional. Build instance size. Defaults to `t3.medium` (from `aws.json`). |

If you omit `aws_vpc_id` and `aws_subnet_id`, OSImager drops them from the build (`warning: removing empty value for: vpc_id`) and the plugin uses the region's default VPC.

You don't set the base AMI here. `aws_ami_filter_name` and `aws_ami_owners` come from the spec, which is loaded after the location, so a location value would be overwritten. To use a different base AMI for one build, use `-D` (for example `-D aws_ami_filter_name='AlmaLinux OS 10.1*x86_64*'`).

Check the location before building:

```bash
mkosimage -x aws/aws-east/alma-10.2-x86_64 alma10-base
```

## 5. Build

```bash
mkosimage aws/aws-east/alma-10.2-x86_64 alma10-base
```

`alma10-base` is the image name. Without it, the name is the spec name (`alma-10.2-x86_64`).

What happens:

1. OSImager merges `aws.json`, your location and the AlmaLinux spec into a Packer build, fills in the secrets, and runs `packer build`. It prints `warning: removing empty value for: ssh_host` (cloud builds let Packer find the instance's address) and the `images/linux/password` warning from step 3. Both are expected.
2. Packer looks up the newest AMI owned by `764336703387` whose name matches `AlmaLinux OS 10*x86_64*`, with an EBS root device and HVM virtualization.
3. It creates a temporary key pair and security group, and launches a `t3.medium` instance from that AMI in your subnet, with a public IP.
4. It connects over SSH as `ec2-user` and runs the Ansible playbook (`config.yml`, with the spec's `specs/rhel/config_9.yml`) using `become`.
5. It removes the temporary SSH key from the instance (`ssh_clear_authorized_keys`), stops it, and creates the AMI `alma10-base-<YYYY-MM-DD>`, tagged `Name=alma10-base` and `Builder=packer`.
6. It terminates the instance and deletes the temporary key pair and security group.

**Which base AMI each version uses** (from the AlmaLinux spec):

| Spec versions | `aws_ami_filter_name` | `aws_ami_owners` |
|---------------|-----------------------|------------------|
| `alma-8.*` | `AlmaLinux OS 8*x86_64*` | `764336703387` |
| `alma-9.*` | `AlmaLinux OS 9*x86_64*` | `764336703387` |
| `alma-10.*` | `AlmaLinux OS 10*x86_64*` | `764336703387` |

The filter matches only the major version, and `most_recent` is `true`. `alma-10.0-x86_64`, `alma-10.1-x86_64` and `alma-10.2-x86_64` all start from the same AMI: the newest AlmaLinux 10 x86_64 AMI in the region. The minor version in the target doesn't pin an AlmaLinux point release. Build `x86_64` targets only. `aws.json` lists `aarch64`, but the filter is hard-wired to `x86_64` and the default instance type is x86.

**Picking the target.** `mkosimage -l` lists every spec, and cloud builds use the same names (`alma-10.2-x86_64`). `alma-latest-x86_64` works too:

```bash
mkosimage --latest | grep alma
#   alma-latest-x86_64                 alma-10.2-x86_64
mkosimage aws/aws-east/alma-latest-x86_64 alma10-base
```

Ignore the ISO column of `mkosimage -a`. A cloud build never downloads the ISO, and OSImager checks the ISO only for builders that use one, so a version whose `-a` entry is a local `file://` path works too. Don't use `--local` for cloud builds. It limits `-latest` to versions whose ISO is on disk.

Other specs with AWS base-image defs for at least some versions: `rhel`, `rocky`, `oel`, `centos`, `debian`, `ubuntu`, `sles`, `fedora` and `amazon`. Check the dump for a filled-in `source_ami_filter` before building one of these.

**Preview without building:**

```bash
mkosimage -u aws/aws-east/alma-10.2-x86_64 alma10-base   # the Packer JSON
mkosimage -n aws/aws-east/alma-10.2-x86_64 alma10-base   # everything except running packer
```

In the `-u` output, check `region`, `vpc_id`, `subnet_id`, `source_ami_filter.filters.name` and `owners`, and check that `variables` shows your access key and `ssh-username` set to `ec2-user`.

## 6. Check it worked

At the end, Packer prints the new AMI ID for the region. In the EC2 console, open **Images → AMIs** in the build region and filter on **Owned by me**. The AMI is named `alma10-base-<YYYY-MM-DD>` with the tag `Name=alma10-base`. From the CLI:

```bash
aws ec2 describe-images --region us-east-1 --owners self \
  --filters "Name=name,Values=alma10-base-*" \
  --query 'Images[].[ImageId,Name,CreationDate]' --output table
```

Launch an instance from the AMI to use it. Log in with the key pair you choose at launch.

## 7. Troubleshooting

**`error: Secrets file not found!`** followed by `error: Your configuration uses secret references but credential_source 'config' is not configured.` The file `~/.config/osimager/secrets` (or `$XDG_CONFIG_HOME/osimager/secrets`) doesn't exist. Create it as shown in step 3.

**`error: Vault credentials not configured!`** `credential_source` is still `vault` (the default). Run `mkosimage --set credential_source=config`, or set `vault_addr` and `vault_token`.

**`warning: secret not found: aws/aws-east/access_key`** The secrets file has no `access_key` under `aws/aws-east`. Check that the path matches the location name in your target exactly. If you meant to use `~/.aws/credentials` or environment variables, you can ignore this warning.

**`Error: location aws-east does not support platform gcp`** The target's platform isn't in the location's `platforms` list.

**`Error loading file '.../locations/aws-east.toml': [Errno 2] No such file or directory`** No location file with that name exists. OSImager looks for `aws-east.json` first, then `aws-east.toml`, and the error names the `.toml` path even if you created a `.json` file in the wrong directory.

**`spec alma-10.9-x86_64 not found`** No such version. List the valid names with `mkosimage -l`.

**`error: post-install requires Ansible 2.18`** Run `mkvenv 2.18`, or build with `--skip`.

**`error: 'packer' not found in PATH`** Install Packer (step 1).

**SSH times out, or authentication fails.** In the `-u` dump, check that `ssh-username` is the AMI's default user (`ec2-user`) and `ssh-password` is empty. Also check that the subnet routes to an internet gateway and that your machine can reach the instance's public IP on port 22. The SSH timeout is 45 minutes (`ssh_timeout` in the ssh spec), so a wrong user can take a long time to fail.

**The AMI name is already in use.** `ami_name` is `<name>-<YYYY-MM-DD>`, so a second build with the same name on the same day collides. Use a different name, or pass `-f`. OSImager hands `-f` to Packer as `-force`, which makes the Amazon builder deregister the existing AMI first.

**`warning: location aws-east sets iso_path, which is ignored`** Remove `iso_path` from the location. It plays no part in cloud builds.

## References

- Amazon plugin, authentication and minimal IAM policy: <https://developer.hashicorp.com/packer/integrations/hashicorp/amazon>
- `amazon-ebs` builder options (`source_ami_filter`, `temporary_key_pair`, `force_deregister`, `associate_public_ip_address`): <https://developer.hashicorp.com/packer/integrations/hashicorp/amazon/latest/components/builder/ebs>
- AlmaLinux on AWS: <https://wiki.almalinux.org/cloud/AWS.html>. The AlmaLinux AWS Marketplace listing gives `ec2-user` as the default cloud user.
