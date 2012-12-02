import os
import os.path
import re
import glob
from os import sep
from itertools import takewhile

# http://vimdoc.sourceforge.net/htmldoc/options.html#'isfname'
FNAME_CHARS =       ('/','\\','.','-','_','"',"'",'+','#','$','%','{','}','[',']',':','@','!','~','=')
WIN32_FNAME_CHARS = FNAME_CHARS + (',',)
WIN32_ROOTS = re.compile('^[a-zA-Z]:[/\\\\]')
MAX_FILE_LENGTH = 255

def iglob(pattern):
    def either(c):
        return '[%s%s]'%(c.lower(),c.upper()) if c.isalpha() else c

    # pattern = pattern.replace('\\\\ ',' ')
    icase_pattern = ''.join(map(either,pattern))
    return glob.iglob(icase_pattern)

def isfnamespec(ch):
    chars = WIN32_FNAME_CHARS if os.name == 'nt' else FNAME_CHARS
    return ch in chars

def isfname(ch):
    return ch.isalnum() or isfnamespec(ch)

def hasnext(itr):
    """
    >>> hasnext(iter([1,2,3]))
    True
    >>> hasnext(iter([]))
    False
    """

    try:
        next(itr)
        return True
    except StopIteration:
        return False

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

def ispathescaped(path):
    """
    Returns true if all spaces in the path are escaped.

    >>> ispathescaped(r'\\\\ catch')
    False
    >>> ispathescaped(r'\\\\\ nocatch')
    True
    >>> ispathescaped(r'\\ \\ \\ space\\ \\ escaped')
    True
    >>> ispathescaped('')
    False
    >>> ispathescaped('string')
    False
    >>> ispathescaped(r'simple\\ escape')
    True
    >>> ispathescaped('simple nonescape')
    False
    >>> ispathescaped(r'almost\\ all\\ spaces escaped')
    False
    """

    has_spaces = False
    i = 0
    while i < len(path):
        ch = path[i]
        nch = path[i+1] if i+1 < len(path) else None

        # print i,ch,nch

        if ch == '\\' and nch == '\\':
            i += 2
        elif ch == '\\' and nch == ' ':
            has_spaces = True
            i += 2
        elif ch == ' ':
            return False
        else:
            i += 1

    return has_spaces

def scanpath(string):
    """
    Return the longest sibstring of str that could be considered as a rpath.

    >>> scanpath(r'with spaces\\\\ home')
    'with spaces\\\\\\\\ home'
    >>> scanpath(r'with spaces\\\\\\ home')
    'spaces\\\\\\\\\\\\ home'
    >>> scanpath('/home')
    '/home'
    >>> scanpath('some text with /home')
    '/home'
    >>> scanpath(r'some text with filename\\ with\\ spaces')
    'filename\\\\ with\\\\ spaces'
    >>> scanpath(r'some text with filename with\\ spaces')
    'with\\\\ spaces'
    >>> scanpath(r'some\\ text with spaces')
    'some\\\\ text with spaces'
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
    >>> scanpath(r'some text C:/Documents\\ and\\ Settings/Directory')
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
                # the number of following \ must be even in order for the current \
                # to be the escape for the space
                next = ''.join([r for r in rstring[i+2:] if r == '\\'])
                if (next.count('\\') & 1) != 1:
                    escaped_path = True
                elif escaped_path:
                    # the current space is not escaped while others were
                    break
            elif escaped_path:
                break

            rpath += ch
        else:
            break

    return rpath[::-1]

def remove_escape_spaces(path):
    return path.replace('\\ ',' ')

def escape_scapes(path):
    return path.replace(' ', '\\ ')

def fuzzypath(path, aglob=iglob):
    """
    Tries to find the longest possible path that actually contains some elements

    @param path to be checked. All space escapes must be removed

    >>> fuzzypath('some precceding test[[[[test', lambda f: iter(['testing']) if f == 'test*' else iter([]))
    'test'
    >>> fuzzypath('[test', lambda f: iter(['testing']) if f == 'test*' else iter([]))
    'test'
    >>> fuzzypath('[ttest', lambda f: iter(['testing']) if f == 'test' else iter([]))
    >>> fuzzypath('[some text ttest', lambda f: iter(['testing']) if f == 'test*' else iter([]))
    >>> fuzzypath('[some text test', lambda f: iter(['testing']) if f == 'test*' else iter([]))
    'test'
    >>> fuzzypath('[/', lambda f: iter(['testing']) if f == '/*' else iter([]))
    '/'
    >>> fuzzypath('/', lambda f: iter(['testing']) if f == '/*' else iter([]))
    '/'
    >>> fuzzypath('/file', lambda f: iter(['testing']) if f == '/file*' else iter([]))
    '/file'
    """

    # if we start with root, try it as well
    bpath = remove_escape_spaces(path)
    if hasnext(aglob(bpath+'*')):
        return path

    for i in range(len(path)):
        ch = path[i]
        if isfnamespec(ch) or ch == ' ':
            apath = path[i+1:] if i+1 < len(path) else path[i:]
            # path without escapes - the one we want to check
            bpath = remove_escape_spaces(apath)
            # print apath
            if len(bpath) and hasnext(aglob(bpath+'*')):
                return apath

    return None

if __name__ == "__main__":
    import doctest
    doctest.testmod()
