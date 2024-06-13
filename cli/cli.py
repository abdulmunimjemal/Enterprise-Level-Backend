import click
from src.core.config import Settings
from rich.console import Console
import os


def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func

    return _add_options


_config_options = []


@click.group()
@click.option("--debug/--no-debug", default=False)
@click.pass_context
def cli(ctx, debug: bool):
    ctx.ensure_object(dict)

    ctx.obj["DEBUG"] = debug


@cli.command()
@add_options(_config_options)
@click.option("--host", default="127.0.0.1", help="Host interface to bind")
@click.option("--port", default=8000, help="Port to bind")
@click.option("--reload/--no-reload", default=False, help="Enable auto-reload")
def serve(host, port, reload):
    import uvicorn

    console = Console()
    console.log("[bold green]Starting server...[/bold green]")

    uvicorn.run("main:app", host=host, port=port, log_level="info", reload=reload)


@cli.command()
@click.pass_context
@click.option(
    "--path",
    "-p",
    help="Generate a private key at this path",
    default="./certs/privkey.pem",
)
@click.option("--size", "-s", help="Size of the key", default=2048)
def generate_privkey(_ctx, path: str, size: int):
    """
    Generate private key
    """
    click.echo("Generating a private key")
    from src.utils.encryption import generate_and_save_rsa_private_key

    if not path:
        path = "/tmp/privkey.pem"
    dir_name = os.path.dirname(path)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    click.echo(f"Generating private key at {path}")
    generate_and_save_rsa_private_key(path, size)
    click.echo(f"Private key generated at {path}")

@cli.command
@click.pass_context
@click.option("--profile", "-p", help="AWS Profile")
def deploy(_ctx, profile: str):
    """
    Deploy the application to AWS
    """
    import subprocess
    click.echo("Deploying the application to AWS")
    p = subprocess.Popen(["cdk", "deploy", "./deploy", "--profile", profile], cwd="deploy")
    p.wait
    


if __name__ == "__main__":
    cli()
