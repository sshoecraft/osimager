---
name: feedback-agreement-is-not-a-go-ahead
description: A user's design observation ("-c would have to be a directory") is not a go-ahead to implement it; wait for an explicit instruction before editing.
metadata:
  type: feedback
tags: [feedback, scope, wait-for-instruction]
---

When the user states how something *should* work, they are thinking out loud about the design, not asking for it to be built. Confirm the point and stop; edit only when they say to.

What happened: while `-c/--config` was an open question ("make it work or remove it?"), the user said "the whole problem with -c is you would have to specify the entire config directory ... NOT a file". Claude agreed and immediately started editing `core.py`. The user stopped it with "i dont remember telling you to do it", and the edit was reverted.

The same session had already shown this pattern: the user asks or reasons about something, and the right response is an answer, not a change.
