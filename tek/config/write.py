import sys
import pkgutil

from tek import logger
from tek.config import Configurations


def write_pkg_config(dir, outfile):
    sys.path[:0] = [dir]
    Configurations.allow_files = False
    Configurations.allow_override = False
    mods = pkgutil.walk_packages([dir], onerror=lambda x: True)
    configs = (name for l, name, ispkg in mods
               if not ispkg and name.rsplit('.', 1)[-1] == 'config')
    for name in configs:
        try:
            mod = __import__(name)
            if hasattr(mod, 'reset_config'):
                mod.reset_config(reset_parent=False)
        except Exception as e:
            logger.debug(e)
    Configurations.write_config(outfile)
