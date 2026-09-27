
"use client";

import type {
  MedicalExplanation,
  ClinicalContextExplanation,
} from "@/services/reportService";

interface MedicalExplanationSectionProps {
  explanation: MedicalExplanation | null;
  loading: boolean;
  error: string;
}

const panel =
  "rounded-2xl border border-white/[0.07] bg-slate-900/60";

function formatCategory(category: string) {
  return category
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase()
    );
}

function confidenceStyle(confidence: string) {
  const styles: Record<string, string> = {
    high: "border-emerald-400/20 bg-emerald-400/10 text-emerald-300",
    medium: "border-amber-400/20 bg-amber-400/10 text-amber-300",
    low: "border-slate-500/20 bg-slate-500/10 text-slate-400",
  };

  return (
    styles[confidence.toLowerCase()] ?? styles.low
  );
}

function SectionHeading({
  eyebrow,
  title,
  description,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
}) {
  return (
    <div>
      {eyebrow && (
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
          {eyebrow}
        </p>
      )}

      <h3 className="text-lg font-semibold tracking-tight text-white sm:text-xl">
        {title}
      </h3>

      {description && (
        <p className="mt-2 text-sm leading-6 text-slate-400">
          {description}
        </p>
      )}
    </div>
  );
}

function SourceText({
  text,
}: {
  text: string | null;
}) {
  if (!text) return null;

  return (
    <details className="group mt-5 border-t border-white/6 pt-4">
      <summary className="cursor-pointer list-none text-xs font-medium text-emerald-300 transition hover:text-emerald-200">
        <span className="flex items-center justify-between gap-3">
          View original report text
          <span className="text-slate-500 transition group-open:rotate-180">
            ▾
          </span>
        </span>
      </summary>

      <p className="mt-3 whitespace-pre-wrap wrap-break-word rounded-xl border border-white/6 bg-[#080d18] p-4 text-sm leading-6 text-slate-400">
        {text}
      </p>
    </details>
  );
}

function ContextCard({
  item,
}: {
  item: ClinicalContextExplanation;
}) {
  return (
    <article className="rounded-xl border border-white/[0.07] bg-[#0b1120] p-5 transition hover:border-emerald-400/20">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <span className="rounded-full border border-emerald-400/20 bg-emerald-400/6 px-3 py-1 text-xs font-medium text-emerald-300">
          {formatCategory(item.category)}
        </span>

        <span
          className={`rounded-full border px-2.5 py-1 text-xs font-medium ${confidenceStyle(item.confidence)}`}
        >
          {item.confidence} confidence
        </span>
      </div>

      <h4 className="mt-4 font-semibold leading-6 text-white">
        {item.item}
      </h4>

      <p className="mt-2 text-sm leading-7 text-slate-400">
        {item.explanation}
      </p>

      <SourceText text={item.source_text} />
    </article>
  );
}

export default function MedicalExplanationSection({
  explanation,
  loading,
  error,
}: MedicalExplanationSectionProps) {
  if (loading) {
    return (
      <section className={`${panel} mt-8 p-6 sm:p-8`}>
        <SectionHeading
          eyebrow="AI-assisted analysis"
          title="Medical Report Explanation"
          description="Preparing the plain-language explanation of your report."
        />

        <div className="mt-6 flex items-center gap-3 rounded-xl border border-white/6 bg-[#0b1120] p-5">
          <span className="h-5 w-5 animate-spin rounded-full border-2 border-emerald-400/20 border-t-emerald-400" />

          <p className="text-sm text-slate-400">
            Loading medical explanation...
          </p>
        </div>
      </section>
    );
  }


if (error || !explanation) {
  return (
    <section className={`${panel} mt-8 overflow-hidden`}>
      {/* Section heading */}
      <div className="border-b border-white/6 px-6 py-5 sm:px-8">
        <SectionHeading
          eyebrow="AI-assisted analysis"
          title="Medical Report Explanation"
        />
      </div>

      {/* Empty state */}
      <div className="flex flex-col items-center px-6 py-10 text-center sm:py-12">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-emerald-400/15 bg-emerald-400/6">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            className="h-7 w-7 text-emerald-400"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 3v3m0 12v3M3 12h3m12 0h3" />
            <path d="M8 8l-2-2m10 10 2 2m0-12-2 2M8 16l-2 2" />
            <circle cx="12" cy="12" r="5" />
          </svg>
        </div>

        <h3 className="mt-5 text-base font-semibold text-white">
          Explanation not available yet
        </h3>

        <p className="mt-2 max-w-md text-sm leading-6 text-slate-400">
          An AI-generated explanation has not been
          generated for this report. Your uploaded
          document and extracted medical information
          are still available above.
        </p>

        <span className="mt-5 inline-flex items-center gap-2 rounded-full border border-slate-700/60 bg-slate-800/40 px-3 py-1.5 text-xs text-slate-500">
          <span className="h-1.5 w-1.5 rounded-full bg-slate-500" />
          Explanation unavailable
        </span>
      </div>
    </section>
  );
}


  return (
    <section className="mt-8 space-y-6">
      {/* Report Summary */}
      <article className="overflow-hidden rounded-2xl border border-emerald-400/15 bg-slate-900/60">
        <div className="border-b border-white/6 p-6 sm:p-8">
          <div className="flex items-start gap-4">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-emerald-400/15 bg-emerald-400/8 text-xl text-emerald-300">
              ✦
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">
                AI-assisted analysis
              </p>

              <h2 className="mt-2 text-xl font-semibold tracking-tight text-white sm:text-2xl">
                Medical Report Explanation
              </h2>

              <p className="mt-2 text-sm leading-6 text-slate-400">
                A plain-language guide to the information
                documented in your report.
              </p>
            </div>
          </div>
        </div>

        <div className="p-6 sm:p-8">
          <div className="rounded-xl border border-white/6 bg-[#0b1120] p-5 sm:p-6">
            <div className="mb-4 flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              <h3 className="text-sm font-semibold text-emerald-300">
                Report Summary
              </h3>
            </div>

            <p className="whitespace-pre-wrap text-sm leading-7 text-slate-300">
              {explanation.report_summary}
            </p>
          </div>
        </div>
      </article>

      {/* Parameter Explanations */}
      <article className={`${panel} p-6 sm:p-8`}>
        <SectionHeading
          eyebrow="Understanding your results"
          title="Test Results Explained"
          description="What each reported parameter measures and how the recorded result is described in the report."
        />

        {explanation.parameter_explanations.length > 0 ? (
          <div className="mt-6 space-y-4">
            {explanation.parameter_explanations.map(
              (parameter, index) => (
                <article
                  key={`${parameter.parameter_name}-${index}`}
                  className="overflow-hidden rounded-xl border border-white/[0.07] bg-[#0b1120]"
                >
                  {/* Parameter Header */}
                  <div className="flex flex-col justify-between gap-3 border-b border-white/6 p-5 sm:flex-row sm:items-start sm:p-6">
                    <div className="min-w-0">
                      <h4 className="text-lg font-semibold text-white">
                        {parameter.parameter_name}
                      </h4>

                      <p className="mt-2 text-sm font-medium leading-6 text-emerald-300">
                        {parameter.result_summary}
                      </p>
                    </div>

                    <span
                      className={`w-fit shrink-0 rounded-full border px-3 py-1 text-xs font-medium ${confidenceStyle(parameter.confidence)}`}
                    >
                      {parameter.confidence} confidence
                    </span>
                  </div>

                  {/* Explanation Content */}
                  <div className="space-y-5 p-5 sm:p-6">
                    <div>
                      <h5 className="text-sm font-semibold text-slate-200">
                        What it measures
                      </h5>

                      <p className="mt-2 text-sm leading-7 text-slate-400">
                        {parameter.what_it_measures}
                      </p>
                    </div>

                    <div className="border-t border-white/6 pt-5">
                      <h5 className="text-sm font-semibold text-slate-200">
                        What your result means
                      </h5>

                      <p className="mt-2 text-sm leading-7 text-slate-400">
                        {parameter.what_your_result_means}
                      </p>
                    </div>

                    <div className="border-t border-white/6 pt-5">
                      <h5 className="text-sm font-semibold text-slate-200">
                        Why it matters
                      </h5>

                      <p className="mt-2 text-sm leading-7 text-slate-400">
                        {parameter.why_it_matters}
                      </p>
                    </div>

                    {parameter.limitations.length > 0 && (
                      <div className="rounded-xl border border-amber-400/15 bg-amber-400/4 p-4">
                        <h5 className="text-sm font-semibold text-amber-300">
                          Limitations
                        </h5>

                        <ul className="mt-3 space-y-2">
                          {parameter.limitations.map(
                            (limitation, limitationIndex) => (
                              <li
                                key={limitationIndex}
                                className="flex items-start gap-3 text-sm leading-6 text-slate-400"
                              >
                                <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-400" />
                                {limitation}
                              </li>
                            )
                          )}
                        </ul>
                      </div>
                    )}

                    <SourceText
                      text={parameter.source_text}
                    />
                  </div>
                </article>
              )
            )}
          </div>
        ) : (
          <p className="mt-5 rounded-xl bg-[#0b1120] p-5 text-sm text-slate-500">
            No parameter explanations are available.
          </p>
        )}
      </article>

      {/* Clinical Context */}
      <article className={`${panel} p-6 sm:p-8`}>
        <SectionHeading
          eyebrow="Additional information"
          title="Clinical Context"
          description="Plain-language explanations of medical history, symptoms, medications, and findings documented in the report."
        />

        {explanation.clinical_context_explanations.length > 0 ? (
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            {explanation.clinical_context_explanations.map(
              (item, index) => (
                <ContextCard
                  key={`${item.category}-${index}`}
                  item={item}
                />
              )
            )}
          </div>
        ) : (
          <p className="mt-5 rounded-xl bg-[#0b1120] p-5 text-sm text-slate-500">
            No clinical context explanations are available.
          </p>
        )}
      </article>

      {/* Important Observations */}
      <article className={`${panel} p-6 sm:p-8`}>
        <SectionHeading
          eyebrow="Key points"
          title="Important Observations"
          description="Observations identified from the information documented in the report."
        />

        {explanation.important_observations.length > 0 ? (
          <ul className="mt-5 space-y-3">
            {explanation.important_observations.map(
              (observation, index) => (
                <li
                  key={index}
                  className="flex items-start gap-3 rounded-xl border border-white/5 bg-[#0b1120] p-4 text-sm leading-6 text-slate-300"
                >
                  <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400" />
                  <span>{observation}</span>
                </li>
              )
            )}
          </ul>
        ) : (
          <p className="mt-5 text-sm text-slate-500">
            No additional observations are available.
          </p>
        )}

        {explanation.limitations.length > 0 && (
          <div className="mt-6 rounded-xl border border-amber-400/15 bg-amber-400/4 p-5">
            <h4 className="font-semibold text-amber-300">
              General Limitations
            </h4>

            <ul className="mt-3 space-y-2">
              {explanation.limitations.map(
                (limitation, index) => (
                  <li
                    key={index}
                    className="flex items-start gap-3 text-sm leading-6 text-slate-400"
                  >
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-400" />
                    {limitation}
                  </li>
                )
              )}
            </ul>
          </div>
        )}
      </article>

      {/* Medical Disclaimer */}
      <aside className="rounded-2xl border border-amber-400/15 bg-amber-400/4 p-5 sm:p-6">
        <div className="flex items-start gap-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-amber-400/15 bg-amber-400/[0.07] text-lg text-amber-300">
            ⓘ
          </div>

          <div>
            <h4 className="font-semibold text-amber-300">
              Important Medical Disclaimer
            </h4>

            <p className="mt-3 text-sm leading-7 text-slate-300">
              {explanation.disclaimer}
            </p>

            <p className="mt-3 text-xs leading-6 text-slate-500">
              This application provides educational
              information only. Always consult a qualified
              healthcare professional for diagnosis and
              treatment decisions.
            </p>
          </div>
        </div>
      </aside>
    </section>
  );
}
