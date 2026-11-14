# Use of Known Kerberos Credentials

## Metadata

- Attack key: `use_of_known_kerberos_credentials`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-652`
- ATT&CK ID: `T1558`

## Attack description

An adversary obtains (i.e. steals or purchases) legitimate Kerberos credentials (e.g. Kerberos service account userID/password or Kerberos Tickets) with the goal of achieving authenticated access to additional systems, applications, or services within the domain.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Acquire known Kerberos credentials: </b>The adversary must obtain known Kerberos credentials in order to access the target system, application, or service within the domain.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>An adversary purchases breached Kerberos service account username/password combinations or leaked hashed passwords from the dark web.</td></tr><tr><td>An adversary guesses the credentials to a weak Kerberos service account.</td></tr><tr><td>An adversary conducts a sniffing attack to steal Kerberos tickets as they are transmitted.</td></tr><tr><td>An adversary conducts a Kerberoasting attack.</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Attempt Kerberos authentication: </b>Try each Kerberos credential against various resources within the domain until the target grants access.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Manually or automatically enter each Kerberos service account credential through the target's interface.</td></tr><tr><td>Attempt a Pass the Ticket attack.</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Impersonate: </b>An adversary can use successful experiments or authentications to impersonate an authorized user or system, or to laterally move within the domain</p></li><li> <p> <b>Spoofing: </b>Malicious data can be injected into the target system or into other systems on the domain. The adversary can also pose as a legitimate domain user to perform social engineering attacks.</p></li><li> <p> <b>Data Exfiltration: </b>The adversary can obtain sensitive data contained within domain systems or applications.</p></li></ol></div>

## Prerequisites

- The system/application leverages Kerberos authentication.
- The system/application uses one factor password-based authentication, SSO, and/or cloud-based authentication for Kerberos service accounts.
- The system/application does not have a sound password policy that is being enforced for Kerberos service accounts.
- The system/application does not implement an effective password throttling mechanism for authenticating to Kerberos service accounts.
- The targeted network allows for network sniffing attacks to succeed.

## Required resources

A valid Kerberos ticket or a known Kerberos service account credential.

## Required skills

Low: Once an adversary obtains a known Kerberos credential, leveraging it is trivial.

## Consequences

Access_Control: ['Gain Privileges']; Authentication: ['Gain Privileges']; Authorization: ['Read Data']; Confidentiality: ['Gain Privileges', 'Read Data']; Integrity: ['Modify Data']

## ATT&CK adversary context

**Technique:** Steal or Forge Kerberos Tickets

Adversaries may attempt to subvert Kerberos authentication by stealing or forging Kerberos tickets to enable [Pass the Ticket](https://attack.mitre.org/techniques/T1550/003). Kerberos is an authentication protocol widely used in modern Windows domain environments. In Kerberos environments, referred to as “realms”, there are three basic participants: client, service, and Key Distribution Center (KDC).(Citation: ADSecurity Kerberos Ring Decoder) Clients request access to a service and through the exchange of Kerberos tickets, originating from KDC, they are granted access after having successfully authenticated. The KDC is responsible for both authentication and ticket granting.  Adversaries may attempt to abuse Kerberos by stealing tickets or forging tickets to enable unauthorized access.

On Windows, the built-in <code>klist</code> utility can be used to list and analyze cached Kerberos tickets.(Citation: Microsoft Klist)


## Affected platforms

- Linux
- macOS
- Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-652 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1558 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
