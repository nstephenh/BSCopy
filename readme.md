# BSCopy

BScopy is a set if simple scripts to copy changes from one battlescribe .cat file to another.

It assumes you will create a template from one .cat file and use it to apply changes to multiple other cat files.
It also assumes that the only changes you want to copy are selection entry links.
This is generally the case when there is one library cat file and multiple files using entries from each of them
(with visibility or category changes only).

It is not currently production ready (and uses hardcoded file paths).

Use at your own risk. Ensure you have a backup of any .cat files you run through this program.

For instructions on the necessary post-processing to use this on the
current [horus heresy dataset](https://github.com/BSData/horus-heresy/),
please refer to [copy_for_hh_files.md](changes_for_hh_files.md)