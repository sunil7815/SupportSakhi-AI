import { useEffect, useMemo, useState } from "react";
import "./KnowledgeAdmin.css";

import {
  approveKnowledgeItem,
  createKnowledgeItem,
  deactivateKnowledgeItem,
  getKnowledgeItems,
  searchKnowledge,
} from "../services/knowledgeService";

const CATEGORY_OPTIONS = [
  "network",
  "email",
  "account_access",
  "software",
  "hardware",
  "security",
  "how_to",
  "other",
];

const INITIAL_FORM = {
  title: "",
  category: "network",
  problem_text: "",
  solution_text: "",
  keywords: "",
  source_type: "manual",
  source_reference: "Admin Knowledge Base",
  confidence: 0.9,
  is_approved: false,
};

function KnowledgeAdmin() {
  const [items, setItems] = useState([]);
  const [searchResults, setSearchResults] = useState([]);

  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState(null);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [includeInactive, setIncludeInactive] = useState(true);
  const [isSearchMode, setIsSearchMode] = useState(false);

  const [form, setForm] = useState(INITIAL_FORM);

  const visibleItems = useMemo(() => {
    return isSearchMode ? searchResults : items;
  }, [isSearchMode, searchResults, items]);

  const approvedCount = useMemo(() => {
    return items.filter((item) => item.is_approved).length;
  }, [items]);

  const activeCount = useMemo(() => {
    return items.filter((item) => item.is_active).length;
  }, [items]);

  const normalizeResponseItems = (data) => {
    if (Array.isArray(data)) {
      return data;
    }

    if (Array.isArray(data?.items)) {
      return data.items;
    }

    if (Array.isArray(data?.results)) {
      return data.results;
    }

    return [];
  };

  const getErrorMessage = (err, fallback) => {
    const detail = err?.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (Array.isArray(detail)) {
      return detail
        .map((item) => item?.msg || "Validation error")
        .join(", ");
    }

    return fallback;
  };

  const loadKnowledge = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await getKnowledgeItems({
        includeInactive,
        category: categoryFilter,
      });

      setItems(normalizeResponseItems(data));
    } catch (err) {
      console.error(err);

      setError(
        getErrorMessage(
          err,
          "Unable to load knowledge base items."
        )
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isSearchMode) {
      loadKnowledge();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [includeInactive, categoryFilter, isSearchMode]);

  const handleInputChange = (event) => {
    const {
      name,
      value,
      type,
      checked,
    } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]:
        type === "checkbox"
          ? checked
          : name === "confidence"
          ? Number(value)
          : value,
    }));
  };

  const handleCreateKnowledge = async (event) => {
    event.preventDefault();

    try {
      setCreating(true);
      setError("");
      setSuccess("");

      const payload = {
        title: form.title.trim(),
        category: form.category,

        problem_text: form.problem_text.trim(),
        solution_text: form.solution_text.trim(),

        keywords: form.keywords
          .split(",")
          .map((keyword) => keyword.trim())
          .filter(Boolean),

        source_type:
          form.source_type.trim() || "manual",

        source_reference:
          form.source_reference.trim() || null,

        confidence: Number(form.confidence),

        is_approved: Boolean(form.is_approved),
      };

      await createKnowledgeItem(payload);

      setSuccess(
        "Knowledge item created successfully."
      );

      setForm(INITIAL_FORM);

      setSearchQuery("");
      setSearchResults([]);
      setIsSearchMode(false);

      await loadKnowledge();
    } catch (err) {
      console.error(err);

      setError(
        getErrorMessage(
          err,
          "Unable to create knowledge item."
        )
      );
    } finally {
      setCreating(false);
    }
  };

  const runSearch = async () => {
    const query = searchQuery.trim();

    if (!query) {
      setSearchResults([]);
      setIsSearchMode(false);

      await loadKnowledge();
      return;
    }

    try {
      setLoading(true);
      setError("");

      const data = await searchKnowledge({
        q: query,
        category: categoryFilter,
        limit: 20,
        minScore: 0.15,
      });

      setSearchResults(
        normalizeResponseItems(data)
      );

      setIsSearchMode(true);
    } catch (err) {
      console.error(err);

      setError(
        getErrorMessage(
          err,
          "Knowledge search failed."
        )
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (event) => {
    event.preventDefault();

    setSuccess("");

    await runSearch();
  };

  const clearSearch = async () => {
    setSearchQuery("");
    setSearchResults([]);
    setIsSearchMode(false);

    setError("");
    setSuccess("");

    await loadKnowledge();
  };

  const refreshCurrentView = async () => {
    if (
      isSearchMode &&
      searchQuery.trim()
    ) {
      await runSearch();
      return;
    }

    await loadKnowledge();
  };

  const handleApprove = async (id) => {
    try {
      setActionLoadingId(id);
      setError("");
      setSuccess("");

      await approveKnowledgeItem(id);

      setSuccess(
        `Knowledge item #${id} approved successfully.`
      );

      await refreshCurrentView();
    } catch (err) {
      console.error(err);

      setError(
        getErrorMessage(
          err,
          "Unable to approve knowledge item."
        )
      );
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleDeactivate = async (id) => {
    try {
      setActionLoadingId(id);
      setError("");
      setSuccess("");

      await deactivateKnowledgeItem(id);

      setSuccess(
        `Knowledge item #${id} deactivated successfully.`
      );

      await refreshCurrentView();
    } catch (err) {
      console.error(err);

      setError(
        getErrorMessage(
          err,
          "Unable to deactivate knowledge item."
        )
      );
    } finally {
      setActionLoadingId(null);
    }
  };

  return (
    <div className="knowledge-admin-page">
      <div className="knowledge-admin-header">
        <div>
          <p className="knowledge-eyebrow">
            RAG Knowledge Management
          </p>

          <h1>Knowledge Base Admin</h1>

          <p>
            Create, search, approve, and deactivate
            support knowledge used by the AI
            resolution engine.
          </p>
        </div>

        <div className="knowledge-summary">
          <div>
            <strong>{items.length}</strong>
            <span>Loaded Items</span>
          </div>

          <div>
            <strong>{approvedCount}</strong>
            <span>Approved</span>
          </div>

          <div>
            <strong>{activeCount}</strong>
            <span>Active</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="knowledge-alert knowledge-alert-error">
          {error}
        </div>
      )}

      {success && (
        <div className="knowledge-alert knowledge-alert-success">
          {success}
        </div>
      )}

      <div className="knowledge-admin-grid">
        {/* CREATE KNOWLEDGE */}
        <section className="knowledge-panel">
          <div className="knowledge-panel-heading">
            <div>
              <p className="knowledge-eyebrow">
                Create Article
              </p>

              <h2>Add Knowledge Item</h2>
            </div>
          </div>

          <form
            className="knowledge-form"
            onSubmit={handleCreateKnowledge}
          >
            <label>
              Title
              <input
                name="title"
                value={form.title}
                onChange={handleInputChange}
                placeholder="WiFi connected but no internet"
                required
              />
            </label>

            <label>
              Category
              <select
                name="category"
                value={form.category}
                onChange={handleInputChange}
              >
                {CATEGORY_OPTIONS.map(
                  (category) => (
                    <option
                      key={category}
                      value={category}
                    >
                      {category.replaceAll(
                        "_",
                        " "
                      )}
                    </option>
                  )
                )}
              </select>
            </label>

            <label>
              Problem
              <textarea
                name="problem_text"
                value={form.problem_text}
                onChange={handleInputChange}
                placeholder="Describe the support problem..."
                rows={4}
                required
              />
            </label>

            <label>
              Solution
              <textarea
                name="solution_text"
                value={form.solution_text}
                onChange={handleInputChange}
                placeholder="Enter troubleshooting and resolution steps..."
                rows={7}
                required
              />
            </label>

            <label>
              Keywords
              <input
                name="keywords"
                value={form.keywords}
                onChange={handleInputChange}
                placeholder="wifi, internet, dns, network"
              />

              <small>
                Separate keywords using commas.
              </small>
            </label>

            <div className="knowledge-form-row">
              <label>
                Source Type
                <select
                  name="source_type"
                  value={form.source_type}
                  onChange={handleInputChange}
                >
                  <option value="manual">
                    Manual
                  </option>

                  <option value="ticket">
                    Ticket
                  </option>

                  <option value="documentation">
                    Documentation
                  </option>

                  <option value="admin">
                    Admin
                  </option>
                </select>
              </label>

              <label>
                Source Reference
                <input
                  name="source_reference"
                  value={form.source_reference}
                  onChange={handleInputChange}
                  placeholder="Admin Knowledge Base"
                />
              </label>
            </div>

            <label>
              Confidence
              <input
                name="confidence"
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={form.confidence}
                onChange={handleInputChange}
                required
              />

              <small>
                Use a value from 0.00 to 1.00.
              </small>
            </label>

            <div className="knowledge-checkbox-row">
              <label>
                <input
                  name="is_approved"
                  type="checkbox"
                  checked={form.is_approved}
                  onChange={handleInputChange}
                />

                Approve immediately
              </label>
            </div>

            <button
              className="knowledge-primary-button"
              type="submit"
              disabled={creating}
            >
              {creating
                ? "Creating..."
                : "Create Knowledge Item"}
            </button>
          </form>
        </section>

        {/* KNOWLEDGE LIBRARY */}
        <section className="knowledge-panel">
          <div className="knowledge-panel-heading">
            <div>
              <p className="knowledge-eyebrow">
                Knowledge Library
              </p>

              <h2>Manage Articles</h2>
            </div>

            <button
              type="button"
              className="knowledge-secondary-button"
              onClick={refreshCurrentView}
              disabled={loading}
            >
              {loading
                ? "Loading..."
                : "Refresh"}
            </button>
          </div>

          <form
            className="knowledge-search-bar"
            onSubmit={handleSearch}
          >
            <input
              value={searchQuery}
              onChange={(event) =>
                setSearchQuery(
                  event.target.value
                )
              }
              placeholder="Search WiFi, Outlook, account access..."
            />

            <select
              value={categoryFilter}
              onChange={(event) =>
                setCategoryFilter(
                  event.target.value
                )
              }
            >
              <option value="">
                All Categories
              </option>

              {CATEGORY_OPTIONS.map(
                (category) => (
                  <option
                    key={category}
                    value={category}
                  >
                    {category.replaceAll(
                      "_",
                      " "
                    )}
                  </option>
                )
              )}
            </select>

            <button
              type="submit"
              className="knowledge-primary-button"
              disabled={loading}
            >
              Search
            </button>

            {isSearchMode && (
              <button
                type="button"
                className="knowledge-secondary-button"
                onClick={clearSearch}
              >
                Clear
              </button>
            )}
          </form>

          <label className="knowledge-inline-check">
            <input
              type="checkbox"
              checked={includeInactive}
              onChange={(event) =>
                setIncludeInactive(
                  event.target.checked
                )
              }
            />

            Include inactive knowledge
          </label>

          {loading ? (
            <div className="knowledge-empty-state">
              Loading knowledge base...
            </div>
          ) : visibleItems.length === 0 ? (
            <div className="knowledge-empty-state">
              No knowledge items found.
            </div>
          ) : (
            <div className="knowledge-list">
              {visibleItems.map((item) => (
                <article
                  className="knowledge-card"
                  key={item.id}
                >
                  <div className="knowledge-card-top">
                    <div>
                      <span className="knowledge-id">
                        #{item.id}
                      </span>

                      <h3>
                        {item.title ||
                          "Untitled Knowledge Item"}
                      </h3>
                    </div>

                    <div className="knowledge-badges">
                      <span
                        className={`knowledge-badge ${
                          item.is_approved
                            ? "knowledge-badge-success"
                            : "knowledge-badge-warning"
                        }`}
                      >
                        {item.is_approved
                          ? "Approved"
                          : "Pending"}
                      </span>

                      <span
                        className={`knowledge-badge ${
                          item.is_active
                            ? "knowledge-badge-success"
                            : "knowledge-badge-muted"
                        }`}
                      >
                        {item.is_active
                          ? "Active"
                          : "Inactive"}
                      </span>
                    </div>
                  </div>

                  <div className="knowledge-meta">
                    <span>
                      {item.category
                        ?.replaceAll(
                          "_",
                          " "
                        ) || "other"}
                    </span>

                    {item.confidence !==
                      undefined &&
                      item.confidence !==
                        null && (
                        <span>
                          Confidence:{" "}
                          {Math.round(
                            Number(
                              item.confidence
                            ) * 100
                          )}
                          %
                        </span>
                      )}

                    {item.relevance_score !==
                      undefined &&
                      item.relevance_score !==
                        null && (
                        <span>
                          Match:{" "}
                          {Math.round(
                            Number(
                              item.relevance_score
                            ) * 100
                          )}
                          %
                        </span>
                      )}
                  </div>

                  <div className="knowledge-content-block">
                    <strong>Problem</strong>

                    <p>
                      {item.problem_text ||
                        "No problem description provided."}
                    </p>
                  </div>

                  <div className="knowledge-content-block">
                    <strong>Solution</strong>

                    <p>
                      {item.solution_text ||
                        "No solution provided."}
                    </p>
                  </div>

                  {item.source_type && (
                    <div className="knowledge-content-block">
                      <strong>
                        Source
                      </strong>

                      <p>
                        {item.source_type}

                        {item.source_reference
                          ? ` — ${item.source_reference}`
                          : ""}
                      </p>
                    </div>
                  )}

                  {Array.isArray(
                    item.keywords
                  ) &&
                    item.keywords.length >
                      0 && (
                      <div className="knowledge-keywords">
                        {item.keywords.map(
                          (
                            keyword,
                            index
                          ) => (
                            <span
                              key={`${item.id}-${keyword}-${index}`}
                            >
                              {keyword}
                            </span>
                          )
                        )}
                      </div>
                    )}

                  <div className="knowledge-card-actions">
                    {!item.is_approved && (
                      <button
                        type="button"
                        className="knowledge-approve-button"
                        disabled={
                          actionLoadingId ===
                          item.id
                        }
                        onClick={() =>
                          handleApprove(
                            item.id
                          )
                        }
                      >
                        {actionLoadingId ===
                        item.id
                          ? "Working..."
                          : "Approve"}
                      </button>
                    )}

                    {item.is_active && (
                      <button
                        type="button"
                        className="knowledge-danger-button"
                        disabled={
                          actionLoadingId ===
                          item.id
                        }
                        onClick={() =>
                          handleDeactivate(
                            item.id
                          )
                        }
                      >
                        {actionLoadingId ===
                        item.id
                          ? "Working..."
                          : "Deactivate"}
                      </button>
                    )}
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

export default KnowledgeAdmin;