# Directory Indexing

## Metadata

- Attack key: `directory_indexing`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-127`
- ATT&CK ID: `T1083`

## Attack description

An adversary crafts a request to a target that results in the target listing/indexing the content of a directory as output. One common method of triggering directory contents as output is to construct a request containing a path that terminates in a directory name rather than a file name since many applications are configured to provide a list of the directory's contents when such a request is received. An adversary can use this to explore the directory tree on a target as well as learn the names of files. This can often end up revealing test files, backup files, temporary files, hidden files, configuration files, user accounts, script contents, as well as naming conventions, all of which can be used by an attacker to mount additional attacks.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Directory Discovery: </b>Use a method, either manual, scripted, or automated to discover the directories on the server by making requests for directories that may possibly exist. During this phase the adversary is less concerned with whether a directory can be accessed or indexed and more focused on simply discovering what directories do exist on the target.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Send requests to the web server for common directory names</td></tr><tr><td>If directories are discovered that are native to a server type further refine the directory search to include directories usually present on those types of servers.</td></tr><tr><td>Search for uncommon or potentially user created directories that may be present.</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Iteratively explore directory/file structures: </b>The adversary attempts to access the discovered directories that allow access and may attempt to bypass server or application level ACLs by using manual or automated methods</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Use a scanner tool to dynamically add directories/files to include their scan based upon data obtained in initial probes.</td></tr><tr><td>Use a browser to manually explore the website by issuing a request ending the URL in a slash '/'.</td></tr><tr><td>Attempt to bypass ACLs on directories by using methods that known to work against some server types by appending data to the directory request. For instance, appending a Null byte to the end of the request which may cause an ACL to fail and allow access.</td></tr><tr><td>Sequentially request a list of common base files to each directory discovered.</td></tr><tr><td>Try multiple fuzzing techniques to list directory contents for directories that will not reveal their contents with a "/" request</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Read directories or files which are not intended for public viewing.: </b>The adversary attempts to access the discovered directories that allow access and may attempt to bypass server or application level ACLs by using manual or automated methods</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Try multiple exploit techniques to list directory contents for directories that will not reveal their contents with a "/" request</td></tr><tr><td>Try other known exploits to elevate privileges sufficient to bypass protected directories.</td></tr><tr><td>List the files in the directory by issuing a request with the URL ending in a "/" slash.</td></tr><tr><td>Access the files via direct URL and capture contents.</td></tr><tr><td>Attempt to bypass ACLs on directories by using methods that are known to work against some server types by appending data to the directory request. For instance, appending a Null byte to the end of the request which may cause an ACL to fail and allow access.</td></tr><tr><td>Sequentially request a list of common base files to each directory discovered.</td></tr></tbody></table></ol></div>

## Prerequisites

- The target must be misconfigured to return a list of a directory's content when it receives a request that ends in a directory name rather than a file name.
- The adversary must be able to control the path that is requested of the target.
- The administrator must have failed to properly configure an ACL or has associated an overly permissive ACL with a particular directory.
- The server version or patch level must not inherently prevent known directory listing attacks from working.

## Required resources

Ability to send HTTP requests to a web application.

## Required skills

High: To bypass the access control of the directory of listings; Low: To issue the request to URL without given a specific file name

## Consequences

Confidentiality: ['Read Data (Information Leakage)']

## ATT&CK adversary context

**Technique:** File and Directory Discovery

Adversaries may enumerate files and directories or may search in specific locations of a host or network share for certain information within a file system. Adversaries may use the information from [File and Directory Discovery](https://attack.mitre.org/techniques/T1083) during automated discovery to shape follow-on behaviors, including whether or not the adversary fully infects the target and/or attempts specific actions.

Many command shell utilities can be used to obtain this information. Examples include <code>dir</code>, <code>tree</code>, <code>ls</code>, <code>find</code>, and <code>locate</code>.(Citation: Windows Commands JPCERT) Custom tools may also be used to gather file and directory information and interact with the [Native API](https://attack.mitre.org/techniques/T1106). Adversaries may also leverage a [Network Device CLI](https://attack.mitre.org/techniques/T1059/008) on network devices to gather file and directory information (e.g. <code>dir</code>, <code>show flash</code>, and/or <code>nvram</code>).(Citation: US-CERT-TA18-106A)

Some files and directories may require elevated or specific user permissions to access.

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

- CAPEC: CAPEC-127 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1083 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
