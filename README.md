[![Version](https://img.shields.io/pypi/v/d2s)](https://pypi.org/project/d2s) [![Test Python package](https://github.com/MaastrichtU-IDS/d2s-cli/actions/workflows/test.yml/badge.svg)](https://github.com/MaastrichtU-IDS/d2s-cli/actions/workflows/test.yml) [![Publish Python package](https://github.com/MaastrichtU-IDS/d2s-cli/actions/workflows/publish.yml/badge.svg)](https://github.com/MaastrichtU-IDS/d2s-cli/actions/workflows/publish.yml)

A Command Line Interface to help orchestrate the integration of heterogenous data sources under a common [RDF Knowledge Graph](https://www.w3.org/RDF/) using Python, RML mappings, Bash, and GitHub Actions workflows (YAML). 

You can find more informations about the Data2Services project on the [d2s documentation website 📖](https://d2s.semanticscience.org/docs/d2s-installation)

## Installation 

Requirements:

* [Python 3.7+](https://d2s.semanticscience.org/docs/d2s-installation#install-pip)
* [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
* Optional: Java 11+ to use `d2s sparql upload`
* Optional: [`oc` command line tool](https://maastrichtu-ids.github.io/dsri-documentation/docs/openshift-install) for deploying to the [DSRI OpenShift cluster](https://maastrichtu-ids.github.io/dsri-documentation/) (for Maastricht University academics and students)

<!-- COMMENTED

### Install from pypi

```bash
pip install d2s
```

> Use [pip](https://pypi.org/project/pip/), pip3 or [pipx](https://pipxproject.github.io/pipx/) depending on your system preferences.

### Update

```bash
pip install --upgrade d2s 
```

### Install from GitHub branch

You can also install it from the `master` branch, if you want the latest updates:

```bash
pip install git+https://github.com/MaastrichtU-IDS/d2s-cli.git@master
```

> See [those instructions to install d2s on Windows](/docs/d2s-installation#install-pipx-on-windows) using the [Chocolatey package manager](https://chocolatey.org/) and [pipx](https://pipxproject.github.io/pipx/). 

-->

### Install d2s

Install `d2s` as executable to run it from the terminal

Clone the repository:

```bash
git clone https://github.com/MaastrichtU-IDS/d2s-cli.git
cd d2s-cli
```

Install `d2s`:

```bash
pip install -e .
```

> `d2s` will be updated directly on change in the code.

#### Optional: isolate with a Virtual Environment

If you face conflicts with already installed packages, then you might want to use a [Virtual Environment](https://docs.python.org/3/tutorial/venv.html) to isolate the installation in the current folder before installing `d2s`:

```bash
# Create the virtual environment folder in your workspace
python3 -m venv .venv
# Activate it using a script in the created folder
source .venv/bin/activate
```

### Uninstall

```bash
pip uninstall d2s
```

## Use d2s

Display the default help command

```bash
d2s
```

### Generate metadata

Analyze a SPARQL endpoint metadata to generate [HCLS descriptive metadata](https://www.w3.org/TR/hcls-dataset/) for each graph:

```bash
d2s metadata analyze https://graphdb.dumontierlab.com/repositories/umids-kg -o metadata.ttl
```

Analyze a SPARQL endpoint metadata to generate metadata specific to Bio2RDF for each graph:

```bash
d2s metadata analyze https://bio2rdf.137.120.31.102.nip.io/sparql -o metadata.ttl -m bio2rdf
```

You can also generate detailed HCLS metadata for the dataset version and distribution by answering the questions after running this command:

```bash
d2s metadata create -o metadata.ttl
```

### Bootstrap a datasets conversion project

`d2s` can be used to help you converting datasets to RDF.

You will need to initialize the current folder, it is highly recommended to do this at the root of a Git repository where the conversion will be stored:

```bash
d2s init
```

This command will create a `datasets` folder to store the datasets conversions and a `.github/workflows` folder for the workflows, if it does not exist already. 

> All `d2s` commands are designed to be run from the project folder

You can create a new dataset conversion:

```bash
d2s new dataset
```

You will be asked a few questions about the dataset via the terminal, then a folder will be generated with:

* Your dataset metadata
* Example YARRRML and RML mappings
* Example python preprocessing script
* Example bash script to download the data to convert
* A GitHub Action workflow to run the different steps of the processing

You can now edit the file generated in the `datasets` folder to implement your data conversion.

### Run the RML mapper

Requirements: Java installed

This feature is still experimental

`d2s` can be used to easily run the RML mapper:

```bash
d2s rml my-dataset
```

## Enable autocompletion

Enable commandline autocompletion in the terminal

> Recommended, it makes `d2s` much more user-friendly 

* **ZSH**: add the import autocomplete line to the `~/.zshrc` file.

```bash
echo 'eval "$(_D2S_COMPLETE=source_zsh d2s)"' >> ~/.zshrc
```

> Set your terminal to use [ZSH](https://github.com/ohmyzsh/ohmyzsh/wiki/Installing-ZSH) by default:
>
> ```shell
> chsh -s /bin/zsh
> ```

> A [oh-my-zsh](https://ohmyz.sh/) theme can be easily chosen for a personalized experience. See [the zsh-theme-biradate](https://github.com/vemonet/zsh-theme-biradate) to easily install a simple theme and configure your terminal in a few minutes.

* **Bash**: add the import autocomplete line to the `~/.bashrc` file. Something like this probably:

```bash
echo 'eval "$(_D2S_COMPLETE=source d2s)"' >> ~/.bashrc
```

## Build and publish

### Publish using Docker

To publish a new version on [pypi](https://pypi.org/project/d2s/):

* upgrade the version in [setup.py](https://github.com/MaastrichtU-IDS/d2s-cli/blob/master/setup.py#L6) (e.g. from `0.2.1` to `0.2.2`)
* use the following script to build and publish automatically using [Docker](https://docs.docker.com/install/):

```bash
./publish_pip.sh
```

> A test will be run using Docker before publishing to make sure `d2s init` works.

### Build locally

Building and publishing can be done locally:

```bash
# Build packages in dist/ folder
python3 setup.py sdist bdist_wheel
# Publish packages previously built in the dist/ folder
twine upload --repository-url https://upload.pypi.org/legacy/ dist/*
```

Additional instructions to install twine locally (not needed)

```bash
pip install twine
```

> If you experience issues with Bash or ZSH because `d2s` is not defined when installing for dev. Then add `pip install --editable develop/d2s-cli` to `.zshrc`

You might need to install Python3.7 for dev (dev with python3.7 should work though)

```bash
sudo apt-get install python3.7 python3.7-venv python3.7-dev
# Set python3 to use 3.7
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 1
sudo update-alternatives --config python3
```

> ```bash
>vim /usr/bin/gnome-terminal
> 
> #!/usr/bin/python3.7
> ```

If you face issue uploading the package on pypi:

```bash
twine check dist/d2s-*-py3-none-any.whl
```
