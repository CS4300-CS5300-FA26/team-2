import type { RouteObject } from "react-router-dom";
import FeedPage from "./FeedPage";
import SavedPage from "./SavedPage";

const routes: RouteObject[] = [
  { path: "/feed", element: <FeedPage />, handle: { nav: "Feed", protected: true, order: 10 } },
  { path: "/saved", element: <SavedPage />, handle: { nav: "Saved", protected: true, order: 20 } },
];

export default routes;
