import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        {/* Brand */}
        <div className="sidebar-brand">
          <div className="sidebar-logo">S</div>

          <div>
            <h2>SupportSakhi</h2>
            <span>AI Support Desk</span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="sidebar-nav">
          <NavLink to="/dashboard">
            Dashboard
          </NavLink>

          <NavLink to="/tickets">
            My Tickets
          </NavLink>

          <NavLink to="/tickets/create">
            Create Ticket
          </NavLink>

          <NavLink to="/ai-chat">
            AI Support Chat
          </NavLink>

          {user?.role === "admin" && (
            <>
              <NavLink to="/knowledge-admin">
                Knowledge Base
              </NavLink>

              <NavLink to="/admin">
                Admin Dashboard
              </NavLink>
            </>
          )}
        </nav>

        {/* User Section */}
        <div className="sidebar-user">
          <div className="user-avatar">
            {user?.name?.charAt(0)?.toUpperCase() || "U"}
          </div>

          <div className="sidebar-user-info">
            <strong>
              {user?.name || "User"}
            </strong>

            <span>
              {user?.role || "user"}
            </span>
          </div>

          <button
            type="button"
            className="sidebar-logout"
            onClick={handleLogout}
          >
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="app-main">
        <header className="topbar">
          <div>
            <h3>SupportSakhi AI</h3>

            <p>
              Intelligent IT support workspace
            </p>
          </div>

          <div className="topbar-status">
            <span className="status-dot" />
            Backend Connected
          </div>
        </header>

        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default AppLayout;