#!/usr/bin/env python3
"""
Rename filenames of video format files to clean them up by removing whitespace
and brackets and characters that may cause problems in the shell.
Then store files in a preferred location.
Can be used with Kodi(XBMC) before it scrapes the files and adds content to
library.

See Kodi Wiki for naming for video files
http://kodi.wiki/view/Naming_video_files/TV_shows
"""

import configparser
import inspect
import logging
import logging.handlers
import os
import re
import shutil
import sys

clean_up_list = []


def pause():
    input("Press any key to continue")


def logging_config(log_level='INFO', log_dir=None):
    """
    Configure logging, setup a file handler and a console handler.
    """
    if not log_dir:
        log_dir = os.path.join(os.path.expanduser('~'), 'log')
    logfile = os.path.join(log_dir, 'rasmf.log')

    if not os.path.isdir(log_dir):
        os.mkdir(log_dir)

    # Set the logger based on namespace and minimum log level
    logger = logging.getLogger('rasmf')
    logger.setLevel(logging.getLevelName(log_level))

    # FileHandler with Timed Rotating logs and set it's minimum log level
    file_handler = logging.handlers.TimedRotatingFileHandler(
        logfile, when='midnight')
    file_handler.setLevel(logging.getLevelName(log_level))

    # Create console handler with a higher log level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create file handler formatter
    file_formatter = logging.Formatter('%(asctime)s:%(levelname)s: %(message)s')
    file_handler.setFormatter(file_formatter)

    # Create console handler formatter
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def lower_splitext(filename):
    """
    Returns a tuple of filename and extension in lowercase.
    """
    return os.path.splitext(filename.lower())


def function_name():
    """
    """
    return inspect.stack()[1][3]  # get name of current function


def sanitise_string(fname):
    """
    Sanitise a string by removing brackets and using a preferred separator
    (e.g. period, underscore or space)
    Currently only returns a string with period as the separator.
    """

    character_list = [' ', '[', ']', '(', ')', "'", '&', '-.', '..']
    for character in character_list:
        if character in fname:
            if character == '&':
                fname = fname.replace('&', 'and')
            else:
                fname = fname.replace(character, '.')
    fname = re.sub(r'\.$', r'', fname)  # remove trailing period
    return fname


def split_on_year(fname):
    """Return the string upto and including a year."""
    fname = re.sub(r'(^.*[0-9][0-9][0-9][0-9]).*', r'\1', fname)
    return fname


def split_on_season(fname):
    """Return the string upto and including the season and episode string
    (e.g. S01E01)
    """
    fname = re.sub(r'(^.*[sS][0-9]+[eE][0-9]+).*$', r'\1', fname)
    return fname


def relative_path(full_path, base_path):
    """
    Returns the first directory of the path relative to source directory.
    An empty string is returned if there is no relative path.
    Used for deleting directories that held the incoming files.
    """
    relpath = os.path.relpath(full_path, start=base_path)
    if relpath == '.':
        return ''
    else:
        path_list = relpath.split(os.sep)
        return path_list[0]


def tv_show_name(first_dir, fname):
    """
    The TV show name is assumed to be the first part of the string
    up to [sS][0-9]+ taken from either the filename or the
    first element of the source directory.
    The TV show name is returned sanitised and title cased.
    """
    # re.sub NOTE: If pattern isn't found, string is returned unchanged
    first_dir = sanitise_string(first_dir)
    first_dir = first_dir.title()
    if re.search(r'^[sS][0-9]+', fname):
        # If the season is at the beginning of the file
        # Use the containing directory for the TV show name
        show_name = re.sub(r'(^.*)[-._][sS][0-9]+', r'\1', first_dir)
    else:
        show_name = re.sub(r'(^.*)[-_.][Ss][0-9]+[Ee][0-9]+.*$', r'\1',  fname)

    return show_name


def tv_show_name_season(sname, fname):
    """
    Returns a string of form Tv.Show.Name.S01
    """
    season = re.sub(r'^.*([Ss][0-9]+).*$', r'\1', fname)
    sname = sname + '-' + season
    return sname


def video_file(rootdir, full_filename, file_extension):
    """
    Determine if the video file is a TV show or movie by applying some regexs.
    """
    global clean_up_list

    logger = logging.getLogger('rasmf')

    config = read_config()
    movie_dir = config['folders']['movie_dir']
    tv_dir = config['folders']['tv_dir']

    # Is it a TV show
    if re.search(r'[sS][0-9]+[eE][0-9]+', full_filename):
        logger.debug("TV Show:{0}".format(full_filename))
        clean_up_item = process_tv_show_file(
            rootdir, full_filename, tv_dir)

        if clean_up_item:
            clean_up_list.append(clean_up_item)

    # Is it a Movie
    # assumes the release year is at the end of the title
    elif re.search(r'[0-9][0-9][0-9][0-9]', full_filename):
        logger.debug("Movie: {0}".format(full_filename))
        clean_up_item = process_movie_file(
            rootdir, full_filename, file_extension, movie_dir)

        if clean_up_item:
            clean_up_list.append(clean_up_item)


def process_tv_show_file(source_dir, source_filename, base_tv_dir):
    """
    """
    config = read_config()
    in_dir = config['folders']['incoming_dir']

    logger = logging.getLogger('rasmf')
    logger.debug("{0} {1} {0}".format('=' * 20, function_name(), ))

    tv_filename, file_extension = lower_splitext(source_filename)
    tv_filename = sanitise_string(tv_filename)
    tv_filename = split_on_season(tv_filename)
    tv_filename = tv_filename.title()

    first_relpath = relative_path(source_dir, in_dir)
    show_name = tv_show_name(first_relpath, tv_filename)

    show_season = tv_show_name_season(show_name, tv_filename)

    target_dir = os.path.join(base_tv_dir, show_name, show_season)

    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)

    source_path = os.path.join(source_dir, source_filename)
    target_path = os.path.join(target_dir, tv_filename + file_extension)

    try:
        shutil.move(source_path, target_path)
        logger.info("TV: {0}".format(target_path))
        return first_relpath
    except OSError as msg:
        logger.error("{}: Unable to move {} to {}".format(
            msg,
            source_path,
            target_path))
        return None


def process_movie_file(source_dir, source_filename,
                       file_extension, base_movie_dir):
    config = read_config()
    in_dir = config['folders']['incoming_dir']

    logger = logging.getLogger('rasmf')
    logger.debug("{0} {1} {0}".format('=' * 20, function_name(), ))

    movie_filename = sanitise_string(source_filename)
    movie_filename = split_on_year(movie_filename)
    movie_filename = movie_filename.title() + '.' + file_extension

    source_path = os.path.join(source_dir, source_filename)
    target_path = os.path.join(base_movie_dir, movie_filename)

    first_relpath = relative_path(source_dir, in_dir)

    try:
        shutil.move(source_path, target_path)
        logger.info("Movie: {0}".format(target_path))
        return first_relpath
    except OSError as msg:
        logger.error("{}: Unable to move {} to {}".format(
            msg,
            source_path,
            target_path))
        return None


def clean_up(config, list_of_dirs):
    """
    This function removes any empty directories or directories with unwanted
    files left behind.
    """
    in_dir = config['folders']['incoming_dir']
    video_file_extensions = config['file_extensions']['video']
    audio_file_extensions = config['file_extensions']['audio']
    doc_extensions = config['file_extensions']['doc']
    other_extensions = config['file_extensions']['other']

    logger = logging.getLogger('rasmf')
    logger.debug("{0} {1} {0}".format('=' * 20, function_name(), ))
    logger.debug("list_of_dirs: {}".format(list_of_dirs))

    # Remove duplicates from list
    clean_list = list(set(list_of_dirs))
    logger.debug("clean_list: {}".format(clean_list))

    for first_level_dir in clean_list:
        logger.info("First level directory: {}".format(first_level_dir))
        if first_level_dir:
            del_target = os.path.normpath(os.path.join(in_dir, first_level_dir))

        dir_can_be_deleted = False

        dir_listing = os.listdir(del_target)
        if len(dir_listing) == 0:
            logger.info(" Empty directory: {}".format(del_target))
            dir_can_be_deleted = True
        else:
            # Check this dir for files
            for rootdir, dirs, files in os.walk(del_target, topdown=False):
                logger.debug("{} {} {}".format(rootdir, dirs, files))
                if files:
                    for full_filename in files:
                        logger.debug(" dir:{} fn:{}".format(
                            rootdir,
                            full_filename))
                        filename, file_extension = os.path.splitext(
                            full_filename.lower())
                        # Skip known filetypes that still exist, just in case
                        if (file_extension in video_file_extensions or
                                file_extension in audio_file_extensions or
                                file_extension in doc_extensions or
                                file_extension in other_extensions):
                            dir_can_be_deleted = False
                else:
                    dir_can_be_deleted = True

        if dir_can_be_deleted:
            if os.path.exists(del_target):
                logger.info(" Removing directory: {}".format(del_target))
                shutil.rmtree(del_target)


def read_config(config_fn='config.ini', example_config_fn='config_example.ini'):
    """
    Read the config.ini file otherwise pass a different config filename.
    Expects user to create a config file based off the template config.
    """
    logger = logging.getLogger('rasmf')

    if not os.path.exists(config_fn):
        logger.error('{0} Does not exist'.format(config_fn))
        logger.warning('Copying {0} ==> {1}'.format(example_config_fn, config_fn))
        shutil.copy(example_config_fn, config_fn)
        logger.warning('NOTE: You must modify {0} before re-running.'.format(config_fn))
        logger.warning('Exiting.....')
        sys.exit(1)

    config = configparser.ConfigParser()

    config.read(config_fn)
    return config


def main():
    """
    """
    config = read_config()

    logging_config(
        log_level=config['options']['log_level'],
        log_dir=config['folders']['log_dir'])
    # logger = logging.getLogger('rasmf')

    # Create the movie and tv folders should they not exist
    for d in [config['folders']['movie_dir'], config['folders']['tv_dir']]:
        if not os.path.exists(d):
            os.makedirs(d)

    for rootdir, dirs, files in os.walk(config['folders']['incoming_dir'],
                                        topdown=False):
        for full_filename in files:
            # get lowercase file extension
            file_extension = os.path.splitext(full_filename)[1]
            file_extension = file_extension.replace('.', '').lower()

            if file_extension in config['file_extensions']['video']:
                video_file(rootdir, full_filename, file_extension)

    # Last step clean up the incoming directory
    clean_up(config, clean_up_list)


if __name__ == "__main__":
    main()
