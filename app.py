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

 function command(cmd) {
   $('a.interface').each(function(i) {
         href = $(this).text();
         url = "http://"+href+":5000/"+cmd;
         $.ajax({
              url: url,
              success: function(data, status, jqXHR){}
          });
   })
 }
 
 $('#startall').click(function(){
   command('start');
 });
 
  $('#stopall').click(function(){
   command('stop');
 });
 
 $('input#label').bind('input',function() {
   command("setlabel/a"+$('input#label').val());
 });

 $('input#flashseq').click(function(){
  code = $('input[name="flashseq"]:checked').val();
  command("set/trigger/flashseq/"+code); 
 });
 
 $('#setinterval').click(function(){
    command("set/trigger/t/"+$('input#interval').val());
 });
 
 $('button#reboot').click(function(){
    command("reboot");
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
            output += "<tr><td>%s</td><td>%s</td><td><a class='interface' href='http://%s:8000'>%s</a></td><td><a class='start' href='http://%s:5000/start'>start</a></td><td><a class='stop' href='http://%s:5000/stop'>stop</a></td></tr>\n" % (r,records[r]['datetime'],ipaddr,ipaddr,ipaddr,ipaddr)
    output += "</table>\n"
    output += """
<br />
<input type='button' id='startall' value='start'></input><input type='button' id='stopall' value='stop'></input></body></html>
<br />
<br />
label for file: <input id="label" value="" /><br/>
<br />
Interval <input id="interval" value=3 size=2/> seconds
<button id="setinterval">set</button><br/>
<br />
Flash seq:
<input type='radio' name='flashseq' id='flashseq' value='0' checked>all
<input type='radio' name='flashseq' id='flashseq' value='1'>2
<input type='radio' name='flashseq' id='flashseq' value='2'>1
<input type='radio' name='flashseq' id='flashseq' value='9'>none
<br />
<br />
<br />
Reboot: <button id="reboot">reboot</button><br/><br />
"""
    return output
