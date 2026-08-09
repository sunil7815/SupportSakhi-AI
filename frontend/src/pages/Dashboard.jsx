import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getMyDashboard } from "../services/dashboardService";
import { useAuth } from "../context/AuthContext";

function Dashboard() {
  const { user } = useAuth();

  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        const data = await getMyDashboard();
        setStats(data);
      } catch (error) {
        setError(
          error.response?.data?.detail ||
          "Unable to load dashboard."
        );
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, []);

  if (loading) {
    return (
      <div className="page-loader">
        Loading dashboard...
      </div>
    );
  }

  return (
    <>
      <section className="page-heading">
        <div>
          <span className="eyebrow">OVERVIEW</span>

          <h1>Welcome, {user?.name}</h1>

          <p>
            Monitor your support requests and ticket activity
            from one workspace.
          </p>
        </div>

        <Link
          to="/tickets/create"
          className="action-button"
        >
          + Create Ticket
        </Link>
      </section>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {stats && (
        <>
          <section className="stats-grid">
            <div className="stat-card">
              <span>Total Tickets</span>
              <strong>{stats.total_tickets || 0}</strong>
              <small>All support requests</small>
            </div>

            <div className="stat-card">
              <span>Open</span>
              <strong>{stats.status?.open || 0}</strong>
              <small>Waiting for action</small>
            </div>

            <div className="stat-card">
              <span>In Progress</span>
              <strong>
                {stats.status?.in_progress || 0}
              </strong>
              <small>Currently being handled</small>
            </div>

            <div className="stat-card">
              <span>Resolved</span>
              <strong>
                {stats.status?.resolved || 0}
              </strong>
              <small>Successfully resolved</small>
            </div>
          </section>

          <section className="dashboard-panels">
            <div className="panel-card">
              <div className="panel-header">
                <h2>Priority Overview</h2>
                <p>Tickets grouped by severity</p>
              </div>

              <div className="priority-list">
                <div>
                  <span>Low</span>
                  <strong>{stats.priority?.low || 0}</strong>
                </div>

                <div>
                  <span>Medium</span>
                  <strong>{stats.priority?.medium || 0}</strong>
                </div>

                <div>
                  <span>High</span>
                  <strong>{stats.priority?.high || 0}</strong>
                </div>

                <div>
                  <span>Urgent</span>
                  <strong>{stats.priority?.urgent || 0}</strong>
                </div>
              </div>
            </div>

            <div className="panel-card">
              <div className="panel-header">
                <h2>Assignment</h2>
                <p>Current ticket ownership</p>
              </div>

              <div className="priority-list">
                <div>
                  <span>Assigned</span>
                  <strong>
                    {stats.assignment?.assigned || 0}
                  </strong>
                </div>

                <div>
                  <span>Unassigned</span>
                  <strong>
                    {stats.assignment?.unassigned || 0}
                  </strong>
                </div>
              </div>
            </div>

            <div className="panel-card">
              <div className="panel-header">
                <h2>Quick Actions</h2>
                <p>Frequently used support actions</p>
              </div>

              <div className="quick-actions">
                <Link to="/tickets/create">
                  Create support ticket
                </Link>

                <Link to="/tickets">
                  View my tickets
                </Link>
              </div>
            </div>
          </section>
        </>
      )}
    </>
  );
}

export default Dashboard;
