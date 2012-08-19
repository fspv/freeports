function addEvent(elem, evType, fn) {
    if (elem.addEventListener) {
        elem.addEventListener(evType, fn, false);
    }
    else if (elem.attachEvent) {
        elem.attachEvent('on' + evType, fn)
    }
    else {
        elem['on' + evType] = fn
    }
}
function sliderHandler(pos, slider) {
    document.getElementById("approxMonth").innerHTML = "~" + Math.round(pos/30-pos%30/30) + " months";
}
function initSlider() {
    var sliderDiv = document.getElementById("sliderSliderContainer");
    var period = document.getElementById("sliderInput").value;
    createSlider(sliderDiv.getElementWidth(),period);
};
Element.prototype.getElementWidth = function() {
    if (typeof this.clip !== "undefined") {
       return this.clip.width;
    } else {
      if (this.style.pixelWidth) {
         return this.style.pixelWidth;
      } else {
         return this.offsetWidth;
      }
   }
};
createSlider = function(width,period) {
    var slider = new dhtmlxSlider("sliderSliderContainer",width);
    slider.setMin(1);
    slider.setMax(365);
    slider.setValue(period);
    slider.setSkin('dhx_skyblue');
    slider.linkTo('sliderInput');
    slider.attachEvent("onChange", sliderHandler);
    slider.init();
};
addEvent(window,"load",initSlider);
