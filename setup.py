from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md')) as f:
    long_description = f.read()

setup(
    name='django-boilerplate',

    version='1.0',

    description='Django tools for reducing boilerplate code',
    long_description=long_description,

    url='https://github.com/hottwaj/django-boilerplate',

    author='Jonathan Clarke',
    author_email='jonathan.a.clarke@gmail.com',

    license='Copyright 2020',

    classifiers=[
    ],

    keywords='',

    packages=["django_boilerplate"],
    
    install_requires=[
    ],
)