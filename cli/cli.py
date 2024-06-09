import click

@click.group()
@click.option('--debug/--no-debug', default=False)
@click.pass_context
def cli(ctx, debug: bool):
    ctx.ensure_object(dict)

    ctx.obj['DEBUG'] = debug

@cli.command()
@click.pass_context
@click.option('--path', '-p', help='Generate a private key at this path', default="./certs/privkey.pem")
@click.option('--size', '-s', help='Size of the key', default=2048)
def generate_privkey(_ctx, path: str, size: int):
    """
    Generate private key
    """
    click.echo('Generating a private key')
    from pybe.core.utils.encryption import generate_and_save_rsa_private_key
    if not path:
        path = '/tmp/privkey.pem'
    click.echo(f'Generating private key at {path}')
    generate_and_save_rsa_private_key(path, size)
    click.echo(f'Private key generated at {path}')