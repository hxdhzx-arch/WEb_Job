/* ══════════════════════════════════════
   credits.js — AI 算力系统 + 验证码绑定 + 验证码登录 + 云端同步
   ══════════════════════════════════════ */
var PowerSystem=(function(){
var _uid="",_did="",_credits=0,_bound=false,_inited=false,_hasUsed=false;
var _bindTarget=""; // 临时存储待绑定的邮箱/手机号

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
    // 初始化云端同步模块
    if(typeof CloudSync!=="undefined")CloudSync.init(_uid,_bound);
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

// ── Bind Modal (改造: 验证码两步流程) ──
function showBind(msg){
  var o=document.getElementById("bind-overlay");if(!o)return;
  if(msg){var el=document.getElementById("bind-reason");if(el)el.textContent=msg;}
  // 重置到 step1
  var s1=document.getElementById("bind-step1"),s2=document.getElementById("bind-step2");
  if(s1)s1.style.display="block";
  if(s2)s2.style.display="none";
  o.classList.add("open");
}
function closeBind(){var o=document.getElementById("bind-overlay");if(o)o.classList.remove("open");}

async function sendBindCode(){
  var val=(document.getElementById("bind-val")||{value:""}).value.trim();
  if(!val){alert("请输入邮箱或手机号");return;}
  _bindTarget=val;
  var btn=document.getElementById("bind-send-code-btn");
  btn.disabled=true;btn.textContent="发送中...";
  try{
    var resp=await fetch("/api/verify/send",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({target:val,purpose:"bind"})});
    var d=await resp.json();
    if(d.error){alert(d.error);return;}
    // 切换到 step2
    document.getElementById("bind-step1").style.display="none";
    document.getElementById("bind-step2").style.display="block";
    document.getElementById("bind-target-display").textContent=d.message.replace("验证码已发送至 ","");
    document.getElementById("bind-code").value="";
    document.getElementById("bind-code").focus();
    _startCountdown("bind",60);
  }catch(e){alert("发送失败，请重试");}
  finally{btn.disabled=false;btn.textContent="发送验证码";}
}

async function submitBind(){
  var code=(document.getElementById("bind-code")||{value:""}).value.trim();
  if(!code||code.length!==6){alert("请输入 6 位验证码");return;}
  var isE=_bindTarget.indexOf("@")>0;
  var btn=document.getElementById("bind-btn");btn.disabled=true;btn.textContent="绑定中...";
  try{
    var body={user_id:_uid,code:code};
    if(isE)body.email=_bindTarget;else body.phone=_bindTarget;
    var resp=await fetch("/api/bind-account",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
    var d=await resp.json();
    if(d.error){alert(d.error);return;}
    if(d.merged&&d.new_user_id){_uid=d.new_user_id;localStorage.setItem("rai_uid",_uid);}
    _credits=d.credits;_bound=true;_updateBadge();closeBind();
    toast("✅ "+d.message);
    // 触发云端保存
    if(typeof CloudSync!=="undefined")CloudSync.onBound(_uid);
  }catch(e){alert("绑定失败");}
  finally{btn.disabled=false;btn.textContent="确认绑定";}
}

// ── Login Modal (新增) ──
var _loginTarget="";
function showLogin(){
  var o=document.getElementById("login-overlay");if(!o)return;
  document.getElementById("login-step1").style.display="block";
  document.getElementById("login-step2").style.display="none";
  o.classList.add("open");
  setTimeout(function(){var inp=document.getElementById("login-val");if(inp)inp.focus();},300);
}
function closeLogin(){var o=document.getElementById("login-overlay");if(o)o.classList.remove("open");}

async function sendLoginCode(){
  var val=(document.getElementById("login-val")||{value:""}).value.trim();
  if(!val){alert("请输入邮箱或手机号");return;}
  _loginTarget=val;
  var btn=document.getElementById("login-send-btn");
  btn.disabled=true;btn.textContent="发送中...";
  try{
    var resp=await fetch("/api/verify/send",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({target:val,purpose:"login"})});
    var d=await resp.json();
    if(d.error){alert(d.error);return;}
    document.getElementById("login-step1").style.display="none";
    document.getElementById("login-step2").style.display="block";
    document.getElementById("login-target-display").textContent=d.message.replace("验证码已发送至 ","");
    document.getElementById("login-code").value="";
    document.getElementById("login-code").focus();
    _startCountdown("login",60);
  }catch(e){alert("发送失败");}
  finally{btn.disabled=false;btn.textContent="发送验证码";}
}

async function submitLogin(){
  var code=(document.getElementById("login-code")||{value:""}).value.trim();
  if(!code||code.length!==6){alert("请输入 6 位验证码");return;}
  var btn=document.getElementById("login-btn");btn.disabled=true;btn.textContent="验证中...";
  try{
    var resp=await fetch("/api/auth/login",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({target:_loginTarget,code:code})});
    var d=await resp.json();
    if(d.error){alert(d.error);return;}
    // 恢复身份
    _uid=d.user_id;localStorage.setItem("rai_uid",_uid);
    _credits=d.credits;_bound=true;_updateBadge();closeLogin();
    toast("✅ 欢迎回来！已恢复您的账号");
    // 恢复云端简历
    if(d.default_resume&&typeof CloudSync!=="undefined"){
      CloudSync.applyResume(d.default_resume);
    }
  }catch(e){alert("验证失败");}
  finally{btn.disabled=false;btn.textContent="验证并恢复";}
}

// ── Countdown Timer ──
var _timers={};
function _startCountdown(prefix,seconds){
  var resend=document.getElementById(prefix+"-resend");
  var countdown=document.getElementById(prefix+"-countdown");
  if(!resend||!countdown)return;
  resend.style.display="none";
  countdown.style.display="inline";
  var remaining=seconds;
  countdown.textContent=remaining+"s 后可重发";
  if(_timers[prefix])clearInterval(_timers[prefix]);
  _timers[prefix]=setInterval(function(){
    remaining--;
    if(remaining<=0){
      clearInterval(_timers[prefix]);
      resend.style.display="inline";
      countdown.style.display="none";
    }else{
      countdown.textContent=remaining+"s 后可重发";
    }
  },1000);
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

return{
  init:init,requirePower:requirePower,
  showReview:showReview,closeReview:closeReview,
  pickStar:pickStar,submitReview:submitReview,
  showBind:showBind,closeBind:closeBind,
  sendBindCode:sendBindCode,submitBind:submitBind,
  showLogin:showLogin,closeLogin:closeLogin,
  sendLoginCode:sendLoginCode,submitLogin:submitLogin,
  promptReview:promptReview,
  getCredits:function(){return _credits;},
  getUID:function(){return _uid;},
  isBound:function(){return _bound;},
  toast:toast
};
})();
document.addEventListener("DOMContentLoaded",function(){PowerSystem.init();});
