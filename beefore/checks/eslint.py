###########################################################################
# Check if any of the Javascript files touched by the commit have
# code style problems.
###########################################################################
import os.path
import re
import requests
import sys
import subprocess

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
            body="At column %(col)d: [(%(code)s) %(description)s](http://.../%(code)s)" % {
                'col': self.col,
                'code': self.code,
                'description': self.description
            },
            commit_id=commit.sha,
            path=self.filename,
            position=position,
        )

    @staticmethod
    def find(filename, content):
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
        for full_name, line, col, level, description, code in matches:
            problems.append(Lint(
                filename=filename,
                line=int(line),
                col=int(col),
                code=code,
                description=description,
            ))

        return problems


def check(pull_request, commit, directory):
    problem_found = False

    diff_content = pull_request.diff().decode('utf-8').split('\n')

    for changed_file in commit.files:
        if os.path.splitext(changed_file['filename'])[-1] == '.js':
            print ("  * %s" % changed_file['filename'])

            # Build a map of line numbers to diff positions
            diff_position = diff.positions(diff_content, changed_file['filename'])

            # If a directory has been provided, use that as the source of
            # the files. Otherwise, download the file blob.
            if directory is None:
                response = requests.get(changed_file['raw_url'])
                content = response.content
            else:
                with open(os.path.join(directory, changed_file['filename'])) as fp:
                    content = fp.read().encode('utf-8')

            problems = Lint.find(
                filename=changed_file['filename'],
                content=content,
            )

            print(diff_position)
            for problem in problems:
                try:
                    print(problem.line)
                    position = diff_position[problem.line]
                    print('    - %s' % problem)
                    problem.add_comment(pull_request, commit, position)
                except KeyError:
                    # Line doesn't exist in the diff; so we can ignore this problem
                    pass

    return not problem_found
