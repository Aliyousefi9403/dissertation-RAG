# Cause Web Server Misclassification

## Metadata

- Attack key: `cause_web_server_misclassification`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-11`
- ATT&CK ID: `T1036.006`

## Attack description

An attack of this type exploits a Web server's decision to take action based on filename or file extension. Because different file types are handled by different server processes, misclassification may force the Web server to take unexpected action, or expected actions in an unexpected sequence. This may cause the server to exhaust resources, supply debug or system data to the attacker, or bind an attacker to a remote process.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Footprint file input vectors: </b>Manually or using an automated tool, an attacker searches for all input locations where a user has control over the filenames or MIME types of files submitted to the web server.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Attacker manually crawls application to identify file inputs</td></tr><tr><td>Attacker uses an automated tool to crawl application identify file inputs</td></tr><tr><td>Attacker manually assesses strength of access control protecting native application files from user control</td></tr><tr><td>Attacker explores potential for submitting files directly to the web server via independently constructed HTTP Requests</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>File misclassification shotgunning: </b>An attacker makes changes to file extensions and MIME types typically processed by web servers and looks for abnormal behavior.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Attacker submits files with switched extensions (e.g. .php on a .jsp file) to web server.</td></tr><tr><td>Attacker adds extra characters (e.g. adding an extra . after the file extension) to filenames of files submitted to web server.</td></tr></tbody></table><li> <p> <b>File misclassification sniping: </b>Understanding how certain file types are processed by web servers, an attacker crafts varying file payloads and modifies their file extension or MIME type to be that of the targeted type to see if the web server is vulnerable to misclassification of that type.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Craft a malicious file payload, modify file extension to the targeted file type and submit it to the web server.</td></tr><tr><td>Craft a malicious file payload, modify its associated MIME type to the targeted file type and submit it to the web server.</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Disclose information: </b>The attacker, by manipulating a file extension or MIME type is able to make the web server return raw information (not executed).</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Manipulate the file names that are explicitly sent to the server.</td></tr><tr><td>Manipulate the MIME sent in order to confuse the web server.</td></tr></tbody></table></ol></div>

## Prerequisites

- Web server software must rely on file name or file extension for processing.
- The attacker must be able to make HTTP requests to the web server.

## Required resources

None: No specialized resources are required to execute this type of attack.

## Required skills

Low: To modify file name or file extension; Medium: To use misclassification to force the Web server to disclose configuration information, source, or binary data

## Consequences

Access_Control: ['Gain Privileges']; Authorization: ['Gain Privileges']; Confidentiality: ['Read Data', 'Gain Privileges']

## ATT&CK adversary context

**Technique:** Space after Filename

Adversaries can hide a program's true filetype by changing the extension of a file. With certain file types (specifically this does not work with .app extensions), appending a space to the end of a filename will change how the file is processed by the operating system.

For example, if there is a Mach-O executable file called <code>evil.bin</code>, when it is double clicked by a user, it will launch Terminal.app and execute. If this file is renamed to <code>evil.txt</code>, then when double clicked by a user, it will launch with the default text editing application (not executing the binary). However, if the file is renamed to <code>evil.txt </code> (note the space at the end), then when double clicked by a user, the true file type is determined by the OS and handled appropriately and the binary will be executed (Citation: Mac Backdoors are back).

Adversaries can use this feature to trick users into double clicking benign-looking files of any format and ultimately executing something malicious.

## Affected platforms

- Linux
- macOS

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-11 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1036.006 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
