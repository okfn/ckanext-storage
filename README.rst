This extension adds:

  * Some new methods to the CKAN API for dealing with storage
  * An /upload page to web interface for doing file uploads
  
It uses OFS to talk to the backing storage so can support anything that OFS
supports including local filesytem, S3, Google Storage etc.

In your config you need something like::

   ckan.plugins = storage
   # this is for google storage
   ofs.impl = google
   ofs.gs_access_key_id = GOOGCABCDASDASD
   ofs.gs_secret_access_key = 134zsdfjkw4234addad

Then there will some new API methods::

     /api/storage/metadata/<bucket>/<label>
     /api/storage/auth/{type}/<bucket>/<label>

And a new upload page at /upload.

Metadata API
------------

     /api/storage/metadata/<label>

  * GET will return the metadata
  * POST will add/update metadata
  * PUT will replace metadata


Auth API
--------

Get credentials for doing operations on storage (usually directly)::

    /api/storage/auth/{request|form}/{label}

Details in docstrings in ckanext/storage/controller.py or by visiting
api/storage when running this extension.

