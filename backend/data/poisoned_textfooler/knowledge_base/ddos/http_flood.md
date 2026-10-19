# HTTP Flood


## Metadata


- Attack key: `http_flood`
- Category: `ddos`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-488`
- ATT&CK ID: `T1499.003`


## Attack description


An adversary may execute a flooding attack using the URL memos with the intent to deny legitimate users access to a service by consuming resources at the implementation layer such as web services and their infrastructure. These attacks use legitimate session-based WWW GET requests designed to consume large amounts of a server's resources. Since these are legitimate sessions this attack is very difficult to detect.

## Prerequisites


This type of an attack requires the ability to generate a large amount of URL traffic to send to a target server.

## ATT&CK adversary context


**Technique:** Application Exhaustion Flood Adversaries may target resource intensive features of applications to cause a denial of service (DoS), denying availability to those applications. For example, specific features in online apps may be highly resource intensive. Repeated requests to those features may be able to exhaust system resources and deny access to the application or the server itself.(Citation: Arbor AnnualDoSreport Jan 2018)

## Affected platforms


- Windows
- IaaS
- Linux
- macOS


## Detection indicators


Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.


## Prevention and mitigation


Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.


## Source mapping


- CAPEC: CAPEC-488 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1499.003 — role: application_exhaustion_context; required
- CAPEC: CAPEC-469 — role: http_dos_context; optional
- OWASP: Denial of Service Cheat Sheet — role: prevention_and_mitigation; optional


## Provenance


- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
