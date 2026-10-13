import React, { useState, useEffect } from 'react';
import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { getSummary } from '../api';
import PeriodSelect from './PeriodSelect';

ChartJS.register(ArcElement, Tooltip, Legend);

const EMPTY_SUMMARY = {
  total_income: 0,
  total_expense: 0,
  net_savings: 0,
  categories: []
};

const CHART_COLORS = [
  '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
  '#FF9F40', '#8BC34A', '#C9CBCF', '#4D5360', '#28A745'
];

const chartOptions = {
  plugins: {
    legend: { position: 'right' },
    tooltip: { callbacks: { label: (ctx) => `RM ${ctx.raw.toFixed(2)}` } }
  }
};

function Dashboard({ refresh }) {
  const [summary, setSummary] = useState(EMPTY_SUMMARY);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getSummary(year, month)
      .then(data => {
        if (cancelled) return;
        setSummary({
          total_income: data.total_income || 0,
          total_expense: data.total_expense || 0,
          net_savings: data.net_savings || 0,
          categories: Array.isArray(data.categories) ? data.categories : []
        });
      })
      .catch(() => {
        if (cancelled) return;
        setError('Failed to load summary. Please check that the backend is running.');
        setSummary(EMPTY_SUMMARY);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [refresh, month, year]);

  const chartData = summary.categories.length > 0 ? {
    labels: summary.categories.map(c => c.category),
    datasets: [
      {
        data: summary.categories.map(c => c.total),
        backgroundColor: CHART_COLORS,
      },
    ],
  } : null;

  return (
    <div className="dashboard">
      <div className="date-selector">
        <PeriodSelect month={month} year={year} onMonthChange={setMonth} onYearChange={setYear} />
      </div>

      {error && <div className="card error" role="alert">{error}</div>}

      <div className="stats-grid" aria-busy={loading}>
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

      {chartData && (
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
