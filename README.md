[![Build](https://github.com/MaastrichtU-IDS/d2s-cli/workflows/Test%20and%20publish%20package/badge.svg)](https://github.com/MaastrichtU-IDS/d2s-cli/actions?query=workflow%3A%22Test+and+publish+package%22) [![Version](https://img.shields.io/pypi/v/d2s)](https://pypi.org/project/d2s)

A Command Line Interface to help orchestrate the integration of heterogenous data sources under a common [RDF Knowledge Graph](https://www.w3.org/RDF/) using Python, RML mappings, Bash, and GitHub Actions workflows (YAML). 

We also provide guidelines and help to deploy of user-facing services over the integrated data using [Docker](https://www.docker.com/) ([SPARQL](https://yasgui.triply.cc/), [BioThings APIs](https://biothings.io/explorer/), [GraphQL-LD](https://comunica.github.io/Article-ISWC2018-Demo-GraphQlLD/), [OpenAPI](https://www.openapis.org/), [Web UI](https://github.com/MaastrichtU-IDS/into-the-graph)).

## Installation 

Complete documentation about the `d2s-cli` on the [d2s documentation website 📖](https://d2s.semanticscience.org/docs/d2s-installation)

Requirements:

* [Python 3.6+](https://d2s.semanticscience.org/docs/d2s-installation#install-pip) (built using [python:3.6](https://github.com/MaastrichtU-IDS/d2s-cli/blob/master/publish.Dockerfile))
* [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
* Optional: Java 11+ to use `d2s sparql upload`
* Optional: [`oc` command line tool](https://maastrichtu-ids.github.io/dsri-documentation/docs/openshift-install) for deploying to the [DSRI OpenShift cluster](https://maastrichtu-ids.github.io/dsri-documentation/) (for Maastricht University academics and students)

### Install from pypi

```bash
pip install d2s
```

> Use [pip](https://pypi.org/project/pip/), pip3 or [pipx](https://pipxproject.github.io/pipx/) depending on your system preferences.

You can also install it from the `master` branch, if you want the latest updates:

```bash
pip install git+https://github.com/MaastrichtU-IDS/d2s-cli.git@master
```

> See [those instructions to install d2s on Windows](/docs/d2s-installation#install-pipx-on-windows) using the [Chocolatey package manager](https://chocolatey.org/) and [pipx](https://pipxproject.github.io/pipx/). 

### Install d2s for development

Install `d2s` as executable in local for development. 

`d2s` will be updated directly on change in the code.

```bash
pip install -e .
```

### Try it

Display the default help command

```bash
d2s
```

Create a d2s project in the given folder 

```bash
d2s init project-folder-name
```

All `d2s` commands are designed to be run from the project folder, move to it

```shell
cd project-folder-name/
```

> Project settings stored if `.d2sconfig` file.

### Update d2s installation

```bash
pip install --upgrade d2s 
```

### Uninstall

```bash
pip uninstall d2s
```

### Enable autocompletion

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

* **Bash**: add the import autocomplete line to the `~/.bashrc` file.

```bash
echo 'eval "$(_D2S_COMPLETE=source d2s)"' >> ~/.bashrc
```

> **To be tested.**

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

You might need to install Python3.6 for dev (dev with python3.6 should work though)

```bash
sudo apt-get install python3.6 python3.6-venv python3.6-dev
# Set python3 to use 3.6
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 1
sudo update-alternatives --config python3
```

> ```bash
>vim /usr/bin/gnome-terminal
> 
> #!/usr/bin/python3.6
> ```

If you face issue uploading the package on pypi:

```bash
twine check dist/d2s-*-py3-none-any.whl
```
