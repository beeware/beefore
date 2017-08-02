from argparse import ArgumentParser
import importlib
import os
import sys

from github3 import login
from github3.exceptions import GitHubError


def run(options):
    try:
        github = login(options.username, password=options.password)
    except GitHubError as ghe:
        print(
            '\n'
            'Unable to log into GitHub: %s' % ghe,
            file=sys.stderr
        )
        sys.exit(10)

    try:
        print('Loading repository %s...' % options.repository)
        owner, repo_name = options.repository.split('/')
        repository = github.repository(owner, repo_name)
    except GitHubError as ghe:
        print(
            '\n'
            'Unable to load repository %s: %s' % (repository, ghe),
            file=sys.stderr
        )
        sys.exit(11)

    try:
        print('Loading pull request #%s...' % options.pull_request)
        pull_request = repository.pull_request(options.pull_request)
    except GitHubError as ghe:
        print(
            '\n'
            'Unable to load pull request %s in %s: %s' % (options.pull_request, repository, ghe),
            file=sys.stderr
        )
        sys.exit(12)

    try:
        print('Loading commit %s...' % options.sha)
        commit = repository.commit(options.sha)
    except GitHubError as ghe:
        print(
            '\n'
            'Unable to load commit %s: %s' % (options.sha, ghe),
            file=sys.stderr
        )
        sys.exit(12)

    print("Running %s check..." % options.check)
    try:
        check_module = importlib.import_module('beefore.checks.%s' % options.check)
    except ImportError:
        print(
            '\n'
            "Unable to load check module '%s'" % options.check,
            file=sys.stderr
        )
        sys.exit(13)

    check_module.prepare(os.path.abspath(options.directory))

    print('==========' * 8)
    passed = check_module.check(pull_request, commit, os.path.abspath(options.directory))
    if passed:
        print("%s: Pre-commit checks passed." % options.check)
        return 0
    else:
        print("%s: Pre-commit checks did NOT pass." % options.check)
        return 1


def main():
    "Perform pre-merge checks for a project"
    parser = ArgumentParser()

    parser.add_argument(
        '--username', '-u', dest='username', required=True,
        help='The GitHub username to use when updating the project.'),
    parser.add_argument(
        '--repository', '-r', dest='repository', required=True,
        help='The name of the repository that contains the pull request.'),
    parser.add_argument(
        '--commit=', '-c', dest='sha', required=True,
        help='The hash of the commit to be checked.'),
    parser.add_argument(
        '--pull-request', '-p', dest='pull_request', required=True,
        help='The pull request containing the commit.'),
    parser.add_argument(
        'check', metavar='check',
        help='Premerge check to run.')
    parser.add_argument(
        'directory', metavar='directory',
        help='Path to directory containing code to check.')
    options = parser.parse_args()

    # Load sensitive environment variables from a .env file
    try:
        with open('.env') as envfile:
            for line in envfile:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())
    except FileNotFoundError:
        pass

    try:
        options.password = os.environ['GITHUB_ACCESS_TOKEN']
    except KeyError as e:
        print("GITHUB_ACCESS_TOKEN not found")
        sys.exit(1)

    return run(options)


if __name__ == '__main__':
    main()
