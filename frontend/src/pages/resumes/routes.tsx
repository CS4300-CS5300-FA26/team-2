import type { RouteObject } from "react-router-dom";
import FeedbackPage from "./FeedbackPage";
import ProfilePage from "./ProfilePage";
import UploadPage from "./UploadPage";

const routes: RouteObject[] = [
  { path: "/resumes/upload", element: <UploadPage />, handle: { nav: "Resumes", protected: true, order: 25 } },
  { path: "/resumes/:id/profile", element: <ProfilePage />, handle: { protected: true } },
  { path: "/resumes/:id/feedback", element: <FeedbackPage />, handle: { protected: true } },
];

export default routes;
