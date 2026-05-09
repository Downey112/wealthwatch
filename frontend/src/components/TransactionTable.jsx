cat > frontend/src/components/TransactionTable.jsx << 'EOF'
export default function TransactionTable({ transactions, onDelete }) {
  if (!transactions.length) {
    return (
      <div className="empty-state">
        <p>No transactions yet. Add your first one! 💸</p>
      </div>
    );
  }

  return (
    <div className="table-container">
      <h2>All Transactions ({transactions.length})</h2>
      <table className="transactions-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Type</th>
            <th>Category</th>
            <th>Note</th>
            <th>Amount (RM)</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map(tx => (
            <tr key={tx.id} className={tx.type}>
              <td>{tx.date}</td>
              <td>
                <span className={`badge ${tx.type}`}>
                  {tx.type === "income" ? "💚 Income" : "🔴 Expense"}
                </span>
              </td>
              <td>{tx.category}</td>
              <td>{tx.note || "—"}</td>
              <td className={`amount ${tx.type}`}>
                {tx.type === "income" ? "+" : "-"}RM {tx.amount.toFixed(2)}
              </td>
              <td>
                <button className="btn-delete"
                  onClick={() => {
                    if (window.confirm("Delete this transaction?")) onDelete(tx.id);
                  }}>
                  🗑️
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
EOF