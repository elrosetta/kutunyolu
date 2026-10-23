class_name HikayeSahne
extends Node2D
## v42 Güneş Ana hikâyesi — dünyada anlatı (Level kancaları: sahne_yeri, hikaye_yeri; yurt; boss arenası).
##
##  * Bölüm sahnesi (Level.sahne_yeri: ana yolun en geniş düz tabanı): bölüme özgü süs — Ötüken'de yanmış tan töreni
##    çemberi, Bozkır / Tamu'da kırık güneş sunağı, Şahmeran / Kaf'ta zincirli tan kuşu — ve bir bitig taşı (kaya
##    resimli yazıt). Bitig taşının yanına gelince yazıtı (data/story.json "lore") taşın üstünde okunur.
##  * Hikâye odası (Level.hikaye_yeri; opts.hikaye_odasi ile her üç bölümden birinde açılan yaratıksız çıkmaz oda):
##    sıcak ışıkta bir sunak / zincirli kuş; içeri girince Gün Ana görümü (story.json "oda").
##  * Biyoma ilk girişte (kalıcı, bir kez) Gün Ana görümü; bölüm başlığı HUD afişinde (bölüm adı + epigraf).
##  * Boss arenası: boss kükreyince sözü (story.json "boss"), devrilince son sözü ve Gün Örgüsü (GunParcasi.gd).
##  * Yurt: Ulu Kayın'ın (yh_kayin) dallarında alınan her örgü için bir altın yaprak kümesi, havada altın yapraklar;
##    tan söktükten sonra yurt sabah ışığında (yurt_sabah).

const TS := 24.0
## bölüm sahnesi: [büyük süs, ikinci süs] (bitig taşı her zaman en sonda)
const SAHNE := {"otuken": ["tan_halkasi"], "bozkir": ["gun_sunagi"], "sahmeran": ["zincirli_kus"], "kaf": ["zincirli_kus"], "tamu": ["gun_sunagi"]}
const ODA := {"otuken": "gun_sunagi", "bozkir": "zincirli_kus", "sahmeran": "gun_sunagi", "kaf": "gun_sunagi", "tamu": "zincirli_kus"}

var level: Node
var _taslar: Array = []        # [konum, yazıt, yakın mı, okundu mu]
var _oda := Vector2.INF
var _oda_gordu := false
var _t := 0.0
var _biyom := ""
var gorum_plan := -1.0          # bu kadar sn sonra biyom görümü (bir kez)
var okunan := 0                 # test: okunan bitig taşı
var sahne_kuruldu := false      # test
var sahne_merkez := Vector2.INF  # test / çekim: büyük süsün yeri
var oda_kuruldu := false        # test


static func kur(lv: Node) -> HikayeSahne:
	## Level.build sonunda: bölüm sahnesi + hikâye odası + ilk giriş görümü
	var h := HikayeSahne.new()
	h.level = lv
	h.z_index = 40
	lv.add_child(h)
	h._biyom = String(lv.biome.get("id", "otuken"))
	h._sahne()
	h._hikaye_odasi()
	if not Hikaye.gorum_goruldu("biyom:" + h._biyom) or Hikaye.safak() and not Hikaye.gorum_goruldu("biyom_safak:" + h._biyom):
		h.gorum_plan = 6.4   # bölüm afişi (6 sn) bittikten sonra
	return h


static func oda_acik(depth: int, seed_v: int) -> bool:
	## Hikâye odası her üç bölümden birinde (tohum + derinlik; üretici zarı tüketilmez). --hikaye_odasi zorlar.
	if OS.get_cmdline_user_args().has("--hikaye_odasi"):
		return true
	return posmod(seed_v + depth * 7, 3) == 0


# ------------------------------------------------------------------ yerleşim
func _prop(dname: String, pos: Vector2, z := -3, flip := false, glow_k := 1.0) -> Sprite2D:
	## Mürekkep süsü (sus_v2.json): Level._decor_ink ile aynı malzeme, ama zar kullanmaz (bölüm üretimi değişmesin)
	var d: Dictionary = level._decor_v2(dname)
	if d.is_empty():
		return null
	var s := Sprite2D.new()
	s.texture = d["tex"]
	s.centered = false
	var k := 1.0 / float(d.get("texel", 4.0))
	s.scale = Vector2(-k if flip else k, k)
	s.offset = Vector2(-float(d["origin"][0]), -float(d["origin"][1]))
	s.position = pos
	s.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/env_ink.gdshader")
	m.set_shader_parameter("moon_gain", float(level.art.get("ground_moon_gain", 0.6)))
	var dt: Array = level.art.get("decor_tint", [1.0, 1.0, 1.0])
	m.set_shader_parameter("tint", Color(dt[0], dt[1], dt[2]))
	s.material = m
	s.z_index = z
	level.decor_root.add_child(s)
	if d.get("glow_tex") != null:
		var g := Sprite2D.new()
		g.texture = d["glow_tex"]
		g.centered = false
		g.offset = s.offset
		g.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		var gm := CanvasItemMaterial.new()
		gm.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		gm.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		g.material = gm
		g.self_modulate = Color(1.5 * glow_k, 1.3 * glow_k, 1.0 * glow_k)
		s.add_child(g)
		var tw := g.create_tween().set_loops()
		tw.tween_property(g, "self_modulate:a", 0.6, 1.4).set_trans(Tween.TRANS_SINE)
		tw.tween_property(g, "self_modulate:a", 1.0, 1.6).set_trans(Tween.TRANS_SINE)
	return s


func _zemin(tx: float, ty_dur: int) -> Vector2:
	## Ayakta durulan satır ty_dur → zeminin üst kenarı (dünya)
	return Vector2(tx * TS + TS * 0.5, (ty_dur + 1) * TS + 2.0)


func _sahne() -> void:
	## Bölüm sahnesi: önce Level.sahne_yeri çevresinde, olmazsa ana yol odalarının tabanında; büyük süs ve bitig taşı
	## düz, üstü açık, eşya / kaide / Kut Taşı / tüccar / kapıyla çakışmayan yerlere (bölüm zarı tüketilmez)
	var sy: Dictionary = level.sahne_yeri
	var depth := int(Game.run.get("depth", 1))
	var buyuk: Array = SAHNE.get(_biyom, ["gun_sunagi"])
	var genis := {"tan_halkasi": 7, "gun_sunagi": 5, "zincirli_kus": 4}
	var gw := float(genis.get(buyuk[0], 5))
	var hedef := float(level.exit_pos.x / TS) * 0.5
	if not sy.is_empty():
		hedef = (float(sy["x0"]) + float(sy["x1"])) * 0.5
	var adaylar := _taban_adaylari()
	var bx := _yer_sec(adaylar, hedef, gw * 0.5)
	if not bx.is_empty():
		var p0 := _zemin(float(bx["x"]), int(bx["y"]))
		_prop(String(buyuk[0]), p0, -3, depth % 2 == 1)
		level.add_light(p0 + Vector2(0, -50), Color(1.0, 0.7, 0.35), 200.0, 0.7, level.decor_root)
		sahne_merkez = p0
		hedef = float(bx["x"]) - gw * 0.5 - 2.0
		# bitig taşı büyük süsün yanında (aynı tabanda olmasa da yakın)
		for c in adaylar:
			if absf(float(c[0]) - float(bx["x"])) < gw * 0.5 + 1.4:
				c[2] = false
	var tx := _yer_sec(adaylar, hedef, 1.2)
	if not tx.is_empty():
		var p := _zemin(float(tx["x"]), int(tx["y"]))
		_prop("bitig_tasi", p, -3)
		var idx := depth * 3 + int(level.rng.seed % 7)
		_taslar.append([p, Hikaye.lore(_biyom, idx), false, false])
	sahne_kuruldu = not bx.is_empty() or not tx.is_empty()


func _taban_adaylari() -> Array:
	## Ana yol odalarının tabanı: [karo x, ayakta durulan satır, kullanılabilir]; üstü 4 karo açık, altı katı
	var out: Array = []
	for rm in level.main_rooms():
		if not rm.has("fl"):
			continue
		var ix0 := int(rm["ix0"])
		var fl: Array = rm["fl"]
		for x in range(ix0, int(rm["ix1"]) + 1):
			var y := int(fl[x - ix0]) - 1
			var ok: bool = level.cell(x, y + 1) == 1
			for k in 4:
				ok = ok and level.cell(x, y - k) == 0
			if ok:
				out.append([x, y, true])
	return out


func _yer_sec(adaylar: Array, hedef: float, yari: float) -> Dictionary:
	## Hedefe en yakın, yari karo boyunca aynı tabanda düz ve boş yer: {x (kesirli, orta), y}
	var by_x := {}
	for c in adaylar:
		by_x[int(c[0])] = c
	var en: Dictionary = {}
	var en_d := 1e9
	for c in adaylar:
		if not bool(c[2]):
			continue
		var cx := float(c[0]) + (0.5 if int(ceil(yari * 2.0)) % 2 == 1 else 0.0)
		var y := int(c[1])
		var ok := true
		for x in range(int(floor(cx - yari)), int(ceil(cx + yari)) + 1):
			var d: Variant = by_x.get(x)
			if d == null or int(d[1]) != y or not bool(d[2]):
				ok = false
				break
		if not ok or not _bos_mu(cx, yari + 0.5):
			continue
		var dd := absf(cx - hedef)
		if dd < en_d:
			en_d = dd
			en = {"x": cx, "y": y}
	return en


func _bos_mu(tx: float, yari: float) -> bool:
	## Karo x çevresinde (yari karo) kaideli eşya / tomar / sunak, Kut Taşı, zamanlı kapı, tüccar, giriş / çıkış yok mu
	var px := tx * TS + TS * 0.5
	var r := yari * TS
	if level.bezirgan_alani(int(tx), int(ceil(yari)) + 1):
		return false
	for p in level.pickups:
		if is_instance_valid(p) and absf(p.global_position.x - px) < r + 20.0 and String(p.kind) in ["item", "tilsim", "lutuf", "parsomen"]:
			return false
	for n in level.tasi + level.zamanli + level.sandiklar:
		if is_instance_valid(n) and absf(n.global_position.x - px) < r + 30.0:
			return false
	if absf(level.exit_pos.x - px) < r + 60.0:
		return false
	if level.player and absf(level.player.global_position.x - px) < r + 60.0:
		return false   # doğuş noktası
	return true


func _hikaye_odasi() -> void:
	var hy: Dictionary = level.hikaye_yeri
	if hy.is_empty():
		return
	var p := _zemin(float(hy["x"]), int(hy["y"]))
	_prop(String(ODA.get(_biyom, "gun_sunagi")), p + Vector2(18, 0), -3, false, 1.3)
	var l: PointLight2D = level.add_light(p + Vector2(10, -60), Color(1.0, 0.72, 0.36), 260.0, 1.1, level.decor_root)
	if l:
		level.titrek(l, "kristal")
	_oda = p
	oda_kuruldu = true


# ------------------------------------------------------------------ yurt
static func yurt_sabah(art: Dictionary) -> void:
	## Tan söktükten sonra yurt sabah ışığında (Level.build_hub, ışıklar kurulmadan): sıcak ortam, güneş rengi
	## "ay" ışığı, derece sıcak / açık
	if not Hikaye.safak():
		return
	art["ambient"] = [0.98, 0.9, 0.82]
	art["sun"] = [1.0, 0.86, 0.66]
	art["sun_energy"] = 0.42
	var g: Dictionary = (art.get("grade", {}) as Dictionary).duplicate()
	g["shadow_tint"] = [1.0, 0.9, 0.92]
	g["mid_tint"] = [1.05, 1.0, 0.94]
	g["high_tint"] = [1.08, 0.98, 0.86]
	g["high_k"] = 0.5
	g["edge_color"] = [0.12, 0.06, 0.05, 1.0]
	g["strength"] = 0.35
	art["grade"] = g


static func yurt(lv: Node) -> HikayeSahne:
	## Yurt: Ulu Kayın'ın (yh_kayin, 24.6. karo) dallarında her örgü için altın yaprak kümesi + düşen altın yapraklar
	var h := HikayeSahne.new()
	h.level = lv
	lv.add_child(h)
	h._biyom = "yurt"
	var n := Hikaye.parca_sayi() if not Hikaye.safak() else 7
	var root: Vector2 = lv._hub_px(24.6, 2.0)
	var rng := RandomNumberGenerator.new()
	rng.seed = 4242
	for k in n * 7:
		var a := rng.randf() * TAU
		var r := sqrt(rng.randf())
		var p := root + Vector2(-6.0 + cos(a) * r * 84.0, -168.0 + sin(a) * r * 52.0)
		var s := h._prop("altin_yaprak", p, -5, rng.randf() < 0.5, 1.2)
		if s:
			s.rotation = rng.randf_range(-0.8, 0.8)
			var tw := s.create_tween().set_loops()
			tw.tween_property(s, "rotation", s.rotation + 0.18, rng.randf_range(1.2, 2.0)).set_trans(Tween.TRANS_SINE)
			tw.tween_property(s, "rotation", s.rotation - 0.1, rng.randf_range(1.2, 2.0)).set_trans(Tween.TRANS_SINE)
	if n > 0:
		lv.add_light(root + Vector2(0, -170), Color(1.0, 0.78, 0.4), 220.0 + 30.0 * n, 0.25 + 0.12 * n, lv.decor_root)
		var d: Dictionary = lv._decor_v2("altin_yaprak")
		var pe: CPUParticles2D = lv._hub_emitter(root + Vector2(0, -170), 2 + n * 2, 7.0, Color(1.4, 1.15, 0.7, 1.0), Vector2(80, 40), true, 4)
		if not d.is_empty():
			pe.texture = d["tex"]
		pe.direction = Vector2(0.3, 1)
		pe.spread = 25.0
		pe.initial_velocity_min = 8.0
		pe.initial_velocity_max = 18.0
		pe.gravity = Vector2(4, 9)
		pe.angular_velocity_min = -90.0
		pe.angular_velocity_max = 90.0
		pe.scale_amount_min = 0.2
		pe.scale_amount_max = 0.3
	h.sahne_kuruldu = true
	return h


# ------------------------------------------------------------------ boss
static func boss(lv: Node) -> void:
	## Arena kuruldu: kükreyişten sonra sözü
	var bid := String(lv.boss_id)
	var s := Hikaye.boss_soz(bid, "once")
	if s == "":
		return
	lv.get_tree().create_timer(2.3, false).timeout.connect(func() -> void:
		if is_instance_valid(lv) and lv.boss != null:
			Gorum.konus(Hikaye.boss_ad(bid), s, Color(1.0, 0.62, 0.5)))


static func boss_dustu(lv: Node, e: Node) -> void:
	## Boss devrildi: son sözü ve Gün Örgüsü düşer (örgü daha önce alındıysa yalnızca söz: dünya zaten ısındı)
	var bid := String(lv.boss_id)
	var s := Hikaye.boss_soz(bid, "sonra")
	if s != "":
		Gorum.konus(Hikaye.boss_ad(bid), s, Color(1.0, 0.62, 0.5))
	if Hikaye.orgu(bid).is_empty():
		return
	var gp := GunParcasi.new()
	gp.bid = bid
	gp.level = lv
	gp.position = e.center() if e.has_method("center") else e.global_position
	lv.add_child(gp)


# ------------------------------------------------------------------ zaman
func _process(delta: float) -> void:
	_t += delta
	if gorum_plan > 0.0:
		gorum_plan -= delta
		if gorum_plan <= 0.0:
			Gorum.gorum(Hikaye.gorum_satiri(_biyom))
			Hikaye.gorum_isaretle(("biyom_safak:" if Hikaye.safak() else "biyom:") + _biyom)
	var pl: Node = level.player if level else null
	if pl == null:
		return
	var fp: Vector2 = pl.global_position
	if _oda != Vector2.INF and not _oda_gordu and fp.distance_to(_oda) < 110.0:
		_oda_gordu = true
		var i := int(Game.run.get("depth", 1)) + int(Game.meta.get("runs", 0))
		Gorum.gorum(Hikaye.oda_satiri(_biyom, i))
		Hikaye.gorum_isaretle("oda:%s:%d" % [_biyom, posmod(i, 3)])
		FX.soul(_oda + Vector2(0, -40), Color(1.0, 0.8, 0.45), 18)
	var ciz := false
	for tas in _taslar:
		var yakin: bool = absf(fp.x - (tas[0] as Vector2).x) < 46.0 and absf(fp.y - (tas[0] as Vector2).y) < 70.0
		if yakin != bool(tas[2]):
			tas[2] = yakin
			ciz = true
			if yakin and not bool(tas[3]):
				tas[3] = true
				okunan += 1
				Ses.play("ui_ac", -10.0, 0.8)
	if ciz or _taslar.any(func(x: Array) -> bool: return bool(x[2])):
		queue_redraw()


func _bolum_baslik() -> String:
	var c := Hikaye.bolum(_biyom)
	return "" if c.is_empty() else "%s · %s" % [String(c.get("no", "")), String(c.get("ad", ""))]


func _draw() -> void:
	for tas in _taslar:
		if not bool(tas[2]):
			continue
		var p: Vector2 = tas[0]
		var lines := PixUI.wrap(String(tas[1]), 230)
		var y0 := p.y - 118.0 - lines.size() * 11.0 + sin(_t * 2.0) * 1.5
		var w := 250.0
		draw_rect(Rect2(p.x - w * 0.5 - 6, y0 - 6, w + 12, lines.size() * 11.0 + 12), Color(0.03, 0.025, 0.03, 0.62))
		for li in lines.size():
			PixUI.text(self, Vector2(p.x - w * 0.5, y0 + li * 11.0), String(lines[li]), Color(1.0, 0.86, 0.6), 1, HORIZONTAL_ALIGNMENT_CENTER, w, 2)
