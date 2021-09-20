Edit the Wiki
===========

Whenever a module is edited or created, please add it to or edit it in the wiki. For this purpose:

1. Clone the *River Architect Wiki*: `git clone https://github.com/RiverArchitect/RA_wiki.git`
1. Modify the wiki markdown files which are located in `RA_wiki/wiki/*.md` ([see conventions](#convent) and [documenting a new module](#newmod))
1. If necessary, edit the sidebar located in `RA_wiki/_includes/own/sidebar.html`
1. Push changes:

```
git add .
git commit -m "Leave a message"
git pull --rebase
git push
```

Please note: if `git pull --rebase` encounters problems, issues will be highlighted in the edited markdown / HTML files.


# Documentation conventions <a name="convent"></a>

For editing markdown documents, we recommend using [Notepad++](https://notepad-plus-plus.org) with [Editoria's markdown syntax style](https://github.com/Edditoria/markdown-plus-plus).
Please be graphically descriptive and add figures to facilitate understanding your coding brilliance. For adding images, upload them to the *River Architect* [Media/images](https://github.com/RiverArchitect/Media) (yes, you will need to clone this repository, too - [read more about using `git`](DevGit)). Images can then be implemented in markdown file with:<br/>

`![img_name](https://github.com/RiverArchitect/Media/raw/master/images/NEW_IMAGE.PNG)`

Finally, please use grammar and spell checker before pushing changes.

# Document a new module <a name="newmod"></a>

For adding new module documentation, create a new markdown file (e.g., `RA_wiki/wiki/NewModule.md`). Describe the new module in the following order:

1. Overview
1. QuickGuide (normal usage - please add screenshots)
1. Output (Products)
1. Detailed descriptions / extended usage (e.g., equations and technical details)


**Document Warning and Error messages** prompted in `try:` - `except:` statements with `self.logger.info("ERROR: Message")` ([see example in the module development Wiki](DevModule#tryexcept)). When writing new code, it is better to use precise exception rules such as `except ValueError:`. We often use the broad "shotgun" approach with `except:` only because we encountered unexpected exception types using `arcpy`. A better and future way of error message logging in *River Architect* will be to use `self.logger.error()` in the exception statement rather than `self.logger.info()`, which should exclusively be used to log calculation progress. **Important is to add error messages, as well as warning messages, to the [Troubleshooting Wiki](Troubleshooting)**. Use warning messages when a function can still work even though a variable assignment error occurred such as when an optional, additional raster is missing.









