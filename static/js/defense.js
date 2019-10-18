
function close_showing() {
	var showing = document.getElementById("showing").value;
	if (showing) {
		document.getElementById(showing).style = "display: none;";
	}
}

var show_stats = function() {
	close_showing();
	document.getElementById(this.id+"_table").style = "display: flex;";
	document.getElementById("showing").value = this.id+"_table";
	window.scrollTo(0, 0);
}

function resetBtns() {
	var btns = document.getElementsByTagName("button");
	for (var i = 0; i < btns.length; ++i) {
		btns[i].className = "";
	}
}

var click_btn = function() {
	var by_team = "none;";
	var by_pos = "none;";
	close_showing();
	resetBtns();
	this.className = "active";
	if (this.innerText.indexOf("Team") >= 0) {
		by_team = "inline-table;";
	} else {
		by_pos = "inline-table;";
	}
	document.getElementById("ppg_by_team").style = "display:"+by_team;
	document.getElementById("ppg_by_pos").style = "display:"+by_pos;
}


var tds = document.getElementsByClassName("clickable");
for (var i = 0; i < tds.length; ++i) {
	tds[i].addEventListener("click", show_stats, false);
}


var btns = document.getElementsByTagName("button");
for (var i = 0; i < btns.length; ++i) {
	btns[i].addEventListener("click", click_btn, false);
}