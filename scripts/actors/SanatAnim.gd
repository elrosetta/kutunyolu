class_name SanatAnim
extends RefCounted
## v27 sanatsal animasyonlar (Player'ın görsel katmanı; zamanlamaya, vuruş kutularına, ara belleklere dokunmaz).
## Geri bildirim: "Bütün silahların animasyonlarını sanatsal yapın." Hedef v25 Yıldırım Kılıcı ölçüsü: her adım kasıtlı,
## pozdan poza bir hareket — güçlü hazırlık pozu (gövde toplanır, silah kurulur), dinamik hareket çizgisi, her adımda başka
## eğimde 3B düzlem yayı, takip ve üst üste binen hareket (saç / giysi zaten fizik), leke (smear) kareleri, imza süslemeli
## ayrı bir bitiriş ve silaha özgü ince mürekkep vurguları.
## Katmanlar:
##   1. Savuruş pozu (swing): savuruş anahtarlarının AÇILARI aileye göre yeniden biçimlenir — derin hazırlıkta kol ve
##      bilek vuruş yönünün tersine bir tık daha kurulur ("cock"), temas anahtarında ön kol gerilir, takipte vuruş yönünde
##      aşar ("fol"). Anahtarların ZAMANLARI (hit, ck, multi, hold_k) aynı: süreler ve isabet anları değişmez.
##      Bazı silahlarda tam yeniden çizilmiş anahtarlar (KEYS) ve ters tutuş ("ters": bilek +pi, bıçak ön kol boyunca geriye).
##   2. Düzlem (Player._plane_at): zincirin her adımına küçük eğim farkı (SILAH "pl": [phi farkı°, r çarpanı, roll farkı°]):
##      aynı savuruş art arda gelse de (kargı, tulpar, ikiz bıçak) başka bir yay çizer.
##   3. Gövde (Player._feel): hazırlıkta geri toplanma, vuruşta öne yüklenme; ayaklar yerde kalsın diye üst gövde eğikliği
##      (anim.skew: baş öne / arkaya kayar, ayak sabit) + dönme; vuruşun yönüne göre (aşağı / yukarı / yatay) ezilme-esneme
##      hedefi (aşağı vuruşta hazırlık uzar, temasta ezilir; yukarı vuruşta hazırlık çömelir, temasta uzar).
##   4. Bitiriş süslemesi (fin): son adımın kilidinin ikinci yarısından toparlanmanın sonuna dek kol pozunun üstüne
##      çizilen imza hareket — kılıç: kan silkme + kına koyma "çıt"ı; düellocu: selam; hançer: bıçağı elde çevirip ters
##      tutuş; ağır: omza vurma; dev kılıç: bıçağı yere dikme; mızrak / sırık: çevirip yere dikme; tırpan: omuz ardına
##      asma; kırbaç: ikinci şaklama; pençe: pençeler havada. Ağır saldırı da aynı süslemeyi alır.
##   5. Leke kareleri (smear): süpürmede silahın bir önceki kareyle arasına iki soluk kopyası (yalnızca hızlı dönüşte).
##   6. Mürekkep vurguları (InkAksanFX): takipte uçtan fiske / nokta, bitirişte hat fırçası, ağır çakmada çatlak, pençe
##      izleri, kırbaç yıldızı, kına koyma parıltısı, yay kirişi şaklaması.
##   7. Yay / fırlatma / büyü: geriliş pozu (gövde arkaya yaslanır, yay kolu uzar), bırakışta geri tepme ve takip; fırlatma
##      baş arkasından kurulup bilekten savrulur; büyüde asa göğe kalkar / öne uzanır, kopuz tıngırdatılır.

## Karşılaştırma için kapatılabilir: -- --sanat_kapali (v26 görünümü; kare şeritlerinde önce / sonra)
static var ON: bool = not OS.get_cmdline_user_args().has("--sanat_kapali")

## Aile (Player._tempo_class) gövde ve poz katmanı.
##   lean   [hazırlık, vuruş, oturma] dönme (rad, + ileri)
##   skew   [hazırlık, vuruş, oturma] üst gövde eğikliği (rad, + ileri; ayaklar sabit)
##   sq     ezilme / esneme genliği
##   cock   [kol, bilek] derin hazırlıkta vuruş yönünün tersine ek kurulma (rad)
##   fol    [kol, bilek] takipte vuruş yönünde aşma (rad)
##   ext    temas anahtarında ön kol uzaması çarpanı
##   acc    takip vurgusu (zincir adımlarında): "fiske", "nokta", "yildiz", ""
const AILE := {
	"hancer": {"lean": [-0.057, 0.138, 0.023], "skew": [-0.156, 0.221, 0.039], "sq": 0.07, "cock": [0.338, 0.65], "fol": [0.2, 0.42], "ext": 1.08, "acc": "fiske"},
	"duello": {"lean": [-0.057, 0.127, 0.023], "skew": [-0.143, 0.195, 0.039], "sq": 0.07, "cock": [0.286, 0.52], "fol": [0.16, 0.34], "ext": 1.06, "acc": "fiske"},
	"kilic": {"lean": [-0.069, 0.127, 0.023], "skew": [-0.13, 0.182, 0.026], "sq": 0.08, "cock": [0.286, 0.416], "fol": [0.16, 0.28], "ext": 1.05, "acc": "nokta"},
	"mizrak": {"lean": [-0.081, 0.138, 0.023], "skew": [-0.169, 0.208, 0.026], "sq": 0.08, "cock": [0.156, 0.13], "fol": [0.08, 0.1], "ext": 1.06, "acc": "nokta"},
	"kirbac": {"lean": [-0.092, 0.127, 0.034], "skew": [-0.195, 0.182, 0.039], "sq": 0.07, "cock": [0.39, 0.715], "fol": [0.22, 0.5], "ext": 1.0, "acc": "yildiz"},
	"uzun": {"lean": [-0.092, 0.115, 0.034], "skew": [-0.169, 0.169, 0.039], "sq": 0.08, "cock": [0.286, 0.312], "fol": [0.2, 0.24], "ext": 1.0, "acc": ""},
	"agir": {"lean": [-0.115, 0.172, 0.046], "skew": [-0.195, 0.247, 0.052], "sq": 0.11, "cock": [0.26, 0.286], "fol": [0.14, 0.2], "ext": 1.04, "acc": ""},
	"dev": {"lean": [-0.127, 0.172, 0.057], "skew": [-0.221, 0.26, 0.065], "sq": 0.13, "cock": [0.234, 0.26], "fol": [0.12, 0.18], "ext": 1.03, "acc": ""},
}

## Silaha özgü: fin (bitiriş süslemesi), pl (zincir adımı başına düzlem farkı [phi°, r çarpanı, roll°]), plh (ağır saldırı),
## ters (ters tutuşlu adımlar), imza (bitiriş vurgusu: "firca" hat fırçası, "girdap" hilal fırçası, "nokta"), shape: false
## (anahtarlar elle çizilmiş, aile biçimlemesi uygulanmaz), acc (aile takip vurgusunun yerine)
const SILAH := {
	# --- kılıçlar: iaido gibi temiz kesikler; bitirişte kan silkme + kına koyma
	"alp_kilici": {"fin": "kin", "pl": [[-6.0, 1.0, 0.0], [7.0, 0.88, 14.0], [-4.0, 1.08, 0.0]], "imza": "firca"},
	"yildirim_kilici": {"fin": "kin", "shape": false, "gec": 0.25, "imza": ""},
	"pala": {"fin": "omuz", "pl": [[-8.0, 1.06, 0.0], [10.0, 0.86, -14.0], [0.0, 1.0, 0.0]], "imza": "firca"},
	"ayaz_kilici": {"fin": "kin", "pl": [[8.0, 0.88, 12.0], [-5.0, 1.08, 0.0]], "imza": "firca"},
	"ruh_kilici": {"fin": "cevir_kin", "pl": [[4.0, 0.9, 16.0], [-6.0, 1.06, 0.0], [6.0, 0.92, -12.0]], "imza": "girdap"},
	"yilan_kilici": {"fin": "cevir_kin", "pl": [[-6.0, 1.0, 20.0], [0.0, 1.1, 0.0], [8.0, 0.9, -16.0]], "imza": "firca"},
	# --- düellocular: hızlı, zarif; bitirişte selam
	"yatagan": {"fin": "selam", "pl": [[6.0, 0.94, 18.0], [-8.0, 1.1, 0.0], [5.0, 0.9, -12.0], [0.0, 1.0, 0.0]], "imza": "firca"},
	"ruzgar_kilici": {"fin": "cevir_kin", "pl": [[-4.0, 0.9, 0.0], [8.0, 0.94, -16.0], [-6.0, 1.08, 10.0]], "imza": "girdap"},
	# --- hançerler: çevik fiskeler, ters tutuş; bitirişte bıçağı elde çevirip ters tutuşa al
	"ikiz_bicak": {"fin": "cevir", "pl": [[-8.0, 1.0, 0.0], [10.0, 0.9, -18.0], [4.0, 1.1, 0.0], [0.0, 1.0, 0.0]], "ters": [1], "imza": "nokta"},
	"bori_hanceri": {"fin": "cevir", "pl": [[6.0, 0.92, 0.0], [-10.0, 1.08, 0.0], [0.0, 1.0, 0.0], [0.0, 1.0, 0.0]], "ters": [0, 1], "imza": "nokta"},
	"kurt_pencesi": {"fin": "pence", "pl": [[-10.0, 1.05, 0.0], [8.0, 0.9, 0.0], [0.0, 1.0, 0.0]], "acc": "", "imza": ""},
	"ay_palasi": {"fin": "cevir", "pl": [[0.0, 1.0, 0.0], [12.0, 0.88, -20.0], [-10.0, 1.08, 14.0], [6.0, 0.9, 0.0], [0.0, 1.0, 0.0]], "imza": "girdap"},
	# --- ağırlar: büyük kurulma, yeri sarsan çakma; bitirişte omza vurma
	"gurz": {"fin": "omuz", "pl": [[-4.0, 1.0, 0.0], [6.0, 0.92, 0.0], [0.0, 1.0, 0.0]], "plh": [0.0, 1.0, 0.0]},
	"civili_topuz": {"fin": "omuz", "pl": [[6.0, 0.94, 0.0], [-6.0, 1.06, 0.0], [0.0, 1.0, 0.0]]},
	"savas_baltasi": {"fin": "omuz", "pl": [[-6.0, 1.0, 0.0], [0.0, 1.0, 0.0]]},
	"ikiz_balta": {"fin": "cevir", "pl": [[-6.0, 1.08, 0.0], [8.0, 0.94, 0.0], [0.0, 1.0, 0.0]], "acc": "nokta"},
	"ulu_kilic": {"fin": "dik", "pl": [[-4.0, 1.0, 0.0], [0.0, 1.0, 0.0]], "imza": "firca"},
	"dag_cekici": {"fin": "omuz", "pl": [[-3.0, 1.0, 0.0], [6.0, 0.9, 0.0]]},
	"kor_cekici": {"fin": "omuz", "pl": [[0.0, 1.0, 0.0], [-4.0, 1.04, 0.0]]},
	"bozgun_kilici": {"fin": "dik", "pl": [[-6.0, 1.0, 0.0], [0.0, 1.0, 0.0], [4.0, 1.06, 0.0]], "imza": "firca"},
	# --- uzun saplar: geniş, dans eder gibi süpürmeler; bitirişte sırığı çevirip yere dikme / tırpanı omuz ardına asma
	"teber": {"fin": "sirik", "pl": [[-6.0, 0.9, 0.0], [8.0, 1.1, 0.0], [0.0, 1.0, 0.0]], "imza": "firca"},
	"erlik_tirpani": {"fin": "tirpan", "pl": [[6.0, 0.92, 0.0], [-8.0, 1.1, 0.0], [0.0, 1.0, 0.0]], "imza": "firca"},
	"kayin_asasi": {"fin": "sirik", "pl": [[-8.0, 0.92, 0.0], [0.0, 1.0, 0.0], [6.0, 1.06, 0.0]], "imza": "girdap"},
	# --- mızraklar: zarif saplama → çevirme → süpürme
	"kargi": {"fin": "mizrak", "pl": [[0.0, 1.0, 0.0], [-6.0, 1.1, 18.0], [0.0, 1.0, 0.0]], "imza": "firca"},
	"tulpar_mizragi": {"fin": "mizrak", "pl": [[4.0, 0.95, 0.0], [-8.0, 1.12, 22.0], [0.0, 1.0, 0.0]], "imza": "firca"},
	# --- kırbaçlar: akan S kıvrımları, şaklamalar; bitirişte ikinci şaklama
	"kement": {"fin": "saklama", "pl": [[0.0, 1.0, 0.0], [8.0, 0.9, 0.0]]},
	"od_kamcisi": {"fin": "saklama", "pl": [[-6.0, 1.04, 0.0], [0.0, 1.0, 0.0], [8.0, 0.92, 0.0]]},
}

## Elle çizilmiş anahtarlar (silah → savuruş → anahtarlar; zamanlar özgün savuruşla birebir aynı)
const KEYS := {
	# İkiz Balta: hançer fiskeleri yerine iki elle, baş üstünden ağır doğrama / alttan ters doğrama
	"ikiz_balta": {
		"dual_l": [[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.18, 3.0, 0.6, 0.65, 1.0, 1.0, 2], [0.26, 3.28, 0.72, 0.78, 1.0, 1.0, 0],
			[0.34, 1.0, 0.0, -0.05, 1.0, 1.15, 1], [0.42, 0.32, 0.18, -0.3, 1.0, 1.05, 2], [0.5, 0.38, 0.3, -0.2, 1.0, 1.0, 0],
			[1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]],
		"dual_r": [[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.18, -0.6, -0.5, -0.62, 1.0, 1.0, 2], [0.26, -0.78, -0.55, -0.7, 1.0, 1.0, 0],
			[0.34, 1.7, 0.0, 0.18, 1.0, 1.15, 1], [0.42, 2.75, 0.15, 0.36, 1.0, 1.05, 2], [0.5, 2.6, 0.3, 0.32, 1.0, 1.0, 0],
			[1.0, 0.8, 0.9, 0.4, 1.0, 1.0, 0]]},
}

## Yukarı süpüren savuruşlar (gövde hazırlıkta çömelir, temasta uzar); aşağı / yatay anahtarlardan kendiliğinden bulunur
const SKIP_SHAPE := ["spin", "spin_2h", "helicopter", "twirl", "flurry", "axe"]


## v28: gövde artık gerçek pozlarla çiziliyor (bengu_govde.py: ayak işi, kalça / omuz dönüşü, eğilme). Bu katmanın
## dönme / eğiklik / ezilme-esnemesi aynı hareketi ikinci kez uygulamasın diye v28 gövdesinde bu orana iner (hafif eğilim kalır).
const V28_K := 0.35
const V28_SQ := 0.5


static func _v28(p: Player) -> bool:
	var a: Dictionary = p.anim.meta["anims"].get(p.anim.anim, {})
	return a.get("v28", false)


static func fam(it: Dictionary) -> String:
	return Player._tempo_class(it)


static func _sil(it: Dictionary) -> Dictionary:
	return SILAH.get(String(it.get("id", "")), {})


static func info(it: Dictionary, c: Dictionary, sw: Dictionary, step: int, heavy: bool) -> Dictionary:
	## Savuruş başına görsel bilgi (atk["art"]): aile, bitiriş süslemesi, adım düzlemi, dikey yön
	var s := _sil(it)
	var fin := ""
	var last: bool = c.get("last", false) or heavy
	if last and not c.get("axe", false):
		fin = String(s.get("fin", ""))
	var pl: Array = []
	if heavy:
		pl = s.get("plh", [])
	elif s.has("pl"):
		var pa: Array = s["pl"]
		if not pa.is_empty():
			pl = pa[clampi(step, 0, pa.size() - 1)]
	if not ON:
		fin = ""
		pl = []
	return {"fam": fam(it), "fin": fin, "pl": pl, "dy": _dy(sw), "m": 1.3 if last else 1.0, "last": last}


static func _th(k: Array) -> float:
	return float(k[1]) + float(k[2]) + float(k[3])


static func _idx(sw: Dictionary) -> Array:
	## [derin hazırlık anahtarı, temas anahtarı]
	var keys: Array = sw["keys"]
	var h0 := float(sw["hit"][0])
	var ck := Player._contact_k(sw)
	var iw := -1
	var ic := -1
	for i in range(1, keys.size()):
		var t := float((keys[i] as Array)[0])
		if t <= h0 + 0.001:
			iw = i
		if ic < 0 and t >= ck - 0.001 and t > h0 + 0.001:
			ic = i
	return [iw, ic]


static func _dy(sw: Dictionary) -> float:
	## Vuruşun dikey yönü: bıçak ucunun derin hazırlıktan temasa dikey değişimi (+ aşağı vuruş, - yukarı)
	var ix := _idx(sw)
	if int(ix[0]) < 0 or int(ix[1]) < 0:
		return 0.0
	var keys: Array = sw["keys"]
	return cos(_th(keys[ix[1]])) - cos(_th(keys[ix[0]]))


static func swing(it: Dictionary, c: Dictionary, sw: Dictionary, step: int, heavy: bool) -> Dictionary:
	## Savuruşun görsel kopyası: anahtar açıları aileye göre biçimlenir; zamanlar ve öbür alanlar aynı.
	if not ON:
		return sw
	var id := String(it.get("id", ""))
	var sname := String(c.get("s", ""))
	var s := _sil(it)
	var out := sw.duplicate()
	var kd: Dictionary = KEYS.get(id, {})
	if kd.has(sname):
		out["keys"] = kd[sname]
	var ters: Array = s.get("ters", [])
	var rev := (not heavy) and step in ters and not sname in SKIP_SHAPE
	if s.get("shape", true) and not sname in SKIP_SHAPE and not out.get("around", false) and not kd.has(sname):
		out = _shape(out, AILE.get(fam(it), AILE["kilic"]), c.get("last", false) or heavy)
	if rev:
		# ters tutuş: bıçak ön kol boyunca geriye bakar; vuruşu yumruk taşır, bıçak arkadan biçer
		var nk: Array = []
		var keys: Array = out["keys"]
		for i in keys.size():
			var k2: Array = (keys[i] as Array).duplicate()
			if i > 0 and i < keys.size() - 1:
				k2[3] = float(k2[3]) + PI
			nk.append(k2)
		out["keys"] = nk
	return out


static func _shape(sw: Dictionary, fa: Dictionary, finisher: bool) -> Dictionary:
	var keys: Array = sw["keys"]
	var ix := _idx(sw)
	var iw := int(ix[0])
	var ic := int(ix[1])
	if iw < 1 or ic <= iw or ic + 1 >= keys.size():
		return sw
	var dsg := signf(_th(keys[ic]) - _th(keys[iw]))
	if dsg == 0.0:
		return sw
	var m := 1.3 if finisher else 1.0
	var cock: Array = fa["cock"]
	var fol: Array = fa["fol"]
	var multi: bool = sw.has("multi")
	var nk: Array = []
	for i in keys.size():
		var k2: Array = (keys[i] as Array).duplicate()
		if (i == iw or i == iw - 1) and i >= 1:
			var f := (1.0 if i == iw else 0.65) * m
			k2[1] = float(k2[1]) - dsg * float(cock[0]) * f
			k2[3] = float(k2[3]) - dsg * float(cock[1]) * f
		elif i == ic:
			k2[5] = float(k2[5]) * float(fa["ext"])
		elif not multi and i == ic + 1 and i < keys.size() - 1:
			k2[1] = float(k2[1]) + dsg * float(fol[0]) * m
			k2[3] = float(k2[3]) + dsg * float(fol[1]) * m
		elif not multi and i == ic + 2 and i < keys.size() - 1:
			k2[1] = float(k2[1]) + dsg * float(fol[0]) * m * 0.6
			k2[3] = float(k2[3]) + dsg * float(fol[1]) * m * 0.6
		nk.append(k2)
	var out := sw.duplicate()
	out["keys"] = nk
	return out


# ------------------------------------------------------------------ evre
static func _phase(p: Player) -> Array:
	## [evre, ilerleme 0..1]: wind (hazırlık), strike (süpürme), lock (kilit), rec (toparlanma), charge (şarj)
	var atk: Dictionary = p.atk
	if atk.get("phase", "") == "charge":
		return ["charge", 1.0]
	var sw: Dictionary = atk["sw"]
	var k := float(atk["t"]) / maxf(0.0001, float(atk["dur"]))
	var h0 := float(sw["hit"][0])
	var h1 := float(sw["hit"][1])
	var ck := clampf(Player._contact_k(sw), h0, h1)
	if k < h0:
		return ["wind", k / maxf(0.0001, h0)]
	if k < ck:
		return ["strike", (k - h0) / maxf(0.0001, ck - h0)]
	if k < h1:
		return ["lock", (k - ck) / maxf(0.0001, h1 - ck)]
	return ["rec", (k - h1) / maxf(0.0001, 1.0 - h1)]


static func _eo(u: float) -> float:
	return 1.0 - pow(1.0 - clampf(u, 0.0, 1.0), 3.0)


static func _curve(v: Array, ph: Array, antic: bool) -> float:
	## [hazırlık, vuruş, oturma] değerlerinden evreye göre sürekli eğri
	var u := float(ph[1])
	match String(ph[0]):
		"wind":
			return float(v[0]) * _eo(u) * (1.18 if antic else 1.0)
		"charge":
			return float(v[0]) * 1.3
		"strike":
			return lerpf(float(v[0]), float(v[1]), u * u)
		"lock":
			return lerpf(float(v[1]), float(v[1]) * 0.75, u)
		_:
			return lerpf(float(v[1]) * 0.75, float(v[2]), smoothstep(0.0, 0.5, u)) * (1.0 - smoothstep(0.55, 1.0, u))
	return 0.0


# ------------------------------------------------------------------ gövde (Player._feel)
static func scale_target(p: Player) -> Vector2:
	## Ezilme-esneme yayının hedefi (saldırı dışında 1)
	if not ON:
		return Vector2.ONE
	if p.atk.is_empty() or not p.atk.has("art") or p.roll_t > 0.0 or p.hurt_t > 0.0:
		return _sec_scale(p)
	var ar: Dictionary = p.atk["art"]
	var fa: Dictionary = AILE.get(String(ar["fam"]), AILE["kilic"])
	var a := float(fa["sq"]) * float(ar["m"]) * (V28_SQ if _v28(p) else 1.0)
	var dy := float(ar["dy"])
	var coil := Vector2(1.0 - a * 0.7, 1.0 + a * 0.6)   # yatay: gövde içe toplanır
	var hit := Vector2(1.0 + a, 1.0 - a * 0.6)
	if dy > 0.6:      # aşağı vuruş: hazırlıkta uzan, temasta ezil
		coil = Vector2(1.0 - a * 0.6, 1.0 + a)
		hit = Vector2(1.0 + a * 1.2, 1.0 - a)
	elif dy < -0.6:   # yukarı vuruş: hazırlıkta çömel, temasta uzan
		coil = Vector2(1.0 + a * 0.9, 1.0 - a * 0.8)
		hit = Vector2(1.0 - a * 0.6, 1.0 + a)
	var ph := _phase(p)
	var u := float(ph[1])
	var fin := String(ar.get("fin", ""))
	match String(ph[0]):
		"wind":
			return Vector2.ONE.lerp(coil, _eo(u) * (1.15 if p.atk.has("antic") else 1.0))
		"charge":
			return coil.lerp(Vector2.ONE, -0.25)
		"strike":
			return coil.lerp(hit, u * u)
		"lock":
			return hit.lerp(Vector2.ONE, u * 0.6)
		_:
			var base := hit.lerp(Vector2.ONE, 0.6).lerp(Vector2.ONE, smoothstep(0.0, 0.6, u))
			if fin == "dik" or fin == "mizrak" or fin == "sirik":
				# yere dikme anında hafif çökme
				var b := smoothstep(0.35, 0.5, u) * (1.0 - smoothstep(0.7, 1.0, u))
				base = base.lerp(Vector2(1.06, 0.94), b)
			elif fin == "omuz":
				var b2 := smoothstep(0.4, 0.55, u) * (1.0 - smoothstep(0.65, 0.95, u))
				base = base.lerp(Vector2(1.05, 0.95), b2)
			return base
	return Vector2.ONE


static func _sec_scale(p: Player) -> Vector2:
	## Yay / fırlatma / büyü gövdesi
	if p.aim_t >= 0.0:
		var pull := p.okc.pull()
		return Vector2(1.0 - 0.03 * pull, 1.0 + 0.03 * pull)
	if p.throw_t >= 0.0:
		var tk := clampf(p.throw_t / 0.28, 0.0, 1.0)
		if tk < 0.25:
			return Vector2.ONE.lerp(Vector2(0.93, 1.07), tk / 0.25)
		return Vector2(1.08, 0.93).lerp(Vector2.ONE, smoothstep(0.25, 1.0, tk))
	if p.cast_t > 0.0:
		var u := 1.0 - p.cast_t / 0.35
		return Vector2(0.95, 1.06).lerp(Vector2.ONE, smoothstep(0.1, 0.9, u))
	return Vector2.ONE


static func lean(p: Player, base: float) -> float:
	## Saldırıda dönme hedefi (Player._feel'in v18 evre eğiminin yerine; + baktığı yöne)
	if not ON:
		return base
	var fc := float(p.facing)
	if p.roll_t > 0.0 or p.hurt_t > 0.0:
		return base
	if p.atk.is_empty() or not p.atk.has("art"):
		if p.aim_t >= 0.0:
			return base - fc * 0.05 * p.okc.pull()
		if p.bow_rel_t > 0.0:
			var rk := p.bow_rel_t / Player.BOW_REL
			return base - fc * 0.07 * rk * rk + fc * 0.03 * (1.0 - rk) * rk
		if p.throw_t >= 0.0:
			var tk := clampf(p.throw_t / 0.28, 0.0, 1.0)
			return base + fc * (-0.08 * _eo(tk / 0.25) if tk < 0.25 else lerpf(0.12, 0.0, smoothstep(0.3, 1.0, tk)))
		if p.cast_t > 0.0:
			var u := 1.0 - p.cast_t / 0.35
			return base + fc * 0.07 * (1.0 - smoothstep(0.2, 1.0, u))
		return base
	if p.atk.get("phase", "") == "charge":
		return base
	var ar: Dictionary = p.atk["art"]
	var fa: Dictionary = AILE.get(String(ar["fam"]), AILE["kilic"])
	var v: Array = fa["lean"]
	var m := float(ar["m"]) * (V28_K if _v28(p) else 1.0)
	return fc * _curve([float(v[0]) * m, float(v[1]) * m, float(v[2]) * m], _phase(p), p.atk.has("antic"))


static func skew(p: Player, delta: float) -> void:
	## Üst gövde eğikliği (ayaklar sabit): yaylı, saldırı dışında 0'a döner
	if not ON:
		return
	var st: Dictionary = p._art
	var tgt := 0.0
	var fc := float(p.facing)
	if p.roll_t <= 0.0 and p.hurt_t <= 0.0:
		if not p.atk.is_empty() and p.atk.has("art"):
			var ar: Dictionary = p.atk["art"]
			var fa: Dictionary = AILE.get(String(ar["fam"]), AILE["kilic"])
			var v: Array = fa["skew"]
			var m := float(ar["m"]) * (V28_K if _v28(p) else 1.0)
			var ph := _phase(p)
			if String(ph[0]) == "charge":
				tgt = fc * float(v[0]) * 1.3
			else:
				tgt = fc * _curve([float(v[0]) * m, float(v[1]) * m, float(v[2]) * m], ph, p.atk.has("antic"))
				# bitiriş süslemesinin gövdesi: kına koyarken dik, selamda hafif eğilme, omuza vururken geriye
				var fin := String(ar.get("fin", ""))
				if String(ph[0]) == "rec" and fin != "":
					var u := float(ph[1])
					match fin:
						"selam":
							tgt += fc * 0.05 * sin(PI * clampf(u / 0.5, 0.0, 1.0))
						"omuz":
							tgt -= fc * 0.06 * smoothstep(0.3, 0.6, u) * (1.0 - smoothstep(0.75, 1.0, u))
						"dik", "mizrak", "sirik":
							tgt += fc * 0.05 * smoothstep(0.3, 0.5, u) * (1.0 - smoothstep(0.7, 1.0, u))
		elif p.aim_t >= 0.0:
			tgt = -fc * 0.08 * p.okc.pull()
		elif p.bow_rel_t > 0.0:
			var rk := p.bow_rel_t / Player.BOW_REL
			tgt = -fc * 0.1 * rk * rk
		elif p.throw_t >= 0.0:
			var tk := clampf(p.throw_t / 0.28, 0.0, 1.0)
			tgt = fc * (-0.14 * _eo(tk / 0.25) if tk < 0.25 else lerpf(0.18, 0.0, smoothstep(0.3, 1.0, tk)))
		elif p.cast_t > 0.0:
			var u2 := 1.0 - p.cast_t / 0.35
			tgt = fc * 0.1 * (1.0 - smoothstep(0.25, 1.0, u2))
	if _v28(p) and (p.atk.is_empty() or not p.atk.has("art")):
		tgt *= V28_K   # yay / fırlatma / büyü gövdesi de çizili
	var sv := float(st.get("skv", 0.0))
	var sk := float(st.get("sk", 0.0))
	sv += ((tgt - sk) * 520.0 - sv * 34.0) * delta
	sk = clampf(sk + sv * delta, -0.35, 0.35)
	st["skv"] = sv
	st["sk"] = sk
	p.anim.skew = sk


# ------------------------------------------------------------------ kol pozu (Player._update_weapon_visual)
const REST := [0.6, 0.9, 0.3]
const SHEATH := [0.12, 1.35, -2.72]   # el kalçanın önünde, bıçak kına doğru geriye (hafif aşağı)


static func _lerp3(a: Array, b: Array, u: float) -> Array:
	return [lerpf(float(a[0]), float(b[0]), u), lerpf(float(a[1]), float(b[1]), u), lerpf(float(a[2]), float(b[2]), u)]


static func _wrap_to(w: float, ref: float) -> float:
	return ref + wrapf(w - ref, -PI, PI)


static func pose(p: Player, it: Dictionary, pose_in: Array) -> Array:
	## Bitiriş süslemesi: son adımın kilidinin ikinci yarısından toparlanma sonuna dek kol pozu bu hedef yola karışır.
	if not ON or p.atk.is_empty() or not p.atk.has("art"):
		return pose_in
	var ar: Dictionary = p.atk["art"]
	var fin := String(ar.get("fin", ""))
	if fin == "":
		return pose_in
	var ph := _phase(p)
	var v := -1.0
	var gec := float(_sil(it).get("gec", 0.0))
	if String(ph[0]) == "lock" and float(ph[1]) > 0.55 and gec <= 0.0:
		v = (float(ph[1]) - 0.55) / 0.45 * 0.12        # kilidin sonu: süsleme başlar (0 .. 0,12)
	elif String(ph[0]) == "rec":
		v = lerpf(0.12, 1.0, float(ph[1])) if gec <= 0.0 else clampf((float(ph[1]) - gec) / (1.0 - gec), 0.0, 1.0)
	if v < 0.0:
		return pose_in
	var out := pose_in.duplicate()
	var a1 := float(out[0])
	var a2 := float(out[1])
	var w := float(out[2])
	var base := [a1, a2, w]
	var tgt := base
	var wgt := smoothstep(0.0, 0.22, v)
	var ext := float(out[4])
	match fin:
		"kin":
			# kan silkme (chiburi): kol öne uzanır, bilek bıçağı aşağı silker; sonra el kalçaya, bıçak kına
			var chib := [1.25, 0.15, -1.0]
			if v < 0.38:
				tgt = _lerp3(base, chib, _eo(v / 0.38))
			else:
				tgt = _lerp3(chib, SHEATH, smoothstep(0.38, 0.82, v))
			_kin_click(p, it, v, 0.84)
		"selam":
			# düellocu selamı: bıçak yüzün önünde dik, sonra aşağı-dışa silkilir ve kına
			var sal := [0.95, 2.15, 0.0]
			var flick := [1.35, 0.25, -1.15]
			if v < 0.36:
				tgt = _lerp3(base, sal, _eo(v / 0.36))
			elif v < 0.6:
				tgt = _lerp3(sal, flick, smoothstep(0.36, 0.6, v))
			else:
				tgt = _lerp3(flick, SHEATH, smoothstep(0.6, 0.9, v))
			_kin_click(p, it, v, 0.9)
		"cevir", "cevir_kin":
			# bıçak elde çevrilir (bir buçuk tur), ters tutuşla aşağıda biter; cevir_kin: sonra kına
			var spin_end := 0.72 if fin == "cevir" else 0.58
			var s := _eo(clampf(v / spin_end, 0.0, 1.0))
			var w0 := _wrap_to(w, 0.3)
			var hold := [1.35, 0.55, w0 + (3.0 * PI) * s]
			if fin == "cevir":
				var rev_low := [0.45, 1.45, 3.0 * PI + 0.3]
				tgt = _lerp3(_lerp3(base, hold, smoothstep(0.0, 0.2, v)), rev_low, smoothstep(spin_end * 0.85, 1.0, v))
				if v < spin_end * 0.85:
					tgt[2] = float(hold[2])
			else:
				var sh := [SHEATH[0], SHEATH[1], float(SHEATH[2]) + 4.0 * PI]
				tgt = _lerp3(_lerp3(base, hold, smoothstep(0.0, 0.2, v)), sh, smoothstep(spin_end, 0.9, v))
				if v < spin_end:
					tgt[2] = float(hold[2])
				_kin_click(p, it, v, 0.9)
		"omuz":
			# ağır baş omza vurulur (yükselir, omza oturur; gövde hafif ezilir)
			var lift := [2.4, 0.6, 0.2]
			var sh2 := [1.85, 1.75, 0.35]
			if v < 0.4:
				tgt = _lerp3(base, lift, _eo(v / 0.4))
			else:
				tgt = _lerp3(lift, sh2, smoothstep(0.4, 0.55, v))
			if v >= 0.55 and not p.atk.get("art_omuz", false):
				p.atk["art_omuz"] = true
				p.vis_scale = Vector2(1.06, 0.95)
		"dik":
			# dev kılıç ucu yere dikilir: kabza göğüs önünde, bıçak dimdik aşağı
			var up := [1.6, 0.3, 0.1]
			var plant := [1.05, 0.35, -1.42]
			if v < 0.32:
				tgt = _lerp3(base, up, _eo(v / 0.32))
			else:
				tgt = _lerp3(up, plant, smoothstep(0.32, 0.48, v) * smoothstep(0.32, 0.48, v))
			if v >= 0.48 and not p.atk.get("art_dik", false):
				p.atk["art_dik"] = true
				_plant_fx(p, it)
		"mizrak", "sirik":
			# mızrak / sırık elde bir tur döner (sırık baş üstünde), sonra dibi yere, ucu göğe dikilir
			var hi := [1.25, 0.75, 0.0] if fin == "mizrak" else [2.75, 0.25, 0.0]
			var s2 := _eo(clampf(v / 0.62, 0.0, 1.0))
			var w1 := _wrap_to(w, 0.3)
			var spin := [float(hi[0]), float(hi[1]), w1 + 2.0 * PI * s2]
			var plant2 := [0.72, 0.62, 2.0 * PI + 1.72]
			tgt = _lerp3(_lerp3(base, spin, smoothstep(0.0, 0.18, v)), plant2, smoothstep(0.62, 0.8, v))
			if v < 0.62:
				tgt[2] = float(spin[2])
			if v >= 0.78 and not p.atk.get("art_dik", false):
				p.atk["art_dik"] = true
				_plant_fx(p, it, true)
		"tirpan":
			# tırpan bir tur döner, sonra omuzların ardına asılır (ağzı öne bakar)
			var s3 := _eo(clampf(v / 0.55, 0.0, 1.0))
			var w2 := _wrap_to(w, 0.3)
			var spin2 := [1.5, 0.4, w2 + 2.0 * PI * s3]
			var rest2 := [2.05, 1.5, 2.0 * PI + 0.75]
			tgt = _lerp3(_lerp3(base, spin2, smoothstep(0.0, 0.18, v)), rest2, smoothstep(0.55, 0.78, v))
			if v < 0.55:
				tgt[2] = float(spin2[2])
		"saklama":
			# ikinci şaklama: el geriye-yukarı çekilir, öne silkilir (uçta yıldız), sonra kıvrılarak iner
			var back := [a1 + 1.1, 0.5, -0.6]
			var snap := [1.45, 0.0, -0.55]
			var low := [0.7, 0.9, 0.2]
			if v < 0.28:
				tgt = _lerp3(base, back, _eo(v / 0.28))
			elif v < 0.42:
				tgt = _lerp3(back, snap, pow((v - 0.28) / 0.14, 2.0))
				ext = 1.0 + 0.18 * smoothstep(0.3, 0.42, v)
			else:
				tgt = _lerp3(snap, low, smoothstep(0.45, 1.0, v))
			if v >= 0.42 and not p.atk.get("art_crack", false):
				p.atk["art_crack"] = true
				_whip_star(p, it)
		"pence":
			# pençeler havada: kollar yukarıda açılır (uluma duruşu), sonra iner
			var howl := [2.85, 0.35, 0.25]
			tgt = _lerp3(base, howl, _eo(clampf(v / 0.4, 0.0, 1.0)))
			tgt = _lerp3(tgt, REST, smoothstep(0.7, 1.0, v))
	out[0] = lerpf(a1, float(tgt[0]), wgt)
	out[1] = lerpf(a2, float(tgt[1]), wgt)
	out[2] = lerpf(w, float(tgt[2]), wgt)
	out[4] = lerpf(float(out[4]), ext, wgt)
	return out


static func _kin_click(p: Player, it: Dictionary, v: float, at: float) -> void:
	## Kına koyma "çıt"ı: kabzada parıltı + kısa metal tık
	if v < at or p.atk.get("art_kin", false):
		return
	p.atk["art_kin"] = true
	var hp := p.arm_root.to_global(p._hand_local)
	InkAksanFX.parilti(hp, p.facing, p.weapon_color(it))
	if Ses.has("kin_kapa"):
		Ses.play("kin_kapa", -6.0, 1.0, 0.05, 0.05, hp)
	p.vis_scale = Vector2(0.97, 1.03)


static func _plant_fx(p: Player, it: Dictionary, butt := false) -> void:
	## Yere dikme: dipte / uçta toz + fırça noktası, küçük sarsıntı yok (yalnızca görsel)
	var R := p._reach(it)
	var tip := p.arm_root.to_global(p._hand_local + p._blade_local * (R if not butt else -R * 0.35))
	var gy := p.global_position.y
	var gp := Vector2(tip.x, gy)
	InkDust.drag(gp, -p.facing)
	InkAksanFX.nokta(gp + Vector2(0, -1), Vector2(p.facing, -0.15), p.weapon_color(it), 1, 1.0)
	Ses.play("inis", -14.0, 1.25, 0.05, 0.05, gp)


static func _whip_star(p: Player, it: Dictionary) -> void:
	var tip := p.arm_root.to_global(p._hand_local + p._blade_local * p._reach(it))
	InkAksanFX.yildiz(tip, Vector2(p.facing, 0.0), p.weapon_color(it), 1.0)
	if Ses.has("darbe_kirbac"):
		Ses.play("darbe_kirbac", -12.0, 1.25, 0.06, 0.05, tip)


# ------------------------------------------------------------------ leke kareleri ve uç yolu (_update_weapon_visual sonu)
static func smear(p: Player, it: Dictionary) -> void:
	if not ON:
		return
	var st: Dictionary = p._art
	if not st.has("gh"):
		var gs: Array = []
		for i in 2:
			var g := Sprite2D.new()
			g.texture = p.weapon.texture
			g.region_enabled = true
			g.centered = false
			g.material = p.weapon.material
			g.visible = false
			p.arm_root.add_child(g)
			p.arm_root.move_child(g, p.weapon.get_index())
			gs.append(g)
		st["gh"] = gs
	var gh: Array = st["gh"]
	var wv: Sprite2D = p.weapon
	if p.throw_t >= 0.0 and p.thrown and p.atk.is_empty():
		wv.visible = false   # fırlatılan silah elden çıktı: takip boş elle (eski: aynı mızrak elde de kalıyordu)
	var cur := [wv.position, wv.rotation, wv.scale]
	var prev: Array = st.get("prev", [])
	st["prev"] = cur
	var active: bool = not p.atk.is_empty() and wv.visible and it.get("kind", "") != "bow"
	var fast := false
	if active and prev.size() == 3:
		var da := absf(wrapf(float(cur[1]) - float(prev[1]), -PI, PI))
		var ph := String(_phase(p)[0]) if p.atk.has("art") else String(p.atk.get("phase", ""))
		fast = da > 0.24 and da < 2.6 and (ph == "strike" or ph == "lock" or ph == "rec")
		# uç yolu (bitiriş hat fırçası için): süpürme ve kilit boyunca
		if ph == "strike" or ph == "lock":
			var tip := p.arm_root.to_global(p._hand_local + p._blade_local * p._reach(it))
			var path: PackedVector2Array = p.atk.get("art_tip", PackedVector2Array())
			if path.is_empty() or path[path.size() - 1].distance_to(tip) > 1.5:
				path.append(tip)
				p.atk["art_tip"] = path
	for i in gh.size():
		var g: Sprite2D = gh[i]
		if not fast:
			g.visible = false
			continue
		var q := 1.0 - float(i + 1) / 3.0
		g.visible = true
		g.texture = wv.texture
		g.region_rect = wv.region_rect
		g.offset = wv.offset
		g.flip_h = wv.flip_h
		g.flip_v = wv.flip_v
		g.z_index = wv.z_index
		g.position = (prev[0] as Vector2).lerp(cur[0], q)
		g.rotation = lerp_angle(float(prev[1]), float(cur[1]), q)
		g.scale = (prev[2] as Vector2).lerp(cur[2], q)
		g.modulate = Color(0.82, 0.86, 0.95, 0.34 if i == 0 else 0.16)


# ------------------------------------------------------------------ vurgular
static func takip(p: Player, it: Dictionary, c: Dictionary) -> void:
	## Süpürme + kilit bitince (vuruş penceresinden çıkış): takip vurgusu; bitirişte hat fırçası
	if not ON or not p.atk.has("art"):
		return
	var ar: Dictionary = p.atk["art"]
	var s := _sil(it)
	var fa: Dictionary = AILE.get(String(ar["fam"]), AILE["kilic"])
	var acc := String(s.get("acc", fa.get("acc", "")))
	var col := p.weapon_color(it)
	var path: PackedVector2Array = p.atk.get("art_tip", PackedVector2Array())
	var tip := p.arm_root.to_global(p._hand_local + p._blade_local * p._reach(it))
	var dir := Vector2(p.facing, 0.0)
	if path.size() >= 2:
		dir = (path[path.size() - 1] - path[maxi(0, path.size() - 3)])
	if ar.get("last", false):
		var imza := String(s.get("imza", "firca"))
		match imza:
			"firca":
				if path.size() >= 5:
					var n := path.size()
					var seg := path.slice(int(n * 0.35), n)
					var ctr := p.center()
					var mid := seg[int(seg.size() / 2.0)]
					var out := (mid - ctr).normalized() * 5.0
					InkAksanFX.firca(seg, col, 2.6 + 1.2 * p._weight(it), out)
			"girdap":
				InkAksanFX.girdap(tip, p.facing, col, 12.0 + 6.0 * p._weight(it))
			"nokta":
				InkAksanFX.nokta(tip, dir, col, 3, 1.1)
		if String(c.get("s", "")) in ["whip_crack", "whip_side"]:
			InkAksanFX.yildiz(tip, dir, col, 1.2)
		return
	match acc:
		"fiske":
			InkAksanFX.fiske(tip, dir, col, 2, 0.9)
		"nokta":
			InkAksanFX.nokta(tip, dir, col, 1, 0.9)
		"yildiz":
			if String(c.get("s", "")) in ["whip_crack", "whip_side"]:
				InkAksanFX.yildiz(tip, dir, col, 0.9)


static func catlak(p: Player, it: Dictionary, gp: Vector2, power: float, lite: bool) -> void:
	## Ağır çakma: yerde dallanan mürekkep çatlakları (hafif değmede yok)
	if not ON or lite:
		return
	InkAksanFX.catlak(gp, p.facing, p.weapon_color(it), clampf(power, 0.6, 1.6))
	if not p.atk.is_empty() and p.atk.get("art", {}).get("last", false):
		p.vis_scale = Vector2(1.2, 0.82)   # bitiriş çakması: gövde yere çöker (ağırlık)


static func vurus(p: Player, it: Dictionary, hp: Vector2, hdir: Vector2) -> void:
	## İsabet vurgusu: Kurt Pençeleri'nde üç paralel tırmık
	if not ON:
		return
	if String(it.get("id", "")) == "kurt_pencesi":
		var d := hdir if hdir.length() > 0.01 else Vector2(p.facing, 0)
		var path: PackedVector2Array = p.atk.get("art_tip", PackedVector2Array()) if not p.atk.is_empty() else PackedVector2Array()
		if path.size() >= 2:
			d = (path[path.size() - 1] - path[0]).normalized()
		InkAksanFX.pence(hp, d, p.weapon_color(it), 1.0)


static func kiris(p: Player, it: Dictionary) -> void:
	## Yay bırakışı: gezde kiriş şaklaması
	if not ON or not p._bow_nock_ok:
		return
	InkAksanFX.kiris(p.arm_root.to_global(p._bow_nock), p.facing, p.weapon_color(it))


# ------------------------------------------------------------------ yay, fırlatma, büyü pozları
static func bow_pose(p: Player, pose_in: Array, pull: float, rk: float) -> Array:
	## Geriliş: yay kolu gerildikçe tam uzanır, tam gerilmede omuz hafif kalkar; bırakışta kol öne-yukarı seker ve
	## sönümlü olarak iner (takip)
	if not ON:
		return pose_in
	var out := pose_in.duplicate()
	if pull > 0.0:
		out[4] = float(out[4]) + 0.08 * pull
		out[0] = float(out[0]) + 0.03 * pull
	if rk > 0.0:
		out[0] = float(out[0]) + 0.1 * rk * rk
		out[4] = float(out[4]) + 0.05 * rk
	return out


const THROW_KEYS := [
	# [t, a1, a2, w, k, ext, ease]: baş arkasına kurulur (gövde toplanır), 0,25'te bilekten savrulur (fırlatma anı
	# Player'da tk 0,25), takipte kol gövdenin önünden aşağı iner
	[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.16, 2.9, 1.25, 0.95, 1.0, 1.0, 2], [0.25, 3.35, 1.05, 1.2, 1.0, 1.0, 0],
	[0.33, 1.35, 0.0, -0.25, 1.0, 1.18, 1], [0.5, 0.6, 0.35, -0.6, 1.0, 1.05, 2], [1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]


static func throw_pose(p: Player, it: Dictionary, tk: float) -> Array:
	if not ON:
		return p._swing_pose(Player.SWINGS["axe"], tk)
	return p._swing_pose({"keys": THROW_KEYS}, tk)


static func cast_pose(p: Player, it: Dictionary, cast_t: float) -> Array:
	## Büyü (asa / kopuz / boru): büyü çıktığı anda bırakış pozu; sonra imza hareket ve dinlenme
	var u := clampf(1.0 - cast_t / 0.35, 0.0, 1.0)
	if not ON:
		return [1.45, 0.1, -0.5, 1.0, 1.0]
	match String(it.get("id", "")):
		"gok_asasi":
			# asa göğe kalkar (yıldırım gökten iner), sonra öne iner
			var up := [3.05, 0.1, -0.1]
			var fwd := [1.5, 0.15, -0.3]
			var q := _lerp3(fwd, up, _eo(u / 0.22)) if u < 0.22 else _lerp3(up, fwd, smoothstep(0.55, 1.0, u))
			return [q[0], q[1], q[2], 1.0, 1.0 + 0.06 * (1.0 - smoothstep(0.0, 0.5, u))]
		"kam_kopuzu":
			# kopuz göğüs önünde, bilek tıngırdatır
			var strum := 0.28 * sin(u * PI * 6.0) * (1.0 - u)
			return [1.05, 1.25, -0.6 + strum, 1.0, 1.0]
		"yel_borusu":
			# boru ağza götürülür, sonra öne uzatılır
			var mouth := [1.25, 2.1, -1.0]
			var fwd2 := [1.55, 0.1, -0.2]
			var q2 := _lerp3(mouth, fwd2, smoothstep(0.15, 0.45, u))
			return [q2[0], q2[1], q2[2], 1.0, 1.0]
	var fwd3 := [1.45, 0.1, -0.5]
	var lift := [2.3, 0.3, -0.2]
	var q3 := _lerp3(lift, fwd3, _eo(u / 0.2)) if u < 0.2 else fwd3
	return [q3[0], q3[1], q3[2], 1.0, 1.0 + 0.08 * (1.0 - smoothstep(0.0, 0.4, u))]
