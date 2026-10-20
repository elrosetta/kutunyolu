class_name Rehber
extends RefCounted
## v32 bot rehberi (--otomatik): dallı bölümde hedef seçer (önce keşfedilmemiş ödül odaları / Kut Taşları, sonra
## Kut Kapısı), LevelGen._moves modeliyle hücre yolu bulur ve yol noktalarına göre tuşlara basar (yürü, zıpla, çift
## zıpla, platformdan aşağı in). Hedef uzaksa ve bulunmuş bir Kut Taşı hedefe daha yakınsa ışınlanır (bazen harita
## ekranı üzerinden: Main "harita" kipi). Takılınca yeniden plan yapar.
## v33: küçük bölümde kuyu kapağından aşağı + zıpla ile iner (aşağı basılı tutulur, Main bu sırada saldırmaz / rastgele
## zıplamaz), zıplama dokunuşu iki kare basılı kalır; keşif sıçraması yalnızca aynı hedefte 40 sn takılınca.

var level: Node
var path: Array = []
var pi := 0
var hedef := Vector2i(-1, -1)
var hedef_tur := ""
var ziyaret: Dictionary = {}     # ödül odası kimliği -> true
var replan_t := 0.0
var stuck_t := 0.0
var last_x := 0.0
var isin_sayac := 0
var ui_isin := 0
var hedef_sayac := 0
var _jump_cd := 0.0
var _kesif_t := 0.0
var _basili: Array = []
## v33: dokunuş (zıpla) iki fizik karesi basılı kalır: Input.action_press'in "yeni basıldı"sı oyuncuya bir sonraki karede
## görünür; tek karelik basış ondan önce bırakılıyor, zıplama / kapaktan inme çoğu kez yutuluyordu
var _dokunus: Dictionary = {}
var iniyor := false       # v33: tek yönlü kapaktan / platformdan aşağı iniyor (Main saldırı basmasın, takılma sayılmasın)


func reset(lv: Node) -> void:
	level = lv
	path = []
	pi = 0
	hedef = Vector2i(-1, -1)
	hedef_tur = ""
	ziyaret = {}
	replan_t = 0.0
	stuck_t = 0.0
	hedef_sayac = 0


func _hedef_sec(pl: Node) -> void:
	## Önce 2 ödül odası (en yakın), sonra çıkış; her 4. hedefte çıkışa gider
	hedef_tur = "cikis"
	hedef = level.exit_cell
	_kesif_t = 0.0   # v33: keşif sıçraması yalnızca aynı hedefte 40 sn ilerleyemeyince (küçük bölümde geri ışınlanmasın)
	var cands: Array = []
	for rm in level.rooms:
		if rm["role"] != "odul" or ziyaret.has(int(rm["id"])):
			continue
		var c: Vector2i = LevelGen._floor_spot(level.grid, level.W, level.H, rm, LevelGen._odul_mid(rm))
		cands.append([int(rm["id"]), c])
	# v33: can %55'in altındaysa ödül odalarına sapmadan Kut Kapısı'na (dövüşmeyen bot derin bölümde ölmesin)
	var can_ok: bool = float(Game.run.get("hp", 1.0)) >= 0.55 * float(Game.run.get("max_hp", 1.0))
	if not cands.is_empty() and hedef_sayac % 4 != 3 and ziyaret.size() < 3 and can_ok:
		var best: Array = cands[0]
		var bd := 1e9
		for cd in cands:
			var d: float = Vector2(cd[1]).distance_to(pl.global_position / float(level.TS))
			if d < bd:
				bd = d
				best = cd
		hedef_tur = "odul:%d" % int(best[0])
		hedef = best[1]
	hedef_sayac += 1


func _plan(pl: Node) -> void:
	var W: int = level.W
	var H: int = level.H
	var s := LevelGen.stand_cell(level.grid, W, H, pl.global_position.x, pl.global_position.y, level.TS)
	path = LevelGen.path_cells(level.grid, W, H, s.x, s.y, hedef.x, hedef.y)
	pi = 1
	replan_t = 2.5
	# uzaksa ve bulunmuş taş hedefe daha yakınsa ışınlan
	if path.size() > 40 and level.harita:
		var best := -1
		var bl := path.size() - 20
		for i in level.harita.bulunan():
			if i == level.tasi_yakin():
				continue
			var tc: Vector2i = level.harita.tasi[i]["cell"]
			var p2 := LevelGen.path_cells(level.grid, W, H, tc.x, tc.y, hedef.x, hedef.y)
			if not p2.is_empty() and p2.size() < bl:
				bl = p2.size()
				best = i
		if best >= 0 and level.isin_t <= 0.0:
			isin_sayac += 1
			if isin_sayac % 2 == 0:
				# harita ekranı üzerinden (Main "harita" kipi seçimi yapar)
				level.harita_istek = best
			else:
				level.isinlan(best)
			path = []
			replan_t = 1.5


func adim(main: Node, pl: Node, delta: float) -> void:
	## Her fizik karesinde: tuşları basar (Main _auto_pressed ile bırakır)
	if level == null or level != main.level:
		reset(main.level)
	for a in _basili:
		Input.action_release(a)
	_basili.clear()
	for a in _dokunus.keys():
		_dokunus[a] = int(_dokunus[a]) - 1
		if int(_dokunus[a]) <= 0:
			Input.action_release(a)
			_dokunus.erase(a)
	if level == null or level.player == null or bool(pl.get("dead")) or level.hub or level.boss_id != "":
		if level and level.boss_id != "" and level.boss != null:
			_press("sag")
		return
	replan_t -= delta
	_jump_cd -= delta
	_kesif_t += delta
	var TS: float = float(level.TS)
	var feet: Vector2 = pl.global_position
	# keşif sıçraması: aynı hedefe 40 sn varılamadıysa, 2+ taş bulunduysa en uzak bulunmuş taşa ışınlan
	if _kesif_t > 40.0 and level.harita and level.isin_t <= 0.0 and level.harita.bulunan().size() >= 2:
		_kesif_t = 0.0
		var far := -1
		var fd := 0.0
		for i in level.harita.bulunan():
			var d: float = Vector2(level.harita.tasi[i]["cell"]).distance_to(feet / TS)
			if d > fd and i != level.tasi_yakin():
				fd = d
				far = i
		if far >= 0:
			isin_sayac += 1
			if isin_sayac % 2 == 0:
				level.harita_istek = far
			else:
				level.isinlan(far)
			path = []
			replan_t = 1.5
			return
	# hedef ziyaret edildi mi
	if hedef_tur.begins_with("odul:") and Vector2(hedef).distance_to(feet / TS) < 6.0:
		ziyaret[int(hedef_tur.trim_prefix("odul:"))] = true
		hedef = Vector2i(-1, -1)
	if hedef_tur.begins_with("odul:") and float(Game.run.get("hp", 1.0)) < 0.55 * float(Game.run.get("max_hp", 1.0)):
		hedef = Vector2i(-1, -1)   # v33: can azaldı: ödülü bırak, kapıya
	if hedef.x < 0 or (hedef_tur == "cikis" and ziyaret.size() < 3 and hedef_sayac % 4 == 3 and false):
		_hedef_sec(pl)
		path = []
	if level.isin_t > 0.0:
		return   # ışınlanma kanalı: kıpırdama
	if path.is_empty() or replan_t <= 0.0:
		_plan(pl)
		if path.is_empty():
			# yol yok: hedefi değiştir, rastgele kıpırda
			_hedef_sec(pl)
			_press("sag" if int(feet.x / TS) % 2 == 0 else "sol")
			if _jump_cd <= 0.0:
				_tap("zipla")
				_jump_cd = 0.4
			return
	# takılma (v33: platformdan inmeye çalışırken sayılmaz)
	if absf(feet.x - last_x) < 1.5 and not iniyor:
		stuck_t += delta
	else:
		stuck_t = 0.0
	last_x = feet.x
	if stuck_t > 1.0:
		stuck_t = 0.0
		replan_t = 0.0
		_tap("zipla")
		return
	# yol noktası
	while pi < path.size():
		var id: int = path[pi]
		var wp := Vector2((id % level.W) * TS + TS * 0.5, (id / level.W) * TS + TS - 1.0)
		if absf(wp.x - feet.x) < 9.0 and absf(wp.y - feet.y) < 14.0:
			pi += 1
			continue
		break
	if pi >= path.size():
		path = []
		return
	var id2: int = path[pi]
	var wp2 := Vector2((id2 % level.W) * TS + TS * 0.5, (id2 / level.W) * TS + TS - 1.0)
	var dx := wp2.x - feet.x
	var dy := wp2.y - feet.y   # negatif: hedef yukarıda
	var on_floor: bool = pl.is_on_floor()
	iniyor = false
	if absf(dx) > 4.0:
		_press("sag" if dx > 0.0 else "sol")
	if dy < -14.0:
		# yukarı: yerdeysen zıpla, havada düşmeye başladıysan çift zıpla
		if on_floor and _jump_cd <= 0.0:
			_tap("zipla")
			_jump_cd = 0.25
		elif not on_floor and float(pl.get("velocity").y) > 40.0 and int(pl.get("air_jumps")) > 0 and _jump_cd <= 0.0:
			_tap("zipla")
			_jump_cd = 0.3
	elif dy > 14.0 and on_floor:
		# aşağı: platformdaysan düşerek in; uçurum kenarı değilse yürü
		var cx := int(floor(feet.x / TS))
		var cy := int(floor((feet.y + 4.0) / TS))
		if level.cell(cx, cy) == 2:
			# v33: aşağı basılı tutulur, zıplama 0,3 sn'de bir (saldırı tamponu zıplamayı yutmasın: Main saldırmaz)
			iniyor = true
			_press("asagi")
			if _jump_cd <= 0.0 and float(pl.get("roll_t")) <= 0.0:
				_tap("zipla")
				_jump_cd = 0.3
		elif absf(dx) > 1.0:
			_press("sag" if dx > 0.0 else "sol")   # kenara / kapağın üstüne yürü
	elif absf(dx) > TS * 2.2 and on_floor and _jump_cd <= 0.0:
		# geniş boşluk: zıplayarak geç
		var cx := int(floor((feet.x + signf(dx) * TS * 1.2) / TS))
		var cy := int(floor((feet.y + 4.0) / TS))
		if level.cell(cx, cy) == 0 or level.cell(cx, cy) == 3:
			_tap("zipla")
			_jump_cd = 0.35


func _press(a: String) -> void:
	Input.action_press(a)
	_basili.append(a)


func _tap(a: String) -> void:
	if _dokunus.has(a):
		return
	Input.action_press(a)
	_dokunus[a] = 2
