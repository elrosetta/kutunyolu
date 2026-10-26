class_name Kodeks
extends RefCounted
## v44 Ozan'ın Destanı (kodeks; Hades Codex / Dead Cells bestiary esinli): yaratıklar ve bosslar (öldürme sayısı,
## N öldürmede açılan zaaf), silah kitaplığı (görülen / açılan / öldürme), Damgalar, görümler ve Gün örgüleri,
## başarımlar; tamamlanma yüzdesi. Ozan'dan (yurt + konak; R) ve duraklatmadan (C) açılır.
##
## Kalıcı kayıt (Game.meta["kodeks"], meta_hazirla göçü):
##   y: {yaratık kimliği: [öldürme, seni devirme]}    s: {eşya kimliği: [görüldü 0/1, öldürme]}
##   d: {damga: alınma sayısı}   dg: [görülen damga]   seckin: seçkin öldürme toplamı   surum: 44
## Silah kitaplığı ky-kavanoz44'ün kavanoz verisini (varsa) yalnızca okur: Game.meta "kavanoz" / "silah_kavanoz".

const SURUM := 44
const ZAAF_N := 5        # sıradan yaratıkta zaaf bu kadar öldürmede açılır
const BILGI_N := 15      # can / hasar bilgisi
const BOSS_ZAAF_N := 1

## Yapay zekâ türüne göre zaaf (öğrenilen savaş bilgisi)
const ZAAF := {
	"lunger": "Atılmadan önce çömelir: atılışı yana yuvarlanarak boşa çıkar, sırtına vur.",
	"flyer_ranged": "Buhurdan sallanırken zehir saçar: altına gir, okla ya da göğe savurmayla düşür.",
	"brute": "Ağır vuruşu yavaştır: '!!' görünce yuvarlan, arkasından vur; duruşu kırılınca infaza açık.",
	"hopper": "İnişinde sarsılır: sıçradığında kenara çekil, yere değdiği an vur.",
	"illusionist": "Hayaletleri tek vuruşta dağılır; gerçeğin ayağının dibinde gölgesi vardır.",
	"grabber": "Uzun kolları önden yakalar: yakalanınca tuşlara bas; arkadan ya da uzaktan vur.",
	"shield": "Önden vurulmaz: arkasına geç; ağır vuruş ya da üç darbe kalkanını düşürür.",
	"diver": "Pikeden önce havada bir an durur: o an yana kaç, yere çakılınca vur.",
	"stalker": "Görünmezken yaklaşır; belirdiği an afallar: ilk vuruşu sen yap.",
	"tornado": "Hortumu içine çeker: uzaktan vur, hortum dinince yaklaş.",
	"archer": "Geri çekilerek atar: üstüne atıl, köşeye sıkıştır.",
	"charger": "Hücumu dümdüz: zıpla ya da yuvarlan; duvara çarpınca sersemler.",
	"teleporter": "Işınlandığı yerde bir an görünür kalır: belirdiği yere dön.",
	"crawler": "Alçaktan atılır: zıplayıp üstüne in.",
	"swarm": "Sürü tek vuruşta dağılır: geniş savuruş ya da patlayıcı kullan.",
	"caster": "Büyüyü hazırlarken durur: o an saldır; yerdeki halkalardan uzak dur.",
	"kamikaze": "Ölünce de patlar: uzaktan bitir ya da vurup çekil.",
	"turtle": "Kabuktayken dokunulmaz: kabuktan çıkınca vur, yuvarlanırken üstünden zıpla.",
	"mimic": "Tanıdık seslerle çağırır, arkadan saldırır: sırtını duvara ver.",
	"charmer": "Büyüsü kontrolleri ters çevirir: gözünü dikmeden önce bitir, okla.",
	"pouncer": "Yüksekten üstüne atlar: gölgesini gör, yuvarlan.",
	"burrower": "Yere dalınca altından çıkar: titreşen toprağı izle, çıktığı an vur.",
	"summoner": "Yavrularını çağırır: önce çağıranı öldür, yavrular dağılır.",
	"swooper": "Yandan alçalıp pençeler: zıplayıp havada karşıla.",
	"lancer": "Hücum şeridi uzundur: şeritten çık, hücum bitince arkasından vur.",
	"slammer": "Çakılınca iki yana şok dalgası: dalgayı zıplayarak aş.",
	"ricochet": "Orağı gidip döner: dönüş yolunda durma, orak elinden çıkınca saldır.",
	"gasser": "Zehir bulutu solur: bulut dağılınca yaklaş; dili seni çeker.",
	"webber": "Ağına düşersen dört kez bas; ağ atmadan dibine gir.",
	"healer": "Yoldaşlarını korur ve iyileştirir: önce onu öldür.",
	"blinker": "Kara dönüşüp arkanda belirir: kaybolunca hemen arkanı dön.",
	"chainer": "Kancalı zinciriyle çeker: zincir gelirken yuvarlan.",
	"breather": "Soluğu koni gibi yayılır: arkasına ya da üstüne geç.",
}
const BOSS_ZAAF := {
	"kara_boru_han": "Uluması sürüyü çağırır; atılışlarının arasında üç vuruşluk açık verir. Önce yavrularını dağıt.",
	"tepegoz": "Tek gözü zaafı: göz parlarken vur; yumruğu yere inerken zıpla.",
	"sahmeran_ana": "Zehir kuşağından uzak dur; kuyruk savuruşunun ardından başı yere iner.",
	"yelbegen": "Üç başı sırayla saldırır; buz yağmurunda durma, başlar yer değiştirirken arkasına geç.",
	"erlik_han": "Zincir halkalarını yaklaşmadan kır; kor dalgasını zıpla, karanlıkta ışığa sığın.",
}
const GIZLI := ["sulmus_yavrusu"]   # kodekse ayrı satır olarak girmeyenler


static func meta_hazirla() -> void:
	## Kayıt göçü: v44 öncesi kayıtta kodeks yok; türleri bozuksa onarılır
	var m: Dictionary = Game.meta
	var k: Variant = m.get("kodeks")
	if not (k is Dictionary):
		k = {}
	var kd: Dictionary = k
	for f in ["y", "s", "d"]:
		if not (kd.get(f) is Dictionary):
			kd[f] = {}
	if not (kd.get("dg") is Array):
		kd["dg"] = []
	kd["seckin"] = int(kd.get("seckin", 0))
	kd["surum"] = SURUM
	m["kodeks"] = kd
	# eski kayıtlarda bilinen silahlar (açılanlar) görülmüş sayılır
	for id in m.get("unlocked", []):
		if not (kd["s"] as Dictionary).has(id):
			kd["s"][id] = [1, 0]
	for id in Game.BASE_UNLOCKED:
		if not (kd["s"] as Dictionary).has(id):
			kd["s"][id] = [1, 0]


static func _k() -> Dictionary:
	if not (Game.meta.get("kodeks") is Dictionary):
		meta_hazirla()
	return Game.meta["kodeks"]


# ------------------------------------------------------------------ kayıt
static func oldur(e: Node) -> void:
	var id := String(e.get("kind"))
	if id == "" or e.has_meta("yavru"):
		return
	var y: Dictionary = _k()["y"]
	var r: Array = y.get(id, [0, 0])
	var ilk := int(r[0]) == 0
	r[0] = int(r[0]) + 1
	y[id] = r
	if bool(e.get("elite")):
		_k()["seckin"] = int(_k().get("seckin", 0)) + 1
	var esik := BOSS_ZAAF_N if bool(e.get("is_boss")) else ZAAF_N
	if ilk or int(r[0]) == esik:
		var main: Node = FX.level.get_parent() if FX.level else null
		if main and main.get("hud"):
			if int(r[0]) == esik and zaaf(id) != "":
				main.hud.flash_msg = "Ozan'ın Destanı: %s için zaaf yazıldı." % ad(id)
			elif ilk:
				main.hud.flash_msg = "Ozan'ın Destanı: yeni sayfa · %s" % ad(id)
			main.hud.flash_t = 3.0


static func devirdi(kind: String) -> void:
	if kind == "":
		return
	var y: Dictionary = _k()["y"]
	var r: Array = y.get(kind, [0, 0])
	r[1] = int(r[1]) + 1
	y[kind] = r


static func silah_gor(it: Dictionary) -> void:
	var id := String(it.get("id", ""))
	if id == "":
		return
	var s: Dictionary = _k()["s"]
	var r: Array = s.get(id, [0, 0])
	r[0] = 1
	s[id] = r


static func silah_oldur(it: Dictionary) -> void:
	var id := String(it.get("id", ""))
	if id == "":
		return
	var s: Dictionary = _k()["s"]
	var r: Array = s.get(id, [1, 0])
	r[0] = 1
	r[1] = int(r[1]) + 1
	s[id] = r


static func damga_gor(id: String) -> void:
	var dg: Array = _k()["dg"]
	if not (id in dg):
		dg.append(id)


static func damga_al(id: String) -> void:
	damga_gor(id)
	var d: Dictionary = _k()["d"]
	d[id] = int(d.get(id, 0)) + 1


# ------------------------------------------------------------------ sorgu
static func oldurme(id: String) -> int:
	var y: Variant = Game.meta.get("kodeks", {}).get("y", {}) if Game.meta.get("kodeks") is Dictionary else {}
	return int((y as Dictionary).get(id, [0, 0])[0])


static func devirme(id: String) -> int:
	return int((_k()["y"] as Dictionary).get(id, [0, 0])[1])


static func toplam_oldurme() -> int:
	var n := 0
	for id in _k()["y"]:
		n += int(_k()["y"][id][0])
	return n


static func yaratiklar() -> Array:
	## Kodeks sırası: biyom sırasıyla yaratıklar, sonra bosslar (world.json "impl" olanlar, tekrar yok)
	var out: Array = []
	var bosses: Array = []
	for e in Data.world.get("enemies", []):
		if not bool(e.get("impl", false)):
			continue
		var id := String(e.get("id", ""))
		if id in GIZLI or id in out or id in bosses:
			continue
		if String(e.get("ai", "")).begins_with("boss"):
			bosses.append(id)
		else:
			out.append(id)
	return out + bosses


static func def(id: String) -> Dictionary:
	return Data.enemy_def(id)


static func ad(id: String) -> String:
	var d := def(id)
	return InkUI.tr_title(String(d.get("name", id))) if String(d.get("ai", "")).begins_with("boss") else String(d.get("name", id))


static func boss_mu(id: String) -> bool:
	return String(def(id).get("ai", "")).begins_with("boss")


static func zaaf(id: String) -> String:
	if BOSS_ZAAF.has(id):
		return String(BOSS_ZAAF[id])
	var ai := String(def(id).get("ai", ""))
	if ai == "":
		ai = String(def(String(def(id).get("sprite", ""))).get("ai", ""))
	return String(ZAAF.get(ai, ""))


static func zaaf_acik(id: String) -> bool:
	return oldurme(id) >= (BOSS_ZAAF_N if boss_mu(id) else ZAAF_N)


static func bilgi_acik(id: String) -> bool:
	return oldurme(id) >= (BOSS_ZAAF_N if boss_mu(id) else BILGI_N)


static func zaaf_sayi() -> int:
	var n := 0
	for id in yaratiklar():
		if zaaf_acik(id):
			n += 1
	return n


static func silahlar() -> Array:
	## Silah kitaplığı: items.json'daki silah / kalkan / teçhizat (gelişmiş sürümler dahil), kategori sırasıyla
	var out: Array = []
	for cat in ["weapons", "shields", "gadgets"]:
		for it in Data.items.get(cat, []):
			if not bool(it.get("impl", true)):
				continue
			out.append(String(it.get("id", "")))
	return out


static func silah_gorulen(id: String) -> bool:
	return int((_k()["s"] as Dictionary).get(id, [0, 0])[0]) > 0


static func silah_oldurme(id: String) -> int:
	return int((_k()["s"] as Dictionary).get(id, [0, 0])[1])


static func kavanozda(id: String) -> bool:
	## ky-kavanoz44 kavanoz galerisi (varsa; yalnızca okunur): {id: ...} ya da [id...]
	for key in ["kavanoz", "silah_kavanoz", "kavanozlar"]:
		var v: Variant = Game.meta.get(key)
		if v is Dictionary and (v as Dictionary).has(id):
			return true
		if v is Array and id in (v as Array):
			return true
	return false


static func damga_alinan(id: String) -> int:
	return int((_k()["d"] as Dictionary).get(id, 0))


static func damga_gorulen(id: String) -> bool:
	return id in (_k()["dg"] as Array) or damga_alinan(id) > 0


static func destan_kayitlari() -> Array:
	## Görümler ve örgüler: [[başlık, satır, açık], ...] (story.json; Hikaye ilerlemesi)
	var out: Array = []
	for bid in Hikaye.ORGU_SIRA:
		var o: Dictionary = Hikaye.orgu(bid)
		out.append([String(o.get("ad", bid)) + " · " + Hikaye.boss_ad(bid), String(o.get("gorum", o.get("alt", ""))), Hikaye.parca_var(bid), "orgu"])
	var bl: Array = ["otuken", "bozkir", "sahmeran", "kaf", "tamu"]
	for b in bl:
		var bad := String(Hikaye.bolum(b).get("ad", b))
		out.append(["Görüm · " + bad, Hikaye.gorum_satiri(b), Hikaye.gorum_goruldu("biyom:" + b), "gorum"])
	for b in bl:
		for i in (Data.story.get("oda", {}).get(b, []) as Array).size():
			var s := Hikaye.oda_satiri(b, i)
			if s == "":
				continue
			out.append(["Taş yazıt · %s %d" % [String(Hikaye.bolum(b).get("ad", b)), i + 1], s, Hikaye.gorum_goruldu("oda:%s:%d" % [b, i]), "tas"])
	return out


static func tamamlanma() -> float:
	## 0..1: yaratık görülen %35, zaaf %15, silah %20, Damga %10, destan %10, başarım %10
	var yl := yaratiklar()
	var yg := 0
	for id in yl:
		if oldurme(id) > 0:
			yg += 1
	var sl := silahlar()
	var sg := 0
	for id in sl:
		if silah_gorulen(id):
			sg += 1
	var dl := Damga.ids()
	var dgn := 0
	for id in dl:
		if damga_alinan(id) > 0:
			dgn += 1
	var ds := destan_kayitlari()
	var dsn := 0
	for r in ds:
		if bool(r[2]):
			dsn += 1
	var t := 0.0
	t += 0.35 * float(yg) / maxf(1.0, yl.size())
	t += 0.15 * float(zaaf_sayi()) / maxf(1.0, yl.size())
	t += 0.2 * float(sg) / maxf(1.0, sl.size())
	t += 0.1 * float(dgn) / maxf(1.0, dl.size())
	t += 0.1 * float(dsn) / maxf(1.0, ds.size())
	t += 0.1 * float(Basarim.acik_sayi()) / maxf(1.0, Basarim.B.size())
	return clampf(t, 0.0, 1.0)


# ------------------------------------------------------------------ portre
static func portre(ci: CanvasItem, id: String, r: Rect2, col := Color.WHITE, anim := "idle") -> bool:
	## Yaratığın mürekkep çiziminden portre: idle ilk karesi, kutuya sığdırılır (ayaklar tabana). false: çizilemedi
	var d := def(id)
	var sk := String(d.get("sprite", ""))
	if sk == "":
		sk = id
	# Enemy._ready ile aynı: kendi çizilmiş çeşitlemesi varsa o, yoksa taban tür + biyom tonu (world.json "tint")
	if sk != id and FileAccess.file_exists("res://assets/sprites/%s_v2.json" % id):
		sk = id
	elif d.has("tint") and col.a > 0.0 and not (col.r == 0.0 and col.g == 0.0 and col.b == 0.0):
		var tt: Array = d["tint"]
		col = Color(col.r * float(tt[0]), col.g * float(tt[1]), col.b * float(tt[2]), col.a)
	var m: Dictionary = {}
	if not ResourceLoader.exists("res://assets/sprites/%s_v2.json" % sk) and not FileAccess.file_exists("res://assets/sprites/%s_v2.json" % sk):
		return false
	m = Data.sprite(sk)
	if m.is_empty() or not m.has("anims"):
		return false
	var anims: Dictionary = m["anims"]
	var an := anim if anims.has(anim) else String(anims.keys()[0])
	var a: Dictionary = anims[an]
	var cell: Array = m["cell"]
	var row := int(a.get("row", 0))
	var tex: Texture2D = m["tex"]
	if a.has("page") and m.has("page_texs"):
		tex = m["page_texs"][mini(int(a["page"]), (m["page_texs"] as Array).size() - 1)]
	elif m.has("page_texs"):
		var pr := maxi(1, int(m.get("page_rows", 9999)))
		var pg := mini(row / pr, (m["page_texs"] as Array).size() - 1)
		row -= pg * pr
		tex = m["page_texs"][pg]
	var src := Rect2(0.0, float(row) * float(cell[1]), float(cell[0]), float(cell[1]))
	var bb := _bbox(id, tex, src)
	var sc := minf(r.size.x / bb.size.x, r.size.y / bb.size.y)
	var dsz := bb.size * sc
	var dst := Rect2(Vector2(r.position.x + (r.size.x - dsz.x) * 0.5, r.end.y - dsz.y), dsz)
	ci.draw_texture_rect_region(tex, dst, bb, col)
	return true


static var _bb: Dictionary = {}


static func _bbox(id: String, tex: Texture2D, src: Rect2) -> Rect2:
	## Karenin dolu bölgesi (boş kenarlar kırpılır; bir kez hesaplanır)
	if _bb.has(id):
		return _bb[id]
	var out := src
	var t: Texture2D = tex
	if tex is CanvasTexture:
		t = (tex as CanvasTexture).diffuse_texture
	if t != null:
		var img := t.get_image()
		if img != null:
			if img.is_compressed():
				img.decompress()
			var sub := img.get_region(Rect2i(src))
			var u := sub.get_used_rect()
			if u.size.x > 4 and u.size.y > 4:
				out = Rect2(src.position + Vector2(u.position), Vector2(u.size)).grow(2.0)
	_bb[id] = out
	return out
