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

import logging

logger = logging.getLogger(__name__)


class S3Wrapper(object):
    """
    Wrapper around S3 API. Intended to possibly, maybe, one day, allow other
    storage backends.
    """

    def __init__(self, bucket_name, prefix=None, dry_run=False):
        """
        Connect to S3 and setup the file storage backend.

        :param bucket_name: name of S3 bucket to upload to
        :type bucket_name: str
        :param prefix: prefix to prepend to file paths, when making them into
          S3 keys.
        :type prefix: str
        :param dry_run: if True, don't actually upload anything, just log what
        would be uploaded.
        :type dry_run: bool
        """
        logger.debug('Initializing S3: bucket_name=%s prefix=%s dry_run=%s',
                     bucket_name, prefix, dry_run)
        self._bucket_name = bucket_name
        self._prefix = prefix
        self._dry_run = dry_run

    def get_filelist(self):
        """
        Return all files currently stored in the backend, as a dict of the file
        path/key to a 3-tuple of the file size in bytes, file modification time
        as a float timestamp, and file md5sum (of the original file,
        not the encrypted file). File paths/keys are excluding ``self.prefix``,
        i.e. the same paths as they would have on the filesystem.

        :return: dict of files currently in S3. Keys are the file path excluding
          ``self.prefix`` (the path to the file on local disk). Values are
          3-tuples of size in bytes of the file's unencrypted contents, file
          modification time as a float timestamp (like the return value of
          :py:meth:`os.path.getmtime`), and md5sum of the unencrypted file
          contents as a hex string.
        :rtype: dict
        """
        raise NotImplementedError()

    def put_file(self, path, size_b, mtime, md5sum):
        """
        Write a file into the S3 storage backend.

        :param path: The path to the file on disk. This will be written into
          ``self.bucket_name``, prefixed with ``self.prefix``.
        :type path: str
        :param size_b: size of the file on disk in bytes
        :type size_b: int
        :param mtime: modification time of the file on disk, as a float
          timestamp (like the return value of :py:meth:`os.path.getmtime`).
        :type mtime: float
        :param md5sum: md5sum of the file contents on disk, as a hex string
        :type md5sum: str
        """
        # set metadata on object in S3
        # see http://boto3.readthedocs.io/en/latest/reference/customizations/s3.html#boto3.s3.transfer.S3Transfer
        # and http://boto3.readthedocs.io/en/latest/reference/services/s3.html#S3.Client.upload_file
        # and http://boto3.readthedocs.io/en/latest/_modules/boto3/s3/transfer.html
        raise NotImplementedError()
