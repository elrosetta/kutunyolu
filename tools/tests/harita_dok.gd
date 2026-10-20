extends SceneTree
## v32 üretici dökümü: her stil × tohum için bölümü üretir, ölçümleri yazar ve genel görünüm PNG'si döker
## (4 px / karo; katı kahve, platform sarı, tehlike kızıl, oda çerçeveleri, kapılar, ana yol, Kut Taşları, ödüller).
## Kullanım: godot --headless --path . --script res://tools/tests/harita_dok.gd -- [--dok_cikti=KLASÖR] [--dok_tohum=N]
##          [--dok_stil=orman] [--dok_pazar] [--dok_yanyana=DOSYA.png: üç stil (orman, mağara, kuyu) yan yana tek görüntü]

## Level.W x Level.H (v33: 172 x 56; --script kipinde Level sınıfı yüklenmez: otomatik yüklemeler yok)
const W := 172
const H := 56


func _arg(name: String, def: String) -> String:
	for a in OS.get_cmdline_user_args():
		if String(a).begins_with(name + "="):
			return String(a).trim_prefix(name + "=")
	return def


func _init() -> void:
	var out := _arg("--dok_cikti", "")
	var n := int(_arg("--dok_tohum", "3"))
	var only := _arg("--dok_stil", "")
	var pazar := OS.get_cmdline_user_args().has("--dok_pazar")
	if out != "":
		DirAccess.make_dir_recursive_absolute(out)
	var t0 := Time.get_ticks_msec()
	var tot := 0
	var ok_n := 0
	var sums := {}
	for style in LevelGen.STYLES:
		if only != "" and style != only:
			continue
		for k in n:
			var rng := RandomNumberGenerator.new()
			rng.seed = 1000 + k * 7919 + style.length() * 31
			var r := LevelGen.generate(rng, W, H, 3, [style], {"pazar": pazar})
			var m: Dictionary = r["metrics"]
			tot += 1
			if bool(m["ok"]):
				ok_n += 1
			for key in m:
				if typeof(m[key]) in [TYPE_INT, TYPE_FLOAT, TYPE_BOOL]:
					sums[key] = float(sums.get(key, 0.0)) + float(m[key])
			var reach := LevelGen.reach_set(r["grid"], W, H, r["heights"])
			var nreach := 0
			var nstand := 0
			var gh := LevelGen._haz_as_air(r["grid"])
			for y in H:
				for x in W:
					if LevelGen._standable(gh, x, y, W, H):
						nstand += 1
						if reach[y * W + x] == 1:
							nreach += 1
			var span := _span(r)
			print("[dok] stil=%s tohum=%d ok=%s deneme=%d oda=%d ana=%d dal=%d çıkmaz=%d döngü=%d geniş=%d yüksek=%d dikey_adım=%d satır=%d kapı=%d taşı=%d zamanlı=%d ulaşılan=%d/%d (%%%.0f) düşey_aralık=%d karo onarım=%d" % [
				style, k, str(m["ok"]), int(m["attempts"]), int(m["oda"]), int(m["ana"]), int(m["dal"]), int(m["cikmaz"]), int(m["dongu"]), int(m["genis"]), int(m["yuksek"]),
				int(m["dikey_adim"]), int(m["satir"]), int(m["kapi"]), int(m["tasi"]), int(m["zamanli"]), nreach, nstand, 100.0 * nreach / maxf(1.0, nstand), span, int(m["trapfix"])])
			if out != "":
				_dump(r, out.path_join("dok_%s_%d.png" % [style, k]), reach)
	print("[dok] TOPLAM bölüm=%d ok=%d süre=%d ms" % [tot, ok_n, Time.get_ticks_msec() - t0])
	var parts: Array = []
	for key in ["oda", "ana", "dal", "cikmaz", "dongu", "genis", "yuksek", "dikey_adim", "satir", "kapi", "tasi", "zamanli", "trapfix", "attempts"]:
		parts.append("%s=%.2f" % [key, float(sums.get(key, 0.0)) / maxf(1.0, tot)])
	print("[dok] ORTALAMA " + " ".join(parts))
	var yy := _arg("--dok_yanyana", "")
	if yy != "":
		_yanyana(yy, int(_arg("--dok_yy_tohum", "1")))
	quit()


func _yanyana(path: String, k: int) -> void:
	## Üç stilin (orman, mağara, kuyu) dökümü üst üste değil yan yana: 4 px / karo, aralarında 24 px boşluk
	var imgs: Array = []
	for style in ["orman", "magara", "kuyu"]:
		var rng := RandomNumberGenerator.new()
		rng.seed = 1000 + k * 7919 + style.length() * 31
		var r := LevelGen.generate(rng, W, H, 3, [style], {"pazar": true})
		var tmp := OS.get_user_data_dir().path_join("dok_tmp_%s.png" % style)
		_dump(r, tmp, LevelGen.reach_set(r["grid"], W, H, r["heights"]))
		var im := Image.load_from_file(tmp)
		var b: Rect2i = r["bounds"]
		imgs.append(im.get_region(Rect2i(b.position * 4, b.size * 4)))
	var tw := 0
	var th := 0
	for im in imgs:
		tw += im.get_width() + 24
		th = maxi(th, im.get_height())
	var out := Image.create(tw - 24, th, false, Image.FORMAT_RGB8)
	out.fill(Color(0.05, 0.05, 0.07))
	var x := 0
	for im in imgs:
		out.blit_rect(im, Rect2i(Vector2i.ZERO, im.get_size()), Vector2i(x, 0))
		x += im.get_width() + 24
	out.save_png(path)
	print("[dok] yan yana: ", path)


func _span(r: Dictionary) -> int:
	var lo := 999
	var hi := 0
	for rm in r["rooms"]:
		if rm["role"] == "yok":
			continue
		for v in rm["fl"]:
			lo = mini(lo, int(v))
			hi = maxi(hi, int(v))
	return hi - lo


func _dump(r: Dictionary, path: String, reach: PackedByteArray) -> void:
	var S := 4
	var g: PackedByteArray = r["grid"]
	var img := Image.create(W * S, H * S, false, Image.FORMAT_RGB8)
	for y in H:
		for x in W:
			var c := Color(0.1, 0.09, 0.12)
			match g[y * W + x]:
				1:
					c = Color(0.5, 0.38, 0.28)
				2:
					c = Color(0.95, 0.8, 0.3)
				3:
					c = Color(0.85, 0.15, 0.12)
			if g[y * W + x] == 0 and reach[y * W + x] == 1 and y > 0 and (g[(y + 1) * W + x] == 1 or g[(y + 1) * W + x] == 2):
				c = Color(0.2, 0.3, 0.22)
			img.fill_rect(Rect2i(x * S, y * S, S, S), c)
	for rm in r["rooms"]:
		if rm["role"] == "yok":
			continue
		var col := Color(0.3, 0.6, 1.0)
		match rm["role"]:
			"giris":
				col = Color(0.3, 1.0, 0.4)
			"cikis":
				col = Color(1.0, 0.5, 0.2)
			"dal":
				col = Color(0.8, 0.5, 1.0)
			"odul":
				col = Color(1.0, 0.95, 0.4)
		var rr := Rect2i(int(rm["ix0"]) * S, int(rm["iy0"]) * S, (int(rm["ix1"]) - int(rm["ix0"]) + 1) * S, (int(rm["iy1"]) - int(rm["iy0"]) + 1) * S)
		_rect_outline(img, rr, col)
	for d in r["doors"]:
		if d["kind"] == "sil":
			continue
		var dc := Color(0.2, 0.9, 1.0) if d["kind"] != "dongu" else Color(1.0, 0.4, 0.9)
		if d["dir"] == "h":
			img.fill_rect(Rect2i(int(d["x"]) * S, (int(d["y"]) - int(d.get("h", 5))) * S - 2, (int(d.get("x2", int(d["x"]) + 3)) - int(d["x"]) + 1) * S, 2), dc)
		else:
			img.fill_rect(Rect2i(int(d["x"]) * S, int(d["y"]) * S - 2, 6 * S, 2), dc if bool(d.get("acik", false)) else Color(1.0, 0.6, 0.2))
	for t in r["tasi"]:
		img.fill_rect(Rect2i(int(t.x) * S - 2, int(t.y) * S - 4, S + 4, S + 6), Color(0.3, 1.0, 1.0))
	for ch in r["chunks"]:
		for mk in ch["marks"]:
			var mc: Color = {"T": Color(1, 0.85, 0.2), "S": Color(1, 0.6, 1), "E": Color(1, 0.2, 0.2), "M": Color(0.6, 1, 0.5), "P": Color(1, 0.7, 0.3), "Z": Color(0.9, 0.9, 1)}.get(String(mk[0]), Color.WHITE)
			img.fill_rect(Rect2i(int(mk[1]) * S - 1, int(mk[2]) * S - 3, S + 2, S + 4), mc)
	for z in r["zamanli"]:
		img.fill_rect(Rect2i(int(z["x"]) * S, (int(z["y"]) - 5) * S, 2, 5 * S), Color(1, 1, 1))
	var sp: Vector2i = r["spawn"]
	img.fill_rect(Rect2i(sp.x * S - 2, sp.y * S - 6, S + 4, S + 6), Color(0.2, 1.0, 0.3))
	var ex: Vector2i = r["exit"]
	img.fill_rect(Rect2i(ex.x * S - 2, ex.y * S - 6, S + 4, S + 6), Color(1.0, 0.4, 0.1))
	img.save_png(path)


func _rect_outline(img: Image, r: Rect2i, c: Color) -> void:
	img.fill_rect(Rect2i(r.position.x, r.position.y, r.size.x, 1), c)
	img.fill_rect(Rect2i(r.position.x, r.end.y - 1, r.size.x, 1), c)
	img.fill_rect(Rect2i(r.position.x, r.position.y, 1, r.size.y), c)
	img.fill_rect(Rect2i(r.end.x - 1, r.position.y, 1, r.size.y), c)
