extends Node
## v25 harita testi: godot --headless --path . --quit-after 999999 -- --harita [--harita_tohum=N] [--harita_bolum=K]
##   IZGARA: v41: her biyom (5) × N tohum (--harita_tohum; biyomun level ayarları, derinliği, tür seçimi; --harita_tur=eski
##           v34 üreticisi) (LevelGen.generate, Level.W × Level.H); TUR satırları: bölüm türü başına ölçüm. Ana yol (girişten Kut Kapısı'na) yalnızca
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
	if OS.get_cmdline_user_args().has("--harita_fizik"):
		# v34 birleştirme: gerçek oyuncu fiziğiyle erişim (tools/tests/erisim_testi.gd)
		var fz: RefCounted = load("res://tools/tests/erisim_testi.gd").new()
		fz.ht = self
		if _arg_or("--fizik_tek", "") != "":
			await fz.tek(_arg_or("--fizik_tek", ""))
			get_tree().quit()
			return
		await fz.kos(int(_arg_or("--fizik_bolum", "120")), int(_arg_or("--fizik_bas", "0")))
		_check(fz.erisilemez.is_empty(), "gerçek oyuncu fiziğiyle her hedef (Kut Kapısı, ödül odaları, Kut Taşları ve dönüş) erişilir (%d hedef, %d erişilemez; %d benzersiz hamle geometrisi, %d model hamlesi yapılamadı)" % [fz.hedef_say, fz.erisilemez.size(), fz.benzersiz, fz.yapilamaz.size()])
		_p("SONUC %s%s" % ["GECTI" if _fail.is_empty() else "KALDI", "" if _fail.is_empty() else " (" + ", ".join(_fail) + ")"])
		get_tree().quit()
		return
	_izgara(int(_arg_or("--harita_tohum", "12")))
	await _bolumler(int(_arg_or("--harita_bolum", "6")))
	await _merak_oyun()
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
	## {ok, seen (PackedByteArray), path (ana yol hücreleri, want_path)}. v32: giriş / çıkış LevelGen._son'dan.
	var gh := LevelGen._haz_as_air(g)
	var sx := int(LevelGen._son["sx"])
	var sy := int(LevelGen._son["sy"])
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
		if LevelGen._goal(cx, cy) and goal < 0:
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


## v33 yol ölçümü: yürüme 155 px/sn = 6,46 karo/sn (Player.RUN), yerçekimi 1180, zıplama 430 px/sn
const KOSU_KARO := 6.46


static func yol_olcum(path: Array, W: int) -> Dictionary:
	## Ana yol hücre dizisi (giriş -> çıkış) üzerinden: uzunluk (karo: yatay + dikey), tahmini süre (sn; hamle başına
	## yatay koşu ile zıplama / düşüş süresinin büyüğü), düşüş (>= 3 karo aşağı), tırmanış (>= 3 karo yukarı), küçük
	## basamak (1-2 karo), en uzun dikey zincir (aynı yönde art arda dikey hamleler, aralarında en çok 4 karo yürüyüş;
	## tırmanış basamakları dahil) ve en uzun KÜÇÜK basamak zinciri (yalnızca 1-2 karoluk adımlar: merdiven yorgunluğu)
	var ln := 0
	var sure := 0.0
	var dusus := 0
	var dusus_max := 0     # v34 birleştirme: en uzun tek düşüş (karo) ve yüksek düşüş sersemlemesi (Player.HERO.stun_h)
	var dusus_hist := {}
	var sersem := 0
	var tirmanis := 0
	var basamak := 0
	var zincir := 0
	var zincir_max := 0
	var zincir_yon := 0
	var duz := 0
	var kz := 0       # küçük basamak (1-2 karo) zinciri: merdiven yorgunluğu
	var kz_max := 0
	var kz_yon := 0
	var kz_duz := 0
	var dikey_karo := 0   # v41: >= 3 karoluk düşüş / tırmanışların toplam yüksekliği
	var y_lo := 9999
	var y_hi := -1
	for i in range(0, path.size()):
		y_lo = mini(y_lo, int(path[i]) / W)
		y_hi = maxi(y_hi, int(path[i]) / W)
	for i in range(1, path.size()):
		var a: int = path[i - 1]
		var b: int = path[i]
		var dx := absi(b % W - a % W)
		var dy := b / W - a / W
		ln += dx + absi(dy)
		var th := float(dx) / KOSU_KARO
		var tv := 0.0
		if dy < 0:
			tv = 0.36 if dy >= -3 else 0.62
		elif dy > 0:
			tv = sqrt(2.0 * dy * 24.0 / 1180.0)
		elif dx > 1:
			tv = 0.25
		sure += maxf(th, tv)
		if dy == 0 or absi(dy) > 2:
			kz_duz += dx if dy == 0 else 99
			if kz_duz > 4:
				kz = 0
		else:
			if kz > 0 and signi(dy) == kz_yon and kz_duz <= 4:
				kz += 1
			else:
				kz = 1
			kz_yon = signi(dy)
			kz_duz = 0
			kz_max = maxi(kz_max, kz)
		if dy == 0:
			duz += dx
			if duz > 4:
				zincir = 0
			continue
		if absi(dy) >= 3:
			dikey_karo += absi(dy)
		if dy >= 3:
			dusus += 1
			dusus_max = maxi(dusus_max, dy)
			dusus_hist[dy] = int(dusus_hist.get(dy, 0)) + 1
			if float(dy * 24) > float(Player.HERO["stun_h"]):
				sersem += 1
		elif dy <= -3:
			tirmanis += 1
		else:
			basamak += 1
		var yon := signi(dy)
		if zincir > 0 and yon == zincir_yon and duz <= 4:
			zincir += 1
		else:
			zincir = 1
		zincir_yon = yon
		duz = 0
		zincir_max = maxi(zincir_max, zincir)
	return {"uzunluk": ln, "sure": sure, "dusus": dusus, "tirmanis": tirmanis, "basamak": basamak, "zincir": zincir_max, "basamak_zinciri": kz_max,
		"dusus_max": dusus_max, "dusus_hist": dusus_hist, "sersem": sersem, "dikey_karo": dikey_karo, "y_aralik": maxi(0, y_hi - y_lo)}


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
	var zorla := _arg_or("--harita_tur", "")   # v41: eski = v34 üreticisi (önce ölçümü); acik / kale / inis / magara
	var biyomlar := _biyomlar()
	_p("IZGARA W=%d H=%d, %d biyom × %d tohum (v41: biyomun level ayarları, derinliği ve tür seçimi; tür zorla=%s)" % [W, H, biyomlar.size(), n_seed, zorla])
	var tur_m := {}   # v41: tür -> ölçüm toplamları
	var fixes := [0, 0, 0]
	var tot := 0
	var walk_ok := 0
	var ok3 := 0
	var min_path_all := 99
	var hist := {}
	var roll_cells := 0
	var tight_cells := 0
	var roll_lv := 0
	# v32 çizge ölçümleri: ana yol odası, dal, çıkmaz, döngü, dikey adım, kesim satırı, Kut Taşı, zamanlı kapı,
	# ulaşılan hücre oranı (girişten BFS / tüm ayakta durma hücreleri), düşey aralık (en yüksek - en alçak taban)
	var m_sum := {}
	var ok_all := 0
	var reach_min := 1.0
	var tasi_min := 99
	var cikmaz_min := 99
	var dikey_min := 99
	var zincir_max := 0
	var kz_max := 0
	var sure_min := 9999.0
	var sure_max := 0.0
	var gen_max := 0.0
	var pencere_var := 0
	var d_hist := {}       # v34 birleştirme: ana yoldaki düşüş yükseklikleri (karo -> sayı)
	var d_max := 0
	var d_sersem := 0
	var d_sersem_lv := 0
	var ot := {"n": 0, "yer": 0, "dort": 0, "uc": 0, "erisim": 0, "kapi_yakin": 0, "uzak_top": 0.0, "yakin_top": 0.0, "oda2": 0, "par_top": 0.0, "par_min": 999.0, "par_max": 0.0, "yol_top": 0.0, "yolsuz": 0, "tur": {}}   # v42 Otağ Yeri
	for bcfg in biyomlar:
		var style: String = String(bcfg["id"])
		var s_walk := 0
		var s_ok3 := 0
		var s_min := 99
		var s_roll := 0
		var s_m := {}
		for k in n_seed:
			var rng := RandomNumberGenerator.new()
			rng.seed = 1000 + k * 7919 + style.length() * 31
			var dpt: int = int(bcfg["d0"]) + k % 2
			var gopts: Dictionary = (bcfg["level"] as Dictionary).duplicate()
			gopts["pazar"] = k % 3 == 0
			gopts["biyom"] = style
			gopts["gecmis"] = _gecmis_sim(1000 + k * 7919, dpt)
			if zorla != "":
				gopts["tur"] = zorla
			var t0 := Time.get_ticks_usec()
			var r := LevelGen.generate(rng, W, H, dpt, bcfg["styles"], gopts)
			var gen_sn := float(Time.get_ticks_usec() - t0) / 1000000.0
			var g: PackedByteArray = r["grid"]
			var hts: Array = r["heights"]
			tot += 1
			var bnd: Rect2i = r["bounds"]
			var hava := 0
			for yy in range(bnd.position.y, bnd.end.y):
				for xx in range(bnd.position.x, bnd.end.x):
					if g[yy * W + xx] != 1:
						hava += 1
			fixes[0] += int(r.get("carved", 0))
			fixes[1] += int(r.get("trapfix", 0))
			fixes[2] += int(r.get("headfix", 0))
			var m: Dictionary = r["metrics"]
			if bool(m["ok"]):
				ok_all += 1
			if int(m.get("pencere", 0)) > 0:
				pencere_var += 1
			var gh := LevelGen._haz_as_air(g)
			var rs := LevelGen.reach_set(g, W, H, hts)
			var n_stand := 0
			var n_reach := 0
			for i in rs.size():
				if LevelGen._standable(gh, i % W, i / W, W, H):
					n_stand += 1
					if rs[i] == 1:
						n_reach += 1
			var rk := float(n_reach) / maxf(1.0, float(n_stand))
			r["_d"] = dpt
			_otag_olc(ot, r, g, W, H, rs)   # v42
			reach_min = minf(reach_min, rk)
			var lo := 999
			var hi := 0
			for rm in r["rooms"]:
				if rm["role"] == "yok":
					continue
				for v in rm["fl"]:
					lo = mini(lo, int(v))
					hi = maxi(hi, int(v))
			m["ulasim"] = rk
			m["dusey"] = hi - lo
			tasi_min = mini(tasi_min, int(m["tasi"]))
			cikmaz_min = mini(cikmaz_min, int(m["cikmaz"]))
			for key in m:
				if typeof(m[key]) in [TYPE_INT, TYPE_FLOAT, TYPE_BOOL]:
					m_sum[key] = float(m_sum.get(key, 0.0)) + float(m[key])
					s_m[key] = float(s_m.get(key, 0.0)) + float(m[key])
			var any := reach(g, W, H, hts, 1)
			var walk := reach(g, W, H, hts, 2, true)
			var w3 := reach(g, W, H, hts, 3)
			var pmin := 99
			if walk["ok"]:
				var wp: Array = (walk["path"] as Array).duplicate()
				wp.reverse()
				var yo := yol_olcum(wp, W)
				var ek := {"gen_sn": gen_sn, "alan_w": bnd.size.x, "alan_h": bnd.size.y, "hava": hava, "yol_karo": yo["uzunluk"], "yol_sn": yo["sure"],
					"dusus": yo["dusus"], "tirmanis": yo["tirmanis"], "basamak": yo["basamak"], "zincir": yo["zincir"], "kzincir": yo["basamak_zinciri"]}
				ek["dikey_karo"] = yo["dikey_karo"]
				ek["y_aralik"] = yo["y_aralik"]
				for key in ek:
					m_sum[key] = float(m_sum.get(key, 0.0)) + float(ek[key])
					s_m[key] = float(s_m.get(key, 0.0)) + float(ek[key])
				var tk := String(r.get("tur", "eski"))
				var tm: Dictionary = tur_m.get(tk, {})
				for key in ["dikey_karo", "y_aralik", "yol_karo", "dusus", "tirmanis", "gen_sn", "hava"]:
					tm[key] = float(tm.get(key, 0.0)) + float(ek[key])
				tm["n"] = int(tm.get("n", 0)) + 1
				tm["dikey_adim"] = float(tm.get("dikey_adim", 0.0)) + float(m["dikey_adim"])
				tm["duz"] = int(tm.get("duz", 0)) + int(m.get("duz", 1 if int(m["dikey_adim"]) <= 1 else 0))
				tm[style] = int(tm.get(style, 0)) + 1
				tur_m[tk] = tm
				if not bool(LevelGen.TURLER.get(tk, {}).get("duz", false)):
					dikey_min = mini(dikey_min, int(m["dikey_adim"]))
				zincir_max = maxi(zincir_max, int(yo["zincir"]))
				for h in yo["dusus_hist"]:
					d_hist[h] = int(d_hist.get(h, 0)) + int(yo["dusus_hist"][h])
				d_max = maxi(d_max, int(yo["dusus_max"]))
				d_sersem += int(yo["sersem"])
				if int(yo["sersem"]) > 0:
					d_sersem_lv += 1
				kz_max = maxi(kz_max, int(yo["basamak_zinciri"]))
				sure_min = minf(sure_min, float(yo["sure"]))
				sure_max = maxf(sure_max, float(yo["sure"]))
				gen_max = maxf(gen_max, gen_sn)
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
		_p("IZGARA stil=%s yürüyerek=%d/%d 3karo=%d/%d yol_en_dar=%d yuvarlanma_hücresi=%d | oda=%.1f ana=%.1f dal=%.1f çıkmaz=%.1f döngü=%.1f dikey_adım=%.1f satır=%.1f taşı=%.1f zamanlı=%.1f ulaşım=%%%.1f düşey=%.0f karo deneme=%.2f onarım=%.1f" % [
			style, s_walk, n_seed, s_ok3, n_seed, s_min, s_roll, float(s_m.get("oda", 0)) / n_seed, float(s_m.get("ana", 0)) / n_seed, float(s_m.get("dal", 0)) / n_seed,
			float(s_m.get("cikmaz", 0)) / n_seed, float(s_m.get("dongu", 0)) / n_seed, float(s_m.get("dikey_adim", 0)) / n_seed, float(s_m.get("satir", 0)) / n_seed,
			float(s_m.get("tasi", 0)) / n_seed, float(s_m.get("zamanli", 0)) / n_seed, 100.0 * float(s_m.get("ulasim", 0)) / n_seed, float(s_m.get("dusey", 0)) / n_seed,
			float(s_m.get("attempts", 0)) / n_seed, float(s_m.get("trapfix", 0)) / n_seed])
		_p("OLCUM stil=%s alan=%.0fx%.0f hava=%.0f yol=%.0f karo (/koşu %.1f sn, hamle ~%.1f sn) düşüş=%.1f tırmanış=%.1f basamak=%.1f dikey_zincir=%.1f basamak_zinciri=%.1f üretim=%.2f sn" % [
			style, float(s_m.get("alan_w", 0)) / n_seed, float(s_m.get("alan_h", 0)) / n_seed, float(s_m.get("hava", 0)) / n_seed, float(s_m.get("yol_karo", 0)) / n_seed,
			float(s_m.get("yol_karo", 0)) / n_seed / KOSU_KARO, float(s_m.get("yol_sn", 0)) / n_seed, float(s_m.get("dusus", 0)) / n_seed, float(s_m.get("tirmanis", 0)) / n_seed, float(s_m.get("basamak", 0)) / n_seed,
			float(s_m.get("zincir", 0)) / n_seed, float(s_m.get("kzincir", 0)) / n_seed, float(s_m.get("gen_sn", 0)) / n_seed])
	_p("MERAK TOPLAM sapak=%%%.0f uzantı_odası=%.2f pencere=%.2f (en az 1: %%%.0f) gizli_cep=%.2f kilit=%.2f dal_ayrılışı=%.2f (ana yol sırası / uzunluk; 0 baş, 1 son) ana_yol_odası=%.1f" % [
		100.0 * float(m_sum.get("sapak", 0)) / tot, float(m_sum.get("uzanti", 0)) / tot, float(m_sum.get("pencere", 0)) / tot, 100.0 * float(pencere_var) / tot,
		float(m_sum.get("cep", 0)) / tot, float(m_sum.get("kilit", 0)) / tot, float(m_sum.get("dal_yeri", 0)) / tot, float(m_sum.get("ana", 0)) / tot])
	_p("IZGARA TOPLAM bölüm=%d yürüyerek(>=2)=%d 3karo=%d ana_yol_en_dar=%d en_iyi_yol_dağılımı=%s yuvarlanma_hücresi=%d (bölüm %d) 2karo_hücre=%d" % [tot, walk_ok, ok3, min_path_all, str(hist), roll_cells, roll_lv, tight_cells])
	_p("IZGARA onarım ortalaması: koridor %.2f, çıkmaz %.2f, açılan tavan karosu %.1f" % [float(fixes[0]) / tot, float(fixes[1]) / tot, float(fixes[2]) / tot])
	_p("IZGARA v32 ÇİZGE ortalama: oda=%.1f ana_yol=%.1f dal=%.2f çıkmaz=%.2f döngü=%.2f geniş=%.2f yüksek=%.2f dikey_adım=%.2f kesim_satırı=%.2f kapı=%.1f Kut_Taşı=%.2f zamanlı=%.2f ulaşım=%%%.1f (en az %%%.1f) düşey_aralık=%.0f karo | en az: taşı=%d çıkmaz=%d dikey=%d | erişim+dönüş=%d/%d" % [
		float(m_sum.get("oda", 0)) / tot, float(m_sum.get("ana", 0)) / tot, float(m_sum.get("dal", 0)) / tot, float(m_sum.get("cikmaz", 0)) / tot, float(m_sum.get("dongu", 0)) / tot,
		float(m_sum.get("genis", 0)) / tot, float(m_sum.get("yuksek", 0)) / tot, float(m_sum.get("dikey_adim", 0)) / tot, float(m_sum.get("satir", 0)) / tot, float(m_sum.get("kapi", 0)) / tot,
		float(m_sum.get("tasi", 0)) / tot, float(m_sum.get("zamanli", 0)) / tot, 100.0 * float(m_sum.get("ulasim", 0)) / tot, 100.0 * reach_min, float(m_sum.get("dusey", 0)) / tot,
		tasi_min, cikmaz_min, dikey_min, ok_all, tot])
	_p("OLCUM TOPLAM alan=%.0fx%.0f (hava %.0f karo) ana_yol=%.0f karo (/koşu %.1f sn; hamle modeli ~%.1f sn, %.1f-%.1f) düşüş=%.2f tırmanış=%.2f küçük_basamak=%.2f dikey_zincir ort=%.2f en_çok=%d basamak_zinciri ort=%.2f en_çok=%d üretim ort=%.2f sn en_çok=%.2f sn" % [
		float(m_sum.get("alan_w", 0)) / tot, float(m_sum.get("alan_h", 0)) / tot, float(m_sum.get("hava", 0)) / tot, float(m_sum.get("yol_karo", 0)) / tot, float(m_sum.get("yol_karo", 0)) / tot / KOSU_KARO,
		float(m_sum.get("yol_sn", 0)) / tot, sure_min, sure_max, float(m_sum.get("dusus", 0)) / tot, float(m_sum.get("tirmanis", 0)) / tot, float(m_sum.get("basamak", 0)) / tot,
		float(m_sum.get("zincir", 0)) / tot, zincir_max, float(m_sum.get("kzincir", 0)) / tot, kz_max, float(m_sum.get("gen_sn", 0)) / tot, gen_max])
	var dk := d_hist.keys()
	dk.sort()
	var ds := ""
	for h in dk:
		ds += "%d:%d " % [h, int(d_hist[h])]
	_p("DUSUS ana yol düşüşleri (karo:sayı) %s| en uzun=%d karo, sersemleten (> %.0f px) toplam=%d, bölüm=%d/%d" % [ds, d_max, float(Player.HERO["stun_h"]), d_sersem, d_sersem_lv, tot])
	_check(d_sersem_lv * 10 <= tot, "ana yolda yüksek düşüş sersemlemesi seyrek (bölümlerin en çok %%10'u; %d/%d)" % [d_sersem_lv, tot])
	_check(walk_ok == tot, "her bölümde ana yol yuvarlanmadan yürünür (%d/%d)" % [walk_ok, tot])
	_check(roll_cells == 0, "girişten ulaşılan yalnızca-yuvarlanma hücresi yok (%d)" % roll_cells)
	_check(ok_all == tot, "her bölümde giriş -> Kut Kapısı ve her ulaşılan hücreden dönüş (%d/%d)" % [ok_all, tot])
	_check(tasi_min >= 3, "her bölümde en az 3 Kut Taşı (en az %d)" % tasi_min)
	_check(cikmaz_min >= 2, "her bölümde en az 2 çıkmaz ödül odası (en az %d)" % cikmaz_min)
	_check(dikey_min >= 1, "düz olmayan türlerde ana yol en az bir kat iner / çıkar (en az %d)" % dikey_min)
	_otag_rapor(ot)   # v42
	_check(reach_min >= 0.85, "ayakta durma hücrelerinin en az %%85'i girişten ulaşılır (en az %%%.1f; kalanı yüksek cep / sarkıt üstü)" % (100.0 * reach_min))
	# v41 bölüm türleri: tür başına sayı ve ana yol dikeyliği; düz bölüm oranı; koşu benzetimi (art arda 3 kuralı)
	var n_duz := 0
	var dk_top := 0.0
	var da_top := 0.0
	var n_t := 0
	for tk in tur_m:
		var tm: Dictionary = tur_m[tk]
		var nn := float(tm["n"])
		var bs := ""
		for b in biyomlar:
			if tm.has(String(b["id"])):
				bs += "%s:%d " % [String(b["id"]), int(tm[String(b["id"])])]
		_p("TUR %s n=%d (%s) düz=%%%.0f dikey_adım=%.2f dikey_karo=%.1f y_aralığı=%.1f yol=%.0f karo düşüş=%.2f tırmanış=%.2f hava=%.0f üretim=%.2f sn" % [tk, int(nn), bs.strip_edges(),
			100.0 * float(tm["duz"]) / nn, float(tm["dikey_adim"]) / nn, float(tm["dikey_karo"]) / nn, float(tm["y_aralik"]) / nn, float(tm["yol_karo"]) / nn,
			float(tm["dusus"]) / nn, float(tm["tirmanis"]) / nn, float(tm["hava"]) / nn, float(tm["gen_sn"]) / nn])
		n_duz += int(tm["duz"])
		dk_top += float(tm["dikey_karo"])
		da_top += float(tm["dikey_adim"])
		n_t += int(nn)
	_p("TUR TOPLAM bölüm=%d düz (ana yol en çok 1 kat)=%%%.0f ana_yol_dikey_adım ort=%.2f ana_yol_dikey_karo (>=3 karoluk düşüş + tırmanış) ort=%.1f y_aralığı ort=%.1f düşüş=%.2f tırmanış=%.2f" % [n_t,
		100.0 * float(n_duz) / maxf(1.0, float(n_t)), da_top / maxf(1.0, float(n_t)), dk_top / maxf(1.0, float(n_t)), float(m_sum.get("y_aralik", 0)) / tot,
		float(m_sum.get("dusus", 0)) / tot, float(m_sum.get("tirmanis", 0)) / tot])
	if zorla == "":
		_check(float(n_duz) >= 0.35 * float(n_t), "bölümlerin en az %%35'i düz (%d/%d)" % [n_duz, n_t])
		var kosu := _kosu_sim(400)
		_p("TUR KOŞU benzetimi (400 koşu, derinlik 1-9): %s; art arda 3 düz olmayan=%d, düz oranı=%%%.0f" % [str(kosu["say"]), int(kosu["ihlal"]), 100.0 * float(kosu["duz"]) / float(kosu["n"])])
		_check(int(kosu["ihlal"]) == 0, "art arda üç bölümün en az biri düz (ihlal %d)" % int(kosu["ihlal"]))


func _biyomlar() -> Array:
	## v41: oyunun biyomları (world.json impl): kimlik, ilk derinlik, stil havuzu, level ayarları (rows / yon)
	var out: Array = []
	for b in Data.world["biomes"]:
		if not b.get("impl", false):
			continue
		var art: Dictionary = b.get("art", {})
		out.append({"id": String(b["id"]), "d0": int((b.get("depths", [1, 1]) as Array)[0]), "styles": art.get("styles", []), "level": b.get("level", {})})
	return out


func _gecmis_sim(tohum: int, d: int) -> Array:
	## v41: d'den önceki iki derinliğin türü (tür seçimi benzetimi; gerçek koşuda Game.run.turler)
	var out: Array = []
	for dd in range(maxi(1, d - 2), d):
		var r := RandomNumberGenerator.new()
		r.seed = tohum * 31 + dd
		out.append(LevelGen.tur_sec(r, String(Game.biome_for_depth(dd).get("id", "diger")), out.duplicate()))
	return out


func _kosu_sim(n: int) -> Dictionary:
	var say := {}
	var ihlal := 0
	var duz := 0
	var top := 0
	for k in n:
		var r := RandomNumberGenerator.new()
		r.seed = 77 + k * 1013
		var g: Array = []
		for d in range(1, 10):
			var t := LevelGen.tur_sec(r, String(Game.biome_for_depth(d).get("id", "diger")), g.slice(maxi(0, g.size() - 6)))
			g.append(t)
			say[t] = int(say.get(t, 0)) + 1
			top += 1
			if bool(LevelGen.TURLER[t]["duz"]):
				duz += 1
			if g.size() >= 3:
				var ok := false
				for i in range(g.size() - 3, g.size()):
					if bool(LevelGen.TURLER[String(g[i])]["duz"]):
						ok = true
				if not ok:
					ihlal += 1
	return {"say": say, "ihlal": ihlal, "duz": duz, "n": top}


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


static func _oda_id(lv: Node, p: Vector2) -> int:
	var rm: Dictionary = lv.room_at(int(floor(p.x / Level.TS)), int(floor((p.y - 4.0) / Level.TS)))
	return int(rm.get("id", -1))


static func icerik(lv: Node) -> Dictionary:
	## v34: oda başına içerik (yaratık, yerdeki ganimet / altın, küp, sandık, gizli duvar, pencere, tehlike karosu) ve
	## altın tanesi tahmini. "Boş oda": hiçbiri olmayan oda (Kut Taşı ve Kut Kapısı sayılmaz). Eski (v33) bölümde de
	## çalışır (v34 alanları yoksa sıfır).
	var out := {"dusman": 0, "d_ana": 0, "d_dal": 0, "d_odul": 0, "grup": 0, "karisik": 0, "seckin": 0, "bos": 0, "ana_bos": 0, "dal_bos": 0,
		"tane": 0, "tane_dusman": 0.0, "tane_gizli": 0.0, "tane_top": 0.0, "deger": 0.0, "pencere": 0, "kirik": 0, "kilit": 0, "anahtar": 0,
		"lanetli": 0, "kup": 0, "giris_yakin": 0, "tasi_yakin": 0}
	var say := {}   # oda kimliği -> içerik sayısı
	var dus := {}   # oda kimliği -> yaratık sayısı
	var TS := float(Level.TS)
	var sp := Vector2(lv.spawn_cell) * TS
	for e in lv.get_tree().get_nodes_in_group("dusman"):
		if not is_instance_valid(e) or e.is_queued_for_deletion() or e.get("level") != lv:
			continue
		out["dusman"] += 1
		if e.elite:
			out["seckin"] += 1
		out["tane_dusman"] += (1.75 if lv.get("kiriklar") != null else 3.0) + (10.0 if e.elite else 0.0)   # v34: 1-2 (+%25); v33: 2-4
		var id := _oda_id(lv, e.global_position)
		say[id] = int(say.get(id, 0)) + 1
		dus[id] = int(dus.get(id, 0)) + 1
		var ep: Vector2 = e.global_position
		if absf(ep.x - sp.x) < 10.0 * TS and absf(ep.y - sp.y) < 5.0 * TS:
			out["giris_yakin"] += 1
		for t in lv.tasi:
			if is_instance_valid(t) and t.global_position.distance_to(ep) < 4.0 * TS and absf(t.global_position.y - ep.y) < 3.0 * TS:
				out["tasi_yakin"] += 1
				if out["tasi_yakin"] <= 2:
					print("[harita]   taşa yakın: %s%s oda=%s x=%d" % [e.kind, "*" if e.elite else "", String(lv.room_at(int(ep.x / TS), int((ep.y - 4.0) / TS)).get("role", "?")), int(ep.x / TS)])
	for g in lv.get("gruplar") if lv.get("gruplar") != null else []:
		out["grup"] += 1
		if bool(g.get("karisik", false)):
			out["karisik"] += 1
	for c in lv.get_children():
		if c is Pickup and is_instance_valid(c):
			var id := _oda_id(lv, c.global_position)
			say[id] = int(say.get(id, 0)) + 1
			if String(c.kind) == "gold":
				out["tane"] += 1
	for key in ["kupler", "sandiklar", "kiriklar", "pencereler", "kilitler"]:
		var arr = lv.get(key)
		if arr == null:
			continue
		for n in arr:
			if not is_instance_valid(n):
				continue
			match key:
				"kupler":
					out["kup"] += 1
					out["tane_gizli"] += float(n.altin_ort())
				"sandiklar":
					out["lanetli"] += 1
					out["tane_gizli"] += float(n.altin)
				"kiriklar":
					out["kirik"] += 1
					out["tane_gizli"] += float(n.altin)
					if String(n.icerik) == "anahtar":
						out["anahtar"] += 1
				"pencereler":
					out["pencere"] += 1
				"kilitler":
					out["kilit"] += 1
			for id in n.odalar():
				say[id] = int(say.get(id, 0)) + 1
	for x in range(lv.bounds.position.x, lv.bounds.end.x):
		for y in range(lv.bounds.position.y, lv.bounds.end.y):
			if lv.cell(x, y) == 3:
				var rm: Dictionary = lv.room_at(x, y)
				var id := int(rm.get("id", -1))
				say[id] = int(say.get(id, 0)) + 1
	var bos_ad: Array = []
	for rm in lv.rooms:
		if rm["role"] == "yok":
			continue
		var id := int(rm["id"])
		var n_d := int(dus.get(id, 0))
		match String(rm["role"]):
			"ana", "giris", "cikis":
				out["d_ana"] += n_d
			"dal":
				out["d_dal"] += n_d
			"odul":
				out["d_odul"] += n_d
		if int(say.get(id, 0)) == 0 and String(rm.get("odul", "")) != "pazar":
			out["bos"] += 1
			bos_ad.append("%s#%d(%s)" % [rm["role"], id, String(rm.get("kind", ""))])
		if String(rm["role"]) in ["ana", "cikis"] and n_d == 0:
			out["ana_bos"] += 1
			print("[harita]   düşmansız ana yol odası: %s#%d %s genişlik=%d" % [rm["role"], id, String(rm.get("kind", "")), int(rm["ix1"]) - int(rm["ix0"]) + 1])
		if String(rm["role"]) == "dal" and n_d == 0:
			out["dal_bos"] += 1
	out["tane_top"] = float(out["tane"]) + float(out["tane_dusman"]) + float(out["tane_gizli"])
	var d := int(Game.run.get("depth", 1))
	out["deger"] = float(out["tane_top"]) * 2.0 * (1.0 + float(Pazar.data().get("altin", {}).get("artis", 0.3)) * (d - 1))
	out["_bos_ad"] = " ".join(bos_ad)
	return out


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
	var ics := {}      # v34: derinlik başına oda içeriği toplamı (icerik)
	var ic_top := {}
	var bos_ornek := 0
	var merak_den := {}
	var merak_hata: Array = []
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
			var ic := icerik(lv)
			for key in ic:
				if String(key).begins_with("_"):
					continue
				ics[key] = float(ics.get(key, 0.0)) + float(ic[key])
				ic_top[key] = float(ic_top.get(key, 0.0)) + float(ic[key])
			# v34: gizli cepler kırılınca cebin tabanından Kut Kapısı'na yol; anahtar girişten ulaşılır; kilit açılınca
			# kilitli odanın ödülüne yol
			if lv.get("kiriklar") != null:
				var W := Level.W
				# pencere: parmaklığın üstünden / yanından geçilemez (üstü ve iki yandaki sütunların tavanı kaya)
				for pk in lv.pencereler:
					var top: Vector2i = pk.cells[0]
					for c in pk.cells:
						top = c if c.y < top.y else top
					merak_den["pencere"] = int(merak_den.get("pencere", 0)) + 1
					var acik := false
					for yy in range(top.y - 6, top.y):
						if lv.cell(top.x, yy) != 1:
							acik = true
					if acik:
						var col := ""
						for yy in range(top.y - 8, top.y + 5):
							col += "%d" % lv.cell(top.x - 1, yy) + "%d" % lv.cell(top.x, yy) + "%d|" % lv.cell(top.x + 1, yy)
						merak_hata.append("pencere üstü açık d%d tohum=%d x=%d y=%d %s" % [d, k, top.x, top.y, col])
				for kk in lv.kilitler:
					lv.anahtar = 1
					kk.ac()
					var rm: Dictionary = lv.rooms[int(kk.oda)]
					var sp: Vector2i = LevelGen._floor_spot(lv.grid, W, Level.H, rm, LevelGen._odul_mid(rm))
					merak_den["kilit"] = int(merak_den.get("kilit", 0)) + 1
					if LevelGen.path_cells(lv.grid, W, Level.H, lv.spawn_cell.x, lv.spawn_cell.y, sp.x, sp.y).is_empty():
						merak_hata.append("kilit d%d tohum=%d" % [d, k])
				for kd in lv.kiriklar:
					kd._kir()
					var cp: Rect2i = kd.cep
					var pc := LevelGen.path_cells(lv.grid, W, Level.H, cp.position.x + 1, cp.end.y - 1, lv.exit_cell.x, lv.exit_cell.y)
					merak_den["cep"] = int(merak_den.get("cep", 0)) + 1
					if pc.is_empty():
						merak_hata.append("cep d%d tohum=%d x=%d y=%d" % [d, k, cp.position.x, cp.end.y - 1])
				for an in lv.anahtarlar:
					if not is_instance_valid(an):
						continue
					var sc := LevelGen.stand_cell(lv.grid, W, Level.H, an.global_position.x, an.global_position.y, Level.TS)
					merak_den["anahtar"] = int(merak_den.get("anahtar", 0)) + 1
					if LevelGen.path_cells(lv.grid, W, Level.H, lv.spawn_cell.x, lv.spawn_cell.y, sc.x, sc.y).is_empty():
						merak_hata.append("anahtar d%d tohum=%d" % [d, k])
				if lv.kilitler.size() > 0 and lv.anahtarlar.is_empty():
					var var_mi := false
					for kd in lv.kiriklar:
						var_mi = var_mi or String(kd.icerik) == "anahtar"
					if not var_mi:
						merak_hata.append("anahtarsız kilit d%d tohum=%d" % [d, k])
			if int(ic["bos"]) > 0 and bos_ornek < 4:
				bos_ornek += 1
				_p("  boş oda d%d tohum=%d stil=%s %s" % [d, k, lv.style, String(ic.get("_bos_ad", ""))])
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
		var ns := float(n_seed)
		_p("ICERIK %d | düşman/bölüm=%.1f (ana yol odası %.1f, dal %.1f, ödül %.1f) grup=%.1f karışık=%.1f seçkin=%.2f | boş oda=%.2f ana_yol_düşmansız=%.2f dal_bekçisiz=%.2f | altın tanesi: yerde=%.1f düşmandan~%.1f küp/zula/sandık~%.1f toplam~%.1f (değer ~%.0f) | pencere=%.2f gizli=%.2f kilit=%.2f anahtar=%.2f lanetli=%.2f küp=%.1f | girişe_yakın=%d taşa_yakın=%d" % [
			d, float(ics.get("dusman", 0)) / ns, float(ics.get("d_ana", 0)) / ns, float(ics.get("d_dal", 0)) / ns, float(ics.get("d_odul", 0)) / ns, float(ics.get("grup", 0)) / ns, float(ics.get("karisik", 0)) / ns, float(ics.get("seckin", 0)) / ns,
			float(ics.get("bos", 0)) / ns, float(ics.get("ana_bos", 0)) / ns, float(ics.get("dal_bos", 0)) / ns,
			float(ics.get("tane", 0)) / ns, float(ics.get("tane_dusman", 0)) / ns, float(ics.get("tane_gizli", 0)) / ns, float(ics.get("tane_top", 0)) / ns, float(ics.get("deger", 0)) / ns,
			float(ics.get("pencere", 0)) / ns, float(ics.get("kirik", 0)) / ns, float(ics.get("kilit", 0)) / ns, float(ics.get("anahtar", 0)) / ns, float(ics.get("lanetli", 0)) / ns, float(ics.get("kup", 0)) / ns,
			int(ics.get("giris_yakin", 0)), int(ics.get("tasi_yakin", 0))])
		ics = {}
	get_tree().paused = false
	var nl := 9.0 * n_seed
	_p("ICERIK TOPLAM düşman/bölüm=%.1f boş_oda=%d (bölüm başına %.2f) ana_yol_düşmansız=%d dal_bekçisiz=%d altın_tanesi/bölüm~%.1f (değer ~%.0f) pencere/bölüm=%.2f gizli=%.2f kilit=%.2f lanetli=%.2f küp=%.1f girişe_yakın=%d taşa_yakın=%d" % [
		float(ic_top.get("dusman", 0)) / nl, int(ic_top.get("bos", 0)), float(ic_top.get("bos", 0)) / nl, int(ic_top.get("ana_bos", 0)), int(ic_top.get("dal_bos", 0)),
		float(ic_top.get("tane_top", 0)) / nl, float(ic_top.get("deger", 0)) / nl, float(ic_top.get("pencere", 0)) / nl, float(ic_top.get("kirik", 0)) / nl, float(ic_top.get("kilit", 0)) / nl,
		float(ic_top.get("lanetli", 0)) / nl, float(ic_top.get("kup", 0)) / nl, int(ic_top.get("giris_yakin", 0)), int(ic_top.get("tasi_yakin", 0))])
	_p("MERAK denetim: kırılan cep=%d anahtar=%d açılan kilit=%d hata=%d %s" % [int(merak_den.get("cep", 0)), int(merak_den.get("anahtar", 0)), int(merak_den.get("kilit", 0)), merak_hata.size(), str(merak_hata.slice(0, 4))])
	_check(merak_hata.is_empty(), "gizli cepten Kut Kapısı'na, girişten anahtara ve açılan kilitli odaya yol var (%d hata)" % merak_hata.size())
	_check(int(ic_top.get("bos", 0)) == 0, "boş oda yok (düşman / ganimet / küp / tehlike / pencere / gizli duvar; %d)" % int(ic_top.get("bos", 0)))
	_check(int(ic_top.get("ana_bos", 0)) == 0, "her ana yol odasında en az bir yaratık grubu (düşmansız %d)" % int(ic_top.get("ana_bos", 0)))
	_check(int(ic_top.get("giris_yakin", 0)) == 0 and int(ic_top.get("tasi_yakin", 0)) == 0, "girişin dibinde / Kut Taşı çevresinde yaratık yok (%d / %d)" % [int(ic_top.get("giris_yakin", 0)), int(ic_top.get("tasi_yakin", 0))])
	_p("BOLUM TOPLAM düşman=%d geçersiz=%d taşınan=%d konmayan=%d nedenler=%s türler=%s eşya_katıda=%d" % [tot_e, tot_bad, tot_mv, tot_sk, str(reasons), str(kinds_bad), tot_item_bad])
	_check(tot_bad == 0, "geçersiz düşman yerleşimi yok (%d / %d)" % [tot_bad, tot_e])
	_check(tot_item_bad == 0, "eşya / tomar / sunak katı karoda değil (%d)" % tot_item_bad)
	_check(bz_ok, "tüccar duvarda değil (duvar_ok)")


func _merak_oyun() -> void:
	## v34 oynanış denetimi (gerçek fizik kareleri): küp kırılır ve altın düşer; çatlak duvar iki vuruşta açılır; anahtarsız
	## kilitli kapı kapalı kalır, anahtar alınınca yaklaşınca açılır; lanetli sandık açılınca lanet (hasar 2 kat), 10
	## öldürmede kalkar
	var ok := {"kup": false, "kirik": false, "kilit": false, "lanet": false, "inis_kup": false, "agir_duvar": false}
	for k in 80:
		var d: int = [1, 3, 5, 7, 9][k % 5]
		var lv := _build(d, 7100 + k * 31)
		main._start_play()
		await _phys(3)
		var pl: Node = lv.player
		Game.run["max_hp"] = 1000.0
		Game.run["hp"] = 1000.0
		var TS := float(Level.TS)
		if not ok["kup"] and not lv.kupler.is_empty():
			var kp: Node = lv.kupler[0]
			var once := 0
			for c in lv.get_children():
				if c is Pickup and String(c.kind) == "gold":
					once += 1
			lv.break_cracks(kp.rect())
			await _phys(2)
			var sonra := 0
			for c in lv.get_children():
				if c is Pickup and String(c.kind) == "gold" and not c.is_queued_for_deletion():
					sonra += 1
			ok["kup"] = sonra > once
			_p("OYUN küp: kırıldı=%s altın tanesi %d -> %d" % [str(not is_instance_valid(kp) or kp.kirildi), once, sonra])
		if not ok["kirik"] and not lv.kiriklar.is_empty():
			var kd: Node = lv.kiriklar[0]
			var w0: Vector2i = kd.cells[0]
			var r1: int = lv.cell(w0.x, w0.y)
			kd.vur(kd.rect())
			await _phys(15)
			var r2: int = lv.cell(w0.x, w0.y)
			kd.vur(kd.rect())
			await _phys(3)
			var r3: int = lv.cell(w0.x, w0.y)
			var cep: Rect2i = kd.cep
			ok["kirik"] = r1 == 1 and r2 == 1 and r3 == 0 and lv.cell(cep.position.x + 1, cep.end.y - 1) == 0 and kd.kirildi
			_p("OYUN gizli duvar: karo %d -> %d -> %d, cep açık=%s içerik=%s" % [r1, r2, r3, str(lv.cell(cep.position.x + 1, cep.end.y - 1) == 0), kd.icerik])
		if not ok["kilit"] and not lv.kilitler.is_empty():
			var kk: Node = lv.kilitler[0]
			_clear_foes(lv, Vector2(kk.cell) * TS, 99999.0)
			var yan := -1 if lv.cell(kk.cell.x - 1, kk.cell.y - 1) == 0 else 1
			pl.global_position = Vector2((kk.cell.x + yan) * TS + 12, kk.cell.y * TS - 1)
			pl.velocity = Vector2.ZERO
			await _phys(20)
			var kapali: bool = not kk.acik and lv.cell(kk.cell.x, kk.cell.y - 2) == 1
			# anahtar: gizli cepteyse duvarı kır, yerdeki anahtara dokun
			for kd in lv.kiriklar:
				if String(kd.icerik) == "anahtar":
					kd._kir()
			await _phys(2)
			var an_ok := false
			for an in lv.anahtarlar:
				if is_instance_valid(an):
					pl.global_position = an.global_position
					await _phys(4)
					an_ok = lv.anahtar > 0
					break
			pl.global_position = Vector2((kk.cell.x + yan) * TS + 12, kk.cell.y * TS - 1)
			await _phys(10)
			ok["kilit"] = kapali and an_ok and kk.acik and lv.cell(kk.cell.x, kk.cell.y - 2) == 0 and lv.anahtar == 0
			_p("OYUN kilit: anahtarsız kapalı=%s anahtar alındı=%s açıldı=%s geçit=%d" % [str(kapali), str(an_ok), str(kk.acik), lv.cell(kk.cell.x, kk.cell.y - 2)])
		if not ok["lanet"] and not lv.sandiklar.is_empty():
			var sd: Node = lv.sandiklar[0]
			_clear_foes(lv, sd.global_position, 400.0)
			pl.global_position = sd.global_position + Vector2(10, 0)
			await _phys(4)
			var yakin: bool = lv.sandik_yakin() == sd
			sd.ac()
			await _phys(2)
			var l0: int = lv.lanet
			var hp0 := float(Game.run["hp"])
			pl.inv_t = 0.0
			pl.roll_t = 0.0
			pl.take_hit(10.0, null)
			await _frames(3)
			await _phys(2)
			var kayip := hp0 - float(Game.run["hp"])
			# v34 birleştirme: lanet yalnız darbeyi iki katlar (zehir / yüksek düşüş öldürmez, iki kat sayılmaz)
			var hp_z := float(Game.run["hp"])
			pl.poison_t = 0.3
			pl._poison_tick = 0.0
			await _phys(4)
			var zehir := hp_z - float(Game.run["hp"])
			pl.poison_t = 0.0
			var n_old := 0
			for e in get_tree().get_nodes_in_group("dusman"):
				if lv.lanet <= 0:
					break
				if is_instance_valid(e) and not e.dead and e.level == lv:
					e.take_hit(1e7, {"kb": 0.0, "dir": signf(pl.global_position.x - e.global_position.x)})
					n_old += 1
					await _phys(20)
			ok["lanet"] = yakin and l0 == Level.LANET_OLDUR and kayip > 15.0 and lv.lanet == 0 and absf(zehir - 2.0) < 0.01
			_p("OYUN lanetli sandık: yakın=%s lanet=%d darbe 10 -> kayıp %.1f, zehir tıkı 2 -> kayıp %.1f, %d öldürme sonra lanet=%d" % [str(yakin), l0, kayip, zehir, n_old, lv.lanet])
			Game.run["lanet"] = 0
		# v34 birleştirme: gerçek oyuncu girdisiyle (Player -> Level.break_cracks) ağır silah savuruşu çatlak duvarı açar;
		# Kahraman İnişi'nin şok dalgası küpü kırar
		if not ok["agir_duvar"] and lv.kiriklar.size() > 1:
			var kd2: Node = lv.kiriklar[1]
			var wx: int = (kd2.cells[0] as Vector2i).x
			var y1 := 0
			for c in kd2.cells:
				y1 = maxi(y1, (c as Vector2i).y)
			_clear_foes(lv, kd2.rect().get_center(), 500.0)
			Game.run["slots"]["melee"] = ItemGen.roll("ulu_kilic", 1, "demir", 0)
			pl.on_equip()
			pl.global_position = Vector2((wx - kd2.yon) * TS + 12.0 - kd2.yon * 4.0, (y1 + 1) * TS - 1.0)
			pl.velocity = Vector2.ZERO
			pl.facing = kd2.yon
			await _phys(6)
			var basis := 0
			for i in 300:
				if kd2.kirildi:
					break
				if i % 20 == 0:
					Input.action_press("saldiri1")
					basis += 1
				elif i % 20 == 3:
					Input.action_release("saldiri1")
				await _phys(1)
			Input.action_release("saldiri1")
			ok["agir_duvar"] = kd2.kirildi
			_p("OYUN ağır silah (ulu kılıç) çatlak duvar: açıldı=%s basış=%d" % [str(kd2.kirildi), basis])
		if not ok["inis_kup"]:
			for kp2 in lv.kupler:
				if not is_instance_valid(kp2) or kp2.kirildi:
					continue
				var cx := int(kp2.global_position.x / TS)
				var cy := int(kp2.global_position.y / TS) - 1
				var acik := true
				for yy in range(cy - 6, cy + 1):
					if lv.cell(cx, yy) != 0:
						acik = false
				if not acik:
					continue
				_clear_foes(lv, kp2.global_position, 500.0)
				pl.global_position = kp2.global_position + Vector2(-30.0, -6.0 * TS)
				pl.velocity = Vector2.ZERO
				pl._air_top = pl.global_position.y
				pl.drop_t = 0.0
				await _phys(3)
				Input.action_press("asagi")
				await _phys(1)
				Input.action_press("zipla")
				await _phys(2)
				Input.action_release("zipla")
				var n0 := int(pl.hero_stats["n"])
				for i in 90:
					await _phys(1)
					if pl.hero_pose_t > 0.0:
						break
				Input.action_release("asagi")
				await _phys(2)
				var kirik: bool = not is_instance_valid(kp2) or kp2.kirildi
				ok["inis_kup"] = kirik
				_p("OYUN Kahraman İnişi küp: dalış=%d küp kırıldı=%s" % [int(pl.hero_stats["n"]) - n0 + (1 if pl.hero_pose_t > 0.0 else 0), str(kirik)])
				break
		if ok["kup"] and ok["kirik"] and ok["kilit"] and ok["lanet"] and ok["agir_duvar"] and ok["inis_kup"]:
			break
	main._start_play()
	for key in ok:
		_check(ok[key], "oynanış: %s" % {"kup": "küp kırılır, altın düşer", "kirik": "çatlak duvar iki vuruşta açılır, cep oyulur", "kilit": "kilitli kapı anahtarla açılır", "lanet": "lanetli sandık: hasar 2 kat, 10 öldürmede kalkar", "agir_duvar": "ağır silah savuruşu çatlak duvarı açar", "inis_kup": "Kahraman İnişi küpü kırar"}[key])


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
		"genel":
			await _ekran_genel()
		"kucuk":
			await _ekran_kucuk()
		"isin":
			await _ekran_isin()
		"tam":
			await _ekran_tam()
		"dusus":
			await _ekran_dusus()
		"merak":
			await _ekran_merak()
	get_tree().quit()


func _ekran_merak() -> void:
	## v34 çekimleri: (1) parmaklıklı pencere ardındaki ödül (yol odasından), (2) çatlak duvar, iki vuruş, açılan gizli
	## cep, (3) kalabalık oda (yaratıklar yerinde, oyuncu girişte), (4) yarı keşfedilmiş tam harita: "?" ipuçları,
	## lanetli sandık / kilit / anahtar işaretleri ve kalan ganimet sayacı (iki biyom)
	var tohum := int(_arg_or("--harita_tohum", "0"))
	var yapildi := {"pencere": false, "kirik": false, "kalabalik": false}
	var tam_n := 0
	var tam_biyom := {}
	for k in 60:
		var d: int = [1, 3, 5, 7, 9][k % 5]
		var lv := _build(d, 3500 + k * 53 + tohum)
		main._start_play()
		main.hud._card_t = 100.0
		await _phys(3)
		var pl: Node = lv.player
		for i in lv.harita.tasi.size():
			lv.harita.tasi_bul(i)
		var TS := Level.TS
		if not yapildi["pencere"] and not lv.pencereler.is_empty():
			var pk: Node = lv.pencereler[0]
			var A: Dictionary = lv.rooms[int(pk.oda_a)]
			var c0: Vector2i = pk.cells[0]
			var yon := 1 if int(A["ix1"]) < c0.x else -1   # pencere oyuncunun hangi yanında
			var fy: int = c0.y + int(pk.cells.size())
			_clear_foes(lv, Vector2(c0) * TS, 600.0)
			pl.global_position = Vector2((c0.x - yon * 3) * TS + 12, fy * TS - 1)
			pl.velocity = Vector2.ZERO
			pl.facing = yon
			Game.camera.snap()
			await _phys(50)
			await _snap("merak_pencere_%s_d%d" % [lv.style, d])
			yapildi["pencere"] = true
		if not yapildi["kirik"] and not lv.kiriklar.is_empty():
			var kd: Node = lv.kiriklar[0]
			var w0: Vector2i = kd.cells[0]
			var fy2: int = kd.cells[kd.cells.size() - 1].y + 1
			_clear_foes(lv, Vector2(w0) * TS, 600.0)
			pl.global_position = Vector2((w0.x - kd.yon * 2) * TS + 12, fy2 * TS - 1)
			pl.velocity = Vector2.ZERO
			pl.facing = kd.yon
			Game.camera.snap()
			await _phys(50)
			await _snap("merak_kirik_0_catlak_%s_d%d" % [lv.style, d])
			var box: Rect2 = kd.rect().grow(4.0)
			kd.vur(box)
			await _phys(20)
			await _snap("merak_kirik_1_vurus_%s_d%d" % [lv.style, d])
			kd._vur_t = 0.0
			kd.vur(box)
			await _phys(30)
			await _snap("merak_kirik_2_acildi_%s_d%d_%s" % [lv.style, d, kd.icerik])
			_p("kırık duvar: d=%d stil=%s içerik=%s kırıldı=%s karo=%d" % [d, lv.style, kd.icerik, str(kd.kirildi), lv.cell(w0.x, w0.y)])
			yapildi["kirik"] = true
		if not yapildi["kalabalik"]:
			# en kalabalık ana yol odası
			var best: Dictionary = {}
			var bn := 0
			for rm in lv.rooms:
				if not (rm["role"] in ["ana", "cikis"]):
					continue
				var n := 0
				for e in get_tree().get_nodes_in_group("dusman"):
					if is_instance_valid(e) and int(lv.room_at(int(e.global_position.x / TS), int((e.global_position.y - 4) / TS)).get("id", -1)) == int(rm["id"]):
						n += 1
				if n > bn:
					bn = n
					best = rm
			if bn >= 5:
				var x0 := int(best["ix0"]) + 1
				pl.global_position = Vector2(x0 * TS + 12, lv.room_floor(best, x0) * TS - 1)
				pl.velocity = Vector2.ZERO
				pl.facing = 1
				Game.camera.snap()
				await _phys(8)
				await _snap("merak_kalabalik_%s_d%d_%d" % [lv.style, d, bn])
				yapildi["kalabalik"] = true
		if tam_n < 2 and not tam_biyom.has(String(lv.biome.get("id", "?"))) and (not lv.sandiklar.is_empty() or not lv.kilitler.is_empty()) and not lv.pencereler.is_empty():
			tam_biyom[String(lv.biome.get("id", "?"))] = true
			# yarı keşif: ana yolun ilk 2/3'ü (çıkış sapağı ve dalların çoğu sisli: "?" ipuçları)
			_clear_foes(lv, Vector2.ZERO, 99999.0)
			var mr: Array = lv.main_rooms()
			var sinir := int(mr.size() * 2 / 3)
			var gezilen := func(x: int, y: int) -> bool:
				var rm: Dictionary = lv.room_at(x, y)
				if rm.is_empty():
					return false
				return int(rm.get("ana_i", -1)) >= 0 and int(rm["ana_i"]) <= sinir
			lv.harita.hepsini_kesfet(gezilen)
			var r0: Dictionary = mr[sinir]
			pl.global_position = Vector2(((int(r0["ix0"]) + int(r0["ix1"])) / 2) * TS + 12, lv.room_floor(r0, (int(r0["ix0"]) + int(r0["ix1"])) / 2) * TS - 1)
			await _phys(4)
			main._harita_ac()
			await _phys(6)
			await _snap("merak_tam_yari_%s_d%d" % [lv.biome.get("id", "?"), d])
			main._start_play()
			await _phys(2)
			# bütünüyle keşfedilmiş (işaretlerin hepsi)
			lv.harita.hepsini_kesfet()
			main._harita_ac()
			await _phys(6)
			await _snap("merak_tam_hepsi_%s_d%d" % [lv.biome.get("id", "?"), d])
			_p("tam harita: d=%d stil=%s sayaç=%s soru=%d" % [d, lv.style, lv.harita.sayac_metni(), lv.harita.sorular().size()])
			main._start_play()
			tam_n += 1
		if yapildi["pencere"] and yapildi["kirik"] and yapildi["kalabalik"] and tam_n >= 2:
			break
	_p("merak çekimleri: %s tam=%d" % [str(yapildi), tam_n])


# ------------------------------------------------------------------ v32 çekimleri
func _genel_kamera(lv: Node) -> Camera2D:
	## Bütün bölümü tek karede gösteren kamera (sınırlar ekrana sığar); oyuncu kamerası kapatılır
	var vp := get_viewport().get_visible_rect().size
	var b: Rect2i = lv.bounds
	var k := minf(vp.x / float(b.size.x * Level.TS), vp.y / float(b.size.y * Level.TS))
	var cam := Camera2D.new()
	cam.position = Vector2(b.get_center()) * Level.TS
	cam.zoom = Vector2.ONE * k
	cam.process_mode = Node.PROCESS_MODE_ALWAYS
	lv.add_child(cam)
	cam.make_current()
	return cam


func _ekran_genel() -> void:
	## Her biyomdan (derinlik 1, 3, 5, 7, 9) bütün bölümün genel görünümü: oyun karoları, süsler, ışıklar; HUD gizli
	var tohum := int(_arg_or("--harita_tohum", "7"))
	for d in [1, 3, 5, 7, 9]:
		for k in 2:
			var lv := _build(d, 3100 + d * 37 + k + tohum)
			main._start_play()
			main.hud.visible = false
			await _phys(3)
			_clear_foes(lv, Vector2.ZERO, 99999.0)
			var cam := _genel_kamera(lv)
			await _phys(20)
			await _snap("genel_%s_d%d_%s_%d" % [lv.biome.get("id", "?"), d, lv.style, k])
			cam.queue_free()
	main.hud.visible = true


func _ekran_kucuk() -> void:
	## Küçük harita: bot rehberi 14 sn gezer (sis açılır, taşlar bulunur), HUD çekilir; sonra tam ekran harita (M) ve
	## ayarlardaki üç harita boyu
	var d := int(_arg_or("--harita_derinlik", "1"))
	var lv := _build(d, 5100 + d)
	main._start_play()
	await _phys(3)
	var pl: Node = lv.player
	main.rehber.reset(lv)
	for i in 14 * 60:
		main.rehber.adim(main, pl, 1.0 / 60.0)
		await get_tree().physics_frame
		if i % 240 == 120:
			await _snap("kucuk_%02d" % (i / 240))
	for a in main.rehber._basili:
		Input.action_release(a)
	await _phys(10)
	for si in [1, 2, 3]:
		Ayarlar.harita_i = si
		await _phys(2)
		await _snap("kucuk_boy_%d" % si)
	Ayarlar.harita_i = 2
	main._harita_ac()
	await _phys(4)
	await _snap("tam_harita")
	_p("küçük: keşif=%%%d taşı=%d/%d ışınlanma=%d" % [int(round(lv.harita.yuzde() * 100.0)), lv.harita.bulunan().size(), lv.harita.tasi.size(), lv.isin_sayi])
	main._start_play()


func _ekran_tam() -> void:
	## v33: biyom başına (derinlik 1, 3, 5, 7, 9) bütünüyle keşfedilmiş tam ekran harita (M): Dead Cells örnek haritasıyla
	## karşılaştırma (küçük oda / koridor ağı); bütün Kut Taşları bulunmuş
	## v41: --tam_tur ile her bölüm türü iki biyomda (tür zorlanır: LevelGen.zorla_tur)
	var plan: Array = []
	if OS.get_cmdline_user_args().has("--tam_tur"):
		plan = [["acik", 1], ["acik", 3], ["kale", 4], ["kale", 9], ["inis", 2], ["inis", 9], ["magara", 5], ["magara", 7]]
	else:
		for d in [1, 3, 5, 7, 9]:
			plan.append(["", d])
	for pl in plan:
		var d: int = pl[1]
		LevelGen.zorla_tur = String(pl[0])
		var lv := _build(d, 3300 + d * 41 + int(_arg_or("--harita_tohum", "0")))
		LevelGen.zorla_tur = ""
		main._start_play()
		await _phys(3)
		_clear_foes(lv, Vector2.ZERO, 99999.0)
		lv.harita.hepsini_kesfet()
		for i in lv.harita.tasi.size():
			lv.harita.tasi_bul(i)
		main._harita_ac()
		await _phys(6)
		await _snap("tam_%s%s_d%d_%s" % ["" if String(pl[0]) == "" else String(pl[0]) + "_", lv.biome.get("id", "?"), d, lv.style])
		_p("tam: d=%d stil=%s sınır=%s oda=%d" % [d, lv.style, str(lv.bounds), lv.rooms.size()])
		main._start_play()
		await _phys(2)


func _ekran_dusus() -> void:
	## v33: oyun içi çekim: ana yolun açık düşüş kuyusunun kenarı (küçük harita sağ altta, o ana dek gezilmiş odalar
	## açık) ve düşüş anı; ardından tek yönlü kapaktan (dal kuyusu) aşağı + zıpla ile iniş
	for d in [1, 5, 3, 9, 7]:
		var lv := _build(d, 3400 + d * 43)
		var acik: Dictionary = {}
		var kapak: Dictionary = {}
		for dr in lv.doors:
			if dr["kind"] == "sil" or dr["dir"] != "v":
				continue
			if bool(dr.get("acik", false)) and acik.is_empty():
				acik = dr
			elif not bool(dr.get("acik", false)) and kapak.is_empty() and dr["kind"] == "dal":
				kapak = dr
		if acik.is_empty() or kapak.is_empty():
			lv.queue_free()
			main.level = null
			continue
		main._start_play()
		main.hud._card_t = 100.0
		await _phys(3)
		var pl: Node = lv.player
		_clear_foes(lv, Vector2.ZERO, 99999.0)
		for i in lv.harita.tasi.size():
			lv.harita.tasi_bul(i)
		var A: Dictionary = lv.rooms[int(acik["a"])]
		var ai := int(A.get("ana_i", 0))
		var sag_uc := int(A["ix1"]) + 2
		var gezilen := func(x: int, y: int) -> bool:
			var rm: Dictionary = lv.room_at(x, y)
			if rm.is_empty():
				return x <= sag_uc
			return int(rm.get("ana_i", 99)) >= 0 and int(rm.get("ana_i", 99)) <= ai
		lv.harita.hepsini_kesfet(gezilen)
		# 1) açık düşüş deliğinin kenarı (deliğe doğru bakar)
		var dx0 := int(acik["dus_x"])
		var fy := int(acik["y"])
		var kenar := dx0 - 1 if lv.cell(dx0 - 1, fy) == 1 else dx0 + 3
		var yon := 1 if kenar < dx0 else -1
		pl.global_position = Vector2(kenar * Level.TS + 12 - yon * 6, fy * Level.TS - 1)
		pl.velocity = Vector2.ZERO
		pl.facing = yon
		Game.camera.snap()
		await _phys(40)
		await _snap("dusus_%s_d%d_0_kenar" % [lv.style, d])
		# 2) düşüş: deliğe yürür, düşerken
		Input.action_press("sag" if yon > 0 else "sol")
		var t0 := 0
		while t0 < 90 and pl.global_position.y < (fy + 4) * Level.TS:
			await _phys(1)
			t0 += 1
		Input.action_release("sag" if yon > 0 else "sol")
		await _phys(4)
		await _snap("dusus_%s_d%d_1_dusus" % [lv.style, d])
		var t1 := 0
		while t1 < 90 and not pl.is_on_floor():
			await _phys(1)
			t1 += 1
		_p("düşüş: d=%d stil=%s kuyu x=%d %d->%d satır, düşüş %d kare, yerde=%s y=%d" % [d, lv.style, dx0, fy, int(acik.get("y2", 0)), t0 + t1, str(pl.is_on_floor()), int(pl.global_position.y / Level.TS)])
		# 3) dal kuyusunun kapağı: üstünde dur, aşağı + zıpla
		var kx := int(kapak["dus_x"]) + 1
		var ky := int(kapak["y"])
		pl.global_position = Vector2(kx * Level.TS + 12, ky * Level.TS - 1)
		pl.velocity = Vector2.ZERO
		Game.camera.snap()
		await _phys(30)
		await _snap("dusus_%s_d%d_2_kapak" % [lv.style, d])
		Input.action_press("asagi")
		await _phys(2)
		Input.action_press("zipla")
		await _phys(2)
		Input.action_release("zipla")
		await _phys(10)
		Input.action_release("asagi")
		await _snap("dusus_%s_d%d_3_kapaktan_inis" % [lv.style, d])
		var t2 := 0
		while t2 < 90 and not pl.is_on_floor():
			await _phys(1)
			t2 += 1
		_p("kapak: d=%d kuyu x=%d %d->%d, indi=%s y=%d (alt oda tabanı %d)" % [d, kx, ky, int(kapak.get("y2", 0)), str(int(pl.global_position.y / Level.TS) > ky + 2), int(pl.global_position.y / Level.TS), int(kapak.get("y2", 0))])
		return


func _ekran_isin() -> void:
	## Işınlanma dizisi: iki taş bulunur, harita ekranından seçim, kanal (0,9 sn) ve varış kareleri
	var lv := _build(int(_arg_or("--harita_derinlik", "1")), 5200)
	main._start_play()
	await _phys(3)
	var pl: Node = lv.player
	_clear_foes(lv, Vector2.ZERO, 99999.0)
	var c0: Vector2i = lv.harita.tasi[0]["cell"]
	var c1: Vector2i = lv.harita.tasi[1]["cell"]
	pl.global_position = Vector2(c1.x * Level.TS + 12, (c1.y + 1) * Level.TS - 1)
	pl.velocity = Vector2.ZERO
	await _phys(8)
	pl.global_position = Vector2((c0.x - 2) * Level.TS + 12, (c0.y + 1) * Level.TS - 1)
	pl.velocity = Vector2.ZERO
	Game.camera.snap()
	await _phys(30)
	await _snap("isin_00_tas")
	main._harita_ac()
	await _phys(3)
	await _snap("isin_01_harita")
	main._harita_sec(lv.harita.bulunan().find(1))
	for i in 12:
		await _phys(5)
		await _snap("isin_%02d" % (2 + i))
	_p("ışınlanma: sayı=%d bozuk=%d oyuncu=%s hedef=%s" % [lv.isin_sayi, lv.isin_bozuk, str((pl.global_position / Level.TS).floor()), str(c1)])


func _ekran_genis() -> void:
	## Geniş bölüm kesitleri: her stilden bir bölüm; 3 karo yüksek tünel, kule altı, hazine odası, seçkin odası, kurgan,
	## mağara tavanı / dar boğaz, kuyu önünde kareler
	var want := ["magara", "harabe", "kuyu", "bozkir", "ucurum", "orman"]
	var pref := ["hazine", "seckin", "tomar", "sunak", "pazar", "zamanli"]
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


# ------------------------------------------------------------------ v42 Otağ Yeri (OtagYeri.yerlesim) ölçümü
func _otag_olc(ot: Dictionary, r: Dictionary, g: PackedByteArray, W: int, H: int, rs: PackedByteArray) -> void:
	var ex: Vector2i = r["exit"]
	var avoid: Array = []
	for c in r.get("tasi", []):
		avoid.append(c)
	for kc in r.get("kaide", []):
		avoid.append(kc)
	for z in r.get("zamanli", []):
		avoid.append(Vector2i(int(z["x"]), int(z["y"]) - 1))
	for ch in r.get("chunks", []):
		for mk in ch.get("marks", []):
			avoid.append(Vector2i(int(mk[1]), int(mk[2])))
	var yer := OtagYeri.yerlesim(g, W, H, r["rooms"], ex, avoid)
	ot["n"] = int(ot["n"]) + 1
	ot["yer"] = int(ot["yer"]) + yer.size()
	if yer.size() >= 4:
		ot["dort"] = int(ot["dort"]) + 1
	if yer.size() >= 3:
		ot["uc"] = int(ot["uc"]) + 1
	var odalar := {}
	var uzak := 0
	var yakin := 999
	var hepsi_erisir := true
	for y in yer:
		var x := int(y["x"])
		var yy := int(y["y"])
		odalar[int(y["oda"])] = true
		var dx := absi(x - ex.x) + absi(yy - ex.y)
		uzak = maxi(uzak, dx)
		yakin = mini(yakin, dx)
		if rs[yy * W + x] != 1:
			hepsi_erisir = false
		if absi(x - ex.x) < 5 and absi(yy - ex.y) < 4:
			ot["kapi_yakin"] = int(ot["kapi_yakin"]) + 1
	if hepsi_erisir:
		ot["erisim"] = int(ot["erisim"]) + 1
	ot["uzak_top"] = float(ot["uzak_top"]) + uzak
	ot["yakin_top"] = float(ot["yakin_top"]) + (yakin if yakin < 999 else 0)
	if odalar.size() >= 2:
		ot["oda2"] = int(ot["oda2"]) + 1
	var tk := String(r.get("tur", "?"))
	var tt: Dictionary = ot["tur"]
	if not tt.has(tk):
		tt[tk] = [0, 0]
	tt[tk][0] += 1
	tt[tk][1] += 1 if yer.size() >= 4 else 0
	var ys := OtagYeri.yol_suresi(g, W, H, r["spawn"], ex)
	if ys < 0.0:
		ot["yolsuz"] = int(ot["yolsuz"]) + 1
		ys = 24.0
	var mana := 0
	for rm in r["rooms"]:
		if int(rm.get("ana_i", -1)) >= 0 and rm["role"] != "yok":
			mana += 1
	var ps := OtagYeri.par_sure(ys, mana, int(r.get("_d", 1)))
	ot["yol_top"] = float(ot["yol_top"]) + ys
	ot["par_top"] = float(ot["par_top"]) + ps
	ot["par_min"] = minf(float(ot["par_min"]), ps)
	ot["par_max"] = maxf(float(ot["par_max"]), ps)


func _otag_rapor(ot: Dictionary) -> void:
	var n := maxf(1.0, float(ot["n"]))
	var ts := ""
	for k in ot["tur"]:
		ts += "%s %d/%d " % [k, int(ot["tur"][k][1]), int(ot["tur"][k][0])]
	_p("OTAG bölüm=%d yer ort=%.2f 4_otağ (Han dahil)=%%%.0f en_az_3=%%%.0f hepsi_erişilir=%d/%d Kut_Kapısı_dibinde=%d iki_odaya_yayılan=%%%.0f kapıya_uzaklık yakın=%.1f uzak=%.1f karo | tür (4 otağ): %s" % [int(ot["n"]),
		float(ot["yer"]) / n, 100.0 * float(ot["dort"]) / n, 100.0 * float(ot["uc"]) / n, int(ot["erisim"]), int(ot["n"]), int(ot["kapi_yakin"]), 100.0 * float(ot["oda2"]) / n,
		float(ot["yakin_top"]) / n, float(ot["uzak_top"]) / n, ts.strip_edges()])
	_p("OTAG Çabuk süresi: yol ort=%.1f sn (yolu bulunamayan %d) par ort=%.0f sn (%.0f-%.0f)" % [float(ot["yol_top"]) / n, int(ot["yolsuz"]), float(ot["par_top"]) / n, float(ot["par_min"]), float(ot["par_max"])])
	_check(int(ot["uc"]) == int(ot["n"]), "her bölümde en az 3 sınav otağı yeri (%d/%d)" % [int(ot["uc"]), int(ot["n"])])
	_check(float(ot["dort"]) >= 0.9 * n, "bölümlerin en az %%90'ında Han Otağı'na da yer (%d/%d)" % [int(ot["dort"]), int(ot["n"])])
	_check(int(ot["erisim"]) == int(ot["n"]), "her otağın kapısı girişten erişilir (%d/%d)" % [int(ot["erisim"]), int(ot["n"])])
	_check(int(ot["kapi_yakin"]) == 0, "Kut Kapısı önü (5 karo) boş (%d otağ dipte)" % int(ot["kapi_yakin"]))
