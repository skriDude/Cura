# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional, TYPE_CHECKING

from PyQt5.QtCore import QObject, pyqtSlot

from UM.i18n import i18nCatalog

if TYPE_CHECKING:
    from cura.CuraApplication import CuraApplication


#
# This manager provides (convenience) functions to the Machine Settings Dialog QML to update certain machine settings.
#
class MachineSettingsManager(QObject):

    def __init__(self, application: "CuraApplication", parent: Optional["QObject"] = None) -> None:
        super().__init__(parent)
        self._i18n_catalog = i18nCatalog("cura")

        self._application = application

    # Force rebuilding the build volume by reloading the global container stack. This is a bit of a hack, but it seems
    # quite enough.
    @pyqtSlot()
    def forceUpdate(self) -> None:
        self._application.getMachineManager().globalContainerChanged.emit()

    # Function for the Machine Settings panel (QML) to update the compatible material diameter after a user has changed
    # an extruder's compatible material diameter. This ensures that after the modification, changes can be notified
    # and updated right away.
    @pyqtSlot(int)
    def updateMaterialForDiameter(self, extruder_position: int) -> None:
        # Updates the material container to a material that matches the material diameter set for the printer
        self._application.getMachineManager().updateMaterialWithVariant(str(extruder_position))

    @pyqtSlot(int)
    def setMachineExtruderCount(self, extruder_count: int) -> None:
        # Note: this method was in this class before, but since it's quite generic and other plugins also need it
        # it was moved to the machine manager instead. Now this method just calls the machine manager.
        self._application.getMachineManager().setActiveMachineExtruderCount(extruder_count)

    # FIXME(Lipu): Better document what this function does, especially the fuzzy gcode flavor and has_materials logic
    #              regarding UM2 and UM2+
    # Function for the Machine Settings panel (QML) to update after the usre changes "Number of Extruders".
    @pyqtSlot()
    def updateHasMaterialsMetadata(self):
        machine_manager = self._application.getMachineManager()
        material_manager = self._application.getMaterialManager()

        global_stack = machine_manager.activeMachine

        definition = global_stack.definition
        if definition.getProperty("machine_gcode_flavor", "value") != "UltiGCode" or definition.getMetaDataEntry(
                "has_materials", False):
            # In other words: only continue for the UM2 (extended), but not for the UM2+
            return

        extruder_positions = list(global_stack.extruders.keys())
        has_materials = global_stack.getProperty("machine_gcode_flavor", "value") != "UltiGCode"

        material_node = None
        if has_materials:
            global_stack.setMetaDataEntry("has_materials", True)
        else:
            # The metadata entry is stored in an ini, and ini files are parsed as strings only.
            # Because any non-empty string evaluates to a boolean True, we have to remove the entry to make it False.
            if "has_materials" in global_stack.getMetaData():
                global_stack.removeMetaDataEntry("has_materials")

        # set materials
        for position in extruder_positions:
            if has_materials:
                material_node = material_manager.getDefaultMaterial(global_stack, position, None)
            machine_manager.setMaterial(position, material_node)

        self.forceUpdate()
