inpt = document.getElementById("search");
btn = document.getElementById("btn");
results = document.getElementById("results");

inpt.value = "";

function go(tid) {
}

inpt.addEventListener("input", () => {
  if (inpt.value == "")
  {
    while (results.firstChild) {
      results.removeChild(results.firstChild);
    }
    return;
  }
  url = window.location.origin = "/search/" + inpt.value;
  //url = "http://localhost:4221/search/" + inpt.value;
  fetch(url)
    .then(function(response) {
      return response.json();
    })
    .then(function(r) {
      while (results.firstChild) {
        results.removeChild(results.firstChild);
      } 
      for (let i=0;i < r.length; ++i)
      {
        let el = document.createElement("div");
        el.classList.add("res");
        //el.innerHTML = "<p class='name'><b>" 
        //  + r[i]["shortName"] + "</b></p> - <p class='tid'>" + r[i]["TID"] + "</p>";
        let url = window.location.origin + "/dashboard/" + r[i]["TID"];
        el.innerHTML = "<a class='res' href='" + url + "'><p class='name'><b>" 
          + r[i]["shortName"] + "</b></p> - <p class='tid'>" + r[i]["TID"] + "</p>";
        results.appendChild(el);
      }
    });
})
