"""Exercise registration with the real editor model and real probed media."""
import json
import shutil
import subprocess
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from reel_edit import or_project as op


class OpenRecorderProjects(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            op.open_recorder()
        except SystemExit as error:
            raise unittest.SkipTest(str(error))

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='reel-project-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.work = self.root / 'work'
        self.work.mkdir()
        self.output = self.root / 'A named reel.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=128x192:r=30:d=1',
                        '-c:v', 'libx264', '-threads', '1', str(self.output)], check=True)
        raw = self.root / 'raw'
        raw.mkdir()
        shutil.copy2(self.output, raw / 'TAKE.MOV')
        op.write(self.work / 'takes.json', {'folder': str(raw), 'takes': [
            {'take': 'TAKE', 'start': 0, 'end': 1, 'from': 0, 'to': 1}]})
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(op, 'REGISTRY', self.root / 'registry.json'))
        self.stack.enter_context(patch.object(op, 'OR_CONFIG', str(self.root / 'config.json')))
        self.stack.enter_context(patch('reel_edit.project.load', return_value=SimpleNamespace(
            output=str(self.output), captions=[('hello', 0, 1)])))

    def test_repeated_prepare_preserves_clip_ids_and_user_cuts(self):
        folder = op.prepare(self.work)
        project_file = folder / '.openrecorder/project.json'
        project = op.read(project_file)
        project['lanes'][0]['clips'][0]['src_out'] = .8
        op.write(project_file, project)
        self.assertEqual(op.prepare(self.work), folder)
        self.assertEqual(op.read(project_file), project)
        self.assertEqual(folder.name, self.output.stem)
        self.assertEqual(len(op.read(self.root / 'config.json')['recent']), 1)

    def test_migration_keeps_edits_remaps_media_and_removes_duplicate_cards(self):
        legacy = self.work / 'openrecorder-revision-3'
        with patch.object(op, 'project_folder', return_value=legacy):
            op.prepare(self.work)
        project_file = legacy / '.openrecorder/project.json'
        project = op.read(project_file)
        project['lanes'][0]['clips'][0]['volume'] = .7
        op.write(project_file, project)
        before = project_file.read_bytes()
        cfg = op.read(self.root / 'config.json')
        cfg['recent'][str(self.work / 'openrecorder-revision-2')] = 1
        cfg['recent'][str(self.root / 'unrelated')] = 2
        op.write(self.root / 'config.json', cfg)
        # An actual second old project, which should be removed only from Recent.
        shutil.copytree(legacy, self.work / 'openrecorder-revision-2')
        folder = op.prepare(self.work)
        current = op.read(folder / '.openrecorder/project.json')
        clip = current['lanes'][0]['clips'][0]
        self.assertEqual(clip['volume'], .7)
        self.assertTrue(Path(clip['media']).is_file())
        self.assertTrue(Path(clip['media']).is_relative_to(folder))
        self.assertEqual(project_file.read_bytes(), before)
        recents = op.read(self.root / 'config.json')['recent']
        self.assertEqual(set(recents), {str(folder), str(self.root / 'unrelated')})
        from open_recorder.project.library import _summary
        self.assertEqual(_summary(folder)['name'], self.output.stem)

    def test_changed_render_does_not_overwrite_user_changes(self):
        folder = op.prepare(self.work)
        project_file = folder / '.openrecorder/project.json'
        project = op.read(project_file)
        project['sequence']['aspect'] = '1:1'
        op.write(project_file, project)
        before = project_file.read_bytes()
        baseline = Path(op.read(folder / 'map.json')['baseline'])
        original = baseline.read_bytes()
        self.output.write_bytes(self.output.read_bytes() + b'changed')
        with self.assertRaises(SystemExit):
            op.prepare(self.work)
        self.assertEqual(project_file.read_bytes(), before)
        self.assertEqual(baseline.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
