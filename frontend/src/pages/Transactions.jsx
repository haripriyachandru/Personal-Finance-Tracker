import React, { useEffect, useState } from "react";
import api from "../api";

const CATEGORIES = [
  "Salary", "Food", "Rent", "Groceries", "Transport", "Entertainment",
  "Shopping", "Utilities", "Healthcare", "Education", "Investment", "Other",
];

export default function Transactions() {
  const [transactions, setTransactions] = useState([]);
  const [type, setType] = useState("expense");
  const [category, setCategory] = useState("Food");
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [date, setDate] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const res = await api.get("/transactions/");
      setTransactions(res.data);
    } catch (err) {
      setError("Failed to load transactions.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await api.post("/transactions/", {
        type,
        category,
        amount: parseFloat(amount),
        description: description || null,
        date: date ? new Date(date).toISOString() : null,
      });
      setAmount("");
      setDescription("");
      setDate("");
      fetchTransactions();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to add transaction.");
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("Delete this transaction?")) return;
    try {
      await api.delete(`/transactions/${id}`);
      fetchTransactions();
    } catch (err) {
      setError("Failed to delete transaction.");
    }
  };

  return (
    <div>
      <h2>Transactions</h2>

      <form className="tx-form" onSubmit={handleSubmit}>
        <select value={type} onChange={(e) => setType(e.target.value)}>
          <option value="expense">Expense</option>
          <option value="income">Income</option>
        </select>

        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>

        <input
          type="number"
          step="0.01"
          placeholder="Amount"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          required
        />

        <input
          type="text"
          placeholder="Description (optional)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />

        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
        />

        <button type="submit">Add</button>
      </form>

      {error && <div className="error-box">{error}</div>}

      {loading ? (
        <p>Loading...</p>
      ) : transactions.length === 0 ? (
        <p>No transactions yet. Add one above or upload a CSV.</p>
      ) : (
        <table className="tx-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Type</th>
              <th>Category</th>
              <th>Description</th>
              <th>Amount</th>
              <th>Flag</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((tx) => (
              <tr key={tx.id} className={tx.is_anomaly ? "anomaly-row" : ""}>
                <td>{new Date(tx.date).toLocaleDateString()}</td>
                <td className={tx.type === "income" ? "text-income" : "text-expense"}>{tx.type}</td>
                <td>{tx.category}</td>
                <td>{tx.description || "-"}</td>
                <td>₹{tx.amount.toFixed(2)}</td>
                <td>{tx.is_anomaly ? "⚠️ Unusual" : ""}</td>
                <td>
                  <button className="link-btn" onClick={() => handleDelete(tx.id)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
