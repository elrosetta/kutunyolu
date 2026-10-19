class_name Silah27
extends Node2D
## v27 yeni silahlar (docs/TASARIM.md "v27: yeni silahlar"). Dört yakın, üç uzak silah; her birinin oyunda daha önce
## olmayan bir mekaniği var. Player.gd yalnızca kanca noktalarından çağırır (savuruş tabloları, kombo / ağır seçimi,
## vuruş başı, isabet, hasar, ikincil girdi, silah pozu); durum ve çizim bu düğümde (oyuncunun çocuğu, top_level:
## küresel koordinatta çizer).
##   Gün-Ay İkizi     "durus"      basılı tut: Gün (birleşik çift ağız, çarklar) / Ay (ikiz hilal kılıç) duruşu değişir
##   Kistin           "dolama"     üçüncü savuruş zinciri düşmana dolar; yeniden bas: Yere Çalma (baş üstünden arkaya)
##   Albastı Hançeri  "albasti"    vuruşlar al izi bırakır; basılı tut: izli düşmanın arkasında belirip saplama
##   Çevgen           "top_gibi"   bitiriş / ağır vuruş düşmanı top gibi fırlatır; çarptığı düşmanları da fırlatır
##   Tatar Yayı       "kurma"      ağır delici ok; kurma çubuğunun altın yerinde basınca Kusursuz Kurma
##   Kam Küzgüsü      "kizginlik"  basılı tut: aynı düşmanda kızan ışın; ayna ısınır, tam ısınınca Gün Patlaması
##   Tengri Bağı      "bag"        gök düğümü düşmanları birbirine bağlar (hasar paylaşılır); yeniden bas: Bağ Çekişi
## v22 kontrol ilkesi: hiçbir mekanik kendiliğinden saldırı atmaz; hepsi oyuncunun basışından ya da kendi isabetinden.

const IDS := ["gun_ay_ikizi", "kistin", "albasti_hanceri", "cevgen", "tatar_yayi", "kam_kuzgusu", "tengri_bagi"]
const SEC_IDS := ["tatar_yayi", "kam_kuzgusu", "tengri_bagi"]

## ------------------------------------------------------------------ savuruşlar (Player.SWINGS ile aynı biçim)
## Anahtar: [t, a1, a2, w, k, ext, ease]; açılar savuruş düzleminde (PLANES). Var olan savuruşlar (dual_l, sweep_low,
## down, slam_2h...) bu silahlarda da kullanılır; burada yalnızca yeni biçimler.
const SWINGS := {
	# Gün duruşu: çift ağız gövdenin çevresinde yassı tam tur (iki uç iki yanı biçer, iki geçiş)
	"gun_cark": {"body": "atk_spin_2h", "hit": [0.28, 0.72], "around": true, "multi": [0.4, 0.62], "ss": 2.2, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.2, -1.0, 0.3, 0.0, 1.0, 1.0, 2], [0.28, -1.15, 0.15, 0.0, 1.0, 1.0, 0],
		[0.72, 5.25, 0.0, 0.0, 1.0, 1.15, 0], [1.0, 5.5, 0.9, 0.3, 1.0, 1.0, 0]]},
	# Gün duruşu: önde dik çark (teker): çift ağız ekran düzleminde öne doğru takla atar
	"gun_teker": {"body": "atk_spin", "hit": [0.26, 0.74], "multi": [0.42, 0.62], "ss": 2.0, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.18, 3.0, 0.3, 0.1, 1.0, 1.0, 2], [0.26, 3.3, 0.2, 0.0, 1.0, 1.0, 0],
		[0.5, 6.45, 0.0, 0.0, 1.0, 1.12, 0], [0.74, 9.6, 0.0, 0.0, 1.0, 1.12, 0], [1.0, 9.9, 0.9, 0.3, 1.0, 1.0, 0]]},
	# Gün duruşu bitirişi (Tutulma): baş üstünden iniş, arka ağız aynı hamlede alttan geri yükselir (iki geçiş)
	"gun_tutulma": {"body": "atk_overhead_2h", "hit": [0.36, 0.68], "hold_k": 0.32, "multi": [0.46, 0.6], "ss": 1.6, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.24, 3.2, 0.4, 0.4, 0.9, 1.0, 2], [0.36, 3.5, 0.35, 0.4, 0.85, 1.0, 0],
		[0.46, 1.0, 0.0, 0.0, 1.0, 1.2, 1], [0.53, 0.2, 0.0, -0.2, 1.0, 1.1, 2], [0.6, -0.65, 0.1, -0.4, 1.0, 1.05, 1],
		[0.68, -0.8, 0.2, -0.4, 1.0, 1.0, 2], [1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# Ay duruşu bitirişi: iki hilal kılıç çapraz (X), iki geçiş
	"ay_hilal": {"body": "atk_dual", "hit": [0.26, 0.66], "multi": [0.32, 0.54], "ss": 1.8, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.2, 2.9, 0.5, 0.75, 0.95, 1.0, 2], [0.26, 3.0, 0.55, 0.8, 0.9, 1.0, 0],
		[0.34, 0.9, 0.0, 0.0, 1.0, 1.18, 1], [0.42, 0.15, 0.0, -0.3, 1.0, 1.05, 2], [0.48, -0.35, -0.3, -0.5, 0.9, 1.0, 2],
		[0.56, 1.45, 0.0, 0.15, 1.0, 1.18, 1], [0.66, 2.7, 0.1, 0.35, 1.0, 1.05, 2], [1.0, 0.7, 0.9, 0.4, 1.0, 1.0, 0]]},
	# geçiş (Gün → Ay): birleşik bıçak ikiye ayrılırken öne büyük çapraz yarık
	"ay_ayrilis": {"body": "atk_dual", "hit": [0.24, 0.7], "hold_k": 0.2, "multi": [0.3, 0.56], "ss": 2.0, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.18, 2.9, 0.5, 0.7, 0.95, 1.0, 2], [0.24, 3.05, 0.55, 0.8, 0.9, 1.0, 0],
		[0.32, 0.9, 0.0, 0.0, 1.0, 1.25, 1], [0.4, 0.15, 0.0, -0.3, 1.0, 1.1, 2], [0.48, -0.35, -0.3, -0.5, 0.9, 1.0, 2],
		[0.58, 1.45, 0.0, 0.15, 1.0, 1.25, 1], [0.7, 2.75, 0.1, 0.35, 1.0, 1.08, 2], [1.0, 0.7, 0.9, 0.4, 1.0, 1.0, 0]]},
	# geçiş (Ay → Gün): iki kılıç kabzadan birleşir, baş üstünde iki tam tur
	"gun_birlesme": {"body": "atk_spin_2h", "hit": [0.26, 0.78], "hold_k": 0.22, "around": true, "multi": [0.42, 0.64], "ss": 2.6, "ws": 1.2, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.2, 2.9, 0.2, 0.1, 1.0, 1.0, 2], [0.26, 3.0, 0.1, 0.0, 0.9, 1.0, 0],
		[0.52, 6.2, 0.0, 0.0, 1.0, 1.2, 0], [0.78, 9.35, 0.0, 0.0, 1.0, 1.2, 0], [1.0, 9.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# Kistin: top sırtın arkasında ağır ağır dolanır, baş üstünden öne iner (top geride kalır: geniş hazırlık)
	"kistin_tepe": {"body": "atk_heavy", "hit": [0.34, 0.62], "hold_k": 0.31, "ck": 0.46, "ws": 1.1, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.18, 2.4, 0.4, 0.6, 1.0, 1.0, 2], [0.34, 3.9, 0.3, 0.6, 0.9, 1.0, 0],
		[0.46, 0.95, 0.0, -0.1, 1.0, 1.25, 1], [0.54, 0.35, 0.0, -0.35, 1.0, 1.12, 2], [0.62, 0.45, 0.1, -0.25, 1.0, 1.08, 0],
		[1.0, 0.6, 0.6, 0.2, 1.0, 1.0, 0]]},
	# Kistin: yassı, çok geniş yatay savruk (zincir boyunca top gövdenin önünden ve arkasından geçer)
	"kistin_yan": {"body": "atk_horiz", "hit": [0.3, 0.6], "ck": 0.45, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, -1.9, -0.1, -0.35, 1.0, 1.1, 2], [0.3, -2.05, -0.15, -0.4, 1.0, 1.1, 0],
		[0.45, 1.7, 0.0, 0.1, 1.0, 1.32, 1], [0.53, 2.45, 0.1, 0.25, 1.0, 1.12, 2], [0.6, 2.35, 0.2, 0.25, 1.0, 1.06, 0],
		[1.0, 0.7, 0.9, 0.4, 1.0, 1.0, 0]]},
	# Kistin: Dolama — zincir kırbaç gibi uzanır, top düşmanın çevresine dolanır
	"kistin_dolama": {"body": "atk_whip", "hit": [0.3, 0.56], "ck": 0.41, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, 3.1, 0.6, 0.9, 1.0, 1.0, 2], [0.3, 3.2, 0.65, 1.0, 1.0, 1.0, 0],
		[0.41, 1.6, 0.0, -0.35, 1.0, 1.5, 1], [0.48, 1.45, 0.0, -0.7, 1.0, 1.35, 2], [0.56, 1.35, 0.1, -0.9, 1.0, 1.25, 0],
		[1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# Kistin: Yere Çalma — bağlı düşmanı önden baş üstüne kaldır, arkaya çal (süpürme uzun: atış yayı görünsün)
	"kistin_cal": {"body": "atk_overhead_2h", "hit": [0.3, 0.7], "hold_k": 0.28, "ck": 0.6, "ms": 5.0, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.2, 1.35, 0.3, 0.1, 1.0, 1.0, 2], [0.3, 1.25, 0.35, 0.1, 1.0, 1.0, 0],
		[0.46, 3.1, 0.1, 0.0, 0.9, 1.1, 1], [0.6, 4.65, 0.0, -0.1, 1.0, 1.15, 1], [0.66, 4.8, 0.1, -0.15, 1.0, 1.05, 2],
		[0.7, 4.75, 0.2, -0.1, 1.0, 1.0, 0], [1.0, 6.88, 0.9, 0.3, 1.0, 1.0, 0]]},
	# Albastı: çabuk çift saplama (bitiriş)
	"albasti_oyma": {"body": "atk_thrust", "hit": [0.18, 0.62], "multi": [0.3, 0.5], "ss": 2.0, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.12, -0.3, 1.9, 0.0, 1.0, 1.0, 2], [0.18, -0.4, 2.0, 0.0, 1.0, 1.0, 0],
		[0.3, 1.55, 0.0, 0.0, 1.0, 1.28, 1], [0.4, -0.2, 1.8, 0.1, 1.0, 1.0, 2], [0.5, 1.5, 0.0, -0.05, 1.0, 1.28, 1],
		[0.62, 1.45, 0.05, 0.0, 1.0, 1.2, 2], [1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# Albastı Göçü: belirince ters el saplama (yukarıdan aşağı, sırta)
	"albasti_goc": {"body": "atk_dual", "hit": [0.3, 0.6], "hold_k": 0.27, "ck": 0.42, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, 2.6, 1.2, 3.0, 1.0, 1.0, 2], [0.3, 2.75, 1.25, 3.05, 1.0, 1.0, 0],
		[0.42, 1.2, -0.2, 2.9, 1.0, 1.2, 1], [0.5, 0.8, -0.3, 2.8, 1.0, 1.08, 2], [0.6, 0.85, -0.2, 2.7, 1.0, 1.0, 0],
		[1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# Çevgen vuruşu: arkada-alçakta kurulur, yere yakın geçip önde yükseklere savrulur (top vuruşu)
	"cevgen_vurus": {"body": "atk_uppercut", "hit": [0.34, 0.62], "hold_k": 0.25, "ck": 0.47, "ws": 1.15, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.24, -1.3, 0.2, -0.3, 0.9, 1.0, 2], [0.34, -1.45, 0.25, -0.38, 0.85, 1.0, 0],
		[0.47, 1.2, 0.0, 0.1, 1.0, 1.28, 1], [0.55, 2.65, 0.0, 0.6, 1.0, 1.12, 2], [0.62, 3.0, 0.1, 0.8, 1.0, 1.05, 0],
		[1.0, 1.0, 0.9, 0.4, 1.0, 1.0, 0]]},
}

const PLANES := {
	"gun_cark": {"p": [[0.0, 94.0, 0.26, 0.0], [0.72, 90.0, 0.3, 0.0]], "b": true},
	"gun_teker": {"p": [[0.0, 18.0, 0.86, 0.0], [0.5, 14.0, 0.9, 20.0], [0.74, 20.0, 0.86, 0.0]], "b": true},
	"gun_tutulma": {"p": [[0.0, 32.0, 0.6, 0.0], [0.46, 30.0, 0.62, 0.0], [0.6, 150.0, 0.5, -25.0], [0.68, 152.0, 0.5, -30.0]]},
	"ay_hilal": {"p": [[0.0, 54.0, 0.48, 0.0], [0.44, 54.0, 0.48, 15.0], [0.5, 126.0, 0.48, 0.0], [0.66, 130.0, 0.52, -25.0]]},
	"ay_ayrilis": {"p": [[0.0, 58.0, 0.42, 0.0], [0.42, 58.0, 0.42, 15.0], [0.5, 122.0, 0.42, 0.0], [0.7, 128.0, 0.46, -25.0]]},
	"gun_birlesme": {"p": [[0.0, 90.0, 0.28, 0.0]], "b": true, "zf": 180.0},
	"kistin_tepe": {"p": [[0.0, 40.0, 0.66, 0.0], [0.34, 30.0, 0.6, 0.0], [0.46, 26.0, 0.62, 0.0], [0.62, 22.0, 0.66, 25.0]]},
	"kistin_yan": {"p": [[0.0, 92.0, 0.22, 0.0], [0.45, 90.0, 0.22, 0.0], [0.6, 98.0, 0.28, 30.0]]},
	"kistin_dolama": {"p": [[0.0, 52.0, 0.56, 0.0], [0.41, 54.0, 0.56, 0.0], [0.56, 44.0, 0.6, 30.0]]},
	"kistin_cal": {"p": [[0.0, 90.0, 0.92, 0.0], [0.46, 90.0, 0.95, 0.0], [0.7, 90.0, 0.92, 0.0]]},
	"albasti_oyma": {"p": [[0.0, 90.0, 0.4, 0.0]]},
	"albasti_goc": {"p": [[0.0, 60.0, 0.5, 25.0], [0.42, 62.0, 0.5, 0.0], [0.6, 66.0, 0.52, -30.0]]},
	"cevgen_vurus": {"p": [[0.0, 116.0, 0.42, 0.0], [0.47, 112.0, 0.4, 0.0], [0.62, 124.0, 0.46, -30.0]]},
}

## Vuruş kutuları [x0, y0, x1 (R'ye eklenir), y1]; "-R" önekli x0: -(R + değer)
const BOX := {
	"gun_cark": [-1.0, -58.0, 12.0, 2.0, 12.0], "gun_teker": [0.0, -66.0, 12.0, 2.0, -6.0], "gun_tutulma": [0.0, -64.0, 14.0, 2.0, -12.0],
	"ay_hilal": [0.0, -46.0, 14.0, -10.0, -2.0], "ay_ayrilis": [0.0, -52.0, 22.0, -6.0, -4.0], "gun_birlesme": [-1.0, -62.0, 12.0, 0.0, 12.0],
	"kistin_tepe": [0.0, -60.0, 12.0, 2.0, -6.0], "kistin_yan": [0.0, -54.0, 16.0, -2.0, -14.0], "kistin_dolama": [0.0, -52.0, 30.0, -14.0, 6.0],
	"kistin_cal": [-1.0, -60.0, 10.0, 4.0, 22.0], "albasti_oyma": [0.0, -42.0, 16.0, -18.0, 4.0], "albasti_goc": [0.0, -48.0, 14.0, -6.0, -10.0],
	"cevgen_vurus": [0.0, -60.0, 14.0, 2.0, -4.0],
}

## ------------------------------------------------------------------ kombolar ve ağır saldırılar
const COMBOS := {
	# Gün duruşu (birleşik çift ağız): yassı çark → önde dik teker → Tutulma (iniş + arka ağız yükselişi)
	"gun_ay_ikizi": {"chain": [{"s": "gun_cark", "mult": 0.8, "kb": 120.0}, {"s": "gun_teker", "mult": 0.8, "kb": 130.0},
		{"s": "gun_tutulma", "mult": 1.0, "kb": 210.0, "slam": true, "last": true}],
		"pause": {"s": "gun_cark", "mult": 1.0, "kb": 140.0, "name": "Gün Çarkı"}},
	# Ay duruşu (ikiz hilal kılıç): sol → sağ → çapraz hilaller
	"gun_ay_ikizi@ay": {"chain": [{"s": "dual_l", "mult": 1.0, "kb": 40.0}, {"s": "dual_r", "mult": 1.0, "kb": 40.0},
		{"s": "ay_hilal", "mult": 0.9, "kb": 110.0, "last": true}],
		"pause": {"s": "ay_hilal", "mult": 1.0, "kb": 110.0, "name": "Ay Hilali"}},
	# Kistin: baş üstü ezme → yassı savruk → Dolama (bağlar) → Yere Çalma (yalnızca bağlı düşman varken)
	"kistin": {"chain": [{"s": "kistin_tepe", "mult": 1.0, "kb": 220.0}, {"s": "kistin_yan", "mult": 1.05, "kb": 200.0},
		{"s": "kistin_dolama", "mult": 0.8, "kb": 0.0, "dolama": true},
		{"s": "kistin_cal", "mult": 1.9, "kb": 160.0, "cal": true, "needs_bind": true, "stun": 0.6, "last": true, "fc": true}],
		"pause": {"s": "kistin_yan", "mult": 1.2, "kb": 220.0, "name": "Kistin Savruğu"}},
	# Albastı Hançeri: sol → ters el → sağ → çift saplama
	"albasti_hanceri": {"chain": [{"s": "dual_l", "mult": 1.0, "kb": 35.0}, {"s": "reverse_grip", "mult": 1.0, "kb": 35.0},
		{"s": "dual_r", "mult": 1.0, "kb": 35.0}, {"s": "albasti_oyma", "mult": 0.85, "kb": 70.0, "last": true}],
		"pause": {"s": "albasti_oyma", "mult": 0.9, "kb": 60.0, "name": "Al Dişleri"}},
	# Çevgen: yerde sürme → kısa çakma → çevgen vuruşu (top gibi fırlatır)
	"cevgen": {"chain": [{"s": "sweep_low", "mult": 1.0, "kb": 140.0}, {"s": "down", "mult": 1.0, "kb": 180.0},
		{"s": "cevgen_vurus", "mult": 1.35, "kb": 260.0, "top": 1.0, "last": true}],
		"pause": {"s": "cevgen_vurus", "mult": 1.4, "kb": 260.0, "top": 1.0, "name": "Çevgen"}},
}

const HEAVIES := {
	"gun_ay_ikizi": {"s": "ay_ayrilis", "mult": 1.5, "kb": 160.0, "durus": "ay", "name": "Ay Ayrılışı"},
	"gun_ay_ikizi@ay": {"s": "gun_birlesme", "mult": 1.5, "kb": 180.0, "durus": "gun", "name": "Gün Birleşmesi"},
	"kistin": {"s": "slam_2h", "mult": 1.9, "kb": 340.0, "shock": true, "slam": true, "stun": 1.2, "name": "Kıyamet Savruğu"},
	"albasti_hanceri": {"s": "albasti_goc", "mult": 1.5, "kb": 120.0, "goc": true, "name": "Albastı Göçü"},
	"cevgen": {"s": "cevgen_vurus", "mult": 1.9, "kb": 320.0, "top": 1.4, "name": "Tam Vuruş"},
}

## Denge sabitleri (süreler sn, mesafeler px)
const GUNAY := {"bonus": 0.25, "krit_t": 1.2}
const KISTIN := {"cal_h": 74.0, "cal_back": 46.0, "cal_r": 46.0, "cal_k": 1.0, "agir_k": 1.0}
const ALBASTI := {"max": 3, "sure": 6.0, "iz_k": 0.35, "dikey": 70.0}
const CEVGEN := {"omur": 0.9, "carp_k": 0.6, "top_k": 0.4, "duvar_k": 0.5, "nesil": 2, "agir_k": 1.3, "yavas": 120.0}
const TATAR := {"hiz": 900.0, "kilit": 0.05, "acik": 0.2, "tatli": [0.62, 0.78], "takilma": 0.5, "kut_k": 1.0}
const KUZGU := {"menzil": 260.0, "tik": 0.1, "taban": 0.5, "rampa": 1.5, "isinma": 38.0, "soguma": 55.0, "sogut": 1.4,
	"patlama_k": 6.0, "patlama_r": 70.0, "yuru": 0.45}
const BAG := {"hiz": 520.0, "omur": 0.55, "sure": 5.0, "menzil": 170.0, "pay": 0.4, "cekis_k": 1.3, "ortalama": 1.15}

## ------------------------------------------------------------------ durum (statik: tek oyuncu)
static var gunay := "gun"        # Gün-Ay İkizi duruşu: "gun" (birleşik) / "ay" (ikiz)
static var stats := {}           # test sayaçları (silah27_testi): olay adı -> sayı


static func stat(k: String, n := 1) -> void:
	stats[k] = int(stats.get(k, 0)) + n


static func node_of(p: Node) -> Silah27:
	if p == null:
		return null
	return p.get_node_or_null("Silah27") as Silah27


## ------------------------------------------------------------------ tablolar (Player / ItemGen kancaları)
static func swing(n: String) -> Dictionary:
	return SWINGS.get(n, {})


static func plane(n: String) -> Dictionary:
	return PLANES.get(n, {})


static func has_combo(it: Dictionary) -> bool:
	return COMBOS.has(String(it.get("id", "")))


static func combo(it: Dictionary) -> Dictionary:
	var id := String(it.get("id", ""))
	if id == "gun_ay_ikizi" and gunay == "ay":
		return COMBOS["gun_ay_ikizi@ay"]
	return COMBOS[id]


static func heavy(it: Dictionary) -> Dictionary:
	var id := String(it.get("id", ""))
	if id == "gun_ay_ikizi" and gunay == "ay":
		return HEAVIES["gun_ay_ikizi@ay"]
	return HEAVIES.get(id, {})


static func box(sw: String, R: float) -> Array:
	if not BOX.has(sw):
		return [0.0, -48.0, R + 8.0, 0.0]
	var b: Array = BOX[sw]
	var x0 := float(b[4])
	if float(b[0]) < 0.0:
		x0 = -(R + float(b[4]))
	return [x0, float(b[1]), R + float(b[2]), float(b[3])]


static func tempo_class(it: Dictionary) -> String:
	## Gün duruşu uzun sap gibi (geniş çarklar), Ay duruşu düellocu gibi (hızlı kesikler)
	if String(it.get("id", "")) == "gun_ay_ikizi":
		return "uzun" if gunay == "gun" else "duello"
	return ""


static func weight(it: Dictionary) -> float:
	match String(it.get("id", "")):
		"gun_ay_ikizi":
			return 0.5 if gunay == "gun" else 0.25
		"kistin", "cevgen":
			return 0.8
		"albasti_hanceri":
			return 0.15
	return -1.0


static func sprite_id(it: Dictionary) -> String:
	var id := String(it.get("id", ""))
	if id == "gun_ay_ikizi" and gunay == "ay":
		return "gun_ay_ikizi_ay"
	return id


static func reach(it: Dictionary) -> float:
	if String(it.get("id", "")) == "gun_ay_ikizi" and gunay == "ay":
		return 23.0
	return -1.0


static func owns_sec(it: Dictionary) -> bool:
	return String(it.get("id", "")) in SEC_IDS


## ------------------------------------------------------------------ kart (ItemGen.dps / aps_eff)
static func _atis_k(it: Dictionary) -> float:
	var pct := Player.hiz_kalici(it)
	return 1.0 + Player.hiz_oran(it, pct) * float(Player.HIZ["atis"])


static func tatar_reload(it: Dictionary) -> float:
	## Kurma süresi: 1 / aps, saldırı hızıyla kısalır (Player._sec_cd ile aynı)
	return 1.0 / maxf(0.05, float(it.get("aps", 0.8))) / _atis_k(it)


static func card_aps(it: Dictionary) -> float:
	match String(it.get("id", "")):
		"tatar_yayi":
			return 1.0 / (tatar_reload(it) + float(TATAR["kilit"]) + 1.0 / 60.0)
		"kam_kuzgusu":
			return 1.0 / float(KUZGU["tik"])
		"tengri_bagi":
			return float(it.get("aps", 1.25)) * _atis_k(it)
	return -1.0


static func kuzgu_cycle(mv: float, cm := 1.0) -> Array:
	## Sürekli basılı tutuşun bir ısınma turu: [taban hasar çarpanı toplamı, süre]. Tik başına çarpan
	## taban × (1 → mv rampa süresinde), tam ısınınca Gün Patlaması (patlama_k; tam kızmış ışında kritik: cm) ve soğuma.
	var tc := 100.0 / float(KUZGU["isinma"])
	var ramp := float(KUZGU["rampa"])
	var dt := float(KUZGU["tik"])
	var s := 0.0
	var t := 0.0
	while t < tc - 0.0001:
		var r := 1.0 + (mv - 1.0) * clampf(t / ramp, 0.0, 1.0)
		s += float(KUZGU["taban"]) * r
		t += dt
	s += float(KUZGU["patlama_k"]) * cm   # sürekli tutuşta patlama hep tam kızmış ışına (kritik)
	return [s, tc + float(KUZGU["sogut"])]


static func card_rate(it: Dictionary) -> float:
	## Taban hasar × bu = saniyedeki hasar (kritik ve tomar ItemGen'de)
	match String(it.get("id", "")):
		"tatar_yayi":
			return card_aps(it)
		"kam_kuzgusu":
			var c := kuzgu_cycle(float(it.get("mech_v", 2.9)), float(it.get("crit_mult", 1.6)))
			return float(c[0]) / float(c[1])
		"tengri_bagi":
			return card_aps(it) * float(BAG["ortalama"])
	return -1.0


## ------------------------------------------------------------------ düğüm (oyuncunun çocuğu)
var pl: Player
# Gün-Ay
var gecis_n := 0
var gecis_t := -9.0
var _back_trail: Node2D = null
# Kistin
var bound: Node = null
var bound_t := 0.0
var _throw: Dictionary = {}
# Çevgen
var balls: Array = []
# Tatar Yayı
var t_attempt := false
var t_kut := false
var t_shot := 0.0
var t_flash := 0.0
var t_flash_col := Color(1, 1, 1)
var t_tilt := 0.0
# Kam Küzgüsü
var k_on := false
var k_heat := 0.0
var k_cool := 0.0
var k_target: Node = null
var k_ramp := 0.0
var k_acc := 0.0
var k_end := Vector2.ZERO
var k_from := Vector2.ZERO
var k_tilt := 0.0
# Tengri Bağı
var links: Array = []   # [{"m": [Enemy...], "t": kalan}]
var _t := 0.0


static func attach(p: Player) -> void:
	var n := Silah27.new()
	n.name = "Silah27"
	n.pl = p
	p.add_child(n)


func _ready() -> void:
	top_level = true
	global_position = Vector2.ZERO
	z_index = 40
	process_physics_priority = 10   # oyuncu ve düşmanlardan sonra (fırlatılan düşmanın konumu son sözü söyler)


func reset() -> void:
	## Yuva değişti: kanal / bağ / bağlama bırakılır
	_kuzgu_stop()
	t_attempt = false
	t_shot = 0.0
	bound = null
	bound_t = 0.0


func _melee_id() -> String:
	return String(pl.slot(pl.mel_slot).get("id", "")) if pl else ""


## ------------------------------------------------------------------ yakın dövüş kancaları
static func step_override(p: Player, _it: Dictionary, chain: Array, step: int, c: Dictionary) -> Array:
	## Kistin: Yere Çalma yalnızca Dolama birini bağladıysa; değilse zincir baştan
	if not c.get("needs_bind", false):
		return [step, c]
	var n := node_of(p)
	if n and n.bound != null and is_instance_valid(n.bound) and not n.bound.dead and n.bound_t > 0.0:
		return [step, c]
	return [0, chain[0]]


static func pre_strike(p: Player) -> void:
	## Vuruş başı (Player._on_strike_start'ın en başında): duruş değişimi, Albastı Göçü, Yere Çalma atışı
	var n := node_of(p)
	if n == null or p.atk.is_empty():
		return
	var c: Dictionary = p.atk["c"]
	var it: Dictionary = p.atk["item"]
	if c.has("durus"):
		n._switch_stance(String(c["durus"]), it)
	if c.get("goc", false):
		n._goc(it)
	if c.get("cal", false):
		n._cal_begin(it)


static func on_hit(p: Player, e: Node, it: Dictionary, c: Dictionary, _opts: Dictionary) -> void:
	## Yakın vuruş isabetinden sonra (Player._melee_hits)
	var n := node_of(p)
	if n == null:
		return
	match String(it.get("mech_id", "")):
		"albasti":
			if is_instance_valid(e) and not e.dead and not c.get("goc", false):
				var k := mini(int(ALBASTI["max"]), int(e.get_meta("v27_iz", 0)) + 1)
				e.set_meta("v27_iz", k)
				e.set_meta("v27_iz_t", Game.clock())
				if k == int(ALBASTI["max"]):
					stat("iz_dolu")
		"dolama":
			if c.get("dolama", false) and is_instance_valid(e) and not e.dead and (n.bound == null or not is_instance_valid(n.bound) or n.bound.dead):
				n.bound = e
				n.bound_t = float(it.get("mech_v", 1.1))
				if not e.is_boss:
					e.root_t = maxf(e.root_t, n.bound_t)
				stat("dolama")
				Ses.play("darbe_kirbac", -4.0, 0.8)
				InkFX.ring(e.center(), 12.0, 0, 0.22)
				FX.anim("tether_catch", e.center(), 0.0, 0.8, Color(1.0, 0.85, 0.6))
		"top_gibi":
			var tk := float(c.get("top", 0.0))
			if tk > 0.0 and is_instance_valid(e) and not e.dead:
				n._ball(e, float(it.get("mech_v", 500.0)) * tk * float(p.facing), 0, it)


static func deal(p: Player, e: Node, it: Dictionary, opts: Dictionary, d: float) -> Array:
	## Player._deal içindeki mekanik eşleşmesi: [hasar, kritik, beceri kritiği (bekleme tanımaz)]
	var n := node_of(p)
	var crit := false
	var serbest := false
	var c: Dictionary = p.atk.get("c", {}) if not p.atk.is_empty() else {}
	match String(it.get("mech_id", "")):
		"durus":
			if n and n.gecis_n > 0 and not p.atk.is_empty() and not p.atk.get("heavy", false):
				d *= 1.0 + float(GUNAY["bonus"])
				n.gecis_n -= 1
			if n and Game.clock() - n.gecis_t < float(GUNAY["krit_t"]) and not p.atk.get("heavy", false):
				crit = true
		"dolama":
			if opts.get("v27_alti", false):
				crit = true
				serbest = true
			if c.get("cal", false) and (e.heavy or e.is_boss):
				d *= float(KISTIN["agir_k"])
		"albasti":
			if c.get("goc", false) and n and p.atk.get("v27_goc") == e:
				var k := int(e.get_meta("v27_iz", 0))
				d *= 1.0 + float(ALBASTI["iz_k"]) * k
				if k >= int(ALBASTI["max"]):
					crit = true
					serbest = true
					opts["force_crit"] = true
					opts["krit_neden"] = "albasti"
					stat("goc_kritik")
				e.set_meta("v27_iz", 0)
		"top_gibi":
			if opts.get("v27_carpma", false):
				crit = true
				serbest = true
			if float(c.get("top", 0.0)) > 0.0 and (e.heavy or e.is_boss):
				d *= float(CEVGEN["agir_k"])
		"kurma":
			if opts.get("v27_kut", false):
				crit = true
				serbest = true
				opts["force_crit"] = true
				opts["krit_neden"] = "kusursuz_kurma"
		"kizginlik":
			if opts.get("v27_tam", false):
				crit = true
				serbest = true
		"bag":
			if opts.get("v27_carp", false):
				crit = true
				serbest = true
	return [d, crit, serbest]


static func after_deal(p: Player, e: Node, _it: Dictionary, opts: Dictionary, d: float, _killed: bool) -> void:
	## Tengri Bağı: bağlı düşmana verilen hasarın bir kısmı bağdaki ötekilere geçer (yinelemesiz)
	if opts.get("v27_pay", false):
		return
	var n := node_of(p)
	if n == null or n.links.is_empty():
		return
	for L in n.links:
		var m: Array = L["m"]
		if not m.has(e):
			continue
		for o in m:
			if o == e or not is_instance_valid(o) or o.dead:
				continue
			var share := d * float(BAG["pay"])
			o.take_hit(share, {"kb": 20.0, "dir": signf(o.center().x - e.center().x), "sfx_done": true, "feel_done": true, "v27_pay": true})
			stat("bag_pay")
			if FX.root:
				FX.lightning(e.center(), o.center(), Color(0.62, 0.72, 1.0))
		return


## ------------------------------------------------------------------ Gün-Ay İkizi
func _switch_stance(to: String, it: Dictionary) -> void:
	gunay = to
	gecis_n = int(it.get("mech_v", 2))
	gecis_t = Game.clock()
	stat("durus_" + to)
	var gun := to == "gun"
	var col := Color(1.0, 0.82, 0.35) if gun else Color(0.78, 0.86, 1.0)
	var hand := pl.arm_root.to_global(pl._hand_local)
	InkFX.ring(hand, 18.0, 9 if gun else 7, 0.3)
	InkFX.ring(pl.center(), 30.0, 9 if gun else 7, 0.36, 0.55)
	FX.flash_light(hand, col, 130.0, 1.6, 0.22)
	FX.text(pl.center() + Vector2(0, -46), "GÜN DURUŞU" if gun else "AY DURUŞU", col, 9)
	Ses.play("kut_donusum", -6.0, 1.25 if gun else 1.5)
	Ses.play("savur_katana", -6.0, 0.8)
	pl.anim.set_flash(0.45)
	get_tree().create_timer(0.06).timeout.connect(func() -> void:
		if is_instance_valid(pl):
			pl.anim.set_flash(0.0))


func _back_blade_tick() -> void:
	## Gün duruşunda çift ağzın arka ucu da iz bırakır (ikinci mürekkep hilali)
	var on: bool = not pl.atk.is_empty() and pl.atk.get("phase", "") == "act" and String(pl.atk["item"].get("id", "")) == "gun_ay_ikizi" \
		and gunay == "gun" and pl.arm_root.visible
	if not on:
		if _back_trail and is_instance_valid(_back_trail):
			_back_trail.set("done", true)
		_back_trail = null
		return
	var it: Dictionary = pl.atk["item"]
	if _back_trail == null or not is_instance_valid(_back_trail):
		_back_trail = FX.trail(Color(0.78, 0.86, 1.0), 0.9)
		if _back_trail == null:
			return
		_back_trail.set("life", 0.1)
		if _back_trail is InkTrail:
			(_back_trail as InkTrail).setup(it, pl.atk, 0.5)
			(_back_trail as InkTrail).pal = 2 if Unsur.of(it) == "" else (_back_trail as InkTrail).pal
			(_back_trail as InkTrail)._apply_mat()
	var R := pl._reach(it)
	var h := pl._hand_local
	var bd := -pl._blade_local
	_back_trail.call("add", pl.arm_root.to_global(h + bd * R * 0.35), pl.arm_root.to_global(h + bd * R))


## ------------------------------------------------------------------ Kistin
func _cal_begin(it: Dictionary) -> void:
	## Yere Çalma: bağlı hafif düşman önden baş üstüne kalkar, arkaya çalınır (iniş temas anında: ck)
	if bound == null or not is_instance_valid(bound) or bound.dead:
		return
	var e: Node = bound
	bound = null
	bound_t = 0.0
	if e.heavy or e.is_boss or e.flying:
		stat("cal_agir")
		FX.text(e.center() + Vector2(0, -30), "SARSILDI", Color(1.0, 0.85, 0.6), 8)
		return
	var dur := maxf(0.08, float(pl.atk["ph"][1]))
	var back := -float(pl.facing)
	var to := Vector2(pl.global_position.x + back * float(KISTIN["cal_back"]), pl.global_position.y)
	if pl.level and pl.level.solid_at(to + Vector2(0, -10)):
		to.x = pl.global_position.x - back * 30.0   # arkada duvar: öne çal
	var gy := -1.0
	if pl.level and pl.level.has_method("ground_y_below"):
		gy = float(pl.level.ground_y_below(Vector2(to.x, pl.global_position.y - 20.0), 80.0))
	if gy >= 0.0:
		to.y = gy
	_throw = {"e": e, "t": 0.0, "dur": dur, "a": e.global_position, "b": to, "it": it}
	e.stun(0.9)
	stat("cal")
	Ses.play("savur_dev", -4.0, 0.85)


func _throw_tick(delta: float) -> void:
	if _throw.is_empty():
		return
	var e: Node = _throw["e"]
	if not is_instance_valid(e) or e.dead:
		_throw = {}
		return
	_throw["t"] = float(_throw["t"]) + delta
	var k := clampf(float(_throw["t"]) / float(_throw["dur"]), 0.0, 1.0)
	var a: Vector2 = _throw["a"]
	var b: Vector2 = _throw["b"]
	var top := minf(a.y, b.y) - float(KISTIN["cal_h"])
	var x := lerpf(a.x, b.x, k)
	var y := (1.0 - k) * (1.0 - k) * a.y + 2.0 * (1.0 - k) * k * top + k * k * b.y
	e.global_position = Vector2(x, y)
	e.velocity = Vector2.ZERO
	e.stun_t = maxf(e.stun_t, 0.2)
	e.set("_tumble", -PI * 1.6 * k * float(pl.facing))
	if Engine.get_physics_frames() % 2 == 0:
		FX.ghost(e.anim.base, Color(1.0, 0.8, 0.6, 0.35), 0.18)
	if k >= 1.0:
		_cal_land(e, _throw["it"])
		_throw = {}


func _cal_land(e: Node, it: Dictionary) -> void:
	var p: Vector2 = e.global_position
	e.set("_tumble", 0.0)
	e.velocity = Vector2(0, 0)
	e.vis_scale = Vector2(1.45, 0.6)
	FX.ground_slam(p, -pl.facing, 1.3, Color(1.0, 0.8, 0.55), true, false, true)
	InkDust.burst(p, -pl.facing, 1.2)
	Game.shake(4.0)
	Game.kick(Vector2.DOWN, 4.0)
	Game.hitstop(0.05)
	Ses.play("sarsinti_buyuk", -3.0)
	for o in get_tree().get_nodes_in_group("dusman"):
		if o == e or not is_instance_valid(o) or o.dead:
			continue
		if absf(o.global_position.x - p.x) < float(KISTIN["cal_r"]) and absf(o.global_position.y - p.y) < 40.0:
			pl._deal(o, float(it["dmg"]) * float(KISTIN["cal_k"]), it, {"kb": 180.0, "dir": signf(o.global_position.x - p.x), "stun": 0.8, "launch": 200.0, "v27_alti": true})
			stat("cal_alti")


## ------------------------------------------------------------------ Albastı Hançeri
func _goc(it: Dictionary) -> void:
	## Albastı Göçü: öndeki (bakılan yönde) en yakın izli düşmanın arkasında belir; yoksa ileri delip geçme
	var best: Node = null
	var bd := float(it.get("mech_v", 220.0))
	for e in get_tree().get_nodes_in_group("dusman"):
		if not is_instance_valid(e) or e.dead or int(e.get_meta("v27_iz", 0)) <= 0:
			continue
		var dx: float = (e.global_position.x - pl.global_position.x) * float(pl.facing)
		if dx < -4.0 or absf(e.center().y - pl.center().y) > float(ALBASTI["dikey"]):
			continue
		if absf(dx) < bd:
			bd = absf(dx)
			best = e
	if best == null:
		pl.atk["through"] = true
		pl.velocity.x = float(pl.facing) * 780.0
		pl.inv_t = maxf(pl.inv_t, 0.3)
		stat("goc_bos")
		return
	var side := float(pl.facing)   # düşmanın arkası: oyuncunun geldiği yönün öbür yanı
	var to := Vector2(best.global_position.x + side * (best.size.x * 0.5 + 12.0), best.global_position.y)
	if pl.level and (pl.level.solid_at(to + Vector2(0, -12)) or pl.level.solid_at(to + Vector2(0, -32))):
		to.x = best.global_position.x - side * (best.size.x * 0.5 + 12.0)   # arkası duvar: önüne
		side = -side
	var from := pl.global_position
	_smoke(from + Vector2(0, -20), true)
	for i in 3:
		FX.ghost(pl.anim.base, Color(0.9, 0.2, 0.25, 0.5 - 0.12 * i), 0.3)
	pl.global_position = to
	pl.velocity = Vector2.ZERO
	pl.facing = -int(side)
	pl.anim.set_facing(pl.facing)
	pl.inv_t = maxf(pl.inv_t, 0.35)
	pl.atk["v27_goc"] = best
	_smoke(to + Vector2(0, -20), false)
	FX.streak(from + Vector2(0, -20), to + Vector2(0, -20), Color(0.9, 0.2, 0.28, 0.8), 0.16)
	Ses.play("albasti_goc", -2.0, 1.0)
	Ses.play("savur_hafif", -6.0, 0.6)
	Game.slowmo(0.5, 0.08)
	stat("goc")


func _smoke(p: Vector2, out: bool) -> void:
	InkFX.ring(p, 14.0 if out else 18.0, 0, 0.25)
	InkFX.hit("cut", p, Vector2(float(pl.facing), -0.2), 0, 1, 0.9)
	FX.smoke(p, 6, 0.5, Color(0.25, 0.05, 0.08, 0.7))
	FX.anim("void_implosion", p, 0.0, 0.55, Color(0.95, 0.25, 0.3))


## ------------------------------------------------------------------ Çevgen
func _ball(e: Node, vx: float, gen: int, it: Dictionary) -> void:
	if e.heavy or e.is_boss or e.flying or e.dead:
		return
	for b in balls:
		if b["e"] == e:
			b["v"] = Vector2(vx, -90.0)
			b["t"] = 0.0
			return
	balls.append({"e": e, "v": Vector2(vx, -90.0), "gen": gen, "t": 0.0, "hit": [e], "it": it, "rot": 0.0})
	stat("top")
	if gen > 0:
		stat("top_zincir")
	Ses.play("darbe_agir", -5.0, 1.15)


func _balls_tick(delta: float) -> void:
	var keep: Array = []
	for b in balls:
		var e: Node = b["e"]
		if not is_instance_valid(e) or e.dead:
			continue
		b["t"] = float(b["t"]) + delta
		var v: Vector2 = b["v"]
		v.y = minf(v.y + 900.0 * delta, 500.0)
		e.velocity = Vector2.ZERO
		e.stun_t = maxf(e.stun_t, 0.12)
		var col: KinematicCollision2D = e.move_and_collide(v * delta)
		if col:
			var nrm := col.get_normal()
			if absf(nrm.x) > 0.6:
				_ball_wall(e, b, nrm)
				continue
			if nrm.y < -0.5:
				v.y = 0.0
				e.move_and_collide(Vector2(v.x * delta, 0.0))
			v.x *= 0.96
		b["v"] = v
		b["rot"] = float(b["rot"]) + signf(v.x) * delta * 18.0
		e.set("_tumble", float(b["rot"]))
		if Engine.get_physics_frames() % 2 == 0:
			FX.ghost(e.anim.base, Color(1.0, 0.85, 0.5, 0.35), 0.16)
		var it: Dictionary = b["it"]
		for o in get_tree().get_nodes_in_group("dusman"):
			if not is_instance_valid(o) or o.dead or (b["hit"] as Array).has(o):
				continue
			if o.hurt_rect().intersects(e.hurt_rect().grow(4.0)):
				(b["hit"] as Array).append(o)
				var dir := signf(v.x)
				var cp: Vector2 = (o.center() + e.center()) * 0.5
				FX.impact_sprite("blunt", cp, Vector2(dir, -0.2), Color(1.0, 0.9, 0.6), 1.2)
				InkFX.hit("blunt", cp, Vector2(dir, -0.2), 9, 2, 1.0)
				Game.hitstop(0.05)
				Game.shake(3.0)
				Ses.play("darbe_cekic", -3.0, 1.1)
				pl._deal(o, float(it["dmg"]) * float(CEVGEN["carp_k"]), it, {"kb": 160.0, "dir": dir, "stun": 0.5, "v27_carpma": true})
				pl._deal(e, float(it["dmg"]) * float(CEVGEN["top_k"]), it, {"kb": 0.0, "dir": dir, "sfx_done": true})
				stat("top_carpma")
				if int(b["gen"]) < int(CEVGEN["nesil"]) and is_instance_valid(o) and not o.dead:
					_ball(o, v.x * 0.75, int(b["gen"]) + 1, it)
				v.x *= 0.5
				b["v"] = v
		if absf(v.x) < float(CEVGEN["yavas"]) or float(b["t"]) > float(CEVGEN["omur"]):
			e.set("_tumble", 0.0)
			continue
		keep.append(b)
	balls = keep


func _ball_wall(e: Node, b: Dictionary, nrm: Vector2) -> void:
	var it: Dictionary = b["it"]
	var cp: Vector2 = e.center() - nrm * 8.0
	FX.impact_sprite("blunt", cp, nrm, Color(1.0, 0.9, 0.7), 1.3)
	FX.dust(e.global_position, nrm, 6, 0.32)
	Game.hitstop(0.06)
	Game.shake(3.5)
	Ses.play("darbe_kunt", -2.0, 0.9)
	e.set("_tumble", 0.0)
	e.vis_scale = Vector2(0.7, 1.3)
	pl._deal(e, float(it["dmg"]) * float(CEVGEN["duvar_k"]), it, {"kb": 40.0, "dir": nrm.x, "stun": 0.9, "sfx_done": true})
	stat("top_duvar")


## ------------------------------------------------------------------ ikincil (uzak) silahlar
static func sec_tick(p: Player, it: Dictionary, press: bool, delta: float) -> void:
	var n := node_of(p)
	if n == null:
		return
	match String(it.get("id", "")):
		"tatar_yayi":
			n._tatar(it, press)
		"kam_kuzgusu":
			n._kuzgu(it, delta)
		"tengri_bagi":
			n._bag(it, press)


func _sk() -> String:
	return pl.sec_slot


# ---- Tatar Yayı
func _tatar(it: Dictionary, press: bool) -> void:
	var k := _sk()
	if not press:
		return
	pl.sec_buf = 0.0
	if float(pl.cd[k]) <= 0.0:
		_tatar_fire(it)
		return
	# kurulurken basış: tek deneme; ilk açıklıkta (atış basışının uzantısı) yok sayılır
	var R := maxf(0.01, float(pl.cd_max[k]))
	var q := 1.0 - float(pl.cd[k]) / R
	if t_attempt or q < float(TATAR["acik"]):
		return
	t_attempt = true
	var sw: Array = TATAR["tatli"]
	var hand := pl.arm_root.to_global(pl._hand_local) if pl.arm_root.visible else pl.center()
	if q >= float(sw[0]) and q <= float(sw[1]):
		pl.cd[k] = 0.0
		t_kut = true
		t_flash = 1.0
		t_flash_col = Color(1.0, 0.85, 0.4)
		stat("kurma_tam")
		Ses.play("tatar_kurma", -2.0, 1.0)
		Ses.play("yay_dolu", -5.0, 0.9)
		Ses.play("ors", -11.0, 1.4)
		InkFX.ring(pl.center() + Vector2(0, -50), 10.0, 9, 0.25)
		FX.flash_light(hand, Color(1.0, 0.85, 0.4), 90.0, 1.4, 0.15)
		FX.text(pl.center() + Vector2(0, -60), "KUSURSUZ KURMA", Color(1.0, 0.86, 0.45), 8)
	else:
		pl.cd[k] = float(pl.cd[k]) + float(TATAR["takilma"])
		pl.cd_max[k] = float(pl.cd_max[k]) + float(TATAR["takilma"])
		t_flash = 1.0
		t_flash_col = Color(0.9, 0.3, 0.3)
		stat("kurma_takildi")
		Ses.play("ui_iptal", -6.0, 0.8)
		Ses.play("darbe_metal", -10.0, 1.5)
		FX.text(pl.center() + Vector2(0, -60), "takıldı", Color(0.95, 0.5, 0.45), 7)


func _tatar_fire(it: Dictionary) -> void:
	var k := _sk()
	var kut := t_kut
	t_kut = false
	t_attempt = false
	t_shot = 0.3
	var origin := pl.global_position + Vector2(float(pl.facing) * 14.0, -27.0)
	var spd := float(TATAR["hiz"]) * (1.1 if kut else 1.0)
	var a := pl.okc._aim_angle(origin, spd, 0.0) if pl.okc else 0.0
	t_tilt = a
	var pr := Projectile.new()
	pr.team = "p"
	pr.kind = "javelin"
	pr.atlas_item = "tatar_oku"
	pr.atlas_mat = String(it.get("material", "demir"))
	pr.position = origin
	pr.velocity = Vector2(cos(a) * float(pl.facing), sin(a)) * spd
	pr.gravity = 0.0
	pr.stick = true
	pr.life = 0.75
	pr.hit_pad = Vector2(8.0, 6.0)
	pr.pierce = (int(it.get("mech_v", 4)) - 1) if kut else 1
	pr.unsur = Unsur.of(it)
	pr.trail_col = Color(1.0, 0.85, 0.4) if kut else Color(0.9, 0.85, 0.75)
	pr.fx_kind = "altin" if kut else ""
	var dmg := float(it["dmg"]) * (float(TATAR["kut_k"]) if kut else 1.0)
	var dirx := float(pl.facing)
	pr.on_hit = func(e: Node) -> void:
		pl._deal(e, dmg, it, {"kb": 170.0 if kut else 130.0, "dir": dirx, "stun": 0.25, "v27_kut": kut})
		stat("tatar_isabet")
	pl.level.add_projectile(pr)
	pl.cd[k] = tatar_reload(it)
	pl.cd_max[k] = pl.cd[k]
	stat("tatar_atis")
	if kut:
		stat("tatar_kut_ok")
	Ses.play("tatar_atis", -1.0, 0.92 if kut else 1.0, 0.05)
	if kut:
		Ses.play("yay_birak_tam", -6.0, 0.7, 0.04)
	Ses.play("darbe_metal", -12.0, 0.6)
	Game.kick(Vector2(-float(pl.facing), 0), 4.0 if kut else 2.5)
	pl.velocity.x -= float(pl.facing) * (70.0 if kut else 45.0)
	pl.vis_scale = Vector2(1.1, 0.92)
	var mz := origin + Vector2(float(pl.facing) * 12.0, 0)
	InkFX.hit("pierce", mz, Vector2(float(pl.facing), 0), 9 if kut else 0, 1, 0.8)
	FX.flash_light(mz, Color(1.0, 0.85, 0.5), 70.0, 1.2, 0.1)


# ---- Kam Küzgüsü
func _kuzgu(it: Dictionary, delta: float) -> void:
	var k := _sk()
	var held := pl.sec_act != "" and Input.is_action_pressed(pl.sec_act) and pl.atk.is_empty() and pl.roll_t <= 0.0
	if k_cool > 0.0:
		held = false
	if held and not k_on:
		k_on = true
		k_target = null
		k_ramp = 0.0
		k_acc = float(KUZGU["tik"])   # ilk tik hemen
		Ses.loop_start("kuzgu", "kuzgu_isin_dongu" if Ses.has("kuzgu_isin_dongu") else "simsek_sizirti_dongu", -10.0, 1.0)
		stat("kuzgu_ac")
	elif not held and k_on:
		_kuzgu_stop()
	if not k_on:
		return
	pl.sec_buf = 0.0
	k_heat += float(KUZGU["isinma"]) * delta
	var hand := pl.arm_root.to_global(pl._hand_local) if pl.arm_root.visible else pl.center()
	var mirror := hand + Vector2(float(pl.facing) * 10.0, -1.0)
	k_from = mirror
	k_tilt = pl.okc._aim_angle(mirror, 2000.0, 0.0) if pl.okc else 0.0
	var dir := Vector2(cos(k_tilt) * float(pl.facing), sin(k_tilt))
	# ışın: ilk değen düşman ya da duvar
	var L := float(KUZGU["menzil"])
	var hitn: Node = null
	var best := L
	for e in get_tree().get_nodes_in_group("dusman"):
		if not is_instance_valid(e) or e.dead:
			continue
		var r: Rect2 = e.hurt_rect().grow(3.0)
		var to: Vector2 = r.get_center() - mirror
		var along := to.dot(dir)
		if along < -4.0 or along > best:
			continue
		var perp := absf(to.x * dir.y - to.y * dir.x)
		if perp <= r.size.y * 0.5 + 4.0:
			best = maxf(0.0, along - r.size.x * 0.5)
			hitn = e
	if pl.level:
		var s := 8.0
		while s < best:
			if pl.level.solid_at(mirror + dir * s):
				best = s
				hitn = null
				break
			s += 8.0
	k_end = mirror + dir * best
	if hitn != k_target:
		k_target = hitn
		k_ramp = 0.0
	if hitn:
		k_ramp += delta
	var mv := float(it.get("mech_v", 2.9))
	var rk := 1.0 + (mv - 1.0) * clampf(k_ramp / float(KUZGU["rampa"]), 0.0, 1.0)
	k_acc += delta
	while k_acc >= float(KUZGU["tik"]) - 0.0001:
		k_acc -= float(KUZGU["tik"])
		if hitn and is_instance_valid(hitn) and not hitn.dead:
			FX.hit_k = 0.35
			pl._deal(hitn, float(it["dmg"]) * float(KUZGU["taban"]) * rk, it, {"kb": 6.0, "dir": float(pl.facing), "sfx_done": true, "feel_done": true})
			FX.hit_k = 1.0
			stat("kuzgu_tik")
	Ses.loop_pitch("kuzgu", 0.85 + 0.5 * clampf(k_heat / 100.0, 0.0, 1.0))
	if Engine.get_physics_frames() % 3 == 0:
		FX.sparks(k_end, -dir, Color(1.0, 0.85, 0.45), 2, 120.0)
	if k_heat >= 100.0:
		_kuzgu_flare(it, rk >= mv - 0.01)


func _kuzgu_flare(it: Dictionary, full: bool) -> void:
	## Tam ısınma: Gün Patlaması (ışının ucunda), ayna soğur (sogut sn kullanılamaz)
	var p := k_end
	var rk := clampf(k_ramp / float(KUZGU["rampa"]), 0.0, 1.0)
	stat("kuzgu_patlama")
	for e in get_tree().get_nodes_in_group("dusman"):
		if is_instance_valid(e) and not e.dead and e.center().distance_to(p) < float(KUZGU["patlama_r"]):
			pl._deal(e, float(it["dmg"]) * float(KUZGU["patlama_k"]) * (0.5 + 0.5 * rk), it,
				{"kb": 140.0, "dir": signf(e.center().x - pl.center().x), "stun": 0.6, "burn": 2.0, "v27_tam": full and e == k_target})
	FX.explosion(p, float(KUZGU["patlama_r"]) * 0.8, Color(1.0, 0.85, 0.4), false, Vector2.UP, true)
	InkFX.ring(p, 30.0, 9, 0.35)
	FX.flash_light(p, Color(1.0, 0.85, 0.45), 200.0, 2.2, 0.3)
	FX.text(pl.center() + Vector2(0, -56), "GÜN PATLAMASI", Color(1.0, 0.85, 0.4), 9)
	Game.shake(4.0)
	Game.hitstop(0.05)
	Ses.play("patlama", -4.0, 1.2)
	_kuzgu_stop()
	k_cool = float(KUZGU["sogut"])
	pl.cd[_sk()] = k_cool
	pl.cd_max[_sk()] = k_cool


func _kuzgu_stop() -> void:
	if k_on:
		Ses.loop_stop("kuzgu")
	k_on = false
	k_target = null
	k_ramp = 0.0


# ---- Tengri Bağı
func _bag(it: Dictionary, press: bool) -> void:
	var k := _sk()
	if not press or float(pl.cd[k]) > 0.0:
		return
	pl.sec_buf = 0.0
	pl.cd[k] = pl._sec_cd(it)
	pl.cd_max[k] = pl.cd[k]
	pl.cast_t = 0.35
	pl.vis_scale = Vector2(0.94, 1.06)
	for L in links:
		var alive := 0
		for o in L["m"]:
			if is_instance_valid(o) and not o.dead:
				alive += 1
		if alive > 0:
			_bag_cekis(it, L)
			links.erase(L)
			return
	_bag_fire(it)


func _bag_fire(it: Dictionary) -> void:
	var origin := pl.global_position + Vector2(float(pl.facing) * 14.0, -28.0)
	var spd := float(BAG["hiz"])
	var a := pl.okc._aim_angle(origin, spd, 0.0) if pl.okc else 0.0
	var pr := Projectile.new()
	pr.team = "p"
	pr.kind = "bag"
	pr.position = origin
	pr.velocity = Vector2(cos(a) * float(pl.facing), sin(a)) * spd
	pr.life = float(BAG["omur"])
	pr.hit_pad = Vector2(6.0, 8.0)
	pr.unsur = Unsur.of(it)
	pr.trail_col = Color(0.6, 0.7, 1.0)
	var orb := BagOrb.new()
	pr.add_child(orb)
	pr.on_hit = func(e: Node) -> void:
		pl._deal(e, float(it["dmg"]), it, {"kb": 50.0, "dir": float(pl.facing), "stun": 0.2})
		if is_instance_valid(e) and not e.dead:
			_bag_link(e, it)
	pl.level.add_projectile(pr)
	stat("bag_atis")
	Ses.play("buyu", -5.0, 1.3)
	Ses.play("yildirim", -14.0, 1.6)


func _bag_link(e: Node, it: Dictionary) -> void:
	var m: Array = [e]
	var cands: Array = []
	for o in get_tree().get_nodes_in_group("dusman"):
		if o == e or not is_instance_valid(o) or o.dead:
			continue
		var d: float = o.center().distance_to(e.center())
		if d < float(BAG["menzil"]):
			cands.append([d, o])
	cands.sort_custom(func(x: Array, y: Array) -> bool: return float(x[0]) < float(y[0]))
	for i in mini(int(it.get("mech_v", 2)), cands.size()):
		m.append(cands[i][1])
	# aynı düşman eski bir bağdaysa o bağ söner (bir düşman tek bağda)
	for L in links.duplicate():
		for o in m:
			if (L["m"] as Array).has(o):
				links.erase(L)
				break
	links.append({"m": m, "t": float(BAG["sure"])})
	stat("bag_kur")
	Ses.play("bag_zincir", -5.0, 1.1)
	stat("bag_uye", m.size())
	for o in m:
		FX.anim("electric_impact", o.center(), 0.0, 0.6, Color(0.62, 0.72, 1.0))
		InkFX.ring(o.center(), 10.0, 10, 0.22)


func _bag_cekis(it: Dictionary, L: Dictionary) -> void:
	## Bağ Çekişi: bağlılar bağın ortasına çekilip birbirine çarpar (tek bağlı: oyuncunun önüne)
	var m: Array = []
	for o in L["m"]:
		if is_instance_valid(o) and not o.dead:
			m.append(o)
	var c := Vector2.ZERO
	for o in m:
		c += o.center()
	c /= float(m.size())
	if m.size() == 1:
		c = pl.center() + Vector2(float(pl.facing) * 34.0, 0)
	var carp := m.size() >= 2
	stat("bag_cekis")
	if carp:
		stat("bag_carpisma")
	for o in m:
		var dir := signf(c.x - o.center().x)
		if not o.heavy and not o.is_boss:
			o.velocity.x = dir * 420.0
			o.velocity.y = minf(o.velocity.y, -120.0)
		FX.lightning(o.center(), c, Color(0.7, 0.8, 1.0))
		pl._deal(o, float(it["dmg"]) * float(BAG["cekis_k"]), it, {"kb": 0.0, "dir": dir, "stun": 0.6, "v27_carp": carp})
	InkFX.ring(c, 26.0, 10, 0.32)
	FX.anim("electric_impact", c, 0.0, 1.1, Color(0.7, 0.8, 1.0))
	FX.flash_light(c, Color(0.6, 0.7, 1.0), 160.0, 1.8, 0.2)
	FX.text(pl.center() + Vector2(0, -50), "BAĞ ÇEKİŞİ", Color(0.75, 0.85, 1.0), 8)
	Game.shake(3.0)
	Game.hitstop(0.05)
	Ses.play("gok_gurleme", -8.0, 1.3)
	Ses.play("bag_zincir", -3.0, 0.8)
	Ses.play("darbe_kirbac", -4.0, 0.7)


func _links_tick(delta: float) -> void:
	var keep: Array = []
	for L in links:
		L["t"] = float(L["t"]) - delta
		var m: Array = []
		for o in L["m"]:
			if is_instance_valid(o) and not o.dead:
				m.append(o)
		L["m"] = m
		if float(L["t"]) <= 0.0 or m.is_empty():
			continue
		if m.size() >= 2:
			var c := Vector2.ZERO
			for o in m:
				c += o.center()
			c /= float(m.size())
			for o in m:
				if not o.heavy and not o.is_boss and o.stun_t <= 0.0:
					o.velocity.x += signf(c.x - o.center().x) * 260.0 * delta
		keep.append(L)
	links = keep


## ------------------------------------------------------------------ poz / gövde / hareket
static func sec_pose(p: Player) -> Array:
	## Silah görseli (Player._update_weapon_visual): Tatar Yayı atış / kurma anı, Küzgü kanalı. Boş: yok
	var n := node_of(p)
	if n == null or p.sec_slot == "":
		return []
	var id := String(p.slot(p.sec_slot).get("id", ""))
	if id == "tatar_yayi" and (n.t_shot > 0.0 or n.t_flash > 0.6):
		var rk := clampf(n.t_shot / 0.3, 0.0, 1.0)
		return [PI * 0.5 - n.t_tilt + 0.22 * rk * rk, 0.05, -0.08 * rk, 1.0, 1.0 - 0.06 * rk]
	if id == "kam_kuzgusu" and n.k_on:
		return [PI * 0.5 - n.k_tilt, 0.05, -0.2 + 0.03 * sin(n._t * 40.0), 1.0, 1.0]
	return []


static func anim_override(p: Player) -> bool:
	var n := node_of(p)
	if n == null or sec_pose(p).is_empty():
		return false
	if absf(p.velocity.x) > 30.0 and p.is_on_floor():
		return false   # yürürken gövde yürür (kol iskeleti silahı tutar)
	p.anim.show_frame("cast" if n.k_on else "bow", 1)
	return true


static func move_k(p: Player) -> float:
	var n := node_of(p)
	if n and n.k_on:
		return float(KUZGU["yuru"])
	return 1.0


static func trail_style(tr: Node, it: Dictionary, atk: Dictionary) -> void:
	## Yeni silahların mürekkep izi (InkTrail.setup sonrası): sınıf ayarları ve palet
	if not (tr is InkTrail):
		return
	var t := tr as InkTrail
	var id := String(it.get("id", ""))
	if not (id in IDS):
		return
	var plain := Unsur.of(it) == ""
	var heavy: bool = atk.get("heavy", false) or atk.get("c", {}).get("last", false)
	match id:
		"kistin", "cevgen":
			t.style = "agir"
			# Kistin: zincirli topun yolu dar, ucu dolgun (geniş "levha" değil); Çevgen: uzun sapın tokmağı orta
			t.w_frac = (0.5 if id == "kistin" else 0.8) * 0.85 * (1.2 if heavy else 1.0)
			t.life = 0.095 * 1.16
			t.fleck_k = 2.4
			t.splash_end = true
			t.ramp_len = 0.8
			t.u_scale = 0.55
			t.layered = maxi(t.layered, 1)
			if plain:
				t.pal = 8 if id == "cevgen" else 0
		"albasti_hanceri":
			if plain:
				t.pal = 0
		"gun_ay_ikizi":
			if gunay == "gun":
				t.w_frac *= 1.1
				t.inner_arc = true
			if plain:
				t.pal = 9 if gunay == "gun" else 7
	t._apply_mat()


## ------------------------------------------------------------------ kare
func _physics_process(delta: float) -> void:
	if pl == null or not is_instance_valid(pl):
		return
	_t += delta
	global_position = Vector2.ZERO
	t_shot = maxf(0.0, t_shot - delta)
	t_flash = maxf(0.0, t_flash - delta * 2.2)
	k_cool = maxf(0.0, k_cool - delta)
	if not k_on:
		k_heat = maxf(0.0, k_heat - float(KUZGU["soguma"]) * delta)
	var sec := pl.slot(pl.sec_slot) if pl.sec_slot != "" else {}
	if k_on and String(sec.get("id", "")) != "kam_kuzgusu":
		_kuzgu_stop()
	if bound_t > 0.0:
		bound_t -= delta
		if bound_t <= 0.0 or bound == null or not is_instance_valid(bound) or bound.dead:
			bound = null
			bound_t = 0.0
	_throw_tick(delta)
	_balls_tick(delta)
	_links_tick(delta)
	_back_blade_tick()
	# al izi söner
	if Engine.get_physics_frames() % 10 == 0:
		for e in get_tree().get_nodes_in_group("dusman"):
			if is_instance_valid(e) and int(e.get_meta("v27_iz", 0)) > 0 and Game.clock() - float(e.get_meta("v27_iz_t", 0.0)) > float(ALBASTI["sure"]):
				e.set_meta("v27_iz", 0)
	queue_redraw()


## ------------------------------------------------------------------ çizim (mürekkep: koyu kenar + renkli çekirdek)
const INK := Color(0.08, 0.07, 0.1, 0.92)


func _ink_line(a: Vector2, b: Vector2, w: float, col: Color) -> void:
	draw_line(a, b, INK, w + 1.6, true)
	draw_line(a, b, col, w, true)


func _jag(a: Vector2, b: Vector2, n: int, amp: float, seed_v: float) -> PackedVector2Array:
	var out := PackedVector2Array()
	var d := b - a
	var nrm := Vector2(-d.y, d.x).normalized()
	for i in n + 1:
		var k := float(i) / float(n)
		var off := 0.0 if (i == 0 or i == n) else sin(seed_v * 13.7 + float(i) * 2.3 + _t * 31.0) * amp
		out.append(a + d * k + nrm * off)
	return out


func _draw() -> void:
	if pl == null:
		return
	# Albastı: al izleri (izli düşmanın başında kızıl tamga taneleri)
	for e in get_tree().get_nodes_in_group("dusman"):
		if not is_instance_valid(e) or e.dead:
			continue
		var iz := int(e.get_meta("v27_iz", 0))
		if iz > 0:
			var top: Vector2 = e.center() + Vector2(0, -e.size.y * 0.5 - 10.0)
			for i in iz:
				var p := top + Vector2((float(i) - (iz - 1) * 0.5) * 7.0, 0)
				var pulse := 1.0 + 0.15 * sin(_t * 9.0 + i)
				draw_circle(p, 3.4 * pulse, INK)
				draw_circle(p, 2.3 * pulse, Color(0.92, 0.12, 0.18) if iz < 3 else Color(1.0, 0.35, 0.3))
				draw_line(p + Vector2(-1.6, -1.6), p + Vector2(1.6, 1.6), INK, 0.8, true)
	# Kistin: dolanan zincir (elden bağlı düşmana, gövdesinde halkalar)
	var be: Node = bound if (bound != null and is_instance_valid(bound) and not bound.dead) else null
	if be == null and not _throw.is_empty() and is_instance_valid(_throw["e"]):
		be = _throw["e"]
	if be:
		var hand := pl.arm_root.to_global(pl._hand_local) if pl.arm_root.visible else pl.center()
		var ec: Vector2 = be.center()
		var sag := minf(18.0, hand.distance_to(ec) * 0.12)
		var mid := (hand + ec) * 0.5 + Vector2(0, sag)
		var pts := PackedVector2Array()
		for i in 13:
			var k := float(i) / 12.0
			pts.append((1.0 - k) * (1.0 - k) * hand + 2.0 * (1.0 - k) * k * mid + k * k * ec)
		draw_polyline(pts, INK, 3.4, true)
		draw_polyline(pts, Color(0.55, 0.56, 0.62), 1.6, true)
		for i in range(1, 12, 2):
			draw_circle(pts[i], 1.7, Color(0.62, 0.63, 0.7))
		# gövdeye dolanan zincir: eğik, yassı elipsler boyunca halka halka (arka yarı soluk)
		var rx: float = be.size.x * 0.6
		for r in 2:
			var ry := -5.0 + r * 7.0
			for q in 14:
				var a := float(q) / 14.0 * TAU + _t * 2.0 + r
				var lp := ec + Vector2(cos(a) * rx, ry + sin(a) * 3.2 + cos(a) * 2.5)
				var front := sin(a) > 0.0
				var lc := Color(0.66, 0.67, 0.74) if front else Color(0.36, 0.36, 0.42, 0.8)
				var ld := Vector2(-sin(a), cos(a) * 0.35).normalized() * 1.9
				draw_line(lp - ld, lp + ld, INK, 3.2, true)
				draw_line(lp - ld, lp + ld, lc, 1.5, true)
	# Tengri Bağı: bağlar (titreyen gök zinciri) ve bağlı düşmanlarda düğüm
	for L in links:
		var m: Array = L["m"]
		var fade := clampf(float(L["t"]) / 0.6, 0.0, 1.0)
		for i in m.size():
			var o: Node = m[i]
			if not is_instance_valid(o):
				continue
			var c: Vector2 = o.center()
			draw_arc(c, 7.0 + 1.5 * sin(_t * 8.0 + i), _t * 4.0, _t * 4.0 + TAU * 0.8, 14, Color(INK, 0.8 * fade), 3.2, true)
			draw_arc(c, 7.0 + 1.5 * sin(_t * 8.0 + i), _t * 4.0, _t * 4.0 + TAU * 0.8, 14, Color(0.6, 0.72, 1.0, fade), 1.5, true)
			if i > 0 and is_instance_valid(m[0]):
				var j := _jag(m[0].center(), c, 9, 3.0, float(i))
				draw_polyline(j, Color(INK, 0.85 * fade), 3.0, true)
				draw_polyline(j, Color(0.62, 0.74, 1.0, fade), 1.4, true)
				draw_polyline(_jag(m[0].center(), c, 9, 1.2, float(i) + 4.0), Color(0.95, 0.97, 1.0, 0.7 * fade), 0.6, true)
	# Kam Küzgüsü: gün ışını (koyu mürekkep kenar, altın gövde, beyaz çekirdek; ısındıkça kızarır)
	if k_on:
		var heat := clampf(k_heat / 100.0, 0.0, 1.0)
		var body := Color(1.0, 0.82, 0.32).lerp(Color(1.0, 0.42, 0.18), heat)
		var rk := clampf(k_ramp / float(KUZGU["rampa"]), 0.0, 1.0)
		var w := 3.0 + 3.2 * rk
		var a := k_from
		var b := k_end
		var d := b - a
		var nrm := Vector2(-d.y, d.x).normalized()
		var n := maxi(4, int(d.length() / 14.0))
		var edge := PackedVector2Array()
		var core := PackedVector2Array()
		for i in n + 1:
			var k := float(i) / float(n)
			var wob := sin(k * 18.0 - _t * 40.0) * (0.6 + 1.2 * rk) * (1.0 - absf(k - 0.5))
			edge.append(a + d * k + nrm * wob)
			core.append(a + d * k + nrm * wob * 0.5)
		draw_polyline(edge, INK, w + 3.2, true)
		draw_polyline(edge, body, w, true)
		draw_polyline(core, Color(1.0, 0.98, 0.9), maxf(1.0, w * 0.35), true)
		draw_circle(b, w * 1.3 + 2.0 * sin(_t * 30.0), INK)
		draw_circle(b, w * 1.1, body)
		draw_circle(b, w * 0.5, Color(1.0, 0.98, 0.9))
		draw_circle(a, 3.0 + 1.0 * rk, Color(1.0, 0.95, 0.75, 0.9))
	# Küzgü ısı göstergesi / Tatar kurma çubuğu (başın üstünde)
	var sec := pl.slot(pl.sec_slot) if pl.sec_slot != "" else {}
	var sid := String(sec.get("id", ""))
	var gp := pl.global_position + Vector2(-14, -58)
	if sid == "kam_kuzgusu" and (k_heat > 0.5 or k_cool > 0.0):
		var q := clampf(k_heat / 100.0, 0.0, 1.0) if k_cool <= 0.0 else k_cool / float(KUZGU["sogut"])
		var col := Color(1.0, 0.8, 0.3).lerp(Color(1.0, 0.3, 0.15), q) if k_cool <= 0.0 else Color(0.55, 0.55, 0.65)
		_bar(gp, 28.0, q, col)
	if sid == "tatar_yayi" and pl.sec_slot != "" and float(pl.cd[pl.sec_slot]) > 0.0:
		var R := maxf(0.01, float(pl.cd_max[pl.sec_slot]))
		var q2 := 1.0 - float(pl.cd[pl.sec_slot]) / R
		var sw: Array = TATAR["tatli"]
		var w0 := 28.0
		draw_rect(Rect2(gp + Vector2(-1.5, -1.5), Vector2(w0 + 3.0, 6.0)), INK)
		draw_rect(Rect2(gp, Vector2(w0, 3.0)), Color(0.2, 0.18, 0.22, 0.9))
		if not t_attempt:
			draw_rect(Rect2(gp + Vector2(w0 * float(sw[0]), -0.5), Vector2(w0 * (float(sw[1]) - float(sw[0])), 4.0)), Color(1.0, 0.8, 0.3, 0.95))
		draw_rect(Rect2(gp, Vector2(w0 * q2, 3.0)), Color(0.92, 0.88, 0.8, 0.85))
		draw_line(gp + Vector2(w0 * q2, -2.5), gp + Vector2(w0 * q2, 5.5), Color(1, 1, 1), 1.2, true)
	if t_flash > 0.0 and sid == "tatar_yayi":
		draw_arc(gp + Vector2(14, 1.5), 10.0 + (1.0 - t_flash) * 10.0, 0.0, TAU, 20, Color(t_flash_col, t_flash), 1.6, true)


func _bar(p: Vector2, w: float, q: float, col: Color) -> void:
	draw_rect(Rect2(p + Vector2(-1.5, -1.5), Vector2(w + 3.0, 6.0)), INK)
	draw_rect(Rect2(p, Vector2(w, 3.0)), Color(0.2, 0.18, 0.22, 0.9))
	draw_rect(Rect2(p, Vector2(w * q, 3.0)), col)


## Tengri Bağı mermisinin görünüşü: dönen gök düğümü (mürekkep halka + iki yay + parlak öz)
class BagOrb:
	extends Node2D
	var t := 0.0

	func _process(delta: float) -> void:
		t += delta
		queue_redraw()

	func _draw() -> void:
		var r := 5.5
		draw_circle(Vector2.ZERO, r + 1.8, Color(0.08, 0.07, 0.12, 0.9))
		draw_circle(Vector2.ZERO, r, Color(0.45, 0.55, 1.0))
		draw_circle(Vector2.ZERO, r * 0.45, Color(0.95, 0.97, 1.0))
		for k in 2:
			var a0 := t * 9.0 + k * PI
			draw_arc(Vector2.ZERO, r + 4.0, a0, a0 + 2.0, 10, Color(0.08, 0.07, 0.12, 0.85), 2.4, true)
			draw_arc(Vector2.ZERO, r + 4.0, a0, a0 + 2.0, 10, Color(0.7, 0.8, 1.0), 1.1, true)
