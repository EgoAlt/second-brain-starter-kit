# Inbox

Staging area for anything you want ingested into the vault before you have decided where it belongs: PDFs, transcripts, articles, screenshots, quick notes. Drop it here and ask the agent to ingest it.

This folder stays empty most of the time. Nothing here is permanent storage, and nothing here is git-tracked except the two conventions files. A file sitting in `Inbox/` has not been processed yet, by definition.

Routing: the `ingest` skill (`.claude/skills/ingest/SKILL.md`) reads each file in full, discusses what it says and where it should go, then writes it into its home per that folder's `CLAUDE.md`. Substantial source material moves to the destination project's `raw/` folder afterwards; a fully absorbed one-off note is deleted.
