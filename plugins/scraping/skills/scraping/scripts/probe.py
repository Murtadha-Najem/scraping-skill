"""probe.py: assess a source before writing any collector. About a dozen polite requests.

    python probe.py https://example.com/some/page [--out probe_out] [--delay 0.6]

Answers, in order (see reference/assess.md):
  1. Does it respond, and how big? Does a stock client get the same answer as a Chrome-shaped one?
  2. Is the data in the HTML, or is it a shell that fills itself? Is there embedded JSON?
  3. Who sits in front of it (Cloudflare, Vercel, CloudFront) and what rate headers does it send?
  4. robots.txt and the sitemaps it declares: are the declared sitemaps really there, and how many URLs?
  5. If it is WordPress: how many items does the CMS say it holds (x-wp-total)?

It never solves a challenge and never retries a refusal. A refusal is reported, and its body
is saved to --out so you can read which layer produced it.
"""
import argparse
import json
import os
import re
import sys
import time
from urllib.parse import urljoin, urlparse

try:
    from curl_cffi import requests as cffi
except Exception:  # curl_cffi is optional here
    cffi = None
import requests

try:
    from selectolax.parser import HTMLParser
except Exception:
    HTMLParser = None

STOCK_UA = {"User-Agent": "python-requests/probe"}


def utf8():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass


class Probe:
    def __init__(self, out, delay):
        self.out, self.delay, self.n = out, delay, 0
        os.makedirs(out, exist_ok=True)

    def get(self, url, chrome=False, **kw):
        self.n += 1
        time.sleep(self.delay)
        try:
            if chrome and cffi:
                return cffi.get(url, impersonate="chrome", timeout=30, allow_redirects=True, **kw)
            return requests.get(url, headers=STOCK_UA, timeout=30, allow_redirects=True, **kw)
        except Exception as e:  # network failure is a finding, not a crash
            return e

    def save(self, tag, url, r):
        if isinstance(r, Exception) or r.status_code == 200:
            return
        path = os.path.join(self.out, "%s_%s.txt" % (r.status_code, tag))
        with open(path, "w", encoding="utf-8") as f:
            f.write("URL: %s\nSTATUS: %s\nHEADERS: %s\n\n%s" % (url, r.status_code, dict(r.headers), r.text[:20000]))
        return path


def brief(r):
    if isinstance(r, Exception):
        return "ERROR %s: %s" % (type(r).__name__, str(r)[:160])
    return "%s  %s  %d bytes" % (r.status_code, (r.headers.get("content-type") or "?").split(";")[0], len(r.content))


def edge_hints(h):
    h = {k.lower(): v for k, v in h.items()}
    hints = []
    if "cf-ray" in h or "cloudflare" in h.get("server", "").lower():
        hints.append("Cloudflare")
    if "x-vercel-id" in h or "vercel" in h.get("server", "").lower():
        hints.append("Vercel")
    if "x-amz-cf-id" in h or "cloudfront" in h.get("via", "").lower():
        hints.append("CloudFront")
    if "x-akamai" in " ".join(h) or "akamai" in h.get("server", "").lower():
        hints.append("Akamai")
    if h.get("x-powered-by"):
        hints.append("x-powered-by: " + h["x-powered-by"])
    if h.get("server"):
        hints.append("server: " + h["server"])
    rate = {k: v for k, v in h.items() if "ratelimit" in k or k == "retry-after"}
    return hints, rate


def analyse_html(html):
    """Shell or real content? Returns (facts dict, list of embedded-data findings)."""
    facts, found = {}, []
    if HTMLParser:
        tree = HTMLParser(html)
        scripts = len(tree.css("script"))
        for n in tree.css("script, style, noscript"):
            n.decompose()
        text = re.sub(r"\s+", " ", (tree.body.text() if tree.body else tree.text())).strip()
        facts.update(scripts=scripts, visible_text_chars=len(text))
        title = tree.css_first("title")
        facts["title"] = title.text().strip()[:120] if title else None
        gen = tree.css_first('meta[name="generator"]')
        facts["generator"] = gen.attributes.get("content") if gen else None
    if "__NEXT_DATA__" in html:
        found.append("Next.js pages router: one __NEXT_DATA__ JSON blob")
    if "self.__next_f.push" in html:
        found.append("Next.js app router: fields streamed as escaped JSON in self.__next_f.push chunks")
    if "__NUXT__" in html or "__NUXT_DATA__" in html:
        found.append("Nuxt payload")
    if "window.__INITIAL_STATE__" in html or "__APOLLO_STATE__" in html:
        found.append("embedded app state (INITIAL_STATE / APOLLO)")
    ld = len(re.findall(r'application/ld\+json', html))
    if ld:
        found.append("%d JSON-LD block(s)" % ld)
    if facts.get("visible_text_chars", 1e9) < 400 and facts.get("scripts", 0) >= 1:
        found.append("LOOKS LIKE A SHELL: little visible text and scripts present; the page probably fills itself. "
                     "Find the data call (network tab, scroll to trigger it, or grep the JS bundle); do not guess paths")
    return facts, found


def sitemap_report(p, url, declared=True):
    r = p.get(url, chrome=True)
    line = "  %s -> %s" % (url, brief(r))
    if isinstance(r, Exception):
        return line
    if r.status_code in (429, 503):
        p.save("sitemap", url, r)
        return line + "   (rate limited, NOT evidence it is missing: rerun with a larger --delay)"
    if r.status_code != 200:
        p.save("sitemap", url, r)
        if declared:
            return line + "   (declared in robots.txt but not served: a declaration is a claim, not a fact)"
        return line + "   (guessed default path, nothing declares it: no sitemap here, or it lives elsewhere)"
    locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", r.text)
    kind = "index of %d sitemaps" % len(locs) if "<sitemapindex" in r.text else "%d URLs" % len(locs)
    return line + "  [%s]" % kind


def main():
    utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--out", default="probe_out")
    ap.add_argument("--delay", type=float, default=0.6)
    a = ap.parse_args()
    p = Probe(a.out, a.delay)
    u = urlparse(a.url)
    origin = "%s://%s" % (u.scheme, u.netloc)

    print("== 1. Response: stock client vs Chrome-shaped (curl_cffi)%s" % ("" if cffi else "  [curl_cffi missing]"))
    stock = p.get(a.url)
    chrome = p.get(a.url, chrome=True)
    print("  stock  :", brief(stock))
    print("  chrome :", brief(chrome))
    p.save("stock", a.url, stock)
    p.save("chrome", a.url, chrome)
    if not isinstance(stock, Exception) and not isinstance(chrome, Exception):
        if stock.status_code != chrome.status_code:
            print("  NOTE: the two clients were treated differently. If the stock client is refused and Chrome is not,")
            print("        copy what the browser sends (headers, then TLS via curl_cffi) before calling this a block.")
    main_r = chrome if (not isinstance(chrome, Exception) and chrome.status_code == 200) else stock
    if isinstance(main_r, Exception) or main_r.status_code != 200:
        print("  Could not get the page. Read the saved error body in %s/ before deciding anything." % a.out)
    else:
        with open(os.path.join(a.out, "page.html"), "w", encoding="utf-8") as f:
            f.write(main_r.text)
        hints, rate = edge_hints(main_r.headers)
        print("\n== 2. Content")
        facts, found = analyse_html(main_r.text)
        for k, v in facts.items():
            print("  %s: %s" % (k, v))
        for f_ in found:
            print("  - " + f_)
        print("\n== 3. In front of it")
        print("  " + ("; ".join(hints) if hints else "no edge hints"))
        print("  rate headers: %s" % (json.dumps(rate) if rate else "none sent (measure the limit; do not assume)"))

    print("\n== 4. robots.txt and sitemaps")
    rob = p.get(origin + "/robots.txt", chrome=True)
    print("  robots.txt:", brief(rob))
    sitemaps = []
    if not isinstance(rob, Exception) and rob.status_code == 200:
        sitemaps = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", rob.text)
        bots = re.findall(r"(?im)^\s*user-agent:\s*(\S+)\s*\n\s*disallow:\s*/\s*$", rob.text)
        if bots:
            print("  blanket Disallow for: " + ", ".join(bots[:12]))
        cs = re.findall(r"(?im)^\s*content-signal:.*$", rob.text)
        if cs:
            print("  " + cs[0].strip())
    else:
        p.save("robots", origin + "/robots.txt", rob)
    declared = bool(sitemaps)
    if not sitemaps:
        sitemaps = [origin + "/sitemap.xml"]
        print("  no Sitemap line; trying /sitemap.xml")
    for s in sitemaps[:4]:
        print(sitemap_report(p, s, declared))

    print("\n== 5. WordPress check")
    wp = p.get(origin + "/wp-json/", chrome=True)
    is_wp = (not isinstance(wp, Exception) and wp.status_code == 200 and "json" in (wp.headers.get("content-type") or ""))
    if is_wp:
        print("  /wp-json/ answers JSON: this is WordPress. The CMS knows its own inventory:")
        for route in ("posts", "pages", "product"):
            r = p.get(origin + "/wp-json/wp/v2/%s?per_page=1" % route, chrome=True)
            if not isinstance(r, Exception) and r.status_code == 200:
                print("    /wp/v2/%s  x-wp-total=%s  x-wp-totalpages=%s" % (
                    route, r.headers.get("x-wp-total"), r.headers.get("x-wp-totalpages")))
        print("  Compare these totals with what the site's own listing pages show (a page is a view, not the list).")
    else:
        print("  not WordPress (or the API is closed): " + brief(wp))

    print("\n%d requests made. Error bodies, if any, are in %s/. Next: reference/assess.md." % (p.n, a.out))


if __name__ == "__main__":
    main()
