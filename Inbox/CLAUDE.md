Vault-wide drop zone for material that has not been ingested yet. Flat, temporary, usually empty.

## Workflow

1. The owner drops a file here.
2. The agent reads it in full and discusses the key takeaways and the proposed destination before writing anything. Never rewrite the vault from a new source silently.
3. The agent ingests it: creates or updates the notes where the content belongs, following that destination's own `CLAUDE.md`.
4. If the source is substantial reference material worth citing long-term, the original moves into the destination project's `raw/` folder and becomes immutable from then on.
5. If the source was a one-off note fully absorbed in step 3, delete it. `Inbox/` goes back to empty.

## Rules

- Never treat a file here as already processed. If it is here, it has not been triaged.
- No subfolders. This is a flat staging area by design.
- Deferring part of a source is the owner's decision, not the agent's. Surface any deferral in chat and record it where the owner will see it again.

<!-- FILL: any owner-specific ingest preferences (a default project for a source type, a file type you never want archived, a size above which you want a summary first). -->
