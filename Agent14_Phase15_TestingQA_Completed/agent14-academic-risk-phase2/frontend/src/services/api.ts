import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api",
  timeout: 15000,
});

api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem("agent14_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    const url = String(error?.config?.url ?? "");
    const isAuthLifecycleRequest = url.includes("/auth/login") || url.includes("/auth/logout");

    if (status === 401 && !isAuthLifecycleRequest && typeof window !== "undefined") {
      const authRedirectKey = "agent14_auth_redirected";
      const alreadyRedirecting = sessionStorage.getItem(authRedirectKey) === "1";
      sessionStorage.removeItem("agent14_token");
      sessionStorage.removeItem("agent14_user");

      if (!alreadyRedirecting && window.location.pathname !== "/login") {
        sessionStorage.setItem(authRedirectKey, "1");
        const next = `${window.location.pathname}${window.location.search}`;
        const loginUrl = next === "/login" ? "/login" : `/login?reason=session_expired&next=${encodeURIComponent(next)}`;
        window.location.assign(loginUrl);
      }
    }

    return Promise.reject(error);
  },
);

export default api;
