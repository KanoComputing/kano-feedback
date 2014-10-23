#!/usr/bin/python
#
#  Module to provide inspectors for each logfile received via Kano Feedback
#

import json
import re
#
# Subclass your inspector from this class below
#
class FeedbackInspector:
    '''
    Each inspector focuses on undrstanding a logfile and provides inspect, a method that parses the log
    The purpose is to fill the object 'report' with info, warn and error data.
    '''
    def __init__(self):
        self.report={ 'info' : [], 'warn' : [], 'error' : [] }
        pass

    def report_info(self):
        return self.report['info']
    def report_warn(self):
        return self.report['warn']
    def report_error(self):
        return self.report['error']

    def add_info(self, entry):
        self.report['info'].append(entry)
    def add_warn(self, entry):
        self.report['warn'].append(entry)
    def add_error(self, entry):
        self.report['error'].append(entry)

    def __assert_finder__(self, logdata, expected, message):
        found_it=False
        for log in logdata.split('\n'):
            if log.find(expected) != -1:
                found_it=True

        return found_it

    def assert_exists(self, logdata, expected, message):
        found_it=self.__assert_finder__(logdata, expected, message)
        if not found_it:
            self.add_warn(message)

        return found_it

    def assert_not_exists(self, logdata, expected, message):
        found_it=self.__assert_finder__(logdata, expected, message)
        if found_it:
            self.add_warn(message)

        return found_it

    def inspect(self, logfile, logdata):
        '''
        Parse logdata and add relevant information to the report, for example:
        self.add_error('something went wrong')
        You can use assert_exists / not_exists to make things easy
        self.assert_exists(logdata, 'I have booted up', 'This unit is not working :-)')
        '''
        pass

#
# Instantiate your specific Inspector for a new logfile parser below
#
class InspectorAppLogsJson(FeedbackInspector):
    def inspect(self, logfile, logdata):

        # Parse each component log entries separately
        try:
            jsonlog=json.loads(logdata)
            for component_name in jsonlog:

                # Search for relevant events on each component
                for component_entry in jsonlog[component_name]:
                    if component_entry['level'] == 'error':
                        self.add_error ("component <%s> reported errors" % component_name)
        except:
            self.add_error('Could not read logs in Json format')
            raise


class InspectorAppLogsRaw(FeedbackInspector):
    def inspect(self, logfile, logdata):
        self.assert_not_exists(logdata, 'rdate FAIL', 'Rdate has failed at least once')
        self.assert_not_exists(logdata, 'make-minecraft error', 'Make Minecraft has reported problems')

class InspectorCmdline(FeedbackInspector):
    def inspect(self, logfile, logdata):
        self.assert_exists(logdata, 'ipv6.disable=1', 'IPv6 is not forcibly disabled through the kernel command line')

class InspectorConfig(FeedbackInspector):
    pass

class InspectorDmesg(FeedbackInspector):
    def inspect(self, logfile, logdata):
        self.assert_exists(logdata, 'wlan0: associated', 'This unit has not been wirelessly associated since it last booted')

class InspectorHdmiInfo(FeedbackInspector):
    def inspect(self, logfile, logdata):

        minimum_display_width=1024
        minimum_display_height=768

        # search for the current video mode (CEA / DMT) and the current display resolution
        try:
            m = re.search('HDMI:EDID found preferred (.*) detail timing format: (.*)x(.*)p.*', logdata)
            video_mode = m.group(1)
            display_width = m.group(2)
            display_height = m.group(3)

            self.add_info('Video mode is set to: %s' % video_mode)

            if int(display_width) < minimum_display_width or int(display_height) < minimum_display_height:
                self.add_error('Current display mode is too small: %sx%s (minimum: %sx%s)' % \
                                   (display_width, display_height, minimum_display_width, minimum_display_height))
            else:
                self.add_info('Current display mode should be ok: %sx%s' % (display_width, display_height))
        except:
            self.add_error('Could not determine current display mode')
            raise


class InspectorKanuxVersion(FeedbackInspector):
    def inspect(self, logfile, logdata):
        self.add_info('Current Kanux Version: %s' % logdata.split('\n')[1])
        self.add_info('Last updated on: %s' % logdata.split('\n')[0])

class InspectorKwifiCache(FeedbackInspector):
    def inspect(self, logfile, logdata):
        if not len(logdata):
            self.add_warn('Looks like there is no wireless credentials cache, unit is connected over Ethernet')
            return

        self.assert_exists(logdata, 'encryption": "wpa"', 'There is a non-WPA connection in the cache (WEP or Open)')

class InspectorPackages(FeedbackInspector):
    def inspect(self, logfile, logdata):
        pkg_gtk_any_regex='libgtk-(.*):armhf.*'
        pkg_gtk310='libgtk-3-0:armhf-3.10.2-1+rpi9rpi1'

        # Search for Gtk current installed package
        try:
            m = re.search(pkg_gtk_any_regex, logdata)
            current_gtk=m.group(0)
            if current_gtk == pkg_gtk310:
                self.add_info('Current Gtk library: %s, looks good!' % (current_gtk))
            else:
                self.add_warn('Current Gtk library: %s, does *not* look good!' % (current_gtk))
        except:
            self.add_error('Could not determine the currently installed Gtk library')


class InspectorProcess(FeedbackInspector):
    pass


class InspectorUsbDevices(FeedbackInspector):
    def inspect(self, logfile, logdata):
        kano_wireless_dongle='Ralink Technology, Corp. RT5370 Wireless Adapter'
        kano_keyboard='ID 1997:2433'

        self.assert_exists(logdata, kano_wireless_dongle, 'This Kit is not using the de-facto wireless dongle provided by Kano')
        self.assert_exists(logdata, kano_keyboard, 'This Kit is not using the de-facto Kano Keyboard')

        
class InspectorWpalog(FeedbackInspector):
    def inspect(self, logfile, logdata):
        wpa_authenticated='EAPOL authentication completed successfully'
        self.assert_exists(logdata, wpa_authenticated, 'There is no indication of a successfull WPA wireless association')


class InspectorIfconfig(FeedbackInspector):
    def inspect(self, logfile, logdata):

        # Determine if Ethernet, Wireless, both, or none
        find_ip_regex='%s.*\n.*inet addr:([0-9\.]*) (.*)'
        ip_ethernet=ip_wireless=None

        try:
            # Find if we have an assigned IP address on the Ethernet interface
            m = re.search(find_ip_regex % 'eth0', logdata, re.MULTILINE)
            ip_ethernet=m.group(1)
        except:
            pass

        try:
            # Same for the wireless device
            m = re.search(find_ip_regex % 'wlan0', logdata, re.MULTILINE)
            ip_wireless=m.group(1)
        except:
            pass

        # Find out how the unit is network connected and explain it
        if not ip_ethernet and not ip_wireless:
            self.add_warn('This unit does *not* have an IP on Ethernet or Wireless')
        elif ip_ethernet and not ip_wireless:
            self.add_info('This unit is connected through the Ethernet device: %s' % ip_ethernet)
        elif not ip_ethernet and ip_wireless:
            self.add_info('This unit is connected through the Wireless device: %s' % ip_wireless)
        elif ip_ethernet and ip_wireless:
            self.add_error('This unit is connected through *both* the Wireless and Ethernet devices: %s - %s' \
                           % ip_wireless, ip_ethernet)


class InspectorScreenshot(FeedbackInspector):
    def inspect(self, logfile, logdata):
        self.add_info('This feedback report contains a screenshot')


#
# Add your inspector to the list
#
inspectors= {
    'app-logs.txt'      : InspectorAppLogsRaw,
    'app-logs-json.txt' : InspectorAppLogsJson,
    'cmdline.txt'       : InspectorCmdline,
    'config.txt'        : InspectorConfig,
    'dmesg.txt'         : InspectorDmesg,
    'hdmi-info.txt'     : InspectorHdmiInfo,
    'kanux_version.txt' : InspectorKanuxVersion,
    'kwificache.txt'    : InspectorKwifiCache,
    'packages.txt'      : InspectorPackages,
    'process.txt'       : InspectorProcess,
    'usbdevices.txt'    : InspectorUsbDevices,
    'wpalog.txt'        : InspectorWpalog,
    'ifconfig.txt'      : InspectorIfconfig,
    'screenshot.png'    : InspectorScreenshot
}
