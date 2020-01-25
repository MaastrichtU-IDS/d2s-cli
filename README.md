## Install 

### With pip

```bash
pip install d2s
```

> Use [pip](https://pypi.org/project/pip/), pip3 or [pipx](https://pipxproject.github.io/pipx/) depending on your preferences.

Requirements:

* docker-compose
* git
* curl

### Enable autocompletion

Enable commandline autocompletion in the terminal

> Highly recommended, it makes `d2s` much more user-friendly

* Bash
```bash
nano .bashrc
# Add the following line:
eval "$(_D2S_COMPLETE=source d2s)"
```

* ZSH
```bash
nano .zshrc
# Add the following line:
eval "$(_D2S_COMPLETE=source_zsh d2s)"
```

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
pip3 install --editable .
```

Build packages
```bash
python3 setup.py sdist bdist_wheel
```

Publish the built dist directory
```bash
twine upload --repository-url https://upload.pypi.org/legacy/ dist/*
```

You might need to install twine

```bash
pipx install twine
```

