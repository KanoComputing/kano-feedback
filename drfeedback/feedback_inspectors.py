#!/usr/bin/python
#
#  Module to provide inspectors for each logfile received via Kano Feedback
#

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
        for log in logdata:
            if log.find(expected) != -1:
                found_it=True

        return found_it

    def assert_exists(self, logdata, expected, message):
        found_it=self.__assert_finder__(logdata, expected, message)
        if not found_it:
            self.add_warn(message)

    def assert_not_exists(self, logdata, expected, message):
        found_it=self.__assert_finder__(logdata, expected, message)
        if found_it:
            self.add_warn(message)

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
class InspectorAppLogs(FeedbackInspector):
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
        self.assert_exists(logdata, 'edid_parser exited with code 0', 'EDID Parser has reported problems')

class InspectorKanuxVersion(FeedbackInspector):
    def inspect(self, logfile, logdata):
        self.add_info('Current Kanux Version: %s' % logdata[1].strip())
        self.add_info('Last updated on: %s' % logdata[0].strip())

class InspectorKwifiCache(FeedbackInspector):
    def inspect(self, logfile, logdata):
        if not len(logdata):
            self.add_warn('Looks like there is no wireless credentials cache, unit is connected over Ethernet')
            return

        self.assert_exists(logdata, 'encryption": "wpa"', 'There is a non-WPA connection in the cache (WEP or Open)')

class InspectorPackages(FeedbackInspector):
    pass

class InspectorProcess(FeedbackInspector):
    pass

class InspectorUsbDevices(FeedbackInspector):
    def inspect(self, logfile, logdata):
        kano_usb_factory='Ralink Technology, Corp. RT5370 Wireless Adapter'
        self.assert_exists(logdata, kano_usb_factory, 'This Kit is not using the de-facto wireless dongle provided by Kano')
        
class InspectorWpalog(FeedbackInspector):
    def inspect(self, logfile, logdata):
        wpa_authenticated='EAPOL authentication completed successfully'
        self.assert_exists(logdata, wpa_authenticated, 'There is no indication of a successfull WPA wireless association')

#
# Add your inspector to the list
#

inspectors= {
    'app-logs.txt'      : InspectorAppLogs,
    'cmdline.txt'       : InspectorCmdline,
    'config.txt'        : InspectorConfig,
    'dmesg.txt'         : InspectorDmesg,
    'hdmi-info.txt'     : InspectorHdmiInfo,
    'kanux_version.txt' : InspectorKanuxVersion,
    'kwificache.txt'    : InspectorKwifiCache,
    'packages.txt'      : InspectorPackages,
    'process.txt'       : InspectorProcess,
    'usbdevices.txt'    : InspectorUsbDevices,
    'wpalog.txt'        : InspectorWpalog
}
