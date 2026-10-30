# Contributing to Liger Player

Thanks for helping! Bug reports, ideas and pull requests are all welcome.

## Fix or add a translation

1. Open `js/i18n.js`.
2. Find your language's code: `hi` Hindi, `bn` Bengali, `ta` Tamil, `brx` Bodo, `ks` Kashmiri, `mni` Manipuri, `sat` Santali, and so on.
3. Edit the strings on that line.
   - Keep **exactly the same number of `|` separators**. The app checks the count and falls back to English if it is wrong.
   - The strings follow the order of the keys `K` (in `LIGER_RAW`) and `K2` (in `LIGER_RAW2`), which are listed in `index.html`.
4. For a language that has no line yet (Bodo, Kashmiri, Manipuri, Santali), copy the English line, translate it, and add it under the language's code.
5. In your pull request, say you are a native or fluent speaker and which script you used.

Notes:

- Write the strings as short interface labels, the way a phone or Windows would phrase them.
- Product names stay as they are: **Liger**, **Tigu**, **RGB**.

## Report a broken Live TV channel

Channels come from [iptv-org](https://github.com/iptv-org/iptv). Report dead or wrong links there, so every player that uses the list benefits.

## Code

- The app is a single file, `index.html`, with no build step. Open it in a browser and edit.
- Before opening a pull request, check:
  - Light, dark and system themes all look right.
  - It works at phone width (about 400 px).
  - Reduced-motion mode still works.
