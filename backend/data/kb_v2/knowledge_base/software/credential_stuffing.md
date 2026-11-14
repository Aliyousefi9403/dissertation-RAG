# Credential Stuffing

## Metadata

- Attack key: `credential_stuffing`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-600`
- ATT&CK ID: `T1110.004`

## Attack description

<xhtml:p>An adversary tries known username/password combinations against different systems, applications, or services to gain additional authenticated access. Credential Stuffing attacks rely upon the fact that many users leverage the same username/password combination for multiple systems, applications, and services.</xhtml:p>

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Acquire known credentials: </b>The adversary must obtain known credentials in order to access the target system, application, or service.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>An adversary purchases breached username/password combinations or leaked hashed passwords from the dark web.</td></tr><tr><td>An adversary leverages a key logger or phishing attack to steal user credentials as they are provided.</td></tr><tr><td>An adversary conducts a sniffing attack to steal credentials as they are transmitted.</td></tr><tr><td>An adversary gains access to a database and exfiltrates password hashes.</td></tr><tr><td>An adversary examines outward-facing configuration and properties files to discover hardcoded credentials.</td></tr></tbody></table><li> <p> <b>Determine target's password policy: </b>Determine the password policies of the target system/application to determine if the known credentials fit within the specified criteria.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Determine minimum and maximum allowed password lengths.</td></tr><tr><td>Determine format of allowed passwords (whether they are required or allowed to contain numbers, special characters, etc., or whether they are allowed to contain words from the dictionary).</td></tr><tr><td>Determine account lockout policy (a strict account lockout policy will prevent brute force attacks if multiple passwords are known for a single user account).</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Attempt authentication: </b>Try each username/password combination until the target grants access.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Manually or automatically enter each username/password combination through the target's interface.</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Impersonate: </b>An adversary can use successful experiments or authentications to impersonate an authorized user or system or to laterally move within a system or application</p></li><li> <p> <b>Spoofing: </b>Malicious data can be injected into the target system or into a victim user's system by an adversary. The adversary can also pose as a legitimate user to perform social engineering attacks.</p></li><li> <p> <b>Data Exfiltration: </b>The adversary can obtain sensitive data contained within the system or application.</p></li></ol></div>

## Prerequisites

- The system/application uses one factor password based authentication, SSO, and/or cloud-based authentication.
- The system/application does not have a sound password policy that is being enforced.
- The system/application does not implement an effective password throttling mechanism.
- The adversary possesses a list of known user accounts and corresponding passwords that may exist on the target.

## Required resources

- A machine with sufficient resources for the job (e.g. CPU, RAM, HD).
- A known list of username/password combinations.
- A custom script that leverages the credential list to launch the attack.

## Required skills

Low: A Credential Stuffing attack is very straightforward.

## Consequences

Access_Control: ['Gain Privileges']; Authentication: ['Gain Privileges']; Authorization: ['Read Data']; Confidentiality: ['Gain Privileges', 'Read Data']; Integrity: ['Modify Data']

## ATT&CK adversary context

**Technique:** Credential Stuffing

Adversaries may use credentials obtained from breach dumps of unrelated accounts to gain access to target accounts through credential overlap. Occasionally, large numbers of username and password pairs are dumped online when a website or service is compromised and the user account credentials accessed. The information may be useful to an adversary attempting to compromise accounts by taking advantage of the tendency for users to use the same passwords across personal and business accounts.

Credential stuffing is a risky option because it could cause numerous authentication failures and account lockouts, depending on the organization's login failure policies.

Typically, management services over commonly used ports are used when stuffing credentials. Commonly targeted services include the following:

* SSH (22/TCP)
* Telnet (23/TCP)
* FTP (21/TCP)
* NetBIOS / SMB / Samba (139/TCP & 445/TCP)
* LDAP (389/TCP)
* Kerberos (88/TCP)
* RDP / Terminal Services (3389/TCP)
* HTTP/HTTP Management Services (80/TCP & 443/TCP)
* MSSQL (1433/TCP)
* Oracle (1521/TCP)
* MySQL (3306/TCP)
* VNC (5900/TCP)

In addition to management services, adversaries may "target single sign-on (SSO) and cloud-based applications utilizing federated authentication protocols," as well as externally facing email applications, such as Office 365.(Citation: US-CERT TA18-068A 2018)

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

- CAPEC: CAPEC-600 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1110.004 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
