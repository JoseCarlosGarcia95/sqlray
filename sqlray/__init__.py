import json
from pydantic import BaseModel
from openai import OpenAI
from typing import List


class ExtractedTables(BaseModel):
    tables: List[str]


class OptimizedQueryResponse(BaseModel):
    prepare_query: List[str]
    query: str
    optimization_score: float
    explanation: str


class SQLRay:
    """
    SQLRay is a class that interacts with the OpenAI API.
    It optimizes SQL queries passed to it.
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

    def __init__(self, openai_client: OpenAI, model: str = "gpt-4o-2024-08-06"):
        self.openai_client = openai_client
        self.model = model

    def load_database_schema(self, database_schema: object):
        required_keys = ["columns", "indexes", "tables", "views", "version"]
        for key in required_keys:
            if key not in database_schema:
                raise ValueError(f"Database schema must contain {key}")

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
                    if "table" not in column:
                        continue
                    if column["table"] == table:
                        columns.append(column)

            if self.indexes is not None:
                for index in self.indexes:
                    if "table" not in index:
                        continue
                    if index["table"] == table:
                        indexes.append(index)

            if self.views is not None:
                for view in self.views:
                    if "table" not in view:
                        continue
                    if view["table"] == table:
                        views.append(view)

            if self.tables_info is not None:
                for table_info in self.tables_info:
                    if "table" not in table_info:
                        continue
                    if table_info["table"] == table:
                        tables_info.append(table_info)

        return columns, indexes, tables_info, views, self.server_version

    def optimize_query(self, query: str):
        tables = self.extract_tables(query)
        columns, indexes, tables_info, views, server_version = self.extract_metadata(
            tables
        )

        prompt = f"""
        Objective: Optimize the provided SQL query for better performance without removing any part of the original query.

        Instructions:
        1. Carefully analyze the given SQL query, including the structure of the tables, columns, views, and indexes.
        2. Identify all potential inefficiencies in the query and/or schema design.
        3. Suggest optimizations, which may include:
            - Rewriting the entire SQL query for better efficiency while preserving all elements of the original logic.
            - Proposing new indexes or adjustments to existing indexes for improved performance.
        4. Present your recommendations in the following strict JSON format only:
        {{
            "prepare_query": [
                "CREATE INDEX index1 ON table(column);",
                "Other necessary preparation steps before executing the query..."
            ],
            "query": "SELECT ...",  # Fully optimized query without removing or omitting any part
            "optimization_score": 0.5,  # A score from 0 (no optimization) to 1 (perfect optimization)
            "explanation": "Detailed explanation of the optimization steps, including the differences between the original and optimized queries."
        }}

        Important Notes:
        - Do **not** remove or omit any part of the original query. The optimized query should include all necessary parts and be ready for direct execution.
        - If optimization can be achieved solely by adding or modifying indexes without changing the SQL command, provide only the relevant index creation commands.
        - Keep your explanation in clear, plain English, suitable for someone with a basic understanding of SQL.
        - Ensure that all returned queries are complete and ready for copy-pasting without additional modifications.

        Provided Information:
        ---
        Server Version:
        {server_version}
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
        Original SQL Query:
        {query}
        ---
        """
        prompt = prompt.strip()

        response = self.openai_client.beta.chat.completions.parse(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format=OptimizedQueryResponse,
        )

        return response.choices[0].message.parsed
