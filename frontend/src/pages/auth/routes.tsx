import type { RouteObject } from "react-router-dom";
import { LoginPage, ProfilePage, SignupPage, VerifyPage } from "./AuthPages";

const routes: RouteObject[] = [
  { path: "/login", element: <LoginPage /> },
  { path: "/signup", element: <SignupPage /> },
  // protected, but reachable while sign-up is unfinished (that's what they finish)
  { path: "/signup/profile", element: <ProfilePage />, handle: { protected: true, allowIncomplete: true } },
  { path: "/signup/verify", element: <VerifyPage />, handle: { protected: true, allowIncomplete: true } },
];
export default routes;
