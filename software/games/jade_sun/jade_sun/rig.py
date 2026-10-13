"""Low-poly rig helpers shared by every art module.

Screen pixels throughout. f is facing (+1 right, -1 left); template x is mirrored about the
origin when f < 0. Light comes from above, so shading is mirror-safe: highlights on top
facets, crescent shadows on the underside.

Cost notes for the device: every call here is one PicoGraphics primitive. triangle, rectangle
and circle with small ints allocate nothing; polygon builds a list, so keep it to a few per
moving sprite and cache templates rather than rebuilding them each frame.
"""
import math
from .hw import display

_NG = {}
_SIN = [math.sin(i * math.pi / 32) for i in range(64)]


def sin64(a):
    """Sine of a 64-step angle (0..63 is one turn). Cheap for animation cycles."""
    return _SIN[int(a) & 63]


def cos64(a):
    return _SIN[(int(a) + 16) & 63]


def poly(pts, ox, oy, f=1):
    """Template polygon pts ((x, y), ...) placed at ox, oy and mirrored when f < 0."""
    display.polygon([(ox + f * x, oy + y) for x, y in pts])


def tri(ox, oy, f, x0, y0, x1, y1, x2, y2):
    """Mirrored triangle from template coords."""
    display.triangle(ox + f * x0, oy + y0, ox + f * x1, oy + y1, ox + f * x2, oy + y2)


def joint(x, y, ang, ln):
    """End point of a bone of length ln from (x, y) at angle ang (radians, 0 = right, +y down)."""
    return x + math.cos(ang) * ln, y + math.sin(ang) * ln


def limb(x, y, ang, ln, w0, w1=None):
    """Tapered bone drawn as one quad; returns the end joint for chaining (articulation).

    hip = (x, y); knee = limb(*hip, a1, 6, 3, 2); foot = limb(*knee, a1 + a2, 5, 2, 2)
    """
    if w1 is None:
        w1 = w0
    c, s = math.cos(ang), math.sin(ang)
    ex, ey = x + c * ln, y + s * ln
    nx, ny = -s * 0.5, c * 0.5
    display.polygon([(int(x + nx * w0), int(y + ny * w0)), (int(ex + nx * w1), int(ey + ny * w1)),
                     (int(ex - nx * w1), int(ey - ny * w1)), (int(x - nx * w0), int(y - ny * w0))])
    return ex, ey


def ngon_pts(r, n, rot=0.0):
    """Cached offsets of a regular n-gon of radius r (rot in radians)."""
    k = (r, n, int(rot * 100))
    pts = _NG.get(k)
    if pts is None:
        pts = tuple((int(round(r * math.cos(rot + i * 6.2832 / n))), int(round(r * math.sin(rot + i * 6.2832 / n))))
                    for i in range(n))
        _NG[k] = pts
    return pts


def ngon(cx, cy, r, n=6, rot=0.0):
    """Faceted disc: the low-poly stand-in for a circle."""
    display.polygon([(cx + x, cy + y) for x, y in ngon_pts(r, n, rot)])


def crescent(cx, cy, r, depth, shadow, body):
    """Round body with a crescent shadow on the underside: 2 primitives.

    depth is the shadow thickness at the bottom (1..r//2)."""
    display.set_pen(shadow)
    display.circle(cx, cy, r)
    display.set_pen(body)
    display.circle(cx, cy - depth // 2, r - (depth + 1) // 2)


def gem(cx, cy, r, lit, mid, dark, n=6):
    """Faceted ball: mid n-gon, dark lower facet, lit upper facet. 3 primitives."""
    display.set_pen(mid)
    ngon(cx, cy, r, n, -1.5708)
    display.set_pen(dark)
    display.triangle(cx - r + 1, cy + 1, cx + r - 1, cy + 1, cx, cy + r)
    display.set_pen(lit)
    display.triangle(cx - r // 2, cy - r // 3, cx + r // 2, cy - r // 3, cx, cy - r + 1)
