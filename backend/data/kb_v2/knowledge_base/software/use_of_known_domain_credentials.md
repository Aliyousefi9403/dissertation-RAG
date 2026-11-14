# Use of Known Domain Credentials

## Metadata

- Attack key: `use_of_known_domain_credentials`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-560`
- ATT&CK ID: `T1078`

## Attack description

<xhtml:p>An adversary guesses or obtains (i.e. steals or purchases) legitimate credentials (e.g. userID/password) to achieve authentication and to perform authorized actions under the guise of an authenticated user or service.</xhtml:p>

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Acquire known credentials: </b>The adversary must obtain known credentials in order to access the target system, application, or service.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>An adversary purchases breached username/password combinations or leaked hashed passwords from the dark web.</td></tr><tr><td>An adversary leverages a key logger or phishing attack to steal user credentials as they are provided.</td></tr><tr><td>An adversary conducts a sniffing attack to steal credentials as they are transmitted.</td></tr><tr><td>An adversary gains access to a database and exfiltrates password hashes.</td></tr><tr><td>An adversary examines outward-facing configuration and properties files to discover hardcoded credentials.</td></tr></tbody></table><li> <p> <b>Determine target's password policy: </b>Determine the password policies of the target system/application to determine if the known credentials fit within the specified criteria.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Determine minimum and maximum allowed password lengths.</td></tr><tr><td>Determine format of allowed passwords (whether they are required or allowed to contain numbers, special characters, etc., or whether they are allowed to contain words from the dictionary).</td></tr><tr><td>Determine account lockout policy (a strict account lockout policy will prevent brute force attacks if multiple passwords are known for a single user account).</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Attempt authentication: </b>Try each credential until the target grants access.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Manually or automatically enter each credential through the target's interface.</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Impersonate: </b>An adversary can use successful experiments or authentications to impersonate an authorized user or system, or to laterally move within a system or application</p></li><li> <p> <b>Spoofing: </b>Malicious data can be injected into the target system or into a victim user's system by an adversary. The adversary can also pose as a legitimate user to perform social engineering attacks.</p></li><li> <p> <b>Data Exfiltration: </b>The adversary can obtain sensitive data contained within the system or application.</p></li></ol></div>

## Prerequisites

- The system/application uses one factor password based authentication, SSO, and/or cloud-based authentication.
- The system/application does not have a sound password policy that is being enforced.
- The system/application does not implement an effective password throttling mechanism.
- The adversary possesses a list of known user accounts and corresponding passwords that may exist on the target.

## Required resources

- A list of known credentials.
- A custom script that leverages the credential list to launch an attack.

## Required skills

Low: Once an adversary obtains a known credential, leveraging it is trivial.

## Consequences

Access_Control: ['Gain Privileges']; Authentication: ['Gain Privileges']; Authorization: ['Read Data']; Confidentiality: ['Gain Privileges', 'Read Data']; Integrity: ['Modify Data']

## ATT&CK adversary context

**Technique:** Valid Accounts

Adversaries may obtain and abuse credentials of existing accounts as a means of gaining Initial Access, Persistence, Privilege Escalation, or Defense Evasion. Compromised credentials may be used to bypass access controls placed on various resources on systems within the network and may even be used for persistent access to remote systems and externally available services, such as VPNs, Outlook Web Access, network devices, and remote desktop.(Citation: volexity_0day_sophos_FW) Compromised credentials may also grant an adversary increased privilege to specific systems or access to restricted areas of the network. Adversaries may choose not to use malware or tools in conjunction with the legitimate access those credentials provide to make it harder to detect their presence.

In some cases, adversaries may abuse inactive accounts: for example, those belonging to individuals who are no longer part of an organization. Using these accounts may allow the adversary to evade detection, as the original account user will not be present to identify any anomalous activity taking place on their account.(Citation: CISA MFA PrintNightmare)

The overlap of permissions for local, domain, and cloud accounts across a network of systems is of concern because the adversary may be able to pivot across accounts and systems to reach a high level of access (i.e., domain or enterprise administrator) to bypass access controls set within the enterprise.(Citation: TechNet Credential Theft)

## Affected platforms

- Containers
- ESXi
- IaaS
- Identity Provider
- Linux
- macOS
- Network Devices
- Office Suite
- SaaS
- Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-560 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1078 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
