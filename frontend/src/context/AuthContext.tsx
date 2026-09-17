"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import {
  getCurrentUser,
  loginUser,
} from "@/services/authService";

import type {
  LoginData,
  TokenResponse,
  User,
} from "@/types/auth";


interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (data: LoginData) => Promise<void>;
  logout: () => void;
}


const AuthContext = createContext<
  AuthContextType | undefined
>(undefined);


export function AuthProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);


  useEffect(() => {
    async function restoreSession() {
      const token = localStorage.getItem("access_token");

      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const currentUser = await getCurrentUser();

        setUser(currentUser);

      } catch {
        localStorage.removeItem("access_token");
        setUser(null);

      } finally {
        setLoading(false);
      }
    }

    restoreSession();
  }, []);


  async function login(data: LoginData) {
    const tokenResponse: TokenResponse =
      await loginUser(data);

    localStorage.setItem(
      "access_token",
      tokenResponse.access_token
    );

    const currentUser = await getCurrentUser();

    setUser(currentUser);
  }


  function logout() {
    localStorage.removeItem("access_token");
    setUser(null);
  }


  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: user !== null,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}


export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used within an AuthProvider"
    );
  }

  return context;
}