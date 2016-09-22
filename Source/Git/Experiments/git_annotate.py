#!/usr/bin/python3
import sys

import git

r = git.Repo( sys.argv[1] )


num = 0

for info in r.blame( 'HEAD', sys.argv[2] ):
    num += 1
    commit = info[0]
    all_lines = info[1]
    print( '%s %6d:%s' % (commit, num, all_lines[0]) )

    for line in all_lines[1:]:
        num += 1
        print( '%*s %6d:%s' % (40, '', num, line) )
