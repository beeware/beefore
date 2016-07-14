###########################################################################
# Check for the existence of a Developer Certificate of Origin
# in the commit.
###########################################################################

LABEL = 'DCO'
DESCRIPTION = {
    'pending': 'Checking for a DCO...',
    'success': 'DCO found and verified!',
    'failure': "Couldn't find a DCO.",
    'error': 'Error while checking for DCO.',
}


def check(reviewer, pull_request, commit, config):
    expected_signoff = '\n\nSigned-off-by: %(name)s <%(email)s>' % commit.commit.committer

    if expected_signoff in commit.message:
        return True

    return False
