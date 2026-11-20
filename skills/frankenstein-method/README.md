# frankenstein-method

*Part of [husein-skills](https://github.com/huseinaa/husein-skills), all my Claude Code skills in one repo.*

**The Frankenstein method is by Moussari.** This skill runs its ideation part for you. It finds the
videos that are outperforming for your competitors on Instagram and hands you one page of the best
topics and formats to steal from.

---

## What it does

1. **Asks a few easy questions**, one at a time: what you do, who you help, and what those people struggle with.
2. **Helps you pick 10 to 15 competitor accounts.** It suggests accounts under 1M followers that talk about
   a problem you solve. You check them, add your own, and confirm the list twice before anything is
   added to your watchlist.
3. **Scans them for outliers on Sandcastles**: every Reel from the last 6 months that got at least 2.5x
   the account's normal views. Trial reels and off-topic personal posts are dropped.
4. **Builds one scrollable page**, the Frankenstein Idea List, best first, with each video's topic and format.
   Press **Save idea** on 15 topics and **Save format** on 3 to 5 formats.
5. Then you post each of those 15 ideas in two different formats over the next 30 days.

The scan and the page cost **no Sandcastles credits**. A deeper breakdown of one video costs 1 credit,
and it always asks first.

---

## What you need

- **Claude** (Claude Code or the Claude app) with artifacts, for the idea page
- A **[Sandcastles](https://sandcastles.ai/?ref=moussari)** account, connected to Claude as a connector.
  The skill walks you through connecting it on the first run. (The link is Moussari's referral link.)
- Instagram Reels only

No Sandcastles? The skill explains how to do the same thing by hand.

---

## Install

One line (needs [Node.js](https://nodejs.org)):

```
npx skills add huseinaa/husein-skills --skill frankenstein-method -g
```

Or with git:

```
git clone https://github.com/huseinaa/husein-skills.git
cd husein-skills
powershell -ExecutionPolicy Bypass -File install.ps1 frankenstein-method   # Windows
./install.sh frankenstein-method       # Mac / Linux
```

Or copy the `skills/frankenstein-method` folder into `~/.claude/skills/`. For the Claude app, upload
the folder as a skill in your settings.

---

## Use it

```
/frankenstein-method
```

Answer the questions, confirm your accounts, and you get the page. Say "continue" in the same chat to pick
up where you left off.

---

## Credit

The Frankenstein method and this skill are by **Moussari**. The credit line and the Sandcastles referral link
inside the skill are his and stay as they are. Shared here by Husein Aboul Hasan,
[unemployedhusein.com](https://unemployedhusein.com).
