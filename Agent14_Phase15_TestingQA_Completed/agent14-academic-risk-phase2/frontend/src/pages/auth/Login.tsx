import { useState } from "react";
import { useNavigate } from "react-router-dom";
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
      setError("We couldn't sign you in. Check your institutional credentials and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f4f7fb]">
      <div className="grid min-h-screen lg:grid-cols-[1.2fr_0.8fr]">
        <section className="relative hidden overflow-hidden bg-gradient-to-br from-[#173e73] via-[#245c9f] to-[#5f9bd8] p-10 text-white lg:flex lg:flex-col lg:justify-between">
          <div className="absolute inset-0 opacity-30 institutional-grid" aria-hidden="true" />
          <div className="relative z-10">
            <img src="/branding/vignan-brand.png" alt="Vignan's University" className="h-16 w-auto rounded-lg bg-white/95 px-2 py-1 object-contain" />
            <p className="mt-12 text-xs font-bold uppercase tracking-[0.24em] text-white/70">CSE · Academic Systems</p>
            <h1 className="mt-3 max-w-xl text-4xl font-extrabold leading-[1.08] tracking-tight xl:text-5xl">Student Academic<br />Risk Management</h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-blue-50/90">An institution-first early-warning workspace for mentors, department heads and academic leadership.</p>
          </div>
          <div className="relative z-10 max-w-2xl rounded-2xl border border-white/15 bg-white/10 p-5 backdrop-blur-sm">
            <div className="flex items-center gap-3"><span className="grid h-9 w-9 place-items-center rounded-xl bg-white/15 text-lg">✦</span><div><p className="text-sm font-bold">Designed around action</p><p className="text-xs text-white/70">Predict · Prioritize · Intervene · Follow up</p></div></div>
          </div>
        </section>

        <section className="flex min-h-screen items-center justify-center px-5 py-8 sm:px-8">
          <div className="w-full max-w-md">
            <div className="mb-8 lg:hidden"><img src="/branding/vignan-brand.png" alt="Vignan's University" className="h-14 w-auto object-contain" /></div>
            <div className="rounded-[24px] border border-slate-200 bg-white p-6 shadow-[0_20px_50px_rgba(24,40,63,0.08)] sm:p-8">
              <div className="mb-7">
                <span className="inline-flex rounded-full border border-[#cfe0f8] bg-[#edf4ff] px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-brand-700">Institutional access</span>
                <h2 className="mt-3 text-2xl font-extrabold tracking-tight text-[#18345f]">Sign in to your workspace</h2>
                <p className="mt-2 text-sm leading-6 text-slate-500">Use your assigned academic-system account. Access is scoped to your role.</p>
              </div>
              <form onSubmit={handleSubmit} className="space-y-4">
                <label className="block text-xs font-bold text-slate-600" htmlFor="login-email">Institutional email
                  <input id="login-email" type="email" required autoComplete="username" placeholder="name@university.edu" value={email} onChange={(e) => setEmail(e.target.value)} className="mt-1.5 w-full rounded-xl border border-slate-200 bg-[#fbfcfe] px-3.5 py-3 text-sm text-ink-900 transition placeholder:text-slate-400 focus:border-brand-400 focus:bg-white focus:outline-none" />
                </label>
                <label className="block text-xs font-bold text-slate-600" htmlFor="login-password">Password
                  <input id="login-password" type="password" required autoComplete="current-password" placeholder="Enter your password" value={password} onChange={(e) => setPassword(e.target.value)} className="mt-1.5 w-full rounded-xl border border-slate-200 bg-[#fbfcfe] px-3.5 py-3 text-sm text-ink-900 transition placeholder:text-slate-400 focus:border-brand-400 focus:bg-white focus:outline-none" />
                </label>
                {error ? <div role="alert" className="rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-xs font-medium leading-5 text-red-700">{error}</div> : null}
                <button type="submit" disabled={loading} className="w-full rounded-xl bg-[#245f9f] px-4 py-3 text-sm font-bold text-white shadow-sm transition hover:bg-[#1e518a] disabled:cursor-not-allowed disabled:opacity-60">{loading ? "Signing in…" : "Sign in"}</button>
              </form>
              <div className="mt-6 border-t border-slate-100 pt-4 text-center"><p className="text-[10px] font-semibold uppercase tracking-[0.13em] text-slate-400">Protected academic workspace</p></div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
