import sys
from .all_settings import *

from . import all_settings

sys.modules['all_settings'] = all_settings
