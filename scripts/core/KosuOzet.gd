class_name KosuOzet
extends RefCounted
## v44 koşu özeti ve rekorlar: koşu boyunca dövüş istatistikleri (Game.run["oz"]) toplanır; koşu bitince (ölüm ya da
## zafer) bitir() özet sayfasının verisini kurar, kalıcı rekorları (Game.meta["rekor"], Mühür kademesine göre
## Game.meta["rekor_m"]["<kademe>"]) günceller, kırılan rekorları "yeni" listesine yazar ve son koşuları saklar
## (Game.meta["gecmis"], en çok 12). ky-ngp44'ün Game.meta["muhur_kayit"] alanı (varsa) rekor sayfasında okunur.
##
## run.oz: verilen, alinan, en_iyi, en_iyi_silah, oldurme {tür: sayı}, seckin, kombo, silahlar [ad], sinav, otag,
##   olum_neden (tür), olum_yer, bolum_alinan (o bölümde alınan hasar: Dokunulmaz başarımı)

const REKOR := ["derinlik", "oldurme", "kombo", "en_iyi", "verilen", "hizli_zafer"]
const REKOR_AD := {"derinlik": "En derin", "oldurme": "En çok öldürme", "kombo": "En yüksek kombo", "en_iyi": "En ağır vuruş",
	"verilen": "En çok hasar", "hizli_zafer": "En hızlı zafer"}


static func _oz() -> Dictionary:
	if Game.run.is_empty():
		return {}
	if not (Game.run.get("oz") is Dictionary) or not (Game.run["oz"] as Dictionary).has("verilen"):
		Game.run["oz"] = {"verilen": 0.0, "alinan": 0.0, "en_iyi": 0.0, "en_iyi_silah": "", "oldurme": {}, "seckin": 0,
			"kombo": 0, "silahlar": [], "sinav": 0, "otag": 0, "olum_neden": "", "bolum_alinan": 0.0}
	return Game.run["oz"]


static func vurus(d: float, it: Dictionary, killed: bool) -> void:
	var o := _oz()
	if o.is_empty():
		return
	o["verilen"] = float(o["verilen"]) + d
	if d > float(o["en_iyi"]):
		o["en_iyi"] = d
		o["en_iyi_silah"] = String(it.get("name", it.get("name_base", "")))
	if killed:
		Kodeks.silah_oldur(it)


static func hasar_al(d: float, from: Node) -> void:
	var o := _oz()
	if o.is_empty():
		return
	d = minf(d, maxf(0.0, float(Game.run.get("hp", 0.0))))   # öldürücü darbenin artığı sayılmaz
	o["alinan"] = float(o["alinan"]) + d
	o["bolum_alinan"] = float(o.get("bolum_alinan", 0.0)) + d
	var k := ""
	if from != null and is_instance_valid(from):
		k = String(from.get("kind")) if from.get("kind") != null else ""
		if k == "" and from.get("owner") != null and is_instance_valid(from.get("owner")):
			var ow: Node = from.get("owner")
			k = String(ow.get("kind")) if ow.get("kind") != null else ""
	o["son_vuran"] = k if k != "" else "tehlike"


static func oldur(e: Node) -> void:
	var o := _oz()
	if o.is_empty() or e.has_meta("yavru"):
		return
	var od: Dictionary = o["oldurme"]
	var k := String(e.get("kind"))
	od[k] = int(od.get(k, 0)) + 1
	if bool(e.get("elite")):
		o["seckin"] = int(o["seckin"]) + 1


static func kombo(n: int) -> void:
	var o := _oz()
	if not o.is_empty() and n > int(o["kombo"]):
		o["kombo"] = n


static func silah(it: Dictionary) -> void:
	var o := _oz()
	if o.is_empty() or it.is_empty():
		return
	Kodeks.silah_gor(it)
	var nm := String(it.get("name_base", it.get("name", "")))
	var sl: Array = o["silahlar"]
	if nm != "" and not (nm in sl) and String(it.get("cat", "weapons")) == "weapons":
		sl.append(nm)


static func sinav() -> void:
	var o := _oz()
	if not o.is_empty():
		o["sinav"] = int(o["sinav"]) + 1


static func otag() -> void:
	var o := _oz()
	if not o.is_empty():
		o["otag"] = int(o["otag"]) + 1


static func olum(yer := "") -> void:
	var o := _oz()
	if o.is_empty():
		return
	o["olum_neden"] = String(o.get("son_vuran", "tehlike"))
	o["olum_yer"] = yer
	Kodeks.devirdi(String(o["olum_neden"]))


static func deger(k: String, zafer: bool) -> float:
	## Rekor anahtarının bu koşudaki değeri (-1: geçersiz)
	var o := _oz()
	match k:
		"derinlik":
			return float(Game.run.get("depth", 1))
		"oldurme":
			return float(Game.run.get("kills", 0))
		"kombo":
			return float(o.get("kombo", 0))
		"en_iyi":
			return float(o.get("en_iyi", 0.0))
		"verilen":
			return float(o.get("verilen", 0.0))
		"hizli_zafer":
			return float(Game.run.get("time", 0.0)) if zafer else -1.0
	return -1.0


static func bitir(zafer: bool) -> Dictionary:
	## Koşu bitti: özet verisi + rekor güncelleme (bir koşuda bir kez). Dönen: Game.run["ozet"]
	if Game.run.is_empty():
		return {}
	if Game.run.get("ozet") is Dictionary:
		return Game.run["ozet"]
	var o := _oz()
	var rk: Dictionary = Game.meta.get("rekor", {}) if Game.meta.get("rekor") is Dictionary else {}
	var rm_all: Dictionary = Game.meta.get("rekor_m", {}) if Game.meta.get("rekor_m") is Dictionary else {}
	var mk := str(int(Game.run.get("muhur", 0)))
	var rm: Dictionary = rm_all.get(mk, {})
	var yeni: Array = []
	var onceki_var := int(Game.meta.get("gecmis", []).size()) > 0 or not rk.is_empty()
	for k: String in REKOR:
		var v := deger(k, zafer)
		if v < 0.0:
			continue
		var kucuk := k == "hizli_zafer"
		var eski: float = float(rk.get(k, -1.0))
		var iyi := eski < 0.0 or (v < eski if kucuk else v > eski)
		if iyi and v > 0.0:
			rk[k] = v
			if onceki_var and eski >= 0.0:
				yeni.append(k)
			elif onceki_var and eski < 0.0 and kucuk:
				yeni.append(k)
		var em: float = float(rm.get(k, -1.0))
		if v > 0.0 and (em < 0.0 or (v < em if kucuk else v > em)):
			rm[k] = v
	rm_all[mk] = rm
	Game.meta["rekor"] = rk
	Game.meta["rekor_m"] = rm_all
	var oz := {
		"zafer": zafer, "derinlik": int(Game.run.get("depth", 1)), "sure": float(Game.run.get("time", 0.0)),
		"oldurme": int(Game.run.get("kills", 0)), "altin": int(Game.run.get("altin_kazanc", 0)), "kut": int(Game.run.get("kut_kazanc", 0)),
		"verilen": float(o.get("verilen", 0.0)), "alinan": float(o.get("alinan", 0.0)), "en_iyi": float(o.get("en_iyi", 0.0)),
		"en_iyi_silah": String(o.get("en_iyi_silah", "")), "kombo": int(o.get("kombo", 0)), "seckin": int(o.get("seckin", 0)),
		"turler": (o.get("oldurme", {}) as Dictionary).duplicate(), "silahlar": (o.get("silahlar", []) as Array).duplicate(),
		"damga": (Game.run.get("damga", []) as Array).duplicate(), "sinav": int(o.get("sinav", 0)), "otag": int(o.get("otag", 0)),
		"neden": String(o.get("olum_neden", "")), "yer": String(o.get("olum_yer", "")), "muhur": int(Game.run.get("muhur", 0)),
		"tomar": int(Game.run.get("scrolls", 0)), "yeni": yeni,
	}
	Game.run["ozet"] = oz
	var g: Array = Game.meta.get("gecmis", []) if Game.meta.get("gecmis") is Array else []
	g.append({"d": oz["derinlik"], "t": int(oz["sure"]), "k": oz["oldurme"], "z": zafer, "m": oz["muhur"], "dm": oz["damga"]})
	while g.size() > 12:
		g.pop_front()
	Game.meta["gecmis"] = g
	if zafer:
		Game.meta["wins"] = int(Game.meta.get("wins", 0)) + 1
	Basarim.olay("bitis", {"yeni": yeni.size(), "zafer": zafer})
	Game.save_meta()
	return oz


static func sure_txt(t: float) -> String:
	return "%d:%02d" % [int(t) / 60, int(t) % 60]


static func rekor_txt(k: String, v: float) -> String:
	if v < 0.0:
		return "—"
	match k:
		"hizli_zafer":
			return sure_txt(v)
		"derinlik":
			return "%d. derinlik" % int(v)
		"en_iyi", "verilen":
			return ItemGen.fmt(v) if v < 10000.0 else ("%.1f bin" % (v / 1000.0)).replace(".", ",")
	return str(int(v))
