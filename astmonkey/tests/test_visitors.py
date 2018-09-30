# -*- coding: utf-8 -*-
import pytest

from astmonkey.tests import utils

try:
    import unittest2 as unittest
except ImportError:
    import unittest
import ast
from astmonkey import visitors, transformers


class TestGraphNodeVisitor(object):
    @pytest.fixture
    def visitor(self):
        return visitors.GraphNodeVisitor()

    def test_has_edge(self, visitor):
        node = transformers.ParentChildNodeTransformer().visit(ast.parse('x = 1'))

        visitor.visit(node)

        assert visitor.graph.get_edge(str(node), str(node.body[0]))

    def test_does_not_have_edge(self, visitor):
        node = transformers.ParentChildNodeTransformer().visit(ast.parse('x = 1'))

        visitor.visit(node)

        assert not visitor.graph.get_edge(str(node), str(node.body[0].value))

    def test_node_label(self, visitor):
        node = transformers.ParentChildNodeTransformer().visit(ast.parse('x = 1'))

        visitor.visit(node)

        dot_node = visitor.graph.get_node(str(node.body[0].value))[0]
        assert dot_node.get_label() == 'ast.Num(n=1)'

    def test_edge_label(self, visitor):
        node = transformers.ParentChildNodeTransformer().visit(ast.parse('x = 1'))

        visitor.visit(node)

        dot_edge = visitor.graph.get_edge(str(node), str(node.body[0]))[0]
        assert dot_edge.get_label() == 'body[0]'

    def test_multi_parents_node_label(self, visitor):
        node = transformers.ParentChildNodeTransformer().visit(ast.parse('x = 1\nx = 2'))

        visitor.visit(node)

        dot_node = visitor.graph.get_node(str(node.body[0].targets[0]))[0]
        assert dot_node.get_label() == "ast.Name(id='x', ctx=ast.Store())"


class TestSourceGeneratorNodeVisitor(object):
    EOL = '\n'
    SIMPLE_ASSIGN = 'x = 1'
    PASS = 'pass'
    INDENT = ' ' * 4
    CLASS_DEF = 'class Sample:'
    EMPTY_CLASS = CLASS_DEF + EOL + INDENT + PASS
    FUNC_DEF = 'def f():'
    EMPTY_FUNC = FUNC_DEF + EOL + INDENT + PASS
    SINGLE_LINE_DOCSTRING = '""" This is a single line docstring."""'
    MULTI_LINE_DOCSTRING = '""" This is a multi line docstring.' + EOL + EOL + 'Further description...' + EOL + '"""'

    testdata = [
        # assign
        SIMPLE_ASSIGN,
        '(x, y) = z',
        'x += 1',
        'a = b = c',
        '(a, b) = enumerate(c)',
        SIMPLE_ASSIGN + EOL + SIMPLE_ASSIGN,
        SIMPLE_ASSIGN + EOL + EOL + SIMPLE_ASSIGN,
        EOL + SIMPLE_ASSIGN,
        EOL + EOL + SIMPLE_ASSIGN,

        # class definition
        EMPTY_CLASS,
        EOL + EMPTY_CLASS,
        CLASS_DEF + EOL + INDENT + EOL + INDENT + PASS,
        EMPTY_FUNC,
        EOL + EMPTY_FUNC,
        CLASS_DEF + EOL + INDENT + FUNC_DEF + EOL + INDENT + INDENT + SIMPLE_ASSIGN,
        'class A(B, C):' + EOL + INDENT + PASS,

        # function definition
        FUNC_DEF + EOL + INDENT + PASS,
        'def f(x, y=1, *args, **kwargs):' + EOL + INDENT + PASS,
        'def f(a, b=\'c\', *args, **kwargs):' + EOL + INDENT + PASS,
        FUNC_DEF + EOL + INDENT + 'return',
        FUNC_DEF + EOL + INDENT + 'return 5',
        # TODO: 'def __init__(self, *args, x=None, **kwargs):' + EOL + PASS,
        # TODO: FUNC_DEF + EOL + INDENT + 'return (x ==' + EOL + INDENT + '        ' + 'x)',

        # yield
        FUNC_DEF + EOL + INDENT + 'yield',
        FUNC_DEF + EOL + INDENT + 'yield 5',

        # importing
        'import x',
        'import x as y',
        'import x.y.z',
        'from x import y',
        'from x import y, z, q',
        'from x import y as z',
        'from x import y as z, q as p',
        'from . import x',
        'from .. import x',
        'from .y import x',
        'import x, y, z',
        'from x import (y, z, q)',

        # operators
        '(x and y)',
        'x < y',
        '(not x)',
        '(x + y)',
        '((x + y) / z)',

        # if
        'if x:' + EOL + INDENT + PASS,
        'if x:' + EOL + INDENT + PASS + EOL + 'else:' + EOL + INDENT + PASS,
        'if x:' + EOL + INDENT + PASS + EOL + 'elif y:' + EOL + INDENT + PASS,
        'if x:' + EOL + INDENT + PASS + EOL + 'elif y:' + EOL + INDENT + PASS
        + EOL + 'else:' + EOL + INDENT + PASS,
        'if x:' + EOL + INDENT + PASS + EOL + 'elif y:' + EOL + INDENT + PASS
        + EOL + 'elif z:' + EOL + INDENT + PASS,
        'if x:' + EOL + INDENT + PASS + EOL + 'elif y:' + EOL + INDENT + PASS
        + EOL + 'elif z:' + EOL + INDENT + PASS + EOL + 'else:' + EOL + INDENT + PASS,
        'x if y else z',
        # 'x = y * (z if z > 1 else 1)',
        # 'if x:' + EOL + INDENT + PASS + EOL + 'else:' + EOL + INDENT + 'if x:' + EOL + INDENT + INDENT + PASS,
        # 'if x' + EOL + INDENT + PASS + EOL + EOL + 'elif x:' + EOL + INDENT + PASS,

        # while
        'while (not i != 1):' + EOL + INDENT + SIMPLE_ASSIGN,
        'while True:' + EOL + INDENT + 'if True:' + EOL + INDENT + INDENT + 'continue',
        'while True:' + EOL + INDENT + 'if True:' + EOL + INDENT + INDENT + 'break',
        SIMPLE_ASSIGN + EOL + EOL + 'while False:' + EOL + INDENT + PASS,

        # for
        'for x in y:' + EOL + INDENT + 'break',
        'for x in y:' + EOL + INDENT + PASS + EOL + 'else:' + EOL + INDENT + PASS,

        # try ... except
        'try:' + EOL + INDENT + PASS + EOL + 'except Y:' + EOL + INDENT + PASS,
        'try:' + EOL + INDENT + PASS + EOL + EOL + EOL + 'except Y:' + EOL + INDENT + PASS,
        'try:' + EOL + INDENT + PASS + EOL + 'except Y as y:' + EOL + INDENT + PASS,
        'try:' + EOL + INDENT + PASS + EOL + 'finally:' + EOL + INDENT + PASS,
        # 'try:' + EOL + INDENT + PASS + EOL + 'except:' + EOL + INDENT + PASS + EOL + 'else:' + EOL + INDENT + PASS,

        # del
        'del x',
        'del x, y, z',
        # with
        'with x:' + EOL + INDENT + 'pass',
        'with x as y:' + EOL + INDENT + 'pass',
        # assert
        'assert True, \'message\'',
        'assert True',
        # lambda
        'lambda x: x',
        'lambda x: (((x ** 2) + (2 * x)) - 5)',
        # '(lambda: (yield))()',

        # subscript
        'x[y]',
        # slice
        'x[y:z:q]',
        'x[1:2,3:4]',
        'x[:2,:2]',
        'x[1:2]',
        'x[::2]',
        # global
        'global x',
        # raise
        'raise Exception()',
        # format
        '(\'a %s\' % \'b\')',
        '\'a {}\'.format(\'b\')',
        # decorator
        '@x(y)' + EOL + EMPTY_FUNC,
        # call
        'f(a)',
        'f(a, b)',
        'f(b=\'c\')',
        'f(*args)',
        'f(**kwargs)',
        'f(a, b=1, *args, **kwargs)',
        # list
        '[1, 2, 3]',
        # dict
        '{a: 3, b: \'c\'}',
        # list comprehension
        'x = [y.value for y in z if y.value >= 3]',
        # generator expression
        '(x for x in y if x)',
        # tuple
        '(1, 2)',
        # attribute
        'x.y',
        # ellipsis
        'x[...]',
        # str
        "x = 'y'",
        # 'r"\\n"',

        # num
        '1',

        # docstring
        SINGLE_LINE_DOCSTRING,
        MULTI_LINE_DOCSTRING,
        CLASS_DEF + EOL + INDENT + MULTI_LINE_DOCSTRING,
        FUNC_DEF + EOL + INDENT + MULTI_LINE_DOCSTRING,
        SIMPLE_ASSIGN + EOL + MULTI_LINE_DOCSTRING,
        MULTI_LINE_DOCSTRING + EOL + MULTI_LINE_DOCSTRING,

        # line continuation
        # TODO: 'x = \\' + EOL + INDENT + 'y = 5',
        # TODO: 'raise TypeError(' + EOL + INDENT + 'f"data argument must be a bytes-like object, "' + EOL + INDENT + 'f"not {type(data).__name__}")'
    ]

    if utils.check_version(from_inclusive=(2, 7)):
        testdata += [
            # set
            '{1, 2}',
            # set comprehension
            '{x for x in y if x}',
            # dict comprehension
            'x = {y: z for (y, z) in a}',
        ]

    if utils.check_version(to_exclusive=(3, 0)):
        testdata += [
            # print
            'print \'a\'',
            'print \'a\',',
            'print >> sys.stderr, \'a\'',
            # raise with msg and tb
            'raise x, y, z',
            # repr
            '`a`'
        ]

    if utils.check_version(from_inclusive=(3, 0)):
        testdata += [
            # nonlocal
            'nonlocal x',
            # starred
            '*x = y',
            # raise from
            'raise Exception() from exc',
            # byte string
            'b\'byte_string\'',
            # unicode string
            'x = \'äöüß\'',
            # metaclass
            'class X(Y, metaclass=Z):' + EOL + INDENT + 'pass',

            # function annotations
            'def f(a: str) -> str:' + EOL + INDENT + PASS,
            "def f(x: 'x' = 0):" + EOL + INDENT + PASS,

            # extended iterable unpacking
            '(x, *y) = z',

        ]

    if utils.check_version(from_inclusive=(3, 3)):
        testdata += [
            # with multiple
            'with x, y:' + EOL + INDENT + 'pass',
            # yield from
            FUNC_DEF + EOL + INDENT + 'yield from x',
        ]

    if utils.check_version(from_inclusive=(3, 5)):
        testdata += [
            # unpack into dict
            '{**kwargs}',

            # async/await
            'async ' + FUNC_DEF + EOL + INDENT + PASS,
            'async ' + FUNC_DEF + EOL + INDENT + 'async for line in reader:' + EOL + INDENT + INDENT + PASS,
            'async ' + FUNC_DEF + EOL + INDENT + 'await asyncio.sleep(1)',
            'async with x:' + EOL + INDENT + PASS,

            # matrix multiplication operator
            'x @ y',

        ]

    if utils.check_version(from_inclusive=(3, 6)):
        testdata += [
            # f-strings
            'f\'He said his name is {name}.\'',
            'f"{x!r}"',
            'f"a\'b"',
        ]

    @pytest.mark.parametrize("source", testdata)
    def test_codegen_roundtrip(self, source):
        node = ast.parse(source)
        generated = visitors.to_source(node)
        node_generated = ast.parse(generated)
        assert ast.dump(node) == ast.dump(node_generated)
