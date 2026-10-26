class_name Damga
extends RefCounted
## v44 Damgalar (Dead Cells mutasyonları / Hades lütufları esinli; Türk boy tamgaları): her konakta Bengisu Usta'nın
## Damga Taşı üç tamga sunar, biri seçilir ve koşu boyunca kalır. Her Damga bir oyun tarzı (öldür-koş, okçu nişanı,
## düşük canla ayı, yanık yayma, usul şifası ...) ve bir ongun rengi taşır: o rengin tomarı en önde (ve en az 1) ise
## Damga UYUM içindedir, sayısal etkisi x1,25 (Damga.k). Yuvalar meta ile açılır (1; Kara Börü Han'ı bir kez devirince
## 2; Şahmeran Ana'yı devirince 3). Yuva doluyken yeni Damga birinin yerine geçer. Bengisu taşı altınla yeniden oyar.
##
## Koşu verisi (Game.run):  damga: [id...]  damga_teklif: [id x3]  damga_konak: teklifin derinliği
##   damga_secildi: bu konakta seçildi (derinlik)  damga_oyma: bu konaktaki yeniden oyma sayısı  damga_dirildi: Börü Yası
## Kalıcı (Game.meta): kodeks.d {id: alınma sayısı}, kodeks.dg [görülen id] (Kodeks.gd)
##
## Kancalar (tek satır): Player._deal (hasar_k, vurus_sonra), Player.take_hit (alinan_k, olumcul), Player hız
## (hiz_k), add_kut (kut_k), _drink (sise_k, icti), _parry (savusturma), Level.on_enemy_died (oldurme), Pickup altın
## (altin_k).

## id: [ad, tamga hücresi (assets/ui/ink/damga44.png), ongun ("" renksiz), nadir, etki, üslup, söz]
const D := {
	"kurt_izi": ["Kurt İzi", 0, "kurt", false, "Öldürünce 3 sn koşu hızı +%30 ve hasar +%15.", "öldür, koş, yine öldür",
		"Kurt izini bırakır, sürü izi takip eder."],
	"kartal_gozu": ["Kartal Gözü", 1, "kartal", false, "Uzak silahla kritik vuruş düşmanı nişanlar: o düşmana sıradaki yakın vuruş +%45.", "uzaktan nişanla, yakından bitir",
		"Kartal önce görür, sonra iner."],
	"ayi_postu": ["Ayı Postu", 2, "ayi", false, "Canın %40'ın altındayken alınan hasar -%30.", "dar boğazda direnen",
		"Yaralı ayı daha çetindir."],
	"od_tamgasi": ["Od Tamgası", 3, "kurt", false, "Yanan düşmana +%20 hasar; yanarken ölen düşman ateşi çevresine sıçratır.", "yangın yayan",
		"Ocağı söndürmeyen boyun tamgası."],
	"kam_tamgasi": ["Kam Tamgası", 4, "kartal", false, "Her öldürme savaş sanatının beklemesini 1 sn (seçkinde 4 sn) kısaltır.", "sanat ardına sanat",
		"Davul durmazsa ruh da durmaz."],
	"boru_yasi": ["Börü Yası", 5, "ayi", true, "Koşuda bir kez: ölümcül darbede canının %30'uyla dirilirsin.", "ikinci can",
		"Asena yavrusunu ölüme bırakmaz."],
	"usul_tamgasi": ["Usul Tamgası", 6, "kartal", false, "Usulde (davul vuruşunda) isabet canının %1'ini geri verir (saniyede en çok %3).", "ritimle yaşayan",
		"Kopuzun teli gerildikçe can tazelenir."],
	"tulga": ["Tulga Tamgası", 7, "ayi", false, "Kalkanla savuşturunca 3 sn hasar +%30 ve sıradaki vuruş kesin kritik.", "karşıla, sonra ez",
		"Tulga darbeyi tutar, kılıç cevabı verir."],
	"yel_tamgasi": ["Yel Tamgası", 8, "kurt", false, "Yuvarlandıktan sonraki 1 sn vuruşların +%35 hasar verir.", "kaç ve sok",
		"Yel görünmez, ama kesik bırakır."],
	"kan_tamgasi": ["Kan Tamgası", 9, "kurt", false, "Kanayan düşmana +%20 hasar; kanayan düşmanı öldürünce canının %2'si döner.", "kanatıp beslenen",
		"Kan kanı çağırır."],
	"ayaz_tamgasi": ["Ayaz Tamgası", 10, "kartal", false, "Vuruşlar %10 şansla dondurur; donmuş ya da sersem düşmana +%25 hasar.", "dondur, parçala",
		"Kaf'ın soluğu tamgaya işlenmiş."],
	"ata_kesesi": ["Ata Kesesi", 11, "", false, "Altın taneleri +%40 değerli; seçkinler 4 tane fazla altın bırakır.", "kervanın dostu",
		"Atalar kesesini torununa bırakır."],
	"kut_tamgasi": ["Kut Tamgası", 12, "", false, "Kut gücü %40 hızlı dolar; seçkin öldürmek +25 Kut gücü verir.", "Bozkurt'a koşan",
		"Kut, taşıyanı seçer."],
	"tengri_tamgasi": ["Tengri Tamgası", 13, "kartal", false, "Kritik vuruş yakındaki bir düşmana şimşekle sıçrar (%35 hasar).", "kritik zinciri",
		"Gök gürler, yer titrer."],
	"umay_tamgasi": ["Umay Tamgası", 14, "ayi", false, "Şişeler %40 fazla iyileştirir; içince 2 sn alınan hasar yarıya iner.", "dayanıklı",
		"Umay Ana'nın sütü acıyı dindirir."],
	"suru_tamgasi": ["Sürü Tamgası", 15, "kurt", false, "Yakındaki her düşman hasarına +%6 katar (en çok +%30).", "kalabalıkta coşan",
		"Kurt sürünün ortasında güçlenir."],
	"demir_tamgasi": ["Demir Tamgası", 16, "ayi", false, "Azami can +%20 (alınca o kadar iyileşirsin).", "demir gövde",
		"Ergenekon'un demiri gövdeye işlendi."],
	"erlik_muhru": ["Erlik Halkası", 17, "", true, "Hasar +%40; ama alınan hasar +%25.", "lanetli güç",
		"Karanlığın armağanı bedelsiz değildir."],
	"okcu_tamgasi": ["Okçu Tamgası", 18, "kartal", false, "Uzak silah vuruşları +%25 hasar.", "uzaktan avlayan",
		"Bamsı'nın okunun ucunda."],
	"balbal_tamgasi": ["Balbal Tamgası", 19, "ayi", false, "Seçkin ve bosslara +%15 hasar; onlardan alınan hasar -%15.", "dev avcısı",
		"Taş alplar devlerin karşısında durur."],
}
const UYUM_K := 1.25
const NADIR_AGIRLIK := 0.35
const OYMA_TABAN := 30          # yeniden oyma: 30 x Pazar.derinlik_k, her oymada x1,5
const KURT_SURE := 3.0
const TULGA_SURE := 3.0
const UMAY_SURE := 2.0
const YEL_SURE := 1.0

static var rng := RandomNumberGenerator.new()
static var _kurt_t := -99.0
static var _tulga_t := -99.0
static var _tulga_krit := false
static var _umay_t := -99.0
static var _usul_t := -99.0
static var _usul_n := 0.0
static var tetik: Dictionary = {}   # test / ölçüm: Damga etkisi kaç kez tetiklendi (id -> sayı)


static func ids() -> Array:
	return D.keys()


static func ad(id: String) -> String:
	return String(D[id][0]) if D.has(id) else id


static func renk(id: String) -> Color:
	## Damganın rengi: ongun rengi (renksizler zerdeçal altını; nadirler kızıl mühür)
	if not D.has(id):
		return InkUI.GOLD
	var o := String(D[id][2])
	if id == "erlik_muhru":
		return Color(0.78, 0.42, 1.0)
	if o == "":
		return InkUI.GOLD
	return PixUI.ongun_col(o)


static func etkin() -> Array:
	return Game.run.get("damga", []) if not Game.run.is_empty() else []


static func has(id: String) -> bool:
	return not Game.run.is_empty() and id in Game.run.get("damga", [])


static func _say(id: String) -> void:
	tetik[id] = int(tetik.get(id, 0)) + 1


static func yuva() -> int:
	## Damga yuvası: 1; Kara Börü Han bir kez devrildiyse 2; Şahmeran Ana devrildiyse 3 (eski kayıtlar: örgü / derinlik)
	var n := 1
	var gp: Array = Game.meta.get("gun_parca", [])
	var bd := int(Game.meta.get("best_depth", 1))
	if Kodeks.oldurme("kara_boru_han") > 0 or "kara_boru_han" in gp or bd >= 3:
		n += 1
	if Kodeks.oldurme("sahmeran_ana") > 0 or "sahmeran" in gp or bd >= 7:
		n += 1
	return n


static func yuva_ipucu() -> String:
	var n := yuva()
	if n == 1:
		return "Kara Börü Han'ı devir: ikinci Damga yuvası açılır."
	if n == 2:
		return "Şahmeran Ana'yı devir: üçüncü Damga yuvası açılır."
	return "Bütün Damga yuvaları açık."


static func uyum(id: String) -> bool:
	## Damganın rengindeki tomar en önde (eşitlik dahil) ve en az 1 ise uyum
	if Game.run.is_empty() or not D.has(id):
		return false
	var o := String(D[id][2])
	if o == "":
		return false
	var og: Dictionary = Game.run.get("ongun", {})
	var lv := int(og.get(o, 0))
	if lv <= 0:
		return false
	for k in og:
		if int(og[k]) > lv:
			return false
	return true


static func k(id: String) -> float:
	## Etki çarpanı: uyumda x1,25
	return UYUM_K if uyum(id) else 1.0


# ------------------------------------------------------------------ konak: teklif, seçim, yeniden oyma
static func kosu_basi() -> void:
	_kurt_t = -99.0
	_tulga_t = -99.0
	_tulga_krit = false
	_umay_t = -99.0
	_usul_t = -99.0
	_usul_n = 0.0


static func yeni_konak(seed_v: int) -> void:
	## Konak kurulurken: teklif konak tohumuyla (aynı tohum aynı teklif); bu derinlikte zaten teklif varsa korunur
	if Game.run.is_empty():
		return
	rng.seed = seed_v * 31 + 7
	var d := int(Game.run.get("depth", 1))
	if int(Game.run.get("damga_konak", -1)) != d:
		Game.run["damga_konak"] = d
		Game.run["damga_oyma"] = 0
		Game.run["damga_teklif"] = teklif_cek()


static func teklif_cek(n := 3) -> Array:
	## Sahip olunmayanlardan n Damga; nadirler seyrek; Erlik Halkası ile Börü Yası aynı teklifte olmaz
	var pool: Array = []
	for id in D:
		if not has(id):
			pool.append(id)
	var out: Array = []
	while out.size() < n and not pool.is_empty():
		var tot := 0.0
		for id in pool:
			tot += NADIR_AGIRLIK if bool(D[id][3]) else 1.0
		var r := rng.randf() * tot
		var pick: String = pool[0]
		for id in pool:
			r -= NADIR_AGIRLIK if bool(D[id][3]) else 1.0
			if r <= 0.0:
				pick = id
				break
		pool.erase(pick)
		if bool(D[pick][3]):
			for o in out:
				if bool(D[o][3]):
					pick = ""
					break
		if pick != "":
			out.append(pick)
	for id in out:
		Kodeks.damga_gor(id)
	return out


static func teklif() -> Array:
	return Game.run.get("damga_teklif", []) if not Game.run.is_empty() else []


static func secildi() -> bool:
	## Bu konakta Damga alındı mı (bir konakta bir Damga)
	return not Game.run.is_empty() and int(Game.run.get("damga_secildi", -1)) == int(Game.run.get("depth", 1))


static func oyma_bedel() -> int:
	var n := int(Game.run.get("damga_oyma", 0))
	var c := float(OYMA_TABAN) * Pazar.derinlik_k() * pow(1.5, n)
	return int(round(c / 5.0)) * 5


static func oy() -> Dictionary:
	## Bengisu taşı yeniden oyar: altın düşer, yeni üç Damga. {ok, msg}
	if secildi():
		return {"ok": false, "msg": "Bu konakta Damgan vuruldu; taş soğudu."}
	var c := oyma_bedel()
	var g := int(Game.run.get("gold", 0))
	if g < c:
		return {"ok": false, "msg": "Altının yetmez (%d gerekir, %d var)." % [c, g]}
	Game.run["gold"] = g - c
	Game.run["damga_oyma"] = int(Game.run.get("damga_oyma", 0)) + 1
	Game.run["damga_teklif"] = teklif_cek()
	return {"ok": true, "msg": "Bengisu taşı yeniden oydu (-%d altın)." % c}


static func al(id: String, yerine := "") -> Dictionary:
	## Damgayı vur. Yuva doluysa yerine verilen Damga silinir (yerine boşsa ret). {ok, msg}
	if Game.run.is_empty() or not D.has(id):
		return {"ok": false, "msg": "Böyle bir Damga yok."}
	if has(id):
		return {"ok": false, "msg": "Bu Damga zaten üzerinde."}
	var a: Array = Game.run.get("damga", [])
	if a.size() >= yuva():
		if yerine == "" or not (yerine in a):
			return {"ok": false, "msg": "Yuvalar dolu: hangisinin silineceğini seç."}
		_birak(yerine)
		a = Game.run.get("damga", [])
	a.append(id)
	Game.run["damga"] = a
	Game.run["damga_secildi"] = int(Game.run.get("depth", 1))
	Kodeks.damga_al(id)
	if id == "demir_tamgasi":
		var ek := float(Game.run["max_hp"]) * 0.2
		Game.run["max_hp"] = float(Game.run["max_hp"]) + ek
		Game.run["hp"] = float(Game.run["hp"]) + ek
		Game.run["demir_ek"] = ek
	Basarim.olay("damga")
	return {"ok": true, "msg": "%s vuruldu: %s" % [ad(id), String(D[id][4])]}


static func _birak(id: String) -> void:
	var a: Array = Game.run.get("damga", [])
	a.erase(id)
	Game.run["damga"] = a
	if id == "demir_tamgasi":
		var ek := float(Game.run.get("demir_ek", 0.0))
		Game.run["max_hp"] = maxf(1.0, float(Game.run["max_hp"]) - ek)
		Game.run["hp"] = minf(float(Game.run["hp"]), float(Game.run["max_hp"]))
		Game.run["demir_ek"] = 0.0


# ------------------------------------------------------------------ etkiler (kancalar)
static func hiz_k() -> float:
	## Koşu hızı çarpanı (Kurt İzi)
	if has("kurt_izi") and Game.clock() < _kurt_t:
		return 1.0 + 0.3 * k("kurt_izi")
	return 1.0


static func kut_k() -> float:
	return 1.0 + 0.4 * k("kut_tamgasi") if has("kut_tamgasi") else 1.0


static func sise_k() -> float:
	return 1.0 + 0.4 * k("umay_tamgasi") if has("umay_tamgasi") else 1.0


static func altin_k() -> float:
	return 1.0 + 0.4 * k("ata_kesesi") if has("ata_kesesi") else 1.0


static func icti() -> void:
	if has("umay_tamgasi"):
		_umay_t = Game.clock() + UMAY_SURE
		_say("umay_tamgasi")


static func savusturma(pl: Node) -> void:
	if has("tulga"):
		_tulga_t = Game.clock() + TULGA_SURE
		_tulga_krit = true
		_say("tulga")
		if pl:
			FX.text(pl.center() + Vector2(0, -48), "TULGA!", renk("tulga"), 9)


static func hasar_k(pl: Node, e: Node, opts: Dictionary) -> float:
	## Player._deal: verilen hasar çarpanı (ve bazı vuruş seçenekleri: Tulga kesin kritiği, Ayaz donması)
	var m := 1.0
	if etkin().is_empty():
		return m
	var now := Game.clock()
	var uzak: bool = bool(opts.get("ok", false))
	if has("kurt_izi") and now < _kurt_t:
		m *= 1.0 + 0.15 * k("kurt_izi")
	if has("kartal_gozu") and not uzak and e.has_meta("damga_nisan") and now < float(e.get_meta("damga_nisan")):
		m *= 1.0 + 0.45 * k("kartal_gozu")
		e.remove_meta("damga_nisan")
		_say("kartal_gozu")
		FX.text(e.center() + Vector2(0, -40), "nişan!", renk("kartal_gozu"), 8)
	if has("od_tamgasi") and float(e.get("burn_t")) > 0.0:
		m *= 1.0 + 0.2 * k("od_tamgasi")
	if has("yel_tamgasi") and float(pl.get("rolled_t")) > 2.0 - 0.4 - YEL_SURE:
		m *= 1.0 + 0.35 * k("yel_tamgasi")
		_say("yel_tamgasi")
	if has("kan_tamgasi") and int(e.get("bleed")) > 0:
		m *= 1.0 + 0.2 * k("kan_tamgasi")
	if has("ayaz_tamgasi"):
		if float(e.get("freeze_t")) > 0.0 or float(e.get("stun_t")) > 0.0:
			m *= 1.0 + 0.25 * k("ayaz_tamgasi")
		if rng.randf() < 0.1 * k("ayaz_tamgasi"):
			opts["freeze"] = maxf(float(opts.get("freeze", 0.0)), 0.8)
			_say("ayaz_tamgasi")
	if has("suru_tamgasi") and pl.is_inside_tree():
		var n := 0
		for o in pl.get_tree().get_nodes_in_group("dusman"):
			if is_instance_valid(o) and not o.dead and o.center().distance_squared_to(pl.center()) < 120.0 * 120.0:
				n += 1
				if n >= 5:
					break
		m *= 1.0 + 0.06 * float(n) * k("suru_tamgasi")
	if has("erlik_muhru"):
		m *= 1.4
	if has("okcu_tamgasi") and uzak:
		m *= 1.0 + 0.25 * k("okcu_tamgasi")
	if has("balbal_tamgasi") and (bool(e.get("elite")) or bool(e.get("is_boss"))):
		m *= 1.0 + 0.15 * k("balbal_tamgasi")
	if has("tulga") and now < _tulga_t:
		m *= 1.0 + 0.3 * k("tulga")
		if _tulga_krit:
			_tulga_krit = false
			opts["force_crit"] = true
	return m


static func vurus_sonra(pl: Node, e: Node, it: Dictionary, opts: Dictionary, d: float, killed: bool) -> void:
	## Player._deal: vuruştan sonra (nişan, usul şifası, Tengri şimşeği)
	if etkin().is_empty():
		return
	var crit: bool = bool(opts.get("crit", false))
	if has("kartal_gozu") and crit and bool(opts.get("ok", false)) and not killed:
		e.set_meta("damga_nisan", Game.clock() + 6.0)
		FX.ring(e.center(), 20, renk("kartal_gozu"), 0.3)
	if has("usul_tamgasi") and bool(opts.get("damga_usul", false)):
		var now := Game.clock()
		if now - _usul_t > 1.0:
			_usul_t = now
			_usul_n = 0.0
		var pay := 0.01 * k("usul_tamgasi")
		if _usul_n + pay <= 0.03 * k("usul_tamgasi") + 0.0001:
			_usul_n += pay
			pl.heal(pl.max_hp() * pay)
			_say("usul_tamgasi")
	if has("tengri_tamgasi") and crit and not bool(opts.get("zincir", false)) and pl.has_method("_tengri_chain"):
		pl._tengri_chain(e, d * 0.35 * k("tengri_tamgasi"), it)
		_say("tengri_tamgasi")


static func alinan_k(_pl: Node, from: Node) -> float:
	## Player.take_hit: alınan hasar çarpanı
	var m := 1.0
	if etkin().is_empty():
		return m
	if has("ayi_postu") and float(Game.run["hp"]) < float(Game.run["max_hp"]) * 0.4:
		m *= 1.0 - minf(0.6, 0.3 * k("ayi_postu"))
		_say("ayi_postu")
	if has("umay_tamgasi") and Game.clock() < _umay_t:
		m *= 0.5
	if has("erlik_muhru"):
		m *= 1.25
	if has("balbal_tamgasi") and from != null and is_instance_valid(from) and (bool(from.get("elite")) or bool(from.get("is_boss"))):
		m *= 1.0 - minf(0.4, 0.15 * k("balbal_tamgasi"))
	return m


static func olumcul(pl: Node) -> bool:
	## Player.take_hit: can 0'a indi. Börü Yası koşuda bir kez diriltir (true: ölüm yok)
	if not has("boru_yasi") or bool(Game.run.get("damga_dirildi", false)):
		return false
	Game.run["damga_dirildi"] = true
	Game.run["hp"] = float(Game.run["max_hp"]) * minf(0.6, 0.3 * k("boru_yasi"))
	pl.set("inv_t", 1.6)
	_say("boru_yasi")
	Game.slowmo(0.3, 0.6)
	var c := renk("boru_yasi")
	FX.soul(pl.center(), c, 36)
	FX.ring(pl.center(), 70, c, 0.6)
	FX.flash_light(pl.center(), c, 260.0, 2.2, 0.7)
	FX.text(pl.center() + Vector2(0, -40), "BÖRÜ YASI: ASENA SENİ GERİ ÇAĞIRDI", c, 10)
	Ses.play("destan", -2.0)
	return true


static func oldurme(lv: Node, e: Node) -> void:
	## Level.on_enemy_died: öldürmeye bağlı Damga etkileri
	if etkin().is_empty() or lv == null:
		return
	var pl: Node = lv.get("player")
	var elite: bool = bool(e.get("elite"))
	if has("kurt_izi"):
		_kurt_t = Game.clock() + KURT_SURE
		_say("kurt_izi")
	if has("kam_tamgasi") and pl and pl.get("sanat") != null:
		var s: Object = pl.get("sanat")
		s.set("cd", maxf(0.0, float(s.get("cd")) - (4.0 if elite else 1.0) * k("kam_tamgasi")))
		_say("kam_tamgasi")
	if has("od_tamgasi") and float(e.get("burn_t")) > 0.0:
		var n := 0
		for o in lv.get_tree().get_nodes_in_group("dusman"):
			if o == e or not is_instance_valid(o) or o.dead:
				continue
			if o.center().distance_to(e.center()) < 90.0 * k("od_tamgasi"):
				o.burn_t = maxf(float(o.burn_t), 3.0)
				FX.burst(o.center(), Color(1.0, 0.55, 0.2), 6, 50, 0.4, 0.16, -60, true)
				n += 1
		if n > 0:
			_say("od_tamgasi")
			FX.ring(e.center(), 40, Color(1.0, 0.55, 0.25), 0.35)
	if has("kan_tamgasi") and int(e.get("bleed")) > 0 and pl:
		pl.heal(pl.max_hp() * 0.02 * k("kan_tamgasi"))
		_say("kan_tamgasi")
	if has("ata_kesesi") and elite and lv.has_method("drop_orb"):
		for i in 4:
			lv.drop_orb("gold", e.center())
		_say("ata_kesesi")
	if has("kut_tamgasi") and elite and pl:
		pl.kut = minf(100.0, float(pl.kut) + 25.0 * k("kut_tamgasi"))
		_say("kut_tamgasi")
