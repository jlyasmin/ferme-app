import json, os, hashlib, uuid
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

USERS_FILE = "users.json"
DATA_FILE  = "data.json"
sessions   = {}

# ── helpers ────────────────────────────────────────────────────────────────
def load(f, d):
    return json.load(open(f, encoding="utf-8")) if os.path.exists(f) else d

def save(f, v):
    json.dump(v, open(f,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

def sha(s): return hashlib.sha256(s.encode()).hexdigest()

def new_session(u):
    t = str(uuid.uuid4()); sessions[t] = u; return t

def get_user(token): return sessions.get(token)

def init():
    if not os.path.exists(USERS_FILE): save(USERS_FILE, {})
    if not os.path.exists(DATA_FILE):  save(DATA_FILE, {})

def export_excel(username):
    users = load(USERS_FILE, {})
    data  = load(DATA_FILE, {})
    animaux = data.get(username, [])
    nom = users.get(username,{}).get("nom","Fermier")
    wb = openpyxl.Workbook(); ws = wb.active
    ws.title = "Animaux"
    hfill = PatternFill("solid", start_color="2E7D32")
    hfont = Font(bold=True, color="FFFFFF", name="Arial", size=11)
    thin  = Border(*[Side(style="thin")]*0,
                   left=Side(style="thin"), right=Side(style="thin"),
                   top=Side(style="thin"),  bottom=Side(style="thin"))
    for c,(h) in enumerate(["N° Animal","Espèce","Poids (kg)","Dernière MAJ"],1):
        cell = ws.cell(1,c,h); cell.font=hfont; cell.fill=hfill
        cell.alignment=Alignment(horizontal="center")
    for r,a in enumerate(animaux,2):
        fill = PatternFill("solid", start_color="F1F8E9" if r%2==0 else "FFFFFF")
        for c,v in enumerate([a["id"],a["espece"],a["poids"],a["date"]],1):
            cell = ws.cell(r,c,v); cell.border=thin
            cell.font=Font(name="Arial",size=10)
            cell.fill=fill; cell.alignment=Alignment(horizontal="center")
    for col,w in zip("ABCD",[14,12,14,16]): ws.column_dimensions[col].width=w
    path = f"/tmp/animaux_{username}.xlsx"; wb.save(path); return path

# ── HTML ───────────────────────────────────────────────────────────────────
CSS_BASE = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
     background:linear-gradient(135deg,#1B5E20 0%,#4CAF50 100%);
     min-height:100vh;display:flex;align-items:center;justify-content:center;}
.card{background:white;border-radius:18px;padding:40px 36px;width:380px;
      box-shadow:0 24px 64px rgba(0,0,0,0.22);}
.logo{text-align:center;margin-bottom:28px;}
.logo-icon{font-size:52px;}
.logo h1{font-size:22px;font-weight:700;color:#1B5E20;margin-top:8px;}
.logo p{font-size:13px;color:#999;margin-top:4px;}
.tabs{display:flex;border:1.5px solid #e0e0e0;border-radius:10px;
      overflow:hidden;margin-bottom:22px;}
.tab{flex:1;padding:10px;text-align:center;font-size:14px;font-weight:600;
     cursor:pointer;background:white;color:#888;border:none;transition:all .2s;}
.tab.active{background:#2E7D32;color:white;}
.panel{display:none;}.panel.active{display:block;}
.fg{margin-bottom:14px;}
label{display:block;font-size:12px;font-weight:600;color:#555;margin-bottom:5px;}
input{width:100%;height:44px;border:1.5px solid #e0e0e0;border-radius:10px;
      padding:0 14px;font-size:15px;outline:none;transition:border-color .2s;}
input:focus{border-color:#4CAF50;}
.btn{width:100%;height:46px;background:#2E7D32;color:white;border:none;
     border-radius:10px;font-size:16px;font-weight:700;cursor:pointer;
     transition:background .2s;margin-top:4px;}
.btn:hover{background:#1B5E20;}
.msg{padding:10px 14px;border-radius:8px;font-size:13px;
     font-weight:600;margin-bottom:14px;display:none;}
.msg.ok{background:#E8F5E9;color:#2E7D32;border:1px solid #A5D6A7;display:block;}
.msg.err{background:#FFEBEE;color:#C62828;border:1px solid #EF9A9A;display:block;}
.footer{text-align:center;margin-top:18px;font-size:12px;color:#ccc;}
"""

PAGE_AUTH = f"""<!DOCTYPE html><html lang="fr"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ferme — Connexion</title><style>{CSS_BASE}</style></head><body>
<div class="card">
  <div class="logo">
    <div class="logo-icon">🐄</div>
    <h1>Gestion Ferme</h1>
    <p>Suivi des poids des animaux</p>
  </div>
  <div class="tabs">
    <button class="tab active" onclick="showTab('login',this)">Se connecter</button>
    <button class="tab" onclick="showTab('register',this)">Créer un compte</button>
  </div>
  <div id="msg" class="msg"></div>

  <!-- LOGIN -->
  <div id="login" class="panel active">
    <div class="fg"><label>Identifiant</label>
      <input id="l-user" placeholder="ex: ahmed123"/></div>
    <div class="fg"><label>Mot de passe</label>
      <input id="l-mdp" type="password" placeholder="••••••••"
             onkeydown="if(event.key==='Enter')login()"/></div>
    <button class="btn" onclick="login()">Se connecter</button>
  </div>

  <!-- REGISTER -->
  <div id="register" class="panel">
    <div class="fg"><label>Nom complet</label>
      <input id="r-nom" placeholder="ex: Ahmed Ben Ali"/></div>
    <div class="fg"><label>Identifiant (sans espaces)</label>
      <input id="r-user" placeholder="ex: ahmed123"/></div>
    <div class="fg"><label>Mot de passe</label>
      <input id="r-mdp" type="password" placeholder="minimum 4 caractères"/></div>
    <div class="fg"><label>Confirmer le mot de passe</label>
      <input id="r-mdp2" type="password" placeholder="répète le mot de passe"
             onkeydown="if(event.key==='Enter')register()"/></div>
    <button class="btn" onclick="register()">Créer mon compte</button>
  </div>

  <div class="footer">Système de gestion des animaux</div>
</div>
<script>
function showTab(id,btn){{
  document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  btn.classList.add('active');
  hide();
}}
function show(msg,ok){{
  const e=document.getElementById('msg');
  e.textContent=msg;e.className='msg '+(ok?'ok':'err');
}}
function hide(){{document.getElementById('msg').className='msg';}}

async function login(){{
  const u=document.getElementById('l-user').value.trim();
  const m=document.getElementById('l-mdp').value;
  if(!u||!m){{show('Remplis tous les champs.',false);return;}}
  const r=await post('/api/login',{{username:u,mdp:m}});
  if(r.ok){{
    localStorage.setItem('token',r.token);
    localStorage.setItem('nom',r.nom);
    localStorage.setItem('username',r.username);
    window.location.href='/app';
  }}else show(r.msg||'Identifiant ou mot de passe incorrect.',false);
}}

async function register(){{
  const nom=document.getElementById('r-nom').value.trim();
  const u=document.getElementById('r-user').value.trim();
  const m=document.getElementById('r-mdp').value;
  const m2=document.getElementById('r-mdp2').value;
  if(!nom||!u||!m||!m2){{show('Remplis tous les champs.',false);return;}}
  if(m!==m2){{show('Les mots de passe ne correspondent pas.',false);return;}}
  if(m.length<4){{show('Mot de passe trop court (minimum 4 caractères).',false);return;}}
  if(!/^[a-zA-Z0-9_]+$/.test(u)){{show('Identifiant : lettres, chiffres et _ uniquement.',false);return;}}
  const r=await post('/api/register',{{nom,username:u,mdp:m}});
  if(r.ok){{
    show('Compte créé ! Tu peux maintenant te connecter.',true);
    showTab('login',document.querySelectorAll('.tab')[0]);
    document.getElementById('l-user').value=u;
  }}else show(r.msg||'Erreur lors de la création.',false);
}}

async function post(url,body){{
  const r=await fetch(url,{{method:'POST',
    headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify(body)}});
  return r.json();
}}
</script></body></html>"""

APP_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
     background:#f5f5f0;color:#1a1a18;min-height:100vh;}
.topbar{background:#2E7D32;color:white;padding:13px 20px;
        display:flex;align-items:center;justify-content:space-between;
        position:sticky;top:0;z-index:10;}
.tl{display:flex;align-items:center;gap:10px;}
.tl h1{font-size:17px;font-weight:700;}
.tl p{font-size:12px;opacity:.8;}
.tr{display:flex;align-items:center;gap:8px;}
.btn-out{background:rgba(255,255,255,.2);color:white;border:none;
         padding:7px 13px;border-radius:8px;font-size:13px;cursor:pointer;}
.btn-out:hover{background:rgba(255,255,255,.3);}
.btn-xl{background:#FF8F00;color:white;border:none;
        padding:7px 13px;border-radius:8px;font-size:13px;
        cursor:pointer;font-weight:600;text-decoration:none;
        display:inline-flex;align-items:center;gap:5px;}
.btn-xl:hover{background:#E65100;}
.wrap{max-width:780px;margin:0 auto;padding:20px 14px;}
.toast{position:fixed;top:14px;right:14px;padding:11px 16px;
       border-radius:9px;font-size:13px;font-weight:600;
       display:none;z-index:99;box-shadow:0 4px 14px rgba(0,0,0,.15);}
.toast.show{display:flex;align-items:center;gap:7px;}
.tok{background:#E8F5E9;color:#1B5E20;border:1px solid #A5D6A7;}
.terr{background:#FFEBEE;color:#C62828;border:1px solid #EF9A9A;}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:18px;}
.stat{background:white;border-radius:10px;padding:14px 16px;
      box-shadow:0 1px 3px rgba(0,0,0,.07);}
.sl{font-size:11px;color:#888;margin-bottom:4px;}
.sv{font-size:22px;font-weight:800;color:#2E7D32;}
.ss{font-size:11px;color:#bbb;margin-top:2px;}
.card{background:white;border-radius:12px;padding:18px 20px;
      box-shadow:0 1px 3px rgba(0,0,0,.07);margin-bottom:18px;}
.card h2{font-size:14px;font-weight:700;color:#333;margin-bottom:14px;
         display:flex;align-items:center;gap:8px;}
.card h2::before{content:'';width:4px;height:15px;background:#2E7D32;
                 border-radius:2px;display:inline-block;}
/* Formulaire pesée */
.fr3{display:grid;grid-template-columns:1fr 1fr auto;gap:10px;align-items:end;}
/* Formulaire ajout animal */
.fr5{display:grid;grid-template-columns:1fr 1fr 1fr 1fr auto;gap:8px;align-items:end;}
.fg{display:flex;flex-direction:column;gap:5px;}
label{font-size:12px;font-weight:600;color:#555;}
input[type=text],input[type=number],select{
  height:40px;border:1.5px solid #e0e0e0;border-radius:9px;
  padding:0 11px;font-size:14px;background:#fafafa;
  outline:none;transition:border-color .2s;width:100%;}
input:focus,select:focus{border-color:#4CAF50;background:white;}
.bsave{height:40px;padding:0 16px;background:#2E7D32;color:white;
       border:none;border-radius:9px;font-size:14px;font-weight:700;
       cursor:pointer;white-space:nowrap;}
.bsave:hover{background:#1B5E20;}
.badd{height:40px;padding:0 14px;background:#1565C0;color:white;
      border:none;border-radius:9px;font-size:13px;font-weight:700;cursor:pointer;}
.badd:hover{background:#0D47A1;}
.bdel{background:none;border:none;color:#EF5350;font-size:16px;
      cursor:pointer;padding:4px 8px;border-radius:6px;}
.bdel:hover{background:#FFEBEE;}
/* Filtre */
.filters{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;}
.fb{padding:5px 13px;border:1.5px solid #ddd;border-radius:20px;
    background:white;font-size:12px;cursor:pointer;transition:all .15s;}
.fb:hover{border-color:#4CAF50;color:#2E7D32;}
.fb.active{background:#2E7D32;color:white;border-color:#2E7D32;}
/* Table */
table{width:100%;border-collapse:collapse;}
thead th{background:#f8f8f6;padding:10px 12px;text-align:left;
         font-size:11px;font-weight:700;color:#777;border-bottom:1px solid #eee;
         text-transform:uppercase;letter-spacing:.4px;}
tbody tr{border-bottom:.5px solid #f0f0ec;transition:background .1s;}
tbody tr:last-child{border-bottom:none;}
tbody tr:hover{background:#f9fdf9;}
tbody tr.hl{background:#E8F5E9!important;}
tbody td{padding:9px 12px;font-size:13px;}
.badge{display:inline-block;padding:2px 9px;border-radius:12px;font-size:11px;font-weight:700;}
.bv{background:#E3F2FD;color:#1565C0;}
.bm{background:#FFF8E1;color:#E65100;}
.bc{background:#F3E5F5;color:#6A1B9A;}
.fw{font-weight:700;}.muted{color:#aaa;font-size:11px;}
.empty{text-align:center;padding:30px;color:#bbb;font-size:14px;}
@media(max-width:600px){
  .fr3,.fr5{grid-template-columns:1fr;}
  .stats{grid-template-columns:1fr 1fr;}
}
"""

PAGE_APP = f"""<!DOCTYPE html><html lang="fr"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ferme — Mon troupeau</title><style>{APP_CSS}</style></head><body>
<div class="topbar">
  <div class="tl">
    <span style="font-size:26px">🐄</span>
    <div><h1 id="tnon">Ferme</h1><p id="trole">Mon troupeau</p></div>
  </div>
  <div class="tr">
    <a class="btn-xl" id="xl-link" href="#" onclick="telechargerExcel()">📊 Excel</a>
    <button class="btn-out" onclick="logout()">⬅ Déconnexion</button>
  </div>
</div>

<div class="wrap">
  <div class="toast" id="toast"></div>
  <div class="stats" id="stats"></div>

  <!-- Pesée -->
  <div class="card">
    <h2>⚖️ Enregistrer une pesée</h2>
    <div class="fr3">
      <div class="fg"><label>Animal</label>
        <select id="sel"><option value="">— Choisir un animal —</option></select></div>
      <div class="fg"><label>Nouveau poids (kg)</label>
        <input type="number" id="inp" placeholder="ex: 465" min="1" max="2000" step="0.5"/></div>
      <div class="fg"><button class="bsave" onclick="peser()">💾 Enregistrer</button></div>
    </div>
  </div>

  <!-- Ajout animal -->
  <div class="card">
    <h2>➕ Ajouter un animal</h2>
    <div class="fr5">
      <div class="fg"><label>N° Animal</label>
        <input type="text" id="a-id" placeholder="ex: ANI-030"/></div>
      <div class="fg"><label>Espèce</label>
        <select id="a-esp">
          <option>Vache</option><option>Mouton</option><option>Chèvre</option>
        </select></div>
      <div class="fg"><label>Poids initial (kg)</label>
        <input type="number" id="a-p" placeholder="ex: 450" min="1"/></div>
      <div class="fg"><label>Date (optionnel)</label>
        <input type="text" id="a-d" placeholder="2026-06-29"/></div>
      <div class="fg"><button class="badd" onclick="ajouter()">+ Ajouter</button></div>
    </div>
  </div>

  <!-- Tableau -->
  <div class="card">
    <h2>📋 Mon troupeau</h2>
    <div class="filters">
      <button class="fb active" onclick="filtrer('tous',this)">Tous</button>
      <button class="fb" onclick="filtrer('Vache',this)">🐄 Vaches</button>
      <button class="fb" onclick="filtrer('Mouton',this)">🐑 Moutons</button>
      <button class="fb" onclick="filtrer('Chèvre',this)">🐐 Chèvres</button>
    </div>
    <table><thead><tr>
      <th>N° Animal</th><th>Espèce</th><th>Poids (kg)</th>
      <th>Dernière MAJ</th><th>Action</th>
    </tr></thead><tbody id="tb"></tbody></table>
  </div>
</div>

<script>
const token=localStorage.getItem('token');
const nom=localStorage.getItem('nom');
const username=localStorage.getItem('username');
if(!token){{window.location.href='/';}}
document.getElementById('tnon').textContent='Bonjour, '+nom+' 👋';

let animaux=[],filtre='tous',lastHL=null;

async function api(method,url,body){{
  const o={{method,headers:{{'Content-Type':'application/json','X-Token':token}}}};
  if(body)o.body=JSON.stringify(body);
  const r=await fetch(url,o);return r.json();
}}

async function charger(){{
  const r=await api('GET','/api/animaux');
  animaux=r.animaux||[];
  remplirSel();afficherStats();afficherTable(lastHL);
}}

function remplirSel(){{
  const s=document.getElementById('sel');
  s.innerHTML='<option value="">— Choisir un animal —</option>';
  animaux.forEach(a=>{{
    const o=document.createElement('option');
    o.value=a.id;
    o.textContent=a.id+' — '+a.espece+' ('+a.poids.toFixed(1)+' kg)';
    s.appendChild(o);
  }});
}}

function afficherStats(){{
  const n=animaux.length;
  const moy=n?animaux.reduce((s,a)=>s+a.poids,0)/n:0;
  const auj=new Date().toISOString().split('T')[0];
  const p=animaux.filter(a=>a.date===auj).length;
  document.getElementById('stats').innerHTML=`
    <div class="stat"><div class="sl">Mes animaux</div>
      <div class="sv">${{n}}</div><div class="ss">dans mon troupeau</div></div>
    <div class="stat"><div class="sl">Poids moyen</div>
      <div class="sv">${{moy.toFixed(1)}}</div><div class="ss">kg / animal</div></div>
    <div class="stat"><div class="sl">Pesées aujourd'hui</div>
      <div class="sv">${{p}}</div><div class="ss">mises à jour</div></div>`;
}}

function afficherTable(hl){{
  const f=filtre==='tous'?animaux:animaux.filter(a=>a.espece===filtre);
  const b=e=>e==='Vache'?'bv':e==='Mouton'?'bm':'bc';
  document.getElementById('tb').innerHTML=f.length?
    f.map(a=>`<tr class="${{a.id===hl?'hl':''}}">
      <td class="fw">${{a.id}}</td>
      <td><span class="badge ${{b(a.espece)}}">${{a.espece}}</span></td>
      <td class="fw">${{a.poids.toFixed(1)}} kg</td>
      <td class="muted">${{a.date}}</td>
      <td><button class="bdel" onclick="supprimer('${{a.id}}')"
          title="Supprimer">🗑</button></td>
    </tr>`).join(''):
    '<tr><td colspan="5" class="empty">Aucun animal — ajoutes-en un !</td></tr>';
}}

function filtrer(f,btn){{
  filtre=f;
  document.querySelectorAll('.fb').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');afficherTable(lastHL);
}}

function toast(msg,ok=true){{
  const t=document.getElementById('toast');
  t.textContent=msg;t.className='toast show '+(ok?'tok':'terr');
  setTimeout(()=>t.className='toast',4000);
}}

async function peser(){{
  const id=document.getElementById('sel').value;
  const p=parseFloat(document.getElementById('inp').value);
  if(!id){{toast('⚠️ Sélectionne un animal.',false);return;}}
  if(!p||p<=0){{toast('⚠️ Saisis un poids valide.',false);return;}}
  const r=await api('POST','/api/update',{{id,poids:p}});
  if(r.ok){{
    lastHL=id;await charger();afficherTable(id);
    const d=p-r.ancien;const s=d>=0?'+':'';
    toast('✅ '+id+' : '+p.toFixed(1)+' kg ('+s+d.toFixed(1)+' kg)');
    document.getElementById('sel').value='';
    document.getElementById('inp').value='';
    setTimeout(()=>{{lastHL=null;afficherTable();}},4000);
  }}else toast('❌ Erreur.',false);
}}

async function ajouter(){{
  const id=document.getElementById('a-id').value.trim().toUpperCase();
  const esp=document.getElementById('a-esp').value;
  const p=parseFloat(document.getElementById('a-p').value);
  const d=document.getElementById('a-d').value.trim()||
           new Date().toISOString().split('T')[0];
  if(!id){{toast('⚠️ Saisis un numéro d\'animal.',false);return;}}
  if(!p||p<=0){{toast('⚠️ Saisis un poids valide.',false);return;}}
  const r=await api('POST','/api/ajouter',{{id,espece:esp,poids:p,date:d}});
  if(r.ok){{
    toast('✅ Animal '+id+' ajouté !');
    document.getElementById('a-id').value='';
    document.getElementById('a-p').value='';
    document.getElementById('a-d').value='';
    await charger();
  }}else toast('❌ '+(r.msg||'Erreur'),false);
}}

async function supprimer(id){{
  if(!confirm('Supprimer '+id+' ?'))return;
  const r=await api('POST','/api/supprimer',{{id}});
  if(r.ok){{toast('🗑 '+id+' supprimé.');await charger();}}
  else toast('❌ Erreur.',false);
}}

async function telechargerExcel(){{
  const r=await fetch('/api/excel',{{headers:{{'X-Token':token}}}});
  const blob=await r.blob();
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  a.href=url;a.download='animaux_'+username+'.xlsx';a.click();
  URL.revokeObjectURL(url);
  toast('📊 Fichier Excel téléchargé !');
}}

function logout(){{localStorage.clear();window.location.href='/';}}
charger();
</script></body></html>"""

# ── Serveur ─────────────────────────────────────────────────────────────────
class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def tok(self): return self.headers.get("X-Token","")
    def usr(self): return get_user(self.tok())
    def body(self):
        n=int(self.headers.get("Content-Length",0))
        return json.loads(self.rfile.read(n)) if n else {}

    def json(self,d,s=200):
        b=json.dumps(d,ensure_ascii=False).encode()
        self.send_response(s)
        self.send_header("Content-Type","application/json;charset=utf-8")
        self.send_header("Content-Length",len(b))
        self.end_headers(); self.wfile.write(b)

    def html(self,h):
        b=h.encode()
        self.send_response(200)
        self.send_header("Content-Type","text/html;charset=utf-8")
        self.send_header("Content-Length",len(b))
        self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        p=urlparse(self.path).path
        u=self.usr()
        if p=="/":           self.html(PAGE_AUTH)
        elif p=="/app":
            if not u: self.send_response(302);self.send_header("Location","/");self.end_headers()
            else: self.html(PAGE_APP)
        elif p=="/api/animaux":
            if not u: self.json({"error":"non autorisé"},401);return
            data=load(DATA_FILE,{})
            self.json({"animaux":data.get(u,[])})
        elif p=="/api/excel":
            if not u: self.json({"error":"non autorisé"},401);return
            path=export_excel(u)
            with open(path,"rb") as f: content=f.read()
            fname=f"animaux_{u}.xlsx"
            self.send_response(200)
            self.send_header("Content-Type","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            self.send_header("Content-Disposition",f'attachment; filename="{fname}"')
            self.send_header("Content-Length",len(content))
            self.end_headers(); self.wfile.write(content)
        else: self.send_response(404);self.end_headers()

    def do_POST(self):
        p=urlparse(self.path).path
        b=self.body()

        if p=="/api/register":
            nom=b.get("nom","").strip()
            un=b.get("username","").strip()
            mdp=b.get("mdp","")
            users=load(USERS_FILE,{})
            if not nom or not un or not mdp:
                self.json({"ok":False,"msg":"Champs manquants"});return
            if un in users:
                self.json({"ok":False,"msg":"Cet identifiant est déjà utilisé."});return
            import re
            if not re.match(r'^[a-zA-Z0-9_]+$',un):
                self.json({"ok":False,"msg":"Identifiant invalide."});return
            users[un]={"nom":nom,"mdp":sha(mdp)}
            save(USERS_FILE,users)
            data=load(DATA_FILE,{})
            data[un]=[]
            save(DATA_FILE,data)
            self.json({"ok":True})

        elif p=="/api/login":
            un=b.get("username","").strip()
            mdp=b.get("mdp","")
            users=load(USERS_FILE,{})
            info=users.get(un,{})
            if info and info.get("mdp")==sha(mdp):
                t=new_session(un)
                self.json({"ok":True,"token":t,"nom":info["nom"],"username":un})
            else:
                self.json({"ok":False,"msg":"Identifiant ou mot de passe incorrect."})

        elif p=="/api/update":
            u=self.usr()
            if not u: self.json({"ok":False});return
            data=load(DATA_FILE,{})
            for a in data.get(u,[]):
                if a["id"]==b.get("id"):
                    ancien=a["poids"]
                    a["poids"]=float(b["poids"])
                    a["date"]=date.today().isoformat()
                    save(DATA_FILE,data)
                    self.json({"ok":True,"ancien":ancien});return
            self.json({"ok":False})

        elif p=="/api/ajouter":
            u=self.usr()
            if not u: self.json({"ok":False});return
            data=load(DATA_FILE,{})
            if u not in data: data[u]=[]
            for a in data[u]:
                if a["id"]==b.get("id"):
                    self.json({"ok":False,"msg":"Ce numéro existe déjà."});return
            data[u].append({
                "id":b.get("id","").upper(),
                "espece":b.get("espece","Vache"),
                "poids":float(b.get("poids",0)),
                "date":b.get("date",date.today().isoformat())
            })
            save(DATA_FILE,data)
            self.json({"ok":True})

        elif p=="/api/supprimer":
            u=self.usr()
            if not u: self.json({"ok":False});return
            data=load(DATA_FILE,{})
            avant=len(data.get(u,[]))
            data[u]=[a for a in data.get(u,[]) if a["id"]!=b.get("id")]
            if len(data[u])<avant:
                save(DATA_FILE,data);self.json({"ok":True})
            else: self.json({"ok":False})

        else: self.send_response(404);self.end_headers()

if __name__=="__main__":
    init()
    PORT=int(os.environ.get("PORT",5000))
    server=HTTPServer(("",PORT),H)
    print(f"\n🌿 Application Ferme démarrée !")
    print(f"   👉 http://localhost:{PORT}")
    print(f"   ⏹️  Ctrl+C pour arrêter\n")
    try: server.serve_forever()
    except KeyboardInterrupt: print("\n✅ Arrêtée.")
