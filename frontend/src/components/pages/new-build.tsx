/**
 * New Build page component for creating builds.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Play, Settings2, Info } from 'lucide-react';
import { usePlatforms, useLocations, useSpecsIndex, useCreateBuild } from '@/hooks/api-hooks';
import { LoadingState } from '@/components/ui/loading';
import type { BuildConfig } from '@/types/api';

export function NewBuildPage() {
  const navigate = useNavigate();
  const [selectedPlatform, setSelectedPlatform] = useState('');
  const [selectedLocation, setSelectedLocation] = useState('');
  const [selectedSpec, setSelectedSpec] = useState('');
  const [buildName, setBuildName] = useState('');
  const [hostname, setHostname] = useState('');
  const [ipAddress, setIpAddress] = useState('');
  const [isAdvanced, setIsAdvanced] = useState(false);

  // Load data
  const { data: platforms, isLoading: platformsLoading } = usePlatforms();
  const { data: locations, isLoading: locationsLoading } = useLocations();
  const { data: specsIndex, isLoading: specsLoading } = useSpecsIndex();
  
  const createBuild = useCreateBuild();

  // Extract platform/location names and process specs index
  const platformNames = platforms || [];
  const locationNames = locations || [];
  
  // Process specs index to create grouped options
  const specsOptions = specsIndex ? Object.entries(specsIndex).map(([key, data]: [string, any]) => ({
    key,
    label: `${data.provides.dist} ${data.provides.version} (${data.provides.arch})`,
    dist: data.provides.dist,
    version: data.provides.version,
    arch: data.provides.arch,
    searchText: `${data.provides.dist} ${data.provides.version} ${data.provides.arch}`.toLowerCase()
  })).sort((a, b) => {
    // Sort by dist, then version, then arch
    if (a.dist !== b.dist) return a.dist.localeCompare(b.dist);
    if (a.version !== b.version) return a.version.localeCompare(b.version);
    return a.arch.localeCompare(b.arch);
  }) : [];

  const isLoading = platformsLoading || locationsLoading || specsLoading;
  const canSubmit = selectedPlatform && selectedLocation && selectedSpec;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!canSubmit) return;

    const config: BuildConfig = {
      platform: selectedPlatform,
      location: selectedLocation,
      spec: selectedSpec,
      name: hostname || undefined,
      ip: ipAddress || undefined,
      variables: {},
      timeout: 3600,
      debug: false,
      dry_run: false
    };

    try {
      const build = await createBuild.mutateAsync({ config });
      navigate(`/builds/${build.id}`);
    } catch (error) {
      // Error is handled by the mutation
    }
  };

  if (isLoading) {
    return <LoadingState message="Loading build options..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <button
          onClick={() => navigate('/builds')}
          className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">New Build</h1>
          <p className="text-gray-600 mt-1">
            Create a new OS image build
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Build Configuration Form */}
        <div className="lg:col-span-2">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h2 className="text-lg font-semibold mb-4">Build Configuration</h2>
              
              <div className="space-y-4">
                {/* Build Name */}
                <div>
                  <label htmlFor="buildName" className="block text-sm font-medium text-gray-700 mb-1">
                    Build Name (Optional)
                  </label>
                  <input
                    type="text"
                    id="buildName"
                    value={buildName}
                    onChange={(e) => setBuildName(e.target.value)}
                    placeholder="Enter a descriptive name for this build"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>

                {/* Platform Selection */}
                <div>
                  <label htmlFor="platform" className="block text-sm font-medium text-gray-700 mb-1">
                    Platform *
                  </label>
                  <select
                    id="platform"
                    value={selectedPlatform}
                    onChange={(e) => setSelectedPlatform(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    required
                  >
                    <option value="">Select a platform...</option>
                    {platformNames.map(name => (
                      <option key={name} value={name}>
                        {name.charAt(0).toUpperCase() + name.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Location Selection */}
                <div>
                  <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-1">
                    Location *
                  </label>
                  <select
                    id="location"
                    value={selectedLocation}
                    onChange={(e) => setSelectedLocation(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    required
                  >
                    <option value="">Select a location...</option>
                    {locationNames.map(name => (
                      <option key={name} value={name}>
                        {name.charAt(0).toUpperCase() + name.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Spec Selection */}
                <div>
                  <label htmlFor="spec" className="block text-sm font-medium text-gray-700 mb-1">
                    Specification *
                  </label>
                  <select
                    id="spec"
                    value={selectedSpec}
                    onChange={(e) => setSelectedSpec(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    required
                  >
                    <option value="">Select a specification...</option>
                    {specsOptions.map(option => (
                      <option key={option.key} value={option.key}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  {selectedSpec && (
                    <p className="mt-1 text-xs text-gray-500">
                      {(() => {
                        const selected = specsOptions.find(opt => opt.key === selectedSpec);
                        return selected ? `Distribution: ${selected.dist}, Version: ${selected.version}, Architecture: ${selected.arch}` : '';
                      })()} 
                    </p>
                  )}
                </div>

                {/* Hostname */}
                <div>
                  <label htmlFor="hostname" className="block text-sm font-medium text-gray-700 mb-1">
                    Hostname (Optional)
                  </label>
                  <input
                    type="text"
                    id="hostname"
                    value={hostname}
                    onChange={(e) => setHostname(e.target.value)}
                    placeholder="Enter hostname for the build"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>

                {/* IP Address */}
                <div>
                  <label htmlFor="ipAddress" className="block text-sm font-medium text-gray-700 mb-1">
                    IP Address (Optional)
                  </label>
                  <input
                    type="text"
                    id="ipAddress"
                    value={ipAddress}
                    onChange={(e) => setIpAddress(e.target.value)}
                    placeholder="Enter IP address for the build"
                    pattern="^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>

                {/* Advanced Options Toggle */}
                <div className="pt-4">
                  <button
                    type="button"
                    onClick={() => setIsAdvanced(!isAdvanced)}
                    className="flex items-center space-x-2 text-sm text-primary-600 hover:text-primary-700"
                  >
                    <Settings2 className="w-4 h-4" />
                    <span>{isAdvanced ? 'Hide' : 'Show'} Advanced Options</span>
                  </button>
                </div>

                {/* Advanced Options */}
                {isAdvanced && (
                  <div className="border-t pt-4 space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="flex items-center space-x-2">
                          <input type="checkbox" className="rounded" />
                          <span className="text-sm text-gray-700">Debug Mode</span>
                        </label>
                      </div>
                      <div>
                        <label className="flex items-center space-x-2">
                          <input type="checkbox" className="rounded" />
                          <span className="text-sm text-gray-700">Dry Run</span>
                        </label>
                      </div>
                    </div>
                    
                    <div>
                      <label htmlFor="timeout" className="block text-sm font-medium text-gray-700 mb-1">
                        Timeout (seconds)
                      </label>
                      <input
                        type="number"
                        id="timeout"
                        defaultValue={3600}
                        min={300}
                        max={86400}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => navigate('/builds')}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!canSubmit || createBuild.isPending}
                className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {createBuild.isPending ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Start Build
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Build Preview/Info */}
        <div className="space-y-6">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4">Build Preview</h3>
            
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Platform:</span>
                <span className="font-medium">{selectedPlatform || 'Not selected'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Location:</span>
                <span className="font-medium">{selectedLocation || 'Not selected'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Specification:</span>
                <span className="font-medium text-right max-w-48">
                  {selectedSpec ? (
                    (() => {
                      const selected = specsOptions.find(opt => opt.key === selectedSpec);
                      return selected ? selected.label : selectedSpec;
                    })()
                  ) : 'Not selected'}
                </span>
              </div>
              {hostname && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Hostname:</span>
                  <span className="font-medium">{hostname}</span>
                </div>
              )}
              {ipAddress && (
                <div className="flex justify-between">
                  <span className="text-gray-600">IP Address:</span>
                  <span className="font-medium font-mono">{ipAddress}</span>
                </div>
              )}
            </div>

            {canSubmit && (
              <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm text-green-800">
                  ✅ Ready to create build
                </p>
              </div>
            )}
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <div className="flex items-start space-x-3">
              <Info className="w-5 h-5 text-blue-600 mt-0.5" />
              <div className="text-sm text-blue-800">
                <p className="font-medium mb-1">Available Options:</p>
                <ul className="space-y-1 text-xs">
                  <li>• {platformNames.length} platforms available</li>
                  <li>• {locationNames.length} locations configured</li>
                  <li>• {specsOptions.length} specifications ready</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
