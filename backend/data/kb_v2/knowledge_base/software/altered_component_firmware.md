# Altered Component Firmware

## Metadata

- Attack key: `altered_component_firmware`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-638`
- ATT&CK ID: `T1542.002`

## Attack description

An adversary exploits systems features and/or improperly protected firmware of hardware components, such as Hard Disk Drives (HDD), with the goal of executing malicious code from within the component's Master Boot Record (MBR). Conducting this type of attack entails the adversary infecting the target with firmware altering malware, using known tools, and a payload. Once this malware is executed, the MBR is modified to include instructions to execute the payload at desired intervals and when the system is booted up. A successful attack will obtain persistence within the victim system even if the operating system is reinstalled and/or if the component is formatted or has its data erased.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Select Target: </b>The adversary searches for a suitable target to attack, such as government and/or private industry organizations.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Conduct reconnaissance to determine potential targets to exploit.</td></tr></tbody></table><li> <p> <b>Identify Components: </b>After selecting a target, the adversary determines whether a vulnerable component, such as a specific make and model of a HDD, is contained within the target system.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>[Remote Access Vector] The adversary gains remote access to the target, typically via additional malware, and explores the system to determine hardware components that are being leveraged.</td></tr><tr><td>[Physical Access Vector] The adversary intercepts components in transit and determines if the component is vulnerable to attack.</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Optional: Create Payload: </b>If not using an already existing payload, the adversary creates their own to be executed at defined intervals and upon system boot processes. This payload may then be tested on the target system or a test system to confirm its functionality.</p></li></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Insert Firmware Altering Malware: </b>Once a vulnerable component has been identified, the adversary leverages known malware tools to infect the component's firmware and drop the payload within the component's MBR. This allows the adversary to maintain persistence on the target and execute the payload without being detected.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>The adversary inserts the firmware altering malware on the target component, via the use of known malware tools.</td></tr><tr><td>[Physical Access Vector] The adversary then sends the component to its original intended destination, where it will be installed onto a victim system.</td></tr></tbody></table></ol></div>

## Prerequisites

- Advanced knowledge about the target component's firmware
- Advanced knowledge about Master Boot Records (MBR)
- Advanced knowledge about tools used to insert firmware altering malware.
- Advanced knowledge about component shipments to the target organization.

## Required resources

- Manufacturer source code for hardware components.
- Malware tools used to insert malware and payload onto target component.
- Either remote or physical access to the target component.

## Required skills

High: Ability to intercept components in transit.; Low: Ability to leverage known malware tools to infect target system and insert firmware altering malware/payload; Medium: Ability to create malicious payload to be executed from MBR.

## Consequences

Access_Control: ['Read Data', 'Modify Data']; Authentication: ['Gain Privileges', 'Execute Unauthorized Commands', 'Bypass Protection Mechanism', 'Hide Activities']; Authorization: ['Gain Privileges', 'Execute Unauthorized Commands', 'Bypass Protection Mechanism', 'Hide Activities']; Confidentiality: ['Read Data', 'Modify Data']

## ATT&CK adversary context

**Technique:** Component Firmware

Adversaries may modify component firmware to persist on systems. Some adversaries may employ sophisticated means to compromise computer components and install malicious firmware that will execute adversary code outside of the operating system and main system firmware or BIOS. This technique may be similar to [System Firmware](https://attack.mitre.org/techniques/T1542/001) but conducted upon other system components/devices that may not have the same capability or level of integrity checking.

Malicious component firmware could provide both a persistent level of access to systems despite potential typical failures to maintain access and hard disk re-images, as well as a way to evade host software-based defenses and integrity checks.

## Affected platforms

- Windows
- Linux
- macOS

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-638 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1542.002 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
