/**
 * Settings page component for application configuration.
 */

import { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  Monitor,
  Bell,
  Shield,
  Download,
  Upload,
  RefreshCw,
  Save,
  AlertCircle
} from 'lucide-react';
import { 
  useSystemInfo, 
  useHealth, 
  useUserConfig, 
  useSystemConfig,
  useUpdateUserConfig,
  useResetUserConfig,
  useExportConfig,
  useImportConfig
} from '@/hooks/api-hooks';
import { useAppStore } from '@/stores/app-store';
import { useTheme } from '@/contexts/theme-context';
import { LoadingButton } from '@/components/ui/loading';
import { ConnectionStatus } from '@/components/ui/status-badge';
import { cn } from '@/lib/utils';

interface SettingsData {
  realtimeEnabled: boolean;
  autoRefresh: boolean;
  refreshInterval: number;
  showToastNotifications: boolean;
  notificationSound: boolean;
  theme: 'light' | 'dark' | 'auto';
  compactMode: boolean;
  showTimestamps: boolean;
  apiTimeout: number;
  maxRetries: number;
  debugMode: boolean;
  verboseLogs: boolean;
}

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'general' | 'notifications' | 'display' | 'advanced'>('general');
  const [hasChanges, setHasChanges] = useState(false);
  const [localSettings, setLocalSettings] = useState<SettingsData | null>(null);

  // API hooks
  const { data: systemInfo } = useSystemInfo();
  const { data: health } = useHealth();
  const { data: userConfig, isLoading: configLoading } = useUserConfig();
  const { data: systemConfig } = useSystemConfig();
  const updateUserConfig = useUpdateUserConfig();
  const resetUserConfig = useResetUserConfig();
  const exportConfig = useExportConfig();
  const importConfig = useImportConfig();
  
  // App state
  const { 
    isConnected, 
    realtimeEnabled, 
    setRealtimeEnabled,
    notifications,
    clearNotifications 
  } = useAppStore();
  
  // Theme state
  const { theme, setTheme } = useTheme();

  // Initialize local settings from API data
  useEffect(() => {
    if (userConfig && !localSettings) {
      const settings: SettingsData = {
        realtimeEnabled: userConfig.realtime_enabled ?? true,
        autoRefresh: userConfig.auto_refresh ?? true,
        refreshInterval: userConfig.refresh_interval ?? 5000,
        showToastNotifications: userConfig.show_toast_notifications ?? true,
        notificationSound: userConfig.notification_sound ?? false,
        theme: userConfig.theme ?? theme,
        compactMode: userConfig.compact_mode ?? false,
        showTimestamps: userConfig.show_timestamps ?? true,
        apiTimeout: userConfig.api_timeout ?? 30000,
        maxRetries: userConfig.max_retries ?? 3,
        debugMode: userConfig.debug_mode ?? false,
        verboseLogs: userConfig.verbose_logs ?? false,
      };
      setLocalSettings(settings);
      // Sync theme context with API data
      if (userConfig.theme && userConfig.theme !== theme) {
        setTheme(userConfig.theme as 'light' | 'dark' | 'auto');
      }
    }
  }, [userConfig, localSettings, theme, setTheme]);

  const handleSettingChange = (key: keyof SettingsData, value: any) => {
    if (!localSettings) return;
    
    setLocalSettings(prev => prev ? { ...prev, [key]: value } : prev);
    setHasChanges(true);

    if (key === 'realtimeEnabled') {
      setRealtimeEnabled(value);
    }
    
    if (key === 'theme') {
      setTheme(value as 'light' | 'dark' | 'auto');
    }
  };

  const handleSaveSettings = async () => {
    if (!localSettings) return;
    
    try {
      const configData = {
        realtime_enabled: localSettings.realtimeEnabled,
        auto_refresh: localSettings.autoRefresh,
        refresh_interval: localSettings.refreshInterval,
        show_toast_notifications: localSettings.showToastNotifications,
        notification_sound: localSettings.notificationSound,
        theme: localSettings.theme,
        compact_mode: localSettings.compactMode,
        show_timestamps: localSettings.showTimestamps,
        api_timeout: localSettings.apiTimeout,
        max_retries: localSettings.maxRetries,
        debug_mode: localSettings.debugMode,
        verbose_logs: localSettings.verboseLogs,
      };
      
      await updateUserConfig.mutateAsync(configData);
      setHasChanges(false);
      setRealtimeEnabled(localSettings.realtimeEnabled);
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  const handleResetSettings = async () => {
    if (window.confirm('Are you sure you want to reset all settings to defaults?')) {
      try {
        const result = await resetUserConfig.mutateAsync();
        if (result.config) {
          const settings: SettingsData = {
            realtimeEnabled: result.config.realtime_enabled,
            autoRefresh: result.config.auto_refresh,
            refreshInterval: result.config.refresh_interval,
            showToastNotifications: result.config.show_toast_notifications,
            notificationSound: result.config.notification_sound,
            theme: result.config.theme,
            compactMode: result.config.compact_mode,
            showTimestamps: result.config.show_timestamps,
            apiTimeout: result.config.api_timeout,
            maxRetries: result.config.max_retries,
            debugMode: result.config.debug_mode,
            verboseLogs: result.config.verbose_logs,
          };
          setLocalSettings(settings);
          setHasChanges(false);
        }
      } catch (error) {
        console.error('Failed to reset settings:', error);
      }
    }
  };

  const handleExportSettings = async () => {
    try {
      await exportConfig.mutateAsync();
    } catch (error) {
      console.error('Failed to export settings:', error);
    }
  };

  const handleImportSettings = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          const importedData = JSON.parse(e.target?.result as string);
          await importConfig.mutateAsync(importedData);
          event.target.value = '';
        } catch (error) {
          alert('Invalid settings file');
        }
      };
      reader.readAsText(file);
    }
  };

  if (configLoading || !localSettings) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
          <p className="text-gray-600">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600 mt-1">
            Manage your OSImager application preferences and configuration
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          {hasChanges && (
            <div className="flex items-center space-x-2 text-amber-600">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm">Unsaved changes</span>
            </div>
          )}
          <LoadingButton
            loading={updateUserConfig.isPending}
            onClick={handleSaveSettings}
            disabled={!hasChanges || updateUserConfig.isPending}
            className="inline-flex items-center px-4 py-2 bg-blue-600 border border-transparent rounded-md font-semibold text-xs text-white uppercase tracking-widest hover:bg-blue-700 focus:outline-none focus:ring focus:ring-blue-200 disabled:opacity-50 transition ease-in-out duration-150"
          >
            <Save className="w-4 h-4 mr-2" />
            Save Changes
          </LoadingButton>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Navigation */}
        <div className="lg:col-span-1">
          <nav className="space-y-1">
            {[
              { id: 'general', label: 'General', icon: SettingsIcon },
              { id: 'notifications', label: 'Notifications', icon: Bell },
              { id: 'display', label: 'Display', icon: Monitor },
              { id: 'advanced', label: 'Advanced', icon: Shield },
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id as any)}
                className={cn(
                  'w-full flex items-center space-x-3 px-3 py-2 text-left rounded-md transition-colors',
                  activeTab === id
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                )}
              >
                <Icon className="w-4 h-4" />
                <span>{label}</span>
              </button>
            ))}
          </nav>

          {/* System Status */}
          <div className="mt-8 bg-white rounded-lg border border-gray-200 p-4">
            <h3 className="text-sm font-medium text-gray-900 mb-3">System Status</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">API</span>
                <span className={`px-2 py-1 rounded-full text-xs ${ 
                  health?.healthy ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                }`}>
                  {health?.healthy ? 'Healthy' : 'Unhealthy'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">WebSocket</span>
                <ConnectionStatus connected={isConnected} />
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Version</span>
                <span className="text-gray-900 font-mono text-xs">1.0.0</span>
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="lg:col-span-3">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            {activeTab === 'general' && (
              <GeneralSettings settings={localSettings} onChange={handleSettingChange} />
            )}
            
            {activeTab === 'notifications' && (
              <NotificationSettings 
                settings={localSettings} 
                onChange={handleSettingChange}
                notifications={notifications}
                onClearNotifications={clearNotifications}
              />
            )}
            
            {activeTab === 'display' && (
              <DisplaySettings settings={localSettings} onChange={handleSettingChange} />
            )}
            
            {activeTab === 'advanced' && (
              <AdvancedSettings
                settings={localSettings}
                onChange={handleSettingChange}
                onReset={handleResetSettings}
                onExport={handleExportSettings}
                onImport={handleImportSettings}
                systemInfo={systemInfo}
                systemConfig={systemConfig}
                isResetting={resetUserConfig.isPending}
                isExporting={exportConfig.isPending}
                isImporting={importConfig.isPending}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Settings tab interfaces and components
interface SettingsTabProps {
  settings: SettingsData;
  onChange: (key: keyof SettingsData, value: any) => void;
}

function GeneralSettings({ settings, onChange }: SettingsTabProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">General Settings</h2>
        <p className="text-gray-600 mb-6">Configure core application behavior and real-time features.</p>
      </div>

      <div className="space-y-6">
        <div>
          <h3 className="text-base font-medium text-gray-900 mb-3">Real-time Updates</h3>
          <div className="space-y-4">
            <label className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-gray-700">Enable real-time monitoring</span>
                <p className="text-xs text-gray-500">Connect to WebSocket for live build updates</p>
              </div>
              <input
                type="checkbox"
                checked={settings.realtimeEnabled}
                onChange={(e) => onChange('realtimeEnabled', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            </label>

            <label className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-gray-700">Auto-refresh data</span>
                <p className="text-xs text-gray-500">Automatically refresh build lists and status</p>
              </div>
              <input
                type="checkbox"
                checked={settings.autoRefresh}
                onChange={(e) => onChange('autoRefresh', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            </label>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Refresh interval</label>
              <select
                className="block w-40 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                value={settings.refreshInterval / 1000}
                onChange={(e) => onChange('refreshInterval', parseInt(e.target.value) * 1000)}
              >
                <option value="2">2 seconds</option>
                <option value="5">5 seconds</option>
                <option value="10">10 seconds</option>
                <option value="30">30 seconds</option>
                <option value="60">1 minute</option>
              </select>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-base font-medium text-gray-900 mb-3">API Configuration</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Request timeout (seconds)</label>
              <input
                type="number"
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                value={settings.apiTimeout / 1000}
                onChange={(e) => onChange('apiTimeout', parseInt(e.target.value) * 1000)}
                min="5"
                max="300"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Max retries</label>
              <input
                type="number"
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                value={settings.maxRetries}
                onChange={(e) => onChange('maxRetries', parseInt(e.target.value))}
                min="0"
                max="10"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

interface NotificationSettingsProps extends SettingsTabProps {
  notifications: any[];
  onClearNotifications: () => void;
}

function NotificationSettings({ settings, onChange, notifications, onClearNotifications }: NotificationSettingsProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Notification Settings</h2>
        <p className="text-gray-600 mb-6">Control how and when you receive notifications.</p>
      </div>

      <div className="space-y-6">
        <div>
          <h3 className="text-base font-medium text-gray-900 mb-3">Preferences</h3>
          <div className="space-y-4">
            <label className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-gray-700">Show toast notifications</span>
                <p className="text-xs text-gray-500">Display pop-up notifications for build events</p>
              </div>
              <input
                type="checkbox"
                checked={settings.showToastNotifications}
                onChange={(e) => onChange('showToastNotifications', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            </label>

            <label className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-gray-700">Notification sounds</span>
                <p className="text-xs text-gray-500">Play sound alerts for important events</p>
              </div>
              <input
                type="checkbox"
                checked={settings.notificationSound}
                onChange={(e) => onChange('notificationSound', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            </label>
          </div>
        </div>

        <div>
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-base font-medium text-gray-900">Recent Notifications</h3>
            {notifications.length > 0 && (
              <button
                onClick={onClearNotifications}
                className="text-sm text-gray-600 hover:text-gray-900"
              >
                Clear all
              </button>
            )}
          </div>
          
          {notifications.length === 0 ? (
            <p className="text-gray-500 text-sm">No recent notifications</p>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {notifications.slice(0, 10).map((notification) => (
                <div key={notification.id} className="p-3 border border-gray-200 rounded-lg">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{notification.title}</p>
                      {notification.message && (
                        <p className="text-xs text-gray-600 mt-1">{notification.message}</p>
                      )}
                    </div>
                    <span className="text-xs text-gray-500">
                      {notification.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function DisplaySettings({ settings, onChange }: SettingsTabProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Display Settings</h2>
        <p className="text-gray-600 mb-6">Customize the appearance and layout of the application.</p>
      </div>

      <div className="space-y-6">
        <div>
          <h3 className="text-base font-medium text-gray-900 mb-3">Theme</h3>
          <div className="grid grid-cols-3 gap-3">
            {[
              { value: 'light', label: 'Light' },
              { value: 'dark', label: 'Dark' },
              { value: 'auto', label: 'Auto' },
            ].map(({ value, label }) => (
              <label key={value} className="flex items-center space-x-2">
                <input
                  type="radio"
                  name="theme"
                  value={value}
                  checked={settings.theme === value}
                  onChange={(e) => onChange('theme', e.target.value)}
                  className="border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">{label}</span>
              </label>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-base font-medium text-gray-900 mb-3">Layout</h3>
          <div className="space-y-4">
            <label className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-gray-700">Compact mode</span>
                <p className="text-xs text-gray-500">Use smaller spacing and components</p>
              </div>
              <input
                type="checkbox"
                checked={settings.compactMode}
                onChange={(e) => onChange('compactMode', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            </label>

            <label className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-gray-700">Show timestamps</span>
                <p className="text-xs text-gray-500">Display detailed timestamp information</p>
              </div>
              <input
                type="checkbox"
                checked={settings.showTimestamps}
                onChange={(e) => onChange('showTimestamps', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}

interface AdvancedSettingsProps extends SettingsTabProps {
  onReset: () => void;
  onExport: () => void;
  onImport: (event: React.ChangeEvent<HTMLInputElement>) => void;
  systemInfo: any;
  systemConfig: any;
  isResetting: boolean;
  isExporting: boolean;
  isImporting: boolean;
}

function AdvancedSettings({ 
  settings, 
  onChange, 
  onReset, 
  onExport, 
  onImport, 
  systemInfo, 
  systemConfig,
  isResetting,
  isExporting
}: AdvancedSettingsProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Advanced Settings</h2>
        <p className="text-gray-600 mb-6">Advanced configuration options and debugging features.</p>
      </div>

      <div className="space-y-6">
        <div>
          <h3 className="text-base font-medium text-gray-900 mb-3">Debugging</h3>
          <div className="space-y-4">
            <label className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-gray-700">Debug mode</span>
                <p className="text-xs text-gray-500">Enable detailed debugging information</p>
              </div>
              <input
                type="checkbox"
                checked={settings.debugMode}
                onChange={(e) => onChange('debugMode', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            </label>

            <label className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-gray-700">Verbose logs</span>
                <p className="text-xs text-gray-500">Log detailed API requests and responses</p>
              </div>
              <input
                type="checkbox"
                checked={settings.verboseLogs}
                onChange={(e) => onChange('verboseLogs', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            </label>
          </div>
        </div>

        <div>
          <h3 className="text-base font-medium text-gray-900 mb-3">Settings Management</h3>
          <div className="space-y-3">
            <div className="flex space-x-3">
              <LoadingButton 
                loading={isExporting}
                onClick={onExport} 
                className="inline-flex items-center px-4 py-2 bg-gray-600 border border-transparent rounded-md font-semibold text-xs text-white uppercase tracking-widest hover:bg-gray-700 focus:outline-none focus:ring focus:ring-gray-200 disabled:opacity-50 transition ease-in-out duration-150"
                disabled={isExporting}
              >
                <Download className="w-4 h-4 mr-2" />
                Export Settings
              </LoadingButton>
              
              <label className="relative inline-flex items-center px-4 py-2 bg-gray-600 border border-transparent rounded-md font-semibold text-xs text-white uppercase tracking-widest hover:bg-gray-700 focus:outline-none focus:ring focus:ring-gray-200 transition ease-in-out duration-150 cursor-pointer overflow-hidden">
                <Upload className="w-4 h-4 mr-2" />
                Import Settings
                <input
                  type="file"
                  accept=".json"
                  onChange={onImport}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
              </label>
            </div>
            
            <LoadingButton 
              loading={isResetting}
              onClick={onReset} 
              className="inline-flex items-center px-4 py-2 bg-red-600 border border-transparent rounded-md font-semibold text-xs text-white uppercase tracking-widest hover:bg-red-700 focus:outline-none focus:ring focus:ring-red-200 disabled:opacity-50 transition ease-in-out duration-150"
              disabled={isResetting}
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Reset to Defaults
            </LoadingButton>
          </div>
        </div>

        <div>
          <h3 className="text-base font-medium text-gray-900 mb-3">System Information</h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Application Info</h4>
              <div className="bg-gray-50 rounded-lg p-4">
                <pre className="text-sm text-gray-900 overflow-x-auto">
                  {JSON.stringify(systemInfo, null, 2)}
                </pre>
              </div>
            </div>
            
            {systemConfig && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">System Configuration</h4>
                <div className="bg-gray-50 rounded-lg p-4">
                  <pre className="text-sm text-gray-900 overflow-x-auto">
                    {JSON.stringify(systemConfig, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
