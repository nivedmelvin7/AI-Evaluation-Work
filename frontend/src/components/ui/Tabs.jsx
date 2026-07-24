import React, { useRef } from 'react';

/**
 * Accessible tab list. `tabs` is [{ id, label, badge? }]. Content is rendered
 * by the caller based on `activeId` — this component only owns the tablist
 * interaction (arrow-key roving focus, click, aria wiring).
 */
export default function Tabs({ tabs, activeId, onChange, idPrefix = 'tab' }) {
  const listRef = useRef(null);

  function handleKeyDown(event) {
    const index = tabs.findIndex((t) => t.id === activeId);
    if (index === -1) return;
    let nextIndex = null;
    if (event.key === 'ArrowRight') nextIndex = (index + 1) % tabs.length;
    else if (event.key === 'ArrowLeft') nextIndex = (index - 1 + tabs.length) % tabs.length;
    else if (event.key === 'Home') nextIndex = 0;
    else if (event.key === 'End') nextIndex = tabs.length - 1;
    if (nextIndex == null) return;
    event.preventDefault();
    const next = tabs[nextIndex];
    onChange(next.id);
    listRef.current?.querySelector(`#${idPrefix}-btn-${next.id}`)?.focus();
  }

  return (
    <div className="tab-list" role="tablist" ref={listRef} onKeyDown={handleKeyDown}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          id={`${idPrefix}-btn-${tab.id}`}
          type="button"
          role="tab"
          className={`tab-btn ${activeId === tab.id ? 'active' : ''}`}
          aria-selected={activeId === tab.id}
          aria-controls={`${idPrefix}-panel-${tab.id}`}
          tabIndex={activeId === tab.id ? 0 : -1}
          onClick={() => onChange(tab.id)}
        >
          {tab.label}
          {tab.badge != null && <span className="badge badge-gray" style={{ marginLeft: '0.4rem', fontSize: '0.68rem' }}>{tab.badge}</span>}
        </button>
      ))}
    </div>
  );
}

export function TabPanel({ id, activeId, idPrefix = 'tab', children }) {
  if (id !== activeId) return null;
  return (
    <div
      id={`${idPrefix}-panel-${id}`}
      role="tabpanel"
      aria-labelledby={`${idPrefix}-btn-${id}`}
      tabIndex={0}
      className="result-tabpanel"
    >
      {children}
    </div>
  );
}
