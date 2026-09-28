#!/usr/bin/env python3
"""Fetch a company's brand assets so the dashboard can carry their real identity.

Given a domain (or homepage URL), print candidate logo URLs, a theme color, and the
social-share image. The model then downloads the best logo, *looks at it*, and derives
2-3 accent colors from it (a script can't reliably read colors out of an SVG/PNG logo,
but you can: view the image and pick).

Usage:
  python3 brand_fetch.py acme.com
  python3 brand_fetch.py https://www.example.com

Stdlib only. Best-effort: sites vary. If nothing good comes back, just search the web
for "<company> brand guidelines / logo png" and eyeball the colors.
"""
import sys, re, json, urllib.request, urllib.parse

UA = "Mozilla/5.0 (compatible; brand-fetch/1.0)"


def norm(d):
    d = d.strip()
    if not d.startswith("http"):
        d = "https://" + d
    return d


def fetch(url, limit=400_000):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read(limit).decode("utf-8", "ignore"), r.geturl()


def absolutize(base, href):
    if not href:
        return None
    return urllib.parse.urljoin(base, href.strip().strip('"\''))


def main():
    if len(sys.argv) < 2:
        print("usage: brand_fetch.py <domain-or-url>", file=sys.stderr)
        sys.exit(1)
    url = norm(sys.argv[1])
    out = {"input": url, "logos": [], "icons": [], "theme_color": None, "og_image": None}
    try:
        html, final = fetch(url)
    except Exception as e:
        print(json.dumps({"error": str(e), "input": url,
                          "fallback_favicon": f"https://www.google.com/s2/favicons?domain={urllib.parse.urlparse(url).netloc}&sz=128"}, indent=2))
        return
    out["resolved"] = final
    host = urllib.parse.urlparse(final).netloc

    def meta(prop):
        m = re.search(rf'<meta[^>]+(?:name|property)=["\']{re.escape(prop)}["\'][^>]+content=["\']([^"\']+)', html, re.I) \
            or re.search(rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:name|property)=["\']{re.escape(prop)}["\']', html, re.I)
        return m.group(1) if m else None

    out["theme_color"] = meta("theme-color")
    out["og_image"] = absolutize(final, meta("og:image"))

    # icon + logo candidates
    for m in re.finditer(r'<link[^>]+rel=["\']([^"\']*icon[^"\']*)["\'][^>]*>', html, re.I):
        tag = m.group(0)
        href = re.search(r'href=["\']([^"\']+)', tag)
        if href:
            out["icons"].append(absolutize(final, href.group(1)))
    # apple-touch-icon is usually the crispest square logo
    at = re.search(r'<link[^>]+rel=["\']apple-touch-icon[^>]*href=["\']([^"\']+)', html, re.I)
    if at:
        out["icons"].insert(0, absolutize(final, at.group(1)))
    # <img> whose src/alt/class hints "logo"
    for m in re.finditer(r'<img[^>]+>', html, re.I):
        tag = m.group(0)
        if re.search(r'logo', tag, re.I):
            href = re.search(r'src=["\']([^"\']+)', tag)
            if href:
                out["logos"].append(absolutize(final, href.group(1)))
    # common brand asset providers as fallbacks
    out["fallbacks"] = [
        f"https://logo.clearbit.com/{host}",              # may 404 (deprecated)
        f"https://www.google.com/s2/favicons?domain={host}&sz=256",
    ]
    # dedupe, keep order
    for k in ("logos", "icons"):
        seen, uniq = set(), []
        for u in out[k]:
            if u and u not in seen:
                seen.add(u); uniq.append(u)
        out[k] = uniq[:6]
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
