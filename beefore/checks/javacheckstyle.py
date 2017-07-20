###########################################################################
# Check if any of the Python files touched by the commit have
# code style problems.
###########################################################################
import os.path
import re
import sys
import subprocess

from beefore import diff


LABEL = 'Java CheckStyle'
LINT_OUTPUT = re.compile("\[checkstyle\] \[(ERROR)\] (.*?):(\d+): (.*) \[(.*)\]")

class Lint:
    def __init__(self, filename, line, code, description):
        self.filename = filename
        self.line = line
        self.code = code
        self.description = description

    def __str__(self):
        return 'Line %s: [%s] %s' % (self.line, self.code, self.description)

    def add_comment(self, pull_request, commit, position):
        pull_request.create_review_comment(
            # body="At column %(col)d: [(%(code)s) %(description)s](http://.../%(code)s)" % {
            body="[%(code)s] %(description)s" % {
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
            ['ant', 'checkstyle'],
            cwd=directory,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        out, err = proc.communicate()

        matches = LINT_OUTPUT.findall(err.decode('utf-8'))
        problems = {}
        for severity, filename, line, description, code in matches:
            problems.setdefault(filename, []).append(Lint(
                filename=filename,
                line=int(line),
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
        if os.path.splitext(changed_file['filename'])[-1] == '.java':
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
