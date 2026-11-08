"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

export default function HomePage() {
  const router = useRouter();

  const { isAuthenticated, loading } = useAuth();

  useEffect(() => {
    // Wait until AuthContext finishes restoring the session
    if (loading) return;

    if (isAuthenticated) {
      router.replace("/dashboard");
    } else {
      router.replace("/login");
    }
  }, [loading, isAuthenticated, router]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#080d18] text-slate-300">
      <div className="flex items-center gap-3">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-emerald-400 border-t-transparent" />
        <span className="text-sm">Loading MediClarity...</span>
      </div>
    </main>
  );
}