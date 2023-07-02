# -*- coding: utf-8 -*-
"""
Created on Sun Jan 30 14:02:59 2022

@author: pyprg
"""
import unittest
import context
from graphparser.parsing import (
    _scanoneline, parse, _tokenize, _Token, _Tokencollection, _Attributetokens,
    _collect_tokens, _parse_params, parse_params, make_objects,
    make_type_data)

class Scanoneline(unittest.TestCase):

    def test_blank(self):
        cat, s = _scanoneline('')
        self.assertEqual(cat, 'b')
        self.assertEqual(s, '')

    def test_comment(self):
        cat, s = _scanoneline('#')
        self.assertEqual(cat, 'c')
        self.assertEqual(s, '#')

    def test_entity(self):
        cat, s = _scanoneline('a')
        self.assertEqual(cat, 'e')

    def test_entity2(self):
        cat, s = _scanoneline('a   a')
        self.assertEqual(cat, 'e')
        self.assertTrue(all(e[1]=='a' for e in s))

    def test_attribute(self):
        cat, s = _scanoneline('a=42')
        self.assertEqual(cat, 'a')
        self.assertEqual(list(s)[0][1], {'a': '42'})

    def test_attribute2(self):
        cat, s = _scanoneline('a.b=42')
        self.assertEqual(cat, 'a')
        self.assertEqual(list(s)[0][1], {'a.b': '42'})

class Parse(unittest.TestCase):

    def test_1_node(self):
        d = 'node'
        ex = [('node', 'node', (), {})]
        self.assertEqual([*parse([d])], ex, f"expected {ex}")

    def test_2_nodes_1_edge(self):
        d = '0 1'
        ex = [
            ('node', '0', ('1',), {}),
            ('edge', ('0', '1'), {}),
            ('node', '1', ('0',), {})]
        self.assertEqual([*parse([d])], ex, f"expected {ex}")

    def test_2_nodes(self):
        d = """
            A

            B"""
        ex = [
            ('node', 'A', (), {}),
            ('node', 'B', (), {})]
        self.assertEqual([*parse([d])], ex, f"expected {ex}")

    def test_2_nodes_valueerror(self):
        d = """
            A
            B"""
        with self.assertRaises(ValueError):
            [*parse([d])]

    def test_2_nodes_att_valueerror(self):
        d = """
            A
                  att=value"
            B"""
        with self.assertRaises(ValueError):
            [*parse([d])]

    def test_2_nodes_comment_valueerror(self):
        d = ("A           \n"
             "# comment   \n"
             "B           ")
        with self.assertRaises(ValueError):
            [*parse([d])]

    def test_2_nodes_no_edge(self):
        d0 = '0_ 1'
        d1 = '0 _1'
        d2 = '0_ _1'
        ex = [
            ('node', '0', (), {}),
            ('node', '1', (), {})]
        self.assertEqual([*parse([d0])], ex, f"expected {ex}")
        self.assertEqual([*parse([d1])], ex, f"expected {ex}")
        self.assertEqual([*parse([d2])], ex, f"expected {ex}")

    def test_3_nodes_2_edges(self):
        d = '0 1 2'
        ex = [
            ('node', '0', ('1',), {}),
            ('edge', ('0', '1'), {}),
            ('node', '1', ('0', '2'), {}),
            ('edge', ('1', '2'), {}),
            ('node', '2', ('1',), {})]
        self.assertEqual([*parse([d])], ex, f"expected {ex}")

    def test_blank(self):
        d = '^°"§$%&/()=?`´\}][{+~@€*;,:.-<>|'
        ex = []
        self.assertEqual([*parse([d])], ex, f"expected {ex}")

    def test_comment(self):
        d = '# this is a comment'
        ex = [('comment', d, 0)]
        self.assertEqual([*parse([d])], ex, f"expected {ex}")

    def test_ignored_att(self):
        d = 'a=42'
        ex = []
        self.assertEqual([*parse([d])], ex, f"expected {ex}")

    def test_node_ignored_att_above(self):
        """ignores attribute as it is neither above nor below the node"""
        d = \
        """
              att=42
        mynode
        """
        ex = [('node', 'mynode', (), {})]
        self.assertEqual([*parse([d])], ex, f"expected {ex}")

    def test_node_att_above(self):
        d0 =  """
                att=42
                mynode"""
        d1 = """
                 att=42
                mynode"""
        d2 = """
                     att=42
                mynode"""
        ex = [('node', 'mynode', (), {'att': '42'})]
        self.assertEqual([*parse([d0])], ex, f"expected {ex}")
        self.assertEqual([*parse([d1])], ex, f"expected {ex}")
        self.assertEqual([*parse([d2])], ex, f"expected {ex}")

    def test_node_ignored_att_below(self):
        """ignores attribute as it is neither above nor below the node"""
        d = \
        """
            mynode
                  att=42
        """
        ex = [('node', 'mynode', (), {})]
        self.assertEqual([*parse([d])], ex, f"expected {ex}")

    def test_node_att_below(self):
        d0 = """
            mynode
            att=42e-6+27j"""
        d1 = """
            mynode
              att=42e-6+27j"""
        d2 = """
            mynode
                 att=42e-6+27j"""
        ex = [('node', 'mynode', (), {'att': '42e-6+27j'})]
        self.assertEqual([*parse([d0])], ex, f"expected {ex}")
        self.assertEqual([*parse([d1])], ex, f"expected {ex}")
        self.assertEqual([*parse([d2])], ex, f"expected {ex}")

    def test_edge_att(self):
        d0 =  """
              att=b
            a==b"""
        d1 = """
            a==b
              att=b"""
        ex = [('node', 'a', ('b',), {}),
              ('edge', ('a', 'b'), {'att': 'b'}),
              ('node', 'b', ('a',), {})]
        self.assertEqual([*parse([d0])], ex, f"expected {ex}")
        self.assertEqual([*parse([d1])], ex, f"expected {ex}")

    def test_node_and_edge_att(self):
        d0 =  """
             g=h
            a==b
            c=d
               e=f"""
        d1 = """
            c=d
               e=f
            a==b
             g=h"""
        ex = [('node', 'a', ('b',), {'c':'d'}),
              ('edge', ('a', 'b'), {'g': 'h'}),
              ('node', 'b', ('a',), {'e':'f'})]
        self.assertEqual([*parse([d0])], ex, f"expected {ex}")
        self.assertEqual([*parse([d1])], ex, f"expected {ex}")

    def test_underscore(self):
        d0 = '_'
        d1 = '__'
        ex = [('node', '', (), {})]
        self.assertEqual([*parse([d0])], ex, f"expected {ex}")
        self.assertEqual([*parse([d1])], ex, f"expected {ex}")

    def test_underscore_underscore(self):
        d0 = '_ _'
        d1 = '__ __'
        ex = [('node', '', (), {}), ('node', '', (), {})]
        self.assertEqual([*parse([d0])], ex, f"expected {ex}")
        self.assertEqual([*parse([d1])], ex, f"expected {ex}")

    def test_3_underscores(self):
        d = '___'
        ex = [('node', '_', (), {})]
        self.assertEqual([*parse([d])], ex, f"expected {ex}")

    def test_3_underscores_3_underscores(self):
        d = '___ ___'
        ex = [('node', '_', (), {}), ('node', '_', (), {})]
        self.assertEqual([*parse([d])], ex, f"expected {ex}")

class Tokenize(unittest.TestCase):

    def test_empty(self):
        self.assertEqual(
            [*_tokenize('')],
            [],
            'no value for empty string')

    def test_element_no_attribute(self):
        self.assertEqual(
            [*_tokenize(['a'])],
            [_Token(type='e', content='a', text='a', row=0, start=0, end=1)],
            'element without attribute')

    def test_element_no_attribute2(self):
        self.assertEqual(
            [*_tokenize(['a,'])],
            [_Token(type='e', content='a', text='a,', row=0, start=0, end=1),
             _Token(type='_', content=',', text='a,', row=0, start=1, end=2)],
            'element without attribute')

    def test_element_no_attribute3(self):
        self.assertEqual(
            [*_tokenize(['ab'])],
            [_Token(type='e', content='ab', text='ab', row=0, start=0, end=2)],
            'element without attribute')

    def test_two_elements_no_attribute(self):
        self.assertEqual(
            [*_tokenize(['a,b'])],
            [_Token(
                type='e', content='a', text='a,b', row=0, start=0, end=1),
             _Token(
                 type='_', content=',', text='a,b', row=0, start=1, end=2),
             _Token(
                 type='e', content='b', text='a,b', row=0, start=2, end=3)],
            'two element without attribute')

    def test_element_empty_attribute(self):
        self.assertEqual(
            [*_tokenize(['ab()'])],
            [_Token(
                type='e', content='ab', text='ab()', row=0, start=0, end=2),
             _Token(
                 type='_', content='(', text='ab()', row=0, start=2, end=3),
             _Token(
                 type='_', content=')', text='ab()', row=0, start=3, end=4)],
            'element with empty attribute')

    def test_element_with_quoted_attribute(self):
        self.assertEqual([*_tokenize([' ab( att = "32") '])],
            [_Token('_', ' ', ' ab( att = "32") ', 0, 0, 1),
             _Token('e', 'ab', ' ab( att = "32") ', 0, 1, 3),
             _Token('_', '(', ' ab( att = "32") ', 0, 3, 4),
             _Token('_', ' ', ' ab( att = "32") ', 0, 4, 5),
             _Token('a', 'att', ' ab( att = "32") ', 0, 5, 8),
             _Token('_', ' ', ' ab( att = "32") ', 0, 8, 9),
             _Token('_', '=', ' ab( att = "32") ', 0, 9, 10),
             _Token('_', ' ', ' ab( att = "32") ', 0, 10, 11),
             _Token('v', '"32"', ' ab( att = "32") ', 0, 11, 15),
             _Token('_', ')', ' ab( att = "32") ', 0, 15, 16),
             _Token('_', ' ', ' ab( att = "32") ', 0, 16, 17)],
            'element with quoted attributes')

    def test_element_invalid_attribute(self):
        self.assertEqual([*_tokenize(['ab(,)'])],
            [_Token('e', content='ab', text='ab(,)', row=0, start=0, end=2),
             _Token('_', content='(', text='ab(,)', row=0, start=2, end=3),
             _Token('F', content=',', text='ab(,)', row=0, start=3, end=4),
             _Token('_', content=')', text='ab(,)', row=0, start=4, end=5)],
            'element with two attributes')

    def test_two_elements(self):
        self.assertEqual([*_tokenize(['ab(a=3, b=(15),c=(3,4), d=28),b'])],
            [_Token('e', 'ab', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 0, 2),
             _Token('_', '(', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 2, 3),
             _Token('a', 'a', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 3, 4),
             _Token('_', '=', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 4, 5),
             _Token('v', '3', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 5, 6),
             _Token('_', ',', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 6, 7),
             _Token('_', ' ', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 7, 8),
             _Token('a', 'b', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 8, 9),
             _Token('_', '=', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 9, 10),
             _Token('_', '(', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 10, 11),
             _Token('v', '15', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 11, 13),
             _Token('_', ')', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 13, 14),
             _Token('_', ',', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 14, 15),
             _Token('a', 'c', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 15, 16),
             _Token('_', '=', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 16, 17),
             _Token('_', '(', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 17, 18),
             _Token('v', '3', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 18, 19),
             _Token('_', ',', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 19, 20),
             _Token('v', '4', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 20, 21),
             _Token('_', ')', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 21, 22),
             _Token('_', ',', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 22, 23),
             _Token('_', ' ', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 23, 24),
             _Token('a', 'd', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 24, 25),
             _Token('_', '=', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 25, 26),
             _Token('v', '28', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 26, 28),
             _Token('_', ')', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 28, 29),
             _Token('_', ',', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 29, 30),
             _Token('e', 'b', 'ab(a=3, b=(15),c=(3,4), d=28),b', 0, 30, 31)],
            'two elements, first with attributes')

class Collect_tokens(unittest.TestCase):

    def test_empty(self):
        self.assertEqual(
            [*_collect_tokens([])],
            [],
            'no element when no token')

    def test(self):
        self.assertEqual(
            [*_collect_tokens([_Token('_')])],
            [],
            'no element for token \'_\'')

    def test_token_C(self):
        """Close token"""
        self.assertEqual(
            [*_collect_tokens([_Token('C')])],
            [],
            'no element for closing token \'C\'')

    def test_unknown_token(self):
        """unknown token"""
        self.assertEqual(
            [*_collect_tokens(
                [_Token('U')])],
            [_Tokencollection(
                _Token('U', 'Message'),
                [_Attributetokens(
                    _Token('a', 'message'),
                    [_Token('v', "error: invalid text ''\n0:0:\n    ^")]),
                 _Attributetokens(
                     _Token(type='a', content='level'),
                     [_Token(type='v', content='2')]) ])])

    def test_token_e(self):
        """two collections"""
        self.assertEqual(
            [*_collect_tokens([_Token('e')])],
            [_Tokencollection(_Token('e'), [])],
            'one token collection')

    def test_token_ee(self):
        """two collections"""
        self.assertEqual(
            [*_collect_tokens(
                [_Token('e'),
                 _Token('e')])],
            [_Tokencollection(_Token('e'), []),
             _Tokencollection(_Token('e'), [])],
             'two token collections')

    def test_token_ea(self):
        """element"""
        self.assertEqual(
            [*_collect_tokens(
                [_Token('e'),
                 _Token('a')])],
            [_Tokencollection(
                _Token('E', 'Message'),
                [_Attributetokens(
                    _Token('a', 'message'),
                    [_Token('v', 'error, unexpected end of data')]),
                 _Attributetokens(
                     _Token('a', 'level'),
                     [_Token('v', '2')])])],
            'unexpected end of data')

    def test_token_eav(self):
        """element with attribute having one value"""
        self.assertEqual(
            [*_collect_tokens(
                [_Token('e', 'distance'),
                 _Token('a', 'length'),
                 _Token('v', '42')])],
            [_Tokencollection(
                _Token('e', 'distance'),
                [_Attributetokens(
                    _Token('a', 'length'),
                    [_Token('v', '42')])])],
            'element with attributes having one value')

    def test_token_eavv(self):
        """element with attribute having two values"""
        self.assertEqual(
            [*_collect_tokens(
                [_Token('e', 'distance'),
                 _Token('a', 'length'),
                 _Token('v', '42'),
                 _Token('v', 'm')])],
            [_Tokencollection(
                _Token('e', 'distance'),
                [_Attributetokens(
                    _Token('a', 'length'),
                    [_Token('v', '42'),
                     _Token('v', 'm')])])],
            'element with attributes having two values')

    def test_token_eavvavv(self):
        """element with attribute having two values"""
        self.assertEqual(
            [*_collect_tokens(
                [_Token('e', 'distance'),
                 _Token('a', 'length'),
                 _Token('v', '42'),
                 _Token('v', 'm'),
                 _Token('a', 'height'),
                 _Token('v', '27'),
                 _Token('v', 'cm')])],
            [_Tokencollection(
                _Token('e', 'distance'),
                [_Attributetokens(
                    _Token('a', 'length'),
                    [_Token('v', '42'),
                     _Token('v', 'm')]),
                 _Attributetokens(
                    _Token('a', 'height'),
                    [_Token('v', '27'),
                     _Token('v', 'cm')])])],
            'element with two attributes each having two values')

    def test_token_E(self):
        """element with attribute having two values"""
        self.assertEqual(
            [*_collect_tokens(
                [_Token('E', 'my error message')])],
            [_Tokencollection(
                _Token(type='E', content='Message'),
                [_Attributetokens(
                    _Token(type='a', content='message'),
                    [_Token(
                        type='v', content='my error message\n0:0:\n    ^')]),
                 _Attributetokens(
                    _Token(type='a', content='level'),
                    [_Token(type='v', content='2')])])],
            'error message')

class Parse_params(unittest.TestCase):

    def test_two_items(self):
        text_lines = (
            "",
            "Mytest(att=val,att2=val),",
            "Mytest2(att20=val, att22=val22)")
        res = [*_parse_params(text_lines)]
        expected = [
            _Tokencollection(
                _Token(
                    'e', 'Mytest',
                    'Mytest(att=val,att2=val),',
                    1, 0, 6),
                [_Attributetokens(
                    _Token(
                        'a', 'att',
                        'Mytest(att=val,att2=val),',
                        1, 7, 10),
                    [_Token(
                        'v', 'val',
                        'Mytest(att=val,att2=val),',
                        1, 11, 14)]),
                 _Attributetokens(
                    _Token(
                        'a', 'att2',
                        'Mytest(att=val,att2=val),',
                        1, 15, 19),
                    [_Token(
                        'v', 'val',
                        'Mytest(att=val,att2=val),',
                        1, 20, 23)])]),
            _Tokencollection(
                _Token(
                    'e', 'Mytest2',
                    'Mytest2(att20=val, att22=val22)',
                    2, 0, 7),
                [_Attributetokens(
                    _Token(
                        'a', 'att20',
                        'Mytest2(att20=val, att22=val22)',
                        2, 8, 13),
                    [_Token(
                        'v', 'val',
                        'Mytest2(att20=val, att22=val22)',
                        2, 14, 17)]),
                 _Attributetokens(
                     _Token(
                         'a', 'att22',
                         'Mytest2(att20=val, att22=val22)',
                         2, 19, 24),
                     [_Token(
                         'v', 'val22',
                         'Mytest2(att20=val, att22=val22)',
                         2, 25, 30)]
                     )])]
        self.assertEqual(
            expected, res, 'two items with attributes')

class Parse_params2(unittest.TestCase):

    def test_two_items(self):
        text_lines = (
            "",
            "Mytest(att=val,att2=val),",
            "Mytest2(att20=val, att22=val22)")
        res = [*parse_params(text_lines)]
        expected = [
            ('Mytest', {'att': ('val',), 'att2': ('val',)}),
            ('Mytest2', {'att20': ('val',), 'att22': ('val22',)})]
        self.assertEqual(
            expected, res, 'two items with attributes')

    def test_item_with_tuple_atts(self):
        text_lines = (
            ["Mytest("
             "  att=(a,\"b\",c),",
             "  att2=('d', 'e'),"
             "  att3=(12.4, 13))"])
        res = [*parse_params(text_lines)]
        expected = [
            ('Mytest',
              {'att': ('a', '"b"', 'c'),
               'att2': ("'d'", "'e'"),
               'att3': ('12.4' , '13' )})]
        self.assertEqual(
            expected, res, 'item with tuple attributes')

from collections import namedtuple
Nt0 = namedtuple('Nt0', '')
Nt1 = namedtuple('Nt1', 'numbers')
Nt2 = namedtuple('Nt2', 'height width')
Nt22 = namedtuple('Nt22', 'height width')
Message = namedtuple('Message', 'message level', defaults=(2,))

# parameters of object factory
_convdata = make_type_data(
     #           type  is_tuple type  is_tuple
    [#          message        level
     (Message, [(str,  False), (int,  False)]),
     (Nt0,     []),
     #          numbers
     (Nt1,     [(int,  True)]),
     #          height           width
     (Nt2,     [(float,  False), (float, False)]),
     #          height           width
     (Nt22,    [(float,  True), (float, True)])])

class Read_tuples(unittest.TestCase):

    def test_empty_string(self):
        self.assertEqual(
            tuple(make_objects({}, Message, ())),
            (),
            'no input')

    def test_unknown_element(self):
        self.assertEqual(
            tuple(make_objects({}, Message, ['a'])),
            (Message(message="unknown element 'a'\n0:0:a\n    ^", level=2),),
            'unknown element')

    def test_missing_attribute(self):
        self.assertEqual(
            tuple(make_objects(_convdata, Message, ['Message'])),
            (Message(
                message="Message.__new__() missing 1 required positional "
                "argument: 'message'\n0:0:Message\n    ^^^^^^^",
                level=2),),
            'missing attribute')

    def test_default_attribute(self):
        self.assertEqual(
            tuple(make_objects(_convdata, Message, ['Message(message=text)'])),
            (Message(message='text', level=2),),
            'default attribute')

    def test_no_attribute(self):
        self.assertEqual(
            tuple(make_objects(_convdata, Message, ['Nt0'])),
            (Nt0(),),
            'no attribute')

    def test_no_attribute2(self):
        self.assertEqual(
            tuple(make_objects(_convdata, Message, ['Nt0   ()'])),
            (Nt0(),),
            'no attribute')

    def test_no_attribute_two_lines(self):
        self.assertEqual(
            tuple(
                make_objects(
                    _convdata,
                    Message,
                    ['Nt0   (', ')'])),
            (Nt0(),),
            'no attribute')

    def test_no_attribute_two_lines2(self):
        self.assertEqual(
            tuple(
                make_objects(
                    _convdata,
                    Message,
                    ['Nt0', '()'])),
            (Nt0(),),
            'no attribute')

    def test_unexpected_attribute(self):
        self.assertEqual(
            tuple(make_objects(_convdata, Message, ['Nt0(b=15)'])),
            (Message(
                message="error: invalid name for attribute 'b'"
                "\n0:4:Nt0(b=15)"
                "\n    ----^",
                level=2),),
            'unexpected attribute')

    def test_tuple_attribute1(self):
        self.assertEqual(
            tuple(make_objects(
                _convdata,
                Message,
                [' Nt1 ( numbers = ( 1 , 2 ) ) '])),
            (Nt1(numbers=(1,2)),),
            'attribute has tuple value')

    def test_invalid_attribute_type(self):
        self.assertEqual(
            tuple(make_objects(
                _convdata,
                Message,
                [' Nt1 ( numbers = ( 1 ,a ) ) '])),
            (Message(
                message="invalid literal for int() with base 10: 'a'"
                "\n'a' cannot be converted to int"
                "\n0:22: Nt1 ( numbers = ( 1 ,a ) ) "
                "\n     ----------------------^",
                level=2),),
            'attribute value has invalid type')

    def test_invalid_attribute_type2(self):
        self.assertEqual(
            tuple(make_objects(
                _convdata,
                Message,
                [' Nt1 ( numbers = ( 1 , a ) ) '])),
            (Message(
                message="invalid literal for int() with base 10: 'a'"
                "\n'a' cannot be converted to int"
                "\n0:23: Nt1 ( numbers = ( 1 , a ) ) "
                "\n     -----------------------^",
                level=2),),
            'attribute value has invalid type')

    def test_invalid_attribute_type3(self):
        self.assertEqual(
            tuple(make_objects(
                _convdata,
                Message,
                [' Nt1 ( numbers = ( 1 ,  a ) ) '])),
            (Message(
                message="invalid literal for int() with base 10: 'a'"
                "\n'a' cannot be converted to int"
                "\n0:24: Nt1 ( numbers = ( 1 ,  a ) ) "
                "\n     ------------------------^",
                level=2),),
            'attribute value has invalid type')

    def test_invalid_attribute_type4(self):
        self.assertEqual(
            tuple(make_objects(
                _convdata,
                Message,
                [' Nt1 ( numbers = ( 1 a ) ) '])),
            (Message(
                message="invalid literal for int() with base 10: 'a'"
                "\n'a' cannot be converted to int"
                "\n0:21: Nt1 ( numbers = ( 1 a ) ) "
                "\n     ---------------------^",
                level=2),),
            'attribute value has invalid type')

    def test_two_attributes(self):
        self.assertEqual(
            tuple(make_objects(
                _convdata,
                Message,
                [' Nt2(height = 13.5, width=21 ) '])),
            (Nt2(height=13.5, width=21),),
            'attribute has tuple value')

    def test_two_attributes_two_lines(self):
        self.assertEqual(
            tuple(make_objects(
                _convdata,
                Message,
                [' Nt2', '(height = 13.5, width=21 ) '])),
            (Nt2(height=13.5, width=21),),
            'attribute has tuple value')

    def test_two_attributes_two_lines2(self):
        self.assertEqual(
            tuple(make_objects(
                _convdata,
                Message,
                [' Nt2(', 'height = 13.5, width=21 ) '])),
            (Nt2(height=13.5, width=21),),
            'attribute has tuple value')

    def test_two_attributes_two_lines3(self):
        self.assertEqual(
            tuple(make_objects(
                _convdata,
                Message,
                [' Nt2(', 'height = 13.5 width=21 ) '])),
            (Nt2(height=13.5, width=21),),
            'attribute has tuple value')

    def test_two_attributes_two_lines4(self):
        self.assertEqual(
            tuple(make_objects(
                _convdata,
                Message,
                ['  Nt2(height=13.5,',
                 '  width=21)'])),
            (Nt2(height=13.5, width=21),),
            'attribute has tuple value')

    def test_two_attributes_three_lines(self):
        self.assertEqual(
            tuple(make_objects(
                _convdata,
                Message,
                [' Nt2(', 'height = 13.5,','width=21 ) '])),
            (Nt2(height=13.5, width=21),),
            'attribute has tuple value')

    def test_two_attributes2(self):
        self.assertEqual(
            tuple(make_objects(
                _convdata,
                Message,
                [' Nt2 ( height = 13.5  width=21 ) '])),
            (Nt2(height=13.5, width=21),),
            'attribute has tuple value')

    def test_two_attributes_tuple(self):
        self.assertEqual(
            tuple(make_objects(
                _convdata,
                Message,
                [' Nt22 ( height = 13.5  width=21 ) '])),
            (Nt2(height=(13.5,), width=(21,)),),
            'attribute has tuple value')

    def test_two_attributes_tuple2(self):
        self.assertEqual(
            tuple(make_objects(
                _convdata,
                Message,
                [' Nt22 ( height = (13.5, 42),  width=(21,27) ) '])),
            (Nt2(height=(13.5, 42), width=(21, 27)),),
            'attribute has tuple value')

    def test_two_attributes_tuple3(self):
        self.assertEqual(
            tuple(make_objects(
                _convdata,
                Message,
                [' Nt22 ( height = (13.5, 42)  width=(21,27) ) '])),
            (Nt2(height=(13.5, 42), width=(21, 27)),),
            'attribute has tuple value')

    def test_two_attributes_tuple4(self):
        self.assertEqual(
            tuple(make_objects(
                _convdata,
                Message,
                [' Nt22( height = (13.5 42)  width=(21 27) ) '])),
            (Nt2(height=(13.5, 42), width=(21, 27)),),
            'attribute has tuple value, no commas')

    def test_two_attributes_tuple5(self):
        """no equal sign required if attribute value is a tuple"""
        self.assertEqual(
            tuple(make_objects(
                _convdata,
                Message,
                [' Nt22( height(13.5 42)  width (21 27) ) '])),
            (Nt2(height=(13.5, 42), width=(21, 27)),),
            'attribute has tuple value, no commas, without equals')

    def test_two_elements(self):
        self.assertEqual(
            tuple(make_objects(
                _convdata,
                Message,
                [' Nt0 Nt0 '])),
            (Nt0(),Nt0()),
            'two elements, no commas')

    def test_two_elements2(self):
        self.assertEqual(
            tuple(make_objects(
                _convdata,
                Message,
                [' Nt0(), Nt0 '])),
            (Nt0(),Nt0()),
            'attribute has tuple value, no commas')

    def test_two_elements3(self):
        self.assertEqual(
            tuple(make_objects(
                _convdata,
                Message,
                [' Nt0(),   Nt0 Nt0  (  ) ,Nt0'])),
            (Nt0(), Nt0(), Nt0(), Nt0()),
            'elements might be separated by commas or not')

if __name__ == '__main__':
    unittest.main()
