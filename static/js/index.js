panel = document.getElementById("panel");
close = document.getElementById("close");
open = document.getElementById("open");
inpt = document.getElementById("inputTID"); inpt.value = "";
inptName = document.getElementById("inputName"); inptName.value = "";
good = document.getElementById("good");
bad = document.getElementById("bad");
check = document.getElementById("check"); check.checked = false;
update = document.getElementById("update");
table = document.getElementById("table");
tablePrefix = "<tr><th></th><th>п/п</th><th>Наименование</th><th>ИНН</th><th>Общее название</th></tr>";
next = document.getElementById("next");
prev = document.getElementById("prev");
summary = document.getElementById("summary");
form = document.getElementById("form");

let pageSize = 10;
let curPage = 1;
let dataLength = 0;
let currentlyChecked = 0;

let checkedIDS = [];

function send() {
  form.submit();
}

function processCheck(el) {
  if (el.checked) {
    currentlyChecked++;
    checkedIDS.push(el.getAttribute("checkID"));
  } else {
    currentlyChecked--;
    checkedIDS.splice(checkedIDS.indexOf(el.getAttribute("")));
  }
  console.log(checkedIDS);

  if (currentlyChecked > 0) {
    summary.innerHTML = "Скачать отчет (" + currentlyChecked + ")";
  } else {
    summary.innerHTML = "Скачать полный отчет";
  }
}

function init() {
  fetchContent(curPage);
}

function renderTable(content) {
  let result = tablePrefix;
  let cont = content.filter((row, index) => {
        let start = (curPage-1)*pageSize;
        let end =curPage*pageSize;
        if(index >= start && index < end) return true;
  });
  for (let i=0;i<cont.length;++i) {
    let c = cont[i];
    if (checkedIDS.includes(c.id.toString()))
    {
      result += `<tr>
       <td><input type='checkbox' name='${c.id}' checkID='${c.id}' checked onchange='processCheck(this)'></td>
       <td>${i+1+curPage * pageSize}</td>
       <td>${c.shortName}</td>
       <td><a class='anim' href='/dashboard/${c.TID}'>${c.TID}</a></td>
       <td>${c.name}</td>
       </tr>`;
    } else {
      result += `<tr>
       <td><input type='checkbox' name='${c.id}' checkID='${c.id}' onchange='processCheck(this)'></td>
       <td>${i+1+(curPage-1) * pageSize}</td>
       <td>${c.shortName}</td>
       <td><a class='anim' href='/dashboard/${c.TID}'>${c.TID}</a></td>
       <td>${c.name}</td>
       </tr>`;
    }
  }
  table.innerHTML = result;
}

function prevPage(ev) {
  ev.preventDefault();
  if(curPage > 1) curPage--;
  fetchContent(curPage);
}

function nextPage(ev) {
  ev.preventDefault();
  if((curPage * pageSize) < dataLength) curPage++;
  fetchContent(curPage);
}

function fetchContent(page) {
  let url = window.location.origin + '/table/' + page;
  fetch(url).then(function (responce){
    return responce.json();
  }).then(function (r){
    dataLength = r["dataLength"];
    pageSize = r["pageSize"];
    renderTable(r["data"]);
  })
}

document.addEventListener("DOMContentLoaded", init, false);
next.addEventListener("click", nextPage, false);
prev.addEventListener("click", prevPage, false);

// left: 37, up: 38, right: 39, down: 40,
// spacebar: 32, pageup: 33, pagedown: 34, end: 35, home: 36
var keys = {37: 1, 38: 1, 39: 1, 40: 1};

function preventDefault(e) {
  e.preventDefault();
}

function preventDefaultForScrollKeys(e) {
  if (keys[e.keyCode]) {
    preventDefault(e);
    return false;
  }
}

// modern Chrome requires { passive: false } when adding event
var supportsPassive = false;
try {
  window.addEventListener("test", null, Object.defineProperty({}, 'passive', {
    get: function () { supportsPassive = true; } 
  }));
} catch(e) {}

var wheelOpt = supportsPassive ? { passive: false } : false;
var wheelEvent = 'onwheel' in document.createElement('div') ? 'wheel' : 'mousewheel';

// call this to Disable
function disableScroll() {
  window.addEventListener('DOMMouseScroll', preventDefault, false); // older FF
  window.addEventListener(wheelEvent, preventDefault, wheelOpt); // modern desktop
  window.addEventListener('touchmove', preventDefault, wheelOpt); // mobile
  window.addEventListener('keydown', preventDefaultForScrollKeys, false);
}

// call this to Enable
function enableScroll() {
  window.removeEventListener('DOMMouseScroll', preventDefault, false);
  window.removeEventListener(wheelEvent, preventDefault, wheelOpt); 
  window.removeEventListener('touchmove', preventDefault, wheelOpt);
  window.removeEventListener('keydown', preventDefaultForScrollKeys, false);
}

function checkTID(tid) {
  let url = window.location.origin + "/check/" + tid;
  fetch(url)
    .then(function(response) {
      return response.json();
    })
    .then(function(r) {
      console.log(r["result"]);
      if (r["result"] == true)
      {
        bad.style.display = "none";
        good.style.display = "block";
      } else {
        bad.style.display = "block";
        good.style.display = "none";
      }
    });
}

function updateDB() {
  update.setAttribute("disabled", "");
  let url = window.location.origin + '/update';
  fetch(url, {
    method: "POST",
    body: "",
    headers: {
      "Content-Type": "application/json"
    }
  }).then(function(responce){
    return responce.json();
  }).then(function(r){
    update.removeAttribute("disabled");
    alert("Процесс обновления запущен");
    panel.classList.remove("active");
    enableScroll();
  })
}

close.addEventListener("click", (ev) => {
  ev.preventDefault();
  panel.classList.remove("active");
  enableScroll();
});

document.body.addEventListener('keydown', function(e) {
  if (e.key == "Escape") {
    panel.classList.remove("active");
    enableScroll();
  }
});

update.addEventListener("click", (ev) => {
  ev.preventDefault();
  updateDB();
})

open.addEventListener("click", (ev) => {
  ev.preventDefault();
  panel.classList.add("active");
  disableScroll();
});

inpt.addEventListener("input", (ev) => {
  if (!ev.currentTarget.value) {
    bad.style.display = "none";
    good.style.display = "none";
    return;
  }

  checkTID(ev.currentTarget.value);
});

enableScroll();
