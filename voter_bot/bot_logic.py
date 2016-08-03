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
import os
import sys
import time
import pickle

from imgurpython.helpers.error import ImgurClientError, ImgurClientRateLimitError

from .tools import time_stamp, get_input


def count_pages(comment_count):
    page_size = 50
    if comment_count <= page_size:
        return 1
    else:
        page_count = int(comment_count / page_size)
        if (comment_count % page_size) > 0:
            page_count += 1
        return page_count


def save_to_cache(filename, comment_list):
    with open(os.path.join('cache', filename), 'wb') as f:
        pickle.dump(comment_list, f)
    f.close()


def read_from_cache(filename):
    pickle_in = open(os.path.join('cache', filename), 'rb')
    comment_list = pickle.load(pickle_in)
    pickle_in.close()
    return comment_list


def calc_progress(current_index, total_votes):
    progress = (current_index + 1) / total_votes
    output = '{0:.1f}%'.format(progress * 100)
    return output


def render_progress(message):
    """ Pre-formatted carriage return printer for same-line output """
    log_wrapper = '\033[93m[bot_logic][INFO]\033[0m >> {0}\r'
    sys.stdout.write(log_wrapper.format(message))
    sys.stdout.flush()


def wait_for_user():
    sys.stdout.write('\t\t     Press Enter to continue...')
    sys.stdout.flush()
    get_input('\t\033[93m^C to cancel.\033[0m')


def calc_credit_cost(voter_bot, target_user):
    # Results are limited to 100 comments per page/request
    # so we calculate the total number of requests to fetch all comments
    comment_count = voter_bot.get_comment_count(target_user)
    if comment_count is not None:
        voter_bot.log.info('Found {0} comment(s) for user: {1}'.format(comment_count, target_user))
        page_count = count_pages(comment_count)
        return comment_count, page_count
    else:
        raise Exception('Unable to calculate credit cost!')


def check_for_mentions(voter_bot):
    # Can't get mentions via the API?
    voter_bot.log.error('Method not implemented.')
    pass


def build_comment_list(voter_bot, page_count, target_user):
    filename = '{0}_comments.pickle'.format(target_user)
    last_modified = 0
    try:
        last_modified = os.path.getmtime(os.path.join('cache', filename))  # UNIX Epoch
        voter_bot.log.debug('[build_comment_list] > {0} last_modifed={1}'.format(
            target_user, time_stamp(int(last_modified))))
    except FileNotFoundError as e:
        voter_bot.log.debug(e)
    # If pickle is older than 24 hours, refresh the list
    if (time.time() - last_modified) > (3600 * 24):
        # Report total requests used for this operation, and allow the user the
        # opportunity to bail out if available credits are too low.
        voter_bot.log.info('Operation will use {0} API Credits, CREDITS AVAILABLE: {1}'.format(
            page_count, voter_bot.get_api_credits()))
        wait_for_user()
        voter_bot.log.info('Refreshing stale/non-existent cached comment list.')
        comment_list = []  # Empty list to store dicts
        voter_bot.log.info('Building comment list for user: {0}'.format(target_user))
        # Iterate through each page
        for x in range(page_count):
            progress = calc_progress(x, page_count)
            render_progress('Processing page {0} of {1}; {2} \r'.format(
                x + 1, page_count, progress))
            comments = voter_bot.get_account_comments(target_user, page=x)
            if comments is not None:
                for comment in comments:
                    # Add an entry for each comment
                    comment = {'id': comment.id, 'vote': comment.vote}
                    comment_list.append(comment)
            else:
                raise Exception('No comments found for user: {0}!'.format(target_user))
        sys.stdout.write('\n')
        save_to_cache(filename, comment_list)
        voter_bot.log.info("{0}'s comment list has been cached.".format(target_user))
        return True
    else:
        voter_bot.log.info('Found valid cache for user {0}; Saved {1} credits.'.format(
            target_user, page_count))
        return True


def cast_votes(voter_bot, page_count, vote_num, vote_type, target_user):
    # Report total requests used for this operation, and allow the user the
    # opportunity to bail out if available credits are too low.
    voter_bot.log.info('Operation will use {0} API Credits, CREDITS AVAILABLE: {1}'.format(
        vote_num, voter_bot.get_api_credits()))
    wait_for_user()
    if vote_num > 1200:
        voter_bot.log.info('Complying with hourly rate limit.')
        voter_bot.log.info('Voting capped to 1200 post credits per operation.')
        vote_num = 1200
    total_votes = 0
    # Load the pickle into memory
    filename = '{0}_comments.pickle'.format(target_user)
    comment_list = read_from_cache(filename)
    # Iterate through the comment_list
    for comment in comment_list:
        # Save progress to cache to limit data loss on interruption
        if total_votes % 25 == 0:
            save_to_cache(filename, comment_list)
        progress = calc_progress(total_votes, vote_num)
        # POST a comment vote request for each comment if vote and vote_type don't match
        if total_votes < vote_num:
            if comment['vote'] != vote_type:
                render_progress('comment_id: {0}; {1} voting; {2}                     \r'.format(
                    comment['id'], vote_type, progress))
                if voter_bot.comment_vote(comment['id'], vote=vote_type):
                    comment['vote'] = vote_type
                    total_votes += 1
                else:
                    continue
            else:
                render_progress('comment_id: {0}; current vote matches vote_type; {1} \r'.format(
                    comment['id'], progress))
                time.sleep(.01)
        elif total_votes == vote_num:
            sys.stdout.write('\n')
            voter_bot.log.info('Voter-Bot posted {0} {1} votes on {2}'.format(
                total_votes, vote_type, target_user))
            break
    save_to_cache(filename, comment_list)
    voter_bot.log.info('{0} changes saved to cache.'.format(total_votes))