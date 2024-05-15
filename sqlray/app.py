import click
import json
import os
from openai import OpenAI

from sqlray import SQLRay


@click.group()
def cli():
    """CLI application to optimize SQL queries using SQLRay and OpenAI."""
    pass


@click.command(
    help="Optimizes a SQL query, loading the database schema and using the OpenAI API key."
)
@click.option(
    "--schema_file",
    "-s",
    required=True,
    type=click.Path(exists=True),
    help="Path to the JSON file containing the database schema.",
)
@click.option(
    "--query",
    "-q",
    help="SQL query to optimize. If omitted, --query_file must be provided.",
)
@click.option(
    "--query_file",
    "-f",
    type=click.Path(exists=True),
    help="File containing the SQL query to optimize. Ignored if --query is provided.",
)
@click.option(
    "--openai_key",
    "-k",
    help="OpenAI API key. If omitted, it will look for the OPENAI_API_KEY environment variable.",
)
@click.option(
    "--model",
    "-m",
    default="gpt-3.5-turbo",
    help="OpenAI model to use for optimization.",
)
def optimize(schema_file, query, query_file, openai_key, model):
    # Attempt to use the provided key or fallback to the environment variable
    api_key = openai_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise click.ClickException(
            click.style(
                "OpenAI API key must be provided or set in the OPENAI_API_KEY environment variable.",
                fg="red",
            )
        )

    # Initialize the OpenAI client
    client = OpenAI(api_key=api_key)
    query_optimizer = SQLRay(client, model)

    # Load the database schema
    try:
        with open(schema_file, "r") as f:
            database_schema = json.load(f)
        query_optimizer.load_database_schema(database_schema)
    except Exception as e:
        raise click.ClickException(
            click.style(f"Failed to load database schema: {e}", fg="red")
        )

    # If query is not directly provided, try to read from file
    if not query:
        if not query_file:
            raise click.ClickException(
                click.style(
                    "Either --query or --query_file must be provided.", fg="red"
                )
            )
        try:
            with open(query_file, "r") as f:
                query = f.read()
        except Exception as e:
            raise click.ClickException(
                click.style(f"Failed to read query from file: {e}", fg="red")
            )

    # Optimize the query
    try:
        optimized_query = query_optimizer.optimize_query(query)
        click.echo(
            click.style("Optimized SQL query: ", fg="green")
            + click.style(optimized_query, fg="yellow")
        )
    except Exception as e:
        raise click.ClickException(
            click.style(f"Failed to optimize query: {e}", fg="red")
        )


@click.command(
    help="Interactive mode to load database schema and optimize SQL queries."
)
@click.option(
    "--schema_file",
    "-s",
    required=False,
    type=click.Path(exists=True),
    help="Path to the JSON file containing the database schema.",
)
def interactive(schema_file):
    click.echo(click.style("Welcome to the interactive mode.", bold=True))

    # Select the model
    model = click.prompt("Please enter the OpenAI model", default="gpt-4o")
    api_key = os.getenv("OPENAI_API_KEY") or click.prompt(
        "Please enter the OpenAI API key"
    )

    # Initialize the OpenAI client with the selected model
    client = OpenAI(api_key=api_key)
    query_optimizer = SQLRay(client, model)

    # Load the database schema
    if schema_file is None or not os.path.isfile(schema_file):
        schema_file = click.prompt(
            "Please enter the path to your database schema JSON file",
            type=click.Path(exists=True),
        )
    try:
        with open(schema_file, "r") as f:
            database_schema = json.load(f)
        query_optimizer.load_database_schema(database_schema)
        click.echo(click.style("Database schema loaded successfully.", fg="green"))
    except Exception as e:
        click.echo(click.style(f"Failed to load database schema: {e}", fg="red"))
        # Trying to load schema_file as JSON
        try:
            with open(schema_file, "r") as f:
                database_schema = json.loads(f.read())
            query_optimizer.load_database_schema(database_schema)
            click.echo(click.style("Database schema loaded successfully.", fg="green"))
        except Exception as e:
            click.echo(click.style(f"Failed to load database schema: {e}", fg="red"))
            return
        return  # Exit if schema loading fails

    # Enter the loop to accept queries
    while True:
        click.echo(
            click.style(
                "If you enter a file path, the query will be read from the file.",
                fg="yellow",
            )
        )
        query = click.prompt("Please enter your SQL query (Type 'exit' to quit)")
        if query.lower() == "exit":
            break  # Exit the loop

        # If query is a file path, load the query from the file
        if os.path.isfile(query):
            try:
                with open(query, "r") as f:
                    query = f.read()
            except Exception as e:
                click.echo(
                    click.style(f"Failed to read query from file: {e}", fg="red")
                )
                continue  # Skip to the next iteration

        # Optimize the query
        try:
            optimized_query = query_optimizer.optimize_query(query)
            click.echo(
                click.style(
                    "Run this query for creating indices: ", fg="green", bold=True
                )
            )
            for query in optimized_query["prepare_query"]:
                click.echo(query)

            click.echo(
                click.style("This is the optimized query: ", fg="green", bold=True)
            )
            click.echo(optimized_query["query"])

            click.echo(click.style("Explanation: ", fg="green", bold=True))
            click.echo(optimized_query["explanation"])
        except Exception as e:
            click.echo(click.style(f"Failed to optimize query: {e}", fg="red"))


cli.add_command(optimize)
cli.add_command(interactive)

if __name__ == "__main__":
    cli()
