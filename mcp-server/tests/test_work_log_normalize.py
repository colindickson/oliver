"""Tests for project-name normalization in the work log tool."""

import json

from tools.work_log import _normalize_project_name, log_work


class TestNormalizeProjectName:
    def test_absolute_path_returns_basename(self):
        assert _normalize_project_name("/Users/cdickson/code/epsilon/poka") == "poka"

    def test_absolute_path_trailing_slash_returns_basename(self):
        assert _normalize_project_name("/Users/cdickson/code/epsilon/poka/") == "poka"

    def test_tilde_path_returns_basename(self):
        assert _normalize_project_name("~/code/epsilon/poka") == "poka"

    def test_plain_name_unchanged(self):
        assert _normalize_project_name("poka") == "poka"

    def test_relative_team_project_unchanged(self):
        assert _normalize_project_name("team/project") == "team/project"

    def test_root_slash_unchanged(self):
        assert _normalize_project_name("/") == "/"

    def test_empty_string_unchanged(self):
        assert _normalize_project_name("") == ""

    def test_whitespace_unchanged(self):
        assert _normalize_project_name("   ") == "   "


class TestLogWorkSeam:
    def test_log_work_normalizes_project_name(self, patched_get_session):
        result = json.loads(
            log_work(
                project_name="/Users/cdickson/code/epsilon/poka",
                description="did some work",
            )
        )
        assert "error" not in result, result
        assert result["project_name"] == "poka"
