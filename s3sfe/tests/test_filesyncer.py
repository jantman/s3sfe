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

from s3sfe.filesyncer import FileSyncer

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT, mock_open  # noqa
else:
    from unittest.mock import patch, call, Mock, DEFAULT, mock_open  # noqa

pbm = 's3sfe.filesyncer'
pb = '%s.FileSyncer' % pbm


class TestInit(object):

    def test_init_default(self):
        m_s3 = Mock()
        with patch('%s.S3Wrapper' % pbm, autospec=True) as mock_s3:
            mock_s3.return_value = m_s3
            cls = FileSyncer('bname')
        assert cls.s3 == m_s3
        assert mock_s3.mock_calls == [
            call('bname', prefix='', dry_run=False, ssec_key=None)
        ]
        assert cls._dry_run is False

    def test_init_prefix_no_slash(self):
        m_s3 = Mock()
        with patch('%s.S3Wrapper' % pbm, autospec=True) as mock_s3:
            mock_s3.return_value = m_s3
            cls = FileSyncer('bname', prefix='foo', ssec_key='foo')
        assert cls.s3 == m_s3
        assert mock_s3.mock_calls == [
            call('bname', prefix='foo', dry_run=False, ssec_key='foo')
        ]

    def test_init_args(self):
        m_s3 = Mock()
        with patch('%s.S3Wrapper' % pbm, autospec=True) as mock_s3:
            mock_s3.return_value = m_s3
            cls = FileSyncer('bname', prefix='/foo', dry_run=True)
        assert cls.s3 == m_s3
        assert mock_s3.mock_calls == [
            call('bname', prefix='/foo', dry_run=True, ssec_key=None)
        ]
        assert cls._dry_run is True


class TestListAllFiles(object):

    def setup(self):
        with patch('%s.S3Wrapper' % pbm, autospec=True) as mock_s3:
            self.cls = FileSyncer('bname')
            self.mock_s3 = mock_s3

    def test_simple(self):
        paths = [
            '/bar',
            '/foo/bar',
            '/foo/baz.txt',
            '/foo/notfile',
            '/foo/bar/one'
        ]

        def se_listdir(_, p):
            return ['/foo/bar/one', '/foo/bar/two', '/foo/bar/three/four']

        def se_exists(p):
            if p in [
                '/foo/bar', '/foo/baz.txt', '/foo/notfile', '/foo/bar/one'
            ]:
                return True
            return False

        def se_isfile(p):
            if p == '/foo/baz.txt' or p == '/foo/bar/one':
                return True
            return False

        def se_isdir(p):
            if p == '/foo/bar':
                return True
            return False

        with patch('%s.logger' % pbm) as mock_logger:
            with patch('%s._listdir' % pb, autospec=True) as mock_listdir:
                mock_listdir.side_effect = se_listdir
                with patch.multiple(
                    '%s.os.path' % pbm,
                    autospec=True,
                    exists=DEFAULT,
                    isfile=DEFAULT,
                    isdir=DEFAULT
                ) as mock_os:
                    mock_os['exists'].side_effect = se_exists
                    mock_os['isfile'].side_effect = se_isfile
                    mock_os['isdir'].side_effect = se_isdir
                    res = self.cls._list_all_files(paths)
        assert sorted(res) == sorted([
            '/foo/bar/one',
            '/foo/bar/two',
            '/foo/bar/three/four',
            '/foo/baz.txt'
        ])
        assert mock_os['exists'].mock_calls == [
            call(x) for x in paths
        ]
        assert mock_os['isfile'].mock_calls == [
            call('/foo/bar'),
            call('/foo/baz.txt'),
            call('/foo/notfile'),
            call('/foo/bar/one')
        ]
        assert mock_os['isdir'].mock_calls == [
            call('/foo/bar'),
            call('/foo/notfile')
        ]
        assert mock_listdir.mock_calls == [
            call(self.cls, '/foo/bar')
        ]
        assert mock_logger.mock_calls == [
            call.info('Listing files under %d paths', 5),
            call.warning('Skipping non-existent path: %s', '/bar'),
            call.debug('Found %d files under %s', 3, '/foo/bar'),
            call.warning('Skipping unknown path type: %s', '/foo/notfile'),
            call.debug('Done finding candidate files.')
        ]


class TestFileMeta(object):

    def setup(self):
        with patch('%s.S3Wrapper' % pbm, autospec=True) as mock_s3:
            self.cls = FileSyncer('bname')
            self.mock_s3 = mock_s3

    def test_simple(self):
        with patch('%s.md5_file' % pbm, autospec=True) as mock_md5:
            mock_md5.side_effect = [
                'abcd1234a',
                'abcd1234b'
            ]
            with patch('%s.os.path.getsize' % pbm, autospec=True) as mock_sz:
                with patch('%s.os.path.getmtime' % pbm,
                           autospec=True) as mock_mtime:
                    mock_sz.side_effect = [6789, 1234]
                    mock_mtime.side_effect = [
                        123456789.0123,
                        987654321.5432
                    ]
                    res = self.cls._file_meta(['a', 'b'])
        assert res == {
            'a': (6789, 123456789.0123, 'abcd1234a'),
            'b': (1234, 987654321.5432, 'abcd1234b')
        }
        assert mock_md5.mock_calls == [call('a'), call('b')]
        assert mock_sz.mock_calls == [call('a'), call('b')]
        assert mock_mtime.mock_calls == [call('a'), call('b')]


class TestListdir(object):

    def setup(self):
        with patch('%s.S3Wrapper' % pbm, autospec=True) as mock_s3:
            self.cls = FileSyncer('bname')
            self.mock_s3 = mock_s3

    def test_simple(self):
        result = [
            ('/foo', ['bar'], ['foo1', 'foo2']),
            ('/foo/bar', ['baz', 'blam'], ['foobar1']),
            ('/foo/bar/baz', [], ['foobarbaz1', 'foobarbaz2'])
        ]
        expected = [
            '/foo/foo1', '/foo/foo2',
            '/foo/bar/foobar1',
            '/foo/bar/baz/foobarbaz1',
            '/foo/bar/baz/foobarbaz2'
        ]
        with patch('%s.os.walk' % pbm, autospec=True) as mock_walk:
            mock_walk.return_value = iter(result)
            res = self.cls._listdir('/foo')
        assert sorted(res) == sorted(expected)
        assert mock_walk.mock_calls == [call('/foo')]


class TestFilesToUpload(object):

    def setup(self):
        with patch('%s.S3Wrapper' % pbm, autospec=True) as mock_s3:
            self.cls = FileSyncer('bname')
            self.mock_s3 = mock_s3

    def test_files_to_upload(self):
        local_files = {
            '/foo/one': (111, 12345.67, 'aaaa'),
            '/foo/two': (222, 23456.78, 'bbbb'),
            '/foo/three': (333, 34567.89, 'cccc'),
        }
        s3_files = {
            '/foo/one': (444, 45678.9, 'dddd'),
            '/foo/three': (555, 456789.01, 'cccc')
        }
        res = self.cls._files_to_upload(local_files, s3_files)
        assert res == {
            '/foo/one': (111, 12345.67, 'aaaa'),
            '/foo/two': (222, 23456.78, 'bbbb')
        }


class TestUploadFiles(object):

    def setup(self):
        with patch('%s.S3Wrapper' % pbm, autospec=True) as mock_s3:
            self.cls = FileSyncer('bname')
            self.mock_s3 = mock_s3

    def test_upload_files(self):
        files = {
            '/foo/one': (111, 12345.67, 'aaaa'),
            '/foo/two': (222, 23456.78, 'bbbb'),
            '/foo/three': (333, 34567.89, 'cccc'),
        }

        def se_put(f, sz, mt, md):
            if f == '/foo/two':
                raise RuntimeError()
            return None

        self.mock_s3.return_value.put_file.side_effect = se_put
        res = self.cls._upload_files(files)
        assert res == (['/foo/two'], 444)


class TestRun(object):

    def setup(self):
        with patch('%s.S3Wrapper' % pbm, autospec=True) as mock_s3:
            self.cls = FileSyncer('bname')
            self.mock_s3 = mock_s3

    def test_simple(self):
        paths = ['a', 'b']
        s3_files = {
            'one': (1, 2, 'three'),
            'two': (4, 5, 'six')
        }
        local_files = {
            'one': (1, 2, 'three'),
            'two': (4, 5, 'NOTsix'),
            'three': (6, 7, 'eight')
        }
        to_upload = {
            'two': (4, 5, 'NOTsix'),
            'three': (6, 7, 'eight')
        }
        self.mock_s3.return_value.get_filelist.return_value = s3_files
        dates = [
            'dt_start',
            'dt_meta',
            'dt_query',
            'dt_calc',
            'dt_upload',
            'dt_end'
        ]
        with patch('%s.dtnow' % pbm, autospec=True) as mock_dtnow:
            mock_dtnow.side_effect = dates
            with patch('%s.RunStats' % pbm, autospec=True) as mock_stats:
                with patch.multiple(
                    pb,
                    autospec=True,
                    _list_all_files=DEFAULT,
                    _file_meta=DEFAULT,
                    _files_to_upload=DEFAULT,
                    _upload_files=DEFAULT
                ) as mocks:
                    mocks['_list_all_files'].return_value = [
                        'one', 'two', 'three']
                    mocks['_file_meta'].return_value = local_files
                    mocks['_files_to_upload'].return_value = to_upload
                    mocks['_upload_files'].return_value = (['one'], 123)
                    res = self.cls.run(paths)
        assert mocks['_list_all_files'].mock_calls == [
            call(self.cls, paths)
        ]
        assert mocks['_file_meta'].mock_calls == [
            call(self.cls, ['one', 'two', 'three'])
        ]
        assert self.mock_s3.return_value.get_filelist.mock_calls == [call()]
        assert mocks['_files_to_upload'].mock_calls == [
            call(self.cls, local_files, s3_files)
        ]
        assert mocks['_upload_files'].mock_calls == [
            call(self.cls, to_upload)
        ]
        assert mock_stats.mock_calls == [
            call(
                'dt_start', 'dt_meta', 'dt_query', 'dt_calc', 'dt_upload',
                'dt_end', 3, 2, ['one'], 11, 123, dry_run=False
            )
        ]
        assert res == mock_stats.return_value
