"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/context/AuthContext";


export default function DashboardPage() {
  const router = useRouter();

  const {
    user,
    loading,
    isAuthenticated,
    logout,
  } = useAuth();


  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [loading, isAuthenticated, router]);


  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p>Loading dashboard...</p>
      </main>
    );
  }


  if (!isAuthenticated || !user) {
    return null;
  }


  return (
    <main className="min-h-screen p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">
          Medical Report Explainer
        </h1>

        <button
          onClick={logout}
          className="rounded-lg bg-red-500 px-4 py-2 text-white"
        >
          Logout
        </button>
      </div>

      <p className="mt-6">
        Welcome, {user.email}
      </p>

      <p className="mt-2 text-gray-500">
        Your dashboard is ready.
      </p>
    </main>
  );
}