import glob
import os
import re


PATH_SEPARATORS = ('/', '\\')
FNAME_CHARS = ('/', '\\', '.', '-', '_', '"', "'", '+', '#', '$', '%', '*', '?',
               '{', '}', '[', ']', ':', '@', '!', '~', '=')
WIN32_FNAME_CHARS = FNAME_CHARS + (',',)
MAX_FILE_LENGTH = 255

_DRIVE_ROOT = re.compile(r'^[a-zA-Z]:[\\/]')
_UNC_ROOT = re.compile(r'^(?:\\\\|//)[^\\/]+[\\/][^\\/]+')


def _split_drive(path):
    """Split a Windows drive even when this module is tested on another OS."""
    drive, tail = os.path.splitdrive(path)
    if not drive and _DRIVE_ROOT.match(path):
        return path[:2], path[2:]
    return drive, tail


def _case_insensitive_literal_pattern(path):
    drive, tail = _split_drive(path)
    parts = []
    for character in tail:
        if character.isalpha():
            parts.append('[{}{}]'.format(character.lower(), character.upper()))
        else:
            parts.append(glob.escape(character))
    return drive + ''.join(parts)


def iglob(prefix):
    """Return case-insensitive, literal-prefix matches without altering a drive."""
    return glob.iglob(_case_insensitive_literal_pattern(prefix) + '*')


def isfnamespec(ch):
    chars = WIN32_FNAME_CHARS if os.name == 'nt' else FNAME_CHARS
    return ch in chars


def isfname(ch):
    return ch.isalnum() or isfnamespec(ch)


def hasnext(itr):
    try:
        next(itr)
        return True
    except StopIteration:
        return False


def hasroot(path):
    """Whether *path* starts at a POSIX, drive, rooted-Windows, or UNC root."""
    return bool(path) and (
        path.startswith('/') or
        path.startswith('\\') or
        _DRIVE_ROOT.match(path) is not None or
        _UNC_ROOT.match(path) is not None
    )


def isexplicitpath(path):
    return hasroot(path) or path == '~' or path.startswith(('~/', '~\\', './',
                                                             '.\\', '../', '..\\'))


def ispathescaped(path):
    """Return true only when every space in *path* is escaped with ``\\``."""
    has_spaces = False
    for index, char in enumerate(path):
        if char != ' ':
            continue
        slash_count = 0
        previous = index - 1
        while previous >= 0 and path[previous] == '\\':
            slash_count += 1
            previous -= 1
        if slash_count % 2 == 0:
            return False
        has_spaces = True
    return has_spaces


def scanpath(text):
    """Return the path-like suffix of *text*."""
    rpath = ''
    reverse_text = text[::-1]
    last_separator = 0
    escaped_path = False

    for index, char in enumerate(reverse_text):
        if char in PATH_SEPARATORS:
            last_separator = index
        if isfname(char):
            rpath += char
            continue
        if char != ' ' or index - last_separator > MAX_FILE_LENGTH:
            break
        if isexplicitpath(rpath[::-1]):
            break

        slash_count = 0
        cursor = index + 1
        while cursor < len(reverse_text) and reverse_text[cursor] == '\\':
            slash_count += 1
            cursor += 1
        if slash_count % 2:
            escaped_path = True
        elif escaped_path:
            break
        rpath += char
    return rpath[::-1]


def remove_escape_spaces(path):
    return path.replace('\\ ', ' ')


def escape_spaces(path):
    return path.replace(' ', '\\ ')


def _join_base(path, cwd):
    return path if hasroot(path) else os.path.join(cwd, path)


def fuzzypath(path, cwd, aglob=iglob):
    """Find the longest path-like suffix that has filesystem matches."""
    if not cwd and not hasroot(path):
        return None
    path = _join_base(path, cwd)
    if hasnext(aglob(remove_escape_spaces(path))):
        return path

    for index, char in enumerate(path):
        if char == ' ' or (isfnamespec(char) and char not in PATH_SEPARATORS):
            candidate = path[index + 1:]
            if not candidate:
                continue
            candidate = _join_base(candidate, cwd)
            if hasnext(aglob(remove_escape_spaces(candidate))):
                return candidate
    return None
