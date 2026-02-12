/**
 * Utility functions for the OSImager frontend.
 */

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { format, formatDistanceToNow, isValid, parseISO } from 'date-fns';
import type { BuildStatus, BuildLogLevel } from '@/types/api';

/**
 * Combine class names with Tailwind CSS conflict resolution.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format date string or Date object for display.
 */
export function formatDate(date: string | Date | null | undefined): string {
  if (!date) return 'N/A';
  
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  
  if (!isValid(dateObj)) return 'Invalid date';
  
  return format(dateObj, 'MMM dd, yyyy HH:mm:ss');
}

/**
 * Format relative time (e.g., "2 minutes ago").
 */
export function formatRelativeTime(date: string | Date | null | undefined): string {
  if (!date) return 'N/A';
  
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  
  if (!isValid(dateObj)) return 'Invalid date';
  
  return formatDistanceToNow(dateObj, { addSuffix: true });
}

/**
 * Format duration in seconds to human readable format.
 */
export function formatDuration(seconds: number | null | undefined): string {
  if (!seconds || seconds < 0) return 'N/A';
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours}h ${minutes}m ${remainingSeconds}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${remainingSeconds}s`;
  } else {
    return `${remainingSeconds}s`;
  }
}

/**
 * Format file size in bytes to human readable format.
 */
export function formatFileSize(bytes: number | null | undefined): string {
  if (!bytes || bytes < 0) return 'N/A';
  
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let size = bytes;
  let unitIndex = 0;
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  
  return `${size.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
}

/**
 * Get CSS classes for build status badge.
 */
export function getBuildStatusClasses(status: BuildStatus): string {
  switch (status) {
    case 'completed':
      return 'badge-success';
    case 'running':
    case 'preparing':
      return 'badge-info';
    case 'queued':
      return 'badge-warning';
    case 'failed':
    case 'timeout':
      return 'badge-danger';
    case 'cancelled':
      return 'badge-gray';
    default:
      return 'badge-gray';
  }
}

/**
 * Get CSS classes for log level badge.
 */
export function getLogLevelClasses(level: BuildLogLevel): string {
  switch (level) {
    case 'error':
    case 'critical':
      return 'badge-danger';
    case 'warning':
      return 'badge-warning';
    case 'info':
      return 'badge-info';
    case 'debug':
      return 'badge-gray';
    default:
      return 'badge-gray';
  }
}

/**
 * Get user-friendly status text.
 */
export function getStatusText(status: BuildStatus): string {
  switch (status) {
    case 'queued':
      return 'Queued';
    case 'preparing':
      return 'Preparing';
    case 'running':
      return 'Running';
    case 'completed':
      return 'Completed';
    case 'failed':
      return 'Failed';
    case 'cancelled':
      return 'Cancelled';
    case 'timeout':
      return 'Timeout';
    default:
      return status;
  }
}

/**
 * Check if a build status is active (can be cancelled).
 */
export function isBuildActive(status: BuildStatus): boolean {
  return ['queued', 'preparing', 'running'].includes(status);
}

/**
 * Check if a build status is completed (finished).
 */
export function isBuildCompleted(status: BuildStatus): boolean {
  return ['completed', 'failed', 'cancelled', 'timeout'].includes(status);
}

/**
 * Generate a random ID for temporary use.
 */
export function generateId(): string {
  return Math.random().toString(36).substring(2, 15) + 
         Math.random().toString(36).substring(2, 15);
}

/**
 * Debounce function calls.
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(null, args), wait);
  };
}

/**
 * Throttle function calls.
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func.apply(null, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

/**
 * Download data as a file.
 */
export function downloadAsFile(data: string, filename: string, mimeType = 'text/plain'): void {
  const blob = new Blob([data], { type: mimeType });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Copy text to clipboard.
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    } else {
      // Fallback for older browsers or non-secure contexts
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      textArea.style.top = '-999999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      
      const success = document.execCommand('copy');
      document.body.removeChild(textArea);
      return success;
    }
  } catch (error) {
    console.error('Failed to copy to clipboard:', error);
    return false;
  }
}

/**
 * Validate JSON string.
 */
export function isValidJSON(str: string): boolean {
  try {
    JSON.parse(str);
    return true;
  } catch {
    return false;
  }
}

/**
 * Pretty print JSON with syntax highlighting classes.
 */
export function formatJSON(obj: any): string {
  return JSON.stringify(obj, null, 2);
}

/**
 * Extract error message from various error types.
 */
export function getErrorMessage(error: any): string {
  if (typeof error === 'string') {
    return error;
  }
  
  if (error?.message) {
    return error.message;
  }
  
  if (error?.error) {
    return error.error;
  }
  
  if (error?.detail) {
    return error.detail;
  }
  
  return 'An unknown error occurred';
}

/**
 * Safely parse JSON with fallback.
 */
export function safeJSONParse<T = any>(str: string, fallback: T): T {
  try {
    return JSON.parse(str);
  } catch {
    return fallback;
  }
}

/**
 * Create a promise that resolves after specified milliseconds.
 */
export function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Retry a function with exponential backoff.
 */
export async function retry<T>(
  fn: () => Promise<T>,
  maxAttempts = 3,
  baseDelay = 1000
): Promise<T> {
  let lastError: any;
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      if (attempt === maxAttempts) {
        throw lastError;
      }
      
      const delayMs = baseDelay * Math.pow(2, attempt - 1);
      await delay(delayMs);
    }
  }
  
  throw lastError;
}
