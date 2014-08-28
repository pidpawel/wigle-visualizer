#!/usr/bin/python3
# Author: pidpawel
# Copyright 2014
# Dual license: MIT and Beerware
from flask import Flask, render_template, jsonify, Markup, request
from flask.json import JSONEncoder
import csv
import re

csv_filename = "WigleWifi_20140828192242.csv"


class Record:
    def __init__(self):
        self.mac = None
        self.ssid = None

        self.tags = None

        self.rssi = None

        self.lat = None
        self.lon = None

    def in_bounds(self, boundN, boundE, boundW, boundS):
        return self.lat <= boundN and self.lat >= boundS and self.lon >= boundW and self.lon <= boundS

    def __repr__(self):
        return '%s (%s)' % (self.ssid, self.mac)

    def to_json(self):
        return {'mac': self.mac,
                'ssid': Markup.escape(self.ssid),

                'tags': self.tags,

                'rssi': self.rssi,

                'lat': self.lat,
                'lon': self.lon}

class RecordContainer:
    def __init__(self, duplicate_treshold=0.01):
        self._duplicate_treshold = duplicate_treshold
        self._records = []

    def parse_file(self, filename):
        with open(filename) as csvfile:
            reader = csv.reader(csvfile)
            lineno = 0
            for row in reader:
                lineno += 1
                if lineno < 3:
                    continue

                if row[10] == 'WIFI':
                    record = Record()
                    record.mac = row[0]
                    record.ssid = row[1]

                    record.tags = sorted(re.findall("\[(.+?)\]", row[2]))

                    record.rssi = int(row[5])

                    record.lat = float(row[6])
                    record.lon = float(row[7])

                    self.insert_record(record)

    def insert_record(self, record):
        self._records.append(record)

    def get_points(self, boundN, boundE, boundW, boundS, filter_ssid=None, skip_duplicates=True):
        all_records = self.get_all(filter_ssid=filter_ssid, skip_duplicates=skip_duplicates)
        r = []
        for record in all_records:
            if record.in_bounds(boundN, boundE, boundW, boundS):
                r.append(record)
        return r

    def get_all(self, filter_ssid=None, skip_duplicates=True):
        all_records = self._records
        if filter_ssid:
            all_records = filter(lambda x: x.ssid == filter_ssid, all_records)

        if skip_duplicates and len(self._records) > 0:
            s = sorted(all_records, key=lambda item: "%s%s" % (item.mac, item.ssid))

            r = []
            last = s[0]
            r.append(last)

            for current in s[1:]:
                if last.mac == current.mac and last.ssid == current.ssid:
                    if abs(last.lat - current.lat) < self._duplicate_treshold \
                       and abs(last.lon - current.lon) < self._duplicate_treshold:
                        continue
                    else:
                        r.append(current)
                        last = current
                else:
                    r.append(current)
                    last = current

            return r
        else:
            return all_records

class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Record):
            return obj.to_json()
        return JSONEncoder.default(self, obj)


app = Flask(__name__)
app.json_encoder = CustomJSONEncoder

# @todo: refactor to flasks global
record_container = RecordContainer()
record_container.parse_file(csv_filename)

@app.route("/api/get_points", methods=['GET'])
def api_get_points():
    boundN = float(request.args.get('boundN', None))
    boundE = float(request.args.get('boundE', None))
    boundW = float(request.args.get('boundW', None))
    boundS = float(request.args.get('boundS', None))

    skip_duplicates = True

    if request.args.get('filter_ssid', None):
        skip_duplicates = False

    r = record_container.get_points(boundN=boundN, boundE=boundE, boundW=boundW, boundS=boundS,
                                    filter_ssid = request.args.get('filter_ssid', None),
                                    skip_duplicates=skip_duplicates)
    return jsonify(points=r)

@app.route("/api/get_all_points")
def api_get_all_points():
    r = record_container.get_all(skip_duplicates=False)
    return jsonify(points=r)

@app.route("/")
def index():
    return render_template('big_map.html')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
