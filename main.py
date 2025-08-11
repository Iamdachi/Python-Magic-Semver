import re
from typing import Optional
from functools import total_ordering


@total_ordering
class Version:
    def __init__(self, version: str):
        version_dict = self.parse_semver(version)
        try:
            self.major = int(version_dict["major"])
            self.minor = int(version_dict["minor"])
            self.patch = int(version_dict["patch"])
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid version number: {version}") from e
        self.pre_release = version_dict.get("pre_release")
        self.build_metadata = version_dict.get("build_metadata")

    @staticmethod
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
            (?:-?(?P<pre_release>
                (?:0|[1-9]\d*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*)
                (?:\.(?:0|[1-9]\d*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*))*
            ))?
            (?:\+(?P<build_metadata>
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

    def compare_pre_release(self, other: "Version") -> bool:
        """Return True if self.pre_release has lower precedence than other.pre_release."""
        if self.pre_release is None and other.pre_release is None:
            return False
        if (self.pre_release is None) ^ (other.pre_release is None):
            return other.pre_release is None

        self_parts = self.pre_release.split(".")
        other_parts = other.pre_release.split(".")

        for self_part, other_part in zip(self_parts, other_parts):
            if self_part != other_part:
                if self_part.isdigit() and other_part.isdigit():
                    return int(self_part) < int(other_part)
                if self_part.isdigit() or other_part.isdigit():
                    return self_part.isdigit()
                return self_part < other_part
        return len(self_parts) < len(other_parts)

    def __eq__(self, other) -> bool:
        return (self.major == other.major
                and self.minor == other.minor
                and self.patch == other.patch
                and self.pre_release == other.pre_release)

    def __lt__(self, other) -> bool:
        if self == other:
            return False

        if self.major != other.major:
            return self.major < other.major

        if self.minor != other.minor:
            return self.minor < other.minor

        if self.patch != other.patch:
            return self.patch < other.patch

        return self.compare_pre_release(other)


def main():
    to_test = [
        ("1.0.0", "2.0.0"),
        ("1.0.0", "1.42.0"),
        ("1.2.0", "1.2.42"),
        ("1.1.0-alpha", "1.2.0-alpha.1"),
        ("1.0.1b", "1.0.10-alpha.beta"),
        ("1.0.0-rc.1", "1.0.0"),
        ("1.0.0-beta", "1.0.0-beta.2"),
        ("1.0.0-beta.2", "1.0.0-beta.11"),
        ("1.0.0-alpha", "1.0.0-alpha.1"),  # more identifiers = higher
        ("1.0.0-alpha.1", "1.0.0-alpha.beta"),  # numeric < alphanumeric
        ("1.0.0-alpha.beta", "1.0.0-beta"),  # alpha < beta
        ("1.0.0-beta", "1.0.0-beta.2"),  # beta < beta.2
        ("1.0.0-beta.11", "1.0.0-rc.1"),  # beta.11 < rc.1
        ("1.0.0-rc.1", "1.0.0-rc.2"),  # rc.1 < rc.2
        ("1.0.0-rc.2", "1.0.0-rc.10"),  # numeric compare
        ("1.0.0-rc.10", "1.0.0"),  # prerelease < release
        ("1.0.0-alpha", "1.0.0"),  # prerelease < release
        ("1.0.0-0.3.7", "1.0.0-alpha"),  # numeric < alpha
        ("1.0.0-alpha", "1.0.0-alpha.0"),  # alpha < alpha.0
        ("1.0.0-alpha.0", "1.0.0-alpha.a"),  # numeric < alpha
        ("1.0.0-alpha.0.0", "1.0.0-alpha.0.a"),  # pre-release: numeric < lexical
    ]

    for left, right in to_test:
        assert Version(left) < Version(right), "le failed"
        assert Version(right) > Version(left), "ge failed"
        assert Version(right) != Version(left), "neq failed"

    to_test_equality = [
        ("1.0.0-alpha", "1.0.0-alpha"),
        ("1.0.0", "1.0.0+build.1"),  # build metadata ignored
        ("1.0.0+build.1", "1.0.0+build.2"),  # build metadata ignored
        ("1.0.0-alpha+exp.sha.5114f85", "1.0.0-alpha"),  # build metadata ignored
    ]

    for left, right in to_test_equality:
        assert Version(right) == Version(left), "eq failed"


if __name__ == "__main__":
    main()
