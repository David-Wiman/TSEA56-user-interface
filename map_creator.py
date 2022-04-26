from PySide6.QtCore import QLineF, QRectF, QSizeF, Qt
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import (QApplication, QGraphicsItem, QGraphicsScene,
                               QGraphicsSceneMouseEvent, QGraphicsView,
                               QMainWindow, QSizePolicy)

from data import MapData


class Node(QGraphicsItem):
    """ A graphical representation of a stop on a Map """

    RADIUS = 60
    BORDER = QPen(Qt.black, 2)  # Color and thickness
    FILL_COLOR = Qt.white

    def __init__(self, parent, name: str):
        super().__init__()
        self.graph: MapCreatorWidget = parent

        self.setZValue(0)
        self.setFlag(self.ItemIsMovable)
        self.setFlag(self.ItemSendsGeometryChanges)
        self.setCacheMode(self.DeviceCoordinateCache)

        self.name = name

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
        last = self.graph.last_selected_node
        if last is None:
            print("Node {} selected".format(self.name))
            self.graph.last_selected_node = self
        else:
            # TODO: Check that a edge doesn't already exist
            print("Connected {}->{}".format(last.name, self.name))
            self.graph.add_edge(last, self)
            self.graph.last_selected_node = None

        self.graph.scene().update()
        return super().mouseDoubleClickEvent(event)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        # Runs when this node has been changed
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Check if user moved this node
            for edge in self.edge_list:
                edge.adjust()  # Adjust edges to new node position

            if self.pos().x() < -250:
                self.graph.delete_node(self)

        return super().itemChange(change, value)

    def boundingRect(self):
        return QRectF(-self.RADIUS/2, -self.RADIUS/2, self.RADIUS, self.RADIUS)

    def paint(self, painter: QPainter, _option, _widget):
        # Draws filled circle with a border
        painter.setBrush(self.FILL_COLOR)
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

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        """ If user double clicks an edge, delete it """
        print("Deleting edge " + self.name)
        self.delete()

        return super().mouseDoubleClickEvent(event)

    def boundingRect(self):
        start = self.line.p1()
        end = self.line.p2()

        rect = QRectF(start, QSizeF(end.x() - start.x(), end.y() - start.y()))
        return rect.normalized()

    def paint(self, painter: QPainter, _option, _widget):
        painter.setPen(QPen(Qt.black, 5, Qt.SolidLine,
                       Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(self.line)

        # Calculate where to put name label
        center_ptn = self.line.center()
        offset_x = self.line.normalVector().dx() / self.line.length() * 15
        offset_y = self.line.normalVector().dy() / self.line.length() * 15

        painter.drawText(center_ptn.x() + offset_x, center_ptn.y() + offset_y,
                         "{}: {}".format(self.name, self.weight))


class MapCreatorWidget(QGraphicsView):
    """ A widget for creating maps, represented as an undrirected weighted graph """

    WINDOW_SIZE = 800

    # Remeber which node was clicked on last
    last_selected_node: Node = None

    def __init__(self):
        super().__init__()
        self.setMinimumSize(self.WINDOW_SIZE, self.WINDOW_SIZE)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setWindowTitle("Kartritning")

        scene = QGraphicsScene()

        scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        scene.setSceneRect(-self.WINDOW_SIZE/2, -self.WINDOW_SIZE/2,
                           self.WINDOW_SIZE, self.WINDOW_SIZE)
        self.setScene(scene)

        # self.setCacheMode(QGraphicsView.CacheBackground)
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

        scene.addItem(Edge(self.nodes[0], self.nodes[1], 0))
        scene.addItem(Edge(self.nodes[1], self.nodes[8]))
        scene.addItem(Edge(self.nodes[2], self.nodes[4]))
        scene.addItem(Edge(self.nodes[3], self.nodes[8]))
        scene.addItem(Edge(self.nodes[8], self.nodes[4]))
        scene.addItem(Edge(self.nodes[8], self.nodes[6], 0))
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


if __name__ == "__main__":
    # Only here for debug purposes
    app = QApplication([])

    map = MapCreatorWidget()

    window = QMainWindow()
    window.setCentralWidget(map)
    window.show()

    app.exec()
