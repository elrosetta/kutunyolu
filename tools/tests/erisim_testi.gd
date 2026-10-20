extends RefCounted
## v34 birleştirme: GERÇEK OYUNCU fiziğiyle erişim denetimi (harita testinin alt kipi):
##   godot --headless --path . --fixed-fps 60 --quit-after 9999999 -- --harita --harita_fizik [--fizik_bolum=120]
## LevelGen._moves erişim modeli (tek / çift zıplama 4 karo yukarı, ±5 sütun, düşüş 15 satır) v33 zıplamasına göre
## kurulmuştu; v34 zıplaması (JUMP_V -565, ayrı yükseliş / düşüş yerçekimi, tek koşu zıplaması 95,6 px) ve v34 bölümleri
## (sapak, uzantı, pencere dalı, gizli cep, kilitli oda) ile modelin her hamlesi gerçek oyuncuyla yapılabiliyor mu?
## Her bölüm (Level.build, derinlik 1-9) için girişten Kut Kapısı'na, her ödül odasına ve her Kut Taşı'na, ve bunların
## her birinden Kut Kapısı'na en kısa model yolları çıkarılır; yollardaki her hamle (yürüme dışında) oyuncu hamlenin
## başına konup tuşlara basılarak (Input.action_press; yürü / zıpla / çift zıpla / kenardan zıpla / platformdan in ...)
## denenir; hamlenin bitiş hücresinde yerde durunca başarılı. Aynı yerel geometri (hamle + çevresi) bir kez denenir.
## Yapılamayan model hamlesi yasaklanır ve yol yeniden bulunur (oyuncu başka yoldan gidebiliyorsa hedef erişilir);
## hedef ancak hiçbir gerçek yol kalmazsa ERİŞİLEMEZ sayılır. Çıktı "[harita] FIZIK ..." satırları; yapılamayan model
## hamleleri (bilgi) ve erişilemeyen hedefler (hata) çevre çizimiyle.

var ht: Node          # harita_testi düğümü (main, _build, _phys)
var TS := 24.0
var _cache := {}      # yerel geometri anahtarı -> [başarı, tarif]
var _tarif_say := {}
var yapilamaz: Array = []    # gerçek oyuncunun yapamadığı model hamleleri (bilgi; başka yoldan gidilebilir)
var erisilemez: Array = []    # hiçbir gerçek yolu bulunamayan hedefler (hata)
var hedef_say := 0
var hamle_say := 0
var benzersiz := 0
var kare_say := 0
var iz := false       # --fizik_tek: kare izi
const ACTS := ["sag", "sol", "zipla", "asagi", "yukari", "saldiri1", "saldiri2", "yuvarlan"]


func _tree() -> SceneTree:
	return ht.get_tree()


func _f() -> void:
	await _tree().physics_frame
	kare_say += 1


func _release() -> void:
	for a in ACTS:
		Input.action_release(a)


static func _key(g: PackedByteArray, W: int, H: int, a: int, b: int) -> String:
	var cx := a % W
	var cy := a / W
	var nx := b % W
	var ny := b / W
	var s := "%d,%d|" % [nx - cx, ny - cy]
	for y in range(mini(cy, ny) - 6, maxi(cy, ny) + 2):
		for x in range(mini(cx, nx) - 3, maxi(cx, nx) + 4):
			s += str(LevelGen._cell(g, x, y, W, H))
		s += "/"
	return s


static func _ascii(g: PackedByteArray, W: int, H: int, a: int, b: int) -> String:
	var cx := a % W
	var cy := a / W
	var nx := b % W
	var ny := b / W
	var s := ""
	for y in range(mini(cy, ny) - 6, maxi(cy, ny) + 2):
		s += "\n      "
		for x in range(mini(cx, nx) - 4, maxi(cx, nx) + 5):
			if x == cx and y == cy:
				s += "A"
			elif x == nx and y == ny:
				s += "B"
			else:
				s += [".", "#", "=", "H", "4"][clampi(LevelGen._cell(g, x, y, W, H), 0, 4)]
	return s


func _hazirla(lv: Node) -> void:
	## Yaratıklar, yerdeki eşyalar, sandık / anahtar kaldırılır; kilitler açılır; Kut Kapısı tetiklenmez
	for e in _tree().get_nodes_in_group("dusman"):
		if is_instance_valid(e):
			e.remove_from_group("dusman")
			e.queue_free()
	for c in lv.get_children():
		if c is Pickup:
			c.queue_free()
	for kk in lv.kilitler:
		if is_instance_valid(kk) and not kk.acik:
			kk.ac()
	lv._done = true
	Game.run["max_hp"] = 100000.0
	Game.run["hp"] = 100000.0


func _hedefler(lv: Node) -> Array:
	## [ad, kaynak hücre, hedef hücre]: girişten Kut Kapısı'na, her ödül odasına / Kut Taşı'na ve oradan Kut Kapısı'na
	var g: PackedByteArray = lv.grid
	var W: int = lv.W
	var H: int = lv.H
	var hedef: Array = []
	for rm in lv.rooms:
		if String(rm["role"]) == "odul":
			hedef.append(["odul#%d" % int(rm["id"]), LevelGen._floor_spot(g, W, H, rm, LevelGen._odul_mid(rm))])
	for t in lv.tasi:
		if is_instance_valid(t):
			hedef.append(["tasi", LevelGen.stand_cell(g, W, H, t.global_position.x, t.global_position.y - 2.0, int(TS))])
	var s: Vector2i = lv.spawn_cell
	var ex: Vector2i = lv.exit_cell
	var out: Array = [["giris>kapi", s, ex]]
	for h in hedef:
		out.append(["giris>" + String(h[0]), s, h[1]])
		out.append([String(h[0]) + ">kapi", h[1], ex])
	return out


func _bfs(gh: PackedByteArray, W: int, H: int, s: Vector2i, gl: Vector2i, yasak: Dictionary, mv: Dictionary) -> Array:
	## LevelGen.path_cells gibi (hedef gx±2, gy±1), yasaklı hamleler (Vector2i(a, b)) atlanır; hamleler önbellekte
	var seen := PackedByteArray()
	seen.resize(W * H)
	seen.fill(0)
	var par := PackedInt32Array()
	par.resize(W * H)
	par.fill(-1)
	var s0 := s.y * W + s.x
	seen[s0] = 1
	var q: Array = [s0]
	var qi := 0
	var goal := -1
	while qi < q.size():
		var id: int = q[qi]
		qi += 1
		var cx := id % W
		var cy := id / W
		if absi(cx - gl.x) <= 2 and absi(cy - gl.y) <= 1:
			goal = id
			break
		if not mv.has(id):
			mv[id] = LevelGen._moves(gh, W, H, cx, cy)
		for n in mv[id]:
			if seen[n] == 0 and not yasak.has(Vector2i(id, n)):
				seen[n] = 1
				par[n] = id
				q.append(n)
	var out: Array = []
	if goal < 0:
		return out
	var c := goal
	while c >= 0:
		out.append(c)
		c = par[c]
	out.reverse()
	return out


func _durdu(pl: Node, nx: int, ny: int) -> bool:
	if not pl.is_on_floor():
		return false
	var fy := int(floor((pl.global_position.y - 2.0) / TS))
	return fy == ny and absf(pl.global_position.x - (nx * TS + 12.0)) <= 14.0


func _dene(lv: Node, pl: Node, a: int, b: int, tarif: String) -> bool:
	var W: int = lv.W
	var g: PackedByteArray = lv.grid
	var cx := a % W
	var cy := a / W
	var nx := b % W
	var ny := b / W
	var step := 1 if nx > cx else (-1 if nx < cx else 0)
	_release()
	pl.global_position = Vector2(cx * TS + 12.0, (cy + 1) * TS - 1.0)
	pl.velocity = Vector2.ZERO
	pl.hero_t = -1.0
	pl.hero_pose_t = 0.0
	pl.fall_stun_t = 0.0
	pl.roll_t = 0.0
	pl.drop_t = 0.0
	pl.mantle_t = 0.0
	pl.jump_buf = 0.0
	pl.hurt_t = 0.0
	pl.inv_t = 99.0
	pl._air_top = pl.global_position.y
	pl._cancel_attack(false)
	Game.run["bolum_sure"] = 0.0
	Game.run["hp"] = 100000.0
	for i in 4:
		await _f()
	if not pl.is_on_floor():
		return false
	var tx := nx * TS + 12.0
	# kenar: hamle yönünde ayakta durulan son sütun (kenardan zıplama tarifleri)
	var e := cx
	if step != 0:
		while e != nx and LevelGen._standable(g, e + step, cy, W, lv.H) and LevelGen._cell(g, e + step, cy - 1, W, lv.H) != 1:
			e += step
	var edge_x := e * TS + 12.0 + step * 7.0
	var faz := 0          # 0: kalkış öncesi, 1: havada (ilk zıplama), 2: çift zıplama basıldı
	var jt := 0           # zıplama tuşunun basılı kaldığı kare
	var geri := 0
	var t := 0
	var yerde_t := 0
	var faz0 := 0
	while t < 170:
		t += 1
		var x: float = pl.global_position.x
		var vy: float = pl.velocity.y
		var on: bool = pl.is_on_floor()
		var press_dir := 0
		var jump := false
		match tarif:
			"yuru":
				press_dir = int(signf(tx - x)) if absf(tx - x) > 3.0 else 0
			"in":
				press_dir = int(signf(tx - x)) if absf(tx - x) > 3.0 else 0
				# aşağı basılı; zıplama yalnız yerdeyken iki kare (havada aşağı + zıpla Kahraman İnişi olur)
				Input.action_press("asagi")
				jump = on and t % 14 >= 3 and t % 14 < 5
			"zipla", "zipla_cift", "erken_cift", "dik_cift":
				if faz == 0:
					jump = true
					faz = 1
				elif faz == 1:
					jump = jt < 22 and (vy < 0.0 or jt < 4)
					var esik := -60.0 if tarif == "zipla_cift" or tarif == "dik_cift" else -260.0
					if tarif != "zipla" and not on and vy > esik and jt >= 6:
						faz = 2
						jt = -2
				elif faz == 2:
					jump = jt >= 0 and jt < 22
				if tarif == "dik_cift" and faz == 1 and vy < -150.0:
					press_dir = 0
				else:
					press_dir = int(signf(tx - x)) if absf(tx - x) > 3.0 else 0
			"alt_zipla", "yakin_zipla", "orta_zipla":
				# önce hedefe (alt_zipla: altına) yürü, D px kala zıpla, tepede çift zıpla
				var D := 4.0 if tarif == "alt_zipla" else (14.0 if tarif == "yakin_zipla" else 40.0)
				if faz == 0:
					press_dir = int(signf(tx - x)) if absf(tx - x) > 3.0 else 0
					if absf(tx - x) <= D or (t > 6 and absf(pl.velocity.x) < 5.0 and absf(tx - x) <= 4.0 * TS) or (not on and t > 2):
						jump = true
						faz = 1
				elif faz == 1:
					press_dir = int(signf(tx - x)) if absf(tx - x) > 3.0 else 0
					jump = jt < 22 and (vy < 0.0 or jt < 4)
					if not on and vy > -60.0 and jt >= 6:
						faz = 2
						jt = -2
				else:
					press_dir = int(signf(tx - x)) if absf(tx - x) > 3.0 else 0
					jump = jt >= 0 and jt < 22
			"kenar_cift", "kenar_tek", "geri_kenar":
				if faz == 0:
					if tarif == "geri_kenar" and geri < 14:
						geri += 1
						press_dir = -step
					else:
						press_dir = step if step != 0 else (int(signf(tx - x)) if absf(tx - x) > 3.0 else 0)
						if step == 0 or (x - edge_x) * step >= 0.0 or not on:
							jump = true
							faz = 1
				elif faz == 1:
					press_dir = int(signf(tx - x)) if absf(tx - x) > 3.0 else 0
					jump = jt < 22 and (vy < 0.0 or jt < 4)
					if tarif != "kenar_tek" and not on and vy > -60.0 and jt >= 6:
						faz = 2
						jt = -2
				else:
					press_dir = int(signf(tx - x)) if absf(tx - x) > 3.0 else 0
					jump = jt >= 0 and jt < 22
		if press_dir > 0:
			Input.action_press("sag")
			Input.action_release("sol")
		elif press_dir < 0:
			Input.action_press("sol")
			Input.action_release("sag")
		else:
			Input.action_release("sag")
			Input.action_release("sol")
		if jump:
			Input.action_press("zipla")
		else:
			Input.action_release("zipla")
		if faz >= 1:
			jt += 1
		Game.run["hp"] = 100000.0
		await _f()
		if iz and (t % 3 == 0 or t > 38):
			ht._p("  iz %s t=%d faz=%d x=%.1f (%.2f karo) y=%.1f (%.2f) vx=%.0f vy=%.0f yer=%s tus=%d/%s hz=%d buf=%.2f coy=%.2f" % [tarif, t, faz, pl.global_position.x, pl.global_position.x / TS, pl.global_position.y, pl.global_position.y / TS, pl.velocity.x, pl.velocity.y, str(pl.is_on_floor()), press_dir, str(jump), int(pl.air_jumps), float(pl.jump_buf), float(pl.coyote)])
		if _durdu(pl, nx, ny):
			_release()
			return true
		# erken vazgeç: hedefin altına düştü ve yerde, ya da uzun süre yerde kıpırdamıyor
		if faz != faz0:
			yerde_t = 0   # zıplama basıldı: yerde sayacı baştan
			faz0 = faz
		var basladi := faz != 0 or tarif == "yuru" or tarif == "in"
		if pl.is_on_floor() and t > 8 and pl.mantle_t <= 0.0 and basladi:
			yerde_t += 1
			if int(floor((pl.global_position.y - 2.0) / TS)) > ny + 1 and yerde_t >= 8 and (faz != 0 or t > 60):
				break
			if yerde_t > 40:
				break
		else:
			yerde_t = 0
	_release()
	return false


func _tarifler(g: PackedByteArray, W: int, H: int, a: int, b: int) -> Array:
	var cx := a % W
	var cy := a / W
	var nx := b % W
	var ny := b / W
	var dy := ny - cy
	var dx := nx - cx
	if dx == 0 and dy > 0:
		return ["in", "yuru"]
	if dy > 0:
		return ["yuru", "kenar_tek", "kenar_cift", "zipla", "zipla_cift", "geri_kenar", "dik_cift", "orta_zipla"]
	if dy == 0 and absi(dx) <= 1:
		return ["yuru", "zipla"]
	return ["zipla", "zipla_cift", "kenar_cift", "alt_zipla", "yakin_zipla", "orta_zipla", "kenar_tek", "dik_cift", "erken_cift", "geri_kenar", "yuru"]


func _hamle(lv: Node, pl: Node, a: int, b: int) -> bool:
	## Model hamlesi gerçek oyuncuyla yapılabiliyor mu (yerel geometri önbelleğiyle)
	var W: int = lv.W
	var H: int = lv.H
	var g: PackedByteArray = lv.grid
	var dx := b % W - a % W
	var dy := b / W - a / W
	if dy == 0 and absi(dx) == 1:
		return true   # düz yürüme
	hamle_say += 1
	var key := _key(g, W, H, a, b)
	if _cache.has(key):
		return bool(_cache[key][0])
	benzersiz += 1
	var ok := false
	var hangi := ""
	for tf in _tarifler(g, W, H, a, b):
		if await _dene(lv, pl, a, b, tf):
			ok = true
			hangi = tf
			break
	_cache[key] = [ok, hangi]
	if ok:
		_tarif_say[hangi] = int(_tarif_say.get(hangi, 0)) + 1
	else:
		yapilamaz.append("d=%d stil=%s A=%d,%d B=%d,%d dx=%d dy=%d%s" % [int(Game.run.get("depth", 0)), String(lv.style), a % W, a / W, b % W, b / W, dx, dy, _ascii(g, W, H, a, b)])
	return ok


func tek(spec: String) -> void:
	## Hata ayıklama: --fizik_tek=derinlik,tohum,ax,ay,bx,by -> o hamle her tarifle, kare iziyle
	var a := spec.split(",")
	var lv: Node = ht._build(int(a[0]), int(a[1]))
	ht.main._start_play()
	await _f()
	_hazirla(lv)
	await _f()
	var W: int = lv.W
	var ia := int(a[3]) * W + int(a[2])
	var ib := int(a[5]) * W + int(a[4])
	ht._p("FIZIK tek stil=%s%s" % [String(lv.style), _ascii(lv.grid, W, lv.H, ia, ib)])
	iz = true
	for tf in _tarifler(lv.grid, W, lv.H, ia, ib):
		var ok: bool = await _dene(lv, lv.player, ia, ib, tf)
		ht._p("FIZIK tek tarif=%s sonuç=%s" % [tf, str(ok)])


func kos(n_bolum: int, bas := 0) -> void:
	var t0 := Time.get_ticks_msec()
	for k in range(bas, bas + n_bolum):
		var d: int = 1 + k % 9
		var seed_v := 9100 + k * 37
		var lv: Node = ht._build(d, seed_v)
		ht.main._start_play()
		await _f()
		_hazirla(lv)
		await _f()
		var pl: Node = lv.player
		var W: int = lv.W
		var H: int = lv.H
		var gh := LevelGen._haz_as_air(lv.grid)
		var yasak := {}
		var mv := {}
		var lv_hedef := 0
		var lv_yok := 0
		var lv_dolasma := 0
		for hd in _hedefler(lv):
			lv_hedef += 1
			hedef_say += 1
			var ok := false
			var ilk := -1
			for deneme in 40:
				var p := _bfs(gh, W, H, hd[1], hd[2], yasak, mv)
				if p.is_empty():
					break
				if ilk < 0:
					ilk = p.size()
				var kirik := -1
				for i in range(1, p.size()):
					if not await _hamle(lv, pl, p[i - 1], p[i]):
						kirik = i
						break
				if kirik < 0:
					ok = true
					if p.size() > ilk:
						lv_dolasma += 1
					break
				yasak[Vector2i(p[kirik - 1], p[kirik])] = true
			if not ok:
				lv_yok += 1
				var src: Vector2i = hd[1]
				erisilemez.append("d=%d tohum=%d stil=%s hedef=%s kaynak=%d,%d hedef=%d,%d" % [d, seed_v, String(lv.style), String(hd[0]), src.x, src.y, (hd[2] as Vector2i).x, (hd[2] as Vector2i).y])
				ht._p("FIZIK ERİŞİLEMEZ " + String(erisilemez[-1]))
		ht._p("FIZIK bölüm %d/%d d=%d tohum=%d stil=%s hedef=%d erişilemez=%d dolaşarak=%d yasak_hamle=%d benzersiz=%d (%.0f sn)" % [k + 1, n_bolum, d, seed_v, String(lv.style), lv_hedef, lv_yok, lv_dolasma, yasak.size(), benzersiz, (Time.get_ticks_msec() - t0) / 1000.0])
	_release()
	ht._p("FIZIK tarifler %s" % str(_tarif_say))
	ht._p("FIZIK TOPLAM bölüm=%d hedef=%d erişilemez=%d | model hamlesi=%d benzersiz_geometri=%d gerçek oyuncunun yapamadığı=%d | fizik_karesi=%d süre=%.0f sn" % [n_bolum, hedef_say, erisilemez.size(), hamle_say, benzersiz, yapilamaz.size(), kare_say, (Time.get_ticks_msec() - t0) / 1000.0])
	for s2 in yapilamaz:
		ht._p("FIZIK yapılamayan model hamlesi " + s2)
	for s2 in erisilemez:
		ht._p("FIZIK ERİŞİLEMEZ " + s2)
