import os
import sys

if len(sys.argv) < 2:
    os.environ['site'] = input('Please Enter the site: ')
else:
    os.environ['site'] = sys.argv[1]
