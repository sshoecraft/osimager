/**
 * Main application store using Zustand.
 * 
 * Manages global application state including builds, WebSocket connection,
 * and real-time updates.
 */

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import type {
  Build,
  BuildList,
  Platform,
  Location,
  Spec,
  SystemInfo,
  HealthCheck,
  BuildLogEntry,
  BuildProgress,
  NotificationState,
} from '@/types/api';

interface AppState {
  // Connection state
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
  
  // System information
  systemInfo: SystemInfo | null;
  health: HealthCheck | null;
  
  // Build state
  builds: Build[];
  activeBuildCount: number;
  totalBuildCount: number;
  selectedBuildId: string | null;
  
  // Configuration state
  platforms: Platform[];
  locations: Location[];
  specs: Spec[];
  
  // Real-time updates
  realtimeEnabled: boolean;
  lastUpdate: Date | null;
  
  // Notifications
  notifications: NotificationState[];
  
  // Actions
  setConnected: (connected: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  
  setSystemInfo: (info: SystemInfo) => void;
  setHealth: (health: HealthCheck) => void;
  
  setBuilds: (buildList: BuildList) => void;
  addBuild: (build: Build) => void;
  updateBuild: (buildId: string, update: Partial<Build>) => void;
  removeBuild: (buildId: string) => void;
  setSelectedBuildId: (buildId: string | null) => void;
  
  setPlatforms: (platforms: Platform[]) => void;
  setLocations: (locations: Location[]) => void;
  setSpecs: (specs: Spec[]) => void;
  
  setRealtimeEnabled: (enabled: boolean) => void;
  updateLastUpdate: () => void;
  
  addNotification: (notification: Omit<NotificationState, 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
  
  // Computed getters
  getActiveBuild: () => Build | null;
  getBuildById: (id: string) => Build | null;
  getActiveBuilds: () => Build[];
  getCompletedBuilds: () => Build[];
}

export const useAppStore = create<AppState>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // Initial state
      isConnected: false,
      isLoading: false,
      error: null,
      
      systemInfo: null,
      health: null,
      
      builds: [],
      activeBuildCount: 0,
      totalBuildCount: 0,
      selectedBuildId: null,
      
      platforms: [],
      locations: [],
      specs: [],
      
      realtimeEnabled: true,
      lastUpdate: null,
      
      notifications: [],
      
      // Actions
      setConnected: (connected) => set({ isConnected: connected }),
      setLoading: (loading) => set({ isLoading: loading }),
      setError: (error) => set({ error }),
      
      setSystemInfo: (systemInfo) => set({ systemInfo }),
      setHealth: (health) => set({ health }),
      
      setBuilds: (buildList) => set({
        builds: buildList.builds,
        activeBuildCount: buildList.active,
        totalBuildCount: buildList.total,
      }),
      
      addBuild: (build) => set((state) => ({
        builds: [build, ...state.builds],
        totalBuildCount: state.totalBuildCount + 1,
        activeBuildCount: ['queued', 'preparing', 'running'].includes(build.status)
          ? state.activeBuildCount + 1
          : state.activeBuildCount,
      })),
      
      updateBuild: (buildId, update) => set((state) => {
        const buildIndex = state.builds.findIndex(b => b.id === buildId);
        if (buildIndex === -1) return state;
        
        const oldBuild = state.builds[buildIndex];
        const newBuild = { ...oldBuild, ...update };
        const newBuilds = [...state.builds];
        newBuilds[buildIndex] = newBuild;
        
        // Recalculate active count if status changed
        let activeBuildCount = state.activeBuildCount;
        const wasActive = ['queued', 'preparing', 'running'].includes(oldBuild.status);
        const isActive = ['queued', 'preparing', 'running'].includes(newBuild.status);
        
        if (wasActive && !isActive) {
          activeBuildCount--;
        } else if (!wasActive && isActive) {
          activeBuildCount++;
        }
        
        return {
          builds: newBuilds,
          activeBuildCount,
        };
      }),
      
      removeBuild: (buildId) => set((state) => {
        const build = state.builds.find(b => b.id === buildId);
        const wasActive = build && ['queued', 'preparing', 'running'].includes(build.status);
        
        return {
          builds: state.builds.filter(b => b.id !== buildId),
          totalBuildCount: Math.max(0, state.totalBuildCount - 1),
          activeBuildCount: wasActive 
            ? Math.max(0, state.activeBuildCount - 1)
            : state.activeBuildCount,
          selectedBuildId: state.selectedBuildId === buildId ? null : state.selectedBuildId,
        };
      }),
      
      setSelectedBuildId: (buildId) => set({ selectedBuildId: buildId }),
      
      setPlatforms: (platforms) => set({ platforms }),
      setLocations: (locations) => set({ locations }),
      setSpecs: (specs) => set({ specs }),
      
      setRealtimeEnabled: (enabled) => set({ realtimeEnabled: enabled }),
      updateLastUpdate: () => set({ lastUpdate: new Date() }),
      
      addNotification: (notification) => set((state) => ({
        notifications: [
          {
            ...notification,
            id: Math.random().toString(36).substring(7),
            timestamp: new Date(),
          },
          ...state.notifications,
        ].slice(0, 10), // Keep only last 10 notifications
      })),
      
      removeNotification: (id) => set((state) => ({
        notifications: state.notifications.filter(n => n.id !== id),
      })),
      
      clearNotifications: () => set({ notifications: [] }),
      
      // Computed getters
      getActiveBuild: () => {
        const state = get();
        return state.selectedBuildId 
          ? state.builds.find(b => b.id === state.selectedBuildId) || null
          : null;
      },
      
      getBuildById: (id) => {
        const state = get();
        return state.builds.find(b => b.id === id) || null;
      },
      
      getActiveBuilds: () => {
        const state = get();
        return state.builds.filter(b => ['queued', 'preparing', 'running'].includes(b.status));
      },
      
      getCompletedBuilds: () => {
        const state = get();
        return state.builds.filter(b => ['completed', 'failed', 'cancelled', 'timeout'].includes(b.status));
      },
    })),
    {
      name: 'osimager-store',
    }
  )
);

// Selectors for performance optimization
export const useBuilds = () => useAppStore(state => state.builds);
export const useActiveBuildCount = () => useAppStore(state => state.activeBuildCount);
export const useSelectedBuild = () => useAppStore(state => {
  const { selectedBuildId, builds } = state;
  return selectedBuildId ? builds.find(b => b.id === selectedBuildId) : null;
});
export const useConnectionState = () => useAppStore(state => ({
  isConnected: state.isConnected,
  isLoading: state.isLoading,
  error: state.error,
}));
export const useSystemInfo = () => useAppStore(state => state.systemInfo);
export const useHealth = () => useAppStore(state => state.health);
export const usePlatforms = () => useAppStore(state => state.platforms);
export const useLocations = () => useAppStore(state => state.locations);
export const useSpecs = () => useAppStore(state => state.specs);
export const useNotifications = () => useAppStore(state => state.notifications);
