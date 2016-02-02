#   Container Diff tool - show differences among container images
#
#   Copyright (C) 2015 Lars Kellogg-Stedman lars@oddbit.com
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


import json
import os
import logging
import tarfile
import tempfile
import shutil
import docker

from contextlib import closing

logger = logging.getLogger(__name__)

def find_layers(img, ID):
    """ Returns list of layers of image *ID*.
    First element of the list is a *ID*, then image's parent etc.

    The image *ID* has to be "full ID" (64 characters long).
    """

    if len(ID) != 64:
        return []

    with closing(img.extractfile('%s/json' % ID)) as fd:
        info = json.loads(fd.read().decode("utf8"))

    logger.debug('layer = %s', ID)
    for k in ['os', 'architecture', 'author', 'created']:
        if k in info:
            logger.debug('%s = %s', k, info[k])

    result = [ID]
    if 'parent' in info:
        result.extend(find_layers(img, info['parent']))

    return result

def extract(ID, output, one_layer=False, whiteouts=True):
    """ Extract the content of image *ID* to folder *output*.

    If *one_layer* is True only layer *ID* is extracted. If *whiteouts*
    is False there is no logic with files started with ".wh.".

    File information like owner, modification time and permissions is
    not set. It is stored in the dict structure with "path to the file"
    key (starting by "/", e.g. "/etc"). This struct is returned by this function.

    Device files are not extracted. Only the additional metadata are
    stored in returned dictionary.
    """
    metadata = {}

    cli = docker.Client(base_url="unix://var/run/docker.sock")
    try:
        ID = cli.inspect_image(ID)["Id"]
    except docker.errors.NotFound:
        logger.error("Can't find image %s. Exit!" % ID)
        return

    logger.info("saving image "+ID+".")
    image = cli.get_image(ID)

    with tempfile.NamedTemporaryFile() as fd:
        fd.write(image.data)

        with tarfile.open(name=fd.name) as img:
            logger.info('extracting image %s', ID)
            if not one_layer:
                layers = find_layers(img, ID)
            else:
                layers = [ID]

            if not os.path.isdir(output):
                os.mkdir(output)

            for layer_id in reversed(layers):
                logger.info('extracting layer %s', layer_id)
                with tarfile.TarFile(fileobj=
                        img.extractfile('%s/layer.tar' % layer_id)) as layer:

                    for member in layer.getmembers():
                        path = member.path
                        if whiteouts and (path.startswith('.wh.') or '/.wh.' in path):
                            if path.startswith('.wh.'):
                                newpath = path[4:]
                            else:
                                newpath = path.replace('/.wh.', '/')

                            logger.info('removing path %s', newpath)
                            del metadata["/"+newpath]
                            newpath = os.path.join(output, newpath)
                            # TODO use try to catch errors
                            if os.path.isdir(newpath):
                                shutil.rmtree(newpath)
                            else:
                                os.unlink(newpath)
                            continue

                        metadata["/"+path] = member.get_info()
                        #logger.debug('member metadata: %s', metadata[path])

                        if not member.isdev():
                            layer.extract(member, path=output, set_attrs=False)
                    logger.info("metadata size - %i", len(metadata))

    return metadata

