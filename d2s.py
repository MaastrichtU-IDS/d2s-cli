import os
import click
import configparser
import datetime
import time
import urllib.request
import fileinput
import cwltool.factory
import cwltool.context

@click.group()
def cli():
   pass

# Start of the docker-compose using d2s-cwl-workflows yaml
docker_compose_cmd = 'docker-compose -f d2s-cwl-workflows/docker-compose.yaml '

# Used for autocompletion
def get_services_list(ctx, args, incomplete):
    # TODO: automate by parsing the docker-compose.yaml
    return filter(lambda x: x.startswith(incomplete), [ 'demo',
    'graphdb', 'virtuoso', 'tmp-virtuoso', 'blazegraph', 'allegrograph', 'anzograph',
    'into-the-graph', 'ldf-server', 'comunica', 'notebook',
    'api', 'drill', 'postgres', 'proxy', 'filebrowser', 'rmlstreamer', 'rmltask' ])
def get_datasets_list(ctx, args, incomplete):
    return filter(lambda x: x.startswith(incomplete), os.listdir("./datasets"))
def get_workflows_list(ctx, args, incomplete):
    return filter(lambda x: x.startswith(incomplete), os.listdir("./d2s-cwl-workflows/workflows"))
def get_workflow_history(ctx, args, incomplete):
    # Sorted from latest to oldest
    files = list(filter(lambda x: x.startswith(incomplete), os.listdir("./workspace/workflow-history")))
    return sorted(files, key=lambda x: os.path.getmtime("./workspace/workflow-history/" + x), reverse=True)
def get_running_workflows(ctx, args, incomplete):
    # Only show workflow logs that have been modified in the last 2 minutes
    # TODO: Will not work for workflow with SPARQL queries longer than 2 minutes
    files = filter(lambda x: x.startswith(incomplete), os.listdir("./workspace/workflow-history"))
    return filter(lambda x: datetime.datetime.fromtimestamp(os.path.getmtime("./workspace/workflow-history/" + x)) > (datetime.datetime.now() - datetime.timedelta(minutes=2)), files)
def get_running_processes(ctx, args, incomplete):
    # Show running processes to be stopped
    return [os.system("ps ax | grep -v time | grep '[c]wl-runner' | awk '{print $1}'")]

@cli.command()
@click.argument('projectname', nargs=1)
@click.pass_context
def init(ctx, projectname):
    """Initialize a project in the provided folder name"""
    # if os.path.exists('.d2sconfig'):
    if os.path.exists(projectname):
        click.echo(click.style('[d2s]', bold=True) + ' The folder ' + click.style(projectname, bold=True) 
            + ' already exists.', err=True)
        return

    config = configparser.ConfigParser()
    config['d2s'] = {}
    # os.system('echo "UID=$UID" > .env')
    # os.system('echo "GID=$GID" >> .env')

    click.echo(click.style('[d2s] ', bold=True) + 'You can generate a new project on GitHub using the provided template:')
    click.secho('https://github.com/MaastrichtU-IDS/d2s-transform-template/generate', bold=True)
    click.echo(click.style('[d2s] ', bold=True) + 'Or use the default template repository.')
    d2s_repository_url = click.prompt(click.style('[?]', bold=True) + ' Enter the URL of the d2s git repository to clone in the current directory. Default', default='https://github.com/MaastrichtU-IDS/d2s-transform-template.git')
    config['d2s']['url'] = d2s_repository_url
    click.echo(click.style('[d2s] ', bold=True) + 'Cloning the repository in ' + projectname + '...')

    os.system('git clone --quiet --recursive ' + d2s_repository_url + ' ' + projectname)
    os.chdir(projectname)
    click.echo(click.style('[d2s]', bold=True) + ' Git repository cloned.')
    if not os.path.exists('./d2s-cwl-workflows'):
        os.system('git submodule add --recursive https://github.com/MaastrichtU-IDS/d2s-cwl-workflows.git')

    # Create workspace directories
    os.system('mkdir -p workspace/output/tmp-outdir')
    os.system('mkdir -p workspace/graphdb-import')
    os.system('chmod -R 777 workspace/graphdb-import')
    os.system('mkdir -p workspace/workflow-history')
    os.system('mkdir -p workspace/download/releases/1')
    click.echo(click.style('[d2s]', bold=True) + ' Downloading RMLStreamer.jar... [80M]')
    urllib.request.urlretrieve ("https://github.com/vemonet/RMLStreamer/raw/fix-mainclass/target/RMLStreamer-1.2.2.jar", "workspace/RMLStreamer.jar")
    # os.system('wget -a workspace/RMLStreamer.jar https://github.com/vemonet/RMLStreamer/raw/fix-mainclass/target/RMLStreamer-1.2.2.jar')
    os.system('chmod +x workspace/RMLStreamer.jar')

    # Copy load.sh in workspace for Virtuoso bulk load
    os.system('mkdir -p workspace/virtuoso && cp d2s-cwl-workflows/support/virtuoso/load.sh workspace/virtuoso')
    os.system('mkdir -p workspace/tmp-virtuoso && cp d2s-cwl-workflows/support/virtuoso/load.sh workspace/tmp-virtuoso')
    # TODO: improve this to include it in Docker deployment

    click.echo()
    # Copy GraphDB zip file to the right folder in d2s-cwl-workflows
    click.echo(click.style('[d2s]', bold=True) + ' The GraphDB triplestore needs to be downloaded for licensing reason.\n'
        + 'Go to ' 
        + click.style('https://ontotext.com/products/graphdb/', bold=True) 
        + ' and provide your email to receive the URL to download ' + click.style('GraphDB version 9.1.1 standalone zip', bold=True))
    
    graphdb_path = click.prompt(click.style('[?]', bold=True) + ' Enter the path to the GraphDB distribution 9.1.1 zip file used to build the Docker image. Default', default='~/graphdb-free-9.1.1-dist.zip')
    os.system('cp ' + graphdb_path + ' ./d2s-cwl-workflows/support/graphdb')
    
    with open('.d2sconfig', 'w') as configfile:
        config.write(configfile)
    
    click.echo()
    click.echo(click.style('[d2s]', bold=True) + ' Your d2s project has been created!')
    click.echo(click.style('[d2s]', bold=True) + ' The project configuration is stored in the ' 
        + click.style('.d2sconfig', bold=True) + ' file')
    click.secho('cd ' + projectname, bold=True)
    click.secho('d2s start demo', bold=True)
    # click.secho('d2s update', bold=True)
    # Execute update directly:
    # click.echo(click.style('[d2s]', bold=True) + ' Running ' + click.style('d2s update', bold=True) + '...')
    # ctx.invoke(update)


@cli.command()
def update():
    """Update Docker images"""
    os.system(docker_compose_cmd + 'pull')
    os.system(docker_compose_cmd + 'build graphdb')
    click.echo(click.style('[d2s]', bold=True) + ' All images pulled and built.')
    click.echo(click.style('[d2s]', bold=True) + ' You can now start services (e.g. demo services):')
    click.secho('d2s start demo', bold=True)


@cli.command()
def config():
    """Show the project configuration"""
    click.echo(click.style('[d2s]', bold=True) + ' Configuration is stored in the ' 
        + click.style('.d2sconfig', bold=True) + ' file:')
    click.echo()
    config = configparser.ConfigParser()
    config.read('.d2sconfig')
    # print(config['d2s']['url'])
    for section_name in config.sections():
        click.secho('[' + section_name + ']', bold=True)
        # print('  Options:', config.options(section_name))
        for name, value in config.items(section_name):
            click.echo('  ' + name + ' = ' + click.style(value, bold=True))


@cli.command()
@click.argument('services', nargs=-1, autocompletion=get_services_list)
@click.option(
    '-d', '--deploy', default='', 
    help='Use custom deployment config')
def start(services, deploy):
    """Start services"""
    if services[0] == "demo":
        deploy = "demo"
        services_string = "graphdb tmp-virtuoso drill api into-the-graph"
        click.echo(click.style('[d2s] ', bold=True) + ' Starting the services for the demo: ' + services_string)
    else:
        services_string = " ".join(services)
    
    # Run docker-compose:
    if deploy:
        os.system(docker_compose_cmd + '-f d2s-cwl-workflows/docker-compose.'
        + deploy + '.yaml up -d --force-recreate ' + services_string)
    else:
        os.system(docker_compose_cmd + 'up -d --force-recreate ' + services_string)

    # Ask user to create the GraphDB test repository
    click.echo(click.style('[d2s] ', bold=True) + services_string + ' started.')
    if 'graphdb' in services or 'demo' in services:
        if click.confirm(click.style('[?]', bold=True) + ' Do you want to create the ' 
        + click.style('demo repository', bold=True) + ' in GraphDB?'):
            click.echo(click.style('[d2s] ', bold=True) 
                + 'Creating the repository, it should take about 20s.')
            time.sleep(10)
            os.system('curl -X POST http://localhost:7200/rest/repositories -F "config=@d2s-cwl-workflows/support/graphdb-repo-config.ttl" -H "Content-Type: multipart/form-data"')
    click.echo()
    click.echo(click.style('[d2s]', bold=True) 
        + ' You can now download data to run a first workflow:')
    click.secho('d2s download', bold=True)


@cli.command()
@click.argument('services', nargs=-1, autocompletion=get_services_list)
@click.option(
    '--all/--no-all', default=False, 
    help='Stop all services')
def stop(services, all):
    """Stop services (--all to stop all services)"""
    if all:
        os.system(docker_compose_cmd + 'down')
        os.system('sudo rm -rf workspace/virtuoso')
        click.echo(click.style('[d2s] ', bold=True) + 'All services stopped.')
    else:
        services_string = " ".join(services)
        os.system(docker_compose_cmd + 'stop ' + services_string)
        click.echo(click.style('[d2s] ', bold=True) + services_string + ' stopped.')


@cli.command()
def services():
    """List running services"""
    os.system('docker ps --format="table {{.Names}}\t{{.Ports}}\t{{.Status}}\t{{.Networks}}"')


@cli.command()
def process_running():
    """List running workflows processes"""
    os.system('echo "PID    CPU  Mem Start    Command"')
    os.system('ps ax -o pid,%cpu,%mem,start,command | grep -v time | grep "[c]wl-runner"')

@cli.command()
@click.argument('process', autocompletion=get_running_processes)
def process_stop(process):
    """Stop a running workflows process"""
    if (process == "0"):
        click.echo(click.style('[d2s] ', bold=True) + 'No process to stop.')
    else:
        os.system('kill -9 ' + process)
        click.echo(click.style('[d2s] ', bold=True) + 'Process ' + click.style(process, bold=True) + ' stopped.')


@cli.command()
@click.argument('workflow', autocompletion=get_running_workflows)
def watch(workflow):
    """Watch running workflow"""
    os.system('watch tail -n 30 workspace/workflow-history/' + workflow)


@cli.command()
@click.argument('workflow', autocompletion=get_workflow_history)
def log(workflow):
    """Display logs of a workflow"""
    os.system('less +G workspace/workflow-history/' + workflow)

@cli.command()
@click.argument('datasets', nargs=-1, autocompletion=get_datasets_list)
def download(datasets):
    """Download a dataset to be processed"""
    start_time = datetime.datetime.now()
    for dataset in datasets:
        os.system('docker run -it -v $PWD:/srv \
            umids/d2s-bash-exec:latest \
            /srv/datasets/' + dataset + '/download/download.sh workspace/input/' + dataset)
        click.echo(click.style('[d2s] ' + dataset, bold=True) + ' dataset downloaded at ' 
        + click.style('workspace/input/' + dataset, bold=True))
    run_time = datetime.datetime.now() - start_time
    click.echo(click.style('[d2s] ', bold=True) 
            + 'Datasets downloaded in: '
            + click.style(str(datetime.timedelta(seconds=run_time.total_seconds())), bold=True))
    click.echo()
    click.echo(click.style('[d2s]', bold=True) + ' You can now run the transformation workflow:')
    click.secho('d2s run', bold=True)

@cli.command()
@click.argument('dataset', autocompletion=get_datasets_list)
# @click.option(
#     '-p', '--parallelism', default='8', # Not working properly.
#     help='Run in parallel, depends on Task Slots availables')
def rml(dataset):
    """Run RML Streamer"""
    click.echo(click.style('[d2s]', bold=True) + ' Execute mappings from ' 
        + click.style('datasets/' + dataset + '/mapping/rml-mappings.ttl', bold=True))
    rmlstreamer_cmd = 'docker exec -d d2s-cwl-workflows_rmlstreamer_1 /opt/flink/bin/flink run /mnt/workspace/RMLStreamer.jar --path /mnt/datasets/' + dataset + '/mapping/rml-mappings.ttl --outputPath /mnt/workspace/graphdb-import/rml-output-' + dataset + '.nt --job-name "[d2s] RMLStreamer dataset ' + dataset + '"'
    # rmlstreamer_cmd = docker_compose_cmd + 'exec -d rmlstreamer /opt/flink/bin/flink run /mnt/workspace/RMLStreamer.jar --path /mnt/datasets/' + dataset + '/mapping/rml-mappings.ttl --outputPath /mnt/workspace/graphdb-import/rml-output-' + dataset + '.nt --job-name "[d2s] RMLStreamer dataset ' + dataset + '"'
    # print(rmlstreamer_cmd)
    os.system(rmlstreamer_cmd)
    click.echo(click.style('[d2s]', bold=True) + ' Check the job running at ' 
        + click.style('http://localhost:8078/#/job/running', bold=True))
    click.echo(click.style('[d2s]', bold=True) + ' Output file in ' 
        + click.style("workspace/graphdb-import/rml-output-" + dataset + ".nt", bold=True))

@cli.command()
@click.argument('workflow', autocompletion=get_workflows_list)
@click.argument('dataset', autocompletion=get_datasets_list)
@click.option(
    '--get-mappings/--no-copy', default=False, 
    help='Copy the mappings generated by the workflow to our datasets folder')
@click.option(
    '--detached/--watch', default=True, 
    help='Run in detached mode or watch workflow')
def run(workflow, dataset, get_mappings, detached):
    """Run CWL workflows"""
    start_time = datetime.datetime.now()
    config = configparser.ConfigParser()
    config.read('.d2sconfig')
    cwl_workflow_path = 'd2s-cwl-workflows/workflows/' + workflow
    dataset_config_path = 'datasets/' + dataset + '/config.yml'

    # TODO: Trying to fix issue where virtuoso bulk load only the first dataset we run
    # It needs restart to work a second time
    click.echo(click.style('[d2s] ', bold=True) 
        + 'Restart tmp Virtuoso and delete file in '
        + click.style('workspace/output', bold=True))
    os.system(docker_compose_cmd + 'stop tmp-virtuoso')
    os.system(docker_compose_cmd + 'up -d --force-recreate tmp-virtuoso')
    # TODO: fix this dirty Virtuoso deployment 
    # Virtuoso unable to handle successive bulk load + permission issues + load.sh in the virtuoso containers
    # I don't know how, they managed to not put it in the container... They had one job...

    # Delete previous output (not archived)
    os.system('rm -r workspace/output/*')
    os.system('rm -r workspace/tmp-virtuoso/*.nq')
    # Make sure the load.sh script is in the tmp Virtuoso folder
    os.system('sudo chmod -R 777 workspace/tmp-virtuoso')
    os.system('mkdir -p workspace/tmp-virtuoso && cp d2s-cwl-workflows/support/virtuoso/load.sh workspace/tmp-virtuoso')
    
    if (detached):
        cwl_command = 'nohup time '
    else:
        cwl_command = ''
    cwl_command = cwl_command +'cwl-runner --custom-net d2s-cwl-workflows_network --outdir {0}/output --tmp-outdir-prefix={0}/output/tmp-outdir/ --tmpdir-prefix={0}/output/tmp-outdir/tmp- {1} {2}'.format('workspace',cwl_workflow_path,dataset_config_path)
    if (detached):
        log_filename = workflow + '-' + dataset + '-' + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + '.txt'
        cwl_command = cwl_command + ' > workspace/workflow-history/' + log_filename + ' &'
    click.echo()
    click.echo(click.style('[d2s] ', bold=True) 
        + 'Running CWL worklow...')
    click.echo(cwl_command)
    os.system(cwl_command)

    # Copy mappings generated by the workflow to datasets folder
    if (get_mappings):
        os.system('cp workspace/output/sparql_mapping_templates/* datasets/' 
        + dataset + '/mapping/')
        click.echo()
        click.echo(click.style('[d2s] ', bold=True) 
            + 'Browse the generated mappings files in '
            + click.style('datasets/' + dataset + '/mapping', bold=True))
    else:
        click.echo()
        click.echo(click.style('[d2s] ', bold=True) + 'Browse the file generated by the workflow in ' 
            + click.style('workspace/output/' + dataset, bold=True))
        # click.echo(click.style('[d2s] ', bold=True)
        #     + 'Access the linked data browser for Virtuoso at '
        #     + click.style('http://localhost:8891', bold=True))
        # click.echo(click.style('[d2s] ', bold=True)
        #     + 'Access Virtuoso (temp store) at '
        #     + click.style('http://localhost:8890', bold=True))
        # click.echo(click.style('[d2s] ', bold=True) 
        #     + 'Access the linked data browser for GraphDB at '
        #     + click.style('http://localhost:7201', bold=True))
        # click.echo(click.style('[d2s] ', bold=True) 
        #     + 'Access GraphDB at '
        #     + click.style('http://localhost:7200', bold=True))
    if (detached):
        click.echo()
        click.echo(click.style('[d2s] ', bold=True) 
            + 'Watch your workflow running: ')
        click.secho('d2s watch ' + log_filename, bold=True)
        click.echo(click.style('[d2s] ', bold=True) 
            + 'Or display the complete workflow logs: ')
        click.secho('d2s log ' + log_filename, bold=True)
    else:
        run_time = datetime.datetime.now() - start_time
        click.echo(click.style('[d2s] ', bold=True) 
                + 'Workflow runtime: '
                + click.style(str(datetime.timedelta(seconds=run_time.total_seconds())), bold=True))

    ## Trying to run using CWL Python library don't work
    # Loading the dataset config.yml file fails
    # dataset_config_file = open('datasets/' + dataset + '/config.yml', 'r')
    # # Define cwl-runner workspace
    # runtime_context = cwltool.context.RuntimeContext()
    # runtime_context.custom_net = 'd2s-cwl-workflows_network'
    # runtime_context.outdir = 'workspace/output'
    # runtime_context.tmp_outdir_prefix = 'workspace/output/tmp-outdir/'
    # runtime_context.tmpdir_prefix = 'workspace/output/tmp-outdir/tmp-'
    # cwl_factory = cwltool.factory.Factory(runtime_context=runtime_context)
    # # Run CWL workflow
    # run_workflow = cwl_factory.make(cwl_workflow_path) # the .cwl file
    # result = run_workflow(inp=dataset_config_file.read())  # the config yaml
    # print('Running!')
    # print(result)


@cli.group()
def generate():
    """Generate new datasets, workflows, tools"""
    pass

@generate.command()
def dataset():
    """Create a new dataset from template in datasets folder"""
    # Automatically fill data about the workflow (git repo URL of mappings)
    # TODO: make it an array of obj
    dataset_id = click.prompt(click.style('[?]', bold=True) 
        + ' Enter the identifier of your datasets, e.g. wikipathways (lowercase, no space or weird characters)')
    dataset_name = click.prompt(click.style('[?]', bold=True) 
        + ' Enter a human-readable name for your datasets, e.g. WikiPathways')
    dataset_description = click.prompt(click.style('[?]', bold=True) 
        + ' Enter a description for this dataset')
    publisher_name = click.prompt(click.style('[?]', bold=True) 
        + ' Enter complete name for the institutions publishing the data and its affiliation, e.g. Institute of Data Science at Maastricht University')
    publisher_url = click.prompt(click.style('[?]', bold=True) 
        + ' Enter a valid URL for the publisher homepage. Default', 
        default='https://maastrichtuniversity.nl/ids')
    source_license = click.prompt(click.style('[?]', bold=True) 
        + ' Enter a valid URL to the license informations about the original dataset. Default', 
        default='http://creativecommons.org/licenses/by-nc/4.0/legalcode')
    rdf_license = click.prompt(click.style('[?]', bold=True) 
        + ' Enter a valid URL to the license informations about the RDF distribution of the dataset. Default', 
        default='http://creativecommons.org/licenses/by-nc/4.0/legalcode')

    dataset_folder_path = 'datasets/' + dataset_id
    os.system('cp -r d2s-cwl-workflows/support/template/dataset ' + dataset_folder_path)
    
    for dname, dirs, files in os.walk(dataset_folder_path):
        for fname in files:
            fpath = os.path.join(dname, fname)
            with open(fpath) as f:
                file_content = f.read()
            file_content = file_content.replace("$dataset_id", dataset_id).replace("$dataset_name", dataset_name).replace("$dataset_description", dataset_description)
            file_content = file_content.replace("$publisher_name", publisher_name).replace("$publisher_url", publisher_url)
            file_content = file_content.replace("$source_license", source_license).replace("$rdf_license", rdf_license)
            with open(fpath, "w") as f:
                f.write(file_content)
    click.echo()
    click.echo(click.style('[d2s]', bold=True) + ' The config, metadata and mapping files for the ' 
        + click.style(dataset_id + ' dataset', bold=True) 
        + ' has been generated')
    click.echo(click.style('[d2s]', bold=True) + ' Start edit them in ' + click.style('datasets/' + dataset_id, bold=True))
    if click.confirm(click.style('[?]', bold=True) + ' Do you want to open the ' 
        + click.style('download', bold=True) + ' file to edit it?'):
        os.system('nano ' + dataset_folder_path + '/download/download.sh')

    