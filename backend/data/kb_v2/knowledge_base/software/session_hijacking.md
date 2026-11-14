# Session Hijacking

## Metadata

- Attack key: `session_hijacking`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-593`
- ATT&CK ID: `T1185`

## Attack description

This type of attack involves an adversary that exploits weaknesses in an application's use of sessions in performing authentication. The adversary is able to steal or manipulate an active session and use it to gain unathorized access to the application.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Discover Existing Session Token: </b>Through varrying means, an adversary will discover and store an existing session token for some other authenticated user session.</p></li></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Insert Found Session Token: </b>The attacker attempts to insert a found session token into communication with the targeted application to confirm viability for exploitation.</p></li></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Session Token Exploitation: </b>The attacker leverages the captured session token to interact with the targeted application in a malicious fashion, impersonating the victim.</p></li></ol></div>

## Prerequisites

An application that leverages sessions to perform authentication.

## Required resources

The adversary must have the ability to communicate with the application over the network.

## Required skills

Low: Exploiting a poorly protected identity token is a well understood attack with many helpful resources available.

## Consequences

Availability: ['Gain Privileges (A successful attack can enable an adversary to gain unauthorized access to an application.)']; Confidentiality: ['Gain Privileges (A successful attack can enable an adversary to gain unauthorized access to an application.)']; Integrity: ['Gain Privileges (A successful attack can enable an adversary to gain unauthorized access to an application.)']

## ATT&CK adversary context

**Technique:** Browser Session Hijacking

Adversaries may take advantage of security vulnerabilities and inherent functionality in browser software to change content, modify user-behaviors, and intercept information as part of various browser session hijacking techniques.(Citation: Wikipedia Man in the Browser)

A specific example is when an adversary injects software into a browser that allows them to inherit cookies, HTTP sessions, and SSL client certificates of a user then use the browser as a way to pivot into an authenticated intranet.(Citation: Cobalt Strike Browser Pivot)(Citation: ICEBRG Chrome Extensions) Executing browser-based behaviors such as pivoting may require specific process permissions, such as <code>SeDebugPrivilege</code> and/or high-integrity/administrator rights.

Another example involves pivoting browser traffic from the adversary's browser through the user's browser by setting up a proxy which will redirect web traffic. This does not alter the user's traffic in any way, and the proxy connection can be severed as soon as the browser is closed. The adversary assumes the security context of whichever browser process the proxy is injected into. Browsers typically create a new process for each tab that is opened and permissions and certificates are separated accordingly. With these permissions, an adversary could potentially browse to any resource on an intranet, such as [Sharepoint](https://attack.mitre.org/techniques/T1213/002) or webmail, that is accessible through the browser and which the browser has sufficient permissions. Browser pivoting may also bypass security provided by 2-factor authentication.(Citation: cobaltstrike manual)

## Affected platforms

Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-593 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1185 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
