/**
 * Build Details page component for viewing build progress and details.
 */

import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  RefreshCw, 
  Download, 
  Square,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Play
} from 'lucide-react';
import { useBuild, useBuildLogs, useCancelBuild } from '@/hooks/api-hooks';
import { LoadingState } from '@/components/ui/loading';
import { StatusBadge } from '@/components/ui/status-badge';
import { ProgressBar } from '@/components/ui/progress-bar';
import { formatRelativeTime, formatDuration, isBuildActive } from '@/lib/utils';
import type { BuildStatus } from '@/types/api';

export function BuildDetailsPage() {
  const { buildId } = useParams<{ buildId: string }>();
  const navigate = useNavigate();

  const { 
    data: build, 
    isLoading: buildLoading, 
    error: buildError,
    refetch: refetchBuild 
  } = useBuild(buildId || null);

  const {
    data: logs,
    isLoading: logsLoading,
    refetch: refetchLogs
  } = useBuildLogs(buildId || null, 50);

  const cancelBuild = useCancelBuild();

  if (!buildId) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600">Invalid build ID</p>
        <button onClick={() => navigate('/builds')} className="mt-4 btn-primary">
          Back to Builds
        </button>
      </div>
    );
  }

  if (buildLoading) {
    return <LoadingState message="Loading build details..." />;
  }

  if (buildError || !build) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600">Build not found or error loading build details</p>
        <button onClick={() => navigate('/builds')} className="mt-4 btn-primary">
          Back to Builds
        </button>
      </div>
    );
  }

  const getStatusIcon = (status: BuildStatus) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-6 h-6 text-green-600" />;
      case 'failed':
        return <XCircle className="w-6 h-6 text-red-600" />;
      case 'running':
        return <Play className="w-6 h-6 text-blue-600" />;
      case 'queued':
        return <Clock className="w-6 h-6 text-yellow-600" />;
      default:
        return <AlertCircle className="w-6 h-6 text-gray-600" />;
    }
  };

  const canCancel = isBuildActive(build.status);

  const handleCancel = async () => {
    if (confirm('Are you sure you want to cancel this build?')) {
      try {
        await cancelBuild.mutateAsync(build.id);
      } catch (error) {
        // Error handled by mutation
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/builds')}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Build Details</h1>
            <p className="text-gray-600 mt-1">
              {build.config.platform} • {build.config.spec} • {build.id.substring(0, 8)}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => {
              refetchBuild();
              refetchLogs();
            }}
            className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>

          {canCancel && (
            <button
              onClick={handleCancel}
              disabled={cancelBuild.isPending}
              className="inline-flex items-center px-3 py-2 border border-red-300 rounded-lg text-sm font-medium text-red-700 bg-white hover:bg-red-50 transition-colors disabled:opacity-50"
            >
              {cancelBuild.isPending ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Square className="w-4 h-4 mr-2" />
              )}
              Cancel Build
            </button>
          )}
        </div>
      </div>

      {/* Build Status Card */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            {getStatusIcon(build.status)}
            <div>
              <div className="flex items-center space-x-3">
                <StatusBadge status={build.status} />
                <span className="text-lg font-semibold text-gray-900">
                  {build.status.charAt(0).toUpperCase() + build.status.slice(1)}
                </span>
              </div>
              {build.error_message && (
                <p className="text-sm text-red-600 mt-1">{build.error_message}</p>
              )}
            </div>
          </div>
        </div>

        {/* Progress */}
        {build.progress && (
          <div className="mb-6">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">Progress</span>
              <span className="text-sm text-gray-600">
                {build.progress.step_number} of {build.progress.total_steps} steps
              </span>
            </div>
            <ProgressBar progress={build.progress} showDetails={true} />
            {build.progress.current_step && (
              <p className="text-sm text-gray-600 mt-2">
                Current step: {build.progress.current_step}
              </p>
            )}
          </div>
        )}

        {/* Build Info Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-1">Platform</h3>
            <p className="text-sm font-semibold text-gray-900">{build.config.platform}</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-1">Specification</h3>
            <p className="text-sm font-semibold text-gray-900">{build.config.spec}</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-1">Location</h3>
            <p className="text-sm font-semibold text-gray-900">{build.config.location}</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-1">Build ID</h3>
            <p className="text-sm font-mono text-gray-900">{build.id}</p>
          </div>
        </div>

        {/* Timing Information */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6 pt-6 border-t border-gray-200">
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-1">Started</h3>
            <p className="text-sm text-gray-900">
              {build.started_at ? formatRelativeTime(build.started_at) : 'Not started'}
            </p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-1">Completed</h3>
            <p className="text-sm text-gray-900">
              {build.completed_at ? formatRelativeTime(build.completed_at) : 'Not completed'}
            </p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-1">Duration</h3>
            <p className="text-sm text-gray-900">
              {build.duration ? formatDuration(build.duration) : 'N/A'}
            </p>
          </div>
        </div>
      </div>

      {/* Build Configuration */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Build Configuration</h2>
        </div>
        <div className="p-6">
          {/* Build Command */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-700 mb-3">Build Command</h3>
            <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm overflow-x-auto">
              <div className="whitespace-pre-wrap">
                {(() => {
                  // Construct the correct command format
                  let cmd = `# Build command that was executed:
cd cli && python3 mkosimage ${build.config.platform}/${build.config.location}/${build.config.spec}`;
                  
                  if (build.config.name) {
                    cmd += ` ${build.config.name}`;
                  }
                  if (build.config.ip) {
                    cmd += ` ${build.config.ip}`;
                  }
                  if (build.config.debug) {
                    cmd += ' --debug';
                  }
                  if (build.config.dry_run) {
                    cmd += ' --dry-run';
                  }
                  if (build.config.timeout) {
                    cmd += ` --timeout ${build.config.timeout}`;
                  }
                  
                  return cmd;
                })()}
              </div>
            </div>
            <p className="mt-2 text-xs text-gray-500">
              Note: The spec parameter '{build.config.spec}' is resolved to the appropriate spec directory during build execution.
            </p>
          </div>
          
          {/* Full Configuration */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-3">Full Configuration</h3>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <pre className="text-sm text-gray-800 whitespace-pre-wrap overflow-x-auto">
                {JSON.stringify(build.config, null, 2)}
              </pre>
            </div>
          </div>
          
          {/* Variables */}
          {build.config.variables && Object.keys(build.config.variables).length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Build Variables</h3>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <pre className="text-sm text-blue-800 whitespace-pre-wrap">
                  {JSON.stringify(build.config.variables, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Build Logs */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Build Logs</h2>
            <div className="flex items-center space-x-2">
              {logsLoading && <RefreshCw className="w-4 h-4 animate-spin text-gray-400" />}
              <span className="text-sm text-gray-500">
                {logs?.length || 0} entries
              </span>
            </div>
          </div>
        </div>

        <div className="p-6">
          {logs && logs.length > 0 ? (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {logs.map((log, index) => (
                <div
                  key={index}
                  className={`p-3 rounded-lg text-sm font-mono ${
                    log.level === 'error' || log.level === 'critical'
                      ? 'bg-red-50 text-red-800 border border-red-200'
                      : log.level === 'warning'
                      ? 'bg-yellow-50 text-yellow-800 border border-yellow-200'
                      : 'bg-gray-50 text-gray-800 border border-gray-200'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <span className="flex-1">{log.message}</span>
                    <span className="text-xs opacity-75 ml-3">
                      {formatRelativeTime(log.timestamp)}
                    </span>
                  </div>
                  {log.source && (
                    <div className="text-xs opacity-60 mt-1">
                      Source: {log.source}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No logs available yet</p>
              <p className="text-sm">Logs will appear here when the build starts</p>
            </div>
          )}
        </div>
      </div>

      {/* Artifacts */}
      {build.artifacts && build.artifacts.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Build Artifacts</h2>
          </div>
          <div className="p-6">
            <div className="space-y-3">
              {build.artifacts.map((artifact, index) => (
                <div key={index} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{artifact.name}</p>
                    <p className="text-xs text-gray-500">
                      {artifact.type} • {(artifact.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  <button className="inline-flex items-center px-3 py-1 text-xs border border-gray-300 rounded text-gray-700 hover:bg-gray-50 transition-colors">
                    <Download className="w-3 h-3 mr-1" />
                    Download
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
