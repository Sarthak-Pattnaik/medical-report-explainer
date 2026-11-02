
"use client";

import { useState } from "react";
import { MessageCircle, X } from "lucide-react";
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
        onClick={() => setIsOpen(true)}
        aria-label="Open report assistant"
        className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500 text-white shadow-lg shadow-emerald-500/25 transition-all hover:scale-105 hover:bg-emerald-400"
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
            aria-label="Medical report assistant"
            className="flex h-[min(780px,88vh)] w-full max-w-[640px] flex-col overflow-hidden rounded-2xl border border-white/10 bg-[#111827] shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Dialog Header */}
            <div className="flex shrink-0 items-center justify-between border-b border-white/10 bg-[#17212b] px-5 py-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/15 text-emerald-400">
                  <MessageCircle size={21} />
                </div>

                <div>
                  <h2 className="font-semibold text-white">
                    Medical Report Assistant
                  </h2>
                  <p className="text-xs text-gray-400">
                    Ask questions about your report
                  </p>
                </div>
              </div>

              <button
                onClick={() => setIsOpen(false)}
                aria-label="Close chat"
                className="rounded-lg p-2 text-gray-400 transition-colors hover:bg-white/10 hover:text-white"
              >
                <X size={20} />
              </button>
            </div>

            {/* Existing Chat Component */}
            <div className="min-h-0 flex-1 overflow-y-auto">
              <ReportChat reportId={reportId} />
            </div>
          </div>
        </div>
      )}
    </>
  );
}
