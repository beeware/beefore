from __future__ import print_function

from distutils.core import Command
import os
import sys

from github3 import login
from github3.exceptions import GitHubError
import yaml

from .check import CheckModule
from .constants import *
from .checks import *


class beefore(Command):
    description = "Perform pre-merge checks for a project"

    user_options = [
        ('username=', 'u',
         'The GitHub username to use when updating the project.'),
        ('repository=', 'r',
         'The name of the repository that contains the pull request.'),
        ('commit-hash=', 'c',
         'The hash of the commit to be checked.'),
        ('pull-request=', 'p',
         'The pull request containing the commit.'),
    ]

    def initialize_options(self):
        self.username = None
        self.password = None
        self.owner = None
        self.repository = None
        self.commit_hash = None
        self.pull_request = None

    def finalize_options(self):
        if self.username is None:
            print(
                '\n'
                'GitHub username not specified. You need to provide\n',
                'a --username argument.',
                file=sys.stderr
            )
            sys.exit(1)

        if self.password is None:
            try:
                self.password = os.environ['BEEFORE_GITHUB_PASSWORD']
            except KeyError:
                print(
                    '\n'
                    'GitHub password not specified. Either provide a --password argument,\n'
                    'or export BEEFORE_GITHUB_PASSWORD into your environment',
                    file=sys.stderr
                )
                sys.exit(2)

        if self.repository is None:
            print(
                '\n'
                'GitHub repository not specified. You need to provide\n',
                'a --repository argument.',
                file=sys.stderr
            )
            sys.exit(4)

        # Read the configuration file
        with open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), '.beefore.yml')) as config_file:
            self.config = yaml.load(config_file)

    def run(self):
        try:
            self.github = login(self.username, password=self.password)
            self.user = self.github.user(self.username)
        except GitHubError as ghe:
            print(
                '\n'
                'Unable to log into GitHub: %s' % ghe,
                file=sys.stderr
            )
            sys.exit(10)

        try:
            print('Loading repository...')
            owner, repo_name = self.repository.split('/')
            repository = self.github.repository(owner, repo_name)
        except GitHubError as ghe:
            print(
                '\n'
                'Unable to load repository %s: %s' % (self.repository, ghe),
                file=sys.stderr
            )
            sys.exit(11)

        try:
            print('Loading pull request...')
            pull_request = repository.pull_request(self.pull_request)
        except GitHubError as ghe:
            print(
                '\n'
                'Unable to load pull request %s in %s: %s' % (self.pull_request, self.repository, ghe),
                file=sys.stderr
            )
            sys.exit(12)

        try:
            print('Loading commit...')
            commit = repository.commit(self.commit_hash)
        except GitHubError as ghe:
            print(
                '\n'
                'Unable to load commit %s: %s' % (self.pull_request, self.repository, ghe),
                file=sys.stderr
            )
            sys.exit(12)

        print("Run pre-merge checks...")
        self.check_modules = {}
        for check, config in self.config['checks'].items():
            try:
                check_module = CheckModule(check, config=self.config['checks'])
                self.check_modules[check] = check_module
            except ValueError:
                print(
                    '\n'
                    "Unable to load check module '%s'" % check,
                    file=sys.stderr
                )
                sys.exit(13)

            self.report_status(
                commit=commit,
                context='Beefore/%s' % check_module.label,
                state=PENDING,
                target_url=check_module.target_url,
                description=check_module.description(PENDING)
            )

        problem_checks = []
        for check in self.config['checks']:
            check_module = self.check_modules[check]
            print("Performing %s check..." % check_module.label)
            try:
                passed = check_module.check(self.user, pull_request, commit)

                if passed:
                    state = SUCCESS
                else:
                    state = FAILURE
                    problem_checks.append(check)

                self.report_status(
                    commit=commit,
                    context='Beefore/%s' % check_module.label,
                    state=state,
                    target_url=check_module.target_url,
                    description=check_module.description(state)
                )
            except Exception as e:
                print(e, file=sys.stderr)
                problem_checks.append(check)
                self.report_status(
                    commit=commit,
                    context='Beefore/%s' % check_module.label,
                    state=ERROR,
                    target_url=check_module.target_url,
                    description=check_module.description(ERROR)
                )

        if problem_checks:
            print("Found a problem with the following checks: %s" % ', '.join(problem_checks))
        else:
            print("Success! All pre-commit checks passed!")

    def report_status(self, commit, context, state, target_url, description):
        print('...', description)
        url = commit._api.replace('commits', 'statuses')
        payload = {
            'context': context,
            'state': state,
            'target_url': target_url,
            'description': description,
        }
        response = commit._post(url, payload)
        if not response.ok:
            raise GitHubError(response.reason)
