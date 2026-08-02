import React, { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { googleSignInUrl } from '../api.js';
import { useAuth } from '../context/AuthContext.jsx';

export default function Login() {
  const { user, loading, login, signup } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mode, setMode] = useState('signin');
  const [form, setForm] = useState({ username: '', displayName: '', email: '', password: '' });
  const [submitting, setSubmitting] = useState(false);
  const googleError = new URLSearchParams(location.search).get('error');
  const [error, setError] = useState(
    googleError === 'google_sign_in_unavailable'
      ? 'Google sign-in has not been configured yet.'
      : googleError === 'google_sign_in_failed'
        ? 'Google sign-in could not be completed. Please try again.'
        : '',
  );

  if (!loading && user) return <Navigate to={location.state?.from?.pathname || '/'} replace />;

  function update(field) {
    return (event) => setForm((current) => ({ ...current, [field]: event.target.value }));
  }

  async function submit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      if (mode === 'signup') {
        await signup({
          username: form.username,
          display_name: form.displayName || undefined,
          email: form.email,
          password: form.password,
        });
      } else {
        await login({ email: form.email, password: form.password });
      }
      navigate(location.state?.from?.pathname || '/', { replace: true });
    } catch (err) {
      setError(err.message || 'We could not sign you in.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="auth-title">
        <div className="auth-brand">⚙ <span>Assessment Workspace</span></div>
        <h1 id="auth-title">{mode === 'signup' ? 'Create your account' : 'Welcome back'}</h1>
        <p className="auth-subtitle">{mode === 'signup' ? 'Keep your evaluations private and available across visits.' : 'Sign in to your private evaluation workspace.'}</p>

        {error && <div className="auth-error" role="alert">{error}</div>}

        <button type="button" className="auth-google-btn" onClick={() => { window.location.assign(googleSignInUrl()); }}>
          <span aria-hidden="true">G</span> Continue with Google
        </button>
        <div className="auth-divider"><span>or</span></div>

        <form className="auth-form" onSubmit={submit}>
          {mode === 'signup' && <>
            <label>Username<input autoComplete="username" value={form.username} onChange={update('username')} minLength="3" maxLength="50" required /></label>
            <label>Display name <small>(optional)</small><input autoComplete="name" value={form.displayName} onChange={update('displayName')} maxLength="255" /></label>
          </>}
          <label>Email<input type="email" autoComplete="email" value={form.email} onChange={update('email')} required /></label>
          <label>Password<input type="password" autoComplete={mode === 'signup' ? 'new-password' : 'current-password'} value={form.password} onChange={update('password')} minLength={mode === 'signup' ? 12 : undefined} required /></label>
          {mode === 'signup' && <p className="auth-hint">Use at least 12 characters. We store only a salted password hash.</p>}
          <button className="btn btn-primary auth-submit" type="submit" disabled={submitting}>{submitting ? 'Please wait…' : mode === 'signup' ? 'Create account' : 'Sign in'}</button>
        </form>
        <p className="auth-switch">{mode === 'signup' ? 'Already have an account?' : 'New here?'} <button type="button" onClick={() => { setMode(mode === 'signup' ? 'signin' : 'signup'); setError(''); }}>{mode === 'signup' ? 'Sign in' : 'Create an account'}</button></p>
      </section>
    </main>
  );
}
