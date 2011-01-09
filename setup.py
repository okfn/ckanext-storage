from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
    name='ckanext-storage',
    version=version,
    description="CKAN API Extension for OFS Storage",
    long_description="""\
    """,
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
        "boto",
        "ofs",
    ],
    entry_points=\
    """
    [ckan.plugins]
    # Add plugins here, eg
    storage=ckanext.storage:Storage
    """,
)
