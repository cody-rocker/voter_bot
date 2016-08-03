# -*- coding: utf-8 -*-

### voter_bot
### GNU/GPL v2
### Author: Cody Rocker
### Author_email: cody.rocker.83@gmail.com
### 2016
#-----------------------------------
#   Requires:                    """
#    - Python 2.7                """
#    - imgurpython               """
#-----------------------------------
import os

class ConfigManager():

    def __init__(self, app_name, config_dir):
        self.config_path = os.path.join(config_dir, app_name)

    def get_config(self):
        ''' Create a config parser for reading INI files '''
        try:
            import configparser
            return configparser.ConfigParser()
        except:
            import configparser
            return configparser.ConfigParser()

    def load_config(self, config_file):
        config = self.get_config()
        try:
            config.read(os.path.join(self.config_path, config_file))
            return config
        except:
            return config

    def write_config(self, config_instance, config_file):
        try:  # try to write to directory, or
            with open(os.path.join(
                self.config_path, config_file), 'w') as configFile:
                    config_instance.write(configFile)
        except:  # create the directory, if necessary
            os.mkdir(self.config_path)
            with open(os.path.join(
                self.config_path, config_file), 'w') as configFile:
                    config_instance.write(configFile)