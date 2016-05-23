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

"""Show diff in container image files."""

import os
import difflib
import logging
import magic
import logging
import tarfile

import containerdiff
import containerdiff.package_managers

logger = logging.getLogger(__name__)

# Contains the object of package manager class
package_manager = containerdiff.package_managers.RPM()

def files_diff(filepath, dirpath1, dirpath2):
    """Return the diff of file specified by absolute path in two
    chroots specified by two root directories.

    Returns unified diff of the file.
    """
    file1 = os.path.normpath(os.sep.join([dirpath1,filepath]))
    file2 = os.path.normpath(os.sep.join([dirpath2,filepath]))
    diff = []
    if os.path.isfile(file1) and os.path.isfile(file2):
        try:
            with open(file1, "r") as fd1, open(file2, "r") as fd2:
                diff = list(difflib.unified_diff(fd1.read().splitlines(), fd2.read().splitlines(), fromfile=file1, tofile=file2, lineterm=""))
        except UnicodeDecodeError:
            # To handle error for non-text file
            pass

    return diff

def metadata_diff(filepath, metadata1, metadata2):
    """Return the differences in metadata for specified file.

    Result is a dict with string keys <name of file property> and it
    value (<value in metadata1>, <value in metadata2>).
    """
    # Find tuples (property, value) in metadata which are not same
    diff = set(metadata1[filepath].items()) ^ set(metadata2[filepath].items())
    # Only tuples ("mtime",...) and ("chksum",...) can be different in file metadata
    diff = list(filter(lambda x: x[0] != "mtime" and x[0] != "chksum", diff))

    result = {}
    for key in diff:
        if isinstance(metadata1[filepath][key[0]], bytes):
            logger.debug("%s is type of bytes", str(key))
            result[key[0]] = (metadata1[filepath][key[0]].decode("utf-8"), metadata2[filepath][key[0]].decode("utf-8"))
        else:
            result[key[0]] = (metadata1[filepath][key[0]], metadata2[filepath][key[0]])

    return result

def device_mime(tar_type):
    """Return string representation of MIME from tarfile.type"""
    if tar_type == tarfile.BLKTYPE:
        return "inode/blockdevice; charset=binary"
    elif tar_type == tarfile.CHRTYPE:
        return "inode/chardevice; charset=binary"
    elif tar_type == tarfile.FIFOTYPE:
        return "inode/fifo; charset=binary"

def test_unowned_files(ID1, output_dir1, metadata1, ID2, output_dir2, metadata2):
    """Test changes in files that are not installed by package manager.

    Result contains a dict {"added":.., "removed":.., "modified"}. Key
    values are lists. Firt two values contain paths to added/removed
    files and its types. Key "modified" by default contains path to file, file type,
    file diff and file metadata changes. So list contains tuples
      (file_path, file_type, file_diff, file_metadatadiff)

    In silent mode, key "modified" contains only file paths and file types.
    """
    unowned_files1 = package_manager.get_unowned_files(ID1, metadata1, output_dir1)
    unowned_files2 = package_manager.get_unowned_files(ID2, metadata2, output_dir2)

    mime_loader = magic.open(magic.MAGIC_MIME)
    mime_loader.load()

    added = []
    for filepath in (set(unowned_files2)-set(unowned_files1)):
        if metadata2[filepath]["type"] in  [tarfile.BLKTYPE, tarfile.CHRTYPE, tarfile.FIFOTYPE]:
            mime = device_mime(metadata2[filepath]["type"])
        else:
            mime = mime_loader.file(os.path.normpath(os.sep.join([output_dir2,filepath])))
        added.append((filepath, mime))
    removed = []
    for filepath in (set(unowned_files1)-set(unowned_files2)):
        if metadata1[filepath]["type"] in  [tarfile.BLKTYPE, tarfile.CHRTYPE, tarfile.FIFOTYPE]:
            mime = device_mime(metadata1[filepath]["type"])
        else:
            mime = mime_loader.file(os.path.normpath(os.sep.join([output_dir1,filepath])))
        removed.append((filepath, mime))
    modified = []
    for filepath in (set(unowned_files1).intersection(set(unowned_files2))):
        metadata = metadata_diff(filepath, metadata1, metadata2)
        diff = files_diff(filepath, output_dir1, output_dir2)
        if metadata2[filepath]["type"] in  [tarfile.BLKTYPE, tarfile.CHRTYPE, tarfile.FIFOTYPE]:
            mime_new = device_mime(metadata2[filepath]["type"])
        else:
            mime_new = mime_loader.file(os.path.normpath(os.sep.join([output_dir2,filepath])))

        if containerdiff.silent:
            if len(diff) != 0 or len(metadata) != 0:
                modified.append((filepath, mime_new))
        else:
            if len(diff) != 0 or len(metadata) != 0:
                modified.append((filepath, mime_new, diff, metadata))

    return {"added":added, "removed":removed, "modified":modified}



def run(image1, image2):
    """Test files in the image.

    Adds one key to the output of the diff tool:
    "files" - dict containing information about changed files (see
              output of "test_files" function in this module)
    """
    ID1, metadata1, output_dir1 = image1
    ID2, metadata2, output_dir2 = image2

    logger.info("Testing files in the image")

    result = {}
    result["files"] = test_unowned_files(ID1, output_dir1, metadata1, ID2, output_dir2, metadata2)
    return result
