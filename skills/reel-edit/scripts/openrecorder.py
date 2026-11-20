"""Hand a finished reel to Open Recorder for small cut fixes, and learn from what the user changed.

    python openrecorder.py WORK --prepare [--fresh]   build the Open Recorder project
    python openrecorder.py WORK --learn               after they exported: what changed -> history
    python openrecorder.py --pending                  reels with an export not learned yet

Open Recorder (github.com/huseinaa/open-recorder, 2.2+) is a free screen recorder and editor.
--prepare  builds or refreshes WORK/<reel title>/ (reel_edit/or_project.py), puts it at the top
           of Open Recorder's start screen and writes "Edit in Open Recorder.cmd" in WORK. The
           export lands next to the reel.
--learn    maps their cut back to the raw takes (reel_edit/or_learn.py), writes history/, and
           puts their export in the reel's place.
"""
import argparse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work", nargs="?")
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--fresh", action="store_true", help="with --prepare: replace a project they already changed")
    ap.add_argument("--learn", action="store_true")
    ap.add_argument("--pending", action="store_true")
    a = ap.parse_args()
    if a.pending:
        from reel_edit.or_learn import pending
        items = pending()
        for work, f in items:
            print(f"{work}\t{f}")
        if not items:
            print("nothing to learn: no new Open Recorder export")
    elif a.work and a.prepare:
        from reel_edit.or_project import prepare
        prepare(a.work, a.fresh)
    elif a.work and a.learn:
        from reel_edit.or_learn import learn
        learn(a.work)
    else:
        ap.error("WORK with --prepare or --learn, or --pending")


if __name__ == "__main__":
    main()
