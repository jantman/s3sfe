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

from s3sfe.s3 import S3Wrapper
from s3sfe.version import VERSION

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, PropertyMock, MagicMock  # noqa
else:
    from unittest.mock import patch, call, Mock, PropertyMock, MagicMock  # noqa

pbm = 's3sfe.s3'
pb = '%s.S3Wrapper' % pbm


class TestInit(object):

    def test_init_default(self):
        with patch('%s.boto3.resource' % pbm, autospec=True) as m_boto_r:
            with patch('%s.boto3.client' % pbm, autospec=True) as m_boto_c:
                with patch('%s._encode_key' % pb, autospec=True) as m_ek:
                    m_ek.return_value = ('foo', 'bar')
                    cls = S3Wrapper('bname')
        assert cls._bucket_name == 'bname'
        assert cls._prefix == ''
        assert cls._dry_run is False
        assert cls._key == 'foo'
        assert cls._keymd5 == 'bar'
        assert m_boto_r.mock_calls == [call('s3')]
        assert m_boto_c.mock_calls == [call('s3')]
        assert m_ek.mock_calls == [call(cls, None)]
        assert cls._s3 == m_boto_r.return_value
        assert cls._s3client == m_boto_c.return_value

    def test_init_nondefault(self):
        with patch('%s.boto3.resource' % pbm, autospec=True) as m_boto_r:
            with patch('%s.boto3.client' % pbm, autospec=True) as m_boto_c:
                with patch('%s._encode_key' % pb, autospec=True) as m_ek:
                    m_ek.return_value = ('foo', 'bar')
                    cls = S3Wrapper(
                        'bktname', prefix='/', dry_run=True, ssec_key='foobar'
                    )
        assert cls._bucket_name == 'bktname'
        assert cls._prefix == '/'
        assert cls._dry_run is True
        assert cls._key == 'foo'
        assert cls._keymd5 == 'bar'
        assert m_boto_r.mock_calls == [call('s3')]
        assert m_boto_c.mock_calls == [call('s3')]
        assert m_ek.mock_calls == [call(cls, 'foobar')]
        assert cls._s3 == m_boto_r.return_value
        assert cls._s3client == m_boto_c.return_value


class TestEncodeKey(object):

    def setup(self):
        with patch('%s.boto3.resource' % pbm, autospec=True):
            with patch('%s.boto3.client' % pbm, autospec=True):
                with patch('%s._encode_key' % pb, autospec=True) as m_ek:
                    m_ek.return_value = ('key', 'md5')
                    self.cls = S3Wrapper('bname')

    def test_encode_key(self):
        key = bytes('foo', 'utf8')
        expected_key = 'Zm9v'
        expected_md5 = 'rL0Y20zC+Fzt72VPzMSk2A=='
        res = self.cls._encode_key(key)
        assert res == (expected_key, expected_md5)


class TestGetFileList(object):

    def setup(self):
        with patch('%s.boto3.resource' % pbm, autospec=True) as m_boto_r:
            with patch('%s.boto3.client' % pbm, autospec=True) as m_boto_c:
                with patch('%s._encode_key' % pb, autospec=True) as m_ek:
                    m_ek.return_value = ('key', 'md5')
                    self.cls = S3Wrapper('bname')
        m_k1 = Mock(key='/foo/key/1', name='m_k1')
        m_k2 = Mock(key='/foo/key/2', name='m_k2')
        m_objects = MagicMock()
        m_objects.filter = MagicMock(return_value=[m_k1, m_k2])
        m_objects.all = MagicMock(return_value=[m_k1, m_k2])
        mock_bucket = Mock()
        mock_bucket.objects = m_objects
        m_boto_r.return_value.Bucket.return_value = mock_bucket
        self.mock_res = m_boto_r
        self.mock_client = m_boto_c

    def test_get_filelist_empty_prefix(self):
        with patch('%s._get_metadata' % pb, autospec=True) as m_meta:
            m_meta.side_effect = [{'meta': '1'}, {'meta': '2'}]
            res = self.cls.get_filelist()
        assert res == {
            '/foo/key/1': {'meta': '1'},
            '/foo/key/2': {'meta': '2'}
        }
        assert self.mock_res.mock_calls == [
            call('s3'),
            call().Bucket('bname'),
            call().Bucket().objects.all(),
        ]

    def test_get_filelist_prefix(self):
        self.cls._prefix = '/foo'
        with patch('%s._get_metadata' % pb, autospec=True) as m_meta:
            m_meta.side_effect = [{'meta': '1'}, {'meta': '2'}]
            res = self.cls.get_filelist()
        assert res == {
            '/key/1': {'meta': '1'},
            '/key/2': {'meta': '2'}
        }
        assert self.mock_res.mock_calls == [
            call('s3'),
            call().Bucket('bname'),
            call().Bucket().objects.filter(Prefix='/foo'),
        ]


class TestGetMetadata(object):

    def setup(self):
        with patch('%s.boto3.resource' % pbm, autospec=True):
            with patch('%s.boto3.client' % pbm, autospec=True) as m_boto_c:
                with patch('%s._encode_key' % pb, autospec=True) as m_ek:
                    m_ek.return_value = ('key', 'md5')
                    self.cls = S3Wrapper('bname')
        self.mock_client = m_boto_c

    def test_get_metadata(self):
        self.mock_client.return_value.head_object.return_value = {
            'Metadata': {'foo': 'bar'}
        }
        assert self.cls._get_metadata('/key/one') == {'foo': 'bar'}
        assert self.mock_client.mock_calls == [
            call('s3'),
            call().head_object(
                Bucket='bname',
                Key='/key/one',
                SSECustomerAlgorithm='AES256',
                SSECustomerKey='key',
                SSECustomerKeyMD5='md5'
            )
        ]


class TestKeyForPath(object):

    def setup(self):
        with patch('%s.boto3.resource' % pbm, autospec=True):
            with patch('%s.boto3.client' % pbm, autospec=True):
                with patch('%s._encode_key' % pb, autospec=True) as m_ek:
                    m_ek.return_value = ('key', 'md5')
                    self.cls = S3Wrapper('bname')

    def test_no_prefix(self):
        self.cls._prefix = ''
        assert self.cls._key_for_path('/foo/bar') == '/foo/bar'

    def test_with_prefix_slash(self):
        self.cls._prefix = '/pre/fix'
        assert self.cls._key_for_path('/foo/bar') == '/pre/fix/foo/bar'

    def test_with_prefix(self):
        self.cls._prefix = 'pre/fix'
        assert self.cls._key_for_path('/foo/bar') == 'pre/fix/foo/bar'


class TestPutFile(object):

    def setup(self):
        with patch('%s.boto3.resource' % pbm, autospec=True) as m_boto_r:
            with patch('%s.boto3.client' % pbm, autospec=True):
                with patch('%s._encode_key' % pb, autospec=True) as m_ek:
                    m_ek.return_value = ('key', 'md5')
                    self.cls = S3Wrapper('bname')
        mock_bucket = Mock()
        m_boto_r.return_value.Bucket.return_value = mock_bucket
        self.mock_res = m_boto_r

    def test_put(self):
        with patch('%s._key_for_path' % pb, autospec=True) as m_kfp:
            m_kfp.return_value = '/key/for/path'
            self.cls.put_file('/f/path', 1234, 5678, 'fmd5')
        assert self.mock_res.mock_calls == [
            call('s3'),
            call().Bucket('bname'),
            call().Bucket().upload_file(
                '/f/path',
                '/key/for/path',
                ExtraArgs={
                    'ACL': 'private',
                    'SSECustomerAlgorithm': 'AES256',
                    'SSECustomerKey': 'key',
                    'SSECustomerKeyMD5': 'md5',
                    'Metadata': {
                        'UploadedBy': 's3sfe-%s' % VERSION,
                        'size_b': '%s' % 1234,
                        'mtime': '%s' % 5678,
                        'md5sum': 'fmd5'
                    }
                }
            ),
        ]
        assert m_kfp.mock_calls == [call(self.cls, '/f/path')]

    def test_dry_run(self):
        self.cls._dry_run = True
        with patch('%s._key_for_path' % pb, autospec=True) as m_kfp:
            m_kfp.return_value = '/key/for/path'
            self.cls.put_file('/f/path', 1234, 5678, 'fmd5')
        assert self.mock_res.mock_calls == [
            call('s3'),
            call().Bucket('bname')
        ]
        assert m_kfp.mock_calls == [call(self.cls, '/f/path')]


class TestGetFile(object):

    def setup(self):
        with patch('%s.boto3.resource' % pbm, autospec=True) as m_boto_r:
            with patch('%s.boto3.client' % pbm, autospec=True):
                with patch('%s._encode_key' % pb, autospec=True) as m_ek:
                    m_ek.return_value = ('key', 'md5')
                    self.cls = S3Wrapper('bname')
        mock_bucket = Mock()
        m_boto_r.return_value.Bucket.return_value = mock_bucket
        self.mock_res = m_boto_r

    def test_put(self):
        with patch('%s._key_for_path' % pb, autospec=True) as m_kfp:
            with patch('%s.os.path.exists' % pbm, autospec=True) as m_exists:
                with patch('%s.os.makedirs' % pbm, autospec=True) as m_mkdirs:
                    m_kfp.return_value = '/key/for/path'
                    m_exists.return_value = True
                    self.cls.get_file('/f/path')
        assert self.mock_res.mock_calls == [
            call('s3'),
            call().Bucket('bname'),
            call().Bucket().download_file(
                '/key/for/path',
                '/f/path',
                ExtraArgs={
                    'SSECustomerAlgorithm': 'AES256',
                    'SSECustomerKey': 'key',
                    'SSECustomerKeyMD5': 'md5'
                }
            ),
        ]
        assert m_kfp.mock_calls == [call(self.cls, '/f/path')]
        assert m_exists.mock_calls == [call('/f')]
        assert m_mkdirs.mock_calls == []

    def test_dry_run(self):
        self.cls._dry_run = True
        with patch('%s._key_for_path' % pb, autospec=True) as m_kfp:
            with patch('%s.os.path.exists' % pbm, autospec=True) as m_exists:
                with patch('%s.os.makedirs' % pbm, autospec=True) as m_mkdirs:
                    m_kfp.return_value = '/key/for/path'
                    m_exists.return_value = True
                    self.cls.get_file('/f/path')
        assert self.mock_res.mock_calls == [
            call('s3'),
            call().Bucket('bname')
        ]
        assert m_kfp.mock_calls == [call(self.cls, '/f/path')]
        assert m_exists.mock_calls == []
        assert m_mkdirs.mock_calls == []

    def test_local_prefix(self):
        with patch('%s._key_for_path' % pb, autospec=True) as m_kfp:
            with patch('%s.os.path.exists' % pbm, autospec=True) as m_exists:
                with patch('%s.os.makedirs' % pbm, autospec=True) as m_mkdirs:
                    m_kfp.return_value = '/key/for/path'
                    m_exists.return_value = False
                    self.cls.get_file('/f/path', local_prefix='/foo')
        assert self.mock_res.mock_calls == [
            call('s3'),
            call().Bucket('bname'),
            call().Bucket().download_file(
                '/key/for/path',
                '/foo/f/path',
                ExtraArgs={
                    'SSECustomerAlgorithm': 'AES256',
                    'SSECustomerKey': 'key',
                    'SSECustomerKeyMD5': 'md5'
                }
            ),
        ]
        assert m_kfp.mock_calls == [call(self.cls, '/f/path')]
        assert m_exists.mock_calls == [call('/foo/f')]
        assert m_mkdirs.mock_calls == [call('/foo/f')]

    def test_local_prefix_rel_path(self):
        with patch('%s._key_for_path' % pb, autospec=True) as m_kfp:
            with patch('%s.os.path.exists' % pbm, autospec=True) as m_exists:
                with patch('%s.os.makedirs' % pbm, autospec=True) as m_mkdirs:
                    m_kfp.return_value = '/key/for/path'
                    m_exists.return_value = False
                    self.cls.get_file('f/path', local_prefix='/foo')
        assert self.mock_res.mock_calls == [
            call('s3'),
            call().Bucket('bname'),
            call().Bucket().download_file(
                '/key/for/path',
                '/foo/f/path',
                ExtraArgs={
                    'SSECustomerAlgorithm': 'AES256',
                    'SSECustomerKey': 'key',
                    'SSECustomerKeyMD5': 'md5'
                }
            ),
        ]
        assert m_kfp.mock_calls == [call(self.cls, 'f/path')]
        assert m_exists.mock_calls == [call('/foo/f')]
        assert m_mkdirs.mock_calls == [call('/foo/f')]


class TestPathForKey(object):

    def setup(self):
        with patch('%s.boto3.resource' % pbm, autospec=True):
            with patch('%s.boto3.client' % pbm, autospec=True):
                with patch('%s._encode_key' % pb, autospec=True) as m_ek:
                    m_ek.return_value = ('key', 'md5')
                    self.cls = S3Wrapper('bname')

    def test_no_prefix(self):
        self.cls._prefix = ''
        assert self.cls._path_for_key('/p/k') == '/p/k'

    def test_prefix_no_slash(self):
        self.cls._prefix = 'foo'
        assert self.cls._path_for_key('foo/foo/bar') == '/foo/bar'

    def test_prefix_with_slash(self):
        self.cls._prefix = 'prefix/'
        assert self.cls._path_for_key('prefix/foo/bar') == '/foo/bar'
