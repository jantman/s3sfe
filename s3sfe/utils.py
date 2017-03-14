"""
The latest version of this package is available at:
<http://github.com/jantman/s3sfe>

################################################################################
Copyright 2017 Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>

    This file is part of s3sfe, also known as s3sfe.

    s3sfe is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    s3sfe is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with s3sfe.  If not, see <http://www.gnu.org/licenses/>.

The Copyright and Authors attributions contained herein may not be removed or
otherwise altered, except to add the Author attribution of a contributor to
this work. (Additional Terms pursuant to Section 7b of the AGPL v3)
################################################################################
While not legally required, I sincerely request that anyone who finds
bugs please submit them at <https://github.com/jantman/s3sfe> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
################################################################################
"""

from datetime import datetime
from hashlib import md5


def md5_file(path):
    """
    Return the MD5 sum of the contents of the file at ``path``.

    :param path: path to the file
    :type path: str
    :return: md5sum of the file at the given path, as a hex digest
    :rtype: str
    """
    with open(path, 'rb') as fh:
        m = md5()
        while True:
            data = fh.read(128)
            if not data:
                break
            m.update(data)
        return m.hexdigest()


def dtnow():
    """
    Helper for testing; just returns datetime.datetime.now()

    :return: current datetime - ``datetime.datetime.now()``
    :rtype: datetime.datetime
    """
    return datetime.now()
