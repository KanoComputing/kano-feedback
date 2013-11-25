CONFIG       += release

greaterThan(QT_MAJOR_VERSION, 4) {
    QT += widgets
}

HEADERS       = include/mainwindow.h
SOURCES       = cpp/main.cpp \
                cpp/mainwindow.cpp
RESOURCES     = kano_feedback.qrc
