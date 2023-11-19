# __init__.py

# DRY canonical information

__author__ = "James Thomas Moon"
__url__ = "https://github.com/jtmoon79/coverlovin2"
__url_source__ = __url__
__url_project__ = "https://pypi.org/project/CoverLovin2/"
__app_name__ = "CoverLovin2"
__version__ = "0.7.4"
__product_token__ = __app_name__ + "/" + __version__
"""
Product Token should follow RFC #1945, used for Discogs requests
https://tools.ietf.org/html/rfc1945#section-3.7
"""
# this __doc__ should be one-line
__doc__ = """Recursively process passed directories of audio media files, attempting\
 to create a missing album image file, either via local searching and\
 copying, or via downloading from various online services."""

NAME = "coverlovin2"
"""recommended by https://packaging.python.org/tutorials/packaging-projects/"""
