Using `git`
===========

For developing *River Architect*, the first step is to become a contributor by <a class="page-scroll" href="mailto:river.architect.program@gmail.com">contacting us</a>. For direct contact, please do not hesitate to contact us by finding prof. Greg Pasternack on the annual AGU meetings!

Using `git` brings many advantages for developers (nothing gets lost) and for users (consistent code). *River Architect* implies multiple repositories, which should be cloned and used in line with the descriptions in the Wiki for developers:

-	The Wiki: `https://github.com/RiverArchitect/RA_wiki.git`
-	Media (presentations and images): `https://github.com/RiverArchitect/Media.git`
-	The website hosted on GitHub pages: `https://github.com/RiverArchitect/RiverArchitect.github.io.git`
-	The main program (this is downloaded when clicking the `Download` button on the website): `https://github.com/RiverArchitect/program.git`
-	Sample data are provided with `https://github.com/RiverArchitect/SampleData.git`
-	Templates for developers are in `https://github.com/RiverArchitect/development.git`

To download, modify and push changes to *River Architect* download and install [*Git Bash*](https://git-scm.com/downloads). *GitHub* provides detailed descriptions and standard procedures to work with their repositories ([read more](https://help.github.com/en/articles/cloning-a-repository)). The following "recipe" guides through the first time installation (cloning) of *River Architect*:

1. Open *Git Bash*
1. Type `cd "D:/Target/Directory/"` to change to the target installation directory (recommended: `cd "D:/Python/RiverArchitect/"`). If the directory does not exist, it can be created in the system explorer (right-click in empty space > `New >` > `Folder`).
1. Clone the repository: `git clone https://github.com/RiverArchitect/program`

**Now is the moment to modify the source code (e.g., [modify or add new modules](DevModule#addmod)).** After finalizing and testing (push **debugged** code only!) new code, go back to *Git Bash* and type:

1. `git status` - this shows the modifications made.
1. If the status seems OK with the consciously made changes, type `git add .`; if only single files were changed, use `git add filename.py` instead. Best solution: use a local [gitignore file](https://help.github.com/en/github/using-git/ignoring-files).
1. Commit changes `git commit -m "Leave a message"` - leave a significant and precise short message.
1. `git pull --rebase` - if locally edited scripts were modified remotely since the last pull, this will prompt issues and highlight problematic section with `>>>`. Manually open concerned files and resolve the issues (delete invalid `>>>` highlights).
1. `git push`

Done. Close *Git Bash*.

Push only relevant files and consider using a [`.gitignore`](https://git-scm.com/docs/gitignore) file. *River Architect* already comes with a `.gitignore` file that excludes `.pyc` (compiled bytecodes) and `.log` (logfiles) files. To exclude local subdirectories from `git push`, or directory patterns, add them as follows (replace `pattern2ignore` and `directory2ignore` with folder names):

```

*.pyc
*.log
**/pattern2ignore/
/directory2ignore/

```

Being a small developer team, we are currently not using [`git` branching](https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell). This may change in the future ...

