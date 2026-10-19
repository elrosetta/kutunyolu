class_name SavasSanati
extends RefCounted
## v27 Savaş Sanatları (Sekiro "Combat Arts" esinli). Ayrıntı: docs/TASARIM.md "v27: savaş sanatları"; veri
## data/sanatlar.json. Player.gd yalnızca birkaç noktadan çağırır (tick, karsila / alinan_k, on_deal); durum burada.
##
## Kaynak: ALP NİŞANI (Sekiro'nun "Spirit Emblem"i gibi ayrık taneler, en çok 5). Kut Bozkurt biçimine (F) ayrılmış
## kalır; nişan yakın vuruş isabetiyle (düşmanın canının payı kadar), öldürmeyle ve ustalıkla (Çarpışma, Karşı Vuruş,
## Kut Alma, duruş kırma, Kut Mührü, Kusursuz Kaçış) dolar. Bir sanat 1-2 nişan: sıradan bir düşman ~yarım nişan,
## seçkin ~1,5, ustalıklı oyuncuda çok daha hızlı: sanat 1-3 dövüşte bir.
## Tuş: T (oyun kolu: LT, v25'te Üç Âlem'den boşaldı). Tek kuşanılan sanat; silah sınıfı desteklemiyorsa simge gri.
## v22 kontrol ilkesi: sanat yalnızca oyuncunun basışıyla başlar; içindeki dizi (Kasırga turları, Göğe Yükseliş'in
## dalışı, Bozkurt Atılışı'nın kın kesiği, Demir Duruş'un karşılığı) basılan sanatın parçasıdır.
##
## Çizim: sanatlar Player'ın v23 3B savuruş düzlemi sistemini kullanır: her karede kol pozu ve düzlem (phi, r, roll)
## burada hesaplanır ve atk sözlüğüne yazılır (sw anahtarları önceki kare → bu kare, atk.plane düzlemi); kol, silah
## önkısalması, arkada çizilen bıçak (çark) ve mürekkep hilali (InkTrail) Player'ın kendi kodundan geçer.

const DATA_PATH := "res://data/sanatlar.json"
static var _data: Dictionary = {}

var p: Player
var cd := 0.0                 # sanat beklemesi (sn)
var cur: Dictionary = {}      # süren sanat
var buf := 0.0                # basış ara belleği
var def_t := 0.0              # Bir Çekiş: Demir Gönül süresi
var def_k := 0.0
var _last_pose: Array = []
var _ev: Dictionary = {}      # v19_stats anlık görüntüsü (nişan ödülleri)
var _pd_prev := 0.0
var _rains: Array = []        # Ok Yağmuru: sürmekte olan sağanaklar
var _msg_t := 0.0
var _kasirga_fx: SanatFX
var _art_hit_t := -9.0        # son sanat vuruşu (sanatın kendi kırdığı duruş nişan vermez)
var ready_flash := 0.0        # HUD: nişan yeni doldu (parıltı)
var fail_flash := 0.0         # HUD: basış reddedildi (sallanır)
## test sayaçları (tools/tests/sanat_testi.gd)
var stats := {"basla": {}, "isabet": {}, "hasar": {}, "red": {}, "kazanc": 0.0}
var log_on := false


func _init(owner: Player) -> void:
	p = owner


# ================================================================== veri, kilit, kayıt (statik)
static func data() -> Dictionary:
	if _data.is_empty():
		var f := FileAccess.open(DATA_PATH, FileAccess.READ)
		if f:
			var d: Variant = JSON.parse_string(f.get_as_text())
			if d is Dictionary:
				_data = d
	return _data


static func liste() -> Array:
	return data().get("sanatlar", [])


static func ids() -> Array:
	var out: Array = []
	for d in liste():
		out.append(String(d["id"]))
	return out


static func def_of(id: String) -> Dictionary:
	for d in liste():
		if String(d["id"]) == id:
			return d
	return {}


static func N(key: String, fallback := 0.0) -> float:
	return float(data().get("nisan", {}).get(key, fallback))


static func birim() -> float:
	return N("birim", 100.0)


static func renk(id: String) -> Color:
	var c: Array = def_of(id).get("renk", [1, 1, 1])
	return Color(float(c[0]), float(c[1]), float(c[2]))


static func acik_mi(id: String) -> bool:
	var d := def_of(id)
	if d.is_empty():
		return false
	return bool(d.get("varsayilan", false)) or id in Game.meta.get("sanat_acik", [])


static func ac(id: String) -> bool:
	## Kalıcı kilit açma (Sanat Tomarı ya da Alp Ata). true: yeni açıldı. İlk açılan sanat boşsa kuşanılır.
	if def_of(id).is_empty() or acik_mi(id):
		return false
	var a: Array = Game.meta.get("sanat_acik", [])
	a.append(id)
	Game.meta["sanat_acik"] = a
	Game.save_meta()
	return true


static func kilitli() -> Array:
	var out: Array = []
	for id in ids():
		if not acik_mi(id):
			out.append(id)
	return out


static func secili() -> String:
	var s := String(Game.meta.get("sanat_secili", ""))
	if s == "" or not acik_mi(s):
		for id in ids():
			if acik_mi(id):
				return id
	return s


static func sec(id: String) -> bool:
	if not acik_mi(id):
		return false
	Game.meta["sanat_secili"] = id
	Game.save_meta()
	return true


static func bedel(id: String) -> int:
	return int(def_of(id).get("bedel", 50))


static func ogret(id: String) -> bool:
	## Alp Ata öğretir: Kut bankasından bedel
	if acik_mi(id):
		return false
	var c := bedel(id)
	if int(Game.meta.get("kut_bank", 0)) < c:
		return false
	Game.meta["kut_bank"] = int(Game.meta["kut_bank"]) - c
	ac(id)
	return true


static func sinif_adi(s: String) -> String:
	return String(data().get("siniflar", {}).get(s, s))


static func siniflar_metni(id: String) -> String:
	var out: Array = []
	for s in def_of(id).get("sinif", []):
		out.append(sinif_adi(String(s)))
	return ", ".join(out)


static func yay_esya() -> Dictionary:
	## Yuvalardaki yay (Ok Yağmuru)
	if Game.run.is_empty():
		return {}
	for s in ["second", "melee"]:
		var it: Dictionary = Game.run["slots"].get(s, {})
		if it.get("kind", "") == "bow":
			return it
	return {}


static func yakin_esya() -> Dictionary:
	if Game.run.is_empty():
		return {}
	for s in ["melee", "second"]:
		var it: Dictionary = Game.run["slots"].get(s, {})
		if Player.is_melee_item(it):
			return it
	return {}


static func uygun(id: String, mel: Dictionary = {}) -> bool:
	## Sanat kuşanılan silahlarla kullanılabilir mi (sınıf kuralı)
	var d := def_of(id)
	if d.is_empty() or Game.run.is_empty():
		return false
	var sn: Array = d.get("sinif", [])
	if "yay" in sn:
		return not yay_esya().is_empty()
	var it := mel if not mel.is_empty() else yakin_esya()
	if it.is_empty():
		return false
	return Player._tempo_class(it) in sn


static func nisan() -> float:
	if Game.run.is_empty():
		return 0.0
	if not Game.run.has("nisan"):
		Game.run["nisan"] = N("baslangic", 2.0) * birim()
	return float(Game.run["nisan"])


static func nisan_max() -> float:
	return N("en_cok", 5.0) * birim()


static func bedel_nisan(id: String) -> float:
	return float(def_of(id).get("nisan", 1.0)) * birim()


# ================================================================== nişan kazancı
func kazan(v: float, neden := "") -> void:
	if v <= 0.0 or Game.run.is_empty():
		return
	var before := nisan()
	var after := minf(nisan_max(), before + v)
	Game.run["nisan"] = after
	stats["kazanc"] = float(stats["kazanc"]) + (after - before)
	var bu := birim()
	if floor(after / bu) > floor(before / bu):
		ready_flash = 1.0
		# yeni nişan: küçük parıltı + ses (sanat bu nişanla kullanılabilir olduysa daha belirgin)
		var id := secili()
		var hazir := after >= bedel_nisan(id) and before < bedel_nisan(id)
		if Ses.has("sanat_hazir"):
			Ses.play("sanat_hazir", -10.0 if not hazir else -5.0, 1.0 + 0.06 * floor(after / bu), 0.02, 0.08)
		if hazir and p and is_instance_valid(p):
			FX.burst(p.center() + Vector2(0, -6), renk(id), 6, 50, 0.4, 0.14, -60, true)
	if log_on and neden != "":
		print("[sanat] kazanc %s %.1f -> %.1f" % [neden, before, after])


func on_deal(e: Node, d: float, killed: bool, opts: Dictionary) -> void:
	## Player._deal: oyuncunun her vuruşu (sanat vuruşları ve süreğen hasar sayılmaz)
	if opts.has("sanat") or e == null or not is_instance_valid(e):
		return
	var mh := maxf(1.0, float(e.max_hp))
	var g := 0.0
	if e.is_boss:
		g = minf(N("boss_vurus_tavan", 6.0), N("boss_vurus_k", 160.0) * d / mh)
	else:
		g = minf(N("vurus_tavan", 10.0), N("vurus_k", 40.0) * d / mh)
	if opts.get("ok", false):
		g *= 0.6
	if killed and not e.is_boss:
		g += N("oldurme_seckin", 40.0) if e.elite else N("oldurme", 12.0)
	kazan(g)


func _watch_events() -> void:
	## Ustalık ödülleri: Player.v19_stats sayaçlarının artışı ve Kusursuz Kaçış
	var st: Dictionary = p.v19_stats
	if _ev.is_empty():
		_ev = st.duplicate()
	for k in [["carpisma", "carpisma"], ["karsi", "karsi_vurus"], ["infaz", "infaz"], ["kirilma", "kirilma"], ["muhur", "muhur"]]:
		var dn := int(st.get(k[0], 0)) - int(_ev.get(k[0], 0))
		if dn > 0 and k[0] == "kirilma" and Game.clock() - _art_hit_t < 0.2:
			continue   # sanatın kendi kırdığı duruş: kendini besleyen döngü olmasın
		if dn > 0:
			kazan(N(k[1], 10.0) * dn, k[0])
	_ev = st.duplicate()
	if p.perfect_t > _pd_prev + 0.5:
		kazan(N("kusursuz_kacis", 25.0), "kacis")
	_pd_prev = p.perfect_t


# ================================================================== ana döngü (Player._physics_process)
func tick(delta: float) -> bool:
	## true: sanat bu karede oyuncuyu yönetti (Player karenin geri kalanını atlar)
	cd = maxf(0.0, cd - delta)
	def_t -= delta
	_msg_t -= delta
	ready_flash = maxf(0.0, ready_flash - delta * 1.6)
	fail_flash = maxf(0.0, fail_flash - delta * 3.0)
	_watch_events()
	_rain_tick(delta)
	if def_t > 0.0 and Engine.get_physics_frames() % 6 == 0:
		FX.burst(p.center() + Vector2(randf_range(-8, 8), randf_range(-14, 10)), Color(1.0, 0.55, 0.45), 1, 16, 0.5, 0.12, -40, true)
	var pressed := Input.is_action_just_pressed("sanat")
	if cur.is_empty():
		if pressed:
			buf = 0.16
			if not _can_start(true):
				return false
		if buf > 0.0:
			buf -= delta
			if _can_start(false):
				buf = 0.0
				_start(secili())
				if not cur.is_empty():
					_step(0.0, false)
					return true
		return false
	# süren sanat: oyuncu başka bir şeye kesildiyse (hasar, kavranma, ölüm) bırak
	if p.dead or p.grabbed_by != null or p.atk.is_empty() or not p.atk.get("sanat", false) or not is_same(p.atk, cur.get("atk")):
		_end(true)
		return false
	_step(delta, pressed)
	return true


func _can_start(feedback: bool) -> bool:
	var id := secili()
	if id == "" or p.dead or p.grabbed_by != null or p.drink_t > 0.0 or p.wolf_t > 0.0 or p.don_on or p.mantle_t > 0.0:
		return false
	if p.roll_t > Player.ROLL_T * 0.5:
		return false
	if not p.atk.is_empty():
		var ph := String(p.atk.get("phase", ""))
		if p.atk.get("exec_t") != null or p.atk.get("c", {}).get("exec", false) or p.atk.get("c", {}).get("plunge", false):
			return false
		if not (ph in ["wind", "rec", "charge"] or p._hit_cancel_ok()):
			return false
	var msg := ""
	if not uygun(id):
		msg = "Bu silahla olmaz: %s" % siniflar_metni(id)
		stats["red"]["sinif"] = int(stats["red"].get("sinif", 0)) + 1
	elif cd > 0.0:
		msg = "%s hazırlanıyor (%.1f sn)" % [String(def_of(id)["ad"]), cd]
		stats["red"]["bekleme"] = int(stats["red"].get("bekleme", 0)) + 1
	elif nisan() < bedel_nisan(id) - 0.001:
		msg = "Alp Nişanı yetmez (%d gerekir)" % int(ceil(bedel_nisan(id) / birim()))
		stats["red"]["nisan"] = int(stats["red"].get("nisan", 0)) + 1
	if msg != "":
		if feedback:
			buf = 0.0
			fail_flash = 1.0
			if _msg_t <= 0.0:
				_msg_t = 0.6
				FX.text(p.center() + Vector2(0, -40), msg, Color(0.85, 0.82, 0.9), 7)
				Ses.play("ui_sec", -8.0, 0.7)
		return false
	return true


# ================================================================== sanat başlangıcı / bitişi
func _start(id: String) -> void:
	var d := def_of(id)
	var sn: Array = d.get("sinif", [])
	var it: Dictionary = yay_esya() if "yay" in sn else p.slot(p.mel_slot)
	if it.is_empty():
		it = yakin_esya()
	if it.is_empty():
		return
	# süren her şeyi bırak (saldırı, nişan, siper, şarj, yuvarlanmanın sonu)
	p._cancel_attack(false)
	p._end_trail()
	if p.aim_t >= 0.0:
		p.okc.melee_interrupt()
	p.aim_t = -1.0
	p.block_t = -1.0
	p.charge_t = -1.0
	if p.charge_fx and is_instance_valid(p.charge_fx):
		p.charge_fx.stop()
	p.charge_fx = null
	p.throw_t = -1.0
	p.roll_t = 0.0
	p._set_crouch(false)
	p.crouch_hold = false
	p.melee_buf = 0.0
	p.sprint = false
	p.last_step = -1
	var din := Input.get_axis("sol", "sag")
	if din != 0.0:
		p.facing = int(signf(din))
	p.anim.set_facing(p.facing)
	Game.run["nisan"] = maxf(0.0, nisan() - bedel_nisan(id))
	cd = float(d.get("bekleme", 4.0))
	_last_pose = []
	cur = {"id": id, "def": d, "item": it, "t": 0.0, "seg": "", "hit": {}, "hs": {}, "pal": int(d.get("pal", 0)),
		"col": renk(id), "fac": p.facing, "x0": p.global_position.x}
	var c := {"s": "spin", "mult": 1.0, "kb": 100.0, "last": true, "sanat": id}
	var a := {"step": 0, "c": c, "sw": {"body": "atk_horiz", "hit": [0.0, 1.5], "keys": []}, "phase": "wind", "t": 1.0, "dur": 1.0,
		"hit": [], "item": it, "hold": 0.0, "pause": false, "multi_i": 0, "ph": [0.1, 0.05, 0.1, 0.1, 0.0], "super_armor": true,
		"sanat": true}
	p.atk = a
	cur["atk"] = a
	stats["basla"][id] = int(stats["basla"].get(id, 0)) + 1
	# telegraf: fırça ensō'su + tamga, ad, ses, kısa parlama
	var col: Color = cur["col"]
	SanatFX.telegraf(p, id, col, int(cur["pal"]), p.facing)
	p._move_label(InkHUD.tr_upper(String(d["ad"])), col, 11)
	p.anim.set_flash(0.45)
	p.get_tree().create_timer(0.06).timeout.connect(func() -> void:
		if is_instance_valid(p):
			p.anim.set_flash(0.0))
	FX.flash_light(p.center(), col, 120.0, 1.3, 0.25)
	if Ses.has("sanat_baslat"):
		Ses.play("sanat_baslat", -4.0, 1.0, 0.03, 0.05, p.center())
	else:
		Ses.play("savur_hazirlik", -6.0, 0.8)
	p.vis_scale = Vector2(0.9, 1.08)
	if log_on:
		print("[sanat] basla %s nisan=%.0f cd=%.1f silah=%s" % [id, nisan(), cd, String(it.get("id", ""))])


func _end(interrupted := false) -> void:
	if cur.is_empty():
		return
	p._end_trail()
	if _kasirga_fx and is_instance_valid(_kasirga_fx):
		_kasirga_fx.alive = false
	_kasirga_fx = null
	_goge_birak()
	var kl: Variant = cur.get("kalkan")
	if is_instance_valid(kl) and kl is SanatFX:
		(kl as SanatFX).alive = false
	if not interrupted and is_same(p.atk, cur.get("atk")):
		p.atk = {}
	p.since_atk = 0.0
	p.last_step = -1
	p._last_pose_ok = false
	if log_on:
		print("[sanat] bitti %s t=%.2f kesildi=%s" % [String(cur["id"]), float(cur["t"]), str(interrupted)])
	cur = {}


# ================================================================== poz ve hareket yardımcıları
static func _ez(u: float, mode: int) -> float:
	match mode:
		1:
			return u * u
		2:
			return 1.0 - pow(1.0 - u, 3.0)
		3:
			return u
	return u * u * (3.0 - 2.0 * u)


static func _seq(keys: Array, tt: float) -> Array:
	## Poz dizisi: [[t sn, a1, a2, w, ext, phi°, r, roll°, ease], ...] -> [a1, a2, w, ext, phi, r, roll]
	var k0: Array = keys[0]
	if tt <= float(k0[0]):
		return k0.slice(1, 8)
	for i in range(keys.size() - 1):
		var a: Array = keys[i]
		var b: Array = keys[i + 1]
		if tt <= float(b[0]):
			var u := _ez(clampf((tt - float(a[0])) / maxf(0.0001, float(b[0]) - float(a[0])), 0.0, 1.0), int(b[8]))
			var out: Array = []
			for j in range(1, 8):
				out.append(lerpf(float(a[j]), float(b[j]), u))
			return out
	var e: Array = keys[keys.size() - 1]
	return e.slice(1, 8)


func _pose(pose: Array, body: String, bu: float, cs := "", behind := false) -> void:
	## Bu karenin kol pozu ve düzlemi: Player'ın atk sözlüğüne (önceki kare → bu kare) yazılır
	var a: Dictionary = cur["atk"]
	var prev: Array = _last_pose if not _last_pose.is_empty() else pose
	var sw: Dictionary = a["sw"]
	sw["body"] = body
	sw["keys"] = [[-1.0, prev[0], prev[1], prev[2], 1.0, prev[3], 0], [0.0, prev[0], prev[1], prev[2], 1.0, prev[3], 0],
		[1.0, pose[0], pose[1], pose[2], 1.0, pose[3], 0]]
	a["plane"] = {"p": [[0.0, prev[4], prev[5], prev[6]], [1.0, pose[4], pose[5], pose[6]]], "b": behind}
	if cs != "":
		a["c"]["s"] = cs
	_last_pose = pose
	if p.anim.has_anim(body):
		var n := p.anim.frame_count(body)
		p.anim.show_frame(body, clampi(int(bu * n), 0, n - 1))
	p.anim.set_facing(p.facing)


func _trail_on(fresh := false, life_k := 1.0, layered := 1, wk := 1.15) -> void:
	## Bu karenin bıçak izini örnekle (Player._sample_trail, önceki → bu kare); fresh: yeni bir hilal başlat
	if fresh:
		p._end_trail()
	var had: bool = p._trail != null and is_instance_valid(p._trail)
	p._trail_prev = [0.0]
	var a: Dictionary = cur["atk"]
	p._sample_trail(cur["item"], a["c"], 1.0)
	if not had and p._trail != null and is_instance_valid(p._trail) and p._trail is InkTrail:
		var tr := p._trail as InkTrail
		tr.pal = int(cur["pal"])
		tr.layered = maxi(tr.layered, layered)
		tr.life *= life_k
		tr.w_frac *= wk
		tr._apply_mat()


func _phase(ph: String) -> void:
	var a: Dictionary = cur["atk"]
	if String(a["phase"]) != ph:
		a["phase"] = ph
		if ph == "act":
			a["strike_at"] = Game.clock()


func _move(delta: float, gmul := 1.0, ctrl := 0.0, fric := 1400.0) -> void:
	var dir := Input.get_axis("sol", "sag")
	if ctrl > 0.0:
		p.velocity.x = move_toward(p.velocity.x, dir * Player.RUN * ctrl, 1200.0 * delta)
	elif p.is_on_floor():
		p.velocity.x = move_toward(p.velocity.x, 0.0, fric * delta)
	p.velocity.y = minf(p.velocity.y + Player.GRAV * gmul * delta, Player.MAX_FALL)
	p.move_and_slide()
	p._hazard_check(delta)
	p._update_weapon_visual()
	p._feel(delta, dir)
	p._look_ahead(delta)
	p._safety(delta)


func _move_raw(delta: float) -> void:
	## Yerçekimsiz / düşüş sınırsız hareket (Göğe Yükseliş: yükseliş, askı, dalış); hız doğrudan verilir
	p.move_and_slide()
	p._hazard_check(delta)
	p._update_weapon_visual()
	p._feel(delta, 0.0)
	p._look_ahead(delta)
	p._safety(delta)


func _R() -> float:
	return p._reach(cur["item"])


func _box(x0: float, y0: float, x1: float, y1: float) -> Rect2:
	## Öne göre kutu (x ileri +), oyuncunun ayağına göre
	var f := float(p.facing)
	var a := p.global_position.x + (x0 if f > 0 else -x1)
	var b := p.global_position.x + (x1 if f > 0 else -x0)
	return Rect2(a, p.global_position.y + y0, b - a, y1 - y0)


func _in_box(box: Rect2, key: String) -> Array:
	## Kutudaki, bu geçişte (key) henüz vurulmamış düşmanlar
	var h: Dictionary = cur["hit"]
	if not h.has(key):
		h[key] = []
	var done: Array = h[key]
	var out: Array = []
	for e in p.get_tree().get_nodes_in_group("dusman"):
		if not is_instance_valid(e) or e.dead or done.has(e):
			continue
		if box.intersects(e.hurt_rect()):
			done.append(e)
			out.append(e)
	return out


func _vur(e: Node, mult: float, key: String, extra: Dictionary = {}, kind := "cut") -> bool:
	## Sanat vuruşu: Player._deal (tomar, kritik, unsur, durum etkileri aynen) + efekt, ses, duraklama. Dönen: öldü mü
	var d: Dictionary = cur["def"]
	var it: Dictionary = cur["item"]
	var boss: bool = e.is_boss
	var m := mult * (float(d.get("boss_k", 0.7)) if boss else 1.0)
	var dirx := signf(e.center().x - p.global_position.x)
	if dirx == 0.0:
		dirx = float(p.facing)
	var o := {"kb": 120.0, "dir": dirx, "poise": float(d.get("durus", 1.5)) * (0.6 if boss else 1.0), "sanat": String(cur["id"]),
		"last": true, "sfx_done": true, "feel_done": true, "step": 0, "behind": "facing" in e and int(e.facing) == int(dirx)}
	o.merge(extra, true)
	var hp: Vector2 = e.hurt_rect().get_center()
	var hp0 := float(e.hp)
	_art_hit_t = Game.clock()
	FX.hit_k = 1.0
	FX.in_hit = true
	p._deal(e, float(it.get("dmg", 10.0)) * m, it, o)
	FX.in_hit = false
	var killed: bool = not is_instance_valid(e) or e.dead
	var dealt := hp0 - (float(e.hp) if is_instance_valid(e) else 0.0)
	var id := String(cur["id"])
	stats["isabet"][id] = int(stats["isabet"].get(id, 0)) + 1
	stats["hasar"][id] = float(stats["hasar"].get(id, 0.0)) + maxf(0.0, dealt)
	if is_instance_valid(e):
		p.combo_add(e)
	var crit: bool = o.get("crit_done", false)
	var col: Color = cur["col"]
	var hdir := Vector2(dirx, -0.25)
	# efekt: mürekkep sıçrantısı sanatın paletinde (büyük kademe), kritikte damga
	var tier := int(extra.get("tier", 2))
	InkFX.hit(kind, hp, hdir, int(cur["pal"]), tier, float(extra.get("fx", 1.15)))
	if crit:
		InkFX.stamp(hp, int(cur["pal"]))
	SanatFX.vurus_leke(hp, hdir, int(cur["pal"]), tier)
	FX.sparks(hp, hdir, col.lightened(0.3), 6 if tier >= 2 else 2, 220.0)
	if crit:
		p._crit_accent(it, hp, col)
	# duraklama ve kamera: geçişin ilk isabeti tam, sonrakiler küçük ek
	var hs: Dictionary = cur["hs"]
	var first := not hs.has(key)
	hs[key] = true
	var base_hs := float(extra.get("hs", 0.07))
	if first:
		Game.hitstop(base_hs + (0.02 if crit else 0.0) + (0.02 if killed else 0.0))
		Game.kick(Vector2(dirx, -0.1), 4.0)
		Game.shake_dir(float(extra.get("sh", 0.3)), Vector2(dirx, 0.3))
		if Ses.has_method("hit"):
			Ses.call("hit", 2 if crit else 1, hp, "kunt" if kind == "blunt" else "")
	else:
		Game.hitstop(0.012)
	if killed:
		Game.rumble(0.35, 0.2, 0.1)
	if log_on:
		print("[sanat] vurus %s %s hasar=%.1f krit=%s oldu=%s" % [id, String(e.kind), dealt, str(crit), str(killed)])
	return killed


func _ses(n: String, vol := -4.0, pitch := 1.0, fallback := "") -> void:
	if Ses.has(n):
		Ses.play(n, vol, pitch, 0.04, 0.03, p.center())
	elif fallback != "":
		Ses.play(fallback, vol, pitch, 0.06, 0.03, p.center())


# ================================================================== sanat adımı
func _step(delta: float, pressed: bool) -> void:
	cur["t"] = float(cur["t"]) + delta
	match String(cur["id"]):
		"kasirga":
			_kasirga(delta, pressed)
		"bir_cekis":
			_bir_cekis(delta)
		"ay_hilali":
			_ay_hilali(delta)
		"goge_yukselis":
			_goge(delta)
		"bozkurt_atilisi":
			_bozkurt(delta)
		"kam_darbesi":
			_kam(delta)
		"ok_yagmuru":
			_ok_yagmuru(delta)
		"demir_durus":
			_demir(delta, pressed)
		_:
			_end()


# ------------------------------------------------------------------ Kasırga Kesişi
const KAS_WIND := 0.18
const KAS_TUR := 0.3
const KAS_REC := 0.22


func _kasirga(delta: float, pressed: bool) -> void:
	var t := float(cur["t"])
	var d: Dictionary = cur["def"]
	if not cur.has("turs"):
		cur["turs"] = 1
		cur["ek"] = 0
	# ek tur: dönerken T (her tur daha pahalı, en çok 3)
	if pressed and t > KAS_WIND:
		var ek := int(cur["ek"])
		var ekl: Array = d.get("ek_tur", [0.5, 1.0, 1.5])
		if ek < ekl.size():
			var c := float(ekl[ek]) * birim()
			if nisan() >= c - 0.001:
				Game.run["nisan"] = nisan() - c
				cur["ek"] = ek + 1
				cur["turs"] = int(cur["turs"]) + 1
				_ses("sanat_kasirga", -6.0, 1.08 + 0.06 * ek, "savur_ruh")
				FX.text(p.center() + Vector2(0, -50), "+1 TUR", cur["col"], 8)
				fail_flash = 0.0
			else:
				fail_flash = 1.0
				FX.text(p.center() + Vector2(0, -50), "nişan yetmez", Color(0.8, 0.8, 0.9), 7)
	var turs := int(cur["turs"])
	var spin_end := KAS_WIND + KAS_TUR * turs
	var two_h := Player.TWO_HANDED.has(String(cur["item"].get("id", "")))
	var body := "atk_spin_2h" if two_h else "atk_spin"
	var R := _R()
	if t < KAS_WIND:
		_phase("wind")
		var u := t / KAS_WIND
		var pose := _seq([[0.0, 0.6, 0.9, 0.3, 1.0, 90.0, 1.0, 0.0, 0], [KAS_WIND, -1.15, 0.55, 0.25, 0.95, 90.0, 0.32, 0.0, 2]], t)
		_pose(pose, body, u * 0.2, "spin", false)
		p.vis_scale = Vector2(1.0 + 0.06 * u, 1.0 - 0.07 * u)
		_move(delta, 1.0, 0.0)
		return
	if t < spin_end:
		_phase("act")
		if _kasirga_fx == null or not is_instance_valid(_kasirga_fx):
			_kasirga_fx = SanatFX.spawn("kasirga", p.global_position + Vector2(0, -24), cur["col"], 9.0, int(cur["pal"]))
			if _kasirga_fx:
				_kasirga_fx.follow = p
				_kasirga_fx.data = {"rx": R + 18.0, "ry": 12.0, "spd": TAU / KAS_TUR * 1.05}
			_ses("sanat_kasirga", -4.0, 1.0, "savur_ruh")
		var st := t - KAS_WIND
		var tur := int(st / KAS_TUR)
		var u := fmod(st, KAS_TUR) / KAS_TUR
		var total := st / KAS_TUR
		var a1 := -1.15 + 0.85 * clampf(st / 0.06, 0.0, 1.0) + TAU * total
		var phi := 90.0 + (6.0 if tur % 2 == 0 else -6.0) * sin(u * PI)
		var pose := [a1, 0.05, 0.0, 1.14, phi, 0.36, 0.0]
		_pose(pose, body, fmod(u * 1.0, 1.0), "spin", true)
		var half := int(st / (KAS_TUR * 0.5))
		_trail_on(half != int(cur.get("half", -1)), 1.5, 1, 0.95)
		if half != int(cur.get("half", -1)):
			cur["half"] = half
			if half > 0 and half % 2 == 0:
				_ses("savur_" + String(Player.WSND.get(String(cur["item"].get("id", "")), "kilic")), -9.0, 1.1 + 0.05 * tur)
		var last_half := half >= turs * 2 - 1
		var key := "h%d" % half
		var box := Rect2(p.global_position.x - R - 20.0, p.global_position.y - 66.0, (R + 20.0) * 2.0, 70.0)
		# girdap: çevredeki hafif düşmanlar içeri çekilir
		for e in p.get_tree().get_nodes_in_group("dusman"):
			if is_instance_valid(e) and not e.dead and not e.heavy and not e.is_boss and not e.flying:
				var dx: float = e.center().x - p.global_position.x
				if absf(dx) < R + 70.0 and absf(e.center().y - p.center().y) < 60.0 and absf(dx) > 10.0:
					e.velocity.x = move_toward(e.velocity.x, -signf(dx) * 150.0, 900.0 * delta)
		for e in _in_box(box, key):
			if last_half:
				_vur(e, float(d.get("son_hasar", 1.15)), key, {"kb": 260.0, "launch": 120.0, "stagger": true, "hs": 0.08, "sh": 0.45})
			else:
				_vur(e, float(d.get("hasar", 0.7)), key, {"kb": 40.0, "hs": 0.035, "sh": 0.15, "tier": 1, "fx": 0.7})
		p.vis_scale = Vector2(1.04, 0.97)
		if Engine.get_physics_frames() % 3 == 0:
			FX.dust(p.global_position, Vector2(-p.facing, -0.3), 2, 0.26)
		_move(delta, 0.55, 0.45)
		return
	if t < spin_end + KAS_REC:
		if String(cur["atk"]["phase"]) != "rec":
			_phase("rec")
			p._end_trail()
			if _kasirga_fx and is_instance_valid(_kasirga_fx):
				_kasirga_fx.alive = false
			InkFX.ring(p.center(), R + 26.0, int(cur["pal"]), 0.3, 0.35)
			SanatFX.kasirga_son(p.global_position + Vector2(0, -24), R, int(cur["pal"]))
			cur["rec_from"] = _last_pose.duplicate()
		var u2 := (t - spin_end) / KAS_REC
		var rf: Array = cur["rec_from"]
		var a1e := float(rf[0])
		var a1r := 0.6 + TAU * floorf(a1e / TAU)
		var pose := _seq([[0.0, a1e, rf[1], rf[2], rf[3], rf[4], rf[5], rf[6], 0], [1.0, a1r + (TAU if a1r < a1e - 0.3 else 0.0), 0.9, 0.3, 1.0, 90.0, 1.0, 0.0, 2]], u2)
		_pose(pose, body, 0.85 + 0.15 * u2, "spin", u2 < 0.5)
		_move(delta, 1.0, 0.0)
		return
	_end()


# ------------------------------------------------------------------ Bir Çekiş
const BC_WIND := 0.42
const BC_HIT := 0.5


func _bir_cekis(delta: float) -> void:
	var t := float(cur["t"])
	var d: Dictionary = cur["def"]
	var keys := [
		[0.0, 0.6, 0.9, 0.3, 1.0, 34.0, 1.0, 0.0, 0],
		[0.3, 3.35, 0.25, 0.3, 1.0, 30.0, 0.6, 0.0, 2],
		[BC_WIND, 3.6, 0.32, 0.38, 0.97, 30.0, 0.6, 0.0, 0],
		[BC_HIT, 0.95, 0.0, 0.0, 1.28, 27.0, 0.6, 0.0, 1],
		[0.58, 0.32, 0.0, -0.16, 1.12, 24.0, 0.64, 18.0, 2],
		[0.78, 0.36, 0.08, -0.1, 1.08, 24.0, 0.64, 18.0, 0],
		[1.0, 0.6, 0.6, 0.2, 1.0, 34.0, 1.0, 0.0, 0]]
	var pose := _seq(keys, t)
	var bu := clampf(t / 0.9, 0.0, 1.0)
	_pose(pose, "atk_overhead_2h", bu, "overhead_2h", false)
	if t < BC_WIND:
		_phase("wind")
		var u := t / BC_WIND
		p.vis_scale = Vector2(1.0 - 0.05 * u, 1.0 + 0.05 * u)
		if t > 0.3 and not cur.has("glint"):
			cur["glint"] = true
			var tip := p.arm_root.to_global(p._hand_local + p._blade_local * _R())
			var g := SanatFX.spawn("parilti", tip, cur["col"], 0.22)
			if g:
				g.data = {"s": 14.0}
			SanatFX.cekis_topla(tip, int(cur["pal"]))
			_ses("sanat_hazir", -6.0, 0.7, "sarj_dolu")
		if t > 0.3:
			p.vis_scale += Vector2(randf_range(-0.01, 0.01), randf_range(-0.01, 0.01))
		_move(delta, 1.0, 0.0)
		return
	if t < 0.62:
		_phase("act")
		_trail_on(not cur.has("tr"), 1.8, 2)
		cur["tr"] = true
		if t >= BC_HIT - 0.02 and not cur.has("hit_done"):
			cur["hit_done"] = true
			_bir_cekis_vur(d)
		_move(delta, 1.0, 0.0)
		return
	if t < 1.0:
		if String(cur["atk"]["phase"]) != "rec":
			_phase("rec")
			p._end_trail()
		_move(delta, 1.0, 0.0)
		return
	_end()


func _bir_cekis_vur(d: Dictionary) -> void:
	var R := _R()
	var box := _box(-8.0, -76.0, R + 28.0, 6.0)
	var gx := p.global_position.x + p.facing * (R * 0.8 + 6.0)
	var gp := Vector2(gx, p.global_position.y)
	var hits := _in_box(box, "iner")
	var targets: Array = [p]
	for e in hits:
		targets.append(e)
		_kalkan_dusur(e)
		var killed := _vur(e, float(d.get("hasar", 3.2)), "iner", {"kb": 300.0, "heavy": true, "stagger": true, "hs": 0.11, "sh": 0.7}, "blunt")
		if not killed and is_instance_valid(e) and not e.is_boss and e.has_method("_guard_break"):
			e._guard_break(signf(e.center().x - p.global_position.x))
	# yer: mürekkep yarığı, toz, şok çizgisi; vurmasa da olay
	FX.ground_slam(gp, p.facing, 1.7, cur["col"].lerp(Color(1.0, 0.85, 0.6), 0.4))
	InkFX.slam(gp, p.facing, 1.15, int(cur["pal"]))
	SanatFX.cekis_inis(gp, p.facing, int(cur["pal"]), 78.0, 86.0)
	Game.shake_dir(0.6, Vector2(0, 1))
	Game.zoom_punch(0.05)
	Game.slowmo(0.4, 0.12)
	if not hits.is_empty():
		ImpactFrame.play(targets, 1.0, 2)
	_ses("sanat_cekis", -2.0, 1.0, "sarsinti_buyuk")
	# Demir Gönül: alınan hasar azalır
	def_t = float(d.get("savunma_sn", 3.0))
	def_k = float(d.get("savunma", 0.35))
	FX.text(p.center() + Vector2(0, -56), "DEMİR GÖNÜL", Color(1.0, 0.6, 0.5), 8)
	FX.ring(p.center(), 34, Color(1.0, 0.55, 0.45), 0.35)


func _kalkan_dusur(e: Node) -> void:
	## Kalkanlı / hücumcu yaratığın kalkanı düşer (sanatın ağır darbesi kalkanı aşar)
	if e.is_boss or not ("guard_hp" in e) or int(e.guard_hp) <= 0:
		return
	if String(e.ai) in ["shield", "charger"]:
		e.guard_hp = 0
		e.state = "stagger"
		e.st = 1.4
		FX.text(e.center() + Vector2(0, -float(e.size.y) - 8.0), "KALKAN DÜŞTÜ!", Color(1.0, 0.85, 0.4), 8)
		FX.anim("resonant_break", e.center(), 0.0, 0.9, Color(1.0, 0.85, 0.5))
		Ses.play("darbe_metal", -2.0, 0.9)


# ------------------------------------------------------------------ Ay Hilali
func _ay_hilali(delta: float) -> void:
	var t := float(cur["t"])
	var d: Dictionary = cur["def"]
	var keys := [
		[0.0, 0.6, 0.9, 0.3, 1.0, 100.0, 1.0, 0.0, 0],
		[0.16, 0.4, 1.65, -1.4, 1.0, 100.0, 0.34, 0.0, 2],
		[0.22, 0.36, 1.7, -1.45, 0.92, 100.0, 0.32, 0.0, 0],
		[0.27, 1.75, 0.0, 0.0, 1.28, 98.0, 0.3, 0.0, 1],
		[0.34, 2.15, 0.0, 0.18, 1.12, 106.0, 0.36, 38.0, 2],
		[0.5, 2.0, 0.12, 0.16, 1.08, 106.0, 0.38, 38.0, 0],
		[0.72, 0.6, 0.9, 0.3, 1.0, 100.0, 1.0, 0.0, 0]]
	_pose(_seq(keys, t), "atk_horiz", clampf(t / 0.6, 0.0, 1.0), "iai", false)
	if t < 0.22:
		_phase("wind")
		if not cur.has("glint") and t > 0.1:
			cur["glint"] = true
			var g := SanatFX.spawn("parilti", p.arm_root.to_global(p._hand_local + p._blade_local * _R() * 0.6), cur["col"], 0.2)
			if g:
				g.data = {"s": 10.0}
		_move(delta, 1.0, 0.0)
		return
	if t < 0.4:
		_phase("act")
		_trail_on(not cur.has("tr"), 1.7, 2)
		cur["tr"] = true
		if t >= 0.26 and not cur.has("atis"):
			cur["atis"] = true
			var h := SanatFX.spawn("hilal", p.center() + Vector2(p.facing * 16.0, -4.0), cur["col"], 3.0, int(cur["pal"]))
			SanatFX.ay_cekis(p.center(), p.facing, int(cur["pal"]))
			if h:
				h.facing = p.facing
				h.vel = Vector2(p.facing * float(d.get("hiz", 330.0)), 0.0)
				h.data = {"menzil": float(d.get("menzil", 300.0)), "max": 6, "pal": int(cur["pal"])}
				var it: Dictionary = cur["item"]
				var dd := d
				var self_ref := self
				h.vurus_cb = func(e: Node, _hp: Vector2) -> void:
					self_ref._uzak_vur(e, it, dd, "hilal", float(dd.get("hasar", 1.6)), {"kb": 160.0, "dir": float(h.facing)})
			_ses("sanat_hilal", -3.0, 1.0, "savur_ruh")
			Game.kick(Vector2(p.facing, 0), 3.0)
			p.velocity.x = -p.facing * 60.0
		_move(delta, 1.0, 0.0)
		return
	if t < 0.72:
		if String(cur["atk"]["phase"]) != "rec":
			_phase("rec")
			p._end_trail()
		_move(delta, 1.0, 0.0)
		return
	_end()


func _uzak_vur(e: Node, it: Dictionary, d: Dictionary, key: String, mult: float, extra: Dictionary) -> void:
	## Sanatın kendisi bitmiş olabilir (hilal, ok yağmuru): kendi vuruşu (cur'dan bağımsız)
	if not is_instance_valid(e) or e.dead or not is_instance_valid(p):
		return
	var boss: bool = e.is_boss
	var m := mult * (float(d.get("boss_k", 0.7)) if boss else 1.0)
	var o := {"kb": 100.0, "poise": float(d.get("durus", 1.0)) * (0.6 if boss else 1.0), "sanat": String(d["id"]), "sfx_done": true,
		"feel_done": true, "last": true}
	o.merge(extra, true)
	var hp0 := float(e.hp)
	var hp: Vector2 = e.hurt_rect().get_center()
	_art_hit_t = Game.clock()
	FX.hit_k = 1.0
	FX.in_hit = true
	p._deal(e, float(it.get("dmg", 10.0)) * m, it, o)
	FX.in_hit = false
	var id := String(d["id"])
	stats["isabet"][id] = int(stats["isabet"].get(id, 0)) + 1
	stats["hasar"][id] = float(stats["hasar"].get(id, 0.0)) + maxf(0.0, hp0 - (float(e.hp) if is_instance_valid(e) else 0.0))
	var crit: bool = o.get("crit_done", false)
	var dir := Vector2(float(o.get("dir", p.facing)), -0.2)
	InkFX.hit("magic" if key == "hilal" else "pierce", hp, dir, int(d.get("pal", 7)), 1 if key != "hilal" else 2, 1.0)
	if crit:
		InkFX.stamp(hp, int(d.get("pal", 7)))
	if Ses.has_method("hit"):
		Ses.call("hit", 2 if crit else (1 if key == "hilal" else 0), hp, "")
	if key == "hilal":
		Game.hitstop(0.035)
		Game.shake_dir(0.18, dir)
	if log_on:
		print("[sanat] vurus %s %s hasar=%.1f krit=%s" % [id, String(e.kind), hp0 - (float(e.hp) if is_instance_valid(e) else 0.0), str(crit)])


# ------------------------------------------------------------------ Göğe Yükseliş (v28: kaldırıcı sanat)
## Yükselen kesik vurulan SIRADAN düşmanları (seçkin, boss, ağır değil: onlar yalnız hasar + duruş alır) oyuncuyla
## birlikte göğe kaldırır; tepede düşmanlar havada KİLİTLİ (Enemy.sanat_tut: yerçekimi ve yapay zekâ yok, küçük
## salınım) oyuncu üç kesiklik hava kombosu yapar (her kesikte düşmanlar sarsılır), sonra aşağı bitiriş: düşmanlar
## oyuncunun önünde yere çakılır, "GÜM!", şok dalgası, yarık, ek hasar ve çevreye küçük alan hasarı.
## Kaldırma yüksekliği tavana göre kısalır (oyuncu ve her düşmanın sütunu taranır); hareket move_and_slide ile
## (duvara / tavana girilmez). v22: dizinin tamamı tek T basışının parçası (açık sanat).
const GY_WIND := 0.14
const GY_RISE := 0.24
const GY_PASS := [0.0, 0.15, 0.3]
const GY_TEPE := 0.47
const GY_DWIND := 0.09
const GY_REC := 0.32


static func kaldirilir(e: Node) -> bool:
	## Göğe Yükseliş'in kaldırabildiği düşman: sıradan (seçkin, boss, ağır / zırhlı değil)
	return e != null and is_instance_valid(e) and not e.dead and not e.is_boss and not e.elite and not e.heavy


func _tavan(x: float, y_top: float, maxh: float) -> float:
	## x sütununda y_top'tan yukarı boş yükseklik (px, en çok maxh); tek yönlü platformlar engel sayılmaz
	var lv: Node = p.level
	if lv == null or not lv.has_method("solid_at"):
		return maxh
	var h := 0.0
	while h < maxh:
		if lv.solid_at(Vector2(x, y_top - h - 2.0)):
			return h
		h += 3.0
	return maxh


func _goge_kilit(delta: float, hover: bool) -> void:
	## Kilitli düşmanlar: oyuncunun önünde dizili ayak hedefi (+ salınım + sarsılma), kilit tazelenir
	var ks: Array = cur.get("kilit", [])
	var xo: Array = cur.get("xo", [])
	var jolt: Array = cur.get("jolt", [])
	var T := float(cur["t"])
	for i in ks.size():
		var e: Node = ks[i]
		if not is_instance_valid(e) or e.dead:
			continue
		var j: Vector2 = jolt[i]
		jolt[i] = j * exp(-14.0 * delta)
		var tgt := p.global_position + Vector2(p.facing * float(xo[i]), -3.0 * float(i % 2))
		if hover:
			tgt.y += sin(T * 8.0 + float(i) * 1.9) * 2.5
		e.sanat_hedef = tgt + j
		e.sanat_tut = 0.25
		e.facing = -p.facing


func _goge(delta: float) -> void:
	var t := float(cur["t"])
	var d: Dictionary = cur["def"]
	var R := _R()
	var seg := String(cur.get("seg", ""))
	if seg == "":
		seg = "wind"
		cur["seg"] = seg
		cur["t0"] = 0.0
		cur["kilit"] = []
		cur["xo"] = []
		cur["jolt"] = []
		cur["y0"] = p.global_position.y
		# oyuncunun tepesindeki boşluk: kaldırma yüksekliği tavana göre kısalır
		var kmax := float(d.get("kaldirma", 112.0))
		cur["H"] = clampf(_tavan(p.global_position.x, p.global_position.y - 40.0, kmax + 8.0) - 8.0, 0.0, kmax)
		stats["goge"] = {"kaldirilan": 0, "seckin": 0, "carpilan": 0, "kilit_kare": 0, "H": float(cur["H"])}
	var st := t - float(cur["t0"])
	var pal := int(cur["pal"])
	match seg:
		"wind":
			_phase("wind")
			var pose := _seq([[0.0, 0.6, 0.9, 0.3, 1.0, 138.0, 1.0, 0.0, 0], [GY_WIND, -0.3, -0.35, -0.65, 1.0, 138.0, 0.5, 0.0, 2]], st)
			_pose(pose, "atk_uppercut", st / GY_WIND * 0.3, "rise")
			p.vis_scale = Vector2(1.0 + 0.1 * st / GY_WIND, 1.0 - 0.12 * st / GY_WIND)
			if not cur.has("toz"):
				cur["toz"] = true
				SanatFX.goge_toplan(p.global_position, p.facing, pal)
			_move(delta, 1.0, 0.0)
			if st >= GY_WIND:
				_goge_seg("rise")
		"rise":
			_phase("act")
			var pose := _seq([[0.0, -0.3, -0.35, -0.65, 1.0, 138.0, 0.5, 0.0, 0], [0.09, 2.45, 0.0, 0.2, 1.18, 136.0, 0.5, 0.0, 1],
				[GY_RISE, 3.05, 0.05, 0.1, 1.08, 146.0, 0.54, -30.0, 2]], st)
			_pose(pose, "atk_uppercut", 0.3 + 0.7 * clampf(st / GY_RISE, 0.0, 1.0), "rise")
			_trail_on(not cur.has("tr1"), 1.6, 2)
			cur["tr1"] = true
			if not cur.has("hop"):
				cur["hop"] = true
				p.air_hang = 0.0
				FX.dust(p.global_position, Vector2.UP, 8, 0.32)
				_ses("sanat_yuksel", -3.0, 1.0, "sicrayis")
				SanatFX.goge_yuksel(p.global_position, float(cur["H"]) + 50.0, p.facing, pal)
			# yükselen kesik: kutudaki herkes vurulur; sıradanlar kilitlenip birlikte kalkar
			var box := _box(-10.0, -78.0, R + 16.0, 6.0)
			for e in _in_box(box, "rise"):
				var hp0 := float(e.hp)
				var lift := kaldirilir(e)
				_vur(e, float(d.get("hasar", 1.2)), "rise", {"kb": 20.0 if lift else 60.0, "stun": 0.6 if not lift else 0.0, "hs": 0.06})
				var landed: bool = is_instance_valid(e) and not e.dead and float(e.hp) < hp0
				if lift and landed:
					_goge_yakala(e)
				elif is_instance_valid(e) and not e.dead and not lift:
					stats["goge"]["seckin"] = int(stats["goge"]["seckin"]) + 1
					FX.text(e.center() + Vector2(0, -float(e.size.y) * 0.5 - 12.0), "kalkmaz", Color(0.9, 0.85, 0.7), 7)
			# yükseliş: hedef yüksekliğe yumuşak (tavan payı _goge_yakala'da da kısalır)
			var H := float(cur["H"])
			var u := clampf(st / GY_RISE, 0.0, 1.0)
			var ty := float(cur["y0"]) - H * (1.0 - pow(1.0 - u, 2.4))
			p.velocity = Vector2(p.facing * 30.0, clampf((ty - p.global_position.y) / maxf(delta, 0.001), -1400.0, 600.0))
			_goge_kilit(delta, false)
			_move_raw(delta)
			if st >= GY_RISE:
				_goge_seg("tepe")
		"tepe":
			# tepede askı: üç kesiklik hava kombosu, kilitli düşmanlar her kesikte sarsılır
			_phase("act")
			var keys := [[0.0, 3.05, 0.05, 0.1, 1.08, 60.0, 0.45, 0.0, 0], [0.07, 0.85, 0.0, 0.0, 1.25, 60.0, 0.45, 0.0, 1],
				[0.12, 0.3, 0.2, 0.05, 1.05, 64.0, 0.48, 25.0, 2], [0.15, 0.1, 0.3, -0.4, 1.0, 120.0, 0.45, 0.0, 0],
				[0.22, 2.6, 0.0, 0.1, 1.25, 120.0, 0.45, 0.0, 1], [0.27, 3.1, 0.05, 0.15, 1.1, 126.0, 0.48, -25.0, 2],
				[0.3, 3.1, 0.05, 0.15, 1.1, 100.0, 0.34, 0.0, 0], [0.34, 0.4, 1.65, -1.4, 0.95, 100.0, 0.34, 0.0, 2],
				[0.39, 1.75, 0.0, 0.0, 1.3, 98.0, 0.3, 0.0, 1], [GY_TEPE, 2.3, 0.0, 0.18, 1.12, 106.0, 0.36, 38.0, 2]]
			var pass_i := 0
			for k in GY_PASS.size():
				if st >= float(GY_PASS[k]):
					pass_i = k
			var body := "atk_up" if pass_i == 1 else "atk_horiz"
			var p0 := float(GY_PASS[pass_i])
			var p1 := float(GY_PASS[pass_i + 1]) if pass_i + 1 < GY_PASS.size() else GY_TEPE
			_pose(_seq(keys, st), body, clampf((st - p0) / (p1 - p0), 0.0, 1.0), "cross_x" if pass_i < 2 else "iai", pass_i == 2 and st - p0 < 0.05)
			var fresh := pass_i != int(cur.get("pass", -1))
			if fresh:
				cur["pass"] = pass_i
				_trail_on(true, 1.5, 2 if pass_i == 2 else 1)
				_ses("savur_" + String(Player.WSND.get(String(cur["item"].get("id", "")), "kilic")), -5.0, 1.12 + 0.1 * pass_i)
				SanatFX.goge_kesik(p.center() + Vector2(p.facing * (R * 0.55 + 14.0), -4.0), p.facing, pass_i, pal, R + 20.0)
			else:
				_trail_on(false)
			# askı: oyuncu ve düşmanlar havada
			p.velocity = Vector2(0.0, (float(cur["y0"]) - float(cur["H"]) + sin(t * 7.0) * 1.5 - p.global_position.y) * 10.0)
			_goge_kilit(delta, true)
			stats["goge"]["kilit_kare"] = int(stats["goge"]["kilit_kare"]) + 1
			# kesik isabeti: kesiğin vuruş anında kilitliler kesin, kutudakiler (uçanlar vb.) de
			var hit_at := p0 + (0.05 if pass_i < 2 else 0.08)
			if st >= hit_at and not cur.has("tepe_vur%d" % pass_i):
				cur["tepe_vur%d" % pass_i] = true
				var key := "tepe%d" % pass_i
				var ks: Array = cur["kilit"]
				var jolt: Array = cur["jolt"]
				var targets: Array = []
				for i in ks.size():
					var e: Node = ks[i]
					if is_instance_valid(e) and not e.dead:
						targets.append(e)
						jolt[i] = Vector2(p.facing * (9.0 + 3.0 * pass_i), [-6.0, 7.0, -3.0][pass_i])
						e._tumble += [0.35, -0.45, 0.3][pass_i] * float(p.facing)
				for e in _in_box(_box(-14.0, -70.0, R + 22.0, 20.0), key):
					if not targets.has(e):
						targets.append(e)
				for e in targets:
					if is_instance_valid(e) and not e.dead:
						_vur(e, float(d.get("tepe_hasar", 0.6)), key, {"kb": 0.0 if ks.has(e) else 40.0, "hs": 0.055 if pass_i < 2 else 0.07,
							"tier": 1 if pass_i < 2 else 2, "fx": 0.85, "sh": 0.25})
			_move_raw(delta)
			if st >= GY_TEPE:
				_goge_seg("dalis")
		"dalis":
			_phase("act")
			var pose := _seq([[0.0, 2.3, 0.0, 0.18, 1.12, 30.0, 0.6, 0.0, 0], [GY_DWIND, 3.4, 0.2, 0.3, 0.95, 28.0, 0.6, 0.0, 2],
				[GY_DWIND + 0.07, 0.4, 0.0, -0.2, 1.2, 26.0, 0.62, 0.0, 1]], st)
			_pose(pose, "atk_slam_jump", 0.5 + 0.25 * clampf(st / (GY_DWIND + 0.07), 0.0, 1.0), "slam_2h")
			if st < GY_DWIND:
				# kısa kalkış: silah baş üstünde, düşmanlar hâlâ askıda
				p.velocity = Vector2(0.0, -40.0)
				_goge_kilit(delta, true)
			else:
				if not cur.has("dus"):
					cur["dus"] = true
					_trail_on(true, 1.4, 2)
					_ses("sanat_yuksel", -6.0, 0.7, "sicrayis")
					Game.kick(Vector2(0, 1), 4.0)
					SanatFX.goge_dalis(p.global_position, p.facing, pal)
					for e in cur["kilit"]:
						if is_instance_valid(e) and not e.dead:
							e.sanat_dus = true
							e.sanat_indi = false
				else:
					_trail_on(false)
				p.velocity = Vector2(p.facing * 20.0, 980.0)
				# düşen düşmanlar oyuncunun önünde (x) çakılır
				var ks: Array = cur["kilit"]
				var xo: Array = cur["xo"]
				for i in ks.size():
					var e: Node = ks[i]
					if is_instance_valid(e) and not e.dead and e.sanat_dus:
						e.sanat_hedef = Vector2(p.global_position.x + p.facing * float(xo[i]), e.global_position.y)
						e.sanat_tut = maxf(float(e.sanat_tut), 0.3)
				if Engine.get_physics_frames() % 2 == 0:
					FX.ghost(p.anim.base, Color(cur["col"], 0.5), 0.2)
				for e in _in_box(_box(-10.0, -50.0, R + 6.0, 10.0), "dalis_yol"):
					if not (cur["kilit"] as Array).has(e):
						_vur(e, 0.6, "dalis_yol", {"kb": 60.0, "hs": 0.03, "tier": 1, "fx": 0.8})
			_move_raw(delta)
			if (st >= GY_DWIND and p.is_on_floor()) or st > 1.0:
				_goge_inis(d)
				_goge_seg("rec")
		"rec":
			if String(cur["atk"]["phase"]) != "rec":
				_phase("rec")
			var pose := _seq([[0.0, 0.4, 0.0, -0.2, 1.2, 26.0, 0.62, 18.0, 0], [0.14, 0.38, 0.07, -0.15, 1.08, 26.0, 0.64, 18.0, 2],
				[GY_REC, 0.6, 0.9, 0.3, 1.0, 90.0, 1.0, 0.0, 0]], st)
			_pose(pose, "atk_slam_jump", 0.75 + 0.25 * clampf(st / GY_REC, 0.0, 1.0), "slam_2h")
			if st > 0.06:
				p._end_trail()
			_move(delta, 1.0, 0.0)
			if st >= GY_REC:
				_end()


func _goge_yakala(e: Node) -> void:
	## Yükselen kesiğe yakalanan sıradan düşman: kilitlenir, oyuncunun önünde dizilir; tavan yüksekliği kısaltır
	var ks: Array = cur["kilit"]
	if ks.has(e):
		return
	var dx := absf(e.global_position.x - p.global_position.x)
	var xo := clampf(dx * 0.6 + 16.0, 20.0, 64.0)
	var xs: Array = cur["xo"]
	for o in xs:
		if absf(float(o) - xo) < 15.0:
			xo = float(o) + 15.0
	xo = minf(xo, 84.0)
	ks.append(e)
	xs.append(xo)
	(cur["jolt"] as Array).append(Vector2.ZERO)
	e.state = "idle"
	e.st = 0.0
	e.cd = maxf(float(e.cd), 0.8)
	e.contact = false
	e.launch_t = 0.0
	e.sanat_dus = false
	e.sanat_indi = false
	e.sanat_hedef = e.global_position
	e.sanat_tut = 0.25
	# düşmanın hedef sütunundaki tavan: kaldırma yüksekliğini kısaltır (gövde boyu + pay)
	var tx := p.global_position.x + p.facing * xo
	var top := float(cur["y0"]) - float(e.size.y)
	var room := minf(_tavan(tx, top, 140.0), _tavan(e.global_position.x, e.global_position.y - float(e.size.y), 140.0))
	cur["H"] = clampf(minf(float(cur["H"]), room - 6.0), 0.0, float(cur["H"]))
	stats["goge"]["kaldirilan"] = int(stats["goge"]["kaldirilan"]) + 1
	stats["goge"]["H"] = float(cur["H"])
	FX.ghost(e.anim.base, Color(cur["col"], 0.45), 0.25)


func _goge_birak(dus := true) -> void:
	## Kilitleri bırak (sanat bitti / kesildi): havadakiler olağan düşüşle iner
	for e in cur.get("kilit", []):
		if is_instance_valid(e) and not e.dead:
			e.sanat_tut = 0.0
			e.sanat_dus = false
			if dus and not e.is_on_floor():
				e.launch_t = 0.4


func _goge_seg(s: String) -> void:
	cur["seg"] = s
	cur["t0"] = float(cur["t"])


func _goge_inis(d: Dictionary) -> void:
	## Yere çakılış: kilitli düşmanlara çakılma hasarı (+ek), çevreye alan hasarı, GÜM!
	var gp := p.global_position
	var ks: Array = cur["kilit"]
	var targets: Array = [p]
	var carp := 0
	for e in ks:
		if not is_instance_valid(e) or e.dead:
			continue
		var killed := _vur(e, float(d.get("dalis_hasar", 2.0)) + float(d.get("carpma_hasar", 0.8)), "carpma",
			{"kb": 40.0, "stun": 0.9, "heavy": true, "hs": 0.12, "sh": 0.85, "tier": 2, "fx": 1.3}, "blunt")
		carp += 1
		if not killed and is_instance_valid(e):
			targets.append(e)
			e.sanat_tut = 0.0
			if e.sanat_dus and not e.is_on_floor():
				# daha düşüyor: kilit bırakılır, yere hızlı iner
				e.sanat_dus = false
				e.velocity = Vector2(0.0, 600.0)
				e.launch_t = 0.5
			else:
				e.sanat_dus = false
				e.velocity = Vector2(p.facing * 40.0, -170.0)
				e.launch_t = 0.35
				e._bounced = true
			SanatFX.yer_carpma(Vector2(e.global_position.x, gp.y), int(cur["pal"]))
	stats["goge"]["carpilan"] = int(stats["goge"]["carpilan"]) + carp
	var alan := float(d.get("alan", 80.0))
	for e in _in_box(Rect2(gp.x - alan, gp.y - 56.0, alan * 2.0, 64.0), "inis"):
		if ks.has(e):
			continue
		_vur(e, float(d.get("dalis_hasar", 2.0)), "inis", {"kb": 240.0, "stun": 0.6, "heavy": true, "hs": 0.1, "sh": 0.65}, "blunt")
	# v28: yer efekti fırça bileşiminde (SanatFX.goge_gum); eski yer şoku küçük (düşmanlar okunur kalsın)
	InkFX.slam(gp, p.facing, 1.1, int(cur["pal"]))
	SanatFX.goge_gum(gp, p.facing, int(cur["pal"]), carp)
	FX.shockwave(gp + Vector2(0, -6), 96.0, 1.1)
	Game.shake_dir(0.85, Vector2(0, 1))
	Game.zoom_punch(0.07)
	Game.rumble(0.8, 0.5, 0.22)
	if carp > 0:
		Game.slowmo(0.3, 0.14)
		ImpactFrame.play(targets, 1.0, 2)
	_ses("sanat_gum", -1.0, 1.0, "sanat_cekis")
	p.vis_scale = Vector2(1.28, 0.76)
	cur["kilit"] = []


# ------------------------------------------------------------------ Bozkurt Atılışı
func _bozkurt(delta: float) -> void:
	var t := float(cur["t"])
	var d: Dictionary = cur["def"]
	var R := _R()
	var DASH := 0.11
	var W := 0.14
	if t < W:
		_phase("wind")
		var pose := _seq([[0.0, 0.6, 0.9, 0.3, 1.0, 88.0, 1.0, 0.0, 0], [W, -0.62, 2.12, 0.0, 0.78, 88.0, 0.38, 0.0, 2]], t)
		_pose(pose, "atk_lunge_long", t / W * 0.35, "stab_heavy")
		p.vis_scale = Vector2(1.1, 0.9)
		if not cur.has("tel"):
			cur["tel"] = true
			_ses("sanat_atilis", -5.0, 1.0, "uluma")
		_move(delta, 1.0, 0.0)
		return
	if t < W + DASH:
		_phase("act")
		var pose := _seq([[W, -0.62, 2.12, 0.0, 0.78, 88.0, 0.38, 0.0, 0], [W + 0.03, 1.6, 0.0, 0.0, 1.6, 88.0, 0.36, 0.0, 1]], t)
		_pose(pose, "atk_lunge_long", 0.45, "stab_heavy")
		if not cur.has("dash"):
			cur["dash"] = true
			cur["p0"] = p.center()
			cur["marked"] = []
			p.inv_t = maxf(p.inv_t, DASH + 0.2)
			Game.kick(Vector2(p.facing, 0), 5.0)
			FX.flash_light(p.center(), cur["col"], 150.0, 1.6, 0.2)
		p.velocity = Vector2(p.facing * float(d.get("mesafe", 150.0)) / DASH, 0.0)
		_trail_on(not cur.has("tr"), 1.5, 1)
		cur["tr"] = true
		if Engine.get_physics_frames() % 2 == 0:
			FX.ghost(p.anim.base, Color(cur["col"], 0.55), 0.22)
		for e in _in_box(_box(-14.0, -50.0, R + 12.0, 2.0), "gecis"):
			_vur(e, float(d.get("hasar", 1.6)), "gecis", {"kb": 30.0, "hs": 0.03, "sh": 0.2, "tier": 1, "fx": 0.9}, "pierce")
			if is_instance_valid(e) and not e.dead:
				(cur["marked"] as Array).append(e)
		_move(delta, 0.0, 0.0, 0.0)
		return
	if not cur.has("line"):
		cur["line"] = true
		SimsekKesikFX.line(cur["p0"] + Vector2(-p.facing * 6.0, 0.0), p.center() + Vector2(p.facing * 18.0, 0.0), cur["col"], 0.8)
		SanatFX.simsek(cur["p0"] + Vector2(-p.facing * 10.0, 2.0), p.center() + Vector2(p.facing * 22.0, 0.0), int(cur["pal"]), 10.0, randi(), 0.2)
		if p.wolf_anim:
			p.wolf_anim.set_facing(p.facing)
			p.wolf_anim.show_frame("pounce", 1)
			var wk := SanatFX.spawn("ruh_kurt", cur["p0"] + Vector2(-p.facing * 30.0, 20.0), cur["col"], 0.34, int(cur["pal"]))
			if wk:
				wk.data["yol"] = p.center() - (cur["p0"] as Vector2) + Vector2(p.facing * 40.0, 0.0)
				wk.setup_kurt(p.wolf_anim.base, p.facing)
		p._end_trail()
		p.velocity.x = p.facing * 220.0
	var KIN := W + DASH + 0.3
	if t < KIN:
		_phase("rec")
		var st := t - (W + DASH)
		var pose := _seq([[0.0, 1.6, 0.0, 0.0, 1.5, 88.0, 0.36, 0.0, 0], [0.12, 1.2, 0.6, -0.5, 1.1, 100.0, 0.34, 20.0, 2],
			[0.26, 0.5, 1.6, -1.35, 1.0, 100.0, 0.34, 0.0, 0]], st)
		_pose(pose, "atk_horiz", clampf(0.6 - st, 0.0, 0.3), "iai")
		_move(delta, 1.0, 0.0, 1800.0)
		return
	if not cur.has("kin"):
		cur["kin"] = true
		# kın sesi: bıçak kına girer, geçilen herkes aynı anda kesilir
		_ses("sanat_kin", -2.0, 1.0, "simsek_catirti")
		for e in cur.get("marked", []):
			if is_instance_valid(e) and not e.dead:
				var c: Vector2 = e.center()
				SanatFX.bozkurt_kin(c, int(cur["pal"]))
				_vur(e, float(d.get("kin_hasar", 0.9)), "kin", {"kb": 140.0, "stagger": true, "hs": 0.08, "sh": 0.35})
		p.anim.set_flash(0.3)
		p.get_tree().create_timer(0.05).timeout.connect(func() -> void:
			if is_instance_valid(p):
				p.anim.set_flash(0.0))
	var END := KIN + 0.16
	if t < END:
		var pose2 := _seq([[0.0, 0.5, 1.6, -1.35, 1.0, 100.0, 0.34, 0.0, 0], [0.16, 0.6, 0.9, 0.3, 1.0, 90.0, 1.0, 0.0, 0]], t - KIN)
		_pose(pose2, "atk_horiz", 0.0, "iai")
		_move(delta, 1.0, 0.0)
		return
	_end()


# ------------------------------------------------------------------ Kam Darbesi
func _kam(delta: float) -> void:
	var t := float(cur["t"])
	var d: Dictionary = cur["def"]
	var R := _R()
	var keys := [
		[0.0, 0.6, 0.9, 0.3, 1.0, 90.0, 1.0, 0.0, 0],
		[0.2, -0.55, 1.95, 1.3, 0.85, 90.0, 0.45, 0.0, 2],
		[0.25, 1.55, 0.05, 1.5, 1.42, 90.0, 0.42, 0.0, 1],
		[0.36, 1.5, 0.1, 1.45, 1.32, 90.0, 0.42, 0.0, 2],
		[0.62, 0.6, 0.9, 0.3, 1.0, 90.0, 1.0, 0.0, 0]]
	_pose(_seq(keys, t), "cast" if p.anim.has_anim("cast") else "atk_thrust", 0.0 if t < 0.22 else 0.99, "thrust")
	if t < 0.22:
		_phase("wind")
		if not cur.has("davul"):
			cur["davul"] = true
			_ses("sanat_kam", -3.0, 1.0, "kam_davul")
			SanatFX.kam_topla(p.arm_root.to_global(p._hand_local) + Vector2(p.facing * 6.0, 0.0), int(cur["pal"]))
		if Engine.get_physics_frames() % 3 == 0:
			var hnd := p.arm_root.to_global(p._hand_local)
			FX.burst(hnd, cur["col"], 2, 40, 0.35, 0.16, -40, true)
		p.vis_scale = Vector2(1.0 - 0.04 * t / 0.22, 1.0 + 0.04 * t / 0.22)
		_move(delta, 1.0, 0.0)
		return
	if t < 0.4:
		_phase("act")
		if not cur.has("vur"):
			cur["vur"] = true
			p.velocity.x = p.facing * 90.0
			var front := p.center() + Vector2(p.facing * 22.0, -2.0)
			# tayfsı ruh kurdu avucun önünde atılır
			if p.wolf_anim:
				p.wolf_anim.set_facing(p.facing)
				p.wolf_anim.show_frame("pounce", 1)
				var k := SanatFX.spawn("ruh_kurt", p.global_position + Vector2(0, 2), cur["col"], 0.46, int(cur["pal"]))
				if k:
					k.setup_kurt(p.wolf_anim.base, p.facing)
			InkFX.hit("magic", front + Vector2(p.facing * 10.0, 0), Vector2(p.facing, 0), int(cur["pal"]), 2, 1.4)
			SanatFX.kam_davul(front, p.facing, int(cur["pal"]))
			FX.shockwave(front, 54.0, 0.8)
			FX.flash_light(front, cur["col"], 160.0, 1.8, 0.22)
			Game.kick(Vector2(p.facing, 0), 6.0)
			var hits := _in_box(_box(-2.0, -58.0, R * 0.5 + 40.0, 4.0), "avuc")
			for e in hits:
				_kalkan_dusur(e)
				var was_armored: bool = float(e.sa_t) > 0.0
				if not e.is_boss:
					e.sa_t = 0.0
				var killed := _vur(e, float(d.get("hasar", 1.0)), "avuc", {"kb": 300.0, "stun": 1.2, "stagger": true, "heavy": true, "hs": 0.1, "sh": 0.55, "tier": 1, "fx": 0.9}, "magic")
				if not killed and is_instance_valid(e) and not e.is_boss and e.has_method("_guard_break"):
					e._guard_break(signf(e.center().x - p.global_position.x))
					if was_armored:
						FX.text(e.center() + Vector2(0, -float(e.size.y) - 18.0), "ZIRH YARILDI", cur["col"].lightened(0.3), 8)
			if not hits.is_empty():
				Game.slowmo(0.35, 0.12)
		_move(delta, 1.0, 0.0)
		return
	if t < 0.62:
		_phase("rec")
		_move(delta, 1.0, 0.0)
		return
	_end()


# ------------------------------------------------------------------ Ok Yağmuru
func _ok_yagmuru(delta: float) -> void:
	var t := float(cur["t"])
	var d: Dictionary = cur["def"]
	var pose := _seq([[0.0, 1.55, 0.05, 0.0, 1.0, 90.0, 1.0, 0.0, 0], [0.14, 2.45, 0.05, 0.0, 0.98, 90.0, 1.0, 0.0, 2],
		[0.24, 2.5, 0.05, 0.0, 1.02, 90.0, 1.0, 0.0, 0], [0.44, 1.7, 0.1, 0.0, 1.0, 90.0, 1.0, 0.0, 0]], t)
	_pose(pose, "bow" if p.anim.has_anim("bow") else "throw", 0.0 if t < 0.18 else 0.99, "spin")
	if not cur.has("hop"):
		cur["hop"] = true
		if p.is_on_floor():
			p.velocity = Vector2(-p.facing * 120.0, -230.0)
		_ses("yay_ger", -4.0, 0.9)
	if t < 0.2:
		_phase("wind")
		_move(delta, 0.8, 0.0, 900.0)
		return
	if not cur.has("atis"):
		cur["atis"] = true
		_phase("act")
		_ses("yay_birak_tam", -2.0, 0.9, "yay_birak")
		var a := Projectile.new()
		a.team = "x"
		a.kind = "arrow"
		a.position = p.center() + Vector2(p.facing * 6.0, -14.0)
		a.velocity = Vector2(p.facing * 90.0, -760.0)
		a.life = 0.5
		a.fx_kind = "od"
		a.trail_col = Color(cur["col"], 0.8)
		if p.level:
			p.level.add_projectile(a)
			SanatFX.ok_iz(a, int(cur["pal"]), 4.0)
		# hedef alanı: öndeki en yakın düşman (260 px), yoksa 120 px önü
		var cx := p.global_position.x + p.facing * 120.0
		var best := 260.0
		for e in p.get_tree().get_nodes_in_group("dusman"):
			if is_instance_valid(e) and not e.dead:
				var dx: float = (e.center().x - p.global_position.x) * p.facing
				if dx > 0.0 and dx < best and absf(e.center().y - p.center().y) < 120.0:
					best = dx
					cx = e.center().x
		var gy := p.global_position.y
		if p.level and p.level.has_method("ground_y_below"):
			var g: float = p.level.ground_y_below(Vector2(cx, p.global_position.y - 60.0), 200.0)
			if g > 0.0:
				gy = g
		_rains.append({"x": cx, "y": gy, "t": -0.35, "n": 0, "it": cur["item"], "d": d, "ring": false})
	if t < 0.46:
		_move(delta, 0.8, 0.0, 900.0)
		return
	_end()


func _rain_tick(delta: float) -> void:
	if _rains.is_empty():
		return
	for r in _rains.duplicate():
		r["t"] = float(r["t"]) + delta
		var d: Dictionary = r["d"]
		var tt := float(r["t"])
		if tt < 0.0:
			continue
		if not r["ring"]:
			r["ring"] = true
			SanatFX.ok_halka(Vector2(float(r["x"]), float(r["y"]) - 2.0), int(d.get("pal", 1)), float(d.get("sure", 1.1)))
			Ses.play("ok_ucus", -6.0, 0.8)
		var total := int(d.get("ok", 18))
		var dur := float(d.get("sure", 1.1))
		var want := mini(total, int(ceil(tt / dur * total)))
		while int(r["n"]) < want:
			r["n"] = int(r["n"]) + 1
			_rain_arrow(r)
		if int(r["n"]) >= total:
			_rains.erase(r)


func _rain_arrow(r: Dictionary) -> void:
	if p.level == null or not is_instance_valid(p):
		return
	var d: Dictionary = r["d"]
	var it: Dictionary = r["it"]
	var x := float(r["x"]) + randf_range(-62.0, 62.0)
	var a := Projectile.new()
	a.team = "p"
	a.kind = "arrow"
	a.position = Vector2(x - p.facing * 40.0, float(r["y"]) - 230.0 - randf_range(0, 30))
	a.velocity = Vector2(p.facing * 110.0, 640.0)
	a.gravity = 0.0
	a.life = 0.9
	a.fx_kind = "od"
	a.trail_col = Color(renk(String(d["id"])), 0.7)
	var self_ref := self
	a.on_hit = func(e: Node) -> void:
		self_ref._uzak_vur(e, it, d, "ok", float(d.get("hasar", 0.45)), {"kb": 30.0, "ok": true, "dir": signf(e.center().x - x) if is_instance_valid(e) else 1.0})
	p.level.add_projectile(a)
	SanatFX.ok_iz(a, int(d.get("pal", 1)), 3.0)
	# yere saplanan okun tozu (okun düşeceği yerde, varış anında)
	var gy := float(r["y"])
	var land := Vector2(x, gy)
	var tw := p.get_tree().create_timer(maxf(0.05, (gy - a.position.y) / 640.0))
	tw.timeout.connect(func() -> void:
		FX.dust(land, Vector2(0, -1), 2, 0.22)
		SanatFX.ok_saplan(land, int(d.get("pal", 1)))
		FX.sparks(land + Vector2(0, -2), Vector2(0, -1), renk(String(d["id"])), 2, 90.0))


# ------------------------------------------------------------------ Demir Duruş
func _demir(delta: float, _pressed: bool) -> void:
	var t := float(cur["t"])
	var d: Dictionary = cur["def"]
	var seg := String(cur.get("seg", ""))
	if seg == "":
		cur["seg"] = "durus"
		cur["t0"] = 0.0
		seg = "durus"
	var st := t - float(cur["t0"])
	match seg:
		"durus":
			_phase("wind")
			var pose := _seq([[0.0, 0.6, 0.9, 0.3, 1.0, 100.0, 1.0, 0.0, 0], [0.1, 1.05, 1.35, -0.35, 0.92, 100.0, 0.62, 30.0, 2]], st)
			pose[0] = float(pose[0]) + 0.02 * sin(t * 30.0)
			_pose(pose, "block" if p.anim.has_anim("block") else "atk_horiz", 0.0, "iai")
			p.vis_scale = Vector2(1.04, 0.97)
			if int(t / 0.3) != int(cur.get("glint_i", -1)):
				cur["glint_i"] = int(t / 0.3)
				var g := SanatFX.spawn("parilti", p.arm_root.to_global(p._hand_local + p._blade_local * _R() * 0.7), cur["col"], 0.25)
				if g:
					g.data = {"s": 9.0}
				if int(t / 0.3) == 0 and not cur.has("kalkan"):
					cur["kalkan"] = SanatFX.demir_kalkan(p, p.facing)
				if int(t / 0.3) == 0:
					_ses("sanat_ors", -9.0, 1.3, "darbe_metal")
			var lim := float(d.get("durus_sn", 0.9))
			if Input.is_action_pressed("sanat"):
				lim = float(d.get("durus_en_cok", 1.4))
			_move(delta, 1.0, 0.0, 2400.0)
			if st >= lim:
				cur["seg"] = "acik"
				cur["t0"] = t
				var kl: Variant = cur.get("kalkan")
				if is_instance_valid(kl) and kl is SanatFX:
					(kl as SanatFX).alive = false
		"acik":
			# boşa giden duruş: kısa açık
			_phase("rec")
			var pose := _seq([[0.0, 1.05, 1.35, -0.35, 0.92, 100.0, 0.62, 30.0, 0], [0.3, 0.6, 0.9, 0.3, 1.0, 90.0, 1.0, 0.0, 0]], st)
			_pose(pose, "atk_horiz", 0.0, "iai")
			cur["atk"]["super_armor"] = false
			_move(delta, 1.0, 0.0)
			if st >= 0.3:
				_end()
		"karsi":
			_demir_karsi(delta, st, d)


func karsila(from: Node, projectile: Node) -> bool:
	## Player.take_hit: Demir Duruş sürerken gelen darbe / mermi karşılanır ve karşılık başlar (öndeki ya da mermi)
	if cur.is_empty() or String(cur["id"]) != "demir_durus" or String(cur.get("seg", "")) != "durus":
		return false
	var src_x: float = from.global_position.x if from != null and is_instance_valid(from) else p.global_position.x + p.facing
	if projectile != null and is_instance_valid(projectile):
		src_x = projectile.global_position.x
	if signf(src_x - p.global_position.x) != float(p.facing) and absf(src_x - p.global_position.x) > 4.0:
		return false
	cur["seg"] = "karsi"
	cur["t0"] = float(cur["t"])
	cur["hedef"] = from if from != null and is_instance_valid(from) and from.has_method("hurt_rect") else null
	var hp := p.center() + Vector2(p.facing * 14.0, -4.0)
	p.inv_t = maxf(p.inv_t, 0.6)
	Game.hitstop(0.09)
	Game.slowmo(0.25, 0.28)
	Game.zoom_punch(0.06)
	Game.rumble(0.5, 0.5, 0.12)
	FX.sparks(hp, Vector2(p.facing, -0.5), Color(1.0, 0.95, 0.75), 18, 260.0)
	FX.flash_light(hp, cur["col"], 180.0, 2.2, 0.25)
	InkFX.flourish(hp, "parry", int(cur["pal"]))
	SanatFX.demir_ors(hp, p.facing)
	var kl: Variant = cur.get("kalkan")
	if is_instance_valid(kl) and kl is SanatFX:
		(kl as SanatFX).alive = false
	FX.text(p.center() + Vector2(0, -48), "ÖRS!", Color(0.85, 0.95, 1.0), 11)
	_ses("sanat_ors", -1.0, 1.0, "ors")
	ImpactFrame.play([p, from] if from != null and is_instance_valid(from) else [p], 1.0, 2)
	if projectile != null and is_instance_valid(projectile) and projectile.has_method("reflect"):
		projectile.reflect(p.facing, 1.5)
	if from != null and is_instance_valid(from) and from.has_method("stun") and not from.is_boss:
		from.stun(0.9)
	if from != null and is_instance_valid(from) and "contact" in from:
		from.contact = false
	stats["red"]["karsilandi"] = int(stats["red"].get("karsilandi", 0)) + 1
	if log_on:
		print("[sanat] demir_durus karsiladi")
	return true


func _demir_karsi(delta: float, st: float, d: Dictionary) -> void:
	var R := _R()
	var keys := [[0.0, 1.05, 1.35, -0.35, 0.92, 100.0, 0.62, 30.0, 0], [0.1, 0.38, 1.7, -1.45, 0.95, 100.0, 0.3, 0.0, 2],
		[0.15, 1.8, 0.0, 0.0, 1.3, 98.0, 0.28, 0.0, 1], [0.22, 2.2, 0.0, 0.2, 1.12, 108.0, 0.34, 40.0, 2],
		[0.5, 0.6, 0.9, 0.3, 1.0, 90.0, 1.0, 0.0, 0]]
	_pose(_seq(keys, st), "atk_horiz", clampf(st / 0.5, 0.0, 1.0), "iai")
	var h: Node = cur.get("hedef")
	if st < 0.1:
		_phase("wind")
		# hedefe atıl (yakın dövüşçüye), mermide yerinde
		if h != null and is_instance_valid(h) and not h.dead:
			var dx: float = h.center().x - p.global_position.x
			if absf(dx) > R * 0.7:
				p.velocity.x = signf(dx) * minf(900.0, (absf(dx) - R * 0.6) / 0.1)
		if Engine.get_physics_frames() % 2 == 0:
			FX.ghost(p.anim.base, Color(cur["col"], 0.5), 0.18)
		_move(delta, 1.0, 0.0, 0.0)
		return
	if st < 0.28:
		_phase("act")
		_trail_on(not cur.has("tr"), 2.0, 2)
		cur["tr"] = true
		p.velocity.x = move_toward(p.velocity.x, 0.0, 6000.0 * delta)
		if st >= 0.14:
			if not cur.has("karsi_fx"):
				cur["karsi_fx"] = true
				SanatFX.demir_karsi(p.center() + Vector2(p.facing * (R * 0.6 + 8.0), -2.0), p.facing, R)
			var box := _box(-8.0, -60.0, R + 26.0, 2.0)
			for e in _in_box(box, "karsi"):
				_vur(e, float(d.get("hasar", 2.6)), "karsi", {"kb": 260.0, "force_crit": true, "krit_neden": "demir_durus", "stun": 1.0,
					"stagger": true, "counter": true, "hs": 0.12, "sh": 0.6})
		_move(delta, 1.0, 0.0, 0.0)
		return
	if st < 0.5:
		_phase("rec")
		p._end_trail()
		_move(delta, 1.0, 0.0)
		return
	_end()


func alinan_k() -> float:
	## Player.take_hit: Demir Gönül sürerken alınan hasar azalır
	return 1.0 - def_k if def_t > 0.0 else 1.0


# ================================================================== HUD / test yardımcıları
func hazir() -> bool:
	var id := secili()
	return cur.is_empty() and cd <= 0.0 and uygun(id) and nisan() >= bedel_nisan(id) - 0.001


func aktif() -> bool:
	return not cur.is_empty()
