"""
Alphabetic Variables

To grab all a, b, c, ... variables::

   >>> from pyeda.alphas import *
"""

import string

from pyeda.expr import exprvar

(a, b, c, d, e, f, g, h, i, j, k, l, m,
 n, o, p, q, r, s, t, u, v, w, x, y, z) = map(exprvar, string.ascii_lowercase)
