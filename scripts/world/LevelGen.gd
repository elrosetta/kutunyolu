class_name LevelGen
extends RefCounted
## v33 bölüm üretimi: küçük Dead Cells mağaraları (v32 oda çizgesinin küçültülmüş, hızlandırılmış hâli).
##
## Bölüm SW x SH = 24 x 13 karolık "kesim"lerden (sektör) bir ızgaradır (stil başına sütun / satır STIL'de; en çok
## 7 x 4 = Level.W x Level.H = 172 x 56 karo; v32: 256 x 90). Her kesime KÜÇÜK bir oda oturur (12-20 karo geniş,
## 6-9 karo hava yüksekliği, basamaklı tavan; kenarlarından 0-6 karo daralır). Yan yana odalar DAR KORİDORLA (4-16 karo
## uzun, 4-5 karo yüksek) bağlanır; üst üste odalar KUYUYLA: üst odanın tabanında 3 karoluk DÜŞÜŞ deliği (ana yol aşağı iniyorsa
## açık, değilse tek yönlü kapak: aşağı + zıpla ile düşülür) ve yanında ince ara duvarla ayrılmış 2 karoluk TIRMANIŞ
## bacası (3 satırda bir tek yönlü basamak; tepesi kapaklı). Aşağı iniş tek düşüştür; geri çıkış birkaç zıplama.
## Oda tabanları düzdür: kesimler arası taban farkı en çok 3 karo (yan kapı eşiği tek zıplama); merdiven / teras
## zinciri, zikzak basamak yok.
##
## Çizge v32'deki gibi: giriş (sol sütun) -> çıkış (sağ sütun) ANA YOL (iniş stillerinde düşerek iner; bir düşüşten
## sonra 1-2 kesim geri dönebilir: yılan); 2-4 DAL (1-2 oda; sonu ÇIKMAZ ödül odası: tomar, hazine, sunak, pazar,
## seçkin bekçisi, zamanlı kapı); komşu odalar arasında DÖNGÜ kapıları; yan yana ana yol odalarının birleşip geniş salon
## olması. Odaların içi türüne göre süslenir (salon, mağara, harabe, çukur, köprü, kuyu (tek yönlü üst güverte), kule,
## teras: tek basamak). Kut Taşları: giriş, ana yolun ortasındaki kavşak, uzak ödül odaları (3-4).
##
## Izgara değerleri: 0 hava, 1 katı, 2 tek yönlü platform, 3 tehlike. v25 kuralları korunur: yürünen her hücrede
## en az BAS_BOSLUGU (3) karo baş boşluğu (_open_headroom), yalnızca yuvarlanarak geçilen yer yok. Erişim modeli
## (_moves: tek / çift zıplama en çok 4 karo yukarı, ±5 sütun; düşüş 15 satır) ile girişten çıkışa yol ve her
## ulaşılan hücreden çıkışa dönüş (traps / fix_traps) denetlenir; geçmeyen taslak yeniden üretilir.
##
## generate(...) döndürür: grid, heights (ana yol odasının tabanı; eski surface_y için), style, chunks (ödül odası
## işaretleri: Level._place_rooms), rooms, doors, path (ana yol kesimleri), spawn / exit (karo), tasi (Kut Taşı
## karoları), zamanli (zamanlı kapı sütunları), kaide (eşya kaidesi karoları), bounds (dolu kesimlerin sıkı kutusu),
## metrics; v34: cepler (gizli cep: çatlak duvar karoları, cep alanı, içerik), kilitli (kilitli kapı sütunu), pencereler
## (parmaklık karoları). Bkz. aşağıdaki v34 sabitleri.

const STYLES := ["orman", "ucurum", "magara", "harabe", "bozkir", "kuyu"]
## v25: yürünen hücrelerin üstünde açık kalması gereken en az karo (ayakta durulan karo dahil; 3 karo = 72 px)
const BAS_BOSLUGU := 3
## Kesim (sektör) boyu: duvarlar dahil; odanın en geniş iç alanı (SW - 4) x 9 karo (yarım ekran kadar)
const SW := 24
const SH := 13
const KENAR := 2
## Kuyu: düşüş bacası 3 + ara duvar 1 + tırmanış bacası 2 sütun
const KUYU_W := 6

## Stil parametreleri: kesim ızgarası (sütun x satır), gök açık mı (üst satır odalarının tavanı yok), ana yolun yönü
## (inis: giriş üstte / çıkış altta; cikis: tersi; serbest), oda türü havuzu, dal sayısı, döngü / birleşme eğilimleri,
## tavan dalgası (mağara tavanı)
const STIL := {
	"orman": {"cols": 7, "rows": 3, "acik": true, "yon": "inis", "kinds": ["salon", "teras", "kopru", "salon", "cukur", "harabe"],
		"dal": [2, 4], "dongu": 0.3, "genis": 0.25, "tavan": 0},
	"ucurum": {"cols": 7, "rows": 4, "acik": true, "yon": "inis", "kinds": ["teras", "kopru", "kule", "cukur", "teras", "salon"],
		"dal": [2, 4], "dongu": 0.25, "genis": 0.15, "tavan": 0},
	"magara": {"cols": 7, "rows": 4, "acik": false, "yon": "inis", "kinds": ["magara", "magara", "kuyu", "cukur", "salon", "magara"],
		"dal": [3, 4], "dongu": 0.35, "genis": 0.2, "tavan": 2},
	"harabe": {"cols": 7, "rows": 4, "acik": false, "yon": "serbest", "kinds": ["harabe", "kule", "salon", "kuyu", "kopru", "harabe"],
		"dal": [2, 4], "dongu": 0.3, "genis": 0.25, "tavan": 1},
	"bozkir": {"cols": 7, "rows": 3, "acik": true, "yon": "serbest", "kinds": ["salon", "teras", "salon", "cukur", "kopru", "harabe"],
		"dal": [2, 3], "dongu": 0.35, "genis": 0.4, "tavan": 0},
	"kuyu": {"cols": 6, "rows": 4, "acik": false, "yon": "inis", "kinds": ["kuyu", "magara", "kule", "cukur", "kopru", "kuyu"],
		"dal": [2, 4], "dongu": 0.3, "genis": 0.1, "tavan": 2},
}

## Oda türüne göre hava yüksekliği (taban - tavan, karo): en az / en çok
const YUK := {"salon": [5, 8], "magara": [6, 9], "harabe": [6, 9], "cukur": [6, 8], "kopru": [6, 8], "teras": [6, 9],
	"kuyu": [8, 9], "kule": [7, 9], "odul": [5, 7], "giris": [6, 8], "tepe": [6, 9], "avlu": [8, 9]}

## Çıkmaz ödülleri (öncelik sırası; pazar istenirse başa eklenir). tomar: Kut Tomarı kaidesi; hazine: üst kademe
## eşya + altın (yükseltilmiş seki); sunak: tanrı lütfu; seckin: seçkin bekçi + eşya; zamanli: bölüm başından 90 sn
## içinde ulaşılırsa açık kalan kapı, ardında üst kademe eşya + altın
const ODULLER := ["tomar", "hazine", "sunak", "seckin", "zamanli", "tomar", "hazine"]
const ZAMANLI_SURE := 90.0

## Eski parça sözlüğü: ödül odası işaretleri (Level._place_rooms, tuccar_testi; "T" hazine kaidesi, "S" sunak, "E" seçkin,
## "M" tomar kaidesi, "P" pazar tezgâhı, "Z" zamanlı kapı ödülü; v34: "L" lanetli sandık, "K" anahtar)
const CHUNKS := {
	"hazine": ["   T   "],
	"sunak": ["   S   "],
	"seckin": ["  E T  "],
	"tomar": ["   M   "],
	"pazar": ["   P   "],
	"lanetli": ["   L   "],
	"zamanli": ["   Z   "],
}

## v34 merak uyandıran bölümler (Dead Cells: görünür ama ulaşılmaz ödüller, gizli duvarlar, anahtarlı kapı, lanetli
## sandık; Kut Kapısı ana yolun ucunda değil):
##   SAPAK_SANS: Kut Kapısı ana yolun son yarısındaki bir kavşaktan (stil yönünde, kapaklı kuyu ya da yan koridor)
##   ayrılan çıkmaz odadadır; görünen koridor sapaktan sonra "uzantı" olarak sürer ve bir ödül odasında (seçkin bekçi /
##   lanetli sandık / hazine) biter.
##   PENCERE: ana yol odasının kapısız yanında demir parmaklıklı pencere; ardındaki ödül odasına yalnızca başka bir
##   kavşaktan dolaşarak (0-1 ara oda) varılır.
##   Gizli cepler (kırık duvar): oda kenarında çatlak mürekkep duvarı (1 sütun, 4 karo); vurulunca açılır, ardında 4 x 4
##   cep (altın / Kut / şifa / eşya / anahtar). Cep üretimde oyulmaz (Level kırınca oyar): erişim denetimi değişmez.
##   KILIT_SANS: yan kapılı bir ödül odasının koridoru kilitli (anahtar bölümde: önce gizli cepte, yoksa başka ödül odasında).
const SAPAK_SANS := 0.95
const PENCERE_EK := 0.4      # ikinci pencere dalı olasılığı
const KILIT_SANS := 0.75
const CEP_SAYI := [2, 3]
const UZANTI_ODUL := ["seckin", "lanetli", "hazine", "lanetli", "seckin"]

## v41 BÖLÜM TÜRLERİ: art arda bölümler aynı mağara / tünel biçiminde olmasın. Tür biyom + derinlik + tohumla seçilir
## (TUR_AGIRLIK; art arda üç bölümün en az biri DÜZ türdür: tur_sec), stilin (STIL) çizge ve oda parametrelerini ezer:
##   acik   "Açık yol / Bozkır akını": 2 satır; ana yol üst satırda soldan sağa DÜZ akar (dikey adım yok; Kut Kapısı
##          sapağı bir mahzene iner: en çok 1 kat). Üst satır göğe açık; açık odalar arası geçitler de açık (tünel değil),
##          taban 1 karoluk basamaklı tepeler / düzlükler ("tepe" türü), yarıklar ve platformlar; dallar mahzenlere iner.
##   kale   "Kale / harabe": 3 satır; ana yol orta satırda uzun salonlar (geniş birleşme sık), avlu arenaları, kuleler;
##          en çok 1 dikey adım; dallar yukarı (dam / kule) ve aşağı (zindan).
##   inis   "İniş" (Kaf'ta tırmanış): v33/v34 düşüş biçimi, yumuşatılmış: 3 satır, en çok 2 dikey adım, kısa kuyular.
##   magara "Mağara ağı": v33/v34 biçimi (biyom satırları: dallar bütün katlara yayılır), ana yol en çok 2 dikey adım
##          (yılan dönüşleriyle), kısa kuyular.
##   eski   v34 üreticisinin aynısı (ölçüm karşılaştırması: --harita_tur=eski / --bolum_turu=eski).
const TURLER := {
	"acik": {"ad": "Açık yol", "duz": true, "rows": 2, "dikey": 1, "yilan": false, "acik": true,
		"kinds": ["tepe", "tepe", "kopru", "tepe", "cukur", "harabe", "tepe"], "dal": [2, 3], "dongu": 0.2, "genis": 0.45, "tavan": 0},
	"kale": {"ad": "Kale / harabe", "duz": true, "rows": 3, "dikey": 1, "yilan": false,
		"kinds": ["harabe", "avlu", "salon", "kule", "harabe", "avlu"], "dal": [2, 4], "dongu": 0.3, "genis": 0.6, "tavan": 0},
	"inis": {"ad": "İniş", "duz": false, "rows": 3, "dikey": 2, "yilan": true},
	"magara": {"ad": "Mağara ağı", "duz": false, "dikey": 2, "yilan": true},
}
## Biyom başına tür ağırlıkları (Ötüken / Bozkır çoğunlukla açık; Kaf sırt + buz mağarası; Şahmeran mağara; Tamu kale +
## iniş). Bilinmeyen biyom: "diger".
const TUR_AGIRLIK := {
	"otuken": {"acik": 5.0, "kale": 1.5, "inis": 2.5, "magara": 1.0},
	"bozkir": {"acik": 6.0, "kale": 3.0, "inis": 1.0},
	"kaf": {"acik": 4.0, "magara": 3.0, "inis": 2.0, "kale": 1.0},
	"sahmeran": {"magara": 5.5, "inis": 2.5, "kale": 2.0},
	"tamu": {"kale": 4.5, "inis": 4.0, "magara": 1.5},
	"diger": {"acik": 3.0, "kale": 2.0, "inis": 3.0, "magara": 2.0},
}
## Türe uygun stiller (biyomun stil havuzunda varsa onlardan biri; yoksa havuzdan rastgele)
const TUR_STIL := {"acik": ["orman", "ucurum", "bozkir"], "kale": ["harabe"], "magara": ["magara", "kuyu"]}
## Gök açabilen biyomlar (açık yol türü yalnız bunlarda; Şahmeran / Tamu yeraltı)
const ACIK_BIYOM := ["otuken", "bozkir", "kaf"]
## Hikâye / anlatı yer tutucusu (v41 kancası): opts.hikaye_odasi = true ise ana yolun ilk yarısındaki bir kavşaktan tek
## kapılı, yaratıksız, ödülsüz "hikaye" odası ayrılır (odul = "hikaye"); her bölümde ayrıca sonuçta "sahne": ana yol
## odalarında en geniş düz taban aralığı ({room, x0, x1, y}: y ayakta durulan satır). Anlatı sahneleri bunlara kurulur.

## Son üretimin giriş / çıkış hücresi (eski imzalı reach_set / traps / _reachable sarmalayıcıları için)
static var _son := {"sx": 5, "sy": 30, "gx": 250, "gy": 30}
## v41: üretilen bölümün türü (_build ve oyma yardımcıları okur; generate her çağrıda kurar)
static var _tur := "eski"
## v41: testler / çekimler için tür zorlaması (opts.tur ve --bolum_turu= yoksa)
static var zorla_tur := ""
## v43 EL YAPIMI ODALAR VE GEÇİTLER (bkz. OdaSablon.gd, GecitGen.gd, docs/TASARIM.md v43): ana yol / dal odalarının çoğu
## data/odalar/*.json şablonlarından (aynalı da) dikilir; her dikey bağlantı biyoma göre bir geçit türüdür (zincir, ip
## merdiven, kök duvarı, kırık merdiven, yar çıkıntıları, rüzgâr bacası, iskele, düşüş deliği); koridor yükseklikleri
## 3-7 ve tavan biçimleri (kemer / kırık), yordamsal odalarda kemer / mağara / kırık çatı / tonoz tavanları, platform
## ritmi. sablon_kapali (ya da --sablon_yok): v42 üreticisi (önce ölçümü); "eski" türde de kapalı.
static var sablon_kapali := false
static var _v43 := true
static var _biyom := "diger"
const SABLON_SANS := 0.88
const SIMGE_SANS := 0.9


static func tur_sec(rng: RandomNumberGenerator, biyom: String, gecmis: Array) -> String:
	## v41: biyom ağırlıklarıyla bölüm türü; son iki bölüm düz değilse (gecmis: önceki türler, en yenisi sonda) yalnız
	## düz türlerden seçilir (art arda üç bölümün en az biri yatay ilerler)
	var ag: Dictionary = TUR_AGIRLIK.get(biyom, TUR_AGIRLIK["diger"])
	var zorla_duz := gecmis.size() >= 2
	for i in range(maxi(0, gecmis.size() - 2), gecmis.size()):
		if bool(TURLER.get(String(gecmis[i]), {}).get("duz", false)) or String(gecmis[i]) == "":
			zorla_duz = false
	var top := 0.0
	var aday: Array = []
	for t in ["acik", "kale", "inis", "magara"]:
		var w := float(ag.get(t, 0.0))
		if t == "acik" and not (biyom in ACIK_BIYOM) and ag == TUR_AGIRLIK["diger"]:
			w = 0.0
		if zorla_duz and not bool(TURLER[t]["duz"]):
			w = 0.0
		if zorla_duz and w <= 0.0 and bool(TURLER[t]["duz"]) and (t != "acik" or biyom in ACIK_BIYOM):
			w = 1.0   # biyomun ağırlığı yoksa da düz tür (Şahmeran: kale)
		if w > 0.0:
			aday.append([t, w])
			top += w
	var r := rng.randf() * top
	for a in aday:
		r -= float(a[1])
		if r <= 0.0:
			return String(a[0])
	return String(aday[aday.size() - 1][0]) if not aday.is_empty() else "inis"


static func generate(rng: RandomNumberGenerator, W: int, H: int, depth: int, allowed: Array = [], opts: Dictionary = {}) -> Dictionary:
	## Döndürür: bkz. dosya başı. opts: pazar (tüccar odası istensin), pazar_kapi (çıkışa yakın), rows / yon ezmesi.
	var pool: Array = allowed if not allowed.is_empty() else STYLES
	# v41 bölüm türü: opts.tur (ya da --bolum_turu=) zorlar; yoksa biyom + geçmişle seçilir
	var tur := String(opts.get("tur", ""))
	if tur == "":
		tur = zorla_tur
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with("--bolum_turu=") and tur == "":
			tur = String(a).trim_prefix("--bolum_turu=")
	if tur != "eski" and not TURLER.has(tur):
		tur = tur_sec(rng, String(opts.get("biyom", "diger")), opts.get("gecmis", []))
	_tur = tur
	_biyom = String(opts.get("biyom", "diger"))
	_v43 = not sablon_kapali and tur != "eski" and not OS.get_cmdline_user_args().has("--sablon_yok")
	var style: String = pool[rng.randi_range(0, pool.size() - 1)]
	if tur == "eski":
		if depth == 1 and rng.randf() < 0.5:
			style = "orman"
	else:
		var uygun: Array = []
		for s in pool:
			if String(s) in TUR_STIL.get(tur, []):
				uygun.append(s)
		if not uygun.is_empty() and (tur != "kale" or rng.randf() < 0.75):
			style = String(uygun[rng.randi_range(0, uygun.size() - 1)])
		opts = opts.duplicate()
		var T: Dictionary = TURLER[tur]
		if T.has("rows"):
			opts["rows"] = mini(int(T["rows"]), int(opts.get("rows", STIL[style]["rows"]))) if tur == "inis" else int(T["rows"])
		if bool(T["duz"]):
			opts["yon"] = "duz"
		elif String(opts.get("yon", STIL[style]["yon"])) == "serbest":
			opts["yon"] = "inis"
	var best: Dictionary = {}
	var best_bad := 999999
	for attempt in 12:
		var r := _build(rng, W, H, style, opts)
		_son = {"sx": r["spawn"].x, "sy": r["spawn"].y, "gx": r["exit"].x, "gy": r["exit"].y}
		r["style"] = style
		r["tur"] = tur
		r["carved"] = 0
		r["trapfix"] = 0
		r["headfix"] = 0
		var ok := false
		for round in 3:
			r["headfix"] = int(r["headfix"]) + _open_headroom(r["grid"], W, H, BAS_BOSLUGU)
			var reach := _reach(_haz_as_air(r["grid"]), W, H, r["heights"])
			if not reach["ok"]:
				break
			r["trapfix"] = int(r["trapfix"]) + fix_traps(r["grid"], W, H, r["heights"])
			r["headfix"] = int(r["headfix"]) + _open_headroom(r["grid"], W, H, BAS_BOSLUGU)
			if _reachable(r["grid"], W, H, r["heights"]) and traps(_haz_as_air(r["grid"]), W, H, r["heights"], r["grid"]).is_empty():
				ok = true
				break
		var bad := 0 if ok else (traps(_haz_as_air(r["grid"]), W, H, r["heights"], r["grid"]).size() + (0 if _reachable(r["grid"], W, H, r["heights"]) else 100000))
		r["attempts"] = attempt + 1
		if ok:
			best = r
			break
		if bad < best_bad:
			best_bad = bad
			best = r
	_son = {"sx": best["spawn"].x, "sy": best["spawn"].y, "gx": best["exit"].x, "gy": best["exit"].y}
	best["metrics"]["ok"] = _reachable(best["grid"], W, H, best["heights"]) and traps(_haz_as_air(best["grid"]), W, H, best["heights"], best["grid"]).is_empty()
	best["metrics"]["attempts"] = int(best.get("attempts", 1))
	best["metrics"]["trapfix"] = int(best.get("trapfix", 0))
	best["metrics"]["tur"] = tur
	return best


static func _idx(x: int, y: int, W: int) -> int:
	return y * W + x


static func _put(g: PackedByteArray, x: int, y: int, W: int, H: int, v: int) -> void:
	if x >= 0 and x < W and y >= 0 and y < H:
		g[y * W + x] = v


static func _cell(g: PackedByteArray, x: int, y: int, W: int, H: int) -> int:
	if x < 0 or x >= W or y < 0 or y >= H:
		return 1
	return g[y * W + x]


# ================================================================== çizge
static func _build(rng: RandomNumberGenerator, W: int, H: int, style: String, opts: Dictionary) -> Dictionary:
	var P: Dictionary = STIL[style]
	if _tur != "eski":
		# v41: tür stilin çizge / oda parametrelerini ezer (bkz. TURLER)
		P = P.duplicate()
		for k in ["kinds", "dal", "dongu", "genis", "tavan", "acik"]:
			if (TURLER[_tur] as Dictionary).has(k):
				P[k] = TURLER[_tur][k]
	var cols := mini(int(P["cols"]), (W - 2 * KENAR) / SW)
	var rows := clampi(int(opts.get("rows", P["rows"])), 1, (H - 2 * KENAR) / SH)
	var yon := String(opts.get("yon", P["yon"]))
	var dikey: int = int(TURLER[_tur]["dikey"]) if _tur != "eski" else 99
	var yilan: bool = bool(TURLER[_tur]["yilan"]) if _tur != "eski" else true
	var grid := PackedByteArray()
	grid.resize(W * H)
	grid.fill(1)
	# --- kesim ızgarası ve ana yol
	var sr := 0
	var er := rows - 1
	match yon:
		"cikis":
			sr = rows - 1
			er = 0
		"serbest":
			# v33: çoğunlukla iner (Dead Cells ana yolları aşağı / yana akar); %25 çıkış girişten bir kat yüksekte
			sr = rng.randi_range(0, maxi(0, rows - 2))
			er = rng.randi_range(mini(rows - 1, sr + 1), rows - 1)
			if rows > 1 and rng.randf() < 0.25:
				er = rng.randi_range(0, rows - 2)
				sr = er + 1
		"duz":
			# v41 düz türler: açık yol üst satırda (yer yüzü) akar; kale orta satırda, %35 bir kat iner / çıkar
			sr = 0 if _tur == "acik" else mini(1, rows - 1)
			er = sr
			if _tur != "acik" and rows > 1 and rng.randf() < 0.35:
				er = clampi(sr + (1 if rng.randf() < 0.7 else -1), 0, rows - 1)   # çoğunlukla zindana iner
	if _tur != "eski" and absi(er - sr) > dikey:
		# v41: giriş / çıkış satırları türün dikey sınırına sığar (kalan katlar dallara)
		match yon:
			"inis":
				sr = rng.randi_range(0, rows - 1 - dikey)
				er = sr + dikey
			"cikis":
				er = rng.randi_range(0, rows - 1 - dikey)
				sr = er + dikey
			_:
				er = sr + signi(er - sr) * dikey
	var path := _ana_yol(rng, cols, rows, sr, er, yon, dikey, yilan)
	# v34: Kut Kapısı sapağı: yol sapaktan sonra "uzantı" olarak sürer (sonu ödül), kapı yandaki çıkmaz odada
	var uzanti: Array = []
	if rng.randf() < SAPAK_SANS:
		var sap := _cikis_sapagi(rng, path, cols, rows, yon, dikey, 0 if (_tur == "eski" or bool(TURLER[_tur]["duz"])) else 1)
		if not sap.is_empty():
			path = sap[0]
			uzanti = sap[1]
	var owner: Array = []   # [c][r] -> oda kimliği
	for c in cols:
		var col: Array = []
		for r in rows:
			col.append(-1)
		owner.append(col)
	var rooms: Array = []
	var doors: Array = []
	for i in path.size():
		var cell: Vector2i = path[i]
		var role := "ana"
		if i == 0:
			role = "giris"
		elif i == path.size() - 1:
			role = "cikis"
		var id := _new_room(rooms, owner, cell, role)
		rooms[id]["ana_i"] = i
		if i > 0:
			_add_door(doors, rooms, owner, path[i - 1], cell, "ana")
			if i == path.size() - 1 and not uzanti.is_empty():
				# v34: Kut Kapısı odasına sapak: kuyuysa kapaklı (yürürken düşülmez: oyuncu seçer), yansa koridor
				doors[doors.size() - 1]["kapak"] = true
				rooms[id]["sapak"] = true
	# ödül sırası: tomar ve hazine kesin, kalanı (sunak / seçkin / zamanlı) karışık; pazar istenirse en başa
	var oduller: Array = ["tomar", "hazine"]
	var rest: Array = ["sunak", "seckin", "zamanli"]
	_shuffle(rng, rest)
	oduller.append_array(rest)
	oduller.append_array(["tomar", "hazine"])
	if bool(opts.get("hikaye_odasi", false)):
		oduller.push_front("hikaye")   # v41 anlatı kancası: yaratıksız, ödülsüz çıkmaz oda (bkz. TURLER altı)
	if bool(opts.get("pazar", false)):
		oduller.push_front("pazar")
	var n_dal := 0
	var n_cikmaz := 0
	# --- v34 uzantı: sapaktan sonra süren görünür koridor (dal odaları), sonu ödül odası
	var n_uzanti := uzanti.size()
	if not uzanti.is_empty():
		var prev: Vector2i = path[path.size() - 2]
		rooms[int(owner[prev.x][prev.y])]["kavsak"] = true
		var last := -1
		for ui in uzanti.size():
			var uc: Vector2i = uzanti[ui]
			last = _new_room(rooms, owner, uc, "dal")
			rooms[last]["uzanti"] = true
			rooms[last]["uz_i"] = path.size() - 1 + ui   # ana yol sırasının devamı (pencere / dal puanlaması)
			_add_door(doors, rooms, owner, prev, uc, "uzanti")
			doors[doors.size() - 1]["ileri"] = uc
			prev = uc
		rooms[last]["role"] = "odul"
		rooms[last]["odul"] = String(UZANTI_ODUL[rng.randi_range(0, UZANTI_ODUL.size() - 1)])
		rooms[last]["dal_uz"] = uzanti.size()
		n_dal += 1
		n_cikmaz += 1
	# --- v34 pencere dalları: ana yoldan parmaklık ardında görünen ödül, dolaşarak varılır
	var n_pencere := 0
	for t in 2:
		if t == 1 and rng.randf() >= PENCERE_EK:
			break
		var odl := "tomar" if oduller.has("tomar") and rng.randf() < 0.5 else "hazine"
		if _pencere_dali(rng, rooms, owner, doors, cols, rows, odl):
			oduller.erase(odl)
			n_pencere += 1
			n_dal += 1
			n_cikmaz += 1
	# --- dallar: kavşaklardan boş kesimlere 1-2 odalık yürüyüş, sonu çıkmaz (ödül)
	var dal_n: int = rng.randi_range(int(P["dal"][0]), int(P["dal"][1]))
	var junctions: Array = []
	for i in range(1, path.size() - 1):
		junctions.append(i)
	if bool(opts.get("pazar", false)) and bool(opts.get("pazar_kapi", false)):
		# boss öncesi: pazar çıkışa yakın kavşaktan ayrılır
		junctions.reverse()
	else:
		# v34: dallar ERKEN ayrılır (Dead Cells: ödül yolları bölümün başında görünür; çıkışa koşan oyuncu "bir şey
		# kaçırdım" der): kavşak sırası yol başına ağırlıklı, rastgele karışık
		var keyed: Array = []
		for i in junctions:
			keyed.append([float(i) / float(path.size()) + rng.randf() * 0.55, i])
		keyed.sort_custom(func(a: Array, b: Array) -> bool: return float(a[0]) < float(b[0]))
		junctions.clear()
		for kk in keyed:
			junctions.append(int(kk[1]))
	# yedek kavşaklar: çıkış ve giriş odası (ara odalardan dal çıkmazsa; en az 2 çıkmaz için)
	junctions.append(path.size() - 1)
	junctions.append(0)
	for ji in junctions:
		if n_dal - (1 if n_uzanti > 0 else 0) >= dal_n:
			break
		if ji == path.size() - 1 and n_uzanti > 0:
			continue   # v34: sapaktaki Kut Kapısı odası tek kapılı çıkmaz kalır
		var cur: Vector2i = path[ji]
		var chain: Array = []
		var ln := 1 + (1 if rng.randf() < 0.35 else 0)
		var prev := cur
		for step in ln:
			var opts2: Array = []
			for d in [Vector2i(0, -1), Vector2i(0, 1), Vector2i(1, 0), Vector2i(-1, 0)]:
				var n: Vector2i = prev + d
				if n.x < 0 or n.x >= cols or n.y < 0 or n.y >= rows or owner[n.x][n.y] >= 0:
					continue
				# v33: yan dal (koridor) ağırlıklı; dikey dal: kapaklı düşüşle inilen / birkaç zıplamayla çıkılan ödül
				var w := 1 if d.y != 0 else 2
				for k in w:
					opts2.append(n)
			if opts2.is_empty():
				break
			var nxt: Vector2i = opts2[rng.randi_range(0, opts2.size() - 1)]
			var id := _new_room(rooms, owner, nxt, "dal")
			_add_door(doors, rooms, owner, prev, nxt, "dal")
			chain.append(id)
			prev = nxt
		if chain.is_empty():
			continue
		n_dal += 1
		rooms[int(owner[cur.x][cur.y])]["kavsak"] = true
		var last: int = chain[chain.size() - 1]
		rooms[last]["role"] = "odul"
		rooms[last]["odul"] = String(oduller.pop_front()) if not oduller.is_empty() else "hazine"
		rooms[last]["dal_uz"] = chain.size()
		n_cikmaz += 1
	# v34: pazar istendiyse ve hiçbir dala düşmediyse (pencere / uzantı dalları sayıyı doldurdu) bir ödül odası pazar
	# olur: boss öncesinde uzantının sonu (çıkışa yakın), değilse sıradan dal, yoksa uzantı / pencere odası
	if oduller.has("pazar"):
		var aday: Dictionary = {}
		var puan := -1
		for rm in rooms:
			if rm["role"] != "odul":
				continue
			var p := 1
			if bool(rm.get("pencere", false)):
				p = 0
			elif bool(rm.get("uzanti", false)):
				p = 3 if bool(opts.get("pazar_kapi", false)) else 1
			else:
				p = 2
			if p > puan:
				puan = p
				aday = rm
		if not aday.is_empty():
			aday["odul"] = "pazar"
			oduller.erase("pazar")
	# --- döngüler: kapısız komşu odalar arasında (ödül odaları tek kapılı kalır)
	var n_dongu := 0
	for c in cols:
		for r in rows:
			var a: int = owner[c][r]
			if a < 0 or rooms[a]["role"] == "odul" or bool(rooms[a].get("sapak", false)):
				continue
			for d in [Vector2i(1, 0), Vector2i(0, 1)]:
				var n: Vector2i = Vector2i(c, r) + d
				if n.x >= cols or n.y >= rows:
					continue
				var b: int = owner[n.x][n.y]
				# v34: sapaktaki Kut Kapısı odası tek kapılı (uzantıdan döngüyle kapıya düşülmesin)
				if b < 0 or b == a or rooms[b]["role"] == "odul" or bool(rooms[b].get("sapak", false)) or _has_door(doors, a, b):
					continue
				if rng.randf() < float(P["dongu"]):
					_add_door(doors, rooms, owner, Vector2i(c, r), n, "dongu")
					n_dongu += 1
	# --- birleşme: yan yana ana yol odaları geniş salon (ödül odaları ve giriş birleşmez; v33: üst üste birleşme yok,
	# dikey geçiş hep kuyu)
	var n_genis := 0
	for i in range(path.size() - 1):
		var a: Vector2i = path[i]
		var b: Vector2i = path[i + 1]
		var ra: int = owner[a.x][a.y]
		var rb: int = owner[b.x][b.y]
		if ra == rb or rooms[ra]["role"] == "giris" or bool(rooms[rb].get("sapak", false)) or (rooms[ra]["cells"] as Array).size() > 1 or (rooms[rb]["cells"] as Array).size() > 1:
			continue
		if b.y == a.y and rng.randf() < float(P["genis"]):
			_merge(rooms, owner, doors, ra, rb)
			n_genis += 1
	# --- oda türleri, kutular, taban / tavan profilleri
	var kinds: Array = P["kinds"]
	var kullan := {}          # v43: bu bölümde kullanılan şablonlar (aynı oda iki kez çıkmaz)
	var simge_var := false    # v43: bölümün sahne parçası (simge şablonu) kondu mu
	for rm in rooms:
		if rm["role"] == "yok":
			_room_rect(rm)
			continue
		var cells: Array = rm["cells"]
		var role: String = rm["role"]
		if role == "odul":
			rm["kind"] = "odul"
		elif role == "giris":
			rm["kind"] = "salon"
		elif cells.size() > 1:
			rm["kind"] = ["salon", "harabe", "teras", "kopru", "kuyu"][rng.randi_range(0, 4)]
			if _tur == "acik":
				rm["kind"] = ["tepe", "tepe", "harabe", "kopru", "tepe"][rng.randi_range(0, 4)]   # v41: geniş açık arazi
			elif _tur == "kale":
				rm["kind"] = ["harabe", "avlu", "salon", "harabe", "kopru"][rng.randi_range(0, 4)]   # v41: uzun salon / avlu
		else:
			rm["kind"] = String(kinds[rng.randi_range(0, kinds.size() - 1)])
		rm["acik"] = bool(P["acik"]) and int((cells[0] as Vector2i).y) == 0
		rm["clear"] = []
		rm["kuyular"] = []
		_room_box(rng, rm, doors)
		rm["_otag_yakin"] = rm["role"] == "ana" and int(rm.get("ana_i", -1)) >= path.size() - 3
		if _v43 and _sablon_sec(rng, rm, kullan, simge_var, path.size()):
			simge_var = simge_var or bool(rm["tpl"]["simge"])
		else:
			_profile(rng, rm, int(P["tavan"]))
	if _v43:
		_sablon_kuyu_denetle(rng, rooms, doors, int(P["tavan"]))
	# --- kapı geometrisi (yan koridorlar, kuyular / v43 geçit türleri)
	var gecit_kul := {}
	for dr in doors:
		_door_geometry(rng, rooms, dr, gecit_kul)
	# pazar dikey kapılı odaya düştüyse yan kapılı başka bir ödül odasıyla yer değiştirir (tüccar istendiyse kaybolmasın;
	# boss öncesi Bezirgân kesin). Yan kapılı ödül odası yoksa kuyulu odada kalır: tezgâh _odul_mid ile kuyudan uzak yana
	# kurulur (kuyu odanın bir ucuna yaslanır).
	for rm in rooms:
		if rm["role"] == "odul" and String(rm["odul"]) == "pazar" and String(rm.get("_door_side", "sol")) in ["ust", "alt"]:
			for rm2 in rooms:
				if rm2["role"] == "odul" and rm2 != rm and not (String(rm2.get("_door_side", "sol")) in ["ust", "alt"]):
					rm["odul"] = rm2["odul"]
					rm2["odul"] = "pazar"
					break
			break
	for rm in rooms:
		# zamanlı kapı yalnızca yan kapılı odada (dikey kuyuya kapı kurulmaz)
		if rm["role"] == "odul" and String(rm.get("_door_side", "sol")) in ["ust", "alt"] and String(rm["odul"]) == "zamanli":
			rm["odul"] = "hazine"
	# v34 kilitli ödül odası: yan kapılı (pazar, zamanlı, pencereli değil); anahtar sonra (_anahtar_yeri)
	var kilit_rm: Dictionary = {}
	if rng.randf() < KILIT_SANS:
		var kc: Array = []
		for rm in rooms:
			if rm["role"] == "odul" and String(rm.get("_door_side", "sol")) in ["sol", "sag"] and not (String(rm["odul"]) in ["pazar", "zamanli", "hikaye"]) and not bool(rm.get("pencere", false)):
				kc.append(rm)
		if not kc.is_empty():
			kilit_rm = kc[rng.randi_range(0, kc.size() - 1)]
			kilit_rm["kilit"] = true
	# Kut Kapısı önü (çıkış odasının sağ ucu, 9 sütun) düz ve boş kalır: sütun / kaya / çukurcuk / tehlike yok.
	# v34: kapı odaya sağdaki koridordan giriliyorsa (sapak) Kut Kapısı odanın SOL ucunda (kapıdan uzak yan)
	for rm in rooms:
		if rm["role"] == "cikis":
			rm["cikis_sol"] = bool(rm["_sag"]) and not bool(rm["_sol"])
			if bool(rm["cikis_sol"]):
				(rm["clear"] as Array).append(Rect2i(int(rm["ix0"]), 0, 10, 999))
			else:
				(rm["clear"] as Array).append(Rect2i(int(rm["ix1"]) - 9, 0, 10, 999))
	# --- oyma
	for rm in rooms:
		if rm["role"] != "yok":
			_carve_room(grid, W, H, rm)
	for rm in rooms:
		if rm["role"] != "yok":
			_features(grid, W, H, rng, rm, style)
	var n_kuyu := 0
	var n_acik := 0
	var gecitler: Array = []   # v43: dikey geçitlerin çizim / tırmanma verisi (Level: GecitCiz, Player tırmanma)
	for dr in doors:
		_carve_door(grid, W, H, rooms, dr)
		if dr["kind"] != "sil" and dr["dir"] == "v":
			n_kuyu += 1
			if bool(dr.get("acik", false)):
				n_acik += 1
			if dr.has("gecit_veri"):
				gecitler.append(dr["gecit_veri"])
	if _tur == "acik":
		# v41: göğe açık sütunlarda ızgaranın en üst satırı da hava (tepede kaya şeridi görünmesin; ulaşılmaz yükseklik)
		for x in range(1, W - 1):
			if grid[W + x] == 0:
				grid[x] = 0
	# --- işaretler, tehlikeler, Kut Taşları, kaideler
	var chunks: Array = []
	var zamanli: Array = []
	var tasi: Array = []
	var kaide: Array = []
	var main_rooms: Array = []
	for rm in rooms:
		if int(rm.get("ana_i", -1)) >= 0 and rm["role"] != "yok":
			main_rooms.append(rm)
	main_rooms.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return int(a["ana_i"]) < int(b["ana_i"]))
	for rm in rooms:
		if rm["role"] == "odul":
			var mk := _odul_marks(grid, W, H, rng, rm, zamanli, doors)
			chunks.append({"name": String(rm["odul"]), "x": int(rm["ix0"]), "marks": mk, "room": int(rm["id"])})
		elif rm["role"] in ["ana", "dal"] and not rm.has("tpl"):
			_hazard_strips(grid, W, H, rng, rm, style)
	# v34 gizli cepler (kırık duvar), kilitli kapı ve anahtarı
	var cepler := _gizli_cepler(grid, W, H, rng, rooms)
	var kilitli: Array = []
	if not kilit_rm.is_empty():
		var kd := _yan_kapi_sutunu(kilit_rm, doors)
		var anahtar := false
		var cc: Array = []
		for cp in cepler:
			if int(cp["room"]) != int(kilit_rm["id"]):
				cc.append(cp)
		if not cc.is_empty():
			cc[rng.randi_range(0, cc.size() - 1)]["icerik"] = "anahtar"
			anahtar = true
		else:
			# gizli cep yoksa: başka bir ödül odasının köşesinde (pazar / kilitli değil)
			for ch in chunks:
				var orm: Dictionary = rooms[int(ch["room"])]
				if orm == kilit_rm or String(orm["odul"]) == "pazar":
					continue
				var kx := clampi(_odul_mid(orm) + (4 if _door_side(orm) != "sag" else -4), int(orm["ix0"]) + 2, int(orm["ix1"]) - 2)
				var ks := _floor_spot(grid, W, H, orm, kx)
				(ch["marks"] as Array).append(["K", ks.x, ks.y])
				anahtar = true
				break
		if anahtar:
			kilitli.append({"x": kd.x, "y": kd.y, "room": int(kilit_rm["id"])})
		else:
			kilit_rm["kilit"] = false
	# Kut Taşları (3-4): giriş (girişin 9 karo sağı); ana yolun ortasına en yakın kavşak (yoksa orta oda); girişten en
	# uzak 1-2 ödül odası (kapıya yakın)
	var g_rm: Dictionary = rooms[0]
	var spawn := Vector2i(int(g_rm["ix0"]) + 3, int(g_rm["fl"][3]) - 1)
	tasi.append(_floor_spot(grid, W, H, g_rm, int(g_rm["ix0"]) + 9))
	var nm := main_rooms.size()
	var mid_rm: Dictionary = main_rooms[nm / 2]
	var mid_d := 999
	for rm in main_rooms:
		if bool(rm.get("kavsak", false)) and rm["role"] == "ana" and absi(int(rm["ana_i"]) - nm / 2) < mid_d:
			mid_d = absi(int(rm["ana_i"]) - nm / 2)
			mid_rm = rm
	_tasi_ekle(tasi, _floor_spot(grid, W, H, mid_rm, (int(mid_rm["ix0"]) + int(mid_rm["ix1"])) / 2))
	var odul_rooms: Array = []
	for rm in rooms:
		if rm["role"] == "odul":
			odul_rooms.append(rm)
	var uzak := func(a: Dictionary, b: Dictionary) -> bool: return absi(int(a["ix0"]) - spawn.x) + 2 * absi(int(a["iy1"]) - spawn.y) > absi(int(b["ix0"]) - spawn.x) + 2 * absi(int(b["iy1"]) - spawn.y)
	odul_rooms.sort_custom(uzak)
	for rm in odul_rooms:
		if tasi.size() >= 4:
			break
		_tasi_ekle(tasi, _odul_tasi(grid, W, H, rm))
	if tasi.size() < 3:
		# yedek: ana yolun 3/4'ündeki oda
		var rq: Dictionary = main_rooms[clampi(nm * 3 / 4, 1, nm - 1)]
		tasi.append(_floor_spot(grid, W, H, rq, (int(rq["ix0"]) + int(rq["ix1"])) / 2))
	# eşya kaideleri: ana yolun 1/4, 2/4, 3/4'ündeki odaların ortası
	for q in [0.25, 0.5, 0.75]:
		var rm: Dictionary = main_rooms[clampi(int(round(q * (nm - 1))), 1, nm - 1)]
		kaide.append(_floor_spot(grid, W, H, rm, _bos_sutun(rm, (int(rm["ix0"]) + int(rm["ix1"])) / 2 + rng.randi_range(-3, 3))))
	# çıkış: çıkış odasının sağ ucu (v34: kapı odaya sağdan giriliyorsa sol ucu)
	var e_rm: Dictionary = main_rooms[nm - 1]
	var exit := _floor_spot(grid, W, H, e_rm, int(e_rm["ix0"]) + 4 if bool(e_rm.get("cikis_sol", false)) else int(e_rm["ix1"]) - 4)
	# heights: sütundaki ana yol odasının (ilk gelinen) tabanı; eski surface_y / süs / test çağrıları için
	var heights: Array = []
	heights.resize(W)
	heights.fill(H - 3)
	for i in range(main_rooms.size() - 1, -1, -1):
		var rm: Dictionary = main_rooms[i]
		for x in range(int(rm["ix0"]), int(rm["ix1"]) + 1):
			heights[x] = int(rm["fl"][x - int(rm["ix0"])])
	for x in range(0, int(rooms[0]["ix0"])):
		heights[x] = heights[int(rooms[0]["ix0"])]
	for x in range(int(e_rm["ix1"]) + 1, W):
		heights[x] = heights[int(e_rm["ix1"])]
	# giriş düzlüğü garantisi
	for x in range(int(g_rm["ix0"]), int(g_rm["ix0"]) + 8):
		var fy: int = int(g_rm["fl"][x - int(g_rm["ix0"])])
		for y in range(maxi(1, fy - 5), fy):
			_put(grid, x, y, W, H, 0)
		_put(grid, x, fy, W, H, 1)
	var dikey_adim := 0
	var rmin := rows
	var rmax := 0
	for i in range(1, path.size()):
		if path[i].y != path[i - 1].y:
			dikey_adim += 1
	for rm in rooms:
		if rm["role"] == "yok":
			continue
		rmin = mini(rmin, int(rm["r0"]))
		rmax = maxi(rmax, int(rm["r1"]))
	var metrics := {"oda": rooms.size() - n_genis, "ana": path.size(), "dal": n_dal, "cikmaz": n_cikmaz, "dongu": n_dongu,
		"genis": n_genis, "yuksek": 0, "dikey_adim": dikey_adim, "satir": rmax - rmin + 1, "kapi": doors.size() - n_genis,
		"tasi": tasi.size(), "zamanli": zamanli.size(), "cols": cols, "rows": rows, "kuyu": n_kuyu, "acik_kuyu": n_acik}
	# v34 ölçümleri: sapak / uzantı, pencere, gizli cep, kilit, dalların ayrıldığı yer (ana yol sırası / uzunluk)
	var pencereler: Array = []
	for dr in doors:
		if dr["kind"] == "pencere" and dr.has("parmak"):
			pencereler.append({"cells": dr["parmak"], "a": int(dr["a"]), "b": int(dr["b"])})
	var kav_sum := 0.0
	var kav_n := 0
	for dr in doors:
		if not (dr["kind"] in ["dal", "pencere_dal"]):
			continue
		for k in ["a", "b"]:
			var jr: Dictionary = rooms[int(dr[k])]
			if int(jr.get("ana_i", -1)) >= 0:
				kav_sum += float(jr["ana_i"]) / float(maxi(1, path.size() - 1))
				kav_n += 1
	metrics["sapak"] = 1 if n_uzanti > 0 else 0
	metrics["uzanti"] = n_uzanti
	metrics["pencere"] = pencereler.size()
	metrics["cep"] = cepler.size()
	metrics["kilit"] = kilitli.size()
	metrics["dal_yeri"] = kav_sum / maxf(1.0, float(kav_n))
	# v41: tür ölçümleri ve anlatı sahnesi yeri
	metrics["tur"] = _tur
	metrics["duz"] = 1 if dikey_adim <= 1 else 0
	var hikaye: Dictionary = {}
	for rm in rooms:
		if rm["role"] == "odul" and String(rm["odul"]) == "hikaye":
			var hx := _floor_spot(grid, W, H, rm, _odul_mid(rm))
			hikaye = {"room": int(rm["id"]), "x": hx.x, "y": hx.y}
	var sahne := _sahne_yeri(grid, W, H, main_rooms)
	var bnd := _sinirlar(grid, W, H)
	for cp in cepler:
		bnd = bnd.merge((cp["cep"] as Rect2i).grow(2)).intersection(Rect2i(0, 0, W, H))
	# v43 ölçümleri: şablon kapsamı (ana yol + dal odaları), bölümdeki ayrı şablon sayısı, geçit türleri, simge
	var n_ad := 0
	var n_tpl := 0
	var adlar := {}
	var simge := ""
	for rm in rooms:
		if rm["role"] in ["ana", "dal"]:
			n_ad += 1
			if rm.has("tpl"):
				n_tpl += 1
		if rm.has("tpl"):
			adlar[String(rm["tpl"]["ad"])] = true
			if bool(rm["tpl"]["simge"]):
				simge = String(rm["tpl"]["ad"])
	var gt := {}
	for gv in gecitler:
		gt[String(gv["tip"])] = int(gt.get(String(gv["tip"]), 0)) + 1
	metrics["sablon_oda"] = n_tpl
	metrics["sablon_aday"] = n_ad
	metrics["sablon_cesit"] = adlar.size()
	metrics["simge"] = 1 if simge != "" else 0
	metrics["gecit_tur"] = gt
	metrics["gecit_cesit"] = gt.size()
	return {"grid": grid, "heights": heights, "chunks": chunks, "rooms": rooms, "doors": doors, "path": path, "spawn": spawn,
		"exit": exit, "tasi": tasi, "zamanli": zamanli, "kaide": kaide, "bounds": bnd, "metrics": metrics,
		"cepler": cepler, "kilitli": kilitli, "pencereler": pencereler, "tur": _tur, "hikaye": hikaye, "sahne": sahne,
		"gecitler": gecitler, "propler": _propler(rooms, doors), "simge": simge}


static func _sahne_yeri(g: PackedByteArray, W: int, H: int, main_rooms: Array) -> Dictionary:
	## v41 anlatı sahnesi: ana yol odalarında (giriş / çıkış değil) en uzun düz, üstü 3 karo kayasız, kapı ağzına / kuyuya
	## girmeyen taban aralığı. {room, x0, x1, y (ayakta durulan satır)}; bulunamazsa boş.
	var best: Dictionary = {}
	var best_n := 5
	for rm in main_rooms:
		if rm["role"] != "ana":
			continue
		var ix0 := int(rm["ix0"])
		var fl: Array = rm["fl"]
		var run0 := -1
		for x in range(ix0, int(rm["ix1"]) + 2):
			var ok := x <= int(rm["ix1"])
			var fy := 0
			if ok:
				fy = int(fl[x - ix0])
				ok = _cell(g, x, fy, W, H) == 1 and not _in_clear(rm, x, fy - 1)
				for y in range(fy - 3, fy):
					if _cell(g, x, y, W, H) == 1 or _cell(g, x, y, W, H) == 3:
						ok = false
				if ok and run0 >= 0 and int(fl[run0 - ix0]) != fy:
					if x - run0 > best_n:
						best_n = x - run0
						best = {"room": int(rm["id"]), "x0": run0, "x1": x - 1, "y": int(fl[run0 - ix0]) - 1}
					run0 = x
			if ok and run0 < 0:
				run0 = x
			elif not ok and run0 >= 0:
				if x - run0 > best_n:
					best_n = x - run0
					best = {"room": int(rm["id"]), "x0": run0, "x1": x - 1, "y": int(fl[run0 - ix0]) - 1}
				run0 = -1
	return best


static func _cikis_sapagi(rng: RandomNumberGenerator, path: Array, cols: int, rows: int, yon: String, dikey := 99, en_az_dikey := 0) -> Array:
	## v34: ana yolun son %60'ındaki j. kesimden (yolun sonuna en az bir oda kala) boş bir komşu kesime Kut Kapısı
	## sapağı. Stil yönü korunur (inis: aşağı ya da yana; cikis: yukarı ya da yana). Döndürür [yeni yol (giriş .. j, sapak),
	## uzantı (eski yolun j+1 .. sonu)] ya da boş dizi.
	var n := path.size()
	if n < 5:
		return []
	var seen := {}
	for c in path:
		seen[c] = true
	var cands: Array = []   # [j, kesim, ağırlık]
	var pv: Array = [0]   # v41: yolun j. kesimine dek dikey adım
	for i in range(1, n):
		pv.append(int(pv[i - 1]) + (1 if path[i].y != path[i - 1].y else 0))
	for j in range(maxi(2, int(ceil(n * 0.4))), n - 1):
		var cur: Vector2i = path[j]
		for d in [Vector2i(0, 1), Vector2i(0, -1), Vector2i(1, 0), Vector2i(-1, 0)]:
			var e: Vector2i = cur + d
			if e.x < 0 or e.x >= cols or e.y < 0 or e.y >= rows or seen.has(e):
				continue
			# v41: türün dikey adım sınırı (düz türlerde ana yol en çok 1 kat; dikey türlerde en az 1)
			var vv: int = int(pv[j]) + (1 if d.y != 0 else 0)
			if vv > dikey or vv < en_az_dikey:
				continue
			var w := 1
			match yon:
				"inis":
					if d.y < 0:
						continue
					w = 3 if d.y > 0 else 1
				"cikis":
					if d.y > 0:
						continue
					w = 3 if d.y < 0 else 1
				_:
					w = 2 if d.y != 0 else 1
			for k in w:
				cands.append([j, e])
	if cands.is_empty():
		return []
	var pick: Array = cands[rng.randi_range(0, cands.size() - 1)]
	var j: int = pick[0]
	var np: Array = path.slice(0, j + 1)
	np.append(pick[1])
	return [np, path.slice(j + 1)]


static func _pencere_dali(rng: RandomNumberGenerator, rooms: Array, owner: Array, doors: Array, cols: int, rows: int, odul: String) -> bool:
	## v34 pencere dalı (Dead Cells'in "görünen ama ulaşılmayan" ödülü): boş R kesimi, yanındaki (yatay) bir yol odası
	## A'ya PARMAKLIKLI PENCEREYLE bakar; R'ye başka bir J odasından (0-1 ara oda) dolaşarak girilir. A erken, J A'dan
	## sonra gelsin (önce görülür, sonra yolu bulunur). true: kuruldu.
	var best: Array = []
	var best_s := -1e9
	var sira := func(id: int) -> float:
		var rm: Dictionary = rooms[id]
		if int(rm.get("ana_i", -1)) >= 0:
			return float(rm["ana_i"])
		return float(rm.get("uz_i", 99))
	var uygun := func(id: int) -> bool:
		if id < 0:
			return false
		var rm: Dictionary = rooms[id]
		return rm["role"] in ["giris", "ana"] or (rm["role"] == "dal" and bool(rm.get("uzanti", false)))
	for c in cols:
		for r in rows:
			if owner[c][r] >= 0:
				continue
			var R := Vector2i(c, r)
			for s in [-1, 1]:
				var A := R + Vector2i(s, 0)
				if A.x < 0 or A.x >= cols or not uygun.call(int(owner[A.x][A.y])):
					continue
				var a_id: int = owner[A.x][A.y]
				for d in [Vector2i(0, 1), Vector2i(0, -1), Vector2i(1, 0), Vector2i(-1, 0)]:
					var X: Vector2i = R + d
					if X == A or X.x < 0 or X.x >= cols or X.y < 0 or X.y >= rows:
						continue
					var xo: int = owner[X.x][X.y]
					if xo >= 0:
						# doğrudan: R, J'ye komşu
						if xo != a_id and uygun.call(xo):
							var sc: float = 1.0 + (2.0 if float(sira.call(xo)) > float(sira.call(a_id)) else 0.0) - 0.15 * float(sira.call(a_id)) + rng.randf() * 0.8
							if sc > best_s:
								best_s = sc
								best = [R, A, X, Vector2i(-1, -1)]
						continue
					# bir ara oda: X boş, X'in komşusu J (R ve A değil)
					for d2 in [Vector2i(0, 1), Vector2i(0, -1), Vector2i(1, 0), Vector2i(-1, 0)]:
						var J: Vector2i = X + d2
						if J == R or J.x < 0 or J.x >= cols or J.y < 0 or J.y >= rows:
							continue
						var jo: int = owner[J.x][J.y]
						if jo == a_id or not uygun.call(jo):
							continue
						var sc2: float = 2.5 + (2.0 if float(sira.call(jo)) > float(sira.call(a_id)) else 0.0) - 0.15 * float(sira.call(a_id)) + rng.randf() * 0.8
						if sc2 > best_s:
							best_s = sc2
							best = [R, A, J, X]
	if best.is_empty():
		return false
	var R2: Vector2i = best[0]
	var A2: Vector2i = best[1]
	var J2: Vector2i = best[2]
	var X2: Vector2i = best[3]
	rooms[int(owner[J2.x][J2.y])]["kavsak"] = true
	var prev := J2
	if X2.x >= 0:
		_new_room(rooms, owner, X2, "dal")
		_add_door(doors, rooms, owner, J2, X2, "dal")
		prev = X2
	var rid := _new_room(rooms, owner, R2, "odul")
	rooms[rid]["odul"] = odul
	rooms[rid]["pencere"] = true
	rooms[rid]["pencere_yan"] = "sol" if A2.x < R2.x else "sag"
	rooms[rid]["dal_uz"] = 2 if X2.x >= 0 else 1
	_add_door(doors, rooms, owner, prev, R2, "dal")
	_add_door(doors, rooms, owner, A2, R2, "pencere")
	return true


static func _yan_kapi_sutunu(rm: Dictionary, doors: Array) -> Vector2i:
	## Yan kapılı ödül odasının koridorunda odaya bitişik sütun ve taban satırı (zamanlı / kilitli kapı: 4 karo geçit)
	var side := _door_side(rm)
	var fl: Array = rm["fl"]
	var dx := int(rm["ix0"]) - 1 if side == "sol" else int(rm["ix1"]) + 1
	var dy := int(fl[0]) if side == "sol" else int(fl[fl.size() - 1])
	for di in rm["doors"]:
		var d: Dictionary = doors[di]
		if d["dir"] == "h" and d["kind"] != "sil" and d["kind"] != "pencere":
			dy = int(d["y"])
	return Vector2i(dx, dy)


static func _gizli_cepler(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rooms: Array) -> Array:
	## v34 gizli cepler: odanın kapısız yan duvarında (taban hizası) 1 sütunluk ÇATLAK DUVAR (4 karo) ve ardında 4 x 4
	## cep. Cep alanı (+1 karo pay) bütünüyle kaya olmalı (koridor / kuyu / başka oda yok). Cep oyulmaz (Level kırınca
	## oyar). İçerik: altın (çoğu), Kut, şifa, eşya ("zula": eski gizli yeraltı odalarının ganimeti), anahtar sonra.
	var want := rng.randi_range(int(CEP_SAYI[0]), int(CEP_SAYI[1]))
	var cands: Array = []
	for rm in rooms:
		if rm["role"] in ["yok", "cikis"] or (rm["fl"] as Array).is_empty():
			continue
		for s in [-1, 1]:
			if (s < 0 and bool(rm["_sol"])) or (s > 0 and bool(rm["_sag"])):
				continue
			cands.append([rm, s])
	_shuffle(rng, cands)
	var out: Array = []
	var used: Array = []
	for cd in cands:
		if out.size() >= want:
			break
		var rm: Dictionary = cd[0]
		var s: int = cd[1]
		var fl: Array = rm["fl"]
		var ex := int(rm["ix1"]) if s > 0 else int(rm["ix0"])        # odanın kenar sütunu
		var fy: int = int(fl[ex - int(rm["ix0"])])
		var ok := true
		# kenar ve yanındaki sütun: tabanı aynı ve katı, üstünde 4 karo hava (çatlak yüzü görünsün, önü yürünür)
		for kx in [ex, ex - s]:
			if _cell(g, kx, fy, W, H) != 1:
				ok = false
			for y in range(fy - 4, fy):
				if _cell(g, kx, y, W, H) != 0:
					ok = false
		if not ok:
			continue
		var wx := ex + s                       # çatlak duvar sütunu
		var px0 := wx + s if s > 0 else wx - 4  # cep sütunları px0 .. px0+3
		# duvar + cep + 1 sütun pay; tavan payı ve taban satırı dahil
		var r := Rect2i(wx, fy - 5, 6, 6) if s > 0 else Rect2i(wx - 5, fy - 5, 6, 6)
		if r.position.x < 2 or r.end.x > W - 2 or r.position.y < 2:
			continue
		for y in range(r.position.y, r.end.y):
			for x in range(r.position.x, r.end.x):
				if _cell(g, x, y, W, H) != 1:
					ok = false
		for u in used:
			if (u as Rect2i).grow(2).intersects(r):
				ok = false
		if not ok:
			continue
		used.append(r)
		var wall: Array = []
		for y in range(fy - 4, fy):
			wall.append(Vector2i(wx, y))
		var roll := rng.randf()
		var ic := "altin"
		if roll < 0.2:
			ic = "zula"
		elif roll < 0.35:
			ic = "kut"
		elif roll < 0.5:
			ic = "sifa"
		out.append({"wall": wall, "cep": Rect2i(px0, fy - 4, 4, 4), "room": int(rm["id"]), "yon": s, "taban": fy, "icerik": ic})
	return out


static func _tasi_ekle(tasi: Array, c: Vector2i) -> void:
	## Kut Taşı yalnızca diğerlerinden uzaksa (16 karo yatay ya da 8 karo dikey)
	for t in tasi:
		if absi(int(t.x) - c.x) < 16 and absi(int(t.y) - c.y) < 8:
			return
	tasi.append(c)


static func _sinirlar(g: PackedByteArray, W: int, H: int) -> Rect2i:
	## Katı olmayan karoların sıkı kutusu + 2 karo pay (kamera ve harita: bölüm parşömene sığar)
	var x0 := W
	var y0 := H
	var x1 := 0
	var y1 := 0
	for y in H:
		for x in W:
			if g[y * W + x] != 1:
				x0 = mini(x0, x)
				x1 = maxi(x1, x)
				y0 = mini(y0, y)
				y1 = maxi(y1, y)
	x0 = maxi(0, x0 - 2)
	y0 = maxi(0, y0 - 2)
	x1 = mini(W - 1, x1 + 2)
	y1 = mini(H - 1, y1 + 2)
	return Rect2i(x0, y0, x1 - x0 + 1, y1 - y0 + 1)


static func _shuffle(rng: RandomNumberGenerator, a: Array) -> void:
	for i in range(a.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var t = a[i]
		a[i] = a[j]
		a[j] = t


static func _ana_yol(rng: RandomNumberGenerator, cols: int, rows: int, sr: int, er: int, yon: String, dikey := 99, yilan := true) -> Array:
	## Giriş (0, sr) -> çıkış (cols-1, er): sağa, dikey (stile göre: inis yalnız aşağı, cikis yalnız yukarı, serbest
	## çoğunlukla aşağı ve en çok bir yukarı) ve v33'te bir dikey adımdan sonra 1-2 kesim SOLA (yılan: Dead Cells'in
	## kıvrılan ana yolu). Her adımda çıkışa hâlâ varılabildiği (boş kesimlerden) denetlenir. Hedef uzunluk:
	## sütun + satır farkı + 2-4. v41: dikey (türün en çok dikey adımı), yilan (sola dönüş; düz türlerde yok: hedef
	## uzunluk sütun + satır farkı).
	var target := cols + absi(er - sr) + rng.randi_range(2, 4)
	if not yilan:
		target = cols + absi(er - sr)
	var goal := Vector2i(cols - 1, er)
	var best: Array = []
	for attempt in 40:
		var path: Array = [Vector2i(0, sr)]
		var seen := {Vector2i(0, sr): true}
		var cur := Vector2i(0, sr)
		var last := Vector2i.ZERO
		var sola := 0
		var up_n := 0
		var v_n := 0
		var guard := 0
		while cur != goal and guard < 80:
			guard += 1
			var cand: Array = []   # [kesim, ağırlık]
			var kalan := target - path.size()   # hedefe kalan oda
			var en_az := (goal.x - cur.x) + absi(goal.y - cur.y)
			if cur.x < cols - 1:
				cand.append([cur + Vector2i(1, 0), 3 if kalan <= en_az + 1 else 2])
			if yilan and cur.x > 0 and cur.y != sr and (last.y != 0 or (last.x < 0 and sola < 2)) and kalan >= en_az + 2:
				cand.append([cur + Vector2i(-1, 0), 3])
			for dy in [-1, 1]:
				var w := 0
				match yon:
					"inis":
						w = 3 if dy > 0 else 0
					"cikis":
						w = 3 if dy < 0 else 0
					"duz":
						w = 1
					_:
						w = 2 if dy > 0 else (1 if up_n == 0 else 0)
				if last.y != 0:
					w = mini(w, 1) if dy > 0 else 0   # art arda iki düşüş seyrek; art arda iki tırmanış yok
				if cur.x == cols - 1:
					w = 4 if signi(goal.y - cur.y) == dy else 0
				if w > 0:
					cand.append([cur + Vector2i(0, dy), w])
			var opts: Array = []
			for cd in cand:
				var n: Vector2i = cd[0]
				if n.x < 0 or n.x >= cols or n.y < 0 or n.y >= rows or seen.has(n):
					continue
				# v41: türün dikey adım sınırı (bu adım + hedef satıra kalan fark)
				if v_n + (1 if n.y != cur.y else 0) + absi(goal.y - n.y) > dikey:
					continue
				if not _yol_varir(seen, n, goal, cols, rows, yon, up_n + (1 if n.y < cur.y else 0)):
					continue
				for k in int(cd[1]):
					opts.append(n)
			if opts.is_empty():
				break
			var nxt: Vector2i = opts[rng.randi_range(0, opts.size() - 1)]
			var mv := nxt - cur
			if mv.x < 0:
				sola += 1
			elif mv.x > 0:
				sola = 0
			if mv.y < 0:
				up_n += 1
			if mv.y != 0:
				v_n += 1
			last = mv
			path.append(nxt)
			seen[nxt] = true
			cur = nxt
		if cur == goal:
			if path.size() >= target - 1:
				return path
			if path.size() > best.size():
				best = path
	if not best.is_empty():
		return best
	# yedek: düz sağa, son sütunda dikey
	var p2: Array = []
	for c in cols:
		p2.append(Vector2i(c, sr))
	var r := sr
	while r != er:
		r += signi(er - sr)
		p2.append(Vector2i(cols - 1, r))
	return p2


static func _yol_varir(seen: Dictionary, from: Vector2i, goal: Vector2i, cols: int, rows: int, yon: String, up_n: int) -> bool:
	## from kesiminden çıkışa, görülmemiş kesimlerden (stilin dikey yönü kuralıyla) varılabilir mi
	var q: Array = [from]
	var vis := {from: true}
	var qi := 0
	while qi < q.size():
		var c: Vector2i = q[qi]
		qi += 1
		if c == goal:
			return true
		for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			if yon == "inis" and d.y < 0:
				continue
			if yon == "cikis" and d.y > 0:
				continue
			if yon == "serbest" and d.y < 0 and up_n > 0:
				continue
			var n: Vector2i = c + d
			if n.x < 0 or n.x >= cols or n.y < 0 or n.y >= rows or seen.has(n) or vis.has(n):
				continue
			vis[n] = true
			q.append(n)
	return false


static func _new_room(rooms: Array, owner: Array, cell: Vector2i, role: String) -> int:
	var id := rooms.size()
	rooms.append({"id": id, "cells": [cell], "role": role, "odul": "", "ana_i": -1, "doors": [], "kavsak": false})
	owner[cell.x][cell.y] = id
	return id


static func _has_door(doors: Array, a: int, b: int) -> bool:
	for d in doors:
		if (int(d["a"]) == a and int(d["b"]) == b) or (int(d["a"]) == b and int(d["b"]) == a):
			return true
	return false


static func _add_door(doors: Array, rooms: Array, owner: Array, ca: Vector2i, cb: Vector2i, kind: String) -> void:
	## ca ile cb komşu kesimler; kapı yönü ca'dan cb'ye (a: sol / üst oda, b: sağ / alt oda)
	var a: int = owner[ca.x][ca.y]
	var b: int = owner[cb.x][cb.y]
	var d := {"a": a, "b": b, "ca": ca, "cb": cb, "dir": "h" if cb.y == ca.y else "v", "kind": kind, "x": 0, "y": 0}
	if d["dir"] == "h" and cb.x < ca.x:
		d = {"a": b, "b": a, "ca": cb, "cb": ca, "dir": "h", "kind": kind, "x": 0, "y": 0}
	elif d["dir"] == "v" and cb.y < ca.y:
		d = {"a": b, "b": a, "ca": cb, "cb": ca, "dir": "v", "kind": kind, "x": 0, "y": 0}
	doors.append(d)
	(rooms[a]["doors"] as Array).append(doors.size() - 1)
	(rooms[b]["doors"] as Array).append(doors.size() - 1)


static func _merge(rooms: Array, owner: Array, doors: Array, ra: int, rb: int) -> void:
	## rb odası ra'ya katılır; aralarındaki kapı silinir (kind "sil": geometri ve oyma atlar), rb'nin diğer kapıları
	## ra'ya bağlanır; çıkış rolü ve kavşaklık korunur, ana yol dizini küçüğü olur. rb "yok" rolüyle boş kalır.
	var rm_a: Dictionary = rooms[ra]
	var rm_b: Dictionary = rooms[rb]
	for cell in rm_b["cells"]:
		(rm_a["cells"] as Array).append(cell)
		owner[cell.x][cell.y] = ra
	for di in doors.size():
		var d: Dictionary = doors[di]
		if (int(d["a"]) == ra and int(d["b"]) == rb) or (int(d["a"]) == rb and int(d["b"]) == ra):
			d["kind"] = "sil"
			continue
		if int(d["a"]) == rb:
			d["a"] = ra
		if int(d["b"]) == rb:
			d["b"] = ra
	rm_a["doors"] = []
	for di in doors.size():
		var d: Dictionary = doors[di]
		if d["kind"] != "sil" and (int(d["a"]) == ra or int(d["b"]) == ra):
			(rm_a["doors"] as Array).append(di)
	if rm_b["role"] == "cikis":
		rm_a["role"] = "cikis"
	rm_a["ana_i"] = mini(int(rm_a["ana_i"]), int(rm_b["ana_i"]))
	rm_a["kavsak"] = bool(rm_a["kavsak"]) or bool(rm_b["kavsak"])
	rm_b["cells"] = []
	rm_b["doors"] = []
	rm_b["role"] = "yok"
	rm_b["ana_i"] = -1


static func _room_rect(rm: Dictionary) -> void:
	## Kesim kapsamı (c0..c1, r0..r1) ve en geniş iç alan (kenar duvarları 2 karo)
	var cells: Array = rm["cells"]
	if cells.is_empty():
		for k in ["ix0", "ix1", "iy0", "iy1", "r0", "r1", "c0", "c1"]:
			rm[k] = 0
		rm["fl"] = []
		rm["ce"] = []
		return
	var c0 := 999
	var c1 := -1
	var r0 := 999
	var r1 := -1
	for cell in cells:
		c0 = mini(c0, cell.x)
		c1 = maxi(c1, cell.x)
		r0 = mini(r0, cell.y)
		r1 = maxi(r1, cell.y)
	rm["c0"] = c0
	rm["c1"] = c1
	rm["r0"] = r0
	rm["r1"] = r1
	rm["ix0"] = KENAR + c0 * SW + 2
	rm["ix1"] = KENAR + (c1 + 1) * SW - 3
	rm["iy0"] = KENAR + r0 * SH + 1
	rm["iy1"] = KENAR + r0 * SH + 10


static func _sector_x0(c: int) -> int:
	return KENAR + c * SW


static func _sector_y0(r: int) -> int:
	return KENAR + r * SH


static func _room_box(rng: RandomNumberGenerator, rm: Dictionary, doors: Array) -> void:
	## Odanın kesim içindeki kutusu: yanlardan 0-4 karo daralır (kuyulu oda daha az: kuyu + ödül / tezgâh sığsın);
	## kesim başına taban satırı y0+8..y0+10 (yan yana kesimlerde en çok 2 karo fark), hava yüksekliği türe göre (YUK).
	_room_rect(rm)
	var nv := 0
	var has_l := false
	var has_r := false
	var v_alt := false   # v41: tabanda kuyu (oda aşağı açılır)
	var v_ust := false
	var pen_l := false   # v34: pencere yanı daralmaz (parmaklık ardındaki ödül yakından görünsün)
	var pen_r := false
	for di in rm["doors"]:
		var d: Dictionary = doors[di]
		if d["kind"] == "sil":
			continue
		if d["dir"] == "v":
			nv += 1
			if int(d["a"]) == int(rm["id"]):
				v_alt = true
			else:
				v_ust = true
		elif int(d["b"]) == int(rm["id"]):
			has_l = true
			pen_l = pen_l or d["kind"] == "pencere"
		else:
			has_r = true
			pen_r = pen_r or d["kind"] == "pencere"
	rm["_sol"] = has_l
	rm["_sag"] = has_r
	rm["_nv"] = nv
	rm["_valt"] = v_alt
	rm["_vust"] = v_ust
	var role: String = rm["role"]
	var maxs := 4
	if role == "giris" or nv >= 2:
		maxs = 0
	elif role == "odul":
		maxs = 0 if nv > 0 else 3
	elif nv == 1 or role == "cikis":
		maxs = 2
	elif (rm["cells"] as Array).size() == 1:
		maxs = 6
	var sl := rng.randi_range(0, maxs)
	var sr := rng.randi_range(0, maxs)
	rm["ix0"] = int(rm["ix0"]) + (0 if pen_l else sl)
	rm["ix1"] = int(rm["ix1"]) - (0 if pen_r else sr)
	var yk: Array = YUK.get("giris" if role == "giris" else String(rm["kind"]), [5, 8])
	var fbs: Array = []
	var hs: Array = []
	# v41 kısa kuyular: aşağı açılan odanın tabanı kesimin altında (9-10), yukarıdan girilen odanınki üstte (7-8): kuyu
	# 13-16 yerine 10-12 karo (eski türde değişmez)
	var f_lo := 0
	var f_hi := 3
	if _tur != "eski":
		if v_alt and not v_ust:
			f_lo = 2
		elif v_ust and not v_alt:
			f_hi = 1
	for c in range(int(rm["c0"]), int(rm["c1"]) + 1):
		var y0 := _sector_y0(int(rm["r0"]))
		var fb := y0 + 7 + rng.randi_range(f_lo, f_hi)
		if not fbs.is_empty():
			fb = clampi(fb, int(fbs[fbs.size() - 1]) - 2, int(fbs[fbs.size() - 1]) + 2)
		var hmax := mini(int(yk[1]), fb - (y0 + 1))
		fbs.append(fb)
		hs.append(rng.randi_range(mini(maxi(int(yk[0]) + 1, 6), hmax), hmax))   # oda koridordan (4) belirgin yüksek
	rm["fbs"] = fbs
	rm["hs"] = hs
	rm["fb"] = int(fbs[0])


static func _profile(rng: RandomNumberGenerator, rm: Dictionary, tavan: int) -> void:
	## fl[x] taban satırı (ilk katı), ce[x] tavan (ilk hava satırı). v33: taban kesim başına düz; geniş odada kesim
	## sınırında en çok 2 karoluk tek basamak; teras: kapısız yanda tek 2-3 karoluk seki. Mağara tavanı dalgalı.
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var n := ix1 - ix0 + 1
	var c0 := int(rm["c0"])
	var y0 := _sector_y0(int(rm["r0"]))
	var kind: String = rm["kind"]
	var fl: Array = []
	var ce: Array = []
	fl.resize(n)
	ce.resize(n)
	var p1 := rng.randf() * TAU
	var p2 := rng.randf() * TAU
	var amp := tavan + (1 if kind == "magara" else 0)
	for i in n:
		var k := clampi((ix0 + i - KENAR) / SW - c0, 0, (rm["fbs"] as Array).size() - 1)
		var f: int = int(rm["fbs"][k])
		fl[i] = f
		var cv: int = f - int(rm["hs"][k])
		if amp > 0 and not bool(rm["acik"]):
			cv -= int(round((sin(i * 0.31 + p1) + 1.0) * 0.5 * amp * (0.6 + 0.4 * sin(i * 0.13 + p2))))
		ce[i] = clampi(cv, y0 + 1, f - 5)
		if bool(rm["acik"]):
			ce[i] = 1
	if not bool(rm["acik"]) and _v43:
		# v43: tavan biçimi türe / biyoma göre (basamak / kemer / mağara / kırık çatı / tonoz)
		# ödül / pazar odası (tezgâh, kaide), çıkış ve ondan önceki iki oda (Otağ Yeri) basamaklı kalır
		var son_oda: bool = rm["role"] == "cikis" or bool(rm.get("_otag_yakin", false))
		var bic := _tavan_bicimi(rng, kind) if rm["role"] != "odul" and not son_oda else "basamak"
		rm["tavan_bicim"] = bic
		_tavan_uygula(rng, ce, fl, n, y0, bic)
	elif not bool(rm["acik"]):
		# basamaklı tavan (Dead Cells odalarının girintili çıkıntılı silueti): 4-9 sütunluk parçalar 0-3 karo alçalır;
		# %20 parça tavana açılan cep (3-5 karo yukarı)
		var x := 0
		while x < n:
			var ln := rng.randi_range(4, 9)
			var off := rng.randi_range(0, 3)
			if rng.randf() < 0.2:
				off = -rng.randi_range(3, 5)
			for i in range(x, mini(n, x + ln)):
				ce[i] = clampi(int(ce[i]) + off, y0 + 1, int(fl[i]) - 5)
			x += ln
	if kind == "teras" and n >= 14 and int(rm["_nv"]) == 0 and not (bool(rm["_sol"]) and bool(rm["_sag"])) and rm["role"] != "cikis":
		# tek seki: kapısız yanın 1/3-1/2'si 2-3 karo yüksek (tek zıplama)
		var raise_l: bool = not bool(rm["_sol"]) if bool(rm["_sag"]) else (rng.randf() < 0.5)
		var s := rng.randi_range(n / 3, n / 2)
		var dh := rng.randi_range(2, 3)
		for j in s:
			var i: int = j if raise_l else n - 1 - j
			fl[i] = int(fl[i]) - dh
			if not bool(rm["acik"]):
				ce[i] = mini(int(ce[i]), int(fl[i]) - 5)
	if _tur == "acik" and bool(rm["acik"]) and kind in ["tepe", "harabe"] and rm["role"] in ["ana", "dal"] and n >= 14:
		_arazi(rng, fl, n, y0)
	rm["fl"] = fl
	rm["ce"] = ce
	var lo := 999
	var hi := 0
	for i in n:
		lo = mini(lo, int(ce[i]))
		hi = maxi(hi, int(fl[i]))
	rm["iy0"] = lo
	rm["iy1"] = hi


static func _arazi(rng: RandomNumberGenerator, fl: Array, n: int, y0: int) -> void:
	## v41 açık yol arazisi: tabanı 3-7 sütunluk parçalarda 1 karo inip çıkan yumuşak tepeler (en çok 3 karo yukarı,
	## 1 karo çukur), arada 8-11 sütunluk düzlükler (anıt / dövüş alanı). Kenarlarda 5 sütun düz (kapı / geçit ağzı);
	## sona doğru temel yüksekliğe döner: her basamak tek zıplama, çoğu yürünerek çıkılan 1 karo.
	var kenar := 5
	var off := 0
	var i := kenar
	while i < n - kenar:
		var ln := rng.randi_range(3, 7)
		if rng.randf() < 0.22:
			ln = rng.randi_range(8, 11)
		var son := mini(n - kenar, i + ln)
		for j in range(i, son):
			fl[j] = clampi(int(fl[j]) + off, y0 + 5, y0 + 11)
		i = son
		var kalan := (n - kenar) - i
		if kalan <= absi(off) * 3 + 2:
			off -= signi(off)          # kenara yaklaşırken temel yüksekliğe dön
		else:
			var adim := -1 if rng.randf() < 0.6 else 1   # çoğunlukla yükselir (tepe)
			off = clampi(off + adim, -3, 1)


# ================================================================== v43 el yapımı oda şablonları
static func _sablon_sec(rng: RandomNumberGenerator, rm: Dictionary, kullan: Dictionary, simge_var: bool, n_yol: int) -> bool:
	## Ana yol / dal odası için uygun bir şablon (biyom, tür, rol, göğe açıklık, kapı / kuyu yuvaları; bölümde
	## kullanılmamış) seçer ve odaya uygular. Simge (sahne parçası) şablonu ana yolun orta yarısında bir kez.
	var role := String(rm["role"])
	if not (role in ["ana", "dal"]) or bool(rm.get("sapak", false)):
		return false
	var cells: Array = rm["cells"]
	if cells.size() > 2:
		return false
	var genis := cells.size() > 1
	var ai := int(rm.get("ana_i", -1))
	# Kut Kapısı'na giden son iki oda Otağ Yeri'dir (v42): yalnızca uzun düz tabanlı şablonlar
	var otag_yakin: bool = role == "ana" and ai >= n_yol - 3
	# simge: ana yolda (giriş / Kut Kapısı'na giden son iki oda dışında) ilk uygun oda; yoksa bir dal odası
	var simge_yer: bool = not simge_var and ((role == "ana" and ai >= 1 and not otag_yakin) or role == "dal")
	if not simge_yer and rng.randf() > SABLON_SANS:
		return false
	var cands: Array = []
	var simgeler: Array = []
	for t in OdaSablon.hepsi():
		if kullan.has(String(t["ad"])):
			continue
		if not OdaSablon.uygun(t, _biyom, _tur, role, bool(rm["acik"]), genis):
			continue
		if not OdaSablon.yuva_uyar(t, bool(rm["_sol"]), bool(rm["_sag"]), bool(rm["_vust"]), bool(rm["_valt"]), 5):
			continue
		if otag_yakin and (int(t["duz"]) < 10 or bool(t["simge"])):
			continue   # Otağ Yeri odaları: yalnızca uzun düz tabanlı şablon
		if bool(t["simge"]):
			if not simge_var:
				simgeler.append(t)
		else:
			cands.append(t)
	if simge_yer and not simgeler.is_empty() and rng.randf() < SIMGE_SANS:
		cands = simgeler
	if cands.is_empty():
		return false
	var top := 0.0
	for t in cands:
		top += float(t["agirlik"])
	var r := rng.randf() * top
	var sec: Dictionary = cands[cands.size() - 1]
	for t in cands:
		r -= float(t["agirlik"])
		if r <= 0.0:
			sec = t
			break
	kullan[String(sec["ad"])] = true
	_sablon_uygula(rng, rm, sec)
	return true


static func _sablon_uygula(rng: RandomNumberGenerator, rm: Dictionary, t: Dictionary) -> void:
	## Şablonu odanın kesimine yerleştirir (kapılı yana yaslı), taban / tavan profillerini (fl / ce) şablondan çıkarır.
	var w := int(t["w"])
	var maxw := 20 if w <= 20 else 44
	var bos := maxi(0, maxw - w)
	var xoff := rng.randi_range(0, bos)
	if bool(rm["_sol"]) and not bool(rm["_sag"]):
		xoff = rng.randi_range(0, mini(2, bos))
	elif bool(rm["_sag"]) and not bool(rm["_sol"]):
		xoff = bos - rng.randi_range(0, mini(2, bos))
	rm["_box"] = [int(rm["ix0"]), int(rm["ix1"])]
	rm["_kind0"] = rm["kind"]
	var x0 := _sector_x0(int(rm["c0"])) + 2 + xoff
	var y0 := _sector_y0(int(rm["r0"])) + 1
	rm["ix0"] = x0
	rm["ix1"] = x0 + w - 1
	rm["tpl"] = t
	rm["tpl_x0"] = x0
	rm["tpl_y0"] = y0
	rm["kind"] = String(t["tip"])
	var rows: Array = t["rows"]
	var h := int(t["h"])
	var fl: Array = []
	var ce: Array = []
	for i in w:
		var f := -1
		for y in range(h - 1, -1, -1):
			if OdaSablon.hucre(String(rows[y])[i]) == 0:
				var alt := 1 if y + 1 >= h else OdaSablon.hucre(String(rows[y + 1])[i])
				if alt == 1 or alt == 3:
					f = y0 + y + 1
					break
		if f < 0:
			f = y0 + h - 1
		var c := -1
		for y in h:
			if OdaSablon.hucre(String(rows[y])[i]) != 1:
				c = y0 + y
				break
		if c < 0 or c >= f:
			c = f - 1
		fl.append(f)
		ce.append(c)
	if int(t["L"]) >= 0:
		fl[0] = y0 + int(t["L"]) + 1
	if int(t["R"]) >= 0:
		fl[w - 1] = y0 + int(t["R"]) + 1
	rm["fl"] = fl
	rm["ce"] = ce
	var lo := 999
	var hi := 0
	for i in w:
		lo = mini(lo, int(ce[i]))
		hi = maxi(hi, int(fl[i]))
	rm["iy0"] = lo
	rm["iy1"] = hi
	var tt: Array = []
	for k in t["T"]:
		tt.append([x0 + int(k[0]), x0 + int(k[1])])
	var bb: Array = []
	for k in t["B"]:
		bb.append([x0 + int(k[0]), x0 + int(k[1]), y0 + int(k[2])])
	rm["tpl_T"] = tt
	rm["tpl_B"] = bb
	var isr: Array = []
	for m in t["isaret"]:
		isr.append([String(m[0]), x0 + int(m[1]), y0 + int(m[2])])
	rm["isaret"] = isr


static func _sablon_geri(rng: RandomNumberGenerator, rm: Dictionary, tavan: int) -> void:
	## Şablon dikey geçide yer vermiyorsa oda yordamsal kutusuna döner
	var b: Array = rm["_box"]
	rm["ix0"] = int(b[0])
	rm["ix1"] = int(b[1])
	rm["kind"] = rm["_kind0"]
	for k in ["tpl", "tpl_x0", "tpl_y0", "tpl_T", "tpl_B", "isaret", "_box", "_kind0"]:
		rm.erase(k)
	_profile(rng, rm, tavan)


static func _sablon_kuyu_denetle(rng: RandomNumberGenerator, rooms: Array, doors: Array, tavan: int) -> void:
	## Her dikey kapıda iki odanın yuvaları en az 5 sütun örtüşmeli; örtüşmüyorsa (simge olmayan) şablon geri alınır
	for it in 4:
		var degisti := false
		for d in doors:
			if d["kind"] == "sil" or d["dir"] != "v":
				continue
			var A: Dictionary = rooms[int(d["a"])]
			var B: Dictionary = rooms[int(d["b"])]
			if not (A.has("tpl") or B.has("tpl")):
				continue
			var sx := _sector_x0((d["ca"] as Vector2i).x)
			var ok := false
			for ia in _kuyu_araliklari(A, true):
				for ib in _kuyu_araliklari(B, false):
					var lo := maxi(maxi(int(ia[0]), int(ib[0])), maxi(maxi(int(A["ix0"]), int(B["ix0"])) + 2, sx + 4))
					var hi := mini(mini(int(ia[1]), int(ib[1])), mini(mini(int(A["ix1"]), int(B["ix1"])) - 2, sx + SW - 5))
					if hi - lo + 1 >= 5:
						ok = true
			if ok:
				continue
			var R: Dictionary = A
			if not A.has("tpl") or (B.has("tpl") and bool(A["tpl"]["simge"])):
				R = B
			_sablon_geri(rng, R, tavan)
			degisti = true
		if not degisti:
			break


static func _sablon_oy(g: PackedByteArray, W: int, H: int, rm: Dictionary) -> void:
	## Şablonu ızgaraya basar; göğe açık odada en üst havanın üstü göğe dek açılır
	var t: Dictionary = rm["tpl"]
	var rows: Array = t["rows"]
	var x0 := int(rm["tpl_x0"])
	var y0 := int(rm["tpl_y0"])
	for yy in int(t["h"]):
		var s: String = rows[yy]
		for xx in int(t["w"]):
			var c := s[xx]
			if c == " ":
				continue
			_put(g, x0 + xx, y0 + yy, W, H, OdaSablon.hucre(c))
	if bool(rm["acik"]):
		# göğe açık: şablonun 0. satırı hava olan sütunlarda üstü göğe dek açılır (çatı / gövde çizilen sütunlar kalır)
		var r0: String = rows[0]
		for xx in int(t["w"]):
			if OdaSablon.hucre(r0[xx]) == 0:
				for y in range(1, y0):
					_put(g, x0 + xx, y, W, H, 0)


static func _propler(rooms: Array, doors: Array) -> Dictionary:
	## v43 şablon süsleri (Level / GecitCiz çizer): kütük köprüler, tırmanılır sarkıtlar, yumuşak yığınlar, su, asılı
	## süsler, simge çapası, yaratık / ganimet işaretleri
	var out := {"kutuk": [], "tirman": [], "yumusak": [], "su": [], "sus": [], "simge": [], "ganimet": []}
	for rm in rooms:
		if not rm.has("tpl"):
			continue
		var t: Dictionary = rm["tpl"]
		var rows: Array = t["rows"]
		var x0 := int(rm["tpl_x0"])
		var y0 := int(rm["tpl_y0"])
		var h := int(t["h"])
		for yy in h:
			var s: String = rows[yy]
			var xa := -1
			for xx in int(t["w"]) + 1:
				var on: bool = xx < int(t["w"]) and s[xx] == "="
				if on and xa < 0:
					xa = xx
				elif not on and xa >= 0:
					out["kutuk"].append([x0 + xa, x0 + xx - 1, y0 + yy, int(rm["id"])])
					xa = -1
		var su_satir := {}
		for m in t["isaret"]:
			var c := String(m[0])
			var mx := int(m[1])
			var my := int(m[2])
			match c:
				"t":
					var ust := my
					while ust > 0 and OdaSablon.hucre(String(rows[ust - 1])[mx]) != 1:
						ust -= 1
					var alt := my
					while alt + 1 < h and OdaSablon.hucre(String(rows[alt + 1])[mx]) == 0:
						alt += 1
					out["tirman"].append([float(x0 + mx) + 0.05, float(y0 + ust), float(x0 + mx) + 0.95, float(y0 + alt + 1)])
				"~":
					var alt2 := my
					while alt2 + 1 < h and OdaSablon.hucre(String(rows[alt2 + 1])[mx]) == 0:
						alt2 += 1
					out["yumusak"].append([x0 + mx, x0 + mx, y0 + alt2 + 1])
				"w":
					su_satir[my] = (su_satir.get(my, []) as Array) + [mx]
				"d":
					var ust2 := my
					while ust2 > 0 and OdaSablon.hucre(String(rows[ust2 - 1])[mx]) != 1:
						ust2 -= 1
					out["sus"].append([x0 + mx, y0 + my, y0 + ust2, int(rm["id"])])
				"*":
					out["simge"].append([x0 + mx, y0 + my, int(rm["id"])])
				"$":
					out["ganimet"].append([x0 + mx, y0 + my, int(rm["id"])])
		for sy in su_satir:
			var xs: Array = su_satir[sy]
			xs.sort()
			var a := int(xs[0])
			var p := a
			for k in range(1, xs.size() + 1):
				if k < xs.size() and int(xs[k]) == p + 1:
					p = int(xs[k])
					continue
				var dip := int(sy)
				while dip + 1 < h and OdaSablon.hucre(String(rows[dip + 1])[a]) == 0:
					dip += 1
				out["su"].append([x0 + a, x0 + p, y0 + int(sy), y0 + dip + 1])
				if k < xs.size():
					a = int(xs[k])
					p = a
	return out


static func _tavan_bicimi(rng: RandomNumberGenerator, kind: String) -> String:
	## v43 yordamsal oda tavanı: tür + biyoma göre basamak / kemer / mağara / kırık çatı / tonoz
	var ag := {"basamak": 0.35, "kemer": 0.35, "tonoz": 0.15, "kirik": 0.15}
	if kind in ["magara", "kuyu"]:
		ag = {"magara": 0.6, "kirik": 0.2, "basamak": 0.2}
	elif kind in ["harabe", "kule", "avlu"]:
		ag = {"kemer": 0.3, "tonoz": 0.3, "kirik": 0.25, "basamak": 0.15}
	elif kind in ["cukur", "kopru"]:
		ag = {"magara": 0.3, "kirik": 0.3, "basamak": 0.2, "kemer": 0.2}
	if _biyom == "sahmeran":
		ag["magara"] = float(ag.get("magara", 0.0)) + 0.5
	elif _biyom == "tamu":
		ag["kirik"] = float(ag.get("kirik", 0.0)) + 0.25
		ag["tonoz"] = float(ag.get("tonoz", 0.0)) + 0.2
	elif _biyom == "kaf":
		ag["magara"] = float(ag.get("magara", 0.0)) + 0.25
	var top := 0.0
	for k in ag:
		top += float(ag[k])
	var r := rng.randf() * top
	for k in ag:
		r -= float(ag[k])
		if r <= 0.0:
			return String(k)
	return "basamak"


static func _tavan_uygula(rng: RandomNumberGenerator, ce: Array, fl: Array, n: int, y0: int, bic: String) -> void:
	match bic:
		"kemer":
			# kemer: duvar diplerinde alçak, ortada yüksek
			var ah := rng.randi_range(2, 4)
			for i in n:
				var k := sin(PI * (float(i) + 0.5) / float(n))
				ce[i] = clampi(int(ce[i]) + 2 - int(round(pow(k, 0.6) * float(ah + 2))), y0 + 1, int(fl[i]) - 5)
		"magara":
			# mağara: düzensiz, sivri tavan (her sütunda -1 / 0 / +1 yürüyüş, ara ara 2 karoluk sarkıt dişi)
			var off := 0
			for i in n:
				off = clampi(off + rng.randi_range(-1, 1), -3, 2)
				var dis := 2 if rng.randf() < 0.08 else 0
				ce[i] = clampi(int(ce[i]) + off + dis, y0 + 1, int(fl[i]) - 5)
		"kirik":
			# kırık çatı: tek basamak + 1-2 çökük delik (yukarı 3-5 karo, kenarları dişli)
			var x := 0
			var off2 := rng.randi_range(0, 2)
			while x < n:
				var ln := rng.randi_range(5, 10)
				for i in range(x, mini(n, x + ln)):
					ce[i] = clampi(int(ce[i]) + off2, y0 + 1, int(fl[i]) - 5)
				off2 = rng.randi_range(0, 2)
				x += ln
			for k in rng.randi_range(1, 2):
				var hw := rng.randi_range(2, 4)
				var hx := rng.randi_range(2, maxi(2, n - hw - 3))
				var hh := rng.randi_range(3, 5)
				for i in range(hx, mini(n, hx + hw)):
					var e := hh - (1 if (i == hx or i == hx + hw - 1) and rng.randf() < 0.6 else 0)
					ce[i] = clampi(int(ce[i]) - e, y0 + 1, int(fl[i]) - 5)
		"tonoz":
			# tonoz: art arda kemerler (5-8 sütunluk), aralarda sarkan kemer ayakları
			var p := rng.randi_range(5, 8)
			var faz := rng.randi_range(0, p - 1)
			for i in n:
				var k := absf(sin(PI * float(i + faz) / float(p)))
				ce[i] = clampi(int(ce[i]) + int(round((1.0 - k) * 2.5)) - 1, y0 + 1, int(fl[i]) - 5)
		_:
			var x2 := 0
			while x2 < n:
				var ln2 := rng.randi_range(4, 9)
				var off3 := rng.randi_range(0, 3)
				if rng.randf() < 0.2:
					off3 = -rng.randi_range(3, 5)
				for i in range(x2, mini(n, x2 + ln2)):
					ce[i] = clampi(int(ce[i]) + off3, y0 + 1, int(fl[i]) - 5)
				x2 += ln2


static func _ritim(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary) -> void:
	## v43 platform ritmi: yüksek odada yükselen 2-3 tek yönlü basamak dizisi (her biri 3 karo yukarı, 3-4 sütun öteye;
	## 2-4 karo uzun), merdiven gibi değil, düzensiz bir tırmanış
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	for t in 8:
		var x := rng.randi_range(ix0 + 2, ix1 - 6)
		var yon := 1 if rng.randf() < 0.5 else -1
		var n := rng.randi_range(2, 3)
		var fy := int(fl[x - ix0])
		var ok := true
		var parca: Array = []
		var cx := x
		for k in n:
			var ln := rng.randi_range(2, 4)
			var y := fy - 3 * (k + 1)
			var a := cx if yon > 0 else cx - ln + 1
			if a < ix0 + 1 or a + ln - 1 > ix1 - 1:
				ok = false
				break
			for xx in range(a, a + ln):
				if int(fl[xx - ix0]) != fy:
					ok = false
			if not ok or not _free_span(g, W, H, rm, a, y, ln, 3, 2):
				ok = false
				break
			parca.append([a, ln, y])
			cx = (a + ln - 1 + rng.randi_range(2, 3)) if yon > 0 else (a - rng.randi_range(2, 3))
		if not ok or parca.size() < 2:
			continue
		for p in parca:
			for xx in range(int(p[0]), int(p[0]) + int(p[1])):
				_put(g, xx, int(p[2]), W, H, 2)
		return


# ================================================================== kapılar
static func _door_geometry(rng: RandomNumberGenerator, rooms: Array, d: Dictionary, gecit_kul: Dictionary = {}) -> void:
	## Yan kapı: A'nın sağ kenarından B'nin sol kenarına koridor; taban satırı yd iki odanın kapı yanındaki tabanından
	## yüksek olanı (öbür yanda en çok 2-3 karoluk eşik), 4-5 karo yüksek. Dikey kapı: kuyu (bkz. dosya başı).
	## v43: koridor 3-7 karo yüksek, tavanı düz / kemer / kırık, iki taban arası 1 karoluk basamaklarla (eşik yok; ödül /
	## pencere koridoru eskisi gibi düz ve 4 karo: zamanlı / kilitli kapı); dikey kapı biyoma göre geçit türü (GecitGen).
	if d["kind"] == "sil":
		return
	var A: Dictionary = rooms[int(d["a"])]
	var B: Dictionary = rooms[int(d["b"])]
	if d["dir"] == "h":
		var fa: int = int(A["fl"][(A["fl"] as Array).size() - 1])
		var fbv: int = int(B["fl"][0])
		var yd := mini(fa, fbv)
		var odul_k: bool = A["role"] == "odul" or B["role"] == "odul"
		var ch := 4 if (odul_k or rng.randf() < 0.8) else 5
		d["x"] = int(A["ix1"]) + 1
		d["x2"] = int(B["ix0"]) - 1
		d["y"] = yd
		if _v43 and not odul_k and d["kind"] != "pencere":
			# v43 koridor çeşitliliği: kısa sıkışık geçit (3), olağan (4-5), yüksek kemerli geçit (6-7)
			var ln := int(d["x2"]) - int(d["x"]) + 1
			var rr := rng.randf()
			if rr < 0.14 and ln <= 10 and absi(fa - fbv) <= 1:
				ch = 3
			elif rr < 0.5:
				ch = 4
			elif rr < 0.76:
				ch = 5
			else:
				ch = rng.randi_range(6, 7)
			d["rampa"] = fa != fbv
			d["tavan"] = ["duz", "kemer", "kirik", "kemer", "kirik"][rng.randi_range(0, 4)] if ln >= 6 and ch >= 4 else "duz"
		d["h"] = ch
		var mh := ch + (2 if String(d.get("tavan", "duz")) == "kemer" else 0)
		(A["clear"] as Array).append(Rect2i(int(A["ix1"]) - 3, yd - mh - 1, 4, fa - yd + mh + 1))
		(B["clear"] as Array).append(Rect2i(int(B["ix0"]), yd - mh - 1, 4, fbv - yd + mh + 1))
		# v41: iki göğe açık yol odası arasında geçit de göğe açık (tünel değil: kesintisiz yer yüzü); ödül odası,
		# pencere ve kilit / zamanlı kapı yerleri tünel kalır
		d["acik_ust"] = _tur == "acik" and bool(A["acik"]) and bool(B["acik"]) and A["role"] != "odul" and B["role"] != "odul" and d["kind"] != "pencere"
		if d["kind"] == "pencere":
			return   # v34: pencere ödül odasının kapısı değil (kapı yanı / zamanlı kapı / Kut Taşı yeri gerçek kapıdan)
		if A["role"] == "odul":
			A["_door_side"] = "sag"
			A["_door_x"] = int(d["x"])
		if B["role"] == "odul":
			B["_door_side"] = "sol"
			B["_door_x"] = int(d["x2"])
	else:
		var ca: Vector2i = d["ca"]
		var sx := _sector_x0(ca.x)
		# ana yol yukarıdan aşağı iniyorsa düşüş deliği açık; dal / döngü / tırmanılan ana yol: tek yönlü kapak
		d["acik"] = d["kind"] == "ana" and int(A["ana_i"]) >= 0 and int(B["ana_i"]) > int(A["ana_i"])
		# v34: uzantı (sapaktan sonra süren yol) aşağı iniyorsa açık düşüş (yol gibi görünür); Kut Kapısı sapağı kapaklı
		if d["kind"] == "uzanti" and d.get("ileri", Vector2i(-1, -1)) == d["cb"]:
			d["acik"] = true
		if bool(d.get("kapak", false)):
			d["acik"] = false
		var tipler: Array = ["kuyu"]
		if _v43:
			# düşüş deliği (geri dönüşsüz) yalnız aşağı inen ana yolda, ödül / sapak odasına değil
			var dusus_ok: bool = bool(d["acik"]) and d["kind"] == "ana" and B["role"] != "odul" and not bool(B.get("sapak", false)) and not bool(A.get("kavsak", false))
			tipler = GecitGen.sirala(rng, _biyom, _tur, gecit_kul, dusus_ok)
			tipler.append("kuyu")
		var hx := -1
		var gw := KUYU_W
		var tip := "kuyu"
		# dört geçiş: (1) iki taban geçit boyunca düz, (2) düz değil (taban geçidin dibine indirilir), (3) şablon yuvası
		# dışında da (şablonu keser), (4) v33 kuyusu yedek
		for gecis in 4:
			for ti in tipler.size():
				var t2 := String(tipler[ti])
				if (gecis < 3 and t2 == "kuyu" and tipler.size() > 1) or (gecis == 3 and t2 != "kuyu"):
					continue
				var gw2 := int(GecitGen.GENISLIK[t2])
				if gecis < 3 and t2 in ["cikinti", "ruzgar", "merdiven", "iskele"] and (A["role"] == "cikis" or B["role"] == "cikis"):
					continue   # Kut Kapısı odasında dar geçit (Otağ Yeri'ne düz taban kalsın)
				var cands := _kuyu_adaylari(A, B, sx, gw2, gecis == 0 and _v43, gecis >= 2 or not _v43)
				if _v43 and gecis < 3:
					for R in [A, B]:
						if R["role"] == "odul" and String(R.get("odul", "")) == "pazar":
							# pazar: tezgâh (11 karo) geçidin bir yanına sığmalı
							var c2: Array = []
							for cx in cands:
								if maxi(int(cx) - int(R["ix0"]), int(R["ix1"]) - (int(cx) + gw2 - 1)) >= 13:
									c2.append(cx)
							cands = c2
				if cands.is_empty():
					continue
				tip = t2
				gw = gw2
				hx = int(cands[rng.randi_range(0, cands.size() - 1)])
				if A["role"] == "odul" or B["role"] == "odul":
					hx = int(cands[0]) if rng.randf() < 0.5 else int(cands[cands.size() - 1])   # ödül / tezgâh öbür yana sığsın
					if _v43 and (String(A.get("odul", "")) == "pazar" or String(B.get("odul", "")) == "pazar"):
						hx = int(cands[0])   # v43: pazar: geçit sol uçta, tezgâh sağda (sol kanadı geniş)
				break
			if hx >= 0:
				break
		if hx < 0:
			hx = maxi(maxi(int(A["ix0"]), int(B["ix0"])), sx + 2) + 2
			tip = "kuyu"
			gw = KUYU_W
		gecit_kul[tip] = int(gecit_kul.get(tip, 0)) + 1
		d["x"] = hx
		d["gw"] = gw
		d["gecit"] = tip
		d["y"] = int(A["fl"][clampi(hx - int(A["ix0"]), 0, (A["fl"] as Array).size() - 1)])
		d["flip"] = rng.randf() < 0.5
		if _v43:
			d["flip2"] = rng.randf() < 0.5
			var gl: Array = []
			for k in 6:
				gl.append(rng.randi_range(2, 3))
			d["genislikler"] = gl
			# zincirin asıldığı yer: üst odanın tavanı (göğe açıksa 7 karo yukarıda kiriş)
			var ce_a: int = int(A["ce"][clampi(hx + gw / 2 - int(A["ix0"]), 0, (A["ce"] as Array).size() - 1)])
			d["capa"] = int(d["y"]) - 7 if bool(A["acik"]) else maxi(ce_a, int(d["y"]) - 9)
		for R in [A, B]:
			(R["kuyular"] as Array).append([hx, hx + gw - 1])
			(R["clear"] as Array).append(Rect2i(hx - 1, 0, gw + 2, 999))
		if A["role"] == "odul":
			A["_door_side"] = "alt"
			A["_door_x"] = hx
			A["_door_w"] = gw
		if B["role"] == "odul":
			B["_door_side"] = "ust"
			B["_door_x"] = hx
			B["_door_w"] = gw


static func _kuyu_araliklari(R: Dictionary, ust_oda: bool) -> Array:
	## v43: odanın dikey geçide verebileceği sütun aralıkları: şablon odasında taban (B) / tavan (T) yuvaları, yordamsal
	## odada iç alan
	if R.has("tpl"):
		var out: Array = []
		for k in (R["tpl_B"] if ust_oda else R["tpl_T"]):
			out.append([int(k[0]), int(k[1])])
		return out
	return [[int(R["ix0"]) + 2, int(R["ix1"]) - 2]]


static func _kuyu_adaylari(A: Dictionary, B: Dictionary, sx: int, gw: int, duz_iste: bool, yuva_yok := false) -> Array:
	## Geçidin sol sütunu adayları: iki odanın ortak iç alanı (v33 kuralları: giriş doğuşu / Kut Kapısı uzak, başka
	## kuyuya 3 karo yaklaşmaz); v43: şablon yuvalarının içinde, iki tabanı geçit boyunca düz (duz_iste)
	var lo := maxi(maxi(int(A["ix0"]), int(B["ix0"])), sx + 2) + 2
	var hi := mini(mini(int(A["ix1"]), int(B["ix1"])), sx + SW - 3) - 2 - (gw - 1)
	for R in [A, B]:
		if R["role"] == "giris":
			lo = maxi(lo, int(R["ix0"]) + 11)   # doğuş yeri ve giriş taşı (ix0+3, ix0+9) düz kalsın
		if R["role"] == "cikis" and int(R["c1"]) == (sx - KENAR) / SW:
			hi = mini(hi, int(R["ix1"]) - 8 - (gw - 1))   # Kut Kapısı (ix1-4) kuyudan uzak
	var ivA := _kuyu_araliklari(A, true)
	var ivB := _kuyu_araliklari(B, false)
	var cands: Array = []
	for hx in range(lo, maxi(lo, hi) + 1):
		if hx > hi and not yuva_yok:
			break
		var ok := true
		for R in [A, B]:
			for k in R["kuyular"]:
				if hx <= int(k[1]) + 3 and hx + gw - 1 >= int(k[0]) - 3:
					ok = false
		if not ok:
			continue
		if _v43 and not yuva_yok:
			var ia := false
			for iv in ivA:
				if hx >= int(iv[0]) and hx + gw - 1 <= int(iv[1]):
					ia = true
			var ib := false
			for iv in ivB:
				if hx >= int(iv[0]) and hx + gw - 1 <= int(iv[1]):
					ib = true
			if not (ia and ib):
				continue
		if duz_iste and _v43:
			for R in [A, B]:
				var fl: Array = R["fl"]
				var f0 := int(fl[clampi(hx - int(R["ix0"]), 0, fl.size() - 1)])
				for x in range(hx - 1, hx + gw + 1):
					if int(fl[clampi(x - int(R["ix0"]), 0, fl.size() - 1)]) != f0:
						ok = false
			if not ok:
				continue
		cands.append(hx)
	return cands


static func _carve_door(g: PackedByteArray, W: int, H: int, rooms: Array, d: Dictionary) -> void:
	if d["kind"] == "sil":
		return
	var A: Dictionary = rooms[int(d["a"])]
	var B: Dictionary = rooms[int(d["b"])]
	if d["dir"] == "h" and bool(d.get("acik_ust", false)):
		# v41 açık geçit: iki odanın kenar tabanı arasında 1 karoluk basamaklarla eğim, üstü göğe dek açık
		var fa: int = int(A["fl"][(A["fl"] as Array).size() - 1])
		var fbv: int = int(B["fl"][0])
		var x0 := int(A["ix1"]) + 1
		var x1 := int(B["ix0"]) - 1
		for x in range(x0, x1 + 1):
			var t := float(x - x0 + 1) / float(x1 - x0 + 2)
			var fy := int(round(lerpf(float(fa), float(fbv), t)))
			for y in range(1, fy):
				_put(g, x, y, W, H, 0)
			_put(g, x, fy, W, H, 1)
		return
	if d["dir"] == "h":
		var yd := int(d["y"])
		var ch := int(d["h"])
		if _v43 and (bool(d.get("rampa", false)) or String(d.get("tavan", "duz")) != "duz"):
			_carve_koridor(g, W, H, A, B, d)
			return
		# koridor + iki odanın kenarındaki ağız (oda tavanı alçaksa da geçit açık)
		for x in range(int(A["ix1"]) - 1, int(B["ix0"]) + 2):
			for y in range(yd - ch, yd):
				_put(g, x, y, W, H, 0)
		for x in range(int(d["x"]), int(d["x2"]) + 1):
			_put(g, x, yd, W, H, 1)
		if d["kind"] == "pencere":
			# v34 parmaklıklı pencere: koridorun ortasındaki sütun ızgarada katı (geçilmez; erişim modeli de duvar
			# sayar); Level karosunu siler, yerine görünür demir parmaklık + çarpışma kutusu koyar
			var bx := (int(d["x"]) + int(d["x2"])) / 2
			var cells: Array = []
			for y in range(yd - ch, yd):
				_put(g, bx, y, W, H, 1)
				cells.append(Vector2i(bx, y))
			d["parmak"] = cells
	else:
		var hx := int(d["x"])
		var fyA: int = int(A["fl"][clampi(hx - int(A["ix0"]), 0, (A["fl"] as Array).size() - 1)])
		var fyB: int = int(B["fl"][clampi(hx - int(B["ix0"]), 0, (B["fl"] as Array).size() - 1)])
		d["y"] = fyA
		d["y2"] = fyB
		var flip: bool = d["flip"]
		if String(d.get("gecit", "kuyu")) != "kuyu":
			# v43 geçit türü: kendi biçimi (GecitGen.oy); harita "?" işareti düşüş yolunun ortasında. Taban geçit
			# boyunca düz değilse üst oda tabanı geçidin ağzında en alçak satıra iner (ağız kapanmasın)
			var gw0 := int(d["gw"])
			for x in range(hx, hx + gw0):
				fyA = maxi(fyA, int(A["fl"][clampi(x - int(A["ix0"]), 0, (A["fl"] as Array).size() - 1)]))
				fyB = maxi(fyB, int(B["fl"][clampi(x - int(B["ix0"]), 0, (B["fl"] as Array).size() - 1)]))
			for x in range(hx, hx + gw0):
				for y in range(int(A["fl"][clampi(x - int(A["ix0"]), 0, (A["fl"] as Array).size() - 1)]), fyA):
					_put(g, x, y, W, H, 0)
			d["y"] = fyA
			d["y2"] = fyB
			var gv := GecitGen.oy(g, W, H, d, _biyom)
			d["gecit_veri"] = gv
			d["dus_x"] = int(gv["lane"][0])
			d["tir_x"] = int(gv["x0"])
			return
		var dx0 := hx + 3 if flip else hx          # düşüş bacası (3)
		var wx := hx + 2 if flip else hx + 3       # ara duvar (1)
		var cx0 := hx if flip else hx + 4          # tırmanış bacası (2)
		d["dus_x"] = dx0
		d["tir_x"] = cx0
		for x in range(dx0, dx0 + 3):
			for y in range(fyA, fyB):
				_put(g, x, y, W, H, 0)
			if not bool(d["acik"]):
				_put(g, x, fyA, W, H, 2)   # kapak: üstünden yürünür, aşağı + zıpla ile düşülür
		for x in range(cx0, cx0 + 2):
			for y in range(fyA + 1, fyB):
				_put(g, x, y, W, H, 0)
			_put(g, x, fyA, W, H, 2)
		for y in range(fyA, fyB - 3):
			_put(g, wx, y, W, H, 1)
		# tırmanış basamakları: tepeden 3 satırda bir; tabana 4 kalırsa ara basamak (2)
		var rungs: Array = []
		var r := fyA
		while fyB - (r + 3) >= 2:
			r += 3
			rungs.append(r)
		if fyB - r == 4:
			rungs.append(fyB - 2)
		for ry in rungs:
			for x in range(cx0, cx0 + 2):
				_put(g, x, ry, W, H, 2)


static func _carve_koridor(g: PackedByteArray, W: int, H: int, A: Dictionary, B: Dictionary, d: Dictionary) -> void:
	## v43 koridor: taban iki odanın kenar tabanı arasında 1 karoluk basamaklarla (yürürken kendiliğinden çıkılır), tavan
	## düz / kemer (ortası 1-2 karo yüksek) / kırık (2-3 sütunda bir 0-1 karo oynar); her sütunda en az ch karo hava
	var fa: int = int(A["fl"][(A["fl"] as Array).size() - 1])
	var fbv: int = int(B["fl"][0])
	var ch := int(d["h"])
	var x0 := int(d["x"])
	var x1 := int(d["x2"])
	var n := x1 - x0 + 1
	var bic := String(d.get("tavan", "duz"))
	var ramp: bool = bool(d.get("rampa", false))
	var kirik := 0
	var hseed := (x0 * 73856093) ^ (int(d["y"]) * 19349663)
	var prev_fy := fa
	for i in range(-2, n + 2):
		var x := x0 + i
		var t := clampf(float(i + 1) / float(n + 1), 0.0, 1.0)
		var fy := int(d["y"])
		if ramp:
			fy = int(round(lerpf(float(fa), float(fbv), t))) if i >= 0 and i < n else (fa if i < 0 else fbv)
			if i >= 0 and i < n:
				fy = clampi(fy, prev_fy - 1, prev_fy + 1)
				prev_fy = fy
		var ek := 0
		if i >= 0 and i < n:
			match bic:
				"kemer":
					ek = int(round(sin(PI * t) * (2.0 if n >= 9 else 1.0)))
				"kirik":
					if i % 2 == 0:
						kirik = ((hseed >> (i % 16)) & 1)
					ek = kirik
		var top := fy - ch - ek
		if i < 0 or i >= n:
			top = mini(top, int(d["y"]) - ch)
		for y in range(top, fy):
			_put(g, x, y, W, H, 0)
		if i >= 0 and i < n:
			_put(g, x, fy, W, H, 1)
			for y in range(fy + 1, fy + 4):
				if y < H - 1 and _cell(g, x, y, W, H) == 0:
					_put(g, x, y, W, H, 1)


# ================================================================== oda oyma ve süsler
static func _carve_room(g: PackedByteArray, W: int, H: int, rm: Dictionary) -> void:
	if rm.has("tpl"):
		_sablon_oy(g, W, H, rm)
		return
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	var ce: Array = rm["ce"]
	for x in range(ix0, ix1 + 1):
		var i := x - ix0
		for y in range(int(ce[i]), int(fl[i])):
			_put(g, x, y, W, H, 0)


static func _in_clear(rm: Dictionary, x: int, y: int) -> bool:
	for c in rm["clear"]:
		if (c as Rect2i).has_point(Vector2i(x, y)):
			return true
	return false


static func _bos_sutun(rm: Dictionary, x: int) -> int:
	## x'e en yakın, kuyu / kapı ağzı bölgesine girmeyen sütun (taban hizasında)
	var fl: Array = rm["fl"]
	for d in range(0, 20):
		for s in ([0] if d == 0 else [1, -1]):
			var cx := clampi(x + d * s, int(rm["ix0"]) + 1, int(rm["ix1"]) - 1)
			if not _in_clear(rm, cx, int(fl[cx - int(rm["ix0"])]) - 1):
				return cx
	return x


static func _free_span(g: PackedByteArray, W: int, H: int, rm: Dictionary, x0: int, y: int, ln: int, up: int, down: int) -> bool:
	## x0..x0+ln-1 sütunlarında y satırı ve üstünde up, altında down satır hava mı; temiz bölgeye girmiyor mu
	for x in range(x0 - 1, x0 + ln + 1):
		if x < int(rm["ix0"]) or x > int(rm["ix1"]):
			return false
		for yy in range(y - up, y + down + 1):
			if _cell(g, x, yy, W, H) != 0 or _in_clear(rm, x, yy):
				return false
	return true


static func _features(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, style: String) -> void:
	## Oda türüne göre iç parçalar (küçük odaya ölçekli): tek yönlü platformlar (tabandan 3 karo: tek zıplama),
	## sütunlar, kemer, sarkıtlar, kayalar, yan cepler, çukur, köprü, üst güverte
	var kind: String = rm["kind"]
	var role: String = rm["role"]
	if rm.has("tpl"):
		return   # v43: el yapımı oda: iç parçalar şablonun kendisi
	if role == "odul":
		_odul_shape(g, W, H, rng, rm)
		return
	if role == "giris":
		_platforms(g, W, H, rng, rm, 1, 3, 3)
		_alcoves(g, W, H, rng, rm, rng.randi_range(0, 1))
		return
	var kx := 2 if (rm["cells"] as Array).size() > 1 else 1
	if _v43 and kind in ["salon", "harabe", "kule", "avlu", "magara", "teras"] and rng.randf() < 0.4:
		_ritim(g, W, H, rng, rm)   # v43: yükselen düzensiz platform dizisi
	match kind:
		"salon":
			_platforms(g, W, H, rng, rm, rng.randi_range(1, 2) * kx, 3, 3)
			_pillars(g, W, H, rng, rm, rng.randi_range(0, 1) * kx)
			_dips(g, W, H, rng, rm, rng.randi_range(0, 1))
			_alcoves(g, W, H, rng, rm, rng.randi_range(0, 1))
			_stalactites(g, W, H, rng, rm, rng.randi_range(0, 1) * kx, 2)
		"teras":
			_platforms(g, W, H, rng, rm, rng.randi_range(1, 2) * kx, 3, 3)
			_alcoves(g, W, H, rng, rm, rng.randi_range(0, 1))
		"harabe":
			_pillars(g, W, H, rng, rm, rng.randi_range(1, 2) * kx)
			_arches(g, W, H, rng, rm, rng.randi_range(0, 1) * kx)
			_platforms(g, W, H, rng, rm, rng.randi_range(0, 1) * kx, 3, 3)
			_alcoves(g, W, H, rng, rm, rng.randi_range(0, 1))
			_stalactites(g, W, H, rng, rm, rng.randi_range(0, 1), 2)
		"magara":
			_stalactites(g, W, H, rng, rm, rng.randi_range(2, 4) * kx, 2)
			_boulders(g, W, H, rng, rm, rng.randi_range(1, 3) * kx)
			_platforms(g, W, H, rng, rm, rng.randi_range(0, 1) * kx, 3, 3)
			_alcoves(g, W, H, rng, rm, rng.randi_range(1, 2))
		"cukur":
			_pit(g, W, H, rng, rm)
			_platforms(g, W, H, rng, rm, rng.randi_range(0, 1) * kx, 3, 3)
			_stalactites(g, W, H, rng, rm, rng.randi_range(0, 1), 2)
		"kopru":
			_bridge(g, W, H, rng, rm)
			_stalactites(g, W, H, rng, rm, rng.randi_range(0, 1), 2)
		"kuyu":
			_deck(g, W, H, rng, rm)
			_alcoves(g, W, H, rng, rm, rng.randi_range(0, 1))
			_stalactites(g, W, H, rng, rm, rng.randi_range(0, 2) * kx, 2)
		"kule":
			_pillars(g, W, H, rng, rm, 1 * kx)
			_platforms(g, W, H, rng, rm, rng.randi_range(1, 2) * kx, 3, 4)
			_alcoves(g, W, H, rng, rm, rng.randi_range(0, 1))
		"tepe":
			# v41 açık yol: tepeler (_arazi), yarık, gözcü iskelesi, kayalar, tek yönlü çıkıntılar
			if rng.randf() < 0.45:
				_yarik(g, W, H, rng, rm)
			if rng.randf() < 0.4:
				_iskele(g, W, H, rng, rm)
			_boulders(g, W, H, rng, rm, rng.randi_range(0, 2) * kx)
			_platforms(g, W, H, rng, rm, rng.randi_range(0, 1) * kx, 3, 3)
		"avlu":
			# v41 kale avlusu (arena): yüksek, düz; iki yanda tek yönlü seyir sekileri, kemer, sütun
			_platforms(g, W, H, rng, rm, 2 * kx, 3, 4)
			_arches(g, W, H, rng, rm, rng.randi_range(0, 1) * kx)
			_pillars(g, W, H, rng, rm, rng.randi_range(0, 1) * kx)


static func _platforms(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, count: int, h0: int, h1: int) -> void:
	## Tek yönlü platformlar (3-5 karo) tabandan h0-h1 karo yukarıda; üstünde 3, altında 2 karo boşluk
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	var tries := 0
	var placed := 0
	while placed < count and tries < 30:
		tries += 1
		var ln := rng.randi_range(3, 5)
		var h4 := false
		if _v43:
			# v43 platform ritmi: 2-6 karo uzun, ara ara 4 karo yukarıda (çift zıplama)
			ln = [2, 3, 3, 4, 5, 6][rng.randi_range(0, 5)]
			h4 = rng.randf() < 0.25
		if ix1 - ln - 2 < ix0 + 2:
			return
		var x := rng.randi_range(ix0 + 2, ix1 - ln - 2)
		var y: int = int(fl[x - ix0]) - (4 if h4 else rng.randi_range(h0, h1))
		if not _free_span(g, W, H, rm, x, y, ln, 3, 2):
			continue
		var flat := true
		for k in ln:
			if int(fl[x + k - ix0]) != int(fl[x - ix0]):
				flat = false
		if not flat:
			continue
		for k in ln:
			_put(g, x + k, y, W, H, 2)
		placed += 1


static func _pillars(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, count: int) -> void:
	## Yıkık taş sütunlar (2 karo geniş, 2 yüksek) tabanda; üstünden tek zıplamayla geçilir
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	var tries := 0
	var placed := 0
	while placed < count and tries < 30:
		tries += 1
		var x := rng.randi_range(ix0 + 4, ix1 - 5)
		var fy: int = int(fl[x - ix0])
		if int(fl[x + 1 - ix0]) != fy or _in_clear(rm, x, fy - 1) or _in_clear(rm, x + 1, fy - 1):
			continue
		if not _free_span(g, W, H, rm, x, fy - 1, 2, 4, 0):
			continue
		for k in 2:
			for y in range(fy - 2, fy):
				_put(g, x + k, y, W, H, 1)
		placed += 1


static func _arches(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, count: int) -> void:
	## Kemer: tabandan 4 karo yukarıda 5-6 karolık taş kiriş (altından yürünür; üstüne çift zıplamayla çıkılır)
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	var tries := 0
	var placed := 0
	while placed < count and tries < 20:
		tries += 1
		var ln := rng.randi_range(5, 6)
		if ix1 - ln - 3 < ix0 + 3:
			return
		var x := rng.randi_range(ix0 + 3, ix1 - ln - 3)
		var y: int = int(fl[x - ix0]) - 4
		if not _free_span(g, W, H, rm, x, y, ln, 3, 3):
			continue
		for k in ln:
			_put(g, x + k, y, W, H, 1)
		placed += 1


static func _stalactites(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, count: int, wmax := 2) -> void:
	## Tavandan sarkan kaya (1-wmax geniş, 1-2 uzun); her sütun kendi tavanından başlar; altında en az 5 karo açık kalır
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	var ce: Array = rm["ce"]
	if bool(rm["acik"]):
		return
	var tries := 0
	var placed := 0
	while placed < count and tries < 30:
		tries += 1
		var wd := rng.randi_range(1, wmax)
		var x := rng.randi_range(ix0 + 2, ix1 - 2 - wd)
		var ln := rng.randi_range(1, 2)
		var ok := true
		for k in wd:
			var i := x + k - ix0
			var top: int = int(ce[i])
			if top < 2 or int(fl[i]) - (top + ln) < 5:
				ok = false
			for y in range(top, top + ln + 1):
				if _in_clear(rm, x + k, y) or _cell(g, x + k, y, W, H) == 2:
					ok = false
		if not ok:
			continue
		for k in wd:
			var i := x + k - ix0
			var top: int = int(ce[i])
			for y in range(top, top + ln):
				_put(g, x + k, y, W, H, 1)
		placed += 1


static func _alcoves(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, count: int) -> void:
	## Kapısız yan duvara oyulmuş taban hizasında cep (2 karo derin, 4 yüksek): Dead Cells'in küçük çıkıntıları
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	for n in count:
		var left := rng.randf() < 0.5
		if left and bool(rm["_sol"]):
			left = false
		if not left and bool(rm["_sag"]):
			if bool(rm["_sol"]):
				return
			left = true
		var xin := ix0 if left else ix1
		var fy: int = int(fl[xin - ix0])
		var ok := true
		for y in range(fy - 5, fy + 1):
			if _in_clear(rm, xin, y):
				ok = false
		for y in range(fy - 4, fy):
			if _cell(g, xin, y, W, H) != 0:
				ok = false
		if not ok:
			continue
		for d in 2:
			var x := xin - 1 - d if left else xin + 1 + d
			for y in range(fy - 4, fy):
				_put(g, x, y, W, H, 0)
			_put(g, x, fy, W, H, 1)


static func _dips(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, count: int) -> void:
	## Tabanda 2-3 karo geniş, 2 karo derin çukurcuk (tek zıplamayla çıkılır); kapı ağzı ve kuyulardan uzak
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	for n in count:
		var wd := rng.randi_range(2, 3)
		if ix1 - 4 - wd < ix0 + 4:
			return
		var x0 := rng.randi_range(ix0 + 4, ix1 - 4 - wd)
		var fy: int = int(fl[x0 - ix0])
		var ok := true
		for x in range(x0 - 2, x0 + wd + 2):
			if int(fl[x - ix0]) != fy or _in_clear(rm, x, fy - 1) or _cell(g, x, fy, W, H) != 1 or _cell(g, x, fy - 1, W, H) != 0:
				ok = false
		if not ok:
			continue
		for x in range(x0, x0 + wd):
			_put(g, x, fy, W, H, 0)
			_put(g, x, fy + 1, W, H, 0)
			_put(g, x, fy + 2, W, H, 1)
			fl[x - ix0] = fy + 2


static func _boulders(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, count: int) -> void:
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	for i in count:
		var x := rng.randi_range(ix0 + 3, ix1 - 4)
		var fy: int = int(fl[x - ix0])
		if _in_clear(rm, x, fy - 1) or _in_clear(rm, x + 1, fy - 1) or not _free_span(g, W, H, rm, x, fy - 1, 2, 4, 0):
			continue
		_put(g, x, fy - 1, W, H, 1)
		if rng.randf() < 0.5:
			_put(g, x + 1, fy - 1, W, H, 1)


static func _span_free(rm: Dictionary, a: int, b: int, y: int) -> bool:
	## a..b sütunları y satırında temiz bölgeye (kapı ağzı, kuyu) girmiyor ve taban düz mü
	var fl: Array = rm["fl"]
	for x in range(a, b + 1):
		if x - 1 < int(rm["ix0"]) or x + 1 > int(rm["ix1"]):
			return false
		if _in_clear(rm, x, y) or int(fl[x - int(rm["ix0"])]) != y + 1:
			return false
	return true


static func _pit(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary) -> void:
	## Ortada 3-4 karo tehlike çukuru (tek zıplamayla aşılır; düşen oyuncu çukurdan sektirilir); geniş odada 5-6 karo
	## ve ortasında tek yönlü basamak
	var ix0 := int(rm["ix0"])
	var fl: Array = rm["fl"]
	var wide: bool = int(rm["ix1"]) - ix0 > 24
	var wd := rng.randi_range(5, 6) if wide else rng.randi_range(3, 4)
	if int(rm["ix1"]) - 4 - wd < ix0 + 4:
		return
	for t in 10:
		var x0 := rng.randi_range(ix0 + 4, int(rm["ix1"]) - 4 - wd)
		var fy: int = int(fl[x0 - ix0])
		if not _span_free(rm, x0 - 2, x0 + wd + 1, fy - 1):
			continue
		for x in range(x0, x0 + wd):
			_put(g, x, fy, W, H, 0)
			_put(g, x, fy + 1, W, H, 3)
			_put(g, x, fy + 2, W, H, 1)
		if wd >= 5:
			for k in 2:
				_put(g, x0 + wd / 2 - 1 + k, fy - 1, W, H, 2)
		return


static func _bridge(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary) -> void:
	## Köprü: ortada 6-10 karo, 3 karo derin yarık; taban hizasında kırık tek yönlü köprü tahtaları (aralar 1-2);
	## yarığa düşen tek zıplamayla çıkar
	var ix0 := int(rm["ix0"])
	var fl: Array = rm["fl"]
	if int(rm["ix1"]) - ix0 - 10 < 6:
		return
	var wd := rng.randi_range(6, mini(10, int(rm["ix1"]) - ix0 - 10))
	for t in 10:
		var a := rng.randi_range(ix0 + 4, int(rm["ix1"]) - 4 - wd)
		var fy: int = int(fl[a - ix0])
		if not _span_free(rm, a - 1, a + wd, fy - 1):
			continue
		for x in range(a, a + wd):
			for y in range(fy, fy + 3):
				_put(g, x, y, W, H, 0)
			fl[x - ix0] = fy + 3
		var bx := a + rng.randi_range(0, 1)
		while bx < a + wd - 1:
			var ln := rng.randi_range(2, 3)
			for k in ln:
				if bx + k < a + wd:
					_put(g, bx + k, fy, W, H, 2)
			bx += ln + rng.randi_range(1, 2)
		if rng.randf() < 0.4:
			var mid := a + wd / 2
			for hx in range(mid - 1, mid + 1):
				_put(g, hx, fy + 2, W, H, 3)
		return


static func _yarik(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary) -> void:
	## v41 açık yol yarığı: düz bir parçada 3-5 karo geniş, 3 karo derin açıklık (koşarak zıplanır; düşen tek zıplamayla
	## çıkar); 5 karoda ortada tek yönlü basamak taşı
	var ix0 := int(rm["ix0"])
	var fl: Array = rm["fl"]
	var wd := rng.randi_range(3, 5)
	if int(rm["ix1"]) - 5 - wd < ix0 + 5:
		return
	for t in 12:
		var a := rng.randi_range(ix0 + 5, int(rm["ix1"]) - 5 - wd)
		var fy: int = int(fl[a - ix0])
		if not _span_free(rm, a - 2, a + wd + 1, fy - 1):
			continue
		for x in range(a, a + wd):
			for y in range(fy, fy + 3):
				_put(g, x, y, W, H, 0)
			fl[x - ix0] = fy + 3
		if wd >= 5:
			_put(g, a + 2, fy, W, H, 2)
		return


static func _iskele(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary) -> void:
	## v41 gözcü iskelesi (açık yolun "yukarı" dalı): tabandan 3 ve 6 karo yukarıda kaydırılmış iki tek yönlü platform
	## (iki zıplama); tepesinden ufuk görünür
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	if ix1 - 11 < ix0 + 4:
		return
	for t in 12:
		var x := rng.randi_range(ix0 + 4, ix1 - 11)
		var fy: int = int(fl[x - ix0])
		var ok := true
		for k in 8:
			if int(fl[x + k - ix0]) != fy:
				ok = false
		if not ok or not _free_span(g, W, H, rm, x, fy - 3, 4, 3, 2) or not _free_span(g, W, H, rm, x + 4, fy - 6, 4, 3, 2):
			continue
		var sag := rng.randf() < 0.5
		for k in 4:
			_put(g, x + k + (4 if sag else 0), fy - 3, W, H, 2)
			_put(g, x + k + (0 if sag else 4), fy - 6, W, H, 2)
		return


static func _deck(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary) -> void:
	## Kuyu türü (yüksek oda): tabandan 4 karo yukarıda tek yönlü üst güverte (odanın yarısı-üçte ikisi, 2-3 parça);
	## aşağı + zıpla ile inilir, çift zıplamayla çıkılır
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	var x := ix0 + rng.randi_range(2, 5)
	while x < ix1 - 4:
		var ln := rng.randi_range(4, 7)
		var y: int = int(fl[x - ix0]) - 4
		var ok := true
		for k in ln:
			var xx := x + k
			if xx > ix1 - 2 or int(fl[xx - ix0]) != y + 4 or _in_clear(rm, xx, y):
				ok = false
				break
			for yy in range(y - 3, y + 4):
				if _cell(g, xx, yy, W, H) != 0:
					ok = false
		if ok:
			for k in ln:
				_put(g, x + k, y, W, H, 2)
			x += ln + rng.randi_range(3, 5)
		else:
			x += 2


static func _odul_shape(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary) -> void:
	## Ödül odası: düz; hazine / zamanlıda 2 karolık taş seki (tek zıplama); seçkinde açık alan
	var ix0 := int(rm["ix0"])
	var fl: Array = rm["fl"]
	var mid := _odul_mid(rm)
	var fy: int = int(fl[mid - ix0])
	match String(rm["odul"]):
		"hazine", "zamanli":
			for x in range(mid - 3, mid + 4):
				if _in_clear(rm, x, fy - 1):
					continue
				for y in range(fy - 2, fy):
					_put(g, x, y, W, H, 1)
				fl[x - ix0] = fy - 2
		"sunak", "tomar":
			_platforms(g, W, H, rng, rm, 1, 3, 3)
		"lanetli":
			# v34 lanetli sandık: alçak taş seki (1 karo) ve iki yanda tek yönlü çıkıntı (uzantının sonu: bekçili oda gibi)
			for x in range(mid - 2, mid + 3):
				if _in_clear(rm, x, fy - 1):
					continue
				_put(g, x, fy - 1, W, H, 1)
				fl[x - ix0] = fy - 1
			_platforms(g, W, H, rng, rm, 1, 3, 3)


static func _odul_mid(rm: Dictionary) -> int:
	## Ödülün sütunu: odanın ortası; kapı tavanda / tabanda (kuyu) ise kuyudan uzak yanın ortası
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var mid := (ix0 + ix1) / 2
	var side := _door_side(rm)
	if side in ["ust", "alt"]:
		var hx := int(rm.get("_door_x", mid))
		var sol := hx - 1 - ix0
		var kw := int(rm.get("_door_w", KUYU_W))
		var sag := ix1 - (hx + kw)
		mid = (hx + kw + 1 + ix1) / 2 + 1 if sag >= sol else (ix0 + hx - 2) / 2
	elif bool(rm.get("pencere", false)):
		# v34: pencereli ödül odası: ödül parmaklığın yakınında (ana yoldan görünsün)
		mid = ix0 + 7 if String(rm.get("pencere_yan", "sol")) == "sol" else ix1 - 6
	return clampi(mid, ix0 + 5, ix1 - 4)


static func _odul_marks(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, zamanli: Array, doors: Array) -> Array:
	## Ödül odası işaretleri [[karakter, x, y_hava]]; zamanlı kapı sütunu kaydedilir
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	var mid := _odul_mid(rm)
	var fy: int = int(fl[mid - ix0])
	var marks: Array = []
	match String(rm["odul"]):
		"hazine":
			marks.append(["T", mid, fy - 1])
		"sunak":
			marks.append(["S", mid, fy - 1])
		"tomar":
			marks.append(["M", mid, fy - 1])
		"pazar":
			var px := mid + 2
			if _v43 and _door_side(rm) in ["ust", "alt"]:
				# v43: tezgâh (P'nin 7 karo solu .. 3 karo sağı) geçidin kapağına binmesin
				var dx0 := int(rm.get("_door_x", 0))
				var dx1 := dx0 + int(rm.get("_door_w", KUYU_W)) - 1
				if dx0 < mid:
					px = clampi(maxi(px, dx1 + 9), ix0 + 8, ix1 - 3)
				else:
					px = clampi(mini(px, dx0 - 5), ix0 + 8, ix1 - 3)
			marks.append(["P", px, int(fl[px - ix0]) - 1])
		"seckin":
			var tx := clampi(mid + 5, ix0 + 2, ix1 - 2)
			if _door_side(rm) == "sag":
				tx = clampi(mid - 5, ix0 + 2, ix1 - 2)
			marks.append(["E", mid + (2 if _door_side(rm) == "sag" else -2), fy - 1])
			marks.append(["T", tx, int(fl[tx - ix0]) - 1])
		"zamanli":
			marks.append(["Z", mid, fy - 1])
			# kapı: koridorun odaya bitişik sütunu (4 karo yüksek geçit kapanır)
			var kd := _yan_kapi_sutunu(rm, doors)
			zamanli.append({"x": kd.x, "y": kd.y, "room": int(rm["id"]), "sure": ZAMANLI_SURE})
		"lanetli":
			marks.append(["L", mid, fy - 1])
	return marks


static func _door_side(rm: Dictionary) -> String:
	## Ödül odasının tek kapısı hangi yanda (sol / sag / ust: tavandaki kuyu / alt: tabandaki kuyu)
	return String(rm.get("_door_side", "sol"))


static func _odul_tasi(g: PackedByteArray, W: int, H: int, rm: Dictionary) -> Vector2i:
	## Ödül odasının Kut Taşı: kapının iç yanı (ödülden uzak); kuyu kapısında kuyunun ödülsüz yanı
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var side := _door_side(rm)
	var x := ix0 + 4 if side == "sol" else ix1 - 4
	if side in ["ust", "alt"]:
		var hx := int(rm.get("_door_x", (ix0 + ix1) / 2))
		x = hx - 2 if _odul_mid(rm) > hx else hx + int(rm.get("_door_w", KUYU_W)) + 1
	return _floor_spot(g, W, H, rm, x)


static func _floor_spot(g: PackedByteArray, W: int, H: int, rm: Dictionary, x: int) -> Vector2i:
	## Odada x sütununda (yakınında) ayakta durulacak hava hücresi (altı katı, üstünde 3 karo hava); tehlike / platform /
	## kuyu ağzı değil
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	for d in range(0, 14):
		for s in ([0] if d == 0 else [1, -1]):
			var cx := clampi(x + d * s, ix0 + 1, ix1 - 1)
			var fy: int = int(fl[cx - ix0])
			# taban satırından yukarı ilk hava hücresi
			var y := fy - 1
			while y > int(rm["iy0"]) and _cell(g, cx, y, W, H) == 1:
				y -= 1
			if _cell(g, cx, y, W, H) == 0 and _cell(g, cx, y + 1, W, H) == 1 and _cell(g, cx, y - 1, W, H) == 0 and _cell(g, cx, y - 2, W, H) == 0 and _cell(g, cx - 1, y + 1, W, H) != 3 and _cell(g, cx + 1, y + 1, W, H) != 3 and _cell(g, cx - 1, y + 1, W, H) != 0 and _cell(g, cx + 1, y + 1, W, H) != 0:
				return Vector2i(cx, y)
	return Vector2i(x, int(fl[clampi(x - ix0, 0, fl.size() - 1)]) - 1)


static func _hazard_strips(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, style: String) -> void:
	## Dövüş odalarının düz tabanında 2-3 karolık tehlike şeridi (tek zıplamayla aşılır); kapı ağzı ve kuyulardan uzak
	if rng.randf() > 0.5:
		return
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	for t in 8:
		var wd := rng.randi_range(2, 3)
		if ix1 - 5 - wd < ix0 + 5:
			return
		var x0 := rng.randi_range(ix0 + 5, ix1 - 5 - wd)
		var fy: int = int(fl[x0 - ix0])
		var ok := true
		for x in range(x0 - 3, x0 + wd + 3):
			if int(fl[x - ix0]) != fy or _in_clear(rm, x, fy - 1) or _cell(g, x, fy, W, H) != 1 or _cell(g, x, fy - 1, W, H) != 0:
				ok = false
		if not ok:
			continue
		for x in range(x0, x0 + wd):
			_put(g, x, fy, W, H, 3)
		return


# ================================================================== erişilebilirlik
static func _open_headroom(g: PackedByteArray, W: int, H: int, need: int) -> int:
	## v25: yürünen her hücrenin (hava ya da tehlike; altı katı / platform) üstünde need karo katı olmayan alan:
	## tavana / ada altına / parça duvarına 1-2 karo kalan yerlerde katı karolar açılır (sürünme geçidi kalmaz).
	## Platform (tek yönlü) baş boşluğunu kesmez. Döndürür: açılan karo sayısı.
	var n := 0
	for x in range(1, W - 1):
		for y in range(2, H - 1):
			var c := _cell(g, x, y, W, H)
			if c != 0 and c != 3:
				continue
			var b := _cell(g, x, y + 1, W, H)
			if b != 1 and b != 2:
				continue
			for k in range(1, need):
				var yy := y - k
				if yy < 1:
					break
				if _cell(g, x, yy, W, H) == 1:
					_put(g, x, yy, W, H, 0)
					n += 1
	return n


static func _standable(g: PackedByteArray, x: int, y: int, W: int, H: int) -> bool:
	## Hava karosu, altı katı/platform olan yer; tehlike (3) üstünde durulmaz
	if _cell(g, x, y, W, H) != 0:
		return false
	var below := _cell(g, x, y + 1, W, H)
	return below == 1 or below == 2


static func _moves(g: PackedByteArray, W: int, H: int, cx: int, cy: int, cols: Array = []) -> Array:
	## Fizik sadık hamleler (oyuncu 2 karo boy, sürünürken 1): yürüme/sürünme ±1; düşme ±5 sütun / 15 satır;
	## zıplama en çok 4 karo yukarı (çift zıplama), çıkış sütununda baş boşluğu, yörünge tepesi açık olmalı.
	## v25: tek yönlü platform (2) baş boşluğunu ve zıplama yörüngesini kesmez (oyuncu altından içinden zıplar).
	## v38: cols (_stand_cols: sütun başına ayakta durulabilir satırlar) verilirse adaylar yalnızca oradan gelir
	## (BFS'lerde 231 adayın _standable denetimi yerine sütun başına birkaç satır); sıra ve sonuç aynıdır.
	var out: Array = []
	var tall: bool = _cell(g, cx, cy - 1, W, H) != 1
	var head := 0
	while head < 5 and _cell(g, cx, cy - 1 - head, W, H) != 1:
		head += 1
	var max_up := (head - 1) if tall else 0
	var ylo := maxi(1, cy - maxi(0, max_up))
	var yhi := mini(H - 2, cy + 15)
	for dx in range(-5, 6):
		var nx := cx + dx
		if nx < 1 or nx >= W - 1:
			continue
		if cols.is_empty():
			for ny in range(ylo, yhi + 1):
				if (dx == 0 and ny == cy) or not _standable(g, nx, ny, W, H):
					continue
				if _hamle_ok(g, W, H, cx, cy, nx, ny, tall):
					out.append(_idx(nx, ny, W))
		else:
			for ny in cols[nx]:
				if ny < ylo:
					continue
				if ny > yhi:
					break
				if dx == 0 and ny == cy:
					continue
				if _hamle_ok(g, W, H, cx, cy, nx, ny, tall):
					out.append(ny * W + nx)
	return out


static func _stand_cols(g: PackedByteArray, W: int, H: int) -> Array:
	## v38: sütun başına ayakta durulabilir satırlar (artan; _standable ile aynı kural), BFS başına bir kez
	var cols: Array = []
	cols.resize(W)
	for x in W:
		var c := PackedInt32Array()
		for y in range(0, H - 1):
			if g[y * W + x] == 0:
				var b: int = g[(y + 1) * W + x]
				if b == 1 or b == 2:
					c.append(y)
		cols[x] = c
	return cols


static func _hamle_ok(g: PackedByteArray, W: int, H: int, cx: int, cy: int, nx: int, ny: int, tall: bool) -> bool:
	## _moves'un aday doğrulaması (varış ayakta durulabilir ve aynı hücre değil): sürünme, yörünge tepesi, iniş yolu
	var dx := nx - cx
	var dy := ny - cy
	var crawl_dest: bool = _cell(g, nx, ny - 1, W, H) == 1
	if crawl_dest and not (dy == 0 and absi(dx) == 1):
		return false
	if not (dy == 0 and absi(dx) == 1):
		if not tall and dy < 0:
			return false
		var apex := mini(cy, ny) - 1 - (1 if dy > 2 else 0)
		if dy < 0:
			apex = ny - 1
		var blocked := false
		var step := 1 if dx > 0 else -1
		var k := cx
		while k != nx:
			k += step
			if _cell(g, k, apex, W, H) == 1 and _cell(g, k, apex + 1, W, H) == 1:
				blocked = true
				break
		if blocked:
			return false
		if dy > 0 and _cell(g, nx, ny - 1, W, H) == 1:
			return false
		# v33 düzeltmeleri (eskiden kayanın / tek yönlü platformun içinden düşülebiliyordu):
		# dikine iniş yalnızca durulan tek yönlü platformdan (aşağı + zıpla); altındaki sütun ilk tutunulacak
		# yere dek boş (araya giren platform / katı karo düşüşü orada keser: o ayrı bir hamledir)
		if dx == 0 and dy > 0:
			if _cell(g, cx, cy + 1, W, H) != 2:
				return false
			var thru := true
			for yy in range(cy + 2, ny):
				if _tutar(_cell(g, cx, yy, W, H)):
					thru = false
					break
			if not thru:
				return false
		# yana düşüş: düşülen sütunda iniş yolu boş olmalı (başlangıç ayak hizasının altındaki platform da
		# tutar); değilse kenardan yürüyüp komşu sütunda düşülür: komşu sütun boş ve varış satırının üstü
		# komşudan varışa dek açık
		if dy > 1 and dx != 0:
			var clear := true
			for yy in range(mini(cy, ny) - 1, ny):
				var cc := _cell(g, nx, yy, W, H)
				if cc == 1 or (cc == 2 and yy > cy):
					clear = false
					break
			if not clear:
				var c1 := cx + step
				var ok2 := true
				for yy in range(cy - 1, ny):
					var cc := _cell(g, c1, yy, W, H)
					if cc == 1 or (cc == 2 and yy > cy):
						ok2 = false
						break
				var k2 := c1
				while ok2 and k2 != nx:
					k2 += step
					if _cell(g, k2, ny - 1, W, H) == 1 or (k2 != nx and _cell(g, k2, ny, W, H) == 2):
						ok2 = false
				if not ok2:
					return false
	return true


static func _tutar(c: int) -> bool:
	## Düşen oyuncuyu tutan karo: katı ya da tek yönlü platform (üstten çarpışır)
	return c == 1 or c == 2


static func _goal(cx: int, cy: int) -> bool:
	return absi(cx - int(_son["gx"])) <= 3 and absi(cy - int(_son["gy"])) <= 1


static func _reach(g: PackedByteArray, W: int, H: int, _heights: Array) -> Dictionary:
	## Girişten çıkışa erişim: {ok, x, y} (x,y: çıkışa en yakın ulaşılan ayakta durma hücresi)
	var sx := int(_son["sx"])
	var sy := int(_son["sy"])
	var seen := PackedByteArray()
	seen.resize(W * H)
	seen.fill(0)
	var q: Array = [_idx(sx, sy, W)]
	seen[q[0]] = 1
	var cols := _stand_cols(g, W, H)
	var best := [sx, sy]
	var bd := 999999
	var qi := 0
	while qi < q.size():
		var id: int = q[qi]
		qi += 1
		var cx := id % W
		var cy := id / W
		var d := absi(cx - int(_son["gx"])) * 2 + absi(cy - int(_son["gy"]))
		if d < bd:
			bd = d
			best = [cx, cy]
		if _goal(cx, cy):
			return {"ok": true, "x": cx, "y": cy}
		for n in _moves(g, W, H, cx, cy, cols):
			if seen[n] == 0:
				seen[n] = 1
				q.append(n)
	return {"ok": false, "x": best[0], "y": best[1]}


static func reach_set(g: PackedByteArray, W: int, H: int, _heights: Array) -> PackedByteArray:
	## Girişten ulaşılabilen ayakta durma hücreleri (1 = ulaşılır; tehlike hava sayılır). Keşif ganimeti, harita testi.
	return reach_from(g, W, H, int(_son["sx"]), int(_son["sy"]))


static func reach_from(g: PackedByteArray, W: int, H: int, sx: int, sy: int) -> PackedByteArray:
	var gh := _haz_as_air(g)
	var seen := PackedByteArray()
	seen.resize(W * H)
	seen.fill(0)
	var s0 := _idx(sx, sy, W)
	seen[s0] = 1
	var q: Array = [s0]
	var qi := 0
	var cols := _stand_cols(gh, W, H)
	while qi < q.size():
		var id: int = q[qi]
		qi += 1
		for n in _moves(gh, W, H, id % W, id / W, cols):
			if seen[n] == 0:
				seen[n] = 1
				q.append(n)
	return seen


static func traps(g: PackedByteArray, W: int, H: int, _heights: Array, orig: PackedByteArray = PackedByteArray()) -> Array:
	## Tuzaklar: girişten ulaşılabilen ama çıkışa ulaşamayan ayakta durma hücreleri (düşülen çıkmaz çukurlar).
	## orig verilirse tehlike (3) tabanlı hücreler sayılmaz (çukur oyuncuyu kendisi dışarı sektirir).
	## v38: ters kenarlar sıkıştırılmış dizide (kenar listesi + sayım sıralaması), hamleler sütun listesinden
	var sx := int(_son["sx"])
	var sy := int(_son["sy"])
	var seen := PackedByteArray()
	seen.resize(W * H)
	seen.fill(0)
	var sira := PackedInt32Array()   # hücre -> q içindeki sıra (yalnızca görülenler için geçerli)
	sira.resize(W * H)
	var es := PackedInt32Array()     # kenar kaynağı (q sırası)
	var ed := PackedInt32Array()     # kenar hedefi (q sırası)
	var q: Array = [_idx(sx, sy, W)]
	seen[q[0]] = 1
	sira[q[0]] = 0
	var cols := _stand_cols(g, W, H)
	var qi := 0
	var goals: Array = []
	while qi < q.size():
		var id: int = q[qi]
		qi += 1
		if _goal(id % W, id / W):
			goals.append(qi - 1)
		for n in _moves(g, W, H, id % W, id / W, cols):
			if seen[n] == 0:
				seen[n] = 1
				sira[n] = q.size()
				q.append(n)
			es.append(qi - 1)
			ed.append(sira[n])
	# ters komşuluk: hedef başına kaynaklar (sayım + önek toplamı)
	var nq := q.size()
	var bas := PackedInt32Array()
	bas.resize(nq + 1)
	bas.fill(0)
	for d in ed:
		bas[d + 1] += 1
	for k in nq:
		bas[k + 1] += bas[k]
	var yaz := bas.duplicate()
	var radj := PackedInt32Array()
	radj.resize(ed.size())
	for k in ed.size():
		var d: int = ed[k]
		radj[yaz[d]] = es[k]
		yaz[d] += 1
	var good := PackedByteArray()
	good.resize(nq)
	good.fill(0)
	var rq: Array = goals.duplicate()
	for gq in goals:
		good[gq] = 1
	var ri := 0
	while ri < rq.size():
		var o: int = rq[ri]
		ri += 1
		for k in range(bas[o], bas[o + 1]):
			var pr: int = radj[k]
			if good[pr] == 0:
				good[pr] = 1
				rq.append(pr)
	var out: Array = []
	for k in nq:
		if good[k] == 0:
			var id3: int = q[k]
			if not orig.is_empty() and orig[id3] == 3:
				continue
			out.append(id3)
	return out


static func fix_traps(g: PackedByteArray, W: int, H: int, heights: Array) -> int:
	## Çıkmazları kapat: en derindeki tuzak hücresinin üstüne zikzak tek yönlü basamaklar koy (2 karoda bir);
	## olmazsa çukur tabanını bir karo yükselt. Döndürür: yapılan düzeltme sayısı.
	var gh := _haz_as_air(g)
	var fixes := 0
	if not _reach(gh, W, H, heights)["ok"]:
		return 0
	for it in 60:
		var tr := traps(gh, W, H, heights, g)
		if tr.is_empty():
			break
		var deep: int = tr[0]
		for id in tr:
			if id / W > deep / W:
				deep = id
		var x := deep % W
		var y := deep / W
		if it < 40:
			var side := 1
			var placed := false
			var py := y - 2
			while py > y - 14 and py > 2:
				var px := x + (0 if side > 0 else -2)
				for k in 3:
					if _cell(gh, px + k, py, W, H) == 0 and _cell(gh, px + k, py - 1, W, H) == 0:
						_put(g, px + k, py, W, H, 2)
						_put(gh, px + k, py, W, H, 2)
						placed = true
				side = -side
				py -= 2
			if not placed:
				_put(g, x, y, W, H, 1)
				_put(gh, x, y, W, H, 1)
		else:
			for k in range(-1, 2):
				if _cell(gh, x + k, y, W, H) == 0:
					_put(g, x + k, y, W, H, 1)
					_put(gh, x + k, y, W, H, 1)
		fixes += 1
	return fixes


static func _reachable(g: PackedByteArray, W: int, H: int, heights: Array) -> bool:
	return _reach(_haz_as_air(g), W, H, heights)["ok"]


static func _haz_as_air(g: PackedByteArray) -> PackedByteArray:
	var c := g.duplicate()
	for i in c.size():
		if c[i] == 3:
			c[i] = 0
	return c


static func guarantee(g: PackedByteArray, W: int, H: int, heights: Array) -> int:
	## Eski imza: girişten çıkışa yol yoksa 0 döndürür (v32: onarım fix_traps ve yeniden üretimle)
	return 0 if _reachable(g, W, H, heights) else 0


# ================================================================== yol bulma (bot / rehber)
static func path_cells(g: PackedByteArray, W: int, H: int, sx: int, sy: int, gx: int, gy: int, max_nodes := 60000) -> Array:
	## Girişten hedefe en kısa hamle dizisi (hücre dizinleri; ilk öğe başlangıç). Hedef: gx±2, gy±1. Boşsa yol yok.
	var gh := _haz_as_air(g)
	var seen := PackedByteArray()
	seen.resize(W * H)
	seen.fill(0)
	var par := PackedInt32Array()
	par.resize(W * H)
	par.fill(-1)
	var s0 := _idx(sx, sy, W)
	seen[s0] = 1
	var q: Array = [s0]
	var qi := 0
	var goal := -1
	var cols := _stand_cols(gh, W, H)
	while qi < q.size() and qi < max_nodes:
		var id: int = q[qi]
		qi += 1
		var cx := id % W
		var cy := id / W
		if absi(cx - gx) <= 2 and absi(cy - gy) <= 1:
			goal = id
			break
		for n in _moves(gh, W, H, cx, cy, cols):
			if seen[n] == 0:
				seen[n] = 1
				par[n] = id
				q.append(n)
	var out: Array = []
	if goal < 0:
		return out
	var c := goal
	while c >= 0:
		out.append(c)
		c = par[c]
	out.reverse()
	return out


static func stand_cell(g: PackedByteArray, W: int, H: int, px: float, py: float, TS: int) -> Vector2i:
	## Dünya ayak noktasından en yakın ayakta durma hücresi (tehlike hava sayılır)
	var gh := _haz_as_air(g)
	var x := clampi(int(floor(px / TS)), 1, W - 2)
	var y := clampi(int(floor((py - 2.0) / TS)), 1, H - 2)
	for d in range(0, 6):
		for dy in range(-d, d + 1):
			for dx in range(-d, d + 1):
				if absi(dx) != d and absi(dy) != d:
					continue
				if _standable(gh, x + dx, y + dy, W, H):
					return Vector2i(x + dx, y + dy)
	return Vector2i(x, y)
