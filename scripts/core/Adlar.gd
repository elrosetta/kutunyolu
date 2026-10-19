class_name Adlar
extends RefCounted
## Ad Koyma Töreni (Dede Korkut geleneği): yiğit, bir destan gösterince adını alır.
## Koşu sırasında yapılan destan "bekleyen" olarak tutulur; yurtta Ozan Bilge Kopuz'a anlatılınca ad konur,
## ad o koşu boyunca bir güç verir ve Ad Defteri'ne (meta) kalıcı olarak yazılır. Yurda varmadan ölürsen destan unutulur.

const ADLAR := {
	"basat": ["Basat", "Tepegöz'ü devirdi", "Boslara +%25 hasar"],
	"bogac": ["Boğaç", "Bir seçkini tam canla devirdi", "Seçkinlere +%30 hasar"],
	"deli_dumrul": ["Deli Dumrul", "Can %15'in altındayken 5 düşman kesti", "Her bölümde bir kez ölümden 1 canla döner"],
	"bamsi_beyrek": ["Bamsı Beyrek", "Bir bölümde yayla 10 düşman kesti", "Oklar +%25 hasar, +1 delme"],
	"kanturali": ["Kanturalı", "DESTAN kombosuna ulaştı", "Kombo süresi +%50"],
	"salur_kazan": ["Salur Kazan", "Bir bölümde 40 düşman kesti", "+1 şifa şişesi"],
	"segrek": ["Segrek", "Tek savuruşta 3 düşman kesti", "Kritik şansı +%10"],
	"kam_ata": ["Kam Ata", "Don kılığında 30 saniye savaştı", "Don kılığında +%25 hasar"],
	"kopuzcu": ["Kopuzcu", "12 kez art arda usulde vurdu", "Usul penceresi geniş, usul hasarı +%10"],
	"donen": ["Dönen", "Üç kez don değiştirdi", "Don süresi +%50"],
	"alp_er_tunga": ["Alp Er Tunga", "Erlik Han'ı devirdi", "Tüm hasar +%15"],
}


static func earned(id: String) -> bool:
	return Game.run.has("adlar") and id in Game.run["adlar"]


static func pending() -> Array:
	return Game.run.get("destan", [])


static func stat(key: String) -> float:
	return float(Game.run.get("dstat", {}).get(key, 0.0))


static func add_stat(key: String, v := 1.0) -> float:
	var d: Dictionary = Game.run.get("dstat", {})
	d[key] = float(d.get(key, 0.0)) + v
	Game.run["dstat"] = d
	return float(d[key])


static func set_stat(key: String, v: float) -> void:
	var d: Dictionary = Game.run.get("dstat", {})
	d[key] = v
	Game.run["dstat"] = d


static func deed(id: String, at := Vector2.INF) -> void:
	## Destan gösterildi: bir kez kaydedilir; ad yurtta Ozan'a anlatılınca konur.
	if Game.run.is_empty() or earned(id) or id in pending() or not ADLAR.has(id):
		return
	var p: Array = pending()
	p.append(id)
	Game.run["destan"] = p
	Ses.play("destan", -2.0)
	if at != Vector2.INF:
		FX.text(at + Vector2(0, -64), "DESTAN!", Color(1.0, 0.85, 0.45), 12)
		FX.text(at + Vector2(0, -50), String(ADLAR[id][1]), Color(1.0, 0.95, 0.8), 8)
		FX.ring(at, 46, Color(1.0, 0.85, 0.45), 0.5)
		FX.burst(at, Color(1.0, 0.85, 0.45), 18, 90, 0.6, 0.2, -60, true)
	var main: Node = FX.level.get_parent() if FX.level else null
	if main and main.get("hud"):
		main.hud.flash_msg = "Destan: %s. Yurtta Ozan'a anlat, adın konsun." % String(ADLAR[id][1])
		main.hud.flash_t = 4.0


static func grant(id: String) -> void:
	## Ozan adı koydu: koşu boyunca güç + Ad Defteri
	var a: Array = Game.run.get("adlar", [])
	if id in a:
		return
	a.append(id)
	Game.run["adlar"] = a
	var p: Array = pending()
	p.erase(id)
	Game.run["destan"] = p
	var book: Dictionary = Game.meta.get("adlar", {})
	book[id] = int(book.get(id, 0)) + 1
	Game.meta["adlar"] = book
	Game.save_meta()
	if id == "salur_kazan":
		Game.run["max_flasks"] = int(Game.run["max_flasks"]) + 1
		Game.run["flasks"] = int(Game.run["flasks"]) + 1


static func title() -> String:
	## Oyuncunun son kazandığı ad (arayüzde "Bengü «Basat»")
	var a: Array = Game.run.get("adlar", [])
	return "" if a.is_empty() else String(ADLAR[a[-1]][0])
