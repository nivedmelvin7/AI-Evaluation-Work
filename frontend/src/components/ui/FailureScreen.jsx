import React from 'react';

export default function FailureScreen({ title = 'Something went wrong', message, onRetry, retryLabel = 'Try again', onStartOver, startOverLabel = 'Start over' }) {
  return (
    <div className="failure-screen" role="alert">
      <div className="failure-icon" aria-hidden="true">✗</div>
      <div className="failure-title">{title}</div>
      {message && <div className="failure-message">{message}</div>}
      <div className="failure-actions">
        {onRetry && (
          <button type="button" className="btn btn-primary" onClick={onRetry}>{retryLabel}</button>
        )}
        {onStartOver && (
          <button type="button" className="btn btn-secondary" onClick={onStartOver}>{startOverLabel}</button>
        )}
      </div>
    </div>
  );
}
