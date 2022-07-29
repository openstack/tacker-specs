================================================
Support OpenID for Kubernetes VIM Authentication
================================================

https://blueprints.launchpad.net/tacker/+spec/support-openid-k8s-vim

Problem description
===================

There are several ways for authentication in Kubernetes VIM.
Currently, Tacker already supports using Service Account Token
as bearer token for authentication.
This specification proposes Tacker to support
OpenID Connect Token [#k8s_auth_oidc]_ as bearer token for authentication.
The OpenID Connect is defined by OpenID Connect Core 1.0 [#oidc]_.


Proposed Change
===============

The following diagram shows the image of authentication with OpenID Connect:
::

             +----------------+   1.setup OpenID Provider(IdP)
             |                +----------------------------------------------------------------+
             |      User      |   2.setup Kubernetes                                           |
             |                +----------------------------------------+                       |
             +-----+------+---+                                        |                       |
     6.CNF LCM     |      | 3.register vim                             |                       |
 (e.g. instantiate)|      |                                            |                       |
                   |      |                                            |                       |
         +-----------------------------------------------------+   +---v---------+    +--------v--------+
         |         |      |                                    |   |     VIM     |    |                 |
         | +-------v------v---+  4.create vim   +------------+ |   | (Kubernetes |    | OpenID Provider |
         | |                  +----------------->            | |   | API Server) |    | (Keycloak etc.) |
         | |  Tacker-server   |                 | NFVOPlugin | |   |             |    |                 |
         | |                  +-----+           |            | |   +---^---------+    +--------^--------+
         | +-------+----------+     |           +------+-----+ |       |                       |
         |         | 8.create       |          5.save  |       |       |                       |
         |         | resource       |          VimAuth |       |       |                       |
         | +------------------+     |7.get      +------v-----+ |       |                       |
         | | +-----v--------+ |     |VimAuth    |            | |       |10.call Kubernetes API |
         | | |              | |     +----------->  TackerDB  | |       |                       |
         | | | InfraDriver  | |                 |            | |       |                       |
         | | | (Kubernetes) | |                 +------------+ |       |                       |
         | | |              +------------------------------------------+           9.get token |
         | | |              +------------------------------------------------------------------+
         | | +--------------+ |                                |
         | | Tacker-conductor |                                |
         | +------------------+                        Tacker  |
         +-----------------------------------------------------+


#. Login to OpenID Provider(IdP), create client, add user and groups,
   and so on.

#. Configure the Kubernetes API server to enable the OpenID Connect(OIDC)
   plugin.

#. Register VIM using command or API.

   * This step is only required for V1 LCM operations.
     In V2 LCM operations, authentication parameters can be passed by
     VimConnectionInfo in each LCM requests, thus this step is no longer
     required.

#. Call the create vim method of class NFVOPlugin.

#. Store the client_id, client_secret, username, password, token_url,
   ssl_ca_cert to TackerDB.

#. Execute CNF LCM operation(e.g. instantiate).

#. Get client_id, client_secret, username, password, token_url, ssl_ca_cert
   from TackerDB.

#. Call InfraDriver's Kubernetes client method to create resources.

#. Get a id_token from the IdP using client_id, client_secret, user_name,
   password, token_url, ssl_ca_cert.

#. Call Kubernetes APIs with the id_token.

.. note::

  The IdP has investigated with Keycloak [#keycloak]_.
  Whether there is a difference using another IdP requires
  additional investigation.


The following changes are required to support OIDC authentication:

+ Changes in VIM APIs
+ Changes in Kubernetes Infra Driver

1) Changes in VIM APIs
----------------------

As mentioned above, Tacker's support for OIDC authentication requires
the following parameters:

+ client_id
+ client_secret
+ username
+ password
+ token_url
+ ssl_ca_cert

.. Note::

  + The client_id is a identifier of Tacker(OIDC client) at the IdP.
  + The username is a identifier of a user at the IdP.
  + The username will be included in id_token(A JSON Web Token).
  + The username in id_token will be verified what permissions it has to
    Kubernetes when calling Kubernetes APIs.

The request parameters of Register VIM API [#register_vim_api]_
should be set as below:

+ The username, password and ssl_ca_cert are set in the ``auth_cred``.
+ The client_id and client_secret should be added as new fields
  in the ``auth_cred``.
+ When using Service Account Token for authentication, the ``auth_url``
  is set to the endpoint of Kubernetes.
  When using OpenID Connect Token for authentication, the ``auth_url``
  is still set to the endpoint of Kubernetes,
  and a new field ``oidc_token_url`` should be added in the ``auth_cred``
  for setting the endpoint of IdP.

As a result, the following functions need to be modified.

+ VIM command group(register/set/list/show)
+ VIM API group(register/update/list/show)

VIM configuration
~~~~~~~~~~~~~~~~~

Sample file of VIM Configuration for Kubernetes:

vim_config.yaml

.. code-block:: yaml

    auth_url: 'https://192.168.2.82:6443'
    oidc_token_url: 'https://192.168.2.81:8443/auth/realms/kubernetes/protocol/openid-connect/token'
    project_name: "default"
    username: 'end-user'
    password: 'end-user'
    client_id: 'tacker'
    client_secret: 'E3xaNpB8reiUuEyrD8y6wQ1obPJAtbbU'
    ssl_ca_cert: |
        -----BEGIN CERTIFICATE-----
        MIICwjCCAaqgAwIBAgIBADANBgkqhkiG9w0BAQsFADASMRAwDgYDVQQDEwdrdWJl
        LWNhMB4XDTIwMDgyNjA5MzIzMVoXDTMwMDgyNDA5MzIzMVowEjEQMA4GA1UEAxMH
        a3ViZS1jYTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALxkeE16lPAd
        pfJj5GJMvZJFcX/CD6EB/LUoKwGmqVoOUQPd3b/NGy+qm+3bO9EU73epUPsVaWk2
        Lr+Z1ua7u+iib/OMsfsSXMZ5OEPgd8ilrTGhXOH8jDkif9w1NtooJxYSRcHEwxVo
        +aXdIJhqKdw16NVP/elS9KODFdRZDfQ6vU5oHSg3gO49kgv7CaxFdkF7QEHbchsJ
        0S1nWMPAlUhA5b8IAx0+ecPlMYUGyGQIQgjgtHgeawJebH3PWy32UqfPhkLPzxsy
        TSxk6akiXJTg6mYelscuxPLSe9UqNvHRIUoad3VnkF3+0CJ1z0qvfWIrzX3w92/p
        YsDBZiP6vi8CAwEAAaMjMCEwDgYDVR0PAQH/BAQDAgKkMA8GA1UdEwEB/wQFMAMB
        Af8wDQYJKoZIhvcNAQELBQADggEBAIbv2ulEcQi019jKz4REy7ZyH8+ExIUBBuIz
        InAkfxNNxV83GkdyA9amk+LDoF/IFLMltAMM4b033ZKO5RPrHoDKO+xCA0yegYqU
        BViaUiEXIvi/CcDpT9uh2aNO8wX5T/B0WCLfWFyiK+rr9qcosFYxWSdU0kFeg+Ln
        YAaeFY65ZWpCCyljGpr2Vv11MAq1Tws8rEs3rg601SdKhBmkgcTAcCzHWBXR1P8K
        rfzd6h01HhIomWzM9xrP2/2KlYRvExDLpp9qwOdMSanrszPDuMs52okXgfWnEqlB
        2ZrqgOcTmyFzFh9h2dj1DJWvCvExybRmzWK1e8JMzTb40MEApyY=
        -----END CERTIFICATE-----
        -----BEGIN CERTIFICATE-----
        MIIDgTCCAmkCFBkaTpj6Fm1yuBJrOI7OF1ZxEKbOMA0GCSqGSIb3DQEBCwUAMH0x
        CzAJBgNVBAYTAkNOMRAwDgYDVQQIDAdKaWFuZ3N1MQ8wDQYDVQQHDAZTdXpob3Ux
        DTALBgNVBAoMBGpmdHQxDDAKBgNVBAsMA2RldjEUMBIGA1UEAwwLdGFja2VyLmhv
        c3QxGDAWBgkqhkiG9w0BCQEWCXRlc3RAamZ0dDAeFw0yMjAzMDgwMjQ2MDZaFw0y
        MzAzMDgwMjQ2MDZaMH0xCzAJBgNVBAYTAkNOMRAwDgYDVQQIDAdKaWFuZ3N1MQ8w
        DQYDVQQHDAZTdXpob3UxDTALBgNVBAoMBGpmdHQxDDAKBgNVBAsMA2RldjEUMBIG
        A1UEAwwLdGFja2VyLmhvc3QxGDAWBgkqhkiG9w0BCQEWCXRlc3RAamZ0dDCCASIw
        DQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALIUIDZLvKs7NKBZo+172uH9dftL
        pNM4dGgfc4jvmFjZswDex9Vqrlt7pcdrorlv2w3PWyODEzmx98EsDxVtrBNPP5lQ
        aGk6zVtC7J7trIODqD/xhS8G2H4weX1znx0NVi50pqDxVxqeXO11rwtglJ7Wwkp6
        R9dkMbr3ZHWWKEZauBWX4NX16XErniSemW8Co/Oa3coX7CtrSzRCDJJcD8MdMFBE
        m02obSh88N+YJPRLBBIGl2JfZdD0IZldUe9RozhGA80gcJeLiVoNeVIpznc/LGTr
        xHWOb2Wh0yP6gl3KX4JjJ0NubZPaskUHILFN34F5a3fVQE3t7dQk8jq7JlMCAwEA
        ATANBgkqhkiG9w0BAQsFAAOCAQEAH0B2qgwKjWje0UfdQOb1go8EKsktHOvIDK5+
        dXz2wNFJpKCekvSGK4/2KEp1McTTDj0w8nlWcGZgaOcvjuq8ufWrggjdADa2xJHr
        4pfxNMQrQXCFZ5ikCoLDx9QKDyN81b12GWpr1yPYIanSghbhx4AW7BkVQwtELun8
        d6nHGTixkqxljbEB9qM/wOrQMlm/9oJvyU4Po7weav8adPVyx8zFh9UCH2qXKUlo
        3e5D8BKkBpo4DtoXGPaYBuNt/lI7emhfikcZ2ZbeytIGdC4InoooYMKJkfjMxyim
        DSqhxuyffTmmMmEx1GK9PYLy7uPJkfn/mn9K9VL71p4QnJQt7g==
        -----END CERTIFICATE-----
    type: "kubernetes"

.. Note::
    The parameter ``auth_cred.ssl_ca_cert`` contains 2 certificates.
    One for VIM and one for IdP.


Parameters for V1/V2 LCM API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As mentioned above, VIM registration is required only for V1 LCM API.
The below shows the sample of request parameter using V1 instantiate
API.

.. code-block:: json

  {
    "flavourId": "simple",
    "additionalParams": {
      "lcm-kubernetes-def-files": [
        "Files/kubernetes/stateful_set.yaml"
      ]
    },
    "vimConnectionInfo": [
      {
        "id": "8a3adb69-0784-43c7-833e-aab0b6ab4470",
        "vimId": "8d8373fe-6977-49ff-83ac-7756572ed186"
        "vimType": "kubernetes"
      }
    ]
  }


In V2 LCM API, authentication information can be included
in VimConnectionInfo in each LCM request parameters, thus
the sample of request parameter of V2 Instantiate VNF
will be as follows:

.. code-block:: json

  {
    "flavourId": "simple",
    "additionalParams": {
      "lcm-kubernetes-def-files": [
        "Files/kubernetes/stateful_set.yaml"
      ]
    },
    "vimConnectionInfo": {
      "vim1": {
        "vimType": "kubernetes",
        "accessInfo": {
          "oidc_token_url": "https://keycloak.example.com:8443/realms/sample-realm/protocol/openid-connect/token",
          "username": "user",
          "password": "password",
          "client_id": "sample-client-id",
          "client_secret": "sample-secret"
        },
        "interfaceInfo": {
          "endpoint": "https://k8s.example.com:6443",
          "ssl_ca_cert": "sample-ssl-ca-cert"
        }
      }
    }
  }


1) Changes in Kubernetes Infra Driver
-------------------------------------

The flow of calling the Kubernetes APIs is shown as below
(take ``instantiate`` as an example):

.. seqdiag::

  seqdiag {
    node_width = 90;
    edge_length = 130;

    "Client"
    "Tacker-server"
    "Tacker-conductor"
    "VnfLcmDriver"
    "InfraDriver(Kubernetes)"
    "IdP"
    "VIM(Kubernetes)"

    "Client" -> "Tacker-server"
      [label = "1. instantiate vnf"];
    "Client" <-- "Tacker-server"
      [label = "response"];
    "Tacker-server" ->> "Tacker-conductor"
      [label = "2. instantiate"];
    "Tacker-conductor" -> "VnfLcmDriver"
      [label = "3. instantiate_vnf"];
    "VnfLcmDriver" -> "InfraDriver(Kubernetes)"
      [label = "4. instantiate_vnf"];
    "InfraDriver(Kubernetes)" -> "IdP"
      [label = "5. get token"];
    "InfraDriver(Kubernetes)" <-- "IdP";
    "InfraDriver(Kubernetes)" -> "VIM(Kubernetes)"
      [label = "6. call Kubernetes APIs"];
    "InfraDriver(Kubernetes)" <-- "VIM(Kubernetes)"
      [label = "response"];
    "VnfLcmDriver" <-- "InfraDriver(Kubernetes)";
    "Tacker-conductor" <-- "VnfLcmDriver";
  }


#. The Client sends a request to Tacker-server to instantiate a vnf.
#. Tacker-server gets the ``vimAuth`` from TackerDB, and calls
   the instantiate rpc-api of Tacker-conductor.
#. Tacker-conductor calls the instantiate_vnf method of VnfLcmDriver.
#. VnfLcmDriver calls the instantiate_vnf of InfraDriver(Kubernetes).
#. InfraDriver(Kubernetes) sends request to IdP to get an id_token.
#. InfraDriver(Kubernetes) sends requests with the id_token to Kubernetes
   to create resources.

.. Note::

  Each LCM operation(instantiate, terminate, etc) will get a individual token
  from IdP, and the token will be used in all API calls to the Kubernetes VIM
  in one LCM processing.


Get token from IdP
~~~~~~~~~~~~~~~~~~

Get token from IdP requires the following parameters:

+ token_url
+ client_id
+ client_secret
+ username
+ password
+ ssl_ca_cert
+ grant_type(the value is fixed to "password")
+ scope(the value is fixed to "openid")

A sample of getting a token through curl:

.. code-block::

  curl --cacert cacert.crt -d "grant_type=password" -d "scope=openid" \
  -d "client_id=kubernetes" -d "client_secret=E3xaNpB8reiUuEyrD8y6wQ1obPJAtbbU" \
  -d "username=tacker" -d "password=tacker" \
  https://keycloakserver:8443/realms/kubenetes/protocol/openid-connect/token


Alternatives
------------

None

Data model impact
-----------------

As mentioned above, OIDC authentication requires the client_id, client_secret,
username, password, token_url, ssl_ca_cert.

The following fields will not change:

+ The username is located at ``VimAuth.auth_cred.username``
+ The password is located at  ``VimAuth.password``
+ The ssl_ca_cert is located at  ``VimAuth.ssl_ca_cert``

The following fields need to be extended in the ``VimAuth.auth_cred``:

+ The client_id will be located at the ``VimAuth.auth_cred.client_id``
+ The client_secret will be located at the ``VimAuth.auth_cred.client_secret``
+ The oidc_token_url will be located
  at the ``VimAuth.auth_cred.oidc_token_url``

Since ``VimAuth.auth_cred`` is a json, the table doesn't actually
need any changes.

.. note::

   For security, client_secret may also need to be encrypted with fernet
   as well as password.


REST API impact
---------------

The parameter ``auth_cred`` in the VIM APIs will add the follow fields:

+ client_id
+ client_secret
+ oidc_token_url

The following APIs need to be changed:

+ Register VIM: POST /v1.0/vims
  (``auth_cred`` in both Request and Response parameters)
+ List VIMs: GET /v1.0/vims  (``auth_cred`` in Response parameters)
+ Show VIM: GET /v1.0/vims/{vim_id}  (``auth_cred`` in Response parameters)
+ Update VIM: PUT /v1.0/vims/{vim_id}
  (``auth_cred`` in both Request and Response parameters)

Security impact
---------------

None

Notifications impact
--------------------

None

Other end user impact
---------------------

None

Performance impact
------------------

None

Other deployer impact
---------------------

None

Developer impact
----------------

None

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Masaki Ueno<masaki.ueno.up@hco.ntt.co.jp>

Other contributors:
  Qibin Yao <yaoqibin@fujitsu.com>

  Ayumu Ueha<ueha.ayumu@fujitsu.com>

  Yoshiyuki Katada <katada.yoshiyuk@fujitsu.com>

  Yusuke Niimi<niimi.yusuke@fujitsu.com>

Work Items
----------
+ Implement to support:

  + Extend client_id and client_secret in ``auth_cred`` of VIM command group.
  + Extend client_id and client_secret in ``auth_cred`` of VIM APIs.
  + Add logic for calling Kubernetes with id_token.
  + Modify the vim config generator tool(gen_vim_config.sh)
    to add client_id and client_secret.
  + Add new unit and functional tests.

Dependencies
============

None

Testing
=======

Unit and functional tests will be added to cover cases required in the spec.

Documentation Impact
====================

#. API guide will add client_id and client_secret
   in the ``auth_cred`` of VIM APIs.
#. User guide will add a manual on how to use the IdP
   to authenticate users in Kubernetes.

References
==========

.. [#k8s_auth_oidc] https://kubernetes.io/docs/reference/access-authn-authz/authentication/#openid-connect-tokens
.. [#oidc] https://openid.net/specs/openid-connect-core-1_0.html
.. [#keycloak] https://www.keycloak.org/
.. [#register_vim_api] https://docs.openstack.org/api-ref/nfv-orchestration/v1/legacy.html?expanded=register-vim-detail
