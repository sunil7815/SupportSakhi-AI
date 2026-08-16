import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  confirmResolution,
  getChatContext,
  getChatHealth,
  sendChatMessage,
} from "../services/chatService";

import "./AIChat.css";


const QUICK_PROMPTS = [
  {
    id: "network",
    icon: "🌐",
    title: "Network Issue",
    description: "WiFi, DNS or internet problems",
    prompt:
      "My WiFi is connected but the internet is not working. Help me troubleshoot the issue.",
  },
  {
    id: "outlook",
    icon: "✉️",
    title: "Outlook Issue",
    description: "Email send / receive problems",
    prompt:
      "Outlook is not sending or receiving emails. Help me diagnose and fix the issue.",
  },
  {
    id: "account",
    icon: "🔐",
    title: "Account Access",
    description: "Login or access problems",
    prompt:
      "I am unable to access my account. Help me troubleshoot the issue safely.",
  },
  {
    id: "software",
    icon: "⚙️",
    title: "Software Problem",
    description: "Applications not working",
    prompt:
      "An application is not opening or working correctly on my computer. Help me troubleshoot it.",
  },
];


function AIChat() {
  const [tickets, setTickets] =
    useState([]);

  const [
    selectedTicketId,
    setSelectedTicketId,
  ] = useState("");

  const [message, setMessage] =
    useState("");

  const [messages, setMessages] =
    useState([
      {
        id: 1,
        role: "assistant",
        text:
          "Hi, I’m SupportSakhi AI. Describe your IT issue or select an existing ticket and I’ll help you troubleshoot it safely.",
        time: new Date(),
      },
    ]);

  const [
    latestResult,
    setLatestResult,
  ] = useState(null);

  const [
    attemptedSteps,
    setAttemptedSteps,
  ] = useState([]);

  const [loading, setLoading] =
    useState(false);

  const [
    contextLoading,
    setContextLoading,
  ] = useState(true);

  const [
    resolutionLoading,
    setResolutionLoading,
  ] = useState(false);

  const [error, setError] =
    useState("");

  const [
    resolutionMessage,
    setResolutionMessage,
  ] = useState("");

  const [
    copiedStep,
    setCopiedStep,
  ] = useState(null);

  const [
    chatHealth,
    setChatHealth,
  ] = useState(null);

  const messageEndRef =
    useRef(null);

  const textareaRef =
    useRef(null);


  // =========================================================
  // HELPERS
  // =========================================================

  const formatTime = (value) => {
    if (!value) {
      return "";
    }

    const date =
      value instanceof Date
        ? value
        : new Date(value);

    return date.toLocaleTimeString(
      [],
      {
        hour: "2-digit",
        minute: "2-digit",
      }
    );
  };


  const toPercent = (value) => {
    const number =
      Number(value);

    if (
      Number.isNaN(number) ||
      number < 0
    ) {
      return 0;
    }

    if (number <= 1) {
      return Math.round(
        number * 100
      );
    }

    return Math.min(
      100,
      Math.round(number)
    );
  };


  const getDecisionText = (
    value,
    fallback = "-"
  ) => {
    if (
      typeof value === "string"
    ) {
      return value;
    }

    if (
      typeof value === "boolean"
    ) {
      return value
        ? "Approved"
        : "Blocked";
    }

    return fallback;
  };


  const buildAssistantText = (
    result
  ) => {
    if (result?.reply) {
      return result.reply;
    }

    if (
      result?.assistant_message
    ) {
      return result.assistant_message;
    }

    if (
      result?.escalation_recommended
    ) {
      return (
        "I analyzed the issue. Automated troubleshooting has limited confidence, so human review or escalation is recommended."
      );
    }

    const steps =
      Array.isArray(
        result
          ?.troubleshooting_steps
      )
        ? result.troubleshooting_steps
        : [];

    if (steps.length > 0) {
      return (
        `I analyzed your issue and prepared ${steps.length} troubleshooting step${
          steps.length === 1
            ? ""
            : "s"
        }. Follow the plan in Agent Intelligence, select the steps you actually tried, and tell me whether the issue was solved.`
      );
    }

    return (
      "I completed the analysis. Review the Agent Intelligence panel for the decision and recommended next action."
    );
  };


  // =========================================================
  // AUTO SCROLL
  // =========================================================

  useEffect(() => {
    messageEndRef.current
      ?.scrollIntoView({
        behavior: "smooth",
        block: "end",
      });
  }, [
    messages,
    loading,
  ]);


  // =========================================================
  // LOAD INITIAL CHAT DATA
  // =========================================================

  useEffect(() => {
    const loadInitialData =
      async () => {
        setContextLoading(true);

        try {
          const [
            contextResult,
            healthResult,
          ] =
            await Promise.allSettled([
              getChatContext(),
              getChatHealth(),
            ]);

          if (
            contextResult.status ===
            "fulfilled"
          ) {
            const data =
              contextResult.value;

            const availableTickets =
              data?.tickets ||
              data?.items ||
              [];

            setTickets(
              Array.isArray(
                availableTickets
              )
                ? availableTickets
                : []
            );
          } else {
            console.error(
              "Chat context failed:",
              contextResult.reason
            );
          }

          if (
            healthResult.status ===
            "fulfilled"
          ) {
            setChatHealth(
              healthResult.value
            );
          } else {
            console.error(
              "Chat health failed:",
              healthResult.reason
            );
          }
        } catch (err) {
          console.error(
            "Chat initialization failed:",
            err
          );
        } finally {
          setContextLoading(false);
        }
      };

    loadInitialData();
  }, []);


  // =========================================================
  // SELECTED TICKET
  // =========================================================

  const selectedTicket =
    useMemo(() => {
      if (
        !selectedTicketId
      ) {
        return null;
      }

      return tickets.find(
        (ticket) =>
          String(ticket.id) ===
          String(
            selectedTicketId
          )
      );
    }, [
      tickets,
      selectedTicketId,
    ]);


  // =========================================================
  // QUICK SUPPORT
  // =========================================================

  const handleQuickPrompt = (
    prompt
  ) => {
    setMessage(prompt);

    setError("");
    setResolutionMessage("");

    window.setTimeout(
      () => {
        textareaRef.current
          ?.focus();
      },
      50
    );
  };


  // =========================================================
  // SEND CHAT MESSAGE
  // =========================================================

  const handleSendMessage =
    async (event) => {
      event?.preventDefault();

      const cleanMessage =
        message.trim();

      if (
        !cleanMessage ||
        loading
      ) {
        return;
      }

      setError("");
      setResolutionMessage("");
      setAttemptedSteps([]);
      setCopiedStep(null);

      const userMessage = {
        id:
          Date.now(),

        role:
          "user",

        text:
          cleanMessage,

        time:
          new Date(),
      };

      setMessages(
        (previous) => [
          ...previous,
          userMessage,
        ]
      );

      setMessage("");
      setLoading(true);

      try {
        const result =
          await sendChatMessage({
            message:
              cleanMessage,

            ticketId:
              selectedTicketId
                ? Number(
                    selectedTicketId
                  )
                : null,
          });

        setLatestResult(
          result
        );

        setMessages(
          (previous) => [
            ...previous,
            {
              id:
                Date.now() + 1,

              role:
                "assistant",

              text:
                buildAssistantText(
                  result
                ),

              time:
                new Date(),
            },
          ]
        );
      } catch (err) {
        console.error(
          "Chat request failed:",
          err
        );

        const detail =
          err?.response
            ?.data?.detail;

        const errorText =
          typeof detail ===
          "string"
            ? detail
            : "Unable to contact the SupportSakhi AI backend.";

        setError(
          errorText
        );

        setMessages(
          (previous) => [
            ...previous,
            {
              id:
                Date.now() + 2,

              role:
                "assistant",

              text:
                "I could not process the request. Please check the backend connection and try again.",

              error:
                true,

              time:
                new Date(),
            },
          ]
        );
      } finally {
        setLoading(false);

        window.setTimeout(
          () => {
            textareaRef.current
              ?.focus();
          },
          100
        );
      }
    };


  // =========================================================
  // SELECT ATTEMPTED STEP
  // =========================================================

  const toggleAttemptedStep = (
    step
  ) => {
    setAttemptedSteps(
      (previous) => {
        if (
          previous.includes(
            step
          )
        ) {
          return previous.filter(
            (item) =>
              item !== step
          );
        }

        return [
          ...previous,
          step,
        ];
      }
    );
  };


  // =========================================================
  // COPY TROUBLESHOOTING STEP
  // =========================================================

  const handleCopyStep =
    async (
      step,
      index
    ) => {
      try {
        await navigator
          .clipboard
          .writeText(step);

        setCopiedStep(
          index
        );

        window.setTimeout(
          () => {
            setCopiedStep(null);
          },
          1500
        );
      } catch (err) {
        console.error(
          "Unable to copy step:",
          err
        );
      }
    };


  // =========================================================
  // RESOLUTION CONFIRMATION
  // =========================================================

  const handleResolution =
    async (resolved) => {
      if (
        !selectedTicketId
      ) {
        setError(
          "Select an existing ticket before confirming the resolution."
        );

        return;
      }

      if (
        resolved &&
        attemptedSteps.length ===
          0
      ) {
        setError(
          "Select at least one troubleshooting step that you actually tried before confirming the issue as solved."
        );

        return;
      }

      setError("");
      setResolutionMessage("");
      setResolutionLoading(
        true
      );

      try {
        const result =
          await confirmResolution({
            ticketId:
              Number(
                selectedTicketId
              ),

            resolved,

            attemptedSteps,

            failureReason:
              resolved
                ? null
                : "User confirmed that the attempted troubleshooting steps did not resolve the issue.",
          });

        const feedbackMessage =
          result?.message ||
          (
            resolved
              ? "Resolution confirmation saved successfully."
              : "Failure feedback saved. The agent will avoid failed steps and prepare the next action."
          );

        setResolutionMessage(
          feedbackMessage
        );

        const nextSteps =
          result?.next_steps ||
          result
            ?.troubleshooting_steps;

        setLatestResult(
          (previous) => ({
            ...(previous ||
              {}),
            ...result,

            ...(
              Array.isArray(
                nextSteps
              )
                ? {
                    troubleshooting_steps:
                      nextSteps,
                  }
                : {}
            ),
          })
        );

        setAttemptedSteps(
          []
        );

        setMessages(
          (previous) => [
            ...previous,
            {
              id:
                Date.now(),

              role:
                "assistant",

              text:
                feedbackMessage,

              time:
                new Date(),
            },
          ]
        );
      } catch (err) {
        console.error(
          "Resolution confirmation failed:",
          err
        );

        const detail =
          err?.response
            ?.data?.detail;

        setError(
          typeof detail ===
          "string"
            ? detail
            : "Unable to save the resolution confirmation."
        );
      } finally {
        setResolutionLoading(
          false
        );
      }
    };


  // =========================================================
  // RESET CHAT
  // =========================================================

  const handleNewChat =
    () => {
      setMessage("");
      setLatestResult(null);
      setAttemptedSteps([]);
      setError("");
      setResolutionMessage("");
      setCopiedStep(null);

      setMessages([
        {
          id:
            Date.now(),

          role:
            "assistant",

          text:
            "New support session started. Describe your IT issue and I’ll analyze it safely.",

          time:
            new Date(),
        },
      ]);

      window.setTimeout(
        () => {
          textareaRef.current
            ?.focus();
        },
        100
      );
    };


  // =========================================================
  // DERIVED RESPONSE DATA
  // =========================================================

  const troubleshootingSteps =
    Array.isArray(
      latestResult
        ?.troubleshooting_steps
    )
      ? latestResult
          .troubleshooting_steps
      : [];


  const classification =
    latestResult
      ?.classification ||
    {};


  const knowledgeRetrieval =
    latestResult
      ?.knowledge_retrieval ||
    {};


  const knowledgeSources =
    Array.isArray(
      knowledgeRetrieval
        ?.sources
    )
      ? knowledgeRetrieval.sources
      : [];


  const verification =
    latestResult
      ?.verification ||
    {};


  const skepticReview =
    latestResult
      ?.skeptic_review ||
    latestResult
      ?.skeptic ||
    {};


  const multiAgent =
    latestResult
      ?.multi_agent_verification ||
    latestResult
      ?.multi_agent ||
    latestResult
      ?.multi_agent_decision ||
    {};


  const multiAgentGate =
    latestResult
      ?.multi_agent_gate ||
    latestResult
      ?.gate ||
    latestResult
      ?.auto_resolution_gate ||
    {};


  const confidencePercent =
    toPercent(
      classification
        ?.confidence
    );


  const verificationPercent =
    toPercent(
      verification
        ?.verification_score
    );


  const allAgentsApproved =
    Boolean(
      multiAgent
        ?.all_agents_approved ??
      multiAgent
        ?.approved ??
      false
    );


  const humanReviewRequired =
    Boolean(
      multiAgentGate
        ?.human_review_required ??
      latestResult
        ?.human_review_required ??
      false
    );


  const autoResolutionAllowed =
    Boolean(
      latestResult
        ?.can_auto_resolve ??
      multiAgentGate
        ?.auto_resolution_allowed ??
      false
    );


  const proofRequired =
    Boolean(
      latestResult
        ?.proof_required_before_resolution ??
      latestResult
        ?.proof_required ??
      false
    );


  const healthFeatures =
    chatHealth
      ?.features ||
    {};


  const knowledgeBaseReady =
    Boolean(
      chatHealth
        ?.knowledge_base ??
      healthFeatures
        ?.knowledge_base ??
      false
    );


  const ragReady =
    Boolean(
      chatHealth
        ?.rag_retrieval ??
      healthFeatures
        ?.rag_retrieval ??
      knowledgeBaseReady
    );


  const aiEngineOnline =
    Boolean(
      chatHealth &&
      (
        chatHealth.status ===
          "healthy" ||
        chatHealth.status ===
          "ok" ||
        chatHealth.service
      )
    );


  // =========================================================
  // AGENT PIPELINE
  // =========================================================

  const agentTimeline = [
    {
      name:
        "Issue Classification",

      complete:
        Boolean(
          classification
            ?.category
        ),

      detail:
        classification
          ?.category ||
        "Waiting",
    },

    {
      name:
        "Knowledge Retrieval",

      complete:
        Boolean(
          knowledgeRetrieval
            ?.status
        ),

      detail:
        knowledgeRetrieval
          ?.used
          ? `${knowledgeRetrieval.result_count || 0} source(s)`
          : (
              knowledgeRetrieval
                ?.status ||
              "Waiting"
            ),
    },

    {
      name:
        "Smart Memory",

      complete:
        latestResult
          ?.failure_memory_used !==
        undefined,

      detail:
        latestResult
          ?.failure_memory_used
          ? "Memory applied"
          : "No prior failure",
    },

    {
      name:
        "Safety Verification",

      complete:
        Boolean(
          verification
            ?.decision
        ),

      detail:
        verification
          ?.decision ||
        "Waiting",
    },

    {
      name:
        "Skeptic Review",

      complete:
        Boolean(
          skepticReview
            ?.decision
        ),

      detail:
        skepticReview
          ?.decision ||
        "Waiting",
    },

    {
      name:
        "Final Consensus",

      complete:
        latestResult !==
        null,

      detail:
        allAgentsApproved
          ? "Approved"
          : (
              latestResult
                ?.agent_decision ||
              latestResult
                ?.decision ||
              "Review"
            ),
    },
  ];


  return (
    <div className="ai-chat-page">

      {/* ===================================================
          HEADER
      =================================================== */}

      <header className="ai-chat-header">

        <div>

          <span className="eyebrow">
            AGENTIC SUPPORT
          </span>

          <h1>
            SupportSakhi AI Assistant
          </h1>

          <p>
            Intelligent IT troubleshooting
            powered by knowledge retrieval,
            Smart Memory, multi-agent safety
            verification and
            Proof-of-Resolution.
          </p>


          <div className="ai-live-status-row">

            <span
              className={
                aiEngineOnline
                  ? "ai-live-chip online"
                  : "ai-live-chip"
              }
            >
              <span className="ai-live-dot" />

              {aiEngineOnline
                ? "AI Engine Online"
                : "AI Engine Offline"}
            </span>


            <span
              className={
                knowledgeBaseReady
                  ? "ai-live-chip online"
                  : "ai-live-chip"
              }
            >
              {knowledgeBaseReady
                ? "Knowledge Base Ready"
                : "Knowledge Base Unavailable"}
            </span>


            <span
              className={
                ragReady
                  ? "ai-live-chip online"
                  : "ai-live-chip"
              }
            >
              {ragReady
                ? "RAG Ready"
                : "RAG Unavailable"}
            </span>

          </div>

        </div>


        <button
          type="button"
          className="secondary-button"
          onClick={
            handleNewChat
          }
        >
          + New Chat
        </button>

      </header>


      {/* ===================================================
          QUICK SUPPORT
      =================================================== */}

      <section className="ai-quick-actions">

        <div className="ai-quick-actions-heading">

          <div>
            <span>
              Quick Support
            </span>

            <small>
              Start with a common IT issue
            </small>
          </div>

          <span className="ai-quick-badge">
            AI Assisted
          </span>

        </div>


        <div className="ai-quick-actions-grid">

          {QUICK_PROMPTS.map(
            (item) => (

              <button
                key={item.id}
                type="button"
                className="ai-quick-action"
                disabled={loading}
                onClick={() =>
                  handleQuickPrompt(
                    item.prompt
                  )
                }
              >

                <span className="ai-quick-action-icon">
                  {item.icon}
                </span>


                <span className="ai-quick-action-content">

                  <strong>
                    {item.title}
                  </strong>

                  <small>
                    {item.description}
                  </small>

                  <span>
                    Ask SupportSakhi →
                  </span>

                </span>

              </button>
            )
          )}

        </div>

      </section>


      {/* ===================================================
          TICKET CONTEXT
      =================================================== */}

      <section className="ai-ticket-selector">

        <div>

          <label htmlFor="ticket-select">
            Link this chat to a ticket
          </label>

          <p>
            Linking a ticket enables
            failure memory,
            Proof-of-Resolution and
            autonomous status updates.
          </p>

        </div>


        <select
          id="ticket-select"
          value={
            selectedTicketId
          }
          disabled={
            contextLoading
          }
          onChange={(event) => {

            setSelectedTicketId(
              event.target.value
            );

            setLatestResult(null);

            setAttemptedSteps([]);

            setResolutionMessage("");

            setError("");
          }}
        >

          <option value="">
            General Support Chat
          </option>

          {tickets.map(
            (ticket) => (

              <option
                key={
                  ticket.id
                }
                value={
                  ticket.id
                }
              >
                #{ticket.id} -{" "}
                {ticket.title}
              </option>

            )
          )}

        </select>

      </section>


      {selectedTicket && (

        <div className="selected-ticket-card">

          <div>

            <span>
              Ticket #
              {selectedTicket.id}
            </span>

            <strong>
              {selectedTicket.title}
            </strong>

          </div>


          <span className="ticket-status-pill">
            {selectedTicket.status}
          </span>

        </div>

      )}


      {/* ===================================================
          MAIN WORKSPACE
      =================================================== */}

      <div className="ai-chat-grid">


        {/* =================================================
            CHAT
        ================================================= */}

        <section className="ai-chat-panel">


          <div className="ai-message-list">

            {messages.map(
              (item) => (

                <div
                  key={
                    item.id
                  }
                  className={
                    item.role ===
                    "user"
                      ? "ai-message ai-message-user"
                      : (
                          item.error
                            ? "ai-message ai-message-assistant ai-message-error"
                            : "ai-message ai-message-assistant"
                        )
                  }
                >

                  <div className="ai-message-meta">

                    <span className="ai-message-role">

                      {item.role ===
                      "user"
                        ? "You"
                        : "SupportSakhi"}

                    </span>


                    <span className="ai-message-time">

                      {formatTime(
                        item.time
                      )}

                    </span>

                  </div>


                  <p>
                    {item.text}
                  </p>

                </div>

              )
            )}


            {loading && (

              <div className="ai-message ai-message-assistant ai-typing-message">

                <div className="ai-message-meta">

                  <span className="ai-message-role">
                    SupportSakhi
                  </span>

                  <span className="ai-processing-label">
                    Processing
                  </span>

                </div>


                <div className="ai-typing-row">

                  <span />
                  <span />
                  <span />

                  <small>
                    Classifying issue,
                    searching knowledge,
                    checking memory and
                    verifying safety...
                  </small>

                </div>

              </div>

            )}


            <div
              ref={
                messageEndRef
              }
            />

          </div>


          {error && (

            <div className="ai-chat-error">
              {error}
            </div>

          )}


          {resolutionMessage && (

            <div className="ai-chat-success">
              {resolutionMessage}
            </div>

          )}


          {/* CHATGPT STYLE COMPOSER */}

          <div className="ai-composer-shell">

            <form
              className="ai-chat-input"
              onSubmit={
                handleSendMessage
              }
            >

              <textarea
                ref={
                  textareaRef
                }
                value={
                  message
                }
                rows={3}
                maxLength={2000}
                disabled={
                  loading
                }
                placeholder={
                  selectedTicket
                    ? `Ask SupportSakhi about ticket #${selectedTicket.id}...`
                    : "Ask SupportSakhi anything about your IT issue..."
                }
                onChange={(
                  event
                ) =>
                  setMessage(
                    event.target
                      .value
                  )
                }
                onKeyDown={(
                  event
                ) => {

                  if (
                    event.key ===
                      "Enter" &&
                    !event.shiftKey
                  ) {

                    event.preventDefault();

                    handleSendMessage(
                      event
                    );
                  }

                }}
              />


              <button
                type="submit"
                className="primary-button"
                disabled={
                  loading ||
                  !message.trim()
                }
              >
                {loading
                  ? "Analyzing..."
                  : "Send →"}
              </button>

            </form>


            <div className="ai-composer-footer">

              <span>
                Enter to send •
                Shift + Enter for new line
              </span>

              <span>
                {message.length}/2000
              </span>

            </div>

          </div>

        </section>


        {/* =================================================
            AGENT INTELLIGENCE
        ================================================= */}

        <aside className="ai-intelligence-panel">


          {!latestResult && (

            <div className="ai-empty-state">

              <div className="ai-empty-icon">
                AI
              </div>

              <h3>
                Agent Intelligence
              </h3>

              <p>
                Classification, RAG
                retrieval, Smart Memory,
                safety verification,
                autonomy and resolution
                status will appear here.
              </p>

            </div>

          )}


          {latestResult && (
            <>


              {/* AGENT PIPELINE */}

              <div className="ai-result-card">

                <div className="ai-result-heading">

                  <h3>
                    Agent Pipeline
                  </h3>

                  <span className="ai-status-badge success">
                    Complete
                  </span>

                </div>


                <div className="agent-timeline">

                  {agentTimeline.map(
                    (
                      item,
                      index
                    ) => (

                      <div
                        key={
                          item.name
                        }
                        className={
                          item.complete
                            ? "agent-timeline-item completed"
                            : "agent-timeline-item"
                        }
                      >

                        <div className="agent-timeline-marker">

                          {item.complete
                            ? "✓"
                            : index + 1}

                        </div>


                        <div>

                          <strong>
                            {item.name}
                          </strong>

                          <span>

                            {getDecisionText(
                              item.detail,
                              "Waiting"
                            )}

                          </span>

                        </div>

                      </div>

                    )
                  )}

                </div>

              </div>


              {/* CLASSIFICATION */}

              <div className="ai-result-card">

                <div className="ai-result-heading">

                  <h3>
                    Classification
                  </h3>

                  <span className="ai-status-badge">

                    {classification
                      ?.category ||
                      "other"}

                  </span>

                </div>


                <div className="ai-metric-grid">

                  <div>
                    <span>
                      Priority
                    </span>

                    <strong>
                      {classification
                        ?.priority ||
                        "-"}
                    </strong>
                  </div>


                  <div>
                    <span>
                      Risk
                    </span>

                    <strong>
                      {classification
                        ?.risk_level ||
                        classification
                          ?.risk ||
                        "-"}
                    </strong>
                  </div>


                  <div>
                    <span>
                      Auto Resolve
                    </span>

                    <strong>

                      {autoResolutionAllowed
                        ? "Allowed"
                        : "Blocked"}

                    </strong>
                  </div>


                  <div>
                    <span>
                      Escalation
                    </span>

                    <strong>

                      {latestResult
                        ?.escalation_recommended
                        ? "Recommended"
                        : "Not Required"}

                    </strong>
                  </div>

                </div>


                <div className="ai-score-section">

                  <div className="ai-score-header">

                    <span>
                      Classification Confidence
                    </span>

                    <strong>
                      {confidencePercent}%
                    </strong>

                  </div>


                  <div className="ai-progress-track">

                    <div
                      className="ai-progress-fill"
                      style={{
                        width:
                          `${confidencePercent}%`,
                      }}
                    />

                  </div>

                </div>

              </div>


              {/* RAG KNOWLEDGE */}

              <div className="ai-result-card">

                <div className="ai-result-heading">

                  <h3>
                    RAG Knowledge
                  </h3>

                  <span
                    className={
                      knowledgeRetrieval
                        ?.used
                        ? "ai-status-badge success"
                        : "ai-status-badge"
                    }
                  >

                    {knowledgeRetrieval
                      ?.status ||
                      "no_match"}

                  </span>

                </div>


                <p className="ai-result-description">

                  {knowledgeRetrieval
                    ?.used
                    ? `${knowledgeRetrieval.result_count || knowledgeSources.length} relevant knowledge source(s) retrieved.`
                    : "No approved knowledge source was used for this request."}

                </p>


                {knowledgeSources.map(
                  (
                    source,
                    index
                  ) => {

                    const relevance =
                      toPercent(
                        source
                          ?.relevance_score
                      );

                    const quality =
                      toPercent(
                        source
                          ?.quality_score
                      );

                    return (

                      <div
                        key={
                          source?.id ??
                          index
                        }
                        className="knowledge-source"
                      >

                        <strong>

                          {source?.title ||
                            "Knowledge Article"}

                        </strong>


                        <div className="knowledge-score-row">

                          <span>
                            Relevance
                          </span>

                          <b>
                            {relevance}%
                          </b>

                        </div>


                        <div className="mini-progress-track">

                          <div
                            className="mini-progress-fill"
                            style={{
                              width:
                                `${relevance}%`,
                            }}
                          />

                        </div>


                        <div className="knowledge-score-row">

                          <span>
                            Quality
                          </span>

                          <b>
                            {quality}%
                          </b>

                        </div>


                        <div className="mini-progress-track">

                          <div
                            className="mini-progress-fill quality"
                            style={{
                              width:
                                `${quality}%`,
                            }}
                          />

                        </div>

                      </div>

                    );
                  }
                )}

              </div>


              {/* TROUBLESHOOTING */}

              <div className="ai-result-card">

                <div className="ai-result-heading">

                  <h3>
                    Troubleshooting Plan
                  </h3>

                  <span className="ai-count-badge">
                    {troubleshootingSteps.length}
                  </span>

                </div>


                {troubleshootingSteps.length ===
                0 ? (

                  <p className="ai-result-description">

                    Automated troubleshooting
                    is unavailable or human
                    review is required.

                  </p>

                ) : (

                  <div className="troubleshooting-list">

                    {troubleshootingSteps.map(
                      (
                        step,
                        index
                      ) => (

                        <div
                          key={`${step}-${index}`}
                          className="troubleshooting-step-wrapper"
                        >

                          <label className="troubleshooting-step">

                            <input
                              type="checkbox"
                              checked={
                                attemptedSteps.includes(
                                  step
                                )
                              }
                              onChange={() =>
                                toggleAttemptedStep(
                                  step
                                )
                              }
                            />

                            <span className="step-number">
                              {index + 1}
                            </span>

                            <span>
                              {step}
                            </span>

                          </label>


                          <button
                            type="button"
                            className="copy-step-button"
                            onClick={() =>
                              handleCopyStep(
                                step,
                                index
                              )
                            }
                          >

                            {copiedStep ===
                            index
                              ? "Copied"
                              : "Copy"}

                          </button>

                        </div>

                      )
                    )}

                  </div>

                )}

              </div>


              {/* SMART MEMORY */}

              <div className="ai-result-card">

                <div className="ai-result-heading">

                  <h3>
                    Smart Memory
                  </h3>

                  <span
                    className={
                      latestResult
                        ?.failure_memory_used
                        ? "ai-status-badge success"
                        : "ai-status-badge"
                    }
                  >

                    {latestResult
                      ?.failure_memory_used
                      ? "Active"
                      : "Fresh"}

                  </span>

                </div>


                <div className="ai-metric-grid">

                  <div>
                    <span>
                      Memory Used
                    </span>

                    <strong>

                      {latestResult
                        ?.failure_memory_used
                        ? "Yes"
                        : "No"}

                    </strong>
                  </div>


                  <div>
                    <span>
                      Failed Attempts
                    </span>

                    <strong>

                      {latestResult
                        ?.repeated_failure_count ??
                        0}

                    </strong>
                  </div>

                </div>


                {Array.isArray(
                  latestResult
                    ?.skipped_failed_steps
                ) &&
                  latestResult
                    .skipped_failed_steps
                    .length > 0 && (

                  <div className="skipped-step-box">

                    <strong>
                      Previously failed steps skipped
                    </strong>

                    {latestResult
                      .skipped_failed_steps
                      .map(
                        (
                          step,
                          index
                        ) => (

                          <p
                            key={`${step}-${index}`}
                          >
                            {step}
                          </p>

                        )
                      )}

                  </div>

                )}

              </div>


              {/* MULTI AGENT */}

              <div className="ai-result-card">

                <div className="ai-result-heading">

                  <h3>
                    Multi-Agent Safety
                  </h3>

                  <span
                    className={
                      allAgentsApproved
                        ? "ai-status-badge success"
                        : "ai-status-badge"
                    }
                  >

                    {allAgentsApproved
                      ? "Consensus"
                      : "Review"}

                  </span>

                </div>


                <div className="agent-check-row">

                  <span>
                    Safety Verifier
                  </span>

                  <strong>
                    {verification
                      ?.decision ||
                      "-"}
                  </strong>

                </div>


                <div className="ai-score-section compact">

                  <div className="ai-score-header">

                    <span>
                      Verification Confidence
                    </span>

                    <strong>
                      {verificationPercent}%
                    </strong>

                  </div>


                  <div className="ai-progress-track">

                    <div
                      className="ai-progress-fill verification"
                      style={{
                        width:
                          `${verificationPercent}%`,
                      }}
                    />

                  </div>

                </div>


                <div className="agent-check-row">

                  <span>
                    Skeptic Agent
                  </span>

                  <strong>
                    {skepticReview
                      ?.decision ||
                      "-"}
                  </strong>

                </div>


                <div className="agent-check-row">

                  <span>
                    Final Consensus
                  </span>

                  <strong>

                    {allAgentsApproved
                      ? "Approved"
                      : "Not Approved"}

                  </strong>

                </div>


                <div className="agent-check-row">

                  <span>
                    Human Review
                  </span>

                  <strong>

                    {humanReviewRequired
                      ? "Required"
                      : "Not Required"}

                  </strong>

                </div>

              </div>


              {/* AUTONOMY */}

              <div className="ai-result-card autonomy-gate-card">

                <div className="ai-result-heading">

                  <h3>
                    Autonomy Gate
                  </h3>

                  <span
                    className={
                      autoResolutionAllowed
                        ? "ai-status-badge success"
                        : "ai-status-badge"
                    }
                  >

                    {autoResolutionAllowed
                      ? "Open"
                      : "Blocked"}

                  </span>

                </div>


                <div className="autonomy-gate-grid">

                  <div>
                    <span>
                      Classification
                    </span>

                    <strong>

                      {classification
                        ?.auto_resolve_candidate
                        ? "Passed"
                        : "Review"}

                    </strong>
                  </div>


                  <div>
                    <span>
                      Verification
                    </span>

                    <strong>

                      {verification
                        ?.decision ||
                        "-"}

                    </strong>
                  </div>


                  <div>
                    <span>
                      Consensus
                    </span>

                    <strong>

                      {allAgentsApproved
                        ? "Passed"
                        : "Blocked"}

                    </strong>
                  </div>


                  <div>
                    <span>
                      Final Gate
                    </span>

                    <strong>

                      {autoResolutionAllowed
                        ? "Eligible"
                        : "Human Review"}

                    </strong>
                  </div>

                </div>

              </div>


              {/* PROOF OF RESOLUTION */}

              <div className="ai-result-card resolution-card">

                <h3>
                  Did this solve the issue?
                </h3>


                {!selectedTicketId ? (

                  <p className="ai-result-description">

                    Link an existing ticket
                    to record
                    Proof-of-Resolution and
                    update ticket status.

                  </p>

                ) : (

                  <p className="ai-result-description">

                    Select only the
                    troubleshooting steps
                    you actually tried and
                    then confirm the result.

                  </p>

                )}


                <div className="resolution-actions">

                  <button
                    type="button"
                    className="resolution-success-button"
                    disabled={
                      resolutionLoading ||
                      !selectedTicketId
                    }
                    onClick={() =>
                      handleResolution(
                        true
                      )
                    }
                  >

                    {resolutionLoading
                      ? "Saving..."
                      : "Issue Solved"}

                  </button>


                  <button
                    type="button"
                    className="resolution-failed-button"
                    disabled={
                      resolutionLoading ||
                      !selectedTicketId
                    }
                    onClick={() =>
                      handleResolution(
                        false
                      )
                    }
                  >
                    Still Not Working
                  </button>

                </div>


                {proofRequired && (

                  <div className="proof-note">

                    Proof-of-Resolution is
                    required before autonomous
                    ticket closure.

                  </div>

                )}

              </div>

            </>
          )}

        </aside>

      </div>

    </div>
  );
}


export default AIChat;