/* ══════════════════════════════════════
   credits.js — AI 算力系统 + 设备指纹 + 评价 + 绑定
   ══════════════════════════════════════ */
var PowerSystem=(function(){
var _uid="",_did="",_credits=0,_bound=false,_inited=false,_hasUsed=false;

function uuid(){return"xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g,function(c){var r=Math.random()*16|0;return(c==="x"?r:r&0x3|0x8).toString(16);});}

async function init(){
  if(_inited)return;
  _uid=localStorage.getItem("rai_uid");
  if(!_uid){_uid=uuid();localStorage.setItem("rai_uid",_uid);}
  try{var fp=await FingerprintJS.load();var r=await fp.get();_did=r.visitorId;}
  catch(e){_did="fb_"+navigator.userAgent.length+"_"+screen.width+"x"+screen.height;}
  try{
    var resp=await fetch("/api/credits/init",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({user_id:_uid,device_hash:_did})});
    var d=await resp.json();
    if(d.error&&d.need_bind){showBind(d.error);return;}
    _credits=d.credits||0;_bound=d.bound||false;_inited=true;_updateBadge();
  }catch(e){console.error("Power init:",e);}
}

function _updateBadge(){
  var els=document.querySelectorAll(".pw-num");
  for(var i=0;i<els.length;i++)els[i].textContent=_credits;
  var b=document.getElementById("power-badge");if(b)b.style.display="flex";
}

async function requirePower(){
  if(_credits>=100){
    var resp=await fetch("/api/credits/consume",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({user_id:_uid})});
    var d=await resp.json();
    if(d.error){
      if(d.need_bind)showBind(d.error);
      else if(d.credits<=0)showReview();
      return false;
    }
    _credits=d.credits;_hasUsed=true;_updateBadge();return true;
  }
  if(_credits<=0&&!_hasUsed)showBind("算力不足");
  else showReview();
  return false;
}

// ── Review Modal ──
var _rating=0;
function showReview(){var o=document.getElementById("review-overlay");if(o)o.classList.add("open");}
function closeReview(){var o=document.getElementById("review-overlay");if(o)o.classList.remove("open");}
function pickStar(n){
  _rating=n;
  var stars=document.querySelectorAll(".rv-s");
  for(var i=0;i<stars.length;i++)stars[i].classList.toggle("on",i<n);
}
async function submitReview(){
  if(_rating<1){alert("请选择评分");return;}
  var ct=(document.getElementById("rv-ct")||{}).value||"";
  var anon=document.getElementById("rv-anon")?document.getElementById("rv-anon").checked:false;
  var name=(document.getElementById("rv-name")||{}).value||"用户";
  var feat=(document.getElementById("rv-feat")||{}).value||"general";
  var btn=document.getElementById("rv-btn");btn.disabled=true;btn.textContent="提交中...";
  try{
    var resp=await fetch("/api/submit-review",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({user_id:_uid,rating:_rating,content:ct,is_anonymous:anon,display_name:anon?"匿名用户":name,feature:feat})});
    var d=await resp.json();
    if(d.error){alert(d.error);return;}
    _credits=d.credits;_updateBadge();closeReview();
    toast("⚡ "+d.message);
    if(d.show_bind&&!_bound)setTimeout(function(){showBind();},800);
  }catch(e){alert("提交失败");}
  finally{btn.disabled=false;btn.textContent="提交评价，获得 ⚡100 算力";}
}

// ── Bind Modal ──
function showBind(msg){
  var o=document.getElementById("bind-overlay");if(!o)return;
  if(msg){var el=document.getElementById("bind-reason");if(el)el.textContent=msg;}
  o.classList.add("open");
}
function closeBind(){var o=document.getElementById("bind-overlay");if(o)o.classList.remove("open");}
async function submitBind(){
  var v=(document.getElementById("bind-val")||{value:""}).value.trim();
  if(!v){alert("请输入邮箱或手机号");return;}
  var isE=v.indexOf("@")>0;
  var btn=document.getElementById("bind-btn");btn.disabled=true;btn.textContent="绑定中...";
  try{
    var body={user_id:_uid};if(isE)body.email=v;else body.phone=v;
    var resp=await fetch("/api/bind-account",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
    var d=await resp.json();
    if(d.error){alert(d.error);return;}
    if(d.merged&&d.new_user_id){_uid=d.new_user_id;localStorage.setItem("rai_uid",_uid);}
    _credits=d.credits;_bound=true;_updateBadge();closeBind();
    toast("✅ "+d.message);
  }catch(e){alert("绑定失败");}
  finally{btn.disabled=false;btn.textContent="一键绑定，永久保存";}
}

function toast(msg){
  var t=document.getElementById("pw-toast");
  if(!t)return;t.textContent=msg;t.classList.add("show");
  setTimeout(function(){t.classList.remove("show");},3000);
}

function promptReview(feat){
  var el=document.getElementById("rv-feat");if(el)el.value=feat;
  if(_hasUsed&&_credits<200)setTimeout(function(){showReview();},3500);
}

return{init:init,requirePower:requirePower,showReview:showReview,closeReview:closeReview,
  pickStar:pickStar,submitReview:submitReview,showBind:showBind,closeBind:closeBind,
  submitBind:submitBind,promptReview:promptReview,getCredits:function(){return _credits;},
  getUID:function(){return _uid;}};
})();
document.addEventListener("DOMContentLoaded",function(){PowerSystem.init();});
