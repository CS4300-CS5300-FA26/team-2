import type { RouteObject } from "react-router-dom";
import AlertsPage from "../AlertsPage";
import NotificationHistoryPage from "../NotificationHistoryPage";

const routes: RouteObject[] = [
  { path: "/alerts", element: <AlertsPage />, handle: { nav: "Alerts", protected: true, order: 30 } },
  { path: "/alerts/history", element: <NotificationHistoryPage />, handle: { nav: "Notifications", protected: true, order: 31 } },
];
export default routes;
