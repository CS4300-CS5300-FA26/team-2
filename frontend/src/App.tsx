import { Link, Navigate, NavLink, Outlet, RouterProvider, createBrowserRouter, useLocation, useNavigate } from "react-router-dom";
import type { RouteObject } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth";
import Button from "./components/Button";
import Card from "./components/Card";
import PageHeader from "./components/PageHeader";

/*
 * ROUTE CONTRACT (no merge conflicts): every `src/pages/<area>/routes.tsx` must
 * default-export a `RouteObject[]` with ABSOLUTE paths ("/feed", "/saved", ...).
 * The shell auto-collects them with import.meta.glob. Optional `handle` on a route:
 *   nav?: string        label -> shows a top-nav link (only when it is also reachable)
 *   order?: number      nav sort order (default 100)
 *   protected?: boolean require login; redirects to /login?next=... and, until sign-up
 *                       is finished, to /signup/profile or /signup/verify
 *   allowIncomplete?: boolean  protected, but skip the unfinished-sign-up redirects
 * Logged-in user anywhere: `const { user } = useAuth()` from "./auth".
 */
interface Handle { nav?: string; order?: number; protected?: boolean; allowIncomplete?: boolean }

const modules = import.meta.glob<{ default: RouteObject[] }>("./pages/*/routes.tsx", { eager: true });
const pageRoutes = Object.values(modules).flatMap((m) => m.default);

function RequireAuth({ allowIncomplete, children }: { allowIncomplete?: boolean; children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const loc = useLocation();
  if (loading) return <p className="muted" role="status">Loading...</p>;
  if (!user) return <Navigate to={`/login?next=${encodeURIComponent(loc.pathname + loc.search)}`} replace />;
  if (!allowIncomplete && !user.profile_complete) return <Navigate to="/signup/profile" replace />;
  if (!allowIncomplete && !user.email_verified) return <Navigate to="/signup/verify" replace />;
  return <>{children}</>;
}

function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const signOut = async () => {
    try { await logout(); } finally { navigate("/login", { replace: true }); }
  };
  const links = pageRoutes
    .filter((r) => (r.handle as Handle | undefined)?.nav && (!(r.handle as Handle).protected || user))
    .sort((a, b) => ((a.handle as Handle).order ?? 100) - ((b.handle as Handle).order ?? 100));
  return (
    <>
      <a className="skip-link" href="#main">Skip to content</a>
      <header className="nav">
        <nav className="nav-inner" aria-label="Main">
          <Link to="/" className="nav-brand">Path<span>finder</span></Link>
          <div className="nav-links">
            {links.map((r) => (
              <NavLink key={r.path} to={r.path!}>{(r.handle as Handle).nav}</NavLink>
            ))}
          </div>
          <div className="nav-user">
            {user ? (
              <>
                <span>{user.first_name || user.username}</span>
                <Button size="sm" onClick={signOut}>Log out</Button>
              </>
            ) : (
              <>
                <Link to="/login" className="btn btn-sm">Log in</Link>
                <Link to="/signup" className="btn btn-sm btn-primary">Sign up</Link>
              </>
            )}
          </div>
        </nav>
      </header>
      <main id="main" className="container">
        <Outlet />
      </main>
    </>
  );
}

function NotFound() {
  return (
    <Card>
      <PageHeader title="Page not found" subtitle="That page doesn't exist." />
      <Link to="/feed" className="btn btn-primary">Back to feed</Link>
    </Card>
  );
}

const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { path: "/", element: <Navigate to="/feed" replace /> },
      ...pageRoutes.map((r) => {
        const h = r.handle as Handle | undefined;
        return h?.protected ? { ...r, element: <RequireAuth allowIncomplete={h.allowIncomplete}>{r.element}</RequireAuth> } : r;
      }),
      // old Django URLs (bookmarks, emails)
      { path: "/accounts/login", element: <Navigate to="/login" replace /> },
      { path: "/accounts/signup", element: <Navigate to="/signup" replace /> },
      { path: "*", element: <NotFound /> },
    ],
  },
]);

export default function App() {
  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  );
}
