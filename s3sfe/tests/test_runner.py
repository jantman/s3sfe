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

from s3sfe.runner import main, parse_args, logger
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
            summary=False,
            key_file='kf',
            exclude_file=None
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
                FileSyncer=DEFAULT,
                read_keyfile=DEFAULT
            ) as mocks:
                mocks['parse_args'].return_value = mock_args
                mocks['FileSyncer'].return_value.run.return_value = m_summary
                mocks['read_keyfile'].return_value = 'mykeybinary'
                with patch.object(
                        sys, 'argv',
                        ['foo', '-f', 'kf', 'mybucket', '/foo/bar']
                ):
                    main()
        assert mocks['set_log_info'].mock_calls == []
        assert mocks['set_log_debug'].mock_calls == []
        assert mocks['parse_args'].mock_calls == [
            call(['-f', 'kf', 'mybucket', '/foo/bar'])
        ]
        assert mocks['read_filelist'].mock_calls == [
            call('/foo/bar')
        ]
        assert mocks['read_keyfile'].mock_calls == [
            call('kf')
        ]
        assert mocks['FileSyncer'].mock_calls == [
            call(
                'mybucket',
                prefix=None,
                dry_run=False,
                ssec_key='mykeybinary'
            ),
            call().run(
                mocks['read_filelist'].return_value,
                exclude_paths=[]
            )
        ]
        assert m_summary.mock_calls == []
        assert mocklogger.mock_calls == []

    def test_main_args(self):
        mock_args = Mock(
            dry_run=False,
            verbose=0,
            prefix=None,
            BUCKET_NAME='mybucket',
            FILELIST_PATH='/foo/bar',
            summary=False,
            key_file='kf',
            exclude_file=None
        )

        m_summary = Mock()
        m_summary.summary.return_value = 'foo'

        with patch('%s.logger' % pbm, autospec=True):
            with patch.multiple(
                pbm,
                autospec=True,
                set_log_info=DEFAULT,
                set_log_debug=DEFAULT,
                read_filelist=DEFAULT,
                parse_args=DEFAULT,
                FileSyncer=DEFAULT,
                read_keyfile=DEFAULT
            ) as mocks:
                mocks['parse_args'].return_value = mock_args
                mocks['FileSyncer'].return_value.run.return_value = m_summary
                mocks['read_keyfile'].return_value = 'mykeybinary'
                main(mock_args)
        assert mocks['parse_args'].mock_calls == []

    def test_main_exclude(self):
        mock_args = Mock(
            dry_run=False,
            verbose=1,
            prefix=None,
            BUCKET_NAME='mybucket',
            FILELIST_PATH='/foo/bar',
            summary=False,
            key_file='kf',
            exclude_file='/foo/exc'
        )

        m_summary = Mock()
        m_summary.summary.return_value = 'foo'

        with patch.multiple(
            pbm,
            autospec=True,
            set_log_info=DEFAULT,
            set_log_debug=DEFAULT,
            read_filelist=DEFAULT,
            parse_args=DEFAULT,
            FileSyncer=DEFAULT,
            read_keyfile=DEFAULT
        ) as mocks:
            mocks['parse_args'].return_value = mock_args
            mocks['FileSyncer'].return_value.run.return_value = m_summary
            mocks['read_keyfile'].return_value = 'mykeybinary'
            mocks['read_filelist'].side_effect = [
                ['/foo1', '/foo2'],
                ['/exc1', '/exc2']
            ]
            main(mock_args)
        assert mocks['read_filelist'].mock_calls == [
            call('/foo/bar'),
            call('/foo/exc')
        ]
        assert mocks['FileSyncer'].mock_calls == [
            call(
                'mybucket',
                prefix=None,
                dry_run=False,
                ssec_key='mykeybinary'
            ),
            call().run(
                ['/foo1', '/foo2'],
                exclude_paths=['/exc1', '/exc2']
            )
        ]

    def test_main_verbose(self):
        mock_args = Mock(
            dry_run=False,
            verbose=1,
            prefix=None,
            BUCKET_NAME='mybucket',
            FILELIST_PATH='/foo/bar',
            summary=False,
            key_file='kf',
            exclude_file=None
        )

        m_summary = Mock()
        m_summary.summary.return_value = 'foo'

        with patch.multiple(
            pbm,
            autospec=True,
            set_log_info=DEFAULT,
            set_log_debug=DEFAULT,
            read_filelist=DEFAULT,
            parse_args=DEFAULT,
            FileSyncer=DEFAULT,
            read_keyfile=DEFAULT
        ) as mocks:
            mocks['parse_args'].return_value = mock_args
            mocks['FileSyncer'].return_value.run.return_value = m_summary
            mocks['read_keyfile'].return_value = 'mykeybinary'
            main(mock_args)
        assert mocks['set_log_info'].mock_calls == [call(logger)]

    def test_main_verbose2(self):
        mock_args = Mock(
            dry_run=False,
            verbose=2,
            prefix=None,
            BUCKET_NAME='mybucket',
            FILELIST_PATH='/foo/bar',
            summary=False,
            key_file='kf',
            exclude_file=None
        )

        m_summary = Mock()
        m_summary.summary.return_value = 'foo'

        with patch.multiple(
            pbm,
            autospec=True,
            set_log_info=DEFAULT,
            set_log_debug=DEFAULT,
            read_filelist=DEFAULT,
            parse_args=DEFAULT,
            FileSyncer=DEFAULT,
            read_keyfile=DEFAULT
        ) as mocks:
            mocks['parse_args'].return_value = mock_args
            mocks['FileSyncer'].return_value.run.return_value = m_summary
            mocks['read_keyfile'].return_value = 'mykeybinary'
            main(mock_args)
        assert mocks['set_log_debug'].mock_calls == [call(logger)]

    def test_main_summary(self, capsys):
        mock_args = Mock(
            dry_run=False,
            verbose=0,
            prefix=None,
            BUCKET_NAME='mybucket',
            FILELIST_PATH='/foo/bar',
            summary=True,
            key_file='kf',
            exclude_file=None
        )

        m_summary = Mock(summary='foo')

        with patch('%s.logger' % pbm, autospec=True):
            with patch.multiple(
                pbm,
                autospec=True,
                set_log_info=DEFAULT,
                set_log_debug=DEFAULT,
                read_filelist=DEFAULT,
                parse_args=DEFAULT,
                FileSyncer=DEFAULT,
                read_keyfile=DEFAULT
            ) as mocks:
                mocks['parse_args'].return_value = mock_args
                mocks['FileSyncer'].return_value.run.return_value = m_summary
                mocks['read_keyfile'].return_value = 'mykeybinary'
                main(mock_args)
        out, err = capsys.readouterr()
        assert err == ''
        assert out == "foo\n"


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

    def test_parse_args_no_key_file(self):
        with pytest.raises(RuntimeError):
            parse_args(['-v', 'bktname', '/foo/bar'])

    def test_parse_args_basic(self):
        res = parse_args(['-f', 'kf', 'bktname', '/foo/bar'])
        assert res.BUCKET_NAME == 'bktname'
        assert res.FILELIST_PATH == '/foo/bar'
        assert res.verbose == 0
        assert res.dry_run is False
        assert res.prefix is None
        assert res.summary is False
        assert res.key_file == 'kf'
        assert res.exclude_file is None

    def test_parse_args_verbose1(self):
        res = parse_args(['-f', 'kf', '-v', 'bktname', '/foo/bar'])
        assert res.verbose == 1

    def test_parse_args_verbose2(self):
        res = parse_args(['-f', 'kf', '-vv', 'bktname', '/foo/bar'])
        assert res.verbose == 2

    def test_parse_args_dry_run(self):
        res = parse_args(['-f', 'kf', '-d', 'bktname', '/foo/bar'])
        assert res.dry_run is True

    def test_parse_args_exclude(self):
        res = parse_args(['-f', 'kf', '-e', '/exc/f', 'bktname', '/foo/bar'])
        assert res.exclude_file == '/exc/f'

    def test_parse_args_prefix(self):
        res = parse_args(
            ['-f', 'kf', '--s3-prefix=foo/bar', 'bktname', '/foo/bar']
        )
        assert res.prefix == 'foo/bar'

    def test_parse_args_summary(self):
        res = parse_args(['-f', 'kf', '--summary', 'bktname', '/foo/bar'])
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
