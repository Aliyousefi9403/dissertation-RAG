# Sniff Application Code

## Metadata

- Attack key: `sniff_application_code`
- Category: `communications`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-65`
- ATT&CK ID: `T1040`

## Attack description

An adversary passively sniffs network communications and captures application code bound for an authorized client. Once obtained, they can use it as-is, or through reverse-engineering glean sensitive information or exploit the trust relationship between the client and server. Such code may belong to a dynamic update to the client, a patch being applied to a client component or any such interaction where the client is authorized to communicate with the server.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Set up a sniffer: </b>The adversary sets up a sniffer in the path between the server and the client and watches the traffic.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>The adversary sets up a sniffer in the path between the server and the client.</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p>[Capturing Application Code Bound During Patching]adversary knows that the computer/OS/application can request new applications to install, or it periodically checks for an available update. The adversary loads the sniffer set up during Explore phase, and extracts the application code from subsequent communication. The adversary then proceeds to reverse engineer the captured code.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>adversary loads the sniffer to capture the application code bound during a dynamic update.</td></tr><tr><td>The adversary proceeds to reverse engineer the captured code.</td></tr></tbody></table></ol></div>

## Prerequisites

- The attacker must have the ability to place themself in the communication path between the client and server.
- The targeted application must receive some application code from the server; for example, dynamic updates, patches, applets or scripts.
- The attacker must be able to employ a sniffer on the network without being detected.

## Required resources

<xhtml:p>The Attacker needs the ability to capture communications between the client being updated and the server providing the update.</xhtml:p>
               <xhtml:p>In the case that encryption obscures client/server communication the attacker will either need to lift key material from the client.</xhtml:p>

## Required skills

Medium: The attacker needs to setup a sniffer for a sufficient period of time so as to capture meaningful quantities of code. The presence of the sniffer should not be detected on the network. Also if the attacker plans to employ an adversary-in-the-middle attack (CAPEC-94), the client or server must not realize this. Finally, the attacker needs to regenerate source code from binary code if the need be.

## Consequences

Access_Control: ['Gain Privileges']; Authorization: ['Gain Privileges']; Confidentiality: ['Read Data', 'Gain Privileges']

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

- CAPEC: CAPEC-65 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1040 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
