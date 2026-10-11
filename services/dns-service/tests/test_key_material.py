"""Tests for DNSSEC/TSIG key material generation."""

from __future__ import annotations

import base64
import uuid

import pytest

from viswall_dns_agent.agent import DNSAgent
from viswall_dns_agent.config import AgentConfig

# Generated per test run — the fixture key value must never look like a
# real credential that leaked into the repo.
TEST_AGENT_KEY = "vw-test-" + uuid.uuid4().hex


@pytest.fixture
def agent(tmp_path):
    cfg = AgentConfig(
        named_conf_path=str(tmp_path / "named.conf.local"),
        named_options_path=str(tmp_path / "named.conf.options"),
        zones_dir=str(tmp_path / "zones"),
        keys_dir=str(tmp_path / "keys"),
        allow_commands=False,
        instance_api_key=TEST_AGENT_KEY,
        gateway_url=None,
        instance_id=None,
        heartbeat_interval=30,
        api_host="127.0.0.1",
        api_port=8082,
    )
    return DNSAgent(cfg)


def test_generate_tsig_secret_is_base64_and_csprng_sized(agent):
    secret = agent.generate_tsig_secret("hmac-sha256")
    assert len(base64.b64decode(secret)) == 32

    secret512 = agent.generate_tsig_secret("hmac-sha512")
    assert len(base64.b64decode(secret512)) == 64

    assert agent.generate_tsig_secret("hmac-sha256") != agent.generate_tsig_secret(
        "hmac-sha256"
    )


def test_generate_tsig_secret_rejects_unknown_algorithm(agent):
    with pytest.raises(ValueError):
        agent.generate_tsig_secret("hmac-md5")


def test_generate_key_tag_stays_in_key_tag_range(agent):
    # Key tags are 16-bit values; the agent draws them from the CSPRNG and
    # constrains them to 1024..65534 (legacy BIND excludes small reserved
    # ranges at the low end).
    tags = {agent._generate_key_tag(1, "KSK", 4096) for _ in range(200)}

    assert all(1024 <= tag <= 65534 for tag in tags)
    assert len(tags) > 10  # not degenerate
