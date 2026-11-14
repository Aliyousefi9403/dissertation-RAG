# System Location Discovery

## Metadata

- Attack key: `system_location_discovery`
- Category: `communications`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-694`
- ATT&CK ID: `T1614`

## Attack description

<xhtml:p>An adversary collects information about the target system in an attempt to identify the system's geographical location.</xhtml:p>
            <xhtml:p>Information gathered could include keyboard layout, system language, and timezone. This information may benefit an adversary in confirming the desired target and/or tailoring further attacks.</xhtml:p>

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>System Locale Information Discovery: </b>The adversary examines system information from various sources such as registry and native API functions and correlates the gathered information to infer the geographical location of the target system</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Registry Query: Query the registry key HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\ContentIndex\Language\Language_Dialect on Windows to obtain system language, Computer\HKEY_CURRENT_USER\Keyboard Layout\Preload to obtain the hexadecimal language IDs of the current user's preloaded keyboard layouts, and Computer\HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\TimeZoneInformation to obtain the system timezone configuration</td></tr><tr><td>Native API Requests: Parse the outputs of Windows API functions GetTimeZoneInformation, GetUserDefaultUILanguage, GetSystemDefaultUILanguage, GetKeyboardLayoutList and GetUserDefaultLangID to obtain information about languages, keyboard layouts, and timezones installed on the system or on macOS or Linux systems, query locale to obtain the $LANG environment variable and view keyboard layout information or use timeanddatectl status to show the system clock settings.</td></tr><tr><td>Read Configuration Files: For macOS and Linux-based systems, view the /etc/vconsole.conf file to get information about the keyboard mapping and console font.</td></tr></tbody></table></ol></div>

## Prerequisites

The adversary must have some level of access to the system and have a basic understanding of the operating system in order to query the appropriate sources for relevant information.

## Required resources

The adversary requires access to the target's operating system tools to query relevant system information. On windows, registry queries can be conducted with powershell, wmi, or regedit. On Linux or macOS, queries can be performed with through a shell.

## Required skills

Low: The adversary must know how to query various system sources of information respective of the system's operating system to obtain the relevant information.

## Consequences

Confidentiality: ['Read Data']

## ATT&CK adversary context

**Technique:** System Location Discovery


Adversaries may gather information in an attempt to calculate the geographical location of a victim host. Adversaries may use the information from [System Location Discovery](https://attack.mitre.org/techniques/T1614) during automated discovery to shape follow-on behaviors, including whether or not the adversary fully infects the target and/or attempts specific actions.

Adversaries may attempt to infer the location of a system using various system checks, such as time zone, keyboard layout, and/or language settings.(Citation: FBI Ragnar Locker 2020)(Citation: Sophos Geolocation 2016)(Citation: Bleepingcomputer RAT malware 2020) Windows API functions such as <code>GetLocaleInfoW</code> can also be used to determine the locale of the host.(Citation: FBI Ragnar Locker 2020) In cloud environments, an instance's availability zone may also be discovered by accessing the instance metadata service from the instance.(Citation: AWS Instance Identity Documents)(Citation: Microsoft Azure Instance Metadata 2021)

Adversaries may also attempt to infer the location of a victim host using IP addressing, such as via online geolocation IP-lookup services.(Citation: Securelist Trasparent Tribe 2020)(Citation: Sophos Geolocation 2016)

## Affected platforms

- IaaS
- Linux
- macOS
- Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-694 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1614 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
