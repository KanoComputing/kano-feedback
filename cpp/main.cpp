/****************************************************************************
# main.cpp
#
# Copyright (C) 2013 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU General Public License v2
#
# A tool for sharing feedback on Kanux
#
****************************************************************************/

#include <QApplication>

#include "include/mainwindow.h"
#include <signal.h>
#include <stdio.h>
int main(int argc, char *argv[])
{
    Q_INIT_RESOURCE(kano_feedback);

    QApplication app(argc, argv);
    MainWindow mainWin(app);
    mainWin.show();
    return app.exec();
}
