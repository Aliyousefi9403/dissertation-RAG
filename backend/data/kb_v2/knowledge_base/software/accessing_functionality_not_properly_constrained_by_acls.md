# Accessing Functionality Not Properly Constrained by ACLs

## Metadata

- Attack key: `accessing_functionality_not_properly_constrained_by_acls`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-1`
- ATT&CK ID: `T1574.010`

## Attack description

In applications, particularly web applications, access to functionality is mitigated by an authorization framework. This framework maps Access Control Lists (ACLs) to elements of the application's functionality; particularly URL's for web apps. In the case that the administrator failed to specify an ACL for a particular element, an attacker may be able to access it with impunity. An attacker with the ability to access functionality not properly constrained by ACLs can obtain sensitive information and possibly compromise the entire application. Such an attacker can access resources that must be available only to users at a higher privilege level, can access management sections of the application, or can run queries for data that they otherwise not supposed to.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Survey: </b>The attacker surveys the target application, possibly as a valid and authenticated user</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Spidering web sites for all available links</td></tr><tr><td>Brute force guessing of resource names</td></tr><tr><td>Brute force guessing of user names / credentials</td></tr><tr><td>Brute force guessing of function names / actions</td></tr></tbody></table><li> <p> <b>Identify Functionality: </b>At each step, the attacker notes the resource or functionality access mechanism invoked upon performing specific actions</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Use the web inventory of all forms and inputs and apply attack data to those inputs.</td></tr><tr><td>Use a packet sniffer to capture and record network traffic</td></tr><tr><td>Execute the software in a debugger and record API calls into the operating system or important libraries. This might occur in an environment other than a production environment, in order to find weaknesses that can be exploited in a production environment.</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Iterate over access capabilities: </b>Possibly as a valid user, the attacker then tries to access each of the noted access mechanisms directly in order to perform functions not constrained by the ACLs.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Fuzzing of API parameters (URL parameters, OS API parameters, protocol parameters)</td></tr></tbody></table></ol></div>

## Prerequisites

- The application must be navigable in a manner that associates elements (subsections) of the application with ACLs.
- The various resources, or individual URLs, must be somehow discoverable by the attacker
- The administrator must have forgotten to associate an ACL or has associated an inappropriately permissive ACL with a particular navigable resource.

## Required resources

None: No specialized resources are required to execute this type of attack.

## Required skills

Low: In order to discover unrestricted resources, the attacker does not need special tools or skills. They only have to observe the resources or access mechanisms invoked as each action is performed and then try and access those access mechanisms directly.

## Consequences

Access_Control: ['Gain Privileges']; Authorization: ['Gain Privileges']; Confidentiality: ['Gain Privileges']

## ATT&CK adversary context

**Technique:** Services File Permissions Weakness

Adversaries may execute their own malicious payloads by hijacking the binaries used by services. Adversaries may use flaws in the permissions of Windows services to replace the binary that is executed upon service start. These service processes may automatically execute specific binaries as part of their functionality or to perform other actions. If the permissions on the file system directory containing a target binary, or permissions on the binary itself are improperly set, then the target binary may be overwritten with another binary using user-level permissions and executed by the original process. If the original process and thread are running under a higher permissions level, then the replaced binary will also execute under higher-level permissions, which could include SYSTEM.

Adversaries may use this technique to replace legitimate binaries with malicious ones as a means of executing code at a higher permissions level. If the executing process is set to run at a specific time or during a certain event (e.g., system bootup) then this technique can also be used for persistence.

## Affected platforms

Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-1 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1574.010 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
