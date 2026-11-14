# Collect Data from Registries

## Metadata

- Attack key: `collect_data_from_registries`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-647`
- ATT&CK ID: `T1005`

## Attack description

An adversary exploits a weakness in authorization to gather system-specific data and sensitive information within a registry (e.g., Windows Registry, Mac plist). These contain information about the system configuration, software, operating system, and security. The adversary can leverage information gathered in order to carry out further attacks.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Gain logical access to system: </b>An adversary must first gain logical access to the system it wants to gather registry information from,</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Obtain user account credentials and access the system</td></tr><tr><td>Plant malware on the system that will give remote logical access to the adversary</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Determine if the permissions are correct: </b>Once logical access is gained, an adversary will determine if they have the proper permissions, or are authorized, to view registry information. If they do not, they will need to escalate privileges on the system through other means</p></li><li> <p> <b>Peruse registry for information: </b>Once an adversary has access to a registry, they will gather all system-specific data and sensitive information that they deem useful.</p></li></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Follow-up attack: </b>Use any information or weaknesses found to carry out a follow-up attack</p></li></ol></div>

## Prerequisites

- The adversary must have obtained logical access to the system by some means (e.g., via obtained credentials or planting malware on the system).
- The adversary must have capability to navigate the operating system to peruse the registry.

## Required resources

None: No specialized resources are required to execute this type of attack.

## Required skills

Low: Once the adversary has logical access (which can potentially require high knowledge and skill level), the adversary needs only the capability and facility to navigate the system through the OS graphical user interface or the command line.

## Consequences

Confidentiality: ['Read Data (The adversary is able to read sensitive information about the system in the registry.)']

## ATT&CK adversary context

**Technique:** Data from Local System

Adversaries may search local system sources, such as file systems, configuration files, local databases, virtual machine files, or process memory, to find files of interest and sensitive data prior to Exfiltration.

Adversaries may do this using a [Command and Scripting Interpreter](https://attack.mitre.org/techniques/T1059), such as [cmd](https://attack.mitre.org/software/S0106) as well as a [Network Device CLI](https://attack.mitre.org/techniques/T1059/008), which have functionality to interact with the file system to gather information.(Citation: show_run_config_cmd_cisco) Adversaries may also use [Automated Collection](https://attack.mitre.org/techniques/T1119) on the local system.


## Affected platforms

- ESXi
- Linux
- macOS
- Network Devices
- Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-647 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1005 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
