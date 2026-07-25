import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar.jsx';
import MobileDrawer from './MobileDrawer.jsx';
import TopBar from './TopBar.jsx';
import { TopBarProvider } from '../../context/TopBarContext.jsx';

const COLLAPSE_KEY = 'engineering-report-sidebar-collapsed';

function initialCollapsed() {
  if (typeof window === 'undefined') return false;
  return window.localStorage.getItem(COLLAPSE_KEY) === '1';
}

export default function AppShell() {
  const [collapsed, setCollapsed] = useState(initialCollapsed);
  const [drawerOpen, setDrawerOpen] = useState(false);

  function toggleCollapse() {
    setCollapsed((current) => {
      const next = !current;
      window.localStorage.setItem(COLLAPSE_KEY, next ? '1' : '0');
      return next;
    });
  }

  return (
    <TopBarProvider>
      <div className="app-shell">
        <Sidebar collapsed={collapsed} onToggleCollapse={toggleCollapse} />
        <MobileDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />
        <div className="app-shell-main">
          <TopBar onOpenDrawer={() => setDrawerOpen(true)} />
          <main className="app-content">
            <Outlet />
          </main>
        </div>
      </div>
    </TopBarProvider>
  );
}
