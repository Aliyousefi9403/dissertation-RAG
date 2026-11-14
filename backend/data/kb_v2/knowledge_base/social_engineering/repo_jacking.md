# Repo Jacking

## Metadata

- Attack key: `repo_jacking`
- Category: `social_engineering`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-695`
- ATT&CK ID: `T1195.001`

## Attack description

<xhtml:p>An adversary takes advantage of the redirect property of directly linked Version Control System (VCS) repositories to trick users into incorporating malicious code into their applications.</xhtml:p>

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Identify target: </b>The adversary must first identify a target repository that is commonly used and whose owner/maintainer has either changed/deleted their username or transferred ownership of the repository and then deleted their account. The target should typically be a popular and widely used package, as to increase the scope of the attack.</p></li></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Recreate initial repository path: </b>The adversary re-registers the account that was renamed/deleted by the target repository's owner/maintainer and recreates the target repository with malicious code intended to exploit an application. These steps may need to happen in reverse (i.e., recreate repository and then rename an existing account to the target account) if protections are in place to prevent repository reuse.</p></li></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Exploit victims: </b>The adversary's malicious code is incorporated into applications that directly reference the initial repository, which further allows the adversary to conduct additional attacks.</p></li></ol></div>

## Prerequisites

- Identification of a popular repository that may be directly referenced in numerous software applications
- A repository owner/maintainer who has recently changed their username or deleted their account

## Required skills

Low: Ability to create malware that can exploit various software applications.

## Consequences

Access_Control: ['Execute Unauthorized Commands', 'Alter Execution Logic', 'Gain Privileges']; Authorization: ['Execute Unauthorized Commands', 'Alter Execution Logic', 'Gain Privileges']; Integrity: ['Read Data', 'Modify Data']

## ATT&CK adversary context

**Technique:** Compromise Software Dependencies and Development Tools

Adversaries may manipulate software dependencies and development tools prior to receipt by a final consumer for the purpose of data or system compromise. Applications often depend on external software to function properly. Popular open source projects that are used as dependencies in many applications, such as pip and NPM packages, may be targeted as a means to add malicious code to users of the dependency.(Citation: Trendmicro NPM Compromise)(Citation: Bitdefender NPM Repositories Compromised 2021)(Citation: MANDVI Malicious npm and PyPI Packages Disguised) This may also include abandoned packages, which in some cases could be re-registered by threat actors after being removed by adversaries.(Citation: The Hacker News PyPi Revival Hijack 2024) Adversaries may also employ "typosquatting" or name-confusion by choosing names similar to existing popular libraries or packages in order to deceive a user.(Citation: Ahmed Backdoors in Python and NPM Packages)(Citation: Meyer PyPI Supply Chain Attack Uncovered)(Citation: Checkmarx-oss-seo)

Additionally, CI/CD pipeline components, such as GitHub Actions, may be targeted in order to gain access to the building, testing, and deployment cycles of an application.(Citation: Unit 42 Palo Alto GitHub Actions Supply Chain Attack 2025) By adding malicious code into a GitHub action, a threat actor may be able to collect runtime credentials (e.g., via [Proc Filesystem](https://attack.mitre.org/techniques/T1003/007)) or insert further malicious components into the build pipelines for a second-order supply chain compromise.(Citation: OWASP CICD-SEC-4) As GitHub Actions are often dependent on other GitHub Actions, threat actors may be able to infect a large number of repositories via the compromise of a single Action.(Citation: Palo Alto Networks GitHub Actions Worm 2023)

Targeting may be specific to a desired victim set or may be distributed to a broad set of consumers but only move on to additional tactics on specific victims. 

## Affected platforms

- Linux
- macOS
- Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-695 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1195.001 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
