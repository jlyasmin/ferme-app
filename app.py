import json
import os
import hashlib
import uuid
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

# ─── BASE DE DONNÉES (fichiers JSON simples) ───────────────────────────────
USERS_FILE  = "users.json"
DATA_FILE   = "data.json"

def charger_json(fichier, defaut):
    if os.path.exists(fichier):
        with open(fichier, "r", encoding="utf-8") as f:
            return json.load(f)
    return defaut

def sauver_json(fichier, contenu):
    with open(fichier, "w", encoding="utf-8") as f:
        json.dump(contenu, f, ensure_ascii=False, indent=2)

def init_donnees():
    # Utilisateurs par défaut si le fichier n'existe pas
    if not os.path.exists(USERS_FILE):
        users = {
            "admin": {
                "nom": "Administrateur",
                "mot_de_passe": hashlib.sha256("admin123".encode()).hexdigest(),
                "role": "admin"
            },
            "fermier1": {
                "nom": "Ahmed Ben Ali",
                "mot_de_passe": hashlib.sha256("1234".encode()).hexdigest(),
                "role": "fermier"
            },
            "fermier2": {
                "nom": "Mohamed Trabelsi",
                "mot_de_passe": hashlib.sha256("1234".encode()).hexdigest(),
                "role": "fermier"
            },
            "fermier3": {
                "nom": "Sami Gharbi",
                "mot_de_passe": hashlib.sha256("1234".encode()).hexdigest(),
                "role": "fermier"
            }
        }
        sauver_json(USERS_FILE, users)

    if not os.path.exists(DATA_FILE):
        data = {
            "fermier1": [
                {"id": "ANI-001", "espece": "Vache",  "poids": 450.0, "date": "2026-06-01"},
                {"id": "ANI-002", "espece": "Mouton", "poids": 65.0,  "date": "2026-06-01"},
                {"id": "ANI-003", "espece": "Vache",  "poids": 480.0, "date": "2026-06-05"},
            ],
            "fermier2": [
                {"id": "ANI-010", "espece": "Chèvre", "poids": 42.0,  "date": "2026-06-03"},
                {"id": "ANI-011", "espece": "Mouton", "poids": 70.0,  "date": "2026-06-02"},
            ],
            "fermier3": [
                {"id": "ANI-020", "espece": "Vache",  "poids": 510.0, "date": "2026-06-01"},
                {"id": "ANI-021", "espece": "Chèvre", "poids": 38.0,  "date": "2026-06-04"},
            ]
        }
        sauver_json(DATA_FILE, data)

# Sessions actives en mémoire
sessions = {}

def creer_session(username):
    token = str(uuid.uuid4())
    sessions[token] = {"username": username, "cree": datetime.now().isoformat()}
    return token

def verifier_session(token):
    return sessions.get(token, {}).get("username")

def hacher(mdp):
    return hashlib.sha256(mdp.encode()).hexdigest()

# ─── HTML PAGES ────────────────────────────────────────────────────────────
PAGE_LOGIN = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ferme — Connexion</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
     background:linear-gradient(135deg,#1B5E20,#4CAF50);
     min-height:100vh;display:flex;align-items:center;justify-content:center;}
.card{background:white;border-radius:16px;padding:40px 36px;width:340px;
      box-shadow:0 20px 60px rgba(0,0,0,0.2);}
.logo{text-align:center;margin-bottom:28px;}
.logo-icon{font-size:48px;}
.logo h1{font-size:22px;font-weight:600;color:#1B5E20;margin-top:8px;}
.logo p{font-size:13px;color:#888;margin-top:4px;}
.form-group{margin-bottom:16px;}
label{display:block;font-size:12px;font-weight:600;color:#555;margin-bottom:6px;}
input{width:100%;height:44px;border:1.5px solid #e0e0e0;border-radius:10px;
      padding:0 14px;font-size:15px;outline:none;transition:border-color 0.2s;}
input:focus{border-color:#4CAF50;}
.btn{width:100%;height:46px;background:#2E7D32;color:white;border:none;
     border-radius:10px;font-size:16px;font-weight:600;cursor:pointer;
     margin-top:8px;transition:background 0.2s;}
.btn:hover{background:#1B5E20;}
.error{background:#FFEBEE;color:#C62828;padding:10px 14px;border-radius:8px;
       font-size:13px;margin-bottom:16px;display:none;}
.error.show{display:block;}
.footer{text-align:center;margin-top:20px;font-size:12px;color:#aaa;}
</style>
</head>
<body>
<div class="card">
  <div class="logo">
    <div class="logo-icon">🐄</div>
    <h1>Gestion Ferme</h1>
    <p>Suivi des poids des animaux</p>
  </div>
  <div id="err" class="error">Identifiant ou mot de passe incorrect.</div>
  <div class="form-group">
    <label>Identifiant</label>
    <input type="text" id="user" placeholder="ex: fermier1" />
  </div>
  <div class="form-group">
    <label>Mot de passe</label>
    <input type="password" id="mdp" placeholder="••••••••"
           onkeydown="if(event.key==='Enter')login()" />
  </div>
  <button class="btn" onclick="login()">Se connecter</button>
  <div class="footer">Système de gestion des animaux • OEP</div>
</div>
<script>
async function login(){
  const u=document.getElementById('user').value.trim();
  const m=document.getElementById('mdp').value;
  if(!u||!m){showErr();return;}
  const r=await fetch('/api/login',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({username:u,mot_de_passe:m})});
  const d=await r.json();
  if(d.ok){
    localStorage.setItem('token',d.token);
    localStorage.setItem('nom',d.nom);
    localStorage.setItem('role',d.role);
    localStorage.setItem('username',d.username);
    window.location.href='/app';
  } else { showErr(); }
}
function showErr(){
  const e=document.getElementById('err');
  e.classList.add('show');
  setTimeout(()=>e.classList.remove('show'),3000);
}
</script>
</body></html>"""

PAGE_APP = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ferme — Application</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
     background:#f5f5f0;color:#1a1a18;min-height:100vh;}
.topbar{background:#2E7D32;color:white;padding:12px 20px;
        display:flex;align-items:center;justify-content:space-between;}
.topbar-left{display:flex;align-items:center;gap:10px;}
.topbar h1{font-size:17px;font-weight:600;}
.topbar p{font-size:12px;opacity:0.8;}
.btn-logout{background:rgba(255,255,255,0.2);color:white;border:none;
            padding:7px 14px;border-radius:8px;font-size:13px;cursor:pointer;}
.btn-logout:hover{background:rgba(255,255,255,0.3);}
.container{max-width:760px;margin:0 auto;padding:20px 16px;}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px;}
.stat{background:white;border-radius:10px;padding:14px 16px;
      box-shadow:0 1px 3px rgba(0,0,0,0.07);}
.stat-label{font-size:11px;color:#888;margin-bottom:4px;}
.stat-value{font-size:22px;font-weight:700;color:#2E7D32;}
.stat-sub{font-size:11px;color:#aaa;margin-top:2px;}
.card{background:white;border-radius:12px;padding:18px 20px;
      box-shadow:0 1px 3px rgba(0,0,0,0.07);margin-bottom:18px;}
.card h2{font-size:14px;font-weight:700;color:#333;margin-bottom:14px;
         display:flex;align-items:center;gap:8px;}
.card h2::before{content:'';display:inline-block;width:4px;height:15px;
                 background:#2E7D32;border-radius:2px;}
.form-row{display:grid;grid-template-columns:1fr 1fr auto;gap:10px;align-items:end;}
.fg{display:flex;flex-direction:column;gap:5px;}
label{font-size:12px;font-weight:600;color:#555;}
select,input[type=number]{height:40px;border:1.5px solid #e0e0e0;border-radius:9px;
      padding:0 12px;font-size:14px;background:#fafafa;outline:none;
      transition:border-color 0.2s;width:100%;}
select:focus,input:focus{border-color:#4CAF50;background:white;}
.btn-save{height:40px;padding:0 18px;background:#2E7D32;color:white;border:none;
          border-radius:9px;font-size:14px;font-weight:600;cursor:pointer;
          white-space:nowrap;transition:background 0.15s;}
.btn-save:hover{background:#1B5E20;}
.toast{position:fixed;top:14px;right:14px;padding:11px 16px;border-radius:9px;
       font-size:13px;font-weight:600;display:none;z-index:99;
       box-shadow:0 4px 14px rgba(0,0,0,0.15);}
.toast.show{display:flex;align-items:center;gap:8px;}
.toast.ok{background:#E8F5E9;color:#1B5E20;border:1px solid #A5D6A7;}
.toast.err{background:#FFEBEE;color:#C62828;border:1px solid #EF9A9A;}
table{width:100%;border-collapse:collapse;}
thead th{background:#f8f8f6;padding:10px 12px;text-align:left;
         font-size:11px;font-weight:700;color:#666;border-bottom:1px solid #eee;
         text-transform:uppercase;letter-spacing:0.5px;}
tbody tr{border-bottom:0.5px solid #f0f0ec;transition:background 0.1s;}
tbody tr:last-child{border-bottom:none;}
tbody tr:hover{background:#f9fdf9;}
tbody tr.hl{background:#E8F5E9!important;}
tbody td{padding:10px 12px;font-size:13px;}
.badge{display:inline-block;padding:2px 9px;border-radius:12px;font-size:11px;font-weight:600;}
.bv{background:#E3F2FD;color:#1565C0;}
.bm{background:#FFF8E1;color:#E65100;}
.bc{background:#E8F5E9;color:#2E7D32;}
.fw{font-weight:700;}
.muted{color:#aaa;font-size:11px;}
.filters{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;}
.fb{padding:5px 12px;border:1.5px solid #ddd;border-radius:20px;
    background:white;font-size:12px;cursor:pointer;transition:all 0.15s;}
.fb:hover{border-color:#4CAF50;color:#2E7D32;}
.fb.active{background:#2E7D32;color:white;border-color:#2E7D32;}
/* Admin panel */
.admin-badge{background:#FF6F00;color:white;font-size:10px;padding:2px 7px;
             border-radius:10px;margin-left:6px;}
.add-form{display:grid;grid-template-columns:1fr 1fr 1fr 1fr auto;gap:8px;align-items:end;margin-top:12px;}
.add-form input,
.add-form select{height:36px;font-size:13px;}
.btn-add{height:36px;padding:0 14px;background:#1565C0;color:white;border:none;
         border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;}
.btn-add:hover{background:#0D47A1;}
@media(max-width:600px){
  .form-row,.add-form{grid-template-columns:1fr;}
  .stats{grid-template-columns:1fr 1fr;}
}
</style>
</head>
<body>
<div class="topbar">
  <div class="topbar-left">
    <span style="font-size:24px">🐄</span>
    <div>
      <h1 id="titre-nom">Gestion Ferme</h1>
      <p id="titre-role"></p>
    </div>
  </div>
  <button class="btn-logout" onclick="logout()">⬅ Déconnexion</button>
</div>

<div class="container">
  <div class="toast" id="toast"></div>
  <div class="stats" id="stats"></div>

  <div class="card">
    <h2>⚖️ Enregistrer une pesée</h2>
    <div class="form-row">
      <div class="fg">
        <label>Animal</label>
        <select id="sel-animal"><option value="">— Choisir —</option></select>
      </div>
      <div class="fg">
        <label>Nouveau poids (kg)</label>
        <input type="number" id="inp-poids" placeholder="ex: 465" min="1" max="2000" step="0.5"/>
      </div>
      <div class="fg">
        <button class="btn-save" onclick="enregistrer()">💾 Enregistrer</button>
      </div>
    </div>
  </div>

  <div class="card">
    <h2>📋 Mon troupeau</h2>
    <div class="filters">
      <button class="fb active" onclick="filtrer('tous',this)">Tous</button>
      <button class="fb" onclick="filtrer('Vache',this)">🐄 Vaches</button>
      <button class="fb" onclick="filtrer('Mouton',this)">🐑 Moutons</button>
      <button class="fb" onclick="filtrer('Chèvre',this)">🐐 Chèvres</button>
    </div>
    <table>
      <thead><tr>
        <th>N° Animal</th><th>Espèce</th><th>Poids (kg)</th><th>Dernière MAJ</th>
      </tr></thead>
      <tbody id="tb"></tbody>
    </table>
  </div>

  <!-- ADMIN uniquement -->
  <div class="card" id="admin-panel" style="display:none">
    <h2>🔧 Panneau Admin <span class="admin-badge">ADMIN</span></h2>
    <p style="font-size:13px;color:#666;margin-bottom:10px;">
      Ajouter un animal à un fermier :
    </p>
    <div class="add-form">
      <div class="fg">
        <label>Fermier</label>
        <select id="ad-fermier"></select>
      </div>
      <div class="fg">
        <label>N° Animal</label>
        <input type="text" id="ad-id" placeholder="ANI-030"/>
      </div>
      <div class="fg">
        <label>Espèce</label>
        <select id="ad-espece">
          <option>Vache</option>
          <option>Mouton</option>
          <option>Chèvre</option>
        </select>
      </div>
      <div class="fg">
        <label>Poids (kg)</label>
        <input type="number" id="ad-poids" placeholder="450" min="1"/>
      </div>
      <div class="fg">
        <button class="btn-add" onclick="ajouterAnimal()">+ Ajouter</button>
      </div>
    </div>
  </div>
</div>

<script>
const token=localStorage.getItem('token');
const role=localStorage.getItem('role');
const nom=localStorage.getItem('nom');
const username=localStorage.getItem('username');
if(!token){window.location.href='/';}

let animaux=[],filtre='tous',lastHL=null;

document.getElementById('titre-nom').textContent='Bonjour, '+nom+' 👋';
document.getElementById('titre-role').textContent=
  role==='admin'?'Administrateur — accès complet':'Fermier — mon troupeau';

if(role==='admin'){
  document.getElementById('admin-panel').style.display='block';
  chargerFermiers();
}

async function chargerFermiers(){
  const r=await api('GET','/api/fermiers');
  const s=document.getElementById('ad-fermier');
  s.innerHTML='';
  r.fermiers.forEach(f=>{
    const o=document.createElement('option');
    o.value=f.username;o.textContent=f.nom;s.appendChild(o);
  });
}

async function charger(){
  const r=await api('GET','/api/animaux');
  animaux=r.animaux||[];
  remplirSelect();
  afficherStats();
  afficherTable();
}

function remplirSelect(){
  const s=document.getElementById('sel-animal');
  s.innerHTML='<option value="">— Choisir un animal —</option>';
  animaux.forEach(a=>{
    const o=document.createElement('option');
    o.value=a.id;
    o.textContent=a.id+' — '+a.espece+' ('+a.poids.toFixed(1)+' kg)';
    s.appendChild(o);
  });
}

function afficherStats(){
  const total=animaux.length;
  const moy=total?animaux.reduce((s,a)=>s+a.poids,0)/total:0;
  const auj=new Date().toISOString().split('T')[0];
  const pesees=animaux.filter(a=>a.date===auj).length;
  document.getElementById('stats').innerHTML=`
    <div class="stat"><div class="stat-label">Mes animaux</div>
      <div class="stat-value">${total}</div><div class="stat-sub">dans mon troupeau</div></div>
    <div class="stat"><div class="stat-label">Poids moyen</div>
      <div class="stat-value">${moy.toFixed(1)}</div><div class="stat-sub">kg / animal</div></div>
    <div class="stat"><div class="stat-label">Pesées aujourd'hui</div>
      <div class="stat-value">${pesees}</div><div class="stat-sub">mises à jour</div></div>`;
}

function afficherTable(hl){
  const filtered=filtre==='tous'?animaux:animaux.filter(a=>a.espece===filtre);
  const badge=e=>e==='Vache'?'bv':e==='Mouton'?'bm':'bc';
  document.getElementById('tb').innerHTML=filtered.length?
    filtered.map(a=>`<tr class="${a.id===hl?'hl':''}">
      <td class="fw">${a.id}</td>
      <td><span class="badge ${badge(a.espece)}">${a.espece}</span></td>
      <td class="fw">${a.poids.toFixed(1)} kg</td>
      <td class="muted">${a.date}</td></tr>`).join(''):
    '<tr><td colspan="4" style="text-align:center;padding:20px;color:#aaa">Aucun animal</td></tr>';
}

function filtrer(f,btn){
  filtre=f;
  document.querySelectorAll('.fb').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  afficherTable(lastHL);
}

function toast(msg,ok=true){
  const t=document.getElementById('toast');
  t.textContent=msg;t.className='toast show '+(ok?'ok':'err');
  setTimeout(()=>t.className='toast',4000);
}

async function enregistrer(){
  const id=document.getElementById('sel-animal').value;
  const p=parseFloat(document.getElementById('inp-poids').value);
  if(!id){toast('⚠️ Sélectionne un animal.',false);return;}
  if(!p||p<=0){toast('⚠️ Saisis un poids valide.',false);return;}
  const r=await api('POST','/api/update',{id,poids:p});
  if(r.ok){
    await charger();lastHL=id;afficherTable(id);
    const diff=p-r.ancien;const sign=diff>=0?'+':'';
    toast('✅ '+id+' mis à jour : '+p.toFixed(1)+' kg ('+sign+diff.toFixed(1)+' kg)');
    document.getElementById('sel-animal').value='';
    document.getElementById('inp-poids').value='';
    setTimeout(()=>{lastHL=null;afficherTable();},4000);
  }else{toast('❌ Erreur lors de la mise à jour.',false);}
}

async function ajouterAnimal(){
  const fermier=document.getElementById('ad-fermier').value;
  const id=document.getElementById('ad-id').value.trim();
  const espece=document.getElementById('ad-espece').value;
  const poids=parseFloat(document.getElementById('ad-poids').value);
  if(!id||!poids){toast('⚠️ Remplis tous les champs.',false);return;}
  const r=await api('POST','/api/ajouter',{fermier,id,espece,poids});
  if(r.ok){toast('✅ Animal '+id+' ajouté à '+fermier);
    document.getElementById('ad-id').value='';
    document.getElementById('ad-poids').value='';
    if(fermier===username)await charger();
  }else{toast('❌ '+(r.msg||'Erreur'),false);}
}

async function api(method,url,body){
  const opts={method,headers:{'Content-Type':'application/json','X-Token':token}};
  if(body)opts.body=JSON.stringify(body);
  const r=await fetch(url,opts);
  return r.json();
}

function logout(){
  localStorage.clear();
  window.location.href='/';
}

charger();
</script>
</body></html>"""

# ─── SERVEUR HTTP ──────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def get_token(self):
        return self.headers.get("X-Token","")

    def get_user(self):
        return verifier_session(self.get_token())

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type","application/json;charset=utf-8")
        self.send_header("Content-Length",len(body))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html):
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type","text/html;charset=utf-8")
        self.send_header("Content-Length",len(body))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        length = int(self.headers.get("Content-Length",0))
        return json.loads(self.rfile.read(length)) if length else {}

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            self.send_html(PAGE_LOGIN)
        elif path == "/app":
            u = self.get_user()
            if not u:
                self.send_response(302)
                self.send_header("Location","/")
                self.end_headers()
            else:
                self.send_html(PAGE_APP)
        elif path == "/api/animaux":
            u = self.get_user()
            if not u:
                self.send_json({"error":"non autorisé"},401); return
            users = charger_json(USERS_FILE, {})
            role  = users.get(u,{}).get("role","fermier")
            data  = charger_json(DATA_FILE, {})
            # Admin voit tout, fermier voit ses animaux
            if role == "admin":
                tous = []
                for k,v in data.items(): tous.extend(v)
                self.send_json({"animaux": tous})
            else:
                self.send_json({"animaux": data.get(u,[])})
        elif path == "/api/fermiers":
            u = self.get_user()
            if not u:
                self.send_json({"error":"non autorisé"},401); return
            users = charger_json(USERS_FILE, {})
            fermiers = [{"username":k,"nom":v["nom"]}
                        for k,v in users.items() if v.get("role")=="fermier"]
            self.send_json({"fermiers": fermiers})
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path
        body = self.read_body()

        if path == "/api/login":
            users = charger_json(USERS_FILE, {})
            u = body.get("username","")
            m = body.get("mot_de_passe","")
            info = users.get(u,{})
            if info and info.get("mot_de_passe") == hacher(m):
                token = creer_session(u)
                self.send_json({"ok":True,"token":token,
                                "nom":info["nom"],"role":info["role"],
                                "username":u})
            else:
                self.send_json({"ok":False})

        elif path == "/api/update":
            u = self.get_user()
            if not u: self.send_json({"ok":False}); return
            users = charger_json(USERS_FILE, {})
            role  = users.get(u,{}).get("role","fermier")
            data  = charger_json(DATA_FILE, {})
            animal_id = body.get("id")
            nouveau   = float(body.get("poids",0))
            # chercher l'animal dans les données du fermier (ou tout si admin)
            cibles = data.keys() if role=="admin" else [u]
            for fermier in cibles:
                for a in data.get(fermier,[]):
                    if a["id"] == animal_id:
                        ancien = a["poids"]
                        a["poids"] = nouveau
                        a["date"]  = date.today().isoformat()
                        sauver_json(DATA_FILE, data)
                        self.send_json({"ok":True,"ancien":ancien})
                        return
            self.send_json({"ok":False})

        elif path == "/api/ajouter":
            u = self.get_user()
            if not u: self.send_json({"ok":False}); return
            users = charger_json(USERS_FILE, {})
            if users.get(u,{}).get("role") != "admin":
                self.send_json({"ok":False,"msg":"Accès refusé"}); return
            data = charger_json(DATA_FILE, {})
            fermier = body.get("fermier")
            if fermier not in data: data[fermier] = []
            # vérifier doublon
            for a in data[fermier]:
                if a["id"] == body.get("id"):
                    self.send_json({"ok":False,"msg":"ID déjà existant"}); return
            data[fermier].append({
                "id":    body.get("id"),
                "espece":body.get("espece","Vache"),
                "poids": float(body.get("poids",0)),
                "date":  date.today().isoformat()
            })
            sauver_json(DATA_FILE, data)
            self.send_json({"ok":True})

        else:
            self.send_response(404); self.end_headers()


if __name__ == "__main__":
    init_donnees()
    PORT = int(os.environ.get("PORT", 5000))
    server = HTTPServer(("", PORT), Handler)
    print(f"\n🌿 Application Ferme démarrée !")
    print(f"   👉 Ouvrez : http://localhost:{PORT}")
    print(f"\n📋 Comptes disponibles :")
    print(f"   admin    / admin123  (administrateur)")
    print(f"   fermier1 / 1234      (Ahmed Ben Ali)")
    print(f"   fermier2 / 1234      (Mohamed Trabelsi)")
    print(f"   fermier3 / 1234      (Sami Gharbi)")
    print(f"\n⏹️  Pour arrêter : Ctrl+C\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ Application arrêtée.")
