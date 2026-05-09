cat > frontend/src/components/TransactionForm.jsx << 'EOF'
import { useState } from "react";

const CATEGORIES = [
  "Food & Drinks","Transport","Shopping","Bills & Utilities",
  "Entertainment","Healthcare","Education","Salary","Freelance","Other"
];

export default function TransactionForm({ onAdd, onSuccess }) {
  const [form, setForm] = useState({
    amount: "", type: "expense",
    category: "Food & Drinks", note: "",
    date: new Date().toISOString().split("T")[0]
  });
  const [submitting, setSubmitting] = useState(false);

  const handleChange = e =>
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async () => {
    if (!form.amount || isNaN(form.amount) || Number(form.amount) <= 0) {
      alert("Please enter a valid amount.");
      return;
    }
    setSubmitting(true);
    await onAdd(form);
    setSubmitting(false);
    setForm({
      amount: "", type: "expense",
      category: "Food & Drinks", note: "",
      date: new Date().toISOString().split("T")[0]
    });
    onSuccess();
  };

  return (
    <div className="form-container">
      <h2>Add Transaction</h2>
      <div className="form-group">
        <label>Amount (RM)</label>
        <input type="number" name="amount" min="0.01" step="0.01"
          placeholder="0.00" value={form.amount} onChange={handleChange}/>
      </div>
      <div className="form-group">
        <label>Type</label>
        <select name="type" value={form.type} onChange={handleChange}>
          <option value="expense">Expense</option>
          <option value="income">Income</option>
        </select>
      </div>
      <div className="form-group">
        <label>Category</label>
        <select name="category" value={form.category} onChange={handleChange}>
          {CATEGORIES.map(c => <option key={c}>{c}</option>)}
        </select>
      </div>
      <div className="form-group">
        <label>Date</label>
        <input type="date" name="date" value={form.date} onChange={handleChange}/>
      </div>
      <div className="form-group">
        <label>Note (optional)</label>
        <input type="text" name="note" placeholder="e.g. Lunch at mamak"
          value={form.note} onChange={handleChange}/>
      </div>
      <button className="btn-primary" onClick={handleSubmit} disabled={submitting}>
        {submitting ? "Saving..." : "Add Transaction"}
      </button>
    </div>
  );
}
EOF