/**
 * Dashboard page component.
 * 
 * Provides system overview and build monitoring with real-time data.
 */

import { Link } from 'react-router-dom';
import { 
  Activity, 
  CheckCircle, 
  XCircle, 
  Plus,
  BarChart3,
  AlertTriangle,
  Clock,
  HardDrive,
  Cpu
} from 'lucide-react';
import { useHealth, useBuilds, useSystemInfo } from '@/hooks/api-hooks';
import { useMemo } from 'react';

export function Dashboard() {
  const { data: health, isLoading: healthLoading, error: healthError } = useHealth();
  const { data: builds, isLoading: buildsLoading } = useBuilds();
  const { data: system, isLoading: systemLoading } = useSystemInfo();

  // Calculate build statistics
  const buildStats = useMemo(() => {
    if (!builds) {
      return {
        total: 0,
        active: 0,
        completed: 0,
        failed: 0,
        activeBuildsList: []
      };
    }

    const activeBuildsList = builds.builds.filter(build => 
      ['queued', 'preparing', 'running'].includes(build.status)
    );
    const completedBuilds = builds.builds.filter(build => build.status === 'completed');
    const failedBuilds = builds.builds.filter(build => build.status === 'failed');

    return {
      total: builds.total,
      active: builds.active,
      completed: completedBuilds.length,
      failed: failedBuilds.length,
      activeBuildsList
    };
  }, [builds]);

  // Recent builds (last 5)
  const recentBuilds = useMemo(() => {
    if (!builds) return [];
    return builds.builds
      .sort((a, b) => new Date(b.started_at || 0).getTime() - new Date(a.started_at || 0).getTime())
      .slice(0, 5);
  }, [builds]);

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">
            System overview and build monitoring
          </p>
        </div>
        <Link
          to="/builds/new"
          className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Build
        </Link>
      </div>

      {/* System Status Banner */}
      {healthError ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <XCircle className="w-5 h-5 text-red-600 mr-2" />
            <p className="text-red-800">
              ⚠️ System Error • Unable to connect to API backend
            </p>
          </div>
        </div>
      ) : health?.healthy ? (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
              <p className="text-green-800">
                ✅ System operational • All systems healthy
              </p>
            </div>
            <div className="text-sm text-green-700">
              {health.details.websocket_connections} WebSocket connections
            </div>
          </div>
        </div>
      ) : health && !health.healthy ? (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertTriangle className="w-5 h-5 text-yellow-600 mr-2" />
            <p className="text-yellow-800">
              ⚠️ System Warning • Some health checks failed
            </p>
          </div>
        </div>
      ) : null}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Total Builds"
          value={buildStats.total}
          icon={BarChart3}
          color="info"
          description="All time builds"
          loading={buildsLoading}
        />
        <StatsCard
          title="Active Builds"
          value={buildStats.active}
          icon={Activity}
          color="primary"
          description="Currently running"
          loading={buildsLoading}
        />
        <StatsCard
          title="Completed"
          value={buildStats.completed}
          icon={CheckCircle}
          color="success"
          description="Successfully completed"
          loading={buildsLoading}
        />
        <StatsCard
          title="Failed"
          value={buildStats.failed}
          icon={XCircle}
          color="danger"
          description="Build failures"
          loading={buildsLoading}
        />
      </div>

      {/* System Resources */}
      {system && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <ResourceCard
            title="CPU Usage"
            value={system.cpu.usage_percent}
            unit="%"
            icon={Cpu}
            color={system.cpu.usage_percent > 80 ? 'danger' : system.cpu.usage_percent > 60 ? 'warning' : 'success'}
            loading={systemLoading}
          />
          <ResourceCard
            title="Memory Usage"
            value={system.memory.percent}
            unit="%"
            icon={HardDrive}
            color={system.memory.percent > 85 ? 'danger' : system.memory.percent > 70 ? 'warning' : 'success'}
            loading={systemLoading}
          />
          <ResourceCard
            title="Disk Usage"
            value={system.disk.percent}
            unit="%"
            icon={HardDrive}
            color={system.disk.percent > 90 ? 'danger' : system.disk.percent > 75 ? 'warning' : 'success'}
            loading={systemLoading}
          />
        </div>
      )}

      {/* Build Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold mb-4">Active Builds</h3>
          {buildsLoading ? (
            <div className="animate-pulse space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-4 bg-gray-200 rounded"></div>
              ))}
            </div>
          ) : buildStats.activeBuildsList.length > 0 ? (
            <div className="space-y-3">
              {buildStats.activeBuildsList.map((build) => (
                <div key={build.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <div className="font-medium text-sm">{build.config.spec}</div>
                    <div className="text-xs text-gray-500">
                      {build.config.platform} • {build.config.location}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <StatusBadge status={build.status} />
                    <div className="text-xs text-gray-400">
                      {build.started_at && new Date(build.started_at).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No active builds</p>
              <p className="text-sm">Start a new build to see activity here</p>
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold mb-4">Recent Builds</h3>
          {buildsLoading ? (
            <div className="animate-pulse space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-4 bg-gray-200 rounded"></div>
              ))}
            </div>
          ) : recentBuilds.length > 0 ? (
            <div className="space-y-3">
              {recentBuilds.map((build) => (
                <div key={build.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <div className="font-medium text-sm">{build.config.spec}</div>
                    <div className="text-xs text-gray-500">
                      {build.config.platform} • {build.config.location}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <StatusBadge status={build.status} />
                    {build.duration && (
                      <div className="text-xs text-gray-400 flex items-center">
                        <Clock className="w-3 h-3 mr-1" />
                        {Math.round(build.duration)}s
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <BarChart3 className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No recent builds</p>
              <p className="text-sm">Build history will appear here</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Stats card component
interface StatsCardProps {
  title: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
  color: 'primary' | 'success' | 'danger' | 'info';
  description: string;
  loading?: boolean;
}

function StatsCard({ title, value, icon: Icon, color, description, loading }: StatsCardProps) {
  const colorClasses = {
    primary: 'bg-primary-100 text-primary-600',
    success: 'bg-green-100 text-green-600',
    danger: 'bg-red-100 text-red-600',
    info: 'bg-gray-100 text-gray-600',
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center">
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          {loading ? (
            <div className="animate-pulse">
              <div className="h-8 bg-gray-200 rounded w-16 mb-1"></div>
              <div className="h-3 bg-gray-200 rounded w-24"></div>
            </div>
          ) : (
            <>
              <p className="text-2xl font-bold text-gray-900">{value}</p>
              <p className="text-xs text-gray-500">{description}</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// Resource card component
interface ResourceCardProps {
  title: string;
  value: number;
  unit: string;
  icon: React.ComponentType<{ className?: string }>;
  color: 'success' | 'warning' | 'danger';
  loading?: boolean;
}

function ResourceCard({ title, value, unit, icon: Icon, color, loading }: ResourceCardProps) {
  const colorClasses = {
    success: 'bg-green-100 text-green-600',
    warning: 'bg-yellow-100 text-yellow-600',
    danger: 'bg-red-100 text-red-600',
  };

  const progressColorClasses = {
    success: 'bg-green-500',
    warning: 'bg-yellow-500',
    danger: 'bg-red-500',
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
            <Icon className="w-5 h-5" />
          </div>
          <div className="ml-3">
            <p className="text-sm font-medium text-gray-600">{title}</p>
          </div>
        </div>
        {loading ? (
          <div className="animate-pulse h-6 bg-gray-200 rounded w-12"></div>
        ) : (
          <span className="text-lg font-bold text-gray-900">
            {Math.round(value)}{unit}
          </span>
        )}
      </div>
      {!loading && (
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${progressColorClasses[color]}`}
            style={{ width: `${Math.min(value, 100)}%` }}
          ></div>
        </div>
      )}
    </div>
  );
}

// Status badge component
interface StatusBadgeProps {
  status: string;
}

function StatusBadge({ status }: StatusBadgeProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'queued':
        return 'bg-yellow-100 text-yellow-800';
      case 'preparing':
        return 'bg-purple-100 text-purple-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(status)}`}>
      {status}
    </span>
  );
}
