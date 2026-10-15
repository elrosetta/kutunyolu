extends Node
## Giriş noktası: başlık → hikâye → (Demirci) → bölüm. Kut Kapısı'ndan geçince eşyalar korunarak
## bir sonraki derinliğe inilir; ölünce toplanan Kut bankaya eklenir ve yeni koşu başlar.
## Tılsım seçimi ve Demirci ekranı burada yönetilir (ağaç duraklıyken girdi).

var level: Level
var hud: HUD
var ui_layer: CanvasLayer
var auto_test := false
var showcase := false
var lab := false
var _lab_i := 0
var scroll_pickup: Pickup
var slot_pickup: Pickup
var _depth_forced := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	ui_layer = CanvasLayer.new()
	ui_layer.layer = 10
	add_child(ui_layer)
	hud = HUD.new()
	hud.main = self
	ui_layer.add_child(hud)
	auto_test = OS.get_cmdline_user_args().has("--otomatik")
	showcase = OS.get_cmdline_user_args().has("--sahne") or OS.get_cmdline_user_args().has("--savurus")
	lab = OS.get_cmdline_user_args().has("--savurus")
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--ekran="):
			_ekran = String(arg).trim_prefix("--ekran=")
			auto_test = false
	_new_run()
	if OS.get_cmdline_user_args().has("--yurt"):
		_build_hub()  # yurt testi: doğrudan Ulu Kayın'da başla
	if OS.get_cmdline_user_args().has("--mekanik"):
		var mt: Node = load("res://tools/tests/mekanik_testi.gd").new()
		mt.set("main", self)
		add_child(mt)
	for arg in OS.get_cmdline_user_args():
		if String(arg) == "--boss":
			_build_boss("kara_boru_han")
		elif String(arg).begins_with("--boss="):
			_build_boss(String(arg).trim_prefix("--boss="))
	if auto_test or showcase or _ekran != "" or OS.get_cmdline_user_args().has("--mekanik"):
		hud.mode = "play"
		get_tree().paused = false
	else:
		hud.mode = "title"
		get_tree().paused = true
		Ses.music("baslik")


func _new_run() -> void:
	Ses.low_hp(0.0)
	Game.new_run()
	Game.meta["runs"] = int(Game.meta.get("runs", 0)) + 1
	Game.save_meta()
	_build_level()


func _build_level() -> void:
	if level:
		level.queue_free()
	level = Level.new()
	level.process_mode = Node.PROCESS_MODE_PAUSABLE
	add_child(level)
	var seed_v := randi() if not auto_test else 1234 + int(Game.run.get("depth", 1))
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--derinlik=") and not _depth_forced:
			_depth_forced = true
			var dd := int(String(arg).trim_prefix("--derinlik="))
			Game.run["depth"] = dd
			Game.run["tier"] = mini(5, dd - 1)
		if String(arg).begins_with("--tohum="):
			seed_v = int(String(arg).trim_prefix("--tohum=")) + int(Game.run.get("depth", 1))
	level.build(seed_v)
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--dok="):
			level.dump_png(String(arg).trim_prefix("--dok="))
	level.finished.connect(_on_finished)
	level.player_died.connect(_on_died)
	level.scroll_requested.connect(_on_scroll)
	level.slot_requested.connect(_on_slot_request)
	level.lutuf_requested.connect(_on_lutuf)
	hud.level = level
	hud._card_t = 0.0


func _build_boss(bid: String) -> void:
	if level:
		level.queue_free()
	level = Level.new()
	level.process_mode = Node.PROCESS_MODE_PAUSABLE
	add_child(level)
	level.build_boss(randi(), bid)
	level.finished.connect(_on_finished)
	level.player_died.connect(_on_died)
	level.slot_requested.connect(_on_slot_request)
	level.boss_died.connect(func() -> void: hud.flash_msg = "Kut Kapısı açılıyor..."; hud.flash_t = 3.0)
	hud.level = level
	hud._card_t = 0.0


func _on_lutuf(p: Pickup) -> void:
	## Sunak: rastgele bir tanrı lütfu (sahip olunmayanlardan), en çok 3
	var have: Array = Game.run.get("lutuf", [])
	if have.size() >= 3:
		hud.flash_msg = "Üç lütuf taşıyorsun; sunak sessiz."
		hud.flash_t = 2.5
		return
	var pool: Array = []
	for k in Game.LUTUF.keys():
		if not (k in have):
			pool.append(k)
	if pool.is_empty():
		return
	var id: String = pool[randi() % pool.size()]
	Game.grant_lutuf(id)
	var l: Array = Game.LUTUF[id]
	var col := Color(l[2][0], l[2][1], l[2][2])
	if level.player:
		FX.ring(level.player.center(), 60, col, 0.6)
		FX.soul(level.player.center(), col, 30)
		FX.flash_light(level.player.center(), col, 260.0, 2.0, 0.5)
		FX.text(level.player.center() + Vector2(0, -44), String(l[0]), col, 11)
		level.player.vis_scale = Vector2(0.85, 1.15)
	Game.slowmo(0.4, 0.3)
	Ses.play("acilis", -2.0)
	hud.flash_msg = "%s: %s" % [l[0], l[1]]
	hud.flash_t = 5.0
	level.pickups.erase(p)
	p.queue_free()


func _build_hub() -> void:
	## Bölüm bitti: Ulu Kayın yurdu (NPC'ler). Eşyalar ve can korunur.
	if level:
		level.queue_free()
	level = Level.new()
	level.process_mode = Node.PROCESS_MODE_PAUSABLE
	add_child(level)
	level.build_hub(77)
	level.finished.connect(_on_finished)
	level.player_died.connect(_on_died)
	level.npc_requested.connect(_on_npc)
	hud.level = level
	hud._card_t = 99.0


func _next_level() -> void:
	Game.next_depth()
	Game.meta["best_depth"] = maxi(int(Game.meta.get("best_depth", 1)), int(Game.run["depth"]))
	Game.save_meta()
	_build_level()
	_start_play()


func _on_finished() -> void:
	if level and level.hub:
		# yurttan derine
		_next_level()
		return
	# bu derinliğin sonunda boss var mı?
	var depth := int(Game.run.get("depth", 1))
	if level and level.boss_id == "":
		var bid: String = String(Game.BOSS_AFTER.get(depth, ""))
		if bid != "" and not (bid in Game.run.get("boss_done", [])):
			_build_boss(bid)
			_start_play()
			Game.run["lutuf"] = Game.run.get("lutuf", [])
			return
	if auto_test or showcase:
		hud.mode = "done"
		get_tree().paused = true
		return
	Game.run["lutuf"] = []  # lütuflar yurda dönünce söner
	_build_hub()
	_start_play()
	hud.flash_msg = "Ulu Kayın yurdu: Kut'unu Umay Ana'ya götür (E). Kapı seni derine indirir."
	hud.flash_t = 5.0


func _on_npc(id: String) -> void:
	hud.sel = 0
	get_tree().paused = true
	match id:
		"umay":
			var saved := int(Game.run.get("kut", 0))
			if saved > 0:
				Game.bank_run_kut()
				Ses.play("kut_banka")
				hud.flash_msg = "%d Kut Umay'a ulaştı." % saved
				hud.flash_t = 3.0
				if level.player:
					FX.soul(level.player.center(), Color(0.6, 1.0, 1.0), 30)
			hud.mode = "umay"
		"demirci":
			Ses.play("ors")
			hud.mode = "demirci"
		"ozan":
			if not Adlar.pending().is_empty():
				_ad_toreni()
				return
			Ses.play("npc_1")
			hud.ozan_i = randi() % 4
			hud.mode = "ozan"


func _on_died() -> void:
	var saved := Game.lose_run_kut()
	hud.flash_msg = ("Ruh Düğümü %d Kut kurtardı." % saved) if saved > 0 else ""
	hud.mode = "dead"
	Ses.music("baslik", 2.5)
	get_tree().paused = true


func _on_scroll(p: Pickup) -> void:
	scroll_pickup = p
	hud.sel = 0
	hud.mode = "tilsim"
	Ses.play("ui_ac")
	get_tree().paused = true


func _on_slot_request(p: Pickup) -> void:
	## İki uygun yuva da dolu: hangisinin değişeceğini oyuncu seçer (oyun durur).
	slot_pickup = p
	var opts: Array = level.slot_options(p.item)
	hud.slot_opts = opts
	hud.sel = maxi(0, opts.find(level.natural_slot(p.item)))
	hud.mode = "slot"
	hud.open_anim()
	Ses.play("ui_ac")
	get_tree().paused = true


func _finish_slot(slot: String) -> void:
	if slot != "" and is_instance_valid(slot_pickup) and level:
		level.equip(slot_pickup, slot)
		Ses.play("esya_degis")
	else:
		Ses.play("ui_iptal")
	slot_pickup = null
	_start_play()


func _apply_scroll(sel: int) -> void:
	var keys := ["kurt", "kartal", "ayi"]
	var k: String = keys[sel]
	Game.run["ongun"][k] = int(Game.run["ongun"][k]) + 1
	var hp_gain := float(Game.run["max_hp"]) * (0.15 if k == "ayi" else 0.06)
	Game.run["max_hp"] = float(Game.run["max_hp"]) + hp_gain
	Game.run["hp"] = minf(float(Game.run["max_hp"]), float(Game.run["hp"]) + hp_gain + float(Game.run["max_hp"]) * 0.1)
	Game.run["scrolls"] = int(Game.run.get("scrolls", 0)) + 1
	Ses.play("tilsim_sec")
	Ses.play("seviye", -4.0)
	if level and level.player:
		var col := Color.from_string(Data.items["ongun"][k]["color"], Color.WHITE)
		FX.ring(level.player.center(), 40, col, 0.4)
		FX.soul(level.player.center(), col, 24)
		FX.text(level.player.center() + Vector2(0, -36), "%s +1" % Data.items["ongun"][k]["name"], col, 9)
		level.player.vis_scale = Vector2(0.85, 1.15)
	if is_instance_valid(scroll_pickup):
		level.pickups.erase(scroll_pickup)
		scroll_pickup.queue_free()
	scroll_pickup = null
	_start_play()


func _unhandled_input(event: InputEvent) -> void:
	var go: bool = event.is_action_pressed("zipla") or (event is InputEventKey and event.pressed and event.physical_keycode == KEY_ENTER)
	match hud.mode:
		"title":
			if go:
				hud.mode = "intro"
				hud.intro_i = 0
				Ses.play("ui_onay")
		"intro":
			if event.is_action_pressed("duraklat"):
				_after_intro()
			elif go:
				hud.intro_i += 1
				if hud.intro_i >= Data.story["intro"].size():
					_after_intro()
		"dead":
			if go:
				_new_run()
				_after_intro()
		"done":
			if go:
				_next_level()
		"tilsim":
			if event.is_action_pressed("sol"):
				hud.sel = (hud.sel + 2) % 3
				Ses.play("ui_gez")
			elif event.is_action_pressed("sag"):
				hud.sel = (hud.sel + 1) % 3
				Ses.play("ui_gez")
			elif event.is_action_pressed("etkiles") or go:
				_apply_scroll(hud.sel)
		"slot":
			var opts: Array = hud.slot_opts
			if event.is_action_pressed("sol") or event.is_action_pressed("sag") or event.is_action_pressed("yukari") or event.is_action_pressed("asagi"):
				hud.sel = 1 - hud.sel
				Ses.play("ui_gez")
			elif event.is_action_pressed("saldiri1") and "melee" in opts:
				_finish_slot("melee")
			elif event.is_action_pressed("saldiri2") and "second" in opts:
				_finish_slot("second")
			elif event.is_action_pressed("techizat1") and "g1" in opts:
				_finish_slot("g1")
			elif event.is_action_pressed("techizat2") and "g2" in opts:
				_finish_slot("g2")
			elif event.is_action_pressed("etkiles") or go:
				_finish_slot(String(opts[clampi(hud.sel, 0, opts.size() - 1)]))
			elif event.is_action_pressed("duraklat") or event.is_action_pressed("yuvarlan"):
				_finish_slot("")
		"demirci":
			var bps: Array = Game.meta.get("blueprints", [])
			if event.is_action_pressed("sol") and bps.size() > 0:
				hud.sel = (hud.sel + bps.size() - 1) % bps.size()
				Ses.play("ui_gez")
			elif event.is_action_pressed("sag") and bps.size() > 0:
				hud.sel = (hud.sel + 1) % bps.size()
				Ses.play("ui_gez")
			elif event.is_action_pressed("etkiles") and bps.size() > 0:
				var id: String = bps[clampi(hud.sel, 0, bps.size() - 1)]
				if Game.unlock(id):
					hud.flash_msg = "%s açıldı! Artık düşebilir." % Data.find_item(id).get("name", id)
					hud.sel = 0
					Ses.play("acilis")
				else:
					hud.flash_msg = "Yeterli Kut yok (%d gerekir)." % Game.unlock_cost(id)
					Ses.play("ui_sec", 0.0, 0.7)
				hud.flash_t = 2.0
			elif go or event.is_action_pressed("duraklat"):
				_start_play()
		"umay":
			var keys: Array = Game.UMAY.keys()
			if event.is_action_pressed("yukari") or event.is_action_pressed("sol"):
				hud.sel = (hud.sel + keys.size() - 1) % keys.size()
				Ses.play("ui_gez")
			elif event.is_action_pressed("asagi") or event.is_action_pressed("sag"):
				hud.sel = (hud.sel + 1) % keys.size()
				Ses.play("ui_gez")
			elif event.is_action_pressed("etkiles"):
				var id: String = keys[hud.sel]
				if Game.umay_buy(id):
					hud.flash_msg = "%s: seviye %d." % [Game.UMAY[id][0], Game.umay_level(id)]
					Ses.play("acilis")
					if id == "sise":
						Game.run["max_flasks"] = int(Game.run["max_flasks"]) + 1
						Game.run["flasks"] = int(Game.run["flasks"]) + 1
					elif id == "can":
						Game.run["max_hp"] = float(Game.run["max_hp"]) * 1.1
						Game.run["hp"] = float(Game.run["hp"]) * 1.1
				else:
					hud.flash_msg = "Yeterli Kut yok." if Game.umay_cost(id) >= 0 else "Bu armağan tamamlandı."
					Ses.play("ui_sec", 0.0, 0.7)
				hud.flash_t = 2.0
			elif go or event.is_action_pressed("duraklat"):
				_start_play()
		"ad":
			if (go or event.is_action_pressed("etkiles") or event.is_action_pressed("duraklat")) and hud.ad_t > 1.2:
				if not Adlar.pending().is_empty():
					_ad_toreni()
				else:
					_start_play()
		"ozan":
			if go or event.is_action_pressed("etkiles"):
				hud.ozan_i += 1
				Ses.play("npc_%d" % (1 + hud.ozan_i % 3))
				if hud.ozan_i >= 4:
					_start_play()
			elif event.is_action_pressed("duraklat"):
				_start_play()
		"play":
			if event.is_action_pressed("duraklat"):
				get_tree().paused = not get_tree().paused


func _ad_toreni() -> void:
	## Ozan kopuzunu alır, destanı anlatır, yiğide adını koyar
	var id: String = Adlar.pending()[0]
	Adlar.grant(id)
	hud.ad_id = id
	hud.ad_t = 0.0
	hud.mode = "ad"
	get_tree().paused = true
	Ses.play("ad_toren", 0.0)
	if level and level.player:
		FX.soul(level.player.center(), Color(1.0, 0.85, 0.45), 30)


func _after_intro() -> void:
	## Hikâyeden (ya da ölümden) sonra: bekleyen parşömen varsa Demirci'ye uğra.
	if not Game.meta.get("blueprints", []).is_empty():
		hud.mode = "demirci"
		hud.sel = 0
		get_tree().paused = true
	else:
		_start_play()


func _start_play() -> void:
	hud.mode = "play"
	hud._card_t = 0.0
	get_tree().paused = false


# ------------------------------------------------------------------ otomatik test (--otomatik)
var _auto_t := 0.0
var _auto_pressed: Array = []
var _auto_last_x := 0.0
var _auto_stuck := 0.0
var _sc_t := 0.0
var _sc_step := -1
var _sc_hold := ""


func _lab(delta: float) -> void:
	## Savuruş laboratuvarı: düşman yok, karakter sabit; her savuruş tipi sırayla, aralarında boşluk.
	if hud.mode != "play" or level == null or level.player == null:
		return
	var pl: Player = level.player
	if _sc_step < 0:
		_sc_step = 0
		var tx := 40
		pl.global_position = Vector2(tx * 24.0, level.surface_y(tx) * 24.0 - 2)
		pl.facing = 1
		Game.camera.reset_smoothing.call_deferred()
	for e in get_tree().get_nodes_in_group("dusman"):
		e.queue_free()
	_sc_t += delta
	var f := int(_sc_t * 60.0)
	# v5: silaha özgü savuruşlar (hepsi sağa bakar; kontak sayfasında kol pozları karşılaştırılır)
	var order := ["diag_down", "diag_up", "cross_x", "overhead_2h", "ground_drag", "sweep_low", "reverse_grip", "twirl", "windmill", "pole_thrust",
		"pole_sweep", "reap", "rake", "whip_crack", "axe_hook", "iai", "uppercut_2h", "slam_2h", "stab_heavy", "helicopter"]
	var items := ["alp_kilici", "alp_kilici", "alp_kilici", "ulu_kilic", "ulu_kilic", "ayaz_kilici", "yatagan", "ay_palasi", "gurz", "kargi",
		"teber", "erlik_tirpani", "kurt_pencesi", "kement", "savas_baltasi", "yildirim_kilici", "dag_cekici", "dag_cekici", "kargi", "teber"]
	if f >= 30 and f % 80 == 30 and _lab_i < order.size():
		pl.facing = 1
		pl.debug_swing(order[_lab_i], items[_lab_i])
		_lab_i += 1


func _showcase(delta: float) -> void:
	if lab:
		_lab(delta)
		return
	## --sahne: düz arenada dövüş gösterisi. Silahlar sırayla değişir, düşmanlar düzenli gelir;
	## efekt ve animasyonları çekim için güvenilir biçimde tekrar eder.
	if hud.mode != "play" or level == null or level.player == null:
		if hud.mode == "tilsim":
			_apply_scroll(0)
		return
	for a in _auto_pressed:
		Input.action_release(a)
	_auto_pressed.clear()
	var pl: Player = level.player
	var TSx := float(Level.TS)
	if _sc_step < 0:
		_sc_step = 0
		var tx := 4
		pl.global_position = Vector2(tx * TSx, level.surface_y(tx) * TSx - 2)
		pl.facing = 1
		for e in get_tree().get_nodes_in_group("dusman"):
			e.queue_free()
		Game.camera.reset_smoothing.call_deferred()
	_sc_t += delta
	Game.run["hp"] = 100.0
	pl.inv_t = maxf(pl.inv_t, 0.0)
	var t := _sc_t
	var tx0 := int(pl.global_position.x / TSx)
	# düşman akışı: her 2.6 sn'de sağdan bir kurt; 9. sn'de balbal, 19. sn'de iye
	if int(t * 60.0) % 156 == 30:
		level.spawn_enemy("kara_boru", Vector2((tx0 + 6) * TSx, level.surface_y(tx0 + 6) * TSx - 1))
	if int(t * 60.0) == 9 * 60:
		level.spawn_enemy("balbal", Vector2((tx0 + 6) * TSx, level.surface_y(tx0 + 6) * TSx - 1))
	if int(t * 60.0) == 19 * 60:
		level.spawn_enemy("agac_iyesi", Vector2((tx0 + 6) * TSx, level.surface_y(tx0 + 6) * TSx - 1))
	if int(t * 60.0) == 28 * 60:
		level.spawn_enemy("surale", Vector2((tx0 + 6) * TSx, level.surface_y(tx0 + 6) * TSx - 1))
	if int(t * 60.0) == 36 * 60:
		level.spawn_enemy("arcura", Vector2((tx0 + 6) * TSx, level.surface_y(tx0 + 6) * TSx - 1))
	# silah programı
	var sched := [[0.0, "ulu_kilic"], [7.0, "dag_cekici"], [12.0, "ruh_kilici"], [17.0, "ay_palasi"], [22.0, "yildirim_kilici"], [27.0, "teber"], [32.0, "erlik_tirpani"], [37.0, "gurz"], [42.0, "alp_kilici"], [47.0, "bozgun_kilici"], [52.0, "bori_hanceri"], [56.0, "tulpar_mizragi"]]
	for s in sched:
		if int(t * 60.0) == int(float(s[0]) * 60.0):
			var mat := "demir"
			match String(s[1]):
				"pala":
					mat = "gok_demiri"
				"teber":
					mat = "od_tasi"
				"ayaz_kilici":
					mat = "ayaz"
			Game.run["slots"]["melee"] = ItemGen.roll(s[1], 1, mat, 1)
			if s[1] == "erlik_tirpani":
				Game.run["slots"]["melee"]["affixes"].append({"id": "zehirleme", "v": 100.0})
			if s[1] == "teber":
				Game.run["slots"]["melee"]["affixes"].append({"id": "yanma", "v": 100.0})
			if s[1] == "ayaz_kilici":
				Game.run["slots"]["melee"]["affixes"].append({"id": "dondurma", "v": 60.0})
			FX.text(pl.center() + Vector2(0, -40), Game.run["slots"]["melee"]["name"], Color(1, 0.9, 0.6), 9)
	var sched2 := [[0.0, "od_oklari"], [8.0, "saganak_yayi"], [16.0, "tufan_yayi"], [24.0, "gok_asasi"], [32.0, "akinci_yayi"], [40.0, "turk_yayi"]]
	for s in sched2:
		if int(t * 60.0) == int(float(s[0]) * 60.0):
			Game.run["slots"]["second"] = ItemGen.roll(s[1], 2, "demir", 1)
	var sched3 := [[3.0, "davul_totemi"], [15.0, "ayaz_tilsimi"], [25.0, "yel_tilsimi"], [35.0, "ok_yagmuru"], [45.0, "kartal_cagrisi"]]
	for s in sched3:
		if int(t * 60.0) == int(float(s[0]) * 60.0):
			Game.run["slots"]["g1"] = ItemGen.roll(s[1], 1, "demir", 0)
			pl.cd["g1"] = 0.0
	# saldırı ritmi: gürz basılı tutulur, diğerleri tıklanır; arada yuvarlanma ve yay
	var cur: String = Game.run["slots"]["melee"].get("id", "")
	var f := int(t * 60.0)
	if cur != "":
		# 150 karelik turlar: A zincir (art arda), B bas-bas-bekle-bas (bekleme bitirişi), C basılı tut (ağır saldırı)
		var cyc := (f / 150) % 5
		var ph := f % 150
		if cyc == 0 and ph in [0, 16, 32, 48, 64]:
			_tap("saldiri1")
		elif cyc == 1 and ph in [0, 16, 78]:
			_tap("saldiri1")
		elif cyc == 2 and ph < 70:
			Input.action_press("saldiri1")
			_auto_pressed.append("saldiri1")
		elif cyc == 3:
			# göğe savur -> zıpla -> hava kombosu -> kartal dalışı
			if ph < 4:
				Input.action_press("yukari")
				_auto_pressed.append("yukari")
				if ph == 1:
					_tap("saldiri1")
			if ph == 18:
				_tap("zipla")
			if ph in [24, 36, 48]:
				_tap("saldiri1")
			if ph >= 62 and ph < 70:
				Input.action_press("asagi")
				_auto_pressed.append("asagi")
				if ph == 64:
					_tap("saldiri1")
		elif cyc == 4:
			# yuvarlan -> dönüş kesiği; koş -> akın kesiği; çömel -> diz biçen
			if ph == 0:
				_tap("yuvarlan")
			if ph == 20:
				_tap("saldiri1")
			if ph >= 50 and ph < 95:
				Input.action_press("yuvarlan")
				_auto_pressed.append("yuvarlan")
				Input.action_press("sag" if pl.facing > 0 else "sol")
				_auto_pressed.append("sag" if pl.facing > 0 else "sol")
				if ph == 90:
					_tap("saldiri1")
			if ph >= 110 and ph < 130:
				Input.action_press("asagi")
				_auto_pressed.append("asagi")
				if ph == 114:
					_tap("saldiri1")
	if f % 240 == 200:
		_tap("yuvarlan")
	if f % 300 >= 250 and f % 300 < 290:
		Input.action_press("saldiri2")
		_auto_pressed.append("saldiri2")
	if f % 300 == 200:
		_tap("techizat1")
	if f == 42 * 60 + 30:
		pl.kut = 100.0
		_tap("kut")
	if pl.wolf_t > 0.0:
		if f % 40 == 20:
			_tap("saldiri2")
		if f % 150 == 100:
			_tap("kut")
	# yüzü hep en yakın düşmana dön
	var best: Node = null
	var bd := 9999.0
	for e in get_tree().get_nodes_in_group("dusman"):
		if is_instance_valid(e) and not e.dead:
			var d: float = absf(e.global_position.x - pl.global_position.x)
			if d < bd:
				bd = d
				best = e
	if best and pl.atk.is_empty() and pl.roll_t <= 0.0:
		pl.facing = int(signf(best.global_position.x - pl.global_position.x))
		if bd > 70.0:
			_tap("sag" if pl.facing > 0 else "sol")


var _ekran := ""
var _ekran_t := 0


func _debug_screen() -> void:
	## --ekran=oyun|tilsim|yuva|duraklat|olum|umay|demirci : arayüz testleri ve ekran görüntüsü için
	_ekran_t += 1
	if _ekran in ["yay", "kilic"] and level and level.player:
		# yay: 45. karede ger, 85. karede bırak; kılıç: 45/70/95. karelerde zincir vuruş
		var pl0: Player = level.player
		for a0 in _auto_pressed:
			Input.action_release(a0)
		_auto_pressed.clear()
		for e in get_tree().get_nodes_in_group("dusman"):
			if e.global_position.distance_to(pl0.global_position) > 60.0:
				e.set_physics_process(false)
		if _ekran_t == 40:
			pl0.facing = 1
			if _ekran == "yay":
				Game.run["slots"]["second"] = ItemGen.roll("turk_yayi", 1, "demir", 1)
			pl0.on_equip()
		if _ekran == "yay":
			if _ekran_t == 45:
				Input.action_press("saldiri2")
			elif _ekran_t == 85:
				Input.action_release("saldiri2")
		elif _ekran_t in [45, 70, 95]:
			_tap("saldiri1")
		return
	if _ekran_t != 40 or level == null or level.player == null:
		return
	var pl: Player = level.player
	Game.run["slots"]["second"] = ItemGen.roll("savas_baltasi", 2, "gumus", 2)
	Game.run["slots"]["g2"] = ItemGen.roll("sifa_muskasi", 1, "tunc", 1)
	Game.run["ongun"] = {"kurt": 3, "kartal": 1, "ayi": 2}
	Game.run["gold"] = 245
	Game.run["kut"] = 37
	pl.kut = 65.0
	var it := ItemGen.roll("dag_cekici", 2, "altin", 3)
	level.drop_item(it, pl.global_position + Vector2(10, -20))
	match _ekran:
		"tilsim":
			hud.sel = 0
			hud.mode = "tilsim"
			get_tree().paused = true
		"yuva":
			await get_tree().create_timer(0.4).timeout
			var p := level.nearest_item(pl.global_position + Vector2(0, -10))
			if p:
				_on_slot_request(p)
		"duraklat":
			get_tree().paused = true
		"olum":
			_on_died()
		"umay":
			_on_npc("umay")
		"demirci":
			Game.meta["blueprints"] = ["saganak_yayi", "ayaz_kilici"]
			_on_npc("demirci")
		"baslik":
			hud.mode = "title"


func _physics_process(delta: float) -> void:
	if _ekran != "":
		_debug_screen()
		return
	if showcase:
		_showcase(delta)
		return
	if not auto_test:
		return
	match hud.mode:
		"tilsim":
			_apply_scroll(randi_range(0, 2))
			return
		"demirci":
			var bps: Array = Game.meta.get("blueprints", [])
			if not bps.is_empty():
				Game.unlock(bps[0])
			_start_play()
			return
		"umay":
			Game.umay_buy("can")
			_start_play()
			return
		"ozan":
			_start_play()
			return
		"done":
			_next_level()
			return
		"dead":
			_new_run()
			_start_play()
			return
	if hud.mode != "play" or level == null or level.player == null:
		return
	for a in _auto_pressed:
		Input.action_release(a)
	_auto_pressed.clear()
	_auto_t += delta
	var t := _auto_t
	var pl: Player = level.player
	if pl.dead:
		return
	Input.action_press("sag")
	if int(t * 60.0) % 23 == 0:
		_tap("saldiri1")
	# v9: koşu (Shift basılı) ve çömelerek saldırı yolları da sınanır
	var f9 := int(t * 60.0) % 700
	if f9 >= 200 and f9 < 330:
		Input.action_press("yuvarlan")
		_auto_pressed.append("yuvarlan")
	if f9 >= 420 and f9 < 470:
		Input.action_press("asagi")
		_auto_pressed.append("asagi")
		if f9 % 12 == 0:
			_tap("saldiri1")
		if f9 == 450:
			Input.action_press("saldiri2")
			_auto_pressed.append("saldiri2")
	if level.hub and int(t * 60.0) % 45 == 0:
		_tap("etkiles")
	# duvara takıldıysa: çift zıpla + yuvarlan
	if absf(pl.global_position.x - _auto_last_x) < 2.0:
		_auto_stuck += delta
	else:
		_auto_stuck = 0.0
	_auto_last_x = pl.global_position.x
	if _auto_stuck > 1.2 and int(t * 60.0) % 20 == 0:
		_tap("zipla")
	if _auto_stuck > 1.2 and int(t * 60.0) % 20 == 12:
		_tap("yuvarlan")
	if int(t * 60.0) % 97 == 0:
		_tap("zipla")
	if int(t * 60.0) % 101 == 50:
		_tap("zipla")
	if int(t * 60.0) % 173 == 0:
		_tap("yuvarlan")
	if int(t * 60.0) % 211 == 0:
		Input.action_press("saldiri2")
	if int(t * 60.0) % 211 == 40:
		Input.action_release("saldiri2")
	if int(t * 60.0) % 317 == 0:
		_tap("techizat1")
	if int(t * 60.0) % 401 == 0:
		_tap("etkiles")
	if int(t * 60.0) % 599 == 0:
		pl.kut = 100.0
		_tap("kut")
	if float(Game.run["hp"]) < 40.0:
		Game.run["hp"] = 100.0
	if Engine.get_physics_frames() % 300 == 0:
		print("[otomatik] biyom=%s stil=%s koridor=%d kare=%d t=%.1f ts=%.2f derinlik=%d x=%.0f y=%.0f zemin=%s öldürülen=%d altın=%d kut=%d yuva1=%s yuva2=%s düşman=%d mermi=%d parşömen=%d" % [level.biome.get("id", "?"), level.style, level.carved, Engine.get_physics_frames(), t, Engine.time_scale, int(Game.run["depth"]), pl.global_position.x, pl.global_position.y, str(pl.is_on_floor()), int(Game.run["kills"]), int(Game.run["gold"]), int(Game.run["kut"]), Game.run["slots"]["melee"].get("name", "-"), Game.run["slots"]["second"].get("name", "-"), get_tree().get_nodes_in_group("dusman").size(), level.proj_root.get_child_count(), Game.meta.get("blueprints", []).size()])


func _tap(a: String) -> void:
	Input.action_press(a)
	_auto_pressed.append(a)
