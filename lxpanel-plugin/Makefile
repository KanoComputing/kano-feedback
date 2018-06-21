# Makefile
#
# Copyright (C) 2014-2018 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU General Public License v2
#

CC=gcc
CFLAGS=`pkg-config --cflags lxpanel gtk+-2.0`
LIBS=`pkg-config --libs lxpanel gtk+-2.0` -lkdesk-hourglass -llxpanel
SRC=kano_feedback.c
BIN=kano_feedback.so
INSTALL_PATH=/usr/lib/arm-linux-gnueabihf/lxpanel/plugins/

# The liblxpanel.so is not reported by pkg-config, help shlibdeps locate it
LXPANEL_RPATH=-Wl,-rpath=/usr/lib/arm-linux-gnueabihf/lxpanel

build: $(BIN)

install:
	install -p -m 0644 $(BIN) $(INSTALL_PATH)

$(BIN): $(SRC)
	$(CC) -Wall $(CFLAGS) -shared -fPIC $(SRC) -o $(BIN) $(LIBS) $(LXPANEL_RPATH)
