import React, { useState } from 'react';
import { supabase } from '../supabase';

function Login() {
  const [mode, setMode] = useState('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);

  const isSignUp = mode === 'signup';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setNotice(null);
    try {
      const credentials = { email: email.trim(), password };
      const { data, error: authError } = isSignUp
        ? await supabase.auth.signUp(credentials)
        : await supabase.auth.signInWithPassword(credentials);
      if (authError) {
        setError(authError.message);
      } else if (!data.session) {
        // The project requires email confirmation before the first sign-in.
        setNotice('Check your email to confirm your account, then sign in.');
        setMode('signin');
      }
      // On success App picks the session up through onAuthStateChange.
    } catch (err) {
      setError('Could not reach the sign-in service. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const switchMode = () => {
    setMode(isSignUp ? 'signin' : 'signup');
    setError(null);
    setNotice(null);
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>💰 WealthWatch</h1>
        <p>Track your finances, achieve your goals</p>

        {supabase ? (
          <form className="login-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="login-email">Email</label>
              <input
                id="login-email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label htmlFor="login-password">Password</label>
              <input
                id="login-password"
                type="password"
                autoComplete={isSignUp ? 'new-password' : 'current-password'}
                minLength={6}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            {error && <p className="form-error" role="alert">{error}</p>}
            {notice && <p className="form-notice" role="status">{notice}</p>}

            <button type="submit" disabled={submitting}>
              {submitting ? 'Please wait...' : isSignUp ? 'Create account' : 'Sign in'}
            </button>

            <p className="login-switch">
              {isSignUp ? 'Already have an account?' : 'New to WealthWatch?'}{' '}
              <button type="button" className="link-btn" onClick={switchMode}>
                {isSignUp ? 'Sign in' : 'Create an account'}
              </button>
            </p>
          </form>
        ) : (
          <p className="form-error" role="alert">
            Sign-in is not configured for this deployment.
          </p>
        )}
      </div>
    </div>
  );
}

export default Login;
