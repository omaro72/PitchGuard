import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { PitchReviewWorkspace } from "@/components/pitch-review-workspace";
import { ReviewReport } from "@/components/review-report";
import type { ReviewDecision, ReviewResponse } from "@/lib/review-types";

const apiBaseUrl = "http://localhost:8000";
const fetchMock = vi.fn();

function completeResponse(decision: ReviewDecision): ReviewResponse {
  return {
    analysis_status: "COMPLETE",
    decision,
    decision_reasons: [`The deterministic policy returned ${decision}.`],
    evidence_review: {
      claims: [
        {
          claim_text: "The fictional trial included 80 participants.",
          claim_type: "STATISTIC",
          importance: "HIGH",
          status: "SUPPORTED",
          explanation: "Evidence E1 contains the same participant count.",
          evidence_ids: ["E1"],
        },
      ],
      summary: "The supplied claim is supported.",
      missing_context: [],
    },
    relevance_review: {
      relevance_score: 85,
      personalization_score: 72,
      summary: "The pitch matches the supplied journalist beat.",
      matched_topics: ["workplace research"],
      mismatches: [],
      missing_context: [],
    },
    risk_review: {
      findings: [],
      summary: "No material PR risks were reported.",
      missing_context: [],
    },
    errors: [],
  };
}

function jsonResponse(body: ReviewResponse, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function fillRequiredFields() {
  fireEvent.change(screen.getByRole("textbox", { name: "Company name" }), {
    target: { value: "Northstar Labs" },
  });
  fireEvent.change(
    screen.getByRole("textbox", { name: "Target audience" }),
    { target: { value: "Workplace technology teams" } },
  );
  fireEvent.change(
    screen.getByRole("textbox", { name: "Announcement" }),
    { target: { value: "Northstar Labs is publishing a fictional workplace research report." } },
  );
  fireEvent.change(screen.getByRole("textbox", { name: "Name" }), {
    target: { value: "Morgan Lee" },
  });
  fireEvent.change(screen.getByRole("textbox", { name: "Publication" }), {
    target: { value: "Example Review" },
  });
  fireEvent.change(screen.getByRole("textbox", { name: "Beat" }), {
    target: { value: "Workplace technology" },
  });
  fireEvent.change(
    screen.getByRole("textbox", { name: "Pitch" }),
    {
      target: {
        value: "Hello Morgan, would you like to review our fictional workplace research report?",
      },
    },
  );
}

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
});

describe("PitchReviewWorkspace", () => {
  test("renders the main review form", () => {
    render(<PitchReviewWorkspace apiBaseUrl={apiBaseUrl} />);

    expect(screen.getByRole("heading", { name: "Campaign" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Supporting evidence" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Journalist" })).toBeTruthy();
    expect(screen.getByRole("textbox", { name: "Pitch" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Review pitch" })).toBeTruthy();
  });

  test("adds and removes evidence and coverage without reusing IDs", async () => {
    const user = userEvent.setup();
    render(<PitchReviewWorkspace apiBaseUrl={apiBaseUrl} />);

    await user.click(screen.getByRole("button", { name: "Add evidence" }));
    await user.click(screen.getByRole("button", { name: "Add evidence" }));
    expect(screen.getByRole("group", { name: "Evidence E1" })).toBeTruthy();
    expect(screen.getByRole("group", { name: "Evidence E2" })).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Remove evidence E1" }));
    await user.click(screen.getByRole("button", { name: "Add evidence" }));
    expect(screen.queryByRole("group", { name: "Evidence E1" })).toBeNull();
    expect(screen.getByRole("group", { name: "Evidence E3" })).toBeTruthy();

    await user.click(screen.getByRole("button", { name: "Add coverage" }));
    await user.click(screen.getByRole("button", { name: "Add coverage" }));
    expect(screen.getByRole("group", { name: "Coverage C1" })).toBeTruthy();
    expect(screen.getByRole("group", { name: "Coverage C2" })).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Remove coverage C1" }));
    await user.click(screen.getByRole("button", { name: "Add coverage" }));
    expect(screen.queryByRole("group", { name: "Coverage C1" })).toBeNull();
    expect(screen.getByRole("group", { name: "Coverage C3" })).toBeTruthy();
  });

  test("builds and submits the backend ReviewRequest payload", async () => {
    const user = userEvent.setup();
    fetchMock.mockResolvedValue(jsonResponse(completeResponse("PASS")));
    render(<PitchReviewWorkspace apiBaseUrl={apiBaseUrl} />);

    fillRequiredFields();
    await user.click(screen.getByRole("button", { name: "Add evidence" }));
    const evidence = screen.getByRole("group", { name: "Evidence E1" });
    fireEvent.change(within(evidence).getByRole("textbox", { name: "Source" }), {
      target: { value: "Trial report" },
    });
    fireEvent.change(
      within(evidence).getByRole("textbox", { name: "Content" }),
      { target: { value: "The fictional trial included 80 participants." } },
    );
    await user.click(
      within(evidence).getByRole("checkbox", { name: "This evidence is confidential" }),
    );

    await user.click(screen.getByRole("button", { name: "Add coverage" }));
    const coverage = screen.getByRole("group", { name: "Coverage C1" });
    fireEvent.change(
      within(coverage).getByRole("textbox", { name: "Title" }),
      { target: { value: "How teams assess workplace tools" } },
    );
    fireEvent.change(
      within(coverage).getByRole("textbox", { name: "Summary" }),
      { target: { value: "A fictional article about workplace research." } },
    );
    fireEvent.change(within(coverage).getByLabelText("Publication date (optional)"), {
      target: { value: "2026-08-15" },
    });
    fireEvent.change(
      within(coverage).getByRole("textbox", { name: "URL (optional)" }),
      { target: { value: "https://example.test/workplace-tools" } },
    );

    await user.click(screen.getByRole("button", { name: "Review pitch" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(`${apiBaseUrl}/api/v1/reviews`);
    expect(options.method).toBe("POST");
    expect(options.headers).toEqual({ "Content-Type": "application/json" });
    expect(JSON.parse(String(options.body))).toEqual({
      campaign: {
        company_name: "Northstar Labs",
        announcement: "Northstar Labs is publishing a fictional workplace research report.",
        target_audience: "Workplace technology teams",
      },
      evidence: [
        {
          id: "E1",
          source: "Trial report",
          content: "The fictional trial included 80 participants.",
          confidential: true,
        },
      ],
      journalist: {
        name: "Morgan Lee",
        publication: "Example Review",
        beat: "Workplace technology",
        recent_coverage: [
          {
            id: "C1",
            title: "How teams assess workplace tools",
            summary: "A fictional article about workplace research.",
            publication_date: "2026-08-15",
            url: "https://example.test/workplace-tools",
          },
        ],
      },
      pitch: "Hello Morgan, would you like to review our fictional workplace research report?",
    });
  });

  test("does not submit when required fields are invalid", async () => {
    const user = userEvent.setup();
    render(<PitchReviewWorkspace apiBaseUrl={apiBaseUrl} />);

    await user.click(screen.getByRole("button", { name: "Review pitch" }));

    expect(fetchMock).not.toHaveBeenCalled();
    expect(
      (screen.getByRole("textbox", { name: "Company name" }) as HTMLInputElement).validity
        .valueMissing,
    ).toBe(true);
  });

  test("shows an understandable backend validation error", async () => {
    const user = userEvent.setup();
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          detail: [
            {
              type: "string_too_long",
              loc: ["body", "pitch"],
              ctx: { max_length: 6000 },
            },
          ],
        }),
        { status: 422, headers: { "Content-Type": "application/json" } },
      ),
    );
    render(<PitchReviewWorkspace apiBaseUrl={apiBaseUrl} />);
    fillRequiredFields();

    await user.click(screen.getByRole("button", { name: "Review pitch" }));

    await waitFor(() => {
      expect(screen.getByRole("alert").textContent).toContain(
        "pitch must be at most 6000 characters.",
      );
    });
  });
});

describe("ReviewReport", () => {
  test.each(["PASS", "REVISE", "BLOCK"] as const)(
    "renders a complete %s report",
    (decision) => {
      render(
        <ReviewReport
          isSubmitting={false}
          onRetry={vi.fn()}
          response={completeResponse(decision)}
        />,
      );

      expect(screen.getByRole("status").textContent).toContain(decision);
      expect(screen.getByText(`The deterministic policy returned ${decision}.`)).toBeTruthy();
      expect(screen.getByText("The supplied claim is supported.")).toBeTruthy();
      expect(screen.getByText("85/100")).toBeTruthy();
      expect(screen.getByText("No material PR risks were reported.")).toBeTruthy();
    },
  );

  test("renders a structured error and preserves successful reviewer results", () => {
    const response: ReviewResponse = {
      ...completeResponse("PASS"),
      analysis_status: "ERROR",
      decision: null,
      decision_reasons: [],
      relevance_review: null,
      risk_review: null,
      errors: [
        {
          reviewer: "RELEVANCE",
          code: "PROVIDER_UNAVAILABLE",
          message: "The local AI service is unavailable.",
          retryable: true,
        },
      ],
    };

    render(<ReviewReport isSubmitting={false} onRetry={vi.fn()} response={response} />);

    expect(screen.getByRole("alert").textContent).toContain("ERROR");
    expect(screen.getByText("The supplied claim is supported.")).toBeTruthy();
    expect(screen.getByText("The local AI service is unavailable.")).toBeTruthy();
    expect(
      screen.getByText("The Journalist Relevance reviewer did not return a usable result."),
    ).toBeTruthy();
    expect(screen.getByText("The PR Risk reviewer did not return a usable result.")).toBeTruthy();
  });
});
