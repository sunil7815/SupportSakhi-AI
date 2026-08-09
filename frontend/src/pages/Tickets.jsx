import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getMyTickets } from "../services/ticketService";

function Tickets() {
  const [tickets, setTickets] = useState([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadTickets = async () => {
    setLoading(true);
    setError("");

    try {
      const data = await getMyTickets({
        search: search || undefined,
        status: status || undefined,
        page: 1,
        page_size: 20,
      });

      setTickets(data.tickets || []);
    } catch (error) {
      setError(
        error.response?.data?.detail ||
          "Unable to load tickets."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTickets();
  }, []);

  const handleFilter = (event) => {
    event.preventDefault();
    loadTickets();
  };

  return (
    <>
      <section className="page-heading">
        <div>
          <span className="eyebrow">SUPPORT</span>
          <h1>My Tickets</h1>
          <p>
            Search, monitor and manage your support requests.
          </p>
        </div>

        <Link
          to="/tickets/create"
          className="action-button"
        >
          + New Ticket
        </Link>
      </section>

      <form
        className="filter-bar"
        onSubmit={handleFilter}
      >
        <input
          type="search"
          placeholder="Search tickets..."
          value={search}
          onChange={(event) =>
            setSearch(event.target.value)
          }
        />

        <select
          value={status}
          onChange={(event) =>
            setStatus(event.target.value)
          }
        >
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </select>

        <button type="submit">
          Apply Filters
        </button>
      </form>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {loading ? (
        <div className="page-loader">
          Loading tickets...
        </div>
      ) : tickets.length === 0 ? (
        <div className="empty-state">
          <h2>No tickets found</h2>
          <p>Create your first support request.</p>

          <Link to="/tickets/create">
            Create Ticket
          </Link>
        </div>
      ) : (
        <div className="ticket-table-card">
          <div className="ticket-table">

            <div className="ticket-row ticket-header">
              <span>ID</span>
              <span>Issue</span>
              <span>Category</span>
              <span>Priority</span>
              <span>Status</span>
            </div>

            {tickets.map((ticket) => (
              <div
                className="ticket-row"
                key={ticket.id}
              >
                <span>#{ticket.id}</span>

                <Link
                  to={"/tickets/" + ticket.id}
                  className="ticket-title ticket-link"
                >
                  {ticket.title}
                </Link>

                <span>
                  {ticket.category || "Unclassified"}
                </span>

                <span
                  className={
                    "badge badge-" + ticket.priority
                  }
                >
                  {ticket.priority}
                </span>

                <span
                  className={
                    "badge badge-" + ticket.status
                  }
                >
                  {ticket.status.replace("_", " ")}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}

export default Tickets;
