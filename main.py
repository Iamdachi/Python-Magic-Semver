import re
from typing import Optional


def parse_semver(version: str) -> dict[str, Optional[str]]:
    """
    Parse a semantic version string into its components.

    Parameters:
        version (str): A version string like "1.0.0-b+a".

    Returns:
        dict: A dictionary with keys: 'major', 'minor', 'patch',
              'prerelease', and 'buildmetadata'.

    Notes:
        To support inputs like "1.0.1b", the regex was modified by replacing
        '-(?P<prerelease>...)' with '-?(?P<prerelease>...)' to allow an optional dash.
    """
    semver_regex = re.compile(
        r"""
        ^(?P<major>0|[1-9]\d*)
        \.
        (?P<minor>0|[1-9]\d*)
        \.
        (?P<patch>0|[1-9]\d*)
        (?:-?(?P<prerelease>
            (?:0|[1-9]\d*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*)
            (?:\.(?:0|[1-9]\d*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*))*
        ))?
        (?:\+(?P<buildmetadata>
            [0-9a-zA-Z-]+
            (?:\.[0-9a-zA-Z-]+)*
        ))?
        $
        """,
        re.VERBOSE,
    )
    match = semver_regex.match(version)
    if not match:
        raise ValueError(f"Invalid version: {version}")
    return match.groupdict()

class Version:
    def __init__(self, version: str):
        version_dict = parse_semver(version)
        try:
            self.major = int(version_dict["major"])
            self.minor = int(version_dict["minor"])
            self.patch = int(version_dict["patch"])
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid version number: {version}") from e
        self.prerelease = version_dict.get("prerelease")
        self.buildmetadata = version_dict.get("buildmetadata")


    def compare_pre_release(self, other):
        """ Returns true if self.preRelease < other.preRelease"""
        if (self.prerelease is None) ^ (other.prerelease is None):
            return other.prerelease is None

        s_pre = self.prerelease.split(".")
        o_pre = other.prerelease.split(".")

        for i, _ in enumerate(s_pre):
            if i >= len(o_pre):
                return False

            if s_pre[i] != o_pre[i]:
                if s_pre[i].isdigit() and o_pre[i].isdigit():
                    return int(s_pre[i]) < int(o_pre[i])

                if s_pre[i].isdigit() or o_pre[i].isdigit():
                    return s_pre[i].isdigit()
                return s_pre[i] < o_pre[i]

        return False

    def __lt__(self, other):
        if self == other:
            return False

        if self.major != other.major:
            return self.major < other.major

        if self.minor != other.minor:
            return self.minor < other.minor

        if self.patch != other.patch:
            return self.patch < other.patch

        return self.compare_pre_release(other)


    def __eq__(self, other):
        return (self.major == other.major
                and self.minor == other.minor
                and self.patch == other.patch
                and self.prerelease == other.prerelease)


    def __le__(self, other):
        return self == other or self < other

    def __gt__(self, other):
        return self != other and not self < other

    def __ge__(self, other):
        return self == other or self > other

    def __ne__(self, other):
        return not self == other

def main():
    to_test = [
        ("1.0.0", "2.0.0"),
        ("1.0.0", "1.42.0"),
        ("1.2.0", "1.2.42"),
        ("1.1.0-alpha", "1.2.0-alpha.1"),
        ("1.0.1b", "1.0.10-alpha.beta"),
        ("1.0.0-rc.1", "1.0.0"),
    ]

    for left, right in to_test:
        assert Version(left) < Version(right), "le failed"
        assert Version(right) > Version(left), "ge failed"
        assert Version(right) != Version(left), "neq failed"

if __name__ == "__main__":
    print((parse_semver("1.0.0b+a")))
    main()
