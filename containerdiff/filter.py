#   ContainerDiff - tool to show differences among container images
#
#   Copyright (C) 2015 Marek Skalicky mskalick@redhat.com
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

"""Filter an output of modules."""

import logging
import re

logger = logging.getLogger(__name__)

def filter_output(data, options):
    """Filter an output of a module.

    'data' - data to filter (dict or list)
    'option' - filtering options (see filter.json for example or
               documentation of containerdiff)

    Return value are filtered data. In case of any error it returns
    unmodified data.
    """
    # Action key is mandatory
    if not "action" in options or not isinstance(options["action"], str):
        logger.error("Filter: wrong or missing \"action\" key in filter options")
        return data
    # Filtering options have to contain regular expressions to match
    if not "data" in options or not isinstance(options["data"], list):
        logger.error("Filter: wrong or missing \"data\" key in filter options")
        return data

    if "keys" in options:
        # Filter each specified key
        if not isinstance(data, dict):
            logger.error("Filter: \"keys\" filter option specified but filtered data is not dictionary")
            return data
        for key in options["keys"]:
            if not key in data:
                logger.warning("Filter: in filtered data there is no key " + key)
                break
            data[key] = filter_output(data[key], {"action":options["action"], "data":options["data"]})
    else:
        if not isinstance(data, list):
            logger.error("Filter: output of the module is not a list")
            return data
        if len(options["data"]) == 0:
            logger.warning("Filter: \"data\" filter option is empty")
            return data

        # Check if item match any regular expression
        pattern = re.compile("|".join(options["data"]))
        # Do filtering of string representations of items
        if options["action"] == "include":
            data = list(filter(lambda item: pattern.search(str(item)), data))
        elif options["action"] == "exclude":
            data = list(filter(lambda item: not pattern.search(str(item)), data))

    return data
