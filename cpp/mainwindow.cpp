/****************************************************************************
**
** Copyright (c) 2013 Samuel Aaron
**
** Permission is hereby granted, free of charge, to any person obtaining a copy
** of this software and associated documentation files (the "Software"), to deal
** in the Software without restriction, including without limitation the rights
** to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
** copies of the Software, and to permit persons to whom the Software is
** furnished to do so, subject to the following conditions:
**
** The above copyright notice and this permission notice shall be included in
** all copies or substantial portions of the Software.
**
** THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
** IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
** FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
** AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
** LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
** OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
** THE SOFTWARE.
**
****************************************************************************/

#include <QAction>
#include <QApplication>
#include <QCloseEvent>
#include <QMessageBox>
#include <QTextEdit>
#include <QFont>
#include <QString>
#include <QLabel>
#include <QGridLayout>
#include <QPushButton>
#include <QComboBox>
#include <QImage>

#include "include/mainwindow.h"

#define WIDTH     500

/******************* Styling *******************/
/*                                             */
/* TODO: Move away from using the preprocessor */
/*                                             */
/***********************************************/

/* General App Style */
#define APP_STYLING  "\
background-color: #d1d2d4"

/* The label describing the output pane */
#define LABEL_STYLING  " \
QLabel { \
    background-color: #e7e7e8; \
    color: #636466; \
    margin-top: 2px; \
    margin-bottom: 0; \
    padding: 8px; \
    font-family: 'Bariol'; \
    font-size: 18px; \
    color: #636466; \
}"

/* The pane showing the output */
#define FEEDBACK_TEXT_PANE_STYLING  " \
QTextEdit { \
    background-color: #ffffff; \
    margin: 0; \
    font-family: 'Bariol'; \
    font-size: 30px; \
}"

#define FEEDBACK_CATEGORY_PANE_STYLING  " \
QComboBox { \
    background-color: #ffffff; \
    margin: 0; \
    font-family: 'Bariol'; \
    font-size: 18px; \
    color: #636466; \
}"

#define SUBMIT_BUTTON_STYLING  " \
QPushButton { \
    background-color: #5cbf48; \
    margin: 0; \
    font-family: 'Bariol'; \
    font-size: 18px; \
    color: #ffffff; \
}"


/***** End *****/
/*      of     */
/*** styling ***/


/***********************************************************/
/*********************** Constructor ***********************/
/***********************************************************/

MainWindow::MainWindow(QApplication &app)
{
  /* Logo */
  QLabel * logoImage = new QLabel();
  logoImage->setPixmap( QPixmap( ":resources/logo.png" ) );
  logoImage->show();

  /* Feedback input */
  QLabel * FeedbackTextLabel = new QLabel(this);
  FeedbackTextLabel->setFixedWidth(WIDTH);
  FeedbackTextLabel->setText(tr("Help us improve your experience. Give us your thoughts"));
  FeedbackTextLabel->setStyleSheet(LABEL_STYLING);

  FeedbackTextPane = new QTextEdit;
  FeedbackTextPane->setFixedWidth(WIDTH);
  FeedbackTextPane->setStyleSheet(FEEDBACK_TEXT_PANE_STYLING);
  FeedbackTextPane->setReadOnly(false);

  /* Feedback category */
  QLabel * FeedbackCategoryLabel = new QLabel(this);
  FeedbackCategoryLabel->setFixedWidth(WIDTH / 2);
  FeedbackCategoryLabel->setText(tr("What category is this?"));
  FeedbackCategoryLabel->setStyleSheet(LABEL_STYLING);

  categories << "Comment" << "Bug" << "Suggestions";

  FeedbackCategoryDropdown = new QComboBox;
  FeedbackCategoryDropdown->setFixedWidth(WIDTH / 2);
  FeedbackCategoryDropdown->setStyleSheet(FEEDBACK_CATEGORY_PANE_STYLING);
  FeedbackCategoryDropdown->addItems(categories);

  QGridLayout * feedbackCategoryLayout = new QGridLayout;
  feedbackCategoryLayout->addWidget(FeedbackCategoryLabel, 0, 0);
  feedbackCategoryLayout->addWidget(FeedbackCategoryDropdown, 0, 1);

  /* Submit button */
  SubmitButton = new QPushButton("Send to us", this);
  SubmitButton->setStyleSheet(SUBMIT_BUTTON_STYLING);

  // Connect button signal to appropriate slot
  connect(SubmitButton, SIGNAL(released()), this, SLOT(handleSubmitButton()));

/* Main Content Layout */
  QGridLayout * mainContentLayout = new QGridLayout;
  mainContentLayout->addWidget(logoImage, 0, 0);
  mainContentLayout->addWidget(FeedbackTextLabel, 1, 0);
  mainContentLayout->addWidget(FeedbackTextPane, 2, 0);
  mainContentLayout->addLayout(feedbackCategoryLayout, 3, 0);
  mainContentLayout->addWidget(SubmitButton, 4, 0);

  mainContentLayout->setVerticalSpacing(0);

  QWidget * mainWidget = new QWidget(this);
  mainWidget->setLayout(mainContentLayout);

  setCentralWidget(mainWidget);

  setStyleSheet(APP_STYLING);

  createActions();

  setWindowTitle("Kano Feedback");

  // connect(runProcess, SIGNAL(readyReadStandardOutput()),
  //         this, SLOT(updateOutput()));

  connect(&app, SIGNAL( aboutToQuit() ), this, SLOT( onExitCleanup() ) );
}

/**************************************************************************/
/*********************** Creation of menus/toolbars ***********************/
/**************************************************************************/

void MainWindow::createActions()
{
  aboutAct = new QAction(tr("&About"), this);
  aboutAct->setStatusTip(tr("Show the application's About box"));
  connect(aboutAct, SIGNAL(triggered()), this, SLOT(about()));

  aboutQtAct = new QAction(tr("About &Qt"), this);
  aboutQtAct->setStatusTip(tr("Show the Qt library's About box"));
  connect(aboutQtAct, SIGNAL(triggered()), qApp, SLOT(aboutQt()));

}

void MainWindow::handleSubmitButton()
{
  int index = FeedbackCategoryDropdown->currentIndex();
  //cout << categories[index];
}

/****************************************************/
/*********************** Exit ***********************/
/****************************************************/

void MainWindow::closeEvent(QCloseEvent *event)
{

}

void MainWindow::onExitCleanup()
{

}

/*******************************************************************/
/*********************** About/Help/Settings ***********************/
/*******************************************************************/

void MainWindow::about()
{
   QMessageBox::about(this, tr("About Kano Feedback"),
            tr("Use <b>Kano Feedback</b> to give us your thoughts on the Kano OS. "
               "Help us improve your experience!"));
}

/******************************************************************/
