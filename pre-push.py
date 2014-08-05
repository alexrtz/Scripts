#!/usr/bin/env python

import fileinput
import os
import sys
import subprocess
import re

# with open(fname) as f:
#    content = f.readlines()

# >>> s1 = ['bacon\n', 'eggs\n', 'ham\n', 'guido\n']
# >>> s2 = ['python\n', 'eggy\n', 'hamster\n', 'guido\n']
# >>> for line in unified_diff(s1, s2, fromfile='before.py', tofile='after.py'):
# ...     sys.stdout.write(line)
# --- before.py
# +++ after.py
# @@ -1,4 +1,4 @@
# -bacon
# -eggs
# -ham
# +python
# +eggy
# +hamster
#  guido


def astyle_and_diff(filename):
    # TODO: sanitize input
    subprocess.call("astyle --options=options.astyle < {0}  > {0}.new".format(filename), shell=True)
    # Use the Python builtin diff instead
    process = subprocess.Popen("diff -u {0} {0}.new|grep -E \"^(\\+|\\-)\"".format(filename), shell=True, stdout=subprocess.PIPE)
    subprocess.call("", shell=True)
    diffout = process.communicate()[0]
    diffout.rstrip()
    return diffout


def get_remote_file(filename, remote_sha):
    # TODO: sanitize input
    subprocess.check_call("git show {0}:{1} > {1}.remote".format(remote_sha, filename), shell=True)
    return "{0}.remote".format(filename)


def check_modified_file(filename, remote_sha):
    remote_filename = get_remote_file(filename, remote_sha)
    return [astyle_and_diff(remote_filename), astyle_and_diff(filename)]


def check_file(filename):
    return astyle_and_diff(filename)


local_ref, local_sha, remote_ref, remote_sha = sys.stdin.read().rstrip().split(" ")

p = subprocess.Popen("git show --name-status --oneline", shell=True, stdout=subprocess.PIPE)
lines = p.communicate()[0].split("\n")
# We don't care about the 1st line (commit hash and message)
lines.pop()

files = []

for line in lines:
    if line == '':
        break
    if re.match("(.*\.cc|.*\.cpp|.*\.hh|.*\.hpp)", line):
        # The output of the show command we ran is action\tfile, where 'action'
        # is A for and added file, M for a modified one, ...
        files.append(line.split('\t'))


diffs_modified = []
diffs_new = []

for action, filename in files:

    if remote_sha == "0000000000000000000000000000000000000000" or action == 'A':
        diff = check_file(filename)
        if diff != "":
            diffs_new.append([filename, diff])
    else:
        diffs_remote_local = check_modified_file(filename, remote_sha)

        # New bad formatted code has been introduced
        if len(diffs_remote_local[0]) < len(diffs_remote_local[1]):
            diffs_modified.append(filename)

if len(diffs_new) != 0 or len(diffs_modified) != 0:
    for diff in diffs_new:
        print "The file \"{0}\" is not compliant to the coding style\n{1}".format(diff[0], diff[1])

    for diff in diffs_modified:
        print "You introduced wrongly formatted code in {0}.".format(diff)

    print "Please fix this before trying to push again"

    sys.exit(1)
