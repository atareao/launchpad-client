#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of launchpad-client
#
# Copyright (c) 2020 Lorenzo Carbonell Cerezo <a.k.a. atareao>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from optparse import OptionParser
import requests
import json
import os
import re
import time
import random
from requests_toolbelt.multipart.encoder import MultipartEncoder


OAUTH_SIGNATURE_METHOD = 'PLAINTEXT'
OAUTH_SIGNATURE = '&'
REQUEST_TOKEN_URL = 'https://launchpad.net/+request-token'
ACCESS_TOKEN_URL = 'https://launchpad.net/+access-token'

URL = 'https://api.launchpad.net/1.0/'


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

def generate_nonce(length=8):
    """Generate pseudorandom number."""
    return ''.join([str(random.randint(0, 9)) for i in range(length)])


def build(owner, ppa, source_name, version, to_serie):
    config = get_config()
    if not config['oauth_consumer_key']:
        print('Set consumer key first')
        return
    if not config['oauth_token'] or not config['oauth_token_secret']:
        print('Request token first')
        return
    params = {
            'OAuth realm': 'https://api.launchpad.net/',
            'oauth_consumer_key': config['oauth_consumer_key'],
            'oauth_token': config['oauth_token'],
            'oauth_signature_method': OAUTH_SIGNATURE_METHOD,
            'oauth_signature': OAUTH_SIGNATURE + config['oauth_token_secret'],
            'oauth_timestamp': str(int(time.time())),
            'oauth_nonce': generate_nonce(),
    }
    authorization = ''
    for key in params:
        if authorization:
            authorization += ',' 
        authorization += '{}="{}"'.format(key, params[key])
    archive = 'https://api.launchpad.net/1.0/~{}/+archive/ubuntu/{}'.format(
            owner, ppa)
    multipart_data = MultipartEncoder(fields={
            'ws.op': 'syncSource',
            'from_archive': archive,
            'to_pocket': 'Release',
            'source_name': source_name,
            'to_series': to_serie,
            'version': version,
            'include_binaries': 'true'
            })
    headers = {'Accept': 'application/json',
               'Content-Type': multipart_data.content_type,
               'Authorization': authorization}
    r = requests.post(archive, headers=headers, data=multipart_data)
    return r.status_code == 200


def go_endpoint(endpoint):
    config = get_config()
    if not config['oauth_consumer_key']:
        print('Set consumer key first')
        return
    if not config['oauth_token'] or not config['oauth_token_secret']:
        print('Request token first')
        return
    params = {
            'OAuth realm': 'https://api.launchpad.net/',
            'oauth_consumer_key': config['oauth_consumer_key'],
            'oauth_token': config['oauth_token'],
            'oauth_signature_method': OAUTH_SIGNATURE_METHOD,
            'oauth_signature': OAUTH_SIGNATURE + config['oauth_token_secret'],
            'oauth_timestamp': str(int(time.time())),
            'oauth_nonce': generate_nonce(),
    }
    authorization = ''
    for key in params:
        if authorization:
            authorization += ',' 
        authorization += '{}="{}"'.format(key, params[key])
    headers = {'Accept': 'application/json',
               'Authorization': authorization}
    url = URL + endpoint
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.content.decode()
    return None


def main():
    usage_msg = 'usage: %prog [options]'
    parser = OptionParser(usage=usage_msg, add_help_option=False)
    parser.add_option('-v', '--version',
                      action='store',
                      dest='version',
                      default=False,
                      help='Version')
    parser.add_option('-u', '--ubuntu',
                      action='store',
                      dest='ubuntu',
                      default=False,
                      help='Ubuntu serie')
    parser.add_option('-i', '--init',
                      action='store',
                      dest='init',
                      default=False,
                      help='Init source')
    parser.add_option('-o', '--owner',
                      action='store',
                      dest='owner',
                      default=False,
                      help='Owner')
    parser.add_option('-c', '--consumer-key',
                      action='store',
                      dest='key',
                      default=False,
                      help='Consumer key')
    parser.add_option('-d', '--distribution',
                      action='store',
                      dest='distribution',
                      default=False,
                      help='Distribution')
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
    parser.add_option('-p', '--ppa',
                      action='store',
                      dest='ppa',
                      default=False,
                      help='PPA')
    parser.add_option('-m', '--me',
                      action='store_true',
                      dest='me',
                      default=False,
                      help='Who am I?')
    parser.add_option('-f', '--files',
                      action='store_true',
                      dest='files',
                      default=False,
                      help='files')
    parser.add_option('-b', '--build',
                      action='store_true',
                      dest='build',
                      default=False,
                      help='Build')
    parser.add_option('-l', '--list',
                      action='store_true',
                      dest='list',
                      default=False,
                      help='List')
    parser.add_option('-e', '--exists',
                      action='store_true',
                      dest='exists',
                      default=False,
                      help='Find builds')
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
    elif option.distribution:
        result = go_endpoint(option.distribution)
        print(result)
        return
    elif option.me:
        result = go_endpoint('people/+me')
        print(result)
        return
    elif option.build:
        build(option.owner, option.ppa, option.init, option.version,
              option.ubuntu)
        return
    elif option.exists:
        if option.owner:
            if option.ppa:
                params = {'ws.op': 'getPublishedSources',
                          'status': 'Published'}
                if option.init:
                    params['source_name'] = option.init
                if option.version:
                    params['version'] = option.version
                if option.ubuntu:
                    url = 'https://api.launchpad.net/1.0/ubuntu/{}'
                    params['distro_series'] = url.format(option.ubuntu)
                options = ['{}={}'.format(key, params[key]) for key in params]
                endpoint = '~{}/+archive/{}?{}'.format(
                        option.owner,
                        option.ppa,
                        '&'.join(options))
                result = go_endpoint(endpoint)
                print(result)
            else:
                print('Set PPA')
        else:
            print('Set owner')
        return

        
    elif option.list:
        if option.owner:
            if option.ppa:
                result = go_endpoint('~{}/+archive/{}'.format(option.owner,
                                                            option.ppa))
            else:
                result = go_endpoint('~{}/ppas'.format(option.owner))
            print(result)
        else:
            print('Set owner')
        return
    parser.print_help()
    exit()

if __name__ == '__main__':
    main()
