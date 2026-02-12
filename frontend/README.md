# OSImager Frontend

Modern React/TypeScript frontend for the OSImager OS image building and automation system.

## 🚀 Features

- **Real-time Monitoring**: Live build status updates via WebSocket
- **Modern UI**: Responsive design with Tailwind CSS
- **Type Safety**: Full TypeScript implementation with API type definitions
- **Performance**: Optimized with React Query for efficient data fetching and caching
- **Real-time Updates**: WebSocket integration for live build monitoring
- **Progressive Enhancement**: Works without JavaScript for basic functionality

## 🛠️ Technology Stack

- **React 18** - Modern React with hooks and concurrent features
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **TanStack Query** - Server state management and caching
- **Zustand** - Lightweight state management
- **Axios** - HTTP client with interceptors
- **React Hot Toast** - Toast notifications
- **Lucide React** - Beautiful icons
- **Date-fns** - Date formatting utilities

## 📦 Installation

### Automatic Setup (Recommended)

```bash
cd frontend
./setup.sh              # Sets up clean node_modules symlink
source ~/.zshrc && pnpm run dev
```

### Manual Setup

1. **Install dependencies**:
   ```bash
   cd frontend
   source ~/.zshrc && pnpm install
   ```

2. **Start development server**:
   ```bash
   source ~/.zshrc && pnpm run dev
   ```

3. **Build for production**:
   ```bash
   source ~/.zshrc && pnpm run build
   ```

### Clean Directory Architecture

This frontend uses a **clean source directory** approach:
- `node_modules/` is a symlink to `~/.local/share/node_modules/osimager-frontend`
- Actual dependencies (187MB) are stored outside the source tree
- Source directory remains lightweight (~3MB) and clean
- Uses **pnpm** with global cache for efficient package management

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── layout/         # Layout components (Header, Layout)
│   │   ├── pages/          # Page components (Dashboard, Builds, etc.)
│   │   └── ui/             # Reusable UI components
│   ├── hooks/              # Custom React hooks
│   │   ├── api-hooks.ts    # React Query hooks for API
│   │   └── websocket-hook.ts # WebSocket connection hook
│   ├── lib/                # Utility libraries
│   │   ├── api-client.ts   # HTTP API client
│   │   ├── websocket-client.ts # WebSocket client
│   │   └── utils.ts        # Helper functions
│   ├── stores/             # Zustand stores
│   │   └── app-store.ts    # Main application store
│   ├── types/              # TypeScript type definitions
│   │   └── api.ts          # API type definitions
│   ├── app.tsx             # Main app component with routing
│   ├── main.tsx            # Application entry point
│   └── index.css           # Global styles and Tailwind imports
├── public/                 # Static assets
├── package.json            # Dependencies and scripts
├── vite.config.ts          # Vite configuration
├── tailwind.config.js      # Tailwind CSS configuration
├── tsconfig.json           # TypeScript configuration
└── README.md               # This file
```

## 🔌 API Integration

The frontend integrates with the OSImager FastAPI backend:

- **REST API**: All CRUD operations for builds, specs, platforms, and locations
- **WebSocket**: Real-time updates for build status, progress, and logs
- **Type Safety**: Generated TypeScript types match backend Pydantic models

### API Endpoints

- `GET /api/health` - System health check
- `GET /api/info` - System information
- `GET /api/builds/` - List builds with filtering
- `POST /api/builds/` - Create new build
- `GET /api/builds/{id}` - Get build details
- `POST /api/builds/{id}/cancel` - Cancel build
- `WebSocket /api/builds/ws` - Real-time updates

## 🎨 UI Components

### Layout Components

- **Header**: Navigation, status indicators, and notifications
- **Layout**: Main app layout with header and content area

### Page Components

- **Dashboard**: System overview and active builds summary
- **Builds**: Complete builds list with filtering and management
- **Build Details**: Individual build monitoring (TODO)
- **New Build**: Build creation form (TODO)

### UI Components

- **LoadingSpinner**: Various loading states
- **StatusBadge**: Build and system status indicators
- **ProgressBar**: Build progress visualization
- **ConnectionStatus**: Real-time connection indicator

## ⚡ Real-time Features

### WebSocket Connection

- Automatic connection on app start
- Reconnection with exponential backoff
- Heartbeat/ping-pong for connection health
- Graceful error handling

### Real-time Updates

- Build status changes
- Build progress updates
- Live log streaming
- System status updates
- Toast notifications for important events

## 🎯 State Management

### Zustand Store

- Global application state
- Build data and status
- WebSocket connection state
- Notifications and alerts
- System information

### React Query

- Server state caching
- Background refetching
- Optimistic updates
- Error handling
- Loading states

## 🚀 Development

### Development Server

```bash
source ~/.zshrc && pnpm run dev
```

The dev server runs on `http://localhost:3000` with:
- Hot module replacement
- Proxy to backend API (`/api` → `http://localhost:8000`)
- TypeScript checking
- ESLint integration

### Building

```bash
source ~/.zshrc && pnpm run build
```

Builds the app for production:
- TypeScript compilation
- Vite optimization
- CSS purging and minification
- Asset optimization

### Type Checking

```bash
source ~/.zshrc && pnpm run type-check
```

### Linting

```bash
source ~/.zshrc && pnpm run lint
```

## 📱 Responsive Design

The UI is fully responsive with breakpoints:
- **Mobile**: < 768px - Stacked layout, mobile menu
- **Tablet**: 768px - 1024px - Compact layout
- **Desktop**: > 1024px - Full layout with sidebar

## 🔧 Configuration

### Environment Variables

Create `.env.local` for local development:

```env
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/api/builds/ws
```

### Proxy Configuration

Vite proxy in `vite.config.ts` routes `/api` requests to the backend server.

## 🐛 Error Handling

- Global error boundaries for React errors
- API error handling with user-friendly messages
- WebSocket connection error recovery
- Toast notifications for user feedback
- Loading states and fallbacks

## 🔮 Future Enhancements

- **Build Details Page**: Detailed build monitoring with logs
- **New Build Form**: Interactive build creation wizard
- **Specs Management**: Full CRUD for build specifications
- **Platform/Location Management**: Configuration management UI
- **Settings Page**: User preferences and system configuration
- **Dark Mode**: Theme switching capability
- **Export/Import**: Configuration backup and restore
- **Advanced Filtering**: More sophisticated search and filters
- **Build Templates**: Reusable build configurations
- **Notification Center**: Persistent notification history

## 📄 License

This project is part of the OSImager system. See the main project README for license information.
