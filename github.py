#!/usr/bin/env python3

from subprocess import check_call
from os import path, environ
from sys import argv, exit
from socket import gethostname
from getpass import getuser, getpass

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
    _otp = 'X-GitHub-OTP'

    def __init__(self, user, password):
        super().__init__(
            'https://api.github.com',
            {
                'headers': {'Accept': 'application/vnd.github.v3+json'},
                'auth': (user, password)
            }
        )

    def check_auth(self):
        response = self.user.get()
        if not response.ok:
            if (
                response.status_code == 401 and
                response.headers.get(self._otp, '').startswith('required')
            ):
                return self.handle_2fa()
            return False
        return True

    def handle_2fa(self):
        code = ''
        while not code:
            code = input('Enter your two-factor authentication code: ')
        self._kwargs['headers'][self._otp] = code.strip()
        return True


def main():
    local_key = SSHKey()
    comment = getuser() + '@' + gethostname()
    if not local_key.exists():
        local_key.generate(comment=comment)
    public_key = local_key.read_public().strip()

    api = GitHub(
        input('Username: ').strip(),
        getpass('Password: ')
    )

    if not api.check_auth():
        print("Failed to authenticate with GitHub")
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
