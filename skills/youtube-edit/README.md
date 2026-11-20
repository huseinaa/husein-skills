# youtube-edit

*Part of [husein-skills](https://github.com/huseinaa/husein-skills), all my Claude Code skills in one repo.*

One command in Claude Code for editing a YouTube video, from raw talking-head footage to a private
YouTube draft. It's a thin router on top of my brother Hasan's open-source editor,
**[claude-youtube-editor](https://github.com/hassancs91/claude-youtube-editor)**. His repo does the
actual work. This skill finds it, sets it up the first time, and sends each request to the right step.

Two ways to have the editor:

- **Bundled:** install the [youtube-editor](../youtube-editor/) skill too (it comes with "install all").
  It's Hasan's editor packaged as a skill, and this skill uses it automatically.
- **Your own clone of Hasan's repo**, so a `git pull` gets his newest updates the day he ships them.

---

## What it does

You type `/youtube-edit` and say what you want. It picks the step and follows the editor's own
instructions for it:

| You ask to | Step in the editor |
|---|---|
| cut the raw footage, remove fillers and retakes, tighten the pacing | clean cut |
| add visuals, overlays, a fake screen recording | Remotion visuals, built as code |
| remove background noise, isolate the voice | voice cleanup |
| add sound effects or music | SFX |
| write titles and make thumbnails | packaging |
| set up the channel's look | brand setup |
| upload | private YouTube draft |

The full pipeline runs in this order: **cut, visuals, voice, SFX, packaging, upload.**

---

## What you need

- **Claude Code**
- **Python 3.10+**, **Node.js** and **ffmpeg**
- **git**, to clone the editor
- An **AssemblyAI** API key, for transcription (the free tier is enough to try it)
- Optional: ElevenLabs (voice isolation and SFX, paid) and Gemini (thumbnails, paid)

---

## Install

**1. Install the skill.** One line (needs [Node.js](https://nodejs.org)):

```
npx skills add huseinaa/husein-skills --skill youtube-edit -g
```

Or with git:

```
git clone https://github.com/huseinaa/husein-skills.git
cd husein-skills
powershell -ExecutionPolicy Bypass -File install.ps1 youtube-edit   # Windows
./install.sh youtube-edit       # Mac / Linux
```

**2. Run it once.** Type `/youtube-edit` in Claude Code. On the first run it:

- uses the bundled youtube-editor skill if it's installed. If not, it asks where your clone is (or clones
  it for you) and remembers the path in the skill's `local/config.json`
- creates the Python venv and installs the Remotion packages
- asks you to copy `.env.example` to `.env` and fill in your keys (it never makes up a key or commits `.env`)
- runs **brand setup**, so your visuals use your own look and not Hasan's house brand

---

## Use it

```
/youtube-edit cut videos/my-first-video
/youtube-edit add the visual beats to videos/my-first-video
/youtube-edit titles and a thumbnail for videos/my-first-video
```

Your videos go in the editor's `videos/<name>/` folder. Raw footage and renders never go to git.

**Your own rules:** put them in the skill's `local/WORKFLOW.md` (for example where your videos live,
your brand notes or extra steps). The skill reads that file first, and it's never committed.

---

## Updating

- The editor: `git pull` inside the editor's folder.
- This skill: `git pull` inside your husein-skills clone, or `npx skills update youtube-edit`.

---

## Credit

The editor is [claude-youtube-editor](https://github.com/hassancs91/claude-youtube-editor) by Hasan,
MIT licensed. Go star it. This skill is only the router, by Husein Aboul Hasan,
[unemployedhusein.com](https://unemployedhusein.com).
