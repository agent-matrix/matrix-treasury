/**
 * Centralized HTTP Client for Matrix Treasury API
 * Handles JWT authentication, error handling, and token management
 */

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  payload: any;

  constructor(status: number, payload: any) {
    super(payload?.detail || payload?.message || `API Error ${status}`);
    this.status = status;
    this.payload = payload;
    this.name = "ApiError";
  }
}

function getToken(): string | null {
  return localStorage.getItem("mmc_token");
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit & { auth?: boolean }
): Promise<T> {
  const { auth = true, ...fetchInit } = init || {};

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(fetchInit.headers || {}),
  };

  // Add JWT Bearer token if auth is required
  if (auth) {
    const token = getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  const url = `${API_BASE_URL}${path}`;

  const response = await fetch(url, {
    ...fetchInit,
    headers,
  });

  // Handle 401 Unauthorized - trigger logout
  if (response.status === 401) {
    localStorage.removeItem("mmc_token");
    window.location.href = "/login";
    throw new ApiError(401, { detail: "Unauthorized - please login again" });
  }

  // Parse response body
  let payload: any;
  const contentType = response.headers.get("content-type");
  if (contentType?.includes("application/json")) {
    payload = await response.json();
  } else {
    payload = await response.text();
  }

  // Throw error for non-2xx responses
  if (!response.ok) {
    throw new ApiError(response.status, payload);
  }

  return payload as T;
}
