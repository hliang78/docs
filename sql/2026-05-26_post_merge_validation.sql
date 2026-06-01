SET NAMES utf8mb4;
SET character_set_client = utf8mb4;
SET character_set_connection = utf8mb4;
SET character_set_results = utf8mb4;

SELECT
  COUNT(*) AS imported_template_count
FROM platform_task_template
WHERE id IN (
  'de29845f-5758-11f1-8dfb-0050569b3ce3',
  'f1882e66-5758-11f1-8dfb-0050569b3ce3',
  'f25ff969-5758-11f1-8dfb-0050569b3ce3',
  'f3242b55-5758-11f1-8dfb-0050569b3ce3',
  'f3eea34e-5758-11f1-8dfb-0050569b3ce3',
  'f4b23008-5758-11f1-8dfb-0050569b3ce3'
);

SELECT
  id,
  name,
  app_type,
  playbook_path,
  repo_url,
  repo_branch,
  description
FROM platform_task_template
WHERE id IN (
  'de29845f-5758-11f1-8dfb-0050569b3ce3',
  'f1882e66-5758-11f1-8dfb-0050569b3ce3',
  'f25ff969-5758-11f1-8dfb-0050569b3ce3',
  'f3242b55-5758-11f1-8dfb-0050569b3ce3',
  'f3eea34e-5758-11f1-8dfb-0050569b3ce3',
  'f4b23008-5758-11f1-8dfb-0050569b3ce3'
)
ORDER BY name;

SELECT
  id,
  name,
  description,
  vars_json
FROM platform_variable_set
WHERE id = '583f754a-2cd7-11f1-b70a-0050569b3ce3';
