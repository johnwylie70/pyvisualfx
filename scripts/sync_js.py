"""Copy the page's half from the JavaScript library, which is where it is written.

    python scripts/sync_js.py [path/to/visualfx.js]

The Python package carries ``visualfx.js`` whole, as ``src/pyvisualfx/web/visualfx.js``, and ``src/pyvisualfx/__init__.py``
carries, between its EFFECTS marks, every effect with its settings and their ranges, read out of
that file by running it (this needs ``node``). Python's functions are made from that list, so an
effect the JavaScript library gains is Python's the next time this runs. Both are copies: change
them in the JavaScript repository (by default the folder ``visualfx.js`` beside this one) and run this.
``--check`` changes nothing and ends with code 1 if a copy differs.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULE = ROOT / "src" / "pyvisualfx" / "__init__.py"
ASK = "import(process.argv[1]).then((m) => console.log(JSON.stringify(m.effects.definitions())))"
MARKS = re.compile(r"# EFFECTS:BEGIN\n.*?# EFFECTS:END\n", re.S)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check = "--check" in sys.argv
    source = (Path(args[0]) if args else ROOT.parent / "visualfx.js") / "visualfx.js"
    text = source.read_text(encoding="utf-8")
    table = subprocess.run(["node", "-e", ASK, str(source)], check=True, capture_output=True, text=True).stdout.strip()
    json.loads(table)
    module = MODULE.read_text(encoding="utf-8")
    if not MARKS.search(module):
        sys.exit("src/pyvisualfx/__init__.py has no EFFECTS marks to write between")
    # One effect to a line, so a change to one effect is one line of a diff.
    data = json.loads(table)
    one = lambda v: json.dumps(v, ensure_ascii=False, separators=(",", ":"))
    parts = ['"effects":{\n%s\n}' % ",\n".join("%s:%s" % (one(k), one(v)) for k, v in data["effects"].items())]
    parts += ["%s:%s" % (one(k), one(v)) for k, v in data.items() if k != "effects"]
    lines = "{%s}" % ",\n".join(parts)
    written = MARKS.sub(lambda m: '# EFFECTS:BEGIN\n_TABLE = json.loads(r"""%s""")\n# EFFECTS:END\n' % lines, module)
    assert json.loads(re.search(r'json\.loads\(r"""(.*?)"""\)', written, re.S).group(1)) == json.loads(table)
    out = 0
    for to, what in ((ROOT / "src" / "pyvisualfx" / "web" / "visualfx.js", text), (MODULE, written)):
        if to.exists() and to.read_text(encoding="utf-8") == what:
            continue
        out += 1
        if check:
            print("%s is not the one from %s" % (to.relative_to(ROOT), source))
            continue
        to.parent.mkdir(parents=True, exist_ok=True)
        to.write_text(what, encoding="utf-8")
        print("wrote %s" % to.relative_to(ROOT))
    sys.exit(1 if check and out else 0)


if __name__ == "__main__":
    main()
