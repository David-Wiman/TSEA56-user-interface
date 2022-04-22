from PySide6.QtCore import QLineF, QPointF, QRectF, QSizeF, Qt
from PySide6.QtGui import QColor, QKeyEvent, QPainter, QPen, QVector2D
from PySide6.QtWidgets import (QApplication, QGraphicsItem, QGraphicsScene,
                               QGraphicsSceneMouseEvent, QGraphicsView,
                               QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                               QPushButton, QSizePolicy, QStackedWidget,
                               QVBoxLayout, QWidget)
from backend import backend_signals

from data import MapData


class Node(QGraphicsItem):
    """ A graphical representation of a stop on a Map """

    RADIUS = 60
    BORDER = QPen(Qt.black, 2)  # Color and thickness
    FILL_COLOR = QColor("blue").lighter(150)

    def __init__(self, parent, name: str):
        super().__init__()
        self.graph: MapCreatorWidget = parent

        self.setZValue(0)
        self.setFlag(self.ItemIsMovable)
        self.setFlag(self.ItemSendsGeometryChanges)
        self.setCacheMode(self.DeviceCoordinateCache)

        self.name = name
        self.fill_color = self.FILL_COLOR

        self.edge_list: list[Edge] = []

    def remove_from_scene(self, scene: QGraphicsScene):
        """ Removes node and its edges from a scene """
        print("Deleting node " + self.name)
        for edge in self.edge_list:
            other = edge.get_other_node(self)
            if other is not None:
                other.disconnect_edge(edge)  # Disonnect edge from other node

            print("Deleting edge " + edge.name)
            scene.removeItem(edge)

        scene.removeItem(self)

    def set_name(self, new_name):
        """ Updates node's name """
        print("New name: " + str(new_name))
        self.name = str(new_name)

        for edge in self.edge_list:
            edge.update_name()  # Update all edge names

        # TODO: Check if name already is in use

        self.update()

    def disconnect_edge(self, edge_rm):
        """ Disconnect edge from this node """
        self.edge_list = [edge for edge in self.edge_list if edge != edge_rm]

    def addEdge(self, edge: 'Edge'):
        """ Adds an edge to this node """
        self.edge_list.append(edge)
        edge.adjust()

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        """ If user double clicks on two nodes, connect them """
        last = self.graph.selected_node

        if last == self:
            # This node already selected -> deselect
            print("Node {} deselected".format(self.name))
            self.graph.selected_node = None
            self.fill_color = self.FILL_COLOR
        elif last is None:
            # No node selected -> select
            print("Node {} selected".format(self.name))
            self.graph.selected_node = self
            self.fill_color = self.FILL_COLOR.lighter(110)
        else:
            # Another node selected -> connect to it with edge
            # TODO: Check that a edge doesn't already exist
            print("Connected {}->{}".format(last.name, self.name))
            self.graph.add_edge(last, self)
            self.graph.selected_node = None

        self.update()
        self.graph.scene().update()
        return super().mouseDoubleClickEvent(event)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        # Runs when this node has been changed
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Check if user moved this node
            for edge in self.edge_list:
                edge.adjust()  # Adjust edges to new node position

        return super().itemChange(change, value)

    def boundingRect(self):
        return QRectF(-self.RADIUS/2, -self.RADIUS/2, self.RADIUS, self.RADIUS)

    def paint(self, painter: QPainter, _option, _widget):
        # Draws filled circle with a border
        painter.setBrush(self.fill_color)
        painter.setPen(self.BORDER)
        painter.drawEllipse(-self.RADIUS/2, -self.RADIUS/2,
                            self.RADIUS, self.RADIUS)
        painter.drawText(-4, 5, self.name)


class Edge(QGraphicsItem):
    """ Represents an edge connecting two Nodes """

    def __init__(self, start_node: Node, end_node: Node, weight: int = 1):
        super().__init__()
        self.setZValue(-1)

        self.line = QLineF()
        self.start = start_node
        self.end = end_node

        self.update_name()
        self.weight = weight

        self.start.addEdge(self)
        self.end.addEdge(self)

        self.adjust()

    def get_other_node(self, node: Node):
        """ Returns the other node this edge is connected to """
        if node != self.start and node != self.end:
            print("Error, node wasn't connected with this edge")
            return

        return self.start if node == self.end else self.end

    def delete(self):
        """ Disconnect edge from nodes and remove from scene """
        if self.start is not None:
            self.start.disconnect_edge(self)
        if self.end is not None:
            self.end.disconnect_edge(self)

        super().scene().removeItem(self)

    def adjust(self):
        self.prepareGeometryChange()

        self.line.setP1(self.start.pos())
        self.line.setP2(self.end.pos())

    def update_name(self):
        """ Sets edge's name as combination of connecting nodes """
        self.name = self.start.name + self.end.name

    def set_weight(self, new_weight):
        """ Updates edge's weight, or deletes it if it was 0 """
        # print("New weight: " + str(new_weight))
        self.weight = abs(int(new_weight))  # No negative or non-int weights

        if self.weight == 0:
            # Edge weight 0 means delete edge
            # print("Deleting edge " + self.name)
            self.delete()

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        """ Opens popup on double click where user can change weight """

        popup = SetPropertyWidget(
            "weight", str(self.weight), self.set_weight)
        popup.show()

        return super().mouseDoubleClickEvent(event)

    def boundingRect(self):
        start = self.line.p1()
        end = self.line.p2()

        rect = QRectF(start, QSizeF(end.x() - start.x(), end.y() - start.y()))
        return rect.normalized()

    def paint(self, painter: QPainter, _option, _widget):
        painter.setPen(QPen(Qt.black, 5, Qt.SolidLine,
                       Qt.RoundCap, Qt.RoundJoin))

        # Draw edge
        painter.drawLine(self.line)

        # Calculate where to put edge label
        offset_x = self.line.normalVector().dx() / self.line.length() * 15 - 15
        offset_y = self.line.normalVector().dy() / self.line.length() * 15 + 5
        text_pos = QPointF(self.line.center().x() + offset_x,
                           self.line.center().y() + offset_y)

        # Draw edge label
        font = painter.font()
        font.setPixelSize(20)
        painter.setFont(font)
        painter.setPen(Qt.white)
        painter.drawText(text_pos, "{}: {}".format(self.name, self.weight))


class SetPropertyWidget(QWidget):
    """ Small popup where user can set a property """

    def __init__(self, label: str, value, change_value):
        super().__init__()

        layout = QHBoxLayout(self)
        self.value_edit_box = QLineEdit(str(value))
        layout.addWidget(QLabel(label))
        layout.addWidget(self.value_edit_box)

        # Update value when user presses enter
        self.value_edit_box.returnPressed.connect(
            lambda: self.change_value_and_close(change_value))

    def change_value_and_close(self, change_value):
        change_value(self.value_edit_box.text())
        self.close()


class MapCreatorWidget(QGraphicsView):
    """ A widget for creating maps, represented as an undirected weighted graph """

    SCENESIZE = 800

    # Remeber which node was clicked on last
    selected_node: Node = None

    def __init__(self):
        super().__init__()

        scene = QGraphicsScene()

        scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        scene.setSceneRect(-self.SCENESIZE/2, -self.SCENESIZE/2,
                           self.SCENESIZE, self.SCENESIZE)
        self.setScene(scene)

        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        self.nodes: list[Node] = []
        self.draw_nodes()

    def draw_nodes(self):
        scene = self.scene()
        self.nodes = [Node(self, "A"), Node(self, "B"), Node(self, "C"),
                      Node(self, "D"), Node(self, "E"), Node(self, "F"),
                      Node(self, "G"), Node(self, "H"), Node(self, "I"),
                      Node(self, "J"), Node(self, "K"), Node(self, "L"),
                      Node(self, "M")]

        for node in self.nodes:
            scene.addItem(node)

        scene.addItem(Edge(self.nodes[0], self.nodes[1], 1))
        scene.addItem(Edge(self.nodes[0], self.nodes[10], 5))
        scene.addItem(Edge(self.nodes[1], self.nodes[2], 2))
        scene.addItem(Edge(self.nodes[1], self.nodes[11], 2))
        scene.addItem(Edge(self.nodes[2], self.nodes[3], 1))
        scene.addItem(Edge(self.nodes[2], self.nodes[11], 2))
        scene.addItem(Edge(self.nodes[3], self.nodes[4], 1))
        scene.addItem(Edge(self.nodes[4], self.nodes[5], 2))
        scene.addItem(Edge(self.nodes[5], self.nodes[6], 3))
        scene.addItem(Edge(self.nodes[6], self.nodes[7], 1))
        scene.addItem(Edge(self.nodes[7], self.nodes[8], 2))
        scene.addItem(Edge(self.nodes[7], self.nodes[12], 2))
        scene.addItem(Edge(self.nodes[8], self.nodes[9], 1))
        scene.addItem(Edge(self.nodes[8], self.nodes[12], 2))
        scene.addItem(Edge(self.nodes[9], self.nodes[10], 1))
        scene.addItem(Edge(self.nodes[11], self.nodes[12], 1))

        space_const = Node.RADIUS * 1.5
        self.nodes[0].setPos(-2*space_const, 2*space_const)
        self.nodes[1].setPos(-space_const, 2*space_const)
        self.nodes[2].setPos(space_const, 2*space_const)
        self.nodes[3].setPos(2*space_const, 2*space_const)
        self.nodes[4].setPos(3*space_const, 2*space_const)
        self.nodes[5].setPos(4*space_const, 0)
        self.nodes[6].setPos(3*space_const, -2*space_const)
        self.nodes[7].setPos(space_const, -2*space_const)
        self.nodes[8].setPos(-space_const, -2*space_const)
        self.nodes[9].setPos(-2*space_const, -2*space_const)
        self.nodes[10].setPos(-3*space_const, -2*space_const)
        self.nodes[11].setPos(0, space_const)
        self.nodes[12].setPos(0, -space_const)

    def keyReleaseEvent(self, event: QKeyEvent):
        """ Delete selected node when user presses delete """
        if event.key() == Qt.Key_Delete:
            self.delete_selected_node()
        return super().keyReleaseEvent(event)

    def add_node(self, name: str = ""):
        """ Add a new node to scene """
        node = Node(self, name)
        self.nodes.append(node)
        self.scene().addItem(node)
        node.setPos(15, 15)

    def add_edge(self, node1, node2):
        """ Connect two nodes with an edge """
        edge = Edge(node1, node2)
        self.scene().addItem(edge)

    def delete_node(self, node: Node):
        """ Deletes node from widget """
        node.remove_from_scene(self.scene())
        self.nodes = [n for n in self.nodes if n != node]

    def delete_selected_node(self):
        """ Deletes selected node from widget """
        if self.selected_node is not None:
            self.selected_node.remove_from_scene(self.scene())
            self.selected_node = None

    def change_selected_node_name(self):
        """ Changes name of selected node """
        if self.selected_node is not None:
            popup = SetPropertyWidget("Name", "",
                                      self.selected_node.set_name)
            popup.show()

    def drawBackground(self, painter: QPainter, _):
        painter.fillRect(self.sceneRect(), Qt.gray)

    def load_map(map_data: MapData):
        """ Populates graph from a MapData instance """
        pass

    def get_map(self) -> MapData:
        """ Returns a MapData instance from current graph """
        return create_map_from_graph(self.nodes)


class MapCreatorWindow(QStackedWidget):

    WINDOW_SIZE = 800

    def __init__(self, creator_widget: MapCreatorWidget):
        super().__init__()

        self.setWindowTitle("Kartritning")
        self.setMinimumSize(self.WINDOW_SIZE,
                            self.WINDOW_SIZE)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.creator_widget = MapCreatorWidget()
        self.addWidget(self.creator_widget)
        self.create_buttons()

    def create_buttons(self):
        """ Create add and delete node buttons """
        buttons = QWidget(self)
        buttons.setFixedSize(120, 120)
        btn_layout = QVBoxLayout()

        add_node_btn = QPushButton("Add node")
        add_node_btn.clicked.connect(lambda: self.creator_widget.add_node())
        btn_layout.addWidget(add_node_btn)

        del_node_btn = QPushButton("Delete node")
        del_node_btn.clicked.connect(self.creator_widget.delete_selected_node)
        btn_layout.addWidget(del_node_btn)

        name_node_btn = QPushButton("Change name")
        name_node_btn.clicked.connect(
            self.creator_widget.change_selected_node_name)
        btn_layout.addWidget(name_node_btn)

        save_graph_btn = QPushButton("Save map")
        save_graph_btn.clicked.connect(self.save_map)
        btn_layout.addWidget(save_graph_btn)

        buttons.setLayout(btn_layout)

    def save_map(self):
        """ Saves the map as json and updates saved map image """
        with open("map/new_map.json", "w") as file:
            file.write(self.creator_widget.get_map().to_json())

        self.creator_widget.grab().save("res/map.png")
        backend_signals().new_map.emit()
        self.close()


# TODO Handle left/right
# TODO Handle intersections


def get_sorted_next_nodes(prev: Node, curr: Node):
    """ Returns the next nodes sorted right to left, relative to prev->curr direction """
    next_nodes = [edge.get_other_node(curr) for edge in curr.edge_list]
    next_nodes.remove(prev)  # Dont return previous node

    # Sorts next nodes based on cross product with the vector prev -> curr.
    # Will be <0 if node is to the right, >0 if on the left and =0 if neither.
    next_nodes.sort(key=lambda next: (curr.x()-prev.x()) * (prev.y()-next.y()) -
                                     (prev.y()-curr.y()) * (next.x()-prev.x()))

    return next_nodes


def edge_weight_str(node_list: list[Node], node_str1: str, node_str2: str):
    node1: Node
    node2: Node

    for node in node_list:
        if node.name == node_str1[0:-1]:
            node1 = node
        elif node.name == node_str2[0:-1]:
            node2 = node

    return edge_weight(node1, node2)


def edge_weight(node1: Node, node2: Node):
    for edge in node1.edge_list:
        if edge.get_other_node(node1).name == node2.name:
            return edge.weight

    print("No edge found between", node1.name, "and", node2.name)
    return None


def connect_node_pair(map: MapData, previous: Node, current: Node,
                      visited: list[str], intersections: list[list[Node]],
                      reversed=False):

    print("Visiting " + current.name)
    next_nodes = get_sorted_next_nodes(previous, current)

    if (len(current.edge_list) == 3 and
            not any(current in intersection for intersection in intersections)):
        # Node is in intersection, and not already added to list
        print("Intersection node", current.name)
        intersections.append(next_nodes + [current])

    current1 = current.name + "1"
    current2 = current.name + "2"

    if current1 in visited or current2 in visited:
        # Node probably already connected
        print("Return from " + current.name)
        return

    visited.extend([current1, current2])

    for next in next_nodes:
        next1 = next.name + "1"
        next2 = next.name + "2"

        if next1 in visited or next2 in visited:
            # Node probably already connected
            print("Skipping " + next.name)
            continue

        if reversed:
            map.connect_node(current1, next1, edge_weight(current, next))
            map.connect_node(next2, current2, edge_weight(next, current))
        else:
            map.connect_node(next1, current1, edge_weight(next, current))
            map.connect_node(current2, next2, edge_weight(current, next))

        # Connect next node pair
        connect_node_pair(map, current, next, visited, intersections, reversed)

        # Loop direction swaps
        print("Direction swap")
        reversed = not reversed

    print("Return from", current.name)


def create_map_from_graph(nodes: list[Node]) -> MapData:
    map = MapData()
    visited = []
    intersections = []  # Remember nodes in intersections for more processing

    prev_node = nodes[0]
    start_node = nodes[1]
    map.connect_node(prev_node.name+"2", start_node.name +
                     "2", edge_weight(prev_node, start_node))
    map.connect_node(start_node.name+"1", prev_node.name +
                     "1", edge_weight(prev_node, start_node))

    connect_node_pair(map, prev_node, start_node, visited, intersections)
    print("Intersections: ", len(intersections))
    for intersection in intersections:
        print([node.name for node in intersection])
        connect_intersection(map, intersection)
    return map


def connect_intersection(map: MapData, intersec_nodes: list[Node]):
    entry_nodes = set()
    exit_nodes = set()
    node_names = [n.name + "1" for n in intersec_nodes] + \
        [n.name + "2" for n in intersec_nodes]

    for node in node_names:
        for neighbour in map.map[node]:
            # Check if node is an exit node
            if neighbour not in node_names:
                # Node is an exit node
                exit_nodes.add(node)

        print(node, map.map[node])

    print("Exit nodes", exit_nodes)
    # Assume exit nodes are labeled correctly, remove duplicates from entry
    for node in entry_nodes.intersection(exit_nodes):
        entry_nodes.remove(node)

    entry_nodes = set(node_names) - exit_nodes

    print("Entry nodes", entry_nodes)

    for entry in entry_nodes:
        for exit in exit_nodes:
            if exit[0:-1] != entry[0:-1]:
                # Connect all entries to exits, except on the same side (eg L1 and L2)
                map.connect_node(entry, exit, edge_weight_str(
                    intersec_nodes, entry, exit))


if __name__ == "__main__":
    # Only here for debug purposes
    app = QApplication([])

    map = MapCreatorWindow()

    window = QMainWindow()
    window.setCentralWidget(map)
    window.show()

    app.exec()
