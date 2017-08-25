What's this all about?
======================

`check_openhab2.py` helps you to integrate your openHAB 2 installation with Icinga 2.

One difficulty is, that there are naturally several different types of items:
* Number items like temperature or humidity
* Switch items which are typically ON or OFF
* Contact items which are typically OPEN or CLOSED
* Player items which can be PLAY, PAUSE and so on
* Rollershutter items which can be INCREASING and DECREASING
* ...

And of course all items could be in unknown state when restarting; to avoid a lot of unnecessary noise you should use a persistence service of your choice to get all items in defined (*last known*) states on restart.

Performance Data
----------------
Performance data are processed in the following use cases:
* when using `check_openhab2.py` with `--stats`
* when using the script with `--item` **and** it is a number item

Examples
--------

### Getting openHAB 2 stats
```
$ ./openhab2.py --host 10.8.0.10 --port 8080 --protocol http --stats
openHAB OK - 36 things and 200 items in openHAB 2 system with UUID 02bb75e1-6195-4154-ae0f-c0b6a5ee6709.|openhab_items=200;;;; openhab_things=36;;;;
```

### Check number item with thresholds
```
$ ./openhab2.py --host 10.8.0.10 --port 8080 --item Wetter_Temperatur --warning 18 --critical 20
openHAB CRITICAL - Wetter_Temperatur=21.4;18;20;;
```

![Number Item Check Example](doc/screenshots/icingaweb2_number_example.jpg)

### Check Switch item with threshold
```
$ ./openhab2.py --host 10.8.0.10 --port 8080 --item Schlafzimmer_0_Fenster --warning OPEN
openHAB OK - CLOSED
```

Arguments
---------

arg                 | explain
-----------------------------
`--host` / `-H`     | **Required.** Host your openHAB 2 installation is running on
`--port` / `-P`     | Port your openHAB 2 REST API is listening on. Default: 8080
`--protocol`        | Choose either HTTP or HTTPS. Default: HTTPS
`--stats` / `-S`    | Get thing and item count for your openHAB 2. Supports perfdata. Mutually exclusive to `--item`
`--item` / `-I`     | Check a specific item (see examples below). Mutually exclusive to `--stats`
`--warning` / `-W`  | Value Icinga 2 should exit WARNING for (see examples)
`--critical` / `-C` | Value Icinga 2 should exit CRITICAL for (see examples)
