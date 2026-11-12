# Design exercise: IDE settings storage and sync

## Prompt

Design a system that stores settings for an IDE. There are two kinds of entity, **User** and **Team**. A user belongs to a team. A team admin can set team settings, and the server pushes them to every user on the team. Users have their own settings and several devices.

## Questions to cover

- **Versioning:** how do settings versions work? What happens on update? Is the version per key, per document or per scope (user vs team)?
- **Precedence:** how do a team's settings and a user's own settings combine? Which settings can a team lock?
- **Sync:** the server pushes to every device. A client disconnects and reconnects. How do you avoid:
  - lost updates
  - duplicate pushes being applied twice
  - version conflicts, such as two devices editing the same key offline
- **Permissions:** who may modify team settings?

## Checklist (drive the design yourself)

1. Requirements, scale (users, devices, size of settings, update rate) and the read/write ratio.
2. API: `GET /settings?since=version`, `PATCH /settings` with a base version, plus a push channel (WebSocket or SSE).
3. Data model: settings stored per scope, each with a monotonic version. Store a change log, not just the latest snapshot.
4. Resolution: merge team settings and user settings, with locked keys taking priority. Compute the merge on the client or on the server.
5. Reconnect: the client sends its last-seen version, and the server replays the change log from there (or sends a snapshot if the log was compacted). Applying an update must be idempotent by version.
6. Conflicts: last-writer-wins per key with a server timestamp, or a version vector per device. Explain the user experience either way.
7. Bottlenecks and trade-offs: fan-out when a large team pushes, hot teams, push vs poll, and offline-first clients.
