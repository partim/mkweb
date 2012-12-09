"""Working with images."""

import os
import subprocess

from weblib.conf import config
from weblib.document import StaticDocument

class ImageDocument(StaticDocument):
    def convert(self, target, force=False):
        source_path, target_path, make = self.prepare_target(target)
        if make or force:
            subprocess.call(("convert", source_path, target_path))

    def resize(self, target, width, height, force=False):
        source_path, target_path, make = self.prepare_target(target)
        if make or force:
            subprocess.call(("convert", source_path, "-resize",
                             "%ix%i" % (width, height), target_path))

