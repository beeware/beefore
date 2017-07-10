###########################################################################
# Check for the existence of a Developer Certificate of Origin
# in the commit.
###########################################################################

LABEL = 'DCO'


def prepare(directory):
    pass


def check(pull_request, commit, directory):
    expected_signoff = '\n\nSigned-off-by: %(name)s <%(email)s>' % commit.commit.committer

    if commit.message and expected_signoff in commit.message:
        print("DCO found.")
        return True

    print("No DCO found.")
    return False
