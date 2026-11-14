# Session Credential Falsification through Forging

## Metadata

- Attack key: `session_credential_falsification_through_forging`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-196`
- ATT&CK ID: `T1134.002`

## Attack description

An attacker creates a false but functional session credential in order to gain or usurp access to a service. Session credentials allow users to identify themselves to a service after an initial authentication without needing to resend the authentication information (usually a username and password) with every message. If an attacker is able to forge valid session credentials they may be able to bypass authentication or piggy-back off some other authenticated user's session. This attack differs from Reuse of Session IDs and Session Sidejacking attacks in that in the latter attacks an attacker uses a previous or existing credential without modification while, in a forging attack, the attacker must create their own credential, although it may be based on previously observed credentials.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Analyze and Understand Session IDs: </b>The attacker finds that the targeted application use session credentials to identify legitimate users.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>An attacker makes many anonymous connections and records the session IDs.</td></tr><tr><td>An attacker makes authorized connections and records the session tokens or credentials.</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Create Session IDs.: </b>Attackers craft messages containing their forged credentials in GET, POST request, HTTP headers or cookies.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>The attacker manipulates the HTTP request message and adds their forged session IDs in to the requests or cookies.</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Abuse the Victim's Session Credentials: </b>The attacker fixates falsified session ID to the victim when victim access the system. Once the victim has achieved a higher level of privilege, possibly by logging into the application, the attacker can now take over the session using the forged session identifier.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>The attacker loads the predefined or predicted session ID into their browser and browses to protected data or functionality.</td></tr><tr><td>The attacker loads the predefined or predicted session ID into their software and utilizes functionality with the rights of the victim.</td></tr></tbody></table></ol></div>

## Prerequisites

The targeted application must use session credentials to identify legitimate users. Session identifiers that remains unchanged when the privilege levels change. Predictable session identifiers.

## Required resources

Attackers may require tools to craft messages containing their forged credentials, and ability to send HTTP request to a web application.

## Required skills

Medium: Forge the session credential and reply the request.

## Consequences

Access_Control: ['Bypass Protection Mechanism']; Accountability: ['Gain Privileges']; Authentication: ['Gain Privileges']; Authorization: ['Execute Unauthorized Commands (Run Arbitrary Code)', 'Gain Privileges', 'Bypass Protection Mechanism']; Confidentiality: ['Read Data']; Integrity: ['Modify Data']; Non-Repudiation: ['Gain Privileges']

## ATT&CK adversary context

**Technique:** Create Process with Token

Adversaries may create a new process with an existing token to escalate privileges and bypass access controls. Processes can be created with the token and resulting security context of another user using features such as <code>CreateProcessWithTokenW</code> and <code>runas</code>.(Citation: Microsoft RunAs)

Creating processes with a token not associated with the current user may require the credentials of the target user, specific privileges to impersonate that user, or access to the token to be used. For example, the token could be duplicated via [Token Impersonation/Theft](https://attack.mitre.org/techniques/T1134/001) or created via [Make and Impersonate Token](https://attack.mitre.org/techniques/T1134/003) before being used to create a process.

While this technique is distinct from [Token Impersonation/Theft](https://attack.mitre.org/techniques/T1134/001), the techniques can be used in conjunction where a token is duplicated and then used to create a new process.

## Affected platforms

Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-196 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1134.002 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
