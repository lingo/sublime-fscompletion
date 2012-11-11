import sublime_plugin

import os
import os.path
import re
import glob
from os import sep
from itertools import takewhile

# Enable SublimeText2 to complete filesystem paths a la VIM:
# @author Luke Hudson <lukeletters@gmail.com>
# @author Filip Krikava <krikava@gmail.com>
#

# http://vimdoc.sourceforge.net/htmldoc/options.html#'isfname'
FNAME_CHARS =       ('/','\\','.','-','_','+',"'",'#','$','%','{','}','[',']',':','@','!','~','=')
WIN32_FNAME_CHARS = FNAME_CHARS + (',',)
WIN32_ROOTS = re.compile('^[a-zA-Z]:[/\\\\]')
MAX_FILE_LENGTH = 255

def iglob(pattern):
    def either(c):
        return '[%s%s]'%(c.lower(),c.upper()) if c.isalpha() else c

    # pattern = pattern.replace('\\\\ ',' ')
    icase_pattern = ''.join(map(either,pattern))
    return glob.iglob(icase_pattern)

def isfname(ch):
    chars = WIN32_FNAME_CHARS if os.name == 'nt' else FNAME_CHARS
    return ch.isalnum() or (ch in chars)

def hasroot(rpath):
    """
    >>> hasroot('/somepath')
    True
    >>> hasroot('C:/somepath')
    True
    >>> hasroot('C:\somepath')
    True
    >>> hasroot('~/somepath')
    False
    >>> hasroot('somepath')
    False
    """
    return rpath.startswith('/') or \
        WIN32_ROOTS.match(rpath) != None

def isexplicitpath(rpath):
    """
    >>> isexplicitpath('/somepath')
    True
    >>> isexplicitpath('./somepath')
    True
    >>> isexplicitpath('~/somepath')
    True
    >>> isexplicitpath('C:/somepath')
    True
    >>> isexplicitpath('C:\somepath')
    True
    >>> isexplicitpath('somepath')
    False
    """
    return hasroot(rpath) or \
        rpath.startswith('~/') or \
        rpath.startswith('./')

def scanpath(string):
    """
    Return the longest sibstring of str that could be considered as a rpath.

    >>> scanpath('/home')
    '/home'
    >>> scanpath('some text with /home')
    '/home'
    >>> scanpath('some text with filename\ with\ spaces')
    'filename\\\\ with\\\\ spaces'
    >>> scanpath('some text with filename with\ spaces')
    'with\\\\ spaces'
    >>> scanpath('some text with ./filename')
    './filename'
    >>> scanpath('some text with ./filename with spaces')
    './filename with spaces'
    >>> scanpath('some text with wrong filename')
    'some text with wrong filename'
    >>> scanpath('some text ~/Documents')
    '~/Documents'
    >>> scanpath('some text C:\Documents')
    'C:\\\\Documents'
    >>> scanpath('some text C:/Documents')
    'C:/Documents'
    >>> scanpath('some text C:/Documents\ and\ Settings/Directory')
    'C:/Documents\\\\ and\\\\ Settings/Directory'
    >>> scanpath('some text C:/Documents and Settings/Directory')
    'C:/Documents and Settings/Directory'
    """
    rpath = ''
    rstring = string[::-1]
    lastsep = 0
    escaped_path = False

    for i,ch in enumerate(rstring):
        if ch == sep: lastsep = i

        if isfname(ch): 
            rpath += ch
        elif (ch == ' ' and i-lastsep <= MAX_FILE_LENGTH):                
            if isexplicitpath(rpath[::-1]):
                break

            nch = rstring[i+1] if i+1 < len(rstring) else ''

            if nch == '\\':
                escaped_path = True
            elif escaped_path:
                # the current space is not escaped while others were
                break

            rpath += ch
        else:
            break

    return rpath[::-1]

activated = False

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
    Enable SublimeText2 to complete filesystem paths a la VIM:
    """

    def on_query_completions(self, view, prefix, locations):
        global activated

        # Find the current location (of first selection)
        rowcol = view.rowcol(locations[0])
        line = view.line(locations[0])
        # Extract the whole line's text (prefix parameter above isn't enough)
        lstr = view.substr(line)
        lstr = lstr[0:rowcol[1] + 1]

        path = scanpath(lstr)

        if not activated and not isexplicitpath(path):
            return None

        activated = False

        # expand ~ if there is any
        path = os.path.expanduser(path)

        # add current directory if is missing
        if not hasroot(path):
            path = os.path.join(os.getcwd(), path)

        escaped_path = False if path.find('\\ ') == -1 else True
        print escaped_path
        if escaped_path:
            path = path.replace('\\ ',' ')
        print path
        matches = []
        for fname in iglob(path + '*'):
            completion = os.path.basename(fname) 

            if escaped_path:
                completion = completion.replace(' ', '\\ ')

            text = ''

            if os.path.isdir(fname):
                text = '%s/\tDir' % completion
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
            if completion.count(' ') > 1:
                completion = completion[completion.find(' ')+1:]

            matches.append((text, completion))

        return matches


if __name__ == "__main__":
    import doctest
    doctest.testmod()