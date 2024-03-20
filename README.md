# SQL Query Optimizer CLI

This CLI tool leverages the capabilities of SQLRay and OpenAI to analyze and optimize SQL queries. It's designed to improve the performance of your SQL queries by suggesting optimizations based on your database schema and the specifics of your query.

## Features

- **Optimize SQL Queries:** Submit your SQL query to be optimized based on your actual database schema.
- **Interactive Mode:** Enter interactive mode to continuously optimize SQL queries with the ability to load a new schema as needed.
- **OpenAI Integration:** Utilizes OpenAI's powerful models to suggest optimizations.

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