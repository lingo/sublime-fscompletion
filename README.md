# FileSystem AutoCompletion #

Enable auto-completion of paths from the file system à la [VIM](http://vimdoc.sourceforge.net/htmldoc/insert.html#i_CTRL-X_CTRL-F).

Depending on the path, the file completion can be trigged automatically using the default <kbd>Ctrl</kbd>+<kbd>Space</kbd> auto-completion or it can be explicitly triggered by <kbd>Ctrl</kbd>+<kbd>Alt</kbd>+<kbd>/</kbd> (on OSX, <kbd>Cmd</kbd> instead of <kbd>Ctrl</kbd>) shortcut. 

This combination can be always rebound to a different key combination in usual SublimeText manner, by opening the User keybindings file (see menu: `Preferences/Package Settings/FileSystem Autocompletion`). 

For example, you should also be able to use the Vim shortcut <kbd>Ctrl</kbd>+<kbd>X</kbd>,<kbd>Ctrl</kbd>+<kbd>F</kbd> by adding the following to your **Keybindings - User** file:

```json
   { "keys": ["ctrl+x","ctrl+f"], "command": "file_system_comp_trigger"}
```

This plugin handles spaces in file names and find the correct file path beginning. If you find any problem, please open an issue.

## Current directory ##
The project-file directory will be used by default (if found).
However, a path starting with '.' will use the current view's directory instead.
The path search order can be configured via the usual settings file:

    "path_search_order": ["project", "view", "window"]

## Installation ##
Either by using the package manager or manually by cloning/downloading the latest snapshot of the `master` branch into the Sublime's package folder (e.g. `~/Library/Application Support/Sublime Text 2/Packages/` on OSX).

## Default auto-completion ##

If the path has a root, this means it starts with `./`, `~/`, `/` (or `C:\` (`C:/` on win32) the auto completion will be triggered automatically using the regular auto-complete command.

## Triggered file auto-completion ##

For relative paths, the file path auto-completion can be triggered by hitting <kbd>Ctrl</kbd>+<kbd>X</kbd>, <kbd>Ctrl</kbd>+<kbd>F</kbd>. This is because we do not want to collide with the other auto-completion.

## Spaces ##

This plugin should handle file paths that contains spaces including escaped spaces with `\`.

For example if there are three files:

    quick test
    quick test 1
    quick test 2

Then `quick test` followed by <kbd>Ctrl</kbd>+<kbd>X</kbd>, <kbd>Ctrl</kbd>+<kbd>F</kbd> will display all three options and when selecting the second one for instance it will get expanded to `quick test 1`. On the other hand `quick\ test` followed by <kbd>Ctrl</kbd>+<kbd>X</kbd>, <kbd>Ctrl</kbd>+<kbd>F</kbd> with the same selection will be expanded to `quick\ test\ 1`. If the path is detected to be escaped it will continue to escape all the followed spaces.

## File path beginning ##

The problem is that a file name can be contain many special characters. For example `\input{some file}` is a valid file. However, it is also a way how to include a file in LaTeX document and more likely we want to have a completion of the path `some file` rather than path `\input{some file}`. This plugin, therefore, tries to determine the beginning of a path from which it should look for the completion by finding the longest possible path that exists. For the example above, with the cursor positioned at the end of `some file`, it will try:

    /Users/user/\input{some file
    Users/user/\input{some file
    krikava/\input{some file
    \input{some file
    input{some file
    some file
    file

and it will stop as soon as any of these path exists (a glob pattern with appended `*` returns something).

## License ##

All parts of this plugin are licensed under GPL v3 (see LICENSE.txt).
