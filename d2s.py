import os
import click
import configparser
import fileinput
import cwltool.factory
import cwltool.context

@click.group()
def cli():
   pass

# Used for autocompletion
def get_services_list(ctx, args, incomplete):
    return ['virtuoso', 'graphdb', 'blazegraph', 'comunica',
    'browse-local-virtuoso', 'browse-local-graphdb', 'browse-local-blazegraph', 
    'drill', 'postgres']
def get_datasets_list(ctx, args, incomplete):
    return os.listdir("./datasets")
def get_workflows_list(ctx, args, incomplete):
    return os.listdir("./d2s-cwl-workflows/workflows")

@cli.command()
def init():
    """Create workspace dir and download workflows examples in current dir"""
    config = configparser.ConfigParser()
    workspace = click.prompt('Enter the absolute path to the working directory (for workflow processing files). Default', default='/data/d2s-workspace')
    config['d2s'] = {'workspace': workspace}
    click.echo()
    click.echo('[ Create ' + workspace + ' ] -- Your password might be required to set ownerships.')
    click.echo()
    os.system('sudo mkdir -p ' + workspace + '/output/tmp-outdir')
    os.system('sudo chown -R ${USER} ' + workspace)

    d2s_repository_url = click.prompt('Enter the URL of the d2s git repository to clone in the current directory. Default', default='https://github.com/MaastrichtU-IDS/d2s-transform-template.git')
    config['d2s']['url'] = d2s_repository_url

    os.system('git clone --recursive ' + d2s_repository_url + ' .')
    if not os.path.exists('./d2s-cwl-workflows'):
        os.system('git submodule add --recursive https://github.com/MaastrichtU-IDS/d2s-cwl-workflows.git')

    # Replace /data/d2s-workspace volume in docker-compose.
    with fileinput.FileInput('d2s-cwl-workflows/docker-compose.yaml', inplace=True, backup='.bck') as file:
        for line in file:
            print(line.replace('/data/d2s-workspace', workspace), end='')

    # Copy load.sh in workspace for Virtuoso bulk load
    os.system('mkdir -p ' + workspace + '/virtuoso && cp d2s-cwl-workflows/support/virtuoso/load.sh ' + workspace + '/virtuoso')

    # Copy GraphDB zip file to the right folder in d2s-cwl-workflows
    click.echo()
    click.echo('[ Download GraphDB version 8.10.1 zip file at  https://ontotext.com/products/graphdb/ ]')
    click.echo()
    graphdb_path = click.prompt('Enter the path to the GraphDB distribution 8.10.1 zip file used to build its image. Default', default='~/graphdb-free-8.10.1-dist.zip')
    os.system('cp ' + graphdb_path + ' ./d2s-cwl-workflows/support/graphdb')
    
    with open('.d2sconfig', 'w') as configfile:
        config.write(configfile)
    
    click.echo()
    click.echo('[ Your d2s project has been created! ]')
    click.echo('[ The project configuration is stored in the .d2sconfig file ]')
    click.echo()
    click.echo('[ You can now run `d2s update` to pull and build all images ]')


@cli.command()
def update():
    """Update d2s docker images"""
    os.system('docker-compose -f d2s-cwl-workflows/docker-compose.yaml pull')
    os.system('docker-compose -f d2s-cwl-workflows/docker-compose.yaml build graphdb')
    click.echo('[ All images pulled and built ]')
    click.echo()
    click.echo('[ You can now run `d2s start virtuoso graphdb` to start virtuoso and graphdb triplestores ]')


@cli.command()
def config():
    """Show d2s configuration"""
    click.echo()
    click.echo('Configuration is stored in the .d2sconfig file')
    click.echo()
    config = configparser.ConfigParser()
    config.read('.d2sconfig')
    # print(config['d2s']['workspace'])
    for section_name in config.sections():
        click.echo('[' + section_name + ']')
        # print('  Options:', config.options(section_name))
        for name, value in config.items(section_name):
            click.echo('  %s = %s' % (name, value))
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
    click.echo()
    click.echo('[ You can now run `d2s download drugbank` to download drugbank sample data to run a first workflow ]')


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
def services():
    """List running services"""
    os.system('docker ps --format="table {{.Names}}\t{{.Ports}}\t{{.Status}}\t{{.Networks}}"')


@cli.command()
@click.argument('datasets', nargs=-1, autocompletion=get_datasets_list)
def download(datasets):
    """Download a dataset to be processed running CWL workflows"""
    config = configparser.ConfigParser()
    config.read('.d2sconfig')
    workspace = config['d2s']['workspace']
    for dataset in datasets:
        os.system('docker run -it -v $(pwd):/srv \
            -v ' + workspace + ':/data \
            umids/d2s-bash-exec:latest \
            /srv/datasets/' + dataset + '/download/download.sh input/' + dataset)
        print('[ ' + dataset + ' downloaded ]')
    click.echo()
    click.echo('[ Datasets downloaded in ' + workspace + '/input/$dataset_id ]')
    click.echo('[ You can now run `d2s run workflow-xml.cwl drugbank` to run drugbank transformation workflow ]')

@cli.command()
@click.argument('workflow', autocompletion=get_workflows_list)
@click.argument('dataset', autocompletion=get_datasets_list)
def run(workflow, dataset):
    """Run CWL workflows (defined in datasets/*/config.yaml)"""
    config = configparser.ConfigParser()
    config.read('.d2sconfig')
    workspace = config['d2s']['workspace']
    cwl_workflow_path = 'd2s-cwl-workflows/workflows/' + workflow
    dataset_config_path = 'datasets/' + dataset + '/config.yml'
    
    cwl_command = 'cwl-runner --custom-net d2s-cwl-workflows_network --outdir {0}/output --tmp-outdir-prefix={0}/output/tmp-outdir/ --tmpdir-prefix={0}/output/tmp-outdir/tmp- {1} {2}'.format(workspace,cwl_workflow_path,dataset_config_path)
    
    os.system(cwl_command)
    click.echo()
    click.echo('[ Browse the file generated by the workflow in ' + workspace + '/output/ ' + dataset + ' ]')
    click.echo('[ Access the linked data browser for Virtuoso at http://localhost:8891 ]')
    click.echo('[ Access Virtuoso (temp store) at http://localhost:8890 ]')
    click.echo('[ Access the linked data browser for GraphDB at http://localhost:7201 ]')
    click.echo('[ Access GraphDB at http://localhost:7200 ]')

    # Loading the datatset config.yml file don't work
    # dataset_config_file = open('datasets/' + dataset + '/config.yml', 'r')
    # # Define cwl-runner workspace
    # runtime_context = cwltool.context.RuntimeContext()
    # runtime_context.custom_net = 'd2s-cwl-workflows_network'
    # runtime_context.outdir = workspace + '/output'
    # runtime_context.tmp_outdir_prefix = workspace + '/output/tmp-outdir/'
    # runtime_context.tmpdir_prefix = workspace + '/output/tmp-outdir/tmp-'
    # cwl_factory = cwltool.factory.Factory(runtime_context=runtime_context)
    # # Run CWL workflow
    # run_workflow = cwl_factory.make(cwl_workflow_path) # the .cwl file
    # result = run_workflow(inp=dataset_config_file.read())  # the config yaml
    # print('Running!')
    # print(result)
