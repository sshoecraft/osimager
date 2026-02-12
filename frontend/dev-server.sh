#!/bin/bash

# OSImager Frontend Development Server
# Starts the React development server with proper configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[OSImager Frontend]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OSImager Frontend]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[OSImager Frontend]${NC} $1"
}

print_error() {
    echo -e "${RED}[OSImager Frontend]${NC} $1"
}

# Check if we're in the frontend directory
if [ ! -f "package.json" ]; then
    print_error "package.json not found. Please run this script from the frontend directory."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 16+ to continue."
    exit 1
fi

# Setup node_modules symlink if needed
if [ ! -d "node_modules" ] || [ ! -L "node_modules" ]; then
    print_status "Setting up node_modules symlink..."
    ./setup.sh
fi

# Check Node.js version
NODE_VERSION=$(node --version | sed 's/v//')
REQUIRED_VERSION="16.0.0"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$NODE_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Node.js version $NODE_VERSION is too old. Please install Node.js 16 or newer."
    exit 1
fi

print_status "Using Node.js version $NODE_VERSION"

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    print_status "Installing dependencies..."
    source ~/.zshrc && pnpm install
    print_success "Dependencies installed successfully"
else
    print_status "Dependencies already installed"
fi

# Check if backend is running
print_status "Checking backend connection..."
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    print_success "Backend is running on port 8000"
else
    print_warning "Backend doesn't seem to be running on port 8000"
    print_warning "Make sure to start the FastAPI backend first:"
    print_warning "  cd ../api && python run_server.py"
fi

# Create .env.local if it doesn't exist
if [ ! -f ".env.local" ]; then
    print_status "Creating .env.local configuration..."
    cat > .env.local << EOF
# OSImager Frontend Environment Configuration
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/api/builds/ws
EOF
    print_success "Created .env.local"
fi

# Start the development server
print_status "Starting React development server..."
print_status "Frontend will be available at: http://localhost:3000"
print_status "Backend API proxy: http://localhost:3000/api -> http://localhost:8000/api"
print_status ""
print_status "Press Ctrl+C to stop the server"

# Run the development server
source ~/.zshrc && pnpm run dev
