import QtQuick
import QtQuick.Layouts
import Quickshell
import qs.Services
import qs.Services as Services
import qs.Common
import qs.Widgets.common

Item {
    id: root

    property var screen: null
    property bool vertical: false
    readonly property bool showValue: PersonalizationConfig.barShowValues

    implicitWidth: mouseArea.implicitWidth
    implicitHeight: mouseArea.implicitHeight

    BarActionButton {
        id: mouseArea
        anchors.fill: parent
        vertical: root.vertical
        expandedContent: root.showValue
        contentItem: Item {
            implicitWidth: content.implicitWidth
            implicitHeight: content.implicitHeight
            GridLayout {
                id: content
                anchors.centerIn: parent
                columns: root.vertical ? 1 : 2
                rowSpacing: Sizes.barItemSpacing
                columnSpacing: Sizes.barLabelSpacing
                ArcGauge {
                    id: gauge
                    Layout.preferredWidth: Sizes.barControlCircleSize
                    Layout.preferredHeight: Sizes.barControlCircleSize
                    Layout.alignment: Qt.AlignCenter

                    value: Services.Volume.sinkVolume
                    progressColor: (Services.Volume.sinkMuted || Services.Volume.sinkVolume <= 0)
                                   ? Appearance.colors.colError : Appearance.colors.colPrimary
                    trackColor: Appearance.colors.colLayer2Hover
                    handleColor: Appearance.colors.colOnSurface
                    iconColor: (Services.Volume.sinkMuted || Services.Volume.sinkVolume <= 0)
                               ? Appearance.colors.colError : Appearance.colors.colOnSurface

                    icon: {
                        if (Services.Volume.isHeadphone)
                            return "headphones";
                        if (Services.Volume.sinkMuted || Services.Volume.sinkVolume <= 0)
                            return "volume_off";
                        if (Services.Volume.sinkVolume < 0.5)
                            return "volume_down";
                        return "volume_up";
                    }
                }

                Text {
                    id: valueText
                    visible: root.showValue
                    text: Math.round(Services.Volume.sinkVolume * 100) + "%"
                    font.family: Fonts.numeric
                    font.pixelSize: 12
                    color: Appearance.colors.colOnSurface
                    Layout.alignment: Qt.AlignCenter
                }
            }
        }
        Accessible.name: tooltip.text

        onClicked: {
            if (root.screen && root.screen.name)
                WidgetState.quickSettingsScreenName = root.screen.name;
            if (WidgetState.quickSettingsOpen && WidgetState.quickSettingsView === "audio") {
                WidgetState.quickSettingsOpen = false;
            } else {
                WidgetState.quickSettingsView = "audio";
                WidgetState.quickSettingsOpen = true;
            }
        }
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.NoButton
        onWheel: wheel => {
                     const delta = wheel.angleDelta.y || wheel.pixelDelta.y;
                     if (delta === 0) {
                         wheel.accepted = false;
                         return;
                     }
                     wheel.accepted = Services.Volume.setSinkVolume(Services.Volume.sinkVolume + (delta > 0
                                                                                                  ? 0.05 :
                                                                                                    -0.05));
                 }
    }

    PopupToolTip {
        id: tooltip
        extraVisibleCondition: mouseArea.pointerHovered
        text: (Services.Volume.sinkMuted ? qsTr("Volume: muted") : qsTr("Volume: ") + Math.round(
                                               Services.Volume.sinkVolume * 100) + "%") + qsTr(
                  "\nScroll to adjust; click to open sound")
    }
}
