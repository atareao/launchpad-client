#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from optparse import OptionParser
import requests
import json
import os
import re


OAUTH_SIGNATURE_METHOD = 'PLAINTEXT'
OAUTH_SIGNATURE = '&'
REQUEST_TOKEN_URL = 'https://launchpad.net/+request-token'
ACCESS_TOKEN_URL = 'https://launchpad.net/+access-token'

url = 'https://api.launchpad.net/1.0/'


def access_token():
    config = get_config()
    if not config['oauth_consumer_key']:
        print('Set consumer key first')
        return
    if not config['oauth_token'] or not config['oauth_token_secret']:
        print('Request token first')
        return
    params = {
            'oauth_token': config['oauth_token'],
            'oauth_consumer_key': config['oauth_consumer_key'],
            'oauth_signature_method': OAUTH_SIGNATURE_METHOD,
            'oauth_signature': OAUTH_SIGNATURE + config['oauth_token_secret']
    }
    r = requests.post(ACCESS_TOKEN_URL, data=params)
    if r.status_code == 200:
        data = r.content.decode()
        regex = r'oauth_token=([^&]*)&oauth_token_secret=([^&]*)'
        matches = re.findall(regex, data, re.MULTILINE)
        if len(matches) == 1 and len(matches[0]) == 2:
            config['oauth_token'] = matches[0][0]
            config['oauth_token_secret'] = matches[0][1]
            set_config(config)
    else:
        print('Something goes wrong')


def request_token():
    config = get_config()
    if config['oauth_consumer_key']:
        params = {
            'oauth_consumer_key': config['oauth_consumer_key'],
            'oauth_signature_method': OAUTH_SIGNATURE_METHOD,
            'oauth_signature': OAUTH_SIGNATURE
        }
        r = requests.post(REQUEST_TOKEN_URL, data=params)
        if r.status_code == 200:
            data = r.content.decode()
            regex = r'oauth_token=([^&]*)&oauth_token_secret=(.*)'
            matches = re.findall(regex, data, re.MULTILINE)
            if len(matches) == 1 and len(matches[0]) == 2:
                config['oauth_token'] = matches[0][0]
                config['oauth_token_secret'] = matches[0][1]
                set_config(config)
            print('Go to  https://launchpad.net/+authorize-token?{}'.format(
                r.content.decode()))
        else:
            print('Something goes wrong')
    else:
        print('Please set consumer key first')


def get_config():
    check_config_dir()
    config_file = os.path.join(os.path.expanduser('~/.config'), 'lp',
                                                  'lp.json')
    if os.path.exists(config_file):
        with open(config_file, 'r') as fr:
            config = json.load(fr)
    else:
        config = {'oauth_consumer_key': '',
                  'oauth_token': '',
                  'oauth_token_secret': ''
                }
    return config


def set_config(config):
    check_config_dir()
    config_file = os.path.join(os.path.expanduser('~/.config'), 'lp',
                                                  'lp.json')
    with open(config_file, 'w') as fw:
        json.dump(config, fw)


def set_consumer_key(key):
    config = get_config()
    config['oauth_consumer_key'] = key
    set_config(config)


def get_consumer_key():
    config = get_config()
    print('Consumer key: {}'.format(config['oauth_consumer_key']))


def check_config_dir():
    config_dir = os.path.join(os.path.expanduser('~/.config'), 'lp')
    if not os.path.exists(config_dir):
        os.makedirs(config_dir) 


def main():
    usage_msg = 'usage: %prog [options]'
    parser = OptionParser(usage=usage_msg, add_help_option=False)
    parser.add_option('-c', '--consumer-key',
                      action='store',
                      dest='key',
                      default=False,
                      help='Consumer key')
    parser.add_option('-s', '--set-consumer-key',
                      action='store_true',
                      dest='set_consumer_key',
                      default=False,
                      help='Save consumer key')
    parser.add_option('-g', '--get-consumer-key',
                      action='store_true',
                      dest='get_consumer_key',
                      default=False,
                      help='Save consumer key')
    parser.add_option('-r', '--request-token',
                      action='store_true',
                      dest='request_token',
                      default=False,
                      help='Request token')
    parser.add_option('-a', '--access-token',
                      action='store_true',
                      dest='access_token',
                      default=False,
                      help='Get access token')
    (option, args) = parser.parse_args()
    if option.set_consumer_key:
        if option.key is False:
            print('Error, consumer key is missing')
        else:
            set_consumer_key(option.key)
        return
    elif option.get_consumer_key:
        get_consumer_key()
        return
    elif option.request_token:
        request_token()
        return
    elif option.access_token:
        access_token()
        return
    parser.print_help()
    exit()

if __name__ == '__main__':
    main()
