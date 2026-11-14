# Password Spraying

## Metadata

- Attack key: `password_spraying`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-565`
- ATT&CK ID: `T1110.003`

## Attack description

<xhtml:p>In a Password Spraying attack, an adversary tries a small list (e.g. 3-5) of common or expected passwords, often matching the target's complexity policy, against a known list of user accounts to gain valid credentials. The adversary tries a particular password for each user account, before moving onto the next password in the list. This approach assists the adversary in remaining undetected by avoiding rapid or frequent account lockouts. The adversary may then reattempt the process with additional passwords, once enough time has passed to prevent inducing a lockout.</xhtml:p>

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Determine target's password policy: </b>Determine the password policies of the target system/application.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Determine minimum and maximum allowed password lengths.</td></tr><tr><td>Determine format of allowed passwords (whether they are required or allowed to contain numbers, special characters, etc., or whether they are allowed to contain words from the dictionary).</td></tr><tr><td>Determine account lockout policy (a strict account lockout policy will prevent brute force attacks).</td></tr></tbody></table><li> <p> <b>Select passwords: </b>Pick the passwords to be used in the attack (e.g. commonly used passwords, passwords tailored to individual users, etc.)</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Select passwords based on common use or a particular user's additional details.</td></tr><tr><td>Select passwords based on the target's password complexity policies.</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Brute force password: </b>Given the finite space of possible passwords dictated by information determined in the previous steps, try each password for all known user accounts until the target grants access.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Manually or automatically enter the first password for each known user account through the target's interface. In most systems, start with the shortest and simplest possible passwords, because most users tend to select such passwords if allowed to do so.</td></tr><tr><td>Iterate through the remaining passwords for each known user account.</td></tr></tbody></table></ol></div>

## Prerequisites

- The system/application uses one factor password based authentication.
- The system/application does not have a sound password policy that is being enforced.
- The system/application does not implement an effective password throttling mechanism.
- The adversary possesses a list of known user accounts on the target system/application.

## Required resources

- A machine with sufficient resources for the job (e.g. CPU, RAM, HD).
- Applicable password lists.
- A password cracking tool or a custom script that leverages the password list to launch the attack.

## Required skills

Low: A Password Spraying attack is very straightforward. A variety of password cracking tools are widely available.

## Consequences

Access_Control: ['Gain Privileges']; Authentication: ['Gain Privileges']; Authorization: ['Read Data']; Confidentiality: ['Gain Privileges', 'Read Data']; Integrity: ['Modify Data']

## ATT&CK adversary context

**Technique:** Password Spraying

Adversaries may use a single or small list of commonly used passwords against many different accounts to attempt to acquire valid account credentials. Password spraying uses one password (e.g. 'Password01'), or a small list of commonly used passwords, that may match the complexity policy of the domain. Logins are attempted with that password against many different accounts on a network to avoid account lockouts that would normally occur when brute forcing a single account with many passwords. (Citation: BlackHillsInfosec Password Spraying)

Typically, management services over commonly used ports are used when password spraying. Commonly targeted services include the following:

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

In order to avoid detection thresholds, adversaries may deliberately throttle password spraying attempts to avoid triggering security alerting. Additionally, adversaries may leverage LDAP and Kerberos authentication attempts, which are less likely to trigger high-visibility events such as Windows "logon failure" event ID 4625 that is commonly triggered by failed SMB connection attempts.(Citation: Microsoft Storm-0940)  

## Affected platforms

- Containers
- ESXi
- IaaS
- Identity Provider
- Linux
- Network Devices
- Office Suite
- SaaS
- Windows
- macOS

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-565 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1110.003 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
