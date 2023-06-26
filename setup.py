#!/usr/bin/env python3

from setuptools import find_packages, setup

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("requirements.txt") as requirements_file:
    requirements = requirements_file.readlines()

setup(
    name="vmm-export",
    author="awk",
    author_email="awk@awk.space",
    version="1.0.0",
    description="Automatically export VMs from Synology VMM.",
    long_description=readme,
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://github.com/awkspace/vmm-export",
    install_requires=requirements,
    packages=find_packages(),
    entry_points={"console_scripts": ["vmm-export = vmm_export.cli:main"]},
)
