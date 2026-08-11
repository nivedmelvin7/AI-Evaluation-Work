import React from 'react';
import HealthBadge from '../HealthBadge.jsx';
import { useTheme } from '../../theme/ThemeContext.jsx';
import { useTopBar } from '../../context/TopBarContext.jsx';
import { useAuth } from '../../context/AuthContext.jsx';

export default function TopBar({ onOpenDrawer }) {
  const { title, action } = useTopBar();
  const { theme, setTheme, themes } = useTheme();
  const { user, logout } = useAuth();

  return (
    <header className="app-topbar">
      <div className="app-topbar-left">
        <button
          type="button"
          className="mobile-menu-btn"
          onClick={onOpenDrawer}
          aria-label="Open navigation menu"
        >
          ☰
        </button>
        <span className="app-topbar-title">{title}</span>
      </div>
      <div className="app-topbar-right">
        <HealthBadge />
        <label className="theme-selector">
          <span className="sr-only">Choose colour theme</span>
          <select value={theme} onChange={(event) => setTheme(event.target.value)} aria-label="Choose colour theme">
            {themes.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
          </select>
        </label>
        <span className="user-chip" title={user?.email}>{user?.display_name || user?.username}</span>
        <button type="button" className="btn btn-secondary btn-sm" onClick={logout}>Sign out</button>
        {action}
      </div>
    </header>
  );
}
