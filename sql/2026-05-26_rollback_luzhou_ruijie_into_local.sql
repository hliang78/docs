-- Roll back the Ruijie-related DC2 config merge from luzhou into local.

START TRANSACTION;

UPDATE device_collection2_policy
SET dataset_keys_json = '["snmp_sys_descr","snmp_if_table","cli_interface_brief"]'
WHERE policy_id = 'dc2p-default-profile-net-ruijie';

COMMIT;
