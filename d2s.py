import click
import os
import configparser
import cwltool.factory

@click.group()
def cli():
   pass


@cli.command()
def init():
    """Create workspace dir and download workflows examples in current dir"""
    config = configparser.ConfigParser()
    workspace = click.prompt('Enter the absolute path to the working directory. Default', default='/data/d2s-workspace')
    config['local'] = {'Workspace': workspace}

    click.echo('[ Create ' + workspace + ' ] -- Your password might be required to set ownerships')
    os.system('sudo mkdir -p ' + workspace)
    os.system('sudo chown -R ${USER} ' + workspace)

    if click.confirm('Do you want to download the template workflows and datasets?'):
        os.system('git clone --recursive https://github.com/MaastrichtU-IDS/d2s-transform-template.git .')
        # Remove link to the GitHub repo and create new repo?
        # os.system('rm -rf .git && git init && git add . && git commit -m "d2s init"')
    
    with open('.d2sconfig', 'w') as configfile:
        config.write(configfile)
    click.echo('[ Your d2s environment config has been stored in the .d2sconfig file ]')

@cli.command()
def update():
    """Update Data2Services docker images"""
    os.system('docker-compose -f d2s-cwl-workflows/docker-compose.yaml pull')
    click.echo('All images pulled.')


@cli.command()
@click.argument('services', nargs=-1)
def start(services):
    """Start services (databases, interfaces)"""
    # for service in services:
    #     click.echo(service)
    services_string = " ".join(services)
    print(services_string)
    os.system('docker-compose -f d2s-cwl-workflows/docker-compose.yaml up -d --build --force-recreate ' + services_string)
    click.echo('[ ' + services_string + ' started ]')


@cli.command()
@click.argument('services', nargs=-1)
@click.option(
    '--all/--no-all', default=False, 
    help='Stop all services')
def stop(services, all):
    """Stop services (--all to stop all services)"""
    if all:
        os.system('docker-compose -f d2s-cwl-workflows/docker-compose.yaml down')
        click.echo('[ All services stopped ]')
    else:
        services_string = " ".join(services)
        os.system('docker-compose -f d2s-cwl-workflows/docker-compose.yaml stop ' + services_string)
        click.echo('[ ' + services_string + ' stopped ]')


@cli.command()
@click.argument('workflow')
@click.argument('dataset')
def run(workflow, dataset):
    """Run CWL workflows"""
    # cwl_factory = cwltool.factory.Factory()
    # run_workflow = cwl_factory.make(workflow) # the .cwl file
    # result = run_workflow(inp=dataset)  # the config yaml
    print('Running!!')

