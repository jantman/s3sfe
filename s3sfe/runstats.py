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


class RunStats(object):
    """
    Object to hold statistics about the FileSyncer run.
    """

    def __init__(self, start_dt, meta_dt, query_dt, calc_dt, upload_dt, end_dt,
                 total_files, files_to_upload, errors, total_size_b,
                 uploaded_size_b):
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

    @property
    def summary(self):
        """
        Return a formatted string summary of the run information.

        :return: human-readable summary
        :rtype: str
        """
        raise NotImplementedError()
