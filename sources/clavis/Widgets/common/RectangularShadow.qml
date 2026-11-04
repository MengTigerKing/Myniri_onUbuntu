import QtQuick

Item {
    id: root

    property real blur: 0
    property bool cached: false
    property color color: "transparent"
    property real radius: 0
    property real spread: 0
    property var target
    property vector2d offset: Qt.vector2d(0, 0)

    visible: opacity > 0 && color.a > 0
    x: offset.x
    y: offset.y
    width: target ? target.width + 2 * spread : 0
    height: target ? target.height + 2 * spread : 0
    opacity: color.a

    Rectangle {
        anchors.fill: parent
        anchors.margins: -root.spread
        color: Qt.rgba(root.color.r, root.color.g, root.color.b, 1)
        radius: root.radius + root.spread
        opacity: 0.28
    }
}
