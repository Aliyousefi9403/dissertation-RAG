# Embedding Scripts within Scripts

## Metadata

- Attack key: `embedding_scripts_within_scripts`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-19`
- ATT&CK ID: `T1027.009`

## Attack description

An adversary leverages the capability to execute their own script by embedding it within other scripts that the target software is likely to execute due to programs' vulnerabilities that are brought on by allowing remote hosts to execute scripts.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Spider: </b>Using a browser or an automated tool, an adversary records all entry points for inputs that happen to be reflected in a client-side script element. These script elements can be located in the HTML content (head, body, comments), in an HTML tag, XML, CSS, etc.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Use a spidering tool to follow and record all non-static links that are likely to have input parameters (through forms, URL, fragments, etc.) actively used by the Web application.</td></tr><tr><td>Use a proxy tool to record all links visited during a manual traversal of the web application.</td></tr><tr><td>Use a browser to manually explore the website and analyze how it is constructed. Many browsers' plugins are available to facilitate the analysis or automate the discovery.</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Probe identified potential entry points for XSS vulnerability: </b>The adversary uses the entry points gathered in the "Explore" phase as a target list and injects various common script payloads to determine if an entry point actually represents a vulnerability and to characterize the extent to which the vulnerability can be exploited.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Manually inject various script payloads into each identified entry point using a list of common script injection probes that typically work in a client-side script elements context and observe system behavior to determine if script was executed.</td></tr><tr><td>Manually inject various script payloads into each identified entry point using a list of common script injection probes that typically work in a server-side script elements context and observe system behavior to determine if script was executed.</td></tr><tr><td>Use an automated injection attack tool to inject various script payloads into each identified entry point using a list of common script injection probes that typically work in a client-side script elements context and observe system behavior to determine if script was executed.</td></tr><tr><td>Use an automated injection attack tool to inject various script payloads into each identified entry point using a list of common script injection probes that typically work in a server-side script elements context and observe system behavior to determine if script was executed.</td></tr><tr><td>Use a proxy tool to record results of the created requests.</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Steal session IDs, credentials, page content, etc.: </b>As the adversary succeeds in exploiting the vulnerability, they can choose to steal user's credentials in order to reuse or to analyze them later on.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Develop malicious JavaScript that is injected through vectors identified during the Experiment Phase and loaded by the victim's browser and sends document information to the adversary.</td></tr><tr><td>Develop malicious JavaScript that injected through vectors identified during the Experiment Phase and takes commands from an adversary's server and then causes the browser to execute appropriately.</td></tr></tbody></table><li> <p> <b>Forceful browsing: </b>When the adversary targets the current application or another one (through CSRF vulnerabilities), the user will then be the one who perform the attacks without being aware of it. These attacks are mostly targeting application logic flaws, but it can also be used to create a widespread attack against a particular website on the user's current network (Internet or not).</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Develop malicious JavaScript that is injected through vectors identified during the Experiment Phase and loaded by the victim's browser and performs actions on the same web site</td></tr><tr><td>Develop malicious JavaScript that injected through vectors identified during the Experiment Phase and takes commands from an adversary's server and then causes the browser to execute request to other web sites (especially the web applications that have CSRF vulnerabilities).</td></tr></tbody></table><li> <p> <b>Content spoofing: </b>By manipulating the content, the adversary targets the information that the user would like to get from the website.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Develop malicious JavaScript that is injected through vectors identified during the Experiment Phase and loaded by the victim's browser and exposes adversary-modified invalid information to the user on the current web page.</td></tr></tbody></table></ol></div>

## Prerequisites

Target software must be able to execute scripts, and also grant the adversary privilege to write/upload scripts.

## Required skills

Low: To load malicious script into open, e.g. world writable directory; Medium: Executing remote scripts on host and collecting output

## Consequences

Access_Control: ['Gain Privileges']; Authorization: ['Gain Privileges']; Availability: ['Execute Unauthorized Commands (Run Arbitrary Code)']; Confidentiality: ['Execute Unauthorized Commands (Run Arbitrary Code)', 'Gain Privileges']; Integrity: ['Execute Unauthorized Commands (Run Arbitrary Code)']

## ATT&CK adversary context

**Technique:** Embedded Payloads

Adversaries may embed payloads within other files to conceal malicious content from defenses. Otherwise seemingly benign files (such as scripts and executables) may be abused to carry and obfuscate malicious payloads and content. In some cases, embedded payloads may also enable adversaries to [Subvert Trust Controls](https://attack.mitre.org/techniques/T1553) by not impacting execution controls such as digital signatures and notarization tickets.(Citation: Sentinel Labs) 

Adversaries may embed payloads in various file formats to hide payloads.(Citation: Microsoft Learn) This is similar to [Steganography](https://attack.mitre.org/techniques/T1027/003), though does not involve weaving malicious content into specific bytes and patterns related to legitimate digital media formats.(Citation: GitHub PSImage) 

For example, adversaries have been observed embedding payloads within or as an overlay of an otherwise benign binary.(Citation: Securelist Dtrack2) Adversaries have also been observed nesting payloads (such as executables and run-only scripts) inside a file of the same format.(Citation: SentinelLabs reversing run-only applescripts 2021) 

Embedded content may also be used as [Process Injection](https://attack.mitre.org/techniques/T1055) payloads used to infect benign system processes.(Citation: Trend Micro) These embedded then injected payloads may be used as part of the modules of malware designed to provide specific features such as encrypting C2 communications in support of an orchestrator module. For example, an embedded module may be injected into default browsers, allowing adversaries to then communicate via the network.(Citation: Malware Analysis Report ComRAT)

## Affected platforms

- Linux
- macOS
- Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-19 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1027.009 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
