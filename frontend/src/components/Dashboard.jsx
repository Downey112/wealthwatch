cat > frontend/src/components/Dashboard.jsx << 'EOF'
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, BarElement,
  ArcElement, Title, Tooltip, Legend
} from "chart.js";
import { Bar, Pie } from "react-chartjs-2";

ChartJS.register(
  CategoryScale, LinearScale, BarElement,
  ArcElement, Title, Tooltip, Legend
);

const COLORS = [
  "#6366f1","#f59e0b","#10b981","#ef4444",
  "#3b82f6","#8b5cf6","#ec4899","#14b8a6"
];

export default function Dashboard({ summary }) {
  if (!summary) return <p style={{color:"#94a3b8",padding:"2rem"}}>No data yet. Add your first transaction!</p>;

  const { totalIncome, totalExpenses, netBalance, byCategory, byMonth } = summary;

  const monthlyData = {
    labels: [...(byMonth || [])].reverse().map(m => m.month),
    datasets: [
      {
        label: "Income (RM)",
        data: [...(byMonth || [])].reverse().map(m => m.income),
        backgroundColor: "#10b981"
      },
      {
        label: "Expenses (RM)",
        data: [...(byMonth || [])].reverse().map(m => m.expenses),
        backgroundColor: "#ef4444"
      }
    ]
  };

  const categoryData = {
    labels: (byCategory || []).map(c => c.category),
    datasets: [{
      data: (byCategory || []).map(c => c.total),
      backgroundColor: COLORS
    }]
  };

  return (
    <div className="dashboard">
      <div className="summary-cards">
        <div className="card income">
          <h3>Total Income</h3>
          <p>RM {totalIncome.toFixed(2)}</p>
        </div>
        <div className="card expenses">
          <h3>Total Expenses</h3>
          <p>RM {totalExpenses.toFixed(2)}</p>
        </div>
        <div className={`card balance ${netBalance >= 0 ? "positive" : "negative"}`}>
          <h3>Net Balance</h3>
          <p>RM {netBalance.toFixed(2)}</p>
        </div>
      </div>

      <div className="charts">
        <div className="chart-box">
          <h3>Monthly Overview</h3>
          {byMonth?.length > 0
            ? <Bar data={monthlyData} options={{ responsive: true }} />
            : <p style={{color:"#64748b"}}>No monthly data yet.</p>
          }
        </div>
        <div className="chart-box">
          <h3>Expenses by Category</h3>
          {byCategory?.length > 0
            ? <Pie data={categoryData} options={{ responsive: true }} />
            : <p style={{color:"#64748b"}}>No category data yet.</p>
          }
        </div>
      </div>
    </div>
  );
}
EOF