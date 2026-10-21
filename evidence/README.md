# Resume demonstration evidence

`resume-demo-walkthrough.html` is a self-playing, four-scene walkthrough of the real controlled pause/resume run. Open it in a browser and use Play or the arrow buttons to navigate.

## Live synthetic run

- Input: `resume_demo_recording_input.csv`, 30 synthetic reviews, separate from the assignment dataset.
- The runner used two workers and paused cleanly after saving four completed enrichments, with no in-flight calls.
- Resuming with the same settings added 26 enrichments and made zero new enrichment calls for the four already completed IDs. Three verification calls then completed.
- Final result: 30 completed, zero failed. All 33 calls returned usage. Known Jev input-token cost was USD 0.001617126.
- Before/after ID snapshots are `resume_demo_checkpoint_before.json` and `resume_demo_checkpoint_after.json`; machine-readable verification is in `resume_demo_report.json`.
- The sample records and compact call log are copied into this folder as `resume_demo_records.jsonl` and `resume_demo_calls.jsonl` so the evidence is included in the repository. Full output files are also under `../outputs/custom-2e1f03ced275/`; the full call ledger is in `../cost/pilot_calls.jsonl` under the run ID in the report.

This was a real controlled interruption/resume using Jev; no 100,000-row output was changed. The 62-second screen recording is saved as `resume_demo_recording.mp4` (SHA-256 `032FC98AA6E77933AE77918B3C6679B90FBFB818BBB83D6BCF89DA4A1ACBFB2F`). The before/after snapshots, input, results, compact calls and report all refer to the same recorded run. The HTML is a companion visual summary.

To make another recording, open PowerShell in the project folder and run `./evidence/record_live_resume_demo.ps1`. The script generates a fresh synthetic input and does a no-call preflight first. When prompted, start Windows screen recording with **Win+Alt+R**, press Enter to run and pause, show the saved checkpoint, press Enter to resume, then stop recording when the script says it is complete. The script's maximum API reserve is printed before the first paid request and remains subject to the project's $8 local cap.
