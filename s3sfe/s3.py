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


class S3Wrapper(object):
    """
    Wrapper around S3 API. Intended to possibly, maybe, one day, allow other
    storage backends.
    """

    def __init__(self, prefix='/'):
        pass

    def get_filelist(self):
        """
        Return all files currently stored in the backend, as a dict of the file
        path/key to a 3-tuple of the file size in bytes, file modification time
        as a datetime.datetime object, and file md5sum (of the original file,
        not the encrypted file). File paths/keys are excluding ``self.prefix``,
        i.e. the same paths as they would have on the filesystem.

        :return:
        :rtype:
        """
        pass

    def put_file(self, path):
        pass
