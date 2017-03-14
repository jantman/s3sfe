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
import os

from s3sfe.version import PROJECT_URL, VERSION
from s3sfe.filesyncer import FileSyncer

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
        description='s3sfe (S3 Sync Filelist Encrypted) Sync a list of files '
                    'to S3, using server-side encryption with '
                    'customer-provided keys. - <%s>' % PROJECT_URL
    )
    p.add_argument('-d', '--dry-run', dest='dry_run', action='store_true',
                   default=False,
                   help='do not actually upload; only log what would be done')
    p.add_argument('-v', '--verbose', dest='verbose', action='count',
                   default=0,
                   help='verbose output. specify twice for debug-level output.')
    p.add_argument('-V', '--version', action='version',
                   version='s3sfe v%s <%s>' % (VERSION, PROJECT_URL))
    p.add_argument('-p', '--s3-prefix', dest='prefix', action='store',
                   default=None, type=str,
                   help='prefix to prepend to file paths when creating S3 keys')
    p.add_argument('-s', '--summary', dest='summary', action='store_true',
                   default=False, help='print summary/stats at end of run')
    p.add_argument('BUCKET_NAME', action='store', type=str,
                   help='Name of S3 bucket to upload to')
    p.add_argument('FILELIST_PATH', action='store', type=str,
                   help='Path to filelist specifying which files or paths to '
                        'upload, one per line. Lines beginning with # will be '
                        'ignored. Directories will be uploaded recursively.')
    args = p.parse_args(argv)
    return args


def set_log_info():
    """set logger level to INFO"""
    set_log_level_format(logging.INFO,
                         '%(asctime)s %(levelname)s:%(name)s:%(message)s')


def set_log_debug():
    """set logger level to DEBUG, and debug-level output format"""
    set_log_level_format(
        logging.DEBUG,
        "%(asctime)s [%(levelname)s %(filename)s:%(lineno)s - "
        "%(name)s.%(funcName)s() ] %(message)s"
    )


def set_log_level_format(level, format):
    """
    Set logger level and format.

    :param level: logging level; see the :py:mod:`logging` constants.
    :type level: int
    :param format: logging formatter format string
    :type format: str
    """
    formatter = logging.Formatter(fmt=format)
    logger.handlers[0].setFormatter(formatter)
    logger.setLevel(level)


def read_filelist(path):
    """
    Given the path to the filelist, read the file and return a list of all
    paths contained in it.

    :param path: path to filelist
    :type path: str
    :return: list of files and directories to back up
    :rtype: list
    """
    logger.debug('Reading filelist from: %s', path)
    if not os.path.exists(path):
        raise RuntimeError('Filelist does not exist: %s' % path)
    files = []
    with open(path, 'r') as fh:
        for line in fh.readlines():
            line = line.strip()
            if line.startswith('#'):
                continue
            if line == '':
                continue
            files.append(line)
    logger.debug('Read %d paths', len(files))
    return files


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
        dry_run=args.dry_run
    )
    files = read_filelist(args.FILELIST_PATH)
    stats = s.run(files)
    if args.summary:
        print(stats.summary())


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    main(args)
