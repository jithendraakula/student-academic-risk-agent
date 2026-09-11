import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Card from "../../components/Card";
import { useAuth } from "../../context/AuthContext";
import type { Role } from "../../types";
import api from "../../services/api";

const ROLE_HOME: Record<Role, string> = {
  mentor: "/mentor",
  hod: "/hod",
  dean: "/dean",
  admin: "/admin",
};

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.post("/auth/login", { email, password });
      login(res.data.user, res.data.token);
      navigate(ROLE_HOME[res.data.user.role as Role]);
    } catch {
      setError("Invalid credentials. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-100 to-brand-50 flex items-center justify-center px-4">
      <Card className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-6">
          <div className="w-12 h-12 rounded-xl bg-brand-500 flex items-center justify-center text-white font-bold text-lg mb-3">
            A14
          </div>
          <h1 className="text-xl font-bold text-ink-900">Academic Risk Agent</h1>
          <p className="text-sm text-slate-500 mt-1">Sign in to continue</p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <label className="flex flex-col gap-1 text-xs font-semibold text-slate-600" htmlFor="login-email">
            Email
            <input
              id="login-email"
              type="email"
              required
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-full border border-slate-200 px-4 py-2.5 text-sm font-normal text-ink-900 focus:outline-none focus:ring-2 focus:ring-brand-300"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs font-semibold text-slate-600" htmlFor="login-password">
            Password
            <input
              id="login-password"
              type="password"
              required
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-full border border-slate-200 px-4 py-2.5 text-sm font-normal text-ink-900 focus:outline-none focus:ring-2 focus:ring-brand-300"
            />
          </label>

          {error && <p className="text-xs text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-full bg-brand-500 hover:bg-brand-600 text-white font-semibold py-2.5 text-sm transition disabled:opacity-60"
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </Card>
    </div>
  );
}
