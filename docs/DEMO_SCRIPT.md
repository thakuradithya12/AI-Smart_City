# 10-minute complaint lifecycle demo

Use a fresh, disposable local database after `docker compose up --build -d db web`, `docker compose exec web python manage.py migrate`, and `docker compose exec web python manage.py seed_demo`. The seed creates phone-based accounts with random passwords and prints each new password once. Keep those passwords in private rehearsal notes; do not paste them into this file, commit them, or reuse them outside this local demo.

These are synthetic local login numbers. They are not verified by SMS, should not be used to contact anyone, and are not production credentials. The seeded ward is a synthetic square around Hyderabad and is not pilot geography. Use a pin within that demo ward; the center is 17.3850 latitude, 78.4867 longitude.

| Role | Demo login phone |
|---|---|
| Citizen | `+919876502201` |
| Triage reviewer | `+919876502202` |
| Department official | `+919876502203` |
| Field worker | `+919876502204` |
| Supervisor | `+919876502205` |
| Admin | `+919876502206` |

Use separate browser profiles or sign out between roles. Start a timer and follow the steps in order.

| Time | Role | Walkthrough |
|---|---|---|
| 0:00–1:30 | Citizen | Sign in with the citizen phone and its seed-generated password. Submit a pothole report with a short description, a local photo, consent, and a confirmed map pin inside the demo ward. Note the displayed complaint ID and open its timeline. The new report moves to triage without an AI decision. |
| 1:30–3:00 | Triage reviewer | Sign in as triage reviewer. Open the triage queue, find the noted complaint ID, review its category and location, then route it to the demo department. Point out that routing is a human decision. |
| 3:00–4:15 | Department official | Sign in as department official. Open the department inbox, acknowledge the routed complaint, and assign it to the demo field worker. |
| 4:15–6:30 | Field worker | Sign in as field worker. Open the assigned task, start work, upload a before photo and an after photo with a short completion note, then submit the work-done claim. Show that this is awaiting verification rather than closed. |
| 6:30–8:00 | Supervisor | Sign in as supervisor. Open the item awaiting verification, review the evidence and claim, and verify the fix. Confirm that the status becomes `verified_closed` and the verification actor is separate from the field worker's claim. |
| 8:00–9:00 | Admin | Sign in as admin. Open the audit workspace and find the complaint's sequence of events. Show the actor/action history and, if useful, demonstrate the CSV export without editing any audit row. |
| 9:00–10:00 | Facilitator | Return to the citizen timeline and recap submission, routing, assignment, claim, and independent verification. Remind viewers that this local demo has no live pilot geography, AI decision, or official integration. |

If an account already existed before this seed run, the command skips it and does not reveal or reset its password. For a fresh local rehearsal database, rerun the seed and keep the printed passwords securely; otherwise reset the relevant demo account password locally with `python manage.py changepassword <phone-number>` inside the web container.

After rehearsal, remove the disposable demo database or disable/rotate the demo accounts. Never seed these accounts on production.
