/**
 * React hooks for platform management.
 * 
 * Provides hooks for CRUD operations on OSImager platforms.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type { 
  PlatformInfo, 
  PlatformListResponse, 
  PlatformCreateRequest, 
  PlatformUpdateRequest 
} from '@/types/api';

// Query keys for React Query cache management
export const platformKeys = {
  all: ['platforms'] as const,
  lists: () => [...platformKeys.all, 'list'] as const,
  list: (filters: string) => [...platformKeys.lists(), { filters }] as const,
  details: () => [...platformKeys.all, 'detail'] as const,
  detail: (id: string) => [...platformKeys.details(), id] as const,
};

// Custom error type for platform operations
export interface PlatformError {
  message: string;
  status?: number;
  data?: any;
}

/**
 * Hook to get list of platform names.
 */
export function usePlatforms() {
  return useQuery({
    queryKey: platformKeys.lists(),
    queryFn: () => apiClient.getPlatforms(),
    staleTime: 30000, // 30 seconds
  });
}

/**
 * Hook to get detailed platform list with metadata.
 */
export function usePlatformsDetailed() {
  return useQuery<PlatformListResponse, PlatformError>({
    queryKey: [...platformKeys.lists(), 'detailed'],
    queryFn: () => apiClient.getPlatformsDetailed(),
    staleTime: 30000, // 30 seconds
  });
}

/**
 * Hook to get a specific platform configuration.
 */
export function usePlatform(platformName: string) {
  return useQuery({
    queryKey: platformKeys.detail(platformName),
    queryFn: () => apiClient.getPlatform(platformName),
    enabled: !!platformName,
    staleTime: 60000, // 1 minute
  });
}

/**
 * Hook to get platform info with metadata.
 */
export function usePlatformInfo(platformName: string) {
  return useQuery<PlatformInfo, PlatformError>({
    queryKey: [...platformKeys.detail(platformName), 'info'],
    queryFn: () => apiClient.getPlatformInfo(platformName),
    enabled: !!platformName,
    staleTime: 60000, // 1 minute
  });
}

/**
 * Hook to create a new platform.
 */
export function useCreatePlatform() {
  const queryClient = useQueryClient();

  return useMutation<any, PlatformError, PlatformCreateRequest>({
    mutationFn: (platform: PlatformCreateRequest) => apiClient.createPlatform(platform),
    onSuccess: () => {
      // Invalidate and refetch platform lists
      queryClient.invalidateQueries({ queryKey: platformKeys.lists() });
    },
    onError: (error: any) => {
      console.error('Error creating platform:', error);
    },
  });
}

/**
 * Hook to update an existing platform.
 */
export function useUpdatePlatform() {
  const queryClient = useQueryClient();

  return useMutation<any, PlatformError, { name: string; platform: PlatformUpdateRequest }>({
    mutationFn: ({ name, platform }) => apiClient.updatePlatform(name, platform),
    onSuccess: (data, variables) => {
      // Invalidate affected queries
      queryClient.invalidateQueries({ queryKey: platformKeys.lists() });
      queryClient.invalidateQueries({ queryKey: platformKeys.detail(variables.name) });
    },
    onError: (error: any) => {
      console.error('Error updating platform:', error);
    },
  });
}

/**
 * Hook to delete a platform.
 */
export function useDeletePlatform() {
  const queryClient = useQueryClient();

  return useMutation<void, PlatformError, string>({
    mutationFn: (platformName: string) => apiClient.deletePlatform(platformName),
    onSuccess: (data, platformName) => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: platformKeys.lists() });
      queryClient.removeQueries({ queryKey: platformKeys.detail(platformName) });
    },
    onError: (error: any) => {
      console.error('Error deleting platform:', error);
    },
  });
}

/**
 * Hook to validate platform configuration.
 */
export function useValidatePlatform() {
  return useMutation<{ valid: boolean; errors?: string[] }, PlatformError, Record<string, any>>({
    mutationFn: (config: Record<string, any>) => apiClient.validatePlatform(config),
    onError: (error: any) => {
      console.error('Error validating platform:', error);
    },
  });
}

/**
 * Utility hook to check if a platform name is available.
 */
export function usePlatformExists(platformName: string) {
  const { data: platforms } = usePlatforms();
  
  return {
    exists: platforms?.includes(platformName) ?? false,
    isLoading: !platforms,
  };
}
