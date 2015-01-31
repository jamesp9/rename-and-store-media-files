#!/usr/bin/env python3

import unittest
import os
import shutil
import platform
import logging
import logging.handlers
import inspect
import re
# import time
# import glob

import rasmf


def whoami():
    return inspect.stack()[1][3]  # get name of current function


# Logging
logfile = os.path.join('log', 'test_rasmf.log')
if not os.path.isdir('log'):
    os.mkdir('log')
# Set the logger based on namespace and minimum log level
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Create the FileHandler with Timed Rotating logs and set it's minimum log level
handler = logging.handlers.TimedRotatingFileHandler(logfile, when='midnight')
handler.setLevel(logging.DEBUG)
# Create log formatter
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)


class TestRASMF(unittest.TestCase):
    def setUp(self):
        if platform.system() == 'Windows':
            self.media_dir = os.path.join('c:\\', 'tmp', 'rasmf')
        else:
            self.media_dir = '/tmp/rasmf'

        self.in_dir = os.path.join(self.media_dir, 'incoming')
        self.movie_dir = os.path.join(self.media_dir, "movies")
        self.tv_dir = os.path.join(self.media_dir, "TV")

        # Make sure the test dir is clean
        if os.path.exists(self.media_dir):
            shutil.rmtree(self.media_dir)

        os.makedirs(self.in_dir)
        os.makedirs(self.movie_dir)
        os.makedirs(self.tv_dir)

    # MOVIE
    def test_sanitise_string_movie(self):
        test_data = [
            'barbaric string of junk_2011-dvdrip.xvid-somedude[www.example.com]',
            'the.title.2006.phatdisc.eng-somechick(www.example.com)',
            'noname',
            """my.test.movie (2001) file.has[bracket's & parnthesis]""",
            ]

        observed = []
        expected = [
            'barbaric.string.of.junk_2011-dvdrip.xvid-somedude.www.example.com',
            'the.title.2006.phatdisc.eng-somechick.www.example.com',
            'noname',
            'my.test.movie.2001.file.has.bracket.s.and.parnthesis',
                ]
        for filename in test_data:
            observed.append(rasmf.sanitise_string(filename))

        observed.sort()
        expected.sort()
        self.assertEqual(observed, expected)

    def test_split_on_year_movie(self):
        test_data = [
            'barbaric.string.of.junk_2011-dvdrip.xvid-somedude.www.example.com',
            'the.title-2006.phatdisc.eng-somechick.www.example.com',
            'noname',
            'my.test.movie.2001.file.has.bracket.s.and.parnthesis',
            ]

        observed = []
        expected = [
            'barbaric.string.of.junk_2011',
            'the.title-2006',
            'noname',
            'my.test.movie.2001',
            ]

        for filename in test_data:
            observed.append(rasmf.split_on_year(filename))

        observed.sort()
        expected.sort()
        self.assertEqual(observed, expected)

    # TV
    def test_sanitise_string_tv(self):
        logger.debug("{0} {1} {0}".format('=' * 20, whoami(), ))

        test_data = [
            'space as seperator - s01e03 this is fun[xyz]',
            'underscores_are_the_go_s01e05_this_is_fun[_]',
            's01e01.this.string.will.be.ignored',
            'a.violent.tv.show.s05e08.hdtv.x264-someone',
            'square.brackets.s01e03-[someguy]',
            'parenthesis.s01e04-(someguy)',
            'me & my dog-S01E02-halfbaked',
            """some..other-.stuff'S05E01-and more stuff""",
            ]

        expected = [
            'space.as.seperator.s01e03.this.is.fun.xyz',
            'underscores_are_the_go_s01e05_this_is_fun._',
            's01e01.this.string.will.be.ignored',
            'a.violent.tv.show.s05e08.hdtv.x264-someone',
            'square.brackets.s01e03.someguy',
            'parenthesis.s01e04.someguy',
            'me.and.my.dog-S01E02-halfbaked',
            'some.other.stuff.S05E01-and.more.stuff',
            ]

        observed = []
        for filename in test_data:
            observed_fn = rasmf.sanitise_string(filename)
            logger.debug("   OBSERVED_FN: {}".format(observed_fn))
            observed.append(observed_fn)

        observed.sort()
        expected.sort()
        self.assertEqual(observed, expected)

    def test_split_on_season(self):
        logger.debug("{0} {1} {0}".format('=' * 20, whoami(), ))

        test_data = [
            'my.favorite.tv.show-s01e03.this.is.fun.xxx',
            'my.favorite.tv.show.s01e05.this.is.fun.Xxx',
            'this.string.is.included.s01e01',
            's01e01.this.string.will.be.ignored',
            ]

        expected = [
            'my.favorite.tv.show-s01e03',
            'my.favorite.tv.show.s01e05',
            'this.string.is.included.s01e01',
            's01e01',
            ]

        observed = []
        for filename in test_data:
            observed_fn = rasmf.split_on_season(filename)
            logger.debug("   OBSERVED_FN: {}".format(observed_fn))
            observed.append(observed_fn)

        observed.sort()
        expected.sort()

        self.assertEqual(observed, expected)

    def test_relative_path(self):
        logger.debug("{0} {1} {0}".format('=' * 20, whoami(), ))
        dl_dir = os.path.join(self.media_dir, 'incoming')

        test_data = [
            dl_dir,
            os.path.join(dl_dir, 'Spaces Are Here S01'),
            os.path.join(dl_dir, 'Periods.And.A.Season.Number-S01'),
            os.path.join(dl_dir, 'Space And Square Brackets S05E08 AND Square[brackets]'),
            ]

        observed = []
        expected = [
            '',
            'Spaces Are Here S01',
            'Periods.And.A.Season.Number-S01',
            'Space And Square Brackets S05E08 AND Square[brackets]',
            ]

        for source_dir in test_data:
            observed_fn = rasmf.relative_path(source_dir, dl_dir)
            logger.debug("   OBSERVED_FN: {}".format(observed_fn))
            observed.append(observed_fn)

        observed.sort()
        expected.sort()
        self.assertEqual(observed, expected)

    def test_tv_show_name(self):
        logger.debug("{0} {1} {0}".format('=' * 20, whoami(), ))

        test_data = [
            ('', 'Spaces.Are.Here.S01E01'),
            ('Just.A.Season-S03', 'S03E03'),
            ('No.Season.Here', 'No.Season.Here'),
            ]

        observed = []
        expected = [
            'Spaces.Are.Here',
            'Just.A.Season',
            'No.Season.Here',  # No re.search would match so the original string would be returned
            ]

        for first_relpath, tv_filename in test_data:
            observed_fn = rasmf.tv_show_name(first_relpath, tv_filename)
            logger.debug("   OBSERVED_FN: {}".format(observed_fn))
            observed.append(observed_fn)

        observed.sort()
        expected.sort()
        self.assertEqual(observed, expected)

    def test_tv_show_name_season(self):
        logger.debug("{0} {1} {0}".format('=' * 20, whoami(), ))

        test_data = [
            ('Spaces.Are.Here', 'Spaces.Are.Here.S01E01'),
            ('Just.A.Season', 'S03E03'),
            ('No.Season.Here', 'No.Season.Here'),
            ]

        observed = []
        expected = [
            'Spaces.Are.Here-S01',
            'Just.A.Season-S03',
            'No.Season.Here-No.Season.Here',
            ]

        for show_name, tv_filename in test_data:
            observed_fn = rasmf.tv_show_name_season(show_name, tv_filename)
            logger.debug("   OBSERVED_FN: {}".format(observed_fn))
            observed.append(observed_fn)

        observed.sort()
        expected.sort()
        self.assertEqual(observed, expected)

    def test_process_tv_show_file(self):
        logger.debug("{0} {1} {0}".format('=' * 20, whoami(), ))

        test_data = [
            (os.path.join(self.in_dir, 'My.Favourite.Tv.Show-S01'),
                'My Favourite Tv Show-S01E01.avi', self.tv_dir),
            (self.in_dir, 'My Favourite Tv Show-S01E02.avi', self.tv_dir),
            (os.path.join(self.in_dir, 'A Different Tv Show'),
                'A Different Tv Show-S01E03.avi', self.tv_dir),
            (os.path.join(self.in_dir, 'More Than one dir deep', 'sample'),
                'More Than One Dir Deep-S01E04.avi', self.tv_dir),
            ]

        observed = []
        expected = [
            os.path.join(self.tv_dir, 'My.Favourite.Tv.Show',
                'My.Favourite.Tv.Show-S01', 'My.Favourite.Tv.Show-S01E01.avi'),
            os.path.join(self.tv_dir, 'My.Favourite.Tv.Show',
                'My.Favourite.Tv.Show-S01', 'My.Favourite.Tv.Show-S01E02.avi'),
            os.path.join(self.tv_dir, 'A.Different.Tv.Show',
                'A.Different.Tv.Show-S01', 'A.Different.Tv.Show-S01E03.avi'),
            os.path.join(self.tv_dir, 'More.Than.One.Dir.Deep',
                'More.Than.One.Dir.Deep-S01', 'More.Than.One.Dir.Deep-S01E04.avi'),
            ]

        # Create test files
        for p1, fn, ptv in test_data:
            os.makedirs(p1, exist_ok=True)
            with open(os.path.join(p1, fn), 'w') as fo:
                fo.write(p1 + fn + ptv)

        # rasmf.pause()

        # Run the main tv function on test files
        for rootdir, dirs, files in os.walk(self.in_dir, topdown=False):
            for full_filename in files:
                # test against file extension
                file_extension = os.path.splitext(full_filename)[1]
                file_extension = file_extension.replace('.', '').lower()

                if file_extension in rasmf.video_file_extensions:
                    # Is it a TV show
                    if re.search(r'[sS][0-9]+[eE][0-9]+', full_filename):
                        rasmf.process_tv_show_file(rootdir, full_filename, self.tv_dir)

        # rasmf.pause()

        # Observe which files are stored in the tv media dir
        for root, dirs, files in os.walk(self.tv_dir, topdown=False):
            for f in files:
                logger.debug("   observed: {} {}".format(root, f))
                observed.append(os.path.join(root, f))

        observed.sort()
        expected.sort()
        self.assertEqual(observed, expected)

    def test_clean_up(self):
        pass

    def tearDown(self):
        shutil.rmtree(self.media_dir)


if __name__ == "__main__":
    unittest.main()
