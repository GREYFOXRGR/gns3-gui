# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 GNS3 Technologies Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Configuration page for IOU devices.
"""

import os

from gns3.qt import QtCore, QtWidgets
from gns3.servers import Servers
from gns3.dialogs.node_properties_dialog import ConfigurationError
from gns3.utils.get_resource import get_resource
from gns3.utils.get_default_base_config import get_default_base_config
from ..ui.iou_device_configuration_page_ui import Ui_iouDeviceConfigPageWidget


class iouDeviceConfigurationPage(QtWidgets.QWidget, Ui_iouDeviceConfigPageWidget):

    """
    QWidget configuration page for IOU devices.
    """

    def __init__(self):

        super().__init__()
        self.setupUi(self)
        self.uiStartupConfigToolButton.clicked.connect(self._startupConfigBrowserSlot)
        self.uiPrivateConfigToolButton.clicked.connect(self._privateConfigBrowserSlot)
        self.uiIOUImageToolButton.clicked.connect(self._iouImageBrowserSlot)
        self.uiDefaultValuesCheckBox.stateChanged.connect(self._useDefaultValuesSlot)
        self._current_iou_image = ""

        # location of the base config templates
        self._base_iou_l2_config_template = get_resource(os.path.join("configs", "iou_l2_base_startup-config.txt"))
        self._base_iou_l3_config_template = get_resource(os.path.join("configs", "iou_l3_base_startup-config.txt"))

    def _useDefaultValuesSlot(self, state):
        """
        Slot to enable or not the RAM and NVRAM spin boxes.
        """

        if state:
            self.uiRamSpinBox.setEnabled(False)
            self.uiNvramSpinBox.setEnabled(False)
        else:
            self.uiRamSpinBox.setEnabled(True)
            self.uiNvramSpinBox.setEnabled(True)

    def _iouImageBrowserSlot(self):
        """
        Slot to open a file browser and select an IOU image.
        """

        from .iou_device_preferences_page import IOUDevicePreferencesPage
        path = IOUDevicePreferencesPage.getIOUImage(self)
        if not path:
            return
        self.uiIOUImageLineEdit.clear()
        self.uiIOUImageLineEdit.setText(path)

        if "l2" in path:
            # set the default L2 base startup-config
            default_base_config = get_default_base_config(self._base_iou_l2_config_template)
            if default_base_config:
                self.uiStartupConfigLineEdit.setText(default_base_config)
        else:
            # set the default L3 base startup-config
            default_base_config = get_default_base_config(self._base_iou_l3_config_template)
            if default_base_config:
                self.uiStartupConfigLineEdit.setText(default_base_config)

    def _startupConfigBrowserSlot(self):
        """
        Slot to open a file browser and select a startup-config file.
        """

        config_dir = os.path.join(os.path.dirname(QtCore.QSettings().fileName()), "base_configs")
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select a startup-config file", config_dir)
        if not path:
            return

        if not os.access(path, os.R_OK):
            QtWidgets.QMessageBox.critical(self, "Startup-config", "Cannot read {}".format(path))
            return

        self.uiStartupConfigLineEdit.clear()
        self.uiStartupConfigLineEdit.setText(path)

    def _privateConfigBrowserSlot(self):
        """
        Slot to open a file browser and select a private-config file.
        """

        config_dir = os.path.join(os.path.dirname(QtCore.QSettings().fileName()), "base_configs")
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select a private-config file", config_dir)
        if not path:
            return

        if not os.access(path, os.R_OK):
            QtWidgets.QMessageBox.critical(self, "Private-config", "Cannot read {}".format(path))
            return

        self.uiPrivateConfigLineEdit.clear()
        self.uiPrivateConfigLineEdit.setText(path)

    def loadSettings(self, settings, node=None, group=False):
        """
        Loads the IOU device settings.

        :param settings: the settings (dictionary)
        :param node: Node instance
        :param group: indicates the settings apply to a group of routers
        """

        if not group:
            self.uiNameLineEdit.setText(settings["name"])

            if "console" in settings:
                self.uiConsolePortSpinBox.setValue(settings["console"])
            else:
                self.uiConsolePortLabel.hide()
                self.uiConsolePortSpinBox.hide()

            # load the IOU image path
            self.uiIOUImageLineEdit.setText(settings["path"])

        else:
            self.uiGeneralgroupBox.hide()

        if not node:
            # load the startup-config and private-config
            self.uiStartupConfigLineEdit.setText(settings["startup_config"])
            self.uiPrivateConfigLineEdit.setText(settings["private_config"])
        else:
            self.uiStartupConfigLabel.hide()
            self.uiStartupConfigLineEdit.hide()
            self.uiStartupConfigToolButton.hide()
            self.uiPrivateConfigLabel.hide()
            self.uiPrivateConfigLineEdit.hide()
            self.uiPrivateConfigToolButton.hide()

        # load advanced settings
        if "l1_keepalives" in settings:
            self.uiL1KeepalivesCheckBox.setChecked(settings["l1_keepalives"])
        else:
            self.uiL1KeepalivesCheckBox.hide()
        self.uiDefaultValuesCheckBox.setChecked(settings["use_default_iou_values"])
        self.uiRamSpinBox.setValue(settings["ram"])
        self.uiNvramSpinBox.setValue(settings["nvram"])

        # load the number of adapters
        self.uiEthernetAdaptersSpinBox.setValue(settings["ethernet_adapters"])
        self.uiSerialAdaptersSpinBox.setValue(settings["serial_adapters"])

        self.server = Servers.instance().getServerFromString(settings["server"])

    def saveSettings(self, settings, node=None, group=False):
        """
        Saves the IOU device settings.

        :param settings: the settings (dictionary)
        :param node: Node instance
        :param group: indicates the settings apply to a group of routers
        """

        # these settings cannot be shared by nodes and updated
        # in the node properties dialog.
        if not group:

            # set the device name
            name = self.uiNameLineEdit.text()
            if not name:
                QtWidgets.QMessageBox.critical(self, "Name", "IOU device name cannot be empty!")
            elif node and not node.validateHostname(name):
                QtWidgets.QMessageBox.critical(self, "Name", "Invalid name detected for IOU device: {}".format(name))
            else:
                settings["name"] = name

            if "console" in settings:
                settings["console"] = self.uiConsolePortSpinBox.value()

            # save the IOU image path
            ios_path = self.uiIOUImageLineEdit.text().strip()
            if ios_path:
                settings["path"] = ios_path
        else:
            del settings["name"]
            del settings["console"]

        if not node:
            # save the startup-config
            startup_config = self.uiStartupConfigLineEdit.text().strip()
            if not startup_config:
                settings["startup_config"] = ""
            elif startup_config != settings["startup_config"]:
                if os.access(startup_config, os.R_OK):
                    settings["startup_config"] = startup_config
                else:
                    QtWidgets.QMessageBox.critical(self, "Startup-config", "Cannot read the startup-config file")

            # save the private-config
            private_config = self.uiPrivateConfigLineEdit.text().strip()
            if not private_config:
                settings["private_config"] = ""
            elif private_config != settings["private_config"]:
                if os.access(private_config, os.R_OK):
                    settings["private_config"] = private_config
                else:
                    QtWidgets.QMessageBox.critical(self, "Private-config", "Cannot read the private-config file")

        # save advanced settings
        settings["l1_keepalives"] = self.uiL1KeepalivesCheckBox.isChecked()
        settings["use_default_iou_values"] = self.uiDefaultValuesCheckBox.isChecked()
        settings["ram"] = self.uiRamSpinBox.value()
        settings["nvram"] = self.uiNvramSpinBox.value()

        ethernet_adapters = self.uiEthernetAdaptersSpinBox.value()
        serial_adapters = self.uiSerialAdaptersSpinBox.value()
        if ethernet_adapters + serial_adapters > 16:
            QtWidgets.QMessageBox.warning(self, settings["name"], "The total number of adapters cannot exceed 16")
            raise ConfigurationError()

        if node:
            if settings["ethernet_adapters"] != ethernet_adapters or settings["serial_adapters"] != serial_adapters:
                # check if the adapters settings have changed
                node_ports = node.ports()
                for node_port in node_ports:
                    if not node_port.isFree():
                        QtWidgets.QMessageBox.critical(self, node.name(), "Changing the number of adapters while links are connected isn't supported yet! Please delete all the links first.")
                        raise ConfigurationError()

        settings["ethernet_adapters"] = ethernet_adapters
        settings["serial_adapters"] = serial_adapters
