import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import TransactionForm from './components/TransactionForm';
import TransactionList from './components/TransactionList';
import './App.css';

// `npm start` has no Static Web Apps auth endpoint, so local development signs
// in as this user. The backend uses DEV_USER_EMAIL for the same purpose.
const DEV_USER = process.env.NODE_ENV === 'development'
  ? { userDetails: 'dev@localhost' }
  : null;

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    // Azure Static Web Apps built-in auth
    fetch('/.auth/me')
      .then(res => res.json())
      .then(data => setUser(data.clientPrincipal || DEV_USER))
      .catch(() => setUser(DEV_USER))
      .finally(() => setLoading(false));
  }, []);

  const handleDataChanged = () => {
    setRefresh(prev => prev + 1);
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (!user) {
    return (
      <div className="login-container">
        <div className="login-card">
          <h1>💰 WealthWatch</h1>
          <p>Track your finances, achieve your goals</p>
          <a href="/.auth/login/aad" className="login-btn">
            Sign in with Microsoft
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <nav className="navbar">
        <h1>WealthWatch</h1>
        <div className="user-info">
          <span>👋 {user.userDetails}</span>
          <a href="/.auth/logout" className="logout-btn">Logout</a>
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
