import sqlray
import json
from openai import OpenAI

client = OpenAI()

query_optimizer = sqlray.SQLRay(client, "gpt-4-turbo-preview")

# Load the database schema from database_schema.json
with open("database_schema.json", "r") as f:
    database_schema = json.load(f)

query_optimizer.load_database_schema(database_schema)

# Get query from query.txt
with open("query.txt", "r") as f:
    query = f.read()

print(query_optimizer.optimize_query(query))