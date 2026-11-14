# Inclusion of Code in Existing Process

## Metadata

- Attack key: `inclusion_of_code_in_existing_process`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-640`
- ATT&CK ID: `T1505.005`

## Attack description

The adversary takes advantage of a bug in an application failing to verify the integrity of the running process to execute arbitrary code in the address space of a separate live process. The adversary could use running code in the context of another process to try to access process's memory, system/network resources, etc. The goal of this attack is to evade detection defenses and escalate privileges by masking the malicious code under an existing legitimate process. Examples of approaches include but not limited to: dynamic-link library (DLL) injection, portable executable injection, thread execution hijacking, ptrace system calls, VDSO hijacking, function hooking, reflective code loading, and more.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Determine target process: </b>The adversary determines a process with sufficient privileges that they wish to include code into.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>On Windows, use the process explorer's security tab to see if a process is running with administror privileges.</td></tr><tr><td>On Linux, use the ps command to view running processes and pipe the output to a search for a particular user, or the root user.</td></tr></tbody></table></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Attempt to include simple code with known output: </b>The adversary attempts to include very simple code into the existing process to determine if the code inclusion worked. The code will differ based on the approach used to include code into an existing process.</p></li></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Include arbitrary code into existing process: </b>Once an adversary has determined that including code into the existing process is possible, they will include code for a targeted purpose, such as accessing that process's memory.</p></li></ol></div>

## Prerequisites

The targeted application fails to verify the integrity of the running process that allows an adversary to execute arbitrary code.

## Required skills

High: Knowledge of how to load malicious code into the memory space of a running process, as well as the ability to have the running process execute this code. For example, with DLL injection, the adversary must know how to load a DLL into the memory space of another running process, and cause this process to execute the code inside of the DLL.

## Consequences

Confidentiality: ['Execute Unauthorized Commands', 'Read Data']; Integrity: ['Execute Unauthorized Commands', 'Read Data']

## ATT&CK adversary context

**Technique:** Terminal Services DLL

Adversaries may abuse components of Terminal Services to enable persistent access to systems. Microsoft Terminal Services, renamed to Remote Desktop Services in some Windows Server OSs as of 2022, enable remote terminal connections to hosts. Terminal Services allows servers to transmit a full, interactive, graphical user interface to clients via RDP.(Citation: Microsoft Remote Desktop Services)

[Windows Service](https://attack.mitre.org/techniques/T1543/003)s that are run as a "generic" process (ex: <code>svchost.exe</code>) load the service's DLL file, the location of which is stored in a Registry entry named <code>ServiceDll</code>.(Citation: Microsoft System Services Fundamentals) The <code>termsrv.dll</code> file, typically stored in `%SystemRoot%\System32\`, is the default <code>ServiceDll</code> value for Terminal Services in `HKLM\System\CurrentControlSet\services\TermService\Parameters\`.

Adversaries may modify and/or replace the Terminal Services DLL to enable persistent access to victimized hosts.(Citation: James TermServ DLL) Modifications to this DLL could be done to execute arbitrary payloads (while also potentially preserving normal <code>termsrv.dll</code> functionality) as well as to simply enable abusable features of Terminal Services. For example, an adversary may enable features such as concurrent [Remote Desktop Protocol](https://attack.mitre.org/techniques/T1021/001) sessions by either patching the <code>termsrv.dll</code> file or modifying the <code>ServiceDll</code> value to point to a DLL that provides increased RDP functionality.(Citation: Windows OS Hub RDP)(Citation: RDPWrap Github) On a non-server Windows OS this increased functionality may also enable an adversary to avoid Terminal Services prompts that warn/log out users of a system when a new RDP session is created.

## Affected platforms

Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-640 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1505.005 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
