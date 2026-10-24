# Square no Tom Sawyer: verified ROM structure (2026-10-23)

The supplied ZIP contained exactly one .nes ROM matching CRC32 `AEA5B066` and SHA-1 `f00d2feb353450bd6294bb431a54cee729e56689`.

iNES header: `4E45531A100012000000000000000000`. Mapper 1 / MMC1; 16 × 16 KiB PRG, no separate CHR ROM (CHR RAM), battery-backed memory indicated.

## Pointer inventory

- Main **candidate dialogue** PRG bank: zero-based bank 6, file offsets `0x18010–0x1C00F`.
- `0x18010`: little-endian end pointer `$BFF7`.
- `0x18012`: initial `$FFFF` delimiter.
- `0x18014`: first pointer record, `$8802`.
- `0x18410`: final `$FFFF` delimiter; further `FFFF` padding appears within the pointer area.
- Four groups with **251, 35, 123, and 70** candidate entries.
- Text span `0x18812–0x1C006`, end exclusive `0x1C007`; 14,325 bytes.
- **479** distinct pointer values, increasing and non-overlapping; indexed records 6–173 bytes; each terminates with `00`.

The text span occupies about 87.4% of the bank. Apparent blank bytes elsewhere are **not certified free space**.

## Unverified assumptions

This is static structural analysis, not decoded Japanese text. Some record bytes may encode metadata, controls, or a dictionary, and the actual renderer/pointer dereference must be traced. Other banks can contain menus, battles, name entry, graphics text, or untabulated dialogue. No release or emulator validation has occurred.

A standard MMC1 PRG bank register has four selection bits. Mapping PRG beyond the existing 256 KiB may require a different compatible board configuration (e.g., an additional bank bit), bank relocation within 256 KiB, or a more extensive mapper conversion. All options remain hypotheses until a controlled boot/renderer test.

## References

- https://www.nesdev.org/wiki/Programming_MMC1
- https://nescartdb.com/profile/view/3896/squares-tom-sawyer
- https://community.romhackplaza.org/threads/technical-nes-square-no-tom-sawyer-nes-rom-expansion.4856/
