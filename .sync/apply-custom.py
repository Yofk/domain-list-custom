#!/usr/bin/env python3
"""Re-apply local customizations onto the upstream build.yml.

Used by .github/workflows/sync.yml after a hard reset to upstream.
Idempotent.  Exits non-zero (loud failure) if an expected anchor is gone, so a
human updates this script instead of silently losing the VPS custom sources.
"""
import sys
import pathlib

path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".github/workflows/build.yml")
text = path.read_text(encoding="utf-8")

MARK = "mihomo.deng2z.xyz/config/direct.txt"
if MARK in text:
    print("custom sources already present; nothing to do")
    sys.exit(0)

ENV_BLOCK = [
    "          # ===== 自定义源（VPS）=====\n",
    '          echo "media_extra_domainset1=https://ruleset.skk.moe/Clash/domainset/download.txt" >> "${GITHUB_ENV}"\n',
    '          echo "media_extra_domainset2=https://mihomo.deng2z.xyz/config/download.txt" >> "${GITHUB_ENV}"\n',
    '          echo "cn_extra=https://mihomo.deng2z.xyz/config/direct.txt" >> "${GITHUB_ENV}"\n',
]
MEDIA_BLOCK = [
    "          # ========== 自定义 media 源（VPS）==========\n",
    "          curl -fsSL \"${media_extra_domainset1}\" | grep -v '^#' | grep -v '^$' | grep -v '^DOMAIN' | grep -v 'ruleset.skk.moe' | grep -v '_' | sed 's/^+\\.//' | sort --ignore-case >> ./tmp/temp-media-sort-suffix.txt\n",
    "          curl -fsSL \"${media_extra_domainset2}\" | grep -v '^#' | grep -v '^$' | grep -v '^DOMAIN' | grep -v '_' | sed 's/^+\\.//' | sort --ignore-case >> ./tmp/temp-media-sort-suffix.txt\n",
]
CN_BLOCK = [
    "          # ========== 自定义 cn 源（VPS）==========\n",
    "          curl -fsSL \"${cn_extra}\" | grep -v '^#' | grep -v '^$' | grep -v '^DOMAIN' | grep -v '_' | sed 's/^+\\.//' | sort --ignore-case >> ./tmp/temp-cn-sort-suffix.txt\n",
]

# (unique substring of the anchor line, block to insert after it)
ANCHORS = [
    ("cn2=https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/China/China.list", ENV_BLOCK),
    ("> ./tmp/temp-media-sort-suffix.txt", MEDIA_BLOCK),
    ("> ./tmp/temp-cn-sort-suffix.txt", CN_BLOCK),
]

lines = text.splitlines(keepends=True)
missing = []
for anchor, _ in ANCHORS:
    if sum(1 for l in lines if anchor in l) != 1:
        missing.append(anchor)
if missing:
    sys.stderr.write("ERROR: expected exactly one anchor line for each of:\n")
    for m in missing:
        sys.stderr.write("  - %s\n" % m)
    sys.stderr.write("Upstream build.yml changed; update .sync/apply-custom.py before syncing.\n")
    sys.exit(1)

for anchor, block in reversed(ANCHORS):
    idx = max(i for i, l in enumerate(lines) if anchor in l)
    lines[idx + 1:idx + 1] = block

path.write_text("".join(lines), encoding="utf-8")
print("custom sources re-applied to %s" % path)
