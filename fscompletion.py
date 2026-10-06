import os

import sublime
import sublime_plugin

from .fsutils import (escape_spaces, fuzzypath, iglob, isexplicitpath,
                      ispathescaped, remove_escape_spaces, scanpath)


SETTINGS_FILE = 'FilesystemAutocompletion.sublime-settings'
DEFAULT_SEARCH_ORDER = ('project', 'view', 'window')
MAX_RESULTS = 200
_activated_view_ids = set()


def _settings():
    return sublime.load_settings(SETTINGS_FILE)


def _debug(message, *args):
    if _settings().get('debug', False):
        print('FSAutocompletion: ' + (message % args if args else message))


def get_cwd_from_project(view, window):
    project_file = window.project_file_name() if window else None
    if project_file:
        cwd = os.path.dirname(project_file)
        _debug('get_cwd_from_project: project file found %s', project_file)
        return cwd
    _debug('get_cwd_from_project: no project file found')
    return None


def get_cwd_from_view(view, window):
    file_name = view.file_name()
    if file_name:
        return os.path.dirname(file_name)
    _debug('get_cwd_from_view: no view filename found')
    return None


def get_cwd_from_window(view, window):
    folders = window.folders() if window else ()
    for folder in folders:
        if isinstance(folder, str) and folder:
            _debug('get_cwd_from_window: folder found %s', folder)
            return folder
    _debug('get_cwd_from_window: no window folder found')
    return None


_SEARCH_FUNCTIONS = {
    'project': get_cwd_from_project,
    'view': get_cwd_from_view,
    'window': get_cwd_from_window,
}


def get_search_functions():
    configured = _settings().get('path_search_order', list(DEFAULT_SEARCH_ORDER))
    if not isinstance(configured, (list, tuple)):
        configured = DEFAULT_SEARCH_ORDER
    functions = [_SEARCH_FUNCTIONS[name] for name in configured
                 if name in _SEARCH_FUNCTIONS]
    return functions or list(DEFAULT_SEARCH_ORDER)


def get_view_cwd(view):
    window = view.window()
    for function in get_search_functions():
        cwd = function(view, window)
        _debug('get_view_cwd: %s => %s', function.__name__, cwd)
        if cwd:
            return cwd
    return None


def _consume_activation(view):
    view_id = view.id()
    if view_id in _activated_view_ids:
        _activated_view_ids.discard(view_id)
        return True
    return False


def completion_insert_text(path, completion):
    """Return content replacing Sublime's final word without duplicating spaces."""
    separator = path.rfind('/')
    if os.name == 'nt':
        separator = max(separator, path.rfind('\\'))
    leaf = path[separator + 1:]
    if not leaf or not completion.startswith(leaf):
        return completion
    index = leaf.rfind(' ')
    if index != -1:
        # Sublime's completion engine replaces only the final word even when
        # the preceding space was escaped in the source text.
        return completion[index + 1:]
    return completion


class FileSystemCompTriggerCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view_id = self.view.id()
        _activated_view_ids.add(view_id)
        sublime.set_timeout(lambda: _activated_view_ids.discard(view_id), 1000)
        self.view.run_command('auto_complete', {
            'disable_auto_insert': True,
            'next_completion_if_showing': False,
        })


class FileSystemCompCommand(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        if not locations:
            return None

        explicitly_activated = _consume_activation(view)
        location = locations[0]
        line = view.line(location)
        # Extract the whole line's text (prefix parameter above isn't enough)
        text = view.substr(sublime.Region(line.begin(), location))
        guessed_path = scanpath(text)

        if not explicitly_activated and not isexplicitpath(guessed_path):
            return None

        view_path = get_view_cwd(view)
        if guessed_path.startswith(('./', '.\\')):
            view_path = get_cwd_from_view(view, view.window()) or view_path

        guessed_path = os.path.expanduser(guessed_path)
        _debug('guessed_path: %s', guessed_path)
        _debug('view_path: %s', view_path)
        if not view_path and not isexplicitpath(guessed_path):
            return None

        escaped_path = ispathescaped(guessed_path)
        fuzzy_path = fuzzypath(guessed_path, view_path)
        if not fuzzy_path:
            return None
        _debug('fuzzy_path: %s', fuzzy_path)
        return (self.get_matches(fuzzy_path, escaped_path),
                sublime.INHIBIT_WORD_COMPLETIONS)

    def get_matches(self, path, escaped_path):
        lookup_path = remove_escape_spaces(path) if escaped_path else path
        _debug('pattern: %s*', lookup_path)
        entries = []
        for filename in iglob(lookup_path):
            entries.append(filename)
            if len(entries) >= MAX_RESULTS:
                break

        matches = []
        for filename in sorted(entries, key=lambda item: os.path.basename(item).casefold()):
            completion = os.path.basename(filename)
            if escaped_path:
                completion = escape_spaces(completion)
            if os.path.isdir(filename):
                trigger = '{} /\tDir'.format(completion)
                inserted = completion + '/' if _settings().get('add_slash', True) else completion
            else:
                trigger = '{}\tFile'.format(completion)
                inserted = completion
            matches.append((trigger, completion_insert_text(path, inserted)))
        return matches
