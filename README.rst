======================
CKAN Storage Extension
======================

This extension adds:

  * Some new methods to the CKAN API for dealing with storage
  * A /storage/upload page to web interface for doing file uploads
  
It uses OFS to talk to the backing storage so can support anything that OFS
supports including local filesytem, S3, Google Storage etc.

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

     /api/storage/metadata/{label}

  * GET will return the metadata
  * POST will add/update metadata
  * PUT will replace metadata

Metadata is a json dict like:

Auth API
========

Get credentials for doing operations on storage directly.


/api/storage/auth/request/{label}
---------------------------------

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

/api/storage/auth/form/{label}
------------------------------

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

