import { ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { ShieldCheck, LogOut } from "lucide-react";
import { useAuth } from "../lib/auth";

export default function Layout({ children, subtitle }: { children: ReactNode; subtitle?: string }) {
  const { email, role, logout } = useAuth();
  const nav = useNavigate();
  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex items-center justify-between px-6 py-3 border-b border-white/5 bg-panel">
        <div className="flex items-center gap-3">
          <ShieldCheck className="text-brand" size={26} />
          <div>
            <div className="font-bold text-lg leading-tight">VisionGuard AI</div>
            <div className="text-xs text-gray-400">{subtitle || "Bengaluru Traffic Intelligence"}</div>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right text-xs">
            <div className="text-gray-200">{email}</div>
            <div className="text-gray-500 capitalize">{role}</div>
          </div>
          <button
            className="btn btn-ghost flex items-center gap-2 text-sm"
            onClick={() => {
              logout();
              nav("/login");
            }}
          >
            <LogOut size={16} /> Logout
          </button>
        </div>
      </header>
      <main className="flex-1 p-6">{children}</main>
      <footer className="text-center text-xs text-gray-600 py-3 border-t border-white/5">
        Reusing Bengaluru Safe City cameras (UVH-26) + India's MLFF/ANPR enforcement pattern · Maps by
        Mappls / MapMyIndia
      </footer>
    </div>
  );
}
