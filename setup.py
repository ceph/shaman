# -*- coding: utf-8 -*-
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='shaman',
    version='0.1',
    description='',
    author='Alfredo Deza',
    author_email='adeza@redhat.com',
    license = "MIT",
    install_requires=[
        "pecan",
        "sqlalchemy",
        "psycopg2",
        "pecan-notario",
        "requests",
        "jinja2",
        "pika",
    ],
    test_suite='shaman',
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(exclude=['ez_setup']),
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Utilities',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
    ],
    entry_points="""
        [pecan.command]
        populate=shaman.commands.populate:PopulateCommand
        """

)
