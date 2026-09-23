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

// ===== BUILD MAJOR PAYLOAD (PORTED DARI cv.py) =====
function buildMajorPayload(accessToken, openId, lang, name) {
  // Bagian 1: header device info (statis)
  const part1 = Buffer.from(
    '1a1320252d30382d33302030353a31393a3231220966726565206669726528013a08312e3131342e31334232416e64726f6964204f532039202f204150492d3238202850492f72656c2e636a772e32303232303531382e313134313333294a0848616e6468656c64520a41544d204d6f62696c735a045749464960b60a68ee05720333300',
    'hex'
  );

  // Bagian 2: lang
  const part2 = Buffer.from(lang, 'ascii');

  // Bagian 3: template panjang dengan placeholder access_token & open_id
  // Placeholder: "afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390" = access_token
  //              "1d8ec0240ede109973f3321b9354b44d" = open_id
  const part3Template = Buffer.from(
    'b201203164386563303234306564653130393937336633333231623933353462343464ba010134c2010848616e6468656c64ca01104173757320415355535f493030354441ea014061666366626631333333346265343230333665346637343263383062393536333434626564373630616339316233616666396236303761363130616234333930f00101ca020a41544d204d6f62696c73d2020457494649ca03203734323862323533646566633136343031386336303461316562626665626466e003a88102e803f6e501f003af13f80384078004e7f0018804a881029004e7f0019804a88102c80401d2043d2f646174612f6170702f636f6d2e6474732e667265656669726574682d506465446e4f696c4353466e3337703141485f466c673d3d2f6c69622f61726de00401ea045f32303837663631633139663537663261663465376665666630623234643964397c2f646174612f6170702f636f6d2e6474732e667265656669726574682d506465446e4f696c4353466e3337703141485f466c673d3d2f626173652e61706bf00403f804018a0502329a050a32303139313138363933b205094f70656e474c455332b805ff7fc00504e005f346ea0507616e64726f6964f205704b71734854355a4c5772596c6a4e62355671682f2f7946526c615048534f394e5753517356764f6d646845456e37572b56484e554b2b512b666475413370744e724742304c6c304c527a335757306a4f7765734c6a3661695537735a34307038426655452f46492f6a7a535477526532f805fbe4068806019006019a060134a2060134b206224751400e5e00440655410e504d0d13685a0754060c6d5c560e6a59563b0b5535',
    'hex'
  );

  // Replace placeholder dengan actual values
  let part3Str = part3Template.toString('latin1');
  part3Str = part3Str.replace('afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390', accessToken);
  part3Str = part3Str.replace('1d8ec0240ede109973f3321b9354b44d', openId);
  const part3 = Buffer.from(part3Str, 'latin1');

  return Buffer.concat([part1, part2, part3]);
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

  // ===== STEP 3: Build Payload + Encrypt =====
  const name = prefix + Math.floor(10000+Math.random()*90000);
  const payload = buildMajorPayload(at, oi, lang, name);
  const e = enc(payload.toString('hex'));

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
    throw new Error('MAJOR_REG_FAIL status=' + mr.status + ' resp=' + String(mr.data).substring(0,200));
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
    uid: String(uid), password: pwd, name,
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
