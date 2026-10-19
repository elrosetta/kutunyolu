extends Node
## Mürekkep fırçası laboratuvarı (stil v2 savuruş izi ve vuruş efektleri çekimi):
##   godot --path . --write-movie C:/x/f.png --fixed-fps 30 --quit-after 900 -- --firca[=silah1,silah2:malzeme,...]
##   [--firca_bos] (düşmansız: yalnız iz) [--firca_adim=zincir,agir,ozel] (sıra)
## Her silahta: 3 vuruşluk zincir (son vuruş bitiriş), basılı tutulan ağır saldırı, savuşturma + kusursuz kaçış süsü.
## Çıktıda "[firca] silah adım kare=N" satırları kareleri bulmak için.

var main: Node
var weapons: Array = ["alp_kilici", "dag_cekici", "kargi", "ikiz_bicak", "kement", "erlik_tirpani", "ayaz_kilici", "od_kamcisi"]
var with_enemy := true


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for arg in OS.get_cmdline_user_args():
		var a := String(arg)
		if a.begins_with("--firca="):
			weapons = Array(a.trim_prefix("--firca=").split(","))
		elif a == "--firca_bos":
			with_enemy = false
		elif a == "--firca_kombo":
			kombo = true
		elif a == "--firca_tam":
			tam = true
		elif a == "--firca_uzak":
			uzak = true
		elif a.begins_with("--anlik="):
			snap_dir = a.trim_prefix("--anlik=")
	if uzak:
		_uzak.call_deferred()
		return
	if kombo:
		_kombo.call_deferred()
		return
	_run.call_deferred()


## v23 kare şeridi: -- --firca=w1,w2 --firca_kombo --anlik=<klasör> [--firca_bos] (headless değil, --fixed-fps 60):
## her silahta 3 vuruşluk zincirin (her savuruşun son anında yeniden basılır) HER karesi, oyuncunun çevresinden
## kırpılmış olarak <klasör>/<silah>_<kare>.png; "[firca] kombo <silah> kareler=N" satırı.
var kombo := false
var tam := false    # v27: --firca_tam: zincirin tamamı (4-5 adımlı silahlarda bitiriş dahil; eski: 3 savuruş)
var uzak := false   # v27: --firca_uzak: ikincil silah (yay: gerip bırak, fırlatma, büyü) kare şeridi
var snap_dir := ""
const CROP := Vector2i(640, 480)


func _crop_snap(pl: Node2D, path: String) -> void:
	await RenderingServer.frame_post_draw
	if snap_dir == "" or DisplayServer.get_name() == "headless":
		return
	var vp := pl.get_viewport()
	var img := vp.get_texture().get_image()
	if vp.use_hdr_2d:
		if img.get_format() != Image.FORMAT_RGBA8 and img.get_format() != Image.FORMAT_RGB8:
			img.convert(Image.FORMAT_RGBA8)
		img.linear_to_srgb()
	var sp := pl.get_global_transform_with_canvas().origin * (Vector2(img.get_size()) / vp.get_visible_rect().size)
	var r := Rect2i(Vector2i(int(sp.x) - CROP.x / 2 + 60, int(sp.y) - CROP.y + 120), CROP)
	r.position = r.position.clamp(Vector2i.ZERO, img.get_size() - CROP)
	img.get_region(r).save_png(path)


func _kombo() -> void:
	await _wait(1.2)
	var pl: Node = main.level.player
	var x0: float = pl.global_position.x
	for w in weapons:
		var parts := String(w).split(":")
		var id := parts[0]
		var mat := parts[1] if parts.size() > 1 else "demir"
		_clear_enemies()
		pl.global_position.x = x0
		pl.velocity = Vector2.ZERO
		pl.facing = 1
		Game.run["slots"]["melee"] = ItemGen.roll(id, 1, mat, 0)
		pl.on_equip()
		await _wait(0.4)
		if with_enemy:
			_spawn(pl, 40.0)
		await _wait(0.3)
		pl.facing = 1
		var n := 0
		var swings := 0
		var last: Dictionary = {}
		var held := 0
		var want := 3
		if tam:
			want = (Player._combo_for(pl.slot("melee"))["chain"] as Array).size()
		Input.action_press("saldiri1")
		held = 2
		while n < (200 if not tam else 360):
			await get_tree().physics_frame
			n += 1
			if held > 0:
				held -= 1
				if held == 0:
					Input.action_release("saldiri1")
			if not pl.atk.is_empty() and not is_same(pl.atk, last):
				last = pl.atk
				swings += 1
			# hızlı oyuncu: savuruşun son anında yeniden bas (3 savuruşa dek)
			if swings < want and held == 0 and not pl.atk.is_empty() and pl._to_chain() <= 0.05:
				Input.action_press("saldiri1")
				held = 2
			if tam and not pl.atk.is_empty():
				var ph := String(SanatAnim._phase(pl)[0]) if pl.atk.has("art") else String(pl.atk.get("phase", ""))
				print("[firca] faz %s %d %d %s %s" % [id, n, swings, ph, String(pl.atk["c"].get("s", ""))])
			await _crop_snap(pl, "%s/%s_%03d.png" % [snap_dir, id, n])
			if swings >= want and pl.atk.is_empty():
				break
		Input.action_release("saldiri1")
		print("[firca] kombo %s kareler=%d savurus=%d" % [id, n, swings])
		await _wait(0.6)
	get_tree().quit()


## v27 ikincil silah şeridi: -- --firca=turk_yayi,cirit,gok_asasi --firca_uzak --anlik=<klasör>: yay 0,7 sn gerilip
## bırakılır, fırlatma / büyü bir kez basılır; HER kare kırpılmış PNG (<silah>_<kare>.png)
func _uzak() -> void:
	await _wait(1.2)
	var pl: Node = main.level.player
	var x0: float = pl.global_position.x
	for w in weapons:
		var id := String(w)
		_clear_enemies()
		pl.global_position.x = x0
		pl.velocity = Vector2.ZERO
		pl.facing = 1
		Game.run["slots"]["second"] = ItemGen.roll(id, 1, "demir", 0)
		pl.on_equip()
		pl.cd[pl.sec_slot] = 0.0
		await _wait(0.4)
		if with_enemy:
			_spawn(pl, 90.0)
		await _wait(0.3)
		pl.facing = 1
		var kind := String(pl.slot(pl.sec_slot).get("kind", ""))
		var hold := 44 if kind == "bow" else 2
		Input.action_press(pl.sec_act)
		var n := 0
		while n < 110:
			await get_tree().physics_frame
			n += 1
			if n == hold:
				Input.action_release(pl.sec_act)
			await _crop_snap(pl, "%s/%s_%03d.png" % [snap_dir, id, n])
		Input.action_release(pl.sec_act)
		print("[firca] uzak %s kareler=%d tur=%s" % [id, n, kind])
		await _wait(0.4)
	get_tree().quit()


func _wait(s: float) -> void:
	await get_tree().create_timer(s, true, false, false).timeout


func _p(s: String) -> void:
	var sp := Vector2.ZERO
	if main and main.level and main.level.player:
		var pl: Node2D = main.level.player
		var vp := pl.get_viewport()
		sp = pl.get_global_transform_with_canvas().origin * (Vector2(vp.get_window().size) / vp.get_visible_rect().size)
	print("[firca] %s kare=%d ekran=%d,%d" % [s, Engine.get_frames_drawn(), int(sp.x), int(sp.y)])


func _clear_enemies() -> void:
	for e in get_tree().get_nodes_in_group("dusman"):
		e.queue_free()


func _spawn(pl: Node, dx: float) -> void:
	var en: Node = main.level.spawn_enemy("kara_boru", pl.global_position + Vector2(dx, 0), false)
	if en:
		en.set_physics_process(false)
		en.facing = -1
		en.anim.set_facing(-1)
		if "hp" in en:
			en.hp = 1.0e6
		if "max_hp" in en:
			en.max_hp = 1.0e6


func _run() -> void:
	await _wait(1.2)
	var pl: Node = main.level.player
	var x0: float = pl.global_position.x
	for w in weapons:
		var parts := String(w).split(":")
		var id := parts[0]
		var mat := parts[1] if parts.size() > 1 else "demir"
		_clear_enemies()
		pl.global_position.x = x0
		pl.velocity = Vector2.ZERO
		pl.facing = 1
		Game.run["slots"]["melee"] = ItemGen.roll(id, 1, mat, 0)
		pl.on_equip()
		await _wait(0.25)
		if with_enemy:
			_spawn(pl, 36.0)
		await _wait(0.2)
		for k in 3:
			pl.facing = 1
			_p("%s zincir%d" % [id, k + 1])
			Input.action_press("saldiri1")
			await _wait(0.06)
			Input.action_release("saldiri1")
			await _wait(0.42)
		await _wait(0.5)
		pl.facing = 1
		_p("%s agir" % id)
		Input.action_press("saldiri1")
		await _wait(0.85)
		Input.action_release("saldiri1")
		_p("%s agir_birak" % id)
		await _wait(1.0)
	_clear_enemies()
	_p("savustur")
	if pl.has_method("_parry"):
		pl._parry({}, null, null)
	await _wait(0.8)
	_p("kusursuz")
	if pl.has_method("_perfect_dodge"):
		pl._perfect_dodge(null)
	await _wait(1.2)
	_p("bitti")
