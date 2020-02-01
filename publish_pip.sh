#!/bin/bash

rm -r dist/

python3 setup.py sdist bdist_wheel

twine upload --verbose --repository-url https://upload.pypi.org/legacy/ dist/*