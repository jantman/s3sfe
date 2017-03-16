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
import pytest
import logging
from textwrap import dedent
from freezegun import freeze_time
from datetime import datetime

from s3sfe.utils import (
    set_log_info, set_log_debug, set_log_level_format,
    read_filelist, read_keyfile, dtnow, md5_file
)

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT, mock_open  # noqa
else:
    from unittest.mock import patch, call, Mock, DEFAULT, mock_open  # noqa

pbm = 's3sfe.utils'


class TestMd5File(object):

    def test_md5_file(self):
        data = ('a' * 128) + ('b' * 128) + ('c' * 30)
        with patch(
            '%s.open' % pbm, mock_open(read_data=data), create=True
        ) as m_open:
            with patch('%s.md5' % pbm, autospec=True) as mock_md5:
                mock_md5.return_value.hexdigest.return_value = 'abc123'
                res = md5_file('/foo/bar')
        assert res == 'abc123'
        assert m_open.mock_calls == [
            call('/foo/bar', 'rb'),
            call().__enter__(),
            call().read(128),
            call().read(128),
            call().__exit__(None, None, None)
        ]
        assert mock_md5.mock_calls == [
            call(),
            call().update(data),
            call().hexdigest()
        ]


class TestDtnow(object):

    @freeze_time('2017-01-02 13:24:36')
    def test_dtnow(self):
        assert dtnow() == datetime(2017, 1, 2, 13, 24, 36)


class TestLogging(object):

    def test_set_log_info(self):
        mockl = Mock()
        with patch('%s.set_log_level_format' % pbm) as mock_set:
            set_log_info(mockl)
        assert mock_set.mock_calls == [
            call(
                mockl, logging.INFO,
                '%(asctime)s %(levelname)s:%(name)s:%(message)s'
            )
        ]

    def test_set_log_debug(self):
        mockl = Mock()
        with patch('%s.set_log_level_format' % pbm) as mock_set:
            set_log_debug(mockl)
        assert mock_set.mock_calls == [
            call(mockl, logging.DEBUG,
                 "%(asctime)s [%(levelname)s %(filename)s:%(lineno)s - "
                 "%(name)s.%(funcName)s() ] %(message)s")
        ]

    def test_set_log_level_format(self):
        mock_handler = Mock(spec_set=logging.Handler)
        mock_l = Mock(spec_set=logging._loggerClass)
        type(mock_l).handlers = [mock_handler]
        with patch('%s.logging.Formatter' % pbm) as mock_formatter:
            set_log_level_format(mock_l, 5, 'foo')
        assert mock_formatter.mock_calls == [
            call(fmt='foo')
        ]
        assert mock_handler.mock_calls == [
            call.setFormatter(mock_formatter.return_value)
        ]
        assert mock_l.mock_calls == [
            call.setLevel(5)
        ]


class TestReadFilelist(object):

    content = dedent("""
    # foo
    /path/one
    # bar
    /path/two.txt
    /foo/baz
    """)

    def test_fail(self):
        with patch('%s.os.path.exists' % pbm, autospec=True) as m_exists:
            with patch(
                '%s.open' % pbm, mock_open(read_data=self.content), create=True
            ) as m_open:
                m_exists.return_value = False
                with pytest.raises(RuntimeError):
                    read_filelist('/my/path')
        assert m_exists.mock_calls == [call('/my/path')]
        assert m_open.mock_calls == []

    def test_pass(self):
        with patch('%s.os.path.exists' % pbm, autospec=True) as m_exists:
            with patch(
                '%s.open' % pbm, mock_open(read_data=self.content), create=True
            ) as m_open:
                m_exists.return_value = True
                res = read_filelist('/my/path')
        assert m_exists.mock_calls == [call('/my/path')]
        assert m_open.mock_calls == [
            call('/my/path', 'r'),
            call().__enter__(),
            call().readlines(),
            call().__exit__(None, None, None)
        ]
        assert sorted(res) == ['/foo/baz', '/path/one', '/path/two.txt']


class TestReadKeyFile(object):

    def test_ok(self):
        content = bytes('abcdefghijklmnopqrstuvwxyz012345', 'utf8')
        with patch('%s.open' % pbm, create=True) as m_open:
            m_read = m_open.return_value.__enter__.return_value.read
            m_read.return_value = content
            res = read_keyfile('/my/path')
        assert res == content
        assert m_open.mock_calls == [
            call('/my/path', 'rb'),
            call().__enter__(),
            call().__enter__().read(),
            call().__exit__(None, None, None)
        ]

    def test_wrong_length(self):
        content = bytes('abc123', 'utf8')
        with patch('%s.open' % pbm, create=True) as m_open:
            m_read = m_open.return_value.__enter__.return_value.read
            m_read.return_value = content
            with pytest.raises(RuntimeError) as exc:
                read_keyfile('/my/path')
            exc_str = 'Key file must be 32 bytes; /my/path is 6 bytes'
            assert exc_str in str(exc)
        assert m_open.mock_calls == [
            call('/my/path', 'rb'),
            call().__enter__(),
            call().__enter__().read(),
            call().__exit__(None, None, None)
        ]
