class_name Hikaye
extends RefCounted
## v42 Güneş Ana hikâyesi: ilerleme ve satır seçimi (veri data/story.json, anlatı docs/HIKAYE.md).
##
## Erlik, tan töreni gecesi Gün Ana'nın beş ışık örgüsünü kesti; Gün Ana'yı dokuz gecenin zinciriyle Tamu'ya bağladı.
## Her boss bir örgü taşır (Al / Ak / Gök / Sarı / Altın). Örgü alınınca (GunParcasi.gd) kalıcı ilerleme Game.meta'ya
## yazılır; dünya bundan sonra her yerde bir tık daha sıcak (grade_v2 "safak", yurtta Ulu Kayın'ın altın yaprakları).
## Erlik'in örgüsüyle son sinema (Sinema.gd "son") ve jenerik oynar; sonra dünya "tan sökmüş" kalır (yurt sabah ışığında).
##
## Kalıcı kayıt alanları (Game.meta; eski kayıtlarda yoksa meta_hazirla varsayılanla kurar):
##   gun_parca: [boss kimliği...]   alınan örgüler (sıra: alınış)
##   gorumler: [kimlik...]          görülen görümler ("biyom:<id>", "oda:<biyom>:<i>", "orgu:<boss>")
##   giris_izlendi: bool             açılış sineması bir kez kendiliğinden oynar (sonra Ozan'dan)
##   son_izlendi: bool               son sinema + jenerik görüldü (tan söktü)
##   hikaye_surum: 42

const ORGU_SIRA := ["kara_boru_han", "tepegoz", "sahmeran", "yelbegen", "erlik_han"]
const SURUM := 42


static func meta_hazirla() -> void:
	## Kayıt göçü: v42 öncesi kayıtlarda alanlar yok; türleri bozuk gelirse (elle düzenlenmiş kayıt) onarılır
	var m: Dictionary = Game.meta
	if not (m.get("gun_parca") is Array):
		m["gun_parca"] = []
	if not (m.get("gorumler") is Array):
		m["gorumler"] = []
	m["giris_izlendi"] = bool(m.get("giris_izlendi", false))
	m["son_izlendi"] = bool(m.get("son_izlendi", false))
	# yalnızca bilinen boss kimlikleri, tekrarsız
	var temiz: Array = []
	for b in m["gun_parca"]:
		if String(b) in ORGU_SIRA and not (String(b) in temiz):
			temiz.append(String(b))
	m["gun_parca"] = temiz
	m["hikaye_surum"] = SURUM


static func _s() -> Dictionary:
	return Data.story


# ------------------------------------------------------------------ ilerleme
static func parca_sayi() -> int:
	return (Game.meta.get("gun_parca", []) as Array).size()


static func parca_var(bid: String) -> bool:
	return bid in Game.meta.get("gun_parca", [])


static func parca_al(bid: String) -> bool:
	## Örgüyü kalıcı kayda yaz; true: ilk kez alındı
	if parca_var(bid) or not (bid in ORGU_SIRA):
		return false
	var a: Array = Game.meta.get("gun_parca", [])
	a.append(bid)
	Game.meta["gun_parca"] = a
	Game.save_meta()
	return true


static func safak() -> bool:
	## Son izlendi: dünya tan sökmüş
	return bool(Game.meta.get("son_izlendi", false))


static func safak_k() -> float:
	## Ekran derecesine (grade_v2 "safak") ufuk sıcaklığı: her örgü 0,11; tan söktükten sonra 0,7 (yurt 1,0 ayrıca)
	if safak():
		return 0.7
	return 0.11 * float(parca_sayi())


static func asama() -> int:
	return clampi(parca_sayi(), 0, 5)


static func gorum_goruldu(id: String) -> bool:
	return id in Game.meta.get("gorumler", [])


static func gorum_isaretle(id: String) -> void:
	var a: Array = Game.meta.get("gorumler", [])
	if id in a:
		return
	a.append(id)
	Game.meta["gorumler"] = a
	Game.save_meta()


# ------------------------------------------------------------------ satırlar
static func bolum(biome_id: String) -> Dictionary:
	return _s().get("bolumler", {}).get(biome_id, {})


static func orgu(bid: String) -> Dictionary:
	return _s().get("orguler", {}).get(bid, {})


static func orgu_renk(bid: String) -> Color:
	var c: Array = orgu(bid).get("renk", [1.0, 0.8, 0.4])
	return Color(float(c[0]), float(c[1]), float(c[2]))


static func gorum_satiri(biome_id: String) -> String:
	if safak():
		return String(_s().get("gorumler", {}).get("safak", ""))
	return String(_s().get("gorumler", {}).get(biome_id, ""))


static func oda_satiri(biome_id: String, i: int) -> String:
	var a: Array = _s().get("oda", {}).get(biome_id, [])
	return "" if a.is_empty() else String(a[posmod(i, a.size())])


static func boss_soz(bid: String, ne: String) -> String:
	return String(_s().get("boss", {}).get(bid, {}).get(ne, ""))


static func boss_ad(bid: String) -> String:
	return String(_s().get("boss", {}).get(bid, {}).get("ad", bid))


static func lore(biome_id: String, i: int) -> String:
	var a: Array = _s().get("lore", {}).get(biome_id, [])
	return "" if a.is_empty() else String(a[posmod(i, a.size())])


static func _sec(a: Array, salt: int) -> String:
	return "" if a.is_empty() else String(a[posmod(salt, a.size())])


static func soz(npc_id: String, salt := 0, konak := false) -> String:
	## NPC'nin başının üstündeki kısa söz: tan söktüyse "safak", yoksa alınan örgü sayısına göre "asama"; konakta bazen
	## kervan sözü
	var d: Dictionary = _s().get("npcs", {}).get(npc_id, {})
	if d.is_empty():
		return ""
	if safak() and d.has("safak"):
		return _sec(d["safak"], salt)
	if konak and d.has("konak") and salt % 3 == 2:
		return _sec(d["konak"], salt)
	var asm: Array = d.get("asama", [])
	if asm.size() > asama():
		return _sec(asm[asama()], salt)
	return _sec(d.get("repeat", []), salt)


static func olum_satiri() -> String:
	var salt := int(Game.meta.get("runs", 0))
	# v43: bu biyomdaki ilk ölüm: Gün Ana'nın biyoma özgü sözü (Main._on_died işaretler)
	var ilk := String(Game.run.get("olum_ilk", ""))
	if ilk != "":
		var ol: Dictionary = _s().get("olay", {}).get("olum", {})
		if ol.has(ilk):
			return "Gün Ana: «%s»" % String(ol[ilk])
	if safak():
		return _sec(_s().get("olum_safak", []), salt)
	var o: Array = _s().get("olum", [])
	if o.size() > asama():
		return _sec(o[asama()], salt)
	return _sec(_s().get("death_lines", []), salt)


static func olum_isaretle(biyom: String) -> void:
	## v43: biyomdaki ilk ölüm (kalıcı "olum_biyom"); bu koşunun ölüm ekranı Gün Ana'nın biyom sözünü gösterir
	var a: Array = Game.meta.get("olum_biyom", []) if Game.meta.get("olum_biyom") is Array else []
	if biyom == "" or biyom in a:
		return
	a.append(biyom)
	Game.meta["olum_biyom"] = a
	Game.run["olum_ilk"] = biyom
	Game.save_meta()


static func ozan_sayfalari() -> Array:
	## Ozan'ın destan özeti (sayfa = birkaç satır): şimdiye dek açılan bölümler (en derin derinliğe göre), alınan
	## örgüler ve son sayfa: Ozan'ın ilerlemeye göre sözü
	var out: Array = []
	var best := int(Game.meta.get("best_depth", 1))
	var bl: Array = []
	for b in Data.world["biomes"]:
		if not b.get("impl", false):
			continue
		var r: Array = b.get("depths", [0, 0])
		if best >= int(r[0]):
			var c := bolum(String(b["id"]))
			if not c.is_empty():
				bl.append(c)
	if bl.is_empty():
		bl.append(bolum("otuken"))
	for c in bl:
		out.append(["%s · %s" % [String(c.get("no", "")), String(c.get("ad", ""))], "«%s»" % String(c.get("epigraf", "")), String(c.get("ogrenilen", ""))])
	var al: Array = []
	for bid in ORGU_SIRA:
		if parca_var(bid):
			al.append(String(orgu(bid).get("ad", bid)))
	var son := soz("ozan", int(Game.meta.get("runs", 0)))
	out.append(["Gün Ana'nın örgüleri", ("Dönenler: %s." % ", ".join(al)) if not al.is_empty() else "Henüz hiçbir örgü dönmedi.", "«%s»" % son])
	return out
