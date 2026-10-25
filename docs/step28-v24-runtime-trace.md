# Step 28 — v23 opening acceptance and v24 read-only FCEUX token tracer

**2026-10-25. v23 boot and English opening confirmed by the user; Bank 6 runtime decoder not yet confirmed.**

## What the user's result establishes

The user reports: **“It works it still show the english intro.”** This confirms that the v23 experimental patch boots and preserves the English opening. It does **not** prove that the modified Bank 6 `$D0–$EC` token dispatcher was invoked: the already translated opening belongs to Bank 8.

Preserve v1.7 as the last fully visual-accepted English intro/menu reference. Treat v23 as **partial FCEUX PASS** (boot + English intro), with Bank 6 runtime token fidelity still pending.

## v24 diagnostic

`tools/fceux_v24_token_trace.lua` is a **read-only Lua execution tracer**, built against the official FCEUX `memory.registerexec`, `memory.readbyte`, `memory.getregister`, `emu.frameadvance`, `gui.text` APIs. It does not patch ROM/RAM, drive the controller, load a savestate, or save gameplay.

The script compares the fixed-bank CPU instruction bytes at `$EDE7` and `$EDFD` against the exact v23 edits before monitoring execution. It displays and logs:

- Main text dispatcher executed at `$EDE7`.
- Token candidate byte in `$D0–$EC`.
- Call to token index resolver at `$EDFD`.
- Call to secondary text reader at `$EE2C`.
- Unexpected high input bytes in `$ED–$FF`.

It periodically writes `SquareTomSawyer_v24_token_trace.txt` in FCEUX's working directory if writable, with full-screen counters as fallback.

## One short FCEUX test, no sequential playthrough

1. Keep the **same v23 standalone IPS** and clean Japanese ROM that display the English intro. **No new IPS** is supplied.
2. In FCEUX's Lua Script window, load `tools/fceux_v24_token_trace.lua`.
3. Confirm `v23 ROM: YES` on screen. Finish the English intro, then trigger one easily accessible **LOOK or nearby NPC response**.
4. Share the generated text report or a screenshot showing the counters.

A zero token count after a Bank 6 text read is **inconclusive**, not a bug: that particular line may not contain a shared token. An actual token plus resolver/secondary reader counts establishes code-path execution, not necessarily rendered-text accuracy. The observer cannot silently prove compatibility for all 479 records.

## Source and test status

The unchanged v23 project has 95 passing local tests. Three new source-free v24 tests confirm that the observer uses only read APIs, includes exact decoder fingerprints, and successfully writes an expected trace under a simulated Lua/FCEUX callback environment. The integrated snapshot passes **98 local tests**. **The actual v24 script has not yet been tested in the user's running FCEUX.**

## Next

If the trace sees the native token/resolver path, proceed to extending the codec beyond its 29 existing shared phrases, with verified control-code handling and storage/mapper access for a larger dictionary. The script-first translation path remains **dump → edit/approve TSV → encode/compress → bulk patch → selective runtime QA**, never sequential translation through gameplay.
