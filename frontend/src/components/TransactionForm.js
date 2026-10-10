import React, { useState } from 'react';
import { addTransaction, errorMessage } from '../api';
import { localDateISO } from '../utils/dates';

const CATEGORIES = {
  income: ['Salary', 'Freelance', 'Investment', 'Gift', 'Other'],
  expense: ['Food', 'Transport', 'Housing', 'Utilities', 'Entertainment', 'Healthcare', 'Shopping', 'Education', 'Other']
};

const emptyForm = () => ({
  amount: '',
  type: 'expense',
  category: CATEGORIES.expense[0],
  description: '',
  transaction_date: localDateISO()
});

function TransactionForm({ onSuccess }) {
  const [formData, setFormData] = useState(emptyForm);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await addTransaction({
        ...formData,
        amount: parseFloat(formData.amount)
      });
      setFormData(emptyForm());
      onSuccess();
    } catch (err) {
      setError(errorMessage(err, 'Failed to add transaction'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card">
      <h2>Add Transaction</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="tx-type">Type</label>
          <select id="tx-type" value={formData.type} onChange={(e) => {
            setFormData({
              ...formData,
              type: e.target.value,
              category: CATEGORIES[e.target.value][0]
            });
          }}>
            <option value="expense">Expense 💸</option>
            <option value="income">Income 💰</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="tx-amount">Amount (RM)</label>
          <input
            id="tx-amount"
            type="number"
            step="0.01"
            min="0.01"
            max="99999999.99"
            required
            value={formData.amount}
            onChange={(e) => setFormData({...formData, amount: e.target.value})}
          />
        </div>

        <div className="form-group">
          <label htmlFor="tx-category">Category</label>
          <select id="tx-category" value={formData.category} onChange={(e) => setFormData({...formData, category: e.target.value})}>
            {CATEGORIES[formData.type].map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="tx-description">Description (optional)</label>
          <input
            id="tx-description"
            type="text"
            maxLength={255}
            value={formData.description}
            onChange={(e) => setFormData({...formData, description: e.target.value})}
          />
        </div>

        <div className="form-group">
          <label htmlFor="tx-date">Date</label>
          <input
            id="tx-date"
            type="date"
            required
            value={formData.transaction_date}
            onChange={(e) => setFormData({...formData, transaction_date: e.target.value})}
          />
        </div>

        {error && <p className="form-error" role="alert">{error}</p>}

        <button type="submit" disabled={submitting}>
          {submitting ? 'Adding...' : 'Add Transaction'}
        </button>
      </form>
    </div>
  );
}

export default TransactionForm;
