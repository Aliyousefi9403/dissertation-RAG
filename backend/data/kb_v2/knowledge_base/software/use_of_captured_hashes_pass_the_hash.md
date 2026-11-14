# Use of Captured Hashes (Pass The Hash)

## Metadata

- Attack key: `use_of_captured_hashes_pass_the_hash`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-644`
- ATT&CK ID: `T1550.002`

## Attack description

An adversary obtains (i.e. steals or purchases) legitimate Windows domain credential hash values to access systems within the domain that leverage the Lan Man (LM) and/or NT Lan Man (NTLM) authentication protocols.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Acquire known Windows credential hash value pairs: </b>The adversary must obtain known Windows credential hash value pairs of accounts that exist on the domain.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>An adversary purchases breached Windows credential hash value pairs from the dark web.</td></tr><tr><td>An adversary conducts a sniffing attack to steal Windows credential hash value pairs as they are transmitted.</td></tr><tr><td>An adversary gains access to a Windows domain system/files and exfiltrates Windows credential hash value pairs.</td></tr><tr><td>An adversary examines outward-facing configuration and properties files to discover hardcoded Windows credential hash value pairs.</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Attempt domain authentication: </b>Try each Windows credential hash value pair until the target grants access.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Manually or automatically enter each Windows credential hash value pair through the target's interface.</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Impersonate: </b>An adversary can use successful experiments or authentications to impersonate an authorized user or system, or to laterally move within the domain</p></li><li> <p> <b>Spoofing: </b>Malicious data can be injected into the target system or into other systems on the domain. The adversary can also pose as a legitimate domain user to perform social engineering attacks.</p></li><li> <p> <b>Data Exfiltration: </b>The adversary can obtain sensitive data contained within domain systems or applications.</p></li></ol></div>

## Prerequisites

- The system/application is connected to the Windows domain.
- The system/application leverages the Lan Man (LM) and/or NT Lan Man (NTLM) authentication protocols.
- The adversary possesses known Windows credential hash value pairs that exist on the target domain.

## Required resources

A list of known Window credential hash value pairs for the targeted domain.

## Required skills

Low: Once an adversary obtains a known Windows credential hash value pair, leveraging it is trivial.

## Consequences

Access_Control: ['Gain Privileges']; Authentication: ['Gain Privileges']; Authorization: ['Read Data']; Confidentiality: ['Gain Privileges', 'Read Data']; Integrity: ['Modify Data']

## ATT&CK adversary context

**Technique:** Pass the Hash

Adversaries may “pass the hash” using stolen password hashes to move laterally within an environment, bypassing normal system access controls. Pass the hash (PtH) is a method of authenticating as a user without having access to the user's cleartext password. This method bypasses standard authentication steps that require a cleartext password, moving directly into the portion of the authentication that uses the password hash.

When performing PtH, valid password hashes for the account being used are captured using a [Credential Access](https://attack.mitre.org/tactics/TA0006) technique. Captured hashes are used with PtH to authenticate as that user. Once authenticated, PtH may be used to perform actions on local or remote systems.

Adversaries may also use stolen password hashes to "overpass the hash." Similar to PtH, this involves using a password hash to authenticate as a user but also uses the password hash to create a valid Kerberos ticket. This ticket can then be used to perform [Pass the Ticket](https://attack.mitre.org/techniques/T1550/003) attacks.(Citation: Stealthbits Overpass-the-Hash)

## Affected platforms

Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-644 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1550.002 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
