# husein-skills

All my Claude Code skills in one place. Each skill is a folder in [`skills/`](skills/) with its own
README that explains what it does and how to set it up.

They also work in other agents that read skills, like Codex and Cursor.

---

## The skills

| Skill | What it does |
|---|---|
| [**reel-edit**](skills/reel-edit/) | Turns the takes you filmed on your phone into a finished vertical reel: cuts, clean voice, word-synced captions, hook, graphics, B-roll and a cover. |
| [**feature-testing**](skills/feature-testing/) | Checks a finished feature without you reading every line: writes missing tests, measures coverage, plants bugs on purpose to prove the tests catch them, fixes what fails. |
| [**youtube-editor**](skills/youtube-editor/) | The full YouTube editor as a skill: raw talking-head footage to a private YouTube draft, with the cut, Remotion visuals, voice cleanup, SFX, titles, thumbnails and upload. By my brother Hasan Aboul Hasan ([claude-youtube-editor](https://github.com/hassancs91/claude-youtube-editor)). |
| [**youtube-edit**](skills/youtube-edit/) | One `/youtube-edit` command that runs Hasan's editor: the bundled youtube-editor skill, or your own clone of his repo for his newest updates. |
| [**app-store-screenshots**](skills/app-store-screenshots/) | Designs App Store and Play Store screenshot sets that look like the best on the store. By Charles Liu. |
| [**frankenstein-method**](skills/frankenstein-method/) | Finds the best-performing topics and formats from your competitors' Reels and gives you one idea page. Method by Moussari. |

---

## Install all of them in one shot

With [Node.js](https://nodejs.org) installed:

```
npx skills add huseinaa/husein-skills --skill '*' -g
```

It asks which agents you use (Claude Code, Codex, Cursor and more) and installs every skill for them.

**Or with git**, so one `git pull` updates everything later:

```
git clone https://github.com/huseinaa/husein-skills.git
cd husein-skills
```

Then link every skill into `~/.claude/skills/`:

- Windows (PowerShell): `powershell -ExecutionPolicy Bypass -File install.ps1`
- Mac / Linux: `./install.sh`

No git? Click **Code > Download ZIP** at the top of this page, unzip it, and run the same installer
inside the folder.

Open a new Claude Code session and type `/` to see them.

> Some skills need more than the install, like Python packages or an API key. Each skill's README has
> a "What you need" section. Read it before the first run.

---

## Install just one

```
npx skills add huseinaa/husein-skills --skill reel-edit -g
```

Or from a clone, give the installer the skill's name:

```
powershell -ExecutionPolicy Bypass -File install.ps1 reel-edit      # Windows
./install.sh reel-edit                                              # Mac / Linux
```

Or copy the skill's folder from `skills/` into `~/.claude/skills/`.

---

## Update

- Installed with git: `git pull` inside your clone. The installer made links, so that's all.
- Installed with npx: `npx skills update`.

Your own settings live in each skill's `local/` folder. It's never in the repo, so an update never
overwrites it.

---

## License

[MIT](LICENSE) for my skills. Three skills here are other people's work, shared with credit:

- **youtube-editor** is my brother Hasan Aboul Hasan's
  [claude-youtube-editor](https://github.com/hassancs91/claude-youtube-editor), under his MIT license
  ([skills/youtube-editor/LICENSE](skills/youtube-editor/LICENSE)). Its sound and music clips come with his
  repo, and their sources are in `media/library/*/catalog.json`.
- **app-store-screenshots** is by Charles Liu, from
  [charles-skills](https://github.com/LemonFace0309/charles-skills), under its own MIT license
  ([skills/app-store-screenshots/LICENSE](skills/app-store-screenshots/LICENSE)).
- **frankenstein-method**: the method and the skill are by Moussari. His credit line and referral link stay as they are.

---

Built by Husein Aboul Hasan, [unemployedhusein.com](https://unemployedhusein.com). If you make something
with these, send it to me.
