import type { RouteObject } from "react-router-dom";
import FeedbackPage from "./FeedbackPage";
import UploadPage from "./UploadPage";

const routes: RouteObject[] = [
  { path: "/resumes/upload", element: <UploadPage /> },
  { path: "/resumes/:id/feedback", element: <FeedbackPage /> },
];

export default routes;
