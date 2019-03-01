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
import queue

# non-standard library imports
from mutagen.id3 import ID3NoHeaderError
from mutagen.asf import ASFHeaderError
from mutagen.flac import FLACNoHeaderError

# custom imports
from ..coverlovin2 import (
    Artist,
    Album,
    DirArtAlb,
    DirArtAlb_List,
    GoogleCSE_Opts,
    ImageSize,
    ImageType,
    URL,
    str_AA,
    func_name,
    similar,
    log_new,
    LOGFORMAT,
    get_artist_album_mp3,
    get_artist_album_mp4,
    get_artist_album_flac,
    get_artist_album_ogg,
    get_artist_album_asf,
    get_artist_album,
    ImageSearcher,
    ImageSearcher_LikelyCover,
    ImageSearcher_EmbeddedMedia,
    ImageSearcher_MusicBrainz,
    ImageSearcher_GoogleCSE,
    process_dir,
    process_dirs,
    parse_args_opts,
)

# all committed test resources should be under this directory
resources = Path.joinpath(Path(__file__).parent, 'test_resources')

empty_ArtAlb = (Artist(''), Album(''))


def exists_or_skip(*args) -> typing.Union[Path, None]:
    """helper for skipping a test if path is not available"""
    fp = resources.joinpath(*args)
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


class Test_ImageSize(object):

    def test_list(self):
        assert ImageSize.list()


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
    def test_WrongUseError(self):
        is_ = ImageSearcher_LikelyCover(Path(''), '', False)
        with pytest.raises(ImageSearcher_LikelyCover.WrongUseError):
            is_.write_album_image(Path(''), True, True)

    A1_Dir = 'test_ImageSearcher_LikelyCover1'  # actual sub-directory
    A1_Mp3 = 'ID3v1 [Bob Dylan] [Highway 61 Revisited].mp3'  # actual test file
    A1_fp = resources.joinpath(A1_Dir, A1_Mp3)  # existent file path

    @pytest.mark.dependency(name='test_res_A1')
    def test_A1_resources_exist_and_correct(self):
        """test resources must exist"""
        assert self.A1_fp
        assert self.A1_fp.exists()
        """there should be no image files in the test resource directory"""
        # TODO: check this

    @pytest.mark.dependency(depends=['init_likelyc'])
    def test_match_likely_name__TypeError(self):
        is_ = ImageSearcher_LikelyCover(Path(), '', False)
        with pytest.raises(TypeError):
            _ = is_._match_likely_name(jpg, None)  # type: ignore

    @pytest.mark.dependency(depends=['init_likelyc'])
    def test_match_likely_name__AttributeError(self):
        is_ = ImageSearcher_LikelyCover(Path(), '', False)
        with pytest.raises(AttributeError):
            _ = is_._match_likely_name(None, None)  # type: ignore

    # pytest.param
    # (
    #   ImageType,
    #   (
    #       Path_to_match1,
    #       Path_to_match2,
    #       ...
    #   ),
    #   Path_expected_to_match
    # ),
    @pytest.mark.parametrize('ti_it, ti_paths, ti_path_match',
        (
            pytest.param
            (
                jpg,
                [],
                None,
                id='empty List (returns None)'
            ),
            pytest.param
            (
                jpg,
                (),
                None,
                id='empty Tuple (returns None)'
            ),
            *(  # generate a simple test case for all ImageTypes
                    pytest.param
                    (
                        it,
                        (
                            Path.joinpath(resources, 'DOES NOT EXIST foo' + it.suffix),
                            Path.joinpath(resources, 'DOES NOT EXIST bar' + it.suffix),
                        ),
                        None,
                        id='quick test of ImageType ' + it.value + ' (returns None)'
                    ) for it in ImageType
            ),
            pytest.param
            (
                jpg,
                (
                    Path('nope' + jpg.suffix),
                    Path('nope' + png.suffix),
                ),
                None,
                id='(no match) nope' + png.suffix + ' (returns None)'
            ),
            pytest.param
            (
                jpg,
                (
                    Path('AlbumArt_Small' + jpg.suffix),
                    Path('AlbumArt_Large' + jpg.suffix)
                ),
                Path('AlbumArt_Large' + jpg.suffix),
                id='AlbumArt_Large' + jpg.suffix
            ),
            pytest.param
            (
                jpg,
                (
                    Path('front-here' + jpg.suffix),
                    Path('here-front' + jpg.suffix)
                ),
                Path('front-here' + jpg.suffix),
                id='front-here' + jpg.suffix
            ),
            pytest.param
            (
                png,
                (
                    Path('fronthere' + png.suffix),
                    Path('here-front' + png.suffix)
                ),
                Path('here-front' + png.suffix),
                id='here-front' + png.suffix
            ),
            pytest.param
            (
                jpg,
                (
                    Path('foo (front)' + jpg.suffix),
                    Path('folder' + jpg.suffix)
                ),
                Path('foo (front)' + jpg.suffix),
                id='foo (front)' + jpg.suffix
             ),
            pytest.param
            (
                jpg,
                (
                    Path('AlbumArt01' + jpg.suffix),
                    Path('foo (front)' + jpg.suffix)
                ),
                Path('AlbumArt01' + jpg.suffix),
                id='AlbumArt01' + jpg.suffix
            ),
            pytest.param
            (
                jpg,
                (
                    Path('foo (front)' + jpg.suffix),
                    Path('AlbumArt01' + jpg.suffix)
                ),
                Path('AlbumArt01' + jpg.suffix),
                id='AlbumArt01' + jpg.suffix
            ),
            pytest.param
            (
                jpg,
                (
                    Path('R-3512668-1489953889-2577 cover.jpeg' + jpg.suffix),
                    Path('nomatch' + jpg.suffix)
                ),
                Path('R-3512668-1489953889-2577 cover.jpeg' + jpg.suffix),
                id='R-3512668-1489953889-2577 cover.jpeg' + jpg.suffix
            ),
            pytest.param
            (
                jpg,
                (
                    Path('album_cover.jpeg' + jpg.suffix),
                    Path('nomatch' + jpg.suffix)
                ),
                Path('album_cover.jpeg' + jpg.suffix),
                id='album_cover.jpeg' + jpg.suffix
            ),
            pytest.param
            (
                jpg,
                (
                    Path('nomatch' + jpg.suffix),
                    Path('Something (front) blarg' + jpg.suffix)
                ),
                Path('Something (front) blarg' + jpg.suffix),
                id='Something (front) blarg' + jpg.suffix
            ),
            pytest.param
            (
                jpg,
                (
                    Path('Something-front-blarg' + jpg.suffix),
                    Path('Something (front) blarg' + jpg.suffix)
                ),
                Path('Something (front) blarg' + jpg.suffix),
                id='Something (front) blarg' + jpg.suffix
            ),
            pytest.param
            (
                png,
                (
                    Path('Something-front-blarg' + png.suffix),
                    Path('Something (front) blarg' + png.suffix)
                ),
                Path('Something (front) blarg' + png.suffix),
                id='Something (front) blarg' + png.suffix
            ),
            pytest.param
            (
                gif,
                (
                    Path('Something-front-blarg' + gif.suffix),
                    Path('Something (front) blarg' + gif.suffix)
                ),
                Path('Something (front) blarg' + gif.suffix),
                id='Something (front) blarg' + gif.suffix
            ),
            pytest.param
            (
                jpg,
                (
                    Path('Something-front-blarg' + jpg.suffix),
                    Path('Something' + png.suffix),
                    Path('Something' + jpg.suffix),
                    Path('Something' + gif.suffix)
                ),
                Path('Something-front-blarg' + jpg.suffix),
                id='Something-front-blarg' + jpg.suffix
            ),
            pytest.param
            (
                jpg,
                (
                    Path('folder' + png.suffix),
                    Path('folder' + jpg.suffix),
                    Path('folder' + gif.suffix)
                ),
                Path('folder' + jpg.suffix),
                id='folder' + jpg.suffix
            ),
            pytest.param
            (
                png,
                (
                    Path('folder' + png.suffix),
                    Path('folder' + jpg.suffix),
                    Path('folder' + gif.suffix)
                ),
                Path('folder' + png.suffix),
                id='folder' + png.suffix
            ),
            pytest.param
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
                Path('Something (front) blarg' + jpg.suffix),
                id='Something (front) blarg' + jpg.suffix
            ),
            pytest.param
            (
                jpg,
                (
                    Path('Something-front-blarg' + jpg.suffix),
                    Path('Something (front) blarg' + '.jpeg'),
                ),
                Path('Something (front) blarg' + '.jpeg'),
                id='Something (front) blarg' + '.jpeg'
            ),
        )
    )
    @pytest.mark.dependency(depends=['init_likelyc'])
    def test_match_likely_name__match(self, ti_it, ti_paths, ti_path_match):
        is_ = ImageSearcher_LikelyCover(Path(), '', False)
        m = is_._match_likely_name(ti_it, ti_paths)
        assert m == ti_path_match

    B_cmp_name = lambda x, y: x.name == y.name
    B2_Dir = 'test_ImageSearcher_LikelyCover2'  # actual sub-directory
    B2_Img = 'album.jpg'  # actual test file in that sub-directory
    B2_image_path = resources.joinpath(B2_Dir, B2_Img)  # file path test resource .../album.jpg
    # these files not need to exist
    B_image_path_ne = Path(r'./THIS FILE DOES NOT EXIST 298389325 (album_cover)' + jpg.suffix)
    B_image_path_1 = Path(r'./ACDC TNT/ACDC TNT' + png.suffix)
    B_image_path_2 = Path(r'./Kraftwerk - Minimum Maximum/Minimum Maximum' + gif.suffix)
    B_image_path_3 = Path(r'./Kraftwerk - Minimum Maximum/Kraftwerk' + jpg.suffix)
    B_image_path_Xid = 'Do match similar file name to similar parent directory name: '

    @pytest.mark.dependency(name='test_res_B2')
    def test_B2_resources_exist(self):
        assert self.B2_image_path.exists()
        for fp in (self.B_image_path_ne,
                   self.B_image_path_1,
                   self.B_image_path_2,
                   self.B_image_path_3,):
            assert not fp.exists()

    @pytest.mark.parametrize(
        'image_path, image_type, files, test_expect, special_cmp',
        (
            pytest.param
            (
                B2_image_path, jpg, (B2_image_path,), None, None,
                id='same file exists (Do not match actual file to itself)' + jpg.suffix
            ),
            pytest.param
            (
                B_image_path_ne, jpg, (B_image_path_ne,), B_image_path_ne, B_cmp_name,
                id='same file not exist (Do match non-existent same file)'
            ),
            pytest.param
            (
                B_image_path_1, png, (B_image_path_1,), B_image_path_1, B_cmp_name,
                id=B_image_path_Xid + str(B_image_path_1)
            ),
            pytest.param
            (
                B_image_path_2, gif, (B_image_path_2,), B_image_path_2, B_cmp_name,
                id=B_image_path_Xid + str(B_image_path_2)
            ),
            pytest.param
            (
                B_image_path_3, jpg, (B_image_path_3,), B_image_path_3, B_cmp_name,
                id=B_image_path_Xid + str(B_image_path_3)
            ),
        )
    )
    @pytest.mark.dependency(depends=['init_likelyc', 'test_res_B2'])
    def test__match_likely_name(self, image_path, image_type, files, test_expect, special_cmp):
        is_ = ImageSearcher_LikelyCover(image_path, '', False)
        mln = is_._match_likely_name(image_type, files)
        assert test_expect == mln
        if special_cmp:
            assert special_cmp(mln, test_expect)

    @pytest.mark.dependency(depends=['init_likelyc', 'test_res_B2'])
    def test_search_album_image_images(self):
        is_ = ImageSearcher_LikelyCover(self.A1_fp, 'referrer', False)
        for it in ImageType.list():
            assert not is_.search_album_image(Artist(''), Album(''),
                                              ImageType(it))


    B_Artist = Artist('Bob Dylan')
    B_Album = Album('Biograph (Disc 1)')
    B3_Dir = 'test_ImageSearcher_LikelyCover3'  # actual sub-directory
    B3_Img1 = 'album1.jpg'  # actual test file in that sub-directory
    B3_Img2 = 'album2.jpg'  # actual test file in that sub-directory
    B3_Img_ne = 'album-not-exists-file.jpg'  # does not exist
    B3_image_path1 = resources.joinpath(B3_Dir, B3_Img1)
    B3_image_path2 = resources.joinpath(B3_Dir, B3_Img2)
    B3_image_path_ne = resources.joinpath(B3_Dir, B3_Img_ne)

    @pytest.mark.dependency(name='test_res_B3')
    def test_B3_resources_exist(self):
        assert self.B3_image_path1.exists()
        assert self.B3_image_path2.exists()
        assert not self.B3_image_path_ne.exists()

    @pytest.mark.parametrize(
        'image_path_src, image_path_dst, image_type, overwrite, test_expect',
        (
            pytest.param
            (
                B3_image_path1, B3_image_path2, jpg, False, False,
                id='destination image already exists - overwrite False, returns False'
            ),
            pytest.param
            (
                B3_image_path1, B3_image_path2, jpg, True, True,
                id='destination image already exists - overwrite True, returns True'
            ),
            pytest.param
            (
                B3_image_path1, B3_image_path_ne, jpg, False, True,
                id='happy path - case 1 - overwrite False'
            ),
            pytest.param
            (
                B3_image_path1, B3_image_path_ne, jpg, True, True,
                id='happy path - case 2 - overwrite True'
            )
        )
    )
    @pytest.mark.dependency(name='test_res_B3')
    def test_write_album_image(self, image_path_src, image_path_dst, image_type, overwrite, test_expect):
        is_ = ImageSearcher_LikelyCover(image_path_dst, '', False)
        assert is_.search_album_image(Artist(''), Album(''), image_type)
        assert test_expect == is_.write_album_image(Path(), overwrite, True)


class Test_ImageSearcher_EmbeddedMedia(object):
    """
    Test the ImageSearcher_EmbeddedMedia class
    """

    E_Artist = Artist('my artist')
    E_Album = Album('my album')
    E_imagepath1 = Path.joinpath(resources, 'test_ImageSearcher_EmbeddedMedia1', 'cover.jpg')
    E_imagepath2 = Path.joinpath(resources, 'test_ImageSearcher_EmbeddedMedia2', 'cover.jpg')
    E_imagepath3jpg = Path.joinpath(resources, 'test_ImageSearcher_EmbeddedMedia3 JPG', 'cover.jpg')
    E_imagepath3png = Path.joinpath(resources, 'test_ImageSearcher_EmbeddedMedia3 PNG', 'cover.png')
    E_imagepath3e_mp3 = Path.joinpath(resources, 'test_ImageSearcher_EmbeddedMedia3 empty mp3', 'cover.png')
    E_imagepath3e_mp4 = Path.joinpath(resources, 'test_ImageSearcher_EmbeddedMedia3 empty mp4', 'cover.png')
    E_imagepath3e_ogg = Path.joinpath(resources, 'test_ImageSearcher_EmbeddedMedia3 empty ogg', 'cover.png')
    E_imagepath3e_flac = Path.joinpath(resources, 'test_ImageSearcher_EmbeddedMedia3 empty flac', 'cover.png')
    E_imagepath3e_wma = Path.joinpath(resources, 'test_ImageSearcher_EmbeddedMedia3 empty wma', 'cover.png')
    E_imagepath3bi = Path.joinpath(resources, 'test_ImageSearcher_EmbeddedMedia3 bad image', 'cover.png')
    E_imagepath4 = Path.joinpath(resources, 'test_ImageSearcher_EmbeddedMedia4 PNG multiple', 'cover.png')

    # @pytest.mark.dependency(name='test_res_E')
    # @pytest.mark.parametrize('test_res_path',
    #     (
    #         D_res_brg,
    #         D_res_br1,
    #         D_res_br2,
    #         D_res_gil,
    #         D_res_grgil,
    #         D_res_sa
    #     )
    # )
    # def test_resources_exist(self, test_res_path):
    #     assert test_res_path.exists()

    @pytest.mark.parametrize('debug', (True, False))
    def test_init(self, debug):
        ImageSearcher_EmbeddedMedia(Path(), 'hello', debug)

    def test_WrongUseError(self):
        is_ = ImageSearcher_EmbeddedMedia(Path(), '', False)
        with pytest.raises(ImageSearcher_EmbeddedMedia.WrongUseError):
            is_.write_album_image(Path(), True, True)

    def test_ValueError(self):
        is_ = ImageSearcher_EmbeddedMedia(Path(), '', False)
        is_._image = True
        with pytest.raises(ValueError):
            is_.write_album_image(Path(), True, True)

    @pytest.mark.parametrize(
        'image_path, artist, album, image_type, test_expect',
        (
            pytest.param
            (
                E_imagepath1, E_Artist, E_Album, jpg, False,
                id='empty dir'
            ),
            pytest.param
            (
                E_imagepath2, E_Artist, E_Album, jpg, False,
                id='normal path - no embedded image'
            ),
            pytest.param
            (
                E_imagepath3jpg, E_Artist, E_Album, jpg, True,
                id='happy path jpg'
            ),
            pytest.param
            (
                E_imagepath3jpg, E_Artist, E_Album, png, True,
                id='happy path - embedded image is jpg, image_type is png'
            ),
            pytest.param
            (
                E_imagepath3png, E_Artist, E_Album, png, True,
                id='happy path png'
            ),
            pytest.param
            (
                E_imagepath3png, E_Artist, E_Album, jpg, True,
                id='happy path - embedded image is png, image_type is jpg'
            ),
            pytest.param
            (
                E_imagepath3e_mp3, E_Artist, E_Album, png, False,
                id='zero size mp3 file'
            ),
            pytest.param
            (
                E_imagepath3e_mp4, E_Artist, E_Album, png, False,
                id='zero size mp4'
            ),
            pytest.param
            (
                E_imagepath3e_flac, E_Artist, E_Album, png, False,
                id='zero size flac'
            ),
            pytest.param
            (
                E_imagepath3e_ogg, E_Artist, E_Album, png, False,
                id='zero size ogg file'
            ),
            pytest.param
            (
                E_imagepath3e_wma, E_Artist, E_Album, png, False,
                id='zero size wma'
            ),
            pytest.param
            (
                E_imagepath3bi, E_Artist, E_Album, png, False,
                id='mp3 file has zero byte image embedded'
            ),
            pytest.param
            (
                E_imagepath4, E_Artist, E_Album, jpg, True,
                id='mp3 file has multiple images embedded'
            )
        )
    )
    def test_search_album_image(self, image_path, artist, album, image_type,
                                test_expect):
        is_ = ImageSearcher_EmbeddedMedia(image_path, '', False)
        assert test_expect == is_.search_album_image(artist, album, image_type)

    @pytest.mark.parametrize(
        'image_path, artist, album, image_type, overwrite, test_expect',
        (
            pytest.param
            (
                E_imagepath3jpg, E_Artist, E_Album, jpg, False, False,
                id='image already exists - overwrite False, returns False'
            ),
            pytest.param
            (
                E_imagepath3jpg, E_Artist, E_Album, jpg, True, True,
                id='image already exists - overwrite True, returns True'
            )
        )
    )
    def test_write_album_image(self, image_path, artist, album, image_type,
                               overwrite, test_expect):
        assert image_path.exists()
        is_ = ImageSearcher_EmbeddedMedia(image_path, '', False)
        assert is_.search_album_image(artist, album, image_type)
        assert test_expect == is_.write_album_image(Path(), overwrite, True)

    # TODO: what else is missing?


class Test_ImageSearcher_GoogleCSE(object):
    """
    Google CSE is tedious to test live so just use dummy data. Requires
    secret values for Key and Search ID. Which then requires adding secret
    data to this project.
    """

    C_Dir = 'test_ImageSearcher_GoogleCSE1'  # actual sub-directory
    C_Img = 'album.jpg'  # actual test file in that sub-directory
    C_fp = resources.joinpath(C_Dir, C_Img)
    # create these once with short names
    C_sz = ImageSize.SML
    C_Artist = Artist('Bob Dylan')
    C_Album = Album('Biograph (Disc 1)')
    test_res1 = resources.joinpath('googlecse-response1.json')
    test_res2 = resources.joinpath('googlecse-response2.json')
    test_res3 = resources.joinpath('googlecse-response3-onlygooglecacheimage.json')

    @pytest.mark.dependency(name='test_res_C')
    @pytest.mark.parametrize('test_res', (test_res1, test_res2, test_res3))
    def test_resources_exist(self, test_res):
        assert test_res.exists()

    @pytest.mark.parametrize('debug', (True, False))
    def test_init(self, debug):
        gco = GoogleCSE_Opts('fake+key', 'fake+ID', self.C_sz)
        ImageSearcher_GoogleCSE(gco, 'referrer!', debug)

    def test_False(self):
        gco = GoogleCSE_Opts('', '', self.C_sz)
        assert not ImageSearcher_GoogleCSE(gco, 'referrer!', False)

    def _stub_response1(*args, **kwargs):
        """To replace `ImageSearcher_GoogleCSE._search_response_json`"""
        return open(str(Test_ImageSearcher_GoogleCSE.test_res1))

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
        return open(
            str(
                resources.joinpath(Test_ImageSearcher_GoogleCSE.test_res3)
            )
        )

    # XXX: presuming only one instance of this test runs at a time
    _6_testfile = Path(tempfile.gettempdir(), tempfile.gettempprefix() +
                       __qualname__)

    #
    # create a finalizer fixture to remove test file after test runs
    #

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



class Test_ImageSearcher_MusicBrainz(object):
    """
    Test the ImageSearcher_MusicBrainz class
    """

    D_Artist = Artist('Bob Dylan')
    D_Album = Album('Biograph (Disc 1)')
    D_res_brg = resources.joinpath('musicbrainz-response-browse_release_groups.json')
    D_res_br1 = resources.joinpath('musicbrainz-response-browse_releases1.json')
    D_res_br2 = resources.joinpath('musicbrainz-response-browse_releases2.json')
    D_res_gil = resources.joinpath('musicbrainz-response-get_image_list.json')
    D_res_grgil = resources.joinpath('musicbrainz-response-get_release_group_image_list.json')
    D_res_sa = resources.joinpath('musicbrainz-response-search_artists.json')

    @pytest.mark.dependency(name='test_res_C')
    @pytest.mark.parametrize('test_res_path',
        (
            D_res_brg,
            D_res_br1,
            D_res_br2,
            D_res_gil,
            D_res_grgil,
            D_res_sa
        )
    )
    def test_resources_exist(self, test_res_path):
        assert test_res_path.exists()

    @pytest.mark.parametrize('debug', (True, False))
    def test_init(self, debug):
        ImageSearcher_MusicBrainz('hello', debug)

    def test_search_album_image_no_Artist_no_Album(self):
        ismb = ImageSearcher_MusicBrainz('hello', False)
        assert not ismb.search_album_image(Artist(''), Album(''),  None)

    @pytest.mark.parametrize('sa_ret, br_ret',
        (
            pytest.param(None, None, id='None'),
            pytest.param([], None, id='[]'),
            pytest.param({}, None, id='{}'),
            pytest.param({'a': 'A'}, None, id='{"a":"A"}'),
            pytest.param({'a': 'A', 'b': 'B'}, None, id='{"a":"A",…}'),
            pytest.param(
                {
                    'artist-list': [
                        'foo',
                    ]
                },
                None,
                id='artist-list: "foo"'
            ),
            pytest.param(
                {
                    'artist-list': [
                        'foo',
                        'bar',
                    ]
                },
                None,
                id='artist-list: "foo" "bar"'
            ),
            pytest.param(
                {
                    'artist-list': [
                        {'a': 'A'},
                        {'b': 'B'},
                    ]
                },
                None,
                id='artist-list: "a:A" "b:B"'
            ),
            pytest.param(
                {
                    'artist-list': [
                        {'a': 'A',
                         'id': 'id of a'},
                        {'b': 'B',
                         'id': 'id of b'},
                    ]
                },
                None,
                id='artist-list: "a:A" "b:B" with "id"'
            ),
            # TODO: add more test cases that exercise more of the function
            #       at this point, add values for br_ret
        )
    )
    def test_search_album_image(self, sa_ret, br_ret):
        ismb = ImageSearcher_MusicBrainz('hello', False)
        def _stub_search_artists(*args, **kwargs):
            return sa_ret
        def _stub_browse_releases(*args, **kwargs):
            return br_ret
        ismb._search_artists = _stub_search_artists
        ismb._browse_releases = _stub_browse_releases
        assert not ismb.search_album_image(self.D_Artist, self.D_Album, None)

    # TODO: test remaining functions of ImageSearcher_MusicBrainz


class Test_complex_funcs(object):

    @pytest.mark.parametrize('dirp, image_nt',
        (
            pytest.param(resources.joinpath('test_process_dir_1_empty'),
                         'not exist.jpg',
                         id='test_process_dir_1_empty'),
        )
    )
    def test_process_dir(self, dirp, image_nt):
        daa_list = []
        sq = queue.SimpleQueue()
        daa_list = process_dir(dirp, image_nt, False, sq, daa_list)
        assert not daa_list
        assert sq.empty()

    res2 = resources.joinpath('test_process_dir_2')
    res2a1 = res2.joinpath('artist1 - album1')
    res2a2 = res2.joinpath('artist2 -- album2')
    res3 = resources.joinpath('test_process_dir_3')
    res3a1 = res3.joinpath('artist1 - album1')
    res3a2a = res3.joinpath('artist2', 'album2a')
    res3a2b = res3.joinpath('artist2', 'album2b')
    res3a3 = res3.joinpath('artist3 -- 2003 -- album3')
    res3a4 = res3.joinpath('artist4 ! -- 2004 -- album4 !')
    res4 = resources.joinpath('test_process_dir_4')
    res4a1 = res4.joinpath('artist1 - album has cover')  # TODO: run test this resource exists
    res4a2 = res4.joinpath('artist2 -- 2002 -- album2')

    @pytest.mark.parametrize('dirp, image_nt, qsize, daa_list_expect',
        (
            pytest.param
            (
                res2, 'cover.jpg', 0, [
                    (res2a1, Artist('artist1'), Album('album1')),
                    (res2a2, Artist('artist2'), Album('album2')),
                ],
                id=res2.name
            ),
            pytest.param
            (
                res3, 'cover.jpg', 0, [
                    (res3a1, Artist('artist1'), Album('album1')),
                    # unable to parse path structure artist/album/song.mp3 so these Artist Album are empty
                    (res3a2a, Artist(''), Album('')),
                    (res3a2b, Artist(''), Album('')),
                    (res3a3, Artist('artist3'), Album('album3')),
                    (res3a4, Artist('artist4 !'), Album('album4 !')),
                ],
                id=res3.name
            ),
            pytest.param
            (
                res4, 'cover.jpg', 1, [
                    # should not include res4a1
                    (res4a2, Artist('artist2'), Album('album2')),
                ],
                id=res4.name
            ),
        )
    )
    def test_process_dir(self, dirp: Path, image_nt: str, qsize, daa_list_expect):
        sq = queue.SimpleQueue()
        assert dirp.is_dir()
        daa_list = process_dir(dirp, image_nt, False, sq, [])
        assert daa_list == daa_list_expect
        assert qsize == sq.qsize()

    # TODO: add testing of process_dir that exercises more code
    #       need to add test "album" directories
    #def test_process_dirs(self):
    #    return True

    @pytest.mark.parametrize('args',
        (
            pytest.param([], id='(empty)'),
            pytest.param(['--help'], id='--help'),
            pytest.param(['.'], id='no search methods selected'),
            pytest.param(['-sg', '.'], id='Google missing gkey gid'),
            pytest.param(['-sg', '--sgkey', 'foobar', '.'], id='Google missing gid'),
            pytest.param(['-sg', '--sgid ', 'foobar', '.'], id='Google missing gkey'),
        )
    )
    def test_parse_args_raises_SystemExit(self, args):
        with pytest.raises(SystemExit):
            parse_args_opts(args=args)


    # These tests do not need to be elaborate. Enough confidence can be had of
    # the argparse.ArgumentParser setup via code inspection; not worth the time
    # trade-off. These tests are to increase code coverage score.
    argtest1 = ['-se', '.']
    argtest2 = ['-se', '--test', '.', '..']
    argtest3 = ['-sg', '--sgid', 'my id', '--sgkey', 'my key', '.']
    argtest4 = ['-sg', '--sgid', 'my id', '--sgkey', 'my key', '.', '.']
    argtest5 = ['.', '-sg', '--sgid', 'my id', '--sgkey', 'my key', '.', '.']
    @pytest.mark.parametrize('args',
        (
            pytest.param(argtest1, id=str(argtest1)),
            pytest.param(argtest2, id=str(argtest2)),
            pytest.param(argtest3, id=str(argtest3)),
            pytest.param(argtest4, id=str(argtest4)),
            pytest.param(argtest5, id=str(argtest5)),
        )
    )
    def test_parse_args(self, args):
        assert parse_args_opts(args=args)

    @pytest.mark.parametrize('args, ret_expect',
        (
            pytest.param(['-s-', '.'],
                         (['.'], None, None, True, True, True, False, None, None, None, None, None),
                         id='-s- .'),
            pytest.param(['.', '-se', '.', '..'],
                         (['.', '.', '..'], None, None, False, True, False, False, None, None, None, None, None),
                         id='. -se . ..'),
            pytest.param(['-s*', '.',  '--sgkey', 'my key', '--sgid', 'my id'],
                         (['.'], None, None, True, True, True, True, None, None, None, None, None),
                         id='-s* . …'),
        )
    )
    def test_parse_args_more(self, args, ret_expect):
        """only compare expected return values that are not None"""
        ret = parse_args_opts(args=args)
        for i in range(len(ret_expect)):
            if ret_expect[i] is None:
                continue
            assert ret[i] == ret_expect[i]



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
            # m4a
            pytest.param('_.m4a', '', '', id='m4a "" ""'),
            pytest.param('artist.m4a', 'my artist', '', id='m4a "my artist" ""'),
            pytest.param('album.m4a', '', 'my album', id='m4a "" "my album"'),
            pytest.param('artist album.m4a', 'my artist', 'my album', id='m4a "my artist" "my album"'),
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
        ar, al = get_artist_album[fp.suffix](fp)
        assert ar == ti_ar
        assert al == ti_al

    def test_ogg_as_mp3_fail(self):
        fp = exists_or_skip('_.ogg')
        assert empty_ArtAlb == get_artist_album_mp3(fp)

    def test_ogg_as_wma_fail(self):
        fp = exists_or_skip('_.ogg')
        assert empty_ArtAlb == get_artist_album_asf(fp)

    def test_ogg_as_flac_fail(self):
        fp = exists_or_skip('_.ogg')
        assert empty_ArtAlb == get_artist_album_flac(fp)

    def test_bad_file_suffix(self):
        with pytest.raises(KeyError):
            _ = get_artist_album['foo.bad']
