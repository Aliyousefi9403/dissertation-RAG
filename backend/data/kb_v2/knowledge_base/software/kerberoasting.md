# Kerberoasting

## Metadata

- Attack key: `kerberoasting`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-509`
- ATT&CK ID: `T1558.003`

## Attack description

Through the exploitation of how service accounts leverage Kerberos authentication with Service Principal Names (SPNs), the adversary obtains and subsequently cracks the hashed credentials of a service account target to exploit its privileges. The Kerberos authentication protocol centers around a ticketing system which is used to request/grant access to services and to then access the requested services. As an authenticated user, the adversary may request Active Directory and obtain a service ticket with portions encrypted via RC4 with the private key of the authenticated account. By extracting the local ticket and saving it disk, the adversary can brute force the hashed value to reveal the target account credentials.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p>Scan for user accounts with set SPN values</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>These can be found via Powershell or LDAP queries, as well as enumerating startup name accounts and other means.</td></tr></tbody></table><li> <p>Request service tickets</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Using user account's SPN value, request other service tickets from Active Directory</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p>Extract ticket and save to disk</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Certain tools like Mimikatz can extract local tickets and save them to memory/disk.</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p>Crack the encrypted ticket to harvest plain text credentials</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Leverage a brute force application/script on the hashed value offline until cracked. The shorter the password, the easier it is to crack.</td></tr></tbody></table></ol></div>

## Prerequisites

- The adversary requires access as an authenticated user on the system. This attack pattern relates to elevating privileges.
- The adversary requires use of a third-party credential harvesting tool (e.g., Mimikatz).
- The adversary requires a brute force tool.

## Required skills

Medium:

## Consequences

Confidentiality: ['Gain Privileges']

## ATT&CK adversary context

**Technique:** Kerberoasting

Adversaries may abuse a valid Kerberos ticket-granting ticket (TGT) or sniff network traffic to obtain a ticket-granting service (TGS) ticket that may be vulnerable to [Brute Force](https://attack.mitre.org/techniques/T1110).(Citation: Empire InvokeKerberoast Oct 2016)(Citation: AdSecurity Cracking Kerberos Dec 2015) 

Service principal names (SPNs) are used to uniquely identify each instance of a Windows service. To enable authentication, Kerberos requires that SPNs be associated with at least one service logon account (an account specifically tasked with running a service(Citation: Microsoft Detecting Kerberoasting Feb 2018)).(Citation: Microsoft SPN)(Citation: Microsoft SetSPN)(Citation: SANS Attacking Kerberos Nov 2014)(Citation: Harmj0y Kerberoast Nov 2016)

Adversaries possessing a valid Kerberos ticket-granting ticket (TGT) may request one or more Kerberos ticket-granting service (TGS) service tickets for any SPN from a domain controller (DC).(Citation: Empire InvokeKerberoast Oct 2016)(Citation: AdSecurity Cracking Kerberos Dec 2015) Portions of these tickets may be encrypted with the RC4 algorithm, meaning the Kerberos 5 TGS-REP etype 23 hash of the service account associated with the SPN is used as the private key and is thus vulnerable to offline [Brute Force](https://attack.mitre.org/techniques/T1110) attacks that may expose plaintext credentials.(Citation: AdSecurity Cracking Kerberos Dec 2015)(Citation: Empire InvokeKerberoast Oct 2016) (Citation: Harmj0y Kerberoast Nov 2016)

This same behavior could be executed using service tickets captured from network traffic.(Citation: AdSecurity Cracking Kerberos Dec 2015)

Cracked hashes may enable [Persistence](https://attack.mitre.org/tactics/TA0003), [Privilege Escalation](https://attack.mitre.org/tactics/TA0004), and [Lateral Movement](https://attack.mitre.org/tactics/TA0008) via access to [Valid Accounts](https://attack.mitre.org/techniques/T1078).(Citation: SANS Attacking Kerberos Nov 2014)

## Affected platforms

Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-509 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1558.003 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
