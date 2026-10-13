import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import Login from './components/Login';
import TransactionForm from './components/TransactionForm';
import TransactionList from './components/TransactionList';
import { supabase } from './supabase';
import './App.css';

// Without Supabase settings `npm start` has nothing to sign in to, so local
// development signs in as this user. The backend uses DEV_USER_EMAIL for the
// same purpose.
const DEV_USER = import.meta.env.MODE === 'development'
  ? { email: 'dev@localhost' }
  : null;

const userOf = (session) => (session ? { email: session.user.email } : null);

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    if (!supabase) {
      setUser(DEV_USER);
      setLoading(false);
      return undefined;
    }

    supabase.auth.getSession()
      .then(({ data }) => setUser(userOf(data.session)))
      .catch(() => setUser(null))
      .finally(() => setLoading(false));

    // Keeps the UI in step with sign-in, sign-out and expiry, in any tab.
    const { data } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(userOf(session));
    });
    return () => data.subscription.unsubscribe();
  }, []);

  const handleDataChanged = () => {
    setRefresh(prev => prev + 1);
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (!user) {
    return <Login />;
  }

  return (
    <div className="app">
      <nav className="navbar">
        <h1>WealthWatch</h1>
        <div className="user-info">
          <span>👋 {user.email}</span>
          {supabase && (
            <button type="button" className="logout-btn" onClick={() => supabase.auth.signOut()}>
              Logout
            </button>
          )}
        </div>
      </nav>
      <div className="container">
        <Dashboard refresh={refresh} />
        <div className="grid-2">
          <TransactionForm onSuccess={handleDataChanged} />
          <TransactionList refresh={refresh} onChange={handleDataChanged} />
        </div>
      </div>
    </div>
  );
}

export default App;
