import importlib
import os

from .constants import *


class CheckModule:
    def __init__(self, path, config=None):
        self.path = path
        self.config = config
        try:
            self.module = importlib.import_module('.%s' % path, 'beefore.checks')
        except ImportError:
            try:
                self.module = importlib.import_module('%s' % path)
            except ImportError:
                raise ValueError("Unable to load check module '%s'" % path)

    @property
    def label(self):
        return getattr(self.module, 'LABEL', self.path)

    @property
    def target_url(self):
        return getattr(self.module, 'TARGET_URL', os.environ.get('BEEFORE_TARGET_URL', 'http://pybee.org'))

    def description(self, state, **context):
        return getattr(self.module, 'DESCRIPTION', {}).get(
            state,
            {
                PENDING: 'Performing %s checks...' % self.label,
                FAILURE: 'Failed %s check.' % self.label,
                SUCCESS: 'Passed %s check.' % self.label,
                ERROR: 'Error while running %s checks.' % self.label,
            }[state]
        ) % context

    def check(self, reviewer, pull_request, commit):
        return self.module.check(reviewer, pull_request, commit, self.config)
