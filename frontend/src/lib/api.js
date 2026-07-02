import axios from "axios";

const API_BASE = `${process.env.REACT_APP_BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("hhf_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("hhf_token");
      localStorage.removeItem("hhf_user");
      // Redirect to login with a friendly reason + Forgot Password nudge, but
      // skip redirect if the caller is a public endpoint that treats 401 as
      // "not authenticated" (e.g. /heroes/*, /wall-of-fame/*, /recognitions).
      const url = err.config?.url || "";
      const isPublic = /(\/heroes\/|\/wall-of-fame|\/recognitions|\/heroic-patrons|\/top-donor-ledger|\/most-generous-ledger|\/office-posts)/.test(url);
      if (!isPublic && typeof window !== "undefined") {
        const path = window.location.pathname;
        if (path && !path.startsWith("/login") && !path.startsWith("/reset-password")) {
          window.location.href = `/login?reason=session_expired&next=${encodeURIComponent(path)}`;
        }
      }
    }
    return Promise.reject(err);
  }
);

export function formatApiError(detail, err) {
  if (detail == null) {
    if (err?.message?.includes("Network Error")) return "Cannot connect to server. Please check your internet connection.";
    if (err?.code === "ERR_NETWORK") return "Cannot reach the server. It may be starting up — please try again in 30 seconds.";
    return "Something went wrong. Please try again.";
  }
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail.map((e) => (e?.msg ? e.msg : JSON.stringify(e))).join(" ");
  if (detail?.msg) return detail.msg;
  return String(detail);
}

export default api;
