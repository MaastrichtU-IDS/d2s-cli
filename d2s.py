import os, sys, stat
from pathlib import Path
import shutil
import glob
import click
import subprocess
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

# Start of the docker-compose using d2s-core yml
docker_compose_cmd = 'docker-compose -f d2s-core/docker-compose.yml '

# Used for autocompletion
def get_services_list(ctx, args, incomplete):
    # TODO: automate by parsing the docker-compose.yml
    return filter(lambda x: x.startswith(incomplete), [ 'demo',
    'graphdb', 'graphdb-ee', 'virtuoso', 'tmp-virtuoso', 'blazegraph', 'allegrograph', 'anzograph', 'fuseki',
    'notebook', 'spark-notebook', 'into-the-graph', 'ldf-server', 'comunica', 'biothings-studio', 'docket',
    'api', 'drill', 'postgres', 'proxy', 'filebrowser', 'rmlstreamer', 'rmltask',
    'limes-server', 'mapeathor', 'neo4j', 'nanobench', 'fairdatapoint' ])
def get_datasets_list(ctx, args, incomplete):
    return filter(lambda x: x.startswith(incomplete), os.listdir("./datasets"))
def get_workflows_list(ctx, args, incomplete):
    return filter(lambda x: x.startswith(incomplete), os.listdir("./d2s-core/cwl/workflows"))
def get_workflow_history(ctx, args, incomplete):
    # Sorted from latest to oldest
    files = list(filter(lambda x: x.startswith(incomplete), os.listdir("./workspace/logs")))
    return sorted(files, key=lambda x: os.path.getmtime("./workspace/logs/" + x), reverse=True)
def get_running_workflows(ctx, args, incomplete):
    # Only show workflow logs that have been modified in the last 2 minutes
    # TODO: Will not work for workflow with SPARQL queries longer than 2 minutes
    files = filter(lambda x: x.startswith(incomplete), os.listdir("./workspace/logs"))
    return filter(lambda x: datetime.datetime.fromtimestamp(os.path.getmtime("./workspace/logs/" + x)) > (datetime.datetime.now() - datetime.timedelta(minutes=2)), files)
def get_running_processes(ctx, args, incomplete):
    # Show running processes to be stopped
    return [os.system("ps ax | grep '[c]wl-runner' | awk '{print $1}'")]

# Change permissions to 777 recursively. 
# See https://stackoverflow.com/questions/16249440/changing-file-permission-in-python
def chmod777(path):
    for dirpath, dirnames, filenames in os.walk(path):
        # Handle permissions errors
        try:
            os.chmod(dirpath, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            # os.chmod(dirpath, 0o777)
            shutil.chown(dirpath, user=os.getuid(), group=os.getgid())
        except:
            click.echo(click.style('[d2s]', bold=True) + ' Issue while updating permissions for ' + dirpath + '.')
        
        for filename in filenames:
            try:
                os.chmod(os.path.join(dirpath, filename), stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                shutil.chown(os.path.join(dirpath, filename), user=os.getuid(), group=os.getgid())
            except:
                click.echo(click.style('[d2s]', bold=True) + ' Issue while updating permissions for ' + os.path.join(dirpath, filename))

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
    config['d2s']['path'] = os.getcwd() + '/' + projectname

    click.echo(click.style('[d2s] ', bold=True) + 'You can generate a new project on GitHub using the provided template:')
    click.secho('https://github.com/MaastrichtU-IDS/d2s-project-template/generate', bold=True)
    click.echo(click.style('[d2s] ', bold=True) + 'Or use the default template repository.')
    d2s_repository_url = click.prompt(click.style('[?]', bold=True) + ' Enter the URL of the d2s git repository to clone in the current directory. Default', default='https://github.com/MaastrichtU-IDS/d2s-project-template.git')
    config['d2s']['url'] = d2s_repository_url
    click.echo(click.style('[d2s] ', bold=True) + 'Cloning the repository in ' + projectname + '...')

    os.system('git clone --quiet --recursive ' + d2s_repository_url + ' ' + projectname)
    os.chdir(projectname)
    click.echo(click.style('[d2s]', bold=True) + ' Git repository cloned.')
    if not os.path.exists('./d2s-core'):
        os.system('git submodule add --recursive https://github.com/MaastrichtU-IDS/d2s-core.git')

    # Create workspace directories and chmod 777
    listToCreate = ["input", "output", "import", "output/tmp-outdir", "resources",
        "logs", "dumps/rdf/releases/1", 'dumps/hdt', 'virtuoso', 'tmp-virtuoso']
    click.echo(click.style('[d2s]', bold=True) + ' Creating following folders in workspace: ' + ", ".join(listToCreate))
    for fileToCreate in listToCreate:
        os.makedirs('workspace/' + fileToCreate, exist_ok=True)
    chmod777('workspace')

    click.echo()
    user_home_dir = str(Path.home())
    # Copy GraphDB zip file to the right folder in d2s-core
    click.echo(click.style('[d2s]', bold=True) + ' The GraphDB triplestore needs to be downloaded for licensing reason.\n'
        + 'Go to ' 
        + click.style('https://ontotext.com/products/graphdb/', bold=True) 
        + ' and provide your email to receive the URL to download ' + click.style('GraphDB version 9.1.1 standalone zip', bold=True))
    
    graphdb_path = click.prompt(click.style('[?]', bold=True) + ' Enter the path to the GraphDB distribution 9.1.1 zip file used to build the Docker image. Default', default=user_home_dir + '/graphdb-free-9.1.1-dist.zip')
    # Get GraphDB installation file
    if os.path.exists(graphdb_path):
        shutil.copy(graphdb_path, 'd2s-core/support/graphdb')
    else:
        click.echo(click.style('[d2s]', bold=True) + ' GraphDB installation file not found. Copy the zip file in d2s-core/support/graphdb after download.')

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
@click.argument('services', nargs=-1, autocompletion=get_services_list)
@click.option(
    '--images/--no-images', default=False, 
    help='Update files permissions (Docker images by default)')
@click.option(
    '--permissions/--no-permissions', default=False, 
    help='Update files permissions (Docker images by default)')
@click.option(
    '--submodules/--no-submodule', default=False, 
    help='Update the Git submodules (d2s-core)')
def update(services, images, permissions, submodules):
    """Update d2s (images, permissions, submodules)"""
    if submodules:
        print("Update submodules: d2s-core")
        project_dir = os.getcwd()
        os.chdir('d2s-core')
        os.system('git checkout master')
        os.system('git pull')
        os.chdir(project_dir)
    if permissions:
        listToUpdate = ["input", "output", "import", "dumps", "tmp-virtuoso", "virtuoso"]
        click.echo(click.style('[d2s]', bold=True) + ' Password might be asked to updates following folder permissions in workspace: ' + ", ".join(listToUpdate))
        for fileToUpdate in listToUpdate:
            chmod777('workspace/' + fileToUpdate)
            os.makedirs('workspace/' + fileToUpdate, exist_ok=True)
        click.echo(click.style('[d2s]', bold=True) + ' Most permissions issues can be fixed by changing the owner of the file while running as administrator')
        click.secho('sudo chown -R ' + os.getuid() + ':' + os.getgid() + ' workspace', bold=True)
    if images:
        # Update Docker images (pull and build graphdb)
        services_string = " ".join(services)
        os.system(docker_compose_cmd + 'pull ' + services_string)
        if not services or "graphdb" in services:
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
    if not services or services[0] == "demo":
        deploy = "demo"
        services_string = "graphdb tmp-virtuoso drill"
        click.echo(click.style('[d2s] ', bold=True) + ' Starting the services for the demo: ' + services_string)
    else:
        services_string = " ".join(services)
    
    # Run docker-compose:
    if deploy:
        os.system(docker_compose_cmd + '-f d2s-core/deployments/'
        + deploy + '.yml up -d --force-recreate ' + services_string)
    else:
        os.system(docker_compose_cmd + 'up -d --force-recreate ' + services_string)

    # Ask user to create the GraphDB test repository
    click.echo(click.style('[d2s] ', bold=True) + services_string + ' started.')
    if 'graphdb' in services or 'demo' in services:
        click.echo(click.style('[d2s] ', bold=True) 
                + 'Create repository on GraphDB: http://localhost:7200/repository')
        # TODO: Creating GraphDB repo by posting multiform with urllib needs to be changed
        # if click.confirm(click.style('[?]', bold=True) + ' Do you want to create the ' 
        # + click.style('demo repository', bold=True) + ' in GraphDB?'):
        #     click.echo(click.style('[d2s] ', bold=True) 
        #         + 'Creating the repository, it should take about 20s.')
        #     time.sleep(10)
        #     localGraphdbUrl = 'http://localhost:7200/rest/repositories'
        #     headers = {'Content-Type': 'multipart/form-data'}
        #     request = urllib.request.Request(localGraphdbUrl, 
        #         open('d2s-core/support/graphdb-repo-config.ttl', 'rb'),
        #                             headers=headers)
        #     response = urllib.request.urlopen(request)
        #     os.system('curl -X POST http://localhost:7200/rest/repositories -F "config=@d2s-core/support/graphdb-repo-config.ttl" -H "Content-Type: multipart/form-data"')
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
    os.system('ps ax -o pid,%cpu,%mem,start,command | grep "[c]wl-runner"')

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
    os.system('watch tail -n 30 workspace/logs/' + workflow)


@cli.command()
@click.argument('workflow', autocompletion=get_workflow_history)
def log(workflow):
    """Display logs of a workflow"""
    os.system('less +G workspace/logs/' + workflow)

@cli.command()
@click.argument('datasets', nargs=-1, autocompletion=get_datasets_list)
def download(datasets):
    """Download a dataset to be processed"""
    start_time = datetime.datetime.now()
    for dataset in datasets:
        os.system('docker run -it -v ' + os.getcwd() + ':/srv \
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
@click.option(
    '--yarrrml/--turtle-rml', default=False, 
    help='Use yarrrml mappings')
@click.option(
    '--mapper/--streamer', default=False, 
    help='Run RML Streamer or Mapper')
@click.option(
    '--detached/--watch', default=True, 
    help='Run in detached mode or watch workflow')
@click.option(
    '--openshift/--local', default=False, 
    help='Run RML Streamer on OpenShift')
@click.option(
    '-p', '--parallelism', default='8',
    help='Run in parallel, depends on Task Slots availables')
def rml(dataset, detached, yarrrml, mapper, openshift, parallelism):
    """Run RML Streamer"""
    if (detached):
        detached_arg = '-d'
    else:
        detached_arg = '-it'

    rml_file_extension = '.rml.ttl'

    # Convert .yarrr.yml files to .yarrr.rml.ttl
    if yarrrml:
        rml_file_extension = '.yarrr.rml.ttl'
        for file in os.listdir('./datasets/' + dataset + '/mapping'):
            mapping_filename = os.fsdecode(file)
            if mapping_filename.endswith(".yarrr.yml"): 
                # Run rmlmapper docker image
                output_filename = mapping_filename.replace('.yarrr.yml', rml_file_extension)
                click.echo(click.style('[d2s]', bold=True) + ' Converting YARRRML file: ' + mapping_filename + ' to datasets/' + dataset + '/mapping/' + output_filename)
                yarrrml_cmd = 'docker run -it --rm -v ' + os.getcwd() + '/datasets:/app/datasets umids/yarrrml-parser:latest -i /app/datasets/' + dataset + '/mapping/' + mapping_filename + ' -o /app/datasets/' + dataset + '/mapping/' + output_filename
                # Run yarrrml parser
                os.system(yarrrml_cmd)

    if openshift:
        # Ask if need to copy file on OpenShift cluster
        click.echo(click.style('[d2s]', bold=True) + ' Running RMLStreamer on OpenShift. Make sure your logged in and in the right project.')
        flink_manager_pod = os.popen('oc get pod --selector app=flink --selector component=jobmanager --no-headers -o=custom-columns=NAME:.metadata.name').read().strip()
        click.echo(click.style('[d2s]', bold=True) + ' ID of the Apache Flink pod used: ' 
            + click.style(flink_manager_pod, bold=True))
        if click.confirm(click.style('[?]', bold=True) + ' It is required to copy (rsync) the workspace to the OpenShift cluster the first time your run it. Do you want to do it?'):
            # rsync input files and mapping files
            os.system('oc exec ' + flink_manager_pod + ' -- mkdir -p /mnt/workspace/import')
            os.system('oc rsync workspace/input ' + flink_manager_pod + ':/mnt/workspace/')
            os.system('oc rsync datasets ' + flink_manager_pod + ':/mnt/')

    for file in os.listdir('./datasets/' + dataset + '/mapping'):
     mapping_filename = os.fsdecode(file)
     if mapping_filename.endswith(rml_file_extension): 
        # print(os.path.join(directory, filename))
        mapping_filepath = 'datasets/' + dataset + '/mapping/' + mapping_filename
        click.echo(click.style('[d2s]', bold=True) + ' Execute mappings from ' 
            + click.style(mapping_filepath, bold=True))

        output_filename = 'rml'
        # Now build the command to run RML processor
        if openshift:
            # Run RMLStreamer in an OpenShift cluster
            output_filename = 'openshift-rmlstreamer-' + mapping_filename.replace('.', '_') + '-' + dataset + '.nt'
            rml_cmd = 'oc exec ' + flink_manager_pod + ' -- /opt/flink/bin/flink run -c io.rml.framework.Main /opt/RMLStreamer.jar --path /mnt/datasets/' + dataset + '/mapping/' + mapping_filename + ' --outputPath /mnt/workspace/import/' + output_filename + ' --job-name "[d2s] RMLStreamer ' + mapping_filename + ' - ' + dataset + '"'
        else:
            # Run locally
            if mapper:
                # Run rmlmapper docker image
                output_filename = 'rmlmapper-' + mapping_filename.replace('.', '_') + '-' + dataset + '.nt'
                rml_cmd = 'docker run ' + detached_arg + ' -v ' + os.getcwd() + '/workspace:/mnt/workspace -v ' + os.getcwd() + '/datasets:/mnt/datasets umids/rmlmapper:4.7.0 -m /mnt/datasets/' + dataset + '/mapping/' + mapping_filename + ' -o /mnt/workspace/import/' + output_filename
            else:
                # Run RMLStreamer in running Apache Flink
                output_filename = 'rmlstreamer-' + mapping_filename.replace('.', '_') + '-' + dataset + '.nt'
                rml_cmd = 'docker exec ' + detached_arg + ' d2s-rmlstreamer /opt/flink/bin/flink run -c io.rml.framework.Main /opt/RMLStreamer.jar --path /mnt/datasets/' + dataset + '/mapping/' + mapping_filename + ' --outputPath /mnt/workspace/import/' + output_filename + ' --job-name "[d2s] RMLStreamer ' + mapping_filename + ' - ' + dataset + '"'
                click.echo(click.style('[d2s]', bold=True) + ' Check the jobs running at ' 
                    + click.style('http://localhost:8078/#/job/running', bold=True))
                ## Try parallelism:
                # rml_cmd = 'docker exec ' + detached_arg + ' d2s-rmlstreamer /opt/flink/bin/flink run -p ' + parallelism + ' -c io.rml.framework.Main /opt/RMLStreamer.jar --path /mnt/datasets/' + dataset + '/mapping/' + mapping_filename + ' --outputPath /mnt/workspace/import/' + output_filename + ' --job-name "[d2s] RMLStreamer ' + mapping_filename + ' - ' + dataset + '" --parallelism ' + parallelism + ' --enable-local-parallel'
        
        # Run RML processor
        print(rml_cmd)
        os.system(rml_cmd)
        # TODO: store logs in a file and get the run time. Use subprocess.call
        # with open('workspace/logs/' + output_filename + '.log', 'a') as output:
        #     process = subprocess.call(rml_cmd, shell=True, 
        #         stdout=output, stderr=output)

        # click.echo(click.style('[d2s]', bold=True) + ' PID of running process: ' + str(process.pid))
        click.echo(click.style('[d2s]', bold=True) + ' Output file in ')
        click.secho('workspace/import/' + output_filename, bold=True)
    
    # Try parallelism:
    # rmlstreamer_cmd = 'docker exec -d d2s-rmlstreamer /opt/flink/bin/flink run -p 4 /opt/RMLStreamer.jar --path /mnt/datasets/' + dataset + '/mapping/rml-mappings.ttl --outputPath /mnt/workspace/import/rml-output-' + dataset + '.nt --job-name "[d2s] RMLStreamer ' + dataset + '" --enable-local-parallel'
    # Try to use docker-compose, but exec dont resolve from the -f file
    # rmlstreamer_cmd = docker_compose_cmd + 'exec -d rmlstreamer /opt/flink/bin/flink run /opt/RMLStreamer.jar --path /mnt/datasets/' + dataset + '/mapping/rml-mappings.ttl --outputPath /mnt/workspace/import/rml-output-' + dataset + '.nt --job-name "[d2s] RMLStreamer ' + dataset + '"'
    # print(rmlstreamer_cmd)

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
    cwl_workflow_path = 'd2s-core/cwl/workflows/' + workflow
    dataset_config_path = 'datasets/' + dataset + '/config.yml'

    # TODO: Trying to fix issue where virtuoso bulk load only the first dataset we run
    # It needs restart to work a second time
    # click.echo(click.style('[d2s] ', bold=True) 
    #     + 'Restart tmp Virtuoso and delete file in '
    #     + click.style('workspace/output', bold=True))
    # os.system(docker_compose_cmd + 'stop tmp-virtuoso')
    # os.system(docker_compose_cmd + 'up -d --force-recreate tmp-virtuoso')
    # TODO: fix this dirty Virtuoso deployment 
    # Virtuoso unable to handle successive bulk load + permission issues + load.sh in the virtuoso containers
    # I don't know how, they managed to not put it in the container... They had one job...

    # Delete previous output (not archived). See article: https://thispointer.com/python-how-to-delete-a-directory-recursively-using-shutil-rmtree/
    shutil.rmtree('workspace/output', ignore_errors=True, onerror=None)
    for file in glob.glob("workspace/tmp-virtuoso/*.nq"):
        os.remove(file)

    if (detached):
        # TODO: Find a better solution to work on windows.
        # time allows to get running time of detached process but require to be installed
        # e.g. yum install time
        # cwl_command = 'nohup time '
        cwl_command = 'nohup '
    else:
        cwl_command = ''
    cwl_command = cwl_command +'cwl-runner --custom-net d2s-core_network --outdir {0}/output --tmp-outdir-prefix={0}/output/tmp-outdir/ --tmpdir-prefix={0}/output/tmp-outdir/tmp- {1} {2}'.format('workspace',cwl_workflow_path,dataset_config_path)
    if (detached):
        log_filename = workflow + '-' + dataset + '-' + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + '.txt'
        cwl_command = cwl_command + ' > workspace/logs/' + log_filename + ' &'
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
    # runtime_context.custom_net = 'd2s-core_network'
    # runtime_context.outdir = 'workspace/output'
    # runtime_context.tmp_outdir_prefix = 'workspace/output/tmp-outdir/'
    # runtime_context.tmpdir_prefix = 'workspace/output/tmp-outdir/tmp-'
    # cwl_factory = cwltool.factory.Factory(runtime_context=runtime_context)
    # # Run CWL workflow
    # run_workflow = cwl_factory.make(cwl_workflow_path) # the .cwl file
    # result = run_workflow(inp=dataset_config_file.read())  # the config yml
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
    metadataArray = []
    metadataArray.append({'id': 'dataset_id', 'description': 'Enter the identifier of your datasets, e.g. drugbank (lowercase, no space or weird characters)'})
    metadataArray.append({'id': 'dataset_name', 'description': 'Enter a human-readable name for your datasets, e.g. DrugBank'})
    metadataArray.append({'id': 'dataset_description', 'description': 'Enter a description for this dataset'})
    metadataArray.append({'id': 'publisher_name', 'default': 'Institute of Data Science at Maastricht University', 'description': 'Enter complete name for the institutions publishing the data and its affiliation, e.g. Institute of Data Science at Maastricht University'})
    metadataArray.append({'id': 'publisher_url', 'default': 'https://maastrichtuniversity.nl/ids', 'description': 'Enter a valid URL for the publisher homepage. Default'})
    metadataArray.append({'id': 'source_license', 'default': 'http://creativecommons.org/licenses/by-nc/4.0/legalcode', 'description': 'Enter a valid URL to the license informations about the original dataset'})
    metadataArray.append({'id': 'inputFormat', 'default': 'application/xml', 'description': 'Enter the format of the source file to transform'})
    metadataArray.append({'id': 'homepage', 'default': 'http://d2s.semanticscience.org/', 'description': 'Enter the URL of the dataset homepage'})
    metadataArray.append({'id': 'accessURL', 'default': 'https://www.drugbank.ca/releases/latest', 'description': 'Specify URL of the directory containing the file(s) of interest (not the direct file URL)'})
    metadataArray.append({'id': 'references', 'default': 'https://www.ncbi.nlm.nih.gov/pubmed/29126136', 'description': 'Enter the URL of a publication supporting the dataset'})
    metadataArray.append({'id': 'keyword', 'default': 'drug', 'description': 'Enter a keyword to describe the dataset'})
    metadataArray.append({'id': 'theme', 'default': 'http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C54708', 'description': 'Enter the URL to an ontology concept describing the dataset theme'})
    metadataArray.append({'id': 'sparqlEndpoint', 'default': 'https://graphdb.dumontierlab.com/repositories/trek', 'description': 'Enter the URL of the final SPARQL endpoint to access the integrated dataset'})
    metadataArray.append({'id': 'downloadURL', 'default': 'https://www.drugbank.ca/releases/5-1-1/downloads/all-full-database', 'description': 'Enter the URL to download the source file to be transformed'})
    metadataArray.append({'id': 'rdfPublisherName', 'default': 'Institute of Data Science at Maastricht University', 'description': 'Enter the name for the publisher of the RDF distribution'})
    metadataArray.append({'id': 'rdfPublisherPage', 'default': 'https://maastrichtuniversity.nl/ids', 'description': 'Enter a valid homepage URL for the publisher of the RDF distribution'})
    metadataArray.append({'id': 'rdf_license', 'default': 'http://creativecommons.org/licenses/by-nc/4.0/legalcode', 'description': 'Enter a valid URL to the license informations about the RDF distribution of the dataset'})
    metadataArray.append({'id': 'rdfDownloadURL', 'default': 'http://download.137.120.31.102.nip.io/#/', 'description': 'Enter a valid URL to download the RDF distribution'})
    
    for metadataObject in metadataArray:
        if 'default' in metadataObject:
            metadataObject['value'] = click.prompt(click.style('[?]', bold=True) 
            + ' ' + metadataObject['description'] + '. Default',
            default=metadataObject['default'])
        else:
            metadataObject['value'] = click.prompt(click.style('[?]', bold=True) 
            + ' ' + metadataObject['description'])

    # dataset_id = click.prompt(click.style('[?]', bold=True) 
    #     + ' Enter the identifier of your datasets, e.g. wikipathways (lowercase, no space or weird characters)')
    # dataset_name = click.prompt(click.style('[?]', bold=True) 
    #     + ' Enter a human-readable name for your datasets, e.g. WikiPathways')
    # dataset_description = click.prompt(click.style('[?]', bold=True) 
    #     + ' Enter a description for this dataset')
    # publisher_name = click.prompt(click.style('[?]', bold=True) 
    #     + ' Enter complete name for the institutions publishing the data and its affiliation, e.g. Institute of Data Science at Maastricht University')
    # publisher_url = click.prompt(click.style('[?]', bold=True) 
    #     + ' Enter a valid URL for the publisher homepage. Default', 
    #     default='https://maastrichtuniversity.nl/ids')
    # source_license = click.prompt(click.style('[?]', bold=True) 
    #     + ' Enter a valid URL to the license informations about the original dataset. Default', 
    #     default='http://creativecommons.org/licenses/by-nc/4.0/legalcode')
    # rdf_license = click.prompt(click.style('[?]', bold=True) 
    #     + ' Enter a valid URL to the license informations about the RDF distribution of the dataset. Default', 
    #     default='http://creativecommons.org/licenses/by-nc/4.0/legalcode')


    # rdf_license = click.prompt(click.style('[?]', bold=True) 
    #     + ' Enter. Default', 
    #     default='changeme')

    dataset_id = metadataArray[0]['value']
    dataset_folder_path = 'datasets/' + dataset_id
    shutil.copytree('d2s-core/support/template/dataset', dataset_folder_path)
    os.rename(dataset_folder_path + '/process-dataset.ipynb', dataset_folder_path + '/process-' + dataset_id + '.ipynb')
    
    # Replace provided metadata in generated files for the new dataset
    for dname, dirs, files in os.walk(dataset_folder_path):
        for fname in files:
            fpath = os.path.join(dname, fname)
            with open(fpath) as f:
                file_content = f.read()
            for metadataObject in metadataArray:
                file_content = file_content.replace("$" + metadataObject['id'], metadataObject['value'])
            with open(fpath, "w") as f:
                f.write(file_content)
    click.echo()
    click.echo(click.style('[d2s]', bold=True) + ' The config, metadata and mapping files for the ' 
        + click.style(dataset_id + ' dataset', bold=True) 
        + ' has been generated')
    click.echo(click.style('[d2s]', bold=True) + ' Start edit them in ' + click.style('datasets/' + dataset_id, bold=True))
    
    # Will not work on all platforms:
    # if click.confirm(click.style('[?]', bold=True) + ' Do you want to open the ' 
    #     + click.style('download', bold=True) + ' file to edit it?'):
    #     os.system('nano ' + dataset_folder_path + '/download/download.sh')

    