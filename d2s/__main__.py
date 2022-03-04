import os
import sys
import stat
import shutil
import click
import datetime

from d2s.generate_metadata import create_dataset_prompt, generate_hcls_from_sparql
from d2s.utils import new_dataset, get_config, init_folder, get_base_dir, init_d2s_java
from d2s.sparql_operations import sparql_insert_files, java_upload_files
from d2s.process_datasets import process_datasets_metadata
from d2s.generate_shacl import generate_shacl
from rdflib import Graph

@click.group()
def cli():
    """d2s Command Line Interface"""
    pass

# @click.argument('projectname', nargs=1)
# @click.pass_context
# def init(ctx, projectname):
@cli.command()
def init():
    """Initialize a project in the provided folder name"""
    init_folder()

@cli.command()
def config():
    """Show the project configuration"""
    get_config()


@cli.group()
def new():
    """Generate new datasets mappings files"""
    pass

@new.command()
def dataset():
    """Create a new folder to map data from a template"""
    new_dataset()


@cli.group()
def metadata():
    """Generate HCLS descriptive metadata for RDF datasets"""
    pass

# @metadata.command(help='Create HCLS metadata for a dataset in the terminal prompt (summary, version and distributions)')
# @click.option(
#     '-o', '--output', default='', 
#     help='Write RDF to output file')
# @click.option(
#     '-u', '--dataset-uri', 
#     help='URI of the dataset distribution to describe')
# def create(output, dataset_uri):
#     create_dataset_prompt(dataset_uri, output=output)



@metadata.command(help='Generate HCLS descriptive metadata (about types and relations) for the graphs in a SPARQL endpoint')
@click.argument('sparql_endpoint')
@click.option(
    '-u', '--dataset-uri', 
    help='URI of the dataset distribution to describe')
@click.option(
    '-o', '--output', default='', 
    help='Write RDF to output file')
@click.option(
    '-m', '--metadata-type', default='hcls', 
    help='Type of metadata to generate (hcls, bio2rdf). Default is hcls')
@click.option(
    '-g', '--graph', default='', 
    help='Compute metadata only for the specified graph in the triplestore (compute for all graphs by default)')
@click.option(
    '--create-dataset/--analyze-only', default=False, 
    help='Prompt questions to generate the dataset metadata and analyze the endpoint (default), or only analyze')
def analyze(sparql_endpoint, dataset_uri, output, metadata_type, graph, create_dataset):

    # if not dataset_uri:
    #     dataset_uri = 'https://w3id.org/d2s/distribution/default'
        
    g = Graph()
    # if create_dataset:
    #     g, metadata_answers = create_dataset_prompt(dataset_uri, g)
    g = generate_hcls_from_sparql(sparql_endpoint, dataset_uri, metadata_type, graph, g, create_dataset)
    if output:
        g.serialize(destination=output, format='turtle')
        print(f"Metadata stored to {output} 📝")
    else:
        print(g.serialize(format='turtle'))




@cli.command(help='Download and convert a dataset to RDF based on its metadata file')
@click.option(
    '-i', '--input-file', default=None, 
    help='Input datasets metadata file to process. If not provided d2s will search for a .ttl or .jsonld file in the current folder.')
# @click.option(
#     '-o', '--output', default='', 
#     help='Write RDF to the given output file')
@click.option(
    '--dryrun/--publish', default=True, 
    help='Dry run, only generate RDF and does not publish to a triplestore')
@click.option(
    '--staging/--production', default=True, 
    help='If --publish enabled: publish in the staging triplestore(default), or publish to the production triplestore. And generate metadata about the graph')
@click.option(
    '-s', '--sample', default=0, 
    help='Produce a sample file with given number of lines for TSV/CSV files (e.g. --sample 100).')
@click.option(
    '--report/--no-report', default=False, 
    help='Activate the generation of a HTML report to explore downloaded tabular files')
@click.option(
    '-m', '--memory', default='4g', 
    help='Memory given to the processing, e.g. for java -Xmx. Default: 4g')
@click.option(
    '--rmlstreamer/--local', default=False, 
    help='Activate the generation of a HTML report to explore downloaded tabular files')
def run(input_file, dryrun, staging, sample, report, memory, rmlstreamer):
    process_datasets_metadata(input_file, dryrun, staging, sample, report, memory, rmlstreamer)
    # if output:
    #     g.serialize(destination=output, format='turtle')
    #     print("Metadata stored to " + output + ' 📝')
    # else:
    #     print(g.serialize(format='turtle'))




# TODO: new command to automatically generate SHACL from a RDF snippet
@cli.command(help='Generate SHACL shapes from a RDF metadata')
@click.argument('rdf_file')
def shacl(rdf_file):
    generate_shacl(rdf_file)





@cli.group()
def sparql():
    """Execute operations on SPARQL endpoints (e.g. execute SPARQL query files)"""
    pass

@sparql.command(help='Execute SPARQL queries in provided files on the provided SPARQL endpoint')
@click.argument('file_pattern')
@click.argument('sparql_endpoint')
@click.option(
    '-u', '--username', default='dba', 
    help='Username for the SPARQL endpoint')
@click.option(
    '-p', '--password', default='dba', 
    help='Password for the SPARQL endpoint')
@click.option(
    '-g', '--graph', default='', 
    help='Graph where to load the RDF')
@click.option(
    '--chunks-size', default='1000', 
    help='Number of statements per chunks inserted. Use -1 to load all in one shot.')
def insert(file_pattern, sparql_endpoint, username, password, graph, chunks_size):
    sparql_insert_files(file_pattern, sparql_endpoint, username, password, graph, chunks_size)

@sparql.command(help='Upload RDF files to a SPARQL endpoint using Java RDF4J (java installed required)')
@click.argument('file_pattern')
@click.argument('sparql_endpoint')
@click.option(
    '-u', '--username', default='dba', 
    help='Username for the SPARQL endpoint')
@click.option(
    '-p', '--password', default='dba', 
    help='Password for the SPARQL endpoint')
@click.option(
    '-g', '--graph', default='', 
    help='Graph where to load the RDF')
def upload(file_pattern, sparql_endpoint, username, password, graph):
    java_upload_files(file_pattern, sparql_endpoint, username, password, graph)







### Commands to run services and workflows:

docker_compose_cmd = 'docker-compose '

# Used for autocompletion
def get_services_list(ctx, args, incomplete):
    # TODO: automate by parsing the docker-compose.yml
    return filter(lambda x: x.startswith(incomplete), [ 'demo',
    'graphdb', 'graphdb-preload', 'graphdb-ee', 'virtuoso', 'tmp-virtuoso', 'blazegraph', 'allegrograph', 'anzograph', 'fuseki',
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
                rml_cmd = 'oc exec ' + flink_manager_pod + ' -- /opt/flink/bin/flink run -p ' + str(parallelism) + ' -c io.rml.framework.Main /opt/RMLStreamer.jar toFile -m /mnt/datasets/' + dataset + '/mapping/' + mapping_filename + ' -o /mnt/workspace/import/' + output_filename + ' --job-name "[d2s] RMLStreamer ' + mapping_filename + ' - ' + dataset + '"'
            else:
                # Run locally
                if mapper:
                    # Run rmlmapper docker image
                    init_d2s_java('rmlmapper')
                    output_filename = 'rmlmapper-' + mapping_filename.replace('.', '_') + '-' + dataset + '.nt'
                    rml_cmd = 'java -jar ' + get_base_dir('rmlmapper.jar') + ' -m ' + dataset + '/mapping/' + mapping_filename + ' -o import/' + output_filename
                    # rml_cmd = 'docker run ' + detached_arg + ' -v ' + os.getcwd() + '/workspace:/mnt/workspace -v ' + os.getcwd() + '/datasets:/mnt/datasets umids/rmlmapper:4.7.0 -m /mnt/datasets/' + dataset + '/mapping/' + mapping_filename + ' -o /mnt/workspace/import/' + output_filename
                else:
                    # Run RMLStreamer in running Apache Flink
                    output_filename = 'rmlstreamer-' + mapping_filename.replace('.', '_') + '-' + dataset + '.nt'
                    rml_cmd = 'docker exec ' + detached_arg + ' d2s-rmlstreamer /opt/flink/bin/flink run -p ' + str(parallelism) + ' -c io.rml.framework.Main /opt/RMLStreamer.jar toFile -m /mnt/datasets/' + dataset + '/mapping/' + mapping_filename + ' -o /mnt/workspace/import/' + output_filename + ' --job-name "[d2s] RMLStreamer ' + mapping_filename + ' - ' + dataset + '"'
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


# # TODO: remove d2s-core references
# @cli.command()
# @click.argument('services', nargs=-1, autocompletion=get_services_list)
# @click.option(
#     '--images/--no-images', default=False, 
#     help='Update files permissions (Docker images by default)')
# @click.option(
#     '--permissions/--no-permissions', default=False, 
#     help='Update files permissions (Docker images by default)')
# @click.option(
#     '--submodules/--no-submodule', default=False, 
#     help='Update the Git submodules (d2s-core)')
# def update(services, images, permissions, submodules):
#     """Update d2s (images, permissions, submodules)"""
#     if submodules:
#         print("Update submodules: d2s-core")
#         project_dir = os.getcwd()
#         os.chdir('d2s-core')
#         os.system('git checkout master')
#         os.system('git pull')
#         os.chdir(project_dir)
#     if permissions:
#         listToUpdate = ["input", "output", "import", "dumps", "tmp-virtuoso", "virtuoso"]
#         click.echo(click.style('[d2s]', bold=True) + ' Password might be asked to updates following folder permissions in workspace: ' + ", ".join(listToUpdate))
#         for fileToUpdate in listToUpdate:
#             chmod777('workspace/' + fileToUpdate)
#             os.makedirs('workspace/' + fileToUpdate, exist_ok=True)
#         click.echo(click.style('[d2s]', bold=True) + ' Most permissions issues can be fixed by changing the owner of the file while running as administrator')
#         click.secho('sudo chown -R ' + os.getuid() + ':' + os.getgid() + ' workspace', bold=True)
#     if images:
#         # Update Docker images (pull and build graphdb)
#         services_string = " ".join(services)
#         os.system(docker_compose_cmd + 'pull ' + services_string)
#         if not services or ("graphdb" and "graphdb-preload") in services:
#             os.system(docker_compose_cmd + 'build graphdb graphdb-preload')
#         click.echo(click.style('[d2s]', bold=True) + ' All images pulled and built.')
#         click.echo(click.style('[d2s]', bold=True) + ' You can now start services (e.g. demo services):')
#         click.secho('d2s start demo', bold=True)


# @cli.command()
# @click.argument('services', nargs=-1, autocompletion=get_services_list)
# @click.option(
#     '-d', '--deploy', default='', 
#     help='Use custom deployment config')
# def start(services, deploy):
#     """Start services"""
#     if not services or services[0] == "demo":
#         deploy = "demo"
#         services_string = "graphdb tmp-virtuoso drill"
#         click.echo(click.style('[d2s] ', bold=True) + ' Starting the services for the demo: ' + services_string)
#     else:
#         services_string = " ".join(services)
    
#     # Run docker-compose:
#     if deploy:
#         os.system(docker_compose_cmd + '-f d2s-core/deployments/'
#         + deploy + '.yml up -d --force-recreate ' + services_string)
#     else:
#         os.system(docker_compose_cmd + 'up -d --force-recreate ' + services_string)

#     # Ask user to create the GraphDB test repository
#     click.echo(click.style('[d2s] ', bold=True) + services_string + ' started.')
#     if 'graphdb' in services or 'demo' in services:
#         click.echo(click.style('[d2s] ', bold=True) 
#                 + 'Create repository on GraphDB: http://localhost:7200/repository')
#         # TODO: Creating GraphDB repo by posting multiform with urllib needs to be changed
#         # if click.confirm(click.style('[?]', bold=True) + ' Do you want to create the ' 
#         # + click.style('demo repository', bold=True) + ' in GraphDB?'):
#         #     click.echo(click.style('[d2s] ', bold=True) 
#         #         + 'Creating the repository, it should take about 20s.')
#         #     time.sleep(10)
#         #     localGraphdbUrl = 'http://localhost:7200/rest/repositories'
#         #     headers = {'Content-Type': 'multipart/form-data'}
#         #     request = urllib.request.Request(localGraphdbUrl, 
#         #         open('d2s-core/support/graphdb-repo-config.ttl', 'rb'),
#         #                             headers=headers)
#         #     response = urllib.request.urlopen(request)
#         #     os.system('curl -X POST http://localhost:7200/rest/repositories -F "config=@d2s-core/support/graphdb-repo-config.ttl" -H "Content-Type: multipart/form-data"')
#     click.echo()
#     click.echo(click.style('[d2s]', bold=True) 
#         + ' You can now download data to run a first workflow:')
#     click.secho('d2s download', bold=True)


# @cli.command()
# @click.argument('services', nargs=-1, autocompletion=get_services_list)
# @click.option(
#     '--all/--no-all', default=False, 
#     help='Stop all services')
# def stop(services, all):
#     """Stop services (--all to stop all services)"""
#     if all:
#         os.system(docker_compose_cmd + 'down')
#         click.echo(click.style('[d2s] ', bold=True) + 'All services stopped.')
#     else:
#         services_string = " ".join(services)
#         os.system(docker_compose_cmd + 'stop ' + services_string)
#         click.echo(click.style('[d2s] ', bold=True) + services_string + ' stopped.')


# @cli.command()
# def services():
#     """List running services"""
#     os.system('docker ps --format="table {{.Names}}\t{{.Ports}}\t{{.Status}}\t{{.Networks}}"')


# @cli.command()
# def process_running():
#     """List running workflows processes"""
#     os.system('echo "PID    CPU  Mem Start    Command"')
#     os.system('ps ax -o pid,%cpu,%mem,start,command | grep "[c]wl-runner"')

# @cli.command()
# @click.argument('process', autocompletion=get_running_processes)
# def process_stop(process):
#     """Stop a running workflows process"""
#     if (process == "0"):
#         click.echo(click.style('[d2s] ', bold=True) + 'No process to stop.')
#     else:
#         os.system('kill -9 ' + process)
#         click.echo(click.style('[d2s] ', bold=True) + 'Process ' + click.style(process, bold=True) + ' stopped.')


# @cli.command()
# @click.argument('workflow', autocompletion=get_running_workflows)
# def watch(workflow):
#     """Watch running workflow"""
#     os.system('watch tail -n 30 workspace/logs/' + workflow)


# @cli.command()
# @click.argument('workflow', autocompletion=get_workflow_history)
# def log(workflow):
#     """Display logs of a workflow"""
#     os.system('less +G workspace/logs/' + workflow)

# @cli.command()
# @click.argument('datasets', nargs=-1, autocompletion=get_datasets_list)
# def download(datasets):
#     """Download a dataset to be processed"""
#     start_time = datetime.datetime.now()
#     for dataset in datasets:
#         os.system('docker run -it -v ' + os.getcwd() + ':/srv \
#             umids/d2s-bash-exec:latest \
#             /srv/datasets/' + dataset + '/download/download.sh workspace/input/' + dataset)
#         click.echo(click.style('[d2s] ' + dataset, bold=True) + ' dataset downloaded at ' 
#         + click.style('workspace/input/' + dataset, bold=True))
#     run_time = datetime.datetime.now() - start_time
#     click.echo(click.style('[d2s] ', bold=True) 
#             + 'Datasets downloaded in: '
#             + click.style(str(datetime.timedelta(seconds=run_time.total_seconds())), bold=True))
#     click.echo()
#     click.echo(click.style('[d2s]', bold=True) + ' You can now run the transformation workflow:')
#     click.secho('d2s run', bold=True)

# @cli.command()
# @click.argument('workflow', autocompletion=get_workflows_list)
# @click.argument('dataset', autocompletion=get_datasets_list)
# @click.option(
#     '--get-mappings/--no-copy', default=False, 
#     help='Copy the mappings generated by the workflow to our datasets folder')
# @click.option(
#     '--detached/--watch', default=True, 
#     help='Run in detached mode or watch workflow')
# def run(workflow, dataset, get_mappings, detached):
#     """Run CWL workflows"""
#     start_time = datetime.datetime.now()
#     cwl_workflow_path = 'd2s-core/cwl/workflows/' + workflow
#     dataset_config_path = 'datasets/' + dataset + '/config.yml'

#     # TODO: Trying to fix issue where virtuoso bulk load only the first dataset we run
#     # It needs restart to work a second time
#     # click.echo(click.style('[d2s] ', bold=True) 
#     #     + 'Restart tmp Virtuoso and delete file in '
#     #     + click.style('workspace/output', bold=True))
#     # os.system(docker_compose_cmd + 'stop tmp-virtuoso')
#     # shutil.rmtree('workspace/tmp-virtuoso', ignore_errors=True, onerror=None)
#     # os.system(docker_compose_cmd + 'up -d --force-recreate tmp-virtuoso')
#     # TODO: fix this dirty Virtuoso deployment 
#     # Virtuoso unable to handle successive bulk load + permission issues + load.sh in the virtuoso containers
#     # I don't know how, they managed to not put it in the container... They had one job...

#     # Delete previous output (not archived). See article: https://thispointer.com/python-how-to-delete-a-directory-recursively-using-shutil-rmtree/
#     shutil.rmtree('workspace/output', ignore_errors=True, onerror=None)
#     # for file in glob.glob("workspace/tmp-virtuoso/*.nq"):
#     #     os.remove(file)

#     if (detached):
#         # TODO: Find a better solution to work on windows.
#         # time allows to get running time of detached process but require to be installed
#         # e.g. yum install time
#         # cwl_command = 'nohup time '
#         cwl_command = 'nohup '
#     else:
#         cwl_command = ''
#     cwl_command = cwl_command +'cwl-runner --custom-net d2s-core_network --outdir {0}/output --tmp-outdir-prefix={0}/output/tmp-outdir/ --tmpdir-prefix={0}/output/tmp-outdir/tmp- {1} {2}'.format('workspace',cwl_workflow_path,dataset_config_path)
#     if (detached):
#         log_filename = workflow + '-' + dataset + '-' + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + '.txt'
#         cwl_command = cwl_command + ' > workspace/logs/' + log_filename + ' &'
#     click.echo()
#     click.echo(click.style('[d2s] ', bold=True) 
#         + 'Running CWL worklow...')
#     click.echo(cwl_command)
#     os.system(cwl_command)

#     # Copy mappings generated by the workflow to datasets folder
#     if (get_mappings):
#         os.system('cp workspace/output/sparql_mapping_templates/* datasets/' 
#         + dataset + '/mapping/')
#         click.echo()
#         click.echo(click.style('[d2s] ', bold=True) 
#             + 'Browse the generated mappings files in '
#             + click.style('datasets/' + dataset + '/mapping', bold=True))
#     else:
#         click.echo()
#         click.echo(click.style('[d2s] ', bold=True) + 'Browse the file generated by the workflow in ' 
#             + click.style('workspace/output/' + dataset, bold=True))

#     if (detached):
#         click.echo()
#         click.echo(click.style('[d2s] ', bold=True) 
#             + 'Watch your workflow running: ')
#         click.secho('d2s watch ' + log_filename, bold=True)
#         click.echo(click.style('[d2s] ', bold=True) 
#             + 'Or display the complete workflow logs: ')
#         click.secho('d2s log ' + log_filename, bold=True)
#     else:
#         run_time = datetime.datetime.now() - start_time
#         click.echo(click.style('[d2s] ', bold=True) 
#                 + 'Workflow runtime: '
#                 + click.style(str(datetime.timedelta(seconds=run_time.total_seconds())), bold=True))

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

if __name__ == "__main__":
    sys.exit(cli())