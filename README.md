CoverLovin2
===========

*coverlovin2* is a Python script for automating downloading album cover art
images.  A common use-case is creating a "folder.jpg" file for a
collection of ripped Compact Disc albums.

coverlovin2 can only be run by python version 3.7 (or greater).

Script Usage
------------

    usage: coverlovin2.py [-h] [-n IMAGE_NAME] [-i {jpg,png,gif}] [-o] [-s*] [-sl]
                          [-sm] [-sg] [-s {small,medium,large}] [--gid GID]
                          [--gkey GKEY] [-r REFERER] [-d] [--test-only]
                          DIRS [DIRS ...]
    
    Given a list of directories, DIRS, recursively identify "album" directories.
    "Album" directories have audio files, e.g. files with extensions like .mp3 or
    .flac.  For each "album" directory, attempt to determine the Artist and Album.
    Then find an album image file using the requested --search providers.  If an
    album image file is found then write it to IMAGE_NAME.TYPE within each
    "album" directory.
    
    A common use-case would be creating a "folder.jpg" file for a collection of
    ripped Compact Disc albums.
    
    Audio files supported are .mp3, .m4a, .mp4, .flac, .ogg, .wma, .asf.
    
    optional arguments:
      -h, --help            show this help message and exit
    
    Required Arguments:
      DIRS                  directories to scan for audio files (Required)
    
    Recommended:
      -n IMAGE_NAME, --image-name IMAGE_NAME
                            cover image file name. This is the file name that will
                            be created within passed DIRS. This will be appended
                            with the preferred image TYPE, e.g. "jpg", "png", etc.
                            (default: "cover")
      -i {jpg,png,gif}, --image-type {jpg,png,gif}
                            image format TYPE (default: "jpg")
      -o, --overwrite       overwrite any previous file of the same file
                            IMAGE_NAME and image TYPE (default: False)
    
    Search all:
      -s*, --search-all     Search for album images using all methods and services
    
    Search the local directory for likely album cover images:
      -sl, --search-likely-cover
                            For any directory with audio media files but no file
                            "NAME.TYPE", search the directory for files that are
                            likely album cover images. For example, given options:
                            --name "cover" --type "jpg", and a directory of .mp3
                            files with a file "album.jpg", it is reasonable to
                            guess "album.jpg" is a an album cover image file. So
                            copy file "album.jpg" to "cover.jpg" . This will skip
                            an internet image lookup and download and could be a
                            more reliable way to retrieve the correct image.
                            (default: False)
    
    Search Musicbrainz NGS webservice:
      -sm, --search-musicbrainz
                            Search for album images using musicbrainz NGS
                            webservice. Requires python module musicbrainzngs. See
                            https://musicbrainz.org/doc/Developer_Resources
                            MusicBrainz lookup is the most reliable search method.
    
    Search Google Custom Search Engine (CSE):
      -sg, --search-googlecse
                            Search for album images using Google CSE. Using the
                            Google CSE requires an Engine ID and API Key. Google
                            CSE reliability entirely depends upon the added "Sites
                            to search". The end of this help message has more
                            advice around using Google CSE. (default: False)
      -s {small,medium,large}, --gsize {small,medium,large}
                            Google CSE optional image file size (default: "large")
      --gid GID             Google CSE Search Engine ID (URL parameter "cx")
                            typically looks like
                            "009494817879853929660:efj39xwwkng". REQUIRED to use
                            Google CSE.
      --gkey GKEY           Google CSE Search Engine API Key (URL parameter "key")
                            typically looks like
                            "KVEIA49cnkwoaaKZKGX_OSIxhatybxc9kd59Dst". REQUIRED to
                            use Google CSE.
    
    Debugging and Miscellanea:
      -r REFERER, --referer REFERER
                            Referer url used in HTTP GET requests (default:
                            "https://github.com/jtmoon79/coverlovin2")
      -d, --debug           Print debug logs (default: False)
      --test-only           Only test, do not write any files (default: False)
    
    This program attempts to create album cover image files for the passed DIRS.  It
    does this several ways, searching for album cover image files already present in
    the directory.  If not found, it attempts to figure out the Artist and Album for
    that directory then searches online services for an album cover image.
    Directories are searched recursively.  Any directory that contains one or more
    with file name extension .mp3 or .m4a or .mp4 or .flac or .ogg or .wma or .asf
    is presumed to be an album directory.  Given a directory of such files, file
    contents will be read for the Artist name and Album name using embedded audio
    tags (ID3, Windows Media, etc.).  If no embedded media tags are present then a
    reasonable guess will be made about the Artist and Album based on the directory
    name; specifically this will try to match a directory name with a pattern like
    "Artist - Year - Album" or "Artist - Album".
    
    If option --search-googlecse is chosen then you must create your Google Custom
    Search Engine (CSE).  This can be setup at https://cse.google.com/cse/all .  It
    takes about 5 minutes.  This is where your own values for --gid and --gkey can
    be created.
    Google CSE settings must have "Image search" as "ON"  and "Search the entire
    web" as "OFF".
    
    Inspired by the program coverlovin.

Installation
------------

* Using `pip` from source:
  
      pip install https://github.com/jtmoon79/coverlovin2/archive/master.zip

* Within a python virtual environment using `pipenv`:

      pipenv shell
      pipenv install https://github.com/jtmoon79/coverlovin2/archive/master.zip

*coverlovin2* uses non-standard libraries [mutagen](https://pypi.org/project/mutagen/)
and [musicbrainzngs](https://pypi.org/project/musicbrainzngs/).

Development
-----------

Install `pipenv`.

Clone the repository:

    git clone git@github.com:jtmoon79/coverlovin2.git

Start the python virtual environment and install the dependencies:

    cd coverlovin2
    pipenv shell
    pipenv install --dev

This will install more non-standard libraries. See the [Pipfile](./Pipfile).

Other Miscellaneous Notes
-------------------------

coverlovin2 is inspired by [coverlovin](https://github.com/amorphic/coverlovin).

coverlovin2 could be used as a module.

coverlovin2 is also for sake of the author learning more about recent changes
in the Python Universe.

coverlovin2 is very type-hinted code and could be even more so. The author
thinks type-hinting is a good idea but it still needs improvement. In it's
current form in Python 3.7, it feels clumsy and can be difficult to grok. Also,
PyCharm and mypy seem to catch different type-hint warnings. 

#### run phases


coverlovin2 runs in a few phases:

1. recursively search passed directory paths for "album" directories. An "album"
directory merely holds audio files of type `.mp3`, `.m4a`, `.mp4`, `.flac`,
`.ogg`, `.wma`, or `.asf`. (see [`coverlovin2/coverlovin2.py::AUDIO_TYPES`](./coverlovin2/coverlovin2.py)).
2. employ a few techniques for determining the artist and album for that
directory.  The most reliable technique is to read available embedded audio tags
within the directory. (see [`coverlovin2/coverlovin2.py::process_dir`](./coverlovin2/coverlovin2.py))
3. using user-passed search options, search for the album cover art image file.
4. if found, create that image file into the "album" directory. The name and
type of image (`.jpg`, `.png`, `.gif`) is based on user-passed options.