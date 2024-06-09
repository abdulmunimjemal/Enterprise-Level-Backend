import click
from src.config import Settings
from rich.console import Console
import os


##################
# Config
##################
def load_config_yaml(ctx, param, value) -> Settings:
    return Settings.load_config_yaml(value.name)


def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func

    return _add_options


_config_options = [
    click.option(
        "--config",
        default="pybe_config.yaml",
        help="Configuration file",
        type=click.File(mode="r"),
        callback=load_config_yaml,
    )
]


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
def serve(config: Settings, host, port, reload):
    import uvicorn
    from src.main import create_app

    console = Console()
    console.log("[bold green]Starting server...[/bold]")
    app = create_app(config)
    uvicorn.run(app, host=host, port=port, log_level="info", reload=reload)


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


if __name__ == "__main__":
    cli()
