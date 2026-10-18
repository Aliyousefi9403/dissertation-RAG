# Operating System Fingerprinting


## Metadata


- Attack key: `os_fingerprinting`
- Category: `reconnaissance`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-312`
- ATT&CK ID: `T1046`


## Attack description


An adversary mesh in activity to observe the run system or firmware version of a remote object by question a device, server, or platform with a examine designed to woo demeanor that will disclose data about the run systems or firmware in the environment. maneuver arrangement spying is possible because implementations of commons protocols (Such as IP or TCP) differ in distinct style. spell the implementation conflict are not sufficient to 'founder' compatibility with the protocol the differences are noticeable because the quarry will react in unique style to specific searching activity that wear the semantic or logical pattern of package building for a protocol. Different run systems will have a alone reception to the anomalous remark, furnish the cornerstone to fingermark the osmium demeanor. This typecast of O fingerprint can key between run system typecast and rendering.

## Prerequisites


The ability to monitor and interact with network communications.Access to at least one host, and the privileges to interface with the web interface card.

## Required resources


<xhtml:p>Any type of active probing that involves non-standard packet headers requires the use of raw sockets, which is not available on particular operating systems (Microsoft Windows XP SP 2, for example). Raw socket manipulation on Unix/Linux requires root privileges.</xhtml:p>
               <xhtml:p>A tool capable of sending and receiving packets from a remote system.</xhtml:p>


## Consequences


Access_Control: ['obliterate activeness']; Authorization: ['Hide Activities']; Confidentiality: ['scan Data', 'obliterate Activities']

## ATT&CK adversary context


**Technique:** Network Service Discovery Adversaries may attempt to get a listing of services running on remote hosts and local network infrastructure devices, including those that may be vulnerable to remote software exploitation. Common methods to acquire this information include port, vulnerability, and/or wordlist scan exploitation tools that are brought onto a system.(Citation: CISA AR21-126A FIVEHANDS May 2021) Within cloud environments, adversary may attempt to discover services running on other cloud hosts. Additionally, if the cloud environment is connected to a on-premises environment, adversaries may be able to identify services lean on non-cloud systems as well. Within macOS environments, adversaries may use the native Bonjour application to discover services running on other macOS hosts within a network. The Bonjour mDNSResponder daemon automatically registers and push a host’s registered services on the network. For example, resister can use a mDNS query (such as <code>dns-sd -B _ssh._tcp .</cipher>) to find other systems disseminate the ssh service.(Citation: apple doco bonjour description)(Citation: macOS APT Activity Bradley)

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
