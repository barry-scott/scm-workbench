'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_exceptions.py

'''
class WorkBenchError(Exception):
    def __init__( self, msg ):
        Exception.__init__( self, msg )

class InternalError(WorkBenchError):
    def __init__( self, msg ):
        WorkBenchError.__init__( self, msg )

#
#    Helper class to cut down code bloat.
#
#    in __init__ add:
#        self.try_wrapper = wb_exceptions.TryWrapperFactory( log )
#
#    where binding an EVT code as:
#
#        xxx.connnect( self.try_wrapper( self.OnSize ) )
#
class TryWrapperFactory:
    def __init__( self, log ):
        self.log = log

    def __call__( self, function ):
        return TryWrapper( self.log, function )

class TryWrapper:
    def __init__( self, log, function ):
        self.log = log
        self.function = function

    def __call__( self, *params, **keywords ):
        try:
            result = self.function( *params, **keywords )
            return result

        except Exception:
            self.log.exception( 'TryWrapper<%s.%s>\n' %
                (self.function.__module__, self.function.__name__ ) )

            return None
