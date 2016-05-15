#!/usr/bin/python3
import sys

import git

r = git.Repo( sys.argv[1] )


def printTree( tree, indent=0 ):
    prefix = ' '*indent
    print( prefix, '-' * 16 )
    print( prefix, 'Tree path %s' % (tree.path,) )
    for blob in tree:
        print( prefix, '%s %s (%s)' % (blob.type, blob.path, blob.hexsha) )

    for child in tree.trees:
        printTree( child, indent+4 )

for commit in r.iter_commits( None ):
    print( '=' * 60 )
    for name in sorted( dir( commit ) ):
        if name[0] not in 'abcdefghijklmnopqrstuvwxyz':
            continue

        print( 'Commit: %s: %r' % (name, getattr( commit, name )) )

    print( '-' * 60 )
    stats = commit.stats

    for name in sorted( dir( stats ) ):
        if name[0] not in 'abcdefghijklmnopqrstuvwxyz':
            continue

        print( 'Commit.Stats: %s: %r' % (name, getattr( stats, name )) )


    print( '-' * 60 )
    tree = commit.tree

    printTree( tree )
    
    break
