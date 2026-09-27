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
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <p className="text-slate-400">
        Loading MediClarity...
      </p>
    </div>
  );
}