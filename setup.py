from setuptools import setup, Extension
import setuptools
import codecs

# with codecs.open("README.md", "r", "utf-8") as file:
#     long_description = file.read()

setup(
    name='d2s',
    version='0.1.8',
    license="MIT license",
    url="https://github.com/MaastrichtU-IDS/d2s-cli",
    author="Vincent Emonet",
    author_email="vincent.emonet@gmail.com",
    description="A Command Line Interface to orchestrate the integration of heterogenous data and the deployment of services consuming the integrated data. See https://d2s.semanticscience.org",
    long_description_content_type="text/markdown",
    long_description=open('README.md').read(),
    # long_description=long_description,
    packages=setuptools.find_packages(),
    py_modules=['d2s'],
    install_requires=[
        'Click', 'cwltool',
    ],
    entry_points={
        'console_scripts': [
            'd2s=d2s:cli'
        ]
    },
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    )
)

