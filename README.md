# GitHub SSH key uploader

A task I find myself doing often after setting up a new virtual machine is
generating an SSH key and adding it to my GitHub account. This script
automates this process.

## Usage

The script is written in Python 3 and uses Requests, which is installed by
default on most modern Linux distributions. Run the script and it will prompt
you to authenticate with GitHub. Once you have done so, the script will add
the default SSH key (`.ssh/id_rsa`) to your account, generating it first if
necessary.
