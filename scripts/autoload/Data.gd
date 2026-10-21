extends Node
## Veri ve görsel önbelleği: JSON verileri, sprite meta bilgisi, CanvasTexture'lar (renk + normal map).

var items: Dictionary = {}
var world: Dictionary = {}
var story: Dictionary = {}
var weapon_meta: Dictionary = {}   # weapons.json: yalnızca meta (eşya listesi, eski hücre pivotları, texel)
var _sprites: Dictionary = {}


## Doku paketi (HD): assets_hd/x2 altında aynı göreli yolla, temel dokunun 2 katı çözünürlükte yeniden çizilmiş renk
## dokuları. manifest.json temel boyutları tutar; yüklenen büyük doku ImageTexture.set_size_override ile temel boyutta
## raporlanır: bölgeler, kareler, köken ve dünya boyu değişmez, yalnızca ayrıntı artar. Maske ve ışıma (_e) haritaları
## temel çözünürlükte kalır. Dokular (doku yoğunluğu 8 piksel / dünya birimi) tools/artgen/hdpack.py ile prosedürel
## çizimden yeniden üretilir; dosya WebP (manifest girişi [g, y, "<dosya>", "<md5>"]). 2K ve 4K aynı x2 paketini kullanır
## (1,7 yakınlıkta 4K'da ~6,8 ekran pikseli / birim). v30: eski v1 piksel 4K paketi (assets_hd/x4) kaldırıldı.
## md5: temel PNG'nin özeti; kaynak dosyalar varken (proje klasöründen çalışma) temel doku sonradan değiştiyse eski HD
## sürüm kullanılmaz (temel doku yüklenir, uyarı).
var pack := 1                 # istenen paket düzeyi (1 / 2 / 4)
var pack_level := 0           # etkin paket (0 yok, 1 = 2K, 2 = 4K; manifest yüklendiyse)
var _packs: Array = []        # [{"dir", "scale", "man"}]
var _tex_cache: Dictionary = {}
var _pack_hits := 0
var _pack_usec := 0          # paket dokularının yükleme süresi (ölçüm: Ayarlar --olcum)


func _init_pack() -> void:
	pack = Ayarlar.pack_scale()
	Ayarlar.lock_pack()
	if pack <= 1:
		return
	var dir := "res://assets_hd/x2/"
	if FileAccess.file_exists(dir + "manifest.json"):
		var man := load_json(dir + "manifest.json")
		if not man.is_empty():
			_packs.append({"dir": dir, "scale": 2, "man": man})
	if _packs.is_empty():
		push_warning("HD doku paketi (x2) bulunamadı; standart dokular kullanılıyor")
		pack = 1
		Ayarlar.pack_missing = true
		Ayarlar.hd_active = 0
		return
	pack_level = 2 if pack >= 4 else 1


func _pack_entry(path: String) -> Dictionary:
	## Bu doku için paket girdisi: {"file": res yolu, "scale": çarpan, "size": temel boyut} ya da boş
	if _packs.is_empty():
		return {}
	var rel := path.trim_prefix("res://assets/")
	for pk in _packs:
		var man: Dictionary = pk["man"]
		if not man.has(rel):
			continue
		var e: Array = man[rel]
		var f: String = String(pk["dir"]) + (String(e[2]) if e.size() > 2 else rel)
		if not ResourceLoader.exists(f):
			continue
		if e.size() > 3 and not _base_matches(path, String(e[3])):
			continue
		return {"file": f, "scale": int(pk["scale"]), "size": Vector2i(int(e[0]), int(e[1]))}
	return {}


var _md5_ok: Dictionary = {}


func _base_matches(path: String, md5: String) -> bool:
	## Temel PNG kaynağı erişilebilirse (proje klasörü) özeti manifesttekiyle aynı mı; dışa aktarılmış oyunda kaynak
	## PNG paketlenmez: özet okunamaz, HD dosya geçerli sayılır.
	if _md5_ok.has(path):
		return _md5_ok[path]
	var ok := true
	if FileAccess.file_exists(path):
		var h := FileAccess.get_md5(path)
		if h != "" and h != md5:
			ok = false
			push_warning("HD doku eski (temel doku değişmiş, hd_paket.py ile yeniden üretin): %s" % path)
	_md5_ok[path] = ok
	return ok


func tex(path: String) -> Texture2D:
	## Renk dokusu: paket etkinse ve bu doku pakette varsa yüksek çözünürlüklü sürüm (temel boyutta raporlanır)
	if _tex_cache.has(path):
		return _tex_cache[path]
	var t: Texture2D = null
	var e := _pack_entry(path)
	if not e.is_empty():
		var t0 := Time.get_ticks_usec()
		# v38: içe aktarılmış BPTC verisi doğrudan dosyadan okunur (_ctex_image); eskiden doku önce GPU'ya yüklenip
		# geri okunuyor (get_image) ve ikinci kez yükleniyordu. Okunamazsa eski yol.
		var img: Image = _ctex_image(String(e["file"]))
		if img == null:
			var big: Texture2D = load(e["file"])
			img = big.get_image() if big else null
		if img != null and not img.is_empty():
			var it := ImageTexture.create_from_image(img)
			it.set_size_override(e["size"])
			it.resource_name = path.get_file()
			t = it
			_pack_hits += 1
		_pack_usec += Time.get_ticks_usec() - t0
	if t == null:
		t = load(path)
	_tex_cache[path] = t
	return t


func _ctex_image(res_path: String) -> Image:
	## v38: içe aktarılmış .ctex dosyasındaki ham (VRAM sıkıştırmalı, mipmap'li) görüntü verisi; GPU'ya yükleme ve geri
	## okuma yok. Biçim (Godot 4 CompressedTexture2D): "GST2", sürüm, g, y, bayraklar, mip sınırı, 3 ayrılmış, veri biçimi
	## (0 = ham görüntü), g16, y16, mip sayısı, Image.Format, veri. Yalnızca ham görüntü (BPTC / S3TC) okunur; WebP / PNG
	## gömülü (kayıpsız) dokular ve beklenmeyen her şey null döner (çağıran eski yola düşer).
	var imp := ConfigFile.new()
	if imp.load(res_path + ".import") != OK:
		return null
	var ctex := ""
	for k in ["path.bptc", "path.s3tc", "path"]:
		if imp.has_section_key("remap", k):
			if k != "path" and not RenderingServer.has_os_feature(k.trim_prefix("path.")):
				continue  # GPU bu sıkıştırmayı desteklemiyor: motorun kendi yükleyicisi çözsün
			ctex = String(imp.get_value("remap", k))
			break
	if ctex == "":
		return null
	var f := FileAccess.open(ctex, FileAccess.READ)
	if f == null or f.get_buffer(4).get_string_from_ascii() != "GST2":
		return null
	f.get_32()  # sürüm
	f.seek(36)
	if f.get_32() != 0:  # veri biçimi: yalnızca ham görüntü
		return null
	var w := f.get_16()
	var h := f.get_16()
	var mips := f.get_32()
	var fmt := f.get_32()
	if w <= 0 or h <= 0 or fmt >= Image.FORMAT_MAX:
		return null
	var n := f.get_length() - f.get_position()
	var data := f.get_buffer(n)
	if data.size() != n:
		return null
	var img := Image.create_from_data(w, h, mips > 0, fmt, data)
	if img == null or img.is_empty():
		return null
	return img


var _budama_bekliyor := false


func budama_planla() -> void:
	## v38: bölüm değişince (Level._exit_tree) yarım saniye sonra budama: o arada yeni bölüm kendi dokularını aldı
	if _budama_bekliyor or not is_inside_tree():
		return
	_budama_bekliyor = true
	get_tree().create_timer(0.5, true, false, true).timeout.connect(budama)


func budama() -> void:
	## v38: önbellekte yalnızca kendisinin tuttuğu paralaks / ön plan şeridi dokuları (eski biyomun katmanları, HD'de biyom
	## başına ~350 MB) bırakılır; biyomdan biyoma VRAM birikmez. Kullanımdaki doku (Sprite2D'ler tutar) kalır; yeniden
	## istenirse diskten yüklenir. Başvuru sayısı: sözlük + bu yerel değişken = 2.
	_budama_bekliyor = false
	var n := 0
	for k in _tex_cache.keys():
		if not String(k).begins_with("res://assets/bg/"):
			continue
		var t: Texture2D = _tex_cache[k]
		if t != null and t.get_reference_count() <= 2:
			_tex_cache.erase(k)
			n += 1
	if n > 0:
		print_verbose("Data.budama: %d arka plan dokusu bırakıldı" % n)


func tex_full(path: String) -> Texture2D:
	## Paket dokusunu GERÇEK boyutunda döndürür (boyut geçersiz kılma yok). TileSet geçersiz kılmayı yok
	## saydığı için karo atlasları bununla yüklenir ve karo boyu pack_scale(path) ile büyütülür; gölgelendiricide
	## textureSize ile ölçeklenen dünya uzayı dokuları (toprak, çayır) da.
	var e := _pack_entry(path)
	if not e.is_empty():
		return load(e["file"])
	return load(path)


func pack_has(path: String) -> bool:
	return not _pack_entry(path).is_empty()


func pack_scale(path: String) -> int:
	## Bu dokunun paketteki gerçek çarpanı (1 = paket yok / temel doku)
	var e := _pack_entry(path)
	return 1 if e.is_empty() else int(e["scale"])


## Görsel stil: elle çizilmiş mürekkep + cel ("v2"). Varlıklar "_v2" adlı dosyalardadır (bengu -> bengu_v2, otuken
## karoları -> otuken_v2 ...). v30: eski v1 piksel stili (--stil=v1) ve dosyaları kaldırıldı.
const STIL := "v2"


func stil_id(id: String, probe: String) -> String:
	## probe: kimliğin yerine geçeceği "%s" içeren yol, ör. "res://assets/sprites/%s.json". "<kimlik>_v2" varsa o,
	## yoksa kimliğin kendisi (zaten stil sürümü olan kimlikler, ör. otuken_v2_0_sky)
	var alt := "%s_%s" % [id, STIL]
	var pth := probe % alt
	if ResourceLoader.exists(pth) or FileAccess.file_exists(pth):
		return alt
	if not id.contains("_" + STIL):  # kimlik zaten stil sürümüyse geri dönüş değil
		PikselIz.iz("stil_id geri dönüşü: " + probe % id)  # "_v2" sürümü yok (denetim: piksel_tara)
	return id


func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--piksel_tara"):
			PikselIz.acik = true  # piksel denetimi (tools/tests/piksel_tara.gd)
	# proje varsayılan doku süzgeci en yakın komşu; kökün varsayılanı doğrusal + mipmap: süzgeci açıkça ayarlanmamış
	# her düğüm (parçacık, etiket, CanvasLayer altı) mürekkep gibi yumuşak çizilir.
	get_tree().root.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	_init_pack()
	items = load_json("res://data/items.json")
	world = load_json("res://data/world.json")
	story = load_json("res://data/story.json")
	# eski silah atlasının meta bilgisi (assets/weapons/weapons.json; dokuları v30'da kaldırıldı): eşya listesi, eski
	# hücre ve pivotları (yerdeki silahın ortalanması, Pickup.gd) ve doku yoğunluğu "texel" (2 = hücre 128x80)
	weapon_meta = load_json("res://assets/weapons/weapons.json")
	weapon_texel = float(weapon_meta.get("texel", 1.0))
	_load_weapon_stil()


var weapon_texel := 1.0


func wscale() -> float:
	## Eski silah hücresinin oyun içi ölçeği (1 / doku yoğunluğu; Pickup.gd ortalama kaydırması dünya biriminde)
	return 1.0 / weapon_texel


func load_json(path: String) -> Dictionary:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		push_error("JSON açılamadı: %s" % path)
		return {}
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	if parsed == null or not (parsed is Dictionary):
		push_error("JSON çözümlenemedi: %s" % path)
		return {}
	return parsed


func canvas_tex(diffuse: String, normal: String) -> CanvasTexture:
	var ct := CanvasTexture.new()
	ct.diffuse_texture = tex(diffuse)
	if ResourceLoader.exists(normal):
		ct.normal_texture = load(normal)
	ct.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	return ct


func sprite(sprite_name: String) -> Dictionary:
	if _sprites.has(sprite_name):
		return _sprites[sprite_name]
	var sid := stil_id(sprite_name, "res://assets/sprites/%s.json")
	var meta := load_json("res://assets/sprites/%s.json" % sid)
	meta["tex"] = canvas_tex("res://assets/sprites/%s.png" % sid, "res://assets/sprites/%s_n.png" % sid)
	if is_linear(meta):
		(meta["tex"] as CanvasTexture).texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	var gp := "res://assets/sprites/%s_e.png" % sid
	meta["glow_tex"] = load(gp) if ResourceLoader.exists(gp) else null
	# sayfalı sayfa (tools/artgen/export_ink.py, json "pages" > 1): satırlar sırayla <ad>.png, <ad>_p1.png ... dokularına
	# bölünür (her biri en çok 4096 px). "page_texs"/"page_glows" sayfa dokuları; SpriteAnim satırın sayfasını seçer.
	var pages := int(meta.get("pages", 1))
	if pages > 1:
		var texs: Array = [meta["tex"]]
		var glows: Array = [meta["glow_tex"]]
		for k in range(1, pages):
			var pid := "%s_p%d" % [sid, k]
			var ct := canvas_tex("res://assets/sprites/%s.png" % pid, "")
			if is_linear(meta):
				ct.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
			texs.append(ct)
			var gpk := "res://assets/sprites/%s_e.png" % pid
			glows.append(load(gpk) if ResourceLoader.exists(gpk) else null)
		meta["page_texs"] = texs
		meta["page_glows"] = glows
	_sprites[sprite_name] = meta
	return meta


func forget_sprite(sprite_name: String) -> void:
	## Büyük sprite sayfalarını (stil v2 bosslar, 20-55 MB VRAM) önbellekten bırakır; dokular son kullanıcısıyla
	## (sahne düğümleri, ceset kopyası) birlikte serbest kalır. Yeniden istenirse diskten yüklenir.
	if not _sprites.has(sprite_name):
		return
	var sid := stil_id(sprite_name, "res://assets/sprites/%s.json")
	_sprites.erase(sprite_name)
	var base := "res://assets/sprites/%s" % sid
	for k in _tex_cache.keys():
		var ks := String(k)
		if ks == base + ".png" or ks.begins_with(base + "_p"):
			_tex_cache.erase(k)


## Stil v2 mürekkep-cel sprite'ları (tools/artgen/inkkit.py; json "filter": "linear"): kenar yumuşatmalı çizim,
## doğrusal süzgeç + mipmap ile ve ink_char.gdshader ile çizilir (piksel-AA ve 3 bantlı toon ışığı yok).
## CanvasTexture süzgeci onu kullanan her düğüme (hayalet, ceset, vuruş karesi) geçer.
const INK_SHADER: Shader = preload("res://shaders/ink_char.gdshader")


static func is_linear(meta: Dictionary) -> bool:
	return String(meta.get("filter", "")) == "linear"


func find_item(id: String) -> Dictionary:
	for cat in ["weapons", "shields", "gadgets"]:
		for it in items[cat]:
			if it["id"] == id:
				var d: Dictionary = it.duplicate(true)
				d["cat"] = cat
				return d
	return {}


func material_def(id: String) -> Dictionary:
	for m in items["materials"]:
		if m["id"] == id:
			return m
	return items["materials"][0]


func has_weapon_sprite(item_id: String) -> bool:
	return (weapon_stil.get("items", {}) as Dictionary).has(item_id)


func weapon_pivot(item_id: String) -> Vector2:
	## Eski silah hücresindeki pivot (weapons.json meta): yerdeki silahın ortalanması için (Pickup.gd)
	var p: Array = weapon_meta["items"][item_id]["pivot"]
	return Vector2(p[0], p[1])


## Mürekkep-cel silah atlası (tools/artgen/weapons_ink.py): weapons_v2.json + sayfalar (weapons_v2_<n>.png).
## Eşya başına sıkı kırpma, pivot kırpma içinde; doğrusal süzgeç + mipmap. Dünyadaki silah sprite'ları ve arayüz
## simgeleri (InkUI.weapon) weapon_sprite() kullanır.
var weapon_stil: Dictionary = {}
var _wst_pages: Array = []
var _wst_imgs: Dictionary = {}
var _wspr_cache: Dictionary = {}


func _load_weapon_stil() -> void:
	var jp := "res://assets/weapons/weapons_%s.json" % STIL
	if not FileAccess.file_exists(jp):
		return
	weapon_stil = load_json(jp)
	for pg in weapon_stil.get("pages", []):
		var ct := CanvasTexture.new()
		ct.diffuse_texture = tex("res://assets/weapons/%s" % pg)
		ct.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		_wst_pages.append(ct)


func weapon_sprite(item_id: String, mat_id: String) -> Dictionary:
	## Dünyadaki silah sprite'ı: {tex, region, pivot, scale, linear, page}. Atlasta olmayan eşya için (has_weapon_sprite
	## yanlış) dokusuz boş bölge.
	var key := item_id + "/" + mat_id
	if _wspr_cache.has(key):
		return _wspr_cache[key]
	var d := {}
	var its: Dictionary = weapon_stil.get("items", {})
	if its.has(item_id) and not _wst_pages.is_empty():
		var e: Dictionary = its[item_id]
		var ms: Dictionary = e["m"]
		var m: Array = ms.get(mat_id, ms.values()[0])
		var sz: Array = e["size"]
		var pv: Array = e["pivot"]
		d = {"tex": _wst_pages[int(m[0])], "region": Rect2(float(m[1]), float(m[2]), float(sz[0]), float(sz[1])),
			"pivot": Vector2(float(pv[0]), float(pv[1])), "scale": 1.0 / float(weapon_stil.get("texel", 4.0)),
			"linear": true, "page": int(m[0])}
	else:
		d = {"tex": null, "region": Rect2(), "pivot": Vector2.ZERO, "scale": 1.0, "linear": true, "page": -1}
	_wspr_cache[key] = d
	return d


func weapon_sprite_image(d: Dictionary) -> Image:
	## weapon_sprite() sözlüğünün doku görüntüsü (yay uçları gibi piksel taramaları için)
	var p := int(d.get("page", -1))
	if p < 0:
		return null
	if not _wst_imgs.has(p):
		# temel sayfa (HD paketi etkin olsa da): bölge koordinatları temel doku pikselinde
		var bt: Texture2D = load("res://assets/weapons/%s" % String(weapon_stil["pages"][p]))
		var img: Image = bt.get_image()
		if img.is_compressed():
			img.decompress()
		_wst_imgs[p] = img
	return _wst_imgs[p]


func enemy_def(id: String) -> Dictionary:
	for e in world["enemies"]:
		if e["id"] == id:
			return e
	return {}
