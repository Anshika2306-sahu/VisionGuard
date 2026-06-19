import { createContext, useContext, useState, ReactNode } from "react";

interface AuthState {
  token: string | null;
  role: string | null;
  email: string | null;
  setAuth: (token: string, role: string, email: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthState>(null as any);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(localStorage.getItem("vg_token"));
  const [role, setRole] = useState<string | null>(localStorage.getItem("vg_role"));
  const [email, setEmail] = useState<string | null>(localStorage.getItem("vg_email"));

  const setAuth = (t: string, r: string, e: string) => {
    localStorage.setItem("vg_token", t);
    localStorage.setItem("vg_role", r);
    localStorage.setItem("vg_email", e);
    setToken(t);
    setRole(r);
    setEmail(e);
  };

  const logout = () => {
    localStorage.removeItem("vg_token");
    localStorage.removeItem("vg_role");
    localStorage.removeItem("vg_email");
    setToken(null);
    setRole(null);
    setEmail(null);
  };

  return (
    <AuthContext.Provider value={{ token, role, email, setAuth, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
