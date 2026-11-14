# Key Negotiation of Bluetooth Attack (KNOB)

## Metadata

- Attack key: `key_negotiation_of_bluetooth_attack_knob`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-668`
- ATT&CK ID: `T1565.002`

## Attack description

An adversary can exploit a flaw in Bluetooth key negotiation allowing them to decrypt information sent between two devices communicating via Bluetooth. The adversary uses an Adversary in the Middle setup to modify packets sent between the two devices during the authentication process, specifically the entropy bits. Knowledge of the number of entropy bits will allow the attacker to easily decrypt information passing over the line of communication.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Discovery: </b>Using an established Person in the Middle setup, search for Bluetooth devices beginning the authentication process.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Use packet capture tools.</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Change the entropy bits: </b>Upon recieving the initial key negotiation packet from the master, the adversary modifies the entropy bits requested to 1 to allow for easy decryption before it is forwarded.</p></li></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Capture and decrypt data: </b>Once the entropy of encryption is known, the adversary can capture data and then decrypt on their device.</p></li></ol></div>

## Prerequisites

Person in the Middle network setup.

## Required resources

Bluetooth adapter, packet capturing capabilities.

## Required skills

Medium: Ability to modify packets.

## Consequences

Access_Control: ['Bypass Protection Mechanism']; Authorization: ['Bypass Protection Mechanism']; Confidentiality: ['Read Data', 'Bypass Protection Mechanism']; Integrity: ['Modify Data']

## ATT&CK adversary context

**Technique:** Transmitted Data Manipulation

Adversaries may alter data en route to storage or other systems in order to manipulate external outcomes or hide activity, thus threatening the integrity of the data.(Citation: FireEye APT38 Oct 2018)(Citation: DOJ Lazarus Sony 2018) By manipulating transmitted data, adversaries may attempt to affect a business process, organizational understanding, and decision making.

Manipulation may be possible over a network connection or between system processes where there is an opportunity deploy a tool that will intercept and change information. The type of modification and the impact it will have depends on the target transmission mechanism as well as the goals and objectives of the adversary. For complex systems, an adversary would likely need special expertise and possibly access to specialized software related to the system that would typically be gained through a prolonged information gathering campaign in order to have the desired impact.

## Affected platforms

- Linux
- macOS
- Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-668 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1565.002 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
