# FileSysCompletion #

Enable auto-completion of paths from the file system à la [VIM](http://vimdoc.sourceforge.net/htmldoc/insert.html#i_CTRL-X_CTRL-F).

The auto-completion works in two modes: default auto-completion and explicit file path auto-completion.

## Default auto-completion ##

If the path is _explicit_ this means it starts with `./`, `~/`, `/` or on win32 `C:\` (`C:/`) the auto completion will be triggered automatically using the regular auto-complete command.

## Explicit file path auto-completion ##

For relative paths, the file path auto-completion can can be triggered by hitting `Ctrl-x, Ctrl-f`. This is because we do not want to collide with the other auto-completion.

## Spaces ##

This plugin should handle file paths that contains spaces including escaped spaces with `\`.

For example if there are three files:

* `quick test`
* `quick test 1`
* `quick test 2`

Then `quick test` followed by `Ctrl-x, Ctrl-f` will display all three options and when selecting the second one for instance it will get expanded to `quick test 1`. On the other hand `quick\ test` followed by `Ctrl-x, Ctrl-f` with the same selection will be expanded to `quick\ test\ 1`. If the path is detected to be escaped it will continue to escape all the followed spaces.

## License ##

Copyright [Luke Hudson](https://github.com/lingo), [Filip Krikava](https://github.com/fikovnik), all parts of this 
plugin are licensed under GPL v3 (see LICENSE.txt).