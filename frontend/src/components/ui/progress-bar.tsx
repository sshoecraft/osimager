/**
 * Progress Bar component for build progress visualization.
 */

import { cn } from '@/lib/utils';
import type { BuildProgress } from '@/types/api';

interface ProgressBarProps {
  progress: BuildProgress;
  className?: string;
  showDetails?: boolean;
}

export function ProgressBar({ progress, className, showDetails = true }: ProgressBarProps) {
  const { current_step, step_number, total_steps, percentage, estimated_remaining } = progress;

  return (
    <div className={cn('space-y-2', className)}>
      {showDetails && (
        <div className="flex justify-between text-sm text-gray-600">
          <span>
            Step {step_number} of {total_steps}: {current_step}
          </span>
          <span>{Math.round(percentage)}%</span>
        </div>
      )}
      
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="bg-primary-600 h-2 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${Math.min(100, Math.max(0, percentage))}%` }}
          role="progressbar"
          aria-valuenow={percentage}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`Build progress: ${Math.round(percentage)}%`}
        />
      </div>
      
      {showDetails && estimated_remaining && (
        <div className="text-xs text-gray-500">
          Estimated remaining: {Math.ceil(estimated_remaining / 60)} minutes
        </div>
      )}
    </div>
  );
}

/**
 * Simple progress bar without details.
 */
interface SimpleProgressBarProps {
  percentage: number;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  color?: 'primary' | 'success' | 'warning' | 'danger';
}

export function SimpleProgressBar({ 
  percentage, 
  className, 
  size = 'md',
  color = 'primary' 
}: SimpleProgressBarProps) {
  const sizeClasses = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  };

  const colorClasses = {
    primary: 'bg-primary-600',
    success: 'bg-success-600',
    warning: 'bg-warning-600',
    danger: 'bg-danger-600',
  };

  return (
    <div className={cn('w-full bg-gray-200 rounded-full', sizeClasses[size], className)}>
      <div
        className={cn(
          'rounded-full transition-all duration-300 ease-out',
          sizeClasses[size],
          colorClasses[color]
        )}
        style={{ width: `${Math.min(100, Math.max(0, percentage))}%` }}
        role="progressbar"
        aria-valuenow={percentage}
        aria-valuemin={0}
        aria-valuemax={100}
      />
    </div>
  );
}

/**
 * Circular progress indicator.
 */
interface CircularProgressProps {
  percentage: number;
  size?: number;
  strokeWidth?: number;
  className?: string;
  showPercentage?: boolean;
}

export function CircularProgress({ 
  percentage, 
  size = 60, 
  strokeWidth = 4,
  className,
  showPercentage = true 
}: CircularProgressProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div className={cn('relative', className)} style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        className="transform -rotate-90"
        aria-label={`Progress: ${Math.round(percentage)}%`}
      >
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="none"
          className="text-gray-200"
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="text-primary-600 transition-all duration-300 ease-out"
        />
      </svg>
      {showPercentage && (
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xs font-medium text-gray-900">
            {Math.round(percentage)}%
          </span>
        </div>
      )}
    </div>
  );
}
