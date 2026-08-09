import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  getAdminDashboard,
  getAllTickets,
  getAllUsers,
  assignTicket,
  adminUpdateTicket,
} from "../services/adminService";

function AdminDashboard() {
  const { user } = useAuth();

  const [stats, setStats] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [users, setUsers] = useState([]);

  const [selectedUsers, setSelectedUsers] = useState({});
  const [selectedStatuses, setSelectedStatuses] = useState({});
  const [selectedPriorities, setSelectedPriorities] = useState({});

  const [busyTicketId, setBusyTicketId] = useState(null);
  const [message, setMessage] = useState("");
  const [totalTickets, setTotalTickets] =
    useState(0);

  const [loading, setLoading] =
    useState(true);
  const [error, setError] =
    useState("");

  const loadAdminData = async () => {
    setLoading(true);
    setError("");

    try {
      const [
        dashboardData,
        ticketData,
      ] = await Promise.all([
        getAdminDashboard(),
        getAllTickets({
          page: 1,
          page_size: 10,
        }),
      ]);

      setStats(dashboardData);

      const ticketList =
        Array.isArray(ticketData)
          ? ticketData
          : Array.isArray(
              ticketData?.tickets
            )
          ? ticketData.tickets
          : [];

      setTickets(ticketList);

      setTotalTickets(
        ticketData?.total ??
          dashboardData?.total ??
          dashboardData?.tickets?.total ??
          ticketList.length
      );
    } catch (err) {
      const detail =
        err.response?.data?.detail;

      if (typeof detail === "string") {
        setError(detail);
      } else {
        setError(
          "Unable to load admin dashboard."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user?.role === "admin") {
      loadAdminData();
    } else {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (user?.role !== "admin") return;

    const loadUsers = async () => {
      try {
        const data = await getAllUsers();

        setUsers(
          Array.isArray(data)
            ? data
            : Array.isArray(data?.users)
            ? data.users
            : []
        );
      } catch (err) {
        console.error("Unable to load users:", err);
      }
    };

    loadUsers();
  }, [user]);

  const getManagementError = (err, fallback) => {
    const detail = err.response?.data?.detail;

    if (typeof detail === "string") return detail;

    if (Array.isArray(detail)) {
      return detail
        .map((item) => item?.msg || JSON.stringify(item))
        .join(", ");
    }

    return fallback;
  };

  const handleAssignTicket = async (ticketId) => {
    const userId = selectedUsers[ticketId];

    if (!userId) {
      setError("Please select a user first.");
      setMessage("");
      return;
    }

    setBusyTicketId(ticketId);
    setError("");
    setMessage("");

    try {
      await assignTicket(ticketId, userId);

      setMessage(
        "Ticket #" + ticketId + " assigned successfully."
      );

      await loadAdminData();
    } catch (err) {
      setError(
        getManagementError(
          err,
          "Unable to assign ticket."
        )
      );
    } finally {
      setBusyTicketId(null);
    }
  };

  const handleUpdateTicket = async (ticket) => {
    const status =
      selectedStatuses[ticket.id] ??
      ticket.status;

    const priority =
      selectedPriorities[ticket.id] ??
      ticket.priority;

    setBusyTicketId(ticket.id);
    setError("");
    setMessage("");

    try {
      await adminUpdateTicket(ticket.id, {
        status,
        priority,
      });

      setMessage(
        "Ticket #" + ticket.id + " updated successfully."
      );

      await loadAdminData();
    } catch (err) {
      setError(
        getManagementError(
          err,
          "Unable to update ticket."
        )
      );
    } finally {
      setBusyTicketId(null);
    }
  };

  if (user?.role !== "admin") {
    return (
      <div className="panel-card">
        <h2>Admin Access Required</h2>
        <p className="muted-text">
          This section is available only
          to administrators.
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="page-loader">
        Loading admin dashboard...
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-message">
        {error}
      </div>
    );
  }

  const userStats = stats?.users || {};

  const status =
    stats?.status || {};

  const priority =
    stats?.priority || {};

  const assignment =
    stats?.assignment || {};

  return (
    <>
      <section className="page-heading">
        <div>
          <span className="eyebrow">
            ADMIN CONTROL CENTER
          </span>

          <h1>Admin Dashboard</h1>

          <p>
            Monitor users, tickets,
            priorities and support workload.
          </p>
        </div>

        <Link
          to="/tickets"
          className="secondary-link"
        >
          My Tickets
        </Link>
      </section>

      <section className="admin-stat-grid">
        <div className="stat-card">
          <span>Total Tickets</span>
          <strong>
            {stats?.total ??
              stats?.tickets?.total ??
              totalTickets}
          </strong>
          <small>
            All support requests
          </small>
        </div>

        <div className="stat-card">
          <span>Open</span>
          <strong>
            {status.open ?? 0}
          </strong>
          <small>
            Waiting for resolution
          </small>
        </div>

        <div className="stat-card">
          <span>In Progress</span>
          <strong>
            {status.in_progress ?? 0}
          </strong>
          <small>
            Currently being handled
          </small>
        </div>

        <div className="stat-card">
          <span>Resolved</span>
          <strong>
            {status.resolved ?? 0}
          </strong>
          <small>
            Completed tickets
          </small>
        </div>
      </section>

      <section className="admin-overview-grid">
        <div className="panel-card">
          <div className="section-header">
            <div>
              <h2>User Overview</h2>
              <p>
                Registered platform users.
              </p>
            </div>
          </div>

          <div className="admin-mini-stats">
            <div>
              <span>Total</span>
              <strong>
                {userStats.total ?? 0}
              </strong>
            </div>

            <div>
              <span>Active</span>
              <strong>
                {userStats.active ?? 0}
              </strong>
            </div>

            <div>
              <span>Inactive</span>
              <strong>
                {userStats.inactive ?? 0}
              </strong>
            </div>
          </div>
        </div>

        <div className="panel-card">
          <div className="section-header">
            <div>
              <h2>Assignment</h2>
              <p>
                Current support workload.
              </p>
            </div>
          </div>

          <div className="admin-mini-stats">
            <div>
              <span>Assigned</span>
              <strong>
                {assignment.assigned ?? 0}
              </strong>
            </div>

            <div>
              <span>Unassigned</span>
              <strong>
                {assignment.unassigned ?? 0}
              </strong>
            </div>
          </div>
        </div>
      </section>

      <section className="panel-card">
        <div className="section-header">
          <div>
            <h2>Priority Overview</h2>
            <p>
              Ticket distribution by urgency.
            </p>
          </div>
        </div>

        <div className="admin-priority-grid">
          {[
            "low",
            "medium",
            "high",
            "urgent",
          ].map((level) => (
            <div
              className="priority-summary"
              key={level}
            >
              <span
                className={
                  "badge badge-" + level
                }
              >
                {level}
              </span>

              <strong>
                {priority[level] ?? 0}
              </strong>
            </div>
          ))}
        </div>
      </section>

      <section className="panel-card">
        <div className="section-header">
          <div>
            <h2>Recent Tickets</h2>
            <p>
              Latest tickets across all users.
            </p>
          </div>

          <span className="count-badge">
            {totalTickets}
          </span>
        </div>

        {tickets.length === 0 ? (
          <div className="empty-inline">
            No tickets found.
          </div>
        ) : (
          <div className="table-wrapper">
            <table className="ticket-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Issue</th>
                  <th>Category</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Assigned</th>
                  <th>Manage</th>
                </tr>
              </thead>

              <tbody>
                {tickets.map((ticket) => (
                  <tr key={ticket.id}>
                    <td>
                      #{ticket.id}
                    </td>

                    <td>
                      <Link
                        to={
                          "/tickets/" +
                          ticket.id
                        }
                        className="ticket-link"
                      >
                        {ticket.title}
                      </Link>
                    </td>

                    <td>
                      {ticket.category ||
                        "Unclassified"}
                    </td>

                    <td>
                      <span
                        className={
                          "badge badge-" +
                          ticket.priority
                        }
                      >
                        {ticket.priority}
                      </span>
                    </td>

                    <td>
                      <span
                        className={
                          "badge badge-" +
                          ticket.status
                        }
                      >
                        {ticket.status?.replace(
                          "_",
                          " "
                        )}
                      </span>
                    </td>

                    <td>
                      {ticket.assigned_to_id
                        ? "User #" + ticket.assigned_to_id
                        : "Unassigned"}
                    </td>

                    <td>
                      <div className="management-controls">

                        <select
                          className="admin-control-select"
                          value={selectedUsers[ticket.id] ?? ""}
                          onChange={(event) =>
                            setSelectedUsers((previous) => ({
                              ...previous,
                              [ticket.id]: event.target.value,
                            }))
                          }
                        >
                          <option value="">
                            Select user
                          </option>

                          {users
                            .filter((platformUser) =>
                              platformUser.is_active !== false
                            )
                            .map((platformUser) => (
                              <option
                                key={platformUser.id}
                                value={platformUser.id}
                              >
                                {platformUser.name ||
                                  platformUser.email ||
                                  "User"}
                                {" (#" + platformUser.id + ")"}
                              </option>
                            ))}
                        </select>

                        <button
                          type="button"
                          className="admin-small-button assign-button"
                          disabled={busyTicketId === ticket.id}
                          onClick={() =>
                            handleAssignTicket(ticket.id)
                          }
                        >
                          Assign
                        </button>

                        <select
                          className="admin-control-select"
                          value={
                            selectedStatuses[ticket.id] ??
                            ticket.status
                          }
                          onChange={(event) =>
                            setSelectedStatuses((previous) => ({
                              ...previous,
                              [ticket.id]: event.target.value,
                            }))
                          }
                        >
                          <option value="open">Open</option>
                          <option value="in_progress">
                            In Progress
                          </option>
                          <option value="resolved">
                            Resolved
                          </option>
                        </select>

                        <select
                          className="admin-control-select"
                          value={
                            selectedPriorities[ticket.id] ??
                            ticket.priority
                          }
                          onChange={(event) =>
                            setSelectedPriorities((previous) => ({
                              ...previous,
                              [ticket.id]: event.target.value,
                            }))
                          }
                        >
                          <option value="low">Low</option>
                          <option value="medium">Medium</option>
                          <option value="high">High</option>
                          <option value="urgent">Urgent</option>
                        </select>

                        <button
                          type="button"
                          className="admin-small-button update-button"
                          disabled={busyTicketId === ticket.id}
                          onClick={() =>
                            handleUpdateTicket(ticket)
                          }
                        >
                          {busyTicketId === ticket.id
                            ? "Working..."
                            : "Update"}
                        </button>

                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}

export default AdminDashboard;


