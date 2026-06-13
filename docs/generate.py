#!/usr/bin/env python3
"""
Auto-generate documentation pages from OSImager spec and platform data.

Produces:
  - docs/reference/supported-os.md
  - docs/reference/defs-reference.md
"""

import json
import os
import re
import sys
from itertools import product
from collections import defaultdict

# Add parent directory to path so we can import osimager
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from osimager.utils import explode_string_with_dynamic_range
import osimager_data


DOCS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(DOCS_DIR)
# Data lives in the separate osimager_data package, not in the engine repo.
DATA_DIR = osimager_data.DATA_DIR
SPECS_DIR = os.path.join(DATA_DIR, "specs")
PLATFORMS_DIR = os.path.join(DATA_DIR, "platforms")


def load_json(path):
    with open(path) as f:
        return json.load(f)


def expand_versions(version_strings):
    """Expand version range strings into individual versions."""
    versions = []
    for vs in version_strings:
        versions.extend(explode_string_with_dynamic_range(vs))
    return versions


def iso_url_present(spec_data, version, arch):
    """Mirror of OSImager.resolve_iso_url: is there a non-empty iso_url for this
    version/arch? Specs no longer declare provides.arches -- an arch is supported
    when its arch_specific (or default) iso_url resolves to a non-empty string. An
    explicit "iso_url": "" blocks an arch."""
    iso_url = spec_data.get("defs", {}).get("iso_url", "")
    for a_s in spec_data.get("arch_specific", []):
        if a_s.get("arch", "") == arch and "iso_url" in a_s.get("defs", {}):
            iso_url = a_s["defs"]["iso_url"]
    for vs in spec_data.get("version_specific", []):
        if re.fullmatch(vs.get("version", ""), version, re.IGNORECASE):
            if "iso_url" in vs.get("defs", {}):
                iso_url = vs["defs"]["iso_url"]
            for a_s in vs.get("arch_specific", []):
                if a_s.get("arch", "") == arch and "iso_url" in a_s.get("defs", {}):
                    iso_url = a_s["defs"]["iso_url"]
    return bool(iso_url)


def candidate_arches(spec_data):
    """Architectures a spec could provide: every arch named in an arch_specific
    entry (top-level or per-version), plus x86_64 when a bare iso_url is defined
    without arch_specific (the common single-arch case). amd64 is treated as an
    x86_64 alias and not listed separately."""
    arches = set()
    for a_s in spec_data.get("arch_specific", []):
        if a_s.get("arch"):
            arches.add(a_s["arch"])
    for vs in spec_data.get("version_specific", []):
        for a_s in vs.get("arch_specific", []):
            if a_s.get("arch"):
                arches.add(a_s["arch"])
    has_bare_iso = bool(spec_data.get("defs", {}).get("iso_url")) or any(
        "iso_url" in vs.get("defs", {}) for vs in spec_data.get("version_specific", [])
    )
    if has_bare_iso:
        arches.add("x86_64")
    arches.discard("amd64")
    return arches


def compute_arches(spec_data, versions):
    """Return (sorted arch list for display, total version x arch count) by
    resolving iso_url availability per version/arch."""
    candidates = candidate_arches(spec_data)
    arch_order = ["x86_64", "aarch64", "arm64", "ppc64le", "ppc64", "s390x", "i386", "i686"]
    supported = set()
    total = 0
    for version in versions:
        for arch in candidates:
            if iso_url_present(spec_data, version, arch):
                supported.add(arch)
                total += 1
    ordered = [a for a in arch_order if a in supported]
    ordered += sorted(a for a in supported if a not in arch_order)
    return ordered, total


# When source filenames don't reveal the installer type, fall back to the
# distribution's known answer-file mechanism. Keeps the audit honest for the
# JSON/answer-file installers added in the 2026 distro expansion.
DIST_INSTALLER = {
    "proxmox-ve": "answer.toml",
    "xcpng": "answerfile.xml",
    "xenserver": "answerfile.xml",
    "alpine": "alpine-answerfile",
    "openbsd": "openbsd-autoinstall",
    "arch": "archinstall",
    "photon": "photon-kickstart",
    "fcos": "ignition",
    "coreos": "ignition",
    "flatcar": "ignition",
    "esxi": "kickstart",
    "esx": "kickstart",
    "esxi35": "kickstart",
}


def _classify_sources(all_sources, dist):
    """Classify installer type from source filenames. Most-specific tokens first
    so JSON installers aren't swallowed by broader matches (e.g. Photon's JSON
    kickstart vs a plain kickstart .cfg)."""
    s = " ".join(all_sources).lower()
    if "ignition" in s or ".ign" in s:
        return "ignition"
    if "archinstall" in s:
        return "archinstall"
    if "agama" in s:
        return "agama"
    if "install.conf" in s:
        return "openbsd-autoinstall"
    if "answer.toml" in s:
        return "answer.toml"
    if "answerfile.xml" in s:
        return "answerfile.xml"
    if "photon" in s and (".json" in s or "kickstart" in s):
        return "photon-kickstart"
    if "kickstart" in s or "ks-part" in s:
        return "kickstart"
    if "preseed" in s or ".seed" in s:
        return "preseed"
    if "cloud-init" in s or "user-data" in s:
        return "cloud-init"
    if "autoinst" in s or "autoyast" in s:
        return "autoyast"
    if "autounattend" in s:
        return "autounattend"
    if ".answers" in s or "answerfile" in s:
        return "alpine-answerfile"
    if "debian" in s:
        return "preseed"
    return None


def get_installer_type(spec_data, dist):
    """Determine the installer type from the files section, following includes and version_specific."""
    files = spec_data.get("files", [])

    # Check top-level files
    if files:
        all_sources = []
        for f in files:
            all_sources.extend(f.get("sources", []))
        result = _classify_sources(all_sources, dist)
        if result:
            return result

    # Check version_specific entries for files
    for vs_entry in spec_data.get("version_specific", []):
        vs_files = vs_entry.get("files", [])
        if vs_files:
            all_sources = []
            for f in vs_files:
                all_sources.extend(f.get("sources", []))
            result = _classify_sources(all_sources, dist)
            if result:
                return result

    # Follow the include chain
    include = spec_data.get("include", None)
    if include:
        if isinstance(include, str):
            include = [include]
        for inc in include:
            inc_path = os.path.join(SPECS_DIR, inc, "spec.json")
            if os.path.exists(inc_path):
                inc_data = load_json(inc_path)
                result = get_installer_type(inc_data, dist)
                if result != "none":
                    return result

    # Sources/includes didn't reveal it -- fall back to the distro's known method.
    return DIST_INSTALLER.get(dist, "none")


def detect_cloud_support(spec_data):
    """Scan version_specific for cloud platform defs (azure, gcp, aws)."""
    clouds = {"azure": set(), "gcp": set(), "aws": set()}
    version_specific = spec_data.get("version_specific", [])

    for entry in version_specific:
        version_pattern = entry.get("version", "")
        defs = entry.get("defs", {})
        has_azure = any(k.startswith("azure_") for k in defs)
        has_gcp = any(k.startswith("gcp_") for k in defs)
        has_aws = any(k.startswith("aws_") for k in defs)

        if has_azure:
            clouds["azure"].add(version_pattern)
        if has_gcp:
            clouds["gcp"].add(version_pattern)
        if has_aws:
            clouds["aws"].add(version_pattern)

    return clouds


def get_platforms_for_spec(spec_data, spec_dir):
    """Get platforms list, following includes if needed."""
    platforms = spec_data.get("platforms", [])
    if platforms:
        return platforms

    # Follow include chain
    include = spec_data.get("include", None)
    if include:
        if isinstance(include, str):
            include = [include]
        for inc in include:
            inc_path = os.path.join(SPECS_DIR, inc, "spec.json")
            if os.path.exists(inc_path):
                inc_data = load_json(inc_path)
                platforms = get_platforms_for_spec(inc_data, inc)
                if platforms:
                    return platforms
    return []


def get_include_chain(spec_data):
    """Get the include chain as a list."""
    chain = []
    include = spec_data.get("include", None)
    if include:
        if isinstance(include, str):
            include = [include]
        for inc in include:
            chain.append(inc)
            inc_path = os.path.join(SPECS_DIR, inc, "spec.json")
            if os.path.exists(inc_path):
                inc_data = load_json(inc_path)
                chain.extend(get_include_chain(inc_data))
    return chain


# Distribution display names. Any spec dir not listed here falls back to its
# directory name, so an unmapped distro still appears in the tables -- it just
# shows the slug until a friendly name is added.
DIST_NAMES = {
    "rhel": "Red Hat Enterprise Linux",
    "alma": "AlmaLinux",
    "rocky": "Rocky Linux",
    "centos": "CentOS",
    "oel": "Oracle Enterprise Linux",
    "debian": "Debian",
    "ubuntu": "Ubuntu",
    "sles": "SUSE Linux Enterprise Server",
    "esxi": "VMware ESXi",
    "esx": "VMware ESX",
    "esxi35": "VMware ESXi 3.5",
    "sysvr4": "System V Release 4",
    "windows": "Windows",
    "windows-server": "Windows Server",
    "fedora": "Fedora",
    "freebsd": "FreeBSD",
    "mxlinux": "MX Linux",
    "proxmox-ve": "Proxmox VE",
    "sco": "SCO OpenServer",
    "unixware": "UnixWare",
    "xcpng": "XCP-ng",
    # 2026 distro expansion (names land ahead of the specs; harmless if unused)
    "amazon": "Amazon Linux",
    "opensuse": "openSUSE Leap",
    "opensuse-leap": "openSUSE Leap",
    "photon": "VMware Photon OS",
    "alpine": "Alpine Linux",
    "openbsd": "OpenBSD",
    "arch": "Arch Linux",
    "fcos": "Fedora CoreOS",
    "coreos": "Fedora CoreOS",
    "flatcar": "Flatcar Container Linux",
    "vyos": "VyOS",
    "mint": "Linux Mint",
    "linuxmint": "Linux Mint",
    "pfsense": "pfSense",
    "opnsense": "OPNsense",
    "truenas": "TrueNAS",
}

# Preferred display order for the mainstream families. Any other buildable spec
# dir (one with a `provides` section) is appended alphabetically -- see
# ordered_spec_names() -- so the count reflects every distro in the repo.
DIST_ORDER = [
    "rhel", "alma", "rocky", "centos", "oel",
    "debian", "ubuntu", "sles",
    "esxi", "sysvr4",
    "windows-server",
]


def ordered_spec_names():
    """All spec dirs that contain a spec.json: DIST_ORDER first (for a sensible
    mainstream ordering), then everything else alphabetically. Specs without a
    `provides` section (base specs like linux/ssh/winrm) are filtered out by the
    caller."""
    names = sorted(
        d for d in os.listdir(SPECS_DIR)
        if os.path.exists(os.path.join(SPECS_DIR, d, "spec.json"))
    )
    ordered = [d for d in DIST_ORDER if d in names]
    ordered += [d for d in names if d not in DIST_ORDER]
    return ordered


def generate_supported_os():
    """Generate the supported-os.md page."""
    lines = []
    lines.append("# Supported Operating Systems")
    lines.append("")
    lines.append("This page is auto-generated from the spec data files.")
    lines.append("")

    total_specs = 0
    total_versions = 0

    # Collect all distro data
    distros = []
    for spec_name in ordered_spec_names():
        spec_path = os.path.join(SPECS_DIR, spec_name, "spec.json")
        if not os.path.exists(spec_path):
            continue
        spec_data = load_json(spec_path)
        provides = spec_data.get("provides", {})
        if not provides:
            continue

        dist = provides.get("dist", spec_name)
        version_strings = provides.get("versions", [])

        versions = expand_versions(version_strings)
        platforms = get_platforms_for_spec(spec_data, spec_name)
        include_chain = get_include_chain(spec_data)
        installer = get_installer_type(spec_data, dist)
        clouds = detect_cloud_support(spec_data)

        # Arches and spec count are derived from iso_url availability per
        # version/arch (specs no longer declare provides.arches).
        arches, spec_count = compute_arches(spec_data, versions)
        total_specs += spec_count
        total_versions += len(versions)

        distros.append({
            "name": spec_name,
            "display_name": DIST_NAMES.get(spec_name, spec_name),
            "dist": dist,
            "versions": versions,
            "version_strings": version_strings,
            "arches": arches,
            "platforms": platforms,
            "include_chain": include_chain,
            "installer": installer,
            "clouds": clouds,
            "spec_count": spec_count,
        })

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Metric | Count |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Distributions | {len(distros)} |")
    lines.append(f"| Total versions | {total_versions} |")
    lines.append(f"| Total specs (version x arch) | {total_specs} |")
    lines.append("")

    # Overview table
    lines.append("## Overview")
    lines.append("")
    lines.append("| Distribution | Versions | Architectures | Installer | Cloud |")
    lines.append("|-------------|----------|---------------|-----------|-------|")

    for d in distros:
        version_range = f"{d['versions'][0]} - {d['versions'][-1]}" if len(d['versions']) > 1 else d['versions'][0]
        arches_str = ", ".join(d["arches"])
        cloud_parts = []
        if d["clouds"]["azure"]:
            cloud_parts.append("Azure")
        if d["clouds"]["gcp"]:
            cloud_parts.append("GCP")
        if d["clouds"]["aws"]:
            cloud_parts.append("AWS")
        cloud_str = ", ".join(cloud_parts) if cloud_parts else "-"
        lines.append(f"| {d['display_name']} | {version_range} | {arches_str} | {d['installer']} | {cloud_str} |")

    lines.append("")

    # Per-distribution detail sections
    lines.append("## Distribution Details")
    lines.append("")

    for d in distros:
        lines.append(f"### {d['display_name']}")
        lines.append("")
        lines.append(f"**Spec name:** `{d['name']}`")
        lines.append("")

        if d["include_chain"]:
            chain = " → ".join([d["name"]] + d["include_chain"])
            lines.append(f"**Include chain:** {chain}")
            lines.append("")

        lines.append(f"**Installer type:** {d['installer']}")
        lines.append("")

        # Version ranges
        lines.append(f"**Version ranges:** `{', '.join(d['version_strings'])}`")
        lines.append("")

        # Expanded versions
        lines.append(f"**Versions ({len(d['versions'])}):** {', '.join(d['versions'])}")
        lines.append("")

        lines.append(f"**Architectures:** {', '.join(d['arches'])}")
        lines.append("")

        # Platforms
        local_plats = [p for p in d["platforms"] if p in ("virtualbox", "vmware", "qemu", "hyperv", "xenserver")]
        enterprise_plats = [p for p in d["platforms"] if p in ("vsphere", "proxmox")]
        cloud_plats = [p for p in d["platforms"] if p in ("azure", "gcp", "aws")]
        other_plats = [p for p in d["platforms"] if p in ("none",)]

        plat_parts = []
        if local_plats:
            plat_parts.append(f"Local: {', '.join(local_plats)}")
        if enterprise_plats:
            plat_parts.append(f"Enterprise: {', '.join(enterprise_plats)}")
        if cloud_plats:
            plat_parts.append(f"Cloud: {', '.join(cloud_plats)}")
        if other_plats:
            plat_parts.append(f"Other: {', '.join(other_plats)}")

        lines.append(f"**Platforms:** {' | '.join(plat_parts)}")
        lines.append("")

        # Cloud support
        if any(d["clouds"].values()):
            lines.append("**Cloud image support:**")
            lines.append("")
            for cloud, patterns in d["clouds"].items():
                if patterns:
                    lines.append(f"- **{cloud.upper()}**: version patterns {', '.join(sorted(patterns))}")
            lines.append("")

        lines.append(f"**Spec count:** {d['spec_count']}")
        lines.append("")
        lines.append("---")
        lines.append("")

    output_path = os.path.join(DOCS_DIR, "reference", "supported-os.md")
    with open(output_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Generated {output_path} ({total_specs} total specs)")


def extract_template_vars(data, pattern=r'>>(\w+)<<'):
    """Recursively extract template variable names from a data structure."""
    found = set()
    if isinstance(data, dict):
        for v in data.values():
            found.update(extract_template_vars(v, pattern))
    elif isinstance(data, list):
        for item in data:
            found.update(extract_template_vars(item, pattern))
    elif isinstance(data, str):
        found.update(re.findall(pattern, data))
    return found


def extract_all_patterns(data):
    """Extract all template patterns from a data structure."""
    patterns = {
        "inline": set(),       # >>var<<
        "value": set(),        # %>var<%
        "basename": set(),     # +>var<+
        "dns": set(),          # *>var<*
        "secret": set(),       # |>var<|
        "expression": set(),   # #>expr<#
        "env": set(),          # $>var<$
        "eval": set(),         # E>expr<E
        "list": set(),         # [>var<]
    }
    _extract_patterns_recursive(data, patterns)
    return patterns


def _extract_patterns_recursive(data, patterns):
    if isinstance(data, dict):
        for v in data.values():
            _extract_patterns_recursive(v, patterns)
    elif isinstance(data, list):
        for item in data:
            _extract_patterns_recursive(item, patterns)
    elif isinstance(data, str):
        patterns["inline"].update(re.findall(r'>>(\w+)<<', data))
        patterns["value"].update(re.findall(r'%>(\w+)<%', data))
        patterns["basename"].update(re.findall(r'\+>(\w+)<\+', data))
        patterns["dns"].update(re.findall(r'\*>(\w+)<\*', data))
        patterns["secret"].update(re.findall(r'\|>([^|]+)<\|', data))
        patterns["expression"].update(re.findall(r'#>([^#]+)<#', data))
        patterns["env"].update(re.findall(r'\$>(\w+)<\$', data))
        patterns["eval"].update(re.findall(r'E>(.+?)<E', data))
        patterns["list"].update(re.findall(r'\[>(\w+)<\]', data))


def generate_defs_reference():
    """Generate the defs-reference.md page."""
    lines = []
    lines.append("# Defs Reference")
    lines.append("")
    lines.append("This page is auto-generated from the platform and spec data files. It documents all template variables (defs) used by each platform.")
    lines.append("")

    # Load all platform configs
    platform_files = sorted([f for f in os.listdir(PLATFORMS_DIR) if f.endswith(".json")])

    # Configuration defaults (formerly in all.json, now in config/built-in defaults)
    all_defs = {"cpu_sockets": 1, "cpu_cores": 2, "memory": 2048, "boot_disk_size": 16384}

    lines.append("## Configuration Defaults")
    lines.append("")
    lines.append("These defaults are set in `~/.config/osimager/config.json` (or built-in if not configured):")
    lines.append("")
    lines.append("| Variable | Default Value |")
    lines.append("|----------|--------------|")
    for key, val in sorted(all_defs.items()):
        lines.append(f"| `{key}` | `{val}` |")
    lines.append("")

    # Categorize platforms
    local_platforms = ["virtualbox", "vmware", "qemu", "hyperv", "xenserver"]
    enterprise_platforms = ["vsphere", "proxmox"]
    cloud_platforms = ["azure", "gcp", "aws"]
    special_platforms = ["none"]

    categories = [
        ("Local ISO Platforms", local_platforms),
        ("Enterprise Platforms", enterprise_platforms),
        ("Cloud Platforms", cloud_platforms),
        ("Special Platforms", special_platforms),
    ]

    for cat_name, cat_platforms in categories:
        lines.append(f"## {cat_name}")
        lines.append("")

        for plat_name in cat_platforms:
            plat_file = f"{plat_name}.json"
            plat_path = os.path.join(PLATFORMS_DIR, plat_file)
            if not os.path.exists(plat_path):
                continue

            plat_data = load_json(plat_path)
            lines.append(f"### {plat_name}")
            lines.append("")

            # Builder type
            config = plat_data.get("config", {})
            builder_type = config.get("type", "unknown")
            lines.append(f"**Builder type:** `{builder_type}`")
            lines.append("")

            # Platform defs
            plat_defs = plat_data.get("defs", {})
            if plat_defs:
                lines.append("**Platform defs:**")
                lines.append("")
                lines.append("| Variable | Value |")
                lines.append("|----------|-------|")
                for key, val in sorted(plat_defs.items()):
                    val_str = str(val)
                    if len(val_str) > 60:
                        val_str = val_str[:57] + "..."
                    lines.append(f"| `{key}` | `{val_str}` |")
                lines.append("")

            # Extract all template variables referenced
            all_patterns = extract_all_patterns(plat_data)

            # Inline vars (>>var<<)
            inline_vars = sorted(all_patterns["inline"])
            if inline_vars:
                lines.append("**Template variables referenced** (`>>var<<`):")
                lines.append("")
                for var in inline_vars:
                    source = "config default" if var in all_defs else "location" if var in (
                        "vms_path", "iso_path", "domain", "gateway", "cidr", "subnet", "prefix",
                        "netmask", "dns_search", "datacenter", "esxi_host", "cluster", "datastore",
                        "folder", "vm_network", "azure_location", "azure_resource_group",
                        "gcp_region", "gcp_zone", "aws_region", "aws_vpc_id", "aws_subnet_id",
                        "proxmox_node", "iso_storage_pool", "vm_storage_pool",
                        "azure_replication_regions"
                    ) else "spec" if var in (
                        "cd_files", "cd_label", "iso_url", "iso_name", "iso_checksum",
                        "iso_path", "spec_name", "azure_image_publisher", "azure_image_offer",
                        "azure_image_sku", "gcp_source_image_family", "gcp_source_image_project_id",
                        "gcp_image_family", "aws_ami_filter_name"
                    ) else "computed"
                    lines.append(f"- `{var}` — {source}")
                lines.append("")

            # Value replacements (%>var<%)
            value_vars = sorted(all_patterns["value"])
            if value_vars:
                lines.append("**Value replacements** (`%>var<%`):")
                lines.append("")
                for var in value_vars:
                    lines.append(f"- `{var}`")
                lines.append("")

            # Expressions (#>expr<#)
            expressions = sorted(all_patterns["expression"])
            if expressions:
                lines.append("**Numeric expressions** (`#>expr<#`):")
                lines.append("")
                for expr in expressions:
                    lines.append(f"- `{expr}`")
                lines.append("")

            # Eval expressions (E>expr<E)
            evals = sorted(all_patterns["eval"])
            if evals:
                lines.append("**Eval expressions** (`E>expr<E`):")
                lines.append("")
                for expr in evals:
                    if len(expr) > 80:
                        expr = expr[:77] + "..."
                    lines.append(f"- `{expr}`")
                lines.append("")

            # Vault variables
            variables = plat_data.get("variables", {})
            if variables:
                lines.append("**Vault/credential variables:**")
                lines.append("")
                lines.append("| Variable | Vault Path |")
                lines.append("|----------|-----------|")
                for var_name, var_val in sorted(variables.items()):
                    # Extract vault path from {{vault `path` `key`}}
                    match = re.search(r'\{\{vault `([^`]+)` `([^`]+)`\}\}', str(var_val))
                    if match:
                        vault_path = f"{match.group(1)}:{match.group(2)}"
                    else:
                        vault_path = str(var_val)
                    if len(vault_path) > 60:
                        vault_path = vault_path[:57] + "..."
                    lines.append(f"| `{var_name}` | `{vault_path}` |")
                lines.append("")

            lines.append("---")
            lines.append("")

    # Computed defs section
    lines.append("## Computed Defs")
    lines.append("")
    lines.append("These defs are computed during the build pipeline and are available for template substitution:")
    lines.append("")
    lines.append("| Variable | Source | Description |")
    lines.append("|----------|--------|-------------|")
    computed = [
        ("name", "CLI or spec", "VM/image name (hostname or spec name)"),
        ("fqdn", "Computed", "Fully qualified domain name (name + domain)"),
        ("ip", "CLI or DNS", "IP address (from CLI arg or DNS lookup)"),
        ("platform", "CLI", "Platform name from target"),
        ("location", "CLI", "Location name from target"),
        ("dist", "Spec provides", "Distribution name"),
        ("version", "Spec provides", "Full version string"),
        ("major", "Computed", "Major version number"),
        ("minor", "Computed", "Minor version number"),
        ("arch", "Spec provides", "Architecture (x86_64, aarch64, etc.)"),
        ("firmware", "Location or default", "Firmware type (bios or efi)"),
        ("base_path", "Settings", "OSImager package base directory"),
        ("data_path", "Settings", "Data directory path"),
        ("user_dir", "Settings", "User config directory (~/.config/osimager)"),
        ("temp_dir", "Computed", "Temporary build directory"),
        ("spec_dir", "Computed", "Spec data directory path"),
        ("spec_name", "Computed", "Spec identifier (dist-version-arch)"),
        ("platform_name", "CLI", "Platform name"),
        ("location_name", "CLI", "Location name"),
        ("platform_type", "Platform config", "Packer builder type"),
        ("subnet", "Computed", "Subnet from CIDR"),
        ("prefix", "Computed", "Network prefix from CIDR"),
        ("netmask", "Computed", "Netmask from CIDR prefix"),
        ("gateway", "Location or CIDR", "Gateway address"),
        ("dns1", "Location DNS", "Primary DNS server"),
        ("dns2", "Location DNS", "Secondary DNS server"),
        ("dns_search", "Location DNS", "DNS search domain"),
        ("ntp1", "Location NTP", "Primary NTP server"),
        ("iso_url", "Spec or local", "ISO download URL"),
        ("iso_name", "Computed", "ISO filename"),
        ("iso_checksum", "Computed", "ISO checksum value"),
        ("local_only", "Settings", "Whether to use local ISOs only"),
    ]
    for var, source, desc in computed:
        lines.append(f"| `{var}` | {source} | {desc} |")
    lines.append("")

    output_path = os.path.join(DOCS_DIR, "reference", "defs-reference.md")
    with open(output_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Generated {output_path}")


if __name__ == "__main__":
    print("Generating documentation pages...")
    generate_supported_os()
    generate_defs_reference()
    print("Done.")
