import os
import tempfile
import unittest
from unittest import mock

import fsutils


class PathUtilityTests(unittest.TestCase):
    def test_hasnext_examples_from_legacy_comments(self):
        self.assertTrue(fsutils.hasnext(iter([1, 2, 3])))
        self.assertFalse(fsutils.hasnext(iter([])))

    def test_hasroot_examples_from_legacy_comments(self):
        cases = {
            '/somepath': True,
            'C:/somepath': True,
            r'C:\somepath': True,
            '~/somepath': False,
            'somepath': False,
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                self.assertEqual(fsutils.hasroot(path), expected)

    def test_isexplicitpath_examples_from_legacy_comments(self):
        cases = {
            '/somepath': True,
            './somepath': True,
            '~/somepath': True,
            'C:/somepath': True,
            r'C:\somepath': True,
            'somepath': False,
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                self.assertEqual(fsutils.isexplicitpath(path), expected)

    def test_explicit_paths_cover_supported_roots(self):
        for path in ('/tmp/file', 'C:/tmp/file', r'C:\\tmp\\file',
                     r'\\\\server\\share\\file', './file', '../file', '~'):
            self.assertTrue(fsutils.isexplicitpath(path), path)

    def test_literal_glob_characters_are_not_wildcards(self):
        with tempfile.TemporaryDirectory() as directory:
            literal = os.path.join(directory, 'a[1]*?.txt')
            other = os.path.join(directory, 'aX1ZZ.txt')
            open(literal, 'w').close()
            open(other, 'w').close()
            self.assertEqual(list(fsutils.iglob(literal)), [literal])
            self.assertTrue(fsutils.isfname('*'))
            self.assertTrue(fsutils.isfname('?'))

    def test_windows_drive_prefix_is_not_case_folded_in_glob_pattern(self):
        with mock.patch.object(fsutils.glob, 'iglob', return_value=iter(())) as iglob:
            list(fsutils.iglob('C:/Users/donal/pro'))

        self.assertEqual(
            iglob.call_args.args[0],
            'C:/[uU][sS][eE][rR][sS]/[dD][oO][nN][aA][lL]/[pP][rR][oO]*')

    def test_fuzzypath_keeps_an_absolute_drive_path(self):
        requested = 'C:/Users/donal/pro'

        def windows_glob(path):
            return iter([path]) if path == requested else iter(())

        self.assertEqual(fsutils.fuzzypath(requested, 'D:/fallback', windows_glob), requested)

    def test_fuzzypath_finds_path_suffix(self):
        with tempfile.TemporaryDirectory() as directory:
            filename = os.path.join(directory, 'target file')
            open(filename, 'w').close()
            self.assertEqual(fsutils.fuzzypath('noise target', directory),
                             os.path.join(directory, 'target'))

    def test_escaped_space_detection(self):
        cases = {
            r'\\ catch': False,
            r'\\\ nocatch': True,
            r'\ \ \ space\ \ escaped': True,
            '': False,
            'string': False,
            r'simple\ escape': True,
            'simple nonescape': False,
            r'almost\ all\ spaces escaped': False,
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                self.assertEqual(fsutils.ispathescaped(path), expected)

    def test_scanpath_examples_from_legacy_comments(self):
        cases = {
            r'with spaces\\\\ home': r'with spaces\\\\ home',
            r'with spaces\\\\\ home': r'spaces\\\\\ home',
            '/home': '/home',
            'some text with /home': '/home',
            r'some text with filename\ with\ spaces': r'filename\ with\ spaces',
            r'some text with filename with\ spaces': r'with\ spaces',
            r'some\ text with spaces': r'some\ text with spaces',
            'some text with ./filename': './filename',
            'some text with ./filename with spaces': './filename with spaces',
            'some text with wrong filename': 'some text with wrong filename',
            'some text ~/Documents': '~/Documents',
            r'some text C:\Documents': r'C:\Documents',
            'some text C:/Documents': 'C:/Documents',
            r'some text C:/Documents\ and\ Settings/Directory': r'C:/Documents\ and\ Settings/Directory',
            'some text C:/Documents and Settings/Directory': 'C:/Documents and Settings/Directory',
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(fsutils.scanpath(text), expected)

    def test_fuzzypath_examples_from_legacy_comments(self):
        base = '/base'

        def matcher(*matches):
            return lambda path: iter([path]) if path in matches else iter([])

        cases = (
            ('some precceding test[[[[test', matcher('/base/test'), '/base/test'),
            ('[test', matcher('/base/test'), '/base/test'),
            ('[ttest', matcher('/base/test'), None),
            ('[some text ttest', matcher('/base/test'), None),
            ('[some text test', matcher('/base/test'), '/base/test'),
            ('[/', matcher('/'), '/'),
            ('/', matcher('/'), '/'),
            ('/file', matcher('/file'), '/file'),
        )
        for path, fake_glob, expected in cases:
            with self.subTest(path=path):
                self.assertEqual(fsutils.fuzzypath(path, base, fake_glob), expected)


if __name__ == '__main__':
    unittest.main()
