# Alteration of a Software Update

## Metadata

- Attack key: `alteration_of_a_software_update`
- Category: `social_engineering`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-669`
- ATT&CK ID: `T1195.002`

## Attack description

<xhtml:p>An adversary with access to an organization’s software update infrastructure inserts malware into the content of an outgoing update to fielded systems where a wide range of malicious effects are possible. With the same level of access, the adversary can alter a software update to perform specific malicious acts including granting the adversary control over the software’s normal functionality.</xhtml:p>

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Identify software with frequent updates: </b>The adversary must first identify a target software that has updates at least with some frequency, enough that there is am update infrastructure.</p></li></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Gain access to udpate infrastructure: </b>The adversary must then gain access to the organization's software update infrastructure. This can either be done by gaining remote access from outside the organization, or by having a malicious actor inside the organization gain access. It is often easier if someone within the organization gains access.</p></li></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Alter the software update: </b>Through access to the software update infrastructure, an adversary will alter the software update by injecting malware into the content of an outgoing update.</p></li></ol></div>

## Prerequisites

An adversary would need to have penetrated an organization’s software update infrastructure including gaining access to components supporting the configuration management of software versions and updates related to the software maintenance of customer systems.

## Required skills

High: Skills required include the ability to infiltrate the organization’s software update infrastructure either from the Internet or from within the organization, including subcontractors, and be able to change software being delivered to customer/user systems in an undetected manner.

## Consequences

Access_Control: ['Gain Privileges']; Authorization: ['Execute Unauthorized Commands']; Confidentiality: ['Read Data']; Integrity: ['Modify Data']

## ATT&CK adversary context

**Technique:** Compromise Software Supply Chain

Adversaries may manipulate application software prior to receipt by a final consumer for the purpose of data or system compromise. Supply chain compromise of software can take place in a number of ways, including manipulation of the application source code, manipulation of the update/distribution mechanism for that software, or replacing compiled releases with a modified version.

Targeting may be specific to a desired victim set or may be distributed to a broad set of consumers but only move on to additional tactics on specific victims.(Citation: Avast CCleaner3 2018)(Citation: Command Five SK 2011)  

## Affected platforms

- Linux
- Windows
- macOS

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-669 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1195.002 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
