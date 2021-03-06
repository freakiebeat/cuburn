#!/usr/bin/env python2

import base64
import binascii
import warnings
import xml.parsers.expat
import numpy as np

from variations import var_params
import util

# Re-exported, since it makes the namespace nice and regular
from blend import node_to_anim, edge_to_anim
from util import json_encode as to_json

class XMLGenomeParser(object):
    """
    Parse an XML genome into a list of dictionaries.
    """
    def __init__(self):
        self.flames = []
        self._flame = None
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.StartElementHandler = self.start_element
        self.parser.EndElementHandler = self.end_element

    def start_element(self, name, attrs):
        if name == 'flame':
            assert self._flame is None
            self._flame = dict(attrs)
            self._flame['xforms'] = []
            if attrs.get('palette'):
                pal = XMLPaletteParser.lookup(int(attrs['palette']))
            else:
                pal = np.ones((256, 4), dtype=np.float32)
            self._flame['palette'] = pal
        elif name == 'xform':
            if 'color' in attrs:
                # Color sometimes has an extra param that is unused by flam3
                attrs['color'] = attrs['color'].strip().split()[0]
            self._flame['xforms'].append(dict(attrs))
            self._flame['xforms']
        elif name == 'finalxform':
            self._flame['finalxform'] = dict(attrs)
        elif name == 'color':
            idx = int(attrs['index'])
            self._flame['palette'][idx][:3] = [float(v) / 255.0
                                               for v in attrs['rgb'].split()]
        elif name == 'symmetry':
            self._flame['symmetry'] = int(attrs['kind'])
    def end_element(self, name):
        if name == 'flame':
            self.flames.append(self._flame)
            self._flame = None

    @classmethod
    def parse(cls, src):
        parser = cls()
        parser.parser.Parse(src, True)
        return parser.flames

class XMLPaletteParser(object):
    _names, _numbers = None, None

    _locations = [
            '/usr/local/share/flam3/flam3-palettes.xml',
            '/usr/share/flam3/flam3-palettes.xml',
        ]

    def __init__(self, src):
        self.names, self.numbers = {}, {}
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.StartElementHandler = self.start_element
        self.parser.EndElementHandler = self.end_element
        self.parser.Parse(src, True)

    def start_element(self, name, attrs):
        if name == 'palette':
            data = binascii.a2b_hex(
                    attrs['data'].replace('\n', '').replace(' ', ''))
            pal = np.fromstring(data, 'u1').reshape((256, 4)) / 255.0
            if 'number' in attrs:
                self.numbers[int(attrs['number'])] = pal
            if 'name' in attrs:
                self.names[attrs['name']] = pal

    def end_element(self, name):
        pass

    @classmethod
    def _load(cls):
        src = None
        for loc in cls._locations:
            try:
                with open(loc) as fp:
                    src = fp.read()
                break
            except:
                pass
        if not src:
            raise IOError("Couldn't find a palettes XML file")
        parser = cls(src)
        cls._names, cls._numbers = parser.names, parser.numbers

    @classmethod
    def lookup(cls, key, isname=False):
        if not cls._names:
            cls._load()
        if isname:
            return np.array(cls._names[key])
        else:
            return np.array(cls._numbers[key])

def convert_affine(aff, animate=False):
    xx, yx, xy, yy, xo, yo = vals = map(float, aff.split())
    if vals == [1, 0, 0, 1, 0, 0]: return None

    # Cuburn's IFS-space vertical direction is inverted with respect to flam3,
    # so we invert all instances of y. (``yy`` is effectively inverted twice.)
    yx, xy, yo = -yx, -xy, -yo

    xa = np.degrees(np.arctan2(yx, xx))
    ya = np.degrees(np.arctan2(yy, xy))
    xm = np.hypot(xx, yx)
    ym = np.hypot(xy, yy)
    spread = ((ya - xa) % 360) / 2
    angle = (xa + spread) % 360
    return dict(spread=spread, magnitude={'x': xm, 'y': ym},
                angle=angle, offset={'x': xo, 'y': yo})

def convert_vars(xf):
    struct = lambda k, ps: ([('weight', k, float)] +
            [(p, k+'_'+p, float) for p in ps])
    return dict([(k, apply_structure(struct(k, ps), xf))
                 for k, ps in var_params.items() if k in xf])

def convert_xform(xf):
    out = apply_structure(xform_structure, xf)

    # Deprecated symmetry arg makes this too much of a bother to handle within
    # the structure framework
    symm = float(xf.get('symmetry', 0))
    anim = xf.get('animate', symm <= 0)
    if 'symmetry' in xf:
        out.setdefault('color_speed', (1-symm)/2)
    if anim and 'pre_affine' in out:
        out['pre_affine']['angle'] = [out['pre_affine']['angle'], -360]
    return out

def make_symm_xforms(kind, offset):
    assert kind != 0, 'Pick your own damn symmetry.'
    out = []
    boring_xf = dict(color=1, color_speed=0, weight=1,
                     variations={'linear': {'weight': 1}})
    if kind < 0:
        out.append(boring_xf.copy())
        out[-1]['pre_affine'] = dict(angle=135, spread=-45)
        kind = -kind
    for i in range(1, kind):
        out.append(boring_xf.copy())
        if kind >= 3:
            out[-1]['color'] = (i - 1) / (kind - 2.0)
        ang = (45 + 360 * i / float(kind)) % 360
        out[-1]['pre_affine'] = dict(angle=ang, spread=-45)
    return dict(enumerate(out, offset))

def convert_xforms(flame):
    xfs = dict(enumerate(map(convert_xform, flame['xforms'])))
    if 'symmetry' in flame:
        xfs.update(make_symm_xforms(flame['symmetry'], len(xfs)))
    return xfs

pair = lambda v: dict(zip('xy', map(float, v.split())))

xform_structure = (
    ('pre_affine',  'coefs', convert_affine),
    ('post_affine', 'post', convert_affine),
    ('color',       'color', float),
    ('color_speed', 'color_speed', float),
    ('opacity',     'opacity', float),
    ('weight',      'weight', float),
    ('chaos',       'chaos',
     lambda s: dict(enumerate(map(float, s.split())))),
    ('variations',  convert_vars)
)

# A list of either three-tuples (dst, src, cvt_val), or two-tuples
# (dst, cvt_dict) for properties that are built from multiple source keys.
# If a function returns 'None', its key is dropped from the result.
flame_structure = (
    ('author.name',             'nick', str),
    ('author.url',              'url',  lambda s: 'http://' + str(s)),
    ('name',                    'name', str),

    ('camera.center',           'center', pair),
    ('camera.rotation',         'rotate', float),
    ('camera.dither_width',     'filter', float),
    ('camera.scale',
     lambda d: float(d['scale']) / float(d['size'].split()[0])),

    ('filters.colorclip.gamma',             'gamma', float),
    ('filters.colorclip.gamma_threshold',   'gamma_threshold', float),
    ('filters.colorclip.highlight_power',   'highlight_power', float),
    ('filters.colorclip.vibrance',          'vibrancy', float),

    ('filters.de.curve',    'estimator_curve', float),
    ('filters.de.radius',   'estimator_radius', float),
    ('filters.de.minimum',
     lambda d: (float(d['estimator_minimum']) /
                float(d.get('estimator_radius', 11)))
               if 'estimator_minimum' in d else None),

    ('filters.logscale.brightness',         'brightness', float),

    ('palette',     'palette', util.palette_encode),
    ('xforms',      convert_xforms),
    ('final_xform', 'finalxform', convert_xform),
)

def apply_structure(struct, src):
    out = {}
    for l in struct:
        if len(l) == 2:
            v = l[1](src)
        else:
            v = l[2](src[l[1]]) if l[1] in src else None
        if v is not None:
            out[l[0]] = v
    return out

def flam3_to_node(flame):
    n = util.unflatten(util.flatten(apply_structure(flame_structure, flame)))
    n['type'] = 'node'
    return n

def nodes_from_xml_path(path):
    """Quick one-shot conversion for an XML genome."""
    flames = XMLGenomeParser.parse(open(path).read())
    if len(flames) > 10:
        warnings.warn("Lot of flames in this file. Sure it's not a "
                      "frame-based animation?")
    for flame in flames:
        yield flam3_to_node(flame)

if __name__ == "__main__":
    import sys
    print '\n\n'.join(map(to_json, nodes_from_xml_path(sys.argv[1])))
