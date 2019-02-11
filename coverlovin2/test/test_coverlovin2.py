#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-

"""
Test the coverlovin2 project using pytest.

Technique and recommendations taken from https://docs.pytest.org/en/latest/

"""

__author__ = 'James Thomas Moon'
__url__ = 'https://github.com/jtmoon79/coverlovin2/test'


# standard library imports
import os
import logging
from pathlib import Path
import pytest
import tempfile
import typing

# non-standard library imports
from mutagen.id3 import ID3NoHeaderError
from mutagen.asf import ASFHeaderError
from mutagen.flac import FLACNoHeaderError

# custom imports
from ..coverlovin2 import Artist
from ..coverlovin2 import Album
from ..coverlovin2 import GoogleCSE_Opts
from ..coverlovin2 import ImageSize
from ..coverlovin2 import ImageType
from ..coverlovin2 import URL
from ..coverlovin2 import str_AA
from ..coverlovin2 import func_name
from ..coverlovin2 import similar
from ..coverlovin2 import log_new
from ..coverlovin2 import LOGFORMAT
from ..coverlovin2 import get_artist_album_mp3
from ..coverlovin2 import get_artist_album_mp4
from ..coverlovin2 import get_artist_album_flac
from ..coverlovin2 import get_artist_album_ogg
from ..coverlovin2 import get_artist_album_asf
from ..coverlovin2 import audio_type_get_artist_album
from ..coverlovin2 import ImageSearcher
from ..coverlovin2 import ImageSearcher_LikelyCover
from ..coverlovin2 import ImageSearcher_GoogleCSE


# all committed test resources should be under this directory
test_resource_path = Path.joinpath(Path(__file__).parent, 'test_resources')


def join_test_rp(*args) -> Path:
    """join test_resource_path to any number of path additions"""
    return Path.joinpath(test_resource_path, *args)


def exists_or_skip(*args) -> typing.Tuple[Path, None]:
    """helper for easily skipping a test if path is not available"""
    fp = join_test_rp(*args)
    if not fp.exists():
        pytest.skip('test resource not available "%s"' % fp)
        return None
    return fp


class Test_GoogleCSE_Opts(object):

    @pytest.mark.parametrize('ti',
        (
            pytest.param(('', '', '',), id='empty param 1 2 3'),
            pytest.param(('foo', '', '',), id='empty param 2 3'),
            pytest.param(('foo', 'bar', '',), id='empty param 3'),
            pytest.param(('foo', 'bar', None,), id='None param 3'),
            pytest.param((None, 'bar', None,), id='None param 1 3'),
            pytest.param((None, None, None,), id='None param 1 2 3'),
        )
    )
    def test_init_False(self, ti):
        gc = GoogleCSE_Opts(*ti)
        assert not gc

    @pytest.mark.parametrize('ti',
        (
            pytest.param(('foo', 'bar', 'baz',), id='basic case #1'),
            pytest.param(('foo', r'as jo2u3 lj;las;  :L@)(* ;23', 'baz',), id='basic case #2'),
        )
    )
    def test_init_True(self, ti):
        gc = GoogleCSE_Opts(*ti)
        assert gc

    @pytest.mark.parametrize('ti',
        (
            pytest.param((), id='()'),
            pytest.param(('',), id='("")'),
            pytest.param(('', ''), id='("","")'),
            pytest.param(('', '', '', '',), id='("","","","")'),
        )
    )
    def test_init_TypeError(self, ti):
        with pytest.raises(TypeError):
            GoogleCSE_Opts(*ti)


class Test_helpers(object):

    @pytest.mark.parametrize('tiAr, tiAl, ti_exp',
        (
            pytest.param('', '', '''｛ "" • "" ｝''', id='empty'),
            pytest.param('Foo', 'Bar', '''｛ "Foo" • "Bar" ｝''', id='Foo Bar'),
        )
    )
    def test_str_AA(self, tiAr, tiAl, ti_exp):
        saa1 = str_AA(Artist(tiAr), Album(tiAl))
        assert saa1 == ti_exp

    @pytest.mark.parametrize('ti',
        (
            pytest.param('http://', id='http'),
            pytest.param('https://', id='https'),
            pytest.param('https://foo', id='https://foo'),
        )
    )
    def test_URL_init(self, ti):
        URL(ti)

    @pytest.mark.parametrize('ti',
        (
            pytest.param('foo', id='foo'),
            pytest.param('', id='""'),
            #pytest.param(bytes('https://', encoding='utf8'), id='type<bytes>'),
        )
    )
    def test_URL_ValueError(self, ti):
        with pytest.raises(ValueError):
            URL(ti)

    def test_URL_TypeErrpr(self):
        with pytest.raises(TypeError):
            URL(bytes('https://', encoding='utf8'))

    def test_URL_False(self):
        assert not URL()

    def test_URL_True(self):
        assert URL('https://foo.com')

    def test_log_new_1(self):
        log1 = log_new('log1', logging.DEBUG)
        assert log1.hasHandlers()

    def test_log_new_2(self):
        log2a = log_new('log2a', logging.DEBUG)
        log2b = log_new('log2b', logging.DEBUG)
        assert log2a is log2b

    def test_log_new_same_id(self):
        log3a = log_new('log3', logging.DEBUG)
        log3b = log_new('log3', logging.DEBUG)
        assert log3a is log3b
        assert id(log3a) == id(log3b)

    def test_func_name_1(self):
        assert func_name() == 'test_func_name_1'

    def test_similar_type(self):
        assert type(similar('', '')) is float

    _str_odd1 = \
        r'an874987()#&_@( 87398skjEQhe]w?a]fuheusn-09- klnknd\#(!  njbBIOE'
    _str_un2 = r'''¶棲摓Ⲫ⸙Ａ'''
    _str_long3 = 'abkjadliuewoijkblhlkjaoiquweaghbkjhkljhldkjhaldkh'

    @pytest.mark.parametrize('ti_a, ti_b, ti_exp',
        (
            pytest.param('', '', 1.0, id='""≟"" == 1.0'),
            pytest.param('a', 'a', 1.0, id='"a"≟"a" == 1.0'),
            pytest.param(_str_odd1, _str_odd1, 1.0, id='_str_odd1 ≟ _str_odd1 == 1.0'),
            pytest.param(_str_un2, _str_un2, 1.0, id='_str_un2 ≟ _str_un2 == 1.0'),
            pytest.param('abcdefg', 'defghijk', (0.5333, 0.534), id='0.533 ≤ overlap ≤ 0.534'),
            pytest.param('', _str_long3, (0, 0.001), id='""≟"jslkjsdlkjf…"'),
            pytest.param(_str_long3, '', (0, 0.001), id='"jslkjsdlkjf…"≟""'),
        )
    )
    def test_similar(self, ti_a, ti_b, ti_exp):
        score = similar(ti_a, ti_b)
        if type(ti_exp) is int or type(ti_exp) is float:
            assert score == ti_exp
        elif type(ti_exp) is tuple and len(ti_exp) == 2:
            assert ti_exp[0] <= score <= ti_exp[1]
        else:
            raise TypeError('bad test case input type %s' % type(ti_exp))


class Test_ImageType(object):

    @pytest.mark.parametrize('ti',
        (
            'unknown type',
            '',
            5,
            {},
            '.gif'
        )
    )
    def test_init_ValueError(self, ti):
        with pytest.raises(ValueError):
            ImageType('unknown type')

    @pytest.mark.parametrize('ti',
        (
            'jpg',
            ImageType.PNG,
            ImageType.GIF,
            ImageType.JPG
        )
    )
    def test_init(self, ti):
        ImageType(ti)

    def test_check_len_types(self):
        """ensure previous tests cover all possible cases. If not then new test
        cases will need to be added.
        """
        assert len(ImageType.list()) == 3


jpg = ImageType.JPG
gif = ImageType.GIF
png = ImageType.PNG


class Test_overrides(object):
    """
    Cannot test @overrides because @overrides check runs at some point prior to
    run-time, during some sort of Python pre-run phase. Prior to pytest being
    ready.
    """


# placeholder image url for testing downloading
image_url = 'http://via.placeholder.com/2'


class Test_ImageSearcher(object):

    # make `log` class-wide (can not implement `__init__` for pytest processed
    # class)
    log = log_new(LOGFORMAT, logging.DEBUG, __qualname__)

    @pytest.mark.dependency(name='net_access_ping')
    def test_net_access_ping(self):
        """check Internet access. ping of known stable IP."""
        # TODO: complete this!
        pass

    @pytest.mark.dependency(name='net_access_dns',
                            depends=['net_access_ping'])
    def test_net_access_dns(self):
        """check Internet access. attempt DNS lookup."""
        # TODO: complete this!
        pass

    @pytest.mark.dependency(name='net_access', depends=['net_access_ping',
                                                        'net_access_dns'])
    def test_net_access(self):
        """Wrapper of two net access dependency for simpler `depends` params"""
        pass

    @pytest.mark.dependency(name='init_is')
    def test_init(self):
        with pytest.raises(TypeError):
            ImageSearcher('', False)

    def test_download_url_ValueError(self):
        with pytest.raises(ValueError):
            """bad url should raise"""
            ImageSearcher.download_url('', self.log)

    def test_download_url_return_None(self):
        """non-exists download URL should return None"""
        assert not ImageSearcher.download_url('http://NOTEXISTURL.TESTFOO',
                                              self.log)

    def test_download_url__1(self):
        assert ImageSearcher.download_url(image_url, self.log)

    def test_download_url__2(self):
        data = ImageSearcher.download_url(image_url, self.log)
        assert type(data) is bytes

class Test_ImageSearcher_LikelyCover(object):

    @pytest.mark.dependency(name='init_likelyc')
    def test_init(self):
        ImageSearcher_LikelyCover(Path(''), '', False)

    @pytest.mark.dependency(depends=['init_likelyc'])
    def test_LikelyCover_WrongUseError(self):
        is_ = ImageSearcher_LikelyCover(Path(''), '', False)
        with pytest.raises(ImageSearcher_LikelyCover.WrongUseError):
            is_.write_album_image(Path(''), True, True)

    A_Dir = 'test_ImageSearcher_LikelyCover1'  # actual sub-directory
    A_Mp3 = 'ID3v1 [Bob Dylan] [Highway 61 Revisited].mp3'  # actual test file

    @pytest.mark.dependency(depends=['init_likelyc'])
    def test_empty_ArtAlb(self):
        """There should be no image files in the directory."""
        fp = exists_or_skip(self.A_Dir, self.A_Mp3)
        is_ = ImageSearcher_LikelyCover(fp, 'my referred', False)
        for it in ImageType.list():
            assert not is_.search_album_image(Artist(''), Album(''),
                                              ImageType(it))

    @pytest.mark.dependency(depends=['init_likelyc'])
    def test_match_likely_name__TypeError(self):
        is_ = ImageSearcher_LikelyCover(Path(), '', False)
        with pytest.raises(TypeError):
            _ = is_._match_likely_name(jpg, None)

    @pytest.mark.dependency(depends=['init_likelyc'])
    def test_match_likely_name__AttributeError(self):
        is_ = ImageSearcher_LikelyCover(Path(), '', False)
        with pytest.raises(AttributeError):
            _ = is_._match_likely_name(None, None)

    @pytest.mark.dependency(depends=['init_likelyc'])
    def test_match_likely_name_empty__file_list(self):
        fp = exists_or_skip(self.A_Dir, self.A_Mp3)
        is_ = ImageSearcher_LikelyCover(fp, '', False)
        assert not is_._match_likely_name(jpg, [])

    @pytest.fixture(params=[it for it in ImageType], ids=ImageType.list())

    @pytest.mark.dependency(depends=['init_likelyc'])
    @pytest.mark.parametrize('ti',
        (pytest.param(it, ids=it.value) for it in ImageType)
    )
    def test_match_likely_name__no_match(self, ti):
        fp = exists_or_skip(self.A_Dir, self.A_Mp3)
        is_ = ImageSearcher_LikelyCover(fp, '', False)
        files = (Path.joinpath(test_resource_path, 'foo' + ti.suffix),
                 Path.joinpath(test_resource_path, 'bar' + ti.suffix),
                 )
        assert not is_._match_likely_name(ti, files)

    # Each following `pytest.fixture` entry within `_LikelyCover_4_entries` is:
    # (
    #   ImageType,
    #   (
    #       Path_to_match1,
    #       Path_to_match2,
    #       ...
    #   ),
    #   Path_expected_to_match
    # ),
    # where `Path_expected_to_match` is a Path to be compared against return
    # value of `_match_likely_name([Path_to_match1, Path_to_match2, ...])`.
    _LikelyCover_4_fixture_entries = (
        (
            jpg,
            (
                Path('nope' + jpg.suffix),
                Path('nope' + png.suffix)
            ),
            None
        ),
        (
            jpg,
            (
                Path('AlbumArt_Small' + jpg.suffix),
                Path('AlbumArt_Large' + jpg.suffix)
            ),
            Path('AlbumArt_Large' + jpg.suffix)
        ),
        (
            jpg,
            (
                Path('front-here' + jpg.suffix),
                Path('here-front' + jpg.suffix)
            ),
            Path('front-here' + jpg.suffix)
        ),
        (
            png,
            (
                Path('fronthere' + png.suffix),
                Path('here-front' + png.suffix)
            ),
            Path('here-front' + png.suffix)
        ),
        (
            jpg,
            (
                Path('foo (front)' + jpg.suffix),
                Path('folder' + jpg.suffix)
            ),
            Path('foo (front)' + jpg.suffix)
         ),
        (
            jpg,
            (
                Path('AlbumArt01' + jpg.suffix),
                Path('foo (front)' + jpg.suffix)
            ),
            Path('AlbumArt01' + jpg.suffix)
        ),
        (
            jpg,
            (
                Path('foo (front)' + jpg.suffix),
                Path('AlbumArt01' + jpg.suffix)
            ),
            Path('AlbumArt01' + jpg.suffix)
        ),
        (
            jpg,
            (
                Path('R-3512668-1489953889-2577 cover.jpeg' + jpg.suffix),
                Path('nomatch' + jpg.suffix)
            ),
            Path('R-3512668-1489953889-2577 cover.jpeg' + jpg.suffix)
        ),
        (
            jpg,
            (
                Path('album_cover.jpeg' + jpg.suffix),
                Path('nomatch' + jpg.suffix)
            ),
            Path('album_cover.jpeg' + jpg.suffix)
        ),
        (
            jpg,
            (
                Path('nomatch' + jpg.suffix),
                Path('Something (front) blarg' + jpg.suffix)
            ),
            Path('Something (front) blarg' + jpg.suffix)
        ),
        (
            jpg,
            (
                Path('Something-front-blarg' + jpg.suffix),
                Path('Something (front) blarg' + jpg.suffix)
            ),
            Path('Something (front) blarg' + jpg.suffix)
        ),
        (
            png,
            (
                Path('Something-front-blarg' + png.suffix),
                Path('Something (front) blarg' + png.suffix)
            ),
            Path('Something (front) blarg' + png.suffix)
        ),
        (
            gif,
            (
                Path('Something-front-blarg' + gif.suffix),
                Path('Something (front) blarg' + gif.suffix)
            ),
            Path('Something (front) blarg' + gif.suffix)
        ),
        (
            jpg,
            (
                Path('Something-front-blarg' + jpg.suffix),
                Path('Something' + png.suffix),
                Path('Something' + jpg.suffix),
                Path('Something' + gif.suffix)
            ),
            Path('Something-front-blarg' + jpg.suffix)
        ),
        (
            jpg,
            (
                Path('folder' + png.suffix),
                Path('folder' + jpg.suffix),
                Path('folder' + gif.suffix)
            ),
            Path('folder' + jpg.suffix)
        ),
        (
            png,
            (
                Path('folder' + png.suffix),
                Path('folder' + jpg.suffix),
                Path('folder' + gif.suffix)
            ),
            Path('folder' + png.suffix)
        ),
        (
            jpg,
            (
                Path('Something-front-blarg' + png.suffix),
                Path('Something-front-blarg' + jpg.suffix),
                Path('Something-front-blarg' + gif.suffix),
                Path('Something (front) blarg' + png.suffix),
                Path('Something (front) blarg' + jpg.suffix),
                Path('Something (front) blarg' + gif.suffix),
            ),
            Path('Something (front) blarg' + jpg.suffix)
        ),
        (
            jpg,
            (
                Path('Something-front-blarg' + jpg.suffix),
                Path('Something (front) blarg' + '.jpeg'),
            ),
            Path('Something (front) blarg' + '.jpeg')
        ),
    )

    @pytest.fixture(params=_LikelyCover_4_fixture_entries)
    def _fixture_4(self, request):
        return request.param

    @pytest.mark.dependency(depends=['init_likelyc'])
    def test_ImageSearcher_LikelyCover_4_match__(self, _fixture_4):
        image_type = _fixture_4[0]
        files = _fixture_4[1]
        is_ = ImageSearcher_LikelyCover(Path(), '', False)
        m = is_._match_likely_name(image_type, files)

        assert m == _fixture_4[2]

    B_Dir = 'test_ImageSearcher_LikelyCover2'  # actual sub-directory
    B_Img = 'album.jpg'  # actual test file in that sub-directory
    B_fp = join_test_rp(B_Dir, B_Img)  # file path test resource .../album.jpg

    @pytest.mark.dependency(name='test_res_B')
    def test_B_resources(self):
        assert self.B_fp.exists()

    @pytest.mark.dependency(depends=['init_likelyc', 'test_res_B'])
    def test_ImageSearcher_LikelyCover_5_nomatch_same_file_exist(self):
        """Do not match actual file to itself."""
        files = (self.B_fp,)
        is_ = ImageSearcher_LikelyCover(self.B_fp, '', False)
        m = is_._match_likely_name(jpg, files)

        assert not m

    @pytest.mark.dependency(depends=['init_likelyc'])
    def test_ImageSearcher_LikelyCover_5_match_same_file_notexist(self):
        """Do match non-existent same file."""
        fp = Path(r'C:/THIS FILE DOES NOT EXIST 298389325 (album_cover)' +
                  jpg.suffix)
        files = (fp,)
        is_ = ImageSearcher_LikelyCover(fp, '', False)
        m = is_._match_likely_name(jpg, files)

        assert m
        assert m.name == fp.name

    @pytest.mark.dependency(depends=['init_likelyc'])
    def test_ImageSearcher_LikelyCover_6_match_similar1(self):
        """Do match similar file name to similar parent directory name."""
        fp = Path(r'C:/ACDC TNT/ACDC TNT' + png.value)
        files = (fp,)
        is_ = ImageSearcher_LikelyCover(fp, '', False)
        m = is_._match_likely_name(png, files)

        assert m.name == fp.name

    @pytest.mark.dependency(depends=['init_likelyc'])
    def test_ImageSearcher_LikelyCover_6_match_similar2(self):
        """Do match similar file name to similar parent directory name."""
        fp = Path(r'C:/Kraftwerk - Minimum Maximum/Minimum Maximum' +
                  gif.suffix)
        files = (fp,)
        is_ = ImageSearcher_LikelyCover(fp, '', False)
        m = is_._match_likely_name(gif, files)

        assert m.name == fp.name

    def test_ImageSearcher_LikelyCover_6_match_similar3(self):
        """Do match similar file name to similar parent directory name."""
        fp = Path(r'C:/Kraftwerk - Minimum Maximum/Kraftwerk' + png.suffix)
        files = (fp,)
        is_ = ImageSearcher_LikelyCover(fp, '', False)
        m = is_._match_likely_name(png, files)

        assert m.name == fp.name


C_Artist = Artist('Bob Dylan')
C_Album = Album('Biograph (Disc 1)')


class Test_ImageSearcher_GoogleCSE(object):
    """
    Google CSE is tedious to test live so just use dummy data. Requires
    secret values for Key and Search ID. Which then requires adding secret
    data to this project.
    """

    C_Dir = 'test_ImageSearcher_GoogleCSE1'  # actual sub-directory
    C_Img = 'album.jpg'  # actual test file in that sub-directory
    C_fp = join_test_rp(C_Dir, C_Img)
    # create these once with short names
    C_sz = ImageSize.SML
    C_testinput = test_resource_path.joinpath('googlecse-response1.json')
    C_Artist = Artist('Bob Dylan')
    C_Album = Album('Biograph (Disc 1)')

    @pytest.mark.dependency(name='test_res_C')
    def test_resources_exist(self):
        assert self.C_fp.exists()
        assert self.C_testinput.exists()

    def test_init(self):
        gco = GoogleCSE_Opts('fake+key', 'fake+ID', self.C_sz)
        ImageSearcher_GoogleCSE(gco, 'referrer!', False)

    def test_False(self):
        gco = GoogleCSE_Opts('', '', self.C_sz)
        assert not ImageSearcher_GoogleCSE(gco, 'referrer!', False)

    def _stub_response1(*args, **kwargs):
        """To replace `ImageSearcher_GoogleCSE._search_response_json`"""
        return open(str(Test_ImageSearcher_GoogleCSE.C_testinput))

    def _stub_download_url(*args, **kwargs):
        """To replace `ImageSearcher_GoogleCSE.download_url`"""
        return bytes('this is fake image date', encoding='utf8')

    # create ImageSearcher_GoogleCSE with stubbed methods
    C_gopt = GoogleCSE_Opts('fake+key', 'fake+ID', ImageSize.SML)
    C_isg = ImageSearcher_GoogleCSE(C_gopt, 'referrer!', False)
    C_isg._search_response_json = _stub_response1
    C_isg.download_url = _stub_download_url

    @pytest.mark.parametrize('ti_Ar, ti_Al, ti_it, ti_ex',
        (
            pytest.param(C_Artist, C_Album, jpg, True, id=str_AA(C_Artist, C_Album)),
            pytest.param(Artist('A'), Album('B'), jpg, True, id=str_AA(Artist('A'), Album('B'))),
            pytest.param(Artist('A'), Album(''), jpg, True, id=str_AA(Artist('A'), Album(''))),
            pytest.param(Artist(''), Album('B'), jpg, True, id=str_AA(Artist(''), Album('B'))),
            pytest.param(Artist(''), Album(''), jpg, False, id=str_AA(Artist(''), Album(''))),
        )
    )
    def test_search_album_image(self, ti_Ar, ti_Al, ti_it, ti_ex):
        assert self.C_isg.search_album_image(ti_Ar, ti_Al, ti_it) == ti_ex

    def _stub_response2(*args, **kwargs):
        testinput2 = test_resource_path.joinpath(
            'googlecse-response3-onlygooglecacheimage.json')
        return open(str(testinput2))

    # XXX: presuming only one instance of this test runs at a time
    _6_testfile = Path(tempfile.gettempdir(), tempfile.gettempprefix() +
                       __qualname__)

    def _6_rm_testfile(self):
        try:
            os.remove(self._6_testfile)
        except OSError:
            pass

    @pytest.fixture()
    def _6_fixture(self, request):
        request.addfinalizer(self._6_rm_testfile)

    @pytest.mark.dependency(depends=['net_access'])
    @pytest.mark.usefixtures("_6_fixture")
    def test_search_album_image__use_altgooglecache(self, _6_fixture):
        """test download from alternate google image cache location"""

        is_ = ImageSearcher_GoogleCSE(self.C_gopt, 'referrer!', False)
        is_._search_response_json = self._stub_response2
        # XXX: hopefully the image URL within the test file remains valid!
        assert is_.search_album_image(Artist('my artist'),
                                      Album('my album'),
                                      ImageType.JPG)
        assert is_.write_album_image(self._6_testfile, False, False)
        # XXX: hopefully the image never changes! (not ideal)
        assert 2000 < os.path.getsize(self._6_testfile) < 2500

    # TODO: XXX: need tests for other ImageSearcher_likely functions:
    #            write_album_image
    # TODO: XXX: need tests for other ImageSearcher classes


class Test_media(object):

    @pytest.mark.parametrize('ti_fname, ti_ar, ti_al',
        (
            # mp3
            pytest.param('ID3v1 _.mp3', '', '', id='mp3 ID3v1 "" ""'),
            pytest.param('ID3v1 artist album.mp3', 'my artist', 'my album', id='mp3 ID3v1 "my artist" "my album"'),
            pytest.param('ID3v1 artist.mp3', 'my artist', '', id='mp3 ID3v1 "my artist" ""'),
            pytest.param('ID3v1 ID3v2 artist album.mp3', 'my artist', 'my album', id='mp3 ID3v1 ID3v2 "my artist" "my album"'),
            pytest.param('ID3v2 artist album.mp3', 'my artist', 'my album', id='mp3 ID3v2 "my artist" "my album"'),
            pytest.param('ID3v1 albumartist album.mp3', 'my albumartist', 'my album', id='mp3 ID3v1 "my artist" "my album"'),
            pytest.param('_.mp3', '', '', id='mp3 no ID'),
            # ogg
            pytest.param('_.ogg', '', '', id='ogg "" ""'),
            pytest.param('artist.ogg', 'my artist', '', id='ogg "my artist" ""'),
            pytest.param('album.ogg', '', 'my album', id='ogg "" "my album"'),
            pytest.param('artist album.ogg', 'my artist', 'my album', id='ogg "my artist" "my album"'),
            # wma
            pytest.param('_.wma', '', '', id='wma "" ""'),
            pytest.param('author.wma', 'my artist', '', id='wma "my artist" ""'),
            pytest.param('WM-AlbumTitle.wma', '', 'my album', id='wma "" "my album"'),
            pytest.param('author WM-AlbumTitle.wma', 'my artist', 'my album', id='wma "my artist" "my album"'),
            # flac
            pytest.param('_.flac', '', '', id='flac "" ""'),
            pytest.param('ARTIST.flac', 'my artist', '', id='flac "my artist" ""'),
            pytest.param('ALBUM.flac', '', 'my album', id='flac "" "my album"'),
            pytest.param('ARTIST ALBUM.flac', 'my artist', 'my album', id='flac "my artist" "my album"'),
            #pytest.param('', '', '', id='"" ""'),
        )
    )
    def test_parse_media_file(self, ti_fname, ti_ar, ti_al):
        fp = exists_or_skip(ti_fname)
        ar, al = audio_type_get_artist_album[fp.suffix](fp)
        assert ar == ti_ar
        assert al == ti_al

    def test_ogg_as_mp3_fail(self):
        fp = exists_or_skip('_.ogg')
        with pytest.raises(ID3NoHeaderError):
            get_artist_album_mp3(fp)

    def test_ogg_as_wma_fail(self):
        fp = exists_or_skip('_.ogg')
        with pytest.raises(ASFHeaderError):
            get_artist_album_asf(fp)

    def test_ogg_as_flac_fail(self):
        fp = exists_or_skip('_.ogg')
        with pytest.raises(FLACNoHeaderError):
            get_artist_album_flac(fp)

    def test_bad_file_suffix(self):
        with pytest.raises(KeyError):
            _ = audio_type_get_artist_album['foo.bad']
