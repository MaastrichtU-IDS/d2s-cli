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
    workspace = click.prompt('Enter the absolute path to the working directory. Default', default='/data/d2s-workspace')
    os.system('echo "' + workspace + '" > .d2s')
    click.echo('[ Create ' + workspace + ' ] -- Your password might be required to set ownerships')
    os.system('sudo mkdir -p ' + workspace)
    os.system('sudo chown -R ${USER} ' + workspace)
    if click.confirm('Do you want to download the template workflows and datasets?'):
        os.system('git clone --recursive https://github.com/MaastrichtU-IDS/d2s-transform-template.git .')
    click.echo('[ Your Data2Services environment has been stored in the .d2s file ]')

@cli.command()
def update():
    os.system('docker-compose -f d2s-cwl-workflows/docker-compose.yaml pull')
    click.echo('All images pulled.')


@cli.command()
@click.argument('services', nargs=-1)
# @click.option(
#     '--api-key', '-a',
#     help='your API key for the OpenWeatherMap API',
# )
def start(services):
    for service in services:
        click.echo(service)
    # os.system('docker-compose -f d2s-cwl-workflows/docker-compose.yaml up -d --build --force-recreate virtuoso drill graphdb browse-local-virtuoso browse-local-graphdb')
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

