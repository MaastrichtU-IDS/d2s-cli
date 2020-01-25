import click
import os
import cwltool.factory

@click.group()
def cli():
   pass


@cli.command()
# @click.option(
#     '--workspace', '-w',
#     help='Path to the working directory. Default: /data/d2s-workspace',
# )
def init():
    # value = click.prompt('Please enter a number', default='/data/d2s-workspace')
    print('[ Create /data/d2s-workspace ] -- Your password might be required to set ownerships')
    os.system('sudo mkdir -p /data/d2s-workspace')
    os.system('sudo chown -R ${USER} /data/d2s-workspace')
    print('Do you want to download the template workflows and datasets?')
    if click.confirm('Do you want to continue?'):
        os.system('git clone --recursive https://github.com/MaastrichtU-IDS/d2s-transform-template.git .')
        click.echo('Template set.')
    print('[ /data/d2s-workspace created ]')

@cli.command()
def update():
    os.system('docker-compose -f d2s-cwl-workflows/docker-compose.yaml pull')
    print('All images pulled.')


@cli.command()
@click.argument('services')
# @click.option(
#     '--api-key', '-a',
#     help='your API key for the OpenWeatherMap API',
# )
def start(services):
    os.system('docker-compose --version')
    print('started!!')


@cli.command()
@click.argument('workflow')
@click.argument('dataset')
# @click.option(
#     '--api-key', '-a',
#     help='your API key for the OpenWeatherMap API',
# )
def run(workflow, dataset):
    # cwl_factory = cwltool.factory.Factory()
    # run_workflow = cwl_factory.make(workflow) # the .cwl file
    # result = run_workflow(inp=dataset)  # the config yaml
    print('started!!')

