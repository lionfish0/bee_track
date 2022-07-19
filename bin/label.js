function convertJSONtoImageURL(data,drawcrosshairs) {
    if (data === null) {alert("Failed");}
    img = data['photo']
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
    
    var sum = 0;
    var count = 0;
    for( var i = 0; i < img.length; i+=1 ){
      for( var j = 0; j < img[i].length; j+=1 ){
        sum += img[i][j]; //don't forget to add the base
        count += 1;
      }
    }
    var avg = sum/count;
    var maxval = avg*2;

    maxval = $('input#scaletext').val();
    //$('span#scaletext').text(maxval.toFixed(2))
    scale = 255/maxval

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
    

    if (drawcrosshairs) {
        
        drawcrosshair(imdata,width,height)
        
    }
    
    
    if (image in tracking_data) {
        

        tdata = tracking_data[image]


        for (var i=0;i<tdata['contact'].length;i++){
            //console.log(tdata['contact'][i]['x'],tdata['contact'][i]['y'])
            drawscaledcrosshair(imdata,width,height,tdata['contact'][i]['x'],tdata['contact'][i]['y'],5,255,255,0)
            if (tdata['contact'][i]['prediction']<3) {
              drawscaledcrosshair(imdata,width,height,tdata['contact'][i]['x'],tdata['contact'][i]['y'],Math.round(-40*(tdata['contact'][i]['prediction']-4)),0,0,255)
            }
            if (tdata['contact'][i]['searchmax']>20) {
              drawscaleddiagcrosshair(imdata,width,height,tdata['contact'][i]['x'],tdata['contact'][i]['y'],Math.round(tdata['contact'][i]['searchmax']/10),255,255,0)
            }
            
                
            /*drawcrosshair(imdata,data['track'][i]['x'],data['track'][i]['y'],Math.round(data['track'][i]['searchmax']/10),blocksize,width,height,0,0,255);
            drawcrosshair(imdata,data['track'][i]['x'],data['track'][i]['y'],Math.round(-data['track'][i]['prediction']*10),blocksize,width,height,255,255,0);
            console.log(data['track'][i]['prediction'])
            drawcircle(imdata,data['track'][i]['x'],data['track'][i]['y'],5,blocksize,width,height,0,0,255);
            if (data['track'][i]['prediction']<$('input#detectthreshold').val()) {
                drawcircle(imdata,data['track'][i]['x'],data['track'][i]['y'],15,blocksize,width,height,255,255,0);
            }
        }*/
            
        }
    }
    // put the modified pixels back on the canvas
    ctx.putImageData(imgData,0,0);
    //console.log(canvas.width)
    if (image in tracking_data) {
        tdata = tracking_data[image]
        if (tdata['contact'].length==0) {
            ctx.font = "20px Courier";
                ctx.fillStyle = "yellow";
                ctx.fillText("Tracking failed on this frame",20,20);
        }
        
        for (var i=0;i<tdata['contact'].length;i++){
            td = tdata['contact'][i]
            if (td['prediction']>12) {continue;}
            ctx.font = "10px Courier";
            ctx.fillStyle = "yellow";
            x = 10+Math.round(width*(td['x'] - x1)/(x2-x1))
            y = Math.round(height*(td['y'] - y1)/(y2-y1))
            ctx.fillText(td['prediction'].toFixed(2)+":"+td['searchmax']+" "+td['centremax']+" "+td['mean']+" "+td['outersurround']+" "+td['innersurround']+" "+td['centre'],x,y);
        }
    }
    return "url('"+canvas.toDataURL()+"')";
}

$('input#scaletext').bind('input',function() {refreshimages();});
$('input#imagenum').bind('input',function() {image = parseInt($('input#imagenum').val()); refreshimages();});
//$('input#datetime').bind('input',function() {
$('button#goto').click(function(){
url = "http://127.0.0.1:"+$('input#port').val()+"/getindexoftime/"+cam+'/'+$('input#datetime').val();
$.getJSON(url, function(data) {console.log("ID:"+data); image=data; $('input#imagenum').val(data); refreshimages();}); 
});

$('button#detectrange').click(function(){
url = "http://127.0.0.1:"+$('input#port').val()+"/detectfromto/"+cam+'/'+image+'/'+(image+50);
$.getJSON(url, function(data) {}); 
});


cam_images = [0,0,0,0,0,0];
image = 0;
x1 = 0;
x2 = 2048;
y1 = 0;
y2 = 1536;
boxsize=300;

$('button#next').click(function(){
image=image+1; 
refreshtracking();
refreshimages(); drawDots(); })
$('button#last').click(function(){
image=image-1; 
refreshtracking();
refreshimages();})
$('button#reset').click(function(){
x1 = 0;
x2 = 2048;
y1 = 0;
y2 = 1536;
boxsize=300;
refreshimages();})
$('button#next10').click(function(){
image=image+10; 
x1 = 0;
x2 = 2048;
y1 = 0;
y2 = 1536;
boxsize=300;
refreshtracking();
refreshimages();})
$('button#last10').click(function(){
image=image-10; 
x1 = 0;
x2 = 2048;
y1 = 0;
y2 = 1536;
boxsize=300;
refreshtracking();
refreshimages();})



$(document).keypress(function(e) {
  if(e.which == 110) {$('button#next').trigger('click');}
  if(e.which == 78) {$('button#next10').trigger('click');}  
  if(e.which == 108) {$('button#last').trigger('click');}    
  if(e.which == 76) {$('button#last10').trigger('click');}
  if(e.which == 114) {$('button#reset').trigger('click');}  
  if(e.which == 113) {
    if (internalcam==0)
    { 
      $(('input:radio#internal1')).trigger('click');
    }
    else
    {
      $(('input:radio#internal0')).trigger('click');    
    }
  }  
  if(e.which == 97) {$(('input:radio#'+(cam+1))).trigger('click');}
  if(e.which == 122) {$(('input:radio#'+(cam-1))).trigger('click');}
  if(e.which == 100) {
        url = "http://127.0.0.1:"+$('input#port').val()+"/deleteallpos/"+cam+'/'+internalcam+'/'+image;
        $.getJSON(url, function(data) {}); 
        setTimeout(refreshimages, 300);  
  }
  if(e.which == 115) {
        url = "http://127.0.0.1:"+$('input#port').val()+"/stick/"+cam+'/'+internalcam+'/'+image+'/'+$('input#sticknum').val();
        $.getJSON(url, function(data) {}); 
        setTimeout(refreshimages, 300);  
  }  
  //if(e.which == 49) {$('input:radio#0').trigger('click');}
  //if(e.which == 50) {$('input:radio#1').trigger('click');}  
  //if(e.which == 51) {$('input:radio#2').trigger('click');}
  //if(e.which == 52) {$('input:radio#3').trigger('click');}   
  //97,122
  //alert(e.which);
});

internalcam = 0
$('input:radio#internal0').click(function(){
  internalcam = 0;
  image = cam_images[cam]
  refreshtracking();
  refreshimages();
});
$('input:radio#internal1').click(function(){
  internalcam = 1;
  image = cam_images[cam]
  refreshtracking();
  refreshimages();
});


cam = 0
$('input:radio#0').click(function(){
  cam = 0;
  image = cam_images[cam]
  refreshtracking();
  refreshimages();
});
$('input:radio#1').click(function(){
  cam = 1;
  image = cam_images[cam]
  refreshtracking();
  refreshimages();
});
$('input:radio#2').click(function(){
  cam = 2;
  image = cam_images[cam]
  refreshtracking();
  refreshimages();
});
$('input:radio#3').click(function(){
  cam = 3;
  image = cam_images[cam]
  refreshtracking();
  refreshimages();
});
$('input:radio#4').click(function(){
  cam = 4;
  image = cam_images[cam]
  refreshtracking();
  refreshimages();
});
$('input:radio#5').click(function(){
  cam = 5;
  image = cam_images[cam]
  refreshtracking();
  refreshimages();
});




function drawpixel(imdata,x,y,width,height) {
    pos = 4*(x+y*width)
    imdata[pos] = 0
    imdata[pos+1] = 0
    imdata[pos+2] = 0
}
function drawscaledpixel(imdata,x,y,width,height,r,g,b) {
    if ((x>x1) && (x<x2) && (y>y1) && (y<y2)) {
        x = Math.round(width*(x - x1)/(x2-x1))
        y = Math.round(height*(y - y1)/(y2-y1))
        
        pos = 4*(x+y*width)
        imdata[pos] = r
        imdata[pos+1] = g
        imdata[pos+2] = b
    }
}

function drawcrosshair(imdata,width,height) {
    x=Math.round(width/2);
    y=Math.round(height/2);
    for (xstep=x-10;xstep<x+10;xstep+=1) {
        drawpixel(imdata,xstep,y,width,height)
    }
    for (ystep=y-10;ystep<y+10;ystep+=1) {
        drawpixel(imdata,x,ystep,width,height)
    }

}

function drawscaledcrosshair(imdata,width,height,x,y,size,r,g,b) {
    if (size<0) {return;}
    size = Math.round(size)+5
    for (step=-size;step<+size;step+=1) {
        if (Math.abs(step)<5) {continue;}
        drawscaledpixel(imdata,x,y+step,width,height,r,g,b)
        drawscaledpixel(imdata,x+step,y,width,height,r,g,b)
    }

}

function drawscaleddiagcrosshair(imdata,width,height,x,y,size,r,g,b) {
    if (size<0) {return;}
    size = Math.round(size)+5
    for (step=-size;step<+size;step+=1) {
       if (Math.abs(step)<5) {continue;}
        drawscaledpixel(imdata,x+step,y+step,width,height,r,g,b)
        drawscaledpixel(imdata,x-step,y+step,width,height,r,g,b)
    }

}



$('button.refreshimages').click(function(){refreshimages();});
//$('#image2').mousemove(function( event ) {
//  var msg = "Handler for .mousemove() called at ";
//  msg += event.pageX + ", " + event.pageY;
//  $( "#log" ).append( "<div>" + msg + "</div>" );
//});

shifted = false
controlpressed = false
$(document).on('keyup keydown', function(e){shifted = e.shiftKey} );
$(document).on('keyup keydown', function(e){controlpressed = e.ctrlKey} );
    
$('#image2').mousedown(function(e){
    if (event.which==2) {
        if (shifted) {confidence=50;} else {confidence=100;}   
        label = "none";     
        if (controlpressed) {label = prompt("Enter label", "none");}
        console.log("SAVING:"+chosenloc[0]+"/"+chosenloc[1]);
        url = "http://127.0.0.1:"+$('input#port').val()+"/savepos/"+cam+'/'+internalcam+'/'+image+"/"+Math.round(chosenloc[0])+"/"+Math.round(chosenloc[1])+"/"+confidence+"/"+label;
        $.getJSON(url, function(data) {}); 
        //console.log("!"+chosenloc[0]+" "+chosenloc[1]);
        //refreshimages();
        setTimeout(refreshimages, 100)
    }
});



$('#image2').click(function(e){
    var posX = $(this).offset().left, posY = $(this).offset().top;
    centrex = (e.pageX - posX);
    centrey = (e.pageY - posY);
    centrex = x1+(x2-x1)*centrex/1024;
    centrey = y1+(y2-y1)*centrey/768;

    if (shifted) {
        landmarkname = prompt("Enter landmark name (e.g. m03_top, nestfrontleft)", "");
        coords = prompt("Enter coords (e.g. 0,2,3.4 or nest, leave as 'skip' to retain current coords)", "skip");
        // /savelm/<string:camst>/<int:x>/<int:y>/<string:lmname>')
        url = "http://127.0.0.1:"+$('input#port').val()+"/savelm/"+cam+'/'+internalcam+'/'+Math.round(centrex)+"/"+Math.round(centrey)+"/"+landmarkname+"/"+coords;
        $.getJSON(url, function(data) {}); 
        return;
    }

    $('span#loc').text(Math.round(centrex) + " " + Math.round(centrey))
    boxsize = boxsize * 0.8; // / 2;
    x1 = -1
    while ((x1<0) | (y1<0) | (x2>2047) | (y2>1535)) {
        x1 = centrex-boxsize;
        x2 = centrex+boxsize;
        y1 = centrey-boxsize/1.3333333;
        y2 = centrey+boxsize/1.3333333;
        //console.log([x1,x2,y1,y2,boxsize])
        if (x1<0) {boxsize = boxsize + x1 - 1; continue;}
        if (y1<0) {boxsize = boxsize + y1*1.3333333 - 1; continue;}
        if (x2>2047) {boxsize=boxsize + (2047-x2) - 1; continue;}
        if (y2>1535) {boxsize = boxsize + (1535-y2)*1.3333333 - 1; continue}
    }
    refreshimages();
});
currentimage = null
positions = null


function drawDots() {
  context.clearRect(0, 0, canvasWidth, canvasHeight)
  context.beginPath();
  
  scale = currentimage['photo'].length/768;
  //console.log(currentimage['photo'][Math.round(dot.y*scale)][Math.round(dot.x*scale)]);//[dot.x,dot.y]);  
  brightestv = 0;
  brightloc = null;
  box = 10;
  //console.log(dot.x+" "+dot.y);
  //console.log(currentimage['photo'].length);
  if (dot.y*scale+box+2>currentimage['photo'].length) {dot.y = (currentimage['photo'].length-box-2)/scale;}
  if (dot.y*scale-box-2<0) {dot.y = (box+2)/scale;}
  for( var i = Math.round(dot.x*scale-box); i < dot.x*scale+box; i+=1 ){
    for( var j = Math.round(dot.y*scale-box); j < dot.y*scale+box; j+=1 ){
      if (currentimage['photo'][j][i]>brightestv) {
        brightestv = currentimage['photo'][j][i];
        brightloc = [i,j];
      }
    }
  }

  chosenloc = [x1+(x2-x1)*brightloc[0]/1024/scale, y1+(y2-y1)*brightloc[1]/768/scale];

  
  context.beginPath();
  context.arc(1+brightloc[0]/scale,1+brightloc[1]/scale, 5, 0, 2 * Math.PI, false);
  context.strokeStyle = '#ffff00';
  context.stroke();
  
  
  console.log(chosenloc);
  console.log("---");
  for (var i = 0; i<positions.length; i+=1) {
    console.log('--->');
    position = positions[i]
    context.beginPath();
    pos = []
    console.log(position);
    console.log(x1+' '+x2+' '+y1+' '+y2);
    pos['x'] = 1024*(position['x']-x1)/(x2-x1);
    pos['y'] = 768*(position['y']-y1)/(y2-y1);
    
    console.log(position['confidence']);
    console.log("SCALE: "+scale);
    if (position['confidence']>75) {
      context.arc(2+pos['x'],1+pos['y'], 28, 0, 2 * Math.PI, false);
      context.strokeStyle = '#00ff00';
      context.stroke(); 
    }
    context.arc(2+pos['x'],1+pos['y'], 25, 0, 2 * Math.PI, false);
    context.strokeStyle = '#00ff00';
    context.stroke(); 
    
  }
}

$('input#maxval').bind('input',function() {refreshimages();});
function refreshimages(){
    cam_images[cam]=image;
    $('input#imagenum').val(image);
    url = "http://127.0.0.1:"+$('input#port').val()+"/filename/"+cam+'/'+internalcam+'/'+image;
    $.getJSON(url, function(data) {$('span#filename').text(data); });  

    url = "http://127.0.0.1:"+$('input#port').val()+"/getimage/"+cam+"/"+internalcam+'/'+image+"/"+Math.round(x1)+"/"+Math.round(y1)+"/"+Math.round(x2)+"/"+Math.round(y2);
    $.getJSON(url, function(data) {$('#image').css("background-image",convertJSONtoImageURL(data,true)); currentimage=data; });  
    
   // await sleep(200);
    url = "http://127.0.0.1:"+$('input#port').val()+"/loadpos/"+cam+'/'+internalcam+'/'+image;
    $.getJSON(url, function(data) {positions = data; console.log(url); console.log(positions); drawDots();});  
    //
}


tracking_data = {}
function refreshtracking(){
    if (document.getElementById('track').checked) {
        url = "http://127.0.0.1:"+$('input#port').val()+"/detect/"+cam+'/'+image;
        $.getJSON(url, (function(imagen) {return function(data) {tracking_data[imagen] = data; refreshimages();}}(image)));
    }
}
refreshtracking();
refreshimages();


var dot = { x: 50, y: 50, radius: 25 };
$('canvas#image2').mousemove(function( event ) {
  dot.x = event.offsetX;
  dot.y = event.offsetY;
  
  drawDots();
  
  x = x1+(x2-x1)*dot.x/1024
  y = y1+(y2-y1)*dot.y/768
  $('span#locationstring').text(Math.round(x)+" "+Math.round(y)+" ("+Math.round(chosenloc[0])+" "+Math.round(chosenloc[1])+")")
});
//////////////
//$(document).ready(function(){
// Setup the canvas element.
var canvas = $('canvas#image2');
var context = canvas[0].getContext('2d');
var canvasWidth = canvas.width();
var canvasHeight = canvas.height();
canvas.attr({height: canvasHeight, width: canvasWidth});

// Set the number of frames we want to run.
var frames = 150;

// We have a currentFrame reference which essentially tracks our place in time.
var currentFrame = 0;

// Set and create our dot.
chosenloc = [0,0];



setTimeout(refreshimages, 100);  
setTimeout(drawDots, 200);  
