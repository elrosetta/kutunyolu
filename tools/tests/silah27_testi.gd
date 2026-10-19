extends Node
## v27 yeni silahlar testi (betikli girdi; oyuncunun kendi yolundan):
##   godot --headless --path . --quit-after 99999 -- --silah27 --boss
## Her silah kuşanılır, mekaniği oyunun girdi yolundan tetiklenir ve doğrulanır (Silah27.stats sayaçları, konum,
## hasar, kritik). Çıktı: "[silah27] <silah> <denetim> GECTI|KALDI ..." ve sonda "[silah27] SONUC GECTI|KALDI HATA=n".
## Çekim (headless değil): -- --silah27 --boss --pencere=1920x1080 --silah27_goruntu=C:/mutlak/klasor
##   her silahın yakın plan sahneleri (kombo, mekanik anı) <klasor>/<silah>_<an>.png

var main: Node
var lv: Node
var pl: Player
var spot := Vector2.ZERO
var bad := 0
var shot_dir := ""
const ACTS := ["saldiri1", "saldiri2", "zipla", "yuvarlan", "sag", "sol", "yukari", "asagi", "techizat1", "techizat2", "sise", "kut"]


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("--silah27_goruntu="):
			shot_dir = String(a).trim_prefix("--silah27_goruntu=")
	_run.call_deferred()


func _p(s: String) -> void:
	print("[silah27] ", s)


func _ok(w: String, what: String, cond: bool, extra := "") -> void:
	if not cond:
		bad += 1
	_p("%s %s %s %s" % [w, what, "GECTI" if cond else "KALDI", extra])


func _f(n := 1) -> void:
	for i in n:
		await get_tree().physics_frame
		Game.run["hp"] = float(Game.run["max_hp"])


func _release_all() -> void:
	for a in ACTS:
		Input.action_release(a)


func _tap(a: String, frames := 2) -> void:
	Input.action_press(a)
	await _f(frames)
	Input.action_release(a)


func _clear() -> void:
	for e in get_tree().get_nodes_in_group("dusman"):
		e.remove_from_group("dusman")
		e.queue_free()


func _enemy(dx: float, kind := "kara_boru") -> Enemy:
	var e: Enemy = lv.spawn_enemy(kind, spot + Vector2(dx, 0))
	e.max_hp = 99999.0
	e.hp = 99999.0
	e.speed = 0.0
	e.cd = 99.0
	e.aggro = false
	e.facing = -1 if dx > 0 else 1
	return e


func _calm() -> void:
	for e in get_tree().get_nodes_in_group("dusman"):
		if is_instance_valid(e) and not e.dead:
			e.cd = 99.0
			e.hp = maxf(e.hp, 1000.0)


func _equip(melee: String, second := "") -> void:
	_release_all()
	_clear()
	await _f(2)
	Game.run["slots"]["melee"] = ItemGen.roll(melee, 1, "demir", 0, "") if melee != "" else {}
	Game.run["slots"]["second"] = ItemGen.roll(second, 1, "demir", 0, "") if second != "" else {}
	for k in ["melee", "second"]:
		var it: Dictionary = Game.run["slots"][k]
		if not it.is_empty() and it.has("mech_v"):
			var r: Array = Data.find_item(String(it["id"]))["mech"]["range"]
			it["mech_v"] = roundf((float(r[0]) + float(r[1])) / 2.0) if bool(Data.find_item(String(it["id"]))["mech"].get("int", false)) else (float(r[0]) + float(r[1])) / 2.0
	pl.on_equip()
	pl.global_position = spot
	pl.velocity = Vector2.ZERO
	pl.facing = 1
	pl.last_step = -1
	pl.since_atk = 9.0
	for k in pl.cd.keys():
		pl.cd[k] = 0.0
	await _f(12)


func _snap(tag: String) -> void:
	if shot_dir == "" or DisplayServer.get_name() == "headless":
		return
	await RenderingServer.frame_post_draw
	var vp := get_viewport()
	var img := vp.get_texture().get_image()
	if vp.use_hdr_2d:
		if img.get_format() != Image.FORMAT_RGBA8 and img.get_format() != Image.FORMAT_RGB8:
			img.convert(Image.FORMAT_RGBA8)
		img.linear_to_srgb()
	img.save_png(shot_dir.path_join(tag + ".png"))


func _chain_taps(n: int, snaps := "", max_f := 260) -> void:
	## Zincir: her savuruşun temasından sonra yeniden bas (n savuruş); snaps verilirse her savuruşun ortasında çekim
	var swings := 0
	var last: Dictionary = {}
	Input.action_press("saldiri1")
	var held := 2
	var snapped := false
	for i in max_f:
		await _f()
		_calm()
		if held > 0:
			held -= 1
			if held == 0:
				Input.action_release("saldiri1")
		if not pl.atk.is_empty() and not is_same(pl.atk, last):
			last = pl.atk
			swings += 1
			snapped = false
		if snaps != "" and not snapped and not pl.atk.is_empty() and pl.atk.get("phase", "") == "act":
			var k := float(pl.atk["t"]) / float(pl.atk["dur"])
			if k > Player._contact_k(pl.atk["sw"]) + 0.02:
				snapped = true
				await _snap("%s_kombo%d" % [snaps, swings])
		if swings < n and held == 0 and not pl.atk.is_empty() and pl._past_contact():
			Input.action_press("saldiri1")
			held = 2
		if swings >= n and pl.atk.is_empty():
			break
	Input.action_release("saldiri1")


func _heavy(frames := 46) -> void:
	Input.action_press("saldiri1")
	await _f(frames)
	Input.action_release("saldiri1")


func _run() -> void:
	await get_tree().process_frame
	await _f(10)
	lv = main.level
	pl = lv.player
	if "boss" in lv and lv.boss != null and is_instance_valid(lv.boss):
		lv.boss.remove_from_group("dusman")
		lv.boss.queue_free()
		lv.boss = null
		spot = Vector2(33 * Level.TS + 12, lv.surface_y(33) * Level.TS - 1)
	else:
		spot = Vector2(40 * Level.TS + 12, lv.surface_y(40) * Level.TS - 1)
	main.hud.mode = "play"
	get_tree().paused = false
	pl.inv_t = 99999.0
	if shot_dir != "":
		await _f(300)   # bölüm başlığı sönsün
	Silah27.stats = {}
	await _gun_ay()
	await _kistin()
	await _albasti()
	await _cevgen()
	await _tatar()
	await _kuzgu()
	await _tengri()
	await _kart()
	_release_all()
	_p("SAYAC %s" % str(Silah27.stats))
	_p("SONUC %s HATA=%d" % ["GECTI" if bad == 0 else "KALDI", bad])
	get_tree().quit()


# ------------------------------------------------------------------ Gün-Ay İkizi
func _gun_ay() -> void:
	Silah27.gunay = "gun"
	await _equip("gun_ay_ikizi")
	var a := _enemy(30.0)
	var b := _enemy(-30.0)
	await _f(20)
	var hb := b.hp
	await _chain_taps(3, "gun_ay_ikizi_gun")
	_ok("gun_ay_ikizi", "gun_carki_iki_yan", b.hp < hb, "arkadaki hasar=%.0f" % (hb - b.hp))
	await _f(30)
	await _snap("gun_ay_ikizi_durus_oncesi")
	Input.action_press("saldiri1")
	for i in 90:
		await _f()
		_calm()
		if pl.atk.get("phase", "") == "charge" and float(pl.atk.get("charge", 0.0)) > 0.4:
			await _snap("gun_ay_ikizi_sarj")
			break
	Input.action_release("saldiri1")
	for i in 14:
		await _f()
		if i == 8:
			await _snap("gun_ay_ikizi_ay_ayrilis")
	await _f(30)
	_ok("gun_ay_ikizi", "duruş_ay", Silah27.gunay == "ay" and Silah27.sprite_id(pl.slot("melee")) == "gun_ay_ikizi_ay", "duruş=%s" % Silah27.gunay)
	var k0 := int(Player.krit_say["kesin"]) + int(Player.krit_say["kosul"])
	await _chain_taps(3, "gun_ay_ikizi_ay")
	_ok("gun_ay_ikizi", "ay_zinciri", String(Player._combo_for(pl.slot("melee"))["chain"][2]["s"]) == "ay_hilal", "")
	await _f(30)
	Input.action_press("saldiri1")
	for i in 90:
		await _f()
		if pl.atk.get("phase", "") == "charge" and float(pl.atk.get("charge", 0.0)) > 0.4:
			break
	Input.action_release("saldiri1")
	await _f(60)
	_ok("gun_ay_ikizi", "duruş_gun_geri", Silah27.gunay == "gun", "")
	var _u := k0 + a.get_instance_id()


# ------------------------------------------------------------------ Kistin
func _kistin() -> void:
	await _equip("kistin")
	var e := _enemy(30.0)
	var o := _enemy(-48.0)   # arkada: çalınan düşman üstüne düşecek
	await _f(20)
	var ho := o.hp
	var x_before := e.global_position.x - pl.global_position.x
	Input.action_press("saldiri1")
	var held := 2
	var swings := 0
	var last: Dictionary = {}
	var shot_cal := false
	for i in 420:
		await _f()
		_calm()
		if held > 0:
			held -= 1
			if held == 0:
				Input.action_release("saldiri1")
		if not pl.atk.is_empty() and not is_same(pl.atk, last):
			last = pl.atk
			swings += 1
		var sn := Silah27.node_of(pl)
		if swings == 3 and sn.bound != null and not shot_cal:
			await _snap("kistin_dolama")
		if swings == 4 and not shot_cal and not sn._throw.is_empty() and float(sn._throw["t"]) > float(sn._throw["dur"]) * 0.5:
			shot_cal = true
			await _snap("kistin_yere_calma")
		if swings < 4 and held == 0 and not pl.atk.is_empty() and pl._past_contact():
			Input.action_press("saldiri1")
			held = 2
		if swings >= 4 and pl.atk.is_empty():
			break
	Input.action_release("saldiri1")
	await _f(10)
	var x_after := e.global_position.x - pl.global_position.x
	_ok("kistin", "dolama", int(Silah27.stats.get("dolama", 0)) >= 1, "")
	_ok("kistin", "yere_calma_arkaya", int(Silah27.stats.get("cal", 0)) >= 1 and signf(x_after) != signf(x_before), "önce dx=%.0f sonra dx=%.0f" % [x_before, x_after])
	_ok("kistin", "altindaki_hasar", o.hp < ho and int(Silah27.stats.get("cal_alti", 0)) >= 1, "arkadaki hasar=%.0f" % (ho - o.hp))
	# bağlamadan dördüncü adım yok: düşmansız zincir 3 savuruşta biter, 4. basış yeniden ilk adım
	await _equip("kistin")
	await _chain_taps(4)
	_ok("kistin", "bagsiz_cal_yok", pl.last_step != 3, "son adım=%d" % pl.last_step)
	await _f(20)
	await _equip("kistin")
	_enemy(30.0, "agac_iyesi")
	await _f(10)
	await _chain_taps(4)
	_ok("kistin", "agir_calinmaz", int(Silah27.stats.get("cal_agir", 0)) >= 1, "")


# ------------------------------------------------------------------ Albastı Hançeri
func _albasti() -> void:
	await _equip("albasti_hanceri")
	var e := _enemy(26.0)
	await _f(20)
	await _chain_taps(3, "albasti_hanceri")
	var iz := int(e.get_meta("v27_iz", 0))
	_ok("albasti_hanceri", "al_izi", iz >= 3, "iz=%d" % iz)
	await _snap("albasti_hanceri_izler")
	# uzaklaş, Göç: izli düşmanın arkasında belir
	pl.global_position = e.global_position + Vector2(-140, 0)
	pl.facing = 1
	await _f(4)
	var hp0 := e.hp
	var kk := int(Player.krit_say["kesin"])
	Input.action_press("saldiri1")
	for i in 40:
		await _f()
		_calm()
	Input.action_release("saldiri1")
	for i in 30:
		await _f()
		if i == 3:
			await _snap("albasti_hanceri_goc")
	var side := signf(pl.global_position.x - e.global_position.x)
	_ok("albasti_hanceri", "goc_arkasinda", int(Silah27.stats.get("goc", 0)) >= 1 and side > 0.0 and pl.facing == -1, "taraf=%.0f yön=%d" % [side, pl.facing])
	_ok("albasti_hanceri", "goc_kritik", e.hp < hp0 and int(Player.krit_say["kesin"]) > kk, "hasar=%.0f" % (hp0 - e.hp))
	await _f(20)


# ------------------------------------------------------------------ Çevgen
func _cevgen() -> void:
	await _equip("cevgen")
	var a := _enemy(28.0)
	var b := _enemy(110.0)
	var c := _enemy(170.0)
	await _f(20)
	var hb := b.hp
	await _chain_taps(3, "cevgen")
	for i in 40:
		await _f()
		if i == 6:
			await _snap("cevgen_top")
	_ok("cevgen", "top_firlatildi", int(Silah27.stats.get("top", 0)) >= 1, "")
	_ok("cevgen", "carpma", b.hp < hb and int(Silah27.stats.get("top_carpma", 0)) >= 1, "B hasar=%.0f zincir=%d" % [hb - b.hp, int(Silah27.stats.get("top_zincir", 0))])
	var _u := a.get_instance_id() + c.get_instance_id()


# ------------------------------------------------------------------ Tatar Yayı
func _tatar() -> void:
	await _equip("", "tatar_yayi")
	var e := _enemy(110.0)
	var e2 := _enemy(150.0)
	await _f(20)
	var h1 := e.hp
	var h2 := e2.hp
	await _tap("saldiri2", 2)
	await _f(3)
	await _snap("tatar_yayi_atis")
	await _f(20)
	_ok("tatar_yayi", "atis_deler", e.hp < h1 and e2.hp < h2, "")
	# kurulurken altın yerde bas
	var k := pl.sec_slot
	for i in 120:
		var q := 1.0 - float(pl.cd[k]) / maxf(0.01, float(pl.cd_max[k]))
		if q >= 0.66:
			break
		await _f()
	await _snap("tatar_yayi_kurma")
	await _tap("saldiri2", 2)
	_ok("tatar_yayi", "kusursuz_kurma", int(Silah27.stats.get("kurma_tam", 0)) == 1 and float(pl.cd[k]) <= 0.0, "")
	await _f(4)
	var kk := int(Player.krit_say["kesin"])
	await _tap("saldiri2", 2)
	await _f(25)
	_ok("tatar_yayi", "kut_oku_kritik", int(Player.krit_say["kesin"]) > kk, "")
	# erken basış: takılır
	for i in 60:
		var q := 1.0 - float(pl.cd[k]) / maxf(0.01, float(pl.cd_max[k]))
		if q >= 0.28:
			break
		await _f()
	var cm := float(pl.cd_max[k])
	await _tap("saldiri2", 2)
	_ok("tatar_yayi", "erken_takilir", int(Silah27.stats.get("kurma_takildi", 0)) == 1 and float(pl.cd_max[k]) > cm, "")
	await _f(120)


# ------------------------------------------------------------------ Kam Küzgüsü
func _kuzgu() -> void:
	await _equip("", "kam_kuzgusu")
	var e := _enemy(90.0)
	await _f(20)
	Input.action_press("saldiri2")
	var first := -1.0
	var last_d := 0.0
	var prev := e.hp
	for i in 200:
		await _f()
		_calm()
		var dd := prev - e.hp
		prev = e.hp
		if dd > 0.0:
			if first < 0.0:
				first = dd
			last_d = dd
		if i == 60:
			await _snap("kam_kuzgusu_isin")
		if i == 140:
			await _snap("kam_kuzgusu_kizgin")
		if int(Silah27.stats.get("kuzgu_patlama", 0)) > 0:
			await _f(3)
			await _snap("kam_kuzgusu_patlama")
			break
	Input.action_release("saldiri2")
	_ok("kam_kuzgusu", "isin_kizar", last_d > first * 2.0, "ilk tik=%.1f son tik=%.1f" % [first, last_d])
	_ok("kam_kuzgusu", "gun_patlamasi", int(Silah27.stats.get("kuzgu_patlama", 0)) >= 1, "")
	await _f(10)
	Input.action_press("saldiri2")
	await _f(10)
	var on := Silah27.node_of(pl).k_on
	Input.action_release("saldiri2")
	_ok("kam_kuzgusu", "soguma", not on, "")
	await _f(110)
	_ok("kam_kuzgusu", "birakinca_durur", not Silah27.node_of(pl).k_on and not Ses._loops.has("kuzgu") or not is_instance_valid(Ses._loops.get("kuzgu")), "")


# ------------------------------------------------------------------ Tengri Bağı
func _tengri() -> void:
	await _equip("alp_kilici", "tengri_bagi")
	var a := _enemy(90.0)
	var b := _enemy(150.0)
	await _f(20)
	await _tap("saldiri2", 2)
	await _f(30)
	await _snap("tengri_bagi_bag")
	var sn := Silah27.node_of(pl)
	_ok("tengri_bagi", "bag_kuruldu", sn.links.size() == 1 and (sn.links[0]["m"] as Array).size() == 2, "")
	var hb := b.hp
	var p0 := int(Silah27.stats.get("bag_pay", 0))
	pl.global_position = a.global_position + Vector2(-26, 0)
	await _f(2)
	await _tap("saldiri1", 2)
	await _f(30)
	_ok("tengri_bagi", "hasar_payi", int(Silah27.stats.get("bag_pay", 0)) > p0 and b.hp < hb, "B hasar=%.0f" % (hb - b.hp))
	for k in pl.cd.keys():
		pl.cd[k] = 0.0
	await _tap("saldiri2", 2)
	await _f(4)
	await _snap("tengri_bagi_cekis")
	await _f(20)
	_ok("tengri_bagi", "bag_cekisi", int(Silah27.stats.get("bag_carpisma", 0)) >= 1 and sn.links.is_empty(), "")


# ------------------------------------------------------------------ kart: SnH ve açıklamalar
func _kart() -> void:
	for id in Silah27.IDS:
		var it := ItemGen.roll(id, 0, "demir", 0, "")
		var dps := float(ItemGen.dps_oyuncu(it))
		var lines := ItemGen.describe(it)
		_ok(id, "kart", dps > 5.0 and dps < 80.0 and not lines.is_empty(), "SnH=%.1f hız=%.2f" % [dps, ItemGen.aps_eff(it)])
	_ok("havuz", "parsomen", ItemGen.locked_implemented().has("tatar_yayi") or Game.is_unlocked("tatar_yayi"), "")
