"""
Runs partition on the input MS
"""
import os,sys
sys.path.append(os.getcwd())

from utils import config_parser
from utils.config_parser import validate_args as va
from utils import globals
from utils import bookkeeping

