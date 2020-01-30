from setuptools import setup
import setuptools

setup(
    name='d2s',
    version='0.1.5',
    url="https://github.com/MaastrichtU-IDS/d2s-cli",
    author="Vincent Emonet",
    author_email="vincent.emonet@gmail.com",
    description="A Command Line Interface for the Data2Services framework. See https://d2s.semanticscience.org/",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    packages=setuptools.find_packages(),
    py_modules=['d2s'],
    install_requires=[
        'Click', 'cwltool',
    ],
    entry_points='''
        [console_scripts]
        d2s=d2s:cli
    ''',
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ),
)

