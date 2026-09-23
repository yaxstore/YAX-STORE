const axios = require('axios');
const crypto = require('crypto');

const AES_KEY = Buffer.from([89,103,38,116,99,37,68,69,117,104,54,37,90,99,94,56]);
const AES_IV = Buffer.from([54,111,121,90,68,114,50,50,69,51,121,99,104,106,77,37]);
const API_SECRET = '2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3';

const REGION_LANG = {
  ME:'ar', IND:'hi', ID:'id', VN:'vi', TH:'th',
  BD:'bn', PK:'ur', TW:'zh', CIS:'ru', SAC:'es',
  SG:'en', US:'en', EU:'en', LK:'en', GHOST:'bn'
};

function enc(hex) {
  const c = crypto.createCipheriv('aes-128-cbc', AES_KEY, AES_IV);
  return Buffer.concat([c.update(Buffer.from(hex,'hex')), c.final()]).toString('hex');
}

function sig(p) {
  return crypto.createHmac('sha256', API_SECRET).update(p).digest('hex');
}

function genPwd() {
  const ch = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let r = '';
  for (let i=0;i<8;i++) r += ch[Math.floor(Math.random()*ch.length)];
  return 'Yax-' + r + '-CORE';
}

function varint(n) {
  const o = [];
  while (true) {
    let b = n & 0x7f;
    n >>>= 7;
    if (n) b |= 0x80;
    o.push(b);
    if (!n) break;
  }
  return Buffer.from(o);
}

function proto(f) {
  const c = [];
  for (const [k,v] of Object.entries(f)) {
    const n = parseInt(k);
    if (typeof v === 'string') {
      const b = Buffer.from(v,'utf-8');
      c.push(varint((n<<3)|2), varint(b.length), b);
    } else if (typeof v === 'number') {
      c.push(varint((n<<3)|0), varint(v));
    }
  }
  return Buffer.concat(c);
}

async function gen(region, prefix) {
  const pwd = genPwd();
  const lang = REGION_LANG[region.toUpperCase()] || 'en';
  const s = axios.create({
    timeout: 8000,
    headers: {
      'User-Agent': 'GarenaMSDK/4.0.44(25028RN03A ;Android 15;ar;EG;app 1.132.1 2019121229;)',
      'Accept': 'application/json',
      'Accept-Encoding': 'gzip'
    },
    validateStatus: () => true
  });

  // ===== STEP 1: Register =====
  const rp = JSON.stringify({ app_id:100067, client_type:2, password:pwd, source:2 });
  const r = await s.post(
    'https://100067.connect.garena.com/api/v2/oauth/guest:register',
    rp,
    {
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': 'Signature ' + sig(rp),
        'Host': '100067.connect.garena.com'
      }
    }
  );

  if (r.status !== 200 || !r.data || r.data.code !== 0) {
    throw new Error('REG_FAIL status=' + r.status + ' data=' + JSON.stringify(r.data).substring(0,200));
  }
  const uid = r.data.data.uid;

  // ===== STEP 2: Token =====
  const tp = JSON.stringify({
    client_id:100067, client_secret:API_SECRET, client_type:2,
    device_id:'02-344afb0e-593c-40b7-92f2-171972f74807',
    password:pwd, response_type:'token', uid
  });
  const t = await s.post(
    'https://100067.connect.garena.com/api/v2/oauth/guest/token:grant',
    tp,
    {
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': 'Signature ' + sig(tp),
        'Host': '100067.connect.garena.com'
      }
    }
  );

  if (t.status !== 200 || !t.data || t.data.code !== 0) {
    throw new Error('TOK_FAIL status=' + t.status + ' data=' + JSON.stringify(t.data).substring(0,200));
  }
  const at = t.data.data.access_token;
  const oi = t.data.data.open_id;

  // ===== STEP 2.5: Build FIELD (XOR open_id) =====
  const keystream = [0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,
                     0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30];
  const fieldBytes = Buffer.alloc(oi.length);
  for (let i = 0; i < oi.length; i++) {
    fieldBytes[i] = oi.charCodeAt(i) ^ keystream[i % keystream.length];
  }
  const field = fieldBytes.toString('latin1');

  // ===== STEP 3: Major Register + Login =====
  const pr = proto({
    1: prefix + Math.floor(10000+Math.random()*90000),
    2: at,
    3: oi,
    5: 102000007,
    6: 4,
    7: 1,
    13: 1,
    14: field,
    15: lang,
    16: 1,
    17: 1
  });
  const e = enc(pr.toString('hex'));

  const mh = {
    'User-Agent':'UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)',
    'Accept-Encoding':'deflate, gzip',
    'X-GA-SV':'1789535859',
    'Authorization':'Bearer',
    'X-GA':'v1 1',
    'ReleaseVersion':'OB55',
    'Content-Type':'application/x-www-form-urlencoded',
    'X-Unity-Version':'2018.4.12f1',
    'Host':'loginbp.ppmainecoonghj.com'
  };

  const mr = await s.post('https://loginbp.ppmainecoonghj.com/MajorRegister', e, { headers: mh });
  if (mr.status !== 200) {
    throw new Error('MAJOR_REG_FAIL status=' + mr.status + ' resp=' + String(mr.data).substring(0,100));
  }

  const lr = await s.post('https://loginbp.ppmainecoonghj.com/MajorLogin', e, { headers: mh });

  // ===== STEP 4: Extract JWT =====
  const txt = typeof lr.data === 'string' ? lr.data : JSON.stringify(lr.data);
  const i = txt.indexOf('eyJ');
  if (i === -1) {
    throw new Error('NO_JWT status=' + lr.status + ' resp=' + txt.substring(0,300));
  }

  let tk = txt.substring(i);
  const d2 = tk.indexOf('.', tk.indexOf('.')+1);
  if (d2 !== -1) tk = tk.substring(0, d2+44);

  const p64 = tk.split('.')[1];
  const pad = '='.repeat((4 - (p64.length%4))%4);
  const dj = JSON.parse(Buffer.from(p64+pad,'base64').toString('utf-8'));
  const aid = dj.account_id || dj.external_id;
  if (!aid) throw new Error('NO_ACCOUNT_ID');

  return {
    uid: String(uid), password: pwd, name: prefix,
    account_id: String(aid), jwt_token: tk, region: region.toUpperCase()
  };
}

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();

  try {
    const count = Math.min(parseInt(req.query.count) || 1, 5);
    const namePrefix = req.query.name || 'Yax';
    const region = req.query.region || 'BD';

    const accounts = [];
    const errors = [];

    for (let i = 0; i < count; i++) {
      try {
        accounts.push(await gen(region, namePrefix));
      } catch (e) {
        errors.push(e.message);
      }
    }

    if (!accounts.length) {
      return res.status(200).json({ success:false, accounts:[], errors });
    }

    return res.status(200).json({ success:true, accounts, errors: errors.length?errors:undefined });

  } catch (fatal) {
    return res.status(200).json({ success:false, accounts:[], errors:['FATAL: ' + fatal.message] });
  }
};
