extends Node
## v22 denge ölçümü: godot --headless --path . --quit-after 600 -- --denge [--denge_muhur=N]
## Her derinlik (1-9) için biyomun her düşman türü: can, vuruş hasarı; başlangıç silahıyla (Demir Alp Kılıcı,
## tılsımsız) ve derinliğe uygun yuvarlanmış silahla (o kademenin Nadir Demir silahı + beklenen tılsım sayısı)
## kaç vuruşta / kaç saniyede ölür; düşman vuruşu oyuncunun canına göre kaç vuruşta öldürür. Bosslar: can, savaş
## süresi (beklenen SnH × isabet payı). Yakın silahların SnH tablosu (ağır / hafif dengesi).
## Hesap oyunun kendi formülleriyle: Enemy.setup, ItemGen.roll / dps, Player.tempo_aps, Game.item_mult.
## Zorluk.gd yoksa (v22 öncesi) eski boss / eşya formülleri kullanılır: önce / sonra tablosu aynı betikle çıkar.

var main: Node
var Z: Variant = null   # scripts/core/Zorluk.gd (v22)

const SILAHLAR := ["alp_kilici", "ikiz_bicak", "kargi", "gurz", "ulu_kilic"]
const BOSSLAR := {"kara_boru_han": 2, "tepegoz": 4, "sahmeran": 6, "yelbegen": 8, "erlik_han": 10}
## beklenen oyuncu: her derinlikte ~2,5 tılsım; %60 Kurt (yakın), %25 Ayı, %15 Kartal
const TILSIM_DERINLIK := 2.5
const ISABET_PAYI := 0.45   # boss savaşında vurabildiğin zaman payı (kaçış, bekleme, evre geçişi)


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	if ResourceLoader.exists("res://scripts/core/Zorluk.gd"):
		Z = load("res://scripts/core/Zorluk.gd")
	_run.call_deferred()


func _p(s: String) -> void:
	print("[denge] ", s)


func _tilsim(d: int) -> Dictionary:
	if Z and Z.has_method("beklenen_tomar"):
		return Z.beklenen_tomar(d)   # v23: zorluk.json "tomar" (derinlik başına tomar + boss tomarları)
	var s := TILSIM_DERINLIK * float(d - 1)
	return {"kurt": int(round(s * 0.6)), "ayi": int(round(s * 0.25)), "kartal": int(round(s * 0.15))}


func _typ_hp(o: Dictionary) -> float:
	if Z and Z.has_method("beklenen_can"):
		return float(Z.beklenen_can(o))
	var hp := 100.0
	for i in int(o["kurt"]) + int(o["kartal"]):
		hp *= 1.06
	for i in int(o["ayi"]):
		hp *= 1.15
	return hp


func _tier(d: int) -> int:
	if Z and Z.has_method("kademe"):
		return int(Z.kademe(d))
	return mini(5, d - 1)


func _wpn(id: String, tier: int, rarity: int) -> Dictionary:
	var it := ItemGen.roll(id, tier, "demir", rarity, "")
	it["affixes"] = []
	if ItemGen.has_method("dmg_for"):
		it["dmg"] = ItemGen.dmg_for(id, tier, "demir", rarity)
	else:
		it["dmg"] = float(Data.find_item(id)["dmg"]) * (1.0 + 0.6 * tier)
	it["crit"] = float(Data.find_item(id)["crit"])
	it["aps"] = float(Data.find_item(id)["aps"])   # kalite yuvarlaması olmadan (tekrarlanabilir)
	return it


func _avg_hit(it: Dictionary) -> float:
	var ta: Array = Player.tempo_aps(it, ItemGen.hiz_pct(it))
	var step := float(ta[1]) / maxf(0.001, float(ta[0]))
	if ItemGen.has_method("zincir_hasar"):
		# v23: vuruş başına ortalama = tur hasarı / turdaki vuruş (bitiriş çarpanı, çok vuruş, yer şoku dahil)
		step = float(ItemGen.zincir_hasar(it)) / maxf(1.0, float(ItemGen.zincir_vurus(it)))
	var cc := clampf(float(it["crit"]) / 100.0, 0.0, 1.0)
	var cm := float(it["crit_mult"])
	return float(it["dmg"]) * step * (1.0 + cc * (cm - 1.0)) * Game.item_mult(it)


func _stats(kind: String, elite: bool, d: int) -> Array:
	var e := Enemy.new()
	e.setup(kind, elite, _tier(d))
	var r := [e.max_hp, e.dmg]
	e.free()
	return r


func _boss_stats(bid: String, d: int) -> Array:
	var bdef: Dictionary = {}
	for b in Data.world["bosses"]:
		if b["id"] == bid:
			bdef = b
	var ek := String(bdef.get("enemy", bid))
	var e := Enemy.new()
	e.setup(ek, false, _tier(d))
	var hp := float(bdef.get("hp", 900)) * (1.0 + 0.35 * float(mini(5, d - 1)))
	if Z and Z.has_method("boss_can"):
		hp = float(Z.boss_can(bid, float(bdef.get("hp", 900))))
	var r := [hp, e.dmg]
	e.free()
	return r


func _pool(d: int) -> Array:
	var bid: String = Game.biome_for_depth(d).get("id", "otuken")
	var pool: Array = []
	for e in Data.world["enemies"]:
		if e.get("biome", "") == bid and e.get("impl", false) and not String(e.get("ai", "")).begins_with("boss"):
			pool.append(e["id"])
	return pool


func _med(a: Array) -> float:
	if a.is_empty():
		return 0.0
	var b := a.duplicate()
	b.sort()
	return float(b[b.size() / 2])


func _set_run(d: int, ongun: Dictionary) -> void:
	Game.run["depth"] = d
	Game.run["tier"] = _tier(d)
	Game.run["ongun"] = ongun.duplicate()


func _run() -> void:
	await get_tree().process_frame
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--denge_cekim="):
			await _cekim(String(arg).trim_prefix("--denge_cekim="))
			get_tree().quit()
			return
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--denge_muhur=") and Z and Z.has_method("set_muhur"):
			Z.set_muhur(int(String(arg).trim_prefix("--denge_muhur=")))
	var saved_run: Dictionary = Game.run.duplicate(true)
	var sv: Dictionary = Game.run["slots"].duplicate(true)
	Game.run["slots"] = {"melee": {}, "second": {}, "g1": {}, "g2": {}}   # kuşanılan teçhizat hız katmasın
	_p("zorluk betiği: %s" % ("var (v22)" if Z else "yok (v22 öncesi)"))
	# ---- 1) yakın silahların SnH'si (kademe 0, Demir, Sıradan, niteliksiz)
	_set_run(1, {"kurt": 0, "kartal": 0, "ayi": 0})
	var rows: Array = []
	for w in Data.items["weapons"]:
		if not w.get("impl", false) or not (String(w.get("kind", "")) in ItemGen.MELEE_KINDS):
			continue
		var it := _wpn(String(w["id"]), 0, 0)
		var ta: Array = Player.tempo_aps(it, 0.0)
		rows.append([String(w["id"]), String(w["kind"]), float(it["dmg"]), float(ta[0]), ItemGen.dps(it), _avg_hit(it)])
	rows.sort_custom(func(a: Array, b: Array) -> bool: return float(a[4]) > float(b[4]))
	_p("SILAH_SNH | silah | tür | hasar | vuruş/sn | SnH | ort. vuruş")
	for r in rows:
		_p("SILAH_SNH | %s | %s | %.1f | %.2f | %.1f | %.1f" % [r[0], r[1], r[2], r[3], r[4], r[5]])
	# ---- 2) derinlik tablosu
	_p("DERINLIK | d | kademe | oyuncu canı (beklenen) | tomar K/A/Ka | başl. ort.vuruş | tipik ort.vuruş | tipik SnH | tomarsız tipik ort.vuruş")
	var summary: Array = []
	for d in range(1, 10):
		var o := _tilsim(d)
		var start := _wpn("alp_kilici", 0, 0)
		_set_run(d, {"kurt": 0, "kartal": 0, "ayi": 0})
		var start_hit := _avg_hit(start)
		var start_dps := ItemGen.dps(start)
		_set_run(d, o)
		var typ_hits: Array = []
		var typ_dps_a: Array = []
		var ns_hits: Array = []
		var start_t_hit := _avg_hit(start)   # v23: başlangıç silahı + beklenen tomar
		for w in SILAHLAR:
			var it := _wpn(w, _tier(d), 1)
			typ_hits.append(_avg_hit(it))
			typ_dps_a.append(ItemGen.dps(it) * Game.item_mult(it))
		_set_run(d, {"kurt": 0, "kartal": 0, "ayi": 0})
		for w in SILAHLAR:
			ns_hits.append(_avg_hit(_wpn(w, _tier(d), 1)))   # v23: aynı tipik silah, tomarsız
		_set_run(d, o)
		var typ_hit := 0.0
		var typ_dps := 0.0
		var ns_hit := 0.0
		for i in typ_hits.size():
			typ_hit += float(typ_hits[i]) / typ_hits.size()
			typ_dps += float(typ_dps_a[i]) / typ_dps_a.size()
			ns_hit += float(ns_hits[i]) / ns_hits.size()
		var php := _typ_hp(o)
		var red := minf(0.3, 0.03 * float(o["ayi"]))
		_p("DERINLIK | %d | %d | %.0f | %d/%d/%d | %.1f | %.1f | %.1f | %.1f" % [d, _tier(d), php, o["kurt"], o["ayi"], o["kartal"], start_hit, typ_hit, typ_dps, ns_hit])
		var htk_s: Array = []
		var htk_t: Array = []
		var htk_ns: Array = []
		var htk_st: Array = []
		var htd: Array = []
		var htd100: Array = []
		for k in _pool(d):
			var st := _stats(k, false, d)
			var hp := float(st[0])
			var dm := float(st[1])
			var a: int = int(ceil(hp / start_hit))
			var b: int = int(ceil(hp / typ_hit))
			var c: int = int(ceil(php / maxf(0.1, dm * (1.0 - red))))
			var c0: int = int(ceil(100.0 / maxf(0.1, dm)))
			htk_s.append(a)
			htk_t.append(b)
			htk_ns.append(int(ceil(hp / ns_hit)))
			htk_st.append(int(ceil(hp / start_t_hit)))
			htd.append(c)
			htd100.append(c0)
			_p("DUSMAN | d%d | %s | %s | can %.0f | vuruş %.1f | başl. %d vuruş %.1f sn | tipik %d vuruş %.1f sn | oyuncu %d vuruşta (100 canla %d)" % [d, k, Data.enemy_def(k).get("ai", "?"), hp, dm, a, hp / start_dps, b, hp / typ_dps, c, c0])
		# seçkin: biyomun ilk türü
		var ek: String = _pool(d)[0]
		var es := _stats(ek, true, d)
		_p("SECKIN | d%d | %s | can %.0f | vuruş %.1f | başl. %d vuruş | tipik %d vuruş %.1f sn | oyuncu %d vuruşta" % [d, ek, es[0], es[1], int(ceil(float(es[0]) / start_hit)), int(ceil(float(es[0]) / typ_hit)), float(es[0]) / typ_dps, int(ceil(php / maxf(0.1, float(es[1]) * (1.0 - red))))])
		summary.append([d, _med(htk_s), _med(htk_t), _med(htd), _med(htd100), int(ceil(float(es[0]) / typ_hit)), int(ceil(float(es[0]) / start_hit)), _med(htk_ns), _med(htk_st)])
	_p("OZET | d | başl. silahla vuruş (ortanca) | tipik vuruş (ortanca) | seçkin tipik | seçkin başl. | oyuncu ölür (tipik can) | oyuncu ölür (100 can) | tipik silah tomarsız | başl. silah + tipik tomar")
	for s in summary:
		_p("OZET | %d | %d | %d | %d | %d | %d | %d | %d | %d" % [s[0], int(s[1]), int(s[2]), int(s[5]), int(s[6]), int(s[3]), int(s[4]), int(s[7]), int(s[8])])
	# ---- 3) bosslar
	_p("BOSS | boss | derinlik | can | vuruş | tipik SnH | süre (sn, isabet payı %.0f%%) | oyuncu ölür" % (ISABET_PAYI * 100.0))
	for bid in BOSSLAR:
		var d: int = BOSSLAR[bid]
		var o := _tilsim(d)
		_set_run(d, o)
		var dps := 0.0
		var dps0 := 0.0
		for w in SILAHLAR:
			var it := _wpn(w, _tier(d), 1)
			dps += ItemGen.dps(it) * Game.item_mult(it) / SILAHLAR.size()
			dps0 += ItemGen.dps(it) / SILAHLAR.size()
		var bs := _boss_stats(bid, d)
		var php := _typ_hp(o)
		var red := minf(0.3, 0.03 * float(o["ayi"]))
		_p("BOSS | %s | %d | %.0f | %.1f | %.1f | %.0f | %d | tomarsız %.0f sn, 100 canla %d" % [bid, d, bs[0], bs[1], dps, float(bs[0]) / maxf(0.1, dps * ISABET_PAYI), int(ceil(php / maxf(0.1, float(bs[1]) * (1.0 - red)))), float(bs[0]) / maxf(0.1, dps0 * ISABET_PAYI), int(ceil(100.0 / maxf(0.1, float(bs[1]))))])
	Game.run = saved_run
	Game.run["slots"] = sv
	_p("BITTI")
	get_tree().quit()


# ------------------------------------------------------------------ can çubuğu çekimleri (headless değil)
## -- --denge --denge_cekim=C:/mutlak/klasor --pencere=1920x1080 [--derinlik=N | --boss=tepegoz]
## Düz alanda durağan yaratıklara hasar verip can çubuklarını çeker: tek, grup, seçkin; boss arenasında boss çubuğu.
func _wait(s: float) -> void:
	await get_tree().create_timer(s, true, false, true).timeout


func _snap(path: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	if get_viewport().use_hdr_2d:
		if img.get_format() != Image.FORMAT_RGBA8 and img.get_format() != Image.FORMAT_RGB8:
			img.convert(Image.FORMAT_RGBA8)
		img.linear_to_srgb()
	img.save_png(path)
	_p("cekim %s" % path)


func _foe(lv: Node, kind: String, at: Vector2, elite := false, ofk := false) -> Enemy:
	var e: Enemy = lv.spawn_enemy(kind, at, elite, ofk)
	e.aggro = false
	e.facing = -1
	return e


func _freeze(e: Node) -> void:
	if is_instance_valid(e):
		e.set_physics_process(false)
		e.velocity = Vector2.ZERO
		if e.anim:
			e.anim.set_facing(-1)


func _cekim(dir: String) -> void:
	DirAccess.make_dir_recursive_absolute(dir)
	await _wait(1.0)
	var guard := 0
	while float(main.hud._card_t) < 4.6 and guard < 2000:   # bölüm adı sönsün
		await get_tree().process_frame
		guard += 1
	_p("bekleme kare=%d card_t=%.2f ts=%.2f" % [guard, float(main.hud._card_t), Engine.time_scale])
	var lv: Node = main.level
	var pl: Node = lv.player
	pl.inv_t = 999.0
	if lv.boss != null and is_instance_valid(lv.boss):
		var b: Node = lv.boss
		await _wait(3.0)
		b.take_hit(b.max_hp * 0.3, {"kb": 0.0, "dir": 1})
		await _wait(0.9)
		b.take_hit(b.max_hp * 0.12, {"kb": 0.0, "dir": 1})
		await _wait(0.12)
		await _snap(dir.path_join("v22_boss_cubugu.png"))
		return
	for e in get_tree().get_nodes_in_group("dusman"):
		e.queue_free()
	await _wait(0.3)
	var base: Vector2 = pl.global_position
	pl.facing = 1
	# 1) tek yaratık: hasar aldı, gecikmeli parça erimeden
	var e1 := _foe(lv, "kara_boru", base + Vector2(110, -2))
	await _wait(0.05)
	_freeze(e1)
	e1.take_hit(e1.max_hp * 0.22, {"kb": 0.0, "dir": 1})
	await _wait(0.12)
	e1.take_hit(e1.max_hp * 0.18, {"kb": 0.0, "dir": 1})
	await _wait(0.1)
	await _snap(dir.path_join("v22_tek_dusman.png"))
	e1.queue_free()
	await _wait(0.2)
	# 2) grup: farklı boylar, durumlar, duruş, kalkan, öfkeli
	var kinds := [["kara_boru", 60, false], ["balbal", 110, false], ["surale", 160, false], ["cor", 205, true], ["bekci", 255, false]]
	var foes: Array = []
	for k in kinds:
		var e := _foe(lv, String(k[0]), base + Vector2(float(k[1]), -2), false, bool(k[2]))
		foes.append(e)
	await _wait(0.05)
	for e in foes:
		_freeze(e)
	foes[0].take_hit(foes[0].max_hp * 0.55, {"kb": 0.0, "dir": 1, "burn": 3.0})
	foes[1].take_hit(foes[1].max_hp * 0.3, {"kb": 0.0, "dir": 1, "poise": 4.5, "poison": 3})
	foes[2].take_hit(foes[2].max_hp * 0.7, {"kb": 0.0, "dir": 1})
	foes[2].bleed = 3
	foes[2].bleed_t = 4.0
	foes[3].take_hit(foes[3].max_hp * 0.2, {"kb": 0.0, "dir": 1, "freeze": 2.0})
	foes[4].facing = 1
	foes[4].take_hit(foes[4].max_hp * 0.4, {"kb": 0.0, "dir": 1, "behind": true})
	foes[4].broken_t = 2.0
	await _wait(0.15)
	foes[1].take_hit(foes[1].max_hp * 0.15, {"kb": 0.0, "dir": 1})
	await _wait(0.08)
	await _snap(dir.path_join("v22_grup.png"))
	for e in foes:
		if is_instance_valid(e):
			e.queue_free()
	await _wait(0.2)
	# 3) seçkin: ağır, duruş çizgisi + durum simgesi
	var el := _foe(lv, "agac_iyesi", base + Vector2(120, -2), true)
	await _wait(0.05)
	_freeze(el)
	el.take_hit(el.max_hp * 0.35, {"kb": 0.0, "dir": 1, "poise": 6.0, "burn": 3.0})
	el.apply_curse()
	await _wait(0.6)
	el.take_hit(el.max_hp * 0.1, {"kb": 0.0, "dir": 1, "poise": 3.0})
	await _wait(0.1)
	await _snap(dir.path_join("v22_seckin.png"))
