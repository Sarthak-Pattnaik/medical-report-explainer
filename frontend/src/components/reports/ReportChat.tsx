"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import axios from "axios";

import {
  sendChatMessage,
  getChatHistory,
  deleteChatHistory,
  type ChatMessage,
} from "@/services/chatService";

interface ReportChatProps {
  reportId: number;
}

const suggestedQuestions = [
  "Explain the abnormal findings in my report.",
  "What do the medical terms in my report mean?",
  "Which findings should I discuss with my doctor?",
];

export default function ReportChat({ reportId }: ReportChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState("");

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to the latest message.
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  };

  // Retrieve previous conversation.
  const loadMessages = useCallback(async () => {
    try {
      setIsLoading(true);
      setError("");

      const response = await getChatHistory(reportId);

      setMessages(response.messages);
    } catch (error) {
      console.error("Failed to load chat history:", error);

      setError("Unable to load your previous conversation.");
    } finally {
      setIsLoading(false);
    }
  }, [reportId]);

  useEffect(() => {
    loadMessages();
  }, [loadMessages]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSending]);

  // Send a message.
  const handleSendMessage = async (message?: string) => {
    const trimmedMessage = (message ?? input).trim();

    if (!trimmedMessage || isSending || isDeleting) {
      return;
    }

    setInput("");
    setError("");
    setIsSending(true);

    // Optimistically display the user's message.
    const temporaryMessage: ChatMessage = {
      id: Date.now(),
      role: "user",
      content: trimmedMessage,
      created_at: new Date().toISOString(),
    };

    setMessages((previous) => [
      ...previous,
      temporaryMessage,
    ]);

    try {
      const response = await sendChatMessage(
        reportId,
        trimmedMessage
      );

      // Replace temporary message with saved messages.
      setMessages((previous) => [
        ...previous.filter(
          (message) => message.id !== temporaryMessage.id
        ),
        response.user_message,
        response.assistant_message,
      ]);
    } catch (error) {
      console.error("Failed to send chat message:", error);

      // Remove the temporary message if sending fails.
      setMessages((previous) =>
        previous.filter(
          (message) => message.id !== temporaryMessage.id
        )
      );

      if (axios.isAxiosError(error)) {
        setError(
          error.response?.data?.detail ??
          "Unable to generate a response. Please try again."
        );
      } else {
        setError("Something went wrong. Please try again.");
      }

      setInput(trimmedMessage);
    } finally {
      setIsSending(false);
    }
  };

  // Delete conversation history.
  const handleDeleteChat = async () => {
    if (isSending || isDeleting || messages.length === 0) {
      return;
    }

    const confirmed = window.confirm(
      "Are you sure you want to clear this conversation? This action cannot be undone."
    );

    if (!confirmed) {
      return;
    }

    try {
      setIsDeleting(true);
      setError("");

      await deleteChatHistory(reportId);

      setMessages([]);
    } catch (error) {
      console.error("Failed to delete chat history:", error);

      setError("Unable to clear the conversation. Please try again.");
    } finally {
      setIsDeleting(false);
    }
  };

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLTextAreaElement>
  ) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <section className="mt-8 overflow-hidden rounded-2xl border border-emerald-400/15 bg-slate-900/60">

      {/* Header */}
      <div className="flex items-center justify-between gap-4 border-b border-white/6 p-5 sm:p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-emerald-400/20 bg-emerald-400/10 text-emerald-300">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              className="h-6 w-6"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 11.5a8.4 8.4 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.4 8.4 0 0 1-3.8-.9L3 21l1.9-5.7a8.4 8.4 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.4 8.4 0 0 1 3.8-.9h.5a8.5 8.5 0 0 1 8 8v.5Z" />
            </svg>
          </div>

          <div>
            <h2 className="font-semibold text-white">
              Ask About Your Report
            </h2>

            <p className="mt-1 text-xs text-slate-500">
              MediClarity AI Assistant
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={handleDeleteChat}
          disabled={
            messages.length === 0 ||
            isDeleting ||
            isSending ||
            isLoading
          }
          className="flex items-center gap-2 rounded-lg border border-white/10 px-3 py-2 text-xs font-medium text-slate-400 transition hover:border-red-400/30 hover:text-red-300 disabled:cursor-not-allowed disabled:opacity-40"
          title="Clear conversation"
        >
          {isDeleting ? (
            "Clearing..."
          ) : (
            <>
              <span aria-hidden="true">⌫</span>
              <span className="hidden sm:inline">Clear chat</span>
            </>
          )}
        </button>
      </div>

      {/* Chat messages */}
      <div
        className="h-[480px] overflow-y-auto p-4 sm:p-6"
        aria-live="polite"
        aria-label="Chat conversation"
      >
        {isLoading ? (
          <div className="flex h-full items-center justify-center gap-3 text-sm text-slate-400">
            <span className="h-5 w-5 animate-spin rounded-full border-2 border-emerald-400/20 border-t-emerald-400" />
            Loading conversation...
          </div>
        ) : (
          <>
            {/* Welcome state */}
            {messages.length === 0 && (
              <div className="flex min-h-full flex-col items-center justify-center py-8 text-center">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-emerald-400/20 bg-emerald-400/10 text-2xl text-emerald-300">
                  ✦
                </div>

                <h3 className="mt-5 text-lg font-semibold text-white">
                  How can I help you understand your report?
                </h3>

                <p className="mt-2 max-w-md text-sm leading-6 text-slate-400">
                  Ask follow-up questions about your medical
                  findings, test results, or unfamiliar
                  medical terminology.
                </p>

                <div className="mt-6 w-full max-w-lg space-y-2">
                  <p className="mb-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Suggested questions
                  </p>

                  {suggestedQuestions.map((question) => (
                    <button
                      key={question}
                      type="button"
                      onClick={() => handleSendMessage(question)}
                      disabled={isSending}
                      className="flex w-full items-center justify-between gap-3 rounded-xl border border-white/[0.07] bg-[#0b1120] px-4 py-3 text-left text-sm text-slate-300 transition hover:border-emerald-400/30 hover:bg-emerald-400/5 hover:text-emerald-200 disabled:opacity-50"
                    >
                      <span>{question}</span>
                      <span className="text-emerald-400">↗</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Conversation messages */}
            {messages.map((message) => (
              <div
                key={message.id}
                className={`mb-5 flex ${message.role === "user"
                    ? "justify-end"
                    : "justify-start"
                  }`}
              >
                <div
                  className={`max-w-[90%] min-w-0 rounded-2xl p-4 sm:max-w-[85%] ${message.role === "user"
                      ? "rounded-br-sm border border-emerald-400/20 bg-emerald-400/10"
                      : "rounded-bl-sm border border-white/[0.07] bg-[#0b1120]"
                    }`}
                >
                  <div className="mb-2 flex items-center gap-2">
                    <span
                      className={`text-xs font-semibold ${message.role === "user"
                          ? "text-emerald-300"
                          : "text-slate-300"
                        }`}
                    >
                      {message.role === "user"
                        ? "You"
                        : "MediClarity AI"}
                    </span>
                  </div>

                  {message.role === "assistant" ? (
                    <div className="prose prose-invert prose-sm max-w-none break-words prose-headings:font-semibold prose-headings:text-white prose-p:leading-7 prose-p:text-slate-300 prose-strong:text-white prose-li:text-slate-300 prose-th:text-slate-200 prose-td:text-slate-300 prose-a:text-emerald-300">

                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          table: ({ children }) => (
                            <div className="my-4 w-full overflow-x-auto rounded-lg border border-white/10">
                              <table className="w-full min-w-[480px] border-collapse text-left text-sm">
                                {children}
                              </table>
                            </div>
                          ),

                          thead: ({ children }) => (
                            <thead className="bg-white/10 text-gray-100">
                              {children}
                            </thead>
                          ),

                          th: ({ children }) => (
                            <th className="border-b border-white/10 px-4 py-3 font-semibold">
                              {children}
                            </th>
                          ),

                          td: ({ children }) => (
                            <td className="border-b border-white/10 px-4 py-3 align-top leading-relaxed text-gray-300">
                              {children}
                            </td>
                          ),

                          h1: ({ children }) => (
                            <h1 className="mb-3 mt-5 text-xl font-bold text-white">
                              {children}
                            </h1>
                          ),

                          h2: ({ children }) => (
                            <h2 className="mb-2 mt-4 text-lg font-semibold text-white">
                              {children}
                            </h2>
                          ),

                          h3: ({ children }) => (
                            <h3 className="mb-2 mt-3 text-base font-semibold text-white">
                              {children}
                            </h3>
                          ),

                          p: ({ children }) => (
                            <p className="mb-3 break-words text-sm leading-7 text-gray-300">
                              {children}
                            </p>
                          ),

                          ul: ({ children }) => (
                            <ul className="mb-3 ml-5 list-disc space-y-2 text-sm leading-7 text-gray-300">
                              {children}
                            </ul>
                          ),

                          ol: ({ children }) => (
                            <ol className="mb-3 ml-5 list-decimal space-y-2 text-sm leading-7 text-gray-300">
                              {children}
                            </ol>
                          ),

                          li: ({ children }) => (
                            <li className="pl-1">{children}</li>
                          ),

                          strong: ({ children }) => (
                            <strong className="font-semibold text-white">
                              {children}
                            </strong>
                          ),

                          blockquote: ({ children }) => (
                            <blockquote className="my-3 border-l-2 border-emerald-500 pl-4 text-gray-400">
                              {children}
                            </blockquote>
                          ),

                          code: ({ children }) => (
                            <code className="rounded bg-white/10 px-1.5 py-0.5 text-emerald-300">
                              {children}
                            </code>
                          ),

                          hr: () => <hr className="my-4 border-white/10" />,
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>

                    </div>
                  ) : (
                    <p className="whitespace-pre-wrap break-words text-sm leading-7 text-slate-200">
                      {message.content}
                    </p>
                  )}

                  <p className="mt-3 text-right text-[10px] text-slate-600">
                    {new Date(message.created_at).toLocaleTimeString(
                      undefined,
                      {
                        hour: "numeric",
                        minute: "2-digit",
                      }
                    )}
                  </p>
                </div>
              </div>
            ))}

            {/* AI loading indicator */}
            {isSending && (
              <div className="mb-5 flex justify-start">
                <div className="rounded-2xl rounded-bl-sm border border-white/[0.07] bg-[#0b1120] px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 animate-bounce rounded-full bg-emerald-400" />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-emerald-400 [animation-delay:150ms]" />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-emerald-400 [animation-delay:300ms]" />
                    <span className="ml-1 text-xs text-slate-500">
                      Thinking...
                    </span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Error message */}
      {error && (
        <div
          role="alert"
          className="mx-4 mb-3 rounded-xl border border-red-400/20 bg-red-400/5 px-4 py-3 text-sm text-red-300 sm:mx-6"
        >
          {error}
        </div>
      )}

      {/* Input */}
      <form
        onSubmit={(event) => {
          event.preventDefault();
          handleSendMessage();
        }}
        className="border-t border-white/6 bg-[#0b1120] p-4 sm:p-5"
      >
        <div className="flex items-end gap-3 rounded-xl border border-white/10 bg-slate-900/60 p-2 transition focus-within:border-emerald-400/40">
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask something about your medical report..."
            rows={2}
            maxLength={4000}
            disabled={isLoading || isSending || isDeleting}
            className="max-h-32 min-h-12 flex-1 resize-none bg-transparent px-3 py-2 text-sm leading-6 text-white outline-none placeholder:text-slate-600 disabled:opacity-50"
          />

          <button
            type="submit"
            disabled={
              !input.trim() ||
              isSending ||
              isLoading ||
              isDeleting
            }
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-emerald-400 text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-40"
            aria-label="Send message"
          >
            {isSending ? (
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-950/30 border-t-slate-950" />
            ) : (
              <svg
                viewBox="0 0 24 24"
                fill="none"
                className="h-5 w-5"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="m22 2-7 20-4-9-9-4Z" />
                <path d="M22 2 11 13" />
              </svg>
            )}
          </button>
        </div>

        <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
          <p className="text-[11px] text-slate-600">
            Enter to send · Shift + Enter for a new line
          </p>

          <p className="text-[11px] text-slate-600">
            Educational information only · Not medical advice
          </p>
        </div>
      </form>
    </section>
  );
}