This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode


==============================================================
Zabbix Plugin for Application Monitoring in Tacker VNF Manager
==============================================================

The URL of the launchpad blueprint:

https://blueprints.launchpad.net/tacker/+spec/zabbix-plugin

Develop a Zabbix plugin in Tacker VNF manager to monitor application level
parameters that can't be supported by current Tacker monitoring driver.

Problem description
===================

Current Tacker monitoring drivers provide simple monitoring capabilities, such
as Ceilometer just supports hardware infrastructure resource-related parameters
(e.g. CPU or memory usage). Ping and http_ping drivers also support basic
checking for aliveness of VNFs. In order to guarantee the availability and
stability of network services provided by VNFs, another advanced monitoring tool
which supports application-level parameters is required into VNF Tacker manager.

Zabbix is the most well-known monitoring tool that monitors and tracks numerous
types of network services, applications, resources and servers to quickly
notify administrators of failures. Zabbix provides easy-to-view, simple Web
pages and agents.

The monitoring targets provided by Zabbix are as follows.

* cpu memory / performance
* os performance
* process load / number
* swap / memory space
* FTP, HTTP, MySQL, NTP, POP, SSH, Telnet, SMTP, etc application status
* customize monitoring

Monitoring provided by Zabbix provides not only the operating system in vnf,
but also the status, memory occupancy, cpu, etc. in relation to
the application. The templates you need for monitoring can use many more
functions through the Zabbix community.

It also provides APIs to provide accurate and versatile monitoring capabilities
for each VDU. It collects data through agents, provides
visual monitoring such as graphs and maps and provides triggers and alarms
according to the collected data conditions to promptly notify when a user-defined
threshold value is exceeded. Depending on these triggers, user-defined commands
can be performed to quickly recover from the failure. User-defined commands can
be executed through the agent in the VDU.

The VNF monitoring that tacker can provide by using this is as follows.

* Application monitoring
* Resources, network monitoring in VNF
* Fault management and recovery within applications in VNFs
* Perform predefined commands
* Collected data can be graphically displayed
* Custom trigger conditions can be set


Proposed changes
================

Template Policy, Service Monitoring Driver and Zabbix Plugin are required for
interoperation with Zabbix. In Tacker, the IP address, name, etc. for the VDU
must be transmitted to the Zabbix server using the API request. Also, it is
necessary to transmit a request for generating Template, Item, Trigger, Graph,
etc. for monitoring to the server through the API. In addition, Service
Monitoring Policy should be defined in Tosca-Template to allow user to define
condition value for trigger notification about monitored application, CPU load,
and status.

Zabbix can collect data (CPU, RAM, disk, network usage) from VNFs using agents
that are installed in each single VM. Through Zabbix APIs, we monitor and get all
information from Zabbix dashboard such as Graphs.

In Tacker VNF descriptor, user defines Zabbix agents via user-data, user also
defines policies and resources for Zabbix such as thresholds, which metrics will
be monitored, etc.

Tacker collects the status of VDU. If VDU responds to Respwan action in policy
or an additional VDU need to be created for scalability, information about
additional VDU is registered as a new monitoring host by requesting Zabbix
server for IP information of new VDU through Zabbix plugin. Should be in the
opposite case, request the delete API for the existing VDU Host registered in
Zabbix Server.

The overall workflow is as follows::

 +----------------------------+                      +----------------------------+
 |                            |                      |                            |
 |        Zabbix Web UI       |                      | Tosca_zabbix_template.yaml |
 |                            |                      |                            |
 +----------------------------+                      +--------------+-------------+
                                                                    |
                                                                    |
 +----------------------------+               +---------------------v-------------------------+
 |           Zabbix           |               |                    Tacker                     |
 |                            |               |                                               |
 |    +------------------+    |               | +-----------------------------------------+   |
 |    |                  |    |               | |                   VNFM                  |   |
 |    |  Zabbix Frontend |    |               | |                                         |   |
 |    |                  |    |               | |  +---------------+   +---------------+  |   |
 |    +------------------+    |               | |  |               |   |   Service     |  |   |
 |                            |               | |  | Zabbix Plugin |   |   Monitoring  |  |   |
 |    +------------------+    |         +----------+               <---+   Driver      |  |   |
 |    |                  |    |         |     | |  |               |   |               |  |   |
 |    |  Zabbix Server   | <------------+     | |  +---------------+   +---------------+  |   |
 |    |                  |    |               | |                                         |   |
 |    +------+-^----+---^+----+               | +-----------------------------------------+   |
 |           | |    |   |     |               +-----------------------------------------------+
 +----------------------------+
             | |    |   +-------------------------------------------------------+
             | |    |                                                           |
             | |    +-----------------------------------+                       |
             | +-------------------+                    |                       |
             |                     |                    |                       |
             |                     |                    |                       |
 +------------------------------------------------------------------------------------------+
 |           |                     |            NFVI    |                       |           |
 | +--------------------------------------------------------------------------------------+ |
 | |         |                     |            VNF     |                       |         | |
 | | +---------------------------------------+  +---------------------------------------+ | |
 | | |       |        VDU          |         |  |       |            VDU        |       | | |
 | | | +-----v---------------------+-------+ |  | +-----v-----------------------+-----+ | | |
 | | | |            Zabbix Agent           | |  | |           Zabbix Agent            | | | |
 | | | +---------+--------------+----------+ |  | +---------+--------------+----------+ | | |
 | | |           |              |            |  |           |              |            | | |
 | | |          +v--------------v+           |  |          +v--------------v+           | | |
 | | |          |     Scripts    |           |  |          |     Scripts    |           | | |
 | | |          +----+---------^-+           |  |          +----+---------^-+           | | |
 | | |               |         |             |  |               |         |             | | |
 | | |      |--------v---------+------+      |  |      |--------v---------+------+      | | |
 | | |      | Application  Or OS Info |      |  |      | Application  Or OS Info |      | | |
 | | |      |          Or             |      |  |      |          Or             |      | | |
 | | |      |       User Define       |      |  |      |       User Define       |      | | |
 | | |      +-------------------------+      |  |      +-------------------------+      | | |
 | | +---------------------------------------+  +---------------------------------------+ | |
 | +--------------------------------------------------------------------------------------+ |
 +------------------------------------------------------------------------------------------+

The Zabbix server requests the Zabbix agent built in each VDU to monitor the item
to be collected, and the Zabbix agent executes the monitoring script for the
embedded item. The collected data is sent to the Zabbix server by the Zabbix
Agent, which determines whether the trigger is generated. Triggers can be
generated according to the average value of collected data and so on.

Tacker VNFM requires Zabbix Server with Service Monitoring Driver and Zabbix
Plugin for API request. This allows VDU to be monitored. The Service Monitoring
Driver extracts the service monitoring policy from the Tosca template and makes
it into a dictionary and delivers it to the Zabbix Plugin. The Zabbix Plugin
first sends a token request API to the Zabbix Server to receive the token.

Zabbix Plugin requests Zabbix Server host creation API including IP address to
register generated VDU as monitoring host. It then requests a generation API
with trigger value and application information to perform monitoring for each
VDU. All of these processes require tokens. Below is an example of a service
monitoring policy.

.. code-block:: yaml

        app_monitoring_policy:
          name: zabbix
          zabbix_username: Admin
          zabbix_password: zabbix
          zabbix_server_ip: 192.168.11.53
          zabbix_server_port: 80
          parameters:
            application:
              appname: apache2
              appport: 80
              app_status:
                condition: [down]
                actioname: cmd
                cmd-action: service apache2 restart
              app_memory:
                condition: [greater,22]
                actioname: cmd
                cmd-action: service apache2 stop
            OS:
              os_agent_info:
                condition: [down]
                actioname: cmd
                cmd-action: service zabbix-agent restart
              os_cpu_usage:
              os_proc_value:
                condition: [and less,30]
                actioname: cmd
                cmd-action: reboot
              os_cpu_load:
                condition: [greater,30]
                actioname: cmd
                cmd-action: reboot

We can enter the ID / PASSWORD / IP / PORT of the Zabbix server in the Template and use this
information to access the zabbix server (e.g. token) to perform monitoring actions.

* zabbix_username & zabbix_password & zabbix_server_ip & zabbix_server_port : The information
  needed for authentication from Zabbix, the ID and Password of the zabbix user, and the IP and Port
  number of the Zabbix server respectively.

Zabbix monitors the inside of the VNFs managed by the Tacker. From the point of
view of Zabbix, VNFs are the physical servers we are operating.

Therefore, it monitors CPU / Memory and application for VNF internal operating
system,and notifies and repairs the occurrence of a failure. All of this can be
verified through VNF internal monitoring via Zabbix web. Tacker can run stable
VNF through Zabbix.

These service monitoring policies should be set individually for each VDU. This
is because the range and monitoring application that each VDU wants to monitor
may be different. The parameters are divided into application and VNF internal
OS monitoring.

* name : The name of the open source monitoring tool.

* application & OS: Information about application and VNF OS-related monitoring.

* appname & appport : Specify monitored application and port information.

* app_status & app_memory: It shows the state of the application and the
  application memory in bytes.

* os_cpu_usage & os_proc_value & os_cpu_load : cpu Indicates the I / O
  throughput, usage, and the number of processes running.

* os_agent_info : os_agent_info can check status of zabbix agent.

Enter a number of authentication information about the zabbix server and call it from
the zabbix plugin to communicate with the Zabbix Server. As a result, the tacker can
make various monitoring requests to the Zabbix Server.It is efficient from a security
point of view.

Each monitoring item can define detailed comparison values and corresponding actions.
This notifies you when a problem with an item occurs and defines additional actions
accordingly. You can increase the stability of VNF application operations by performing
actions defined in the event of a failure.

The details that can be set for each monitoring target are as follows.

* condition: [comparison, value ]

The condition consists of comparison and value. Comparisons include greater, less,
and greater, and less, and zabbix determines whether a failure occurs for the item
based on a comparison with the baseline value.

* actioname: [action name]
* cmd-action: [Command to be executed in VNF]

The current action supports cmd, and a respawn, scale action will be added in the future.
If the condition specified in condition is true, the cmd-action is performed within the VNF.

Allows you to perform an action in response to a failure. The actions provided by Zabbix
include remote commands, script execution, and so on. These commands can be set to run
through Zabbix-agent or via Zabbix-server. Use script execution provided by zabbix to do cmd.

If you choose cmd,you must define cmd-action. This is the cmd - action command to be executed
through zabbix-agent in vnf. In conclusion, the execution of each cmd is as follows.

* cmd: The zabbix server automatically performs actions according to the user cmd-action through
  the zabbix agent in vnf.

VDU can install Zabbix Agent on the image itself, or create an automatic
monitoring environment through scripting in user data session of Tosca Template.
An example script used in user data is shown below.

.. code-block:: console

        user_data: |
            #!/bin/bash
            sudo apt-get -y update
            sudo apt-get -y upgrade
            sudo apt-get -y install zabbix-agent
            sudo apt-get -y install apache2

            sudo sed -i "2s/.*/`ifconfig [Interface name in VNF] | grep ""\"inet addr:\"""| cut -d: -f2 | awk ""\"{ print $1 }\"""`/g" "/etc/hosts"
            sudo sed -i "s/Bcast/`cat /etc/hostname`/g" "/etc/hosts"
            sudo sed -i "3s/.*/[Zabbix server's IP Address]\tmonitor/g" "/etc/hosts"
            sudo /etc/init.d/networking restart
            sudo echo 'zabbix ALL=NOPASSWD: ALL' >> /etc/sudoers

            sudo sed -i "s/# EnableRemoteCommands=0/EnableRemoteCommands=1/" "/etc/zabbix/zabbix_agentd.conf"
            sudo sed -i "s/Server=127.0.0.1/Server=[Zabbix server's IP Address]/" "/etc/zabbix/zabbix_agentd.conf"
            sudo sed -i "s/ServerActive=127.0.0.1/ServerActive=[Zabbix server's IP Address:Port]/" "/etc/zabbix/zabbix_agentd.conf"
            sudo sed -i "s/Hostname=Zabbix server/Hostname=`cat /etc/hostname`/" "/etc/zabbix/zabbix_agentd.conf"

            sudo service apache2 restart
            sudo service zabbix-agent restart

Install Zabbix-agent with apt-get. Also, after installing zabbix-agent, replace
the configuration file with sed command. This process is performed during the
VDU initialization process.

As a result of this process, Zabbix provides a stable monitoring function that
allows the Tacker to set the monitoring range and targets for each VDU in
detail, and to provide more stable support for the applications provided by the
VDU.

If an application monitoring policy and a current monitoring policy are used at
the same time, respawn or scale action occurs according to the current monitoring policy,
the existing respawn or scale action proceeds as it is. However, when these actions occur,
the application monitoring policy does not work. In the scope of the current proposal, the
user must select either the current monitoring policy or the application monitoring policy.
It can be resolved if the repawn, scale action is added at the level of the application
monitoring that is separate from the current monitoring policy.

Alternatives
------------
Open source monitoring tool providing API(e.g. nagios)


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

Implementation
==============

Assignee(s)
-----------

Primary author and contact.

  MinWookKim <delightwook@dcn.ssu.ac.kr>

Primary assignee:

  MinWookKim <delightwook@dcn.ssu.ac.kr>

Work Items
----------
1. Zabbix-plugin in monitoring_driver
2. Plugin in VNFM for called Zabbix-plugin
3. Additional features in the alarm-receiver for receiving alarms from the Zabbix server
4. Definition of server IP address, Port, Id, Password for requesting Zabbix server from
   Zabbix-plugin in tacker.conf
5. Extract app_monitoring_policy defined in template from utils, translate_template

Dependencies
============
* Zabbix-Server Installation
* Zabbix-Agent Installation

Testing
=======
* Add function test for vnf service monitoring
* Performance test for vnf failure recovery and detection in Zabbix
* Service monitoring policy based on the overall workflow test

Documentation Impact
====================
None

References
==========
.. [#first] https://www.zabbix.com/documentation/3.0/manual
.. [#second] https://share.zabbix.com/
.. [#third] https://www.nagios.org/documentation/