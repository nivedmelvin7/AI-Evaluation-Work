import React from 'react';
import HealthBadge from '../HealthBadge.jsx';
import { useTheme } from '../../theme/ThemeContext.jsx';
import { useTopBar } from '../../context/TopBarContext.jsx';

export default function TopBar({ onOpenDrawer, onOpenSessions }) {
  const { title, action } = useTopBar();
  const { theme, setTheme, themes } = useTheme();

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
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={onOpenSessions}
          aria-label="Open evaluation history"
          title="Evaluation history"
        >
          🕘 History
        </button>
        <HealthBadge />
        <label className="theme-selector">
          <span className="sr-only">Choose colour theme</span>
          <select value={theme} onChange={(event) => setTheme(event.target.value)} aria-label="Choose colour theme">
            {themes.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
          </select>
        </label>
        {action}
      </div>
    </header>
  );
}
