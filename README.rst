======================
CKAN Storage Extension
======================

This extension adds:

  * Some new methods to the CKAN API for dealing with storage
  * A /storage/upload page to web interface for doing file uploads
  
It uses `OFS`_ to talk to the backing storage so can support anything that OFS
supports including local filesytem, S3, Google Storage etc.

.. _OFS: http://pypi.python.org/pypi/ofs/

In your config you need something like::

   ckan.plugins = storage
   # this is for google storage
   ofs.impl = google
   ofs.gs_access_key_id = GOOGCABCDASDASD
   ofs.gs_secret_access_key = 134zsdfjkw4234addad
   ckanext.storage.bucket = the bucket to use for uploading
   ckanext.storage.max_content_length = [optional] maximum content size for uploads (defaults to 50Mb)


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
    :param kwargs: sent either via query string for GET or json-encoded
        dict for POST. Possible key values are as for arguments to this
        underlying method:
        http://boto.cloudhackers.com/ref/s3.html?highlight=s3#boto.s3.connection.S3Connection.build_post_form_args

    :return: json-encoded dictionary with action parameter and fields list.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

