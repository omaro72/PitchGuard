"use client";

import type { FormEvent, ReactNode } from "react";
import { useEffect, useRef, useState } from "react";

import { ReviewReport } from "@/components/review-report";
import { submitReview } from "@/lib/review-api";
import type {
  CoverageItem,
  EvidenceItem,
  ReviewRequest,
  ReviewResponse,
} from "@/lib/review-types";

const inputClassName =
  "mt-2 w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 shadow-sm outline-none placeholder:text-slate-400 focus:border-cyan-700 focus:ring-2 focus:ring-cyan-100";
const textareaClassName = `${inputClassName} resize-y leading-6`;
const secondaryButtonClassName =
  "rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-sm font-semibold text-slate-700 shadow-sm hover:border-slate-400 hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-700 disabled:cursor-not-allowed disabled:opacity-50";

const initialRequest: ReviewRequest = {
  campaign: {
    company_name: "",
    announcement: "",
    target_audience: "",
  },
  evidence: [],
  journalist: {
    name: "",
    publication: "",
    beat: "",
    recent_coverage: [],
  },
  pitch: "",
};

interface PitchReviewWorkspaceProps {
  apiBaseUrl: string;
}

interface FormSectionProps {
  number: string;
  title: string;
  description: string;
  action?: ReactNode;
  children: ReactNode;
}

interface RequestFailure {
  title: string;
  message: string;
}

function FormSection({ number, title, description, action, children }: FormSectionProps) {
  return (
    <section className="border-b border-slate-200 px-5 py-7 last:border-b-0 sm:px-7">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-cyan-700">
            {number}
          </p>
          <h2 className="mt-1 text-xl font-semibold tracking-tight text-slate-950">
            {title}
          </h2>
          <p className="mt-1 max-w-xl text-sm leading-6 text-slate-600">{description}</p>
        </div>
        {action}
      </div>
      <div className="mt-6">{children}</div>
    </section>
  );
}

function normalizedRequest(reviewRequest: ReviewRequest): ReviewRequest {
  return {
    campaign: {
      company_name: reviewRequest.campaign.company_name.trim(),
      announcement: reviewRequest.campaign.announcement.trim(),
      target_audience: reviewRequest.campaign.target_audience.trim(),
    },
    evidence: reviewRequest.evidence.map((item) => ({
      id: item.id,
      source: item.source.trim(),
      content: item.content.trim(),
      confidential: item.confidential,
    })),
    journalist: {
      name: reviewRequest.journalist.name.trim(),
      publication: reviewRequest.journalist.publication.trim(),
      beat: reviewRequest.journalist.beat.trim(),
      recent_coverage: reviewRequest.journalist.recent_coverage.map((item) => ({
        id: item.id,
        title: item.title.trim(),
        summary: item.summary.trim(),
        publication_date: item.publication_date,
        url: item.url?.trim() || null,
      })),
    },
    pitch: reviewRequest.pitch.trim(),
  };
}

export function PitchReviewWorkspace({ apiBaseUrl }: PitchReviewWorkspaceProps) {
  const [reviewRequest, setReviewRequest] = useState<ReviewRequest>(initialRequest);
  const [reviewResponse, setReviewResponse] = useState<ReviewResponse | null>(null);
  const [requestFailure, setRequestFailure] = useState<RequestFailure | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const nextEvidenceId = useRef(1);
  const nextCoverageId = useRef(1);
  const formRef = useRef<HTMLFormElement>(null);
  const resultsRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (reviewResponse || requestFailure) {
      resultsRef.current?.focus();
      resultsRef.current?.scrollIntoView({ block: "start" });
    }
  }, [reviewResponse, requestFailure]);

  function addEvidence() {
    if (reviewRequest.evidence.length >= 10) {
      return;
    }
    const item: EvidenceItem = {
      id: `E${nextEvidenceId.current}`,
      source: "",
      content: "",
      confidential: false,
    };
    nextEvidenceId.current += 1;
    setReviewRequest((current) => ({
      ...current,
      evidence: [...current.evidence, item],
    }));
  }

  function updateEvidence(index: number, values: Partial<Omit<EvidenceItem, "id">>) {
    setReviewRequest((current) => ({
      ...current,
      evidence: current.evidence.map((item, itemIndex) =>
        itemIndex === index ? { ...item, ...values } : item,
      ),
    }));
  }

  function removeEvidence(index: number) {
    setReviewRequest((current) => ({
      ...current,
      evidence: current.evidence.filter((_, itemIndex) => itemIndex !== index),
    }));
  }

  function addCoverage() {
    if (reviewRequest.journalist.recent_coverage.length >= 10) {
      return;
    }
    const item: CoverageItem = {
      id: `C${nextCoverageId.current}`,
      title: "",
      summary: "",
      publication_date: null,
      url: null,
    };
    nextCoverageId.current += 1;
    setReviewRequest((current) => ({
      ...current,
      journalist: {
        ...current.journalist,
        recent_coverage: [...current.journalist.recent_coverage, item],
      },
    }));
  }

  function updateCoverage(index: number, values: Partial<Omit<CoverageItem, "id">>) {
    setReviewRequest((current) => ({
      ...current,
      journalist: {
        ...current.journalist,
        recent_coverage: current.journalist.recent_coverage.map((item, itemIndex) =>
          itemIndex === index ? { ...item, ...values } : item,
        ),
      },
    }));
  }

  function removeCoverage(index: number) {
    setReviewRequest((current) => ({
      ...current,
      journalist: {
        ...current.journalist,
        recent_coverage: current.journalist.recent_coverage.filter(
          (_, itemIndex) => itemIndex !== index,
        ),
      },
    }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    setReviewResponse(null);
    setRequestFailure(null);

    const result = await submitReview(apiBaseUrl, normalizedRequest(reviewRequest));

    if (result.kind === "review") {
      setReviewResponse(result.response);
    } else {
      setRequestFailure({
        title: result.kind === "validation_error" ? "Check the form" : "Review unavailable",
        message: result.message,
      });
    }
    setIsSubmitting(false);
  }

  function retryReview() {
    formRef.current?.requestSubmit();
  }

  return (
    <div className="grid items-start gap-8 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
      <form
        className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
        id="pitch-review-form"
        onSubmit={handleSubmit}
        ref={formRef}
      >
        <FormSection
          description="Describe the organization and the news you want the journalist to consider."
          number="Step 1"
          title="Campaign"
        >
          <div className="grid gap-5 sm:grid-cols-2">
            <label className="block text-sm font-semibold text-slate-800">
              Company name
              <input
                autoComplete="organization"
                className={inputClassName}
                maxLength={120}
                onChange={(event) =>
                  setReviewRequest((current) => ({
                    ...current,
                    campaign: { ...current.campaign, company_name: event.target.value },
                  }))
                }
                placeholder="Example Labs"
                required
                value={reviewRequest.campaign.company_name}
              />
            </label>
            <label className="block text-sm font-semibold text-slate-800">
              Target audience
              <input
                className={inputClassName}
                maxLength={500}
                onChange={(event) =>
                  setReviewRequest((current) => ({
                    ...current,
                    campaign: { ...current.campaign, target_audience: event.target.value },
                  }))
                }
                placeholder="Who should care about this news?"
                required
                value={reviewRequest.campaign.target_audience}
              />
            </label>
          </div>
          <label className="mt-5 block text-sm font-semibold text-slate-800">
            Announcement
            <textarea
              className={`${textareaClassName} min-h-28`}
              maxLength={2000}
              minLength={20}
              onChange={(event) =>
                setReviewRequest((current) => ({
                  ...current,
                  campaign: { ...current.campaign, announcement: event.target.value },
                }))
              }
              placeholder="Explain the announcement, why it matters, and the intended angle."
              required
              value={reviewRequest.campaign.announcement}
            />
          </label>
        </FormSection>

        <FormSection
          action={
            <button
              className={secondaryButtonClassName}
              disabled={reviewRequest.evidence.length >= 10}
              onClick={addEvidence}
              type="button"
            >
              Add evidence
            </button>
          }
          description="Add only facts that the reviewers may use to assess campaign claims. This section can be empty."
          number="Step 2"
          title="Supporting evidence"
        >
          {reviewRequest.evidence.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-5 text-sm leading-6 text-slate-600">
              No evidence added. Claims without supplied support may be marked unsupported or unclear.
            </div>
          ) : (
            <div className="space-y-5">
              {reviewRequest.evidence.map((item, index) => (
                <fieldset
                  className="rounded-xl border border-slate-200 bg-slate-50 p-4 sm:p-5"
                  key={item.id}
                >
                  <legend className="px-1 font-semibold text-slate-950">
                    Evidence {item.id}
                  </legend>
                  <button
                    aria-label={`Remove evidence ${item.id}`}
                    className="float-right -mt-7 text-sm font-semibold text-red-700 hover:text-red-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-700"
                    onClick={() => removeEvidence(index)}
                    type="button"
                  >
                    Remove
                  </button>
                  <div className="mt-4 grid gap-4 sm:grid-cols-[7rem_1fr]">
                    <label className="block text-sm font-semibold text-slate-800">
                      ID
                      <input
                        aria-readonly="true"
                        className={`${inputClassName} bg-slate-100 font-mono`}
                        readOnly
                        value={item.id}
                      />
                    </label>
                    <label className="block text-sm font-semibold text-slate-800">
                      Source
                      <input
                        className={inputClassName}
                        maxLength={300}
                        onChange={(event) => updateEvidence(index, { source: event.target.value })}
                        placeholder="Study, report, or approved campaign material"
                        required
                        value={item.source}
                      />
                    </label>
                  </div>
                  <label className="mt-4 block text-sm font-semibold text-slate-800">
                    Content
                    <textarea
                      className={`${textareaClassName} min-h-28`}
                      maxLength={3000}
                      minLength={10}
                      onChange={(event) => updateEvidence(index, { content: event.target.value })}
                      placeholder="Paste the exact supporting information."
                      required
                      value={item.content}
                    />
                  </label>
                  <label className="mt-4 flex w-fit items-center gap-3 text-sm font-medium text-slate-800">
                    <input
                      checked={item.confidential}
                      className="h-4 w-4 rounded border-slate-300 accent-cyan-700"
                      onChange={(event) =>
                        updateEvidence(index, { confidential: event.target.checked })
                      }
                      type="checkbox"
                    />
                    This evidence is confidential
                  </label>
                </fieldset>
              ))}
            </div>
          )}
        </FormSection>

        <FormSection
          description="Use only information supplied for this review. PitchGuard will not look up the journalist."
          number="Step 3"
          title="Journalist"
        >
          <div className="grid gap-5 sm:grid-cols-2">
            <label className="block text-sm font-semibold text-slate-800">
              Name
              <input
                autoComplete="name"
                className={inputClassName}
                maxLength={120}
                onChange={(event) =>
                  setReviewRequest((current) => ({
                    ...current,
                    journalist: { ...current.journalist, name: event.target.value },
                  }))
                }
                placeholder="Journalist name"
                required
                value={reviewRequest.journalist.name}
              />
            </label>
            <label className="block text-sm font-semibold text-slate-800">
              Publication
              <input
                className={inputClassName}
                maxLength={160}
                onChange={(event) =>
                  setReviewRequest((current) => ({
                    ...current,
                    journalist: { ...current.journalist, publication: event.target.value },
                  }))
                }
                placeholder="Publication name"
                required
                value={reviewRequest.journalist.publication}
              />
            </label>
          </div>
          <label className="mt-5 block text-sm font-semibold text-slate-800">
            Beat
            <textarea
              className={`${textareaClassName} min-h-28`}
              maxLength={500}
              onChange={(event) =>
                setReviewRequest((current) => ({
                  ...current,
                  journalist: { ...current.journalist, beat: event.target.value },
                }))
              }
              placeholder="Topics and industries this journalist covers"
              required
              value={reviewRequest.journalist.beat}
            />
          </label>

          <div className="mt-7 border-t border-slate-200 pt-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h3 className="font-semibold text-slate-950">Recent coverage</h3>
                <p className="mt-1 text-sm leading-6 text-slate-600">
                  Add supplied examples when available. This list can be empty.
                </p>
              </div>
              <button
                className={secondaryButtonClassName}
                disabled={reviewRequest.journalist.recent_coverage.length >= 10}
                onClick={addCoverage}
                type="button"
              >
                Add coverage
              </button>
            </div>

            {reviewRequest.journalist.recent_coverage.length === 0 ? (
              <div className="mt-5 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-5 text-sm leading-6 text-slate-600">
                No recent coverage added. The relevance reviewer will use the supplied beat only.
              </div>
            ) : (
              <div className="mt-5 space-y-5">
                {reviewRequest.journalist.recent_coverage.map((item, index) => (
                  <fieldset
                    className="rounded-xl border border-slate-200 bg-slate-50 p-4 sm:p-5"
                    key={item.id}
                  >
                    <legend className="px-1 font-semibold text-slate-950">
                      Coverage {item.id}
                    </legend>
                    <button
                      aria-label={`Remove coverage ${item.id}`}
                      className="float-right -mt-7 text-sm font-semibold text-red-700 hover:text-red-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-700"
                      onClick={() => removeCoverage(index)}
                      type="button"
                    >
                      Remove
                    </button>
                    <div className="mt-4 grid gap-4 sm:grid-cols-[7rem_1fr]">
                      <label className="block text-sm font-semibold text-slate-800">
                        ID
                        <input
                          aria-readonly="true"
                          className={`${inputClassName} bg-slate-100 font-mono`}
                          readOnly
                          value={item.id}
                        />
                      </label>
                      <label className="block text-sm font-semibold text-slate-800">
                        Title
                        <input
                          className={inputClassName}
                          maxLength={300}
                          onChange={(event) => updateCoverage(index, { title: event.target.value })}
                          placeholder="Article title"
                          required
                          value={item.title}
                        />
                      </label>
                    </div>
                    <label className="mt-4 block text-sm font-semibold text-slate-800">
                      Summary
                      <textarea
                        className={`${textareaClassName} min-h-28`}
                        maxLength={1000}
                        minLength={10}
                        onChange={(event) =>
                          updateCoverage(index, { summary: event.target.value })
                        }
                        placeholder="Briefly describe the article and its focus."
                        required
                        value={item.summary}
                      />
                    </label>
                    <div className="mt-4 grid gap-4 sm:grid-cols-2">
                      <label className="block text-sm font-semibold text-slate-800">
                        Publication date <span className="font-normal text-slate-500">(optional)</span>
                        <input
                          className={inputClassName}
                          onChange={(event) =>
                            updateCoverage(index, {
                              publication_date: event.target.value || null,
                            })
                          }
                          type="date"
                          value={item.publication_date ?? ""}
                        />
                      </label>
                      <label className="block text-sm font-semibold text-slate-800">
                        URL <span className="font-normal text-slate-500">(optional)</span>
                        <input
                          className={inputClassName}
                          onChange={(event) =>
                            updateCoverage(index, { url: event.target.value || null })
                          }
                          placeholder="https://example.com/article"
                          type="url"
                          value={item.url ?? ""}
                        />
                      </label>
                    </div>
                  </fieldset>
                ))}
              </div>
            )}
          </div>
        </FormSection>

        <FormSection
          description="Paste the exact outreach message you want PitchGuard to review."
          number="Step 4"
          title="Draft pitch"
        >
          <label className="block text-sm font-semibold text-slate-800">
            Pitch
            <textarea
              className={`${textareaClassName} min-h-64`}
              maxLength={6000}
              minLength={50}
              onChange={(event) =>
                setReviewRequest((current) => ({ ...current, pitch: event.target.value }))
              }
              placeholder="Paste the complete draft pitch here."
              required
              value={reviewRequest.pitch}
            />
          </label>
          <p className="mt-3 text-xs leading-5 text-slate-500">
            The review is decision support only. You remain responsible for approving and sending the pitch.
          </p>
        </FormSection>

        <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-50 px-5 py-5 sm:px-7">
          <p aria-live="polite" className="text-sm text-slate-600">
            {isSubmitting ? "The three reviewers are processing the pitch." : "Ready for review."}
          </p>
          <button
            className="rounded-lg bg-cyan-800 px-5 py-3 text-sm font-bold text-white shadow-sm hover:bg-cyan-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-800 disabled:cursor-wait disabled:opacity-60"
            disabled={isSubmitting}
            type="submit"
          >
            {isSubmitting ? "Reviewing pitch…" : "Review pitch"}
          </button>
        </div>
      </form>

      <section
        aria-labelledby="review-results-title"
        className="scroll-mt-6 outline-none"
        ref={resultsRef}
        tabIndex={-1}
      >
        <div className="mb-5">
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-cyan-700">
            Quality gate
          </p>
          <h2
            className="mt-1 text-2xl font-semibold tracking-tight text-slate-950"
            id="review-results-title"
          >
            Review report
          </h2>
        </div>

        {isSubmitting ? (
          <div
            aria-live="polite"
            className="rounded-2xl border border-cyan-200 bg-cyan-50 p-6 shadow-sm"
            role="status"
          >
            <h3 className="font-semibold text-cyan-950">Review in progress</h3>
            <p className="mt-2 text-sm leading-6 text-cyan-900">
              Evidence, relevance, and PR risk reviewers are running. A final decision will only appear if all three complete.
            </p>
          </div>
        ) : requestFailure ? (
          <div
            className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-950 shadow-sm"
            role="alert"
          >
            <h3 className="font-semibold">{requestFailure.title}</h3>
            <p className="mt-2 text-sm leading-6">{requestFailure.message}</p>
            <button
              className="mt-4 rounded-lg border border-red-300 bg-white px-4 py-2 text-sm font-semibold text-red-900 hover:bg-red-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-800"
              onClick={retryReview}
              type="button"
            >
              Retry review
            </button>
          </div>
        ) : reviewResponse ? (
          <ReviewReport
            isSubmitting={isSubmitting}
            onRetry={retryReview}
            response={reviewResponse}
          />
        ) : (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center shadow-sm">
            <div
              aria-hidden="true"
              className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-cyan-100 text-xl font-bold text-cyan-800"
            >
              ✓
            </div>
            <h3 className="mt-4 font-semibold text-slate-950">Your report will appear here</h3>
            <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-600">
              Complete the form to review claim support, journalist relevance, personalization, and PR risk.
            </p>
          </div>
        )}
      </section>
    </div>
  );
}
