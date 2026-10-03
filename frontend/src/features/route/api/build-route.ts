import { apiPost } from "@/shared/api";

import type { RouteRequest, RouteResponse } from "../model/route";

export const ROUTE_PATH = "/route";

export function buildRoute(request: RouteRequest, signal?: AbortSignal) {
  return apiPost<RouteResponse>(ROUTE_PATH, request, { signal });
}