#!/usr/bin/env python3

from setuptools import setup,find_packages

long_desc = '''autopwn is designed to make a pentester's life easier and more consistent by allowing them to specify tools they would like to run against targets, without having to type them in a shell or write a script. This tool will probably be useful during certain exams as well..
Originally created by Aidan Marlin'''

setup(
    name='autopwn',
    version='2.0.0',
    description='Specify targets and run sets of tools against them',
    long_description=long_desc,
    author='Steven van der Baan',
    author_email='steven.vanderbaan@nccgroup.trust',
    url='https://github.com/nccgroup/autopwn',
    license='GNU Affero GPL v3',
    # packages=['autopwn2', 'autopwn2.api','autopwn2.api.endpoints','autopwn2.commands','autopwn2.database','autopwn2.schedule'],
    packages=find_packages(),
    package_data={
        '': ['*.conf'],
    },
    install_requires=[
        # 'PyYAML', 'screenutils', 'inquirer', 'readchar', 'Flask', 'Flask-RESTful', ' aniso8601', 'pytz'
        'Flask-restplus', 'flask-sqlalchemy', 'flask-apscheduler', 'click_shell', 'requests', 'pysqlite3'
    ],
    include_package_data=True,
    zip_safe=False,
    entry_points={'console_scripts': ['autopwn = autopwn2.app:main', 'autopwn-cli = autopwn2.cli:cli']},
    classifiers=[
        'Programming Language :: Python :: 3',
        'Intended Audience :: Information Technology',
        'Topic :: Security',
        'Environment :: Console'],
    keywords='autopwn pentest automate toolset hack',
)
