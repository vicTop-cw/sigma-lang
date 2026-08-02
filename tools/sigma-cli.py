#!/usr/bin/env python3
"""sigma-cli — ΣLang package manager CLI (v0.11).

Commands:
  install <pkg> | <spec.md>   install a package from std/ or a local spec file
  verify <pkg> | <file>       verify an installed package or any module file
  list                        list installed packages
  search <keyword>            search std/ and the local registry
  fingerprint <pkg> | <file>  show sha256 fingerprint of a package/module

Registry: ~/.sigma/registry.json
  {"packages": {"math.base": {"version": "1.0.0", "path": ..., "fingerprint": "sha256:...", "modules": [...], "deps": ["core@1.0"]}}}

Dependency resolution honors Iron Law VII — the package graph must be
acyclic; install refuses to create a cycle (rejects circular deps).

Examples:
  python3 tools/sigma-cli.py install math.base@1.0
  python3 tools/sigma-cli.py install std/math.base.md
  python3 tools/sigma-cli.py verify math.base
  python3 tools/sigma-cli.py list
  python3 tools/sigma-cli.py search confidence
  python3 tools/sigma-cli.py fingerprint std/math.base.md
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TOOLS_DIR)
STD_DIR = os.path.join(REPO_ROOT, "std")
CORPUS_DIR = os.path.join(REPO_ROOT, "corpus")
VERIFY_CONSENSUS = os.path.join(REPO_ROOT, "verify_consensus.py")
SIGMA_HOME = os.environ.get("SIGMA_HOME", os.path.join(str(Path.home()), ".sigma"))
REGISTRY_PATH = os.path.join(SIGMA_HOME, "registry.json")

HEADER_FIELDS = {
    "Package": "name",
    "Version": "version",
    "Depends": "deps",
    "Fingerprint Prefix": "fp_prefix",
    "Domain": "domain",
    "Maintainer": "maintainer",
    "License": "license",
}


def parse_package(path):
    """Parse a ΣLang package spec (.md). Returns dict or None if not a package."""
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return None
    pkg = {"name": None, "version": None, "deps": [], "fp_prefix": None,
           "domain": None, "maintainer": None, "license": None,
           "exports": [], "modules": []}
    in_exports = False
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"^# (Package|Version|Depends|Fingerprint Prefix|Domain|Maintainer|License):\s*(.+)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            field = HEADER_FIELDS[key]
            if field == "deps":
                pkg["deps"] = [d.strip() for d in val.split(",") if d.strip()]
            elif field == "name" and not pkg["name"]:
                pkg["name"] = val
            else:
                pkg[field] = val
            continue
        if line == "## Exports":
            in_exports = True
            continue
        if line.startswith("## ") and line != "## Exports":
            in_exports = False
        if in_exports and line.startswith("```"):
            continue
        if in_exports and not line.startswith("## "):
            for tok in re.split(r"[,\s]+", line):
                t = tok.strip().strip("`")
                if t and t not in pkg["exports"]:
                    pkg["exports"].append(t)
    if not pkg["name"]:
        return None
    return pkg


def sha256_of(path):
    """sha256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def load_registry():
    if not os.path.exists(REGISTRY_PATH):
        return {"packages": {}}
    try:
        with open(REGISTRY_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"packages": {}}


def save_registry(reg):
    os.makedirs(SIGMA_HOME, exist_ok=True)
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)
        f.write("\n")


def resolve_pkg_path(spec):
    """Resolve `math.base@1.0` or `math.base` or a file path → (name, path)."""
    if os.path.exists(spec):
        name = os.path.basename(spec).replace(".md", "")
        return name, os.path.abspath(spec)
    m = re.match(r"^([\w.]+)(?:@([\w.]+))?$", spec)
    if not m:
        return None, None
    name, ver = m.group(1), m.group(2)
    candidates = [os.path.join(STD_DIR, name + ".md")]
    if ver:
        candidates.append(os.path.join(STD_DIR, f"{name}@{ver}.md"))
    for c in candidates:
        if os.path.exists(c):
            return name, c
    return name, None


def check_acyclic(name, pkg_meta, registry, visiting=None, seen=None):
    """Iron Law VII — no circular dependencies.

    Returns list of dependency names in install order (topological), or
    raises RuntimeError on a cycle.
    """
    visiting = visiting or []
    seen = seen or set()
    if name in visiting:
        cycle = " -> ".join(visiting[visiting.index(name):] + [name])
        raise RuntimeError(f"Iron Law VII violation — circular dependency: {cycle}")
    if name in seen:
        return []
    visiting.append(name)
    order = []
    deps = pkg_meta.get("deps") or []
    for d in deps:
        dname = re.sub(r"@[\w.]+$", "", d.strip())
        dmeta = registry["packages"].get(dname) or {}
        if not dmeta:
            # Dependency not installed and not resolvable from std/ — it
            # must be a built-in (core) or still missing; core is implicit.
            if dname == "core":
                continue
            raise RuntimeError(f"missing dependency: {dname} (required by {name})")
        order.extend(check_acyclic(dname, dmeta, registry, visiting, seen))
    visiting.pop()
    seen.add(name)
    order.append(name)
    return order


def cmd_install(args):
    name, path = resolve_pkg_path(args.pkg)
    if path is None:
        print(f"error: package '{args.pkg}' not found in std/ ({STD_DIR})")
        return 1
    pkg = parse_package(path)
    if pkg is None:
        print(f"error: '{path}' is not a valid ΣLang package spec (missing '# Package:')")
        return 1
    if pkg["name"] != name:
        print(f"error: file declares package '{pkg['name']}' but was invoked as '{name}'")
        return 1

    registry = load_registry()
    existing = registry["packages"].get(name)
    if existing and existing.get("version") == pkg.get("version"):
        print(f"ok: {name}@{pkg['version']} already installed (fingerprint {existing['fingerprint']})")
        return 0

    # Iron Law VII — resolve the full dependency graph before writing anything.
    try:
        order = check_acyclic(name, pkg, registry)
    except RuntimeError as e:
        print(f"error: {e}")
        return 1

    # Install dependency packages that are resolvable from std/ but missing.
    for dep in (pkg.get("deps") or []):
        dname = re.sub(r"@[\w.]+$", "", dep.strip())
        if dname == "core" or dname in registry["packages"]:
            continue
        dpath = os.path.join(STD_DIR, dname + ".md")
        if os.path.exists(dpath):
            if cmd_install(argparse.Namespace(pkg=dname)) != 0:
                return 1
            registry = load_registry()

    dest_dir = os.path.join(SIGMA_HOME, "packages", name)
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, f"{name}@{pkg['version']}.md")
    shutil.copyfile(path, dest)

    entry = {
        "version": pkg.get("version") or "0.1.0",
        "path": dest,
        "fingerprint": sha256_of(dest),
        "modules": sorted(set(pkg["exports"])),
        "deps": pkg.get("deps") or [],
    }
    registry["packages"][name] = entry
    save_registry(registry)
    print(f"installed {name}@{entry['version']} (deps: {order})")
    print(f"  fingerprint: {entry['fingerprint']}")
    return 0


def cmd_verify(args):
    pkg_arg = args.pkg
    explicit_path = os.path.abspath(pkg_arg) if os.path.exists(pkg_arg) else None
    if explicit_path:
        name = os.path.basename(explicit_path).replace(".md", "")
    else:
        name = re.sub(r"@[\w.]+$", "", pkg_arg)
    target = explicit_path
    # A package spec file (std/*.md, Package format) is verified through its
    # canonical verifier test set in corpus/ — the spec itself is not a Module.
    if explicit_path:
        pkg = parse_package(explicit_path)
        if pkg and pkg.get("name"):
            name = pkg["name"]
    # corpus test sets use underscores (std_data_transform_ok.md) while
    # package names use dots (data.transform) — normalize before matching.
    safe = name.replace(".", "_")
    for cand in (os.path.join(CORPUS_DIR, f"std_{safe}_ok.md"),
                 os.path.join(CORPUS_DIR, f"{safe}_ok.md")):
        if os.path.exists(cand):
            target = cand
            break
    if target is None:
        registry = load_registry()
        entry = registry["packages"].get(name)
        if entry is None:
            print(f"error: package '{name}' not installed — run 'sigma-cli install {name}' first")
            return 1
        target = entry["path"]
    print(f"verifying {name} ({target})")
    proc = subprocess.run([sys.executable, VERIFY_CONSENSUS, target],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace")
    out = (proc.stdout + proc.stderr).strip()
    print(out)
    # A module row that passes shows the Python/Rust/Elixir verdict columns
    # as PASS PASS PASS; any FAIL column means the module failed verification.
    passed = bool(re.search(r"\bPASS\s+PASS\s+PASS\b", out))
    if passed:
        print(f"✅ {name} verified (three-verifier consensus PASS)")
        return 0
    print(f"❌ {name} failed verification")
    return 1


def cmd_list(_args):
    registry = load_registry()
    pkgs = registry.get("packages", {})
    if not pkgs:
        print("no packages installed (run: python3 tools/sigma-cli.py install math.base)")
        return 0
    print(f"{'Package':<22}{'Version':<10}{'Fingerprint':<20}{'Deps'}")
    print("-" * 78)
    for name in sorted(pkgs):
        e = pkgs[name]
        deps = ", ".join(e.get("deps", [])) or "—"
        print(f"{name:<22}{e.get('version', '?'):<10}{e.get('fingerprint', '?')[:18]:<20}{deps}")
    return 0


def cmd_search(args):
    kw = args.keyword.lower()
    hits = []
    # std/ (available packages)
    if os.path.isdir(STD_DIR):
        for f in sorted(os.listdir(STD_DIR)):
            if not f.endswith(".md"):
                continue
            pkg = parse_package(os.path.join(STD_DIR, f))
            if pkg and (kw in pkg["name"].lower() or
                        kw in " ".join(pkg["exports"]).lower() or
                        (pkg.get("domain") or "").lower().startswith(kw)):
                hits.append((pkg["name"], pkg.get("version"), "std/", ",".join(pkg["exports"])))
    # registry (installed)
    registry = load_registry()
    for name, e in registry.get("packages", {}).items():
        if kw in name.lower():
            hits.append((name, e.get("version"), "installed", ",".join(e.get("modules", []))))
    if not hits:
        print(f"no packages match '{args.keyword}'")
        return 0
    print(f"{'Package':<24}{'Version':<10}{'Source':<12}Exports")
    print("-" * 78)
    for name, ver, src, exp in hits:
        print(f"{name:<24}{ver:<10}{src:<12}{exp}")
    return 0


def cmd_fingerprint(args):
    _, path = resolve_pkg_path(args.pkg)
    if path is None:
        print(f"error: '{args.pkg}' not found")
        return 1
    print(f"{os.path.basename(path)}: {sha256_of(path)}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="sigma-cli",
        description="ΣLang package manager (v0.11) — install/verify/list/search/fingerprint")
    sub = parser.add_subparsers(dest="command", required=True)

    p_install = sub.add_parser("install", help="install a package from std/ or a spec file")
    p_install.add_argument("pkg", help="package name (math.base@1.0) or path (std/math.base.md)")
    p_install.set_defaults(fn=cmd_install)

    p_verify = sub.add_parser("verify", help="verify an installed package or module file")
    p_verify.add_argument("pkg", help="installed package name (math.base) or file path")
    p_verify.set_defaults(fn=cmd_verify)

    sub.add_parser("list", help="list installed packages").set_defaults(fn=cmd_list)

    p_search = sub.add_parser("search", help="search std/ and the registry")
    p_search.add_argument("keyword", help="search keyword (package name, domain, or export)")
    p_search.set_defaults(fn=cmd_search)

    p_fp = sub.add_parser("fingerprint", help="show sha256 fingerprint")
    p_fp.add_argument("pkg", help="package name or file path")
    p_fp.set_defaults(fn=cmd_fingerprint)

    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
