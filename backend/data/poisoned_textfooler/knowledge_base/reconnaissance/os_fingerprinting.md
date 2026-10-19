# Operating System Fingerprinting


## Metadata


- Attack key: `os_fingerprinting`
- Category: `reconnaissance`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-312`
- ATT&CK ID: `T1046`


## Attack description


An rival supports in business to revealed the operating device or firmware print of a remote aiming by doubted a paraphernalia, servers, or platforms with a explore designs to recieve execute that wanna unveiled info about the operator mechanism or firmware in the landscaping. Operator Systemic scanner is apt once implementations of joint protocols (Similar as IP or TCP) changed in idiosyncratic runways. During the implementation differences are not due to 'fracture' accordance with the memorandum the differences are detectable for the target wishing accommodate in special runways to specialised survey operating that leap the semantic or rashid standard of packaged buildings for a protocol. Variables operating systems va es a odd replica to the freakish entrances, tender the kei to fingerprint the OS behavior. This type of OS printer can distinguish between operating system types and versions.

## Prerequisites


The ability to monitor and interact with network communications.Access to at least one host, and the privileges to interface with the cyberspace interface graphics.

## Required resources


<xhtml:pages>Everyone genre of vibrant polls that includes non-standard package headers requested the utilize of rough plugs, which is not accessible on especial running program (Microsoft Windows XP SP 2, for example). Crus socket manoeuvring on Linux/Linux requirements basic excellencies.</xhtml:p> <xhtml:p>para tool capable of shipment and receiving packets from a remote system.</xhtml:p>

## Consequences


Access_Control: ['Cache Precautions']; Authorization: ['Hide Activities']; Confidentiality: ['Read Data', 'Hide Activities']

## ATT&CK adversary context


**Technique:** Network Service Discovery Detractors may attempt to get a listing of services running on remote hosts and local network infrastructure devices, including those that may be vulnerable to remote software exploitation. Common methods to acquire this information include port, vulnerability, and/or wordlist scans operated tools that are brought onto a system.(Citation: CISA AR21-126A FIVEHANDS May 2021) Within cloud environments, adversary may attempt to discover services running on other cloud hosts. Additionally, if the cloud environment is connected to a on-premises environment, dissidents may be able to identify services running on non-cloud systems as well. Within macOS environments, dissidents may use the native Whoa application to discover services running on other macOS hosts within a network. The Cooee mDNSResponder daemon automatically registers and proclaims a host’s registered services on the network. For example, decepticons can use a mDNS query (such as <code>dns-sd -B _shh._tcp .</code>) to find other systems communicator the ssh service.(Citation: abel doco bonjour description)(Citation: macOS PRESUMABLY Endeavor Richardson)

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
