# Malicious File Upload


## Metadata


- Attack key: `uploading`
- Category: `injection`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-17`
- ATT&CK ID: `T1190`


## Attack description


An attack of this type exploits a system's configuration that allows an adversary to either directly access an executable file, for example through shell access; or in a possible worst case allows an adversary to upload a file and then execute it. Web servers, ftp servers, and message oriented middleware systems which have many integration points are particularly vulnerable, because both the programmers and the administrators must be in synch regarding the interfaces and the correct privileges for each interface.


## Execution flow


<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Determine File/Directory Configuration: </b>The adversary looks for misconfigured files or directories on a system that might give executable access to an overly broad group of users.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Through shell access to a system, use the command "ls -l" to view permissions for files and directories.</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Upload Malicious Files: </b>If the adversary discovers a directory that has executable permissions, they will attempt to upload a malicious file to execute.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Upload a malicious file through a misconfigured FTP server.</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Execute Malicious File: </b>The adversary either executes the uploaded malicious file, or executes an existing file that has been misconfigured to allow executable access to the adversary.</p></li></ol></div>


## Prerequisites


System's configuration must allow an attacker to directly access executable files or upload files to execute. This means that any access control system that is supposed to mediate communications between the subject and the object is set incorrectly or assumes a benign environment.


## Required resources


Ability to communicate synchronously or asynchronously with server that publishes an over-privileged directory, program, or interface. Optionally, ability to capture output directly through synchronous communication or other method such as FTP.


## Required skills


Low: To identify and execute against an over-privileged system interface


## Consequences


Access_Control: ['Gain Privileges']; Authorization: ['Gain Privileges']; Availability: ['Execute Unauthorized Commands (Run Arbitrary Code)']; Confidentiality: ['Execute Unauthorized Commands (Run Arbitrary Code)', 'Read Data', 'Gain Privileges']; Integrity: ['Execute Unauthorized Commands (Run Arbitrary Code)', 'Modify Data']


## ATT&CK adversary context


**Technique:** Exploit Public-Facing Application

Adversaries may attempt to exploit a weakness in an Internet-facing host or system to initially access a network. The weakness in the system can be a software bug, a temporary glitch, or a misconfiguration.

Exploited applications are often websites/web servers, but can also include databases (like SQL), standard services (like SMB or SSH), network device administration and management protocols (like SNMP and Smart Install), and any other system with Internet-accessible open sockets.(Citation: NVD CVE-2016-6662)(Citation: CIS Multiple SMB Vulnerabilities)(Citation: US-CERT TA18-106A Network Infrastructure Devices 2018)(Citation: Cisco Blog Legacy Device Attacks)(Citation: NVD CVE-2014-7169) On ESXi infrastructure, adversaries may exploit exposed OpenSLP services; they may alternatively exploit exposed VMware vCenter servers.(Citation: Recorded Future ESXiArgs Ransomware 2023)(Citation: Ars Technica VMWare Code Execution Vulnerability 2021) Depending on the flaw being exploited, this may also involve [Exploitation for Stealth](https://attack.mitre.org/techniques/T1211) or [Exploitation for Client Execution](https://attack.mitre.org/techniques/T1203).

If an application is hosted on cloud-based infrastructure and/or is containerized, then exploiting it may lead to compromise of the underlying instance or container. This can allow an adversary a path to access the cloud or container APIs (e.g., via the [Cloud Instance Metadata API](https://attack.mitre.org/techniques/T1552/005)), exploit container host access via [Escape to Host](https://attack.mitre.org/techniques/T1611), or take advantage of weak identity and access management policies.

Adversaries may also exploit edge network infrastructure and related appliances, specifically targeting devices that do not support robust host-based defenses.(Citation: Mandiant Fortinet Zero Day)(Citation: Wired Russia Cyberwar)

For websites and databases, the OWASP top 10 and CWE top 25 highlight the most common web-based vulnerabilities.(Citation: OWASP Top 10)(Citation: CWE top 25)


## Affected platforms


- Containers
- ESXi
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


- CAPEC: CAPEC-17 — role: malicious_file_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1190 — role: public_facing_application_context; optional
- OWASP: File Upload Cheat Sheet — role: prevention_and_mitigation; required
- CWE: CWE-434 — role: dangerous_file_type_context; required


## Provenance


- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
