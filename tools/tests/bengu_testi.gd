extends Node
## v20/v21 Bengü testi (saç fiziği + görünüm). Betikli girdiyle (Input.action_press) oyuncuyu sürer:
##   godot --headless --path . --quit-after 99999 -- --bengu            denetim: saç zinciri uzunluğu / NaN / gövde
##                                                                      çarpışması / dönüşte baş üstü kamçısı / sola
##                                                                      bakarken durgun saç / hayalet saçı / kurt
##                                                                      dönüşümü sonrası sıfırlama / süre ölçümü
##   godot --path . --fixed-fps 60 -- --bengu=C:/mutlak/klasor --pencere=1920x1080 [--doku=2]
##        durgun, koşu, sıçrayış, saldırı, yay germe, yuvarlanma, dönüş çekimleri + koşu→duruş→sıçrayış kare dizisi
##        (<klasor>/dizi/sNNN.png, oyuncu çevresinden kırpılmış)
## Çıktı: "[bengu] ..." satırları, sonda "[bengu] OZET hata=n".

var main: Node
var lv: Node
var pl: Player
var spot := Vector2.ZERO
var out_dir := ""
var hata := 0
var _seq_i := 0
var yakin := false
var _olcum := 0.0
var _olcum_n := 0
var _olcum_max := 0.0
var _dseq := 0
var _dusus_cekildi := false

const ACTS := ["saldiri1", "saldiri2", "zipla", "yuvarlan", "sag", "sol", "yukari", "asagi", "techizat1", "techizat2", "sise", "kut"]


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--bengu="):
			out_dir = String(arg).trim_prefix("--bengu=")
	yakin = OS.get_cmdline_user_args().has("--sac_yakin")
	_run.call_deferred()


func _p(s: String) -> void:
	print("[bengu] ", s)


func _f(n := 1) -> void:
	for i in n:
		await get_tree().physics_frame
		if yakin:  # inceleme: kamera ~2,2 kat yakın (--sac_yakin)
			Game.base_zoom = 3.7
		if pl:
			Game.run["hp"] = float(Game.run["max_hp"])
			if pl.sac and pl.sac.is_visible_in_tree():
				_olcum += pl.sac.olcum_us
				_olcum_n += 1
				_olcum_max = maxf(_olcum_max, pl.sac.olcum_us)


func _release_all() -> void:
	for a in ACTS:
		Input.action_release(a)


func _tap(a: String, frames := 2) -> void:
	Input.action_press(a)
	await _f(frames)
	Input.action_release(a)


func _find_spot() -> Vector2:
	if "boss" in lv and lv.boss != null and is_instance_valid(lv.boss):
		lv.boss.remove_from_group("dusman")
		lv.boss.queue_free()
		lv.boss = null
		return Vector2(24 * Level.TS + 12, lv.surface_y(24) * Level.TS - 1)
	for x in range(20, Level.W - 30):
		var y0: int = lv.surface_y(x)
		var ok := true
		for dx in range(-10, 22):
			if lv.surface_y(x + dx) != y0:
				ok = false
				break
		if ok:
			return Vector2(x * Level.TS + 12, y0 * Level.TS - 1)
	return Vector2(40 * Level.TS + 12, lv.surface_y(40) * Level.TS - 1)


func _clear() -> void:
	for e in get_tree().get_nodes_in_group("dusman"):
		e.remove_from_group("dusman")
		e.queue_free()


func _img() -> Image:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	if get_viewport().use_hdr_2d:
		if img.get_format() != Image.FORMAT_RGBA8 and img.get_format() != Image.FORMAT_RGB8:
			img.convert(Image.FORMAT_RGBA8)
		img.linear_to_srgb()
	return img


func _shot(name: String) -> void:
	if out_dir == "":
		return
	var img: Image = await _img()
	img.save_png(out_dir.path_join(name + ".png"))
	# oyuncu çevresinden kırpılmış yakın çekim (inceleme için)
	var vs := Vector2(img.get_size())
	var sp: Vector2 = pl.get_global_transform_with_canvas().origin * vs / get_viewport().get_visible_rect().size
	var h := int(vs.y * (0.64 if yakin else 0.3))
	var r := Rect2i(int(sp.x - h * 0.6), int(sp.y - h * 0.82), int(h * 1.2), h).intersection(Rect2i(Vector2i.ZERO, img.get_size()))
	img.get_region(r).save_png(out_dir.path_join("k_" + name + ".png"))
	_p("görüntü %s" % name)


func _seq_frame(pre := "s") -> void:
	## kare dizisi: oyuncunun ekran konumu çevresinden kırpılmış (koşu→duruş→sıçrayış saç hareketi; "d": dönüş dizisi)
	if out_dir == "":
		return
	var img: Image = await _img()
	var vs := Vector2(img.get_size())
	var sp: Vector2 = pl.get_global_transform_with_canvas().origin * vs / get_viewport().get_visible_rect().size
	var h := int(vs.y * (0.8 if yakin else 0.42))
	var w := int(h * 1.25)
	var r := Rect2i(int(sp.x - w * 0.5), int(sp.y - h * 0.8), w, h)
	r = r.intersection(Rect2i(Vector2i.ZERO, img.get_size()))
	if pre == "s":
		img.get_region(r).save_png(out_dir.path_join("dizi/s%03d.png" % _seq_i))
		_seq_i += 1
	else:
		img.get_region(r).save_png(out_dir.path_join("dizi/%s%03d.png" % [pre, _dseq]))
		_dseq += 1


# ------------------------------------------------------------------ denetim
func _check(tag: String) -> void:
	## saç zincirlerinin sağlığı: NaN yok, parça boyları korunuyor, uçlar kökten makul uzaklıkta, gövdenin önüne geçmiyor
	var s: BenguSac = pl.sac
	if s == null:
		hata += 1
		_p("HATA %s: saç yok" % tag)
		return
	if not s.is_visible_in_tree():
		return
	if OS.get_cmdline_user_args().has("--sac_iz"):
		var oz = _zincir("yakin_orgu")
		var ps := []
		for i in oz.n:
			ps.append(str((oz.p[i] - oz.r1).round()))
		_p("  örgü %s a=%.2f f=%d anim=%s: %s" % [tag, oz.a1, pl.facing, pl.anim.anim, " ".join(ps)])
	for z in s.zincirler:
		var worst := 0.0
		for i in range(1, z.n):
			var d: float = (z.p[i] - z.p[i - 1]).length()
			if is_nan(d) or is_inf(d):
				hata += 1
				_p("HATA %s: %s NaN" % [tag, z.ad])
				return
			worst = maxf(worst, (d - z.seg) / z.seg)  # yalnızca uzama (yerde yığılma serbest)
		var reach: float = (z.p[z.n - 1] - z.r1).length()
		if worst > 0.06 or reach > z.seg * z.n * 1.06:
			hata += 1
			_p("HATA %s: %s uzama=%.3f erim=%.1f" % [tag, z.ad, worst, reach])


func _front_ratio() -> float:
	## at kuyruğunun gövdenin önüne geçen nokta oranı (durgunken ~0 olmalı)
	var z = _zincir("kuyruk")
	var n := 0
	for i in range(3, z.n):
		if (z.p[i].x - pl.global_position.x) * float(pl.facing) > 3.0:
			n += 1
	return float(n) / float(z.n - 3)


func _dump() -> void:
	for z in pl.sac.zincirler:
		var ps := []
		for i in z.n:
			ps.append(str((z.p[i] - z.r1).round()))
		_p("  %s kök=%s a=%.2f v=%s: %s" % [z.ad, str((z.r1 - pl.global_position).round()), z.a1, str(pl.velocity.round()), " ".join(ps)])


func _zincir(ad: String):
	for z in pl.sac.zincirler:
		if z.ad == ad:
			return z
	return null


func _bas_ustu() -> float:
	## yelenin baş üstüne / yüz önüne geçen en kötü noktası: başlık tepesinin ne kadar üstünde (birim; > 0 kamçı)
	var z = _zincir("kuyruk")
	var hd: Variant = pl.anim.anchor("head")
	var top: Vector2 = pl.anim.to_global(hd if hd != null else Vector2(0, -47)) + Vector2(0, -6)
	var worst := -99.0
	for i in range(3, z.n):
		var q: Vector2 = z.p[i]
		if (q.x - top.x) * float(pl.facing) > -2.0:  # başın önü / tam üstü
			worst = maxf(worst, top.y - q.y)
	return worst


func _tip(ad: String) -> Vector2:
	for z in pl.sac.zincirler:
		if z.ad == ad:
			return z.p[z.n - 1] - z.r1
	return Vector2.ZERO


func _run() -> void:
	await get_tree().create_timer(0.6).timeout
	lv = main.level
	pl = lv.player
	_clear()
	main.hud.set("_card_t", 100.0)  # bölüm başlık kartı çekimleri örtmesin
	spot = _find_spot()
	_p("arena=%s stil=%s sac=%s" % [str(spot), Data.stil, str(pl.sac != null)])
	if out_dir != "":
		DirAccess.make_dir_recursive_absolute(out_dir.path_join("dizi"))
	Game.run["slots"]["melee"] = ItemGen.roll("alp_kilici", 1, "demir", 0)
	Game.run["slots"]["second"] = ItemGen.roll("turk_yayi", 1, "demir", 0)
	pl.on_equip()
	pl.global_position = spot
	pl.velocity = Vector2.ZERO
	pl.facing = 1
	if OS.get_cmdline_user_args().has("--sac_govdesiz"):  # hata ayıklama: sırt çarpışması kapalı
		for z in pl.sac.zincirler:
			z.govde = false
	if OS.get_cmdline_user_args().has("--sac_renk"):  # hata ayıklama: saç şeritlerini parlak renkle göster
		pl.sac.mat.set_shader_parameter("base_col", Color(1, 1, 0))
		pl.sac.mat.set_shader_parameter("deep_col", Color(0.8, 0.8, 0))
		pl.sac.mat.set_shader_parameter("shade_col", Color(1, 0.5, 0))
		pl.sac.mat.set_shader_parameter("ink_col", Color(1, 0, 0))
		pl.sac.mat.set_shader_parameter("hi_col", Color(0, 1, 0))
		pl.sac.mat.set_shader_parameter("band_col", Color(0, 0, 1))
		pl.sac.mat.set_shader_parameter("flash_color", Color(1, 0, 1))
	await _f(90)
	_check("durgun")
	var fr := _front_ratio()
	var dinlen_x := _tip("kuyruk").x
	_p("durgun: uç(kuyruk)=%s önde=%.2f" % [str(_tip("kuyruk").round()), fr])
	_dump()
	if fr > 0.25:
		hata += 1
		_p("HATA durgun: saç gövdenin önünde")
	await _shot("1_durgun")
	# ---- koşu → duruş → sıçrayış (kare dizisi)
	Input.action_press("sag")
	for i in 50:
		await _f()
		if i % 2 == 0:
			await _seq_frame()
		_check("koşu")
		if OS.get_cmdline_user_args().has("--sac_iz") and i % 5 == 0:
			_dump()
	_dump()
	var tr := _tip("kuyruk")
	_p("koşu: uç(kuyruk)=%s (arkaya akmalı: x<0)" % str(tr.round()))
	if tr.x > -6.0:
		hata += 1
		_p("HATA koşu: saç arkaya akmıyor")
	await _shot("2_kosu")
	Input.action_release("sag")
	var salin := -99.0
	for i in 40:
		await _f()
		salin = maxf(salin, _tip("kuyruk").x)
		if i % 2 == 0:
			await _seq_frame()
	var dur_son := _tip("kuyruk")
	_p("duruş: en öne salınım uç.x=%.1f (durgun %.1f), sonra=%s (öne salınıp arkaya yerleşmeli)" % [salin, dinlen_x, str(dur_son.round())])
	if salin < dinlen_x + 2.0:
		hata += 1
		_p("HATA duruş: saç öne salınmıyor (ip gibi)")
	Input.action_press("zipla")
	for i in 56:
		await _f()
		if i == 14:
			Input.action_release("zipla")
		if i % 2 == 0:
			await _seq_frame()
		if i == 10:
			var tj := _tip("kuyruk")
			_p("sıçrayış (yükseliş): uç=%s (aşağı sarkmalı)" % str(tj.round()))
			await _shot("3_sicrayis")
		if pl.velocity.y > 320.0 and not _dusus_cekildi:
			_dusus_cekildi = true
			_p("düşüş: uç=%s v=%s (saç yukarı kalkmalı: uç.y küçülür)" % [str(_tip("kuyruk").round()), str(pl.velocity.round())])
			await _shot("3b_dusus")
		_check("sıçrayış")
	await _f(20)
	# ---- saldırı
	await _tap("saldiri1", 2)
	await _f(7)
	await _shot("4_saldiri")
	await _f(40)
	_check("saldırı")
	# ---- yay germe
	Input.action_press("saldiri2")
	await _f(30)
	await _shot("5_yay")
	Input.action_release("saldiri2")
	await _f(40)
	# ---- yuvarlanma
	Input.action_press("sag")
	await _f(10)
	await _tap("yuvarlan", 2)
	for i in 6:
		await _f()
		if OS.get_cmdline_user_args().has("--sac_iz"):
			_dump()
	await _shot("6_yuvarlanma")
	for i in 10:
		await _f()
		if OS.get_cmdline_user_args().has("--sac_iz"):
			_dump()
	_check("yuvarlanma")
	Input.action_release("sag")
	await _f(30)
	# ---- dönüş: sola koş (saç kesmeden öbür yana geçmeli)
	var before := _tip("kuyruk")
	_p("dönüş öncesi f=%d anim=%s v=%s" % [pl.facing, pl.anim.anim, str(pl.velocity.round())])
	Input.action_press("sol")
	var kamci := -99.0
	for i in 34:
		await _f()
		kamci = maxf(kamci, _bas_ustu())
		if OS.get_cmdline_user_args().has("--sac_iz"):
			var zz = _zincir("kuyruk")
			_p("  iz %d f=%d v=%s a=%.2f uç=%s orta=%s anim=%s" % [i, pl.facing, str(pl.velocity.round()), zz.a1, str(_tip("kuyruk").round()), str((zz.p[6] - zz.r1).round()), pl.anim.anim])
		if i % 2 == 0:
			await _seq_frame("d")
		if i == 3:
			await _shot("7_donus")
		_check("dönüş")
	var after := _tip("kuyruk")
	Input.action_release("sol")
	_p("dönüş: baş üstü en kötü=%.1f (<= 0 olmalı: saç başın üstünden öne kamçılanmaz)" % kamci)
	if kamci > 0.0:
		hata += 1
		_p("HATA dönüş: saç başın üstünden öne kamçılandı")
	_p("dönüş: uç önce=%s sonra=%s" % [str(before.round()), str(after.round())])
	if after.x < 4.0:
		hata += 1
		_p("HATA dönüş: saç sola dönünce sağa (arkaya) geçmedi")
	# yerinde dönüş dizisi: sağa, sonra sola kısa dokunuş
	for yon in ["sag", "sol"]:
		await _f(24)
		await _tap(yon, 3)
		for i in 24:
			await _f()
			kamci = maxf(kamci, _bas_ustu())
			if i % 3 == 0:
				await _seq_frame("d")
	_p("yerinde dönüş: baş üstü en kötü=%.1f" % kamci)
	if kamci > 0.0:
		hata += 1
		_p("HATA yerinde dönüş: saç başın üstünden öne kamçılandı")
	for k in 6:
		await _f(25)
		if OS.get_cmdline_user_args().has("--sac_iz"):
			_dump()
	_check("dönüş")
	# sola bakarken durgun saç öne (yüz yanına) sürüklenmemeli (eski sürümde sürekli sol esinti vardı)
	var fl := _front_ratio()
	_p("sola durgun: uç=%s önde=%.2f" % [str(_tip("kuyruk").round()), fl])
	_dump()
	if pl.facing < 0 and fl > 0.25:
		hata += 1
		_p("HATA sola durgun: saç öne sürükleniyor")
	await _shot("8_sol_durgun")
	# hayalet izi: saçlı kopya da çıkmalı
	var nk := FX.root.get_child_count()
	FX.ghost(pl.anim.base, Color(0.55, 0.85, 1.0, 0.5), 0.3)
	var kopya := 0
	for i in range(nk, FX.root.get_child_count()):
		if FX.root.get_child(i) is BenguSac.Kopya:
			kopya += 1
	_p("hayalet: saç kopyası=%d (1 olmalı)" % kopya)
	if kopya != 1:
		hata += 1
		_p("HATA hayalet: saç kopyası yok")
	# darbe karesi: beyaz siluette saç da olmalı
	ImpactFrame.play([pl], 1.0, 2, true)
	var dk := 0
	if ImpactFrame._active:
		for ch in ImpactFrame._active.get_children():
			if ch is BenguSac.Kopya:
				dk += 1
	_p("darbe karesi: saç kopyası=%d (1 olmalı)" % dk)
	if dk != 1:
		hata += 1
		_p("HATA darbe karesi: saç yok")
	await _f(6)
	# ---- kurt dönüşümü: saç gizlenir, dönünce dinlenme duruşundan başlar
	if pl.has_method("_begin_wolf"):
		pl.call("_begin_wolf")
		await _f(30)
		var vis: bool = pl.sac.is_visible_in_tree()
		_p("kurt: saç görünür=%s (false olmalı) kurt=%s" % [str(vis), str(pl.wolf_anim.visible)])
		if vis:
			hata += 1
		await _shot("9_kurt")
		pl.call("_end_wolf")
		await _f(3)
		_check("kurt sonrası")
		await _f(30)
		_p("kurt sonrası: saç görünür=%s uç=%s" % [str(pl.sac.is_visible_in_tree()), str(_tip("kuyruk").round())])
		await _shot("10_kurt_sonrasi")
	_release_all()
	_p("saç süresi: ortalama %.3f ms, en çok %.3f ms / kare (benzetim + çizim verisi, %d kare)" % [_olcum / maxf(1.0, _olcum_n) / 1000.0, _olcum_max / 1000.0, _olcum_n])
	_p("OZET hata=%d" % hata)
	get_tree().quit()
