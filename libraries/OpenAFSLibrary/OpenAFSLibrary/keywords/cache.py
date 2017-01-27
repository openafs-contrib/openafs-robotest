import sys
import os
import re

from robot.api import logger
from OpenAFSLibrary.command import fs

class _CacheKeywords(object):
    """Cache keywords."""

    def get_cache_size(self):
        """Get the cache size.

        Outputs AFS cache size as the number of 1K blocks."""
        s = fs("getcacheparms") # get output string
        size = re.findall('\d+', s) # find the decimal values in the string
        return int(size[1]) # output integer for number of 1K blocks
