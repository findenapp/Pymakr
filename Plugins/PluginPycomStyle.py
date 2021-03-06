import os
import sys

from PyQt5.QtCore import QObject, Qt
from PyQt5.QtGui import QFontDatabase, QFont, QColor
from PyQt5.Qsci import QsciScintilla
from Preferences.PreferencesLexer import PreferencesLexer
import Preferences

from PluginUpdate import calc_int_version
from PycomStyle.qdarkstyle import pyqt5_style_rc

import UI.Info
from PycomStyle import StyleHelper
from E5Gui.E5Application import e5App


# Start-Of-Header
name = "Pycom Style"
author = "Pycom"
autoactivate = True
deactivateable = False
version = "1.0.0"
className = "PluginPycomStyle"
packageName = "PluginPycomStyle"
shortDescription = "Set UI themes"
longDescription = "This plugin sets colors, fonts and control sizes and shapes"

pyqtApi = 2
python2Compatible = True

path = os.path.dirname(os.path.realpath(__file__))
sl = "/"
if "\Plugins" in path:
    sl = "\\"
pluginsPath = path[0:path.index(sl+'Plugins')+8] + sl+"PycomStyle"+sl

# data
styles = ['Dark','Light']
styleSheets = ['qdarkstyle/style.qss','qdarkstyle/style-light.qss']

class PluginPycomStyle(QObject):

    def __init__(self, ui):
        super(PluginPycomStyle, self).__init__(ui)
        self.__ui = ui
        self.__ui.preferencesChanged.connect(self.preferencesChanged)
        self.__path = os.path.dirname(os.path.realpath(__file__))
        self.__loadFont()

        # first time settings initialization
        if not Preferences.isConfigured() or \
           Preferences.Prefs.settings.value("General/IniVersion", "1.0.0.b1") == "1.0.0.b1" or \
           hasattr(ui, 'firstBoot'):
            ui.firstBoot = True
            self.__firstLoad()
        
        self.__storePreviousSettings()
        # detect wrong path of stylesheet and correct it

        self.__styleSheet = Preferences.getUI("StyleSheet")
        stylesheetUrls = []
        for sheet in styleSheets:
            stylesheetUrls.append(pluginsPath+sheet)
        if self.__styleSheet not in stylesheetUrls:
            for style in styleSheets:
                if style in self.__styleSheet:
                    self.__styleSheet = pluginsPath+style

    
    def activate(self):
        """
        Public method to activate this plugin.

        @return tuple of None and activation status (boolean)
        """
        return None, True

    def deactivate(self):
        """
        Public method to deactivate this plugin.
        """
        pass

    def preferencesChanged(self):
    
        if Preferences.getUI("StyleSheet") != self.__styleSheet:
            self.__storePreviousSettings()
            self.__loadQssColors()
            self.__loadPythonColors()
            self.__overrideStyleConfig()
            self.__refreshEditor()
        
        if self.__fontChanged():
            self.__storePreviousSettings()
            self.__loadQssColors()
            self.__loadPythonColors()
            self.__refreshEditor()
    

    def __refreshEditor(self):
        viewManager = e5App().getObject('ViewManager')
        openFiles = viewManager.getOpenFilenames()
        for fn in openFiles:
            editor = viewManager.getOpenEditor(fn)
            editor.setLanguage(fn,editor.getLanguage()) # get and set language to refresh lexer

    def __firstLoad(self):
        """
        Private method called if there are no settings.
        """
        Preferences.setUI("StyleSheet", \
            self.__path + "/PycomStyle/" + styleSheets[0])

        self.__ui.setStyle(Preferences.getUI("Style"), Preferences.getUI("StyleSheet"))
        self.__loadQssColors()
        self.__setupDefaultParameters()
        self.__loadPythonColors()

    def __storePreviousSettings(self):
        self.__styleSheet = Preferences.getUI("StyleSheet")
        self.__useMonospacedFont = Preferences.getEditor("UseMonospacedFont")
        self.__monospacedFont = Preferences.getEditorOtherFonts("MonospacedFont")
        self.__defaultFont = Preferences.getEditorOtherFonts("DefaultFont")

    def __fontChanged(self):
        return (Preferences.getEditor("UseMonospacedFont") != self.__useMonospacedFont or
                Preferences.getEditorOtherFonts("MonospacedFont") != self.__monospacedFont or
                Preferences.getEditorOtherFonts("DefaultFont") != self.__defaultFont)

    def __getFont(self):
        if Preferences.getEditor("UseMonospacedFont"):
            return Preferences.getEditorOtherFonts("MonospacedFont")
        else:
            return Preferences.getEditorOtherFonts("DefaultFont")

    def __loadFont(self):
        osFamily = sys.platform
        if osFamily == 'darwin':
            fontVariations = ["Thin", "ThinItalic"]
            self.__defaultFontSize = 14
        else:
            fontVariations = ["Light", "LightItalic"]
            self.__defaultFontSize = -1

        for variation in fontVariations:
            QFontDatabase.addApplicationFont(self.__path + \
              "/PycomStyle/Fonts/RobotoMono-" + variation + ".ttf")

    def __overrideStyleConfig(self):
         for key in self.editorColorsDefaults:
            Preferences.setEditorColour(key,self.editorColorsDefaults[key])
        
    def __applyMonokaiPython(self, lexerName, defaultFont=None):
        # defaultFont = QFont(fontName, self.__defaultFontSize, -1, False)
        if defaultFont == None:
            defaultFont = self.__getFont()
        
        lexer = PreferencesLexer(lexerName)

        for i in range(0, 15):
            lexer.setPaper(self.editorColorsDefaults['EditAreaBackground'], i)
            lexer.setFont(defaultFont, i)
            lexer.setColor(QColor(self.textColors[i]), i)

        # specific values now
        # comment
        defaultFont.setItalic(True)
        lexer.setFont(defaultFont, 1)
        defaultFont.setItalic(False)

        # class name
        defaultFont.setUnderline(True)
        lexer.setFont(defaultFont, 8)

        # Unclosed string
        lexer.setPaper(QColor("#f92672"), 13)
        lexer.setEolFill(True, 13)

        lexer.writeSettings(Preferences.Prefs.settings, "Scintilla")

    def __loadPythonColors(self):
        self.__applyMonokaiPython("C++")
        self.__applyMonokaiPython("Python2")
        self.__applyMonokaiPython("Python3")

    def __setupDefaultParameters(self):
        # defaultFont = QFont("Roboto Mono", self.__defaultFontSize, -1, False)
        defaultFont = self.__getFont()

        editorOtherFontsDefaults = {
            "MarginsFont": defaultFont,
            "DefaultFont": defaultFont,
            "MonospacedFont": defaultFont}

        shellDefaults = {
            "UseMonospacedFont": True,
            "MonospacedFont": defaultFont,
            "MarginsFont": defaultFont}

        editorDefaults = {
            "FoldingStyle": 7, # arrow tree
            "ShowWhitespace": True,
            "UseMonospacedFont": True,
            "OverrideEditAreaColours": True,
            "CustomSelectionColours": True,
            "EdgeMode": QsciScintilla.EdgeLine,
            "EdgeColumn": 80,
            "CaretLineVisible": True,
            "ColourizeSelText": True,
            "AutoCompletionEnabled": True,
            "AutoCompletionCaseSensitivity": False,
            "AutoCompletionReplaceWord": True,
            "AutoCompletionThreshold": 1,
            "AutoCompletionFillups": True,
            "AutoCompletionScintillaOnFail": True,
            "CallTipsEnabled": True,
            "CallTipsVisible": 0,
            "OnlineSyntaxCheckInterval": 0,
            "MiniContextMenu": True,
            "AnnotationsEnabled": False}

        for n, value in editorOtherFontsDefaults.iteritems():
            Preferences.setEditorOtherFonts(n, value)

        for n, value in shellDefaults.iteritems():
            Preferences.setShell(n, value)

        for n, value in editorDefaults.iteritems():
            Preferences.setEditor(n, value)

        for n, value in self.editorColorsDefaults.iteritems():
            Preferences.setEditorColour(n, value)

    def __loadQssColors(self):
        qssColors = StyleHelper.readQssColors()
        if qssColors:
            self.textColors = qssColors['colors']
            del qssColors['colors']
            self.editorColorsDefaults = qssColors
