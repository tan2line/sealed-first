---
name: seal
description: Seals the user's own take on a question before any AI answers it, then gets a blind answer that never sees the take, compares the two, and logs the result to the user's Sealed First log. Use when the user types /seal, says "seal this", "seal my take", "let me seal first", "blind check", or asks a consequential question and says they want to commit to their own view before seeing the AI's.
---

# Seal

Run the Sealed First routine inside a chat. The goal is an honest record: the user's take is fixed before any AI answer exists, and the AI answer comes from something that never saw the take.

Read `references/config.md` for the data model, the storage options and the exact prompts.

## The one rule that matters

Never answer the user's question yourself in this conversation. You have read their take, so any answer you write is anchored and not blind. The blind answer must come from a separate subagent that receives the question and nothing else. If this tool has no subagent, seal the take, then ask the user to paste the question (only the question) into a fresh chat or another AI and paste the answer back here. Do not fall back to answering.

## Storage

Use the local log by default: `python3 scripts/seals.py` in this skill's folder (it prints JSON). The log lives at `~/.sealed-first/seals.json` unless `SEALED_FIRST_LOG` is set, and it imports straight into the free app at sealedfirst.com. If `references/config.md` names a personal log page and an artifact-data tool is available, write there instead, using the same fields.

## Steps

1. **Collect the seal.** Get the question, the user's take, and how sure they are. If the user gave the question but no take, ask for the take before anything else and do not discuss the question. Ask confidence and domain together:
   - Confidence: Hunch (60), Fairly sure (75), Sure (90), or any number from 50 to 100.
   - Domain: clinical, policy, venture, technical, other.
   If the user is in a hurry, default to 75 and the domain that fits, and say which you used.
2. **Seal it.** Run `python3 scripts/seals.py new --q "<question>" --take "<take>" --conf <n> --tag <tag>`. Pass the text as arguments; never edit the script. Confirm in one line that the take is sealed and show the 12-character fingerprint. Nothing else happens until this succeeds.
3. **Get the blind answer.** Start a subagent with only the blind prompt from `references/config.md`, filled with the question, plus one line telling it to answer directly without tools. Do not mention the user, their take, or this routine in the subagent prompt.
4. **Reveal.** `seals.py update <id> ai="<answer>" aiSource=claude revealedAt=<ms> status=revealed` (use `aiSource=pasted` for an answer the user pasted). Show the sealed take with its confidence, then the blind answer.
5. **Judge.** Ask how they compare (agree / partly / disagree) and where the user landed (held / updated / switched). If they updated or switched, ask what changed their mind and require a short reason. If they agreed, offer the red-team pass first, since shared blind spots hide in agreements.
6. **Red team (optional, after the reveal only).** Run a second subagent with the red-team prompt. Save `redteam` and `redteamAt`. Show it and let the user revise where they landed.
7. **Log.** `seals.py update <id> verdict=<v> final=<f> why="<reason>" judgedAt=<ms> status=judged`. Tell the user the seal waits until they know who was right, and that "resolve <short question>" closes it.

## Resolving

When the user says who turned out right, find the seal with `seals.py list --status judged`, confirm the match if there is any doubt, and set `outcome` (me, ai, both, neither, or na for "can't be checked"), `resolvedAt` and `status=resolved`.

## Style

Fast: the whole routine should feel like 30 seconds plus the blind answer. One line per step, no lectures. Get timestamps with `python3 -c "import time;print(int(time.time()*1000))"`.
