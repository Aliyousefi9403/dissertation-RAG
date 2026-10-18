# Port Scanning


## Metadata


- Attack key: `port_scanning`
- Category: `reconnaissance`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-300`
- ATT&CK ID: `T1046`


## Attack description


An resister utilisation a combination of techniques to determine the state of the ports on a remote butt. Any service or application available for TCP or UDP networking will have a port open for communications over the web.

## Prerequisites


The antagonist requires logical access to the target's web in guild to carry out this type of onrush.

## Required resources


The opponent involve a network mapping/scanning tool, or must conduct socket programming on the bidding stock. bundle injection tools are also useful for this purpose. Depending upon the method used it may be necessary to sniff the network in order to see the response.

## Consequences


Access_Control: ['beltway security Mechanism', 'Hide Activities']; Authorization: ['beltway security Mechanism', 'Hide Activities']; Confidentiality: ['Other', 'Bypass aegis Mechanism', 'Hide Activities']

## ATT&CK adversary context


**Technique:** Network Service Discovery

Adversaries may attempt to get a listing of services running on remote hosts and local network infrastructure devices, including those that may be vulnerable to remote software exploitation. Common methods to acquire this information include port, vulnerability, and/or wordlist scans using tools that are brought onto a system.(Citation: CISA AR21-126A FIVEHANDS May 2021)   

Within cloud environments, adversaries may attempt to discover services running on other cloud hosts. Additionally, if the cloud environment is connected to a on-premises environment, adversaries may be able to identify services running on non-cloud systems as well.

Within macOS environments, adversaries may use the native Bonjour application to discover services running on other macOS hosts within a network. The Bonjour mDNSResponder daemon automatically registers and advertises a host’s registered services on the network. For example, adversaries can use a mDNS query (such as <code>dns-sd -B _ssh._tcp .</code>) to find other systems broadcasting the ssh service.(Citation: apple doco bonjour description)(Citation: macOS APT Activity Bradley)


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


- CAPEC: CAPEC-300 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1046 — role: network_service_scanning_context; required
- CAPEC: CAPEC-287 — role: tcp_syn_scan_context; optional
- CAPEC: CAPEC-308 — role: udp_scan_context; optional


## Provenance


- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
