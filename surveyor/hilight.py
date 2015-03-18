from PySide import QtCore, QtGui


class Highlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(Highlighter, self).__init__(parent)
        keywordFormat = QtGui.QTextCharFormat()
        keywordFormat.setForeground(QtGui.QColor("#f92672"))
        keywordPatterns = ["-\\s*['\"]?\\bname\\b['\"]? ?:",
                           "['\"]?\\border\\b['\"]? ?:",
                           "['\"]?\\bresponses\\b['\"]? ?:",
                           "['\"]?\\bversion\\b['\"]? ?:"]
        self.highlightingRules = [(QtCore.QRegExp(pattern),
                                  keywordFormat) for pattern
                                  in keywordPatterns]
        classFormat = QtGui.QTextCharFormat()
        classFormat.setFontWeight(QtGui.QFont.Bold)
        classFormat.setForeground(QtGui.QColor("#66d9ef"))
        self.highlightingRules.append(
                                      (QtCore.QRegExp("['\"]?\\b(questions|"
                                       "options)\\b['\"]? ?:"), classFormat))
        versionFormat = QtGui.QTextCharFormat()
        versionFormat.setForeground(QtGui.QColor("#e6db74"))
        self.highlightingRules.append(
                            (QtCore.QRegExp("['\"]?\\bonlyif\\b['\"]?"
                             " ?: ?\{['\"]?\\bquestion\\b['\"]? ?: ?[0-9].*,.*"
                                            "\\bequals\\b ?: ?[0-9].*\}"),
                             versionFormat))
        multiLineCommentFormat = QtGui.QTextCharFormat()
        multiLineCommentFormat.setForeground(QtGui.QColor("#a6e22e"))
        self.highlightingRules.append(
                                      (QtCore.QRegExp(
                                       "-.*['\"]?\\bname\\b"
                                       "['\"]? ?:.*"),
                                       multiLineCommentFormat))
        quotationFormat = QtGui.QTextCharFormat()
        quotationFormat.setForeground(QtGui.QColor("#f92672"))
        quotationFormat.setFontItalic(True)
        self.highlightingRules.append(
                            (QtCore.QRegExp(
                             "\\s+['\"]?\\b(vendor|"
                             "title|id\\d|returns|save_as|cpt)\\b['\"]? ?:.*"),
                                quotationFormat))
        intFormat = QtGui.QTextCharFormat()
        intFormat.setFontWeight(QtGui.QFont.Bold)
        intFormat.setForeground(QtGui.QColor("#ae81ff"))
        self.highlightingRules.append(
                                (QtCore.QRegExp(
                                 "\\b(\\d+|['\"]?[A-Z]['\"]?)\\s*$"),
                                 intFormat))
        functionFormat = QtGui.QTextCharFormat()
        functionFormat.setFontItalic(True)
        functionFormat.setForeground(QtGui.QColor("#f8f8f2"))
        self.highlightingRules.append(
                                (QtCore.QRegExp(
                                 "\\s{4,}['\"]?[A-Za-z0-9_]+['\"]? ?: ?\\d"),
                                    functionFormat))
        self.commentStartExpression = QtCore.QRegExp("/\\*")
        self.commentEndExpression = QtCore.QRegExp("\\*/")

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = QtCore.QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)
        self.setCurrentBlockState(0)
        startIndex = 0
        if self.previousBlockState() != 1:
            startIndex = self.commentStartExpression.indexIn(text)
        while startIndex >= 0:
            endIndex = self.commentEndExpression.indexIn(text, startIndex)
            if endIndex == -1:
                self.setCurrentBlockState(1)
                commentLength = len(text) - startIndex
            else:
                commentLength = (endIndex - startIndex +
                                 self.commentEndExpression.matchedLength())
            self.setFormat(startIndex, commentLength,
                           self.multiLineCommentFormat)
            startIndex = self.commentStartExpression.indexIn(
                                                             text,
                                                             (startIndex +
                                                              commentLength))
