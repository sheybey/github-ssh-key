# GitHub SSH key uploader

A task I find myself doing often after setting up a new virtual machine is
generating an SSH key and adding it to my GitHub account. This script
automates this process.

## Usage

The script is written in Python 3 and uses Requests, which is installed by default on most modern Linux distributions. Run the script and it will prompt you for your GitHub username and password (and OTP token if neccessary.) 