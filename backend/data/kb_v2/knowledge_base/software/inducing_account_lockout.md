# Inducing Account Lockout

## Metadata

- Attack key: `inducing_account_lockout`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-2`
- ATT&CK ID: `T1531`

## Attack description

An attacker leverages the security functionality of the system aimed at thwarting potential attacks to launch a denial of service attack against a legitimate system user. Many systems, for instance, implement a password throttling mechanism that locks an account after a certain number of incorrect log in attempts. An attacker can leverage this throttling mechanism to lock a legitimate user out of their own account. The weakness that is being leveraged by an attacker is the very security feature that has been put in place to counteract attacks.

## Execution flow

<h2> Execution Flow </h2><div><h3>Experiment</h3><ol><li> <p> <b>Investigate account lockout behavior of system: </b>Investigate the security features present in the system that may trigger an account lockout</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Analyze system documentation to find list of events that could potentially cause account lockout</td></tr><tr><td>Obtain user account in system and attempt to lock it out by sending malformed or incorrect data repeatedly</td></tr><tr><td>Determine another user's login ID, and attempt to brute force the password (or other credentials) for it a predetermined number of times, or until the system provides an indication that the account is locked out.</td></tr></tbody></table><li> <p> <b>Obtain list of user accounts to lock out: </b>Generate a list of valid user accounts to lock out</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Obtain list of authorized users using another attack pattern, such as SQL Injection.</td></tr><tr><td>Attempt to create accounts if possible; system should indicate if a user ID is already taken.</td></tr><tr><td>Attempt to brute force user IDs if system reveals whether a given user ID is valid or not upon failed login attempts.</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Lock Out Accounts: </b>Perform lockout procedure for all accounts that the attacker wants to lock out.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>For each user ID to be locked out, perform the lockout procedure discovered in the first step.</td></tr></tbody></table></ol></div>

## Prerequisites

- The system has a lockout mechanism.
- An attacker must be able to reproduce behavior that would result in an account being locked.

## Required resources

Computer with access to the login portion of the target system

## Required skills

Low: No programming skills or computer knowledge is needed. An attacker can easily use this attack pattern following the Execution Flow above.

## Consequences

Availability: ['Resource Consumption (Denial of Service)']

## ATT&CK adversary context

**Technique:** Account Access Removal

Adversaries may interrupt availability of system and network resources by inhibiting access to accounts utilized by legitimate users. Accounts may be deleted, locked, or manipulated (ex: changed credentials, revoked permissions for SaaS platforms such as Sharepoint) to remove access to accounts.(Citation: Obsidian Security SaaS Ransomware June 2023) Adversaries may also subsequently log off and/or perform a [System Shutdown/Reboot](https://attack.mitre.org/techniques/T1529) to set malicious changes into place.(Citation: CarbonBlack LockerGoga 2019)(Citation: Unit42 LockerGoga 2019)

In Windows, [Net](https://attack.mitre.org/software/S0039) utility, <code>Set-LocalUser</code> and <code>Set-ADAccountPassword</code> [PowerShell](https://attack.mitre.org/techniques/T1059/001) cmdlets may be used by adversaries to modify user accounts. Accounts could also be disabled by Group Policy. In Linux, the <code>passwd</code> utility may be used to change passwords. On ESXi servers, accounts can be removed or modified via esxcli (`system account set`, `system account remove`).

Adversaries who use ransomware or similar attacks may first perform this and other Impact behaviors, such as [Data Destruction](https://attack.mitre.org/techniques/T1485) and [Defacement](https://attack.mitre.org/techniques/T1491), in order to impede incident response/recovery before completing the [Data Encrypted for Impact](https://attack.mitre.org/techniques/T1486) objective. 

## Affected platforms

- Linux
- macOS
- Windows
- SaaS
- IaaS
- Office Suite
- ESXi

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-2 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1531 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
