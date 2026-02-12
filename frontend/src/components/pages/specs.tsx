/**
 * Specs Management page component for managing OS specifications.
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Plus,
  Search,
  Filter,
  RefreshCw,
  Edit,
  Trash2,
  FileText,
  Copy
} from 'lucide-react';
import { useSpecs, useCreateSpec, useUpdateSpec, useDeleteSpec } from '@/hooks/api-hooks';
import { LoadingState } from '@/components/ui/loading';
import { StatusBadge } from '@/components/ui/status-badge';
import { SpecEditorModal } from '@/components/ui/spec-editor-modal';
import { formatRelativeTime } from '@/lib/utils';
import type { SpecMetadata } from '@/types/api';

export function SpecsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSpec, setSelectedSpec] = useState<SpecMetadata | null>(null);
  const [editorMode, setEditorMode] = useState<'view' | 'edit' | 'create' | 'duplicate'>('edit');
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  
  // Get specs data with error handling
  const { 
    data: specsData, 
    isLoading: specsLoading, 
    error: specsError,
    refetch: refetchSpecs 
  } = useSpecs();
  
  // Mutations
  const createSpecMutation = useCreateSpec();
  const updateSpecMutation = useUpdateSpec();
  const deleteSpecMutation = useDeleteSpec();

  // Modal handlers
  const openEditor = (spec: SpecMetadata | null, mode: 'view' | 'edit' | 'create' | 'duplicate') => {
    setSelectedSpec(spec);
    setEditorMode(mode);
    setIsEditorOpen(true);
  };

  const closeEditor = () => {
    setIsEditorOpen(false);
    setSelectedSpec(null);
  };

  const handleSaveSpec = async (name: string, content: any) => {
    try {
      if (editorMode === 'create' || editorMode === 'duplicate') {
        await createSpecMutation.mutateAsync({ name, content });
      } else if (editorMode === 'edit' && selectedSpec) {
        await updateSpecMutation.mutateAsync({ name: selectedSpec.name, content });
      }
      // Refresh the specs list
      refetchSpecs();
    } catch (error) {
      throw error; // Let the modal handle the error display
    }
  };

  // Get the actual specs array from the response
  const specs = specsData?.specs || [];
  const totalSpecs = specsData?.total || specs.length;

  // Filter specs based on search
  const filteredSpecs = specs.filter(spec => 
    spec.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Show loading state
  if (specsLoading) {
    return <LoadingState message="Loading specifications..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Specifications</h1>
          <p className="text-gray-600 mt-1">
            Manage OS image specifications and configurations
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => refetchSpecs()}
            className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
            disabled={specsLoading}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${specsLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button 
            onClick={() => openEditor(null, 'create')}
            className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Spec
          </button>
        </div>
      </div>

      {/* Error state */}
      {specsError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">⚠️ Error loading specifications: {specsError.message}</p>
          <button 
            onClick={() => refetchSpecs()}
            className="mt-2 text-red-600 hover:text-red-700 text-sm underline"
          >
            Try again
          </button>
        </div>
      )}

      {/* Search */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search specifications..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Stats summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{totalSpecs}</p>
            <p className="text-sm text-gray-600">Total Specs</p>
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-primary-600">{filteredSpecs.length}</p>
            <p className="text-sm text-gray-600">Filtered Results</p>
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">{specs.length}</p>
            <p className="text-sm text-gray-600">Available</p>
          </div>
        </div>
      </div>

      {/* Specs grid */}
      {!specsError && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredSpecs.length > 0 ? (
            filteredSpecs.map(spec => (
              <SpecCard
                key={spec.name}
                spec={spec}
                onEdit={(spec) => openEditor(spec, 'edit')}
                onView={(spec) => openEditor(spec, 'view')}
                onDuplicate={(spec) => openEditor(spec, 'duplicate')}
                onDelete={async (spec) => {
                  if (confirm(`Are you sure you want to delete spec "${spec.name}"?`)) {
                    try {
                      await deleteSpecMutation.mutateAsync(spec.name);
                      refetchSpecs();
                    } catch (error) {
                      alert(`Failed to delete spec: ${error instanceof Error ? error.message : 'Unknown error'}`);
                    }
                  }
                }}

                isDeleting={deleteSpecMutation.isPending}
              />
            ))
          ) : specs.length > 0 ? (
            <div className="col-span-full text-center py-8 text-gray-500">
              <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No specifications match your search</p>
              <p className="text-sm">Try adjusting your search terms</p>
            </div>
          ) : (
            <div className="col-span-full text-center py-12 text-gray-500">
              <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <h3 className="text-lg font-medium mb-2">No specifications yet</h3>
              <p className="text-sm mb-4">Create your first OS specification to get started</p>
              <button 
                onClick={() => openEditor(null, 'create')}
                className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create First Spec
              </button>
            </div>
          )}
        </div>
      )}

      {/* API Integration Success */}
      {specs.length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-green-900 mb-2">✅ Specs API Integration Working!</h3>
          <p className="text-green-800">
            Successfully loaded {specs.length} specifications from the OSImager backend.
          </p>
          <div className="mt-3 text-sm text-green-700">
            <p>📋 Specs include: {specs.slice(0, 3).map(s => s.name).join(', ')}{specs.length > 3 ? '...' : ''}</p>
            <p>🔍 Search and filtering: Working</p>
            <p>⚙️ CRUD operations: Ready for implementation</p>
          </div>
        </div>
      )}

      {/* Spec Editor Modal */}
      <SpecEditorModal
        isOpen={isEditorOpen}
        onClose={closeEditor}
        spec={selectedSpec}
        mode={editorMode}
        onSave={handleSaveSpec}
        isLoading={createSpecMutation.isPending || updateSpecMutation.isPending}
      />
    </div>
  );
}

// Spec card component
interface SpecCardProps {
  spec: SpecMetadata;
  onEdit: (spec: SpecMetadata) => void;
  onView: (spec: SpecMetadata) => void;
  onDuplicate: (spec: SpecMetadata) => void;
  onDelete: (spec: SpecMetadata) => void;
  isDeleting?: boolean;
}

function SpecCard({ spec, onEdit, onView, onDuplicate, onDelete, isDeleting }: SpecCardProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-gray-900 truncate">
            {spec.name}
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            OS Specification
          </p>
        </div>
        <StatusBadge status="available" />
      </div>

      {/* Spec details */}
      <div className="space-y-2 mb-4 text-sm text-gray-600">
        <div className="flex justify-between">
          <span>Size:</span>
          <span className="font-medium">{(spec.size / 1024).toFixed(1)} KB</span>
        </div>
        <div className="flex justify-between">
          <span>Modified:</span>
          <span className="font-medium">{formatRelativeTime(spec.modified)}</span>
        </div>
        <div className="flex justify-between">
          <span>Created:</span>
          <span className="font-medium">{formatRelativeTime(spec.created)}</span>
        </div>
        <div className="text-xs text-gray-500 mt-2">
          Path: {spec.path.split('/').pop()}
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-between items-center pt-4 border-t border-gray-200">
        <div className="flex space-x-1">
          <button
            onClick={() => onView(spec)}
            className="inline-flex items-center px-2 py-1 text-xs border border-gray-300 rounded text-gray-700 hover:bg-gray-50 transition-colors"
            disabled={isDeleting}
            title="View spec"
          >
            <FileText className="w-3 h-3 mr-1" />
            View
          </button>
          <button
            onClick={() => onEdit(spec)}
            className="inline-flex items-center px-2 py-1 text-xs border border-gray-300 rounded text-gray-700 hover:bg-gray-50 transition-colors"
            disabled={isDeleting}
            title="Edit spec"
          >
            <Edit className="w-3 h-3 mr-1" />
            Edit
          </button>
          <button
            onClick={() => onDuplicate(spec)}
            className="inline-flex items-center px-2 py-1 text-xs border border-gray-300 rounded text-gray-700 hover:bg-gray-50 transition-colors"
            disabled={isDeleting}
            title="Duplicate spec"
          >
            <Copy className="w-3 h-3 mr-1" />
            Copy
          </button>
        </div>
        <div className="flex space-x-1">
          <button
            onClick={() => onDelete(spec)}
            className="inline-flex items-center px-2 py-1 text-xs border border-red-300 rounded text-red-700 hover:bg-red-50 transition-colors"
            disabled={isDeleting}
            title="Delete spec"
          >
            {isDeleting ? (
              <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
            ) : (
              <Trash2 className="w-3 h-3 mr-1" />
            )}
            {isDeleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  );
}
