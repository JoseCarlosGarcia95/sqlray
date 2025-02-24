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
    default="o1-2024-12-17",
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
    model = click.prompt("Please enter the OpenAI model", default="o1-2024-12-17")
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
        return  # Exit if schema loading fails

    # Enter the loop to accept queries
    while True:
        click.echo("\n" + click.style("Interactive SQL Query Editor", bold=True, fg="yellow"))
        click.echo(click.style("Type 'exit' to quit, or press Enter to open the editor.", fg="yellow"))

        # Preguntamos si el usuario quiere poner un fichero, salir o abrir el editor
        user_input = click.prompt("File path or 'exit' or just press Enter to open editor", default="", show_default=False)

        if user_input.strip().lower() == "exit":
            break  # Salimos del modo interactivo

        # Si el usuario ha introducido algo y es un path, tratamos de leerlo
        if user_input and os.path.isfile(user_input):
            try:
                with open(user_input, "r") as f:
                    query = f.read()
            except Exception as e:
                click.echo(click.style(f"Failed to read query from file: {e}", fg="red"))
                continue
        elif user_input.strip():
            # Si el usuario ha introducido texto que no es 'exit' ni un fichero, asumimos que es la query directa
            query = user_input
        else:
            # Si no introdujo nada, abrimos el editor
            initial_message = (
                "-- Write or modify your SQL query here.\n"
                "-- Lines starting with '--' are treated as comments.\n\n"
            )
            edited_text = click.edit(initial_message)
            if edited_text is None:
                # Significa que el usuario salió del editor sin editar (posible cancelación)
                continue
            # Si no es None, lo tomamos como la consulta
            query = edited_text.strip()
            if not query:
                continue

        # Por si el usuario vuelve a escribir 'exit' dentro del editor
        if query.lower() == "exit":
            break

        # Ahora optimizamos la consulta
        try:
            click.echo(click.style("Optimizing query...", fg="yellow"))
            optimized_query = query_optimizer.optimize_query(query)

            # Por convención en SQLRay, asumimos que 'optimized_query' puede ser un objeto con atributos
            # prepare_query (lista), query (str) y explanation (str). Ajusta según tu caso:
            click.echo(
                click.style("Run this query for creating indices: ", fg="green", bold=True)
            )
            for idx_query in optimized_query.prepare_query:
                click.echo(idx_query)

            click.echo(
                click.style("This is the optimized query: ", fg="green", bold=True)
            )
            click.echo(optimized_query.query)

            click.echo(click.style("Explanation: ", fg="green", bold=True))
            click.echo(optimized_query.explanation)

            click.echo(click.style("Score: ", fg="green", bold=True))
            click.echo(optimized_query.optimization_score)
        except Exception as e:
            click.echo(click.style(f"Failed to optimize query: {e}", fg="red"))


cli.add_command(optimize)
cli.add_command(interactive)

if __name__ == "__main__":
    cli()
