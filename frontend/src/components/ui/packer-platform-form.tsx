/**
 * Specialized Platform Form Components.
 * 
 * Form components for editing specific Packer integration configurations.
 */

import React, { useState, useEffect } from 'react';
import { 
  HelpCircle, 
  ExternalLink, 
  ChevronDown, 
  ChevronRight,
  Info,
  AlertCircle 
} from 'lucide-react';
import type { 
  PackerIntegration, 
  PackerField 
} from '@/lib/packer-integrations';

interface FieldGroupProps {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
  description?: string;
}

function FieldGroup({ title, children, defaultOpen = true, description }: FieldGroupProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border border-gray-200 rounded-lg mb-4">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center space-x-2">
          {isOpen ? (
            <ChevronDown className="w-4 h-4 text-gray-500" />
          ) : (
            <ChevronRight className="w-4 h-4 text-gray-500" />
          )}
          <h3 className="text-sm font-medium text-gray-900">{title}</h3>
        </div>
        {description && (
          <span className="text-xs text-gray-500">{description}</span>
        )}
      </button>
      {isOpen && (
        <div className="p-4 space-y-4">
          {children}
        </div>
      )}
    </div>
  );
}

interface FieldProps {
  field: PackerField;
  value: any;
  onChange: (name: string, value: any) => void;
  error?: string;
}

function FormField({ field, value, onChange, error }: FieldProps) {
  const [showHelp, setShowHelp] = useState(false);

  const handleChange = (newValue: any) => {
    // Validate the value if validation rules exist
    if (field.validation) {
      const { min, max, pattern } = field.validation;
      
      if (field.type === 'number') {
        const numValue = Number(newValue);
        if (min !== undefined && numValue < min) return;
        if (max !== undefined && numValue > max) return;
      }
      
      if (field.type === 'string' && pattern) {
        const regex = new RegExp(pattern);
        if (!regex.test(newValue)) return;
      }
    }
    
    onChange(field.name, newValue);
  };

  const renderInput = () => {
    const commonProps = {
      id: field.name,
      className: `w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
        error ? 'border-red-300 bg-red-50' : 'border-gray-300'
      }`,
      placeholder: field.placeholder,
    };

    switch (field.type) {
      case 'string':
        return (
          <input
            type="text"
            value={value || ''}
            onChange={(e) => handleChange(e.target.value)}
            {...commonProps}
          />
        );

      case 'number':
        return (
          <input
            type="number"
            value={value || ''}
            onChange={(e) => handleChange(e.target.value)}
            min={field.validation?.min}
            max={field.validation?.max}
            {...commonProps}
          />
        );

      case 'boolean':
        return (
          <div className="flex items-center">
            <input
              type="checkbox"
              id={field.name}
              checked={value || false}
              onChange={(e) => handleChange(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor={field.name} className="ml-2 text-sm text-gray-700">
              {field.description}
            </label>
          </div>
        );

      case 'select':
        return (
          <select
            value={value || ''}
            onChange={(e) => handleChange(e.target.value)}
            {...commonProps}
          >
            <option value="">Select {field.label}</option>
            {field.options?.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        );

      case 'multiselect':
        return (
          <div className="space-y-2">
            {field.options?.map((option) => (
              <div key={option.value} className="flex items-center">
                <input
                  type="checkbox"
                  id={`${field.name}-${option.value}`}
                  checked={(value || []).includes(option.value)}
                  onChange={(e) => {
                    const currentValues = value || [];
                    const newValues = e.target.checked
                      ? [...currentValues, option.value]
                      : currentValues.filter((v: any) => v !== option.value);
                    handleChange(newValues);
                  }}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor={`${field.name}-${option.value}`} className="ml-2 text-sm text-gray-700">
                  {option.label}
                </label>
              </div>
            ))}
          </div>
        );

      case 'array':
        return (
          <textarea
            value={typeof value === 'string' ? value : JSON.stringify(value || [], null, 2)}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                handleChange(parsed);
              } catch {
                // Keep the text value for editing
                handleChange(e.target.value);
              }
            }}
            rows={4}
            className={`${commonProps.className} font-mono text-sm`}
            placeholder="JSON array format"
          />
        );

      case 'object':
        return (
          <textarea
            value={typeof value === 'string' ? value : JSON.stringify(value || {}, null, 2)}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                handleChange(parsed);
              } catch {
                // Keep the text value for editing
                handleChange(e.target.value);
              }
            }}
            rows={6}
            className={`${commonProps.className} font-mono text-sm`}
            placeholder="JSON object format"
          />
        );

      default:
        return (
          <input
            type="text"
            value={value || ''}
            onChange={(e) => handleChange(e.target.value)}
            {...commonProps}
          />
        );
    }
  };

  if (field.type === 'boolean') {
    return (
      <div className="space-y-1">
        {renderInput()}
        {error && (
          <p className="text-sm text-red-600 flex items-center">
            <AlertCircle className="w-4 h-4 mr-1" />
            {error}
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-1">
      <div className="flex items-center space-x-2">
        <label htmlFor={field.name} className="text-sm font-medium text-gray-700">
          {field.label}
          {field.required && <span className="text-red-500 ml-1">*</span>}
        </label>
        {field.helpText && (
          <button
            type="button"
            onClick={() => setShowHelp(!showHelp)}
            className="text-gray-400 hover:text-gray-600"
          >
            <HelpCircle className="w-4 h-4" />
          </button>
        )}
      </div>
      
      {showHelp && field.helpText && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
          {field.helpText}
        </div>
      )}
      
      <div className="space-y-1">
        {renderInput()}
        {field.description && field.type !== 'boolean' && (
          <p className="text-xs text-gray-500">{field.description}</p>
        )}
        {error && (
          <p className="text-sm text-red-600 flex items-center">
            <AlertCircle className="w-4 h-4 mr-1" />
            {error}
          </p>
        )}
      </div>
    </div>
  );
}

interface PackerPlatformFormProps {
  integration: PackerIntegration;
  values: Record<string, any>;
  onChange: (values: Record<string, any>) => void;
  errors?: Record<string, string>;
  mode: 'create' | 'edit' | 'view';
}

export function PackerPlatformForm({ 
  integration, 
  values, 
  onChange, 
  errors = {},
  mode 
}: PackerPlatformFormProps) {
  const isReadOnly = mode === 'view';
  
  const handleFieldChange = (name: string, value: any) => {
    if (isReadOnly) return;
    
    const newValues = { ...values, [name]: value };
    onChange(newValues);
  };

  // Group fields by their group property
  const fieldGroups = integration.fields.reduce((groups, field) => {
    const group = field.group || 'General';
    if (!groups[group]) {
      groups[group] = [];
    }
    groups[group].push(field);
    return groups;
  }, {} as Record<string, PackerField[]>);

  // Define group order and descriptions
  const groupOrder = ['Basic', 'Connection', 'AWS Settings', 'VM Settings', 'Resources', 'Hardware', 'Storage', 'Network', 'ISO', 'Docker Settings', 'Display', 'Output', 'Advanced'];
  const groupDescriptions: Record<string, string> = {
    'Basic': 'Core platform configuration',
    'Connection': 'Authentication and connection settings',
    'AWS Settings': 'Amazon Web Services configuration',
    'VM Settings': 'Virtual machine basic settings',
    'Resources': 'vSphere resources and placement',
    'Hardware': 'CPU, memory, and hardware configuration',
    'Storage': 'Disk and storage configuration',
    'Network': 'Network adapter settings',
    'ISO': 'Installation media configuration',
    'Docker Settings': 'Container configuration',
    'Display': 'GUI and display options',
    'Output': 'Build output settings',
    'Advanced': 'Advanced configuration options'
  };

  return (
    <div className="space-y-6">
      {/* Integration Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-lg font-medium text-blue-900 mb-1">
              {integration.name}
            </h3>
            <p className="text-sm text-blue-700 mb-2">
              {integration.description}
            </p>
            <div className="flex items-center space-x-4 text-xs">
              <span className={`px-2 py-1 rounded-full ${
                integration.type === 'official' ? 'bg-green-100 text-green-800' :
                integration.type === 'partner' ? 'bg-blue-100 text-blue-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {integration.type.charAt(0).toUpperCase() + integration.type.slice(1)}
              </span>
              <span className="text-blue-600 capitalize">{integration.category}</span>
            </div>
          </div>
          <a
            href={integration.documentation}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center text-sm text-blue-600 hover:text-blue-800"
          >
            <ExternalLink className="w-4 h-4 mr-1" />
            Docs
          </a>
        </div>
      </div>

      {/* Required Fields Notice */}
      {integration.requiredFields.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-start">
            <Info className="w-5 h-5 text-amber-600 mr-2 mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-amber-800">Required Fields</h4>
              <p className="text-sm text-amber-700 mt-1">
                The following fields are required for this integration: {integration.requiredFields.join(', ')}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Form Fields Grouped */}
      <div className="space-y-4">
        {groupOrder.map(groupName => {
          const fields = fieldGroups[groupName];
          if (!fields || fields.length === 0) return null;

          return (
            <FieldGroup
              key={groupName}
              title={groupName}
              description={groupDescriptions[groupName]}
              defaultOpen={groupName === 'Basic' || groupName === 'Connection'}
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {fields.map(field => (
                  <div
                    key={field.name}
                    className={field.type === 'array' || field.type === 'object' ? 'md:col-span-2' : ''}
                  >
                    <FormField
                      field={field}
                      value={values[field.name]}
                      onChange={handleFieldChange}
                      error={errors[field.name]}
                    />
                  </div>
                ))}
              </div>
            </FieldGroup>
          );
        })}

        {/* Additional ungrouped fields */}
        {fieldGroups['General'] && fieldGroups['General'].length > 0 && (
          <FieldGroup title="General" description="General configuration options">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {fieldGroups['General'].map(field => (
                <div
                  key={field.name}
                  className={field.type === 'array' || field.type === 'object' ? 'md:col-span-2' : ''}
                >
                  <FormField
                    field={field}
                    value={values[field.name]}
                    onChange={handleFieldChange}
                    error={errors[field.name]}
                  />
                </div>
              ))}
            </div>
          </FieldGroup>
        )}
      </div>

      {/* OSImager Template Variables Info */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-2">OSImager Template Variables</h4>
        <p className="text-sm text-gray-600 mb-3">
          You can use OSImager template variables in your configuration:
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
          <div>
            <strong>String variables:</strong> <code>&gt;&gt;name&lt;&lt;</code>, <code>&gt;&gt;iso_path&lt;&lt;</code>
          </div>
          <div>
            <strong>Numeric variables:</strong> <code>#&gt;memory&lt;#</code>, <code>#&gt;cpu_cores&lt;#</code>
          </div>
          <div>
            <strong>Boolean variables:</strong> <code>%&gt;thin_disk&lt;%</code>, <code>%&gt;local_only&lt;%</code>
          </div>
          <div>
            <strong>Expressions:</strong> <code>E&gt;'value1' if condition else 'value2'&lt;E</code>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PackerPlatformForm;