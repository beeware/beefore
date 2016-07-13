from __future__ import print_function

from distutils.core import Command
import os
import sys

from github3 import login
from github3.models import GitHubError


class beefore(Command):
    description = "Perform pre-merge checks for a project"

    user_options = [
        ('install', None,
         'Create the Github resources for this project'),
        ('github-username', None,
         'The GitHub username to use when updating the project.'),
        ('github-password', None,
         'The password (or access token) for the GitHub user.'),
    ]

    def initialize_options(self):
        self.install = False
        self.github_user = None
        self.github_password = None

    def finalize_options(self):
        if self.github_user is None:
            try:
                self.github_user = os.environ['BEEFORE_GITHUB_USERNAME']
            except KeyError:
                print(
                    '\n'
                    'GitHub username not specified. Either provide a --github-username argument,\n'
                    'or export BEEFORE_GITHUB_USERNAME into your environment',
                    file=sys.stderr
                )
                sys.exit(1)

        if self.github_password is None:
            try:
                self.github_password = os.environ['BEEFORE_GITHUB_PASSWORD']
            except KeyError:
                print(
                    '\n'
                    'GitHub password not specified. Either provide a --github-passowrd argument,\n'
                    'or export BEEFORE_GITHUB_PASSWORD into your environment',
                    file=sys.stderr
                )
                sys.exit(2)

        try:
            self.github = login(self.github_user, password=self.github_password)
        except GitHubError as ghe:
            print(
                '\n'
                'Unable to log into GitHub: %s' % ghe,
                file=sys.stderr
            )
            sys.exit(3)

    def run(self):
        if self.install:
            self.install_hooks()
        else:
            print("Run pre-merge checks...")
            try:
                print('Freakboy is: %s' % self.github.user('freakboy3742'))
            except GitHubError as ghe:
                print(
                    '\n'
                    'Unable get GitHub user: %s' % ghe,
                    file=sys.stderr
                )
                sys.exit(3)

    def install_hooks(self):
        print("Install hooks for %s:%s" % (self.github_user, self.github_password))
