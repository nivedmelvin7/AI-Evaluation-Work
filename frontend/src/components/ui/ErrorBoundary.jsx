import React from 'react';
import FailureScreen from './FailureScreen.jsx';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
    this.handleReset = this.handleReset.bind(this);
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    // eslint-disable-next-line no-console
    console.error('Unhandled UI error:', error, info?.componentStack);
  }

  handleReset() {
    this.setState({ error: null });
    window.location.assign('/');
  }

  render() {
    if (this.state.error) {
      return (
        <div className="error-boundary-screen">
          <FailureScreen
            title="The application hit an unexpected error"
            message={this.state.error?.message || 'Please reload the page. If the problem persists, contact support.'}
            onRetry={this.handleReset}
            retryLabel="Reload application"
          />
        </div>
      );
    }
    return this.props.children;
  }
}
