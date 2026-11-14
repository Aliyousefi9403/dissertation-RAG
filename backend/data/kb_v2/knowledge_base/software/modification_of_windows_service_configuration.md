# Modification of Windows Service Configuration

## Metadata

- Attack key: `modification_of_windows_service_configuration`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-478`
- ATT&CK ID: `T1574.011`

## Attack description

An adversary exploits a weakness in access control to modify the execution parameters of a Windows service. The goal of this attack is to execute a malicious binary in place of an existing service.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Determine target system: </b>The adversary must first determine the system they wish to modify the registry of. This needs to be a windows machine as this attack only works on the windows registry.</p></li></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Gain access to the system: </b>The adversary needs to gain access to the system in some way so that they can modify the windows registry.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Gain physical access to a system either through shoulder surfing a password or accessing a system that is left unlocked.</td></tr><tr><td>Gain remote access to a system through a variety of means.</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Modify windows registry: </b>The adversary will modify the windows registry by changing the configuration settings for a service. Specifically, the adversary will change the path settings to define a path to a malicious binary to be executed.</p></li></ol></div>

## Prerequisites

The adversary must have the capability to write to the Windows Registry on the targeted system.

## Required resources

None: No specialized resources are required to execute this type of attack.

## Consequences

Integrity: ['Execute Unauthorized Commands (By altering specific configuration settings for the service, the adversary could run arbitrary code to be executed.)']

## ATT&CK adversary context

**Technique:** Services Registry Permissions Weakness

Adversaries may execute their own malicious payloads by hijacking the Registry entries used by services. Flaws in the permissions for Registry keys related to services can allow adversaries to redirect the originally specified executable to one they control, launching their own code when a service starts. Windows stores local service configuration information in the Registry under <code>HKLM\SYSTEM\CurrentControlSet\Services</code>. The information stored under a service's Registry keys can be manipulated to modify a service's execution parameters through tools such as the service controller, sc.exe,  [PowerShell](https://attack.mitre.org/techniques/T1059/001), or [Reg](https://attack.mitre.org/software/S0075). Access to Registry keys is controlled through access control lists and user permissions. (Citation: Registry Key Security)(Citation: malware_hides_service)

If the permissions for users and groups are not properly set and allow access to the Registry keys for a service, adversaries may change the service's binPath/ImagePath to point to a different executable under their control. When the service starts or is restarted, the adversary-controlled program will execute, allowing the adversary to establish persistence and/or privilege escalation to the account context the service is set to execute under (local/domain account, SYSTEM, LocalService, or NetworkService).

Adversaries may also alter other Registry keys in the service’s Registry tree. For example, the <code>FailureCommand</code> key may be changed so that the service is executed in an elevated context anytime the service fails or is intentionally corrupted.(Citation: Kansa Service related collectors)(Citation: Tweet Registry Perms Weakness)

The <code>Performance</code> key contains the name of a driver service's performance DLL and the names of several exported functions in the DLL.(Citation: microsoft_services_registry_tree) If the <code>Performance</code> key is not already present and if an adversary-controlled user has the <code>Create Subkey</code> permission, adversaries may create the <code>Performance</code> key in the service’s Registry tree to point to a malicious DLL.(Citation: insecure_reg_perms)

Adversaries may also add the <code>Parameters</code> key, which can reference malicious drivers file paths. This technique has been identified to be a method of abuse by configuring DLL file paths within the <code>Parameters</code> key of a given services registry configuration. By placing and configuring the <code>Parameters</code> key to reference a malicious DLL, adversaries can ensure that their code is loaded persistently whenever the associated service or library is invoked.

For example, the registry path(Citation: MDSec) <code>HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\WinSock2\Parameters</code>(Citation: hexacorn)(Citation: gendigital) contains the <code>AutodiaDLL</code> value, which specifies the DLL to be loaded for autodial funcitionality. An adversary could set the <code>AutodiaDLL</code> to point to a hijacked or malicious DLL:

<code>"AutodialDLL"="c:\temp\foo.dll"</code>

This ensures persistence, as it causes the DLL (in this case, foo.dll) to be loaded each time the Winsock 2 library is invoked.

## Affected platforms

Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-478 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1574.011 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
