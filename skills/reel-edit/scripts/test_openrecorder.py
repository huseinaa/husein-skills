"""Checks for the Open Recorder hand-off. Run with python -m unittest discover -s scripts -p test_openrecorder.py.
Pure functions only: no Open Recorder install, ffmpeg or video needed."""
import unittest
from pathlib import Path

from reel_edit import or_learn as orx

MAP = {"baseline": "B", "lane": "L", "raw": {str(Path("R").resolve()).lower(): "take1"},
       "pieces": [{"take": "take1", "reel_s": 0.0, "reel_e": 2.0, "raw_from": 1.0, "raw_to": 3.0},
                  {"take": "take2", "reel_s": 2.0, "reel_e": 3.0, "raw_from": 5.0, "raw_to": 6.5}]}


def clip(media, start, src_in, src_out, **kw):
    return {"media": media, "start": start, "src_in": src_in, "src_out": src_out, **kw}


def project(*clips, aspect="9:16", lanes=None):
    return {"sequence": {"aspect": aspect}, "media": {"R": {"path": "R"}},
            "lanes": lanes or [{"id": "L", "name": "Reel", "kind": "video", "clips": list(clips)}]}


AI = project(clip("B", 0, 0, 2), clip("B", 2, 2, 3))


class OpenRecorderHandOff(unittest.TestCase):
    def test_reel_time_maps_to_raw_time_with_retime(self):
        self.assertAlmostEqual(orx.to_raw(MAP["pieces"][0], 0.5), 1.5)
        self.assertAlmostEqual(orx.to_raw(MAP["pieces"][1], 2.5), 5.75)  # piece played faster than filmed

    def test_untouched_project_has_the_ai_ranges(self):
        ranges, _ = orx.raw_ranges(AI, MAP)
        self.assertEqual(ranges, {"take1": [[1.0, 3.0]], "take2": [[5.0, 6.5]]})

    def test_trim_and_delete_and_raw_restore(self):
        his = project(clip("B", 0, 0, 1.5), clip("R", 1.5, 0.5, 1.0))
        a, _ = orx.raw_ranges(AI, MAP)
        h, _ = orx.raw_ranges(his, MAP)
        self.assertEqual(h["take1"], [[0.5, 2.5]])
        removed = {t: orx.subtract(a[t], h.get(t, [])) for t in a}
        restored = {t: orx.subtract(h[t], a.get(t, [])) for t in h}
        self.assertEqual(removed, {"take1": [[2.5, 3.0]], "take2": [[5.0, 6.5]]})
        self.assertEqual(restored, {"take1": [[0.5, 1.0]]})

    def test_exports_beside_the_reel_are_found(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            reel = Path(d) / "My Reel.mp4"
            for name in ("My Reel.mp4", "My Reel (2).mp4", "My Reel - YouTube.mp4", "Other (2).mp4"):
                (Path(d) / name).write_bytes(b"x")
            self.assertEqual([f.name for f in orx.exports_of(reel)], ["My Reel (2).mp4"])

    def test_extras_notice_reframe_volume_and_broll(self):
        his = project(lanes=[
            {"id": "X", "name": "B-roll", "kind": "video", "clips": [clip("broll.mp4", 1, 0, 2)]},
            {"id": "L", "name": "Reel", "kind": "video", "clips": [
                clip("B", 0, 0, 2, volume=1.5, transform={"x": 0, "y": 0, "w": 1.2, "h": 1.2, "fit": "cover", "mask": "none"}),
                clip("B", 2, 2, 3, transform={"x": 0, "y": 0, "w": 1, "h": 1, "fit": "cover", "mask": "none"})]}])
        ex = orx.extras(AI, his, MAP)
        self.assertEqual(ex["volume"], [1.5])
        self.assertEqual(ex["reframed"][0]["at"], [0])
        self.assertTrue(ex["added"][0]["new_lane"])
        self.assertEqual(ex["added"][0]["clips"], 1)
        self.assertNotIn("aspect", ex)


if __name__ == "__main__":
    unittest.main()
