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
import argparse
import logging

from s3sfe.version import PROJECT_URL, VERSION
from s3sfe.filesyncer import FileSyncer
from s3sfe.utils import (
    set_log_info, set_log_debug, read_filelist, read_keyfile
)

FORMAT = "[%(asctime)s %(levelname)s] %(message)s"
logging.basicConfig(level=logging.WARNING, format=FORMAT)
logger = logging.getLogger()

# suppress boto3 internal logging below WARNING level
boto3_log = logging.getLogger("boto3")
boto3_log.setLevel(logging.WARNING)
boto3_log.propagate = True

# suppress botocore internal logging below WARNING level
botocore_log = logging.getLogger("botocore")
botocore_log.setLevel(logging.WARNING)
botocore_log.propagate = True


def parse_args(argv):
    """
    Use Argparse to parse command-line arguments.

    :param argv: list of arguments to parse (``sys.argv[1:]``)
    :type argv: list
    :return: parsed arguments
    :rtype: :py:class:`argparse.Namespace`
    """
    p = argparse.ArgumentParser(
        description='s3sfe (S3 Sync Filelist Encrypted) file restoration '
                    'script - <%s>' % PROJECT_URL
    )
    p.add_argument('-d', '--dry-run', dest='dry_run', action='store_true',
                   default=False,
                   help='do not actually restore; only log what would be done')
    p.add_argument('-v', '--verbose', dest='verbose', action='count',
                   default=0,
                   help='verbose output. specify twice for debug-level output.')
    p.add_argument('-V', '--version', action='version',
                   version='s3sfe v%s <%s>' % (VERSION, PROJECT_URL))
    p.add_argument('-p', '--s3-prefix', dest='prefix', action='store',
                   default=None, type=str,
                   help='prefix to prepend to file paths when creating S3 keys')
    p.add_argument('-f', '--key-file', dest='key_file', action='store',
                   type=str, default=None,
                   help='path to AES256 key file. This should be a binary file'
                        'containing a 32-byte encryption key to use for SSE-C')
    p.add_argument('-l', '--filelist-path', dest='FILELIST_PATH', type=str,
                   action='store', default=None,
                   help='Path to filelist specifying which files or paths to '
                        'restore; same format as s3sfe FILELIST_PATH argument. '
                        'This option cannot be specified in combination with '
                        'PATHs.')
    p.add_argument('BUCKET_NAME', action='store', type=str,
                   help='Name of S3 bucket to upload to')
    p.add_argument('LOCAL_PREFIX', action='store', type=str,
                   help='Local filesystem path prefix to download/restore '
                        'files under ; set to "/" to overwrite original source '
                        'paths')
    p.add_argument('PATH', action='store', type=str, default=None, nargs='?',
                   help='One specific path or path prefix (directory) to '
                        'restore; can be specified multiple times. This option '
                        'cannot be specified in combination with '
                        '-l|--filelist-path.')
    args = p.parse_args(argv)
    if args.key_file is None:
        raise RuntimeError('Error: -f|--key-file must be specified.')
    if args.PATH is None and args.FILELIST_PATH is None:
        raise RuntimeError('Error: you must specify either PATH or '
                           '-l|--filelist-path')
    if args.PATH is not None and args.FILELIST_PATH is not None:
        raise RuntimeError('Error: you must specify either PATH or '
                           '-l|--filelist-path')
    return args


def main(args=None):
    """
    Main entry point
    """
    # parse args
    if args is None:
        args = parse_args(sys.argv[1:])

    # set logging level
    if args.verbose > 1:
        set_log_debug()
    elif args.verbose == 1:
        set_log_info()

    s = FileSyncer(
        args.BUCKET_NAME,
        prefix=args.prefix,
        dry_run=args.dry_run,
        ssec_key=read_keyfile(args.key_file)
    )
    files = read_filelist(args.FILELIST_PATH)
    stats = s.run(files)
    if args.summary:
        print(stats.summary)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    main(args)
