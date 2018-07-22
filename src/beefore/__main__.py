from argparse import ArgumentParser
import importlib
import os
import sys

import git

from . import github
from . import local


def main():
    "Perform pre-merge checks for a project"
    parser = ArgumentParser()

    # GitHub required arguments...
    username_arg = parser.add_argument(
        '--username', '-u', dest='username',
        help='The GitHub username to use when updating the project.'
    )
    repository_arg = parser.add_argument(
        '--repository', '-r', dest='repo_path',
        help='The name of the repository that contains the pull request.'
    )
    commit_arg = parser.add_argument(
        '--commit=', '-c', dest='sha',
        help='The hash of the commit to be checked.'
    )
    pull_request_arg = parser.add_argument(
        '--pull-request', '-p', dest='pull_request',
        help='The pull request containing the commit.'
    )

    # local required arguments ...
    parser.add_argument(
        '--branch', '-b', dest='branch', default='master',
        help='The branch to compare against.'
    )

    # Common arguments
    parser.add_argument(
        'check', metavar='check',
        help='Premerge check to run.')
    parser.add_argument(
        'directory', nargs='?', default='.',
        help='Path to directory containing code to check.')

    options = parser.parse_args()

    # Load the check module
    try:
        if '.' in options.check:
            module_name = options.check
        else:
            module_name = 'beefore.checks.{}'.format(options.check)

        check_module = importlib.import_module(module_name)
    except ImportError:
        print(
            '\n'
            "Unable to load check module '%s'" % options.check,
            file=sys.stderr
        )
        sys.exit(20)

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
        # If the provided directory is a Git checkout, then this
        # is a check running on a local code checkout.
        repository = git.Repo(options.directory)
        passed = local.check(
            check_module=check_module,
            directory=options.directory,
            repository=repository,
            branch=options.branch,
        )

    except git.InvalidGitRepositoryError:
        # Directory isn't a git checkout; that means it's a
        # code tarball from a Github Pull Request

        # Now we know it's a Github Pull Request, the Github-related
        # command line options are mandatory.
        # Reparse the options based on that new knowledge.
        username_arg.required = True
        repository_arg.required = True
        commit_arg.required = True
        pull_request_arg.required = True

        options = parser.parse_args()

        try:
            options.password = os.environ['GITHUB_ACCESS_TOKEN']
        except KeyError as e:
            print("GITHUB_ACCESS_TOKEN not found")
            sys.exit(1)

        passed = github.check(
            check_module=check_module,
            directory=options.directory,
            username=options.username,
            password=options.password,
            repo_path=options.repo_path,
            pull_request=options.pull_request,
            sha=options.sha,
        )

    print()
    if passed:
        print("%s: Pre-commit check passed." % options.check)
        sys.exit(0)
    else:
        print("%s: Pre-commit check FAILED." % options.check)
        sys.exit(1)


if __name__ == '__main__':
    main()
