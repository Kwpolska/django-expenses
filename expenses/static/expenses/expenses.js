!function(e){var t={};function n(a){if(t[a])return t[a].exports;var r=t[a]={i:a,l:!1,exports:{}};return e[a].call(r.exports,r,r.exports,n),r.l=!0,r.exports}n.m=e,n.c=t,n.d=function(e,t,a){n.o(e,t)||Object.defineProperty(e,t,{enumerable:!0,get:a})},n.r=function(e){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})},n.t=function(e,t){if(1&t&&(e=n(e)),8&t)return e;if(4&t&&"object"==typeof e&&e&&e.__esModule)return e;var a=Object.create(null);if(n.r(a),Object.defineProperty(a,"default",{enumerable:!0,value:e}),2&t&&"string"!=typeof e)for(var r in e)n.d(a,r,function(t){return e[t]}.bind(null,r));return a},n.n=function(e){var t=e&&e.__esModule?function(){return e.default}:function(){return e};return n.d(t,"a",t),t},n.o=function(e,t){return Object.prototype.hasOwnProperty.call(e,t)},n.p="",n(n.s=2)}([function(e,t,n){"use strict";t.__esModule=!0,t.getNewAIDForSelector=function(e){var t=document.querySelector(e),n=parseInt(t.dataset.last_aid)+1;return t.dataset.last_aid=n.toString(),n},t.getTrForEvent=function(e){return e.target.closest("tr")},t.formatMoney=function e(t){return isNaN(t)?e(0):new Intl.NumberFormat(_expConfig_.currencyLocale.replace("_","-"),{style:"currency",currency:_expConfig_.currencyCode}).format(t)}},function(e,t,n){"use strict";
/*!
 * Expenses AutoComplete
 * Copyright © 2018, Chris Warrick. All rights reserved. License: 3-clause BSD.
 */t.__esModule=!0,t.default=function(e,t,n,a,r,l,o){if("string"==typeof e&&(e=document.querySelector(e)),void 0===a&&(a=1),null!==e&&void 0!=e){var s=document.createElement("datalist");null!==t&&void 0!==t||(t=e.name);var d="acdl_"+t.replace(".","");s.id=d,e.setAttribute("list",d),e.nextSibling?e.parentElement.insertBefore(s,e.nextSibling):e.parentElement.appendChild(s),0===a&&i(),e.addEventListener("input",i)}function i(t){var d;d="string"!=typeof n?n():n,s.innerHTML="";var i=e.value;"off"!==e.dataset.autocomplete&&(i.trim().length<a||(void 0!==l&&i.startsWith(l)?o(i):(-1!==d.indexOf("?")?d+="&q="+encodeURIComponent(i):d+="?q="+encodeURIComponent(i),fetch(d).then(function(e){return e.json()}).then(function(e){1===e.length&&e[0]===i||e.forEach(function(e){var t=document.createElement("option");t.value=void 0!==r?r(e):e,s.appendChild(t)})}))))}}},function(e,t,n){"use strict";t.__esModule=!0;
/*!
 * Expenses Scripting Enhancements
 * Copyright © 2018, Chris Warrick. All rights reserved. License: 3-clause BSD.
 */
var a=n(3),r=n(4),l=n(5),o=n(1);document.addEventListener("DOMContentLoaded",function(){if(o.default(".expenses-addform-vendor","vendor","/expenses/api/autocomplete/expense/vendor/"),o.default(".expenses-billaddform-vendor","vendor","/expenses/api/autocomplete/bill/vendor/"),o.default(".expenses-addform-description","description",function(){var e=document.querySelector(".expenses-addform-vendor").value.trim();return 0==e.length?"/expenses/api/autocomplete/expense/description/":"/expenses/api/autocomplete/expense/description/?vendor="+encodeURIComponent(e)}),null!==document.querySelector("#expenses-billtable-form")&&a.default(),null!==document.querySelector("#expenses-bulkcatedit-form")&&r.default(),null!==document.querySelector("#expenses-search-form")&&l.default(),-1!=navigator.userAgent.indexOf("ExpensesWebView")){var e=document.querySelector(".navbar-kw");e.classList.remove("static-top"),e.classList.add("fixed-top"),document.querySelector("body").style.paddingTop="50px"}},!1)},function(e,t,n){"use strict";
/*!
 * Expenses Bill Editor
 * Copyright © 2018, Chris Warrick. All rights reserved. License: 3-clause BSD.
 */t.__esModule=!0;var a=n(0),r=n(1),l=["expenses-billtable-serving","expenses-billtable-count","expenses-billtable-unitprice"];function o(e){s(a.getTrForEvent(e))}function s(e){var t=e.getElementsByClassName("expenses-billtable-unitprice")[0],n=e.getElementsByClassName("expenses-billtable-count")[0],r=t.getElementsByTagName("input")[0],l=n.getElementsByTagName("input")[0],o=e.getElementsByClassName("expenses-billtable-amount")[0],s=parseFloat(r.value)*parseFloat(l.value);o.innerText=a.formatMoney(s),o.dataset.value=s.toString(),d()}function d(){for(var e=document.querySelectorAll("td.expenses-billtable-amount"),t=0,n=0;n<e.length;n++){var r=parseFloat(e[n].dataset.value);isNaN(r)||(t+=r)}document.querySelector(".expenses-bill-total").innerText=a.formatMoney(t)}function i(){document.querySelector("#expenses-billtable-savechanges").disabled=!1}function c(e){var t={edit:{classNames:"btn-info expenses-billtable-btn-edit",title:a.gettext("Edit"),icon:"fa-edit",callback:b},undo:{classNames:"btn-warning expenses-billtable-btn-undo",title:a.gettext("Undo Changes"),icon:"fa-undo",callback:v},delete:{classNames:"btn-danger expenses-billtable-btn-delete",title:a.gettext("Delete"),icon:"fa-trash-alt",callback:f},accept:{classNames:"btn-success expenses-billtable-btn-accept",title:a.gettext("Accept"),icon:"fa-check",callback:x}};return function(e){var t=document.createElement("div");return t.className="btn-group",t.setAttribute("role","group"),t.setAttribute("aria-label","Item actions"),e.forEach(function(e){var n=document.createElement("button");n.type="button",n.className="btn "+e.classNames,n.title=e.title,n.innerHTML='<i class="fa fa-fw '+e.icon+'"></i>',n.addEventListener("click",e.callback),t.appendChild(n)}),t}(e.map(function(e){return t[e]}))}function u(){document.querySelector("#expenses-billtable-addrow .expenses-billtable-product input").focus()}function p(e){var t=document.querySelector("#expenses-billtable-addrow"),n=document.createElement("tr");n.classList.add("expenses-billtable-row","table-success");var r="a"+a.getNewAIDForSelector("#expenses-billtable-form");n.dataset.id=r,m(n,t,r,"add",["edit","delete"]),t.getElementsByClassName("expenses-billtable-amount")[0].innerText=a.formatMoney(0),document.querySelector("#expenses-billtable tbody").insertBefore(n,t),t.querySelectorAll("input").forEach(function(e){void 0!==e.dataset.default?e.value=e.dataset.default:e.value=""}),i(),u()}function m(e,t,n,r,o){e.dataset.type=r;for(var s=t.querySelectorAll("input"),d={},i=0;i<s.length;i++){var u=s[i];if(!u.reportValidity())throw new Error("Field "+u.name+" was invalid.");var p=document.createElement("td"),m=u.parentElement;m.dataset.hasOwnProperty("orig_text")&&(p.dataset.orig_text=m.dataset.orig_text,p.dataset.orig_value=m.dataset.orig_value),p.className=u.parentElement.className;var b=document.createElement("input");b.hidden=!0,b.value=u.value;var f=u.name;-1==f.indexOf("__")?b.name=n+"__"+f:b.name=f,p.appendChild(b);var v=u.value;"expenses-billtable-unitprice"==p.className&&(v=a.formatMoney(parseFloat(u.value)),p.dataset.value=u.value),p.appendChild(document.createTextNode(v)),e.appendChild(p),-1!=l.indexOf(p.className)?d[u.name]=parseFloat(u.value):d[u.name]=u.value}var x=t.getElementsByClassName("expenses-billtable-amount")[0],y=document.createElement("td");y.className="expenses-billtable-amount",y.innerText=x.innerText,y.dataset.value=x.dataset.value,x.dataset.hasOwnProperty("orig_text")&&(y.dataset.orig_text=x.dataset.orig_text,y.dataset.orig_value=x.dataset.orig_value),e.appendChild(y);var g=document.createElement("td");g.className="expenses-billtable-actions",g.innerHTML="",g.appendChild(c(o)),e.appendChild(g)}function b(e){for(var t=a.getTrForEvent(e),n=document.querySelector("#expenses-billtable-addrow"),r=0;r<t.children.length;r++){var l=t.children[r];if("expenses-billtable-actions"!=l.className){var s=l.getElementsByTagName("input"),d="";d=s.length>0?s[0].value:l.dataset.value?l.dataset.value:l.innerText.trim(),l.dataset.hasOwnProperty("orig_text")||(l.dataset.orig_text=l.innerText.trim(),l.dataset.orig_value=d.trim());var u=n.querySelector("."+l.className+" input");if(null!==u){var p=u.cloneNode(),m=p.name;p.value=d,p.name=t.dataset.id+"__"+m,"count"!=m&&"unit_price"!=m||p.addEventListener("input",o),p.addEventListener("keypress",E),l.innerHTML="",l.appendChild(p)}}else l.innerHTML="",l.appendChild(c(["accept","undo"]))}i(),e.preventDefault()}function f(e){var t=a.getTrForEvent(e),n=t.dataset.id;if("add"!==t.dataset.type){var r=document.querySelector("#expenses-billtable-deletions"),l=document.createElement("input");l.hidden=!0,l.name="d__"+n,r.appendChild(l)}t.remove(),d(),i(),e.preventDefault()}function v(e){var t=a.getTrForEvent(e);t.classList.remove("table-info"),t.querySelectorAll("td").forEach(function(e){e.dataset.hasOwnProperty("orig_text")&&(e.innerText=e.dataset.orig_text,e.dataset.value=e.dataset.orig_value),"expenses-billtable-actions"==e.className&&(e.innerHTML="",e.appendChild(c(["edit","delete"])))}),d(),e.preventDefault()}function x(e){y(a.getTrForEvent(e))}function y(e){var t=e.dataset.id,n=document.createElement("tr");n.classList.add("expenses-billtable-row","table-info"),n.dataset.id=t,m(n,e,t,function(e){return"a"==e.charAt(0)}(t)?"add":"edit",["edit","undo","delete"]),e.parentElement.replaceChild(n,e)}function g(){var e=document.querySelector("#expenses-billtable-addrow").querySelectorAll("input");e.forEach(function(e){return e.disabled=!0});try{document.querySelectorAll(".expenses-billtable-btn-accept").forEach(function(e){return y(e.closest("tr"))}),document.querySelector("#expenses-billtable-form").submit()}catch(t){e.forEach(function(e){return e.disabled=!1}),event.preventDefault()}}function E(e){if(13==e.keyCode){if(e.metaKey||e.ctrlKey)g();else{var t=a.getTrForEvent(e);"expenses-billtable-addrow"===t.id?p():y(t)}return!1}}t.default=function(){var e=document.querySelector("#expenses-billtable-btn-add");e.type="button",e.addEventListener("click",p),document.querySelectorAll(".expenses-billtable-btn-edit").forEach(function(e){return e.addEventListener("click",b)}),document.querySelectorAll(".expenses-billtable-btn-delete").forEach(function(e){return e.addEventListener("click",f)}),document.querySelector("#expenses-billtable-addrow .expenses-billtable-unitprice input").addEventListener("input",o),document.querySelector("#expenses-billtable-addrow .expenses-billtable-count input").addEventListener("input",o),document.querySelector("#expenses-billtable-addrow .expenses-billtable-amount").innerText=a.formatMoney(0),document.querySelectorAll("#expenses-billtable-addrow input").forEach(function(e){return e.addEventListener("keydown",E)}),document.querySelector("#expenses-billtable-savechanges").addEventListener("click",g);var t=document.querySelector("#expenses-billtable-form");t.action="",t.dataset.last_aid="0";var n=document.querySelector("#expenses-billtable-addrow .expenses-billtable-product input");r.default(n,null,function(){var e=document.querySelector("#expenses-bill-meta-vendor").innerText;return"/expenses/api/autocomplete/bill/item/?vendor="+encodeURIComponent(e)},3,function(e){var t=e;return"✨ "+t.product+" ⚖️"+t.serving+" 💶"+t.unit_price},"✨",function(e){var t=document.querySelector("#expenses-billtable-addrow"),a=/✨ (.*?) ⚖️(.*?) 💶(.*)/.exec(e),r={product:a[1],serving:a[2],unitprice:a[3]};for(var l in n.dataset.autocomplete="off",r)t.querySelector(".expenses-billtable-"+l+" input").value=r[l];n.dataset.autocomplete="on",s(t)}),u()}},function(e,t,n){"use strict";
/*!
 * Expenses Bulk Category Editor
 * Copyright © 2018, Chris Warrick. All rights reserved. License: 3-clause BSD.
 */t.__esModule=!0;var a=n(0);function r(e){var t=document.querySelector("#expenses-bulkcatedit-addrow"),n=document.createElement("tr");n.classList.add("table-success");for(var r="a"+a.getNewAIDForSelector("#expenses-bulkcatedit-form"),o=t.querySelectorAll("input"),d=0;d<o.length;d++){var i=o[d];if(!i.reportValidity())throw new Error("Field "+i.name+" was invalid.");var c=document.createElement("td");c.className=i.closest("td").className;var u=i.cloneNode();u.name=u.name.replace("add_","add_"+r+"_"),u.addEventListener("keypress",s),c.appendChild(u),n.appendChild(c)}var p=document.createElement("td");p.className="expenses-bulkcatedit-actions";var m=document.createElement("btn");m.className="btn btn-danger",m.innerHTML='<i class="fa fa-fw fa-trash-alt"></i>',m.addEventListener("click",l),p.appendChild(m),n.appendChild(p),document.querySelector("#expenses-bulkcatedit-form tbody").insertBefore(n,t),o.forEach(function(e){return e.value=""})}function l(e){a.getTrForEvent(e).remove()}function o(e){document.querySelectorAll("#expenses-bulkcatedit-addrow input").forEach(function(e){return e.disabled=!0});var t=document.querySelector("#expenses-bulkcatedit-form");t.reportValidity()?t.submit():document.querySelectorAll("#expenses-bulkcatedit-addrow input").forEach(function(e){return e.disabled=!1}),null!==e&&e.preventDefault()}function s(e){if(13==e.keyCode){if("expenses-bulkcatedit-addrow"===a.getTrForEvent(e).id){var t=document.querySelector("#expenses-bulkcatedit-addrow").querySelectorAll("input");""===t[0].value&&""===t[1].value?o(null):r()}else o(null);return!1}}t.default=function(){var e=document.querySelector("#expenses-bulkcatedit-btn-add");e.type="button",e.addEventListener("click",r),document.querySelectorAll("#expenses-bulkcatedit-addrow input").forEach(function(e){e.disabled=!1,e.addEventListener("keypress",s)}),document.querySelectorAll("#expenses-bulkcatedit-addrow input").forEach(function(e){return e.addEventListener("keypress",s)});var t=document.querySelector("#expenses-bulkcatedit-btn-save");t.type="button",t.addEventListener("click",o),document.querySelector("#expenses-bulkcatedit-form").dataset.last_aid="0"}},function(e,t,n){"use strict";
/*!
 * Expenses Search Form
 * Copyright © 2018, Chris Warrick. All rights reserved. License: 3-clause BSD.
 */function a(e){var t=document.querySelector("#search-date-start"),n=document.querySelector("#search-date-end");document.querySelector("#search-date-spec-any").checked?(t.disabled=!0,n.disabled=!0):(t.disabled=!1,n.disabled=!1)}function r(e){var t=document.querySelector("#search-include-expenses"),n=document.querySelector("#search-include-bills");document.querySelector("#search-for-billitems").checked?(t.disabled=!0,n.disabled=!0):(t.disabled=!1,n.disabled=!1)}t.__esModule=!0,t.default=function(){document.querySelector("#search-for-expenses").addEventListener("click",r),document.querySelector("#search-for-billitems").addEventListener("click",r),r(),document.querySelector("#search-date-spec-any").addEventListener("click",a),document.querySelector("#search-date-spec-between").addEventListener("click",a),a()}}]);