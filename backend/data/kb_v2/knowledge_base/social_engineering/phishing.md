# Phishing

## Metadata

- Attack key: `phishing`
- Category: `social_engineering`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-98`
- ATT&CK ID: `T1566`

## Attack description

Phishing is a social engineering technique where an attacker masquerades as a legitimate entity with which the victim might do business in order to prompt the user to reveal some confidential information (very frequently authentication credentials) that can later be used by an attacker. Phishing is essentially a form of information gathering or "fishing" for information.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Obtain domain name and certificate to spoof legitimate site: </b>This optional step can be used to help the attacker impersonate the legitimate site more convincingly. The attacker can use homograph attacks to convince users that they are using the legitimate website. Note that this step is not required for phishing attacks, and many phishing attacks simply supply URLs containing an IP address and no SSL certificate.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Optionally obtain a domain name that visually looks similar to the legitimate site's domain name. An example is www.paypaI.com vs. www.paypal.com (the first one contains a capital i, instead of a lower case L)</td></tr><tr><td>Optionally obtain a legitimate SSL certificate for the new domain name.</td></tr></tbody></table><li> <p> <b>Explore legitimate website and create duplicate: </b>An attacker creates a website (optionally at a URL that looks similar to the original URL) that closely resembles the website that they are trying to impersonate. That website will typically have a login form for the victim to put in their authentication credentials. There can be different variations on a theme here.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Use spidering software to get copy of web pages on legitimate site.</td></tr><tr><td>Manually save copies of required web pages from legitimate site.</td></tr><tr><td>Create new web pages that have the legitimate site's look and feel, but contain completely new content.</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Convince user to enter sensitive information on attacker's site.: </b>An attacker sends an e-mail to the victim that has some sort of a call to action to get the user to click on the link included in the e-mail (which takes the victim to attacker's website) and log in. The key is to get the victim to believe that the e-mail is coming from a legitimate entity with which the victim does business and that the website pointed to by the URL in the e-mail is the legitimate website. A call to action will usually need to sound legitimate and urgent enough to prompt action from the user.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Send the user a message from a spoofed legitimate-looking e-mail address that asks the user to click on the included link.</td></tr><tr><td>Place phishing link in post to online forum.</td></tr></tbody></table><li> <p> <b>Use stolen credentials to log into legitimate site: </b>Once the attacker captures some sensitive information through phishing (login credentials, credit card information, etc.) the attacker can leverage this information. For instance, the attacker can use the victim's login credentials to log into their bank account and transfer money to an account of their choice.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Log in to the legitimate site using another user's supplied credentials</td></tr></tbody></table></ol></div>

## Prerequisites

- An attacker needs to have a way to initiate contact with the victim. Typically that will happen through e-mail.
- An attacker needs to correctly guess the entity with which the victim does business and impersonate it. Most of the time phishers just use the most popular banks/services and send out their "hooks" to many potential victims.
- An attacker needs to have a sufficiently compelling call to action to prompt the user to take action.
- The replicated website needs to look extremely similar to the original website and the URL used to get to that website needs to look like the real URL of the said business entity.

## Required resources

Some web development tools to put up a fake website.

## Required skills

Medium: Basic knowledge about websites: obtaining them, designing and implementing them, etc.

## Consequences

Access_Control: ['Gain Privileges']; Authorization: ['Gain Privileges']; Confidentiality: ['Gain Privileges', 'Read Data']; Integrity: ['Modify Data']

## ATT&CK adversary context

**Technique:** Phishing

Adversaries may send phishing messages to gain access to victim systems. All forms of phishing are electronically delivered social engineering. Phishing can be targeted, known as spearphishing. In spearphishing, a specific individual, company, or industry will be targeted by the adversary. More generally, adversaries can conduct non-targeted phishing, such as in mass malware spam campaigns.

Adversaries may send victims emails containing malicious attachments or links, typically to execute malicious code on victim systems. Phishing may also be conducted via third-party services, like social media platforms. Phishing may also involve social engineering techniques, such as posing as a trusted source, as well as evasive techniques such as removing or manipulating emails or metadata/headers from compromised accounts being abused to send messages (e.g., [Email Hiding Rules](https://attack.mitre.org/techniques/T1564/008)).(Citation: Microsoft OAuth Spam 2022)(Citation: Palo Alto Unit 42 VBA Infostealer 2014) Another way to accomplish this is by [Email Spoofing](https://attack.mitre.org/techniques/T1684/002)(Citation: Proofpoint-spoof) the identity of the sender, which can be used to fool both the human recipient as well as automated security tools,(Citation: cyberproof-double-bounce) or by including the intended target as a party to an existing email thread that includes malicious files or links (i.e., "thread hijacking").(Citation: phishing-krebs)

Victims may also receive phishing messages that instruct them to call a phone number where they are directed to visit a malicious URL, download malware,(Citation: sygnia Luna Month)(Citation: CISA Remote Monitoring and Management Software) or install adversary-accessible remote management tools onto their computer (i.e., [User Execution](https://attack.mitre.org/techniques/T1204)).(Citation: Unit42 Luna Moth)

## Affected platforms

- Identity Provider
- Linux
- macOS
- Office Suite
- SaaS
- Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-98 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1566 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
