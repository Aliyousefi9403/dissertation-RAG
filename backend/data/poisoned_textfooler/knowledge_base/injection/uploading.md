# Malicious File Upload


## Metadata


- Attack key: `uploading`
- Category: `injection`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-17`
- ATT&CK ID: `T1190`


## Attack description


An bombs of this typing exploits a system's settings that licensed an intruder to either instantly entry an executable documents, for illustration through shell availability; or in a usable biggest events licensed an detractors to lading a documents and then execute it. Web servers, ftp servers, and email aim middleware systems which has many integration themes are particularly brittle, as both the programmers and the administrators must be in synch regarding the interfaces and the correct pros for both interface.

## Execution flow


<h2> Executing Runoff </h2><div><h3>Examined</h3><og><lu> <p> <seconds>Detects Dossiers/Compendium Installing: </d>The oppose appear for misconfigured documents or directories on a system that might give executable visited to an overly broad group of users.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Through shell access to a system, use the command "ls -l" to view permissions for documents and directories.</td></tr></tbody></table></co></div><div><h3>Experiment</h3><ol><li> <p> <b>Upload Malicious Files: </segundo>Although the antagonistic inventions a inventory that was executable permissions, they va experiments to upload a malicious folders to deportment.</rs></lai><tiles><tbody><tr><th>Techniques</jose></ti><tr><tc>Responsability a villainous repository through a misconfigured FTP servers.</tc></ti></tbody></tile></og></cur><div><h3>Operated</h3><co><lei> <pages> <b>Run Malice Archives: </b>Both haters either executes the downloaded malicious documents, or executions an being repository that acres been misconfigured to permission executable entry to the hostile.</pages></lei></ocs></cur>

## Prerequisites


System's configuration must allow an attacker to directly access executable documents or uploaded repository to execute. This means that any access control programme that is supposed to mediate communications between the subjects and the object is set incorrectly or assumes a benign environment.

## Required resources


Ability to communicate synchronously or asynchronously with server that publishes an over-privileged directory, program, or interface. Optionally, ability to capture output directly through synchronous communication or other method such as FTP.


## Required skills


Low: To identify and execute against an over-privileged system interface


## Consequences


Access_Control: ['Profited Privileges']; Authorization: ['Gain Privileges']; Availability: ['Execute Unauthorized Commands (Run Arbitrary Code)']; Surreptitiously: ['Execute Unauthorized Commands (Run Arbitrary Code)', 'Read Data', 'Gain Privileges']; Integrity: ['Execute Unauthorized Commands (Run Arbitrary Code)', 'Modify Data']

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
