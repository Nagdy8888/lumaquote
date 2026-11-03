import "./shell.css";
import { useState } from "react";
import { NavLink, Outlet, Link } from "react-router-dom";
import {
  Activity,
  ArrowUpRight,
  BookOpen,
  Camera,
  Check,
  FileText,
  Inbox,
  Layers3,
  LayoutDashboard,
  LogOut,
  Menu,
  Plug,
  Plus,
  ShieldCheck,
} from "lucide-react";
import { useWorkspace } from "@/features/workspace/api";
import { useLiveUpdates } from "@/features/workspace/useLiveUpdates";
import { auth } from "@/shared/auth/client";
import { Button } from "@/shared/ui/button";
import { Skeleton } from "@/shared/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/alert";

const navigation = [
  { to: "/", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/inbox", label: "Inbox", icon: Inbox },
  { to: "/quotations", label: "Quotations", icon: FileText },
  { to: "/catalog", label: "Catalog & evidence", icon: BookOpen },
  { to: "/integrations", label: "Connections", icon: Plug },
];

/** Compose the working shell; features own tasks while TanStack Query owns all remote collections. */
export function AppShell() {
  const { connected } = useLiveUpdates();
  const workspace = useWorkspace();
  const [capture, setCapture] = useState(false);
  if (workspace.isPending)
    return (
      <main className="app-loading" aria-label="Loading workspace">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-64 w-full" />
      </main>
    );
  if (workspace.isError)
    return (
      <main className="app-loading">
        <Alert variant="destructive">
          <AlertTitle>The workspace could not be loaded</AlertTitle>
          <AlertDescription>{workspace.error.message}</AlertDescription>
        </Alert>
        <Button onClick={() => workspace.refetch()}>Try again</Button>
        <Button variant="outline" onClick={() => auth.auth.signOut()}>
          Sign out
        </Button>
      </main>
    );
  const data = workspace.data;
  const pending = data.conversations.filter((c) =>
    ["review", "new", "needs_staff"].includes(c.status),
  ).length;
  return (
    <div className={`app-shell${capture ? " capture-mode" : ""}`}>
      <a className="skip-link" href="#workspace-main">
        Skip to workspace
      </a>
      <aside className="sidebar" aria-label="Workspace navigation and account">
        <Link to="/" className="brand">
          <Layers3 />
          <span>
            LumaQuote<span className="brand-dot">.</span>
          </span>
        </Link>
        <div className="company-switch">
          <div className="company-mark">LS</div>
          <div>
            <strong>{data.company.name}</strong>
            <span>Sales workspace</span>
          </div>
        </div>
        <nav aria-label="Main navigation">
          {navigation.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              aria-label={item.label}
              end={item.end}
              className={({ isActive }) =>
                isActive ? "nav-item active" : "nav-item"
              }
            >
              <item.icon />
              <span>{item.label}</span>
              {item.label === "Inbox" && pending > 0 && (
                <span className="nav-count">{pending}</span>
              )}
            </NavLink>
          ))}
        </nav>
        <details className="mobile-workspace-menu">
          <summary aria-label="More workspace navigation">
            <Menu />
          </summary>
          <nav aria-label="Additional workspace navigation">
            <Link to="/catalog">Catalog & evidence</Link>
            <Link to="/integrations">Connections</Link>
            <button onClick={() => auth.auth.signOut()}>Sign out</button>
          </nav>
        </details>
        <div className="sidebar-bottom">
          <div className="approval-promise">
            <ShieldCheck />
            <span>
              Every quotation.
              <br />
              <strong>Human approved.</strong>
            </span>
          </div>
          <div className="staff-profile">
            <div className="avatar">{data.role === "admin" ? "AD" : "SA"}</div>
            <div>
              <strong>
                {data.role === "admin" ? "Administrator" : "Salesperson"}
              </strong>
              <span>Local staff account</span>
            </div>
            <button aria-label="Sign out" onClick={() => auth.auth.signOut()}>
              <LogOut />
            </button>
          </div>
        </div>
      </aside>
      <div className="shell-main">
        <header className="topbar">
          <div className="local-state">
            <span className="state-dot" />
            <span className="workspace-location">Local workspace</span>
            <span className="topbar-divider" />
            <span className="workspace-disclosure">
              Synthetic supplier data
            </span>
            <span className="topbar-divider" />
            <span className="live-state" data-live={connected}>
              {connected ? "Live" : "Refreshing every few seconds"}
            </span>
          </div>
          <div className="topbar-actions">
            <button
              className={`capture-button${capture ? " enabled" : ""}`}
              aria-pressed={capture}
              aria-label="Capture mode"
              onClick={() => setCapture(!capture)}
            >
              {capture ? <Check /> : <Camera />}
              <span>Capture mode</span>
            </button>
            <Button size="sm" asChild>
              <Link to="/requests/new">
                <Plus data-icon="inline-start" />
                New request
              </Link>
            </Button>
          </div>
        </header>
        <main id="workspace-main" className="workspace-main">
          <Outlet context={{ data, capture }} />
        </main>
        <footer className="app-footer">
          <span>
            <Activity />
            LumaQuote · Fictional company, real workflow
          </span>
          <Link to="/integrations">
            Connection status
            <ArrowUpRight />
          </Link>
        </footer>
      </div>
    </div>
  );
}
