# This script is licensed CC 0 1.0, so that you can learn from it.

# ------ CC 0 1.0 ---------------

# The person who associated a work with this deed has dedicated the
# work to the public domain by waiving all of his or her rights to the
# work worldwide under copyright law, including all related and
# neighboring rights, to the extent allowed by law.

# You can copy, modify, distribute and perform the work, even for
# commercial purposes, all without asking permission.

# https://creativecommons.org/publicdomain/zero/1.0/legalcode

from . import documenttoolsdialog
from . import SpineExport

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QFormLayout, QListWidget, QAbstractItemView, QLineEdit, QFileDialog,
                             QDialogButtonBox, QVBoxLayout, QFrame, QTabWidget,
                             QPushButton, QAbstractScrollArea, QMessageBox, QHBoxLayout)
import os
import krita
import importlib


class UIDocumentTools(object):

    def __init__(self):
        self.mainDialog = documenttoolsdialog.DocumentToolsDialog()
        self.spineExport = SpineExport.SpineExport()
        self.mainLayout = QVBoxLayout(self.mainDialog)
        self.formLayout = QFormLayout()
        self.documentLayout = QVBoxLayout()
        self.refreshButton = QPushButton(i18n("Refresh"))
        self.widgetDocuments = QListWidget()
        self.tabTools = QTabWidget()
        self.buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        # Output directory
        self.directorySelectorLayout = QHBoxLayout()
        self.directoryTextField = QLineEdit()
        self.directoryDialogButton = QPushButton(i18n("..."))

        self.kritaInstance = krita.Krita.instance()
        self.documentsList = []

        self.refreshButton.clicked.connect(self.refreshButtonClicked)
        self.buttonBox.accepted.connect(self.confirmButton)
        self.buttonBox.rejected.connect(self.mainDialog.close)
        self.directoryDialogButton.clicked.connect(self._selectDir)

        self.mainDialog.setWindowModality(Qt.NonModal)
        self.widgetDocuments.setSelectionMode(QAbstractItemView.MultiSelection)
        self.widgetDocuments.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

    def initialize(self):
        self.loadDocuments()
        self.loadTools()

        self.documentLayout.addWidget(self.widgetDocuments)
        self.documentLayout.addWidget(self.refreshButton)
        self.directorySelectorLayout.addWidget( self.directoryTextField)
        self.directorySelectorLayout.addWidget(self.directoryDialogButton)

        self.formLayout.addRow(i18n("Documents:"), self.documentLayout)
        self.formLayout.addRow(i18n("Output Directory:"), self.directorySelectorLayout)
        self.formLayout.addRow(self.tabTools)

        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.mainLayout.addLayout(self.formLayout)
        self.mainLayout.addWidget(self.line)
        self.mainLayout.addWidget(self.buttonBox)

        self.mainDialog.resize(500, 300)
        self.mainDialog.setWindowTitle(i18n("Document Tools"))
        self.mainDialog.setSizeGripEnabled(True)
        self.mainDialog.show()
        self.mainDialog.activateWindow()

    def loadTools(self):
        modulePath = 'KritaToSpine.tools'
        toolsModule = importlib.import_module(modulePath)
        modules = []

        for classPath in toolsModule.ToolClasses:
            _module = classPath[:classPath.rfind(".")]
            _klass = classPath[classPath.rfind(".") + 1:]
            modules.append(dict(module='{0}.{1}'.format(modulePath, _module),
                                klass=_klass))

        for module in modules:
            m = importlib.import_module(module['module'])
            toolClass = getattr(m, module['klass'])
            obj = toolClass(self.mainDialog)
            self.tabTools.addTab(obj, obj.objectName())

    def loadDocuments(self):
        self.widgetDocuments.clear()

        self.documentsList = [
            document for document in self.kritaInstance.documents()
            if document.fileName()
        ]

        for document in self.documentsList:
            self.widgetDocuments.addItem(document.fileName())

    def refreshButtonClicked(self):
        self.loadDocuments()

    def confirmButton(self):
        selectedPaths = [
            item.text() for item in self.widgetDocuments.selectedItems()]
        selectedDocuments = [
            document for document in self.documentsList
            for path in selectedPaths if path == document.fileName()]

        self.msgBox = QMessageBox(self.mainDialog)

        if selectedDocuments:
            # TODO have this loop through the tabs and apply all of the items
            widget = self.tabTools.currentWidget()
            for document in selectedDocuments:
                cloneDoc = document.clone()
                widget.adjust(cloneDoc)
                # Save the json from the clone
                self.spineExport.exportDocument(cloneDoc)
                # Clone no longer needed
                cloneDoc.close()

            self.msgBox.setText(i18n("The selected documents have been modified."))
        else:
            self.msgBox.setText(i18n("Select at least one document."))
        self.msgBox.exec_()

    def _selectDir(self):
        directory = QFileDialog.getExistingDirectory(self.mainDialog, i18n("Select a Folder"), os.path.expanduser("~"), QFileDialog.ShowDirsOnly)
        self.directoryTextField.setText(directory)
