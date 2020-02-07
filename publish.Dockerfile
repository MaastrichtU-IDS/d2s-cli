FROM python:3.6

WORKDIR /build

RUN pip install twine

COPY *.py ./
COPY *.md ./
COPY LICENSE ./

RUN python3 setup.py sdist bdist_wheel

CMD ["twine", "upload", "--repository-url", "https://upload.pypi.org/legacy/", "dist/*"]
