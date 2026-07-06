import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  if (!user) return null;

  return (
    <nav className="navbar">
      <div className="navbar-brand">💰 AI Finance Tracker</div>
      <div className="navbar-links">
        <Link to="/dashboard">Dashboard</Link>
        <Link to="/transactions">Transactions</Link>
        <Link to="/upload">Upload CSV</Link>
        <Link to="/insights">AI Insights</Link>
      </div>
      <div className="navbar-user">
        <span>Hi, {user.name}</span>
        <button onClick={handleLogout}>Logout</button>
      </div>
    </nav>
  );
}
