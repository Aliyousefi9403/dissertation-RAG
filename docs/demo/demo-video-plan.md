# AegisRAG demo video: plan

Handbook §6.3 requirements: about 15 minutes, mandatory (no video = fail), voice-over throughout,
structured as (1) introduction, (2) narrated demo of the software running (about a third),
(3) narrated code walkthrough **in a debugger** (about a third), (4) other outputs and results.
Assume the marker has never seen the project. Put your name in the file name,
e.g. `AliYousefi_AegisRAG_demo.mp4`. Check the audio and that text on screen is readable.

## Running order (target 15:00)

| Time | Part | What is on screen | What you say (key points, in your own words) |
|---|---|---|---|
| 0:00–2:30 | 1 Introduction | Title slide; one diagram of the RAG pipeline (question → retrieve 3 passages → language model → answer) | The problem: a RAG assistant trusts its knowledge base; word-substitution poisoning (PWWS) edits it quietly. The research questions. The idea: detect swapped words with relative entropy (Dr Nikos Komninos's suggestion). What was built. |
| 2:30–3:30 | 1 Introduction | One slide with three example swaps (deny → abnegate, server → waiter, implants malicious software → Engraft Malicious Package) | Why the text still reads normally, and why the swapped words are improbable. |
| 3:30–8:30 | 2 Demo | The web interface, live | See "Demo script" below. |
| 8:30–13:30 | 3 Code walkthrough | VS Code with the Python debugger, stepping through the filter | See "Code walkthrough" below. |
| 13:30–15:00 | 4 Results | Figures 3, 6 and 7, the evidence index page | The main numbers and what they mean; limitations; where everything is. |

## Demo script (about 5 minutes)

Start the app beforehand with `./start-aegisrag.sh` and check the backend shows "online".

1. **Clean mode.** Ask: *"What are the execution steps of a backdoor attack?"* Show the answer and the three source cards.
2. **PWWS Poisoned mode**, same question. Show that the answer changes and the sources contain odd words. Point at one substituted word.
3. **Compare mode.** The two answers side by side; mention the edited-text exposure measure.
4. **Defended mode** (word-frequency filter). Show the shield, a source card's score in bits against the 7.23-bit threshold, and the explanation "abnegate → deny". Say that passages above the threshold were dropped and the next ones used.
5. **Contextual mode** (language-model filter). Same question; show which candidates were dropped and the evidence words.
6. **Evidence check toggle** on a clean answer: claims, verdicts and verified quotations. Say briefly what it is and what the evaluation found (it checks grounding, not completeness).

Tip: record each mode as a separate clip so a slow answer can be cut, and rehearse the questions once beforehand so the answers are cached.

## Code walkthrough (about 5 minutes, in a debugger)

Handbook: "stepping through a section of your code that implements one or more key features, in a debugger, explaining how it works."

Recommended target: the word-frequency filter, `backend/app/defence/entropy_filter.py`, because it is short and every step is visible.

1. Open `backend/tests/test_entropy_filter.py` and run one test under the debugger (VS Code: Testing panel → debug the test), or use a small script that calls `score_text` on a poisoned passage.
2. Breakpoint in `DomainReference.probability`: show q(w) = 0.5 × (count in the *other* documents) + 0.5 × (general-English frequency). Explain leave-one-document-out.
3. Breakpoint in `score_text`, inside the loop: step through one word. Show its WordNet synonyms, the best one under q, and the gap in bits: log₂ q(synonym) − log₂ q(word). Watch "abnegate" get a large gap with "deny" as its likely original.
4. Show `top` (the 3 largest gaps) and the passage score, and compare it with `THRESHOLD_BITS` = 7.2262. Explain that the threshold was fixed once on development documents.
5. Step into `filter_results`: candidates are scored in rank order, flagged ones are skipped, and the first 3 unflagged ones are kept with their verdict attached (this is what the interface displays).
6. Optional (30 seconds): open `contextual_filter.py` and show that the same log-ratio uses a language model's probability of the whole passage instead of q.

## Results segment (about 1.5 minutes)

- PWWS lowers correctness from 0.714 to 0.555, entirely on questions whose source section was attacked.
- Detection: letter-level KL fails (0.33), the synonym gap works (0.82), and the language-model version is best (0.95) and ignores layout (0.53 on the control).
- Live: the contextual filter halves poisoned exposure (41% → 20%) and removes confidently wrong answers, with no measurable cost on clean data, but cannot restore correctness.
- Adaptive attackers: the frequency-matched attacker beats the word-frequency detector but not the contextual one; an attacker that must stay probable under the language model succeeds on 0 of 57 sections.
- Everything is recorded and checked: the evidence index matches every headline number.

## Recording checklist

- Screen recorder: QuickTime (macOS: File → New Screen Recording) or OBS; 1080p; record the window, not the whole desktop.
- Microphone: a headset or the laptop microphone in a quiet room; do a 20-second test first.
- Font size up in VS Code (Cmd + a few times) and browser zoom at 125% so text is readable.
- Close notifications; hide API keys (never show `.env`).
- Edit: cut pauses and waiting time; keep the total near 15 minutes.
- Export as MP4; name it with your name; upload to the correct (non-confidential) submission area.
