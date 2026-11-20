---
name: youtube-edit
description: Edit a YouTube video with claude-youtube-editor (Hasan's open-source editor), the full pipeline from raw talking-head footage to a private YouTube draft (clean cut, Remotion visuals built as code, voice cleanup, SFX, titles and thumbnails, upload). Use when the user asks to edit, cut, add visuals or overlays to, sound-design, package or upload a YouTube video, or types /youtube-edit. Not for Instagram reels (that is /reel-edit).
---

# /youtube-edit

A router. The editor itself is Hasan's open-source project,
[claude-youtube-editor](https://github.com/hassancs91/claude-youtube-editor) (MIT). It is installed as its
own git repo so `git pull` picks up his updates. Nothing from it is copied here. **Read its files and
follow them, they are the source of truth.**

## Before anything

1. If `local/WORKFLOW.md` exists next to this SKILL.md, read it first. Its rules win over the defaults below.
2. Find the editor repo (called `<repo>` below):
   - `local/config.json` next to this SKILL.md, key `editor_repo`, if it exists.
   - Otherwise ask the user once where it is. If they don't have it, offer to clone it:
     `git clone https://github.com/hassancs91/claude-youtube-editor.git` into a folder they pick
     (default: their home folder). Then write the path into `local/config.json` as
     `{"editor_repo": "<absolute path>"}` so you never ask again. `local/` is never committed.

## Every run

1. Read `<repo>/CLAUDE.md`. It has the pipeline, the layout and the hard rules.
2. Pick the step from what the user asked and read that step's skill before doing anything:

| They ask to | Read `<repo>/.claude/skills/...` |
|---|---|
| cut the raw footage, remove fillers and retakes, tighten pacing | `clean-cut/SKILL.md` |
| build the visual beats, add overlays, fake a screen recording | `make-tsx/SKILL.md`, `fake-screencast/SKILL.md`, and `vidtsx-2d-generator/SKILL.md` for the authoring rules |
| remove background noise, isolate the voice | `clean-audio/SKILL.md` |
| add sound effects or music | `suggest-sfx/SKILL.md` |
| titles and thumbnails | `packaging/SKILL.md`, `thumbnail/SKILL.md` |
| set up or change the channel's look | `brand-setup/SKILL.md` |
| upload | `tools/yt_upload.py`, setup in `tools/yt_upload_SETUP.md` |

Pipeline order: **cut, visuals, voice, SFX, packaging, upload.**

3. Run every tool **from the repo root with its own venv**, passing the project as `videos/<name>`:

```
cd "<repo>"
venv\Scripts\python tools\transcribe.py videos/video-1      # Windows
venv/bin/python tools/transcribe.py videos/video-1          # Mac / Linux
```

Videos go in `<repo>/videos/<name>/`. Raw footage and renders never go to git.

## First use

Check each one and do what is missing. Say what you did in one line each.

| Step | Command (from the repo root) | Done when |
|---|---|---|
| Python venv | `python -m venv venv`, then install `requirements.txt` with the venv's pip | the venv's python can `import requests, PIL` |
| Remotion | `cd remotion`, `npm install`, `npm run gen` | `remotion/node_modules` exists |
| Keys | copy `.env.example` to `.env` | `ASSEMBLYAI_API_KEY` is filled in. ElevenLabs is only for voice isolation and SFX, Gemini only for thumbnails |
| **Brand** | run the `brand-setup` skill | `brand.md` describes the user's channel, not Hasan's |

**Do not skip the brand step.** The repo ships with Hasan's own indigo house brand. Until `brand-setup`
runs, every visual it builds looks like his channel, not the user's.

The keys are the user's to add. Never invent one, and never commit `.env`.

## What it costs

The project is free. The services are not: Claude Code, AssemblyAI (free tier is enough to try it),
ElevenLabs (paid, optional), Gemini (paid, thumbnails only), YouTube upload (free, OAuth).

## Updating

`git -C "<repo>" pull` updates the editor. Updating this skill is a `git pull` in the husein-skills clone.
