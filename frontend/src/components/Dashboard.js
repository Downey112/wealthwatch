import React, { useState, useEffect, useCallback } from 'react';
import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import axios from 'axios';

ChartJS.register(ArcElement, Tooltip, Legend);

function Dashboard({ refresh }) {
  const [summary, setSummary] = useState({
    total_income: 0,
    total_expense: 0,
    net_savings: 0,
    categories: []
  });
  const [loading, setLoading] = useState(true);
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());

  const fetchSummary = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axios.get(`/api/GetSummary?year=${year}&month=${month}`);
      setSummary(response.data);
    } catch (error) {
      console.error('Error fetching summary:', error);
    } finally {
      setLoading(false);
    }
  }, [year, month]);

  useEffect(() => {
    fetchSummary();
  }, [refresh, month, year, fetchSummary]);

  const chartData = {
    labels: summary.categories.map(c => c.category),
    datasets: [
      {
        data: summary.categories.map(c => c.total),
        backgroundColor: [
          '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
          '#FF9F40', '#FF6384', '#C9CBCF', '#4D5360', '#28A745'
        ],
      },
    ],
  };

  const chartOptions = {
    plugins: {
      legend: { position: 'right' },
      tooltip: { callbacks: { label: (ctx) => `RM ${ctx.raw.toFixed(2)}` } }
    }
  };

  if (loading) return <div className="card">Loading dashboard...</div>;

  return (
    <div className="dashboard">
      <div className="date-selector">
        <select value={month} onChange={(e) => setMonth(parseInt(e.target.value))}>
          {[1,2,3,4,5,6,7,8,9,10,11,12].map(m => (
            <option key={m} value={m}>{new Date(2024, m-1).toLocaleString('default', { month: 'long' })}</option>
          ))}
        </select>
        <select value={year} onChange={(e) => setYear(parseInt(e.target.value))}>
          <option value={2023}>2023</option>
          <option value={2024}>2024</option>
          <option value={2025}>2025</option>
        </select>
      </div>

      <div className="stats-grid">
        <div className="stat-card income">
          <h3>Total Income</h3>
          <p>RM {summary.total_income.toFixed(2)}</p>
        </div>
        <div className="stat-card expense">
          <h3>Total Expense</h3>
          <p>RM {summary.total_expense.toFixed(2)}</p>
        </div>
        <div className="stat-card savings">
          <h3>Net Savings</h3>
          <p className={summary.net_savings >= 0 ? 'positive' : 'negative'}>
            RM {summary.net_savings.toFixed(2)}
          </p>
        </div>
      </div>

      {summary.categories.length > 0 && (
        <div className="chart-container">
          <h3>Spending by Category</h3>
          <div className="pie-chart-wrapper">
            <Pie data={chartData} options={chartOptions} />
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;