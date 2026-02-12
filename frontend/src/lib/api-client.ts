/**
 * OSImager API Client.
 * 
 * Provides type-safe HTTP client for communicating with the FastAPI backend.
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios';
import type {
  Build,
  BuildCreate,
  BuildList,
  BuildLogEntry,
  Platform,
  PlatformInfo,
  PlatformListResponse,
  PlatformCreateRequest,
  PlatformUpdateRequest,
  Location,
  Spec,
  SpecList,
  SystemInfo,
  HealthCheck,
  ApiResponse,
} from '@/types/api';

export class OSImagerAPIClient {
  private client: AxiosInstance;

  constructor(baseURL: string = '/api') {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for logging
    this.client.interceptors.request.use(
      (config) => {
        console.debug(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        console.debug(`API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        const message = error.response?.data?.detail || error.message || 'Unknown error';
        console.error('API Response Error:', message);
        
        // Transform axios error to our format
        const apiError = {
          error: message,
          status: error.response?.status,
          data: error.response?.data,
        };
        
        return Promise.reject(apiError);
      }
    );
  }

  // Health and system endpoints
  async getHealth(): Promise<HealthCheck> {
    const response = await this.client.get<HealthCheck>('/status/health');
    return response.data;
  }

  async getSystemInfo(): Promise<SystemInfo> {
    const response = await this.client.get<SystemInfo>('/status/system');
    return response.data;
  }

  // Build management endpoints
  async getBuilds(status?: string, limit: number = 50): Promise<BuildList> {
    const params: Record<string, any> = { limit };
    if (status) params.status = status;
    
    const response = await this.client.get<BuildList>('/builds/', { params });
    return response.data;
  }

  async getBuild(buildId: string): Promise<Build> {
    const response = await this.client.get<Build>(`/builds/${buildId}`);
    return response.data;
  }

  async createBuild(buildCreate: BuildCreate): Promise<Build> {
    const response = await this.client.post<Build>('/builds/', buildCreate);
    return response.data;
  }

  async cancelBuild(buildId: string): Promise<Build> {
    const response = await this.client.post<Build>(`/builds/${buildId}/cancel`);
    return response.data;
  }

  async getBuildLogs(buildId: string, limit: number = 100): Promise<BuildLogEntry[]> {
    const response = await this.client.get<BuildLogEntry[]>(
      `/builds/${buildId}/logs`,
      { params: { limit } }
    );
    return response.data;
  }

  // Spec management endpoints
  async getSpecs(): Promise<SpecList> {
    const response = await this.client.get<SpecList>('/specs/');
    return response.data;
  }

  async getSpec(specName: string): Promise<Spec> {
    const response = await this.client.get<Spec>(`/specs/${specName}`);
    return response.data;
  }

  async createSpec(specData: { name: string; content: any }): Promise<Spec> {
    const response = await this.client.post<Spec>('/specs/', specData);
    return response.data;
  }

  async updateSpec(specName: string, specData: { content: any }): Promise<Spec> {
    const response = await this.client.put<Spec>(`/specs/${specName}`, specData);
    return response.data;
  }

  async deleteSpec(specName: string): Promise<void> {
    await this.client.delete(`/specs/${specName}`);
  }

  async validateSpec(spec: Spec): Promise<{ valid: boolean; errors?: string[] }> {
    const response = await this.client.post('/specs/validate', spec);
    return response.data;
  }

  async getSpecsIndex(): Promise<Record<string, any>> {
    const response = await this.client.get<Record<string, any>>('/specs/index');
    return response.data;
  }

  async rebuildSpecsIndex(): Promise<void> {
    await this.client.post('/specs/rebuild-index');
  }

  // Platform management endpoints
  async getPlatforms(): Promise<string[]> {
    const response = await this.client.get<string[]>('/platforms/');
    return response.data;
  }

  async getPlatformsDetailed(): Promise<PlatformListResponse> {
    const response = await this.client.get<PlatformListResponse>('/platforms/list/detailed');
    return response.data;
  }

  async getPlatform(platformName: string): Promise<Platform> {
    const response = await this.client.get<Platform>(`/platforms/${platformName}`);
    return response.data;
  }

  async getPlatformInfo(platformName: string): Promise<PlatformInfo> {
    const response = await this.client.get<PlatformInfo>(`/platforms/${platformName}/info`);
    return response.data;
  }

  async createPlatform(platform: PlatformCreateRequest): Promise<Platform> {
    const response = await this.client.post<Platform>('/platforms/', platform);
    return response.data;
  }

  async updatePlatform(platformName: string, platform: PlatformUpdateRequest): Promise<Platform> {
    const response = await this.client.put<Platform>(`/platforms/${platformName}`, platform);
    return response.data;
  }

  async deletePlatform(platformName: string): Promise<void> {
    await this.client.delete(`/platforms/${platformName}`);
  }

  async validatePlatform(config: Record<string, any>): Promise<{ valid: boolean; errors?: string[] }> {
    const response = await this.client.post('/platforms/validate', config);
    return response.data;
  }

  // Location management endpoints
  async getLocations(): Promise<string[]> {
    const response = await this.client.get<string[]>('/locations/');
    return response.data;
  }

  async getLocation(locationName: string): Promise<Location> {
    const response = await this.client.get<Location>(`/locations/${locationName}`);
    return response.data;
  }

  async createLocation(location: Location): Promise<Location> {
    const response = await this.client.post<Location>('/locations/', location);
    return response.data;
  }

  async updateLocation(locationName: string, location: Partial<Location>): Promise<Location> {
    const response = await this.client.put<Location>(`/locations/${locationName}`, location);
    return response.data;
  }

  async deleteLocation(locationName: string): Promise<void> {
    await this.client.delete(`/locations/${locationName}`);
  }

  // Status endpoint
  async getStatus(): Promise<any> {
    const response = await this.client.get('/status/system');
    return response.data;
  }

  // Configuration endpoints
  async getUserConfig(): Promise<any> {
    const response = await this.client.get('/config/user');
    return response.data;
  }

  async updateUserConfig(config: any): Promise<any> {
    const response = await this.client.put('/config/user', config);
    return response.data;
  }

  async getSystemConfig(): Promise<any> {
    const response = await this.client.get('/config/system');
    return response.data;
  }

  async resetUserConfig(): Promise<any> {
    const response = await this.client.post('/config/reset');
    return response.data;
  }

  async exportConfig(): Promise<any> {
    const response = await this.client.get('/config/export');
    return response.data;
  }

  async importConfig(configData: any): Promise<any> {
    const response = await this.client.post('/config/import', configData);
    return response.data;
  }
}

// Create and export singleton instance
export const apiClient = new OSImagerAPIClient();

// Export for dependency injection in tests
export default OSImagerAPIClient;
