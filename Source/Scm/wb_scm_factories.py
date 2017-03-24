'''
 ====================================================================
 Copyright (c) 2003-2017 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_scm_factories.py

'''

def allScmFactories():
    all_factories = []
    all_messages = []

    try:
        import wb_git_factory
        all_factories.append( wb_git_factory.WbGitFactory() )

    except ImportError as e:
        all_messages.append( 'Git is not available - %s' % (e,) )

    try:
        import wb_hg_factory
        all_factories.append( wb_hg_factory.WbHgFactory() )

    except ImportError as e:
        all_messages.append( 'Mercurial (hg) is not available - %s' % (e,) )

    try:
        import wb_svn_factory
        all_factories.append( wb_svn_factory.WbSvnFactory() )

    except ImportError as e:
        all_messages.append( 'Subversion (svn) is not available - %s' % (e,) )

    return all_factories, all_messages
