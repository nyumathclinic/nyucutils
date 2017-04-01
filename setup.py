#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Click>=6.0',
    'lxml>=3.7.2',
    'Pandas>=0.19.2'
    # TODO: put package requirements here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='nyucutils',
    version='0.1.0',
    description="A suite of tools for various NYU learning content management systems",
    long_description=readme + '\n\n' + history,
    author="Matthew Leingang",
    author_email='leingang@nyu.edu',
    url='https://github.com/nyumathclinic/nyucutils',
    packages=[
        'nyucutils',
    ],
    package_dir={'nyucutils':
                 'nyucutils'},
    entry_points={
        'console_scripts': [
            'wacv2csv=nyucutils.vendors.webassign:assignments_from_html_to_csv',
            'wa2nyuc=nyucutils.vendors.webassign:wagb_to_nyucgb',
            'nyuc2gs=nyucutils.vendors.gradescope:munge',
            'gs2nyuc=nyucutils.vendors.gradescope:gs2nyuc'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='nyucutils',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
