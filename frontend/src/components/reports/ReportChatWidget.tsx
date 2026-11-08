"use client";

import { useState } from "react";
import { MessageCircle } from "lucide-react";
import ReportChat from "./ReportChat";

interface ReportChatWidgetProps {
  reportId: number;
}

export default function ReportChatWidget({
  reportId,
}: ReportChatWidgetProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Floating Chat Button */}
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        aria-label="Open MediClarity AI Assistant"
        className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-400 text-slate-950 shadow-lg shadow-emerald-500/20 transition-all hover:scale-105 hover:bg-emerald-300"
      >
        <MessageCircle size={26} />
      </button>

      {/* Chat Dialog */}
      {isOpen && (
        <div
          className="fixed inset-0 z-[60] flex items-end justify-end bg-black/50 p-4 backdrop-blur-sm"
          onClick={() => setIsOpen(false)}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-label="MediClarity AI Assistant"
            className="flex h-[min(780px,88vh)] w-full max-w-[640px] flex-col overflow-hidden rounded-2xl border border-white/10 bg-[#0b1120] shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <ReportChat
              reportId={reportId}
              onClose={() => setIsOpen(false)}
            />
          </div>
        </div>
      )}
    </>
  );
}