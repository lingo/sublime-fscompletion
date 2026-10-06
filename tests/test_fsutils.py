import os
import tempfile
import unittest

import fsutils


class PathUtilityTests(unittest.TestCase):
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

    def test_fuzzypath_finds_path_suffix(self):
        with tempfile.TemporaryDirectory() as directory:
            filename = os.path.join(directory, 'target file')
            open(filename, 'w').close()
            self.assertEqual(fsutils.fuzzypath('noise target', directory),
                             os.path.join(directory, 'target'))

    def test_escaped_space_detection(self):
        self.assertTrue(fsutils.ispathescaped(r'a\ b\ c'))
        self.assertFalse(fsutils.ispathescaped(r'a\ b c'))


if __name__ == '__main__':
    unittest.main()
