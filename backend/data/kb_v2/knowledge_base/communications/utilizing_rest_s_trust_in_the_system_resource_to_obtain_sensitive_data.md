# Utilizing REST's Trust in the System Resource to Obtain Sensitive Data

## Metadata

- Attack key: `utilizing_rest_s_trust_in_the_system_resource_to_obtain_sensitive_data`
- Category: `communications`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-57`
- ATT&CK ID: `T1040`

## Attack description

This attack utilizes a REST(REpresentational State Transfer)-style applications' trust in the system resources and environment to obtain sensitive data once SSL is terminated.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Find a REST-style application that uses SSL: </b>The adversary must first find a REST-style application that uses SSL to target. Because this attack is easier to carry out from inside of a server network, it is likely that an adversary could have inside knowledge of how services operate.</p></li></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Insert a listener to sniff client-server communication: </b>The adversary inserts a listener that must exist beyond the point where SSL is terminated. This can be placed on the client side if it is believed that sensitive information is being sent to the client as a response, although most often the listener will be placed on the server side to listen for client authentication information.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Run wireshark or tcpdump on a device that is on the inside of a firewall, load balancer, or router of a network and capture traffic after SSL has been terminated</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Gather information passed in the clear: </b>If developers have not hashed or encrypted data sent in the sniffed request, the adversary will be able to read this data in the clear. Most commonly, they will now have a username or password that they can use to submit requests to the web service just as an authorized user</p></li></ol></div>

## Prerequisites

- Opportunity to intercept must exist beyond the point where SSL is terminated.
- The adversary must be able to insert a listener actively (proxying the communication) or passively (sniffing the communication) in the client-server communication path.

## Required skills

Low: To insert a network sniffer or other listener into the communication stream

## Consequences

Access_Control: ['Gain Privileges']; Authorization: ['Gain Privileges']; Confidentiality: ['Gain Privileges']

## ATT&CK adversary context

**Technique:** Network Sniffing

Adversaries may passively sniff network traffic to capture information about an environment, including authentication material passed over the network. Network sniffing refers to using the network interface on a system to monitor or capture information sent over a wired or wireless connection. An adversary may place a network interface into promiscuous mode to passively access data in transit over the network, or use span ports to capture a larger amount of data.

Data captured via this technique may include user credentials, especially those sent over an insecure, unencrypted protocol. Techniques for name service resolution poisoning, such as [Name Resolution Poisoning and SMB Relay](https://attack.mitre.org/techniques/T1557/001), can also be used to capture credentials to websites, proxies, and internal systems by redirecting traffic to an adversary.

Network sniffing may reveal configuration details, such as running services, version numbers, and other network characteristics (e.g. IP addresses, hostnames, VLAN IDs) necessary for subsequent [Lateral Movement](https://attack.mitre.org/tactics/TA0008) and/or [Stealth](https://attack.mitre.org/tactics/TA0005) activities. Adversaries may likely also utilize network sniffing during [Adversary-in-the-Middle](https://attack.mitre.org/techniques/T1557) (AiTM) to passively gain additional knowledge about the environment.

In cloud-based environments, adversaries may still be able to use traffic mirroring services to sniff network traffic from virtual machines. For example, AWS Traffic Mirroring, GCP Packet Mirroring, and Azure vTap allow users to define specified instances to collect traffic from and specified targets to send collected traffic to.(Citation: AWS Traffic Mirroring)(Citation: GCP Packet Mirroring)(Citation: Azure Virtual Network TAP) Often, much of this traffic will be in cleartext due to the use of TLS termination at the load balancer level to reduce the strain of encrypting and decrypting traffic.(Citation: Rhino Security Labs AWS VPC Traffic Mirroring)(Citation: SpecterOps AWS Traffic Mirroring) The adversary can then use exfiltration techniques such as Transfer Data to Cloud Account in order to access the sniffed traffic.(Citation: Rhino Security Labs AWS VPC Traffic Mirroring)

On network devices, adversaries may perform network captures using [Network Device CLI](https://attack.mitre.org/techniques/T1059/008) commands such as `monitor capture`.(Citation: US-CERT-TA18-106A)(Citation: capture_embedded_packet_on_software)

## Affected platforms

- IaaS
- Linux
- macOS
- Network Devices
- Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-57 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1040 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
