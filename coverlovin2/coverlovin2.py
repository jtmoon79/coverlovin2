#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-

"""
Recursively process subdirectories looking for audio media files. Download
 appropriate cover images for the directory that is presumed to be an album.

The author wanted to learn more about the unexpected and welcome addition of
type-hinting in Python. Code in this file uses several methods of type-hinting.
Some readers might think it's overzealous. Others might welcome it.

This also makes use of inheritance decorators @overrides and @abstractmethod.
"""

__author__ = 'James Thomas Moon'
__url__ = 'https://github.com/jtmoon79/coverlovin2'
__url_source__ = __url__
__url_project__ = 'https://pypi.org/project/CoverLovin2/'
__version__ = '0.5.3'  # canonical version (don't set version anywhere else)
__doc__ = \
    """Recursively process passed directories of audio media files, attempting
 to create a missing album image file, either via local searching and
 copying, or via downloading from various online services."""


#
# stdlib imports
#
import sys
# XXX: PEP8 complains about this occurring. But do this check sooner so the
#      user does not install non-standard libraries (due to import failures)
#      only to find out they used the wrong version of Python 3.
if sys.version_info < (3, 7):
    raise Exception('This script is meant for python 3.7 or newer and will fail'
                    ' using this python version %s' % sys.version)
import os
import json
import re
import urllib.request
import urllib.error
import urllib.parse
import argparse  # ArgumentParser
import shutil  # copy2
import difflib  # SequenceMatcher
import collections  # defaultdict
import abc  # ABC, abstractmethod
import io  # BytesIO
# threading stuff
import threading
import queue  # Queue, SimpleQueue Empty
# logging and printing
import logging
from pprint import pformat
from pprint import pprint as pp  # for help live-debugging

#
# non-standard imports
#
# XXX: PEP8 complaint that this is not used.  But try this import before going
#      too far.
import mutagen  # see README.md for installation help

#
# type hints and type precision
#
from pathlib import Path
import typing  # Union, NewType, Tuple, List
import enum  # Enum
import collections  # namedtuple

#
# Using a few different methods for typing things.
#
Artist = typing.NewType('Artist', str)
Album = typing.NewType('Album', str)
# ('Dir'ectory, 'Art'ist, 'Alb'um)
DirArtAlb = typing.NewType('DirArtAlb', typing.Tuple[Path, Artist, Album])
DirArtAlb_List = typing.List[DirArtAlb]
Path_List = typing.List[Path]


class URL(str):
    """string type with constraints on values.
    The value must look like an http* URL string.

    Immutable types are treated differently when inherited:
    https://stackoverflow.com/a/2673863/471376
    """
    def __new__(cls, *value):
        if value:
            v0 = value[0]
            if not type(v0) is str:
                raise TypeError('Unexpected type for URL: "%s"' % type(v0))
            if not (v0.startswith('http://') or v0.startswith('https://')):
                raise ValueError('Passed string value "%s" is not an'
                                 ' "http*://" URL' % (v0,))
        # else allow None to be passed. This allows an "empty" URL, `URL()` that
        # evaluates False
        return str.__new__(cls, *value)


#
# Google CSE Options
#

# (API Key, CX ID, Image Size)
#GoogleCSE_Key = typing.NewType('GoogleCSE_Key', str)
#GoogleCSE_ID = collections.namedtuple('GoogleCSE_ID', str)
#GoogleCSE_Opts = typing.NewType('GoogleCSE_Opts', typing.Tuple[GoogleCSE_Key,
#                                GoogleCSE_ID,
#                                str])):


class ImageSize(enum.Enum):
    """must match https://developers.google.com/custom-search/v1/cse/list"""

    SML = 'small'
    MED = 'medium'
    LRG = 'large'

    @classmethod
    def list(cls) -> typing.List[str]:
        return [is_.value for is_ in ImageSize]


# Tying out namedtuple for typing this.
# XXX: AFAICT, cannot type-hint the attributes within the namedtuple.
# TODO: use typing.NamedTuple
class GoogleCSE_Opts(collections.namedtuple('GoogleCSE_Opts',
                                            'key id image_size')):

    # XXX: How to best `assert image_size in ImageSize.list()` ?

    def __bool__(self):
        if self.id and self.key and self.image_size:
            return True
        return False


class ImageType(enum.Enum):
    """Improve these from just a `str` to a highly typed object."""

    JPG = 'jpg'
    PNG = 'png'
    GIF = 'gif'

    @property
    def suffix(self) -> str:
        return os.extsep + self.value

    @property
    def re_suffix(self) -> str:
        # JPG files can match '.jpg' and '.jpeg'
        if self is ImageType.JPG:
            return re.escape(os.extsep) + r'jp[e]?g'
        return re.escape(self.suffix)

    @staticmethod
    def list() -> typing.List:
        return [it.value for it in ImageType]

    @staticmethod
    def ImageFromFormat(fmt: str):
        """from PIL.Image.format string to corresponding ImageType instance
        return None if none found"""
        fmt = fmt.lower()
        if fmt == 'jpeg':  # this darn special case!
            return ImageType.JPG
        try:
            ImageType(fmt)
        except ValueError:
            return None
        return ImageType(fmt)


def overrides(interface_class):
    """
    Function decorator.  Will raise at program start if super-class does not
    implement the overridden function.
    Corollary to @abc.abstractmethod.
    Modified from answer https://stackoverflow.com/a/8313042/471376
    """
    def confirm_override(method):
        if method.__name__ not in dir(interface_class):
            raise NotImplementedError('function "%s" is an @override but that'
                                      ' function is not implemented in base'
                                      ' class %s'
                                      % (method.__name__,
                                         interface_class)
                                      )

        def func():
            pass

        attr = getattr(interface_class, method.__name__)
        if type(attr) is not type(func):
            raise NotImplementedError('function "%s" is an @override'
                                      ' but that is implemented as type %s'
                                      ' in base class %s, expected implemented'
                                      ' type %s'
                                      % (method.__name__,
                                         type(attr),
                                         interface_class,
                                         type(func))
                                      )
        return method
    return confirm_override


def str_AA(artist: Artist, album: Album) -> str:
    return '｛ "%s" • "%s" ｝' % (artist, album)


def log_new(logformat: str, level: int, logname: str = None) \
        -> logging.Logger:
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


# recomended format
LOGFORMAT = '%(levelname)s: [%(threadName)s %(name)s]: %(message)s'
# the file-wide logger instance
log = log_new(LOGFORMAT, logging.INFO)

REFERER_DEFAULT = __url__
# task_queue has this many threads consuming tasks
TASK_THREAD_COUNT = 8


#
# helper functions
#
func_name = lambda n=0: sys._getframe(n + 1).f_code.co_name

#
# audio file types (i.e. file name extensions)
#

def get_artist_album_mp3(ffp: Path) -> typing.Tuple[Artist, Album]:
    """
    :param ffp: full file path of .mp3 file
    :return: (artist, album)
    """
    from mutagen.easyid3 import EasyID3
    media = EasyID3(ffp)

    artist = ''
    try:
        artist = media['artist'][0]
    except KeyError:
        pass
    except IndexError:
        pass
    try:
        if not artist:
            artist = media['albumartist'][0]
    except KeyError:
        pass
    except IndexError:
        pass

    album = ''
    try:
        album = media['album'][0]
    except KeyError:
        pass
    except IndexError:
        pass

    return Artist(artist), Album(album)


def get_artist_album_mp4(ffp: Path) -> typing.Tuple[Artist, Album]:
    """
    :param ffp: full file path of media file
    :return: (artist, album)
    """
    from mutagen.easymp4 import EasyMP4
    media = EasyMP4(ffp)

    artist = ''
    try:
        artist = media['artist'][0]
    except KeyError:
        pass
    except IndexError:
        pass

    album = ''
    try:
        album = media['album'][0]
    except KeyError:
        pass
    except IndexError:
        pass

    return Artist(artist), Album(album)

def get_artist_album_flac(ffp: Path) -> typing.Tuple[Artist, Album]:
    """
    :param ffp: full file path of media file
    :return: (artist, album)
    """
    from mutagen.flac import FLAC
    media = FLAC(ffp)

    artist = ''
    try:
        artist = media['ARTIST'][0]
    except KeyError:
        pass
    except IndexError:
        pass

    album = ''
    try:
        album = media['ALBUM'][0]
    except KeyError:
        pass
    except IndexError:
        pass

    return Artist(artist), Album(album)

def get_artist_album_ogg(ffp: Path) -> typing.Tuple[Artist, Album]:
    """
    :param ffp: full file path of media file
    :return: (artist, album)
    """
    from mutagen.oggvorbis import OggVorbis
    media = OggVorbis(ffp)

    artist = ''
    try:
        artist = media.tags['ARTIST'][0]
    except:
        pass
    try:
        if not artist:
            artist = media.tags['ARTIST'][1]
    except:
        pass
    try:
        if not artist:
            artist = media.tags['artist'][0]
    except:
        pass
    try:
        if not artist:
            artist = media.tags['artist'][1]
    except:
        pass
    try:
        if not artist:
            artist = media.tags['albumartist'][0]
    except:
        pass
    try:
        if not artist:
            artist = media.tags['albumartist'][1]
    except:
        pass

    album = Album('')
    try:
        album = media.tags['ALBUM'][0]
    except:
        pass
    try:
        if not album:
            album = media.tags['ALBUM'][1]
    except:
        pass
    try:
        if not album:
            album = media.tags['album'][0]
    except:
        pass
    try:
        if not album:
            album = media.tags['album'][1]
    except:
        pass

    return Artist(artist), Album(album)

def get_artist_album_asf(ffp: Path) -> typing.Tuple[Artist, Album]:
    """
    :param ffp: full file path of media file
    :return: (artist, album)
    """
    from mutagen.asf import ASF
    media = ASF(ffp)

    artist = ''
    try:
        artist = str(media.tags['Author'][1])
    except:
        pass
    try:
        if not artist:
            artist = str(media.tags['Artist'][1])
    except:
        pass
    try:
        if not artist:
            artist = str(media.tags['WM/AlbumArtist'][1])
    except:
        pass
    try:
        if not artist:
            artist = str(media.tags['Author'][0])
    except:
        pass
    try:
        if not artist:
            artist = str(media.tags['Artist'][0])
    except:
        pass
    try:
        if not artist:
            artist = str(media.tags['WM/AlbumArtist'][0])
    except:
        pass

    album = ''
    try:
        album = str(media.tags['Album'][1])
    except:
        pass
    try:
        if not album:
            album = str(media.tags['WM/AlbumTitle'][1])
    except:
        pass
    try:
        if not album:
            album = str(media.tags['Album'][0])
    except:
        pass
    try:
        if not album:
            album = str(media.tags['WM/AlbumTitle'][0])
    except:
        pass

    return Artist(artist), Album(album)


# associate file extension to retrieval helper functions
audio_type_get_artist_album = {
    '.mp3': get_artist_album_mp3,
    '.m4a': get_artist_album_mp4,
    '.mp4': get_artist_album_mp4,
    '.flac': get_artist_album_flac,
    '.ogg': get_artist_album_ogg,
    '.wma': get_artist_album_asf,
    '.asf': get_artist_album_asf
}
AUDIO_TYPES = list(audio_type_get_artist_album.keys())


def sanitise(param: str):
    """sanitise a string for use as a url parameter"""
    if not param:
        return ''
    return urllib.parse.quote(param)


def similar(title1: str, title2: str) -> float:
    """
    :return: float value between 0 to 1 where higher value means more
             similarity among passed string values
    """
    return difflib.SequenceMatcher(None, title1, title2).ratio()


class ImageSearcher(abc.ABC):
    NAME = __qualname__

    def __init__(self, referer: str, debug: bool):
        self.referer = referer
        self._image_bytes = bytes()
        self.result_message = ''
        # setup new logger for this class instance
        self._logname = self.NAME + '(' + str(id(self)) + ')'
        self._log = log_new(LOGFORMAT,
                            logging.DEBUG if debug else logging.INFO,
                            self._logname)
        super().__init__()


    @abc.abstractmethod
    def search_album_image(self, artist: Artist, album: Album,
                        image_type: ImageType) -> bytes:
        pass

    @staticmethod
    def download_url(url: URL, log_: logging.Logger) -> bytes:
        """
        Download the data from the url, return it as bytes. Return None upon
        failure.
        """

        assert URL(url), 'empty URL'

        try:
            log_.debug('image download urllib.request.urlopen("%s")', url)
            response = urllib.request.urlopen(url, None, 10)
        except Exception as err:
            log_.exception(err, exc_info=True)
            return bytes()

        image_bytes = response.read()

        # XXX: development self-check
        assert type(image_bytes) is bytes, \
            'expected response data type %s, got %s' % \
            (type(bytes), type(image_bytes))

        return image_bytes

    def write_album_image(self, image_path: Path, overwrite: bool, test: bool)\
            -> bool:
        """Write `self.image_bytes` to Path `image_path`

        :param image_path: full file path to image file
        :param overwrite: if (overwrite and file exists) then write new file
                          else return
        :param test: if test do not actually write anything
        """
        assert self._image_bytes, 'Error: self._image_bytes not set. Was ' \
                                  '%s.search_album_image called?' % self.NAME

        if image_path.exists() and not overwrite:
            self._log.debug('file already exists and --overwrite not enabled;'
                           ' skipping "%s"', image_path)
            return False

        if test:
            self.result_message = '(--test-only) %s would have wrote %d bytes'\
                ' to "%s"' % (self.NAME, len(self._image_bytes), image_path)
            self._log.debug(self.result_message)
            return True

        with open(image_path, 'wb+') as fh:
            fh.write(self._image_bytes)

        self.result_message = '%s wrote %d bytes to "%s"' % \
                              (self.NAME, len(self._image_bytes), image_path)
        self._log.debug(self.result_message)

        return True


class ImageSearcher_LikelyCover(ImageSearcher):
    """
    ImageSearcher that searches the parent directory of passed `image_path`
    for files that are likely cover files, e.g. 'album.jpg' or 'album_front.jpg'
    It searches for matching image types (using file extension), e.g. image_path
    with file name extension '.png' only searches for other '.png' files.
    If a suitable file is found then copy that file to `image_path`.
    """
    NAME = __qualname__

    def __init__(self, image_path: Path, referer: str, debug: bool):
        self.copy_src = None
        self.copy_dst = image_path
        super().__init__(referer, debug)

    def _match_likely_name(self, image_type: ImageType,
                           files: typing.Sequence[Path])\
            -> typing.Union[None, Path]:
        """
        Given a sequence of image files (Paths), find the most likely album cover
        match by analyzing the image file name.

        This function makes no changes to the class instance.

        :param image_type: ImageType to look for
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
        candidates_by_pref: typing.DefaultDict[int, typing.List[Path]] = \
            collections.defaultdict(list)

        # These re patterns are ordered by preference.
        # For example, if there are files "AlbumArtSmall.jpg" and
        # "AlbumArtLarge.jpg" then this ordering will prefer "AlbumArtLarge.jpg"
        # as the eventual self.copy_src.
        patterns = [
            # AlbumArtLarge.jpg
            # AlbumArt_{74AF69EF-02BA-43F5-B54B-3A379289FBEB}_Large.jpg
            r'''AlbumArt.*Large''' + image_type.re_suffix,
            # AlbumArtSmall.jpg
            # AlbumArt_{74AF69EF-02BA-43F5-B54B-3A379289FBEB}_Small.jpg
            r'''AlbumArt.*Small''' + image_type.re_suffix,
            # albumcover.jpg
            # album cover.jpg
            # album_cover.jpg
            r'''album[ \-_]?cover''' + image_type.re_suffix,
            # album.jpg
            # album_something.jpg
            r'''album[ \-_]?.*''' + image_type.re_suffix,
            # Something (album cover).jpg
            r'''.*[ \-_]+\(album[ \-_]cover\)''' + image_type.re_suffix,
            # AlbumArt01.jpg
            r'''AlbumArt[\w]+''' + image_type.re_suffix,
            # Something (front cover) blarg.jpg
            r'''.* \(front cover\)''' + image_type.re_suffix,
            # Something (cover front) blarg.jpg
            r'''.* \(cover front\)''' + image_type.re_suffix,
            # Something (front).jpg
            r'''.*[ \-_]\(front\)''' + image_type.re_suffix,
            # Something (front) blarg.jpg
            r'''.*[ \-_]\(front\)[ \-_].*''' + image_type.re_suffix,
            # Something Front Cover.jpg
            r'''.*[ \-_]front[ \-_]cover''' + image_type.re_suffix,
            # Something Cover Front.jpg
            r'''.*[ \-_]cover[ \-_]front''' + image_type.re_suffix,
            # front.jpg
            # front_something.jpg
            # front-something.jpg
            # front something.jpg
            r'''front[ \-_][\w]*''' + image_type.re_suffix,
            # Something-front.jpg
            # Something_front.jpg
            r'''.*[\-_]front''' + image_type.re_suffix,
            # Something-front-blarg.jpg
            # Something_front_blarg.jpg
            # Something - front - blarg.jpg
            # Something-front_cover-blarg.jpg
            r'''.*[\-_ ]front[\-_ ][\w]+''' + image_type.re_suffix,
            # Something_something_album_cover.jpg
            r'''.*[ \-_]+album_cover''' + image_type.re_suffix,
            # folder.jpg
            r'''folder''' + image_type.re_suffix,
            # cover.jpg
            # Something cover.jpg
            # Something_cover.jpg
            r'''.*[ \-_]?cover''' + image_type.re_suffix,
            # R-3512668-1489953889-2577 cover.jpeg.jpg
            r'''.*[\W]cover[\W].*''' + image_type.re_suffix,
            # Side A.jpg
            r'''.*[ \-_]Side A''' + image_type.re_suffix,
            # Side 1.jpg
            r'''.*[ \-_]Side 1''' + image_type.re_suffix,
            # SOMETHINGFRONT.JPG
            r'''.*front''' + image_type.re_suffix,
        ]

        for filep in files:
            for index, pattern in enumerate(patterns):
                try:
                    fm = re.fullmatch(pattern, filep.name, flags=re.IGNORECASE)
                    if fm:
                        if filep == self.copy_dst \
                           and self.copy_dst.exists():
                            self._log.debug('Matched name "%s" to pattern "%s" '
                                            'but that is the same file as the '
                                            'destination file!',
                                            filep.name, pattern)
                        else:
                            self._log.debug('Matched name "%s" to pattern "%s"',
                                            filep.name, pattern)
                            candidates_by_pref[index].append(filep)
                except Exception as ex:
                    self._log.exception(ex, exc_info=True)

        #
        # Look for a file with a name similar to the directory name, this is
        # likely the album cover. e.g. "ACDC - TNT/acdc_tnt.jpg" means file
        # "acdc_tnt.jpg" is likely the album cover file within the album
        # directory "ACDC - TNT".
        # The similar score must be above 0.4 to be considered.
        #
        dirp = self.copy_dst.parent
        score_max = 0.4
        score_candidate = None
        for filep in files:
            score = similar(filep.name, dirp.name)
            if score > score_max:
                score_max = score
                score_candidate = filep
                self._log.debug('File "%s" is similar (%f) to directory'
                                ' name "%s"', filep.name, score, dirp.name)

        if not candidates_by_pref and not score_candidate:
            self._log.debug('No likely pattern matched, similar named file')
            return None

        # choose the most preferred file: select the lowest key value
        if candidates_by_pref:
            cands = candidates_by_pref[
                sorted(candidates_by_pref.keys())[0]
            ]
            # XXX: mypy says this doesn't make sense
            # XXX: debug self-check
            if len(cands) > 1:
                self._log.debug('Note: multiple values in copy_src, choosing'
                                ' the first from:\n%s', pformat(cands))
            copy_src = cands[0]
        elif score_candidate:
            copy_src = score_candidate
        else:
            self._log.error('Bad if-elif, cannot find a candidate')
            return None

        return copy_src

    @overrides(ImageSearcher)
    def search_album_image(self, _1: Artist, _2: Album, image_type: ImageType)\
            -> bool:
        """
        Search `self.copy_dst.parent` for a file that is very likely an album
        cover image.

        TODO: also check sub-directory .mediaartlocal for an image file
        """
        self._log.debug('search_album_image(…) self.copy_dst="%s"',
                        self.copy_dst)

        candidates = []  # files that are of the same media image type
        try:
            re_suffix_exact = '^' + image_type.re_suffix + '$'
            for fp in self.copy_dst.parent.iterdir():  # 'fp' means file path
                if fp.is_file() and re.match(re_suffix_exact, fp.suffix,
                                             flags=re.IGNORECASE):
                    candidates.append(fp)
        except OSError as ose:
            self._log.exception(ose)

        self.copy_src = self._match_likely_name(image_type, candidates)  # type: ignore
        if not self.copy_src:
            return False

        return True

    class WrongUseError(Exception):
        pass

    @overrides(ImageSearcher)
    def write_album_image(self, _: Path, overwrite: bool, test: bool)\
            -> bool:
        """
        Copy `self._image_bytes` file from `copy_src` to `copy_dst`

        :param _: image_path but is not used by this function override
        :param overwrite: if (overwrite and file exists) then write new file
                          else return
        :param test: if test do not actually write anything
        """
        self._log.debug('write_album_image(…)')

        if not self.copy_src:
            raise self.WrongUseError('self.copy_src is not set, must call'
                                     ' search_album_image before calling'
                                     ' write_album_image')

        # sanity self-checks
        assert self.copy_src and self.copy_dst, \
            'Something is wrong, copy_src and/or copy_dst is not set\n' \
            'cpy_src: "%s"\ncpy_dst: "%s"' % (self.copy_src, self.copy_dst)
        assert self.copy_src.is_file(), 'copy_src "%s" is not a file⁈' % \
            self.copy_src

        if self.copy_src == self.copy_dst:
            self.warning('copying the same file to itself⁈ "%s"',
                         self.copy_src)
        # it's somewhat pointless to pass image_path since copy_dst should be
        # the same, but image_path is passed only for sake of consistency with
        # sibling classes. So may as well do this sanity check. Then forget
        # about image_path.
        #assert self.copy_dst == image_path, \
        #    'Something is wrong, expected copy_dst and passed image_path to ' \
        #    'be the same\n"%s" ≠ "%s"' % (self.copy_dst, image_path)

        if self.copy_dst.exists() and not overwrite:
            self._log.info('file already exists and --overwrite not enabled;'
                           ' skipping "%s"', self.copy_dst)
            return False

        if test:
            self.result_message = '(--test-only) %s would have copied "%s"' \
                                  ' to "%s"' % (self.NAME, self.copy_src,
                                                self.copy_dst)
            self._log.debug(self.result_message)
            return True

        shutil.copy2(self.copy_src, self.copy_dst)

        self.result_message = '%s copied "%s" to "%s"' % \
                               (self.NAME, self.copy_src, self.copy_dst)
        self._log.debug(self.result_message)

        return True


class ImageSearcher_EmbeddedMedia(ImageSearcher):
    """
    ImageSearcher that searches the media files for an embedded image.
    """
    NAME = __qualname__

    def __init__(self, image_path: Path, referer: str, debug: bool):
        self.copy_dst = image_path
        self._image = None
        self._image_src = None
        self._image_type = None
        super().__init__(referer, debug)

    @overrides(ImageSearcher)
    def search_album_image(self, _1: Artist, _2: Album, image_type: ImageType) \
            -> bool:
        """
        Search `self.copy_dst.parent` for an audio media file that contains
        an embedded album cover image
        """
        self._log.debug('search_album_image(…) self.copy_dst="%s"',
                        self.copy_dst)

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
        from PIL import Image
        key_apic = 'APIC:'
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
                image = Image.open(io.BytesIO(image_data))
            except:
                continue
            # the PIL.Image will later be PIL.Image.save to the
            # self._image_type type (i.e. it will be format converted by the PIL
            # module)
            self._image_type = ImageType.ImageFromFormat(image.format)
            if not self._image_type:
                continue
            self._image = image
            self._image.size_pixels = image.height * image.width
            self._image_src = fp
            return True

        return False

    class WrongUseError(Exception):
        pass

    @overrides(ImageSearcher)
    def write_album_image(self, _: Path, overwrite: bool, test: bool) \
            -> bool:
        """
        extract embedded image from `self._image`.

        :param _: image_path but is not used by this function override
        :param overwrite: if (overwrite and file exists) then write new file
                          else return
        :param test: if test do not actually write anything
        """
        self._log.debug('write_album_image(…)')

        if not self._image:
            raise self.WrongUseError('self._image is not set, must call'
                                     ' search_album_image before calling'
                                     ' write_album_image')
        if not self._image_type:
            raise ValueError('self._image_type not set, something is wrong')

        if self.copy_dst.exists() and not overwrite:
            self._log.info('file already exists and --overwrite not enabled;'
                           ' skipping "%s"', self.copy_dst)
            return False

        if test:
            self.result_message = '(--test-only) %s extracted %d pixels from' \
                                  ' "%s", wrote to "%s"' \
                                  % (self.NAME, self._image.size_pixels,
                                     self._image_src, self.copy_dst)
            self._log.debug(self.result_message)
            return True

        self._image.save(self.copy_dst, self._image_type.value.upper())

        self.result_message = '%s extracted %d pixels from "%s", wrote to "%s"'\
                              % (self.NAME, self._image.size_pixels,
                                 self._image_src, self.copy_dst)
        self._log.debug(self.result_message)

        return True


class ImageSearcher_GoogleCSE(ImageSearcher):
    NAME = __qualname__

    # google_search_api = 'https://cse.google.com/cse'
    google_search_api = 'https://www.googleapis.com/customsearch/v1'

    def __init__(self, google_opts: GoogleCSE_Opts, referer: str, debug: bool):
        self.__google_opts = google_opts
        self.key = google_opts.key
        self.cxid = google_opts.id
        self.image_size = google_opts.image_size
        super().__init__(referer, debug)

    def __bool__(self):
        return bool(self.__google_opts)

    def _search_response_json(self, request, *args, **kwargs):
        """Add wrapper so it may be overridden by a testing harness (pytest)"""
        return urllib.request.urlopen(request, *args, **kwargs)

    @overrides(ImageSearcher)
    def search_album_image(self, artist: Artist, album: Album,
                           image_type: ImageType) -> bool:
        self._log.debug('search_album_image("%s", "%s", …)', artist, album)

        if not artist and not album:
            return False

        # construct url, parameters documented at
        # https://developers.google.com/custom-search/v1/using_rest
        url = URL(
            ImageSearcher_GoogleCSE.google_search_api
                + '?'
                + 'key=' + self.key
                + '&cx=' + self.cxid
                + '&prettyPrint=true'
                + '&q=' + sanitise(artist) + '+' + sanitise(album)
                + '&fileType=' + image_type.value
                + '&imgSize=' + self.image_size.value
                + '&imgColorType=color'
                + '&searchType=image'
                + '&fields=items(title,link,image(thumbnailLink))'
                + '&num=' + str(1)
        )
        request = urllib.request.Request(url, data=None,
                                         headers={'Referer': self.referer})

        # make request from the provided url
        try:
            self._log.debug('Google CSE urllib.request.urlopen("%s")',
                            request.full_url)
            response = self._search_response_json(request, data=None, timeout=5)
        except Exception as err:
            self._log.exception('Error %s returned for url "%s"', str(err), url)
            return False

        # load json response results into python dict
        try:
            resp = response.read()
            resp_json = json.loads(resp)
        except Exception as err:
            self._log.warning('Error during json loading: %s\nfor url "%s"',
                              str(err), url)
            return False

        if not resp_json:
            self._log.debug('response json is empty')
            return False
        if not type(resp_json) is dict:
            self._log.debug('response json is not a dict')
            return False
        if 'items' not in resp_json:
            self._log.debug('response json has no "items" key')
            return False
        if len(resp_json['items']) == 0:
            self._log.debug('response json ["items"] has no entries')
            return False

        # get the original image link and the Google-hosted thumbnail
        img_urls = []
        title = ''
        item0 = resp_json['items'][0]
        if 'link' in item0 and item0['link']:
            img_urls.append(item0['link'])
        if 'image' in item0 and 'thumbnailLink' in item0['image']:
            img_urls.append(item0['image']['thumbnailLink'])
        if 'title' in item0:
            title = item0['title']

        # try to download the original image link, failing that try the
        # Google-hosted thumbnail image
        self._log.debug('downloading image for resource titled "%s"', title)
        for url in img_urls:
            bytes_ = self.download_url(url, self._log)
            if bytes_:
                self._image_bytes = bytes_
                break

        return True if self._image_bytes else False


class ImageSearcher_MusicBrainz(ImageSearcher):
    NAME = __qualname__

    def _search_artists(self, mb, artist: Artist) -> dict:
        """extract this function call to allow for pytest stubbing"""
        self._log.debug('· mb.search_artists(query="%s", limit=1)', artist)
        return mb.search_artists(query=artist, limit=1)

    def _browse_releases(self, mb, artist_id: str) -> dict:
        """extract this function call to allow for pytest stubbing"""
        self._log.debug('· mb.browse_releases(artist="%s", limit=500)',
                        artist_id)
        return mb.browse_releases(artist=artist_id, limit=500)

    @overrides(ImageSearcher)
    def search_album_image(self, artist: Artist, album: Album,
                        _: ImageType) -> bool:
        """There are a number of ways to use the musicbrainz searching and
        browse API functions.
        The particular order of operations here appears
        seemed to be reasonably accurate. First, search on Artist string for an
        Artist ID then search on Album string confined to that Artist ID.
        Trying to search with just one API call using with Album+Artist string
        yielded too many ambiguous results.

        :param artist: Artist name
        :param album: Album name
        :return: image data as bytes
        """
        #self._log.debug('search_album_image("%s", "%s", …)', artist, album)

        if not artist and not album:
            return False

        import musicbrainzngs
        mb = musicbrainzngs  # helper alias
        ua_app = mb.__package__
        ua_ver = mb.musicbrainz._version
        self._log.debug('· mb.set_useragent("%s", %s)', ua_app, ua_ver)
        mb.set_useragent(ua_app, ua_ver)
        self._log.debug('· mb.set_format(fmt="json")')
        # use fmt='xml' because fmt='json' causes this warning:
        #     musicbrainzngs\musicbrainz.py:584: UserWarning: The json format is
        #     non-official and may change at any time
        # as of musicbrainzngs==0.6
        mb.set_format(fmt='xml')
        artist_list = self._search_artists(mb, artist)

        # verify results exist before attempting to use them
        if not artist_list:
            self._log.debug('search_artists("%s") returned nothing', artist)
            return False
        if type(artist_list) is not dict:
            self._log.debug('search_artists("%s") returned unexpected type %s',
                            artist, type(artist_list))
            return False
        if 'artist-list' not in artist_list:
            self._log.debug('search_artists("%s") results do not include an '
                            '"artist-list" entry', artist)
            return False
        if len(artist_list['artist-list']) < 1:
            self._log.debug('search_artists("%s")["artist-list"] is an empty '
                            'list', artist)
            return False
        if 'id' not in artist_list['artist-list'][0]:
            self._log.debug('search_artists("%s")["artist-list"] results do not'
                            ' include an artist "id"', artist)
            return False
        # pick the first artist id from the list, this is most likely the
        # correct matching artist
        artist_id = artist_list['artist-list'][0]['id']

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
            self._log.debug('browse_releases("%s") returned nothing',
                            artist_id)
            return False
        if type(releases) is not dict:
            self._log.debug('browse_releases("%s") returned unexpected type %s',
                            artist_id, type(releases))
            return False
        if 'release-list' not in releases:
            self._log.debug('browse_releases("%s") results do not include a '
                            '"release-list" entry', artist_id)
            return False

        possible = list(
            filter(lambda rle: similar(rle['title'], album) >= 0.4,
                   releases['release-list'])
        )
        self._log.debug('· mb.browse_release_groups(artist="%s", limit=500)',
                        artist_id)
        release_groups = mb.browse_release_groups(artist=artist_id, limit=100)
        possible += list(
            filter(lambda rgle: similar(rgle['title'], album) >= 0.4,
                   release_groups['release-group-list'])
        )

        # store tuple pairs of (`similar` score, release/release_group entry)

        score_album = []
        for p_ in possible:
            # XXX: slightly inefficient because the `similar` function was
            #      called with the same information earlier. good enough.
            score_album.append((similar(p_['title'], album), p_))
        if not score_album:
            return False
        score_album.sort(key=lambda x: x[0], reverse=True)
        # TODO: further refinement would be to disclude entries that explicitly
        #       do not have an associated 'cover-art-archive', e.g.
        #       ['release-list'][x]['cover-art-archive']['artwork'] == 'false'

        # index 0 has most `similar` album by title string
        try:
            album_id = score_album[0][1]['id']
        except IndexError as ie:
            self._log.exception(ie, exc_info=True)
            return False

        # try several sources for the image
        image_list: typing.Dict = dict()
        try:
            self._log.debug('· mb.get_image_list("%s")', album_id)
            image_list = mb.get_image_list(album_id)
        except musicbrainzngs.musicbrainz.ResponseError:
            pass
        try:
            self._log.debug('· mb.get_release_group_image_list("%s")', album_id)
            image_list.update(mb.get_release_group_image_list(album_id))
        except musicbrainzngs.musicbrainz.ResponseError:
            pass

        # do this once
        dmsg = 'for %s MusicBrainz album  ID "%s"' % (str_AA(artist, album),
                                                      album_id)
        # assume the first url available is the best
        if not image_list:
            self._log.debug('unable to find an image URL ' + dmsg)
            return False
        if type(image_list) is not dict:
            self._log.debug('unexected type returned ' + dmsg)
            return False
        if 'images' not in image_list:
            self._log.debug('"images" key not in returned list ' + dmsg)
            return False
        if len(image_list['images']) < 1:
            self._log.debug('list of "images" has no entries ' + dmsg)
            return False
        image0 = image_list['images'][0]
        if 'image' not in image0:
            self._log.debug('images[0] has no "image" entry for %s ' + dmsg)
            return False
        url = image0['image']

        self._image_bytes = self.download_url(url, self._log)

        return True if self._image_bytes else False


def process_dir(dirp: Path, image_path: Path, overwrite: bool,
                result_queue: queue.SimpleQueue, daa_list: DirArtAlb_List)\
        -> DirArtAlb_List:
    """
    Recursively process sub-directories of given directory,
    gathering artist/album info per-directory.

    Call initially with empty daa_list. daa_list will be
    gradually populated by recursive calls. Provide coverFiles
    list to ignore directories where cover files already exist.

    TODO: XXX: this function does too much. work within this function needs to
               be seperated into more discrete tasks starting with:
               def deteremine_Artist_Album(dirp: Path) -> DirArtAlb

    :param dirp: directory path to process
    :param image_path: path to image file (which may or many not exist)
                       the parent dir should be dirp
    :param overwrite: --overwrite
    :param daa_list: accumulated directories for later processing
    :return accumulated directories for later processing
    """
    log.debug('process_dir("%s", "%s", …)', dirp, image_path)

    dirs = []
    files = []

    if not dirp.exists():
        log.error('path does not exist: "%s"', dirp)
        return daa_list
    if not dirp.is_dir():
        log.error('path is not a directory: "%s"', dirp)
        return daa_list

    if not dirp == image_path.parent:
        raise ValueError('Expected directory and image_path to be related'
                         ' "%s" ≠ "%s"' % (dirp, image_path))

    # read dirp directory contents
    try:
        log.debug('%s: reading directory "%s"', func_name(), dirp)
        for fp in dirp.iterdir():  # 'fp' is a file path
            log.debug('%s: processing "%s"', func_name(), fp)
            if fp.is_dir():
                dirs.append(fp)
            elif fp.is_file():
                files.append(fp)
    except OSError as err:
        log.exception(err)
        return daa_list

    #log.debug('%s: found dirs\n%s', func_name(), pformat(dirs))
    #log.debug('%s: found files\n%s', func_name(), pformat(files))

    # recurse into subdirs
    dirs.sort()
    for dir_ in dirs:
        ipath = dir_.joinpath(image_path.name)
        # XXX: should not this append the return of process_dir?
        daa_list = process_dir(dir_, ipath, overwrite, result_queue,
                               daa_list=daa_list)

    # if there are no audio media files in this directory (search by suffix,
    # e.g. '.mp3', '.flac', etc.) then (presume it's not a music album
    # directory) so return
    if not any(suffix in set([f.suffix.lower() for f in files])
               for suffix in AUDIO_TYPES):
        log.debug('no audio media files within directory "%s"', dirp)
        return daa_list

    # if image file path already exists and not overwrite then return
    if image_path.exists():
        if not overwrite:
            log.debug('cover file "%s" exists and no overwrite,'
                      ' skip directory "%s"', image_path.name, dirp)
            result_queue.put('cover file "%s" exists and no overwrite,'
                             ' skip directory "%s"' % (image_path.name, dirp))
            return daa_list
        else:
            log.debug('cover file "%s" exists and passed --overwrite',
                      image_path.name)

    # if `dirp` is already within daa_list then no further processing needed
    if dirp in [d_[0] for d_ in daa_list]:
        log.warning('directory "%s" already in daa_list', dirp)
        return daa_list

    # TODO: it would be good to take the most common strings found for
    #       artist and album among all media files found in the directory. It's
    #       probably common that audio media files vary in their correctness,
    #       e.g. some mp3 files may not have ID3 set, and some mp3 have the
    #       wrong ID3 'album' value.
    # TODO: related to prior, Various Artists albums will have inconsistent
    #       Artist tag but consistent Album tag.

    files.sort()
    for fp in files:  # file path
        ext = fp.suffix.lower()
        if ext not in AUDIO_TYPES:
            continue
        # try to get media tag info from file
        artist = Artist('')
        album = Album('')
        try:
            ar, al = audio_type_get_artist_album[ext](fp)
            # sometimes a long string of spaces is returned
            ar = Artist(ar.strip())
            al = Album(al.strip())
            # Don't overwrite prior good values with new empty values.
            # Also careful of special cases of 'Unknown Artist' (set for tag
            # 'WM/AlbumArtist' in poorly maintained .wma files)
            if not artist and ar and ar != Artist('Unknown Artist'):
                artist = Artist(ar)
            if not album and al and al != Album('Unknown Album'):
                album = Album(al)
        except Exception as err:
            log.exception(err)
            continue
        # if artist and album found, append to daa_list and return
        if artist and album:
            log.info('Album details found: %s within file "%s"',
                     str_AA(artist, album), fp)
            daa = DirArtAlb((dirp, artist, album))

            # XXX: development self-check
            if daa in daa_list:
                log.warning('DAA "%s" already in daa_list1', daa)

            daa_list.append(daa)
            return daa_list

    # no Artist /Album data found within media files, guess the Artist • Album
    # based on directory name. Try several re patterns to match the directory
    # name
    # tuple of (re pattern, artist match group index, album match group index)
    artist = Artist('')
    album = Album('')
    bname = dirp.name
    for patt in [# Artist -- Year -- Album
                 (r'''([\w\W]+)[ ]+\-\-[ ]+([\d]{4})[ ]+\-\-[ ]+([\w\W]+)''',
                  0, 2),
                 # Artist -- Album
                 (r'''([\w\W]+) \-\- ([\w\W]+)''', 0, 1),
                 # Artist - Album
                 (r'''([\w\W]+) \- ([\w\W]+)''', 0, 2),
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
                log.info('Album details found: %s derived from '
                         'directory name "%s"', str_AA(artist, album), bname)
                daa = DirArtAlb((dirp, artist, album))

                # XXX: development self-check
                if daa in daa_list:
                    log.warning('DAA "%s" already in daa_list2', daa)

                daa_list.append(daa)
                return daa_list
        # XXX: this except is too broad
        except:
            pass

    log.debug('no Artist or Album found or no suitable media files within "%s"',
              dirp)

    # XXX: This special case must be handled in implementations of
    #      `search_album_image`. It is used in
    #      `ImageSearcher_LikelyCover.search_album_image`.
    #      Not ideal.
    daa = DirArtAlb((dirp, Artist(''), Album('')))

    # XXX: development self-check
    if daa in daa_list:
        log.warning('DAA "%s" already in daa_list3', daa)

    daa_list.append(daa)
    return daa_list


def process_dirs(dirs: typing.List[Path], image_name: str,
                 image_type: ImageType, overwrite: bool,
                 result_queue: queue.SimpleQueue)\
        -> Path_List:
    """
    Gather list of directories where Album • Artist info can be derived.
    """
    log.debug('')

    daa_list: DirArtAlb_List = []
    for dir_ in dirs:
        d_ = Path(dir_)
        image_path = d_.joinpath(image_name + os.extsep + image_type.value)
        daal = process_dir(d_, image_path, overwrite, result_queue, daa_list=[])
        if daal:
            daa_list += daal
        log.debug('')

    # remove duplicates
    path_list: Path_List = list(set(daa for daa in daa_list))
    log.debug('directories to process:\n%s', pformat(path_list))

    return path_list


def search_create_image(image_path: Path, artist: Artist, album: Album,
                        image_type: ImageType, image_name: str,
                        searches,
                        googlecse_opts: GoogleCSE_Opts,
                        referer: str, overwrite: bool, debug: bool, test: bool)\
        -> typing.Tuple[bool, str]:
    """
    Do the download using ImageSearchers given the needed data. Write image
    file data to `image_path`.
    Return count of bytes of image data written to file.
    """
    log.debug('  search_create_image("%s", "%s", …)', artist, album)

    # TODO: Have order of requested searchers matter. Search in order of passed
    #       script options.
    search_likely, search_embedded, search_musicbrainz, search_googlecse \
        = searches
    searchers = (
        ImageSearcher_LikelyCover(image_path, referer, debug)
            if search_likely else None,
        ImageSearcher_EmbeddedMedia(image_path, referer, debug)
        if search_embedded else None,
        ImageSearcher_MusicBrainz(referer, debug)
            if search_musicbrainz else None,
        ImageSearcher_GoogleCSE(googlecse_opts, referer, debug)
            if search_googlecse else None,
    )
    result = False
    result_message = 'No suitable image found for %s that could be written to' \
                     ' "%s"' \
                     % (str_AA(artist, album), image_path)

    for is_ in searchers:
        try:
            if not is_:
                continue
            if not is_.search_album_image(artist, album, image_type):
                log.debug('  no album image found from image searcher %s for'
                          ' %s', is_.NAME, str_AA(artist, album))
                continue
            if not is_.write_album_image(image_path, overwrite, test):
                log.debug('  write_album_image failed for image searcher %s for'
                          ' %s', is_.NAME, str_AA(artist, album))
                continue
            result = True
            result_message = is_.result_message
            break
        except Exception as ex:
            log.exception(ex)

    return result, result_message


def process_tasks(task_queue: queue.Queue, result_queue: queue.SimpleQueue)\
        -> None:
    """
    Thread entry point.
    While things to process in task_queue then do so. This function will
    exit when task_queue.get raises Empty.

    :param task_queue: queue of tasks (images to search for)
    :param result_queue: queue of attempts at downloads/copies, used for later
                        printing of program results
    :return: None
    """
    log.debug('→')

    while True:
        try:
            # don't block (use `get_nowait`) because the task_queue
            # is assumed to have been filled with tasks by now. It's only being
            # consumed at this point in the program.
            (
                daa,
                image_path,
                image_type,
                image_name,
                (search_likely, search_embedded, search_musicbrainz,
                 search_googlecse),
                googlecse_opts,
                referer,
                overwrite,
                debug,
                test
            ) = task_queue.get_nowait()
        except queue.Empty:  # catch Empty and return gracefully
            log.debug('←')
            return
        _, artist, album = daa
        log.debug('☐ task: %s', str_AA(artist, album))
        try:
            result, result_mesg = search_create_image(
                image_path,
                artist,
                album,
                image_type,
                image_name,
                (search_likely, search_embedded, search_musicbrainz,
                 search_googlecse),
                googlecse_opts,
                referer,
                overwrite,
                debug,
                test
            )
            result_queue.put(result_mesg)
        except Exception as ex:
            log.exception(ex)

        log.debug('☑ task_done %s', str_AA(artist, album))
        task_queue.task_done()


def parse_args_opts():
    """parse command line arguments and options"""

    parser = argparse.ArgumentParser(formatter_class=
                                     argparse.RawDescriptionHelpFormatter)
    parser.description = '''\
This Python-based program is for automating downloading album cover art images.
A common use-case is creating a "folder.jpg" file for a collection of ripped
Compact Disc albums.

Given a list of directories, DIRS, recursively identify "album" directories.
"Album" directories have audio files, e.g. files with extensions like .mp3 or
.flac.  For each "album" directory, attempt to determine the Artist and Album.
Then find an album cover image file using the requested --search providers.  If
an album cover image file is found then write it to IMAGE_NAME.IMAGE_TYPE within
each "album" directory.

Audio files supported are %s.''' % ', '.join(AUDIO_TYPES)

    # TODO: Have order of requested searchers matter. Search in order of passed
    #       script options.

    argg = parser.add_argument_group('Required Arguments')
    argg.add_argument(dest='dirs', metavar='DIRS', action='append', type=str,
                      nargs='+',
                      help='directories to scan for audio files (Required)')

    argg = parser.add_argument_group('Recommended')
    argg.add_argument('-n', '--image-name', dest='image_name', action='store',
                      default='cover',
                      help='cover image file name IMAGE_NAME. This is the file'
                           ' name that will be created within passed DIRS. '
                           ' This will be appended with the preferred image'
                           ' TYPE, e.g. "jpg", "png", etc.'
                           ' (default: "%(default)s")')
    argg.add_argument('-i', '--image-type', dest='image_type', action='store',
                      default=ImageType.list()[0], choices=ImageType.list(),
                      help='image format IMAGE_TYPE (default: "%(default)s")')
    argg.add_argument('-o', '--overwrite', dest='overwrite',
                      action='store_true', default=False,
                      help='overwrite any previous file of the same file'
                           ' IMAGE_NAME and IMAGE_TYPE (default: %(default)s)')

    argg = parser.add_argument_group('Search all')
    argg.add_argument('-s*', '--search-all', dest='search_all',
                      action='store_true', default=False,
                      help='Search for album cover images using all methods and'
                           ' services'
                      )

    argg = parser.add_argument_group('Search the local directory for likely'
                                     ' album cover images')
    argg.add_argument('-sl', '--search-likely-cover', dest='search_likely',
                      action='store_true', default=False,
                      help='For any directory with audio media files but no'
                           ' file "IMAGE_NAME.IMAGE_TYPE", search the directory'
                           ' for files that are likely album cover images. For'
                           ' example, given options: --name "cover" --type'
                           ' "jpg", and a directory of .mp3 files with a file'
                           ' "album.jpg", it is reasonable to guess'
                           ' "album.jpg" is a an album cover image file. So'
                           ' copy file "album.jpg" to "cover.jpg" . This will'
                           ' skip an internet image lookup and download and'
                           ' could be a more reliable way to retrieve the'
                           ' correct album cover image.')

    argg = parser.add_argument_group('Search the local directory for an'
                                     ' embedded album cover image')
    argg.add_argument('-se', '--search-embedded', dest='search_embedded',
                      action='store_true', default=False,
                      help='Search audio media files for embedded images. If'
                           ' found, attempt to extract the embedded image.'
                     )

    argg = parser.add_argument_group('Search Musicbrainz NGS webservice')
    argg.add_argument('-sm', '--search-musicbrainz', dest='search_musicbrainz',
                      action='store_true', default=False,
                      help='Search for album cover images using musicbrainz NGS'
                           ' webservice.'
                           ' MusicBrainz lookup is the most reliable search'
                           ' method.'
                      )

    argg = parser.add_argument_group('Search Google Custom Search Engine (CSE)')
    gio = ImageSize.list()
    argg.add_argument('-sg', '--search-googlecse', dest='search_googlecse',
                      action='store_true', default=False,
                      help='Search for album cover images using Google CSE.'
                           ' Using the Google CSE requires an Engine ID and API'
                           ' Key. Google CSE reliability entirely depends upon'
                           ' the added "Sites to search".'
                           ' The end of this help message has more advice'
                           ' around using Google CSE.'
                      )
    argg.add_argument('-s', '--gsize', dest='gsize', action='store',
                      default=gio[len(gio)-1], choices=gio,
                      help='Google CSE optional image file size '
                      '(default: "%(default)s")')
    argg.add_argument('--gid', dest='gid', action='store',
                      help='Google CSE ID (URL parameter "cx")'
                      ' typically looks like'
                      ' "009494817879853929660:efj39xwwkng".  REQUIRED to use'
                      ' Google CSE.')
    argg.add_argument('--gkey', dest='gkey', action='store',
                      help='Google CSE API Key (URL parameter "key") typically'
                      ' looks like'
                      ' "KVEIA49cnkwoaaKZKGX_OSIxhatybxc9kd59Dst". REQUIRED to'
                      ' use Google CSE.')
    #argg.add_argument('-c', '--count', dest='count', action='store',
    #                  default='8', type=int,
    #                  help='image lookup count (default: %(default)s)')

    argg = parser.add_argument_group('Debugging and Miscellanea')
    argg.add_argument('-v', '--version', action='version', version=__version__)
    argg.add_argument('-r', '--referer', dest='referer', action='store',
                      default=REFERER_DEFAULT,
                      help='Referer url used in HTTP GET requests'
                           ' (default: "%(default)s")')
    argg.add_argument('-d', '--debug', dest='debug', action='store_true',
                      default=False,
                      help='Print debugging messages (default: %(default)s)')
    argg.add_argument('--test-only', dest='test', action='store_true',
                      default=False,
                      help='Only test, do not write any files'
                           ' (default: %(default)s)')

    parser.epilog = '''\
This program attempts to create album cover image files for the passed DIRS.  It
does this several ways, searching for album cover image files already present in
the directory (-sl).  If not found, it attempts to figure out the Artist and
Album for that directory then searches online services for an album cover image
(-sm or -sg).

Directories are searched recursively.  Any directory that contains one or more
with file name extension %s''' % ' or '.join(AUDIO_TYPES) + '''
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
takes about 5 minutes.  This is where your own values for --gid and --gkey can
be created. --gid is "Search engine ID" (URI parameter "cx") and --gkey is
under the "Custom Search JSON API" from which you can generate an API Key (URI
parameter "key"). A key can be generated at
https://console.developers.google.com/apis/credentials.
Google CSE settings must have "Image search" as "ON"  and "Search the entire
web" as "OFF".

PyPi project: %s
Source code: %s

Inspired by the program coverlovin.''' % (__url_project__, __url_source__)

    args = parser.parse_args()

    if args.search_all:
        args.search_likely = True
        args.search_embedded = True
        args.search_musicbrainz = True
        args.search_googlecse = True

    if not (args.search_likely or args.search_musicbrainz
            or args.search_googlecse or args.search_embedded):
        parser.error('no selected search method. Select a search, e.g. -sl or '
                     '--search-musicbrainz or -s*')

    if args.search_googlecse:
        if not args.gkey:
            parser.error('passed --search-googlecse (-sg or -s*) so --gid is'
                         ' also required')
        if not args.gkey:
            parser.error('passed --search-googlecse (-sg or -s*) so --gkey is'
                         ' also required')
    elif args.gkey or args.gkey:
        log.warning('not passed --search-googlecse (-sg) so --gkey and --gid'
                    ' are not necessary')

    if args.search_musicbrainz:
        try:
            import musicbrainzngs
        except ModuleNotFoundError as err:
            log.error('MusicBrainz library must be installed\n'
                      '   pip install musicbrainzngs')
            raise err

    return args.dirs[0], ImageType(args.image_type), args.image_name, \
           args.search_likely, \
           args.search_embedded, \
           args.search_musicbrainz, \
           args.search_googlecse, \
           GoogleCSE_Opts(args.gkey, args.gid, ImageSize(args.gsize)), \
           args.overwrite, args.referer, args.debug, args.test


def main():
    """
    Recursively download cover images for music files in a
    given directory and its sub-directories
    """
    dirs, image_type, image_name, \
    search_likely, \
    search_embedded, \
    search_musicbrainz, \
    search_googlecse, googlecse_opts, \
    overwrite, referer, debug, test \
        = parse_args_opts()

    if debug:
        log.setLevel(logging.DEBUG)

    # results of attempting to update directories
    result_queue = queue.SimpleQueue()

    # gather list of directories where Album • Artist info can be derived.
    # 'daa' is a DirArtAlb tuple
    daa_list = process_dirs(dirs, image_name, image_type, overwrite,
                            result_queue)

    #
    # do the remaining tasks in separate threads relying on a Queue
    # to multiplex those tasks
    #

    task_queue = queue.Queue()

    image_nt = image_name + image_type.suffix
    for daa in daa_list:
        image_path = Path(daa[0], image_nt)
        task_queue.put(
            (
                daa,
                image_path,
                image_type,
                image_name,
                (search_likely, search_embedded, search_musicbrainz,
                 search_googlecse),
                googlecse_opts,
                referer,
                overwrite,
                debug,
                test,
            )
        )

    for _ in range(TASK_THREAD_COUNT):
        th = threading.Thread(target=process_tasks,
                              args=(task_queue, result_queue))
        # daemon: don't wait on threads, task_queue signals when complete
        th.daemon = True
        th.start()

    # `.join` returns when task_queue is empty of tasks (task_done)
    task_queue.join()

    # print results and exit gracefully
    try:
        while True:
            msg = result_queue.get_nowait()
            print(msg)
    except queue.Empty:
        pass

    return 0


if __name__ == '__main__':
    sys.exit(main())
