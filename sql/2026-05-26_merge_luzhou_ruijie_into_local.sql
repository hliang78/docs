-- Merge Ruijie-related DC2 config from luzhou into local.
-- Scope: only the net-ruijie policy dataset selection in local MySQL.

START TRANSACTION;

UPDATE device_collection2_policy
SET dataset_keys_json = '["snmp_sys_descr","snmp_if_table","cli_lldp_neighbors"]'
WHERE policy_id = 'dc2p-default-profile-net-ruijie';

COMMIT;
