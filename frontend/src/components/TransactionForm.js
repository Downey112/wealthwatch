import React, { useState } from 'react';
import axios from 'axios';

function TransactionForm({ onSuccess }) {
  const [formData, setFormData] = useState({
    amount: '',
    type: 'expense',
    category: 'Food',
    description: '',
    transaction_date: new Date().toISOString().split('T')[0]
  });
  const [submitting, setSubmitting] = useState(false);

  const categories = {
    income: ['Salary', 'Freelance', 'Investment', 'Gift', 'Other'],
    expense: ['Food', 'Transport', 'Housing', 'Utilities', 'Entertainment', 'Healthcare', 'Shopping', 'Education', 'Other']
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await axios.post('https://wealthwatch-api-luqman-g5b6bgb9hzhfdwc5.southeastasia-01.azurewebsites.net/api/addtransaction', {
        ...formData,
        amount: parseFloat(formData.amount)
      });
      setFormData({
        amount: '',
        type: 'expense',
        category: 'Food',
        description: '',
        transaction_date: new Date().toISOString().split('T')[0]
      });
      onSuccess();
    } catch (error) {
      console.error('Error adding transaction:', error);
      alert('Failed to add transaction');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card">
      <h2>Add Transaction</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Type</label>
          <select value={formData.type} onChange={(e) => {
            setFormData({
              ...formData,
              type: e.target.value,
              category: e.target.value === 'income' ? 'Salary' : 'Food'
            });
          }}>
            <option value="expense">Expense 💸</option>
            <option value="income">Income 💰</option>
          </select>
        </div>

        <div className="form-group">
          <label>Amount (RM)</label>
          <input
            type="number"
            step="0.01"
            required
            value={formData.amount}
            onChange={(e) => setFormData({...formData, amount: e.target.value})}
          />
        </div>

        <div className="form-group">
          <label>Category</label>
          <select value={formData.category} onChange={(e) => setFormData({...formData, category: e.target.value})}>
            {categories[formData.type].map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Description (optional)</label>
          <input
            type="text"
            value={formData.description}
            onChange={(e) => setFormData({...formData, description: e.target.value})}
          />
        </div>

        <div className="form-group">
          <label>Date</label>
          <input
            type="date"
            required
            value={formData.transaction_date}
            onChange={(e) => setFormData({...formData, transaction_date: e.target.value})}
          />
        </div>

        <button type="submit" disabled={submitting}>
          {submitting ? 'Adding...' : 'Add Transaction'}
        </button>
      </form>
    </div>
  );
}

export default TransactionForm;