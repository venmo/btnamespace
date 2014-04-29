import logging

from ._version import __version__
from .namespace import Namespace
from .shared import NamespaceError

# appease flake8
(Namespace, NamespaceError, __version__)

__title__ = 'btnamespace'
__author__ = 'Simon Weber'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014 Venmo'


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# Set default logging handler to avoid "No handler found" warnings.
try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logger.addHandler(NullHandler())
