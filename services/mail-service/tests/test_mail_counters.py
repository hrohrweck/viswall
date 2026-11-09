"""Tests for the rotation-safe Exim mainlog counter behind GET /stats."""
import json
import os

import pytest
from fastapi.testclient import TestClient

import mail_agent

ARRIVAL = (
    "2026-11-09 10:12:14 1xQMMH-000000000b0-2ZLX <= prvs=766ed0671=maria.kern@pearl.de "
    "H=mail-wr1-f70.google.com [209.85.222.70] P=esmtps S=1024 id=<x@y>\n"
)
DELIVERY = (
    "2026-11-09 10:12:15 1xQMMH-000000000b0-2ZLX => fabius <pearl@webmasters.co.at> "
    'R=virtual_mailbox T=dovecot_lmtp C="250 2.0.0 ok"\n'
)
SPAM_REJECT = (
    "2026-11-09 10:12:16 rejected H=(spam.example) [192.0.2.1] F=<spam@spam.example> "
    "after DATA: spam score 14.2 above threshold\n"
)
VIRUS_REJECT = (
    "2026-11-09 10:12:17 rejected H=(virus.example) [192.0.2.2] F=<v@virus.example> "
    "after DATA: malware found by clamd\n"
)
UNCLASSIFIED = (
    "2026-11-09 10:12:18 1xQMMH-000000000b0-2ZLX Completed\n"
    "2026-11-09 10:12:19 1xQMO1-000000000b0-1AAA == user@remote.defer "
    "T=remote_lsmtp defer (-1): timeout\n"
)
ZERO = {"received": 0, "delivered": 0, "rejected_spam": 0, "rejected_virus": 0}


@pytest.fixture()
def paths(monkeypatch, tmp_path):
    """Point the log, rotated log, and state file (in a fresh subdir) at tmp_path."""
    log = tmp_path / "mainlog"
    rotated = tmp_path / "mainlog.1"
    state = tmp_path / "state" / "mail-stats.json"
    monkeypatch.setattr(mail_agent, "MAIL_LOG_PATH", str(log))
    monkeypatch.setattr(mail_agent, "MAIL_LOG_ROTATED_PATH", str(rotated))
    monkeypatch.setattr(mail_agent, "MAIL_STATS_STATE_PATH", str(state))
    return log, rotated, state


class TestMailCounters:
    def test_counts_fixture_log_and_second_call_is_idempotent(self, paths):
        log, _, state = paths
        log.write_text(ARRIVAL * 5 + DELIVERY * 3 + SPAM_REJECT * 2 + VIRUS_REJECT + UNCLASSIFIED)

        first = mail_agent._mail_counters()
        assert first == {"received": 5, "delivered": 3, "rejected_spam": 2, "rejected_virus": 1}

        second = mail_agent._mail_counters()  # no new lines → counters unchanged
        assert second == first

        saved = json.loads(state.read_text())
        assert saved["inode"] == log.stat().st_ino
        assert saved["offset"] == log.stat().st_size
        assert saved["counters"] == first

    def test_rotation_drains_rotated_remainder_then_reads_new_file(self, paths):
        log, rotated, state = paths
        log.write_text(ARRIVAL * 2 + DELIVERY)
        assert mail_agent._mail_counters() == {**ZERO, "received": 2, "delivered": 1}

        with open(log, "a") as fh:  # unread remainder before rotation
            fh.write(SPAM_REJECT)
        os.replace(log, rotated)  # logrotate-style rename
        log.write_text(VIRUS_REJECT + ARRIVAL)

        result = mail_agent._mail_counters()
        # 2 arrivals + 1 delivery (pre-rotation, counted) + spam reject
        # (rotated remainder) + virus reject + arrival (new file) — and the
        # drain must not double-count the already-read rotated prefix.
        assert result == {"received": 3, "delivered": 1, "rejected_spam": 1, "rejected_virus": 1}
        saved = json.loads(state.read_text())
        assert saved["inode"] == log.stat().st_ino
        assert saved["offset"] == log.stat().st_size
        assert saved["counters"] == result

    def test_rotation_without_rotated_file_advances_state(self, paths):
        # Fresh anonymous /var/log/exim4 volume after a container recreate:
        # the persisted state still holds the old inode and mainlog.1 is gone.
        log, rotated, state = paths
        log.write_text(ARRIVAL * 3)
        assert mail_agent._mail_counters() == {**ZERO, "received": 3}
        stale_inode = json.loads(state.read_text())["inode"]

        fresh = log.with_name("fresh-mainlog")  # created while the old log exists
        fresh.write_text(ARRIVAL + DELIVERY)
        os.replace(fresh, log)  # new inode at the same path, no mainlog.1
        assert not rotated.exists()

        result = mail_agent._mail_counters()
        assert result == {**ZERO, "received": 4, "delivered": 1}

        saved = json.loads(state.read_text())  # state must ADVANCE, never stick
        assert saved["inode"] == log.stat().st_ino
        assert saved["inode"] != stale_inode
        assert saved["offset"] == log.stat().st_size
        assert saved["counters"] == result

    def test_missing_log_returns_none_without_writing_state(self, paths):
        log, _, state = paths  # log never created
        assert mail_agent._mail_counters() is None
        assert not state.exists()

    def test_empty_and_garbage_log_classify_nothing(self, paths):
        log, _, _ = paths
        log.write_text("")
        assert mail_agent._mail_counters() == dict(ZERO)

        log.write_text(
            "\x00\xff\xfe not an exim line\n"
            "something=>x without spaces\n"
            "  <=no trailing space\n"
        )
        assert mail_agent._mail_counters() == dict(ZERO)


class TestStatsEndpoint:
    def test_stats_returns_queue_length_and_mail_counters(self, monkeypatch):
        counters = {"received": 7, "delivered": 5, "rejected_spam": 1, "rejected_virus": 0}
        monkeypatch.setattr(mail_agent, "_mail_counters", lambda: counters)
        monkeypatch.setattr(mail_agent, "_queue_length", lambda: 4)

        client = TestClient(mail_agent.app)
        response = client.get("/stats")

        assert response.status_code == 200
        assert response.json() == {"queue_length": 4, "mail": counters}

    def test_stats_reports_mail_null_when_counters_unavailable(self, monkeypatch):
        monkeypatch.setattr(mail_agent, "_mail_counters", lambda: None)
        monkeypatch.setattr(mail_agent, "_queue_length", lambda: 0)

        client = TestClient(mail_agent.app)
        response = client.get("/stats")

        assert response.status_code == 200
        assert response.json() == {"queue_length": 0, "mail": None}
