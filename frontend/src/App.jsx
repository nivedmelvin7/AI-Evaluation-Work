import React from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import AppShell from './components/layout/AppShell.jsx';
import ErrorBoundary from './components/ui/ErrorBoundary.jsx';
import Dashboard from './pages/Dashboard.jsx';
import NewEvaluation from './pages/NewEvaluation.jsx';
import RunningEvaluation from './pages/RunningEvaluation.jsx';
import ResultWorkspace from './pages/ResultWorkspace.jsx';

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/evaluate/new" element={<NewEvaluation />} />
            <Route path="/evaluate/:jobId/run" element={<RunningEvaluation />} />
            <Route path="/evaluate/:jobId/result" element={<ResultWorkspace />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
