
#------------------------------------------------------------
#
#   progress reporting API
#
#------------------------------------------------------------
class WbScmProgress:
    def __init__( self, status_widget ):
        self.status_widget = status_widget
        self.progress_format = None

        self.__total = None
        self.__event_count = None
        self.__in_conflict = None

        self.status_widget.setText( '' )

    def start( self, fmt, total=0 ):
        self.progress_format = fmt

        self.__total = total
        self.__event_count = 0
        self.__in_conflict = 0

        self.__updateStatusCtrl()

    def __updateStatusCtrl( self ):
        if self.progress_format is None:
            return

        progress_values = {
            'count':    self.__event_count,
            'conflict': self.__in_conflict,
            'total':    self.__total,
            }
        if self.__total > 0:
            progress_values['percent'] = self.__event_count*100/self.__total

        self.status_widget.setText( self.progress_format % progress_values )

    def incEventCount( self ):
        self.__event_count += 1
        self.__updateStatusCtrl()

    def getEventCount( self ):
        return self.__event_count

    def incInConflictCount( self ):
        self.__in_conflict += 1
        self.__updateStatusCtrl()

    def getInConflictCount( self ):
        return self.__in_conflict

    def end( self ):
        self.status_widget.setText( '' )
