#!/usr/bin/env python3

from subprocess import check_call
from os import path, environ
from sys import argv, exit
from socket import gethostname
from getpass import getuser
from time import sleep

from requests import get, post


class SSHKey():
    def __init__(
        self,
        dirname=path.join(environ['HOME'], '.ssh'),
        basename='id_rsa'
    ):
        self.private = path.join(dirname, basename)
        self.public = self.private + ".pub"

    def exists(self):
        return path.isfile(self.private)

    def generate(self, comment, bits=4096):
        if self.exists():
            raise ValueError('key already exists')

        check_call([
            'ssh-keygen',
            '-t', 'rsa',
            '-N', '',
            '-C', comment,
            '-b', str(bits),
            '-f', self.private
        ])

    def read_public(self):
        with open(self.public, 'r', encoding='ascii') as key_file:
            return key_file.read().strip()


class API():
    def __init__(self, url, kwargs={}):
        self._url = url
        self._kwargs = kwargs

    def __getattr__(self, attr):
        return API(self._url + '/' + attr, self._kwargs)

    def get(self, params=None, **kwargs):
        kwargs.update(self._kwargs)
        return get(self._url or '/', params, **kwargs)

    def post(self, data=None, json=None, **kwargs):
        kwargs.update(self._kwargs)
        return post(self._url or '/', data, json, **kwargs)


class GitHub(API):
    def __init__(self, client_id):
        self._client_id = client_id
        super().__init__(
            'https://api.github.com',
            {'headers': {'Accept': 'application/vnd.github.v3+json'}}
        )

    def authenticate(self):
        code = post(
            'https://github.com/login/device/code',
            data={
                'client_id': self._client_id,
                'scope': 'admin:public_key'
            },
            headers={'Accept': 'application/json'}
        ).json()

        print('Please enter the following code at', code['verification_uri'])
        print(code['user_code'])

        token = None
        while token is None:
            token = self._poll_for_token(code)
        if token is False:
            return False

        self._kwargs['headers']['Authorization'] = 'Bearer ' + token
        return True

    def _poll_for_token(self, code):
        sleep(code['interval'])
        token = post(
            'https://github.com/login/oauth/access_token',
            data={
                'client_id': self._client_id,
                'device_code': code['device_code'],
                'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
            },
            headers={'Accept': 'application/json'}
        ).json()

        access_token = token.get('access_token')
        if access_token is not None:
            return access_token
        else:
            error = token.get('error')
            if error == 'authorization_pending':
                return None
            else:
                print('GitHub authorization error:', error)
                return False


CLIENT_ID = '269e96cbf27d57068fae'


def main():
    local_key = SSHKey()
    comment = getuser() + '@' + gethostname()
    if not local_key.exists():
        local_key.generate(comment=comment)
    public_key = local_key.read_public().strip()

    api = GitHub(CLIENT_ID)
    if api.authenticate():
        print('Authenticated. Checking keys...')
    else:
        print('Failed to authenticate with GitHub')
        exit(1)

    keys = api.user.keys.get().json()
    for key in keys:
        if public_key.startswith(key['key']):
            print(
                'The key on this machine is already on GitHub.',
                'You\'re good to go!'
            )
            break
    else:
        response = api.user.keys.post(json={
            'title': comment,
            'key': public_key
        })
        if response.ok:
            print('Key', comment, 'created! Check your account.')
        else:
            print('Could not create key!')
            exit(1)


if __name__ == "__main__":
    main()
