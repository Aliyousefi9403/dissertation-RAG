# Subverting Environment Variable Values

## Metadata

- Attack key: `subverting_environment_variable_values`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-13`
- ATT&CK ID: `T1562.003`

## Attack description

The adversary directly or indirectly modifies environment variables used by or controlling the target software. The adversary's goal is to cause the target software to deviate from its expected operation in a manner that benefits the adversary.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Probe target application: </b>The adversary first probes the target application to determine important information about the target. This information could include types software used, software versions, what user input the application consumes, and so on. Most importantly, the adversary tries to determine what environment variables might be used by the underlying software, or even the application itself.</p></li></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Find user-controlled environment variables: </b>Using the information found by probing the application, the adversary attempts to manipulate any user-controlled environment variables they have found are being used by the application, or suspect are being used by the application, and observe the effects of these changes. If the adversary notices any significant changes to the application, they will know that a certain environment variable is important to the application behavior and indicates a possible attack vector.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Alter known environment variables such as "$PATH", "$HOSTNAME", or "LD_LIBRARY_PATH" and see if application behavior changes.</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Manipulate user-controlled environment variables: </b>The adversary manipulates the found environment variable(s) to abuse the normal flow of processes or to gain access to privileged resources.</p></li></ol></div>

## Prerequisites

- An environment variable is accessible to the user.
- An environment variable used by the application can be tainted with user supplied data.
- Input data used in an environment variable is not validated properly.
- The variables encapsulation is not done properly. For instance setting a variable as public in a class makes it visible and an adversary may attempt to manipulate that variable.

## Required skills

High: Some more advanced attacks may require knowledge about protocols and probing technique which help controlling a variable. The malicious user may try to understand the authentication mechanism in order to defeat it.; Low: In a web based scenario, the client controls the data that it submitted to the server. So anybody can try to send malicious data and try to bypass the authentication mechanism.

## Consequences

Access_Control: ['Bypass Protection Mechanism']; Accountability: ['Hide Activities']; Authorization: ['Bypass Protection Mechanism']; Availability: ['Execute Unauthorized Commands (Run Arbitrary Code)', 'Unreliable Execution']; Confidentiality: ['Execute Unauthorized Commands (Run Arbitrary Code)', 'Bypass Protection Mechanism', 'Read Data']; Integrity: ['Execute Unauthorized Commands (Run Arbitrary Code)']

## ATT&CK adversary context

**Technique:** Impair Command History Logging

Adversaries may impair command history logging to hide commands they run on a compromised system. Various command interpreters keep track of the commands users type in their terminal so that users can retrace what they've done. 

On Linux and macOS, command history is tracked in a file pointed to by the environment variable <code>HISTFILE</code>. When a user logs off a system, this information is flushed to a file in the user's home directory called <code>~/.bash_history</code>. The <code>HISTCONTROL</code> environment variable keeps track of what should be saved by the <code>history</code> command and eventually into the <code>~/.bash_history</code> file when a user logs out. <code>HISTCONTROL</code> does not exist by default on macOS, but can be set by the user and will be respected. The `HISTFILE` environment variable is also used in some ESXi systems.(Citation: Google Cloud Threat Intelligence ESXi VIBs 2022)

Adversaries may clear the history environment variable (<code>unset HISTFILE</code>) or set the command history size to zero (<code>export HISTFILESIZE=0</code>) to prevent logging of commands. Additionally, <code>HISTCONTROL</code> can be configured to ignore commands that start with a space by simply setting it to "ignorespace". <code>HISTCONTROL</code> can also be set to ignore duplicate commands by setting it to "ignoredups". In some Linux systems, this is set by default to "ignoreboth" which covers both of the previous examples. This means that “ ls” will not be saved, but “ls” would be saved by history. Adversaries can abuse this to operate without leaving traces by simply prepending a space to all of their terminal commands. 

On Windows systems, the <code>PSReadLine</code> module tracks commands used in all PowerShell sessions and writes them to a file (<code>$env:APPDATA\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt</code> by default). Adversaries may change where these logs are saved using <code>Set-PSReadLineOption -HistorySavePath {File Path}</code>. This will cause <code>ConsoleHost_history.txt</code> to stop receiving logs. Additionally, it is possible to turn off logging to this file using the PowerShell command <code>Set-PSReadlineOption -HistorySaveStyle SaveNothing</code>.(Citation: Microsoft PowerShell Command History)(Citation: Sophos PowerShell command audit)(Citation: Sophos PowerShell Command History Forensics)

Adversaries may also leverage a [Network Device CLI](https://attack.mitre.org/techniques/T1059/008) on network devices to disable historical command logging (e.g. <code>no logging</code>).

## Affected platforms

- ESXi
- Linux
- macOS
- Network Devices
- Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-13 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1562.003 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
