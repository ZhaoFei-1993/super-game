import sys
from .all_settings import *
import pymysql

from . import all_settings

sys.modules['all_settings'] = all_settings

pymysql.install_as_MySQLdb()
