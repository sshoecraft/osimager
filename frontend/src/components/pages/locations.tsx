/**
 * Location management page.
 * 
 * Provides comprehensive location CRUD operations with a modern interface.
 */

import React, { useState, useMemo, useEffect } from 'react';
import { 
  Plus, 
  Search, 
  Filter, 
  MapPin, 
  Edit, 
  Trash2, 
  Eye, 
  FileText, 
  Clock,
  Network,
  Globe,
  Copy,
  Download,
  Upload,
  AlertTriangle,
  Shield
} from 'lucide-react';
import { 
  useLocationsDetailed, 
  useDeleteLocation,
  useCreateLocation,
  useUpdateLocation,
  locationKeys 
} from '@/hooks/use-locations';
import type { LocationInfo } from '@/types/api';

// Location type icons mapping
const LocationIcons: Record<string, React.ReactNode> = {
  'dev': <MapPin className="w-4 h-4 text-blue-600" />,
  'lab': <Network className="w-4 h-4 text-green-600" />,
  'production': <Globe className="w-4 h-4 text-orange-600" />,
  'local': <MapPin className="w-4 h-4 text-purple-600" />,
  'pnet': <Network className="w-4 h-4 text-red-600" />,
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

// Location card component
interface LocationCardProps {
  location: LocationInfo;
  onEdit: (location: LocationInfo) => void;
  onView: (location: LocationInfo) => void;
  onDelete: (location: LocationInfo) => void;
  onDuplicate: (location: LocationInfo) => void;
}

function LocationCard({ location, onEdit, onView, onDelete, onDuplicate }: LocationCardProps) {
  const [showActions, setShowActions] = useState(false);
  const icon = LocationIcons[location.type] || LocationIcons.unknown;
  const isCorelocation = location.name === 'all';

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
      {/* Location header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          {icon}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              {location.name}
              {isCorelocation && (
                <Shield className="w-4 h-4 ml-2 text-blue-600" title="Core location" />
              )}
            </h3>
            <p className="text-sm text-gray-500 capitalize">{location.type}</p>
          </div>
        </div>
        
        {/* Action buttons */}
        <div className={`flex items-center space-x-1 transition-opacity duration-200 ${
          showActions ? 'opacity-100' : 'opacity-0'
        }`}>
          <button
            onClick={() => onView(location)}
            className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            title="View details"
          >
            <Eye className="w-4 h-4" />
          </button>
          <button
            onClick={() => onEdit(location)}
            className="p-2 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
            title="Edit location"
          >
            <Edit className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDuplicate(location)}
            className="p-2 text-gray-500 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
            title="Duplicate location"
          >
            <Copy className="w-4 h-4" />
          </button>
          {!isCorelocation && (
            <button
              onClick={() => onDelete(location)}
              className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              title="Delete location"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Location description */}
      {location.description && (
        <p className="text-sm text-gray-600 mb-4 line-clamp-2">
          {location.description}
        </p>
      )}

      {/* Location metadata */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-gray-500">Size:</span>
          <span className="ml-2 text-gray-900">{formatFileSize(location.size)}</span>
        </div>
        <div>
          <span className="text-gray-500">Modified:</span>
          <span className="ml-2 text-gray-900">{formatDate(location.modified)}</span>
        </div>
        {location.include && (
          <div className="col-span-2">
            <span className="text-gray-500">Includes:</span>
            <span className="ml-2 text-gray-900">{location.include}</span>
          </div>
        )}
        {location.arches.length > 0 && (
          <div className="col-span-2">
            <span className="text-gray-500">Architectures:</span>
            <span className="ml-2 text-gray-900">{location.arches.join(', ')}</span>
          </div>
        )}
      </div>

      {/* Core location indicator */}
      {isCorelocation && (
        <div className="absolute top-3 right-3">
          <div className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
            Core
          </div>
        </div>
      )}
    </div>
  );
}

// Location editor modal/dialog would go here
interface LocationEditorProps {
  location?: LocationInfo;
  isOpen: boolean;
  onClose: () => void;
  onSave: (location: any) => void;
  mode: 'create' | 'edit' | 'view' | 'duplicate';
  isLoading?: boolean;
}

function LocationEditor({ location, isOpen, onClose, onSave, mode, isLoading = false }: LocationEditorProps) {
  const [config, setConfig] = useState<Record<string, any>>({});
  const [description, setDescription] = useState('');
  const [type, setType] = useState('dev');
  const [include, setInclude] = useState('all');
  const [defs, setDefs] = useState<Record<string, any>>({});
  const [name, setName] = useState('');
  const [errors, setErrors] = useState<string[]>([]);
  const [configError, setConfigError] = useState<string>('');

  // Initialize form data when location or mode changes
  useEffect(() => {
    if (isOpen) {
      if (location && (mode === 'edit' || mode === 'view' || mode === 'duplicate')) {
        // OSImager location structure: { include, arches, defs, config: { type, ...packerConfig } }
        const locationConfig = location.config || {};
        const locationType = locationConfig.type || location.type || 'dev';
        
        setName(mode === 'duplicate' ? `${location.name}-copy` : location.name);
        setDescription(location.description || '');
        setInclude(location.include || 'all');
        setDefs(location.defs || {});
        setConfig(locationConfig);
        setType(locationType);
      } else {
        // New location - set defaults
        setName('');
        setDescription('');
        setInclude('all');
        setDefs({});
        setConfig({ type: 'dev' });
        setType('dev');
      }
      setErrors([]);
      setConfigError('');
    }
  }, [isOpen, location, mode]);

  if (!isOpen) return null;

  const isReadOnly = mode === 'view';
  const isCreate = mode === 'create' || mode === 'duplicate';

  const handleSave = () => {
    const validationErrors: string[] = [];
    
    // Validate required fields
    if (!name.trim()) {
      validationErrors.push('Location name is required');
    }
    
    if (!type) {
      validationErrors.push('Location type is required');
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
    
    const locationData = {
      name: name.trim(),
      description: description.trim(),
      type,  // Keep type at root for compatibility
      config: finalConfig,  // Packer config with type
      include,
      defs
    };
    
    setErrors([]);
    onSave(locationData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-4xl h-5/6 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">
            {mode === 'create' && 'Create Location'}
            {mode === 'edit' && 'Edit Location'}
            {mode === 'view' && 'View Location'}
            {mode === 'duplicate' && 'Duplicate Location'}
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
                  Location Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  disabled={isReadOnly || (!isCreate && location?.name === 'all')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                  placeholder="Enter location name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Location Type
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
                  <option value="dev">VMware ISO</option>
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
                  Include Base Location
                </label>
                <input
                  type="text"
                  value={include}
                  onChange={(e) => setInclude(e.target.value)}
                  disabled={isReadOnly}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                  placeholder="Base location to include"
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
                  placeholder="Location description"
                />
              </div>
            </div>

            {/* Configuration JSON Editor */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Location Configuration
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
                placeholder="Location configuration in JSON format"
              />
            </div>

            {/* Definitions JSON Editor */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Location Definitions
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
                placeholder="Location definitions in JSON format"
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
                : (isCreate ? 'Create Location' : 'Save Changes')
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
  location?: LocationInfo;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  isLoading: boolean;
}

function DeleteConfirmation({ location, isOpen, onClose, onConfirm, isLoading }: DeleteConfirmationProps) {
  if (!isOpen || !location) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <div className="flex items-center mb-4">
          <AlertTriangle className="w-6 h-6 text-red-600 mr-3" />
          <h3 className="text-lg font-semibold text-gray-900">Delete Location</h3>
        </div>
        
        <p className="text-gray-600 mb-6">
          Are you sure you want to delete the location <strong>{location.name}</strong>? 
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
            {isLoading ? 'Deleting...' : 'Delete Location'}
          </button>
        </div>
      </div>
    </div>
  );
}

// Main locations page component
export function LocationsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [editingLocation, setEditingLocation] = useState<LocationInfo | undefined>();
  const [editorMode, setEditorMode] = useState<'create' | 'edit' | 'view' | 'duplicate'>('view');
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [deletingLocation, setDeletingLocation] = useState<LocationInfo | undefined>();
  
  const { data: locationsData, isLoading, error } = useLocationsDetailed();
  const deleteMutation = useDeleteLocation();
  const createMutation = useCreateLocation();
  const updateMutation = useUpdateLocation();

  const locations = locationsData?.locations || [];

  // Filter locations based on search and type
  const filteredLocations = useMemo(() => {
    return locations.filter(location => {
      const matchesSearch = location.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           location.description.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesType = typeFilter === 'all' || location.type === typeFilter;
      return matchesSearch && matchesType;
    });
  }, [locations, searchTerm, typeFilter]);

  // Get unique location types for filter
  const locationTypes = useMemo(() => {
    const types = new Set(locations.map(p => p.type));
    return Array.from(types).sort();
  }, [locations]);

  const handleCreateLocation = () => {
    setEditingLocation(undefined);
    setEditorMode('create');
    setIsEditorOpen(true);
  };

  const handleEditLocation = (location: LocationInfo) => {
    setEditingLocation(location);
    setEditorMode('edit');
    setIsEditorOpen(true);
  };

  const handleViewLocation = (location: LocationInfo) => {
    setEditingLocation(location);
    setEditorMode('view');
    setIsEditorOpen(true);
  };

  const handleDuplicateLocation = (location: LocationInfo) => {
    setEditingLocation(location);
    setEditorMode('duplicate');
    setIsEditorOpen(true);
  };

  const handleDeleteLocation = (location: LocationInfo) => {
    setDeletingLocation(location);
  };

  const confirmDelete = async () => {
    if (deletingLocation) {
      await deleteMutation.mutateAsync(deletingLocation.name);
      setDeletingLocation(undefined);
    }
  };

  const handleSaveLocation = async (locationData: any) => {
    try {
      if (editorMode === 'create' || editorMode === 'duplicate') {
        await createMutation.mutateAsync(locationData);
      } else if (editorMode === 'edit') {
        const { name, ...updateData } = locationData;
        await updateMutation.mutateAsync({ 
          name: editingLocation!.name, 
          location: updateData 
        });
      }
      setIsEditorOpen(false);
      setEditingLocation(undefined);
    } catch (error) {
      console.error('Error saving location:', error);
      // Error handling will be shown by the mutations
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Locations</h1>
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
          <h1 className="text-3xl font-bold text-gray-900">Locations</h1>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center">
            <AlertTriangle className="w-5 h-5 text-red-600 mr-3" />
            <h3 className="text-lg font-medium text-red-800">Error Loading Locations</h3>
          </div>
          <p className="text-red-700 mt-2">
            {error.message || 'Failed to load locations. Please try again.'}
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
          <h1 className="text-3xl font-bold text-gray-900">Locations</h1>
          <p className="text-gray-600 mt-1">
            Manage virtualization location configurations
          </p>
        </div>
        <button
          onClick={handleCreateLocation}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Location
        </button>
      </div>

      {/* Stats and search */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="grid grid-cols-3 gap-6">
            <div>
              <p className="text-sm text-gray-500">Total Locations</p>
              <p className="text-2xl font-semibold text-gray-900">{locations.length}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Location Types</p>
              <p className="text-2xl font-semibold text-gray-900">{locationTypes.length}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Filtered Results</p>
              <p className="text-2xl font-semibold text-gray-900">{filteredLocations.length}</p>
            </div>
          </div>
        </div>

        {/* Search and filters */}
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search locations..."
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
              {locationTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Locations grid */}
      {filteredLocations.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <MapPin className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No locations found</h3>
          <p className="text-gray-600 mb-6">
            {searchTerm || typeFilter !== 'all' 
              ? 'No locations match your current filters.'
              : 'Get started by creating your first location.'
            }
          </p>
          {(!searchTerm && typeFilter === 'all') && (
            <button
              onClick={handleCreateLocation}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors mx-auto"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Location
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredLocations.map((location) => (
            <LocationCard
              key={location.name}
              location={location}
              onEdit={handleEditLocation}
              onView={handleViewLocation}
              onDelete={handleDeleteLocation}
              onDuplicate={handleDuplicateLocation}
            />
          ))}
        </div>
      )}

      {/* Location Editor Modal */}
      <LocationEditor
        location={editingLocation}
        isOpen={isEditorOpen}
        onClose={() => setIsEditorOpen(false)}
        onSave={handleSaveLocation}
        mode={editorMode}
        isLoading={createMutation.isPending || updateMutation.isPending}
      />

      {/* Delete Confirmation Modal */}
      <DeleteConfirmation
        location={deletingLocation}
        isOpen={!!deletingLocation}
        onClose={() => setDeletingLocation(undefined)}
        onConfirm={confirmDelete}
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}
