#   ContainerDiff - tool to show differences among container images
#
#   Copyright (C) 2015 Lars Kellogg-Stedman lars@oddbit.com
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

""" Extract a content of docker image."""

import json
import os
import logging
import tarfile
import tempfile
import shutil
import docker

import containerdiff

from contextlib import closing

logger = logging.getLogger(__name__)

def find_layers(img, ID):
    """Returns a list of underlying layers for the layer 'ID'. First
    element of the list is a top layer and then the underlying layers -
    it is reversed order in which docker expands layers during
    container creation.

    'img' is a TarFile object of open docker image.

    The 'ID' has to be 'full ID' (64 characters long).
    """
    if len(ID) != 64:
        return []

    with closing(img.extractfile('%s/json' % ID)) as fd:
        info = json.loads(fd.read().decode('utf8'))

    logger.debug('layer = %s', ID)
    for k in ['os', 'architecture', 'author', 'created']:
        if k in info:
            logger.debug('%s = %s', k, info[k])

    result = [ID]
    if 'parent' in info:
        result.extend(find_layers(img, info['parent']))

    return result

def extract(ID, output, one_layer=False, whiteouts=True):
    """Extract the content of image *ID* to folder *output*.

    If *one_layer* is True only layer *ID* is extracted. If *whiteouts*
    is False there is no logic with files started with '.wh.'.

    File information like owner, modification time and permissions is
    not set. It is stored in the dict structure with 'path to the file'
    key (starting by '/', e.g. '/etc'). This struct is returned by this function.

    Device files are not extracted. Only the additional metadata are
    stored in returned dictionary.
    """
    metadata = {}

    cli = docker.AutoVersionClient(base_url = containerdiff.docker_socket)
    try:
        ID = cli.inspect_image(ID)['Id']
    except docker.errors.NotFound:
        logger.critical("Can't find image %s", ID)
        raise

    logger.info('Saving image %s', ID)
    image = cli.get_image(ID)

    with tempfile.NamedTemporaryFile() as fd:
        fd.write(image.data)

        with tarfile.open(name=fd.name) as img:
            logger.info('Extracting image %s', ID)
            # Get ID of the first layer if docker uses content addressability
            if ('manifest.json' and ID.split(':')[-1]+'.json') in img.getnames():
                with closing(img.extractfile('manifest.json')) as fd:
                    manifest = json.loads(fd.read().decode('utf8'))
                ID = manifest[0]['Layers'][-1].split('/')[0]

            if not one_layer:
                layers = find_layers(img, ID)
            else:
                layers = [ID]

            if not os.path.isdir(output):
                os.mkdir(output)

            for layer_id in reversed(layers):
                logger.info('Extracting layer %s', layer_id)
                with tarfile.TarFile(fileobj=
                        img.extractfile('%s/layer.tar' % layer_id)) as layer:
                    # Extract all members in a layer
                    for member in layer.getmembers():
                        path = member.path
                        if whiteouts and (path.startswith('.wh.') or '/.wh.' in path):
                            if path.startswith('.wh.'):
                                newpath = path[4:]
                            else:
                                newpath = path.replace('/.wh.', '/')

                            logger.debug('Removing path %s', newpath)
                            del metadata['/'+newpath]
                            newpath = os.path.join(output, newpath)

                            if os.path.isdir(newpath):
                                shutil.rmtree(newpath)
                            else:
                                os.unlink(newpath)
                            continue

                        metadata['/'+path] = member.get_info()

                        if not member.isdev():
                            layer.extract(member, path=output, set_attrs=False)
                    logger.debug('Actual metadata size - %i', len(metadata))

    return metadata

