#!/usr/bin/env python

__author__ = 'Marianne M. Spiller <github@spiller.me>'
__license__ = 'GPLv3'
__version__  = '0.1'

import argparse
import requests
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

def openHAB_request(url):
    try:
        r = requests.get(url, timeout=10)
    except ConnectionError as e:
        print e
        icinga_critical('REST API not responding') 
    if r.status_code != 200:
        icinga_critical('Item unknown, check name.')

    data = r.json()
    return data

def main():
    main_parser = argparse.ArgumentParser(description=""" Icinga plugin to integrate openHAB 2 """)

    main_parser.add_argument('--protocol', choices=['http', 'https'], default='http', help='Runs your openHAB 2 on HTTP or HTTPS? Default: HTTP.')
    main_parser.add_argument('--host', '-H', dest='host', help='Host running openHAB 2 instance.')
    main_parser.add_argument('--port', '-P', type=int, default=8080, dest='port', help='Port openHAB 2 is running on (default: 8080).')
##    main_parser.add_argument('--timeout', '-T', type=int, default=10, help='Connection timeout, defaults to 10 seconds.')

    mode = main_parser.add_mutually_exclusive_group()
    mode.add_argument('--stats', '-S', action='store_true', help='Get general statistics about your openHAB 2 installation.')
    mode.add_argument('--item', '-I', dest='item', help='Item to get state or value off.')

    main_parser.add_argument('--warning', '-W', help='Optional when using --item. WARNING value; see docs.')
    main_parser.add_argument('--critical', '-C', help='Optional when using --item. CRITICAL value; see docs.')
    main_parser.add_argument('--invertcheck', choices=['true', 'false'], default='false', help='Optional when using --item. Invert check; see docs.')

    args = main_parser.parse_args()
    restapi = args.protocol + '://' + args.host + ':{}'.format(args.port) + '/rest'

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
        itemcount = str(len(openHAB_request(restapi + '/items?recursive=true')))
        thingcount = str(len(openHAB_request(restapi + '/things')))
        systemuuid = requests.get(restapi + '/uuid')
        exit_msg = thingcount + ' things and ' + itemcount + ' items in openHAB 2 system with UUID ' + systemuuid.text + '.|openhab_items=' + itemcount + ';;;; openhab_things=' + thingcount + ';;;;'
        icinga_ok(exit_msg)

    elif args.item:
        itemvalue = openHAB_request(restapi + '/items/' + args.item)

        try:
            float(itemvalue['state'].partition(' ')[0])
            isalpha = False
        except ValueError:
            isalpha = True 

        if isalpha:
            itemstate = str(itemvalue['state'])
            if args.critical:
                if args.critical == itemstate:
                    if args.invertcheck == 'true':
                        icinga_ok(itemstate)
                    else:
                        icinga_critical(itemstate)
                else:
                    if args.invertcheck == 'true':
                        icinga_critical(itemstate)
                    else:
                        icinga_ok(itemstate)
            elif args.warning:
                if args.warning == itemstate:
                    if args.ivertcheck == 'true':
                        icinga_ok(itemstate)
                    else:
                        icinga_warning(itemstate)
                else:
                    if args.invertcheck == 'true':
                        icinga_warning(itemstate)
                    else:
                        icinga_ok(itemstate)
            else:
                icinga_ok(itemstate)
        else:
            itemstate = float(itemvalue['state'].partition(' ')[0])
            perfdata = args.item +'=' + str(itemstate) +';' +perfdata_warn +';' +perfdata_crit +';;'
            exit_msg = str(itemstate) +'|' + perfdata

            if args.critical:
                crit = float(args.critical)
                if itemstate > crit and args.invertcheck == 'false':
                    icinga_critical(exit_msg)
                if itemstate < crit and args.invertcheck == 'true':
                    icinga_critical(exit_msg)

            if args.warning:
                warn = float(args.warning)
                if itemstate > warn and args.invertcheck == 'false':
                    icinga_warning(exit_msg)
                if itemstate < warn and args.invertcheck == 'true':
                    icinga_warning(exit_msg)

            icinga_ok(exit_msg)

    else:
        exit_msg = 'Choose either --stats or --item.'
        icinga_unknown(exit_msg)

if __name__ == "__main__":
    main()
