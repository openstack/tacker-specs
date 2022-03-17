===============================================
Add multi-tenant policy on Lifecycle Management
===============================================

https://blueprints.launchpad.net/tacker/+spec/multi-tenant-policy

This spec shows problems in Lifecycle Management on multi-tenant case and
proposed changes to solve them.
The aim of this specification is to separate resources related to ETSI
NFV-SOL based VNF management by using tenant.
The target is the following resources.

- Virtualized Infrastructure Managers (VIMs)

  - /v1.0/vims

- Virtualized Network Function Packages (VNF packages)

  - /vnfpkgm/v1/vnf_packages

- Virtualized Network Function Lifecycle Management Interface (VNF LCM)

  - /vnflcm/v1/vnf_instances

  - /vnflcm/v1/vnf_lcm_op_occs

  - /vnflcm/v1/subscriptions

Problem description
===================

In the current Tacker implementation, resource separation using tenants
does not work correctly.
VNF LCMs and those used in their operation should be separated by tenants.
There are two problems in multi-tenant case.

1) No support for subscription, LCM operation occurrence on different tenants.
------------------------------------------------------------------------------

Subscription and LCM operation occurrence are not separated by tenant.
We cannot get the information for each tenant correctly.

We also have to be careful about notification.
Subscription API can only be set to Callback URL.
In such a case, Notification can be sent to show the status of Lifecycle
Management operations that occurred in different tenants.

2) No restriction in associating VIM and VNF with different tenants.
--------------------------------------------------------------------

Currently Tacker can associate a VIM with a VNF, even if both belong to
different tenants.

For example, admin user can instantiate VNF using VIM belonging to different
tenant than VNF.
A non-admin user cannot terminate VNF because the non-admin user doesn't belong
to the tenant of VIM.

#. The non-admin user creates a VNF.
#. The admin user instantiates the VNF by specifying a VIM to which the non-admin
   user doesn't belong.
#. The non-admin user cannot terminates the VNF.

It does not problem that the admin user can get resource information for VNF or
operate VNF LCM.
The problem is that the admin user can operate the LCM on a VIM that belongs to
a different tenant than the VNF belongs to tenant.

Proposed change
===============

In order to solve these problems, we propose the following changes.

1) Add tenant_id to VnfLcmSubscriptions and VnfLcmOpOccs:
---------------------------------------------------------

We add ``tenant_id`` field in DB tables ``vnf_lcm_subscriptions`` and
``vnf_lcm_op_occs`` as well as objects ``VnfLcmSubscriptions`` and
``VnfLcmOpOccs``.

Users can get the above information only in their own tenant.

2) Specifying tenant in sending notification:
---------------------------------------------

Notification is modified to check the tenant which is assigned during
subscription sequence and then notify events to the specified tenant.

.. seqdiag::

    seqdiag {
        node_width = 80;
        edge_length = 100;

        "Client belong to tenant-B"
        "Tacker-server"
        "Tacker-condunctor"
        "Notify Receiver of tenant-A"
        "Notify Receiver of tenant-B"

        "Client belong to tenant-B" -> "Tacker-server"
            [label = "Request LCM Operation"];
        "Tacker-server" -> "Tacker-condunctor"
            [label = "Execute LCM Operation"];
        "Tacker-condunctor" -> "Tacker-condunctor"
            [label = "Checking tenant of operation and vnf instance"];
        "Tacker-condunctor" -> "Notify Receiver of tenant-B"
            [label = "Send LCM Operation Notification"];
        "Tacker-condunctor" <-- "Notify Receiver of tenant-B"
        "Tacker-condunctor" -> "Tacker-condunctor"
            [label = "Execute LCM Process"];

    }

3) Prohibiting VIM and VNF association created in different tenants:
--------------------------------------------------------------------

Tacker only allows associating a VIM with a VNF that belongs to the same
tenant as the VIM.

.. seqdiag::

    seqdiag {
        node_width = 80;
        edge_length = 100;

        "client"
        "tacker-server"
        "tacker-condunctor"
        "vnflcm_driver"
        "infra_driver"

        "client" -> "tacker-server"
            [label = "Request Instantiate VNF"];
        "client" <- "tacker-server"
        "tacker-server" --> "tacker-condunctor"
            [label = "Execute instantiate"];
        "tacker-condunctor" -> "vnflcm_driver"
            [label = "Execute instantiate_vnf"];
        "vnflcm_driver" -> "vnflcm_driver"
            [label = "Verify VIM and VNF belong to the same Tenant"];
        === if same tenant ===
        "vnflcm_driver" -> "infra_driver"
            [label = "create VNF resrouces"];
        === if not same tenant ===
        "tacker-condunctor" <- "vnflcm_driver"
            [label = "return TenantMatchFailure"];

    }

How to design Functional Testing
--------------------------------

To address these three proposed change, we need to confirm that the solution
is working in the multi tenant environment.
However, the existing functional test is only for single tenant verification,
and it can't be verified from the multi tenant perspective.
So we need to add a new test case to see the multi tenant.

To see multi tenant working, we need at least two different tenants.
This specification configures User, VIM, and VNF for each tenant, operates the
VNF Package and VNF LCM on each tenant, and verifies that notification of
operation results only reaches the subscription notification server belonging
to its tenant.


Multi Tenant Functional Test Directory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Adding a test for this specification to an existing Functional Test has a large
impact and complicates the testing perspective.
Therefore, we will add a new test case for Multi Tenant.

.. code-block::

    tacker/tacker/tests/functional/
        legacy/
        sol/
        sol_kuberenates/
        sol_separatednfvo/
        sol_v2/
        sol_multi_tenant/   <--- new add test case


Test perspective for proposed changes (1) and (2)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to verify the operation of proposed changes (1) and (2) in this Spec,
the following test cases are added.

- Register, show, list Subscription
    - User A belongs to Project A registers Subscription A
      (Notification Server A)
    - User B belongs to Project B registers Subscription B
      (Notification Server B)
    - User A belongs to Project A gets the subscription list and confirms that
      only Subscription A is printed
    - User B belongs to Project B gets the subscription list and confirms that
      only Subscription B is printed
    - User A belongs to Project A gets information about Subscription A, and
      information about Subscription A is output.
    - User A belongs to Project A can't get information about Subscription B,
      and should not get information of Subscription B.
    - User B belongs to Project B gets information about Subscription B, and
      information about Subscription B is output.
    - User B belongs to Project B can't get information about Subscription A,
      and should not get information of Subscription A.

.. seqdiag::

    seqdiag {
        node_width = 80;
        edge_length = 100;

        "Test Class"
        "User A"
        "User B"
        "Tacker"
        "Subscription A"
        "Subscription B"

        "Test Class" -> "User A" [label = "Set User"];
        "Test Class" <- "User A";

        "Test Class" -> "User B" [label = "Set User"];
        "Test Class" <- "User B";

        "User A" -> "Tacker" [label = "Register Subscription"];
            "Tacker" -> "Subscription A" [label = "Registered Subscription"];
            "Tacker" <- "Subscription A";
        "User A" <-- "Tacker" [label = "Registered OK"];

        "User B" -> "Tacker" [label = "Register Subscription"];
            "Tacker" -> "Subscription B" [label = "Registered Subscription"];
            "Tacker" <- "Subscription B";
        "User B" <-- "Tacker" [label = "Registered OK"];

        "User A" -> "Tacker"
            [label = "Get subscription List of Subscription A"];
            "Tacker" -> "Subscription A"
                [label = "Return list of only Subscription A"];
            "Tacker" <- "Subscription A";
        "User A" <-- "Tacker" [label = "Get list of Subscription A"];

        "User B" -> "Tacker"
            [label = "Get subscription List of Subscription B"];
            "Tacker" -> "Subscription B"
                [label = "Return list of only Subscription B"];
            "Tacker" <- "Subscription B";
        "User B" <-- "Tacker" [label = "Get list of Subscription B"];

        "User A" -> "Tacker" [label = "Show subscription of Subscription A"];
            "Tacker" -> "Subscription A" [label = "Return of Subscription A"];
            "Tacker" <- "Subscription A";
        "User A" <-- "Tacker" [label = "Showed Subscription A"];

        "User A" -> "Tacker" [label = "Show subscription of Subscription B"];
        "User A" <-- "Tacker" [label = "Fail to showed Subscription A"];

        "User B" -> "Tacker" [label = "Show subscription of Subscription B"];
            "Tacker" -> "Subscription B" [label = "Return of Subscription B"];
            "Tacker" <- "Subscription B";
        "User B" <-- "Tacker" [label = "Showed Subscription B"];

        "User B" -> "Tacker" [label = "Show subscription of Subscription A"];
        "User B" <-- "Tacker" [label = "Fail to showed Subscription A"];
    }

- Create, upload, show, list VNF Package
    - User A belongs to Project A create VNF Package A
    - User A belongs to Project A upload VNF Package A
    - User B belongs to Project B create VNF Package B
    - User B belongs to Project B upload VNF Package B
    - User A belongs to Project A gets the VNF Package list and confirms that
      only VNF Package A is output
    - User B belongs to Project B gets the VNF Package list and confirms that
      only VNF Package B is output
    - User A belongs to Project A show VNF Package A
    - User B belongs to Project B show VNF Package B
    - User A belongs to Project A show VNF Package B, and should fail
    - User B belongs to Project B show VNF Package A, and should fail

.. seqdiag::

    seqdiag {
        node_width = 80;
        edge_length = 100;

        "Test Class"
        "User A"
        "User B"
        "Tacker"
        "VNF Package A"
        "VNF Package B"

        "Test Class" -> "User A" [label = "Set User"];
        "Test Class" <- "User A";

        "Test Class" -> "User B" [label = "Set User"];
        "Test Class" <- "User B";

        "User A" -> "Tacker" [label = "Create VNF Package A"];
            "Tacker" -> "VNF Package A" [label = "Create VNF Package A"];
            "Tacker" <- "VNF Package A";
        "User A" <-- "Tacker" [label = "Created VNF Package A"];

        "User A" -> "Tacker" [label = "Upload VNF Package A"];
            "Tacker" -> "VNF Package A" [label = "Upload VNF Package A"];
            "Tacker" <- "VNF Package A";
        "User A" <-- "Tacker" [label = "Uploaded VNF Package A"];

        "User B" -> "Tacker" [label = "Create VNF Package B"];
            "Tacker" -> "VNF Package B" [label = "Create VNF Package B"];
            "Tacker" <- "VNF Package B";
        "User B" <-- "Tacker" [label = "Created VNF Package B"];

        "User B" -> "Tacker" [label = "Upload VNF Package B"];
            "Tacker" -> "VNF Package B" [label = "Upload VNF Package B"];
            "Tacker" <- "VNF Package B";
        "User B" <-- "Tacker" [label = "Uploaded VNF Package B"];

        "User A" -> "Tacker" [label = "Get VNF Package List of VNF Package A"];
            "Tacker" -> "VNF Package A"
                [label = "Return list of only VNF Package A"];
            "Tacker" <- "VNF Package A";
        "User A" <-- "Tacker" [label = "Get list of VNF Package A"];

        "User B" -> "Tacker" [label = "Get VNF Package List of VNF Package B"];
            "Tacker" -> "VNF Package B"
                [label = "Return list of only VNF Package B"];
            "Tacker" <- "VNF Package B";
        "User B" <-- "Tacker" [label = "Get list of VNF Package B"];

        "User A" -> "Tacker" [label = "Show VNF Package A"];
            "Tacker" -> "VNF Package A" [label = "Show VNF Package A"];
            "Tacker" <- "VNF Package A";
        "User A" <-- "Tacker" [label = "Showed VNF Package A"];

        "User A" -> "Tacker" [label = "Show VNF Package B"];
        "User A" <-- "Tacker" [label = "Fail to showed VNF Package B"];

        "User B" -> "Tacker" [label = "Show VNF Package B"];
            "Tacker" -> "VNF Package B" [label = "Return of VNF Package B"];
            "Tacker" <- "VNF Package B";
        "User B" <-- "Tacker" [label = "Showed VNF Package B"];

        "User B" -> "Tacker" [label = "Show VNF Package A"];
        "User B" <-- "Tacker" [label = "Fail to showed VNF Package A"];
    }

- Create VNF
    - User A belongs to Project A uses VNF Package B to create VNF Instance B,
      and should fail
    - User B belongs to Project B uses VNF Package A to create VNF Instance A,
      and should fail
    - User A belongs to Project A uses VNF Package A to create VNF Instance A
    - User B belongs to Project B uses VNF Package B to create VNF Instance B
    - Verify that Notification Server A is able to get the Create information
      for VNF Instance A
    - Verify that Notification Server B is unable to get the Create information
      for VNF Instance A
    - Verify that Notification Server B is able to get the Create information
      for VNF Instance B
    - Verify that Notification Server A is unable to get the Create information
      for VNF Instance B

.. seqdiag::

    seqdiag {
        node_width = 80;
        edge_length = 100;

        "Test Class"
        "User A"
        "User B"
        "Tacker"
        "VNF A"
        "VNF B"
        "Notification Server A"
        "Notification Server B"

        "Test Class" -> "User A" [label = "Set User"];
        "Test Class" <- "User A";

        "Test Class" -> "User B" [label = "Set User"];
        "Test Class" <- "User B";

        "User A" -> "Tacker" [label = "Create VNF B using VNF Package B"];
        "User A" <-- "Tacker" [label = "Failed to create VNF B"];

        "User B" -> "Tacker" [label = "Create VNF A using VNF Package A"];
        "User B" <-- "Tacker" [label = "Failed to create VNF A"];

        "User A" -> "Tacker" [label = "Create VNF A"];
            "Tacker" -> "VNF A" [label = "Create VNF A"];
            "Tacker" <- "VNF A";
            "Tacker" -> "Notification Server A" [label = "send notification"];
            "Tacker" <- "Notification Server A";
        "User A" <-- "Tacker" [label = "Created VNF A"];

        "User B" -> "Tacker" [label = "Create VNF B"];
            "Tacker" -> "VNF B" [label = "Create VNF B"];
            "Tacker" <- "VNF B";
            "Tacker" -> "Notification Server B" [label = "send notification"];
            "Tacker" <- "Notification Server B";
        "User B" <-- "Tacker" [label = "Created VNF B"];

        "User A" -> "Notification Server A"
            [label = "Check the exist notification that created VNF A"];
        "User A" <-- "Notification Server A"
            [label = "check existing notification that created VNF A"];

        "User B" -> "Notification Server B"
            [label = "Check the not exist notification that created VNF A"];
        "User B" <-- "Notification Server B"
            [label = "check not existing notification that created VNF A"];

        "User B" -> "Notification Server B"
            [label = "Check the exist notification that created VNF B"];
        "User B" <-- "Notification Server B"
            [label = "check existing notification that created VNF B"];

        "User A" -> "Notification Server A"
            [label = "Check the not exist notification that created VNF B"];
        "User A" <-- "Notification Server A"
            [label = "check not existing notification that created VNF B"];


    }

- Instantiate VNF
    - User A belongs to Project A instantiate VNF Instance B, and should fail
    - User B belongs to Project B instantiate VNF Instance A, and should fail
    - User A belongs to Project A instantiate VNF Instance A
    - User B belongs to Project B instantiate VNF Instance B
    - User A belongs to Project A gets LcmOpOccs List, and should get
      LcmOpOccs of only VNF Instance A
    - User B belongs to Project B gets LcmOpOccs List, and should get
      LcmOpOccs of only VNF Instance B
    - User A belongs to Project A shows LcmOpOccs of VNF Instance A
    - User A belongs to Project A shows LcmOpOccs of VNF Instance B, and should
      not get information of LcmOpOccs of VNF Instance B
    - User B belongs to Project B shows LcmOpOccs of VNF Instance B
    - User B belongs to Project B shows LcmOpOccs of VNF Instance A, and should
      not get information of LcmOpOccs of VNF Instance A
    - Verify that Notification Server A is able to get the Instantiation
      information for VNF Instance A
    - Verify that Notification Server B is unable to get the Instantiation
      information for VNF Instance A
    - Verify that Notification Server B is able to get the Instantiate
      information for VNF Instance B
    - Verify that Notification Server A is unable to get the Instantiate
      information for VNF Instance B

.. seqdiag::

    seqdiag {
        node_width = 80;
        edge_length = 100;

        "Test Class"
        "User A"
        "User B"
        "Tacker"
        "VNF A"
        "VNF B"
        "VnfLcmOpOccs A"
        "VnfLcmOpOccs B"
        "Notification Server A"
        "Notification Server B"

        "Test Class" -> "User A" [label = "Set User"];
        "Test Class" <- "User A";

        "Test Class" -> "User B" [label = "Set User"];
        "Test Class" <- "User B";

        "User A" -> "Tacker" [label = "Instantiate VNF B"];
        "User A" <-- "Tacker" [label = "Failed to Instantiate VNF B"];

        "User B" -> "Tacker" [label = "Instantiate VNF A"];
        "User B" <-- "Tacker" [label = "Failed to Instantiate VNF A"];

        "User A" -> "Tacker" [label = "Instantiate VNF A"];
            "Tacker" -> "VNF A" [label = "Instantiate VNF A"];
            "Tacker" <- "VNF A";
            "Tacker" -> "Notification Server A" [label = "send notification"];
            "Tacker" <- "Notification Server A";
        "User A" <-- "Tacker" [label = "Instantiated VNF A"];

        "User B" -> "Tacker" [label = "Instantiate VNF B"];
            "Tacker" -> "VNF B" [label = "Instantiate VNF B"];
            "Tacker" <- "VNF B";
            "Tacker" -> "Notification Server B" [label = "send notification"];
            "Tacker" <- "Notification Server B";
        "User B" <-- "Tacker" [label = "Instantiated VNF B"];

        "User A" -> "Tacker" [label = "Get VnfLcmOpOccs List of only VNF A"];
            "Tacker" -> "VnfLcmOpOccs A"
                [label = "Return list of VnfLcmOpOccs"];
            "Tacker" <- "VnfLcmOpOccs A";
        "User A" <-- "Tacker" [label = "Get list of VnfLcmOpOccs"];

        "User B" -> "Tacker" [label = "Get VnfLcmOpOccs List of only VNF B"];
            "Tacker" -> "VnfLcmOpOccs B"
                [label = "Return list of VnfLcmOpOccs"];
            "Tacker" <- "VnfLcmOpOccs B";
        "User B" <-- "Tacker" [label = "Get list of VnfLcmOpOccs"];

        "User A" -> "Tacker" [label = "Show VnfLcmOpOccs A"];
            "Tacker" -> "VnfLcmOpOccs A" [label = "Show VnfLcmOpOccs A"];
            "Tacker" <- "VnfLcmOpOccs A";
        "User A" <-- "Tacker" [label = "Showed VnfLcmOpOccs A"];

        "User A" -> "Tacker" [label = "Show VnfLcmOpOccs B"];
        "User A" <-- "Tacker" [label = "failed to show VnfLcmOpOccs B"];

        "User B" -> "Tacker" [label = "Show VnfLcmOpOccs B"];
            "Tacker" -> "VnfLcmOpOccs B" [label = "Show VnfLcmOpOccs B"];
            "Tacker" <- "VnfLcmOpOccs B";
        "User B" <-- "Tacker" [label = "Showed VnfLcmOpOccs B"];

        "User B" -> "Tacker" [label = "Show VnfLcmOpOccs A"];
        "User B" <-- "Tacker" [label = "failed to show VnfLcmOpOccs A"];

        "User A" -> "Notification Server A"
            [label = "Check the exist notification that Instantiated VNF A"];
        "User A" <-- "Notification Server A"
            [label = "check existing notification that Instantiated VNF A"];

        "User B" -> "Notification Server B"
            [label = "Check the not exist notification that Instantiated VNF A"];
        "User B" <-- "Notification Server B"
            [label = "check not existing notification that Instantiated VNF A"];

        "User B" -> "Notification Server B"
            [label = "Check the exist notification that Instantiated VNF B"];
        "User B" <-- "Notification Server B"
            [label = "check existing notification that Instantiated VNF B"];

        "User A" -> "Notification Server A"
            [label = "Check the not exist notification that Instantiated VNF B"];
        "User A" <-- "Notification Server A"
            [label = "check not existing notification that Instantiated VNF B"];


    }

- Terminate VNF
    - User A belongs to Project A terminate VNF Instance B, and should fail
    - User B belongs to Project B terminate VNF Instance A, and should fail
    - User A belongs to Project A terminate VNF Instance A
    - User B belongs to Project B terminate VNF Instance B
    - User A belongs to Project A gets LcmOpOcc List, and should get only
      LcmOpOcc of VNF Instance A
    - User B belongs to Project B gets LcmOpOcc List, and should get only
      LcmOpOcc of VNF Instance B
    - User A belongs to Project A shows LcmOpOcc of VNF Instance A
    - User A belongs to Project A shows LcmOpOcc of VNF Instance B, and should
      not get information of LcmOpOcc of VNF Instance B
    - User B belongs to Project B shows LcmOpOcc of VNF Instance B
    - User B belongs to Project B shows LcmOpOcc of VNF Instance A, and should
      not get information of LcmOpOcc of VNF Instance A
    - Verify that Notification Server A is able to get the Termination
      information for VNF Instance A
    - Verify that Notification Server B is unable to get the Termination
      information for VNF Instance A
    - Verify that Notification Server B is able to get the Termination
      information for VNF Instance B
    - Verify that Notification Server A is unable to get the Termination
      information for VNF Instance B

.. seqdiag::

    seqdiag {
        node_width = 80;
        edge_length = 100;

        "Test Class"
        "User A"
        "User B"
        "Tacker"
        "VNF A"
        "VNF B"
        "VnfLcmOpOccs A"
        "VnfLcmOpOccs B"
        "Notification Server A"
        "Notification Server B"

        "Test Class" -> "User A" [label = "Set User"];
        "Test Class" <- "User A";

        "Test Class" -> "User B" [label = "Set User"];
        "Test Class" <- "User B";

        "User A" -> "Tacker" [label = "Terminate VNF B"];
        "User A" <-- "Tacker" [label = "Failed to Terminate VNF B"];

        "User B" -> "Tacker" [label = "Terminate VNF A"];
        "User B" <-- "Tacker" [label = "Failed to Terminate VNF A"];

        "User A" -> "Tacker" [label = "Terminate VNF A"];
            "Tacker" -> "VNF A" [label = "Terminate VNF A"];
            "Tacker" <- "VNF A";
            "Tacker" -> "Notification Server A" [label = "send notification"];
            "Tacker" <- "Notification Server A";
        "User A" <-- "Tacker" [label = "Terminated VNF A"];

        "User B" -> "Tacker" [label = "Terminate VNF B"];
            "Tacker" -> "VNF B" [label = "Terminate VNF B"];
            "Tacker" <- "VNF B";
            "Tacker" -> "Notification Server B" [label = "send notification"];
            "Tacker" <- "Notification Server B";
        "User B" <-- "Tacker" [label = "Terminated VNF B"];

        "User A" -> "Tacker" [label = "Get VnfLcmOpOccs List of only VNF A"];
            "Tacker" -> "VnfLcmOpOccs A"
                [label = "Return list of VnfLcmOpOccs"];
            "Tacker" <- "VnfLcmOpOccs A";
        "User A" <-- "Tacker" [label = "Get list of VnfLcmOpOccs"];

        "User B" -> "Tacker" [label = "Get VnfLcmOpOccs List of only VNF B"];
            "Tacker" -> "VnfLcmOpOccs B"
                [label = "Return list of VnfLcmOpOccs"];
            "Tacker" <- "VnfLcmOpOccs B";
        "User B" <-- "Tacker" [label = "Get list of VnfLcmOpOccs"];

        "User A" -> "Tacker" [label = "Show VnfLcmOpOccs A"];
            "Tacker" -> "VnfLcmOpOccs A" [label = "Show VnfLcmOpOccs A"];
            "Tacker" <- "VnfLcmOpOccs A";
        "User A" <-- "Tacker" [label = "Showed VnfLcmOpOccs A"];

        "User A" -> "Tacker" [label = "Show VnfLcmOpOccs B"];
        "User A" <-- "Tacker" [label = "failed to show VnfLcmOpOccs B"];

        "User B" -> "Tacker" [label = "Show VnfLcmOpOccs B"];
            "Tacker" -> "VnfLcmOpOccs B" [label = "Show VnfLcmOpOccs B"];
            "Tacker" <- "VnfLcmOpOccs B";
        "User B" <-- "Tacker" [label = "Showed VnfLcmOpOccs B"];

        "User B" -> "Tacker" [label = "Show VnfLcmOpOccs A"];
        "User B" <-- "Tacker" [label = "failed to show VnfLcmOpOccs A"];

        "User A" -> "Notification Server A"
            [label = "Check the exist notification that Terminated VNF A"];
        "User A" <-- "Notification Server A"
            [label = "check existing notification that Terminated VNF A"];

        "User B" -> "Notification Server B"
            [label = "Check the not exist notification that Terminated VNF A"];
        "User B" <-- "Notification Server B"
            [label = "check not existing notification that Terminated VNF A"];

        "User B" -> "Notification Server B"
            [label = "Check the exist notification that Terminated VNF B"];
        "User B" <-- "Notification Server B"
            [label = "check existing notification that Terminated VNF B"];

        "User A" -> "Notification Server A"
            [label = "Check the not exist notification that Terminated VNF B"];
        "User A" <-- "Notification Server A"
            [label = "check not existing notification that Terminated VNF B"];

    }

- Delete VNF
    - User A belongs to Project A deletes VNF Instance B, and should fail
    - User B belongs to Project B deletes VNF Instance A, and should fail
    - User A belongs to Project A deletes VNF Instance A
    - User B belongs to Project B deletes VNF Instance B
    - Verify that Notification Server A is able to retrieve Delete
      information for VNF Instance A
    - Verify that Notification Server B is unable to get Delete
      information for VNF Instance A

.. seqdiag::

    seqdiag {
        node_width = 80;
        edge_length = 100;

        "Test Class"
        "User A"
        "User B"
        "Tacker"
        "VNF A"
        "VNF B"
        "Notification Server A"
        "Notification Server B"

        "Test Class" -> "User A" [label = "Set User"];
        "Test Class" <- "User A";

        "Test Class" -> "User B" [label = "Set User"];
        "Test Class" <- "User B";

        "User A" -> "Tacker" [label = "Delete VNF B"];
        "User A" <-- "Tacker" [label = "Failed to Delete VNF B"];

        "User B" -> "Tacker" [label = "Delete VNF A"];
        "User B" <-- "Tacker" [label = "Failed to Delete VNF A"];

        "User A" -> "Tacker" [label = "Delete VNF A"];
            "Tacker" -> "VNF A" [label = "Delete VNF A"];
            "Tacker" <- "VNF A";
            "Tacker" -> "Notification Server A" [label = "send notification"];
            "Tacker" <- "Notification Server A";
        "User A" <-- "Tacker" [label = "Deleted VNF A"];

        "User B" -> "Tacker" [label = "Delete VNF B"];
            "Tacker" -> "VNF B" [label = "Delete VNF B"];
            "Tacker" <- "VNF B";
            "Tacker" -> "Notification Server B" [label = "send notification"];
            "Tacker" <- "Notification Server B";
        "User B" <-- "Tacker" [label = "Deleted VNF B"];

        "User A" -> "Notification Server A"
            [label = "Check the exist notification that Deleted VNF A"];
        "User A" <-- "Notification Server A"
            [label = "check existing notification that Deleted VNF A"];

        "User B" -> "Notification Server B"
            [label = "Check the not exist notification that Deleted VNF A"];
        "User B" <-- "Notification Server B"
            [label = "check not existing notification that Deleted VNF A"];

        "User B" -> "Notification Server B"
            [label = "Check the exist notification that Deleted VNF B"];
        "User B" <-- "Notification Server B"
            [label = "check existing notification that Deleted VNF B"];

        "User A" -> "Notification Server A"
            [label = "Check the not exist notification that Deleted VNF B"];
        "User A" <-- "Notification Server A"
            [label = "check not existing notification that Deleted VNF B"];


    }

- Delete VNF Package
    - User A belongs to Project A deletes VNF Package B, and should fail
    - User B belongs to Project B deletes VNF Package A, and should fail
    - User A belongs to Project A deletes VNF Package A
    - User B belongs to Project B deletes VNF Package B

.. seqdiag::

    seqdiag {
        node_width = 80;
        edge_length = 100;

        "Test Class"
        "User A"
        "User B"
        "Tacker"
        "VNF Package A"
        "VNF Package B"

        "Test Class" -> "User A" [label = "Set User"];
        "Test Class" <- "User A";

        "Test Class" -> "User B" [label = "Set User"];
        "Test Class" <- "User B";

        "User A" -> "Tacker" [label = "Delete VNF Package B"];
        "User A" <-- "Tacker" [label = "Failed to delete VNF Package B"];

        "User B" -> "Tacker" [label = "Delete VNF Package A"];
        "User B" <-- "Tacker" [label = "Failed to delete VNF Package A"];

        "User A" -> "Tacker" [label = "Delete VNF Package A"];
            "Tacker" -> "VNF Package A" [label = "Delete VNF Package A"];
            "Tacker" <- "VNF Package A";
        "User A" <-- "Tacker" [label = "Deleted VNF Package A"];

        "User B" -> "Tacker" [label = "Delete VNF Package B"];
            "Tacker" -> "VNF Package B" [label = "Delete VNF Package B"];
            "Tacker" <- "VNF Package B";
        "User B" <-- "Tacker" [label = "Deleted VNF Package B"];

    }

- Delete Subscription
    - User A belongs to Project A deletes Subscription B, and should fail
    - User B belongs to Project B deletes Subscription A, and should fail
    - User A belongs to Project A deletes Subscription A
    - User B belongs to Project B deletes Subscription B

.. seqdiag::

    seqdiag {
        node_width = 80;
        edge_length = 100;

        "Test Class"
        "User A"
        "User B"
        "Tacker"
        "Subscription A"
        "Subscription B"

        "Test Class" -> "User A" [label = "Set User"];
        "Test Class" <- "User A";

        "Test Class" -> "User B" [label = "Set User"];
        "Test Class" <- "User B";

        "User A" -> "Tacker" [label = "Delete Subscription B"];
        "User A" <-- "Tacker" [label = "Failed to delete Subscription B"];

        "User B" -> "Tacker" [label = "Delete Subscription A"];
        "User B" <-- "Tacker" [label = "Failed to delete Subscription A"];


        "User A" -> "Tacker" [label = "Delete Subscription A"];
            "Tacker" -> "Subscription A" [label = "Delete Subscription A"];
            "Tacker" <- "Subscription A";
        "User A" <-- "Tacker" [label = "Deleted Subscription A"];

        "User B" -> "Tacker" [label = "Delete Subscription B"];
            "Tacker" -> "Subscription B" [label = "Delete Subscription B"];
            "Tacker" <- "Subscription B";
        "User B" <-- "Tacker" [label = "Deleted Subscription B"];

    }


Test perspective for proposed changes (3)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to verify the operation of proposed changes (3) in this Spec,
the following test cases are added.

- Filed to instantiate with different VIM
    - User A belongs to Project A registers VIM A for default VIM.
    - User B belongs to Project B registers VIM B for default VIM.
    - User A belongs to Project A create VNF Package A
    - User A belongs to Project A upload VNF Package A
    - User B belongs to Project B create VNF Package B
    - User B belongs to Project B upload VNF Package B
    - User A belongs to Project A uses VNF Package A to create VNF Instance A
    - User B belongs to Project B uses VNF Package B to create VNF Instance B
    - User A belongs to Project A instantiate VNF Instance A with VIM B, and should fail
    - User B belongs to Project B instantiate VNF Instance B with VIM A, and should fail
    - User A belongs to Project A instantiate VNF Instance A with VIM A
    - User B belongs to Project B instantiate VNF Instance B with VIM B
    - User A belongs to Project A terminate VNF Instance A
    - User B belongs to Project B terminate VNF Instance B
    - User A belongs to Project A deletes VNF Instance A
    - User B belongs to Project B deletes VNF Instance B

.. seqdiag::

    seqdiag {
        node_width = 80;
        edge_length = 100;

        "Test Class"
        "User A"
        "User B"
        "Tacker"
        "VIM A"
        "VIM B"
        "VNF A"
        "VNF B"

        "Test Class" -> "User A" [label = "Set User"];
        "Test Class" <- "User A";

        "Test Class" -> "User B" [label = "Set User"];
        "Test Class" <- "User B";

        "User A" -> "Tacker" [label = "Register VIM A"];
            "Tacker" -> "VIM A" [label = "Register VIM A"];
            "Tacker" <- "VIM A";
        "User A" <-- "Tacker" [label = "Registered VIM A"];

        "User B" -> "Tacker" [label = "Register VIM B"];
            "Tacker" -> "VIM B" [label = "Register VIM B"];
            "Tacker" <- "VIM B";
        "User A" <-- "Tacker" [label = "Registered VIM B"];

        "User A" -> "Tacker" [label = "Create VNF A"];
            "Tacker" -> "VNF A" [label = "Create VNF A"];
            "Tacker" <- "VNF A";
        "User A" <-- "Tacker" [label = "Created VNF A"];

        "User B" -> "Tacker" [label = "Create VNF B"];
            "Tacker" -> "VNF B" [label = "Create VNF B"];
            "Tacker" <- "VNF B";
        "User B" <-- "Tacker" [label = "Created VNF B"];

        "User A" -> "Tacker" [label = "Instantiate VNF A with VIM B"];
        "User A" <-- "Tacker" [label = "Failed to Instantiate VNF A"];

        "User B" -> "Tacker" [label = "Instantiate VNF B with VIM A"];
        "User B" <-- "Tacker" [label = "Failed to Instantiate VNF B"];

        "User A" -> "Tacker" [label = "Instantiate VNF A"];
            "Tacker" -> "VNF A" [label = "Instantiate VNF A"];
            "Tacker" <- "VNF A";
        "User A" <-- "Tacker" [label = "Instantiated VNF A"];

        "User B" -> "Tacker" [label = "Instantiate VNF B"];
            "Tacker" -> "VNF B" [label = "Instantiate VNF B"];
            "Tacker" <- "VNF B";
        "User B" <-- "Tacker" [label = "Instantiated VNF B"];

        "User A" -> "Tacker" [label = "Terminate VNF A"];
            "Tacker" -> "VNF A" [label = "Terminate VNF A"];
            "Tacker" <- "VNF A";
        "User A" <-- "Tacker" [label = "Terminated VNF A"];

        "User B" -> "Tacker" [label = "Terminate VNF B"];
            "Tacker" -> "VNF B" [label = "Terminate VNF B"];
            "Tacker" <- "VNF B";
        "User B" <-- "Tacker" [label = "Terminated VNF B"];

        "User A" -> "Tacker" [label = "Delete VNF A"];
            "Tacker" -> "VNF A" [label = "Delete VNF A"];
            "Tacker" <- "VNF A";
        "User A" <-- "Tacker" [label = "Deleted VNF A"];

        "User B" -> "Tacker" [label = "Delete VNF B"];
            "Tacker" -> "VNF B" [label = "Delete VNF B"];
            "Tacker" <- "VNF B";
        "User B" <-- "Tacker" [label = "Deleted VNF B"];

    }



Alternatives
------------

None

Data model impact
-----------------

Add to Tacker Database tables as below.

vnf_lcm_subscriptions:

.. code-block:: python

   tenant_id varchar(64)

vnf_lcm_op_occs:

.. code-block:: python

   tenant_id varchar(64)


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

None

Developer impact
----------------

None

Upgrade impact
--------------

None


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Koichi Edagawa <edagawa.kc@nec.com>


Work Items
----------

* Modify the tenant policy to prohibit associating a VIM with a VNF
  which belongs to the different tenant as the VIM.
* Modify Notification process to specify the tenant assigned during
  subscription sequence.
* Change notifying events so that Notification is sent to specified tenants
  only.

Dependencies
============

None


Testing
=======

Add a multi tenant functional testing case.
Details are provided in How to design Functional Testing.

Documentation Impact
====================

None

References
==========

None

History
=======

None
