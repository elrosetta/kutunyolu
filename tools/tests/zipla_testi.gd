extends Node
## v34 zıplama / Kahraman İnişi testi (mekanik testinin alt kipi; boss arenası düz ve 30 karo yüksek):
##   godot --headless --path . --fixed-fps 60 --quit-after 6000 -- --mekanik --zipla --boss
## Ölçer (60 Hz kare): tam / dokunuş zıplama yüksekliği, tepeye varış, havada kalış, koşu zıplaması yatay menzili,
## çift zıplama toplam yüksekliği, coyote (kenardan düştükten sonra kaç kare zıplanır), zıplama tamponu (inişten önce
## basış), düşüş hızı / süresi, 1 karoluk basamağa zıplamadan çıkış, 2-3-4 karoluk kenara tutunma, tek yönlü
## platformdan aşağı + zıpla ile iniş (dalış değil), Kahraman İnişi (düşüş hızı, isabet, hasar yok, sersemleme yok,
## poz) ve yüksek normal düşüşte sersemleme / hasar. Erişim: LevelGen._moves modeline (4 karo yukarı, ±5 sütun) göre.
## Çıktı: "[zipla] ..." satırları, sonda "[zipla] OZET hata=n". --anlik=<klasör> (pencereli): kare çekimleri.

var main: Node
var lv: Node
var pl: Node   # (eski sürümle karşılaştırma için tipsiz)
var spot := Vector2.ZERO
var hata := 0
var _blocks: Array = []
var _snap_dir := ""
var _snap_n := 0
const TS := 24.0
const ACTS := ["saldiri1", "saldiri2", "zipla", "yuvarlan", "sag", "sol", "yukari", "asagi"]


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--anlik="):
			_snap_dir = String(arg).trim_prefix("--anlik=")
	_run.call_deferred()


func _p(s: String) -> void:
	print("[zipla] ", s)


func _ok(cond: bool, what: String) -> void:
	if not cond:
		hata += 1
		_p("HATA: " + what)


func _f(n := 1) -> void:
	for i in n:
		await get_tree().physics_frame
		Game.run["hp"] = maxf(float(Game.run["hp"]), 1.0)


func _release_all() -> void:
	for a in ACTS:
		Input.action_release(a)


func _has(f: String) -> bool:
	return f in pl


func _place(pos: Vector2, settle := 12) -> void:
	_release_all()
	pl.global_position = pos
	pl.velocity = Vector2.ZERO
	pl.facing = 1
	pl.roll_t = 0.0
	pl.hurt_t = 0.0
	pl.inv_t = 99.0
	pl.jump_buf = 0.0
	pl.drop_t = 0.0
	pl.mantle_t = 0.0
	pl._fall_peak = 0.0
	if _has("hero_t"):
		pl.hero_t = -1.0
		pl.hero_pose_t = 0.0
		pl.fall_stun_t = 0.0
		pl._air_top = pos.y
	var cam: Camera2D = Game.camera
	if cam:
		if _snap_dir != "":
			cam.position_smoothing_enabled = false   # çekimde kamera oyuncuyu kaçırmasın
		cam.reset_smoothing()
	await _f(settle)


func _block(tx: float, tiles_w: int, tiles_h: int) -> StaticBody2D:
	## Arenaya katı blok (görünür mürekkep kutusu): sol kenar tx karo, taban arena zemini
	var floor_y := spot.y + 1.0
	var b := StaticBody2D.new()
	b.collision_layer = Game.LAYER_WORLD
	b.collision_mask = 0
	var cs := CollisionShape2D.new()
	var sh := RectangleShape2D.new()
	sh.size = Vector2(tiles_w * TS, tiles_h * TS)
	cs.shape = sh
	b.add_child(cs)
	b.position = Vector2(tx * TS + tiles_w * TS * 0.5, floor_y - tiles_h * TS * 0.5)
	var poly := Polygon2D.new()
	var hw := tiles_w * TS * 0.5
	var hh := tiles_h * TS * 0.5
	poly.polygon = PackedVector2Array([Vector2(-hw, -hh), Vector2(hw, -hh), Vector2(hw, hh), Vector2(-hw, hh)])
	poly.color = Color(0.13, 0.11, 0.15)
	b.add_child(poly)
	var edge := Line2D.new()
	edge.points = PackedVector2Array([Vector2(-hw, hh), Vector2(-hw, -hh), Vector2(hw, -hh), Vector2(hw, hh)])
	edge.width = 2.0
	edge.default_color = Color(0.82, 0.76, 0.66)
	b.add_child(edge)
	lv.add_child(b)
	_blocks.append(b)
	return b


func _clear_blocks() -> void:
	for b in _blocks:
		if is_instance_valid(b):
			b.queue_free()
	_blocks.clear()
	await _f(2)


func _snap(tag: String) -> void:
	if _snap_dir == "" or DisplayServer.get_name() == "headless":
		return
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	if get_viewport().use_hdr_2d:
		if img.get_format() != Image.FORMAT_RGBA8 and img.get_format() != Image.FORMAT_RGB8:
			img.convert(Image.FORMAT_RGBA8)
		img.linear_to_srgb()
	_snap_n += 1
	var out := "%s/z_%03d_%s.png" % [_snap_dir, _snap_n, tag]
	img.save_png(out)
	var sp: Vector2 = get_viewport().get_canvas_transform() * pl.global_position
	_p("anlik %s ekran=%d,%d boyut=%dx%d" % [out, int(sp.x), int(sp.y), img.get_width(), img.get_height()])


# ------------------------------------------------------------------ ölçümler
func _jump(hold: int, run := false, x_tile := 33.0, snap_tag := "", dbl := false) -> Dictionary:
	## Zıplama: hold kare basılı (büyük = tam). run: önce sağa koşu hızına çık
	var start := Vector2(x_tile * TS + 12.0, spot.y)
	await _place(start)
	if run:
		Input.action_press("sag")
		await _f(14)
	var y0: float = pl.global_position.y
	var x0: float = pl.global_position.x
	var top := y0
	var t_apex := 0
	var t_land := -1
	Input.action_press("zipla")
	var second := false
	for i in 150:
		if i == hold:
			Input.action_release("zipla")
		await _f()
		if dbl and not second and i > 3 and pl.velocity.y >= 0.0:
			Input.action_release("zipla")
			await _f()
			Input.action_press("zipla")   # tepede çift zıplama
			second = true
		if snap_tag != "" and i % 4 == 1:
			await _snap("%s_%02d" % [snap_tag, i])
		if pl.global_position.y < top - 0.01:
			top = pl.global_position.y
			t_apex = i + 1
		if i > 2 and pl.is_on_floor():
			t_land = i + 1
			break
	var dx: float = pl.global_position.x - x0
	if snap_tag != "":
		await _snap(snap_tag + "_inis")
	_release_all()
	return {"h": y0 - top, "apex": t_apex / 60.0, "air": t_land / 60.0, "dx": dx}


func _double_jump() -> Dictionary:
	await _place(Vector2(33.0 * TS + 12.0, spot.y))
	var y0: float = pl.global_position.y
	var top := y0
	Input.action_press("zipla")
	var second := false
	for i in 150:
		await _f()
		if not second and pl.velocity.y >= 0.0 and i > 3:
			Input.action_release("zipla")
			await _f()
			Input.action_press("zipla")
			second = true
		top = minf(top, pl.global_position.y)
		if i > 3 and pl.is_on_floor():
			break
	_release_all()
	return {"h": y0 - top}


func _coyote() -> int:
	## Platform kenarından yürüyüp düş; düştükten n kare sonra zıpla: zıplıyorsa n geçerli. En büyük geçerli n.
	var best := -1
	for n in [2, 4, 5, 6, 7, 8]:
		await _place(Vector2(44.0 * TS, 25.0 * TS - 1.0), 16)
		if not pl.is_on_floor():
			_p("coyote: platformda duramadı")
			return -1
		Input.action_press("sag")
		var left := -1
		for i in 60:
			await _f()
			if not pl.is_on_floor():
				left = i
				break
		if left < 0:
			continue
		await _f(n - 1)
		Input.action_press("zipla")
		await _f(2)
		var jumped: bool = pl.velocity.y < -250.0 and pl.air_jumps >= (2 if Game.has_lutuf("umay") else 1)
		_release_all()
		if jumped:
			best = n
	return best


func _buffer(early: int) -> bool:
	## Çift zıplama harcandıktan sonra, inişten "early" kare önce basılan zıplama inince çıkar mı?
	await _place(Vector2(33.0 * TS + 12.0, spot.y - 3.0 * TS), 1)
	# önce aynı düşüş tamponsuz: iniş karesi
	await _f(2)
	Input.action_press("zipla")
	await _f(2)
	Input.action_release("zipla")
	var land := -1
	for i in 120:
		await _f()
		if pl.is_on_floor():
			land = i
			break
	await _place(Vector2(33.0 * TS + 12.0, spot.y - 3.0 * TS), 1)
	await _f(2)
	Input.action_press("zipla")
	await _f(2)
	Input.action_release("zipla")
	var ok := false
	for i in 120:
		if i == land - early:
			Input.action_press("zipla")
		await _f()
		if i >= land and pl.velocity.y < -250.0:
			ok = i <= land + 1
			break
		if i > land + 4:
			break
	_release_all()
	return ok


func _fall(tiles: float) -> Dictionary:
	await _place(Vector2(33.0 * TS + 12.0, spot.y - tiles * TS), 1)
	var hp0 := float(Game.run["hp"])
	var vmax := 0.0
	var t := -1
	for i in 240:
		await _f()
		vmax = maxf(vmax, pl.velocity.y)
		if pl.is_on_floor():
			t = i + 1
			break
	await _f()
	var stun := float(pl.fall_stun_t) if _has("fall_stun_t") else 0.0
	var dmg := hp0 - float(Game.run["hp"])
	await _f(50)
	return {"t": t / 60.0, "vmax": vmax, "stun": stun, "dmg": dmg}


func _climb(tiles_h: int, jump_at := -1.0, hold := 40) -> Dictionary:
	## Sağa yürü (gerekirse bloğa jump_at px kala zıpla): bloğun üstüne çıkış süresi
	await _clear_blocks()
	var bx := 36.0
	_block(bx, 4, tiles_h)
	await _place(Vector2(31.0 * TS + 12.0, spot.y), 6)
	var top_y := spot.y + 1.0 - tiles_h * TS
	Input.action_press("sag")
	var jumped := -1
	var t := -1
	var touch := -1
	var mantles0 := int(pl.hero_stats["mantle"]) if _has("hero_stats") else 0
	var steps0 := int(pl.hero_stats["step"]) if _has("hero_stats") else 0
	for i in 150:
		await _f()
		if touch < 0 and bx * TS - pl.global_position.x <= 7.0:
			touch = i   # duvara değdi (yürüyüş)
		if jump_at >= 0.0 and jumped < 0 and bx * TS - pl.global_position.x <= jump_at:
			Input.action_press("zipla")
			jumped = i
		if jumped >= 0 and i - jumped == hold:
			Input.action_release("zipla")
		if jumped >= 0 and tiles_h >= 4 and i - jumped == 22:
			Input.action_release("zipla")
			await _f()
			Input.action_press("zipla")   # çift zıplama
		if pl.global_position.y <= top_y + 1.5 and pl.global_position.x > bx * TS + 4.0 and pl.is_on_floor():
			t = i + 1
			break
	_release_all()
	var from := float(jumped if jumped >= 0 else touch)
	var r := {"ok": t >= 0, "t": (t - from) / 60.0 if t >= 0 else -1.0, "jump": jumped >= 0,
		"mantle": (int(pl.hero_stats["mantle"]) - mantles0) if _has("hero_stats") else 0,
		"step": (int(pl.hero_stats["step"]) - steps0) if _has("hero_stats") else 0}
	await _clear_blocks()
	return r


func _drop_platform() -> Dictionary:
	await _place(Vector2(43.5 * TS, 25.0 * TS - 1.0), 16)
	var n0 := int(pl.hero_stats["n"]) if _has("hero_stats") else 0
	var y0: float = pl.global_position.y
	Input.action_press("asagi")
	await _f(2)
	Input.action_press("zipla")
	await _f(2)
	Input.action_release("zipla")
	await _f(14)
	var r := {"dropped": pl.global_position.y > y0 + 12.0, "dive": (int(pl.hero_stats["n"]) - n0) if _has("hero_stats") else 0}
	_release_all()
	await _f(40)
	return r


func _enemy(dx: float) -> Enemy:
	var e: Enemy = lv.spawn_enemy("kara_boru", spot + Vector2(dx, 0))
	e.max_hp = 99999.0
	e.hp = 99999.0
	e.speed = 0.0
	e.cd = 99.0
	e.aggro = false
	return e


func _clear_enemies() -> void:
	for e in get_tree().get_nodes_in_group("dusman"):
		e.remove_from_group("dusman")
		e.queue_free()


func _hero(tiles: float, snap := false) -> Dictionary:
	_clear_enemies()
	await _f(2)
	var foes := [_enemy(-40.0), _enemy(90.0), _enemy(190.0)]
	await _place(Vector2(33.0 * TS + 12.0, spot.y - tiles * TS), 1)
	pl.inv_t = 0.0
	var hp0 := float(Game.run["hp"])
	var hits0 := int(pl.hero_stats["hits"])
	var n0 := int(pl.hero_stats["n"])
	pl.hero_stats["vy"] = 0.0
	await _f(4)
	Input.action_press("asagi")
	await _f(1)
	Input.action_press("zipla")
	await _f(2)
	Input.action_release("zipla")
	var t := -1
	for i in 200:
		await _f()
		for e in foes:
			if is_instance_valid(e):
				e.cd = 99.0
		if snap and i % 3 == 0 and pl.hero_t >= 0.0:
			await _snap("dalis_%02d" % i)
		if pl.hero_pose_t > 0.0:
			t = i + 3
			break
	Input.action_release("asagi")
	if snap:
		await _snap("inis_an")
	var pose_seen: bool = pl.hero_pose_t > 0.0
	var stun := float(pl.fall_stun_t)
	var dmg := hp0 - float(Game.run["hp"])
	var hurt_foes := 0
	for e in foes:
		if is_instance_valid(e) and e.hp < 99999.0:
			hurt_foes += 1
	if snap:
		for k in [3, 6, 10, 16]:
			await _f(3 if k == 3 else (3 if k == 6 else (4 if k == 10 else 6)))
			await _snap("poz_%02d" % k)
	await _f(40)
	var r := {"t": t / 60.0, "vmax": float(pl.hero_stats["vy"]), "hits": int(pl.hero_stats["hits"]) - hits0, "foes": hurt_foes,
		"dmg": dmg, "stun": stun, "pose": pose_seen, "n": int(pl.hero_stats["n"]) - n0, "h": float(pl.hero_stats["h"])}
	_clear_enemies()
	return r


func _run() -> void:
	await get_tree().create_timer(0.6).timeout
	lv = main.level
	pl = lv.player
	if "boss" in lv and lv.boss != null and is_instance_valid(lv.boss):
		lv.boss.remove_from_group("dusman")
		lv.boss.queue_free()
		lv.boss = null
		spot = Vector2(33 * TS + 12, lv.surface_y(33) * TS - 1)
	else:
		_p("UYARI: --boss olmadan arena yok; düz zemin varsayılıyor")
		spot = pl.global_position
	_clear_enemies()
	if Game.run["slots"]["melee"].is_empty() or String(Game.run["slots"]["melee"].get("id", "")) != "alp_kilici":
		Game.run["slots"]["melee"] = ItemGen.roll("alp_kilici", 1, "demir", 0)
		pl.on_equip()
	var v34 := _has("hero_t")
	_p("surum=%s RUN=%.0f JUMP_V=%.0f GRAV=%.0f MAX_FALL=%.0f ACC_AIR=%.0f coyote=%.3f tampon=%.3f" % ["v34" if v34 else "eski",
		Player.RUN, Player.JUMP_V, Player.GRAV, Player.MAX_FALL, Player.ACC_AIR, float(Player.FLOW["coyote"]), float(Player.FLOW["buf_jump"])])
	# ---- zıplama yayı
	var full := await _jump(60)
	var tap := await _jump(2)
	var runj := await _jump(60, true, 27.0)
	var runj2 := await _jump(90, true, 26.0, "", true)
	var dj := await _double_jump()
	_p("tam zıplama: yükseklik=%.1f px (%.2f karo) tepeye=%.3f sn havada=%.3f sn" % [full["h"], full["h"] / TS, full["apex"], full["air"]])
	_p("dokunuş (2 kare): yükseklik=%.1f px (%.2f karo) havada=%.3f sn" % [tap["h"], tap["h"] / TS, tap["air"]])
	_p("koşu zıplaması: yatay=%.1f px (%.2f karo) havada=%.3f sn" % [runj["dx"], runj["dx"] / TS, runj["air"]])
	_p("koşu + çift zıplama: yatay=%.1f px (%.2f karo) havada=%.3f sn" % [runj2["dx"], runj2["dx"] / TS, runj2["air"]])
	_ok(runj["dx"] >= 4.0 * TS - 12.0 + 6.0, "koşu zıplaması 4 karoluk boşluğu (LevelGen ±5 sütun) geçemiyor")
	_p("çift zıplama: toplam yükseklik=%.1f px (%.2f karo)" % [dj["h"], dj["h"] / TS])
	_ok(full["h"] >= 75.5, "tam zıplama eski yüksekliğin (v33 ölçümü 75,7 px) altında")
	_ok(dj["h"] >= 4.0 * TS + 8.0, "çift zıplama 4 karoya yetmiyor (LevelGen modeli)")
	if v34:
		_ok(full["apex"] < 0.4, "tepeye varış eskisinden (0,4 sn) kısa değil")
	# ---- coyote / tampon
	var cy := await _coyote()
	_p("coyote: kenardan düştükten sonra en çok %d kare (%.3f sn) zıplanır" % [cy, cy / 60.0])
	var b6 := await _buffer(6)
	var b8 := await _buffer(8)
	_p("tampon: inişten 6 kare (0,10 sn) önce basış=%s, 8 kare (0,13 sn)=%s" % [str(b6), str(b8)])
	_ok(cy >= 5, "coyote 5 kareden kısa")
	_ok(b6, "0,1 sn erken zıplama tamponlanmadı")
	# ---- düşüş
	var f10 := await _fall(10.0)
	_p("düşüş 10 karo: süre=%.3f sn en hızlı=%.0f px/sn sersem=%.2f hasar=%.1f" % [f10["t"], f10["vmax"], f10["stun"], f10["dmg"]])
	# ---- basamak / tutunma
	var c1 := await _climb(1)
	var c2 := await _climb(2, 26.0)
	var c2t := await _climb(2, 26.0, 4)
	var c3 := await _climb(3, 30.0)
	var c4 := await _climb(4, 34.0)
	_p("1 karo basamak (zıplamadan, yürüyerek): çıktı=%s duvara değişten üstte durana=%.3f sn basamak=%d" % [str(c1["ok"]), c1["t"], c1["step"]])
	_p("2 karo kenar (tam zıpla): çıktı=%s zıplamadan sonra=%.3f sn tutunma=%d" % [str(c2["ok"]), c2["t"], c2["mantle"]])
	_p("2 karo kenar (4 karelik kısa zıplama): çıktı=%s zıplamadan sonra=%.3f sn tutunma=%d" % [str(c2t["ok"]), c2t["t"], c2t["mantle"]])
	_p("3 karo kenar (zıpla): çıktı=%s zıplamadan sonra=%.3f sn tutunma=%d" % [str(c3["ok"]), c3["t"], c3["mantle"]])
	_p("4 karo kenar (çift zıpla): çıktı=%s zıplamadan sonra=%.3f sn tutunma=%d" % [str(c4["ok"]), c4["t"], c4["mantle"]])
	if v34:
		_ok(c1["ok"] and not c1["jump"], "1 karo basamağa yürüyerek çıkılamadı")
		_ok(c2["ok"] and c3["ok"] and c4["ok"], "2-4 karo kenara çıkılamadı")
	# ---- tek yönlü platform: aşağı + zıpla = in (dalış değil)
	var dp := await _drop_platform()
	_p("tek yönlü platform aşağı+zıpla: indi=%s dalış=%d (0 olmalı)" % [str(dp["dropped"]), dp["dive"]])
	_ok(dp["dropped"] and dp["dive"] == 0, "platformdan iniş bozuldu")
	if not v34:
		_p("OZET hata=%d (eski sürüm: Kahraman İnişi yok)" % hata)
		get_tree().quit()
		return
	# ---- yüksek düşüş: sersemleme / hasar
	var f13 := await _fall(13.0)
	var f19 := await _fall(19.0)
	_p("düşüş 13 karo: süre=%.3f sn sersem=%.2f sn hasar=%.1f" % [f13["t"], f13["stun"], f13["dmg"]])
	_p("düşüş 19 karo: süre=%.3f sn sersem=%.2f sn hasar=%.1f" % [f19["t"], f19["stun"], f19["dmg"]])
	_ok(f10["stun"] <= 0.0 and f10["dmg"] <= 0.0, "10 karo düşüş sersemletmemeli")
	_ok(f13["stun"] > 0.0 and f13["dmg"] <= 0.0, "13 karo düşüş: kısa sersemleme, hasarsız olmalı")
	_ok(f19["stun"] > 0.0 and f19["dmg"] > 0.0, "19 karo düşüş: sersemleme + az hasar olmalı")
	# ---- Kahraman İnişi
	var h13 := await _hero(13.0, true)
	var h4 := await _hero(4.0)
	for r in [[13, h13], [4, h4]]:
		var d: Dictionary = r[1]
		_p("Kahraman İnişi %d karo: basıştan inişe=%.3f sn en hızlı=%.0f px/sn yükseklik=%.0f isabet=%d (yaralanan %d/3) oyuncu_hasar=%.1f sersem=%.2f poz=%s" % [r[0], d["t"], d["vmax"], d["h"], d["hits"], d["foes"], d["dmg"], d["stun"], str(d["pose"])])
	_ok(h13["n"] == 1 and h13["pose"], "Kahraman İnişi başlamadı / poz yok")
	_ok(h13["vmax"] >= 850.0, "dalış hızı düşük")
	_ok(h13["hits"] == 2, "13 karo inişte yakındaki iki düşman vurulmalı (uzaktaki değil)")
	_ok(h13["dmg"] <= 0.0 and h13["stun"] <= 0.0, "Kahraman İnişi hasar / sersemleme verdi")
	_ok(h13["t"] < f13["t"], "dalış normal düşüşten hızlı değil")
	# ---- görseller: koşu zıplaması yayı ve basamak
	if _snap_dir != "" and DisplayServer.get_name() != "headless":
		await _jump(60, true, 27.0, "yay")
		await _clear_blocks()
		_block(36.0, 4, 2)
		await _place(Vector2(31.0 * TS + 12.0, spot.y), 6)
		Input.action_press("sag")
		var jp := false
		var jf := 0
		for i in 60:
			await _f()
			if jp and i - jf == 4:
				Input.action_release("zipla")   # kısa zıplama: kenara tutunur
			if not jp and 36.0 * TS - pl.global_position.x <= 26.0:
				Input.action_press("zipla")
				jp = true
				jf = i
			if jp and i % 2 == 0:
				await _snap("tutun_%02d" % i)
			if jp and pl.is_on_floor() and pl.global_position.y < spot.y - 30.0:
				await _f(6)
				await _snap("tutun_son")
				break
		_release_all()
		await _clear_blocks()
	_p("OZET hata=%d" % hata)
	get_tree().quit()
