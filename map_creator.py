from PySide6.QtCore import QLineF, QRectF, QSizeF, Qt
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import (QApplication, QGraphicsItem, QGraphicsScene,
                               QGraphicsView, QMainWindow)

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


class Edge(QGraphicsItem):
    """ Represents an edge connecting two Nodes """

    def __init__(self, start_node: Node, end_node: Node):
        super().__init__()
        self.setAcceptedMouseButtons(Qt.NoButton)
        self.setZValue(-1)

        self.line = QLineF()
        self.start = start_node
        self.end = end_node

        self.name = start_node.name + end_node.name  # Combine both node names
        self.weight = 1  # Default weight

        self.start.addEdge(self)
        self.end.addEdge(self)

        self.adjust()

    def get_other_node(self, node: Node):
        """ Returns the other node this edge is connected to """
        if node != self.start and node != self.end:
            print("Error, node wasn't connected with this edge")
            return

        return self.start if node == self.end else self.end

    def adjust(self):
        self.prepareGeometryChange()

        self.line.setP1(self.start.pos())
        self.line.setP2(self.end.pos())

    def boundingRect(self):
        pen_width = 5
        extra = (pen_width + 10) / 2.0

        start = self.line.p1()
        end = self.line.p2()

        rect = QRectF(start, QSizeF(end.x() - start.x(), end.y() - start.y()))
        rect = rect.normalized().adjusted(-extra, -extra, -extra, -extra)
        return rect

    def paint(self, painter: QPainter, _option, _widget):
        painter.setPen(QPen(Qt.black, 5, Qt.SolidLine,
                       Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(self.line)


class MapCreatorWidget(QGraphicsView):
    """ A widget for creating maps """

    WINDOW_SIZE = 800

    def __init__(self):
        super().__init__()
        self.setMaximumSize(self.WINDOW_SIZE, self.WINDOW_SIZE)
        self.setWindowTitle("Kartritning")

        scene = QGraphicsScene()

        scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        scene.setSceneRect(-self.width()/2, -self.width()/2,
                           self.width(), self.width())
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
