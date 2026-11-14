# Collect Data from Clipboard

## Metadata

- Attack key: `collect_data_from_clipboard`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-637`
- ATT&CK ID: `T1115`

## Attack description

The adversary exploits an application that allows for the copying of sensitive data or information by collecting information copied to the clipboard. Data copied to the clipboard can be accessed by other applications, such as malware built to exfiltrate or log clipboard contents on a periodic basis. In this way, the adversary aims to garner information to which they are unauthorized.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Find an application that allows copying sensititve data to clipboad: </b>An adversary first needs to find an application that allows copying and pasting of sensitive information. This could be an application that prints out temporary passwords to the screen, private email addresses, or any other sensitive information or data</p></li></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Target users of the application: </b>An adversary will target users of the application in order to obtain the information in their clipboard on a periodic basic</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Install malware on a user's system designed to log clipboard contents periodically</td></tr><tr><td>Get the user to click on a malicious link that will bring them to an application to log the contents of the clipboard</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Follow-up attack: </b>Use any sensitive information found to carry out a follow-up attack</p></li></ol></div>

## Prerequisites

The adversary must have a means (i.e., a pre-installed tool or background process) by which to collect data from the clipboard and store it. That is, when the target copies data to the clipboard (e.g., to paste into another application), the adversary needs some means of capturing that data in a third location.

## Required skills

High: To deploy a hidden process or malware on the system to automatically collect clipboard data.

## Consequences

Confidentiality: ['Read Data']

## ATT&CK adversary context

**Technique:** Clipboard Data

Adversaries may collect data stored in the clipboard from users copying information within or between applications. 

For example, on Windows adversaries can access clipboard data by using <code>clip.exe</code> or <code>Get-Clipboard</code>.(Citation: MSDN Clipboard)(Citation: clip_win_server)(Citation: CISA_AA21_200B) Additionally, adversaries may monitor then replace users’ clipboard with their data (e.g., [Transmitted Data Manipulation](https://attack.mitre.org/techniques/T1565/002)).(Citation: mining_ruby_reversinglabs)

macOS and Linux also have commands, such as <code>pbpaste</code>, to grab clipboard contents.(Citation: Operating with EmPyre)

## Affected platforms

- Linux
- macOS
- Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-637 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1115 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
