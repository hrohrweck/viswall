"""QoS contract tests (todo 11): stats mapping + HTB classes delivery.

``setup_qos`` must (1) validate the gateway class list BEFORE the first tc
command, (2) build the HTB leaf hierarchy from the classes when
``algorithm="htb"``, and (3) keep the legacy 30/40/30 hierarchy when classes
are empty. ``get_stats`` must answer the gateway contract shape
``{"queues": [{name, bytes, packets, dropped, rate}], "raw": <tc -s text>}``.
"""

from __future__ import annotations

import asyncio

import pytest

from viswall_firewall_agent.qos import (
    QoSValidationError,
    TrafficControlManager,
    _parse_qdisc_stats,
)

TC_STATS_FIXTURE = (
    "qdisc cake 1: root refcnt 2 bandwidth 100Mbit diffserv4 dual-srchost nat wash\n"
    " Sent 1583412 bytes 12007 pkt (dropped 3, overlimits 0 requeues 0)\n"
    " backlog 0b 0p requeues 0\n"
    "qdisc fq_codel 8002: parent 1:10 limit 10240p flows 1024 quantum 1514\n"
    " Sent 981234 bytes 8100 pkt (dropped 1, overlimits 0 requeues 0)\n"
    " backlog 0b 0p requeues 0\n"
)


def _classes() -> list[dict]:
    return [
        {
            "name": "voip",
            "min_rate_kbps": 30000,
            "max_rate_kbps": 100000,
            "match_ports": [22, 53],
            "match_protocol": "any",
            "priority": 1,
        },
        {
            "name": "normal",
            "min_rate_kbps": 40000,
            "match_ports": [],
            "match_protocol": "any",
            "priority": 2,
        },
        {
            "name": "bulk",
            "min_rate_kbps": 30000,
            "max_rate_kbps": 100000,
            "match_ports": [],
            "match_protocol": "any",
            "priority": 3,
        },
    ]


def _u32(port: str, proto_num: str, proto_name: str, classid: str) -> list[str]:
    return [
        "tc", "filter", "add", "dev", "eth0", "protocol", "ip", "parent", "1:0",
        "prio", "1", "u32", "match", "ip", "protocol", proto_num, "0xff",
        "match", proto_name, "dport", port, "0xffff", "flowid", classid,
    ]


def _flower(port: str, proto_name: str, classid: str) -> list[str]:
    return [
        "tc", "filter", "add", "dev", "eth0", "protocol", "ipv6", "parent", "1:0",
        "prio", "1", "flower", "ip_proto", proto_name, "dst_port", port,
        "flowid", classid,
    ]


def _htb_expected() -> list[list[str]]:
    expected: list[list[str]] = [
        ["tc", "qdisc", "del", "dev", "eth0", "root"],
        ["tc", "qdisc", "add", "dev", "eth0", "root", "handle", "1:", "htb", "default", "12"],
        ["tc", "class", "add", "dev", "eth0", "parent", "1:", "classid", "1:1", "htb",
         "rate", "100000kbit", "burst", "15k"],
        ["tc", "class", "add", "dev", "eth0", "parent", "1:1", "classid", "1:10", "htb",
         "rate", "30000kbit", "ceil", "100000kbit", "prio", "1"],
        ["tc", "qdisc", "add", "dev", "eth0", "parent", "1:10", "fq_codel"],
    ]
    for port in ("22", "53"):
        for proto_name, proto_num in (("tcp", "6"), ("udp", "17")):
            expected.append(_u32(port, proto_num, proto_name, "1:10"))
            expected.append(_flower(port, proto_name, "1:10"))
    expected += [
        ["tc", "class", "add", "dev", "eth0", "parent", "1:1", "classid", "1:11", "htb",
         "rate", "40000kbit", "ceil", "100000kbit", "prio", "2"],
        ["tc", "qdisc", "add", "dev", "eth0", "parent", "1:11", "fq_codel"],
        ["tc", "class", "add", "dev", "eth0", "parent", "1:1", "classid", "1:12", "htb",
         "rate", "30000kbit", "ceil", "100000kbit", "prio", "3"],
        ["tc", "qdisc", "add", "dev", "eth0", "parent", "1:12", "fq_codel"],
    ]
    return expected


class TestStatsMapping:
    def test_parse_qdisc_stats_maps_contract_shape(self) -> None:
        queues = _parse_qdisc_stats(TC_STATS_FIXTURE)
        assert queues == [
            {"name": "1:", "bytes": 1583412, "packets": 12007, "dropped": 3, "rate": "100Mbit"},
            {"name": "8002:", "bytes": 981234, "packets": 8100, "dropped": 1, "rate": ""},
        ]

    def test_parse_qdisc_stats_empty_output(self) -> None:
        assert _parse_qdisc_stats("") == []

    def test_get_stats_returns_raw_and_queues(self, subprocess_fake) -> None:
        manager = TrafficControlManager()
        subprocess_fake.on(lambda c: c[0] == "tc", rc=0, out=TC_STATS_FIXTURE.encode())

        stats = asyncio.run(manager.get_stats("eth0"))

        assert stats["raw"] == TC_STATS_FIXTURE
        assert stats["queues"][0]["rate"] == "100Mbit"
        assert [q["name"] for q in stats["queues"]] == ["1:", "8002:"]
        assert subprocess_fake.calls("tc") == [["tc", "-s", "qdisc", "show", "dev", "eth0"]]


class TestClassesDelivery:
    def test_setup_qos_htb_delivers_classes(self, subprocess_fake) -> None:
        manager = TrafficControlManager()
        subprocess_fake.on(lambda c: c[0] == "tc", rc=0)

        ok = asyncio.run(
            manager.setup_qos(
                interface="eth0",
                download_rate=100000,
                upload_rate=50000,
                algorithm="htb",
                classes=_classes(),
            )
        )

        assert ok is True
        assert subprocess_fake.calls("tc") == _htb_expected()

    def test_setup_qos_legacy_defaults_without_classes(self, subprocess_fake) -> None:
        manager = TrafficControlManager()
        subprocess_fake.on(lambda c: c[0] == "tc", rc=0)

        ok = asyncio.run(
            manager.setup_qos(
                interface="eth0",
                download_rate=100000,
                upload_rate=50000,
                algorithm="htb",
                classes=[],
            )
        )

        assert ok is True
        commands = subprocess_fake.calls("tc")
        assert ["tc", "class", "add", "dev", "eth0", "parent", "1:1", "classid", "1:10",
                "htb", "rate", "30000kbit", "ceil", "100000kbit", "prio", "100"] in commands
        assert ["tc", "class", "add", "dev", "eth0", "parent", "1:1", "classid", "1:11",
                "htb", "rate", "40000kbit", "ceil", "100000kbit", "prio", "200"] in commands
        assert _u32("22", "6", "tcp", "1:10") in commands
        assert _flower("5060", "udp", "1:10") in commands

    def test_setup_qos_cake_ignores_classes(self, subprocess_fake) -> None:
        manager = TrafficControlManager()
        subprocess_fake.on(lambda c: c[0] == "tc", rc=0)

        ok = asyncio.run(
            manager.setup_qos(
                interface="eth0",
                download_rate=100000,
                upload_rate=50000,
                algorithm="cake",
                classes=_classes(),
            )
        )

        assert ok is True
        commands = subprocess_fake.calls("tc")
        assert any("cake" in c for c in commands)
        assert not any("class" in c and "classid" in c for c in commands)

    def test_setup_qos_returns_false_when_tc_unavailable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import asyncio as aio

        async def _missing_binary(*args, **kwargs) -> None:
            raise OSError("tc: command not found")

        monkeypatch.setattr(aio, "create_subprocess_exec", _missing_binary)
        manager = TrafficControlManager()

        ok = asyncio.run(
            manager.setup_qos(interface="eth0", download_rate=1000, upload_rate=1000)
        )

        assert ok is False


class TestValidateBeforeTouch:
    """Malformed class payloads raise BEFORE the first tc command."""

    @pytest.mark.parametrize(
        "classes,message",
        [
            ({"not": "a list"}, "classes must be a list"),
            ([{"name": "no-min"}], "min_rate_kbps is required"),
            ([{"min_rate_kbps": 0}], "min_rate_kbps must be >= 1"),
            ([{"min_rate_kbps": 1000, "match_ports": ["80"]}], "match_ports entry must be a number"),
            ([{"min_rate_kbps": 1000, "match_ports": [0]}], "match_ports entry must be >= 1"),
            ([{"min_rate_kbps": 1000, "match_ports": [70000]}], "exceeds 65535"),
            ([{"min_rate_kbps": 1000, "match_protocol": "sctp"}], "unsupported match_protocol"),
            ([{"min_rate_kbps": 1000, "match_protocol": 7}], "match_protocol must be a string"),
            ([{"min_rate_kbps": 1000, "priority": 8}], "priority must be between 0 and 7"),
        ],
    )
    def test_invalid_classes_raise_before_any_tc_call(
        self, classes, message: str
    ) -> None:
        # The conftest guard is active: any tc spawn would raise AssertionError
        # and fail this test — proving validate-before-touch.
        manager = TrafficControlManager()
        with pytest.raises(QoSValidationError, match=message):
            asyncio.run(
                manager.setup_qos(
                    interface="eth0",
                    download_rate=1000,
                    upload_rate=1000,
                    algorithm="htb",
                    classes=classes,
                )
            )


class TestReturncodeChecks:
    """F2 MINOR #10: a failed qdisc/class/filter ADD must yield False, not a
    silent success on a half-installed tree."""

    def test_setup_qos_returns_false_when_qdisc_add_fails(self, subprocess_fake) -> None:
        manager = TrafficControlManager()
        subprocess_fake.on(
            lambda c: c[0] == "tc" and c[1] == "qdisc" and c[2] == "del", rc=0
        )
        subprocess_fake.on(
            lambda c: c[0] == "tc" and c[1] == "qdisc" and c[2] == "add",
            rc=2,
            err=b"RTNETLINK answers: Operation not permitted",
        )

        ok = asyncio.run(
            manager.setup_qos(interface="eth0", download_rate=1000, upload_rate=1000)
        )

        assert ok is False

    def test_setup_qos_returns_false_when_class_add_fails(self, subprocess_fake) -> None:
        manager = TrafficControlManager()
        subprocess_fake.on(
            lambda c: c[0] == "tc" and c[2] == "del", rc=0
        )
        subprocess_fake.on(
            lambda c: c[0] == "tc" and c[1] == "class",
            rc=1,
            err=b"RTNETLINK answers: File exists",
        )
        subprocess_fake.on(
            lambda c: c[0] == "tc" and c[1] == "qdisc" and c[2] == "add", rc=0
        )

        ok = asyncio.run(
            manager.setup_qos(
                interface="eth0",
                download_rate=100000,
                upload_rate=50000,
                algorithm="htb",
                classes=[],
            )
        )

        assert ok is False

    def test_setup_qos_still_succeeds_when_all_adds_ok(self, subprocess_fake) -> None:
        manager = TrafficControlManager()
        subprocess_fake.on(lambda c: c[0] == "tc", rc=0)

        ok = asyncio.run(
            manager.setup_qos(interface="eth0", download_rate=1000, upload_rate=1000)
        )

        assert ok is True
