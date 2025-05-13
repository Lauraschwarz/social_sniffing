from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("social_sniffing")
except PackageNotFoundError:
    # package is not installed
    pass
