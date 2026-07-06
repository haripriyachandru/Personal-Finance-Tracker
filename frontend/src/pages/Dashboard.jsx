import React, { useEffect, useState } from "react";
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  BarChart, Bar,
} from "recharts";
import api from "../api";

const COLORS = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#06b6d4", "#a855f7", "#ec4899", "#84cc16"];

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [cluster, setCluster] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [summaryRes, predRes, clusterRes] = await Promise.all([
          api.get("/dashboard/summary"),
          api.get("/ml/predict"),
          api.get("/ml/cluster"),
        ]);
        setSummary(summaryRes.data);
        setPrediction(predRes.data);
        setCluster(clusterRes.data);
      } catch (err) {
        setError("Failed to load dashboard data.");
      }
    };
    fetchAll();
  }, []);

  if (error) return <div className="error-box">{error}</div>;
  if (!summary) return <p>Loading dashboard...</p>;

  return (
    <div>
      <h2>Dashboard</h2>

      <div className="stat-grid">
        <div className="stat-card income">
          <h4>Total Income</h4>
          <p>₹{summary.total_income.toFixed(2)}</p>
        </div>
        <div className="stat-card expense">
          <h4>Total Expense</h4>
          <p>₹{summary.total_expense.toFixed(2)}</p>
        </div>
        <div className="stat-card savings">
          <h4>Net Savings</h4>
          <p>₹{summary.net_savings.toFixed(2)}</p>
        </div>
        {cluster && (
          <div className="stat-card behavior">
            <h4>Spending Behavior</h4>
            <p>{cluster.label}</p>
          </div>
        )}
      </div>

      {prediction && (
        <div className="info-banner">
          📈 Predicted next month's expense: <strong>₹{prediction.next_month_predicted_expense.toFixed(2)}</strong>{" "}
          (trend: {prediction.trend}) — {prediction.confidence_note}
        </div>
      )}

      <div className="chart-grid">
        <div className="chart-box">
          <h3>Spending by Category</h3>
          {summary.category_breakdown.length === 0 ? (
            <p>No expense data yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={summary.category_breakdown}
                  dataKey="total"
                  nameKey="category"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={(entry) => entry.category}
                >
                  {summary.category_breakdown.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="chart-box">
          <h3>Income vs Expense Trend</h3>
          {summary.monthly_trend.length === 0 ? (
            <p>No transaction history yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={summary.monthly_trend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="income" stroke="#22c55e" strokeWidth={2} />
                <Line type="monotone" dataKey="expense" stroke="#ef4444" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="chart-box full-width">
          <h3>Monthly Summary</h3>
          {summary.monthly_trend.length === 0 ? (
            <p>No transaction history yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={summary.monthly_trend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="income" fill="#22c55e" />
                <Bar dataKey="expense" fill="#ef4444" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}
