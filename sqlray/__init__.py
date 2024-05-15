import json
from openai import OpenAI


class SQLRay:
    """
    SQLRay is a class that is used to interact with the OpenAI API
    SQLRay will optimize the queries that are passed to it
    """

    __slots__ = [
        "openai_client",
        "columns",
        "indexes",
        "tables_info",
        "views",
        "server_version",
        "model",
    ]
    """
    Slots are used to restrict the attributes that can be assigned to an object
    This is done to reduce the memory footprint of the object
    """

    def __init__(self, openai_client: OpenAI, model: str = "gpt-3.5-turbo"):
        """
        :param openai_client: OpenAI object that is used to interact with the OpenAI API
        """
        self.openai_client = openai_client
        self.model = model

    def load_database_schema(self, database_schema: object):
        """
        :param database_schema: An object that contains the schema of the database
        """
        if "columns" not in database_schema:
            raise ValueError("Database schema must contain columns")
        if "indexes" not in database_schema:
            raise ValueError("Database schema must contain indexes")
        if "tables" not in database_schema:
            raise ValueError("Database schema must contain tables")
        if "views" not in database_schema:
            raise ValueError("Database schema must contain views")
        if "version" not in database_schema:
            raise ValueError("Database schema must contain version")

        self.columns = database_schema["columns"]
        self.indexes = database_schema["indexes"]
        self.tables_info = database_schema["tables"]
        self.views = database_schema["views"]
        self.server_version = database_schema["version"]

    def extract_tables(self, query: str) -> dict:
        """
        This function is used to extract the tables from a SQL query

        :param query: The query from which the tables need to be extracted
        :return: The tables extracted from the query
        """

        prompt = f"""
    The following is a SQL query that selects data from a database. Please extract the tables from the query. Answering as JSON with the following format:
    {{
        "tables": [
            "table1",
            "table2",
            "table3"
        ]
    }}
    ---
    SQL query:
    {query}
    ---
    """
        prompt = prompt.strip()
        response = self.openai_client.chat.completions.create(
            model=self.model, messages=[{"role": "user", "content": prompt}]
        )

        response_content = response.choices[0].message.content

        if "```json" in response_content:
            response_content = response_content[8:-3]

        return json.loads(response_content)["tables"]

    def extract_metadata(self, tables: list):
        """
        This function is used to extract the metadata of the tables

        :param tables: The tables for which the metadata needs to be extracted
        :return: The metadata of the tables
        """
        columns = []
        indexes = []
        views = []
        tables_info = []

        for table in tables:
            if self.columns is not None:
                for column in self.columns:
                    if column["table"] == table:
                        columns.append(column)

            if self.indexes is not None:
                for index in self.indexes:
                    if index["table"] == table:
                        indexes.append(index)

            if self.views is not None:
                for view in self.views:
                    if view["table"] == table:
                        views.append(view)

            if self.tables_info is not None:
                for table_info in self.tables_info:
                    if table_info["table"] == table:
                        tables_info.append(table_info)

        return columns, indexes, tables_info, views, self.server_version

    def optimize_query(self, query: str):
        """
        :param query: The query that needs to be optimized
        :return: The optimized query
        """
        tables = self.extract_tables(query)
        columns, indexes, tables_info, views, server_version = self.extract_metadata(
            tables
        )

        prompt = f"""
    Objective: Optimize a given SQL query for better performance.
    Instructions:
    1. Examine the provided SQL query, tables, columns, and indexes.
    2. Identify potential inefficiencies in the query and/or schema design.
    3. Propose optimizations which may include:
        - Rewriting the query for efficiency.
        - Suggesting new indexes or modifications to existing indexes.
    4. Document your proposed changes in JSON format, as specified below. And answer only the following JSON format:
    {{
        "prepare_query": [
            "create index1....",
            "other things before running the query...",
        ],
        "query": "SELECT ... # optimized query",
        "optimization_score": 0.5, # a score between 0 and 1, where 0 is no optimization, and 1 is a perfect optimization
        "explanation": "explanation of the optimization, and explain differences between the original query and the optimized query"
    }}
    Note:
    - If the query can be optimized solely by creating indexes, without altering the SQL command, only include the index creation commands.
    - Ensure your explanation is in plain English, accessible to someone with a basic understanding of SQL.
    Provided Information:
    ---
    Server: {server_version}
    ---
    Tables:
    {tables_info}
    ---
    Columns:
    {columns}
    ---
    Indexes:
    {indexes}
    ---
    Views:
    {views}
    ---
    SQL query:
    {query}
    ---
    """
        prompt = prompt.strip()

        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )

        optimized_response = response.choices[0].message.content

        if "```json" in optimized_response:
            optimized_response = optimized_response[7:-3]
        if "---" in optimized_response:
            optimized_response = optimized_response.split("---")[1]

        return json.loads(optimized_response)
