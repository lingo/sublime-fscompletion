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


def is_fname_char(ch):
    chars = WIN32_FNAME_CHARS if os.name == 'nt' else FNAME_CHARS
    return ch in chars


def is_fname(ch):
    return ch.isalnum() or is_fname_char(ch)


def has_next(itr):
    try:
        next(itr)
        return True
    except StopIteration:
        return False


def has_root(path):
    """Whether *path* starts at a POSIX, drive, rooted-Windows, or UNC root."""
    return bool(path) and (
        path.startswith('/') or
        path.startswith('\\') or
        _DRIVE_ROOT.match(path) is not None or
        _UNC_ROOT.match(path) is not None
    )


def is_explicit_path(path):
    return has_root(path) or path == '~' or path.startswith(('~/', '~\\', './',
                                                             '.\\', '../', '..\\'))


def is_path_escaped(path):
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


def _is_escaped_space(reversed_text, space_index):
    """Whether the space at *space_index* is preceded by an odd ``\\`` run."""
    backslash_count = 0
    for character in reversed_text[space_index + 1:]:
        if character != '\\':
            break
        backslash_count += 1
    return bool(backslash_count % 2)


def scanpath(text):
    """Return the path-like suffix of *text*.

    Scan backwards from the cursor so that completion receives only the final
    path candidate.  An escaped space may be part of a relative path; ordinary
    spaces are included only after an explicit path prefix has been found.
    """
    reversed_text = text[::-1]
    reversed_path = []
    nearest_separator = 0
    found_escaped_space = False

    for index, character in enumerate(reversed_text):
        if character in PATH_SEPARATORS:
            nearest_separator = index

        if is_fname(character):
            reversed_path.append(character)
            continue

        if character != ' ' or index - nearest_separator > MAX_FILE_LENGTH:
            break
        if is_explicit_path(''.join(reversed(reversed_path))):
            break

        if _is_escaped_space(reversed_text, index):
            found_escaped_space = True
        elif found_escaped_space:
            break
        reversed_path.append(character)

    return ''.join(reversed(reversed_path))


def remove_escape_spaces(path):
    return path.replace('\\ ', ' ')


def escape_spaces(path):
    return path.replace(' ', '\\ ')


def _join_base(path, cwd):
    return path if has_root(path) else os.path.join(cwd, path)


def fuzzypath(path, cwd, aglob=iglob):
    """Find the longest path-like suffix that has filesystem matches."""
    if not cwd and not has_root(path):
        return None
    path = _join_base(path, cwd)
    if has_next(aglob(remove_escape_spaces(path))):
        return path

    for index, char in enumerate(path):
        if char == ' ' or (is_fname_char(char) and char not in PATH_SEPARATORS):
            candidate = path[index + 1:]
            if not candidate:
                continue
            candidate = _join_base(candidate, cwd)
            if has_next(aglob(remove_escape_spaces(candidate))):
                return candidate
    return None
