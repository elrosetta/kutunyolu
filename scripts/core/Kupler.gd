class_name Kupler
## v44 Ata Kurganı / Silah Küpleri: yurdun girişindeki koleksiyon duvarının kalıcı verisi (Dead Cells'in kavanozları gibi).
## Her silah ve kalkan için bir küp; durumlar:
##   "kilitli"  : hiç ele geçmedi (içinde kara gölge, çatlak mühür, ad "???", nereden çıktığına dair ipucu)
##   "parsomen" : parşömeni bulundu, Demirci Kam Kuzgun'da açılmayı bekliyor (biçimi soluk görünür)
##   "acik"     : temel eşya, Demirci'de açıldı ya da bir koşuda en az bir kez kuşanıldı (silah ışıyarak süzülür)
## "yeni" listesindeki açık küp kıvılcım + YENİ etiketi taşır (kartı görülene dek); "uyandi" listesine girmeyen yeni küp
## yurtta ilk görüldüğünde uyanış canlandırmasını oynatır (KupGaleri). Açık bir küpte W: o silah BAŞLANGIÇ silahı olur
## (meta.kup.secim: yakın dövüş "melee" ve ikincil "second" yuvası ayrı; "?" = Rastgele küp). Eşikler data/kupler.json.
## Kayıt: Game.meta["kup"] = {kesif, yeni, uyandi, secim}.

const RASTGELE := "?"
static var devre_disi := false   # Main: test / çekim kipinde koşu başı seçimi ve eşik ödülleri uygulanmaz (bot belirlenimci)
static var _veri: Dictionary = {}
static var _liste: Array = []


static func veri() -> Dictionary:
	if _veri.is_empty():
		_veri = Data.load_json("res://data/kupler.json")
	return _veri


static func kup() -> Dictionary:
	var k: Dictionary = Game.meta.get("kup", {})
	for a in ["kesif", "yeni", "uyandi"]:
		if not k.has(a):
			k[a] = []
	if not k.has("secim"):
		k["secim"] = {}
	Game.meta["kup"] = k
	return k


static func sinif(id: String) -> String:
	var b := Data.find_item(id)
	if String(b.get("cat", "")) == "shields":
		return "shield"
	return String(b.get("kind", ""))


static func sinif_adi(id: String) -> String:
	if id == RASTGELE:
		return "Ata'nın Zarı"
	for s in veri().get("siniflar", []):
		if String(s[0]) == sinif(id):
			return String(s[1])
	return ""


static func tur(id: String) -> String:
	## Küp biçimi: a omuzlu ruh kavanozu, b geniş tunç küp, c ince tüp (kup_ink.py)
	if id == RASTGELE:
		return "a"
	for s in veri().get("siniflar", []):
		if String(s[0]) == sinif(id):
			return String(s[2])
	return "a"


static func liste() -> Array:
	## Duvardaki sıra: sınıf sırasıyla (data/kupler.json "siniflar"), sınıf içinde items.json sırası; en sonda Rastgele.
	if not _liste.is_empty():
		return _liste
	var out: Array = []
	for s in veri().get("siniflar", []):
		var cats := ["shields"] if String(s[0]) == "shield" else ["weapons"]
		for c in cats:
			for it in Data.items[c]:
				if it.get("impl", false) and sinif(String(it["id"])) == String(s[0]):
					out.append(String(it["id"]))
	out.append(RASTGELE)
	_liste = out
	return _liste


static func toplam() -> int:
	return liste().size() - 1


static func durum(id: String) -> String:
	if id == RASTGELE:
		return "acik" if esik_var("rastgele") else "kilitli"
	if Game.is_unlocked(id) and (id in Game.BASE_UNLOCKED or id in Game.meta.get("unlocked", []) or id in kup()["kesif"]):
		return "acik"
	if id in Game.meta.get("blueprints", []):
		return "parsomen"
	return "kilitli"


static func acilan() -> int:
	var n := 0
	for id in liste():
		if id != RASTGELE and durum(id) == "acik":
			n += 1
	return n


static func yeni_mi(id: String) -> bool:
	return id in kup()["yeni"]


static func uyandi_mi(id: String) -> bool:
	return id in kup()["uyandi"]


static func kesfet(id: String, once := "") -> bool:
	## Silah ele geçti (koşuda kuşanıldı ya da Demirci açtı): küp açılır. true: küp bu çağrıyla açıldı (YENİ).
	## once: Demirci açılıştan ÖNCEKİ durumu verir (Game.unlock eşyayı zaten açık saydırır)
	if id == "" or not (id in liste()):
		return false
	var k := kup()
	var n0 := acilan()
	if once == "":
		once = durum(id)
	elif once != "acik" and durum(id) == "acik":
		n0 -= 1
	if not (id in k["kesif"]):
		(k["kesif"] as Array).append(id)
	var yeni := once != "acik" and durum(id) == "acik"
	if yeni and not (id in k["yeni"]):
		(k["yeni"] as Array).append(id)
		(k["uyandi"] as Array).erase(id)
	# eşik geçildiyse eşik de "yeni" (Rastgele küp uyanır)
	for e in veri().get("esikler", []):
		if n0 < int(e["n"]) and acilan() >= int(e["n"]) and String(e["id"]) == "rastgele" and not (RASTGELE in k["yeni"]):
			(k["yeni"] as Array).append(RASTGELE)
	Game.save_meta()
	if yeni:
		Basarim.olay("kup")   # v44 birleştirme: küp başarımları
	return yeni


static func goruldu(id: String) -> void:
	var k := kup()
	if id in k["yeni"]:
		(k["yeni"] as Array).erase(id)
		Game.save_meta()


static func uyandir(id: String) -> void:
	var k := kup()
	if not (id in k["uyandi"]):
		(k["uyandi"] as Array).append(id)
		Game.save_meta()


# ------------------------------------------------------------------ eşikler
static func esik_var(eid: String) -> bool:
	var n := acilan()
	for e in veri().get("esikler", []):
		if String(e["id"]) == eid and n >= int(e["n"]):
			return true
	return false


static func esik_toplam(eid: String) -> float:
	var n := acilan()
	var t := 0.0
	for e in veri().get("esikler", []):
		if String(e["id"]) == eid and n >= int(e["n"]):
			t += float(e.get("v", 1.0))
	return t


static func sonraki_esik() -> Dictionary:
	var n := acilan()
	for e in veri().get("esikler", []):
		if n < int(e["n"]):
			return e
	return {}


# ------------------------------------------------------------------ başlangıç silahı
static func yuva(id: String) -> String:
	if id == RASTGELE:
		return "melee"
	var b := Data.find_item(id).duplicate()
	return "second" if Player.is_second_item(b) else "melee"


static func secili(slot: String) -> String:
	return String(kup()["secim"].get(slot, ""))


static func sec(id: String) -> bool:
	## Açık küpü başlangıç silahı yap (yuvasına göre). Aynısı yeniden seçilirse varsayılana döner (seçim kalkar).
	if durum(id) != "acik":
		return false
	var s: Dictionary = kup()["secim"]
	var sl := yuva(id)
	if String(s.get(sl, "")) == id:
		s.erase(sl)
	else:
		s[sl] = id
	Game.save_meta()
	return true


static func rastgele_id(slot: String, rng: RandomNumberGenerator = null) -> String:
	var aday: Array = []
	for id in liste():
		if id != RASTGELE and durum(id) == "acik" and yuva(id) == slot:
			aday.append(id)
	if aday.is_empty():
		return ""
	var i := rng.randi_range(0, aday.size() - 1) if rng else randi() % aday.size()
	return String(aday[i])


static func esya(id: String, ust: bool, rng: RandomNumberGenerator = null) -> Dictionary:
	## Başlangıç eşyası: kademe 0 demir sıradan (Umay "Demirci Dostu": kademe 1 tunç nadir, eskisi gibi);
	## Rastgele küp: açık küplerden rastgele yakın dövüş silahı, nadirlik bir kademe üstün.
	var rar := 1 if ust else 0
	if id == RASTGELE:
		id = rastgele_id("melee", rng)
		rar += 1
		if id == "":
			return {}
	var it := ItemGen.roll(id, 1 if ust else 0, "tunc" if ust else "demir", rar)
	if not it.is_empty() and String(kup()["secim"].get("melee", "")) == RASTGELE and yuva(id) == "melee":
		it["kup_rastgele"] = true
	return it


static func baslangic(run: Dictionary, ust: bool) -> void:
	## Game.new_run çağırır: seçili başlangıç silahları ve eşik ödülleri (test kipinde kapalı)
	if devre_disi or Game.meta.is_empty():
		return
	var s: Dictionary = kup()["secim"]
	for sl in ["melee", "second"]:
		var id := String(s.get(sl, ""))
		if id == "" or durum(id) != "acik":
			continue
		var it := esya(id, ust)
		if not it.is_empty():
			run["slots"][sl] = it
	var g := int(esik_toplam("altin"))
	if g > 0:
		run["gold"] = int(run.get("gold", 0)) + g
	var c := esik_toplam("can")
	if c > 0.0:
		run["max_hp"] = float(run["max_hp"]) * (1.0 + c)
		run["hp"] = float(run["max_hp"])


static func ipucu(id: String) -> String:
	## Kilitli küpün altındaki ipucu: nereden çıktığı
	if id == RASTGELE:
		return "%d küp açılınca uyanır." % int(sonraki_esik_n("rastgele"))
	var b := Data.find_item(id)
	var d := int(b.get("min_tier", 0)) + 1
	if b.has("upgrade_of"):
		var ust := String(Data.find_item(String(b["upgrade_of"])).get("name", ""))
		if durum(id) == "parsomen":
			return "Parşömeni sende: Demirci Kam Kuzgun %d Kut'a açar." % Game.unlock_cost(id)
		return "%s'nın gelişmiş hâli. Parşömeni %d. derinlikten sonra düşer; Demirci açar." % [ust, d]
	if d > 1:
		return "Koşularda %d. derinlikten sonra bulunur. Bir kez kuşan, küpü açılsın." % d
	return "Koşularda bulunur. Bir kez kuşan, küpü açılsın."


static func sonraki_esik_n(eid: String) -> int:
	for e in veri().get("esikler", []):
		if String(e["id"]) == eid:
			return int(e["n"])
	return 0
