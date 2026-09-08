# Scenario 4: Clearly wrong journalist

All names, organizations, publications, facts, and URLs in this scenario are fictional. The expected signals are test expectations, not recorded results.

## What this tests

A supported clean-energy announcement sent to a journalist whose supplied work is exclusively about video games. This should exercise the low-relevance `BLOCK` condition.

## Campaign

- **Company name:** KindredGrid Energy
- **Target audience:** Commercial building operators interested in energy-demand planning
- **Announcement:** KindredGrid Energy is releasing a fictional report about electricity-demand planning across 40 commercial buildings.

## Supporting evidence

### Evidence E1

- **ID:** E1
- **Source:** KindredGrid fictional building study
- **Content:** The report summarizes hourly electricity-demand data supplied by 40 fictional commercial buildings between January and June 2026.
- **Confidential:** No

## Journalist

- **Name:** Rowan Ellis
- **Publication:** Pixel Play Review
- **Beat / topics covered:** Video-game releases, esports tournaments, and game-console hardware

## Recent coverage

### Coverage C1

- **ID:** C1
- **Title:** Cooperative games arriving this autumn
- **Summary:** A fictional preview of cooperative console games scheduled for autumn release.
- **Publication date:** 2026-08-29
- **URL:** https://example.test/pixel-play/cooperative-games

## Pitch

```text
Hello Rowan,

KindredGrid Energy is releasing a report based on hourly electricity-demand data from 40 commercial buildings. The report discusses planning considerations for commercial building operators.

Would you like a copy of the fictional report?
```

## Expected review signals

- The factual scope should be supported by E1.
- Relevance should be very low because the campaign does not match the supplied beat or recent coverage.
- Personalization should also be weak because the pitch does not meaningfully connect to the journalist's work.
- The likely decision is `BLOCK` if relevance is below 40.
