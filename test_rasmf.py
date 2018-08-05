#!/usr/bin/env python3

import unittest
import os
import shutil
import platform
import logging
import inspect
import re

import rasmf


def whoami():
    return inspect.stack()[1][3]  # get name of current function


class TestRASMF(unittest.TestCase):

    test_config_fn = 'config_test.ini'

    def setUp(self):
        """
        """
        # Make a test config file
        shutil.copy('config_example.ini', self.test_config_fn)
        self.config = rasmf.read_config(self.test_config_fn)

        # Modify the config to use testing paths
        if platform.system() == 'Windows':
            base_dir = os.path.join('C:\\', 'tmp', 'rasmf')
        else:
            base_dir = '/tmp/rasmf'

        self.config['folders']['incoming_dir'] = os.path.join(
            base_dir, 'incoming')
        self.config['folders']['media_dir'] = os.path.join(base_dir, 'media')
        self.config['folders']['movie_dir'] = os.path.join(
            base_dir, 'media', 'movie')
        self.config['folders']['tv_dir'] = os.path.join(
            base_dir, 'media', 'tv')
        self.config['folders']['log_dir'] = os.path.join(base_dir, 'log')

        self.in_dir = self.config['folders']['incoming_dir']
        self.media_dir = self.config['folders']['media_dir']
        self.movie_dir = self.config['folders']['movie_dir']
        self.tv_dir = self.config['folders']['tv_dir']

        # Write the config as rasmf will read config from here.
        with open(self.test_config_fn, 'w') as configfile:
            self.config.write(configfile)

        # Make sure the test dir is clean
        if os.path.exists(base_dir):
            shutil.rmtree(base_dir)

        for folder in self.config['folders'].keys():
            os.makedirs(self.config['folders'][folder])

    def test_sanitise_string_movie(self):
        """
        Test Sanitisation of a movie filename.
        """
        test_data = [
            'barbaric string of junk_2011-dvdrip.xvid-somedude[www.example.com]',
            'the.title.2006.phatdisc.eng-thatchick(www.example.com)',
            'noname',
            """my.test.movie (2001) file.has[bracket's & parnthesis]""",
        ]

        observed = []
        expected = [
            'barbaric.string.of.junk_2011-dvdrip.xvid-somedude.www.example.com',
            'the.title.2006.phatdisc.eng-thatchick.www.example.com',
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
            'the.title-2006.phatdisc.eng-thatchick.www.example.com',
            'noname',
            'my.test.movie.2001.file.has.bracket.s.and.parnthesis',
            '1984-1984',
            '2015.more.title.as.string-1984.some.other.junk',
            'string.in.front.2015.more.title.as.string.1984.some.other.junk',
        ]

        observed = []
        expected = [
            'barbaric.string.of.junk_2011',
            'the.title-2006',
            'noname',
            'my.test.movie.2001',
            '1984-1984',
            '2015.more.title.as.string-1984',
            'string.in.front.2015.more.title.as.string.1984',
        ]

        for filename in test_data:
            observed.append(rasmf.split_on_year(filename))

        observed.sort()
        expected.sort()
        self.assertEqual(observed, expected)

    # TV
    def test_sanitise_string_tv(self):
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
            observed.append(observed_fn)

        observed.sort()
        expected.sort()
        self.assertEqual(observed, expected)

    def test_split_on_season_tv(self):
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
            observed.append(observed_fn)

        observed.sort()
        expected.sort()

        self.assertEqual(observed, expected)

    def test_relative_path_tv(self):
        dl_dir = os.path.join(self.media_dir, 'incoming')

        test_data = [
            dl_dir,
            os.path.join(dl_dir, 'Spaces Are Here S01'),
            os.path.join(dl_dir, 'Periods.And.A.Season.Number-S01'),
            os.path.join(
                dl_dir,
                'Space And Square Brackets S05E08 AND Square[brackets]'),
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
            observed.append(observed_fn)

        observed.sort()
        expected.sort()
        self.assertEqual(observed, expected)

    def test_tv_show_name(self):
        test_data = [
            ('', 'Spaces.Are.Here.S01E01'),
            ('Just.A.Season-S03', 'S03E03'),
            ('No.Season.Here', 'No.Season.Here'),
        ]

        observed = []
        expected = [
            'Spaces.Are.Here',
            'Just.A.Season',
            # No re.search would match so the original string would be returned
            'No.Season.Here',
        ]

        for first_relpath, tv_filename in test_data:
            observed_fn = rasmf.tv_show_name(first_relpath, tv_filename)
            observed.append(observed_fn)

        observed.sort()
        expected.sort()
        self.assertEqual(observed, expected)

    def test_tv_show_name_season(self):
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
            observed.append(observed_fn)

        observed.sort()
        expected.sort()
        self.assertEqual(observed, expected)

    def test_process_tv_show_file(self):
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
            os.path.join(
                self.tv_dir,
                'My.Favourite.Tv.Show',
                'My.Favourite.Tv.Show-S01',
                'My.Favourite.Tv.Show-S01E01.avi'),
            os.path.join(
                self.tv_dir,
                'My.Favourite.Tv.Show',
                'My.Favourite.Tv.Show-S01',
                'My.Favourite.Tv.Show-S01E02.avi'),
            os.path.join(
                self.tv_dir,
                'A.Different.Tv.Show',
                'A.Different.Tv.Show-S01',
                'A.Different.Tv.Show-S01E03.avi'),
            os.path.join(
                self.tv_dir,
                'More.Than.One.Dir.Deep',
                'More.Than.One.Dir.Deep-S01',
                'More.Than.One.Dir.Deep-S01E04.avi'),
        ]

        # Create test files
        for p1, fn, ptv in test_data:
            os.makedirs(p1, exist_ok=True)
            with open(os.path.join(p1, fn), 'w') as fo:
                fo.write(p1 + fn + ptv)

        # Run the main tv function on test files
        for rootdir, dirs, files in os.walk(self.in_dir, topdown=False):
            for full_filename in files:
                # test against file extension
                file_extension = os.path.splitext(full_filename)[1]
                file_extension = file_extension.replace('.', '').lower()

                if file_extension in self.config['file_extensions']['video']:
                    # Is it a TV show
                    if re.search(r'[sS][0-9]+[eE][0-9]+', full_filename):
                        rasmf.process_tv_show_file(
                            rootdir, full_filename, self.tv_dir)

        # Observe which files are stored in the tv media dir
        for root, dirs, files in os.walk(self.tv_dir, topdown=False):
            for f in files:
                observed.append(os.path.join(root, f))

        observed.sort()
        expected.sort()
        self.assertEqual(observed, expected)

    def test_clean_up_tv(self):
        """
        """
        logger = logging.getLogger('rasmf')
        test_data = [
            ('Empty.Folder.Tv.Show-S01', ''),
            ('Empty.Folder.Tv.Show-S02', ''),
            ('Folder With A File-S01', 'the offending file.pdf'),
            (os.path.join('More Than one dir deep', 'sample'), ''),
            ('', ''),
        ]
        test_list = [
            'Empty.Folder.Tv.Show-S01',
            'Empty.Folder.Tv.Show-S02',
            'Folder With A File-S01',
            'More Than one dir deep', ]

        observed = []
        expected = ['Folder With A File-S01', ]

        # Create test directories and files
        for path_1, filename in test_data:
            abs_path = os.path.join(self.in_dir, path_1)
            os.makedirs(abs_path, exist_ok=True)

            if filename:
                abs_filename_path = os.path.join(abs_path, filename)
                logger.debug("Writing file: {}".format(abs_filename_path))
                with open(os.path.join(abs_path, filename), 'w') as fo:
                    fo.write(path_1 + filename)

        rasmf.clean_up(self.config, test_list)

        for incoming in os.listdir(self.in_dir):
            logger.debug("Observed: {}".format(incoming))
            if os.path.isdir(os.path.join(self.in_dir, incoming)):
                observed.append(incoming)

        observed.sort()
        logger.debug("observed: {}".format(observed))
        expected.sort()
        logger.debug("expected: {}".format(expected))
        self.assertEqual(observed, expected)

    def tearDown(self):
        shutil.rmtree(self.media_dir)
        os.remove(self.test_config_fn)


if __name__ == "__main__":
    rasmf.logging_config('DEBUG')
    test_logger = logging.getLogger('rasmf')
    test_logger.info("\n")
    test_logger.info("{0} Starting tests {0}".format("*" * 30))
    unittest.main()
