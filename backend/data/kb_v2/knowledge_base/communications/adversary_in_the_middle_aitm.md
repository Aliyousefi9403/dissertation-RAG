# Adversary in the Middle (AiTM)

## Metadata

- Attack key: `adversary_in_the_middle_aitm`
- Category: `communications`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-94`
- ATT&CK ID: `T1557`

## Attack description

<xhtml:p>An adversary targets the communication between two components (typically client and server), in order to alter or obtain data from transactions. A general approach entails the adversary placing themself within the communication channel between the two components.</xhtml:p>

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Determine Communication Mechanism: </b>The adversary determines the nature and mechanism of communication between two components, looking for opportunities to exploit.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Perform a sniffing attack and observe communication to determine a communication protocol.</td></tr><tr><td>Look for application documentation that might describe a communication mechanism used by a target.</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Position In Between Targets: </b>The adversary inserts themself into the communication channel initially acting as a routing proxy between the two targeted components.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Install spyware on a client that will intercept outgoing packets and route them to their destination as well as route incoming packets back to the client.</td></tr><tr><td>Exploit a weakness in an encrypted communication mechanism to gain access to traffic. Look for outdated mechanisms such as SSL.</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Use Intercepted Data Maliciously: </b>The adversary observes, filters, or alters passed data of its choosing to gain access to sensitive information or to manipulate the actions of the two target components for their own purposes.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Prevent some messages from reaching their destination, causing a denial of service.</td></tr></tbody></table></ol></div>

## Prerequisites

- There are two components communicating with each other.
- An attacker is able to identify the nature and mechanism of communication between the two target components.
- An attacker can eavesdrop on the communication between the target components.
- Strong mutual authentication is not used between the two target components yielding opportunity for attacker interposition.
- The communication occurs in clear (not encrypted) or with insufficient and spoofable encryption.

## Required skills

Medium: This attack can get sophisticated since the attack may use cryptography.

## Consequences

Access_Control: ['Gain Privileges']; Authorization: ['Gain Privileges']; Confidentiality: ['Gain Privileges', 'Read Data']; Integrity: ['Modify Data']

## ATT&CK adversary context

**Technique:** Adversary-in-the-Middle

Adversaries may attempt to position themselves between two or more networked devices using an adversary-in-the-middle (AiTM) technique to support follow-on behaviors such as [Network Sniffing](https://attack.mitre.org/techniques/T1040), [Transmitted Data Manipulation](https://attack.mitre.org/techniques/T1565/002), or replay attacks ([Exploitation for Credential Access](https://attack.mitre.org/techniques/T1212)). By abusing features of common networking protocols that can determine the flow of network traffic (e.g. ARP, DNS, LLMNR, etc.), adversaries may force a device to communicate through an adversary controlled system so they can collect information or perform additional actions.(Citation: Rapid7 MiTM Basics)

For example, adversaries may manipulate victim DNS settings to enable other malicious activities such as preventing/redirecting users from accessing legitimate sites and/or pushing additional malware.(Citation: ttint_rat)(Citation: dns_changer_trojans)(Citation: ad_blocker_with_miner) Adversaries may also manipulate DNS and leverage their position in order to intercept user credentials, including access tokens ([Steal Application Access Token](https://attack.mitre.org/techniques/T1528)) and session cookies ([Steal Web Session Cookie](https://attack.mitre.org/techniques/T1539)).(Citation: volexity_0day_sophos_FW)(Citation: Token tactics) [Downgrade Attack](https://attack.mitre.org/techniques/T1689)s can also be used to establish an AiTM position, such as by negotiating a less secure, deprecated, or weaker version of communication protocol (SSL/TLS) or encryption algorithm.(Citation: mitm_tls_downgrade_att)(Citation: taxonomy_downgrade_att_tls)(Citation: tlseminar_downgrade_att)

Adversaries may also leverage the AiTM position to attempt to monitor and/or modify traffic, such as in [Transmitted Data Manipulation](https://attack.mitre.org/techniques/T1565/002). Adversaries can setup a position similar to AiTM to prevent traffic from flowing to the appropriate destination, potentially to impair defenses and/or in support of a [Network Denial of Service](https://attack.mitre.org/techniques/T1498).

## Affected platforms

- Linux
- macOS
- Network Devices
- Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-94 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1557 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
