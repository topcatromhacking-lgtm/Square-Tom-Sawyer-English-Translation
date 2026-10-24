# Roadmap

**Verified:** source ROM identity and indexed text inventory; partial Japanese glyph map; first 3 English intro lines rendered in FCEUX; two historical predecessor IPS binaries compared.

**v1.4 — current:** generate 479-record metadata, reconcile external BlackPaladin pointers and English candidates by *exact pointer and text offsets*, flag unmatched/duplicate records, estimate one-byte English text budget and overflow. Private script copies and all local output stay outside Git.

**v1.5:** consolidate a single A–Z/number/punctuation encoder, define and verify control codes, support lossless source roundtrip.

**v1.6:** relocate overflowing records safely within banks; then, only where necessary, implement mapper-safe ROM expansion.

**v1.7:** playable first quest, including menus, battle messages, NPCs and items.

**v2.0 goal:** whole-game translation, full playthrough verification, documentation and standalone patch release.

Do not resume speculative font-loader pointer edits. Do not equate static verification with an FCEUX runtime test.
