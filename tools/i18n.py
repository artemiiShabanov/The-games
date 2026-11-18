#!/usr/bin/env python3
"""Строки игры для перевода (2026-11-18, локализация).

Ключ перевода это русский текст из кода и ресурсов; переводы лежат в
`thegames/locale/<lang>/*.po` (по файлу на часть игры), см. `scripts/menu/lang.gd`.

    python3 tools/i18n.py                   сводка: строк игрока, переведено, не хватает по файлам
    python3 tools/i18n.py --missing [путь]  непереведённые строки (можно ограничить папкой/файлом)
    python3 tools/i18n.py --check           для ci: падает, если чего-то не хватает
    python3 tools/i18n.py --project         список .po в project.godot по папке locale
    python3 tools/i18n.py --unused          строки .po, которых больше нет в игре

Служебные строки не считаются: `debug/`, комментарии, заметки и провалы автотеста
(`auto_test.gd`, `AutoTest.*`, `_expect`, `fail(`), `push_error`, `print`, `Debug.*`, строки с пометкой
`# i18n: skip` в конце. Ресурсы `.tres` считаются все.
"""
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "thegames")
ROOT = os.path.normpath(ROOT)
LOCALE = os.path.join(ROOT, "locale")
CYR = re.compile(r"[А-Яа-яЁё]")
DEV = re.compile(r"AutoTest\.|_expect\(|\bfail\(|push_error|push_warning|\bprints?\(|\bassert\(|Debug\.|_note\(|_check\(|i18n: skip")
## Служебные файлы целиком.
SKIP_FILES = {"scripts/auto_test.gd"}
STR = re.compile(r'"((?:[^"\\]|\\.)*)"')


def strip_comment(line):
    out, q = [], False
    i = 0
    while i < len(line):
        c = line[i]
        if c == "\\" and q:
            out.append(line[i:i + 2])
            i += 2
            continue
        if c == '"':
            q = not q
        elif c == "#" and not q:
            break
        out.append(c)
        i += 1
    return "".join(out)


def statements(path):
    """Логические строки: продолжения в скобках склеены. Даёт (номер строки, текст, хвост комментария)."""
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    buf, start, depth, raw = [], 0, 0, []
    for n, line in enumerate(lines, 1):
        code = strip_comment(line)
        if not buf:
            start = n
        buf.append(code)
        raw.append(line)
        no_str = STR.sub('""', code)
        depth += no_str.count("(") + no_str.count("[") + no_str.count("{")
        depth -= no_str.count(")") + no_str.count("]") + no_str.count("}")
        if depth <= 0 and not code.rstrip().endswith("\\"):
            yield start, "\n".join(buf), "\n".join(raw)
            buf, raw, depth = [], [], 0
    if buf:
        yield start, "\n".join(buf), "\n".join(raw)


def code_strings():
    found = {}
    for base, _, files in os.walk(os.path.join(ROOT, "scripts")):
        for name in sorted(files):
            if not name.endswith(".gd"):
                continue
            path = os.path.join(base, name)
            rel = os.path.relpath(path, ROOT)
            if rel in SKIP_FILES:
                continue
            for n, stmt, raw in statements(path):
                if not CYR.search(stmt) or DEV.search(stmt) or "i18n: skip" in raw:
                    continue
                for m in STR.finditer(stmt):
                    s = m.group(1)
                    if CYR.search(s):
                        found.setdefault(s, []).append("%s:%d" % (rel, n))
    return found


def res_strings():
    found = {}
    for base, _, files in os.walk(os.path.join(ROOT, "resources")):
        for name in sorted(files):
            if not name.endswith(".tres"):
                continue
            path = os.path.join(base, name)
            rel = os.path.relpath(path, ROOT)
            with open(path, encoding="utf-8") as f:
                for n, line in enumerate(f, 1):
                    for m in STR.finditer(line):
                        s = m.group(1)
                        if CYR.search(s):
                            found.setdefault(s, []).append("%s:%d" % (rel, n))
    return found


def po_files(lang="en"):
    d = os.path.join(LOCALE, lang)
    if not os.path.isdir(d):
        return []
    return sorted(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".po"))


def _unq(s):
    return s.strip()[1:-1]


def parse_po(path):
    """msgid -> msgstr (сырой текст с экранированием, как в коде)."""
    out = {}
    cur, key = None, None
    entry = {}

    def flush():
        if "msgid" in entry and entry["msgid"]:
            out[entry["msgid"]] = entry.get("msgstr", entry.get("msgstr[0]", ""))

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                if line.strip() == "" and entry:
                    flush()
                    entry = {}
                continue
            m = re.match(r'^(msgid|msgid_plural|msgstr|msgstr\[\d+\])\s+(".*")$', line)
            if m:
                key = m.group(1)
                if key == "msgid" and entry.get("msgid") is not None and "msgstr" in "".join(entry):
                    flush()
                    entry = {}
                entry[key] = _unq(m.group(2))
            elif line.startswith('"') and key:
                entry[key] = entry.get(key, "") + _unq(line)
    if entry:
        flush()
    return out


def translations(lang="en"):
    out = {}
    for p in po_files(lang):
        out.update(parse_po(p))
    return out


def all_strings():
    s = code_strings()
    for k, v in res_strings().items():
        s.setdefault(k, []).extend(v)
    return s


def sync_project():
    path = os.path.join(ROOT, "project.godot")
    pos = []
    for base, _, files in os.walk(LOCALE):
        for f in files:
            if f.endswith(".po"):
                pos.append("res://" + os.path.relpath(os.path.join(base, f), ROOT))
    pos.sort()
    line = "locale/translations=PackedStringArray(%s)" % ", ".join('"%s"' % p for p in pos)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^locale/translations=.*$", line, text, flags=re.M)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("project.godot: %d файлов перевода" % len(pos))


def main():
    args = sys.argv[1:]
    if "--project" in args:
        sync_project()
        return 0
    strings = all_strings()
    tr = translations()
    missing = {k: v for k, v in strings.items() if not tr.get(k)}
    if "--unused" in args:
        for k in sorted(set(tr) - set(strings)):
            print(k)
        return 0
    if "--missing" in args:
        filt = [a for a in args if not a.startswith("--")]
        for k, locs in sorted(missing.items(), key=lambda kv: kv[1][0]):
            if filt and not any(any(f in l for f in filt) for l in locs):
                continue
            print("%-48s %s" % (locs[0], k))
        return 0
    by_file = {}
    for k, locs in missing.items():
        for f in {l.rsplit(":", 1)[0] for l in locs}:
            by_file[f] = by_file.get(f, 0) + 1
    print("строк игрока %d, переведено %d, не хватает %d" % (len(strings), len(strings) - len(missing), len(missing)))
    if "--check" in args:
        for f, c in sorted(by_file.items(), key=lambda kv: -kv[1])[:20]:
            print("  %4d  %s" % (c, f))
        return 1 if missing else 0
    for f, c in sorted(by_file.items(), key=lambda kv: kv[0]):
        print("  %4d  %s" % (c, f))
    return 0


if __name__ == "__main__":
    sys.exit(main())
