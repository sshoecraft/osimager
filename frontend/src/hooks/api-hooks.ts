/**
 * React Query hooks for OSImager API operations.
 * 
 * Provides type-safe, cached API operations with error handling and optimistic updates.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { apiClient } from '@/lib/api-client';
import { useAppStore } from '@/stores/app-store';
import type {
  Build,
  BuildCreate,
  BuildList,
  Platform,
  Location,
  Spec,
  SpecList,
  SystemInfo,
  HealthCheck,
  BuildLogEntry,
} from '@/types/api';

// Query keys
export const queryKeys = {
  health: ['health'] as const,
  systemInfo: ['systemInfo'] as const,
  builds: ['builds'] as const,
  buildsList: (status?: string, limit?: number) => ['builds', 'list', { status, limit }] as const,
  build: (id: string) => ['builds', id] as const,
  buildLogs: (id: string, limit?: number) => ['builds', id, 'logs', { limit }] as const,
  platforms: ['platforms'] as const,
  platform: (name: string) => ['platforms', name] as const,
  locations: ['locations'] as const,
  location: (name: string) => ['locations', name] as const,
  specs: ['specs'] as const,
  specsIndex: ['specs', 'index'] as const,
  spec: (name: string) => ['specs', name] as const,
  status: ['status'] as const,
  config: ['config'] as const,
  systemConfig: ['config', 'system'] as const,
};

// Health and system info hooks
export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: () => apiClient.getHealth(),
    refetchInterval: 30000, // Refetch every 30 seconds
    staleTime: 20000, // Consider stale after 20 seconds
  });
}

export function useSystemInfo() {
  return useQuery({
    queryKey: queryKeys.systemInfo,
    queryFn: () => apiClient.getSystemInfo(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
}

// Build hooks
export function useBuilds(status?: string, limit: number = 50) {
  const setBuilds = useAppStore(state => state.setBuilds);
  
  const query = useQuery({
    queryKey: queryKeys.buildsList(status, limit),
    queryFn: () => apiClient.getBuilds(status, limit),
    refetchInterval: 10000, // Refetch every 10 seconds
    staleTime: 30000, // Consider fresh for 30 seconds
    retry: 2, // Only retry twice on failure
  });

  // Update store when data changes
  if (query.data) {
    setBuilds(query.data);
  }

  return query;
}

export function useBuild(buildId: string | null) {
  return useQuery({
    queryKey: queryKeys.build(buildId!),
    queryFn: () => apiClient.getBuild(buildId!),
    enabled: !!buildId,
    refetchInterval: 2000, // Refetch every 2 seconds for real-time updates
  });
}

export function useBuildLogs(buildId: string | null, limit: number = 100) {
  return useQuery({
    queryKey: queryKeys.buildLogs(buildId!, limit),
    queryFn: () => apiClient.getBuildLogs(buildId!, limit),
    enabled: !!buildId,
    refetchInterval: 3000, // Refetch logs every 3 seconds
  });
}

export function useCreateBuild() {
  const queryClient = useQueryClient();
  const addBuild = useAppStore(state => state.addBuild);
  
  return useMutation({
    mutationFn: (buildData: BuildCreate) => apiClient.createBuild(buildData),
    onSuccess: (newBuild: Build) => {
      // Add to store immediately
      addBuild(newBuild);
      
      // Invalidate builds list to refetch
      queryClient.invalidateQueries({ queryKey: queryKeys.builds });
      
      toast.success(`Build ${newBuild.id} created successfully`);
    },
    onError: (error: any) => {
      toast.error(`Failed to create build: ${error.error || error.message}`);
    },
  });
}

export function useCancelBuild() {
  const queryClient = useQueryClient();
  const updateBuild = useAppStore(state => state.updateBuild);
  
  return useMutation({
    mutationFn: (buildId: string) => apiClient.cancelBuild(buildId),
    onSuccess: (updatedBuild: Build) => {
      // Update store immediately
      updateBuild(updatedBuild.id, updatedBuild);
      
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.build(updatedBuild.id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.builds });
      
      toast.success(`Build ${updatedBuild.id} cancelled`);
    },
    onError: (error: any) => {
      toast.error(`Failed to cancel build: ${error.error || error.message}`);
    },
  });
}

// Platform hooks
export function usePlatforms() {
  const setPlatforms = useAppStore(state => state.setPlatforms);
  
  const query = useQuery({
    queryKey: queryKeys.platforms,
    queryFn: () => apiClient.getPlatforms(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });

  // Update store when data changes
  if (query.data) {
    // Transform string array to Platform objects for the store
    const platforms = query.data.map(name => ({ 
      name, 
      type: 'unknown', 
      config: {} 
    } as Platform));
    setPlatforms(platforms);
  }

  return query;
}

export function usePlatform(platformName: string | null) {
  return useQuery({
    queryKey: queryKeys.platform(platformName!),
    queryFn: () => apiClient.getPlatform(platformName!),
    enabled: !!platformName,
    staleTime: 10 * 60 * 1000,
  });
}

export function useCreatePlatform() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (platform: Platform) => apiClient.createPlatform(platform),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.platforms });
      toast.success('Platform created successfully');
    },
    onError: (error: any) => {
      toast.error(`Failed to create platform: ${error.error || error.message}`);
    },
  });
}

export function useUpdatePlatform() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ name, platform }: { name: string; platform: Partial<Platform> }) =>
      apiClient.updatePlatform(name, platform),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.platforms });
      queryClient.invalidateQueries({ queryKey: queryKeys.platform(variables.name) });
      toast.success('Platform updated successfully');
    },
    onError: (error: any) => {
      toast.error(`Failed to update platform: ${error.error || error.message}`);
    },
  });
}

export function useDeletePlatform() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (platformName: string) => apiClient.deletePlatform(platformName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.platforms });
      toast.success('Platform deleted successfully');
    },
    onError: (error: any) => {
      toast.error(`Failed to delete platform: ${error.error || error.message}`);
    },
  });
}

// Location hooks
export function useLocations() {
  const setLocations = useAppStore(state => state.setLocations);
  
  const query = useQuery({
    queryKey: queryKeys.locations,
    queryFn: () => apiClient.getLocations(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });

  // Update store when data changes
  if (query.data) {
    // Transform string array to Location objects for the store
    const locations = query.data.map(name => ({ 
      name, 
      config: {} 
    } as Location));
    setLocations(locations);
  }

  return query;
}

export function useLocation(locationName: string | null) {
  return useQuery({
    queryKey: queryKeys.location(locationName!),
    queryFn: () => apiClient.getLocation(locationName!),
    enabled: !!locationName,
    staleTime: 10 * 60 * 1000,
  });
}

export function useCreateLocation() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (location: Location) => apiClient.createLocation(location),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.locations });
      toast.success('Location created successfully');
    },
    onError: (error: any) => {
      toast.error(`Failed to create location: ${error.error || error.message}`);
    },
  });
}

export function useUpdateLocation() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ name, location }: { name: string; location: Partial<Location> }) =>
      apiClient.updateLocation(name, location),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.locations });
      queryClient.invalidateQueries({ queryKey: queryKeys.location(variables.name) });
      toast.success('Location updated successfully');
    },
    onError: (error: any) => {
      toast.error(`Failed to update location: ${error.error || error.message}`);
    },
  });
}

export function useDeleteLocation() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (locationName: string) => apiClient.deleteLocation(locationName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.locations });
      toast.success('Location deleted successfully');
    },
    onError: (error: any) => {
      toast.error(`Failed to delete location: ${error.error || error.message}`);
    },
  });
}

// Spec hooks
export function useSpecs() {
  const setSpecs = useAppStore(state => state.setSpecs);
  
  const query = useQuery({
    queryKey: queryKeys.specs,
    queryFn: () => apiClient.getSpecs(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });

  // Update store when data changes
  if (query.data) {
    // Transform SpecMetadata array to Spec objects for the store
    const specs = query.data.specs.map(meta => ({ 
      name: meta.name, 
      config: {},
      metadata: meta
    } as Spec));
    setSpecs(specs);
  }

  return query;
}

export function useSpec(specName: string | null) {
  return useQuery({
    queryKey: queryKeys.spec(specName!),
    queryFn: () => apiClient.getSpec(specName!),
    enabled: !!specName,
    staleTime: 10 * 60 * 1000,
  });
}

export function useCreateSpec() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (specData: { name: string; content: any }) => apiClient.createSpec(specData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.specs });
      toast.success('Spec created successfully');
    },
    onError: (error: any) => {
      toast.error(`Failed to create spec: ${error.error || error.message}`);
    },
  });
}

export function useUpdateSpec() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ name, content }: { name: string; content: any }) =>
      apiClient.updateSpec(name, { content }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.specs });
      queryClient.invalidateQueries({ queryKey: queryKeys.spec(variables.name) });
      toast.success('Spec updated successfully');
    },
    onError: (error: any) => {
      toast.error(`Failed to update spec: ${error.error || error.message}`);
    },
  });
}

export function useDeleteSpec() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (specName: string) => apiClient.deleteSpec(specName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.specs });
      toast.success('Spec deleted successfully');
    },
    onError: (error: any) => {
      toast.error(`Failed to delete spec: ${error.error || error.message}`);
    },
  });
}

export function useValidateSpec() {
  return useMutation({
    mutationFn: (spec: Spec) => apiClient.validateSpec(spec),
    onError: (error: any) => {
      toast.error(`Spec validation failed: ${error.error || error.message}`);
    },
  });
}

export function useSpecsIndex() {
  return useQuery({
    queryKey: queryKeys.specsIndex,
    queryFn: () => apiClient.getSpecsIndex(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
}

export function useRebuildSpecsIndex() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => apiClient.rebuildSpecsIndex(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.specsIndex });
      queryClient.invalidateQueries({ queryKey: queryKeys.specs });
      toast.success('Specs index rebuilt successfully');
    },
    onError: (error: any) => {
      toast.error(`Failed to rebuild specs index: ${error.error || error.message}`);
    },
  });
}

// Status hook
export function useStatus() {
  return useQuery({
    queryKey: queryKeys.status,
    queryFn: () => apiClient.getStatus(),
    refetchInterval: 15000, // Refetch every 15 seconds
    staleTime: 10000, // Consider fresh for 10 seconds
    retry: 2,
  });
}

// Configuration hooks
export function useUserConfig() {
  return useQuery({
    queryKey: queryKeys.config,
    queryFn: () => apiClient.getUserConfig(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
}

export function useSystemConfig() {
  return useQuery({
    queryKey: queryKeys.systemConfig,
    queryFn: () => apiClient.getSystemConfig(),
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: 2,
  });
}

export function useUpdateUserConfig() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (config: any) => apiClient.updateUserConfig(config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.config });
      toast.success('Configuration saved successfully');
    },
    onError: (error: any) => {
      toast.error(`Failed to save configuration: ${error.error || error.message}`);
    },
  });
}

export function useResetUserConfig() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => apiClient.resetUserConfig(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.config });
      toast.success('Configuration reset to defaults');
    },
    onError: (error: any) => {
      toast.error(`Failed to reset configuration: ${error.error || error.message}`);
    },
  });
}

export function useExportConfig() {
  return useMutation({
    mutationFn: () => apiClient.exportConfig(),
    onSuccess: (data) => {
      // Create download
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `osimager-config-${new Date().toISOString().split('T')[0]}.json`;
      link.click();
      URL.revokeObjectURL(url);
      
      toast.success('Configuration exported successfully');
    },
    onError: (error: any) => {
      toast.error(`Failed to export configuration: ${error.error || error.message}`);
    },
  });
}

export function useImportConfig() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (configData: any) => apiClient.importConfig(configData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.config });
      toast.success('Configuration imported successfully');
    },
    onError: (error: any) => {
      toast.error(`Failed to import configuration: ${error.error || error.message}`);
    },
  });
}
