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
from platform import node
from datetime import datetime
import requests
from pprint import pformat

from s3sfe.version import PROJECT_URL, VERSION

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

# suppress requests internal logging below WARNING level
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)
requests_log.propagate = True


def parse_args(argv):
    """
    Use Argparse to parse command-line arguments.

    :param argv: list of arguments to parse (``sys.argv[1:]``)
    :type argv: list
    :return: parsed arguments
    :rtype: :py:class:`argparse.Namespace`
    """
    p = argparse.ArgumentParser(
        description='webhook2lambda2sqs - Generate code and manage '
                    'infrastructure for receiving webhooks with AWS API '
                    'Gateway and pushing to SQS via Lambda - <%s>' % PROJECT_URL
    )
    p.add_argument('-c', '--config', dest='config', type=str,
                   action='store', default='config.json',
                   help='path to config.json (default: ./config.json)')
    p.add_argument('-v', '--verbose', dest='verbose', action='count',
                   default=0,
                   help='verbose output. specify twice for debug-level output.')
    p.add_argument('-V', '--version', action='version',
                   version='webhook2lambda2sqs v%s <%s>' % (
                       VERSION, PROJECT_URL
                   ))
    subparsers = p.add_subparsers(title='Action (Subcommand)', dest='action',
                                  metavar='ACTION', description='Action to '
                                  'perform; each action may take further '
                                  'parameters. Use ACTION -h for subcommand-'
                                  'specific options and arguments.')
    subparsers.add_parser(
        'generate', help='generate lambda function and terraform configs in ./'
    )
    tf_parsers = [
        ('genapply', 'generate function and terraform configs in ./, then run '
                     'terraform apply'),
        ('plan', 'run terraform plan to show changes which will be made'),
        ('apply', 'run terraform apply to apply changes/create infrastructure'),
        ('destroy',
         'run terraform destroy to completely destroy infrastructure')
    ]
    tf_p_objs = {}
    for cname, chelp in tf_parsers:
        tf_p_objs[cname] = subparsers.add_parser(cname, help=chelp)
        tf_p_objs[cname].add_argument('-t', '--terraform-path', dest='tf_path',
                                      action='store', default='terraform',
                                      type=str, help='path to terraform '
                                                     'binary, if not in PATH')
        tf_p_objs[cname].add_argument('-S', '--no-stream-tf', dest='stream_tf',
                                      action='store_false', default=True,
                                      help='DO NOT stream Terraform output to '
                                           'STDOUT (combined) in realtime')
    apilogparser = subparsers.add_parser('apilogs', help='show last 10 '
                                         'CloudWatch Logs entries for the '
                                         'API Gateway')
    apilogparser.add_argument('-c', '--count', dest='log_count', type=int,
                              default=10, help='number of log entries to show '
                              '(default 10')
    logparser = subparsers.add_parser('logs', help='show last 10 CloudWatch '
                                      'Logs entries for the function')
    logparser.add_argument('-c', '--count', dest='log_count', type=int,
                           default=10, help='number of log entries to show '
                                            '(default 10')
    queueparser = subparsers.add_parser('queuepeek', help='show messages from '
                                        'one or all of the SQS queues')
    queueparser.add_argument('-n', '--name', type=str, dest='queue_name',
                             default=None, help='queue name to read (defaults '
                                                'to None to read all)')
    queueparser.add_argument('-d', '--delete', action='store_true',
                             dest='queue_delete', default=False,
                             help='delete messages after reading')
    queueparser.add_argument('-c', '--count', dest='msg_count', type=int,
                             default=10, help='number of messages to read from '
                                              'each queue (default 10)')
    testparser = subparsers.add_parser('test', help='send test message to '
                                                    'one or more endpoints')
    testparser.add_argument('-t', '--terraform-path', dest='tf_path',
                            action='store', default='terraform',
                            type=str, help='path to terraform '
                            'binary, if not in PATH')
    testparser.add_argument('-n', '--endpoint-name', dest='endpoint_name',
                            type=str, default=None,
                            help='endpoint name (default: None, to send to '
                                 'all endpoints)')
    subparsers.add_parser(
        'example-config', help='write example config to STDOUT and description '
                               'of it to STDERR, then exit'
    )
    args = p.parse_args(argv)
    if args.action is None:
        # for py3, which doesn't raise on this
        sys.stderr.write("ERROR: too few arguments\n")
        raise SystemExit(2)
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

    print(args)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    main(args)
