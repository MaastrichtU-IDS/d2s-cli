A Command Line Interface to orchestrate the integration of heterogenous data sources under a common [RDF Knowledge Graph](https://www.w3.org/RDF/) using [CWL workflows](https://www.commonwl.org/), and the deployment of user-facing services over the integrated data using [Docker](https://www.docker.com/) ([SPARQL](https://yasgui.triply.cc/), [GraphQL-LD](https://comunica.github.io/Article-ISWC2018-Demo-GraphQlLD/), [OpenAPI](https://www.openapis.org/), [Web UI](https://github.com/MaastrichtU-IDS/into-the-graph)).

## Installation 

More detailed instruction on the [d2s documentation website](https://d2s.semanticscience.org/docs/d2s-installation).

### Install with pip

```bash
pip install d2s cwlref-runner
```

> Use [pip](https://pypi.org/project/pip/), pip3 or [pipx](https://pipxproject.github.io/pipx/) depending on your system preferences.

Requirements:

* [Python 3.6](https://d2s.semanticscience.org/docs/d2s-installation#install-pip)
* [docker-compose](https://docs.docker.com/compose/install/)
* git
* curl

### Enable autocompletion

Enable commandline autocompletion in the terminal

> Highly recommended, it makes `d2s` much more user-friendly

* **Bash**: add the import autocomplete line to `.bashrc`

```bash
echo 'eval "$(_D2S_COMPLETE=source d2s)"' >> ~/.bashrc
```

> `nano .bashrc` if issues with the import 

* **ZSH**: add the import autocomplete line to `.zshrc`

```bash
echo 'eval "$(_D2S_COMPLETE=source_zsh d2s)"' >> ~/.zshrc
```

> `nano .zshrc` if issues with the import 

## Try it

Display the default help command

```bash
d2s
```

Create a d2s project in the current directory

```bash
d2s init
```

# Development setup

```bash
# Add new package
pip install package && pip freeze > requirements.txt
```

### Install for dev

Install `d2s` as cli in local for dev. `d2s` will be updated directly on change.

```bash
pip install --editable .
```

Recommended script to build and publish automatically using Docker:

```bash
./publish_pip.sh
```

Or do it locally 

```bash
# Build packages in dist/
python3 setup.py sdist bdist_wheel
# Publish the built dist/ directory
twine upload --repository-url https://upload.pypi.org/legacy/ dist/*
```

You might need to install twine

```bash
pipx install twine
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

If you face issue uploading the package on pypi

```bash
twine check dist/d2s-*-py3-none-any.whl
```