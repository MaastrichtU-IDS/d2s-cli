Install Poetry

```bash
pip install poetry
```

Install dependencies

```bash
poetry install
```

Add dependencies:

```bash
poetry add click cwltool
```

Run using Poetry

```bash
poetry run d2s start virtuoso
```

Publish

https://codingdose.info/2019/06/16/develop-and-publish-with-poetry/

```bash
poetry build

# https://pypi.org/account/register/
poetry publish
```

Install the tool

```bash
pip install d2s
```

# Try with setuptools

```bash
# Install package
pip install package && pip freeze > requirements.txt
```

Install `d2s` as cli in local
```bash
pip3 install --editable .
```

Build packages
```bash
python3 setup.py sdist bdist_wheel
```

Publish
```bash
pipx install twine
twine upload --repository-url https://upload.pypi.org/legacy/ dist/*
```