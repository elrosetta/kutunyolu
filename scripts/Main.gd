extends Node
## Giriş noktası: başlık → hikâye → Ulu Kayın yurdu (koşu başı; Umay / Demirci / Ozan / Alp Ata) → kapı → 1. derinlik.
## v32: Kut Kapısı'ndan geçince yurda DÖNÜLMEZ; bir sonraki derinliğin eşiğinde gezgin bir Konak kurulur (Level.build_konak:
## Umay Ocağı Kut'u bankaya alır, Bengisu Usta altınla silah nakışlar, bazen Bezirgân), konağın kapısı derine indirir.
## Boss derinliklerinde: bölüm → boss arenası → konak. Ölünce toplanan Kut (Ruh Düğümü payı) bankaya eklenir, yeni koşu
## yurtta başlar. Tılsım seçimi, Demirci ve Usta ekranları burada yönetilir (ağaç duraklıyken girdi).

var level: Level
var hud: HUD
var ui_layer: CanvasLayer
var auto_test := false
var showcase := false
var lab := false
var _lab_i := 0
var scroll_pickup: Pickup
var slot_pickup: Pickup
var _depth_forced := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	ui_layer = CanvasLayer.new()
	ui_layer.layer = 10
	add_child(ui_layer)
	hud = HUD.new()
	hud.main = self
	ui_layer.add_child(hud)
	add_child(Gorum.new())   # v42: Gün Ana görümleri ve konuşma alt yazıları (oyun durmaz)
	auto_test = OS.get_cmdline_user_args().has("--otomatik")
	showcase = OS.get_cmdline_user_args().has("--sahne") or OS.get_cmdline_user_args().has("--savurus")
	lab = OS.get_cmdline_user_args().has("--savurus")
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--muhur="):
			Zorluk.set_muhur(int(String(arg).trim_prefix("--muhur=")))   # v23 test: kayıtlı mühürden bağımsız ölçüm
		if String(arg).begins_with("--ekran="):
			_ekran = String(arg).trim_prefix("--ekran=")
			auto_test = false
	_test_kipi = _test_bayragi()
	_new_run()
	if OS.get_cmdline_user_args().has("--yurt") and not (level and level.hub):
		_build_hub()  # yurt testi: doğrudan Ulu Kayın'da başla
	if OS.get_cmdline_user_args().has("--konak"):
		# v32 konak / Bengisu Usta testi (tools/tests/konak_testi.gd): kapı → konak → şifa / şişe → hizmetler → derine, boss akışı
		var kt: Node = load("res://tools/tests/konak_testi.gd").new()
		kt.set("main", self)
		add_child(kt)
	if OS.get_cmdline_user_args().has("--otag"):
		# v42 sınav ve otağ testi (tools/tests/otag_testi.gd): mühür kazanma / kaybetme, otağa giriş, ödüller, türler, değer
		var ot: Node = load("res://tools/tests/otag_testi.gd").new()
		ot.set("main", self)
		add_child(ot)
	if OS.get_cmdline_user_args().has("--mekanik"):
		var mt: Node = load("res://tools/tests/mekanik_testi.gd").new()
		mt.set("main", self)
		add_child(mt)
	if OS.get_cmdline_user_args().has("--denge"):
		# v22 denge ölçümü (tools/tests/denge_testi.gd): derinlik başına vuruş sayıları, boss süreleri, silah SnH
		var dg: Node = load("res://tools/tests/denge_testi.gd").new()
		dg.set("main", self)
		add_child(dg)
	if OS.get_cmdline_user_args().has("--tomar"):
		# v23 tomar ekonomisi testi (tools/tests/tomar_testi.gd): tomar okununca gösterilen SnH = ölçülen SnH, kritik oranı
		var tt: Node = load("res://tools/tests/tomar_testi.gd").new()
		tt.set("main", self)
		add_child(tt)
	if OS.get_cmdline_user_args().has("--dovus"):
		# dövüş akıcılığı testi (tools/tests/dovus_testi.gd): betikli girdiyle gecikme / iptal / ara bellek ölçümü
		var dt: Node = load("res://tools/tests/dovus_testi.gd").new()
		dt.set("main", self)
		add_child(dt)
	if OS.get_cmdline_user_args().has("--zeka"):
		# v23 yapay zekâ denetimi (tools/tests/zeka_testi.gd): yaratık / boss başına saldırı sıklığı, kilit payı, hasar
		var zt: Node = load("res://tools/tests/zeka_testi.gd").new()
		zt.set("main", self)
		add_child(zt)
	if OS.get_cmdline_user_args().has("--tuccar"):
		# v24 tüccar testi (tools/tests/tuccar_testi.gd): pazar, satın alma, altın, SnH farkı, yenileme, parşömen armağanı
		var tct: Node = load("res://tools/tests/tuccar_testi.gd").new()
		tct.set("main", self)
		add_child(tct)
	if OS.get_cmdline_user_args().has("--harita"):
		# v25 harita testi (tools/tests/harita_testi.gd): baş boşluğu / ana yol ölçümü, düşman yerleşimi, tehlike, tüccar
		var ht: Node = load("res://tools/tests/harita_testi.gd").new()
		ht.set("main", self)
		add_child(ht)
	if OS.get_cmdline_user_args().has("--isinlan"):
		# v32 ışınlanma testi (tools/tests/isinlan_testi.gd): Kut Taşı keşfi, harita ekranı, kanal, bozulma, zamanlı kapı
		var it: Node = load("res://tools/tests/isinlan_testi.gd").new()
		it.set("main", self)
		add_child(it)
	if OS.get_cmdline_user_args().has("--silah27"):
		# v27 yeni silahlar testi / çekimi (tools/tests/silah27_testi.gd): her silahın mekaniği, kart, görüntüler
		var s27: Node = load("res://tools/tests/silah27_testi.gd").new()
		s27.set("main", self)
		add_child(s27)
	if OS.get_cmdline_user_args().has("--yay"):
		# v19 okçuluk testi (tools/tests/yay_testi.gd): her yayın dokunuş / tam bırakış / seri atış / akış ölçümü
		var yt2: Node = load("res://tools/tests/yay_testi.gd").new()
		yt2.set("main", self)
		add_child(yt2)
	if OS.get_cmdline_user_args().has("--vahset"):
		# v36 ölüm patlaması testi (tools/tests/vahset_testi.gd): kare şeritleri, 40 öldürüşte başarım, oda görüntüsü
		var vt: Node = load("res://tools/tests/vahset_testi.gd").new()
		vt.set("main", self)
		add_child(vt)
	if OS.get_cmdline_user_args().has("--perf"):
		# v38 başarım ölçümü (tools/tests/perf_testi.gd): bölüm kurma, yurt / konak, gezinti, kalabalık dövüş; Prof tablosu
		var pf: Node = load("res://tools/tests/perf_testi.gd").new()
		pf.set("main", self)
		add_child(pf)
	if OS.get_cmdline_user_args().has("--hikaye_test"):
		# v42 Güneş Ana hikâyesi testi / çekimi (tools/tests/hikaye_testi.gd): sinema panelleri, görüm, örgü, son, konak
		var hk: Node = load("res://tools/tests/hikaye_testi.gd").new()
		hk.set("main", self)
		add_child(hk)
	if OS.get_cmdline_user_args().has("--sanat"):
		# v27 savaş sanatları testi (tools/tests/sanat_testi.gd): bedel, bekleme, isabet, sınıf kuralı, kilit ve kayıt
		var sat: Node = load("res://tools/tests/sanat_testi.gd").new()
		sat.set("main", self)
		add_child(sat)
	var bengu_t := false
	for arg in OS.get_cmdline_user_args():
		bengu_t = bengu_t or String(arg) == "--bengu" or String(arg).begins_with("--bengu=")
	if bengu_t:
		# v20 Bengü testi (tools/tests/bengu_testi.gd): saç fiziği denetimi / çekimleri
		var bt: Node = load("res://tools/tests/bengu_testi.gd").new()
		bt.set("main", self)
		add_child(bt)
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--piksel_tara"):
			# stil v2 piksel denetimi (tools/tests/piksel_tara.gd): başka test bayraklarıyla birlikte çalışır
			var pt: Node = load("res://tools/tests/piksel_tara.gd").new()
			pt.set("main", self)
			add_child(pt)
			break
	var sus := false
	for arg in OS.get_cmdline_user_args():
		sus = sus or String(arg).begins_with("--sus=")
	if sus:  # stil v2 süs / toplanabilir / tehlike çekimi (tools/tests/sus_testi.gd)
		var st: Node = load("res://tools/tests/sus_testi.gd").new()
		st.set("main", self)
		add_child(st)
	if OS.get_cmdline_user_args().has("--unsur"):
		# v20 unsur testi (tools/tests/unsur_testi.gd): tetiklenme sayıları, ek hasar, iz / toz çekimleri
		var ut: Node = load("res://tools/tests/unsur_testi.gd").new()
		ut.set("main", self)
		add_child(ut)
	var firca := false
	for arg in OS.get_cmdline_user_args():
		firca = firca or String(arg).begins_with("--firca")
	if firca:  # stil v2 mürekkep fırçası laboratuvarı (tools/tests/firca_testi.gd)
		var ft: Node = load("res://tools/tests/firca_testi.gd").new()
		ft.set("main", self)
		add_child(ft)
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--fx_vitrin="):
			# efekt vitrini (tools/tests/fx_vitrin.gd): her efekt türü sabit düzende, önce/sonra çekimleri
			var fv: Node = load("res://tools/tests/fx_vitrin.gd").new()
			fv.set("main", self)
			add_child(fv)
			firca = true
	# yaratık testleri: --yaratik_cikti=... verilirse poz galerisi (yaratik_galeri.gd), yoksa canlı yapay zekâlı
	# çekim sahnesi ve Bozkurt biçimi (yaratik_testi.gd)
	var galeri := false
	for arg in OS.get_cmdline_user_args():
		galeri = galeri or String(arg).begins_with("--yaratik_cikti")
	for arg in OS.get_cmdline_user_args():
		if String(arg) == "--yaratik" or String(arg).begins_with("--yaratik="):
			var yt: Node = load("res://tools/tests/yaratik_galeri.gd" if galeri else "res://tools/tests/yaratik_testi.gd").new()
			yt.set("main", self)
			add_child(yt)
			firca = true  # oyun kipinde başla (başlık ekranı yok)
			break
	for arg in OS.get_cmdline_user_args():
		if String(arg) == "--boss":
			_build_boss("kara_boru_han")
		elif String(arg).begins_with("--boss="):
			_build_boss(String(arg).trim_prefix("--boss="))
	if auto_test or showcase or _ekran != "" or firca or sus or bengu_t or OS.get_cmdline_user_args().has("--mekanik") or OS.get_cmdline_user_args().has("--dovus") or OS.get_cmdline_user_args().has("--yay") or OS.get_cmdline_user_args().has("--unsur") or OS.get_cmdline_user_args().has("--denge") or OS.get_cmdline_user_args().has("--tomar") or OS.get_cmdline_user_args().has("--zeka") or OS.get_cmdline_user_args().has("--tuccar") or OS.get_cmdline_user_args().has("--harita") or OS.get_cmdline_user_args().has("--sanat") or OS.get_cmdline_user_args().has("--konak") or OS.get_cmdline_user_args().has("--isinlan") or OS.get_cmdline_user_args().has("--vahset") or OS.get_cmdline_user_args().has("--perf") or OS.get_cmdline_user_args().has("--otag") or OS.get_cmdline_user_args().has("--hikaye_test"):
		hud.mode = "play"
		get_tree().paused = false
	else:
		hud.mode = "title"
		get_tree().paused = true
		Ses.music("baslik")
	_v44_test()
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--sinema_kayit="):
			# v43 sinema kaydı / önizleme: --sinema_kayit=<ad> [--write-movie x.avi --fixed-fps 30]: oynatır, bitince çıkar
			var sk := String(arg).trim_prefix("--sinema_kayit=")
			hud.mode = "sinema"
			get_tree().paused = true
			sinema = Sinema.oynat(self, sk, Sinema.ornek_degisken(sk))
			sinema.bitti.connect(func() -> void: get_tree().quit())


## v44 testleri / çekimleri (tools/tests/derinlik44_testi.gd): --damga, --kodeks, --ozet, --basarim, --derinlik_ekran=<ad>.
## TEST_BAYRAKLARI'na girmez (koşu yurtta kurulur, test kendi bölümünü / konağını kurar); oyun kipinde başlar.
func _v44_test() -> void:
	for arg in OS.get_cmdline_user_args():
		var a := String(arg)
		if a in ["--damga", "--kodeks", "--ozet", "--basarim"] or a.begins_with("--derinlik_ekran="):
			var dt: Node = load("res://tools/tests/derinlik44_testi.gd").new()
			dt.set("main", self)
			add_child(dt)
			hud.mode = "play"
			get_tree().paused = false
			return


## v32: test / çekim bayraklarından biri varsa koşu doğrudan 1. derinlikte başlar (eski davranış; testler ve bot bölümü
## bekler); gerçek oyunda koşu Ulu Kayın yurdunda başlar (kapı 1. derinliğe indirir)
var _test_kipi := false
const TEST_BAYRAKLARI := ["--otomatik", "--sahne", "--savurus", "--ekran=", "--firca", "--fx_vitrin=", "--sus=", "--bengu", "--mekanik",
	"--dovus", "--yay", "--unsur", "--denge", "--tomar", "--zeka", "--tuccar", "--harita", "--sanat", "--yaratik", "--silah27",
	"--boss", "--piksel_tara", "--konak", "--isinlan", "--arayuz=", "--vahset", "--perf", "--otag", "--hikaye_test"]


func _test_bayragi() -> bool:
	for arg in OS.get_cmdline_user_args():
		for b in TEST_BAYRAKLARI:
			if String(arg) == b or String(arg).begins_with(b):
				return true
	return false


func _new_run() -> void:
	Ses.low_hp(0.0)
	Game.new_run()
	Game.meta["runs"] = int(Game.meta.get("runs", 0)) + 1
	Game.save_meta()
	if _test_kipi:
		_build_level()
	else:
		_build_hub()   # v32: koşu yurtta başlar (Umay / Demirci / Alp Ata / Ozan), kapı 1. derinliğe indirir
	if auto_test and _bot_gercek:
		_bot_loadout()


func _bot_loadout() -> void:
	## v22 --bot_gercek: derinliğe uygun "beklenen" donanım (o kademenin Nadir Demir Alp Kılıcı, derinlik başına
	## ~2,5 tılsımın etkisi; tools/tests/denge_testi.gd ile aynı varsayım), böylece bot derin bölümde de ölçü olur
	var d := int(Game.run.get("depth", 1))
	var o := Zorluk.beklenen_tomar(d)   # v23: derinlik başına tomar + geçilen boss tomarları (zorluk.json "tomar")
	if OS.get_cmdline_user_args().has("--tomarsiz"):
		o = {"kurt": 0, "kartal": 0, "ayi": 0}   # v23 ölçüm: tomar toplamayan oyuncu
	Game.run["ongun"] = o
	var hp := Zorluk.beklenen_can(o, float(Game.run["max_hp"]))
	Game.run["max_hp"] = hp
	Game.run["hp"] = hp
	if d > 1:
		Game.run["slots"]["melee"] = ItemGen.roll("alp_kilici", int(Game.run.get("tier", 0)), "demir", 1, "")
	if level and level.player:
		level.player.on_equip()
	_bot_last_hp = hp


func _build_level() -> void:
	if level:
		level.queue_free()
	level = Level.new()
	level.process_mode = Node.PROCESS_MODE_PAUSABLE
	add_child(level)
	Gorum.temizle()   # v42: önceki yerin sırada bekleyen konuşmaları
	var seed_v := randi() if not auto_test else 1234 + int(Game.run.get("depth", 1))
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--derinlik=") and not _depth_forced:
			_depth_forced = true
			var dd := int(String(arg).trim_prefix("--derinlik="))
			Game.run["depth"] = dd
			Game.run["tier"] = Zorluk.kademe(dd)
		if String(arg).begins_with("--tohum="):
			seed_v = int(String(arg).trim_prefix("--tohum=")) + int(Game.run.get("depth", 1))
	level.build(seed_v)
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--dok="):
			level.dump_png(String(arg).trim_prefix("--dok="))
	level.finished.connect(_on_finished)
	level.player_died.connect(_on_died)
	level.scroll_requested.connect(_on_scroll)
	level.slot_requested.connect(_on_slot_request)
	level.lutuf_requested.connect(_on_lutuf)
	level.tuccar_requested.connect(_on_tuccar)   # v24 Bezirgân Sartak
	level.harita_requested.connect(_harita_ac)   # v32: Kut Taşı'nın dibinde W
	level.tasi_bulundu.connect(func(i: int) -> void:
		hud.flash_msg = "Kut Taşı bulundu: %s  ·  M haritadan ışınlan" % String(level.harita.tasi[i]["ad"])
		hud.flash_t = 3.5
		hud._tut_show("kut_tasi"))
	hud.level = level
	hud._card_t = 0.0
	rehber.reset(level)


# ------------------------------------------------------------------ v32 harita ve Kut Taşı ışınlanması
var rehber := Rehber.new()   # --otomatik: dallı bölümde yol bulan bot rehberi


func _harita_ac() -> void:
	## Tam ekran harita (M ya da Kut Taşı'nın dibinde W): ağaç durur; A/D taş seçer, Boşluk ışınlanır
	if level == null or level.player == null or level.hub or level.boss_id != "" or level.harita == null:
		return
	hud.mode = "harita"
	var found: Array = level.harita.bulunan()
	hud.sel = 0
	var yakin: int = level.tasi_yakin()
	for i in found.size():
		if int(found[i]) != yakin:
			hud.sel = i
			break
	hud.open_anim()
	get_tree().paused = true
	Ses.play("ui_ac")


func _harita_sec(i: int) -> void:
	## Haritada seçili (i: bulunan taşlar dizini) Kut Taşı'na ışınlanma kanalını başlat ve haritayı kapat
	var found: Array = level.harita.bulunan()
	if found.is_empty():
		Ses.play("ui_sec", 0.0, 0.7)
		return
	var idx: int = int(found[clampi(i, 0, found.size() - 1)])
	if level.tasi_yakin() == idx:
		hud.flash_msg = "Zaten bu taşın dibindesin."
		hud.flash_t = 2.0
		Ses.play("ui_sec", 0.0, 0.7)
		return
	_start_play()
	if level.isinlan(idx):
		Ses.play("ui_onay")


func _build_boss(bid: String) -> void:
	if level:
		level.queue_free()
	level = Level.new()
	level.process_mode = Node.PROCESS_MODE_PAUSABLE
	add_child(level)
	Gorum.temizle()   # v42: önceki yerin sırada bekleyen konuşmaları
	level.build_boss(randi(), bid)
	level.finished.connect(_on_finished)
	level.player_died.connect(_on_died)
	level.slot_requested.connect(_on_slot_request)
	level.scroll_requested.connect(_on_scroll)   # v23: boss tomar bırakır
	level.boss_died.connect(func() -> void: hud.flash_msg = "Kut Kapısı açılıyor..."; hud.flash_t = 3.0)
	hud.level = level
	hud._card_t = 0.0


func _on_lutuf(p: Pickup) -> void:
	## Sunak: rastgele bir tanrı lütfu (sahip olunmayanlardan), en çok 3
	var have: Array = Game.run.get("lutuf", [])
	if have.size() >= 3:
		hud.flash_msg = "Üç lütuf taşıyorsun; sunak sessiz."
		hud.flash_t = 2.5
		return
	var pool: Array = []
	for k in Game.LUTUF.keys():
		if not (k in have):
			pool.append(k)
	if pool.is_empty():
		return
	var id: String = pool[randi() % pool.size()]
	Game.grant_lutuf(id)
	var l: Array = Game.LUTUF[id]
	var col := Color(l[2][0], l[2][1], l[2][2])
	if level.player:
		FX.ring(level.player.center(), 60, col, 0.6)
		FX.soul(level.player.center(), col, 30)
		FX.flash_light(level.player.center(), col, 260.0, 2.0, 0.5)
		FX.text(level.player.center() + Vector2(0, -44), String(l[0]), col, 11)
		level.player.vis_scale = Vector2(0.85, 1.15)
	Game.slowmo(0.4, 0.3)
	Ses.play("acilis", -2.0)
	hud.flash_msg = "%s: %s" % [l[0], l[1]]
	hud.flash_t = 5.0
	level.pickups.erase(p)
	p.queue_free()


func _on_tuccar() -> void:
	## v24: Bezirgân Sartak'ın pazarı (oyun durur). Mallar Level.bezirgan.offers; satın alma Pazar.satin_al.
	if level == null or level.bezirgan == null:
		return
	Pazar.gozde_tazele(level.bezirgan)   # v34: gözde mal oyuncunun şimdiki donanımına göre
	hud.sel = 0
	hud.tuccar_onay = false
	hud.mode = "tuccar"
	hud.open_anim()
	Ses.play("npc_1")
	Ses.play("ui_ac", -4.0)
	get_tree().paused = true


func _tuccar_sec(i: int) -> void:
	## Pazarda seçilen satıra onay (Boşluk / Enter): mal ise önce onay sorulur, ikinci basışta alınır; son satır yeniler.
	var bz: Bezirgan = level.bezirgan
	if i >= bz.offers.size():
		var ry := Pazar.yenile(bz)
		hud.flash_msg = ry["msg"]
		hud.flash_t = 2.5
		Ses.play("acilis" if ry["ok"] else "ui_sec", -4.0 if ry["ok"] else 0.0, 1.0 if ry["ok"] else 0.7)
		return
	var o: Dictionary = bz.offers[i]
	if bool(o["satildi"]):
		hud.flash_msg = "Bu mal satıldı."
		hud.flash_t = 2.0
		Ses.play("ui_sec", 0.0, 0.7)
		return
	if int(Game.run.get("gold", 0)) < int(o["fiyat"]):
		hud.flash_msg = "Altının yetmez (%d gerekir, %d var)." % [int(o["fiyat"]), int(Game.run.get("gold", 0))]
		hud.flash_t = 2.5
		Ses.play("ui_sec", 0.0, 0.7)
		return
	if not hud.tuccar_onay:
		hud.tuccar_onay = true
		Ses.play("ui_gez")
		return
	hud.tuccar_onay = false
	var r := Pazar.satin_al(level, bz, i)
	hud.flash_msg = r["msg"]
	hud.flash_t = 3.0
	if r["ok"]:
		Ses.play("altin", -2.0, 0.8)
		Ses.play("esya_kusan", -4.0)
		bz.talk()
		if level.player:
			FX.burst(level.player.center(), Color(1.0, 0.85, 0.4), 14, 70, 0.4, 0.16, -60, true)
	else:
		Ses.play("ui_sec", 0.0, 0.7)


func _demirci_ac(id: String) -> bool:
	## Parşömeni aç (Kut bankasından). v24: açılan eşya HEMEN verilir: koşu başı gücünde (kademe 0) normal düşüş gibi
	## rastgele yuvarlanır (malzeme, nadirlik, hasar, ek özellik, unsur) ve oyuncunun önüne bırakılır; düşme havuzuna da
	## girer (Game.unlock). Kart Demirci ekranında gösterilir (hud.demirci_son).
	if not Game.unlock(id):
		return false
	var it := ItemGen.roll(id, 0)
	hud.demirci_son = it
	if level and level.player:
		var pl: Player = level.player
		var x := pl.global_position.x + float(pl.facing) * 30.0
		var gy: float = level.ground_y_below(Vector2(x, pl.global_position.y - 30.0), 140.0)
		if gy < 0.0:
			x = pl.global_position.x
			gy = pl.global_position.y
		level.drop_item(it, Vector2(x, gy - 12.0))
		var p: Pickup = level.pickups[level.pickups.size() - 1]
		p.set_meta("parsomen_armagani", id)
		var rc := Color.from_string(Data.items["rarities"][int(it["rarity"])]["color"], Color.WHITE)
		FX.ring(Vector2(x, gy - 16.0), 30, rc, 0.5)
		FX.burst(Vector2(x, gy - 16.0), Color(1.0, 0.6, 0.3), 18, 90, 0.5, 0.2, -80, true)
	return true


func _build_hub() -> void:
	## Bölüm bitti: Ulu Kayın yurdu (NPC'ler). Eşyalar ve can korunur.
	if level:
		level.queue_free()
	level = Level.new()
	level.process_mode = Node.PROCESS_MODE_PAUSABLE
	add_child(level)
	Gorum.temizle()   # v42: önceki yerin sırada bekleyen konuşmaları
	level.build_hub(77)
	level.finished.connect(_on_finished)
	level.player_died.connect(_on_died)
	level.npc_requested.connect(_on_npc)
	level.slot_requested.connect(_on_slot_request)   # v24: Demirci'nin dövdüğü eşya yurtta alınır (yuva seçimi)
	hud.level = level
	hud._card_t = 99.0
	HikayeSahne.yoldas(level)   # v43: yeni örgüyle Umay'ın anısı


func _next_level() -> void:
	## Konaksız geçiş (--sahne "done" ekranı): bir sonraki derinlik hemen kurulur
	Game.next_depth()
	Game.meta["best_depth"] = maxi(int(Game.meta.get("best_depth", 1)), int(Game.run["depth"]))
	Game.save_meta()
	_build_level()
	_start_play()


func _build_konak() -> void:
	## v32: derinlikler arası gezgin konak (Level.build_konak). Eşyalar ve can korunur; tohum derinliğe bağlı (test belirlenimci)
	if level:
		level.queue_free()
	level = Level.new()
	level.process_mode = Node.PROCESS_MODE_PAUSABLE
	add_child(level)
	Gorum.temizle()   # v42: önceki yerin sırada bekleyen konuşmaları
	var seed_v := randi() if not auto_test else 4321 + int(Game.run.get("depth", 1))
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--tohum="):
			seed_v = int(String(arg).trim_prefix("--tohum=")) * 7 + int(Game.run.get("depth", 1))
	level.build_konak(seed_v)
	level.finished.connect(_on_finished)
	level.player_died.connect(_on_died)
	level.npc_requested.connect(_on_npc)
	level.tuccar_requested.connect(_on_tuccar)
	level.slot_requested.connect(_on_slot_request)
	level.scroll_requested.connect(_on_scroll)
	hud.level = level
	hud._card_t = 0.0
	HikayeSahne.yoldas(level)   # v43: Umay'ın anısı, Ozan'ın bölüm dizesi


func _to_konak() -> void:
	## Kut Kapısı (ya da boss) geçildi: bir sonraki derinliğe inilir (Game.next_depth: can +%15, şişeler dolar), konak kurulur
	var hp0 := float(Game.run.get("hp", 0.0))
	Game.run["lutuf"] = []  # lütuflar konakta söner (eskiden yurda dönünce)
	Game.next_depth()
	Game.meta["best_depth"] = maxi(int(Game.meta.get("best_depth", 1)), int(Game.run["depth"]))
	Game.save_meta()
	_build_konak()
	_start_play()
	# v44 başarımlar (konak: Yel Gibi, Çıplak Yiğit, Dokunulmaz); bölümde alınan hasar sıfırlanır
	var oz44: Dictionary = Game.run.get("oz", {})
	Basarim.olay("konak", {"hasarsiz": float(oz44.get("bolum_alinan", 1.0)) <= 0.0 and int(Game.run.get("kills", 0)) > 0})
	oz44["bolum_alinan"] = 0.0
	var heal := int(round(float(Game.run.get("hp", 0.0)) - hp0))
	hud.flash_msg = "Konak: can +%d, şişeler doldu. Kut'u ocağa, silahını Bengisu Usta'ya götür; kapı derine indirir." % heal
	hud.flash_t = 5.0
	if level.player:
		if heal > 0:
			FX.number(level.player.center() + Vector2(0, -12), float(heal), false, Color(0.55, 1.0, 0.55))
		FX.soul(level.player.center(), Color(0.6, 1.0, 0.75), 12)


func _on_finished() -> void:
	if level and (level.hub or level.konak):
		# yurttan 1. derinliğe / konaktan sıradaki derinliğe (derinlik Game.run'da hazır)
		_build_level()
		_start_play()
		return
	# bu derinliğin sonunda boss var mı?
	var depth := int(Game.run.get("depth", 1))
	if level and level.boss_id == "":
		var bid: String = String(Game.BOSS_AFTER.get(depth, ""))
		if bid != "" and not (bid in Game.run.get("boss_done", [])):
			_build_boss(bid)
			_start_play()
			Game.run["lutuf"] = Game.run.get("lutuf", [])
			return
	if auto_test:
		_bot_report("BOLUM_SONU")   # v32: bot da konaktan geçer (kapı → konak → Usta → kapı)
	elif showcase:
		hud.mode = "done"
		get_tree().paused = true
		return
	_to_konak()


func _on_npc(id: String) -> void:
	hud.sel = 0
	get_tree().paused = true
	match id:
		"umay":
			var saved := int(Game.run.get("kut", 0))
			if saved > 0:
				Game.bank_run_kut()
				Ses.play("kut_banka")
				hud.flash_msg = "%d Kut Umay'a ulaştı." % saved
				hud.flash_t = 3.0
				if level.player:
					FX.soul(level.player.center(), Color(0.6, 1.0, 1.0), 30)
			hud.mode = "umay"
		"demirci":
			Ses.play("ors")
			hud.mode = "demirci"
		"ozan":
			if not Adlar.pending().is_empty():
				_ad_toreni()
				return
			Ses.play("npc_1")
			hud.ozan_i = 0   # v42: destan özeti ilk sayfadan (Hikaye.ozan_sayfalari)
			hud.mode = "ozan"
		"alp_ata":
			Ses.play("npc_2")
			_open_sanat(true)
		"usta":
			_usta_ac()
		"damga":
			DerinlikUI.damga_ac(self)   # v44 Damga Taşı


# ------------------------------------------------------------------ v32 Bengisu Usta (konak)
func _usta_ac() -> void:
	## Usta ekranı: 0 silah seç → 1 hizmet seç → 2 (nakış / unsur) seçenek → 3 sonuç kartı. Oyun durur.
	hud.usta_adim = 0
	hud.usta_slot = ""
	hud.usta_hid = ""
	hud.usta_secs = []
	hud.usta_sonuc = {}
	hud.usta_onay = false
	hud.sel = 0
	hud.mode = "usta"
	hud.open_anim()
	Ses.play("npc_3")
	Ses.play("ui_ac", -4.0)
	get_tree().paused = true


func _usta_satirlar() -> int:
	## Usta ekranında şu adımın satır sayısı
	match hud.usta_adim:
		0:
			return Usta.silahlar().size()
		1:
			return Usta.HIZMETLER.size()
		2:
			return hud.usta_secs.size()
	return 1


func _usta_sec(i: int) -> void:
	## Boşluk / Enter: adım ilerler; doğrudan hizmetlerde (dövme / kalite / mühür) ilk basış onay, ikincisi uygular
	match hud.usta_adim:
		0:
			var sl := Usta.silahlar()
			if sl.is_empty():
				hud.flash_msg = "Kuşanılı silahın yok."
				hud.flash_t = 2.0
				Ses.play("ui_sec", 0.0, 0.7)
				return
			hud.usta_slot = String(sl[clampi(i, 0, sl.size() - 1)])
			hud.usta_adim = 1
			hud.sel = 0
			hud.open_anim()
			Ses.play("ui_onay")
		1:
			var it: Dictionary = Game.run["slots"].get(hud.usta_slot, {})
			var hs := Usta.hizmetler(it)
			var h: Dictionary = hs[clampi(i, 0, hs.size() - 1)]
			if not bool(h["uygun"]):
				hud.flash_msg = String(h["neden"])
				hud.flash_t = 2.5
				Ses.play("ui_sec", 0.0, 0.7)
				return
			var hid := String(h["id"])
			if hid in ["nakis", "unsur"]:
				hud.usta_hid = hid
				hud.usta_secs = Usta.secenekler(hid, hud.usta_slot, it)
				hud.usta_adim = 2
				hud.sel = 0
				hud.usta_onay = false
				hud.open_anim()
				Ses.play("ui_onay")
				return
			if int(Game.run.get("gold", 0)) < int(h["fiyat"]):
				hud.flash_msg = "Altının yetmez (%d gerekir, %d var)." % [int(h["fiyat"]), int(Game.run.get("gold", 0))]
				hud.flash_t = 2.5
				Ses.play("ui_sec", 0.0, 0.7)
				return
			if not hud.usta_onay:
				hud.usta_onay = true
				hud.usta_hid = hid
				Ses.play("ui_gez")
				return
			hud.usta_onay = false
			_usta_uygula(hid, {})
		2:
			if hud.usta_secs.is_empty():
				return
			var o: Dictionary = hud.usta_secs[clampi(i, 0, hud.usta_secs.size() - 1)]
			if int(Game.run.get("gold", 0)) < int(o["fiyat"]):
				hud.flash_msg = "Altının yetmez (%d gerekir, %d var)." % [int(o["fiyat"]), int(Game.run.get("gold", 0))]
				hud.flash_t = 2.5
				Ses.play("ui_sec", 0.0, 0.7)
				return
			if not hud.usta_onay:
				hud.usta_onay = true
				Ses.play("ui_gez")
				return
			hud.usta_onay = false
			_usta_uygula(hud.usta_hid, o)
		3:
			# sonuç kartı kapanır: aynı silahla hizmet listesine dönülür
			hud.usta_sonuc = {}
			hud.usta_adim = 1
			hud.sel = 0
			hud.open_anim()
			Ses.play("ui_gez")


func _usta_uygula(hid: String, opt: Dictionary) -> Dictionary:
	## Hizmeti uygula (Usta.uygula), sonucu karta koy; efekt + ses
	var r := Usta.uygula(hid, hud.usta_slot, opt)
	if not r["ok"]:
		hud.flash_msg = String(r["msg"])
		hud.flash_t = 2.5
		Ses.play("ui_sec", 0.0, 0.7)
		return r
	hud.usta_sonuc = r
	hud.usta_adim = 3
	hud.usta_damga_t = 0.0
	hud.flash_msg = String(r["msg"])
	hud.flash_t = 4.0
	Ses.play("altin", -4.0, 0.9)
	match hid:
		"nakis":
			Ses.play("usta_nakis")
			Ses.play("usta_damga", -3.0)
		"dovme":
			Ses.play("usta_dovme")
		"unsur":
			Ses.play("buyu", -4.0, 1.1)
			Ses.play("usta_damga", -3.0)
		"kalite":
			Ses.play("usta_dovme" if bool(r["iyi"]) else "ui_sec", 0.0 if bool(r["iyi"]) else -2.0, 1.0 if bool(r["iyi"]) else 0.6)
		"muhur":
			Ses.play("usta_damga")
			Ses.play("kut_banka" if bool(r["iyi"]) else "ui_iptal", -4.0)
	if level and level.player:
		level.player.on_equip()
		var pc: Vector2 = level.player.center()
		if bool(r["kotu"]):
			FX.soul(pc, Color(0.7, 0.3, 0.9), 16)
		else:
			FX.sparks(pc + Vector2(0, -6), Vector2(0.3, -1), Color(1.0, 0.8, 0.4), 10, 110.0)
			FX.ring(pc, 30, Color(0.55, 1.0, 0.9), 0.4)
		for n in level.npcs:
			if n.id == "usta":
				n.talk()
	return r


func _open_sanat(mentor: bool) -> void:
	## v27 savaş sanatları ekranı: duraklatmadan (T) kuşan; Alp Ata'da öğren (Kut bankası) + kuşan
	hud.sanat_ogretmen = mentor
	hud.sel = maxi(0, SavasSanati.ids().find(SavasSanati.secili()))
	hud.mode = "sanat"
	hud.open_anim()
	Ses.play("ui_ac", -4.0)
	get_tree().paused = true


func _sanat_sec(i: int) -> void:
	var ids := SavasSanati.ids()
	var id: String = ids[clampi(i, 0, ids.size() - 1)]
	var ad := String(SavasSanati.def_of(id).get("ad", id))
	if SavasSanati.acik_mi(id):
		if SavasSanati.secili() == id:
			hud.flash_msg = "%s zaten kuşanılı." % ad
			Ses.play("ui_sec", 0.0, 0.8)
		else:
			SavasSanati.sec(id)
			hud.flash_msg = "%s kuşanıldı (T)." % ad
			Ses.play("esya_kusan", -4.0)
	elif hud.sanat_ogretmen:
		if SavasSanati.ogret(id):
			SavasSanati.sec(id)
			hud.flash_msg = "Alp Ata %s sanatını öğretti; kuşanıldı." % ad
			Ses.play("acilis", -2.0)
			Ses.play("ors", -8.0, 1.2)
			if level and level.player:
				FX.soul(level.player.center(), SavasSanati.renk(id), 24)
		else:
			hud.flash_msg = "Yeterli Kut yok (%d gerekir, bankada %d)." % [SavasSanati.bedel(id), int(Game.meta.get("kut_bank", 0))]
			Ses.play("ui_sec", 0.0, 0.7)
	else:
		hud.flash_msg = "Kilitli: yurtta Alp Ata öğretir ya da Sanat Tomarı bul."
		Ses.play("ui_sec", 0.0, 0.7)
	hud.flash_t = 2.5


func _on_died() -> void:
	if level and not level.hub and not level.konak:
		Hikaye.olum_isaretle(String(level.biome.get("id", "")))   # v43: biyomdaki ilk ölüm satırı
	var saved := Game.lose_run_kut()
	KosuOzet.olum(String(level.biome.get("id", "")) if level else "")   # v44: ölüm nedeni (kodeks: seni devirdi)
	DerinlikUI.ozet_kur(false)   # v44 koşu özeti ve rekorlar
	hud.flash_msg = ("Ruh Düğümü %d Kut kurtardı." % saved) if saved > 0 else ""
	hud.mode = "dead"
	Ses.music("baslik", 2.5)
	get_tree().paused = true


func _on_scroll(p: Pickup) -> void:
	scroll_pickup = p
	hud.sel = 0
	hud.mode = "tilsim"
	Ses.play("ui_ac")
	get_tree().paused = true


func _on_slot_request(p: Pickup) -> void:
	## İki uygun yuva da dolu: hangisinin değişeceğini oyuncu seçer (oyun durur).
	slot_pickup = p
	var opts: Array = level.slot_options(p.item)
	hud.slot_opts = opts
	hud.sel = maxi(0, opts.find(level.natural_slot(p.item)))
	hud.mode = "slot"
	hud.open_anim()
	Ses.play("ui_ac")
	get_tree().paused = true


func _finish_slot(slot: String) -> void:
	if slot != "" and is_instance_valid(slot_pickup) and level:
		level.equip(slot_pickup, slot)
		Ses.play("esya_degis")
	else:
		Ses.play("ui_iptal")
	slot_pickup = null
	_start_play()


func _apply_scroll(sel: int) -> void:
	## v23 Kut Tomarı: seçilen stat +1 (eşyaların hasarı Zorluk.tomar_k ile), azami can artar; SnH değişimi duyurulur
	var keys := ["kurt", "kartal", "ayi"]
	var k: String = keys[sel]
	var msk := String(level.player.mel_slot) if level and level.player and String(level.player.mel_slot) != "" else "melee"
	var mel: Dictionary = Game.run["slots"].get(msk, {})
	var dps0 := ItemGen.dps_oyuncu(mel) if not mel.is_empty() else 0.0
	Game.run["ongun"][k] = int(Game.run["ongun"][k]) + 1
	var hp_gain := float(Game.run["max_hp"]) * Zorluk.tomar_can(k)
	Game.run["max_hp"] = float(Game.run["max_hp"]) + hp_gain
	Game.run["hp"] = minf(float(Game.run["max_hp"]), float(Game.run["hp"]) + hp_gain + float(Game.run["max_hp"]) * Zorluk.tomar_iyilesme())
	Game.run["scrolls"] = int(Game.run.get("scrolls", 0)) + 1
	var dps1 := ItemGen.dps_oyuncu(mel) if not mel.is_empty() else 0.0
	if dps1 > dps0 + 0.05:
		hud.flash_msg = "%s +1 · %s SnH %s → %s" % [Data.items["ongun"][k]["name"], String(mel.get("name_base", "")), ItemGen.fmt(dps0), ItemGen.fmt(dps1)]
	else:
		hud.flash_msg = "%s +1 · azami can +%d" % [Data.items["ongun"][k]["name"], int(round(hp_gain))]
	hud.flash_t = 3.5
	Ses.play("tilsim_sec")
	Ses.play("seviye", -4.0)
	if level and level.player:
		var col := Color.from_string(Data.items["ongun"][k]["color"], Color.WHITE)
		FX.ring(level.player.center(), 40, col, 0.4)
		FX.soul(level.player.center(), col, 24)
		FX.text(level.player.center() + Vector2(0, -36), "%s +1" % Data.items["ongun"][k]["name"], col, 9)
		level.player.vis_scale = Vector2(0.85, 1.15)
	if is_instance_valid(scroll_pickup):
		if level:   # v34: tomar kaidenin üstünde açılır, seçilen statın tamgası parlayıp oyuncuya uçar
			TomarV2.acilis(level, scroll_pickup.global_position + Vector2(0, Pickup.TOMAR_Y), k, level.player)
		level.pickups.erase(scroll_pickup)
		scroll_pickup.queue_free()
	scroll_pickup = null
	_start_play()


func _unhandled_input(event: InputEvent) -> void:
	if DerinlikUI.girdi(self, event):
		return   # v44: Damga Taşı, Ozan'ın Destanı, zafer özeti (ve ölüm / Ozan / duraklatmadan C)
	var go: bool = event.is_action_pressed("zipla") or (event is InputEventKey and event.pressed and event.physical_keycode == KEY_ENTER)
	match hud.mode:
		"ayarlar":
			var n: int = Ayarlar.rows().size()
			if event.is_action_pressed("yukari"):
				hud.sel = (hud.sel + n - 1) % n
				Ses.play("ui_gez")
			elif event.is_action_pressed("asagi"):
				hud.sel = (hud.sel + 1) % n
				Ses.play("ui_gez")
			elif event.is_action_pressed("sol") or event.is_action_pressed("sag"):
				Ayarlar.change(hud.sel, -1 if event.is_action_pressed("sol") else 1)
				Ses.play("ui_onay")
			elif go:   # v23: menüde onay Boşluk / Enter (W / ↑ seçimi gezer)
				Ayarlar.change(hud.sel, 1)
				Ses.play("ui_onay")
			elif event.is_action_pressed("duraklat") or event.is_action_pressed("ayarlar"):
				hud.mode = hud.back_mode
				Ses.play("ui_iptal")
		"title":
			if event.is_action_pressed("ayarlar"):
				_open_settings()
			elif go:
				Ses.play("ui_onay")
				if not bool(Game.meta.get("giris_izlendi", false)):
					_giris_oynat(true)   # v42: açılış sineması ilk kez kendiliğinden (sonra Ozan'dan)
				else:
					_after_intro()
		"intro":
			if event.is_action_pressed("duraklat"):
				_after_intro()
			elif go:
				hud.intro_i += 1
				if hud.intro_i >= Data.story["intro"].size():
					_after_intro()
		"dead":
			if go:
				_new_run()
				_after_intro()
		"done":
			if go:
				_next_level()
		"tilsim":
			if event.is_action_pressed("sol"):
				hud.sel = (hud.sel + 2) % 3
				Ses.play("ui_gez")
			elif event.is_action_pressed("sag"):
				hud.sel = (hud.sel + 1) % 3
				Ses.play("ui_gez")
			elif go or event.is_action_pressed("saldiri1"):
				_apply_scroll(hud.sel)
		"slot":
			var opts: Array = hud.slot_opts
			if event.is_action_pressed("sol") or event.is_action_pressed("sag") or event.is_action_pressed("yukari") or event.is_action_pressed("asagi"):
				hud.sel = 1 - hud.sel
				Ses.play("ui_gez")
			elif event.is_action_pressed("saldiri1") and "melee" in opts:
				_finish_slot("melee")
			elif event.is_action_pressed("saldiri2") and "second" in opts:
				_finish_slot("second")
			elif event.is_action_pressed("techizat1") and "g1" in opts:
				_finish_slot("g1")
			elif event.is_action_pressed("techizat2") and "g2" in opts:
				_finish_slot("g2")
			elif go:
				_finish_slot(String(opts[clampi(hud.sel, 0, opts.size() - 1)]))
			elif event.is_action_pressed("duraklat") or event.is_action_pressed("yuvarlan"):
				_finish_slot("")
		"demirci":
			var bps: Array = Game.meta.get("blueprints", [])
			if not hud.demirci_son.is_empty():
				# v24: dövülen eşyanın kartı açık; Boşluk / Esc kapatır (sonra başka parşömen açılabilir)
				if go or event.is_action_pressed("duraklat") or event.is_action_pressed("yuvarlan"):
					hud.demirci_son = {}
					Ses.play("ui_gez")
				return
			if event.is_action_pressed("sol") and bps.size() > 0:
				hud.sel = (hud.sel + bps.size() - 1) % bps.size()
				Ses.play("ui_gez")
			elif event.is_action_pressed("sag") and bps.size() > 0:
				hud.sel = (hud.sel + 1) % bps.size()
				Ses.play("ui_gez")
			elif go and bps.size() > 0:   # v23: Boşluk / Enter parşömeni açar; Esc yola çıkar
				var id: String = bps[clampi(hud.sel, 0, bps.size() - 1)]
				if _demirci_ac(id):
					hud.flash_msg = "%s dövüldü: önüne bırakıldı. Artık düşebilir de." % Data.find_item(id).get("name", id)
					hud.sel = 0
					Ses.play("acilis")
				else:
					hud.flash_msg = "Yeterli Kut yok (%d gerekir)." % Game.unlock_cost(id)
					Ses.play("ui_sec", 0.0, 0.7)
				hud.flash_t = 2.0
			elif go or event.is_action_pressed("duraklat") or event.is_action_pressed("yuvarlan"):
				_start_play()
		"tuccar":
			# v24 pazar: W/S (A/D) satır, Boşluk / Enter onay (iki adım), Esc / L onayı geri alır ya da ayrılır
			var n_rows: int = level.bezirgan.offers.size() + 1 if level and level.bezirgan else 1
			if event.is_action_pressed("yukari") or event.is_action_pressed("sol"):
				hud.sel = (hud.sel + n_rows - 1) % n_rows
				hud.tuccar_onay = false
				Ses.play("ui_gez")
			elif event.is_action_pressed("asagi") or event.is_action_pressed("sag"):
				hud.sel = (hud.sel + 1) % n_rows
				hud.tuccar_onay = false
				Ses.play("ui_gez")
			elif go:
				_tuccar_sec(hud.sel)
			elif event.is_action_pressed("duraklat") or event.is_action_pressed("yuvarlan"):
				if hud.tuccar_onay:
					hud.tuccar_onay = false
					Ses.play("ui_iptal")
				else:
					Ses.play("ui_iptal")
					_start_play()
		"usta":
			# v32 Usta: W/S satır, Boşluk / Enter ilerle / onay, Esc / L bir adım geri (ilk adımda ayrıl)
			var n_u := maxi(1, _usta_satirlar())
			if event.is_action_pressed("yukari") or event.is_action_pressed("sol"):
				hud.sel = (hud.sel + n_u - 1) % n_u
				hud.usta_onay = false
				Ses.play("ui_gez")
			elif event.is_action_pressed("asagi") or event.is_action_pressed("sag"):
				hud.sel = (hud.sel + 1) % n_u
				hud.usta_onay = false
				Ses.play("ui_gez")
			elif go:
				_usta_sec(hud.sel)
			elif event.is_action_pressed("duraklat") or event.is_action_pressed("yuvarlan"):
				Ses.play("ui_iptal")
				if hud.usta_onay:
					hud.usta_onay = false
				elif hud.usta_adim == 0:
					_start_play()
				elif hud.usta_adim == 3:
					hud.usta_sonuc = {}
					hud.usta_adim = 1
					hud.sel = 0
				else:
					hud.usta_adim -= 1
					hud.sel = 0
					hud.open_anim()
		"umay":
			var keys: Array = Game.UMAY.keys()
			if event.is_action_pressed("yukari") or event.is_action_pressed("sol"):
				hud.sel = (hud.sel + keys.size() - 1) % keys.size()
				Ses.play("ui_gez")
			elif event.is_action_pressed("asagi") or event.is_action_pressed("sag"):
				hud.sel = (hud.sel + 1) % keys.size()
				Ses.play("ui_gez")
			elif go:   # v23: Boşluk / Enter alır; Esc ayrılır
				var id: String = keys[hud.sel]
				if Game.umay_buy(id):
					hud.flash_msg = "%s: seviye %d." % [Game.UMAY[id][0], Game.umay_level(id)]
					Ses.play("acilis")
					if id == "sise":
						Game.run["max_flasks"] = int(Game.run["max_flasks"]) + 1
						Game.run["flasks"] = int(Game.run["flasks"]) + 1
					elif id == "can":
						Game.run["max_hp"] = float(Game.run["max_hp"]) * 1.1
						Game.run["hp"] = float(Game.run["hp"]) * 1.1
				else:
					hud.flash_msg = "Yeterli Kut yok." if Game.umay_cost(id) >= 0 else "Bu armağan tamamlandı."
					Ses.play("ui_sec", 0.0, 0.7)
				hud.flash_t = 2.0
			elif event.is_action_pressed("duraklat") or event.is_action_pressed("yuvarlan"):
				_start_play()
		"ad":
			if (go or event.is_action_pressed("duraklat")) and hud.ad_t > 1.2:
				if not Adlar.pending().is_empty():
					_ad_toreni()
				else:
					_start_play()
		"ozan":
			if go:
				hud.ozan_i += 1
				Ses.play("npc_%d" % (1 + hud.ozan_i % 3))
				if hud.ozan_i >= Hikaye.ozan_sayfalari().size():
					_start_play()
			elif event.is_action_pressed("techizat1"):
				_giris_oynat(false)   # v42: Ozan açılış destanını yeniden anlatır
			elif event.is_action_pressed("duraklat") or event.is_action_pressed("yuvarlan"):
				_start_play()
		"sanat":
			# v27 savaş sanatları: W/S seç, Boşluk / Enter kuşan (Alp Ata'da öğren), Esc / L geri
			var n_s: int = SavasSanati.ids().size()
			if event.is_action_pressed("yukari") or event.is_action_pressed("sol"):
				hud.sel = (hud.sel + n_s - 1) % n_s
				Ses.play("ui_gez")
			elif event.is_action_pressed("asagi") or event.is_action_pressed("sag"):
				hud.sel = (hud.sel + 1) % n_s
				Ses.play("ui_gez")
			elif go:
				_sanat_sec(hud.sel)
			elif event.is_action_pressed("duraklat") or event.is_action_pressed("yuvarlan") or (event.is_action_pressed("sanat") and not hud.sanat_ogretmen):
				Ses.play("ui_iptal")
				if hud.sanat_ogretmen:
					_start_play()
				else:
					hud.mode = "play"   # duraklatma ekranına dön (ağaç duraklı kalır)
		"harita":
			# v32: A/D (W/S) taş seç, Boşluk / Enter ışınlan, M / Esc kapat
			var nf: int = level.harita.bulunan().size() if level and level.harita else 0
			if event.is_action_pressed("sol") or event.is_action_pressed("yukari"):
				if nf > 0:
					hud.sel = (hud.sel + nf - 1) % nf
					Ses.play("ui_gez")
			elif event.is_action_pressed("sag") or event.is_action_pressed("asagi"):
				if nf > 0:
					hud.sel = (hud.sel + 1) % nf
					Ses.play("ui_gez")
			elif go:
				_harita_sec(hud.sel)
			elif event.is_action_pressed("duraklat") or event.is_action_pressed("harita") or event.is_action_pressed("yuvarlan"):
				Ses.play("ui_kapa")
				_start_play()
		"play":
			if event.is_action_pressed("duraklat"):
				get_tree().paused = not get_tree().paused
			elif event.is_action_pressed("harita") and not get_tree().paused:
				_harita_ac()   # v32: tam ekran harita
			elif event.is_action_pressed("ayarlar") and get_tree().paused:
				_open_settings()
			elif event.is_action_pressed("sanat") and get_tree().paused:
				_open_sanat(false)   # v27: duraklatmada T savaş sanatlarını açar


func _open_settings() -> void:
	hud.back_mode = hud.mode
	hud.mode = "ayarlar"
	hud.sel = 0
	hud.open_anim()
	Ses.play("ui_ac")


func _ad_toreni() -> void:
	## Ozan kopuzunu alır, destanı anlatır, yiğide adını koyar
	var id: String = Adlar.pending()[0]
	Adlar.grant(id)
	hud.ad_id = id
	hud.ad_t = 0.0
	hud.mode = "ad"
	get_tree().paused = true
	Ses.play("ad_toren", 0.0)
	if level and level.player:
		FX.soul(level.player.center(), Color(1.0, 0.85, 0.45), 30)


# ------------------------------------------------------------------ v42 Güneş Ana hikâyesi
var sinema: Sinema = null


func _giris_oynat(ilk: bool) -> void:
	## Açılış sineması (Sinema.gd "giris"). ilk: başlıktan (bitince yurda), değilse Ozan'dan (bitince oyuna dönülür)
	hud.mode = "sinema"
	get_tree().paused = true
	sinema = Sinema.oynat(self, "giris")
	sinema.bitti.connect(func() -> void:
		sinema = null
		Game.meta["giris_izlendi"] = true
		Game.save_meta()
		if ilk:
			_after_intro()
		else:
			Ses.music("yurt", 1.5)
			_start_play())


func hikaye_sinema(k: String, deg := {}, sonra := Callable()) -> Sinema:
	## v43 oyun içi kısa sinema (boss kartı, örgü sahnesi, bölüm açılışı; Sinema.gd motoru): ağaç durur, bitince oyuna
	## dönülür. Başka bir sinema sürüyorsa oynamaz (null).
	if sinema != null or not Sinema.var_mi(k):
		return null
	hud.mode = "sinema"
	get_tree().paused = true
	# v43 birleştirme: _start_play bölüm afişini sıfırlıyordu: boss kartı / örgü sahnesi bitince arenada biyom afişi
	# ("Bozkır Kurganları") baştan yeniden oynuyordu. Afişin sayacı sinema boyunca korunur.
	var kart_t: float = hud._card_t
	sinema = Sinema.oynat(self, k, deg)
	sinema.bitti.connect(func() -> void:
		sinema = null
		_start_play()
		hud._card_t = kart_t
		if sonra.is_valid():
			sonra.call())
	return sinema


func hikaye_orgu_alindi(bid: String, yeni: bool) -> bool:
	## GunParcasi: örgü alındı. v43: ilk kez alındıysa örgü sahnesi (data/sinema/orgu_sahne.json; örgü Gün Ana'ya akar,
	## beş yuvadan biri dolar), bitince HUD'da Gün Örgüleri göstergesi; Erlik'in Altın Örgüsü sahneden sonra son sinemayı
	## başlatır. true: sahne oynadı (GunParcasi ayrıca görüm göstermez).
	var sira := Hikaye.ORGU_SIRA.find(bid)
	var son := bid == "erlik_han" and not Hikaye.safak()
	if yeni:
		var dolu: Array = (Game.meta.get("gun_parca", []) as Array).filter(func(x: Variant) -> bool: return String(x) != bid)
		var s := hikaye_sinema("orgu_sahne", Sinema.orgu_degisken(bid, dolu), func() -> void:
			OrguGosterge.bildir(sira)
			if son:
				get_tree().create_timer(0.8, false).timeout.connect(hikaye_son))
		if s != null:
			return true
	OrguGosterge.bildir(sira)
	if son:
		get_tree().create_timer(6.5, false).timeout.connect(hikaye_son)
	return false


func hikaye_son() -> void:
	## Son: zincir kırılır, Gün Ana yükselir, tan söker; jenerik. Sonra dünya "tan sökmüş" kalır: koşu biter (Kut
	## bankaya), yeni koşu sabah ışığındaki yurtta başlar (yeni oyun+ aynı yoldan sürer).
	if sinema != null or Hikaye.safak():
		return
	hud.mode = "sinema"
	get_tree().paused = true
	sinema = Sinema.oynat(self, "son")
	sinema.bitti.connect(func() -> void:
		sinema = null
		Game.meta["son_izlendi"] = true
		Game.bank_run_kut()
		DerinlikUI.ozet_kur(true)   # v44: zafer özeti (yeni koşudan önce)
		Game.save_meta()
		Game.new_run()
		Game.meta["runs"] = int(Game.meta.get("runs", 0)) + 1
		Game.save_meta()
		_build_hub()
		_start_play()
		hud.flash_msg = "Tan söktü. Ulu Kayın sabah ışığında; gece yine gelecek, yol yine aşağı iner."
		hud.flash_t = 6.0
		hud.mode = "zafer"   # v44: zafer özeti (Boşluk ile yurtta devam)
		get_tree().paused = true)


func _after_intro() -> void:
	## Hikâyeden (ya da ölümden) sonra: v32 koşu yurtta başlar (Demirci orada; bekleyen parşömen varsa hatırlatılır).
	## Test kipinde (bölümde başlayınca) bekleyen parşömen varsa eski Demirci ekranı açılır.
	if level and level.hub:
		_start_play()
		var bps: Array = Game.meta.get("blueprints", [])
		hud.flash_msg = ("Ulu Kayın yurdu: %d parşömen bekliyor, Demirci'ye uğra. Kapı derine indirir." % bps.size()) if not bps.is_empty() else "Ulu Kayın yurdu: Kut'unu Umay Ana'ya götür (W). Kapı seni derine indirir."
		hud.flash_t = 5.0
	elif not Game.meta.get("blueprints", []).is_empty():
		hud.mode = "demirci"
		hud.sel = 0
		get_tree().paused = true
	else:
		_start_play()


func _start_play() -> void:
	hud.mode = "play"
	hud._card_t = 0.0
	get_tree().paused = false


# ------------------------------------------------------------------ otomatik test (--otomatik)
var _auto_t := 0.0
var _auto_pressed: Array = []
var _auto_last_x := 0.0
var _auto_stuck := 0.0
var _sc_t := 0.0
var _sc_step := -1
var _sc_hold := ""


func _lab(delta: float) -> void:
	## Savuruş laboratuvarı: düşman yok, karakter sabit; her savuruş tipi sırayla, aralarında boşluk.
	if hud.mode != "play" or level == null or level.player == null:
		return
	var pl: Player = level.player
	if _sc_step < 0:
		_sc_step = 0
		var tx := 40
		pl.global_position = Vector2(tx * 24.0, level.surface_y(tx) * 24.0 - 2)
		pl.facing = 1
		Game.camera.reset_smoothing.call_deferred()
	for e in get_tree().get_nodes_in_group("dusman"):
		e.queue_free()
	_sc_t += delta
	var f := int(_sc_t * 60.0)
	# v5: silaha özgü savuruşlar (hepsi sağa bakar; kontak sayfasında kol pozları karşılaştırılır)
	var order := ["diag_down", "diag_up", "cross_x", "overhead_2h", "ground_drag", "sweep_low", "reverse_grip", "twirl", "windmill", "pole_thrust",
		"pole_sweep", "reap", "rake", "whip_crack", "axe_hook", "iai", "uppercut_2h", "slam_2h", "stab_heavy", "helicopter",
		"pole_thrust_lo", "pole_rise", "dual_l", "dual_r", "whip_side"]
	var items := ["alp_kilici", "alp_kilici", "alp_kilici", "ulu_kilic", "ulu_kilic", "ayaz_kilici", "yatagan", "ay_palasi", "gurz", "kargi",
		"teber", "erlik_tirpani", "kurt_pencesi", "kement", "savas_baltasi", "yildirim_kilici", "dag_cekici", "dag_cekici", "kargi", "teber",
		"kargi", "kargi", "ikiz_bicak", "ikiz_bicak", "kement"]
	if f >= 30 and f % 80 == 30 and _lab_i < order.size():
		pl.facing = 1
		pl.debug_swing(order[_lab_i], items[_lab_i])
		_lab_i += 1


func _showcase(delta: float) -> void:
	if lab:
		_lab(delta)
		return
	## --sahne: düz arenada dövüş gösterisi. Silahlar sırayla değişir, düşmanlar düzenli gelir;
	## efekt ve animasyonları çekim için güvenilir biçimde tekrar eder.
	if hud.mode != "play" or level == null or level.player == null:
		if hud.mode == "tilsim":
			_apply_scroll(0)
		return
	for a in _auto_pressed:
		Input.action_release(a)
	_auto_pressed.clear()
	var pl: Player = level.player
	var TSx := float(Level.TS)
	if _sc_step < 0:
		_sc_step = 0
		var tx := 4
		pl.global_position = Vector2(tx * TSx, level.surface_y(tx) * TSx - 2)
		pl.facing = 1
		for e in get_tree().get_nodes_in_group("dusman"):
			e.queue_free()
		Game.camera.reset_smoothing.call_deferred()
	_sc_t += delta
	Game.run["hp"] = 100.0
	pl.inv_t = maxf(pl.inv_t, 0.0)
	var t := _sc_t
	var tx0 := int(pl.global_position.x / TSx)
	# düşman akışı: her 2.6 sn'de sağdan bir kurt; 9. sn'de balbal, 19. sn'de iye
	if int(t * 60.0) % 156 == 30:
		level.spawn_enemy("kara_boru", Vector2((tx0 + 6) * TSx, level.surface_y(tx0 + 6) * TSx - 1))
	if int(t * 60.0) == 9 * 60:
		level.spawn_enemy("balbal", Vector2((tx0 + 6) * TSx, level.surface_y(tx0 + 6) * TSx - 1))
	if int(t * 60.0) == 19 * 60:
		level.spawn_enemy("agac_iyesi", Vector2((tx0 + 6) * TSx, level.surface_y(tx0 + 6) * TSx - 1))
	if int(t * 60.0) == 28 * 60:
		level.spawn_enemy("surale", Vector2((tx0 + 6) * TSx, level.surface_y(tx0 + 6) * TSx - 1))
	if int(t * 60.0) == 36 * 60:
		level.spawn_enemy("arcura", Vector2((tx0 + 6) * TSx, level.surface_y(tx0 + 6) * TSx - 1))
	# silah programı
	var sched := [[0.0, "ulu_kilic"], [7.0, "dag_cekici"], [12.0, "ruh_kilici"], [17.0, "ay_palasi"], [22.0, "yildirim_kilici"], [27.0, "teber"], [32.0, "erlik_tirpani"], [37.0, "gurz"], [42.0, "alp_kilici"], [47.0, "bozgun_kilici"], [52.0, "bori_hanceri"], [56.0, "tulpar_mizragi"]]
	for s in sched:
		if int(t * 60.0) == int(float(s[0]) * 60.0):
			var mat := "demir"
			match String(s[1]):
				"pala":
					mat = "gok_demiri"
				"teber":
					mat = "od_tasi"
				"ayaz_kilici":
					mat = "ayaz"
			Game.run["slots"]["melee"] = ItemGen.roll(s[1], 1, mat, 1)
			if s[1] == "erlik_tirpani":
				Game.run["slots"]["melee"]["affixes"].append({"id": "zehirleme", "v": 100.0})
			if s[1] == "teber":
				Game.run["slots"]["melee"]["affixes"].append({"id": "yanma", "v": 100.0})
			if s[1] == "ayaz_kilici":
				Game.run["slots"]["melee"]["affixes"].append({"id": "dondurma", "v": 60.0})
			FX.text(pl.center() + Vector2(0, -40), Game.run["slots"]["melee"]["name"], Color(1, 0.9, 0.6), 9)
	var sched2 := [[0.0, "od_oklari"], [8.0, "saganak_yayi"], [16.0, "tufan_yayi"], [24.0, "gok_asasi"], [32.0, "akinci_yayi"], [40.0, "turk_yayi"]]
	for s in sched2:
		if int(t * 60.0) == int(float(s[0]) * 60.0):
			Game.run["slots"]["second"] = ItemGen.roll(s[1], 2, "demir", 1)
	var sched3 := [[3.0, "davul_totemi"], [15.0, "ayaz_tilsimi"], [25.0, "yel_tilsimi"], [35.0, "ok_yagmuru"], [45.0, "kartal_cagrisi"]]
	for s in sched3:
		if int(t * 60.0) == int(float(s[0]) * 60.0):
			Game.run["slots"]["g1"] = ItemGen.roll(s[1], 1, "demir", 0)
			pl.cd["g1"] = 0.0
	# saldırı ritmi: gürz basılı tutulur, diğerleri tıklanır; arada yuvarlanma ve yay
	var cur: String = Game.run["slots"]["melee"].get("id", "")
	var f := int(t * 60.0)
	if cur != "":
		# 150 karelik turlar: A zincir (art arda), B bas-bas-bekle-bas (bekleme bitirişi), C basılı tut (ağır saldırı)
		var cyc := (f / 150) % 5
		var ph := f % 150
		if cyc == 0 and ph in [0, 16, 32, 48, 64]:
			_tap("saldiri1")
		elif cyc == 1 and ph in [0, 16, 78]:
			_tap("saldiri1")
		elif cyc == 2 and ph < 70:
			Input.action_press("saldiri1")
			_auto_pressed.append("saldiri1")
		elif cyc == 3:
			# göğe savur -> zıpla -> hava kombosu -> kartal dalışı
			if ph < 4:
				Input.action_press("yukari")
				_auto_pressed.append("yukari")
				if ph == 1:
					_tap("saldiri1")
			if ph == 18:
				_tap("zipla")
			if ph in [24, 36, 48]:
				_tap("saldiri1")
			if ph >= 62 and ph < 70:
				Input.action_press("asagi")
				_auto_pressed.append("asagi")
				if ph == 64:
					_tap("saldiri1")
		elif cyc == 4:
			# yuvarlan -> dönüş kesiği; koş -> akın kesiği; çömel -> diz biçen
			if ph == 0:
				_tap("yuvarlan")
			if ph == 20:
				_tap("saldiri1")
			if ph >= 50 and ph < 95:
				Input.action_press("yuvarlan")
				_auto_pressed.append("yuvarlan")
				Input.action_press("sag" if pl.facing > 0 else "sol")
				_auto_pressed.append("sag" if pl.facing > 0 else "sol")
				if ph == 90:
					_tap("saldiri1")
			if ph >= 110 and ph < 130:
				Input.action_press("asagi")
				_auto_pressed.append("asagi")
				if ph == 114:
					_tap("saldiri1")
	if f % 240 == 200:
		_tap("yuvarlan")
	if f % 300 >= 250 and f % 300 < 290:
		Input.action_press("saldiri2")
		_auto_pressed.append("saldiri2")
	if f % 300 == 200:
		_tap("techizat1")
	if f == 42 * 60 + 30:
		pl.kut = 100.0
		_tap("kut")
	if pl.wolf_t > 0.0:
		if f % 40 == 20:
			_tap("saldiri2")
		if f % 150 == 100:
			_tap("kut")
	# yüzü hep en yakın düşmana dön
	var best: Node = null
	var bd := 9999.0
	for e in get_tree().get_nodes_in_group("dusman"):
		if is_instance_valid(e) and not e.dead:
			var d: float = absf(e.global_position.x - pl.global_position.x)
			if d < bd:
				bd = d
				best = e
	if best and pl.atk.is_empty() and pl.roll_t <= 0.0:
		pl.facing = int(signf(best.global_position.x - pl.global_position.x))
		if bd > 70.0:
			_tap("sag" if pl.facing > 0 else "sol")


var _ekran := ""
var _ekran_t := 0
var _ekran_ikinci := false


func _debug_screen() -> void:
	## --ekran=oyun|tilsim|yuva|duraklat|olum|umay|demirci : arayüz testleri ve ekran görüntüsü için
	## v40: kare sayacı bölüm ve oyuncu hazır olduktan sonra işler (açılışta uzun takılma olursa fizik kareleri 40'ı
	## bölüm kurulmadan geçiyor, ekran hiç kurulmuyordu)
	if level == null or level.player == null:
		return
	_ekran_t += 1
	if _ekran in ["yay", "kilic"] and level and level.player:
		# yay: 45. karede ger, 85. karede bırak; kılıç: 45/70/95. karelerde zincir vuruş
		var pl0: Player = level.player
		for a0 in _auto_pressed:
			Input.action_release(a0)
		_auto_pressed.clear()
		for e in get_tree().get_nodes_in_group("dusman"):
			if e.global_position.distance_to(pl0.global_position) > 60.0:
				e.set_physics_process(false)
		if _ekran_t == 40:
			pl0.facing = 1
			if _ekran == "yay":
				Game.run["slots"]["second"] = ItemGen.roll("turk_yayi", 1, "demir", 1)
			for arg in OS.get_cmdline_user_args():
				if String(arg).begins_with("--silah="):
					Game.run["slots"]["melee"] = ItemGen.roll(String(arg).trim_prefix("--silah="), 1, "demir", 0)
				elif String(arg).begins_with("--ikinci="):
					Game.run["slots"]["second"] = ItemGen.roll(String(arg).trim_prefix("--ikinci="), 2, "demir", 0)
					_ekran_ikinci = true
			pl0.on_equip()
			# vuruş testi: önüne iki durağan düşman koy (--dusman=kimlik ile tür seçilir)
			var ek := "kara_boru"
			for arg in OS.get_cmdline_user_args():
				if String(arg).begins_with("--dusman="):
					ek = String(arg).trim_prefix("--dusman=")
			for i in 2:
				var en := level.spawn_enemy(ek, pl0.global_position + Vector2(34 + i * 26, 0), i == 1)
				if en:
					en.set_physics_process(false)
					en.facing = -1
					en.anim.set_facing(-1)
		if _ekran == "yay":
			if _ekran_t == 45:
				Input.action_press("saldiri2")
			elif _ekran_t == 85:
				Input.action_release("saldiri2")
		elif _ekran_t in [45, 70, 95]:
			_tap("saldiri2" if _ekran_ikinci else "saldiri1")
		return
	if _ekran_t != 40 or level == null or level.player == null:
		return
	var pl: Player = level.player
	if _ekran == "tomar":
		_ekran_tomar(pl)
		return
	Game.run["slots"]["second"] = ItemGen.roll("savas_baltasi", 2, "gumus", 2)
	Game.run["slots"]["g2"] = ItemGen.roll("sifa_muskasi", 1, "tunc", 1)
	Game.run["ongun"] = {"kurt": 3, "kartal": 1, "ayi": 2}
	Game.run["gold"] = 245
	Game.run["kut"] = 37
	pl.kut = 65.0
	var it := ItemGen.roll("dag_cekici", 2, "altin", 3)
	level.drop_item(it, pl.global_position + Vector2(10, -20))
	# v23: biraz ötede ikinci bir silah (yerdeki silahın SnH etiketi ▲ / ▼)
	level.drop_item(ItemGen.roll("ikiz_bicak", 1, "gumus", 1), pl.global_position + Vector2(130, -20))
	level.drop_item(ItemGen.roll("ulu_kilic", 0, "demir", 0), pl.global_position + Vector2(-110, -20))
	match _ekran:
		"tilsim":
			hud.sel = 0
			hud.mode = "tilsim"
			get_tree().paused = true
		"yuva":
			await get_tree().create_timer(0.4).timeout
			var p := level.nearest_item(pl.global_position + Vector2(0, -10))
			if p:
				_on_slot_request(p)
		"duraklat":
			get_tree().paused = true
		"olum":
			_on_died()
		"umay":
			_on_npc("umay")
		"demirci":
			Game.meta["blueprints"] = ["saganak_yayi", "ayaz_kilici"]
			_on_npc("demirci")
		"sanat":   # v27: duraklatmadan savaş sanatları (kart: Ay Hilali)
			Game.meta["sanat_acik"] = ["ay_hilali", "bir_cekis", "demir_durus"]
			get_tree().paused = true
			_open_sanat(false)
			hud.sel = 2
		"ogretmen":   # v27: Alp Ata (Kut bankasıyla öğretme)
			Game.meta["sanat_acik"] = ["ay_hilali"]
			Game.meta["kut_bank"] = maxi(int(Game.meta.get("kut_bank", 0)), 85)
			_on_npc("alp_ata")
			hud.sel = 3
		"sanat_hud":   # v27: HUD halkası, dolu nişan
			Game.run["nisan"] = 340.0
		"alp_ata":   # v27: yurtta Alp Ata (--yurt ile): oyuncu yanına
			for n in level.npcs:
				if n.id == "alp_ata":
					pl.global_position = n.global_position + Vector2(-34, -2)
					pl.facing = 1
					Game.camera.reset_smoothing.call_deferred()
		"baslik":
			hud.mode = "title"
		"ayarlar":
			hud.mode = "title"
			_open_settings()
			hud.sel = 2   # grafik kalitesi; --ayar_sel=<satır> başka satır (v38: en uzun açıklamalı satırın çekimi)
			for arg in OS.get_cmdline_user_args():
				if String(arg).begins_with("--ayar_sel="):
					hud.sel = int(String(arg).trim_prefix("--ayar_sel="))


func _ekran_tomar(pl: Player) -> void:
	## v34 çekim: --ekran=tomar: oyuncunun önüne bir Kut Tomarı (kaidesiyle) konur, yakındaki yaratıklar kalkar.
	## --tomar_oku=<sn> verilirse o kadar sonra tomar oyunun yolundan okunur (_on_scroll -> _apply_scroll; açılış
	## animasyonu), --tomar_stat=0|1|2 seçilen stat (Bozkurt / Kartal / Ayı). --tomar_dx=<birim> tomarın uzaklığı,
	## --tomar_yavas=<k> okurken oyun hızı, --tomar_seri=<mutlak önek>: okununca açılışın 14 karesini (her 0,1 oyun sn)
	## <önek>_<i>.png olarak kaydeder ve çıkar (çekim süresinden bağımsız, belirlenimci).
	var oku := -1.0
	var st := 0
	var dx := 64.0
	var yavas := 1.0
	var seri := ""
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--tomar_seri="):
			seri = String(arg).trim_prefix("--tomar_seri=")
		if String(arg).begins_with("--tomar_yavas="):
			yavas = float(String(arg).trim_prefix("--tomar_yavas="))
		if String(arg).begins_with("--tomar_oku="):
			oku = float(String(arg).trim_prefix("--tomar_oku="))
		elif String(arg).begins_with("--tomar_stat="):
			st = int(String(arg).trim_prefix("--tomar_stat="))
		elif String(arg).begins_with("--tomar_dx="):
			dx = float(String(arg).trim_prefix("--tomar_dx="))
	for e in get_tree().get_nodes_in_group("dusman"):
		if is_instance_valid(e) and e.global_position.distance_to(pl.global_position) < 600.0:
			e.queue_free()
	pl.facing = 1
	var at := pl.global_position + Vector2(dx, -30.0)
	var gy: float = level.ground_y_below(at, 160.0)
	level.drop_scroll(Vector2(at.x, gy if gy > 0.0 else pl.global_position.y))
	var p: Pickup = level.pickups[level.pickups.size() - 1]
	print("[tomar] ekran: oyuncu=%s tomar=%s zemin=%.0f ms=%d" % [str(pl.global_position), str(p.global_position), gy, Time.get_ticks_msec()])
	Game.camera.reset_smoothing()
	if oku >= 0.0:
		await get_tree().create_timer(oku).timeout
		if is_instance_valid(p):
			print("[tomar] okunuyor ms=%d" % Time.get_ticks_msec())
			_on_scroll(p)
			hud.sel = st
			_apply_scroll(st)
			Engine.time_scale = yavas
			if seri != "":
				for i in 14:
					await RenderingServer.frame_post_draw
					var img := get_viewport().get_texture().get_image()
					if get_viewport().use_hdr_2d:
						if img.get_format() != Image.FORMAT_RGBA8 and img.get_format() != Image.FORMAT_RGB8:
							img.convert(Image.FORMAT_RGBA8)
						img.linear_to_srgb()
					img.save_png("%s_%02d.png" % [seri, i])
					await get_tree().create_timer(0.1).timeout
				print("[tomar] seri bitti")
				get_tree().quit()


func _physics_process(delta: float) -> void:
	if Prof.on:
		var t0 := Time.get_ticks_usec()
		_physics_process_ic(delta)
		Prof.ekle(&"bot", t0)
		return
	_physics_process_ic(delta)


func _physics_process_ic(delta: float) -> void:
	if _ekran != "":
		_debug_screen()
		return
	if showcase:
		_showcase(delta)
		return
	if not auto_test:
		return
	match hud.mode:
		"tilsim":
			_apply_scroll(0 if _bot_gercek else randi_range(0, 2))
			return
		"demirci":
			var bps: Array = Game.meta.get("blueprints", [])
			if not bps.is_empty():
				_demirci_ac(bps[0])
			hud.demirci_son = {}
			_start_play()
			return
		"tuccar":
			_start_play()
			return
		"usta":
			# v32 bot: ilk silaha paranın yettiği ilk hizmet (belirlenimci: konak tohumu), sonra yola
			var sl := Usta.silahlar()
			if not sl.is_empty():
				var r := Usta.bot_hizmet(String(sl[0]))
				print("[otomatik] USTA derinlik=%d %s altın=%d" % [int(Game.run.get("depth", 1)), String(r.get("msg", "")), int(Game.run.get("gold", 0))])
				if r.get("ok", false) and level and level.player:
					level.player.on_equip()
			_start_play()
			return
		"sanat":
			_start_play()
			return
		"damga":
			# v44 bot: teklifin ilk Damgası (yuva doluysa en eski silinir), sonra yola
			var tk: Array = Damga.teklif()
			if not tk.is_empty() and not Damga.secildi():
				var et: Array = Damga.etkin()
				var r44 := Damga.al(String(tk[0]), String(et[0]) if et.size() >= Damga.yuva() and not et.is_empty() else "")
				print("[otomatik] DAMGA derinlik=%d %s" % [int(Game.run.get("depth", 1)), String(r44.get("msg", ""))])
			DerinlikUI.damga_sonuc = ""
			_start_play()
			return
		"kodeks", "zafer":
			_start_play()
			return
		"umay":
			Game.umay_buy("can")
			_start_play()
			return
		"ozan":
			_start_play()
			return
		"ad":
			# v42: konakta Ozan'a uğrayan bot ad törenine girebilir (yurtta hiç uğramıyordu)
			if not Adlar.pending().is_empty():
				_ad_toreni()
			else:
				_start_play()
			return
		"sinema":
			return   # v42: hikâye sineması kendi kendine akar
		"harita":
			# v32 bot: rehberin istediği (ya da rastgele bulunmuş) taşı seçer
			var found: Array = level.harita.bulunan() if level and level.harita else []
			var want: int = found.find(level.harita_istek) if level else -1
			level.harita_istek = -1
			# v33: dibinde durulan taştan başka bulunmuş taş yoksa haritayı kapat (eskiden "Zaten bu taşın dibindesin"
			# deyip harita açık kalıyor, bot oyunu durdurulmuş ağaçta bekliyordu: giriş taşının dibinde W)
			var yakin: int = level.tasi_yakin() if level else -1
			var sec: int = want if want >= 0 else randi_range(0, maxi(0, found.size() - 1))
			if not found.is_empty() and int(found[clampi(sec, 0, found.size() - 1)]) == yakin:
				sec = -1
				for j in found.size():
					if int(found[j]) != yakin:
						sec = j
						break
			if found.is_empty() or sec < 0:
				_start_play()
			else:
				_harita_sec(sec)
			return
		"done":
			_next_level()
			return
		"dead":
			_bot_olum += 1
			_bot_report("OLUM")
			if _bot_gercek:
				_depth_forced = false   # v22: ölçüm kipinde aynı derinlikten yeniden başla
			_new_run()
			_start_play()
			_bot_last_hp = float(Game.run["hp"])
			return
	if hud.mode != "play" or level == null or level.player == null:
		return
	for a in _auto_pressed:
		Input.action_release(a)
	_auto_pressed.clear()
	_auto_t += delta
	var t := _auto_t
	var pl: Player = level.player
	if pl.dead:
		return
	if level.konak:
		# v32 konak: düşman yok; sağa koş, her 12 karede 3 kare W bas (Umay Ocağı, Usta, Bezirgân; yüklü makinede tek
		# karelik basış Level._process'e görünmeden bırakılıyordu), takılırsa zıpla. Dövüş / çömelme dizisi burada
		# çalışmaz: saldırı basışı W dokunuşunu bozuyor, bot Usta'nın 60 px'lik penceresini kaçırıyordu.
		Input.action_press("sag")
		if int(t * 60.0) % 12 < 3:
			Input.action_press("etkiles")
			_auto_pressed.append("etkiles")
		if absf(pl.global_position.x - _auto_last_x) < 2.0:
			_auto_stuck += delta
		else:
			_auto_stuck = 0.0
		_auto_last_x = pl.global_position.x
		if _auto_stuck > 1.2 and int(t * 60.0) % 20 == 0:
			_tap("zipla")
		_bot_last_hp = float(Game.run["hp"])
		return
	if _bot_gercek and _bot_fight(pl, t):
		pass   # v22: ölçüm kipinde yakındaki düşmanla dövüşür (aşağıdaki yürüyüş / zıplama dizisi yine işler)
	elif not level.rooms.is_empty() and not level.hub:
		rehber.adim(self, pl, delta)   # v32: dallı bölümde yol bulma, ödül odaları, Kut Taşı ışınlanması
		if level.harita_istek >= 0 and hud.mode == "play" and not get_tree().paused:
			_harita_ac()   # rehber harita ekranından ışınlanmak istedi
		if int(t * 60.0) % 23 == 0 and not rehber.iniyor:
			_tap("saldiri1")
	else:
		Input.action_press("sag")
		if int(t * 60.0) % 23 == 0:
			_tap("saldiri1")
	# v9: koşu (Shift basılı) ve çömelerek saldırı yolları da sınanır
	var f9 := int(t * 60.0) % 700
	# v33: dallı bölümde rehber yürürken rastgele zıplama / yuvarlanma / çömelme dizileri yolu bozuyordu (kuyu kapağından
	# inemiyor, düşüş kenarında geri sekiyordu): yalnızca düz alanlarda (boss arenası) ve ölçüm botunda (--bot_gercek) işler
	var ini: bool = not level.rooms.is_empty() and not level.hub and not _bot_gercek
	if f9 >= 200 and f9 < 330 and not ini:
		Input.action_press("yuvarlan")
		_auto_pressed.append("yuvarlan")
	if f9 >= 420 and f9 < 470 and not ini:
		Input.action_press("asagi")
		_auto_pressed.append("asagi")
		if f9 % 12 == 0:
			_tap("saldiri1")
		if f9 == 450:
			Input.action_press("saldiri2")
			_auto_pressed.append("saldiri2")
	if level.hub and int(t * 60.0) % 45 == 0:
		_tap("etkiles")
	# duvara takıldıysa: çift zıpla + yuvarlan
	if absf(pl.global_position.x - _auto_last_x) < 2.0:
		if _auto_stuck <= 1.2 and _auto_stuck + delta > 1.2:
			_bot_takilma += 1
		_auto_stuck += delta
	else:
		_auto_stuck = 0.0
	if pl.is_on_floor() and pl.wolf_t <= 0.0 and not pl.don_on and pl.grabbed_by == null and pl._head_blocked():
		_bot_alcak += 1
		if _bot_alcak % 30 == 1 and _bot_alcak < 200:
			var tx := int(pl.global_position.x / Level.TS)
			var ty := int(pl.global_position.y / Level.TS)
			var col := ""
			for yy in range(ty - 4, ty + 1):
				for xx in range(tx - 1, tx + 2):
					col += str(level.cell(xx, yy))
				col += "|"
			print("[otomatik] ALCAK x=%.0f y=%.0f karo=%d,%d çevre=%s" % [pl.global_position.x, pl.global_position.y, tx, ty, col])
	if float(pl._haz_last) > _bot_cukur_t:
		_bot_cukur_t = float(pl._haz_last)
		_bot_cukur += 1
	_auto_last_x = pl.global_position.x
	if _auto_stuck > 1.2 and int(t * 60.0) % 20 == 0 and not ini:
		_tap("zipla")
	if _auto_stuck > 1.2 and int(t * 60.0) % 20 == 12 and not ini:
		_tap("yuvarlan")
	if int(t * 60.0) % 97 == 0 and not ini:
		_tap("zipla")
	if int(t * 60.0) % 101 == 50 and not ini:
		_tap("zipla")
	if int(t * 60.0) % 173 == 0 and not ini:
		_tap("yuvarlan")
	if int(t * 60.0) % 211 == 0:
		Input.action_press("saldiri2")
	if int(t * 60.0) % 211 == 40:
		Input.action_release("saldiri2")
	if int(t * 60.0) % 317 == 0:
		_tap("techizat1")
	if int(t * 60.0) % 401 == 0:
		_tap("etkiles")
	if int(t * 60.0) % 599 == 0:
		pl.kut = 100.0
		_tap("kut")
	# v22: alınan hasar sayacı; --bot_gercek kipinde can doldurulmaz (şişe içilir, ölüm sayılır)
	var hp_now := float(Game.run["hp"])
	if hp_now < _bot_last_hp:
		_bot_hasar += _bot_last_hp - hp_now
	if _bot_gercek:
		if int(Game.run["flasks"]) < _bot_fl:
			_bot_sise += 1
		_bot_fl = int(Game.run["flasks"])
		if hp_now < float(Game.run["max_hp"]) * 0.35 and int(Game.run["flasks"]) > 0 and pl.drink_t <= 0.0 and int(t * 60.0) % 10 == 0:
			_tap("sise")
	elif hp_now < 40.0:
		Game.run["hp"] = maxf(100.0, float(Game.run["max_hp"]) * 0.6)
		_bot_dolum += 1
	_bot_last_hp = float(Game.run["hp"])
	if Engine.get_physics_frames() % 300 == 0:
		print("[otomatik] can=%d/%d hasar=%d dolum=%d şişe=%d ölüm=%d" % [int(Game.run["hp"]), int(Game.run["max_hp"]), int(_bot_hasar), _bot_dolum, _bot_sise, _bot_olum])
		print("[otomatik] biyom=%s stil=%s koridor=%d kare=%d t=%.1f ts=%.2f derinlik=%d x=%.0f y=%.0f zemin=%s öldürülen=%d altın=%d kut=%d yuva1=%s yuva2=%s düşman=%d mermi=%d parşömen=%d" % [level.biome.get("id", "?"), level.style, level.carved, Engine.get_physics_frames(), t, Engine.time_scale, int(Game.run["depth"]), pl.global_position.x, pl.global_position.y, str(pl.is_on_floor()), int(Game.run["kills"]), int(Game.run["gold"]), int(Game.run["kut"]), Game.run["slots"]["melee"].get("name", "-"), Game.run["slots"]["second"].get("name", "-"), get_tree().get_nodes_in_group("dusman").size(), level.proj_root.get_child_count(), Game.meta.get("blueprints", []).size()])


var _bot_gercek := OS.get_cmdline_user_args().has("--bot_gercek")
var _bot_hasar := 0.0
var _bot_last_hp := 100.0
var _bot_dolum := 0
var _bot_sise := 0
var _bot_fl := 99
var _bot_tgt: Node = null
var _bot_tgt_hp := 0.0
var _bot_tgt_t := 0.0
var _bot_skip: Dictionary = {}
var _bot_olum := 0
var _bot_takilma := 0      # v25: duvara / engele 1,2 sn'den uzun takılma sayısı
var _bot_alcak := 0        # v25: ayağa kalkılamayan alçak tavan altında geçen kare (yalnızca yuvarlanarak geçilen yer)
var _bot_cukur := 0        # v25: tehlike çukuruna değme sayısı
var _bot_cukur_t := -9.0


func _bot_fight(pl: Player, t: float) -> bool:
	## v22 --bot_gercek: basit dövüşçü. Yakında (130 px) uyanık düşman varsa durur, ona döner, 8 karede bir vurur;
	## hazırlıktaki düşman yakınsa yarı yarıya yuvarlanarak kaçar (orta beceri). true: dövüşüyor.
	var best: Node = null
	var bd := 130.0
	for e in get_tree().get_nodes_in_group("dusman"):
		if not is_instance_valid(e) or e.dead or _bot_skip.has(e.get_instance_id()):
			continue
		var dx: float = absf(e.global_position.x - pl.global_position.x)
		if dx < bd and absf(e.center().y - pl.center().y) < 70.0:
			bd = dx
			best = e
	if best == null:
		return false
	# aynı hedefe 5 sn boyunca hasar veremediyse (uçan, kabukta, ulaşılmaz) onu bırak
	if best != _bot_tgt or float(best.hp) < _bot_tgt_hp - 0.5:
		_bot_tgt = best
		_bot_tgt_hp = float(best.hp)
		_bot_tgt_t = t
	elif t - _bot_tgt_t > 5.0:
		_bot_skip[best.get_instance_id()] = true
		return false
	var f := int(t * 60.0)
	if pl.atk.is_empty() and pl.roll_t <= 0.0:
		pl.facing = int(signf(best.global_position.x - pl.global_position.x)) if absf(best.global_position.x - pl.global_position.x) > 2.0 else pl.facing
	if best.state == "windup" and bd < 90.0 and f % 30 == 0 and randf() < 0.5:
		_tap("yuvarlan")
	elif bd > 46.0:
		_tap("sag" if pl.facing > 0 else "sol")
	if f % 8 == 0:
		_tap("saldiri1")
	return true


func _exit_tree() -> void:
	## v26: bot ölçümü --quit-after ile bitince de son satırları yaz (kritik payı, ölüm, hasar)
	if auto_test and is_instance_valid(level) and not Game.run.is_empty():
		_bot_report("CIKIS")


func _bot_report(tag: String) -> void:
	## v22 bot ölçümü: bölüm sonu / ölüm satırı (denge raporu için)
	print("[otomatik] %s derinlik=%d süre=%.1f öldürülen=%d hasar=%d dolum=%d şişe=%d ölüm=%d can=%d/%d" % [tag, int(Game.run.get("depth", 1)), _auto_t, int(Game.run.get("kills", 0)), int(_bot_hasar), _bot_dolum, _bot_sise, _bot_olum, int(Game.run.get("hp", 0)), int(Game.run.get("max_hp", 0))])
	# v25 harita: takılma, alçak tavan (yalnızca yuvarlanarak geçilen yer) ve tehlike çukuru sayaçları
	print("[otomatik] HARITA derinlik=%d genişlik=%d takılma=%d alçak_tavan_kare=%d çukur_değme=%d düşman_taşınan=%d konmayan=%d" % [int(Game.run.get("depth", 1)), Level.W, _bot_takilma, _bot_alcak, _bot_cukur, int(level.spawn_moved) if level else 0, int(level.spawn_skipped) if level else 0])
	# v32: keşif yüzdesi, bulunan Kut Taşı, ışınlanma, ziyaret edilen ödül odası
	if level and level.harita:
		print("[otomatik] KESIF derinlik=%d keşif=%%%d taşı=%d/%d ışınlanma=%d bozuk=%d ödül_odası=%d/%d" % [int(Game.run.get("depth", 1)), int(round(level.harita.yuzde() * 100.0)), level.harita.bulunan().size(), level.harita.tasi.size(), level.isin_sayi, level.isin_bozuk, rehber.ziyaret.size(), int(level.metrics.get("cikmaz", 0))])
	# v24 altın ekonomisi: bu koşuda toplanan altın (Pickup altin_kazanc) ve bölümdeki tüccar
	var bz_n := 1 if level and level.bezirgan else 0
	print("[otomatik] ALTIN derinlik=%d toplanan=%d kese=%d bezirgan=%d duvar_ok=%s" % [int(Game.run.get("depth", 1)), int(Game.run.get("altin_kazanc", 0)), int(Game.run.get("gold", 0)), bz_n, str(level.bezirgan_ok()) if level else "-"])
	# v23 kritik oranı (Player.krit_say: şans / silah koşulu / kesin)
	var ks: Dictionary = Player.krit_say
	var n := maxi(1, int(ks["isabet"]))
	print("[otomatik] KRIT isabet=%d kritik=%%%.1f (şans %%%.1f, koşul %%%.1f, kesin %%%.1f) tomar K/Ka/A=%d/%d/%d" % [int(ks["isabet"]), 100.0 * float(int(ks["sans"]) + int(ks["kosul"]) + int(ks["kesin"])) / n, 100.0 * float(ks["sans"]) / n, 100.0 * float(ks["kosul"]) / n, 100.0 * float(ks["kesin"]) / n, int(Game.run["ongun"]["kurt"]), int(Game.run["ongun"]["kartal"]), int(Game.run["ongun"]["ayi"])])
	var kes: Array = []
	for kk in ks:
		if String(kk).begins_with("kesin_"):
			kes.append("%s %d" % [String(kk).trim_prefix("kesin_"), int(ks[kk])])
	print("[otomatik] KRIT_KESIN " + ", ".join(kes))


func _tap(a: String) -> void:
	Input.action_press(a)
	_auto_pressed.append(a)
