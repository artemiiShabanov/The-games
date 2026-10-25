#!/usr/bin/env python3
"""docs/plan.yaml -> docs/PLAN.md и, с --github, метки, вехи и issues на GitHub через gh.
Идемпотентно: существующее пропускается, ничего не удаляется.

    python3 tools/sync_plan.py                       # PLAN.md
    python3 tools/sync_plan.py --github              # плюс GitHub
    python3 tools/sync_plan.py --github --dry-run    # показать команды gh
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAN_YAML = os.path.join(ROOT, "docs", "plan.yaml")
PLAN_MD = os.path.join(ROOT, "docs", "PLAN.md")
SIZE_DAYS = {"S": 0.5, "M": 1.0, "L": 2.0, "XL": 3.0}


def load_yaml(path):
    try:
        import yaml
    except ImportError:
        sys.exit("Нужен PyYAML: pip3 install pyyaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def render_md(plan):
    name = plan.get("project", "")
    out = ["# План %s" % name, "",
           "Источник: `docs/plan.yaml`. Обновить: `python3 tools/sync_plan.py`.", "",
           "Размеры: S = полдня, M = день, L = два дня, XL = три дня.", ""]
    total = left = 0.0
    for ph in plan.get("phases") or []:
        issues = ph.get("issues") or []
        days = sum(SIZE_DAYS[i["size"]] for i in issues)
        open_days = sum(SIZE_DAYS[i["size"]] for i in issues if not i.get("done"))
        total += days
        left += open_days
        out += ["## %s" % ph["title"], "",
                "**Цель:** %s  " % ph.get("goal", ""),
                "**Готово, когда:** %s  " % ph.get("done_when", ""),
                "**Оценка:** %.1f дн." % days + (" (осталось %.1f)" % open_days if open_days != days else ""), "",
                "| | Задача | Тип | Кто | Размер |", "|---|---|---|---|---|"]
        for i in issues:
            out.append("| [%s] | %s | %s | %s | %s |" % (
                "x" if i.get("done") else " ", i["title"], ", ".join(i.get("types", [])), i.get("owner", ""), i["size"]))
        out.append("")
    out += ["## Итого", "", "Всего %.1f рабочих дней, из них осталось %.1f." % (total, left), ""]
    return "\n".join(out)


def gh(args, dry_run, capture=False):
    cmd = ["gh"] + args
    if dry_run:
        print(" ".join(repr(a) if " " in a else a for a in cmd))
        return ""
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    if res.returncode != 0:
        print("  gh failed:", res.stderr.strip())
    return res.stdout if capture else ""


def sync_github(plan, dry_run):
    existing = set()
    if not dry_run:
        raw = gh(["label", "list", "--limit", "200", "--json", "name"], dry_run, capture=True)
        existing = {l["name"] for l in json.loads(raw or "[]")}
    for group in (plan.get("labels") or {}).values():
        for name, spec in group.items():
            if name not in existing:
                gh(["label", "create", name, "--color", spec["color"], "--description", spec["desc"]], dry_run)

    phases = plan.get("phases") or []
    milestones = {}
    if not dry_run:
        raw = gh(["api", "repos/{owner}/{repo}/milestones?state=all&per_page=100"], dry_run, capture=True)
        milestones = {m["title"]: m["number"] for m in json.loads(raw or "[]")}
    for ph in phases:
        if ph["title"] not in milestones:
            gh(["api", "repos/{owner}/{repo}/milestones", "-f", "title=" + ph["title"],
                "-f", "description=" + ph.get("goal", "")], dry_run)

    titles = set()
    if not dry_run:
        raw = gh(["issue", "list", "--state", "all", "--limit", "1000", "--json", "title"], dry_run, capture=True)
        titles = {i["title"] for i in json.loads(raw or "[]")}
    for ph in phases:
        for i in ph.get("issues") or []:
            if i["title"] in titles:
                continue
            labels = ["type: " + t for t in i.get("types", [])] + ["size: " + i["size"]]
            if i.get("owner"):
                labels.append("owner: " + i["owner"])
            body = (i.get("body") or "") + "\n\nРазмер: %s (%.1f дн.)\nВеха: %s" % (i["size"], SIZE_DAYS[i["size"]], ph["title"])
            args = ["issue", "create", "--title", i["title"], "--body", body, "--milestone", ph["title"]]
            for l in labels:
                args += ["--label", l]
            out = gh(args, dry_run, capture=True)
            if i.get("done") and out.strip():
                gh(["issue", "close", out.strip().rsplit("/", 1)[-1]], dry_run)

    if not dry_run:
        raw = gh(["api", "repos/{owner}/{repo}/milestones?state=all&per_page=100"], dry_run, capture=True)
        milestones = {m["title"]: m for m in json.loads(raw or "[]")}
    for ph in phases:
        m = milestones.get(ph["title"]) if not dry_run else None
        if ph.get("status") == "done" and (dry_run or (m and m["state"] == "open")):
            gh(["api", "-X", "PATCH", "repos/{owner}/{repo}/milestones/" + (str(m["number"]) if m else "<n>"),
                "-f", "state=closed"], dry_run)


def main():
    plan = load_yaml(PLAN_YAML)
    with open(PLAN_MD, "w", encoding="utf-8") as f:
        f.write(render_md(plan))
    print("wrote", os.path.relpath(PLAN_MD, ROOT))
    if "--github" in sys.argv:
        sync_github(plan, "--dry-run" in sys.argv)


if __name__ == "__main__":
    main()
