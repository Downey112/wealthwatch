import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

function TransactionList({ refresh }) {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterMonth, setFilterMonth] = useState(new Date().getMonth() + 1);
  const [filterYear, setFilterYear] = useState(new Date().getFullYear());

  // Use the full Function App URL directly
  const API_BASE = 'https://wealthwatch-api-luqman-g5b6bgb9hzhfdwc5.southeastasia-01.azurewebsites.net/api';

  const fetchTransactions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const url = `${API_BASE}/GetTransactions?year=${filterYear}&month=${filterMonth}`;
      console.log('Fetching transactions from:', url);
      
      const response = await axios.get(url);
      console.log('Transactions response:', response.data);
      
      setTransactions(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Error fetching transactions:', error);
      setError('Failed to load transactions');
      setTransactions([]);
    } finally {
      setLoading(false);
    }
  }, [filterYear, filterMonth, API_BASE]);

  useEffect(() => {
    fetchTransactions();
  }, [refresh, filterMonth, filterYear, fetchTransactions]);

  const handleDelete = async (id) => {
    if (window.confirm('Delete this transaction?')) {
      try {
        await axios.delete(`${API_BASE}/DeleteTransaction/${id}`);
        fetchTransactions();
      } catch (error) {
        console.error('Error deleting:', error);
        alert('Failed to delete');
      }
    }
  };

  if (loading) return <div className="card">Loading transactions...</div>;
  if (error) return <div className="card error">{error}</div>;

  return (
    <div className="card">
      <div className="list-header">
        <h2>Transactions</h2>
        <div className="filter-controls">
          <select value={filterMonth} onChange={(e) => setFilterMonth(parseInt(e.target.value))}>
            {[1,2,3,4,5,6,7,8,9,10,11,12].map(m => (
              <option key={m} value={m}>{new Date(2024, m-1).toLocaleString('default', { month: 'short' })}</option>
            ))}
          </select>
          <select value={filterYear} onChange={(e) => setFilterYear(parseInt(e.target.value))}>
            <option value={2023}>2023</option>
            <option value={2024}>2024</option>
            <option value={2025}>2025</option>
          </select>
        </div>
      </div>

      {transactions.length === 0 ? (
        <p className="empty-state">No transactions for this period</p>
      ) : (
        <div className="transaction-list">
          {transactions.map(tx => (
            <div key={tx.id} className={`transaction-item ${tx.type}`}>
              <div className="tx-info">
                <span className="tx-category">{tx.category}</span>
                <span className="tx-date">{tx.date}</span>
                {tx.description && <span className="tx-desc">📝 {tx.description}</span>}
              </div>
              <div className="tx-amount">
                <span className={tx.type === 'income' ? 'income-amount' : 'expense-amount'}>
                  {tx.type === 'income' ? '+' : '-'} RM {Math.abs(tx.amount).toFixed(2)}
                </span>
                <button onClick={() => handleDelete(tx.id)} className="delete-btn">🗑️</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default TransactionList;