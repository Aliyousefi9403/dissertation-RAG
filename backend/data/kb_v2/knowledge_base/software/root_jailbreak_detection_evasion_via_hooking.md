# Root/Jailbreak Detection Evasion via Hooking

## Metadata

- Attack key: `root_jailbreak_detection_evasion_via_hooking`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-660`
- ATT&CK ID: `T1055`

## Attack description

An adversary forces a non-restricted mobile application to load arbitrary code or code files, via Hooking, with the goal of evading Root/Jailbreak detection. Mobile device users often Root/Jailbreak their devices in order to gain administrative control over the mobile operating system and/or to install third-party mobile applications that are not provided by authorized application stores (e.g. Google Play Store and Apple App Store). Adversaries may further leverage these capabilities to escalate privileges or bypass access control on legitimate applications. Although many mobile applications check if a mobile device is Rooted/Jailbroken prior to authorized use of the application, adversaries may be able to "hook" code in order to circumvent these checks. Successfully evading Root/Jailbreak detection allows an adversary to execute administrative commands, obtain confidential data, impersonate legitimate users of the application, and more.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Identify application with attack potential: </b>The adversary searches for and identifies a mobile application that could be exploited for malicious purposes (e.g. banking, voting, or medical applications).</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Search application stores for mobile applications worth exploiting</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Develop code to be hooked into chosen target application: </b>The adversary develops code or leverages existing code that will be hooked into the target application in order to evade Root/Jailbreak detection methods.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Develop code or leverage existing code to bypass Root/Jailbreak detection methods.</td></tr><tr><td>Test the code to see if it works.</td></tr><tr><td>Iteratively develop the code until Root/Jailbreak detection methods are evaded.</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Execute code hooking to evade Root/Jailbreak detection methods: </b>Once hooking code has been developed or obtained, execute the code against the target application to evade Root/Jailbreak detection methods.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Hook code into the target application.</td></tr></tbody></table></ol></div>

## Prerequisites

The targeted application must be non-restricted to allow code hooking.

## Required resources

- The adversary must have a Rooted/Jailbroken mobile device.
- The adversary needs to have enough access to the target application to control the included code or file.

## Required skills

High: Knowledge about Root/Jailbreak detection and evasion techniques.; Medium: Knowledge about code hooking.

## Consequences

Access_Control: ['Read Data (An adversary may leverage Root/Jailbreak Detection Evasion via Hooking in order to obtain sensitive information.)']; Authorization: ['Execute Unauthorized Commands (Through Root/Jailbreak Detection Evasion via Hooking, the adversary compromises the integrity of the application.)', 'Gain Privileges']; Confidentiality: ['Gain Privileges', 'Read Data (An adversary may leverage Root/Jailbreak Detection Evasion via Hooking in order to obtain sensitive information.)']; Integrity: ['Execute Unauthorized Commands (Through Root/Jailbreak Detection Evasion via Hooking, the adversary compromises the integrity of the application.)']

## ATT&CK adversary context

**Technique:** Process Injection

Adversaries may inject code into processes in order to evade process-based defenses as well as possibly elevate privileges. Process injection is a method of executing arbitrary code in the address space of a separate live process. Running code in the context of another process may allow access to the process's memory, system/network resources, and possibly elevated privileges. Execution via process injection may also evade detection from security products since the execution is masked under a legitimate process. 

There are many different ways to inject code into a process, many of which abuse legitimate functionalities. These implementations exist for every major OS but are typically platform specific. 

More sophisticated samples may perform multiple process injections to segment modules and further evade detection, utilizing named pipes or other inter-process communication (IPC) mechanisms as a communication channel. 

## Affected platforms

- Linux
- macOS
- Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-660 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1055 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
