extends Node
## v38 başarım ölçümü (-- --perf [--perf_faz=uretim,yurt,konak,gezinti,savas3,savas7] [--perf_sure=60]):
##   uretim : 20 tohumda bölüm kurma süresi (Main._build_level; derinlik 1..10) + kurulumdan sonraki ilk kare,
##            her kurulumdan sonra düğüm / nesne sayısı (sızıntı: kurulumlar arasında büyümemeli)
##   yurt / konak : Ulu Kayın yurdu ve gezgin konak, bot yürür (10 sn)
##   gezinti: 2. derinlik, rehber botu bölümü gezer, küçük harita açık (45 sn)
##   savas3 / savas7: gerçek bölüm (3. / 7. derinlik), oyuncunun çevresinde ~25 düşman, bot dövüşür, test 0,4 sn'de bir
##            yakındaki düşmanı öldürür (gore / kan / ceset), eksilen düşman yenilenir (60 sn); sonunda düşmanlar
##            temizlenip 4 sn beklenir: düğüm sayısı dövüş öncesine dönmeli (sızıntı denetimi)
## Her evre için: kare süresi ort / p95 / p99 / en kötü (duvar saati), TIME_PROCESS / TIME_PHYSICS_PROCESS,
## düğüm / nesne / çizim çağrısı / statik bellek, 33 ms'yi aşan takılmalar (o karenin en pahalı sistemleriyle) ve
## Prof (scripts/core/Prof.gd) sistem başına kare başı ms tablosu. Satırlar "[perf] ...".
## Pencereli koşuda dikey eşitleme kapatılır (kare süresi gerçek maliyet olsun): --fixed-fps 60 ile çalıştırın.

var main: Node
var fazlar: Array = ["uretim", "yurt", "konak", "gezinti", "savas3", "savas7"]
var sure_k := 1.0

# evre ölçüm durumu
var _olc := false
var _ad := ""
var _prev_us := 0
var _kare: PackedFloat32Array = PackedFloat32Array()
var _proc: PackedFloat32Array = PackedFloat32Array()
var _fiz: PackedFloat32Array = PackedFloat32Array()
var _takilma: Array = []
var _prof_onceki: Dictionary = {}
var _dugum_ilk := 0
var _dugum_max := 0
var _cizim_max := 0
var _t_evre := 0.0
var _olay := ""   # bu karede testin yaptığı iş (takılma nedeni)
var _sonuc: Array = []


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	process_priority = -1000   # karenin ilk düğümü: kare süresi bir önceki karenin tamamı
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--perf_faz="):
			fazlar = Array(String(arg).trim_prefix("--perf_faz=").split(","))
		if String(arg).begins_with("--perf_sure="):
			sure_k = float(String(arg).trim_prefix("--perf_sure=")) / 60.0
	Prof.on = true
	if DisplayServer.get_name() != "headless":
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
		Engine.max_fps = 0
	Ayarlar.harita_i = 2   # küçük harita açık (yalnızca bellekte; ayar dosyasına yazılmaz)
	_run.call_deferred()


func _process(_d: float) -> void:
	var now := Time.get_ticks_usec()
	if not Game.run.is_empty():
		Game.run["hp"] = float(Game.run.get("max_hp", 100.0))   # oyuncu ölmez: ölçüm kesilmesin
	if main and main.hud and main.hud.mode == "slot":
		main._start_play()   # yerden eşya alınca açılan yuva seçimi ağacı durduruyordu (bot bu ekranı çözmez)
	if _olc:
		var ms := float(now - _prev_us) / 1000.0
		_kare.append(ms)
		_proc.append(Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0)
		_fiz.append(Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0)
		var dn := int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))
		_dugum_max = maxi(_dugum_max, dn)
		_cizim_max = maxi(_cizim_max, int(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)))
		if ms > 33.0:
			var en: Array = []
			for k in Prof.acc:
				var d := float(int(Prof.acc[k]) - int(_prof_onceki.get(k, 0))) / 1000.0
				if d > 1.0:
					en.append([d, String(k)])
			en.sort_custom(func(a, b): return a[0] > b[0])
			var s := ""
			for i in mini(4, en.size()):
				s += "%s %.1f " % [en[i][1], en[i][0]]
			_takilma.append("t=%.1f %.1fms dugum=%d olay=%s [%s]" % [_t_evre, ms, dn, _olay, s.strip_edges()])
		_prof_onceki = Prof.acc.duplicate()
	_olay = ""
	_prev_us = now


func _bekle(s: float) -> void:
	await get_tree().create_timer(s, true, false, true).timeout


func _basla(ad: String) -> void:
	_ad = ad
	_kare = PackedFloat32Array()
	_proc = PackedFloat32Array()
	_fiz = PackedFloat32Array()
	_takilma.clear()
	_dugum_ilk = int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))
	_dugum_max = _dugum_ilk
	_cizim_max = 0
	Prof.sifirla()
	_prof_onceki = {}
	_t_evre = 0.0
	_olc = true


func _yuzde(a: PackedFloat32Array, q: float) -> float:
	if a.is_empty():
		return 0.0
	var b := a.duplicate()
	b.sort()
	return b[clampi(int(floor(q * float(b.size() - 1))), 0, b.size() - 1)]


func _ort(a: PackedFloat32Array) -> float:
	var s := 0.0
	for v in a:
		s += v
	return s / maxf(1.0, float(a.size()))


func _bitir(ek := "") -> void:
	_olc = false
	var n := _kare.size()
	var mx := 0.0
	for v in _kare:
		mx = maxf(mx, v)
	var satir := "%s kare=%d ort=%.2f p95=%.2f p99=%.2f max=%.2f | proc p50=%.2f p99=%.2f | fizik p50=%.2f p99=%.2f | dugum %d->%d (max %d) nesne=%d cizim_max=%d bellek=%.1fMB %s" % [
		_ad, n, _ort(_kare), _yuzde(_kare, 0.95), _yuzde(_kare, 0.99), mx, _yuzde(_proc, 0.5), _yuzde(_proc, 0.99), _yuzde(_fiz, 0.5), _yuzde(_fiz, 0.99),
		_dugum_ilk, int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT)), _dugum_max, int(Performance.get_monitor(Performance.OBJECT_COUNT)),
		_cizim_max, Performance.get_monitor(Performance.MEMORY_STATIC) / 1048576.0, ek]
	print("[perf] EVRE " + satir)
	_sonuc.append(satir)
	# sistem başına kare başı ms (Prof)
	var ks: Array = Prof.acc.keys()
	ks.sort_custom(func(a, b): return int(Prof.acc[a]) > int(Prof.acc[b]))
	var tablo := ""
	for k in ks:
		tablo += "%s=%.3f(%d) " % [String(k), float(Prof.acc[k]) / 1000.0 / maxf(1.0, float(n)), int(Prof.say[k]) / maxi(1, n)]
	print("[perf] SISTEM %s ms/kare: %s" % [_ad, tablo])
	for i in mini(12, _takilma.size()):
		print("[perf] TAKILMA %s %s" % [_ad, _takilma[i]])
	if _takilma.size() > 12:
		print("[perf] TAKILMA %s ... toplam %d" % [_ad, _takilma.size()])


func _dusmanlar() -> Array:
	var out: Array = []
	for e in get_tree().get_nodes_in_group("dusman"):
		if is_instance_valid(e) and not e.dead and not e.is_queued_for_deletion():
			out.append(e)
	return out


func _sure(s: float) -> float:
	return s * sure_k


func _run() -> void:
	await _bekle(1.0)
	main.auto_test = true   # Main bot: mod geçişlerini (tılsım, konak, harita) kendisi çözer
	for f in fazlar:
		match String(f):
			"uretim":
				await _uretim()
			"yurt":
				await _yurt()
			"konak":
				await _konak()
			"gezinti":
				await _gezinti()
			"savas3":
				await _savas(3)
			"savas7":
				await _savas(7)
	print("[perf] OZET ----")
	for s in _sonuc:
		print("[perf] OZET " + String(s))
	print("[perf] BITTI")
	Prof.on = false
	get_tree().quit()


func _uretim() -> void:
	var tl: Array = []
	var ilk: Array = []
	var nesne: Array = []
	var dugum: Array = []
	main._depth_forced = true
	Prof.sifirla()
	for i in 20:
		Game.run["depth"] = 1 + i % 10
		Game.run["tier"] = Zorluk.kademe(int(Game.run["depth"]))
		seed(1000 + i)
		var t0 := Time.get_ticks_usec()
		main._build_level()
		main._start_play()
		tl.append(float(Time.get_ticks_usec() - t0) / 1000.0)
		var t1 := Time.get_ticks_usec()
		await get_tree().process_frame
		ilk.append(float(Time.get_ticks_usec() - t1) / 1000.0)
		await get_tree().process_frame
		await get_tree().process_frame
		dugum.append(int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT)))
		nesne.append(int(Performance.get_monitor(Performance.OBJECT_COUNT)))
	var s := 0.0
	var mx := 0.0
	for v in tl:
		s += float(v)
		mx = maxf(mx, float(v))
	var s2 := 0.0
	var mx2 := 0.0
	for v in ilk:
		s2 += float(v)
		mx2 = maxf(mx2, float(v))
	var satir := "uretim tohum=20 kurma_ort=%.1fms kurma_max=%.1fms ilk_kare_ort=%.1fms ilk_kare_max=%.1fms dugum=%s nesne_ilk=%d nesne_son=%d" % [
		s / 20.0, mx, s2 / 20.0, mx2, str(dugum), int(nesne[0]), int(nesne[nesne.size() - 1])]
	print("[perf] EVRE " + satir)
	print("[perf] URETIM sureler=%s" % str(tl.map(func(v): return snappedf(v, 0.1))))
	print("[perf] URETIM nesne=%s" % str(nesne))
	var ks: Array = Prof.acc.keys().filter(func(k): return String(k).begins_with("kur"))
	ks.sort_custom(func(a, b): return int(Prof.acc[a]) > int(Prof.acc[b]))
	var tablo := ""
	for k in ks:
		tablo += "%s=%.1f " % [String(k).trim_prefix("kur_"), float(Prof.acc[k]) / 1000.0 / 20.0]
	print("[perf] URETIM adim_ms(ort): " + tablo)
	_sonuc.append(satir)


func _yurt() -> void:
	main._build_hub()
	main._start_play()
	await _bekle(1.0)
	_basla("yurt")
	await _sur(_sure(10.0))
	_bitir()


func _konak() -> void:
	Game.run["depth"] = 3
	main._build_konak()
	main._start_play()
	await _bekle(1.0)
	_basla("konak")
	await _sur(_sure(6.0))
	_bitir()


func _sur(s: float) -> void:
	## s saniye ölç; bot kapıdan geçip bölüm değişirse ölçüm orada biter (kurulum takılması bu evreye sayılmasın)
	var lv: Node = main.level
	var t := 0.0
	while t < s:
		await get_tree().process_frame
		t += get_process_delta_time()
		_t_evre = t
		if main.level != lv:
			_kare.resize(maxi(0, _kare.size() - 1))
			print("[perf] %s: bölüm değişti, ölçüm %.1f sn'de bitti" % [_ad, t])
			return


func _gezinti() -> void:
	Game.run["depth"] = 2
	Game.run["tier"] = Zorluk.kademe(2)
	main._bot_gercek = false
	seed(2002)
	main._build_level()
	main._start_play()
	await _bekle(1.0)
	_basla("gezinti")
	var lv: Node = main.level
	var t := 0.0
	while t < _sure(45.0):
		await get_tree().process_frame
		var dt := get_process_delta_time()
		t += dt
		_t_evre = t
		if main.level != lv:
			_olay = "bolum_degisti"
			lv = main.level
	_bitir("kesif=%%%d" % int(round(main.level.harita.yuzde() * 100.0)) if main.level and main.level.harita else "")


func _savas(derinlik: int) -> void:
	Game.run["depth"] = derinlik
	Game.run["tier"] = Zorluk.kademe(derinlik)
	main._bot_gercek = true
	seed(3000 + derinlik)
	main._build_level()
	main._start_play()
	await _bekle(1.0)
	var lv: Node = main.level
	# bölümün kendi düşmanlarını temizle: ölçüm oyuncunun çevresindeki kalabalıkla yapılır
	for e in _dusmanlar():
		e.queue_free()
	await _bekle(0.5)
	var dugum0 := int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))
	var hist0 := _histogram()
	var pool: Array = lv._biome_pool()
	var rng := RandomNumberGenerator.new()
	rng.seed = 77 + derinlik
	var pl: Node2D = lv.player
	var merkez := pl.global_position   # dövüş alanı: bot düşmansız anda rehberle Kut Kapısı'na yürümesin
	Game.run["max_hp"] = 100000.0   # derin bölümde tek karede gelen birden çok vuruş da öldürmesin (ölüm yeni koşu kurar)
	Game.run["hp"] = 100000.0
	_basla("savas%d" % derinlik)
	var t := 0.0
	var t_spawn := 0.0
	var t_kill := 0.0
	var olum := 0
	var dogan := 0
	while t < _sure(60.0):
		await get_tree().process_frame
		var dt := get_process_delta_time()
		t += dt
		_t_evre = t
		if main.level != lv or not is_instance_valid(pl):
			_olay = "bolum_degisti"
			break
		t_spawn -= dt
		t_kill -= dt
		if pl.global_position.distance_to(merkez) > 420.0:
			pl.global_position = merkez
			pl.velocity = Vector2.ZERO
			_olay += "geri "
		var ens := _dusmanlar()
		if t_spawn <= 0.0 and ens.size() < 22:
			t_spawn = 0.5
			var n := 0
			var dene := 0
			while ens.size() + n < 25 and n < 6 and dene < 16:
				# yer denetimli doğum (Level.find_spawn); sığmazsa başka uzaklık denenir
				var kind: String = pool[rng.randi_range(0, pool.size() - 1)]
				var dx := rng.randf_range(60.0, 480.0) * (1.0 if rng.randf() < 0.5 else -1.0)
				var e: Node = lv.spawn_enemy(kind, pl.global_position + Vector2(dx, -4.0), rng.randf() < 0.08, false, true)
				dene += 1
				if e:
					n += 1
					dogan += 1
			_olay += "dogum%d " % n
		if t_kill <= 0.0 and not ens.is_empty():
			t_kill = 0.4
			var best: Node = null
			var bd := 1e9
			for e in ens:
				var d: float = (e.global_position - pl.global_position).length()
				if d < bd:
					bd = d
					best = e
			if best and bd < 420.0:
				var heavy := olum % 3 == 2
				best.take_hit(float(best.hp) * (1.0 if olum % 2 == 0 else 2.2) + 1.0, {"dir": 1 if best.global_position.x > pl.global_position.x else -1,
					"kb": 340.0 if heavy else 140.0, "heavy": heavy, "crit": olum % 4 == 1})
				olum += 1
				_olay += "olum "
	var ek := "olum=%d dogan=%d oldurulen_toplam=%d gore=%s" % [olum, dogan, int(Game.run.get("kills", 0)), str(Gore.stats())]
	_bitir(ek)
	# sızıntı denetimi: düşmanları temizle, efektler / cesetler / lekeler sönsün
	for e in get_tree().get_nodes_in_group("dusman"):
		e.queue_free()
	await _bekle(6.0)
	print("[perf] SIZINTI savas%d dugum_once=%d dugum_sonra=%d nesne=%d mod=%s duraklat=%s gore=%s" % [derinlik, dugum0,
		int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT)), int(Performance.get_monitor(Performance.OBJECT_COUNT)),
		String(main.hud.mode), str(get_tree().paused), str(Gore.stats())])
	# hangi düğüm türü arttı (betik adı ya da sınıf): pickup / ceset gibi beklenenler ile sızıntıyı ayırmak için
	var hist1 := _histogram()
	var fark := ""
	for k in hist1:
		var d := int(hist1[k]) - int(hist0.get(k, 0))
		if d >= 3:
			fark += "%s+%d " % [k, d]
	print("[perf] SIZINTI savas%d artan: %s" % [derinlik, fark])


func _histogram() -> Dictionary:
	var h := {}
	var st: Array = [get_tree().root]
	while not st.is_empty():
		var n: Node = st.pop_back()
		var sc: Script = n.get_script()
		var k: String = sc.resource_path.get_file().get_basename() if sc else n.get_class()
		h[k] = int(h.get(k, 0)) + 1
		st.append_array(n.get_children())
	return h
