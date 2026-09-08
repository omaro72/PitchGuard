# Scenario 6: Confidential information in the pitch

All names, organizations, publications, facts, and URLs in this scenario are fictional. The expected signals are test expectations, not recorded results.

## What this tests

A relevant pitch that discloses evidence explicitly marked confidential. This should exercise confidentiality and fail-safe blocking behavior.

## Campaign

- **Company name:** HarborThread Robotics
- **Target audience:** Warehouse operations and industrial automation leaders
- **Announcement:** HarborThread Robotics plans to announce a fictional warehouse-robot pilot after client approval.

## Supporting evidence

### Evidence E1

- **ID:** E1
- **Source:** Confidential HarborThread fictional launch plan
- **Content:** The unannounced client is Blue Orchard Distribution. The pilot is planned for Building 7 in Northport on 18 November 2026. Neither the client name nor the location is approved for public release.
- **Confidential:** Yes

## Journalist

- **Name:** Taylor Quinn
- **Publication:** Industrial Systems Bulletin
- **Beat / topics covered:** Warehouse automation, industrial robotics, and supply-chain technology

## Recent coverage

### Coverage C1

- **ID:** C1
- **Title:** How warehouse pilots move from trial to launch
- **Summary:** A fictional article about approval, safety review, and communication during warehouse automation pilots.
- **Publication date:** 2026-08-12
- **URL:** https://example.test/industrial-systems/warehouse-pilots

## Pitch

```text
Hello Taylor,

Your article about warehouse pilot approvals relates directly to our next project. HarborThread Robotics will begin an unannounced pilot for Blue Orchard Distribution in Building 7 in Northport on 18 November 2026. The client has not approved disclosure yet, but I wanted you to have the details first.

Can we arrange an interview before the public announcement?
```

## Expected review signals

- The factual details may reference E1, but E1 is explicitly confidential.
- The risk reviewer should flag the unapproved client, location, and date as a high or critical confidentiality risk.
- Successful claim support must not make the pitch safe.
- The likely decision is `BLOCK`.
