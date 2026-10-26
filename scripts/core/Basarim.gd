class_name Basarim
extends RefCounted
## v44 Destan Başarıları: 25 başarım (v44 birleştirmesiyle 32: Mühür yolu ve Ata Kurganı'nın küpleri), mürekkep rozet (simge + mühür), açılınca bildirim (DerinlikUI.toast) ve küçük
## ödül: HUD çerçeve rengi (Kodeks > Başarımlar'da seçilir), Ozan dizesi (Ozan'ın sayfalarına eklenir) ya da Kut.
## Koşullar olaylarda denetlenir (olay: oldurme, boss, konak, damga, bitis, kodeks); her koşul kalıcı kayıttan ya da
## koşu verisinden okunur, bu yüzden göçte (meta_hazirla) eski kayıtların hak ettikleri sessizce açılır.
##
## Kalıcı kayıt: Game.meta["basarim"] {id: açılış unix zamanı}, Game.meta["hud_renk"] seçili çerçeve rengi kimliği

## id: [ad, açıklama, simge (InkUI simgesi ya da "d:<hücre>" Damga tamgası), ödül türü, ödül]
const B := {
	"ilk_kan": ["İlk Kan", "İlk düşmanını devir.", "kilic", "soz", "Ozan: «İlk kan yere düştü; destan böyle başlar.»"],
	"yuz_bas": ["Yüz Baş", "Toplam 100 düşman devir.", "kafatasi", "renk", "kizil"],
	"bin_bas": ["Bin Baş", "Toplam 1000 düşman devir.", "kafatasi", "renk", "altin"],
	"kara_boru": ["Sürünün Hanı Düştü", "Kara Börü Han'ı devir.", "kurt", "kut", 20],
	"basat": ["Basat'ın İzinde", "Tepegöz'ü devir.", "nazar", "renk", "firuze"],
	"sahmeran": ["Şahmeran'ın Sırrı", "Şahmeran Ana'yı devir.", "zehir", "renk", "mor"],
	"yelbegen": ["Yel Durdu", "Yelbegen'i devir.", "buz", "renk", "ayaz"],
	"tan": ["Tan Söktü", "Erlik Han'ı devir.", "yildiz", "renk", "tan"],
	"derin5": ["Beşinci Kat", "5. derinliğe in.", "harita", "kut", 15],
	"derin10": ["Dokuz Gecenin Dibi", "10. derinliğe in.", "harita", "soz", "Ozan: «Dokuz gece indin; onuncusunda ışık seni bekliyordu.»"],
	"damga_ilk": ["İlk Tamga", "Bir Damga vur.", "damga", "soz", "Ozan: «Tamgasız boy olmaz; artık senin de bir izin var.»"],
	"damga_uc": ["Üç Tamgalı", "Aynı koşuda üç Damga taşı.", "damga", "kut", 25],
	"damga_uyum": ["Ongun Uyumu", "Uyumlu bir Damgayla 3 tomar oku.", "tilsim", "soz", "Ozan: «Damga ile ongun bir oldu; kurt kendi izini tanıdı.»"],
	"damga_bilge": ["Tamga Bilgesi", "Yirmi Damganın hepsini en az bir kez vur.", "muhur", "renk", "yesim"],
	"kombo": ["Destan Kombosu", "55 vuruşluk DESTAN kombosuna ulaş.", "davul", "soz", "Ozan: «Kopuzum yetişemedi; vuruşların türkü oldu.»"],
	"dag_yaran": ["Dağ Yaran", "Tek vuruşta 300 hasar ver.", "hiz", "kut", 15],
	"seckin": ["Seçkin Avcısı", "Toplam 25 seçkin devir.", "yildiz", "kut", 20],
	"zaaf": ["Zaaf Bilgini", "On yaratığın zaafını öğren.", "nisan", "soz", "Ozan: «Düşmanını bilen, yarı yolu yürümüştür.»"],
	"tam_destan": ["Ozan'ın Tam Destanı", "Bütün yaratıkları ve bossları en az bir kez devir.", "ruh", "renk", "gece"],
	"yel_gibi": ["Yel Gibi", "3. derinliğin konağına 12 dakikadan kısa sürede var.", "zaman", "kut", 15],
	"ciplak": ["Çıplak Yiğit", "Hiç tomar okumadan 3. derinliğe var.", "kalkan", "soz", "Ozan: «Ne ongun ne tılsım; yalnızca yürek.»"],
	"dokunulmaz": ["Dokunulmaz", "Bir bölümü hiç hasar almadan bitir.", "nazar", "kut", 20],
	"sartak": ["Sartak'ın Dostu", "Bir koşuda 500 altın biriktir.", "altin", "kut", 10],
	"ad_sahibi": ["Ad Sahibi", "Ozan'dan üç ayrı ad al.", "ruh", "soz", "Ozan: «Üç adın var; üç destan anlatılır senin için.»"],
	"yari_destan": ["Yarı Destan", "Ozan'ın Destanı'nın yarısını doldur.", "tilsim", "renk", "kemik"],
	# v44 birleştirme: Mühür yolu (MuhurYolu.gd) ve silah küpleri (Kupler.gd)
	"ilk_muhur": ["Zincirden İlk Halka", "Erlik Han'ı yen: Mühür Taşı'na ilk Kut Mührü basılsın.", "muhur", "kut", 25],
	"bes_muhur": ["Beş Mühürlü", "Beşinci Mühürde Erlik Han'ı yen.", "muhur", "renk", "sabah"],
	"gercek_son": ["Zincirin Sonu", "Gerçek sonu gör.", "ruh", "soz", "Ozan: «Zincir koptu, gece döndü; bu destanın sonu sabahtır.»"],
	"emanet": ["Emanetçi", "Bir mühür emanetini eline al.", "kilic", "kut", 20],
	"kup10": ["Küp Dolduran", "Ata Kurganı'nda 10 silah küpü aç.", "sise", "kut", 15],
	"kup30": ["Kurgan Bekçisi", "Ata Kurganı'nda 30 silah küpü aç.", "sise", "kut", 30],
	"kup_hepsi": ["Atalar Kurganı Dolu", "Ata Kurganı'nın bütün silah küplerini aç.", "sise", "renk", "kurgan"],
}
## HUD çerçeve renkleri (ödül): kimlik -> [ad, renk]
const RENK := {
	"": ["Mürekkep (varsayılan)", Color(0.62, 0.47, 0.25)],
	"kizil": ["Kızıl", Color(0.86, 0.24, 0.2)],
	"altin": ["Altın", Color(1.0, 0.8, 0.36)],
	"firuze": ["Firuze", Color(0.36, 0.86, 0.86)],
	"mor": ["Şahmeran moru", Color(0.66, 0.42, 0.95)],
	"ayaz": ["Ayaz", Color(0.7, 0.88, 1.0)],
	"tan": ["Tan", Color(1.0, 0.62, 0.38)],
	"yesim": ["Yeşim", Color(0.5, 0.9, 0.55)],
	"gece": ["Gece mavisi", Color(0.42, 0.52, 1.0)],
	"kemik": ["Kemik", Color(0.95, 0.88, 0.74)],
	"sabah": ["Sabah ışığı", Color(1.0, 0.93, 0.66)],
	"kurgan": ["Kurgan tuncu", Color(0.8, 0.56, 0.32)],
}

static var kuyruk: Array = []   # açılan başarımlar: [id, açılış saati (Game.clock)] (DerinlikUI.toast çizer)
static var sessiz := false       # göçte sessiz açılış (bildirim yok)


static func meta_hazirla() -> void:
	if not (Game.meta.get("basarim") is Dictionary):
		Game.meta["basarim"] = {}
	if not (String(Game.meta.get("hud_renk", "")) in RENK):
		Game.meta["hud_renk"] = ""
	sessiz = true
	olay("goc")
	sessiz = false


static func acik(id: String) -> bool:
	return (Game.meta.get("basarim", {}) as Dictionary).has(id)


static func acik_sayi() -> int:
	var n := 0
	for id in B:
		if acik(id):
			n += 1
	return n


static func hud_renk() -> Color:
	return RENK.get(String(Game.meta.get("hud_renk", "")), RENK[""])[1]


static func renk_acik(rid: String) -> bool:
	if rid == "":
		return true
	for id in B:
		if String(B[id][3]) == "renk" and String(B[id][4]) == rid and acik(id):
			return true
	return false


static func ozan_dizeleri() -> Array:
	## Açılan "soz" ödülleri (Ozan'ın sayfalarında)
	var out: Array = []
	for id in B:
		if String(B[id][3]) == "soz" and acik(id):
			out.append(String(B[id][4]))
	return out


static func ac(id: String) -> bool:
	if acik(id) or not B.has(id):
		return false
	var b: Dictionary = Game.meta.get("basarim", {})
	b[id] = int(Time.get_unix_time_from_system())
	Game.meta["basarim"] = b
	match String(B[id][3]):
		"kut":
			Game.meta["kut_bank"] = int(Game.meta.get("kut_bank", 0)) + int(B[id][4])
	if not sessiz:
		kuyruk.append([id, Game.clock()])
		Ses.play("destan", -3.0)
	Game.save_meta()
	return true


static func olay(_ad: String, _v := {}) -> void:
	## Olayda bütün koşullar denetlenir (ucuz: kayıttan okur)
	var R: Dictionary = Game.run
	var oz: Dictionary = R.get("oz", {}) if R.get("oz") is Dictionary else {}
	var top := Kodeks.toplam_oldurme()
	if top >= 1:
		ac("ilk_kan")
	if top >= 100:
		ac("yuz_bas")
	if top >= 1000:
		ac("bin_bas")
	if Kodeks.oldurme("kara_boru_han") > 0:
		ac("kara_boru")
	if Kodeks.oldurme("tepegoz") > 0:
		ac("basat")
	if Kodeks.oldurme("sahmeran_ana") > 0:
		ac("sahmeran")
	if Kodeks.oldurme("yelbegen") > 0:
		ac("yelbegen")
	if Kodeks.oldurme("erlik_han") > 0 or bool(Game.meta.get("son_izlendi", false)):
		ac("tan")
	var bd := maxi(int(Game.meta.get("best_depth", 1)), int(R.get("depth", 1)))
	if bd >= 5:
		ac("derin5")
	if bd >= 10:
		ac("derin10")
	var kd: Dictionary = Game.meta.get("kodeks", {}).get("d", {}) if Game.meta.get("kodeks") is Dictionary else {}
	if not kd.is_empty():
		ac("damga_ilk")
	var dm: Array = R.get("damga", [])
	if dm.size() >= 3:
		ac("damga_uc")
	for id in dm:
		if Damga.uyum(id) and int(R.get("ongun", {}).get(String(Damga.D[id][2]), 0)) >= 3:
			ac("damga_uyum")
	var hepsi := true
	for id in Damga.D:
		if int(kd.get(id, 0)) <= 0:
			hepsi = false
			break
	if hepsi:
		ac("damga_bilge")
	if int(oz.get("kombo", 0)) >= 55:
		ac("kombo")
	if float(oz.get("en_iyi", 0.0)) >= 300.0:
		ac("dag_yaran")
	if int(Game.meta.get("kodeks", {}).get("seckin", 0)) >= 25:
		ac("seckin")
	if (_ad != "oldurme" or top % 5 == 0) and Kodeks.zaaf_sayi() >= 10:
		ac("zaaf")
	if _ad in ["kodeks", "boss", "goc", "bitis"]:
		var tum := true
		for id in Kodeks.yaratiklar():
			if Kodeks.oldurme(id) <= 0:
				tum = false
				break
		if tum:
			ac("tam_destan")
		if Kodeks.tamamlanma() >= 0.5:
			ac("yari_destan")
	if _ad == "konak" and not R.is_empty():
		var d := int(R.get("depth", 1))
		if d >= 3 and float(R.get("time", 0.0)) < 720.0:
			ac("yel_gibi")
		if d >= 3 and int(R.get("scrolls", 0)) == 0:
			ac("ciplak")
		if bool(_v.get("hasarsiz", false)):
			ac("dokunulmaz")
	if int(R.get("gold", 0)) >= 500:
		ac("sartak")
	if (Game.meta.get("adlar", {}) as Dictionary).size() >= 3:
		ac("ad_sahibi")
	# v44 birleştirme: Mühür yolu ve silah küpleri (kayıttan; öldürme olayında denetlenmez)
	if _ad in ["bitis", "goc", "kodeks", "kup", "emanet"]:
		if Zorluk.muhur_acik() >= 1 or MuhurYolu.zafer_var(0):
			ac("ilk_muhur")
		if MuhurYolu.zafer_var(MuhurYolu.EN_COK):
			ac("bes_muhur")
		if bool(Game.meta.get("gercek_son", false)):
			ac("gercek_son")
		if not (Game.meta.get("muhur_emanet_bulunan", []) as Array).is_empty():
			ac("emanet")
		var kn := Kupler.acilan()
		if kn >= 10:
			ac("kup10")
		if kn >= 30:
			ac("kup30")
		if kn >= Kupler.toplam():
			ac("kup_hepsi")
