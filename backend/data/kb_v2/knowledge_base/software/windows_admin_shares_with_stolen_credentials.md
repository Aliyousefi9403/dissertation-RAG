# Windows Admin Shares with Stolen Credentials

## Metadata

- Attack key: `windows_admin_shares_with_stolen_credentials`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-561`
- ATT&CK ID: `T1021.002`

## Attack description

An adversary guesses or obtains (i.e. steals or purchases) legitimate Windows administrator credentials (e.g. userID/password) to access Windows Admin Shares on a local machine or within a Windows domain.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Acquire known Windows administrator credentials: </b>The adversary must obtain known Windows administrator credentials in order to access the administrative network shares.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>An adversary purchases breached Windows administrator credentials from the dark web.</td></tr><tr><td>An adversary leverages a key logger or phishing attack to steal administrator credentials as they are provided.</td></tr><tr><td>An adversary conducts a sniffing attack to steal Windows administrator credentials as they are transmitted.</td></tr><tr><td>An adversary gains access to a Windows domain system/files and exfiltrates Windows administrator password hashes.</td></tr><tr><td>An adversary examines outward-facing configuration and properties files to discover hardcoded Windows administrator credentials.</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Attempt domain authentication: </b>Try each Windows administrator credential against the hidden network shares until the target grants access.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Manually or automatically enter each administrator credential through the target's interface.</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Malware Execution: </b>An adversary can remotely execute malware within the administrative network shares to infect other systems within the domain.</p></li><li> <p> <b>Data Exfiltration: </b>The adversary can remotely obtain sensitive data contained within the administrative network shares.</p></li></ol></div>

## Prerequisites

- The system/application is connected to the Windows domain.
- The target administrative share allows remote use of local admin credentials to log into domain systems.
- The adversary possesses a list of known Windows administrator credentials that exist on the target domain.

## Required resources

A list of known Windows administrator credentials for the targeted domain.

## Required skills

Low: Once an adversary obtains a known Windows credential, leveraging it is trivial.

## Consequences

Access_Control: ['Gain Privileges']; Authentication: ['Gain Privileges']; Authorization: ['Read Data']; Confidentiality: ['Gain Privileges', 'Read Data']; Integrity: ['Modify Data']

## ATT&CK adversary context

**Technique:** SMB/Windows Admin Shares

Adversaries may use [Valid Accounts](https://attack.mitre.org/techniques/T1078) to interact with a remote network share using Server Message Block (SMB). The adversary may then perform actions as the logged-on user.

SMB is a file, printer, and serial port sharing protocol for Windows machines on the same network or domain. Adversaries may use SMB to interact with file shares, allowing them to move laterally throughout a network. Linux and macOS implementations of SMB typically use Samba.

Windows systems have hidden network shares that are accessible only to administrators and provide the ability for remote file copy and other administrative functions. Example network shares include `C$`, `ADMIN$`, and `IPC$`. Adversaries may use this technique in conjunction with administrator-level [Valid Accounts](https://attack.mitre.org/techniques/T1078) to remotely access a networked system over SMB,(Citation: Wikipedia Server Message Block) to interact with systems using remote procedure calls (RPCs),(Citation: TechNet RPC) transfer files, and run transferred binaries through remote Execution. Example execution techniques that rely on authenticated sessions over SMB/RPC are [Scheduled Task/Job](https://attack.mitre.org/techniques/T1053), [Service Execution](https://attack.mitre.org/techniques/T1569/002), and [Windows Management Instrumentation](https://attack.mitre.org/techniques/T1047). Adversaries can also use NTLM hashes to access administrator shares on systems with [Pass the Hash](https://attack.mitre.org/techniques/T1550/002) and certain configuration and patch levels.(Citation: Microsoft Admin Shares)

## Affected platforms

Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-561 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1021.002 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
