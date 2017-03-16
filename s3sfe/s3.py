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

import boto3
import logging
import os
from base64 import b64encode
from hashlib import md5
from s3sfe.version import VERSION
import re

logger = logging.getLogger(__name__)


class S3Wrapper(object):
    """
    Wrapper around S3 API. Intended to possibly, maybe, one day, allow other
    storage backends.
    """

    slash_re = re.compile('\/+')

    def __init__(self, bucket_name, prefix='', dry_run=False, ssec_key=None):
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
        :param ssec_key: 32-bit AES256 SSE-C key (binary)
        :type ssec_key: bytes
        """
        logger.debug('Initializing S3: bucket_name=%s prefix=%s dry_run=%s',
                     bucket_name, prefix, dry_run)
        self._bucket_name = bucket_name
        self._prefix = prefix
        self._dry_run = dry_run
        self._key, self._keymd5 = self._encode_key(ssec_key)
        logger.debug('Connecting to S3')
        self._s3 = boto3.resource('s3')
        self._s3client = boto3.client('s3')

    def _encode_key(self, key):
        """
        Determine the base64-encoded SSE-C key and its MD5sum, for use in API
        calls.

        :param key:
        :type key:
        :return: 2-tuple of base64-encoded key and base64-encoded MD5 of key
        :rtype: tuple
        """
        k = b64encode(key).decode('utf-8')
        m = b64encode(md5(key).digest()).decode('utf-8')
        return k, m

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
          :py:func:`os.path.getmtime`), and md5sum of the unencrypted file
          contents as a hex string.
        :rtype: dict
        """
        logger.debug('Listing all objects in bucket, under given prefix')
        files = {}
        bkt = self._s3.Bucket(self._bucket_name)
        if self._prefix == '':
            objects = bkt.objects.all()
        else:
            objects = bkt.objects.filter(Prefix=self._prefix)
        for obj in objects:
            files[self._path_for_key(obj.key)] = self._get_metadata(obj.key)
        logger.debug('Found %d matching objects', len(files))
        return files

    def _path_for_key(self, key):
        """
        Given a key in S3, return the filesystem path it corresponds to

        :param key: S3 key
        :type key: str
        :return: corresponding file path
        :rtype: str
        """
        if self._prefix == '':
            return key
        k = key[len(self._prefix):]
        if self._prefix.endswith('/') and not k.startswith('/'):
            k = '/' + k
        return k

    def _get_metadata(self, key):
        """
        Return metadata for one key in the bucket.

        :param key: key in the bucket
        :type key: str
        :return: metadata for key
        :rtype: dict
        """
        m = self._s3client.head_object(
            Bucket=self._bucket_name,
            Key=key,
            SSECustomerAlgorithm='AES256',
            SSECustomerKey=self._key,
            SSECustomerKeyMD5=self._keymd5
        )['Metadata']

        return m

    def _key_for_path(self, path):
        """
        Return the S3 key prefix for a given file.

        :param path: The path to the file on disk.
        :type path: str
        :return: S3 key for the given local path
        :rtype: str
        """
        if self._prefix is None or self._prefix == '':
            return path
        # be sure to collapse slashes
        p = self.slash_re.sub('/', self._prefix + '/' + path)
        return p

    def put_file(self, path, size_b, mtime, md5sum):
        """
        Write a file into the S3 storage backend.

        :param path: The path to the file on disk. This will be written into
          ``self.bucket_name``, prefixed with ``self.prefix``.
        :type path: str
        :param size_b: size of the file on disk in bytes
        :type size_b: int
        :param mtime: modification time of the file on disk, as a float
          timestamp (like the return value of :py:func:`os.path.getmtime`).
        :type mtime: float
        :param md5sum: md5sum of the file contents on disk, as a hex string
        :type md5sum: str
        """
        bkt = self._s3.Bucket(self._bucket_name)
        key = self._key_for_path(path)
        if self._dry_run:
            logger.warning("DRY RUN; would upload %s to %s", path, key)
            return
        logger.debug('Uploading %s to %s', path, key)
        bkt.upload_file(
            path,
            key,
            ExtraArgs={
                'ACL': 'private',
                'SSECustomerAlgorithm': 'AES256',
                'SSECustomerKey': self._key,
                'SSECustomerKeyMD5': self._keymd5,
                'Metadata': {
                    'UploadedBy': 's3sfe-%s' % VERSION,
                    'size_b': '%s' % size_b,
                    'mtime': '%s' % mtime,
                    'md5sum': '%s' % md5sum
                }
            }
        )

    def get_file(self, path, local_prefix=None):
        """
        Download a file that was originally at ``path`` locally. If
        ``local_prefix`` is not None, the local file will be replaced with the
        downloaded one. Otherwise, the download path will be prefixed with
        ``local_prefix``.

        :param path: local file path to download from S3
        :type path: str
        :param local_prefix: prefix to download under locally
        :type local_prefix: str
        """
        bkt = self._s3.Bucket(self._bucket_name)
        key = self._key_for_path(path)
        if local_prefix is None:
            real_path = os.path.abspath(path)
        else:
            if path[0] == '/':
                path = path[1:]
            real_path = os.path.abspath(os.path.join(local_prefix, path))
        dldir = os.path.dirname(real_path)
        if self._dry_run:
            logger.warning("DRY RUN; would download %s to %s", key, real_path)
            return
        logger.debug('Downloading s3 key %s to %s', key, real_path)
        if not os.path.exists(dldir):
            logger.debug('Creating download directory: %s', dldir)
            os.makedirs(dldir)
        bkt.download_file(
            key,
            real_path,
            ExtraArgs={
                'SSECustomerAlgorithm': 'AES256',
                'SSECustomerKey': self._key,
                'SSECustomerKeyMD5': self._keymd5
            }
        )
