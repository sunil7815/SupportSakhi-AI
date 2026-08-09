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
        <div className="sidebar-brand">
          <div className="sidebar-logo">S</div>

          <div>
            <h2>SupportSakhi</h2>
            <span>AI Support Desk</span>
          </div>
        </div>

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

          {user?.role === "admin" && (
            <NavLink to="/admin">
              Admin Dashboard
            </NavLink>
          )}
        </nav>

        <div className="sidebar-user">
          <div className="user-avatar">
            {user?.name?.charAt(0)?.toUpperCase() || "U"}
          </div>

          <div className="sidebar-user-info">
            <strong>{user?.name}</strong>
            <span>{user?.role}</span>
          </div>

          <button
            className="sidebar-logout"
            onClick={handleLogout}
          >
            Logout
          </button>
        </div>
      </aside>

      <div className="app-main">
        <header className="topbar">
          <div>
            <h3>SupportSakhi AI</h3>
            <p>Intelligent IT support workspace</p>
          </div>

          <div className="topbar-status">
            <span className="status-dot"></span>
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
