import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from "react";
import { useRouter } from "@tanstack/react-router";
import { toast } from "sonner";

interface User {
  id: string;
  name: string;
  email: string;
  picture: string;
}

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  loginWithEmail: (email: string, password: string) => Promise<void>;
  signUpWithEmail: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * Base URL for the FastAPI backend.
 *
 * Set VITE_API_URL in your .env file:
 *   VITE_API_URL=http://localhost:8000      ← local dev
 *   VITE_API_URL=https://your-app.onrender.com  ← production (Vercel env var)
 */
const API_BASE =
  `${(import.meta.env["VITE_API_URL"] as string | undefined) ?? "http://localhost:8000"}/api/auth`;

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const fetchUser = useCallback(async (token: string) => {
    try {
      const res = await fetch(`${API_BASE}/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Invalid or expired token");
      const data = await res.json() as { id: string; full_name: string; email: string };

      setUser({
        id: data.id,
        name: data.full_name,
        email: data.email,
        picture: `https://ui-avatars.com/api/?name=${encodeURIComponent(data.full_name)}&background=0D8ABC&color=fff`,
      });
      setIsAuthenticated(true);
    } catch {
      localStorage.removeItem("token");
      setIsAuthenticated(false);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      fetchUser(token);
    } else {
      setIsLoading(false);
    }
  }, [fetchUser]);

  const loginWithEmail = async (email: string, password: string) => {
    const res = await fetch(`${API_BASE}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({})) as { detail?: string };
      throw new Error(errorData.detail ?? "Invalid email or password.");
    }

    const data = await res.json() as { access_token: string };
    localStorage.setItem("token", data.access_token);
    await fetchUser(data.access_token);

    router.navigate({ to: "/" });
  };

  const signUpWithEmail = async (name: string, email: string, password: string) => {
    const res = await fetch(`${API_BASE}/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ full_name: name, email, password }),
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({})) as { detail?: string };
      throw new Error(errorData.detail ?? "Failed to create account.");
    }

    // Sign-up succeeded — show a message and redirect to login.
    toast.success("Account created successfully. Please log in.");
    logout();
  };

  const logout = () => {
    setIsAuthenticated(false);
    setUser(null);
    localStorage.removeItem("token");
    router.navigate({ to: "/login" });
  };

  return (
    <AuthContext.Provider
      value={{ isAuthenticated, user, loginWithEmail, signUpWithEmail, logout, isLoading }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
