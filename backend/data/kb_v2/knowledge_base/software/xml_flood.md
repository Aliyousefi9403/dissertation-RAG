# XML Flood

## Metadata

- Attack key: `xml_flood`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-528`
- ATT&CK ID: `T1499.002`

## Attack description

An adversary may execute a flooding attack using XML messages with the intent to deny legitimate users access to a web service. These attacks are accomplished by sending a large number of XML based requests and letting the service attempt to parse each one. In many cases this type of an attack will result in a XML Denial of Service (XDoS) due to an application becoming unstable, freezing, or crashing.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Survey the target: </b>Using a browser or an automated tool, an attacker records all instance of web services to process XML requests.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Use an automated tool to record all instances of URLs to process XML requests.</td></tr><tr><td>Use a browser to manually explore the website and analyze how the application processes XML requests.</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p>An adversary crafts input data that may have an adverse effect on the operation of the web service when the XML data sent to the service.</p></li></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Launch a resource depletion attack: </b>The attacker delivers a large number of XML messages to the target URLs found in the explore phase at a sufficiently rapid rate. It causes denial of service to the target application.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Send a large number of crafted XML messages to the target URL.</td></tr></tbody></table></ol></div>

## Prerequisites

- The target must receive and process XML transactions.
- An adverssary must possess the ability to generate a large amount of XML based messages to send to the target service.

## Required skills

Low: Denial of service

## Consequences

Availability: ['Resource Consumption']

## ATT&CK adversary context

**Technique:** Service Exhaustion Flood

Adversaries may target the different network services provided by systems to conduct a denial of service (DoS). Adversaries often target the availability of DNS and web services, however others have been targeted as well.(Citation: Arbor AnnualDoSreport Jan 2018) Web server software can be attacked through a variety of means, some of which apply generally while others are specific to the software being used to provide the service.

One example of this type of attack is known as a simple HTTP flood, where an adversary sends a large number of HTTP requests to a web server to overwhelm it and/or an application that runs on top of it. This flood relies on raw volume to accomplish the objective, exhausting any of the various resources required by the victim software to provide the service.(Citation: Cloudflare HTTPflood)

Another variation, known as a SSL renegotiation attack, takes advantage of a protocol feature in SSL/TLS. The SSL/TLS protocol suite includes mechanisms for the client and server to agree on an encryption algorithm to use for subsequent secure connections. If SSL renegotiation is enabled, a request can be made for renegotiation of the crypto algorithm. In a renegotiation attack, the adversary establishes a SSL/TLS connection and then proceeds to make a series of renegotiation requests. Because the cryptographic renegotiation has a meaningful cost in computation cycles, this can cause an impact to the availability of the service when done in volume.(Citation: Arbor SSLDoS April 2012)

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

- CAPEC: CAPEC-528 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1499.002 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
