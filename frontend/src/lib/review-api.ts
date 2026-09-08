import type { ReviewRequest, ReviewResponse } from "@/lib/review-types";

export type ReviewSubmissionResult =
  | { kind: "review"; response: ReviewResponse }
  | { kind: "validation_error"; message: string }
  | { kind: "request_error"; message: string };

const fieldNames: Record<string, string> = {
  announcement: "announcement",
  beat: "journalist beat",
  company_name: "company name",
  content: "evidence content",
  evidence: "evidence",
  id: "item ID",
  journalist: "journalist details",
  name: "journalist name",
  pitch: "pitch",
  publication: "publication",
  publication_date: "publication date",
  recent_coverage: "recent coverage",
  source: "evidence source",
  summary: "coverage summary",
  target_audience: "target audience",
  title: "coverage title",
  url: "coverage URL",
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isReviewResponse(value: unknown): value is ReviewResponse {
  if (!isRecord(value)) {
    return false;
  }

  const validDecision =
    value.decision === null ||
    value.decision === "PASS" ||
    value.decision === "REVISE" ||
    value.decision === "BLOCK";
  const validAnalysisStatus =
    value.analysis_status === "COMPLETE" || value.analysis_status === "ERROR";
  const validReview = (review: unknown) => review === null || isRecord(review);

  return (
    validAnalysisStatus &&
    validDecision &&
    Array.isArray(value.decision_reasons) &&
    validReview(value.evidence_review) &&
    validReview(value.relevance_review) &&
    validReview(value.risk_review) &&
    Array.isArray(value.errors)
  );
}

function validationIssue(detail: unknown): string | null {
  if (!isRecord(detail) || !Array.isArray(detail.loc)) {
    return null;
  }

  const field = [...detail.loc]
    .reverse()
    .find((location): location is string => typeof location === "string");
  if (!field) {
    return null;
  }

  const label = fieldNames[field] ?? field.replaceAll("_", " ");
  const errorType = typeof detail.type === "string" ? detail.type : "";
  const context = isRecord(detail.ctx) ? detail.ctx : {};
  const maximum = typeof context.max_length === "number" ? context.max_length : null;
  const minimum = typeof context.min_length === "number" ? context.min_length : null;

  if (errorType === "missing") {
    return `${label} is required.`;
  }
  if (errorType === "string_too_long" && maximum !== null) {
    return `${label} must be at most ${maximum} characters.`;
  }
  if (errorType === "string_too_short" && minimum !== null) {
    return `${label} must be at least ${minimum} characters.`;
  }
  if (errorType === "too_long" && maximum !== null) {
    return `${label} must contain at most ${maximum} items.`;
  }
  if (errorType.startsWith("url_")) {
    return `${label} must be a valid HTTP or HTTPS URL.`;
  }
  if (errorType.startsWith("date_")) {
    return `${label} must be a valid date.`;
  }
  return `Check ${label}.`;
}

function validationMessage(value: unknown): string {
  if (!isRecord(value) || !Array.isArray(value.detail)) {
    return "The review service rejected the form. Check the required fields and try again.";
  }

  const issues = value.detail
    .flatMap((detail) => {
      const issue = validationIssue(detail);
      return issue ? [issue] : [];
    })
    .filter((issue, index, values) => values.indexOf(issue) === index)
    .slice(0, 4);

  if (issues.length === 0) {
    return "The review service rejected the form. Check the required fields and try again.";
  }

  return issues.join(" ");
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

export async function submitReview(
  apiBaseUrl: string,
  reviewRequest: ReviewRequest,
): Promise<ReviewSubmissionResult> {
  let response: Response;

  try {
    response = await fetch(`${apiBaseUrl}/api/v1/reviews`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(reviewRequest),
    });
  } catch {
    return {
      kind: "request_error",
      message:
        "PitchGuard could not reach the review service. Check that the backend is running and try again.",
    };
  }

  const body = await readJson(response);

  if (response.status === 422) {
    return { kind: "validation_error", message: validationMessage(body) };
  }

  if (response.status === 200 || response.status === 503) {
    if (!isReviewResponse(body)) {
      return {
        kind: "request_error",
        message: "The review service returned an unreadable response. Please try again.",
      };
    }
    if (
      (response.status === 200 && body.analysis_status !== "COMPLETE") ||
      (response.status === 503 && body.analysis_status !== "ERROR")
    ) {
      return {
        kind: "request_error",
        message: "The review service returned an inconsistent response. Please try again.",
      };
    }
    return { kind: "review", response: body };
  }

  return {
    kind: "request_error",
    message:
      response.status >= 500
        ? "The review service encountered an unexpected error. Please try again."
        : "The review request could not be completed. Check the form and try again.",
  };
}
