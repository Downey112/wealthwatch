import { useState, useEffect } from "react";
import Dashboard from "./components/Dashboard";
import TransactionForm from "./components/TransactionForm";
import TransactionTable from "./components/TransactionTable";
import "./App.css";

const DEMO_USER = "demo_user";

function App() {
  const [transactions, setTransactions] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("dashboard");

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [txRes, sumRes] = await Promise.all([
        fetch(`/api/transactions?user=${DEMO_USER}`),
        fetch(`/api/summary?user=${DEMO_USER}`)
      ]);

      if (!txRes.ok) throw new Error(`Transactions API: ${txRes.status}`);
      if (!sumRes.ok) throw new Error(`Summary API: ${sumRes.status}`);

      const txData = await txRes.json();
      const sumData = await sumRes.json();
      setTransactions(txData);
      setSummary(sumData);
    } catch (err) {
      console.error("API error:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleAdd = async (transaction) => {
    try {
      const res = await fetch("/api/transactions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...transaction, user: DEMO_USER })
      });
      if (!res.ok) throw new Error(`Add failed: ${res.status}`);
      await fetchData();
    } catch (err) {
      alert("Failed to add transaction: " + err.message);
    }
  };

  const handleDelete = async (id) => {
    try {
      const res = await fetch(
        `/api/transactions?id=${id}&user=${DEMO_USER}`,
        { method: "DELETE" }
      );
      if (!res.ok) throw new Error(`Delete failed: ${res.status}`);
      await fetchData();
    } catch (err) {
      alert("Failed to delete: " + err.message);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>💰 WealthWatch</h1>
        <p>Your personal cloud finance tracker</p>
      </header>

      <nav className="app-nav">
        {["dashboard", "transactions", "add"].map(tab => (
          <button
            key={tab}
            className={activeTab === tab ? "active" : ""}
            onClick={() => setActiveTab(tab)}
          >
            {tab === "dashboard" && "📊 Dashboard"}
            {tab === "transactions" && "📋 Transactions"}
            {tab === "add" && "➕ Add New"}
          </button>
        ))}
      </nav>

      <main className="app-main">
        {loading && (
          <div className="loading">Loading your finances...</div>
        )}

        {error && (
          <div className="error-box">
            <strong>API Error:</strong> {error}
            <br />
            <small>Check the browser Console (F12) for details.</small>
            <br />
            <button onClick={fetchData} style={{marginTop:"8px"}}>
              Retry
            </button>
          </div>
        )}

        {!loading && !error && (
          <>
            {activeTab === "dashboard" && (
              <Dashboard summary={summary} />
            )}
            {activeTab === "transactions" && (
              <TransactionTable
                transactions={transactions}
                onDelete={handleDelete}
              />
            )}
            {activeTab === "add" && (
              <TransactionForm
                onAdd={handleAdd}
                onSuccess={() => setActiveTab("transactions")}
              />
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default App;