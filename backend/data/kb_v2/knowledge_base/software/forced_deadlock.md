# Forced Deadlock

## Metadata

- Attack key: `forced_deadlock`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-25`
- ATT&CK ID: `T1499.004`

## Attack description

The adversary triggers and exploits a deadlock condition in the target software to cause a denial of service. A deadlock can occur when two or more competing actions are waiting for each other to finish, and thus neither ever does. Deadlock conditions can be difficult to detect.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p>The adversary initiates an exploratory phase to get familiar with the system.</p></li><li> <p>The adversary triggers a first action (such as holding a resource) and initiates a second action which will wait for the first one to finish.</p></li><li> <p>If the target program has a deadlock condition, the program waits indefinitely resulting in a denial of service.</p></li></ol></div>

## Prerequisites

- The target host has a deadlock condition. There are four conditions for a deadlock to occur, known as the Coffman conditions. [REF-101]
- The target host exposes an API to the user.

## Required skills

Medium: This type of attack may be sophisticated and require knowledge about the system's resources and APIs.

## Consequences

Availability: ['Resource Consumption (A successful forced deadlock attack compromises the availability of the system by exhausting its available resources.)']

## ATT&CK adversary context

**Technique:** Application or System Exploitation

Adversaries may exploit software vulnerabilities that can cause an application or system to crash and deny availability to users. (Citation: Sucuri BIND9 August 2015) Some systems may automatically restart critical applications and services when crashes occur, but they can likely be re-exploited to cause a persistent denial of service (DoS) condition.

Adversaries may exploit known or zero-day vulnerabilities to crash applications and/or systems, which may also lead to dependent applications and/or systems to be in a DoS condition. Crashed or restarted applications or systems may also have other effects such as [Data Destruction](https://attack.mitre.org/techniques/T1485), [Firmware Corruption](https://attack.mitre.org/techniques/T1495), [Service Stop](https://attack.mitre.org/techniques/T1489) etc. which may further cause a DoS condition and deny availability to critical information, applications and/or systems. 

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

- CAPEC: CAPEC-25 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1499.004 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
