#!/usr/bin/env python3
"""
Build a browsable offline mirror from raw/ WITHOUT changing any page content.

The ONLY modifications are the mechanical link conversions that every website
archiver (wget --convert-links, HTTrack) must apply so the exact pages resolve
as local files:

  * dynamic detail links  MutationDetailPage.external?sp=N  ->  mutations/sp-N.html
  * server-absolute asset paths  /include /assets /image  ->  page-relative
  * root link  /Home.html  ->  page-relative Home.html

No banners, no injected scripts, no replacement search, no added pages.
Text, data, markup and assets are otherwise byte-for-byte identical to raw/.
raw/ itself remains the untouched, canonical capture.
"""
import glob, os, re, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw")
SITE = os.path.join(ROOT, "site")


def convert(html, depth):
    root = "../" * depth
    html = re.sub(r'MutationDetailPage\.external\?sp=(\d+)',
                  lambda m: f'{root}mutations/sp-{m.group(1)}.html', html)
    for d in ("include", "assets", "image"):
        html = html.replace(f'"/{d}/', f'"{root}{d}/').replace(f"'/{d}/", f"'{root}{d}/")
    html = html.replace('href="/Home.html"', f'href="{root}Home.html"')
    if depth:
        html = re.sub(r'"(?:\.\./)*download/', f'"{root}download/', html)
    return html


def main():
    if os.path.exists(SITE):
        shutil.rmtree(SITE)
    os.makedirs(SITE)

    for sub in ("include", "assets", "image", "download"):
        src = os.path.join(RAW, sub)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(SITE, sub), dirs_exist_ok=True)

    for p in glob.glob(os.path.join(RAW, "*.html")):
        html = open(p, encoding="utf-8", errors="ignore").read()
        open(os.path.join(SITE, os.path.basename(p)), "w",
             encoding="utf-8").write(convert(html, 0))

    os.makedirs(os.path.join(SITE, "mutations"), exist_ok=True)
    n = 0
    for p in glob.glob(os.path.join(RAW, "mutations", "sp-*.html")):
        html = open(p, encoding="utf-8", errors="ignore").read()
        open(os.path.join(SITE, "mutations", os.path.basename(p)), "w",
             encoding="utf-8").write(convert(html, 1))
        n += 1

    print(f"mirror built: {n} mutation pages + static pages under site/")


if __name__ == "__main__":
    main()
