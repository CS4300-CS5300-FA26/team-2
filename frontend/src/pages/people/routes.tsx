import type { RouteObject } from "react-router-dom";
import PeoplePage from "./PeoplePage";

const routes: RouteObject[] = [
  { path: "/people", element: <PeoplePage />, handle: { nav: "People", protected: true, order: 40 } },
];
export default routes;
