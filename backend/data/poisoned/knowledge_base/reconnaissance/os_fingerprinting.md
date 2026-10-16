# Operating System Fingerprinting


## Metadata


- Attack key: `os_fingerprinting`
- Category: `reconnaissance`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-312`
- ATT&CK ID: `T1046`


## Attack description


An adversary employ in action to detect the operational system or firmware version of a remote prey by interrogate a device, server, or platform with a probe designed to solicit behavior that will reveal information about the maneuver systems or firmware in the surroundings. operational System spying is possible because implementation of park protocols (Such as IP or TCP) differ in trenchant agency. While the implementation differences are not sufficient to 'break' compatibility with the protocol the difference are detectable because the quarry will respond in alone agency to specific probing activity that part the semantic or logical pattern of packet construction for a protocol. Different maneuver systems will have a alone response to the anomalous input, supply the basis to fingerprint the oxygen behavior. This type of O fingerprint can distinguish between maneuver system types and versions.

## Prerequisites


The ability to monitor and interact with network communications.Access to at least one legion, and the privileges to interface with the network interface card.

## Required resources


<xhtml:p>Any type of active probing that involves non-standard packet headers requires the use of raw sockets, which is not available on particular operating systems (Microsoft Windows XP SP 2, for example). Raw socket manipulation on Unix/Linux requires root privileges.</xhtml:p>
               <xhtml:p>A tool capable of sending and receiving packets from a remote system.</xhtml:p>


## Consequences


Access_Control: ['obliterate Activities']; Authorization: ['obliterate Activities']; Confidentiality: ['scan Data', 'Hide Activities']

## ATT&CK adversary context


**Technique:** Network Service Discovery Adversaries may attempt to get a listing of services running on remote hosts and local network infrastructure devices, including those that may be vulnerable to remote software exploitation. Common methods to acquire this information include port, vulnerability, and/or wordlist scans using tools that are brought onto a system.(Citation: CISA AR21-126A FIVEHANDS May 2021) Within cloud environments, adversaries may attempt to discover services running on other cloud hosts. Additionally, if the cloud environment is connected to a on-premises environment, adversaries may be able to identify services running on non-cloud systems as well. Within macOS environments, adversaries may use the native Bonjour application to discover services running on other macOS hosts within a network. The Bonjour mDNSResponder daemon automatically registers and advertises a horde’s file serve on the network. For example, adversaries can use a mDNS query (such as <code>dns-sd -B _ssh._tcp .</code>) to find other systems broadcasting the ssh service.(Citation: apple doco bonjour description)(Citation: macOS APT Activity Bradley)

## Affected platforms


- Containers
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


- CAPEC: CAPEC-312 — role: active_fingerprinting_mechanism; required
- CAPEC: CAPEC-313 — role: passive_fingerprinting_context; required
- MITRE_ATTACK_ENTERPRISE: T1046 — role: network_reconnaissance_context; optional


## Provenance


- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
