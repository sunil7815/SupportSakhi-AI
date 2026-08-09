import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createTicket } from "../services/ticketService";

function CreateTicket() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    title: "",
    description: "",
    priority: "medium",
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (event) => {
    setForm({
      ...form,
      [event.target.name]: event.target.value,
    });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      await createTicket(form);
      navigate("/tickets");
    } catch (error) {
      setError(
        error.response?.data?.detail ||
        "Unable to create ticket."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <section className="page-heading">
        <div>
          <span className="eyebrow">NEW REQUEST</span>
          <h1>Create Support Ticket</h1>
          <p>
            Describe the issue clearly so it can be resolved faster.
          </p>
        </div>
      </section>

      <div className="form-panel">
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <form
          className="ticket-form"
          onSubmit={handleSubmit}
        >
          <div className="form-group">
            <label>Issue Title</label>

            <input
              name="title"
              value={form.title}
              onChange={handleChange}
              placeholder="Example: Laptop not starting"
              required
            />
          </div>

          <div className="form-group">
            <label>Description</label>

            <textarea
              name="description"
              value={form.description}
              onChange={handleChange}
              placeholder="Explain the issue clearly..."
              rows="7"
              required
            />
          </div>

          <div className="form-group">
            <label>Priority</label>

            <select
              name="priority"
              value={form.priority}
              onChange={handleChange}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
          </div>

          <div className="form-actions">
            <button
              type="button"
              className="secondary-button"
              onClick={() => navigate("/tickets")}
            >
              Cancel
            </button>

            <button
              type="submit"
              className="action-button"
              disabled={loading}
            >
              {loading ? "Creating..." : "Create Ticket"}
            </button>
          </div>
        </form>
      </div>
    </>
  );
}

export default CreateTicket;
