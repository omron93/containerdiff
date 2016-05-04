#   ContainerDiff - tool to show differences among container images
#
#   Copyright (C) 2016 Marek Skalicky mskalick@redhat.com
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
#   along with containerdiff.  If not, see <http://www.gnu.org/licenses/>.
#

""" Show diff in container image files and packages.
"""

import os
import difflib
import logging
import magic
import docker
import tempfile
import shutil

import containerdiff

logger = logging.getLogger(__name__)

def get_output_from_container(image, command):
    logger.info("Running '%s' in image '%s'", command, image)
    cli = docker.AutoVersionClient(base_url = containerdiff.docker_socket)

    volume_dir = tempfile.mkdtemp(dir="/tmp")
    logger.debug("Container output volume: %s", volume_dir)

    container=cli.create_container(image, volumes=[volume_dir],
            host_config=cli.create_host_config(binds=[volume_dir+":/mnt/containerdiff-volume:Z"]),
            command="/bin/sh -c 'set -m; touch /mnt/containerdiff-volume/output; chmod a+rw /mnt/containerdiff-volume/output; exec 1>/mnt/containerdiff-volume/output; "+command+"'",
            user=os.geteuid())

    cli.start(container);
    error = cli.logs(container)
    if error != b'':
        logger.error(error)

    cli.stop(container)
    cli.remove_container(container)

    output = open(os.path.join(volume_dir, "output")).read()

    shutil.rmtree(volume_dir, ignore_errors=True)

    return output


class RPM:
    """ This class represents RPM package manager.

    It is also possible to add support to another package mangers. To
    be able to use tests in this module with the new package manager it is
    necessary to implement it as a class which provides functions:
    get_installed_packages and get_unowned_files . Instance of this
    class have to be assigned to "package_manager" variable of this
    module.
    """

    def _get_owned_files(self, ID, root):
        """ Get list files installed by rpms in image 'ID' which is
        expanded into 'root'. It runs 'rpm -qal' command in the image
        and removes symbolic links in directories in the result.
        """
        # Some RPM package does not contain file, so rpm prints
        # '(contains no files)' string.
        filelist = get_output_from_container(ID, "rpm -qal | grep -v \(contains\ no\ files\)").split('\n')

        # Do not use directory symlinks in paths.
        # Some packages for example say that own files in /lib and some
        # say in /usr/lib. Often these files are in same location (lib ->
        # usr/lib). In this situation some package says it owns file in
        # /lib but in root the file is under /usr/lib. So in the result
        # list store only path without symbolic links for easier
        # comparison.

        filelist = [os.sep.join(["",os.path.relpath(os.path.realpath(os.sep.join([root, os.path.dirname(filepath)])), start=root), os.path.basename(filepath)]) \
                        for filepath in filelist]
        return filelist

    def get_unowned_files(self, ID, metadata, root):
        """ Return the list of files that are listed in metadata dict
        (result from extracting the image) and are not installed by
        rpm packages.
        """

        owned_files = self._get_owned_files(ID, root)
        return list(set(metadata.keys())-set(owned_files))

    def get_installed_packages(self, ID):
        """ Return list of installed files. Each element of the list is
        a tuple (<package name>, <version>).
        """
        packages = get_output_from_container(ID, "rpm -qa").split()

        name_version = []
        for package in packages:
            elements = package.split("-")
            name_version.append(("-".join(elements[:-2]), "-".join(elements[-2:])))
        return name_version


# Contains the object of package manager class
package_manager = RPM()

def test_packages(ID1, ID2, silent):
    """ Test changes in packages installed by package manager.

    Result contains a dict {"added":.., "removed":.., "modified"}. Each
    key has a list value. Values for first two keys contain tuples
    ("<package_name>,<version>") for added/removed packages. Key
    "modified" contains tuples (<package_name>, <old_version>,
    <new_version>).
    """
    packages1, versions1 = zip(*package_manager.get_installed_packages(ID1))
    packages2, versions2 = zip(*package_manager.get_installed_packages(ID2))

    # Removed packages - list of strgins "package-version"
    removed = [(package, versions1[packages1.index(package)]) for package in list(set(packages1)-set(packages2))]
    # Added packages - list of strings "package-version"
    added = [(package, versions2[packages2.index(package)]) for package in list(set(packages2)-set(packages1))]
    # Packages with different versions - list of tuples ("package-oldversion", "package-newversion")
    modified = [(package, versions1[packages1.index(package)], versions2[packages2.index(package)]) \
                for package in list(set(packages2).intersection(set(packages1))) \
                if versions1[packages1.index(package)] != versions2[packages2.index(package)]]

    return {"added":added, "removed":removed, "modified":modified}

def files_diff(filepath, dirpath1, dirpath2):
    """ Return the diff of file specified by absolute path in two
    chroots specified by two root directories.

    Result is unified diff of the file.
    """
    file1 = os.path.normpath(os.sep.join([dirpath1,filepath]))
    file2 = os.path.normpath(os.sep.join([dirpath2,filepath]))
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
            logger.debug("%s is type of bytes", str(key))
            result[key[0]] = (metadata1[filepath][key[0]].decode("utf-8"), metadata2[filepath][key[0]].decode("utf-8"))
        else:
            result[key[0]] = (metadata1[filepath][key[0]], metadata2[filepath][key[0]])

    return result


def test_unowned_files(ID1, output_dir1, metadata1, ID2, output_dir2, metadata2, silent):
    """ Test changes in files that are not installed by package manager.

    Result contains a dict {"added":.., "removed":.., "modified"}. Key
    values are lists. Firt two values contain paths to added/removed
    files. Key "modified" by default contains path to file, file type,
    file diff and file metadata changes. So list contains tuples
      (file_path, file_type, file_diff, file_metadatadiff)

    In silent mode, key "modified" contains only file paths.
    """
    unowned_files1 = package_manager.get_unowned_files(ID1, metadata1, output_dir1)
    unowned_files2 = package_manager.get_unowned_files(ID2, metadata2, output_dir2)

    mime_loader = magic.open(magic.MAGIC_MIME)
    mime_loader.load()

    added = []
    for filepath in (set(unowned_files2)-set(unowned_files1)):
        mime = mime_loader.file(os.path.normpath(os.sep.join([output_dir2,filepath])))
        added.append((filepath, mime))
    removed = []
    for filepath in (set(unowned_files1)-set(unowned_files2)):
        mime = mime_loader.file(os.path.normpath(os.sep.join([output_dir1,filepath])))
        removed.append((filepath, mime))
    modified = []
    for filepath in (set(unowned_files1).intersection(set(unowned_files2))):
        metadata = metadata_diff(filepath, metadata1, metadata2)
        diff = files_diff(filepath, output_dir1, output_dir2)
        mime_new = mime_loader.file(os.path.normpath(os.sep.join([output_dir2,filepath])))

        if silent:
            if len(diff) != 0 or len(metadata) != 0:
                modified.append((filepath, mime_new))
        else:
            if len(diff) != 0 or len(metadata) != 0:
                modified.append((filepath, mime_new, diff, metadata))

    return {"added":added, "removed":removed, "modified":modified}



def run(image1, image2, silent):
    """ Test files and packages in the image.

    Adds two keys to the output of the diff tool:
    "packages" - see output of "test_packages" function in this module
    "files" - see output of "test_files" function in this module
    """
    ID1, metadata1, output_dir1 = image1
    ID2, metadata2, output_dir2 = image2

    logger.info("Testing files and packages in the image")

    result = {}
    result["packages"] = test_packages(ID1, ID2, silent)
    result["files"] = test_unowned_files(ID1, output_dir1, metadata1, ID2, output_dir2, metadata2, silent)
    return result
