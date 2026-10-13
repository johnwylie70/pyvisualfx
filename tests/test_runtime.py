"""What Python sends, with no browser: a stand-in for Pyctures writes down every command.

    python tests/test_runtime.py        (or pytest)
"""
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


class Page:
    """A Pyctures reference that keeps what was asked of it."""
    _enc = True

    def __init__(self, sent, name="effects"):
        object.__setattr__(self, "_sent", sent)
        object.__setattr__(self, "_name", name)

    def __getattr__(self, name):
        return lambda *args: self._sent.append((name,) + args)


def scene():
    """A fresh run: a new stand-in Pyctures that has the effects built in, and the library as that run sees it."""
    sent = []
    p = types.ModuleType("pyctures")
    p.js = object()
    p.H_EFFECTS = 13
    p.JsRef = lambda handle: Page(sent)
    p.S = types.SimpleNamespace(ending=[], dt=None)
    sys.modules["pyctures"] = p
    import pyvisualfx
    return pyvisualfx, p, sent


def raises(kind, fn):
    try:
        fn()
    except kind as e:
        return str(e)
    raise AssertionError("it did not complain")


def test_an_effect_is_one_command_and_a_setting_is_one_more():
    pyvisualfx, p, sent = scene()
    k = pyvisualfx.kaleidoscope(8, zoom=1.2)
    assert sent == [("make", "kaleidoscope", 1, [{"segments": 8, "zoom": 1.2}])]
    assert (k.segments, k.zoom, k.angle, k.amount, k.x) == (8, 1.2, 0, 1, None)
    k.segments = 12
    k.angle += 15
    k.set("zoom", 2)
    assert sent[1:] == [("set", 1, "segments", 12), ("set", 1, "angle", 15), ("set", 1, "zoom", 2)]
    assert k.segments == 12 and k.get("angle") == 15
    k.off(); k.on(); k.remove()
    assert sent[4:] == [("call", 1, "off"), ("call", 1, "on"), ("call", 1, "remove")]


def test_python_spellings_reach_the_page_as_its_own():
    pyvisualfx, p, sent = scene()
    pyvisualfx.zoom_blur(0.3)
    pyvisualfx.rgb_split(4, spread=True)
    pyvisualfx.colour_cycle("fire")
    pyvisualfx.color_cycle(["navy", "gold"])
    pyvisualfx.tint(color="red")
    pyvisualfx.bloom(1)
    assert [s[1] for s in sent] == ["zoomBlur", "rgbSplit", "colourCycle", "colourCycle", "tint", "glow"]
    assert sent[4][3] == [{"colour": "red"}]
    assert set(pyvisualfx.effect_names()) <= set(pyvisualfx.__all__) and "zoom_blur" in pyvisualfx.__all__ and "clear_effects" in pyvisualfx.__all__


def test_every_effect_of_the_javascript_library_is_a_python_function_with_its_defaults():
    pyvisualfx, p, sent = scene()
    for name in pyvisualfx.effect_names():
        fx = getattr(pyvisualfx, name)()
        assert fx.amount == 1 and fx.settings, name
    assert len(sent) == len(pyvisualfx.effect_names()) >= 94
    assert pyvisualfx.trails().length == 0.5 and pyvisualfx.glow().threshold == 0.5 and pyvisualfx.mirror().side == "left"


def test_a_mistake_is_said_in_python_on_the_line_that_made_it():
    pyvisualfx, p, sent = scene()
    k = pyvisualfx.kaleidoscope()
    assert "no setting called 'segmnts'" in raises(AttributeError, lambda: setattr(k, "segmnts", 3))
    assert "segments, angle, zoom" in raises(AttributeError, lambda: k.segmnts)
    assert "is a number" in raises(ValueError, lambda: setattr(k, "segments", "many"))
    assert 'one of "left", "right"' in raises(ValueError, lambda: pyvisualfx.mirror("sideways"))
    assert "was given 3 values and takes 1 (radius)" in raises(TypeError, lambda: pyvisualfx.blur(1, 2, 3))
    assert "no setting called 'radis'" in raises(TypeError, lambda: pyvisualfx.blur(radis=3))
    assert 'no look called "nope"' in raises(ValueError, lambda: pyvisualfx.look("nope"))
    assert 'no palette called "nope"' in raises(ValueError, lambda: pyvisualfx.plasma("nope"))
    assert "vec4 effect(vec2 uv)" in raises(ValueError, lambda: pyvisualfx.shader("void main() {}"))
    assert "bass, mids, highs" in raises(ValueError, lambda: pyvisualfx.react(k, "zoom", "treble"))
    assert len(sent) == 1


def test_looks_shaders_music_and_the_frame():
    pyvisualfx, p, sent = scene()
    dream = pyvisualfx.look("dream")
    dream.amount = 0.5
    s = pyvisualfx.shader("vec4 effect(vec2 uv) { return texture(picture, uv) * lift; }", lift=0.5)
    s.lift = 0.8
    g = pyvisualfx.glow(0.3)
    pyvisualfx.react(g, "strength", "bass", 0.3, 1.2)
    pyvisualfx.react(g, "radius", "pulse")
    synth = types.SimpleNamespace(page=Page([], "synth"))
    pyvisualfx.listen_to(synth)
    pyvisualfx.clear_effects()
    pyvisualfx.effects_quality(0.5)
    assert sent[0] == ("make", "look", 1, ["dream", 1]) and sent[1] == ("set", 1, "amount", 0.5)
    assert sent[2][:3] == ("make", "shader", 2) and sent[2][3][1] == {"lift": 0.5} and sent[3] == ("set", 2, "lift", 0.8)
    assert sent[5] == ("react", 3, "strength", "bass", {"from": 0.3, "to": 1.2}) and sent[6] == ("react", 3, "radius", "pulse", {})
    assert sent[7][0] == "listen" and sent[7][1] is synth.page
    assert sent[8:] == [("clearEffects",), ("effectsQuality", 0.5)]
    assert "makes sound in the page" in raises(ValueError, lambda: pyvisualfx.listen_to(object()))
    # The frame: one command as each frame is sent, with the seconds Pyctures gave the scene.
    del sent[:]
    assert len(p.S.ending) == 1
    p.S.dt = 1 / 30
    p.S.ending[0]()
    assert sent == [("frame", 1 / 30)]
    # What a file draws as it starts is a frame with no time: the effects are run on it. What is sent that is no frame runs none.
    del sent[:]
    p.S.dt = 0.0
    p.S.ending[0]()
    p.S.dt = None
    p.S.ending[0]()
    assert sent == [("frame", 0.0)]
    # The music's numbers are asked for once, and are what the page last told.
    assert pyvisualfx.bass() == 0
    assert sent[1][0] == "report"
    sent[1][1]({"b": [0.5, 0.25, 0.125, 1, 0]})
    assert (pyvisualfx.bass(), pyvisualfx.mids(), pyvisualfx.highs(), pyvisualfx.loudness(), pyvisualfx.pulse()) == (0.5, 0.25, 0.125, 1, 0) and sent[-1] == ("ack",)


def test_a_new_run_starts_with_nothing():
    pyvisualfx, p, sent = scene()
    pyvisualfx.glow()
    vfx2, p2, sent2 = scene()
    vfx2.blur()
    assert sent2 == [("make", "blur", 1, [{}])]


def test_the_copies_are_the_javascript_library():
    js = ROOT.parent / "visualfx.js" / "visualfx.js"
    if js.exists():
        assert (ROOT / "src" / "pyvisualfx" / "web" / "visualfx.js").read_text(encoding="utf-8") == js.read_text(encoding="utf-8"), "run scripts/sync_js.py"


if __name__ == "__main__":
    failed = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            try:
                fn()
                print("  ok   " + name[5:].replace("_", " "))
            except Exception as e:
                failed += 1
                print("  FAIL %s\n       %s: %s" % (name[5:].replace("_", " "), type(e).__name__, e))
    sys.exit(1 if failed else 0)
