# Scenario 3: Contradicted high-importance claim

All names, organizations, publications, facts, and URLs in this scenario are fictional. The expected signals are test expectations, not recorded results.

## What this tests

A central performance claim that changes both the size and scope of the supplied evidence. This should exercise a deterministic `BLOCK` condition.

## Campaign

- **Company name:** CedarPeak Analytics
- **Target audience:** Operations teams evaluating administrative software
- **Announcement:** CedarPeak Analytics is sharing results from a small fictional pilot of its administrative workflow tool.

## Supporting evidence

### Evidence E1

- **ID:** E1
- **Source:** CedarPeak fictional four-week pilot summary
- **Content:** In a four-week pilot with 24 volunteer participants, average time spent on two selected administrative tasks decreased by 12%.
- **Confidential:** No

## Journalist

- **Name:** Riley North
- **Publication:** Operations Ledger
- **Beat / topics covered:** Business operations, workplace tools, and productivity research

## Recent coverage

### Coverage C1

- **ID:** C1
- **Title:** What small software pilots can really demonstrate
- **Summary:** A fictional article about interpreting limited workplace software trials without overstating their conclusions.
- **Publication date:** 2026-07-22
- **URL:** https://example.test/operations-ledger/small-pilots

## Pitch

```text
Hello Riley,

Following your article about interpreting small software pilots, CedarPeak Analytics can now prove that its platform saves 45% of all working time across more than 500 companies. Our study confirms that the result applies to every administrative process.

Would you like to interview our product lead this week?
```

## Expected review signals

- The 45%, 500-company, all-working-time, and every-process statements conflict with E1.
- At least the central performance claim should be `CONTRADICTED` and high importance.
- Journalist relevance may still be strong.
- The likely decision is `BLOCK` because of the high-importance contradiction.
