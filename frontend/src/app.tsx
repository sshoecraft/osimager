/**
 * React app entry point with routing and providers.
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@/contexts/theme-context';
import { Layout } from '@/components/layout/layout';
import { Dashboard } from '@/components/pages/dashboard';
import { SpecsPage } from '@/components/pages/specs';
import { BuildsPage } from '@/components/pages/builds';
import { NewBuildPage } from '@/components/pages/new-build';
import { BuildDetailsPage } from '@/components/pages/build-details';
import { PlatformsPage } from '@/components/pages/platforms';
import { LocationsPage } from '@/components/pages/locations';
import { SettingsPage } from '@/components/pages/settings';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30000, // 30 seconds
    },
    mutations: {
      retry: 1,
    },
  },
});

// Simple test pages for other routes
function TestPage({ title }: { title: string }) {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">{title}</h1>
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <p className="text-gray-600">This page is working! 🎉</p>
        <p className="text-sm text-gray-500 mt-2">
          Full functionality will be restored step by step.
        </p>
      </div>
    </div>
  );
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="builds" element={<BuildsPage />} />
              <Route path="builds/:buildId" element={<BuildDetailsPage />} />
              <Route path="builds/new" element={<NewBuildPage />} />
              <Route path="specs" element={<SpecsPage />} />
              <Route path="platforms" element={<PlatformsPage />} />
              <Route path="locations" element={<LocationsPage />} />
              <Route path="settings" element={<SettingsPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
