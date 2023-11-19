#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# app.py
#
# black line length 100
#     $ black -l 100 app.py
#
# … ← ↑ → ↓

"""\
Recursively process subdirectories looking for audio media files. Download
appropriate cover images for the directory that is presumed to be an album.

The author wanted to learn more about the addition of type-hinting in Python.
Code in this file uses several methods of type-hinting.
Some readers might think it's overzealous, others will welcome it.

This also makes use of inheritance decorators @overrides and @abstractmethod.
And other Python 3.x novelties!

Because the author was concentrating on experimentation, the program flow is
somewhat cumbersome, overwrought, and inefficient. However, the program should
accomplish what is needed for the user.
"""

# HACK: Begin workaround for Python's exasperating package+import system.
#       It's easy to get importing working. It's difficult to get it working for the various
#       circumstances of program execution and module packaging.
#       This will satisfy all modes of execution in `tools/build-install-test.sh`.
#       see
#       https://gideonbrimleaf.github.io/2021/01/26/relative-imports-python.html
#       https://stackoverflow.com/questions/2632199/how-do-i-get-the-path-of-the-current-executed-file-in-python
#       https://stackoverflow.com/a/21233334/471376
import inspect
import os.path
import sys

__frame_filename__ = inspect.getframeinfo(inspect.currentframe()).filename
__frame_dirpath__ = os.path.dirname(os.path.relpath(__frame_filename__))
sys.path.insert(0, __frame_dirpath__)

# do relative import
from __init__ import (
    name,
    __url__,
    __url_source__,
    __url_project__,
    __version__,
    __product_token__,
)

sys.path.pop(0)

# HACK: End workaround for Python's exasperating package+import system.

# HACK: if built with py2exe and run as an .exe then exception
#           NameError: name '__file__' is not defined
#       force __file__ to be defined
if "__file__" not in globals():
    __file__ = "app.py"

#
# stdlib imports
#

# XXX: PEP8 complains about non-import statements before imports are done. But
#      do this check sooner so the user does not install non-standard libraries
#      (due to import failures) only to find out they used the wrong version of
#      Python 3
if sys.version_info < (3, 7):
    raise RuntimeError(
        "This script is meant for python 3.7 or newer. It will"
        " fail using this python version %s" % sys.version
    )
_: bool = True  # SyntaxError here means file is parsed (but not run) by interpreter <3.7 (most likely pip)

# XXX: workaround for https://github.com/pytest-dev/pytest/issues/4843
if "pytest" not in sys.modules:
    sys.stdout.reconfigure(encoding="utf-8", errors="namereplace")
    sys.stderr.reconfigure(encoding="utf-8", errors="namereplace")

import abc  # ABC, abstractmethod
import argparse  # ArgumentParser
import datetime
import difflib  # SequenceMatcher
import io  # BytesIO
import json
import os
import time
import re
import shutil  # copy2
import tempfile
import urllib.request
import urllib.error
import urllib.parse

# threading stuff
import threading
import queue  # Queue, SimpleQueue Empty

# type hints and type precision
from pathlib import Path
import collections  # namedtuple
import enum  # Enum
import typing
from typing import (
    Any,
    DefaultDict,
    Dict,
    List,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    Union,
)

# logging and printing
import logging
from pprint import pformat
from pprint import pprint as pp  # convenience during live-debugging

#
# vendor/3rd party imports
#

# https://pypi.org/project/attrs/
import attr

# https://pypi.org/project/mutagen/
import mutagen

# https://pypi.org/project/Pillow/
try:
    import PIL
    from PIL import Image
except ImportError as ie:
    # XXX: on some Linux, `pip install Pillow` does not install required OS library, results in
    #        ImportError: libopenjp2.so.7: cannot open shared object file: No such file or directory
    #      https://stackoverflow.com/q/48012582/471376
    if "libopenjp2" in str(ie):
        print(
            "It appears library libopenjp2 is missing. apt install command is:\n"
            "    apt install libopenjp2-7\n",
            file=sys.stderr,
        )
        raise

# https://pypi.org/project/tabulate/
from tabulate import tabulate

# https://pypi.org/project/requests/
import requests

PREFERENCE_FILE_NAME = name + ".prefs.py"

HTTP_GET = "GET"
HTTP_POST = "POST"

#
# Using a few different methods for typing things.
#

Artist = typing.NewType("Artist", str)
Album = typing.NewType("Album", str)
ArtAlb = typing.NewType("ArtAlb", Tuple[Artist, Album])

Headers = typing.NewType("Headers", Dict[str, str])


# add this method to act as __bool__
# TODO: XXX: how to override __bool__ for typing.NewType ? Should that be done?
#            try inheriting typing.Tuple and override __bool__ ?
def ArtAlb_is(artalb: ArtAlb) -> bool:
    return bool(artalb[0]) or bool(artalb[1])


def ArtAlb_new(artist: Union[str, Artist], album: Union[str, Album]) -> ArtAlb:
    return ArtAlb(
        (
            Artist(artist),
            Album(album),
        )
    )


ArtAlb_empty = ArtAlb_new("", "")
# ('Dir'ectory, 'Art'ist, 'Alb'um)
DirArtAlb = typing.NewType("DirArtAlb", Tuple[Path, ArtAlb])
DirArtAlb_List = List[DirArtAlb]
Path_List = List[Path]


@attr.s(slots=True, frozen=True)
class WrOpts:
    """Write Options - these should always travel together"""

    overwrite: bool = attr.ib()
    test: bool = attr.ib()


class URL(str):
    """
    string type with constraints on values.
    The value must look like an http* URL string.

    NOTE: There are great libraries for safe and flexible URL handling (e.g.
          purl). But this project is for the sake of learning.

    Immutable types are treated differently when inherited:
    https://stackoverflow.com/a/2673863/471376
    """

    def __new__(cls, *value):
        if value:
            v0 = value[0]
            if not type(v0) is str:
                raise TypeError('Unexpected type for URL: "%s"' % type(v0))
            if not (v0.startswith("http://") or v0.startswith("https://")):
                raise ValueError('Passed string value "%s" is not an' ' "http*://" URL' % (v0,))
        # else allow None to be passed. This allows an "empty" URL, `URL()` that
        # evaluates False
        return str.__new__(cls, *value)


class SearcherMedium(enum.Enum):
    """
    Distinguish the medium the ImageSearcher class uses.

    TODO: someday, somehow this would assist in queuing ImageSearcher work
          by medium. Work via NETWORK would allow many simultaneous ImageSearcher
          instances, and work via DISK would allow fewer.
          For now, this information is a NOOP (though a fun little exercise in
          class organization).
    """

    DISK = "disk"
    NETWORK = "network"

    @classmethod
    def list(cls) -> List[str]:
        return [sm_.value for sm_ in SearcherMedium]


#
# Google CSE Options
#


class ImageSize(enum.Enum):
    """
    must match https://developers.google.com/custom-search/v1/cse/list
    (http://archive.fo/Oi3mv)
    """

    SML = "small"
    MED = "medium"
    LRG = "large"

    @classmethod
    def list(cls) -> List[str]:
        return [is_.value for is_ in ImageSize]


# (API Key, CX ID, Image Size)
# GoogleCSE_Key = typing.NewType('GoogleCSE_Key', str)
# GoogleCSE_ID = collections.namedtuple('GoogleCSE_ID', str)
# GoogleCSE_Opts = typing.NewType('GoogleCSE_Opts', typing.Tuple[GoogleCSE_Key,
#                                GoogleCSE_ID,
#                                str])):

# Trying out namedtuple for typing this.
# XXX: AFAICT, cannot type-hint the attributes within the collections.namedtuple
class GoogleCSE_Opts(collections.namedtuple("GoogleCSE_Opts", "key id image_size")):

    # XXX: How to best `assert image_size in ImageSize.list()` ?

    def __bool__(self) -> bool:
        return bool(self.id) and bool(self.key) and bool(self.image_size)


class Discogs_Args(collections.namedtuple("Discogs_Args", "pat_token")):
    """
    pat_token is Discogs Personal Access Token
    """

    def __bool__(self) -> bool:
        return bool(self.pat_token)


class ImageType(enum.Enum):
    """
    Represent different Image Types as an Enum
    Add workarounds for the ongoing indecision of ".jpg" vs. ".jpeg" phrasing
    and file naming.
    """

    JPG = "jpg"
    PNG = "png"
    GIF = "gif"

    @property
    def suffix(self) -> str:
        return os.extsep + self.value

    @property
    def re_suffix(self) -> str:
        # JPG files can match '.jpg' and '.jpeg'
        if self is ImageType.JPG:
            return re.escape(os.extsep) + r"jp[e]?g"
        return re.escape(self.suffix)

    @staticmethod
    def list() -> List:
        return [it.value for it in ImageType]

    @staticmethod
    def ImageFromFormat(fmt: str):
        """
        from PIL.Image.format string to corresponding ImageType instance
        return None if none found
        """
        fmt = fmt.lower()
        if fmt == "jpeg":  # this darn special case!
            return ImageType.JPG
        try:
            ImageType(fmt)
        except ValueError:
            return None
        return ImageType(fmt)

    @property
    def pil_format(self) -> str:
        """
        Pillow Image module prefers the identifier 'JPEG', not 'JPG'
        else, PIL/Image.py:Image.save raises KeyError 'JPG'
        Pass this for `format` keyword
        Accurate as of Pillow version 6.1.0
        """
        if self is ImageType.JPG:
            return "JPEG"
        return self.value.upper()


class Result(NamedTuple):
    """
    Save the results of ImageSearcher work in a formalized manner. Intended for
    later printing in a meaningful way.

    TODO: This class is clunky and terribly overwrought. It was an
          experiment with NamedTuple that turned out ugly.
          No need to save all this data, just create a message at time of
          instantiation and move on. This class could become an enum.Enum
          class. Add an `_ignore_` field `message` that explains specifics.
    """

    artalb: Optional[ArtAlb]
    imagesearcher_type: Any  # TODO: how to narrow this down to ImageSearcher type or inherited?
    image_type: Optional[ImageType]
    image_path: Path
    result_written: bool  # bytes that comprise an image were written to `image_path`
    wropts: WrOpts  # was --overwrite or --test enabled?
    result_nosuitable: bool  # nothing was found, no suitable image was found, nothing was written
    message: str  # tell the user about what happened
    error: bool  # was there an error?
    error_mesg: str  # if error: the error message the user should see

    def __bool__(self) -> bool:
        if self.error or self.result_nosuitable:
            return False
        if self.image_path == Path():  # this instance was not initialized
            return False
        return True

    @staticmethod
    def strt(test: bool) -> str:
        """if test then return prepended string"""
        return "(--test) " if test else ""

    @classmethod
    def NoSuitableImageFound(cls, artalb: ArtAlb, image_path: Path, wropts: WrOpts):
        message = "%sNo suitable image found" % cls.strt(
            wropts.test,
        )
        return Result(artalb, None, None, image_path, False, wropts, True, message, False, "")

    @classmethod
    def SkipDueToNoOverwrite(
        cls, artalb: Optional[ArtAlb], imagesearcher: Any, image_path: Path, wropts: WrOpts
    ):
        if not image_path.exists():
            raise RuntimeError('expected a file that exists, does not "%s"', image_path)
        if wropts.overwrite:
            raise ValueError("WriteOptions.overwrite must be False")
        message = '%sfile "%s" already exists and --overwrite not enabled' % (
            cls.strt(wropts.test),
            image_path.name,
        )
        return Result(
            artalb, imagesearcher, None, image_path, False, wropts, False, message, False, ""
        )

    @classmethod
    def Downloaded(
        cls, artalb: ArtAlb, imagesearcher: Any, size: int, image_path: Path, wropts: WrOpts
    ):
        message = "%sFound %s and downloaded %d bytes from %s" % (
            cls.strt(wropts.test),
            str_ArtAlb(artalb),
            size,
            imagesearcher.provider(),
        )
        return Result(
            artalb, imagesearcher, None, image_path, True, wropts, False, message, False, ""
        )

    @classmethod
    def Copied(
        cls,
        artalb: ArtAlb,
        imagesearcher: Any,
        size: int,
        copy_src: Path,
        copy_dst: Path,
        wropts: WrOpts,
    ):
        source = "?"
        if imagesearcher is ImageSearcher_EmbeddedMedia:
            source = 'embedded image in "%s"' % copy_src.name
        elif imagesearcher is ImageSearcher_LikelyCover:
            source = 'likely cover "%s"' % copy_src.name
        message = "%sCopied %d bytes from %s" % (cls.strt(wropts.test), size, source)
        return Result(
            artalb, imagesearcher, None, copy_dst, True, wropts, False, message, False, ""
        )

    @classmethod
    def Extracted(
        cls,
        artalb: ArtAlb,
        imagesearcher: Any,
        size: int,
        copy_src: Path,
        copy_dst: Path,
        wropts: WrOpts,
    ):
        message = '%sExtracted %d pixels from embedded media "%s"' % (
            cls.strt(wropts.test),
            size,
            copy_src.name,
        )
        return Result(
            artalb,
            imagesearcher,
            None,
            copy_dst,
            True,
            wropts,
            False,
            message,
            False,
            "",
        )

    @classmethod
    def Error(cls, artalb: ArtAlb, imagesearcher: Any, copy_dst: Path, err_msg: str):
        message = "An error occurred for %s %s" % (str_ArtAlb(artalb), err_msg)
        return Result(
            artalb,
            imagesearcher,
            None,
            copy_dst,
            True,
            WrOpts(False, False),
            False,
            message,
            False,
            "",
        )


def overrides(interface_class):
    """
    Function decorator.  Will raise at program start if super-class does not
    implement the overridden function.
    Corollary to @abc.abstractmethod.
    Modified from answer https://stackoverflow.com/a/8313042/471376
    """

    def confirm_override(method):
        if method.__name__ not in dir(interface_class):
            raise NotImplementedError(
                'function "%s" is an @override but that'
                " function is not implemented in base"
                " class %s" % (method.__name__, interface_class)
            )

        def func():
            pass

        attr = getattr(interface_class, method.__name__)
        if type(attr) is not type(func):
            raise NotImplementedError(
                "function %r is an @override"
                " but that is implemented as type %s"
                " in base class %s, expected implemented"
                " type %s" % (method.__name__, type(attr), interface_class, type(func))
            )
        return method

    return confirm_override


strAAL = "["  # string AlbumArtist left-side
strAAR = "]"  # string AlbumArtist right-side
strAAM = "•"  # string AlbumArtist middle separator


def str_AA(artist: Artist, album: Album) -> str:
    return '%s "%s" %s "%s" %s' % (strAAL, artist, strAAM, album, strAAR)


def str_ArtAlb(artalb: ArtAlb) -> str:
    return str_AA(artalb[0], artalb[1])


def log_new(logformat: str, level: int, logname: str = None) -> logging.Logger:
    """
    Create a new logger instance or return the prior-created logger instance
    that has the same logname.

    :param logformat: logging message format, see docs.
    :param level: logging level
    :param logname: something meaningful helps
    :return: logging.Logger instance
    """

    if not logname:
        logname = os.path.basename(__file__).split(os.extsep)[0]
    log = logging.getLogger(logname)
    log.setLevel(level)
    # if the logger already has handlers then do not add more handlers
    # otherwise there will be duplicate log messages
    if log.hasHandlers():
        return log
    logformatter = logging.Formatter(logformat)
    loghandler = logging.StreamHandler()
    loghandler.setFormatter(logformatter)
    log.addHandler(loghandler)
    return log


#
# global instances
#

LOGFORMAT = "%(levelname)s: [%(threadName)s %(name)s]: %(message)s"
"""recommended format"""
log = log_new(LOGFORMAT, logging.WARNING)
"""the file-wide logger instance"""

REFERER_DEFAULT = __url__

SEMAPHORE_COUNT_DISK = 2
SEMAPHORE_COUNT_NETWORK = 16
TASK_QUEUE_THREAD_COUNT = SEMAPHORE_COUNT_DISK + SEMAPHORE_COUNT_NETWORK + 1
"""task_queue has this many threads consuming tasks"""
# XXX: for help during development
# TASK_QUEUE_THREAD_COUNT = 1


#
# helper functions
#


def func_name(foffset: int = 0) -> str:
    """
    return the name of the function at frame offset `foffset`
    by default, the current function
    """
    return sys._getframe(foffset + 1).f_code.co_name


def split_parameters(
    parm_str: str, keys_ret: Sequence[str], maxsplit: int = -1
) -> Tuple[str, ...]:
    """
    given a `parm_str` like "a=1&bb=22&ccc=333", return the values of `keys_ret`
    helper to do some more pro-active checking as it goes
    """
    FS = "&"
    EQ = "="
    if not parm_str:
        return tuple()
    if parm_str.count(FS) == 0:
        raise ValueError("Bad parameter string; has no field separator '%s'" % (FS,))
    parameters = parm_str.split(FS, maxsplit=maxsplit)
    # create dict of parameter keys values
    kv = dict()  # type: Dict[str, str]
    for p_ in parameters:
        if p_.count(EQ) == 0:
            raise ValueError("Bad parameter field '%s'; has no equal '%s'" % (p_, EQ))
        k, v = p_.split(EQ, 1)
        kv[k] = v
    # collect the values for keys-of-interest
    ret = list()
    for kr in keys_ret:
        if kr not in kv.keys():
            raise ValueError(
                "Parameter '%s' not in parameter string '%s'"
                % (
                    kr,
                    parm_str[0:1000],
                )
            )
        ret.append(kv[kr])
    # return as tuple
    return tuple(ret)


def preferences_file() -> Tuple[Path, Any]:
    """
    find the most suitable `pypref` Preferences path
    """
    # Linux
    home = Path.home()
    tmpd = Path(tempfile.gettempdir())
    # Windows
    localappdata = os.environ.get("LOCALAPPDATA")
    if localappdata:
        localappdata = Path(localappdata)
    appdata = os.environ.get("APPDATA")
    if appdata:
        appdata = Path(appdata)
    # search in order of preferred path
    for configd in (
        localappdata,
        appdata,
        home.joinpath(".config"),
        home,
        tmpd,
    ):
        if not configd:
            continue
        if configd.is_dir() and os.access(configd, os.W_OK):
            break
        configd = None
    if not configd:
        raise RuntimeError("No writeable preferences directory found")

    # https://bachiraoun.github.io/pypref/
    from pypref import Preferences

    pref = Preferences(filename=str(PREFERENCE_FILE_NAME), directory=str(configd))
    path_ = configd.joinpath(PREFERENCE_FILE_NAME)
    return path_, pref


#
# audio file types (i.e. file name extensions)
#


def get_artist_album_mp3(ffp: Path) -> ArtAlb:
    """
    :param ffp: full file path of .mp3 file
    :return: (artist, album)
    """
    from mutagen.easyid3 import EasyID3
    from mutagen.id3 import ID3NoHeaderError
    from mutagen.id3 import ID3TagError

    try:
        media = EasyID3(ffp)
    except (ID3NoHeaderError, ID3TagError) as err:
        log.debug(err)
        return ArtAlb_empty

    artist = ""
    try:
        artist = media["artist"][0]
    except (KeyError, IndexError):
        pass
    try:
        if not artist:
            artist = media["albumartist"][0]
    except (KeyError, IndexError):
        pass

    album = ""
    try:
        album = media["album"][0]
    except (KeyError, IndexError):
        pass

    return ArtAlb((Artist(artist), Album(album)))


def get_artist_album_mp4(ffp: Path) -> ArtAlb:
    """
    :param ffp: full file path of media file
    :return: (artist, album)
    """
    from mutagen.easymp4 import EasyMP4

    media = EasyMP4(ffp)

    artist = ""
    try:
        artist = media["artist"][0]
    except (KeyError, IndexError):
        pass

    album = ""
    try:
        album = media["album"][0]
    except (KeyError, IndexError):
        pass

    return ArtAlb((Artist(artist), Album(album)))


def get_artist_album_flac(ffp: Path) -> ArtAlb:
    """
    :param ffp: full file path of media file
    :return: (artist, album)
    """
    from mutagen.flac import FLAC
    from mutagen.flac import FLACVorbisError
    from mutagen.flac import FLACNoHeaderError

    try:
        media = FLAC(ffp)
    except (FLACVorbisError, FLACNoHeaderError) as err:
        log.debug(err)
        return ArtAlb_empty

    artist = ""
    try:
        artist = media["ARTIST"][0]
    except (KeyError, IndexError):
        pass

    album = ""
    try:
        album = media["ALBUM"][0]
    except (KeyError, IndexError):
        pass

    return ArtAlb((Artist(artist), Album(album)))


def get_artist_album_ogg(ffp: Path) -> ArtAlb:
    """
    :param ffp: full file path of media file
    :return: (artist, album)
    """
    from mutagen.oggvorbis import OggVorbis
    from mutagen.oggvorbis import OggError

    try:
        media = OggVorbis(ffp)
    except OggError as err:
        log.debug(err)
        return ArtAlb_empty

    artist = ""
    try:
        artist = media.tags["ARTIST"][0]
    except:
        pass
    try:
        if not artist:
            artist = media.tags["ARTIST"][1]
    except:
        pass
    try:
        if not artist:
            artist = media.tags["artist"][0]
    except:
        pass
    try:
        if not artist:
            artist = media.tags["artist"][1]
    except:
        pass
    try:
        if not artist:
            artist = media.tags["albumartist"][0]
    except:
        pass
    try:
        if not artist:
            artist = media.tags["albumartist"][1]
    except:
        pass

    album = Album("")
    try:
        album = media.tags["ALBUM"][0]
    except:
        pass
    try:
        if not album:
            album = media.tags["ALBUM"][1]
    except:
        pass
    try:
        if not album:
            album = media.tags["album"][0]
    except:
        pass
    try:
        if not album:
            album = media.tags["album"][1]
    except:
        pass

    return ArtAlb((Artist(artist), Album(album)))


def get_artist_album_asf(ffp: Path) -> ArtAlb:
    """
    :param ffp: full file path of media file
    :return: (artist, album)
    """
    from mutagen.asf import ASF
    from mutagen.asf._util import ASFHeaderError

    try:
        media = ASF(ffp)
    except ASFHeaderError as err:
        log.debug(err)
        return ArtAlb_empty

    artist = ""
    try:
        artist = str(media.tags["Author"][1])
    except:
        pass
    try:
        if not artist:
            artist = str(media.tags["Artist"][1])
    except:
        pass
    try:
        if not artist:
            artist = str(media.tags["WM/AlbumArtist"][1])
    except:
        pass
    try:
        if not artist:
            artist = str(media.tags["Author"][0])
    except:
        pass
    try:
        if not artist:
            artist = str(media.tags["Artist"][0])
    except:
        pass
    try:
        if not artist:
            artist = str(media.tags["WM/AlbumArtist"][0])
    except:
        pass

    album = ""
    try:
        album = str(media.tags["Album"][1])
    except:
        pass
    try:
        if not album:
            album = str(media.tags["WM/AlbumTitle"][1])
    except:
        pass
    try:
        if not album:
            album = str(media.tags["Album"][0])
    except:
        pass
    try:
        if not album:
            album = str(media.tags["WM/AlbumTitle"][0])
    except:
        pass

    return ArtAlb((Artist(artist), Album(album)))


# associate file extension to retrieval helper functions
# TODO: XXX: after adding all the prior get_artist_album_XXX methods, I noticed
#            the `mutagen.File` does this for the user. So let mutagen.File
#            figure out the type and remove get_artist_album_XXX methods. RTFM!
get_artist_album = {
    ".mp3": get_artist_album_mp3,
    ".m4a": get_artist_album_mp4,
    ".mp4": get_artist_album_mp4,
    ".flac": get_artist_album_flac,
    ".ogg": get_artist_album_ogg,
    ".wma": get_artist_album_asf,
    ".asf": get_artist_album_asf,
}
AUDIO_TYPES = list(get_artist_album.keys())


def sanitise(param: str):
    """sanitise a string for use as a url parameter"""
    if not param:
        return ""
    return urllib.parse.quote(param)


def similar(title1: str, title2: str) -> float:
    """
    :return: float value between 0 to 1 where higher value means more
             similarity among passed string values
    """
    return difflib.SequenceMatcher(None, title1, title2).ratio()


class ImageSearcher(abc.ABC):
    NAME = __qualname__

    def __init__(self, artalb: ArtAlb, image_type: ImageType, wropts: WrOpts, loglevel: int):
        """
        :param artalb: artist and album presumed. may be an "empty"
                       Artist and Album
        :param image_type: jpg, png, ...
        :param opts.overwrite: if (overwrite and file exists) then write new file
                          else return
        :param opts.loglevel: logging level
        :param opts.test: if test do not actually write anything
        """
        self.artalb = artalb  # type: ArtAlb
        self.image_type = image_type  # type: ImageType
        self.wropts = wropts  # type: WrOpts
        self.loglevel = loglevel  # type: int
        #
        self._image_bytes = bytes()  # type: bytes
        # setup new logger for this class instance
        self._logname = self.NAME + "(0x%08x)" % id(self)  # type: str
        self._log = log_new(LOGFORMAT, loglevel, self._logname)  # type: logging.Logger
        super().__init__()

    # TODO: XXX: abstractproperty has been deprecated since Python 3.3
    #            what technique can abstract a @property now?
    @abc.abstractmethod
    def search_medium(self) -> SearcherMedium:
        # pass
        raise NotImplementedError("child class failed to implement abstractmethod")

    @abc.abstractmethod
    def go(self) -> Optional[Result]:
        # pass
        raise NotImplementedError("child class failed to implement abstractmethod")

    @abc.abstractmethod
    def search_album_image(self) -> bytes:
        # pass
        raise NotImplementedError("child class failed to implement abstractmethod")

    @staticmethod
    def download_url(url: URL, log_: logging.Logger) -> bytes:
        """
        Download the data from the url, return it as bytes. Return empty bytes
        if failure.
        """

        if not url:
            raise ValueError("bad URL %r" % url)

        try:
            log_.info('image download urllib.request.urlopen("%s")', url)
            response = urllib.request.urlopen(url, None, 10)
        except Exception as err:
            log_.exception(err, exc_info=True)
            return bytes()

        return response.read()

    def write_album_image(self, image_path: Path) -> Result:
        """
        Write `self._image_bytes` to passed Path `image_path`

        :param image_path: full file path to image file
        """
        if not self._image_bytes:
            emsg = (
                "self._image_bytes not set, skip writing album image for %s . "
                "Was %s.search_album_image called?"
                % (str_ArtAlb(self.artalb), self.NAME)
            )
            self._log.warning(emsg)
            return Result.Error(self.artalb, self, image_path, emsg)

        if image_path.exists() and not self.wropts.overwrite:
            result = Result.SkipDueToNoOverwrite(
                self.artalb, self.__class__, image_path, self.wropts
            )
            self._log.debug(result.message)
            return result

        if not self.wropts.test:
            with open(str(image_path), "wb+") as fh:
                fh.write(self._image_bytes)
                self._log.info('Wrote %s bytes to "%s"', len(self._image_bytes), image_path)

        result = Result.Downloaded(
            self.artalb, self.__class__, len(self._image_bytes), image_path, self.wropts
        )
        self._log.debug(result.message)
        return result


class ImageSearcher_Medium_Disk(ImageSearcher):
    @overrides(ImageSearcher)
    def search_medium(self) -> SearcherMedium:
        return SearcherMedium.DISK


class ImageSearcher_Medium_Network(ImageSearcher):
    # specific Request class to allow pytest override with stub
    RequestClass = urllib.request.Request

    @overrides(ImageSearcher)
    def search_medium(self) -> SearcherMedium:
        return SearcherMedium.NETWORK

    # @abc.abstractclassmethod  # XXX: deprecated, what is an alternative?
    @classmethod
    def provider(cls) -> str:
        raise NotImplementedError("child class failed to implement abstractmethod")


class ImageSearcher_LikelyCover(ImageSearcher_Medium_Disk):
    """
    ImageSearcher that searches the parent directory of passed `image_path`
    for files that are likely cover files, e.g. 'album.jpg' or 'album_front.jpg'
    It searches for matching image types (using file extension), e.g. image_path
    with file name extension '.png' only searches for other '.png' files.
    If a suitable file is found then copy that file to `image_path`.

    For example, given image_path
         /home/user/music/ACDC - Back In Black/cover.jpg
    if ImageSearcher_LikelyCover instance finds a file
         /home/user/music/ACDC - Back In Black/Album Front.jpg
    then it will copy "Album Front.jpg" to "cover.jpg".
    """

    NAME = __qualname__

    def __init__(
        self, artalb: ArtAlb, image_type: ImageType, image_path: Path, wropts: WrOpts, loglevel: int
    ):
        self.copy_src = None  # type: Optional[Path]
        self.copy_dst = image_path  # type: Path
        super().__init__(artalb, image_type, wropts, loglevel)

    def _match_likely_name(self, files: Sequence[Path]) -> Optional[Path]:
        """
        Given a sequence of image files (Paths), find the most likely album cover
        match by analyzing the image file name.

        This function makes no changes to the class instance.

        :param files: sequence of Paths. Each .name is checked against some re
                      patterns to see if it is likely an album cover file name.
                      e.g. 'album cover.jpg' or
                           'ACDC Let There Be Rock (front).jpg'
                      would match one of the patterns. One of those file Paths
                      would be returned. See the order of matches in this
                      function to see how matches are ranked.
        :return Path: the most likely candidate Path that is an album cover
                      image
                      if no good candidate files then return None
        """

        # file path candidates keyed by integer preference (lower key value is
        # better)
        candidates_by_pref: DefaultDict[int, List[Path]] = collections.defaultdict(
            list
        )

        image_type = self.image_type
        # These re patterns are ordered by preference.
        # For example, if there are files "AlbumArtSmall.jpg" and
        # "AlbumArtLarge.jpg" then this ordering will prefer "AlbumArtLarge.jpg"
        # as the eventual self.copy_src.
        patterns = [
            # AlbumArtLarge.jpg
            # AlbumArt_{74AF69EF-02BA-43F5-B54B-3A379289FBEB}_Large.jpg
            r"""AlbumArt.*Large""" + image_type.re_suffix,
            # AlbumArtSmall.jpg
            # AlbumArt_{74AF69EF-02BA-43F5-B54B-3A379289FBEB}_Small.jpg
            r"""AlbumArt.*Small""" + image_type.re_suffix,
            # albumcover.jpg
            # album cover.jpg
            # album_cover.jpg
            r"""album[ \-_]?cover""" + image_type.re_suffix,
            # album.jpg
            # album_something.jpg
            r"""album[ \-_]?.*""" + image_type.re_suffix,
            # Something (album cover).jpg
            r""".*[ \-_]+\(album[ \-_]cover\)""" + image_type.re_suffix,
            # AlbumArt01.jpg
            r"""AlbumArt[\w]+""" + image_type.re_suffix,
            # Something (front cover) blarg.jpg
            r""".* \(front cover\)""" + image_type.re_suffix,
            # Something (cover front) blarg.jpg
            r""".* \(cover front\)""" + image_type.re_suffix,
            # Something (front).jpg
            r""".*[ \-_]\(front\)""" + image_type.re_suffix,
            # Something (front) blarg.jpg
            r""".*[ \-_]\(front\)[ \-_].*""" + image_type.re_suffix,
            # Something Front Cover.jpg
            r""".*[ \-_]front[ \-_]cover""" + image_type.re_suffix,
            # Something Cover Front.jpg
            r""".*[ \-_]cover[ \-_]front""" + image_type.re_suffix,
            # front.jpg
            # front_something.jpg
            # front-something.jpg
            # front something.jpg
            r"""front[ \-_][\w]*""" + image_type.re_suffix,
            # Something-front.jpg
            # Something_front.jpg
            r""".*[\-_]front""" + image_type.re_suffix,
            # Something-front-blarg.jpg
            # Something_front_blarg.jpg
            # Something - front - blarg.jpg
            # Something-front_cover-blarg.jpg
            r""".*[\-_ ]front[\-_ ][\w]+""" + image_type.re_suffix,
            # Something_something_album_cover.jpg
            r""".*[ \-_]+album_cover""" + image_type.re_suffix,
            # folder.jpg
            r"""folder""" + image_type.re_suffix,
            # cover.jpg
            # Something cover.jpg
            # Something_cover.jpg
            r""".*[ \-_]?cover""" + image_type.re_suffix,
            # R-3512668-1489953889-2577 cover.jpeg.jpg
            r""".*[\W]cover[\W].*""" + image_type.re_suffix,
            # Side A.jpg
            r""".*[ \-_]Side A""" + image_type.re_suffix,
            # Side 1.jpg
            r""".*[ \-_]Side 1""" + image_type.re_suffix,
            # SOMETHINGFRONT.JPG
            r""".*front""" + image_type.re_suffix,
            # Art.jpg
            r"""Art""" + image_type.re_suffix,
        ]

        for filep in files:
            # XXX: TODO: break this out into a private function? (for more concentrated pytests)
            for index, pattern in enumerate(patterns):
                try:
                    fm = re.fullmatch(pattern, filep.name, flags=re.IGNORECASE)
                    if fm:
                        if filep == self.copy_dst and self.copy_dst.exists():
                            self._log.debug(
                                'Matched name "%s" to pattern "%s" '
                                "but that is the same file as the "
                                "destination file!",
                                filep.name,
                                pattern,
                            )
                        else:
                            self._log.debug(
                                'Matched name "%s" to pattern "%s"', filep.name, pattern
                            )
                            candidates_by_pref[index].append(filep)
                            # matched current filep, no need to look for more
                            # re matches (they are already ordered by priority)
                            break
                except Exception as ex:
                    self._log.exception(ex, exc_info=True)

        #
        # Look for a file with a name similar to the directory name, this is
        # likely the album cover. e.g. "ACDC - TNT/acdc_tnt.jpg" means file
        # "acdc_tnt.jpg" is likely the album cover file within the album
        # directory "ACDC - TNT".
        # The similar score must be above 0.4 to be considered.
        # XXX: TODO: break this out into a private function? (for more concentrated pytests)
        #
        dirp = self.copy_dst.parent
        max_score = 0.4
        candidate_score = None
        for filep in files:
            # XXX: TODO: disclude file suffix for `similar` scoring
            score = similar(filep.name, dirp.name)
            if score > max_score:
                max_score = score
                candidate_score = filep
                self._log.debug(
                    'File "%s" is similar (%f) to directory' ' name "%s"',
                    filep.name,
                    score,
                    dirp.name,
                )

        if not (candidates_by_pref or candidate_score):
            self._log.debug("No likely pattern matched, similar named file")
            return None

        if candidates_by_pref:
            # choose the most preferred file, select the lowest key value
            # (related to order of matching patterns above)
            cands = candidates_by_pref[sorted(candidates_by_pref.keys())[0]]
            # XXX: debug self-check
            # XXX: mypy says this does not make sense
            if len(cands) > 1:
                self._log.debug(
                    "Note: multiple values in copy_src, choosing" " the first from:\n%s",
                    pformat(cands),
                )
            copy_src = cands[0]
        elif candidate_score:
            # choose file with the has high similar score of .name to
            # parentdir.name
            copy_src = candidate_score
        else:
            self._log.error("Bad if-elif, cannot find a candidate")
            return None

        return copy_src

    @overrides(ImageSearcher)
    def go(self) -> Optional[Result]:
        if not self.search_album_image():
            return None
        return self.write_album_image()

    def _find_likely_covers(self, image_type: ImageType, path: Path) -> Path_List:
        """
        Search directory entries under directory `path`.
        Return list of files that are likely to be an album cover image file.
        """
        candidates = []
        try:
            re_suffix_exact = "^" + image_type.re_suffix + "$"
            for fp in path.iterdir():
                if fp.is_file() and re.match(re_suffix_exact, fp.suffix, flags=re.IGNORECASE):
                    candidates.append(fp)
        except OSError as ose:
            self._log.exception(ose)
        candidates = sorted(candidates)  # iterdir does not guarantee order which may fail pytests

        return candidates

    @overrides(ImageSearcher)
    def search_album_image(self) -> bool:
        """
        Search `self.copy_dst.parent` directory and subdirectories for a file
        that is very likely an album cover image.
        """
        self._log.debug('search_album_image(…) self.copy_dst="%s"', self.copy_dst)

        candidates = []  # files that are of the same media image type
        try:
            candidates += self._find_likely_covers(self.image_type, self.copy_dst.parent)
            # search directories within directory of image_path for possible
            # cover art file candidates
            for fp in self.copy_dst.parent.iterdir():
                if fp.is_dir():
                    candidates += self._find_likely_covers(self.image_type, fp)
        except OSError as ose:
            self._log.exception(ose)
        candidates = sorted(candidates)  # iterdir does not guarantee order which may fail pytests

        self.copy_src = self._match_likely_name(candidates)
        if not self.copy_src:
            return False

        return True

    class WrongUseError(Exception):
        pass

    @overrides(ImageSearcher)
    def write_album_image(self) -> Result:
        """
        Copy `self.copy_src` to `self.copy_dst`
        """
        self._log.debug("write_album_image()")

        if not self.copy_src:
            raise self.WrongUseError(
                "self.copy_src is not set, must call"
                " search_album_image before calling"
                " write_album_image"
            )

        # sanity self-checks
        assert self.copy_src and self.copy_dst, (
            "Something is wrong, copy_src and/or copy_dst is not set\n"
            'cpy_src: "%s"\ncpy_dst: "%s"' % (self.copy_src, self.copy_dst)
        )
        assert self.copy_src.is_file(), 'copy_src "%s" is not a file⁈' % self.copy_src

        if self.copy_src == self.copy_dst:
            self._log.warning('copying the same file to itself⁈ "%s"', self.copy_src)
        # it's somewhat pointless to pass image_path since copy_dst should be
        # the same, but image_path is passed only for sake of consistency with
        # sibling classes. So may as well do this sanity check. Then forget
        # about image_path.
        # assert self.copy_dst == image_path, \
        #    'Something is wrong, expected copy_dst and passed image_path to ' \
        #    'be the same\n"%s" ≠ "%s"' % (self.copy_dst, image_path)

        if self.copy_dst.exists() and not self.wropts.overwrite:
            result = Result.SkipDueToNoOverwrite(
                self.artalb, self.__class__, self.copy_dst, self.wropts
            )
            self._log.debug(result.message)
            return result

        size = self.copy_src.stat().st_size
        if not self.wropts.test:
            shutil.copy2(str(self.copy_src), str(self.copy_dst))
            self._log.info('Copied "%s" to "%s"', self.copy_src, self.copy_dst)

        result = Result.Copied(
            self.artalb, self.__class__, size, self.copy_src, self.copy_dst, self.wropts
        )
        self._log.debug(result.message)
        return result


class ImageSearcher_EmbeddedMedia(ImageSearcher_Medium_Disk):
    """
    ImageSearcher that searches the media files for an embedded image.
    """

    NAME = __qualname__

    def __init__(
        self, artalb: ArtAlb, image_type: ImageType, image_path: Path, wropts: WrOpts, loglevel: int
    ):
        self.copy_dst = image_path
        self.image_type_PIL = None  # type: Optional[ImageType]
        self._image = None  # type: Optional[PIL.Image.Image]
        self._image_src = None  # type: Optional[Path]
        super().__init__(artalb, image_type, wropts, loglevel)

    @overrides(ImageSearcher)
    def go(self) -> Optional[Result]:
        if not self.search_album_image():
            return None
        return self.write_album_image()

    @overrides(ImageSearcher)
    def search_album_image(self) -> bool:
        """
        Search `self.copy_dst.parent` for an audio media file that contains
        an embedded album cover image
        """
        self._log.debug('search_album_image() self.copy_dst="%s"', self.copy_dst)

        media_files = []
        try:
            for fp in self.copy_dst.parent.iterdir():  # 'fp' means file path
                if fp.suffix.lower() in AUDIO_TYPES:
                    media_files.append(fp)
        except OSError as ose:
            self._log.exception(ose)

        if not media_files:
            return False

        # for media files, try to extract an embedded image bytes, constitute
        # the bytes with a PIL.Image class instance, store that as `self._image`
        # help from https://stackoverflow.com/a/54773705/471376
        from mutagen.id3 import ID3

        key_apic = "APIC:"
        for fp in media_files:
            try:
                media = ID3(fp)
            except:  # XXX: most likely will be ID3NoHeaderError
                continue
            if key_apic not in media:
                continue
            apic = media.get(key_apic)
            image_data = apic.data
            try:
                image = Image.open(io.BytesIO(image_data))  # type: PIL.Image
            except:
                continue
            # the PIL.Image will later be PIL.Image.save to the
            # self._image_type type (i.e. it will be format converted by the PIL
            # module)
            self.image_type_PIL = ImageType.ImageFromFormat(image.format)
            if not self.image_type_PIL:
                continue
            self._image = image
            self._image.size_pixels = image.height * image.width
            self._image_src = fp  # type: Path
            return True

        return False

    class WrongUseError(Exception):
        pass

    @overrides(ImageSearcher)
    def write_album_image(self) -> Result:
        """
        extract embedded image from `self._image`.
        """
        self._log.debug("write_album_image(…)")

        assert self.image_type, "self.image_type not set, something is wrong"
        if not self._image:
            raise self.WrongUseError(
                "self._image is not set, must call"
                " search_album_image before calling"
                " write_album_image"
            )

        if self.copy_dst.exists() and not self.wropts.overwrite:
            result = Result.SkipDueToNoOverwrite(
                self.artalb, self.__class__, self.copy_dst, self.wropts
            )
            self._log.debug(result.message)
            return result

        if not self.wropts.test:
            format_ = self.image_type.pil_format
            try:
                self._image.save(self.copy_dst, format=format_)
                self._log.info('Extracted %sx%s pixels %s bytes to "%s"',
                               self._image.width, self._image.height,
                               self._image.size_pixels, self.copy_dst)
            except PermissionError as pe:
                log.error(str(pe))
                return Result.Error(self.artalb, self.__class__, self.copy_dst, str(pe))

        result = Result.Extracted(
            self.artalb,
            self.__class__,
            self._image.size_pixels,
            self._image_src,
            self.copy_dst,
            self.wropts,
        )
        self._log.debug(result.message)
        return result


class ImageSearcher_GoogleCSE(ImageSearcher_Medium_Network):
    NAME = __qualname__

    # google_search_api = 'https://cse.google.com/cse'
    google_search_api = "https://www.googleapis.com/customsearch/v1"

    def __init__(
        self,
        artalb: ArtAlb,
        image_type: ImageType,
        image_path: Path,
        google_opts: GoogleCSE_Opts,
        referer: str,
        wropts: WrOpts,
        loglevel: int,
    ):
        self.__google_opts = google_opts  # in case these are needed later
        self.referer = referer
        self.key = google_opts.key
        self.cxid = google_opts.id
        self.image_size = google_opts.image_size
        self.image_path = image_path
        super().__init__(artalb, image_type, wropts, loglevel)

    def __bool__(self) -> bool:
        return bool(self.__google_opts)

    @classmethod
    # @overrides(ImageSearcher_Medium_Network)
    def provider(cls) -> str:
        return "Google"

    @overrides(ImageSearcher)
    def go(self) -> Optional[Result]:
        if not self.search_album_image():
            return None
        return self.write_album_image(self.image_path)

    def _search_response_json(self, request, *args, **kwargs):
        """
        Wrapper function so network request may be overridden by a testing
        harness (pytest)
        """
        return urllib.request.urlopen(request, *args, **kwargs)

    @overrides(ImageSearcher)
    def search_album_image(self) -> bool:
        self._log.debug("search_album_image() %s", str_ArtAlb(self.artalb))

        if self.artalb == ArtAlb_empty:
            return False

        # construct the URL
        # URI parameters documented at
        # https://developers.google.com/custom-search/v1/using_rest
        # (http://archive.fo/Ljx73)
        url = URL(
            ImageSearcher_GoogleCSE.google_search_api
            + "?"
            + "key="
            + self.key
            + "&cx="
            + self.cxid
            + "&prettyPrint=true"
            + "&q="
            + sanitise(self.artalb[0])
            + "+"
            + sanitise(self.artalb[1])
            + "&fileType="
            + str(self.image_type.value)
            + "&imgSize="
            + self.image_size.value
            + "&imgColorType=color"
            + "&searchType=image"
            + "&fields=items(title,link,image(thumbnailLink))"
            + "&num="
            + str(1)
        )
        request = self.RequestClass(url, data=None, headers={"Referer": self.referer})

        # make request from the provided url
        try:
            self._log.info('Google CSE urllib.request.urlopen("%s")', request.full_url)
            response = self._search_response_json(request, data=None, timeout=5)
        except urllib.error.HTTPError:
            return False
        except Exception as err:
            self._log.exception('Error %s returned for url "%s"', str(err), url)
            return False

        # load json response results into python dict
        try:
            resp = response.read()
            resp_json = json.loads(resp)
        except Exception as err:
            self._log.warning('Error during json loading: %s\nfor url "%s"', str(err), url)
            return False

        if not resp_json:
            self._log.debug("response json is empty")
            return False
        if not type(resp_json) is dict:
            self._log.debug("response json is not a dict")
            return False
        if "items" not in resp_json:
            self._log.debug('response json has no "items" key')
            return False
        if len(resp_json["items"]) == 0:
            self._log.debug('response json ["items"] has no entries')
            return False

        # get the original image link and the Google-hosted thumbnail
        img_urls = []
        title = ""
        item0 = resp_json["items"][0]
        if "link" in item0 and item0["link"]:
            img_urls.append(item0["link"])
        if "image" in item0 and "thumbnailLink" in item0["image"]:
            img_urls.append(item0["image"]["thumbnailLink"])
        if "title" in item0:
            title = item0["title"]

        # try to download the original image link, failing that try the
        # Google-hosted thumbnail image
        self._log.debug('downloading image for resource titled "%s"', title)
        for url in img_urls:
            bytes_ = self.download_url(url, self._log)
            if bytes_:
                self._image_bytes = bytes_
                break

        return True if self._image_bytes else False


class ImageSearcher_MusicBrainz(ImageSearcher_Medium_Network):
    NAME = __qualname__

    def __init__(
        self, artalb: ArtAlb, image_type: ImageType, image_path: Path, wropts: WrOpts, loglevel: int
    ):
        self.image_path = image_path
        super().__init__(artalb, image_type, wropts, loglevel)

    @classmethod
    # @overrides(ImageSearcher_Medium_Network)
    def provider(cls) -> str:
        return "musicbrainz.org"

    @overrides(ImageSearcher)
    def go(self) -> Optional[Result]:
        if not self.search_album_image():
            return None
        return self.write_album_image(self.image_path)

    def _search_artists(self, mb, artist: Artist) -> dict:
        """extract this function call to allow for pytest stubbing"""
        self._log.debug('· mb.search_artists(query="%s", limit=1)', artist)
        return mb.search_artists(query=artist, limit=1)

    def _browse_releases(self, mb, artist_id: str) -> dict:
        """extract this function call to allow for pytest stubbing"""
        self._log.debug('· mb.browse_releases(artist="%s", limit=500)', artist_id)
        return mb.browse_releases(artist=artist_id, limit=500)

    @overrides(ImageSearcher)
    def search_album_image(self) -> bool:
        """There are a number of ways to use the musicbrainz searching and
        browse API functions.
        The particular order of operations here appears
        seemed to be reasonably accurate. First, search on Artist string for an
        Artist ID then search on Album string confined to that Artist ID.
        Trying to search with just one API call using with Album+Artist string
        yields too many ambiguous results.

        TODO: XXX: this does not account for different image types!
                   only returns .jpg

        :return: found image or not?
        """

        artist = self.artalb[0]
        album = self.artalb[1]

        # XXX: these next two checks are an easy way out of making a complicated
        #      search for these special cases

        # if Artist is unknown, the artist search will raise
        if not artist:
            return False
        # if Album is unknown, the image selection will be too broad
        if not album:
            return False

        import musicbrainzngs

        mb = musicbrainzngs  # helper alias
        ua_app = mb.__package__
        ua_ver = mb.musicbrainz._version
        self._log.debug("· import %s version %s", ua_app, ua_ver)
        self._log.debug('· mb.set_useragent("%s", %s)', ua_app, ua_ver)
        mb.set_useragent(ua_app, ua_ver)
        self._log.debug('· mb.set_format(fmt="json")')
        # use fmt='xml' because fmt='json' causes this warning:
        #     musicbrainzngs\musicbrainz.py:584: UserWarning: The json format is
        #     non-official and may change at any time
        # as of musicbrainzngs==0.6
        mb.set_format(fmt="xml")
        artist_list = self._search_artists(mb, artist)

        # verify results exist before attempting to use them
        if not artist_list:
            self._log.debug('search_artists("%s") returned nothing', artist)
            return False
        if type(artist_list) is not dict:
            self._log.debug(
                'search_artists("%s") returned unexpected type %s', artist, type(artist_list)
            )
            return False
        if "artist-list" not in artist_list:
            self._log.debug(
                'search_artists("%s") results do not include an ' '"artist-list" entry', artist
            )
            return False
        if len(artist_list["artist-list"]) < 1:
            self._log.debug('search_artists("%s")["artist-list"] is an empty ' "list", artist)
            return False
        if "id" not in artist_list["artist-list"][0]:
            self._log.debug(
                'search_artists("%s")["artist-list"] results do not' ' include an artist "id"',
                artist,
            )
            return False
        # pick the first artist id from the list, this is most likely the
        # correct matching artist
        artist_id = artist_list["artist-list"][0]["id"]

        #
        # download releases (i.e. Studio albums) and release-groups
        # (i.e. Compilation albums) lists
        #

        # limit is a high number because popular artists have enormous
        # number of similar releases, re-releases, bootlegs, re-pressings,
        # packaging variations, media types (CD, cassette, etc.) and each has
        # an entry in the MusicBrainz database
        # e.g. Bob Dylan, Beatles, Pearl Jam, etc.
        releases = self._browse_releases(mb, artist_id)
        # verify before attempting to use releases
        if not releases:
            self._log.debug('browse_releases("%s") returned nothing', artist_id)
            return False
        if type(releases) is not dict:
            self._log.debug(
                'browse_releases("%s") returned unexpected type %s', artist_id, type(releases)
            )
            return False
        if "release-list" not in releases:
            self._log.debug(
                'browse_releases("%s") results do not include a ' '"release-list" entry', artist_id
            )
            return False

        possible = list(
            filter(lambda rle: similar(rle["title"], album) >= 0.4, releases["release-list"])
        )
        self._log.debug('· mb.browse_release_groups(artist="%s", limit=500)', artist_id)
        release_groups = mb.browse_release_groups(artist=artist_id, limit=100)
        possible += list(
            filter(
                lambda rgle: similar(rgle["title"], album) >= 0.4,
                release_groups["release-group-list"],
            )
        )

        # store tuple pairs of (`similar` score, release/release_group entry)

        score_album = []
        for p_ in possible:
            # XXX: slightly inefficient because the `similar` function was
            #      called with the same information earlier. good enough.
            score_album.append((similar(p_["title"], album), p_))
        if not score_album:
            return False
        score_album.sort(key=lambda x: x[0], reverse=True)
        # TODO: further refinement would be to disclude entries that explicitly
        #       do not have an associated 'cover-art-archive', e.g.
        #       ['release-list'][x]['cover-art-archive']['artwork'] == 'false'

        # index 0 has most `similar` album by title string
        try:
            album_id = score_album[0][1]["id"]
        except IndexError as ie:
            self._log.exception(ie, exc_info=True)
            return False

        # try several sources for the image
        image_list: Dict = dict()
        try:
            self._log.debug('· mb.get_image_list("%s")', album_id)
            image_list = mb.get_image_list(album_id)
        except (musicbrainzngs.musicbrainz.ResponseError, musicbrainzngs.musicbrainz.NetworkError):
            self._log.debug('Exception during get_image_list("%s")', album_id, exc_info=True)
            pass
        try:
            self._log.debug('· mb.get_release_group_image_list("%s")', album_id)
            image_list.update(mb.get_release_group_image_list(album_id))
        except (musicbrainzngs.musicbrainz.ResponseError, musicbrainzngs.musicbrainz.NetworkError):
            self._log.debug(
                'Exception during get_release_group_image_list("%s")', album_id, exc_info=True
            )
            pass

        # do this once
        dmsg = 'for %s MusicBrainz album  ID "%s"' % (str_AA(artist, album), album_id)
        # assume the first url available is the best
        if not image_list:
            self._log.debug("unable to find an image URL " + dmsg)
            return False
        if type(image_list) is not dict:
            self._log.debug("unexected type returned " + dmsg)
            return False
        if "images" not in image_list:
            self._log.debug('"images" key not in returned list ' + dmsg)
            return False
        if len(image_list["images"]) < 1:
            self._log.debug('list of "images" has no entries ' + dmsg)
            return False
        image0 = image_list["images"][0]
        if "image" not in image0:
            self._log.debug('images[0] has no "image" entry for %s ' + dmsg)
            return False
        url = image0["image"]

        self._image_bytes = self.download_url(url, self._log)

        return True if self._image_bytes else False


# discogs HTTP requests must handle rate-limit
# this is a slightly inefficient way to simplify handling the rate-limit response value
Discogs_Request_Lock = threading.RLock()


class Discogs_Downloader(abc.ABC):
    """
    "Interface" class for discogs.com album image downloads and API interaction.

    Inheriting classes must implement the underlying authentication mechanism, HTTP
    session handling, and @override the @abc.abstractmethod.
    """

    NAME = __qualname__

    HEADER_ACCEPT = "application/vnd.discogs.v2.plaintext+json"

    """
    from https://www.discogs.com/developers/#page:database,header:database-search

        /database/search?q={query}&{?type,title,release_title,credit,artist,anv,label,genre,style,country,year,format,catno,barcode,track,submitter,contributor}
    """
    URL_SEARCH = "https://api.discogs.com/database/search"

    """
    Requests are throttled by the server by source IP to 60 per minute for authenticated
    requests, and 25 per minute for unauthenticated requests, with some exceptions.
    Example rate-limit response headers:

        X-Discogs-Ratelimit: 60
        X-Discogs-Ratelimit-Remaining: 57
        X-Discogs-Ratelimit-Used: 3

    See https://www.discogs.com/developers/#page:home,header:home-rate-limiting

    Because of rate-limiting, a global `Discogs_Request_Lock` is used to coordinate
    Discogs requests, and the necessary sleeps when the X-Discogs-Ratelimit-Used goes to 0.
    If not for the rate-limiting, this class could just use then requests.Session
    to handle the multi-threaded requests.
    Currently, this causes only one discogs.com HTTP request to occur at a time, which is
    somewhat inefficient but also easiest to implement.
    """
    k_header_ratelimit = "X-Discogs-Ratelimit"
    k_header_ratelimit_remain = "X-Discogs-Ratelimit-Remaining"
    k_header_ratelimit_used = "X-Discogs-Ratelimit-Used"
    Ratelimit_Reset_Wait = 60 + 1  # wait time in seconds

    """
    class-wide requests.Session
    requests.Session underlying implementation users urllib3.HTTPConnectionPool which is thread-safe
    from https://urllib3.readthedocs.io/en/latest/reference/urllib3.connectionpool.html

         Thread-safe connection pool for one host.
    """
    __Session = requests.Session()
    __Session.rate_limit_time_last = float(0)

    def __init__(self, loglevel: int):
        self._logname = self.NAME + "(0x%08x)" % id(self)
        self._log = log_new(LOGFORMAT, loglevel, self._logname)
        self._log.debug("class-wide requests.Session object @0x%08X", id(self._session))

    @property
    def _session(self) -> requests.Session:
        return self.__Session

    def _ratelimit_wait(self) -> None:
        if self._session.rate_limit_time_last != 0:
            wait_another = Discogs_Downloader.Ratelimit_Reset_Wait - (
                time.time() - self._session.rate_limit_time_last
            )
            self._log.debug("Waiting %.3fs to so Discogs servers reset rate-limit…", wait_another)
            while Discogs_Downloader.Ratelimit_Reset_Wait > (
                time.time() - self._session.rate_limit_time_last
            ):
                time.sleep(1)
            self._session.rate_limit_time_last = float(0)
            self._log.debug("Session.rate_limit_time_last has been reset to 0")
        else:
            self._log.debug("Session.rate_limit_time_last is 0; skip waiting")

    def _ratelimit_update(self, remain: Optional[int]) -> None:
        self._log.debug("X-Discogs-Ratelimit-Remaining is %s", remain)
        if remain is None or remain > 1:
            return
        self._session.rate_limit_time_last = time.time()
        self._log.debug("Updated Discogs wait time to %.3f", self._session.rate_limit_time_last)

    def _do_request(self, request: requests.Request) -> requests.Response:
        """
        safe-wrapper for `self.__do_request_unsafe`
        """
        global Discogs_Request_Lock
        self._log.debug("Discogs_Request_Lock.acquire()…")
        if not Discogs_Request_Lock.acquire():
            raise RuntimeError("Failed to Discogs_Request_Lock.acquire() during _ratelimit_wait")
        try:
            self._log.debug("Discogs_Request_Lock.acquired")
            response = self.__do_request_unsafe(request)
        finally:
            self._log.debug("Discogs_Request_Lock.release()")
            Discogs_Request_Lock.release()
        return response

    def __do_request_unsafe(self, request: requests.Request) -> requests.Response:
        """
        Perform an HTTP Request with much debug logging.
        Handles discogs.com rate-limit throttling.
        """
        prequest = request.prepare()

        self._ratelimit_wait()

        headers_text = ""
        if self._log.isEnabledFor(logging.DEBUG):
            headers_text = pformat(
                [(h + ": " + v) for h, v in prequest.headers.items()], indent=4, sort_dicts=True
            ).replace("\n", "\n\t")
        self._log.debug(
            """
request:
    method: %s
    url: '%s'
    all headers:
        %s
    body:
        %s
""",
            prequest.method,
            prequest.url,
            headers_text,
            prequest.body,
        )

        response = self._session.send(prequest)  # type: requests.Response

        h_content_length = "Content-Length"
        content_length = ""
        try:
            content_length = response.headers[h_content_length]
            content_length = content_length
        except KeyError:
            self._log.debug("Header '%s' not found", h_content_length)

        h_content_type = "Content-Type"
        content_type = ""
        try:
            content_type = response.headers[h_content_type]
        except KeyError:
            self._log.debug("Header '%s' not found", h_content_type)

        headers_text = ""
        if self._log.isEnabledFor(logging.DEBUG):
            headers_text = pformat(
                [(h + ": " + v) for h, v in response.headers.items()], indent=4, sort_dicts=True
            ).replace("\n", "\n\t")
        debug_text = ""
        if self._log.isEnabledFor(logging.DEBUG):
            # TODO: match smaller set of printable types, instead of matching large set of non-printable
            if content_type.startswith("image/"):
                debug_text = "*binary image data*"
            else:
                debug_text = response.text[0:5000].replace("\n", "\n\t").strip()
        self._log.debug(
            """
response:
    url: '%s'
    status_code: %s
    reason: %s
    encoding: %s
    content-type: %s
    content-length: %s
    all headers:
        %s
    text:
        %s
""",
            response.url,
            response.status_code,
            response.reason,
            response.encoding,
            content_type,
            content_length,
            headers_text,
            debug_text,
        )

        if not Discogs_Downloader.is_response_success(response):
            self._log.error(
                "Discogs request returned %s %s for '%s'",
                response.status_code,
                response.reason,
                prequest.url,
            )

        remain = None
        try:
            if Discogs_Downloader.k_header_ratelimit_remain in response.headers:
                remain = int(response.headers[Discogs_Downloader.k_header_ratelimit_remain])
        except Exception:
            self._log.exception("failed to parse X-Discogs-Ratelimit headers")
            return response

        self._ratelimit_update(remain)

        return response

    @staticmethod
    def _search_url_assemble(artalb: ArtAlb) -> str:
        """
        return URL for searching discogs for given ArtAlb
        see https://www.discogs.com/developers/#page:database,header:database-search
        """
        return (
            Discogs_Downloader.URL_SEARCH
            + "?"
            + "&".join(
                (
                    "type=release",
                    "artist=" + urllib.parse.quote_plus(artalb[0]),
                    "release_title=" + urllib.parse.quote_plus(artalb[1]),
                    # rely on discogs.com sorting to have the first entry in the search
                    # be the most relevant
                    # see https://www.discogs.com/developers/#page:home,header:home-pagination
                    "page=1",
                    "per_page=1",
                ),
            )
        )

    @staticmethod
    def extract_cover_image(json_str: str, log_: logging.Logger) -> Optional[str]:
        """
        Navigate JSON string returned from a search response.
        Return the value of `cover_image` or `thumb`, prefer `cover_image`.
        The returned value should be a URL as a string.
        Return None if anything unexpected occurs.

        example JSON response for GET https://api.discogs.com/database/search?type=release&artist=Bob+Dylan&release_title=Highway+61+Revisited&page=2&per_page=1

        {'pagination': {'items': 351,
                        'page': 1,
                        'pages': 351,
                        'per_page': 1,
                        'urls': {'first': 'https://api.discogs.com/database/search?type=release&artist=Bob+Dylan&release_title=Highway+61+Revisited&page=1&per_page=1',
                                 'last': 'https://api.discogs.com/database/search?type=release&artist=Bob+Dylan&release_title=Highway+61+Revisited&page=351&per_page=1',
                                 'next': 'https://api.discogs.com/database/search?type=release&artist=Bob+Dylan&release_title=Highway+61+Revisited&page=3&per_page=1',
                                 'prev': 'https://api.discogs.com/database/search?type=release&artist=Bob+Dylan&release_title=Highway+61+Revisited&page=1&per_page=1'}},
         'results': [{'barcode': ['ASCAP',
                                  '7',
                                  'XSM 110640',
                                  'XSM 110641',
                                  'XSM110640 1A',
                                  'XSM110641 1A',
                                  'XSM110640 1B',
                                  'XSM110641 1B'],
                      'catno': 'CS 9189',
                      'community': {'have': 1750, 'want': 1193},
                      'country': 'US',
                      'cover_image': 'https://img.discogs.com/ES6RsrOk7uWbQJ-lqyc-kfkzREc=/fit-in/600x604/filters:strip_icc():format(jpeg):mode_rgb():quality(90)/discogs-images/R-3336238-1436579911-6632.jpeg.jpg',
                      'format': ['Vinyl', 'LP', 'Album', 'Stereo'],
                      'format_quantity': 1,
                      'formats': [{'descriptions': ['LP', 'Album', 'Stereo'],
                                   'name': 'Vinyl',
                                   'qty': '1',
                                   'text': 'Alternate Take Of "From A Buick 6"'}],
                      'genre': ['Rock'],
                      'id': 3336238,
                      'label': ['Columbia',
                                'Bob Dylan',
                                'Customatrix',
                                'M. Witmark & Sons'],
                      'master_id': 3986,
                      'master_url': 'https://api.discogs.com/masters/3986',
                      'resource_url': 'https://api.discogs.com/releases/3336238',
                      'style': ['Blues Rock', 'Folk Rock'],
                      'thumb': 'https://img.discogs.com/xKdGaGmgnus0YwZRqC3ut-flF4E=/fit-in/150x150/filters:strip_icc():format(jpeg):mode_rgb():quality(40)/discogs-images/R-3336238-1436579911-6632.jpeg.jpg',
                      'title': 'Bob Dylan - Highway 61 Revisited',
                      'type': 'release',
                      'uri': '/release/3336238-Bob-Dylan-Highway-61-Revisited',
                      'user_data': {'in_collection': False, 'in_wantlist': False},
                      'year': '1965'}]}
        """

        resp_json = dict()
        try:
            resp_json = json.loads(json_str)  # type: dict
            log_.debug("JSON:\n%s", pformat(resp_json).replace("\n", "\n\t").strip())
        except Exception as ex:
            log_.warning("Response fails to parse as json %s", ex)
            return
        cover_image_url = None
        try:
            results = resp_json["results"]
            if not results:
                log_.debug("'results' is empty")
                return
            result0 = results[0]
            # prefer the `cover_image` image but fallback to `thumb` image
            if "cover_image" in result0:
                cover_image_url = result0["cover_image"]
            elif "thumb" in result0:
                cover_image_url = result0["thumb"]
        except Exception as ex:
            log_.warning("Request response fails to find expected json structure %s", ex)
            return

        return cover_image_url

    @staticmethod
    def is_response_success(response: requests.Response):
        return 200 <= response.status_code < 300

    @abc.abstractmethod
    def download_album_cover(self, artalb: ArtAlb) -> Optional[bytes]:
        raise NotImplementedError(
            "child class failed to implement @abc.abstractmethod" " 'download_album_cover'"
        )


class Discogs_Downloader_PAT(Discogs_Downloader):
    """
    Download images from discogs.com using Personal Access Token authentication.
    Handles PAT authentication header.

    "Personal Access Token" can be generated from
    https://www.discogs.com/settings/developers (requires login)
    """

    NAME = __qualname__

    def __init__(self, discogs_token: str, *args: Tuple[Any]):
        self.pat_token = discogs_token
        super().__init__(*args)

    @staticmethod
    def _headers(pat_token: str) -> Headers:
        """
        return HTTP headers for a request

        See https://www.discogs.com/developers/#page:authentication,header:authentication-discogs-auth-flow
        """
        return Headers({"Authorization": "Discogs token=%s" % (pat_token,)})

    @overrides(Discogs_Downloader)
    def download_album_cover(self, artalb: ArtAlb) -> Optional[bytes]:
        self._log.debug("%s.download_album_cover(%s)", self.NAME, artalb)
        url = self._search_url_assemble(artalb)
        request1 = requests.Request(method=HTTP_GET, url=url, headers=self._headers(self.pat_token))
        self._log.info("HTTP Request '%s'", request1.url)
        response1 = self._do_request(request1)
        if not Discogs_Downloader.is_response_success(response1):
            return
        cover_image_url = Discogs_Downloader.extract_cover_image(response1.text, self._log)
        if cover_image_url:
            request2 = requests.Request(
                method=HTTP_GET,
                url=cover_image_url,
                headers=self._headers(self.pat_token),
            )
            self._log.info("HTTP Request '%s'", request2.url)
            response2 = self._do_request(request2)
            if not Discogs_Downloader.is_response_success(response2):
                return
            return response2.content
        return


# global thread lock for all `Discogs_Downloader_OAuth` instances
# XXX: should this declaration be moved to within the class?
Discogs_Oauth_Prefs_Mutex = threading.Lock()


class Discogs_Downloader_OAuth(Discogs_Downloader):
    """
    XXX: INCOMPLETE: Consumer Key and Consumer Secret are hardcoded to erroneous values.
                     This authentication method, OAuth 1.0a, remains mostly completed but not
                     plumbed end-to-end.

    Download images from discogs.com using OAuth authentication.
    Handles OAuth authentication, caching, and other varied HTTP requests.

    See https://www.discogs.com/developers (https://archive.ph/onn00)

    TODO: identity test is still done once per class instance. Only needs to be done
          once per set of Oauth credentials (effectively, once for the entire process run)
    """

    NAME = __qualname__

    """
    URLs from https://www.discogs.com/developers/#page:authentication,header:authentication-discogs-auth-flow
    """
    URL_REQUEST_TOKEN = "https://api.discogs.com/oauth/request_token"
    URL_AUTHORIZE = "https://www.discogs.com/oauth/authorize"
    URL_ACCESS_TOKEN = "https://api.discogs.com/oauth/access_token"
    URL_IDENTITY = "https://api.discogs.com/oauth/identity"
    """
    values from https://www.discogs.com/applications/edit/24597 (requires app owner login)
    """
    # XXX: hardcoded erroneous values, must manually override to use this
    #      Oauth 1.0a authentication
    DISCOGS_CONSUMER_KEY = "Erroneous Consumer Key"
    DISCOGS_CONSUMER_SECRET = "Erroneous Consumer Secret"

    def __init__(self, *args: Tuple[Any]):
        super().__init__(*args)
        self._oauth = dict()
        self._oauth.update(
            {
                "consumer_key": self.DISCOGS_CONSUMER_KEY,
                "consumer_secret": self.DISCOGS_CONSUMER_SECRET,
            }
        )
        self.__identity_test = False

    @staticmethod
    def _headers(**kwargs) -> Headers:
        headers = {
            "Accept": Discogs_Downloader_OAuth.HEADER_ACCEPT,
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": __product_token__,
        }
        header_value_oauth = Discogs_Downloader_OAuth._oauth_header_create(**kwargs)
        headers["Authorization"] = header_value_oauth
        return Headers(headers)

    @staticmethod
    def _oauth_header_create(
        consumer_key: str = "",
        consumer_secret: str = "",
        oauth_token: str = "",
        oauth_token_secret: str = "",
        oauth_callback: str = "",
        oauth_verifier: str = "",
    ):
        """
        from https://oauth.net/core/1.0/#nonce

            The Consumer SHALL then generate a Nonce value that is unique
            for all requests with that timestamp.
        """
        ts = datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
        oauth_nonce = ts
        oath_timestamp = int(ts)

        oauth_consumer_key = consumer_key

        """
        from https://www.discogs.com/developers/#page:authentication

            This is an explanation of how a web application may work with Discogs
            using OAuth 1.0a.
        """
        oath_version = "1.0a"

        """
        from https://www.discogs.com/developers/#page:authentication,header:authentication-oauth-flow

            we suggest sending requests with HTTPS and the PLAINTEXT signature method over HMAC-SHA1
            due to its simple yet secure nature. This involves setting your oauth_signature_method to
            “PLAINTEXT” and your oauth_signature to be your consumer secret followed by an
            ampersand (&).
        """
        oauth_signature_method = "PLAINTEXT"
        oauth_signature = consumer_secret + "&"
        if oauth_token_secret:
            oauth_signature += oauth_token_secret

        header_value_oauth = """\
OAuth \
oath_version={oath_version}, \
oauth_nonce="{oauth_nonce}", \
oauth_timestamp="{oath_timestamp}", \
oauth_consumer_key="{oauth_consumer_key}", \
oauth_signature_method="{oauth_signature_method}", \
oauth_signature="{oauth_signature}"\
""".format(
            oath_version=oath_version,
            oauth_nonce=oauth_nonce,
            oath_timestamp=oath_timestamp,
            oauth_consumer_key=oauth_consumer_key,
            oauth_signature_method=oauth_signature_method,
            oauth_signature=oauth_signature,
        )
        if oauth_callback:
            header_value_oauth += ', oauth_callback="{oauth_callback}"'.format(
                oauth_callback=oauth_callback
            )
        if oauth_token:
            header_value_oauth += ', oauth_token="{oauth_token}"'.format(oauth_token=oauth_token)
        if oauth_verifier:
            header_value_oauth += ', oauth_verifier="{oauth_verifier}"'.format(
                oauth_verifier=oauth_verifier
            )
        return header_value_oauth

    def __oauth_establish_unsafe(self) -> None:
        """
        Discogs images download requires authentication (i.e. user login and app credentials)
        from https://www.discogs.com/developers/#page:images

            Image requests require authentication and are subject to rate limiting.
        """
        self._log.debug("→ __oauth_establish_unsafe()")

        k_oauth_token = "oauth_token"
        k_oauth_token_secret = "oauth_token_secret"

        self._log.debug("Searching for preferences file…")
        prefs_path, prefs = preferences_file()
        pf = str(prefs).strip().replace("\r", "").replace("\n", "\n\t")
        self._log.debug("Preferences (%s):\n\t%s", prefs_path, pf)
        oauth_token = prefs.get(k_oauth_token)
        oauth_token_secret = prefs.get(k_oauth_token_secret)
        if oauth_token and oauth_token_secret:
            self._log.info("Prior OAuth credentials will be used")
            self._oauth.update(
                {
                    k_oauth_token: oauth_token,
                    k_oauth_token_secret: oauth_token_secret,
                }
            )
            self._log.debug("← __oauth_establish_unsafe()")
            return
        # self-check
        if (oauth_token and not oauth_token_secret) or (not oauth_token and oauth_token_secret):
            self._log.warning(
                "unexpected oauth_token '%s' yet oauth_token_secret '%s'",
                oauth_token,
                oauth_token_secret,
            )

        self._log.debug("import %s version %s", requests.__name__, requests.__version__)
        self._log.debug("requests User-Agent: %s", __product_token__)

        """
        from https://www.discogs.com/applications/edit/24597

            Callback URL (optional)
                Where should the user be directed after authorization?
                OAuth 1.0a applications should provide an oauth_callback during the request token step
                regardless of what's entered here.
        """
        oauth_callback = "https://api.discogs.com/oauth/identity"
        # using `oauth_callback = https://api.discogs.com/oauth/identity` results in redirect to page with JSON body
        #    {"message": "You must authenticate to access this resource."}
        """
        from https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_1_flows.htm&type=5

            oob = Out Of Band
        """
        oauth_callback = "oob"
        request1 = requests.Request(
            method=HTTP_POST,
            url=self.URL_REQUEST_TOKEN,
            headers=self._headers(**self._oauth, oauth_callback=oauth_callback),
        )
        response1 = self._do_request(request1)
        """
        response body example:

            oauth_token=EvbRqfuLpPugOtKUciplzRitBSnYtzLvxZqPtIYY&oauth_token_secret=nglMVUAClSnrxzxhNvGCZeBhvVvbBwrEUWUfltyH&oauth_callback_confirmed=true

        response body as one field per line:
            oauth_token=EvbRqfuLpPugOtKUciplzRitBSnYtzLvxZqPtIYY
            oauth_token_secret=nglMVUAClSnrxzxhNvGCZeBhvVvbBwrEUWUfltyH
            oauth_callback_confirmed=true
        """
        if not Discogs_Downloader.is_response_success(response1):
            raise ConnectionRefusedError(
                "Discogs API returned HTTP %s %s, refused OAuth request for a token '%s'"
                % response1.status_code,
                response1.reason,
                request1.url,
            )
        oauth_token, oauth_token_secret = split_parameters(
            response1.text, [k_oauth_token, k_oauth_token_secret]
        )
        self._oauth.update(
            {
                k_oauth_token: oauth_token,
                k_oauth_token_secret: oauth_token_secret,
            }
        )

        url_auth = "https://discogs.com/oauth/authorize?oauth_token=" + oauth_token
        print("Authorize this application by browsing to", url_auth)
        """
        discogs page in user browser should display HTML that reads:

            Authorization successful
            If the application asks you for a code, enter the following:
                iHCGVwxCBg
            You can now close this window.

        code will vary.
        """
        print("Enter the code displayed: ", end="")
        oauth_verifier = input()
        oauth_verifier = oauth_verifier.strip()

        """
        https://www.discogs.com/developers#page:authentication,header:authentication-oauth-flow

            Send a POST request to the Discogs access token URL

        https://www.discogs.com/forum/thread/402590

            be sure that your oauth_timestamp is dynamically generated at the time of the request; the OAuth server we
            use returns 401s if these timestamps are too old (5 minutes, I believe).
        """
        headers2 = self._headers(
            **self._oauth,
            oauth_verifier=oauth_verifier,
        )
        request2 = requests.Request(
            method=HTTP_POST,
            url=self.URL_ACCESS_TOKEN,
            headers=headers2,
        )
        response2 = self._do_request(request2)
        if not Discogs_Downloader.is_response_success(response2):
            raise ConnectionRefusedError(
                "Discogs API returned HTTP %s %s, refused OAuth access of a token '%s'"
                % (
                    response1.status_code,
                    response1.reason,
                    request2.url,
                )
            )
        """
        https://www.discogs.com/developers/#page:authentication,header:authentication-oauth-flow

            A successful request will return a response that contains an OAuth access token
            (oauth_token) and an OAuth access token secret (oauth_token_secret). These tokens
            do not expire (unless the user revokes access from your app), so you should store
            these tokens in a database or persistent storage to make future requests signed
            with OAuth. All requests that require OAuth will require these two tokens to be
            sent in the request.

        response body example:

            oauth_token=PJpiKwdfmPtHmJEJfiZDhJgThUOncATSgGJvjvcs&oauth_token_secret=GSutOLUpEALwOBLursEBvQLSsRaxKMiIPjJYdVqr

        response body example one field per line:

            oauth_token=PJpiKwdfmPtHmJEJfiZDhJgThUOncATSgGJvjvcs
            oauth_token_secret=GSutOLUpEALwOBLursEBvQLSsRaxKMiIPjJYdVqr

        """
        oauth_token, oauth_token_secret = split_parameters(
            response2.text, [k_oauth_token, k_oauth_token_secret]
        )
        tokens = {
            k_oauth_token: oauth_token,
            k_oauth_token_secret: oauth_token_secret,
        }
        self._log.debug("set_preferences(%s)", tokens)
        prefs.set_preferences(preferences=tokens)
        self._log.info("New OAuth credentials established, saved in '%s'", prefs_path)
        self._oauth.update(tokens)
        self._log.debug("← __oauth_establish_unsafe()")

    def _oauth_establish(self) -> None:
        """
        call `self.__oauth_establish_unsafe` wrapping call with lock of mutex
        """
        global Discogs_Oauth_Prefs_Mutex
        if not Discogs_Oauth_Prefs_Mutex.acquire():
            raise RuntimeError("Failed Discogs_Oauth_Prefs_Mutex.acquire()")
        try:
            self.__oauth_establish_unsafe()
        finally:
            Discogs_Oauth_Prefs_Mutex.release()

    def _oauth_identity_test(self) -> bool:
        """
        Establish OAuth credentials and then test that OAuth credentials are functioning
        by doing a simple user identity request.
        https://www.discogs.com/developers/#page:user-identity,header:user-identity-identity

            You can use this resource to find out who you’re authenticated as,
            and it also doubles as a good sanity check to ensure that you’re using OAuth correctly.

        TODO: only do identity test once per process
        """
        if self.__identity_test:
            self._log.debug("_oauth_identity_test already passed; skip")
            return True

        self._log.debug("→ _oauth_identity_test()")

        self._oauth_establish()
        request = requests.Request(
            method=HTTP_GET,
            url=self.URL_IDENTITY,
            headers=self._headers(**self._oauth),
        )
        self._log.info(
            "Request identity URL '%s' to verify Discogs OAuth Credentials", self.URL_IDENTITY
        )
        response = self._do_request(request)
        if not Discogs_Downloader.is_response_success(response):
            self._log.warning(
                "Discogs identity request '%s' returned %s %s, something is wrong with Oauth Credentials",
                self.URL_IDENTITY,
                response.status_code,
                response.reason,
            )
            self._log.debug("← _oauth_identity_test()")
            return False
        self._log.info("Discogs OAuth Credentials satisfied identity request:\n\t%s", response.text)
        self.__identity_test = True
        self._log.debug("← _oauth_identity_test()")
        return True

    @overrides(Discogs_Downloader)
    def download_album_cover(self, artalb: ArtAlb) -> Optional[bytes]:
        """
        construct an album-oriented search query, search discogs, find the image URL for the most
        likely candidate album.
        API description https://www.discogs.com/developers/#page:database,header:database-search

        Return album cover image as `bytes`, failure returns `None`
        """
        self._log.debug("%s.download_album_cover(%s)", self.NAME, artalb)

        if not self._oauth_identity_test():
            return

        url = self._search_url_assemble(artalb)
        request1 = requests.Request(
            method=HTTP_GET,
            url=url,
            headers=self._headers(**self._oauth),
        )
        self._log.info("HTTP Request '%s'", request1.url)
        response1 = self._do_request(request1)
        if not Discogs_Downloader.is_response_success(response1):
            return
        cover_image_url = Discogs_Downloader.extract_cover_image(response1.text, self._log)
        if cover_image_url:
            request2 = requests.Request(
                method=HTTP_GET,
                url=cover_image_url,
                headers=self._headers(**self._oauth),
            )
            self._log.info("HTTP Request '%s'", request2.url)
            response2 = self._do_request(request2)
            if not Discogs_Downloader.is_response_success(response2):
                return
            return response2.content


class ImageSearcher_Discogs(ImageSearcher_Medium_Network):

    NAME = __qualname__

    def __init__(
        self,
        artalb: ArtAlb,
        image_type: ImageType,
        image_path: Path,
        discogs_args: Discogs_Args,
        wropts: WrOpts,
        loglevel: int,
    ):
        self.image_path = image_path
        super().__init__(artalb, image_type, wropts, loglevel)
        # self.discogs_downloader = Discogs_Downloader_OAuth(loglevel)
        self.discogs_downloader = Discogs_Downloader_PAT(
            discogs_args.pat_token, loglevel
        )  # type: Discogs_Downloader

    @classmethod
    # @overrides(ImageSearcher_Medium_Network)
    def provider(cls) -> str:
        return "discogs.org"

    @overrides(ImageSearcher)
    def go(self) -> Optional[Result]:
        if not self.search_album_image():
            return None
        return self.write_album_image(self.image_path)

    @overrides(ImageSearcher)
    def search_album_image(self) -> bool:
        """
        TODO: XXX: this does not account for different image types!
                   only returns .jpg
        :return: found image or not?
        """

        artist = self.artalb[0]
        album = self.artalb[1]

        # if either Artist or Album is unknown, the image search will be too broad to be useful
        # XXX: is that true?
        if not artist or not album:
            return False

        self._image_bytes = self.discogs_downloader.download_album_cover(self.artalb)
        # self.write_album_image(self.image_path)

        return True if self._image_bytes else False


def process_dir(
    dirp: Path,
    image_nt: str,
    overwrite: bool,
    result_queue: queue.SimpleQueue,
    daa_list: DirArtAlb_List,
) -> DirArtAlb_List:
    """
    Recursively process sub-directories of given directory,
    gathering artist/album info per-directory.

    Call initially with empty daa_list. daa_list will be
    gradually populated by recursive calls. Provide coverFiles
    list to ignore directories where cover files already exist.

    TODO: XXX: This function does too much!
               This function should just return a list of directories that are
               deemed to be Album directories.
               Put that check into helper function
                  e.g.
                  `is_album_dir(dirp: Path) -> bool`
               Let something outside of this attempt to determine
               1. if the directory should be written to (check if image exists
                  and overwrite)
                  e.g.
                  `dir_requires_cover(dirp: Path) -> bool`
               2. deteremine the Artist and Album of that directory.
                  e.g.
                  `def deteremine_ArtAlb(dirp: Path) -> ArtAlb`

    TODO: XXX: Implementing this recursively just makes this function weird.
               Consider `os.walk` instead.

    TODO: XXX: I really hate this function.

    :param dirp: directory path to process
    :param image_nt: image name and type, e.g. "cover.jpg"
    :param overwrite: --overwrite
    :param result_queue: append Result about any found image files
    :param daa_list: accumulated directories for later processing
    :return accumulated directories for later processing
    """
    log.debug('process_dir("%s", "%s", …)', dirp, image_nt)

    dirs = []
    files = []

    if not dirp.exists():
        log.error('path does not exist: "%s"', dirp)
        return daa_list
    if not dirp.is_dir():
        log.error('path is not a directory: "%s"', dirp)
        return daa_list

    # read dirp directory contents
    try:
        log.debug('%s: processing directory "%s"', func_name(), dirp)
        for fp in dirp.iterdir():  # 'fp' is a file path
            log.debug('%s: found "%s"', func_name(), fp)
            if fp.is_dir():
                dirs.append(fp)
            elif fp.is_file():
                files.append(fp)
    except OSError as err:
        log.exception(err)
        return daa_list

    # recurse into subdirs
    dirs.sort()
    for dir_ in dirs:
        # XXX: should not this append the return of process_dir?
        daa_list = process_dir(dir_, image_nt, overwrite, result_queue, daa_list=daa_list)

    # if there are no audio media files in this directory (search by suffix,
    # e.g. '.mp3', '.flac', etc.) then (presume it's not a music album
    # directory) so return
    if not any(suffix in set([f.suffix.lower() for f in files]) for suffix in AUDIO_TYPES):
        log.debug('no audio media files within directory "%s"', dirp)
        return daa_list
    log.debug('found audio media files within directory "%s"', dirp)

    # if image file path already exists and not overwrite then return
    image_path = dirp.joinpath(image_nt)
    if image_path.exists():
        if not overwrite:
            log.info(
                'cover file "%s" exists and no overwrite, skip directory "%s"', image_nt, dirp
            )
            r_ = Result.SkipDueToNoOverwrite(
                artalb=None,
                imagesearcher=None,
                image_path=image_path,
                wropts=WrOpts(overwrite, False),
            )
            result_queue.put(r_)
            return daa_list
        else:
            log.debug('cover file "%s" exists and passed --overwrite', image_nt)

    # if dirp is already within daa_list then no further processing needed
    if dirp in [d_[0] for d_ in daa_list]:
        log.warning('directory "%s" already in daa_list', dirp)
        return daa_list

    # TODO: it would be good to take the most common strings found for
    #       artist and album among all media files found in the directory. It's
    #       probably common that audio media files vary in their correctness,
    #       e.g. some mp3 files may not have ID3 set, and some mp3 have the
    #       wrong ID3 'album' value.

    # TODO: related to prior TODO, Various Artists albums will have inconsistent
    #       Artist tag but consistent Album tag.

    files.sort()
    for fp in files:  # file path
        ext = fp.suffix.lower()
        if ext not in AUDIO_TYPES:
            continue
        # try to get media tag info from file
        artist = Artist("")
        album = Album("")
        try:
            ar, al = get_artist_album[ext](fp)
            # sometimes a long string of spaces is returned
            ar = Artist(ar.strip())
            al = Album(al.strip())
            # Don't overwrite prior good values with new empty values.
            # Also careful of special cases of 'Unknown Artist' (set for tag
            # 'WM/AlbumArtist' in poorly maintained .wma files)
            if not artist and ar and ar != Artist("Unknown Artist"):
                artist = Artist(ar)
            if not album and al and al != Album("Unknown Album"):
                album = Album(al)
        except Exception as err:
            log.error(
                'Exception: (%s) while processing file "%s"'
                % (
                    err,
                    fp,
                )
            )
            continue
        # if artist and album found, append to daa_list and return
        if artist and album:
            log.info('Album details found: %s within file "%s"', str_AA(artist, album), fp)
            daa = DirArtAlb((dirp, ArtAlb_new(artist, album)))

            # XXX: development self-check
            if daa in daa_list:
                log.warning('DAA "%s" already in daa_list1', daa)

            daa_list.append(daa)
            return daa_list

    # no Artist /Album data found within media files, guess the Artist • Album
    # based on directory name. Try several re patterns to match the directory
    # name
    # tuple of (re pattern, artist match group index, album match group index)
    # TODO: move this name matching subsection into an easily testable function
    artist = Artist("")
    album = Album("")
    bname = dirp.name
    for patt in [
        # Artist -- Year -- Album
        (r"""([\w\W]+) -- ([12][\d]{3}) -- ([\w\W]+)""", 0, 2),
        # Artist • Year • Album
        (r"""([\w\W]+) • ([12][\d]{3}) • ([\w\W]+)""", 0, 2),
        # Artist - Year - Album
        (r"""([\w\W]+) [\-] ([12][\d]{3}) [\-] ([\w\W]+)""", 0, 2),
        # Artist -- Album
        (r"""([\w\W]+) -- ([\w\W]+)""", 0, 1),
        # Artist • Album
        (r"""([\w\W]+) • ([\w\W]+)""", 0, 1),
        # Artist - Album
        (r"""([\w\W]+) - ([\w\W]+)""", 0, 1),
    ]:
        try:
            fm = re.fullmatch(patt[0], bname)
            if fm:
                ar = Artist(fm.groups()[patt[1]])
                al = Album(fm.groups()[patt[2]])
                if not artist:
                    artist = Artist(ar)
                if not album:
                    album = Album(al)
            if artist and album:
                log.info(
                    "Album details found: %s derived from " 'directory name "%s"',
                    str_AA(artist, album),
                    bname,
                )
                daa = DirArtAlb((dirp, ArtAlb_new(artist, album)))

                # XXX: development self-check
                if daa in daa_list:
                    log.warning('DAA "%s" already in daa_list2', daa)

                daa_list.append(daa)
                return daa_list
        # XXX: this except is too broad
        except:
            pass

    log.debug("no Artist or Album found or derived or no suitable media files" ' within "%s"', dirp)

    # XXX: This special case must be handled in implementations of
    #      `search_album_image`. It is used in
    #      `ImageSearcher_LikelyCover.search_album_image`.
    #      Not ideal.
    #      See Issue #7
    daa = DirArtAlb((dirp, ArtAlb_empty))

    # XXX: development self-check
    if daa in daa_list:
        log.warning('DAA "%s" already in daa_list3', daa)

    daa_list.append(daa)
    return daa_list


def process_dirs(
    dirs: List[Path],
    image_name: str,
    image_type: ImageType,
    overwrite: bool,
    result_queue: queue.SimpleQueue,
) -> DirArtAlb_List:
    """
    Gather list of directories where Album • Artist info can be derived.

    XXX: `process_dirs` and `process_dir` are inefficient. The "album cover search"
         tasks are not immediately handed off to the global task queues. Instead,
         this entire "album directory search phase" done within `process_dirs` must
         entirely complete before further processing. If this program was to be made
         faster, then this would be a good place ot start; handing off processing
         task to the global task queue for each "album directory" found as soon as
         possible.
    """
    log.debug("process_dirs()")

    daa_list: DirArtAlb_List = []
    for dir_ in dirs:
        log.debug('process_dirs loop "%s"', dir_)
        d_ = Path(dir_)
        image_nt = image_name + os.extsep + image_type.value
        daal = process_dir(d_, image_nt, overwrite, result_queue, daa_list=[])
        if daal:
            daa_list += daal

    # remove duplicates
    daa_list: DirArtAlb_List = list(set(daa for daa in daa_list))
    log.debug("directories to process:\n\t%s", pformat(daa_list))
    # sort
    daa_list.sort()

    return daa_list


disk_semaphore = threading.Semaphore(value=SEMAPHORE_COUNT_DISK)
network_semaphore = threading.Semaphore(value=SEMAPHORE_COUNT_NETWORK)


def search_create_image(
    artalb: ArtAlb,
    image_type: ImageType,
    image_path: Path,
    searches,
    googlecse_opts: GoogleCSE_Opts,
    discogs_args: Discogs_Args,
    referer: str,
    wropts: WrOpts,
    loglevel: int,
) -> Result:
    """
    Do the download using ImageSearchers given the needed data. Write image
    file data to `image_path`.
    Return count of bytes of image data written to file.
    """
    log.debug("  search_create_image(%s, …)", str_ArtAlb(artalb))

    # TODO: Have order of user requested searchers matter (i.e. note order of
    #       command-line arguments passed). Search in order of passed script
    #       options.

    search_likely, search_embedded, search_musicbrainz, search_discogs, search_googlecse = searches

    searchers = []
    if search_likely:
        searchers.append(
            ImageSearcher_LikelyCover(artalb, image_type, image_path, wropts, loglevel)
        )
    if search_embedded:
        searchers.append(
            ImageSearcher_EmbeddedMedia(artalb, image_type, image_path, wropts, loglevel)
        )
    if search_musicbrainz:
        searchers.append(
            ImageSearcher_MusicBrainz(artalb, image_type, image_path, wropts, loglevel)
        )
    if search_discogs:
        searchers.append(
            ImageSearcher_Discogs(artalb, image_type, image_path, discogs_args, wropts, loglevel)
        )
    if search_googlecse:
        searchers.append(
            ImageSearcher_GoogleCSE(
                artalb, image_type, image_path, googlecse_opts, referer, wropts, loglevel
            )
        )

    global disk_semaphore, network_semaphore

    # fallback result
    result = Result.NoSuitableImageFound(artalb, image_path, wropts)
    log.debug("  searching for %s", str_ArtAlb(artalb))
    for is_ in searchers:
        semaphore = None
        try:
            if is_.search_medium() is SearcherMedium.DISK:
                semaphore = disk_semaphore
            elif is_.search_medium() is SearcherMedium.NETWORK:
                semaphore = network_semaphore
            else:
                raise ValueError("Unknown SearcherMedium %s" % is_.search_medium())
            semaphore.acquire()

            res = is_.go()
            if not res:
                log.debug("  %s did not find an album cover image", is_.NAME)
                continue
            result = res
            break
        except Exception as ex:
            log.exception(ex)
        finally:
            if semaphore:
                semaphore.release()

    return result


def process_tasks(task_queue: queue.Queue, result_queue: queue.SimpleQueue) -> None:
    """
    Thread entry point.
    While things to process in task_queue then do so. This function will
    exit when task_queue.get raises Empty.

    TODO: it should be a speed improvement to differentiate between tasks that
          are more suited for parallel work (e.g. network requests) and those
          suited for sequential work (e.g. local disk reads). Currently, the
          task divvying does not distinguish.

    :param task_queue: queue of tasks (images to search for)
    :param result_queue: queue of attempts at downloads/copies, used for later
                        printing of program results
    :return: None
    """
    log.debug("→")

    while True:
        try:
            # don't block (use `get_nowait`) because the task_queue
            # is assumed to have been filled with tasks by now. It's only being
            # consumed at this point in the program.
            (
                daa,
                image_type,
                image_name,
                (
                    search_likely,
                    search_embedded,
                    search_musicbrainz,
                    search_discogs,
                    search_googlecse,
                ),
                googlecse_opts,
                discogs_args,
                referer,
                wropts,
                loglevel,
            ) = task_queue.get_nowait()
        except queue.Empty:  # catch Empty and return gracefully
            log.debug("←")
            return
        pathd, artalb = daa
        image_nt = image_name + image_type.suffix
        image_path = Path(pathd, image_nt)
        log.debug("☐ task: %s", str_ArtAlb(artalb))
        try:
            result = search_create_image(
                artalb,
                image_type,
                image_path,
                (
                    search_likely,
                    search_embedded,
                    search_musicbrainz,
                    search_discogs,
                    search_googlecse,
                ),
                googlecse_opts,
                discogs_args,
                referer,
                wropts,
                loglevel,
            )
            result_queue.put(result)
        except Exception as ex:
            log.exception(ex)

        log.debug("☑ task_done %s", str_ArtAlb(artalb))
        task_queue.task_done()


def parse_args_opts(
    args=None,
) -> Tuple[
    List[Path],
    ImageType,
    str,
    Tuple[
        bool,
        bool,
        bool,
        bool,
        bool,
    ],
    GoogleCSE_Opts,
    Discogs_Args,
    str,
    WrOpts,
    int,
]:
    """parse command line arguments and options"""

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.description = """\
This Python-based program is for automating downloading album cover art images.
A common use-case is creating a "cover.jpg" file for a collection of ripped
Compact Disc albums.

Given a list of directories, DIRS, recursively identify "album" directories.
"Album" directories have audio files, e.g. files with extensions like .mp3 or
.flac.  For each "album" directory, attempt to determine the Artist and Album.
Then find an album cover image file using the requested --search providers.  If
an album cover image file is found then write it to IMAGE_NAME.IMAGE_TYPE within
each "album" directory.

Audio files supported are %s.""" % ", ".join(
        AUDIO_TYPES
    )

    # TODO: Have order of requested searchers matter. Search in order of passed
    #       script options.

    argg = parser.add_argument_group("Required Arguments")
    argg.add_argument(
        dest="dirs",
        metavar="DIRS",
        action="append",
        type=str,
        nargs="+",
        help="directories to scan for audio files (Required)",
    )

    argg = parser.add_argument_group("Recommended")
    argg.add_argument(
        "-n",
        "--image-name",
        dest="image_name",
        action="store",
        default="cover",
        help="cover image file name IMAGE_NAME. This is the file"
        " name that will be created within passed DIRS. "
        " This will be appended with the preferred image"
        ' TYPE, e.g. "jpg", "png", etc.'
        ' (default: "%(default)s")',
    )
    argg.add_argument(
        "-i",
        "--image-type",
        dest="image_type",
        action="store",
        default=ImageType.list()[0],
        choices=ImageType.list(),
        help='image format IMAGE_TYPE (default: "%(default)s")',
    )
    argg.add_argument(
        "-o",
        "--overwrite",
        dest="overwrite",
        action="store_true",
        default=False,
        help="overwrite any previous file of the same file"
        " IMAGE_NAME and IMAGE_TYPE (default: %(default)s)",
    )

    argg = parser.add_argument_group("Search all")
    argg.add_argument(
        "-s*",
        "--search-all",
        dest="search_all",
        action="store_true",
        default=False,
        help="Search for album cover images using all methods and" " services",
    )
    argg.add_argument(
        "-s-",
        "--search-all-no-init",
        dest="search_all_noinit",
        action="store_true",
        default=False,
        help="Search for album cover images using all methods and"
        " services that do not require user initialization"
        " (e.g. no Google CSE, no Discogs).",
    )

    argg = parser.add_argument_group("Search the local directory for likely" " album cover images")
    argg.add_argument(
        "-sl",
        "--search-likely-cover",
        dest="search_likely",
        action="store_true",
        default=False,
        help="For any directory with audio media files but no"
        ' file "IMAGE_NAME.IMAGE_TYPE", search the directory'
        " for files that are likely album cover images. For"
        ' example, given options: --name "cover" --type'
        ' "jpg", and a directory of .mp3 files with a file'
        ' "album.jpg", it is reasonable to guess'
        ' "album.jpg" is a an album cover image file. So'
        ' copy file "album.jpg" to "cover.jpg" . This will'
        " skip an internet image lookup and download and"
        " could be a more reliable way to retrieve the"
        " correct album cover image.",
    )

    argg = parser.add_argument_group(
        "Search the local directory for an" " embedded album cover image"
    )
    argg.add_argument(
        "-se",
        "--search-embedded",
        dest="search_embedded",
        action="store_true",
        default=False,
        help="Search audio media files for embedded images. If"
        " found, attempt to extract the embedded image.",
    )

    argg = parser.add_argument_group("Search Musicbrainz NGS webservice")
    argg.add_argument(
        "-sm",
        "--search-musicbrainz",
        dest="search_musicbrainz",
        action="store_true",
        default=False,
        help="Search for album cover images using musicbrainz NGS"
        " webservice."
        " MusicBrainz lookup is the most reliable web search"
        " method.",
    )

    argg = parser.add_argument_group("Search Google Custom Search Engine (CSE)")
    gio = ImageSize.list()
    argg.add_argument(
        "-sg",
        "--search-googlecse",
        dest="search_googlecse",
        action="store_true",
        default=False,
        help="Search for album cover images using Google CSE."
        " Using the Google CSE requires an Engine ID and API"
        " Key. Google CSE reliability entirely depends upon"
        ' the added "Sites to search".'
        " The end of this help message has more advice"
        " around using Google CSE."
        " Google CSE is the most cumbersome search method.",
    )
    argg.add_argument(
        "-sgz",
        "--sgsize",
        dest="gsize",
        action="store",
        default=gio[len(gio) - 1],
        choices=gio,
        help="Google CSE optional image file size " '(default: "%(default)s")',
    )
    argg.add_argument(
        "--sgid",
        dest="gid",
        action="store",
        help='Google CSE ID (URL parameter "cx")'
        " typically looks like"
        ' "009494817879853929660:efj39xwwkng".  REQUIRED to use'
        " Google CSE.",
    )
    argg.add_argument(
        "--sgkey",
        dest="gkey",
        action="store",
        help='Google CSE API Key (URL parameter "key") typically'
        " looks like"
        ' "KVEIA49cnkwoaaKZKGX_OSIxhatybxc9kd59Dst". REQUIRED to'
        " use Google CSE.",
    )

    argg = parser.add_argument_group("Search Discogs webservice")
    argg.add_argument(
        "-sd",
        "--search-discogs",
        dest="search_discogs",
        action="store_true",
        default=False,
        help="Search for album cover images using Discogs webservice.",
    )
    argg.add_argument(
        "-dt",
        "--discogs-token",
        dest="discogs_token",
        action="store",
        default="",
        help="Discogs authentication Personal Access Token.",
    )

    argg = parser.add_argument_group("Debugging and Miscellanea")
    argg.add_argument("-v", "--version", action="version", version=__version__)
    argg.add_argument(
        "-r",
        "--referer",
        dest="referer",
        action="store",
        default=REFERER_DEFAULT,
        help="Referer url used in HTTP GET requests" ' (default: "%(default)s")',
    )
    argg.add_argument(
        "-d",
        "--debug",
        dest="debug",
        action="count",
        default=0,
        help="Print debugging messages. May be passed twice.",
    )
    argg.add_argument(
        "--test",
        dest="test",
        action="store_true",
        default=False,
        help="Only test, do not write any files",
    )

    parser.epilog = (
        """\
This program attempts to create album cover image files for the passed DIRS.  It
does this several ways, searching for album cover image files already present in
the directory (-sl).  If not found, it attempts to figure out the Artist and
Album for that directory then searches online services for an album cover image
(-sm or -sg).

Directories are searched recursively.  Any directory that contains one or more
with file name extension """
        + " or ".join(AUDIO_TYPES)
        + """
is presumed to be an album directory.  Given a directory of such files, file
contents will be read for the Artist name and Album name using embedded audio
tags (ID3, Windows Media, etc.).  If no embedded media tags are present then a
reasonable guess will be made about the Artist and Album based on the directory
name; specifically this will try to match a directory name with a pattern like
"Artist - Year - Album" or "Artist - Album".
From there, online search services are used to search for the required album
cover image. If found, it is written to the album directory to file name
IMAGE_NAME.IMAGE_TYPE (-n … -i …).

If option --search-googlecse is chosen then you must create your Google Custom
Search Engine (CSE).  This can be setup at https://cse.google.com/cse/all .  It
takes about 5 minutes.  This is where your own values for --sgid and --sgkey can
be created. --sgid is "Search engine ID" (URI parameter "cx") and --sgkey is
under the "Custom Search JSON API" from which you can generate an API Key (URI
parameter "key"). A key can be generated at
https://console.developers.google.com/apis/credentials.
Google CSE settings must have "Image search" as "ON"  and "Search the entire
web" as "OFF".

If option --search-discogs is chosen then you must pass a Discogs Personal
Access Token (PAT). A PAT is a forty character string generated at
https://www.discogs.com/settings/developers with the button "Generate new token".
Requires a discogs account.
Discogs does rate-limit throttling which this program will wait on. It significantly
increases the time to search for candidate album cover images.

Shortcomings:

- Does not handle Various Artist albums.

- --search-discogs can only retrieve jpg file no matter the --image-type passed.

- Multi-threading is only a rudimentary implementation. Does not efficiently queue
  non-overlapping tasks, i.e. the artist-album directory search phase must entirely
  finish before the album cover search phase begins, e.g. will not do HTTP searches
  as soon as possible.

PyPi project: %s
Source code: %s

Inspired by the program coverlovin."""
        % (
            __url_project__,
            __url_source__,
        )
    )

    args = parser.parse_intermixed_args(args)

    if args.search_all:
        args.search_likely = True
        args.search_embedded = True
        args.search_musicbrainz = True
        args.search_discogs = True
        args.search_googlecse = True

    if args.search_all_noinit:
        args.search_likely = True
        args.search_embedded = True
        args.search_musicbrainz = True
        if args.search_googlecse:
            log.warning(
                "--search-googlecse was selected while --search-all-noinit was also selected"
            )
        if args.search_discogs:
            log.warning("--search-discogs was selected while --search-all-noinit was also selected")

    if not (
        args.search_likely
        or args.search_musicbrainz
        or args.search_googlecse
        or args.search_embedded
        or args.search_discogs
    ):
        parser.error(
            "no selected search method. Select a search, e.g. -sl or " "--search-musicbrainz or -s*"
        )

    if args.search_googlecse:
        if not args.gid:
            parser.error("passed --search-googlecse (-sg or -s*) so --sgid is" " also required")
        if not args.gkey:
            parser.error("passed --search-googlecse (-sg or -s*) so --sgkey is" " also required")
    elif args.gkey or args.gkey:
        log.warning(
            "not passed --search-googlecse (-sg) so --sgkey and --sgid" " are not necessary"
        )

    if args.search_discogs:
        if not args.discogs_token:
            parser.error(
                "Using --search-discogs (-sd) requires passing --discogs-token DISCOGS_TOKEN"
            )

    if args.search_musicbrainz:
        try:
            import musicbrainzngs
        except ModuleNotFoundError as err:
            log.error("MusicBrainz library must be installed\n" "   pip install musicbrainzngs")
            raise err

    loglevel = logging.WARNING
    if args.debug == 1:
        loglevel = logging.INFO
    elif args.debug >= 2:
        loglevel = logging.DEBUG

    return (
        args.dirs[0],
        ImageType(args.image_type),
        args.image_name,
        (
            args.search_likely,
            args.search_embedded,
            args.search_musicbrainz,
            args.search_discogs,
            args.search_googlecse,
        ),
        GoogleCSE_Opts(args.gkey, args.gid, ImageSize(args.gsize)),
        Discogs_Args(args.discogs_token),
        args.referer,
        WrOpts(args.overwrite, args.test),
        loglevel,
    )


def main() -> int:
    """
    Recursively download cover images for music files in a
    given directory and its sub-directories
    """
    (
        dirs,
        image_type,
        image_name,
        (search_likely, search_embedded, search_musicbrainz, search_discogs, search_googlecse),
        googlecse_opts,
        discogs_args,
        referer,
        wropts,
        loglevel,
    ) = parse_args_opts()

    log.setLevel(loglevel)

    # XXX: task queuing does not adequately distinguish SearcherMedium.DISK
    #      tasks and SearcherMedium.NETWORK tasks

    # results of attempting to update directories
    # (SimpleQueue is an unbounded queue, new in Python 3.7!)
    result_queue = queue.SimpleQueue()

    # gather list of directories where Album • Artist info can be derived.
    # 'daa' is a DirArtAlb tuple
    daa_list = process_dirs(dirs, image_name, image_type, wropts.overwrite, result_queue)
    print("Found {0} Album directories.".format(len(daa_list)))

    #
    # do the remaining tasks in separate threads relying on a Queue
    # to multiplex those tasks
    #

    task_queue = queue.Queue()
    for daa in daa_list:
        task_queue.put(
            (
                daa,
                image_type,
                image_name,
                (
                    search_likely,
                    search_embedded,
                    search_musicbrainz,
                    search_discogs,
                    search_googlecse,
                ),
                googlecse_opts,
                discogs_args,
                referer,
                wropts,
                loglevel,
            )
        )
        log.debug("Queued task path '%s'", str(daa[0]))

    # When there are few directories to process then no need to start extra
    # threads.
    # XXX: task queues does not distinguish SearcherMedium.DISK queues and
    #      SearcherMedium.NETWORK queues. Would be much faster if it did.
    task_queue_thread_count = min(TASK_QUEUE_THREAD_COUNT, len(daa_list))
    log.debug("Starting %s threads for task queue…", task_queue_thread_count)
    for tc_ in range(task_queue_thread_count):
        th = threading.Thread(target=process_tasks, args=(task_queue, result_queue))
        # daemon: don't wait on threads, task_queue signals when complete
        th.daemon = True
        log.debug("Thread %s starting…", tc_ + 1)
        th.start()

    # `.join` returns when task_queue is empty of tasks (task_done)
    task_queue.join()
    # done with all the hard work

    # pop all result from the queue into a list
    results: List[Result] = []
    try:
        while True:
            result = result_queue.get_nowait()
            results.append(result)
    except queue.Empty:
        pass

    # print results and exit gracefully
    if not results:
        print("No album cover images could be found.")
        return 0

    results_table = []
    count_total = 0
    count_image = 0
    for r_ in results:
        sAA = ""
        if r_.artalb:
            sAA = str_ArtAlb(r_.artalb)
        # TODO: the Results class should be an Enum or contain an Enum
        #       that would allow a more informative summary table ending.
        #       currently, summary table does not distinguish between
        #       new files, copied files, extracted files, already found files
        #       or errors, no suitable image.
        if not r_:
            results_table.append(("✗", sAA, r_.message, r_.image_path.parent))
        else:
            results_table.append(("✓", sAA, r_.message, r_.image_path))
            count_image += 1
        count_total += 1
    sys.stderr.flush()
    sys.stdout.flush()
    print(
        tabulate(
            results_table,
            ("", "Artist & Album", "Result", "Path"),
            colalign=("left", "left", "left", "left"),
        )
    )
    print(
        "Among {} Album directories, wrote or found {} '{}{}' files.".format(
            count_total,
            count_image,
            image_name,
            image_type.suffix,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
