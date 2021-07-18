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

#$("a.start")[0].click();

@app.route("/get")
def hello_world():
    output = "" 
    output+= """<html><head><script src="https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js"></script>
    <script type="text/javascript">
$(document).ready(function(){
 
 $('#startall').click(function(){
   $("a.start").each(function(i) { this.click(); });
 });
 
  $('#stopall').click(function(){
   $("a.stop").each(function(i) { this.click(); });
 });
});
</script>
    """
    output+="</head><body><table>\n"
    output += "<tr><th>Device</th></th>IP Address</th><th>Last seen</th></tr>\n"
    now = datetime.datetime.now()
    for r in records:
        ipaddr = records[r]['ipaddress']
        if ((now - records[r]['datetime'])<datetime.timedelta(hours = 12)):
            output += "<tr><td>%s</td><td>%s</td><td><a href='http://%s:8000'>%s</a></td><td><a class='start' href='http://%s:5000/start'>start</a></td><td><a class='stop' href='http://%s:5000/stop'>stop</a></td></tr>\n" % (r,records[r]['datetime'],ipaddr,ipaddr,ipaddr,ipaddr)
    output += "</table>\n"
    
    
    output += "<input type='button' id='startall' value='start'></input><input type='button' id='stopall' value='stop'></input></body></html>"
    return output
