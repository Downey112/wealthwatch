import React, { useState, useEffect, useCallback } from 'react';
import { getTransactions, deleteTransaction, errorMessage } from '../api';
import PeriodSelect from './PeriodSelect';

function TransactionList({ refresh, onChange }) {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterMonth, setFilterMonth] = useState(new Date().getMonth() + 1);
  const [filterYear, setFilterYear] = useState(new Date().getFullYear());

  const fetchTransactions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getTransactions(filterYear, filterMonth);
      setTransactions(Array.isArray(data) ? data : []);
    } catch (err) {
      setError('Failed to load transactions');
      setTransactions([]);
    } finally {
      setLoading(false);
    }
  }, [filterYear, filterMonth]);

  useEffect(() => {
    fetchTransactions();
  }, [refresh, fetchTransactions]);

  const handleDelete = async (id) => {
    if (window.confirm('Delete this transaction?')) {
      try {
        await deleteTransaction(id);
        // Refreshes this list and the dashboard totals together.
        onChange();
      } catch (err) {
        setError(errorMessage(err, 'Failed to delete transaction'));
      }
    }
  };

  return (
    <div className="card">
      <div className="list-header">
        <h2>Transactions</h2>
        <div className="filter-controls">
          <PeriodSelect
            month={filterMonth}
            year={filterYear}
            onMonthChange={setFilterMonth}
            onYearChange={setFilterYear}
            monthFormat="short"
          />
        </div>
      </div>

      {error && <p className="form-error" role="alert">{error}</p>}

      {loading && transactions.length === 0 ? (
        <p className="empty-state">Loading transactions...</p>
      ) : transactions.length === 0 ? (
        !error && <p className="empty-state">No transactions for this period</p>
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
                <button
                  onClick={() => handleDelete(tx.id)}
                  className="delete-btn"
                  aria-label={`Delete ${tx.category} transaction of RM ${Math.abs(tx.amount).toFixed(2)}`}
                >
                  🗑️
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default TransactionList;
