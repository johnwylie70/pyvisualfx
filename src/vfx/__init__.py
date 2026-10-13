"""vfx: effects for a Pyctures scene. Draw some shapes, then turn one on.

    from pyctures import *
    from vfx import *

    kaleidoscope(8)                              # on, eight segments
    glow(0.8)                                    # bright things shine
    trail = trails(0.5, zoom=1.5, spin=20)

    def update(dt):
        trail.spin = math.sin(time) * 40         # a setting is a plain attribute: change it any time

EFFECTS APPLY IN THE ORDER THEY ARE TURNED ON, to everything the scene has
drawn, 2D or 3D. Each has ``off()``, ``on()`` and ``remove()``, and ``amount``
(0 to 1: how much of it is mixed in). ``clear_effects()`` takes them all away.
``look("dream")`` is several at once.

THE PAGE'S GRAPHICS CARD DOES THE WORK. Python never touches the page (it may be
in a worker, or on another computer). Each function here sends ONE command that
turns the effect on in the page, from ``web/vfx.js`` (the very file that is the
JavaScript library; a Pyctures that has it built in says so with ``H_EFFECTS``,
and then this module reads no other file), and Python keeps a small object that
stands for it. Setting an attribute is one command more. The effects are run
once for each frame Python sends, straight after its drawing, on Python's clock:
so a scene recorded a frame at a time gives exactly the frames it should.

MUSIC: ``listen_to(sound_output())`` (or a synth: anything that makes sound in
the page), then ``react(shine, "strength", "bass", 0.3, 1.2)`` ties a setting
to the bass, the mids, the highs, the loudness or the pulse of a beat. That
is done in the page, on the beat, with no trip through Python. ``bass()``,
``mids()``, ``highs()``, ``loudness()`` and ``pulse()`` are the same numbers for
your own drawing, as the page last told them: a frame late.

YOUR OWN: ``shader("vec4 effect(vec2 uv) { return texture(picture, uv).bgra; }")``.

The effects, their settings and their ranges are those of the JavaScript library,
written into this file by ``scripts/sync_js.py``: this module is one file.

MIT licence.
"""
import json
import os
import re
import sys

__version__ = "0.0.0"

_HERE = os.path.dirname(os.path.abspath(__file__))
# Every effect, its settings and their ranges, as the JavaScript library has them. Written by
# scripts/sync_js.py (which runs that library and asks it): do not edit it by hand.
# EFFECTS:BEGIN
_TABLE = json.loads(r"""{"effects":{"kaleidoscope":{"order":["segments"],"settings":{"segments":{"kind":"int","default":8,"min":2,"max":32},
"angle":{"kind":"float","default":0,"min":-360,"max":360},"zoom":{"kind":"float","default":1,"min":0.2,"max":5},"x":{
"kind":"float","default":null,"min":0,"max":4000,"place":true},"y":{"kind":"float","default":null,"min":0,"max":4000,
"place":true},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false},"mirror":{"order":["side"],
"settings":{"side":{"kind":"choice","default":"left","choices":["left","right","top","bottom","four"]},"amount":{
"kind":"float","default":1,"min":0,"max":1}},"backdrop":false},"pixelate":{"order":["size"],"settings":{"size":{
"kind":"float","default":10,"min":1,"max":100},"amount":{"kind":"float","default":1,"min":0,"max":1}},
"backdrop":false},"waves":{"order":["size"],"settings":{"size":{"kind":"float","default":12,"min":0,"max":100},
"length":{"kind":"float","default":160,"min":10,"max":1000},"speed":{"kind":"float","default":0.5,"min":-5,"max":5},
"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false},"ripple":{"order":["size"],"settings":{
"size":{"kind":"float","default":8,"min":0,"max":100},"length":{"kind":"float","default":60,"min":10,"max":1000},
"speed":{"kind":"float","default":1,"min":-5,"max":5},"x":{"kind":"float","default":null,"min":0,"max":4000,
"place":true},"y":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"amount":{"kind":"float",
"default":1,"min":0,"max":1}},"backdrop":false},"wobble":{"order":["size"],"settings":{"size":{"kind":"float",
"default":14,"min":0,"max":100},"scale":{"kind":"float","default":120,"min":10,"max":1000},"speed":{"kind":"float",
"default":0.4,"min":-5,"max":5},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false},"swirl":{
"order":["angle"],"settings":{"angle":{"kind":"float","default":180,"min":-1440,"max":1440},"radius":{"kind":"float",
"default":0,"min":0,"max":2000},"x":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"y":{
"kind":"float","default":null,"min":0,"max":4000,"place":true},"amount":{"kind":"float","default":1,"min":0,"max":1}},
"backdrop":false},"fisheye":{"order":["strength"],"settings":{"strength":{"kind":"float","default":0.5,"min":-1,
"max":1},"radius":{"kind":"float","default":0,"min":0,"max":2000},"x":{"kind":"float","default":null,"min":0,
"max":4000,"place":true},"y":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"amount":{"kind":"float",
"default":1,"min":0,"max":1}},"backdrop":false},"tunnel":{"order":["speed"],"settings":{"speed":{"kind":"float",
"default":0.4,"min":-5,"max":5},"repeat":{"kind":"int","default":2,"min":1,"max":12},"depth":{"kind":"float",
"default":0.5,"min":0.05,"max":4},"x":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"y":{
"kind":"float","default":null,"min":0,"max":4000,"place":true},"amount":{"kind":"float","default":1,"min":0,"max":1}},
"backdrop":false},"tile":{"order":["across"],"settings":{"across":{"kind":"int","default":3,"min":1,"max":40},"down":{
"kind":"int","default":0,"min":0,"max":40},"flip":{"kind":"bool","default":false,"min":0,"max":1},"amount":{
"kind":"float","default":1,"min":0,"max":1}},"backdrop":false},"zoomBlur":{"order":["strength"],"settings":{
"strength":{"kind":"float","default":0.25,"min":0,"max":1},"x":{"kind":"float","default":null,"min":0,"max":4000,
"place":true},"y":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"amount":{"kind":"float",
"default":1,"min":0,"max":1}},"backdrop":false},"spinBlur":{"order":["angle"],"settings":{"angle":{"kind":"float",
"default":8,"min":-90,"max":90},"x":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"y":{
"kind":"float","default":null,"min":0,"max":4000,"place":true},"amount":{"kind":"float","default":1,"min":0,"max":1}},
"backdrop":false},"rgbSplit":{"order":["size"],"settings":{"size":{"kind":"float","default":4,"min":0,"max":60},
"angle":{"kind":"float","default":0,"min":-360,"max":360},"spread":{"kind":"bool","default":false,"min":0,"max":1},
"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false},"hue":{"order":["shift"],"settings":{
"shift":{"kind":"float","default":90,"min":-360,"max":360},"speed":{"kind":"float","default":0,"min":-720,"max":720},
"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false},"saturate":{"order":["strength"],"settings":{
"strength":{"kind":"float","default":1.6,"min":0,"max":4},"amount":{"kind":"float","default":1,"min":0,"max":1}},
"backdrop":false},"brighten":{"order":["strength"],"settings":{"strength":{"kind":"float","default":1.3,"min":0,
"max":4},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false},"contrast":{"order":["strength"],
"settings":{"strength":{"kind":"float","default":1.4,"min":0,"max":4},"amount":{"kind":"float","default":1,"min":0,
"max":1}},"backdrop":false},"invert":{"order":[],"settings":{"amount":{"kind":"float","default":1,"min":0,"max":1}},
"backdrop":false},"posterize":{"order":["levels"],"settings":{"levels":{"kind":"int","default":4,"min":2,"max":16},
"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false},"tint":{"order":["colour"],"settings":{
"colour":{"kind":"colour","default":"gold"},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false},
"duotone":{"order":["dark","light"],"settings":{"dark":{"kind":"colour","default":"midnightblue"},"light":{
"kind":"colour","default":"gold"},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false},
"colourCycle":{"order":["palette"],"settings":{"palette":{"kind":"palette","default":"rainbow"},"speed":{
"kind":"float","default":0.3,"min":-5,"max":5},"bands":{"kind":"float","default":1,"min":0.1,"max":8},"amount":{
"kind":"float","default":1,"min":0,"max":1}},"backdrop":false},"scanlines":{"order":["strength"],"settings":{
"strength":{"kind":"float","default":0.5,"min":0,"max":1},"size":{"kind":"float","default":3,"min":1,"max":40},
"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false},"crt":{"order":["curve"],"settings":{
"curve":{"kind":"float","default":0.18,"min":0,"max":1},"lines":{"kind":"float","default":0.45,"min":0,"max":1},
"size":{"kind":"float","default":3,"min":1,"max":40},"amount":{"kind":"float","default":1,"min":0,"max":1}},
"backdrop":false},"glitch":{"order":["strength"],"settings":{"strength":{"kind":"float","default":0.5,"min":0,"max":1}
,"speed":{"kind":"float","default":1,"min":0,"max":10},"seed":{"kind":"int","default":1,"min":0,"max":9999},"amount":{
"kind":"float","default":1,"min":0,"max":1}},"backdrop":false},"grain":{"order":["strength"],"settings":{"strength":{
"kind":"float","default":0.18,"min":0,"max":1},"size":{"kind":"float","default":1.5,"min":0.5,"max":20},"seed":{
"kind":"int","default":1,"min":0,"max":9999},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false},
"vignette":{"order":["strength"],"settings":{"strength":{"kind":"float","default":0.6,"min":0,"max":1},"size":{
"kind":"float","default":0.75,"min":0,"max":2},"colour":{"kind":"colour","default":"black"},"amount":{"kind":"float",
"default":1,"min":0,"max":1}},"backdrop":false},"edges":{"order":["strength"],"settings":{"strength":{"kind":"float",
"default":2,"min":0,"max":10},"size":{"kind":"float","default":1.5,"min":0.5,"max":20},"fill":{"kind":"float",
"default":0,"min":0,"max":1},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false},"dots":{
"order":["size"],"settings":{"size":{"kind":"float","default":9,"min":2,"max":100},"angle":{"kind":"float",
"default":25,"min":-360,"max":360},"paper":{"kind":"colour","default":"black"},"amount":{"kind":"float","default":1,
"min":0,"max":1}},"backdrop":false},"letters":{"order":["size"],"settings":{"size":{"kind":"float","default":10,
"min":4,"max":100},"colour":{"kind":"colour","default":"white"},"own":{"kind":"bool","default":true,"min":0,"max":1},
"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false},"plasma":{"order":["palette"],"settings":{
"palette":{"kind":"palette","default":"sunset"},"speed":{"kind":"float","default":0.3,"min":-5,"max":5},"scale":{
"kind":"float","default":1,"min":0.1,"max":10},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":true}
,"starfield":{"order":["speed"],"settings":{"speed":{"kind":"float","default":0.5,"min":-5,"max":5},"stars":{
"kind":"float","default":1,"min":0,"max":4},"colour":{"kind":"colour","default":"white"},"x":{"kind":"float",
"default":null,"min":0,"max":4000,"place":true},"y":{"kind":"float","default":null,"min":0,"max":4000,"place":true},
"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":true},"metaballs":{"order":["palette"],"settings":{
"palette":{"kind":"palette","default":"neon"},"speed":{"kind":"float","default":0.5,"min":-5,"max":5},"count":{
"kind":"int","default":7,"min":1,"max":12},"size":{"kind":"float","default":1,"min":0.2,"max":4},"amount":{
"kind":"float","default":1,"min":0,"max":1}},"backdrop":true},"flow":{"order":["palette"],"settings":{"palette":{
"kind":"palette","default":"ocean"},"speed":{"kind":"float","default":0.2,"min":-5,"max":5},"scale":{"kind":"float",
"default":1,"min":0.1,"max":10},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":true},"blur":{
"order":["radius"],"settings":{"radius":{"kind":"float","default":8,"min":0,"max":200},"amount":{"kind":"float",
"default":1,"min":0,"max":1}},"backdrop":false},"glow":{"order":["strength"],"settings":{"strength":{"kind":"float",
"default":0.8,"min":0,"max":4},"threshold":{"kind":"float","default":0.5,"min":0,"max":1},"radius":{"kind":"float",
"default":24,"min":2,"max":200},"amount":{"kind":"float","default":1,"min":0,"max":1}},"backdrop":false},"trails":{
"order":["length"],"settings":{"length":{"kind":"float","default":0.5,"min":0,"max":20},"zoom":{"kind":"float",
"default":1,"min":0.1,"max":10},"spin":{"kind":"float","default":0,"min":-720,"max":720},"hue":{"kind":"float",
"default":0,"min":-720,"max":720},"dx":{"kind":"float","default":0,"min":-2000,"max":2000},"dy":{"kind":"float",
"default":0,"min":-2000,"max":2000},"x":{"kind":"float","default":null,"min":0,"max":4000,"place":true},"y":{
"kind":"float","default":null,"min":0,"max":4000,"place":true},"amount":{"kind":"float","default":1,"min":0,"max":1}},
"backdrop":false}},"looks":["dream","arcade","vhs","neon","comic","underwater","oldfilm","disco","terminal"],
"palettes":["rainbow","fire","ocean","sunset","neon","candy","forest","ice","lava","mono"],"aliases":{"bloom":"glow",
"colorCycle":"colourCycle","bulge":"fisheye","halftone":"dots"}}""")
# EFFECTS:END
_EFFECTS = _TABLE["effects"]
_source = [None]


def _snake(name):
    return re.sub(r"[A-Z]", lambda m: "_" + m.group(0).lower(), name)


def _camel(name):
    return re.sub(r"_([a-z])", lambda m: m.group(1).upper(), name)


# Python's spelling of a setting: colour or color, and `from_` where a word is Python's own.
_SPELLING = {"color": "colour", "colors": "colours"}


def _key(name):
    name = _camel(name.rstrip("_"))
    return _SPELLING.get(name, name)


def _library():
    """The page's half as text that can be made into a function: a page is given no file to load."""
    if _source[0] is None:
        with open(os.path.join(_HERE, "web", "vfx.js"), encoding="utf-8") as f:
            _source[0] = f.read().replace("export {", "return {")
    return _source[0]


class _Run:
    """One run of a scene: its page, and the effects made in it."""

    def __init__(self, js=None):
        self.js = js
        self.api = None
        self.next_id = 1
        self.bands = [0.0, 0.0, 0.0, 0.0, 0.0]
        self.hearing = False
        self.dt = None


_run = _Run()


def _pyctures():
    # Looked up each time: in a browser every scene has its own copy of the module.
    module = sys.modules.get("pyctures")
    if module is None:
        import pyctures as module
    return module


def _page():
    """The page's effects for the scene that is running, made the first time one is wanted."""
    global _run
    p = _pyctures()
    # A new run has a new `js`: what was made for the last run is gone with its page.
    if _run.js is not p.js:
        _run = _Run(p.js)
        handle = getattr(p, "H_EFFECTS", None)
        if handle is not None:
            _run.api = p.JsRef(handle)      # a Pyctures that has the effects built in
        else:
            lib = p.js.Function(_library())()
            _run.api = lib.effects(p.canvas, {"fresh": True, "manual": True})
        # The effects are run once for every frame Python sends, after its drawing, on Python's clock.
        ending = getattr(getattr(p, "S", None), "ending", None)
        if isinstance(ending, list):
            ending.append(_frame)
        _watch_dt(p)
    return _run.api


def _watch_dt(p):
    """The seconds each frame is given (what update(dt) is told). A Pyctures that keeps it says so with S.dt;
    one that does not is listened to where it hands dt to the scene's functions."""
    call = getattr(p, "_call_frame_functions", None)
    if hasattr(getattr(p, "S", None), "dt") or call is None or getattr(call, "_vfx", False):
        return

    def frame_functions(dt):
        _run.dt = dt
        return call(dt)
    frame_functions._vfx = True
    p._call_frame_functions = frame_functions


def _frame():
    """As a frame is sent: the last command in it runs the effects over what the frame drew."""
    p = _pyctures()
    if _run.js is not p.js or _run.api is None:
        return
    dt = getattr(p.S, "dt", None)
    if not isinstance(dt, (int, float)):
        dt = _run.dt
    # A frame that is not one of the clock's (the page asked for a picture again) moves nothing on.
    _run.dt = None
    if isinstance(dt, (int, float)) and dt > 0:
        _run.api.frame(dt)


def _told(bands):
    _run.bands = [float(b) for b in bands]
    _run.api.ack()


def _in_page(target):
    """The target as an object in the page, when that is where it lives; else None."""
    if target is None:
        return None
    if hasattr(type(target), "_enc"):
        return target
    page = getattr(target, "page", None)
    if callable(page) and not hasattr(type(page), "_enc"):
        page = page()
    return page if hasattr(type(page), "_enc") else None


class Effect:
    """What Python keeps of an effect that is on in the page. Its settings are plain attributes."""

    def __init__(self, kind, settings, values, args):
        api = _page()
        object.__setattr__(self, "_kind", kind)
        object.__setattr__(self, "_settings", settings)
        object.__setattr__(self, "_values", values)
        object.__setattr__(self, "active", True)
        object.__setattr__(self, "_id", _run.next_id)
        _run.next_id += 1
        api.make(kind, self._id, args)

    @property
    def name(self):
        return self._kind

    @property
    def settings(self):
        return list(self._settings)

    def _setting(self, name):
        key = _key(name)
        if key not in self._settings:
            raise AttributeError("%s has no setting called %r. Its settings are %s"
                                 % (_snake(self._kind), name, ", ".join(_snake(s) for s in self._settings)))
        return key

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return self._values.get(self._setting(name))

    def __setattr__(self, name, value):
        self.set(name, value)

    def set(self, name, value):
        """Change a setting: effect.set("segments", 12) is effect.segments = 12."""
        key = self._setting(name)
        _check(self._kind, key, self._settings[key], value)
        self._values[key] = value
        _page().set(self._id, key, value)

    def get(self, name):
        return self._values.get(self._setting(name))

    def describe(self, name):
        """What a dial needs to know of a setting: its range, its kind, where it starts."""
        key = self._setting(name)
        s = self._settings[key]
        d = {"name": _snake(key), "kind": "text" if s["kind"] in ("colour", "palette") else s["kind"], "default": s.get("default")}
        for k in ("min", "max", "choices"):
            if k in s:
                d[k] = s[k]
        return d

    def on(self):
        object.__setattr__(self, "active", True)
        _page().call(self._id, "on")
        return self

    def off(self):
        object.__setattr__(self, "active", False)
        _page().call(self._id, "off")
        return self

    def remove(self):
        """Take it off the scene for good."""
        object.__setattr__(self, "active", False)
        _page().call(self._id, "remove")

    def __repr__(self):
        return "<%s %s>" % (_snake(self._kind), ", ".join("%s=%r" % (_snake(k), v) for k, v in self._values.items() if k != "amount"))


def _check(kind, key, s, value):
    """A wrong value is said here, in Python, on the line that gave it: the page would say it a frame later."""
    name, what = _snake(kind), _snake(key)
    k = s["kind"]
    if k == "choice":
        if value not in s["choices"]:
            raise ValueError("%s's %s is one of %s, not %r" % (name, what, ", ".join('"%s"' % c for c in s["choices"]), value))
    elif k == "palette":
        if isinstance(value, str) and value.lower() not in _TABLE["palettes"]:
            raise ValueError('There is no palette called "%s". There are %s, or give a list of colours: ["navy", "magenta", "gold"]'
                             % (value, ", ".join(_TABLE["palettes"])))
    elif k == "colour":
        if not isinstance(value, (str, list, tuple)):
            raise ValueError("%s's %s is a colour (\"gold\", \"#ff8800\"), not %r" % (name, what, value))
    elif k == "bool":
        pass
    elif value is None and s.get("place"):
        pass
    elif isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("%s's %s is a number, not %r" % (name, what, value))


def _maker(kind):
    spec = _EFFECTS[kind]
    order, settings = spec["order"], spec["settings"]

    def make(*args, **options):
        if len(args) > len(order):
            raise TypeError("%s() was given %d values and takes %s. Its other settings go in by name: %s(%s)" % (
                _snake(kind), len(args), "%d (%s)" % (len(order), ", ".join(order)) if order else "none", _snake(kind),
                ", ".join("%s=…" % _snake(n) for n in list(settings)[len(order):len(order) + 2])))
        given = dict(zip(order, args))
        for name, value in options.items():
            key = _key(name)
            if key not in settings:
                raise TypeError("%s has no setting called %r. Its settings are %s" % (_snake(kind), name, ", ".join(_snake(s) for s in settings)))
            given[key] = value
        for key, value in given.items():
            _check(kind, key, settings[key], value)
        values = {k: s.get("default") for k, s in settings.items()}
        values.update(given)
        return Effect(kind, settings, values, [given])

    make.__name__ = _snake(kind)
    shown = ", ".join("%s=%r" % (_snake(k), s.get("default")) for k, s in settings.items() if k != "amount")
    make.__doc__ = "Turn %s on: %s(%s). It gives the effect back: its settings are attributes, and it has off(), on() and remove()." % (
        _snake(kind), _snake(kind), shown)
    return make


__all__ = []
for _kind in _EFFECTS:
    globals()[_snake(_kind)] = _maker(_kind)
    __all__.append(_snake(_kind))
for _alias, _kind in _TABLE["aliases"].items():
    globals()[_snake(_alias)] = globals()[_snake(_kind)]
    __all__.append(_snake(_alias))


class Look:
    """Several effects turned on together: look("dream")."""

    def __init__(self, name, amount):
        api = _page()
        self.name = name
        self._amount = amount
        self._id = _run.next_id
        _run.next_id += 1
        api.make("look", self._id, [name, amount])

    @property
    def amount(self):
        return self._amount

    @amount.setter
    def amount(self, value):
        self._amount = value
        _page().set(self._id, "amount", value)

    def on(self):
        _page().call(self._id, "on")
        return self

    def off(self):
        _page().call(self._id, "off")
        return self

    def remove(self):
        _page().call(self._id, "remove")


def look(name, amount=1):
    """Several effects at once: look("dream"), look("arcade"), look("vhs"). The names: look_names()."""
    key = re.sub(r"[\s_-]", "", str(name).lower())
    if key not in _TABLE["looks"]:
        raise ValueError('There is no look called "%s". There are %s' % (name, ", ".join(_TABLE["looks"])))
    return Look(key, amount)


def shader(source, **settings):
    """Your own effect, from a program for the graphics card that has `vec4 effect(vec2 uv)`: the colour at one
    place of the picture. Settings by name are numbers it can use: shader(source, speed=2). A mistake in it is
    said by the page, with its line."""
    if not isinstance(source, str) or not re.search(r"\beffect\s*\(", source):
        raise ValueError('shader() takes a program that has a function `vec4 effect(vec2 uv)`: the colour at one place of the picture. '
                         'For example: shader("vec4 effect(vec2 uv) { return texture(picture, uv).bgra; }")')
    table = {k: {"kind": "colour" if isinstance(v, str) else "bool" if isinstance(v, bool) else "float", "default": v} for k, v in settings.items()}
    table["amount"] = {"kind": "float", "default": 1}
    values = dict(settings, amount=1)
    return Effect("shader", table, values, [source, {k: (list(v) if isinstance(v, tuple) else v) for k, v in settings.items()}])


def clear_effects():
    """Take every effect off the scene."""
    _page().clearEffects()


def listen_to(target):
    """What the music is taken from: sound_output(), a synth, a song or the microphone (anything that makes its
    sound in the page). None stops listening."""
    api = _page()
    if target is None:
        api.listen(None)
        return
    page = _in_page(target)
    if page is None:
        raise ValueError("listen_to() is given something that makes sound in the page: sound_output(), or a synth from make_synth()")
    api.listen(page)


_BANDS = ("bass", "mids", "highs", "loudness", "pulse")


def react(effect, setting, band="loudness", low=None, high=None, **given):
    """Tie a setting to the music: react(shine, "strength", "bass", 0.3, 1.2) makes the glow 0.3 when there is
    no bass and 1.2 when there is all of it. The bands: bass, mids, highs, loudness, pulse. It is done in the
    page, on the beat."""
    if not isinstance(effect, Effect):
        raise ValueError('react() is given an effect, the name of one of its settings and what to follow: react(shine, "strength", "bass")')
    key = effect._setting(setting)
    which = {"level": "loudness", "beat": "pulse"}.get(str(band).lower(), str(band).lower())
    if which not in _BANDS:
        raise ValueError('"%s" is not something the music has. There are %s' % (band, ", ".join(_BANDS)))
    low = given.get("from_", given.get("start", low))
    high = given.get("to", given.get("end", high))
    span = {}
    if low is not None:
        span["from"] = low
    if high is not None:
        span["to"] = high
    _page().react(effect._id, key, which, span)
    return effect


def _band(i):
    def read():
        api = _page()
        if not _run.hearing:
            _run.hearing = True
            api.report(_told)
        return _run.bands[i]
    read.__name__ = _BANDS[i]
    read.__doc__ = "The music's %s, from 0 to 1, as the page last told it (a frame ago). For a setting that must be on the beat, use react()." % _BANDS[i]
    return read


bass, mids, highs, loudness, pulse = (_band(i) for i in range(5))


def effects_quality(value):
    """How many of the picture's pixels the effects work on: 1 is all, 0.5 is half each way, "auto" lets the device decide."""
    if value != "auto" and not (isinstance(value, (int, float)) and value > 0):
        raise ValueError('effects_quality() is given a number from 0.25 to 1, or "auto"')
    _page().effectsQuality(value)


def look_names():
    return list(_TABLE["looks"])


def effect_names():
    return [_snake(k) for k in _EFFECTS]


def palette_names():
    return list(_TABLE["palettes"])


__all__ += ["shader", "look", "clear_effects", "listen_to", "react", "bass", "mids", "highs", "loudness", "pulse",
            "effects_quality", "look_names", "effect_names", "palette_names"]
