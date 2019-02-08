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
import re
import logging
from pathlib import Path
import pytest
import tempfile

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
#from ..coverlovin2 import get_artist_album_mp4
from ..coverlovin2 import get_artist_album_flac
#from ..coverlovin2 import get_artist_album_ogg
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
    fp = join_test_rp(*args)
    if not fp.exists():
        pytest.skip('test resource not available "%s"' % fp)
        return None
    return fp


class Test_CoverLovin2_GoogleCSE_Opts(object):

    def test_1a_False(self):
        gc = GoogleCSE_Opts('', '', '')
        assert not gc

    def test_1b_False(self):
        gc = GoogleCSE_Opts('foo', '', '')
        assert not gc

    def test_1c_False(self):
        gc = GoogleCSE_Opts('foo', 'bar', '')
        assert not gc

    def test_1d_False(self):
        gc = GoogleCSE_Opts('foo', 'bar', None)
        assert not gc

    def test_1e_False(self):
        gc = GoogleCSE_Opts(None, 'bar', None)
        assert not gc

    def test_2a_True(self):
        gc = GoogleCSE_Opts('foo', 'bar', 'baz')
        assert gc

    def test_2b_True(self):
        gc = GoogleCSE_Opts('foo', r'as jo2u3 lj;las;  :L@)(* ;23', 'baz')
        assert gc

    def test_3a_raise(self):
        with pytest.raises(TypeError):
            GoogleCSE_Opts()

    def test_3b_raise(self):
        with pytest.raises(TypeError):
            GoogleCSE_Opts('')

    def test_3c_raise(self):
        with pytest.raises(TypeError):
            GoogleCSE_Opts('', '')

    def test_3d_raise(self):
        with pytest.raises(TypeError):
            GoogleCSE_Opts('', '', '', '')


class Test_CoverLovin2_helpers(object):

    def test_str_AA_1(self):
        saa1 = str_AA(Artist(''), Album(''))
        assert saa1 == '''｛ "" • "" ｝'''

    def test_str_AA_2(self):
        saa1 = str_AA(Artist('Foo'), Album('Bar'))
        assert saa1 == '''｛ "Foo" • "Bar" ｝'''

    def test_URL_is_http_1_True(self):
        _ = URL('https://')

    def test_URL_is_http_2_True(self):
        _ = URL('http://')

    def test_URL_is_http_3_False(self):
        with pytest.raises(ValueError):
            _ = URL('foo')

    def test_URL_is_http_4_False(self):
        with pytest.raises(ValueError):
            _ = URL('')

    def test_URL_is_http_5_False(self):
        url = URL()
        assert not url

    def test_str_log_new_1(self):
        log1 = log_new('log1', logging.DEBUG)
        assert log1.hasHandlers()

    def test_str_log_new_2(self):
        log2a = log_new('log2a', logging.DEBUG)
        log2b = log_new('log2b', logging.DEBUG)
        assert log2a is log2b

    def test_str_log_2_same_id(self):
        log3a = log_new('log3', logging.DEBUG)
        log3b = log_new('log3', logging.DEBUG)
        assert log3a is log3b
        assert id(log3a) == id(log3b)

    def test_func_name_1(self):
        assert func_name() == 'test_func_name_1'

    def test_similar_type(self):
        s1 = similar('', '')
        assert type(s1) is float

    # try this using @pytest.fixture
    # convenient place to set each test entry on one line
    _str_odd1 = \
        r'an874987()#&_@( 87398skjEQhe]w?a]fuheusn-09- klnknd\#(!  njbBIOE'
    _str_un2 = r'''¶棲摓Ⲫ⸙Ａ'''
    _str_long3 = 'abkjadliuewoijkblhlkjaoiquweaghbkjhkljhldkjhaldkh'

    sim_fixture_entries = (
        #((string1, string2), expected_value),  # passed as `fixture_5_` in
        #                                       # `test_similar`
        #                       explanatory_string_id_printed_in_results)
        #
        # `expected_value` may be an int value for `a == score` comparison
        #  or it is a two-element tuple for `a ≤ score ≤ b` comparison
        ((('', ''), 1.0),                   '""≟"" == 1.0'),
        ((('a', 'a'), 1.0),                 '"a"≟"a" == 1.0'),
        (((_str_odd1, _str_odd1), 1.0),     '_str_odd1 ≟ _str_odd1 == 1.0'),
        (((_str_un2, _str_un2), 1.0),       '_str_un2 ≟ _str_un2 == 1.0'),
        ((('abcdefg', 'defghijk'), (0.5333, 0.534)), '0.533 ≤ overlap ≤ 0.534'),
        ((('', _str_long3), (0, 0.001)),    '""≟"jslkjsdlkjf…"'),
        (((_str_long3, ''), (0, 0.001)),    '"jslkjsdlkjf…"≟""'),
    )

    @pytest.fixture(params=[p[0] for p in sim_fixture_entries],
                    ids=[p[1] for p in sim_fixture_entries])
    def fixture_5_(self, request):
        return request.param

    def test_similar(self, fixture_5_):
        s1, s2 = fixture_5_[0]
        score = similar(s1, s2)
        compare = fixture_5_[1]
        if type(compare) is int or type(compare) is float:
            assert score == compare
        elif type(compare) is tuple and len(compare) == 2:
            assert compare[0] <= score <= compare[1]
        else:
            raise ValueError('test_case[1] entry is not correct')


class Test_CoverLovin2_ImageType(object):

    def test_2a_raise(self):
        with pytest.raises(ValueError):
            ImageType('unknown type')

    def test_2b_raise(self):
        with pytest.raises(ValueError):
            ImageType('')

    def test_2c_raise(self):
        with pytest.raises(ValueError):
            ImageType(5)

    def test_2d_raise(self):
        with pytest.raises(ValueError):
            ImageType({})

    def test_2e_raise(self):
        with pytest.raises(ValueError):
            ImageType('.gif')

    def test_3a_okay(self):
        ImageType('jpg')

    def test_3b_okay(self):
        ImageType(ImageType.PNG)

    def test_3c_okay(self):
        ImageType(ImageType.GIF)

    def test_3d_okay(self):
        """ensure previous `test_3*_okay` tests cover possible cases"""
        assert len(ImageType.list()) == 3


jpg = ImageType.JPG
gif = ImageType.GIF
png = ImageType.PNG


class Test_CoverLovin2_overrides(object):
    """
    Cannot test @overrides because @overrides check runs at some point prior to
    run-time, during some sort of Python pre-run phase. Prior to pytest being
    ready.
    """


# placeholder image url for testing downloading
image_url = 'http://via.placeholder.com/2'

class Test_CoverLovin2_ImageSearcher(object):

    # make `log` class-wide (can not implement `__init__` for pytest processed
    # class)
    log = log_new(LOGFORMAT, logging.DEBUG, __qualname__)

    @pytest.mark.dependency(name=['net_access_ping'])
    def test_net_access_ping(self):
        """check Internet access. ping of known stable IP."""
        # TODO: complete this!
        pass

    @pytest.mark.dependency(name=['net_access_dns'],
                            depends=['net_access_ping'])
    def test_net_access_dns(self):
        """check Internet access. attempt DNS lookup."""
        # TODO: complete this!
        pass

    @pytest.mark.dependency(name=['net_access'], depends=['net_access_ping',
                                                          'net_access_dns'])
    def test_net_access(self):
        """Wrapper of two net access dependency for simpler `depends` params"""
        pass

    @pytest.mark.dependency(name='init_is')
    def test_ImageSearcher_init(self):
        with pytest.raises(TypeError):
            ImageSearcher('', False)

    def test_ImageSearcher_download_url__assert(self):
        with pytest.raises(AssertionError):
            """bad url should raise"""
            ImageSearcher.download_url('', self.log)

    def test_ImageSearcher_download_url__None(self):
        """non-exists download URL should return None"""
        assert not ImageSearcher.download_url('http://NOTEXISTURL.TESTFOO',
                                              self.log)

    def test_ImageSearcher_download_url__1(self):
        assert ImageSearcher.download_url(image_url, self.log)

    def test_ImageSearcher_download_url__2(self):
        data = ImageSearcher.download_url(image_url, self.log)
        assert type(data) is bytes

    @pytest.mark.dependency(name='init_likelyc')
    def test_ImageSearcher_LikelyCover_1_init(self):
        ImageSearcher_LikelyCover(Path(''), '', False)

    @pytest.mark.dependency(depends=['init_likelyc'])
    def test_ImageSearcher_LikelyCover_1_WrongUseError(self):
        is_ = ImageSearcher_LikelyCover(Path(''), '', False)
        with pytest.raises(ImageSearcher_LikelyCover.WrongUseError):
            is_.write_album_image(Path(''), True, True)

    A_Dir = 'test_ImageSearcher_LikelyCover1'  # actual sub-directory
    A_Mp3 = 'ID3v1 [Bob Dylan] [Highway 61 Revisited].mp3'  # actual test file

    @pytest.mark.dependency(depends=['init_likelyc'])
    def test_ImageSearcher_LikelyCover_2_empty_ArtAlb(self):
        """There should be no image files in the directory."""
        fp = exists_or_skip(self.A_Dir, self.A_Mp3)
        is_ = ImageSearcher_LikelyCover(fp, 'my referred', False)
        for it in ImageType.list():
            assert not is_.search_album_image(Artist(''), Album(''),
                                              ImageType(it))

    @pytest.mark.dependency(depends=['init_likelyc'])
    def test_ImageSearcher_LikelyCover_3_assert_TypeError(self):
        is_ = ImageSearcher_LikelyCover(Path(), '', False)
        with pytest.raises(TypeError):
            _ = is_._match_likely_name(jpg, None)

    @pytest.mark.dependency(depends=['init_likelyc'])
    def test_ImageSearcher_LikelyCover_3_assert_AttributeError(self):
        is_ = ImageSearcher_LikelyCover(Path(), '', False)
        with pytest.raises(AttributeError):
            _ = is_._match_likely_name(None, None)

    @pytest.mark.dependency(depends=['init_likelyc'])
    def test_ImageSearcher_LikelyCover_3_match__empty_file_list(self):
        fp = exists_or_skip(self.A_Dir, self.A_Mp3)
        is_ = ImageSearcher_LikelyCover(fp, '', False)
        assert not is_._match_likely_name(jpg, [])

    @pytest.fixture(params=[it for it in ImageType], ids=ImageType.list())
    def _fixture_3(self, request):
        return request.param

    @pytest.mark.dependency(depends=['init_likelyc'])
    def test_ImageSearcher_LikelyCover_3_nomatch_(self, _fixture_3):
        image_type = _fixture_3
        fp = exists_or_skip(self.A_Dir, self.A_Mp3)
        is_ = ImageSearcher_LikelyCover(fp, '', False)
        files = [Path.joinpath(test_resource_path, 'foo' + image_type.suffix),
                 Path.joinpath(test_resource_path, 'bar' + image_type.suffix)
                 ]
        assert not is_._match_likely_name(image_type, files)

    # def test_ImageSearcher_LikelyCover_3_nomatch_png(self):
    #     fp = exists_or_skip(Test_CoverLovin2_ImageSearcher.A_Dir,
    #                         Test_CoverLovin2_ImageSearcher.A_Mp3)
    #     is_ = ImageSearcher_LikelyCover(fp, '', False)
    #     files = [Path.joinpath(test_resource_path, 'foo' + jpg.suffix),
    #              Path.joinpath(test_resource_path, 'bar' + jpg.suffix)
    #              ]
    #     assert not is_._match_likely_name(jpg, files)
    # 
    # def test_ImageSearcher_LikelyCover_3_match_nomatch_gif(self):
    #     fp = exists_or_skip(Test_CoverLovin2_ImageSearcher.A_Dir,
    #                         Test_CoverLovin2_ImageSearcher.A_Mp3)
    #     is_ = ImageSearcher_LikelyCover(fp, '', False)
    #     files = [Path.joinpath(test_resource_path, 'foo' + gif.suffix),
    #              Path.joinpath(test_resource_path, 'bar' + gif.suffix)
    #              ]
    #     assert not is_._match_likely_name(gif, files)

    @pytest.mark.dependency(depends=['init_likelyc'])
    def test_ImageSearcher_LikelyCover_3_match__no_matches(self):
        fp = exists_or_skip(self.A_Dir, self.A_Mp3)
        files = [Path.joinpath(test_resource_path, 'foo' + jpg.suffix),
                 Path.joinpath(test_resource_path, 'bar' + jpg.suffix)
                 ]
        is_ = ImageSearcher_LikelyCover(fp, '', False)
        assert not is_._match_likely_name(jpg, files)

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

    @pytest.mark.dependency(name=['test_res_B'])
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
    def test_ImageSearcher_GoogleCSE_test_res(self):
        assert self.C_fp.exists()
        assert self.C_testinput.exists()

    def test_ImageSearcher_GoogleCSE_1_init(self):
        gco = GoogleCSE_Opts('fake+key', 'fake+ID', self.C_sz)
        ImageSearcher_GoogleCSE(gco, 'referrer!', False)

    def test_ImageSearcher_GoogleCSE_1_false(self):
        gco = GoogleCSE_Opts('', '', self.C_sz)
        assert not ImageSearcher_GoogleCSE(gco, 'referrer!', False)

    def _stub_response1(*args, **kwargs):
        """To replace `ImageSearcher_GoogleCSE._search_response_json`"""
        return open(str(Test_CoverLovin2_ImageSearcher.C_testinput))

    def _stub_download_url(*args, **kwargs):
        """To replace `ImageSearcher_GoogleCSE.download_url`"""
        return bytes('fake image date', encoding='utf8')

    # create ImageSearcher_GoogleCSE with stubbed methods
    C_gopt = GoogleCSE_Opts('fake+key', 'fake+ID', ImageSize.SML)
    C_isg = ImageSearcher_GoogleCSE(C_gopt, 'referrer!', False)
    C_isg._search_response_json = _stub_response1
    C_isg.download_url = _stub_download_url

    def test_ImageSearcher_GoogleCSE_2_search_basic(self):
        assert self.C_isg.search_album_image(self.C_Artist, self.C_Album, jpg)

    def test_ImageSearcher_GoogleCSE_2_search_basic_diff_ArtAlb1(self):
        """
        This implementation of search_album_image doesn't look directly
        at Artist and Album value, it only hands it off.
        """
        assert self.C_isg.search_album_image(Artist('A'), Album('B'), jpg)

    def test_ImageSearcher_GoogleCSE_2_search_basic_diff_ArtAlb2(self):
        assert self.C_isg.search_album_image(Artist('A'), Album(''), jpg)

    def test_ImageSearcher_GoogleCSE_2_search_basic_diff_ArtAlb3(self):
        assert self.C_isg.search_album_image(Artist(''), Album('A'), jpg)

    def test_ImageSearcher_GoogleCSE_2_search_empty_False(self):
        assert not self.C_isg.search_album_image(Artist(''), Album(''), jpg)

    def _stub_response2(*args, **kwargs):
        testinput2 = test_resource_path.joinpath(
            'googlecse-response3-onlygooglecacheimage.json')
        return open(str(testinput2))

    # XXX: presuming only one instance of this test runs at a time
    _6_testfile = Path(tempfile.gettempdir(), tempfile.gettempprefix() +
                       __qualname__)

    #XXX: how to pass in the Path to this fixture finalizer?
    def _6_rm_testfile(self):
        try:
            os.remove(self._6_testfile)
        except OSError:
            pass

    @pytest.fixture()
    def _6_fixture(self, request):
        request.addfinalizer(self._6_rm_testfile)

    @pytest.mark.dependency(depends=['net_access'])
    def test_ImageSearcher_GoogleCSE_2_search_use_altgooglecache(self,
                                                                 _6_fixture):
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


class Test_CoverLovin2_media(object):

    def test_mp3_ID3v1_(self):
        fp = exists_or_skip('ID3v1 _.mp3')
        ar, al = audio_type_get_artist_album[fp.suffix](fp)
        assert ar == ''
        assert al == ''

    def test_mp3_ID3v1_artist_album(self):
        fp = exists_or_skip('ID3v1 artist album.mp3')
        ar, al = audio_type_get_artist_album[fp.suffix](fp)
        assert ar == 'my artist'
        assert al == 'my album'

    def test_mp3_ID3v1_artist(self):
        fp = exists_or_skip('ID3v1 artist.mp3')
        ar, al = audio_type_get_artist_album[fp.suffix](fp)
        assert ar == 'my artist'
        assert al == ''

    def test_mp3_ID3v1_ID3v2_artist_album(self):
        fp = exists_or_skip('ID3v1 ID3v2 artist album.mp3')
        ar, al = audio_type_get_artist_album[fp.suffix](fp)
        assert ar == 'my artist'
        assert al == 'my album'

    def test_mp3_ID3v2_artist_album(self):
        fp = exists_or_skip('ID3v2 artist album.mp3')
        ar, al = audio_type_get_artist_album[fp.suffix](fp)
        assert ar == 'my artist'
        assert al == 'my album'

    def test_mp3_ID3v1_albumartist_album(self):
        fp = exists_or_skip('ID3v1 albumartist album.mp3')
        ar, al = audio_type_get_artist_album[fp.suffix](fp)
        assert ar == 'my albumartist'
        assert al == 'my album'

    def test_mp3__(self):
        fp = exists_or_skip('_.mp3')
        ar, al = audio_type_get_artist_album[fp.suffix](fp)
        assert ar == ''
        assert al == ''

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

    def test_ogg__(self):
        fp = exists_or_skip('_.ogg')
        ar, al = audio_type_get_artist_album[fp.suffix](fp)
        assert ar == ''
        assert al == ''

    def test_ogg_artist(self):
        fp = exists_or_skip('artist.ogg')
        ar, al = audio_type_get_artist_album[fp.suffix](fp)
        assert ar == 'my artist'
        assert al == ''

    def test_ogg_album(self):
        fp = exists_or_skip('album.ogg')
        ar, al = audio_type_get_artist_album[fp.suffix](fp)
        assert ar == ''
        assert al == 'my album'

    def test_ogg_artist_album(self):
        fp = exists_or_skip('artist album.ogg')
        ar, al = audio_type_get_artist_album[fp.suffix](fp)
        assert ar == 'my artist'
        assert al == 'my album'

    def test_wma__(self):
        fp = exists_or_skip('_.wma')
        ar, al = audio_type_get_artist_album[fp.suffix](fp)
        assert ar == ''
        assert al == ''

    def test_wma_artist(self):
        fp = exists_or_skip('author.wma')
        ar, al = audio_type_get_artist_album[fp.suffix](fp)
        assert ar == 'my artist'
        assert al == ''

    def test_wma_album(self):
        fp = exists_or_skip('WM-AlbumTitle.wma')
        ar, al = audio_type_get_artist_album[fp.suffix](fp)
        assert ar == ''
        assert al == 'my album'

    def test_wma_artist_album(self):
        fp = exists_or_skip('author WM-AlbumTitle.wma')
        ar, al = audio_type_get_artist_album[fp.suffix](fp)
        assert ar == 'my artist'
        assert al == 'my album'

    def test_flac__(self):
        fp = exists_or_skip('_.flac')
        ar, al = audio_type_get_artist_album[fp.suffix](fp)
        assert ar == ''
        assert al == ''

    def test_flac_artist(self):
        fp = exists_or_skip('ARTIST.flac')
        ar, al = audio_type_get_artist_album[fp.suffix](fp)
        assert ar == 'my artist'
        assert al == ''

    def test_flac_album(self):
        fp = exists_or_skip('ALBUM.flac')
        ar, al = audio_type_get_artist_album[fp.suffix](fp)
        assert ar == ''
        assert al == 'my album'

    def test_flac_artist_album(self):
        fp = exists_or_skip('ARTIST ALBUM.flac')
        ar, al = audio_type_get_artist_album[fp.suffix](fp)
        assert ar == 'my artist'
        assert al == 'my album'

    def test_bad_file_suffix(self):
        with pytest.raises(KeyError):
            _ = audio_type_get_artist_album['.bad']
