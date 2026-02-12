/**
 * Main entry point for the OSImager React application.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './app';
import './index.css';

// Debug logging
console.log('🚀 OSImager React app starting...');
console.log('🔍 Root element:', document.getElementById('root'));

try {
  const root = document.getElementById('root');
  if (!root) {
    throw new Error('Root element not found');
  }
  
  console.log('✅ Creating React root...');
  const reactRoot = ReactDOM.createRoot(root);
  
  console.log('✅ Rendering App component...');
  reactRoot.render(<App />);
  
  console.log('🎉 React app rendered successfully!');
} catch (error) {
  console.error('❌ Failed to start React app:', error);
  // Fallback content
  const root = document.getElementById('root');
  if (root) {
    root.innerHTML = `
      <div style="padding: 20px; font-family: Arial, sans-serif;">
        <h1 style="color: red;">React App Error</h1>
        <p>Failed to start the React application:</p>
        <pre style="background: #f0f0f0; padding: 10px; overflow: auto;">${error}</pre>
        <p>Check the browser console for more details.</p>
      </div>
    `;
  }
}
