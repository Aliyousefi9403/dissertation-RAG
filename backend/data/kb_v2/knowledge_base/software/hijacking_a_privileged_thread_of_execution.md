# Hijacking a Privileged Thread of Execution

## Metadata

- Attack key: `hijacking_a_privileged_thread_of_execution`
- Category: `software`
- Origin: `clean`
- Document status: `generated_from_authoritative_sources`
- CAPEC ID: `CAPEC-30`
- ATT&CK ID: `T1055.003`

## Attack description

An adversary hijacks a privileged thread of execution by injecting malicious code into a running process. By using a privleged thread to do their bidding, adversaries can evade process-based detection that would stop an attack that creates a new process. This can lead to an adversary gaining access to the process's memory and can also enable elevated privileges. The most common way to perform this attack is by suspending an existing thread and manipulating its memory.

## Execution flow

<h2> Execution Flow </h2><div><h3>Explore</h3><ol><li> <p> <b>Determine target thread: </b>The adversary determines the underlying system thread that is subject to user-control</p></li></ol></div><div><h3>Experiment</h3><ol><li> <p> <b>Gain handle to thread: </b>The adversary then gains a handle to a process thread.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>Use the "OpenThread" API call in Windows on a known thread.</td></tr><tr><td>Cause an exception in a java privileged block public function and catch it, or catch a normal signal. The thread is then hanging and the adversary can attempt to gain a handle to it.</td></tr></tbody></table><li> <p> <b>Alter process memory: </b>Once the adversary has a handle to the target thread, they will suspend the thread and alter the memory using native OS calls.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>On Windows, use "SuspendThread" followed by "VirtualAllocEx", "WriteProcessMemory", and "SetThreadContext".</td></tr></tbody></table></ol></div><div><h3>Exploit</h3><ol><li> <p> <b>Resume thread execution: </b>Once the process memory has been altered to execute malicious code, the thread is then resumed.</p></li><table><tbody><tr><th>Techniques</th></tr><tr><td>On Windows, use "ResumeThread".</td></tr></tbody></table></ol></div>

## Prerequisites

- The application in question employs a threaded model of execution with the threads operating at, or having the ability to switch to, a higher privilege level than normal users
- In order to feasibly execute this class of attacks, the adversary must have the ability to hijack a privileged thread. This ability includes, but is not limited to, modifying environment variables that affect the process the thread belongs to, or calling native OS calls that can suspend and alter process memory. This does not preclude network-based attacks, but makes them conceptually more difficult to identify and execute.

## Required resources

<xhtml:p>None: No specialized resources are required to execute this type of attack. The adversary needs to be able to latch onto a privileged thread.</xhtml:p>
               <xhtml:p>The adversary does, however, need to be able to program, compile, and link to the victim binaries being executed so that it will turn control of a privileged thread over to the adversary's malicious code. This is the case even if the adversary conducts the attack remotely.</xhtml:p>

## Required skills

High: Hijacking a thread involves knowledge of how processes and threads function on the target platform, the design of the target application as well as the ability to identify the primitives to be used or manipulated to hijack the thread.

## Consequences

Access_Control: ['Gain Privileges']; Authorization: ['Gain Privileges']; Availability: ['Execute Unauthorized Commands (Run Arbitrary Code)']; Confidentiality: ['Gain Privileges', 'Execute Unauthorized Commands (Run Arbitrary Code)']; Integrity: ['Execute Unauthorized Commands (Run Arbitrary Code)']

## ATT&CK adversary context

**Technique:** Thread Execution Hijacking

Adversaries may inject malicious code into hijacked processes in order to evade process-based defenses as well as possibly elevate privileges. Thread Execution Hijacking is a method of executing arbitrary code in the address space of a separate live process. 

Thread Execution Hijacking is commonly performed by suspending an existing process then unmapping/hollowing its memory, which can then be replaced with malicious code or the path to a DLL. A handle to an existing victim process is first created with native Windows API calls such as <code>OpenThread</code>. At this point the process can be suspended then written to, realigned to the injected code, and resumed via <code>SuspendThread </code>, <code>VirtualAllocEx</code>, <code>WriteProcessMemory</code>, <code>SetThreadContext</code>, then <code>ResumeThread</code> respectively.(Citation: Elastic Process Injection July 2017)

This is very similar to [Process Hollowing](https://attack.mitre.org/techniques/T1055/012) but targets an existing process rather than creating a process in a suspended state.  

Running code in the context of another process may allow access to the process's memory, system/network resources, and possibly elevated privileges. Execution via Thread Execution Hijacking may also evade detection from security products since the execution is masked under a legitimate process. 

## Affected platforms

Windows

## Detection indicators

Detection content is not automatically inferred. It must be added from an explicitly mapped authoritative detection source and reviewed before experimental use.

## Prevention and mitigation

Mitigation guidance in this document is limited to content explicitly present in the mapped CAPEC or ATT&CK sources. OWASP, NIST, CISA, or other guidance must be ingested separately before being represented as source-derived content.

## Source mapping

- CAPEC: CAPEC-30 — role: attack_mechanism; required
- MITRE_ATTACK_ENTERPRISE: T1055.003 — role: adversary_context; required

## Provenance

- Generated automatically: yes
- LLM-generated technical content: no
- Human review required: yes
- Source text preserved where supplied by STIX: yes
