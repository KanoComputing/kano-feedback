/*
 * kano_feedback.c
 *
 * Copyright (C) 2014, 2015 Kano Computing Ltd.
 * License: http://www.gnu.org/licenses/gpl-2.0.txt GNU General Public License v2
 *
 */

#include <gtk/gtk.h>
#include <gdk/gdk.h>
#include <glib/gi18n.h>
#include <gdk-pixbuf/gdk-pixbuf.h>
#include <gio/gio.h>

#include <lxpanel/plugin.h>

#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <time.h>

#include <kdesk-hourglass.h>

#include <libintl.h>
#define _(str) gettext(str)

#define WIDGET_ICON "/usr/share/kano-feedback/media/icons/feedback-widget.png"
#define CONTACT_ICON "/usr/share/kano-feedback/media/icons/Icon-Contact.png"
#define SCREENSHOT_ICON "/usr/share/kano-feedback/media/icons/Icon-Report.png"
#define KNOWLEDGE_ICON "/usr/share/kano-feedback/media/icons/Icon-Help.png"

#define CONTACT_CMD "/usr/bin/kano-feedback"
#define REPORT_CMD "/usr/bin/kano-feedback bug"
#define HELP_CMD "/usr/bin/kano-help-launcher"
#define SOUND_CMD "/usr/bin/aplay /usr/share/kano-media/sounds/kano_open_app.wav"

#define PLUGIN_TOOLTIP "Help"

typedef struct {
    LXPanel *panel;
} kano_feedback_plugin_t;

static gboolean show_menu(GtkWidget *, GdkEventButton *);
static GtkWidget* get_resized_icon(const char* filename);
static void selection_done(GtkWidget *);
static void menu_pos(GtkMenu *menu, gint *x, gint *y, gboolean *push_in,
                     GtkWidget *widget);

static GtkWidget *plugin_constructor(LXPanel *panel, config_setting_t *settings)
{
    /* initialize i18n */
    setlocale(LC_MESSAGES,"");
    setlocale(LC_CTYPE,"");
    bindtextdomain("kano-feedback","/usr/share/locale");
    textdomain("kano-feedback");

    /* allocate our private structure instance */
    kano_feedback_plugin_t *plugin = g_new0(kano_feedback_plugin_t, 1);
    plugin->panel = panel;

    /* need to create a widget to show */
    GtkWidget *pwid = gtk_button_new();
    gtk_button_set_relief(GTK_BUTTON(pwid), GTK_RELIEF_NONE);

    lxpanel_plugin_set_data(pwid, plugin, g_free);

    /* create an icon */
    GtkWidget *icon = gtk_image_new_from_file(WIDGET_ICON);

    /* set border width */
    gtk_container_set_border_width(GTK_CONTAINER(pwid), 0);

    /* add the label to the container */
    gtk_container_add(GTK_CONTAINER(pwid), GTK_WIDGET(icon));

    /* our widget doesn't have a window... */
    gtk_widget_set_has_window(pwid, FALSE);

    gtk_signal_connect(GTK_OBJECT(pwid), "button-press-event",
               GTK_SIGNAL_FUNC(show_menu), NULL);

    /* Set a tooltip to the icon to show when the mouse sits over the it */
    GtkTooltips *tooltips;
    tooltips = gtk_tooltips_new();
    gtk_tooltips_set_tip(tooltips, GTK_WIDGET(icon), PLUGIN_TOOLTIP, NULL);

    gtk_widget_set_sensitive(icon, TRUE);

    /* show our widget */
    gtk_widget_show_all(pwid);

    return pwid;
}

static void launch_cmd(const char *cmd, const char *appname)
{
    GAppInfo *appinfo = NULL;
    gboolean ret = FALSE;

    appinfo = g_app_info_create_from_commandline(cmd, NULL,
                G_APP_INFO_CREATE_NONE, NULL);

    if (appname) {
        kdesk_hourglass_start((char *) appname);
    }

    if (appinfo == NULL) {
        perror("Command lanuch failed.");
        if (appname) {
            kdesk_hourglass_end();
        }
        return;
    }

    ret = g_app_info_launch(appinfo, NULL, NULL, NULL);
    if (!ret) {
        perror("Command lanuch failed.");
        if (appname) {
            kdesk_hourglass_end();
        }
    }
}

void contact_clicked(GtkWidget* widget)
{
    /* Launch Contact Us*/
    launch_cmd(CONTACT_CMD, "kano-feedback");
    /* Play sound */
    launch_cmd(SOUND_CMD, NULL);
}

void screenshot_clicked(GtkWidget* widget)
{
    /* Launch Report a problem*/
    launch_cmd(REPORT_CMD, "kano-feedback");
    /* Play sound */
    launch_cmd(SOUND_CMD, NULL);
}

void knowledge_clicked(GtkWidget* widget)
{
    /* Launch help center */
    launch_cmd(HELP_CMD, "kano-help-launcher");
    /* Play sound */
    launch_cmd(SOUND_CMD, NULL);
}

static gboolean show_menu(GtkWidget *widget, GdkEventButton *event)
{
    GtkWidget *menu = gtk_menu_new();
    GtkWidget *header_item;

    if (event->button != 1)
        return FALSE;

    /* Create the menu items */
    header_item = gtk_menu_item_new_with_label("Help");
    gtk_widget_set_sensitive(header_item, FALSE);
    gtk_menu_append(GTK_MENU(menu), header_item);
    gtk_widget_show(header_item);

    /* Contact button */
    GtkWidget* contact_item = gtk_image_menu_item_new_with_label(_("Contact Us"));
    g_signal_connect(contact_item, "activate", G_CALLBACK(contact_clicked), NULL);
    gtk_menu_append(GTK_MENU(menu), contact_item);
    gtk_widget_show(contact_item);
    gtk_image_menu_item_set_image(GTK_IMAGE_MENU_ITEM(contact_item), get_resized_icon(CONTACT_ICON));
    /* Knowledge button */
    GtkWidget* knowledge_item = gtk_image_menu_item_new_with_label(_("Help Center"));
    g_signal_connect(knowledge_item, "activate", G_CALLBACK(knowledge_clicked), NULL);
    gtk_menu_append(GTK_MENU(menu), knowledge_item);
    gtk_widget_show(knowledge_item);
    gtk_image_menu_item_set_image(GTK_IMAGE_MENU_ITEM(knowledge_item), get_resized_icon(KNOWLEDGE_ICON));
    /* Screenshot button */
    GtkWidget* screenshot_item = gtk_image_menu_item_new_with_label(_("Report a Problem"));
    g_signal_connect(screenshot_item, "activate", G_CALLBACK(screenshot_clicked), NULL);
    gtk_menu_append(GTK_MENU(menu), screenshot_item);
    gtk_widget_show(screenshot_item);
    gtk_image_menu_item_set_image(GTK_IMAGE_MENU_ITEM(screenshot_item), get_resized_icon(SCREENSHOT_ICON));

    g_signal_connect(menu, "selection-done", G_CALLBACK(selection_done), NULL);

    /* Show the menu. */
    gtk_menu_popup(GTK_MENU(menu), NULL, NULL,
               (GtkMenuPositionFunc) menu_pos, widget,
               event->button, event->time);

    return TRUE;
}

static GtkWidget* get_resized_icon(const char* filename)
{
    GError *error = NULL;
    GdkPixbuf* pixbuf = gdk_pixbuf_new_from_file_at_size (filename, 40, 40, &error);
    return gtk_image_new_from_pixbuf(pixbuf);
}

static void selection_done(GtkWidget *menu)
{
    gtk_widget_destroy(menu);
}

static void menu_pos(GtkMenu *menu, gint *x, gint *y, gboolean *push_in,
                     GtkWidget *widget)
{
    int ox, oy, w, h;
    kano_feedback_plugin_t *plugin = lxpanel_plugin_get_data(widget);
    GtkAllocation allocation;

    gtk_widget_get_allocation(GTK_WIDGET(widget), &allocation);

    gdk_window_get_origin(gtk_widget_get_window(widget), &ox, &oy);

    /* FIXME The X origin is being truncated for some reason, reset
       it from the allocaation. */
    ox = allocation.x;

#if GTK_CHECK_VERSION(2,20,0)
    GtkRequisition requisition;
    gtk_widget_get_requisition(GTK_WIDGET(menu), &requisition);
    w = requisition.width;
    h = requisition.height;

#else
    w = GTK_WIDGET(menu)->requisition.width;
    h = GTK_WIDGET(menu)->requisition.height;
#endif
    if (panel_get_orientation(plugin->panel) == GTK_ORIENTATION_HORIZONTAL) {
        *x = ox;
        if (*x + w > gdk_screen_width())
            *x = ox + allocation.width - w;
        *y = oy - h;
        if (*y < 0)
            *y = oy + allocation.height;
    } else {
        *x = ox + allocation.width;
        if (*x > gdk_screen_width())
            *x = ox - w;
        *y = oy;
        if (*y + h >  gdk_screen_height())
            *y = oy + allocation.height - h;
    }

    /* Debugging prints */
    /*printf("widget: x,y=%d,%d  w,h=%d,%d\n", ox, oy, allocation.width, allocation.height );
    printf("w-h %d %d\n", w, h); */

    *push_in = TRUE;

    return;
}

FM_DEFINE_MODULE(lxpanel_gtk, kano_feedback)

/* Plugin descriptor. */
LXPanelPluginInit fm_module_init_lxpanel_gtk = {
    .name = N_("Kano Feedback"),
    .description = N_("Reach out to us and get help."),
    .new_instance = plugin_constructor,
    .one_per_system = FALSE,
    .expand_available = FALSE
};
