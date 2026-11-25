# Privacy notice

## Account information

Citizen accounts store the person's name and unique Indian mobile number. The mobile number is the sign-in identifier and associates reports with the account. The number is not verified by SMS. Citizens may optionally add an email address for notifications and recovery; it is not required for registration. No government identity numbers are collected. Existing staff email identifiers are retained during phone-number migration.

## Complaint information

Reports may include category, optional description, a confirmed location pin, consent timestamp, and private photos. Photos and report details are visible only to people authorized for that complaint. This service is not an emergency service.

## Provisional retention defaults

These owner-provided periods are implementation defaults, not legal advice.

- Closed complaints and their photos: 12 months after closure.
- Rejected or cancelled complaints and their photos: 6 months.
- Inactive accounts: 24 months.
- Deletion requests: handled within 30 days. Audit rows remain for traceability, with the person's name anonymised.

The periods are configurable through settings. When complaint retention expires, the description, landmark, precise location, GPS accuracy, messages and evidence files are removed; the complaint shell and append-only status/audit rows remain. A deletion request anonymises the account's name, phone, email and login identifier while keeping audit actor references pointed at that anonymised account. Older audit entries may preserve message text recorded in their immutable payloads.

The current in-app notice version is `2026-11-25-v1`; each new complaint records the version accepted with its consent timestamp. Signed-in users can export their profile (including phone number), visible complaint history, messages, evidence metadata and audit actions as JSON. Citizens can request account deletion from the privacy page. The scheduled `purge_expired` command processes pending requests and applies the retention cleanup.

## Recovery and notifications

An in-app inbox is available to all roles. Optional citizen email may be used for notifications and recovery. Citizens without email use an admin-assisted reset process. There is no SMS or OTP verification. Optional citizen profile email and admin-assisted recovery are still being implemented.
