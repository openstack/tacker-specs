=====================================
Add artifacts support for vnf package
=====================================
https://blueprints.launchpad.net/tacker/+spec/add-artifacts-vnf-packages

This specification describes enhancement of VNF Packages Management in
Tacker.

Problem description
===================

In ``Train`` and ``Ussuri`` release, we have added limited support of VNF
Package Management as defined in ETSI NFV-SOL 005 `etsi_sol005`_
as described in `spec1`_ and `spec2`_. Now, we want to extend that support
and implement reading artifacts information from TOSCA.meta and manifest files
present inside CSAR package as described in ETSI NFV-SOL 004 `etsi_sol004`_
during uploading of the VNF
package.

Proposed change
===============

To add artifacts support in VNF packages, we will need to make changes in the
following components:

* Tacker API and Conductor service

  * Read the artifacts information from TOSCA.meta and Manifest file while
    uploading vnf packages and store it in the new db table as described in
    `Data model Impact`_.
  * Modify ``GET /vnf_packages/{vnfPkgId}`` REST API to include
    ``additionalArtifacts`` parameter in the response.
  * Add a new REST API
    ``GET /vnf_packages/{vnfPkgId}/artifacts/{artifactPath}``
    to fetch individual artifact in an on-boarded VNF package.
  * Read and verify artifacts information from TOSCA.meta and manifest file.

* python-tackerclient

  * Modify ``vnf package show`` command to display ``additionalArtifacts``
    information.
  * Add new OSC command ``vnf package artifact`` to fetch individual artifact
    in an on-boarded VNF package.

Read artifacts information from TOSCA.meta and Manifest File
------------------------------------------------------------

Artifacts information can be found in CSAR package in the following types
of files:-

1. TOSCA.meta

   If CSAR package contains TOSCA.meta file, it's possible to specify artifacts
   information as shown below::

     TOSCA-Meta-File-Version: 1.0
     Created-by: Author_name
     CSAR-Version: 1.1
     Entry-Definitions: Definitions/root.yaml

     Source: MRF.yaml
     Algorithm: SHA-256
     Hash: 09e5a788acb180162c51679ae4c998039fa6644505db2415e35107d1ee213943

     Source: scripts/install.sh
     Algorithm: SHA-256
     Hash: d0e7828293355a07c2dccaaa765c80b507e60e6167067c950dc2e6b0da0dbd8b

     Source: https://www.vendor_org.com/MRF/v4.1/scripts/scale/scale.sh
     Algorithm: SHA-256
     Hash: 36f945953929812aca2701b114b068c71bd8c95ceb3609711428c26325649165

     Source: Files/images/cirros.img
     Algorithm: SHA-256
     Hash: 9569dfc57e26436315180cb61f2d0d45c0de7c0ddb47d5759271ae825dc3acab

.. note:: In case, the source is referred in any of VNFDs under the ``artifacts``
          properties of type ``tosca.nodes.nfv.Vdu.VirtualBlockStorage`` and
          ``tosca.nodes.nfv.Vdu.Compute`` and if artifact type is
          ``tosca.artifacts.nfv.SwImage`` or it's derived from type
          ``tosca.artifacts.Deployment.Image``, then those artifacts should be
          ignored as software images shouldn't be included in
          ``additionalArtifacts`` as described in table 10.5.2.2
          `etsi_sol003`_.

.. note:: When an external resource having the ``Source`` of URI is provided in
          TOSCA.meta or manifest file, it should be stored in the vnf_artifacts
          DB table but it is not possible to fetch with the new API of
          ``GET /vnf_packages/{vnfPkgId}/artifacts/{artifactPath}`` because users
          can get it directly from the URI.

2. Manifest file

   A CSAR VNF package shall have a manifest file. The manifest file shall have an
   extension .mf and the same name as the main TOSCA definitions YAML file and be
   located at the root of the archive (archive without TOSCA-Metadata directory)
   or in the location specified by the TOSCA.meta file
   (archive with a TOSCA-Metadata directory). In the latter case, the corresponding
   entry shall be named "ETSI-Entry-Manifest".

   The manifest file shall start with the VNF package metadata in the form of
   a name-value pairs but in 'Victoria' release, we will ignore metadata section
   completely and only process the artifacts information as shown below::

     metadata:
       vnf_product_name: vMRF
       vnf_provider_id: Acme
       vnf_package_version: 1.0
       vnf_release_date_time: 2017-01-01T10:00:00+03:00

     Source: MRF.yaml
     Algorithm: SHA-256
     Hash: 09e5a788acb180162c51679ae4c998039fa6644505db2415e35107d1ee213943

     Source: scripts/install.sh
     Algorithm: SHA-256
     Hash: d0e7828293355a07c2dccaaa765c80b507e60e6167067c950dc2e6b0da0dbd8b

     Source: https://www.vendor_org.com/MRF/v4.1/scripts/scale/scale.sh
     Algorithm: SHA-256
     Hash: 36f945953929812aca2701b114b068c71bd8c95ceb3609711428c26325649165

     Source: Files/images/cirros.img
     Algorithm: SHA-256
     Hash: 9569dfc57e26436315180cb61f2d0d45c0de7c0ddb47d5759271ae825dc3acab

.. note:: In case, the source is referred in any of VNFDs under the artifacts
          and if artifact type is ``tosca.artifacts.nfv.SwImage`` or it's
          derived from type ``tosca.artifacts.Deployment.Image``, then those
          artifacts should be ignored. There is no provision made to specify
          ``metadata`` for artifact in manifest file so the ``metadata``
          returned for type ``VnfPackageArtifactInfo`` in ``additionalArtifacts``
          parameter will always be an empty dictionary.

3. Tosca definition VNFD file

   You can also add artifacts in VNFD for software images
   and/or other artifacts that's derived from type ``tosca.artifacts.Deployment``
   or directly from ``tosca.artifacts.Root`` but it doesn't mandate you to
   specify ``checksum`` which is a must as per ETSI GS NFV-SOL 003,
   Section 10.5.3.3 `etsi_sol003`_, so, all such any artifacts included in
   the VNFDs will be ignored and it would not be returned in ``additionalArtifacts``
   parameter of ``GET /vnf_packages/{vnfPkgId}`` API response.

   Example::

     VDU2:
       type: tosca.nodes.nfv.Vdu.Compute
         properties:
           name: VDU2
           sw_image_data:
             name: VrtualStorage
             version: '0.4.0'
             checksum:
               algorithm: sha-256
               hash: b9c3036539fd7a5f87a1bf38eb05fdde8b556a1a7e664dbeda90ed3cd74b4f9d
             container_format: bare
             disk_format: qcow2
             min_disk: 2 GB
             min_ram: 8192 MB
             size: 2 GB
           .....
       artifacts:
         sw_image:
           type: tosca.artifacts.nfv.SwImage
           file: Files/images/cirros.img
         python_script:
           type: tosca.artifacts.Deployment
           file: Files/scripts/my_python.py

During uploading of CSAR package in ``PUT /vnf_packages/{id}/package_content`` API,
it will read artifacts information from TOSCA.meta and Manifest files and store
these artifacts in the new DB table ``vnf_artifacts``. This artifact information
will then be returned in ``GET /vnf_packages/{vnfPkgId}`` API as shown below::

  {
    'additionalArtifacts': [{
        'artifactPath': 'MRF.yaml',
        'checksum': {
          'algorithm': 'sha-256',
          'hash': '09e5a788acb180162c51679ae4c998039fa6644505db2415e35107d1ee213943'
        }
        'metadata': {}
    },
    {
        'artifactPath': 'https://www.vendor_org.com/MRF/v4.1/scripts/scale/scale.sh',
        'checksum': {
          'algorithm': 'sha-256',
          'hash': '36f945953929812aca2701b114b068c71bd8c95ceb3609711428c26325649165'
        }
        'metadata': {}
    },
    {
        'artifactPath': 'scripts/install.sh',
        'checksum': {
          'algorithm': 'sha-256',
          'hash': 'd0e7828293355a07c2dccaaa765c80b507e60e6167067c950dc2e6b0da0dbd8b'
        }
        'metadata': {}
    }]
  }

Data model Impact
=================

Add below new db table in 'tacker' database.

vnf_artifacts::
  `id` int(11) Pri, auto_increment

  `package_uuid` varchar(36) NOT NULL

  `artifact_path` text NOT NULL

  `algorithm` varchar(64) NOT NULL

  `hash` varchar(128) NOT NULL

  `metadata` json NULL

  `created_at` datetime NOT NULL

  `updated_at` datetime NOT NULL

  `deleted_at` datetime NULL

  `deleted` tinyint(1) NULL

  This table will have `id` as primary key. `package_uuid` will be foreign
  key of `vnf_packages`.`package_uuid`.


REST API impact
===============

* Modify GET /vnf_packages/{vnfPkgId}

  Return ``additionalArtifacts`` parameter in the response as shown below::

     {
       "vnfSoftwareVersion":"1.0",
       "usageState":"NOT_IN_USE",
       "vnfProductName":"Sample VNF",
       "softwareImages":[]
       "vnfProvider":"Test VNF Provider",
       "userDefinedData":{}
       "vnfdId":"b3ab49d6-389d-46f9-8650-d0bf778b5e92",
       "additionalArtifacts": [{
         "artifactPath" : "foobar/foo/foo.yaml"
         "checksum": {
           "algorithm": "sha-256",
           "hash": "b9c3036539fd7a5f87a1bf38eb05fdde8b556a1a7e664dbeda90ed3cd74b4f9d"
         },
         "metadata": {
           "Content-Type": "application/json",
           "size": "1024",
         }
       }],
       "_links":{
         "packageContent":{
           "href":"/vnfpkgm/v1/vnf_packages/4e8b9d2c-ecb5-408b-a8ce-8ea0890bacbb/package_content"
         },
         "self":{
           "href":"/vnfpkgm/v1/vnf_packages/4e8b9d2c-ecb5-408b-a8ce-8ea0890bacbb"
         },
         "vnfd":{
           "href":"/vnfpkgm/v1/vnf_packages/4e8b9d2c-ecb5-408b-a8ce-8ea0890bacbb/vnfd"
         }
       },
       "vnfdVersion":"1.0",
       "onboardingState":"ONBOARDED",
       "operationalState":"DISABLED",
       "id":"4e8b9d2c-ecb5-408b-a8ce-8ea0890bacbb"
     }

.. note:: If user has already uploaded vnf packages in the previous release,
          then in such cases, ``additionalArtifacts`` parameter will always
          return an empty list in the response in case of
          ``GET /vnf_packages/{vnfPkgId}`` API. This parameter shall not be
          present before the VNF package content is on-boarded.

.. note:: ``additionalArtifacts`` shall not include images for VNFC.

* Modify GET /vnf_packages

  Allow users to filter out vnf packages based on ``additionalArtifacts`` query
  parameter in the request.

  For example, below URL query parameter will fetch those vnf packages
  matching artifacts with algorithm=sha-256::

    GET /vnf_packages?filter=(eq,additionalArtifacts/checksum/algorithm,sha-256)

  The ``additionalArtifacts`` attribute  is a complex attribute so by default
  it won't be returned in the response. If user wants to see/hide this complex
  attribute, then user will need to query explicitly using following ways:-

  #. all_fields: This URI query parameter requests that all complex attributes
     are included in the response,
     For example, ``GET /vnf_packages?all_fields`` will return additionalArtifacts
     in the response.
  #. fields: This URI query parameter requests that only the listed complex
     attributes are included in the response.
     For example, ``GET /vnf_packages?fields=additionalArtifacts/checksum``,
     will return only the checksum of additionalArtifacts along with other simple
     attributes.

     Sample response would look like::

       {
         'vnfSoftwareVersion': '1.0',
         'usageState': 'NOT_IN_USE',
         'vnfProductName': 'Sample VNF',
         ...
         'additionalArtifacts': [{
             'checksum': {
                 'algorithm': 'sha-256',
                 "hash": "b9c3036539fd7a5f87a1bf38eb05fdde8b556a1a7e664dbeda90ed3cd74b4f9d"
             }
         }]
       }

  #. exclude_fields: This URI query parameter requests that the listed complex
     attributes are excluded from the response.

     For example, ``GET /vnf_packages?exclude_fields=additionalArtifacts/checksum``
     will not return ``checksum`` of additionalArtifacts. It will include the
     other attributes from additionalArtifacts like ``metadata`` and
     ``artifactPath``.
  #. exclude_default: Presence of this URI query parameter requests that a
     default set of complex attributes shall be excluded from the response.

     For example, ``GET /vnf_packages?exclude_default`` or ``GET /vnf_packages``
     will not include ``additionalArtifacts`` complex attribute in the response.

* Add new API - GET /vnf_packages/{vnfPkgId}/artifacts/{artifactPath}

  * Fetches the content of an artifact within a VNF package. The request may
    contain a "Range" HTTP header to obtain single range of bytes from an
    artifact file.

  * Method type: GET

  * Normal http response code : 200 OK or 206 Partial Content

  * Expected error http response codes::

      401 NotAuthorized: shall be returned when authentication fails.

      403 Forbidden: Shall be returned when user is not authorized to call
      this REST API.

      404 NotFound: Shall be returned when the vnfPkgId or artifactPath specified in
      the URL doesn't exists.

      409 Conflict: Shall be returned when "onboardingState" of the VNF package has
      value different from "ONBOARDED".

      416 Range Not Satisfiable: Shall be returned when the byte range passed in the
      "Range" header did not match any available byte range in the artifact file.
      (e.g. "access after end of file").

  * Response - Return the whole content of the artifact file.
    The payload body shall contain a copy of the artifact file
    from the VNF package, as defined by ETSI GS NFV-SOL 004 `etsi_sol004`_.
    The ``Content-Type`` HTTP header shall be set according to the content type
    of the artifact file. If the content type cannot be determined, the header
    shall be set to the value ``application/octet-stream``.

Other end user impact
=====================

* Add new OSC command to fetch an individual artifact in an on-boarded
  VNF package::

    openstack vnf package artifact <vnfPkgId> <artifactPath>

* Modify OSC commands ``vnf package list`` and ``vnf package show`` to display
  ``additionalArtifacts`` information on the console output.


Other deployer impact
=====================

Below default policies will be added for the newly added restFul APIs.
If you want to customize these policies, you must edit policy.json file.

.. code-block:: console

    # Fetch an individual artifact in an on-boarded VNF package.
    # GET  /vnf_packages/{vnfPkgId}/artifacts/{artifactPath}
    # "os_nfv_orchestration_api:vnf_packages:fetch_artifact": "rule:admin_or_owner"

..

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Yoshito Ito <yoshito.itou.dr@hco.ntt.co.jp>

Other contributors:
  Nitin Uikey <nitin.uikey@nttdata.com>

  Tushar Patil <tushar.vitthal.patil@gmail.com>

  Prashant Bhole <prashant.bhole@nttdata.com>

Work Items
----------

* Modify ``GET /vnf_packages/{vnfPkgId}`` API to return ``additionalArtifacts``
  parameter in the response..
* Modify ``GET /vnf_packages`` API to filter out VNF packages based on attribute
  selection query parameters specific to type ``VnfPackageArtifactInfo``.
* Implement new Rest API ``GET /vnf_packages/{vnfPkgId}/artifacts/{artifactPath}``
  to fetch individual artifact in an on-boarded VNF package.
* Modify tosca-parser to read and verify artifact information from TOSCA.meta
  and Manifest file.
* Read artifacts information from TOSCA.meta and Manifest file during uploading
  of VNF package.
* Add unit and functional tests.

Dependencies
============

None

Testing
=======

Required unit and functional tests  will be added to verify
artifacts information is set and retrieved properly from an onboarded
VNF package.

Documentation Impact
====================

* Update API documentation for the all API changes mentioned in the
  `REST API impact`_.

References
==========

.. _etsi_sol003: https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/003/02.06.01_60/gs_nfv-sol003v020601p.pdf
.. _etsi_sol004:  https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/004/02.06.01_60/gs_nfv-sol004v020601p.pdf
.. _etsi_sol005: https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/005/02.06.01_60/gs_nfv-sol005v020601p.pdf
.. _spec1: https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/005/02.06.01_60/gs_nfv-sol005v020601p.pdf
.. _spec2: https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/005/02.06.01_60/gs_nfv-sol005v020601p.pdf
