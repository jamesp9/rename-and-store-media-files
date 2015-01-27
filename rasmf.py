#!/usr/bin/env python3
######################################################################
# Rename and Store Media Files
# Filename: rasmf.py
# Author:   James Pinkster
# Version:  0.04
# For refence see Kodi Wiki
# http://kodi.wiki/view/Naming_video_files/TV_shows#Split-episode
######################################################################
"""Rename video files formats to somthing sensible (i.e. removing whitespaces and brackets)
and then store files in a preferred location.  
In preparation for Kodi(XBMC) to scrape the files and add to library.
"""

import os
import shutil
import re

#media_dir = "/zdata"
media_dir = "/tmp/rasmf"
#dldir = os.path.join(media_dir, "download", "holding")
dldir = os.path.join(media_dir, "download")

movie_dir = os.path.join(media_dir, "movies")
tv_dir = os.path.join(media_dir, "TV")

video_file_extensions = ['avi','divx','wmv', 'mp4', 'mkv', 'mpg', 'm4v']
audio_file_extensions = ['flac','mp3','ogg']
doc_ext = ['doc','docx','pdf']

directory_deletion_list = []



def pause():
    input("Press any key to continue")


def lower_splitext(filename):
    return os.path.splitext(filename.lower())


def sanitise_string(fname):
    """
    Sanatise a string by removing brackets and using a preferred seperator (e.g. period, underscore or space)
    Currently only returns a string with period as the seperator.
    """

    character_list = [' ', '[', ']', '(', ')', "'", '&', '-.', '..']
    for character in character_list:
        if character in fname:
            if character == '&':
                fname = fname.replace('&', 'and')
            else:
                fname = fname.replace(character,'.')
    fname = re.sub(r'\.$', r'', fname) #remove trailing period
    return fname


def split_on_year(fname):
    """Return the string upto and including a year."""
    fname = re.sub(r'(^.*[0-9][0-9][0-9][0-9]).*', r'\1', fname)
    return fname


def split_on_season(fname):
    """Return the string upto and including the season and episode string(e.g. S01E01)"""
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
    The TV show name is assumed to be the first part of the string up to [sS][0-9]+ taken from
    either the filename of first element of the source directory.
    The TV show name is returned sanitised and title cased.
    """
    # Return the string from left to the character before the first '-' hyphen
    # e.g. "vikings-s01e05" would become "vikings"
    #
    # re.sub(pattern, repl, string, count=0, flags=0)
    # If the pattern isn't found, string is returned unchanged
    #print("first_dir:{}, fname:{}".format(first_dir, fname))
    first_dir = sanitise_string(first_dir)
    first_dir = first_dir.title()
    if re.search(r'^[sS][0-9]+', fname):
        # If the season is at the beginning of the file 
        # Use the containing directory to for the TV show name
        show_name = re.sub(r'(^.*)[-._][sS][0-9]+', r'\1', first_dir)
    else:
        #show_name = re.sub(r'(^.*)-.*$', r'\1',  fname)
        show_name = re.sub(r'(^.*)[-_.][Ss][0-9]+[Ee][0-9]+.*$', r'\1',  fname)
        
    return show_name


def tv_show_name_season(sname, fname):
    """
    Returns a string of form Tv.Show.Name.S01
    """
    season = re.sub(r'^.*([Ss][0-9]+).*$', r'\1', fname)
    sname = sname + '-' + season
    return sname


def process_tv_show_file(source_dir, source_filename, base_tv_dir):
    global dldir
    tv_filename, tv_ext = lower_splitext(source_filename)
    tv_filename = sanitise_string(tv_filename)
    tv_filename = split_on_season(tv_filename)
    tv_filename = tv_filename.title()

    first_relpath = relative_path(source_dir, dldir)
    #print("first_relpath: {}".format(first_relpath))
    show_name = tv_show_name(first_relpath, tv_filename)
    #print("show_name: {}".format(show_name))

    show_season = tv_show_name_season(show_name, tv_filename)
    #print("show_season: {}".format(show_season))

    #print("base_tv_dir: {}".format(base_tv_dir))
    target_dir = os.path.join(base_tv_dir, show_name, show_season)
    #print("target_dir: {}".format(target_dir))

    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)

    source_path = os.path.join(source_dir, source_filename)
    #print("source_path: {}".format(source_path))
    target_path = os.path.join(target_dir, tv_filename + tv_ext)
    #print("target_path: {}".format(target_path))

    #print("TV: ", source_dir, " ==> ", target_dir)
    shutil.move(source_path, target_path)
    
    # afterwards only remove source_dir we have moved files from
    # This helps avoid deleting file unessarily
    directory_deletion_list.append(first_relpath)



if __name__ == "__main__":
    # Create the movie and tv folders should they not exist
    for d in [movie_dir, tv_dir]:
        if not os.path.exists(d):
            os.makedirs(d)

    for rootdir, dirs, files in os.walk(dldir,topdown=False):
        for full_filename in files:
            # test against file extension
            file_extension = os.path.splitext(full_filename)[1]
            file_extension = file_extension.replace('.', '').lower()

            if file_extension in video_file_extensions:
                # Is it a TV show
                if re.search(r'[sS][0-9]+[eE][0-9]+', full_filename):
                    #print("-" * 79)
                    #print("rootdir: {} full_filename: {} tv_dir: {}".format(rootdir, full_filename, tv_dir))
                    process_tv_show_file(rootdir, full_filename, tv_dir)

                # Is it a Movie
                # they often have their year in the middle of the filename
                elif re.search(r'[0-9][0-9][0-9][0-9]', full_filename):
                    movie_filename = sanitise_string(full_filename)
                    movie_filename = split_on_year(movie_filename)
                    movie_filename = movie_filename.title()

                    source_dir = os.path.join(rootdir,full_filename)
                    target_dir = os.path.join(movie_dir, movie_filename)
                    #print("MOVIE: ", source_dir, " ==> ", target_dir)
                    shutil.move(source_dir, target_dir)

                    # afterwards only remove directory we have moved files from
                    # This needs to be tested in case the movie was in the main dldir
                    directory_deletion_list.append(os.path.dirname(rootdir.replace(dldir, '')))



        
    # This needs to be changed, only files that have been processed should be removed
    for del_dir in directory_deletion_list:
        target = os.path.join(dldir, del_dir)
        for rootdir, dirs, files in os.walk(target):
            for full_filename in files:
                filename, file_extension = os.path.splitext(full_filename.lower())
                if file_extension in video_file_extensions or file_extension in audio_file_extensions:
                    continue
                else:
                    #print("Removing Dir: ", target)
                    shutil.rmtree(target)