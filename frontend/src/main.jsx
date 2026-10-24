import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { ToastProvider } from './ui';
import { AuthProvider, SettingsProvider, YearProvider } from './context';
import '@fontsource-variable/inter';
import './styles.css';

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider><SettingsProvider><YearProvider><App /></YearProvider></SettingsProvider></AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
