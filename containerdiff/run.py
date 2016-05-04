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

import argparse
import logging
import docker
import sys
import tempfile
import importlib
import pkgutil
import os
import json
import shutil

import containerdiff

from . import undocker
from . import modules
from .filter import filter_output

# Import program_version and program_desctiptions
from . import program_description, program_version

logger = logging.getLogger(__name__)

default_filter = os.path.join(os.path.dirname(__file__), "filter.json")

def run(args):
    """
    dictionary = {'silent': (True|False), 'log_level': \d+, 'imageID': [\s+, \s+], 'output': (None|\s+), 'filter': (None|\s+), 'directory': (None|\s+), 'host': (None|\s+)}
    """
    # Set logger
    logging.basicConfig(level=args['log_level'])

    # Set docker host
    if args['host']:
        containerdiff.docker_socket = args['host']

    # Get full image IDs
    ID1 = None
    ID2 = None
    cli = docker.AutoVersionClient(base_url = containerdiff.docker_socket)
    try:
        ID1 = cli.inspect_image(args['imageID'][0])["Id"]
    except docker.errors.NotFound:
        logger.critical("Can't find image %s. Exit!", args['imageID'][0])
        raise
    try:
        ID2 = cli.inspect_image(args['imageID'][1])["Id"]
    except docker.errors.NotFound:
        logger.critical("Can't find image %s. Exit!", args['imageID'][1])
        raise
    logger.info("ID1 - "+ID1)
    logger.info("ID2 - "+ID2)

    # Prepare filtering
    if args['filter']:
        with open(args['filter']) as filter_file:
            logger.debug("Using %s to get filter optins", args['filter'])
            filter_options = json.load(filter_file)

    try:
        extract_dir = "/tmp"
        if args['directory']:
            extract_dir = args['directory']
        output_dir1 = tempfile.mkdtemp(dir=extract_dir)
        output_dir2 = tempfile.mkdtemp(dir=extract_dir)

        metadata1 = undocker.extract(ID1, output_dir1)
        metadata2 = undocker.extract(ID2, output_dir2)

        image1 = (ID1, metadata1, output_dir1)
        image2 = (ID2, metadata2, output_dir2)

        result = {}
        for _, module_name, _ in pkgutil.iter_modules([os.path.dirname(modules.__file__)]):
            module = importlib.import_module(modules.__package__+"."+module_name)
            module_result = {}
            try:
                logger.info("Going to run modules.%s", module_name)
                module_result = module.run(image1, image2, args['silent'])
            except AttributeError:
                logger.error("Module file %s.py does not contain function run(image1, image2, verbosity)", module_name)
            if args['filter']:
                for key in module_result.keys():
                    if key in filter_options:
                        logger.info("Filtering '%s' key in output", key)
                        module_result[key] = filter_output(module_result[key], filter_options[key])
            result.update(module_result)

        logger.info("All modules finished")
        #return result
        if args['output']:
            logger.info("Writing output to %s", args['output'])
            with open(args['output'], "w") as fd:
                fd.write(json.dumps(result))

        if not args['directory']:
            logger.debug("Removing temporary directories")
            shutil.rmtree(output_dir1)
            shutil.rmtree(output_dir2)
        else:
            #with open(os.path.join(args.directory,ID1+".json"), "w") as fd:
            #    fd.write(json.dumps(metadata1))
            #with open(os.path.join(args.directory,ID2+".json"), "w") as fd:
            #    fd.write(json.dumps(metadata2))
            print("Image "+args['imageID'][0]+" extracted to "+output_dir1+".")
            print("Image "+args['imageID'][1]+" extracted to "+output_dir2+".")

        return result
    except:
        logger.debug("Error occured - cleaning temporary directories")
        shutil.rmtree(output_dir1, ignore_errors=True)
        shutil.rmtree(output_dir2, ignore_errors=True)
        raise

def main():
    """ Run Container Diff tool.

    This function takes arguments from *sys.argv*. So you can call this
    function by running this script witch specified command line
    arguments. Or assign arguments to sys.argv:
                    sys.argv = ['containerdiff.py', ID1, ID2, ...]
    and calling main function from this module.
    """
    parser = argparse.ArgumentParser(prog="containerdiff", description=program_description)
    parser.add_argument("-s", "--silent", help="Lower verbosity of diff output. See help of individual modules.", action="store_true")
    parser.add_argument("-f", "--filter", help="Enable filtering. Optionally specify JSON file with options (preinstalled \"filter.json\" by default).", type=str, const=default_filter, nargs="?")
    parser.add_argument("-o", "--output", help="Output file.", type=str)
    parser.add_argument("-p", "--preserve", help="Do not remove directories with extracted images. Optionally specify directory where to extact images (\"/tmp\" by default).", type=str, const="/tmp", nargs="?", dest="directory")
    parser.add_argument("--host", help="Docker daemon socket to connect to", type=str)
    parser.add_argument("-l", "--logging", help="Print additional logging information.", default=logging.WARN,  type=int, choices=[logging.DEBUG, logging.INFO, logging.WARN, logging.ERROR, logging.CRITICAL], dest="log_level")
    parser.add_argument("-d", "--debug", help="Print additional debug information (= -l "+str(logging.DEBUG)+").", action="store_const", const=logging.DEBUG, dest="log_level")
    parser.add_argument("--version", action="version", version="%(prog)s "+program_version)
    parser.add_argument("imageID", help="Docker ID of image", nargs=2)
    args = parser.parse_args()

    result = run(args.__dict__)
    if not args.output:
        sys.stdout.write(json.dumps(result))
