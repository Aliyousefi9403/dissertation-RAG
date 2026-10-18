# Cross-Site Scripting


## Metadata


- Attack key: `xss`
- Category: `injection`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-63`
- ATT&CK ID: `T1190`


## Attack description


An adversary embeds malicious scripts in content that will be served to web browsers. The goal of the attack is for the target software, the client-side browser, to execute the script with the users' privilege level. An attack of this type exploits a programs' vulnerabilities that are brought on by allowing remote hosts to execute code and scripts. Web browsers, for example, have some simple security controls in place, but if a remote attacker is allowed to execute scripts (through injecting them in to user-generated content like bulletin boards) then these controls may be bypassed. Further, these attacks are very difficult for an end user to detect.


## Execution flow


<h2> Execution flux </h2><div><h3>Explore</h3><ol><lithium> <phosphorus> <barn>Survey the coating for user-controllable stimulation: </barn>employ a browser or an automated instrument, an attacker observe all public unite and sue on a network site. They tape all the unite, the mold, the resource accessed and all other voltage entry-points for the web coating.</p></li><board><tbody><tr><th>Techniques</th></tr><tr><td>employment a spidering instrument to observe and tape all nexus and canvas the net Page to observe introduction signal. stool special observe of any nexus that include parameters in the URL.</td></tr><tr><td>employment a proxy instrument to record all contact visited during a manual traverse of the vane application.</td></tr><tr><td>Use a browser to manually explore the website and study how it is manufacture. Many browser' plugins are available to facilitate the analysis or automate the breakthrough.</td></tr></tbody></mesa></ol></div><div><h3>Experiment</h3><ol><lithium> <p> <boron>Probe identified potential introduction signal for XSS vulnerability: </b>The aggressor apply the launching signal assemble in the "Explore" phase as a target list and injects various mutual script payloads to specify if an introduction stage actually correspond a vulnerability and to characterize the extent to which the vulnerability can be exploited.</p></li><board><tbody><tr><th>Techniques</th></tr><tr><td>Use a list of XSS probe chain to inject script in parameters of known URLs. If possible, the probe train contain a unique identifier.</td></tr><tr><td>Use a proxy tool to record solvent of manual input of XSS probes in known URLs.</td></tr><tr><td>practice a list of XSS probe strings to inject hand into UI introduction orbit. If possible, the probe twine contain a unique identifier.</td></tr><tr><td>Use a list of XSS probe strings to inject script into resources accessed by the application. If possible, the probe strings contain a unique identifier.</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Steal session IDs, credentials, page content, etc.: </b>As the attacker succeeds in exploiting the vulnerability, they can choose to steal user's credentials in order to reuse or to analyze them later on.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Develop malicious JavaScript that is injected through vectors identified during the Experiment Phase and loaded by the victim's browser and sends document information to the attacker.</td></tr><tr><td>Develop malicious JavaScript that injected through vectors identified during the Experiment Phase and takes commands from an attacker's server and then causes the browser to execute appropriately.</td></tr></tbody></table><li> <p> <b>Forceful browsing: </b>When the attacker targets the current application or another one (through CSRF vulnerabilities), the user will then be the one who perform the attacks without being aware of it. These attacks are mostly targeting application logic flaws, but it can also be used to create a widespread attack against a particular website on the user's current network (Internet or not).</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Develop malicious JavaScript that is injected through vectors identified during the Experiment Phase and loaded by the victim's browser and performs actions on the same web site</td></tr><tr><td>Develop malicious JavaScript that injected through vectors identified during the Experiment Phase and takes commands from an attacker's server and then causes the browser to execute request to other web sites (especially the web applications that have CSRF vulnerabilities).</td></tr></tbody></table><li> <p> <b>Content spoofing: </b>By manipulating the content, the attacker targets the information that the user would like to get from the website.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Develop malicious JavaScript that is injected through vectors identified during the Experiment Phase and loaded by the victim's browser and exposes attacker-modified invalid information to the user on the current web page.</td></tr></tbody></table></ol></div>

## Prerequisites


Target client software must be a client that allows scripting communication from remote hosts, such as a JavaScript-enabled Web Browser.


## Required resources


Ability to deploy a usance hostile service for access by aim node. Ability to commune synchronously or asynchronously with node machine.

## Required skills


High: Exploiting a client side vulnerability to inject malicious scripts into the browser's executable process.; Low: To achieve a redirection and use of less trusted source, an attacker can simply place a script in bulletin board, blog, wiki, or other user-generated content site that are echoed back to other client machines.


## Consequences


accessibility: ['Execute Unauthorized mastery (Run Arbitrary Code)']; Confidentiality: ['accomplish wildcat mastery (Run Arbitrary encrypt)', 'scan information']; Integrity: ['accomplish unauthorised bidding (campaign Arbitrary inscribe)', 'qualify information']

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
