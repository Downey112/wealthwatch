import React from 'react';
import './App.css';

function App() {
  // Mock data for our aesthetic chart bars
  const chartData = [
    { height: '40%', type: 'green' },
    { height: '60%', type: 'red' },
    { height: '30%', type: 'green' },
    { height: '80%', type: 'green' },
    { height: '50%', type: 'red' },
    { height: '70%', type: 'green' },
    { height: '40%', type: 'red' },
    { height: '90%', type: 'green' },
    { height: '100%', type: 'green' },
  ];

  return (
    <div className="app-container">
      {/* NAVBAR */}
      <nav className="navbar">
        <div className="logo">
          Wealth<span className="logo-accent">Watch</span>
        </div>
        <div className="nav-links">
          <span className="active">DASHBOARD</span>
          <span>TRANSACTIONS</span>
          <span>ANALYTICS</span>
        </div>
        <button className="launch-btn">LAUNCH APP →</button>
      </nav>

      {/* HERO SECTION */}
      <main className="hero-section">
        
        {/* Left Side: Typography */}
        <div className="hero-text">
          <div className="label">CLOUD-NATIVE FINANCE</div>
          <h1>
            Track every<br />
            <i>ringgit,</i><br />
            own your<br />
            future
          </h1>
          <p>
            A full-stack personal finance dashboard built on Microsoft Azure. 
            Visualize income, expenses and net worth — synced to the cloud in real time.
          </p>
        </div>

        {/* Right Side: The Dashboard Card */}
        <div className="dashboard-widget">
          <div className="widget-header">
            <span className="widget-title">NET OVERVIEW</span>
            <div className="live-badge">
              <span className="dot"></span> LIVE
            </div>
          </div>
          
          <h2 className="balance-amount">RM 2,480.00</h2>
          <div className="balance-trend">↑ +12.4% this month</div>

          {/* Mini CSS Bar Chart */}
          <div className="chart-bars">
            {chartData.map((bar, index) => (
              <div 
                key={index} 
                className={`bar ${bar.type}`} 
                style={{ height: bar.height }}
              ></div>
            ))}
          </div>

          {/* Bottom Stats */}
          <div className="widget-stats">
            <div className="stat-box">
              <div className="stat-label">INCOME</div>
              <div className="stat-value income">RM 5,200</div>
            </div>
            <div className="stat-box">
              <div className="stat-label">EXPENSES</div>
              <div className="stat-value expense">RM 2,720</div>
            </div>
          </div>
        </div>
        
      </main>
    </div>
  );
}

export default App;