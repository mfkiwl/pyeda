"""
Boolean Logic Expressions

Interface Functions:
    var
    comp

    factor

    f_not, f_or, f_nor, f_and, f_nand, f_xor, f_xnor

    cube_sop
    cube_pos
    iter_space
    iter_points

Interface Classes:
    Expression
        Literal
        OrAnd
            Or
            And
        BufNot
            Buf
            Not
        Exclusive
            Xor
            Xnor
"""

__copyright__ = "Copyright (c) 2012, Chris Drake"

from .common import bit_on, cached_property

from .boolfunc import Variable, Function

VARIABLES = dict()
COMPLEMENTS = dict()

def var(name, index=None):
    """Return a single variable expression."""
    try:
        ret = VARIABLES[(name, index)]
    except KeyError:
        ret = _Variable(name, index)
        VARIABLES[(name, index)] = ret
    return ret

def comp(var):
    """Return a single complement expression."""
    try:
        ret = COMPLEMENTS[var]
    except KeyError:
        ret = _Complement(var)
        COMPLEMENTS[var] = ret
    return ret

def factor(expr):
    """Return a factored expression."""
    return expr.factor()

# factored operators
def f_not(x):
    return Not(x).factor()

def f_or(*args):
    return Or(*args).factor()

def f_nor(*args):
    return Not(Or(*args)).factor()

def f_and(*args):
    return And(*args).factor()

def f_nand(*args):
    return Not(And(*args)).factor()

def f_xor(*args):
    return Xor(*args).factor()

def f_xnor(*args):
    return Xnor(*args).factor()

def cube_sop(vs):
    """
    Return the multi-dimensional space spanned by N Boolean variables as a
    sum of products.
    """
    points = [p for p in iter_points(And, vs)]
    return Or(*points)

def cube_pos(vs):
    """
    Return the multi-dimensional space spanned by N Boolean variables as a
    product of sums.
    """
    points = [p for p in iter_points(Or, vs)]
    return And(*points)

def iter_space(vs):
    """Return the multi-dimensional space spanned by N Boolean variables."""
    for n in range(2 ** len(vs)):
        yield tuple((v if bit_on(n, i) else -v) for i, v in enumerate(vs))

def iter_points(op, vs):
    """
    Iterate through all OR/AND points in the multi-dimensional space spanned
    by N Boolean variables.
    """
    if not issubclass(op, OrAnd):
        raise TypeError("iter_points() expected op type OR/AND")
    for space in iter_space(vs):
        yield op(*space)


class Expression(Function):
    """Boolean function represented by a logic expression"""

    SOP, POS = range(2)

    # From Function
    @cached_property
    def support(self):
        return {v for v in self.iter_vars()}

    def op_not(self):
        return Not(self)

    def op_or(self, *args):
        return Or(self, *args)

    def op_nor(self, *args):
        return Not(Or(self, *args))

    def op_and(self, *args):
        return And(self, *args)

    def op_nand(self, *args):
        return Not(And(self, *args))

    def op_xor(self, *args):
        return Xor(self, *args)

    def op_xnor(self, *args):
        return Xnor(self, *args)

    def op_le(self, *args):
        return self if len(args) == 0 else _le(self, *args)

    def op_ge(self, *args):
        return self if len(args) == 0 else _ge(self, *args)

    def is_neg_unate(self, vs=None):
        if vs is None:
            vs = self.support
        for v in vs:
            fv0, fv1 = self.cofactors([v])
            if fv0 in {0, 1} or fv1 in {0, 1}:
                if not (fv0 == 1 or fv1 == 0):
                    return False
            # FIXME -- broken
            elif not (fv0.minterms >= fv1.minterms):
                return False
        return True

    def is_pos_unate(self, vs=None):
        if vs is None:
            vs = self.support
        for v in vs:
            fv0, fv1 = self.cofactors([v])
            if fv0 in {0, 1} or fv1 in {0, 1}:
                if not (fv1 == 1 or fv0 == 0):
                    return False
            # FIXME -- broken
            elif not (fv1.minterms >= fv0.minterms):
                return False
        return True

    def smoothing(self, *vs):
        return Or(*self.cofactors(vs))

    def consensus(self, *vs):
        return And(*self.cofactors(vs))

    def derivative(self, *vs):
        return Xor(*self.cofactors(vs))

    # Specific to Expression
    def __lt__(self, other):
        """Implementing this function makes expressions sortable."""
        raise NotImplementedError()

    def __repr__(self):
        """Return a printable representation."""
        return self.__str__()

    def __iter__(self):
        return iter(self.args)

    def __len__(self):
        return len(self.args)

    @property
    def depth(self):
        """The number of levels in the expression tree."""
        raise NotImplementedError()

    def invert(self):
        """Return an inverted expression."""
        raise NotImplementedError()

    #def iter_outputs(self):
    #    for n in range(2 ** abs(self)):
    #        d = {v: bit_on(n, i) for i, v in enumerate(self.inputs)}
    #        yield self.restrict(d)

    def factor(self):
        """Return a factored expression.

        A factored expression is one and only one of the following:
        * A literal.
        * A sum / product of factored expressions.
        """
        raise NotImplementedError()

    @cached_property
    def inputs(self):
        """Return the support set in name/index order."""
        return sorted(self.support)

    def iter_vars(self):
        """Recursively iterate through all variables in the expression."""
        raise NotImplementedError()

    def iter_minterms(self):
        """Iterate through the sum of products of N literals."""
        for n in range(2 ** self.degree):
            d = dict()
            space = list()
            for i, v in enumerate(self.inputs):
                on = bit_on(n, i)
                d[v] = on
                space.append(v if on else -v)
            output = self.restrict(d)
            if output:
                yield And(*space)

    def iter_maxterms(self):
        """Iterate through the product of sums of N literals."""
        for n in range(2 ** self.degree):
            d = dict()
            space = list()
            for i, v in enumerate(self.inputs):
                on = bit_on(n, i)
                d[v] = on
                space.append(-v if on else v)
            output = self.restrict(d)
            if not output:
                yield Or(*space)

    @cached_property
    def minterms(self):
        """The sum of products of N literals"""
        return {term for term in self.iter_minterms()}

    @cached_property
    def maxterms(self):
        """The product of sums of N literals"""
        return {term for term in self.iter_maxterms()}

    def to_sop(self):
        """Return the expression as a sum of products."""
        return self.factor()._flatten(And)

    def to_pos(self):
        """Return the expression as a product of sums."""
        return self.factor()._flatten(Or)

    def to_csop(self):
        """Return the expression as a sum of products of N literals."""
        return Or(*[term for term in self.iter_minterms()])

    def to_cpos(self):
        """Return the expression as a product of sums of N literals."""
        return And(*[term for term in self.iter_maxterms()])

    def is_term(self):
        return False

    def term_index(self):
        return None

    def equals(self, other):
        """Return whether this expression is equivalent to another.

        NOTE: This algorithm uses exponential time and memory.
        """
        if self.support == other.support:
            self_idxs = {term.term_index for term in self.minterms}
            other_idxs = {term.term_index for term in other.minterms}
            return self_idxs == other_idxs
        else:
            return False

    def _get_replace(self, d):
        replace = dict()
        for i, arg in enumerate(self.args):
            new_arg = arg.restrict(d)
            if id(new_arg) != id(arg):
                replace[i] = new_arg
        return replace


class Literal(Expression):
    """An instance of a variable or of its complement"""

    # From Expression
    @property
    def depth(self):
        return 0

    def factor(self):
        return self

    # Specific to Literal
    @property
    def args(self):
        return {self}

    def is_term(self):
        return True

    @property
    def _oidx(self):
        """Return an index for ordering comparison."""
        return (-1 if self.index is None else self.index)


class _Variable(Variable, Literal):
    """Boolean variable (expression)"""

    def __init__(self, name, index=None):
        Variable.__init__(self, name, index)
        Literal.__init__(self)

    # From Function
    def restrict(self, d):
        try:
            # FIXME -- check this input
            return int(d[self])
        except KeyError:
            return self

    def compose(self, d):
        try:
            return d[self]
        except KeyError:
            return self

    # From Expression
    def __lt__(self, other):
        if isinstance(other, Literal):
            return (self.name < other.name or
                    self.name == other.name and self._oidx < other._oidx)
        if isinstance(other, Expression):
            return True
        return id(self) < id(other)

    def invert(self):
        return comp(self)

    def iter_vars(self):
        yield self

    # Specific to _Variable
    @property
    def term_index(self):
        return 1


class _Complement(Literal):
    """Boolean complement"""

    # Postfix symbol used in string representation
    OP = "'"

    def __init__(self, var):
        self._var = var

    # From Function
    def restrict(self, d):
        try:
            # FIXME -- check this input
            return Not(int(d[self._var]))
        except KeyError:
            return self

    def compose(self, d):
        try:
            return Not(d[self._var])
        except KeyError:
            return self

    # From Expression
    def __lt__(self, other):
        if isinstance(other, _Variable):
            return (self.name < other.name or
                    self.name == other.name and self._oidx <= other._oidx)
        if isinstance(other, _Complement):
            return (self.name < other.name or
                    self.name == other.name and self._oidx < other._oidx)
        if isinstance(other, Expression):
            return True
        return id(self) < id(other)

    def invert(self):
        return self._var

    def iter_vars(self):
        yield self._var

    # Specific to _Complement
    def __str__(self):
        return str(self._var) + self.OP

    @property
    def var(self):
        return self._var

    @property
    def name(self):
        return self._var.name

    @property
    def index(self):
        return self._var.index

    @property
    def term_index(self):
        return 0


class OrAnd(Expression):
    """base class for Boolean OR/AND expressions"""

    def __new__(cls, *args):
        temps, args = list(args), list()
        while temps:
            arg = temps.pop()
            if isinstance(arg, Expression):
                # associative
                if isinstance(arg, cls):
                    temps.extend(arg.args)
                # complement
                elif -arg in args:
                    return cls.DOMINATOR
                # idempotent
                elif arg not in args:
                    args.append(arg)
            else:
                num = int(arg)
                # domination
                if num == cls.DOMINATOR:
                    return cls.DOMINATOR
                # identity
                elif num == cls.IDENTITY:
                    pass
                else:
                    raise ValueError("input not in {0, 1}: " + str(num))

        if len(args) == 0:
            return cls.IDENTITY
        if len(args) == 1:
            return args[0]

        self = super(OrAnd, cls).__new__(cls)
        self.args = args
        return self

    # From Function
    def restrict(self, d):
        replace = self._get_replace(d)
        if replace:
            args = self.args[:]
            for i, new_arg in replace.items():
                # speed hack
                if new_arg == self.DOMINATOR:
                    return self.DOMINATOR
                else:
                    args[i] = new_arg
            return self.__class__(*args)
        else:
            return self

    def compose(self, d):
        replace = self._get_replace(d)
        if replace:
            args = self.args[:]
            for i, new_arg in replace.items():
                args[i] = new_arg
            return self.__class__(*args)
        else:
            return self

    # From Expression
    def __lt__(self, other):
        if isinstance(other, Literal):
            return self.support < other.support
        if isinstance(other, self.__class__) and self.depth == other.depth == 1:
            # min/max term
            if self.support == other.support:
                return self.term_index < other.term_index
            else:
                # support containment
                if self.support < other.support:
                    return True
                if other.support < self.support:
                    return False
                # support disjoint
                v = sorted(self.support ^ other.support)[0]
                if v in self.support:
                    return True
                if v in other.support:
                    return False
        return id(self) < id(other)

    @cached_property
    def depth(self):
        return max(arg.depth + 1 for arg in self.args)

    def invert(self):
        return self.DUAL(*[Not(arg) for arg in self.args])

    def factor(self):
        return self.__class__(*[arg.factor() for arg in self.args])

    def absorb(self):
        terms, args = list(), list()
        for arg in self.args:
            if arg.is_term():
                terms.append(arg)
            else:
                args.append(arg)

        # Drop all terms that are a subset of other terms
        while terms:
            fst, rst, terms = terms[0], terms[1:], list()
            drop_fst = False
            for term in rst:
                drop_term = False
                if fst.equals(term):
                    drop_term = True
                else:
                    if all(any(farg.equals(targ) for targ in term.args)
                           for farg in fst.args):
                        drop_term = True
                    if all(any(farg.equals(targ) for targ in fst.args)
                           for farg in term.args):
                        drop_fst = True
                if not drop_term:
                    terms.append(term)
            if not drop_fst:
                args.append(fst)

        return self.__class__(*args)

    def iter_vars(self):
        for arg in self.args:
            for v in arg.iter_vars():
                yield v

    # Specific to OrAnd
    @cached_property
    def _duals(self):
        return [arg for arg in self.args if isinstance(arg, self.DUAL)]

    def _flatten(self, op):
        if isinstance(self, op):
            if self._duals:
                dual = self._duals[0]
                others = [arg for arg in self.args if arg != dual]
                expr = op.DUAL(*[op(arg, *others) for arg in dual.args])
                if isinstance(expr, OrAnd):
                    return expr._flatten(op)
                else:
                    return expr
            else:
                return self
        else:
            nested, others = list(), list()
            for arg in self.args:
                if arg.depth > 1:
                    nested.append(arg)
                else:
                    others.append(arg)
            args = [arg._flatten(op) for arg in nested] + others
            return op.DUAL(*args)

    def is_term(self):
        return self.depth == 1


class Or(OrAnd):
    """Boolean addition (or) operator"""

    # Infix symbol used in string representation
    OP = "+"

    IDENTITY = 0
    DOMINATOR = 1

    def __str__(self):
        sep = " " + self.OP + " "
        return sep.join(str(arg) for arg in sorted(self.args))

    @cached_property
    def term_index(self):
        if self.depth > 1:
            return None
        n = self.degree - 1
        idx = 0
        for i, v in enumerate(self.inputs):
            if -v in self.args:
                idx |= 1 << (n - i)
        return idx


class And(OrAnd):
    """Boolean multiplication (and) operator"""

    # Infix symbol used in string representation
    OP = "*"

    IDENTITY = 1
    DOMINATOR = 0

    def __str__(self):
        s = list()
        for arg in sorted(self.args):
            if isinstance(arg, Or):
                s.append("(" + str(arg) + ")")
            else:
                s.append(str(arg))
        sep = " " + self.OP + " "
        return sep.join(s)

    @cached_property
    def term_index(self):
        if self.depth > 1:
            return None
        n = self.degree - 1
        idx = 0
        for i, v in enumerate(self.inputs):
            if v in self.args:
                idx |= 1 << (n - i)
        return idx


Or.DUAL = And
And.DUAL = Or


class BufNot(Expression):
    """base class for BUF/NOT operators"""

    def __init__(self, arg):
        self.arg = arg

    # From Function
    def compose(self, d):
        expr = self.arg.restrict(d)
        if id(expr) == id(self.arg):
            return self
        else:
            return self.__class__(expr)

    # From Expression
    @property
    def depth(self):
        return self.arg.depth

    def iter_vars(self):
        for v in self.arg.iter_vars():
            yield v

    # Specific to BufNot
    @property
    def args(self):
        return {self.arg}


class Buf(BufNot):
    """buffer operator"""

    def __new__(cls, arg):
        # Auto-simplify numbers and literals
        if isinstance(arg, Expression):
            if isinstance(arg, Literal):
                return arg
            else:
                return super(Buf, cls).__new__(cls)
        else:
            num = int(arg)
            if num in {0, 1}:
                return num
            else:
                raise ValueError("input not in {0, 1}: " + str(num))

    def __str__(self):
        return "Buf({0.arg})".format(self)

    # From Function
    def restrict(self, d):
        arg = self.arg.restrict(d)
        # speed hack
        if arg in {0, 1}:
            return arg
        elif id(arg) == id(self.arg):
            return self
        else:
            return self.__class__(arg)

    # From Expression
    def invert(self):
        return Not(self.arg)

    def factor(self):
        return self.arg.factor()


class Not(BufNot):
    """Boolean NOT operator"""

    def __new__(cls, arg):
        # Auto-simplify numbers and literals
        if isinstance(arg, Expression):
            if isinstance(arg, Literal):
                return arg.invert()
            else:
                return super(Not, cls).__new__(cls)
        else:
            num = int(arg)
            if num in {0, 1}:
                return 1 - num
            else:
                raise ValueError("input not in {0, 1}: " + str(num))

    def __str__(self):
        return "Not({0.arg})".format(self)

    # From Function
    def restrict(self, d):
        arg = self.arg.restrict(d)
        # speed hack
        if arg in {0, 1}:
            return 1 - arg
        elif id(arg) == id(self.arg):
            return self
        else:
            return self.__class__(arg)

    # From Expression
    def invert(self):
        return self.arg

    def factor(self):
        return self.arg.invert().factor()


class Exclusive(Expression):
    """Boolean exclusive (XOR, XNOR) operator"""

    IDENTITY = 0

    def __new__(cls, *args):
        parity = cls.PARITY
        temps, args = list(args), list()
        while temps:
            arg = temps.pop()
            if isinstance(arg, Expression):
                # associative
                if isinstance(arg, cls):
                    temps.extend(arg.args)
                # XOR(x, x') = 1
                elif -arg in args:
                    args.remove(-arg)
                    parity ^= 1
                # XOR(x, x) = 0
                elif arg in args:
                    args.remove(arg)
                else:
                    args.append(arg)
            else:
                num = int(arg)
                if num in {0, 1}:
                    parity ^= num
                else:
                    raise ValueError("input not in {0, 1}: " + str(num))

        if len(args) == 0:
            return Not(cls.IDENTITY) if parity else cls.IDENTITY
        if len(args) == 1:
            return Not(args[0]) if parity else args[0]

        self = super(Exclusive, cls).__new__(cls)
        self.args = args
        self._parity = parity
        return self

    def __str__(self):
        args = ", ".join(str(arg) for arg in self.args)
        if self._parity:
            return "Xnor(" + args + ")"
        else:
            return "Xor(" + args + ")"

    # From Function
    def restrict(self, d):
        return self.compose(d)

    def compose(self, d):
        replace = self._get_replace(d)
        if replace:
            args = self.args[:]
            for i, new_arg in replace.items():
                args[i] = new_arg
            return Xnor(*args) if self._parity else Xor(*args)
        else:
            return self

    # From Expression
    @property
    def depth(self):
        return max(arg.depth + 2 for arg in self.args)

    def factor(self):
        arg, args = self.args[0], self.args[1:]
        expr = Or(And(Not(arg), Xor(*args)), And(arg, Xnor(*args)))
        if self._parity:
            return Not(expr).factor()
        else:
            return expr.factor()

    def iter_vars(self):
        for arg in self.args:
            for v in arg.iter_vars():
                yield v

class Xor(Exclusive):
    PARITY = 0

class Xnor(Exclusive):
    PARITY = 1


def _le(*args):
    if len(args) == 1:
        return args[0]
    else:
        return Or(Not(args[0]), _le(*args[1:]))

def _ge(*args):
    if len(args) == 1:
        return Not(args[0])
    else:
        return Or(args[0], _ge(*args[1:]))