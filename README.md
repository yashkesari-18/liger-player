# Liger Player

A free, open-source media player that runs in your browser. It has a clean white or dark gaming look, RGB lighting, free Live TV, and **Tigu**, a 16-bit tiger cub who lives in the grass at the bottom of the screen.

> Two versions live in this repository:
> - **Windows app** (`desktop/`): a native program with no web view, powered by libmpv, so it plays practically any file, like VLC. See [desktop/README.md](desktop/README.md).
> - **Web version** (`index.html`): runs in any browser, hosted free on GitHub Pages.

## Features

- **Plays local files.** Drag and drop video or audio files, or use **Open media**. Supports a queue, shuffle, three repeat modes, A–B loop, frame stepping, and resuming where you left off.
- **Simple mode by default.** About 12 everyday settings are shown first. **Advanced** reveals around 90 more, plus a search box.
- **Video:** brightness, contrast, saturation, hue, sharpening, aspect ratio and crop, zoom, rotate, mirror.
- **Audio:**
  - 10-band equalizer with a *Footsteps* preset for game clips.
  - Volume boost up to 200%.
  - Night mode, mono or swapped channels, and lip-sync delay.
- **Subtitles:** load SRT or VTT files; adjust size, colour, background, outline, font, position and delay (`G` / `H`).
- **RGB lighting:**
  - Effects: Wave, Rotate, Ripple, Breathing, Spectrum, Audio-reactive or Solid.
  - Motion: Static, Loop or Play once.
  - 8 directions, speed, brightness and saturation controls.
  - Palettes: Rainbow, Cyber, Ember, Ocean, Tiranga, Aurora, Mono or your own colours.
  - Choose where it glows (border, seek bar, play button and more).
- **Live TV:**
  - Free public channels from [iptv-org](https://github.com/iptv-org/iptv), browsable by country (with flags that wave on hover), category and search.
  - Favourites, and channel surfing with `N` / `P`.
  - Manual or automatic updates, plus your own M3U playlists.
- **Tigu the tiger:**
  - Idles in the grass, hides when you press Play, and peeks out when you pause.
  - Roams the screen after 2 minutes of inactivity and naps after 10.
  - Reacts when you click it.
- **Built for gamers:**
  - Every keyboard shortcut can be rebound.
  - Gamepad support.
  - Stats overlay (FPS, dropped frames, display Hz).
  - Pauses when you alt-tab, if you turn that on.
  - Media keys and screenshots.
- **Light, dark or system theme**, an RGB accent colour picker, a choice of corner styles, and interface scaling.
- **30 languages:** English, Russian, Korean, Chinese, Japanese, French, German, Thai, and all 22 languages of India's Eighth Schedule. See [Translations](#translations).
- **Export to mpv.conf.** Your settings can be exported as an mpv config file, ready for the desktop build or for mpv itself.

## Download for Windows

Get `LigerPlayer-…-Setup.exe` (installer) or `LigerPlayer-…-portable.zip` (no install) from the **Releases** page. Every push also builds them automatically; see [desktop/README.md](desktop/README.md#build-it-yourself).

## Run the web version

**On your computer:** open `index.html` in Chrome, Edge or Firefox. That's all. Live TV needs the page to be served (see below), because browsers block some requests from `file://` pages.

**On GitHub Pages (free hosting):**

1. Create a new public repository, for example `liger-player`.
2. Upload every file in this folder: `index.html`, `README.md`, `LICENSE`, `CONTRIBUTING.md`, `.nojekyll`, and the `js/` and `assets/` folders.
3. Go to **Settings → Pages**. Under *Build and deployment*, set **Source** to *Deploy from a branch*. Choose branch `main` and folder `/ (root)`, then click **Save**.
4. After about a minute, the player is live at `https://<your-username>.github.io/liger-player/`.

## Keyboard shortcuts (defaults)

| Key | Action | Key | Action |
|---|---|---|---|
| `Space` | Play / pause | `N` / `P` | Next / previous (channels on Live TV) |
| `←` `→` | Seek 5 s (Shift: 30 s) | `↑` `↓` | Volume |
| `[` `]` | Slower / faster | `B` | Set A, set B, clear loop |
| `F` | Fullscreen | `M` | Mute |
| `V` | Subtitles on/off | `G` / `H` | Subtitles earlier / later |
| `S` | Screenshot | `I` | Stats overlay |
| `T` | Live TV tab | `C` | Settings |
| `.` `,` | Frame step (paused) | `L` / `Z` | Repeat / shuffle |

All of these can be changed in **Settings → Controls**.

## Live TV notice

Liger Player does not host or stream any video itself. Live TV reads the public channel list maintained by the [iptv-org](https://github.com/iptv-org/iptv) community.

- iptv-org lists stream links that, to its maintainers' knowledge, broadcasters made public on purpose.
- To report a link that infringes someone's rights, open an issue with iptv-org.
- Liger always removes channels that iptv-org marks as adult (NSFW) or blocklisted.
- Some channels may be region-locked, offline, or use plain `http://`, which secure (`https://`) pages cannot play. Liger marks these as offline and skips them.

## Translations

Translations are in [`js/i18n.js`](js/i18n.js). Each language is a single line, with strings separated by `|`.

| Status | Languages |
|---|---|
| Machine-assisted, reviewed for meaning | Assamese, Bengali, Gujarati, Hindi, Kannada, Malayalam, Marathi, Nepali, Odia, Punjabi, Tamil, Telugu, Urdu, Russian, Korean, Chinese (Simplified), Japanese, French, German, Thai |
| Draft, needs a native speaker | Dogri, Konkani, Maithili, Sanskrit, Sindhi |
| Help wanted (shows English) | Bodo, Kashmiri, Manipuri (Meitei), Santali (Ol Chiki) |

Native speakers are very welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Roadmap

- Windows app: gamepad support, seek-bar thumbnails, and opening files in the window that's already running (single instance).
- Hand-drawn flags for every country. About 50 are drawn so far; the rest show a code badge.
- Seek-bar thumbnail previews and auto-cropping of black bars.
- A "Second screen" mini player, and saved settings profiles.
- Exporting A–B clips.

## Credits

- **Live TV channel data:** [iptv-org](https://github.com/iptv-org) (The Unlicense).
- **HLS playback:** [hls.js](https://github.com/video-dev/hls.js) (Apache-2.0), loaded from cdnjs only when needed.
- **Fonts:** Chakra Petch, Manrope, JetBrains Mono and Noto Sans, via Google Fonts (SIL Open Font License).
- **Artwork:** Tigu, the flags and the icon are original, drawn in code for this project.
- **Inspiration:** the open-source players VLC, mpv and MPC-HC. Liger contains no code from them.

## License

Web version: [MIT](LICENSE). Windows app: GPL-3.0-or-later ([LICENSE-DESKTOP.txt](LICENSE-DESKTOP.txt)), because it bundles libmpv.
