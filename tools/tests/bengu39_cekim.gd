extends Node
## v39 Bengü çekim aracı: hareket / saldırı kare dizileri + oyun içi tam ekran çekimler (önce / sonra karşılaştırması)
##   godot --path . --fixed-fps 60 -- --bengu=C:/mutlak/klasor --bengu_sayfa [--derinlik=5] --pencere=1920x1080
## Her bölüm <klasor>/<bolum>_NNN.png (oyuncu çevresinden kırpılmış, ayak alt %80 çizgisinde) yazar; tam ekran çekimler
## <klasor>/tam_<ad>.png. Kontak sayfası: tools/artgen/bengu39_sayfa.py.

var main: Node
var lv: Node
var pl: Player
var out_dir := ""
var spot := Vector2.ZERO

const ACTS := ["saldiri1", "saldiri2", "zipla", "yuvarlan", "sag", "sol", "yukari", "asagi", "techizat1", "techizat2", "sise", "kut"]


func _p(s: String) -> void:
	print("[bengu39] ", s)


func _f(n := 1) -> void:
	for i in n:
		await get_tree().physics_frame
		if pl:
			Game.run["hp"] = float(Game.run["max_hp"])


func _img() -> Image:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	if get_viewport().use_hdr_2d:
		if img.get_format() != Image.FORMAT_RGBA8 and img.get_format() != Image.FORMAT_RGB8:
			img.convert(Image.FORMAT_RGBA8)
		img.linear_to_srgb()
	return img


func _crop(name: String) -> void:
	var img: Image = await _img()
	var vs := Vector2(img.get_size())
	var sp: Vector2 = pl.get_global_transform_with_canvas().origin * vs / get_viewport().get_visible_rect().size
	var h := int(vs.y * 0.3)
	var w := int(h * 1.3)
	var r := Rect2i(int(sp.x - w * 0.5), int(sp.y - h * 0.8), w, h).intersection(Rect2i(Vector2i.ZERO, img.get_size()))
	img.get_region(r).save_png(out_dir.path_join(name + ".png"))


func _full(name: String) -> void:
	var img: Image = await _img()
	img.save_png(out_dir.path_join("tam_" + name + ".png"))
	_p("tam %s" % name)


func _release_all() -> void:
	for a in ACTS:
		Input.action_release(a)


func _reset(face := 1) -> void:
	_release_all()
	pl.global_position = spot
	pl.velocity = Vector2.ZERO
	pl.facing = face
	pl.inv_t = 0.0
	await _f(30)


func _seg(name: String, frames: int, every: int, press := {}, release := {}) -> void:
	## frames kare boyunca; press / release: {kare: [eylemler]}; her "every" karede bir kırpım
	var n := 0
	for i in frames:
		if press.has(i):
			for a in press[i]:
				Input.action_press(a)
		if release.has(i):
			for a in release[i]:
				Input.action_release(a)
		await _f()
		if i % every == 0:
			await _crop("%s_%03d" % [name, n])
			n += 1
	_release_all()
	_p("bölüm %s: %d kare" % [name, n])


func _equip(melee: String, second := "turk_yayi") -> void:
	Game.run["slots"]["melee"] = ItemGen.roll(melee, 1, "demir", 0)
	Game.run["slots"]["second"] = ItemGen.roll(second, 1, "demir", 0)
	pl.on_equip()


func run_all(m: Node, dir: String) -> void:
	main = m
	out_dir = dir
	DirAccess.make_dir_recursive_absolute(out_dir)
	await get_tree().create_timer(0.6).timeout
	lv = main.level
	_p("ekran=%s pencere=%s vp=%s" % [str(DisplayServer.screen_get_size()), str(get_window().size), str(get_viewport().get_texture().get_size())])
	pl = lv.player
	main.hud.set("_card_t", 100.0)
	for e in get_tree().get_nodes_in_group("dusman"):
		e.remove_from_group("dusman")
		e.queue_free()
	get_parent().lv = lv
	spot = get_parent()._find_spot() + Vector2(220, 0)   # iskelenin dışında, düz zemin
	_equip("alp_kilici")
	await _reset()
	await _f(60)
	await _full("durgun")
	# ---- hareket
	await _seg("idle", 96, 4)
	await _seg("run", 70, 2, {0: ["sag"]})
	await _full("kosu")
	await _reset()
	await _seg("jump", 80, 3, {0: ["zipla"]}, {16: ["zipla"]})
	await _reset()
	await _seg("roll", 30, 2, {0: ["yuvarlan"]}, {3: ["yuvarlan"]})
	await _reset()
	pl.take_hit(1.0, null, null, true)
	await _seg("hurt", 30, 2)
	# kahraman inişi: yüksekten düş, havada aşağı + zıpla
	await _reset()
	pl.global_position = spot - Vector2(0, 150)
	await _seg("hero", 80, 2, {8: ["asagi"], 10: ["zipla"]}, {14: ["zipla", "asagi"]})
	# ---- saldırılar
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
	# ---- oyun içi tam ekran: saldırı ortası ve yanında yaratıklar
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


func _seg_taps(name: String, frames: int, every: int, at: Array) -> void:
	var pr := {}
	var rl := {}
	for t in at:
		pr[int(t)] = ["saldiri1"]
		rl[int(t) + 3] = ["saldiri1"]
	await _seg(name, frames, every, pr, rl)
