# -*- coding: utf-8 -*-

### voter_bot
### GNU/GPL v2
### Author: Cody Rocker
### Author_email: cody.rocker.83@gmail.com
### 2016
#-----------------------------------
#   Requires:                    """
#    - Python 3                  """
#    - imgurpython               """
#-----------------------------------
import argparse
import logging
import time

def time_stamp(unix_time):
    return time.strftime('%H:%M %m-%d', time.localtime(unix_time))


def parse_args(show_usage=False):
    desc = ('Up/Down vote all imgur comments/submissions from a user.')
    parser = argparse.ArgumentParser(description = desc, formatter_class = argparse.RawTextHelpFormatter)

    parser.add_argument('-u', '--user', action='store', help='Imgur username.')
    parser.add_argument('-v', dest='vote', action='store', default='up', choices=['up', 'down'], help='Vote to submit. [DEFAULT=up]')
    parser.add_argument('--config', action ='store_true', help='Run user-bot configuration.')
    parser.add_argument('--get-credits', dest='get_credits', action='store_true', help='Show api credit info.')
    parser.add_argument('--check-messages', dest='check_messages', action='store_true', help='Check for new notifications on linked account.')
    parser.add_argument('--limit', action='store', nargs=1, dest='vote_num', help='Limit how many votes are processed.')

    # logger verbosity/path_settings args
    parser.add_argument('--logging-level', dest='logging_level', action='store',
        default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='[--logging-level LOGGING_LEVEL];\n-- Default=[INFO]')
    parser.add_argument('--log-file-path', dest='log_file_path', action='store',
        help='[--log-file-path PATH/TO/LOG];\n-- File to write the logs to (content replaced '
             'each\n   time). If this option is not specified, the logs\n   are sent to the standard'
             ' output (according to the\n   logging verbosity level).')

    parser.add_argument('--version', action='version', version='1.0')
    if show_usage:
        parser.print_usage()
    else:
        args = parser.parse_args()
        return args


def init_logger(args):
    log = logging.getLogger('__name__')
    handler = None
    if (args.log_file_path is not None):
        handler = logging.FileHandler(
            args.log_file_path, 'w', encoding=None, delay='true')
    else:
        handler = logging.StreamHandler()
    # ref: https://docs.python.org/2/library/logging.html#logrecord-attributes
    log_format = '\033[93m[%(module)s][%(levelname)s]\033[0m >> %(message)s'
    handler.setFormatter(logging.Formatter(log_format))
    log.addHandler(handler)
    log.setLevel(getattr(logging, args.logging_level))
    return log

def get_input(string):
    """ Return correct user_input command for Python 2 or 3 """
    try:
        return raw_input(string)
    except:
        return input(string)
