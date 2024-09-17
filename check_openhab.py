#!/usr/bin/env python

__author__ = 'Marianne M. Spiller <github@spiller.me>'
__license__ = 'GPLv3'
__version__  = '0.1'

import argparse
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError
import sys

def icinga_ok(msg):
    msg = str(msg)
    print('openHAB OK - ' + msg)
    sys.exit(0)

def icinga_warning(msg):
    msg = str(msg)
    print('openHAB WARNING - ' + msg)
    sys.exit(1)

def icinga_critical(msg):
    msg = str(msg)
    print('openHAB CRITICAL - ' + msg)
    sys.exit(2)

def icinga_unknown(msg):
    msg = str(msg)
    print('openHAB UNKNOWN - ' + msg)
    sys.exit(3)

def openHAB_request(url, auth):
    try:
        r = requests.get(url, timeout=10, auth=auth)
    except ConnectionError as e:
        print(e)
        icinga_unknown('REST API not responding')
    if r.status_code == 401:
        icinga_unknown('Item unknown, authentication required.')
    if r.status_code == 403:
        icinga_unknown('Item unknown, authentication failed.')
    if r.status_code != 200:
        icinga_unknown('Item unknown, check name.')

    data = r.json()
    return data

def main():
    main_parser = argparse.ArgumentParser(description=""" Icinga plugin to integrate openHAB """)

    main_parser.add_argument('--protocol', choices=['http', 'https'], default='http', help='Runs your openHAB on HTTP or HTTPS? Default: HTTP.')
    main_parser.add_argument('--host', '-H', dest='host', help='Host running openHAB instance.')
    main_parser.add_argument('--port', '-P', type=int, default=8080, dest='port', help='Port openHAB is running on (default: 8080).')
##    main_parser.add_argument('--timeout', '-T', type=int, default=10, help='Connection timeout, defaults to 10 seconds.')

    mode = main_parser.add_mutually_exclusive_group()
    mode.add_argument('--stats', '-S', action='store_true', help='Get general statistics about your openHAB installation.')
    mode.add_argument('--item', '-I', dest='item', help='Item to get state or value off.')
    mode.add_argument('--thing', '-T', dest='thing', help='Thing to get state or value off.')

    main_parser.add_argument('--warning', '-W', help='Optional when using --item. WARNING value; see docs.')
    main_parser.add_argument('--critical', '-C', help='Optional when using --item. CRITICAL value; see docs.')
    main_parser.add_argument('--invert', '-i', action='store_true', help='Invert compare direction.')

    main_parser.add_argument('--user', '-U', help='Optional when authentication is needed. USER value; see docs.')
    main_parser.add_argument('--password', '-p', help='Optional when authentication is needed. PASSWORD value; see docs.')

    args = main_parser.parse_args()
    restapi = args.protocol + '://' + args.host + ':{}'.format(args.port) + '/rest'

    auth = None
    if args.user:
        auth = HTTPBasicAuth(args.user, '' if args.password is None else args.password)

    if args.port < 1 or args.port > 65535:
        icinga_unknown('Port has to be something between 1 and 65535.')

    if args.warning:
        perfdata_warn = str(args.warning)
    else:
        perfdata_warn = ''

    if args.critical:
        perfdata_crit = str(args.critical)
    else:
        perfdata_crit = ''

    if args.stats:
        itemcount = str(len(openHAB_request(restapi + '/items?recursive=true', auth)))
        thingcount = str(len(openHAB_request(restapi + '/things', auth)))
        systemuuid = requests.get(restapi + '/uuid', auth=auth)
        exit_msg = thingcount + ' things and ' + itemcount + ' items in openHAB system with UUID ' + systemuuid.text + '.|openhab_items=' + itemcount + ';;;; openhab_things=' + thingcount + ';;;;'
        icinga_ok(exit_msg)

    elif args.item:
        itemvalue = openHAB_request(restapi + '/items/' + args.item, auth)
        if itemvalue['state'].isalpha() == True:
            itemstate = str(itemvalue['state'])
            if args.critical:
                if args.critical == itemstate:
                    icinga_critical(itemstate)
                else:
                    icinga_ok(itemstate)
            elif args.warning:
                if args.warning == itemstate:
                    icinga_warning(itemstate)
                else:
                    icinga_ok(itemstate)
            else:
                icinga_ok(itemstate)
        else:
            itemstate = float(itemvalue['state'])
            perfdata = args.item +'=' + str(itemstate) +';' +perfdata_warn +';' +perfdata_crit +';;'
            exit_msg = str(itemstate) +'|' + perfdata

            if args.critical:
                crit = float(args.critical)
                if args.invert:
                    if itemstate < crit:
                        icinga_crtitical(exit_msg)
                else:
                    if itemstate > crit:
                        icinga_critical(exit_msg)

            if args.warning:
                warn = float(args.warning)
                if args.invert:
                    if itemstate < warn:
                        icinga_warning(exit_msg)
                else:
                    if itemstate > warn:
                        icinga_warning(exit_msg)

            icinga_ok(exit_msg)

    elif args.thing:
        thingvalue = openHAB_request(restapi + '/things/' + args.thing, auth)
        thingstatus = str(thingvalue['statusInfo']['status'])
        thingstatusdetail = str(thingvalue['statusInfo']['statusDetail'])

        if thingstatus == 'ONLINE':
            icinga_ok(thingvalue['label'] + ' ' + thingstatus)
        elif thingstatus == 'OFFLINE':
            if thingstatusdetail != 'NONE':
                icinga_critical(thingvalue['label'] + ' ' + thingstatus + ' - ' + thingstatusdetail)
            else:
                icinga_critical(thingvalue['label'] + ' ' + thingstatus)
        else:
            if thingstatusdetail != 'NONE':
                icinga_warning(thingvalue['label'] + ' ' + thingstatus + ' - ' + thingstatusdetail)
            else:
                icinga_warning(thingvalue['label'] + ' ' + thingstatus)

    else:
        exit_msg = 'Choose either --stats, --item or --thing'
        icinga_unknown(exit_msg)

if __name__ == "__main__":
    main()
