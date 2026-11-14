# Task Impersonation

## Metadata

- Attack key: `task_impersonation`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-504`
- ATT&CK ID: `T1036.004`

## Attack description

An adversary, through a previously installed malicious application, impersonates an expected or routine task in an attempt to steal sensitive information or leverage a user's privileges.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Determine suitable tasks to exploit: </b>Determine what tasks exist on the target system that may result in a user providing sensitive information.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Determine what tasks prompt a user for their credentials.</td></tr><tr><td>Determine what tasks may prompt a user to authorize a process to execute with elevated privileges.</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Impersonate Task: </b>Impersonate a legitimate task, either expected or unexpected, in an attempt to gain user credentials or to ride the user's privileges.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Prompt a user for their credentials, while making the user believe the credential request is legitimate.</td></tr><tr><td>Prompt a user to authorize a task to run with elevated privileges, while making the user believe the request is legitimate.</td></tr></tbody></table></ol></div>

## Prerequisites

- The adversary must already have access to the target system via some means.
- A legitimate task must exist that an adversary can impersonate to glean credentials.
- The user's privileges allow them to execute certain tasks with elevated privileges.

## Required resources

- Malware or some other means to initially comprise the target system.
- Additional malware to impersonate a legitimate task.

## Required skills

Low: Once an adversary has gained access to the target system, impersonating a task is trivial.

## Consequences

Access_Control: ['Gain Privileges']; Authentication: ['Gain Privileges']

## ATT&CK adversary context

**Technique:** Masquerade Task or Service

Adversaries may attempt to manipulate the name of a task or service to make it appear legitimate or benign. Tasks/services executed by the Task Scheduler or systemd will typically be given a name and/or description.(Citation: TechNet Schtasks)(Citation: Systemd Service Units) Windows services will have a service name as well as a display name. Many benign tasks and services exist that have commonly associated names. Adversaries may give tasks or services names that are similar or identical to those of legitimate ones.

Tasks or services contain other fields, such as a description, that adversaries may attempt to make appear legitimate.(Citation: Palo Alto Shamoon Nov 2016)(Citation: Fysbis Dr Web Analysis)

## Affected platforms

- Linux
- macOS
- Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-504 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1036.004 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
