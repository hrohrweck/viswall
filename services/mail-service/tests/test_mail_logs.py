"""Tests for the filtered, paginated GET /logs endpoint (X-Instance-Key protected)."""
import os

import pytest
from fastapi.testclient import TestClient

import mail_agent

KEY = "test-key-123"
HEADERS = {"X-Instance-Key": KEY}

# Realistic exim mainlog fixture lines, oldest→newest (L0's seconds are :00
# so the 16-char since-bound padding is observable; L2 sits inside minute
# 10:05 so the until-bound ":59" padding is observable).
L0 = "2026-11-09 09:59:00 1xQaAA-000000000b0-A0A <= dawn@external.example H=mail.example.net [192.0.2.10] P=esmtps S=2048"
L1 = "2026-11-09 10:00:01 1xQaAB-000000000b0-AAA <= alice@external.example H=mail-wr1-f70.google.com [209.85.222.70] P=esmtps S=1024"
L2 = "2026-11-09 10:05:02 1xQaAB-000000000b0-AAA => bob <bob@viswall.test> R=virtual_mailbox T=dovecot_lmtp C=\"250 2.0.0 ok\""
L3 = "2026-11-09 11:00:03 rejected H=(spam.example) [192.0.2.99] F=<spam@spam.example> after DATA: spam score 14.2 above threshold"
L4 = "2026-11-09 11:30:04 1xQaCD-000000000b0-BBB => carol <carol@other.test> R=virtual_mailbox T=dovecot_lmtp"
L5 = "2026-11-09 12:00:05 1xQaCD-000000000b0-BBB Completed"
GARBAGE = "garbage line without any exim timestamp"
SHORT = "2026-11-09 1"  # shorter than 19 chars
ALL_LINES = [L0, L1, L2, L3, L4, L5]


@pytest.fixture()
def paths(monkeypatch, tmp_path):
    """Point MAIL_LOG_PATH / MAIL_LOG_ROTATED_PATH at a unique tmp_path."""
    log = tmp_path / "mainlog"
    rotated = tmp_path / "mainlog.1"
    monkeypatch.setattr(mail_agent, "MAIL_LOG_PATH", str(log))
    monkeypatch.setattr(mail_agent, "MAIL_LOG_ROTATED_PATH", str(rotated))
    return log, rotated


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(mail_agent, "INSTANCE_API_KEY", KEY)
    return TestClient(mail_agent.app)


def write_log(path, lines):
    path.write_text("".join(line + "\n" for line in lines))


class TestLogsDefaults:
    def test_default_returns_all_lines_oldest_first(self, paths, client):
        log, _ = paths
        write_log(log, ALL_LINES)
        response = client.get("/logs", headers=HEADERS)
        assert response.status_code == 200
        assert response.json() == {
            "lines": ALL_LINES,
            "total_matched": 6,
            "next_offset": None,
            "source_files": ["mainlog"],
        }

    def test_offset_limit_slicing(self, paths, client):
        log, _ = paths
        write_log(log, ALL_LINES)
        body = client.get("/logs", headers=HEADERS, params={"offset": 1, "limit": 2}).json()
        assert body["lines"] == [L1, L2]
        assert body["total_matched"] == 6
        assert body["next_offset"] == 3

    def test_next_offset_none_at_exact_boundary(self, paths, client):
        log, _ = paths
        write_log(log, ALL_LINES)
        body = client.get("/logs", headers=HEADERS, params={"offset": 2, "limit": 4}).json()
        assert body["lines"] == [L2, L3, L4, L5]
        assert body["next_offset"] is None  # total_matched == offset + limit

    def test_offset_past_end_returns_empty_page_with_none(self, paths, client):
        log, _ = paths
        write_log(log, ALL_LINES)
        body = client.get("/logs", headers=HEADERS, params={"offset": 100}).json()
        assert body["lines"] == []
        assert body["total_matched"] == 6
        assert body["next_offset"] is None

    def test_negative_offset_is_422(self, paths, client):
        log, _ = paths
        write_log(log, ALL_LINES)
        assert client.get("/logs", headers=HEADERS, params={"offset": -1}).status_code == 422

    def test_limit_clamped_to_500(self, paths, client):
        log, _ = paths
        write_log(
            log,
            [
                f"2026-11-09 13:{i // 60:02d}:{i % 60:02d} 1xQaZZ-000000000b0-Z{i:03d} <= gen{i}@gen.test"
                for i in range(600)
            ],
        )
        body = client.get("/logs", headers=HEADERS, params={"limit": 1000}).json()
        assert len(body["lines"]) == 500
        assert body["lines"][0].endswith("Z000 <= gen0@gen.test")
        assert body["total_matched"] == 600
        assert body["next_offset"] == 500

    def test_limit_clamped_to_1(self, paths, client):
        log, _ = paths
        write_log(log, ALL_LINES)
        body = client.get("/logs", headers=HEADERS, params={"limit": 0}).json()
        assert body["lines"] == [L0]
        assert body["next_offset"] == 1

    def test_negative_limit_clamped_to_1_not_422(self, paths, client):
        log, _ = paths
        write_log(log, ALL_LINES)
        body = client.get("/logs", headers=HEADERS, params={"limit": -7}).json()
        assert body["lines"] == [L0]
        assert body["total_matched"] == 6


class TestLogsFilters:
    def test_q_is_case_insensitive_substring(self, paths, client):
        log, _ = paths
        write_log(log, ALL_LINES)
        for needle in ("rejected", "REJECTED", "Rejected"):
            body = client.get("/logs", headers=HEADERS, params={"q": needle}).json()
            assert body["lines"] == [L3]
            assert body["total_matched"] == 1

    def test_domain_substring_matches_user_at_domain(self, paths, client):
        log, _ = paths
        write_log(log, ALL_LINES)
        assert client.get("/logs", headers=HEADERS, params={"domain": "viswall.test"}).json()["lines"] == [L2]

    def test_domain_substring_matches_helo_case_insensitive(self, paths, client):
        log, _ = paths
        write_log(log, ALL_LINES)
        assert client.get("/logs", headers=HEADERS, params={"domain": "SPAM.EXAMPLE"}).json()["lines"] == [L3]

    def test_mail_id_substring(self, paths, client):
        log, _ = paths
        write_log(log, ALL_LINES)
        body = client.get("/logs", headers=HEADERS, params={"mail_id": "1xQaAB"}).json()
        assert body["lines"] == [L1, L2]
        assert body["total_matched"] == 2

    def test_combined_filters_apply_with_and(self, paths, client):
        log, _ = paths
        write_log(log, ALL_LINES)
        body = client.get("/logs", headers=HEADERS, params={"q": "=>", "domain": "other.test"}).json()
        assert body["lines"] == [L4]

    def test_combined_filters_and_can_match_nothing(self, paths, client):
        log, _ = paths
        write_log(log, ALL_LINES)
        body = client.get(
            "/logs", headers=HEADERS, params={"q": "Completed", "domain": "viswall.test"}
        ).json()
        assert body["lines"] == []
        assert body["total_matched"] == 0
        assert body["next_offset"] is None


class TestLogsTimeFilter:
    def test_since_is_inclusive(self, paths, client):
        log, _ = paths
        write_log(log, ALL_LINES)
        body = client.get("/logs", headers=HEADERS, params={"since": "2026-11-09 11:00:03"}).json()
        assert body["lines"] == [L3, L4, L5]  # the bound line itself is kept

    def test_until_is_inclusive(self, paths, client):
        log, _ = paths
        write_log(log, ALL_LINES)
        body = client.get("/logs", headers=HEADERS, params={"until": "2026-11-09 10:05:02"}).json()
        assert body["lines"] == [L0, L1, L2]

    def test_since_and_until_window(self, paths, client):
        log, _ = paths
        write_log(log, ALL_LINES)
        body = client.get(
            "/logs",
            headers=HEADERS,
            params={"since": "2026-11-09 10:00:00", "until": "2026-11-09 11:30:04"},
        ).json()
        assert body["lines"] == [L1, L2, L3, L4]

    def test_t_separator_normalized(self, paths, client):
        log, _ = paths
        write_log(log, ALL_LINES)
        body = client.get("/logs", headers=HEADERS, params={"since": "2026-11-09T11:30:04"}).json()
        assert body["lines"] == [L4, L5]

    def test_16_char_since_pads_seconds_00(self, paths, client):
        # L0 ends on :00 — without the ":00" padding it would compare
        # greater than the 16-char bound "2026-11-09 09:59" and drop out.
        log, _ = paths
        write_log(log, ALL_LINES)
        body = client.get("/logs", headers=HEADERS, params={"since": "2026-11-09 09:59"}).json()
        assert body["lines"] == ALL_LINES

    def test_16_char_until_pads_seconds_59(self, paths, client):
        # L2 (10:05:02) falls inside minute 10:05 only with the ":59" padding.
        log, _ = paths
        write_log(log, ALL_LINES)
        body = client.get("/logs", headers=HEADERS, params={"until": "2026-11-09T10:05"}).json()
        assert body["lines"] == [L0, L1, L2]

    def test_untimestamped_lines_excluded_only_while_time_filter_active(self, paths, client):
        log, _ = paths
        write_log(log, [GARBAGE, SHORT, *ALL_LINES])
        # No time filter → untimestamped lines pass through like any other.
        body = client.get("/logs", headers=HEADERS).json()
        assert body["lines"] == [GARBAGE, SHORT, *ALL_LINES]
        assert body["total_matched"] == 8
        # since active → excluded.
        body = client.get("/logs", headers=HEADERS, params={"since": "2026-11-09 00:00:00"}).json()
        assert body["lines"] == ALL_LINES
        # until active → excluded.
        body = client.get("/logs", headers=HEADERS, params={"until": "2026-11-30 23:59:59"}).json()
        assert body["lines"] == ALL_LINES


class TestLogsRotation:
    OLD_ROTATED = [
        "2026-11-08 08:00:00 1xQOld-000000000b0-OLD <= old@external.example H=mail.example.net [192.0.2.1] P=esmtp S=10",
        "2026-11-08 08:05:00 1xQOld-000000000b0-OLD => done <done@viswall.test> R=virtual_mailbox T=dovecot_lmtp",
    ]
    FRESH = (
        "2026-11-09 13:00:00 1xQNew-000000000b0-NEW <= new@external.example "
        "H=mail.example.net [192.0.2.2] P=esmtp S=20"
    )

    def test_rotated_lines_come_first(self, paths, client):
        log, rotated = paths
        write_log(rotated, self.OLD_ROTATED)
        write_log(log, ALL_LINES)
        body = client.get("/logs", headers=HEADERS).json()
        assert body["lines"] == self.OLD_ROTATED + ALL_LINES
        assert body["total_matched"] == 8
        assert body["source_files"] == ["mainlog.1", "mainlog"]

    def test_rotated_only_mainlog_missing(self, paths, client):
        log, rotated = paths
        write_log(rotated, self.OLD_ROTATED)  # mainlog never created
        body = client.get("/logs", headers=HEADERS).json()
        assert body["lines"] == self.OLD_ROTATED
        assert body["source_files"] == ["mainlog.1"]

    def test_rotation_between_pages_tolerated(self, paths, client):
        log, rotated = paths
        write_log(rotated, self.OLD_ROTATED)
        write_log(log, ALL_LINES)
        first = client.get("/logs", headers=HEADERS, params={"offset": 0, "limit": 2}).json()
        assert first["lines"] == self.OLD_ROTATED
        assert first["total_matched"] == 8
        assert first["next_offset"] == 2

        # logrotate renames mainlog→mainlog.1 (overwriting it) and a fresh
        # mainlog starts: the rotated prefix the client already paginated
        # past is gone and offsets drift. The endpoint must stay stateless
        # and answer with a valid page — never a 500.
        os.replace(log, rotated)
        write_log(log, [self.FRESH])

        second = client.get("/logs", headers=HEADERS, params={"offset": 2, "limit": 2})
        assert second.status_code == 200
        body = second.json()
        assert set(body) == {"lines", "total_matched", "next_offset", "source_files"}
        assert body["source_files"] == ["mainlog.1", "mainlog"]
        assert body["total_matched"] == 7
        stamps = [line[:19] for line in body["lines"]]
        assert stamps == sorted(stamps)  # ordering preserved despite the shift


class TestLogsMissingFiles:
    def test_no_log_files_at_all_returns_empty_200(self, paths, client):
        response = client.get("/logs", headers=HEADERS)
        assert response.status_code == 200
        assert response.json() == {
            "lines": [],
            "total_matched": 0,
            "next_offset": None,
            "source_files": [],
        }

    def test_empty_log_file_is_a_readable_source(self, paths, client):
        log, _ = paths
        log.write_text("")
        response = client.get("/logs", headers=HEADERS)
        assert response.status_code == 200
        assert response.json() == {
            "lines": [],
            "total_matched": 0,
            "next_offset": None,
            "source_files": ["mainlog"],
        }


class TestLogsAuth:
    def test_missing_key_header_is_401(self, paths, client):
        log, _ = paths
        write_log(log, ALL_LINES)
        assert client.get("/logs").status_code == 401

    def test_wrong_key_is_401(self, paths, client):
        log, _ = paths
        write_log(log, ALL_LINES)
        assert client.get("/logs", headers={"X-Instance-Key": "wrong"}).status_code == 401

    def test_unset_key_is_503(self, paths, monkeypatch):
        log, _ = paths
        write_log(log, ALL_LINES)
        monkeypatch.setattr(mail_agent, "INSTANCE_API_KEY", None)
        client = TestClient(mail_agent.app)
        assert client.get("/logs", headers=HEADERS).status_code == 503
