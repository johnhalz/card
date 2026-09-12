# card

Digital contact card at **https://johnhalz.github.io/card/**

One HTML file, no build step, no dependencies. The only generated artifact is
`contact.vcf`.

## Changing a detail

1. Edit `contact.json` — it is the source of truth for the vCard.
2. Regenerate: `python3 scripts/build-vcf.py` (stdlib only, no install).
3. **Update `index.html` to match.** The page does not read `contact.json`;
   the name, title and office are written into the HTML directly. They will
   drift if you only do step 1.
4. Commit and push to `main`. GitHub Pages redeploys in about a minute.

`build-vcf.py` bumps `REV` on every run, which is how contact apps tell an
updated card from one already saved.

## Replacing the photo

```sh
SRC=path/to/new.jpg
magick "$SRC" -resize 600x600^  -gravity north -extent 600x600 -quality 86 -strip photo.jpg
magick "$SRC" -resize 300x300^  -gravity north -extent 300x300 -quality 80 -strip photo-small.jpg
magick "$SRC" -resize 1200x630^ -gravity north -extent 1200x630 -quality 85 -strip og.jpg
python3 scripts/build-vcf.py
```

`photo-small.jpg` is the base64 source embedded in the vCard — keep it under
40KB. `photo.jpg` is what the page displays.

## Regenerating the QR code

`qr.svg` encodes the page URL, not the vCard, so the details can change without
reprinting anything.

```sh
qrencode -t SVG -m 1 -o qr.svg "https://johnhalz.github.io/card/"
```

It is SVG, so it scales into slides or an email signature at any size.

## NFC

An NTAG215 sticker costs about a franc. The NFC Tools app writes the page URL to
it in under a minute — no need to buy a vendor's NFC business card.

## Why vCard 3.0

3.0 is what iOS Contacts and Android parse without surprises; 4.0 still trips up
some clients. The file needs CRLF line endings (enforced by `.gitattributes`) and
the photo embedded as base64 rather than a URL — many clients never fetch a
remote photo and the contact ends up with no face.
