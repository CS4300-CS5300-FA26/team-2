import type { RouteObject } from "react-router-dom";
import FeedPage from "./FeedPage";
import SavedPage from "./SavedPage";

const routes: RouteObject[] = [
  { path: "/feed", element: <FeedPage /> },
  { path: "/saved", element: <SavedPage /> },
];

export default routes;
