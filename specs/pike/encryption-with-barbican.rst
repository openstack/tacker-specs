..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


===================================
Storing VIM credentials in barbican
===================================

Include the URL of your launchpad blueprint:

https://blueprints.launchpad.net/tacker/+spec/encryption-with-barbican

This spec introduces a way of storing VIM credentials in barbican.

Problem description
===================

Tacker supports register VIM with credentials, which are used for
nfvo and vnfm to operation resources in NFVI. The credentials include
username, password, and project information. We can not explicitly
store the plain text password in tacker db for security consideration.
So currently we use keystone's fernet to generate a key to encrypt
the password, save the encrypted secret into tacker db, and save
the fernet key on local file system.

When we need the authorization to a VIM, we retrieve the original
password by decrypting the secret in tacker db with the fernet key
in local file system.

The problem is, if tacker service serves API requests through
a load balancer, then the operation will fail if the request is not
fulfilled by the server node which created and stored the fernet key.
We need a possible solution for syncing the keys across multiple
server nodes. This adds operationally complexity for tacker
administrators as they add tacker-server instances for scaling.

Barbican introduction
=====================

Barbican [1]_ is a REST API designed for the secure storage, provisioning and
management of secrets. It is aimed at being useful for all environments,
including large ephemeral Clouds.

The barbican API [2]_ includes the following items:

* Secrets API. It provides access to the secret / keying material stored
  in the system, including Private Key/Certificate/Password/SSH Keys

* Secret Metadata API. It allows a user to be able to associate various
  key/value pairs with a Secret.

* Containers API. It creates a logical object that can be used to
  hold secret references.

* ACL API. It supports access control for secrets and containers.

* Certificate Authorities API. It is used as an interface to interact
  with Certificate Authorities.

* Quotas API. It limit on the number of resources that are allowed
  to be created.

* Consumers API. It is a way to register as an interested party
  for a container.

* Certificates API [deprecated in Pike]. It manages the lifecycle of
  x509 certificates covering operations such as initial certificate
  issuance, certificate re-issuance, certificate renewal and
  certificate revocation.

* Orders API [deprecated in Pike]. It allows user to request barbican
  to generate a secret, create certificates and public/private key pairs.

In tacker vim use case, we can use the Secrets API to restore the password
of VIM. And in future, we can use Barbican to support TLS in Tacker API, the
new blueprint URL to be realized is:
https://blueprints.launchpad.net/tacker/+spec/support-tls-in-api

The command to store the password:

.. code-block:: console

  $ source devstack/openrc admin
  $ openstack secret store --name 'vim_password' --payload-content-type='text/plain' --payload="123456"
  +---------------+--------------------------------------------------------------+
  | Field         | Value                                                        |
  +---------------+--------------------------------------------------------------+
  | Secret href   | http://192.168.80.128:9311/v1/secrets/fd44e2ed-b318-4924     |
  |               | -a43f-afac4ba45aca                                           |
  | Name          | vim_password                                                 |
  | Created       | None                                                         |
  | Status        | None                                                         |
  | Content types | {u'default': u'text/plain'}                                  |
  | Algorithm     | aes                                                          |
  | Bit length    | 256                                                          |
  | Secret type   | opaque                                                       |
  | Mode          | cbc                                                          |
  | Expiration    | None                                                         |
  +---------------+--------------------------------------------------------------+

The command to retrieve the password:

.. code-block:: console

  $ openstack secret get http://192.168.80.128:9311/v1/secrets/fd44e2ed-b318-4924-a43f-afac4ba45aca --decrypt
  +---------+--------+
  | Field   | Value  |
  +---------+--------+
  | Payload | 123456 |
  +---------+--------+

Let's look into other projects about how Barbican is invoked.

Invoked in Nova or Cinder
-------------------------

Barbican is introduced into nova and cinder to support the volume
encryption feature [3]_ [4]_.
They invoke castellan as key_mamager, allowing Barbican to securely
generate, store, and present encryption keys.

Invoked in Neutron-lbaas or Magnum
----------------------------------

Neutron-lbaas and Magnum introduces barbican to support TLS [5]_ [6]_.
They invoke barbicanclient directly to store tenants' TLS certificates in
barbican secure containers.

Castellan introduction
----------------------

Castellan [7]_ is the library of Barbican, working on the principle of providing
an abstracted key manager based on the configurations. In this manner,
several different management services can be supported through a single
interface. In addition to the key manager, Castellan also provides primitives
for various types of secrets (for example, asymmetric keys,simple
passphrases, and certificates). These primitives are used in conjunction
with the key manager to create, store, retrieve, and destroy managed secrets.

barbicanclient VS castellan
---------------------------

Barbicanclient supports full APIs of Barbican.
Castellan is a library which invokes barbicanclient, offering
an elaborate API, and more easier to use than the client.

Unfortunately castellan can not support ACL for secrets or
containers currently.
So we will invoke barbicanclient only in this spec, and may
consider to use castellan in future if necessary.

How to use castellan
--------------------

* Example. Creating and storing a key.

  .. code-block:: python

    from castellan.common.objects import passphrase
    from castellan import key_manager

    key = passphrase.Passphrase('super_secret_password')
    manager = key_manager.API()
    stored_key_id = manager.store(context, key)

* Example. Retrieving a key.

  .. code-block:: python

    from castellan import key_manager

    manager = key_manager.API()
    key = manager.get(context, stored_key_id)
    key.get_encoded()

* Example. Deleting a key.

  .. code-block:: python

    from castellan import key_manager

    manager = key_manager.API()
    manager.delete(context, stored_key_id)

How to use barbicanclient
-------------------------

We can refer to castellan to see how to invoke barbicanclient [12]_:

store secret:

.. code-block:: python

    barbican_client = self._get_barbican_client(context)

    try:
        secret = self._get_barbican_object(barbican_client,
                                           managed_object)
        secret.expiration = expiration
        secret_ref = secret.store()
        return self._retrieve_secret_uuid(secret_ref)
    except (barbican_exceptions.HTTPAuthError,
            barbican_exceptions.HTTPClientError,
            barbican_exceptions.HTTPServerError) as e:
        LOG.error(_LE("Error storing object: %s"), e)
        raise exception.KeyManagerError(reason=e)

get secret:

.. code-block:: python

    try:
        secret = self._get_secret(context, managed_object_id)
        return self._get_castellan_object(secret, metadata_only)
    except (barbican_exceptions.HTTPAuthError,
            barbican_exceptions.HTTPClientError,
            barbican_exceptions.HTTPServerError) as e:
        LOG.error(_LE("Error retrieving object: %s"), e)
        if self._is_secret_not_found_error(e):
            raise exception.ManagedObjectNotFoundError(
                uuid=managed_object_id)
        else:
            raise exception.KeyManagerError(reason=e)


How to generate context
-----------------------

Let's look into how to generate the context for castellan.

For security consideration, barbican need to get authorization from
the keystone. And the secrets stored in barbican is private to the operator,
the users in the same project can retrieval the secrets by default RBAC
policy.

There are two methods to generate the context.

1. Using a reserved project

Castellan Usage [8]_ shows a method, saving the credentials in configuration.
We can create a reserved tenant (e.g. 'tacker-vim-credential-store' or
long living existing created user), and all vims' passwords are saved and
retrieved in this tenant's domain.

.. code-block:: ini

  [castellan]
  auth_type = 'keystone_password'
  username = 'tacker-vim-credential-store'
  password = 'passw0rd1'
  project_id = 'tacker-vim-credential-store'
  user_domain_name = 'default'

As discussion in IRC [11], we should not do in this way.

2. Using the operator's context (who creates vim)

The default RBAC policy [9]_ about secrets are following:

.. code-block:: ini

    "admin": "role:admin",
    "observer": "role:observer",
    "creator": "role:creator",
    "audit": "role:audit",
    "service_admin": "role:key-manager:service-admin",
    "admin_or_user_does_not_work": "project_id:%(project_id)s",
    "admin_or_user": "rule:admin or project_id:%(project_id)s",
    "admin_or_creator": "rule:admin or rule:creator",
    "all_but_audit": "rule:admin or rule:observer or rule:creator",
    "all_users": "rule:admin or rule:observer or rule:creator or rule:audit or rule:service_admin",
    "secret_project_match": "project:%(target.secret.project_id)s",
    "secret_acl_read": "'read':%(target.secret.read)s",
    "secret_private_read": "'False':%(target.secret.read_project_access)s",
    "secret_creator_user": "user:%(target.secret.creator_id)s",

    "secret_non_private_read": "rule:all_users and rule:secret_project_match and not rule:secret_private_read",
    "secret_decrypt_non_private_read": "rule:all_but_audit and rule:secret_project_match and not rule:secret_private_read",
    "secret_project_admin": "rule:admin and rule:secret_project_match",
    "secret_project_creator": "rule:creator and rule:secret_project_match and rule:secret_creator_user",

    "secret:decrypt": "rule:secret_decrypt_non_private_read or rule:secret_project_creator or rule:secret_project_admin or rule:secret_acl_read",
    "secret:get": "rule:secret_non_private_read or rule:secret_project_creator or rule:secret_project_admin or rule:secret_acl_read",
    "secret:put": "rule:admin_or_creator and rule:secret_project_match",
    "secret:delete": "rule:secret_project_admin or rule:secret_project_creator",
    "secrets:post": "rule:admin_or_creator",
    "secrets:get": "rule:all_but_audit",

The barbican support a white-list ACL for each secret. It is not
convenient to add all projects to the ACL [10]_ if vim is shared.

In this method, we can not support shared vim. As result of IRC
discussion [11]_, in future, vim is limited to be shared with
specified projects via rbac policies, we may add these projects
into the ACL of the secret.

Transmitting encrypted password
-------------------------------

For security consideration, we need avoid sending unencrypted cleartext
password transmitting from tacker to barbican.

There are two methods:
1. use fernet to encode vim password, and save fernet key into barbican.
2. support TLS between tacker with barbican.
I suggest use method 1, just like the current vim encode way.

Proposed change
===============

We need retain current realization for a release cycle,
make it configurable, and use local file system by default.

.. code-block:: python

  OPTS = [
      cfg.StrOpt('use_barbican', default='no',
                 help=_("Use barbican to encrypt vim password if yes,
                         Save vim credentials in local file system if no")),
  ]
  cfg.CONF.register_opts(OPTS, 'tacker')

We add a directory named keymgr under tacker, which
invokes the barbicanclient.
Add a class BarbicanKeyManager including following method:

.. code-block:: python

    def __init__(self, configuration):

    def _get_barbican_client(self, context):
        """Creates a client to connect to the Barbican service."""

    def store(self, context, secret, expiration=None):
        """Stores (i.e., registers) a secret with the key manager."""

    def get(self, context, managed_secret_id, metadata_only=False):
        """Retrieves the specified managed secret."""

    def delete(self, context, managed_secret_id):
        """Deletes the specified managed secret."""

    def create_acl(self, context, entity_ref=None, users=None,
                   project_access=None,
                   operation_type=DEFAULT_OPERATION_TYPE):
        """Creates acl for the specified managed secret."""

    def get_acl(self, context, entity_ref):
        """Retrieves acl of the specified managed secret."""

In nfvo.nfvo_plugin.NfvoPlugin:
 1. in create/update/delete_vim, add context into vim_obj
 2. in delete_vim, invoke vim_driver with vim_obj

In nfvo.drivers.vim.openstack_driver.OpenStack_Driver:

 1. __init__
 initializes keymgr, loads the credentials in configuration,
 self.key_manager = BarbicanKeyManager()

 2. register_vim
 check whether barbican is available. If no, do as before, if yes,
 get original password and context from vim_obj,
 use fernet to encode password which generates a fernet_key,
 invoke self.key_manager.store(context, fernet_key) which returns
 a secret uuid,
 save the uuid into vim_obj['auth_cred']['password'],
 set the vim_obj['auth_cred']['key_type'] with barbican_secret

 3. deregister_vim
 check whether barbican is available. If no, do as before, if yes,
 replace the function parameter vim with vim_obj,
 retrieve key_id from vim_obj['auth_cred']['password'],
 retrieve context from vim_obj,
 invoke self.key_manager.delete(context, key_id)

In vnfm.vim_client.VimClient

 1. add context into _build_vim_auth parammeter list.

 2. _build_vim_auth
 according to the key_type in vim_info['auth_cred'],
 if key_type is fernet_key, do as before, if it's barbican_secret,
 retrieve key_id from vim_obj['auth_cred']['password'],
 invoke BarbicanKeyManager().get(context, key_id) to decode password.

Alternatives
------------

None

Data model impact
-----------------

In current realization, the fernet-encrypted password is saved in
VimAuth.password and VimAuth.auth_cred['password'].
When using barbican, we will save the secret UUID in these fields.
A new filed will be added into VimAuth to distinguish what type of
the password, which will help to retrieve password.

Currently vim is created with shared property by default.
After we support vim rbac in future, we should support to modify the
ACL of barbican secrets.

.. code-block:: python

    class Vim(model_base.BASE,
              models_v1.HasId,
              models_v1.HasTenant,
              models_v1.Audit):
        type = sa.Column(sa.String(64), nullable=False)
        name = sa.Column(sa.String(255), nullable=False)
        description = sa.Column(sa.Text, nullable=True)
        placement_attr = sa.Column(types.Json, nullable=True)
        # modify the default value to false
        shared = sa.Column(sa.Boolean, default=True, server_default=sql.false(
        ), nullable=False)

    class VimAuth(model_base.BASE, models_v1.HasId):
        vim_id = sa.Column(types.Uuid, sa.ForeignKey('vims.id'),
                           nullable=False)
        password = sa.Column(sa.String(255), nullable=False)
        auth_url = sa.Column(sa.String(255), nullable=False)
        vim_project = sa.Column(types.Json, nullable=False)
        auth_cred = sa.Column(types.Json, nullable=False)
        # 'fernet_key' or 'barbican_secret'
        key_type = sa.Column(sa.String(255), nullable=False)


REST API impact
---------------

None

Security impact
---------------

None

Notifications impact
--------------------

None

Other end user impact
---------------------

None

Performance Impact
------------------

None

Other deployer impact
---------------------

We need Barbican and Castellan installed if we configure 'use_barbican'
to 'yes'.

Developer impact
----------------

None

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Yan Xing an<yanxingan@cmss.chinamobile.com>

Other contributors:
  None

Work Items
----------

The BP involves following tasks:

#. nfvo and vim driver with unit tests
#. functional tests
#. installation document
#. support barbican in devstack


Dependencies
============

 * Barbican

Testing
=======

 * FT/UT

Documentation Impact
====================

 * installation document

References
==========

.. [1] https://github.com/openstack/barbican
.. [2] https://developer.openstack.org/api-guide/key-manager/
.. [3] https://github.com/openstack/nova-specs/blob/master/specs/juno/approved/encryption-with-barbican.rst
.. [4] https://review.opendev.org/#/c/106437/2/specs/juno/encryption-with-barbican.rst
.. [5] https://github.com/openstack/neutron-specs/blob/master/specs/kilo/lbaas-tls.rst
.. [6] https://github.com/openstack/magnum-specs/blob/master/specs/pre-ocata/implemented/tls-support-magnum.rst
.. [7] https://github.com/openstack/castellan
.. [8] https://docs.openstack.org/developer/castellan/usage.html
.. [9] https://github.com/openstack/barbican/blob/master/etc/barbican/policy.json
.. [10] https://developer.openstack.org/api-guide/key-manager/acls.html
.. [11] http://eavesdrop.openstack.org/meetings/tacker/2017/tacker.2017-04-05-05.30.log.html
.. [12] https://github.com/openstack/castellan/blob/master/castellan/key_manager/barbican_key_manager.py

