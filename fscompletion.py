import sublime, sublime_plugin

import os
import os.path
import re
import glob
from os import sep
from itertools import takewhile

if sublime.version() < '3000':
    # we are on ST2 and Python 2.X
    _ST3 = False
    from fsutils import *
else:
    _ST3 = True
    from .fsutils import *

# Enable SublimeText2 to complete filesystem paths a la VIM:
# @author Luke Hudson <lukeletters@gmail.com>
# @author Filip Krikava <krikava@gmail.com>
#

settings = sublime.load_settings('FilesystemAutocompletion.sublime-settings')
debug    = settings.get('debug', False)

# Force generation of User settings file
settings.set('debug', debug)
settings.set('add_slash', settings.get('add_slash'))

activated = False

def getviewcwd(view):
    default = '/' ## What to return if nothing else found
    cwd     = view.file_name() ## Try to get the current view's filename
    if cwd == None:
        cwd = default
        if debug:
            print("FSAutocompletion: getviewcwd: No view filename found")
        ## File is not saved to disk, look for project dir
        window = sublime.active_window()
        if window == None:
            if debug:
                print("FSAutocompletion: getviewcwd: No active window found")
            return cwd ## Give up here if we can't even get an active window!
        try:
            folder = window.project_data()['folders'].pop()
            if debug:
                print("FSAutocompletion: getviewcwd: folder found", folder)
            cwd = folder['path']
        except AttributeError:
            if debug:
                print("FSAutocompletion: getviewcwd: project_data not found, or no folders found in data")
            try:
                folder = window.folders().pop()
                if debug:
                    print("FSAutocompletion: getviewcwd: folder found", folder)
                cwd = folder.path
            except AttributeError:
                if debug:
                    print("FSAutocompletion: getviewcwd: folders() not found, or was empty list")
                pass
        if debug:
            print("FSAutocompletion: getviewcwd: returning cwd", cwd)
        return cwd
    else:
        return os.path.dirname(cwd)

class FileSystemCompTriggerCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        global activated
        view = self.view

        activated = True

        view.run_command('auto_complete',
            {'disable_auto_insert': True,
             'next_completion_if_showing': False})

class FileSystemCompCommand(sublime_plugin.EventListener):
    """
    Enable SublimeText2 to complete
    filesystem paths a la VIM:
    """

    def on_query_completions(self, view, prefix, locations):
        global activated

        # Find the current location (of first selection)
        rowcol = view.rowcol(locations[0])
        line = view.line(locations[0])
        # Extract the whole line's text (prefix parameter above isn't enough)
        lstr = view.substr(line)
        lstr = lstr[0:rowcol[1]]

        guessed_path = scanpath(lstr)

        # If it is not obvious (part starts in a file system root) then we have
        # to be explicitly activated
        if not activated and not isexplicitpath(guessed_path):
            return None

        # expand ~ if there is any
        guessed_path = os.path.expanduser(guessed_path)
        escaped_path = ispathescaped(guessed_path)

        # view path
        view_path = getviewcwd(view)

        if debug:
            print ("FSAutocompletion: guessed_path:", guessed_path)
        if debug:
            print ("FSAutocompletion: view_path:", view_path)

        fuzzy_path = fuzzypath(guessed_path, view_path)
        if not fuzzy_path:
            return None

        if debug:
            print ("FSAutocompletion: fuzzy_path:", fuzzy_path)

        matches = self.get_matches(fuzzy_path, escaped_path)

        # # if there are no matches this means that the path does not exists in
        # # latex for example one can do \input{$cur} where $cur is the cursor
        # # position. This will scan '\input{' as a guessed_path since it is
        # # really a valid path. The glob pattern however will not match anything
        # # and thus we need to add a new one that will simply $cwd/*
        # if not matches and activated:
        #     matches = self.get_matches(getviewcwd(view)+sep)

        activated = False

        return (matches, sublime.INHIBIT_WORD_COMPLETIONS)

    def get_matches(self, path, escaped_path):

        if escaped_path:
            path = remove_escape_spaces(path)

        pattern = path + '*'
        if debug:
            print ("FSAutocompletion: pattern:", pattern)

        matches = []
        for fname in iglob(pattern):
            completion = os.path.basename(fname)

            if escaped_path:
                completion = escape_scapes(completion)

            text = ''

            if os.path.isdir(fname):
                text = '%s/\tDir' % completion
                if (settings.get('add_slash', True)):
                    completion = completion + '/' # Append the slash for dirs
            else:
                text = '%s\tFile' % completion

            # FIXME:
            # this one is a bit weird
            # for example if there are three files:
            # /quick test
            # /quick test 1
            # /quick test 2
            # and user types 'quick' and asks for compliction
            # he will get all three choises, so far so good,
            # if he selects the first one, everything is fine, but
            # if he selects the second or third, the code completin will replace
            # /quick quick test 1
            # /quick quick test 2
            # I guess the problem is that the first item in the tuple is
            # what should be replaced, but it only works on words and
            # space will break the word boundary

            # last word that will be completed (is highlighted in the box)
            # if the last charcated is a space then it will be the whole word
            # from the last separator
            lastword = path[path.rfind(sep)+1:]

            # difference between the completion and the lastword
            rest = ''

            if path[-1] != ' ':
                lastword = lastword[lastword.rfind(' ')+1:]
                rest = completion[completion.find(lastword):]
            else:
                rest = completion[completion.find(lastword)+len(lastword):]

            if rest.find(' ') != -1:
                completion = rest

            matches.append((text, completion))

        return matches

if __name__ == "__main__":
    import doctest
    doctest.testmod()
