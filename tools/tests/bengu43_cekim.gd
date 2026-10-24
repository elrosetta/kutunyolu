extends "res://tools/tests/bengu39_cekim.gd"
## v43 yeni Bengü çekim aracı (bengu39_cekim'in yardımcılarıyla): hareket, dönüş takibi (saç / kaftan / kuşak gecikmesi),
## dönüş + saldırı, silah aileleri, tırmanma ('tirman' / 'tirman_bekle' satırları) ve ölüm satırı + tam ekran çekimler.
##   godot --path . --resolution 1920x1080 --fixed-fps 60 --quit-after 12000 -- --bengu=C:/mutlak/klasor --bengu43_sayfa
##     --boss=kara_boru_han --pencere=1920x1080 --grafik=2 [--derinlik=5]
## Kontak sayfası: python tools/artgen/bengu39_sayfa.py <klasor> out.jpg idle:0:24:3 donus:0:20 ...


func _p(s: String) -> void:
	print("[bengu43] ", s)


func _satir(name: String, an: String, frames: int, every: int) -> void:
	## Oyuncu fiziği durdurulup gövde satırı doğrudan oynatılır (tırmanma durumu ky-harita43'te; burada yalnızca çizim)
	pl.set_physics_process(false)
	pl.arm_root.visible = false
	pl.arm_root_b.visible = false
	pl.anim.play(an, true)
	var n := 0
	for i in frames:
		await get_tree().physics_frame
		if i % every == 0:
			await _crop("%s_%03d" % [name, n])
			n += 1
	pl.set_physics_process(true)
	_p("satır %s: %d kare" % [name, n])


func run_all(m: Node, dir: String) -> void:
	main = m
	out_dir = dir
	DirAccess.make_dir_recursive_absolute(out_dir)
	await get_tree().create_timer(0.6).timeout
	lv = main.level
	pl = lv.player
	main.hud.set("_card_t", 100.0)
	for e in get_tree().get_nodes_in_group("dusman"):
		e.remove_from_group("dusman")
		e.queue_free()
	get_parent().lv = lv
	spot = get_parent()._find_spot() + Vector2(220, 0)
	_equip("alp_kilici")
	await _reset()
	await _f(60)
	await _full("durgun")
	await _seg("idle", 120, 4)
	await _seg("run", 70, 2, {0: ["sag"]})
	await _full("kosu")
	# dönüş takibi: sağa koşarken sola dön (saç, kaftan etekleri ve kuşak gecikmeyle savrulur)
	await _reset()
	await _seg("donus", 60, 2, {0: ["sag"], 28: ["sol"]}, {28: ["sag"]})
	# dönüş + saldırı
	await _reset()
	await _seg("donus_saldiri", 60, 2, {0: ["sag"], 24: ["sol"], 27: ["saldiri1"]}, {24: ["sag"], 30: ["saldiri1", "sol"]})
	await _reset()
	await _seg("jump", 80, 3, {0: ["zipla"]}, {16: ["zipla"]})
	await _reset()
	await _seg("roll", 30, 2, {0: ["yuvarlan"]}, {3: ["yuvarlan"]})
	await _reset()
	pl.take_hit(1.0, null, null, true)
	await _seg("hurt", 30, 2)
	await _reset()
	pl.global_position = spot - Vector2(0, 150)
	await _seg("hero", 80, 2, {8: ["asagi"], 10: ["zipla"]}, {14: ["zipla", "asagi"]})
	await _reset()
	await _seg_taps("kilic", 120, 2, [0, 16, 32, 48])
	await _reset()
	await _seg("agir", 120, 3, {0: ["saldiri1"]}, {60: ["saldiri1"]})
	_equip("kargi")
	await _reset()
	await _seg_taps("mizrak", 120, 2, [0, 18, 36])
	_equip("gurz")
	await _reset()
	await _seg_taps("gurz", 150, 3, [0, 24, 48])
	_equip("alp_kilici")
	await _reset()
	await _seg("yay", 70, 3, {0: ["saldiri2"]}, {40: ["saldiri2"]})
	# tırmanma + ölüm satırları (havada asılı: zincir / ip yerine)
	await _reset()
	pl.global_position = spot - Vector2(0, 40)
	await _satir("tirman", "tirman", 48, 2)
	await _reset()
	pl.global_position = spot - Vector2(0, 40)
	await _satir("tirman_bekle", "tirman_bekle", 32, 4)
	await _reset()
	await _satir("olum", "olum", 40, 3)
	await _reset()
	Input.action_press("saldiri1")
	await _f(3)
	Input.action_release("saldiri1")
	await _f(9)
	await _full("saldiri")
	await _reset()
	var ids := ["balbal", "agac_iyesi"]
	match String(lv.biome.get("id", "otuken")):
		"sahmeran":
			ids = ["yilan_muhafiz", "su_iyesi"]
		"tamu":
			ids = ["tamu_bekcisi", "od_iyesi"]
	var k := 0
	for id in ids:
		var e: Node = lv.spawn_enemy(id, spot + Vector2(70 + 70 * k, 0))
		if e:
			e.remove_from_group("dusman")
			await _f(2)
			e.process_mode = Node.PROCESS_MODE_DISABLED
		k += 1
	await _f(20)
	await _full("yaratiklarla")
	_p("BITTI")
	get_tree().quit()
