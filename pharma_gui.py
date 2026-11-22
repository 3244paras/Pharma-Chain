import streamlit as st
import sqlite3, hashlib, json, math
from datetime import datetime, date, timedelta

try:
    import pandas as pd
except ImportError:
    pd = None
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except Exception:
    plt = None
    MATPLOTLIB_AVAILABLE = False
try:
    import numpy as np
except ImportError:
    np = None
try:
    import folium
    from streamlit_folium import st_folium
    MAP_AVAILABLE = True
except Exception:
    MAP_AVAILABLE = False
try:
    import cv2
    CV2_AVAILABLE = True
except Exception:
    CV2_AVAILABLE = False
try:
    from pyzbar.pyzbar import decode as decode_barcode
    PYZBAR_AVAILABLE = True
except Exception:
    PYZBAR_AVAILABLE = False
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False

DB_NAME = "pharma_database.db"
st.set_page_config(page_title="PharmaChain Research Platform", page_icon="💊", layout="wide")

# ============================================================
# DATABASE / MIGRATION
# ============================================================
BASE_COLUMNS = {
    "medicine_id":"TEXT", "medicine_name":"TEXT", "batch_number":"TEXT",
    "manufacturer":"TEXT", "manufacturer_location":"TEXT", "manufacturer_lat":"REAL", "manufacturer_lon":"REAL",
    "distributor":"TEXT", "distributor_location":"TEXT", "distributor_lat":"REAL", "distributor_lon":"REAL",
    "pharmacy":"TEXT", "pharmacy_location":"TEXT", "pharmacy_lat":"REAL", "pharmacy_lon":"REAL",
    "expiry_date":"TEXT", "qr_verified":"INTEGER", "identity_verified":"INTEGER", "identity_source":"TEXT",
    "package_intact":"INTEGER", "batch_verified":"INTEGER", "temperature":"REAL", "humidity":"REAL", "transport_time":"REAL",
    "temperature_source":"TEXT", "humidity_source":"TEXT", "transport_source":"TEXT", "location_source":"TEXT",
    "dispatch_time":"TEXT", "receipt_time":"TEXT", "temp_min":"REAL", "temp_max":"REAL", "humidity_min":"REAL", "humidity_max":"REAL",
    "temp_excursions":"INTEGER", "humidity_excursions":"INTEGER",
    "atc":"REAL", "atc_status":"TEXT", "medicine_trust":"REAL", "success_rate":"REAL", "medicine_integrity":"REAL", "compliance_history":"REAL",
    "historical_trust":"REAL", "trust_change":"REAL", "macs":"REAL", "macs_status":"TEXT", "counterfeit":"TEXT", "risk_level":"TEXT", "risk_score":"REAL", "pti":"REAL", "pti_status":"TEXT",
    "updated_trust":"REAL", "updated_pti":"REAL", "recovery":"REAL", "recovery_status":"TEXT", "network_status":"TEXT",
    "detected_problems":"TEXT", "risk_reasons":"TEXT", "block_hash":"TEXT", "previous_hash":"TEXT", "verification_time":"TEXT"
}

CASE_COLUMNS = {
    "case_id":"TEXT", "transaction_id":"INTEGER", "status":"TEXT", "priority":"TEXT", "created_at":"TEXT", "notes":"TEXT"
}

def db():
    return sqlite3.connect(DB_NAME, timeout=20)

def init_db():
    con = db(); cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS medicine_transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, medicine_id TEXT NOT NULL, medicine_name TEXT NOT NULL, batch_number TEXT NOT NULL)")
    cur.execute("PRAGMA table_info(medicine_transactions)")
    existing = {r[1] for r in cur.fetchall()}
    for col, typ in BASE_COLUMNS.items():
        if col not in existing:
            cur.execute(f"ALTER TABLE medicine_transactions ADD COLUMN {col} {typ}")
    cur.execute("CREATE TABLE IF NOT EXISTS investigation_cases (id INTEGER PRIMARY KEY AUTOINCREMENT)")
    cur.execute("PRAGMA table_info(investigation_cases)")
    c_existing = {r[1] for r in cur.fetchall()}
    for col, typ in CASE_COLUMNS.items():
        if col not in c_existing:
            cur.execute(f"ALTER TABLE investigation_cases ADD COLUMN {col} {typ}")
    for sql in [
        "CREATE INDEX IF NOT EXISTS idx_mid ON medicine_transactions(medicine_id)",
        "CREATE INDEX IF NOT EXISTS idx_batch ON medicine_transactions(batch_number)",
        "CREATE INDEX IF NOT EXISTS idx_hash ON medicine_transactions(block_hash)",
        "CREATE INDEX IF NOT EXISTS idx_participant_dist ON medicine_transactions(distributor)",
        "CREATE INDEX IF NOT EXISTS idx_participant_man ON medicine_transactions(manufacturer)"
    ]:
        cur.execute(sql)
    con.commit(); con.close()

init_db()

def df_all():
    if pd is None: return None
    con=db(); x=pd.read_sql_query("SELECT * FROM medicine_transactions ORDER BY id DESC", con); con.close(); return x

def count_tx():
    con=db(); n=con.execute("SELECT COUNT(*) FROM medicine_transactions").fetchone()[0]; con.close(); return n

def clear_tx():
    con=db(); con.execute("DELETE FROM medicine_transactions"); con.execute("DELETE FROM investigation_cases"); con.execute("DELETE FROM sqlite_sequence WHERE name IN ('medicine_transactions','investigation_cases')"); con.commit(); con.close()

# ============================================================
# BLOCKCHAIN-STYLE AUDIT CHAIN
# ============================================================
def hash_payload(record, previous):
    payload = {k: record.get(k) for k in sorted(record) if k not in ("block_hash", "previous_hash", "id")}
    raw = json.dumps({"previous_hash": previous, "data": payload}, sort_keys=True, default=str, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()

def db_last_hash():
    con=db(); r=con.execute("SELECT block_hash FROM medicine_transactions ORDER BY id DESC LIMIT 1").fetchone(); con.close(); return r[0] if r and r[0] else "GENESIS"

def save_tx(result):
    result=dict(result); previous=db_last_hash(); result["previous_hash"]=previous; result["block_hash"]=hash_payload(result, previous)
    cols=list(BASE_COLUMNS); vals=[result.get(c) for c in cols]
    con=db(); cur=con.cursor(); cur.execute(f"INSERT INTO medicine_transactions ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})", vals); tid=cur.lastrowid; con.commit(); con.close(); return tid,result["block_hash"]

def verify_chain():
    con=db(); cur=con.cursor(); rows=cur.execute("SELECT * FROM medicine_transactions ORDER BY id ASC").fetchall(); cols=[d[0] for d in cur.description]; con.close(); previous="GENESIS"
    for row in rows:
        rec=dict(zip(cols,row)); tid=rec["id"]
        if (rec.get("previous_hash") or "") != previous: return False,f"Transaction {tid}: previous hash does not match.",tid
        expected=hash_payload({k:rec.get(k) for k in BASE_COLUMNS},previous)
        if expected != (rec.get("block_hash") or ""): return False,f"Transaction {tid}: stored hash does not match the record.",tid
        previous=rec.get("block_hash")
    return True,"Audit chain integrity verified.",None

def rebuild_chain():
    con=db(); cur=con.cursor(); rows=cur.execute("SELECT * FROM medicine_transactions ORDER BY id ASC").fetchall(); cols=[d[0] for d in cur.description]; previous="GENESIS"
    for row in rows:
        rec=dict(zip(cols,row)); new=hash_payload({k:rec.get(k) for k in BASE_COLUMNS},previous); cur.execute("UPDATE medicine_transactions SET previous_hash=?, block_hash=? WHERE id=?",(previous,new,rec["id"])); previous=new
    con.commit(); con.close(); return len(rows)

# ============================================================
# SCORING / TRUST ENGINE
# ============================================================
def bound(x):
    return round(max(0,min(100,float(x))),2)

def condition(x, lo, hi, alo, ahi):
    return (100,"OPTIMAL") if lo<=x<=hi else ((60,"ACCEPTABLE") if alo<=x<=ahi else (0,"UNSAFE"))

def identity_ok(qr, source):
    return bool(qr or source in {"Batch + manufacturer record","Manual verified identity","GS1/barcode scan","QR code"})

def macs(qr, source, pkg, batch, temp, hum, travel, expiry):
    ip=20 if identity_ok(qr,source) else 0; pp=15 if pkg else 0; bp=20 if batch else 0
    tq,tl=condition(temp,2,30,0,40); hq,hl=condition(hum,20,70,10,80)
    tp=15*tq/100; hp=10*hq/100
    tr,trl=(10,"OPTIMAL") if travel<=24 else ((5,"ACCEPTABLE") if travel<=48 else (0,"EXCESSIVE"))
    ep=10 if expiry else 0
    score=bound(ip+pp+bp+tp+hp+tr+ep)
    status="GENUINE" if score>=80 else ("SUSPICIOUS" if score>=60 else "COUNTERFEIT RISK")
    breakdown=[
        ("Identity verification",ip,"PASS" if identity_ok(qr,source) else "FAIL"),
        ("Package integrity",pp,"PASS" if pkg else "FAIL"),
        ("Batch verification",bp,"PASS" if batch else "FAIL"),
        ("Temperature",round(tp,2),tl),("Humidity",round(hp,2),hl),
        ("Transport time",tr,trl),("Expiry",ep,"VALID" if expiry else "EXPIRED")]
    return score,status,breakdown

def medicine_trust(qr,source,pkg,batch,temp,hum,travel,expiry):
    ident=100 if identity_ok(qr,source) else 0
    tq,_=condition(temp,2,30,0,40); hq,_=condition(hum,20,70,10,80)
    trans=100 if travel<=24 else (60 if travel<=48 else (30 if travel<=72 else 0)); exp=100 if expiry else 0
    return bound(.20*ident+.20*(100 if pkg else 0)+.20*(100 if batch else 0)+.15*tq+.10*hq+.10*trans+.05*exp)

def participant_history(name, role):
    if not name: return {"count":0,"good":0,"risk":0,"avg_trust":70.0,"current_trust":70.0,"last_risk":"NONE"}
    col={"Manufacturer":"manufacturer","Distributor":"distributor","Pharmacy":"pharmacy"}[role]
    con=db(); rows=con.execute(f"SELECT risk_level, atc, pti, updated_trust FROM medicine_transactions WHERE {col}=? ORDER BY id ASC",(name,)).fetchall(); con.close()
    if not rows: return {"count":0,"good":0,"risk":0,"avg_trust":70.0,"current_trust":70.0,"last_risk":"NONE"}
    current=70.0; good=0; risk=0
    for risk_level,a,p,u in rows:
        if risk_level=="LOW": good+=1; current=min(100,current+3)
        elif risk_level=="MEDIUM": risk+=1; current=max(0,current-8)
        elif risk_level=="HIGH": risk+=1; current=max(0,current-20)
        else: current=max(0,current-3)
        if u is not None: current=.6*current+.4*float(u)
    return {"count":len(rows),"good":good,"risk":risk,"avg_trust":bound(sum(float(r[1] or 0) for r in rows)/len(rows)),"current_trust":bound(current),"last_risk":rows[-1][0] or "NONE"}

def compliance(man,dist,pharmacy=""):
    names=[(man,"manufacturer"),(dist,"distributor"),(pharmacy,"pharmacy")]
    vals=[]
    con=db()
    for name,col in names:
        if not name: continue
        rows=con.execute(f"SELECT risk_level,atc,pti FROM medicine_transactions WHERE {col}=? ORDER BY id DESC LIMIT 20",(name,)).fetchall()
        for risk,a,p in rows:
            vals.append(.50*(100 if risk=="LOW" else 60 if risk=="MEDIUM" else 20)+.25*float(a or 0)+.25*float(p or 0))
    con.close()
    return (bound(sum(vals)/len(vals)),len(vals)) if vals else (70.0,0)

def atc(mt, qr, source, pkg, batch, comp, historical):
    sr=sum([identity_ok(qr,source),bool(pkg),bool(batch)])/3*100
    integrity=50*int(pkg)+50*int(batch)
    # Adaptive version: historical participant trust is an explicit component.
    score=bound(.35*mt+.20*sr+.15*integrity+.15*comp+.15*historical)
    status="TRUSTED" if score>=70 else ("MONITOR" if score>=50 else "SUSPICIOUS")
    return score,status,round(sr,2),integrity,round(comp,2)

def pti(a,m,c,risk):
    x=.40*a+.40*m+.20*c-(20 if risk=="HIGH" else 8 if risk=="MEDIUM" else 0); x=bound(x)
    return x,"HIGHLY TRUSTED" if x>=80 else ("TRUSTED" if x>=60 else ("MONITOR" if x>=40 else "LOW TRUST"))

def healing(name,a,p,counterfeit,risk,history):
    # Penalty on an adverse event + recovery for sustained good history.
    if risk=="HIGH": ut,up=max(0,a-20),max(0,p-15); ns=f"{name} isolated from network"
    elif risk=="MEDIUM": ut,up=max(0,a-8),max(0,p-6); ns=f"{name} placed under monitoring"
    elif counterfeit: ut,up=max(0,a-3),max(0,p-2); ns=f"{name} under observation"
    else: ut,up=a,p; ns="Network Stable"
    if history.get("count",0)>=2 and history.get("risk",0)==0 and not counterfeit:
        bonus=min(8, history["good"]*1.5); ut=min(100,ut+bonus); up=min(100,up+bonus/2); ns=f"{name} recovering through compliant history"
    rec=bound((ut+up)/2)
    rs="HEALTHY" if rec>=80 else ("STABLE" if rec>=60 and not counterfeit else ("RECOVERING" if rec>=60 else ("DEGRADED" if rec>=40 else "CRITICAL")))
    return bound(ut),bound(up),rec,ns,rs

# ============================================================
# DATA SOURCES / SCANNER
# ============================================================
def transport_hours(dispatch,receipt):
    if not dispatch or not receipt:return None,"Missing timestamps."
    try:
        a=datetime.fromisoformat(dispatch); b=datetime.fromisoformat(receipt); sec=(b-a).total_seconds()
        if sec<0:return None,"Receipt time cannot be before dispatch time."
        return round(sec/3600,2),None
    except ValueError:return None,"Invalid timestamp."

def sensor_csv(file):
    if pd is None:return None,"pandas is not installed."
    try: file.seek(0); raw=pd.read_csv(file)
    except Exception as e:return None,f"Could not read CSV: {e}"
    cols={str(c).strip().lower():c for c in raw.columns}
    tc=next((cols[k] for k in ["temperature","temp","temperature_c","temp_c"] if k in cols),None)
    hc=next((cols[k] for k in ["humidity","rh","humidity_percent","humidity_pct"] if k in cols),None)
    if tc is None or hc is None:return None,"CSV needs temperature and humidity columns."
    out=pd.DataFrame({"temperature":pd.to_numeric(raw[tc],errors="coerce"),"humidity":pd.to_numeric(raw[hc],errors="coerce")}).dropna()
    return (out,None) if len(out) else (None,"No valid sensor rows found.")

def sensor_summary(x):
    t=x.temperature.astype(float); h=x.humidity.astype(float)
    return dict(temperature=round(t.mean(),2),humidity=round(h.mean(),2),temp_min=round(t.min(),2),temp_max=round(t.max(),2),humidity_min=round(h.min(),2),humidity_max=round(h.max(),2),temp_excursions=int(((t<2)|(t>30)).sum()),humidity_excursions=int(((h<20)|(h>70)).sum()),rows=len(x))

def scan_image(file):
    if not CV2_AVAILABLE or file is None:return None
    try:
        import numpy as np_local
        img=cv2.imdecode(np_local.frombuffer(file.getvalue(),dtype=np_local.uint8),cv2.IMREAD_COLOR)
        if img is None:return None
        val,_,_=cv2.QRCodeDetector().detectAndDecode(img)
        if val:return val
        if PYZBAR_AVAILABLE:
            found=decode_barcode(img)
            if found:return found[0].data.decode("utf-8",errors="ignore")
    except Exception:return None
    return None

def parse_scan(s):
    if not s:return {}
    try:
        x=json.loads(s); return x if isinstance(x,dict) else {"medicine_id":s}
    except Exception:return {"medicine_id":s}

# ============================================================
# ANOMALIES / EXPLAINABILITY
# ============================================================
def anomalies(result):
    p=[]
    if not result.get("identity_verified"):p.append("Medicine identity could not be verified.")
    if not result.get("package_intact"):p.append("Package integrity failed.")
    if not result.get("batch_verified"):p.append("Batch verification failed.")
    if float(result.get("transport_time") or 0)>72:p.append("Excessive transport time (>72 hours).")
    if float(result.get("temperature") or 25)<0 or float(result.get("temperature") or 25)>40:p.append("Unsafe average temperature condition.")
    if float(result.get("humidity") or 50)<10 or float(result.get("humidity") or 50)>80:p.append("Unsafe average humidity condition.")
    if int(result.get("temp_excursions") or 0)>0:p.append(f"Temperature excursion detected ({result.get('temp_excursions')} reading(s)).")
    if int(result.get("humidity_excursions") or 0)>0:p.append(f"Humidity excursion detected ({result.get('humidity_excursions')} reading(s)).")
    if not result.get("expiry_valid"):p.append("Medicine is expired.")
    con=db()
    repeat=con.execute("SELECT COUNT(*) FROM medicine_transactions WHERE (manufacturer=? OR distributor=? OR pharmacy=?) AND risk_level IN ('MEDIUM','HIGH')",(result.get("manufacturer",""),result.get("distributor",""),result.get("pharmacy",""))).fetchone()[0]
    same=con.execute("SELECT COUNT(*) FROM medicine_transactions WHERE medicine_id=? AND batch_number=?",(result.get("medicine_id",""),result.get("batch_number",""))).fetchone()[0]
    con.close()
    if repeat>=2:p.append("Repeated participant risk detected in history.")
    if same>=1:p.append("Same medicine ID + batch already exists in the database.")
    return p

def risk_score_from(result, problems):
    score=0
    if not result.get("identity_verified"):score+=25
    if not result.get("batch_verified"):score+=25
    if not result.get("package_intact"):score+=15
    if not result.get("expiry_valid"):score+=15
    if float(result.get("temperature") or 25)<0 or float(result.get("temperature") or 25)>40:score+=10
    if float(result.get("humidity") or 50)<10 or float(result.get("humidity") or 50)>80:score+=10
    if float(result.get("transport_time") or 0)>72:score+=10
    score+=min(20,int(result.get("temp_excursions") or 0)*5)
    score+=min(20,int(result.get("humidity_excursions") or 0)*5)
    if any("Repeated participant" in x for x in problems):score+=15
    if any("already exist" in x for x in problems):score+=10
    return min(100,score)

def risk_reasons(result, problems):
    reasons=[]
    weights=[]
    mapping=[
        (not result.get("identity_verified"),"Identity verification failed",25),
        (not result.get("batch_verified"),"Batch verification failed",25),
        (not result.get("package_intact"),"Package integrity failed",15),
        (not result.get("expiry_valid"),"Expiry validation failed",15),
        (float(result.get("temperature") or 25)<0 or float(result.get("temperature") or 25)>40,"Unsafe average temperature",10),
        (float(result.get("humidity") or 50)<10 or float(result.get("humidity") or 50)>80,"Unsafe average humidity",10),
        (float(result.get("transport_time") or 0)>72,"Excessive transport duration",10),
        (int(result.get("temp_excursions") or 0)>0,"Temperature excursion history",5),
        (int(result.get("humidity_excursions") or 0)>0,"Humidity excursion history",5),
    ]
    for flag,text,w in mapping:
        if flag: weights.append((text,w))
    for p in problems:
        if "Repeated participant" in p: weights.append(("Repeated participant risk",15))
        if "already exist" in p: weights.append(("Duplicate medicine/batch record",10))
    for text,w in sorted(weights,key=lambda z:z[1],reverse=True): reasons.append(f"{text} (+{w})")
    return reasons

def build(data):
    try: expiry=date.fromisoformat(data["expiry_date"])>=date.today() if data["expiry_date"] else True
    except ValueError: expiry=False
    ident=identity_ok(data["qr_verified"],data["identity_source"])
    m,ms,breakdown=macs(data["qr_verified"],data["identity_source"],data["package_intact"],data["batch_verified"],data["temperature"],data["humidity"],data["transport_time"],expiry)
    mt=medicine_trust(data["qr_verified"],data["identity_source"],data["package_intact"],data["batch_verified"],data["temperature"],data["humidity"],data["transport_time"],expiry)
    comp,hist=0,0
    comp,hist=__import__('builtins').tuple(compliance(data["manufacturer"],data["distributor"],data["pharmacy"]))
    # Most relevant participant is the distributor; manufacturer/pharmacy history is shown separately.
    ph=participant_history(data["distributor"],"Distributor")
    historical=ph["current_trust"]
    a,ast,sr,integrity,comp2=atc(mt,data["qr_verified"],data["identity_source"],data["package_intact"],data["batch_verified"],comp,historical)
    prelim=[]
    if not ident:prelim.append("Identity verification failed.")
    if not data["package_intact"]:prelim.append("Package integrity failed.")
    if not data["batch_verified"]:prelim.append("Batch verification failed.")
    counterfeit=(not ident and not data["package_intact"] and not data["batch_verified"]) or m<60
    risk="HIGH" if ((not ident and not data["package_intact"] and not data["batch_verified"]) or m<40) else ("MEDIUM" if m<80 or len(prelim)>=2 or float(data["transport_time"])>72 else "LOW")
    ps=risk_score_from({**data,"identity_verified":ident,"expiry_valid":expiry},prelim)
    ps=min(100,ps+20 if risk=="HIGH" else ps)
    p,pstatus=pti(a,m,comp,risk)
    # Self-healing receives history before this transaction.
    ut,up,rec,ns,rs=healing(data["distributor"] or data["manufacturer"] or "Participant",a,p,counterfeit,risk,ph)
    out=dict(data,identity_verified=ident,expiry_valid=expiry,medicine_trust=mt,success_rate=sr,medicine_integrity=integrity,compliance_history=comp2,historical_trust=historical,trust_change=round(a-historical,2),atc=a,atc_status=ast,macs=m,macs_status=ms,counterfeit="YES" if counterfeit else "NO",risk_level=risk,risk_score=ps,pti=p,pti_status=pstatus,updated_trust=ut,updated_pti=up,recovery=rec,recovery_status=rs,network_status=ns)
    probs=anomalies(out); reasons=risk_reasons(out,probs)
    out["detected_problems"]="; ".join(probs) if probs else "None"; out["risk_reasons"]="; ".join(reasons) if reasons else "No material risk factors detected."
    out["verification_time"]=datetime.now().isoformat(timespec="seconds")
    return out,breakdown,ph

# ============================================================
# RESEARCH DATA / ML EXPERIMENTS
# ============================================================
FEATURES=["identity_verified","package_intact","batch_verified","expiry_valid","temperature","humidity","transport_time","temp_excursions","humidity_excursions","historical_trust"]

def generate_research_data(n=1200, seed=42):
    if pd is None: return None
    import random
    rng=random.Random(seed); rows=[]
    for i in range(n):
        bad=rng.random()<0.35
        identity=(rng.random()>0.20 if bad else rng.random()>0.03)
        package=(rng.random()>0.22 if bad else rng.random()>0.03)
        batch=(rng.random()>0.25 if bad else rng.random()>0.03)
        expiry=(rng.random()>0.18 if bad else rng.random()>0.02)
        temp=(rng.uniform(0,50) if bad else rng.uniform(2,30))
        hum=(rng.uniform(10,90) if bad else rng.uniform(20,70))
        travel=(rng.uniform(24,120) if bad else rng.uniform(4,36))
        te=rng.randint(0,4) if bad else (1 if rng.random()<0.03 else 0)
        he=rng.randint(0,4) if bad else (1 if rng.random()<0.03 else 0)
        hist=rng.uniform(20,80) if bad else rng.uniform(65,100)
        # Independent synthetic ground-truth rule for a research simulation, not real medicine labels.
        severity=(not identity)*3+(not package)*2+(not batch)*3+(not expiry)*2+(temp<0 or temp>40)*2+(hum<10 or hum>80)*2+(travel>72)*2+(te>0)*1+(he>0)*1+(hist<50)*2
        label=int(severity>=4)
        rows.append(dict(transaction_id=i+1,identity_verified=int(identity),package_intact=int(package),batch_verified=int(batch),expiry_valid=int(expiry),temperature=round(temp,2),humidity=round(hum,2),transport_time=round(travel,2),temp_excursions=te,humidity_excursions=he,historical_trust=round(hist,2),ground_truth=label))
    return pd.DataFrame(rows)

def run_ml_experiment(df):
    if not SKLEARN_AVAILABLE:return None,"scikit-learn is not installed."
    X=df[FEATURES].astype(float); y=df["ground_truth"].astype(int)
    if y.nunique()<2:return None,"Need both classes in the dataset."
    Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.25,random_state=42,stratify=y)
    model=RandomForestClassifier(n_estimators=250,max_depth=8,random_state=42,class_weight="balanced")
    model.fit(Xtr,ytr); pred=model.predict(Xte)
    cm=confusion_matrix(yte,pred)
    metrics={"Accuracy":accuracy_score(yte,pred),"Precision":precision_score(yte,pred,zero_division=0),"Recall":recall_score(yte,pred,zero_division=0),"F1":f1_score(yte,pred,zero_division=0)}
    importance=pd.DataFrame({"Feature":FEATURES,"Importance":model.feature_importances_}).sort_values("Importance",ascending=False)
    return {"metrics":metrics,"matrix":cm,"importance":importance,"model":model},None

# ============================================================
# CASE MANAGEMENT
# ============================================================
def create_case(txid, priority, notes):
    cid="CASE-"+datetime.now().strftime("%Y%m%d%H%M%S")+"-"+str(txid)
    con=db(); con.execute("INSERT INTO investigation_cases (case_id,transaction_id,status,priority,created_at,notes) VALUES (?,?,?,?,?,?)",(cid,txid,"OPEN",priority,datetime.now().isoformat(timespec="seconds"),notes)); con.commit(); con.close(); return cid

def cases_df():
    if pd is None:return None
    con=db(); x=pd.read_sql_query("SELECT * FROM investigation_cases ORDER BY id DESC",con); con.close(); return x


# ============================================================
# VISUAL DESIGN / DASHBOARD HELPERS
# ============================================================
def apply_theme():
    st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg,#080c14 0%,#0d1420 52%,#0a111b 100%); }
    [data-testid="stSidebar"] { background: linear-gradient(180deg,#0b111b 0%,#101827 100%); border-right: 1px solid rgba(255,255,255,.08); }
    .hero { padding: 26px 30px; border-radius: 22px; background: linear-gradient(135deg,rgba(30,64,175,.30),rgba(8,145,178,.18)); border:1px solid rgba(125,211,252,.20); box-shadow: 0 18px 50px rgba(0,0,0,.25); margin-bottom: 22px; }
    .hero h1 { margin:0; font-size: 2.15rem; letter-spacing:-.03em; color:#f8fbff; }
    .hero p { margin:8px 0 0; color:#b9c7d9; font-size:1rem; }
    .eyebrow { color:#67e8f9; font-weight:700; text-transform:uppercase; letter-spacing:.12em; font-size:.74rem; margin-bottom:8px; }
    .glass { padding:18px 20px; border-radius:18px; background:rgba(17,25,39,.72); border:1px solid rgba(255,255,255,.08); box-shadow:0 10px 30px rgba(0,0,0,.18); height:100%; }
    .glass h3 { margin:0 0 7px; color:#f1f5f9; font-size:1.02rem; }
    .glass p { margin:0; color:#aebed0; font-size:.9rem; line-height:1.5; }
    .kpi { padding:18px 18px 15px; border-radius:18px; background:linear-gradient(180deg,rgba(20,30,45,.95),rgba(12,18,29,.95)); border:1px solid rgba(255,255,255,.08); min-height:112px; }
    .kpi .label { color:#94a3b8; font-size:.78rem; text-transform:uppercase; letter-spacing:.07em; }
    .kpi .value { color:#f8fafc; font-size:1.75rem; font-weight:800; margin-top:5px; }
    .kpi .sub { color:#67e8f9; font-size:.78rem; margin-top:3px; }
    .score-card { padding:17px; border-radius:18px; background:#101827; border:1px solid rgba(255,255,255,.08); }
    .score-title { color:#94a3b8; font-size:.76rem; text-transform:uppercase; letter-spacing:.08em; }
    .score-value { font-size:2rem; font-weight:800; color:#f8fafc; }
    .score-status { color:#67e8f9; font-size:.78rem; }
    .bar { height:8px; background:#1e293b; border-radius:99px; overflow:hidden; margin-top:9px; }
    .bar > div { height:100%; border-radius:99px; background:linear-gradient(90deg,#22d3ee,#60a5fa); }
    .flow-wrap { padding:20px; border-radius:20px; background:rgba(15,23,42,.78); border:1px solid rgba(255,255,255,.08); margin:12px 0 20px; }
    .flow { display:flex; align-items:center; justify-content:center; gap:8px; flex-wrap:wrap; }
    .flow-box { min-width:135px; text-align:center; padding:13px 10px; border-radius:14px; background:linear-gradient(180deg,#172338,#101827); border:1px solid rgba(103,232,249,.18); color:#e2e8f0; font-weight:700; font-size:.84rem; }
    .flow-box small { display:block; color:#94a3b8; font-weight:400; margin-top:4px; }
    .arrow { color:#67e8f9; font-size:1.35rem; }
    .status-pill { display:inline-block; padding:5px 10px; border-radius:999px; background:rgba(34,211,238,.10); border:1px solid rgba(34,211,238,.18); color:#67e8f9; font-size:.76rem; font-weight:700; }
    .research-note { padding:13px 16px; border-left:3px solid #22d3ee; background:rgba(34,211,238,.06); color:#b8c7d9; border-radius:10px; margin:12px 0; }
    .section-title { font-size:1.35rem; font-weight:800; color:#f8fafc; margin:20px 0 10px; }
    </style>
    """, unsafe_allow_html=True)

def hero(title, subtitle, eyebrow="PHARMACHAIN RESEARCH PLATFORM"):
    st.markdown(f'<div class="hero"><div class="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)

def section(title, subtitle=None):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.caption(subtitle)

def kpi(label, value, sub=""):
    st.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div><div class="sub">{sub}</div></div>', unsafe_allow_html=True)

def score_card(title, value, status):
    v=max(0,min(100,float(value)))
    st.markdown(f'<div class="score-card"><div class="score-title">{title}</div><div class="score-value">{v:.1f}</div><div class="score-status">{status}</div><div class="bar"><div style="width:{v:.1f}%"></div></div></div>', unsafe_allow_html=True)

def architecture_diagram():
    st.markdown('''
    <div class="flow-wrap">
      <div class="eyebrow">SYSTEM ARCHITECTURE</div>
      <div class="flow">
        <div class="flow-box">Medicine Data<small>Identity • Batch • Expiry</small></div><div class="arrow">→</div>
        <div class="flow-box">Evidence Layer<small>Sensor • Transport • Location</small></div><div class="arrow">→</div>
        <div class="flow-box">Anomaly Engine<small>Detect unusual events</small></div><div class="arrow">→</div>
        <div class="flow-box">MACS<small>Medicine trust</small></div><div class="arrow">→</div>
        <div class="flow-box">ATC / PTI<small>Adaptive trust</small></div><div class="arrow">→</div>
        <div class="flow-box">Risk + Self-Healing<small>Monitor • Isolate • Recover</small></div><div class="arrow">→</div>
        <div class="flow-box">Blockchain Audit<small>Tamper-evident history</small></div>
      </div>
    </div>
    ''', unsafe_allow_html=True)

def risk_banner(level, score):
    if level == "HIGH":
        style, icon, text = "background:rgba(239,68,68,.10);border-color:rgba(239,68,68,.30);color:#fecaca", "🔴", "Isolate / investigate"
    elif level == "MEDIUM":
        style, icon, text = "background:rgba(245,158,11,.10);border-color:rgba(245,158,11,.30);color:#fde68a", "🟠", "Place under monitoring"
    else:
        style, icon, text = "background:rgba(34,197,94,.10);border-color:rgba(34,197,94,.25);color:#bbf7d0", "🟢", "No major risk pattern detected"
    st.markdown(f'<div style="padding:16px 18px;border:1px solid;border-radius:15px;{style}"><b style="font-size:1.1rem">{icon} {level} RISK</b><span style="float:right;font-weight:700">Risk score {score}/100</span><div style="margin-top:5px;font-size:.86rem">{text}</div></div>', unsafe_allow_html=True)

def chain_diagram():
    st.markdown('''
    <div class="flow-wrap">
      <div class="eyebrow">TAMPER-EVIDENT AUDIT CHAIN</div>
      <div class="flow">
        <div class="flow-box">TX 01<small>Genesis / record</small></div><div class="arrow">→</div>
        <div class="flow-box">Hash A<small>SHA-256</small></div><div class="arrow">→</div>
        <div class="flow-box">TX 02<small>Previous = Hash A</small></div><div class="arrow">→</div>
        <div class="flow-box">Hash B<small>Linked record</small></div><div class="arrow">→</div>
        <div class="flow-box">TX 03<small>Chain continues</small></div>
      </div>
    </div>
    ''', unsafe_allow_html=True)

def healing_diagram():
    st.markdown('''
    <div class="flow-wrap">
      <div class="eyebrow">SELF-HEALING TRUST LOOP</div>
      <div class="flow">
        <div class="flow-box">Good history<small>Trust increases</small></div><div class="arrow">→</div>
        <div class="flow-box">Normal state<small>Network stable</small></div><div class="arrow">→</div>
        <div class="flow-box">Anomaly<small>Trust penalty</small></div><div class="arrow">→</div>
        <div class="flow-box">Monitor / Isolate<small>Risk response</small></div><div class="arrow">→</div>
        <div class="flow-box">Compliant recovery<small>Trust can recover</small></div>
      </div>
    </div>
    ''', unsafe_allow_html=True)

apply_theme()


# ============================================================
# VERSION 3 UI — SIMPLE USER + RESEARCHER VIEW
# ============================================================
def apply_theme():
    st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at 20% 0%, #0d2540 0%, #07111e 35%, #050b14 100%); }
    [data-testid="stSidebar"] { background: linear-gradient(180deg,#071321 0%,#0b1728 100%); border-right:1px solid rgba(148,163,184,.16); }
    .hero { padding:24px 28px; border-radius:22px; background:linear-gradient(135deg,rgba(14,65,115,.58),rgba(7,35,61,.70)); border:1px solid rgba(56,189,248,.20); box-shadow:0 20px 55px rgba(0,0,0,.30); margin-bottom:18px; }
    .hero h1 { margin:0; color:#f8fafc; font-size:2.05rem; letter-spacing:-.03em; }
    .hero p { margin:7px 0 0; color:#b9c7d9; font-size:.98rem; }
    .eyebrow { color:#67e8f9; font-weight:800; text-transform:uppercase; letter-spacing:.12em; font-size:.70rem; margin-bottom:7px; }
    .glass { padding:17px 18px; border-radius:18px; background:rgba(11,24,40,.82); border:1px solid rgba(148,163,184,.13); box-shadow:0 10px 30px rgba(0,0,0,.20); height:100%; }
    .glass h3 { margin:0 0 7px; color:#f1f5f9; font-size:1.02rem; }
    .glass p { margin:0; color:#aebed0; font-size:.88rem; line-height:1.48; }
    .kpi { padding:16px 17px; border-radius:17px; background:linear-gradient(180deg,rgba(17,31,49,.96),rgba(8,17,29,.96)); border:1px solid rgba(148,163,184,.13); min-height:105px; }
    .kpi .label { color:#94a3b8; font-size:.72rem; text-transform:uppercase; letter-spacing:.07em; }
    .kpi .value { color:#f8fafc; font-size:1.62rem; font-weight:850; margin-top:5px; }
    .kpi .sub { color:#67e8f9; font-size:.74rem; margin-top:3px; }
    .score-card { padding:16px; border-radius:18px; background:#0b192a; border:1px solid rgba(148,163,184,.14); }
    .score-title { color:#94a3b8; font-size:.72rem; text-transform:uppercase; letter-spacing:.08em; }
    .score-value { font-size:1.9rem; font-weight:850; color:#f8fafc; }
    .score-status { color:#cbd5e1; font-size:.76rem; }
    .bar { height:9px; background:#1e293b; border-radius:99px; overflow:hidden; margin-top:9px; }
    .bar > div { height:100%; border-radius:99px; }
    .flow-wrap { padding:18px; border-radius:20px; background:rgba(8,20,34,.84); border:1px solid rgba(148,163,184,.13); margin:10px 0 18px; }
    .flow { display:flex; align-items:center; justify-content:center; gap:7px; flex-wrap:wrap; }
    .flow-box { min-width:128px; text-align:center; padding:12px 10px; border-radius:14px; background:linear-gradient(180deg,#142a43,#0b192a); border:1px solid rgba(56,189,248,.17); color:#e2e8f0; font-weight:750; font-size:.82rem; }
    .flow-box small { display:block; color:#94a3b8; font-weight:400; margin-top:4px; }
    .arrow { color:#38bdf8; font-size:1.25rem; font-weight:800; }
    .journey { display:flex; align-items:center; justify-content:space-between; gap:5px; flex-wrap:wrap; padding:17px; border-radius:19px; background:rgba(6,18,31,.88); border:1px solid rgba(148,163,184,.12); }
    .journey-node { flex:1; min-width:115px; text-align:center; padding:12px 8px; border-radius:15px; background:#0e2238; border:1px solid rgba(56,189,248,.14); }
    .journey-icon { font-size:1.65rem; }
    .journey-name { color:#e2e8f0; font-weight:750; font-size:.82rem; margin-top:3px; }
    .journey-sub { color:#94a3b8; font-size:.70rem; margin-top:3px; }
    .journey-arrow { color:#38bdf8; font-size:1.2rem; }
    .simple-step { padding:15px; border-radius:17px; background:#0c1c2e; border:1px solid rgba(148,163,184,.13); height:100%; }
    .simple-step .num { display:inline-flex; width:28px; height:28px; border-radius:50%; align-items:center; justify-content:center; background:#0ea5e9; color:white; font-weight:800; margin-bottom:7px; }
    .simple-step h4 { margin:0 0 5px; color:#f8fafc; font-size:.98rem; }
    .simple-step p { margin:0; color:#aebed0; font-size:.82rem; line-height:1.45; }
    .legend { display:flex; gap:10px; flex-wrap:wrap; margin:7px 0 12px; }
    .legend-item { padding:7px 11px; border-radius:999px; font-size:.75rem; font-weight:750; }
    .legend-low { background:rgba(34,197,94,.12); color:#86efac; border:1px solid rgba(34,197,94,.25); }
    .legend-med { background:rgba(245,158,11,.12); color:#fde68a; border:1px solid rgba(245,158,11,.25); }
    .legend-high { background:rgba(239,68,68,.12); color:#fca5a5; border:1px solid rgba(239,68,68,.25); }
    .risk-banner { padding:16px 18px; border-radius:16px; border:1px solid; }
    .risk-banner .title { font-size:1.12rem; font-weight:850; }
    .risk-banner .action { margin-top:4px; font-size:.84rem; }
    .plain-result { padding:17px 19px; border-radius:17px; background:#0b1c2e; border:1px solid rgba(148,163,184,.13); }
    .plain-result h3 { margin:0 0 5px; color:#f8fafc; }
    .plain-result p { margin:0; color:#b9c7d9; line-height:1.5; }
    .research-note { padding:13px 16px; border-left:3px solid #22d3ee; background:rgba(34,211,238,.06); color:#b8c7d9; border-radius:10px; margin:12px 0; }
    .section-title { font-size:1.28rem; font-weight:820; color:#f8fafc; margin:18px 0 9px; }
    </style>
    """, unsafe_allow_html=True)

def hero(title, subtitle, eyebrow="PHARMACHAIN SECURE"):
    st.markdown(f'<div class="hero"><div class="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)

def section(title, subtitle=None):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle: st.caption(subtitle)

def kpi(label, value, sub=""):
    st.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div><div class="sub">{sub}</div></div>', unsafe_allow_html=True)

def score_card(title, value, status, kind="good"):
    v=max(0,min(100,float(value)))
    if kind in ("risk","high"): color="#ef4444"
    elif kind in ("medium","warning"): color="#f59e0b"
    elif kind in ("good","low"): color="#22c55e"
    else: color="#38bdf8"
    st.markdown(f'<div class="score-card"><div class="score-title">{title}</div><div class="score-value">{v:.1f}<span style="font-size:.78rem;color:#64748b">/100</span></div><div class="score-status">{status}</div><div class="bar"><div style="width:{v:.1f}%;background:{color}"></div></div></div>', unsafe_allow_html=True)

def architecture_diagram():
    st.markdown('''<div class="flow-wrap"><div class="eyebrow">HOW THE SYSTEM WORKS</div><div class="flow">
    <div class="flow-box">💊 Medicine<small>Enter / scan details</small></div><div class="arrow">→</div>
    <div class="flow-box">🔎 Check<small>Identity • batch • expiry</small></div><div class="arrow">→</div>
    <div class="flow-box">🌡️ Conditions<small>Temperature • humidity • travel</small></div><div class="arrow">→</div>
    <div class="flow-box">🧠 Analyse<small>Find unusual patterns</small></div><div class="arrow">→</div>
    <div class="flow-box">📊 Trust<small>MACS • ATC • PTI</small></div><div class="arrow">→</div>
    <div class="flow-box">🚦 Decide<small>Low • Medium • High</small></div><div class="arrow">→</div>
    <div class="flow-box">⛓️ Record<small>Tamper-evident audit</small></div></div></div>''', unsafe_allow_html=True)

def medicine_journey():
    st.markdown('''<div class="journey">
    <div class="journey-node"><div class="journey-icon">🏭</div><div class="journey-name">Manufacturer</div><div class="journey-sub">Medicine made</div></div><div class="journey-arrow">→</div>
    <div class="journey-node"><div class="journey-icon">🚚</div><div class="journey-name">Distributor</div><div class="journey-sub">Transported</div></div><div class="journey-arrow">→</div>
    <div class="journey-node"><div class="journey-icon">🏢</div><div class="journey-name">Warehouse</div><div class="journey-sub">Stored safely</div></div><div class="journey-arrow">→</div>
    <div class="journey-node"><div class="journey-icon">🏪</div><div class="journey-name">Pharmacy</div><div class="journey-sub">Checked before sale</div></div><div class="journey-arrow">→</div>
    <div class="journey-node"><div class="journey-icon">👤</div><div class="journey-name">Patient</div><div class="journey-sub">Safer decision</div></div></div>''', unsafe_allow_html=True)

def risk_legend():
    st.markdown('<div class="legend"><div class="legend-item legend-low">🟢 LOW — normal</div><div class="legend-item legend-med">🟡 MEDIUM — check / monitor</div><div class="legend-item legend-high">🔴 HIGH — investigate</div></div>', unsafe_allow_html=True)

def risk_banner(level, score):
    if level == "HIGH": style="background:rgba(239,68,68,.10);border-color:rgba(239,68,68,.34);color:#fecaca"; icon="🔴"; action="Stop / isolate the record and investigate before release."
    elif level == "MEDIUM": style="background:rgba(245,158,11,.10);border-color:rgba(245,158,11,.34);color:#fde68a"; icon="🟡"; action="Place the medicine or participant under monitoring and re-check the evidence."
    else: style="background:rgba(34,197,94,.10);border-color:rgba(34,197,94,.30);color:#bbf7d0"; icon="🟢"; action="No major risk pattern was detected from the supplied evidence."
    st.markdown(f'<div class="risk-banner" style="{style}"><div class="title">{icon} {level} RISK <span style="float:right">{float(score):.1f}/100</span></div><div class="action">{action}</div></div>', unsafe_allow_html=True)

def chain_diagram():
    st.markdown('''<div class="flow-wrap"><div class="eyebrow">SIMPLE BLOCKCHAIN VIEW</div><div class="flow">
    <div class="flow-box">📦 Transaction 1<small>Medicine record</small></div><div class="arrow">→</div>
    <div class="flow-box">🔐 Hash A<small>Digital fingerprint</small></div><div class="arrow">→</div>
    <div class="flow-box">📦 Transaction 2<small>Links to Hash A</small></div><div class="arrow">→</div>
    <div class="flow-box">🔐 Hash B<small>Another fingerprint</small></div><div class="arrow">→</div>
    <div class="flow-box">📦 Transaction 3<small>Chain continues</small></div></div></div>''', unsafe_allow_html=True)

def healing_diagram():
    st.markdown('''<div class="flow-wrap"><div class="eyebrow">SELF-HEALING TRUST LOOP</div><div class="flow">
    <div class="flow-box">🟢 Good history<small>Trust grows</small></div><div class="arrow">→</div>
    <div class="flow-box">✅ Normal<small>Network stable</small></div><div class="arrow">→</div>
    <div class="flow-box">⚠️ Anomaly<small>Trust falls</small></div><div class="arrow">→</div>
    <div class="flow-box">🛑 Monitor / isolate<small>Risk response</small></div><div class="arrow">→</div>
    <div class="flow-box">🔄 Recovery<small>Trust can rebuild</small></div></div></div>''', unsafe_allow_html=True)

def simple_result_text(level):
    if level == "HIGH": return "This medicine needs attention. The available information shows a high-risk pattern, so it should be isolated and investigated before being released."
    if level == "MEDIUM": return "This medicine needs a second check. Some warning signs were found, so keep it under monitoring until the evidence is confirmed."
    return "This medicine looks low risk based on the information provided. No major warning pattern was detected, but the result depends on the quality of the supplied evidence."

def action_card(level):
    if level == "HIGH": return "🛑 Recommended action", "Do not release until the issue is investigated. Check identity, batch, package, environment and transport records."
    if level == "MEDIUM": return "🟡 Recommended action", "Keep under monitoring. Re-check the flagged evidence and collect stronger source data if possible."
    return "🟢 Recommended action", "Continue normal handling and keep the evidence record for audit."

def plot_risk_distribution(d):
    if not MATPLOTLIB_AVAILABLE:
        st.bar_chart(d.risk_level.value_counts()); return
    counts=[int((d.risk_level==x).sum()) for x in ["LOW","MEDIUM","HIGH"]]
    fig,ax=plt.subplots(figsize=(7.2,3.4)); bars=ax.bar(["LOW","MEDIUM","HIGH"],counts,color=["#22c55e","#f59e0b","#ef4444"],edgecolor="none")
    ax.set_ylabel("Transactions"); ax.set_title("Risk distribution"); ax.grid(axis="y",alpha=.18); ax.spines[['top','right']].set_visible(False)
    for b,v in zip(bars,counts): ax.text(b.get_x()+b.get_width()/2,v+max(counts+[1])*.02,str(v),ha="center",fontweight="bold")
    fig.tight_layout(); st.pyplot(fig,use_container_width=True); plt.close(fig)

def plot_framework_means(d):
    if not MATPLOTLIB_AVAILABLE:
        st.bar_chart(d[["macs","atc","pti","recovery"]].mean()); return
    vals=[float(d.macs.mean()),float(d.atc.mean()),float(d.pti.mean()),float(d.recovery.mean())]
    fig,ax=plt.subplots(figsize=(7.2,3.4)); bars=ax.bar(["MACS","ATC","PTI","Recovery"],vals,color=["#22c55e","#f59e0b","#38bdf8","#a78bfa"],edgecolor="none")
    ax.set_ylim(0,100); ax.set_ylabel("Score / 100"); ax.set_title("Framework score comparison"); ax.grid(axis="y",alpha=.18); ax.spines[['top','right']].set_visible(False)
    for b,v in zip(bars,vals): ax.text(b.get_x()+b.get_width()/2,v+2,f"{v:.1f}",ha="center",fontweight="bold")
    fig.tight_layout(); st.pyplot(fig,use_container_width=True); plt.close(fig)

def plot_participant_history(r):
    if not MATPLOTLIB_AVAILABLE:
        st.line_chart(r[["id","atc","pti","recovery"]].set_index("id")); return
    fig,ax=plt.subplots(figsize=(8,3.6)); x=r.id.astype(int)
    ax.plot(x,r.atc,marker="o",label="ATC",color="#f59e0b"); ax.plot(x,r.pti,marker="o",label="PTI",color="#38bdf8"); ax.plot(x,r.recovery,marker="o",label="Recovery",color="#22c55e")
    ax.set_ylim(0,100); ax.set_xlabel("Transaction ID"); ax.set_ylabel("Score / 100"); ax.set_title("Trust history"); ax.grid(alpha=.16); ax.legend(); ax.spines[['top','right']].set_visible(False); fig.tight_layout(); st.pyplot(fig,use_container_width=True); plt.close(fig)

def plot_feature_importance(importance):
    if not MATPLOTLIB_AVAILABLE:
        st.bar_chart(importance.set_index("Feature")); return
    q=importance.sort_values("Importance")
    fig,ax=plt.subplots(figsize=(8,4)); ax.barh(q.Feature,q.Importance,color="#38bdf8",edgecolor="none"); ax.set_xlabel("Importance"); ax.set_title("Feature importance"); ax.grid(axis="x",alpha=.16); ax.spines[['top','right']].set_visible(False); fig.tight_layout(); st.pyplot(fig,use_container_width=True); plt.close(fig)

apply_theme()

if "result" not in st.session_state: st.session_state.result=None
if "saved" not in st.session_state: st.session_state.saved=False
if "research_df" not in st.session_state: st.session_state.research_df=None
if "ml_result" not in st.session_state: st.session_state.ml_result=None

st.sidebar.markdown("# 💊 PharmaChain Secure")
st.sidebar.caption("Safe medicines • trusted supply chain • transparent audit")
st.sidebar.markdown('<span class="status-pill">RESEARCH PROTOTYPE</span>', unsafe_allow_html=True)
view=st.sidebar.radio("Interface",["👤 Simple User","🔬 Researcher"],index=0)
pages=["🏠 Overview","🔍 Verify Medicine","📊 Dashboard","📋 Medicine Database","🗺️ Supply Chain Map","⛓️ Blockchain Audit","🚨 Anomaly & Alerts","👥 Participant Profiles","🕸️ Risk Network","🧾 Investigation Cases","🛡️ Regulator Dashboard","🧪 Research Evaluation"]
page=st.sidebar.radio("Navigation",pages)
st.sidebar.divider(); st.sidebar.metric("Audit transactions",count_tx()); st.sidebar.caption("🟢 Low • 🟡 Medium • 🔴 High")

if page=="🏠 Overview":
    hero("Pharmaceutical Supply Chain Integrity", "Check a medicine, understand the result, follow its journey and keep a tamper-evident audit trail.")
    architecture_diagram(); section("Medicine journey", "The system follows evidence across the supply chain instead of looking only at the final medicine record."); medicine_journey(); risk_legend()
    d=df_all(); total=0 if d is None else len(d); high=0 if d is None else int((d.risk_level=="HIGH").sum()); med=0 if d is None else int((d.risk_level=="MEDIUM").sum()); low=0 if d is None else int((d.risk_level=="LOW").sum()); avg_pti=0 if d is None or len(d)==0 else float(d.pti.mean())
    c1,c2,c3,c4,c5=st.columns(5)
    with c1:kpi("Transactions",total,"Audit records")
    with c2:kpi("Low risk",low,"🟢 Normal")
    with c3:kpi("Medium risk",med,"🟡 Monitoring")
    with c4:kpi("High risk",high,"🔴 Investigation")
    with c5:kpi("Average PTI",f"{avg_pti:.1f}","Overall trust")
    section("Use it in 3 simple steps")
    a,b,c=st.columns(3)
    with a: st.markdown('<div class="simple-step"><div class="num">1</div><h4>Enter or scan</h4><p>Add medicine, batch, package, expiry and optional sensor or transport evidence.</p></div>',unsafe_allow_html=True)
    with b: st.markdown('<div class="simple-step"><div class="num">2</div><h4>Check the result</h4><p>The system combines the evidence and shows a clear green, yellow or red risk result.</p></div>',unsafe_allow_html=True)
    with c: st.markdown('<div class="simple-step"><div class="num">3</div><h4>Take action</h4><p>Follow the recommendation, save the record and keep the audit history for later investigation.</p></div>',unsafe_allow_html=True)
    section("What do the scores mean?")
    a,b,c=st.columns(3)
    with a: st.markdown('<div class="glass"><h3>💊 MACS — Medicine check</h3><p>Looks at evidence about the medicine itself: identity, package, batch, expiry, temperature, humidity and transport.</p></div>',unsafe_allow_html=True)
    with b: st.markdown('<div class="glass"><h3>👥 ATC — Participant trust</h3><p>Looks at the behaviour and history of the people or organisations handling the medicine.</p></div>',unsafe_allow_html=True)
    with c: st.markdown('<div class="glass"><h3>⛓️ PTI — Overall trust</h3><p>Combines medicine confidence, participant trust and compliance into one overall framework score.</p></div>',unsafe_allow_html=True)
    if view=="🔬 Researcher":
        section("Research architecture"); healing_diagram(); st.markdown('<div class="research-note"><b>Research note:</b> MACS, ATC and PTI are proposed framework scores, not validated probabilities. Synthetic ML labels must not be presented as real pharmaceutical ground truth.</div>',unsafe_allow_html=True)
    else:
        with st.expander("🔬 Show research details"): st.write("Research View exposes score breakdowns, participant history, audit hashes and controlled ML experiments.")

elif page=="🔍 Verify Medicine":
    hero("Check a Medicine", "Enter the available evidence and get a simple risk decision. You do not need a QR code to use the system.", "MEDICINE VERIFICATION")
    st.info("💡 QR/barcode, sensor data, GPS and timestamps are optional. Manual and simulated evidence is clearly marked.")
    with st.expander("📷 Optional QR / Barcode",expanded=False):
        scan_file=st.file_uploader("Upload medicine QR/barcode image",type=["png","jpg","jpeg"],key="scan"); scanned=scan_image(scan_file) if scan_file else None; payload={}
        if scanned: st.success("Code detected."); st.code(scanned); payload=parse_scan(scanned)
        else: st.caption("No scan is required. You can enter medicine details manually.")
    section("1. Medicine details")
    c1,c2,c3=st.columns(3); medicine_id=c1.text_input("Medicine ID",payload.get("medicine_id","MED001")); medicine_name=c2.text_input("Medicine name",payload.get("medicine_name","Paracetamol")); batch=c3.text_input("Batch number",payload.get("batch_number","BATCH001"))
    c1,c2,c3=st.columns(3); manufacturer=c1.text_input("Manufacturer",payload.get("manufacturer","ABC Pharma")); distributor=c2.text_input("Distributor",payload.get("distributor","Distributor A")); pharmacy=c3.text_input("Pharmacy",payload.get("pharmacy","Pharmacy A"))
    c1,c2,c3=st.columns(3); identity_source=c1.selectbox("How was identity checked?",["Manual verified identity","Batch + manufacturer record","QR code","GS1/barcode scan","No verified identity"]); qr_verified=c2.checkbox("QR/barcode verified",value=bool(scanned)); expiry=c3.date_input("Expiry date",value=date.today()+timedelta(days=365))
    c1,c2,c3=st.columns(3); package=c1.checkbox("Package intact",True); batch_ok=c2.checkbox("Batch verified",True); location_source=c3.selectbox("Location evidence",["GPS/device","Verified map/address","User entered","Unavailable"])
    section("2. Supply-chain locations"); locs=[]
    for role in ["Manufacturer","Distributor","Pharmacy"]:
        a,b,c,d=st.columns(4); name={"Manufacturer":manufacturer,"Distributor":distributor,"Pharmacy":pharmacy}[role]; a.write(f"**{role}** — {name}"); lat=a.number_input(f"{role} latitude",value=12.9716 if role=="Manufacturer" else (19.0760 if role=="Distributor" else 12.9352),format="%.6f",key=role+"lat"); lon=b.number_input(f"{role} longitude",value=77.5946 if role=="Manufacturer" else (72.8777 if role=="Distributor" else 77.6245),format="%.6f",key=role+"lon"); address=c.text_input(f"{role} location",f"{role} location",key=role+"addr"); d.caption("May be simulated for research."); locs.append((role,lat,lon,address))
    section("3. Environment evidence"); env_source=st.radio("Source",["IoT/data logger CSV","Manual observation","Research simulation"],horizontal=True); temp=25.0; hum=50.0; tmin=tmax=hmin=hmax=None; te=he=0
    if env_source=="IoT/data logger CSV":
        sensor_file=st.file_uploader("CSV with temperature and humidity",type=["csv"],key="sensor")
        if sensor_file:
            sx,err=sensor_csv(sensor_file)
            if sx is not None:
                ss=sensor_summary(sx); temp,hum,tmin,tmax,hmin,hmax,te,he=ss["temperature"],ss["humidity"],ss["temp_min"],ss["temp_max"],ss["humidity_min"],ss["humidity_max"],ss["temp_excursions"],ss["humidity_excursions"]; st.success(f"Loaded {ss['rows']} sensor readings."); st.dataframe(sx.head(20),use_container_width=True,hide_index=True)
            else: st.error(err)
    elif env_source=="Manual observation":
        a,b=st.columns(2); temp=a.number_input("Temperature °C",value=25.0); hum=b.number_input("Humidity %",value=50.0); tmin=tmax=temp; hmin=hmax=hum
    else:
        a,b=st.columns(2); temp=a.number_input("Simulated temperature °C",value=25.0); hum=b.number_input("Simulated humidity %",value=50.0); tmin=tmax=temp; hmin=hmax=hum; st.caption("Research simulation — not a real sensor measurement.")
    section("4. Transport evidence"); trans_source=st.radio("Transport source",["Dispatch + receipt timestamps","Manual entry","Research simulation"],horizontal=True); dispatch=receipt=""; travel=24.0
    if trans_source=="Dispatch + receipt timestamps":
        dispatch_default=datetime.now()-timedelta(hours=24); receipt_default=datetime.now(); a,b=st.columns(2); dispatch_date=a.date_input("Dispatch date",value=dispatch_default.date()); dispatch_time=a.time_input("Dispatch time",value=dispatch_default.time().replace(second=0,microsecond=0)); receipt_date=b.date_input("Receipt date",value=receipt_default.date()); receipt_time=b.time_input("Receipt time",value=receipt_default.time().replace(second=0,microsecond=0)); dispatch_dt=datetime.combine(dispatch_date,dispatch_time); receipt_dt=datetime.combine(receipt_date,receipt_time); dispatch=dispatch_dt.isoformat(); receipt=receipt_dt.isoformat(); travel,err=transport_hours(dispatch,receipt)
        if err: st.error(err); travel=0.0
    elif trans_source=="Manual entry": travel=st.number_input("Transport time (hours)",min_value=0.0,value=24.0)
    else: travel=st.number_input("Simulated transport time (hours)",min_value=0.0,value=24.0); st.caption("Research simulation — not a logistics record.")
    section("5. Run the check")
    if st.button("🔎 CHECK MEDICINE + CALCULATE TRUST",type="primary",use_container_width=True):
        coords={}
        for role,lat,lon,address in locs: coords[role.lower()+"_lat"]=lat; coords[role.lower()+"_lon"]=lon; coords[role.lower()+"_location"]=address
        data={"medicine_id":medicine_id.strip(),"medicine_name":medicine_name.strip(),"batch_number":batch.strip(),"manufacturer":manufacturer.strip(),"distributor":distributor.strip(),"pharmacy":pharmacy.strip(),"expiry_date":str(expiry),"qr_verified":int(qr_verified),"identity_source":identity_source,"package_intact":int(package),"batch_verified":int(batch_ok),"temperature":float(temp),"humidity":float(hum),"transport_time":float(travel),"temperature_source":env_source,"humidity_source":env_source,"transport_source":trans_source,"location_source":location_source,"dispatch_time":dispatch,"receipt_time":receipt,"temp_min":tmin,"temp_max":tmax,"humidity_min":hmin,"humidity_max":hmax,"temp_excursions":te,"humidity_excursions":he,**coords}
        r,bd,ph=build(data); st.session_state.result=(r,bd,ph); st.session_state.saved=False
    if st.session_state.result:
        r,bd,ph=st.session_state.result; st.divider(); section("Your result"); risk_banner(r["risk_level"],r["risk_score"]); risk_legend(); st.markdown(f'<div class="plain-result"><h3>What this means</h3><p>{simple_result_text(r["risk_level"])}</p></div>',unsafe_allow_html=True)
        title,action=action_card(r["risk_level"]); (st.warning if r["risk_level"]!="LOW" else st.success)(f"**{title}:** {action}")
        a,b,c,d=st.columns(4); score_card("MACS",r["macs"],r["macs_status"],"good" if r["macs"]>=80 else "medium" if r["macs"]>=60 else "risk"); score_card("ATC",r["atc"],r["atc_status"],"good" if r["atc"]>=70 else "medium" if r["atc"]>=50 else "risk"); score_card("PTI",r["pti"],r["pti_status"],"good" if r["pti"]>=60 else "medium" if r["pti"]>=40 else "risk"); score_card("Risk score",r["risk_score"],r["risk_level"],"risk" if r["risk_level"]=="HIGH" else "medium" if r["risk_level"]=="MEDIUM" else "good")
        if view=="🔬 Researcher":
            x,y=st.columns(2); x.subheader("🧠 Why this risk?"); [x.write("• "+q) for q in r["risk_reasons"].split("; ") if q]; y.subheader("🔄 Self-healing"); y.write(f"**Network:** {r['network_status']}"); y.write(f"**Historical distributor trust:** {r['historical_trust']:.2f}"); y.write(f"**Trust change:** {r['trust_change']:+.2f}"); y.write(f"**Recovery score:** {r['recovery']:.2f} ({r['recovery_status']})")
            with st.expander("🧮 Technical scoring breakdown"): st.dataframe(pd.DataFrame(bd,columns=["Parameter","Points","Condition"]),use_container_width=True,hide_index=True); st.write({"Medicine Trust":r["medicine_trust"],"Success Rate":r["success_rate"],"Medicine Integrity":r["medicine_integrity"],"Compliance History":r["compliance_history"],"Historical Trust":r["historical_trust"]})
        else:
            with st.expander("ℹ️ What are MACS, ATC and PTI?"): st.write("MACS checks the medicine evidence. ATC reflects participant trust. PTI is the overall framework trust score. These are research scores, not certified probabilities.")
        st.subheader("⚠️ Detected warnings")
        if r["detected_problems"]=="None": st.success("No detected problems.")
        else:
            for q in r["detected_problems"].split("; "): st.error("✕ "+q)
        if view=="🔬 Researcher":
            st.subheader("📚 Evidence provenance"); st.dataframe(pd.DataFrame([{"Identity":r["identity_source"],"Temperature":r["temperature_source"],"Humidity":r["humidity_source"],"Transport":r["transport_source"],"Location":r["location_source"],"Temperature range":f"{r['temp_min']}–{r['temp_max']}","Humidity range":f"{r['humidity_min']}–{r['humidity_max']}"}]),use_container_width=True,hide_index=True)
        if not st.session_state.saved:
            if st.button("💾 SAVE RESULT TO DATABASE + AUDIT CHAIN",type="primary",use_container_width=True): tid,bh=save_tx(r); st.session_state.saved=True; st.session_state.txid=tid; st.session_state.bh=bh; st.success(f"Saved transaction {tid}."); st.rerun()
        else: st.success(f"Already saved as transaction {st.session_state.txid}.")
        if r["risk_level"] in ["MEDIUM","HIGH"] and st.button("🧾 CREATE INVESTIGATION CASE",use_container_width=True): cid=create_case(st.session_state.get("txid",0),r["risk_level"],r["risk_reasons"]); st.success(f"Created {cid}")
        st.download_button("📥 Download verification record",pd.DataFrame([r]).to_csv(index=False),file_name=f"{r['medicine_id']}_verification.csv",mime="text/csv",use_container_width=True)

elif page=="📊 Dashboard":
    hero("Supply Chain Dashboard", "A quick view of how many records look safe, need monitoring or need investigation.", "SYSTEM OVERVIEW"); d=df_all()
    if d is None or len(d)==0: st.info("No transactions yet. Go to Check a Medicine and save your first result.")
    else:
        risk_legend(); a,b,c,e=st.columns(4); kpi("Transactions",len(d),"Stored audit records"); kpi("Mean MACS",f"{d.macs.mean():.2f}","Medicine confidence"); kpi("Mean ATC",f"{d.atc.mean():.2f}","Participant trust"); kpi("Mean PTI",f"{d.pti.mean():.2f}","Overall trust")
        x,y=st.columns(2)
        with x: plot_risk_distribution(d)
        with y: plot_framework_means(d)
        st.subheader("Recent transactions"); st.dataframe(d[["id","medicine_id","medicine_name","batch_number","distributor","macs","atc","pti","risk_score","risk_level","verification_time"]].head(30),use_container_width=True,hide_index=True)

elif page=="📋 Medicine Database":
    hero("Medicine Database", "Search and inspect the evidence records created by the verification process.", "DATA EXPLORER"); d=df_all()
    if d is None or len(d)==0: st.info("Database is empty.")
    else:
        q=st.text_input("Search ID, name, batch, manufacturer, distributor or pharmacy"); f=d.copy()
        if q.strip():
            q=q.lower(); mask=False
            for col in ["medicine_id","medicine_name","batch_number","manufacturer","distributor","pharmacy"]: mask=mask|f[col].fillna("").astype(str).str.lower().str.contains(q,regex=False)
            f=f[mask]
        st.write(f"**{len(f)} matching records**"); risk_legend(); st.dataframe(f,use_container_width=True,hide_index=True); st.download_button("📥 Export database CSV",f.to_csv(index=False),"pharma_database_export.csv","text/csv")

elif page=="🗺️ Supply Chain Map":
    hero("Supply Chain Map", "See where the manufacturer, distributor and pharmacy records are located.", "GEOSPATIAL VIEW"); d=df_all()
    if d is None or len(d)==0: st.info("No data.")
    else:
        rows=[]
        for _,r in d.iterrows():
            for role,lat,lon,name in [("Manufacturer","manufacturer_lat","manufacturer_lon","manufacturer"),("Distributor","distributor_lat","distributor_lon","distributor"),("Pharmacy","pharmacy_lat","pharmacy_lon","pharmacy")]:
                if pd.notna(r.get(lat)) and pd.notna(r.get(lon)): rows.append({"Role":role,"Name":r.get(name,""),"Medicine":r.get("medicine_name",""),"Batch":r.get("batch_number",""),"Latitude":r[lat],"Longitude":r[lon],"Risk":r.get("risk_level",""),"Source":r.get("location_source","")})
        if not rows: st.warning("No coordinates stored.")
        else:
            ld=pd.DataFrame(rows); risk_legend(); st.dataframe(ld,use_container_width=True,hide_index=True)
            if MAP_AVAILABLE:
                fmap=folium.Map(location=[float(ld.Latitude.mean()),float(ld.Longitude.mean())],zoom_start=5)
                for _,r in ld.iterrows():
                    icon_color="red" if r.Risk=="HIGH" else "orange" if r.Risk=="MEDIUM" else "green"; folium.Marker([float(r.Latitude),float(r.Longitude)],popup=f"{r.Role}: {r.Name}<br>Medicine: {r.Medicine}<br>Batch: {r.Batch}<br>Risk: {r.Risk}<br>Source: {r.Source}",icon=folium.Icon(color=icon_color)).add_to(fmap)
                st_folium(fmap,use_container_width=True,height=550)
            else: st.info("Install folium and streamlit-folium for the interactive map.")

elif page=="⛓️ Blockchain Audit":
    hero("Blockchain Audit", "Understand the chain first, then inspect the technical hashes.", "INTEGRITY LAYER"); chain_diagram(); d=df_all()
    if d is None or len(d)==0: st.info("No transactions to audit.")
    else:
        ok,msg,bad=verify_chain(); st.success("🟢 Audit chain verified — no hash mismatch detected.") if ok else st.error("🔴 Audit chain mismatch detected.")
        with st.expander("🔬 Technical blockchain details",expanded=view=="🔬 Researcher"):
            st.caption("This prototype uses a local SHA-256 hash-linked audit chain. It is not a decentralized public blockchain."); st.dataframe(d[["id","medicine_id","batch_number","risk_level","previous_hash","block_hash","verification_time"]],use_container_width=True,hide_index=True); st.write(msg)
            if not ok: st.warning("In production, a hash mismatch should be treated as tampering evidence, not automatically repaired.")
            st.divider(); st.subheader("Legacy migration"); st.caption("Only for old prototype records whose schema changed. Back up first.")
            if st.button("🔧 Rebuild current audit chain"): n=rebuild_chain(); st.success(f"Rebuilt {n} transaction hashes using the current schema."); st.rerun()

elif page=="🚨 Anomaly & Alerts":
    hero("Anomaly & Alerts", "See the unusual patterns that caused records to be flagged.", "RISK INTELLIGENCE"); d=df_all()
    if d is None or len(d)==0: st.info("No data.")
    else:
        risk_legend(); a,b,c,e=st.columns(4); a.metric("🔴 High risk",int((d.risk_level=="HIGH").sum())); b.metric("🟡 Medium risk",int((d.risk_level=="MEDIUM").sum())); c.metric("Temp excursions",int(d.temp_excursions.fillna(0).sum())); e.metric("Duplicate records",int(d.duplicated(["medicine_id","batch_number"],keep=False).sum())); flagged=d[d.risk_level.isin(["MEDIUM","HIGH"]) | (d.detected_problems.fillna("")!="None")]; st.dataframe(flagged[["id","medicine_id","batch_number","distributor","risk_score","risk_level","detected_problems","risk_reasons"]],use_container_width=True,hide_index=True) if len(flagged) else st.success("🟢 No current anomalies.")

elif page=="👥 Participant Profiles":
    hero("Participant Trust", "See how trust changes for a manufacturer, distributor or pharmacy over time.", "TRUST ENGINE"); healing_diagram(); d=df_all()
    if d is None or len(d)==0: st.info("No participant data.")
    else:
        role=st.selectbox("Participant type",["Manufacturer","Distributor","Pharmacy"]); col={"Manufacturer":"manufacturer","Distributor":"distributor","Pharmacy":"pharmacy"}[role]; names=sorted([x for x in d[col].dropna().astype(str).unique() if x.strip()])
        if not names: st.info("No named participants.")
        else:
            name=st.selectbox("Select participant",names); ph=participant_history(name,role); r=d[d[col]==name]; a,b,c,e=st.columns(4); a.metric("Transactions",ph["count"]); b.metric("Current trust",f"{ph['current_trust']:.2f}"); c.metric("Risk events",ph["risk"]); e.metric("Good events",ph["good"])
            if len(r): plot_participant_history(r); st.dataframe(r[["id","medicine_name","batch_number","atc","pti","recovery","risk_level","risk_score","verification_time"]],use_container_width=True,hide_index=True)
            st.info(f"Adaptive trust is reconstructed from transaction history. Current trust: {ph['current_trust']:.2f}/100.")

elif page=="🕸️ Risk Network":
    hero("Supply-Chain Risk Network", "Find repeated risk events across participants and relationships.", "NETWORK INTELLIGENCE"); d=df_all()
    if d is None or len(d)==0: st.info("Save transactions to build the network.")
    else:
        rows=[]
        for _,r in d.iterrows(): rows.append({"Manufacturer":r.manufacturer,"Distributor":r.distributor,"Pharmacy":r.pharmacy,"Risk":r.risk_level,"PTI":r.pti,"ATC":r.atc})
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True); st.subheader("Participant risk frequency"); counts=[]
        for col,role in [("manufacturer","Manufacturer"),("distributor","Distributor"),("pharmacy","Pharmacy")]:
            q=d[d.risk_level.isin(["MEDIUM","HIGH"])][col].fillna("").value_counts()
            for n,v in q.items():
                if n: counts.append({"Participant":n,"Role":role,"Risk events":int(v)})
        cd=pd.DataFrame(counts); st.dataframe(cd.sort_values("Risk events",ascending=False) if len(cd) else pd.DataFrame(columns=["Participant","Role","Risk events"]),use_container_width=True,hide_index=True)

elif page=="🧾 Investigation Cases":
    hero("Investigation Cases", "Turn suspicious transactions into traceable evidence bundles.", "CASE MANAGEMENT"); d=cases_df()
    if d is None or len(d)==0: st.info("No investigation cases.")
    else:
        st.dataframe(d,use_container_width=True,hide_index=True); selected=st.selectbox("Case",d.case_id.tolist()); case=d[d.case_id==selected].iloc[0]; tx=df_all(); txrow=tx[tx.id==case.transaction_id] if tx is not None else pd.DataFrame()
        if len(txrow): st.subheader("Evidence bundle"); st.dataframe(txrow.T.rename(columns={txrow.index[0]:"Value"}),use_container_width=True); st.download_button("📥 Export case evidence JSON",txrow.iloc[0].to_json(indent=2),f"{selected}.json","application/json")

elif page=="🛡️ Regulator Dashboard":
    hero("Regulatory & Oversight Dashboard", "Prioritize high-risk medicines, participants and environmental issues.", "OVERSIGHT"); d=df_all()
    if d is None or len(d)==0: st.info("No transactions yet.")
    else:
        a,b,c,e=st.columns(4); a.metric("Total checks",len(d)); b.metric("🔴 High-risk",int((d.risk_level=="HIGH").sum())); c.metric("Suspicious participants",int((d.atc<50).sum())); e.metric("Possible tampering",0 if verify_chain()[0] else 1); st.subheader("Priority records"); pr=d.sort_values(["risk_score","pti"],ascending=[False,True]); st.dataframe(pr[["id","medicine_name","batch_number","manufacturer","distributor","risk_score","risk_level","pti","detected_problems"]].head(50),use_container_width=True,hide_index=True); st.subheader("Environmental compliance"); st.write({"temperature excursions":int(d.temp_excursions.fillna(0).sum()),"humidity excursions":int(d.humidity_excursions.fillna(0).sum()),"records with >72h transport":int((d.transport_time.fillna(0)>72).sum())})

elif page=="🧪 Research Evaluation":
    hero("Research Evaluation", "Measure the proposed framework and run controlled ML experiments without confusing simulation with real-world validation.", "EXPERIMENT LAB"); d=df_all()
    if d is not None and len(d):
        a,b,c,e=st.columns(4); a.metric("N saved",len(d)); b.metric("Mean MACS",f"{d.macs.mean():.2f}"); c.metric("Mean ATC",f"{d.atc.mean():.2f}"); e.metric("Mean PTI",f"{d.pti.mean():.2f}"); st.subheader("Observed risk distribution"); risk_legend(); plot_risk_distribution(d); st.subheader("Adaptive trust trend"); plot_participant_history(d.sort_values("id")[["id","atc","pti","recovery"]].assign(risk_level="LOW")); st.download_button("📥 Download saved research dataset",d.to_csv(index=False),"pharmachain_research_dataset.csv","text/csv")
    st.divider(); st.subheader("Controlled research simulation"); n=st.slider("Synthetic sample size",200,5000,1200,100); seed=st.number_input("Random seed",0,9999,42)
    if st.button("🧪 Generate + evaluate ML model",type="primary"):
        rdf=generate_research_data(n,int(seed)); st.session_state.research_df=rdf; result,err=run_ml_experiment(rdf); st.session_state.ml_result=result
        if err: st.error(err)
    if st.session_state.get("research_df") is not None:
        rdf=st.session_state.research_df; st.caption("Synthetic research data. Labels are generated by a controlled simulation rule and are not real pharmaceutical ground truth."); st.dataframe(rdf.head(30),use_container_width=True,hide_index=True); result=st.session_state.get("ml_result")
        if result:
            st.subheader("ML evaluation"); m=result["metrics"]; cols=st.columns(4)
            for c,(k,v) in zip(cols,m.items()): c.metric(k,f"{v*100:.2f}%")
            st.write("Confusion matrix"); st.dataframe(pd.DataFrame(result["matrix"],index=["Actual 0","Actual 1"],columns=["Predicted 0","Predicted 1"]),use_container_width=False); st.subheader("Feature importance"); plot_feature_importance(result["importance"])
        st.download_button("📥 Download synthetic experiment dataset",rdf.to_csv(index=False),"pharmachain_synthetic_experiment.csv","text/csv")
    st.caption("For a publishable accuracy claim, replace simulated labels with independently verified ground-truth data and report the train/test protocol and class balance.")

# ============================================================
# ADMIN / SAFETY FOOTER
# ============================================================
st.sidebar.divider()
with st.sidebar.expander("⚠️ Prototype data controls"):
    st.caption("Deleting data is irreversible. Export a backup before clearing.")
    if st.button("Export DB CSV before clear"):
        d=df_all(); st.download_button("Download backup",d.to_csv(index=False) if d is not None else "","pharma_backup.csv","text/csv")
    if st.button("Delete ALL test transactions",type="secondary"):
        clear_tx(); st.warning("All prototype transactions and cases were deleted."); st.rerun()
st.sidebar.caption("Research prototype — not a pharmaceutical regulatory certification system.")
