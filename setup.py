from setuptools import setup
import setuptools

setup(
    name='d2s',
    version='0.3.3',
    license="MIT License",
    url="https://github.com/MaastrichtU-IDS/d2s-cli",
    author="Vincent Emonet",
    author_email="vincent.emonet@gmail.com",
    description="A Command Line Interface to orchestrate the integration of heterogenous data and the deployment of services consuming the integrated data. See https://d2s.semanticscience.org",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    # package_dir={'': 'src'},
    package_data={'': [ 'queries/*', 'queries/hcls/*', 'queries/bio2rdf/*', 
                        'templates/*', 'templates/project/*', 'templates/dataset/*',
                        'templates/dataset/mapping/*', 'templates/dataset/scripts/*']},
    # package_data={'': ['queries/**', 
    #                     'templates/**']},
    include_package_data=True,
    # py_modules=['d2s'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    install_requires=open("requirements.txt", "r").readlines(),
    entry_points={
        'console_scripts': [
            'd2s=d2s.__main__:cli',
        ],
    },
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9"
    ],
    project_urls={
        "Issues": "https://github.com/MaastrichtU-IDS/d2s-cli/issues",
        "Source Code": "https://github.com/MaastrichtU-IDS/d2s-cli",
        "CI": "https://github.com/MaastrichtU-IDS/d2s-cli/actions",
        "Releases": "https://github.com/MaastrichtU-IDS/d2s-cli/releases"
    },
)
