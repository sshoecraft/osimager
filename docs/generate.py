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


DOCS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(DOCS_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, "osimager", "data")
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


def _classify_sources(all_sources, dist):
    """Classify installer type from source file list."""
    source_str = " ".join(all_sources).lower()
    if "kickstart" in source_str or "ks-part" in source_str:
        return "kickstart"
    elif "preseed" in source_str or ".seed" in source_str:
        return "preseed"
    elif "cloud-init" in source_str or "user-data" in source_str:
        return "cloud-init"
    elif "autoinst" in source_str or "autoyast" in source_str:
        return "autoyast"
    elif "autounattend" in source_str:
        return "autounattend"
    elif "debian" in source_str:
        return "preseed"
    elif dist in ("esxi",):
        return "kickstart"
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

    return "none"


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


# Distribution display names
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
    "sysvr4": "System V Release 4",
    "windows": "Windows",
    "windows-server": "Windows Server",
}

# Ordered list of distributions for display
DIST_ORDER = [
    "rhel", "alma", "rocky", "centos", "oel",
    "debian", "ubuntu", "sles",
    "esxi", "sysvr4",
    "windows-server",
]


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
    for spec_name in DIST_ORDER:
        spec_path = os.path.join(SPECS_DIR, spec_name, "spec.json")
        if not os.path.exists(spec_path):
            continue
        spec_data = load_json(spec_path)
        provides = spec_data.get("provides", {})
        if not provides:
            continue

        dist = provides.get("dist", spec_name)
        version_strings = provides.get("versions", [])
        arches = provides.get("arches", [])

        versions = expand_versions(version_strings)
        platforms = get_platforms_for_spec(spec_data, spec_name)
        include_chain = get_include_chain(spec_data)
        installer = get_installer_type(spec_data, dist)
        clouds = detect_cloud_support(spec_data)

        # Count specs (version x arch)
        spec_count = len(versions) * len(arches)
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
        local_plats = [p for p in d["platforms"] if p in ("virtualbox", "vmware", "qemu", "libvirt", "hyperv", "xenserver")]
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

    # Load all.json defaults
    all_data = load_json(os.path.join(PLATFORMS_DIR, "all.json"))
    all_defs = all_data.get("defs", {})

    lines.append("## Base Defaults (all.json)")
    lines.append("")
    lines.append("These defaults are inherited by all platforms:")
    lines.append("")
    lines.append("| Variable | Default Value |")
    lines.append("|----------|--------------|")
    for key, val in sorted(all_defs.items()):
        lines.append(f"| `{key}` | `{val}` |")
    lines.append("")

    # Categorize platforms
    local_platforms = ["virtualbox", "vmware", "qemu", "libvirt", "hyperv", "xenserver"]
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
                    source = "all.json default" if var in all_defs else "location" if var in (
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
