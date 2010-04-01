"""
<name>PIPA Database</name>
<description>Access data from PIPA RNA-Seq database.</description>
<icon>icons/PIPA.png</icon>
<priority>30</priority>
"""

from OWWidget import *
import obiDicty
import OWGUI
import orngEnviron
import sys, os
from collections import defaultdict



#def pyqtConfigure(object, **kwargs):
#    if hasattr(object, "pyqtConfigure"):
#        object.pyqtConfigure(**kwargs)
#    else:
#        for name, value in kwargs.items():
#            if object.metaObject().indexOfProperty(name) != -1:
#                object.setProperty(name, value)
#            elif object.metaObject().indexOfSignal(name) != -1:
#                object.connect(object.

def tfloat(s):
    try:
        return float(s)
    except:
        return None

class MyTreeWidgetItem(QTreeWidgetItem):

    def __init__(self, parent, *args):
        QTreeWidgetItem.__init__(self, parent, *args)
        self.par = parent

    def __contains__(self, text):
        return any(text.upper() in str(self.text(i)).upper() for i in range(self.columnCount()))    
 
    def __lt__(self, o1):
        col = self.par.sortColumn()
        if col in [6,7,8]: #WARNING: hardcoded column numbers
            return tfloat(self.text(col)) < tfloat(o1.text(col))
        else:
            return QTreeWidgetItem.__lt__(self, o1)


#set buffer file
bufferpath = os.path.join(orngEnviron.directoryNames["bufferDir"], "pipa")
try:
    os.makedirs(bufferpath)
except:
    pass
bufferfile = os.path.join(bufferpath, "database.sq3")

CACHED_COLOR = Qt.darkGreen

class ListItemDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index):
        size = QStyledItemDelegate.sizeHint(self, option, index)
        size = QSize(size.width(), size.height() + 4)
        return size

    def createEditor(self, parent, option, index):
        return QLineEdit(parent)
    
    def setEditorData(self, editor, index):
        editor.setText(index.data(Qt.DisplayRole).toString())
        
    def setModelData(self, editor, model, index):
#        print index
        model.setData(index, QVariant(editor.text()), Qt.EditRole)

class SelectionSetsWidget(QFrame):
    """ Widget for managing multiple stored item selections 
    """
    def __init__(self, parent):
        QFrame.__init__(self, parent)
        self.setContentsMargins(0, 0, 0, 0)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
#        self._titleLabel = QLabel(self)
#        self._titleLabel
#        layout.addWidget(self._titleLabel)
        self._setNameLineEdit = QLineEdit(self)
        layout.addWidget(self._setNameLineEdit)
        
        self._setListView = QListView(self)
        self._listModel = QStandardItemModel(self)
        self._proxyModel = QSortFilterProxyModel(self)
        self._proxyModel.setSourceModel(self._listModel)
        
        self._setListView.setModel(self._proxyModel)
        self._setListView.setItemDelegate(ListItemDelegate(self))
        
        self.connect(self._setNameLineEdit, SIGNAL("textChanged(QString)"), self._proxyModel.setFilterFixedString)
        
        self._completer = QCompleter(self._listModel, self)
        
        self._setNameLineEdit.setCompleter(self._completer)
        
        self.connect(self._listModel, SIGNAL("itemChanged(QStandardItem *)"), self._onSetNameChange)
        layout.addWidget(self._setListView)
        buttonLayout = QHBoxLayout()
        
        self._addAction = QAction("+", self)
        self._updateAction = QAction("Update", self)
        self._removeAction = QAction("-", self)
        
        self._addToolButton = QToolButton(self)
        self._updateToolButton = QToolButton(self)
        self._removeToolButton = QToolButton(self)
        self._updateToolButton.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        
        self._addToolButton.setDefaultAction(self._addAction)
        self._updateToolButton.setDefaultAction(self._updateAction)
        self._removeToolButton.setDefaultAction(self._removeAction)
         
        buttonLayout.addWidget(self._addToolButton)
        buttonLayout.addWidget(self._updateToolButton)
        buttonLayout.addWidget(self._removeToolButton)
        
        layout.addLayout(buttonLayout)
        self.setLayout(layout)
        
        self.connect(self._addAction, SIGNAL("triggered()"), self.addCurrentSelection)
        self.connect(self._updateAction, SIGNAL("triggered()"), self.updateSelectedSelection)
        self.connect(self._removeAction, SIGNAL("triggered()"), self.removeSelectedSelection)
        
        self.connect(self._setListView.selectionModel(), SIGNAL("selectionChanged(QItemSelection, QItemSelection)"), self._onListViewSelectionChanged)
        self.selectionModel = None
        self._selections = []
        
    def sizeHint(self):
        size = QFrame.sizeHint(self)
        return QSize(size.width(), 200)
        
    def _onSelectionChanged(self, selected, deselected):
        self.setSelectionModified(True)
        
    def _onListViewSelectionChanged(self, selected, deselected):
        try:
            index= self._setListView.selectedIndexes()[0]
        except IndexError:
            return 
        self.commitSelection(self._proxyModel.mapToSource(index).row())

    def _onSetNameChange(self, item):
        self.selections[item.row()].name = str(item.text())
                
    def _setButtonStates(self, val):
        self._updateToolButton.setEnabled(val)
        
    def setSelectionModel(self, selectionModel):
        if self.selectionModel:
            self.disconnect(self.selectionModel, SIGNAL("selectionChanged(QItemSelection, QItemSelection)", self._onSelectionChanged))
        self.selectionModel = selectionModel
        self.connect(self.selectionModel, SIGNAL("selectionChanged(QItemSelection, QItemSelection)"), self._onSelectionChanged)
        
    def addCurrentSelection(self):
        item = self.addSelection(SelectionByKey(self.selectionModel.selection(), name="New selection", key=(0,1,2,3, 8)))
        index = self._proxyModel.mapFromSource(item.index())
        self._setListView.setCurrentIndex(index)
        self._setListView.edit(index)
        self.setSelectionModified(False)
    
    def removeSelectedSelection(self):
        i = self._proxyModel.mapToSource(self._setListView.currentIndex()).row()
        self._listModel.takeRow(i)
        del self.selections[i]
    
    def updateCurentSelection(self):
        i = self._proxyModel.mapToSource(self._setListView.selectedIndex()).row()
        self.selections[i].setSelection(self.selectionModel.selection())
        self.setSelectionModified(False)
        
    def addSelection(self, selection, name=""):
        self._selections.append(selection)
        item = QStandardItem(selection.name)
        self._listModel.appendRow(item)
        self.setSelectionModified(False)
        return item
        
    def updateSelectedSelection(self):
        i = self._proxyModel.mapToSource(self._setListView.currentIndex()).row()
        self.selections[i].setSelection(self.selectionModel.selection())
        self.setSelectionModified(False)
        
    def setSelectionModified(self, val):
        self._selectionModified = val
        self._setButtonStates(val)
        self.emit(SIGNAL("selectionModified(bool)"), bool(val))
        
    def commitSelection(self, index):
        selection = self.selections[index]
        selection.select(self.selectionModel)
        
    def setSelections(self, selections):
        self._listModel.clear()
#        print selections
        for selection in selections:
            self.addSelection(selection)
            
    def selections(self):
        return self._selections
    
    selections = property(selections, setSelections)
    
class SelectionByKey(object):
    """ An object stores item selection by unique key values 
    (works only for row selections in list and table models)
    Example::
        ## Save selection by unique tuple pairs (DisplayRole of column 1 and 2)
        selection = SelectionsByKey(itemView.selectionModel().selection(), key = (1,2))
        ...
        ## restore selection (Possibly omitting rows not present in the model)  
        selection.select(itemView.selectionModel())
    """
    
    def __init__(self, itemSelection, name="", key=(0,)):
        self._key = key
        self.name = name
        self._selected_keys = []
        if itemSelection:
            self.setSelection(itemSelection)
        
    def _row_key(self, model, row):
        val = lambda row, col: str(model.data(model.index(row, col), Qt.DisplayRole).toString())
        return tuple(val(row, col) for col in self._key)
    
    def setSelection(self, itemSelection):
        self._selected_keys = [self._row_key(ind.model(), ind.row()) for ind in itemSelection.indexes() if ind.column() == 0]
    
    def select(self, selectionModel):
        model = selectionModel.model()
        selected = []
        selectionModel.clear()
        for i in range(model.rowCount()):
            if self._row_key(model, i) in self._selected_keys:
                selectionModel.select(model.index(i, 0), QItemSelectionModel.Select | QItemSelectionModel.Rows)
                
class SortedListWidget(QWidget):
    class _MyItemDelegate(QStyledItemDelegate):
        def __init__(self, sortingModel, parent):
            QStyledItemDelegate.__init__(self, parent)
            self.sortingModel = sortingModel
            
        def sizeHint(self, option, index):
            size = QStyledItemDelegate.sizeHint(self, option, index)
            return QSize(size.width(), size.height() + 4)
            
        def createEditor(self, parent, option, index):
            cb = QComboBox(parent)
            cb.setModel(self.sortingModel)
            cb.showPopup()
            return cb
        
        def setEditorData(self, editor, index):
            pass # TODO: sensible default 
        
        def setModelData(self, editor, model, index):
            text = editor.currentText()
            model.setData(index, QVariant(text))
    
    def __init__(self, *args):
        QWidget.__init__(self, *args)
        self.setContentsMargins(0, 0, 0, 0)
        gridLayout = QGridLayout()
        gridLayout.setContentsMargins(0, 0, 0, 0)
        gridLayout.setSpacing(1)
        self._listView = QListView(self)
        self._listView.setModel(QStandardItemModel(self))
#        self._listView.setDragEnabled(True)
        self._listView.setDropIndicatorShown(True)
        self._listView.viewport().setAcceptDrops(True)
        self._listView.setDragDropMode(QAbstractItemView.InternalMove)
        self._listView.setMinimumHeight(100)
        
        gridLayout.addWidget(self._listView, 0, 0, 2, 2)
        
        vButtonLayout = QVBoxLayout()
        
        self._upAction = QAction(QIcon(os.path.join(orngEnviron.widgetDir, "icons/Dlg_up3.png")), "Up", self)
        
        self._upButton = QToolButton(self)
        self._upButton.setDefaultAction(self._upAction)
        self._upButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.MinimumExpanding)

        self._downAction = QAction(QIcon(os.path.join(orngEnviron.widgetDir, "icons/Dlg_down3.png")), "Down", self)
        self._downButton = QToolButton(self)
        self._downButton.setDefaultAction(self._downAction)
        self._downButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.MinimumExpanding)
        
        vButtonLayout.addWidget(self._upButton)
        vButtonLayout.addWidget(self._downButton)
        
        gridLayout.addLayout(vButtonLayout, 0, 2, 2, 1)
        
        hButtonLayout = QHBoxLayout()
        
        self._addAction = QAction("+", self)
        self._addButton = QToolButton(self)
        self._addButton.setDefaultAction(self._addAction)
        
        self._removeAction = QAction("-", self)
        self._removeButton = QToolButton(self)
        self._removeButton.setDefaultAction(self._removeAction)
        hButtonLayout.addWidget(self._addButton)
        hButtonLayout.addWidget(self._removeButton)
        hButtonLayout.addStretch(10)
        gridLayout.addLayout(hButtonLayout, 2, 0, 1, 2)
        
        self.setLayout(gridLayout)
        
        self.connect(self._addAction, SIGNAL("triggered()"), self._onAddAction)
        self.connect(self._removeAction, SIGNAL("triggered()"), self._onRemoveAction)
        self.connect(self._upAction, SIGNAL("triggered()"), self._onUpAction)
        self.connect(self._downAction, SIGNAL("triggered()"), self._onDownAction)
        
    def sizeHint(self):
        size = QWidget.sizeHint(self)
        return QSize(size.width(), 100)
        
    def _onAddAction(self):
        item = QStandardItem("")
        self._listView.model().appendRow(item)
        self._listView.setCurrentIndex(item.index())
        self._listView.edit(item.index()) 
        
    
    def _onRemoveAction(self):
        current = self._listView.currentIndex()
        self._listView.model().takeRow(current.row())
    
    def _onUpAction(self):
        row = self._listView.currentIndex().row()
        model = self._listView.model()
        if row > 0:
            items = model.takeRow(row)
            model.insertRow(row - 1, items)
            self._listView.setCurrentIndex(model.index(row - 1, 0))
    
    def _onDownAction(self):
        row = self._listView.currentIndex().row()
        model = self._listView.model()
        print row, model.rowCount()
        if row < model.rowCount() and row >= 0:
            items = model.takeRow(row)
            if row == model.rowCount():
                model.appendRow(items)
            else:
                model.insertRow(row + 1, items)
            self._listView.setCurrentIndex(model.index(row + 1, 0))
    
    def setModel(self, model):
        """ Set a model to select items from
        """
        self._model  = model
        self._listView.setItemDelegate(self._MyItemDelegate(self._model, self))
        
    def addItem(self, *args):
        """ Add a new entry in the list 
        """
        item = QStandardItem(*args)
        self._listView.model().appendRow(item)
        
    def setItems(self, items):
        self._listView.model().clear()
        for item in items:
            self.addItem(item)
         
    def items(self):
        order = []
        for row in range(self._listView.model().rowCount()):
             order.append(str(self._listView.model().item(row ,0).text()))
        return order
    
    sortingOrder = property(items, setItems)
        
    
class OWPIPA(OWWidget):
    settingsList = [ "platform", "selectedExperiments", "server", "buffertime", "excludeconstant", "username", "password","joinreplicates",
                     "selectionSetsWidget.selections", "columnsSortingWidget.sortingOrder", "currentSelection"]
    def __init__(self, parent=None, signalManager=None, name="PIPA database"):
        OWWidget.__init__(self, parent, signalManager, name)
        self.outputs = [("Example table", ExampleTable)]

        self.platform = None
        self.username = ""
        self.password = ""

        self.selectedExperiments = []
        self.buffer = obiDicty.BufferSQLite(bufferfile)

        self.searchString = ""
        self.excludeconstant = False
        self.joinreplicates = False
        self.currentSelection = None

        self.chips = []
        self.annots = []
        

        self.controlArea.setMaximumWidth(250)
        self.controlArea.setMinimumWidth(250)

        OWGUI.button(self.controlArea, self, "Reload", callback=self.Reload)
        OWGUI.button(self.controlArea, self, "Clear cache", callback=self.clear_cache)
        
        b = OWGUI.widgetBox(self.controlArea, "Experiment Sets")
        self.selectionSetsWidget = SelectionSetsWidget(self)
        self.selectionSetsWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
#        self.controlArea.layout().addWidget(self.selectionSetsWidget)
        b.layout().addWidget(self.selectionSetsWidget)
        
        b = OWGUI.widgetBox(self.controlArea, "Sort output columns")
        self.columnsSortingWidget = SortedListWidget(self)
        self.columnsSortingWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
#        self.controlArea.layout().addWidget(self.columnsSortingWidget)
        b.layout().addWidget(self.columnsSortingWidget)
        self.columnsSortingWidget.setModel(QStringListModel(["Strain", "Genotype", "Timepoint", "Growth", "Species", "Id", "Name"]))
        self.columnsSortingWidget.sortingOrder = ["Strain", "Genotype", "Timepoint"]
        OWGUI.rubber(self.controlArea)

        OWGUI.checkBox(self.controlArea, self, "excludeconstant", "Exclude labels with constant values" )
        OWGUI.checkBox(self.controlArea, self, "joinreplicates", "Average replicates (use median)" )

        OWGUI.button(self.controlArea, self, "&Commit", callback=self.Commit)

        OWGUI.rubber(self.controlArea)
        OWGUI.rubber(self.controlArea)
        OWGUI.rubber(self.controlArea)
        OWGUI.rubber(self.controlArea)

        box  = OWGUI.widgetBox(self.controlArea, "Authentication")

        OWGUI.lineEdit(box, self, "username", "Username:", labelWidth=100, orientation='horizontal', callback=self.AuthChanged)
        self.passf = OWGUI.lineEdit(box, self, "password", "Password:", labelWidth=100, orientation='horizontal', callback=self.AuthChanged)
        self.passf.setEchoMode(QLineEdit.Password)

        OWGUI.lineEdit(self.mainArea, self, "searchString", "Search", callbackOnType=True, callback=self.SearchUpdate)
        self.experimentsWidget = QTreeWidget()
        self.experimentsWidget.setHeaderLabels(["", "Species", "Strain", "Genotype", "Treatment", "Growth", "Timepoint", "Replicate", "ID"])
        self.experimentsWidget.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.experimentsWidget.setRootIsDecorated(False)
        self.experimentsWidget.setSortingEnabled(True)
        contextEventFilter = OWGUI.VisibleHeaderSectionContextEventFilter(self.experimentsWidget)
        self.experimentsWidget.header().installEventFilter(contextEventFilter)
        self.experimentsWidget.setItemDelegateForColumn(0, OWGUI.IndicatorItemDelegate(self, role=Qt.DisplayRole))
        self.experimentsWidget.setAlternatingRowColors(True)
        
        self.connect(self.experimentsWidget.selectionModel(),
                     SIGNAL("selectionChanged(QItemSelection, QItemSelection)"),
                     self.onSelectionChanged)

        self.selectionSetsWidget.setSelectionModel(self.experimentsWidget.selectionModel())

        self.mainArea.layout().addWidget(self.experimentsWidget)

        self.loadSettings()
        
        self.dbc = None

        self.AuthSet()

        QTimer.singleShot(100, self.UpdateExperiments)

        self.resize(800, 600)        

    def __updateSelectionList(self, oldList, oldSelection, newList):
        oldList = [oldList[i] for i in oldSelection]
        return [ i for i, new in enumerate(newList) if new in oldList]
    
    def AuthSet(self):
        if len(self.username):
            self.passf.setDisabled(False)
        else:
            self.passf.setDisabled(True)

    def AuthChanged(self):
        self.AuthSet()
        self.ConnectAndUpdate()

    def ConnectAndUpdate(self):
        self.Connect()
        self.UpdateExperiments(reload=True)

    def Connect(self):

        self.error(1)
        self.warning(1)

        #obiDicty.verbose = 1
        def en(x):
            return x if len(x) else None

        self.dbc = obiDicty.PIPA(buffer=self.buffer, username=en(self.username), password=self.password)

        #check password
        if en(self.username) != None:
            try:
                self.dbc.list(reload=True)
            except obiDicty.AuthenticationError:
                self.error(1, "Wrong username or password")
                self.dbc = None
            except Exception, ex:
                try: #mable cached?
                    chips = self.dbc.list()
                    self.warning(1, "Can not access database - using cached data.")
                except Exception,ex:
                    self.dbc = None
                    self.error(1, "Can not access database.")

    def Reload(self):
        #self.buffer.clear()
        self.UpdateExperiments(reload=True)

    def clear_cache(self):
        self.buffer.clear()
        self.Reload()

    def UpdateExperiments(self, reload=False):
        self.chipsl = []
        self.experimentsWidget.clear()
        self.items = []

        self.progressBarInit()

        if not self.dbc:
            self.Connect()
 
        #obiDicty.verbose = 1

        chips, annots = [], []
        
        sucind = False #success indicator for database index

        try:
            chips = self.dbc.list(reload=reload)
            annots = self.dbc.annotations(chips, reload=reload)
            sucind = True
        except Exception, ex:
            try:
                chips = self.dbc.list()
                annots = self.dbc.annotations(chips)
                self.warning(0, "Can not access database - using cached data.")
                sucind = True
            except Exception,ex:
                self.error(0, "Can not access database.")

        if sucind:
            self.warning(0)
            self.error(0)

        self.chips = list(chips)
        self.annots = list(annots)

        elements = []
        pos = 0

        for chip,annot in zip(self.chips, self.annots):
            pos += 1
            d = defaultdict(lambda: "?", annot)
            elements.append(["", d["species"], d["strain"], d["genotype"], d["treatment"], d["growth"], d["tp"], d["replicate"], chip])
#            self.progressBarSet((100.0 * pos) / len(chips))
            
            el = elements[-1]
            ci = MyTreeWidgetItem(self.experimentsWidget, el)

            self.items.append(ci)

        for i in range(7):
            self.experimentsWidget.resizeColumnToContents(i)

        adic = dict(zip(self.chips, self.annots))
        #which is the ok buffer version
        self.wantbufver = lambda x,ad=adic: defaultdict(lambda: "?", ad[x])["map_stop1"]

        self.UpdateCached()

        self.progressBarFinished()
        
        if self.currentSelection:
            self.currentSelection.select(self.experimentsWidget.selectionModel())

    def UpdateCached(self):
        if self.wantbufver and self.dbc:
            fn = self.dbc.chips_keynaming()
            for item in self.items:
                c = str(item.text(8))
                item.setData(0, Qt.DisplayRole, QVariant(" " if self.dbc.inBuffer(fn(c)) == self.wantbufver(c) else ""))
#                color = Qt.black
#                if self.dbc.inBuffer(fn(c)) == self.wantbufver(c):
#                    color = CACHED_COLOR
#                brush = QBrush(color)
#                for i in range(item.columnCount()):
#                    item.setForeground(i, brush)

    def SearchUpdate(self, string=""):
        for item in self.items:
            item.setHidden(not all(s in item for s in self.searchString.split()))

    def Commit(self):
        if not self.dbc:
            self.Connect()
        allTables = []

        import time
        start = time.time()

        pb = OWGUI.ProgressBar(self, iterations=1000)

        table = None

        ids = []
        for item in self.experimentsWidget.selectedItems():
            ids += [ str(item.text(8)) ]

        table = self.dbc.get_data(ids=ids, callback=pb.advance, exclude_constant_labels=self.excludeconstant, bufver=self.wantbufver)

        if self.joinreplicates:
            table = obiDicty.join_replicates(table, ignorenames=["id", "replicate", "name", "map_stop1"], namefn=None, avg=obiDicty.median)

        end = int(time.time()-start)
        
        pb.finish()

        # Sort attributes
        sortOrder = self.columnsSortingWidget.sortingOrder
#        print sortOrder
        keys = {"Strain": "strain", "Genotype": "genotype", "Timepoint": "map_stop1", "Growth": "growth",
                "Species": "species", "Id":"id", "Name": "name"}
        attributes = sorted(table.domain.attributes, key=lambda attr: tuple([attr.attributes.get(keys[name], "") for name in sortOrder]))
        domain = orange.Domain(attributes, table.domain.classVar)
        domain.addmetas(table.domain.getmetas())
        table = orange.ExampleTable(domain, table)
        
        from orngDataCaching import data_hints
        data_hints.set_hint(table, "taxid", "352472") 
        data_hints.set_hint(table, "genesinrows", False)
        
        self.send("Example table", table)

        self.UpdateCached()

    def onSelectionChanged(self, selected, deselected):
        self.currentSelection = SelectionByKey(self.experimentsWidget.selectionModel().selection(),
                                               key=(0,1,2,3, 8))
        
if __name__ == "__main__":
    app  = QApplication(sys.argv)
##    from pywin.debugger import set_trace
##    set_trace()
    w = OWPIPA()
    w.show()
    app.exec_()
    w.saveSettings()
            
        