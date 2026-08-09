import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  analyzeTicket,
  getTicketById,
  getTicketComments,
  addTicketComment,
  getTicketActivity,
} from "../services/ticketService";

function TicketDetails() {
  const { ticketId } = useParams();

  const [ticket, setTicket] = useState(null);
  const [aiResult, setAiResult] = useState(null);
  const [comments, setComments] = useState([]);
  const [activities, setActivities] = useState([]);

  const [commentText, setCommentText] = useState("");
  const [slaSeconds, setSlaSeconds] = useState(null);

  const [loading, setLoading] = useState(true);
  const [aiLoading, setAiLoading] = useState(false);
  const [commentLoading, setCommentLoading] = useState(false);

  const [error, setError] = useState("");
  const [aiError, setAiError] = useState("");
  const [commentError, setCommentError] = useState("");

  const loadTicket = async () => {
    const data = await getTicketById(ticketId);
    setTicket(data);
  };

  const loadComments = async () => {
    const data = await getTicketComments(ticketId);

    const commentList = Array.isArray(data)
      ? data
      : Array.isArray(data?.comments)
      ? data.comments
      : Array.isArray(data?.ticket_comments)
      ? data.ticket_comments
      : [];

    setComments(commentList);
  };

  const loadActivity = async () => {
    const data = await getTicketActivity(ticketId);

    const activityList = Array.isArray(data)
      ? data
      : Array.isArray(data?.activities)
      ? data.activities
      : Array.isArray(data?.ticket_activities)
      ? data.ticket_activities
      : [];

    setActivities(activityList);
  };

  const loadAll = async () => {
    setLoading(true);
    setError("");

    try {
      await Promise.all([
        loadTicket(),
        loadComments(),
        loadActivity(),
      ]);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to load ticket details."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, [ticketId]);

  useEffect(() => {
    if (!ticket) return;

    const initialSeconds =
      ticket.sla_remaining_seconds == null
        ? null
        : Number(ticket.sla_remaining_seconds);

    setSlaSeconds(initialSeconds);

    if (
      initialSeconds == null ||
      ticket.sla_status === "completed" ||
      ticket.sla_status === "breached"
    ) {
      return;
    }

    const timer = setInterval(() => {
      setSlaSeconds((previous) => {
        if (previous == null) return null;
        return Math.max(0, previous - 1);
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [
    ticket?.id,
    ticket?.sla_remaining_seconds,
    ticket?.sla_status,
  ]);


  const handleAnalyze = async () => {
    setAiLoading(true);
    setAiError("");

    try {
      const result = await analyzeTicket(ticketId);

      setAiResult(result);

      await Promise.all([
        loadTicket(),
        loadActivity(),
      ]);
    } catch (err) {
      setAiError(
        err.response?.data?.detail ||
        "AI analysis failed."
      );
    } finally {
      setAiLoading(false);
    }
  };

  const handleCommentSubmit = async (event) => {
    event.preventDefault();

    const cleanComment = commentText.trim();

    if (!cleanComment) {
      setCommentError("Comment cannot be empty.");
      return;
    }

    setCommentLoading(true);
    setCommentError("");

    try {
      await addTicketComment(ticketId, cleanComment);

      setCommentText("");

      await Promise.all([
        loadComments(),
        loadActivity(),
      ]);
    } catch (err) {
      console.error("Add comment failed:", err);

      const detail = err.response?.data?.detail;

      let message = "Unable to add comment.";

      if (typeof detail === "string") {
        message = detail;
      } else if (Array.isArray(detail)) {
        message = detail
          .map((item) => item?.msg || JSON.stringify(item))
          .join(", ");
      } else if (detail) {
        message = JSON.stringify(detail);
      }

      setCommentError(message);
    } finally {
      setCommentLoading(false);
    }
  };

  const formatDate = (value) => {
    if (!value) return "";

    const dateValue = String(value);

    const hasTimezone =
      /(?:Z|[+-]\d{2}:\d{2})$/i.test(dateValue);

    const normalizedValue = hasTimezone
      ? dateValue
      : dateValue + "Z";

    return new Date(
      normalizedValue
    ).toLocaleString();
  };

  const formatSlaTime = (totalSeconds) => {
    if (totalSeconds == null) return "--";

    const seconds = Math.max(
      0,
      Number(totalSeconds)
    );

    const days = Math.floor(seconds / 86400);
    const hours = Math.floor(
      (seconds % 86400) / 3600
    );
    const minutes = Math.floor(
      (seconds % 3600) / 60
    );
    const remainingSeconds =
      Math.floor(seconds % 60);

    const time = [
      hours,
      minutes,
      remainingSeconds,
    ]
      .map((value) =>
        String(value).padStart(2, "0")
      )
      .join(":");

    return days > 0
      ? `${days}d ${time}`
      : time;
  };


  const formatAction = (action = "") => {
    return action
      .replaceAll("_", " ")
      .replace(/\b\w/g, (letter) =>
        letter.toUpperCase()
      );
  };

  if (loading) {
    return (
      <div className="page-loader">
        Loading ticket...
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

  if (!ticket) return null;

  const solution =
    aiResult?.solution ||
    ticket.ai_solution ||
    [];

  const slaTotalSeconds =
    Number(ticket.sla_hours || 0) * 3600;

  let displaySlaStatus =
    ticket.sla_status || "within_sla";

  if (
    !["completed", "breached"].includes(
      displaySlaStatus
    ) &&
    slaSeconds != null
  ) {
    if (slaSeconds <= 0) {
      displaySlaStatus = "breached";
    } else if (
      slaTotalSeconds > 0 &&
      slaSeconds <= slaTotalSeconds * 0.2
    ) {
      displaySlaStatus = "near_breach";
    }
  }

  const slaLabels = {
    within_sla: "Within SLA",
    near_breach: "Near Breach",
    breached: "Breached",
    completed: "Completed",
  };

  const slaLabel =
    slaLabels[displaySlaStatus] ||
    "Within SLA";

  return (
    <>
      <section className="page-heading">
        <div>
          <span className="eyebrow">
            TICKET #{ticket.id}
          </span>

          <h1>{ticket.title}</h1>

          <p>
            Review issue details, AI recommendations,
            comments and activity history.
          </p>
        </div>

        <Link
          to="/tickets"
          className="secondary-link"
        >
          Back to Tickets
        </Link>
      </section>

      <section className="ticket-details-grid">
        <div className="ticket-details-main">

          <div className="panel-card">
            <h2>Issue Description</h2>

            <p className="ticket-description">
              {ticket.description}
            </p>
          </div>

          <div className="panel-card ai-panel">
            <div className="ai-panel-header">
              <div>
                <span className="ai-label">
                  AI SUPPORT
                </span>

                <h2>Support Assistant</h2>

                <p className="muted-text">
                  Analyze this ticket and generate troubleshooting recommendations.
                </p>
              </div>

              <button
                type="button"
                className="action-button"
                onClick={handleAnalyze}
                disabled={aiLoading}
              >
                {aiLoading
                  ? "Analyzing..."
                  : "Analyze with AI"}
              </button>
            </div>

            {aiError && (
              <div className="error-message">
                {aiError}
              </div>
            )}

            {aiResult && (
              <div className="ai-analysis-card">
                <div className="ai-result-grid">
                  <div>
                    <span>Category</span>
                    <strong>
                      {aiResult.category || "General"}
                    </strong>
                  </div>

                  <div>
                    <span>Suggested Priority</span>
                    <strong>
                      {aiResult.suggested_priority ||
                        ticket.priority}
                    </strong>
                  </div>

                  <div>
                    <span>Saved</span>
                    <strong>
                      {aiResult.saved_to_database
                        ? "Yes"
                        : "No"}
                    </strong>
                  </div>
                </div>

                <div className="ai-summary">
                  <h3>Analysis</h3>
                  <p>{aiResult.analysis}</p>
                </div>
              </div>
            )}

            {solution.length > 0 && (
              <div className="ai-solution">
                <h3>
                  Recommended Troubleshooting Steps
                </h3>

                <ol>
                  {solution.map((step, index) => (
                    <li key={index}>
                      <span className="step-number">
                        {index + 1}
                      </span>

                      <p>{step}</p>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>

          <div className="panel-card">
            <div className="section-header">
              <div>
                <h2>Comments</h2>
                <p>
                  Add updates or troubleshooting notes.
                </p>
              </div>

              <span className="count-badge">
                {comments.length}
              </span>
            </div>

            <form
              className="comment-form"
              onSubmit={handleCommentSubmit}
            >
              <textarea
                value={commentText}
                onChange={(event) =>
                  setCommentText(event.target.value)
                }
                placeholder="Write a comment..."
                rows="4"
              />

              {commentError && (
                <div className="error-message">
                  {commentError}
                </div>
              )}

              <div className="comment-form-actions">
                <button
                  type="submit"
                  className="action-button"
                  disabled={commentLoading}
                >
                  {commentLoading
                    ? "Adding..."
                    : "Add Comment"}
                </button>
              </div>
            </form>

            <div className="comments-list">
              {comments.length === 0 ? (
                <div className="empty-inline">
                  No comments yet.
                </div>
              ) : (
                comments.map((comment) => (
                  <div
                    className="comment-card"
                    key={comment.id}
                  >
                    <div className="comment-avatar">
                      U
                    </div>

                    <div className="comment-content">
                      <div className="comment-meta">
                        <strong>
                          User #{String(comment.user_id ?? "")}
                        </strong>

                        <span>
                          {formatDate(comment.created_at)}
                        </span>
                      </div>

                      <p>{typeof comment.comment === "object" ? JSON.stringify(comment.comment) : String(comment.comment ?? "")}</p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="panel-card">
            <div className="section-header">
              <div>
                <h2>Activity Timeline</h2>
                <p>
                  Complete history of this ticket.
                </p>
              </div>

              <span className="count-badge">
                {activities.length}
              </span>
            </div>

            <div className="activity-timeline">
              {activities.length === 0 ? (
                <div className="empty-inline">
                  No activity recorded.
                </div>
              ) : (
                activities.map((activity) => (
                  <div
                    className="activity-item"
                    key={activity.id}
                  >
                    <div className="activity-marker">
                      <span></span>
                    </div>

                    <div className="activity-content">
                      <div className="activity-title">
                        <strong>
                          {formatAction(String(activity.action ?? "activity"))}
                        </strong>

                        <span>
                          {formatDate(activity.created_at)}
                        </span>
                      </div>

                      {activity.details && (
                        <p>
                          {typeof activity.details === "object"
                            ? JSON.stringify(activity.details)
                            : String(activity.details)}
                        </p>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>

        <aside className="ticket-meta-card">
          <h2>Ticket Details</h2>

          <div className="meta-row">
            <span>Status</span>

            <strong
              className={"badge badge-" + ticket.status}
            >
              {ticket.status.replace("_", " ")}
            </strong>
          </div>

          <div className="meta-row">
            <span>Priority</span>

            <strong
              className={"badge badge-" + ticket.priority}
            >
              {ticket.priority}
            </strong>
          </div>

          <div
            className={
              "sla-summary-card sla-" +
              displaySlaStatus
            }
          >
            <div className="sla-summary-header">
              <div>
                <span className="sla-eyebrow">
                  SERVICE LEVEL
                </span>
                <h3>SLA Tracking</h3>
              </div>

              <span
                className={
                  "sla-status-badge sla-status-" +
                  displaySlaStatus
                }
              >
                {slaLabel}
              </span>
            </div>

            <div className="sla-countdown">
              <span>
                {displaySlaStatus === "completed"
                  ? "SLA Result"
                  : displaySlaStatus === "breached"
                  ? "SLA Timer"
                  : "Time Remaining"}
              </span>

              <strong>
                {displaySlaStatus === "completed"
                  ? "Completed"
                  : displaySlaStatus === "breached"
                  ? "00:00:00"
                  : formatSlaTime(slaSeconds)}
              </strong>
            </div>

            <div className="sla-info-row">
              <span>SLA Target</span>
              <strong>
                {ticket.sla_hours != null
                  ? ticket.sla_hours + " hours"
                  : "--"}
              </strong>
            </div>

            <div className="sla-info-row">
              <span>Due At</span>
              <strong>
                {ticket.sla_due_at
                  ? formatDate(ticket.sla_due_at)
                  : "--"}
              </strong>
            </div>

            {ticket.sla_breached_at && (
              <div className="sla-info-row">
                <span>Breached At</span>
                <strong>
                  {formatDate(
                    ticket.sla_breached_at
                  )}
                </strong>
              </div>
            )}
          </div>

          <div className="meta-row">
            <span>Category</span>
            <strong>
              {ticket.category || "Unclassified"}
            </strong>
          </div>

          <div className="meta-row">
            <span>Assigned To</span>
            <strong>
              {ticket.assigned_to_id
                ? "User #" + ticket.assigned_to_id
                : "Unassigned"}
            </strong>
          </div>

          <div className="meta-row">
            <span>Created</span>
            <strong>
              {formatDate(ticket.created_at)}
            </strong>
          </div>
        </aside>
      </section>
    </>
  );
}

export default TicketDetails;

