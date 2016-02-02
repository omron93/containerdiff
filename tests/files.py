#   Container Diff tool - show differences among container images
#
#   Copyright (C) 2015 Marek Skalický mskalick@redhat.com
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
#

""" Show diff in container image files and packages.
"""

import rpm
import os
import difflib
import filecmp
import logging

from os.path import join as pjoin

logger = logging.getLogger(__name__)

class RPM:
    """ This class represents RPM package manager.

    It is also possible to add support to another package mangers. To
    be able to use tests in this module with the new package manager it is
    necessary to implement it as a class which provides functions:
    get_installed_packages and get_unowned_files . Instance of this
    class have to be assigned to "package_manager" variable of this
    module.
    """

    def _get_owned_files(self, root, dbpath="var/lib/rpm"):
        """ Get list files installed by rpms in directory specified by
        root parameter. It checks rpm database to get list of installed
        packages. Path to database in root directory can be set by
        dbpath parameter (by default var/lib/rpm).
        """

        rpm.addMacro("_dbpath", os.path.abspath(pjoin(root, dbpath)))
        ts = rpm.TransactionSet()
        mi = ts.dbMatch()
        filenames = [ hdr['FILENAMES'] for hdr in mi]

        # Expand FILENAMES into one list
        filelist = [filepath.decode("utf-8") for package_files in filenames for filepath in package_files]

        # Do not use directory symlinks in paths.
        # Some packages for example say that own files in /lib and some
        # say in /usr/lib. Often these files are in same location (lib ->
        # usr/lib). In this situation some package says it owns file in
        # /lib but in root the file is under /usr/lib. So in the result
        # list store only path without symbolic links for easier
        # comparison.

        filelist = [os.path.relpath(pjoin(os.path.realpath(pjoin(root, os.path.dirname(filepath))), os.path.basename(filepath)), start=root)[1:] \
                        for filepath in filelist]
        return filelist

    def get_unowned_files(self, root, metadata):
        """ Return the list of files that are listed in metadata dict
        (result from extracting the image) and are not installed by
        rpm packages.
        """

        owned_files = self._get_owned_files(root)
        return list(set(metadata.keys())-set(owned_files))

    def get_installed_packages(self, root, dbpath="var/lib/rpm"):
        """ Return list of installed files. Each element of the list is
        a tuple (<package name>, <version>).
        """

        rpm.addMacro("_dbpath", os.path.abspath(os.path.join(root, dbpath)))
        ts = rpm.TransactionSet()
        mi = ts.dbMatch()

        name_version = [ (hdr['name'].decode("utf-8"), hdr['version'].decode("utf-8")) for hdr in mi]
        return name_version


# Contains the object of package manager class
package_manager = RPM()

def test_packages(output_dir1, output_dir2, verbosity):
    """ Test changes in packages installed by package manager.

    Result contains a dict {"added":.., "removed":.., "modified"}.
    First two keys have list values. These lists contains string
    "<package name>-<version>" for added/removed packages. Key
    "modified" has value according the verbose mode.

    Verbose modes:
    verbose     - "modified" contains tuple
            (<package name>-<old version>,<package name>-<new version>)
    silet       - same as verbose
    supersilent - same as silent + ability to filter values in the dict
    """
    packages1, versions1 = zip(*package_manager.get_installed_packages(output_dir1))
    packages2, versions2 = zip(*package_manager.get_installed_packages(output_dir2))

    # Removed packages - list of strgins "package-version"
    removed = [package+"-"+versions1[packages1.index(package)] for package in list(set(packages1)-set(packages2))]
    # Added packages - list of strings "package-version"
    added = [package+"-"+versions2[packages2.index(package)] for package in list(set(packages2)-set(packages1))]
    # Packages with different versions - list of tuples ("package-oldversion", "package-newversion")
    modified = [(package+"-"+versions1[packages1.index(package)], package+"-"+versions2[packages2.index(package)]) \
                for package in list(set(packages2).intersection(set(packages1))) \
                if versions1[packages1.index(package)] != versions2[packages2.index(package)]]

    return {"added":added, "removed":removed, "modified":modified}

def files_diff(filepath, dirpath1, dirpath2):
    """ Return the diff of file specified by absolute path in two
    chroots specified by two root directories.

    Result is unified diff of the file.
    """
    file1 = os.path.join(dirpath1,filepath[1:])
    file2 = os.path.join(dirpath2,filepath[1:])
    diff = []
    if os.path.isfile(file1) and os.path.isfile(file2):
        try:
            with open(file1, "r") as fd1, open(file2, "r") as fd2:
                diff = list(difflib.unified_diff(fd1.read().splitlines(), fd2.read().splitlines(), fromfile=file1, tofile=file2, lineterm=""))
        except UnicodeDecodeError:
            pass

    return diff

def metadata_diff(filepath, metadata1, metadata2):
    """ Return the differences in metadata for specified file.

    Result is a dict with string keys <name of file property> and it
    value (<value in metadata1>, <value in metadata2>).
    """
    # Find tuples (property, value) in metadata which are not same
    diff = set(metadata1[filepath].items()) ^ set(metadata2[filepath].items())
    # Only tuples ('mtime',...) and ('chksum',...) can be different in file metadata
    diff = list(filter(lambda x: x[0] != "mtime" and x[0] != "chksum", diff))

    result = {}
    for key in diff:
        if isinstance(metadata1[filepath][key[0]], bytes):
            logger.debug(str(key)+"is type of bytes")
            result[key[0]] = (metadata1[filepath][key[0]].decode("utf-8"), metadata2[filepath][key[0]].decode("utf-8"))
        else:
            result[key[0]] = (metadata1[filepath][key[0]], metadata2[filepath][key[0]])

    return result


def test_unowned_files(output_dir1, metadata1, output_dir2, metadata2, verbosity):
    """ Test changes in files that are not installed by package manager.

    Result contains a dict {"added":.., "removed":.., "modified"}.
    First two keys have list values. These lists contains paths to
    added/removed files. Key "modified" has value according the verbose
    mode.

    Verbose modes:
    verbose     - "modified" contains diff of files with changes and its metadata changes
    silet       - "modified" contains only names of added/modified/removed files
    supersilent - same as silent + ability to filter values in the dict
    """
    unowned_files1 = package_manager.get_unowned_files(output_dir1, metadata1)
    unowned_files2 = package_manager.get_unowned_files(output_dir2, metadata2)

    added = [file for file in (set(unowned_files2)-set(unowned_files1))]
    removed = [file for file in (set(unowned_files1)-set(unowned_files2))]
    modified = []
    for file in (set(unowned_files1).intersection(set(unowned_files2))):
        metadata = metadata_diff(file, metadata1, metadata2)
        files = files_diff(file, output_dir1, output_dir2)
        if verbosity >= 3:
            if len(files) != 0 or len(metadata) != 0:
                modified.append((file, files, metadata))
        else:
            modified.append(file)

    return {"added":added, "removed":removed, "modified":modified}



def run(image1, image2, verbosity):
    """ Test files and packages in the image.

    Adds two keys to the output of the diff tool:
    "packages" - see output of "test_packages" function in this module
    "files" - see output of "test_files" function in this module
    """
    ID1, metadata1, output_dir1 = image1
    ID2, metadata2, output_dir2 = image2

    logger.info("Going to test files and packages in the image.")

    result = {}
    result["packages"] = test_packages(output_dir1, output_dir2, verbosity)
    result["files"] = test_unowned_files(output_dir1, metadata1, output_dir2, metadata2, verbosity)
    return result
