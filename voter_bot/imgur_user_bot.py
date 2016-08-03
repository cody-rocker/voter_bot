# -*- coding: utf-8 -*-

### imgur_user_bot
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

from imgurpython import ImgurClient
from imgurpython.helpers.error import ImgurClientError, ImgurClientRateLimitError

from .config_manager import ConfigManager
from .tools import time_stamp, get_input

APPLICATION_NAME = "voter-bot"
CONFIG_FILES = {'bot_settings': 'bot_settings.ini'}
CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.config')

class ImgurUserBot:
    """ Returns a logged in user client to handle requests to imgur API """
    ## TODO: get_input validation

    def __init__(self, log):
        self.log = log
        self.log.debug('[ImgurUserBot.__init__] > Initializing {0};;'.format(APPLICATION_NAME))
        self.config_manager = ConfigManager(APPLICATION_NAME, CONFIG_DIR)
        self.bot_settings = self.config_manager.load_config(CONFIG_FILES['bot_settings'])
        self.client = None
        # Check for valid saved configuration
        if not self.bot_settings.sections():
            self.log.info('No configuration found, running setup.')
            self.bot_settings.add_section('Initialization')
            self.bot_settings.set('Initialization', 'first_run', 'True')
            self.save_settings()
            self.first_run()
        if self.client == None:
            self.login()
        self.refresh_rate_limits()
        self.log.debug('[ImgurUserBot.__init__] > Initialization complete;;')

    def get_bot_settings(self):
        return self.bot_settings

    def save_settings(self):
        self.config_manager.write_config(self.bot_settings, CONFIG_FILES['bot_settings'])
        self.log.debug('[ImgurUserBot.save_settings] > ImgurUserBot settings saved.')

    def login(self):
        config = self.get_bot_settings()
        client_id = config.get('credentials', 'client_id')
        client_secret = config.get('credentials', 'client_secret')
        refresh_token = config.get('credentials', 'refresh_token')
        self.client = ImgurClient(client_id, client_secret, None, refresh_token)
        self.log.info('ImgurUserBot successfully logged into Imgur.')

    def first_run(self):
        sys.stdout.write('\n\n** Take a moment to configure VoterBot **\n\n'
                         'You can reconfigure at any time by passing the argument --config\n'
                         'or manually editing the config files (~/.config/{0})\n'.format(
                            APPLICATION_NAME))
        sys.stdout.flush()
        self._register_application(self.bot_settings)
        self.client = self._authenticate(self.bot_settings)
        self.log.info('Settings saved to ~/.config/{0}/bot_settings.ini'.format(APPLICATION_NAME))

    def refresh_rate_limits(self):
        credit_dict = self.client.credits
        if credit_dict['UserRemaining'] is not None:
            self.user_credit_remaining = int(credit_dict['UserRemaining'])
            self.client_credit_remaining = int(credit_dict['ClientRemaining'])
            self.user_reset = credit_dict['UserReset']  # Unix Epoch

    def _register_application(self, settings):
        sys.stdout.write('\nVisit <https://api.imgur.com/oauth2/addclient> to register bot with\n'
                         'imgur API. Make note of the client_id and client_secret you are assigned\n\n')
        sys.stdout.flush()
        client_id = get_input('Client ID: ')
        client_secret = get_input('Client Secret: ')
        try:
            settings.add_section('credentials')
        except:
            # Most likely already exists, need more specific handling here.
            pass
        settings.set('credentials', 'client_id', client_id)
        settings.set('credentials', 'client_secret', client_secret)
        self.save_settings()

    def _authenticate(self, settings):
        client_id = settings.get('credentials', 'client_id')
        client_secret = settings.get('credentials', 'client_secret')
        client = ImgurClient(client_id, client_secret)
        authorization_url = client.get_auth_url('pin')
        sys.stdout.write('\nGo to the following URL:\n  >> {0}\n\n'.format(authorization_url))
        sys.stdout.flush()
        pin = get_input('Enter pin code: ')
        credentials = client.authorize(pin, 'pin')
        client.set_user_auth(credentials['access_token'], credentials['refresh_token'])
        settings.set('credentials', 'refresh_token', credentials['refresh_token'])
        sys.stdout.write('\nAuthentication successful! Here are the details:\nAccess token: {0}\n'
                         'Refresh token: {1}\n** Configuration Updated **\n\n'.format(
                            credentials['access_token'], credentials['refresh_token']))
        sys.stdout.flush()
        self.save_settings()
        return client

    def get_api_credits(self):
        """ Return lowest value (int) in current API credit pool """
        self.refresh_rate_limits()
        self.log.debug(' > {0} user credits remaining;;'.format(self.user_credit_remaining))
        self.log.debug(' > {0} client credits remainging;;'.format(self.client_credit_remaining))
        self.log.debug(' > Next reset {0};;'.format(time_stamp(int(self.user_reset))))
        if self.client_credit_remaining < self.user_credit_remaining:
            return int(self.client_credit_remaining)
        else:
            return int(self.user_credit_remaining)

    def get_comment_count(self, username):
        try:
            return self.client.get_account_comment_count(username)
        except ImgurClientError as e:
            self.log.error(e.error_message)
            return None

    def get_account_comments(self, username, sort='newest', page=1):
        try:
            return self.client.get_account_comments(username, sort, page)
        except ImgurClientError as e:
            self.log.error(e.error_message)
            return None

    def comment_vote(self, comment_id, vote='up'):
        try:
            self.client.comment_vote(comment_id, vote=vote)
            return True
        except ImgurClientRateLimitError as e:
            self.log.error(e.error_message)
            raise Exception(e)  # HACK: Break out of loop if batch vote
        except ImgurClientError as e:
            self.log.debug('COMMENT_ID={0};'.format(comment['id']))
            self.log.error(e.error_message)
            return False
