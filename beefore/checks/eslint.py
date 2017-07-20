###########################################################################
# Check if any of the Javascript files touched by the commit have
# code style problems.
###########################################################################
import json
import os.path
import re
import sys
import subprocess

import yaml

from beefore import diff


LABEL = 'ESLint'
LINT_OUTPUT = re.compile('(.*?): line (\d+), col (\d+), (.*?) - (.*) \((.*)\)')


class Lint:
    def __init__(self, filename, line, col, code, description):
        self.filename = filename
        self.line = line
        self.col = col
        self.code = code
        self.description = description

    def __str__(self):
        return 'Line %s, col %s: [%s] %s' % (self.line, self.col, self.code, self.description)

    def add_comment(self, pull_request, commit, position):
        pull_request.create_review_comment(
            body="At column %(col)d: [(%(code)s) %(description)s](http://eslint.org/docs/rules/%(code)s)" % {
                'col': self.col,
                'code': self.code,
                'description': self.description
            },
            commit_id=commit.sha,
            path=self.filename,
            position=position,
        )

    @staticmethod
    def find(directory, filename):
        proc = subprocess.Popen(
            [
                '../node_modules/.bin/eslint',
                '--format', 'compact',
                filename,
            ],
            cwd=directory,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        out, err = proc.communicate()

        matches = LINT_OUTPUT.findall(out.decode('utf-8'))
        problems = []
        for full_name, line, col, level, description, code in matches:
            problems.append(Lint(
                filename=filename,
                line=int(line),
                col=int(col),
                code=code,
                description=description,
            ))

        return problems

SIMPLE_COMMENT = re.compile('//.*')
MULTILINE_COMMENT = re.compile('/\*.*?\*/', re.DOTALL)
SYMBOL_TO_STRING = re.compile('([a-zA-Z_][-\w_]*)\s*:')

def clean_json(raw):
    # Replace  //-style comments
    clean = SIMPLE_COMMENT.sub('', raw)

    # Replace  /* */-style comments
    clean = MULTILINE_COMMENT.sub('', clean)

    # Replace unadorned foo: 42 with "foo": 42
    clean = SYMBOL_TO_STRING.sub('"\\1":', clean)
    return clean


def install_eslint_config(directory):
    if os.path.isfile(os.path.join(directory, '.eslintrc')):
        with open(os.path.join(directory, '.eslintrc')) as config_file:
            config = json.loads(clean_json(config_file.read()))
    elif os.path.isfile(os.path.join(directory, '.eslintrc.json')):
        with open(os.path.join(directory, '.eslintrc.json')) as config_file:
            config = json.loads(clean_json(config_file.read()))
    elif os.path.isfile(os.path.join(directory, '.eslintrc.yml')):
        with open(os.path.join(directory, '.eslintrc.yml')) as config_file:
            config = yaml.load(config_file.read())
    else:
        config_file = None

    if config_file is None:
        print("No ESLint configuration file found.")
    else:
        try:
            extends_name = config['extends']
            print("Installing base ESLint configuration 'eslint-config-%s'..." % extends_name)
            proc = subprocess.Popen(['npm', 'install', 'eslint-config-%s' % extends_name])
            proc.wait()
        except KeyError as e:
            print("No base ESLint configuration specified.")


def prepare(directory):
    install_eslint_config(directory)


def check(pull_request, commit, directory):
    problem_found = False

    diff_content = pull_request.diff().decode('utf-8').split('\n')

    for changed_file in commit.files:
        if os.path.splitext(changed_file['filename'])[-1] == '.js':
            print ("  * %s" % changed_file['filename'])

            # Build a map of line numbers to diff positions
            diff_position = diff.positions(diff_content, changed_file['filename'])

            problems = Lint.find(
                directory=directory,
                filename=changed_file['filename'],
            )

            for problem in problems:
                try:
                    position = diff_position[problem.line]
                    problem_found = True
                    print('    - %s' % problem)
                    problem.add_comment(pull_request, commit, position)
                except KeyError:
                    # Line doesn't exist in the diff; so we can ignore this problem
                    print('     - [IGNORED] %s' % problem)

    return not problem_found
