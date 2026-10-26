extends Node
## Oyun durumu: giriş haritası, koşu (run) verisi, kalıcı kayıt (kilitler, parşömenler, Kut bankası),
## kamera sarsıntısı/itişi, vuruş duraklaması ve ağır çekim.

const SAVE_PATH := "user://kayit.json"
const LAYER_WORLD := 1
const LAYER_PLAYER := 2
const LAYER_ENEMY := 4
const LAYER_PLATFORM := 8

## Her koşuda açık olan eşyalar; diğerleri parşömenle Demirci'de açılır.
const BASE_UNLOCKED := ["alp_kilici", "turk_yayi", "kara_barut", "yuvarlak_kalkan", "pala", "coban_sapani"]

## Tanrı lütufları (sunaktan alınır; bir sonraki konağa dek sürer — v32'den önce yurda dönene dek —, en çok 3)
const LUTUF := {
	"tengri": ["Tengri'nin Yıldırımı", "Darbeler %22 şansla yakındaki düşmana şimşekle sıçrar.", [0.7, 0.85, 1.0]],
	"ulgen": ["Ülgen'in Işığı", "Her öldürmede %3 can.", [1.0, 0.95, 0.6]],
	"umay": ["Umay'ın Kanadı", "Havada iki kez daha zıpla.", [0.6, 1.0, 1.0]],
	"erlik": ["Erlik'in Gölgesi", "Hasar +%35; en yüksek can -%20.", [0.7, 0.3, 0.9]],
	"kayra": ["Kayra'nın Kutu", "Kut iki kat hızlı dolar.", [0.45, 0.93, 1.0]],
	"yer_sub": ["Yer-Sub Zırhı", "Alınan hasar -%25.", [0.55, 0.85, 0.45]],
	"ay_ata": ["Ay Ata'nın Gözü", "Kritik şansı +%10.", [0.85, 0.9, 1.0]],
	"gun_ana": ["Gün Ana'nın Közü", "Darbeler %25 şansla tutuşturur.", [1.0, 0.6, 0.3]],
	"yel_ana": ["Yel Ana'nın Soluğu", "Saldırı hızı +%10.", [0.72, 0.95, 0.82]],   # v20 (Player.HIZ.lutuf; v25: 15 → 10)
}
## Boss arenaları: bu derinlik bitince (Kut Kapısı) önce boss, sonra konak (v32; eskiden yurt)
const BOSS_AFTER := {2: "kara_boru_han", 4: "tepegoz", 6: "sahmeran", 8: "yelbegen", 10: "erlik_han"}

## Umay Ana'nın kalıcı armağanları: Kut bankasıyla alınır (Dead Cells "Collector" mantığı).
## id: [ad, açıklama, [seviye maliyetleri...]]
const UMAY := {
	"sise": ["Umay'ın Şişesi", "Koşuya +1 şifa şişesiyle başla.", [30, 70]],
	"can": ["Kayın Özü", "En yüksek can +%10.", [25, 45, 75]],
	"kut_koruma": ["Ruh Düğümü", "Ölünce taşıdığın Kut'un %30 / %60'ı Umay'a ulaşır.", [40, 90]],
	"altin": ["Ata Kesesi", "Koşuya +60 altınla başla.", [20, 40]],
	"kut_hizi": ["Bozkurt Çağrısı", "Kut gücü %20 daha hızlı dolar.", [35, 70]],
	"silah": ["Demirci Dostu", "Başlangıç silahı bir kademe üstün döner.", [60]],
	"hiz": ["Kam Davulu", "Saldırı hızı +%3 (her seviye).", [40, 85]],   # v20 (Player.HIZ.umay; v25: 4 → 3)
}

var meta: Dictionary = {}
var run: Dictionary = {}
var camera: Camera2D
var shake_amount := 0.0
var kick_off := Vector2.ZERO
## Travma tabanlı sarsıntı (Vlambeer / Nijman): olaylar travma ekler, kamera travma² ile sallanır,
## travma üstel söner. Yön verilirse sarsıntı o eksende yoğunlaşır (ağır tepeden vuruş kamerayı aşağı iter).
var trauma := 0.0
var trauma_dir := Vector2.ZERO
var _noise_t := 0.0
var _rumble_until := 0.0
var look_ahead := 0.0   # kamera ileri bakış (oyuncu yazar, Level kamerayı taşır)
var fx_scale := 1.0     # Ayarlar > Sarsıntı ve flaş: 1 tam, 0,5 azaltılmış, 0 kapalı
const SHAKE_MAX := Vector2(10.0, 7.0)
const KICK_MAX := 9.0
const SHAKE_ROT := 0.012
var _hitstop_until := 0.0
var _slow_until := 0.0
var _zoom := 0.0
var _zoom_peak := 0.0   # v25: yakınlaşma itişinin hedefi (kamera 2-3 karede yumuşakça yaklaşır, sonra söner)
var _kick_target := Vector2.ZERO   # v25: kamera itişinin hedefi (kamera tek karede sıçramaz)
## ------------------------------------------------------------------ v25 akıcı vuruş duraklaması
## Geri bildirim: "kritikte bir anlık donma oyun takılıyormuş gibi; daha akıcı olsun." Ölçünce sebepler: (1) duraklama
## zaman ölçeğini tek karede 1 → 0,05'e indirip süre bitince tek karede 1'e çıkarıyordu (sert durma + sert kalkış:
## "takıldı"); (2) aynı karede ya da art arda gelen duraklama / ağır çekimler (vuruş + kritik + öldürüş) üst üste biniyor,
## ölçek 0,05 → 0,3 → 1 basamaklarıyla zıplıyordu; (3) kamera itişi ve yakınlaşma tek karede sıçrıyordu.
## Şimdi her duraklama / ağır çekim bir "dip" eğrisi: anında dibe iner (vuruş sert okunur), dipte kısa durur, sonra
## yumuşak (smoothstep) bir eğriyle 1'e döner; etkin diplerin her an en yavaşı geçerli (biri ötekini yeniden başlatmaz).
## Art arda gelen duraklamalar sığlaşır; 1 sn'lik pencerede toplam "kayıp zaman" sınırlı. Kamera ve arayüz gerçek
## zamanda (process_mode ALWAYS, rd = delta / ölçek) akmaya devam eder.
const HS := {
	"floor": 0.1,          # duraklamanın dibi (eski: 0,05 sert donma)
	"hold": 0.5,           # süresinin bu oranı dipte geçer
	"release": 0.9,        # dipten 1'e yumuşak dönüş: süre × release + release_min
	"release_min": 0.03,
	"budget": 0.2,         # 1 sn'lik pencerede duraklama + kısa ağır çekimin en çok "kayıp zamanı" (sn)
	"chain_t": 0.25,       # bu süre içinde gelen yeni duraklama sığlaşır (çok vuruşlu savuruş, öldürüş + kritik)
	"chain_floor": 0.12,   # ardışık her duraklamada dip bu kadar yükselir (en çok 3 adım)
	"slow_hold": 0.55,     # ağır çekimde dipte geçen oran; ardından yumuşak dönüş: süre × slow_release (en çok 0,2 sn)
	"slow_release": 0.45,
	"slow_budget_max": 0.25,   # bundan kısa ağır çekimler (dövüş) kayıp zaman sınırına sayılır; uzunlar (boss ölümü) sayılmaz
}
var _dips: Array = []    # [dip ölçeği, başlangıç, dip bitişi, bitiş] (Game.clock, sn)
var _lost: Array = []    # [an, kayıp zaman] (kayıp zaman sınırı için)
var _hs_last := -9.0
var _hs_n := 0
var hs_log: Array = []   # test (dovus_testi --takilma): [an, ölçek] kare kaydı
var hs_log_on := false
var hs_eski := false     # test (dovus_testi --takilma_eski): v24'ün sert duraklaması (karşılaştırma için)
## Kameranın taban yakınlığı (Level ayarlar): v1 1,0 (960x540 dünya birimi), stil v2 mürekkep ortamı 1,5 (640x360;
## karakterler ekranda 1,5 kat büyük). zoom_punch bunun üstüne çarpılır.
var base_zoom := 1.0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_movie = Engine.get_write_movie_path() != ""
	_movie_clock = Time.get_ticks_msec() / 1000.0
	_setup_input()
	load_meta()
	_on_yukle_baslat()


# ------------------------------------------------------------------ v38 efekt dokusu ön yüklemesi
## İlk kullanımda yüklenen efekt / arayüz dokuları (ör. hush_lock 40 ms, smoke_puff 25 ms) dövüşün ortasında kare
## takılmasıydı: oyun açılırken arka plan iş parçacığında yüklenir ve başvurusu tutulur (ResourceLoader önbelleğinde
## kalır; Data.tex / InkDraw / AnimFX'in load() çağrısı anında döner). HD paketindeki dokular atlanır (Data.tex onları
## paketten alır).
const ON_YUKLE_DIZIN := ["res://assets/fx/anim/", "res://assets/fx/ink/", "res://assets/fx/ink_p/", "res://assets/ui/ink/"]
var _on_bekleyen: Array = []
var _on_yuklu: Array = []


func _on_yukle_baslat() -> void:
	for d in ON_YUKLE_DIZIN:
		if not DirAccess.dir_exists_absolute(d):
			continue
		for f in ResourceLoader.list_directory(d):
			var p := String(d) + String(f)
			if not p.ends_with(".png") or Data.pack_has(p):
				continue
			if ResourceLoader.load_threaded_request(p) == OK:
				_on_bekleyen.append(p)


func _on_yukle_tick() -> void:
	## Her karede yalnızca biten isteklerin sonucu alınır (bekleme yok)
	while not _on_bekleyen.is_empty():
		var p: String = _on_bekleyen[0]
		var st := ResourceLoader.load_threaded_get_status(p)
		if st == ResourceLoader.THREAD_LOAD_IN_PROGRESS:
			return
		_on_bekleyen.pop_front()
		if st == ResourceLoader.THREAD_LOAD_LOADED:
			_on_yuklu.append(ResourceLoader.load_threaded_get(p))


## Zaman kaynağı: gerçek zaman; --write-movie çekiminde kare saati (çekim gerçek zamandan yavaş işlenir; duraklama ve
## ağır çekim kayıtta oyundaki süresiyle görünsün diye ölçeksiz kare süreleri toplanır).
var _movie := false
var _movie_clock := 0.0


func clock() -> float:
	return _movie_clock if _movie else Time.get_ticks_msec() / 1000.0


func _process(delta: float) -> void:
	if Prof.on:
		var t0 := Time.get_ticks_usec()
		_process_ic(delta)
		Prof.ekle(&"game", t0)
		return
	_process_ic(delta)


func _process_ic(delta: float) -> void:
	if not _on_bekleyen.is_empty():
		_on_yukle_tick()
	if _movie:
		_movie_clock += delta / maxf(0.001, Engine.time_scale)
	var now := clock()
	var ts := _dip_now(now)
	if get_tree().paused:
		ts = 1.0
	Engine.time_scale = ts
	if hs_log_on:
		hs_log.append([now, ts])
	var rd := delta / maxf(0.05, ts)
	if camera:
		# v25: yakınlaşma ve itiş hedefe 2-3 karede yumuşakça varır, hedef üstel söner (tek karede sıçrama yok)
		_zoom_peak = lerpf(_zoom_peak, 0.0, clampf(rd * 7.0, 0.0, 1.0))
		_zoom = lerpf(_zoom, _zoom_peak, clampf(rd * 26.0, 0.0, 1.0))
		camera.zoom = Vector2.ONE * base_zoom * (1.0 + _zoom)
		_kick_target = _kick_target.lerp(Vector2.ZERO, clampf(rd * 12.0, 0.0, 1.0))
		kick_off = kick_off.lerp(_kick_target, clampf(rd * 30.0, 0.0, 1.0))
		var off := kick_off
		# eski doğrusal sarsıntı (küçük olaylar) + travma sarsıntısı (büyük olaylar, üstel sönüm, yönlü)
		if shake_amount > 0.05:
			off += Vector2(randf_range(-1, 1), randf_range(-1, 1)) * shake_amount
			shake_amount = move_toward(shake_amount, 0.0, rd * 30.0)
		var rot := 0.0
		if trauma > 0.01:
			_noise_t += rd * 38.0
			var k := trauma * trauma
			var nx := sin(_noise_t * 1.7) * 0.6 + sin(_noise_t * 4.3 + 1.3) * 0.4
			var ny := sin(_noise_t * 2.1 + 0.7) * 0.6 + sin(_noise_t * 5.1 + 2.9) * 0.4
			var sh := Vector2(nx * SHAKE_MAX.x, ny * SHAKE_MAX.y) * k
			if trauma_dir.length() > 0.01:
				# yönlü: sarsıntı darbe ekseninde 2 kat, dik eksende yarım
				var d := trauma_dir.normalized()
				var along := sh.dot(d)
				var perp := sh - d * along
				sh = d * along * 1.6 + perp * 0.45
			off += sh
			rot = nx * SHAKE_ROT * k
			trauma = maxf(0.0, trauma - rd * 2.6)
			trauma_dir = trauma_dir.lerp(Vector2.ZERO, clampf(rd * 3.0, 0.0, 1.0))
		camera.offset = off
		camera.rotation = rot
		if _rumble_until > 0.0 and now > _rumble_until:
			_rumble_until = 0.0
			for d in Input.get_connected_joypads():
				Input.stop_joy_vibration(d)


func shake(amount: float) -> void:
	shake_amount = maxf(shake_amount, amount * fx_scale)


func shake_dir(amount: float, dir := Vector2.ZERO) -> void:
	## Travma sarsıntısı: amount 0..1 (0,25 hafif, 0,5 ağır vuruş, 0,8 patlama); dir darbe yönü (isteğe bağlı)
	trauma = minf(1.0, trauma + amount * fx_scale)
	if dir.length() > 0.01:
		trauma_dir = (trauma_dir + dir.normalized() * amount).limit_length(1.0)


func rumble(strong := 0.5, weak := 0.3, dur := 0.12) -> void:
	## Oyun kolu titreşimi: güçlü motor (alçak gürleme) / zayıf motor (tiz vızıltı)
	var now := clock()
	for d in Input.get_connected_joypads():
		Input.start_joy_vibration(d, weak, strong, dur)
	_rumble_until = maxf(_rumble_until, now + dur)


func kick(dir: Vector2, amount := 4.0) -> void:
	## Kamera itişi: darbe yönünde kısa bir kayma, hızla geri döner.
	if dir.length() > 0.01:
		_kick_target += dir.normalized() * amount * (0.5 + 0.5 * fx_scale)
		# v17: aynı anda gelen itişler toplanıp kamerayı savurmasın (çok düşmanlı vuruş, patlama + darbe)
		_kick_target = _kick_target.limit_length(KICK_MAX)


func zoom_punch(amount := 0.05) -> void:
	## Kritik / ağır öldürmede kamera bir an yaklaşır (v25: hedef; kamera 2-3 karede yumuşakça yaklaşır)
	_zoom_peak = maxf(_zoom_peak, amount * (0.6 + 0.4 * fx_scale))


func hitstop(duration: float) -> void:
	## Vuruş duraklaması (v25): sert donma yerine dip eğrisi — anında HS.floor'a iner, sürenin HS.hold'u dipte, sonra
	## yumuşakça 1'e döner. Süren bir dibin içindeyse yeniden başlamaz; art arda gelenler sığlaşır; kayıp zaman sınırlı.
	if duration <= 0.0:
		return
	var now := clock()
	if hs_eski:
		_hitstop_until = maxf(_hitstop_until, now + duration)
		return
	_hs_n = _hs_n + 1 if now - _hs_last < float(HS["chain_t"]) else 0
	_hs_last = now
	var fl := minf(0.5, float(HS["floor"]) + float(HS["chain_floor"]) * float(mini(_hs_n, 3)))
	var h := duration * float(HS["hold"])
	var r := duration * float(HS["release"]) + float(HS["release_min"])
	_add_dip(now, fl, h, r, true)


func slowmo(scale_v: float, duration: float) -> void:
	## Ağır çekim (kritik, öldürücü vuruş, savuşturma).
	## v17: üst üste gelen çağrılar birbirini ezmez: her an süresi dolmamış çağrıların en yavaşı geçerli.
	## v25: süre bitince tek karede 1'e zıplamaz; son kısmı yumuşak dönüş (HS.slow_hold / slow_release).
	if duration <= 0.0:
		return
	var now := clock()
	if hs_eski:
		_dips.append([scale_v, now, now + duration, now + duration])
		return
	var h := duration * float(HS["slow_hold"])
	var r := minf(duration * float(HS["slow_release"]), 0.2) + float(HS["release_min"])
	_add_dip(now, clampf(scale_v, 0.02, 1.0), h, r, duration <= float(HS["slow_budget_max"]))


func _add_dip(now: float, fl: float, h: float, r: float, budgeted: bool) -> void:
	_dips = _dips.filter(func(d: Array) -> bool: return float(d[3]) > now)
	# yeniden başlatma yok: süren bir dip bu dibi zaten kapsıyorsa (daha derin ya da eşit ve daha uzun) ekleme
	for d in _dips:
		if float(d[0]) <= fl + 0.001 and float(d[2]) >= now + h - 0.001 and float(d[3]) >= now + h + r - 0.001:
			return
	if budgeted:
		var cur := _dip_now(now)
		_lost = _lost.filter(func(l: Array) -> bool: return now - float(l[0]) < 1.0)
		var used := 0.0
		for l in _lost:
			used += float(l[1])
		# yeni dibin eklediği kayıp zaman (dip + dönüşün ortalaması; şu an zaten yavaşsa yalnızca fazlası)
		var loss := maxf(0.0, cur - fl) * (h + 0.5 * r)
		var room := maxf(0.0, float(HS["budget"]) - used)
		if loss > room:
			if room < 0.004:
				return
			var k := room / loss
			h *= k
			r = maxf(float(HS["release_min"]), r * k)
			loss = room
		_lost.append([now, loss])
	_dips.append([fl, now, now + h, now + h + r])
	_hitstop_until = maxf(_hitstop_until, now + h)
	_slow_until = maxf(_slow_until, now + h + r)


func _dip_now(now: float) -> float:
	## Etkin diplerin şu anki ölçeklerinin en küçüğü: dipte sabit, dönüşte smoothstep (türevi iki uçta 0: kalkış ve
	## varış "kesik" okunmaz)
	var sc := 1.0
	if hs_eski and now < _hitstop_until:
		return 0.05
	for d in _dips:
		var t0 := float(d[1])
		var te := float(d[3])
		if now < t0 or now >= te:
			continue
		var fl := float(d[0])
		var th := float(d[2])
		var v := fl
		if now > th:
			var u := clampf((now - th) / maxf(0.001, te - th), 0.0, 1.0)
			v = lerpf(fl, 1.0, u * u * (3.0 - 2.0 * u))
		sc = minf(sc, v)
	return sc


func time_k() -> float:
	## Test / görsel: şu anki duraklama ölçeği (1 = normal)
	return _dip_now(clock())


func new_run() -> void:
	var start_melee := ItemGen.roll("alp_kilici", 0, "demir", 0)
	var start_bow := ItemGen.roll("turk_yayi", 0, "demir", 0)
	var start_bomb := ItemGen.roll("kara_barut", 0, "demir", 0)
	if umay_level("silah") > 0:
		start_melee = ItemGen.roll("alp_kilici", 1, "tunc", 1)
	var mhp := 100.0 * (1.0 + 0.1 * umay_level("can"))
	# v22: Kut Mührü (koşu başında seçili zorluk kademesi; Zorluk.gd) şişe sayısını azaltabilir, en az 1 kalır
	var muhur := Zorluk.muhur_secili()
	run = {"muhur": muhur}
	var fl := maxi(1, 2 + umay_level("sise") + Zorluk.sise_ek())
	run = {
		"muhur": muhur,
		"hp": mhp, "max_hp": mhp, "gold": 60 * umay_level("altin"), "kut": 0, "flasks": fl, "max_flasks": fl,
		"ongun": {"kurt": 0, "kartal": 0, "ayi": 0},
		"slots": {"melee": start_melee, "second": start_bow, "g1": start_bomb, "g2": {}},
		"kills": 0, "time": 0.0, "tier": 0, "depth": 1, "scrolls": 0, "lutuf": [], "boss_done": [],
		"adlar": [], "destan": [], "dstat": {},
	}
	Kupler.baslangic(run, umay_level("silah") > 0)   # v44: Ata Kurganı'nda seçilen başlangıç silahı ve küp eşikleri


func umay_level(id: String) -> int:
	return int(meta.get("umay", {}).get(id, 0))


func umay_cost(id: String) -> int:
	## -1: en üst seviye
	var lv := umay_level(id)
	var costs: Array = UMAY[id][2]
	return int(costs[lv]) if lv < costs.size() else -1


func umay_buy(id: String) -> bool:
	var c := umay_cost(id)
	if c < 0 or int(meta.get("kut_bank", 0)) < c:
		return false
	meta["kut_bank"] = int(meta["kut_bank"]) - c
	var u: Dictionary = meta.get("umay", {})
	u[id] = umay_level(id) + 1
	meta["umay"] = u
	save_meta()
	return true


func lose_run_kut() -> int:
	## Ölüm: taşınan Kut yitirilir; Ruh Düğümü bir kısmını Umay'a ulaştırır. Dönen: kurtarılan miktar.
	if run.is_empty():
		return 0
	var keep: float = [0.0, 0.3, 0.6][clampi(umay_level("kut_koruma"), 0, 2)]
	var saved := int(floor(int(run.get("kut", 0)) * keep))
	meta["kut_bank"] = int(meta.get("kut_bank", 0)) + saved
	run["kut_lost"] = int(run.get("kut", 0)) - saved
	run["kut"] = 0
	save_meta()
	return saved


func biome_for_depth(depth: int) -> Dictionary:
	## Derinlik aralıklarına göre biyom (world.json "depths"); eşleşme yoksa en derin biyom
	var last: Dictionary = {}
	for b in Data.world["biomes"]:
		if not b.get("impl", false):
			continue
		var r: Array = b.get("depths", [0, 0])
		if depth >= int(r[0]) and depth <= int(r[1]):
			return b
		if int(r[1]) >= 99:
			last = b
	return last if not last.is_empty() else Data.world["biomes"][0]


func next_depth() -> void:
	## Kut Kapısı'ndan geçiş (v32: konağa varış): eşyalar, ongunlar ve can korunur; can +%15 (Zorluk.derinlik_sifa),
	## şişeler dolar; düşmanlar sertleşir.
	run["depth"] = int(run.get("depth", 1)) + 1
	run["tier"] = Zorluk.kademe(int(run["depth"]))   # v22: kademe = derinlik - 1 (en çok 8; Zorluk)
	run["flasks"] = int(run["max_flasks"])
	run["hp"] = minf(float(run["max_hp"]), float(run["hp"]) + float(run["max_hp"]) * Zorluk.derinlik_sifa())


func has_lutuf(id: String) -> bool:
	return not run.is_empty() and id in run.get("lutuf", [])


func grant_lutuf(id: String) -> void:
	var l: Array = run.get("lutuf", [])
	if id in l:
		return
	l.append(id)
	run["lutuf"] = l
	if id == "erlik":
		run["max_hp"] = float(run["max_hp"]) * 0.8
		run["hp"] = minf(float(run["hp"]), float(run["max_hp"]))


func ongun_mult(ongun: String) -> float:
	## v23 tomar ekonomisi: stat seviyesi (o renkte okunan tomar) -> hasar çarpanı, azalan getiriyle (Zorluk.tomar_k)
	if run.is_empty():
		return 1.0
	return Zorluk.tomar_k(int(run["ongun"].get(ongun, 0)))


func ongun_mult_lv(ongun: String, add := 0) -> float:
	## Önizleme: stat add tomar daha okunursa çarpan (tomar seçim ekranı)
	var lv := 0 if run.is_empty() else int(run["ongun"].get(ongun, 0))
	return Zorluk.tomar_k(lv + add)


func item_onguns(it: Dictionary) -> Array:
	## Eşyanın ongunları: bir ya da iki renk (Dead Cells'in çift renkli eşyaları).
	var out: Array = []
	var o: Variant = it.get("ongun", "")
	if o is Array:
		out = (o as Array).duplicate()
	elif String(o) != "":
		out.append(String(o))
	var o2 := String(it.get("ongun2", ""))
	if o2 != "" and not (o2 in out):
		out.append(o2)
	return out


func item_best_ongun(it: Dictionary) -> String:
	## Çift renkli eşya hangi ongun daha yüksekse ona göre güçlenir; eşitlikte ilk renk.
	var best := ""
	var best_lv := -1
	for o in item_onguns(it):
		var lv := int(run.get("ongun", {}).get(o, 0)) if not run.is_empty() else 0
		if lv > best_lv:
			best_lv = lv
			best = o
	return best if best != "" else "kurt"


func item_mult(it: Dictionary) -> float:
	return ongun_mult(item_best_ongun(it))


func bank_run_kut() -> void:
	## Koşu bitince (ölüm ya da kapı) toplanan Kut, Umay'ın bankasına eklenir.
	if run.is_empty():
		return
	meta["kut_bank"] = int(meta.get("kut_bank", 0)) + int(run.get("kut", 0))
	run["kut"] = 0
	save_meta()


func is_unlocked(id: String) -> bool:
	## Temel eşyalar baştan açık; yalnızca gelişmiş sürümler (upgrade_of) parşömenle açılır.
	if id in BASE_UNLOCKED or id in meta.get("unlocked", []):
		return true
	var base := Data.find_item(id)
	return not base.is_empty() and not base.has("upgrade_of")


func unlock_cost(id: String) -> int:
	var base := Data.find_item(id)
	var c := 12
	if base.get("cat", "") == "weapons":
		c = 14 + int(float(base.get("dmg", 8)) * 0.4)
	elif base.get("cat", "") == "gadgets":
		c = 12
	else:
		c = 10
	return c


func learned(id: String) -> int:
	## Öğretici: bu ipucu kaç kez gösterildi (kalıcı)
	return int(meta.get("ogrendi", {}).get(id, 0))


func learn(id: String) -> void:
	var o: Dictionary = meta.get("ogrendi", {})
	o[id] = learned(id) + 1
	meta["ogrendi"] = o
	save_meta()


func add_blueprint(id: String) -> bool:
	## Parşömen toplandı; henüz açılmadı. true: yeni.
	var bps: Array = meta.get("blueprints", [])
	if id in bps or is_unlocked(id):
		return false
	bps.append(id)
	meta["blueprints"] = bps
	save_meta()
	return true


func unlock(id: String) -> bool:
	var cost := unlock_cost(id)
	if int(meta.get("kut_bank", 0)) < cost:
		return false
	meta["kut_bank"] = int(meta["kut_bank"]) - cost
	var ul: Array = meta.get("unlocked", [])
	ul.append(id)
	meta["unlocked"] = ul
	var bps: Array = meta.get("blueprints", [])
	bps.erase(id)
	meta["blueprints"] = bps
	save_meta()
	return true


func load_meta() -> void:
	meta = {"runs": 0, "wins": 0, "kut_bank": 0, "unlocked": [], "blueprints": [], "best_depth": 1}
	if FileAccess.file_exists(SAVE_PATH):
		var f := FileAccess.open(SAVE_PATH, FileAccess.READ)
		var d: Variant = JSON.parse_string(f.get_as_text())
		if d is Dictionary:
			meta.merge(d, true)
	Hikaye.meta_hazirla()   # v42: hikâye alanları (gun_parca, gorumler, giris_izlendi, son_izlendi) varsayılan / göç


func save_meta() -> void:
	var f := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(meta))


# ------------------------------------------------------------------ giriş haritası
func _bind(action: String, keys: Array, mouse := -1, buttons: Array = [], axes: Array = []) -> void:
	if not InputMap.has_action(action):
		InputMap.add_action(action, 0.3)
	for k in keys:
		var e := InputEventKey.new()
		e.physical_keycode = k
		InputMap.action_add_event(action, e)
	if mouse >= 0:
		var m := InputEventMouseButton.new()
		m.button_index = mouse
		InputMap.action_add_event(action, m)
	for b in buttons:
		var j := InputEventJoypadButton.new()
		j.button_index = b
		InputMap.action_add_event(action, j)
	for ax in axes:
		var a := InputEventJoypadMotion.new()
		a.axis = ax[0]
		a.axis_value = ax[1]
		InputMap.action_add_event(action, a)


func _setup_input() -> void:
	_bind("sol", [KEY_A, KEY_LEFT], -1, [JOY_BUTTON_DPAD_LEFT], [[JOY_AXIS_LEFT_X, -1.0]])
	_bind("sag", [KEY_D, KEY_RIGHT], -1, [JOY_BUTTON_DPAD_RIGHT], [[JOY_AXIS_LEFT_X, 1.0]])
	_bind("yukari", [KEY_W, KEY_UP], -1, [JOY_BUTTON_DPAD_UP], [[JOY_AXIS_LEFT_Y, -1.0]])
	_bind("asagi", [KEY_S, KEY_DOWN], -1, [JOY_BUTTON_DPAD_DOWN], [[JOY_AXIS_LEFT_Y, 1.0]])
	_bind("zipla", [KEY_SPACE], -1, [JOY_BUTTON_A])
	_bind("saldiri1", [KEY_J], MOUSE_BUTTON_LEFT, [JOY_BUTTON_X])
	_bind("saldiri2", [KEY_K], MOUSE_BUTTON_RIGHT, [JOY_BUTTON_Y])
	_bind("yuvarlan", [KEY_L, KEY_SHIFT], -1, [JOY_BUTTON_B])
	# v23: yan teçhizat sol elin altında: E / R (eskiden U / I; etkileşim W / ↑ dokunuşuna geçti)
	_bind("techizat1", [KEY_E], -1, [JOY_BUTTON_LEFT_SHOULDER])
	_bind("techizat2", [KEY_R], -1, [JOY_BUTTON_RIGHT_SHOULDER])
	_bind("kut", [KEY_F], -1, [JOY_BUTTON_RIGHT_STICK])
	_bind("sise", [KEY_Q], -1, [JOY_BUTTON_LEFT_STICK])
	# v23: etkileşim W / ↑ (oyun kolunda yön yukarı ya da Back); kısa dokunuşun bırakılışında tetiklenir, ↑+J göğe
	# savurmayla çakışmaz (Level._etkiles_tap). Menülerde onay Boşluk / Enter (oyun kolunda A).
	_bind("etkiles", [KEY_W, KEY_UP], -1, [JOY_BUTTON_BACK, JOY_BUTTON_DPAD_UP])
	_bind("don", [KEY_G], -1, [], [[JOY_AXIS_TRIGGER_RIGHT, 1.0]])
	# v27 savaş sanatı: T (v25'te Üç Âlem'den boşaldı); oyun kolunda LT (sol tetik)
	_bind("sanat", [KEY_T], -1, [], [[JOY_AXIS_TRIGGER_LEFT, 1.0]])
	_bind("duraklat", [KEY_ESCAPE, KEY_P], -1, [JOY_BUTTON_START])
	_bind("ayarlar", [KEY_TAB, KEY_O], -1, [JOY_BUTTON_GUIDE])
	# v32 harita: M (oyun kolunda sağ çubuk basışı Kut'ta; harita için D-pad aşağı uzun basış yok: yalnızca klavye)
	_bind("harita", [KEY_M])
