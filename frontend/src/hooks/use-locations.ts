/**
 * React hooks for location data management.
 * 
 * Provides hooks for fetching, creating, updating, and deleting locations.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { LocationInfo, LocationListResponse } from '@/types/api';

// API client methods for locations using fetch directly
const locationsApi = {
  // Get all location names
  getLocationNames: async (): Promise<string[]> => {
    try {
      const response = await fetch('/backend/locations/');
      if (!response.ok) {
        throw new Error('Failed to fetch location names');
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching location names:', error);
      throw error;
    }
  },

  // Get detailed location information
  getLocationsDetailed: async (): Promise<LocationListResponse> => {
    try {
      const response = await fetch('/backend/locations/detailed');
      if (!response.ok) {
        throw new Error('Failed to fetch locations');
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching detailed locations:', error);
      throw error;
    }
  },

  // Get specific location
  getLocation: async (name: string): Promise<Record<string, any>> => {
    try {
      const response = await fetch(`/backend/locations/${name}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch location ${name}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`Error fetching location ${name}:`, error);
      throw error;
    }
  },

  // Get location info with metadata
  getLocationInfo: async (name: string): Promise<LocationInfo> => {
    try {
      const response = await fetch(`/backend/locations/${name}/info`);
      if (!response.ok) {
        throw new Error(`Failed to fetch location info for ${name}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`Error fetching location info for ${name}:`, error);
      throw error;
    }
  },

  // Create new location
  createLocation: async (location: {
    name: string;
    description?: string;
    platforms?: string[];
    arches?: string[];
    defs?: Record<string, any>;
    config?: Record<string, any>;
    platform_specific?: Array<Record<string, any>>;
  }): Promise<{ message: string }> => {
    try {
      const response = await fetch('/backend/locations/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(location),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create location');
      }
      return await response.json();
    } catch (error) {
      console.error('Error creating location:', error);
      throw error;
    }
  },

  // Update existing location
  updateLocation: async (name: string, location: {
    name: string;
    description?: string;
    platforms?: string[];
    arches?: string[];
    defs?: Record<string, any>;
    config?: Record<string, any>;
    platform_specific?: Array<Record<string, any>>;
  }): Promise<{ message: string }> => {
    try {
      const response = await fetch(`/backend/locations/${name}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(location),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update location');
      }
      return await response.json();
    } catch (error) {
      console.error('Error updating location:', error);
      throw error;
    }
  },

  // Delete location
  deleteLocation: async (name: string): Promise<{ message: string }> => {
    try {
      const response = await fetch(`/backend/locations/${name}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete location');
      }
      return await response.json();
    } catch (error) {
      console.error('Error deleting location:', error);
      throw error;
    }
  },

  // Validate location
  validateLocation: async (name: string): Promise<{
    valid: boolean;
    issues: string[];
    warnings: string[];
    summary: Record<string, any>;
  }> => {
    try {
      const response = await fetch(`/backend/locations/${name}/validate`, {
        method: 'POST',
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to validate location');
      }
      return await response.json();
    } catch (error) {
      console.error('Error validating location:', error);
      throw error;
    }
  },
};

// Query keys for React Query
export const locationKeys = {
  all: ['locations'] as const,
  names: () => [...locationKeys.all, 'names'] as const,
  detailed: () => [...locationKeys.all, 'detailed'] as const,
  detail: (name: string) => [...locationKeys.all, 'detail', name] as const,
  info: (name: string) => [...locationKeys.all, 'info', name] as const,
  validate: (name: string) => [...locationKeys.all, 'validate', name] as const,
};

// Hook to get location names
export function useLocationNames() {
  return useQuery({
    queryKey: locationKeys.names(),
    queryFn: locationsApi.getLocationNames,
    staleTime: 30000, // 30 seconds
  });
}

// Hook to get detailed location information
export function useLocationsDetailed() {
  return useQuery({
    queryKey: locationKeys.detailed(),
    queryFn: locationsApi.getLocationsDetailed,
    staleTime: 30000, // 30 seconds
  });
}

// Hook to get specific location configuration
export function useLocation(name: string, enabled = true) {
  return useQuery({
    queryKey: locationKeys.detail(name),
    queryFn: () => locationsApi.getLocation(name),
    enabled: enabled && !!name,
    staleTime: 30000, // 30 seconds
  });
}

// Hook to get location info with metadata
export function useLocationInfo(name: string, enabled = true) {
  return useQuery({
    queryKey: locationKeys.info(name),
    queryFn: () => locationsApi.getLocationInfo(name),
    enabled: enabled && !!name,
    staleTime: 30000, // 30 seconds
  });
}

// Hook to validate location
export function useLocationValidation(name: string, enabled = true) {
  return useQuery({
    queryKey: locationKeys.validate(name),
    queryFn: () => locationsApi.validateLocation(name),
    enabled: enabled && !!name,
    staleTime: 60000, // 1 minute
    retry: false, // Don't retry validation failures
  });
}

// Hook to create a new location
export function useCreateLocation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: locationsApi.createLocation,
    onSuccess: () => {
      // Invalidate and refetch location queries
      queryClient.invalidateQueries({ queryKey: locationKeys.all });
    },
    onError: (error: any) => {
      console.error('Error creating location:', error);
      // You could add toast notifications here
    },
  });
}

// Hook to update an existing location
export function useUpdateLocation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ name, location }: { 
      name: string; 
      location: Parameters<typeof locationsApi.updateLocation>[1] 
    }) => locationsApi.updateLocation(name, location),
    onSuccess: (data, variables) => {
      // Invalidate and refetch location queries
      queryClient.invalidateQueries({ queryKey: locationKeys.all });
      
      // If location was renamed, also invalidate the old name
      if (variables.location.name !== variables.name) {
        queryClient.invalidateQueries({ 
          queryKey: locationKeys.detail(variables.name) 
        });
        queryClient.invalidateQueries({ 
          queryKey: locationKeys.info(variables.name) 
        });
      }
    },
    onError: (error: any) => {
      console.error('Error updating location:', error);
      // You could add toast notifications here
    },
  });
}

// Hook to delete a location
export function useDeleteLocation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: locationsApi.deleteLocation,
    onSuccess: (data, locationName) => {
      // Invalidate and refetch location queries
      queryClient.invalidateQueries({ queryKey: locationKeys.all });
      
      // Remove specific location queries from cache
      queryClient.removeQueries({ 
        queryKey: locationKeys.detail(locationName) 
      });
      queryClient.removeQueries({ 
        queryKey: locationKeys.info(locationName) 
      });
      queryClient.removeQueries({ 
        queryKey: locationKeys.validate(locationName) 
      });
    },
    onError: (error: any) => {
      console.error('Error deleting location:', error);
      // You could add toast notifications here
    },
  });
}

// Hook for bulk operations (future enhancement)
export function useBulkLocationOperations() {
  const queryClient = useQueryClient();

  const validateMultiple = useMutation({
    mutationFn: async (names: string[]) => {
      const results = await Promise.allSettled(
        names.map(name => locationsApi.validateLocation(name))
      );
      return results.map((result, index) => ({
        name: names[index],
        result: result.status === 'fulfilled' ? result.value : null,
        error: result.status === 'rejected' ? result.reason : null,
      }));
    },
  });

  const deleteMultiple = useMutation({
    mutationFn: async (names: string[]) => {
      const results = await Promise.allSettled(
        names.map(name => locationsApi.deleteLocation(name))
      );
      return results.map((result, index) => ({
        name: names[index],
        success: result.status === 'fulfilled',
        error: result.status === 'rejected' ? result.reason : null,
      }));
    },
    onSuccess: () => {
      // Invalidate all location queries after bulk delete
      queryClient.invalidateQueries({ queryKey: locationKeys.all });
    },
  });

  return {
    validateMultiple,
    deleteMultiple,
  };
}

// Utility hook for location statistics
export function useLocationStats() {
  const { data: locationsData } = useLocationsDetailed();
  
  if (!locationsData) {
    return {
      total: 0,
      byPlatform: {},
      byArch: {},
      totalDefs: 0,
      averageSize: 0,
    };
  }

  const locations = locationsData.locations;
  
  // Calculate statistics
  const byPlatform: Record<string, number> = {};
  const byArch: Record<string, number> = {};
  let totalDefs = 0;
  let totalSize = 0;

  locations.forEach(location => {
    // Count by platform
    location.platforms.forEach(platform => {
      byPlatform[platform] = (byPlatform[platform] || 0) + 1;
    });

    // Count by architecture
    location.arches.forEach(arch => {
      byArch[arch] = (byArch[arch] || 0) + 1;
    });

    // Count definitions
    totalDefs += Object.keys(location.defs).length;
    totalSize += location.size;
  });

  return {
    total: locations.length,
    byPlatform,
    byArch,
    totalDefs,
    averageSize: locations.length > 0 ? totalSize / locations.length : 0,
  };
}
