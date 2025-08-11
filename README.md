## Extend the implementation of the Version class to allow it to be used for semantic comparison

Small explanation: I used the regex to parse version strings.
Then I implemented rich comparison methods(using @total_ordering) for Version class, using precedence rules.

Both regex and precedence rules are given in semver documentation (https://semver.org/). 
