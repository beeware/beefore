###########################################################################
# Check if any of the Python files touched by the commit have
# code style problems.
###########################################################################
import os.path
import sys
import subprocess

from beefore import diff


LABEL = 'PyCodeStyle'


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
            # body="At column %(col)d: [(%(code)s) %(description)s](http://.../%(code)s)" % {
            body="At column %(col)d: (%(code)s) %(description)s" % {
                'col': self.col,
                'code': self.code,
                'description': self.description
            },
            commit_id=commit.sha,
            path=self.filename,
            position=position,
        )

    @staticmethod
    def find(directory):
        proc = subprocess.Popen(
            ['flake8'],
            cwd=directory,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        out, err = proc.communicate()

        out_lines = [line for line in out.decode('utf-8').strip().split('\n') if line]

        problems = {}
        for problem in out_lines:
            fname, line, col, remainder = problem.split(':', 4)
            filename = os.path.abspath(fname)
            code, description = remainder.strip().split(' ', 1)
            problems.setdefault(filename, []).append(Lint(
                filename=filename,
                line=int(line),
                col=int(col),
                code=code,
                description=description,
            ))

        return problems


def prepare(directory):
    pass


def check(pull_request, commit, directory):
    problem_found = False

    problems = Lint.find(directory=directory)

    diff_content = pull_request.diff().decode('utf-8').split('\n')
    for changed_file in commit.files:
        if os.path.splitext(changed_file['filename'])[-1] == '.py':
            filename = os.path.join(directory, changed_file['filename'])
            print("  * %s" % changed_file['filename'])

            # Build a map of line numbers to diff positions
            diff_position = diff.positions(diff_content, changed_file['filename'])

            for problem in sorted(problems[filename], key=lambda p: p.line):
                try:
                    position = diff_position[problem.line]
                    problem_found = True
                    print('    - %s' % problem)
                    problem.add_comment(pull_request, commit, position)
                except KeyError:
                    # Line doesn't exist in the diff; so we can ignore this problem
                    print('     - [IGNORED] %s' % problem)

    return not problem_found
