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

"""Show diff in container image packages."""

import os
import difflib
import logging
import magic
import logging

import containerdiff.package_managers

logger = logging.getLogger(__name__)

# Contains the object of package manager class
package_manager = containerdiff.package_managers.RPM()

def test_packages(ID1, ID2):
    """Test changes in packages installed by package manager.

    Result contains a dict {"added":.., "removed":.., "modified"}. Each
    key has a list value. Values for first two keys contain tuples
    ("<package_name>,<version>") for added/removed packages. Key
    "modified" contains tuples (<package_name>, <old_version>,
    <new_version>).
    """
    packages1, versions1 = zip(*package_manager.get_installed_packages(ID1))
    packages2, versions2 = zip(*package_manager.get_installed_packages(ID2))

    # Removed packages - list of tuples ("package", "version")
    removed = [(package, versions1[packages1.index(package)]) for package in list(set(packages1)-set(packages2))]
    # Added packages - list of tuples ("package", "version")
    added = [(package, versions2[packages2.index(package)]) for package in list(set(packages2)-set(packages1))]
    # Packages with different versions - list of tuples ("package", "old_version", "new_version")
    modified = [(package, versions1[packages1.index(package)], versions2[packages2.index(package)]) \
                for package in list(set(packages2).intersection(set(packages1))) \
                if versions1[packages1.index(package)] != versions2[packages2.index(package)]]

    return {"added":added, "removed":removed, "modified":modified}



def run(image1, image2):
    """Test packages in the image.

    Adds one key to the output of the diff tool:
    "packages" - dict containing information about changed files (see
                 output of "test_packages" function in this module)
    """
    ID1, metadata1, output_dir1 = image1
    ID2, metadata2, output_dir2 = image2

    logger.info("Testing packages in the image")

    result = {}
    result["packages"] = test_packages(ID1, ID2)
    return result
