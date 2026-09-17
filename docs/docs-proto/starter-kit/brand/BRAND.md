# ANCA Motion — brand basics (for the operator-assistant teams)

A light brand kit so your app can look like ANCA rather than a default template. This is a
trimmed subset of ANCA Motion's brand standards, provided for the COMP30022 project only
(see `../NOTICE.md`). If you'd like the full guidelines, ask the client contact.

## Logo

- `anca-motion-logo-colour.png` — full-colour, transparent background. Use on light backgrounds.
- `anca-motion-logo-white.png` — reversed/white, transparent background. Use on dark backgrounds.
- `anca-motion-logo-black.png` — black, transparent background. Use on light backgrounds.
- `anca-logo-white.png` — white, transparent background. Use on dark backgrounds.
- `anca-logo-black.png` — black, transparent background. Use on light backgrounds.

Do: keep clear space around it; keep it legible.
Don't: recolour it, stretch/skew it, rotate it, or place the colour version on a busy or
low-contrast background.

## Colours

Primary:

| Role | Hex |
|------|-----|
| ANCA blue (primary) | `#026CB6` |
| Light blue (accent) | `#9ACAEB` |
| Dark grey / navy (text, dark bg) | `#435363` |
| Black | `#000000` |
| White | `#FFFFFF` |

Secondary / accents (use sparingly — charts, highlights):

| Colour | Hex |
|--------|-----|
| Red | `#CF0A2C` |
| Green | `#00B288` |
| Yellow | `#FFB819` |
| Warm grey | `#D8D1CA` |

Keep ANCA blue dominant; let white space breathe; use accents sparingly.

## Fonts (all free / web-friendly)

- **Headings:** Bebas Neue — free on Google Fonts.
- **Body / UI:** Roboto — free on Google Fonts (this is ANCA's secondary typeface and works well for a web UI).
- If you can't load a web font, system sans-serif (or Calibri/Arial) is a fine fallback.

```html
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
```

## A note for the factory floor

The operator app is used at a machine, often in bright light with gloves on. Favour high
contrast, large touch targets, and clear typography over decoration — an on-brand *and*
readable app beats a pretty one that's hard to use on the floor.
