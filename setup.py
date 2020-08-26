from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md')) as f:
    long_description = f.read()

setup(
    name='django-snippets',

    version='0.5',
    
    python_requires='>3.7',

    description='Useful Django snippets, and tools for reducing boilerplate',
    long_description=long_description,

    url='https://github.com/hottwaj/django-snippets',

    author='Jonathan Clarke',
    author_email='jonathan.a.clarke@gmail.com',

    license='Copyright 2020',

    classifiers=[
    ],

    keywords='',

    packages=["django_snippets"],
    include_package_data=True,
    
    install_requires=[
        "django>=3.1",
        "django-import-export>=2.0",
    ],
)