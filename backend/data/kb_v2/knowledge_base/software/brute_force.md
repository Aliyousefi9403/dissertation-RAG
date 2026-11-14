# Brute Force

## Metadata

- Attack key: `brute_force`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-112`
- ATT&CK ID: `T1110`

## Attack description

In this attack, some asset (information, functionality, identity, etc.) is protected by a finite secret value. The attacker attempts to gain access to this asset by using trial-and-error to exhaustively explore all the possible secret values in the hope of finding the secret (or a value that is functionally equivalent) that will unlock the asset.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Determine secret testing procedure: </b>Determine how a potential guess of the secret may be tested. This may be accomplished by comparing some manipulation of the secret to a known value, use of the secret to manipulate some known set of data and determining if the result displays specific characteristics (for example, turning cryptotext into plaintext), or by submitting the secret to some external authority and having the external authority respond as to whether the value was the correct secret. Ideally, the attacker will want to determine the correctness of their guess independently since involvement of an external authority is usually slower and can provide an indication to the defender that a brute-force attack is being attempted.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Determine if there is a way to parallelize the attack. Most brute force attacks can take advantage of parallel techniques by dividing the search space among available resources, thus dividing the average time to success by the number of resources available. If there is a single choke point, such as a need to check answers with an external authority, the attackers' position is significantly degraded.</td></tr></tbody></table><li> <p> <b>Reduce search space: </b>Find ways to reduce the secret space. The smaller the attacker can make the space they need to search for the secret value, the greater their chances for success. There are a great many ways in which the search space may be reduced.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>If possible, determine how the secret was selected. If the secret was determined algorithmically (such as by a random number generator) the algorithm may have patterns or dependencies that reduce the size of the secret space. If the secret was created by a human, behavioral factors may, if not completely reduce the space, make some types of secrets more likely than others. (For example, humans may use the same secrets in multiple places or use secrets that look or sound familiar for ease of recall.)</td></tr><tr><td>If the secret was chosen algorithmically, cryptanalysis can be applied to the algorithm to discover patterns in this algorithm. (This is true even if the secret is not used in cryptography.) Periodicity, the need for seed values, or weaknesses in the generator all can result in a significantly smaller secret space.</td></tr><tr><td>If the secret was chosen by a person, social engineering and simple espionage can indicate patterns in their secret selection. If old secrets can be learned (and a target may feel they have little need to protect a secret that has been replaced) hints as to their selection preferences can be gleaned. These can include character substitutions a target employs, patterns in sources (dates, famous phrases, music lyrics, family members, etc.). Once these patterns have been determined, the initial efforts of a brute-force attack can focus on these areas.</td></tr><tr><td>Some algorithmic techniques for secret selection may leave indicators that can be tested for relatively easily and which could then be used to eliminate large areas of the search space for consideration. For example, it may be possible to determine that a secret does or does not start with a given character after a relatively small number of tests. Alternatively, it might be possible to discover the length of the secret relatively easily. These discoveries would significantly reduce the search space, thus increasing speed with which the attacker discovers the secret.</td></tr></tbody></table><li> <p> <b>Expand victory conditions: </b>It is sometimes possible to expand victory conditions. For example, the attacker might not need to know the exact secret but simply needs a value that produces the same result using a one-way function. While doing this does not reduce the size of the search space, the presence of multiple victory conditions does reduce the likely amount of time that the attacker will need to explore the space before finding a workable value.</p></li></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Gather information so attack can be performed independently.: </b>If possible, gather the necessary information so a successful search can be determined without consultation of an external authority. This can be accomplished by capturing cryptotext (if the goal is decoding the text) or the encrypted password dictionary (if the goal is learning passwords).</p></li></ol></div>

## Prerequisites

The attacker must be able to determine when they have successfully guessed the secret. As such, one-time pads are immune to this type of attack since there is no way to determine when a guess is correct.

## Required resources

None: No specialized resources are required to execute this type of attack. Ultimately, the speed with which an attacker discovers a secret is directly proportional to the computational resources the attacker has at their disposal. This attack method is resource expensive: having large amounts of computational power do not guarantee timely success, but having only minimal resources makes the problem intractable against all but the weakest secret selection procedures.

## Required skills

Low: The attack simply requires basic scripting ability to automate the exploration of the search space. More sophisticated attackers may be able to use more advanced methods to reduce the search space and increase the speed with which the secret is located.

## Consequences

Access_Control: ['Gain Privileges']; Authorization: ['Gain Privileges']; Confidentiality: ['Read Data', 'Gain Privileges']

## ATT&CK adversary context

**Technique:** Brute Force

Adversaries may use brute force techniques to gain access to accounts when passwords are unknown or when password hashes are obtained.(Citation: TrendMicro Pawn Storm Dec 2020) Without knowledge of the password for an account or set of accounts, an adversary may systematically guess the password using a repetitive or iterative mechanism.(Citation: Dragos Crashoverride 2018) Brute forcing passwords can take place via interaction with a service that will check the validity of those credentials or offline against previously acquired credential data, such as password hashes.

Brute forcing credentials may take place at various points during a breach. For example, adversaries may attempt to brute force access to [Valid Accounts](https://attack.mitre.org/techniques/T1078) within a victim environment leveraging knowledge gathered from other post-compromise behaviors such as [OS Credential Dumping](https://attack.mitre.org/techniques/T1003), [Account Discovery](https://attack.mitre.org/techniques/T1087), or [Password Policy Discovery](https://attack.mitre.org/techniques/T1201). Adversaries may also combine brute forcing activity with behaviors such as [External Remote Services](https://attack.mitre.org/techniques/T1133) as part of Initial Access. 

If an adversary guesses the correct password but fails to login to a compromised account due to location-based conditional access policies, they may change their infrastructure until they match the victim’s location and therefore bypass those policies.(Citation: ReliaQuest Health Care Social Engineering Campaign 2024)

## Affected platforms

- Containers
- ESXi
- IaaS
- Identity Provider
- Linux
- macOS
- Network Devices
- Office Suite
- SaaS
- Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-112 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1110 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
