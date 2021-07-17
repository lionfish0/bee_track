function getdatestring() {
    //https://stackoverflow.com/a/25835182
    var d = new Date();
    var curr_day = d.getDate();
    var curr_month = d.getMonth();
    var curr_year = d.getFullYear();
    var curr_hour = d.getHours();
    var curr_min = d.getMinutes();
    var curr_sec = d.getSeconds();
    curr_month++ ; // In js, first month is 0, not 1
    st = curr_year + "-" + curr_month + "-" + curr_day + "T" + curr_hour + ":" + curr_min + ":" + curr_sec;
    return st   
}
    
function msg(message) {
    if (message.slice(-1) != '\n') {message=message + "\n";}
    $("#console").val($("#console").val() + message);// + "\n");
    var con = $('#console');
    con.scrollTop(con[0].scrollHeight - con.height());
}


image = 0
imagecount = 0
$("input#url").val(window.location.hostname+":5000")
url = "http://"+$('input#url').val()+"/setdatetime/"+getdatestring();
    $.ajax({
      url: url,
      success: function(data, status, jqXHR){
        msg(data);
      },
      error: function(jqXHR, status, errorThrown){msg('Startup Error');},
    });
$('button#start').click(function(){
    msg('Starting...');
    url = "http://"+$('input#url').val()+"/start";
    $.ajax({
      url: url,
      success: function(data, status, jqXHR){
        msg(data);
      },
      error: function(jqXHR, status, errorThrown){msg('Start Error');},
    });
});
$('button#stop').click(function(){
    msg('Stop...');
    url = "http://"+$('input#url').val()+"/stop";
    $.ajax({
      url: url,
      success: function(data, status, jqXHR){
        msg(data);
      },
      error: function(jqXHR, status, errorThrown){msg('Stop Error');},
    });
});
$('button#imageup').click(function(){image=image+1;})
$('button#imagedown').click(function(){image=image-1;})
$('button#imageupx10').click(function(){image=image+10;})
$('button#imagedownx10').click(function(){image=image-10;})


setInterval(function(){ 
    url = "http://"+$('input#url').val()+"/getdiskfree";
    $.ajax({
      url: url,
      success: function(data, status, jqXHR){
        msg("Disk space: "+Math.round(parseInt(data)/1000000)+" Mb");
      }});
}, 60000);

setInterval(function(){ 
    url = "http://"+$('input#url').val()+"/getbattery";
    $.ajax({
      url: url,
      success: function(data, status, jqXHR){
        msg("!!");
        msg("Get Battery: "+data)
        $('#battery').html(data)
        if (data.substring(0,3)=='low') {$('#lowbattery').get(0).play();}
      }});
}, 60000);


setInterval(function(){ 

    url = "http://"+$('input#url').val()+"/getimagecount";
    $.ajax({
      url: url,
      success: function(data, status, jqXHR){

        newtic = data
        if (newtic!=imagecount)
        {

            imagecount = newtic
            msg("new image");
            if($("#latestimage").is(':checked')) {

                image = imagecount-1
                $('#download').click();
            }
        }
      }
      
      
      });
}, 1000);






setInterval(function(){ 
    if($("#contactimage").is(':checked')) {
        url = "http://"+$('input#url').val()+"/getcontact";
        $.ajax({
          url: url,
          success: function(data, status, jqXHR){
            console.log(data);
            if (data!=null) {$('#beep').get(0).play();}
            if ((data!=null) && ('track' in data) && (data['track']!=null) && (data['track'].length>0)) {
                
                confident = false;
                for (var i=0;i<data['track'].length;i++){
                    //confident = confident | data['track'][i]['confident']; //true if any of the patches is true
                    console.log(data['track'][i]['prediction']);
                    console.log($('input#detectthreshold').val());
                    confident = confident | (data['track'][i]['prediction']<$('input#detectthreshold').val()); //true if any of the predictions=0 (which is detected)
                }
                if (confident) {$('#beep2s').get(0).play();}
                image = data['index']-1
                $('#download').click();
            }
          }
          
          
          });
    }
}, 500);




setInterval(function(){ 
    url = "http://"+$('input#url').val()+"/getmessage";
    $.ajax({
      url: url,
      success: function(data, status, jqXHR){
        if (data.length>1) {
          msg(data)
        }
      }
      
      
      });
}, 1000);

function drawpixel(imdata,x,y,width,height,r,g,b) {
    pos = 4*(x+y*width)
    imdata[pos] = r
    imdata[pos+1] = g
    imdata[pos+2] = b
}

function drawcircle(imdata,x,y,size,imscale,width,height,r,g,b) {
    if (size<0) { size=0; }

    x=Math.round(x/imscale)
    //y=height-Math.round(y/imscale)
    y=Math.round(y/imscale)
    for (angle=0;angle<2*3.14159;angle+=0.1) {
        drawpixel(imdata,Math.round(x+Math.cos(angle)*size),Math.round(y+Math.sin(angle)*size),width,height,r,g,b)
    }
}

function drawcrosshair(imdata,x,y,size,imscale,width,height,r,g,b) {
    if (size<0) { size=0; }
    size = size + 3; //corrects for removed pixels around centre of reticule, and a bit more
    x=Math.round(x/imscale)
    //y=height-Math.round(y/imscale)
    y=Math.round(y/imscale)
    for (xstep=x-size;xstep<x+size;xstep+=1) {
        if (Math.abs(xstep-x)>3) {
            drawpixel(imdata,xstep,y,width,height,r,g,b) }
    }
    for (ystep=y-size;ystep<y+size;ystep+=1) {
        if (Math.abs(ystep-y)>3) {
            drawpixel(imdata,x,ystep,width,height,r,g,b) }
    }

}

function convertJSONtoImageURL(data) {
    img = data['photo']
    record = data['record']
    height = img.length
    width = img[0].length

    var canvas=document.createElement("canvas");
    var ctx=canvas.getContext("2d");

    // size the canvas to your desired image
    canvas.width=width;
    canvas.height=height;

    // get the imageData and pixel array from the canvas
    var imgData=ctx.getImageData(0,0,width,height);
    var imdata=imgData.data;

    // manipulate some pixel elements
    row = 0; //height-1;
    col = 0;
    scale = 255/$('input#maxval').val()

    for(var i=0;i<imdata.length;i+=4){
        c = img[row][col]*scale;
        if (c>255) {c=255;}
        imdata[i]=c;
        imdata[i+1] = c;
        imdata[i+2] = c;
        imdata[i+3]=255; // make this pixel opaque
        col = col + 1;
        if (col>=width) {
          col = 0;
          row = row + 1;
        }
    }

    blocksize = 5;
    if ('track' in data) {
        if ((data['track']!=null) && (data['track'].length>0)) {
            console.log(data['track']);
            for (var i=0;i<data['track'].length;i++){
                msg([data['track'][i]['searchmax'],data['track'][i]['mean'],data['track'][i]['centremax'],data['track'][i]['prediction']])
                drawcrosshair(imdata,data['track'][i]['x'],data['track'][i]['y'],Math.round(data['track'][i]['searchmax']/10),blocksize,width,height,0,0,255);
                drawcrosshair(imdata,data['track'][i]['x'],data['track'][i]['y'],Math.round(-data['track'][i]['prediction']*10),blocksize,width,height,255,255,0);
                console.log(data['track'][i]['prediction'])
                drawcircle(imdata,data['track'][i]['x'],data['track'][i]['y'],5,blocksize,width,height,0,0,255);
                if (data['track'][i]['prediction']<$('input#detectthreshold').val()) {
                    drawcircle(imdata,data['track'][i]['x'],data['track'][i]['y'],15,blocksize,width,height,255,255,0);
                }
            }
            
        }
    }
    // put the modified pixels back on the canvas
    ctx.putImageData(imgData,0,0);
    return "url('"+canvas.toDataURL()+"')";
}


$('button.refreshimages').click(function(){refreshimages();});

$('input#label').bind('input',function() {
url = "http://"+$('input#url').val()+"/setlabel/a"+$('input#label').val(); //have to add an extra character so an empty string can be sent!
$.ajax({
      url: url,
      success: function(data, status, jqXHR){
        msg('Set');
      },
      error: function(jqXHR, status, errorThrown){msg('Set Error');}
    });
});

$('input#maxval').bind('input',function() {refreshimages();});
function refreshimages(){
    //$('audio#beep')[0].play();
    $('span#index').text(image+1);//have to add one as python is zero indexed
    $('span#imagecount').text(imagecount);
    msg('Downloading...');
    
    camid = $('input#camid').val()
    url = "http://"+$('input#url').val()+"/getimage/"+image+"/"+camid;
    $.getJSON(url, function(data) {$('#image').css("background-image",convertJSONtoImageURL(data)); }); 
    
    url = "http://"+$('input#url').val()+"/getimagecentre/"+image+"/"+camid;
    $.getJSON(url, function(data) {$('#image_centre').css("background-image",convertJSONtoImageURL(data)); }); 
}

$('input#realtimetracking').click(function(){
  if (document.getElementById('realtimetracking').checked) {
    code = "1";
  }
  else
  {
    code = "0";
  }
  url = "http://"+$('input#url').val()+"/set/tracking/track/"+code;
  $.ajax({
      url: url,
      success: function(data, status, jqXHR){
        msg('Set');
      },
      error: function(jqXHR, status, errorThrown){msg('Set Error');}
  });
});

$('button#setinterval').click(function(){
    msg('Setting...');
    url = "http://"+$('input#url').val()+"/set/trigger/t/"+$('input#interval').val();
    $.ajax({
      url: url,
      success: function(data, status, jqXHR){
        msg('Set');
      },
      error: function(jqXHR, status, errorThrown){msg('Set Error');}
    });
});

function sendinstruction(instruction){
    msg(instruction);
    url = "http://"+$('input#url').val()+instruction;
    $.ajax({
      url: url,
      success: function(data, status, jqXHR){
        msg(data);
      },
      error: function(jqXHR, status, errorThrown){msg('Instruction Error');}
    });
}

$('input#console_input').keyup(function(e){
    if(e.keyCode == 13)
    {
        sendinstruction($('input#console_input').val());
    }
});
