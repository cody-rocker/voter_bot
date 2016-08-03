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
import sys
import time

from .tools import parse_args, init_logger, time_stamp
from .imgur_user_bot import ImgurUserBot
from .bot_logic import calc_credit_cost, build_comment_list, cast_votes, check_for_mentions


def main(vote_limit=None):
    log.debug('[main] > vote_type={0}; target_user={1};;'.format(vote_type, target_user))
    # Log in a new UserBot client
    ## TODO: IF --config is passed AND there is no config file the configurations runs twice.
    ##             This logic needs to be cleaned up.
    voter_bot = ImgurUserBot(log)
    if args.config:  # Catch config command line flag
        log.info('Running voter-bot configuration...')
        voter_bot.first_run()
        quit()
    elif args.get_credits:  # Catch get-credits command line flag
        voter_bot.get_api_credits()
        log.info('{0} user credits remaining;'.format(voter_bot.user_credit_remaining))
        log.info('{0} client credits remaining;'.format(voter_bot.client_credit_remaining))
        log.info('Next reset {0};'.format(time_stamp(int(voter_bot.user_reset))))
        quit()
    elif args.check_messages:
        # check_for_mentions(voter_bot)
        quit()
    else:  # Run the bot
        # Make sure required arguments are passed
        if target_user == None:
            log.error('Missing required argument(s)!  [-u, --user]')
            parse_args(show_usage=True)
            quit(exit_code=1)
        # Bot Logic
        try:
            comment_count, page_count = calc_credit_cost(voter_bot, target_user)
            build_comment_list(voter_bot, page_count, target_user)
            CREDITS_REMAINING = voter_bot.get_api_credits()
            # Try to leave an emergency reserve of api credits for debugging requests
            if CREDITS_REMAINING < comment_count:
                vote_num = CREDITS_REMAINING - 50
            else:
                vote_num = comment_count
            if vote_limit:
                if vote_num > vote_limit:
                    vote_num = vote_limit
            if vote_num <= 0:
                log.error('No available credits; Operation aborted.')
                raise Exception('rate limit error; vote_num <= 0')
            cast_votes(voter_bot, page_count, vote_num, vote_type, target_user)
            log.debug('[main] > CREDITS_REMAINING={0};;'.format(voter_bot.get_api_credits()))
            log.info('Rate limit reset scheduled for {0}'.format(time_stamp(int(voter_bot.user_reset))))
            quit()
        except Exception as e:
            voter_bot.log.error(e)
            quit(exit_code=1)


def quit(exit_code=0):
    elapsed_time = '{0:.2f} seconds elapsed.'.format(time.time() - start_time)
    if exit_code == 0:
        log.info('Voter-Bot executed successfully; {0}'.format(elapsed_time))
        sys.exit(0)
    elif exit_code == 1:
        log.critical('Voter-Bot encountered an error: {0}'.format(elapsed_time))
        sys.exit(1)

if __name__ == '__main__':
    start_time = time.time()
    # Get values from command line arguments
    args = parse_args()
    # Initialize logging
    log = init_logger(args)
    # Set variables from command line args
    target_user = args.user
    vote_type = args.vote
    vote_limit = None
    if args.vote_num:
        vote_limit = int(args.vote_num[0])
        log.debug('[__argparser__] > VOTE_LIMIT={0};;'.format(vote_limit))
    try:
        # Run the bot logic
        main(vote_limit=vote_limit)
    except KeyboardInterrupt:
        print('')
        log.critical('Voter-Bot operation aborted by user! {0:.2f} seconds elapsed.'.format(
            time.time() - start_time))
        sys.exit()