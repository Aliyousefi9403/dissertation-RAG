# Leverage Alternate Encoding

## Metadata

- Attack key: `leverage_alternate_encoding`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-267`
- ATT&CK ID: `T1027`

## Attack description

An adversary leverages the possibility to encode potentially harmful input or content used by applications such that the applications are ineffective at validating this encoding standard.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Survey the application for user-controllable inputs: </b>Using a browser, an automated tool or by inspecting the application, an adversary records all entry points to the application.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Use a spidering tool to follow and record all links and analyze the web pages to find entry points. Make special note of any links that include parameters in the URL.</td></tr><tr><td>Use a proxy tool to record all user input entry points visited during a manual traversal of the web application.</td></tr><tr><td>Use a browser to manually explore the website and analyze how it is constructed. Many browsers' plugins are available to facilitate the analysis or automate the discovery.</td></tr><tr><td>Manually inspect the application to find entry points.</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Probe entry points to locate vulnerabilities: </b>The adversary uses the entry points gathered in the "Explore" phase as a target list and injects various payloads using a variety of different types of encodings to determine if an entry point actually represents a vulnerability with insufficient validation logic and to characterize the extent to which the vulnerability can be exploited.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Try to use different encodings of content in order to bypass validation routines.</td></tr></tbody></table></ol></div>

## Prerequisites

The application's decoder accepts and interprets encoded characters. Data canonicalization, input filtering and validating is not done properly leaving the door open to harmful characters for the target host.

## Required skills

Low: An adversary can inject different representation of a filtered character in a different encoding.; Medium: An adversary may craft subtle encoding of input data by using the knowledge that they have gathered about the target host.

## Consequences

Access_Control: ['Bypass Protection Mechanism']; Accountability: ['Gain Privileges']; Authentication: ['Gain Privileges']; Authorization: ['Execute Unauthorized Commands (Run Arbitrary Code)', 'Gain Privileges', 'Bypass Protection Mechanism']; Availability: ['Unreliable Execution (Denial of Service)', 'Resource Consumption (Denial of Service)']; Confidentiality: ['Read Data']; Integrity: ['Modify Data']; Non-Repudiation: ['Gain Privileges']

## ATT&CK adversary context

**Technique:** Obfuscated Files or Information

Adversaries may attempt to make an executable or file difficult to discover or analyze by encrypting, encoding, or otherwise obfuscating its contents on the system or in transit. This is common behavior that can be used across different platforms and the network to evade defenses. 

Payloads may be compressed, archived, or encrypted in order to avoid detection. These payloads may be used during Initial Access or later to mitigate detection. Sometimes a user's action may be required to open and [Deobfuscate/Decode Files or Information](https://attack.mitre.org/techniques/T1140) for [User Execution](https://attack.mitre.org/techniques/T1204). The user may also be required to input a password to open a password protected compressed/encrypted file that was provided by the adversary.(Citation: Volexity PowerDuke November 2016) Adversaries may also use compressed or archived scripts, such as JavaScript. 

Portions of files can also be encoded to hide the plain-text strings that would otherwise help defenders with discovery.(Citation: Linux/Cdorked.A We Live Security Analysis) Payloads may also be split into separate, seemingly benign files that only reveal malicious functionality when reassembled.(Citation: Carbon Black Obfuscation Sept 2016)

Adversaries may also abuse [Command Obfuscation](https://attack.mitre.org/techniques/T1027/010) to obscure commands executed from payloads or directly via [Command and Scripting Interpreter](https://attack.mitre.org/techniques/T1059). Environment variables, aliases, characters, and other platform/language specific semantics can be used to evade signature based detections and application control mechanisms.(Citation: FireEye Obfuscation June 2017)(Citation: FireEye Revoke-Obfuscation July 2017)(Citation: PaloAlto EncodedCommand March 2017) 

## Affected platforms

- ESXi
- Linux
- macOS
- Network Devices
- Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-267 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1027 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
