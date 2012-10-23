import sublime_plugin
from glob import iglob
import os
import re

# Enable SublimeText2 to complete filesystem paths a la VIM:
# @author Luke Hudson <lukeletters@gmail.com>
#
# Test cases:
#      /home/
#      C:\abc
#      c:/
#


class FileSystemCompCommand(sublime_plugin.EventListener):
    """
    Enable SublimeText2 to complete filesystem paths a la VIM:
    """

    def on_query_completions(self, view, prefix, locations):

        # Find the current location (of first selection)
        rowcol = view.rowcol(locations[0])
        line = view.line(locations[0])
        # print "rowcol = %s" % str(rowcol)
        # print "line = %s" % line

        # Extract the whole line's text (prefix parameter above isn't enough)
        lstr = view.substr(line)
        lstr = lstr[0:rowcol[1] + 1]

        # Now strip off leading comments or whitespaces.
        lstr = re.sub(r'^[#/*]*[ \t]*', '', lstr)
        preRepl = lstr
        if lstr.find('\\') != -1 or lstr.find(':') != -1:
            lstr = re.sub(r'.*([a-z]:\.*)', r'\1', lstr, re.IGNORECASE)
        elif lstr.find('/') != -1:
            lstr = re.sub(r'[^/]*(.*)', r'\1', lstr)
        else:
            return None
        print "FileSystemCompletion: line was '%s', replaced to '%s'" % (preRepl, lstr)

        # Generate completions from the path found.
        # We return tuples because this should be (label,completion)
        matches = []
        for x in iglob(lstr + "*"):
            y = os.path.basename(x)
            matches.append((y, y))
        return matches
