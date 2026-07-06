import React, { useState } from "react";
import api from "../api";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setError("");
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await api.post("/upload/csv", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Upload failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Upload Bank Statement (CSV)</h2>
      <p>
        Your CSV should have columns: <code>date, description, category, amount, type</code>.
        The <code>type</code> column should be "income" or "expense" — if omitted, it's
        inferred from the sign of the amount.
      </p>

      <form onSubmit={handleSubmit} className="upload-form">
        <input
          type="file"
          accept=".csv"
          onChange={(e) => setFile(e.target.files[0])}
        />
        <button type="submit" disabled={!file || loading}>
          {loading ? "Uploading..." : "Upload"}
        </button>
      </form>

      {error && <div className="error-box">{error}</div>}
      {result && (
        <div className="info-banner">
          ✅ {result.message}
        </div>
      )}

      <div className="sample-csv">
        <h4>Example CSV format</h4>
        <pre>{`date,description,category,amount,type
2026-01-05,Salary,Salary,50000,income
2026-01-07,Groceries,Groceries,1200,expense
2026-01-10,Netflix,Entertainment,499,expense`}</pre>
      </div>
    </div>
  );
}
