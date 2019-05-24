# Spine export
# Forked from Unofficial Spine Export (https://github.com/chartinger/krita-unofficial-spine-export)
# 

import os
import json
import re

from PyQt5.QtWidgets import (QFileDialog, QMessageBox)
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from krita import (Krita, Extension)


class SpineExport(Extension):

    def __init__(self, parent):
        super().__init__(parent)
        self.directory = None
        self.msgBox = None
        self.fileFormat = 'png'
        self.bonePattern = re.compile("\(bone\)|\[bone\]", re.IGNORECASE)
        self.mergePattern = re.compile("\(merge\)|\[merge\]", re.IGNORECASE)
        self.slotPattern = re.compile("\(slot\)|\[slot\]", re.IGNORECASE)
        self.skinPattern = re.compile("\(skin\)|\[skin\]", re.IGNORECASE)
    def setup(self):
        pass

    def createActions(self, window):
        action = window.createAction("spineexportAction", "Export to Spine", "tools/scripts")
        action.triggered.connect(self.exportDocument)

    def exportDocument(self):
        document = Krita.instance().activeDocument()

        if document is not None:
            if not self.directory:
                self.directory = os.path.dirname(document.fileName()) if document.fileName() else os.path.expanduser("~")
            self.directo1ry = QFileDialog.getExistingDirectory(None, "Select a folder to export Spine assets to", self.directory, QFileDialog.ShowDirsOnly)

            if not self.directory:
                self._alert('Abort!')
                return

            self.json = {
                "skeleton": {"images": self.directory},
                "bones": [{"name": "root"}],
                "slots": [],
                "skins": {"default": {}},
                "animations": {}
            }
            self.spineBones = self.json['bones']
            self.spineSlots = self.json['slots']
            self.spineDefaultSkin = self.json['skins']['default']

            Krita.instance().setBatchmode(True)
            self.document = document
            self._export(document.rootNode(), self.directory)
            Krita.instance().setBatchmode(False)
            with open('{0}/{1}'.format(self.directory, 'spine.json'), 'w') as outfile:
                json.dump(self.json, outfile, indent=2)
            self._alert("Spine export successful")
        else:
            self._alert("Please select a Document")

    def _alert(self, message):
        self.msgBox = self.msgBox if self.msgBox else QMessageBox()
        self.msgBox.setText(message)
        self.msgBox.exec_()

    def _export(self, node, directory, bone="root", xOffset=0, yOffset=0, slot=None):
        for child in node.childNodes():
            if "selectionmask" in child.type():
                continue

            if not child.visible():
                continue

            if '(ignore)' in child.name():
                continue

            if child.childNodes():
                if not self.mergePattern.search(child.name()):
                    newBone = bone
                    newSlot = slot
                    newX = xOffset
                    newY = yOffset
                    # Found a bone
                    if self.bonePattern.search(child.name()):
                        newBone = self.bonePattern.sub('', child.name()).strip()
                        rect = child.bounds()
                        newX = rect.left() + rect.width() / 2 - xOffset
                        newY = (- rect.bottom() + rect.height() / 2) - yOffset
                        self.spineBones.append({
                            'name': newBone,
                            'parent': bone,
                            'x': newX,
                            'y': newY
                        })
                        newX = xOffset + newX
                        newY = yOffset + newY
                    # Found a slot
                    if self.slotPattern.search(child.name()):
                        newSlotName = self.slotPattern.sub('', child.name()).strip()
                        newSlot = {
                            'name': newSlotName,
                            'bone': bone,
                            'attachment': None,
                        }
                        self.spineSlots.append(newSlot)

                    ## Found a skin
                    if self.skinPattern.search(child.name()):
                        newSkin = self.skinPattern.sub('', child.name()).strip()

                    self._export(child, directory, newBone, newX, newY, newSlot)
                    continue

            name = self.mergePattern.sub('', child.name()).strip()
            layerFileName = '{0}/{1}.{2}'.format(directory, name, self.fileFormat)
            child.save(layerFileName, 96, 96)

            newSlot = slot

            if not newSlot:
                newSlot = {
                    'name': name,
                    'bone': bone,
                    'attachment': name,
                }
                self.spineSlots.append(newSlot)
            else:
                if not newSlot['attachment']:
                    newSlot['attachment'] = name

            rect = child.bounds()
            slotName = newSlot['name']
            if slotName not in self.spineDefaultSkin:
                self.spineDefaultSkin[slotName] = {}
            self.spineDefaultSkin[slotName][name] = {
                'x': rect.left() + rect.width() / 2 - xOffset,
                'y': (- rect.bottom() + rect.height() / 2) - yOffset,
                'rotation': 0,
                'width': rect.width(),
                'height': rect.height(),
            }


# And add the extension to Krita's list of extensions:
Krita.instance().addExtension(SpineExport(Krita.instance()))

# End of file
