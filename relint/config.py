import collections
import fnmatch
import re
import warnings
from abc import ABC, abstractmethod

import yaml

from .exceptions import ConfigError

Test = collections.namedtuple(
    "Test",
    (
        "name",
        "pattern",
        "hint",
        "file_pattern",
        "error",
    ),
)


class FileMatcher(ABC):
    """
    Adapts different file pattern matching methods to be exchangeable.

    Implements match method -> returns True / False
    """
    def __init__(self, pattern):
        self.pattern = pattern

    def __eq__(self, other):
        return self.pattern == other.pattern

    @abstractmethod
    def match(self, filename):
        raise NotImplementedError


class FilenameFileMatcher(FileMatcher):
    """Adapter for fnmatch."""
    def match(self, filename):
        return fnmatch.fnmatchcase(filename, self.pattern)


class RegexFileMatcher(FileMatcher):
    """Adapter for regex."""
    def __init__(self, pattern):
        self.pattern = re.compile(pattern)

    def match(self, filename):
        if self.pattern.match(filename):
            return True
        return False


def file_patterns(test):
    """
    Generates file patterns valid for test.

    Each file pattern is object that has match method,
    so it can be checked against a single file name.
    """
    if "filename" in test:
        if isinstance(test["filename"], str):
            yield FilenameFileMatcher(test["filename"])
        elif isinstance(test["filename"], list):
            for filename in test["filename"]:
                yield FilenameFileMatcher(filename)
    else:
        yield RegexFileMatcher(test.get("filePattern", ".*"))


def load_config(path, fail_warnings):
    with open(path) as fs:
        try:
            for test in yaml.safe_load(fs):
                for pattern in file_patterns(test):
                    yield Test(
                        name=test["name"],
                        pattern=re.compile(test["pattern"], re.MULTILINE),
                        hint=test.get("hint"),
                        file_pattern=pattern,
                        error=test.get("error", True) or fail_warnings,
                    )
        except yaml.YAMLError as e:
            raise ConfigError("Error parsing your relint config file.") from e
        except TypeError:
            warnings.warn(
                "Your relint config is empty, no tests were executed.", UserWarning
            )
        except (AttributeError, ValueError) as e:
            raise ConfigError(
                "Your relint config is not a valid YAML list of relint tests."
            ) from e
