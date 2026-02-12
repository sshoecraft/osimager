/**
 * Status Badge component for displaying build and system statuses.
 */

import { cn, getBuildStatusClasses, getLogLevelClasses, getStatusText } from '@/lib/utils';
import type { BuildStatus, BuildLogLevel } from '@/types/api';

interface StatusBadgeProps {
  status: BuildStatus | BuildLogLevel | string;
  type?: 'build' | 'log' | 'custom';
  className?: string;
  showIcon?: boolean;
}

export function StatusBadge({ 
  status, 
  type = 'build', 
  className,
  showIcon = true 
}: StatusBadgeProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return '✓';
      case 'running':
      case 'preparing':
        return '▶';
      case 'queued':
        return '⏸';
      case 'failed':
      case 'error':
      case 'critical':
        return '✗';
      case 'cancelled':
        return '⏹';
      case 'timeout':
        return '⏰';
      case 'warning':
        return '⚠';
      case 'info':
        return 'ℹ';
      default:
        return '';
    }
  };

  const getBadgeClasses = () => {
    if (type === 'build') {
      return getBuildStatusClasses(status as BuildStatus);
    } else if (type === 'log') {
      return getLogLevelClasses(status as BuildLogLevel);
    } else {
      return 'badge-gray';
    }
  };

  const getDisplayText = () => {
    if (type === 'build') {
      return getStatusText(status as BuildStatus);
    }
    return status.charAt(0).toUpperCase() + status.slice(1);
  };

  return (
    <span className={cn(getBadgeClasses(), className)}>
      {showIcon && getStatusIcon(status) && (
        <span className="mr-1" aria-hidden="true">
          {getStatusIcon(status)}
        </span>
      )}
      {getDisplayText()}
    </span>
  );
}

/**
 * Connection status indicator.
 */
interface ConnectionStatusProps {
  connected: boolean;
  onReconnect?: () => void;
  className?: string;
}

export function ConnectionStatus({ connected, onReconnect, className }: ConnectionStatusProps) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div
        className={cn(
          'w-2 h-2 rounded-full',
          connected ? 'bg-success-500' : 'bg-danger-500'
        )}
        aria-hidden="true"
      />
      <span className={cn('text-sm', connected ? 'text-success-700' : 'text-danger-700')}>
        {connected ? 'Connected' : 'Disconnected'}
      </span>
      {!connected && onReconnect && (
        <button
          onClick={onReconnect}
          className="text-xs px-2 py-1 bg-primary-600 text-white rounded hover:bg-primary-700 transition-colors"
          title="Reconnect WebSocket"
        >
          Reconnect
        </button>
      )}
    </div>
  );
}

/**
 * Health status indicator.
 */
interface HealthStatusProps {
  status: 'healthy' | 'degraded' | 'unhealthy' | string;
  className?: string;
}

export function HealthStatus({ status, className }: HealthStatusProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'healthy':
        return 'text-success-700 bg-success-100';
      case 'degraded':
        return 'text-warning-700 bg-warning-100';
      case 'unhealthy':
        return 'text-danger-700 bg-danger-100';
      default:
        return 'text-gray-700 bg-gray-100';
    }
  };

  return (
    <span className={cn('badge', getStatusColor(), className)}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}
