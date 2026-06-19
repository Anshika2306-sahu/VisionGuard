import { Navigate, Route, Routes } from "react-router-dom";
import Login from "./pages/Login";
import CommandCenter from "./pages/CommandCenter";
import CitizenPortal from "./pages/CitizenPortal";
import { useAuth } from "./lib/auth";

function RequireRole({ roles, children }: { roles: string[]; children: JSX.Element }) {
  const { token, role } = useAuth();
  if (!token) return <Navigate to="/login" replace />;
  if (role && !roles.includes(role)) return <Navigate to="/citizen" replace />;
  return children;
}

export default function App() {
  const { token, role } = useAuth();
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/command"
        element={
          <RequireRole roles={["admin", "officer"]}>
            <CommandCenter />
          </RequireRole>
        }
      />
      <Route
        path="/citizen"
        element={
          token ? <CitizenPortal /> : <Navigate to="/login" replace />
        }
      />
      <Route
        path="*"
        element={
          <Navigate to={!token ? "/login" : role === "citizen" ? "/citizen" : "/command"} replace />
        }
      />
    </Routes>
  );
}
