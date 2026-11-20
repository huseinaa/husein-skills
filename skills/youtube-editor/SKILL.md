---
name: youtube-editor
description: claude-youtube-editor by Hasan Aboul Hasan, bundled as a ready-to-use skill. The whole editor lives in this folder - raw talking-head footage to a private YouTube draft (clean cut, Remotion visuals built as code, voice cleanup, SFX, titles and thumbnails, upload). Use when the user types /youtube-editor, when /youtube-edit routes here, or when they ask to edit, cut, add visuals to, sound-design, package or upload a YouTube video and no separate clone of the editor is set up.
---

# /youtube-editor

This folder **is** the editor: my brother Hasan Aboul Hasan's open-source
[claude-youtube-editor](https://github.com/hassancs91/claude-youtube-editor) (MIT, see [LICENSE](LICENSE)),
bundled so it installs with one command. All credit for the editor goes to him.

The folder that holds this SKILL.md is the editor's repo root, called `<root>` below.

## Every run

1. If `local/WORKFLOW.md` exists in `<root>`, read it first. Its rules win over the defaults.
2. Read `<root>/CLAUDE.md`. It has the pipeline, the layout and the hard rules. Follow it.
3. Pick the step from what the user asked and read that step's skill before doing anything:

| They ask to | Read `<root>/.claude/skills/...` |
|---|---|
| cut the raw footage, remove fillers and retakes, tighten pacing | `clean-cut/SKILL.md` |
| build the visual beats, add overlays, fake a screen recording | `make-tsx/SKILL.md`, `fake-screencast/SKILL.md`, and `vidtsx-2d-generator/SKILL.md` for the authoring rules |
| remove background noise, isolate the voice | `clean-audio/SKILL.md` |
| add sound effects or music | `suggest-sfx/SKILL.md` |
| titles and thumbnails | `packaging/SKILL.md`, `thumbnail/SKILL.md` |
| set up or change the channel's look | `brand-setup/SKILL.md` |
| upload | `tools/yt_upload.py`, setup in `tools/yt_upload_SETUP.md` |

Pipeline order: **cut, visuals, voice, SFX, packaging, upload.**

4. Run every tool **from `<root>` with its own venv**, passing the project as `videos/<name>`:

```
cd "<root>"
venv\Scripts\python tools\transcribe.py videos/video-1      # Windows
venv/bin/python tools/transcribe.py videos/video-1          # Mac / Linux
```

Videos go in `<root>/videos/<name>/`. Raw footage and renders never go to git.

## First use

Check each one and do what is missing. Say what you did in one line each.

| Step | Command (from `<root>`) | Done when |
|---|---|---|
| Python venv | `python -m venv venv`, then install `requirements.txt` with the venv's pip | the venv's python can `import requests, PIL` |
| Remotion | `cd remotion`, `npm install`, `npm run gen` | `remotion/node_modules` exists |
| Keys | copy `.env.example` to `.env` | `ASSEMBLYAI_API_KEY` is filled in. ElevenLabs is only for voice isolation and SFX, Gemini only for thumbnails |
| **Brand** | run the `brand-setup` step | `brand.md` describes the user's channel, not Hasan's |

**Do not skip the brand step.** The editor ships with Hasan's own indigo house brand. Until brand setup
runs, every visual looks like his channel, not the user's.

The keys are the user's to add. Never invent one, and never commit `.env`.

## What it costs

The editor is free. The services are not: Claude Code, AssemblyAI (free tier is enough to try it),
ElevenLabs (paid, optional; `clean-audio` also has a local RNNoise method with no key), Gemini (paid,
thumbnails only), YouTube upload (free, OAuth).
