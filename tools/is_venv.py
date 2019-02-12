#!/usr/bin/env python

"""
Return 0 if python appears to be running in python virtual environment
else return 1
"""

import sys


# from https://stackoverflow.com/a/42580137/471376
def is_venv():
    return (hasattr(sys, 'real_prefix')
            or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))

if is_venv():
    print('venv')
else:
    print('normal')
    sys.exit(1)

sys.exit(0)
