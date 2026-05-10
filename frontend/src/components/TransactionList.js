import React, { useState, useEffect } from 'react';
import axios from 'axios';

function TransactionList({ refresh }) {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterMonth, setFilterMonth] = useState(new Date().getMonth() + 1);
  const [filterYear, setFilterYear] = useState(new Date().getFullYear());

  useEffect(() => {
    fetchTransactions();
  }, [refresh, filterMonth, filterYear]);

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`/api/GetTransactions?year=${filterYear}&month=${filterMonth}`);
      setTransactions(response.data);
    } catch (error) {
      console.error('Error fetching transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Delete this transaction?')) {
      try {
        await axios.delete(`/api/DeleteTransaction/${id}`);
        fetchTransactions();
      } catch (error) {
        console.error('Error deleting:', error);
        alert('Failed to delete');
      }
    }
  };

  if (loading) return <div className="card">Loading transactions...</div>;

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