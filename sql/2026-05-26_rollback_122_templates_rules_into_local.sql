SET NAMES utf8mb4;
SET character_set_client = utf8mb4;
SET character_set_connection = utf8mb4;
SET character_set_results = utf8mb4;

START TRANSACTION;

DELETE FROM platform_task_template
WHERE id IN (
  'de29845f-5758-11f1-8dfb-0050569b3ce3',
  'f1882e66-5758-11f1-8dfb-0050569b3ce3',
  'f25ff969-5758-11f1-8dfb-0050569b3ce3',
  'f3242b55-5758-11f1-8dfb-0050569b3ce3',
  'f3eea34e-5758-11f1-8dfb-0050569b3ce3',
  'f4b23008-5758-11f1-8dfb-0050569b3ce3'
);

UPDATE platform_variable_set
SET
  created_at = '2026-03-31 07:58:03.534',
  updated_at = '2026-03-31 07:58:03.534',
  deleted_at = NULL,
  name = 'task-center-ansible-switch-baseline-defaults',
  description = '交换机主线基线盘点默认变量组。',
  vars_json = '{"cisco_ios_baseline_commands":["show version","show inventory","show ip interface brief","show lldp neighbors detail"],"cisco_nxos_baseline_commands":["show version","show inventory","show interface brief","show lldp neighbors detail"],"huawei_ce_baseline_commands":["display version","display device","display ip interface brief","display lldp neighbor verbose"],"h3c_cli_baseline_commands":["display version","display device manuinfo","display ip interface brief","display lldp neighbor-information verbose"]}',
  parameter_specs_json = NULL,
  tenant_code = NULL
WHERE id = '583f754a-2cd7-11f1-b70a-0050569b3ce3';

COMMIT;
