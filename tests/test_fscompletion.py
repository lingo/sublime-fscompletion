import contextlib
import importlib.util
import io
import pathlib
import sys
import tempfile
import types
import unittest


class FakeSettings(dict):
    def get(self, key, default=None):
        return super().get(key, default)


class FakeSublime(types.SimpleNamespace):
    INHIBIT_WORD_COMPLETIONS = 1

    @staticmethod
    def load_settings(name):
        return FakeSettings({'path_search_order': ['project', 'view', 'window']})

    @staticmethod
    def set_timeout(callback, timeout):
        return None


def load_module():
    root = pathlib.Path(__file__).resolve().parents[1]
    package = types.ModuleType('sublime_fscompletion')
    package.__path__ = [str(root)]
    sys.modules['sublime'] = FakeSublime()
    sys.modules['sublime_plugin'] = types.SimpleNamespace(TextCommand=object, EventListener=object)
    sys.modules['sublime_fscompletion'] = package
    spec = importlib.util.spec_from_file_location(
        'sublime_fscompletion.fscompletion', root / 'fscompletion.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


completion = load_module()


class CompletionTests(unittest.TestCase):
    def test_debug_output_is_gated_and_formats_context(self):
        original = completion._settings
        completion._settings = lambda: FakeSettings({'debug': True})
        output = io.StringIO()
        try:
            with contextlib.redirect_stdout(output):
                completion._debug('pattern: %s*', '/tmp/file')
        finally:
            completion._settings = original
        self.assertEqual(output.getvalue(), 'FSAutocompletion: pattern: /tmp/file*\n')

    def test_space_completion_replaces_only_the_final_word(self):
        self.assertEqual(completion.completion_insert_text('/tmp/quick test', 'quick test 1'), 'test 1')
        self.assertEqual(completion.completion_insert_text('/tmp/quick\\ test', 'quick\\ test\\ 1'), 'test\\ 1')

    def test_three_file_space_completion_scenario_from_legacy_comment(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in ('quick test', 'quick test 1', 'quick test 2'):
                pathlib.Path(directory, name).touch()

            matches = completion.FileSystemCompCommand().get_matches(
                str(pathlib.Path(directory, 'quick')), escaped_path=False)
            inserted = [contents for _, contents in matches]

            self.assertEqual(inserted, ['quick test', 'quick test 1', 'quick test 2'])
            self.assertEqual(
                completion.completion_insert_text(
                    str(pathlib.Path(directory, 'quick test')), 'quick test 1'),
                'test 1')

    def test_activation_is_view_scoped_and_one_shot(self):
        class View:
            def id(self):
                return 42
        view = View()
        completion._activated_view_ids.add(42)
        self.assertTrue(completion._consume_activation(view))
        self.assertFalse(completion._consume_activation(view))

    def test_invalid_search_order_uses_defaults(self):
        original = completion._settings
        completion._settings = lambda: FakeSettings({'path_search_order': ['missing']})
        try:
            self.assertEqual(len(completion.get_search_functions()), 3)
        finally:
            completion._settings = original

    def test_project_and_window_cwds_use_current_api_values(self):
        class Window:
            def project_file_name(self):
                return '/project/site.sublime-project'

            def folders(self):
                return ['/workspace/one', '/workspace/two']

        window = Window()
        self.assertEqual(completion.get_cwd_from_project(None, window), '/project')
        self.assertEqual(completion.get_cwd_from_window(None, window), '/workspace/one')


if __name__ == '__main__':
    unittest.main()
