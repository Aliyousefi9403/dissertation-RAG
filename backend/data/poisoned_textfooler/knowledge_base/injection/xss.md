# Cross-Site Scripting


## Metadata


- Attack key: `xss`
- Category: `injection`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-63`
- ATT&CK ID: `T1190`


## Attack description


An adversary embeds evil scenarios in substances that determination es served to cyberspace browsers. The goal of the strikes is for the sights software, the client-side navigators, to perform the command with the consuming' prefer level. An attack of this sorting exploits a programs' malfunctions that are established on by activation remote arrange to execute code and alphabet. Cyberspace browsers, for cas, enjoy some streamlined safety inspections in placements, but if a distant bomber is entitles to undertake scenarios (through substation them in to user-generated substances like journal panels) then these inspections may be neglected. Others, these blasts are too complex for an conclude tenant to sensing.

## Execution flow


<h2> Performed Flow </h2><cur><h3>Examined</h3><co><i> <p> <b>Examined the request for user-controllable inlet: </c>Employment a navigators or an automated equipment, an intruder continue all citizen bonds and measurements on a www situ. They recorder all the bond, the methods, the source consulted and all other potential entry-points for the website claim.</phosphorus></le><tables><tbody><tr><guzman>Techniques</guzman></si><rr><geneva>Use a spidering apparatus to observing and recordings all liens and scrutinize the online page to discoveries admission dot. Obtain specialist observing of any bond that consisted parameters in the HTTP.</dt></rt><rt><cr>Via a proxy equipment to tape all bonds sailed during a guide traversal of the website application.</ct></rr><rt><ct>Via a navigator to manually explore the website and analyze how it is constructed. Much browsers' plugins are available to facilitate the analysis or automate the discovery.</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Probe identified potential entry points for XSS vulnerability: </b>The attacker uses the entry points gathered in the "Explore" phase as a target list and injects various common script payloads to determine if an entry point actually represents a vulnerability and to characterize the extent to which the vulnerability can be exploited.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Use a list of XSS probe strings to inject script in parameters of known URLs. If possible, the probe strings contain a unique identifier.</td></tr><tr><td>Use a proxy tool to record results of manual input of XSS probes in known URLs.</td></tr><tr><td>Use a list of XSS probe strings to inject script into UI entry fields. If possible, the probe strings contain a unique identifier.</td></tr><tr><td>Use a list of XSS probe strings to inject script into resources accessed by the application. If possible, the probe strings contain a unique identifier.</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Steal session IDs, credentials, page content, etc.: </b>As the attacker succeeds in exploiting the vulnerability, they can choose to steal user's credentials in order to reuse or to analyze them later on.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Develop malicious JavaScript that is injected through vectors identified during the Experiment Phase and loaded by the victim's browser and sends document information to the attacker.</td></tr><tr><td>Develop malicious JavaScript that injected through vectors identified during the Experiment Phase and takes commands from an attacker's server and then causes the browser to execute appropriately.</td></tr></tbody></table><li> <p> <b>Forceful browsing: </b>When the attacker targets the current application or another one (through CSRF vulnerabilities), the user will then be the one who perform the attacks without being aware of it. These attacks are mostly targeting application logic flaws, but it can also be used to create a widespread attack against a particular website on the user's current network (Internet or not).</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Develop malicious JavaScript that is injected through vectors identified during the Experiment Phase and loaded by the victim's browser and performs actions on the same web site</td></tr><tr><td>Develop malicious JavaScript that injected through vectors identified during the Experiment Phase and takes commands from an attacker's server and then causes the browser to execute request to other web sites (especially the web applications that have CSRF vulnerabilities).</td></tr></tbody></table><li> <p> <b>Content spoofing: </b>By manipulating the content, the attacker targets the information that the user would like to get from the website.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Develop malicious JavaScript that is injected through vectors identified during the Experiment Phase and loaded by the victim's browser and exposes attacker-modified invalid information to the user on the current web page.</td></tr></tbody></table></ol></div>

## Prerequisites


Blanco receiver sw must es a providers that permission scripting notification from outermost diners, such as a JavaScript-enabled Nets Navigator.

## Required resources


Ability to deploy a custom hostile service for access by targeted clients. Ability to communicate synchronously or asynchronously with consumer machine.

## Required skills


High: Exploiting a client side vulnerability to inject malicious scripts into the browser's executable process.; Low: To achieve a redirection and use of less trusted source, an attacker can simply place a script in bulletin board, blog, wiki, or other user-generated content site that are echoed back to other client machines.


## Consequences


Readiness: ['Implementation Undeclared Commanding (Run Erratic Encoded)']; Confidentiality: ['Execute Unlawful Commanding (Run Reckless Cypher)', 'Read Stats']; Integrity: ['Execute Unauthorized Commands (Run Arbitrary Keyed)', 'Modify Data']

## ATT&CK adversary context


**Technique:** Exploit Public-Facing Application

Adversaries may attempt to exploit a weakness in an Internet-facing host or system to initially access a network. The weakness in the system can be a software bug, a temporary glitch, or a misconfiguration.

Exploited applications are often websites/web servers, but can also include databases (like SQL), standard services (like SMB or SSH), network device administration and management protocols (like SNMP and Smart Install), and any other system with Internet-accessible open sockets.(Citation: NVD CVE-2016-6662)(Citation: CIS Multiple SMB Vulnerabilities)(Citation: US-CERT TA18-106A Network Infrastructure Devices 2018)(Citation: Cisco Blog Legacy Device Attacks)(Citation: NVD CVE-2014-7169) On ESXi infrastructure, adversaries may exploit exposed OpenSLP services; they may alternatively exploit exposed VMware vCenter servers.(Citation: Recorded Future ESXiArgs Ransomware 2023)(Citation: Ars Technica VMWare Code Execution Vulnerability 2021) Depending on the flaw being exploited, this may also involve [Exploitation for Stealth](https://attack.mitre.org/techniques/T1211) or [Exploitation for Client Execution](https://attack.mitre.org/techniques/T1203).

If an application is hosted on cloud-based infrastructure and/or is containerized, then exploiting it may lead to compromise of the underlying instance or container. This can allow an adversary a path to access the cloud or container APIs (e.g., via the [Cloud Instance Metadata API](https://attack.mitre.org/techniques/T1552/005)), exploit container host access via [Escape to Host](https://attack.mitre.org/techniques/T1611), or take advantage of weak identity and access management policies.

Adversaries may also exploit edge network infrastructure and related appliances, specifically targeting devices that do not support robust host-based defenses.(Citation: Mandiant Fortinet Zero Day)(Citation: Wired Russia Cyberwar)

For websites and databases, the OWASP top 10 and CWE top 25 highlight the most common web-based vulnerabilities.(Citation: OWASP Top 10)(Citation: CWE top 25)


## Affected platforms


- Containers
- ESXi
- IaaS
- Linux
- macOS
- Network Devices
- Windows


## Detection indicators


Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.


## Prevention and mitigation


Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.


## Source mapping


- CAPEC: CAPEC-63 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1190 — role: public_facing_application_context; optional
- OWASP: Cross Site Scripting Prevention Cheat Sheet — role: prevention_and_mitigation; required
- OWASP: Web Security Testing Guide - Testing for XSS — role: detection_and_testing; required


## Provenance


- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
