""" Symbolic (N-Ary) Expression Tree

    The following script will extend the expression tree from SymPy,
    allowing direct node manipulation for subexpression replacement.
    The expression tree structure within SymPy expressions stores
    subexpressions inside immutable tuples, preventing the client from
    modifying the expression tree. Therefore, the client must depend on
    build-in functions, such as xreplace, for subexpression replacement,
    which might be suboptimal for their specific purpose. The ExprTree class
    is implemented as an n-ary tree data structure for SymPy expressions,
    equipped with a build method for constructing the expression tree,
    a reconstruct method for reconstructing the root expression, a replace
    method for subexpression replacement, and preorder/postorder traversal
    iterators (or generators). The __repr__ representation of the expression
    tree will return a string of the expressions using the preorder traversal,
    while the __str__ representation will return a string of the class name
    and root expression. The Node subclass has a field for an expression and
    a field for subexpression children (implemented as a mutable list).
"""
# Author: Ken Sible
# Email:  ksible *at* outlook *dot* com

import sys  # Standard Python module for multiplatform OS-level functions


class ExprTree:
    """Symbolic (N-Ary) Expression Tree

    >>> from sympy.abc import a, b, x
    >>> from sympy import cos
    >>> tree = ExprTree(cos(a + b)**2)
    >>> print(tree)
    ExprTree(cos(a + b)**2)
    >>> [node.expr for node in tree.preorder()]
    [cos(a + b)**2, cos(a + b), a + b, a, b, 2]
    """

    def __init__(self, expr):
        self.root = self.Node(expr, None)
        self.build(self.root)

    def build(self, node, clear=True):
        """Build expression (sub)tree.

        :arg:   root node of (sub)tree
        :arg:   clear children (default: True)

        >>> from sympy.abc import a, b
        >>> from sympy import cos, sin
        >>> tree = ExprTree(cos(a + b)**2)
        >>> tree.root.expr = sin(a*b)**2
        >>> tree.build(tree.root, clear=True)
        >>> [node.expr for node in tree.preorder()]
        [sin(a*b)**2, sin(a*b), a*b, a, b, 2]
        """
        if clear:
            del node.children[:]
        for arg in node.expr.args:
            subtree = self.Node(arg, node.expr.func)
            node.append(subtree)
            self.build(subtree)

    def preorder(self, node=None):
        """Generate iterator for preorder traversal.

        :arg:    root node of (sub)tree
        :return: iterator

        >>> from sympy.abc import a, b
        >>> from sympy import cos, Mul
        >>> tree = ExprTree(cos(a*b)**2)
        >>> for i, subtree in enumerate(tree.preorder()):
        ...     if subtree.expr.func == Mul:
        ...         print((i, subtree.expr))
        (2, a*b)
        """
        if node is None:
            node = self.root
        yield node
        for child in node.children:
            for subtree in self.preorder(child):
                yield subtree

    def postorder(self, node=None):
        """Generate iterator for postorder traversal.

        :arg:    root node of (sub)tree
        :return: iterator

        >>> from sympy.abc import a, b
        >>> from sympy import cos, Mul
        >>> tree = ExprTree(cos(a*b)**2)
        >>> for i, subtree in enumerate(tree.postorder()):
        ...     if subtree.expr.func == Mul:
        ...         print((i, subtree.expr))
        (2, a*b)
        """
        if node is None:
            node = self.root
        for child in node.children:
            for subtree in self.postorder(child):
                yield subtree
        yield node

    def reconstruct(self, evaluate=False):
        """
        Reconstruct root expression from expression tree.

        :arg:    evaluate root expression (default: False)
        :return: root expression

        >>> from sympy.abc import a, b
        >>> from sympy import cos, sin
        >>> tree = ExprTree(cos(a + b)**2)
        >>> tree.root.children[0].expr = sin(a + b)
        >>> tree.reconstruct()
        sin(a + b)**2
        """
        for subtree in self.postorder():
            if subtree.children:
                expr_list = [node.expr for node in subtree.children]
                try:
                    subtree.expr = subtree.expr.func(*expr_list, evaluate=evaluate)
                except TypeError as e:
                    subtree.expr = subtree.expr.func(*expr_list)

        return self.root.expr

    def find(self, find):
        """
        Find an expression in the tree

        :arg:    expression to be found
        :return: a generator for the matching nodes

        >>> from sympy.abc import a, b
        >>> from sympy import cos, sin
        >>> tree = ExprTree(cos(a + b)**2)
        >>> for node in tree.find(a + b):
        >>>    print(node)
        a+b
        """
        if isinstance(find, (list, tuple, set, frozenset)):
            for match in find:
                yield from self.find(match)
        else:
            if isinstance(find, ExprTree.Node):
                match = find
            elif isinstance(find, ExprTree):
                match = find.root
            else:
                match = ExprTree(find).root
            yield from self.root.find(match)

    def replace(self, find, replace=None):
        """
        Find and replace an expression in the tree

        :arg:    expression to be replaced
        :arg:    new expression to insert inplace of find
        :return: None

        >>> from sympy.abc import a, b
        >>> from sympy import cos, sin
        >>> tree = ExprTree(cos(a + b)**2)
        >>> tree.replace(a + b, a*a + b)
        >>> tree.reconstruct()
        sin(a**2 + b)**2
        """
        if isinstance(find, (list, set, tuple)):
            for (match, new) in zip(find, replace):
                self.replace(match, new)
        elif isinstance(find, dict):
            for match, new in find.items():
                self.replace(match,new)
        else:
            if isinstance(find, ExprTree.Node):
                match = find
            elif isinstance(find, ExprTree):
                match = find.root
            else:
                match = ExprTree(find).root
            if isinstance(replace, ExprTree.Node):
                new = replace
            elif isinstance(replace, ExprTree):
                new = replace.root
            else:
                new = ExprTree(replace).root
            self.root.replace(match, new)
        
        return self

    class Node:
        """Expression Tree Node"""

        def __init__(self, expr, func):
            self.expr = expr
            self.func = func
            self.children = []

        def append(self, node):
            self.children.append(node)

        def find(self, find):
            if self.expr == find.expr:
                yield self
            else:
                for child in self.children:
                    yield from child.find(find)

        def update(self, node):
            self.expr = node.expr
            self.children = []
            for child in node.children:
                self.children.append(child)

        def _checkFlatMatch(self,find,replace):
            for i in range(len(self.children)-len(find.children)+1):
                matched = True
                for k in range(len(find.children)):
                    if ( not (self.children[i+k].expr == find.children[k].expr) or
                         not (self.children[i+k].func == find.children[k].func) ):
                        matched = False
                if matched:
                    self.children[i].update(replace)
                    for k in range(1,len(find.children)):
                        self.children.pop()
        
        def replace(self, find, replace):
            for curNode in self.find(find):
                curNode.update(replace)
            self._checkFlatMatch(find,replace)
            for curNode in self.children:
                curNode._checkFlatMatch(find,replace)
                         
        def __repr__(self):
            return "Node(%s, %s)" % (self.expr, self.func)

        def __str__(self):
            return str(self.expr)

        def __eq__(self, other):
            return self.expr == other.expr

    def __repr__(self):
        return "ExprTree(" + str(self.root.expr) + ")"

    __str__ = __repr__


if __name__ == "__main__":
    import doctest

    sys.exit(doctest.testmod()[0])
