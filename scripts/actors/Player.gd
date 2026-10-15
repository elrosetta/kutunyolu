class_name Player
extends CharacterBody2D
## Bengü: hareket hissi (squash & stretch, eğilme, toz, coyote/apex), silah başına özgün kombolar,
## kılıç izi ve darbe efektleri, yay/fırlatma, kalkan, teçhizat, şişe, Kut gücü, tünel yuvarlanması.

const RUN := 155.0
const ACC_GROUND := 2600.0
const DEC_GROUND := 2400.0
const ACC_AIR := 1500.0
const JUMP_V := -430.0
const GRAV := 1180.0
const MAX_FALL := 560.0
const ROLL_V := 300.0
const ROLL_T := 0.3

## ------------------------------------------------------------------ SAVURUŞLAR
## Ön kol ve silah oyunda sürülür. Anahtar: [t, a1, a2, w, k, ext, ease]
##   a1 üst kol açısı, a2 dirsek bükümü, w bilek (silahın ön kola göre açısı); 0 aşağı, pi/2 ileri, pi yukarı
##   k  yatay derinlik kısalması (1 = yan görünüş; küçük = kola/silaha kameraya doğru bakıyor)
##   ext ön kol uzatması (darbe anındaki abartı), ease: 0 yumuşak, 1 hızlanarak (vuruş), 2 yavaşlayarak (takip)
## Hazırlık yavaş, vuruş çok hızlı (kareler arası 1-2 ara örnek), takip ağırlıkla yavaşlar.
const SWINGS := {
	# yukarıdan aşağı: kılıç sırtın arkasına çekilir, baş üstünden öne-aşağı iner
	"down": {"body": "atk_down", "hit": [0.3, 0.56], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, 3.2, 0.7, 0.8, 1.0, 1.0, 2], [0.3, 3.3, 0.75, 0.85, 1.0, 1.0, 0],
		[0.42, 1.3, 0.0, 0.2, 1.0, 1.15, 1], [0.56, 0.6, 0.15, 0.05, 1.0, 1.05, 2], [1.0, 0.5, 0.9, 0.4, 1.0, 1.0, 0]]},
	# aşağıdan yukarı: kol aşağı-geride, kılıç önden yukarı fırlar
	"up": {"body": "atk_up", "hit": [0.3, 0.56], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, -0.5, -0.5, -0.4, 1.0, 1.0, 2], [0.3, -0.62, -0.55, -0.45, 1.0, 1.0, 0],
		[0.42, 1.9, 0.0, 0.25, 1.0, 1.12, 1], [0.56, 2.65, 0.1, 0.2, 1.0, 1.05, 2], [1.0, 0.8, 0.9, 0.4, 1.0, 1.0, 0]]},
	# soldan sağa (düz el): kol arkada yatay, kameraya doğru kısalarak geçer, önde açılır
	"horiz": {"body": "atk_horiz", "hit": [0.3, 0.56], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, -1.4, -0.25, -0.15, 1.0, 1.0, 2], [0.3, -1.48, -0.3, -0.2, 1.0, 1.0, 0],
		[0.355, -1.45, -0.1, 0.0, 0.22, 1.0, 1], [0.356, 1.5, 0.1, 0.0, 0.22, 1.0, 0],
		[0.42, 1.55, 0.0, 0.05, 1.0, 1.12, 2], [0.56, 1.75, 0.2, 0.2, 0.7, 1.0, 2], [1.0, 0.7, 0.9, 0.4, 1.0, 1.0, 0]]},
	# sağdan sola (ters el): kılıç göğüs önünden omuz üstüne çekilir, ters elle öne savrulur
	"back": {"body": "atk_horiz", "hit": [0.3, 0.56], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, 0.9, 1.9, 1.2, 1.0, 1.0, 2], [0.3, 0.85, 2.0, 1.3, 1.0, 1.0, 0],
		[0.355, 1.2, 1.0, 1.4, 0.3, 1.0, 1], [0.356, 1.4, 0.2, -0.2, 0.3, 1.0, 0],
		[0.42, 1.6, 0.0, 0.0, 1.0, 1.12, 2], [0.56, 1.35, 0.3, -0.25, 0.75, 1.0, 2], [1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# saplama: dirsek geri, el kalçada; ok gibi ileri
	"thrust": {"body": "atk_thrust", "hit": [0.32, 0.56], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, -0.3, 1.9, 0.0, 1.0, 1.0, 2], [0.32, -0.48, 2.05, 0.0, 1.0, 1.0, 0],
		[0.4, 1.55, 0.0, 0.0, 1.0, 1.3, 1], [0.56, 1.5, 0.05, 0.0, 1.0, 1.2, 2], [1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# hücum: saplama + gövde ileri fırlar
	"lunge": {"body": "atk_lunge", "hit": [0.3, 0.58], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, -0.4, 2.0, -0.1, 1.0, 1.0, 2], [0.3, -0.55, 2.1, -0.1, 1.0, 1.0, 0],
		[0.38, 1.57, 0.0, 0.0, 1.0, 1.35, 1], [0.58, 1.52, 0.0, 0.0, 1.0, 1.3, 2], [1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# ağır iniş (iki el): kol dimdik yukarıda, tüm ağırlıkla yere
	"heavy": {"body": "atk_heavy", "hit": [0.33, 0.62], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.25, 3.3, 0.3, 0.25, 1.0, 1.0, 2], [0.33, 3.45, 0.35, 0.3, 1.0, 1.0, 0],
		[0.45, 0.9, 0.0, 0.0, 1.0, 1.15, 1], [0.62, 0.5, 0.0, -0.1, 1.0, 1.1, 2], [1.0, 0.6, 0.6, 0.2, 1.0, 1.0, 0]]},
	# çevrinti: silah gövdenin önünde tam tur döner (iki yanı biçer)
	"spin": {"body": "atk_spin", "hit": [0.3, 0.66], "around": true, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, 0.2, 0.3, 0.1, 1.0, 1.0, 2], [0.3, 0.35, 0.1, 0.0, 1.0, 1.0, 0],
		[0.66, 6.63, 0.0, 0.0, 1.0, 1.12, 0], [1.0, 6.9, 0.9, 0.3, 1.0, 1.0, 0]]},
	# yükselen kesik: çömel, yukarı savur (düşmanı havaya atar)
	"rise": {"body": "atk_up", "hit": [0.3, 0.58], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, -0.2, -0.3, -0.6, 1.0, 1.0, 2], [0.3, -0.3, -0.35, -0.65, 1.0, 1.0, 0],
		[0.44, 2.4, 0.0, 0.2, 1.0, 1.15, 1], [0.58, 3.0, 0.05, 0.1, 1.0, 1.08, 2], [1.0, 1.2, 0.9, 0.4, 1.0, 1.0, 0]]},
	# seri saplama: üç hızlı saplama (her biri ayrı vuruş)
	"flurry": {"body": "atk_thrust", "hit": [0.14, 0.66], "multi": [0.2, 0.36, 0.52], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.12, -0.3, 1.9, 0.0, 1.0, 1.0, 2], [0.2, 1.55, 0.0, 0.0, 1.0, 1.25, 1],
		[0.28, -0.2, 1.8, 0.1, 1.0, 1.0, 2], [0.36, 1.45, 0.0, -0.05, 1.0, 1.25, 1], [0.44, -0.2, 1.8, 0.0, 1.0, 1.0, 2],
		[0.52, 1.62, 0.0, 0.05, 1.0, 1.3, 1], [0.66, 1.5, 0.05, 0.0, 1.0, 1.2, 2], [1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# zıplayıp ezme: ağır inişin büyük sürümü (sıçrayarak)
	"slam": {"body": "atk_heavy", "hit": [0.36, 0.66], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.28, 3.4, 0.25, 0.3, 1.0, 1.0, 2], [0.36, 3.55, 0.3, 0.3, 1.0, 1.0, 0],
		[0.48, 0.8, 0.0, -0.05, 1.0, 1.2, 1], [0.66, 0.45, 0.0, -0.15, 1.0, 1.12, 2], [1.0, 0.6, 0.6, 0.2, 1.0, 1.0, 0]]},
	# fırlatma (balta)
	"axe": {"body": "throw", "hit": [0.3, 0.4], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.25, 3.4, 0.8, 0.3, 1.0, 1.0, 2], [0.35, 1.4, 0.0, 0.0, 1.0, 1.1, 1], [1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# ---------------------------------------------------------------- v5: silaha özgü savuruşlar
	# çapraz iniş: omuzdan kalçaya (sağ üst -> sol alt)
	"diag_down": {"body": "atk_down", "hit": [0.3, 0.55], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, 2.7, 0.5, 0.7, 0.95, 1.0, 2], [0.3, 2.85, 0.55, 0.75, 0.9, 1.0, 0],
		[0.42, 1.1, 0.0, 0.1, 1.0, 1.15, 1], [0.55, 0.35, 0.1, -0.2, 1.0, 1.05, 2], [1.0, 0.5, 0.9, 0.4, 1.0, 1.0, 0]]},
	# çapraz yükseliş: kalçadan omuza
	"diag_up": {"body": "atk_up", "hit": [0.3, 0.55], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, -0.35, -0.4, -0.5, 0.95, 1.0, 2], [0.3, -0.45, -0.45, -0.55, 0.9, 1.0, 0],
		[0.42, 1.3, 0.0, 0.15, 1.0, 1.12, 1], [0.55, 2.5, 0.1, 0.3, 1.0, 1.05, 2], [1.0, 0.8, 0.9, 0.4, 1.0, 1.0, 0]]},
	# çapraz kesik (X): iniş + yükseliş tek hamlede, iki vuruş
	"cross_x": {"body": "atk_horiz", "hit": [0.24, 0.7], "multi": [0.3, 0.56], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.18, 2.8, 0.5, 0.7, 0.95, 1.0, 2], [0.24, 2.9, 0.55, 0.75, 0.9, 1.0, 0],
		[0.32, 0.9, 0.0, 0.0, 1.0, 1.15, 1], [0.4, 0.2, 0.0, -0.3, 1.0, 1.05, 2],
		[0.48, -0.3, -0.3, -0.5, 0.9, 1.0, 2], [0.58, 1.4, 0.0, 0.15, 1.0, 1.15, 1], [0.7, 2.6, 0.1, 0.3, 1.0, 1.05, 2], [1.0, 0.7, 0.9, 0.4, 1.0, 1.0, 0]]},
	# iki elli baş üstü iniş (dev kılıç / balta)
	"overhead_2h": {"body": "atk_heavy", "hit": [0.4, 0.64], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.3, 3.35, 0.25, 0.3, 0.85, 1.0, 2], [0.4, 3.5, 0.3, 0.35, 0.8, 1.0, 0],
		[0.52, 1.0, 0.0, 0.0, 1.0, 1.2, 1], [0.64, 0.35, 0.0, -0.15, 1.0, 1.1, 2], [1.0, 0.6, 0.6, 0.2, 1.0, 1.0, 0]]},
	# yerde sürükleyip yukarı: kılıç arkada toprağı yalar, kıvılcımla yükselir
	"ground_drag": {"body": "atk_up", "hit": [0.34, 0.6], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.24, -0.95, 0.15, 0.35, 1.0, 1.0, 2], [0.34, -1.05, 0.2, 0.4, 1.0, 1.0, 0],
		[0.47, 1.5, 0.0, 0.1, 1.0, 1.15, 1], [0.6, 2.5, 0.05, 0.2, 1.0, 1.08, 2], [1.0, 1.0, 0.9, 0.4, 1.0, 1.0, 0]]},
	# diz hizası yatay süpürme (alçak)
	"sweep_low": {"body": "atk_horiz", "hit": [0.3, 0.56], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, -0.9, 0.0, -0.3, 0.9, 1.0, 2], [0.3, -1.0, 0.0, -0.35, 0.85, 1.0, 0],
		[0.355, 0.1, 0.0, -0.2, 0.25, 1.1, 1], [0.356, 0.8, 0.0, -0.2, 0.25, 1.1, 0],
		[0.42, 1.05, 0.0, -0.1, 1.0, 1.15, 2], [0.56, 1.25, 0.1, 0.0, 0.8, 1.05, 2], [1.0, 0.7, 0.9, 0.4, 1.0, 1.0, 0]]},
	# ters el: bıçak ön kol boyunca geriye bakar, dirsekten çevrilerek savrulur
	"reverse_grip": {"body": "atk_horiz", "hit": [0.3, 0.56], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, 1.5, 1.7, 3.0, 1.0, 1.0, 2], [0.3, 1.55, 1.8, 3.05, 1.0, 1.0, 0],
		[0.355, 1.5, 0.8, 3.0, 0.35, 1.0, 1], [0.356, 1.45, 0.3, 3.0, 0.35, 1.0, 0],
		[0.42, 1.4, -0.3, 2.95, 1.0, 1.1, 2], [0.56, 1.2, -0.5, 2.9, 0.9, 1.0, 2], [1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# bilek çevrimi: kılıç elde tam tur döner (iki vuruş)
	"twirl": {"body": "atk_spin", "hit": [0.26, 0.7], "multi": [0.36, 0.58], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.2, 1.5, 0.1, 0.2, 1.0, 1.0, 2], [0.26, 1.55, 0.05, 0.0, 1.0, 1.0, 0],
		[0.48, 1.55, 0.0, 3.2, 1.0, 1.05, 0], [0.7, 1.5, 0.0, 6.4, 1.0, 1.05, 0], [1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# yel değirmeni: baş üstünden tam tur geriye, sonra tüm ağırlıkla yere
	"windmill": {"body": "atk_heavy", "hit": [0.44, 0.66], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.16, 1.3, 0.2, 0.1, 1.0, 1.0, 0], [0.3, 3.0, 0.2, 0.2, 0.75, 1.0, 0], [0.44, 4.6, 0.2, 0.3, 0.8, 1.0, 0],
		[0.55, 7.1, 0.0, 0.0, 1.0, 1.2, 1], [0.66, 6.65, 0.0, -0.15, 1.0, 1.1, 2], [1.0, 6.9, 0.6, 0.2, 1.0, 1.0, 0]]},
	# mızrak saplaması: uzun uzanış
	"pole_thrust": {"body": "atk_thrust", "hit": [0.3, 0.54], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, -0.6, 2.0, 0.1, 1.0, 0.8, 2], [0.3, -0.75, 2.1, 0.1, 1.0, 0.75, 0],
		[0.38, 1.55, 0.0, 0.0, 1.0, 1.5, 1], [0.54, 1.5, 0.05, 0.0, 1.0, 1.4, 2], [1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# iki elli geniş sırık süpürmesi
	"pole_sweep": {"body": "atk_horiz", "hit": [0.3, 0.6], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, -1.5, -0.2, -0.4, 0.9, 1.1, 2], [0.3, -1.6, -0.25, -0.45, 0.85, 1.1, 0],
		[0.36, -1.4, 0.0, -0.2, 0.3, 1.2, 1], [0.361, 1.3, 0.0, -0.2, 0.3, 1.2, 0],
		[0.45, 1.6, 0.0, 0.0, 1.0, 1.3, 2], [0.6, 2.0, 0.2, 0.3, 0.7, 1.1, 2], [1.0, 0.7, 0.9, 0.4, 1.0, 1.0, 0]]},
	# biçme: önden geriye, kendine çekerek (tırpan)
	"reap": {"body": "atk_horiz", "hit": [0.3, 0.58], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, 2.0, 0.2, 0.4, 0.9, 1.15, 2], [0.3, 2.1, 0.2, 0.45, 0.85, 1.15, 0],
		[0.36, 1.6, 0.0, 0.3, 0.4, 1.2, 1], [0.361, 0.9, 0.0, 0.2, 0.4, 1.2, 0],
		[0.46, -0.5, 0.2, 0.0, 1.0, 1.1, 2], [0.58, -0.9, 0.4, -0.2, 0.85, 1.0, 2], [1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# pençe tırmığı: iki hızlı aşağı tırmalama
	"rake": {"body": "atk_down", "hit": [0.2, 0.62], "multi": [0.28, 0.5], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.14, 2.2, 0.3, 0.6, 1.0, 1.0, 2], [0.2, 2.3, 0.3, 0.6, 1.0, 1.0, 0],
		[0.3, 0.9, 0.0, 0.0, 1.0, 1.1, 1], [0.38, 2.0, 0.3, 0.5, 1.0, 1.0, 2], [0.52, 0.7, 0.0, -0.1, 1.0, 1.12, 1], [0.62, 0.5, 0.1, -0.2, 1.0, 1.05, 2], [1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# kırbaç şaklaması: kol arkaya yukarı, öne şaklar (uzun uzanış)
	"whip_crack": {"body": "atk_down", "hit": [0.3, 0.52], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, 3.0, 0.6, 0.9, 1.0, 1.0, 2], [0.3, 3.1, 0.65, 1.0, 1.0, 1.0, 0],
		[0.4, 1.6, 0.0, -0.4, 1.0, 1.4, 1], [0.52, 1.4, 0.0, -0.6, 1.0, 1.25, 2], [1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# balta kancası: baş üstünden iniş, sonra kancayla kendine çekiş
	"axe_hook": {"body": "atk_down", "hit": [0.3, 0.6], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, 3.1, 0.5, 0.4, 1.0, 1.0, 2], [0.3, 3.2, 0.55, 0.45, 1.0, 1.0, 0],
		[0.42, 1.0, 0.0, 0.0, 1.0, 1.15, 1], [0.52, 0.6, 0.3, -0.6, 1.0, 1.0, 2], [0.6, 0.4, 0.9, -0.9, 1.0, 0.9, 2], [1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# çekiş (iai): kılıç kalçada geriye bakar, tek hamlede açılır
	"iai": {"body": "atk_horiz", "hit": [0.26, 0.42], "keys": [
		[0.0, 0.5, 1.5, -1.3, 1.0, 1.0, 0], [0.2, 0.45, 1.6, -1.35, 1.0, 1.0, 2], [0.26, 0.4, 1.65, -1.4, 0.9, 1.0, 0],
		[0.34, 1.7, 0.0, 0.0, 1.0, 1.2, 1], [0.42, 2.0, 0.0, 0.1, 1.0, 1.1, 2], [1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# iki elli aparkat: alçak-arkadan baş üstüne (fırlatır)
	"uppercut_2h": {"body": "atk_up", "hit": [0.34, 0.6], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.24, -0.5, 0.3, 0.2, 0.9, 1.0, 2], [0.34, -0.6, 0.35, 0.25, 0.85, 1.0, 0],
		[0.47, 1.6, 0.0, 0.0, 1.0, 1.2, 1], [0.6, 2.8, 0.0, 0.1, 1.0, 1.1, 2], [1.0, 1.0, 0.9, 0.4, 1.0, 1.0, 0]]},
	# iki elli çakma: sıçrayıp yere
	"slam_2h": {"body": "atk_heavy", "hit": [0.4, 0.68], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.3, 3.4, 0.2, 0.3, 0.85, 1.0, 2], [0.4, 3.55, 0.25, 0.35, 0.8, 1.0, 0],
		[0.54, 0.9, 0.0, 0.0, 1.0, 1.2, 1], [0.68, 0.35, 0.0, -0.2, 1.0, 1.1, 2], [1.0, 0.6, 0.6, 0.2, 1.0, 1.0, 0]]},
	# şarjlı saplama: uzun uzanış + öne hamle
	"stab_heavy": {"body": "atk_lunge", "hit": [0.36, 0.62], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.26, -0.6, 2.1, 0.0, 1.0, 0.8, 2], [0.36, -0.7, 2.15, 0.0, 1.0, 0.75, 0],
		[0.44, 1.6, 0.0, 0.0, 1.0, 1.55, 1], [0.62, 1.55, 0.0, 0.0, 1.0, 1.45, 2], [1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# baş üstü çark: iki tam tur, iki yanı biçer (iki vuruş)
	"helicopter": {"body": "atk_spin", "hit": [0.26, 0.78], "around": true, "multi": [0.4, 0.62], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.2, 2.9, 0.2, 0.1, 1.0, 1.0, 2], [0.26, 3.0, 0.1, 0.0, 0.9, 1.0, 0],
		[0.52, 6.1, 0.0, 0.0, 0.6, 1.2, 0], [0.78, 9.3, 0.0, 0.0, 0.6, 1.2, 0], [1.0, 9.6, 0.9, 0.3, 1.0, 1.0, 0]]},
}

## Silah uzunluğu (kabzadan uca, piksel): iz ve vuruş kutusu buna göre ölçeklenir
const REACH := {"ulu_kilic": 48.0, "dag_cekici": 40.0, "ruh_kilici": 32.0, "ay_palasi": 20.0, "alp_kilici": 31.0, "yildirim_kilici": 36.0, "pala": 28.0, "yatagan": 27.0, "gurz": 24.0, "teber": 34.0, "kargi": 44.0,
	"ikiz_bicak": 16.0, "savas_baltasi": 26.0, "erlik_tirpani": 40.0, "kurt_pencesi": 14.0, "ayaz_kilici": 33.0, "civili_topuz": 27.0,
	"kement": 38.0, "od_kamcisi": 38.0, "yilan_kilici": 30.0, "kor_cekici": 36.0, "ruzgar_kilici": 32.0,
	"tulpar_mizragi": 48.0, "bori_hanceri": 15.0, "ikiz_balta": 26.0, "kayin_asasi": 40.0, "bozgun_kilici": 42.0}
## Ağır silahlar: daha uzun duraklama, daha sert kamera, daha geniş sarsıntı
const HEAVY := ["gurz", "teber", "civili_topuz", "erlik_tirpani", "savas_baltasi", "ulu_kilic", "dag_cekici", "kor_cekici", "bozgun_kilici"]

## Kombolar: "chain" art arda basınca, "pause" iki (ya da daha çok) vuruştan sonra kısa bekleyip basınca.
## Adım: {"s": savuruş, "mult": hasar, "kb": geri itme, ...bayraklar}. Bayraklar: last, shock, launch, dash,
## double, slam, whip, axe, wave. Her silahın zinciri, bekleme bitirişi ve ağır saldırısı (HEAVIES) kendine özgüdür.
const COMBOS := {
	# --- tür varsayılanları
	"slash": {"chain": [{"s": "horiz", "mult": 1.0, "kb": 110.0}, {"s": "down", "mult": 1.0, "kb": 110.0}, {"s": "back", "mult": 1.3, "kb": 220.0, "last": true}],
		"pause": {"s": "spin", "mult": 1.25, "kb": 160.0, "name": "Kasırga"}},
	"dual": {"chain": [{"s": "horiz", "mult": 1.0, "kb": 45.0}, {"s": "back", "mult": 1.0, "kb": 45.0}, {"s": "horiz", "mult": 1.0, "kb": 45.0}, {"s": "thrust", "mult": 1.3, "kb": 170.0, "double": true, "last": true}],
		"pause": {"s": "flurry", "mult": 0.8, "kb": 60.0, "name": "Bıçak Yağmuru"}},
	"heavy": {"chain": [{"s": "windmill", "mult": 1.0, "kb": 280.0, "shock": true}, {"s": "overhead_2h", "mult": 1.1, "kb": 200.0, "last": true}],
		"pause": {"s": "slam", "mult": 1.6, "kb": 300.0, "shock": true, "slam": true, "name": "Yer Yaran"}},
	"thrust": {"chain": [{"s": "thrust", "mult": 1.0, "kb": 150.0}, {"s": "thrust", "mult": 1.1, "kb": 170.0}, {"s": "horiz", "mult": 1.3, "kb": 230.0, "last": true}],
		"pause": {"s": "lunge", "mult": 1.6, "kb": 220.0, "dash": 90.0, "name": "Akın"}},
	"whip": {"chain": [{"s": "whip_crack", "mult": 1.0, "kb": 40.0, "whip": true}, {"s": "horiz", "mult": 1.1, "kb": 60.0, "whip": true, "last": true}],
		"pause": {"s": "spin", "mult": 1.2, "kb": 120.0, "whip": true, "name": "Kement Halkası"}},
	# --- kılıçlar
	"alp_kilici": {"chain": [{"s": "diag_down", "mult": 1.0, "kb": 110.0}, {"s": "horiz", "mult": 1.0, "kb": 110.0}, {"s": "down", "mult": 1.35, "kb": 240.0, "last": true}],
		"pause": {"s": "cross_x", "mult": 1.1, "kb": 150.0, "name": "Alp Çaprazı"}},
	"yildirim_kilici": {"chain": [{"s": "iai", "mult": 1.0, "kb": 100.0}, {"s": "back", "mult": 1.0, "kb": 110.0}, {"s": "thrust", "mult": 1.3, "kb": 180.0, "last": true}],
		"pause": {"s": "flurry", "mult": 0.8, "kb": 70.0, "name": "Şimşek Dişleri"}},
	"pala": {"chain": [{"s": "diag_down", "mult": 1.0, "kb": 100.0}, {"s": "back", "mult": 1.05, "kb": 110.0}, {"s": "sweep_low", "mult": 1.3, "kb": 160.0, "last": true}],
		"pause": {"s": "lunge", "mult": 1.5, "kb": 200.0, "dash": 70.0, "name": "Pala Akını"}},
	"yatagan": {"chain": [{"s": "reverse_grip", "mult": 0.9, "kb": 70.0}, {"s": "horiz", "mult": 0.9, "kb": 70.0}, {"s": "reverse_grip", "mult": 0.9, "kb": 70.0}, {"s": "lunge", "mult": 1.4, "kb": 160.0, "dash": 70.0, "last": true}],
		"pause": {"s": "flurry", "mult": 0.85, "kb": 60.0, "name": "Yatağan Fırtınası"}},
	"ayaz_kilici": {"chain": [{"s": "sweep_low", "mult": 1.0, "kb": 100.0}, {"s": "diag_down", "mult": 1.0, "kb": 110.0}, {"s": "thrust", "mult": 1.3, "kb": 200.0, "last": true}],
		"pause": {"s": "spin", "mult": 1.3, "kb": 160.0, "name": "Ayaz Halkası"}},
	"ulu_kilic": {"chain": [{"s": "horiz", "mult": 1.0, "kb": 200.0}, {"s": "overhead_2h", "mult": 1.15, "kb": 240.0, "slam": true, "last": true}],
		"pause": {"s": "helicopter", "mult": 1.5, "kb": 260.0, "name": "Ulu Çark"}},
	"ruh_kilici": {"chain": [{"s": "diag_down", "mult": 1.0, "kb": 80.0, "wave": true}, {"s": "back", "mult": 1.0, "kb": 80.0, "wave": true}, {"s": "twirl", "mult": 1.2, "kb": 140.0, "wave": true, "last": true}],
		"pause": {"s": "spin", "mult": 1.2, "kb": 120.0, "wave": true, "name": "Ruh Fırtınası"}},
	"ay_palasi": {"chain": [{"s": "twirl", "mult": 1.0, "kb": 40.0}, {"s": "back", "mult": 1.0, "kb": 40.0}, {"s": "diag_down", "mult": 1.0, "kb": 40.0}, {"s": "reverse_grip", "mult": 1.0, "kb": 40.0}, {"s": "thrust", "mult": 1.4, "kb": 150.0, "double": true, "last": true}],
		"pause": {"s": "flurry", "mult": 0.85, "kb": 50.0, "name": "Ay Dansı"}},
	# --- ağır silahlar
	"gurz": {"chain": [{"s": "windmill", "mult": 1.0, "kb": 280.0, "shock": true}, {"s": "down", "mult": 1.1, "kb": 220.0, "last": true}],
		"pause": {"s": "slam", "mult": 1.7, "kb": 320.0, "shock": true, "slam": true, "name": "Dağ Devirici"}},
	"civili_topuz": {"chain": [{"s": "windmill", "mult": 1.0, "kb": 260.0, "shock": true}, {"s": "down", "mult": 1.1, "kb": 200.0, "last": true}],
		"pause": {"s": "slam", "mult": 1.6, "kb": 300.0, "shock": true, "slam": true, "name": "Çivi Yağmuru"}},
	"dag_cekici": {"chain": [{"s": "windmill", "mult": 1.0, "kb": 320.0, "shock": true}, {"s": "uppercut_2h", "mult": 1.2, "kb": 240.0, "launch": 320.0, "last": true}],
		"pause": {"s": "slam", "mult": 1.9, "kb": 360.0, "shock": true, "slam": true, "name": "Dağ Yıkan"}},
	"savas_baltasi": {"chain": [{"s": "axe_hook", "mult": 1.0, "kb": 130.0}, {"s": "axe", "mult": 0.0, "kb": 0.0, "axe": true, "last": true}],
		"pause": {"s": "spin", "mult": 1.35, "kb": 180.0, "name": "Balta Çarkı"}},
	# --- sırıklar
	"teber": {"chain": [{"s": "pole_sweep", "mult": 1.0, "kb": 120.0}, {"s": "rise", "mult": 1.05, "kb": 40.0, "launch": 300.0}, {"s": "overhead_2h", "mult": 1.5, "kb": 260.0, "slam": true, "last": true}],
		"pause": {"s": "helicopter", "mult": 1.2, "kb": 200.0, "name": "Teber Çarkı"}},
	"erlik_tirpani": {"chain": [{"s": "reap", "mult": 1.0, "kb": 120.0}, {"s": "sweep_low", "mult": 1.1, "kb": 140.0}, {"s": "helicopter", "mult": 1.3, "kb": 180.0, "last": true}],
		"pause": {"s": "heavy", "mult": 1.7, "kb": 240.0, "slam": true, "name": "Ruh Biçen"}},
	"kargi": {"chain": [{"s": "pole_thrust", "mult": 1.0, "kb": 150.0}, {"s": "pole_thrust", "mult": 1.1, "kb": 170.0}, {"s": "pole_sweep", "mult": 1.3, "kb": 230.0, "last": true}],
		"pause": {"s": "lunge", "mult": 1.6, "kb": 220.0, "dash": 90.0, "name": "Süngü Akını"}},
	# --- çift bıçaklar / pençeler
	"ikiz_bicak": {"chain": [{"s": "horiz", "mult": 1.0, "kb": 45.0}, {"s": "back", "mult": 1.0, "kb": 45.0}, {"s": "rake", "mult": 0.9, "kb": 45.0}, {"s": "thrust", "mult": 1.3, "kb": 170.0, "double": true, "last": true}],
		"pause": {"s": "flurry", "mult": 0.8, "kb": 50.0, "name": "Gölge Dişleri"}},
	"kurt_pencesi": {"chain": [{"s": "rake", "mult": 1.0, "kb": 50.0}, {"s": "back", "mult": 1.0, "kb": 50.0}, {"s": "rise", "mult": 1.2, "kb": 60.0, "launch": 240.0, "last": true}],
		"pause": {"s": "flurry", "mult": 0.85, "kb": 60.0, "name": "Pençe Seli"}},
	# --- kırbaçlar
	"kement": {"chain": [{"s": "whip_crack", "mult": 1.0, "kb": 40.0, "whip": true}, {"s": "horiz", "mult": 1.1, "kb": 60.0, "whip": true, "last": true}],
		"pause": {"s": "spin", "mult": 1.2, "kb": 120.0, "whip": true, "name": "Kement Halkası"}},
	"od_kamcisi": {"chain": [{"s": "whip_crack", "mult": 1.0, "kb": 40.0, "whip": true}, {"s": "sweep_low", "mult": 1.1, "kb": 60.0, "whip": true, "last": true}],
		"pause": {"s": "spin", "mult": 1.2, "kb": 120.0, "whip": true, "name": "Od Halkası"}},
	# --- v7
	"yilan_kilici": {"chain": [{"s": "diag_down", "mult": 1.0, "kb": 90.0}, {"s": "reverse_grip", "mult": 1.0, "kb": 90.0}, {"s": "thrust", "mult": 1.3, "kb": 170.0, "last": true}],
		"pause": {"s": "twirl", "mult": 1.1, "kb": 100.0, "venom": true, "name": "Yılan Dansı"}},
	"kor_cekici": {"chain": [{"s": "windmill", "mult": 1.0, "kb": 280.0, "shock": true}, {"s": "overhead_2h", "mult": 1.2, "kb": 240.0, "slam": true, "last": true}],
		"pause": {"s": "slam", "mult": 1.7, "kb": 320.0, "shock": true, "slam": true, "name": "Kor Yağmuru"}},
	"ruzgar_kilici": {"chain": [{"s": "iai", "mult": 1.0, "kb": 70.0}, {"s": "back", "mult": 1.0, "kb": 70.0}, {"s": "horiz", "mult": 1.0, "kb": 80.0}, {"s": "cross_x", "mult": 1.2, "kb": 150.0, "last": true}],
		"pause": {"s": "helicopter", "mult": 1.2, "kb": 160.0, "name": "Kasırga Dansı"}},
	# --- v10
	"tulpar_mizragi": {"chain": [{"s": "pole_thrust", "mult": 1.0, "kb": 140.0, "dash": 30.0}, {"s": "pole_thrust", "mult": 1.05, "kb": 150.0, "dash": 30.0}, {"s": "pole_sweep", "mult": 1.1, "kb": 180.0}, {"s": "stab_heavy", "mult": 1.5, "kb": 260.0, "dash": 90.0, "last": true}],
		"pause": {"s": "helicopter", "mult": 1.3, "kb": 200.0, "name": "Tulpar Çarkı"}},
	"bori_hanceri": {"chain": [{"s": "reverse_grip", "mult": 1.0, "kb": 30.0}, {"s": "horiz", "mult": 1.0, "kb": 30.0}, {"s": "reverse_grip", "mult": 1.0, "kb": 30.0}, {"s": "rake", "mult": 1.0, "kb": 40.0}, {"s": "thrust", "mult": 1.5, "kb": 150.0, "double": true, "last": true}],
		"pause": {"s": "flurry", "mult": 0.9, "kb": 40.0, "name": "Börü Dişleri"}},
	"ikiz_balta": {"chain": [{"s": "axe_hook", "mult": 1.0, "kb": 120.0}, {"s": "diag_down", "mult": 1.0, "kb": 120.0, "double": true}, {"s": "windmill", "mult": 1.3, "kb": 220.0, "last": true}],
		"pause": {"s": "helicopter", "mult": 1.4, "kb": 200.0, "name": "Kanlı Çark"}},
	"kayin_asasi": {"chain": [{"s": "pole_sweep", "mult": 1.0, "kb": 220.0}, {"s": "twirl", "mult": 0.9, "kb": 200.0}, {"s": "overhead_2h", "mult": 1.3, "kb": 300.0, "last": true}],
		"pause": {"s": "helicopter", "mult": 1.2, "kb": 320.0, "name": "Kayın Fırtınası"}},
	"bozgun_kilici": {"chain": [{"s": "diag_down", "mult": 1.0, "kb": 180.0}, {"s": "horiz", "mult": 1.1, "kb": 200.0}, {"s": "overhead_2h", "mult": 1.4, "kb": 280.0, "slam": true, "last": true}],
		"pause": {"s": "cross_x", "mult": 1.3, "kb": 220.0, "name": "Bozgun Çaprazı"}},
}
const COMBOS_EXTRA := {}
const CHAIN_WINDOW := 0.28   # bu süre içinde basarsan zincir sürer
const PAUSE_WINDOW := 0.95   # 0.28 - 0.95 sn arası bekleyip basarsan bekleme bitirişi

## Ağır saldırılar: saldırı tuşu basılı tutulunca (hazırlık bitince HOLD_T kadar daha basılıysa) şarj başlar;
## bırakınca silahın özgün ağır vuruşu çıkar. Şarj HEAVY_MAX'a kadar hasarı 1.9 kata çıkarır.
const HOLD_T := 0.16
const HEAVY_MAX := 0.85
const HEAVIES := {
	"slash": {"s": "overhead_2h", "mult": 1.6, "kb": 260.0, "slam": true, "name": "Ağır Darbe"},
	"dual": {"s": "cross_x", "mult": 1.5, "kb": 150.0, "name": "Çapraz"},
	"heavy": {"s": "slam_2h", "mult": 1.8, "kb": 340.0, "shock": true, "slam": true, "name": "Yıkım"},
	"thrust": {"s": "stab_heavy", "mult": 1.9, "kb": 260.0, "dash": 60.0, "name": "Deliş"},
	"whip": {"s": "whip_crack", "mult": 1.6, "kb": 150.0, "whip": true, "name": "Şaklama"},
	"alp_kilici": {"s": "overhead_2h", "mult": 1.6, "kb": 260.0, "slam": true, "name": "Alp Darbesi"},
	"yildirim_kilici": {"s": "iai", "mult": 1.4, "kb": 60.0, "lightning": true, "name": "Yıldırım Hamlesi"},
	"pala": {"s": "reap", "mult": 1.6, "kb": 200.0, "name": "Kanlı Kanca"},
	"yatagan": {"s": "iai", "mult": 1.9, "kb": 180.0, "dash": 50.0, "name": "Yatağan Çekişi"},
	"ayaz_kilici": {"s": "overhead_2h", "mult": 1.6, "kb": 220.0, "slam": true, "name": "Buz Yarığı"},
	"ulu_kilic": {"s": "slam_2h", "mult": 2.0, "kb": 380.0, "shock": true, "slam": true, "name": "Ulu Yıkım"},
	"ruh_kilici": {"s": "cross_x", "mult": 1.5, "kb": 120.0, "wave": true, "name": "Ruh Çaprazı"},
	"ay_palasi": {"s": "helicopter", "mult": 1.5, "kb": 160.0, "name": "Dolunay"},
	"gurz": {"s": "slam_2h", "mult": 1.8, "kb": 340.0, "shock": true, "slam": true, "name": "Gürz Yıkımı"},
	"civili_topuz": {"s": "slam_2h", "mult": 1.8, "kb": 320.0, "shock": true, "slam": true, "name": "Çivi Çakışı"},
	"dag_cekici": {"s": "slam_2h", "mult": 2.1, "kb": 400.0, "shock": true, "slam": true, "name": "Dağ Çökertme"},
	"savas_baltasi": {"s": "overhead_2h", "mult": 1.8, "kb": 300.0, "slam": true, "name": "Balta Yarığı"},
	"teber": {"s": "sweep_low", "mult": 1.7, "kb": 240.0, "launch": 260.0, "name": "Diz Biçen"},
	"erlik_tirpani": {"s": "reap", "mult": 2.0, "kb": 240.0, "name": "Erlik'in Orağı"},
	"kargi": {"s": "stab_heavy", "mult": 1.9, "kb": 260.0, "dash": 70.0, "name": "Kargı Delişi"},
	"ikiz_bicak": {"s": "cross_x", "mult": 1.5, "kb": 150.0, "name": "İkiz Çapraz"},
	"kurt_pencesi": {"s": "rake", "mult": 1.7, "kb": 120.0, "name": "Kurt Tırmığı"},
	"kement": {"s": "whip_crack", "mult": 1.6, "kb": 150.0, "whip": true, "name": "Kement Şaklaması"},
	"od_kamcisi": {"s": "whip_crack", "mult": 1.6, "kb": 150.0, "whip": true, "name": "Od Şaklaması"},
	"yilan_kilici": {"s": "reap", "mult": 1.6, "kb": 200.0, "venom": true, "name": "Zehir Orağı"},
	"kor_cekici": {"s": "slam_2h", "mult": 1.9, "kb": 360.0, "shock": true, "slam": true, "name": "Cehennem Çakışı"},
	"ruzgar_kilici": {"s": "cross_x", "mult": 1.5, "kb": 140.0, "name": "Yel Çaprazı"},
	"tulpar_mizragi": {"s": "stab_heavy", "mult": 2.0, "kb": 300.0, "dash": 160.0, "name": "Tulpar Akını"},
	"bori_hanceri": {"s": "cross_x", "mult": 1.7, "kb": 120.0, "name": "Gölge Çaprazı"},
	"ikiz_balta": {"s": "slam_2h", "mult": 1.9, "kb": 320.0, "shock": true, "slam": true, "name": "İkiz Yarık"},
	"kayin_asasi": {"s": "pole_sweep", "mult": 1.7, "kb": 420.0, "name": "Kayın Savuruşu"},
	"bozgun_kilici": {"s": "slam_2h", "mult": 2.0, "kb": 340.0, "shock": true, "slam": true, "name": "Bozgun Yarığı"},
}
## Silaha özgü görsel: iz genişliği, iz rengi, darbe animasyonu (PVFX) ve ek parçacık
const WFX := {
	"alp_kilici": {"trail": 1.0, "hit": "crescent_slash", "hit_scale": 0.6},
	"yildirim_kilici": {"trail": 0.8, "col": Color(0.6, 0.85, 1.0), "hit": "electric_impact", "hit_scale": 0.6, "extra": "ghost"},
	"pala": {"trail": 1.1, "col": Color(1.0, 0.62, 0.5), "hit": "crescent_slash", "hit_scale": 0.55, "extra": "blood"},
	"yatagan": {"trail": 0.7, "col": Color(0.95, 0.95, 1.0), "extra": "ghost"},
	"ayaz_kilici": {"trail": 1.0, "col": Color(0.65, 0.9, 1.0), "hit": "frost_nova", "hit_scale": 0.5, "extra": "frost"},
	"ulu_kilic": {"trail": 2.0, "hit": "mass_release", "hit_scale": 0.8, "extra": "dust"},
	"ruh_kilici": {"trail": 1.2, "col": Color(0.5, 1.0, 0.9), "hit": "spectral_bloom", "hit_scale": 0.6, "extra": "soul"},
	"ay_palasi": {"trail": 0.8, "col": Color(0.8, 0.9, 1.0), "hit": "arcane_parry", "hit_scale": 0.5, "extra": "ghost"},
	"gurz": {"trail": 1.6, "col": Color(1.0, 0.85, 0.6), "hit": "resonant_break", "hit_scale": 0.7, "extra": "dust"},
	"civili_topuz": {"trail": 1.6, "col": Color(1.0, 0.8, 0.6), "hit": "resonant_break", "hit_scale": 0.8, "extra": "blood"},
	"dag_cekici": {"trail": 1.8, "col": Color(1.0, 0.8, 0.55), "hit": "resonant_break", "hit_scale": 1.0, "extra": "dust"},
	"savas_baltasi": {"trail": 1.3, "hit": "resonant_break", "hit_scale": 0.6, "extra": "blood"},
	"teber": {"trail": 1.5, "hit": "crescent_slash", "hit_scale": 0.8},
	"erlik_tirpani": {"trail": 1.5, "col": Color(0.7, 0.45, 1.0), "hit": "spectral_bloom", "hit_scale": 0.55, "extra": "soul"},
	"kargi": {"trail": 0.6, "hit": "solar_shrapnel", "hit_scale": 0.5},
	"ikiz_bicak": {"trail": 0.6, "hit": "crescent_slash", "hit_scale": 0.4},
	"kurt_pencesi": {"trail": 0.6, "col": Color(1.0, 0.6, 0.5), "hit": "crescent_slash", "hit_scale": 0.45, "extra": "blood"},
	"kement": {"trail": 0.5, "hit": "tether_catch", "hit_scale": 0.6},
	"od_kamcisi": {"trail": 0.7, "col": Color(1.0, 0.6, 0.3), "hit": "ember_jet", "hit_scale": 0.6, "extra": "fire"},
	"yilan_kilici": {"trail": 0.9, "col": Color(0.55, 1.0, 0.45), "hit": "acid_splash", "hit_scale": 0.45, "extra": "poison"},
	"kor_cekici": {"trail": 1.6, "col": Color(1.0, 0.55, 0.25), "hit": "warm_explosion", "hit_scale": 0.5, "extra": "fire"},
	"ruzgar_kilici": {"trail": 0.8, "col": Color(0.78, 0.95, 1.0), "hit": "leaf_gust", "hit_scale": 0.5, "extra": "ghost"},
	"tulpar_mizragi": {"trail": 0.7, "col": Color(1.0, 0.9, 0.6), "hit": "solar_shrapnel", "hit_scale": 0.6, "extra": "ghost"},
	"bori_hanceri": {"trail": 0.5, "col": Color(0.85, 0.75, 1.0), "hit": "crescent_slash", "hit_scale": 0.4, "extra": "blood"},
	"ikiz_balta": {"trail": 1.2, "col": Color(1.0, 0.55, 0.45), "hit": "resonant_break", "hit_scale": 0.6, "extra": "blood"},
	"kayin_asasi": {"trail": 1.4, "col": Color(0.75, 1.0, 0.7), "hit": "leaf_gust", "hit_scale": 0.7, "extra": "dust"},
	"bozgun_kilici": {"trail": 1.6, "col": Color(1.0, 0.4, 0.8), "hit": "void_implosion", "hit_scale": 0.5, "extra": "soul"},
}
## Silah ses sınıfı: savuruş (savur_<sınıf>) ve darbe (darbe_<...>) sesleri gerçek kayıt katmanlarından seçilir
const WSND := {"alp_kilici": "kilic", "pala": "kilic", "yatagan": "kilic", "ayaz_kilici": "kilic", "yilan_kilici": "kilic", "ruzgar_kilici": "kilic",
	"yildirim_kilici": "katana", "ulu_kilic": "dev", "erlik_tirpani": "dev", "gurz": "cekic", "civili_topuz": "cekic", "dag_cekici": "cekic",
	"kor_cekici": "cekic", "savas_baltasi": "balta", "teber": "balta", "kargi": "sirik", "ikiz_bicak": "bicak", "kurt_pencesi": "bicak",
	"ay_palasi": "bicak", "kement": "kirbac", "od_kamcisi": "kirbac", "ruh_kilici": "ruh",
	"tulpar_mizragi": "sirik", "bori_hanceri": "bicak", "ikiz_balta": "balta", "kayin_asasi": "sirik", "bozgun_kilici": "dev"}
## İki elle tutulan silahlar: arka el kabzanın gerisine (bıçak yönünde negatif ofset) IK ile yerleşir
const TWO_HANDED := {"ulu_kilic": -7.0, "dag_cekici": -9.0, "kor_cekici": -8.0, "gurz": -6.0, "civili_topuz": -6.0, "teber": -13.0, "kargi": -14.0,
	"erlik_tirpani": -12.0, "savas_baltasi": -7.0, "tulpar_mizragi": -15.0, "kayin_asasi": -14.0, "bozgun_kilici": -8.0}

var anim: SpriteAnim
var weapon: Sprite2D
var shield_spr: Sprite2D
var cshape: CollisionShape2D
var facing := 1
var coyote := 0.0
var jump_buf := 0.0
var air_jumps := 1
var jumping := false
var roll_t := 0.0
var roll_cd := 0.0
var inv_t := 0.0
var hurt_t := 0.0
var drop_t := 0.0
var drink_t := 0.0
var land_t := 0.0
var dead := false
var atk: Dictionary = {}
var combo_step := 0
var combo_window := 0.0
var melee_buf := 0.0
var aim_t := -1.0
var throw_t := -1.0
var thrown := false
var block_t := -1.0
var cd := {"melee": 0.0, "second": 0.0, "g1": 0.0, "g2": 0.0}
var cd_max := {"melee": 1.0, "second": 1.0, "g1": 1.0, "g2": 1.0}
## Dead Cells gibi iki silah yuvası: J ("melee") ve K ("second") yuvasına her tür silah/kalkan konabilir.
## Yakın dövüş rolü ve ikincil rol (yay, fırlatma, büyü, kalkan) her karede yuvalardaki eşyalardan çözülür.
var mel_slot := "melee"
var sec_slot := "second"
var mel_act := "saldiri1"
var sec_act := "saldiri2"
var _want_mel := ""
const SLOT_ACT := {"melee": "saldiri1", "second": "saldiri2"}
var kut := 0.0
var spirit_t := 0.0
var ward := false
var momentum := 0
var momentum_t := 0.0
var sure_crits := 0
var rolled_t := 0.0
var level: Node
var crouched := false
var crouch_hold := false   # S basılı: isteyerek çömelme (çömelirken saldırı / yay)
var combo_n := 0            # kesintisiz isabet sayısı (2,4 sn içinde vurmaya devam et)
var combo_t := 0.0
var combo_best := 0
var combo_rank := 0
var air_hang := 0.0         # havada isabet: kısa asılı kalma (hava kombosu)
var mantle_t := 0.0         # kenara tutunup çıkma
var _mantle_a := Vector2.ZERO
var _mantle_b := Vector2.ZERO
var _prev_vy := 0.0
const COMBO_RANKS := [[5, "ER", Color(0.9, 0.9, 0.95)], [12, "ALP", Color(0.6, 0.95, 1.0)], [22, "BAHADIR", Color(1.0, 0.85, 0.4)],
	[35, "HAN", Color(1.0, 0.55, 0.3)], [55, "DESTAN", Color(1.0, 0.35, 0.6)]]
var sprint := false        # Shift basılı tutuluyor: koşu
var _roll_hold := 0.0
var _haz_t := 0.0          # tehlike karosu hasar sayacı
var on_ice := false
var charge_t := -1.0  # Yıldırım Kılıcı: basılı tutma süresi
var charge_fx: AnimFX
var _heavy_fx: AnimFX  # ağır saldırı şarj halkası
var axe_out := false
var regen_t := 0.0
var revive := false
var grabbed_by: Node
var mash := 0
# Bozkurt biçimi
var wolf_t := 0.0
var wolf_anim: SpriteAnim
var wolf_atk: Dictionary = {}
var wolf_step := 0
var wolf_since := 9.0
var howl_cd := 0.0
var pounce_t := 0.0
var wolf_hit: Array = []
var poison_t := 0.0
var _poison_tick := 0.0
var last_safe := Vector2.ZERO
var _safe_t := 0.0
var _still_t := 0.0
var _embed_t := 0.0
var _prev_pos := Vector2.ZERO
# his (feel) durumu
var vis_scale := Vector2.ONE
var vis_lean := 0.0
var _was_floor := true
var _fall_peak := 0.0
var _dust_t := 0.0
var _ghost_t := 0.0
var _skid := false
var _trail: WeaponTrail
var _trail_prev: Array = []
# kol iskeleti
var arm_root: Node2D
var arm_upper: Sprite2D
var arm_fore: Sprite2D
var arm_fist: Sprite2D
var arm_root_b: Node2D
var arm_upper_b: Sprite2D
var arm_fore_b: Sprite2D
var arm_fist_b: Sprite2D
var wind_n := 0  # Rüzgâr Kılıcı: üçüncü kesik sayacı
var arm_meta: Dictionary = {}
var _hand_local := Vector2.ZERO
## Yay: kiriş + yaydaki ok çizimi (kol iskeletinin içinde, silahın üstünde)
var bow_str: BowString
var bow_rel_t := 0.0        # bırakış sonrası takip: kiriş titrer, yay geri teper
var _bow_full := false
var _bow_nock := Vector2.ZERO
var _bow_nock_ok := false
var _bow_tip_cache: Dictionary = {}
const BOW_REL := 0.24
const BAKED_ARROW_BOWS := ["saganak_yayi", "tufan_yayi", "od_oklari"]


class BowString extends Node2D:
	## Piksel kiriş: uçlardan geri çekilen gez noktasına iki düz çizgi; isteğe bağlı yaydaki ok.
	var top := Vector2.ZERO
	var bot := Vector2.ZERO
	var nock := Vector2.ZERO
	var dir := 1
	var arrow_on := false
	var arrow_head := Color(0.88, 0.92, 0.98)
	var fletch := Color(0.85, 0.25, 0.2)
	var glow := 0.0
	var str_col := Color(0.93, 0.88, 0.75)

	func _seg(a: Vector2, b: Vector2, col: Color) -> void:
		var n := maxi(1, int(ceilf(maxf(absf(b.x - a.x), absf(b.y - a.y)))))
		for i in n + 1:
			var q := a.lerp(b, float(i) / n).floor()
			draw_rect(Rect2(q, Vector2.ONE), col)

	func _draw() -> void:
		_seg(top, nock, str_col)
		_seg(nock, bot, str_col)
		if arrow_on:
			var tail := nock + Vector2(-dir * 1, 0)
			var head := nock + Vector2(dir * 21, 0)
			_seg(tail, head - Vector2(dir * 3, 0), Color(0.79, 0.6, 0.37))
			# uç
			_seg(head - Vector2(dir * 3, 0), head, arrow_head)
			draw_rect(Rect2((head - Vector2(dir * 2, 1)).floor(), Vector2.ONE), arrow_head)
			draw_rect(Rect2((head - Vector2(dir * 2, -1)).floor(), Vector2.ONE), arrow_head)
			# tüyler
			draw_rect(Rect2((tail + Vector2(dir * 1, -1)).floor(), Vector2(2, 1)), fletch)
			draw_rect(Rect2((tail + Vector2(dir * 1, 1)).floor(), Vector2(2, 1)), Color(0.95, 0.93, 0.88))
			if glow > 0.0:
				var g := Color(1.0, 0.92, 0.55, glow)
				draw_rect(Rect2((head - Vector2(1, 1)).floor(), Vector2(3, 3)), Color(g, glow * 0.5))
				draw_rect(Rect2((head + Vector2(dir * 1, -3)).floor(), Vector2(1, 7)), Color(g, glow * 0.7))
				draw_rect(Rect2((head + Vector2(dir * 1 - 3, 0)).floor(), Vector2(7, 1)), Color(g, glow * 0.7))
var _blade_local := Vector2.RIGHT
var since_atk := 9.0       # son saldırının bitişinden beri geçen süre (zincir / bekleme ayrımı)
var last_step := -1
var _pause_ready_fx := false
var cast_t := 0.0


func _ready() -> void:
	add_to_group("oyuncu")
	collision_layer = Game.LAYER_PLAYER
	collision_mask = Game.LAYER_WORLD | Game.LAYER_PLATFORM
	floor_snap_length = 6.0
	floor_max_angle = deg_to_rad(50)
	var shape := RectangleShape2D.new()
	shape.size = Vector2(12, 40)
	cshape = CollisionShape2D.new()
	cshape.shape = shape
	cshape.position = Vector2(0, -20)
	add_child(cshape)
	anim = SpriteAnim.new()
	add_child(anim)
	anim.setup("bengu")
	anim.play("idle")
	wolf_anim = SpriteAnim.new()
	add_child(wolf_anim)
	wolf_anim.setup("bengu_kurt")
	wolf_anim.visible = false
	wolf_anim.z_index = 3
	# Ön kol iskeleti: üst kol -> ön kol -> silah -> yumruk (yumruk silahın kabzasını örter).
	# anim düğümünün çocuğu: gövdenin ezilme/esneme ve eğilmesini birebir izler.
	arm_meta = Data.load_json("res://assets/sprites/bengu_kol.json")
	var arm_tex := Data.canvas_tex("res://assets/sprites/bengu_kol.png", "")
	var am := ShaderMaterial.new()
	am.shader = Game.toon_shader
	arm_root = Node2D.new()
	arm_root.visible = false
	anim.add_child(arm_root)
	var cw: float = float(arm_meta["cell"][0])
	var ch: float = float(arm_meta["cell"][1])
	var pv := Vector2(float(arm_meta["pivot"][0]), float(arm_meta["pivot"][1]))
	var fpv := Vector2(float(arm_meta["fist_pivot"][0]), float(arm_meta["fist_pivot"][1]))
	arm_upper = _arm_piece(arm_tex, Rect2(0, 0, cw, ch), pv, am)
	arm_fore = _arm_piece(arm_tex, Rect2(cw, 0, cw, ch), pv, am)
	weapon = Sprite2D.new()
	weapon.texture = Data.weapon_tex
	weapon.region_enabled = true
	weapon.centered = false
	var wm := ShaderMaterial.new()
	wm.shader = Game.toon_shader
	weapon.material = wm
	weapon.visible = false
	arm_root.add_child(weapon)
	shield_spr = weapon.duplicate()
	shield_spr.material = wm
	arm_root.add_child(shield_spr)
	bow_str = BowString.new()
	bow_str.visible = false
	arm_root.add_child(bow_str)
	arm_fist = _arm_piece(arm_tex, Rect2(cw * 2, 0, cw, ch), fpv, am)
	# arka kol: gövdenin arkasında (z -1), iki elli silahlarda kabzaya IK ile uzanır
	arm_root_b = Node2D.new()
	arm_root_b.z_index = -1
	arm_root_b.visible = false
	anim.add_child(arm_root_b)
	var parts: Array = arm_meta.get("parts", [])
	if parts.size() >= 6:
		arm_upper_b = _arm_piece_in(arm_root_b, arm_tex, Rect2(cw * 3, 0, cw, ch), pv, am)
		arm_fore_b = _arm_piece_in(arm_root_b, arm_tex, Rect2(cw * 4, 0, cw, ch), pv, am)
		arm_fist_b = _arm_piece_in(arm_root_b, arm_tex, Rect2(cw * 5, 0, cw, ch), fpv, am)
	anim.finished.connect(_on_anim_finished)


func _arm_piece_in(root_n: Node2D, tex: Texture2D, region: Rect2, pivot: Vector2, mat: Material) -> Sprite2D:
	var sp := Sprite2D.new()
	sp.texture = tex
	sp.region_enabled = true
	sp.region_rect = region
	sp.centered = false
	sp.offset = -pivot
	sp.material = mat
	root_n.add_child(sp)
	return sp


func _ik2(sh: Vector2, target: Vector2, l1: float, l2: float) -> Array:
	## İki kemikli analitik IK: dirsek aşağı-geriye sarkar. [dirsek, el]
	var d := target - sh
	var dist := clampf(d.length(), absf(l1 - l2) + 0.5, l1 + l2 - 0.5)
	var dir := d.normalized() if d.length() > 0.01 else Vector2(0, 1)
	var cosang := clampf((l1 * l1 + dist * dist - l2 * l2) / (2.0 * l1 * dist), -1.0, 1.0)
	var a := acos(cosang)
	var e1 := sh + dir.rotated(a) * l1
	var e2 := sh + dir.rotated(-a) * l1
	var e := e1 if (e1.y - facing * e1.x * 0.3) > (e2.y - facing * e2.x * 0.3) else e2
	return [e, sh + dir * dist]


func _update_back_arm(it: Dictionary, h: Vector2, bd: Vector2, is_shield: bool) -> void:
	## Arka kol: iki elli silahta kabzaya uzanır; yoksa gövde animasyonunun kaydettiği açılarla sürülür.
	if arm_upper_b == null:
		return
	var sh_b: Variant = anim.anchor("sh_b")
	if sh_b == null:
		arm_root_b.visible = false
		return
	arm_root_b.visible = true
	var l1 := float(arm_meta.get("upper_len", 8.5))
	var l2 := float(arm_meta.get("fore_len", 8.0))
	var e: Vector2
	var hb: Vector2
	var iid: String = it.get("id", "")
	if it.get("kind", "") == "bow" and _bow_nock_ok and (aim_t >= 0.0 or bow_rel_t > 0.0):
		# yay: arka el gezde; bırakınca geriye savrulur
		var follow := Vector2(-facing * 5.0, -2.0) * clampf(bow_rel_t / BOW_REL, 0.0, 1.0) if aim_t < 0.0 else Vector2.ZERO
		var r2 := _ik2(sh_b, _bow_nock + follow, l1, l2)
		e = r2[0]
		hb = r2[1]
	elif TWO_HANDED.has(iid) and not is_shield and not atk.is_empty():
		var target: Vector2 = h + bd.normalized() * float(TWO_HANDED[iid])
		var r := _ik2(sh_b, target, l1, l2)
		e = r[0]
		hb = r[1]
	else:
		var ab := _frame_arm_b()
		e = sh_b + Vector2(sin(ab.x) * facing, cos(ab.x)) * l1
		hb = e + Vector2(sin(ab.x + ab.y) * facing, cos(ab.x + ab.y)) * l2
	_place_bone(arm_upper_b, sh_b, e, l1)
	_place_bone(arm_fore_b, e, hb, l2)
	arm_fist_b.position = hb
	arm_fist_b.rotation = arm_fore_b.rotation
	arm_fist_b.flip_h = facing < 0


func _frame_arm_b() -> Vector2:
	var a: Dictionary = anim.meta["anims"].get(anim.anim, {})
	var data: Array = a.get("data", [])
	if anim.frame < data.size():
		var d: Dictionary = data[anim.frame]
		if d.has("arm_b"):
			return Vector2(float(d["arm_b"][0]), float(d["arm_b"][1]))
	return Vector2(0.2, 0.45)


func _arm_piece(tex: Texture2D, region: Rect2, pivot: Vector2, mat: Material) -> Sprite2D:
	var sp := Sprite2D.new()
	sp.texture = tex
	sp.region_enabled = true
	sp.region_rect = region
	sp.centered = false
	sp.offset = -pivot
	sp.material = mat
	arm_root.add_child(sp)
	return sp


# ------------------------------------------------------------------ yardımcılar
func slot(s: String) -> Dictionary:
	if s == "":
		return {}
	return Game.run["slots"].get(s, {})


static func is_melee_item(it: Dictionary) -> bool:
	return it.get("cat", "") == "weapons" and not (it.get("kind", "") in ["bow", "throw", "magic"])


static func is_second_item(it: Dictionary) -> bool:
	return it.get("cat", "") == "shields" or (it.get("cat", "") == "weapons" and it.get("kind", "") in ["bow", "throw", "magic"])


func _resolve_roles() -> void:
	## Hangi yuva yakın dövüş, hangisi ikincil? İki yakın silah varsa basılan tuşun silahı kullanılır
	## (saldırı sürerken kilitli, bitince geçilir); iki yay/kalkan varsa da aynı.
	var a := slot("melee")
	var b := slot("second")
	var mels: Array = []
	var secs: Array = []
	if is_melee_item(a):
		mels.append("melee")
	if is_melee_item(b):
		mels.append("second")
	if is_second_item(a):
		secs.append("melee")
	if is_second_item(b):
		secs.append("second")
	# yakın dövüş rolü
	if mels.is_empty():
		if atk.is_empty():
			mel_slot = ""
	elif mels.size() == 1:
		if atk.is_empty() or mel_slot == "":
			mel_slot = mels[0]
	else:
		for sl in mels:
			if Input.is_action_just_pressed(SLOT_ACT[sl]) and sl != mel_slot:
				if atk.is_empty():
					mel_slot = sl
					last_step = -1
					since_atk = 99.0
				else:
					_want_mel = sl
		if atk.is_empty() and _want_mel != "":
			mel_slot = _want_mel
			_want_mel = ""
			last_step = -1
			since_atk = 99.0
		if not (mel_slot in mels):
			mel_slot = mels[0]
	# ikincil rol (yay gerili / kalkan kalkık / fırlatma sürerken kilitli)
	var busy2 := aim_t >= 0.0 or block_t >= 0.0 or throw_t >= 0.0
	if secs.is_empty():
		if not busy2:
			sec_slot = ""
	elif secs.size() == 1:
		if not busy2:
			sec_slot = secs[0]
	elif not busy2:
		for sl in secs:
			if Input.is_action_just_pressed(SLOT_ACT[sl]):
				sec_slot = sl
		if not (sec_slot in secs):
			sec_slot = secs[0]
	mel_act = SLOT_ACT.get(mel_slot, "")
	sec_act = SLOT_ACT.get(sec_slot, "")


func on_equip() -> void:
	## Yuva değişti: süren saldırı / nişan / siper bırakılır, roller yeniden çözülür.
	_end_trail()
	atk = {}
	aim_t = -1.0
	block_t = -1.0
	throw_t = -1.0
	charge_t = -1.0
	last_step = -1
	_want_mel = ""
	_resolve_roles()


func hurt_rect() -> Rect2:
	if wolf_t > 0.0:
		return Rect2(global_position + Vector2(-15, -26), Vector2(30, 26))
	if crouched:
		return Rect2(global_position + Vector2(-6, -20), Vector2(12, 20))
	return Rect2(global_position + Vector2(-6, -40), Vector2(12, 40))


func center() -> Vector2:
	return global_position + Vector2(0, -20)


func max_hp() -> float:
	return float(Game.run["max_hp"])


func heal(v: float) -> void:
	var before := float(Game.run["hp"])
	Game.run["hp"] = minf(max_hp(), before + v)
	if Game.run["hp"] > before:
		FX.number(center() + Vector2(0, -12), Game.run["hp"] - before, false, Color(0.55, 1.0, 0.55))


func add_kut(v: float) -> void:
	var m := 1.12 if slot(mel_slot).get("material", "") == "tunc" else 1.0
	if Game.has_lutuf("kayra"):
		m *= 2.0
	m *= 1.0 + 0.2 * Game.umay_level("kut_hizi")
	kut = minf(100.0, kut + v * m)


func shove(v: Vector2) -> void:
	## Düşman itişi (kalkan darbesi, hücum): hız verilir, kısa sendeleme
	velocity = v
	hurt_t = maxf(hurt_t, 0.18)
	vis_scale = Vector2(0.85, 1.12)


func _bozgun_shards(e: Node, it: Dictionary) -> void:
	## Bozgun Kılıcı: öldürülen düşmandan üç bozgun kristali yakındaki düşmanlara fırlar
	var targets: Array = []
	for o in get_tree().get_nodes_in_group("dusman"):
		if o != e and is_instance_valid(o) and not o.dead and o.center().distance_to(e.center()) < 220.0:
			targets.append(o)
	FX.anim("void_implosion", e.center(), 0.0, 0.8, Color(1.0, 0.4, 0.8))
	for k in 3:
		var p := Projectile.new()
		p.team = "p"
		p.kind = "wave"
		p.position = e.center()
		var tgt: Vector2 = targets[k % targets.size()].center() if not targets.is_empty() else e.center() + Vector2(cos(k * 2.1) * 80, -60)
		p.velocity = (tgt - e.center()).normalized() * 300.0
		p.homing = 2.0
		p.pierce = 1
		p.life = 1.2
		p.trail_col = Color(1.0, 0.4, 0.8)
		p.on_hit = func(o: Node) -> void:
			_deal(o, float(it["dmg"]) * 0.6, it, {"kb": 80.0, "dir": signf(p.velocity.x), "sfx_done": true})
		level.add_projectile(p)


func _tengri_chain(e: Node, d: float, it: Dictionary) -> void:
	## Tengri'nin Yıldırımı: darbe yakındaki bir düşmana şimşekle sıçrar
	var best: Node = null
	var bd := 130.0
	for o in get_tree().get_nodes_in_group("dusman"):
		if o == e or not is_instance_valid(o) or o.dead:
			continue
		var dd: float = o.center().distance_to(e.center())
		if dd < bd:
			bd = dd
			best = o
	if best == null:
		return
	FX.lightning(e.center(), best.center(), Color(0.7, 0.85, 1.0))
	FX.anim("electric_impact", best.center(), 0.0, 0.7, Color(0.7, 0.85, 1.0))
	Ses.play("yildirim", -8.0, 1.3)
	best.take_hit(d, {"kb": 60.0, "dir": signf(best.center().x - e.center().x), "stun": 0.3, "zincir": true, "sfx_done": true})


func _corner_correct() -> void:
	## Köşe düzeltme: zıplarken baş bir köşeye takılırsa 1-7 px yana kaydırıp zıplamayı sürdür
	if _prev_vy >= -40.0 or not is_on_ceiling():
		return
	for d in [2, 4, 6, 8]:
		for sgn in [1, -1]:
			var xf := global_transform.translated(Vector2(sgn * d, 0))
			if not test_move(global_transform, Vector2(sgn * d, 0)) and not test_move(xf, Vector2(0, -6)):
				global_position.x += sgn * d
				velocity.y = _prev_vy
				return


func _try_mantle(dir: float) -> void:
	## Kenara tutunma: havada, duvara doğru basılı, eller kenar hizasındaysa otomatik tırmanış
	if is_on_floor() or mantle_t > 0.0 or roll_t > 0.0 or not atk.is_empty() or aim_t >= 0.0 or level == null:
		return
	if dir == 0 or int(signf(dir)) != facing or velocity.y < -80.0:
		return
	var fx := global_position.x + facing * 10.0
	var tx := int(floor(fx / 24.0))
	var top := -1
	for ty in range(int(floor((global_position.y - 50.0) / 24.0)), int(floor((global_position.y - 10.0) / 24.0)) + 1):
		if level.cell(tx, ty) == 1 and level.cell(tx, ty - 1) == 0 and level.cell(tx, ty - 2) == 0:
			top = ty
			break
	if top < 0:
		return
	var ledge_y := top * 24.0
	if ledge_y < global_position.y - 52.0 or ledge_y > global_position.y - 8.0:
		return
	if level.solid_at(Vector2(global_position.x, ledge_y - 30.0)):
		return
	_mantle_a = global_position
	_mantle_b = Vector2(tx * 24.0 + 12.0 - facing * 4.0, ledge_y - 0.5)
	mantle_t = 0.16
	jumping = false
	Ses.play("zipla", -12.0, 0.8)


func _hazard_check(delta: float) -> void:
	## Tehlike karoları: diken/zehir/lav üstünde durunca hasar + durum; 0,7 sn'de bir
	_haz_t -= delta
	if level == null or not level.has_method("hazard_at") or dead or roll_t > 0.0:
		return
	var hz: String = level.hazard_at(global_position + Vector2(0, -4))
	if hz == "":
		hz = level.hazard_at(global_position + Vector2(0, 2))
	if hz == "" or hz == "buz":
		return
	if _haz_t > 0.0:
		return
	_haz_t = 0.7
	var frac := 0.14 if hz == "lav" else (0.08 if hz == "diken" else 0.06)
	if take_hit(max_hp() * frac, null, null, true):
		velocity.y = -300.0
		velocity.x = -facing * 120.0
		match hz:
			"lav":
				FX.fire(global_position, 10, 0.4, 8.0)
				FX.anim("ember_jet", global_position, -PI / 2.0, 0.9, Color(1.0, 0.6, 0.25))
				FX.text(center() + Vector2(0, -34), "LAV!", Color(1.0, 0.6, 0.3), 9)
			"zehir":
				apply_poison(3.0)
				FX.anim("acid_splash", global_position, 0.0, 0.9, Color(0.6, 1.0, 0.4))
			"diken":
				FX.blood(global_position, Vector2.UP, Color(0.75, 0.1, 0.12), 8)
				FX.text(center() + Vector2(0, -34), "diken", Color(1.0, 0.5, 0.5), 8)


func weapon_color(it: Dictionary) -> Color:
	var col := Color(1.0, 0.92, 0.75)
	if it.is_empty():
		return col
	var m: Dictionary = Data.material_def(it.get("material", "demir"))
	if float(m.get("glow", 0)) > 0.0:
		col = Color.from_hsv(float(m["hue"]) / 360.0, 0.55, 1.0)
	elif m.has("hue"):
		col = col.lerp(Color.from_hsv(float(m["hue"]) / 360.0, 0.35, 1.0), 0.35)
	return col


func _head_blocked() -> bool:
	## Ayakta durunca başın gireceği yer katı mı? (tünel / alçak geçit)
	if level == null:
		return false
	# ayakta gövde 40 px: 21-40 px arası tamamı boş olmalı (tavan tam karo sınırındaysa da yakala)
	for dx in [-5.5, 0.0, 5.5]:
		for dy in [-22.0, -30.0, -39.5]:
			if level.solid_at(global_position + Vector2(dx, dy)):
				return true
	return false


func _overlapping() -> bool:
	## Gövde şu an bir katı karonun içinde mi? (gömülme denetimi)
	var q := PhysicsShapeQueryParameters2D.new()
	q.shape = cshape.shape
	q.transform = Transform2D(0.0, global_position + cshape.position)
	q.collision_mask = Game.LAYER_WORLD
	q.margin = -1.0
	return not get_world_2d().direct_space_state.intersect_shape(q, 1).is_empty()


func _set_crouch(v: bool) -> void:
	if crouched == v:
		return
	crouched = v
	var sh := cshape.shape as RectangleShape2D
	sh.size = Vector2(12, 20) if v else Vector2(12, 40)
	cshape.position = Vector2(0, -10) if v else Vector2(0, -20)


# ------------------------------------------------------------------ ana döngü
func _physics_process(delta: float) -> void:
	# düşük can: kalp atışı ve boğuk ses (Ses.low_hp 0..1)
	Ses.low_hp(0.0 if dead else clampf(1.0 - float(Game.run["hp"]) / float(Game.run["max_hp"]) / 0.3, 0.0, 1.0))
	if dead:
		velocity.y = minf(velocity.y + GRAV * delta, MAX_FALL)
		velocity.x = move_toward(velocity.x, 0.0, 600 * delta)
		move_and_slide()
		_feel(delta, 0.0)
		return
	if grabbed_by != null:
		if not is_instance_valid(grabbed_by) or grabbed_by.dead:
			release_grab(Vector2(-facing * 120.0, -120.0))
		else:
			# yakalandın: tuşlara basarak kurtul (4 basış)
			velocity = Vector2.ZERO
			atk = {}
			_end_trail()
			anim.play("hurt")
			anim.set_facing(facing)
			vis_scale = Vector2(1.0 + 0.08 * sin(Time.get_ticks_msec() / 40.0), 1.0 - 0.08 * sin(Time.get_ticks_msec() / 40.0))
			if Input.is_action_just_pressed("saldiri1") or Input.is_action_just_pressed("zipla") or Input.is_action_just_pressed("yuvarlan"):
				mash += 1
				FX.sparks(center(), Vector2.UP, Color(1, 0.9, 0.6), 3, 90.0)
				if mash >= 4:
					var g := grabbed_by
					release_grab(Vector2(-facing * 160.0, -200.0))
					if g.has_method("stun"):
						g.stun(1.2)
					FX.text(center() + Vector2(0, -34), "KURTULDUN", Color(1.0, 0.95, 0.7), 9)
			_feel(delta, 0.0)
			return
	if poison_t > 0.0:
		poison_t -= delta
		_poison_tick -= delta
		var pt := Time.get_ticks_msec() / 1000.0
		anim.set_tint(Color(1, 1, 1).lerp(Color(0.75, 1.3, 0.65), 0.4 + 0.2 * sin(pt * 7.0)))
		if Engine.get_physics_frames() % 12 == 0:
			FX.bubbles(center(), 1)
		if _poison_tick <= 0.0:
			_poison_tick = 0.6
			Game.run["hp"] = maxf(1.0, float(Game.run["hp"]) - 2.0)
			FX.number(center(), 2.0, false, Color(0.55, 1.0, 0.35))
		if poison_t <= 0.0:
			anim.set_tint(Color(1, 1, 1))
	if wolf_t > 0.0:
		_wolf_process(delta)
		return
	if combo_n > 0:
		combo_t -= delta
		if combo_t <= 0.0:
			combo_break("")
	if mantle_t > 0.0:
		# kenara tutunup çık: kısa, kavisli kayma (önce yukarı, sonra öne)
		mantle_t -= delta
		var k := 1.0 - clampf(mantle_t / 0.16, 0.0, 1.0)
		var up := clampf(k * 1.6, 0.0, 1.0)
		var fw := clampf((k - 0.35) / 0.65, 0.0, 1.0)
		global_position = Vector2(lerpf(_mantle_a.x, _mantle_b.x, fw), lerpf(_mantle_a.y, _mantle_b.y, up))
		velocity = Vector2.ZERO
		anim.show_frame("land", 0 if k < 0.6 else 1)
		vis_scale = Vector2(0.9, 1.1).lerp(Vector2.ONE, k)
		_feel(delta, 0.0)
		if mantle_t <= 0.0:
			vis_scale = Vector2(1.15, 0.88)
			FX.dust(global_position, Vector2(-facing, -0.5), 3, 0.24)
		return
	air_hang -= delta
	for k in cd.keys():
		cd[k] = maxf(0.0, cd[k] - delta)
	bow_rel_t -= delta
	coyote -= delta
	jump_buf -= delta
	roll_cd -= delta
	inv_t -= delta
	hurt_t -= delta
	drop_t -= delta
	land_t -= delta
	combo_window -= delta
	melee_buf -= delta
	momentum_t -= delta
	rolled_t -= delta
	if momentum_t <= 0.0:
		momentum = 0
	if spirit_t > 0.0:
		spirit_t -= delta
		if Engine.get_physics_frames() % 4 == 0:
			FX.burst(center() + Vector2(randf_range(-8, 8), randf_range(-14, 14)), Color(0.55, 0.95, 1.0), 1, 30, 0.6, 0.18, -60, true)
		if Engine.get_physics_frames() % 3 == 0 and absf(velocity.x) > 40.0:
			FX.ghost(anim.base, Color(0.45, 0.9, 1.0, 0.35), 0.2)
	set_collision_mask_value(4, drop_t <= 0.0)

	var dir := Input.get_axis("sol", "sag")
	_resolve_roles()
	if Input.is_action_just_pressed("zipla"):
		jump_buf = 0.13
	if not is_on_floor():
		_fall_peak = maxf(_fall_peak, velocity.y)
	if is_on_floor():
		coyote = 0.09
		air_jumps = 2 if Game.has_lutuf("umay") else 1
		jumping = false
		if not _was_floor:
			_on_land()
	_was_floor = is_on_floor()

	# yuvarlanma (alçak geçitlerde kendiliğinden sürer); Shift basılı tutulursa yuvarlanma biter bitmez koşuya geçer
	if Input.is_action_just_pressed("yuvarlan") and roll_cd <= 0.0 and roll_t <= 0.0 and drink_t <= 0.0:
		_start_roll(dir)
	if Input.is_action_pressed("yuvarlan"):
		_roll_hold += delta
	else:
		_roll_hold = 0.0
		sprint = false
	if _roll_hold > 0.3 and roll_t <= 0.0 and atk.is_empty() and aim_t < 0.0 and block_t < 0.0 and not crouch_hold:
		sprint = true
	# çömelme: yerde S basılıyken; çömelirken saldırı ve yay serbest, yürüme yavaş
	var want_crouch := is_on_floor() and Input.is_action_pressed("asagi") and roll_t <= 0.0 and drink_t <= 0.0 and jump_buf <= 0.0 and wolf_t <= 0.0
	if want_crouch and not crouched:
		_set_crouch(true)
		crouch_hold = true
		sprint = false
	elif crouch_hold and (not Input.is_action_pressed("asagi") or not is_on_floor()):
		if not _head_blocked():
			crouch_hold = false
			_set_crouch(false)
	if roll_t > 0.0:
		roll_t -= delta
		_set_crouch(true)
		velocity.x = facing * ROLL_V
		velocity.y = minf(velocity.y + GRAV * delta, MAX_FALL)
		anim.set_facing(facing)
		var n := anim.frame_count("roll")
		var rf := int((1.0 - roll_t / ROLL_T) * n)
		anim.show_frame("roll", clampi(rf, 0, n - 1))
		_ghost_t -= delta
		if _ghost_t <= 0.0:
			_ghost_t = 0.045
			FX.ghost(anim.base, Color(0.55, 0.85, 1.0, 0.5), 0.22)
		if is_on_floor() and Engine.get_physics_frames() % 5 == 0:
			FX.dust(global_position + Vector2(-facing * 4, 0), Vector2(-facing, -0.4), 2, 0.26)
		_update_weapon_visual()
		move_and_slide()
		_feel(delta, dir)
		_safety(delta)
		if roll_t <= 0.0:
			if _head_blocked():
				roll_t = 0.14  # tavan alçak: sürünmeye devam
			else:
				_set_crouch(false)
		if jump_buf > 0.0 and coyote > 0.0 and not _head_blocked():
			roll_t = 0.0
			_set_crouch(false)
			_jump(false)
		if sec_act != "" and slot(sec_slot).get("id", "") == "akinci_yayi" and Input.is_action_just_pressed(sec_act) and cd[sec_slot] <= 0.0:
			_fire_bow(0.5)
		return
	if crouched and not crouch_hold:
		# yuvarlanma bitti ama hâlâ alçak yerdeyiz: sürün
		if _head_blocked():
			velocity.x = move_toward(velocity.x, dir * RUN * 0.45, ACC_GROUND * delta)
			if dir != 0:
				facing = int(signf(dir))
			velocity.y = minf(velocity.y + GRAV * delta, MAX_FALL)
			anim.set_facing(facing)
			anim.show_frame("roll", 0 if absf(velocity.x) < 10.0 else int(Time.get_ticks_msec() / 70) % anim.frame_count("roll"))
			move_and_slide()
			_feel(delta, dir)
			_safety(delta)
			return
		_set_crouch(false)

	# saldırı girdileri
	var mel := slot(mel_slot)
	var lightning := false  # v5: yıldırım hamlesi artık genel ağır saldırı (basılı tut) üzerinden
	if mel_act != "" and (Input.is_action_just_pressed(mel_act) or (_want_mel != "" and Input.is_action_just_pressed(SLOT_ACT[_want_mel]))):
		if lightning and atk.is_empty() and drink_t <= 0.0:
			charge_t = 0.0  # basılı tutma başladı: kısa dokunuş = kombo, uzun = şimşek hamlesi
		else:
			melee_buf = 0.2
	if charge_t >= 0.0:
		charge_t += delta
		if mel_act != "" and Input.is_action_pressed(mel_act) and charge_t < 1.2:
			if charge_t > 0.2 and charge_fx == null:
				charge_fx = FX.anim("focus_charge", center(), 0.0, 0.7, Color(0.6, 0.85, 1.0), true, false, self)
				if charge_fx:
					charge_fx.loop = true
				FX.text(center() + Vector2(0, -34), "", Color.WHITE, 7)
			if charge_t > 0.2:
				anim.show_frame("atk_lunge", 1)
				anim.set_facing(facing)
				if Engine.get_physics_frames() % 4 == 0:
					FX.sparks(center() + Vector2(facing * 8, 6), Vector2(-facing, -1), Color(0.6, 0.85, 1.0), 2, 80.0)
				if dir != 0:
					facing = int(signf(dir))
		else:
			var held := charge_t
			charge_t = -1.0
			if charge_fx and is_instance_valid(charge_fx):
				charge_fx.stop()
			charge_fx = null
			if held < 0.2:
				melee_buf = 0.2
			else:
				_lightning_dash(mel, held)
	var busy: bool = not atk.is_empty() and atk["phase"] != "rec"
	if atk.is_empty():
		since_atk += delta
		# bekleme bitirişi hazır: yumrukta küçük bir parıltı (oyuncuya "şimdi bas" der)
		if not _pause_ready_fx and last_step >= 1 and since_atk >= CHAIN_WINDOW and since_atk < PAUSE_WINDOW:
			_pause_ready_fx = true
			FX.burst(center() + Vector2(facing * 6, 2), Color(1.0, 0.85, 0.45), 6, 40, 0.3, 0.18, -40, true)
			anim.set_flash(0.35)
			get_tree().create_timer(0.06).timeout.connect(func() -> void: anim.set_flash(0.0))
	if melee_buf > 0.0 and drink_t <= 0.0 and aim_t < 0.0 and block_t < 0.0:
		if atk.is_empty():
			if since_atk < CHAIN_WINDOW and last_step >= 0:
				_start_attack(last_step + 1)
			elif since_atk < PAUSE_WINDOW and last_step >= 1:
				_start_attack(-1)  # bekleme bitirişi
			else:
				_start_attack(0)
		elif atk["phase"] == "rec" and not atk.get("pause", false):
			_start_attack(atk["step"] + 1)
	if regen_t > 0.0:
		regen_t -= delta
		if Engine.get_physics_frames() % 30 == 0:
			heal(max_hp() * 0.015)
			FX.burst(center() + Vector2(randf_range(-8, 8), randf_range(-10, 10)), Color(0.5, 1.0, 0.7), 1, 20, 0.5, 0.14, -50, true)

	var sec := slot(sec_slot)
	var sec_kind: String = sec.get("kind", "")
	if atk.is_empty() and drink_t <= 0.0:
		if sec_kind == "bow":
			if Input.is_action_just_pressed(sec_act) and cd[sec_slot] <= 0.0:
				aim_t = 0.0
				_bow_full = false
				Ses.play("yay_ger", -8.0)
			if aim_t >= 0.0:
				aim_t += delta
				if aim_t >= 0.55 and not _bow_full:
					_bow_full = true
					Ses.play("yay_dolu", -6.0)
					anim.set_flash(0.3)
					get_tree().create_timer(0.05).timeout.connect(func() -> void: anim.set_flash(0.0))
					if _bow_nock_ok:
						FX.burst(arm_root.to_global(_bow_nock + Vector2(facing * 21, 0)), Color(1.0, 0.9, 0.5), 6, 40, 0.25, 0.14, 0, true)
				if aim_t > 0.5 and Engine.get_physics_frames() % 3 == 0:
					FX.burst(global_position + Vector2(facing * 14, -30), Color(1.0, 0.95, 0.7), 1, 20, 0.25, 0.14, 0, true)
				if not Input.is_action_pressed(sec_act):
					_fire_bow(clampf(aim_t / 0.55, 0.0, 1.0))
					aim_t = -1.0
		elif sec_kind == "throw":
			if Input.is_action_just_pressed(sec_act) and cd[sec_slot] <= 0.0 and throw_t < 0.0:
				throw_t = 0.0
				thrown = false
		elif sec_kind == "magic":
			if Input.is_action_just_pressed(sec_act) and cd[sec_slot] <= 0.0:
				_cast_magic(sec)
		elif sec_kind == "shield":
			if Input.is_action_just_pressed(sec_act):
				block_t = 0.0
				vis_scale = Vector2(1.1, 0.92)
			if block_t >= 0.0:
				block_t += delta
				if not Input.is_action_pressed(sec_act):
					block_t = -1.0
	if throw_t >= 0.0:
		throw_t += delta
		var tf := int(throw_t / 0.07)
		anim.show_frame("throw", mini(tf, 2))
		if tf >= 1 and not thrown:
			thrown = true
			_throw_item(sec)
		if throw_t > 0.28:
			throw_t = -1.0

	# teçhizat, şişe, Kut
	for gs in ["g1", "g2"]:
		if Input.is_action_just_pressed("techizat1" if gs == "g1" else "techizat2"):
			_use_gadget(gs)
	if Input.is_action_just_pressed("sise"):
		_drink()
	if Input.is_action_just_pressed("kut"):
		_kut_power()

	# yatay hareket
	var spd := RUN * (1.15 if spirit_t > 0.0 else 1.0)
	if sprint and dir != 0:
		spd *= 1.55
	var target := dir * spd
	if busy:
		target = 0.0
	elif not atk.is_empty():
		target *= 0.45
	if crouch_hold:
		target *= 0.35
	if aim_t >= 0.0 or block_t >= 0.0:
		target *= 0.3
		if block_t >= 0.0 and sec.get("mech_id", "") == "agir_blok":
			target *= 1.0 - float(sec.get("mech_v", 40.0)) / 100.0
	if charge_t > 0.2:
		target *= 0.25
	if drink_t > 0.0:
		target *= 0.3
	if land_t > 0.0:
		target *= 0.5
	var acc := ACC_GROUND if is_on_floor() else ACC_AIR
	if is_on_floor() and (dir == 0 or signf(dir) != signf(velocity.x)):
		acc = DEC_GROUND
	if sprint and dir != 0:
		acc = 1300.0  # koşuya yumuşak geçiş
	on_ice = is_on_floor() and level != null and level.has_method("ice_at") and level.ice_at(global_position + Vector2(0, 3))
	if on_ice:
		acc *= 0.22
	if hurt_t <= 0.0:
		velocity.x = move_toward(velocity.x, target, acc * delta)
	if dir != 0 and not busy and aim_t < 0.0 and block_t < 0.0 and hurt_t <= 0.0:
		facing = int(signf(dir))
	# kayma tozu: yön değiştirirken
	if is_on_floor() and dir != 0 and signf(dir) != signf(velocity.x) and absf(velocity.x) > 90.0:
		if not _skid:
			_skid = true
			FX.dust(global_position, Vector2(signf(velocity.x), -0.5), 6, 0.3)
	else:
		_skid = false

	# zıplama
	if jump_buf > 0.0:
		if is_on_floor() and Input.is_action_pressed("asagi"):
			drop_t = 0.25
			jump_buf = 0.0
			position.y += 2
		elif coyote > 0.0:
			_jump(false)
		elif air_jumps > 0:
			air_jumps -= 1
			_jump(true)
	if jumping and velocity.y < -140.0 and not Input.is_action_pressed("zipla"):
		velocity.y *= 0.55
		jumping = false

	var gmul := 1.0
	if air_hang > 0.0 and not is_on_floor() and not atk.get("c", {}).get("plunge", false):
		gmul = 0.08
		velocity.y = minf(velocity.y, 30.0)
	elif not atk.is_empty() and atk["phase"] != "rec" and not is_on_floor():
		gmul = 0.4
	elif not is_on_floor() and absf(velocity.y) < 60.0 and jumping:
		gmul = 0.62  # tepe noktasında kısa asılı kalış
	velocity.y = minf(velocity.y + GRAV * gmul * delta, MAX_FALL)

	if drink_t > 0.0:
		drink_t -= delta
	if cast_t > 0.0:
		cast_t -= delta
	# toparlanma iptali: vuruş bitti, oyuncu yürür / zıplar / yuvarlanırsa savuruşun kuyruğunu bekletme
	if not atk.is_empty() and atk["phase"] == "rec" and not atk.get("heavy", false) and (dir != 0 or jump_buf > 0.0):
		_end_trail()
		var cc: Dictionary = atk["c"]
		last_step = -1 if (cc.get("last", false) or atk.get("pause", false)) else int(atk["step"])
		since_atk = 0.0
		atk = {}
	if not atk.is_empty():
		_update_attack(delta)

	_prev_vy = velocity.y
	move_and_slide()
	_corner_correct()
	_try_mantle(dir)
	_hazard_check(delta)
	_update_anim(dir)
	_update_weapon_visual()
	_feel(delta, dir)
	_run_dust(delta)
	_safety(delta)


func _safety(delta: float) -> void:
	## Güvenlik ağı: yerde, ayakta ve serbestken son güvenli noktayı kaydet; gömülür ya da haritanın
	## altına düşersen oraya geri al (küçük bir sarsıntıyla).
	_safe_t -= delta
	if is_on_floor() and not crouched and roll_t <= 0.0 and _safe_t <= 0.0 and not _overlapping():
		last_safe = global_position
		_safe_t = 0.4
	# gömülme: gövde katının içinde 0,25 sn kalırsa (hareket etse bile) kurtar
	if _overlapping():
		_embed_t += delta
	else:
		_embed_t = 0.0
	_prev_pos = global_position
	var fell: bool = level != null and global_position.y > (Level.H + 2) * Level.TS
	if (fell or _embed_t > 0.25) and last_safe != Vector2.ZERO:
		_embed_t = 0.0
		global_position = last_safe
		velocity = Vector2.ZERO
		_set_crouch(false)
		roll_t = 0.0
		_still_t = 0.0
		FX.dust(global_position, Vector2.UP, 6, 0.3)
		Game.shake(2.0)


func _feel(delta: float, _dir: float) -> void:
	## Squash & stretch ve eğilme: ölçek hedefe yaylanır, gövde hız yönünde yatar.
	vis_scale = vis_scale.lerp(Vector2.ONE, clampf(delta * 11.0, 0.0, 1.0))
	anim.scale = vis_scale
	var lean_target := 0.0
	if atk.is_empty() and roll_t <= 0.0 and hurt_t <= 0.0:
		lean_target = clampf(velocity.x / RUN, -1.0, 1.0) * (0.11 if is_on_floor() else 0.07)
	vis_lean = lerpf(vis_lean, lean_target, clampf(delta * 10.0, 0.0, 1.0))
	anim.rotation = vis_lean


func _run_dust(delta: float) -> void:
	_dust_t -= delta
	if sprint and is_on_floor() and absf(velocity.x) > RUN * 1.2 and Engine.get_physics_frames() % 4 == 0:
		FX.ghost(anim.base, Color(0.9, 0.85, 0.7, 0.3), 0.16)
	if is_on_floor() and absf(velocity.x) > 70.0 and roll_t <= 0.0 and _dust_t <= 0.0:
		_dust_t = 0.17 if not sprint else 0.11
		FX.dust(global_position + Vector2(-facing * 5, 0), Vector2(-facing, -0.35), 2, 0.22)
		var bid: String = level.biome.get("id", "otuken") if level else "otuken"
		var surf := "cim"
		match bid:
			"sahmeran", "tamu":
				surf = "tas"
			"kaf":
				surf = "kar"
		Ses.play("adim_" + surf, -14.0, 1.0, 0.08, 0.1)


func _on_land() -> void:
	var f := _fall_peak
	_fall_peak = 0.0
	if f > 150.0:
		var k := clampf((f - 150.0) / 400.0, 0.0, 1.0)
		vis_scale = Vector2(1.0 + 0.3 * k + 0.1, 1.0 - 0.3 * k - 0.1)
		FX.dust(global_position, Vector2.UP, 3 + int(4 * k), 0.22 + 0.12 * k)
		FX.anim("landing_dust", global_position, 0.0, 0.55 + 0.45 * k, Color(0.85, 0.8, 0.8, 0.8), false)
		land_t = 0.06 + 0.08 * k
		Ses.play("inis_2" if k > 0.5 else "inis_1", -6.0 + 4.0 * k)
		if atk.is_empty():
			anim.play("land", true)
		if k > 0.6:
			Game.shake(1.5 + 2.0 * k)
			Game.kick(Vector2.DOWN, 3.0)


func _start_roll(dir: float) -> void:
	if dir != 0:
		facing = int(signf(dir))
	atk = {}
	_end_trail()
	aim_t = -1.0
	block_t = -1.0
	roll_t = ROLL_T
	roll_cd = ROLL_T + 0.12
	rolled_t = 2.0
	Ses.play("yuvarlan", -6.0)
	_ghost_t = 0.0
	vis_scale = Vector2(1.15, 0.85)
	if slot(mel_slot).get("mech_id", "") == "golge_adim":
		sure_crits = int(slot(mel_slot).get("mech_v", 1))
	FX.dust(global_position, Vector2(-facing, -0.6), 6, 0.3)


func _jump(air: bool) -> void:
	velocity.y = JUMP_V * (0.92 if air else 1.0)
	jump_buf = 0.0
	coyote = 0.0
	jumping = true
	vis_scale = Vector2(0.78, 1.26)
	Ses.play("zipla", -8.0, 1.15 if air else 1.0, 0.08)
	if air:
		FX.burst(global_position, Color(0.75, 0.95, 1.0), 10, 70, 0.35, 0.2, 20, true)
		FX.ring(global_position, 12, Color(0.7, 0.95, 1.0), 0.2)
		FX.ghost(anim.base, Color(0.5, 0.9, 1.0, 0.45), 0.25)
	else:
		FX.dust(global_position, Vector2.UP, 5, 0.26)


func _update_anim(dir: float) -> void:
	anim.set_facing(facing)
	if not atk.is_empty() or throw_t >= 0.0:
		return
	if charge_t > 0.2:
		return
	if hurt_t > 0.0:
		anim.play("hurt")
	elif drink_t > 0.0:
		anim.play("drink")
	elif cast_t > 0.0:
		anim.show_frame("cast", 1 if cast_t < 0.2 else 0)
	elif aim_t >= 0.0:
		if crouch_hold and crouched:
			anim.show_frame("crouch_atk", 0)
		else:
			anim.show_frame("bow", 1 if aim_t > 0.12 else 0)
	elif bow_rel_t > 0.0 and slot(sec_slot).get("kind", "") == "bow":
		anim.show_frame("bow", 1)
	elif block_t >= 0.0:
		anim.show_frame("block", 0)
	elif crouch_hold and crouched:
		anim.play("crouch")
	elif not is_on_floor():
		anim.play("jump" if velocity.y < 0 else "fall")
	elif land_t > 0.0:
		anim.play("land")
	elif sprint and absf(velocity.x) > RUN * 1.15:
		anim.play("sprint")
	elif absf(velocity.x) > 12.0:
		anim.play("run")
	else:
		anim.play("idle")


# ------------------------------------------------------------------ yakın dövüş
func _combo_for(it: Dictionary) -> Dictionary:
	if COMBOS_EXTRA.has(it.get("id", "")):
		return COMBOS_EXTRA[it["id"]]
	if COMBOS.has(it.get("id", "")):
		return COMBOS[it["id"]]
	return COMBOS.get(it.get("kind", "slash"), COMBOS["slash"])


func _reach(it: Dictionary) -> float:
	return float(REACH.get(it.get("id", ""), 28.0)) * _reach_mult(it)


func _start_attack(step: int) -> void:
	## step >= 0: zincirdeki adım; step == -1: bekleme bitirişi
	var it := slot(mel_slot)
	if it.is_empty():
		return
	var combo := _combo_for(it)
	var chain: Array = combo["chain"]
	var c: Dictionary
	var is_pause := step < 0
	if is_pause:
		c = combo["pause"]
		step = last_step
	else:
		step = step % chain.size()
		c = chain[step]
	# yön tuşuyla özel hamleler (zinciri bozmaz, araya girer): dalış, göğe savurma, akın kesiği, dönüş kesiği, diz biçen
	var sp := _special_move(it)
	if not sp.is_empty():
		c = sp
		is_pause = false
		step = maxi(0, last_step)
	var sw: Dictionary = SWINGS[c["s"]]
	var spd_mult := 1.0 + ItemGen.aff(it, "hiz") / 100.0
	if it.get("mech_id", "") == "ivme":
		spd_mult *= 1.0 + momentum * float(it.get("mech_v", 8.0)) / 100.0
	if it.get("kind", "") == "dual":
		spd_mult *= 1.0 + 0.07 * step  # ikiz bıçak: kombo ilerledikçe hızlanır
	if it.get("mech_id", "") == "ay_dansi":
		spd_mult *= 1.0 + float(it.get("mech_v", 6.0)) / 100.0 * step
		if c.get("last", false) and not is_pause:
			inv_t = maxf(inv_t, 0.6)
			FX.ghost(anim.base, Color(0.8, 0.9, 1.0, 0.5), 0.3)
	if it["flaw"] == "agir":
		spd_mult *= 0.88
	var total := 1.0 / (float(it["aps"]) * spd_mult)
	if is_pause:
		total *= 1.35
	if c["s"] in ["spin", "flurry", "slam"]:
		total *= 1.25
	if c.get("special", false):
		total *= float(c.get("tm", 1.0))
		FX.text(center() + Vector2(0, -40), String(c.get("name", "")), Color(0.75, 0.95, 1.0), 8)
		if c.get("plunge", false):
			velocity = Vector2(velocity.x * 0.3, -160.0)
	atk = {"step": step, "c": c, "sw": sw, "phase": "wind", "t": 0.0, "dur": total, "hit": [], "item": it, "hold": 0.0, "pause": is_pause, "multi_i": 0}
	combo_step = step
	melee_buf = 0.0
	_pause_ready_fx = false
	_swing_sfx(it, sw, is_pause)
	vis_scale = Vector2(0.92, 1.06)
	if is_pause:
		# bekleme bitirişi: kısa parlama ve yükselen kıvılcımlar; adı ekranda belirir
		anim.set_flash(0.6)
		get_tree().create_timer(0.07).timeout.connect(func() -> void: anim.set_flash(0.0))
		FX.text(center() + Vector2(0, -40), String(c.get("name", "")), Color(1.0, 0.85, 0.45), 9)
		FX.burst(center(), Color(1.0, 0.85, 0.45), 14, 90, 0.4, 0.2, -60, true)
		if c["s"] == "slam" and is_on_floor():
			velocity.y = -330.0  # sıçra, sonra çak
	# kargı hücumu
	if it.get("mech_id", "") == "hucum" and absf(velocity.x) > RUN * 0.6 and is_on_floor():
		atk["dash"] = float(it.get("mech_v", 60.0))
		inv_t = maxf(inv_t, 0.2)
	if c.has("dash"):
		atk["dash"] = float(c["dash"])
	# Kurt Pençeleri: havadayken en yakın düşmana sıçra
	if it.get("mech_id", "") == "sicrama" and not is_on_floor():
		var best: Node = null
		var bd := 120.0
		for e in get_tree().get_nodes_in_group("dusman"):
			if is_instance_valid(e) and not e.dead:
				var d: float = center().distance_to(e.center())
				if d < bd:
					bd = d
					best = e
		if best:
			var to: Vector2 = best.center() - center()
			facing = int(signf(to.x)) if absf(to.x) > 2.0 else facing
			velocity = to.normalized() * 420.0
			atk["pounce"] = true
			inv_t = maxf(inv_t, 0.15)
			for i in 3:
				FX.ghost(anim.base, Color(0.9, 0.5, 0.4, 0.4), 0.2)


func _special_move(it: Dictionary) -> Dictionary:
	## Bağlam hamleleri (her silahta): havada ↓+J dalış, yerde ↑+J göğe savurma, koşarken J akın kesiği,
	## yuvarlanmadan hemen sonra J dönüş kesiği, çömelirken J diz biçen.
	var heavy_w: bool = it.get("id", "") in HEAVY
	if not is_on_floor() and Input.is_action_pressed("asagi"):
		return {"s": "slam_2h", "mult": 1.5, "kb": 160.0, "launch": 0.0, "special": true, "plunge": true, "tm": 1.0, "name": "Kartal Dalışı"}
	if is_on_floor() and Input.is_action_pressed("yukari"):
		return {"s": "uppercut_2h" if heavy_w else "rise", "mult": 1.1, "kb": 40.0, "launch": 360.0, "special": true, "hop": -330.0, "tm": 1.05, "name": "Göğe Savur"}
	if crouch_hold and crouched:
		return {"s": "sweep_low", "mult": 1.1, "kb": 60.0, "special": true, "trip": true, "tm": 0.9, "name": "Diz Biçen"}
	if sprint and absf(velocity.x) > RUN * 1.2:
		return {"s": "lunge", "mult": 1.5, "kb": 240.0, "dash": 140.0, "special": true, "tm": 1.0, "name": "Akın Kesiği"}
	if rolled_t > 1.4 and rolled_t < 1.72:
		return {"s": "spin", "mult": 1.3, "kb": 180.0, "special": true, "crit": true, "tm": 0.9, "name": "Dönüş Kesiği"}
	return {}


func combo_add(e: Node) -> void:
	## Kesintisiz isabet: sayaç artar, kademe atlayınca ödül (Kut, ağır çekim, ses)
	combo_n += 1
	combo_t = 2.4
	combo_best = maxi(combo_best, combo_n)
	var r := 0
	for i in COMBO_RANKS.size():
		if combo_n >= int(COMBO_RANKS[i][0]):
			r = i + 1
	if r > combo_rank:
		combo_rank = r
		var rk: Array = COMBO_RANKS[r - 1]
		var col: Color = rk[2]
		FX.text(center() + Vector2(0, -56), "%s!  x%d" % [rk[1], combo_n], col, 10 + r)
		FX.ring(center(), 30 + 10 * r, col, 0.35)
		Ses.play("seviye", -6.0 + r, 0.9 + 0.08 * r)
		add_kut(4.0 * r)
		if r >= 3:
			Game.slowmo(0.5, 0.12)
			Game.zoom_punch(0.03 + 0.01 * r)


func combo_break(reason := "") -> void:
	if combo_n >= 8:
		FX.text(center() + Vector2(0, -50), "Kombo x%d %s" % [combo_n, reason], Color(0.8, 0.75, 0.85), 8)
	combo_n = 0
	combo_rank = 0
	combo_t = 0.0


func combo_mult() -> float:
	return 1.0 + minf(0.45, 0.015 * float(combo_n))


func debug_swing(sw_name: String, item_id := "alp_kilici") -> void:
	## Savuruş laboratuvarı (--savurus): tek bir savuruşu zorla başlatır.
	var it := slot("melee")
	if it.get("id", "") != item_id:
		Game.run["slots"]["melee"] = ItemGen.roll(item_id, 1, "demir", 0)
		it = slot("melee")
	var sw: Dictionary = SWINGS[sw_name]
	atk = {"step": 0, "c": {"s": sw_name, "mult": 1.0, "kb": 100.0}, "sw": sw, "phase": "wind", "t": 0.0,
		"dur": 1.0 / float(it["aps"]) * (1.25 if sw_name in ["spin", "flurry", "slam"] else 1.0), "hit": [], "item": it, "hold": 0.0, "pause": false, "multi_i": 0}


func _atk_act() -> String:
	## Süren yakın saldırının tuşu (iki yakın silahta hangisiyle başladıysa)
	return mel_act if mel_act != "" else "saldiri1"


func _ease(u: float, mode: int) -> float:
	match mode:
		1:
			return u * u * u            # hızlanarak: vuruşun son anı en hızlı
		2:
			return 1.0 - pow(1.0 - u, 3.0)  # yavaşlayarak: takip, ağırlık
	return u * u * (3.0 - 2.0 * u)


func _swing_pose(sw: Dictionary, k: float) -> Array:
	## [a1, a2, w, k_depth, ext] — anahtarlar arasında kolay geçiş
	var keys: Array = sw["keys"]
	for i in range(keys.size() - 1):
		var k0: Array = keys[i]
		var k1: Array = keys[i + 1]
		if k <= float(k1[0]):
			var span := maxf(0.0001, float(k1[0]) - float(k0[0]))
			var u := _ease(clampf((k - float(k0[0])) / span, 0.0, 1.0), int(k1[6]))
			var out: Array = []
			for j in range(1, 6):
				out.append(lerpf(float(k0[j]), float(k1[j]), u))
			return out
	var last: Array = keys[keys.size() - 1]
	return [last[1], last[2], last[3], last[4], last[5]]


func _update_attack(delta: float) -> void:
	var c: Dictionary = atk["c"]
	var sw: Dictionary = atk["sw"]
	var it: Dictionary = atk["item"]
	var hit0: float = float(sw["hit"][0])
	var hit1: float = float(sw["hit"][1])
	# ---- v5: basılı tutma = ağır saldırı. Şarj fazı ayrı güncellenir.
	if atk["phase"] == "charge":
		_update_charge(delta)
		return
	# ---- v10: dalış (havada ↓+J): bıçak aşağıda, hızla düşer; yere değince şok dalgası
	if c.get("plunge", false) and not atk.get("plunged", false):
		var k0: float = atk["t"] / atk["dur"]
		if k0 >= hit1 - 0.04:
			if not is_on_floor():
				atk["t"] = atk["dur"] * (hit1 - 0.04)
				velocity.y = 820.0
				velocity.x = move_toward(velocity.x, 0.0, 800 * delta)
				if Engine.get_physics_frames() % 2 == 0:
					FX.ghost(anim.base, Color(0.7, 0.9, 1.0, 0.45), 0.18)
				anim.show_frame(sw["body"], clampi(int(k0 * anim.frame_count(sw["body"])), 0, anim.frame_count(sw["body"]) - 1))
				_update_weapon_visual()
				_melee_hits()
				_sample_trail(it, c, k0)
				return
			atk["plunged"] = true
			_plunge_land(it)
	# Hazırlık bitince tuş hâlâ basılıysa kısa süre bekle; bırakılırsa normal vuruş, HOLD_T'yi aşarsa ağır saldırı.
	if atk["phase"] == "wind" and _can_hold_heavy(c) and Input.is_action_pressed(_atk_act()):
		var wind_end: float = atk["dur"] * (hit0 - 0.02)
		if atk["t"] + delta >= wind_end:
			atk["t"] = wind_end
			atk["hold_wait"] = float(atk.get("hold_wait", 0.0)) + delta
			var bodyw: String = sw["body"]
			anim.show_frame(bodyw, clampi(int((atk["t"] / atk["dur"]) * anim.frame_count(bodyw)), 0, anim.frame_count(bodyw) - 1))
			_update_weapon_visual()
			if float(atk["hold_wait"]) >= HOLD_T:
				_begin_heavy(it)
			return
	# gürz şarjı: hazırlıkta tuş basılıysa bekle, güç birikir
	if c.get("charge", false) and atk["phase"] == "wind" and Input.is_action_pressed(_atk_act()) and atk["hold"] < 0.7:
		if atk["hold"] == 0.0:
			var fc := FX.anim("focus_charge", center(), 0.0, 0.8, Color(1.0, 0.8, 0.4), true, false, self)
			if fc:
				fc.loop = true
				atk["charge_fx"] = fc
		atk["hold"] += delta
		if Engine.get_physics_frames() % 4 == 0:
			FX.burst(arm_root.to_global(_hand_local), Color(1.0, 0.8, 0.4), 2, 50, 0.3, 0.16, -120, true)
		vis_scale = Vector2(1.0 + 0.05 * sin(atk["hold"] * 40.0), 1.0 - 0.05 * sin(atk["hold"] * 40.0))
		atk["t"] = minf(atk["t"] + delta, atk["dur"] * (hit0 - 0.02))
	else:
		atk["t"] += delta
	var k: float = atk["t"] / atk["dur"]
	var body: String = sw["body"]
	if crouch_hold and crouched and anim.has_anim("crouch_atk"):
		anim.show_frame("crouch_atk", 0)
	else:
		anim.show_frame(body, clampi(int(k * anim.frame_count(body)), 0, anim.frame_count(body) - 1))
	if k < hit0:
		atk["phase"] = "wind"
		_wind_fx(it, sw, k)
	elif k < hit1:
		if atk["phase"] == "wind":
			atk["phase"] = "act"
			_on_strike_start()
			if atk.is_empty():
				return
		if atk.has("dash_px"):
			velocity.x = facing * 1100.0
			velocity.y = 0.0
			if Engine.get_physics_frames() % 2 == 0:
				FX.ghost(anim.base, Color(0.6, 0.85, 1.0, 0.5), 0.18)
				FX.sparks(global_position + Vector2(-facing * 6, -4), Vector2(-facing, -0.6), Color(0.7, 0.9, 1.0), 2, 120.0)
		# seri saplama: her saplamada vuruş listesi yenilenir
		if sw.has("multi"):
			var mi: int = atk["multi_i"]
			var marks: Array = sw["multi"]
			if mi < marks.size() and k >= float(marks[mi]) - 0.04:
				atk["hit"] = []
				atk["multi_i"] = mi + 1
				vis_scale = Vector2(1.08, 0.94)
				velocity.x = facing * 60.0
				if sw["body"] == "atk_thrust":
					_thrust_streak(it)
		_update_weapon_visual()
		_melee_hits()
		_sample_trail(it, c, k)
	elif k < 1.0:
		if atk["phase"] == "act":
			_end_trail()
		atk["phase"] = "rec"
	else:
		_end_trail()
		last_step = -1 if (c.get("last", false) or atk.get("pause", false) or atk.get("heavy", false)) else int(atk["step"])
		since_atk = 0.0
		atk = {}


func _pose_points(pose: Array) -> Array:
	## Kol iskeleti: omuz çapası + açılar -> [omuz, dirsek, el, bıçak yönü] (anim yerel uzayında)
	var sh: Variant = anim.anchor("sh_f")
	if sh == null:
		sh = Vector2(2.0 * facing, -31.0)
	var kd: float = pose[3]
	var a1: float = pose[0]
	var a2: float = pose[1]
	var w: float = pose[2]
	var e: Vector2 = sh + Vector2(sin(a1) * facing * kd, cos(a1)) * float(arm_meta.get("upper_len", 8.5))
	var h: Vector2 = e + Vector2(sin(a1 + a2) * facing * kd, cos(a1 + a2)) * float(arm_meta.get("fore_len", 8.0)) * float(pose[4])
	var bd := Vector2(sin(a1 + a2 + w) * facing * kd, cos(a1 + a2 + w))
	return [sh, e, h, bd]


func _sample_trail(it: Dictionary, c: Dictionary, k: float) -> void:
	## Tek iz: gerçek bıçak ucunun yolu. Hızlı vuruşlarda kareler arası ara örneklerle pürüzsüz yay.
	if _trail == null or not is_instance_valid(_trail):
		var f: Dictionary = WFX.get(it.get("id", ""), {})
		var col: Color = f.get("col", weapon_color(it))
		var wmul := float(f.get("trail", 1.0))
		if atk.get("pause", false):
			col = col.lerp(Color(1.0, 0.85, 0.45), 0.6)
			wmul *= 1.4
		if atk.get("heavy", false):
			col = col.lerp(Color.WHITE, 0.25)
			wmul *= 1.3 + 0.4 * float(atk.get("hold", 0.0)) / 0.7
		_trail = FX.trail(col, wmul)
		if _trail == null:
			return
	var R := _reach(it)
	var sw: Dictionary = atk["sw"]
	var prev_k: float = float(_trail_prev[0]) if _trail_prev.size() > 0 else k
	var steps := 4
	for i in range(1, steps + 1):
		var kk := lerpf(prev_k, k, float(i) / steps)
		var pts := _pose_points(_swing_pose(sw, kk))
		var hand: Vector2 = pts[2]
		var bd: Vector2 = pts[3]
		var base := arm_root.to_global(hand + bd * R * 0.35)
		var tip := arm_root.to_global(hand + bd * R)
		_trail.add(base, tip)
	_trail_prev = [k]


func _end_trail() -> void:
	if _trail and is_instance_valid(_trail):
		_trail.done = true
	_trail = null
	_trail_prev = []
	if _heavy_fx and is_instance_valid(_heavy_fx):
		_heavy_fx.stop()
		Ses.loop_stop("sarj")
	_heavy_fx = null


func _on_strike_start() -> void:
	var c: Dictionary = atk["c"]
	var it: Dictionary = atk["item"]
	var hold: float = atk.get("hold", 0.0)
	var heavy_w: bool = it.get("id", "") in HEAVY
	if atk.has("charge_fx") and is_instance_valid(atk["charge_fx"]):
		atk["charge_fx"].stop()
	vis_scale = Vector2(1.12, 0.9)
	if c.has("hop") and is_on_floor():
		velocity.y = float(c["hop"])
		air_hang = 0.0
	if atk.get("heavy", false):
		# ağır vuruş: sert kamera, ışık patlaması, tam şarjda halka
		Game.kick(Vector2(facing, 0.3), 5.0 + 4.0 * hold)
		FX.flash_light(center(), weapon_color(it), 150.0 + 100.0 * hold, 1.5, 0.2)
		if hold > 0.6:
			FX.ring(center(), 50, weapon_color(it), 0.3)
	if c.get("axe", false):
		_throw_axe(it)
		return
	if atk.has("dash_px"):
		# Yıldırım hamlesi: sabit hızla ileri; yoldaki herkesi deler
		velocity.x = facing * 1100.0
		velocity.y = 0.0
		inv_t = maxf(inv_t, 0.3)
		FX.flash_light(center(), Color(0.6, 0.85, 1.0), 160.0, 2.0, 0.25)
		Game.kick(Vector2(facing, 0), 5.0)
		return
	# silahın ağırlığı gövdeyi öne taşır
	if is_on_floor():
		velocity.x = facing * ((95.0 if heavy_w else 70.0) + float(atk.get("dash", 0.0)) * 4.0)
	elif c.get("slam", false) or c.get("shock", false):
		velocity.y = maxf(velocity.y, 420.0)  # havada ağır vuruş: aşağı çakılır
	if atk.has("dash"):
		inv_t = maxf(inv_t, 0.18)
		for i in 3:
			FX.ghost(anim.base, Color(1.0, 0.9, 0.6, 0.4), 0.2)
	if atk.get("pause", false):
		Game.slowmo(0.55, 0.1)
		FX.flash_light(center(), Color(1.0, 0.85, 0.5), 140.0, 1.4, 0.2)
	if c["s"] in ["thrust", "lunge"]:
		_thrust_streak(it)
	_slash_fx(it, c)
	if c.get("wave", false):
		_spirit_wave(it)
	if it.get("mech_id", "") == "kor_izi" and (c.get("slam", false) or c.get("shock", false)) and is_on_floor():
		level.fire_pool(global_position + Vector2(facing * 26, 0), float(it.get("mech_v", 60.0)) * (0.6 + 0.8 * hold + (0.6 if atk.get("pause", false) else 0.0)), 3.0, float(it["dmg"]) * 0.25)
	if c.get("venom", false):
		for k in 3:
			_spirit_wave(it, Color(0.55, 1.0, 0.45), {"poison": 2, "kb": 40.0}, -40.0 + 40.0 * k, 260.0)
	if c.get("launch", false):
		FX.dust(global_position + Vector2(facing * 10, 0), Vector2.UP, 4, 0.22)
	if (c.get("shock", false) or c.get("slam", false)) and is_on_floor():
		var w := float(it.get("mech_v", 50.0)) * (1.0 + hold / 0.7 * 0.8) if c.get("shock", false) else 40.0
		if atk.get("pause", false):
			w *= 1.6
		Game.shake(5.0 + 6.0 * hold)
		Game.kick(Vector2.DOWN, 4.0 + 5.0 * hold)
		Ses.play("sarsinti", -2.0 + 3.0 * hold)
		FX.ring(global_position + Vector2(facing * 22, -2), w * 0.6, Color(1.0, 0.8, 0.5), 0.3, 0.3)
		FX.shock_line(global_position + Vector2(facing * 22, 0), w * 0.5)
		var gy: float = level.ground_y_below(global_position + Vector2(facing * 22, -4)) if level else -1.0
		if gy >= 0.0:
			FX.decal("decal_crack_%d" % (randi() % 2), Vector2(global_position.x + facing * 22, gy + 2), 0.0, 12.0, 0.7 + w / 100.0)
		FX.anim("earth_rupture", global_position + Vector2(facing * 24, 2), 0.0, 0.6 + w / 80.0, Color(1.0, 0.85, 0.6), false)
		FX.flash_light(global_position + Vector2(facing * 22, -10), Color(1.0, 0.8, 0.5), 120.0 + w, 1.4, 0.2)
		if c.get("shock", false):
			for e in get_tree().get_nodes_in_group("dusman"):
				if not is_instance_valid(e) or e.dead:
					continue
				var ec: Vector2 = e.center()
				if absf(ec.x - (global_position.x + facing * 22)) < w * 0.5 + 16 and absf(e.global_position.y - global_position.y) < 30:
					_deal(e, float(it["dmg"]) * 0.5 * (1.0 + hold), it, {"stun": 1.0 + hold, "kb": 160.0})


func _can_hold_heavy(c: Dictionary) -> bool:
	return not atk.get("pause", false) and not atk.get("heavy", false) and not atk.has("dash_px") \
		and not c.get("axe", false) and not c.get("charge", false) and not c.get("special", false)


func _plunge_land(it: Dictionary) -> void:
	## Kartal Dalışı inişi: çevreye şok, fırlatma, krater çatlağı; düşüş yüksekliğiyle güçlenir
	var power := clampf(_fall_peak / 600.0, 0.5, 1.5)
	var r := 70.0 * power
	Game.shake(6.0 * power)
	Game.kick(Vector2.DOWN, 6.0)
	Game.hitstop(0.08)
	vis_scale = Vector2(1.35, 0.7)
	FX.anim("earth_rupture", global_position, 0.0, 0.9 * power, Color(0.8, 0.9, 1.0), false)
	FX.ring(global_position + Vector2(0, -4), r, Color(0.75, 0.9, 1.0), 0.3, 0.3)
	FX.shock_line(global_position, r * 0.8)
	FX.dust(global_position, Vector2.UP, 10, 0.36)
	FX.flash_light(global_position + Vector2(0, -10), Color(0.75, 0.9, 1.0), 160.0, 1.6, 0.2)
	FX.decal("decal_crack_%d" % (randi() % 2), global_position + Vector2(0, 2), 0.0, 10.0, 0.9 * power)
	Ses.play("darbe_cekic", -1.0, 1.05)
	Ses.play("sarsinti", -5.0)
	for e in get_tree().get_nodes_in_group("dusman"):
		if not is_instance_valid(e) or e.dead:
			continue
		if absf(e.global_position.x - global_position.x) < r and absf(e.global_position.y - global_position.y) < 40.0:
			_deal(e, float(it["dmg"]) * 1.2 * power, it, {"kb": 160.0, "dir": signf(e.global_position.x - global_position.x), "launch": 260.0, "stun": 0.4, "sfx_done": true})
			combo_add(e)


func _heavy_for(it: Dictionary) -> Dictionary:
	if HEAVIES.has(it.get("id", "")):
		return HEAVIES[it["id"]]
	return HEAVIES.get(it.get("kind", "slash"), HEAVIES["slash"])


func _begin_heavy(it: Dictionary) -> void:
	## Ağır saldırı: hazırlık pozunda şarj; bırakınca (ya da dolup 0.5 sn geçince) silahın özgün ağır vuruşu
	var h := _heavy_for(it)
	var sw: Dictionary = SWINGS[h["s"]]
	var spd_mult := 1.0 + ItemGen.aff(it, "hiz") / 100.0
	if it["flaw"] == "agir":
		spd_mult *= 0.88
	var total := 1.0 / (float(it["aps"]) * spd_mult) * 1.45
	if sw.has("multi") or sw.get("around", false):
		total *= 1.2
	atk = {"step": atk.get("step", 0), "c": h, "sw": sw, "phase": "charge", "t": 0.0, "dur": total, "hit": [], "item": it,
		"hold": 0.0, "pause": false, "multi_i": 0, "heavy": true, "charge": 0.0, "full_fx": false}
	if h.has("dash"):
		atk["dash"] = float(h["dash"])
	combo_step = 0
	melee_buf = 0.0
	_end_trail()
	vis_scale = Vector2(0.9, 1.1)
	anim.set_flash(0.25)
	get_tree().create_timer(0.05).timeout.connect(func() -> void: anim.set_flash(0.0))
	var col := weapon_color(it)
	var fc := FX.anim("focus_charge", center(), 0.0, 0.9, col, true, false, self)
	if fc:
		fc.loop = true
		_heavy_fx = fc
	FX.burst(center(), col, 8, 60, 0.3, 0.16, -40, true)
	Ses.loop_start("sarj", "sarj_dongu", -10.0, 0.8)


func _update_charge(delta: float) -> void:
	## Şarj fazı: hazırlık pozu tutulur, silaha kıvılcım akar; dolunca parlama + ad. Bırakınca vuruşa geçer.
	var c: Dictionary = atk["c"]
	var sw: Dictionary = atk["sw"]
	var it: Dictionary = atk["item"]
	var hit0: float = float(sw["hit"][0])
	atk["charge"] = float(atk["charge"]) + delta
	var ch: float = atk["charge"]
	var full := ch >= HEAVY_MAX
	var wob := minf(ch, HEAVY_MAX) / HEAVY_MAX
	atk["t"] = atk["dur"] * (hit0 - 0.02) * clampf(ch / 0.12, 0.0, 1.0)
	var body: String = sw["body"]
	anim.show_frame(body, clampi(int((atk["t"] / atk["dur"]) * anim.frame_count(body)), 0, anim.frame_count(body) - 1))
	_update_weapon_visual()
	var col := weapon_color(it)
	var hand := arm_root.to_global(_hand_local)
	if Engine.get_physics_frames() % 3 == 0:
		var from := hand + Vector2(randf_range(-28, 28), randf_range(-28, 28))
		FX.streak(from, hand, Color(col, 0.6), 0.1)
	if Engine.get_physics_frames() % 5 == 0:
		FX.burst(hand, col, 2, 40, 0.3, 0.14, -80, true)
	vis_scale = Vector2(1.0 + 0.035 * wob * sin(ch * 45.0), 1.0 - 0.035 * wob * sin(ch * 45.0))
	velocity.x = move_toward(velocity.x, 0.0, 1200.0 * delta)
	Ses.loop_pitch("sarj", 0.8 + 0.7 * wob)
	if full and not atk["full_fx"]:
		atk["full_fx"] = true
		Ses.play("sarj_dolu", -2.0)
		anim.set_flash(0.6)
		get_tree().create_timer(0.08).timeout.connect(func() -> void: anim.set_flash(0.0))
		FX.ring(hand, 26, col, 0.3)
		FX.flash_light(hand, col, 110.0, 1.6, 0.2)
		FX.text(center() + Vector2(0, -40), String(c.get("name", "AĞIR")), col.lerp(Color.WHITE, 0.3), 9)
		Game.kick(Vector2.UP, 2.0)
	if not Input.is_action_pressed(_atk_act()) or ch >= HEAVY_MAX + 0.5:
		if _heavy_fx and is_instance_valid(_heavy_fx):
			_heavy_fx.stop()
		_heavy_fx = null
		Ses.loop_stop("sarj")
		Ses.play("agir_birak", -1.0, 0.9 + 0.2 * wob)
		atk["hold"] = 0.7 * wob
		if c.get("lightning", false):
			_lightning_dash(it, 0.2 + 0.6 * wob)
			return
		atk["phase"] = "wind"
		atk["t"] = atk["dur"] * (hit0 - 0.02)
		for i in 2:
			FX.ghost(anim.base, Color(col, 0.45), 0.2)
		if full:
			Game.slowmo(0.5, 0.08)
		if c.get("slam", false) and is_on_floor():
			velocity.y = -300.0 - 120.0 * wob


func _wind_fx(it: Dictionary, sw: Dictionary, k: float) -> void:
	## Hazırlık efektleri: yerde sürüklenen kılıç kıvılcım saçar, çekişte kabza parlar, çarklarda iz hazırlıkta başlar.
	var sname: String = atk["c"]["s"]
	match sname:
		"ground_drag":
			if Engine.get_physics_frames() % 2 == 0 and k > 0.12:
				var tip := arm_root.to_global(_hand_local + _blade_local * _reach(it))
				FX.sparks(tip, Vector2(-facing, -0.8), Color(1.0, 0.8, 0.5), 3, 150.0)
				FX.dust(tip, Vector2(-facing, -0.3), 1, 0.2)
		"iai":
			if not atk.get("wind_fx", false):
				atk["wind_fx"] = true
				FX.flash_light(arm_root.to_global(_hand_local), weapon_color(it), 60.0, 1.2, 0.12)
		"windmill", "helicopter":
			if k > 0.15:
				_sample_trail(it, atk["c"], k)
		"overhead_2h", "slam_2h", "uppercut_2h":
			if Engine.get_physics_frames() % 4 == 0 and k > 0.15:
				FX.burst(arm_root.to_global(_hand_local), weapon_color(it), 1, 30, 0.25, 0.14, -60, true)


func _weapon_hit_fx(it: Dictionary, hp: Vector2, hdir: Vector2, big: bool) -> void:
	## Silaha özgü darbe efekti (kılıç hilali, çekiç çatlağı, buz, od, ruh...)
	var f: Dictionary = WFX.get(it.get("id", ""), {})
	var col: Color = f.get("col", weapon_color(it))
	var sc := float(f.get("hit_scale", 0.6)) * (1.4 if big else 1.0)
	if f.has("hit"):
		FX.anim(f["hit"], hp, hdir.angle(), sc, col, true, facing < 0)
	match String(f.get("extra", "")):
		"blood":
			FX.blood(hp, hdir, Color(0.75, 0.1, 0.12), 8)
		"fire":
			FX.fire(hp, 6, 0.34)
		"frost":
			FX.frost(hp, 4)
		"ghost":
			FX.ghost(anim.base, Color(col, 0.5), 0.25)
		"dust":
			FX.dust(Vector2(hp.x, global_position.y), Vector2(facing, -0.6), 6, 0.3)
		"soul":
			FX.soul(hp, col, 6)


func _spirit_wave(it: Dictionary, col := Color(0.5, 1.0, 0.9), extra: Dictionary = {}, vy := 0.0, speed := 340.0) -> void:
	## Ruh Kılıcı: savuruşla birlikte uçan hilal; 2 düşmanı deler, menzil mech_v. (Yılan / Rüzgâr kılıcı da kullanır.)
	var p := Projectile.new()
	p.team = "p"
	p.kind = "wave"
	p.position = global_position + Vector2(facing * 16, -28)
	p.velocity = Vector2(facing * speed, vy)
	p.pierce = 2
	p.life = float(it.get("mech_v", 160.0)) / speed
	p.trail_col = col
	var origin := global_position
	p.on_hit = func(e: Node) -> void:
		var o := {"kb": 70.0, "dir": facing, "far": absf(e.center().x - origin.x) > 90.0}
		o.merge(extra, true)
		_deal(e, float(it["dmg"]) * 0.8, it, o)
	level.add_projectile(p)
	FX.slash_sprite("arc_short", p.position, 0.0, Vector2(0.9 * facing, 0.9), col, false, Vector2(-1, -1), p, 30.0)


func _impact_kind(it: Dictionary) -> String:
	var iid: String = it.get("id", "")
	if iid in ["ruh_kilici", "ay_palasi", "yildirim_kilici", "ayaz_kilici"]:
		return "magic"
	match String(it.get("kind", "slash")):
		"heavy":
			return "blunt"
		"thrust":
			return "pierce"
	return "cut"


func _slash_fx(it: Dictionary, c: Dictionary) -> void:
	## Vuruş anında savuruşa uygun kesik sprite'ı: yay (omuz merkezli, bıçak ucundan geçer), çizgi, halka, çapraz
	var sname: String = c["s"]
	var R := _reach(it)
	var f: Dictionary = WFX.get(it.get("id", ""), {})
	var col: Color = f.get("col", weapon_color(it))
	if atk.get("pause", false):
		col = col.lerp(Color(1.0, 0.85, 0.45), 0.5)
	var heavy: bool = atk.get("heavy", false) or it.get("id", "") in HEAVY
	# normal zincir vuruşlarında ana efekt piksel izdir; büyük hilal yalnızca bitiriş, ağır ve özel savuruşlarda
	if not (atk.get("pause", false) or atk.get("heavy", false) or c.get("last", false) or sname in ["thrust", "flurry", "lunge", "pole_thrust", "stab_heavy", "spin", "helicopter", "twirl", "cross_x"]):
		return
	var pts := _pose_points(_swing_pose(atk["sw"], 0.0))
	var sh := arm_root.to_global(pts[0])
	var rad := R + float(arm_meta.get("upper_len", 8.5)) + float(arm_meta.get("fore_len", 8.0)) * 0.9
	var sc := rad / 51.0  # yay sayfalarında yarıçap = 0.4 x genişlik
	match sname:
		"thrust", "flurry", "lunge", "pole_thrust", "stab_heavy":
			FX.slash_sprite("line", Vector2(global_position.x + facing * 6, center().y - 4), 0.0 if facing > 0 else PI,
				Vector2((R + 34.0) / 86.0, 0.8 + (0.5 if heavy else 0.0)), col, false, Vector2(0.1, 0.5))
		"spin", "helicopter", "twirl":
			FX.slash_sprite("ring", center() + Vector2(0, -6), 0.0, Vector2(sc * 0.9 * facing, sc * 0.9), col, false, Vector2(-1, -1), self)
		"cross_x":
			FX.slash_sprite("x", sh + Vector2(facing * rad * 0.45, 2), 0.0, Vector2(sc * 0.8 * facing, sc * 0.8), col)
		_:
			var n := "arc_heavy" if heavy else ("arc_short" if R < 20.0 else ("arc_thin" if sname in ["horiz", "back", "reverse_grip", "sweep_low", "pole_sweep", "reap", "iai"] else "arc"))
			sc = 0.78 * rad / (0.4 * float(SlashFX.meta()[n]["w"]))
			var rot := 0.0
			var fv := false
			var sy := 1.0
			match sname:
				"diag_down":
					rot = 0.35
				"up", "rise", "uppercut_2h":
					fv = true
				"diag_up", "ground_drag":
					fv = true
					rot = -0.35
				"horiz", "reverse_grip", "sweep_low", "pole_sweep", "iai":
					rot = -0.3
					sy = 0.72
				"back", "reap":
					rot = 0.3
					fv = true
					sy = 0.72
			FX.slash_sprite(n, sh, rot * facing, Vector2(sc * facing, sc * sy), col, fv)


func _thrust_streak(it: Dictionary) -> void:
	## Saplama hız çizgisi: elden uca ve ötesine incelerek solan parlak çizgi + uçta kıvılcım
	var R := _reach(it)
	var y := center().y - 4.0
	var x0 := global_position.x + facing * 6.0
	FX.streak(Vector2(x0, y), Vector2(x0 + facing * (R + 34.0), y), weapon_color(it))


func _reach_mult(it: Dictionary) -> float:
	if it.get("mech_id", "") == "genis_yay":
		return 1.0 + float(it.get("mech_v", 20.0)) / 100.0
	return 1.0


func _swing_box(sw_name: String, R: float) -> Rect2:
	## Vuruş kutusu savuruş tipine ve silah boyuna göre: [x0, y0, x1, y1] (ileri yön +)
	var b: Array
	match sw_name:
		"down", "heavy", "slam", "diag_down", "axe_hook", "whip_crack", "rake", "windmill":
			b = [-4.0, -54.0, R + 10.0, 0.0]
		"overhead_2h", "slam_2h":
			b = [-6.0, -60.0, R + 14.0, 2.0]
		"up", "rise", "diag_up", "ground_drag", "uppercut_2h":
			b = [-2.0, -66.0, R + 8.0, -4.0]
		"horiz", "back", "cross_x", "reverse_grip", "iai", "twirl":
			b = [-4.0, -48.0, R + 12.0, -8.0]
		"reap":
			b = [-10.0, -50.0, R + 14.0, -6.0]
		"sweep_low":
			b = [-8.0, -30.0, R + 14.0, 2.0]
		"thrust", "flurry":
			b = [4.0, -42.0, R + 16.0, -18.0]
		"pole_thrust", "stab_heavy":
			b = [4.0, -44.0, R + 26.0, -16.0]
		"pole_sweep":
			b = [-8.0, -52.0, R + 20.0, -6.0]
		"lunge":
			b = [-6.0, -46.0, R + 22.0, -6.0]
		"spin", "helicopter":
			b = [-(R + 10.0), -62.0, R + 10.0, 0.0]
		_:
			b = [0.0, -48.0, R + 8.0, 0.0]
	var x0: float = b[0]
	var x1: float = b[2]
	if facing < 0:
		var t := -x1
		x1 = -x0
		x0 = t
	return Rect2(global_position.x + x0, global_position.y + float(b[1]), x1 - x0, float(b[3]) - float(b[1]))


func _melee_hits() -> void:
	var c: Dictionary = atk["c"]
	var it: Dictionary = atk["item"]
	var sw: Dictionary = atk["sw"]
	var R := _reach(it)
	if it.get("mech_id", "") == "ulu_kesik":
		R = maxf(R, float(it.get("mech_v", 60.0)))
	var box := _swing_box(String(c["s"]), R)
	var around: bool = sw.get("around", false)
	var hold: float = atk.get("hold", 0.0)
	var heavy_w: bool = it.get("id", "") in HEAVY
	for e in get_tree().get_nodes_in_group("dusman"):
		if not is_instance_valid(e) or e.dead or atk["hit"].has(e):
			continue
		if box.intersects(e.hurt_rect()):
			atk["hit"].append(e)
			var opts := {"kb": float(c["kb"]), "step": atk["step"], "last": c.get("last", false) or atk.get("pause", false)}
			var dist := absf(e.center().x - global_position.x)
			opts["tip"] = dist > R * 0.75
			opts["dash"] = atk.has("dash")
			if c.has("launch"):
				opts["launch"] = float(c["launch"])
			if around:
				opts["dir"] = signf(e.center().x - global_position.x)
			var mult := float(c["mult"]) * (1.0 + hold / 0.7 * 0.9)
			var hp: Vector2 = e.hurt_rect().intersection(box).get_center()
			# darbe noktası: bıçak ucuna en yakın yer
			var tip_g := arm_root.to_global(_hand_local + _blade_local * R * 0.85)
			if e.hurt_rect().grow(6).has_point(tip_g):
				hp = tip_g
			var hdir := Vector2(float(opts.get("dir", facing)), -0.3)
			if atk.has("dash_px"):
				opts["pierce_n"] = atk["hit"].size()
				opts["kb"] = 60.0
			if atk.get("pounce", false):
				opts["pounce"] = true
			if c.get("whip", false):
				opts["whip"] = true
			if c.get("crit", false):
				opts["force_crit"] = true
			if c.get("trip", false):
				opts["stun"] = 0.9
				opts["launch"] = 140.0
			opts["behind"] = "facing" in e and int(e.facing) == int(signf(float(opts.get("dir", facing))))
			opts["heavy"] = atk.get("heavy", false)
			opts["hit_n"] = atk["hit"].size()
			opts["sfx_done"] = true
			_deal(e, float(it["dmg"]) * mult, it, opts)
			_hit_sfx(it, opts.get("crit_done", false) or atk.get("pause", false) or atk.get("heavy", false), opts.get("crit_done", false), String(c["s"]))
			var big: bool = opts.get("crit_done", false) or atk.get("pause", false) or atk.get("heavy", false)
			FX.impact(hp, hdir, weapon_color(it), 1.0 if big else 0.6)
			var fcol: Color = WFX.get(it.get("id", ""), {}).get("col", weapon_color(it))
			FX.impact_sprite(_impact_kind(it), hp, hdir, fcol, (1.35 if big else 0.95) * (1.25 if heavy_w else 1.0))
			FX.sparks(hp, hdir, weapon_color(it).lerp(Color.WHITE, 0.3), 9 if big else 6, 200.0)
			_weapon_hit_fx(it, hp, hdir, big)
			if opts.get("crit_done", false):
				FX.anim("electric_impact", hp, 0.0, 0.8, Color(1.0, 0.9, 0.5))
			elif it.get("material", "") == "od_tasi":
				FX.fire(hp, 5, 0.32)
			elif it.get("material", "") == "ayaz":
				FX.anim("frost_nova", hp, 0.0, 0.5, Color(0.7, 0.9, 1.0))
			Game.kick(Vector2(facing, 0), 4.5 if heavy_w else 2.5)
			if c.get("double", false):
				var opts2 := opts.duplicate()
				opts2["kb"] = float(c["kb"]) * 0.6
				_deal(e, float(it["dmg"]) * mult * 0.7, it, opts2)
				FX.impact(hp + Vector2(facing * 6, -6), hdir, weapon_color(it), 0.8)
			combo_add(e)
			if not is_on_floor():
				air_hang = 0.28
			var hs_k := 1.0 + minf(0.5, 0.02 * float(combo_n))
			if atk.get("heavy", false):
				Game.hitstop((0.09 + 0.04 * hold) * hs_k)
				Game.shake(3.0 + 3.0 * hold)
				if hold > 0.5 and level and level.has_method("flash_white"):
					level.flash_white()
			elif heavy_w or float(c["kb"]) > 200.0 or big:
				Game.hitstop((0.075 if heavy_w else 0.06) * hs_k)
			else:
				Game.hitstop(0.04 * hs_k)
	if level and level.has_method("break_cracks"):
		level.break_cracks(box)


# ------------------------------------------------------------------ hasar hesabı
func _deal(e: Node, base: float, it: Dictionary, opts: Dictionary = {}) -> void:
	var d := base * Game.item_mult(opts.get("scale_item", it))
	d *= 1.0 + ItemGen.aff(it, "hasar") / 100.0
	var hp_k := float(Game.run["hp"]) / max_hp()
	if hp_k >= 0.999:
		d *= 1.0 + ItemGen.aff(it, "tam_can") / 100.0
	if hp_k < 0.35:
		d *= 1.0 + ItemGen.aff(it, "dusuk_can") / 100.0
	if not is_on_floor():
		d *= 1.0 + ItemGen.aff(it, "hava") / 100.0
	if rolled_t > 0.0:
		d *= 1.0 + ItemGen.aff(it, "yuvarlanma") / 100.0
	if spirit_t > 0.0:
		d *= 1.5
	if e.elite:
		d *= 1.0 + ItemGen.aff(it, "seckin") / 100.0
	if e.is_boss:
		d *= 1.0 + ItemGen.aff(it, "boss") / 100.0
	var mech: String = it.get("mech_id", "")
	var mv := float(it.get("mech_v", 0.0))
	d *= combo_mult()
	# mekanik kritik koşulları
	var crit := randf() * 100.0 < float(it.get("crit", 0.0)) + ItemGen.aff(it, "krit_sans") + (10.0 if Game.has_lutuf("ay_ata") else 0.0)
	if Game.has_lutuf("erlik"):
		d *= 1.35
	match mech:
		"ucuncu_vurus":
			if opts.get("last", false):
				crit = true
				d *= 1.0 + mv / 100.0
		"kanatma":
			if e.bleed > 0:
				crit = true
			if randf() * 100.0 < mv:
				e.bleed = mini(5, e.bleed + 1)
				e.bleed_t = 4.0
		"ivme":
			momentum = mini(5, momentum + 1)
			momentum_t = 1.0
			if momentum >= 5:
				crit = true
		"sarsinti":
			if e.stun_t > 0.0:
				crit = true
			opts["stun"] = maxf(float(opts.get("stun", 0.0)), 0.6)
		"genis_yay":
			if opts.get("tip", false):
				crit = true
		"hucum":
			if opts.get("dash", false):
				crit = true
		"golge_adim":
			if sure_crits > 0:
				crit = true
				sure_crits -= 1
			if e.facing == sign(e.center().x - center().x):
				crit = true
		"kemankes":
			if opts.get("full", false):
				crit = true
		"part_atisi":
			d *= 1.0 + mv / 100.0
			if roll_t > 0.0 or velocity.x * float(opts.get("dir", facing)) < -20.0:
				crit = true
		"saplan":
			if e.root_t > 0.0:
				crit = true
			opts["root"] = mv
		"sekme":
			if e.stun_t > 0.0:
				crit = true
		"simsek_hamlesi":
			if int(opts.get("pierce_n", 0)) >= 1:
				crit = true
		"sicrama":
			if opts.get("pounce", false):
				d *= 1.0 + mv / 100.0
			if e.flying or not e.is_on_floor():
				crit = true
		"ruh_bic":
			if e.hp < e.max_hp * 0.3:
				crit = true
		"don":
			if e.freeze_t > 0.0:
				crit = true
				d *= 1.3
				e.freeze_t = 0.0
				FX.anim("resonant_break", e.center(), 0.0, 0.8, Color(0.7, 0.9, 1.0))
			else:
				e.frost += 1
				if e.frost >= 3:
					e.frost = 0
					opts["freeze"] = mv
		"zirh_kir":
			if e.armor_break >= 3:
				crit = true
			e.armor_break = mini(3, e.armor_break + 1)
			e.armor_mv = mv
		"firlat_cagir":
			if opts.get("axe_return", false):
				crit = true
		"yakala":
			if opts.get("whip", false):
				if e.heavy:
					velocity.x = signf(e.center().x - center().x) * mv * 3.0
				else:
					e.velocity.x = -float(opts.get("dir", facing)) * mv * 3.0
					e.pulled_t = 0.6
				FX.anim("tether_catch", e.center(), 0.0, 0.7, Color(0.9, 0.8, 0.6))
			if e.pulled_t > 0.0:
				crit = true
		"tutustur":
			if e.burn_t > 0.0:
				crit = true
			opts["burn"] = maxf(float(opts.get("burn", 0.0)), mv)
		"yelpaze", "alev_oku":
			if opts.get("full", false) or (mech == "alev_oku" and e.burn_t > 0.0):
				crit = true
		"ses_dalgasi":
			if e.stun_t > 0.0:
				crit = true
			if randf() * 100.0 < mv:
				opts["stun"] = maxf(float(opts.get("stun", 0.0)), 0.8)
		"yildirim":
			if e.freeze_t > 0.0 or e.stun_t > 0.0:
				crit = true
		"itme":
			if opts.get("walled", false):
				crit = true
		"gudum":
			if opts.get("far", false):
				crit = true
		"ezme":
			if opts.get("falling", false):
				crit = true
		"ulu_kesik":
			if int(opts.get("hit_n", 0)) >= 2:
				crit = true
		"dag_sarsintisi":
			if not e.is_on_floor() or e.launch_t > 0.0 or e.stun_t > 0.0:
				crit = true
				e.velocity.y = 500.0
		"ruh_dalgasi":
			if opts.get("far", false):
				crit = true
		"ay_dansi":
			if opts.get("last", false):
				crit = true
		"zehir_dis":
			opts["poison"] = 1
			if e.poison >= 3:
				crit = true
		"tulpar":
			if sprint or atk.has("dash") or opts.get("dash", false):
				crit = true
			opts["pierce"] = true
		"arkadan":
			if opts.get("behind", false) or e.stun_t > 0.0 or e.state == "stagger":
				crit = true
				FX.text(e.center() + Vector2(0, -24), "arkadan!", Color(0.85, 0.75, 1.0), 7)
		"kanli_kesik":
			e.bleed = mini(5, e.bleed + 1)
			e.bleed_t = 4.0
			if e.bleed >= 3:
				crit = true
		"itki":
			opts["kb"] = float(opts.get("kb", 100.0)) * 1.8
			e._slam_t = 0.45
			if e.stun_t > 0.0:
				crit = true
		"bozgun":
			if e.max_hp > 0.0 and e.hp / e.max_hp < 0.35:
				crit = true
		"kor_izi":
			if e.burn_t > 0.0:
				crit = true
		"yel_kesigi":
			wind_n += 1
			if wind_n % 3 == 0:
				_spirit_wave.call_deferred(it, Color(0.78, 0.95, 1.0), {"kb": 60.0}, 0.0, 380.0)
			if not e.is_on_floor():
				crit = true
	if opts.get("force_crit", false):
		crit = true
	if crit:
		d *= float(it.get("crit_mult", 1.9)) + ItemGen.aff(it, "krit_hasar") / 100.0
		opts["crit_done"] = true
	opts["crit"] = crit
	opts["dir"] = opts.get("dir", facing)
	if randf() * 100.0 < ItemGen.aff(it, "yanma") or (it["material"] == "od_tasi" and randf() < 0.2):
		opts["burn"] = 3.0
	if randf() * 100.0 < ItemGen.aff(it, "kanama"):
		e.bleed = mini(5, e.bleed + 1)
		e.bleed_t = 4.0
	if randf() * 100.0 < ItemGen.aff(it, "dondurma"):
		opts["freeze"] = 1.2
	if randf() * 100.0 < ItemGen.aff(it, "zehirleme") or (mech == "ruh_bic" and randf() < 0.3):
		opts["poison"] = 1
	if it["material"] == "ayaz" and randf() < 0.15:
		opts["freeze"] = maxf(float(opts.get("freeze", 0.0)), 0.8)
	if it["material"] == "kara_tas":
		opts["stagger"] = true
	if Game.has_lutuf("gun_ana") and randf() < 0.25:
		opts["burn"] = maxf(float(opts.get("burn", 0.0)), 3.0)
	var killed: bool = e.take_hit(d, opts)
	add_kut(d * 0.22 + ItemGen.aff(it, "kut"))
	if Game.has_lutuf("tengri") and randf() < 0.22 and not opts.get("zincir", false):
		_tengri_chain(e, d * 0.5, it)
	if killed and mech == "bozgun":
		_bozgun_shards(e, it)
	if killed and Game.has_lutuf("ulgen"):
		heal(max_hp() * 0.03)
		FX.burst(center(), Color(1.0, 0.95, 0.6), 6, 40, 0.5, 0.16, -60, true)
	if crit and it["material"] == "yesim":
		heal(2)
	if killed:
		var lc := ItemGen.aff(it, "can_calma") + (max_hp() * 0.02 if it["material"] == "kemik" else 0.0)
		if mech == "ruh_bic":
			lc += mv
			FX.soul(center(), Color(0.6, 0.2, 0.6), 10)
		if lc > 0:
			heal(lc)
		var boom := ItemGen.aff(it, "patlama")
		if boom > 0 and level:
			level.explode(e.center(), 36, boom * (1.0 + 0.6 * float(it["tier"])), true)


# ------------------------------------------------------------------ uzak silahlar
func _swing_sfx(it: Dictionary, sw: Dictionary, is_pause: bool) -> void:
	## Savuruş sesi: silahın ses sınıfına göre gerçek kayıt katmanı; saplamalar ince ve hızlı, ağır savuruşlar kalın
	var sname: String = atk["c"]["s"]
	var cls: String = WSND.get(it.get("id", ""), "kilic" if it.get("kind", "") != "heavy" else "cekic")
	var is_thrust: bool = sname in ["thrust", "flurry", "lunge", "pole_thrust", "stab_heavy"]
	var is_big: bool = atk.get("heavy", false) or sname in ["overhead_2h", "slam_2h", "windmill", "helicopter", "uppercut_2h", "slam", "heavy"]
	var vol := -5.0
	var pit := 1.0 + 0.04 * float(atk.get("step", 0))
	var name := "savur_" + cls
	if is_thrust:
		name = "savur_sirik" if cls in ["sirik", "dev", "cekic", "balta"] else ("savur_bicak" if cls == "bicak" else "savur_kilic")
		pit *= 1.15
	if is_big:
		name = "savur_dev" if cls in ["kilic", "katana", "ruh", "dev", "balta"] else ("savur_cekic" if cls in ["cekic", "sirik"] else name)
		pit *= 0.92
		vol = -3.0
	if sname == "iai":
		name = "savur_katana"
	Ses.play(name, vol, pit, 0.06)
	if is_pause:
		Ses.play("savur_dev", -7.0, 1.1, 0.05, 0.0)


func _hit_sfx(it: Dictionary, big: bool, crit: bool, sname: String) -> void:
	## Darbe sesi: silah sınıfı + vuruşun büyüklüğü (et kesme, künt, delme, balta, kırbaç, çekiç çakma)
	var cls: String = WSND.get(it.get("id", ""), "kilic" if it.get("kind", "") != "heavy" else "cekic")
	var is_thrust: bool = sname in ["thrust", "flurry", "lunge", "pole_thrust", "stab_heavy"]
	var name := "darbe_kesik"
	var pit := 1.0
	match cls:
		"kilic", "katana", "ruh":
			name = "darbe_delme" if is_thrust else ("darbe_kesik_agir" if big else "darbe_kesik")
		"dev":
			name = "darbe_kesik_agir"
		"cekic":
			name = "darbe_cekic" if big else "darbe_kunt"
		"balta":
			name = "darbe_balta"
		"sirik":
			name = "darbe_delme" if is_thrust else "darbe_kesik"
		"bicak":
			name = "darbe_kesik"
			pit = 1.2
		"kirbac":
			name = "darbe_kirbac"
	Ses.play(name, -2.0 if big else -4.0, pit, 0.07, 0.02)
	if crit:
		Ses.play("darbe_kritik", -1.0, 1.0, 0.04, 0.05)


func _fire_bow(charge: float) -> void:
	Ses.play("yay_birak_tam" if charge >= 0.99 else "yay_birak", -3.0, 0.95 + 0.1 * charge)
	var it := slot(sec_slot)
	var full := charge >= 0.98
	var spd := lerpf(300.0, 560.0, charge)
	var mech: String = it.get("mech_id", "")
	var n_arrows := int(it.get("mech_v", 1)) if mech == "yelpaze" else 1
	for i in n_arrows:
		var p := Projectile.new()
		p.kind = "arrow"
		p.team = "p"
		p.position = (arm_root.to_global(_bow_nock + Vector2(facing * 12, 0)) if _bow_nock_ok else global_position + Vector2(facing * 10, -30))
		var ang := 0.0
		if n_arrows > 1:
			ang = lerpf(-0.42, 0.42, float(i) / float(n_arrows - 1))
		p.velocity = Vector2(facing * spd, -20.0 * (1.0 - charge)).rotated(ang * facing)
		p.gravity = 260.0 * (1.0 - charge)
		p.pierce = int(it.get("mech_v", 1)) if (full and mech == "kemankes") else (1 if (full and mech == "yelpaze") else 0)
		# her yayın kendi iz rengi ve uçuş efekti
		match String(it.get("id", "")):
			"akinci_yayi":
				p.trail_col = Color(1.0, 0.35, 0.3)
			"saganak_yayi", "tufan_yayi":
				p.trail_col = Color(0.5, 0.8, 1.0)
				p.fx_kind = "sel"
			"od_oklari":
				p.trail_col = Color(1.0, 0.55, 0.15)
				p.fx_kind = "od"
			_:
				p.trail_col = Color(1.0, 0.95, 0.8)
		if full and p.fx_kind == "":
			p.trail_col = Color(1.0, 0.85, 0.4)
			p.fx_kind = "altin"
		var dmg_k := lerpf(0.6, 1.6, charge) * (0.75 if n_arrows > 1 else 1.0)
		p.on_hit = func(e: Node) -> void:
			_deal(e, float(it["dmg"]) * dmg_k, it, {"full": full, "kb": 60.0, "dir": facing})
			if mech == "alev_oku":
				level.fire_pool(e.global_position, 22.0, float(it.get("mech_v", 2.0)), 2.0)
		level.add_projectile(p)
	if mech == "alev_oku":
		FX.fire(global_position + Vector2(facing * 14, -30), 4, 0.3)
	cd[sec_slot] = 1.0 / float(it["aps"])
	cd_max[sec_slot] = cd[sec_slot]
	vis_scale = Vector2(0.94, 1.04)
	bow_rel_t = BOW_REL
	_bow_full = false
	Ses.play("ok_ucus", -12.0, 0.9 + 0.25 * charge, 0.08, 0.03, center())
	var muzzle := arm_root.to_global(_bow_nock + Vector2(facing * 20, 0)) if _bow_nock_ok else global_position + Vector2(facing * 10, -30)
	if full:
		Game.hitstop(0.03)
	FX.burst(muzzle, Color(1, 0.95, 0.8), 4 + int(6 * charge), 40 + 60 * charge, 0.2, 0.15, 0, true)
	if full:
		FX.ring(muzzle, 14, Color(1.0, 0.9, 0.5), 0.18)
		Game.kick(Vector2(-facing, 0), 3.0)


func _throw_item(it: Dictionary) -> void:
	var p := Projectile.new()
	p.team = "p"
	p.position = global_position + Vector2(facing * 10, -32)
	if it["id"] == "cirit":
		p.kind = "javelin"
		p.velocity = Vector2(facing * 430, -40)
		p.gravity = 180.0
		p.atlas_item = "cirit"
		p.atlas_mat = it["material"]
		p.stick = true
		p.trail_col = Color(0.9, 0.85, 0.7)
	elif it["id"] == "kartal_tuyleri":
		var n := int(it.get("mech_v", 3))
		for i in n:
			var f := Projectile.new()
			f.team = "p"
			f.kind = "feather"
			f.position = global_position + Vector2(facing * 8, -34 + i * 3)
			f.velocity = Vector2(facing * 300, -60 + i * 40).rotated(randf_range(-0.2, 0.2))
			f.homing = 5.0
			f.life = 2.2
			f.trail_col = Color(0.9, 0.9, 1.0)
			var origin := global_position
			f.on_hit = func(e: Node) -> void:
				_deal(e, float(it["dmg"]), it, {"kb": 50.0, "dir": signf(e.center().x - origin.x), "far": e.center().distance_to(origin) > 150.0})
			level.add_projectile(f)
		cd[sec_slot] = 1.0 / float(it["aps"])
		cd_max[sec_slot] = cd[sec_slot]
		vis_scale = Vector2(1.06, 0.95)
		return
	elif it["id"] == "mancinik_tasi":
		p.kind = "stone_big"
		p.atlas_item = "mancinik_tasi"
		p.atlas_mat = "kara_tas"
		p.velocity = Vector2(facing * 260, -300)
		p.gravity = 620.0
		p.explode_on_wall = true
		var r := float(it.get("mech_v", 60))
		p.on_explode = func(pos: Vector2) -> void:
			level.quake(pos, r, float(it["dmg"]), it, self)
		level.add_projectile(p)
		cd[sec_slot] = 1.0 / float(it["aps"])
		cd_max[sec_slot] = cd[sec_slot]
		vis_scale = Vector2(1.1, 0.9)
		return
	else:
		p.kind = "stone"
		p.velocity = Vector2(facing * 380, -60)
		p.gravity = 300.0
		p.bounces = int(it.get("mech_v", 1))
	p.on_hit = func(e: Node) -> void:
		_deal(e, float(it["dmg"]), it, {"kb": 90.0, "dir": facing, "stun": 0.25 if it["id"] == "coban_sapani" else 0.0})
	level.add_projectile(p)
	cd[sec_slot] = 1.0 / float(it["aps"])
	cd_max[sec_slot] = cd[sec_slot]
	vis_scale = Vector2(1.08, 0.94)


# ------------------------------------------------------------------ teçhizat
func _use_gadget(gs: String) -> void:
	var it := slot(gs)
	if it.is_empty():
		return
	if cd[gs] > 0.0:
		FX.text(center() + Vector2(0, -24), "hazır değil", Color(0.8, 0.8, 0.9), 7)
		return
	var cdv := float(it["cd"]) * (1.0 - ItemGen.aff(it, "bekleme") / 100.0)
	var power := float(it.get("power", 1.0)) * Game.item_mult(it)
	var radius := 40.0 * (1.0 + ItemGen.aff(it, "genis") / 100.0)
	match it["id"]:
		"kara_barut", "od_testisi":
			var p := Projectile.new()
			p.team = "p"
			p.kind = "bomb" if it["id"] == "kara_barut" else "pot"
			p.atlas_item = it["id"]
			p.atlas_mat = "demir"
			p.position = global_position + Vector2(facing * 8, -34)
			p.velocity = Vector2(facing * 230 + velocity.x * 0.3, -230)
			p.gravity = 700.0
			p.explode_on_wall = true
			var is_bomb: bool = it["id"] == "kara_barut"
			p.on_explode = func(pos: Vector2) -> void:
				if is_bomb:
					level.explode(pos, radius, 32.0 * power, true)
				else:
					level.fire_pool(pos, radius * 0.8, 4.0, 3.0 * power)
			level.add_projectile(p)
		"bozkurt_cagrisi":
			level.spawn_spirit_wolf(global_position + Vector2(-facing * 20, 0), 12.0, 9.0 * power)
		"nazar_boncugu":
			ward = true
			FX.ring(center(), 24, Color(0.35, 0.6, 1.0), 0.4)
			FX.text(center() + Vector2(0, -28), "Nazar", Color(0.6, 0.8, 1.0), 8)
		"sifa_muskasi":
			regen_t = 8.0
			FX.anim("radiant_heal", global_position, 0.0, 1.0, Color(0.6, 1.0, 0.8), true, false, self)
		"ayaz_tilsimi":
			var ip := Projectile.new()
			ip.team = "p"
			ip.kind = "ice"
			ip.atlas_item = "ayaz_tilsimi"
			ip.atlas_mat = "ayaz"
			ip.position = global_position + Vector2(facing * 8, -34)
			ip.velocity = Vector2(facing * 220 + velocity.x * 0.3, -220)
			ip.gravity = 700.0
			ip.explode_on_wall = true
			ip.on_explode = func(pos: Vector2) -> void:
				FX.anim("frost_nova", pos, 0.0, 1.0 + radius / 60.0, Color(0.7, 0.9, 1.0))
				FX.flash_light(pos, Color(0.6, 0.85, 1.0), radius * 3.0, 1.6, 0.3)
				for e in get_tree().get_nodes_in_group("dusman"):
					if is_instance_valid(e) and not e.dead and e.center().distance_to(pos) < radius + 14.0:
						e.take_hit(6.0 * power, {"freeze": 3.0, "kb": 20.0, "dir": signf(e.center().x - pos.x)})
			level.add_projectile(ip)
		"yel_tilsimi":
			FX.anim("leaf_gust", center(), 0.0, 1.5, Color(0.8, 1.0, 0.8))
			FX.ring(center(), 100, Color(0.7, 1.0, 0.8), 0.35)
			FX.dust(global_position, Vector2.UP, 12, 0.4)
			Game.shake(3.0)
			for e in get_tree().get_nodes_in_group("dusman"):
				if is_instance_valid(e) and not e.dead and e.center().distance_to(center()) < 110.0:
					var dirx := signf(e.center().x - center().x)
					e.take_hit(4.0 * power, {"kb": 340.0, "dir": dirx, "launch": 180.0, "stun": 0.3})
		"davul_totemi":
			var t := Totem.new()
			t.level = level
			t.dmg = 7.0 * power
			t.position = Vector2(global_position.x + facing * 20, level.surface_y(int(global_position.x / 24.0 + facing)) * 24.0)
			level.actors.add_child(t)
		"ok_yagmuru":
			var ox := global_position.x + facing * 90
			var ground_y: float = level.surface_y(int(ox / 24.0)) * 24.0
			level.telegraph_ground(Vector2(ox, ground_y), 0.5)
			_arrow_rain(ox, ground_y, 3.0, 4.0 * power, it)
		"kartal_cagrisi":
			var ep := Projectile.new()
			ep.team = "p"
			ep.kind = "eagle"
			ep.position = global_position + Vector2(-facing * 60, -90)
			ep.velocity = Vector2(facing * 380, 120)
			ep.gravity = -140.0
			ep.pierce = 99
			ep.life = 1.6
			ep.trail_col = Color(0.9, 0.85, 0.6)
			ep.on_hit = func(e: Node) -> void:
				e.take_hit(14.0 * power, {"kb": 160.0, "dir": facing, "launch": 120.0})
			level.add_projectile(ep)
			FX.text(center() + Vector2(0, -34), "Kartal!", Color(1.0, 0.9, 0.6), 8)
		"ruh_kusu":
			level.spawn_spirit_wolf(global_position + Vector2(-facing * 20, -30), 15.0, 6.0 * power, "cor")
		"umay_tuyu":
			revive = true
			FX.anim("radiant_heal", global_position, 0.0, 1.1, Color(1.0, 0.95, 0.7), true, false, self)
			FX.text(center() + Vector2(0, -34), "Umay'ın tüyü seni gözetiyor", Color(1.0, 0.95, 0.7), 8)
		"erlik_zinciri":
			var cpos := center() + Vector2(facing * 40, 0)
			FX.anim("tether_catch", cpos, 0.0, 1.3, Color(0.7, 0.4, 0.9))
			FX.ring(cpos, 110, Color(0.6, 0.3, 0.8), 0.4)
			for e in get_tree().get_nodes_in_group("dusman"):
				if is_instance_valid(e) and not e.dead and e.center().distance_to(cpos) < 120.0:
					var to: Vector2 = cpos - e.center()
					e.velocity = to.normalized() * 380.0
					e.pulled_t = 0.8
					e.take_hit(3.0 * power, {"kb": 0.0, "stun": 0.6, "dir": signf(to.x)})
	cd[gs] = cdv
	cd_max[gs] = cdv


func _drink() -> void:
	if int(Game.run["flasks"]) <= 0 or float(Game.run["hp"]) >= max_hp() or drink_t > 0.0:
		return
	Game.run["flasks"] = int(Game.run["flasks"]) - 1
	drink_t = 0.5
	Ses.play("sise", -3.0)
	atk = {}
	_end_trail()
	heal(max_hp() * 0.5)
	FX.anim("radiant_heal", global_position, 0.0, 1.0, Color(0.6, 1.0, 0.8), true, false, self)
	FX.soul(center(), Color(0.5, 1.0, 0.8), 12)


func _kut_power() -> void:
	if kut < 100.0:
		FX.text(center() + Vector2(0, -24), "Kut dolmadı", Color(0.8, 0.8, 0.9), 7)
		return
	kut = 0.0
	_begin_wolf()


func _begin_wolf() -> void:
	## Bozkurt biçimi: 9 sn boyunca büyük ruh kurduna dönüşürsün. J ısırık zinciri, K sıçrayış, F uluma, Shift atılış.
	wolf_t = 9.0
	spirit_t = wolf_t
	atk = {}
	_end_trail()
	charge_t = -1.0
	if charge_fx and is_instance_valid(charge_fx):
		charge_fx.stop()
	charge_fx = null
	aim_t = -1.0
	block_t = -1.0
	throw_t = -1.0
	roll_t = 0.0
	_set_crouch(false)
	wolf_atk = {}
	wolf_step = 0
	wolf_since = 9.0
	howl_cd = 0.0
	anim.visible = false
	arm_root.visible = false
	weapon.visible = false
	shield_spr.visible = false
	wolf_anim.visible = true
	wolf_anim.set_facing(facing)
	wolf_anim.play("idle", true)
	var sh := cshape.shape as RectangleShape2D
	sh.size = Vector2(30, 30)
	cshape.position = Vector2(0, -15)
	Game.shake(5.0)
	Game.slowmo(0.3, 0.35)
	Game.kick(Vector2.UP, 4.0)
	FX.ring(center(), 80, Color(0.5, 0.95, 1.0), 0.5)
	FX.anim("spectral_bloom", global_position, 0.0, 1.9, Color(0.6, 0.95, 1.0))
	FX.anim("void_implosion", center(), 0.0, 1.2, Color(0.6, 0.95, 1.0))
	FX.impact(center(), Vector2.UP, Color(0.5, 0.95, 1.0), 2.4)
	FX.soul(center(), Color(0.6, 1.0, 1.0), 30)
	FX.flash_light(center(), Color(0.5, 0.95, 1.0), 300.0, 2.4, 0.6)
	FX.text(center() + Vector2(0, -44), "BOZKURT", Color(0.6, 1.0, 1.0), 12)
	Ses.play("kut_donusum", 0.0)


func _end_wolf() -> void:
	wolf_t = 0.0
	spirit_t = 0.0
	wolf_atk = {}
	pounce_t = 0.0
	wolf_anim.visible = false
	anim.visible = true
	anim.set_facing(facing)
	var sh := cshape.shape as RectangleShape2D
	sh.size = Vector2(12, 40)
	cshape.position = Vector2(0, -20)
	inv_t = maxf(inv_t, 0.5)
	FX.anim("smoke_puff", center(), 0.0, 1.1, Color(0.6, 0.9, 1.0), true)
	FX.soul(center(), Color(0.6, 1.0, 1.0), 14)
	FX.ghost(wolf_anim.base, Color(0.6, 0.95, 1.0, 0.5), 0.35)


func _wolf_nearby(radius: float, front_only := false) -> Array:
	var out: Array = []
	for e in get_tree().get_nodes_in_group("dusman"):
		if is_instance_valid(e) and not e.dead and e.center().distance_to(center()) < radius:
			if front_only and signf(e.center().x - center().x) != facing:
				continue
			out.append(e)
	return out


func _wolf_process(delta: float) -> void:
	wolf_t -= delta
	spirit_t = wolf_t
	howl_cd -= delta
	inv_t -= delta
	hurt_t -= delta
	wolf_since += delta
	coyote -= delta
	jump_buf -= delta
	if wolf_t <= 0.0:
		_end_wolf()
		return
	var it := slot(mel_slot)
	var dir := Input.get_axis("sol", "sag")
	if Input.is_action_just_pressed("zipla"):
		jump_buf = 0.13
	if is_on_floor():
		coyote = 0.09
		air_jumps = 1
	# kut izi
	if Engine.get_physics_frames() % 3 == 0:
		FX.burst(center() + Vector2(randf_range(-14, 6) * facing, randf_range(-10, 8)), Color(0.55, 0.95, 1.0), 1, 25, 0.5, 0.16, -50, true)
	if Engine.get_physics_frames() % 4 == 0 and absf(velocity.x) > 120.0:
		FX.ghost(wolf_anim.base, Color(0.45, 0.9, 1.0, 0.35), 0.22)
	# --- sıçrayış (K ya da Shift): ileri 180 px, yoldaki herkesi devirir
	if (Input.is_action_just_pressed("saldiri2") or Input.is_action_just_pressed("yuvarlan")) and pounce_t <= 0.0 and wolf_atk.is_empty():
		if dir != 0:
			facing = int(signf(dir))
		pounce_t = 0.3
		wolf_hit = []
		inv_t = maxf(inv_t, 0.35)
		velocity = Vector2(facing * 640.0, -120.0)
		wolf_anim.set_facing(facing)
		FX.dust(global_position, Vector2(-facing, -0.5), 8, 0.34)
		Ses.play("sicrayis", -2.0)
		FX.anim("mass_release", global_position + Vector2(facing * 30, -16), 0.0 if facing > 0 else PI, 1.2, Color(0.6, 0.95, 1.0))
		Game.kick(Vector2(facing, 0), 5.0)
	# --- uluma (F): çevredekileri sersemletir, Kut parçası toplar
	if Input.is_action_just_pressed("kut") and howl_cd <= 0.0 and wolf_atk.is_empty() and pounce_t <= 0.0:
		howl_cd = 3.0
		wolf_atk = {"kind": "howl", "t": 0.0, "dur": 0.7}
		velocity.x = 0.0
		Game.shake(4.0)
		Game.slowmo(0.5, 0.15)
		FX.ring(center(), 130, Color(0.6, 0.95, 1.0), 0.6)
		FX.ring(center(), 90, Color(0.8, 1.0, 1.0), 0.4)
		FX.anim("hush_lock", center() + Vector2(facing * 14, -10), 0.0, 1.4, Color(0.6, 0.95, 1.0))
		FX.flash_light(center(), Color(0.6, 0.95, 1.0), 260.0, 2.0, 0.5)
		FX.text(center() + Vector2(0, -40), "ULUMA", Color(0.6, 1.0, 1.0), 10)
		Ses.play("uluma", 0.0)
		for e in _wolf_nearby(140.0):
			e.take_hit(float(it.get("dmg", 10)) * 0.5, {"kb": 120.0, "dir": signf(e.center().x - center().x), "stun": 1.8, "stagger": true})
			FX.anim("electric_impact", e.center(), 0.0, 0.6, Color(0.6, 0.95, 1.0))
		wolf_t = minf(9.0, wolf_t + 1.0)
	# --- ısırık (J): üçlü zincir; üçüncü ısırık tutup fırlatır
	if Input.is_action_just_pressed("saldiri1") and wolf_atk.is_empty() and pounce_t <= 0.0:
		if wolf_since > 0.45:
			wolf_step = 0
		wolf_atk = {"kind": "bite", "t": 0.0, "dur": 0.32 if wolf_step < 2 else 0.42, "step": wolf_step}
		wolf_hit = []
		if dir != 0:
			facing = int(signf(dir))
		velocity.x = facing * (220.0 if wolf_step < 2 else 300.0)
		wolf_anim.set_facing(facing)
		vis_scale = Vector2(1.15, 0.9)
		Ses.play("isirik", -2.0, 1.0 if wolf_step < 2 else 0.85)
		FX.dust(global_position, Vector2(-facing, -0.3), 3, 0.26)
	# saldırı güncelle
	if not wolf_atk.is_empty():
		wolf_atk["t"] += delta
		var k: float = wolf_atk["t"] / wolf_atk["dur"]
		if wolf_atk["kind"] == "howl":
			wolf_anim.show_frame("howl", clampi(int(k * 4), 0, 3))
			velocity.x = move_toward(velocity.x, 0.0, 800 * delta)
		else:
			wolf_anim.show_frame("bite", clampi(int(k * 5), 0, 4))
			if k > 0.2 and k < 0.7:
				var box := Rect2(global_position.x + (4.0 if facing > 0 else -68.0), global_position.y - 44.0, 64.0, 44.0)
				for e in get_tree().get_nodes_in_group("dusman"):
					if not is_instance_valid(e) or e.dead or wolf_hit.has(e):
						continue
					if box.intersects(e.hurt_rect()):
						wolf_hit.append(e)
						var last: bool = wolf_atk["step"] == 2
						var opts := {"kb": 90.0 if not last else 260.0, "dir": facing, "launch": 180.0 if last else 0.0, "force_crit": last, "last": last}
						_deal(e, float(it.get("dmg", 10)) * (1.2 if not last else 1.9), it, opts)
						var hp: Vector2 = e.hurt_rect().intersection(box).get_center()
						FX.impact(hp, Vector2(facing, -0.3), Color(0.6, 0.95, 1.0), 1.4 if last else 1.0)
						FX.blood(hp, Vector2(facing, -0.5), e.blood_col(), 10)
						FX.anim("crescent_slash", hp, 0.0 if facing > 0 else PI, 0.6, Color(0.6, 0.95, 1.0), true, facing < 0)
						Game.kick(Vector2(facing, 0), 4.0)
						Game.hitstop(0.05 if not last else 0.08)
						wolf_t = minf(9.0, wolf_t + 0.3)
		if k >= 1.0:
			wolf_step = 0 if wolf_atk["kind"] == "howl" or wolf_atk["step"] == 2 else int(wolf_atk["step"]) + 1
			wolf_since = 0.0
			wolf_atk = {}
	# sıçrayış güncelle
	if pounce_t > 0.0:
		pounce_t -= delta
		wolf_anim.show_frame("pounce", 1 if pounce_t > 0.1 else 2)
		velocity.x = facing * 640.0
		if Engine.get_physics_frames() % 2 == 0:
			FX.ghost(wolf_anim.base, Color(0.55, 0.95, 1.0, 0.5), 0.2)
		for e in get_tree().get_nodes_in_group("dusman"):
			if is_instance_valid(e) and not e.dead and not wolf_hit.has(e) and hurt_rect().grow(10).intersects(e.hurt_rect()):
				wolf_hit.append(e)
				_deal(e, float(it.get("dmg", 10)) * 1.5, it, {"kb": 200.0, "dir": facing, "launch": 220.0, "stun": 0.5})
				FX.impact(e.center(), Vector2(facing, -0.4), Color(0.6, 0.95, 1.0), 1.3)
				FX.anim("solar_shrapnel", e.center(), 0.0, 0.6, Color(0.6, 0.95, 1.0))
				Game.hitstop(0.05)
		if pounce_t <= 0.0:
			velocity.x *= 0.4
	else:
		# hareket: hızlı, keskin
		var spd := RUN * 1.6
		var target := dir * spd
		if not wolf_atk.is_empty():
			target *= 0.2
		var acc := ACC_GROUND * 1.2 if is_on_floor() else ACC_AIR
		if hurt_t <= 0.0:
			velocity.x = move_toward(velocity.x, target, acc * delta)
		if dir != 0 and wolf_atk.is_empty() and hurt_t <= 0.0:
			facing = int(signf(dir))
		if jump_buf > 0.0 and (coyote > 0.0 or air_jumps > 0):
			if coyote <= 0.0:
				air_jumps -= 1
				FX.ring(global_position, 14, Color(0.6, 0.95, 1.0), 0.2)
			velocity.y = JUMP_V * 1.08
			jump_buf = 0.0
			coyote = 0.0
			vis_scale = Vector2(0.85, 1.18)
			FX.dust(global_position, Vector2.UP, 4, 0.28)
	velocity.y = minf(velocity.y + GRAV * delta, MAX_FALL)
	move_and_slide()
	wolf_anim.set_facing(facing)
	if wolf_atk.is_empty() and pounce_t <= 0.0:
		if hurt_t > 0.0:
			wolf_anim.play("hurt")
		elif not is_on_floor():
			wolf_anim.show_frame("pounce", 1 if velocity.y < 0 else 2)
		elif absf(velocity.x) > 14.0:
			wolf_anim.play("run")
			wolf_anim.speed = clampf(absf(velocity.x) / (RUN * 1.6), 0.6, 1.4)
		else:
			wolf_anim.play("idle")
			wolf_anim.speed = 1.0
	vis_scale = vis_scale.lerp(Vector2.ONE, clampf(delta * 11.0, 0.0, 1.0))
	wolf_anim.scale = vis_scale
	if Engine.get_physics_frames() % 10 == 0 and is_on_floor() and absf(velocity.x) > 100.0:
		FX.dust(global_position + Vector2(-facing * 10, 0), Vector2(-facing, -0.3), 2, 0.24)
	_safety(delta)
	# bitişe yakın: uyarı titremesi
	if wolf_t < 1.5 and int(wolf_t * 8.0) % 2 == 0:
		wolf_anim.set_flash(0.3)
	else:
		wolf_anim.set_flash(0.0)


# ------------------------------------------------------------------ silah görseli
func _update_weapon_visual() -> void:
	## Silah gösteren her durumda ön kol iskeletle çizilir; aksi halde gövde sprite'ındaki kol kullanılır.
	var it: Dictionary = {}
	var pose: Array = []
	var is_shield := false
	if not atk.is_empty():
		it = atk["item"]
		pose = _swing_pose(atk["sw"], atk["t"] / atk["dur"])
	elif charge_t > 0.2:
		it = slot(mel_slot)
		pose = [-0.5, 1.95, -0.15, 1.0, 1.0]
	elif aim_t >= 0.0:
		it = slot(sec_slot)
		var pull := clampf(aim_t / 0.55, 0.0, 1.0)
		# tam gerilince ok ucu hafifçe titrer (gerginlik)
		var quiver := 0.012 * sin(aim_t * 70.0) if pull >= 1.0 else 0.0
		pose = [1.55 + quiver, 0.05, 0.0, 1.0, 1.0 - 0.05 * pull]
	elif bow_rel_t > 0.0 and slot(sec_slot).get("kind", "") == "bow":
		it = slot(sec_slot)
		var rk := bow_rel_t / BOW_REL
		pose = [1.55 + 0.12 * rk, 0.05, -0.1 * rk, 1.0, 1.0 + 0.04 * rk]
	elif throw_t >= 0.0:
		it = slot(sec_slot)
		var tk := clampf(throw_t / 0.28, 0.0, 1.0)
		pose = _swing_pose(SWINGS["axe"], tk)
	elif block_t >= 0.0:
		it = slot(sec_slot)
		is_shield = true
		pose = [1.25, 0.9, 0.0, 1.0, 1.0]
	elif cast_t > 0.0:
		it = slot(sec_slot)
		pose = [1.45, 0.1, -0.5, 1.0, 1.0]
	var show := not pose.is_empty() and not it.is_empty() and roll_t <= 0.0 and hurt_t <= 0.0
	arm_root.visible = show
	if bow_str and (not show or it.get("kind", "") != "bow"):
		bow_str.visible = false
		_bow_nock_ok = false
	if not show:
		weapon.visible = false
		shield_spr.visible = false
		if arm_root_b:
			arm_root_b.visible = false
		return
	var pts := _pose_points(pose)
	var sh: Vector2 = pts[0]
	var e: Vector2 = pts[1]
	var h: Vector2 = pts[2]
	var bd: Vector2 = pts[3]
	_hand_local = h
	_blade_local = bd.normalized() if bd.length() > 0.01 else Vector2(facing, 0)
	_place_bone(arm_upper, sh, e, float(arm_meta.get("upper_len", 8.5)))
	_place_bone(arm_fore, e, h, float(arm_meta.get("fore_len", 8.0)))
	arm_fist.position = h
	arm_fist.rotation = arm_fore.rotation
	arm_fist.flip_h = facing < 0
	_update_back_arm(it, h, bd, is_shield)
	var has_sprite := Data.has_weapon_sprite(it.get("id", ""))
	weapon.visible = has_sprite and not is_shield
	shield_spr.visible = has_sprite and is_shield
	if weapon.visible:
		weapon.region_rect = Data.weapon_region(it["id"], it["material"])
		weapon.offset = -Data.weapon_pivot(it["id"])
		weapon.position = h
		if it.get("kind", "") == "bow":
			weapon.rotation = 0.0 if facing > 0 else PI
			_update_bow(it, h)
		else:
			weapon.rotation = bd.angle()
			weapon.scale = Vector2(clampf(bd.length(), 0.15, 1.0), facing)
	if shield_spr.visible:
		shield_spr.region_rect = Data.weapon_region(it["id"], it["material"])
		shield_spr.offset = -Data.weapon_pivot(it["id"])
		shield_spr.position = h + Vector2(facing * 3, 0)
		shield_spr.rotation = 0.0
		shield_spr.scale = Vector2(facing, 1)


func _bow_tips(it: Dictionary) -> Array:
	## Yay sprite'ının üst ve alt ucu (pivot'a göre); görüntüden bir kez okunur.
	var key := String(it["id"]) + "/" + String(it["material"])
	if _bow_tip_cache.has(key):
		return _bow_tip_cache[key]
	var out := [Vector2(-2, -16), Vector2(-2, 16)]
	var img: Image = Data.weapon_tex.diffuse_texture.get_image()
	if img:
		if img.is_compressed():
			img.decompress()
		var reg := Rect2i(Data.weapon_region(it["id"], it["material"]))
		var piv := Data.weapon_pivot(it["id"])
		var top := Vector2.INF
		var bot := Vector2.INF
		# uçlar: kabzanın (pivot) solunda kalan, en üst ve en alt dolu pikseller
		for y in reg.size.y:
			for x in range(0, int(piv.x) + 6):
				if img.get_pixel(reg.position.x + x, reg.position.y + y).a > 0.5:
					if top == Vector2.INF:
						top = Vector2(x, y)
					bot = Vector2(x, y)
					break
		if top != Vector2.INF:
			out = [top - piv + Vector2(0.5, 0.5), bot - piv + Vector2(0.5, 0.5)]
	_bow_tip_cache[key] = out
	return out


func _update_bow(it: Dictionary, h: Vector2) -> void:
	## Yay: gerildikçe kollar esner (yatay sıkışma), kiriş gez noktasına geri çekilir, ok yayda durur;
	## bırakınca kiriş sönümlü titrer ve yay geri teper.
	var pull := clampf(aim_t / 0.55, 0.0, 1.0) if aim_t >= 0.0 else 0.0
	var rk := clampf(bow_rel_t / BOW_REL, 0.0, 1.0) if aim_t < 0.0 else 0.0
	var flex := 1.0 - 0.1 * pull
	weapon.scale = Vector2(flex, facing)
	weapon.position = h + Vector2(-facing * 2.0 * rk * rk, 0)
	var tips := _bow_tips(it)
	var t0: Vector2 = tips[0]
	var t1: Vector2 = tips[1]
	var top := weapon.position + Vector2(t0.x * flex * facing, t0.y * (1.0 - 0.05 * pull))
	var bot := weapon.position + Vector2(t1.x * flex * facing, t1.y * (1.0 - 0.05 * pull))
	var mid := (top + bot) * 0.5
	var nock := mid + Vector2(-facing * (1.0 + 11.0 * pull), 0)
	if rk > 0.0:
		var tt := Time.get_ticks_msec() / 1000.0
		nock.x = mid.x + facing * sin(tt * 75.0) * 2.5 * rk
	bow_str.visible = true
	bow_str.top = top
	bow_str.bot = bot
	bow_str.nock = nock.round()
	bow_str.dir = facing
	bow_str.arrow_on = aim_t >= 0.0 and not (String(it["id"]) in BAKED_ARROW_BOWS)
	bow_str.glow = (0.6 + 0.4 * sin(aim_t * 18.0)) if (aim_t >= 0.0 and pull >= 1.0) else 0.0
	match String(it["id"]):
		"akinci_yayi":
			bow_str.fletch = Color(0.75, 0.1, 0.16)
			bow_str.arrow_head = Color(0.8, 0.82, 0.88)
		_:
			bow_str.fletch = Color(0.85, 0.25, 0.2)
			bow_str.arrow_head = Color(0.88, 0.92, 0.98) if pull < 1.0 else Color(1.0, 0.9, 0.55)
	bow_str.queue_redraw()
	_bow_nock = nock
	_bow_nock_ok = true


func _place_bone(sp: Sprite2D, a: Vector2, b: Vector2, rest_len: float) -> void:
	## Aşağıyı gösteren parça sprite'ını a'dan b'ye yerleştir (uzunluğa göre esnet).
	var d := b - a
	sp.position = a
	sp.rotation = atan2(-d.x, d.y)
	sp.scale = Vector2(1.0, maxf(0.2, d.length() / rest_len))


func _on_anim_finished(_n: String) -> void:
	pass


# ------------------------------------------------------------------ hasar alma
func apply_poison(t: float) -> void:
	if poison_t <= 0.0:
		FX.text(center() + Vector2(0, -34), "zehirlendin", Color(0.55, 1.0, 0.35), 7)
	poison_t = maxf(poison_t, t)


func get_grabbed(by: Node) -> void:
	grabbed_by = by
	mash = 0
	roll_t = 0.0
	charge_t = -1.0
	Game.slowmo(0.4, 0.15)
	Game.kick(Vector2(0, 1), 3.0)


func release_grab(throw_v: Vector2) -> void:
	grabbed_by = null
	velocity = throw_v
	inv_t = 0.6
	hurt_t = 0.2
	vis_scale = Vector2(0.85, 1.15)
	FX.ghost(anim.base, Color(1.0, 0.9, 0.6, 0.4), 0.2)


func take_hit(dmg: float, from: Node, projectile: Node = null, forced := false) -> bool:
	## true: hasar alındı; "parry" durumunda saldıran sersemletilir. forced: yakalanmışken gıdıklama (dokunulmazlık yok)
	if dead or (not forced and (inv_t > 0.0 or roll_t > 0.0)):
		return false
	if ward:
		ward = false
		FX.ring(center(), 26, Color(0.35, 0.6, 1.0), 0.35)
		FX.impact(center(), Vector2.UP, Color(0.4, 0.65, 1.0), 1.5)
		FX.text(center() + Vector2(0, -28), "Nazar değdi!", Color(0.6, 0.8, 1.0), 8)
		if from and from.has_method("apply_curse"):
			from.apply_curse()
		inv_t = 0.4
		return false
	var sh := slot(sec_slot)
	var src_x: float = from.global_position.x if from else global_position.x + facing
	var facing_src: bool = sign(src_x - global_position.x) == facing
	if block_t >= 0.0 and sh.get("kind", "") == "shield" and facing_src:
		if block_t <= float(sh.get("parry_win", 0.18)):
			_parry(sh, from, projectile)
			return false
		dmg *= 1.0 - float(sh.get("block", 0.7))
		match sh.get("mech_id", ""):
			"diken":
				if from and from.has_method("take_hit") and from.has_method("center"):
					from.take_hit(float(sh.get("mech_v", 10)), {"kb": 40.0, "dir": facing, "stagger": true})
			"kok":
				if from and "root_t" in from:
					from.root_t = maxf(from.root_t, float(sh.get("mech_v", 1.0)))
					FX.anim("rootscript", from.global_position, 0.0, 0.8, Color(0.6, 0.9, 0.5), false)
		FX.sparks(center() + Vector2(facing * 12, 0), Vector2(facing, -0.6), Color(1, 0.9, 0.6), 8, 160.0)
		FX.impact(center() + Vector2(facing * 12, 0), Vector2(facing, 0), Color(1, 0.9, 0.6), 0.8)
		vis_scale = Vector2(0.9, 1.08)
	dmg *= 1.0 - minf(0.3, 0.03 * float(Game.run["ongun"]["ayi"]))
	if Game.has_lutuf("yer_sub"):
		dmg *= 0.75
	if wolf_t > 0.0:
		dmg *= 0.6
		wolf_atk = {}
		pounce_t = 0.0
	Game.run["hp"] = float(Game.run["hp"]) - dmg
	inv_t = 0.8
	hurt_t = 0.25
	combo_break("kırıldı")
	Ses.play("bengu_can", -1.0)
	Ses.play("darbe_et", -4.0)
	atk = {}
	_end_trail()
	aim_t = -1.0
	var kdir := signf(global_position.x - src_x)
	if kdir == 0:
		kdir = -facing
	velocity = Vector2(kdir * 170.0, -160.0)
	vis_scale = Vector2(1.25, 0.8)
	FX.number(center(), dmg, false, Color(1.0, 0.45, 0.4))
	FX.impact(center(), Vector2(kdir, -0.4), Color(1.0, 0.4, 0.35), 1.3)
	FX.anim("solar_shrapnel", center(), 0.0, 0.7, Color(1.0, 0.5, 0.4))
	FX.blood(center(), Vector2(kdir, -0.6), Color(0.75, 0.12, 0.14), 9)
	Game.shake(5.0)
	Game.kick(Vector2(kdir, -0.3), 6.0)
	Game.hitstop(0.07)
	Game.slowmo(0.5, 0.12)
	if level:
		level.flash_red()
	for s in ["melee", "second"]:
		if slot(s).get("flaw", "") == "lanetli":
			kut *= 0.5
	if float(Game.run["hp"]) <= 0.0:
		if revive:
			revive = false
			Game.run["hp"] = max_hp() * 0.5
			inv_t = 1.5
			Game.slowmo(0.3, 0.5)
			FX.anim("radiant_heal", global_position, 0.0, 1.6, Color(1.0, 0.95, 0.7))
			FX.soul(center(), Color(1.0, 0.95, 0.7), 30)
			FX.flash_light(center(), Color(1.0, 0.95, 0.7), 240.0, 2.2, 0.6)
			FX.text(center() + Vector2(0, -36), "UMAY SENİ GERİ ÇAĞIRDI", Color(1.0, 0.95, 0.7), 10)
			return true
		Game.run["hp"] = 0.0
		_die()
	return true


func _parry(sh: Dictionary, from: Node, projectile: Node) -> void:
	inv_t = 0.25
	Game.hitstop(0.1)
	Game.slowmo(0.3, 0.25)
	Game.shake(3.0)
	Game.kick(Vector2(-facing, 0), 4.0)
	FX.ring(center() + Vector2(facing * 12, 0), 26, Color(1.0, 0.9, 0.5), 0.3)
	FX.impact(center() + Vector2(facing * 12, 0), Vector2(facing, 0), Color(1.0, 0.95, 0.6), 2.0)
	FX.sparks(center() + Vector2(facing * 12, 0), Vector2(facing, -0.5), Color(1.0, 0.95, 0.6), 14, 240.0)
	FX.flash_light(center() + Vector2(facing * 12, 0), Color(1.0, 0.9, 0.5), 180.0, 2.2, 0.25)
	FX.anim("arcane_parry", center() + Vector2(facing * 10, 0), 0.0, 1.0, Color(1.0, 0.95, 0.6))
	FX.text(center() + Vector2(0, -30), "SAVUŞTURMA", Color(1.0, 0.9, 0.5), 9)
	vis_scale = Vector2(0.88, 1.1)
	add_kut(15)
	var mv := float(sh.get("mech_v", 1.0))
	match sh.get("mech_id", ""):
		"sersemlet":
			if from and from.has_method("stun"):
				from.stun(mv)
		"hayalet_kartal":
			var p := Projectile.new()
			p.team = "p"
			p.kind = "eagle"
			p.position = center()
			p.velocity = Vector2(facing * 260, -60)
			p.homing = 6.0
			p.pierce = 2
			p.trail_col = Color(0.5, 0.95, 1.0)
			p.on_hit = func(e: Node) -> void:
				_deal(e, 10.0 * mv / 100.0 * (1.0 + 0.6 * float(sh["tier"])), slot(mel_slot), {"kb": 120.0, "dir": facing, "scale_item": sh})
			level.add_projectile(p)
			if from and from.has_method("stun"):
				from.stun(0.6)
		"yansit":
			if from and from.has_method("stun"):
				from.stun(0.5)
		"sifa":
			heal(mv)
		"ates_puskur":
			level.fire_pool(global_position + Vector2(facing * 36, 0), 30.0, mv, 4.0)
			FX.anim("ember_jet", center() + Vector2(facing * 20, 0), 0.0 if facing > 0 else PI, 1.0, Color(1.0, 0.7, 0.3))
	if projectile and is_instance_valid(projectile):
		projectile.reflect(facing, mv / 100.0 if sh.get("mech_id", "") == "yansit" else 1.5)
	var hp_back := ItemGen.aff(sh, "blok_can")
	if hp_back > 0:
		heal(hp_back)


func _lightning_dash(it: Dictionary, held: float) -> void:
	## Yıldırım Kılıcı: basılı tutma süresine göre 60-100% menzil; lunge animasyonuyla delici hamle
	var mv := float(it.get("mech_v", 150.0))
	var px := mv * (0.6 + 0.4 * clampf((held - 0.2) / 0.6, 0.0, 1.0))
	var c := {"s": "lunge", "mult": 1.4, "kb": 60.0, "last": true}
	var sw: Dictionary = SWINGS["lunge"]
	# süre: hamle 1100 px/sn; vuruş fazı bu mesafeyi alacak kadar
	var dur := (px / 1100.0) / (float(sw["hit"][1]) - float(sw["hit"][0]))
	atk = {"step": 0, "c": c, "sw": sw, "phase": "wind", "t": dur * 0.24, "dur": dur, "hit": [], "item": it, "hold": 0.0, "dash_px": px, "pause": false, "multi_i": 0}
	combo_step = 0
	vis_scale = Vector2(0.85, 1.12)
	FX.anim("electric_impact", center(), 0.0, 0.9, Color(0.6, 0.85, 1.0))
	Game.hitstop(0.05)
	Ses.play("yildirim", -2.0)


func _throw_axe(it: Dictionary) -> void:
	if axe_out:
		return
	axe_out = true
	var p := Projectile.new()
	p.team = "p"
	p.kind = "axe"
	p.atlas_item = "savas_baltasi"
	p.atlas_mat = it["material"]
	p.position = global_position + Vector2(facing * 10, -30)
	p.velocity = Vector2(facing * 400, 0)
	p.pierce = 99
	p.life = 4.0
	p.return_px = float(it.get("mech_v", 120.0))
	p.owner_node = self
	p.trail_col = weapon_color(it)
	var ret_mult := 1.0 + float(it.get("mech_v", 120.0)) / 100.0 * 0.3
	p.on_hit = func(e: Node) -> void:
		_deal(e, float(it["dmg"]) * (ret_mult if p.returning else 1.0), it, {"kb": 110.0, "dir": signf(p.velocity.x), "axe_return": p.returning})
	level.add_projectile(p)
	vis_scale = Vector2(1.1, 0.92)
	Game.kick(Vector2(-facing, 0), 2.0)


func _arrow_rain(x: float, ground_y: float, dur: float, dmg: float, it: Dictionary) -> void:
	var n := int(dur / 0.12)
	for i in n:
		await get_tree().create_timer(0.12).timeout
		if level == null or not is_inside_tree():
			return
		var a := Projectile.new()
		a.team = "p"
		a.kind = "arrow"
		a.position = Vector2(x + randf_range(-44, 44), ground_y - 200)
		a.velocity = Vector2(randf_range(-20, 20), 520)
		a.gravity = 0.0
		a.life = 1.0
		a.trail_col = Color(1.0, 0.9, 0.6)
		a.on_hit = func(e: Node) -> void:
			e.take_hit(dmg, {"kb": 20.0, "dir": signf(e.center().x - x), "crit": randf() < 0.1})
		level.add_projectile(a)


func _cast_magic(it: Dictionary) -> void:
	Ses.play("buyu", -4.0)
	var mv := float(it.get("mech_v", 3))
	var power := Game.item_mult(it)
	cd[sec_slot] = 1.0 / float(it["aps"])
	cd_max[sec_slot] = cd[sec_slot]
	cast_t = 0.35
	anim.show_frame("cast", 1)
	vis_scale = Vector2(0.94, 1.06)
	match it["id"]:
		"kam_kopuzu":
			var p := Projectile.new()
			p.team = "p"
			p.kind = "wave"
			p.position = global_position + Vector2(facing * 12, -28)
			p.velocity = Vector2(facing * 280, 0)
			p.pierce = 99
			p.life = 1.2
			p.on_hit = func(e: Node) -> void:
				_deal(e, float(it["dmg"]), it, {"kb": 70.0, "dir": facing})
			level.add_projectile(p)
			FX.anim("hush_lock", global_position + Vector2(facing * 14, -28), 0.0, 0.8, Color(0.7, 0.9, 1.0))
		"gok_asasi":
			var hit: Array = []
			var from_pos := center() + Vector2(facing * 10, -4)
			var cur := from_pos
			var dmg_k := 1.0
			for i in int(mv):
				var best: Node = null
				var bd := 170.0 if i == 0 else 120.0
				for e in get_tree().get_nodes_in_group("dusman"):
					if is_instance_valid(e) and not e.dead and not hit.has(e):
						var d: float = cur.distance_to(e.center())
						if d < bd and (i > 0 or signf(e.center().x - center().x) == facing):
							bd = d
							best = e
				if best == null:
					break
				hit.append(best)
				FX.lightning(cur, best.center(), Color(0.7, 0.85, 1.0))
				FX.anim("electric_impact", best.center(), 0.0, 0.8, Color(0.7, 0.85, 1.0))
				_deal(best, float(it["dmg"]) * dmg_k, it, {"kb": 40.0, "dir": signf(best.center().x - cur.x), "stun": 0.25})
				cur = best.center()
				dmg_k *= 0.85
			if hit.is_empty():
				FX.lightning(from_pos, from_pos + Vector2(facing * 120, randf_range(-30, 30)), Color(0.7, 0.85, 1.0, 0.6))
			FX.flash_light(from_pos, Color(0.7, 0.85, 1.0), 180.0, 1.8, 0.2)
			Game.hitstop(0.04)
		"yel_borusu":
			FX.anim("leaf_gust", global_position + Vector2(facing * 40, -26), 0.0 if facing > 0 else PI, 1.3, Color(0.85, 1.0, 0.85))
			FX.dust(global_position + Vector2(facing * 30, -10), Vector2(facing, -0.2), 10, 0.36)
			Game.kick(Vector2(-facing, 0), 3.0)
			for e in get_tree().get_nodes_in_group("dusman"):
				if not is_instance_valid(e) or e.dead:
					continue
				var to: Vector2 = e.center() - center()
				if signf(to.x) == facing and absf(to.x) < 110.0 and absf(to.y) < 60.0:
					var walled: bool = level.solid_at(e.center() + Vector2(facing * mv * 0.5, 0))
					e.take_hit(float(it["dmg"]) * power, {"kb": mv * 3.0, "dir": facing, "launch": 100.0, "walled": walled, "stagger": true})
					if walled:
						FX.impact(e.center() + Vector2(facing * 10, 0), Vector2(facing, 0), Color(0.9, 1.0, 0.9), 1.2)


func _die() -> void:
	dead = true
	anim.play("hurt")
	_end_trail()
	Ses.play("bengu_olum", 0.0)
	Game.slowmo(0.3, 0.8)
	FX.anim("void_implosion", center(), 0.0, 1.4, Color(0.6, 0.9, 1.0))
	FX.soul(center(), Color(0.55, 0.95, 1.0), 40)
	FX.burst(center(), Color(0.55, 0.95, 1.0), 30, 160, 1.2, 0.3, -40, true)
	FX.flash_light(center(), Color(0.55, 0.95, 1.0), 220.0, 2.0, 0.8)
	if level:
		level.on_player_died()
