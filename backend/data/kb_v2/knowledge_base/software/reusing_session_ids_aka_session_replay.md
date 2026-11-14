# Reusing Session IDs (aka Session Replay)

## Metadata

- Attack key: `reusing_session_ids_aka_session_replay`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-60`
- ATT&CK ID: `T1134.001`

## Attack description

This attack targets the reuse of valid session ID to spoof the target system in order to gain privileges. The attacker tries to reuse a stolen session ID used previously during a transaction to perform spoofing and session hijacking. Another name for this type of attack is Session Replay.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p>The attacker interacts with the target host and finds that session IDs are used to authenticate users.</p></li><li> <p>The attacker steals a session ID from a valid user.</p></li></ol></div><div><h3>Exploit</h3><ol><li> <p>The attacker tries to use the stolen session ID to gain access to the system with the privileges of the session ID's original owner.</p></li></ol></div>

## Prerequisites

- The target host uses session IDs to keep track of the users.
- Session IDs are used to control access to resources.
- The session IDs used by the target host are not well protected from session theft.

## Required skills

Low: If an attacker can steal a valid session ID, they can then try to be authenticated with that stolen session ID.; Medium: More sophisticated attack can be used to hijack a valid session from a user and spoof a legitimate user by reusing their valid session ID.

## Consequences

Access_Control: ['Gain Privileges']; Authorization: ['Gain Privileges']; Confidentiality: ['Gain Privileges']

## ATT&CK adversary context

**Technique:** Token Impersonation/Theft

Adversaries may duplicate then impersonate another user's existing token to escalate privileges and bypass access controls. For example, an adversary can duplicate an existing token using `DuplicateToken` or `DuplicateTokenEx`.(Citation: DuplicateToken function) The token can then be used with `ImpersonateLoggedOnUser` to allow the calling thread to impersonate a logged on user's security context, or with `SetThreadToken` to assign the impersonated token to a thread.

An adversary may perform [Token Impersonation/Theft](https://attack.mitre.org/techniques/T1134/001) when they have a specific, existing process they want to assign the duplicated token to. For example, this may be useful for when the target user has a non-network logon session on the system.

When an adversary would instead use a duplicated token to create a new process rather than attaching to an existing process, they can additionally [Create Process with Token](https://attack.mitre.org/techniques/T1134/002) using `CreateProcessWithTokenW` or `CreateProcessAsUserW`. [Token Impersonation/Theft](https://attack.mitre.org/techniques/T1134/001) is also distinct from [Make and Impersonate Token](https://attack.mitre.org/techniques/T1134/003) in that it refers to duplicating an existing token, rather than creating a new one.

## Affected platforms

Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-60 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1134.001 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
