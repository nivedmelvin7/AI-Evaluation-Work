import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext.jsx';

export default function RequireAuth({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <div className="auth-loading">Loading your workspace…</div>;
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />;
  return children;
}
