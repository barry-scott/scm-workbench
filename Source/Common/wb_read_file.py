'''
 ====================================================================
 Copyright (c) 2005-2010 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_read_file.py

'''
import locale
import codecs

import wb_platform_specific

def readFileContentsAsUnicode( filename ):
    f = open( filename, 'rb' )
    contents = f.read()
    f.close()

    return contentsAsUnicode( contents )

def contentsAsUnicode( contents ):
    encoding = encodingFromContents( contents )

    try:
        return contents.decode( encoding )

    except UnicodeDecodeError:
        try:
            # use the choosen encoding and replace chars in error
            return contents.decode( encoding, 'replace' )

        except UnicodeDecodeError:
            # fall back to latin-1
            return contents.decode( 'iso8859-1', 'replace' )

def encodingFromContents( contents ):
    if( len(contents) > len(codecs.BOM_UTF8)
    and contents[0:len(codecs.BOM_UTF8)] == codecs.BOM_UTF8 ):
        encoding = 'utf-8'

    elif( len(contents) > len(codecs.BOM_UTF16_LE)
    and contents[0:len(codecs.BOM_UTF16_LE)] in [codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE]):
        encoding = 'utf-16'

    elif( len(contents) > len(codecs.BOM_UTF32_LE)
    and contents[0:len(codecs.BOM_UTF32_LE)] in [codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE]):
        encoding = 'utf-32'

    else:
        encoding = locale.getdefaultlocale()[1]

        # Mac says mac-roman when utf-8 is what is required
        if encoding == 'mac-roman':
            encoding = 'utf-8'

    if encoding is None:
        encoding = 'iso8859-1'

    return encoding
