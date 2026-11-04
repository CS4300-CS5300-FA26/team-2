import type { RouteObject } from "react-router-dom";
import { LoginPage, ProfilePage, SignupPage } from "./AuthPages";

const routes: RouteObject[] = [
  { path: "/login", element: <LoginPage /> },
  { path: "/signup", element: <SignupPage /> },
  // protected, but reachable while the profile is incomplete (that's what it completes)
  { path: "/signup/profile", element: <ProfilePage />, handle: { protected: true, allowIncomplete: true } },
];
export default routes;
