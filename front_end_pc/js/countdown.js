$(function(){
    var oFuture = new Date(2018,2,14,23,0,0);
    var $hour = $('.hours'),$minute = $('.minutes'),$second = $('.seconds');

    setInterval(fnTimeLeft,1000)
    fnTimeLeft();
    function fnTimeLeft(){
        var oNow = new Date();
        var iTimeLeft = parseInt((oFuture-oNow)/1000);
        var iHours = parseInt(iTimeLeft/3600);
        var iMinutes = parseInt((iTimeLeft%3600)/60);
        var iSeconds = iTimeLeft%60;
        $hour.html(fnToDou(iHours));
        $minute.html(fnToDou(iMinutes));
        $second.html(fnToDou(iSeconds));
    }
    function fnToDou(n){
        if(n<10)
        {
            return '0'+n;
        }
        else{
            return n;
        }
    }
})