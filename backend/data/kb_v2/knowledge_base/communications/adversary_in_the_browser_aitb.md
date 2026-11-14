# Adversary in the Browser (AiTB)

## Metadata

- Attack key: `adversary_in_the_browser_aitb`
- Category: `communications`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-662`
- ATT&CK ID: `T1185`

## Attack description

<xhtml:p>An adversary exploits security vulnerabilities or inherent functionalities of a web browser, in order to manipulate traffic between two endpoints.</xhtml:p>

## Execution flow

<h2> Execution Flow </h2><div><h3>Experiment</h3><ol><li> <p>The adversary tricks the victim into installing the Trojan Horse malware onto their system.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Conduct phishing attacks, drive-by malware installations, or masquerade malicious browser extensions as being legitimate.</td></tr></tbody></table><li> <p>The adversary inserts themself into the communication channel initially acting as a routing proxy between the two targeted components.</p></li></ol></div><div><h3>Exploit</h3><ol><li> <p>The adversary observes, filters, or alters passed data of their choosing to gain access to sensitive information or to manipulate the actions of the two target components for their own purposes.</p></li></ol></div>

## Prerequisites

- The adversary must install or convince a user to install a Trojan.
- There are two components communicating with each other.
- An attacker is able to identify the nature and mechanism of communication between the two target components.
- Strong mutual authentication is not used between the two target components yielding opportunity for adversarial interposition.
- For browser pivoting, the SeDebugPrivilege and a high-integrity process must both exist to execute this attack.

## Required skills

Medium: Tricking the victim into installing the Trojan is often the most difficult aspect of this attack. Afterwards, the remainder of this attack is fairly trivial.

## Consequences

Access_Control: ['Gain Privileges']; Authorization: ['Gain Privileges']; Confidentiality: ['Gain Privileges', 'Read Data']; Integrity: ['Modify Data']

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

- CAPEC: CAPEC-662 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1185 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
