# Scenario 5: Relevant journalist but generic personalization

All names, organizations, publications, facts, and URLs in this scenario are fictional. The expected signals are test expectations, not recorded results.

## What this tests

A relevant and supported campaign whose opening uses only a generic compliment. This should isolate the personalization threshold and produce a likely `REVISE` result.

## Campaign

- **Company name:** MintBridge Learning
- **Target audience:** School technology leaders and teacher-support teams
- **Announcement:** MintBridge Learning is publishing a fictional survey about how teachers evaluate classroom software training.

## Supporting evidence

### Evidence E1

- **ID:** E1
- **Source:** MintBridge fictional teacher survey methodology
- **Content:** The survey collected complete responses from 310 fictional teachers about classroom software training between May and June 2026.
- **Confidential:** No

## Journalist

- **Name:** Samir Brooks
- **Publication:** Learning Systems Today
- **Beat / topics covered:** Education technology, teacher training, and school software procurement

## Recent coverage

### Coverage C1

- **ID:** C1
- **Title:** What schools ask before buying classroom software
- **Summary:** A fictional article about procurement questions, teacher preparation, and evidence requirements for classroom technology.
- **Publication date:** 2026-08-06
- **URL:** https://example.test/learning-systems/school-software

## Pitch

```text
Hello Samir,

I am a huge fan of everything you write. MintBridge Learning surveyed 310 teachers about classroom software training between May and June 2026 and is publishing the fictional results.

Would you like the survey summary and methodology?
```

## Expected review signals

- The survey size and dates should be `SUPPORTED` by E1.
- Relevance should be high because the campaign matches the supplied topics.
- Personalization should be below the pass threshold because the pitch does not mention C1 or a specific idea from it.
- The likely decision is `REVISE` if personalization is below 60.
