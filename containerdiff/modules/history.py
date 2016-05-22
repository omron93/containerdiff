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

"""Show diff in container image history."""

import difflib
import docker
import logging

import containerdiff

logger = logging.getLogger(__name__)

def dockerfile_from_image(ID, cli):
    """Return list of commands used to create image 'ID'. These
    commands is an output from docker history.
    """
    info = cli.inspect_image(ID)

    commands = []

    history = cli.history(ID)

    for item in history:
        # Remove prefix to get output more similar to Dockerfile
        if "/bin/sh -c #(nop) " in item["CreatedBy"]:
            commands.append(item["CreatedBy"][18:])
        else:
            commands.append(item["CreatedBy"])

    # Return time order of commands
    commands.reverse()
    return commands


def run(image1, image2):
    """Test history of the image.

    Adds one key to the output of the diff tool:
    "history" - unified_diff style changes in commands used to create
                the image
    """
    ID1, metadata1, output_dir1 = image1
    ID2, metadata2, output_dir2 = image2

    logger.info("Testing history of the image")

    cli = docker.AutoVersionClient(base_url = containerdiff.docker_socket)

    history1 = dockerfile_from_image(ID1, cli)
    history2 = dockerfile_from_image(ID2, cli)

    # Do unified_diff of commands
    diff = [item for item in difflib.unified_diff(history1, history2, n=0) if not item.startswith(("+++","---","@@"))]

    return {"history":diff}
