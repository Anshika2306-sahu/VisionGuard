import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ShieldCheck } from "lucide-react";
import { login } from "../lib/api";
import { useAuth } from "../lib/auth";

const DEMO = [
  { label: "Officer (Command Center)", email: "officer@visionguard.in", password: "officer123" },
  { label: "Admin", email: "admin@visionguard.in", password: "admin123" },
  { label: "Citizen", email: "citizen@visionguard.in", password: "citizen123" },
];

export default function Login() {
  const { setAuth } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("officer@visionguard.in");
  const [password, setPassword] = useState("officer123");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const { access_token, role } = await login(email, password);
      setAuth(access_token, role, email);
      nav(role === "citizen" ? "/citizen" : "/command");
    } catch {
      setError("Invalid email or password");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="card w-full max-w-md">
        <div className="flex items-center gap-3 mb-6">
          <ShieldCheck className="text-brand" size={32} />
          <div>
            <div className="text-2xl font-bold">VisionGuard AI</div>
            <div className="text-xs text-gray-400">Bengaluru Traffic Police · ASTraM · MapMyIndia</div>
          </div>
        </div>
        <form onSubmit={submit} className="space-y-3">
          <input className="input w-full" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
          <input className="input w-full" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" />
          {error && <div className="text-danger text-sm">{error}</div>}
          <button className="btn btn-primary w-full" disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <div className="mt-5 text-xs text-gray-400">
          <div className="mb-1">Demo accounts (click to fill):</div>
          <div className="flex flex-col gap-1">
            {DEMO.map((d) => (
              <button
                key={d.email}
                className="text-left text-brand hover:underline"
                onClick={() => {
                  setEmail(d.email);
                  setPassword(d.password);
                }}
              >
                {d.label} — {d.email}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
