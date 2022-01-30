# graphparser

graphparser provides a primitive function for input of tiny graphs using a 
string e.g. as a part of a Jupyter notebook. The function 'parsing.parse' 
reads a multiline string and returns nodes and edges. Nodes and edges can have 
attributes.

Nodes are defined by writing words. Edges are implicitely defined for
adjacent words (which are IDs of the nodes). Attributes are strings
of key value pairs separated by an equal sign. Attributes of nodes are
placed above or below the nodes they should be assigned to. Attributes of 
edges are placed above or below the edges (space between two nodes).

Example_1
```
                distance=23km            temperature=220_K
node1                                   node2                           node3
 color=red          cost=48              price=45EUR age=10e6_d
 hight=20.0cm
```
However, the intention is to give some pseudo graphical support. 
Non-word-chracters can be used to make the structure visible.

Example_2
```
                distance=23km            temperature=220_K
node1<<------------------------------->>node2<<----------------------->>node3
 color=red          cost=48              price=45EUR age=10e6_d
 hight=20.0cm
```

running `[*parse(Example_1)]` creates a list of node- and edge-data:
```
[('node', 'node1', ('node2',), {'color': 'red', 'hight': '20.0cm'}),
 ('edge', ('node1', 'node2'), {'distance': '23km', 'cost': '48'}),
 ('node', 'node2', ('node1', 'node3'), 
     {'temperature': '220_K', 'price': '45EUR', 'age': '10e6_d'}),
 ('edge', ('node2', 'node3'), {}),
 ('node', 'node3', ('node2',), {})]
```

tuple of node-data:
    0. 'node'
    1. ID (name) of node
    2. tuple of adjacent nodes (IDs of nodes)
    3. dict of attributes

tuple of edge-data:
    0. 'edge'
    1. tuples of adjacent nodes (left_node, right_node)
    2. dict of attributes

One text line has either data of nodes or data of attributes. The type of 
the first detected entity is the type of the complete line. Attributes placed
in node lines are skipped and vice versa. Lines starting with '#' are ignored.
'Blank' lines are neither node- nor edge- nor comment-lines. At least one
'blank' line must exist between to node-lines (Arbitrary non-word characters 
are possible). No 'blank' line exists between node-lines and 
associated attributes.

Example_3
```
                distance=23km            temperature=220_K
node1<<------------------------------->>node2<<----------------------->>node3
 color=red          cost=48              price=45EUR age=10e6_d
 hight=20.0cm

    ~~~        ~~~        ~~~        ~~~        ~~~        ~~~        ~~~       
    
                distance=23km            temperature=220_K
node4<<------------------------------->>node5<<----------------------->>node6
 color=red          cost=48              price=45EUR age=10e6_d
 hight=20.0cm
 
```
The first character of the attribute is used to find the associated node/edge.
No edge is created when a node starts/ends with underscore. First and last
underscore of the node are not part of the ID (name). This gives the
chance to place nodes in one text line which have no relation.
Chains of attributes are attributes separated by a single comma or space. Again
The first character of the attribute sequence is used to find the assodiated
node/edge.