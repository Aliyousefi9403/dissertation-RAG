# ARP Spoofing

## Metadata

- Attack key: `arp_spoofing`
- Category: `spoofing`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-141`
- ATT&CK ID: `T1557.002`

## Attack description

An attacker exploits the functionality of cache technologies to cause specific data to be cached that aids the attackers' objectives. This describes any attack whereby an attacker places incorrect or harmful material in cache. The targeted cache can be an application's cache (e.g. a web browser cache) or a public cache (e.g. a DNS or ARP cache). Until the cache is refreshed, most applications or clients will treat the corrupted cache value as valid. This can lead to a wide range of exploits including redirecting web browsers towards sites that install malware and repeatedly incorrect calculations based on the incorrect value.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Identify and explore caches: </b>Use tools to sniff traffic and scan a network in order to locate application's cache (e.g. a web browser cache) or a public cache (e.g. a DNS or ARP cache) that may have vulnerabilities. Look for poisoning point in cache table entries.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Run tools that check available entries in the cache.</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Cause specific data to be cached: </b>An attacker sends bogus request to the target, and then floods responses that trick a cache to remember malicious responses, which are wrong answers of queries.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Intercept or modify a query, or send a bogus query with known credentials (such as transaction ID).</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Redirect users to malicious website: </b>As the attacker succeeds in exploiting the vulnerability, they are able to manipulate and interpose malicious response data to targeted victim queries.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Intercept or modify a query, or send a bogus query with known credentials (such as transaction ID).</td></tr><tr><td>Adversary-in-the-Middle attacks (CAPEC-94) intercept secure communication between two parties.</td></tr></tbody></table></ol></div>

## Prerequisites

- The attacker must be able to modify the value stored in a cache to match a desired value.
- The targeted application must not be able to detect the illicit modification of the cache and must trust the cache value in its calculations.

## Required skills

Medium: To overwrite/modify targeted cache

## ATT&CK adversary context

**Technique:** ARP Cache Poisoning

Adversaries may poison Address Resolution Protocol (ARP) caches to position themselves between the communication of two or more networked devices. This activity may be used to enable follow-on behaviors such as [Network Sniffing](https://attack.mitre.org/techniques/T1040) or [Transmitted Data Manipulation](https://attack.mitre.org/techniques/T1565/002).

The ARP protocol is used to resolve IPv4 addresses to link layer addresses, such as a media access control (MAC) address.(Citation: RFC826 ARP) Devices in a local network segment communicate with each other by using link layer addresses. If a networked device does not have the link layer address of a particular networked device, it may send out a broadcast ARP request to the local network to translate the IP address to a MAC address. The device with the associated IP address directly replies with its MAC address. The networked device that made the ARP request will then use as well as store that information in its ARP cache.

An adversary may passively wait for an ARP request to poison the ARP cache of the requesting device. The adversary may reply with their MAC address, thus deceiving the victim by making them believe that they are communicating with the intended networked device. For the adversary to poison the ARP cache, their reply must be faster than the one made by the legitimate IP address owner. Adversaries may also send a gratuitous ARP reply that maliciously announces the ownership of a particular IP address to all the devices in the local network segment.

The ARP protocol is stateless and does not require authentication. Therefore, devices may wrongly add or update the MAC address of the IP address in their ARP cache.(Citation: Sans ARP Spoofing Aug 2003)(Citation: Cylance Cleaver)

Adversaries may use ARP cache poisoning as a means to intercept network traffic. This activity may be used to collect and/or relay data such as credentials, especially those sent over an insecure, unencrypted protocol.(Citation: Sans ARP Spoofing Aug 2003)


## Affected platforms

- Linux
- Windows
- macOS

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- MITRE_ATTACK_ENTERPRISE: T1557.002 — role: attack_mechanism; required
- CAPEC: CAPEC-141 — role: cache_poisoning_context; optional
- MITRE_ATTACK_ICS: T0830 — role: ics_man_in_the_middle_context; optional

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
