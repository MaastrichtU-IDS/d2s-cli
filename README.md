A Command Line Interface to orchestrate the integration of heterogenous data sources under a common [RDF Knowledge Graph](https://www.w3.org/RDF/) using [CWL workflows](https://www.commonwl.org/), and the deployment of user-facing services over the integrated data using [Docker](https://www.docker.com/) ([SPARQL](https://yasgui.triply.cc/), [GraphQL-LD](https://comunica.github.io/Article-ISWC2018-Demo-GraphQlLD/), [OpenAPI](https://www.openapis.org/), [Web UI](https://github.com/MaastrichtU-IDS/into-the-graph)).

## Installation 

Complete documentation about the `d2s-cli` on the [d2s documentation website 📖](https://d2s.semanticscience.org/docs/d2s-installation)

### Install with pipx

```bash
pipx install d2s cwlref-runner
```

> Use [pip](https://pypi.org/project/pip/), pip3 or [pipx](https://pipxproject.github.io/pipx/) depending on your system preferences.

Requirements:

* [Python 3.6](https://d2s.semanticscience.org/docs/d2s-installation#install-pip)
* [docker-compose](https://docs.docker.com/compose/install/)
* git, curl, time (bash)

### Enable autocompletion

Enable commandline autocompletion in the terminal

> Highly recommended, it makes `d2s` much more user-friendly 

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

### Upgrade package

With `pipx`:

```bash
pipx uninstall d2s
pipx install d2s
```

With `pip`:

```bash
pip install --upgrade d2s 
```

## Try it

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

# Development setup

Install package and add it to `requirements.txt`:

```bash
pip install package && pip freeze > requirements.txt
```

### Install for dev

Install `d2s` as executable in local for development. `d2s` will be updated directly on change in the code.

```bash
pip install --editable .
```

To publish a new version, upgrade the version in [setup.py](https://github.com/MaastrichtU-IDS/d2s-cli/blob/master/setup.py#L6) and use the following script to build and publish automatically using [Docker](https://docs.docker.com/install/):

```bash
./publish_pip.sh
```

Or do it locally:

```bash
# Build packages in dist/ folder
python3 setup.py sdist bdist_wheel
# Publish packages previously built in the dist/ folder
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

If you face issue uploading the package on pypi:

```bash
twine check dist/d2s-*-py3-none-any.whl
```