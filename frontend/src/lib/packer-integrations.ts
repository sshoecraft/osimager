/**
 * Packer Integration Definitions.
 * 
 * Comprehensive list of HashiCorp Packer integrations with their configuration schemas.
 */

export interface PackerIntegration {
  id: string;
  name: string;
  type: 'official' | 'partner' | 'community';
  category: 'cloud' | 'virtualization' | 'container' | 'bare-metal';
  description: string;
  documentation: string;
  fields: PackerField[];
  requiredFields: string[];
  defaultConfig?: Record<string, any>;
}

export interface PackerField {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'array' | 'object' | 'select' | 'multiselect';
  label: string;
  description: string;
  required: boolean;
  default?: any;
  options?: Array<{ label: string; value: any }>;
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    message?: string;
  };
  group?: string;
  dependsOn?: string;
  helpText?: string;
  placeholder?: string;
}

// Comprehensive Packer Integration definitions
export const PACKER_INTEGRATIONS: PackerIntegration[] = [
  // ============================================
  // VIRTUALIZATION PLATFORMS
  // ============================================
  {
    id: 'vmware-iso',
    name: 'VMware ISO',
    type: 'official',
    category: 'virtualization',
    description: 'Creates VMs from ISO on VMware Workstation/Player/Fusion',
    documentation: 'https://developer.hashicorp.com/packer/integrations/hashicorp/vmware',
    requiredFields: ['type', 'iso_url', 'iso_checksum', 'ssh_username'],
    defaultConfig: {
      type: 'vmware-iso',
      headless: false,
      keep_registered: true,
      skip_export: true
    },
    fields: [
      {
        name: 'type',
        type: 'string',
        label: 'Builder Type',
        description: 'Packer builder type',
        required: true,
        default: 'vmware-iso',
        group: 'Basic'
      },
      // VM Configuration
      {
        name: 'vm_name',
        type: 'string',
        label: 'VM Name',
        description: 'Name of the virtual machine',
        required: false,
        default: '>>name<<',
        placeholder: 'packer-vm',
        group: 'VM Settings'
      },
      {
        name: 'guest_os_type',
        type: 'select',
        label: 'Guest OS Type',
        description: 'Guest operating system type',
        required: false,
        options: [
          { label: 'Other Linux (64-bit)', value: 'other-64' },
          { label: 'Ubuntu (64-bit)', value: 'ubuntu-64' },
          { label: 'CentOS (64-bit)', value: 'centos-64' },
          { label: 'Red Hat (64-bit)', value: 'rhel-64' },
          { label: 'Windows Server 2019', value: 'windows2019srv-64' },
          { label: 'Windows 10 (64-bit)', value: 'windows10-64' }
        ],
        group: 'VM Settings'
      },
      {
        name: 'cpus',
        type: 'number',
        label: 'CPU Count',
        description: 'Number of virtual CPUs',
        required: false,
        default: '#>cpu_sockets*cpu_cores<#',
        validation: { min: 1, max: 32 },
        group: 'Hardware'
      },
      {
        name: 'cores',
        type: 'number',
        label: 'CPU Cores',
        description: 'Number of cores per CPU',
        required: false,
        default: '#>cpu_cores<#',
        validation: { min: 1, max: 16 },
        group: 'Hardware'
      },
      {
        name: 'memory',
        type: 'number',
        label: 'Memory (MB)',
        description: 'RAM in megabytes',
        required: false,
        default: '#>memory<#',
        validation: { min: 512, max: 65536 },
        group: 'Hardware'
      },
      {
        name: 'disk_size',
        type: 'number',
        label: 'Disk Size (MB)',
        description: 'Primary disk size in megabytes',
        required: false,
        default: '#>boot_disk_size<#',
        validation: { min: 1024 },
        group: 'Storage'
      },
      {
        name: 'disk_adapter_type',
        type: 'select',
        label: 'Disk Adapter Type',
        description: 'Virtual disk adapter type',
        required: false,
        options: [
          { label: 'SCSI', value: 'scsi' },
          { label: 'IDE', value: 'ide' },
          { label: 'SATA', value: 'sata' }
        ],
        default: 'scsi',
        group: 'Storage'
      },
      // ISO Configuration
      {
        name: 'iso_url',
        type: 'string',
        label: 'ISO URL',
        description: 'URL or path to the OS ISO file',
        required: true,
        default: "E>'>>iso_path<<>>iso_name<<' if >>local_only<< else '>>iso_url<<'<E",
        placeholder: 'https://releases.ubuntu.com/22.04/ubuntu-22.04-server-amd64.iso',
        group: 'ISO'
      },
      {
        name: 'iso_checksum',
        type: 'string',
        label: 'ISO Checksum',
        description: 'Checksum of the ISO file (sha256:hash)',
        required: true,
        default: "E>'>>iso_checksum<<' if len('>>iso_checksum<<') else 'none'<E",
        placeholder: 'sha256:84aeaf7823c8c61baa0ae862d0a06b03409394800000b3235854a6b38eb4856f',
        group: 'ISO'
      },
      // Output Configuration
      {
        name: 'output_directory',
        type: 'string',
        label: 'Output Directory',
        description: 'Directory where VM files will be stored',
        required: false,
        default: '>>vms_path<</vmware/>>name<<',
        placeholder: './output-vmware',
        group: 'Output'
      },
      {
        name: 'headless',
        type: 'boolean',
        label: 'Headless Mode',
        description: 'Run VM without GUI',
        required: false,
        default: false,
        group: 'Display'
      },
      // Advanced Options
      {
        name: 'vnc_disable_password',
        type: 'boolean',
        label: 'Disable VNC Password',
        description: 'Disable VNC password protection',
        required: false,
        default: true,
        group: 'Advanced'
      },
      {
        name: 'skip_export',
        type: 'boolean',
        label: 'Skip Export',
        description: 'Skip exporting the VM',
        required: false,
        default: true,
        group: 'Advanced'
      },
      {
        name: 'keep_registered',
        type: 'boolean',
        label: 'Keep Registered',
        description: 'Keep VM registered after build',
        required: false,
        default: true,
        group: 'Advanced'
      }
    ]
  },

  // ============================================
  // VSPHERE
  // ============================================
  {
    id: 'vsphere-iso',
    name: 'VMware vSphere ISO',
    type: 'official',
    category: 'virtualization',
    description: 'Creates VMs from ISO on VMware vSphere/ESXi',
    documentation: 'https://developer.hashicorp.com/packer/integrations/hashicorp/vsphere',
    requiredFields: ['type', 'vcenter_server', 'username', 'password', 'datacenter', 'iso_url', 'iso_checksum'],
    defaultConfig: {
      type: 'vsphere-iso',
      insecure_connection: true,
      convert_to_template: false
    },
    fields: [
      // Connection Settings
      {
        name: 'vcenter_server',
        type: 'string',
        label: 'vCenter Server',
        description: 'vCenter server hostname or IP',
        required: true,
        placeholder: 'vcenter.example.com',
        group: 'Connection'
      },
      {
        name: 'username',
        type: 'string',
        label: 'Username',
        description: 'vSphere username',
        required: true,
        placeholder: 'administrator@vsphere.local',
        group: 'Connection'
      },
      {
        name: 'password',
        type: 'string',
        label: 'Password',
        description: 'vSphere password',
        required: true,
        group: 'Connection'
      },
      {
        name: 'insecure_connection',
        type: 'boolean',
        label: 'Insecure Connection',
        description: 'Skip SSL certificate verification',
        required: false,
        default: true,
        group: 'Connection'
      },
      // vSphere Resources
      {
        name: 'datacenter',
        type: 'string',
        label: 'Datacenter',
        description: 'vSphere datacenter name',
        required: true,
        default: '>>datacenter<<',
        group: 'Resources'
      },
      {
        name: 'cluster',
        type: 'string',
        label: 'Cluster',
        description: 'vSphere cluster name',
        required: false,
        default: '>>cluster<<',
        group: 'Resources'
      },
      {
        name: 'datastore',
        type: 'string',
        label: 'Datastore',
        description: 'vSphere datastore name',
        required: true,
        default: '>>datastore<<',
        group: 'Resources'
      },
      {
        name: 'folder',
        type: 'string',
        label: 'VM Folder',
        description: 'vSphere folder for the VM',
        required: false,
        default: '>>folder<<',
        group: 'Resources'
      },
      // VM Configuration
      {
        name: 'vm_name',
        type: 'string',
        label: 'VM Name',
        description: 'Name of the virtual machine',
        required: false,
        default: '>>name<<',
        group: 'VM Settings'
      },
      {
        name: 'CPUs',
        type: 'number',
        label: 'CPU Count',
        description: 'Number of virtual CPUs',
        required: false,
        default: '#>cpu_sockets*cpu_cores<#',
        validation: { min: 1, max: 128 },
        group: 'Hardware'
      },
      {
        name: 'cpu_cores',
        type: 'number',
        label: 'CPU Cores per Socket',
        description: 'Cores per CPU socket (0 for topology assignment)',
        required: false,
        default: 0,
        validation: { min: 0, max: 64 },
        group: 'Hardware'
      },
      {
        name: 'RAM',
        type: 'number',
        label: 'Memory (MB)',
        description: 'RAM in megabytes',
        required: false,
        default: '#>memory<#',
        validation: { min: 512 },
        group: 'Hardware'
      },
      {
        name: 'firmware',
        type: 'select',
        label: 'Firmware',
        description: 'VM firmware type',
        required: false,
        options: [
          { label: 'BIOS', value: 'bios' },
          { label: 'EFI', value: 'efi' }
        ],
        default: '>>firmware<<',
        group: 'Hardware'
      },
      // Network Configuration
      {
        name: 'network_adapters',
        type: 'array',
        label: 'Network Adapters',
        description: 'Network adapter configuration',
        required: false,
        group: 'Network'
      },
      // Storage Configuration
      {
        name: 'storage',
        type: 'array',
        label: 'Storage Configuration',
        description: 'Disk configuration',
        required: false,
        group: 'Storage'
      },
      {
        name: 'disk_controller_type',
        type: 'select',
        label: 'Disk Controller Type',
        description: 'Storage controller type',
        required: false,
        options: [
          { label: 'PVSCSI', value: 'pvscsi' },
          { label: 'LSI Logic', value: 'lsilogic' },
          { label: 'LSI Logic SAS', value: 'lsilogic-sas' }
        ],
        default: 'pvscsi',
        group: 'Storage'
      },
      // Template Options
      {
        name: 'convert_to_template',
        type: 'boolean',
        label: 'Convert to Template',
        description: 'Convert VM to template after build',
        required: false,
        default: false,
        group: 'Output'
      }
    ]
  },

  // ============================================
  // VIRTUALBOX
  // ============================================
  {
    id: 'virtualbox-iso',
    name: 'VirtualBox ISO',
    type: 'official',
    category: 'virtualization',
    description: 'Creates VMs from ISO on Oracle VirtualBox',
    documentation: 'https://developer.hashicorp.com/packer/integrations/hashicorp/virtualbox',
    requiredFields: ['type', 'iso_url', 'iso_checksum', 'ssh_username'],
    defaultConfig: {
      type: 'virtualbox-iso',
      headless: true,
      guest_additions_mode: 'disable'
    },
    fields: [
      {
        name: 'type',
        type: 'string',
        label: 'Builder Type',
        description: 'Packer builder type',
        required: true,
        default: 'virtualbox-iso',
        group: 'Basic'
      },
      {
        name: 'vm_name',
        type: 'string',
        label: 'VM Name',
        description: 'Name of the virtual machine',
        required: false,
        default: '>>name<<',
        group: 'VM Settings'
      },
      {
        name: 'guest_os_type',
        type: 'select',
        label: 'Guest OS Type',
        description: 'VirtualBox guest OS type',
        required: false,
        options: [
          { label: 'Ubuntu (64-bit)', value: 'Ubuntu_64' },
          { label: 'Red Hat (64-bit)', value: 'RedHat_64' },
          { label: 'CentOS (64-bit)', value: 'RedHat_64' },
          { label: 'Windows 10 (64-bit)', value: 'Windows10_64' },
          { label: 'Windows Server 2019', value: 'Windows2019_64' }
        ],
        group: 'VM Settings'
      },
      {
        name: 'cpus',
        type: 'number',
        label: 'CPU Count',
        description: 'Number of virtual CPUs',
        required: false,
        default: '#>cpu_sockets*cpu_cores<#',
        validation: { min: 1, max: 32 },
        group: 'Hardware'
      },
      {
        name: 'memory',
        type: 'number',
        label: 'Memory (MB)',
        description: 'RAM in megabytes',
        required: false,
        default: '#>memory<#',
        validation: { min: 512 },
        group: 'Hardware'
      },
      {
        name: 'disk_size',
        type: 'number',
        label: 'Disk Size (MB)',
        description: 'Primary disk size in megabytes',
        required: false,
        default: '#>boot_disk_size<#',
        validation: { min: 1024 },
        group: 'Storage'
      },
      {
        name: 'hard_drive_interface',
        type: 'select',
        label: 'Hard Drive Interface',
        description: 'Virtual disk interface type',
        required: false,
        options: [
          { label: 'IDE', value: 'ide' },
          { label: 'SATA', value: 'sata' },
          { label: 'SCSI', value: 'scsi' },
          { label: 'VirtIO', value: 'virtio' }
        ],
        default: 'sata',
        group: 'Storage'
      },
      {
        name: 'headless',
        type: 'boolean',
        label: 'Headless Mode',
        description: 'Run VM without GUI',
        required: false,
        default: true,
        group: 'Display'
      },
      {
        name: 'guest_additions_mode',
        type: 'select',
        label: 'Guest Additions Mode',
        description: 'VirtualBox Guest Additions installation mode',
        required: false,
        options: [
          { label: 'Disable', value: 'disable' },
          { label: 'Upload', value: 'upload' },
          { label: 'Attach', value: 'attach' }
        ],
        default: 'disable',
        group: 'Advanced'
      }
    ]
  },

  // ============================================
  // QEMU
  // ============================================
  {
    id: 'qemu',
    name: 'QEMU',
    type: 'official',
    category: 'virtualization',
    description: 'Creates VMs using QEMU/KVM',
    documentation: 'https://developer.hashicorp.com/packer/integrations/hashicorp/qemu',
    requiredFields: ['type', 'iso_url', 'iso_checksum', 'ssh_username'],
    defaultConfig: {
      type: 'qemu',
      accelerator: 'kvm',
      format: 'qcow2'
    },
    fields: [
      {
        name: 'type',
        type: 'string',
        label: 'Builder Type',
        description: 'Packer builder type',
        required: true,
        default: 'qemu',
        group: 'Basic'
      },
      {
        name: 'accelerator',
        type: 'select',
        label: 'Accelerator',
        description: 'QEMU accelerator type',
        required: false,
        options: [
          { label: 'KVM', value: 'kvm' },
          { label: 'TCG', value: 'tcg' },
          { label: 'Xen', value: 'xen' }
        ],
        default: 'kvm',
        group: 'VM Settings'
      },
      {
        name: 'vm_name',
        type: 'string',
        label: 'VM Name',
        description: 'Name of the virtual machine',
        required: false,
        default: '>>name<<',
        group: 'VM Settings'
      },
      {
        name: 'memory',
        type: 'number',
        label: 'Memory (MB)',
        description: 'RAM in megabytes',
        required: false,
        default: '#>memory<#',
        validation: { min: 512 },
        group: 'Hardware'
      },
      {
        name: 'cpus',
        type: 'number',
        label: 'CPU Count',
        description: 'Number of virtual CPUs',
        required: false,
        default: '#>cpu_sockets*cpu_cores<#',
        validation: { min: 1, max: 256 },
        group: 'Hardware'
      },
      {
        name: 'disk_size',
        type: 'string',
        label: 'Disk Size',
        description: 'Primary disk size (e.g., 20G)',
        required: false,
        default: '>>boot_disk_size<<M',
        placeholder: '20G',
        group: 'Storage'
      },
      {
        name: 'format',
        type: 'select',
        label: 'Disk Format',
        description: 'Output disk format',
        required: false,
        options: [
          { label: 'QCOW2', value: 'qcow2' },
          { label: 'RAW', value: 'raw' },
          { label: 'VDI', value: 'vdi' },
          { label: 'VMDK', value: 'vmdk' }
        ],
        default: 'qcow2',
        group: 'Storage'
      },
      {
        name: 'disk_interface',
        type: 'select',
        label: 'Disk Interface',
        description: 'Virtual disk interface',
        required: false,
        options: [
          { label: 'VirtIO', value: 'virtio' },
          { label: 'IDE', value: 'ide' },
          { label: 'SCSI', value: 'scsi' }
        ],
        default: 'virtio',
        group: 'Storage'
      },
      {
        name: 'net_device',
        type: 'select',
        label: 'Network Device',
        description: 'Network interface type',
        required: false,
        options: [
          { label: 'VirtIO-Net', value: 'virtio-net' },
          { label: 'E1000', value: 'e1000' },
          { label: 'RTL8139', value: 'rtl8139' }
        ],
        default: 'virtio-net',
        group: 'Network'
      }
    ]
  },

  // ============================================
  // CLOUD PLATFORMS
  // ============================================
  {
    id: 'amazon-ebs',
    name: 'Amazon EBS',
    type: 'official',
    category: 'cloud',
    description: 'Creates AMIs on Amazon Web Services',
    documentation: 'https://developer.hashicorp.com/packer/integrations/hashicorp/amazon',
    requiredFields: ['type', 'region', 'source_ami', 'instance_type', 'ssh_username', 'ami_name'],
    defaultConfig: {
      type: 'amazon-ebs',
      encrypt_boot: false
    },
    fields: [
      {
        name: 'type',
        type: 'string',
        label: 'Builder Type',
        description: 'Packer builder type',
        required: true,
        default: 'amazon-ebs',
        group: 'Basic'
      },
      {
        name: 'region',
        type: 'select',
        label: 'AWS Region',
        description: 'AWS region for the build',
        required: true,
        options: [
          { label: 'US East (N. Virginia)', value: 'us-east-1' },
          { label: 'US East (Ohio)', value: 'us-east-2' },
          { label: 'US West (Oregon)', value: 'us-west-2' },
          { label: 'US West (N. California)', value: 'us-west-1' },
          { label: 'Europe (Ireland)', value: 'eu-west-1' },
          { label: 'Europe (London)', value: 'eu-west-2' },
          { label: 'Asia Pacific (Tokyo)', value: 'ap-northeast-1' },
          { label: 'Asia Pacific (Singapore)', value: 'ap-southeast-1' }
        ],
        group: 'AWS Settings'
      },
      {
        name: 'source_ami',
        type: 'string',
        label: 'Source AMI',
        description: 'AMI ID to use as base image',
        required: true,
        placeholder: 'ami-0abcdef1234567890',
        group: 'AWS Settings'
      },
      {
        name: 'instance_type',
        type: 'select',
        label: 'Instance Type',
        description: 'EC2 instance type for building',
        required: true,
        options: [
          { label: 't3.micro', value: 't3.micro' },
          { label: 't3.small', value: 't3.small' },
          { label: 't3.medium', value: 't3.medium' },
          { label: 't3.large', value: 't3.large' },
          { label: 'm5.large', value: 'm5.large' },
          { label: 'm5.xlarge', value: 'm5.xlarge' },
          { label: 'c5.large', value: 'c5.large' },
          { label: 'c5.xlarge', value: 'c5.xlarge' }
        ],
        default: 't3.micro',
        group: 'AWS Settings'
      },
      {
        name: 'ami_name',
        type: 'string',
        label: 'AMI Name',
        description: 'Name for the created AMI',
        required: true,
        default: '>>name<<-{{timestamp}}',
        placeholder: 'my-custom-ami-{{timestamp}}',
        group: 'Output'
      },
      {
        name: 'ami_description',
        type: 'string',
        label: 'AMI Description',
        description: 'Description for the created AMI',
        required: false,
        placeholder: 'Custom AMI built with Packer',
        group: 'Output'
      }
    ]
  },

  // ============================================
  // CONTAINER PLATFORMS
  // ============================================
  {
    id: 'docker',
    name: 'Docker',
    type: 'official',
    category: 'container',
    description: 'Creates Docker container images',
    documentation: 'https://developer.hashicorp.com/packer/integrations/hashicorp/docker',
    requiredFields: ['type', 'image'],
    defaultConfig: {
      type: 'docker',
      pull: true
    },
    fields: [
      {
        name: 'type',
        type: 'string',
        label: 'Builder Type',
        description: 'Packer builder type',
        required: true,
        default: 'docker',
        group: 'Basic'
      },
      {
        name: 'image',
        type: 'string',
        label: 'Base Image',
        description: 'Docker base image to use',
        required: true,
        placeholder: 'ubuntu:22.04',
        group: 'Docker Settings'
      },
      {
        name: 'pull',
        type: 'boolean',
        label: 'Pull Image',
        description: 'Pull the latest version of the base image',
        required: false,
        default: true,
        group: 'Docker Settings'
      },
      {
        name: 'commit',
        type: 'boolean',
        label: 'Commit Container',
        description: 'Commit the container to an image',
        required: false,
        default: true,
        group: 'Output'
      },
      {
        name: 'export_path',
        type: 'string',
        label: 'Export Path',
        description: 'Path to export container as tar file',
        required: false,
        placeholder: './docker-image.tar',
        group: 'Output'
      }
    ]
  }
];

// Helper function to get integration by ID
export function getPackerIntegration(id: string): PackerIntegration | undefined {
  return PACKER_INTEGRATIONS.find(integration => integration.id === id);
}

// Helper function to get integrations by category
export function getPackerIntegrationsByCategory(category: string): PackerIntegration[] {
  return PACKER_INTEGRATIONS.filter(integration => integration.category === category);
}

// Helper function to get all integration IDs for dropdown
export function getPackerIntegrationOptions() {
  return PACKER_INTEGRATIONS.map(integration => ({
    label: integration.name,
    value: integration.id,
    description: integration.description,
    category: integration.category,
    type: integration.type
  }));
}