from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("doujinshi-meta")
except PackageNotFoundError:
    __version__ = "unknown"
