# Break-glass runbook (Work Zone)

This document travels with the code. The sealed envelope in the safe holds the
break-glass superuser password plus a printed copy of the "Custodian card" below.

## 1. Creation ceremony (once)
1. Owner creates the Django superuser on her own machine (`createsuperuser`).
2. Superuser creates the 2 master users (panel `/master/users/` or shell).
3. Write the superuser password on paper, seal the envelope, store in the safe.
4. Never use the superuser for daily ops again.

## 2. Custodian card (for non-technical custodians)
> "If the owner asks for the envelope, hand it over and call [technician name/phone].
> Say exactly: 'Work Zone break-glass, envelope opened on [date]'.
> Do nothing else. Do not photograph or copy the password."

## 3. Recovery when both masters are lost
1. Open the envelope, log into Django admin or shell as superuser.
2. Reset the masters (`/api/master/users/reset-request/` or `set_password`).
3. Verify both masters log in.
4. Rotate the superuser password the same day, reseal a new envelope.
5. Record everything in the audit log (actions are auto-logged).

## 4. Offboarding a master
1. Revoke all sessions (`/api/master/sessions/revoke/`).
2. Deactivate the user.
3. Remove company assignments.
4. Rotate any shared secret they knew.

## 5. Rules
- Any superuser login outside ceremony/recovery = incident + rotation.
- Nobody resets their own password via another master (endpoint forbids self-reset).
- This runbook is reviewed whenever the company grows (quorum, TOTP, HSM then).
