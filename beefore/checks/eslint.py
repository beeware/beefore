###########################################################################
# Check if any of the Python files touched by the commit have
# code style problems.
###########################################################################
import os.path
import re
import requests
import sys
import subprocess


LABEL = 'ESLint'
DESCRIPTION = {
    'pending': 'Checking Javascript code style...',
    'success': 'Code meets JavaScript style standards!',
    'failure': 'Found some JavaScript code style problems.',
    'error': 'Error while checking JavaScript code style.',
}

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

    def add_comment(self, reviewer, commit):
        pass

    @staticmethod
    def find(filename, content, config):
        cmd_line = [
            'eslint',
            '--config', '.eslintrc.yml',
            '--format', 'compact',
            '--stdin',
            '--stdin-filename', filename,
        ]
        proc = subprocess.Popen(
            cmd_line,
            cwd=os.path.dirname(os.path.abspath(sys.argv[1])),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        out, err = proc.communicate(content)

        matches = LINT_OUTPUT.findall(out.decode('utf-8'))
        problems = []
        for filename, line, col, level, description, code in matches:
            problems.append(Lint(
                filename=filename,
                line=line,
                col=col,
                code=code,
                description=description,
            ))

        return problems


def check(reviewer, pull_request, commit, config):
    problem_found = False
    for changed_file in commit.files:
        if os.path.splitext(changed_file['filename'])[-1] == '.js':
            print ("  * %s" % changed_file['filename'])

            response = requests.get(changed_file['raw_url'])

            problems = Lint.find(
                filename=changed_file['filename'],
                content=response.content,
                config=config
            )
            for problem in problems:
                print('    - %s' % problem)
                problem.add_comment(reviewer, commit)

    return problem_found
