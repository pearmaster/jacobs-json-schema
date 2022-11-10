from setuptools import setup, find_packages
import jacobsjsonschema._version as _version

with open("README.md", "r") as fh:
    long_description = fh.read()

install_requires = []
try:
    with open("requirements.txt", "r") as fh:
        install_requires = [ x for x in fh.read().split("\n") if len(x) > 0 ]
except FileNotFoundError:
    pass

setup(
    name="jacobs-json-schema",
    version=_version.__version__,
    description='Another JSON-Schema Validator',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Jacob Brunson",
    author_email="pypi@jacobbrunson.com",
    url="https://github.com/pearmaster/jacobs-json-schema",
    license='MIT',
    packages=find_packages(),
    install_requires=install_requires,
    keywords=['json schema', 'validation', 'data validation', 'json'],
    classifiers= [
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires='>=3.5',
)