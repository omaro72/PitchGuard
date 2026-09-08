import type { ReactNode } from "react";

import type {
  ClaimStatus,
  ReviewDecision,
  ReviewResponse,
  RiskSeverity,
} from "@/lib/review-types";

const decisionStyles: Record<ReviewDecision | "ERROR", string> = {
  PASS: "border-emerald-300 bg-emerald-50 text-emerald-950 shadow-[inset_5px_0_0_0_#059669]",
  REVISE: "border-amber-300 bg-amber-50 text-amber-950 shadow-[inset_5px_0_0_0_#d97706]",
  BLOCK: "border-red-300 bg-red-50 text-red-950 shadow-[inset_5px_0_0_0_#dc2626]",
  ERROR: "border-slate-300 bg-slate-100 text-slate-900 shadow-[inset_5px_0_0_0_#64748b]",
};

const claimStyles: Record<ClaimStatus, string> = {
  SUPPORTED: "bg-emerald-100 text-emerald-800",
  UNSUPPORTED: "bg-amber-100 text-amber-900",
  CONTRADICTED: "bg-red-100 text-red-800",
  UNCLEAR: "bg-slate-200 text-slate-800",
};

const severityStyles: Record<RiskSeverity, string> = {
  LOW: "bg-slate-200 text-slate-800",
  MEDIUM: "bg-amber-100 text-amber-900",
  HIGH: "bg-orange-100 text-orange-900",
  CRITICAL: "bg-red-100 text-red-800",
};

interface ReviewReportProps {
  response: ReviewResponse;
  isSubmitting: boolean;
  onRetry: () => void;
}

interface ReportSectionProps {
  eyebrow: string;
  title: string;
  children: ReactNode;
}

interface TextListProps {
  items: string[];
  emptyText: string;
}

function readableLabel(value: string): string {
  return value
    .toLowerCase()
    .replaceAll("_", " ")
    .replace(/(^|\s)\S/g, (letter) => letter.toUpperCase());
}

function Badge({ children, className }: { children: ReactNode; className: string }) {
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-[0.68rem] font-bold tracking-wide ${className}`}
    >
      {children}
    </span>
  );
}

function ReportSection({ eyebrow, title, children }: ReportSectionProps) {
  return (
    <section className="rounded-[1.5rem] border border-slate-200 bg-white p-5 shadow-[0_20px_55px_-48px_rgba(15,23,42,0.7)] sm:p-7">
      <p className="text-[0.68rem] font-bold uppercase tracking-[0.2em] text-teal-700">
        {eyebrow}
      </p>
      <h3 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">
        {title}
      </h3>
      <div className="mt-6">{children}</div>
    </section>
  );
}

function TextList({ items, emptyText }: TextListProps) {
  if (items.length === 0) {
    return <p className="text-sm text-slate-500">{emptyText}</p>;
  }

  return (
    <ul className="space-y-2 text-sm leading-6 text-slate-700">
      {items.map((item, index) => (
        <li className="flex gap-2" key={`${item}-${index}`}>
          <span aria-hidden="true" className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-teal-600" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

function MissingContext({ items }: { items: string[] }) {
  return (
    <div className="mt-6 rounded-xl border border-dashed border-slate-200 bg-slate-50/70 p-4">
      <h4 className="text-sm font-semibold text-slate-900">Missing context</h4>
      <div className="mt-2">
        <TextList items={items} emptyText="No missing context reported." />
      </div>
    </div>
  );
}

function Score({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <div className="flex items-baseline justify-between gap-4">
        <span className="text-xs font-bold uppercase tracking-[0.12em] text-slate-600">{label}</span>
        <span className="text-2xl font-bold tracking-tight text-slate-950">{value}/100</span>
      </div>
      <meter
        aria-label={`${label}: ${value} out of 100`}
        className="mt-4 h-2 w-full accent-teal-700"
        max={100}
        min={0}
        value={value}
      />
    </div>
  );
}

export function ReviewReport({ response, isSubmitting, onRetry }: ReviewReportProps) {
  const reportStatus =
    response.analysis_status === "ERROR" || response.decision === null
      ? "ERROR"
      : response.decision;

  return (
    <div className="space-y-5">
      <section
        aria-live="polite"
        className={`rounded-[1.5rem] border p-6 sm:p-8 ${decisionStyles[reportStatus]}`}
        role={reportStatus === "ERROR" ? "alert" : "status"}
      >
        <p className="text-[0.68rem] font-bold uppercase tracking-[0.2em]">Review decision</p>
        <div className="mt-3 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-4xl font-semibold tracking-tight">{reportStatus}</h2>
          {reportStatus === "ERROR" ? (
            <button
              className="w-full rounded-xl border border-slate-400 bg-white px-4 py-2.5 text-sm font-semibold text-slate-900 transition-colors hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-800 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
              disabled={isSubmitting}
              onClick={onRetry}
              type="button"
            >
              {isSubmitting ? "Retrying…" : "Retry review"}
            </button>
          ) : null}
        </div>
        <p className="mt-3 max-w-3xl text-sm leading-6">
          {reportStatus === "ERROR"
            ? "The review did not complete, so PitchGuard did not assign a final decision. Successful reviewer results are preserved below."
            : "This decision was calculated by application rules from the completed reviewer results. A human must review the findings before using the pitch."}
        </p>
      </section>

      <ReportSection eyebrow="Decision" title="Reasons">
        <TextList
          items={response.decision_reasons}
          emptyText={
            reportStatus === "ERROR"
              ? "No decision reasons are available because the review did not complete."
              : "No additional decision reasons were returned."
          }
        />
      </ReportSection>

      <ReportSection eyebrow="Reviewer 1" title="Claim and Evidence review">
        {response.evidence_review ? (
          <>
            <p className="text-sm leading-6 text-slate-700">
              {response.evidence_review.summary}
            </p>
            <div className="mt-5 space-y-4">
              {response.evidence_review.claims.length === 0 ? (
                <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">
                  No factual or measurable claims were reported.
                </p>
              ) : (
                response.evidence_review.claims.map((claim, index) => (
                  <article
                    className="rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:p-5"
                    key={`${claim.claim_text}-${index}`}
                  >
                    <div className="flex flex-wrap gap-2">
                      <Badge className={claimStyles[claim.status]}>{claim.status}</Badge>
                      <Badge className="bg-teal-100 text-teal-900">
                        {readableLabel(claim.claim_type)}
                      </Badge>
                      <Badge className="bg-slate-200 text-slate-800">
                        {readableLabel(claim.importance)} importance
                      </Badge>
                    </div>
                    <h4 className="mt-3 font-semibold leading-6 text-slate-950">
                      {claim.claim_text}
                    </h4>
                    <p className="mt-2 text-sm leading-6 text-slate-700">
                      {claim.explanation}
                    </p>
                    <div className="mt-3 text-sm text-slate-600">
                      <span className="font-semibold text-slate-800">Evidence IDs: </span>
                      {claim.evidence_ids.length > 0
                        ? claim.evidence_ids.join(", ")
                        : "None referenced"}
                    </div>
                  </article>
                ))
              )}
            </div>
            <MissingContext items={response.evidence_review.missing_context} />
          </>
        ) : (
          <p className="text-sm text-slate-500">
            The Claim and Evidence reviewer did not return a usable result.
          </p>
        )}
      </ReportSection>

      <ReportSection eyebrow="Reviewer 2" title="Journalist Relevance review">
        {response.relevance_review ? (
          <>
            <div className="grid gap-3 sm:grid-cols-2">
              <Score label="Relevance" value={response.relevance_review.relevance_score} />
              <Score
                label="Personalization"
                value={response.relevance_review.personalization_score}
              />
            </div>
            <p className="mt-5 text-sm leading-6 text-slate-700">
              {response.relevance_review.summary}
            </p>
            <div className="mt-5 grid gap-5 sm:grid-cols-2">
              <div>
                <h4 className="text-sm font-semibold text-slate-900">Matched topics</h4>
                <div className="mt-2">
                  <TextList
                    items={response.relevance_review.matched_topics}
                    emptyText="No matched topics reported."
                  />
                </div>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-slate-900">Mismatches</h4>
                <div className="mt-2">
                  <TextList
                    items={response.relevance_review.mismatches}
                    emptyText="No mismatches reported."
                  />
                </div>
              </div>
            </div>
            <MissingContext items={response.relevance_review.missing_context} />
          </>
        ) : (
          <p className="text-sm text-slate-500">
            The Journalist Relevance reviewer did not return a usable result.
          </p>
        )}
      </ReportSection>

      <ReportSection eyebrow="Reviewer 3" title="PR Risk review">
        {response.risk_review ? (
          <>
            <p className="text-sm leading-6 text-slate-700">
              {response.risk_review.summary}
            </p>
            <div className="mt-5 space-y-4">
              {response.risk_review.findings.length === 0 ? (
                <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">
                  No PR risk findings were reported.
                </p>
              ) : (
                response.risk_review.findings.map((finding, index) => (
                  <article
                    className="rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:p-5"
                    key={`${finding.category}-${index}`}
                  >
                    <div className="flex flex-wrap gap-2">
                      <Badge className={severityStyles[finding.severity]}>
                        {finding.severity}
                      </Badge>
                      <Badge className="bg-teal-100 text-teal-900">
                        {readableLabel(finding.category)}
                      </Badge>
                    </div>
                    {finding.pitch_excerpt ? (
                      <blockquote className="mt-3 border-l-2 border-slate-300 pl-3 text-sm italic leading-6 text-slate-600">
                        “{finding.pitch_excerpt}”
                      </blockquote>
                    ) : null}
                    <p className="mt-3 text-sm leading-6 text-slate-700">
                      {finding.explanation}
                    </p>
                    <p className="mt-3 text-sm leading-6 text-slate-700">
                      <span className="font-semibold text-slate-900">Recommendation: </span>
                      {finding.recommendation}
                    </p>
                  </article>
                ))
              )}
            </div>
            <MissingContext items={response.risk_review.missing_context} />
          </>
        ) : (
          <p className="text-sm text-slate-500">
            The PR Risk reviewer did not return a usable result.
          </p>
        )}
      </ReportSection>

      {response.errors.length > 0 ? (
        <ReportSection eyebrow="Incomplete analysis" title="Reviewer errors">
          <ul className="space-y-3">
            {response.errors.map((error) => (
              <li
                className="rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:p-5"
                key={`${error.reviewer}-${error.code}`}
              >
                <div className="flex flex-wrap items-center gap-2">
                  <Badge className="bg-slate-200 text-slate-800">{error.reviewer}</Badge>
                  <span className="break-all font-mono text-xs font-medium text-slate-500">{error.code}</span>
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-700">{error.message}</p>
                <p className="mt-2 text-xs font-medium text-slate-500">
                  {error.retryable ? "This reviewer may succeed on retry." : "Manual review is required."}
                </p>
              </li>
            ))}
          </ul>
        </ReportSection>
      ) : null}
    </div>
  );
}
