class_name Sinav
extends RefCounted
## v42 bölüm sınavları (Dead Cells'in zamanlı kapıları / hasarsız ödülleri esinli): her bölümde üç mühür. Kazanılan
## mührün otağı bölüm sonundaki Otağ Yeri'nde (OtagYeri, Otag) açılır; üçü birden kazanılırsa Han Otağı da açılır.
##   cabuk       Çabuk: Otağ Yeri'ne (Kut Kapısı'nın önü) `par` saniyede var (OtagYeri.par_sure: yol x 2 + oda x 5 + ...).
##   dokunulmaz  Dokunulmaz: Otağ Yeri'ne dek CANINDAN hiç düşmesin. Kalkanla tutulan / savuşturulan darbe, dokunulmazlık
##               karelerinde sıyıran vuruş sayılmaz; şişe ve şifa serbest (can artışı bozmaz). Tuzak, düşüş, lanet sayılır.
##   avci        Avcı: tamgalı av: ya bölümdeki bir yaratık türünden N tane ("sürü"), ya seçkin "Av Beyi" (tek). Hedefler
##               başlarının üstünde kızıl av tamgasıyla belli; bölüm bitene dek kazanılabilir (Otağ Yeri'ne varınca da).
## Durum: 0 sürüyor, 1 kazanıldı (altın mühür), -1 kaybedildi (çatlak). Kaybetme cezasızdır: yalnız otağ kapalı kalır.
## Bölümden bölüme hiçbir şey taşınmaz; Game.meta["sinav"] yalnızca istatistik (en iyi süre, kazanılan mühür sayısı).

const TURLER := ["cabuk", "dokunulmaz", "avci"]
const AD := {"cabuk": "Çabuk", "dokunulmaz": "Dokunulmaz", "avci": "Avcı", "han": "Han Otağı"}
const RENK := {"cabuk": Color(1.0, 0.8, 0.36), "dokunulmaz": Color(0.92, 0.95, 1.0), "avci": Color(1.0, 0.42, 0.34), "han": Color(1.0, 0.86, 0.5)}
const AV_SILAH := ["bow", "throw", "thrust"]   # Avcı otağının silahı: av silahları (yay, atılan, mızrak)

var level: Node
var par := 120.0
var yol_sn := 0.0
var durum := {"cabuk": 0, "dokunulmaz": 0, "avci": 0}
var vardi := false          # Otağ Yeri'ne varıldı
var var_sure := -1.0        # varış anındaki bölüm süresi
var av_mod := "suru"        # suru | bey
var av_tur := ""
var av_ad := ""
var av_gerek := 1
var av_say := 0
var olaylar: Array = []     # [tür, "damga" | "catlak", Game.clock()] (arayüz canlandırması)
var _son_hp := -1.0
var _av_t := 0.0


func kur(lv: Node, rng: RandomNumberGenerator) -> void:
	level = lv
	var d := int(Game.run.get("depth", 1))
	yol_sn = OtagYeri.yol_suresi(lv.grid, lv.W, lv.H, lv.spawn_cell, lv.exit_cell)
	par = OtagYeri.par_sure(yol_sn if yol_sn > 0.0 else 24.0, lv.main_rooms().size(), d)
	_son_hp = float(Game.run.get("hp", 0.0))
	_av_sec(rng)


func _av_sec(rng: RandomNumberGenerator) -> void:
	## Av hedefi: bölümün yaratıklarından (uçan / seçkin olmayan, girişe uzak). %45 Av Beyi: yolun ikinci yarısındaki bir
	## yaratık aynı türden SEÇKİN bir avla değişir; yoksa en kalabalık tür (en az 4) "sürü" olur: N = %60'ı (3-6).
	var adaylar: Array = []
	var say := {}
	for e in level.actors.get_children():
		if not (e is Enemy) or e.dead or e.is_boss or e.has_meta("yavru"):
			continue
		say[e.kind] = int(say.get(e.kind, 0)) + 1
		if not e.elite and not e.flying and absf(e.global_position.x - level.spawn_cell.x * level.TS) > 30.0 * level.TS:
			adaylar.append(e)
	var en := ""
	for k in say:
		if en == "" or int(say[k]) > int(say[en]):
			en = String(k)
	if (rng.randf() < 0.45 or en == "" or int(say.get(en, 0)) < 4) and not adaylar.is_empty():
		for _deneme in mini(6, adaylar.size()):
			var e0: Enemy = adaylar[rng.randi_range(0, adaylar.size() - 1)]
			adaylar.erase(e0)
			var kind: String = e0.kind
			var yeni: Enemy = level.spawn_enemy(kind, e0.global_position, true, false, true)
			if yeni == null:
				continue
			var tc := Vector2i(int(floor(yeni.position.x / level.TS)), int(floor((yeni.position.y - 4.0) / level.TS)))
			if level._yaratik_yasak(tc.x, tc.y):
				yeni.queue_free()   # seçkin gövdesi Kut Taşı'nın / girişin dibine kaydı
				continue
			e0.queue_free()
			e0.dead = true
			av_mod = "bey"
			av_tur = kind
			av_ad = "Av Beyi: " + String(Data.enemy_def(kind).get("name", kind))
			av_gerek = 1
			isaretle(yeni)
			return
	if en == "":
		durum["avci"] = -1
		return
	av_mod = "suru"
	av_tur = en
	av_gerek = clampi(int(round(float(say[en]) * 0.6)), 3, 6)
	av_gerek = mini(av_gerek, int(say[en]))
	av_ad = "%s x%d" % [String(Data.enemy_def(en).get("name", en)), av_gerek]
	for e in level.actors.get_children():
		if e is Enemy and not e.dead and e.kind == en and not e.is_boss:
			isaretle(e)


func isaretle(e: Enemy) -> void:
	e.set_meta("av", true)
	var m := AvIsaret.new()
	m.e = e
	e.add_child(m)


func olduruldu(e: Enemy) -> void:
	if not e.has_meta("av") or durum["avci"] != 0:
		return
	av_say += 1
	if av_say >= av_gerek:
		kazan("avci")
	else:
		FX.text(e.center() + Vector2(0, -36), "Av %d / %d" % [av_say, av_gerek], RENK["avci"], 8)


func kalan() -> float:
	return par - float(Game.run.get("bolum_sure", 0.0))


func tick(delta: float) -> void:
	if level == null or level.player == null or level.player.dead:
		return
	var hp := float(Game.run.get("hp", 0.0))
	if not vardi and _son_hp >= 0.0 and hp < _son_hp - 0.01 and durum["dokunulmaz"] == 0:
		kaybet("dokunulmaz")
	_son_hp = hp
	if not vardi and durum["cabuk"] == 0 and kalan() <= 0.0:
		kaybet("cabuk")
	if not vardi and level.otag_yerinde():
		vardi = true
		var_sure = float(Game.run.get("bolum_sure", 0.0))
		if durum["cabuk"] == 0:
			kazan("cabuk")
			var rek: Dictionary = Game.meta.get("sinav", {})
			var anahtar := "%s_%d" % [String(Game.run.get("biome", "")), int(Game.run.get("depth", 1))]
			var eb: Dictionary = rek.get("en_iyi", {})
			if not eb.has(anahtar) or var_sure < float(eb[anahtar]):
				eb[anahtar] = snappedf(var_sure, 0.1)
			rek["en_iyi"] = eb
			Game.meta["sinav"] = rek
		if durum["dokunulmaz"] == 0:
			kazan("dokunulmaz")
	# av: kalan tamgalı yaratık yetmiyorsa mühür çatlar (ör. Av Beyi uçuruma düştü)
	_av_t -= delta
	if _av_t <= 0.0 and durum["avci"] == 0:
		_av_t = 0.5
		var canli := 0
		for e in level.actors.get_children():
			if e is Enemy and not e.dead and e.has_meta("av"):
				canli += 1
		if canli < av_gerek - av_say:
			kaybet("avci")


func kazan(k: String) -> void:
	if int(durum.get(k, 0)) != 0:
		return
	durum[k] = 1
	olaylar.append([k, "damga", Game.clock()])
	var rek: Dictionary = Game.meta.get("sinav", {})
	rek["muhur"] = int(rek.get("muhur", 0)) + 1
	Game.meta["sinav"] = rek
	Ses.play("otag_damga", -3.0, 1.0, 0.02)
	if level and level.player:
		FX.text(level.player.center() + Vector2(0, -52), "%s mührü!" % AD[k], RENK[k], 10)
		FX.ring(level.player.center(), 30, RENK[k], 0.4)
	if hepsi():
		olaylar.append(["han", "damga", Game.clock() + 0.6])
		if level and level.player:
			FX.text(level.player.center() + Vector2(0, -70), "Üç mühür: Han Otağı açıldı!", RENK["han"], 11)
	if level and level.has_method("otag_tazele"):
		level.otag_tazele()


func kaybet(k: String) -> void:
	if int(durum.get(k, 0)) != 0:
		return
	durum[k] = -1
	olaylar.append([k, "catlak", Game.clock()])
	Ses.play("otag_catlak", -7.0, 1.0, 0.03)
	if level and level.player:
		FX.text(level.player.center() + Vector2(0, -52), "%s mührü çatladı" % AD[k], Color(0.7, 0.68, 0.66), 8)
	if level and level.has_method("otag_tazele"):
		level.otag_tazele()


func hepsi() -> bool:
	return durum["cabuk"] == 1 and durum["dokunulmaz"] == 1 and durum["avci"] == 1


func acik(k: String) -> bool:
	if k == "han":
		return hepsi()
	return int(durum.get(k, 0)) == 1


func durum_of(k: String) -> int:
	## Han: üçü kazanıldıysa 1, biri çatladıysa -1, yoksa 0
	if k == "han":
		if hepsi():
			return 1
		for t in TURLER:
			if int(durum[t]) == -1:
				return -1
		return 0
	return int(durum.get(k, 0))


func aciklama(k: String) -> String:
	match k:
		"cabuk":
			return "Otağ Yeri'ne %d:%02d içinde var" % [int(par) / 60, int(par) % 60]
		"dokunulmaz":
			return "Otağ Yeri'ne dek can yitirme (kalkan, savuşturma, şişe serbest)"
		"avci":
			return "Tamgalı avı vur: " + av_ad
	return "Üç mührü birden kazan"


# ------------------------------------------------------------------ ödüller
static func odul(k: String, d: int, tier: int, rng: RandomNumberGenerator) -> Dictionary:
	## Otağ sandığı: {altin, kut, items: [eşya], tomar: 0/1, parsomen: id}. Derinlikle ölçeklenir (Pazar.derinlik_k).
	##   cabuk       30 x k altın + 1 eşya (bir kademe üst, nadirlik zarı 3 sütun ileri, en az Nadir)
	##   dokunulmaz  Kut Tomarı + (%35, açılmamış eşya varsa) parşömen
	##   avci        5 + derinlik Kut + bir av silahı (yay / atılan / mızrak; derinliğin kademesi, en az Nadir)
	##   han         Efsanevi eşya (bir kademe üst) + 20 x k altın + 6 Kut
	var kk := Pazar.derinlik_k(d)
	var o := {"altin": 0, "kut": 0, "items": [], "tomar": 0, "parsomen": ""}
	match k:
		"cabuk":
			o["altin"] = int(round(30.0 * kk))
			o["items"].append(_esya(tier + 1, 1, ""))
		"dokunulmaz":
			o["tomar"] = 1
			var locked := ItemGen.locked_implemented()
			if not locked.is_empty() and rng.randf() < 0.35:
				o["parsomen"] = String(locked[rng.randi_range(0, locked.size() - 1)])
		"avci":
			o["kut"] = 5 + d
			o["items"].append(_av_silahi(tier, rng))
		"han":
			o["altin"] = int(round(20.0 * kk))
			o["kut"] = 6
			var it := ItemGen.tuccar_drop(tier + 1, tier + 4, "weapons" if rng.randf() < 0.7 else "")
			o["items"].append(ItemGen.roll(String(it["id"]), tier + 1, "", 3))
	return o


static func _esya(t: int, nadir_en_az: int, cat: String) -> Dictionary:
	var it := ItemGen.tuccar_drop(t, t + 3, cat)
	if int(it.get("rarity", 0)) < nadir_en_az:
		it = ItemGen.roll(String(it["id"]), t, "", nadir_en_az)
	return it


static func _av_silahi(t: int, rng: RandomNumberGenerator) -> Dictionary:
	var pool: Array = []
	for id in ItemGen.unlocked("weapons"):
		var b := Data.find_item(id)
		if String(b.get("kind", "")) in AV_SILAH and t >= int(b.get("min_tier", 0)):
			pool.append(id)
	if pool.is_empty():
		return _esya(t, 1, "weapons")
	var id2: String = pool[rng.randi_range(0, pool.size() - 1)]
	var rw: Array = []
	for r in Data.items["rarities"]:
		rw.append(ItemGen._w_at(r["weight"], clampi(t + 3, 0, 8)))
	var rar := maxi(1, Data.items["rarities"].find(ItemGen._wpick(Data.items["rarities"], rw)))
	return ItemGen.roll(id2, t, "", rar)


static func deger(o: Dictionary, d: int) -> float:
	## Altın karşılığı (beklenen değer ölçümü): altın + eşya Bezirgân fiyatı + Kut Tomarı fiyatı + Kut (tanesi ~2 altın)
	## + parşömen (~Kut Tomarı'nın yarısı)
	var v := float(o.get("altin", 0)) + 2.0 * float(o.get("kut", 0))
	for it in o.get("items", []):
		v += float(Pazar.esya_fiyat(it, d))
	v += float(o.get("tomar", 0)) * float(Pazar.tomar_fiyat(d))
	if String(o.get("parsomen", "")) != "":
		v += 0.5 * float(Pazar.tomar_fiyat(d))
	return v
