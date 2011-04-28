This adds some bits to the CKAN API for dealing with storage. It uses OFS to
talk to the backing storage so can support anything that OFS supports including
local filesytem, S3, Google Storage etc.

In your config you need something like::

   ckan.plugins = storage
   # this is for google storage
   ofs.impl = google
   ofs.gs_access_key_id = GOOGCABCDASDASD
   ofs.gs_secret_access_key = 134zsdfjkw4234addad

Then there will some new API methods::

     /api/storage/metadata/<bucket>/<label>
     /api/storage/auth/{type}/<bucket>/<label>

Metadata API
------------

     /api/storage/metadata/<bucket>/<label>

  * GET will return the metadata
  * POST will add/update metadata
  * PUT will replace metadata


Auth API
--------

Get credentials for doing operations on storage (usually directly)::

    /api/storage/auth/{request|form}/{bucket}/{label}

Details in docstrings in ckanext/storage/controller.py.

