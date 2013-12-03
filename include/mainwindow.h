/****************************************************************************
# main.cpp
#
# Copyright (C) 2013 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU General Public License v2
#
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
    void onExit();
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
