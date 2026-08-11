-- Reemplazar TU-BUCKET por el nombre real del bucket (red-cuidado-storage-xxxxxxxx)

CREATE DATABASE IF NOT EXISTS redcuidado_analytics;

CREATE EXTERNAL TABLE IF NOT EXISTS redcuidado_analytics.users (
  id bigint,
  username string,
  email string,
  first_name string,
  last_name string,
  is_active boolean
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
  'separatorChar' = ',',
  'quoteChar' = '"',
  'escapeChar' = '\\'
)
STORED AS TEXTFILE
LOCATION 's3://TU-BUCKET/athena/source/users/'
TBLPROPERTIES ('skip.header.line.count' = '1');

CREATE EXTERNAL TABLE IF NOT EXISTS redcuidado_analytics.courses (
  id bigint,
  title string,
  code string,
  description string,
  duration_days bigint
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
  'separatorChar' = ',',
  'quoteChar' = '"',
  'escapeChar' = '\\'
)
STORED AS TEXTFILE
LOCATION 's3://TU-BUCKET/athena/source/courses/'
TBLPROPERTIES ('skip.header.line.count' = '1');

CREATE EXTERNAL TABLE IF NOT EXISTS redcuidado_analytics.enrollments (
  id bigint,
  user_id bigint,
  course_id bigint,
  enrolled_at string,
  is_completed boolean
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
  'separatorChar' = ',',
  'quoteChar' = '"',
  'escapeChar' = '\\'
)
STORED AS TEXTFILE
LOCATION 's3://TU-BUCKET/athena/source/enrollments/'
TBLPROPERTIES ('skip.header.line.count' = '1');

CREATE EXTERNAL TABLE IF NOT EXISTS redcuidado_analytics.test_results (
  id bigint,
  user_id bigint,
  test_id bigint,
  score double,
  passed boolean,
  attempted_at string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
  'separatorChar' = ',',
  'quoteChar' = '"',
  'escapeChar' = '\\'
)
STORED AS TEXTFILE
LOCATION 's3://TU-BUCKET/athena/source/test_results/'
TBLPROPERTIES ('skip.header.line.count' = '1');

CREATE EXTERNAL TABLE IF NOT EXISTS redcuidado_analytics.bitacora (
  id bigint,
  author_id bigint,
  entry_type string,
  description string,
  created_at string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
  'separatorChar' = ',',
  'quoteChar' = '"',
  'escapeChar' = '\\'
)
STORED AS TEXTFILE
LOCATION 's3://TU-BUCKET/athena/source/bitacora/'
TBLPROPERTIES ('skip.header.line.count' = '1');

-- KPIs de ejemplo (los mismos que corre scripts/etl_from_sqlite.py)
SELECT COUNT(*) AS total_courses FROM courses;

SELECT COALESCE(ROUND(100.0 * SUM(CASE WHEN is_completed THEN 1 ELSE 0 END)
  / NULLIF(COUNT(*), 0), 1), 0) AS completion_rate FROM enrollments;

SELECT COALESCE(ROUND(AVG(score), 1), 0) AS average_score FROM test_results;
