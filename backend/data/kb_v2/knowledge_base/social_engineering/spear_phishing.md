# Spear Phishing

## Metadata

- Attack key: `spear_phishing`
- Category: `social_engineering`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-163`
- ATT&CK ID: `T1534`

## Attack description

An adversary targets a specific user or group with a Phishing (CAPEC-98) attack tailored to a category of users in order to have maximum relevance and deceptive capability. Spear Phishing is an enhanced version of the Phishing attack targeted to a specific user or group. The quality of the targeted email is usually enhanced by appearing to come from a known or trusted entity. If the email account of some trusted entity has been compromised the message may be digitally signed. The message will contain information specific to the targeted users that will enhance the probability that they will follow the URL to the compromised site. For example, the message may indicate knowledge of the targets employment, residence, interests, or other information that suggests familiarity. As soon as the user follows the instructions in the message, the attack proceeds as a standard Phishing attack.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Obtain useful contextual detailed information about the targeted user or organization: </b>An adversary collects useful contextual detailed information about the targeted user or organization in order to craft a more deceptive and enticing message to lure the target into responding.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Conduct web searching research of target. See also: CAPEC-118.</td></tr><tr><td>Identify trusted associates, colleagues and friends of target. See also: CAPEC-118.</td></tr><tr><td>Utilize social engineering attack patterns such as Pretexting. See also: CAPEC-407.</td></tr><tr><td>Collect social information via dumpster diving. See also: CAPEC-406.</td></tr><tr><td>Collect social information via traditional sources. See also: CAPEC-118.</td></tr><tr><td>Collect social information via Non-traditional sources. See also: CAPEC-118.</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Optional: Obtain domain name and certificate to spoof legitimate site: </b>This optional step can be used to help the adversary impersonate the legitimate site more convincingly. The adversary can use homograph attacks to convince users that they are using the legitimate website. Note that this step is not required for phishing attacks, and many phishing attacks simply supply URLs containing an IP address and no SSL certificate.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Optionally obtain a domain name that visually looks similar to the legitimate site's domain name. An example is www.paypaI.com vs. www.paypal.com (the first one contains a capital i, instead of a lower case L).</td></tr><tr><td>Optionally obtain a legitimate SSL certificate for the new domain name.</td></tr></tbody></table><li> <p> <b>Optional: Explore legitimate website and create duplicate: </b>An adversary creates a website (optionally at a URL that looks similar to the original URL) that closely resembles the website that they are trying to impersonate. That website will typically have a login form for the victim to put in their authentication credentials. There can be different variations on a theme here.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Use spidering software to get copy of web pages on legitimate site.</td></tr><tr><td>Manually save copies of required web pages from legitimate site.</td></tr><tr><td>Create new web pages that have the legitimate site's look at feel, but contain completely new content.</td></tr></tbody></table><li> <p> <b>Optional: Build variants of the website with very specific user information e.g., living area, etc.: </b>Once the adversary has their website which duplicates a legitimate website, they need to build very custom user related information in it. For example, they could create multiple variants of the website which would target different living area users by providing information such as local news, local weather, etc. so that the user believes this is a new feature from the website.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Integrate localized information in the web pages created to duplicate the original website. Those localized information could be dynamically generated based on unique key or IP address of the future victim.</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Convince user to enter sensitive information on adversary's site.: </b>An adversary sends a message (typically an e-mail) to the victim that has some sort of a call to action to get the user to click on the link included in the e-mail (which takes the victim to adversary's website) and log in. The key is to get the victim to believe that the message is coming from a legitimate entity trusted by the victim or with which the victim or does business and that the website pointed to by the URL in the e-mail is the legitimate website. A call to action will usually need to sound legitimate and urgent enough to prompt action from the user.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Send the user a message from a spoofed legitimate-looking e-mail address that asks the user to click on the included link.</td></tr><tr><td>Place phishing link in post to online forum.</td></tr></tbody></table><li> <p> <b>Use stolen credentials to log into legitimate site: </b>Once the adversary captures some sensitive information through phishing (login credentials, credit card information, etc.) the adversary can leverage this information. For instance, the adversary can use the victim's login credentials to log into their bank account and transfer money to an account of their choice.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Log in to the legitimate site using another user's supplied credentials.</td></tr></tbody></table></ol></div>

## Prerequisites

None. Any user can be targeted by a Spear Phishing attack.

## Required resources

An adversay must have the ability communicate their phishing scheme to the victims (via email, instance message, etc.), as well as a website or other platform for victims to enter personal information into.

## Required skills

Medium: Spear phishing attacks require specific knowledge of the victims being targeted, such as which bank is being used by the victims, or websites they commonly log into (Google, Facebook, etc).

## Consequences

Accountability: ['Gain Privileges (Privilege Escalation)']; Authentication: ['Gain Privileges (Privilege Escalation)']; Authorization: ['Gain Privileges (Privilege Escalation)']; Confidentiality: ['Read Data (Information Leakage)']; Integrity: ['Modify Data (Data Modification)']; Non-Repudiation: ['Gain Privileges (Privilege Escalation)']

## ATT&CK adversary context

**Technique:** Internal Spearphishing

After they already have access to accounts or systems within the environment, adversaries may use internal spearphishing to gain access to additional information or compromise other users within the same organization. Internal spearphishing is multi-staged campaign where a legitimate account is initially compromised either by controlling the user's device or by compromising the account credentials of the user. Adversaries may then attempt to take advantage of the trusted internal account to increase the likelihood of tricking more victims into falling for phish attempts, often incorporating [Impersonation](https://attack.mitre.org/techniques/T1684/001).(Citation: Trend Micro - Int SP)

For example, adversaries may leverage [Spearphishing Attachment](https://attack.mitre.org/techniques/T1566/001) or [Spearphishing Link](https://attack.mitre.org/techniques/T1566/002) as part of internal spearphishing to deliver a payload or redirect to an external site to capture credentials through [Input Capture](https://attack.mitre.org/techniques/T1056) on sites that mimic login interfaces.

Adversaries may also leverage internal chat apps, such as Microsoft Teams, to spread malicious content or engage users in attempts to capture sensitive information and/or credentials.(Citation: Int SP - chat apps)

## Affected platforms

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

- CAPEC: CAPEC-163 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1534 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
