from PySide6.QtCore import QLineF, QPointF, QRectF, QSizeF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (QApplication, QGraphicsItem, QGraphicsScene,
                               QGraphicsSceneMouseEvent, QGraphicsView,
                               QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                               QPushButton, QSizePolicy, QStackedWidget,
                               QWidget)

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

        self.name = start_node.name + end_node.name  # Combine both node names
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

    def set_weight(self, new_weight: int):
        """ Updates edge's weight, or deletes it if it was 0 """
        print("New weight: " + str(new_weight))
        self.weight = abs(new_weight)  # No negative weights
        self.popup.close()

        if self.weight == 0:
            # Edge weight 0 means delete edge
            print("Deleting edge " + self.name)
            self.delete()

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        """ Opens popup on double click where user can change weight """

        self.popup = SetWeightWidget(self.weight, self.set_weight)
        self.popup.show()

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


class SetWeightWidget(QWidget):
    """ Small popup where user can enter a new edge weight """

    def __init__(self, weight: int, change_weight):
        super().__init__()

        layout = QHBoxLayout(self)
        weight_box = QLineEdit(str(weight))
        layout.addWidget(QLabel("weight"))
        layout.addWidget(weight_box)

        # Update weight when user presses enter
        weight_box.returnPressed.connect(
            lambda: change_weight(int(weight_box.text())))


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
        self.scale(1, 1)

        self.nodes: list[Node] = []
        self.draw_nodes()

    def draw_nodes(self):
        scene = self.scene()
        self.nodes = [Node(self, "A"), Node(self, "B"), Node(self, "C"),
                      Node(self, "D"), Node(self, "E"), Node(self, "F"),
                      Node(self, "G"), Node(self, "H"), Node(self, "I")]

        for node in self.nodes:
            scene.addItem(node)

        scene.addItem(Edge(self.nodes[0], self.nodes[1]))
        scene.addItem(Edge(self.nodes[1], self.nodes[8]))
        scene.addItem(Edge(self.nodes[2], self.nodes[4]))
        scene.addItem(Edge(self.nodes[3], self.nodes[8]))
        scene.addItem(Edge(self.nodes[8], self.nodes[4]))
        scene.addItem(Edge(self.nodes[8], self.nodes[6]))
        scene.addItem(Edge(self.nodes[4], self.nodes[7]))
        scene.addItem(Edge(self.nodes[6], self.nodes[5]))
        scene.addItem(Edge(self.nodes[7], self.nodes[6]))

        space_const = Node.RADIUS * 2
        self.nodes[8].setPos(0, 0)
        self.nodes[0].setPos(-space_const, -space_const)
        self.nodes[1].setPos(0, -space_const)
        self.nodes[2].setPos(space_const, -space_const)
        self.nodes[3].setPos(-space_const, 0)
        self.nodes[4].setPos(space_const, 0)
        self.nodes[5].setPos(-space_const, space_const)
        self.nodes[6].setPos(0, space_const)
        self.nodes[7].setPos(space_const, space_const)

    def add_node(self, name: str):
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

    def drawBackground(self, painter: QPainter, _):
        painter.fillRect(self.sceneRect(), Qt.gray)

    def load_map(map_data: MapData):
        """ Populates graph from a MapData instance """
        pass

    def get_map() -> MapData:
        """ Returns a MapData instance from current graph """
        pass


class MapCreatorWindow(QStackedWidget):

    WINDOW_SIZE = 800

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Kartritning")
        self.setMinimumSize(self.WINDOW_SIZE,
                            self.WINDOW_SIZE)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        creator_widget = MapCreatorWidget()
        self.addWidget(creator_widget)
        add_node_btn = QPushButton("Add node", self)
        add_node_btn.clicked.connect(lambda: creator_widget.add_node("_"))


if __name__ == "__main__":
    # Only here for debug purposes
    app = QApplication([])

    map = MapCreatorWindow()

    window = QMainWindow()
    window.setCentralWidget(map)
    window.show()

    app.exec()
