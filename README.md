# SQL Query Optimizer CLI

This CLI tool leverages the capabilities of SQLRay and OpenAI to analyze and optimize SQL queries. It's designed to improve the performance of your SQL queries by suggesting optimizations based on your database schema and the specifics of your query.

## Features

- **Optimize SQL Queries:** Submit your SQL query to be optimized based on your actual database schema.
- **Interactive Mode:** Enter interactive mode to continuously optimize SQL queries with the ability to load a new schema as needed.
- **OpenAI Integration:** Utilizes OpenAI's powerful models to suggest optimizations.

## Getting Started with SQLRay (Docker)

1. First of all, get the database schema and save a file database_schema.json with the schema. You can generate the schema directly from `Get database schema` section below.
2. Run the following command to start the SQLRay container:
```bash
docker run -it --rm -v $(pwd)/:/tmp/local -w /tmp/local ghcr.io/josecarlosgarcia95/sqlray:main interactive
```
3. Once the container is running, you can start optimizing your SQL queries.

### Example

I have the schema in a file called database_schema.json on my current working directory.
```bash
❯ docker run -it --rm -v $(pwd)/:/tmp/local -w /tmp/local sqlray interactive
Welcome to the interactive mode.
Please enter the OpenAI model [gpt-4o]: 
Please enter the OpenAI API key: sk-xxxx
Please enter the path to your database schema JSON file: database_schema.json
Database schema loaded successfully.
If you enter a file path, the query will be read from the file.
Please enter your SQL query (Type 'exit' to quit): SELECT * FROM users WHERE id = 1;
```

## Get database schema

To get the database schema, you can use the following command:

### MySQL 8.0+
```mysql
SELECT JSON_OBJECT( 'columns',( SELECT JSON_ARRAYAGG( JSON_OBJECT( 'schema', cols.table_schema, 'table', cols.table_name, 'name', cols.column_name, 'type', cols.column_type, 'nullable', (cols.IS_NULLABLE = 'YES'), 'collation', cols.COLLATION_NAME) ) FROM information_schema.columns cols WHERE cols.table_schema = DATABASE() ), 'indexes', ( SELECT JSON_ARRAYAGG( JSON_OBJECT( 'schema', indexes.table_schema, 'table', indexes.table_name, 'name', indexes.index_name, 'size', ( SELECT IFNULL(SUM(stat_value * @@innodb_page_size), -1) FROM mysql.innodb_index_stats WHERE stat_name = 'size' AND index_name = indexes.index_name AND table_name = indexes.table_name AND database_name = indexes.table_schema ), 'column', indexes.column_name, 'index_type', LOWER(indexes.index_type), 'cardinality', indexes.cardinality, 'direction', (CASE WHEN indexes.collation = 'D' THEN 'desc' ELSE 'asc' END), 'unique', (indexes.non_unique = 0) ) ) FROM information_schema.statistics indexes WHERE indexes.table_schema = DATABASE() ), 'tables', ( SELECT JSON_ARRAYAGG( JSON_OBJECT( 'schema', tbls.TABLE_SCHEMA, 'table', tbls.TABLE_NAME, 'rows', IFNULL(tbls.TABLE_ROWS, 0), 'type', IFNULL(tbls.TABLE_TYPE, ''), 'engine', IFNULL(tbls.ENGINE, ''), 'collation', IFNULL(tbls.TABLE_COLLATION, '') ) ) FROM information_schema.tables tbls WHERE tbls.table_schema = DATABASE() ), 'views', ( SELECT JSON_ARRAYAGG( JSON_OBJECT( 'schema', views.TABLE_SCHEMA, 'view_name', views.TABLE_NAME, 'definition', REPLACE(REPLACE(TO_BASE64(views.VIEW_DEFINITION), ' ', ''), '\n', '') ) ) FROM information_schema.views views WHERE views.table_schema = DATABASE() ), 'server_name', @@hostname, 'version', VERSION() ) AS info;
```

### MySQL 5.7+
```mysql
SELECT CONCAT( '{', '"columns": [', GROUP_CONCAT(DISTINCT columns_json SEPARATOR ','), '],', '"indexes": [', GROUP_CONCAT(DISTINCT indexes_json SEPARATOR ','), '],', '"tables": [', GROUP_CONCAT(DISTINCT tables_json SEPARATOR ','), '],', '"views": [', GROUP_CONCAT(DISTINCT views_json SEPARATOR ','), '],', '"server_name": "', @@hostname, '",', '"version": "', VERSION(), '"', '}') AS info FROM( SELECT CONCAT( '{', '"schema": "', cols.table_schema, '",', '"table": "', cols.table_name, '",', '"name": "', cols.column_name, '",', '"type": "', cols.column_type, '",', '"nullable": ', IF(cols.IS_NULLABLE = 'YES', 'true', 'false'), ',', '"collation": "', IFNULL(cols.COLLATION_NAME, ''), '"', '}' ) AS columns_json, NULL AS indexes_json, NULL AS tables_json, NULL AS views_json FROM information_schema.columns cols WHERE cols.table_schema = DATABASE() UNION ALL SELECT NULL, CONCAT( '{', '"schema": "', indexes.table_schema, '",', '"table": "', indexes.table_name, '",', '"name": "', indexes.index_name, '",', '"column": "', indexes.column_name, '",', '"index_type": "', LOWER(indexes.index_type), '",', '"cardinality": ', indexes.cardinality, ',', '"direction": "', IF(indexes.collation = 'D', 'desc', 'asc'), '",', '"unique": ', IF(indexes.non_unique = 0, 'true', 'false'), '}' ), NULL, NULL FROM information_schema.statistics indexes WHERE indexes.table_schema = DATABASE() UNION ALL SELECT NULL, NULL, CONCAT( '{', '"schema": "', tbls.TABLE_SCHEMA, '",', '"table": "', tbls.TABLE_NAME, '",', '"rows": ', IFNULL(tbls.TABLE_ROWS, 0), ',', '"type": "', IFNULL(tbls.TABLE_TYPE, ''), '",', '"engine": "', IFNULL(tbls.ENGINE, ''), '",', '"collation": "', IFNULL(tbls.TABLE_COLLATION, ''), '"', '}' ), NULL FROM information_schema.tables tbls WHERE tbls.table_schema = DATABASE() UNION ALL SELECT NULL, NULL, NULL, CONCAT( '{', '"schema": "', views.TABLE_SCHEMA, '",', '"view_name": "', views.TABLE_NAME, '",', '"definition": "', REPLACE(REPLACE(TO_BASE64(views.VIEW_DEFINITION), ' ', ''), '
', ''), '"', '}' ) FROM information_schema.views views WHERE views.table_schema = DATABASE() ) AS subqueries;
```

### PostgreSQL
```sql
SELECT json_build_object( 'columns',( SELECT json_agg( json_build_object( 'schema', cols.table_schema, 'table', cols.table_name, 'name', cols.column_name, 'type', cols.data_type, 'nullable', (cols.is_nullable = 'YES'), 'collation', cols.collation_name) ) FROM information_schema.columns cols WHERE cols.table_schema = current_schema() ), 'indexes', ( SELECT json_agg( json_build_object( 'schema', ix.schemaname, 'table', ix.tablename, 'name', ix.indexname, 'definition', ix.indexdef ) ) FROM pg_indexes ix WHERE ix.schemaname = current_schema() ), 'tables', ( SELECT json_agg( json_build_object( 'schema', tbl.table_schema, 'table', tbl.table_name, 'type', tbl.table_type, 'rows', ( SELECT reltuples::bigint FROM pg_class WHERE oid = ('"' || tbl.table_schema || '"."' || tbl.table_name || '"')::regclass ), 'engine', 'N/A', 'collation', 'N/A' ) ) FROM information_schema.tables tbl WHERE tbl.table_schema = current_schema() ), 'views', ( SELECT json_agg( json_build_object( 'schema', v.table_schema, 'view_name', v.table_name, 'definition', pg_get_viewdef(('"' || v.table_schema || '"."' || v.table_name || '"')::regclass) ) ) FROM information_schema.views v WHERE v.table_schema = current_schema() ), 'server_name', '', 'version', version() ) AS info;
```

This command will return a JSON object with the database schema, please create a file with the output.

## Installation

Before you can run the tool, ensure you have Python installed on your system. This tool has been tested with Python 3.8 and above.

You can install directly from PyPI using pip:

```bash
sudo pip install sqlray
```

You can run directly sqlray from the command line:

```bash
sqlray --help
```

Or using python -m:

```bash
python -m sqlray --help
```