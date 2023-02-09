import pytest

from relint.config import FilenameFileMatcher, RegexFileMatcher, load_config

CONFIG_FILE__NO_FILE_PATTERN = """
- name: No ToDo
  pattern: "[tT][oO][dD][oO]"
  hint: Get it done right away!
"""

CONFIG_FILE__SPECIFIC_FILE_PATERN = """
- name: No ToDo
  pattern: "[tT][oO][dD][oO]"
  hint: Get it done right away!
  filePattern: .*\.py
"""  # NoQA

CONFIG_FILE__MULTIPLE_FILE_PATTERN_INVALID = """
- name: No ToDo
  pattern: "[tT][oO][dD][oO]"
  hint: Get it done right away!
  filePattern:
    - .*\.py
    - \/management\/commands\/.*\.py
"""  # NoQA

CONFIG_FILE__FILENAME = """
- name: No ToDo
  pattern: "[tT][oO][dD][oO]"
  hint: Get it done right away!
  filename: "**/test_*.py"
"""

CONFIG_FILE__FILENAME_LIST = """
- name: No ToDo
  pattern: "[tT][oO][dD][oO]"
  hint: Get it done right away!
  filename:
    - "**/test_*.py"
"""

CONFIG_FILE__MULTIPLE_FILENAMES = """
- name: No ToDo
  pattern: "[tT][oO][dD][oO]"
  hint: Get it done right away!
  filename:
    - "**/test_*.py"
    - "conftest.py"
    - "**/conftest.py"
"""


class TestConfigFileNamePattern:
    @staticmethod
    def get_relint_test_from_config_file(tmpdir, config_content):
        config_file = tmpdir.join(".relint.yml")
        config_file.write(config_content)
        return list(load_config(path=config_file, fail_warnings=True))

    def test_default_file_pattern(self, tmpdir):
        tests = self.get_relint_test_from_config_file(
            tmpdir, CONFIG_FILE__NO_FILE_PATTERN)
        assert tests[0].file_pattern == RegexFileMatcher(r".*")

    @pytest.mark.parametrize(
        "filename, is_match",
        (
            ("foo/bar.csv", True),
            ("foo_bar.xyz", True),
            ("foo/eggs/on/beckon/bar.foo", True),
            ("test.py", True),
        )
    )
    def test_default_file_pattern_matches_all_kind_of_files(
            self, filename, is_match, tmpdir
    ):
        tests = self.get_relint_test_from_config_file(
            tmpdir, CONFIG_FILE__NO_FILE_PATTERN)
        assert tests[0].file_pattern.match(filename) == is_match

    def test_specific_file_pattern(self, tmpdir):
        tests = self.get_relint_test_from_config_file(
            tmpdir, CONFIG_FILE__SPECIFIC_FILE_PATERN)
        assert tests[0].file_pattern == RegexFileMatcher(r".*\.py")

    @pytest.mark.parametrize(
        "filename, is_match",
        (
            ("foo.py", True),
            ("bar/foo.py", True),
            ("foo/bar.csv", False),
            ("foo_bar.xyz", False),
            ("foo/eggs/on/beckon/bar.foo", False),
        )
    )
    def test_specific_file_pattern_matches_specific_files(
            self, filename, is_match, tmpdir
    ):
        tests = self.get_relint_test_from_config_file(
            tmpdir, CONFIG_FILE__SPECIFIC_FILE_PATERN)
        assert tests[0].file_pattern.match(filename) == is_match

    def test_filename(self, tmpdir):
        tests = self.get_relint_test_from_config_file(
            tmpdir, CONFIG_FILE__FILENAME)
        assert tests[0].file_pattern == FilenameFileMatcher("**/test_*.py")

    @pytest.mark.parametrize(
        "filename, is_match",
        (
            ("tests/test_foo.py", True),
            ("bar/tests/test_foo.py", True),
            ("bar/testing/bar/tests/test_foo.py", True),
            ("test.py", False),
            ("tests/foo.py", False),
            ("test_foo.py", False),
        )
    )
    def test_filename_matches_correct_filenames(self, filename, is_match, tmpdir):
        tests = self.get_relint_test_from_config_file(
            tmpdir, CONFIG_FILE__FILENAME_LIST)
        assert tests[0].file_pattern.match(filename) == is_match

    def test_multiple_filenames(self, tmpdir):
        tests = self.get_relint_test_from_config_file(
            tmpdir, CONFIG_FILE__MULTIPLE_FILENAMES)
        assert len(tests) == 3

    def test_multiple_file_patterns_invalid(self, tmpdir):
        with pytest.warns(UserWarning) as warnings:
            tests = self.get_relint_test_from_config_file(
                tmpdir, CONFIG_FILE__MULTIPLE_FILE_PATTERN_INVALID)

        expected_warning = "Your relint config is empty, no tests were executed."
        assert len(tests) == 0
        assert warnings[0].message.args[0] == expected_warning
