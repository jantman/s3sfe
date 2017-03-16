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
from s3sfe.version import VERSION
from platform import node
from getpass import getuser
from humanize import intcomma, naturalsize

logger = logging.getLogger(__name__)


class RunStats(object):
    """
    Object to hold statistics about the FileSyncer run.
    """

    def __init__(self, start_dt, meta_dt, query_dt, calc_dt, upload_dt, end_dt,
                 total_files, files_to_upload, errors, total_size_b,
                 uploaded_size_b, dry_run=False):
        """

        :param start_dt: when the run began; before listing all files
        :type start_dt: datetime.datetime
        :param meta_dt: when run started finding file metadata
        :type meta_dt: datetime.datetime
        :param query_dt: when run started querying storage backend for current
        :type query_dt: datetime.datetime
        :param calc_dt: when run started calculating list of files to upload
        :type calc_dt: datetime.datetime
        :param upload_dt: when run started uploading files
        :type upload_dt: datetime.datetime
        :param end_dt: when run finished
        :type end_dt: datetime.datetime
        :param total_files: total number of files matched by input list
        :type total_files: int
        :param files_to_upload: number of files that should be uploaded
        :type files_to_upload: int
        :param total_size_b: total size of all matched files in bytes
        :type total_size_b: int
        :param uploaded_size_b: total size of uploaded files in bytes
        :type uploaded_size_b: int
        :param errors: list of files that errored when uploading
        :type errors: list
        :param dry_run: if true, do not actually upload; print what would be
          done
        :type dry_run: bool
        """
        self._start_dt = start_dt
        self._meta_dt = meta_dt
        self._query_dt = query_dt
        self._calc_dt = calc_dt
        self._upload_dt = upload_dt
        self._end_dt = end_dt
        self._total_files = total_files
        self._files_uploaded = files_to_upload
        self._total_size_b = total_size_b
        self._uploaded_size_b = uploaded_size_b
        self._errors = errors
        self._dry_run = dry_run

    @property
    def time_total(self):
        """
        Return a timedelta describing the total run time.

        :return: total run time
        :rtype: datetime.timedelta
        """
        return self._end_dt - self._start_dt

    @property
    def time_listing(self):
        """
        Return a timedelta describing the time taken to list files.

        :return: time taken to list files
        :rtype: datetime.timedelta
        """
        return self._meta_dt - self._start_dt

    @property
    def time_meta(self):
        """
        Return a timedelta describing the time taken to query file metadata.

        :return: time taken to query file metadata
        :rtype: datetime.timedelta
        """
        return self._query_dt - self._meta_dt

    @property
    def time_s3_query(self):
        """
        Return a timedelta describing the time taken to query current files in
        S3.

        :return: time to query files in S3
        :rtype: datetime.timedelta
        """
        return self._calc_dt - self._query_dt

    @property
    def time_calc(self):
        """
        Return a timedelta describing the time taken to determine which files
        to upload.

        :return: time to determine which files to upload
        :rtype: datetime.timedelta
        """
        return self._upload_dt - self._calc_dt

    @property
    def time_upload(self):
        """
        Return a timedelta describing the time required to upload the files.

        :return: time taken to upload the files
        :rtype: datetime.timedelta
        """
        return self._end_dt - self._upload_dt

    @property
    def total_files(self):
        """
        Return the total number of files being backed up from the local
        filesystem.

        :return: total number of files being backed up from local filesystem
        :rtype: int
        """
        return self._total_files

    @property
    def total_bytes(self):
        """
        Return the total size in bytes of all files being backed up from the
        local filesystem.

        :return: total size in bytes of files being backed up from local
          filesystem
        :rtype: int
        """
        return self._total_size_b

    @property
    def files_uploaded(self):
        """
        Return the number of files uploaded to S3.

        :return: number of files uploaded to S3
        :rtype: int
        """
        return self._files_uploaded

    @property
    def bytes_uploaded(self):
        """
        Return the bytes uploaded to S3.

        :return: bytes uploaded to S3
        :rtype: int
        """
        return self._uploaded_size_b

    @property
    def error_files(self):
        """
        Return a list of local file paths that encountered errors while
        uploading.

        :return: local paths that failed/errored uploading
        :rtype: list
        """
        return self._errors

    @property
    def summary(self):
        """
        Return a formatted string summary of the run information.

        :return: human-readable summary
        :rtype: str
        """
        s = "s3sfe v%s run report\n" % VERSION
        x = "%s (%s on %s)\n" % (
            self._end_dt.strftime('%A, %B %d, %Y %H:%M:%S'),
            getuser(), node()
        )
        s += x
        s += ('-' * (len(x)-1)) + "\n"
        if self._dry_run:
            s += "-- DRY RUN - NO FILES ACTUALLY UPLOADED --\n"
        s += "Total Run Time: %s\n" % self.time_total
        s += "Time Listing Files: %s\n" % self.time_listing
        s += "Time Getting Metadata: %s\n" % self.time_meta
        s += "Time Querying S3: %s\n" % self.time_s3_query
        s += "Time Calculating Uploads: %s\n" % self.time_calc
        s += "Time Uploading Files: %s\n" % self.time_upload
        s += "\n"
        s += "Backed-up files on disk: %s files; %s\n" % (
            intcomma(self.total_files), naturalsize(self.total_bytes)
        )
        s += "Uploaded %s files; %s\n" % (
            intcomma(self.files_uploaded), naturalsize(self.bytes_uploaded)
        )
        if len(self.error_files) < 1:
            s += "\nAll files uploaded successfully.\n"
        else:
            s += "\n%d files failed uploading:\n" % len(self.error_files)
            for f in sorted(self.error_files):
                s += "%s\n" % f
        if self._dry_run:
            s += "-- DRY RUN - NO FILES ACTUALLY UPLOADED --\n"
        return s
