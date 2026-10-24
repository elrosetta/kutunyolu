class_name OrtamCila
extends Node
## v40 ortam cilası (Level._build_particles sonunda kurulur; yalnızca stil v2 mürekkep ortamı):
##   * temas gölgeleri: platformların ve tavan çıkıntılarının altına, arka plana düşen yumuşak gölge şeritleri + duvar
##     diplerinde zemine düşen köşe gölgesi (tek Polygon2D, köşe renkli; çizim çağrısı 2)
##   * hava canlıları: biyoma göre uzakta süzülen karga / kartal / yarasa siluetleri (CPUParticles2D, 4 kare kanat
##     çırpışı, ekran uzayı katman -9: paralaksın önünde, dünyanın arkasında)
##   * rüzgâr esintisi: zamanla değişen esinti + aralıklı güçlü esinti; ön plan şeritleri (fg_sway amp/speed), örtü
##     öbekleri (env_ink sway_px), süzülen yaprak parçacıkları aynı esintiyle salınır (data/stil_v2.json "ruzgar" çarpanı)
##   * bakış anıtları: geniş açık odalarda arka plana (z -4) biyomun anıtı (anit_<biyom>_v2: Ötüken kurt başlı
##     kam direkleri ve ulu kayın kökü, Bozkır kurgan, Kaf buz kulesi, Şahmeran yılan sütunu, Tamu kemik kapısı)

var level: Level
var yapraklar: CPUParticles2D          # Level._build_particles'ın yaprak / kırıntı / kül üreticisi (yoksa null)
var _fg_mats: Array = []
var _fg_amp: Array = []
var _fg_hazir := false
var _tuft_mat: ShaderMaterial
var _tuft_base := 0.0
var _ruzgar_k := 1.0
var _t := 0.0
var _esinti_t := 7.0       # sonraki güçlü esintiye kalan süre
var _esinti := 0.0         # güçlü esinti şiddeti (0..1, yükselip söner)
var _yaprak_hiz := Vector2.ZERO
var _yaprak_cek := Vector2.ZERO
var _last_wind := -1.0

## biyom varsayılanları (data/stil_v2.json "hava" ile ezilir): doku, kare, sayı, hız (px/sn), y bandı (ekran oranı),
## ölçek, renk, kanat hızı (çırpış/sn), yön (+1 sağa)
const HAVA := {
	"otuken": {"tex": "hava_karga", "n": 4, "hiz": [22.0, 40.0], "y": [0.06, 0.42], "olcek": [0.28, 0.5], "renk": "1a1420", "alfa": 0.8, "cirp": 2.4, "yon": -1.0, "yayil": 10.0},
	"bozkir": {"tex": "hava_kartal", "n": 3, "hiz": [14.0, 26.0], "y": [0.08, 0.38], "olcek": [0.3, 0.55], "renk": "3a2232", "alfa": 0.85, "cirp": 0.5, "yon": 1.0, "yayil": 8.0},
	"kaf": {"tex": "hava_kartal", "n": 2, "hiz": [12.0, 22.0], "y": [0.06, 0.3], "olcek": [0.3, 0.5], "renk": "1a1c30", "alfa": 0.7, "cirp": 0.45, "yon": -1.0, "yayil": 8.0},
	"sahmeran": {"tex": "hava_yarasa", "n": 9, "hiz": [60.0, 110.0], "y": [0.04, 0.5], "olcek": [0.22, 0.4], "renk": "061a1c", "alfa": 0.85, "cirp": 6.0, "yon": 1.0, "yayil": 26.0},
	"tamu": {"tex": "hava_karga", "n": 3, "hiz": [26.0, 46.0], "y": [0.05, 0.36], "olcek": [0.3, 0.5], "renk": "16080a", "alfa": 0.85, "cirp": 2.2, "yon": 1.0, "yayil": 12.0},
	"yurt": {"tex": "hava_karga", "n": 2, "hiz": [16.0, 28.0], "y": [0.05, 0.3], "olcek": [0.26, 0.42], "renk": "0c0e1c", "alfa": 0.75, "cirp": 2.2, "yon": -1.0, "yayil": 8.0},
}
const RUZGAR := {"otuken": 1.0, "bozkir": 1.5, "kaf": 1.35, "sahmeran": 0.3, "tamu": 0.55, "yurt": 0.8}


static var KAPALI := OS.get_cmdline_user_args().has("--v40yok")   # karşılaştırma çekimi: v40 cilası kapalı


static func kur(lv: Level, leaves: CPUParticles2D) -> OrtamCila:
	if KAPALI:
		return null
	var oc := OrtamCila.new()
	oc.level = lv
	oc.yapraklar = leaves
	oc.name = "OrtamCila"
	lv.add_child(oc)
	return oc


func _ready() -> void:
	var bid := _biyom()
	_ruzgar_k = float(level.art.get("ruzgar", RUZGAR.get(bid, 1.0)))
	if not level.hub and not level.konak:
		_temas_golgeleri()
	_hava_canlilari(bid)
	if not level.hub and not level.konak and level.boss_id == "":
		_anitlar()
	if level.konak:
		_konak_susleri()
	if _ruzgar_k >= 1.2 and not Ayarlar.arka_katman_az():
		_esinti_cizgileri()
	# örtü öbekleri (ot / kar tümseği / kül): Bozkır'da zaten salınır (tuft_sway); öbür biyomlarda hafif esinti
	if level.overlay != null and level.overlay.material is ShaderMaterial:
		_tuft_mat = level.overlay.material
		_tuft_base = float(level.art.get("tuft_sway", 1.4))
		_tuft_mat.set_shader_parameter("cell_px", float(level._tile_px()))
	if yapraklar != null and is_instance_valid(yapraklar):
		_yaprak_hiz = Vector2(yapraklar.initial_velocity_min, yapraklar.initial_velocity_max)
		_yaprak_cek = yapraklar.gravity


func _biyom() -> String:
	if level.hub:
		return "yurt"
	return String(level.biome.get("id", "otuken"))


# ------------------------------------------------------------------ temas gölgeleri
func _temas_golgeleri() -> void:
	## Platform / tavan çıkıntısı altındaki havaya (arka plana) düşen yumuşak gölge (ambient occlusion): üstte koyu,
	## aşağı doğru erir, uçlarda daralır. Duvar diplerinde zemine düşen köşe gölgesi ayrı çokgen (z 1: zeminin üstünde).
	var TS: int = Level.TS
	var dc: Array = level.art.get("deep_color", [0.06, 0.04, 0.08])
	var col := Color(float(dc[0]) * 0.5, float(dc[1]) * 0.5, float(dc[2]) * 0.6, 1.0)
	var gk: float = 0.5 if Ayarlar.arka_katman_az() else 1.0
	# dörtgenler: [sol üst, sağ üst, yükseklik, üst alfa, alt alfa, uçlarda daralma]
	var hava: Array = []     # platform / çıkıntı altı (z -1, havada)
	var kose: Array = []     # [x0, x1, y, sol mu] duvar dibi (zemine düşer)
	var y := 1
	while y < level.H - 1:
		var x := 0
		while x < level.W:
			var c := level.cell(x, y)
			if c == 2:
				# tek yönlü platform koşusu
				var x0 := x
				while x < level.W and level.cell(x, y) == 2:
					x += 1
				var ln := float(x - x0)
				hava.append([Vector2(x0 * TS, (y + 1) * TS - 2.0), Vector2(x * TS, (y + 1) * TS - 2.0), TS * 1.9, 0.5 * gk, 0.0, minf(TS * 0.6, ln * TS * 0.25)])
				continue
			if c == 1 and level.cell(x, y + 1) == 0 and level.cell(x, y + 2) == 0:
				# tavan çıkıntısı: altı en az iki karo hava olan katı koşu
				var x0 := x
				while x < level.W and level.cell(x, y) == 1 and level.cell(x, y + 1) == 0 and level.cell(x, y + 2) == 0:
					x += 1
				var ln := float(x - x0)
				if ln >= 2.0:
					hava.append([Vector2(x0 * TS, (y + 1) * TS - 1.0), Vector2(x * TS, (y + 1) * TS - 1.0), TS * (1.6 + minf(ln, 10.0) * 0.12), 0.42 * gk, 0.0, minf(TS * 0.8, ln * TS * 0.2)])
				continue
			if c == 0 and level.cell(x, y + 1) == 1 and level.cell(x, y - 1) == 0:
				# zemin üstünde duvar dibi: sol ya da sağ komşu katı ise köşe gölgesi (zemine düşer)
				var l := level.cell(x - 1, y) == 1 and level.cell(x - 1, y - 1) == 1
				var r := level.cell(x + 1, y) == 1 and level.cell(x + 1, y - 1) == 1
				if l or r:
					kose.append([x, y, l])
			x += 1
		y += 1
	if not hava.is_empty():
		var verts := PackedVector2Array()
		var cols := PackedColorArray()
		var polys: Array = []
		for q in hava:
			var i0 := verts.size()
			var a: Vector2 = q[0]
			var b: Vector2 = q[1]
			var ince: float = q[5]
			verts.append(a)
			verts.append(b)
			verts.append(b + Vector2(-ince, float(q[2])))
			verts.append(a + Vector2(ince, float(q[2])))
			cols.append(Color(col, float(q[3])))
			cols.append(Color(col, float(q[3])))
			cols.append(Color(col, float(q[4])))
			cols.append(Color(col, float(q[4])))
			polys.append(PackedInt32Array([i0, i0 + 1, i0 + 2, i0 + 3]))
		var ust := Polygon2D.new()
		ust.polygon = verts
		ust.polygons = polys
		ust.vertex_colors = cols
		ust.antialiased = true
		ust.z_index = -1
		ust.name = "TemasGolgesi"
		var um := CanvasItemMaterial.new()
		um.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		ust.material = um
		level.add_child(ust)
	if not kose.is_empty() and level.decal_root != null:
		var kv := PackedVector2Array()
		var kc := PackedColorArray()
		var kp: Array = []
		var al := 0.34 * gk
		for q in kose:
			var i0 := kv.size()
			var l: bool = q[2]
			var gy := float((int(q[1]) + 1) * TS)
			var w := TS * 1.4
			var xa := float(int(q[0]) * TS) if l else float((int(q[0]) + 1) * TS) - w
			kv.append(Vector2(xa, gy - 1.0))
			kv.append(Vector2(xa + w, gy - 1.0))
			kv.append(Vector2(xa + w, gy + 5.0))
			kv.append(Vector2(xa, gy + 5.0))
			kc.append(Color(col, al if l else 0.0))
			kc.append(Color(col, 0.0 if l else al))
			kc.append(Color(col, 0.0 if l else al))
			kc.append(Color(col, al if l else 0.0))
			kp.append(PackedInt32Array([i0, i0 + 1, i0 + 2, i0 + 3]))
		var ks := Polygon2D.new()
		ks.polygon = kv
		ks.polygons = kp
		ks.vertex_colors = kc
		ks.antialiased = true
		ks.name = "KoseGolgesi"
		var km := CanvasItemMaterial.new()
		km.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		ks.material = km
		level.decal_root.add_child(ks)


# ------------------------------------------------------------------ hava canlıları
func _hava_canlilari(bid: String) -> void:
	var spec: Dictionary = HAVA.get(bid, {}).duplicate()
	if level.art.has("hava"):
		for k in level.art["hava"]:
			spec[k] = level.art["hava"][k]
	if spec.is_empty() or int(spec.get("n", 0)) <= 0:
		return
	if level.boss_id != "" and bid != "sahmeran":
		return   # arenada yalnızca yarasalar (gök yok)
	var path := "res://assets/bg/%s_v2.png" % String(spec["tex"])
	if not ResourceLoader.exists(path):
		return
	var cl := CanvasLayer.new()
	cl.layer = -9
	cl.name = "HavaCanli"
	level.add_child(cl)
	var vp := level.get_viewport().get_visible_rect().size
	var p := CPUParticles2D.new()
	p.texture = Data.tex(path)
	p.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	var n := int(spec["n"])
	if Ayarlar.arka_katman_az():
		n = maxi(1, n / 2)
	p.amount = n
	var hiz: Array = spec["hiz"]
	var yon := float(spec.get("yon", -1.0))
	var yb: Array = spec["y"]
	var ol: Array = spec["olcek"]
	# ömür: ekranı bir uçtan öbür uca geçecek kadar (+ kenar payı); yeniden doğuş rastgele y'de
	var yol := vp.x + 160.0
	p.lifetime = yol / float(hiz[0])
	p.preprocess = p.lifetime * 0.8
	p.explosiveness = 0.0
	p.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	p.emission_rect_extents = Vector2(10.0, (float(yb[1]) - float(yb[0])) * vp.y * 0.5)
	p.position = Vector2(-80.0 if yon > 0.0 else vp.x + 80.0, (float(yb[0]) + float(yb[1])) * 0.5 * vp.y)
	p.direction = Vector2(yon, 0.0)
	p.spread = float(spec.get("yayil", 10.0))
	p.initial_velocity_min = float(hiz[0])
	p.initial_velocity_max = float(hiz[1])
	p.gravity = Vector2.ZERO
	p.scale_amount_min = float(ol[0])
	p.scale_amount_max = float(ol[1])
	p.color = Color(String(spec.get("renk", "101018")), float(spec.get("alfa", 0.8)))
	# kanat çırpışı: 4 kare yatay şerit; anim_speed = ömür boyunca döngü sayısı
	var mat := CanvasItemMaterial.new()
	mat.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	mat.particles_animation = true
	mat.particles_anim_h_frames = int(spec.get("kare", 4))
	mat.particles_anim_v_frames = 1
	mat.particles_anim_loop = true
	p.material = mat
	var cirp := float(spec.get("cirp", 2.0))
	p.anim_speed_min = cirp * p.lifetime * 0.8
	p.anim_speed_max = cirp * p.lifetime * 1.2
	p.anim_offset_min = 0.0
	p.anim_offset_max = 1.0
	# yön: doku sağa uçar; sola uçanlar aynalanır (ölçek eksi)
	if yon < 0.0:
		p.scale = Vector2(-1.0, 1.0)
		p.position.x = vp.x + 80.0
		p.direction = Vector2(1.0, 0.0)   # yerel eksende sağa = ekranda sola
	# uzaklık: yumuşak sis karışımı için hafif saydam; büyük (yakın) olanlar biraz daha koyu (renk rampası yok: tek renk)
	p.local_coords = true
	cl.add_child(p)


# ------------------------------------------------------------------ bakış anıtları
func _anitlar() -> void:
	## Geniş, tavansız odalarda (salon / teras) arka plana biyomun anıtı; bölüm başına en çok 2, oda başına 1.
	## Ayrı rng (bölüm rng'sinin durumundan türetilir): sonraki yerleşimlerin dizisi değişmez.
	var bid := _biyom()
	var d: Dictionary = level._decor_v2("anit")
	if d.is_empty():
		return
	var r := RandomNumberGenerator.new()
	r.seed = int(level.rng.state ^ 0x4F0A17)
	var adaylar: Array = []
	for rm in level.rooms:
		if rm.get("role", "") in ["yok", "cikis", "giris"] or rm.get("odul", "") != "":
			continue
		if not (String(rm.get("kind", "")) in ["salon", "teras", "harabe", "magara", "kule", "cukur", "tepe", "avlu"]):
			continue
		var ix0 := int(rm["ix0"])
		var ix1 := int(rm["ix1"])
		if ix1 - ix0 < 14:
			continue
		adaylar.append(rm)
	var n := 0
	# v43: simge (sahne parçası) şablonunun "*" çapası: anıt oraya kesin konur
	for s in level.propler.get("simge", []):
		_anit_sprite(d, int(s[0]), int(s[1]) + 1, r.randf() < 0.5 and not bool(d.get("noflip", false)))
		n += 1
		for rm in adaylar.duplicate():
			if int(rm.get("id", -1)) == int(s[2]):
				adaylar.erase(rm)
	if adaylar.is_empty():
		return
	adaylar.shuffle()
	var TS: int = Level.TS
	var wtile := int(ceil(float((d["size"] as Array)[0]) / float(d.get("texel", 4.0)) / TS))
	var htile := int(ceil(float((d["size"] as Array)[1]) / float(d.get("texel", 4.0)) / TS))
	# oda tavanları 5-9 karo: anıtın tepesi (yaprak, zincir, tuğ) tavan kayasının ardında kalabilir (z -4, karolar
	# önde çizilir); yalnızca alt 5 karosu açık olsun yeter
	var hgerek := mini(htile, 5)
	for rm in adaylar:
		if n >= 2:
			break
		var ix0 := int(rm["ix0"])
		var ix1 := int(rm["ix1"])
		var best := -1
		var best_sc := 0
		for dene in 10:
			var x := r.randi_range(ix0 + 3 + wtile / 2, ix1 - 3 - wtile / 2)
			if x <= ix0 or x >= ix1:
				continue
			var sy := level.surface_y(x)
			if level.cell(x, sy) != 1:
				continue
			# düz ve açık: anıtın genişliğinde aynı yüzey, üstünde en az hgerek karo hava
			var ok := true
			for dx in range(-wtile / 2, wtile / 2 + 1):
				if level.surface_y(x + dx) != sy or level.cell(x + dx, sy) != 1:
					ok = false
					break
				for dy in range(1, hgerek + 1):
					if level.cell(x + dx, sy - dy) != 0:
						ok = false
						break
				if not ok:
					break
			if ok and level.bezirgan_alani(x, wtile):
				ok = false
			if ok:
				var sc := 1 + (ix1 - ix0)
				if sc > best_sc:
					best_sc = sc
					best = x
		if best >= 0:
			_anit_sprite(d, best, level.surface_y(best), r.randf() < 0.5 and not bool(d.get("noflip", false)))
			n += 1
	if n > 0:
		print("[ortam] anit=%d biyom=%s" % [n, bid])


func _anit_sprite(d: Dictionary, tile_x: int, tile_y: int, flip: bool) -> void:
	## Level._decor_ink'in bölüm rng'sine dokunmayan kopyası (aynalama kararı dışarıdan)
	var TS: int = Level.TS
	var s := Sprite2D.new()
	s.texture = d["tex"]
	s.centered = false
	var k := 1.0 / float(d.get("texel", 4.0))
	s.scale = Vector2(k, k)
	s.offset = Vector2(-float(d["origin"][0]), -float(d["origin"][1]))
	s.position = Vector2(tile_x * TS + TS / 2.0, tile_y * TS + 2)
	s.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/env_ink.gdshader")
	m.set_shader_parameter("moon_gain", float(level.art.get("ground_moon_gain", 0.6)))
	var dt: Array = level.art.get("decor_tint", [1.0, 1.0, 1.0])
	m.set_shader_parameter("tint", Color(dt[0], dt[1], dt[2]))
	s.material = m
	s.z_index = -4
	s.flip_h = flip
	level.decor_root.add_child(s)
	if d.get("glow_tex") != null:
		var g := Sprite2D.new()
		g.texture = d["glow_tex"]
		g.centered = false
		g.offset = s.offset
		g.flip_h = flip
		g.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		var gm := CanvasItemMaterial.new()
		gm.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		gm.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		g.material = gm
		g.self_modulate = Color(1.3, 1.25, 1.2)
		s.add_child(g)
		var tw := g.create_tween().set_loops()
		tw.tween_property(g, "self_modulate:a", 0.6, 1.9).set_trans(Tween.TRANS_SINE)
		tw.tween_property(g, "self_modulate:a", 1.0, 2.1).set_trans(Tween.TRANS_SINE)


# ------------------------------------------------------------------ konak: yaşanmış görünüm
func _konak_susleri() -> void:
	## Gezgin konak: çadırdan ocağın yanındaki direğe fener dizisi, ateş çevresinde ateş böcekleri / kor, yolda ikinci duman
	var G: Dictionary = Data.load_json("res://data/konak.json").get("genel", {})
	var ax := float(G.get("ates", 22))
	var tx := float(G.get("tezgah", 33))
	level._hub_string(level._hub_px(ax - 9.5, -96), level._hub_px(ax - 1.0, -70), 9.0, true, -6)
	level._hub_string(level._hub_px(ax + 1.0, -70), level._hub_px(tx - 2.0, -92), 11.0, true, -6)
	var bid := String(level.biome.get("id", ""))
	var col := Color(1.3, 1.5, 0.55, 0.9)
	if bid == "sahmeran":
		col = Color(0.6, 1.4, 0.9, 0.9)
	elif bid == "tamu":
		col = Color(1.5, 0.7, 0.3, 0.9)
	elif bid == "kaf":
		col = Color(0.8, 1.1, 1.5, 0.8)
	var ff: CPUParticles2D = level._hub_emitter(level._hub_px(ax + 8.0, -40), 26, 6.0, col, Vector2(220, 36), true, 6)
	ff.direction = Vector2(1, -0.2)
	ff.spread = 180.0
	ff.initial_velocity_min = 3.0
	ff.initial_velocity_max = 9.0
	ff.gravity = Vector2(0, -1.5)
	ff.scale_amount_min = 0.09
	ff.scale_amount_max = 0.16


# ------------------------------------------------------------------ rüzgâr
var _cizgi: CPUParticles2D


func _esinti_cizgileri() -> void:
	## Güçlü esintide ekranı rüzgâr yönünde geçen ince mürekkep çizgileri (Bozkır / Kaf); yalnızca esinti anında üretilir
	var cl := CanvasLayer.new()
	cl.layer = -9
	cl.name = "Esinti"
	level.add_child(cl)
	var vp := level.get_viewport().get_visible_rect().size
	var p := CPUParticles2D.new()
	p.texture = InkDraw.particle("k_trace")
	p.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	p.amount = 18
	p.lifetime = 1.3
	p.emitting = false
	p.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	p.emission_rect_extents = Vector2(40.0, vp.y * 0.42)
	var yon := 1.0 if String(level.biome.get("id", "")) == "bozkir" else -1.0
	p.position = Vector2(-70.0 if yon > 0.0 else vp.x + 70.0, vp.y * 0.42)
	p.direction = Vector2(yon, 0.06)
	p.spread = 4.0
	p.initial_velocity_min = 520.0
	p.initial_velocity_max = 760.0
	p.gravity = Vector2.ZERO
	p.scale_amount_min = 0.9
	p.scale_amount_max = 2.2
	p.angle_min = 0.0
	p.angle_max = 0.0
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 0))
	g.set_color(1, Color(1, 1, 1, 0))
	g.add_point(0.25, Color(1, 1, 1, 0.5))
	g.add_point(0.7, Color(1, 1, 1, 0.4))
	p.color_ramp = g
	p.color = Color(0.95, 0.9, 0.86, 1.0) if yon > 0.0 else Color(0.86, 0.92, 1.0, 1.0)
	var m := CanvasItemMaterial.new()
	m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	p.material = m
	cl.add_child(p)
	_cizgi = p


func _process(delta: float) -> void:
	_t += delta
	if not _fg_hazir:
		_fg_bul()
	# süregelen esinti (iki yavaş dalga) + aralıklı güçlü esinti (1,4 sn yükselir, 3,5 sn söner)
	_esinti_t -= delta
	if _esinti_t <= 0.0:
		_esinti = 1.0
		_esinti_t = randf_range(9.0, 18.0)
	_esinti = maxf(0.0, _esinti - delta / 3.5)
	var dalga := 0.5 + 0.5 * sin(_t * 0.37) * sin(_t * 0.11 + 1.3)
	var guc := 1.0 - absf(2.0 * (1.0 - _esinti) - 1.0)   # 0 -> 1 -> 0 üçgen
	var wind := clampf((0.35 + 0.45 * dalga + 1.1 * guc) * _ruzgar_k, 0.0, 2.2)
	if _cizgi != null:
		_cizgi.emitting = guc > 0.35
	if absf(wind - _last_wind) < 0.004:
		return
	_last_wind = wind
	for i in _fg_mats.size():
		var m: ShaderMaterial = _fg_mats[i]
		m.set_shader_parameter("amp_px", float(_fg_amp[i]) * (0.45 + 0.9 * wind))
		m.set_shader_parameter("speed", 1.1 * (0.6 + 0.5 * wind))
	if _tuft_mat != null:
		_tuft_mat.set_shader_parameter("sway_px", _tuft_base * (0.3 + 0.9 * wind))
	if yapraklar != null and is_instance_valid(yapraklar):
		var k := 0.55 + 0.75 * wind
		yapraklar.initial_velocity_min = _yaprak_hiz.x * k
		yapraklar.initial_velocity_max = _yaprak_hiz.y * k
		yapraklar.gravity = Vector2(_yaprak_cek.x * k, _yaprak_cek.y)


func _fg_bul() -> void:
	for c in level.get_children():
		if c is ForegroundV2:
			for S in (c as ForegroundV2)._strips:
				var m: ShaderMaterial = S["mat"]
				_fg_mats.append(m)
				_fg_amp.append(float(m.get_shader_parameter("amp_px")))
			_fg_hazir = true
			return
	# ön plansız biyom / yurt: tekrar arama
	_fg_hazir = true
