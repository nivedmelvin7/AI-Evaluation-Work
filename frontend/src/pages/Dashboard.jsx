import React from 'react';
import { Link } from 'react-router-dom';
import EmptyState from '../components/ui/EmptyState.jsx';
import { useTopBarConfig } from '../context/TopBarContext.jsx';

export default function Dashboard() {
  useTopBarConfig({ title: 'Dashboard' });

  return (
    <EmptyState
      icon="⚙"
      title="No evaluation open"
      message="Submit an engineering report to get a scored, evidence-backed assessment across nine criteria. Evaluation history and cohort views arrive in a later release."
      action={
        <Link to="/evaluate/new" className="btn btn-primary btn-lg">
          + New evaluation
        </Link>
      }
    />
  );
}
