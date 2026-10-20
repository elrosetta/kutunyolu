class_name Prof
extends RefCounted
## v38 hafif profil ölçer (yalnızca -- --perf): sıcak _process / _physics_process / _draw gövdeleri
## "if Prof.on: var t0 := Time.get_ticks_usec(); ...; Prof.ekle(&"ad", t0)" ile sarılır. Kapalıyken tek bir
## statik bool okuması kalır. tools/tests/perf_testi.gd sistem başına ms tablosunu buradan yazar.

static var on := false
static var acc: Dictionary = {}   # ad -> toplam mikro saniye
static var say: Dictionary = {}   # ad -> çağrı sayısı


static func ekle(ad: StringName, t0: int) -> void:
	var dt := Time.get_ticks_usec() - t0
	if acc.has(ad):
		acc[ad] += dt
		say[ad] += 1
	else:
		acc[ad] = dt
		say[ad] = 1


static func sifirla() -> void:
	acc.clear()
	say.clear()
