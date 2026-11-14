# Symlink Attack

## Metadata

- Attack key: `symlink_attack`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-132`
- ATT&CK ID: `T1547.009`

## Attack description

An adversary positions a symbolic link in such a manner that the targeted user or application accesses the link's endpoint, assuming that it is accessing a file with the link's name.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Identify Target: </b>Adversary identifies the target application by determining whether there is sufficient check before writing data to a file and creating symlinks to files in different directories.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>The adversary writes to files in different directories to check whether the application has sufficient checking before file operations.</td></tr><tr><td>The adversary creates symlinks to files in different directories.</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Try to create symlinks to different files: </b>The adversary then uses a variety of techniques, such as monitoring or guessing to create symlinks to the files accessed by the target application in the directories which are identified in the explore phase.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>The adversary monitors the file operations performed by the target application using a tool like dtrace or FileMon. And the adversary can delay the operations by using "sleep(2)" and "usleep()" to prepare the appropriate conditions for the attack, or make the application perform expansive tasks (large files parsing, etc.) depending on the purpose of the application.</td></tr><tr><td>The adversary may need a little guesswork on the filenames on which the target application would operate.</td></tr><tr><td>The adversary tries to create symlinks to the various filenames.</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Target application operates on created symlinks to sensitive files: </b>The adversary is able to create symlinks to sensitive files while the target application is operating on the file.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Create the symlink to the sensitive file such as configuration files, etc.</td></tr></tbody></table></ol></div>

## Prerequisites

The targeted application must perform the desired activities on a file without checking whether the file is a symbolic link or not. The adversary must be able to predict the name of the file the target application is modifying and be able to create a new symbolic link where that file would appear.

## Required resources

None: No specialized resources are required to execute this type of attack. The only requirement is the ability to create the necessary symbolic link.

## Required skills

High: To identify the files and create the symlinks during the file operation time window; Low: To create symlinks

## Consequences

Access_Control: ['Bypass Protection Mechanism']; Accountability: ['Gain Privileges']; Authentication: ['Gain Privileges']; Authorization: ['Execute Unauthorized Commands (Run Arbitrary Code)', 'Gain Privileges', 'Bypass Protection Mechanism']; Availability: ['Unreliable Execution']; Confidentiality: ['Other (Information Leakage)', 'Read Data']; Integrity: ['Modify Data', 'Modify Data']; Non-Repudiation: ['Gain Privileges']

## ATT&CK adversary context

**Technique:** Shortcut Modification

Adversaries may create or modify shortcuts that can execute a program during system boot or user login. Shortcuts or symbolic links are used to reference other files or programs that will be opened or executed when the shortcut is clicked or executed by a system startup process.

Adversaries may abuse shortcuts in the startup folder to execute their tools and achieve persistence.(Citation: Shortcut for Persistence ) Although often used as payloads in an infection chain (e.g. [Spearphishing Attachment](https://attack.mitre.org/techniques/T1566/001)), adversaries may also create a new shortcut as a means of indirection, while also abusing [Masquerading](https://attack.mitre.org/techniques/T1036) to make the malicious shortcut appear as a legitimate program. Adversaries can also edit the target path or entirely replace an existing shortcut so their malware will be executed instead of the intended legitimate program.

Shortcuts can also be abused to establish persistence by implementing other methods. For example, LNK browser extensions may be modified (e.g. [Browser Extensions](https://attack.mitre.org/techniques/T1176/001)) to persistently launch malware.

## Affected platforms

Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-132 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1547.009 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
