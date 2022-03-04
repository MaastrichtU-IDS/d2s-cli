import os
from pathlib import Path
import pkg_resources
import shutil
import click
import dotenv 
import git
import requests
import yaml
# For JSON-LD:
# from rdflib.serializer import Serializer
# from rdflib import plugin

from d2s.generate_metadata import create_dataset_prompt

# logging.basicConfig(stream=sys.stderr, level=logging.INFO)

def get_git_path(find_file=None):
    """Return path of the root folder of the git repo the user is in. Or the asked file in this folder"""
    # if not path:
    path = os.getcwd()
    for folder in Path(path).parents:
        # Check whether "path/.git" exists and is a directory
        git_dir = folder / ".git"
        if git_dir.is_dir():
            # print(os.path.isfile(folder / find_file))
            if find_file and os.path.isfile(str(folder) + '/' + find_file):
                return str(folder) + '/' + find_file
            else:
                return str(folder)
    print('Warning: could not find a git repository among parents folder, using the current folder.')
    return str(path)
    # Note: gitPython does not work for some git repository, without no reason
    # git_repo = git.Repo(path, search_parent_directories=True)
    # git_root = git_repo.working_tree_dir
    # return git_root

def get_yaml_config(key=None):
    """Return path of the root folder of the git repo the user is in"""
    yaml_path = get_git_path('d2s.yml')
    if os.path.isfile(yaml_path):
        with open(yaml_path) as file:
            yaml_file = yaml.load(file, Loader=yaml.FullLoader)
            if not key:
                return yaml_file
            else: 
                if key in yaml_file.keys():
                    return yaml_file[key]
                else:
                    return None
    else:
        return {}

def get_base_dir(file=''):
    """Base dir (XDG standard) for d2s executables and jar in ~/.local/share/d2s"""
    return str(Path.home()) + '/.local/share/d2s/' + file

def init_d2s_java(init_file=''):
    """Download jar files if not present"""
    os.makedirs(get_base_dir(), exist_ok=True)
    if init_file == 'sparql-operations' and not os.path.isfile(get_base_dir('sparql-operations.jar')):
        print('Downloading sparql-operations.jar in ' + get_base_dir())
        r = requests.get('https://github.com/MaastrichtU-IDS/d2s-sparql-operations/releases/latest/download/sparql-operations.jar')
        with open(get_base_dir('sparql-operations.jar'), 'wb') as f:
            f.write(r.content)

    if init_file == 'rmlmapper' and not os.path.isfile(get_base_dir('rmlmapper.jar')):
        print('Downloading rmlmapper.jar in ' + get_base_dir())
        r = requests.get('https://github.com/RMLio/rmlmapper-java/releases/download/v4.12.0/rmlmapper.jar')
        with open(get_base_dir('rmlmapper.jar'), 'wb') as f:
            f.write(r.content)


def get_parse_format(input_file):
    """Given a filepath, return the format use by RDFLib to parse this file"""
    filename, file_extension = os.path.splitext(input_file)
    file_format = ''
    # Get file format for rdflib.parse based on file extension
    if file_extension in ['.trig', '.n3']:
        file_format = 'n3'
    elif file_extension in ['.json', '.jsonld', '.json-ld']:
        file_format = 'json-ld'
    elif file_extension in ['.xml', '.rdf']:
        file_format = 'xml'
    elif file_extension in ['.ttl', '.shacl']:
        file_format = 'ttl'
    elif file_extension in ['.nt']:
        file_format = 'nt'
    elif file_extension in ['.nq']:
        file_format = 'nquads'
    return file_format


# Init project and config
def init_folder():
    """Initialize a project in the current folder"""
    d2s_repository_url = click.prompt(click.style('[?]', bold=True) + ' Enter the Git repository URL for this project if you already have one (leave empty to use the current git repository, or init a new git repository): ', default="")

    # Clone git repo if URL provided
    if os.path.exists('.git'):
        click.echo(click.style('[d2s]', bold=True) + ' Git repository already initialized.')
    elif d2s_repository_url:
        click.echo(click.style('[d2s] ', bold=True) + 'Cloning the repository in the current folder...')
        git_repo = git.Repo.clone_from(d2s_repository_url, '.')
        git_repo.git.submodule('update', '--init')
        click.echo(click.style('[d2s]', bold=True) + ' Git repository cloned.')
    else:
        click.echo(click.style('[d2s] ', bold=True) + 'Initializing a bare git repository, think to push it to a remote repository on GitHub or GitLab to save it and share it.')
        git.Repo.init('.git', bare=True)
    
    # Create required files if missing (readme, requirements...)
    for dname, dirs, files in os.walk(pkg_resources.resource_filename('d2s', 'templates/project')):
        for filename in files:
            filepath = os.path.join(dname, filename)
            if not os.path.exists(filename):
                click.echo(click.style('[d2s]', bold=True) + ' Creating missing file: ' + filename)
                shutil.copyfile(filepath, os.getcwd() + '/' + filename)

    # Create datasets and workflows empty folders
    folders_to_create = ['datasets', '.github/workflows']
    click.echo(click.style('[d2s]', bold=True) + " Creating following folders in workspace if they don't exist already: " + ", ".join(folders_to_create))
    for file_to_create in folders_to_create:
        os.makedirs(file_to_create, exist_ok=True)

    # Create the .env file
    # f = open(".env", "w").close
    # if d2s_repository_url:
    #     dotenv.set_key('.env', 'GIT_URL', d2s_repository_url, quote_mode="noquote")
    # click.echo(click.style('[d2s] ', bold=True) + 'Setting the VIRTUOSO_PASSWORD if the .env file (not commited in git) to dba, change it to your password')
    # dotenv.set_key('.env', 'VIRTUOSO_PASSWORD', 'dba', quote_mode="noquote")
    # dotenv.set_key('.env', "PATH", os.getcwd(), quote_mode="noquote")

    click.echo()
    click.echo(click.style('[d2s]', bold=True) + ' Your d2s project has been initialized!')
    click.echo(click.style('[d2s]', bold=True) + ' Generate mappings for a dataset by running: d2s new dataset')

    ## Automatically commit files generated by d2s init?
    # os.system('git add .')
    # os.system('git commit -m "Initialize mapping project with d2s"')


def new_dataset():
    """Create a folder to map a new dataset"""
    # Go to the root of the git repo
    os.chdir(get_git_path())
    # Make sure datasets and .github/workflows folder have been created
    os.makedirs('datasets', exist_ok=True)
    os.makedirs('.github/workflows', exist_ok=True)

    sparql_endpoint = click.prompt(click.style('[?]', bold=True) 
            + ' Provide the SPARQL endpoint where to access the dataset')
    dataset_id = click.prompt(click.style('[?]', bold=True) 
            + ' Enter the identifier of your datasets, e.g. drugbank (lowercase, no space or weird characters)')
    distribution_uri = click.prompt(click.style('[?]', bold=True) 
            + ' Provide the URI of the dataset distribution')

    # Ask dataset metadata to the user and generate rdflib graph
    g, dataset_metadata = create_dataset_prompt(sparql_endpoint, distribution_uri)

    dataset_folder_path = 'datasets/' + dataset_id

    # Copy template folder with example mappings
    shutil.copytree(pkg_resources.resource_filename('d2s', 'templates/dataset'), dataset_folder_path)
    os.rename(dataset_folder_path + '/dataset-yourdataset.jsonld', dataset_folder_path + '/dataset-' + dataset_id + '.jsonld')
    # for filename in os.listdir(pkg_resources.resource_filename('d2s', 'templates/dataset')):
    #     with open(pkg_resources.resource_filename('d2s', 'queries/' + filename), 'r') as f:

    # Metadata file currently defined using an existing .jsonld file
    # os.makedirs(dataset_folder_path + '/metadata', exist_ok=True)
    # g.serialize(destination=dataset_folder_path + '/metadata-' + dataset_id + '.ttl', format='turtle')
    # g.serialize(destination=dataset_folder_path + '/metadata/' + dataset_id + '-metadata.jsonld', format='json-ld')
    # print("Metadata stored to " + dataset_folder_path + '/metadata-' + dataset_id + '.ttl' + ' 📝')

    # Replace metadata in all files from template for the new dataset (mainly for the dataset_id)
    for dname, dirs, files in os.walk(dataset_folder_path):
        for fname in files:
            fpath = os.path.join(dname, fname)
            with open(fpath) as f:
                file_content = f.read()
            for metadata_id, metadata_value in dataset_metadata.items():
                file_content = file_content.replace("$" + metadata_id, str(metadata_value))
            with open(fpath, "w") as f:
                f.write(file_content)

    # Copy example GitHub Actions workflow file, and replace dataset_id in it
    workflow_filepath = '.github/workflows/process-' + dataset_id + '.yml'
    shutil.copyfile(pkg_resources.resource_filename('d2s', 'templates/process-dataset.yml'), workflow_filepath)
    with open(workflow_filepath) as f:
        file_content = f.read()
        file_content = file_content.replace("$dataset_id", dataset_id)
    with open(workflow_filepath, "w") as f:
        f.write(file_content)

    click.echo()
    click.echo(click.style('[d2s]', bold=True) + ' Metadata, example mapping files and scripts for the ' 
        + click.style(dataset_id + ' dataset', bold=True) 
        + ' has been generated')
    click.echo(click.style('[d2s]', bold=True) + ' 📝 Start edit them in ' + click.style('datasets/' + dataset_id, bold=True))
    click.echo(click.style('[d2s]', bold=True) + ' 🐈 GitHub Actions workflow file in ' + click.style(workflow_filepath, bold=True))


def get_config():
    """Show the project configuration"""
    click.echo(click.style('[d2s]', bold=True) + ' Configuration is stored in the ' 
        + click.style('.env', bold=True) + ' file:')
    click.echo()
    with open('.env') as f:
        click.echo(f.read())


## Configure GraphDB triplestore docker deployment
# user_home_dir = str(Path.home())
# click.echo()
# shutil.copy(pkg_resources.resource_filename('d2s', 'templates/graphdb-repo-config.ttl'), 'workspace/graphdb/preload-config.ttl')
# # Copy GraphDB zip file to the right folder in d2s-core
# click.echo(click.style('[d2s]', bold=True) + ' The GraphDB triplestore needs to be downloaded for licensing reason.\n'
#     + 'Go to ' 
#     + click.style('https://ontotext.com/products/graphdb/', bold=True) 
#     + ' and provide your email to receive the URL to download the ' + click.style('GraphDB latest version standalone zip', bold=True))
# graphdb_version = click.prompt(click.style('[?]', bold=True) + ' Enter the version of the GraphDB triplestore used. Default', default='9.3.0')
# dotenv.set_key('.env', 'GRAPHDB_VERSION', graphdb_version, quote_mode="noquote")
# graphdb_heap_size = click.prompt(click.style('[?]', bold=True) + ' Enter the Java heap size allocated to GraphDB. Default', default='2G')
# dotenv.set_key('.env', 'GRAPHDB_HEAP_SIZE', graphdb_heap_size, quote_mode="noquote")
# graphdb_path = click.prompt(click.style('[?]', bold=True) + ' Enter the path to the GraphDB ' + graphdb_version + ' zip file that will be used to build the Docker image. Default', default=user_home_dir + '/graphdb-free-' + graphdb_version + '-dist.zip')
# # Get GraphDB installation file
# if os.path.exists(graphdb_path):
#     shutil.copy(graphdb_path, 'd2s-core/support/graphdb')
#     click.echo(click.style('[d2s]', bold=True) + ' GraphDB installation file copied imported successfully!')
# else:
#     click.echo(click.style('[d2s]', bold=True) + ' GraphDB installation file not found. Copy the zip file in d2s-core/support/graphdb after download.')
