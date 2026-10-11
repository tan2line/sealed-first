# Sealed First configuration

## Storage

| Setting | Value |
|---|---|
| Local log (default) | `~/.sealed-first/seals.json`, or the path in `SEALED_FIRST_LOG` |
| Personal log page (optional) | none |
| Team pilot page (optional) | none |

To use a claude.ai Sealed First page instead of the local file, put its link in the table above. The skills then read and write that page's data store with the same fields.

The local log is a JSON list. Import it into the free app at https://sealedfirst.com/app with "Import log", or export from the app and point `SEALED_FIRST_LOG` at the file.

## Seal fields

| Field | Type | Set when |
|---|---|---|
| id | 20 hex characters | sealed |
| q | string, trimmed | sealed |
| take | string, trimmed | sealed |
| conf | integer 50–100 | sealed |
| tag | clinical \| policy \| venture \| technical \| other | sealed |
| createdAt | integer, ms since epoch | sealed |
| hash | first 12 hex chars of SHA-256 of `q + "\n" + take + "\n" + createdAt` | sealed |
| status | sealed → revealed → judged → resolved | each step |
| ai, aiSource ("claude" or "pasted"), revealedAt | | revealed |
| verdict (agree \| partly \| disagree), final (held \| updated \| switched), why, judgedAt | | judged |
| redteam, redteamAt | | optional, after reveal |
| outcome (me \| ai \| both \| neither \| na), resolvedAt | | resolved |

The first six fields never change after sealing. The app checks the fingerprint and flags any seal whose take was edited.

## Prompts

Blind answer:

```
Answer the question below on your own. You have not seen anyone else's view of it.

Give your position and the main reasons in under 150 words. Commit to a position. Don't hedge to stay agreeable, and say plainly if it can't be answered with confidence.
End with one line that starts "Bottom line:".

Question:
<q>
```

Red team (only after the reveal):

```
You are an adversarial reviewer. Below are two answers to the same question: a person's take, written before they saw any AI output, and an AI's independent answer.[ The two broadly agree.]

Make the strongest case that BOTH are wrong or missing something important, in under 150 words:
1. The shared assumption most likely to fail.
2. The best counter-position a smart skeptic would take.
3. The one piece of evidence that would settle it.
Don't summarize either answer and don't pick a winner.

Question:
<q>

Person's take:
<take>

AI's answer:
<ai>
```

Include the bracketed sentence only when the verdict is `agree`.

## Team pilot data

A team pilot exports an evidence CSV with these columns: reviewer, reviewer_id, case_ref, sealed_at, sealed_decision, confidence, fingerprint, attested_independent, ai_recommendation, final_decision, changed_after_reveal, switched_to_ai, reason, submitted_at, correct_decision. The `seal-team` skill reports from that file.
