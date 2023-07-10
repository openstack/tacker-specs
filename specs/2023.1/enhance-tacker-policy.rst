..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


=================================================
Enhancement of Tacker API Resource Access Control
=================================================

https://blueprints.launchpad.net/tacker/+spec/enhance-api-policy

Problem description
===================

In the current implementation, the Tacker API policy only supports whether the
user can access the API, but does not determine whether the user can access the
object on which the API call operates. However, in commercial networks, telecom
operators need finer-grained access control for API resources. For example, only
engineers of Company A are allowed to operate VNF/CNF of Company A, but
engineers of other companies cannot.

The oslo.policy [#oslo.policy]_ supports the function to compare API attributes
to object attributes. For example:

.. code-block:: console

  "os_nfv_orchestration_api:vnf_instances:show" : "project_id:%(project_id)s"

The project_id string before the colon is an API attribute, namely the project
ID of the API user. It is compared with the project ID of the object (in this
case, a VNF instance). More precisely, it is compared with the project_id
field of that object in the database. If the two values are equal, permission is
granted.

Based on this function, this specification describes implements of fine-grained
access control based on user and VNF information for API resources.

Proposed change
===============
The following changes are needed:

#. Add additional attributes to resources when be created.
#. Change the API process to support Tacker policy checker.
#. Add the Tacker policy filter to the list API processes.
#. Convert special roles to API attributes in context.
#. Add a configuration option.
#. Policy and roles samples.

Add Additional Attributes to Resources When Be Created
------------------------------------------------------

#. Register Vim API

   + Put an area attribute into request parameter 'extra'. It will be stored
     into DB by later API process.

#. Create VNF instance API v1/v2

   + Get area attribute from default Vim, then put it in the 'extra' field of
     VimConnectionInfo object in VnfInstance object, and then store it into DB.

#. Instantiate VNF instance v1/v2

   + Get Vim info by vim_id in VimConnectionInfo from request body.
   + Get area attribute from Vim info, then put it in the 'extra' field of
     VimConnectionInfo object in InstantiateVnfRequest object, and then store it
     into DB.

.. note::
  Area attribute is a area-region pair. The value of this attribute is a string
  in the format of "area@region".

Change the API Process to Support Tacker Policy Checker
-------------------------------------------------------

In the current implementation, the Tacker API process did not pass in the
attributes of the accessed resource when calling the policy function. However,
those attributes are needed by enhanced Tacker API policy function to determine
if a user can access the resource or not. Therefore, we should modify the API
process. Get the attributes required by policy checker from the database and
pass them to policy checker when calling.

The flow of a policy check in API process to support enhanced Tacker policy.

.. seqdiag::

  seqdiag {
    Client -> Keystonemiddleware [label = "request"];
    Keystonemiddleware -> "API Process" [label = "1. Request with user info"];
    "API Process" -> TackerDB [label = "2. Get the accessed \nresources from the TackerDB"]
    "API Process" <-- TackerDB [label = "return the accessed\n resources"];
    "API Process" -> "API Process" [label = "3. Get required \nresource \nattributes \nfrom accessed \nresources"];
    "API Process" -> Context [label = "4. Invoke policy check function with accessed resource\n attributes"];
    Context -> Context [label = "5. Convert special \nroles to user\n attributes"];
    Context -> oslo.policy [label = "6. Invoke policy enforcer\n with resource attributes\n and user attributes"];
    Context <-- oslo.policy;
    "API Process" <-- Context;
    === 7. Operate the accessed resource. ===
    Keystonemiddleware <-- "API Process" [label = "response"];
    Client <-- Keystonemiddleware [label = "response"];
  }

Step 3 is specialized and needs to be implemented by each API process by itself.
The other steps are common or already exist for all API processes to be changed:

1. Keystonemiddleware will send request to API process with user info which
   includes user roles. Special user roles will be converted to user attributes
   in later step. This step is an existing step and does not need to be
   modified.
2. API Process gets the accessed resources from the TackerDB. This step is
   existing and does not need to be modified.
3. API Process gets required resource attributes from accessed resources. This
   step is newly added.
4. API Process invokes policy check function with accessed resource attributes.
   This step is existing, but what needs to be modified is to add resource
   attributes as call parameters when calling the policy check
   function.
5. Context converts special roles to user attributes. This step is newly added
   and whether it is executed or not will be determined by the configuration
   option described in the following section
   `Add a Configuration Option`_. For the conversion rules, please refer to the
   later section `Convert Special Roles to API Attributes in Context`_ for
   details.
6. Context invokes policy enforcer with resource attributes and user
   attributes. This step is existing and does not need to be modified.
7. API Process operates the accessed resource. This step is existing and does
   not need to be modified.

Vim API processes to be changed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Vim delete
* Vim update
* Vim show

The following table shows that the attribute required by a policy checker could
be queried by which API request parameter from which table and stored in which
field.

.. list-table::
  :widths: 10 28 16 12 50
  :header-rows: 1

  * - Attribute
    - Request Parameter
    - Table
    - Field
    - Sample
  * - area
    - vim_id
    - vims
    - extra
    - {"area": "tokyo@japan"}


VNF Package API processes to be changed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* VNF package show
* VNF package delete
* VNF package update
* VNF package read
* VNF package fetch

The following table shows that the attribute required by policy check could be
queried by which API request parameter from which table and stored in which
field.

.. list-table::
  :widths: 10 28 14 12 50
  :header-rows: 1

  * - Attribute
    - Request Parameter
    - Table
    - Field
    - Sample
  * - vendor
    - vnf_package_id
    - vnf_package_vnfd
    - vnf_provider
    - "Company"

VNF Instance API processes to be changed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The change of VNF instance API processes include v1 and v2 versions.

#. VNF instance create API process needs to be changed:
   The following table shows that the attribute required by policy check could
   be queried by which API request parameter from which table and stored in
   which field.

   .. list-table::
     :widths: 10 28 14 12 50
     :header-rows: 1

     * - Attribute
       - Request Parameter
       - Table
       - Field
       - Sample
     * - vendor
       - vnfdId
       - vnf_package_vnfd
       - vnf_provider
       - "Company"

#. VNF instance instantiate API process needs to be changed:
   The following table shows that the attribute required by policy check could
   be queried by which API request parameter from which table and stored in
   which field.

   .. list-table::
     :widths: 10 28 14 12 50
     :header-rows: 1

     * - Attribute
       - Request Parameter
       - Table
       - Field
       - Sample
     * - vendor
       - vnfdId
       - vnf_instances,VnfInstanceV2
       - vnf_provider,vnfProvider
       - "Company"

#. The following API processes need to be changed:

   * VNF instance terminate
   * VNF instance heal
   * VNF instance delete
   * VNF instance show
   * VNF instance scale
   * VNF instance modify
   * VNF instance change_ext_conn
   * VNF instance change_vnfpkg (v2)

   The following table shows that the attribute required by policy check could
   be queried by which API request parameter from which table and stored in
   which field.

   .. list-table::
     :widths: 10 28 14 12 50
     :header-rows: 1

     * - Attribute
       - Request Parameter
       - Table
       - Field
       - Sample
     * - vendor
       - vnfdId
       - vnf_instances,VnfInstanceV2
       - vnf_provider,vnfProvider
       - "Company"
     * - area
       - vnfInstanceId
       - vnf_instances,VnfInstanceV2
       - vim_connection_info/extra,vimConnectionInfo/extra
       - {"area": "tokyo@japan"}
     * - tenant
       - vnfInstanceId
       - vnf_instances,VnfInstanceV2
       - vnf_metadata,instantiatedVnfInfo/metadata
       - {"tenant": "default"}

Add the Tacker Policy Filter to the List API Processes
------------------------------------------------------
In the current implementation, Tacker policy does not support filter for list
API. We will add a filter based on policy rule to filter the results of the
list operation.

The flow of a policy filter in API process to support enhanced Tacker policy.

.. seqdiag::

  seqdiag {
    Client -> Keystonemiddleware [label = "request"];
    Keystonemiddleware -> "API Process" [label = "1. Request with user info"];
    "API Process" -> Context [label = "2. Invoke policy check\n function without resource \nattributes"];
    "API Process" <-- Context;
    "API Process" -> TackerDB [label = "3. Get the accessed resources from the database"];
    "API Process" <-- TackerDB [label = "return accessed resources"];
    "API Process" -> Context [label = "4. Get user attributes"];
    Context -> Context [label = "5. Convert special \nroles to user\n attributes"];
    "API Process" <-- Context [label = "return user attributes"];
    "API Process" -> "API Process" [label = "6. Filter the list\n operation results \nbased on policy\n rules"];
    Keystonemiddleware <-- "API Process" [label = "7. Return the filtered\n result to user"];
    Client <-- Keystonemiddleware [label = "response"];
  }

Step 6 is specialized and needs to be implemented by each API process by itself.
The other steps are common or already exist steps for all API processes to be
changed:

1. Keystonemiddleware will send request to API process with user info which
   includes user roles. Special user roles will be converted to user attributes
   in later step. This step is an existing step and does not need to be
   modified.
2. API Process invokes policy check function without resource attributes. This
   step is an existing step and does not need to be modified.
3. API Process gets the accessed resources from the database. This step is an
   existing step and does not need to be modified.
4. API Process gets user attributes from context. This step is newly added and
   common.
5. Context converts special roles to user attributes, this step is newly added
   and depends on the configuration option described in the following section
   `Add a Configuration Option`_. For the conversion rules, please refer to the
   later section `Convert Special Roles to API Attributes in Context`_ for
   details.
6. API Process filters the list operation results based on policy rules. This
   step is newly added.
7. API Process returns the filtered result to user. This step is existing and
   does not need to be modified.

The List API Processes to be changed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#.  For Vim list API, the following attributes are supported by Tacker policy
    filter.

    .. list-table::
      :widths: 10 14 12 50
      :header-rows: 1

      * - Attribute
        - Table
        - Field
        - Sample
      * - area
        - vims
        - extra
        - {"area": "tokyo@japan"}

#.  For VNF package list API, the following attributes are supported by Tacker
    policy filter.

    .. list-table::
      :widths: 10 14 12 50
      :header-rows: 1

      * - Attribute
        - Table
        - Field
        - Sample
      * - vendor
        - vnf_package_vnfd
        - vnf_provider
        - "Company"

#.  For VNF instance list API, the following attributes are supported by Tacker
    policy filter.

    .. list-table::
      :widths: 10 14 12 50
      :header-rows: 1

      * - Attribute
        - Table
        - Field
        - Sample
      * - vendor
        - vnf_instances,VnfInstanceV2
        - vnf_provider,vnfProvider
        - "Company"
      * - area
        - vnf_instances,VnfInstanceV2
        - vim_connection_info/extra,vimConnectionInfo/extra
        - {"area": "tokyo@japan"}
      * - tenant
        - vnf_instances,VnfInstanceV2
        - vnf_metadata,instantiatedVnfInfo/metadata
        - {"tenant": "default"}

Convert Special Roles to API Attributes in Context
--------------------------------------------------
Special Roles' Naming Rules
~~~~~~~~~~~~~~~~~~~~~~~~~~~
We will define some special roles, and the naming of these roles follows the
following rules.

#. The role name consists of three parts: prefix + "_" + [attribute
   value/special value]
#. Supported prefixes, attribute values and special values are shown in the
   following table:

.. list-table::
  :widths: 10 14 12 50
  :header-rows: 1

  * - Prefix
    - Attribute value
    - Special value
    - Sample
  * - AREA
    - area value
    - all@all, all@{region_value}
    - AREA_tokyo@japan, AREA_all@all, AREA_all@japan
  * - VENDOR
    - vendor value
    - all
    - VENDOR_vendor_A, VENDOR_all
  * - TENANT
    - tenant value
    - all
    - TENANT_default, TENANT_all

.. note::

  As "all" is treated as a special value, the above attribute of resource
  cannot use "all" as the attribute value.

Conversion rules
~~~~~~~~~~~~~~~~
In Tacker context, we convert these special roles into API attributes and
provide them to Tacker policy. Please refer to the
`Change the API Process to Support Tacker Policy Checker`_ and
`Add the Tacker Policy Filter to the List API Processes`_ sections of this
specification for the flow chart of this change. The conversion follows the
following rules:

#.  For ordinary attribute values, they will be directly converted to user
    attribute values.

    .. list-table::
      :widths: 10 14 50
      :header-rows: 1

      * - Prefix
        - Attribute Name
        - Sample (special role -> user attribute value)
      * - AREA
        - area
        - AREA_tokyo@japan -> {"area": ["tokyo@japan"]}
      * - VENDOR
        - vendor
        - VENDOR_vendor_A -> {"vendor": ["vendor_A"]}
      * - TENANT
        - tenant value
        - TENANT_default -> {"tenant": ["default"]}

#.  For special value in policy checker, the corresponding attribute value of
    resource will be assigned to user.

    .. list-table::
      :widths: 10 14 14 50
      :header-rows: 1

      * - Prefix
        - Attribute Name
        - Special Value
        - Sample (resource attribute -> user attribute)
      * - AREA
        - area
        - all@all
        - {"area": "tokyo@japan"} -> {"area": ["tokyo@japan"]}
      * - AREA
        - area
        - all@{region_value}
        - same region value:

          .. code-block:: console

            {"area": "tokyo@japan"} -> {"area": ["tokyo@japan"]}

          different region value:

          .. code-block:: console

            any -> {"area": []}

      * - VENDOR
        - vendor
        - all
        - {"vendor": "vendor_A"} -> {"vendor": ["vendor_A"]}
      * - TENANT
        - tenant value
        - all
        - {"tenant": "default"} -> {"tenant": ["default"]}

#.  For special value "all" in policy filter, the attribute will not be used as
    a filtering attribute. Note that the "area" attribute needs to be divided
    into two parts with "@" when it is used as a filter attribute. Therefore,
    the special value "all@{region_value}" of "area" needs to be divided into
    "all" and "{region_value}". The part of "area" is not used as a filter
    attribute, but "{region_value}" should be used as a filter attribute because
    it is the special value "all".

Add a Configuration Option
--------------------------
As the function defined in this specification changes the default behavior of
the Tacker API policy, it is suggested to add a configuration option to the
``tacker.conf`` file. Therefore, a user can choose whether to enable this
function or not.

.. code-block::

  [oslo_policy]
  enhanced_tacker_policy = False

As a suggested implementation, when the enhanced_tacker_policy is True, the
function of converting special roles to user attributes in context described in
the previous chapter `Convert special roles to API attributes in context`_
takes effect; When enhanced_tacker_policy is False, this function will not take
effect.

.. note::

  When enhanced_tacker_policy is False, special roles will not be converted to
  user attributes, then users will not have the enhanced policy attributes such
  as area, vendor and tenant. At this time, if the enhanced policy
  attributes are used as comparison attributes in the policy rule, this rule
  will prevent users from accessing any resource as the comparison result is
  always false.

Policy and Roles Samples
------------------------

Policy Examples
~~~~~~~~~~~~~~~

.. note::

  For details on Tacker policy configuration, please refer to Tacker
  Configuration Guide [#tacker_policy]_.

.. code-block:: yaml

  # Decides what is required for the 'is_admin:True' check to succeed.
  "context_is_admin": "role:admin"

  # Default rule for most non-Admin APIs.
  "admin_or_owner": "is_admin:True or project_id:%(project_id)s"

  # Default rule for most Admin APIs.
  "admin_only": "is_admin:True"

  # Default rule for sharing vims.
  "shared": "field:vims:shared=True"

  # Default rule for most non-Admin APIs.
  "default": "rule:admin_or_owner"

  # For manager
  "manager_and_owner": "rule:manager and project_id:%(project_id)s"

  # For user
  "owner": "project_id:%(project_id)s"

  # VIM resource attributes compare rule.
  "vim_attrs_cmp": "area:%(area)s"

  # Register a VIM.
  # Post  /v1.0/vims
  "create_vim": "@"

  # List VIMs or show a VIM.
  # GET /v1.0/vims
  # GET /v1.0/vims/{vim_id}
  "get_vim": "rule:vim_attrs_cmp and rule:owner"

  # Update a VIM.
  # PUT /v1.0/vims/{vim_id}
  "update_vim": "rule:vim_attrs_cmp and rule:manager_and_owner"

  # Delete a VIM.
  # DELETE /v1.0/vims/{vim_id}
  "delete_vim": "rule:vim_attrs_cmp and rule:manager_and_owner"

  # vnf_packages resource attributes compare rule.
  "vnf_pkg_attrs_cmp": "vendor:%(vendor)s"

  # Create a VNF package.
  # POST  /vnf_packages
  "os_nfv_orchestration_api:vnf_packages:create": "rule:admin_or_owner"

  # Show a VNF package.
  # GET  /vnf_packages/{vnf_package_id}
  "os_nfv_orchestration_api:vnf_packages:show": "rule:vnf_pkg_attrs_cmp and rule:owner"

  # List all VNF packages.
  # GET  /vnf_packages/
  "os_nfv_orchestration_api:vnf_packages:index": "rule:vnf_pkg_attrs_cmp and rule:owner"

  # Delete a VNF package.
  # DELETE  /vnf_packages/{vnf_package_id}
  "os_nfv_orchestration_api:vnf_packages:delete": "rule:vnf_pkg_attrs_cmp and rule:manager_and_owner"

  # Fetch the contents of an on-boarded VNF Package.
  # GET  /vnf_packages/{vnf_package_id}/package_content
  "os_nfv_orchestration_api:vnf_packages:fetch_package_content": "rule:vnf_pkg_attrs_cmp and rule:owner"

  # Upload a VNF package content.
  # PUT  /vnf_packages/{vnf_package_id}/package_content
  "os_nfv_orchestration_api:vnf_packages:upload_package_content": "rule:admin_or_owner"

  # Upload a VNF package content from URI.
  # POST  /vnf_packages/{vnf_package_id}/package_content/upload_from_uri
  "os_nfv_orchestration_api:vnf_packages:upload_from_uri": "rule:admin_or_owner"

  # Update information of VNF package.
  # PATCH  /vnf_packages/{vnf_package_id}
  "os_nfv_orchestration_api:vnf_packages:patch": "rule:vnf_pkg_attrs_cmp  and rule:manager_and_owner"

  # Read the content of the VNFD within a VNF package.
  # GET  /vnf_packages/{vnf_package_id}/vnfd
  "os_nfv_orchestration_api:vnf_packages:get_vnf_package_vnfd": "rule:vnf_pkg_attrs_cmp and rule:owner"

  # Read the content of the artifact within a VNF package.
  # GET  /vnf_packages/{vnfPkgId}/artifacts/{artifactPath}
  "os_nfv_orchestration_api:vnf_packages:fetch_artifact": "rule:vnf_pkg_attrs_cmp and rule:owner"

  # vnflcm create attributes compare rule.
  "vnflcm_create_attrs_cmp": "vendor:%(vendor)s and rule:manager_and_owner"

  # vnflcm instantiate attributes compare rule.
  "vnflcm_inst_attrs_cmp": "vendor:%(vendor)s and rule:manager_and_owner"

  # vnflcm resource attributes compare rule.
  "vnflcm_attrs_cmp": "area:%(area)s and vendor:%(vendor)s and tenant:%(tenant)s"

  # Get API Versions.
  # GET  /vnflcm/v1/api_versions
  "os_nfv_orchestration_api:vnf_instances:api_versions": "@"

  # Create VNF instance.
  # POST  /vnflcm/v1/vnf_instances
  "os_nfv_orchestration_api:vnf_instances:create": "rule:vnflcm_create_attrs_cmp and rule:manager_and_owner"

  # Instantiate VNF instance.
  # POST  /vnflcm/v1/vnf_instances/{vnfInstanceId}/instantiate
  "os_nfv_orchestration_api:vnf_instances:instantiate": "rule:vnflcm_inst_attrs_cmp and rule:manager_and_owner"

  # Query an Individual VNF instance.
  # GET  /vnflcm/v1/vnf_instances/{vnfInstanceId}
  "os_nfv_orchestration_api:vnf_instances:show": "rule:vnflcm_attrs_cmp and rule:owner"

  # Terminate a VNF instance.
  # POST  /vnflcm/v1/vnf_instances/{vnfInstanceId}/terminate
  "os_nfv_orchestration_api:vnf_instances:terminate": "rule:vnflcm_attrs_cmp and rule:manager_and_owner"

  # Heal a VNF instance.
  # POST  /vnflcm/v1/vnf_instances/{vnfInstanceId}/heal
  "os_nfv_orchestration_api:vnf_instances:heal": "rule:vnflcm_attrs_cmp and rule:manager_and_owner"

  # Scale a VNF instance.
  # POST  /vnflcm/v1/vnf_instances/{vnfInstanceId}/scale
  "os_nfv_orchestration_api:vnf_instances:scale": "rule:vnflcm_attrs_cmp and rule:manager_and_owner"

  # Query an Individual VNF LCM operation occurrence.
  # GET  /vnflcm/v1/vnf_lcm_op_occs/{vnfLcmOpOccId}
  "os_nfv_orchestration_api:vnf_instances:show_lcm_op_occs": "rule:admin_or_owner"

  # Query VNF LCM operation occurrence.
  # GET  /vnflcm/v1/vnf_lcm_op_occs
  "os_nfv_orchestration_api:vnf_instances:list_lcm_op_occs": "rule:admin_or_owner"

  # Query VNF instances.
  # GET  /vnflcm/v1/vnf_instances
  "os_nfv_orchestration_api:vnf_instances:index": "rule:vnflcm_attrs_cmp and rule:owner"

  # Delete an Individual VNF instance.
  # DELETE  /vnflcm/v1/vnf_instances/{vnfInstanceId}
  "os_nfv_orchestration_api:vnf_instances:delete": "rule:vnflcm_attrs_cmp and rule:manager_and_owner"

  # Update an Individual VNF instance.
  # PATCH  /vnflcm/v1/vnf_instances/{vnfInstanceId}
  "os_nfv_orchestration_api:vnf_instances:update_vnf": "rule:vnflcm_attrs_cmp and rule:manager_and_owner"

  # Rollback a VNF instance.
  # POST  /vnflcm/v1/vnf_lcm_op_occs/{vnfLcmOpOccId}/rollback
  "os_nfv_orchestration_api:vnf_instances:rollback": "rule:admin_or_owner"

  # Cancel a VNF instance.
  # POST  /vnflcm/v1/vnf_lcm_op_occs/{vnfLcmOpOccId}/cancel
  "os_nfv_orchestration_api:vnf_instances:cancel": "rule:admin_or_owner"

  # Fail a VNF instance.
  # POST  /vnflcm/v1/vnf_lcm_op_occs/{vnfLcmOpOccId}/fail
  "os_nfv_orchestration_api:vnf_instances:fail": "rule:admin_or_owner"

  # Retry a VNF instance.
  # POST  /vnflcm/v1/vnf_lcm_op_occs/{vnfLcmOpOccId}/retry
  "os_nfv_orchestration_api:vnf_instances:retry": "rule:admin_or_owner"

  # Change external VNF connectivity.
  # POST  /vnflcm/v1/vnf_instances/{vnfInstanceId}/change_ext_conn
  "os_nfv_orchestration_api:vnf_instances:change_ext_conn": "rule:vnflcm_attrs_cmp and rule:manager_and_owner"

  # Get API Versions.
  # GET  /vnflcm/v2/api_versions
  "os_nfv_orchestration_api_v2:vnf_instances:api_versions": "@"

  # Create VNF instance.
  # POST  /vnflcm/v2/vnf_instances
  "os_nfv_orchestration_api_v2:vnf_instances:create": "rule:vnflcm_create_attrs_cmp and rule:manager_and_owner"

  # Query VNF instances.
  # GET  /vnflcm/v2/vnf_instances
  "os_nfv_orchestration_api_v2:vnf_instances:index": "rule:vnflcm_attrs_cmp and rule:owner"

  # Query an Individual VNF instance.
  # GET  /vnflcm/v2/vnf_instances/{vnfInstanceId}
  "os_nfv_orchestration_api_v2:vnf_instances:show": "rule:vnflcm_attrs_cmp and rule:owner"

  # Delete an Individual VNF instance.
  # DELETE  /vnflcm/v2/vnf_instances/{vnfInstanceId}
  "os_nfv_orchestration_api_v2:vnf_instances:delete": "rule:vnflcm_attrs_cmp and rule:manager_and_owner"

  # Modify VNF instance information.
  # PATCH  /vnflcm/v2/vnf_instances/{vnfInstanceId}
  "os_nfv_orchestration_api_v2:vnf_instances:update": "rule:vnflcm_attrs_cmp and rule:manager_and_owner"

  # Instantiate VNF instance.
  # POST  /vnflcm/v2/vnf_instances/{vnfInstanceId}/instantiate
  "os_nfv_orchestration_api_v2:vnf_instances:instantiate": "rule:vnflcm_inst_attrs_cmp and rule:manager_and_owner"

  # Terminate VNF instance.
  # POST  /vnflcm/v2/vnf_instances/{vnfInstanceId}/terminate
  "os_nfv_orchestration_api_v2:vnf_instances:terminate": "rule:vnflcm_attrs_cmp and rule:manager_and_owner"

  # Scale VNF instance.
  # POST  /vnflcm/v2/vnf_instances/{vnfInstanceId}/scale
  "os_nfv_orchestration_api_v2:vnf_instances:scale": "rule:vnflcm_attrs_cmp and rule:manager_and_owner"

  # Heal VNF instance.
  # POST  /vnflcm/v2/vnf_instances/{vnfInstanceId}/heal
  "os_nfv_orchestration_api_v2:vnf_instances:heal": "rule:vnflcm_attrs_cmp and rule:manager_and_owner"

  # Change external VNF connectivity.
  # POST  /vnflcm/v2/vnf_instances/{vnfInstanceId}/change_ext_conn
  "os_nfv_orchestration_api_v2:vnf_instances:change_ext_conn": "rule:vnflcm_attrs_cmp and rule:manager_and_owner"

  # Change VNF package.
  # POST  /vnflcm/v2/vnf_instances/{vnfInstanceId}/change_vnfpkg
  "os_nfv_orchestration_api_v2:vnf_instances:change_vnfpkg": "rule:vnflcm_attrs_cmp and rule:manager_and_owner"

  # Create subscription.
  # POST  /vnflcm/v2/subscriptions
  "os_nfv_orchestration_api_v2:vnf_instances:subscription_create": "@"

  # List subscription.
  # GET  /vnflcm/v2/subscriptions
  "os_nfv_orchestration_api_v2:vnf_instances:subscription_list": "@"

  # Show subscription.
  # GET  /vnflcm/v2/vnf_instances/{subscriptionId}
  "os_nfv_orchestration_api_v2:vnf_instances:subscription_show": "@"

  # Delete subscription.
  # DELETE  /vnflcm/v2/vnf_instances/{subscriptionId}
  "os_nfv_orchestration_api_v2:vnf_instances:subscription_delete": "@"

  # List VnfLcmOpOcc.
  # GET  /vnflcm/v2/vnf_lcm_op_occs
  "os_nfv_orchestration_api_v2:vnf_instances:lcm_op_occ_list": "@"

  # Show VnfLcmOpOcc.
  # GET  /vnflcm/v2/vnf_lcm_op_occs/{vnfLcmOpOccId}
  "os_nfv_orchestration_api_v2:vnf_instances:lcm_op_occ_show": "@"

  # Retry VnfLcmOpOcc.
  # POST  /vnflcm/v2/vnf_lcm_op_occs/{vnfLcmOpOccId}/retry
  "os_nfv_orchestration_api_v2:vnf_instances:lcm_op_occ_retry": "@"

  # Rollback VnfLcmOpOcc.
  # POST  /vnflcm/v2/vnf_lcm_op_occs/{vnfLcmOpOccId}/rollback
  "os_nfv_orchestration_api_v2:vnf_instances:lcm_op_occ_rollback": "@"

  # Fail VnfLcmOpOcc.
  # POST  /vnflcm/v2/vnf_lcm_op_occs/{vnfLcmOpOccId}/fail
  "os_nfv_orchestration_api_v2:vnf_instances:lcm_op_occ_fail": "@"

  # Delete VnfLcmOpOcc.
  # DELETE  /vnflcm/v2/vnf_lcm_op_occs/{vnfLcmOpOccId}
  "os_nfv_orchestration_api_v2:vnf_instances:lcm_op_occ_delete": "@"

Roles Examples
~~~~~~~~~~~~~~
Create the following roles:

* admin
* member
* reader
* manager
* AREA_area_A@region_A
* AREA_area_B@region_A
* AREA_area_A@region_B
* AREA_area_B@region_B
* AREA_all@region_A
* AREA_all@region_B
* AREA_all@all
* VENDOR_vendor_A
* VENDOR_vendor_B
* VENDOR_all
* TENANT_default
* TENANT_tenant_A
* TENANT_all

The root user needs to be assigned the following roles:

* admin
* manager
* AREA_all@all
* VENDOR_all
* TENANT_all

The region manager needs to be assigned the following roles:

* manager
* AREA_all@region_A (or AREA_all@region_B)
* VENDOR_all
* TENANT_all

The area manager and the tenant (area) manager
need to be assigned the following roles:

* manager
* AREA_area_A@region_A (or AREA_area_B@region_A or
  AREA_area_A@region_B or AREA_area_B@region_B)
* VENDOR_all
* TENANT_all

.. note::
  The difference between "area manager" and
  "tenant (area) manager" is the owned project.
  "tenant (area) manager" generally has one project;
  while "area manager" can have multiple projects.

The tenant manager needs to be assigned the following roles:

* manager
* AREA_all@all
* VENDOR_all
* TENANT_all

The tenant user needs to be assigned the following roles:

* member or reader
* AREA_all@all
* VENDOR_all
* TENANT_all

The tenant (area) user needs to be assigned the following roles:

* member or reader
* AREA_area_A@region_A (or AREA_area_B@region_A or
  AREA_area_A@region_B or AREA_area_B@region_B)
* VENDOR_all
* TENANT_all

The vendor manager needs to be assigned the following roles:
* manager
* AREA_all@all
* VENDOR_vendor_A (or VENDOR_vendor_B)
* TENANT_all

Alternatives
------------

None

Data model impact
-----------------

None

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

As the resources created in the previous version of Tacker may not have enhanced
policy attributes, if the enhanced policy attributes are used as comparison
attributes in the policy rule, this rule will prevent users from accessing those
resources without these attributes as the comparison result is always false.

Performance Impact
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
  Yuta Kazato <yuta.kazato.nw@hco.ntt.co.jp>

  Hiromu Asahina <hiromu.asahina.az@hco.ntt.co.jp>

Other contributors:
  Koji Shimizu <shimizu.koji@fujitsu.com>

  Yoshiyuki Katada <katada.yoshiyuk@fujitsu.com>

  Ayumu Ueha <ueha.ayumu@fujitsu.com>

  Yusuke Niimi <niimi.yusuke@fujitsu.com>

Work Items
----------

+ Implement Tacker to support:

  + Add Additional Attributes to Resources When Be Created
  + Change the API Process to Support Tacker Policy Checker
  + Add the Tacker Policy Filter to the List API Processes
  + Convert Special Roles to API Attributes in Context
  + Add a Configuration Option
  + Policy and Roles Samples

+ Add new unit and functional tests.
+ Write Tacker documentation to explain how to use the function described in
  this specification.

Dependencies
============

None

Testing
=======

Unit and functional tests will be added to cover cases required
in this specification.

Documentation Impact
====================

Description about enhanced Tacker API policy function will be added to the
Tacker user guide.

References
==========

.. [#oslo.policy] https://docs.openstack.org/oslo.policy/latest/
.. [#tacker_policy] https://docs.openstack.org/tacker/latest/configuration/index.html#policy
