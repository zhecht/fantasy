
// GLOBALS
var settings = {};

function close_showing() {
	var showing = document.getElementById("showing").value;
	if (showing) {
		document.getElementById(showing).style = "display: none;";
	}
}

var close_table = function() {
	close_showing();
}

var change_scoring = function() {
	document.getElementById("darkened_back").style = "display: block;";
	document.getElementById("scoring").style = "display: flex;";
}

var show_stats = function() {
	close_showing();
	var suffix = "_table";
	var css = "flex;";
	if (window.innerWidth <= 420) {
		suffix = "_mobile_table";
		css = "inline-table;";		
	}
	document.getElementById(this.id+suffix).style = "display: "+css;
	document.getElementById("showing").value = this.id+suffix;
	window.scrollTo(0, 0);
}

var mobile_show_stats = function(e) {
	var is_show = this.innerText.indexOf("Show") >= 0;
	var txt = "Show";
	var css = "none;";
	if (is_show) {
		txt = "Hide";
		css = "table-cell;text-align:center;";
	}
	this.innerText = txt;
	document.getElementById(this.id+"_stats").style = "display:"+css;
	e.preventDefault();
	return false;
}

var hide_pos = function() {

	var pos = this.parentElement.id.split("_")[0];
	var tds = document.getElementsByClassName(pos+"_td");
	for (var i = 0; i < tds.length; ++i) {
		if (this.checked) {
			tds[i].style.display = "none";
		} else {
			tds[i].style.display = "table-cell";
		}
	}
}

function resetBtns(div_id) {
	var btns = document.getElementById(div_id).getElementsByTagName("button");
	for (var i = 0; i < btns.length; ++i) {
		btns[i].className = "";
	}
}

function resetBtnsWithEl(div) {
	var btns = div.getElementsByTagName("button");
	for (var i = 0; i < btns.length; ++i) {
		btns[i].className = "";
	}
}

var click_btn = function() {
	var by_team = "none;";
	var by_pos = "none;";
	close_showing();
	resetBtns("sort_div");
	this.className = "active";
	if (this.innerText.indexOf("Team") >= 0) {
		by_team = window.innerWidth <= 420 ? "block" : "inline-table;";
	} else {
		by_pos =  window.innerWidth <= 420 ? "block" : "inline-table;";
	}
	document.getElementById("ppg_by_team").style = "display:"+by_team;
	document.getElementById("ppg_by_pos").style = "display:"+by_pos;
}

var click_scoring_btn = function() {
	resetBtns(this.parentElement.id);
	this.className = "active";
	if (this.parentElement.id == "ppr") {
		val = parseFloat(this.id);
	} else {
		val = parseInt(this.innerText);
	}
	settings[this.parentElement.id] = val;
}

var select_setting = function() {
	if (this.parentElement.id == "ppr") {
		val = parseFloat(this.options[this.selectedIndex].innerText);
	} else {
		val = parseInt(this.options[this.selectedIndex].innerText);
	}
	settings[this.parentElement.id] = val;
}

var click_scoring_save_btn = function() {
	if (this.innerText == "Save") {
		var settings_string = JSON.stringify(settings);
		var xhttp = new XMLHttpRequest();
		xhttp.onreadystatechange = function() {
			if (this.readyState === 4 && this.status === 200) {
				var j = JSON.parse(this.responseText);
				localStorage.setItem("session_id", j["session_id"]);
				window.location.href = "/defense?session_id="+encodeURIComponent(j["session_id"]);
			}
		};
		var url = "/defense?settings="+encodeURI(settings_string);
		if (localStorage.getItem("session_id") != null) {
			url += "&session_id="+encodeURIComponent(localStorage.getItem("session_id"));
		}
		xhttp.open("POST", url);
		xhttp.send();
		//document.getElementById("scoring").style = "display: none;";
		document.getElementById("scoring_result").style = "display: flex;";
	} else {
		document.getElementById("darkened_back").style = "display: none;";
		document.getElementById("scoring").style = "display: none;";
	}
}

// if no session_id in url but in local storage, refresh with session
if (window.location.search.indexOf("session_id") == -1 && localStorage.getItem("session_id") != null) {
	window.location.href = "/defense?session_id="+encodeURIComponent(localStorage.getItem("session_id"));
}

if (window.innerWidth <= 420) {
	document.getElementById("ppg_by_team").style = "display: block;";
} else {
	document.getElementById("ppg_by_team").style = "display: inline-table;";
}

var tds = document.getElementsByClassName("clickable");
for (var i = 0; i < tds.length; ++i) {
	tds[i].addEventListener("click", show_stats, false);
}


var btns = document.getElementById("sort_div").getElementsByTagName("button");
for (var i = 0; i < btns.length; ++i) {
	btns[i].addEventListener("click", click_btn, false);
}

var btns = document.getElementById("ppr").getElementsByTagName("button");
for (var i = 0; i < btns.length; ++i) {
	btns[i].addEventListener("click", click_scoring_btn, false);
}

var btns = document.getElementById("save_div").getElementsByTagName("button");
for (var i = 0; i < btns.length; ++i) {
	btns[i].addEventListener("click", click_scoring_save_btn, false);
}

var btns = document.getElementById("main_scoring").getElementsByTagName("button");
for (var i = 0; i < btns.length; ++i) {
	btns[i].addEventListener("click", click_scoring_btn, false);
}

var btns = document.getElementsByTagName("select");
for (var i = 0; i < btns.length; ++i) {
	btns[i].addEventListener("change", select_setting, false);
}

var btns = document.getElementsByClassName("mobile_show_stats");
for (var i = 0; i < btns.length; ++i) {
	btns[i].addEventListener("click", mobile_show_stats, false);
}

var btns = document.getElementsByClassName("close_table");
for (var i = 0; i < btns.length; ++i) {
	btns[i].addEventListener("click", close_table, false);
}

var btns = document.getElementById("hide_div").getElementsByTagName("input");
for (var i = 0; i < btns.length; ++i) {
	btns[i].addEventListener("click", hide_pos, false);
}

var btns = document.getElementById("change_scoring").addEventListener("click", change_scoring, false);