# Redirect Access to Libraries

## Metadata

- Attack key: `redirect_access_to_libraries`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-159`
- ATT&CK ID: `T1574.008`

## Attack description

An adversary exploits a weakness in the way an application searches for external libraries to manipulate the execution flow to point to an adversary supplied library or code base. This pattern of attack allows the adversary to compromise the application or server via the execution of unauthorized code. An application typically makes calls to functions that are a part of libraries external to the application. These libraries may be part of the operating system or they may be third party libraries. If an adversary can redirect an application's attempts to access these libraries to other libraries that the adversary supplies, the adversary will be able to force the targeted application to execute arbitrary code. This is especially dangerous if the targeted application has enhanced privileges. Access can be redirected through a number of techniques, including the use of symbolic links, search path modification, and relative path manipulation.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Identify Target: </b>The adversary identifies the target application and determines what libraries are being used.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Find public source code and identify library dependencies.</td></tr><tr><td>Gain access to the system hosting the application and look for libraries in common locations.</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Deploy Malicious Libraries: </b>The adversary crafts malicious libraries and deploys them on the system where the application is running, or in a remote location that can be loaded by the application.</p></li></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Redirect Library Calls to Malicious Library: </b>Once the malicious library crafted by the adversary is deployed, the adversary will manipulate the flow of the application such that it calls the malicious library. This can be done in a variety of ways based on how the application is loading and calling libraries.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Poison the DNS cache of the system so that it loads a malicious library from a remote location hosted by the adversary instead of the legitimate location</td></tr><tr><td>Create a symlink that tricks the application into thinking that a malicious library is the legitimate library.</td></tr><tr><td>Use DLL side-loading to place a malicious verison of a DLL in the windows directory.</td></tr></tbody></table></ol></div>

## Prerequisites

The target must utilize external libraries and must fail to verify the integrity of these libraries before using them.

## Required skills

High: To reverse engineering the libraries and inject malicious code into the libraries; Low: To modify the entries in the configuration file pointing to malicious libraries; Medium: To force symlink and timing issues for redirecting access to libraries

## Consequences

Access_Control: ['Bypass Protection Mechanism']; Authorization: ['Execute Unauthorized Commands (Run Arbitrary Code)', 'Bypass Protection Mechanism']

## ATT&CK adversary context

**Technique:** Path Interception by Search Order Hijacking

Adversaries may execute their own malicious payloads by hijacking the search order used to load other programs. Because some programs do not call other programs using the full path, adversaries may place their own file in the directory where the calling program is located, causing the operating system to launch their malicious software at the request of the calling program.

Search order hijacking occurs when an adversary abuses the order in which Windows searches for programs that are not given a path. Unlike [DLL](https://attack.mitre.org/techniques/T1574/001) search order hijacking, the search order differs depending on the method that is used to execute the program. (Citation: Microsoft CreateProcess) (Citation: Windows NT Command Shell) (Citation: Microsoft WinExec) However, it is common for Windows to search in the directory of the initiating program before searching through the Windows system directory. An adversary who finds a program vulnerable to search order hijacking (i.e., a program that does not specify the path to an executable) may take advantage of this vulnerability by creating a program named after the improperly specified program and placing it within the initiating program's directory.

For example, "example.exe" runs "cmd.exe" with the command-line argument <code>net user</code>. An adversary may place a program called "net.exe" within the same directory as example.exe, "net.exe" will be run instead of the Windows system utility net. In addition, if an adversary places a program called "net.com" in the same directory as "net.exe", then <code>cmd.exe /C net user</code> will execute "net.com" instead of "net.exe" due to the order of executable extensions defined under PATHEXT. (Citation: Microsoft Environment Property)

Search order hijacking is also a common practice for hijacking DLL loads and is covered in [DLL](https://attack.mitre.org/techniques/T1574/001).

## Affected platforms

Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-159 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1574.008 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
