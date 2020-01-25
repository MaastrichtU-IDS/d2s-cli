import os
import click
import configparser
import fileinput
import cwltool.factory

@click.group()
def cli():
   pass

# Used for services autocompletion
def get_services_list(ctx, args, incomplete):
    return ['virtuoso', 'graphdb', 'blazegraph', 'comunica',
    'browse-local-virtuoso', 'browse-local-graphdb', 'browse-local-blazegraph', 
    'drill', 'postgres']


@cli.command()
def init():
    """Create workspace dir and download workflows examples in current dir"""
    config = configparser.ConfigParser()
    workspace = click.prompt('Enter the absolute path to the working directory. Default', default='/data/d2s-workspace')
    config['d2s'] = {'workspace': workspace}

    click.echo('[ Create ' + workspace + ' ] -- Your password might be required to set ownerships')
    os.system('sudo mkdir -p ' + workspace)
    os.system('sudo chown -R ${USER} ' + workspace)

    d2s_repository_url = click.prompt('Enter the URL to the d2s git repository to clone in the current directory. Default', default='https://github.com/MaastrichtU-IDS/d2s-transform-template.git')
    config['d2s']['url'] = d2s_repository_url

    os.system('git clone --recursive ' + d2s_repository_url + ' .')
    # Replace /data/d2s-workspace volume in docker-compose.
    with fileinput.FileInput('d2s-cwl-workflows/docker-compose.yaml', inplace=True, backup='.bck') as file:
        for line in file:
            print(line.replace('/data/d2s-workspace', workspace), end='')

    # Copy load.sh in workspace for Virtuoso bulk load
    os.system('mkdir -p ' + workspace + '/virtuoso && cp d2s-cwl-workflows/support/virtuoso/load.sh ' + workspace + '/virtuoso')
    graphdb_path = click.prompt('Enter the path to the GraphDB distribution 8.10.1 zip file used to build its image. Default', default='~/graphdb-free-8.10.1-dist.zip')
    os.system('cp ' + graphdb_path + ' ./d2s-cwl-workflows/support/graphdb')
    
    with open('.d2sconfig', 'w') as configfile:
        config.write(configfile)
    click.echo('[ Your d2s environment config has been stored in the .d2sconfig file ]')


@cli.command()
def update():
    """Update d2s docker images"""
    os.system('docker-compose -f d2s-cwl-workflows/docker-compose.yaml pull')
    os.system('docker-compose -f d2s-cwl-workflows/docker-compose.yaml build graphdb')
    click.echo('[ All images pulled and built ]')


@cli.command()
def config():
    """Show d2s configuration"""
    click.echo()
    click.echo('Configuration is stored in the .d2sconfig file')
    click.echo()
    config = configparser.ConfigParser()
    config.read('.d2sconfig')
    # print(config['local']['workspace'])
    for section_name in config.sections():
        print('[', section_name, ']')
        # print('  Options:', config.options(section_name))
        for name, value in config.items(section_name):
            print('  %s = %s' % (name, value))
    click.echo()


@cli.command()
@click.argument('services', nargs=-1, autocompletion=get_services_list)
def start(services):
    """Start services (triplestores, databases, interfaces)"""
    services_string = " ".join(services)
    print(services_string)
    os.system('docker-compose -f d2s-cwl-workflows/docker-compose.yaml up -d --force-recreate ' + services_string)
    click.echo('[ ' + services_string + ' started ]')
    if 'graphdb' in services:
        if click.confirm('Do you want to create the test repository in GraphDB?'):   
            os.system('curl -X POST http://localhost:7200/rest/repositories -F "config=@d2s-cwl-workflows/support/graphdb-test-repo-config.ttl" -H "Content-Type: multipart/form-data"')
            click.echo('Note: [ Empty reply from server ] means the repository test has been properly created')


@cli.command()
@click.argument('services', nargs=-1, autocompletion=get_services_list)
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
def status():
    """Show running services"""
    os.system('docker ps')


@cli.command()
@click.argument('workflow')
@click.argument('dataset')
def run(workflow, dataset):
    """Run CWL workflows"""
    # cwl_factory = cwltool.factory.Factory()
    # run_workflow = cwl_factory.make(workflow) # the .cwl file
    # result = run_workflow(inp=dataset)  # the config yaml
    print('Running!!')
