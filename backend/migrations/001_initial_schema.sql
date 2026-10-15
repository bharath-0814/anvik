-- Migration 001: Initial Anvik Database Schema for Accounts, Devices, Transactions, Complaints, and Imports
-- Compatible with Turso (libSQL/SQLite)

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at_utc TEXT NOT NULL
);

-- Accounts table
CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    holder_name TEXT NOT NULL,
    vpa TEXT UNIQUE NOT NULL,
    bank TEXT NOT NULL,
    raw_created_at TEXT NOT NULL,
    created_at_utc TEXT
);

-- Unique Devices table
CREATE TABLE IF NOT EXISTS devices (
    device_id TEXT PRIMARY KEY
);

-- Account to Device many-to-many relationship table
CREATE TABLE IF NOT EXISTS account_devices (
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    device_id TEXT NOT NULL REFERENCES devices(device_id),
    PRIMARY KEY (account_id, device_id)
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    txn_id TEXT PRIMARY KEY,
    sender_account_id TEXT NOT NULL REFERENCES accounts(account_id),
    receiver_account_id TEXT NOT NULL REFERENCES accounts(account_id),
    sender_vpa TEXT NOT NULL,
    receiver_vpa TEXT NOT NULL,
    amount_paise INTEGER NOT NULL CHECK (amount_paise >= 0),
    amount_inr REAL NOT NULL,
    raw_timestamp TEXT NOT NULL,
    timestamp_utc TEXT NOT NULL,
    txn_type TEXT NOT NULL,
    status TEXT NOT NULL,
    device_id TEXT NOT NULL REFERENCES devices(device_id)
);

-- Complaints table
CREATE TABLE IF NOT EXISTS complaints (
    complaint_id TEXT PRIMARY KEY,
    victim_account_id TEXT NOT NULL REFERENCES accounts(account_id),
    victim_vpa TEXT NOT NULL,
    txn_id TEXT NOT NULL REFERENCES transactions(txn_id),
    raw_complaint_date TEXT NOT NULL,
    complaint_date_utc TEXT
);

-- Dataset Import tracking table for idempotency
CREATE TABLE IF NOT EXISTS dataset_imports (
    import_id TEXT PRIMARY KEY,
    dataset_id TEXT NOT NULL,
    data_hash TEXT NOT NULL,
    imported_at_utc TEXT NOT NULL,
    account_count INTEGER NOT NULL,
    device_count INTEGER NOT NULL,
    account_device_count INTEGER NOT NULL,
    transaction_count INTEGER NOT NULL,
    complaint_count INTEGER NOT NULL,
    status TEXT NOT NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_accounts_vpa ON accounts(vpa);
CREATE INDEX IF NOT EXISTS idx_txns_sender_acc ON transactions(sender_account_id);
CREATE INDEX IF NOT EXISTS idx_txns_receiver_acc ON transactions(receiver_account_id);
CREATE INDEX IF NOT EXISTS idx_txns_timestamp_utc ON transactions(timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_txns_status_type ON transactions(status, txn_type);
CREATE INDEX IF NOT EXISTS idx_txns_device ON transactions(device_id);
CREATE INDEX IF NOT EXISTS idx_complaints_txn ON complaints(txn_id);
CREATE INDEX IF NOT EXISTS idx_complaints_victim_acc ON complaints(victim_account_id);
CREATE INDEX IF NOT EXISTS idx_acc_devices_dev ON account_devices(device_id);
