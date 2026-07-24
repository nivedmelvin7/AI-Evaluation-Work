import React from 'react';

export default function EmptyState({ icon = '📄', title, message, action }) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon" aria-hidden="true">{icon}</div>
      <div className="empty-state-title">{title}</div>
      {message && <div className="empty-state-sub">{message}</div>}
      {action}
    </div>
  );
}
