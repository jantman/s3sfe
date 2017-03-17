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
import os

from .runstats import RunStats
from .s3 import S3Wrapper
from .utils import md5_file, dtnow

logger = logging.getLogger(__name__)


class FileSyncer(object):
    """
    Main class that handles synchronizing files to S3.
    """

    def __init__(self, bucket_name, prefix=None, dry_run=False, ssec_key=None):
        """
        Initialize the FileSyncer

        :param bucket_name: name of S3 bucket to sync to
        :type bucket_name: str
        :param prefix: string to prefix file paths with, to determine their
          keys in S3
        :type prefix: str
        :param dry_run: if true, do not actually upload; print what would be
          done
        :type dry_run: bool
        :param ssec_key: 32-bit AES256 SSE-C key (binary)
        :type ssec_key: bytes
        """
        if prefix is None:
            prefix = ''
        logger.debug('Using S3 prefix: "%s"', prefix)
        self.s3 = S3Wrapper(
            bucket_name, prefix=prefix, dry_run=dry_run, ssec_key=ssec_key
        )
        self._dry_run = dry_run

    def run(self, file_paths, exclude_paths=[]):
        """
        Run the sync. Return some statistics about it.

        :param file_paths: list of file paths to synchronize. Can be files or
          directories; directories will be synced recursively.
        :type file_paths: list
        :param exclude_paths: list of path starting substrings to exclude from
          backups. Any path beginning with one of these strings will be
          excluded from the backup.
        :type exclude_paths: list
        :return: statistics about the synchronization operation.
        :rtype: s3sfe.runstats.RunStats
        """
        logger.debug('Starting run...')
        start_dt = dtnow()
        all_files = self._list_all_files(file_paths)
        if len(exclude_paths) > 0:
            all_files = self._filter_filelist(all_files, exclude_paths)
        meta_dt = dtnow()
        files = self._file_meta(all_files)
        total_size = sum(files[f][0] for f in files.keys())
        logger.info('Source: %d files total, %d bytes total',
                    len(files), total_size)
        query_dt = dtnow()
        s3files = self._s3_files()
        logger.info('S3: %d files total', len(s3files))
        calc_dt = dtnow()
        to_upload = self._files_to_upload(files, s3files)
        upload_dt = dtnow()
        errors, uploaded_bytes = self._upload_files(to_upload)
        end_dt = dtnow()
        logger.debug('Ending run...')
        return RunStats(
            start_dt, meta_dt, query_dt, calc_dt, upload_dt, end_dt,
            len(all_files), len(to_upload), errors, total_size, uploaded_bytes,
            dry_run=self._dry_run
        )

    def _s3_files(self):
        """
        Return a dict of files currently in S3, where keys are local file
        paths and values are 3-tuples of (file size in bytes, file modification
        time as a float timestamp, and file md5sum as a hex string).

        :return: mapping of file paths to file metadata
        :rtype: dict
        """
        files = {}
        for k, d in self.s3.get_filelist().items():
            files[k] = (
                int(d.get('size_b', 0)),
                float(d.get('mtime', 0)),
                d.get('md5sum', None)
            )
        return files

    def restore(self, local_prefix, file_paths):
        """
        Restore one or more files.

        :param local_prefix: local filesystem prefix to restore files under
        :type local_prefix: str
        :param file_paths: list of file paths to synchronize. Can be files or
          directories; directories will be synced recursively.
        :type file_paths: list
        """
        logger.info('Beginning restoration of files to: %s', local_prefix)
        logger.debug('Files to restore: %s', file_paths)
        logger.debug('Listing files in S3 bucket')
        s3files = self.s3.get_filelist()
        logger.debug(
            'Found %d files in S3; building restore file list', len(s3files)
        )
        restore_files = self._make_restore_file_list(file_paths, s3files)
        logger.info('Found %d files to restore', len(restore_files))
        success = 0
        errors = []
        for fpath in restore_files:
            try:
                self.s3.get_file(fpath, local_prefix)
                success += 1
            except Exception as ex:
                logger.error('Error downloading file %s: %s',
                             fpath, ex, exc_info=True)
                errors.append(fpath)
        if len(errors) > 0:
            logger.error(
                'ERROR: Failed downloading %d of %d files',
                len(errors), len(restore_files)
            )
        else:
            logger.info(
                'Successfully downloaded all %d files', len(restore_files)
            )
        return errors

    def _make_restore_file_list(self, restore_paths, s3_files):
        """
        Given a list of paths the user asked to restore and a the files in
        S3, build the full list of files to restore/download.

        :param restore_paths: list of file paths to synchronize. Can be files or
          directories; directories will be synced recursively.
        :type restore_paths: list
        :param s3_files: S3 file paths to current metadata
        :type s3_files: dict
        :return: list of S3 files to download
        :rtype: list
        """
        res = []
        s3_files = s3_files.keys()
        for fpath in restore_paths:
            if fpath in s3_files:
                res.append(fpath)
                continue
            # not in S3 files... might be a path
            subs = 0
            for s3path in s3_files:
                if s3path.startswith(fpath):
                    res.append(s3path)
                    subs += 1
            if subs > 0:
                logger.debug('Found %d files in S3 under path %s', subs, s3path)
        return res

    def _list_all_files(self, paths):
        """
        Given a list of paths on the local filesystem, return a list of all
        files in ``paths`` that exist, and for any directories in ``paths`` that
        exist, all files recursively contained in them.

        :param paths: list of file/directory paths to check
        :type paths: list
        :return: list of all extant files contained under those paths
        :rtype: list
        """
        files = []
        logger.info('Listing files under %d paths', len(paths))
        for p in paths:
            if not os.path.exists(p):
                logger.warning('Skipping non-existent path: %s', p)
                continue
            if os.path.isfile(p):
                files.append(p)
            elif os.path.isdir(p):
                dirs = self._listdir(p)
                logger.debug('Found %d files under %s', len(dirs), p)
                files.extend(dirs)
            else:
                logger.warning('Skipping unknown path type: %s', p)
        logger.debug('Done finding candidate files.')
        return list(set(files))

    def _listdir(self, path):
        """
        Given the path to a directory, return a list of all file paths under
        that directory (recursively).

        :param path: path to directory
        :type path: str
        :return: list of regular file paths under that directory
        :rtype: list
        """
        files = []
        for root, _, filenames in os.walk(path):
            for fn in filenames:
                p = os.path.join(root, fn)
                if os.path.isfile(p):
                    files.append(p)
        return files

    def _file_meta(self, files):
        """
        Given a list of local file paths, return a dict where keys are those
        paths and values are 3-tuples of (file size in bytes, file modification
        time as a float timestamp, and file md5sum as a hex string).

        :param files: files to get metadata for
        :type files: list
        :return: mapping of file paths to file metadata
        :rtype: dict
        """
        logger.info('Finding metadata for all %d files', len(files))
        meta = {}
        for f in files:
            logger.debug('Checking metadata for: %s', f)
            meta[f] = (
                os.path.getsize(f),
                os.path.getmtime(f),
                md5_file(f)
            )
        return meta

    def _filter_filelist(self, all_files, exclude_paths):
        """
        Given a list of all candidate files and a list of path prefixes to
        exclude, return all files from ``all_files`` that do not begin with an
        excluded path.

        :param all_files: list of all candidate local files
        :type all_files: list
        :param exclude_paths: list of path starting substrings to exclude from
          backups. Any path beginning with one of these strings will be
          excluded from the backup.
        :type exclude_paths: list
        :return: all files not excluded
        :rtype: list
        """
        res = []
        for f in all_files:
            for path in exclude_paths:
                if f.startswith(path):
                    # excluded; ignore
                    logger.debug('Excluding %s based on exclude path %s',
                                 f, path)
                    break
            else:
                res.append(f)
        return res

    def _files_to_upload(self, local_files, s3_files):
        """
        Given two dicts of files, one local and one in S3, each having keys of
        the local file path and values that are 3-tuples of (file size in bytes,
        file modification time as a float timestamp, and file md5sum as a hex
        string), return the subset of ``local_files`` that are not in, or do
        not have md5sums matching, ``s3_files``.

        If ``exclude_paths`` is not empty, any local file with a path beginning
        with an entry in ``exclude_paths`` will be omitted.

        :param local_files: local file paths to current metadata
        :type local_files: dict
        :param s3_files: S3 file paths to current metadata
        :type s3_files: dict
        :return: subset of local_files that are not in S3, or need to be
          updated in S3 (per the md5sum)
        :rtype: dict
        """
        logger.debug('Comparing %d local files with %d S3 files',
                     len(local_files), len(s3_files))
        files = {}
        for k in local_files.keys():
            if k not in s3_files:
                files[k] = local_files[k]
            elif local_files[k][2] != s3_files[k][2]:
                files[k] = local_files[k]
        logger.info('Found %d files to upload', len(files))
        return files

    def _upload_files(self, files):
        """
        Upload the specified files to S3.

        :param files: dict of files that need to be uploaded to S3. Keys are
          local file paths, values are 3-tuples of (file size in bytes,
          file modification time as a float timestamp, and file md5sum as a hex
          string)
        :type files: dict
        :return: 2-tuple of (list of file paths that errored uploading, total
          bytes uploaded)
        :rtype: tuple
        """
        logger.info('Beginning upload of %d files', len(files))
        errored = []
        total_bytes = 0
        for f in sorted(files.keys()):
            try:
                self.s3.put_file(f, files[f][0], files[f][1], files[f][2])
                total_bytes += files[f][0]
            except Exception as ex:
                logger.error('Error uploading file %s: %s',
                             f, ex, exc_info=True)
                errored.append(f)
        return errored, total_bytes
