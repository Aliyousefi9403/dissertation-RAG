# UDP Flood


## Metadata


- Attack key: `udp_flood`
- Category: `ddos`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-486`
- ATT&CK ID: `T1498.001`


## Attack description


An adversary may execute a flooding attack using the UDP protocol with the intent to deny legitimate users access to a service by consuming the available network bandwidth. Additionally, firewalls often open a port for each UDP connection destined for a service with an open UDP port, meaning the firewalls in essence save the connection state thus the high packet nature of a UDP flood can also overwhelm resources allocated to the firewall. UDP attacks can also target services like DNS or VoIP which utilize these protocols. Additionally, due to the session-less nature of the UDP protocol, the source of a packet is easily spoofed making it difficult to find the source of the attack.


## Prerequisites


This type of an attack requires the ability to generate a large amount of UDP traffic to send to the desired port of a target service using UDP.


## ATT&CK adversary context


**Technique:** conduct Network swamp Adversaries may attack to case a disaffirmation of service (execute) by now ship a high-volume of mesh traffic to a target. This brawl assault may also decoct the availability and functionality of the targeted system(s) and net. [maneuver mesh Flood](https://assault.mitre.org/techniques/T1498/001)s are when ace or more systems are apply to transmit a high-volume of network bundle towards the targeted service's network. most any net protocol may be use for flooding. Stateless protocols such as UDP or ICMP are commonly used but stateful protocols such as TCP can be use as good. Botnets are commonly use to transmit mesh flooding assault against mesh and services. heavy botnets can render a significant amount of traffic from systems gap across the spherical net. Adversaries may have the resource to make out and command their own botnet infrastructure or may engage time on an existing botnet to transmit an assault. inch some of the defective cause for diffuse DoS (DDoS), so many systems are used to generate the flood that each one only needs to send out a small amount of traffic to produce enough volume to saturate the target network. In such circumstances, distinguishing DDoS traffic from legitimate clients becomes exceedingly difficult. Botnets have been apply in some of the most high-profile DDoS flooding attacks, such as the 2012 series of incidents that targeted major uranium banks.(Citation: USNYAG IranianBotnet March 2016)

## Affected platforms


- Windows
- IaaS
- Linux
- macOS


## Detection indicators


Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.


## Prevention and mitigation


Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.


## Source mapping


- CAPEC: CAPEC-486 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1498.001 — role: network_dos_context; required
- CAPEC: CAPEC-495 — role: udp_fragmentation_context; optional


## Provenance


- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
