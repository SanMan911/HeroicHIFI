import { createContext, useContext, useState, useEffect } from "react";
import api from "../lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("hhf_token");
    const stored = localStorage.getItem("hhf_user");
    if (token && stored) {
      try {
        setUser(JSON.parse(stored));
      } catch { /* ignore */ }
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    localStorage.setItem("hhf_token", data.token);
    localStorage.setItem("hhf_user", JSON.stringify(data.user));
    setUser(data.user);
    return data;
  };

  const register = async () => {
    // Registration is handled directly in Login page with OTP flow
    throw new Error("Use OTP registration flow in Login page");
  };

  const logout = () => {
    localStorage.removeItem("hhf_token");
    localStorage.removeItem("hhf_user");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
