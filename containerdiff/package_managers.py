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

"""Add support for different package managers.

It is also possible to add support to another package mangers. To be
able to use tests in modules with the new package manager it is
necessary to implement it as a class which provides functions:
get_installed_packages and get_unowned_files .
"""

import docker
import tempfile
import os
import shutil
import logging

import containerdiff

logger = logging.getLogger(__name__)

def get_output_from_container(image, command):
    """Run 'command' in shell in container based on 'image'. Get its
    output by redirecting STDOUT to mounted file.

    Return list o lines from the 'command' output.
    """
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
    """This class represents RPM package manager."""

    def _get_owned_files(self, ID, root):
        """Get list files installed by rpms in image 'ID' which is
        expanded into 'root'. It runs "rpm -qal" command in the image
        and removes symbolic links in directories in the result.
        """
        # Some RPM package does not contain file, so rpm prints
        # "(contains no files)" string.
        filelist = get_output_from_container(ID, "rpm -qal | grep -v \(contains\ no\ files\)").split("\n")

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
        """Return the list of files that are listed in 'metadata' dict
        (result from extracting the image) and are not installed by
        rpm packages in image 'ID'.
        """

        owned_files = self._get_owned_files(ID, root)
        return list(set(metadata.keys())-set(owned_files))

    def get_installed_packages(self, ID):
        """Return list of installed packages in image 'ID'. Each
        element of the list is a tuple (<package name>, <version>).
        """
        packages = get_output_from_container(ID, "rpm -qa").split()

        name_version = []
        for package in packages:
            elements = package.split("-")
            name_version.append(("-".join(elements[:-2]), "-".join(elements[-2:])))
        return name_version
