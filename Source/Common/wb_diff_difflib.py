'''
 ====================================================================
 Copyright (c) 2003-2010 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_diff_difflib.py

'''
import sys
import re
import difflib
import wb_exceptions
import wb_read_file

# define what "junk" means

def IS_LINE_JUNK(line, pat=None):
    return False

def IS_CHARACTER_JUNK(ch, ws=" \t"):
    return False

class Difference:
    'Difference'
    def __init__( self, text_body ):
        self.text_body = text_body

    # meant for dumping lines
    def dump( self, fn, x, lo, hi ):
        for i in range(lo, hi):
            fn( x[i] )

    def plain_replace( self, a, alo, ahi, b, blo, bhi ):
        assert alo < ahi and blo < bhi
        # dump the shorter block first -- reduces the burden on short-term
        # memory if the blocks are of very different sizes
        if bhi - blo < ahi - alo:
            self.dump(self.text_body.addInsertedLine, b, blo, bhi)
            self.dump(self.text_body.addDeletedLine, a, alo, ahi)
        else:
            self.dump(self.text_body.addDeletedLine, a, alo, ahi)
            self.dump(self.text_body.addInsertedLine, b, blo, bhi)

    # When replacing one block of lines with another, this guy searches
    # the blocks for *similar* lines; the best-matching pair (if any) is
    # used as a synch point, and intraline difference marking is done on
    # the similar pair.  Lots of work, but often worth it.

    def fancy_replace( self, a, alo, ahi, b, blo, bhi):

        # don't synch up unless the lines have a similarity score of at
        # least cutoff; best_ratio tracks the best score seen so far
        best_ratio, cutoff = 0.51, 0.52
        cruncher = difflib.SequenceMatcher(IS_CHARACTER_JUNK)
        eqi, eqj = None, None   # 1st indices of equal lines (if any)

        # search for the pair that matches best without being identical
        # (identical lines must be junk lines, & we don't want to synch up
        # on junk -- unless we have to)
        for j in xrange(blo, bhi):
            bj = b[j]
            cruncher.set_seq2(bj)
            for i in xrange(alo, ahi):
                ai = a[i]
                if ai == bj:
                    if eqi is None:
                        eqi, eqj = i, j
                    continue
                cruncher.set_seq1(ai)
                # computing similarity is expensive, so use the quick
                # upper bounds first -- have seen this speed up messy
                # compares by a factor of 3.
                # note that ratio() is only expensive to compute the first
                # time it's called on a sequence pair; the expensive part
                # of the computation is cached by cruncher
                if( cruncher.real_quick_ratio() > best_ratio
                and cruncher.quick_ratio() > best_ratio
                and cruncher.ratio() > best_ratio ):
                    best_ratio, best_i, best_j = cruncher.ratio(), i, j

        if best_ratio < cutoff:
            # no non-identical "pretty close" pair
            if eqi is None:
                # no identical pair either -- treat it as a straight replace
                self.plain_replace( a, alo, ahi, b, blo, bhi )
                return
            # no close pair, but an identical pair -- synch up on that
            best_i, best_j, best_ratio = eqi, eqj, 1.0
        else:
            # there's a close pair, so forget the identical pair (if any)
            eqi = None

        # a[best_i] very similar to b[best_j]; eqi is None iff they're not
        # identical

        # pump out diffs from before the synch point
        self.fancy_helper( a, alo, best_i, b, blo, best_j )

        # do intraline marking on the synch pair
        aelt, belt = a[ best_i ], b[ best_j ]
        if eqi is None:
            self.text_body.addChangedLineBegin()

            cruncher.set_seqs( aelt, belt )
            for tag, ai1, ai2, bj1, bj2 in cruncher.get_opcodes():
                la, lb = ai2 - ai1, bj2 - bj1
                if tag == 'replace':
                    self.text_body.addChangedLineReplace( aelt[ai1:ai2], belt[bj1:bj2] )
                elif tag == 'delete':
                    self.text_body.addChangedLineDelete( aelt[ai1:ai2] )
                elif tag == 'insert':
                    self.text_body.addChangedLineInsert( belt[bj1:bj2] )
                elif tag == 'equal':
                    self.text_body.addChangedLineEqual( belt[bj1:bj2] )
                else:
                    raise ValueError( 'unknown tag ' + str(tag) )

            self.text_body.addChangedLineEnd()
        else:
            self.text_body.addNormalLine( aelt )

        # pump out diffs from after the synch point
        self.fancy_helper(a, best_i+1, ahi, b, best_j+1, bhi)

    def fancy_helper( self, a, alo, ahi, b, blo, bhi):
        if alo < ahi:
            if blo < bhi:
                self.fancy_replace( a, alo, ahi, b, blo, bhi)
            else:
                self.dump(self.text_body.addDeletedLine, a, alo, ahi)
        elif blo < bhi:
            self.dump(self.text_body.addInsertedLine, b, blo, bhi)

    def fail(self, msg):
        out = sys.stderr.write
        out(msg + "\n\n")
        return 0

    # filename can be a list of lines of the name of a file to open
    def filecompare( self, filename_left, filename_right ):
        if type(filename_left) == type([]):
            lines_left = filename_left
        else:
            try:
                lines_left = wb_read_file.readFileContentsAsUnicode( filename_left ).split('\n')

            except IOError( detail ):
                print( 'Error opening %s\n%s' % (filename_left, detail) )
                return 0

        if type(filename_right) == type([]):
            lines_right = filename_right
        else:
            try:
                lines_right = wb_read_file.readFileContentsAsUnicode( filename_right ).split('\n')

            except IOError( detail ):
                print( 'Error opening %s\n%s' % (filename_right, detail) )
                return 0

        lines_left = [eolRemoval( line ) for line in lines_left]
        lines_right = [eolRemoval( line ) for line in lines_right]



        matcher = difflib.SequenceMatcher( IS_LINE_JUNK, lines_left, lines_right )
        for tag, left_lo, left_hi, right_lo, right_hi in matcher.get_opcodes():
            if tag == 'replace':
                self.fancy_replace( lines_left, left_lo, left_hi, lines_right, right_lo, right_hi )
            elif tag == 'delete':
                self.dump( self.text_body.addDeletedLine, lines_left, left_lo, left_hi )
            elif tag == 'insert':
                self.dump( self.text_body.addInsertedLine, lines_right, right_lo, right_hi )
            elif tag == 'equal':
                self.dump( self.text_body.addNormalLine, lines_left, left_lo, left_hi )
            else:
                raise ValueError( 'unknown tag ' + str( tag ) )

        self.text_body.addEnd()
        return 1

# need to strip any \n or \r thats on the end of the line
def eolRemoval( line ):
    while line and line[-1] in ['\n','\r']:
        line = line[:-1]
    return line
