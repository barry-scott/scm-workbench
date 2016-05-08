#!/usr/bin/python3
import sys

import git

r = git.Repo( sys.argv[1] )

index = r.index

verbose = '-v' in sys.argv[2:]

print( 'Changes to be committed:' )
for diff in r.index.diff( r.head.commit ):
    if verbose:
        print( '-'*50 )
        for name in dir(diff):
            if name[0] not in '_N' and name not in ('re_header',):
                print( '   %s: %r' % (name, getattr( diff, name )) )

    if diff.renamed:
        print( '        renamed:    %s -> %s' % (diff.b_path, diff.a_path) )

    elif diff.deleted_file:
        print( '        new file:   %s' % (diff.b_path,) )
        
    elif diff.new_file:
        print( '        deleted :   %s' % (diff.b_path,) )

    else:
        print( '        modified:   %s' % (diff.b_path,) )
        
print()
print( 'Changes not staged for commit:' )
for diff in r.index.diff( None ):
    if diff.deleted_file:
        print( '        deleted:    %s' % (diff.a_path,) )

    else:
        print( '        modified:   %s' % (diff.a_path,) )

    if verbose:
        print( '-'*50 )
        for name in dir(diff):
            if name[0] not in '_N' and name not in ('re_header',):
                print( '   %s: %r' % (name, getattr( diff, name )) )

print()
print( 'Untracked files:' )
for filename in r.untracked_files:
    print( '        %s' % (filename,) )
