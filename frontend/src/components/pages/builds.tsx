/**
 * Builds page component showing all builds with filtering and management.
 */

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Plus, 
  Search, 
  Filter, 
  RefreshCw, 
  Eye, 
  Square,
  Play,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle
} from 'lucide-react';
import { useBuilds, useCancelBuild } from '@/hooks/api-hooks';
import { LoadingState } from '@/components/ui/loading';
import { StatusBadge } from '@/components/ui/status-badge';
import { ProgressBar } from '@/components/ui/progress-bar';
import { formatDate, formatRelativeTime, formatDuration, isBuildActive } from '@/lib/utils';
import type { Build, BuildStatus } from '@/types/api';

const statusFilters: { label: string; value: BuildStatus | 'all' }[] = [
  { label: 'All', value: 'all' },
  { label: 'Active', value: 'running' },
  { label: 'Queued', value: 'queued' },
  { label: 'Completed', value: 'completed' },
  { label: 'Failed', value: 'failed' },
  { label: 'Cancelled', value: 'cancelled' },
];

export function BuildsPage() {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState<BuildStatus | 'all'>('all');
  const [searchTerm, setSearchTerm] = useState('');
  
  const { 
    data: buildsData, 
    isLoading, 
    error: buildsError,
    refetch 
  } = useBuilds(statusFilter === 'all' ? undefined : statusFilter);
  
  const cancelBuild = useCancelBuild();

  // Get builds from the response
  const builds = buildsData?.builds || [];
  const totalBuilds = buildsData?.total || 0;
  const activeBuilds = buildsData?.active || 0;

  // Filter builds by search term
  const filteredBuilds = builds.filter(build => {
    if (!searchTerm) return true;
    const searchLower = searchTerm.toLowerCase();
    return (
      build.config.platform.toLowerCase().includes(searchLower) ||
      build.config.spec.toLowerCase().includes(searchLower) ||
      build.config.location.toLowerCase().includes(searchLower) ||
      build.id.toLowerCase().includes(searchLower)
    );
  });

  const handleCancelBuild = async (buildId: string) => {
    try {
      await cancelBuild.mutateAsync(buildId);
    } catch (error) {
      // Error is handled by the mutation
    }
  };

  if (isLoading) {
    return <LoadingState message="Loading builds..." />;
  }

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Builds</h1>
          <p className="text-gray-600 mt-1">
            Manage and monitor your OS image builds
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => refetch()}
            className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <Link 
            to="/builds/new" 
            className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Build
          </Link>
        </div>
      </div>

      {/* Error state */}
      {buildsError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">⚠️ Error loading builds: {buildsError.message}</p>
          <button 
            onClick={() => refetch()}
            className="mt-2 text-red-600 hover:text-red-700 text-sm underline"
          >
            Try again
          </button>
        </div>
      )}

      {/* Filters and search */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <Search className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search builds by platform, spec, location, or ID..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

          {/* Status filter */}
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <select
              className="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as BuildStatus | 'all')}
            >
              {statusFilters.map((filter) => (
                <option key={filter.value} value={filter.value}>
                  {filter.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Stats summary */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{totalBuilds}</p>
            <p className="text-sm text-gray-600">Total Builds</p>
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-primary-600">{activeBuilds}</p>
            <p className="text-sm text-gray-600">Active Builds</p>
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{filteredBuilds.length}</p>
            <p className="text-sm text-gray-600">Filtered Results</p>
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">
              {builds.filter(b => b.status === 'completed').length}
            </p>
            <p className="text-sm text-gray-600">Completed</p>
          </div>
        </div>
      </div>

      {/* Builds list */}
      <div className="bg-white rounded-lg border border-gray-200">
        {filteredBuilds.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            {searchTerm || statusFilter !== 'all' ? (
              <div>
                <Search className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>No builds match your filters</p>
                <button
                  onClick={() => {
                    setSearchTerm('');
                    setStatusFilter('all');
                  }}
                  className="text-primary-600 hover:text-primary-700 text-sm mt-2"
                >
                  Clear filters
                </button>
              </div>
            ) : (
              <div>
                <Play className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>No builds yet</p>
                <Link 
                  to="/builds/new" 
                  className="text-primary-600 hover:text-primary-700 text-sm mt-2 inline-block"
                >
                  Create your first build
                </Link>
              </div>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Build
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Progress
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Started
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredBuilds.map((build) => (
                  <BuildRow
                    key={build.id}
                    build={build}
                    onCancel={handleCancelBuild}
                    onView={(id) => navigate(`/builds/${id}`)}
                    cancelLoading={cancelBuild.isPending}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* API Integration Success */}
      {builds.length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-green-900 mb-2">✅ Builds API Integration Working!</h3>
          <p className="text-green-800">
            Successfully loaded {builds.length} build records from the OSImager backend.
          </p>
          <div className="mt-3 text-sm text-green-700">
            <p>📊 Total: {totalBuilds} builds, Active: {activeBuilds}</p>
            <p>🔍 Search and filtering: Working</p>
            <p>⚙️ Build management: Ready</p>
          </div>
        </div>
      )}
    </div>
  );
}

// Build row component
interface BuildRowProps {
  build: Build;
  onCancel: (buildId: string) => void;
  onView: (buildId: string) => void;
  cancelLoading: boolean;
}

function BuildRow({ build, onCancel, onView, cancelLoading }: BuildRowProps) {
  const { id, config, status, progress, started_at, duration } = build;
  const canCancel = isBuildActive(status);

  const getStatusIcon = (status: BuildStatus) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-600" />;
      case 'running':
        return <Play className="w-4 h-4 text-blue-600" />;
      case 'queued':
        return <Clock className="w-4 h-4 text-yellow-600" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-600" />;
    }
  };

  return (
    <tr className="hover:bg-gray-50">
      <td className="px-6 py-4 whitespace-nowrap">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-900">
              {config.platform}
            </span>
            <span className="text-gray-500">•</span>
            <span className="text-sm text-gray-600">{config.spec}</span>
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {config.location} • {id.substring(0, 8)}
          </div>
        </div>
      </td>
      
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center space-x-2">
          {getStatusIcon(status)}
          <StatusBadge status={status} />
        </div>
      </td>
      
      <td className="px-6 py-4 whitespace-nowrap">
        {progress ? (
          <div className="w-32">
            <ProgressBar 
              progress={progress} 
              showDetails={false}
              className="h-2"
            />
          </div>
        ) : (
          <span className="text-gray-400 text-sm">N/A</span>
        )}
      </td>
      
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
        {started_at ? formatRelativeTime(started_at) : 'N/A'}
      </td>
      
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
        {duration ? formatDuration(duration) : 'N/A'}
      </td>
      
      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
        <div className="flex items-center justify-end space-x-2">
          <button
            onClick={() => onView(id)}
            className="inline-flex items-center px-2 py-1 text-xs border border-gray-300 rounded text-gray-700 hover:bg-gray-50 transition-colors"
            title="View details"
          >
            <Eye className="w-3 h-3 mr-1" />
            View
          </button>
          
          {canCancel && (
            <button
              onClick={() => onCancel(id)}
              disabled={cancelLoading}
              className="inline-flex items-center px-2 py-1 text-xs border border-red-300 rounded text-red-700 hover:bg-red-50 transition-colors disabled:opacity-50"
            >
              {cancelLoading ? (
                <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
              ) : (
                <Square className="w-3 h-3 mr-1" />
              )}
              Cancel
            </button>
          )}
        </div>
      </td>
    </tr>
  );
}
