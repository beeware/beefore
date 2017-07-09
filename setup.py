#!/usr/bin/env python
import io
import re
from setuptools import setup, find_packages


with io.open('./beefore/__init__.py', encoding='utf8') as version_file:
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file.read(), re.M)
    if version_match:
        version = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string.")


with io.open('README.rst', encoding='utf8') as readme:
    long_description = readme.read()


setup(
    name='beefore',
    version=version,
    description='Performs pre-merge checks (such as code style) on a pull request.',
    long_description=long_description,
    author='Russell Keith-Magee',
    author_email='russell@keith-magee.com',
    url='http://pybee.org/beefore',
    keywords=['lint', 'merge', 'dco'],
    packages=find_packages(exclude=['tests']),
    entry_points={
        'console_scripts': [
            'beefore = beefore.command:main',
        ]
    },
    install_requires=[
        'github3.py',
        'PyYAML',
        'flake8>=3.0.0b2',
    ],
    license='New BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
    test_suite='tests'
)
