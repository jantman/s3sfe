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

import sys
from datetime import datetime, timedelta
from textwrap import dedent

from s3sfe.runstats import RunStats
from s3sfe.version import VERSION

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT, mock_open  # noqa
else:
    from unittest.mock import patch, call, Mock, DEFAULT, mock_open  # noqa

pbm = 's3sfe.runstats'
pb = '%s.RunStats' % pbm


class TestRunStatsInit(object):

    def test_init(self):
        dt_s = datetime(2017, 1, 1, 11, 12, 13)
        dt_m = datetime(2017, 1, 1, 11, 12, 14)
        dt_q = datetime(2017, 1, 1, 11, 12, 16)
        dt_c = datetime(2017, 1, 1, 11, 12, 19)
        dt_u = datetime(2017, 1, 1, 11, 12, 23)
        dt_e = datetime(2017, 1, 1, 11, 12, 28)
        r = RunStats(
            dt_s, dt_m, dt_q, dt_c, dt_u, dt_e,
            11, 10, ['foo'], 12345, 789,
        )
        assert r._start_dt == dt_s
        assert r._meta_dt == dt_m
        assert r._query_dt == dt_q
        assert r._calc_dt == dt_c
        assert r._upload_dt == dt_u
        assert r._end_dt == dt_e
        assert r._total_files == 11
        assert r._files_uploaded == 10
        assert r._errors == ['foo']
        assert r._total_size_b == 12345
        assert r._uploaded_size_b == 789
        assert r._dry_run is False

    def test_init_dry_run(self):
        dt_s = datetime(2017, 1, 1, 11, 12, 13)
        dt_m = datetime(2017, 1, 1, 11, 12, 14)
        dt_q = datetime(2017, 1, 1, 11, 12, 16)
        dt_c = datetime(2017, 1, 1, 11, 12, 19)
        dt_u = datetime(2017, 1, 1, 11, 12, 23)
        dt_e = datetime(2017, 1, 1, 11, 12, 28)
        r = RunStats(
            dt_s, dt_m, dt_q, dt_c, dt_u, dt_e,
            11, 10, ['foo'], 12345, 789,
            dry_run=True
        )
        assert r._dry_run is True


class TestRunStats(object):

    def setup(self):
        self.dt_s = datetime(2017, 1, 1, 11, 12, 13)
        self.dt_m = datetime(2017, 1, 1, 11, 12, 14)
        self.dt_q = datetime(2017, 1, 1, 11, 12, 16)
        self.dt_c = datetime(2017, 1, 1, 11, 12, 19)
        self.dt_u = datetime(2017, 1, 1, 11, 12, 23)
        self.dt_e = datetime(2017, 1, 1, 11, 12, 28)
        self.stats = RunStats(
            self.dt_s, self.dt_m, self.dt_q, self.dt_c, self.dt_u, self.dt_e,
            11, 10, ['foo'], 12345, 789
        )

    def test_time_total(self):
        assert self.stats.time_total == timedelta(seconds=15)

    def test_time_listing(self):
        assert self.stats.time_listing == timedelta(seconds=1)

    def test_time_meta(self):
        assert self.stats.time_meta == timedelta(seconds=2)

    def test_time_s3_query(self):
        assert self.stats.time_s3_query == timedelta(seconds=3)

    def test_time_calc(self):
        assert self.stats.time_calc == timedelta(seconds=4)

    def test_time_upload(self):
        assert self.stats.time_upload == timedelta(seconds=5)

    def test_total_files(self):
        assert self.stats.total_files == 11

    def test_total_bytes(self):
        assert self.stats.total_bytes == 12345

    def test_files_uploaded(self):
        assert self.stats.files_uploaded == 10

    def test_bytes_uploaded(self):
        assert self.stats.bytes_uploaded == 789

    def test_error_files(self):
        assert self.stats.error_files == ['foo']

    def test_summary_errors(self):
        expected = dedent("""
        s3sfe v%s run report
        Sunday, January 01, 2017 11:12:28 (myuser on myhost)
        ----------------------------------------------------
        Total Run Time: 0:00:15
        Time Listing Files: 0:00:01
        Time Getting Metadata: 0:00:02
        Time Querying S3: 0:00:03
        Time Calculating Uploads: 0:00:04
        Time Uploading Files: 0:00:05

        Backed-up files on disk: 11 files; 12.3 kB
        Uploaded 10 files; 789 Bytes

        1 files failed uploading:
        foo
        """ % VERSION).strip() + "\n"
        with patch.multiple(
            pbm,
            autospec=True,
            getuser=DEFAULT,
            node=DEFAULT
        ) as mocks:
            mocks['getuser'].return_value = 'myuser'
            mocks['node'].return_value = 'myhost'
            res = self.stats.summary
        assert res == expected
