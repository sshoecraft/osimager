#!/bin/bash
# OSImager Frontend Setup Script
# Creates symlinked node_modules to keep source directory clean

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GLOBAL_NODE_MODULES="$HOME/.local/share/node_modules"
PROJECT_NODE_MODULES="$GLOBAL_NODE_MODULES/osimager-frontend"

echo "🔧 Setting up OSImager Frontend..."

# Ensure global node_modules directory exists
mkdir -p "$GLOBAL_NODE_MODULES"

# Remove existing node_modules if it exists and is not a symlink
if [ -d "$SCRIPT_DIR/node_modules" ] && [ ! -L "$SCRIPT_DIR/node_modules" ]; then
    echo "📦 Moving existing node_modules to global location..."
    mv "$SCRIPT_DIR/node_modules" "$PROJECT_NODE_MODULES"
elif [ ! -d "$PROJECT_NODE_MODULES" ]; then
    echo "📦 Creating global node_modules directory..."
    mkdir -p "$PROJECT_NODE_MODULES"
fi

# Create symlink if it doesn't exist
if [ ! -L "$SCRIPT_DIR/node_modules" ]; then
    echo "🔗 Creating symlink to global node_modules..."
    ln -s "$PROJECT_NODE_MODULES" "$SCRIPT_DIR/node_modules"
fi

# Install dependencies if needed
cd "$SCRIPT_DIR"
if [ ! -f "$PROJECT_NODE_MODULES/.modules.yaml" ]; then
    echo "📥 Installing dependencies..."
    source ~/.zshrc && pnpm install
else
    echo "✅ Dependencies already installed"
fi

echo "🎉 Setup complete!"
echo ""
echo "📂 Node modules location: $PROJECT_NODE_MODULES"
echo "🔗 Symlink: $SCRIPT_DIR/node_modules -> $PROJECT_NODE_MODULES"
echo "💾 Disk usage in source directory: $(du -sh "$SCRIPT_DIR/node_modules" | cut -f1)"
echo "💾 Actual size: $(du -sh "$PROJECT_NODE_MODULES" | cut -f1)"
echo ""
echo "To start development:"
echo "  source ~/.zshrc && pnpm run dev"
