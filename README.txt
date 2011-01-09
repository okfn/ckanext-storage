This adds some bits to the CKAN API for dealing with storage.

In your config you need something like:

   ckan.plugins = storage
   ofs.impl = google
   ofs.gs_access_key_id = GOOGCABCDASDASD
   ofs.gs_secret_access_key = 134zsdfjkw4234addad

Then there will some new API methods

     /api/storage/metadata/<bucket>/<label>

	* GET will return the metadata
	* POST will add/update metadata
	* PUT will replace metadata

    /api/storage/auth/<bucket>/<label>

        * before using this a POST or PUT on the metadata method must have
	  been previously called to create the blob.

        * need to post relevant http headers encoded as json. important ones
	  are:

		Content-Type
		Content-Encoding (optional)
		Content-Length
		Content-MD5
		Expect (should be '100-Continue')

	* the response is a json object, a list, containing (host, headers) which
	  is the host to do a PUT operation on to upload the data, and the headers
	  have been filled in with credentials that are good for 15 minutes
