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
import logging
import pytest
from textwrap import dedent

from s3sfe.runner import (
    main, parse_args, set_log_info, set_log_debug, set_log_level_format,
    read_filelist
)
from s3sfe.version import PROJECT_URL, VERSION

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT, mock_open  # noqa
else:
    from unittest.mock import patch, call, Mock, DEFAULT, mock_open  # noqa

pbm = 's3sfe.runner'


class TestMain(object):

    def test_main_simple(self):
        mock_args = Mock(
            dry_run=False,
            verbose=0,
            prefix=None,
            BUCKET_NAME='mybucket',
            FILELIST_PATH='/foo/bar',
            summary=False
        )

        m_summary = Mock()
        m_summary.summary.return_value = 'foo'

        with patch('%s.logger' % pbm, autospec=True) as mocklogger:
            with patch.multiple(
                pbm,
                autospec=True,
                set_log_info=DEFAULT,
                set_log_debug=DEFAULT,
                read_filelist=DEFAULT,
                parse_args=DEFAULT,
                FileSyncer=DEFAULT
            ) as mocks:
                mocks['parse_args'].return_value = mock_args
                mocks['FileSyncer'].return_value.run.return_value = m_summary
                with patch.object(sys, 'argv', ['foo', 'mybucket', '/foo/bar']):
                    main()
        assert mocks['set_log_info'].mock_calls == []
        assert mocks['set_log_debug'].mock_calls == []
        assert mocks['parse_args'].mock_calls == [
            call(['mybucket', '/foo/bar'])
        ]
        assert mocks['read_filelist'].mock_calls == [
            call('/foo/bar')
        ]
        assert mocks['FileSyncer'].mock_calls == [
            call('mybucket', prefix=None, dry_run=False),
            call().run(mocks['read_filelist'].return_value)
        ]
        assert mocklogger.mock_calls == []


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


class TestParseArgs(object):

    def test_parse_args_no_args(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            parse_args([])
        assert excinfo.value.code == 2
        out, err = capsys.readouterr()
        assert (
            'too few arguments' in err or
            'the following arguments are required' in err
        )
        assert out == ''

    def test_parse_args_one_arg(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            parse_args(['foo'])
        assert excinfo.value.code == 2
        out, err = capsys.readouterr()
        assert (
            'too few arguments' in err or
            'the following arguments are required' in err
        )
        assert out == ''

    @pytest.mark.skipif(sys.version_info[0:2] != (2, 7), reason='py27 only')
    def test_parse_args_none_py27(self, capsys):
        """this just exists to get coverage to pass on py27"""
        m_args = Mock(BUCKET_NAME=None)
        with pytest.raises(SystemExit) as excinfo:
            with patch('%s.argparse.ArgumentParser' % pbm) as mock_parser:
                mock_parser.return_value.parse_args.return_value = m_args
                parse_args([])
        out, err = capsys.readouterr()
        assert out == ''
        assert err == "ERROR: too few arguments\n"
        assert excinfo.value.code == 2

    def test_parse_args_basic(self):
        res = parse_args(['bktname', '/foo/bar'])
        assert res.BUCKET_NAME == 'bktname'
        assert res.FILELIST_PATH == '/foo/bar'
        assert res.verbose == 0
        assert res.dry_run is False
        assert res.prefix is None
        assert res.summary is False

    def test_parse_args_verbose1(self):
        res = parse_args(['-v', 'bktname', '/foo/bar'])
        assert res.verbose == 1

    def test_parse_args_verbose2(self):
        res = parse_args(['-vv', 'bktname', '/foo/bar'])
        assert res.verbose == 2

    def test_parse_args_dry_run(self):
        res = parse_args(['-d', 'bktname', '/foo/bar'])
        assert res.dry_run is True

    def test_parse_args_prefix(self):
        res = parse_args(['--s3-prefix=foo/bar', 'bktname', '/foo/bar'])
        assert res.prefix == 'foo/bar'

    def test_parse_args_summary(self):
        res = parse_args(['--summary', 'bktname', '/foo/bar'])
        assert res.summary is True

    def test_parse_args_version(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            parse_args(['-V'])
        assert excinfo.value.code == 0
        expected = "s3sfe v%s <%s>\n" % (
            VERSION, PROJECT_URL
        )
        out, err = capsys.readouterr()
        if (sys.version_info[0] < 3 or
                (sys.version_info[0] == 3 and sys.version_info[1] < 4)):
            assert out == ''
            assert err == expected
        else:
            assert out == expected
            assert err == ''


class TestLogging(object):

    def test_set_log_info(self):
        with patch('%s.set_log_level_format' % pbm) as mock_set:
            set_log_info()
        assert mock_set.mock_calls == [
            call(logging.INFO, '%(asctime)s %(levelname)s:%(name)s:%(message)s')
        ]

    def test_set_log_debug(self):
        with patch('%s.set_log_level_format' % pbm) as mock_set:
            set_log_debug()
        assert mock_set.mock_calls == [
            call(logging.DEBUG,
                 "%(asctime)s [%(levelname)s %(filename)s:%(lineno)s - "
                 "%(name)s.%(funcName)s() ] %(message)s")
        ]

    def test_set_log_level_format(self):
        mock_handler = Mock(spec_set=logging.Handler)
        with patch('%s.logger' % pbm) as mock_logger:
            with patch('%s.logging.Formatter' % pbm) as mock_formatter:
                type(mock_logger).handlers = [mock_handler]
                set_log_level_format(5, 'foo')
        assert mock_formatter.mock_calls == [
            call(fmt='foo')
        ]
        assert mock_handler.mock_calls == [
            call.setFormatter(mock_formatter.return_value)
        ]
        assert mock_logger.mock_calls == [
            call.setLevel(5)
        ]
