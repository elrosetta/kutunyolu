extends Node
## v25 harita testi: godot --headless --path . --quit-after 999999 -- --harita [--harita_tohum=N] [--harita_bolum=K]
##   IZGARA: her stil (6) × N tohum (LevelGen.generate, Level.W × Level.H): ana yol (girişten Kut Kapısı'na) yalnızca
##           yürüyerek (yuvarlanmadan, baş boşluğu >= 2 karo) geçilebiliyor mu; yol boyunca en dar baş boşluğu; 3 karo ile
##           geçilebiliyor mu; girişten ulaşılan "yalnızca yuvarlanarak" (1 karo) ve 2 karoluk hücre sayısı.
##   BOLUM:  derinlik 1-9 × K tohum tam bölüm kurulur (Level.build): her düşmanın gövdesi (çarpışma boyu × görsel ölçek)
##           duvara / tavana girmiyor mu, yerdekinin altı düz ve tehlikesiz mi; eşyalar katı karoda değil mi; tüccar
##           duvar denetimi (Level.bezirgan_ok); tehlike çukuru sayısı.
## Çekim kipleri (--goruntu ile, headless değil): --harita_ekran=genis (geniş bölüm kesitleri), tuzak (çukur sektirmesi
##   kare dizisi), tepegoz (göz ışını iki yöne, tarama, 3. evre).
## Çıktı "[harita] ..." satırları, sonda "[harita] SONUC GECTI|KALDI".

var main: Node
var _fail: Array = []
var _ekran := ""
var _cikti := ""


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("--harita_ekran="):
			_ekran = String(a).trim_prefix("--harita_ekran=")
		elif String(a).begins_with("--harita_cikti="):
			_cikti = String(a).trim_prefix("--harita_cikti=")
	_run.call_deferred()


func _p(s: String) -> void:
	print("[harita] ", s)


func _check(ok: bool, what: String) -> void:
	_p(("TAMAM " if ok else "HATA ") + what)
	if not ok:
		_fail.append(what)


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _arg_or(name: String, def: String) -> String:
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with(name + "="):
			return String(a).trim_prefix(name + "=")
	return def


func _run() -> void:
	await _frames(5)
	if _ekran != "":
		await _ekran_kur()
		return
	var bak := _arg_or("--harita_bak", "")
	if bak != "":
		# hata ayıklama: --harita_bak=derinlik,tohum,x -> o bölümün x çevresi (ızgara)
		var a := bak.split(",")
		get_tree().paused = true
		var lv := _build(int(a[0]), int(a[1]))
		var x := int(a[2])
		_p("bak stil=%s x=%d sy=%d çıkış=%s%s" % [lv.style, x, lv.surface_y(x), str(lv.exit_pos / Level.TS), _area(lv.grid, Level.W, Level.H, x, lv.surface_y(x) - 1)])
		get_tree().quit()
		return
	_izgara(int(_arg_or("--harita_tohum", "12")))
	await _bolumler(int(_arg_or("--harita_bolum", "6")))
	_p("SONUC %s%s" % ["GECTI" if _fail.is_empty() else "KALDI", "" if _fail.is_empty() else " (" + ", ".join(_fail) + ")"])
	get_tree().quit()


# ------------------------------------------------------------------ ızgara ölçümü
static func head(g: PackedByteArray, W: int, H: int, x: int, y: int) -> int:
	## Ayakta durulan hücreden yukarı katı olmayan (hava / platform / tehlike) karo sayısı (en çok 9)
	var n := 0
	while n < 9 and y - n >= 0 and LevelGen._cell(g, x, y - n, W, H) != 1:
		n += 1
	return n


static func reach(g: PackedByteArray, W: int, H: int, heights: Array, min_h: int, want_path := false) -> Dictionary:
	## Girişten BFS (LevelGen._moves); min_h > 1: yalnızca baş boşluğu >= min_h hücrelerden / hücrelere (yuvarlanmadan).
	## {ok, seen (PackedByteArray), path (ana yol hücreleri, want_path)}
	var gh := LevelGen._haz_as_air(g)
	var sx := 5
	var sy: int = int(heights[sx]) - 1
	var seen := PackedByteArray()
	seen.resize(W * H)
	seen.fill(0)
	var par := PackedInt32Array()
	if want_path:
		par.resize(W * H)
		par.fill(-1)
	var s0 := sy * W + sx
	seen[s0] = 1
	var q: Array = [s0]
	var qi := 0
	var goal := -1
	while qi < q.size():
		var id: int = q[qi]
		qi += 1
		var cx := id % W
		var cy := id / W
		if cx >= W - 7 and goal < 0:
			goal = id
			if not want_path:
				break
		for n in LevelGen._moves(gh, W, H, cx, cy):
			if seen[n] != 0:
				continue
			if min_h > 1 and head(g, W, H, n % W, n / W) < min_h:
				continue
			seen[n] = 1
			if want_path:
				par[n] = id
			q.append(n)
	var path: Array = []
	if want_path and goal >= 0:
		var c := goal
		while c >= 0:
			path.append(c)
			c = par[c]
	return {"ok": goal >= 0, "seen": seen, "path": path}


static func _area(g: PackedByteArray, W: int, H: int, x: int, y: int) -> String:
	var s := "
"
	for yy in range(y - 12, y + 4):
		for xx in range(x - 6, x + 14):
			var c := LevelGen._cell(g, xx, yy, W, H)
			s += "@" if (xx == x and yy == y) else ["." , "#", "=", "H", "4"][clampi(c, 0, 4)]
		s += "
"
	return s


static func _col(g: PackedByteArray, W: int, H: int, x: int, y: int) -> String:
	## Hücrenin çevresi (y-3 .. y+1, x-2 .. x+2): # katı, = platform, H tehlike, . hava, @ hücre
	var s := ""
	for yy in range(y - 3, y + 2):
		for xx in range(x - 2, x + 3):
			var c := LevelGen._cell(g, xx, yy, W, H)
			s += "@" if (xx == x and yy == y) else ["." , "#", "=", "H", "4"][clampi(c, 0, 4)]
		s += "|"
	return s


func _izgara(n_seed: int) -> void:
	var W := int(_arg_or("--harita_w", str(Level.W)))   # --harita_w=230: eski genişlikle karşılaştırma
	var H := Level.H
	_p("IZGARA W=%d H=%d, %d stil × %d tohum" % [W, H, LevelGen.STYLES.size(), n_seed])
	var fixes := [0, 0, 0]
	var tot := 0
	var walk_ok := 0
	var ok3 := 0
	var min_path_all := 99
	var hist := {}
	var roll_cells := 0
	var tight_cells := 0
	var roll_lv := 0
	for style in LevelGen.STYLES:
		var s_walk := 0
		var s_ok3 := 0
		var s_min := 99
		var s_roll := 0
		for k in n_seed:
			var rng := RandomNumberGenerator.new()
			rng.seed = 1000 + k * 7919 + style.length() * 31
			var r := LevelGen.generate(rng, W, H, 3, [style])
			var g: PackedByteArray = r["grid"]
			var hts: Array = r["heights"]
			tot += 1
			fixes[0] += int(r.get("carved", 0))
			fixes[1] += int(r.get("trapfix", 0))
			fixes[2] += int(r.get("headfix", 0))
			var any := reach(g, W, H, hts, 1)
			var walk := reach(g, W, H, hts, 2, true)
			var w3 := reach(g, W, H, hts, 3)
			var pmin := 99
			if walk["ok"]:
				walk_ok += 1
				s_walk += 1
				for id in walk["path"]:
					pmin = mini(pmin, head(g, W, H, id % W, id / W))
			if w3["ok"]:
				ok3 += 1
				s_ok3 += 1
			var best_min := 3 if w3["ok"] else (2 if walk["ok"] else 1)
			if not walk["ok"]:
				pmin = 1
				var rr := LevelGen._reach(LevelGen._haz_as_air(g), W, H, hts)
				_p("  yürünemeyen stil=%s tohum=%d (yuvarlanarak=%s) en_uzak=%d,%d çevre=%s" % [style, k, str(any["ok"]), int(rr["x"]), int(rr["y"]), _area(g, W, H, int(rr["x"]), int(rr["y"]))])
			elif pmin < 2:
				for id in walk["path"]:
					if head(g, W, H, id % W, id / W) < 2:
						_p("  yolda dar stil=%s tohum=%d x=%d y=%d sütun=%s" % [style, k, id % W, id / W, _col(g, W, H, id % W, id / W)])
						break
			min_path_all = mini(min_path_all, pmin)
			s_min = mini(s_min, pmin)
			hist[best_min] = int(hist.get(best_min, 0)) + 1
			# girişten ulaşılan dar hücreler
			var seen: PackedByteArray = any["seen"]
			var rc := 0
			for id in seen.size():
				if seen[id] == 0:
					continue
				var hh := head(g, W, H, id % W, id / W)
				if hh <= 1:
					rc += 1
					if rc <= 2:
						_p("  dar hücre stil=%s tohum=%d x=%d y=%d baş=%d sütun=%s" % [style, k, id % W, id / W, hh, _col(g, W, H, id % W, id / W)])
				elif hh == 2:
					tight_cells += 1
			roll_cells += rc
			s_roll += rc
			if rc > 0:
				roll_lv += 1
		_p("IZGARA stil=%s yürüyerek=%d/%d 3karo=%d/%d yol_en_dar=%d yuvarlanma_hücresi=%d" % [style, s_walk, n_seed, s_ok3, n_seed, s_min, s_roll])
	_p("IZGARA TOPLAM bölüm=%d yürüyerek(>=2)=%d 3karo=%d ana_yol_en_dar=%d en_iyi_yol_dağılımı=%s yuvarlanma_hücresi=%d (bölüm %d) 2karo_hücre=%d" % [tot, walk_ok, ok3, min_path_all, str(hist), roll_cells, roll_lv, tight_cells])
	_p("IZGARA onarım ortalaması: koridor %.2f, çıkmaz %.2f, açılan tavan karosu %.1f" % [float(fixes[0]) / tot, float(fixes[1]) / tot, float(fixes[2]) / tot])
	_check(walk_ok == tot, "her bölümde ana yol yuvarlanmadan yürünür (%d/%d)" % [walk_ok, tot])
	_check(roll_cells == 0, "girişten ulaşılan yalnızca-yuvarlanma hücresi yok (%d)" % roll_cells)


# ------------------------------------------------------------------ tam bölüm: yerleşim
func _build(d: int, seed_v: int) -> Node:
	Game.run["depth"] = d
	Game.run["tier"] = Zorluk.kademe(d)
	if main.level:
		main.level.queue_free()
	var lv := Level.new()
	lv.process_mode = Node.PROCESS_MODE_PAUSABLE
	main.add_child(lv)
	main.level = lv
	lv.build(seed_v)
	main.hud.level = lv
	return lv


static func body_rect(e: Node) -> Rect2:
	var s: Vector2 = e.size * Vector2(absf(e.base_scale.x), absf(e.base_scale.y))
	var p: Vector2 = e.global_position
	return Rect2(p.x - s.x / 2.0, p.y - s.y, s.x, s.y)


static func spawn_problem(lv: Node, e: Node) -> String:
	## "" geçerli; değilse neden (duvar / tavan / zemin yok / tehlike / dar)
	var TS: int = Level.TS
	var r := body_rect(e)
	var core := r.grow(-1.0)
	var x0 := int(floor(core.position.x / TS))
	var x1 := int(floor(core.end.x / TS))
	var y0 := int(floor((core.position.y - 4.0) / TS))
	var y1 := int(floor(core.end.y / TS))
	for x in range(x0, x1 + 1):
		for y in range(y0, y1 + 1):
			var c: int = lv.cell(x, y)
			if c == 1:
				return "duvar" if y >= int(floor((core.end.y - 2.0) / TS)) - 1 else "tavan"
			if c == 3:
				return "tehlike"
	if e.flying:
		return ""
	var fy := int(floor((e.global_position.y + 4.0) / TS))
	for x in range(int(floor((r.position.x + 2.0) / TS)), int(floor((r.end.x - 2.0) / TS)) + 1):
		var f: int = lv.cell(x, fy)
		if f == 3:
			return "tehlike"
		if f != 1 and f != 2:
			return "zemin_yok"
	return ""


func _bolumler(n_seed: int) -> void:
	_p("BOLUM derinlik | bölüm | düşman | geçersiz | seçkin | taşınan / konmayan | eşya kaidesi / bölüm | eşya katıda | tehlike karo / bölüm | tüccar duvar")
	var tot_mv := 0
	var tot_sk := 0
	var tot_e := 0
	var tot_bad := 0
	var tot_item_bad := 0
	var bz_ok := true
	var reasons := {}
	var kinds_bad := {}
	get_tree().paused = true
	for d in range(1, 10):
		var ne := 0
		var nb := 0
		var nel := 0
		var nib := 0
		var nh := 0
		var nmv := 0
		var nsk := 0
		var nit := 0
		var wall := true
		for k in n_seed:
			var lv := _build(d, 5000 + d * 101 + k * 7)
			for e in get_tree().get_nodes_in_group("dusman"):
				if not is_instance_valid(e) or e.is_queued_for_deletion() or e.get_parent() == null or e.level != lv:
					continue
				ne += 1
				if e.elite:
					nel += 1
				var why := spawn_problem(lv, e)
				if why != "":
					nb += 1
					reasons[why] = int(reasons.get(why, 0)) + 1
					var kk := "%s%s" % [e.kind, "*" if e.elite else ""]
					kinds_bad[kk] = int(kinds_bad.get(kk, 0)) + 1
					if nb <= 4:
						_p("  geçersiz d%d %s x=%d y=%d boy=%s (%s)" % [d, kk, int(e.global_position.x / Level.TS), int(e.global_position.y / Level.TS), str(e.size), why])
			nmv += int(lv.get("spawn_moved") if lv.get("spawn_moved") != null else 0)
			nsk += int(lv.get("spawn_skipped") if lv.get("spawn_skipped") != null else 0)
			for p in lv.pickups:
				if is_instance_valid(p) and p.kind == "item":
					nit += 1
				if is_instance_valid(p) and p.kind in ["item", "tilsim", "lutuf"] and lv.solid_at(p.global_position + Vector2(0, -4)):
					nib += 1
			for i in lv.grid.size():
				if lv.grid[i] == 3:
					nh += 1
			if lv.bezirgan != null:
				wall = wall and lv.bezirgan_ok()
			lv.queue_free()
			main.level = null
			await _frames(1)
		tot_e += ne
		tot_bad += nb
		tot_item_bad += nib
		bz_ok = bz_ok and wall
		tot_mv += nmv
		tot_sk += nsk
		_p("BOLUM %d | %d | %d | %d | %d | %d / %d | %.1f | %d | %.1f | %s" % [d, n_seed, ne, nb, nel, nmv, nsk, float(nit) / n_seed, nib, float(nh) / n_seed, "duvar_ok" if wall else "DUVARDA"])
	get_tree().paused = false
	_p("BOLUM TOPLAM düşman=%d geçersiz=%d taşınan=%d konmayan=%d nedenler=%s türler=%s eşya_katıda=%d" % [tot_e, tot_bad, tot_mv, tot_sk, str(reasons), str(kinds_bad), tot_item_bad])
	_check(tot_bad == 0, "geçersiz düşman yerleşimi yok (%d / %d)" % [tot_bad, tot_e])
	_check(tot_item_bad == 0, "eşya / tomar / sunak katı karoda değil (%d)" % tot_item_bad)
	_check(bz_ok, "tüccar duvarda değil (duvar_ok)")


# ------------------------------------------------------------------ çekim kipleri
func _snap(name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	if img and _cikti != "":
		var path := _cikti.path_join(name + ".png")
		img.save_png(path)
		_p("kare: " + path)


func _clear_foes(lv: Node, around: Vector2, r: float) -> void:
	for e in get_tree().get_nodes_in_group("dusman"):
		if is_instance_valid(e) and e != lv.boss and e.global_position.distance_to(around) < r:
			e.remove_from_group("dusman")
			e.queue_free()


func _phys(n: int) -> void:
	for i in n:
		await get_tree().physics_frame


func _ekran_kur() -> void:
	if _cikti != "":
		DirAccess.make_dir_recursive_absolute(_cikti)
	Game.run["max_hp"] = 100000.0
	Game.run["hp"] = 100000.0
	match _ekran:
		"genis":
			await _ekran_genis()
		"tuzak":
			await _ekran_tuzak()
		"tepegoz":
			await _ekran_tepegoz()
	get_tree().quit()


func _ekran_genis() -> void:
	## Geniş bölüm kesitleri: her stilden bir bölüm; 3 karo yüksek tünel, kule altı, hazine odası, seçkin odası, kurgan,
	## mağara tavanı / dar boğaz, kuyu önünde kareler
	var want := ["magara", "harabe", "kuyu", "bozkir", "ucurum", "orman"]
	var pref := ["tunel", "kule", "hazine", "seckin", "kurgan", "cukur", "merdiven", "sutunlar", "zehir_cukuru"]
	var done := {}
	for d in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
		for k in 6:
			var lv := _build(d, 3000 + d * 31 + k)
			if done.has(lv.style) or not (lv.style in want):
				continue
			done[lv.style] = true
			main._start_play()
			main.hud._card_t = 100.0
			await _phys(10)
			var pl: Node = lv.player
			_clear_foes(lv, pl.global_position, 99999.0)
			var xs: Array = []
			for nm in pref:
				for ch in lv.chunks:
					if String(ch["name"]) == nm and xs.size() < 2:
						xs.append([nm, int(ch["x"]) + 6])
			xs.append(["orta", Level.W / 2])
			for e2 in xs:
				var x: int = e2[1]
				if OS.get_cmdline_user_args().has("--harita_dok"):
					var sy0: int = lv.surface_y(x)
					_p("dok %s x=%d sy=%d%s" % [String(e2[0]), x, sy0, _area(lv.grid, Level.W, Level.H, x - 6, sy0 - 1)])
				pl.global_position = Vector2((x - 8) * Level.TS, lv.surface_y(x - 8) * Level.TS - 1)
				pl.velocity = Vector2.ZERO
				pl.facing = 1
				Game.camera.reset_smoothing()
				await _phys(45)
				await _snap("genis_%s_d%d_%s_%d" % [lv.style, d, String(e2[0]), x])
			break
		if done.size() >= want.size():
			break


func _ekran_tuzak() -> void:
	## Tehlike çukuru sektirmesi: oyuncu ilk diken çukuruna sağa yürür; 4 karede bir kare (sonra harita_testi kare dizisi)
	var lv: Node = null
	var px := -1
	var py := -1
	for k in 30:
		lv = _build(int(_arg_or("--harita_derinlik", "1")), 900 + k)
		if lv.haz_kind != "diken":
			continue
		for x in range(20, Level.W - 20):
			var sy: int = lv.surface_y(x)
			if lv.cell(x, sy) == 3 and lv.cell(x - 1, lv.surface_y(x - 1)) != 3 and lv.cell(x - 3, lv.surface_y(x - 3)) == 1:
				px = x
				py = sy
				break
		if px >= 0:
			break
	if px < 0:
		_p("diken çukuru bulunamadı")
		return
	main._start_play()
	await _phys(6)
	var pl: Player = lv.player
	_clear_foes(lv, Vector2(px * Level.TS, py * Level.TS), 1200.0)
	pl.global_position = Vector2((px - 4) * Level.TS + 12, lv.surface_y(px - 4) * Level.TS - 1)
	pl.velocity = Vector2.ZERO
	pl.facing = 1
	Game.camera.reset_smoothing()
	await _phys(30)
	await _snap("tuzak_00_once")
	Input.action_press("sag")
	for i in 22:
		await _phys(4)
		if i == 8:
			Input.action_release("sag")
		await _snap("tuzak_%02d" % (i + 1))
	Input.action_release("sag")
	_p("tuzak: son vuruş=%.2f sn önce, oyuncu x=%d y=%d zemin=%s (çukur x=%d)" % [Game.clock() - float(pl._haz_last), int(pl.global_position.x / Level.TS), int(pl.global_position.y / Level.TS), str(pl.is_on_floor()), px])


func _ekran_tepegoz() -> void:
	## Tepegöz göz ışını: iki yöne (sağa / sola bakarken), hazırlık (nişan çizgisi) ve ışın; 3. evrede gidip gelen tarama
	for ph in [2, 3]:
		for side in [1, -1]:
			main._build_boss("tepegoz")
			main._start_play()
			await _phys(4)
			var lv: Node = main.level
			var b = lv.boss
			var pl: Player = lv.player
			Game.run["max_hp"] = 100000.0
			Game.run["hp"] = 100000.0
			b.global_position.x = 42 * Level.TS
			pl.global_position = Vector2(b.global_position.x + side * 260.0, pl.global_position.y)
			await _phys(60)
			b.phase = ph
			b.hp = b.max_hp * (0.55 if ph == 2 else 0.22)
			var w := 0
			while String(b.state) != "chase" and w < 400:
				await _phys(1)
				w += 1
			b.global_position.x = 42 * Level.TS
			pl.global_position.x = b.global_position.x + side * 260.0
			b._face(pl.center() - b.center())
			b.call("_start", "beam")
			for i in 14:
				await _phys(9)
				await _snap("tepegoz_e%d_%s_%02d" % [ph, "sag" if side > 0 else "sol", i])
				if is_instance_valid(b._beam2):
					var bm: Isin = b._beam2
					_p("göz e%d %s kare=%d anim=%s/%d göz=%s ışın_başı=%s fark=%.1f" % [ph, "sag" if side > 0 else "sol", i, b.anim.anim, b.anim.frame, str(b._tg_eye().round()), str(bm.origin.round()), bm.origin.distance_to(b._tg_eye())])
