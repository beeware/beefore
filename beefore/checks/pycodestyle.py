###########################################################################
# Check if any of the Python files touched by the commit have
# code style problems.
###########################################################################
import os.path
import requests
import sys
import subprocess


LABEL = 'PyCodeStyle'
DESCRIPTION = {
    'pending': 'Checking Python code style...',
    'success': 'Code meets Python style standards!',
    'failure': 'Found some Python code style problems.',
    'error': 'Error while checking Python code style.',
}


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
        # commit.add_comment(
        #     "At column %(col)d, found [%(code)s: %(description)s](http://.../%(code)s)" % {
        #         'col': self.col,
        #         'code': self.code,
        #         'description': self.description
        #     },
        #     filename=self.filename,
        #     line=self.line,
        #     author=reviewer
        # )

    @staticmethod
    def find(filename, content, config):
        cmd_line = [
            sys.executable, '-m', 'flake8',
            '--config', '.flake8.ini',
            '--stdin-display-name', filename,
            '-'
        ]

        proc = subprocess.Popen(
            cmd_line,
            cwd=os.path.dirname(os.path.abspath(sys.argv[1])),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        out, err = proc.communicate(content)

        out_lines = out.decode('utf-8').strip().split('\n')

        problems = []
        for problem in out_lines:
            fname, line, col, remainder = problem.split(':', 4)
            code, description = remainder.strip().split(' ', 1)
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
        if os.path.splitext(changed_file['filename'])[-1] == '.py':
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
