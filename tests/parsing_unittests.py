# -*- coding: utf-8 -*-
"""
Created on Sun Jan 30 14:02:59 2022

@author: pyprg
"""
import unittest
import context
from graphparser.parsing import parse, _tokenize, _collect_elements

class Parse(unittest.TestCase):
    
    def test_1_node(self):
        d = 'node'
        ex = [('node', 'node', (), {})]
        self.assertEqual([*parse(d)], ex, f"expected {ex}")
    
    def test_2_nodes_1_edge(self):
        d = '0 1'
        ex = [
            ('node', '0', ('1',), {}), 
            ('edge', ('0', '1'), {}), 
            ('node', '1', ('0',), {})]
        self.assertEqual([*parse(d)], ex, f"expected {ex}")
    
    def test_2_nodes(self):
        d = """
            A
            
            B"""
        ex = [
            ('node', 'A', (), {}), 
            ('node', 'B', (), {})]
        self.assertEqual([*parse(d)], ex, f"expected {ex}")
    
    def test_2_nodes_valueerror(self):
        d = """
            A
            B"""
        with self.assertRaises(ValueError):
            [*parse(d)]
    
    def test_2_nodes_att_valueerror(self):
        d = """
            A
                  att=value"
            B"""
        with self.assertRaises(ValueError):
            [*parse(d)]
    
    def test_2_nodes_comment_valueerror(self):
        d = ("A           \n"
             "# comment   \n"
             "B           ")
        with self.assertRaises(ValueError):
            [*parse(d)]
    
    def test_2_nodes_no_edge(self):
        d0 = '0_ 1'
        d1 = '0 _1'
        d2 = '0_ _1'
        ex = [
            ('node', '0', (), {}), 
            ('node', '1', (), {})]
        self.assertEqual([*parse(d0)], ex, f"expected {ex}")
        self.assertEqual([*parse(d1)], ex, f"expected {ex}")
        self.assertEqual([*parse(d2)], ex, f"expected {ex}")
    
    def test_3_nodes_2_edges(self):
        d = '0 1 2'
        ex = [
            ('node', '0', ('1',), {}), 
            ('edge', ('0', '1'), {}), 
            ('node', '1', ('0', '2'), {}),
            ('edge', ('1', '2'), {}), 
            ('node', '2', ('1',), {})]
        self.assertEqual([*parse(d)], ex, f"expected {ex}")

    def test_blank(self):
        d = '^°"§$%&/()=?`´\}][{+~@€*;,:.-<>|'
        ex = []
        self.assertEqual([*parse(d)], ex, f"expected {ex}")

    def test_comment(self):
        d = '# this is a comment'
        ex = [('comment', d)]
        self.assertEqual([*parse(d)], ex, f"expected {ex}")

    def test_ignored_att(self):
        d = 'a=42'
        ex = []
        self.assertEqual([*parse(d)], ex, f"expected {ex}")
    
    def test_node_ignored_att_above(self):
        """ignores attribute as it is neither above nor below the node"""
        d = \
        """
              att=42
        mynode
        """
        ex = [('node', 'mynode', (), {})]
        self.assertEqual([*parse(d)], ex, f"expected {ex}")
    
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
        self.assertEqual([*parse(d0)], ex, f"expected {ex}")
        self.assertEqual([*parse(d1)], ex, f"expected {ex}")
        self.assertEqual([*parse(d2)], ex, f"expected {ex}")
    
    def test_node_ignored_att_below(self):
        """ignores attribute as it is neither above nor below the node"""
        d = \
        """
            mynode
                  att=42
        """
        ex = [('node', 'mynode', (), {})]
        self.assertEqual([*parse(d)], ex, f"expected {ex}")
    
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
        self.assertEqual([*parse(d0)], ex, f"expected {ex}")
        self.assertEqual([*parse(d1)], ex, f"expected {ex}")
        self.assertEqual([*parse(d2)], ex, f"expected {ex}")
    
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
        self.assertEqual([*parse(d0)], ex, f"expected {ex}")
        self.assertEqual([*parse(d1)], ex, f"expected {ex}")
    
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
        self.assertEqual([*parse(d0)], ex, f"expected {ex}")
        self.assertEqual([*parse(d1)], ex, f"expected {ex}")

    def test_underscore(self):
        d0 = '_'
        d1 = '__'
        ex = [('node', '', (), {})]
        self.assertEqual([*parse(d0)], ex, f"expected {ex}")
        self.assertEqual([*parse(d1)], ex, f"expected {ex}")

    def test_underscore_underscore(self):
        d0 = '_ _'
        d1 = '__ __'
        ex = [('node', '', (), {}), ('node', '', (), {})]
        self.assertEqual([*parse(d0)], ex, f"expected {ex}")
        self.assertEqual([*parse(d1)], ex, f"expected {ex}")

    def test_3_underscores(self):
        d = '___'
        ex = [('node', '_', (), {})]
        self.assertEqual([*parse(d)], ex, f"expected {ex}")

    def test_3_underscores_3_underscores(self):
        d = '___ ___'
        ex = [('node', '_', (), {}), ('node', '_', (), {})]
        self.assertEqual([*parse(d)], ex, f"expected {ex}")

class Tokenize(unittest.TestCase):
    
    def test_empty(self):
        self.assertEqual(
            [*_tokenize('')], 
            [], 
            'no value for empty string')

    def test_element_no_attribute(self):
        self.assertEqual(
            [*_tokenize('a')], 
            [('-', 'a')], 
            'element without attribute')
        
    def test_element_no_attribute2(self):
        self.assertEqual(
            [*_tokenize('a,')], 
            [('-', 'a')], 
            'element without attribute')

    def test_element_no_attribute3(self):
        self.assertEqual(
            [*_tokenize('ab')], 
            [('-', 'ab')], 
            'element without attribute')

    def test_two_elements_no_attribute(self):
        self.assertEqual(
            [*_tokenize('a,b')], 
            [('-', 'a'), ('-', 'b')], 
            'two element without attribute')

    def test_element_empty_attribute(self):
        self.assertEqual(
            [*_tokenize('ab()')], 
            [('+', 'ab'), ('a', '')], 
            'element with empty attribute')

    def test_element_two_attributes(self):
        self.assertEqual([*_tokenize('ab(,)')], 
            [('+', 'ab'), ('a', ''), ('a', '')], 
            'element with two attributes')

    def test_element_with_attributes(self):
        self.assertEqual([*_tokenize('ab((,),(,))')], 
            [('+', 'ab'), ('a', '(,)'), ('a', '(,)')], 
            'element with attributes')

    def test_element_with_quoted_attribute(self):
        self.assertEqual([*_tokenize(' ab( att = "32") ')], 
            [('+', 'ab'), ('a', 'att = "32"')], 
            'element with quoted attributes')

    def test_two_elements(self):
        self.assertEqual([*_tokenize('ab(a=3, b=(15,),c=(3,4), d=28),b')], 
            [('+', 'ab'), ('a', 'a=3'), ('a', 'b=(15,)'), ('a', 'c=(3,4)'), 
              ('a', 'd=28'), ('-', 'b')], 
            'two elements, first with attribute')

    def test_error_closing_brace(self):
        with self.assertRaises(ValueError):
            [*_tokenize('ab(a=3, b=(15,),c)=(3,4), d=28),b')]

    def test_error_closing_brace2(self):
        with self.assertRaises(ValueError):
            [*_tokenize('ab(a=3, b=(15,),c=(3,4), d=28)),b')]

    def test_error_missing_closing(self):
        with self.assertRaises(ValueError):
            [*_tokenize('ab(a=3, b=(15,),c=(3,4), d=28')]
            

class Collect_elements(unittest.TestCase):
    
    def test_empty(self):
        self.assertEqual(
            [*_collect_elements([])],
            [], 
            'no element for no token')

    def test(self):
        self.assertEqual(
            [*_collect_elements(
                [('+', 'ab'),
                 ('a', 'a=3'),
                 ('a', 'b=(15,)'),
                 ('a', 'c=(3,4)'),
                 ('a', 'd=28'),
                 ('-', 'b')])],
            [('ab', 
              {'a': '3', 
               'b': ('15',), 
               'c': ('3', '4'), 
               'd': '28'}), 
             ('b', {})])

    def test_unknown_token(self):
        with self.assertRaises(ValueError):
            [*_collect_elements(
                [('u', 'ab'),
                 ('a', 'a=3'),
                 ('a', 'b=(15,)'),
                 ('a', 'c=(3,4)'),
                 ('a', 'd=28'),
                 ('-', 'b')])]
            
    def test_unknown_token2(self):
        with self.assertRaises(ValueError):
            [*_collect_elements(
                [('+', 'ab'),
                 ('a', 'a=3'),
                 ('u', 'b=(15,)'),
                 ('a', 'c=(3,4)'),
                 ('a', 'd=28'),
                 ('-', 'b')])]
            
    def test_not_expected_token(self):
        with self.assertRaises(ValueError):
            [*_collect_elements(
                [('+', 'ab'),
                 ('+', 'a=3'),
                 ('a', 'b=(15,)'),
                 ('a', 'c=(3,4)'),
                 ('a', 'd=28'),
                 ('-', 'b')])]
            
    def test_not_expected_token2(self):
        with self.assertRaises(ValueError):
            [*_collect_elements(
                [('-', 'ab'),
                 ('a', 'a=3'),
                 ('a', 'b=(15,)'),
                 ('a', 'c=(3,4)'),
                 ('a', 'd=28'),
                 ('-', 'b')])]
            
if __name__ == '__main__':
    unittest.main()
    