###########################################################################
# Check for the existence of a Developer Certificate of Origin
# in the commit.
###########################################################################

LABEL = 'DCO'


def check(pull_request, commit, directory):
    expected_signoff = '\n\nSigned-off-by: %(name)s <%(email)s>' % commit.commit.committer

    if commit.message and expected_signoff in commit.message:
        return True

    return False
