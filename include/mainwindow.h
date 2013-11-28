/****************************************************************************
**
** Copyright (C) 2004-2006 Trolltech ASA. All rights reserved.
**
** This file is part of the example classes of the Qt Toolkit.
**
** Licensees holding a valid Qt License Agreement may use this file in
** accordance with the rights, responsibilities and obligations
** contained therein.  Please consult your licensing agreement or
** contact sales@trolltech.com if any conditions of this licensing
** agreement are not clear to you.
**
** Further information about Qt licensing is available at:
** http://www.trolltech.com/products/qt/licensing.html or by
** contacting info@trolltech.com.
**
** This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
** WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
**
****************************************************************************/

#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QPushButton>
#include <QComboBox>

#include <string>

class QAction;
class QMenu;
class QProcess;
class QTextEdit;
class QString;

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    MainWindow(QApplication &ref);

protected:
    void closeEvent(QCloseEvent *event);

private slots:
    void onExitCleanup();
    void about();
    void handleSubmitButton();


private:
    void createActions();
    std::string executeCommand(const char* command);
    std::string removeQuotationMarks(std::string data);
    bool emailValid(std::string email);


    QTextEdit *FeedbackTextPane;

    QStringList categories;
    QComboBox *FeedbackCategoryDropdown;

    QPushButton *SubmitButton;

    QAction *aboutAct;
    QAction *aboutQtAct;

};

#endif
