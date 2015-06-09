#!/usr/bin/env python3

from setuptools import setup

long_desc = '''autopwn is designed to make a pentester's life easier and more consistent by allowing them to specify tools they would like to run against targets, without having to type them in a shell or write a script. This tool will probably be useful during certain exams as well..'''


setup(
    name='autopwn',
    version='0.18.0',
    description='Specify pentest targets and run sets of tools against them',
    long_description=long_desc,
    author='Aidan Marlin',
    author_email='aidan.marlin@nccgroup.trust',
    url='https://github.com/nccgroup/autopwn',
    license='GNU Affero GPL v3',
    packages=['autopwn'],
    install_requires=[
        'PyYAML', 'screenutils', 'inquirer',
        'readchar<=0.7' # https://github.com/magmax/python-inquirer/issues/8
    ],
    include_package_data=True,
    zip_safe=False,
    entry_points={'console_scripts': ['autopwn = autopwn:main']},
    classifiers=[
        'Programming Language :: Python :: 3',
        'Intended Audience :: Information Technology',
        'Topic :: Security',
        'Environment :: Console']
)
