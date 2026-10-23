"""Renderer regression suite (todo 7 acceptance, todo 14 gate).

Covers the docker-safe renderer: no ``flush ruleset``, ``table inet viswall``
only, SSH(22)/WG(51820)/established always present (lockout regression),
dport-guarded meters, DOCKER-USER internal-port set, docker bridge coexistence,
loopback guards + anti-spoof placement, ``meta nfproto ipv6`` scoping, the
SSH/WG-before-user-rules ordering invariant, and the VALIDATION_MODE
pass-through mutation check (flip the flag, flip the output).
"""

from __future__ import annotations

import re

import pytest

from viswall_firewall_agent.nft import (
    DEFAULT_INTERNAL_PORTS,
    FirewallAction,
    FirewallRule,
    NATRule,
    NFTablesManager,
)


def _rule(rule_id: int, name: str, chain: str = "input", **kwargs) -> FirewallRule:
    return FirewallRule(id=rule_id, name=name, chain=chain, **kwargs)


def _interfaces() -> list[dict]:
    return [{"name": "enp0s31f6", "type": "wan"}]


def _base_rules() -> list[FirewallRule]:
    """Fixture exercising every tagged rule class the renderer special-cases."""
    return [
        _rule(1, "ssh limit", protocol="tcp", destination_port=22, limit="8/minute"),
        _rule(2, "https limit", protocol="tcp", destination_port=443, limit="120/minute"),
        _rule(
            3,
            "loopback guard 8000",
            action=FirewallAction.DROP,
            destination="127.0.0.1",
            protocol="tcp",
            destination_port=8000,
        ),
        _rule(
            4,
            "loopback guard 8001",
            action=FirewallAction.DROP,
            destination="127.0.0.1",
            protocol="tcp",
            destination_port=8001,
        ),
        _rule(
            5,
            "loopback guard 8080",
            action=FirewallAction.DROP,
            destination="127.0.0.1",
            protocol="tcp",
            destination_port=8080,
        ),
        _rule(
            6,
            "anti-spoof container web",
            chain="forward",
            anti_spoof=True,
            interface_in="br-abc123",
            destination="172.19.0.5",
        ),
        _rule(
            7,
            "internal-port 11434",
            chain="forward",
            protocol="tcp",
            destination_port=11434,
        ),
        _rule(
            8,
            "user rule input",
            protocol="tcp",
            destination_port=21115,
            action=FirewallAction.ACCEPT,
            comment="user rule input",
            order=50,
        ),
        _rule(
            9,
            "user rule limited",
            protocol="tcp",
            destination_port=9090,
            limit="30/minute",
            action=FirewallAction.ACCEPT,
            comment="limit-carrying user rule",
            order=60,
        ),
    ]


def _nat_rules() -> list[NATRule]:
    return [
        NATRule(
            id=1,
            name="mail dnat",
            type="dnat",
            chain="prerouting",
            destination="46.4.63.216",
            protocol="tcp",
            port=25,
            to_destination="172.20.0.10:25",
            comment="mail dnat",
        ),
        NATRule(
            id=2,
            name="vpn snat",
            type="snat",
            chain="postrouting",
            source="10.80.0.0/16",
            to_source="46.4.63.216",
        ),
        NATRule(id=3, name="wan masquerade", type="masquerade", chain="postrouting"),
    ]


def _render(
    manager: NFTablesManager,
    *,
    rules: list[FirewallRule] | None = None,
    nat: list[NATRule] | None = None,
    interfaces: list[dict] | None = None,
    **kwargs,
) -> str:
    return manager.generate_ruleset(
        interfaces=interfaces if interfaces is not None else _interfaces(),
        firewall_rules=rules if rules is not None else _base_rules(),
        nat_rules=nat or [],
        **kwargs,
    )


def _chain_section(ruleset: str, chain: str) -> str:
    """Slice the lines of one chain block out of the ruleset."""
    lines = ruleset.splitlines()
    start = lines.index(f"    chain {chain} {{")
    depth = 0
    for index in range(start, len(lines)):
        if "{" in lines[index]:
            depth += lines[index].count("{")
        if "}" in lines[index]:
            depth -= lines[index].count("}")
        if depth == 0:
            return "\n".join(lines[start : index + 1])
    raise AssertionError(f"chain {chain} not closed")


class TestLockoutRegression:
    """An applied ruleset must never lock out SSH/WG — in EVERY render."""

    @pytest.mark.parametrize(
        "rules,nat,kwargs",
        [
            (None, None, {}),
            ([], None, {}),
            (None, None, {"enable_logging": False}),
            (None, None, {"enable_conntrack": False}),
            ([], None, {"enable_logging": False, "enable_conntrack": False}),
        ],
    )
    def test_no_flush_and_viswall_table_only(
        self, rules, nat, kwargs, monkeypatch
    ) -> None:
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        ruleset = _render(NFTablesManager(), rules=rules, nat=nat, **kwargs)
        assert "flush ruleset" not in ruleset
        assert "table inet viswall" in ruleset

    @pytest.mark.parametrize(
        "rules,nat,kwargs",
        [
            (None, None, {}),
            ([], None, {}),
            (None, None, {"enable_logging": False}),
        ],
    )
    def test_ssh_and_wg_always_present(self, rules, nat, kwargs, monkeypatch) -> None:
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        ruleset = _render(NFTablesManager(), rules=rules, nat=nat, **kwargs)
        input_chain = _chain_section(ruleset, "input")

        # ssh meter: dport-guarded (Oracle #11), family-scoped, ``over`` so it
        # drops only the over-limit traffic, with exactly ONE burst clause.
        # The rate differs per fixture (DB-origin limit overrides the default).
        assert re.search(
            r"meta nfproto ipv4 tcp dport 22 meter ssh_limit \{ ip saddr "
            r"limit rate over \S+ burst 5 packets \} drop",
            input_chain,
        )
        # v6 ssh meter: family-scoped v6 bucket never bypassed (todo 39 E02).
        assert re.search(
            r"meta nfproto ipv6 tcp dport 22 meter ssh_limit_v6 \{ ip6 saddr "
            r"limit rate over \S+ burst 5 packets \} drop",
            input_chain,
        )
        # ssh accept: 22 is inside both family-scoped accept sets.
        assert "meta nfproto ipv4 tcp dport {22, " in input_chain
        assert "meta nfproto ipv6 tcp dport {22, 80, 443} accept" in input_chain
        # wg 51820: family-scoped meter + family-scoped accepts.
        assert "meta nfproto ipv4 udp dport 51820 meter wireguard_limit" in input_chain
        assert "meta nfproto ipv6 udp dport 51820 meter wireguard_limit_v6" in input_chain
        assert "51820" in input_chain.split("meta nfproto ipv4 udp dport")[1]
        assert "meta nfproto ipv6 udp dport {51820} accept" in input_chain
        # established/related must always come first.
        assert "ct state established,related accept" in input_chain

    def test_db_limit_wins_over_default_for_ssh(self, monkeypatch) -> None:
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        ruleset = _render(NFTablesManager())
        assert (
            "meta nfproto ipv4 tcp dport 22 meter ssh_limit "
            "{ ip saddr limit rate over 8/minute burst 5 packets } drop"
            in ruleset
        )

    def test_db_limit_with_burst_emitted_verbatim_once(self, monkeypatch) -> None:
        """Todo 38 finding #1: a DB limit that already carries burst must NOT
        get a second burst clause appended (double-burst fails nft -c)."""
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        rules = [
            r
            if r.id != 1
            else _rule(1, "ssh limit", protocol="tcp", destination_port=22,
                       limit="10/minute burst 5 packets")
            for r in _base_rules()
        ]
        ruleset = _render(NFTablesManager(), rules=rules)
        assert (
            "meta nfproto ipv4 tcp dport 22 meter ssh_limit "
            "{ ip saddr limit rate over 10/minute burst 5 packets } drop"
            in ruleset
        )
        assert "burst 5 packets burst 5 packets" not in ruleset

    def test_v6_meter_rate_from_v6_suffixed_row(self, monkeypatch) -> None:
        """The _v6-named row feeds the v6 bucket; a plain row feeds v4."""
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        rules = _base_rules() + [
            _rule(
                21,
                "ssh_limit_v6",
                protocol="tcp",
                destination_port=22,
                limit="7/minute",
            )
        ]
        ruleset = _render(NFTablesManager(), rules=rules)
        assert (
            "meta nfproto ipv4 tcp dport 22 meter ssh_limit "
            "{ ip saddr limit rate over 8/minute burst 5 packets } drop"
            in ruleset
        )
        assert (
            "meta nfproto ipv6 tcp dport 22 meter ssh_limit_v6 "
            "{ ip6 saddr limit rate over 7/minute burst 5 packets } drop"
            in ruleset
        )

    def test_every_meter_carries_dport_guard(self, monkeypatch) -> None:
        """Oracle #11: a meter without its dport guard rate-limits ALL traffic."""
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        ruleset = _render(NFTablesManager())
        meter_lines = [
            line.strip() for line in ruleset.splitlines() if " meter " in line
        ]
        assert len(meter_lines) == 8  # 4 ports x (ipv4 + ipv6)
        for line in meter_lines:
            assert re.match(
                r"^meta nfproto ipv[46] (tcp|udp) dport \d+ meter \w+ \{ ip6? saddr",
                line,
            ), line
        assert sum("ipv4" in line for line in meter_lines) == 4
        assert sum("ipv6" in line for line in meter_lines) == 4


class TestDockerCoexistence:
    def test_bridge_input_and_forward_accepts(self, monkeypatch) -> None:
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        ruleset = _render(NFTablesManager())
        input_chain = _chain_section(ruleset, "input")
        forward_chain = _chain_section(ruleset, "forward")
        # todo 38/39: live INPUT accepts docker0 ONLY — no br-* INPUT accept.
        assert 'iifname "docker0" accept' in input_chain
        assert 'iifname "br-*" accept' not in input_chain
        for expected in (
            'iifname "docker0" accept',
            'oifname "docker0" accept',
            'iifname "br-*" accept',
            'oifname "br-*" accept',
        ):
            assert expected in forward_chain

    def test_docker_user_replacement_precedes_bridge_accepts(self, monkeypatch) -> None:
        """Todo 38 finding #2: the DOCKER-USER replacement must fire BEFORE
        the bridge accepts, or WAN->published internal ports slip through."""
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        ruleset = _render(NFTablesManager())
        forward_chain = _chain_section(ruleset, "forward")
        established = forward_chain.index("ct state established,related accept")
        docker_user = forward_chain.index(
            'iifname "enp0s31f6" meta l4proto tcp ct direction original'
        )
        bridge_accept = forward_chain.index('iifname "docker0" accept')
        assert established < docker_user < bridge_accept

    def test_docker_user_replacement_is_tcp_scoped(self, monkeypatch) -> None:
        """Todo 39 D18: live DOCKER-USER carries -p tcp; the replacement must
        not drop non-tcp flows whose original dst port collides with the set."""
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        ruleset = _render(NFTablesManager())
        forward_chain = _chain_section(ruleset, "forward")
        assert (
            'iifname "enp0s31f6" meta l4proto tcp ct direction original ct original proto-dst {11434} drop'
            in forward_chain
        )

    def test_docker_user_port_set_with_db_rule(self, monkeypatch) -> None:
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        ruleset = _render(NFTablesManager())
        forward_chain = _chain_section(ruleset, "forward")
        assert (
            'iifname "enp0s31f6" meta l4proto tcp ct direction original ct original proto-dst {11434} drop'
            in forward_chain
        )

    def test_docker_user_port_set_defaults_without_db_rule(self, monkeypatch) -> None:
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        rules = [r for r in _base_rules() if "internal-port" not in r.name]
        ruleset = _render(NFTablesManager(), rules=rules)
        forward_chain = _chain_section(ruleset, "forward")
        expected_set = "{5000, 5055, 5678, 8000, 8001, 8080, 8089, 8090, 8091, 8096, 8100, 8201, 8502, 8888, 9090, 10000, 11434}"
        assert f"ct original proto-dst {expected_set} drop" in forward_chain
        assert tuple(DEFAULT_INTERNAL_PORTS) == (
            5000,
            5055,
            5678,
            8000,
            8001,
            8080,
            8089,
            8090,
            8091,
            8096,
            8100,
            8201,
            8502,
            8888,
            9090,
            10000,
            11434,
        )

    def test_no_masquerade_rule_ever(self, monkeypatch) -> None:
        """Docker owns NAT; masquerade may appear only as a skip comment."""
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        ruleset = _render(NFTablesManager(), nat=_nat_rules())
        assert not re.search(r"^\s+masquerade\s", ruleset, re.MULTILINE)
        assert "masquerade skipped (docker owns NAT): wan masquerade" in ruleset

    def test_snat_dnat_render_but_only_with_nat_rules(self, monkeypatch) -> None:
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        manager = NFTablesManager()
        with_nat = _render(manager, nat=_nat_rules())
        assert "chain prerouting" in with_nat
        assert "chain postrouting" in with_nat
        assert (
            "ip daddr 46.4.63.216 ip protocol tcp tcp dport 25 dnat to 172.20.0.10:25 comment \"mail dnat\""
            in with_nat
        )
        assert "ip saddr 10.80.0.0/16 snat to 46.4.63.216" in with_nat

        without_nat = _render(manager, nat=[])
        assert "chain prerouting" not in without_nat
        assert "chain postrouting" not in without_nat


class TestChainPlacement:
    def test_loopback_guards_render_in_raw_prerouting(self, monkeypatch) -> None:
        """Todo 39 A32: the guards live in raw PREROUTING (pre-DNAT); the
        input hook sees docker's 127.0.0.1-published flows already DNAT'd."""
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        ruleset = _render(NFTablesManager())
        prerouting = _chain_section(ruleset, "raw_prerouting")
        assert (
            'iifname != "lo" ip daddr 127.0.0.1 tcp dport {8000, 8001, 8080} drop'
            in prerouting
        )
        assert "type filter hook prerouting priority -300; policy accept;" in prerouting

    def test_loopback_guards_never_in_input_or_forward(self, monkeypatch) -> None:
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        ruleset = _render(NFTablesManager())
        input_chain = _chain_section(ruleset, "input")
        forward_chain = _chain_section(ruleset, "forward")
        assert "127.0.0.1" not in input_chain
        assert "127.0.0.1" not in forward_chain

    def test_anti_spoof_renders_in_raw_prerouting_only(self, monkeypatch) -> None:
        """Todo 39b: anti-spoof must run PRE-DNAT. In the forward chain it
        also matches docker's DNAT'd published-port flows (post-DNAT daddr is
        the container IP) and drops every WAN-published port."""
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        ruleset = _render(NFTablesManager())
        input_chain = _chain_section(ruleset, "input")
        forward_chain = _chain_section(ruleset, "forward")
        prerouting = _chain_section(ruleset, "raw_prerouting")
        assert 'iifname != "br-abc123" ip daddr 172.19.0.5 drop' in prerouting
        assert "172.19.0.5" not in input_chain
        assert "172.19.0.5" not in forward_chain

    def test_anti_spoof_bridge_parsed_from_name_convention(self, monkeypatch) -> None:
        """Todo 38/39 gap: rows carry the bridge in the name ("via <bridge>"),
        not in interface_in (the schema column does not exist)."""
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        rules = _base_rules() + [
            _rule(
                14,
                "anti-spoof 172.18.0.3 via br-d46e3a305cbd",
                chain="forward",
                destination="172.18.0.3/32",
                action=FirewallAction.DROP,
            ),
            _rule(
                15,
                "anti-spoof fd00:42::2 via docker0",
                chain="forward",
                destination="fd00:42::2/128",
                action=FirewallAction.DROP,
            ),
        ]
        ruleset = _render(NFTablesManager(), rules=rules)
        prerouting = _chain_section(ruleset, "raw_prerouting")
        assert (
            'iifname != "br-d46e3a305cbd" ip daddr 172.18.0.3/32 drop'
            in prerouting
        )
        assert 'iifname != "docker0" ip6 daddr fd00:42::2/128 drop' in prerouting

    def test_ipv6_scoping_matches_open_set(self, monkeypatch) -> None:
        """Oracle #8: v6 opens only 22/80/443/51820; mail ports stay v4-only."""
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        ruleset = _render(NFTablesManager())
        assert (
            "meta nfproto ipv4 tcp dport {22, 25, 53, 80, 110, 143, 443, 993, 995, 21114-21119} accept"
            in ruleset
        )
        assert "meta nfproto ipv4 udp dport {53, 21116, 51820} accept" in ruleset
        assert "meta nfproto ipv6 tcp dport {22, 80, 443} accept" in ruleset
        assert "meta nfproto ipv6 udp dport {51820} accept" in ruleset

    def test_ordering_invariant_ssh_wg_before_user_rules(self, monkeypatch) -> None:
        """A console rule can never override SSH/WG/established access."""
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        ruleset = _render(NFTablesManager())
        lines = ruleset.splitlines()
        mandatory = lines.index("        ct state established,related accept")
        meter = lines.index(
            "        meta nfproto ipv4 tcp dport 22 meter ssh_limit "
            "{ ip saddr limit rate over 8/minute burst 5 packets } drop"
        )
        first_user = next(
            i for i, line in enumerate(lines) if "user rule input" in line
        )
        final_drop = lines.index('        log prefix "FIREWALL-DROP: " limit rate 5/minute drop')
        assert mandatory < meter < first_user < final_drop
        assert 'tcp dport 5432 drop' in ruleset  # postgres never exposed

    def test_firewall_drop_log_gated_by_logging_flag(self, monkeypatch) -> None:
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        with_log = _render(NFTablesManager())
        assert 'log prefix "FIREWALL-DROP: " limit rate 5/minute drop' in with_log

        without_log = _render(NFTablesManager(), enable_logging=False)
        assert "FIREWALL-DROP" not in without_log
        input_chain = _chain_section(without_log, "input")
        assert input_chain.rstrip().endswith("        drop\n    }")

    def test_conntrack_flag_controls_ct_rules(self, monkeypatch) -> None:
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        without_ct = _render(NFTablesManager(), enable_conntrack=False)
        assert "ct state established,related" not in without_ct
        assert "ct state invalid" not in without_ct

        with_ct = _render(NFTablesManager())
        assert "ct state established,related accept" in with_ct
        assert "ct state invalid drop" in with_ct


class TestTodo39bParity:
    """Regressions for the todo-39b parity fixes (checklist A05/A06/A29/A32/D18
    and the published-port divergence found in the 7b render)."""

    def test_udp_25_not_opened(self, monkeypatch) -> None:
        """Todo 39 A29: live opens tcp/25 only (v4:82); the renderer must not
        open udp/25 (live drops it)."""
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        ruleset = _render(NFTablesManager())
        assert "meta nfproto ipv4 udp dport {53, 21116, 51820} accept" in ruleset
        assert "meta nfproto ipv4 udp dport {25," not in ruleset

    def test_docker0_accept_after_meters(self, monkeypatch) -> None:
        """Live INPUT order (lines 80-96): the hashlimits precede the docker0
        accept, so docker0-sourced ssh/http/https/wg IS rate-limited. An early
        docker0 accept would let bridge traffic bypass the meters."""
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        ruleset = _render(NFTablesManager())
        input_chain = _chain_section(ruleset, "input")
        meter = input_chain.index("meta nfproto ipv4 tcp dport 22 meter ssh_limit")
        mgmt = input_chain.index("meta nfproto ipv4 tcp dport {22,")
        docker0 = input_chain.index('iifname "docker0" accept')
        pg = input_chain.index("tcp dport 5432 drop")
        assert meter < mgmt < docker0 < pg

    def test_invalid_drop_after_accepts(self, monkeypatch) -> None:
        """Live has no invalid-state rule: invalids to open ports/lo/docker0
        pass its unqualified accepts. The explicit invalid drop must therefore
        sit AFTER the accepts and cover only the policy-DROP remainder."""
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        ruleset = _render(NFTablesManager())
        input_chain = _chain_section(ruleset, "input")
        docker0 = input_chain.index('iifname "docker0" accept')
        first_user = input_chain.index("user rule input")
        invalid = input_chain.index("ct state invalid drop")
        final = input_chain.index('log prefix "FIREWALL-DROP: " limit rate 5/minute drop')
        assert docker0 < first_user < invalid < final

    def test_raw_prerouting_skipped_in_validation_mode(self, monkeypatch) -> None:
        monkeypatch.setenv("VALIDATION_MODE", "1")
        ruleset = _render(NFTablesManager())
        assert "raw_prerouting" not in ruleset

    def test_raw_prerouting_omitted_without_rules(self, monkeypatch) -> None:
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        ruleset = _render(NFTablesManager(), rules=[])
        assert "chain raw_prerouting" not in ruleset


class TestValidationMode:
    """a2: VALIDATION_MODE=1 renders a pass-through ruleset."""

    def test_validation_render_has_zero_drop_and_meter(self, monkeypatch) -> None:
        monkeypatch.setenv("VALIDATION_MODE", "1")
        ruleset = _render(NFTablesManager())
        assert "drop" not in ruleset
        assert "meter" not in ruleset
        assert "limit rate 5/second" not in ruleset
        assert ruleset.count("VW-VALIDATION") == 3
        assert ruleset.count("limit rate 10/minute") == 3
        for chain in ("input", "forward", "output"):
            section = _chain_section(ruleset, chain)
            assert f"policy accept;" in section

    def test_validation_render_skips_nat(self, monkeypatch) -> None:
        monkeypatch.setenv("VALIDATION_MODE", "1")
        ruleset = _render(NFTablesManager())
        assert "chain prerouting" not in ruleset
        assert "chain postrouting" not in ruleset

    def test_validation_flag_flip_flips_output(self, monkeypatch) -> None:
        """Mutation check: flipping the flag must flip the rendered output."""
        manager = NFTablesManager()
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        real = _render(manager)
        monkeypatch.setenv("VALIDATION_MODE", "1")
        validation = _render(manager)
        assert real != validation
        assert "policy drop" in real and "policy drop" not in validation
        assert "VW-VALIDATION" not in real and "VW-VALIDATION" in validation
        assert "FIREWALL-DROP" in real and "FIREWALL-DROP" not in validation


class TestUserRuleRendering:
    def test_user_rule_with_limit_and_comment(self, monkeypatch) -> None:
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        ruleset = _render(NFTablesManager())
        assert (
            'ip protocol tcp tcp dport 21115 accept comment "user rule input"'
            in ruleset
        )
        assert (
            'ip protocol tcp tcp dport 9090 limit rate 30/minute accept comment "limit-carrying user rule"'
            in ruleset
        )

    def test_user_rule_log_action_uses_quoted_prefix(self, monkeypatch) -> None:
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        rules = _base_rules() + [
            _rule(
                10,
                "log rule",
                protocol="udp",
                destination_port=9999,
                action=FirewallAction.LOG,
                order=70,
            )
        ]
        ruleset = _render(NFTablesManager(), rules=rules)
        assert (
            'ip protocol udp udp dport 9999 log prefix "[NFT log rule]" accept'
            in ruleset
        )

    def test_ipv6_user_rule_uses_nexthdr(self, monkeypatch) -> None:
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        rules = _base_rules() + [
            _rule(
                11,
                "v6 rule",
                source="2001:db8::/32",
                protocol="tcp",
                destination_port=8443,
                action=FirewallAction.ACCEPT,
                order=80,
            )
        ]
        ruleset = _render(NFTablesManager(), rules=rules)
        assert "ip6 saddr 2001:db8::/32 ip6 nexthdr tcp tcp dport 8443 accept" in ruleset

    def test_malformed_rule_renders_bare_accept(self, monkeypatch) -> None:
        """A rule with all optionals unset must still yield nft-valid syntax."""
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        rules = [FirewallRule(id=20, name="bare", chain="input")]
        ruleset = _render(NFTablesManager(), rules=rules)
        input_chain = _chain_section(ruleset, "input")
        assert "        accept\n" in input_chain

    def test_invalid_limit_and_ifname_are_skipped(self, monkeypatch) -> None:
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        rules = _base_rules() + [
            _rule(
                12,
                "bad limit",
                protocol="tcp",
                destination_port=7777,
                limit="30/minutes",
                order=90,
            ),
            _rule(
                13,
                "bad iface",
                interface_in="eth0; rm -rf /",
                destination="10.0.0.1",
                order=91,
            ),
        ]
        ruleset = _render(NFTablesManager(), rules=rules)
        assert "30/minutes" not in ruleset
        assert "rm -rf" not in ruleset
        assert 'iifname "eth0; rm -rf /"' not in ruleset

    def test_wan_interface_sanitized_falls_back_to_default(self, monkeypatch) -> None:
        monkeypatch.delenv("VALIDATION_MODE", raising=False)
        ruleset = _render(
            NFTablesManager(), interfaces=[{"name": "bad iface!", "type": "wan"}]
        )
        assert 'iifname "enp0s31f6" meta l4proto tcp ct direction original' in ruleset
        assert 'iifname "bad iface!"' not in ruleset


class TestPureHelpers:
    def test_port_set_sorts_and_ranges(self) -> None:
        manager = NFTablesManager()
        assert manager._port_set({22, 443, 80}) == "{22, 80, 443}"
        assert manager._port_set({(21114, 21119), 22}) == "{22, 21114-21119}"

    def test_parse_addr_family(self) -> None:
        assert NFTablesManager._parse_addr_family("10.0.0.1") == "ip"
        assert NFTablesManager._parse_addr_family("2001:db8::1") == "ip6"
        assert NFTablesManager._parse_addr_family("not-an-ip") is None

    def test_quote_escapes(self) -> None:
        from viswall_firewall_agent.nft import _quote

        assert _quote('a"b') == '"a\'b"'
        assert _quote("plain") == '"plain"'

    def test_validators(self) -> None:
        from viswall_firewall_agent.nft import _safe_ifname, _valid_limit, _valid_net

        assert _valid_net("10.0.0.0/8") is True
        assert _valid_net("nope") is False
        assert _valid_limit("30/minute") is True
        assert _valid_limit("30/minutes") is False
        assert _safe_ifname("enp0s31f6") is True
        assert _safe_ifname("eth0; rm") is False
