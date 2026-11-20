# Fixing cuts in Open Recorder and learning from them

After a reel is built and checked, the user can fix small things themselves in
[Open Recorder](https://github.com/huseinaa/open-recorder) (2.2 or later), a free screen
recorder and editor for Windows. The skill learns from what they changed.

```
python scripts/openrecorder.py <workdir> --prepare
```

It builds an Open Recorder project in `<workdir>/<reel title>/`, named after the reel, and puts
it at the top of Open Recorder's start screen (`<workdir>/Edit in Open Recorder.cmd` opens it
too). Nothing is added to the reel's final folder: it keeps the reel, its other copies, the
cover and `assets/`. Run it with the Python Open Recorder is installed in. If the user is
filming, prepare it and do not open anything.

## What they get

One `Reel` lane: the finished reel split at every cut the AI made, so trimming a piece keeps
the captions, graphics and sound design that belong to that footage. The media bin holds only
the reel. The raw takes stay in the reel's `assets/` folder: dragging one in from there brings
back footage the AI cut, as it was filmed (no captions or graphics on it, say so when it
matters). Everything else Open Recorder does works too: extra lanes for B-roll or music, blur
boxes, reframing, volume, its AI chat.

They export from Open Recorder, and the export lands right beside the reel as `<reel> (2).mp4`
(Open Recorder never overwrites). `--learn` then puts it in the reel's place, so the folder is
back to one reel. The AI's version stays frozen in the project (`media/baseline-<hash>.mp4`). A
platform copy made from the AI's cut (such as a YouTube version without a DM ask) is not
rebuilt by itself: `--learn` says when one exists, and it is rebuilt only if the user wants.

## What is saved

In `<workdir>/<reel title>/`:

- `media/baseline-<hash>.mp4`: the checked reel, frozen. The project plays from it. Earlier baseline files stay intact when the render changes.
- `project.ai.json`: the project exactly as the AI cut it.
- `map.json`: for every piece, reel time against raw take time (`raw_from`, `raw_to`), the
  caption text, the raw take files, and the lane id.
- `review-diff.txt`: what changed, readable, written by `--learn`.

`history/openrecorder-projects.json` in this skill lists every prepared reel and the last
export learned. Each `--learn` writes `history/<reel>-<time>.json` with `learned: false`.

Revisions reuse this same folder and recent-project entry. Preparation migrates a registered legacy
project once, remaps its media paths and removes older duplicate Recent entries without deleting
their files. An unchanged render preserves clip IDs and user edits. A changed render refuses to
overwrite a project the user already changed. Learn from it first, or
`--prepare --fresh` only when they ask to start again (their version is kept as
`project.<time>.json`). It also removes what the older built-in cut reviewer left beside a reel
(`Edit cuts.cmd`, `_edit/review/`).

## Before the next reel, and when they say they exported

```
python scripts/openrecorder.py --pending        reels with an export waiting beside them
python scripts/openrecorder.py <workdir> --learn
```

The history file holds:

| Field | What it holds |
|---|---|
| `he_cut` | stretches the AI kept and they removed, in raw take time, with `edge` (`head`, `tail`, `whole` piece, or none for a cut inside a piece) and the caption text there |
| `he_restored` | stretches the AI cut and they brought back from a raw take |
| `reordered` | pieces play in a different order |
| `open_recorder` | what only the editor can change: `reframed` pieces, `volume`, `added` (lanes, B-roll, images, music, blur, with files and boxes), `lanes_off`, `aspect` |
| `changed: false` | the AI cut was exported untouched. That is evidence too |

Write observed patterns to `deltas.md`, with the reel, the date and the exact evidence.
Separate what they changed from your reading of why. Only mark the history file
`learned: true` after recording its lesson (or noting that nothing changed). Do not infer a
timing rule from an untouched export or a single ambiguous cut. A preference repeated across
two reels can become a default; an explicit instruction applies immediately. Lecture pacing
rules do not transfer to reels by themselves.

Keep the work folder until they have exported: the project plays from its frozen `media/baseline-<hash>.mp4`.
