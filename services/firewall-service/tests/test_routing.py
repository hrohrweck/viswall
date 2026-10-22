"""Idempotent tagged policy routing (todo 13).

A stateful fake ``ip`` runner (no subprocess at all — the runner seam the
landed ``RoutingManager`` provides) emulates the kernel: it answers the
``-j`` queries from its own state and applies the ``add``/``del`` mutations.
The todo-13 contract: applying the same payload twice produces ZERO mutations
on the second run; every created object carries the viswall ownership tags
(``protocol 30`` + ``vw-table-<n>``); removing an entry from the payload
deletes exactly that entry; foreign (non-viswall) entries are never touched.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

from viswall_firewall_agent.routing import RoutingManager


class FakeIpState:
    """Minimal kernel emulation: ``ip -j`` queries + rule/route mutations."""

    def __init__(self) -> None:
        self.rules: list[dict] = []
        self.routes: list[dict] = []
        self.commands: list[list[str]] = []

    async def __call__(self, command: list[str]) -> tuple[int, str, str]:
        self.commands.append(list(command))
        if command[:2] == ["ip", "-j"]:
            if command[2] == "rule":
                return 0, json.dumps(self.rules), ""
            if command[2] == "route":
                return 0, json.dumps(self.routes), ""
        if len(command) >= 3 and command[1] in ("rule", "route"):
            self._mutate(command)
            return 0, "", ""
        raise AssertionError(f"unexpected ip invocation: {command}")

    def _mutate(self, command: list[str]) -> None:
        kind, action = command[1], command[2]
        tokens = command[3:]
        if kind == "rule":
            entry = self._parse_rule(tokens)
            if action == "add":
                self.rules.append(entry)
            else:
                self.rules.remove(entry)
        else:
            entry = self._parse_route(tokens)
            if action == "add":
                self.routes.append(entry)
            else:
                self.routes.remove(entry)

    @staticmethod
    def _parse_rule(tokens: list[str]) -> dict:
        entry: dict[str, Any] = {"priority": 0, "src": "all", "protocol": "30"}
        index = 0
        while index < len(tokens):
            token = tokens[index]
            if token in ("from", "to", "fwmark", "iif", "table", "prio", "protocol"):
                value: Any = tokens[index + 1]
                if token == "from":
                    entry["src"] = value
                elif token == "to":
                    entry["dst"] = value
                elif token == "fwmark":
                    entry["fwmark"] = int(value)
                elif token == "iif":
                    entry["iif"] = value
                elif token == "table":
                    entry["table"] = value
                elif token == "prio":
                    entry["priority"] = int(value)
                else:
                    entry["protocol"] = value
                index += 2
            else:
                index += 1
        return entry

    @staticmethod
    def _parse_route(tokens: list[str]) -> dict:
        entry: dict[str, Any] = {"protocol": "30", "dst": tokens[0]}
        index = 1
        while index < len(tokens):
            token = tokens[index]
            if token == "via":
                entry["gateway"] = tokens[index + 1]
            elif token == "dev":
                entry["dev"] = tokens[index + 1]
            elif token == "src":
                entry["prefsrc"] = tokens[index + 1]
            elif token == "metric":
                entry["metric"] = int(tokens[index + 1])
            elif token == "table":
                entry["table"] = tokens[index + 1]
            elif token == "proto":
                entry["protocol"] = tokens[index + 1]
            index += 2
        return entry


PAYLOAD = [
    {
        "id": 1,
        "name": "policy-vpn",
        "source": "10.80.0.0/16",
        "table": 200,
        "gateway": "10.80.0.1",
        "priority": 100,
    },
    {
        "id": 2,
        "name": "mark-route",
        "mark": 7,
        "table": 201,
        "priority": 101,
    },
]

FIRST_APPLY_MUTATIONS = [
    ["ip", "rule", "add", "from", "10.80.0.0/16", "table", "vw-table-200",
     "prio", "100", "protocol", "30"],
    ["ip", "rule", "add", "fwmark", "7", "table", "vw-table-201",
     "prio", "101", "protocol", "30"],
    ["ip", "route", "add", "default", "via", "10.80.0.1", "src", "10.80.0.0/16",
     "table", "vw-table-200", "proto", "30"],
]


@pytest.fixture
def manager(tmp_path: Path):
    state = FakeIpState()
    rt_tables = tmp_path / "rt_tables"
    rt_tables.write_text(
        "#\n# reserved\n#\n255\tlocal\n254\tmain\n253\tdefault\n0\tunspec\n"
    )
    routing = RoutingManager(rt_tables_path=str(rt_tables), runner=state)
    return routing, state, rt_tables


class TestIdempotence:
    def test_first_apply_adds_only_deltas(self, manager) -> None:
        routing, state, _rt_tables = manager

        assert asyncio.run(routing.apply_routing(PAYLOAD)) is True

        assert routing.errors == []
        assert routing.mutations == FIRST_APPLY_MUTATIONS
        assert len(state.rules) == 2
        assert len(state.routes) == 1

    def test_second_apply_zero_mutations(self, manager) -> None:
        routing, _state, _rt_tables = manager
        assert asyncio.run(routing.apply_routing(PAYLOAD)) is True

        # routing.mutations / file_mutations are append-only audit trails:
        # clear them so the second run is measured on its own.
        routing.mutations.clear()
        routing.file_mutations.clear()
        assert asyncio.run(routing.apply_routing(PAYLOAD)) is True

        assert routing.mutations == []
        assert routing.file_mutations == []
        assert routing.errors == []

    def test_removed_rule_is_deleted(self, manager) -> None:
        routing, state, _rt_tables = manager
        assert asyncio.run(routing.apply_routing(PAYLOAD)) is True

        routing.mutations.clear()
        assert asyncio.run(routing.apply_routing([PAYLOAD[0]])) is True

        deletions = [m for m in routing.mutations if m[2] == "del"]
        assert len(deletions) == 1
        assert deletions[0][0] == "ip" and deletions[0][1] == "rule"
        assert "fwmark" in deletions[0] and "7" in deletions[0]
        assert any(r.get("fwmark") == 7 for r in state.rules) is False

    def test_foreign_entries_never_deleted(self, manager) -> None:
        routing, state, _rt_tables = manager
        state.rules.append(
            {"priority": 32000, "src": "all", "table": "main", "protocol": "boot"}
        )
        state.routes.append(
            {"dst": "default", "gateway": "46.4.63.193", "dev": "enp0s31f6",
             "table": "main", "protocol": "boot"}
        )

        assert asyncio.run(routing.apply_routing(PAYLOAD)) is True

        deletions = [m for m in routing.mutations if m[2] == "del"]
        assert deletions == []
        assert any(r.get("gateway") == "46.4.63.193" for r in state.routes)
        assert len(state.routes) == 2  # foreign default + our tagged route


class TestOwnershipTags:
    def test_every_mutation_carries_tags(self, manager) -> None:
        routing, _state, _rt_tables = manager
        assert asyncio.run(routing.apply_routing(PAYLOAD)) is True

        for mutation in routing.mutations:
            pairs = list(zip(mutation, mutation[1:]))
            assert ("protocol", "30") in pairs or ("proto", "30") in pairs
            assert any(str(token).startswith("vw-table-") for token in mutation)


class TestTableRegistry:
    def test_rt_tables_registered_exactly_once(self, manager) -> None:
        routing, _state, rt_tables = manager
        assert asyncio.run(routing.apply_routing(PAYLOAD)) is True
        content = rt_tables.read_text()
        assert "200 vw-table-200" in content
        assert "201 vw-table-201" in content
        assert content.count("vw-table-200") == 1
        assert content.count("vw-table-201") == 1

    def test_reserved_tables_never_registered(self, tmp_path: Path) -> None:
        state = FakeIpState()
        rt_tables = tmp_path / "rt_tables"
        rt_tables.write_text("255\tlocal\n254\tmain\n")
        routing = RoutingManager(rt_tables_path=str(rt_tables), runner=state)

        assert asyncio.run(
            routing.apply_routing([{"id": 3, "name": "main-rule", "table": 254}])
        ) is True
        assert routing.file_mutations == []
        assert routing.mutations == []
