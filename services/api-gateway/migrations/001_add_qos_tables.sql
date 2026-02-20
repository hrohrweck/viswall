-- Migration: Add QoS (Traffic Shaping) tables
-- Generated: 2026-02-20
-- Description: Creates qos_policies and qos_classes tables for traffic shaping management

-- ============================================================================
-- QoS Policies table
-- ============================================================================

CREATE TABLE IF NOT EXISTS qos_policies (
    id SERIAL PRIMARY KEY,
    instance_id INTEGER NOT NULL REFERENCES instances(id) ON DELETE CASCADE,
    interface_id INTEGER REFERENCES network_interfaces(id) ON DELETE SET NULL,
    
    name VARCHAR(100) NOT NULL,
    description TEXT,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    
    algorithm VARCHAR(20) NOT NULL DEFAULT 'cake',
    download_kbps INTEGER NOT NULL,
    upload_kbps INTEGER NOT NULL,
    
    interface_name VARCHAR(50) NOT NULL,
    
    applied BOOLEAN NOT NULL DEFAULT FALSE,
    last_applied_at TIMESTAMP,
    apply_error TEXT,
    
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE qos_policies IS 'QoS policy attached to a network interface on an instance';
COMMENT ON COLUMN qos_policies.algorithm IS 'tc algorithm: cake, fq_codel, or htb';
COMMENT ON COLUMN qos_policies.download_kbps IS 'Ingress rate ceiling in kbps';
COMMENT ON COLUMN qos_policies.upload_kbps IS 'Egress rate ceiling in kbps';

-- Index for common query pattern
CREATE INDEX IF NOT EXISTS idx_qos_policies_instance_id ON qos_policies(instance_id);
CREATE INDEX IF NOT EXISTS idx_qos_policies_interface_name ON qos_policies(instance_id, interface_name);

-- ============================================================================
-- QoS Classes table (for HTB algorithm)
-- ============================================================================

CREATE TABLE IF NOT EXISTS qos_classes (
    id SERIAL PRIMARY KEY,
    policy_id INTEGER NOT NULL REFERENCES qos_policies(id) ON DELETE CASCADE,
    
    name VARCHAR(50) NOT NULL,
    priority INTEGER NOT NULL DEFAULT 2,
    
    min_rate_kbps INTEGER NOT NULL,
    max_rate_kbps INTEGER NOT NULL,
    
    match_ports JSONB DEFAULT '[]',
    match_dscp VARCHAR(10),
    match_protocol VARCHAR(10) DEFAULT 'any',
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE qos_classes IS 'Traffic class within an HTB QoS policy';
COMMENT ON COLUMN qos_classes.priority IS '1 = highest, 3 = lowest';
COMMENT ON COLUMN qos_classes.min_rate_kbps IS 'Guaranteed bandwidth in kbps';
COMMENT ON COLUMN qos_classes.max_rate_kbps IS 'Burst ceiling in kbps';
COMMENT ON COLUMN qos_classes.match_ports IS 'List of destination port numbers to match';

-- Index for class lookups by policy
CREATE INDEX IF NOT EXISTS idx_qos_classes_policy_id ON qos_classes(policy_id);

-- ============================================================================
-- Trigger to auto-update updated_at timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_qos_policies_updated_at
    BEFORE UPDATE ON qos_policies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_qos_classes_updated_at
    BEFORE UPDATE ON qos_classes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Rollback (if needed)
-- ============================================================================
-- To rollback:
-- DROP TABLE IF EXISTS qos_classes;
-- DROP TABLE IF EXISTS qos_policies;
