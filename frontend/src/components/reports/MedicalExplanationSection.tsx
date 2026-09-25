
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

function formatCategory(category: string) {
  return category
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase()
    );
}

function formatConfidence(confidence: string) {
  return confidence.charAt(0).toUpperCase()
    + confidence.slice(1);
}

function ContextCard({
  item,
}: {
  item: ClinicalContextExplanation;
}) {
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900/70 p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400">
          {formatCategory(item.category)}
        </span>

        <span className="text-xs text-slate-500">
          Confidence: {formatConfidence(item.confidence)}
        </span>
      </div>

      <h4 className="mt-3 font-semibold text-white">
        {item.item}
      </h4>

      <p className="mt-2 text-sm leading-6 text-slate-300">
        {item.explanation}
      </p>

      {item.source_text && (
        <details className="mt-4">
          <summary className="cursor-pointer text-xs text-emerald-400 hover:text-emerald-300">
            View source from report
          </summary>

          <p className="mt-2 rounded-lg bg-slate-950 p-3 text-sm text-slate-400">
            {item.source_text}
          </p>
        </details>
      )}
    </div>
  );
}

export default function MedicalExplanationSection({
  explanation,
  loading,
  error,
}: MedicalExplanationSectionProps) {
  if (loading) {
    return (
      <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="text-xl font-semibold">
          Medical Report Explanation
        </h2>

        <p className="mt-4 animate-pulse text-sm text-slate-400">
          Generating your explanation...
        </p>
      </section>
    );
  }

  if (error || !explanation) {
    return (
      <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="text-xl font-semibold">
          Medical Report Explanation
        </h2>

        <p className="mt-4 text-sm text-slate-400">
          {error || "No explanation is available for this report."}
        </p>

        <p className="mt-2 text-xs text-slate-500">
          Your extracted text and structured parameters
          remain available above.
        </p>
      </section>
    );
  }

  return (
    <section className="mt-8 space-y-6">

      {/* Report Summary */}

      <div className="rounded-2xl border border-emerald-500/20 bg-slate-900 p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400">
            <span className="text-xl">✦</span>
          </div>

          <div>
            <h2 className="text-xl font-bold">
              Medical Report Explanation
            </h2>

            <p className="mt-1 text-sm text-slate-400">
              A plain-language explanation of your report
            </p>
          </div>
        </div>

        <div className="mt-5 rounded-xl bg-slate-950/70 p-5">
          <h3 className="font-semibold text-emerald-400">
            Report Summary
          </h3>

          <p className="mt-3 text-sm leading-7 text-slate-300">
            {explanation.report_summary}
          </p>
        </div>
      </div>

      {/* Parameter Explanations */}

      <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h3 className="text-xl font-semibold">
          Test Results Explained
        </h3>

        <p className="mt-2 text-sm text-slate-400">
          Understand what each reported parameter measures
          and what the recorded result means.
        </p>

        {explanation.parameter_explanations.length > 0 ? (
          <div className="mt-5 space-y-4">
            {explanation.parameter_explanations.map(
              (parameter, index) => (
                <div
                  key={`${parameter.parameter_name}-${index}`}
                  className="rounded-xl border border-slate-700 bg-slate-950/60 p-5"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h4 className="text-lg font-semibold">
                        {parameter.parameter_name}
                      </h4>

                      <p className="mt-1 text-sm text-emerald-400">
                        {parameter.result_summary}
                      </p>
                    </div>

                    <span className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-400">
                      {formatConfidence(parameter.confidence)} confidence
                    </span>
                  </div>

                  <div className="mt-5 space-y-4">
                    <div>
                      <h5 className="text-sm font-semibold text-slate-200">
                        What it measures
                      </h5>

                      <p className="mt-1 text-sm leading-6 text-slate-400">
                        {parameter.what_it_measures}
                      </p>
                    </div>

                    <div>
                      <h5 className="text-sm font-semibold text-slate-200">
                        What your result means
                      </h5>

                      <p className="mt-1 text-sm leading-6 text-slate-400">
                        {parameter.what_your_result_means}
                      </p>
                    </div>

                    <div>
                      <h5 className="text-sm font-semibold text-slate-200">
                        Why it matters
                      </h5>

                      <p className="mt-1 text-sm leading-6 text-slate-400">
                        {parameter.why_it_matters}
                      </p>
                    </div>
                  </div>

                  {parameter.limitations.length > 0 && (
                    <div className="mt-5 rounded-lg border border-amber-500/20 bg-amber-500/5 p-4">
                      <h5 className="text-sm font-semibold text-amber-400">
                        Limitations
                      </h5>

                      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-400">
                        {parameter.limitations.map(
                          (limitation, limitationIndex) => (
                            <li key={limitationIndex}>
                              {limitation}
                            </li>
                          )
                        )}
                      </ul>
                    </div>
                  )}

                  {parameter.source_text && (
                    <details className="mt-4">
                      <summary className="cursor-pointer text-xs text-emerald-400 hover:text-emerald-300">
                        View original report text
                      </summary>

                      <p className="mt-2 rounded-lg bg-slate-900 p-3 text-sm text-slate-400">
                        {parameter.source_text}
                      </p>
                    </details>
                  )}
                </div>
              )
            )}
          </div>
        ) : (
          <p className="mt-4 text-sm text-slate-500">
            No parameter explanations are available.
          </p>
        )}
      </div>

      {/* Clinical Context */}

      <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h3 className="text-xl font-semibold">
          Clinical Context
        </h3>

        <p className="mt-2 text-sm text-slate-400">
          Plain-language explanations of the medical history,
          symptoms, medications, and findings documented
          in the report.
        </p>

        {explanation.clinical_context_explanations.length > 0 ? (
          <div className="mt-5 grid gap-4 md:grid-cols-2">
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
          <p className="mt-4 text-sm text-slate-500">
            No clinical context explanations are available.
          </p>
        )}
      </div>

      {/* Important Observations */}

      <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h3 className="text-xl font-semibold">
          Important Observations
        </h3>

        {explanation.important_observations.length > 0 ? (
          <ul className="mt-4 space-y-3">
            {explanation.important_observations.map(
              (observation, index) => (
                <li
                  key={index}
                  className="flex items-start gap-3 text-sm leading-6 text-slate-300"
                >
                  <span className="mt-1 text-emerald-400">
                    •
                  </span>

                  <span>{observation}</span>
                </li>
              )
            )}
          </ul>
        ) : (
          <p className="mt-3 text-sm text-slate-500">
            No additional observations are available.
          </p>
        )}

        {explanation.limitations.length > 0 && (
          <div className="mt-6 border-t border-slate-800 pt-5">
            <h4 className="font-semibold text-amber-400">
              General Limitations
            </h4>

            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-400">
              {explanation.limitations.map(
                (limitation, index) => (
                  <li key={index}>{limitation}</li>
                )
              )}
            </ul>
          </div>
        )}
      </div>

      {/* Disclaimer */}

      <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-5">
        <div className="flex items-start gap-3">
          <span className="text-lg text-amber-400">ⓘ</span>

          <div>
            <h4 className="font-semibold text-amber-400">
              Important Medical Disclaimer
            </h4>

            <p className="mt-2 text-sm leading-6 text-slate-300">
              {explanation.disclaimer}
            </p>

            <p className="mt-2 text-xs leading-5 text-slate-500">
              Always consult a qualified healthcare professional
              for diagnosis and treatment decisions.
            </p>
          </div>
        </div>
      </div>

    </section>
  );
}
