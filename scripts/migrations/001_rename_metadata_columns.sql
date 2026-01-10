-- Migration: Rename 'metadata' columns to avoid SQLAlchemy conflict
-- Run this if you already have a database with 'metadata' columns

BEGIN;

-- Agents table
ALTER TABLE agents 
RENAME COLUMN metadata TO agent_metadata;

-- Transactions table
ALTER TABLE transactions 
RENAME COLUMN metadata TO tx_metadata;

-- Billing records table
ALTER TABLE billing_records 
RENAME COLUMN metering_metadata TO metering_metadata; -- Already correct

-- Stabilizer actions table
ALTER TABLE stabilizer_actions 
RENAME COLUMN metadata TO action_metadata;

-- Audit logs table
ALTER TABLE audit_logs 
RENAME COLUMN metadata TO event_metadata;

COMMIT;
