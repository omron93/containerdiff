#   Container Diff tool - show differences among container images
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
#   along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
#

"""Main module of containerdiff.

I contains some options and import all parts of 'run' module.
"""

program_version = "0.4"
program_description = "Show changes among two container images."

docker_socket = "unix://var/run/docker.sock"
silent = False

from containerdiff.run import *
