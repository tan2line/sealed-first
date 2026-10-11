# Pilot guardrails

Apply all of these to every pilot plan and setup.

## Data
- Case references only. No names, dates of birth, member or medical record numbers, or free text that identifies a person. The page is not a system of record for protected health information.
- The pilot record holds reviewer decisions about the AI, not the case itself.
- Reviewer identity is stored as an opaque id. Names are resolved at display time only.

## Independence
- The review tool must hide the AI's recommendation until the reviewer records a first call. If it can't, say plainly that the seal records intent, not independence, and that the attestation rate becomes the key number.
- Outcomes are entered by QA or an auditor, never by the reviewer whose decision is being checked.

## Sample sizes
- 20 submitted reviews for a first status reading.
- 10 outcome checks before drawing any conclusion about whether switching to the AI helps or hurts.
- Report rates with their counts. Never present a rate without its denominator.

## Framing
- Per-reviewer numbers are coaching signals, not performance ratings. A high match rate can mean easy cases.
- The report measures whether human review adds an independent check. It does not certify the AI or the reviewers.

## Conflicts
- Whoever runs and reports the pilot should be independent of the workflow being assessed. Don't run a pilot, or write its report, for an organization where you hold an official role.

## Exit report
- Period, workflow, counts, status, the four independence/anchoring/documentation/outcome sections, limits of the evidence, and a recommendation: keep the review step as is, change how it works, or redesign it.
