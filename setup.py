from setuptools import setup, find_packages
import jacobsjsonschema._version as _version

with open("README.md", "r") as fh:
    long_description = fh.read()

install_requires = []
with open("requirements.txt", "r") as fh:
    install_requires = [ x for x in fh.read().split("\n") if len(x) > 0 ]

setup(
    name="jacobs-json-schema",
    version=_version.__version__,
    description='Another JSON-Schema Validator',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Jacob Brunson",
    author_email="pypi@jacobbrunson.com",
    url="https://github.com/pearmaster/jacobs-json-schema",
    license='GPLv2',
    packages=find_packages(),
    install_requires=install_requires,
    keywords='conversion',
    classifiers= [
        "Programming Language :: Python :: 3",
    ],
    python_requires='>=3.5',
)