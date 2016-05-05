#!/usr/bin/env python
import sys
import os
os.environ[ 'PYLINTHOME' ] = 'pylint.d'
from pylint import lint
lint.Run( ['--rcfile=./pylintrc'] + sys.argv[1:] )
