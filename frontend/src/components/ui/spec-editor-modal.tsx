/**
 * Spec Editor Modal Component
 * Provides a modal interface for editing OSImager specifications with JSON editing capabilities
 */

import { useState, useEffect } from 'react';
import { X, Save, AlertCircle, RefreshCw, Eye, Edit3, Copy } from 'lucide-react';
import type { Spec, SpecMetadata } from '@/types/api';

interface SpecEditorModalProps {
  isOpen: boolean;
  onClose: () => void;
  spec: SpecMetadata | null;
  mode: 'view' | 'edit' | 'create' | 'duplicate';
  onSave: (name: string, content: any) => Promise<void>;
  isLoading?: boolean;
}

export function SpecEditorModal({
  isOpen,
  onClose,
  spec,
  mode,
  onSave,
  isLoading = false
}: SpecEditorModalProps) {
  const [specContent, setSpecContent] = useState<Spec | null>(null);
  const [jsonContent, setJsonContent] = useState('');
  const [specName, setSpecName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isValid, setIsValid] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [contentLoading, setContentLoading] = useState(false);

  // Load spec content when modal opens or spec changes
  useEffect(() => {
    if (isOpen && spec) {
      loadSpecContent();
    } else if (isOpen && mode === 'create') {
      // Initialize with empty spec template
      const emptySpec = {
        platforms: [],
        locations: [],
        provides: {
          dist: '',
          versions: [],
          arches: []
        },
        defs: {},
        config: {},
        flavor: 'linux'
      };
      setSpecContent(emptySpec);
      setJsonContent(JSON.stringify(emptySpec, null, 2));
      setSpecName('');
      setError(null);
    }
  }, [isOpen, spec, mode]);

  // Update spec name when spec changes
  useEffect(() => {
    if (spec) {
      if (mode === 'duplicate') {
        setSpecName(`${spec.name}-copy`);
      } else {
        setSpecName(spec.name);
      }
    }
  }, [spec, mode]);

  const loadSpecContent = async () => {
    if (!spec) return;

    setContentLoading(true);
    setError(null);

    try {
      const response = await fetch(`/backend/specs/${spec.name}`);
      if (!response.ok) {
        throw new Error(`Failed to load spec: ${response.statusText}`);
      }

      const data: Spec = await response.json();
      
      // Remove metadata for editing (it's read-only)
      const { metadata, ...editableContent } = data;
      
      setSpecContent(data);
      setJsonContent(JSON.stringify(editableContent, null, 2));
      setIsValid(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load spec content');
    } finally {
      setContentLoading(false);
    }
  };

  const validateJsonContent = (content: string): boolean => {
    try {
      const parsed = JSON.parse(content);
      
      // Basic validation - check required fields
      if (!parsed.provides || !parsed.provides.dist || !parsed.provides.versions || !parsed.provides.arches) {
        setError('Missing required fields: provides.dist, provides.versions, provides.arches');
        return false;
      }

      setError(null);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid JSON syntax');
      return false;
    }
  };

  const handleJsonChange = (value: string) => {
    setJsonContent(value);
    const valid = validateJsonContent(value);
    setIsValid(valid);
  };

  const handleSave = async () => {
    if (!isValid || !specName.trim()) {
      setError('Please fix validation errors and provide a spec name');
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      const content = JSON.parse(jsonContent);
      await onSave(specName.trim(), content);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save spec');
    } finally {
      setIsSaving(false);
    }
  };

  const getModalTitle = () => {
    switch (mode) {
      case 'view':
        return `View Spec: ${spec?.name}`;
      case 'edit':
        return `Edit Spec: ${spec?.name}`;
      case 'create':
        return 'Create New Spec';
      case 'duplicate':
        return `Duplicate Spec: ${spec?.name}`;
      default:
        return 'Spec Editor';
    }
  };

  const getModalIcon = () => {
    switch (mode) {
      case 'view':
        return <Eye className="w-5 h-5" />;
      case 'edit':
        return <Edit3 className="w-5 h-5" />;
      case 'create':
        return <Edit3 className="w-5 h-5" />;
      case 'duplicate':
        return <Copy className="w-5 h-5" />;
      default:
        return <Edit3 className="w-5 h-5" />;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black bg-opacity-50 transition-opacity" onClick={onClose} />
      
      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0 text-primary-600">
                {getModalIcon()}
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  {getModalTitle()}
                </h2>
                {spec && (
                  <p className="text-sm text-gray-600 mt-1">
                    Last modified: {new Date(spec.modified).toLocaleDateString()}
                  </p>
                )}
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-hidden flex flex-col">
            {contentLoading ? (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <RefreshCw className="w-8 h-8 mx-auto text-gray-400 animate-spin mb-2" />
                  <p className="text-gray-600">Loading spec content...</p>
                </div>
              </div>
            ) : (
              <>
                {/* Spec Name Input (for create/duplicate modes) */}
                {(mode === 'create' || mode === 'duplicate') && (
                  <div className="p-6 border-b border-gray-200">
                    <label htmlFor="spec-name" className="block text-sm font-medium text-gray-700 mb-2">
                      Specification Name
                    </label>
                    <input
                      id="spec-name"
                      type="text"
                      value={specName}
                      onChange={(e) => setSpecName(e.target.value)}
                      placeholder="Enter spec name..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      disabled={mode === 'view'}
                    />
                  </div>
                )}

                {/* JSON Editor */}
                <div className="flex-1 p-6 overflow-hidden">
                  <div className="flex items-center justify-between mb-4">
                    <label className="block text-sm font-medium text-gray-700">
                      Specification Configuration
                    </label>
                    {!isValid && (
                      <div className="flex items-center text-red-600 text-sm">
                        <AlertCircle className="w-4 h-4 mr-1" />
                        Invalid JSON
                      </div>
                    )}
                  </div>
                  
                  <textarea
                    value={jsonContent}
                    onChange={(e) => handleJsonChange(e.target.value)}
                    className={`w-full h-96 px-3 py-2 border rounded-lg font-mono text-sm resize-none focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
                      !isValid ? 'border-red-300 bg-red-50' : 'border-gray-300'
                    }`}
                    placeholder="JSON configuration will appear here..."
                    disabled={mode === 'view'}
                    spellCheck={false}
                  />

                  {/* Error Message */}
                  {error && (
                    <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                      <div className="flex items-center">
                        <AlertCircle className="w-4 h-4 text-red-600 mr-2 flex-shrink-0" />
                        <p className="text-red-800 text-sm">{error}</p>
                      </div>
                    </div>
                  )}

                  {/* Help Text */}
                  <div className="mt-3 text-xs text-gray-500">
                    <p>
                      <strong>Required fields:</strong> provides.dist, provides.versions, provides.arches
                    </p>
                    <p className="mt-1">
                      <strong>Optional sections:</strong> platforms, locations, defs, config, files, provisioners
                    </p>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
            <div className="text-sm text-gray-600">
              {mode === 'view' ? (
                'Read-only view'
              ) : (
                'Changes will be saved to the OSImager specifications'
              )}
            </div>
            
            <div className="flex space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
                disabled={isSaving}
              >
                {mode === 'view' ? 'Close' : 'Cancel'}
              </button>
              
              {mode !== 'view' && (
                <button
                  type="button"
                  onClick={handleSave}
                  disabled={!isValid || !specName.trim() || isSaving || contentLoading}
                  className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-lg hover:bg-primary-700 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isSaving ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="w-4 h-4 mr-2" />
                      Save Spec
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}