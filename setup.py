from setuptools import setup, find_packages
import sys, os

version = '0.4'
try:
    long_description = open('README.txt').read()
except:
    long_description = ''

setup(
    name='ckanext-storage',
    version=version,
    description="CKAN API Extension for OFS Storage",
    long_description=long_description,
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Open Knowledge Foundation',
    author_email='okfn-dev@lists.okfn.org',
    url='http://okfn.org/',
    license='AGPL',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # google storage support only appeared in 2.0
        # note that lucid packages 1.9
        "boto>=2.0b1",
        "ofs>=0.4",
    ],
    entry_points=\
    """
    [ckan.plugins]
    storage=ckanext.storage:Storage
    """,
)
