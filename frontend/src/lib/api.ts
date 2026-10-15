// // Dev-only: hardcoded auth until Phase 8 auth screens are built.
// const BASE_URL = "http://localhost:8000/api/v1";
// let devToken: string | null = null;

// export async function ensureDevToken(): Promise<string> {
//   if (devToken) return devToken;
//   const email = `dev_${Date.now()}@example.com`;
//   const res = await fetch(`${BASE_URL}/auth/register`, {
//     method: "POST",
//     headers: { "Content-Type": "application/json" },
//     body: JSON.stringify({ email, password: "password123" }),
//   });
//   const data = await res.json();
//   devToken = data.access_token;
//   return devToken!;
// }

// export function getDevTokenSync(): string | null {
//   return devToken;
// }

// export async function apiFetch(path: string, init: RequestInit = {}) {
//   const token = await ensureDevToken();
//   const isFormData = init.body instanceof FormData;
//   return fetch(`${BASE_URL}${path}`, {
//     ...init,
//     headers: {
//       ...init.headers,
//       Authorization: `Bearer ${token}`,
//       ...(init.body && !isFormData ? { "Content-Type": "application/json" } : {}),
//     },
//   });
// }

// export { BASE_URL };


const BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const ACCESS_TOKEN_KEY = "docsage_access_token";
const REFRESH_TOKEN_KEY = "docsage_refresh_token";

let accessToken: string | null = sessionStorage.getItem(ACCESS_TOKEN_KEY);
let refreshToken: string | null = sessionStorage.getItem(REFRESH_TOKEN_KEY);

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAuthTokens(access: string, refresh: string): void {
  accessToken = access;
  refreshToken = refresh;
  sessionStorage.setItem(ACCESS_TOKEN_KEY, access);
  sessionStorage.setItem(REFRESH_TOKEN_KEY, refresh);
}

export function clearAuthTokens(): void {
  accessToken = null;
  refreshToken = null;
  sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  sessionStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function isAuthenticated(): boolean {
  return Boolean(accessToken);
}

export async function login(email: string, password: string) {
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(data.detail || "Login failed. Check your credentials.");
  }

  setAuthTokens(data.access_token, data.refresh_token);
  return data;
}

export async function register(email: string, password: string) {
  const res = await fetch(`${BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(data.detail || "Registration failed.");
  }

  setAuthTokens(data.access_token, data.refresh_token);
  return data;
}

export async function logout(): Promise<void> {
  const token = accessToken;
  const refresh = refreshToken;

  try {
    if (token) {
      await fetch(`${BASE_URL}/auth/logout`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ refresh_token: refresh }),
      });
    }
  } finally {
    clearAuthTokens();
  }
}

export async function apiFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  if (!accessToken) {
    throw new Error("Please log in to continue.");
  }

  const isFormData = init.body instanceof FormData;

  const makeRequest = (token: string) =>
    fetch(`${BASE_URL}${path}`, {
      ...init,
      headers: {
        ...init.headers,
        Authorization: `Bearer ${token}`,
        ...(init.body && !isFormData
          ? { "Content-Type": "application/json" }
          : {}),
      },
    });

  let response = await makeRequest(accessToken);

  if (response.status === 401 && refreshToken) {
    const res = await fetch(`${BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    const data = await res.json().catch(() => ({}));

    if (res.ok && data.access_token && data.refresh_token) {
      setAuthTokens(data.access_token, data.refresh_token);
      response = await makeRequest(data.access_token);
    } else {
      clearAuthTokens();
      window.dispatchEvent(new Event("docsage:unauthorized"));
    }
  } else if (response.status === 401) {
    clearAuthTokens();
    window.dispatchEvent(new Event("docsage:unauthorized"));
  }

  return response;
}

export { BASE_URL };
