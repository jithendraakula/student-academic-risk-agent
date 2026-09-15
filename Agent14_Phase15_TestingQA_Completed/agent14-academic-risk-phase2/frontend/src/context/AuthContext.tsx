import api from "../services/api";
import { createContext, useContext, useState, type ReactNode } from "react";
import type { AuthUser } from "../types";

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  login: (user: AuthUser, token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    const raw = sessionStorage.getItem("agent14_user");
    if (!raw) return null;
    try {
      return JSON.parse(raw) as AuthUser;
    } catch {
      sessionStorage.removeItem("agent14_user");
      sessionStorage.removeItem("agent14_token");
      return null;
    }
  });
  const [token, setToken] = useState<string | null>(() =>
    sessionStorage.getItem("agent14_token")
  );

  function login(newUser: AuthUser, newToken: string) {
    setUser(newUser);
    setToken(newToken);
    sessionStorage.setItem("agent14_user", JSON.stringify(newUser));
    sessionStorage.setItem("agent14_token", newToken);
    sessionStorage.removeItem("agent14_auth_redirected");
  }

  function logout() {
    void api.post("/auth/logout").catch(() => undefined);
    setUser(null);
    setToken(null);
    sessionStorage.removeItem("agent14_user");
    sessionStorage.removeItem("agent14_token");
    sessionStorage.removeItem("agent14_auth_redirected");
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
