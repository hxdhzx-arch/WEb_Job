/* ══════════════════════════════════════
   script.js — Pro Resume Builder (14 Templates)
   ══════════════════════════════════════ */

// ══ 1. FONTS ══
var FONT_LIST=[
{key:"notosans",name:"思源黑体 Noto Sans",css:"'Noto Sans SC',sans-serif"},
{key:"roboto",name:"Roboto",css:"'Roboto',sans-serif"},
{key:"lato",name:"Lato",css:"'Lato',sans-serif"},
{key:"montserrat",name:"Montserrat",css:"'Montserrat',sans-serif"},
{key:"merriweather",name:"Merriweather",css:"'Merriweather',serif"},
{key:"lora",name:"Lora",css:"'Lora',serif"},
{key:"notoserif",name:"思源宋体 Noto Serif",css:"'Noto Serif SC',serif"}
];
function fontCSS(key){for(var i=0;i<FONT_LIST.length;i++)if(FONT_LIST[i].key===key)return FONT_LIST[i].css;return FONT_LIST[0].css;}

// ══ 2. TEMPLATE REGISTRY ══
var TPL_REG=[
{id:1,name:"标准",cat:"campus",color:"#e8eaed"},{id:2,name:"清新",cat:"campus",color:"#dbeafe"},
{id:3,name:"严谨",cat:"campus",color:"#f3f4f6"},
{id:4,name:"投行",cat:"elite",color:"#fef3c7"},{id:5,name:"咨询",cat:"elite",color:"#fce7f3"},
{id:6,name:"精英",cat:"elite",color:"#ede9fe"},
{id:7,name:"科技蓝",cat:"tech",color:"#1e3a5f"},{id:8,name:"墨绿",cat:"tech",color:"#1b4332"},
{id:9,name:"深灰",cat:"tech",color:"#1f2937"},
{id:10,name:"创意橙",cat:"creative",color:"#ff6b35"},{id:11,name:"品牌紫",cat:"creative",color:"#7c3aed"},
{id:12,name:"活力绿",cat:"creative",color:"#10b981"},
{id:13,name:"科研A",cat:"academic",color:"#f5f5f5"},{id:14,name:"科研B",cat:"academic",color:"#eef2ff"}
];

// ══ 3. STATE ══
var resumeData={basic:{name:"",age:"",phone:"",email:"",city:"",years:"",photo:""},intent:{job:"",salary:""},education:[{school:"",major:"",degree:"",time:""}],work:[{company:"",title:"",time:"",duties:[""]}],skills:"",intro:"",certs:""};
var TC={templateId:1,fontKey:"notosans",colors:{primary:"#2D5AF0",secondary:"#475569",text:"#1C1C1E"},typography:{nameSize:26,nameWeight:800,titleSize:15,baseSize:13,lineHeight:1.55,itemSpacing:18,avatarSize:90},layout:{avatarPosition:"right",avatarShape:"rounded",nameAlign:"center",contactStyle:"pipe"},modules:{order:["intro","work","education","skills","certs"],visible:{intro:true,work:true,education:true,skills:true,certs:true}},titles:{basic:"基本信息",intent:"求职意向",education:"教育背景",work:"工作经历",skills:"技能特长",intro:"自我评价",certs:"证书"}};
var customMode=false;
var SAVE_KEY="resumeAI_data",SAVE_TC="resumeAI_tc";

// Template-specific optimal defaults
var _campusDef={fontKey:"notosans",colors:{primary:"#1C1C1E",secondary:"#475569",text:"#1C1C1E"},typography:{nameSize:26,nameWeight:800,titleSize:15,baseSize:13,lineHeight:1.55,itemSpacing:18,avatarSize:90},layout:{avatarPosition:"right",avatarShape:"rounded",nameAlign:"center",contactStyle:"pipe"},modules:{order:["intro","work","education","skills","certs"],visible:{intro:true,work:true,education:true,skills:true,certs:true}}};
var _eliteDef={fontKey:"merriweather",colors:{primary:"#1C1C1E",secondary:"#475569",text:"#1C1C1E"},typography:{nameSize:24,nameWeight:700,titleSize:14,baseSize:12.5,lineHeight:1.5,itemSpacing:16,avatarSize:80},layout:{avatarPosition:"hidden",avatarShape:"square",nameAlign:"center",contactStyle:"pipe"},modules:{order:["intro","work","education","skills","certs"],visible:{intro:true,work:true,education:true,skills:true,certs:true}}};
var _techDef={fontKey:"roboto",colors:{primary:"#60A5FA",secondary:"#94A3B8",text:"#1C1C1E"},typography:{nameSize:22,nameWeight:700,titleSize:15,baseSize:13,lineHeight:1.55,itemSpacing:18,avatarSize:88},layout:{avatarPosition:"right",avatarShape:"circle",nameAlign:"center",contactStyle:"pipe"},modules:{order:["intro","work","education","skills","certs"],visible:{intro:true,work:true,education:true,skills:true,certs:true}}};
var _creativeDef={fontKey:"montserrat",colors:{primary:"#fff",secondary:"#64748B",text:"#1E293B"},typography:{nameSize:28,nameWeight:800,titleSize:16,baseSize:13,lineHeight:1.6,itemSpacing:20,avatarSize:80},layout:{avatarPosition:"right",avatarShape:"circle",nameAlign:"left",contactStyle:"pipe"},modules:{order:["intro","work","education","skills","certs"],visible:{intro:true,work:true,education:true,skills:true,certs:true}}};
var _academicDef={fontKey:"notoserif",colors:{primary:"#1E40AF",secondary:"#475569",text:"#1C1C1E"},typography:{nameSize:24,nameWeight:700,titleSize:14,baseSize:13,lineHeight:1.65,itemSpacing:20,avatarSize:80},layout:{avatarPosition:"right",avatarShape:"square",nameAlign:"left",contactStyle:"twoLine"},modules:{order:["intro","education","work","skills","certs"],visible:{intro:true,work:true,education:true,skills:true,certs:true}}};
var TEMPLATE_DEFAULTS={};
(function(){for(var i=1;i<=3;i++)TEMPLATE_DEFAULTS[i]=_campusDef;for(var i=4;i<=6;i++)TEMPLATE_DEFAULTS[i]=_eliteDef;for(var i=7;i<=9;i++)TEMPLATE_DEFAULTS[i]=_techDef;for(var i=10;i<=12;i++)TEMPLATE_DEFAULTS[i]=_creativeDef;for(var i=13;i<=14;i++)TEMPLATE_DEFAULTS[i]=_academicDef;})();

// ══ 4. Persistence ══
function saveToLocal(){try{localStorage.setItem(SAVE_KEY,JSON.stringify(resumeData));localStorage.setItem(SAVE_TC,JSON.stringify(TC));}catch(e){}}
function loadFromLocal(){try{var d=localStorage.getItem(SAVE_KEY);if(d){var p=JSON.parse(d);if(p.basic)resumeData=p;}var t=localStorage.getItem(SAVE_TC);if(t){var q=JSON.parse(t);if(q.typography)TC=q;}}catch(e){}}
function exportJSON(){var b=new Blob([JSON.stringify({resumeData:resumeData,TC:TC},null,2)],{type:"application/json"});var a=document.createElement("a");a.href=URL.createObjectURL(b);a.download="resume_"+new Date().toISOString().slice(0,10)+".json";a.click();}
function importJSON(input){if(!input.files||!input.files[0])return;var r=new FileReader();r.onload=function(e){try{var j=JSON.parse(e.target.result);if(j.resumeData)resumeData=j.resumeData;if(j.TC)TC=j.TC;saveToLocal();syncFormFromState();syncControlsFromTC();renderWorkExperience();renderEducation();buildTplGrid();renderPreview();}catch(err){alert("格式错误");}};r.readAsText(input.files[0]);input.value="";}
function resetAll(){if(!confirm("清空所有？"))return;localStorage.removeItem(SAVE_KEY);localStorage.removeItem(SAVE_TC);location.reload();}

function clearAllDataAndExit(){
  if(!confirm("确定要清除所有简历数据并离开吗？\n\n此操作将永久删除浏览器中保存的所有简历内容，不可恢复。"))return;
  localStorage.removeItem(SAVE_KEY);
  localStorage.removeItem(SAVE_TC);
  localStorage.clear();
  window.location.href="/?cleared=1";
}

// ══ 5. Debounce ══
function debounce(fn,ms){var t;return function(){clearTimeout(t);var c=this,a=arguments;t=setTimeout(function(){fn.apply(c,a);},ms);};}
var liveRender=debounce(function(){renderPreview();saveToLocal();},80);
var liveRenderSlow=debounce(function(){renderPreview();saveToLocal();},150);

// ══ 6. State Ops ══
function addWorkEntry(){resumeData.work.push({company:"",title:"",time:"",duties:[""]});renderWorkExperience();liveRender();}
function removeWorkEntry(i){if(resumeData.work.length<=1)return;resumeData.work.splice(i,1);renderWorkExperience();liveRender();}
function addDuty(wi){resumeData.work[wi].duties.push("");renderWorkExperience();}
function removeDuty(wi,di){if(resumeData.work[wi].duties.length<=1)return;resumeData.work[wi].duties.splice(di,1);renderWorkExperience();liveRender();}
function addEducationEntry(){resumeData.education.push({school:"",major:"",degree:"",time:""});renderEducation();liveRender();}
function removeEducationEntry(i){if(resumeData.education.length<=1)return;resumeData.education.splice(i,1);renderEducation();liveRender();}

// ══ 7. DOM Renderers (Form) ══
function renderWorkExperience(){var c=document.getElementById("work-list");if(!c)return;var tpl=document.getElementById("tpl-work");c.innerHTML="";for(var i=0;i<resumeData.work.length;i++){var n=tpl.content.cloneNode(true),w=n.querySelector(".entry-card");w.setAttribute("data-index",i);n.querySelector(".entry-number").textContent="#"+(i+1);n.querySelector("[data-field=company]").value=resumeData.work[i].company;n.querySelector("[data-field=title]").value=resumeData.work[i].title;n.querySelector("[data-field=time]").value=resumeData.work[i].time;if(resumeData.work.length<=1){var db=n.querySelector(".btn-remove-entry");if(db)db.style.display="none";}var dc=n.querySelector(".duty-list"),dt=document.getElementById("tpl-duty");for(var j=0;j<resumeData.work[i].duties.length;j++){var dn=dt.content.cloneNode(true),dw=dn.querySelector(".duty-item");dw.setAttribute("data-duty-index",j);dn.querySelector("[data-field=duty]").value=resumeData.work[i].duties[j];if(resumeData.work[i].duties.length<=1){var rd=dn.querySelector(".btn-remove-duty");if(rd)rd.style.display="none";}dc.appendChild(dn);}c.appendChild(n);}}
function renderEducation(){var c=document.getElementById("edu-list");if(!c)return;var tpl=document.getElementById("tpl-edu");c.innerHTML="";for(var i=0;i<resumeData.education.length;i++){var n=tpl.content.cloneNode(true),w=n.querySelector(".entry-card");w.setAttribute("data-index",i);n.querySelector(".entry-number").textContent="#"+(i+1);n.querySelector("[data-field=school]").value=resumeData.education[i].school;n.querySelector("[data-field=major]").value=resumeData.education[i].major;n.querySelector("[data-field=degree]").value=resumeData.education[i].degree;n.querySelector("[data-field=time]").value=resumeData.education[i].time;if(resumeData.education.length<=1){var db=n.querySelector(".btn-remove-entry");if(db)db.style.display="none";}c.appendChild(n);}}

// ══ 8. Sync State → Form ══
function syncFormFromState(){var d=resumeData.basic,bf=document.getElementById("basic-form");if(bf){var fs=bf.querySelectorAll("[data-field]");for(var i=0;i<fs.length;i++){var f=fs[i].getAttribute("data-field");if(d[f]!==undefined)fs[i].value=d[f];}}var inf=document.getElementById("intent-form");if(inf){var is=inf.querySelectorAll("[data-field]");for(var i=0;i<is.length;i++){var f=is[i].getAttribute("data-field");if(resumeData.intent[f]!==undefined)is[i].value=resumeData.intent[f];}}var sk=document.getElementById("b-skills");if(sk)sk.value=resumeData.skills;var intro=document.getElementById("b-intro");if(intro)intro.value=resumeData.intro;var certs=document.getElementById("b-certs");if(certs)certs.value=resumeData.certs;if(resumeData.basic.photo){var pp=document.getElementById("photo-preview");if(pp)pp.innerHTML='<img src="'+resumeData.basic.photo+'">';}}

function syncControlsFromTC(){
  var T=TC.typography,C=TC.colors,L=TC.layout;
  if(!TC.modules)TC.modules={order:["intro","work","education","skills","certs"],visible:{intro:true,work:true,education:true,skills:true,certs:true}};
  if(!T.nameWeight)T.nameWeight=800;
  if(!L.avatarShape)L.avatarShape="rounded";
  if(!L.nameAlign)L.nameAlign="center";
  if(!L.contactStyle)L.contactStyle="pipe";
  function sv(id,v){var e=document.getElementById(id);if(e)e.value=v;}
  function st(id,v){var e=document.getElementById(id);if(e)e.textContent=v;}
  sv("ctrl-font",TC.fontKey);sv("ctrl-font-quick",TC.fontKey);
  sv("ctrl-name-size",T.nameSize);st("v-name",T.nameSize);
  sv("ctrl-name-weight",T.nameWeight);st("v-nw",T.nameWeight);
  sv("ctrl-title-size",T.titleSize);st("v-title",T.titleSize);
  sv("ctrl-base-size",T.baseSize);st("v-base",T.baseSize);
  sv("ctrl-size-quick",T.baseSize);st("qsize-val",T.baseSize);
  sv("ctrl-lh",T.lineHeight);st("v-lh",T.lineHeight);
  sv("ctrl-gap",T.itemSpacing);st("v-gap",T.itemSpacing);
  sv("ctrl-avatar-size",T.avatarSize||90);st("v-avatar",T.avatarSize||90);
  sv("ctrl-primary",C.primary);sv("ctrl-secondary",C.secondary);sv("ctrl-text",C.text);
  // Sync seg-btns for layout
  var syncSeg=function(key,val){var btns=document.querySelectorAll(".seg-btns");for(var i=0;i<btns.length;i++){var parent=btns[i].closest(".adv-row");if(!parent)continue;var label=parent.querySelector("label");if(!label)continue;var match=false;if(key==="nameAlign"&&label.textContent.indexOf("姓名对齐")>=0)match=true;if(key==="avatarPosition"&&label.textContent.indexOf("头像位置")>=0)match=true;if(key==="avatarShape"&&label.textContent.indexOf("头像形状")>=0)match=true;if(key==="contactStyle"&&label.textContent.indexOf("联系方式")>=0)match=true;if(match){var sb=btns[i].querySelectorAll(".seg-btn");for(var j=0;j<sb.length;j++){sb[j].classList.remove("active");if(sb[j].getAttribute("onclick")&&sb[j].getAttribute("onclick").indexOf("'"+val+"'")>=0)sb[j].classList.add("active");}}}};
  syncSeg("nameAlign",L.nameAlign);syncSeg("avatarPosition",L.avatarPosition);syncSeg("avatarShape",L.avatarShape);syncSeg("contactStyle",L.contactStyle);
  buildModuleOrderList();
}

var MOD_LABELS={intro:"个人简介",work:"工作经历",education:"教育背景",skills:"技能特长",certs:"证书资质"};
function buildModuleOrderList(){
  var list=document.getElementById("module-order-list");if(!list)return;
  if(!TC.modules)TC.modules={order:["intro","work","education","skills","certs"],visible:{intro:true,work:true,education:true,skills:true,certs:true}};
  list.innerHTML="";
  for(var i=0;i<TC.modules.order.length;i++){
    var key=TC.modules.order[i],vis=TC.modules.visible[key]!==false;
    var label=getTitle(key,MOD_LABELS[key]||key);
    var div=document.createElement("div");
    div.className="mod-order-item";div.setAttribute("draggable","true");div.setAttribute("data-mod",key);
    div.innerHTML='<span class="mod-drag">☰</span><span class="mod-label">'+label+'</span><label class="mod-toggle"><input type="checkbox" '+(vis?"checked":"")+' onchange="toggleModule(\''+key+'\',this.checked)"><span class="mt-slider"></span></label>';
    div.addEventListener("dragstart",onModDragStart);
    div.addEventListener("dragover",onModDragOver);
    div.addEventListener("drop",onModDrop);
    div.addEventListener("dragend",onModDragEnd);
    list.appendChild(div);
  }
}
function toggleModule(key,checked){TC.modules.visible[key]=checked;saveToLocal();renderPreview();}
var _dragItem=null;
function onModDragStart(e){_dragItem=this;this.classList.add("dragging");e.dataTransfer.effectAllowed="move";}
function onModDragOver(e){e.preventDefault();e.dataTransfer.dropEffect="move";var target=e.target.closest(".mod-order-item");if(target&&target!==_dragItem){var list=document.getElementById("module-order-list");var items=Array.from(list.children);var dragIdx=items.indexOf(_dragItem),targetIdx=items.indexOf(target);if(dragIdx<targetIdx)list.insertBefore(_dragItem,target.nextSibling);else list.insertBefore(_dragItem,target);}}
function onModDrop(e){e.preventDefault();}
function onModDragEnd(){if(_dragItem)_dragItem.classList.remove("dragging");_dragItem=null;var list=document.getElementById("module-order-list");var items=list.querySelectorAll(".mod-order-item");TC.modules.order=[];for(var i=0;i<items.length;i++)TC.modules.order.push(items[i].getAttribute("data-mod"));saveToLocal();renderPreview();}

// ══ 9. Event Delegation ══
function initEventDelegation(){var bf=document.getElementById("basic-form");if(bf)bf.addEventListener("input",function(e){var f=e.target.getAttribute("data-field");if(f){resumeData.basic[f]=e.target.value;liveRender();}});var inf=document.getElementById("intent-form");if(inf)inf.addEventListener("input",function(e){var f=e.target.getAttribute("data-field");if(f){resumeData.intent[f]=e.target.value;liveRender();}});var wl=document.getElementById("work-list");if(wl){wl.addEventListener("input",function(e){var card=e.target.closest(".entry-card");if(!card)return;var idx=parseInt(card.getAttribute("data-index")),f=e.target.getAttribute("data-field");if(f==="duty"){var di=e.target.closest(".duty-item");resumeData.work[idx].duties[parseInt(di.getAttribute("data-duty-index"))]=e.target.value;liveRender();}else if(f&&resumeData.work[idx]){resumeData.work[idx][f]=e.target.value;liveRender();}});wl.addEventListener("click",function(e){var btn=e.target.closest("button");if(!btn)return;var card=btn.closest(".entry-card");if(btn.classList.contains("btn-remove-entry")&&card)removeWorkEntry(parseInt(card.getAttribute("data-index")));else if(btn.classList.contains("btn-add-duty")&&card)addDuty(parseInt(card.getAttribute("data-index")));else if(btn.classList.contains("btn-remove-duty")&&card){var di=btn.closest(".duty-item");removeDuty(parseInt(card.getAttribute("data-index")),parseInt(di.getAttribute("data-duty-index")));}});}var el=document.getElementById("edu-list");if(el){el.addEventListener("input",function(e){var card=e.target.closest(".entry-card");if(!card)return;var idx=parseInt(card.getAttribute("data-index")),f=e.target.getAttribute("data-field");if(f&&resumeData.education[idx]){resumeData.education[idx][f]=e.target.value;liveRender();}});el.addEventListener("click",function(e){var btn=e.target.closest("button");if(btn&&btn.classList.contains("btn-remove-entry"))removeEducationEntry(parseInt(btn.closest(".entry-card").getAttribute("data-index")));});}var sk=document.getElementById("b-skills");if(sk)sk.addEventListener("input",function(){resumeData.skills=this.value;liveRenderSlow();});var intro=document.getElementById("b-intro");if(intro)intro.addEventListener("input",function(){resumeData.intro=this.value;liveRenderSlow();});var certs=document.getElementById("b-certs");if(certs)certs.addEventListener("input",function(){resumeData.certs=this.value;liveRender();});}

// ══ 10. Controls ══
function handlePhoto(input){if(input.files&&input.files[0]){var r=new FileReader();r.onload=function(e){resumeData.basic.photo=e.target.result;document.getElementById("photo-preview").innerHTML='<img src="'+e.target.result+'">';liveRender();};r.readAsDataURL(input.files[0]);}}

function selectTemplate(n){TC.templateId=n;if(!customMode){var def=TEMPLATE_DEFAULTS[n]||TEMPLATE_DEFAULTS[1];TC.fontKey=def.fontKey;TC.colors=JSON.parse(JSON.stringify(def.colors));TC.typography=JSON.parse(JSON.stringify(def.typography));TC.layout=JSON.parse(JSON.stringify(def.layout));TC.modules=JSON.parse(JSON.stringify(def.modules));syncControlsFromTC();}buildTplGrid();saveToLocal();renderPreview();}
function applyStyle(){
  var T=TC.typography,C=TC.colors;
  var gv=function(id){var e=document.getElementById(id);return e?e.value:null;};
  if(gv("ctrl-font"))TC.fontKey=gv("ctrl-font");
  if(gv("ctrl-name-size")){T.nameSize=parseInt(gv("ctrl-name-size"));var v=document.getElementById("v-name");if(v)v.textContent=T.nameSize;}
  if(gv("ctrl-name-weight")){T.nameWeight=parseInt(gv("ctrl-name-weight"));var v=document.getElementById("v-nw");if(v)v.textContent=T.nameWeight;}
  if(gv("ctrl-title-size")){T.titleSize=parseInt(gv("ctrl-title-size"));var v=document.getElementById("v-title");if(v)v.textContent=T.titleSize;}
  if(gv("ctrl-base-size")){T.baseSize=parseFloat(gv("ctrl-base-size"));var v=document.getElementById("v-base");if(v)v.textContent=T.baseSize;var qs=document.getElementById("qsize-val");if(qs)qs.textContent=T.baseSize;}
  if(gv("ctrl-lh")){T.lineHeight=parseFloat(gv("ctrl-lh"));var v=document.getElementById("v-lh");if(v)v.textContent=T.lineHeight;}
  if(gv("ctrl-gap")){T.itemSpacing=parseInt(gv("ctrl-gap"));var v=document.getElementById("v-gap");if(v)v.textContent=T.itemSpacing;}
  if(gv("ctrl-avatar-size")){T.avatarSize=parseInt(gv("ctrl-avatar-size"));var v=document.getElementById("v-avatar");if(v)v.textContent=T.avatarSize;}
  if(gv("ctrl-primary"))C.primary=gv("ctrl-primary");
  if(gv("ctrl-secondary"))C.secondary=gv("ctrl-secondary");
  if(gv("ctrl-text"))C.text=gv("ctrl-text");
  saveToLocal();renderPreview();
}
function quickFont(v){TC.fontKey=v;var af=document.getElementById("ctrl-font");if(af)af.value=v;saveToLocal();renderPreview();}
function quickSize(v){TC.typography.baseSize=parseFloat(v);document.getElementById("qsize-val").textContent=v;var as=document.getElementById("ctrl-base-size");if(as)as.value=v;saveToLocal();renderPreview();}
function setLayout(key,val,btn){TC.layout[key]=val;var parent=btn.closest(".seg-btns");if(parent){var btns=parent.querySelectorAll(".seg-btn");for(var i=0;i<btns.length;i++)btns[i].classList.remove("active");btn.classList.add("active");}saveToLocal();renderPreview();}
function printResume(){
  renderPreview();
  var layout=document.getElementById("editor-layout");
  var wasHidden=layout&&!layout.classList.contains("show-preview");
  if(wasHidden)layout.classList.add("show-preview");
  // Show print guide
  var guide=document.getElementById("print-guide");
  if(guide){
    guide.style.display="flex";
    // Store state for after print
    guide._wasHidden=wasHidden;
    guide._layout=layout;
  }else{
    setTimeout(function(){window.print();},300);
  }
}

function polishField(fieldId,fieldLabel){
  var ta=document.getElementById(fieldId);if(!ta||!ta.value.trim()){return;}
  var btn=event.target.closest(".btn-ai-mini");
  var origHTML=btn.innerHTML;
  btn.disabled=true;btn.innerHTML='<span class="mini-spin"></span> 润色中';
  var prompt="你是专业简历润色专家。请只对以下【"+fieldLabel+"】部分进行润色优化，要求：更专业、更精炼、突出量化成果。只输出润色后的文本，不加任何解释。\n\n原文：\n"+ta.value;
  fetch("/api/polish-resume",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({resume_text:prompt})})
  .then(function(r){return r.json().then(function(d){if(!r.ok)throw new Error(d.error||"润色失败");return d;});})
  .then(function(d){
    ta.value=d.polished_text;
    if(fieldId==="b-skills")resumeData.skills=d.polished_text;
    else if(fieldId==="b-intro")resumeData.intro=d.polished_text;
    liveRender();
  })
  .catch(function(e){alert("润色失败: "+e.message);})
  .finally(function(){btn.disabled=false;btn.innerHTML=origHTML;});
}

function aiExpandDuties(btnEl){
  var card=btnEl.closest(".entry-card");
  if(!card)return;
  var idx=parseInt(card.getAttribute("data-index"));
  var work=resumeData.work[idx];
  if(!work)return;
  // Gather existing duties as raw text
  var rawText=work.duties.filter(function(d){return d.trim();}).join("\n");
  if(!rawText){
    // Use company+title as context
    rawText=work.company+" "+work.title;
    if(!rawText.trim()){alert("请先填写公司/职位或至少一条工作内容");return;}
  }
  var context=(work.company||"")+" "+(work.title||"");
  var origHTML=btnEl.innerHTML;
  btnEl.disabled=true;
  btnEl.innerHTML='<span class="expand-spin"></span> 扩写中…';
  fetch("/api/auto-fill",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:rawText,context:context.trim()})})
  .then(function(r){return r.json().then(function(d){if(!r.ok)throw new Error(d.error||"扩写失败");return d;});})
  .then(function(d){
    // Parse expanded text into duty lines
    var lines=d.expanded.split("\n").map(function(l){return l.replace(/^[\-\*·•\d\.]+\s*/,"").trim();}).filter(function(l){return l.length>0;});
    if(lines.length>0){
      resumeData.work[idx].duties=lines;
      renderWorkExperience();
      liveRender();
    }
  })
  .catch(function(e){alert("扩写失败: "+e.message);})
  .finally(function(){btnEl.disabled=false;btnEl.innerHTML=origHTML;});
}

// ══ PDF Upload & AI Layout ══
function handlePdfDrop(e){
  e.preventDefault();
  document.getElementById("upload-zone").classList.remove("dragover");
  if(e.dataTransfer.files&&e.dataTransfer.files[0])uploadPdf(e.dataTransfer.files[0]);
}
function handlePdfSelect(input){if(input.files&&input.files[0])uploadPdf(input.files[0]);input.value="";}

function uploadPdf(file){
  if(!file.name.toLowerCase().endsWith(".pdf")){setUploadStatus("请上传 PDF 文件","error");return;}
  if(file.size>10*1024*1024){setUploadStatus("文件过大（最大 10MB）","error");return;}
  setUploadStatus("AI 正在解析简历…","loading");
  var fd=new FormData();fd.append("file",file);
  fetch("/api/parse-resume-pdf",{method:"POST",body:fd})
  .then(function(r){return r.json().then(function(d){if(!r.ok)throw new Error(d.error||"解析失败");return d;});})
  .then(function(d){
    if(!d.resumeData){throw new Error("返回数据格式异常");}
    // Merge parsed data into resumeData
    var rd=d.resumeData;
    if(rd.basic){for(var k in rd.basic){if(rd.basic[k])resumeData.basic[k]=rd.basic[k];}}
    if(rd.intent){for(var k in rd.intent){if(rd.intent[k])resumeData.intent[k]=rd.intent[k];}}
    if(rd.education&&rd.education.length)resumeData.education=rd.education;
    if(rd.work&&rd.work.length){
      for(var i=0;i<rd.work.length;i++){
        if(!rd.work[i].duties)rd.work[i].duties=[""];
        if(typeof rd.work[i].duties==="string")rd.work[i].duties=rd.work[i].duties.split("\n").filter(function(s){return s.trim();});
        if(!rd.work[i].duties.length)rd.work[i].duties=[""];
      }
      resumeData.work=rd.work;
    }
    if(rd.skills)resumeData.skills=rd.skills;
    if(rd.intro)resumeData.intro=rd.intro;
    if(rd.certs)resumeData.certs=rd.certs;
    // Refresh everything
    syncFormFromState();renderWorkExperience();renderEducation();saveToLocal();renderPreview();
    setUploadStatus("✓ 解析成功！已自动填充","success");
    setTimeout(function(){setUploadStatus("","");},3000);
  })
  .catch(function(e){setUploadStatus(e.message,"error");});
}

function setUploadStatus(msg,type){
  var el=document.getElementById("upload-status");
  if(!el)return;
  el.textContent=msg;
  el.className="upload-status"+(type?" "+type:"");
}

function aiOptimalLayout(){
  // Calculate total character count
  var total=0;
  total+=(resumeData.basic.name||"").length;
  total+=(resumeData.intro||"").length;
  total+=(resumeData.skills||"").length;
  total+=(resumeData.certs||"").length;
  for(var i=0;i<resumeData.work.length;i++){
    var w=resumeData.work[i];
    total+=(w.company||"").length+(w.title||"").length+(w.time||"").length;
    for(var j=0;j<w.duties.length;j++)total+=(w.duties[j]||"").length;
  }
  for(var i=0;i<resumeData.education.length;i++){
    var ed=resumeData.education[i];
    total+=(ed.school||"").length+(ed.major||"").length+(ed.degree||"").length+(ed.time||"").length;
  }

  var T=TC.typography;
  if(total<300){
    // Very sparse: make it breathe
    T.baseSize=15;T.nameSize=32;T.titleSize=18;T.lineHeight=2.0;T.itemSpacing=28;
  }else if(total<500){
    // Sparse
    T.baseSize=14.5;T.nameSize=28;T.titleSize=17;T.lineHeight=1.8;T.itemSpacing=24;
  }else if(total<800){
    // Normal
    T.baseSize=13.5;T.nameSize=26;T.titleSize=16;T.lineHeight=1.65;T.itemSpacing=20;
  }else if(total<1200){
    // Dense
    T.baseSize=13;T.nameSize=24;T.titleSize=15;T.lineHeight=1.55;T.itemSpacing=18;
  }else if(total<1800){
    // Very dense
    T.baseSize=12.5;T.nameSize=22;T.titleSize=14;T.lineHeight=1.5;T.itemSpacing=16;
  }else{
    // Extremely dense
    T.baseSize=12;T.nameSize=20;T.titleSize=13;T.lineHeight=1.45;T.itemSpacing=14;
  }

  syncControlsFromTC();saveToLocal();renderPreview();

  // Visual feedback
  var area=document.getElementById("preview-area");
  if(area){area.style.transition="box-shadow .3s";area.style.boxShadow="0 0 0 3px rgba(0,122,255,.25)";setTimeout(function(){area.style.boxShadow="";},1200);}
}

function toggleMobileView(){document.getElementById("editor-layout").classList.toggle("show-preview");var b=document.getElementById("mobile-toggle");b.textContent=document.getElementById("editor-layout").classList.contains("show-preview")?"编辑":"预览";}

function toggleCustomMode(){
  customMode=document.getElementById("custom-mode-toggle").checked;
  document.getElementById("advanced-panel").style.display=customMode?"block":"none";
  document.getElementById("quick-bar").style.display=customMode?"none":"flex";
  document.getElementById("mode-label-rec").classList.toggle("active-label",!customMode);
  document.getElementById("mode-label-cus").classList.toggle("active-label",customMode);
  // Toggle title editing
  var titles=document.querySelectorAll(".section-title[data-title-key]");
  for(var i=0;i<titles.length;i++){
    if(customMode){
      titles[i].setAttribute("contenteditable","true");
      titles[i].setAttribute("spellcheck","false");
    }else{
      titles[i].removeAttribute("contenteditable");
    }
  }
  if(!customMode){
    var def=TEMPLATE_DEFAULTS[TC.templateId]||TEMPLATE_DEFAULTS[1];
    TC.fontKey=def.fontKey;
    TC.colors=JSON.parse(JSON.stringify(def.colors));
    TC.typography=JSON.parse(JSON.stringify(def.typography));
    TC.layout=JSON.parse(JSON.stringify(def.layout));
    TC.modules=JSON.parse(JSON.stringify(def.modules));
    TC.titles={basic:"基本信息",intent:"求职意向",education:"教育背景",work:"工作经历",skills:"技能特长",intro:"自我评价",certs:"证书"};
    syncTitlesToDOM();
    syncControlsFromTC();saveToLocal();renderPreview();
  } else {
    buildModuleOrderList();
  }
}

function syncTitlesToDOM(){
  if(!TC.titles)return;
  var els=document.querySelectorAll(".section-title[data-title-key]");
  for(var i=0;i<els.length;i++){
    var key=els[i].getAttribute("data-title-key");
    if(TC.titles[key]){
      // Preserve AI buttons if present
      var aiBtn=els[i].querySelector(".btn-ai-mini");
      els[i].textContent=TC.titles[key];
      if(aiBtn)els[i].appendChild(document.createTextNode(" ")),els[i].appendChild(aiBtn);
    }
  }
}

function initTitleEditing(){
  document.addEventListener("blur",function(e){
    if(!e.target.classList||!e.target.classList.contains("section-title"))return;
    var key=e.target.getAttribute("data-title-key");
    if(!key||!customMode)return;
    // Get only text content (exclude button text)
    var text=e.target.firstChild?e.target.firstChild.textContent.trim():"";
    if(text&&TC.titles){TC.titles[key]=text;saveToLocal();renderPreview();}
  },true);
}

var _currentFilterCat="all";
function filterTemplates(cat,btn){
  _currentFilterCat=cat;
  var btns=document.querySelectorAll(".tpl-cat");for(var i=0;i<btns.length;i++)btns[i].classList.remove("active");btn.classList.add("active");
  var thumbs=document.querySelectorAll(".tpl-thumb");
  for(var i=0;i<thumbs.length;i++){
    if(cat==="all")thumbs[i].style.display="";
    else thumbs[i].style.display=thumbs[i].getAttribute("data-cat")===cat?"":"none";
  }
}

function buildTplGrid(){
  var g=document.getElementById("tpl-grid");if(!g)return;g.innerHTML="";
  for(var i=0;i<TPL_REG.length;i++){
    var t=TPL_REG[i];
    var div=document.createElement("div");
    div.className="tpl-thumb"+(TC.templateId===t.id?" selected":"");
    div.setAttribute("data-cat",t.cat);
    div.setAttribute("onclick","selectTemplate("+t.id+")");
    div.innerHTML='<div class="tpl-mini" style="background:'+t.color+'"></div><div class="tpl-name">'+t.name+'</div>';
    // Preserve current filter
    if(_currentFilterCat!=="all"&&t.cat!==_currentFilterCat)div.style.display="none";
    g.appendChild(div);
  }
}

function populateFontSelects(){
  var ids=["ctrl-font","ctrl-font-quick"];
  for(var k=0;k<ids.length;k++){
    var sel=document.getElementById(ids[k]);if(!sel)continue;sel.innerHTML="";
    for(var i=0;i<FONT_LIST.length;i++){
      var o=document.createElement("option");o.value=FONT_LIST[i].key;o.textContent=FONT_LIST[i].name;sel.appendChild(o);
    }
    sel.value=TC.fontKey;
  }
}

// ══════════════════════════════════════
// 11. RENDER ENGINE (14 Templates)
// ══════════════════════════════════════

function E(s){var d=document.createElement("div");d.textContent=s;return d.innerHTML;}
function F(){return fontCSS(TC.fontKey);}
var T,C,L; // shorthand aliases set in renderPreview

// Shared building blocks
function bullets(duties){var v=duties.filter(function(d){return d.trim();});if(!v.length)return"";var h='<ul style="margin:5px 0 0;padding-left:17px;color:'+C.text+';font-size:'+T.baseSize+'px;line-height:'+(T.lineHeight+.05)+';list-style:disc">';for(var i=0;i<v.length;i++)h+='<li style="margin-bottom:2px">'+E(v[i])+'</li>';return h+'</ul>';}
function contactPipe(){var items=[];var d=resumeData.basic;if(d.phone)items.push(E(d.phone));if(d.email)items.push(E(d.email));if(d.city)items.push(E(d.city));if(resumeData.intent.job)items.push(E(resumeData.intent.job));if(resumeData.intent.salary)items.push('期望'+E(resumeData.intent.salary));if(d.years)items.push(E(d.years)+'经验');if(!items.length)return"";var style=(TC.layout&&TC.layout.contactStyle)||"pipe";if(style==="twoLine"){var line1=[],line2=[];if(d.phone)line1.push(E(d.phone));if(d.email)line1.push(E(d.email));if(d.city)line1.push(E(d.city));if(resumeData.intent.job)line2.push(E(resumeData.intent.job));if(resumeData.intent.salary)line2.push('期望'+E(resumeData.intent.salary));if(d.years)line2.push(E(d.years)+'经验');var sep=' <span style="color:#CBD5E1;margin:0 5px">|</span> ';var h='';if(line1.length)h+='<div>'+line1.join(sep)+'</div>';if(line2.length)h+='<div style="margin-top:3px">'+line2.join(sep)+'</div>';return h;}return items.join(' <span style="color:#CBD5E1;margin:0 5px">|</span> '); }
function photoHTML(w,h,radius){if(L.avatarPosition==="hidden"||!resumeData.basic.photo)return"";var shape=L.avatarShape||"rounded";var r=shape==="circle"?"50%":shape==="square"?"2px":"6px";return'<img src="'+resumeData.basic.photo+'" style="width:'+w+'px;height:'+h+'px;object-fit:cover;border-radius:'+r+';border:1px solid #E5E7EB">';}
function workHTML(){var h="";for(var i=0;i<resumeData.work.length;i++){var w=resumeData.work[i];if(!w.company&&!w.title)continue;h+='<div style="margin-bottom:'+(T.itemSpacing*.65)+'px"><div style="display:flex;justify-content:space-between;align-items:baseline"><div><span style="font-size:'+(T.baseSize+1)+'px;font-weight:700;color:'+C.text+'">'+E(w.company)+'</span>';if(w.title)h+='<span style="color:'+C.secondary+';margin-left:10px;font-size:'+T.baseSize+'px">'+E(w.title)+'</span>';h+='</div><span style="font-size:'+(T.baseSize-1)+'px;color:#9CA3AF;white-space:nowrap">'+E(w.time)+'</span></div>'+bullets(w.duties)+'</div>';}return h;}
function eduHTML(){var h="";for(var i=0;i<resumeData.education.length;i++){var ed=resumeData.education[i];if(!ed.school)continue;h+='<div style="margin-bottom:8px"><div style="display:flex;justify-content:space-between;align-items:baseline"><span style="font-weight:700;font-size:'+(T.baseSize+1)+'px;color:'+C.text+'">'+E(ed.school)+'</span><span style="font-size:'+(T.baseSize-1)+'px;color:#9CA3AF">'+E(ed.time)+'</span></div>';var sub=[ed.major,ed.degree].filter(Boolean);if(sub.length)h+='<div style="font-size:'+T.baseSize+'px;color:'+C.secondary+';margin-top:2px">'+sub.map(E).join(' · ')+'</div>';h+='</div>';}return h;}
function skillTags(){if(!resumeData.skills)return"";var sk=resumeData.skills.split(/[,，、\n]+/).filter(function(s){return s.trim();});var h='<div style="display:flex;flex-wrap:wrap;gap:6px">';for(var i=0;i<sk.length;i++)h+='<span style="padding:3px 10px;background:#F1F5F9;border-radius:4px;font-size:'+(T.baseSize-1)+'px;color:'+C.secondary+'">'+E(sk[i].trim())+'</span>';return h+'</div>';}
function skillInline(){if(!resumeData.skills)return"";return'<div style="font-size:'+T.baseSize+'px;color:'+C.secondary+';line-height:1.7">'+resumeData.skills.split(/[,，、\n]+/).filter(function(s){return s.trim();}).map(function(s){return E(s.trim());}).join(' · ')+'</div>';}

// Section header variations
function secUnderline(title){return'<div style="margin-bottom:12px;padding-bottom:5px;border-bottom:1.5px solid '+C.primary+'"><span style="font-size:'+T.titleSize+'px;font-weight:700;color:'+C.primary+'">'+title+'</span></div>';}
function secDotted(title){return'<div style="margin-bottom:10px;padding-bottom:5px;border-bottom:1px dashed #CBD5E1"><span style="font-size:'+T.titleSize+'px;font-weight:700;color:'+C.text+'">'+title+'</span></div>';}
function secDouble(title){return'<div style="margin-bottom:10px;border-bottom:3px double '+C.primary+';padding-bottom:4px"><span style="font-size:'+T.titleSize+'px;font-weight:700;color:'+C.primary+'">'+title+'</span></div>';}
function secLeftBar(title){return'<div style="margin-bottom:12px;padding-left:12px;border-left:3px solid '+C.primary+'"><span style="font-size:'+T.titleSize+'px;font-weight:700;color:'+C.primary+'">'+title+'</span></div>';}
function secCaps(title){return'<div style="margin-bottom:10px"><span style="font-size:13px;font-weight:600;color:#9CA3AF;text-transform:uppercase;letter-spacing:.1em">'+title+'</span></div>';}

function page(inner){return'<div style="font-family:'+F()+';color:'+C.text+';font-size:'+T.baseSize+'px;line-height:'+T.lineHeight+';-webkit-font-smoothing:antialiased;position:relative">'+inner+'</div>';}

function sec(secFn,title,content){return content?'<div style="margin-bottom:'+T.itemSpacing+'px">'+secFn(title)+content+'</div>':"";}

function renderPreview(){
  var area=document.getElementById("preview-area");if(!area)return;
  T=TC.typography;C=TC.colors;L=TC.layout;
  if(!resumeData.basic.name.trim()){area.innerHTML='<div style="display:flex;align-items:center;justify-content:center;height:400px;color:#9CA3AF;font-size:14px;font-family:sans-serif">输入姓名开始预览</div>';return;}
  var id=TC.templateId;
  if(id>=1&&id<=3)area.innerHTML=renderCampus(id);
  else if(id>=4&&id<=6)area.innerHTML=renderElite(id);
  else if(id>=7&&id<=9)area.innerHTML=renderTech(id);
  else if(id>=10&&id<=12)area.innerHTML=renderCreative(id);
  else area.innerHTML=renderAcademic(id);
}
function generateResume(){renderPreview();}

// ── Campus (T1-T3) Single column, strict ──
// Shared: render modules in user-defined order
function getTitle(key,fallback){return(TC.titles&&TC.titles[key])||fallback;}
var MOD_LABELS_DEFAULT={intro:"个人简介",work:"工作经历",education:"教育背景",skills:"技能特长",certs:"证书资质"};
function renderModules(secFn){
  if(!TC.modules)TC.modules={order:["intro","work","education","skills","certs"],visible:{intro:true,work:true,education:true,skills:true,certs:true}};
  var d=resumeData,h="",V=TC.modules.visible;
  var MOD_RENDER={
    intro:function(){return V.intro!==false&&d.intro?sec(secFn,getTitle("intro","个人简介"),'<div style="color:'+C.secondary+'">'+E(d.intro)+'</div>'):"";},
    work:function(){return V.work!==false?sec(secFn,getTitle("work","工作经历"),workHTML()):"";},
    education:function(){return V.education!==false?sec(secFn,getTitle("education","教育背景"),eduHTML()):"";},
    skills:function(){return V.skills!==false&&d.skills?sec(secFn,getTitle("skills","技能特长"),skillInline()):"";},
    certs:function(){return V.certs!==false&&d.certs?sec(secFn,getTitle("certs","证书"),E(d.certs)):"";}
  };
  for(var i=0;i<TC.modules.order.length;i++){var k=TC.modules.order[i];if(MOD_RENDER[k])h+=MOD_RENDER[k]();}
  return h;
}

function renderCampus(id){
  var d=resumeData,sf=[secUnderline,secDotted,secDouble][id-1];
  var align=L.nameAlign||"center";
  var h='';
  var photoR=L.avatarPosition!=="hidden"&&d.basic.photo;
  if(photoR&&L.avatarPosition==="right")h+='<div style="position:absolute;top:0;right:0">'+photoHTML(T.avatarSize,Math.round(T.avatarSize*1.2),"3px")+'</div>';
  if(photoR&&L.avatarPosition==="left")h+='<div style="position:absolute;top:0;left:0">'+photoHTML(T.avatarSize,Math.round(T.avatarSize*1.2),"3px")+'</div>';
  var padR=photoR&&L.avatarPosition==="right"?(T.avatarSize+20)+"px":"0";
  var padL=photoR&&L.avatarPosition==="left"?(T.avatarSize+20)+"px":"0";
  h+='<div style="text-align:'+align+';margin-bottom:'+T.itemSpacing+'px;padding-right:'+padR+';padding-left:'+padL+'">';
  h+='<div style="font-size:'+T.nameSize+'px;font-weight:'+T.nameWeight+';color:'+C.text+';letter-spacing:.01em">'+E(d.basic.name)+'</div>';
  var cp=contactPipe();if(cp)h+='<div style="font-size:'+(T.baseSize-1)+'px;color:#6B7280;margin-top:5px">'+cp+'</div>';
  h+='</div>';
  h+=renderModules(sf);
  return page(h);
}

// ── Elite (T4-T6) Serif, compact, right-aligned dates ──
function renderElite(id){
  var d=resumeData;
  var serifFont=id===4?"'Merriweather',serif":id===5?"'Lora',serif":"'Noto Serif SC',serif";
  var h='<div style="font-family:'+serifFont+'">';
  var align=L.nameAlign||"center";
  h+='<div style="text-align:'+align+';margin-bottom:'+(T.itemSpacing+4)+'px;padding-bottom:12px;border-bottom:1px solid #1C1C1E">';
  h+='<div style="font-size:'+(T.nameSize+2)+'px;font-weight:'+T.nameWeight+';color:#1C1C1E;letter-spacing:.05em;text-transform:uppercase">'+E(d.basic.name)+'</div>';
  var cp=contactPipe();if(cp)h+='<div style="font-size:'+(T.baseSize-1)+'px;color:#6B7280;margin-top:6px;font-family:'+F()+'">'+cp+'</div>';
  h+='</div>';
  if(d.basic.photo&&L.avatarPosition!=="hidden")h+='<div style="position:absolute;top:0;right:0">'+photoHTML(T.avatarSize,Math.round(T.avatarSize*1.2),"2px")+'</div>';
  var sf=id===4?secUnderline:id===5?secDouble:secDotted;
  h+=renderModules(sf);
  h+='</div>';
  return page(h);
}

// ── Tech (T7-T9) Dual column sidebar ──
function renderTech(id){
  var d=resumeData,sbColor=id===7?"#1e3a5f":id===8?"#1b4332":"#1f2937";
  var h='<div style="display:flex;min-height:984px;margin:-48px -56px">';
  // Sidebar
  h+='<div style="width:230px;background:'+sbColor+';color:#fff;padding:32px 20px;flex-shrink:0;display:flex;flex-direction:column">';
  h+='<div style="text-align:center;margin-bottom:24px">';
  if(d.basic.photo&&L.avatarPosition!=="hidden")h+='<div style="margin-bottom:12px">'+photoHTML(T.avatarSize,T.avatarSize,"50%")+'</div>';
  h+='<div style="font-size:'+(T.nameSize-6)+'px;font-weight:700">'+E(d.basic.name)+'</div>';
  if(d.intent.job)h+='<div style="font-size:'+(T.baseSize-2)+'px;opacity:.7;margin-top:3px">'+E(d.intent.job)+'</div>';
  h+='</div>';
  var sbSec=function(t,c){return'<div style="margin-bottom:18px"><div style="font-size:11px;text-transform:uppercase;letter-spacing:1.2px;opacity:.4;margin-bottom:8px;font-weight:600">'+t+'</div>'+c+'</div>';};
  var ci='';if(d.basic.phone)ci+='<div style="font-size:'+(T.baseSize-2)+'px;opacity:.85;margin-bottom:5px">'+E(d.basic.phone)+'</div>';if(d.basic.email)ci+='<div style="font-size:'+(T.baseSize-2)+'px;opacity:.85;margin-bottom:5px">'+E(d.basic.email)+'</div>';if(d.basic.city)ci+='<div style="font-size:'+(T.baseSize-2)+'px;opacity:.85">'+E(d.basic.city)+'</div>';
  if(ci)h+=sbSec(getTitle('basic','联系方式'),ci);
  if(d.intent.salary||d.basic.years||d.intent.job){var ii='';if(d.intent.job)ii+='<div style="font-size:'+(T.baseSize-2)+'px;opacity:.85;margin-bottom:5px">'+E(d.intent.job)+'</div>';if(d.intent.salary)ii+='<div style="font-size:'+(T.baseSize-2)+'px;opacity:.85;margin-bottom:5px">期望 '+E(d.intent.salary)+'</div>';if(d.basic.years)ii+='<div style="font-size:'+(T.baseSize-2)+'px;opacity:.85">经验 '+E(d.basic.years)+'</div>';h+=sbSec(getTitle('intent','求职意向'),ii);}
  if(d.skills){var sk='';d.skills.split(/[,，、\n]+/).forEach(function(s){if(s.trim())sk+='<div style="font-size:'+(T.baseSize-2)+'px;opacity:.85;padding:4px 0;border-bottom:1px solid rgba(255,255,255,.08)">'+E(s.trim())+'</div>';});h+=sbSec(getTitle('skills','技能'),sk);}
  if(d.certs)h+=sbSec(getTitle('certs','证书'),'<div style="font-size:'+(T.baseSize-2)+'px;opacity:.85">'+E(d.certs)+'</div>');
  h+='</div>';
  // Main
  h+='<div style="flex:1;padding:36px 32px">';
  if(d.intro)h+=sec(secLeftBar,'个人简介','<div style="color:'+C.secondary+'">'+E(d.intro)+'</div>');
  h+=sec(secLeftBar,'工作经历',workHTML());
  h+=sec(secLeftBar,'教育背景',eduHTML());
  h+='</div></div>';
  return'<div style="font-family:'+F()+';font-size:'+T.baseSize+'px;line-height:'+T.lineHeight+';color:'+C.text+';-webkit-font-smoothing:antialiased">'+h+'</div>';
}

// ── Creative (T10-T12) Color accent blocks ──
function renderCreative(id){
  var d=resumeData,ac=id===10?"#ff6b35":id===11?"#7c3aed":"#10b981";
  var h='';
  // Colored header
  h+='<div style="background:'+ac+';color:#fff;padding:36px 40px;margin:-48px -56px 28px;display:flex;gap:20px;align-items:center">';
  if(d.basic.photo&&L.avatarPosition!=="hidden")h+=photoHTML(T.avatarSize,T.avatarSize,"50%");
  h+='<div><div style="font-size:'+T.nameSize+'px;font-weight:800">'+E(d.basic.name)+'</div>';
  if(d.intent.job)h+='<div style="font-size:'+(T.baseSize+1)+'px;opacity:.85;margin-top:3px">'+E(d.intent.job)+'</div>';
  var ci=[d.basic.phone,d.basic.email,d.basic.city].filter(Boolean);
  if(ci.length)h+='<div style="font-size:'+(T.baseSize-2)+'px;opacity:.65;margin-top:6px">'+ci.map(E).join(" | ")+'</div>';
  h+='</div></div>';
  var sf=function(title){return'<div style="margin-bottom:12px;padding-bottom:6px;border-bottom:2px solid '+ac+'"><span style="font-size:'+T.titleSize+'px;font-weight:700;color:'+ac+'">'+title+'</span></div>';};
  if(d.intro)h+=sec(sf,'个人简介','<div style="color:'+C.secondary+'">'+E(d.intro)+'</div>');
  h+=sec(sf,'工作经历',workHTML());
  h+=sec(sf,'教育背景',eduHTML());
  if(d.skills)h+=sec(sf,'技能特长','<div style="display:flex;flex-wrap:wrap;gap:6px">'+d.skills.split(/[,，、\n]+/).filter(function(s){return s.trim();}).map(function(s){return'<span style="padding:3px 10px;background:'+ac+'12;color:'+ac+';border-radius:4px;font-size:'+(T.baseSize-1)+'px;font-weight:500">'+E(s.trim())+'</span>';}).join("")+'</div>');
  if(d.certs)h+=sec(sf,'证书','<div style="color:'+C.secondary+'">'+E(d.certs)+'</div>');
  return page(h);
}

// ── Academic (T13-T14) Research focus ──
function renderAcademic(id){
  var d=resumeData,sf=id===13?secUnderline:secCaps;
  var h='';
  h+='<div style="margin-bottom:'+T.itemSpacing+'px">';
  h+='<div style="font-size:'+T.nameSize+'px;font-weight:'+(id===13?'800':'300')+';color:'+C.text+'">'+E(d.basic.name)+'</div>';
  var cp=contactPipe();if(cp)h+='<div style="font-size:'+(T.baseSize-1)+'px;color:#6B7280;margin-top:5px">'+cp+'</div>';
  if(d.basic.photo&&L.avatarPosition!=="hidden")h+='<div style="position:absolute;top:0;right:0">'+photoHTML(T.avatarSize,Math.round(T.avatarSize*1.2),"2px")+'</div>';
  h+='</div>';
  if(d.intro)h+=sec(sf,id===13?'研究兴趣':'简介','<div style="color:'+C.secondary+';line-height:1.75">'+E(d.intro)+'</div>');
  h+=sec(sf,'教育背景',eduHTML());
  h+=sec(sf,id===13?'科研/工作经历':'经历',workHTML());
  if(d.skills)h+=sec(sf,id===13?'专业技能':'技能',skillInline());
  if(d.certs)h+=sec(sf,id===13?'发表/证书':'证书','<div style="color:'+C.secondary+';line-height:1.75">'+E(d.certs)+'</div>');
  return page(h);
}

// ══ 12. Other Pages (kept for resume.html / jd_match.html) ══
var JD_DATA={"互联网/IT":{"前端开发":"岗位职责：\n1. 前端开发\n\n要求：\n1. 3年+\n2. React/Vue","后端开发":"岗位职责：\n1. 架构设计\n\n要求：\n1. Java/Python","产品经理":"岗位职责：\n1. 需求分析\n\n要求：\n1. 2年+","数据分析":"岗位职责：\n1. 数据体系\n\n要求：\n1. SQL/Python"},"金融/银行":{"风控分析":"岗位：\n1. 风险模型\n\n要求：\n1. 金融本科","投资顾问":"岗位：\n1. 投资建议\n\n要求：\n1. 证券资格","客户经理":"岗位：\n1. 客户\n\n要求：\n1. 银行经验"},"教育/培训":{"课程设计":"岗位：\n1. 课程\n\n要求：\n1. 教育本科","教师":"岗位：\n1. 教学\n\n要求：\n1. 资格证","培训讲师":"岗位：\n1. 培训\n\n要求：\n1. 3年"},"医疗/健康":{"临床研究":"岗位：\n1. 临床\n\n要求：\n1. 医学本科","医药代表":"岗位：\n1. 客户\n\n要求：\n1. 医药","健康管理":"岗位：\n1. 方案\n\n要求：\n1. 管理师证"}};
function onIndustryChange(s){var i=s.value,p=document.getElementById("position-select"),j=document.getElementById("jd-input");p.innerHTML='<option value="">-- 选择 --</option>';if(j)j.value="";if(i&&JD_DATA[i]){var k=Object.keys(JD_DATA[i]);for(var x=0;x<k.length;x++){var o=document.createElement("option");o.value=k[x];o.textContent=k[x];p.appendChild(o);}p.disabled=false;}else p.disabled=true;}
function onPositionChange(s){var i=document.getElementById("industry-select").value,p=s.value,j=document.getElementById("jd-input");if(i&&p&&JD_DATA[i]&&JD_DATA[i][p])j.value="岗位："+p+"\n\n"+JD_DATA[i][p];}
function switchResumeMode(m){var f=document.getElementById("free-mode"),t=document.getElementById("template-mode"),bf=document.getElementById("btn-mode-free"),bt=document.getElementById("btn-mode-template");if(m==="template"){f.style.display="none";t.style.display="block";bf.classList.remove("active");bt.classList.add("active");}else{f.style.display="block";t.style.display="none";bf.classList.add("active");bt.classList.remove("active");}}
function getResumeText(){var f=document.getElementById("free-mode");if(f&&f.style.display!=="none")return document.getElementById("resume-input").value.trim();var v=function(id){return(document.getElementById(id)||{}).value||"";};var p=[];var n=v("t-name").trim();if(n)p.push(n);var ph=v("t-phone").trim(),em=v("t-email").trim();if(ph||em)p.push("联系："+[ph,em].filter(Boolean).join("|"));var sc=v("t-school").trim();if(sc){p.push("");p.push("教育："+[v("t-grad-year"),sc,v("t-major"),v("t-education")].filter(Boolean).join(" "));}var exp=v("t-experience").trim();if(exp){p.push("");p.push("经历：\n"+exp);}var sk=v("t-skills").trim();if(sk)p.push("\n技能："+sk);var si=v("t-self-intro").trim();if(si)p.push("\n评价："+si);return p.join("\n");}
function showError(m){var t=document.getElementById("error-toast");if(!t)return;t.textContent=m;t.classList.add("visible");setTimeout(function(){t.classList.remove("visible");},4000);}
function getScoreColor(s){return s>=80?"#10B981":s>=60?"#F59E0B":"#EF4444";}
function renderScoreRing(id,sc,label){var c=document.getElementById(id);if(!c)return;var col=getScoreColor(sc),ci=2*Math.PI*54,off=ci-(sc/100)*ci;c.innerHTML='<div class="score-ring"><svg viewBox="0 0 128 128"><circle class="bg-circle" cx="64" cy="64" r="54"/><circle class="score-circle" cx="64" cy="64" r="54" stroke="'+col+'" stroke-dasharray="'+ci+'" stroke-dashoffset="'+ci+'"/></svg><div class="score-value" style="color:'+col+'">'+sc+'</div></div><div class="score-label">'+(label||"综合评分")+'</div>';requestAnimationFrame(function(){var el=c.querySelector(".score-circle");if(el)el.style.strokeDashoffset=off;});}
function renderDimensions(id,dims){var c=document.getElementById(id);if(!c||!dims)return;var h="<h3>维度评分</h3>";for(var i=0;i<dims.length;i++){var d=dims[i],p=d.score*10,col=getScoreColor(p);h+='<div class="dim-item"><div class="dim-header"><span class="dim-name">'+d.name+'</span><span class="dim-score" style="color:'+col+'">'+d.score+'/10</span></div><div class="dim-bar"><div class="dim-bar-fill" data-width="'+p+'%" style="background:'+col+'"></div></div><div class="dim-comment">'+d.comment+'</div></div>';}c.innerHTML=h;requestAnimationFrame(function(){var fs=c.querySelectorAll(".dim-bar-fill");for(var j=0;j<fs.length;j++)fs[j].style.width=fs[j].getAttribute("data-width");});}
function renderList(id,title,items,ic,lc){var c=document.getElementById(id);if(!c||!items||!items.length){if(c)c.style.display="none";return;}var h='<h3><span class="icon '+ic+'"></span>'+title+'</h3><ul class="info-list '+lc+'">';for(var i=0;i<items.length;i++)h+="<li>"+items[i]+"</li>";c.innerHTML=h+"</ul>";c.style.display="block";}
function renderSummary(id,title,text){var c=document.getElementById(id);if(!c||!text){if(c)c.style.display="none";return;}c.innerHTML="<h3>"+title+"</h3><p>"+text+"</p>";c.style.display="block";}
var _lastResumeText="";
function submitResume(){var consent=document.getElementById("privacy-consent");if(consent&&!consent.checked){showError("请先勾选同意隐私政策和用户协议");return;}var btn=document.getElementById("submit-btn"),rp=document.getElementById("result-panel"),text=getResumeText();if(!text){showError("请输入");return;}_lastResumeText=text;btn.disabled=true;btn.innerHTML='<span class="loading-spinner"></span>分析中...';rp.classList.remove("visible");fetch("/api/analyze-resume",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({resume_text:text})}).then(function(r){return r.json().then(function(d){if(!r.ok)throw new Error(d.error);return d;});}).then(function(d){renderScoreRing("score-container",d.overall_score||0);renderDimensions("dimensions-container",d.dimensions);renderList("highlights-container","亮点",d.highlights,"green","green");renderList("issues-container","待改进",d.issues,"red","red");renderList("suggestions-container","建议",d.suggestions,"blue","blue");renderSummary("summary-container","AI改写简介",d.rewritten_summary);var ps=document.getElementById("polish-section");if(ps)ps.style.display="block";rp.classList.add("visible");rp.scrollIntoView({behavior:"smooth"});}).catch(function(e){showError(e.message);}).finally(function(){btn.disabled=false;btn.innerHTML="开始诊断";});}
var _missingKeywords=[];
function submitJdMatch(){var consent=document.getElementById("privacy-consent-jd");if(consent&&!consent.checked){showError("请先勾选同意隐私政策和用户协议");return;}var btn=document.getElementById("submit-btn"),rp=document.getElementById("result-panel"),rt=getResumeText(),jt=document.getElementById("jd-input").value.trim();if(!rt||!jt){showError("请填写");return;}_lastResumeText=rt;_missingKeywords=[];btn.disabled=true;btn.innerHTML='<span class="loading-spinner"></span>匹配中...';rp.classList.remove("visible");fetch("/api/match-jd",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({resume_text:rt,jd_text:jt})}).then(function(r){return r.json().then(function(d){if(!r.ok)throw new Error(d.error);return d;});}).then(function(d){
  var score=d.match_score||0;
  renderScoreRing("score-container",score,"🤖 ATS 模拟机器初筛通过率");
  // ATS Warning
  var aw=document.getElementById("ats-warning");
  if(aw){
    if(score<60){aw.className="ats-warning danger";aw.innerHTML='<span class="ats-icon">🚨</span> <strong>高风险</strong>：当前通过率较低，存在被 ATS 系统自动拦截的风险。建议立即优化关键词覆盖率。';aw.style.display="block";}
    else if(score<75){aw.className="ats-warning caution";aw.innerHTML='<span class="ats-icon">⚠️</span> <strong>需优化</strong>：通过率偏低，部分关键词未覆盖。建议补充缺失词以提高机筛通过率。';aw.style.display="block";}
    else{aw.className="ats-warning safe";aw.innerHTML='<span class="ats-icon">✅</span> <strong>通过率良好</strong>：关键词覆盖较全面，ATS 机筛通过概率较高。';aw.style.display="block";}
  }
  if(d.sub_scores){var ss=d.sub_scores,lb={skill_match:"技能",experience_match:"经验",education_match:"学历",industry_match:"行业"},h="",ks=Object.keys(lb);for(var i=0;i<ks.length;i++){var v=ss[ks[i]]||0;h+='<div class="sub-score-item"><div class="sub-score-value" style="color:'+getScoreColor(v)+'">'+v+'</div><div class="sub-score-label">'+lb[ks[i]]+'</div></div>';}var sc=document.getElementById("sub-scores-container");if(sc)sc.innerHTML=h;}
  // Keywords + inject section
  renderKeywordsWithInject("keywords-container",d.matched_keywords,d.missing_keywords);
  _missingKeywords=d.missing_keywords||[];
  var injectSec=document.getElementById("inject-section");
  if(injectSec){injectSec.style.display=_missingKeywords.length>0?"block":"none";document.getElementById("inject-result").style.display="none";}
  renderList("strengths-container","匹配优势",d.strengths,"green","green");renderList("gaps-container","差距分析",d.gaps,"red","red");renderList("suggestions-container","优化建议",d.suggestions,"blue","blue");renderSummary("summary-container","针对该岗位的个人简介",d.tailored_summary);var ps=document.getElementById("polish-section");if(ps)ps.style.display="block";rp.classList.add("visible");rp.scrollIntoView({behavior:"smooth"});}).catch(function(e){showError(e.message);}).finally(function(){btn.disabled=false;btn.innerHTML="开始匹配分析";});}
function polishResume(){var btn=document.getElementById("polish-btn"),rd=document.getElementById("polish-result");if(!_lastResumeText){showError("无内容");return;}btn.disabled=true;btn.innerHTML='<span class="loading-spinner"></span>润色中...';rd.style.display="none";fetch("/api/polish-resume",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({resume_text:_lastResumeText})}).then(function(r){return r.json().then(function(d){if(!r.ok)throw new Error(d.error);return d;});}).then(function(d){rd.innerHTML='<h3 style="color:#007AFF;margin-bottom:12px">润色结果</h3><div style="white-space:pre-wrap;line-height:1.8;font-size:14px;color:#374151">'+d.polished_text.replace(/</g,"&lt;")+'</div><div style="margin-top:16px"><button class="btn btn-primary" style="max-width:360px" onclick="goToBuilder()">生成简历</button></div>';rd.style.display="block";_lastResumeText=d.polished_text;rd.scrollIntoView({behavior:"smooth"});}).catch(function(e){showError(e.message);}).finally(function(){btn.disabled=false;btn.innerHTML="AI润色";});}
function goToBuilder(){window.location.href="/builder?intro="+encodeURIComponent(_lastResumeText);}

// ══ Career Advisor Modal ══
function openCareerModal(){
  var overlay=document.getElementById("career-modal-overlay");
  if(!overlay)return;
  overlay.classList.add("open");
  document.body.style.overflow="hidden";
  setTimeout(function(){var ta=document.getElementById("career-query");if(ta)ta.focus();},300);
}
function closeCareerModal(e){
  if(e&&e.target&&!e.target.classList.contains("modal-overlay"))return;
  var overlay=document.getElementById("career-modal-overlay");
  if(!overlay)return;
  overlay.classList.remove("open");
  document.body.style.overflow="";
}
function submitCareerQuery(){
  var ta=document.getElementById("career-query");
  var btn=document.getElementById("career-submit-btn");
  var resultDiv=document.getElementById("career-result");
  if(!ta||!ta.value.trim()){alert("请描述你的情况");return;}
  btn.disabled=true;
  btn.innerHTML='<span class="loading-spinner"></span> AI 分析中，请稍候...';
  resultDiv.style.display="none";
  fetch("/api/career-advisor",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({user_query:ta.value})})
  .then(function(r){return r.json().then(function(d){if(!r.ok)throw new Error(d.error||"请求失败");return d;});})
  .then(function(d){
    var h='';
    // Salary evaluation
    if(d.salary_evaluation){
      h+='<div class="cr-section"><div class="cr-label">💰 薪资评估</div><div class="cr-salary">'+d.salary_evaluation.replace(/</g,"&lt;")+'</div></div>';
    }
    // Recommended roles
    if(d.recommended_roles&&d.recommended_roles.length){
      h+='<div class="cr-section"><div class="cr-label">🎯 推荐岗位</div><div class="cr-roles">';
      for(var i=0;i<d.recommended_roles.length;i++){
        var role=d.recommended_roles[i];
        h+='<div class="cr-role"><div><div class="cr-role-title">'+(role.title||"").replace(/</g,"&lt;")+'</div><div class="cr-role-reason">'+(role.reason||"").replace(/</g,"&lt;")+'</div></div></div>';
      }
      h+='</div></div>';
    }
    // Best match JD preview
    if(d.best_match_jd){
      h+='<div class="cr-section"><div class="cr-label">📋 最佳匹配 JD</div><div class="cr-jd-preview">'+d.best_match_jd.replace(/</g,"&lt;")+'</div></div>';
      h+='<button class="cr-adopt-btn" onclick="adoptCareerJD()">✅ 一键采纳此 JD，开始匹配分析</button>';
      window._careerBestJD=d.best_match_jd;
    }
    resultDiv.innerHTML=h;
    resultDiv.style.display="block";
    resultDiv.scrollIntoView({behavior:"smooth",block:"nearest"});
  })
  .catch(function(e){
    resultDiv.innerHTML='<div style="padding:16px;background:#FEF2F2;border-radius:10px;color:#DC2626;font-size:.88rem">'+e.message+'</div>';
    resultDiv.style.display="block";
  })
  .finally(function(){
    btn.disabled=false;
    btn.innerHTML="获取 AI 建议";
  });
}
function adoptCareerJD(){
  var jdInput=document.getElementById("jd-input");
  if(!jdInput||!window._careerBestJD)return;
  jdInput.value=window._careerBestJD;
  // Visually dim the selectors since we're using AI-generated JD
  var indSel=document.getElementById("industry-select");
  var posSel=document.getElementById("position-select");
  if(indSel)indSel.style.opacity=".4";
  if(posSel)posSel.style.opacity=".4";
  closeCareerModal();
  jdInput.scrollIntoView({behavior:"smooth"});
  // Flash effect on textarea
  jdInput.style.transition="box-shadow .3s";
  jdInput.style.boxShadow="0 0 0 3px rgba(0,122,255,.3)";
  setTimeout(function(){jdInput.style.boxShadow="";},1500);
}

// ══ Keywords with Inject + ATS Functions ══
function renderKeywordsWithInject(id,m,mi){
  var c=document.getElementById(id);if(!c)return;
  if((!m||!m.length)&&(!mi||!mi.length)){c.style.display="none";return;}
  var h="<h3>关键词覆盖分析</h3>";
  if(m&&m.length){h+='<div class="keyword-group"><div class="keyword-group-label">✅ 已覆盖 ('+m.length+')</div><div class="keyword-tags">';for(var i=0;i<m.length;i++)h+='<span class="keyword-tag matched">'+m[i]+'</span>';h+="</div></div>";}
  if(mi&&mi.length){h+='<div class="keyword-group"><div class="keyword-group-label">❌ 未覆盖 ('+mi.length+') — 这些关键词缺失会降低 ATS 通过率</div><div class="keyword-tags">';for(var j=0;j<mi.length;j++)h+='<span class="keyword-tag missing">'+mi[j]+'</span>';h+="</div></div>";}
  c.innerHTML=h;c.style.display="block";
}

function injectMissingKeywords(){
  if(!_missingKeywords.length||!_lastResumeText){showError("没有缺失关键词");return;}
  var btn=document.getElementById("inject-btn");
  var resultDiv=document.getElementById("inject-result");
  btn.disabled=true;
  btn.innerHTML='<span class="inject-spin"></span> AI 正在智能融合关键词...';
  resultDiv.style.display="none";
  fetch("/api/inject-keywords",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({resume_text:_lastResumeText,missing_keywords:_missingKeywords})})
  .then(function(r){return r.json().then(function(d){if(!r.ok)throw new Error(d.error||"融合失败");return d;});})
  .then(function(d){
    _lastResumeText=d.enhanced_resume;
    resultDiv.innerHTML='<div class="summary-card" style="margin-bottom:0"><h3 style="color:#059669">✅ 关键词融合完成</h3><p style="font-size:.85rem;color:#374151;line-height:1.7;white-space:pre-wrap;max-height:300px;overflow-y:auto">'+d.enhanced_resume.replace(/</g,"&lt;")+'</p></div><button class="btn-apply-builder" onclick="applyToBuilder()">🚀 一键应用到简历编辑器，查看最终效果</button>';
    resultDiv.style.display="block";
    resultDiv.scrollIntoView({behavior:"smooth",block:"nearest"});
  })
  .catch(function(e){
    resultDiv.innerHTML='<div style="padding:14px;background:#FEF2F2;border-radius:10px;color:#DC2626;font-size:.88rem">'+e.message+'</div>';
    resultDiv.style.display="block";
  })
  .finally(function(){btn.disabled=false;btn.innerHTML="⚡ 一键智能融合缺失关键词到简历";});
}

function applyToBuilder(){
  if(!_lastResumeText)return;
  // Save enhanced resume to localStorage for builder to pick up
  var builderData={basic:{name:"",age:"",phone:"",email:"",city:"",years:"",photo:""},intent:{job:"",salary:""},education:[{school:"",major:"",degree:"",time:""}],work:[{company:"",title:"",time:"",duties:[""]}],skills:"",intro:_lastResumeText,certs:""};
  try{localStorage.setItem("resumeAI_data",JSON.stringify(builderData));}catch(e){}
  window.location.href="/builder?intro="+encodeURIComponent(_lastResumeText);
}

// ══ 13. Init ══
document.addEventListener("DOMContentLoaded",function(){
  if(document.getElementById("work-list")){
    loadFromLocal();populateFontSelects();syncFormFromState();syncControlsFromTC();
    buildTplGrid();renderWorkExperience();renderEducation();initEventDelegation();
    initTitleEditing();syncTitlesToDOM();
    document.getElementById("mode-label-rec").classList.add("active-label");
    renderPreview();
  }
  var p=new URLSearchParams(window.location.search);
  if(p.get("intro")){var el=document.getElementById("b-intro");if(el){el.value=decodeURIComponent(p.get("intro"));resumeData.intro=el.value;saveToLocal();}}
});
