# -*- coding: utf-8 -*-
"""
Parser for input of graph data using a string.
Copyright (C) 2022 pyprg

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.

@author: pyprg
"""
import re
from operator import itemgetter
from functools import reduce
from itertools import chain

ENTITY_ID = r'\b\w+\b' # word boundary, word characters, word boundary
ATTRIBUTE_KEY_CLASS = r'\w' # word character
ATTRIBUTE_KEY = f'{ATTRIBUTE_KEY_CLASS}+' # word characters
KEY_VALUE_SEP = r'='
ATTRIBUTE_VALUE_CLASS = r'[+\-.\w]'# plus, minus, decimal point, word character
ATTRIBUTE_VALUE = f'{ATTRIBUTE_VALUE_CLASS}+' 
ATTRIBUTE_SEP = r' ,' # space, comma

# string versions of regular expressions
BLANK = r'^([\s\W]*)$'
COMMENT = r'^#.*$'
ENTITY = (
    f'(?<!{ATTRIBUTE_KEY_CLASS}{KEY_VALUE_SEP}){ENTITY_ID}'
    f'(?!{KEY_VALUE_SEP}{ATTRIBUTE_VALUE_CLASS})')
ATTRIBUTES = (
    f'(({ATTRIBUTE_KEY}{KEY_VALUE_SEP}{ATTRIBUTE_VALUE}'
    f'[{ATTRIBUTE_SEP}]?)+)')
ALL = f'{BLANK}|{COMMENT}|({ENTITY}|{ATTRIBUTES})'

# compiled regular expressions
RE_ATTRIBUTE_SEP = re.compile(f'[{ATTRIBUTE_SEP}]')
RE_KEY_VALUE_SEP = re.compile(KEY_VALUE_SEP)
RE_BLANK = re.compile(BLANK)
RE_COMMENT = re.compile(COMMENT)
RE_ATTRIBUTES = re.compile(ATTRIBUTES)
RE_ENTITY = re.compile(ENTITY)
RE_ALL = re.compile(ALL)

_empty_tuple = ()
_empty_dict = {}

def _make_att_dict(match):
    """Creates a dict of attribute_name: attribute_value {str: str} from
    an re.Match.
    
    Parameters
    ----------
    match: re.Match
    
    Returns
    -------
    dict
        {str: str}"""
    atts = RE_ATTRIBUTE_SEP.split(match.group(0).rstrip(ATTRIBUTE_SEP))
    return dict(RE_KEY_VALUE_SEP.split(att) for att in atts)

def _line_attributes(firstmatch):
    """Extracts attributes (key-value pairs) from a text line.
    
    Parameters
    ----------
    firstmatch: re.Match
        first match of regular expression in processed line
    
    Yields
    ------
    list
        tuple
            * int pos_x
            * dict, key->value"""
    start, end = firstmatch.span()
    yield start, _make_att_dict(firstmatch)
    for m in RE_ATTRIBUTES.finditer(firstmatch.string[end:]):
         yield end + m.span()[0], _make_att_dict(m)
         
def _line_entities(firstmatch):
    """Extracts entities (nodes) from a text line.
    
    Parameters
    ----------
    firstmatch: re.Match
        first match of regular expression in processed line
    
    Returns
    -------
    list
        tuple
            * int, int, tuple pos_x, pos_y
            * str, id of entity"""
    start, end = firstmatch.span()
    entities = [(firstmatch.span(), firstmatch.group(0))]
    entities.extend(
        (((end + m2.span()[0]), (end + m2.span()[1])), m2.group(0))
        for m2 in RE_ENTITY.finditer(firstmatch.string[firstmatch.span()[1]:]))
    return entities

def _scanoneline(oneline):
    """Scans one line of a string. Determins the data category
    ::
        'c' - comment
        'a' - attributes
        'e' - entities
        'b' - blank
    and creates a result structure, which is a tuple with first 
    element 'c'|'a'|'e'|'b' and a category specific tail.
    
    Parameters
    ----------
    oneline: str
    
    Returns
    -------
    tuple
        * str, category marker 'c'|'a'|'e'|'b'
        * category specific payload"""
    m = RE_ALL.search(oneline)
    if m:
        if RE_COMMENT.match(m.group()):
            return 'c', None
        if RE_ATTRIBUTES.match(m.group()):
            return 'a', _line_attributes(m)
        if RE_ENTITY.match(m.group()):
            return 'e', _line_entities(m)
    return 'b', m.group()

def _scanlines(lines):
    """Scans a sequence (iterable) of strings.
    
    Parameters
    ----------
    lines: iterable
        str
    
    Yields
    ------
    dict
        * 'entities': list
            tuple - (start, end), id_of_entity
        * 'atts': list
            tuple - start, ({key:value, ...}, ...)"""
    entities = None
    atts = list()
    for line in lines:
        marker, data = _scanoneline(line)
        if marker == 'b':
            if entities:
                yield {'entities': entities, 'atts': atts}
            atts = list()
            entities = None
        elif marker == 'a':
            atts.extend(data)
        elif marker == 'e':
            if not entities is None:
                msg = (
                    "unexpected entity (node) line, "
                    "lines with entities (nodes) must be "
                    f"separated by 'blank' lines, processed line: {line}")
                raise ValueError(msg)
            entities = data
    if entities:
        yield {'entities': entities, 'atts': atts}

def _scanentities(lines):
    """Scans a sequence (iterable) of strings.
    
    Parameters
    ----------
    lines: iterable
        str
    
    Yields
    ------
    dict
        * 'entities': list
            tuple - (start, end), id_of_entity
        * 'atts': list
            tuple - start, ({key:value, ...}, ...)"""
    entities = None
    atts = list()
    for idx, line in enumerate(lines):
        marker, data = _scanoneline(line)
        if marker == 'e':
            yield tuple((t[1], (t[0][0], -idx)) for t in data)
    if entities:
        yield {'entities': entities, 'atts': atts}
    

def _get_positions(posl, posr, l_connect, r_connect):
    """Corrects position of start by +1 if not connected at left side,
    end position by -1 if not connected at right side.
    
    Parameters
    ----------
    posl: int
        start position
    posr: int
        end position
    l_connect: bool
        connected at left side?
    r_connect: bool
        connected at right side?
    
    Returns
    -------
    tuple
        int, int (start position, end position)"""
    return posl if l_connect else posl + 1, posr if r_connect else posr - 1

def _get_connect(e_id):
    """Checks if given entity shall be connected to left/right adjacent
    entity.
    
    Parameters
    ----------
    e_id: str
        string of entity-ID
    
    Returns
    -------
    tuple
        * bool, connects to left neighbour
        * bool, connects to right neighbour"""
    return not e_id.startswith('_'), not e_id.endswith('_')

def strip_id(e_id, l_connect, r_connect):
    """Removes leading/trailing character when l_connect/r_connect.
    
    Parameters
    ----------
    e_id: str
        string of entity-ID
    l_connect: bool
        entity shall be connected to left neighbour
    r_connect:
        entity shall be connected to right neighbour
    
    Returns
    -------
    str
        stripped e_id"""
    return (
        e_id if l_connect and r_connect else
        # strip one leading and one trailing underscore
        e_id[0 if l_connect else 1:None if r_connect else -1])    
        
def _correct_id_pos(e_id, poss):
    """Corrects position and strips id in case of leading/trailing underscore
    
    Parameters
    ----------
    e_id: str
        ID of entity
    poss: tuple
        int, int (start position, end position - exclusive)

    Returns
    -------
    tuple
        * str, ID
        * tuple int, int (start position, end position)"""
    l_connect, r_connect = _get_connect(e_id)
    return (
        strip_id(e_id, l_connect, r_connect),
        _get_positions(*poss, l_connect, r_connect))

def _add_connects(poss, e_id):
    """Leading/trailing underscore means no connection to left/right.
    The function checks connections, corrects positions and ID.
    
    Parameters
    ----------
    poss: tuple
        int, int (start position, end position - exclusive)
    e_id: str
        ID of entity
        
    Returns
    -------
    tuple
        * tuple int, int (start position, end position)
        * str, ID
        * bool, left connection?
        * bool, right connection?"""
    l_connect, r_connect = _get_connect(e_id)
    return (
        _get_positions(*poss, l_connect, r_connect), 
        (strip_id(e_id, l_connect, r_connect), 
         l_connect, 
         r_connect))

def _neighbourids(infos):
    """Returns IDs of left/right nodes connected by an edge to current node.
    
    Parameters
    ----------
    info: array_like
        tuple (str, bool, bool), (ID, connects_l, connects_r)
    
    Returns
    -------
    tuple
        str"""
    # info: tuple(ID, connects_l, connects_r)
    l_info = infos[-3] if 2 < len(infos) else None
    r_info = infos[-1]
    c_info = infos[-2]
    l_connected = c_info[1] and (l_info[2] if l_info else False)
    r_connected = c_info[2] and r_info[1]
    if l_connected:
        return (l_info[0], r_info[0]) if r_connected else (l_info[0],)
    elif r_connected:
        return r_info[0],
    return _empty_tuple

def _leftneighbourid(info):
    """Returns a tuple of one ID if a left neighbour exists else
    returns an empty tuple."""
    return (info[0],) if info[2] else _empty_tuple

def _insert_edges(entities):
    """Adds edge tuples in the sequence of nodes. '_' on left/right side of ID
    means that node is not connected to left/right neighbour. The function
    does not insert an edge in this case.
    
    Parameter
    ---------
    entities: iterable
        tuple, created by parsing function
            * int, int (pos_x, pos_y)
            * entity data
    Yields
    ------
    tuple
        * (int, int), pos_x, pos_y
        * 'node'|'edge'
        * data of node or edge
        * ..."""
    pre_poss, pre_info = _add_connects(*entities[0])
    other_infos = [pre_info]
    for e_poss, e_info in (_add_connects(*e) for e in entities[1:]):
        other_infos.append(e_info)
        yield pre_poss, 'node', pre_info[0], _neighbourids(other_infos)
        if pre_info[2] and e_info[1]:
            start = pre_poss[1]
            end = e_poss[0]
            yield (start, end), 'edge', (pre_info[0], e_info[0])
        pre_poss = e_poss
        pre_info = e_info
    yield (
        pre_poss, 
        'node', 
        pre_info[0], 
        (_leftneighbourid(other_infos[-2]) 
         if (pre_info[1] and 1 < len(other_infos)) else _empty_tuple))

def _get_collect_atts(atts):
    """Creates a function returning attributes for a given interval of 
    positions (columns).
    
    Parameters
    ----------
    atts: iterable
        tuple int, some_data, 
        (the iterable is sorted according to position)
    
    Returns
    -------
    function
        (int,int)-yields->(some_data)"""
    atts_iter = iter(atts if atts else ())
    pos = -1
    data = None
    def collect(start, end):
        """Yields data whose pos is in interval [start, end).
        Maintains an internal state containing attributes sorted according
        to their positions. Moves in this list to greater position only.
        That means that for subsequent calls the interval must also
        grow towards greater positions.
        
        Parameters
        ----------
        start: int
            start position
        end: int
            last position (exclusive)
        
        Yields
        ------
        some_data"""
        nonlocal pos
        nonlocal data
        theend = start + end, None # if empty string end < start
        while pos < start:
            pos, data = next(atts_iter, theend)
        while pos < end:
            yield data
            pos, data = next(atts_iter, theend)
    return collect

def _merge_dicts(dicta, dictb):
    """Merge dictb into dicta if dctb exists, return dicta otherwise."""
    return {**dicta, **dictb} if dictb else dicta

def _add_atts(sorted_entities, sorted_atts):
    """Adds attributes having suitable position to entities (nodes/edges).
    
    Parameters
    ----------
    sorted_entities: iterable
        tuples, sorted according to start position
    sorted_atts: iterable
        tuples, sorted according to position 
        (which is the position of the left most characters)
    
    Yields
    ------
    tuple
        ...
        * dict of attributes"""
    atts = _get_collect_atts(sorted_atts)
    if sorted_entities:
        for e in sorted_entities:
            start, end = e[0]
            yield *e[1:], reduce(_merge_dicts, atts(start, end), _empty_dict)

def _entities_and_atts(mydict):
    """Extracts 'entities' and 'atts' from mydict. Returns a tuple
    of the obtained values. If any of the keys is not in mydict an empty
    tuple is returned instead.
    
    Parameters
    ----------
    mydict: dict
    
    Returns
    -------
    tuple"""
    return (
        mydict.get('entities', _empty_tuple), 
        mydict.get('atts', _empty_tuple))

_get_start = itemgetter(0)

def parse_graph(textlines):
    """This function is intended for input of small graphs using a string.
    The function parses the lines and returns nodes and edges. Nodes and
    edges can have attributes.

    example_string ('-' characters are used to improve readability for humans,
    '-' has no meaning and is not processed, other non-word characters may also 
    be used for the purpose of improved readability):
    ::
        
            cn=0-1
                  a=10
        a=15      b=30
        n0-------n1----------n2
                     cn=1-2   a=hello
            
                  a=30     
        n0-------n3----------n4
                     cn=3-4 row=2

    [*parse(example_string)] produces a list of tuples:
    ::
        [
            ('node', 'n0', ('n1',), {'a': '15'}), 
            ('edge', ('n0', 'n1'), {'cn': '0-1'}), 
            ('node', 'n1', ('n0', 'n2'), {'a': '10', 'b': '30'}), 
            ('edge', ('n1', 'n2'), {'cn': '1-2'}), 
            ('node', 'n2', ('n1',), {'a': 'hallo'}), 
            ('node', 'n0', ('n3',), {}), ('edge', ('n0', 'n3'), {}), 
            ('node', 'n3', ('n0', 'n4'), {'a': '30'}), 
            ('edge', ('n3', 'n4'), {'cn': '3-4', 'row': '2'}), 
            ('node', 'n4', ('n3',), {})
        ]        
    
    The format has three types of text-lines:
        * 'blank' line
        * comment line
        * node line
        * attribute line
    'Blank' Line:
        A blank line may contain an arbitrary sequence of non-word-characters.
    Comments:
        A line is a comment if first character is '#'. When '#' is not first
        the line is not a comment. Comments are ignored by the parser.
    Node line:
        A node line defines nodes and adjacent nodes. The parser creates an 
        edge between two nodes. A node is expressed as sequence of word 
        characters (a-zA-Z0-9_), left and right borders are non-word 
        characters, Leading/trailing underscore ('_') prevents addition of an 
        edge by the parser to the left/right. The leading/trailing
        underscore is not part of the node ID.
    Attribute line:
        Attributes are key-value pairs, which are two strings separated by
        character '=' (example: myproperty=42). The key is a sequence of
        word characters, the value a sequence of word characters plus
        '.', '+', '-'. A sequence of attributes are attributes separated by 
        one space (' ') or one comma (',').
    A Processing Unit is one node line with no, one or multiple attribute 
    lines. Units are separated by 'blank' lines.
    Sequences of attributes are associated to the node or edge sharing one
    position (column) with the first character of the attributes-sequence.
    
    Parameters
    ----------
    textlines: iterable
        strings to be parsed
    
    Returns
    -------
    collections.abc.Iterable
        * tuple (either 'node' or 'edge'), all values are strings: 
            * 'node': 
                * ('node', 
                  ID, 
                  tuple_of_adjacent_node_ids, 
                  dict_of_attributes)
            * 'edge': 
                * ('edge', 
                  (ID_of_left_node, ID_of_right_node), 
                  dict_of_attributes)
    
    Raises
    ------
    ValueError"""
    return chain.from_iterable(
        _add_atts(_insert_edges(e), sorted(atts, key=_get_start))
        for e, atts in (_entities_and_atts(l) for l in _scanlines(textlines)))

def parse(string):
    """Parses a string of graph data. More help is available at function
    'parse_graph'.
    
    Parameters
    ----------
    string: str
        text to parse
    
    Returns
    -------
    collections.abc.Iterable
        * tuple (either 'node' or 'edge'), all values are strings: 
            * 'node': 
                * ('node', 
                  ID, 
                  tuple_of_adjacent_node_ids, 
                  dict_of_attributes)
            * 'edge': 
                * ('edge', 
                  (ID_of_left_node, ID_of_right_node), 
                  dict_of_attributes)
    
    Raises
    ------
    ValueError"""
    return parse_graph(string.split('\n'))

def parse_positions(textlines):
    """Extracts nodes and positions of their first characters from iterable
    of text lines.
    
    Parameters
    ----------
    lines: iterable
        str
    
    Returns
    -------
    iterator
        tuple
            * tuple, float, position x, y
            * str, id
    
    Raises
    ------
    ValueError"""
    return (
        _correct_id_pos(*t)
        for t in chain.from_iterable(_scanentities(textlines)))

_sides = set(('l', 'r'))

def disconnect(schema='', devid='', side='r', nodeid='n'):
    """Helper function for manipulation of schema before parsing.
    Inserts an additional node with leading/trailing '_' character to the
    left or right of a node having the ID of devid. The function checks
    if the schema provides enough space before/after the addressed devid and
    inserts '_' + nodeid or nodeid + '_'. The function returns
    the modified string if the change is possible, None otherwise.
    
    Paramters
    ---------
    schema: str
        string to modify
    devid: str
        ID of node to disconnect
    side: 'l'|'r'
        side of node to be disconnected
        'l' - left, 'r' - right
    nodeid: str
        ID of new helper node to insert
    
    Returns
    -------
    str"""
    assert side in set(_sides)
    if side == 'l':
        subs = f'_{nodeid}'
        length = 1 + len(subs)
        pattern, replacement = (
            f'(?P<PRE>\w)([\s\W]{{{length}}})(?P<ID>[\s\W]+{devid})',
            r'\g<PRE> ' + subs + r'\g<ID>')
    else:
        subs = f'{nodeid}_'
        length = 1 + len(subs)
        pattern, replacement = (
            f'(?P<ID>{devid}[\s\W]+)([\s\W]{{{length}}})(?P<POST>\w)',
            r'\g<ID>' + subs + r' \g<POST>')
    expr = re.compile(pattern, re.MULTILINE)
    m = expr.search(schema)
    if m:
        start = m.string[:m.start()]
        subs = m.expand(replacement)
        end = m.string[m.end():]
        return f"{start}{subs}{end}"
    return None

def cut(schema='', devid='', side='', nodeid='n'):
    """Helper function for manipulation of multiline-string schema 
    before parsing.
    
    Parameters
    ----------
    schema: str
        string to modify
    devid: str
        ID of entity to disconnect
    side: 'l'|'r'
        left/right
    nodeid: str
        ID (name) of additional entity to be inserted as a terminating node
    
    Returns
    -------
    str
        modified schema"""
    if side in _sides:
        return disconnect(schema, devid, side, nodeid)
    res = disconnect(schema, devid, 'l', nodeid)
    return res if res else disconnect(schema, devid, 'r', nodeid)

def cuts(schema, devs=_empty_tuple):
    """Creates versions of schema by inserting a terminating node
    which is close to removing an edge.
    
    Parameters
    ----------
    schema: str
    
    devs: iterable
        str, IDs of nodes to modify one after another
        
    Returns
    -------
    iterator, str (version of schema)"""
    return (cut(schema, **dev) for dev in devs)
