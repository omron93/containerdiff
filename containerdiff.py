#!/usr/bin/env python3
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


import argparse
import logging
import docker
import sys
import tempfile
import importlib
import pkgutil
import os
import json

import undocker
import tests

program_version = "0.1"

def main():
    """ Run Container Diff tool.

    This function takes arguments from *sys.argv*. So you can call this
    function by running this script witch specified command line
    arguments. Or assign arguments to sys.argv:
                    sys.argv = ['containerdiff.py', ID1, ID2, ...]
    and calling main function from this module.
    """
    parser = argparse.ArgumentParser(prog="containerdiff", description="Show changes among two container images.")
    parser.add_argument("-o", "--output", help="Output directory.")
    parser.add_argument("-v", "--verbose", help="Set the verbosity of diff output. See help of individual tests.", action="store_const", default=3, const=3, dest="verbosity")
    parser.add_argument("-s", "--silent", help="Set the verbosity of diff output. See help of individual tests.", action="store_const", default=3, const=2, dest="verbosity")
    parser.add_argument("-ss", "--supersilent", help="Set the verbosity of diff output. See help of individual tests.", action="store_const", default=3, const=1, dest="verbosity")
    parser.add_argument("-l", "--logging", help="Print additional logging information.", default=logging.WARN,  type=int, choices=[logging.DEBUG, logging.INFO, logging.WARN, logging.ERROR, logging.CRITICAL], dest="log_level")
    parser.add_argument("-d", "--debug", help="Print additional debug information (= -l 10).", action="store_const", const=logging.DEBUG, dest="log_level")
    parser.add_argument("--version", action="version", version="%(prog)s "+program_version)
    parser.add_argument("imageID", nargs=2)
    args = parser.parse_args()

    # Set logger
    logging.basicConfig(level=args.log_level)
    logger = logging.getLogger(__name__)
    # Get full image IDs
    ID1 = None
    ID2 = None
    cli = docker.Client(base_url="unix://var/run/docker.sock")
    try:
        ID1 = cli.inspect_image(args.imageID[0])["Id"]
    except docker.errors.NotFound:
        logger.critical("Can't find image %s. Exit!" % args.imageID[0])
        sys.exit(1)

    try:
        ID2 = cli.inspect_image(args.imageID[1])["Id"]
    except docker.errors.NotFound:
        logger.critical("Can't find image %s. Exit!" % args.imageID[1])
        sys.exit(1)

    logger.info("ID1 - "+ID1)
    logger.info("ID2 - "+ID2)

    with tempfile.TemporaryDirectory() as output_dir1, \
            tempfile.TemporaryDirectory() as output_dir2:
        metadata1 = undocker.extract(ID1, output_dir1)
        metadata2 = undocker.extract(ID2, output_dir2)

        image1 = (ID1, metadata1, output_dir1)
        image2 = (ID2, metadata2, output_dir2)

        result = {}
        for _, module_name, _ in pkgutil.iter_modules([os.path.dirname(tests.__file__)]):
            module = importlib.import_module("tests."+module_name)
            try:
                logger.info("Going to run tests."+module_name+".")
                test_result = module.run(image1, image2, args.verbosity)
                result.update(test_result)
            except AttributeError:
                logger.error("Test file "+module_name+".py does not contain function run(image1, image2, verbosity)")

        logger.info("Tests finished. Writing output.")
        #return result
        if args.output:
            with open(args.output, "w") as fd:
                fd.write(json.dumps(result))
        else:
            sys.stdout.write(json.dumps(result))

    return result


if __name__ == '__main__':
    main()
