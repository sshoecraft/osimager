/**
 * Platform management page.
 * 
 * Provides comprehensive platform CRUD operations with a modern interface.
 */

import React, { useState, useMemo, useEffect } from 'react';
import { 
  Plus, 
  Search, 
  Filter, 
  Server, 
  Edit, 
  Trash2, 
  Eye, 
  FileText, 
  Clock,
  Database,
  Settings,
  Copy,
  Download,
  Upload,
  AlertTriangle,
  Shield
} from 'lucide-react';
import { 
  usePlatformsDetailed, 
  useDeletePlatform,
  useCreatePlatform,
  useUpdatePlatform,
  platformKeys 
} from '@/hooks/use-platforms';
import { 
  PACKER_INTEGRATIONS,
  getPackerIntegration,
  getPackerIntegrationOptions,
  type PackerIntegration
} from '@/lib/packer-integrations';
import { PackerPlatformForm } from '@/components/ui/packer-platform-form';
import type { PlatformInfo } from '@/types/api';

// Platform type icons mapping
const PlatformIcons: Record<string, React.ReactNode> = {
  'vmware-iso': <Server className="w-4 h-4 text-blue-600" />,
  'qemu': <Database className="w-4 h-4 text-green-600" />,
  'virtualbox-iso': <Settings className="w-4 h-4 text-orange-600" />,
  'libvirt': <Server className="w-4 h-4 text-purple-600" />,
  'proxmox': <Database className="w-4 h-4 text-red-600" />,
  'vsphere': <Server className="w-4 h-4 text-blue-800" />,
  'unknown': <FileText className="w-4 h-4 text-gray-500" />,
};

// Format file size helper
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

// Format date helper
function formatDate(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// Platform card component
interface PlatformCardProps {
  platform: PlatformInfo;
  onEdit: (platform: PlatformInfo) => void;
  onView: (platform: PlatformInfo) => void;
  onDelete: (platform: PlatformInfo) => void;
  onDuplicate: (platform: PlatformInfo) => void;
}

function PlatformCard({ platform, onEdit, onView, onDelete, onDuplicate }: PlatformCardProps) {
  const [showActions, setShowActions] = useState(false);
  const icon = PlatformIcons[platform.type] || PlatformIcons.unknown;
  const isCoreplatform = platform.name === 'all';

  return (
    <div 
      className={`
        relative bg-white rounded-lg border border-gray-200 p-6 
        hover:border-blue-300 hover:shadow-md transition-all duration-200
        ${showActions ? 'ring-2 ring-blue-500 ring-opacity-20' : ''}
      `}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      {/* Platform header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          {icon}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              {platform.name}
              {isCoreplatform && (
                <Shield className="w-4 h-4 ml-2 text-blue-600" title="Core platform" />
              )}
            </h3>
            <p className="text-sm text-gray-500 capitalize">{platform.type}</p>
          </div>
        </div>
        
        {/* Action buttons */}
        <div className={`flex items-center space-x-1 transition-opacity duration-200 ${
          showActions ? 'opacity-100' : 'opacity-0'
        }`}>
          <button
            onClick={() => onView(platform)}
            className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            title="View details"
          >
            <Eye className="w-4 h-4" />
          </button>
          <button
            onClick={() => onEdit(platform)}
            className="p-2 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
            title="Edit platform"
          >
            <Edit className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDuplicate(platform)}
            className="p-2 text-gray-500 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
            title="Duplicate platform"
          >
            <Copy className="w-4 h-4" />
          </button>
          {!isCoreplatform && (
            <button
              onClick={() => onDelete(platform)}
              className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              title="Delete platform"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Platform description */}
      {platform.description && (
        <p className="text-sm text-gray-600 mb-4 line-clamp-2">
          {platform.description}
        </p>
      )}

      {/* Platform metadata */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-gray-500">Size:</span>
          <span className="ml-2 text-gray-900">{formatFileSize(platform.size)}</span>
        </div>
        <div>
          <span className="text-gray-500">Modified:</span>
          <span className="ml-2 text-gray-900">{formatDate(platform.modified)}</span>
        </div>
        {platform.include && (
          <div className="col-span-2">
            <span className="text-gray-500">Includes:</span>
            <span className="ml-2 text-gray-900">{platform.include}</span>
          </div>
        )}
        {platform.arches.length > 0 && (
          <div className="col-span-2">
            <span className="text-gray-500">Architectures:</span>
            <span className="ml-2 text-gray-900">{platform.arches.join(', ')}</span>
          </div>
        )}
      </div>

      {/* Core platform indicator */}
      {isCoreplatform && (
        <div className="absolute top-3 right-3">
          <div className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
            Core
          </div>
        </div>
      )}
    </div>
  );
}

// Platform editor modal/dialog would go here
interface PlatformEditorProps {
  platform?: PlatformInfo;
  isOpen: boolean;
  onClose: () => void;
  onSave: (platform: any) => void;
  mode: 'create' | 'edit' | 'view' | 'duplicate';
  isLoading?: boolean;
}

function PlatformEditor({ platform, isOpen, onClose, onSave, mode, isLoading = false }: PlatformEditorProps) {
  const [config, setConfig] = useState<Record<string, any>>({});
  const [description, setDescription] = useState('');
  const [type, setType] = useState('vmware-iso');
  const [include, setInclude] = useState('all');
  const [defs, setDefs] = useState<Record<string, any>>({});
  const [name, setName] = useState('');
  const [errors, setErrors] = useState<string[]>([]);
  const [configError, setConfigError] = useState<string>('');

  // Initialize form data when platform or mode changes
  useEffect(() => {
    if (isOpen) {
      if (platform && (mode === 'edit' || mode === 'view' || mode === 'duplicate')) {
        // OSImager platform structure: { include, arches, defs, config: { type, ...packerConfig } }
        const platformConfig = platform.config || {};
        const platformType = platformConfig.type || platform.type || 'vmware-iso';
        
        setName(mode === 'duplicate' ? `${platform.name}-copy` : platform.name);
        setDescription(platform.description || '');
        setInclude(platform.include || 'all');
        setDefs(platform.defs || {});
        setConfig(platformConfig);
        setType(platformType);
      } else {
        // New platform - set defaults
        setName('');
        setDescription('');
        setInclude('all');
        setDefs({});
        setConfig({ type: 'vmware-iso' });
        setType('vmware-iso');
      }
      setErrors([]);
      setConfigError('');
    }
  }, [isOpen, platform, mode]);

  if (!isOpen) return null;

  const isReadOnly = mode === 'view';
  const isCreate = mode === 'create' || mode === 'duplicate';

  const handleSave = () => {
    const validationErrors: string[] = [];
    
    // Validate required fields
    if (!name.trim()) {
      validationErrors.push('Platform name is required');
    }
    
    if (!type) {
      validationErrors.push('Platform type is required');
    }
    
    // Validate JSON config
    if (configError) {
      validationErrors.push('Configuration JSON is invalid');
    }
    
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }
    
    // Ensure the type is set in the config
    const finalConfig = { ...config, type };
    
    const platformData = {
      name: name.trim(),
      description: description.trim(),
      type,  // Keep type at root for compatibility
      config: finalConfig,  // Packer config with type
      include,
      defs
    };
    
    setErrors([]);
    onSave(platformData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-4xl h-5/6 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">
            {mode === 'create' && 'Create Platform'}
            {mode === 'edit' && 'Edit Platform'}
            {mode === 'view' && 'View Platform'}
            {mode === 'duplicate' && 'Duplicate Platform'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 p-2"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {/* Error messages */}
          {errors.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="flex items-center mb-2">
                <AlertTriangle className="w-4 h-4 text-red-600 mr-2" />
                <h4 className="text-sm font-medium text-red-800">Please fix the following errors:</h4>
              </div>
              <ul className="text-sm text-red-700 list-disc list-inside space-y-1">
                {errors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </div>
          )}
          
          <div className="space-y-6">
            {/* Basic Information */}
            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Platform Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  disabled={isReadOnly || (!isCreate && platform?.name === 'all')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                  placeholder="Enter platform name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Platform Type
                </label>
                <select
                  value={type}
                  onChange={(e) => {
                    const newType = e.target.value;
                    setType(newType);
                    // Also update the type in the config
                    setConfig(prev => ({ ...prev, type: newType }));
                  }}
                  disabled={isReadOnly}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                >
                  <option value="vmware-iso">VMware ISO</option>
                  <option value="qemu">QEMU</option>
                  <option value="virtualbox-iso">VirtualBox ISO</option>
                  <option value="libvirt">Libvirt</option>
                  <option value="proxmox">Proxmox</option>
                  <option value="vsphere">vSphere</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Include Base Platform
                </label>
                <input
                  type="text"
                  value={include}
                  onChange={(e) => setInclude(e.target.value)}
                  disabled={isReadOnly}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                  placeholder="Base platform to include"
                />
              </div>
              <div className="col-span-1">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  disabled={isReadOnly}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                  placeholder="Platform description"
                />
              </div>
            </div>

            {/* Configuration JSON Editor */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Platform Configuration
                {configError && (
                  <span className="text-red-600 text-xs ml-2">({configError})</span>
                )}
              </label>
              <textarea
                value={JSON.stringify(config, null, 2)}
                onChange={(e) => {
                  try {
                    const parsed = JSON.parse(e.target.value);
                    setConfig(parsed);
                    setConfigError('');
                  } catch (error) {
                    setConfigError('Invalid JSON syntax');
                  }
                }}
                disabled={isReadOnly}
                rows={12}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm disabled:bg-gray-100 ${
                  configError ? 'border-red-300 bg-red-50' : 'border-gray-300'
                }`}
                placeholder="Platform configuration in JSON format"
              />
            </div>

            {/* Definitions JSON Editor */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Platform Definitions
              </label>
              <textarea
                value={JSON.stringify(defs, null, 2)}
                onChange={(e) => {
                  try {
                    setDefs(JSON.parse(e.target.value));
                  } catch {
                    // Invalid JSON, don't update
                  }
                }}
                disabled={isReadOnly}
                rows={6}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm disabled:bg-gray-100"
                placeholder="Platform definitions in JSON format"
              />
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-4 p-6 border-t">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
          >
            {isReadOnly ? 'Close' : 'Cancel'}
          </button>
          {!isReadOnly && (
            <button
              onClick={handleSave}
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center"
            >
              {isLoading && (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              )}
              {isLoading 
                ? (isCreate ? 'Creating...' : 'Saving...') 
                : (isCreate ? 'Create Platform' : 'Save Changes')
              }
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// Delete confirmation modal
interface DeleteConfirmationProps {
  platform?: PlatformInfo;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  isLoading: boolean;
}

function DeleteConfirmation({ platform, isOpen, onClose, onConfirm, isLoading }: DeleteConfirmationProps) {
  if (!isOpen || !platform) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <div className="flex items-center mb-4">
          <AlertTriangle className="w-6 h-6 text-red-600 mr-3" />
          <h3 className="text-lg font-semibold text-gray-900">Delete Platform</h3>
        </div>
        
        <p className="text-gray-600 mb-6">
          Are you sure you want to delete the platform <strong>{platform.name}</strong>? 
          This action cannot be undone.
        </p>
        
        <div className="flex items-center justify-end space-x-4">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
          >
            {isLoading ? 'Deleting...' : 'Delete Platform'}
          </button>
        </div>
      </div>
    </div>
  );
}

// Main platforms page component
export function PlatformsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [editingPlatform, setEditingPlatform] = useState<PlatformInfo | undefined>();
  const [editorMode, setEditorMode] = useState<'create' | 'edit' | 'view' | 'duplicate'>('view');
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [deletingPlatform, setDeletingPlatform] = useState<PlatformInfo | undefined>();
  
  const { data: platformsData, isLoading, error } = usePlatformsDetailed();
  const deleteMutation = useDeletePlatform();
  const createMutation = useCreatePlatform();
  const updateMutation = useUpdatePlatform();

  const platforms = platformsData?.platforms || [];

  // Filter platforms based on search and type
  const filteredPlatforms = useMemo(() => {
    return platforms.filter(platform => {
      const matchesSearch = platform.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           platform.description.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesType = typeFilter === 'all' || platform.type === typeFilter;
      return matchesSearch && matchesType;
    });
  }, [platforms, searchTerm, typeFilter]);

  // Get unique platform types for filter
  const platformTypes = useMemo(() => {
    const types = new Set(platforms.map(p => p.type));
    return Array.from(types).sort();
  }, [platforms]);

  const handleCreatePlatform = () => {
    setEditingPlatform(undefined);
    setEditorMode('create');
    setIsEditorOpen(true);
  };

  const handleEditPlatform = (platform: PlatformInfo) => {
    setEditingPlatform(platform);
    setEditorMode('edit');
    setIsEditorOpen(true);
  };

  const handleViewPlatform = (platform: PlatformInfo) => {
    setEditingPlatform(platform);
    setEditorMode('view');
    setIsEditorOpen(true);
  };

  const handleDuplicatePlatform = (platform: PlatformInfo) => {
    setEditingPlatform(platform);
    setEditorMode('duplicate');
    setIsEditorOpen(true);
  };

  const handleDeletePlatform = (platform: PlatformInfo) => {
    setDeletingPlatform(platform);
  };

  const confirmDelete = async () => {
    if (deletingPlatform) {
      await deleteMutation.mutateAsync(deletingPlatform.name);
      setDeletingPlatform(undefined);
    }
  };

  const handleSavePlatform = async (platformData: any) => {
    try {
      if (editorMode === 'create' || editorMode === 'duplicate') {
        await createMutation.mutateAsync(platformData);
      } else if (editorMode === 'edit') {
        const { name, ...updateData } = platformData;
        await updateMutation.mutateAsync({ 
          name: editingPlatform!.name, 
          platform: updateData 
        });
      }
      setIsEditorOpen(false);
      setEditingPlatform(undefined);
    } catch (error) {
      console.error('Error saving platform:', error);
      // Error handling will be shown by the mutations
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Platforms</h1>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Platforms</h1>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center">
            <AlertTriangle className="w-5 h-5 text-red-600 mr-3" />
            <h3 className="text-lg font-medium text-red-800">Error Loading Platforms</h3>
          </div>
          <p className="text-red-700 mt-2">
            {error.message || 'Failed to load platforms. Please try again.'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Platforms</h1>
          <p className="text-gray-600 mt-1">
            Manage virtualization platform configurations
          </p>
        </div>
        <button
          onClick={handleCreatePlatform}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Platform
        </button>
      </div>

      {/* Stats and search */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="grid grid-cols-3 gap-6">
            <div>
              <p className="text-sm text-gray-500">Total Platforms</p>
              <p className="text-2xl font-semibold text-gray-900">{platforms.length}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Platform Types</p>
              <p className="text-2xl font-semibold text-gray-900">{platformTypes.length}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Filtered Results</p>
              <p className="text-2xl font-semibold text-gray-900">{filteredPlatforms.length}</p>
            </div>
          </div>
        </div>

        {/* Search and filters */}
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search platforms..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Types</option>
              {platformTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Platforms grid */}
      {filteredPlatforms.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <Server className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No platforms found</h3>
          <p className="text-gray-600 mb-6">
            {searchTerm || typeFilter !== 'all' 
              ? 'No platforms match your current filters.'
              : 'Get started by creating your first platform.'
            }
          </p>
          {(!searchTerm && typeFilter === 'all') && (
            <button
              onClick={handleCreatePlatform}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors mx-auto"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Platform
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPlatforms.map((platform) => (
            <PlatformCard
              key={platform.name}
              platform={platform}
              onEdit={handleEditPlatform}
              onView={handleViewPlatform}
              onDelete={handleDeletePlatform}
              onDuplicate={handleDuplicatePlatform}
            />
          ))}
        </div>
      )}

      {/* Platform Editor Modal */}
      <PlatformEditor
        platform={editingPlatform}
        isOpen={isEditorOpen}
        onClose={() => setIsEditorOpen(false)}
        onSave={handleSavePlatform}
        mode={editorMode}
        isLoading={createMutation.isPending || updateMutation.isPending}
      />

      {/* Delete Confirmation Modal */}
      <DeleteConfirmation
        platform={deletingPlatform}
        isOpen={!!deletingPlatform}
        onClose={() => setDeletingPlatform(undefined)}
        onConfirm={confirmDelete}
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}
