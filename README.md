# Sealed First

**Write your answer before the AI does.**

Sealed First is a small habit for anyone who works with AI. Seal your own take, get the AI's answer blind, record where you landed, and keep score of whether your judgment holds up. Teams use the same routine to show whether their human review is independent, or just agreeing with the machine.

Free app: **https://sealedfirst.com/app**

## Install

### Claude Code

```
/plugin marketplace add tan2line/sealed-first
/plugin install sealed-first@sealed-first
```

### Claude apps

Download [`sealed-first.plugin`](https://sealedfirst.com/sealed-first.plugin) and open it in Claude to install.

### Other tools that read SKILL.md skills

Codex CLI, GitHub Copilot, Gemini CLI, Cursor and others read the same skill format. Copy the three folders in [`plugin/skills/`](plugin/skills) into your tool's skills directory. The skills need Python 3 for the log and scoring scripts.

## Skills

| Skill | What it does |
|---|---|
| `/seal` | Seals your take, gets a blind answer from a separate subagent that never sees your take, compares, optionally red-teams both, and logs it. |
| `/seal-brief` | Your judgment retention score: score, domain split, patterns, open seals to clear. |
| `/seal-team` | Oversight evidence report from a team pilot's export, pilot plans, and setup. |

## Why the blind answer runs separately

A model that has read your take can't answer independently. `/seal` writes your seal first, then asks a fresh subagent that receives only the question. In a tool with no subagents, it seals and asks you to get the answer from a fresh chat instead. It never answers your question itself.

## Your log

Seals are saved to `~/.sealed-first/seals.json` (or the path in `SEALED_FIRST_LOG`). The file imports into the free app, and the app's export works with the skills, so one log follows you across tools. Nothing is sent anywhere by the skills except the question you ask the blind subagent.

## The score

Judgment retention score, 0–100, over the last 90 days:

- **Final calls right (45%).** After seeing the AI, was your final position the one that held up?
- **Confidence matches results (25%).** Saying 80% sure should mean being right about 80% of the time.
- **Kept the cadence (15%).** Seals in the last four weeks against your weekly target.
- **Explained changes of mind (15%).** Every update or switch carries a written reason.

Provisional until five seals are resolved. Outcomes are self-graded, so the score is only as honest as you are. Team pilots fix that by having QA enter outcomes.

## Repository

- `plugin/` is the Claude plugin and the skills.
- `site/` is sealedfirst.com, including the free browser app.

## Team pilots

For a workflow where people review AI recommendations (prior authorization, claims, contract review, analysis), a pilot measures whether reviewers form their own call, how often they switch to the AI after disagreeing, and whether those switches help or hurt. See https://sealedfirst.com/pilot.

---

Built by Andrew Plummer, MD, MPH. (Views my own.) · Contact: drplummer@gmail.com

License: MIT
