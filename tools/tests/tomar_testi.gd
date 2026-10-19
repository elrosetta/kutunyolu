extends Node
## v23 tomar ekonomisi testi: godot --headless --path . --quit-after 99999 -- --tomar --boss
##   SNH:  silah kuşanılır, Kut Tomarları oyunun kendi yolundan okunur (yere tomar düşer, Main._on_scroll /
##         _apply_scroll), kartın gösterdiği SnH (ItemGen.dps_oyuncu; HUD aynı sayıyı çizer) durağan bir kuklaya
##         sürekli zincirle vurularak ölçülen SnH ile karşılaştırılır (oyun zamanı; kombo sayacı, usul ve Kızışma
##         her karede sıfırlanır, çünkü kart bunları saymaz). "koşul" silahları (kendi koşul kritiğini kendisi
##         doğuran) yalnızca bilgi için ölçülür.
##   KRIT: her yakın silah kuklaya --krit_sn sn zincir vurur; isabetlerin yüzde kaçı kritik (şans / silah koşulu /
##         kesin). -- --tomar --krit yalnızca bunu koşar; --snh yalnızca SnH'yi.
## Çıktı: "[tomar] ..." satırları, sonda "[tomar] OZET ..." ve "[tomar] SONUC GECTI|KALDI".

var main: Node
var lv: Node
var pl: Player
var spot := Vector2.ZERO
var dummy: Node = null
var _game_t := 0.0
var _hold := false
var _iz := OS.get_cmdline_user_args().has("--snh_iz")
var _snh_kipi := false
var _dx := 26.0   # kuklanın oyuncuya uzaklığı (v25 uzak silah ölçümünde 110 px)
var _uzak_ok := true   # v27 uzak silahlarında kart ↔ ölçülen sınır denetimi

## v25 uzak silah SnH (-- --tomar --uzak): [silah, basış kipi]. Kipler: "gec" yay dolar, pencereden sonra bırakılır
## (kartın saydığı tam güç, kritiksiz); "tam" her ok tam bırakış (beceri tavanı, kesin kritik); "tut" basılı tut
## (Akıncı seri atış); "dokun" her 2 karede bir basış (fırlatma / büyü). Kartal tomarıyla ölçülür, yakın silahlar
## (Kurt tomarı) aynı tomar sayısında aynı çarpanı alır.
const UZAK_SILAHLAR := [["turk_yayi", "gec"], ["turk_yayi", "tam"], ["akinci_yayi", "tut"], ["saganak_yayi", "gec"],
	["saganak_yayi", "tam"], ["od_oklari", "gec"], ["tufan_yayi", "gec"], ["cirit", "dokun"], ["coban_sapani", "dokun"],
	["kartal_tuyleri", "dokun"], ["mancinik_tasi", "dokun"], ["kam_kopuzu", "dokun"], ["yel_borusu", "dokun"],
	["gok_asasi", "dokun"],
	# v27: Tatar Yayı "kur_yok" (yalnızca hazırken bas: kartın saydığı), "kur_tam" (her kurmada altın yerde bas: beceri
	# tavanı); Kam Küzgüsü basılı tut; Tengri Bağı dokun (düğüm / çekiş sırayla)
	["tatar_yayi", "kur_yok"], ["tatar_yayi", "kur_tam"], ["kam_kuzgusu", "tut"], ["tengri_bagi", "dokun"]]
## v27 uzak silahlarında kart ↔ ölçülen sınırı (beceri tavanı kipleri hariç)
const UZAK27 := ["tatar_yayi/kur_yok", "kam_kuzgusu/tut", "tengri_bagi/dokun"]
const UZAK_TOMAR := [0, 7]

## SnH karşılaştırması: [silah, koşul kritiği kuklada kendiliğinden doğar mı]
## "evet": kuklada betikli basışla ölçüm kartı temsil etmez (bilgi için): kargı hücum, yatağan ivme ve gürz sersemletme
## koşul kritiğini kendisi doğurur; yatağan geri sıçrayışı ve yıldırım kılıcı atılışı zinciri kukladan uzaklaştırıp
## kırar; tırpanın çarkı basılı tuttukça uzar (2 karede bir basış "basılı" sayılır)
const SNH_SILAHLAR := [["alp_kilici", false], ["ikiz_bicak", false], ["ulu_kilic", false], ["bozgun_kilici", false],
	["kargi", true], ["yatagan", true], ["gurz", true], ["yildirim_kilici", true], ["erlik_tirpani", true],
	["gun_ay_ikizi", false], ["kistin", false], ["albasti_hanceri", false], ["cevgen", false]]
const TOMAR_ADIM := [0, 3, 7]   # her ölçümden önce toplam okunmuş Kurt tomarı
const SINIR := 0.07   # gösterilen / ölçülen SnH farkı sınırı (kare yuvarlaması, kuklanın itilmesi ±%5 oynatır)
const KRIT_SILAHLAR := ["ikiz_bicak", "bori_hanceri", "kurt_pencesi", "ay_palasi", "yatagan", "ruzgar_kilici", "alp_kilici", "pala",
	"ruh_kilici", "yilan_kilici", "ayaz_kilici", "yildirim_kilici", "kargi", "tulpar_mizragi", "kement", "od_kamcisi", "teber",
	"erlik_tirpani", "kayin_asasi", "gurz", "civili_topuz", "savas_baltasi", "ikiz_balta", "ulu_kilic", "bozgun_kilici", "dag_cekici",
	"kor_cekici"]
const ACTS := ["saldiri1", "saldiri2", "zipla", "yuvarlan", "sag", "sol", "yukari", "asagi", "techizat1", "techizat2", "sise", "kut"]


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	process_physics_priority = -100   # oyuncudan önce: sayaç sıfırlama ve kukla konumu
	_run.call_deferred()


func _p(s: String) -> void:
	print("[tomar] ", s)


func _arg(name: String, def: String) -> String:
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with(name + "="):
			return String(a).trim_prefix(name + "=")
	return def


func _physics_process(delta: float) -> void:
	if pl == null:
		return
	_game_t += delta
	Game.run["hp"] = float(Game.run["max_hp"])
	# kartın saymadığı geçici çarpanlar: kombo sayacı, usul, Kızışma
	pl.combo_n = 0
	pl.usul_buff_t = 0.0
	pl.kz_n = 0
	pl._yk_early = true   # Kut Yankısı da kartta sayılmaz: yankı penceresi hiç açılmasın
	if dummy and is_instance_valid(dummy):
		dummy.hp = 1.0e9
		dummy.max_hp = 1.0e9
		dummy.cd = 99.0   # saldırmasın (yapay zekâ ve durum süreleri işler: sersemleme, kanama, yanma söner)
		dummy.global_position = Vector2(pl.global_position.x + _dx * pl.facing, spot.y)
		dummy.velocity = Vector2.ZERO
		if _snh_kipi:
			# SnH karşılaştırması: kartın saymadığı düşmana bağlı çarpanlar (duruş kırılması x1,25, nazar, zırh kırığı)
			dummy.broken_t = 0.0
			dummy.cursed_t = 0.0
			dummy.armor_break = 0
	if not _hold and pl.atk.is_empty():
		pl.facing = 1


func _f(n := 1) -> void:
	for i in n:
		await get_tree().physics_frame


func _release_all() -> void:
	for a in ACTS:
		Input.action_release(a)


func _find_spot() -> Vector2:
	if "boss" in lv and lv.boss != null and is_instance_valid(lv.boss):
		lv.boss.remove_from_group("dusman")
		lv.boss.queue_free()
		lv.boss = null
		return Vector2(33 * Level.TS + 12, lv.surface_y(33) * Level.TS - 1)
	return Vector2(40 * Level.TS + 12, lv.surface_y(40) * Level.TS - 1)


func _clear() -> void:
	for e in get_tree().get_nodes_in_group("dusman"):
		e.remove_from_group("dusman")
		e.queue_free()
	dummy = null


func _equip(id: String) -> Dictionary:
	var it := ItemGen.roll(id, 0, "demir", 0, "")
	it["affixes"] = []
	it["dmg"] = ItemGen.dmg_for(id, 0, "demir", 0)
	# SnH kipinde şans kritiği 0: 10 sn'lik ölçümde 1-2 rastgele kritik farkı ±%5 oynatıyordu (kartın kritik terimi
	# 1 + şans x (çarpan - 1) basit bir beklenen değer; KRIT kipinde silahın kendi şansı kullanılır)
	it["crit"] = 0.0 if _snh_kipi else float(Data.find_item(id)["crit"])
	it["aps"] = float(Data.find_item(id)["aps"])
	if it.has("mech_v"):
		var r: Array = Data.find_item(id)["mech"]["range"]
		it["mech_v"] = (float(r[0]) + float(r[1])) / 2.0
	Game.run["slots"]["melee"] = it
	Game.run["slots"]["second"] = {}
	Game.run["slots"]["g1"] = {}
	Game.run["slots"]["g2"] = {}
	pl.on_equip()
	return it


func _spawn_dummy() -> void:
	_clear()
	await _f(2)
	dummy = lv.spawn_enemy("kara_boru", spot + Vector2(26, 0))
	dummy.facing = -1
	dummy.aggro = false
	await _f(2)


func _shown(it: Dictionary) -> float:
	if ItemGen.has_method("dps_oyuncu"):
		return float(ItemGen.dps_oyuncu(it))
	return ItemGen.dps(it) * Game.item_mult(it)


func _read_scrolls(n: int) -> void:
	## Oyunun kendi yolu: yere tomar düşer, oyuncu "okur" (Main._on_scroll -> _apply_scroll(0) = Kurt)
	for i in n:
		lv.drop_scroll(pl.global_position + Vector2(-20, 0))
		await _f(1)
		var p: Node = lv.pickups[lv.pickups.size() - 1]
		main._on_scroll(p)
		main._apply_scroll(0)
		await _f(1)


func _hit_loop(secs: float) -> Array:
	## Kuklaya sürekli zincir: her 2 karede bir saldırı basışı (isabetten önce basış Kut Yankısı'nı bozar).
	## Dönen: [oyun süresi, verilen hasar, yankılı isabet]
	pl.global_position = spot
	pl.velocity = Vector2.ZERO
	pl.facing = 1
	await _f(6)
	var hp0 := float(dummy.hp)
	var t0 := _game_t
	var yk := 0
	var dealt := 0.0
	var fr := 0
	var n_hit := 0
	var n_tur := 0
	var last_atk: Dictionary = {}
	while _game_t - t0 < secs:
		var before := float(dummy.hp)
		if fr % 2 == 0:
			Input.action_press("saldiri1")
		else:
			Input.action_release("saldiri1")
		await _f(1)
		fr += 1
		if not is_instance_valid(dummy):
			break
		var dd := maxf(0.0, before - float(dummy.hp))
		dealt += dd
		if dd > 0.0:
			n_hit += 1
		if not pl.atk.is_empty() and not is_same(pl.atk, last_atk) and int(pl.atk.get("step", -1)) == 0:
			n_tur += 1
		last_atk = pl.atk
		if _iz and dd > 0.0:
			_p("IZ | kare %d | t %.2f | adım %s | %s | hasar %.1f | kritik toplam %d" % [fr, _game_t - t0, str(pl.atk.get("step", "-")), String(pl.atk.get("c", {}).get("s", "-")), dd, int(Player.krit_say["sans"]) + int(Player.krit_say["kosul"]) + int(Player.krit_say["kesin"])])
		if int(pl.atk.get("yanki", 0)) > 0:
			yk += 1
		# kukla her karede 1e9'a döner; oyuncu kayarsa sahneye geri
		if absf(pl.global_position.x - spot.x) > 140.0 and pl.atk.is_empty():
			pl.global_position = spot
	Input.action_release("saldiri1")
	var _unused := hp0
	await _f(30)
	return [_game_t - t0, dealt, yk, n_hit, n_tur]


func _equip_uzak(id: String) -> Dictionary:
	var it := ItemGen.roll(id, 0, "demir", 0, "")
	it["affixes"] = []
	it["dmg"] = ItemGen.dmg_for(id, 0, "demir", 0)
	it["crit"] = 0.0
	it["aps"] = float(Data.find_item(id)["aps"])
	if it.has("mech_v"):
		var r: Array = Data.find_item(id)["mech"]["range"]
		var mv := (float(r[0]) + float(r[1])) / 2.0
		it["mech_v"] = roundf(mv) if bool(Data.find_item(id)["mech"].get("int", false)) else mv
	Game.run["slots"]["melee"] = {}
	Game.run["slots"]["second"] = it
	Game.run["slots"]["g1"] = {}
	Game.run["slots"]["g2"] = {}
	pl.on_equip()
	return it


func _uzak_loop(secs: float, kip: String) -> Array:
	## Uzak silah: kukla _dx px önde; basış kipine göre sürekli atış. Dönen: [oyun süresi, hasar, atış (yay)]
	pl.global_position = spot
	pl.velocity = Vector2.ZERO
	pl.facing = 1
	for k in pl.cd.keys():
		pl.cd[k] = 0.0
	if pl.okc:
		pl.okc.hazir = 0
		if "ammo" in pl.okc:
			pl.okc.call("ammo_fill")
	await _f(6)
	var t0 := _game_t
	var dealt := 0.0
	var fr := 0
	var down := false
	var f0 := int(pl.okc.stats["fire"]) if pl.okc else 0
	var it: Dictionary = Game.run["slots"]["second"]
	var pr: Dictionary = Okculuk.prof(it) if it.get("kind", "") == "bow" else {}
	while _game_t - t0 < secs:
		var before := float(dummy.hp)
		var want := false
		match kip:
			"dokun":
				want = fr % 2 == 0
			"tut":
				want = true
			"tam":
				if pl.aim_t < 0.0:
					# bekleme bitene dek bırakılı (bekleme sırasındaki basış saklanır ve bırakılınca en kısa gerilmede atar)
					want = pl.cd[pl.sec_slot] <= 0.0
				else:
					want = not pl.okc.in_perfect()
			"kur_yok":
				want = pl.cd[pl.sec_slot] <= 0.0
			"kur_tam":
				var q27 := 1.0 - float(pl.cd[pl.sec_slot]) / maxf(0.01, float(pl.cd_max[pl.sec_slot]))
				want = (pl.cd[pl.sec_slot] <= 0.0 and fr % 2 == 0) or (q27 >= 0.66 and q27 <= 0.72)
			"gec":
				if pl.aim_t < 0.0:
					want = pl.cd[pl.sec_slot] <= 0.0
				else:
					want = pl.aim_t < float(pr["draw"]) + float(pr["perfect"]) + 0.017
		if want and not down:
			Input.action_press("saldiri2")
		elif not want and down:
			Input.action_release("saldiri2")
		down = want
		await _f(1)
		fr += 1
		if not is_instance_valid(dummy):
			break
		dealt += maxf(0.0, before - float(dummy.hp))
		pl.global_position.x = spot.x
	Input.action_release("saldiri2")
	await _f(30)
	return [_game_t - t0, dealt, (int(pl.okc.stats["fire"]) - f0) if pl.okc else 0]


func _uzak() -> void:
	_p("UZAK | silah | kip | Kartal tomarı | gösterilen SnH | ölçülen SnH | fark | atış/sn | süre")
	var secs := float(_arg("--snh_sn", "14"))
	var only_w := _arg("--snh_silah", "")
	_snh_kipi = true
	_dx = float(_arg("--uzak_px", "110"))
	for row in UZAK_SILAHLAR:
		var id: String = row[0]
		var kip: String = row[1]
		if only_w != "" and not (id in only_w.split(",")):
			continue
		Game.run["ongun"] = {"kurt": 0, "kartal": 0, "ayi": 0}
		Game.run["max_hp"] = 100.0
		var it := _equip_uzak(id)
		await _spawn_dummy()
		var have := 0
		for target in UZAK_TOMAR:
			for i in target - have:
				Game.run["ongun"]["kartal"] = int(Game.run["ongun"]["kartal"]) + 1
			have = target
			it = Game.run["slots"]["second"]
			var shown := _shown(it)
			var r: Array = await _uzak_loop(secs, kip)
			var meas := float(r[1]) / maxf(0.001, float(r[0]))
			_p("UZAK | %s | %s | %d | %.1f | %.1f | %+.1f%% | %.2f | %.1f" % [id, kip, int(Game.run["ongun"]["kartal"]), shown, meas, (meas / maxf(0.001, shown) - 1.0) * 100.0, float(r[2]) / maxf(0.001, float(r[0])), float(r[0])])
			if ("%s/%s" % [id, kip]) in UZAK27 and absf(meas / maxf(0.001, shown) - 1.0) > SINIR:
				_uzak_ok = false
	_clear()
	_snh_kipi = false
	_dx = 26.0


func _run() -> void:
	await get_tree().process_frame
	await _f(10)
	lv = main.level
	pl = lv.player
	spot = _find_spot()
	pl.global_position = spot
	pl.inv_t = 99999.0
	main.hud.mode = "play"
	get_tree().paused = false
	if OS.get_cmdline_user_args().has("--uzak"):
		await _uzak()
		_release_all()
		_p("SONUC %s" % ("GECTI" if _uzak_ok else "KALDI"))
		get_tree().quit()
		return
	var only_krit := OS.get_cmdline_user_args().has("--krit")
	var only_snh := OS.get_cmdline_user_args().has("--snh")
	var ok := true
	var worst := 0.0
	if not only_krit:
		var tk: Array = []
		for n in range(0, 25, 3):
			var mult := 1.0 + 0.15 * n
			if ClassDB.class_exists("Zorluk") or ResourceLoader.exists("res://scripts/core/Zorluk.gd"):
				var Z: Variant = load("res://scripts/core/Zorluk.gd")
				if Z.has_method("tomar_k"):
					mult = float(Z.tomar_k(n))
			tk.append("%d→×%.2f" % [n, mult])
		_p("tomar çarpanı (stat seviyesi → hasar): " + ", ".join(tk))
		_p("SNH | silah | Kurt tomarı | gösterilen SnH | ölçülen SnH | fark | isabet süresi (sn) | yankı karesi | koşul silahı")
		var secs := float(_arg("--snh_sn", "14"))
		var only_w := _arg("--snh_silah", "")
		_snh_kipi = true
		for row in SNH_SILAHLAR:
			var id: String = row[0]
			if only_w != "" and not (id in only_w.split(",")):
				continue
			var kosul: bool = row[1]
			Game.run["ongun"] = {"kurt": 0, "kartal": 0, "ayi": 0}
			Game.run["max_hp"] = 100.0
			var it := _equip(id)
			await _spawn_dummy()
			var have := 0
			for target in TOMAR_ADIM:
				await _read_scrolls(target - have)
				have = target
				it = Game.run["slots"]["melee"]
				var shown := _shown(it)
				var r: Array = await _hit_loop(secs)
				var meas := float(r[1]) / maxf(0.001, float(r[0]))
				var diff := meas / maxf(0.001, shown) - 1.0
				if not kosul:
					worst = maxf(worst, absf(diff))
					if absf(diff) > SINIR:
						ok = false
				var zs := float(ItemGen.zincir_sure(it)) if ItemGen.has_method("zincir_sure") else 0.0
				var zv := float(ItemGen.zincir_vurus(it)) if ItemGen.has_method("zincir_vurus") else 0.0
				_p("SNH | %s | %d | %.1f | %.1f | %+.1f%% | %.1f | %d | %s | tur: kart %.3f sn %.0f vuruş, ölçülen %.3f sn %.1f vuruş" % [id, int(Game.run["ongun"]["kurt"]), shown, meas, diff * 100.0, float(r[0]), int(r[2]), "evet" if kosul else "hayır", zs, zv, float(r[0]) / maxf(1.0, float(r[4])), float(r[3]) / maxf(1.0, float(r[4]))])
			_p("SNH_CAN | %s | tomar %d | azami can %.0f" % [id, int(Game.run.get("scrolls", 0)), float(Game.run["max_hp"])])
		_clear()
		_snh_kipi = false
	if not only_snh:
		_p("KRIT | silah | isabet | kritik % | şans % | koşul % | kesin %")
		var ksecs := float(_arg("--krit_sn", "10"))
		Game.run["ongun"] = {"kurt": 0, "kartal": 0, "ayi": 0}
		var tot := {"isabet": 0, "sans": 0, "kosul": 0, "kesin": 0}
		var pcts: Array = []
		for id in KRIT_SILAHLAR:
			_equip(id)
			await _spawn_dummy()
			var k0: Dictionary = Player.krit_say.duplicate()
			await _hit_loop(ksecs)
			var dk := {}
			for kk in tot:
				dk[kk] = int(Player.krit_say[kk]) - int(k0[kk])
				tot[kk] = int(tot[kk]) + int(dk[kk])
			var n := maxi(1, int(dk["isabet"]))
			var c := int(dk["sans"]) + int(dk["kosul"]) + int(dk["kesin"])
			pcts.append(100.0 * c / n)
			_p("KRIT | %s | %d | %.1f | %.1f | %.1f | %.1f" % [id, int(dk["isabet"]), 100.0 * c / n, 100.0 * int(dk["sans"]) / n, 100.0 * int(dk["kosul"]) / n, 100.0 * int(dk["kesin"]) / n])
		var n2 := maxi(1, int(tot["isabet"]))
		pcts.sort()
		_p("KRIT_OZET | isabet %d | kritik %%%.1f | şans %%%.1f | koşul %%%.1f | kesin %%%.1f | silah ortancası %%%.1f | en yüksek %%%.1f" % [n2, 100.0 * float(int(tot["sans"]) + int(tot["kosul"]) + int(tot["kesin"])) / n2, 100.0 * int(tot["sans"]) / n2, 100.0 * int(tot["kosul"]) / n2, 100.0 * int(tot["kesin"]) / n2, float(pcts[pcts.size() / 2]), float(pcts[pcts.size() - 1])])
		_clear()
	_release_all()
	if not only_krit:
		_p("OZET snh_en_buyuk_fark=%%%.1f (koşulsuz silahlar, sınır %%%d)" % [worst * 100.0, int(SINIR * 100.0)])
	_p("SONUC %s" % ("GECTI" if ok else "KALDI"))
	get_tree().quit()
