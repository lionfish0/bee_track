from flask import Flask, jsonify
import datetime

app = Flask(__name__)

records = {}

@app.route("/set/<int:systemid>/<string:ipaddress>")
def save(systemid,ipaddress):
    now = datetime.datetime.now()
    records[systemid] = {'datetime':now, 'ipaddress':ipaddress}
    return "Saved"

@app.route("/get_json")
def get():
    return jsonify(records)

@app.route("/get")
def hello_world():
    output = "<html><body><table>\n"
    output += "<tr><th>Device</th></th>IP Address</th><th>Last seen</th></tr>\n"
    now = datetime.datetime.now()
    for r in records:
        ipaddr = records[r]['ipaddress']
        if ((now - records[r]['datetime'])<datetime.timedelta(hours = 12)):
            output += "<tr><td>%s</td><td>%s</td><td><a href='http://%s:8000'>%s</a></td></tr>\n" % (r,records[r]['datetime'],ipaddr,ipaddr)
    output += "</table>\n</body></html>"
    return output

