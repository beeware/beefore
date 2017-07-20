import re

FILE_START = re.compile("diff --git a/(.*) b/(.*)")
LINE_RANGE = re.compile("@@ -(\d+),(\d+) \+(\d+),(\d+) @@")


def positions(diff, filename):
    """Given a diff payload, look for all the line ranges described for a given file.

    Returns a map of source file lines, mapped to the position in the diff
    that the line is referenced.
    """
    current_file = None
    start = None
    offset = None
    for i, d in enumerate(diff):
        match = FILE_START.match(d)
        if match:
            if match.group(1) == filename:
                current_file = {}
            else:
                if current_file is not None:
                    return current_file
        elif current_file is not None:
            match = LINE_RANGE.match(d)
            if match:
                # Found the start of a new range in the file
                first_line = int(match.group(3))
                start = i + 1
                offset = 1 if match.group(1) == '0' else 0
            elif start and len(d) > 0:
                if d[0] == '-':
                    offset += 1
                else:
                    current_file[i - start - offset + first_line] = i + 1

    return current_file
