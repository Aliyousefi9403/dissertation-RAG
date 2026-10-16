# SQL Injection


## Metadata


- Attack key: `sql_injection`
- Category: `injection`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-66`
- ATT&CK ID: `T1190`


## Attack description


This attack exploits target software that constructs SQL statements based on user input. An attacker crafts input strings so that when the target software constructs SQL statements based on the input, the resulting SQL statement performs actions other than those the application intended. SQL Injection results from failure of the application to appropriately validate input.


## Execution flow


<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Survey application: </b>The attacker first takes an inventory of the functionality exposed by the application.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Spider web sites for all available links</td></tr><tr><td>Sniff network communications with application using a utility such as WireShark.</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Determine user-controllable input susceptible to injection: </b>Determine the user-controllable input susceptible to injection. For each user-controllable input that the attacker suspects is vulnerable to SQL injection, attempt to inject characters that have special meaning in SQL (such as a single quote character, a double quote character, two hyphens, a parenthesis, etc.). The goal is to create a SQL query with an invalid syntax.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Use web browser to inject input through text fields or through HTTP GET parameters.</td></tr><tr><td>Use a web application debugging tool such as Tamper Data, TamperIE, WebScarab,etc. to modify HTTP POST parameters, hidden fields, non-freeform fields, etc.</td></tr><tr><td>Use network-level packet injection tools such as netcat to inject input</td></tr><tr><td>Use modified client (modified by reverse engineering) to inject input.</td></tr></tbody></table><li> <p> <b>Experiment with SQL Injection vulnerabilities: </b>After determining that a given input is vulnerable to SQL Injection, hypothesize what the underlying query looks like. Iteratively try to add logic to the query to extract information from the database, or to modify or delete information in the database.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Use public resources such as "SQL Injection Cheat Sheet" at http://ferruh.mavituna.com/makale/sql-injection-cheatsheet/, and try different approaches for adding logic to SQL queries.</td></tr><tr><td>Add logic to query, and use detailed error messages from the server to debug the query. For example, if adding a single quote to a query causes an error message, try : "' OR 1=1; --", or something else that would syntactically complete a hypothesized query. Iteratively refine the query.</td></tr><tr><td>Use "Blind SQL Injection" techniques to extract information about the database schema.</td></tr><tr><td>If a denial of service attack is the goal, try stacking queries. This does not work on all platforms (most notably, it does not work on Oracle or MySQL). Examples of inputs to try include: "'; DROP TABLE SYSOBJECTS; --" and "'); DROP TABLE SYSOBJECTS; --". These particular queries will likely not work because the SYSOBJECTS table is generally protected.</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Exploit SQL Injection vulnerability: </b>After refining and adding various logic to SQL queries, craft and execute the underlying SQL query that will be used to attack the target system. The goal is to reveal, modify, and/or delete database data, using the knowledge obtained in the previous step. This could entail crafting and executing multiple SQL queries if a denial of service attack is the intent.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Craft and Execute underlying SQL query</td></tr></tbody></table></ol></div>


## Prerequisites


- SQL queries used by the application to store, retrieve or modify data.
- User-controllable input that is not properly validated by the application as part of SQL queries.


## Required resources


None: No specialized resources are required to execute this type of attack.


## Required skills


Low: It is fairly simple for someone with basic SQL knowledge to perform SQL injection, in general. In certain instances, however, specific knowledge of the database employed may be required.


## Consequences


Access_Control: ['Gain Privileges']; Authorization: ['Gain Privileges']; Availability: ['Execute Unauthorized Commands (Run Arbitrary Code)']; Confidentiality: ['Read Data', 'Execute Unauthorized Commands (Run Arbitrary Code)', 'Gain Privileges']; Integrity: ['Modify Data', 'Execute Unauthorized Commands (Run Arbitrary Code)']

## ATT&CK adversary context


**Technique:** Exploit Public-Facing Application Adversaries may attempt to exploit a weakness in an Internet-facing host or system to initially access a network. The weakness in the system can be a software bug, a temporary glitch, or a misconfiguration. Exploited applications are often websites/web servers, but can also include databases (like SQL), standard services (like SMB or SSH), network device administration and management protocols (like SNMP and Smart Install), and any other system with Internet-accessible open sockets.(Citation: NVD CVE-2016-6662)(Citation: CIS Multiple SMB Vulnerabilities)(Citation: US-CERT TA18-106A Network Infrastructure Devices 2018)(Citation: Cisco Blog Legacy Device Attacks)(Citation: NVD CVE-2014-7169) On ESXi infrastructure, adversaries may exploit exposed OpenSLP services; they may alternatively exploit exposed VMware vCenter servers.(Citation: Recorded Future ESXiArgs Ransomware 2023)(Citation: Ars Technica VMWare Code Execution Vulnerability 2021) Depending on the flaw being exploited, this may also involve [Exploitation for Stealth](https://attack.mitre.org/techniques/T1211) or [Exploitation for Client Execution](https://attack.mitre.org/techniques/T1203). If an application is hosted on cloud-based infrastructure and/or is containerized, then exploiting it may lead to compromise of the underlying instance or container. This can allow an adversary a path to access the cloud or container APIs (e.g., via the [Cloud Instance Metadata API](https://attack.mitre.org/techniques/T1552/005)), exploit container host access via [Escape to Host](https://attack.mitre.org/techniques/T1611), or take advantage of weak identity and access management policies. Adversaries may also exploit edge network infrastructure and related appliances, specifically targeting devices that do not support robust host-based defenses.(Citation: Mandiant Fortinet Zero Day)(Citation: Wired Russia Cyberwar) For websites and databases, the OWASP top 10 and CWE top 25 highlight the most common web-based vulnerabilities.(Citation: OWASP Top 10)(Citation: CWE top 25)

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


- CAPEC: CAPEC-66 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1190 — role: adversary_context; required
- MITRE_ATTACK_ICS: T0819 — role: iot_ics_context; optional
- OWASP: SQL Injection Prevention Cheat Sheet — role: prevention_and_mitigation; required
- NIST: NIST SP 800-53 SI-10 — role: input_validation_guidance; optional


## Provenance


- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
