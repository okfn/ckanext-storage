======================
CKAN Storage Extension
======================

This extension adds:

  * Some new methods to the CKAN API for dealing with storage
  * A /storage/upload page to web interface for doing file uploads
  
It uses `OFS`_ to talk to the backing storage so can support anything that OFS
supports including local filesytem, S3, Google Storage etc.

.. _OFS: http://packages.python.org/ofs/

Installation
============

Install the extension::

    # using pip (could use easy_install)
    pip install ckanext-storage
    # could install from source
    # hg clone https://bitbucket.org/okfn/ckanext-storage
    # cd ckanext-storage
    # pip install -e .

Note that for use of S3-like backends (S3, Google Storage etc) you will need boto (this is installed by default at the moment). For local filesystem backend you need to install pairtree (`pip install pairtree`).

In your config you need something like::

   ckan.plugins = storage

   ## OFS configuration
   ## This is for google storage. Example for another backend is below
   ## See OFS docs for full details
   ofs.impl = google
   ofs.gs_access_key_id = GOOGCABCDASDASD
   ofs.gs_secret_access_key = 134zsdfjkw4234addad
   ## bucket to use in storage You *must* set this
   ckanext.storage.bucket = ....

   ## optional
   ## maximum content size for uploads in bytes, defaults to 1Gb
   # ckanext.storage.max_content_length = 1000000000
   ## prefix for all keys. Useful because we may use a single bucket and want to
   ## partition file uploads. Defaults to file/
   # ckanext.storage.key_prefix = file/

For local file storage you would replace ofs arguments with::

   ofs.impl = pairtree
   ofs.storage_dir = /my/path/to/storage/root/directory

If when uploading and using the local file storage you receive a 
pairtree.storage_exceptions.NotAPairtreeStoreException exception then 
you need to let pairtree know that your chosen folder (ofs.storage_dir) is 
a store.  You can do this by creating a file in the ofs.storage_dir called 
pairtree_version0_1 which can be empty as it is only a marker.


Upload Web Interface
====================

There will be a new upload page at /storage/upload. 

Metadata API
============

The API is located at::

     /api/storage/metadata/{label}

It supports the following methods:

  * GET will return the metadata
  * POST will add/update metadata
  * PUT will replace metadata

Metadata is a json dict of key values which for POST and PUT should be send in body of request.

A standard response looks like::

    {
      "_bucket": "ckannet-storage",
      _content_length: 1074
      _format: "text/plain"
      _label: "/file/8630a664-0ae4-485f-99c2-126dae95653a"
      _last_modified: "Fri, 29 Apr 2011 19:27:31 GMT"
      _location: "some-location"
      _owner: null
      uploaded-by: "bff737ef-b84c-4519-914c-b4285144d8e6"
    }

Note that values with '_' are standard OFS metadata and are mostly read-only -- _format i.e. content-type can be set).


Auth API
========

Get credentials for doing operations on storage directly.


Request Authentication
----------------------

The API is at::

    /api/storage/auth/request/{label}

Provide authentication information for a request so a client can
interact with backend storage directly::

    :param label: label.
    :param kwargs: sent either via query string for GET or json-encoded
        dict for POST). Interpreted as http headers for request plus an
        (optional) method parameter (being the HTTP method).

        Examples of headers are:

            Content-Type
            Content-Encoding (optional)
            Content-Length
            Content-MD5
            Expect (should be '100-Continue')

    :return: is a json hash containing various attributes including a
    headers dictionary containing an Authorization field which is good for
    15m.

Form Authentication
-------------------

The API is located at::

    /api/storage/auth/form/{label}

Provide fields for a form upload to storage including authentication::

    :param label: label.
    :return: json-encoded dictionary with action parameter and fields list.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

