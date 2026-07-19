/* ===================================================================
   Čiara — darts scoring (501 / 301 / 701 + Cricket)
   Local multiplayer, no backend. State machine + undo stack.
   =================================================================== */
'use strict';

const PLAYER_COLORS = ['#c6f24e','#ff5964','#54c7ff','#ffd76a','#b18bff','#4ade80','#ff9f6a','#f472b6'];
const CRICKET_NUMS = [20,19,18,17,16,15,25]; // 25 = bull

/* ---- Checkout table (double-out finishes), 2..170 ---- */
const CHECKOUTS = {
 170:'T20 T20 Bull',167:'T20 T19 Bull',164:'T20 T18 Bull',161:'T20 T17 Bull',160:'T20 T20 D20',
 158:'T20 T20 D19',157:'T20 T19 D20',156:'T20 T20 D18',155:'T20 T19 D19',154:'T20 T18 D20',
 153:'T20 T19 D18',152:'T20 T20 D16',151:'T20 T17 D20',150:'T20 T18 D18',149:'T20 T19 D16',
 148:'T20 T16 D20',147:'T20 T17 D18',146:'T20 T18 D16',145:'T20 T15 D20',144:'T20 T20 D12',
 143:'T20 T17 D16',142:'T20 T14 D20',141:'T20 T19 D12',140:'T20 T20 D10',139:'T20 T13 D20',
 138:'T20 T18 D12',137:'T20 T19 D10',136:'T20 T20 D8',135:'T20 T17 D12',134:'T20 T14 D16',
 133:'T20 T19 D8',132:'T20 T16 D12',131:'T20 T13 D16',130:'T20 T18 D8',129:'T19 T16 D12',
 128:'T18 T14 D16',127:'T20 T17 D8',126:'T19 T19 D6',125:'Bull T20 D20',124:'T20 T16 D8',
 123:'T19 T16 D9',122:'T18 T20 D4',121:'T20 T11 D14',120:'T20 20 D20',119:'T19 T12 D13',
 118:'T20 18 D20',117:'T20 17 D20',116:'T20 16 D20',115:'T20 15 D20',114:'T20 14 D20',
 113:'T20 13 D20',112:'T20 12 D20',111:'T20 19 D16',110:'T20 Bull D5',109:'T20 9 D20',
 108:'T20 16 D16',107:'T19 18 D16',106:'T20 14 D16',105:'T20 13 D16',104:'T18 Bull D5',
 103:'T19 6 D20',102:'T20 10 D16',101:'T17 Bull D5',100:'T20 D20',99:'T19 10 D16',
 98:'T20 D19',97:'T19 D20',96:'T20 D18',95:'T19 D19',94:'T18 D20',93:'T19 D18',92:'T20 D16',
 91:'T17 D20',90:'T20 D15',89:'T19 D16',88:'T20 D14',87:'T17 D18',86:'T18 D16',85:'T15 D20',
 84:'T20 D12',83:'T17 D16',82:'T14 D20',81:'T19 D12',80:'T20 D10',79:'T19 D11',78:'T18 D12',
 77:'T19 D10',76:'T20 D8',75:'T17 D12',74:'T14 D16',73:'T19 D8',72:'T16 D12',71:'T13 D16',
 70:'T18 D8',69:'T19 D6',68:'T20 D4',67:'T17 D8',66:'T10 D18',65:'T19 D4',64:'T16 D8',
 63:'T13 D12',62:'T10 D16',61:'T15 D8',60:'20 D20',59:'19 D20',58:'18 D20',57:'17 D20',
 56:'16 D20',55:'15 D20',54:'14 D20',53:'13 D20',52:'20 D16',51:'19 D16',50:'Bull',
 49:'17 D16',48:'16 D16',47:'15 D16',46:'14 D16',45:'13 D16',44:'12 D16',43:'11 D16',
 42:'10 D16',41:'9 D16',40:'D20',39:'19 D10',38:'D19',37:'19 D9',36:'D18',35:'19 D8',
 34:'D17',33:'17 D8',32:'D16',31:'15 D8',30:'D15',29:'13 D8',28:'D14',27:'19 D4',26:'D13',
 25:'17 D4',24:'D12',23:'19 D2',22:'D11',21:'19 D1',20:'D10',19:'11 D4',18:'D9',17:'9 D4',
 16:'D8',15:'7 D4',14:'D7',13:'5 D4',12:'D6',11:'3 D4',10:'D5',9:'1 D4',8:'D4',7:'3 D2',
 6:'D3',5:'1 D2',4:'D2',3:'1 D1',2:'D1'
};

/* =========================== STATE =========================== */
let G = null;        // active game object
const history = [];  // undo stack of deep snapshots

const $  = (s,r=document)=>r.querySelector(s);
const $$ = (s,r=document)=>[...r.querySelectorAll(s)];

/* =========================== SETUP =========================== */
const setup = {
  mode:'x01', start:501, doubleOut:true, legs:1,
  players:['Hráč 1','Hráč 2']
};

function renderPlayers(){
  const box = $('#playerList'); box.innerHTML='';
  setup.players.forEach((name,i)=>{
    const row = document.createElement('div');
    row.className='player-row';
    row.innerHTML =
      `<span class="player-dot" style="background:${PLAYER_COLORS[i%PLAYER_COLORS.length]}"></span>
       <input type="text" value="${escapeHtml(name)}" maxlength="16" placeholder="Meno hráča" data-i="${i}">
       ${setup.players.length>1?`<button class="rm" data-rm="${i}" title="Odobrať">×</button>`:''}`;
    box.appendChild(row);
  });
  box.querySelectorAll('input').forEach(inp=>{
    inp.oninput = e=>{ setup.players[+e.target.dataset.i] = e.target.value; };
  });
  box.querySelectorAll('.rm').forEach(b=>{
    b.onclick = ()=>{ setup.players.splice(+b.dataset.rm,1); renderPlayers(); };
  });
}

$('#addPlayer').onclick = ()=>{
  if(setup.players.length>=8) return;
  setup.players.push('Hráč '+(setup.players.length+1));
  renderPlayers();
};

$$('#modeGrid .mode-btn').forEach(btn=>{
  btn.onclick = ()=>{
    $$('#modeGrid .mode-btn').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    setup.mode = btn.dataset.mode;
    if(btn.dataset.start) setup.start = +btn.dataset.start;
    $('#x01Options').style.display = setup.mode==='x01' ? '' : 'none';
  };
});

$('#doubleOut').onchange = e=> setup.doubleOut = e.target.checked;

$$('.step-btn[data-legs]').forEach(b=>{
  b.onclick = ()=>{
    setup.legs = Math.min(9, Math.max(1, setup.legs + (+b.dataset.legs)));
    $('#legsVal').textContent = setup.legs;
  };
});

$('#startGame').onclick = ()=>{
  setup.players = setup.players.map((n,i)=> (n||'').trim() || 'Hráč '+(i+1));
  startGame();
};

/* =========================== GAME INIT =========================== */
function startGame(){
  const players = setup.players.map((name,i)=>({
    name, color: PLAYER_COLORS[i%PLAYER_COLORS.length],
    legsWon:0,
    // x01
    score:setup.start, dartsThrown:0, totalScored:0, lastTurn:null,
    // cricket
    marks:Object.fromEntries(CRICKET_NUMS.map(n=>[n,0])), points:0
  }));

  G = {
    mode:setup.mode, start:setup.start, doubleOut:setup.doubleOut,
    legsToWin:setup.legs,
    players, cur:0, leg:1,
    turn:[],          // darts in current turn: {v,m,val,label}
    turnStart:null,   // snapshot of active player at turn start (x01 revert on bust)
    over:false, bustFlag:false
  };
  history.length=0;
  pushHistory();

  $('#setup').classList.remove('active');
  $('#game').classList.add('active');
  buildPad();
  render();
}

/* =========================== SNAPSHOT / UNDO =========================== */
function pushHistory(){
  history.push(JSON.stringify(serialize()));
  $('#undoBtn').disabled = history.length<=1;
}
function serialize(){
  return {players:G.players, cur:G.cur, leg:G.leg, turn:G.turn, over:G.over, bustFlag:G.bustFlag};
}
$('#undoBtn').onclick = ()=>{
  if(history.length<=1) return;
  history.pop();                          // drop current
  const snap = JSON.parse(history[history.length-1]);
  Object.assign(G, snap);
  G.turnStart = snapshotActive();
  $('#winOverlay').classList.remove('show');
  $('#undoBtn').disabled = history.length<=1;
  buildPad();
  render();
};

function snapshotActive(){ return JSON.parse(JSON.stringify(G.players[G.cur])); }

/* =========================== EXIT =========================== */
$('#exitBtn').onclick = ()=>{
  if(!G) return;
  if(!G.over && !confirm('Ukončiť hru a vrátiť sa do menu?')) return;
  $('#game').classList.remove('active');
  $('#setup').classList.add('active');
  $('#winOverlay').classList.remove('show');
  G=null;
};

/* =========================== INPUT: keypad =========================== */
let mult = 1;
$$('#multRow .mult-btn').forEach(b=>{
  b.onclick = ()=>{ setMult(+b.dataset.mult); };
});
function setMult(m){
  mult=m;
  $$('#multRow .mult-btn').forEach(x=>x.classList.toggle('active', +x.dataset.mult===m));
}

function buildPad(){
  const pad = $('#pad');
  pad.className = 'pad '+(G.mode==='cricket'?'cricket':'x01');
  pad.innerHTML='';
  const nums = G.mode==='cricket' ? [20,19,18,17,16,15] : range(1,20);
  nums.forEach(n=>{
    const k=document.createElement('button');
    k.className='key'; k.textContent=n; k.dataset.n=n;
    k.onclick=()=>throwDart(n);
    pad.appendChild(k);
  });
  // Bull
  const bull=document.createElement('button');
  bull.className='key bull '+(G.mode==='cricket'?'wide':'bullbar');
  bull.innerHTML='◎ Bull'; bull.dataset.n=25;
  bull.onclick=()=>throwDart(25);
  pad.appendChild(bull);
}

$('#missBtn').onclick = ()=> throwDart(0);
$('#nextBtn').onclick = ()=> nextPlayer();

/* multiplier legality for bull: only single(25) or double(50) */
function throwDart(n){
  if(!G || G.over || G.turn.length>=3 || G.bustFlag) return;
  let m = mult;
  if(n===0) m=1;                          // miss
  if(n===25 && m===3) m=2;                // no triple bull
  const val = n*m;
  const label = n===0 ? '—' : (n===25 ? (m===2?'Bull2':'Bull') : (['','','D','T'][m]||'')+n);

  const dart = {n,m,val,label};
  G.turn.push(dart);

  if(G.mode==='x01') applyX01(dart);
  else applyCricket(dart);

  pushHistory();
  render();

  // auto-advance when 3 darts thrown (x01 stays to show result; user taps Next)
  if(!G.over && G.turn.length===3 && !G.bustFlag){
    $('#nextBtn').classList.add('ready');
  }
}

/* =========================== X01 LOGIC =========================== */
function applyX01(dart){
  const p = G.players[G.cur];
  if(!G.turnStart) G.turnStart = snapshotActive(); // safety
  const remaining = p.score - dart.val;

  // Bust conditions (double-out)
  let bust=false;
  if(remaining<0) bust=true;
  else if(remaining===0 && G.doubleOut && !(dart.m===2)) bust=true; // must finish on a double (Bull=50 counts as double)
  else if(remaining===1 && G.doubleOut) bust=true;

  if(dart.n===25 && dart.m===2) dart._isDouble=true; // bull50 = valid double finish
  const finishesOnDouble = dart.m===2;

  if(bust){
    G.bustFlag=true;
    // revert score to turn start; darts still counted as thrown
    const dartsThisTurn = G.turn.length;
    p.score = G.turnStart.score;
    p.totalScored = G.turnStart.totalScored;
    p.dartsThrown = G.turnStart.dartsThrown + dartsThisTurn;
    p.lastTurn = {sum:0, bust:true};
    return;
  }

  p.score = remaining;
  p.dartsThrown++;
  p.totalScored += dart.val;

  if(remaining===0 && (!G.doubleOut || finishesOnDouble)){
    winLeg();
  }
}

/* =========================== CRICKET LOGIC =========================== */
function applyCricket(dart){
  if(dart.n===0){ return; }               // miss counts as a dart, no effect
  const num = dart.n;
  if(!CRICKET_NUMS.includes(num)) return; // non-scoring number (only via miss safety)
  const p = G.players[G.cur];
  let hits = dart.m;
  if(num===25) hits = dart.m; // bull single=1, double=2

  for(let h=0; h<hits; h++){
    if(p.marks[num] < 3){
      p.marks[num]++;
    } else {
      // number already closed by this player -> score points if any opponent hasn't closed it
      if(!allClosed(num)){
        p.points += num;
      }
    }
  }
  checkCricketWin();
}
function allClosed(num){ return G.players.every(pl=>pl.marks[num]>=3); }
function checkCricketWin(){
  const p=G.players[G.cur];
  const allNumsClosed = CRICKET_NUMS.every(n=>p.marks[n]>=3);
  if(!allNumsClosed) return;
  const maxOther = Math.max(...G.players.filter((_,i)=>i!==G.cur).map(pl=>pl.points));
  if(p.points>=maxOther) winGame(G.cur);
}

/* =========================== TURN / LEG / GAME FLOW =========================== */
function nextPlayer(){
  if(!G || G.over) return;
  // commit x01 turn summary
  if(G.mode==='x01' && !G.bustFlag){
    const sum = G.turn.reduce((a,d)=>a+d.val,0);
    G.players[G.cur].lastTurn = {sum, bust:false};
  }
  G.turn=[];
  G.bustFlag=false;
  $('#nextBtn').classList.remove('ready');
  do { G.cur = (G.cur+1)%G.players.length; } while(false);
  G.turnStart = snapshotActive();
  pushHistory();
  render();
}

function winLeg(){
  const p=G.players[G.cur];
  p.legsWon++;
  G.turn=[];
  if(p.legsWon >= majority()){
    winGame(G.cur);
    return;
  }
  // next leg: reset scores, alternate starter
  setTimeout(()=>{
    G.leg++;
    G.players.forEach(pl=>{ pl.score=G.start; pl.dartsThrown=0; pl.totalScored=0; pl.lastTurn=null; });
    G.cur = (G.leg-1) % G.players.length;   // rotate who starts
    G.bustFlag=false;
    G.turnStart = snapshotActive();
    pushHistory();
    render();
  }, 900);
  render();
}
function majority(){ return Math.floor(G.legsToWin/2)+1; }

function winGame(idx){
  G.over=true;
  const p=G.players[idx];
  render();
  const detail = G.mode==='x01'
    ? `${G.start} · ${p.legsWon} ${plural(p.legsWon,'leg','legy','legov')} · priemer ${avg3(p)} na 3 šípky`
    : `Cricket · ${p.points} ${plural(p.points,'bod','body','bodov')}`;
  $('#winName').textContent = p.name;
  $('#winName').style.color = p.color;
  $('#winDetail').textContent = detail;
  $('.win-burst').style.background =
    `radial-gradient(circle, ${hexA(p.color,.32)}, transparent 62%)`;
  setTimeout(()=> $('#winOverlay').classList.add('show'), 260);
}

$('#rematchBtn').onclick = ()=>{ $('#winOverlay').classList.remove('show'); startGame(); };
$('#newGameBtn').onclick = ()=>{
  $('#winOverlay').classList.remove('show');
  $('#game').classList.remove('active');
  $('#setup').classList.add('active');
  G=null;
};

/* =========================== RENDER =========================== */
function render(){
  if(!G) return;
  // head
  $('#gameTitle').textContent = G.mode==='x01' ? String(G.start) : 'Cricket';
  const legTxt = majority()>1 ? ` · leg ${G.leg} (do ${majority()})` : '';
  $('#gameSub').textContent = (G.mode==='x01'
      ? (G.doubleOut?'double out':'straight out') : 'zavri 15–20 + bull') + legTxt;

  // board
  if(G.mode==='x01') renderX01(); else renderCricket();

  // turn bar
  renderTurnBar();

  // pad availability (bull triple etc handled in throwDart)
  const disable = G.over || G.turn.length>=3 || G.bustFlag;
  $$('#pad .key').forEach(k=>k.disabled=disable);
  $('#missBtn').disabled = disable;
  $('#nextBtn').disabled = G.over;
}

function renderX01(){
  const board=$('#board');
  board.className='board';
  let html='<div class="x01-cards">';
  G.players.forEach((p,i)=>{
    const active = i===G.cur && !G.over;
    const co = checkoutHint(p.score);
    const legDots = majority()>1
      ? `<span class="p-legs">${Array.from({length:majority()},(_,k)=>`<i class="${k<p.legsWon?'on':''}"></i>`).join('')}</span>`:'';
    const last = p.lastTurn
      ? (p.lastTurn.bust ? '<span style="color:var(--red)">BUST</span>' : `−${p.lastTurn.sum}`)
      : '—';
    html+=`
    <div class="pcard ${active?'active':''}" style="--clr:${p.color}">
      <div class="p-id">
        <span class="p-name">${escapeHtml(p.name)}</span>
        ${legDots}
      </div>
      <div class="p-score">${p.score}</div>
      <div class="p-meta">
        <span>posledný <b>${last}</b></span>
        <span>Ø3 <b>${avg3(p)}</b></span>
        <span>šípky <b>${p.dartsThrown}</b></span>
        ${co?`<span class="checkout-hint">checkout <b>${co}</b></span>`:''}
      </div>
    </div>`;
  });
  html+='</div>';
  board.innerHTML=html;
}

function renderCricket(){
  const board=$('#board');
  board.className='board';
  const leadPts = Math.max(...G.players.map(p=>p.points));
  let html='<div class="cricket-wrap"><table class="cricket-grid"><thead><tr><th></th>';
  G.players.forEach((p,i)=>{
    html+=`<th class="${i===G.cur&&!G.over?'active':''}"><span class="cname" style="color:${i===G.cur&&!G.over?p.color:''}">${escapeHtml(p.name)}</span></th>`;
  });
  html+='</tr></thead><tbody>';
  CRICKET_NUMS.forEach(num=>{
    const label = num===25?'BULL':num;
    html+=`<tr><th class="num-label">${label}${num===25?'<small>◎</small>':''}</th>`;
    const closedAll = allClosed(num);
    G.players.forEach((p,i)=>{
      const m=p.marks[num];
      html+=`<td class="mark-cell ${i===G.cur&&!G.over?'col-active':''} ${closedAll?'closed-all':''}">${markSVG(m,p.color)}</td>`;
    });
    html+='</tr>';
  });
  html+='</tbody><tfoot><tr><th>Body</th>';
  G.players.forEach(p=>{
    html+=`<td class="${p.points===leadPts&&leadPts>0?'lead':''}" style="${p.points===leadPts&&leadPts>0?'color:'+p.color:''}">${p.points}</td>`;
  });
  html+='</tr></tfoot></table></div>';
  board.innerHTML=html;
}

function markSVG(m,color){
  // 0 nothing, 1 "/", 2 "X", 3 circle around X
  return `<span class="marks"><svg viewBox="0 0 34 30">
    <line class="m ${m>=1?'show':''}" x1="6" y1="24" x2="28" y2="6" style="stroke:${color}"/>
    <line class="m ${m>=2?'show':''}" x1="6" y1="6" x2="28" y2="24" style="stroke:${color}"/>
    <circle class="m ${m>=3?'show':''}" cx="17" cy="15" r="12" style="stroke:${color}"/>
  </svg></span>`;
}

function renderTurnBar(){
  const slots=$$('#dartSlots .dart-slot');
  slots.forEach((s,i)=>{
    const d=G.turn[i];
    s.className='dart-slot'+(d?' filled':'')+(G.bustFlag?' bust':'');
    s.textContent = d ? d.label : '';
  });
  const meta=$('#turnMeta');
  if(G.bustFlag){ meta.className='turn-meta bust'; meta.innerHTML='<b>BUST</b> — ťuk na Ďalší'; return; }
  meta.className='turn-meta';
  if(G.mode==='x01'){
    const sum=G.turn.reduce((a,d)=>a+d.val,0);
    const rem=G.players[G.cur].score;
    meta.innerHTML = G.turn.length ? `hod <b>${sum}</b> · zostáva ${rem}` : (G.over?'':`na rade <b>${escapeHtml(G.players[G.cur].name)}</b>`);
  } else {
    meta.innerHTML = G.over?'':`na rade <b style="color:${G.players[G.cur].color}">${escapeHtml(G.players[G.cur].name)}</b>`;
  }
}

/* =========================== HELPERS =========================== */
function checkoutHint(score){
  if(G.mode!=='x01') return '';
  if(score>170 || score<2) return '';
  if(G.doubleOut) return CHECKOUTS[score]||'';
  return score<=60||score===50 ? (score===50?'Bull':(''+score)) : '';
}
function avg3(p){ if(!p.dartsThrown) return '0.0'; return (p.totalScored/p.dartsThrown*3).toFixed(1); }
function range(a,b){ return Array.from({length:b-a+1},(_,i)=>a+i); }
function escapeHtml(s){ return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function hexA(hex,a){ const h=hex.replace('#',''); const n=parseInt(h,16); return `rgba(${(n>>16)&255},${(n>>8)&255},${n&255},${a})`; }
function plural(n,one,few,many){ if(n===1) return one; if(n>=2&&n<=4) return few; return many; }

/* =========================== BOOT =========================== */
renderPlayers();
$('#legsVal').textContent = setup.legs;
