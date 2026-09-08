# Scenario 1: Supported and relevant pitch

All names, organizations, publications, facts, and URLs in this scenario are fictional. The expected signals are test expectations, not recorded results.

## What this tests

A well-supported pitch sent to a relevant journalist with specific personalization. This should exercise the strongest likely `PASS` path.

## Campaign

- **Company name:** BrightHarbor Labs
- **Target audience:** Workplace operations leaders at small and medium-sized companies
- **Announcement:** BrightHarbor Labs is publishing the results of a six-week pilot of its fictional team-scheduling tool with 120 workplace teams.

## Supporting evidence

### Evidence E1

- **ID:** E1
- **Source:** BrightHarbor fictional pilot report, September 2026
- **Content:** During a six-week pilot involving 120 workplace teams, participating teams recorded 18% fewer meeting reschedules than during the previous six weeks.
- **Confidential:** No

## Journalist

- **Name:** Jordan Vale
- **Publication:** WorkPattern Weekly
- **Beat / topics covered:** Workplace operations software, team coordination, and evidence-based management practices

## Recent coverage

### Coverage C1

- **ID:** C1
- **Title:** Why scheduling friction affects distributed teams
- **Summary:** A fictional article examining how repeated meeting changes affect distributed teams and how managers measure scheduling problems.
- **Publication date:** 2026-08-18
- **URL:** https://example.test/workpattern/scheduling-friction

## Pitch

```text
Hello Jordan,

Your recent article about scheduling friction in distributed teams examined how managers measure repeated meeting changes. BrightHarbor Labs has completed a six-week pilot with 120 workplace teams. Participants recorded 18% fewer meeting reschedules than during the previous six weeks.

Would you like to receive the fictional pilot report and methodology for review?
```

## Expected review signals

- The 120-team and 18% claims should reference E1 and be classified as `SUPPORTED`.
- Relevance and personalization should both be strong.
- No material PR risk should be reported.
- The likely decision is `PASS`, but live-model wording and scores may vary.
