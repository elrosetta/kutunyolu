class_name Sinema
extends CanvasLayer
## v43 sinematik motoru: veri güdümlü çekim listesi (data/sinema/<ad>.json) oynatır. Açılış, son, boss kartları, örgü
## sahnesi ve bölüm açılışları aynı motoru kullanır (biçim: docs/TASARIM.md "v43: sinematik motoru").
##
##  * Çekim = katmanlar (assets/sinema/*.webp, tools/artgen/sinema43.py; ya da herhangi bir res:// doku) + canlı öğeler
##    (SinemaEfekt.gd) + kamera anahtarları + yazı + ses. Her katman bir derinlik (d) düzleminde durur: kamera kayınca
##    / yaklaşınca uzak düzlem az, yakın düzlem çok kayar (paralaks); odak anahtarları odak dışındaki düzlemi bulanıklaştırır
##    (odak çekimi); katmanlar rüzgârda salınabilir, mürekkeple belirebilir, anahtarlarla oynatılabilir (oyuncular).
##  * Çekimler iki SubViewport'a dönüşümlü çizilir; birleştirici (shaders/sinema_ekran.gdshader) aralarında mürekkep
##    yıkaması / fırça silmesi / kâğıt yırtığı / karart / ak ışık / kesme geçişi yapar, kâğıt tanesi + sinema bantları ekler.
##  * Müzik ayrı oynatıcıda (döngüsüz; çekim süreleri müziğin vuruşlarına göre yazılmıştır — tools/audiogen/v43_sinema.py
##    aynı JSON'dan vuruşları okur), sesler çekim zamanına bağlı.
##  * Geçmek için basılı tut (Esc / Boşluk / Enter / saldırı / tık): fırça çemberi dolar. Oyun ağacı duraklıyken oynar.
##  * degisken: JSON'daki "{ad}" yer tutucularına değer (boss kartı: ad / söz / örgü rengi; bölüm açılışı: biyom).
## Bitince "bitti" sinyali, düğüm kendini siler.

signal bitti

const TUVAL := Vector2(2560.0, 1440.0)
const BONE := Color(0.95, 0.9, 0.8)
const ALTIN := Color(1.0, 0.84, 0.52)
const GEC_SURE := 1.1          # basılı tutma süresi (sn)
const YAZI_HIZ := 26.0         # anlatı yazısı: sn başına harf
const GECIS_TUR := {"kesme": 0, "murekkep": 1, "firca": 2, "yirtik": 3, "karart": 4, "beyaz": 5}

static var etkin: Sinema = null
static var oyun_ici_zorla := false   # test: test kiplerinde de bölüm açılışı oynasın (hikaye_testi)
static var _meta: Dictionary = {}

var ad := ""
var veri: Dictionary = {}
var degisken: Dictionary = {}
var cekimler: Array = []
var ci := -1                   # şimdiki çekim
var t := 0.0                   # çekim içi zaman
var gt := 0.0                  # genel zaman
var saydam := false
var kayit := false             # film kaydı (--write-movie): sabit adım, sesle eş
var _vp: Array = []
var _slot := 0
var _cur: Dictionary = {}
var _prev: Dictionary = {}
var _gk := 1.0                 # geçiş ilerlemesi
var _gsure := 1.0
var _gtur := 1
var _ekran: ColorRect
var _emat: ShaderMaterial
var _yazi: Control
var _muzik: AudioStreamPlayer
var _ses_i := 0
var _basili := 0.0
var _serbest := false          # açılıştaki basılı tuş bir kez bırakılmadan geçme sayılmaz
var _ipucu_t := 0.0
var _kapanis := -1.0
var _jenerik := false
var _jt := 0.0
var _bitti := false
var _solma := 0.0
var _bant: TextureRect = null


static func oynat(parent: Node, k: String, degiskenler := {}) -> Sinema:
	## k: data/sinema/<k>.json. Dönen düğümün "bitti" sinyaline bağlanılır.
	var s := Sinema.new()
	s.ad = k
	s.degisken = degiskenler
	parent.add_child(s)
	return s


static func buyuk(s: String) -> String:
	## Türkçe büyük harf (i → İ, ı → I)
	return s.replace("i", "İ").replace("ı", "I").to_upper()


static func ornek_degisken(k: String) -> Dictionary:
	## Kayıt / test için yer tutucu örnekleri (oyunda çağıran doldurur)
	match k:
		"boss_kart":
			return boss_degisken("kara_boru_han")
		"orgu_sahne":
			return orgu_degisken("kara_boru_han", [])
		"bolum_acilis":
			return bolum_degisken("otuken")
	return {}


static func boss_degisken(bid: String) -> Dictionary:
	var o := Hikaye.orgu(bid)
	var c := Hikaye.orgu_renk(bid)
	return {"ad": Hikaye.boss_ad(bid), "unvan": ("%s BEKÇİSİ" % buyuk(String(o.get("ad", "")))) if not o.is_empty() else "",
		"soz": Hikaye.boss_soz(bid, "once"), "renk": [c.r, c.g, c.b]}


static func orgu_degisken(bid: String, dolu: Array) -> Dictionary:
	var o := Hikaye.orgu(bid)
	var c := Hikaye.orgu_renk(bid)
	var d: Array = []
	for b in dolu:
		d.append(Hikaye.ORGU_SIRA.find(b))
	return {"orgu": String(o.get("ad", "")), "gorum": String(o.get("gorum", "")), "renk": [c.r, c.g, c.b], "sira": Hikaye.ORGU_SIRA.find(bid), "dolu": d}


static func bolum_degisken(biyom: String) -> Dictionary:
	var c := Hikaye.bolum(biyom)
	return {"biyom": biyom, "no": buyuk(String(c.get("no", ""))), "bolum": String(c.get("ad", "")), "epigraf": String(c.get("epigraf", "")),
		"gorum": Hikaye.gorum_satiri(biyom)}


static func var_mi(k: String) -> bool:
	return FileAccess.file_exists("res://data/sinema/%s.json" % k)


func _ready() -> void:
	layer = 40
	process_mode = Node.PROCESS_MODE_ALWAYS
	etkin = self
	if _meta.is_empty() and FileAccess.file_exists("res://assets/sinema/katmanlar.json"):
		_meta = Data.load_json("res://assets/sinema/katmanlar.json")
	veri = _yerlestir_degisken(Data.load_json("res://data/sinema/%s.json" % ad)) if var_mi(ad) else {}
	cekimler = veri.get("cekimler", [])
	saydam = bool(veri.get("saydam", false))
	kayit = OS.get_cmdline_args().has("--write-movie")
	var px := _px()
	for i in 2:
		var sv := SubViewport.new()
		sv.size = px
		sv.transparent_bg = saydam
		sv.world_2d = World2D.new()   # kendi dünyası: oyunun tuvali çekim dokusuna karışmasın
		sv.disable_3d = true
		sv.use_hdr_2d = false   # çekimler sRGB'de çizilir; ana görüntü HDR ise birleştirici doğrusala çevirir
		sv.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_LINEAR
		sv.render_target_update_mode = SubViewport.UPDATE_DISABLED
		add_child(sv)
		_vp.append(sv)
	# saydam kartın mürekkep bandı: birleştiricinin altında ekran boyu (oyun ardında görünür)
	if veri.has("bant_doku"):
		_bant = TextureRect.new()
		_bant.texture = _doku(String(veri["bant_doku"]))
		_bant.set_anchors_preset(Control.PRESET_FULL_RECT)
		_bant.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		_bant.stretch_mode = TextureRect.STRETCH_SCALE
		_bant.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_bant.modulate.a = 0.0
		add_child(_bant)
	_ekran = ColorRect.new()
	_ekran.set_anchors_preset(Control.PRESET_FULL_RECT)
	_ekran.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_emat = ShaderMaterial.new()
	_emat.shader = load("res://shaders/sinema_ekran.gdshader")
	_emat.set_shader_parameter("saydam", saydam)
	_emat.set_shader_parameter("tex_a", _vp[1].get_texture())
	_emat.set_shader_parameter("tex_b", _vp[0].get_texture())
	_emat.set_shader_parameter("aspect", float(px.x) / float(px.y))
	_emat.set_shader_parameter("solma", 0.0)
	_emat.set_shader_parameter("dogrusal", false)
	_ekran.material = _emat
	add_child(_ekran)
	_yazi = Control.new()
	_yazi.set_anchors_preset(Control.PRESET_FULL_RECT)
	_yazi.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_yazi.draw.connect(_ciz)
	add_child(_yazi)
	_muzik = AudioStreamPlayer.new()
	_muzik.bus = "Music" if AudioServer.get_bus_index("Music") >= 0 else "Master"
	add_child(_muzik)
	var mz: Dictionary = veri.get("muzik", {})
	if not mz.is_empty():
		var path := "res://assets/audio/music/%s.wav" % String(mz.get("ad", ""))
		if ResourceLoader.exists(path):
			var st: AudioStream = load(path)
			if st is AudioStreamWAV:
				(st as AudioStreamWAV).loop_mode = AudioStreamWAV.LOOP_DISABLED
			_muzik.stream = st
			_muzik.volume_db = float(mz.get("db", 0.0))
			if bool(mz.get("sustur", true)):
				Ses.music_stop(0.6)
			_muzik.play()
	if cekimler.is_empty():
		_bitir()
		return
	_baslat_cekim(0, 0.0)


func _px() -> Vector2i:
	var w := get_window()
	var s := w.size if w != null else Vector2i(1280, 720)
	return Vector2i(maxi(s.x, 320), maxi(s.y, 180))


func _exit_tree() -> void:
	if etkin == self:
		etkin = null


# ------------------------------------------------------------------ veri
func _yerlestir_degisken(v: Variant) -> Variant:
	## "{ad}" tam eşleşirse değerin kendisi (renk dizisi, sayı), metin içindeyse yazıya dönüştürülür
	if v is Dictionary:
		var o := {}
		for k in v:
			o[k] = _yerlestir_degisken(v[k])
		return o
	if v is Array:
		var a := []
		for x in v:
			a.append(_yerlestir_degisken(x))
		return a
	if v is String:
		var s: String = v
		if s.begins_with("{") and s.ends_with("}") and degisken.has(s.substr(1, s.length() - 2)):
			return degisken[s.substr(1, s.length() - 2)]
		if s.contains("{"):
			for k in degisken:
				s = s.replace("{%s}" % k, str(degisken[k]))
		return s
	return v


func cekim_sure(i: int) -> float:
	return float(cekimler[i].get("sure", 6.0)) if i >= 0 and i < cekimler.size() else 0.0


func toplam_sure() -> float:
	var s := 0.0
	for i in cekimler.size():
		s += cekim_sure(i)
	return s


func cekim_basi(i: int) -> float:
	var s := 0.0
	for k in mini(i, cekimler.size()):
		s += cekim_sure(k)
	return s


# ------------------------------------------------------------------ çekim kurma
func _doku(ad_: String) -> Texture2D:
	var p := ad_ if ad_.begins_with("res://") else "res://assets/sinema/%s.webp" % ad_
	return load(p) if ResourceLoader.exists(p) else null


func _kur(i: int, slot: int) -> Dictionary:
	var c: Dictionary = cekimler[i]
	var sv: SubViewport = _vp[slot]
	for ch in sv.get_children():
		ch.queue_free()
	var kok := Node2D.new()
	sv.add_child(kok)
	var arka := ColorRect.new()
	var ar: Array = c.get("zemin", [0.02, 0.018, 0.025, 0.0 if saydam else 1.0])
	arka.color = Color(float(ar[0]), float(ar[1]), float(ar[2]), float(ar[3]) if ar.size() > 3 else 1.0)
	arka.size = Vector2(sv.size)
	kok.add_child(arka)
	var oge: Array = []
	var sira := 0
	for k in c.get("katmanlar", []):
		var o := _katman_kur(k, kok, sira)
		sira += 1
		if not o.is_empty():
			oge.append(o)
	for e in c.get("efektler", []):
		var dz := Node2D.new()
		dz.z_index = int(e.get("z", 50))
		kok.add_child(dz)
		var ef := SinemaEfekt.new()
		ef.kur(e)
		dz.add_child(ef)
		oge.append({"tur": "efekt", "duzlem": dz, "d": float(e.get("d", 1.0)), "efekt": ef, "veri": e})
	sv.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	return {"i": i, "kok": kok, "oge": oge, "veri": c, "slot": slot}


func _katman_kur(k: Dictionary, kok: Node2D, sira: int) -> Dictionary:
	var ad_ := String(k.get("resim", ""))
	var tex := _doku(ad_)
	if tex == null:
		if not bool(k.get("istege_bagli", false)):
			push_warning("Sinema: katman yok: " + ad_)
		return {}
	var m: Dictionary = _meta.get(ad_, {})
	var ofs := Vector2(float(m.get("ofs", [0, 0])[0]), float(m.get("ofs", [0, 0])[1]))
	if k.has("ofs"):
		ofs = Vector2(float(k["ofs"][0]), float(k["ofs"][1]))
	var olcek := float(k.get("olcek", 1.0))
	var tsz := Vector2(tex.get_size()) * olcek
	match String(k.get("hiza", "")):
		"alt":
			ofs.y = TUVAL.y - tsz.y
		"ust":
			ofs.y = 0.0
		"orta":
			ofs = (TUVAL - tsz) * 0.5
	var pv: Variant = k.get("pivot", m.get("pivot", null))
	var piv := ofs + tsz * 0.5 if pv == null else Vector2(float(pv[0]), float(pv[1]))
	var dz := Node2D.new()
	dz.z_index = int(k.get("z", sira))
	kok.add_child(dz)
	var pn := Node2D.new()
	pn.position = piv
	dz.add_child(pn)
	var sp := Sprite2D.new()
	sp.texture = tex
	sp.centered = false
	sp.position = ofs - piv
	sp.scale = Vector2(olcek, olcek)
	sp.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	var mat := ShaderMaterial.new()
	mat.shader = load("res://shaders/sinema_katman.gdshader")
	mat.set_shader_parameter("seed", float(sira) * 0.37 + float(ad_.hash() % 97) * 0.01)
	mat.set_shader_parameter("sway", float(k.get("salinim", 0.0)))
	mat.set_shader_parameter("sway_freq", float(k.get("salinim_hiz", 0.7)))
	mat.set_shader_parameter("reveal_mode", int(k.get("kip", 0)))
	mat.set_shader_parameter("radial_a0", float(k.get("enso_a0", -2.4)))
	if k.has("renk"):
		var rc: Array = k["renk"]
		mat.set_shader_parameter("tint", Color(float(rc[0]), float(rc[1]), float(rc[2]), float(rc[3]) if rc.size() > 3 else 1.0))
	sp.material = mat
	pn.add_child(sp)
	var gl: Sprite2D = null
	if bool(m.get("isik", false)) and bool(k.get("isik", true)):
		var gt_ := _doku(ad_ + "_isik")
		if gt_ != null:
			gl = Sprite2D.new()
			gl.texture = gt_
			gl.centered = false
			gl.position = -piv
			gl.scale = TUVAL / Vector2(gt_.get_size())
			gl.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
			var gm := ShaderMaterial.new()
			gm.shader = load("res://shaders/sinema_isik.gdshader")
			gm.set_shader_parameter("seed", mat.get_shader_parameter("seed"))
			gm.set_shader_parameter("sway", float(k.get("salinim", 0.0)) * 0.5)
			gm.set_shader_parameter("sway_freq", float(k.get("salinim_hiz", 0.7)))
			gl.material = gm
			pn.add_child(gl)
	return {"tur": "katman", "duzlem": dz, "pivot": pn, "piv": piv, "sprite": sp, "isik": gl, "d": float(k.get("d", 1.0)), "veri": k, "olcek": olcek}


# ------------------------------------------------------------------ zaman çizelgesi
func _baslat_cekim(i: int, tloc: float, gecis := true) -> void:
	if not _prev.is_empty():
		_birak(_prev)
		_prev = {}
	if gecis and not _cur.is_empty():
		_prev = _cur
	elif not _cur.is_empty():
		_birak(_cur)
	ci = i
	t = tloc
	_slot = 1 - _slot if not _prev.is_empty() else _slot
	_cur = _kur(i, _slot)
	var g: Dictionary = cekimler[i].get("gecis", {})
	_gtur = int(GECIS_TUR.get(String(g.get("tur", "murekkep")), 1))
	_gsure = maxf(0.01, float(g.get("sure", 1.2)))
	_gk = 0.0 if not _prev.is_empty() else 1.0
	_emat.set_shader_parameter("tex_b", _vp[_slot].get_texture())
	_emat.set_shader_parameter("tex_a", _vp[1 - _slot].get_texture())
	_emat.set_shader_parameter("tur", _gtur)
	_emat.set_shader_parameter("seed", float(i) * 0.73)
	_emat.set_shader_parameter("bant", float(cekimler[i].get("bant", veri.get("bant", 0.0))))
	_emat.set_shader_parameter("vign", float(cekimler[i].get("kenar", veri.get("kenar", 0.35))))
	_emat.set_shader_parameter("grain", float(veri.get("tane", 0.045)))
	_ses_i = 0
	var sl: Array = cekimler[i].get("ses", [])
	while _ses_i < sl.size() and float(sl[_ses_i][0]) < t - 0.05:
		_ses_i += 1
	_guncelle(_cur, t)


func _birak(c: Dictionary) -> void:
	var sv: SubViewport = _vp[int(c["slot"])]
	sv.render_target_update_mode = SubViewport.UPDATE_DISABLED
	if is_instance_valid(c.get("kok")):
		(c["kok"] as Node).queue_free()


func git(hedef: float) -> void:
	## Genel zamanda bir ana atla (test, kayıt): o anın çekimi geçişsiz kurulur; müzik de oraya sarar
	hedef = clampf(hedef, 0.0, toplam_sure() - 0.01)
	var i := 0
	while i < cekimler.size() - 1 and cekim_basi(i + 1) <= hedef:
		i += 1
	gt = hedef
	_baslat_cekim(i, hedef - cekim_basi(i), false)
	_gk = 1.0
	if _muzik.stream != null:
		_muzik.play(hedef)


func _process(delta: float) -> void:
	_girdi(delta)
	if _kapanis >= 0.0:
		_kapanis += delta
		var k := clampf(1.0 - _kapanis / 0.7, 0.0, 1.0)
		_emat.set_shader_parameter("solma", k * _solma)
		_yazi.modulate.a = k
		if _bant != null:
			_bant.modulate.a = minf(_bant.modulate.a, k)
		_muzik.volume_db = float(veri.get("muzik", {}).get("db", 0.0)) - (1.0 - k) * 40.0
		if _kapanis >= 0.8 and not _bitti:
			_bitti = true
			bitti.emit()
			queue_free()
		return
	_solma = minf(1.0, _solma + delta / float(veri.get("acilis", 0.8)))
	if _bant != null:
		_bant.modulate.a = minf(_solma, clampf((toplam_sure() - gt) / 0.5, 0.0, 1.0)) * float(veri.get("bant_a", 0.9))
	_emat.set_shader_parameter("solma", _solma)
	if _jenerik:
		_jt += delta
		t += delta
		_guncelle(_cur, t)
		var n_j: int = (Data.story.get("jenerik", []) as Array).size()
		if _jt > 3.0 + n_j * 2.6 + 3.0:
			_bitir()
		_yazi.queue_redraw()
		return
	gt += delta
	# müzik saatiyle uzlaş (oyun takılırsa görüntü müziği kovalar)
	if not kayit and _muzik.playing and _muzik.stream != null:
		var mp := _muzik.get_playback_position() + AudioServer.get_time_since_last_mix()
		if absf(mp - gt) > 0.12:
			gt = lerpf(gt, mp, 0.5)
	t = gt - cekim_basi(ci)
	if t >= cekim_sure(ci):
		if ci + 1 < cekimler.size():
			_baslat_cekim(ci + 1, t - cekim_sure(ci))
		elif bool(veri.get("jenerik", false)):
			_jenerik = true
			_jt = 0.0
		else:
			_bitir()
			return
	if _gk < 1.0:
		_gk = minf(1.0, _gk + delta / _gsure)
		_emat.set_shader_parameter("k", _gk * _gk * (3.0 - 2.0 * _gk) if _gtur != 0 else _gk)
		if not _prev.is_empty():
			_guncelle(_prev, t + cekim_sure(int(_prev["i"])))
		if _gk >= 1.0 and not _prev.is_empty():
			_birak(_prev)
			_prev = {}
	else:
		_emat.set_shader_parameter("k", 1.0)
	_guncelle(_cur, t)
	_sesler()
	_yazi.queue_redraw()


func _sesler() -> void:
	var sl: Array = cekimler[ci].get("ses", [])
	while _ses_i < sl.size() and float(sl[_ses_i][0]) <= t:
		var e: Array = sl[_ses_i]
		_ses_i += 1
		if Ses.has(String(e[1])):
			Ses.play(String(e[1]), float(e[2]) if e.size() > 2 else 0.0, float(e[3]) if e.size() > 3 else 1.0, 0.0, 0.0)


# ------------------------------------------------------------------ anahtar değerleri
static func _ease(f: float, e: String) -> float:
	match e:
		"lin":
			return f
		"i":
			return f * f * f
		"o":
			return 1.0 - pow(1.0 - f, 3.0)
	return f * f * (3.0 - 2.0 * f)


static func anahtar(keys: Array, tt: float, idx: int, def: float, egri := "io") -> float:
	## [[t, v1, v2, ...], ...] anahtarlarında idx. değer (yumuşak geçiş)
	if keys.is_empty():
		return def
	if tt <= float(keys[0][0]):
		return float(keys[0][idx]) if (keys[0] as Array).size() > idx else def
	for i in keys.size() - 1:
		var a: Array = keys[i]
		var b: Array = keys[i + 1]
		if tt <= float(b[0]):
			var f := (tt - float(a[0])) / maxf(0.001, float(b[0]) - float(a[0]))
			var e := String(b[idx + 1]) if b.size() > idx + 1 and b[idx + 1] is String else egri
			var va := float(a[idx]) if a.size() > idx and not (a[idx] is String) else def
			var vb := float(b[idx]) if b.size() > idx and not (b[idx] is String) else def
			return lerpf(va, vb, _ease(f, e))
	var l: Array = keys[keys.size() - 1]
	return float(l[idx]) if l.size() > idx and not (l[idx] is String) else def


static func anim_deger(keys: Array, tt: float, alan: String, def: float) -> float:
	## [[t, {x, y, r, s, a, e}], ...]: alanın tanımlı olduğu anahtarlar arasında
	var ks: Array = []
	for k in keys:
		var dd: Dictionary = k[1]
		if dd.has(alan):
			ks.append([float(k[0]), float(dd[alan]), String(dd.get("e", "io"))])
	if ks.is_empty():
		return def
	if tt <= float(ks[0][0]):
		return float(ks[0][1])
	for i in ks.size() - 1:
		if tt <= float(ks[i + 1][0]):
			var f := (tt - float(ks[i][0])) / maxf(0.001, float(ks[i + 1][0]) - float(ks[i][0]))
			return lerpf(float(ks[i][1]), float(ks[i + 1][1]), _ease(f, String(ks[i + 1][2])))
	return float(ks[ks.size() - 1][1])


func _guncelle(c: Dictionary, tt: float) -> void:
	if c.is_empty() or not is_instance_valid(c.get("kok")):
		return
	var v: Dictionary = c["veri"]
	var px := Vector2(_vp[int(c["slot"])].size)
	var s0 := maxf(px.x / TUVAL.x, px.y / TUVAL.y) * 1.04
	var kam: Array = v.get("kamera", [[0, 1280, 720, 1.0]])
	var cam := Vector2(anahtar(kam, tt, 1, 1280.0), anahtar(kam, tt, 2, 720.0))
	var z := anahtar(kam, tt, 3, 1.0)
	# sarsıntı
	var sh := Vector2.ZERO
	for e in v.get("sars", []):
		var dt := tt - float(e[0])
		var sure := float(e[2]) if (e as Array).size() > 2 else 0.8
		if dt >= 0.0 and dt < sure:
			var a := float(e[1]) * (1.0 - dt / sure)
			sh += Vector2(sin(tt * 61.0) + sin(tt * 37.0) * 0.5, cos(tt * 53.0) + sin(tt * 29.0) * 0.5) * a
	# flaş (yalnızca şimdiki çekim)
	if c == _cur:
		var fa := 0.0
		var fc := Color(1.0, 0.95, 0.85)
		for e in v.get("flas", []):
			var dt := tt - float(e[0])
			var sure := float(e[2]) if (e as Array).size() > 2 else 0.5
			if dt >= 0.0 and dt < sure:
				fa = maxf(fa, float(e[1]) * pow(1.0 - dt / sure, 2.0))
				if (e as Array).size() > 3:
					fc = Color(float(e[3][0]), float(e[3][1]), float(e[3][2]))
		_emat.set_shader_parameter("flas", Color(fc, fa))
	var odak: Array = v.get("odak", [])
	var f := anahtar(odak, tt, 1, -1.0)
	var guc := float(v.get("odak_guc", 14.0))
	for o in c["oge"]:
		var dd := float(o["d"])
		var zd := 1.0 + (z - 1.0) * dd
		var cd := TUVAL * 0.5 + (cam - TUVAL * 0.5) * dd + sh * dd
		var dz: Node2D = o["duzlem"]
		dz.scale = Vector2.ONE * zd * s0
		dz.position = px * 0.5 - cd * zd * s0
		if o["tur"] == "efekt":
			(o["efekt"] as SinemaEfekt).adim(tt)
			continue
		var k: Dictionary = o["veri"]
		var pn: Node2D = o["pivot"]
		var an: Array = k.get("anim", [])
		var al := float(k.get("a", 1.0))
		if not an.is_empty():
			pn.position = Vector2(o["piv"]) + Vector2(anim_deger(an, tt, "x", 0.0), anim_deger(an, tt, "y", 0.0))
			pn.rotation = deg_to_rad(anim_deger(an, tt, "r", 0.0))
			pn.scale = Vector2.ONE * anim_deger(an, tt, "s", 1.0)
			al *= anim_deger(an, tt, "a", 1.0)
		var sp: Sprite2D = o["sprite"]
		sp.modulate.a = al
		var mat := sp.material as ShaderMaterial
		var rv := 1.0
		if k.has("acilis"):
			var ac: Array = k["acilis"]
			rv = clampf((tt - float(ac[0])) / maxf(0.01, float(ac[1]) - float(ac[0])), 0.0, 1.0)
			rv = rv * rv * (3.0 - 2.0 * rv) if int(k.get("kip", 0)) == 0 else rv
		mat.set_shader_parameter("reveal", rv)
		var bl := float(k.get("bulanik", 0.0))
		if f >= 0.0 and not bool(k.get("keskin", false)):
			bl += absf(dd - f) * guc
		mat.set_shader_parameter("blur", bl / float(o["olcek"]))
		var gl: Sprite2D = o["isik"]
		if gl != null:
			var na := float(k.get("isik_a", 0.85))
			gl.modulate = Color(1, 1, 1, al * na * (0.8 + 0.2 * sin(tt * 1.7 + float(o["d"]) * 3.0)))
			var gm := gl.material as ShaderMaterial
			gm.set_shader_parameter("reveal", rv)
			gm.set_shader_parameter("blur", bl * 0.5)


# ------------------------------------------------------------------ girdi: basılı tutunca geç
func _girdi(delta: float) -> void:
	var bas := Input.is_action_pressed("duraklat") or Input.is_action_pressed("zipla") or Input.is_action_pressed("saldiri1") \
		or Input.is_physical_key_pressed(KEY_ENTER) or Input.is_physical_key_pressed(KEY_ESCAPE) or Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT)
	if not bas:
		_serbest = true
	if bas and _serbest and _kapanis < 0.0:
		_basili += delta
		_ipucu_t = 2.5
		if _basili >= GEC_SURE:
			_bitir()
	else:
		_basili = maxf(0.0, _basili - delta * 3.0)
		_ipucu_t = maxf(0.0, _ipucu_t - delta)


func _input(event: InputEvent) -> void:
	# sinema sürerken oyunun girdisi (duraklat menüsü vb.) tetiklenmesin
	if event is InputEventKey or event is InputEventJoypadButton or event is InputEventMouseButton:
		get_viewport().set_input_as_handled()


func _bitir() -> void:
	if _kapanis >= 0.0:
		return
	_kapanis = 0.0


# ------------------------------------------------------------------ yazı
func _yazilar() -> Array:
	return cekimler[ci].get("yazi", []) if ci >= 0 and ci < cekimler.size() else []


func _ciz() -> void:
	var c := _yazi
	var vp := c.get_viewport_rect().size
	if _jenerik:
		_ciz_jenerik(c, vp)
	elif ci >= 0:
		for y in _yazilar():
			_ciz_yazi(c, vp, y)
	# geçme göstergesi: fırça çemberi
	if _ipucu_t > 0.0 and _kapanis < 0.0 and not bool(veri.get("gizli_gec", false)):
		var a := clampf(_ipucu_t / 0.5, 0.0, 1.0)
		var cp := Vector2(vp.x - 34.0, vp.y - 30.0)
		InkUI.ring(c, cp, 14.0, _basili / GEC_SURE, Color(ALTIN, a), true)
		var fb := InkUI.font("body")
		var hint := "Geçmek için basılı tut"
		var w := fb.get_string_size(hint, HORIZONTAL_ALIGNMENT_LEFT, -1, 11).x
		c.draw_string(fb, Vector2(cp.x - 24.0 - w, cp.y + 4.0), hint, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(BONE, 0.6 * a))


func _ciz_yazi(c: Control, vp: Vector2, y: Dictionary) -> void:
	var t0 := float(y.get("t", 0.0))
	var sure := float(y.get("sure", 4.0))
	var lt := t - t0
	if lt < 0.0 or lt > sure + 0.8:
		return
	var out := clampf((sure + 0.8 - lt) / 0.8, 0.0, 1.0)
	var stil := String(y.get("stil", "anlati"))
	var metin := String(y.get("metin", ""))
	var col := BONE
	if y.has("renk"):
		var rc: Array = y["renk"]
		col = Color(float(rc[0]), float(rc[1]), float(rc[2]))
	match stil:
		"bolum":
			# bölüm başlığı: küçük büyük harf sıra + fırça ad + altın çizgi
			var fc := InkUI.font("caps")
			var fbr := InkUI.font("brush")
			var no := String(y.get("ust", ""))
			var a := clampf(lt / 0.8, 0.0, 1.0) * out
			var wn := fc.get_string_size(no, HORIZONTAL_ALIGNMENT_LEFT, -1, 15).x
			c.draw_string(fc, Vector2((vp.x - wn) * 0.5, vp.y * 0.36), no, HORIZONTAL_ALIGNMENT_LEFT, -1, 15, Color(ALTIN, a * 0.9))
			_firca_yazi(c, fbr, metin, Vector2(vp.x * 0.5, vp.y * 0.36 + 58.0), 52, col, lt - 0.3, out, 14.0)
			var st := InkUI.tex("stroke")
			var ww := minf(1.0, maxf(0.0, lt - 0.8) / 0.8) * 220.0
			if st and ww > 0.0:
				c.draw_texture_rect(st, Rect2(vp.x * 0.5 - ww * 0.5, vp.y * 0.36 + 72.0, ww, 5.0), false, Color(InkUI.SEAL, 0.85 * out))
		"ad":
			# boss adı: dev fırça yazısı soldan sağa mürekkeple
			_firca_yazi(c, InkUI.font("brush"), metin, Vector2(vp.x * 0.5, vp.y * 0.5 + 6.0), 62, col, lt, out, 12.0)
			var alt := String(y.get("alt", ""))
			if alt != "":
				var fl := InkUI.font("caps")
				var wa := fl.get_string_size(alt, HORIZONTAL_ALIGNMENT_LEFT, -1, 13).x
				c.draw_string(fl, Vector2((vp.x - wa) * 0.5, vp.y * 0.5 - 52.0), alt, HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color(ALTIN, clampf(lt / 0.6, 0.0, 1.0) * out * 0.9))
		_:
			_daktilo(c, vp, metin, stil, col, lt, out, y)


func _firca_yazi(c: Control, f: Font, s: String, merkez: Vector2, fs: int, col: Color, lt: float, out: float, hiz: float) -> void:
	## Harf harf fırça: harf önce kalın / bulanık (mürekkep yayılıyor), sonra oturur
	var w := f.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	var x0 := merkez.x - w * 0.5
	var shown := lt * hiz
	for i in s.length():
		var a := clampf((shown - float(i)) / 2.5, 0.0, 1.0) * out
		if a <= 0.0:
			break
		var px := x0 + f.get_string_size(s.substr(0, i), HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		var ch := s.substr(i, 1)
		var p := Vector2(px, merkez.y + (1.0 - a) * 4.0)
		c.draw_string_outline(f, p, ch, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, 6, Color(0.02, 0.02, 0.03, 0.55 * a))
		if a < 1.0:
			c.draw_string_outline(f, p, ch, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, int(5.0 * (1.0 - a)) + 1, Color(col, a * 0.3))
		c.draw_string(f, p, ch, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color(col, a))


func _daktilo(c: Control, vp: Vector2, s: String, stil: String, col: Color, lt: float, out: float, y: Dictionary) -> void:
	var f := InkUI.font("lore")
	var fs := int(y.get("boy", 24 if stil == "orta" else (19 if stil == "soz" else 21)))
	var lines := s.split("\n")
	var lh := fs * 1.45
	var y0: float
	match stil:
		"orta":
			y0 = vp.y * 0.5 - lines.size() * lh * 0.5
		"soz":
			y0 = vp.y * 0.74 - lines.size() * lh * 0.5
		_:
			y0 = vp.y - 46.0 - lines.size() * lh - float(cekimler[ci].get("bant", veri.get("bant", 0.0))) * vp.y * 0.0
	# ardında yumuşak yıkama bandı
	var band_a := clampf(lt * 1.5, 0.0, 1.0) * out
	var wash := InkUI.tex("smoke")
	var koyu := col.get_luminance() < 0.4   # açık kâğıt üstünde koyu mürekkep yazı: yıkama bandı yok
	var kontur := Color(0.95, 0.9, 0.8, 0.0) if koyu else Color(0.01, 0.01, 0.02, 0.45)
	if wash and stil != "orta" and not koyu:
		var by := y0 + lines.size() * lh * 0.5
		c.draw_texture_rect(wash, Rect2(vp.x * 0.12, by - 66.0, vp.x * 0.76, 132.0), false, Color(0.02, 0.02, 0.03, 0.5 * band_a))
	var shown := lt * float(y.get("hiz", YAZI_HIZ))
	var k := 0
	for li in lines.size():
		var line: String = lines[li]
		var w := f.get_string_size(line, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		var x := (vp.x - w) * 0.5
		var yy := y0 + li * lh + fs
		for i in line.length():
			var a := clampf((shown - float(k)) / 6.0, 0.0, 1.0) * out
			k += 1
			if a <= 0.0:
				break
			var ch := line.substr(i, 1)
			var px := x + f.get_string_size(line.substr(0, i), HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
			var p := Vector2(px, yy + (1.0 - a) * 5.0)
			if kontur.a > 0.0:
				c.draw_string_outline(f, p, ch, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, 4, Color(kontur, kontur.a * a))
			if a < 1.0:
				c.draw_string_outline(f, p, ch, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, int(3.0 * (1.0 - a)) + 1, Color(col, a * 0.25))
			c.draw_string(f, p, ch, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color(col, a))


func _ciz_jenerik(c: Control, vp: Vector2) -> void:
	## Jenerik: son çekimin üstünde sırayla belirip kaybolan adlar (fırçayla, ortada)
	c.draw_rect(Rect2(Vector2.ZERO, vp), Color(0.02, 0.02, 0.03, clampf(_jt / 2.0, 0.0, 0.6)))
	var J: Array = Data.story.get("jenerik", [])
	var fl := InkUI.font("caps")
	var fs := InkUI.font("lore")
	for q in J.size():
		var st := 1.5 + q * 2.6
		var lt := _jt - st
		if lt < 0.0 or lt > 4.2:
			continue
		var a := clampf(minf(lt / 0.8, (4.2 - lt) / 0.9), 0.0, 1.0)
		var e: Array = J[q]
		var yy := vp.y * 0.5 - 20.0 - lt * 6.0
		var big := 30 if q == 0 else 22
		var s1 := String(e[0])
		var w1 := fl.get_string_size(s1, HORIZONTAL_ALIGNMENT_LEFT, -1, big).x
		c.draw_string(fl, Vector2((vp.x - w1) * 0.5, yy), s1, HORIZONTAL_ALIGNMENT_LEFT, -1, big, Color(1.0, 0.86, 0.55, a))
		if String(e[1]) != "":
			var s2 := String(e[1])
			var w2 := fs.get_string_size(s2, HORIZONTAL_ALIGNMENT_LEFT, -1, 17).x
			c.draw_string(fs, Vector2((vp.x - w2) * 0.5, yy + 30.0), s2, HORIZONTAL_ALIGNMENT_LEFT, -1, 17, Color(BONE, a * 0.85))
		var st_t := InkUI.tex("stroke")
		if st_t:
			c.draw_texture_rect(st_t, Rect2(vp.x * 0.5 - w1 * 0.4 * a, yy + 8.0, w1 * 0.8 * a, 4.0), false, Color(InkUI.SEAL, 0.8 * a))
