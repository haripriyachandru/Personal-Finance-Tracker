import React, { useEffect, useState } from "react";
import api from "../api";

export default function Insights() {
  const [insights, setInsights] = useState(null);
  const [source, setSource] = useState("");
  const [anomalies, setAnomalies] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [insightsRes, anomaliesRes] = await Promise.all([
          api.get("/assistant/insights"),
          api.get("/ml/anomalies"),
        ]);
        setInsights(insightsRes.data.insights);
        setSource(insightsRes.data.source);
        setAnomalies(anomaliesRes.data);
      } catch (err) {
        setError("Failed to load insights.");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <p>Analyzing your financial data...</p>;
  if (error) return <div className="error-box">{error}</div>;

  return (
    <div>
      <h2>AI Assistant Insights</h2>
      <p className="muted">
        Source: {source === "ai" ? "Claude AI" : "Built-in rule-based engine"}
      </p>

      <div className="insights-list">
        {insights.map((text, i) => (
          <div key={i} className="insight-card">💡 {text}</div>
        ))}
      </div>

      <h3 style={{ marginTop: "2rem" }}>Unusual / Suspicious Transactions</h3>
      {anomalies.length === 0 ? (
        <p>No unusual transactions detected.</p>
      ) : (
        <div className="insights-list">
          {anomalies.map((a) => (
            <div key={a.transaction.id} className="insight-card anomaly">
              ⚠️ {a.reason}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
