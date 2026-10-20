class_name Player
extends CharacterBody2D
## Bengü: hareket hissi (squash & stretch, eğilme, toz, coyote/apex), silah başına özgün kombolar,
## kılıç izi ve darbe efektleri, yay/fırlatma, kalkan, teçhizat, şişe, Kut gücü, tünel yuvarlanması.

const RUN := 155.0
const ACC_GROUND := 2600.0
const DEC_GROUND := 2400.0
const ACC_AIR := 2400.0     # v34: 1500 → 2400 (havada güçlü yön verme)
const JUMP_V := -565.0      # v34: -430 → -565 (tepeye ~0,3 sn; eski 0,4)
const GRAV := 1180.0        # yuvarlanma / sürünme / ölüm / sanatlar (zıplama yayı GRAV_RISE / GRAV_FALL ile)
const MAX_FALL := 620.0     # v34: 560 → 620
const ROLL_V := 300.0
const ROLL_T := 0.3

## ------------------------------------------------------------------ v34 ZIPLAMA (Dead Cells usulü)
## Geri bildirim: "Zıplama çok hantal; basamak çıkmak yorucu." Yükseliş hızlı ve kısa, tepede kısa asılı kalış, düşüş
## yükselişten sert (yerçekimi ayrı), havada güçlü yön verme, tuşu erken bırakınca alçak zıplama. 1 karoluk basamağa
## yürüyünce kendiliğinden çıkılır; 2-3 karoluk kenara zıplayınca eller yetişince otomatik tutunulur (hızlı tırmanış).
## Tepe yüksekliği ≥ eski (LevelGen._moves modeli: tek / çift zıplama 4 karo yukarı, ±5 sütun).
const GRAV_RISE := 1950.0       # yükselirken (tuş basılı)
const GRAV_FALL := 2100.0       # düşerken (eski: her iki yönde 1180)
const JUMP_CUT := 0.5           # yükselirken tuş bırakılırsa hız bu orana iner (alçak zıplama)
const APEX := {"vy": 60.0, "g": 0.6}     # tepe: |vy| < 60 iken tuş basılıysa yerçekimi %60 (kısa asılı kalış)
const TURN_AIR := 1.5           # havada ters yöne basınca ivme çarpanı (keskin dönüş)
const STEP_UP := 28.0           # yürürken kendiliğinden çıkılan basamak (px; 1 karo = 24)
const LEDGE_UP := 60.0          # havada tutunulan kenar: ayak hizasının en çok bu kadar üstü (eller)
## v34 birleştirme: platformdan inişte (aşağı + zıpla, drop_t = 0,25) tek yönlü platform çarpışması yalnız ilk 0,1 sn
## kapalı (drop_t > DROP_MASK). Eskiden 0,25 sn boyunca kapalıydı: v34 düşüş yerçekimiyle (2100) bu sürede ~65 px
## (2,7 karo) düşülüyor, 2 karo alttaki platform (kuyu tırmanış bacasının ara basamağı) da geçiliyordu; erişim modeli
## (LevelGen._moves: dikine iniş ilk tutunulacak yere dek) ile gerçek oyuncu ayrışıyordu. 0,1 sn ~12 px: üstünde
## durulan platformdan (6 px kalın) geçmeye yeter. Kalan süre (drop_t) yalnız Kahraman İnişi'ni engeller.
const DROP_MASK := 0.15
## Kahraman İnişi (havada S + Boşluk): hızla çakılır, yere değince şok dalgası (yükseklikle güçlenir); düşüş
## sersemlemesi / hasarı yok. Yüksek normal düşüş (> stun_h px) kısa sersemletir, çok yüksekte (> dmg_h) az hasar.
## v34 birleştirme: stun_h 12 -> 17 karo, dmg_h 18 -> 23 karo. Bölüm kuyuları 10-15 karo (ana yolda %76 bölümde 13-15
## karoluk düşüş vardı: oyuncu her bölümde zorla sersemliyordu); artık ana yoldan yürüyerek düşen sersemlemez, yalnız
## yolun dışındaki çok yüksek düşüşte (ya da derin kuyuya zıplayarak girince) sersemler.
const HERO := {"antic": 0.06, "v": 880.0, "v_max": 1150.0, "acc": 2600.0, "steer": 0.25, "r": 56.0, "r_k": 44.0,
	"pose": 0.32, "stun_h": 408.0, "stun_t": 0.45, "dmg_h": 552.0, "dmg_k": 0.05, "dmg_stun_t": 0.6}
## kol pozları [a1 üst kol, a2 dirsek, w bilek, k derinlik, ext uzatma] (SWINGS ile aynı açı düzeni: 0 aşağı, pi/2 ileri)
const HERO_POSE_DIVE := [2.75, 0.35, 0.55, 1.0, 1.0]
const HERO_POSE_LAND := [0.42, 0.0, -3.0, 1.0, 1.25]   # yumruk yerde, bıçak geriye-yukarı

## ------------------------------------------------------------------ AKICILIK (v17)
## Dövüşün "akışı": girdi ara belleği, iptal pencereleri, saldırırken hareket, hedef yardımı, vuruş duraklaması.
## Ölçüm: tools/tests/dovus_testi.gd (-- --dovus). Süreler saniye, mesafeler piksel.
const FLOW := {
	# --- ara bellek (v22, Dead Cells usulü): savuruş yokken / toparlanmada basış 0,12 sn saklanır. Savuruş sürerken
	# yalnızca SON ANINDA (zincir noktasına "buf_melee_late" sn kala; çoğu silahta temastan sonraki kilit) yapılan basış
	# kuyruğa girer ve toparlanmanın ilk karesinde çıkar; hazırlıkta / süpürmede yapılan erken basış yok sayılır (eskiden
	# 0,3 sn saklanıp savuruş boyunca hiç erimiyordu: ağır silahta hazırlıkta basılan tuş ~0,5 sn sonra kendiliğinden
	# yeni bir savuruş çıkarıyordu). Kuyrukta en çok bir savuruş durur.
	"buf_melee": 0.12,
	"buf_melee_late": 0.16,
	# temastan sonra (bıçak düşmana varıp süpürme bittikten sonra, kilitte: isabeti görüp basınca, Kut Yankısı zamanlaması)
	# yapılan basış her zaman kuyruğa girer; kilit en uzun dev silah bitirişinde ~0,33 sn
	"buf_jump": 0.15,         # eski 0,13
	"coyote": 0.125,          # eski 0,09; v34 0,11 → 0,125 (kenardan 6 kare / 0,1 sn sonra da zıplanır)
	"buf_roll": 0.2,          # yuvarlanma basışı (yuvarlanma / bekleme sürerken basılırsa biter bitmez)
	"buf_sec": 0.15,          # yay / fırlatma / büyü / kalkan: saldırı toparlanmasında basılırsa saldırıyı keser (v22: 0,2 → 0,15)
	"roll_gap": 0.05,         # yuvarlanma bitiminden yenisine bekleme (eski 0,12)
	# --- ağır saldırı: basıştan itibaren bu kadar basılı tutulursa ağır (eski: hazırlık sonu + 0,16 sn bekleme)
	"heavy_hold": 0.3,        # v22: 0,2 → 0,3 (250-280 ms'lik "biraz uzun" dokunuş ağır saldırıya dönüyordu)
	"heavy_nowait_w": 0.5,    # bu ağırlığa dek (hançer, düellocu, kırbaç, v18: kılıç, pala, mızrak) hafif vuruş hiç
	                          # bekletilmez; tuş basılı kalırsa ağır şarj toparlanmadan açılır
	# --- yuvarlanma → saldırı (kaçış saldırısı)
	"roll_atk_k": 0.45,       # yuvarlanmanın bu oranından sonra saldırı basışı yuvarlanmayı keser
	"roll_atk_inv": 0.1,      # kesilince dokunulmazlık bu kadar daha sürer
	"roll_atk_win": 0.18,     # yuvarlanma bitiminden sonra Dönüş Kesiği penceresi (v22: 0,32 → 0,18)
	# --- zıplama iptali: hazırlığın bu oranına dek zıplama saldırıyı keser (süper zırhlı savuruş kesilmez);
	# vuruş anında basılan zıplama toparlanmada çıkar
	"jump_cancel_k": [1.0, 0.75, 0.4],   # [hafif ≤0,3, orta ≤0,65, ağır] silah ağırlığı
	# --- saldırırken hareket: yerde sürtünme (eski: hedef hız 0, 2400 px/sn² ile ~65 ms'de dururdu)
	"atk_fric": 1100.0,
	"atk_fric_heavy": 1500.0,
	"step": [7.0, 9.0],       # vuruş anı öne adım (hafif, ağır); + adımın "dash" değeri × step_dash
	"step_dash": 0.38,
	"air_ctrl": 0.6,          # havada saldırırken yön tuşu (koşu hızının oranı)
	"air_acc": 950.0,
	# --- v22: hedef yardımı kalktı (düşmana dönme ve düşmana doğru uzayan adım yok; yön oyuncunun). assist_dy yalnızca
	# dibindeki düşmanın içinden geçmemek için adımın kısaltılmasında ve infaz hedefinde dikey yakınlık.
	"assist_dy": 44.0,
	# --- vuruş hissi: aynı savuruşta ikinci, üçüncü düşman duraklamayı / kamera itişini yeniden vermez
	"hs_extra": 0.008,        # her ek düşman için duraklama artışı
	"hs_light_min": 0.75,     # hafif vuruş duraklaması hançerde bu orana iner (ağırlıkla ölçeklenir)
}

## ------------------------------------------------------------------ TEMPO (v18, Dead Cells esinli)
## Savuruş süresi artık "1 / aps"in sabit oranlara bölünmesi değil: her silah sınıfının üç evresi gerçek saniye olarak
## tanımlı ve savuruş anahtarları (SWINGS, normalize k) bu evrelere zaman bükmesiyle oturur (_atk_advance):
##   hazırlık  0 → hit[0]   (ilk vuruş / zincir içi ayrı: zincirde kol önceki vuruşun takibinden doğrudan gerilir)
##   vuruş     hit[0] → hit[1]   (yay 2-4 karede geçer; isabet "ck" temas anında başlar; sonunda zincir / iptal açılır)
##   toparlanma hit[1] → 1   (yalnızca girdi yoksa görünür; yürüme, zıplama, yuvarlanma, saldırı keser)
## Dead Cells wiki'sinin silah verisi (ItemDetails: "charge" basıştan vuruşa, "lock" vuruştan sonraki girdiye kadar):
## Balanced Blade 0,07-0,10 / 0,05-0,15 sn, bitiriş 0,30 / 0,30; Rapier 0,1 / 0; War Spear 0,1-0,38 / 0-0,2;
## Wrenching Whip 0,2 / 0,1; Nutcracker 0,4-0,5 / 0,1-0,2; Broadsword 0,4-0,5 / 0,2-0,4. Bizimki aynı ölçekte:
## Sütunlar (sn): [basış→temas (ilk), basış→temas (zincir), süpürme (bıçağın son hızlı yayı, temasa dek),
##                 kilit (temastan zincire / iptale), toparlanma (girdisiz kuyruk), hazırlık tutuşu (ilk), tutuş (zincir)]
## Hazırlık = basış→temas − süpürme − tutuş. Evre sınırları savuruşta: 0 → hit[0] hazırlık, hit[0] → ck süpürme,
## ck → hit[1] kilit (isabet penceresi ck'de açılır), hit[1] → 1 toparlanma.
const TEMPO := {
	"hancer": [0.067, 0.05, 0.025, 0.067, 0.12, 0.0, 0.0],      # ikiz bıçak, böri, pençe, ay palası: ~7,5 vuruş/sn
	"duello": [0.083, 0.067, 0.03, 0.083, 0.13, 0.0, 0.0],      # yatağan, rüzgâr kılıcı
	"kilic": [0.1, 0.083, 0.033, 0.1, 0.15, 0.017, 0.0],        # alp, pala, ruh, yılan, ayaz, yıldırım
	"mizrak": [0.117, 0.083, 0.033, 0.083, 0.15, 0.017, 0.0],   # kargı, tulpar: saplama dizisi
	"kirbac": [0.15, 0.117, 0.033, 0.1, 0.16, 0.017, 0.0],      # kement, od kamçısı
	"uzun": [0.167, 0.133, 0.04, 0.117, 0.18, 0.033, 0.0],      # teber, tırpan, kayın asası
	"agir": [0.25, 0.2, 0.05, 0.15, 0.22, 0.05, 0.017],         # gürz, topuz, balta, ikiz balta
	"dev": [0.33, 0.267, 0.05, 0.2, 0.28, 0.067, 0.033],        # ulu kılıç, dağ / kor çekici, bozgun kılıcı
}

## ------------------------------------------------------------------ TEMPO v20: biraz daha ağır kombolar
## Geri bildirim: "kombolar çok hızlı oldu, biraz yavaşlatalım; kombo güzel görünüyor." Savuruş biçimleri, iptaller ve ara
## bellekler aynı; yalnızca evre süreleri uzar. Yanıt verme önce: ilk hazırlık (basış→temas) çok az uzar, uzayan asıl
## zincir aralığıdır (kilit + zincir hazırlığı). Süpürme (bıçağın 2-3 karelik son yayı, smear karesi) hiç değişmez:
## kombonun "görünüşü" odur.
## Tek düğme: TEMPO_YAVAS. Her evrenin çarpanı 1 + TEMPO_YAVAS × pay; 0 = v19 temposu, 1 = v20, 1,5 = daha da ağır.
## Sınıf payları (TEMPO_V20): [ilk hazırlık, zincir hazırlığı, süpürme, kilit, toparlanma]; hafif / orta silahta zincir
## aralığı ~%15-18, ağır ~%7, dev ~%6 uzar (ölçüm: docs/TASARIM.md "v20").
const TEMPO_YAVAS := 1.0
const TEMPO_V20 := {
	"hancer": [0.05, 0.15, 0.0, 0.25, 0.15],
	"duello": [0.05, 0.15, 0.0, 0.22, 0.15],
	"kilic": [0.05, 0.15, 0.0, 0.22, 0.15],
	"mizrak": [0.05, 0.15, 0.0, 0.22, 0.15],
	"kirbac": [0.05, 0.12, 0.0, 0.2, 0.12],
	"uzun": [0.04, 0.12, 0.0, 0.18, 0.12],
	"agir": [0.03, 0.06, 0.0, 0.1, 0.08],
	"dev": [0.0, 0.06, 0.0, 0.1, 0.06],
}

## ------------------------------------------------------------------ TEMPO v25: ağır tempo
## Geri bildirim (oynayarak): "Saldırı hızı hâlâ çok yüksek; özellikle küçük kılıç ve hançerler ışık hızında. Dövüştüğümüzü
## hissetmeliyiz." v20'nin üstüne sınıfa göre ikinci bir yavaşlama: hafif silah en çok, ağır en az (hançer / ikiz bıçak
## zincir aralığı ~+%50, düello ~+%45, kılıç ~+%35, mızrak / kırbaç / uzun sap ~+%25, ağır / dev ~+%12). Yalnızca
## sürelerin uzaması değil, savuruşa ağırlık: hazırlık uzar ve her savuruşta okunur bir HAZIRLIK TUTUŞU (bıçak geride bir
## an durur, gövde toplanır) eklenir, süpürme 2-3 kareye çıkar (bıçak "ışınlanmaz", yayı görünür), kilit (temastan sonraki
## oturma) uzar, girdisiz toparlanma (takip pozu) biraz daha görünür. Tek düğme TEMPO_AGIR (0 = v24 temposu, 1 = v25).
## Sütunlar: [ilk hazırlık ×, zincir hazırlığı ×, süpürme ×, kilit ×, toparlanma ×, + tutuş ilk (sn), + tutuş zincir (sn)]
const TEMPO_AGIR := 1.0
const TEMPO_V25 := {
	"hancer": [1.6, 2.0, 1.3, 1.2, 1.2, 0.017, 0.017],
	"duello": [1.5, 1.8, 1.25, 1.2, 1.2, 0.017, 0.017],
	"kilic": [1.35, 1.5, 1.2, 1.18, 1.15, 0.017, 0.017],
	"mizrak": [1.2, 1.4, 1.15, 1.18, 1.1, 0.012, 0.012],
	"kirbac": [1.15, 1.3, 1.12, 1.22, 1.1, 0.012, 0.012],
	"uzun": [1.12, 1.32, 1.1, 1.26, 1.1, 0.012, 0.012],
	"agir": [1.05, 1.12, 1.05, 1.12, 1.05, 0.008, 0.008],
	"dev": [1.03, 1.1, 1.05, 1.13, 1.05, 0.01, 0.01],
	# silaha özgü (sınıfın yerine): Ay Palası beşli zincirde her adım hızlanır (Ay Dansı); taban daha ağır
	"ay_palasi": [1.6, 2.4, 1.3, 1.4, 1.2, 0.017, 0.017],
}
## v25: ikiz bıçağın zincir boyunca hızlanması (adım başına; eski 0,07: dördüncü vuruş %21 hızlıydı); v26 0,04 → 0,025
const DUAL_RAMP := 0.025

## ------------------------------------------------------------------ TEMPO v26: daha da yavaş
## Geri bildirim (v25'i oynayarak): "Saldırı hızı ve kritik oranı hâlâ çok yüksek." v25'in üstüne üçüncü katman: hafif /
## orta silahlarda (hançer, ikiz bıçak, düello, kılıç) zincir aralığı ve kilit ~%25-30, mızrak / kırbaç / uzun sap
## ~%12, ağır / dev ~%5 daha uzun. Basış→temas (ilk hazırlık) yalnızca az uzar: tepki aynı, oturma ve yeniden gerilme
## uzar (vuruş "ağır" okunur). Tek düğme TEMPO_V26K (0 = v25 temposu, 1 = v26). Sütunlar TEMPO_V25 ile aynı.
const TEMPO_V26K := 1.0
const TEMPO_V26 := {
	"hancer": [1.1, 1.3, 1.08, 1.25, 1.2, 0.008, 0.01],
	"duello": [1.1, 1.36, 1.08, 1.3, 1.22, 0.008, 0.012],
	"kilic": [1.08, 1.32, 1.06, 1.28, 1.2, 0.008, 0.01],
	"mizrak": [1.03, 1.13, 1.02, 1.13, 1.08, 0.0, 0.006],
	"kirbac": [1.03, 1.14, 1.02, 1.14, 1.08, 0.0, 0.006],
	"uzun": [1.03, 1.14, 1.02, 1.14, 1.08, 0.0, 0.006],
	"agir": [1.02, 1.06, 1.0, 1.06, 1.04, 0.0, 0.004],
	"dev": [1.02, 1.05, 1.0, 1.06, 1.04, 0.0, 0.004],
	"ay_palasi": [1.1, 1.26, 1.08, 1.22, 1.2, 0.008, 0.01],
}

## ------------------------------------------------------------------ TEMPO v34: ağır silahın hazırlığı kısalır
## Geri bildirim (oynayarak): "Bazı iki elli kılıçların ve büyük çift ağızlı ağır silahların savuruşu o kadar yavaş ki
## sinir bozuyor." Dead Cells'in ağır silahları gibi: ağırlık yavaşlıktan değil darbeden gelir. Basış→temas (hazırlık +
## tutuş) en çok kısalır (en ağırda ~0,49 → ~0,3 sn), süpürme (görünüş) aynı, kilit / toparlanma biraz kısalır;
## zincir ilerledikçe savuruş hızlanır (adım başına "ramp"); hazırlıkta süper zırh (sarsılmaz, yine de zıplamayla
## kesilir); vuruş duraklaması ve öne adım biraz büyür (V34_AGIR). Hasar, saniyedeki hasar eski düzeyde kalsın diye
## items.json'da indirildi (docs/TASARIM.md "v34"). Tek düğme TEMPO_V34K (0 = v33 temposu, 1 = v34).
## Sütunlar: [ilk hazırlık ×, zincir hazırlığı ×, süpürme ×, kilit ×, toparlanma ×, tutuş ×, adım başına hızlanma,
##            bitiriş hazırlığı ×]
const TEMPO_V34K := 1.0
const TEMPO_V34 := {
	"uzun": [0.82, 0.88, 1.0, 0.95, 0.9, 0.8, 0.04, 0.95],
	"agir": [0.66, 0.75, 1.0, 0.9, 0.85, 0.65, 0.06, 0.9],
	"dev": [0.62, 0.7, 1.0, 0.85, 0.8, 0.55, 0.07, 0.85],
	"gun_ay_ikizi": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 1.0],   # iki duruşlu (Ay duruşu düellocu): dokunulmadı
}
## hs: orta kademe vuruş duraklaması çarpanı, step: vuruş anı öne adım (px; eski 9), sa_wind: hazırlıkta süper zırhlı
## sınıflar, sarj_k: items.json'da hasar ~%10-25 indiği için basılı tutulan (şarjlı) ağır vuruşun çarpanı (şarj süresi
## kısalmadı; ağır vuruş eski hasarında kalır)
const V34_AGIR := {"hs": 1.2, "step": 13.0, "sa_wind": ["agir", "dev"], "sarj_k": {"dev": 1.33, "agir": 1.27, "uzun": 1.1}}
## v35 sanatsal kombolar: tutarlı vuruş duraklaması kademeleri (sn; ağır / dev ×V34_AGIR.hs, öldürüş +0,02, en çok 0,12)
## hafif ara vuruş · orta (ağır silah ara vuruşu, büyük itiş) · zincir bitirişi · kritik eki. Bitiriş gösterisi
## (KesikFX hüsnühat kesiği + mürekkep dikenleri, yakınlaşma, yönlü sarsıntı, darbe karesi) yalnızca bitirişte;
## ara vuruşlar sade ve keskin. Bitiriş izi ×fin_iz, sınıf iz eni (hançer / mızrak izleri okunur olsun).
const V35 := {"hs_hafif": 0.03, "hs_orta": 0.05, "hs_bitiris": 0.09, "hs_krit": 0.03, "hs_olum": 0.02,
	"fin_zoom": 0.05, "fin_zoom_agir": 0.025, "fin_sarsinti": 0.32, "fin_itis": 5.0, "fin_firlat": 150.0,
	"olum_yavas": [0.35, 0.12], "fin_iz": 1.15, "iz_sinif": {"hancer": 1.2, "mizrak": 1.15, "duello": 1.1}}

## ------------------------------------------------------------------ SALDIRI HIZI (v20)
## Oyuncu statı (yüzde): evre sürelerini (hazırlık, süpürme, kilit, toparlanma, tutuş) ve dolayısıyla zincir aralığını
## 1 / (1 + hız × sınıf etkisi) oranında kısaltır. Kaynaklar (hiz_kaynak):
##   silah   yakın silahın kendi "hiz" niteliği (Çevik, +%6-20; yalnız o silah için)
##   techizat  kalkan / teçhizat "saldiri_hizi" niteliği (Tez Elli, +%4-10; kuşanılan her eşya toplanır)
##   kurt    Kurt ongunu: tılsım seviyesi başına +%2 (koşu içinde kazanılır)
##   lutuf   Yel Ana'nın Soluğu (tanrı sunağı): +%15, bir sonraki konağa dek (v32; eskiden yurda dönene dek)
##   umay    Kam Davulu (Umay Ana, kalıcı): seviye başına +%4
## Kalıcı kaynaklar toplamı "cap" ile sınırlı; Kızışma yükleri bunun üstüne eklenir, hepsi "cap_all"da durur. Ağır
## silahlarda etkisi azalır ("sinif"); hiçbir evre "min_*" karesinin altına inmez (vuruş okunur kalsın). Yaylarda gerilme,
## en kısa bırakış ve atış kilidi "yay" oranında, fırlatma / büyü beklemesi "atis" oranında kısalır.
## KIZIŞMA (silah pasifi, items.json "kizisma"): her isabet (savuruş geçişi başına bir) bir yük ve yük başına +%kz_v
## saldırı hızı verir (en çok kz_max); "kz_decay" sn vuruşsuz kalınca ya da hasar alınca söner. Kolda incelen mürekkep
## hız çizgileri, HUD'da yuvanın üstünde yük taneleri, savuruş sesi incelir, tam yükte altın parıltı.
## v25: "ışık hızı" geri gelmesin: üst sınırlar %40 / %60 → %25 / %35, kaynaklar küçüldü, sınıf etkisi hafif silahta
## da 1'in altında (hançer 1,0 → 0,7: zaten en kısa evreler oransal kısalmayla en çok hızlanıyordu), en az kareler arttı.
## v26: yine geri gelmesin: üst sınırlar %25 / %35 → %18 / %25, Kurt ongunu 1,5 → 1, Yel Ana 10 → 7, Kam Davulu 3 → 2;
## sınıf etkisi ~%20 düştü (hançer 0,7 → 0,55). En hızlı birikim (bütün kaynaklar + tam Kızışma) zincir aralığını en çok
## ~%12 kısaltır (v25 ~%20).
const HIZ := {
	"cap": 18.0,
	"cap_all": 25.0,
	"kurt": 1.0,
	"lutuf": 7.0,
	"umay": 2.0,
	"sinif": {"hancer": 0.55, "duello": 0.6, "kilic": 0.7, "mizrak": 0.7, "kirbac": 0.65, "uzun": 0.6, "agir": 0.55, "dev": 0.45},
	"min_wind": 0.05,       # hazırlık en az 3 kare (taban zaten kısaysa tabanın altına inmez)
	"min_sweep": 0.025,     # süpürme en az 1,5 kare
	"min_lock": 0.067,      # kilit en az 4 kare
	"yay": 0.6,
	"atis": 0.8,
	"kz_decay": 1.8,
	"kz_pitch": 0.08,       # tam yükte savuruş sesi bu oranda incelir
}

## ------------------------------------------------------------------ SAVURUŞLAR
## Ön kol ve silah oyunda sürülür. Anahtar: [t, a1, a2, w, k, ext, ease]
##   a1 üst kol açısı, a2 dirsek bükümü, w bilek (silahın ön kola göre açısı); 0 aşağı, pi/2 ileri, pi yukarı
##   k  yatay derinlik kısalması (1 = yan görünüş; küçük = kola/silaha kameraya doğru bakıyor)
##   ext ön kol uzatması (darbe anındaki abartı), ease: 0 yumuşak, 1 hızlanarak (vuruş), 2 yavaşlayarak (takip)
## Hazırlık yavaş, vuruş çok hızlı (kareler arası 1-2 ara örnek), takip ağırlıkla yavaşlar.
## v15 alanları: "hold_k" hazırlık tutuşu / şarj pozunun k noktası (sıçramalı gövdelerde havadaki kare yerine çömelme
## karesi tutulsun diye), "around" iki yan, "multi" çoklu vuruş anları.
## v18 alanları (süre artık TEMPO'dan, "tm" kalktı): "ck" temas anahtarı (isabet ve süpürme sonu), "ws" hazırlık, "ss" kilit
## (çark / çok vuruşlu savuruşta yay bu evrede döner), "ms" süpürme, "rs" toparlanma çarpanları. Kalıp: dinlenme →
## hazırlık (yavaşlayarak oturur) → derin hazırlık (tutuş) → temas (kare hızlanma, 2-3 kare) → takip (kilidin ilk
## yarısında aşar) → oturma (kilidin sonu) → dinlenme. Zincirde ilk bölüm önceki savuruşun son pozundan başlar
## (_atk_pose); zincirler bir vuruşun bittiği yerden ötekinin hazırlığı başlayacak biçimde dizildi (iniş → yükseliş →
## baş üstü). v23: açılar artık savuruşun eğik 3B DÜZLEMİNDE (PLANES); yatay savuruşlardaki "k 0,22 + tek karede
## açı sıçraması" hilesi kalktı: bıçak düzlemde sürekli döner, kameraya dönen kısımda izdüşüm onu kendiliğinden kısaltır.
const SWINGS := {
	# yukarıdan aşağı: kılıç sırtın arkasına çekilir, baş üstünden öne-aşağı iner
	"down": {"body": "atk_down", "hit": [0.3, 0.56], "ck": 0.42, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, 3.2, 0.7, 0.8, 1.0, 1.0, 2], [0.3, 3.3, 0.75, 0.85, 1.0, 1.0, 0],
		[0.42, 1.3, 0.0, 0.2, 1.0, 1.15, 1], [0.49, 0.6, 0.15, 0.05, 1.0, 1.05, 2], [0.56, 0.588, 0.24, 0.092, 1.0, 1.044, 0],
		[1.0, 0.5, 0.9, 0.4, 1.0, 1.0, 0]]},
	# aşağıdan yukarı: kol aşağı-geride, kılıç önden yukarı fırlar
	"up": {"body": "atk_up", "hit": [0.3, 0.56], "ck": 0.42, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, -0.5, -0.5, -0.4, 1.0, 1.0, 2], [0.3, -0.62, -0.55, -0.45, 1.0, 1.0, 0],
		[0.42, 1.9, 0.0, 0.25, 1.0, 1.12, 1], [0.49, 2.65, 0.1, 0.2, 1.0, 1.05, 2], [0.56, 2.428, 0.196, 0.224, 1.0, 1.044, 0],
		[1.0, 0.8, 0.9, 0.4, 1.0, 1.0, 0]]},
	# soldan sağa (düz el): kol arkada yatay, kameraya doğru kısalarak geçer, önde açılır
	"horiz": {"body": "atk_horiz", "hit": [0.3, 0.56], "ck": 0.42, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, -1.4, -0.25, -0.15, 1.0, 1.0, 2], [0.3, -1.48, -0.3, -0.2, 1.0, 1.0, 0],
		[0.42, 1.55, 0.0, 0.05, 1.0, 1.12, 1],
		[0.49, 1.75, 0.2, 0.2, 1.0, 1.0, 2], [0.56, 1.624, 0.284, 0.224, 1.0, 1.0, 0], [1.0, 0.7, 0.9, 0.4, 1.0, 1.0, 0]]},
	# sağdan sola (ters el): kılıç göğüs önünden omuz üstüne çekilir, ters elle öne savrulur
	"back": {"body": "atk_horiz", "hit": [0.3, 0.56], "ck": 0.42, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, 0.9, 1.9, 1.2, 1.0, 1.0, 2], [0.3, 0.85, 2.0, 1.3, 1.0, 1.0, 0],
		[0.42, 1.6, 0.0, 0.0, 1.0, 1.12, 1],
		[0.49, 1.35, 0.3, -0.25, 1.0, 1.0, 2], [0.56, 1.26, 0.372, -0.184, 1.0, 1.0, 0], [1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# saplama: dirsek geri, el kalçada; ok gibi ileri
	"thrust": {"body": "atk_thrust", "hit": [0.32, 0.56], "ck": 0.4, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, -0.3, 1.9, 0.0, 1.0, 1.0, 2], [0.32, -0.48, 2.05, 0.0, 1.0, 1.0, 0],
		[0.4, 1.55, 0.0, 0.0, 1.0, 1.3, 1], [0.48, 1.5, 0.05, 0.0, 1.0, 1.2, 2], [0.56, 1.392, 0.152, 0.036, 1.0, 1.176, 0],
		[1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# hücum: saplama + gövde ileri fırlar
	"lunge": {"body": "atk_lunge", "hit": [0.3, 0.58], "ss": 1.2, "ck": 0.38, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, -0.4, 2.0, -0.1, 1.0, 1.0, 2], [0.3, -0.55, 2.1, -0.1, 1.0, 1.0, 0],
		[0.38, 1.57, 0.0, 0.0, 1.0, 1.35, 1], [0.48, 1.52, 0.0, 0.0, 1.0, 1.3, 2], [0.58, 1.41, 0.108, 0.036, 1.0, 1.264, 0],
		[1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# ağır iniş (iki el): kol dimdik yukarıda, tüm ağırlıkla yere
	"heavy": {"body": "atk_heavy", "hit": [0.33, 0.62], "ck": 0.45, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.25, 3.3, 0.3, 0.25, 1.0, 1.0, 2], [0.33, 3.45, 0.35, 0.3, 1.0, 1.0, 0],
		[0.45, 0.9, 0.0, 0.0, 1.0, 1.15, 1], [0.535, 0.5, 0.0, -0.1, 1.0, 1.1, 2], [0.62, 0.512, 0.072, -0.064, 1.0, 1.088, 0],
		[1.0, 0.6, 0.6, 0.2, 1.0, 1.0, 0]]},
	# çevrinti: silah gövdenin önünde tam tur döner (iki yanı biçer)
	"spin": {"body": "atk_spin", "hit": [0.3, 0.66], "around": true, "ss": 2.2, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, 0.2, 0.3, 0.1, 1.0, 1.0, 2], [0.3, 0.35, 0.1, 0.0, 1.0, 1.0, 0],
		[0.66, 6.63, 0.0, 0.0, 1.0, 1.12, 0], [1.0, 6.9, 0.9, 0.3, 1.0, 1.0, 0]]},
	# yükselen kesik: çömel, yukarı savur (düşmanı havaya atar)
	"rise": {"body": "atk_uppercut", "hit": [0.3, 0.58], "hold_k": 0.24, "ck": 0.44, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, -0.2, -0.3, -0.6, 1.0, 1.0, 2], [0.3, -0.3, -0.35, -0.65, 1.0, 1.0, 0],
		[0.44, 2.4, 0.0, 0.2, 1.0, 1.15, 1], [0.51, 3.0, 0.05, 0.1, 1.0, 1.08, 2], [0.58, 2.784, 0.152, 0.136, 1.0, 1.07, 0],
		[1.0, 1.2, 0.9, 0.4, 1.0, 1.0, 0]]},
	# seri saplama: üç hızlı saplama (her biri ayrı vuruş)
	"flurry": {"body": "atk_thrust", "hit": [0.14, 0.66], "multi": [0.2, 0.36, 0.52], "ss": 3.0, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.12, -0.3, 1.9, 0.0, 1.0, 1.0, 2], [0.2, 1.55, 0.0, 0.0, 1.0, 1.25, 1],
		[0.28, -0.2, 1.8, 0.1, 1.0, 1.0, 2], [0.36, 1.45, 0.0, -0.05, 1.0, 1.25, 1], [0.44, -0.2, 1.8, 0.0, 1.0, 1.0, 2],
		[0.52, 1.62, 0.0, 0.05, 1.0, 1.3, 1], [0.66, 1.5, 0.05, 0.0, 1.0, 1.2, 2], [1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# zıplayıp ezme: ağır inişin büyük sürümü (sıçrayarak)
	"slam": {"body": "atk_slam_jump", "hit": [0.5, 0.72], "hold_k": 0.24, "ws": 1.6, "ck": 0.6, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.24, 3.3, 0.3, 0.3, 1.0, 1.0, 2], [0.5, 3.55, 0.3, 0.3, 1.0, 1.0, 0],
		[0.6, 0.8, 0.0, -0.05, 1.0, 1.2, 1], [0.66, 0.45, 0.0, -0.15, 1.0, 1.12, 2], [0.72, 0.468, 0.072, -0.108, 1.0, 1.106, 0],
		[1.0, 0.6, 0.6, 0.2, 1.0, 1.0, 0]]},
	# fırlatma (balta)
	"axe": {"body": "atk_throw_axe", "hit": [0.3, 0.4], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.25, 3.4, 0.8, 0.3, 1.0, 1.0, 2], [0.35, 1.4, 0.0, 0.0, 1.0, 1.1, 1],
		[1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# ---------------------------------------------------------------- v5: silaha özgü savuruşlar
	# çapraz iniş: omuzdan kalçaya (sağ üst -> sol alt)
	"diag_down": {"body": "atk_down", "hit": [0.3, 0.55], "ck": 0.42, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, 2.7, 0.5, 0.7, 0.95, 1.0, 2], [0.3, 2.85, 0.55, 0.75, 0.9, 1.0, 0],
		[0.42, 1.1, 0.0, 0.1, 1.0, 1.15, 1], [0.485, 0.35, 0.1, -0.2, 1.0, 1.05, 2], [0.55, 0.368, 0.196, -0.128, 1.0, 1.044, 0],
		[1.0, 0.5, 0.9, 0.4, 1.0, 1.0, 0]]},
	# çapraz yükseliş: kalçadan omuza
	"diag_up": {"body": "atk_up", "hit": [0.3, 0.55], "ck": 0.42, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, -0.35, -0.4, -0.5, 0.95, 1.0, 2], [0.3, -0.45, -0.45, -0.55, 0.9, 1.0, 0],
		[0.42, 1.3, 0.0, 0.15, 1.0, 1.12, 1], [0.485, 2.5, 0.1, 0.3, 1.0, 1.05, 2], [0.55, 2.296, 0.196, 0.312, 1.0, 1.044, 0],
		[1.0, 0.8, 0.9, 0.4, 1.0, 1.0, 0]]},
	# çapraz kesik (X): iniş + yükseliş tek hamlede, iki vuruş
	"cross_x": {"body": "atk_horiz", "hit": [0.24, 0.7], "multi": [0.3, 0.56], "ss": 2.0, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.18, 2.8, 0.5, 0.7, 0.95, 1.0, 2], [0.24, 2.9, 0.55, 0.75, 0.9, 1.0, 0],
		[0.32, 0.9, 0.0, 0.0, 1.0, 1.15, 1], [0.4, 0.2, 0.0, -0.3, 1.0, 1.05, 2], [0.48, -0.3, -0.3, -0.5, 0.9, 1.0, 2],
		[0.58, 1.4, 0.0, 0.15, 1.0, 1.15, 1], [0.7, 2.6, 0.1, 0.3, 1.0, 1.05, 2], [1.0, 0.7, 0.9, 0.4, 1.0, 1.0, 0]]},
	# iki elli baş üstü iniş (dev kılıç / balta)
	"overhead_2h": {"body": "atk_overhead_2h", "hit": [0.4, 0.64], "hold_k": 0.34, "ws": 1.1, "ck": 0.52, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.3, 3.35, 0.25, 0.3, 0.85, 1.0, 2], [0.4, 3.55, 0.3, 0.35, 0.8, 1.0, 0],
		[0.52, 1.0, 0.0, 0.0, 1.0, 1.2, 1], [0.58, 0.35, 0.0, -0.15, 1.0, 1.1, 2], [0.64, 0.38, 0.072, -0.108, 1.0, 1.088, 0],
		[1.0, 0.6, 0.6, 0.2, 1.0, 1.0, 0]]},
	# yerde sürükleyip yukarı: kılıç arkada toprağı yalar, kıvılcımla yükselir
	"ground_drag": {"body": "atk_up", "hit": [0.34, 0.6], "ck": 0.47, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.24, -0.95, 0.15, 0.35, 1.0, 1.0, 2], [0.34, -1.05, 0.2, 0.4, 1.0, 1.0, 0],
		[0.47, 1.5, 0.0, 0.1, 1.0, 1.15, 1], [0.535, 2.5, 0.05, 0.2, 1.0, 1.08, 2], [0.6, 2.32, 0.152, 0.224, 1.0, 1.07, 0],
		[1.0, 1.0, 0.9, 0.4, 1.0, 1.0, 0]]},
	# diz hizası yatay süpürme (alçak)
	"sweep_low": {"body": "atk_sweep_low", "hit": [0.3, 0.56], "ck": 0.42, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, -0.9, 0.0, -0.3, 0.9, 1.0, 2], [0.3, -1.0, 0.0, -0.35, 0.85, 1.0, 0],
		[0.42, 1.05, 0.0, -0.1, 1.0, 1.15, 1],
		[0.49, 1.25, 0.1, 0.0, 1.0, 1.05, 2], [0.56, 1.184, 0.196, 0.048, 1.0, 1.044, 0], [1.0, 0.7, 0.9, 0.4, 1.0, 1.0, 0]]},
	# ters el: bıçak ön kol boyunca geriye bakar, dirsekten çevrilerek savrulur
	"reverse_grip": {"body": "atk_horiz", "hit": [0.3, 0.56], "ck": 0.42, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, 1.5, 1.7, 3.0, 1.0, 1.0, 2], [0.3, 1.55, 1.8, 3.05, 1.0, 1.0, 0],
		[0.42, 1.4, -0.3, 2.95, 1.0, 1.1, 1],
		[0.49, 1.2, -0.5, 2.9, 1.0, 1.0, 2], [0.56, 1.128, -0.332, 2.588, 1.0, 1.0, 0], [1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# bilek çevrimi: kılıç elde tam tur döner (iki vuruş)
	"twirl": {"body": "atk_spin", "hit": [0.26, 0.7], "multi": [0.36, 0.58], "ss": 2.0, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.2, 1.5, 0.1, 0.2, 1.0, 1.0, 2], [0.26, 1.55, 0.05, 0.0, 1.0, 1.0, 0],
		[0.48, 1.55, 0.0, 3.2, 1.0, 1.05, 0], [0.7, 1.5, 0.0, 6.4, 1.0, 1.05, 0], [1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# yel değirmeni: baş üstünden tam tur geriye, sonra tüm ağırlıkla yere
	"windmill": {"body": "atk_heavy", "hit": [0.44, 0.66], "ws": 1.4, "ck": 0.55, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.16, 1.3, 0.2, 0.1, 1.0, 1.0, 0], [0.3, 3.0, 0.2, 0.2, 0.75, 1.0, 0],
		[0.44, 4.6, 0.2, 0.3, 0.8, 1.0, 0], [0.55, 7.1, 0.0, 0.0, 1.0, 1.2, 1], [0.605, 6.65, 0.0, -0.15, 1.0, 1.1, 2],
		[0.66, 6.68, 0.072, -0.108, 1.0, 1.088, 0], [1.0, 6.9, 0.6, 0.2, 1.0, 1.0, 0]]},
	# mızrak saplaması: uzun uzanış
	"pole_thrust": {"body": "atk_thrust", "hit": [0.3, 0.54], "ck": 0.38, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, -0.6, 2.0, 0.1, 1.0, 0.8, 2], [0.3, -0.75, 2.1, 0.1, 1.0, 0.75, 0],
		[0.38, 1.55, 0.0, 0.0, 1.0, 1.5, 1], [0.46, 1.5, 0.05, 0.0, 1.0, 1.4, 2], [0.54, 1.392, 0.152, 0.036, 1.0, 1.352, 0],
		[1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# iki elli geniş sırık süpürmesi
	# v18 alçak saplama: diz hizasına, gövde öne eğik (kargı zincirinin ikinci vuruşu; ilk saplamanın tekrarı gibi okunmasın)
	"pole_thrust_lo": {"body": "atk_lunge_long", "hit": [0.3, 0.54], "ck": 0.38, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, -0.9, 2.2, 0.0, 1.0, 0.8, 2], [0.3, -1.0, 2.3, 0.0, 1.0, 0.75, 0],
		[0.38, 1.35, 0.0, 0.0, 1.0, 1.5, 1], [0.46, 1.3, 0.05, 0.0, 1.0, 1.42, 2], [0.54, 1.22, 0.15, 0.04, 1.0, 1.37, 0],
		[1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	"pole_sweep": {"body": "atk_horiz", "hit": [0.3, 0.6], "ck": 0.45, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, -1.5, -0.2, -0.4, 0.9, 1.1, 2], [0.3, -1.6, -0.25, -0.45, 0.85, 1.1, 0],
		[0.45, 1.6, 0.0, 0.0, 1.0, 1.3, 1],
		[0.525, 1.8, 0.1, 0.1, 1.0, 1.15, 2], [0.6, 1.72, 0.2, 0.15, 1.0, 1.1, 0], [1.0, 0.7, 0.9, 0.4, 1.0, 1.0, 0]]},
	# v18 sırık yükselişi: mızrak alçaktan geriye çekilir, önden baş üstüne geniş hilalle kalkar (kargı bitirişi)
	"pole_rise": {"body": "atk_up", "hit": [0.3, 0.58], "ck": 0.42, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, -0.7, -0.3, -0.3, 1.0, 0.9, 2], [0.3, -0.8, -0.35, -0.35, 1.0, 0.85, 0],
		[0.42, 1.6, 0.0, 0.15, 1.0, 1.25, 1], [0.5, 2.5, 0.1, 0.25, 1.0, 1.1, 2], [0.58, 2.4, 0.2, 0.25, 1.0, 1.05, 0],
		[1.0, 0.8, 0.9, 0.4, 1.0, 1.0, 0]]},
	# biçme: önden geriye, kendine çekerek (tırpan)
	"reap": {"body": "atk_horiz", "hit": [0.3, 0.58], "ck": 0.36, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, 2.0, 0.2, 0.4, 0.9, 1.15, 2], [0.3, 2.1, 0.2, 0.45, 0.85, 1.15, 0],
		[0.36, 1.25, 0.0, 0.25, 1.0, 1.2, 1], [0.41, -0.5, 0.2, 0.0, 1.0, 1.1, 2],
		[0.47, -0.9, 0.4, -0.2, 1.0, 1.0, 2], [0.58, -0.72, 0.46, -0.14, 1.0, 1.0, 0], [1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# pençe tırmığı: iki hızlı aşağı tırmalama
	"rake": {"body": "atk_down", "hit": [0.2, 0.62], "multi": [0.28, 0.5], "ss": 1.8, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.14, 2.2, 0.3, 0.6, 1.0, 1.0, 2], [0.2, 2.3, 0.3, 0.6, 1.0, 1.0, 0],
		[0.3, 0.9, 0.0, 0.0, 1.0, 1.1, 1], [0.38, 2.0, 0.3, 0.5, 1.0, 1.0, 2], [0.52, 0.7, 0.0, -0.1, 1.0, 1.12, 1],
		[0.62, 0.5, 0.1, -0.2, 1.0, 1.05, 2], [1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# kırbaç şaklaması: kol arkaya yukarı, öne şaklar (uzun uzanış)
	"whip_crack": {"body": "atk_whip", "hit": [0.3, 0.52], "ck": 0.4, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, 3.0, 0.6, 0.9, 1.0, 1.0, 2], [0.3, 3.1, 0.65, 1.0, 1.0, 1.0, 0],
		[0.4, 1.6, 0.0, -0.4, 1.0, 1.4, 1], [0.46, 1.4, 0.0, -0.6, 1.0, 1.25, 2], [0.52, 1.304, 0.108, -0.492, 1.0, 1.22, 0],
		[1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# balta kancası: baş üstünden iniş, sonra kancayla kendine çekiş
	"axe_hook": {"body": "atk_down", "hit": [0.3, 0.6], "ck": 0.42, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, 3.1, 0.5, 0.4, 1.0, 1.0, 2], [0.3, 3.2, 0.55, 0.45, 1.0, 1.0, 0],
		[0.42, 1.0, 0.0, 0.0, 1.0, 1.15, 1], [0.47, 0.6, 0.3, -0.6, 1.0, 1.0, 2], [0.51, 0.4, 0.9, -0.9, 1.0, 0.9, 2],
		[0.6, 0.424, 0.9, -0.756, 1.0, 0.912, 0], [1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# çekiş (iai): kılıç kalçada geriye bakar, tek hamlede açılır
	"iai": {"body": "atk_horiz", "hit": [0.26, 0.42], "ck": 0.34, "keys": [
		[0.0, 0.5, 1.5, -1.3, 1.0, 1.0, 0], [0.2, 0.45, 1.6, -1.35, 1.0, 1.0, 2], [0.26, 0.4, 1.65, -1.4, 0.9, 1.0, 0],
		[0.34, 1.7, 0.0, 0.0, 1.0, 1.2, 1], [0.38, 2.0, 0.0, 0.1, 1.0, 1.1, 2], [0.42, 1.832, 0.108, 0.124, 1.0, 1.088, 0],
		[1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# iki elli aparkat: alçak-arkadan baş üstüne (fırlatır)
	# v25: baş geride-aşağıda bilekten geri kalır, temasta bilek öne geçer (uç kolu yönetir), takipte bilek kıvrılır:
	# iz düz kenarlı geniş "levha" değil, dar eğik, ucu kancalı hilal
	"uppercut_2h": {"body": "atk_uppercut", "hit": [0.34, 0.6], "hold_k": 0.24, "ck": 0.47, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.24, -0.5, 0.3, -0.35, 0.9, 1.0, 2], [0.34, -0.6, 0.35, -0.42, 0.85, 1.0, 0],
		[0.47, 1.45, 0.0, 0.35, 1.0, 1.2, 1], [0.535, 2.35, 0.0, 1.15, 1.0, 1.1, 2], [0.6, 2.25, 0.1, 1.05, 1.0, 1.088, 0],
		[1.0, 1.0, 0.9, 0.4, 1.0, 1.0, 0]]},
	# iki elli çakma: sıçrayıp yere
	"slam_2h": {"body": "atk_slam_jump", "hit": [0.5, 0.72], "hold_k": 0.24, "ws": 1.6, "ck": 0.6, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.26, 3.4, 0.2, 0.3, 0.85, 1.0, 2], [0.5, 3.55, 0.25, 0.35, 0.8, 1.0, 0],
		[0.6, 0.9, 0.0, 0.0, 1.0, 1.2, 1], [0.66, 0.35, 0.0, -0.2, 1.0, 1.1, 2], [0.72, 0.38, 0.072, -0.152, 1.0, 1.088, 0],
		[1.0, 0.6, 0.6, 0.2, 1.0, 1.0, 0]]},
	# şarjlı saplama: uzun uzanış + öne hamle
	"stab_heavy": {"body": "atk_lunge_long", "hit": [0.36, 0.62], "ss": 1.2, "ck": 0.44, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.26, -0.6, 2.1, 0.0, 1.0, 0.8, 2], [0.36, -0.7, 2.15, 0.0, 1.0, 0.75, 0],
		[0.44, 1.6, 0.0, 0.0, 1.0, 1.55, 1], [0.53, 1.55, 0.0, 0.0, 1.0, 1.45, 2], [0.62, 1.436, 0.108, 0.036, 1.0, 1.396, 0],
		[1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# baş üstü çark: iki tam tur, iki yanı biçer (iki vuruş)
	"helicopter": {"body": "atk_spin_2h", "hit": [0.26, 0.78], "around": true, "multi": [0.4, 0.62], "ss": 2.6, "ws": 1.2, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.2, 2.9, 0.2, 0.1, 1.0, 1.0, 2], [0.26, 3.0, 0.1, 0.0, 0.9, 1.0, 0],
		[0.52, 6.1, 0.0, 0.0, 1.0, 1.2, 0], [0.78, 9.3, 0.0, 0.0, 1.0, 1.2, 0], [1.0, 9.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# ---------------------------------------------------------------- v15: arketip savuruşları
	# geri sıçrayış kesiği: gövde geriye hoplarken bıçak öne yatay geçer (yatağan / rüzgâr / yıldırım çekilmesi)
	"backstep": {"body": "atk_backstep", "hit": [0.3, 0.56], "hold_k": 0.24, "ss": 1.1, "ck": 0.42, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, -1.2, -0.1, -0.2, 1.0, 1.0, 2], [0.3, -1.3, -0.15, -0.25, 1.0, 1.0, 0],
		[0.42, 1.7, 0.0, 0.1, 1.0, 1.15, 1],
		[0.49, 2.0, 0.2, 0.25, 1.0, 1.0, 2], [0.56, 1.844, 0.284, 0.268, 1.0, 1.0, 0], [1.0, 0.7, 0.9, 0.4, 1.0, 1.0, 0]]},
	# uzun hamle: derin adım, arka bacak gergin; sırık ok gibi uzanır (kargı / mızrak zincir sonu)
	"lunge_long": {"body": "atk_lunge_long", "hit": [0.34, 0.62], "ss": 1.2, "ck": 0.42, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.24, -0.7, 2.1, 0.0, 1.0, 0.8, 2], [0.34, -0.8, 2.15, 0.0, 1.0, 0.75, 0],
		[0.42, 1.6, 0.0, 0.0, 1.0, 1.55, 1], [0.52, 1.55, 0.0, 0.0, 1.0, 1.45, 2], [0.62, 1.436, 0.108, 0.036, 1.0, 1.396, 0],
		[1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# tam gövde çark: pala / tırpan / ulu kılıç; iki yanı biçer, iki vuruş (basılı tutulunca sürer: spin_hold)
	"spin_2h": {"body": "atk_spin_2h", "hit": [0.3, 0.7], "around": true, "multi": [0.38, 0.6], "ss": 2.2, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, -1.2, 0.2, 0.0, 1.0, 1.0, 2], [0.3, -1.3, 0.1, 0.0, 1.0, 1.0, 0],
		[0.7, 5.1, 0.0, 0.0, 1.0, 1.15, 0], [1.0, 5.4, 0.9, 0.3, 1.0, 1.0, 0]]},
	# ikiz bıçak: ön omuzdan hızlı düz kesik
	"dual_l": {"body": "atk_dual", "hit": [0.26, 0.5], "ck": 0.34, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.18, 2.6, 0.9, 0.9, 1.0, 1.0, 2], [0.26, 2.75, 0.95, 1.0, 1.0, 1.0, 0],
		[0.34, 1.2, 0.0, 0.1, 1.0, 1.15, 1], [0.42, 0.55, 0.2, -0.2, 1.0, 1.05, 2], [0.5, 0.58, 0.3, -0.1, 1.0, 1.0, 0],
		[1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# ikiz bıçak: ters el, arka omuzdan
	"dual_r": {"body": "atk_dual", "hit": [0.26, 0.5], "ck": 0.34, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.18, -0.4, -0.4, -0.5, 1.0, 1.0, 2], [0.26, -0.5, -0.45, -0.55, 1.0, 1.0, 0],
		[0.34, 1.75, 0.0, 0.2, 1.0, 1.15, 1], [0.42, 2.55, 0.1, 0.25, 1.0, 1.05, 2], [0.5, 2.45, 0.25, 0.25, 1.0, 1.0, 0],
		[1.0, 0.8, 0.9, 0.4, 1.0, 1.0, 0]]},
	# çapraz delip geçme: X kesik + gövde düşmanın içinden öteye fırlar (ikiz bıçak 4. vuruş, böri sırt saplaması)
	"cross_dash": {"body": "atk_dual", "hit": [0.26, 0.66], "multi": [0.32, 0.54], "ss": 2.0, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.2, 2.8, 0.5, 0.7, 0.95, 1.0, 2], [0.26, 2.9, 0.55, 0.75, 0.9, 1.0, 0],
		[0.34, 0.9, 0.0, 0.0, 1.0, 1.15, 1], [0.42, 0.2, 0.0, -0.3, 1.0, 1.05, 2], [0.48, -0.3, -0.3, -0.5, 0.9, 1.0, 2],
		[0.56, 1.4, 0.0, 0.15, 1.0, 1.15, 1], [0.66, 2.6, 0.1, 0.3, 1.0, 1.05, 2], [1.0, 0.7, 0.9, 0.4, 1.0, 1.0, 0]]},
	# kırbaç yan şaklama: uzun yatay uzanış
	"whip_side": {"body": "atk_whip", "hit": [0.3, 0.54], "ck": 0.4, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, -0.8, -0.3, -0.5, 1.0, 1.0, 2], [0.3, -0.9, -0.35, -0.6, 1.0, 1.0, 0],
		[0.4, 1.5, 0.0, -0.1, 1.0, 1.3, 1], [0.47, 2.0, 0.05, -0.4, 1.0, 1.2, 2], [0.54, 1.9, 0.15, -0.3, 1.0, 1.15, 0],
		[1.0, 0.7, 0.9, 0.4, 1.0, 1.0, 0]]},
	# adımlı iniş: tek elli ama tüm gövdeyle; baş üstünden adım atarak iner (alp / ayaz / bozgun bitirişi)
	"step_down": {"body": "atk_overhead_2h", "hit": [0.38, 0.62], "hold_k": 0.33, "ws": 1.1, "ck": 0.5, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.28, 3.25, 0.6, 0.7, 1.0, 1.0, 2], [0.38, 3.4, 0.65, 0.75, 1.0, 1.0, 0],
		[0.5, 1.2, 0.0, 0.15, 1.0, 1.18, 1], [0.56, 0.5, 0.1, 0.0, 1.0, 1.05, 2], [0.62, 0.5, 0.196, 0.048, 1.0, 1.044, 0],
		[1.0, 0.5, 0.9, 0.4, 1.0, 1.0, 0]]},
	# sırık atlayışı: sırık yere saplanır, gövde ileri-yukarı fırlar; ucu kalkarken vurur (kargı / mızrak ↑+J)
	"pole_vault": {"body": "atk_uppercut", "hit": [0.3, 0.58], "hold_k": 0.24, "ss": 1.2, "ck": 0.44, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, 0.9, 0.6, -0.3, 1.0, 1.0, 2], [0.3, 0.8, 0.7, -0.35, 1.0, 1.0, 0],
		[0.44, 2.3, 0.0, 0.1, 1.0, 1.2, 1], [0.51, 2.9, 0.0, 0.0, 1.0, 1.1, 2], [0.58, 2.696, 0.108, 0.048, 1.0, 1.088, 0],
		[1.0, 1.2, 0.9, 0.4, 1.0, 1.0, 0]]},
	# ---------------------------------------------------------------- v25: Yıldırım Kılıcı (YK tablosu)
	# Çekiş (iaido): el kalçada, bıçak kında geriye-aşağı bakar (-0,6 rad); tek hamlede alttan öne, oradan öne-yukarı
	# (~3,2 rad'lık geniş yay, yassı yatay düzlemde: gövdenin önünden kameraya dönerek geçen uzun hilal)
	"yk_iai": {"body": "atk_horiz", "hit": [0.3, 0.52], "hold_k": 0.27, "ck": 0.39, "yk_end": [0.45], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.22, 0.25, 1.55, -2.35, 1.0, 1.0, 2], [0.3, 0.2, 1.6, -2.42, 0.9, 1.0, 0],
		[0.39, 1.5, 0.0, -0.05, 1.0, 1.22, 1], [0.46, 2.2, 0.05, 0.35, 1.0, 1.1, 2], [0.52, 2.1, 0.14, 0.38, 1.0, 1.06, 0],
		[1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
	# Şimşek Çaprazı: iki dik çapraz kesik, iki ayrı düzlemde (önce baş üstünden öne-aşağı, sonra alttan öne-yukarı);
	# ikinci kesik birincinin önünde onu keser (X)
	"yk_cross": {"body": "atk_horiz", "hit": [0.24, 0.68], "multi": [0.31, 0.55], "ss": 1.35, "yk_end": [0.41, 0.645], "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.18, 2.95, 0.5, 0.8, 0.95, 1.0, 2], [0.24, 3.05, 0.55, 0.85, 0.9, 1.0, 0],
		[0.33, 0.95, 0.0, -0.1, 1.0, 1.15, 1], [0.4, 0.2, 0.1, -0.45, 1.0, 1.05, 2], [0.47, -0.3, -0.3, -0.6, 0.9, 1.0, 2],
		[0.57, 1.55, 0.0, 0.2, 1.0, 1.15, 1], [0.63, 2.7, 0.1, 0.35, 1.0, 1.05, 2], [0.68, 2.58, 0.18, 0.36, 1.0, 1.03, 0],
		[1.0, 0.7, 0.9, 0.4, 1.0, 1.0, 0]]},
	# Şimşek Çekişi (bitiriş): bıçak kına iner, gövde derin çömelir (okunur tutuş); bırakışta bıçak tek karede yatay
	# öne açılır ve gövde yerde ileri atılır (YK.flash_px); bıçak uzanmış kalır (zanshin), sonra kına döner
	"yk_flash": {"body": "atk_lunge", "hit": [0.34, 0.62], "hold_k": 0.32, "ss": 1.25, "ck": 0.4, "keys": [
		[0.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0], [0.24, 0.3, 1.6, -2.25, 1.0, 1.0, 2], [0.34, 0.22, 1.7, -2.35, 0.9, 1.0, 0],
		[0.4, 1.55, 0.0, 0.0, 1.0, 1.3, 1], [0.5, 1.72, 0.0, 0.08, 1.0, 1.26, 2], [0.62, 1.68, 0.05, 0.1, 1.0, 1.2, 0],
		[1.0, 0.6, 0.9, 0.3, 1.0, 1.0, 0]]},
}

## ------------------------------------------------------------------ v23 3B SAVURUŞ DÜZLEMLERİ
## Geri bildirim: "kılıç savuruşları direkt daire şeklinde, çok basit" (Dead Cells: bıçak gövdenin çevresinde eğik bir
## 3B düzlemde döner; iz, perspektifte görülen bir elips yayı olur). SWINGS anahtarları kolu ve bıçağı savuruş
## DÜZLEMİNİN içinde sürer (a1, a2, w bu düzlemdeki açılar); düzlem kameraya göre eğiktir ve ekrana dik izdüşümle
## çizilir: düzlemin ekrandaki büyük ekseni "phi" yönünde (açı kuralı kollarla aynı: 0 aşağı, 90 ileri, 180 yukarı;
## derece), ona dik bileşen "r" oranında kısalır (r = cos(eğim); 1 = ekran düzlemi, eski daire; küçük = yatık düzlem,
## yassı elips). Uç ve kabza aynı düzlemde ama farklı yarıçapta döndüğünden ikisi ayrı elips çizer (iz hilalinin iç ve
## dış kenarı farklı eğri); bıçak büyük eksenden uzaklaştıkça ekranda kısalır (silah sprite'ı da: önkısalma).
## Kol (omuz → dirsek → el) aynı düzlemde ama daha az kısalarak (ARM_PLANE) izdüşer: el de eşleşen bir elipste gezer,
## gövde ile bıçak aynı hareketi anlatır.
##   "p": [[k, phi, r, roll], ...]  savuruş içindeki anahtarlar (k: normalize zaman; tek kayıt = sabit düzlem). roll
##        bileğin bıçak ekseni çevresinde dönüşü (derece): silah sprite'ının eni cos(roll) ile incelir / yüz değiştirir.
##   "b": true  bıçak düzlemin arka yarısına geçince (derinlik < 0) gövdenin ARKASINDA çizilir (çark: gövdeyi dolanır)
##   "zf": düzlemin kameraya bakan yarısının yönü (derece; varsayılan 0 = düzlemde "aşağı" ön taraf)
## Hazırlığın başında düzlem önceki savuruşun düzleminden (zincir) ya da ekran düzleminden (dinlenme) bu savuruşunkine
## geçer; toparlanmada ekran düzlemine döner. Her savuruşa küçük rastgele sapma (PLANE_JIT: ±derece, ±oran): art arda
## aynı savuruş birebir aynı görünmez ama okunur kalır. Zamanlama ve vuruş kutuları değişmedi; temas anında bıçak
## büyük eksene yakın tutuldu (görünen erim eskisiyle aynı kalsın: ileri yön düzlemlerin çoğunda kısalmaz).
const ARM_PLANE := 0.55          # kolun düzlem kısalmasına katılımı (0: kol ekran düzleminde, 1: bıçakla aynı)
const PLANE_JIT := [4.0, 0.04]   # savuruş başına rastgele sapma: phi ±derece, r ±oran
## Silah sınıfına göre düzlem çarpanı [phi ekleme (derece), r çarpanı]: hançer fiskeleri daha dik ve küçük, uzun sap /
## mızrak süpürmeleri daha yassı ve geniş
const CLASS_PLANE := {"hancer": [0.0, 1.12], "duello": [0.0, 1.0], "kilic": [0.0, 1.0], "mizrak": [0.0, 0.9],
	"kirbac": [0.0, 0.95], "uzun": [0.0, 0.86], "agir": [0.0, 1.0], "dev": [0.0, 1.0]}
const PLANES := {
	# kılıç zinciri: çapraz iniş (omuz arkasından baş üstünden öne-aşağı; büyük eksen çapraz) → çapraz yükseliş
	# (alt-arkadan öne-yukarı) → adımlı baş üstü "C" (dik, uzun elips)
	"diag_down": {"p": [[0.0, 62.0, 0.42, 0.0], [0.42, 64.0, 0.42, 0.0], [0.55, 58.0, 0.45, 35.0]]},
	"diag_up": {"p": [[0.0, 118.0, 0.42, 0.0], [0.42, 120.0, 0.42, 0.0], [0.55, 128.0, 0.46, -30.0]]},
	"step_down": {"p": [[0.0, 34.0, 0.6, 0.0], [0.5, 30.0, 0.62, 0.0], [0.62, 26.0, 0.66, 25.0]]},
	"down": {"p": [[0.0, 58.0, 0.5, 0.0], [0.42, 60.0, 0.5, 0.0], [0.56, 50.0, 0.55, 30.0]]},
	"up": {"p": [[0.0, 122.0, 0.5, 0.0], [0.42, 120.0, 0.5, 0.0], [0.56, 130.0, 0.52, -25.0]]},
	# yatay: yatık düzlem, yassı geniş hilal; bıçak öne doğru kameraya dönerek (kısalarak) geçer
	"horiz": {"p": [[0.0, 96.0, 0.3, 0.0], [0.42, 94.0, 0.3, 0.0], [0.56, 100.0, 0.34, 40.0]]},
	"back": {"p": [[0.0, 80.0, 0.38, 0.0], [0.42, 82.0, 0.38, 0.0], [0.56, 76.0, 0.42, -40.0]], "zf": 180.0},
	"reverse_grip": {"p": [[0.0, 62.0, 0.5, 30.0], [0.42, 66.0, 0.48, 0.0], [0.56, 70.0, 0.5, -30.0]]},
	"iai": {"p": [[0.0, 100.0, 0.34, 0.0], [0.34, 98.0, 0.32, 0.0], [0.42, 104.0, 0.36, 35.0]]},
	"backstep": {"p": [[0.0, 100.0, 0.34, 0.0], [0.42, 98.0, 0.34, 0.0], [0.56, 106.0, 0.38, 35.0]]},
	"sweep_low": {"p": [[0.0, 82.0, 0.28, 0.0], [0.42, 80.0, 0.27, 0.0], [0.56, 88.0, 0.3, 30.0]]},
	"rise": {"p": [[0.0, 138.0, 0.5, 0.0], [0.44, 136.0, 0.5, 0.0], [0.58, 146.0, 0.54, -30.0]]},
	"cross_x": {"p": [[0.0, 60.0, 0.45, 0.0], [0.42, 60.0, 0.45, 0.0], [0.5, 120.0, 0.45, 0.0], [0.7, 124.0, 0.48, -25.0]]},
	"twirl": {"p": [[0.0, 70.0, 0.48, 0.0]]},
	"spin": {"p": [[0.0, 90.0, 0.3, 0.0]], "b": true},
	"spin_2h": {"p": [[0.0, 92.0, 0.3, 0.0], [0.7, 88.0, 0.32, 0.0]], "b": true},
	"helicopter": {"p": [[0.0, 90.0, 0.3, 0.0]], "b": true, "zf": 180.0},
	# saplamalar: hafif yaylı düz çizgi (kol yassı elipste öne fırlar)
	"thrust": {"p": [[0.0, 90.0, 0.36, 0.0]]},
	"lunge": {"p": [[0.0, 88.0, 0.36, 0.0]]},
	"flurry": {"p": [[0.0, 92.0, 0.4, 0.0]]},
	"pole_thrust": {"p": [[0.0, 90.0, 0.4, 0.0]]},
	"pole_thrust_lo": {"p": [[0.0, 76.0, 0.4, 0.0]]},
	"lunge_long": {"p": [[0.0, 88.0, 0.38, 0.0]]},
	"stab_heavy": {"p": [[0.0, 88.0, 0.38, 0.0]]},
	"pole_rise": {"p": [[0.0, 128.0, 0.4, 0.0], [0.42, 126.0, 0.4, 0.0], [0.58, 138.0, 0.44, -25.0]]},
	"pole_vault": {"p": [[0.0, 140.0, 0.5, 0.0]]},
	# ağır: dik "C" ezmeler, geniş eğik yel değirmeni
	"heavy": {"p": [[0.0, 32.0, 0.62, 0.0], [0.45, 30.0, 0.62, 0.0], [0.62, 24.0, 0.66, 20.0]]},
	"overhead_2h": {"p": [[0.0, 30.0, 0.6, 0.0], [0.52, 28.0, 0.6, 0.0], [0.64, 22.0, 0.64, 20.0]]},
	"slam": {"p": [[0.0, 28.0, 0.62, 0.0]]},
	"slam_2h": {"p": [[0.0, 26.0, 0.62, 0.0]]},
	# yel değirmeni: baş üstü geriye tur eğik düzlemde, vuruş yatık düzlemde: baş yerde sürünmez, gövdenin önünden
	# (kameraya doğru) geniş, yassı bir elipsle geçer
	"windmill": {"p": [[0.0, 60.0, 0.6, 0.0], [0.3, 72.0, 0.55, 0.0], [0.44, 96.0, 0.38, 0.0], [0.55, 90.0, 0.4, 0.0],
		[0.66, 80.0, 0.45, 20.0]]},
	"uppercut_2h": {"p": [[0.0, 142.0, 0.36, 0.0], [0.47, 138.0, 0.33, 0.0], [0.6, 152.0, 0.4, -35.0]]},   # v25: dar eğik elips (eski 134°/0,48 geniş levha)
	"ground_drag": {"p": [[0.0, 104.0, 0.45, 0.0], [0.47, 108.0, 0.45, 0.0], [0.6, 122.0, 0.5, -20.0]]},
	"axe": {"p": [[0.0, 40.0, 0.7, 0.0]]},
	"axe_hook": {"p": [[0.0, 45.0, 0.55, 0.0], [0.42, 45.0, 0.55, 0.0], [0.5, 100.0, 0.42, 30.0]]},
	# uzun sap: geniş yassı süpürmeler
	"pole_sweep": {"p": [[0.0, 92.0, 0.26, 0.0], [0.45, 90.0, 0.26, 0.0], [0.6, 98.0, 0.3, 30.0]]},
	"reap": {"p": [[0.0, 86.0, 0.3, 0.0], [0.36, 86.0, 0.3, 0.0], [0.58, 78.0, 0.34, -30.0]]},
	# hançer: küçük eğik fiskeler (dik iniş, ters el yükseliş), iki tırmık farklı düzlemde, X delip geçiş
	"dual_l": {"p": [[0.0, 52.0, 0.5, 0.0], [0.34, 54.0, 0.5, 0.0], [0.5, 46.0, 0.55, 35.0]]},
	"dual_r": {"p": [[0.0, 128.0, 0.48, 20.0], [0.34, 130.0, 0.48, 0.0], [0.5, 140.0, 0.52, -40.0]]},
	"rake": {"p": [[0.0, 34.0, 0.55, 0.0], [0.32, 34.0, 0.55, 0.0], [0.4, 56.0, 0.5, 0.0]]},
	"cross_dash": {"p": [[0.0, 56.0, 0.46, 0.0], [0.44, 56.0, 0.46, 0.0], [0.5, 124.0, 0.46, 0.0], [0.66, 128.0, 0.5, -25.0]]},
	# kırbaç: eğik şaklama, yassı yan kurdele
	"whip_crack": {"p": [[0.0, 55.0, 0.55, 0.0], [0.4, 56.0, 0.55, 0.0], [0.52, 46.0, 0.6, 30.0]]},
	"whip_side": {"p": [[0.0, 100.0, 0.38, 0.0], [0.4, 98.0, 0.38, 0.0], [0.54, 108.0, 0.42, 30.0]]},
	# v25 Yıldırım Kılıcı: çekiş çok yassı yatay elips (bıçak gövdenin önünden kameraya dönerek geçer, takipte bilek
	# döner), çapraz iki dik eğik düzlem (48° iniş → 132° yükseliş), bitiriş yatay çizgi
	"yk_iai": {"p": [[0.0, 102.0, 0.24, 0.0], [0.39, 98.0, 0.22, 0.0], [0.46, 108.0, 0.28, 30.0], [0.52, 112.0, 0.32, 45.0]]},
	"yk_cross": {"p": [[0.0, 48.0, 0.5, 0.0], [0.4, 46.0, 0.5, 20.0], [0.47, 132.0, 0.5, 0.0], [0.63, 134.0, 0.52, -30.0]]},
	"yk_flash": {"p": [[0.0, 92.0, 0.3, 0.0], [0.4, 90.0, 0.3, 0.0], [0.62, 92.0, 0.32, 20.0]]},
}

## Silah uzunluğu (kabzadan uca, piksel): iz ve vuruş kutusu buna göre ölçeklenir
const REACH := {"ulu_kilic": 48.0, "dag_cekici": 40.0, "ruh_kilici": 32.0, "ay_palasi": 20.0, "alp_kilici": 31.0, "yildirim_kilici": 36.0, "pala": 28.0, "yatagan": 27.0, "gurz": 24.0, "teber": 34.0, "kargi": 44.0,
	"ikiz_bicak": 16.0, "savas_baltasi": 26.0, "erlik_tirpani": 40.0, "kurt_pencesi": 14.0, "ayaz_kilici": 33.0, "civili_topuz": 27.0,
	"kement": 46.0, "od_kamcisi": 46.0, "yilan_kilici": 30.0, "kor_cekici": 36.0, "ruzgar_kilici": 32.0,
	"tulpar_mizragi": 48.0, "bori_hanceri": 15.0, "ikiz_balta": 26.0, "kayin_asasi": 40.0, "bozgun_kilici": 42.0,
	"gun_ay_ikizi": 30.0, "kistin": 38.0, "albasti_hanceri": 16.0, "cevgen": 40.0}
## Ağır silahlar: daha uzun duraklama, daha sert kamera, daha geniş sarsıntı
const HEAVY := ["gurz", "teber", "civili_topuz", "erlik_tirpani", "savas_baltasi", "ulu_kilic", "dag_cekici", "kor_cekici", "bozgun_kilici",
	"kistin", "cevgen"]

## Kombolar: "chain" art arda basınca, "pause" iki (ya da daha çok) vuruştan sonra kısa bekleyip basınca.
## Adım: {"s": savuruş, "mult": hasar, "kb": geri itme, ...bayraklar}. Bayraklar: last, shock, launch, dash,
## double, slam, whip, axe, wave. v15 bayrakları: backstep (geriye hoplayarak kes), through (düşmanın içinden
## öteye fırla), spin_hold (tuş basılıysa çark 1,2 sn'ye dek sürer), pull (düşmanı kendine çek, px/sn),
## tipcrit (uçtan isabet kesin kritik), stun (sn), sa (süper zırh: atk.super_armor), vault (sırık atlayışı), tm (süre çarpanı).
## Her arketip başka bir karakter gibi oynanır: tempo, adım işi, vuruş kutusu, geri itme yönü ve bir imza mekanik.
const COMBOS := {
	# --- tür varsayılanları
	"slash": {"chain": [{"s": "horiz", "mult": 1.0, "kb": 110.0}, {"s": "down", "mult": 1.0, "kb": 110.0}, {"s": "step_down", "mult": 1.3, "kb": 220.0, "dash": 20.0, "last": true}],
		"pause": {"s": "spin_2h", "mult": 1.25, "kb": 160.0, "name": "Kasırga"}},
	"dual": {"chain": [{"s": "dual_l", "mult": 1.0, "kb": 45.0}, {"s": "dual_r", "mult": 1.0, "kb": 45.0}, {"s": "dual_l", "mult": 1.0, "kb": 45.0}, {"s": "cross_dash", "mult": 1.3, "kb": 120.0, "through": true, "last": true}],
		"pause": {"s": "flurry", "mult": 0.8, "kb": 60.0, "name": "Bıçak Yağmuru"}},
	"heavy": {"chain": [{"s": "windmill", "mult": 1.0, "kb": 280.0, "shock": true}, {"s": "slam", "mult": 1.2, "kb": 300.0, "slam": true, "shock": true, "last": true}],
		"pause": {"s": "slam", "mult": 1.6, "kb": 300.0, "shock": true, "slam": true, "name": "Yer Yaran"}},
	"thrust": {"chain": [{"s": "thrust", "mult": 1.0, "kb": 150.0}, {"s": "thrust", "mult": 1.1, "kb": 170.0}, {"s": "lunge_long", "mult": 1.3, "kb": 260.0, "dash": 40.0, "last": true}],
		"pause": {"s": "lunge", "mult": 1.6, "kb": 220.0, "dash": 90.0, "name": "Akın"}},
	"whip": {"chain": [{"s": "whip_crack", "mult": 1.0, "kb": 40.0, "whip": true, "tipcrit": true}, {"s": "whip_side", "mult": 1.1, "kb": 60.0, "whip": true, "tipcrit": true, "last": true}],
		"pause": {"s": "spin", "mult": 1.2, "kb": 120.0, "whip": true, "name": "Kement Halkası"}},
	# --- kılıçlar
	# Alp Kılıcı: dengeli; çapraz iniş → çapraz yükseliş → adımlı baş üstü (v18: her vuruş bir öncekinin bittiği yerden
	# gerilir: aşağıda biten iniş yükselişin hazırlığıdır, yukarıda biten yükseliş baş üstü inişin) (üçüncü vuruş kritik)
	"alp_kilici": {"chain": [{"s": "diag_down", "mult": 1.0, "kb": 110.0, "dash": 10.0}, {"s": "diag_up", "mult": 1.0, "kb": 110.0}, {"s": "step_down", "mult": 1.35, "kb": 240.0, "dash": 30.0, "last": true}],
		"pause": {"s": "cross_x", "mult": 1.1, "kb": 150.0, "name": "Alp Çaprazı"}},
	# Yıldırım Kılıcı (katana; v25 yeniden: YK tablosu): Çekiş (iaido yatay hilal) → Şimşek Çaprazı (iki dik çapraz kesik,
	# kesişmede çıtırdayan kıvılcım) → Şimşek Çekişi (yerde göz açıp kapayıncaya dek ileri atılan kesik çizgisi; vurulan
	# düşmanda gecikmeli gök çatırtısı, yalnız görsel); ağır: şimşek hamlesi (v21). Eski geri sıçrayış (havaya hoplatıyordu) kalktı.
	"yildirim_kilici": {"chain": [{"s": "yk_iai", "mult": 1.0, "kb": 100.0, "dash": 16.0}, {"s": "yk_cross", "mult": 0.55, "kb": 80.0, "xspark": true}, {"s": "yk_flash", "mult": 1.35, "kb": 200.0, "flash": true, "last": true}],
		"pause": {"s": "iai", "mult": 1.5, "kb": 140.0, "dash": 70.0, "crit": true, "name": "Şimşek Çekişi"}},
	# Pala (kasap): çapraz doğrama → ters el → tam gövde çark; çarkta tuş basılıysa 1,2 sn döner, iki yanı biçer
	"pala": {"chain": [{"s": "diag_down", "mult": 1.0, "kb": 100.0, "dash": 15.0}, {"s": "back", "mult": 1.05, "kb": 110.0}, {"s": "spin_2h", "mult": 1.2, "kb": 160.0, "spin_hold": true, "last": true}],
		"pause": {"s": "lunge", "mult": 1.5, "kb": 200.0, "dash": 70.0, "name": "Pala Akını"}},
	# Yatağan (düellocu): ters el → düz → geriye sıçrayarak kesik (çekilirken kesin kritik) → hücum
	"yatagan": {"chain": [{"s": "reverse_grip", "mult": 0.9, "kb": 70.0}, {"s": "horiz", "mult": 0.9, "kb": 70.0}, {"s": "backstep", "mult": 1.0, "kb": 90.0, "backstep": true, "crit": true}, {"s": "lunge", "mult": 1.4, "kb": 160.0, "dash": 80.0, "last": true}],
		"pause": {"s": "flurry", "mult": 0.85, "kb": 60.0, "name": "Yatağan Fırtınası"}},
	# Ayaz Kılıcı: ağır ve ölçülü iki vuruş: alçak süpürme → adımlı iniş (don yükü biriktirir)
	"ayaz_kilici": {"chain": [{"s": "sweep_low", "mult": 1.0, "kb": 100.0}, {"s": "step_down", "mult": 1.4, "kb": 220.0, "slam": true, "last": true}],
		"pause": {"s": "spin_2h", "mult": 1.3, "kb": 160.0, "name": "Ayaz Halkası"}},
	# Ulu Kılıç (dev kılıç): baş üstü iniş → tam gövde çark; savuruş boyunca süper zırh (atk.super_armor)
	"ulu_kilic": {"chain": [{"s": "overhead_2h", "mult": 1.0, "kb": 220.0, "slam": true, "sa": true}, {"s": "spin_2h", "mult": 1.25, "kb": 260.0, "sa": true, "last": true, "fc": true}],
		"pause": {"s": "helicopter", "mult": 1.5, "kb": 260.0, "sa": true, "name": "Ulu Çark"}},
	# Ruh Kılıcı: her kesik ruh hilali salar; v19: düz → iniş → yükselen kesik (havaya atar; palayla aynı açılmasın)
	"ruh_kilici": {"chain": [{"s": "horiz", "mult": 1.0, "kb": 80.0, "wave": true}, {"s": "down", "mult": 1.0, "kb": 80.0, "wave": true}, {"s": "rise", "mult": 1.2, "kb": 60.0, "launch": 220.0, "wave": true, "last": true}],
		"pause": {"s": "spin", "mult": 1.2, "kb": 120.0, "wave": true, "name": "Ruh Fırtınası"}},
	# Ay Palası (dansçı): beşli zincir, her adım hızlanır; geri sıçrayışla aradan çıkar, çift saplamayla biter
	"ay_palasi": {"chain": [{"s": "twirl", "mult": 1.0, "kb": 40.0}, {"s": "dual_r", "mult": 1.0, "kb": 40.0}, {"s": "dual_l", "mult": 1.0, "kb": 40.0}, {"s": "backstep", "mult": 1.0, "kb": 60.0, "backstep": true}, {"s": "thrust", "mult": 1.4, "kb": 150.0, "double": true, "last": true}],
		"pause": {"s": "flurry", "mult": 0.85, "kb": 50.0, "name": "Ay Dansı"}},
	# --- ağır silahlar
	# Gürz (v19): kısa baş üstü ezme → yel değirmeni → sıçrayıp çakma (üçlü, Nutcracker gibi; bitiriş kesin kritik); ağır sersemletir
	"gurz": {"chain": [{"s": "heavy", "mult": 0.9, "kb": 200.0}, {"s": "windmill", "mult": 1.0, "kb": 280.0, "shock": true}, {"s": "slam", "mult": 1.25, "kb": 300.0, "slam": true, "shock": true, "last": true, "fc": true}],
		"pause": {"s": "slam", "mult": 1.7, "kb": 320.0, "shock": true, "slam": true, "name": "Dağ Devirici"}},
	# Çivili Topuz: hızlı iniş → aparkat (havaya) → sıçrayıp çakma (zırh kırığı biriktirir)
	"civili_topuz": {"chain": [{"s": "down", "mult": 1.0, "kb": 200.0}, {"s": "uppercut_2h", "mult": 1.1, "kb": 160.0, "launch": 320.0}, {"s": "slam", "mult": 1.2, "kb": 280.0, "slam": true, "shock": true, "last": true}],
		"pause": {"s": "slam", "mult": 1.6, "kb": 300.0, "shock": true, "slam": true, "name": "Çivi Yağmuru"}},
	# Dağ Çekici: en ağır tempo: baş üstü iniş (şok, süper zırh) → aparkat; havadaki düşman yere çakılır
	"dag_cekici": {"chain": [{"s": "overhead_2h", "mult": 1.0, "kb": 320.0, "shock": true, "slam": true, "sa": true}, {"s": "uppercut_2h", "mult": 1.2, "kb": 240.0, "launch": 340.0, "last": true}],
		"pause": {"s": "slam", "mult": 1.9, "kb": 360.0, "shock": true, "slam": true, "name": "Dağ Yıkan"}},
	# Savaş Baltası: kancayla çek → fırlat (ikinci basış); bekleme: tam gövde çark
	"savas_baltasi": {"chain": [{"s": "axe_hook", "mult": 1.0, "kb": 40.0, "pull": 140.0}, {"s": "axe", "mult": 0.0, "kb": 0.0, "axe": true, "last": true}],
		"pause": {"s": "spin_2h", "mult": 1.35, "kb": 180.0, "name": "Balta Çarkı"}},
	# --- sırıklar
	# Teber: geniş sırık süpürmesi → alçak biçme (çelme) → baş üstü iniş
	"teber": {"chain": [{"s": "pole_sweep", "mult": 1.0, "kb": 120.0}, {"s": "sweep_low", "mult": 1.05, "kb": 60.0, "trip": true}, {"s": "overhead_2h", "mult": 1.5, "kb": 260.0, "slam": true, "last": true, "fc": true}],
		"pause": {"s": "helicopter", "mult": 1.2, "kb": 200.0, "name": "Teber Çarkı"}},
	# Erlik Tırpanı: biçme düşmanı kendine çeker → alçak süpürme → tam gövde çark; bekleme: büyük biçme (çekiş)
	"erlik_tirpani": {"chain": [{"s": "reap", "mult": 1.0, "kb": 30.0, "pull": 240.0}, {"s": "sweep_low", "mult": 1.1, "kb": 140.0}, {"s": "spin_2h", "mult": 1.3, "kb": 180.0, "last": true}],
		"pause": {"s": "reap", "mult": 1.7, "kb": 30.0, "pull": 320.0, "slam": true, "name": "Ruh Biçen"}},
	# Kargı (v18): saplama → alçak saplama → alttan baş üstüne geniş süpürme (havaya kaldırır; Dead Cells mızrağı gibi
	# saplama-saplama-süpürme);
	# bekleme bitirişi uzun hamle; ↑+J sırık atlayışı
	"kargi": {"chain": [{"s": "pole_thrust", "mult": 1.0, "kb": 150.0}, {"s": "pole_thrust_lo", "mult": 1.1, "kb": 170.0, "dash": 20.0}, {"s": "pole_rise", "mult": 1.35, "kb": 200.0, "launch": 160.0, "dash": 24.0, "last": true}],
		"pause": {"s": "lunge", "mult": 1.6, "kb": 220.0, "dash": 90.0, "name": "Süngü Akını"}},
	# --- çift bıçaklar / pençeler
	# İkiz Bıçak: sol-sağ-sol hızlı kesikler → 4. vuruş: çapraz kesikle düşmanın içinden geçiş
	"ikiz_bicak": {"chain": [{"s": "dual_l", "mult": 1.0, "kb": 45.0}, {"s": "dual_r", "mult": 1.0, "kb": 45.0}, {"s": "rake", "mult": 0.9, "kb": 45.0}, {"s": "cross_dash", "mult": 1.3, "kb": 120.0, "through": true, "last": true}],
		"pause": {"s": "flurry", "mult": 0.8, "kb": 50.0, "name": "Gölge Dişleri"}},
	# Kurt Pençeleri: tırmık → ters el → çömelmeden yükseliş (havaya atar; havada sıçrama mekaniğiyle sürer)
	"kurt_pencesi": {"chain": [{"s": "rake", "mult": 1.0, "kb": 50.0}, {"s": "dual_r", "mult": 1.0, "kb": 50.0}, {"s": "rise", "mult": 1.2, "kb": 60.0, "launch": 240.0, "last": true}],
		"pause": {"s": "flurry", "mult": 0.85, "kb": 60.0, "name": "Pençe Seli"}},
	# --- kırbaçlar
	# Kement: şaklama + yan şaklama; uçtan isabet kesin kritik (menzil ödülü), yakala mekaniği çeker
	"kement": {"chain": [{"s": "whip_crack", "mult": 1.0, "kb": 40.0, "whip": true, "tipcrit": true}, {"s": "whip_side", "mult": 1.1, "kb": 60.0, "whip": true, "tipcrit": true, "last": true}],
		"pause": {"s": "spin", "mult": 1.2, "kb": 120.0, "whip": true, "name": "Kement Halkası"}},
	# Od Kamçısı: şaklama → alçak yer süpürmesi → şaklama; uçtan isabet kritik
	"od_kamcisi": {"chain": [{"s": "whip_crack", "mult": 1.0, "kb": 40.0, "whip": true, "tipcrit": true}, {"s": "sweep_low", "mult": 1.1, "kb": 60.0, "whip": true}, {"s": "whip_crack", "mult": 1.2, "kb": 80.0, "whip": true, "tipcrit": true, "last": true}],
		"pause": {"s": "spin", "mult": 1.2, "kb": 120.0, "whip": true, "name": "Od Halkası"}},
	# --- v7
	# Yılan Kılıcı: ters el → saplama → alçak süpürme (çelme); her vuruş zehir
	"yilan_kilici": {"chain": [{"s": "reverse_grip", "mult": 1.0, "kb": 90.0}, {"s": "thrust", "mult": 1.0, "kb": 120.0}, {"s": "sweep_low", "mult": 1.3, "kb": 140.0, "trip": true, "last": true}],
		"pause": {"s": "twirl", "mult": 1.1, "kb": 100.0, "venom": true, "name": "Yılan Dansı"}},
	# Kor Çekici (v19): çekiç yerde sürüklenir, kor saçarak alttan kalkar (yakar, hafif kaldırır) → baş üstü iniş (kor gölü, bitiriş kesin kritik)
	"kor_cekici": {"chain": [{"s": "ground_drag", "mult": 1.0, "kb": 160.0, "launch": 140.0, "burn": 2.0}, {"s": "overhead_2h", "mult": 1.25, "kb": 240.0, "slam": true, "last": true, "fc": true}],
		"pause": {"s": "slam", "mult": 1.7, "kb": 320.0, "shock": true, "slam": true, "name": "Kor Yağmuru"}},
	# Rüzgâr Kılıcı (hava): çekiş → ters el (v25: eski geri sıçrayış oyuncuyu havaya hoplatıyordu; yerde ters el kesiği) →
	# yükselen kesik (DÜŞMANI havaya atar, oyuncu yerde kalır; havadaki düşmana kritik)
	"ruzgar_kilici": {"chain": [{"s": "iai", "mult": 1.0, "kb": 70.0, "dash": 20.0}, {"s": "back", "mult": 1.0, "kb": 70.0}, {"s": "rise", "mult": 1.2, "kb": 60.0, "launch": 300.0, "last": true}],
		"pause": {"s": "helicopter", "mult": 1.2, "kb": 160.0, "name": "Kasırga Dansı"}},
	# --- v10
	# Tulpar Mızrağı: her saplama ileri taşır; uzun hamleyle biter (koşarken hepsi kritik)
	"tulpar_mizragi": {"chain": [{"s": "pole_thrust", "mult": 1.0, "kb": 140.0, "dash": 30.0}, {"s": "pole_thrust", "mult": 1.05, "kb": 150.0, "dash": 30.0}, {"s": "lunge_long", "mult": 1.5, "kb": 260.0, "dash": 90.0, "last": true}],
		"pause": {"s": "helicopter", "mult": 1.3, "kb": 200.0, "name": "Tulpar Çarkı"}},
	# Böri Hançeri (suikastçı): üç hızlı kesik → çapraz kesikle düşmanın arkasına geçiş (arkadan kritik)
	"bori_hanceri": {"chain": [{"s": "dual_l", "mult": 1.0, "kb": 30.0}, {"s": "dual_r", "mult": 1.0, "kb": 30.0}, {"s": "reverse_grip", "mult": 1.0, "kb": 30.0}, {"s": "cross_dash", "mult": 1.5, "kb": 110.0, "through": true, "last": true}],
		"pause": {"s": "flurry", "mult": 0.9, "kb": 40.0, "name": "Börü Dişleri"}},
	# İkiz Balta: sol-sağ doğrama (ikincisi çift) → tam gövde çark
	"ikiz_balta": {"chain": [{"s": "dual_l", "mult": 1.0, "kb": 120.0}, {"s": "dual_r", "mult": 1.0, "kb": 120.0, "double": true}, {"s": "spin_2h", "mult": 1.3, "kb": 220.0, "last": true}],
		"pause": {"s": "helicopter", "mult": 1.4, "kb": 200.0, "name": "Kanlı Çark"}},
	# Ulu Kayın Asası: sırık süpürmesi → çevrim → aparkat (havaya atar; geri itme 1,8x)
	"kayin_asasi": {"chain": [{"s": "pole_sweep", "mult": 1.0, "kb": 220.0}, {"s": "twirl", "mult": 0.9, "kb": 200.0}, {"s": "uppercut_2h", "mult": 1.3, "kb": 240.0, "launch": 320.0, "last": true}],
		"pause": {"s": "helicopter", "mult": 1.2, "kb": 320.0, "name": "Kayın Fırtınası"}},
	# Bozgun Kılıcı: çapraz → tam gövde çark (süper zırh) → adımlı iniş
	"bozgun_kilici": {"chain": [{"s": "diag_down", "mult": 1.0, "kb": 180.0}, {"s": "spin_2h", "mult": 1.1, "kb": 200.0, "sa": true}, {"s": "step_down", "mult": 1.4, "kb": 280.0, "slam": true, "sa": true, "last": true}],
		"pause": {"s": "cross_x", "mult": 1.3, "kb": 220.0, "name": "Bozgun Çaprazı"}},
}
const COMBOS_EXTRA := {}

## ------------------------------------------------------------------ v19 DÖVÜŞ: yeni mekanikler
## Ayrıntı: docs/TASARIM.md "Dövüş v19". Süreler gerçek saniye (Game.clock(): vuruş donması / ağır çekim sırasında da akar).
##   Kut Yankısı   isabetin hemen ardından (donmanın içinde ya da ~150 ms içinde) basılan saldırı: sıradaki vuruş daha
##                 hızlı gerilir, daha sert vurur ve izi altın mürekkeple çizilir (v22: 70 ms sonra kendiliğinden gelen
##                 ikinci "yankı kesiği" kalktı, hasarı vuruşun kendisine eklendi). İsabetten ÖNCE basmak (tuşa ezbere
##                 basmak) yankıyı bozar. Art arda üç yankı: Kut Mührü (sıradaki isabet kesin kritik). Usul vuruşuna da
##                 denk gelirse çift yankı (daha güçlü vuruş).
##   Çarpışma      savuruşun ilk anlarında (bıçak önünde dönerken) gelen darbe / mermi bıçağa çarpar: hasar yok, saldıran
##                 sersemler, mermi geri sekiştirilir; sıradaki vuruş kesin kritik ("karşılık").
##   Karşı Vuruş   saldırı hazırlığındaki ("!") düşmana isabet: hazırlığı keser (ağırlarınki de), kesin kritik.
##                 v26: yalnızca "!"yi okuyan savuruş: hazırlık başladıktan sonra, zincirin akışı dışında (beklemeden)
##                 başlamış olmalı; zırhlı "!!" hazırlığa karşı vuruş yok (ezilen kombo hazırlıkları kendiliğinden kesmez).
##   Kut Alma      duruşu kırılmış / sersemlemiş / donmuş ve canı az düşman (kırmızı mürekkep mührü) saldırıyla infaz edilir:
##                 kısa ağır çekim, silaha özgü bitiriş, can + Kut.
##   İsabet iptali isabetten kısa süre sonra zıplama ve ikincil, kilidi keser (hava kombosuna / yaya geçiş).
const V19 := {
	"yk_win": 0.15,          # isabetten sonra yankı penceresi
	"yk_wind": 0.72,         # yankılı vuruşun hazırlığı (ve tutuşu) bu orana iner (v26 0,55 → 0,72: yankı zinciri "ışık hızı" olmasın)
	"yk_mult": 1.3,          # yankılı vuruş hasarı
	"yk_echo": 0.35,         # v22: yankı artık ayrı, gecikmeli bir kesik değil: bu oran vuruşun kendisine eklenir
	                         # (usul vuruşunda iki kat); görseli savuruşun kendi izinin altın mürekkebe dönmesi
	"yk_seal": 3,            # art arda bu kadar yankı: Kut Mührü
	"pr_win": 0.16,          # savuruş vuruşa başladıktan bu kadar sonrasına dek çarpışma (savuşturma)
	"pr_stun": 0.8,
	"pr_stun_heavy": 0.45,
	"pr_riposte": 1.2,       # çarpışmadan sonra karşılık (kesin kritik) penceresi
	"ex_hp": 0.3,            # infaz: canın bu oranı altında (seçkinde ex_hp_elite)
	"ex_hp_elite": 0.18,
	"ex_reach": 20.0,        # silah eriminin bu kadar ötesine dek infaz başlar
	"ex_heal": 0.04,
	"ex_kut": 12.0,
	"hc_cancel": 0.05,       # isabetten bu kadar sonra zıplama / ikincil kilidi keser
	"fin_hs": 0.02,          # zincir bitirişine ek duraklama
}
## v22 vuruş efekti sadeleştirme (Player._melee_hits → FX.hit_k): aynı düşmana "repeat_t" sn içinde gelen sıradan vuruş
## "lite" oranında küçük / sade efekt alır (sayı, kan, sıçrantı, kıvılcım); aynı savuruşun 2., 3. düşmanı ×extra_foe.
## İlk vuruş, zincir bitirişi, ağır saldırı, kesin kritik ve infaz her zaman tam efekt.
const V22_FX := {"repeat_t": 0.5, "lite": 0.5, "extra_foe": 0.75}
## ------------------------------------------------------------------ v25 Yıldırım Kılıcı
## Geri bildirim: "Yıldırım Kılıcı'nın kombosu çok çirkin; sanatsal, güzel bir şey yapın." Zincir (v23 3B düzlemleriyle):
##   Çekiş          iaido: el kalçada, bıçak kında; tek hamlede yassı yatay elipste geniş hilal. Bıçak ucunun yolunda
##                  şimşek parlaklığında yay (SimsekKesikFX "arc": ön uçta kalın beyaz çekirdek, yay boyunca kılcallar).
##   Şimşek Çaprazı iki dik çapraz kesik iki ayrı düzlemde (baş üstünden öne-aşağı, alttan öne-yukarı); her geçişin
##                  parlak yayı, ikinci geçişte kesişme noktasında çıtırdayan mürekkep kıvılcımları (kısa şimşek dalları).
##   Şimşek Çekişi  bitiriş: bıçak kına, gövde çömelir (okunur tutuş); bırakışta yerde göz açıp kapayıncaya dek ileri
##                  (flash_px / flash_t) atılır, geçtiği yol ekranı bir an ikiye bölen kesik çizgisiyle (SimsekKesikFX
##                  "line") parlar; vurulan her düşmanın tepesinde crack_delay sn sonra gök çatırtısı — yalnızca görsel ve
##                  ses: ek vuruş / hasar yok, hasar oyuncunun kendi vuruşunda (v22 kontrol ilkesi).
## Ağır (basılı tut): v21 Yıldırım Hamlesi aynı (tam şarjda deldiği düşmanlara yıldırım); yoluna aynı kesik çizgisi.
## v25: yukarı süpüren ağır savuruşlarda mürekkep hilalinin genişlik çarpanı (Player._sample_trail)
const UPSWEEP_THIN := {"uppercut_2h": 0.55, "ground_drag": 0.7}
const YK := {"flash_px": 84.0, "flash_t": 0.075, "crack_delay": 0.16, "col": Color(0.62, 0.86, 1.0)}
## İnfaz (Kut Alma) savuruşu silah sınıfına göre (_tempo_class)
const EXEC_SW := {"hancer": "cross_dash", "duello": "iai", "kilic": "iai", "mizrak": "stab_heavy", "kirbac": "whip_crack",
	"uzun": "reap", "agir": "overhead_2h", "dev": "overhead_2h"}
const CHAIN_WINDOW := 0.28   # bu süre içinde basarsan zincir sürer
## v22: bekleme bitirişi (zincirden sonra 0,28-0,95 sn bekleyip basınca kendiliğinden çıkan başka hamle) kaldırıldı:
## hamle zamanlamayla değişmez; bekledikten sonraki basış yeni bir zincir açar. COMBOS "pause" kayıtları kullanılmıyor.

## Ağır saldırılar: saldırı tuşu basılı tutulunca (hazırlık bitince HOLD_T kadar daha basılıysa) şarj başlar;
## bırakınca silahın özgün ağır vuruşu çıkar. Şarj HEAVY_MAX'a kadar hasarı 1.9 kata çıkarır.
const HOLD_T := 0.16
const HEAVY_MAX := 0.55   # v18: tam şarj 0,85 → 0,55 sn (Dead Cells ağır silah hazırlığı 0,4-0,5 sn)
const HEAVIES := {
	"slash": {"s": "overhead_2h", "mult": 1.6, "kb": 260.0, "slam": true, "name": "Ağır Darbe"},
	"dual": {"s": "cross_dash", "mult": 1.5, "kb": 150.0, "through": true, "name": "Çapraz"},
	"heavy": {"s": "slam_2h", "mult": 1.8, "kb": 340.0, "shock": true, "slam": true, "stun": 1.2, "name": "Yıkım"},
	"thrust": {"s": "stab_heavy", "mult": 1.9, "kb": 260.0, "dash": 60.0, "name": "Deliş"},
	"whip": {"s": "whip_crack", "mult": 1.6, "kb": 150.0, "whip": true, "tipcrit": true, "name": "Şaklama"},
	"alp_kilici": {"s": "overhead_2h", "mult": 1.6, "kb": 260.0, "slam": true, "name": "Alp Darbesi"},
	"yildirim_kilici": {"s": "iai", "mult": 1.4, "kb": 60.0, "lightning": true, "name": "Yıldırım Hamlesi"},
	"pala": {"s": "reap", "mult": 1.6, "kb": 60.0, "pull": 200.0, "name": "Kanlı Kanca"},
	"yatagan": {"s": "iai", "mult": 1.9, "kb": 180.0, "dash": 50.0, "name": "Yatağan Çekişi"},
	"ayaz_kilici": {"s": "overhead_2h", "mult": 1.6, "kb": 220.0, "slam": true, "name": "Buz Yarığı"},
	"ulu_kilic": {"s": "slam_2h", "mult": 2.0, "kb": 380.0, "shock": true, "slam": true, "sa": true, "name": "Ulu Yıkım"},
	"ruh_kilici": {"s": "cross_x", "mult": 1.5, "kb": 120.0, "wave": true, "name": "Ruh Çaprazı"},
	"ay_palasi": {"s": "helicopter", "mult": 1.5, "kb": 160.0, "name": "Dolunay"},
	"gurz": {"s": "slam_2h", "mult": 1.8, "kb": 340.0, "shock": true, "slam": true, "stun": 1.4, "name": "Gürz Yıkımı"},
	"civili_topuz": {"s": "slam_2h", "mult": 1.8, "kb": 320.0, "shock": true, "slam": true, "stun": 1.2, "name": "Çivi Çakışı"},
	"dag_cekici": {"s": "slam_2h", "mult": 2.1, "kb": 400.0, "shock": true, "slam": true, "stun": 1.6, "sa": true, "name": "Dağ Çökertme"},
	"savas_baltasi": {"s": "overhead_2h", "mult": 1.8, "kb": 300.0, "slam": true, "name": "Balta Yarığı"},
	"teber": {"s": "sweep_low", "mult": 1.7, "kb": 240.0, "launch": 260.0, "name": "Diz Biçen"},
	"erlik_tirpani": {"s": "reap", "mult": 2.0, "kb": 40.0, "pull": 340.0, "name": "Erlik'in Orağı"},
	"kargi": {"s": "stab_heavy", "mult": 1.9, "kb": 260.0, "dash": 70.0, "name": "Kargı Delişi"},
	"ikiz_bicak": {"s": "cross_dash", "mult": 1.5, "kb": 150.0, "through": true, "name": "İkiz Çapraz"},
	"kurt_pencesi": {"s": "rake", "mult": 1.7, "kb": 120.0, "name": "Kurt Tırmığı"},
	"kement": {"s": "whip_crack", "mult": 1.6, "kb": 150.0, "whip": true, "tipcrit": true, "name": "Kement Şaklaması"},
	"od_kamcisi": {"s": "whip_crack", "mult": 1.6, "kb": 150.0, "whip": true, "tipcrit": true, "name": "Od Şaklaması"},
	"yilan_kilici": {"s": "reap", "mult": 1.6, "kb": 200.0, "venom": true, "name": "Zehir Orağı"},
	"kor_cekici": {"s": "slam_2h", "mult": 1.9, "kb": 360.0, "shock": true, "slam": true, "stun": 1.2, "name": "Cehennem Çakışı"},
	"ruzgar_kilici": {"s": "cross_x", "mult": 1.5, "kb": 140.0, "name": "Yel Çaprazı"},
	"tulpar_mizragi": {"s": "stab_heavy", "mult": 2.0, "kb": 300.0, "dash": 160.0, "name": "Tulpar Akını"},
	"bori_hanceri": {"s": "cross_dash", "mult": 1.7, "kb": 120.0, "through": true, "name": "Gölge Çaprazı"},
	"ikiz_balta": {"s": "spin_2h", "mult": 1.7, "kb": 260.0, "spin_hold": true, "name": "Kanlı Çark"},
	"kayin_asasi": {"s": "pole_sweep", "mult": 1.7, "kb": 420.0, "stun": 0.8, "name": "Kayın Savuruşu"},
	"bozgun_kilici": {"s": "slam_2h", "mult": 2.0, "kb": 340.0, "shock": true, "slam": true, "sa": true, "name": "Bozgun Yarığı"},
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
	# v27
	"gun_ay_ikizi": {"trail": 1.1, "col": Color(1.0, 0.85, 0.45), "hit": "crescent_slash", "hit_scale": 0.6, "extra": "ghost"},
	"kistin": {"trail": 1.5, "col": Color(0.9, 0.8, 0.7), "hit": "resonant_break", "hit_scale": 0.7, "extra": "dust"},
	"albasti_hanceri": {"trail": 0.55, "col": Color(1.0, 0.35, 0.4), "hit": "crescent_slash", "hit_scale": 0.42, "extra": "blood"},
	"cevgen": {"trail": 1.5, "col": Color(0.8, 1.0, 0.85), "hit": "resonant_break", "hit_scale": 0.75, "extra": "dust"},
}
## Silah ses sınıfı: savuruş (savur_<sınıf>) ve darbe (darbe_<...>) sesleri gerçek kayıt katmanlarından seçilir
const WSND := {"alp_kilici": "kilic", "pala": "kilic", "yatagan": "kilic", "ayaz_kilici": "kilic", "yilan_kilici": "kilic", "ruzgar_kilici": "kilic",
	"yildirim_kilici": "katana", "ulu_kilic": "dev", "erlik_tirpani": "dev", "gurz": "cekic", "civili_topuz": "cekic", "dag_cekici": "cekic",
	"kor_cekici": "cekic", "savas_baltasi": "balta", "teber": "balta", "kargi": "sirik", "ikiz_bicak": "bicak", "kurt_pencesi": "bicak",
	"ay_palasi": "bicak", "kement": "kirbac", "od_kamcisi": "kirbac", "ruh_kilici": "ruh",
	"tulpar_mizragi": "sirik", "bori_hanceri": "bicak", "ikiz_balta": "balta", "kayin_asasi": "sirik", "bozgun_kilici": "dev",
	"gun_ay_ikizi": "katana", "kistin": "cekic", "albasti_hanceri": "bicak", "cevgen": "cekic"}
## İki elle tutulan silahlar: arka el kabzanın gerisine (bıçak yönünde negatif ofset) IK ile yerleşir
const TWO_HANDED := {"ulu_kilic": -7.0, "dag_cekici": -9.0, "kor_cekici": -8.0, "gurz": -6.0, "civili_topuz": -6.0, "teber": -13.0, "kargi": -14.0,
	"erlik_tirpani": -12.0, "savas_baltasi": -7.0, "tulpar_mizragi": -15.0, "kayin_asasi": -14.0, "bozgun_kilici": -8.0,
	"cevgen": -12.0}

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
var roll_buf := 0.0        # v17 ara bellekler (FLOW)
var sec_buf := 0.0
var _mel_down_t := -1.0    # saldırı tuşu ne zamandır basılı (-1: basılı değil); ağır saldırı bununla tanınır
var _heavy_armed := false  # hafif silah: basılı tutulan tuşla başlayan saldırı -> süre dolunca ağır saldırıya geçer
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
var _mantle_dur := 0.16
var _prev_vy := 0.0
var hero_t := -1.0          # v34 Kahraman İnişi: >= 0 dalış sürüyor (havada; süre)
var hero_pose_t := 0.0      # iniş pozu (diz yerde, yumruk toprakta)
var fall_stun_t := 0.0      # yüksek düşüş sersemlemesi
var _air_top := 0.0         # havadaki en yüksek ayak hizası (düşüş yüksekliği buradan)
var last_fall_h := 0.0      # son inişin düşüş yüksekliği (px; test / öğretici)
var hero_stats := {"n": 0, "hits": 0, "h": 0.0, "vy": 0.0, "stun": 0, "step": 0, "mantle": 0}   # test sayaçları
const COMBO_RANKS := [[5, "ER", Color(0.9, 0.9, 0.95)], [12, "ALP", Color(0.6, 0.95, 1.0)], [22, "BAHADIR", Color(1.0, 0.85, 0.4)],
	[35, "HAN", Color(1.0, 0.55, 0.3)], [55, "DESTAN", Color(1.0, 0.35, 0.6)]]
var sprint := false        # Shift basılı tutuluyor: koşu
var _roll_hold := 0.0
var _haz_t := 0.0          # tehlike karosu: sektirme sonrası dokunulmazlık (v25; sürekli hasar yok)
var _haz_safe := Vector2.INF   # v25: son güvenli zemin (çukura ikinci düşüşte buraya dönülür)
var _haz_last := -9.0          # v25: son çukur vuruşunun anı (Game.clock)
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
# v12: Don Değiştirme, Usul Vuruşu (Üç Âlem v25'te kaldırıldı)
var don: DonForm
var don_on := false
var don_kind := ""
var usul_streak := 0
var usul_buff_t := 0.0
var usul_strong := false
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
var _vs_v := Vector2.ZERO  # v11: ölçek yayının hızı
var _lean_v := 0.0
var _feel_face := 1
var _feel_floor := true
var _feel_vy := 0.0
var _feel_vx := 0.0
var _was_floor := true
var _fall_peak := 0.0
var _dust_t := 0.0
var _ghost_t := 0.0
var _skid := false
var _trail: WeaponTrail
var _trail_prev: Array = []
# kol iskeleti
var arm_root: Node2D
var sac: BenguSac  # v20: Bengü'nün uzun saçı (scripts/core/BenguSac.gd)
var arm_upper: Sprite2D
var arm_fore: Sprite2D
var arm_fist: Sprite2D
var arm_root_b: Node2D
var arm_upper_b: Sprite2D
var arm_fore_b: Sprite2D
var arm_fist_b: Sprite2D
var wind_n := 0  # Rüzgâr Kılıcı: üçüncü kesik sayacı
var arm_meta: Dictionary = {}
var arm_inv := 1.0  # kol parçası doku yoğunluğunun tersi (bengu_kol.json "texel")
var _hand_local := Vector2.ZERO
## Savuruş hissi (v14): hazırlık tutuşu, kırbaç gecikmesi (bıçak kolu geriden izler), aşma-oturma yayı
## Kusursuz Kaçış (v14): darbenin isabet edeceği ilk 120 ms içinde yuvarlanırsan zaman yavaşlar, sıradaki vuruş kritik olur
var perfect_t := 0.0
var perfect_cd := 0.0
var _pd_done := false
const PERFECT_WIN := 0.12
var _whip := 0.0
var _whip_v := 0.0
var _prev_a1 := 0.0
var _prev_a1_ok := false
var _over_amp := 0.0
var _over_t := 1.0
var _over_dir := 0.0
## Vuruş kademeleri: 0 hafif zincir vuruşu, 1 orta (zincir sonu / ağır silah), 2 büyük (kritik, ağır şarj, bitiriş)
## [hitstop, kamera itişi, travma, kıvılcım sayısı, darbe yıldızı boyu]
const HIT_FEEL := [[0.035, 1.6, 0.0, 4, 0.45], [0.065, 3.2, 0.16, 7, 0.75], [0.09, 4.5, 0.3, 10, 1.1]]   # v25: büyük 0,105 → 0,09 (dip eğrisi, Game.HS)
## Yay: kiriş + yaydaki ok çizimi (kol iskeletinin içinde, silahın üstünde)
var bow_str: BowString
var bow_rel_t := 0.0        # bırakış sonrası takip: kiriş titrer, yay geri teper
var _bow_full := false
var _bow_nock := Vector2.ZERO
var _bow_nock_ok := false
var _bow_tip_cache: Dictionary = {}
const BOW_REL := 0.24
const BAKED_ARROW_BOWS := ["saganak_yayi", "tufan_yayi", "od_oklari"]
## v19 Okçuluk (Okculuk.gd): gerilme / atış / tam bırakış / ok sökme / ok toplama / süzülüş
var okc: Okculuk
var sanat: SavasSanati   # v27 savaş sanatları (scripts/actors/SavasSanati.gd)


class BowString extends Node2D:
	## Kiriş: uçlardan geri çekilen gez noktasına iki çizgi; isteğe bağlı yaydaki ok.
	## v1 piksel; stil v2 mürekkep: kenar yumuşatmalı koyu mürekkep kiriş + açık çekirdek, yaydaki ok uçuştaki okla
	## aynı mürekkep sprite'ı, tam bırakış penceresi: ok ucunda daralan altın halka ve dört kollu parıltı.
	var top := Vector2.ZERO
	var bot := Vector2.ZERO
	var nock := Vector2.ZERO
	var dir := 1
	var arrow_on := false
	var arrow_head := Color(0.88, 0.92, 0.98)
	var fletch := Color(0.85, 0.25, 0.2)
	var glow := 0.0
	var str_col := Color(0.93, 0.88, 0.75)
	var ring := -1.0          # tam bırakış halkası 1 -> 0 (yoksa < 0)
	var perfect := false      # pencere açık: parıltı
	var variant := "normal"
	var tilt := 0.0           # v2: hedef yardımı eğimi (yay ve ok bu açıyla döner)
	var pull := 0.0           # v31: gerilme (0..1): kiriş incelir, parlar, iki yanında titreşen gerilim telleri
	var _ink_arrow: Sprite2D
	var _ink_var := ""

	func _draw_ink() -> void:
		var pts := PackedVector2Array([top, nock, bot])
		# v31 gerilim: kiriş gerildikçe incelir ve ışır; gezde küçük mürekkep düğümü; tam gerilmede iki yanında hafifçe
		# titreşen soluk gerilim telleri (kirişin titreşimi)
		var tens := clampf(pull, 0.0, 1.0)
		var inkc := Color(0.05, 0.035, 0.04, 0.95)
		if tens > 0.3:
			var tt := Time.get_ticks_msec() / 1000.0
			for sg: float in [-1.0, 1.0]:
				var o := Vector2(0, sg * (0.55 + 0.35 * sin(tt * 95.0 + sg))) * tens
				var tp := PackedVector2Array([top, nock + o, bot])
				draw_polyline(tp, Color(str_col.r, str_col.g, str_col.b, 0.22 * tens), 0.3, true)
		draw_polyline(pts, inkc, 0.95 - 0.2 * tens, true)
		draw_polyline(pts, str_col.lerp(Color(1.2, 1.12, 0.95), 0.55 * tens), 0.38 + 0.06 * tens, true)
		if tens > 0.05:
			draw_circle(nock, 0.7 + 0.5 * tens, inkc)
		# yaydaki ok: uçuştaki okla aynı mürekkep sprite'ı (gövdesi 24 birim), kuyruğu gezde
		if arrow_on:
			if _ink_arrow == null or _ink_var != variant:
				if _ink_arrow:
					_ink_arrow.queue_free()
				_ink_arrow = SusV2.sprite("ok_" + variant, true)
				_ink_var = variant
				if _ink_arrow:
					add_child(_ink_arrow)
			if _ink_arrow:
				_ink_arrow.visible = true
				var k := 0.8 / float(SusV2.meta().get("texel", 4.0))
				_ink_arrow.scale = Vector2(k * dir, k)
				_ink_arrow.rotation = tilt
				_ink_arrow.position = nock + Vector2(dir * 13.6, 0).rotated(tilt)
		elif _ink_arrow:
			_ink_arrow.visible = false
		var head := nock + Vector2(dir * (24.0 if arrow_on else 12.0), 0).rotated(tilt)
		if ring >= 0.0:
			var gc := Color(1.0, 0.86, 0.45, 0.35 + 0.55 * (1.0 - ring))
			draw_arc(head, 2.0 + 7.0 * ring, 0.0, TAU, 28, Color(0.05, 0.035, 0.04, gc.a * 0.7), 0.85, true)
			draw_arc(head, 2.0 + 7.0 * ring, 0.0, TAU, 28, gc, 0.4, true)
		if perfect:
			var t := Time.get_ticks_msec() / 1000.0
			var s := 4.5 + 1.2 * sin(t * 40.0)
			var gc2 := Color(1.0, 0.9, 0.55, 0.95)
			draw_line(head + Vector2(-s, 0), head + Vector2(s, 0), Color(0.05, 0.035, 0.04, 0.7), 1.0, true)
			draw_line(head + Vector2(0, -s), head + Vector2(0, s), Color(0.05, 0.035, 0.04, 0.7), 1.0, true)
			draw_line(head + Vector2(-s, 0), head + Vector2(s, 0), gc2, 0.45, true)
			draw_line(head + Vector2(0, -s), head + Vector2(0, s), gc2, 0.45, true)
			draw_arc(head, 1.6, 0.0, TAU, 16, gc2, 0.6, true)

	func _draw() -> void:
		_draw_ink()
var _blade_local := Vector2.RIGHT
var _last_pose: Array = []     # v18: son çizilen kol pozu (zincirde sonraki savuruş buradan gerilir)
var _last_pose_ok := false
var _plane_rng := RandomNumberGenerator.new()   # v23: savuruş düzlemi sapması (oyunun ortak rastgeleliğine dokunmaz)
var _art: Dictionary = {}   # v27 SanatAnim durumu (gövde eğikliği yayı, leke kareleri)
var since_atk := 9.0       # son saldırının bitişinden beri geçen süre (zincir / bekleme ayrımı)
var last_step := -1
var cast_t := 0.0
# v19 dövüş (V19): Kut Yankısı, Çarpışma karşılığı, infaz
var _yk_contact := -9.0     # son onaylı isabetin anı (Game.clock); yankı penceresi buradan sayılır
var _yk_early := false      # bu savuruşta isabetten önce saldırıya basıldı (yankı bozulur)
var _atk_t0 := -9.0         # v26: son savuruşun başladığı an (Game.clock)
var _atk_fresh := false     # v26: son savuruş zincirin akışında değil, beklemeden sonra yeni başladı (okuyup karşılama)
var _yk_ready := -9.0       # yankı basışının anı: sıradaki savuruş (0,5 sn içinde başlarsa) yankılı
var yk_n := 0               # art arda yankı sayısı (V19.yk_seal'da Kut Mührü)
var _yk_seal := false       # Kut Mührü: sıradaki isabet kesin kritik
var riposte_t := 0.0        # çarpışmadan sonra karşılık penceresi
var v19_stats := {"yanki": 0, "muhur": 0, "carpisma": 0, "karsi": 0, "infaz": 0, "kirilma": 0}  # test sayaçları
## v22 kontrol günlüğü (test: dovus_testi --kontrol): oyuncunun her vuruşu nedeniyle kaydedilir. "basis" = taze bir
## saldırı basışından çıkan savuruş (age = basıştan bu yana oyun zamanı, vuruş donması sayılmaz); "auto" = basışsız
## çıkan vuruş / dönüş / hamle (yankı kesiği, ruh kurdu pençesi, kendiliğinden dönme, düşmana kayan adım...).
var log_on := false
var strike_log: Array = []
var _gt := 0.0              # oyun zamanı (delta toplamı)
var _press_gt := -9.0       # son saldırı basışının oyun zamanı
var _press_used := true     # son basış bir savuruşa harcandı mı
var _press_dir := 0         # v22: son saldırı basışı anındaki yön tuşu (-1, 0, 1)
var _press_hit := false     # v22: son basış süren savuruşun temasından sonra mı (kilitte) yapıldı


func slog(cause: String, move: String, auto: bool, extra := {}) -> void:
	if not log_on:
		return
	var r := {"t": _gt, "f": Engine.get_physics_frames(), "cause": cause, "move": move, "auto": auto,
		"age": (_gt - _press_gt) if not auto else -1.0, "fresh": not _press_used, "facing": facing}
	r.merge(extra, true)
	strike_log.append(r)


func _ready() -> void:
	add_to_group("oyuncu")
	_plane_rng.randomize()
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
	# Kut ışığı: oyuncu karanlık biyomda / ay gölgesinde hiç kaybolmasın (çok kısık, gölgesiz, yakın erim)
	var kl := PointLight2D.new()
	var lg := GradientTexture2D.new()
	lg.width = 128
	lg.height = 128
	lg.fill = GradientTexture2D.FILL_RADIAL
	lg.fill_from = Vector2(0.5, 0.5)
	lg.fill_to = Vector2(1.0, 0.5)
	var gr := Gradient.new()
	gr.set_color(0, Color(1, 1, 1, 1))
	gr.set_color(1, Color(1, 1, 1, 0))
	lg.gradient = gr
	kl.texture = lg
	kl.texture_scale = 1.1
	kl.color = Color(1.0, 0.9, 0.78)
	kl.energy = 0.32
	kl.height = 30.0
	kl.position = Vector2(0, -18)
	add_child(kl)
	wolf_anim = SpriteAnim.new()
	add_child(wolf_anim)
	wolf_anim.setup("bengu_kurt")
	# ruh kurdu: gövdenin ~%24'ü ışıyan doku; 1,6x eklemeli ışıma HDR parıltısıyla bembeyaz yanıyordu
	if wolf_anim.glow:
		wolf_anim.glow.self_modulate = Color(0.7, 0.7, 0.7)
	wolf_anim.mat.set_shader_parameter("tint", Color(0.86, 0.88, 0.92))
	wolf_anim.visible = false
	wolf_anim.z_index = 3
	don = DonForm.new()
	don.visible = false
	don.z_index = 3
	add_child(don)
	# Ön kol iskeleti: üst kol -> ön kol -> silah -> yumruk (yumruk silahın kabzasını örter).
	# anim düğümünün çocuğu: gövdenin ezilme/esneme ve eğilmesini birebir izler.
	var kol := Data.stil_id("bengu_kol", "res://assets/sprites/%s.json")
	arm_meta = Data.load_json("res://assets/sprites/%s.json" % kol)
	arm_inv = 1.0 / float(arm_meta.get("texel", 1.0))  # 1.5x yoğunluklu kol parçaları 2/3 ölçekle çizilir
	var arm_tex := Data.canvas_tex("res://assets/sprites/%s.png" % kol, "")
	var am := ShaderMaterial.new()
	am.shader = Data.INK_SHADER  # mürekkep-cel kol parçaları: gövdeyle aynı süzgeç ve ışık
	if arm_meta.has("alt_row"):  # ışığı aynalanmış ikinci satır: ink_char parçanın açısına göre karıştırır
		am.set_shader_parameter("alt_uv", Vector2(0.0, float(arm_meta["cell"][1]) * float(arm_meta["alt_row"]) / float(arm_tex.get_height())))
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
	weapon.region_enabled = true
	weapon.centered = false
	var wm := ShaderMaterial.new()
	wm.shader = Data.INK_SHADER  # doku ve malzeme _apply_wspr'de (mürekkep-cel silah atlası)
	weapon.material = wm
	weapon.visible = false
	arm_root.add_child(weapon)
	shield_spr = weapon.duplicate()
	shield_spr.material = wm
	arm_root.add_child(shield_spr)
	bow_str = BowString.new()
	bow_str.visible = false
	arm_root.add_child(bow_str)
	okc = Okculuk.new(self)
	sanat = SavasSanati.new(self)
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
	# v20: uzun saç (verlet zinciri, çalışma zamanında mürekkep şeridi; yalnızca stil v2): gövdenin arkası + önü
	sac = BenguSac.ekle(anim, self)
	anim.finished.connect(_on_anim_finished)
	Silah27.attach(self)   # v27 yeni silahların durumu ve çizimi (scripts/core/Silah27.gd)


func set_moon_shade(v: float) -> void:
	## GroundShadow çağırır: gövde, kollar ve silah aynı ay gölgesini alır
	for m in [anim.mat, arm_upper.material if arm_upper else null, weapon.material if weapon else null]:
		if m is ShaderMaterial:
			(m as ShaderMaterial).set_shader_parameter("moon_shade", v)


func _arm_piece_in(root_n: Node2D, tex: Texture2D, region: Rect2, pivot: Vector2, mat: Material) -> Sprite2D:
	var sp := Sprite2D.new()
	sp.texture = tex
	sp.region_enabled = true
	sp.region_rect = region
	sp.centered = false
	sp.offset = -pivot
	sp.scale = Vector2.ONE * arm_inv
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
	sp.scale = Vector2.ONE * arm_inv
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
	if Silah27.node_of(self):
		Silah27.node_of(self).reset()
	_end_trail()
	_cancel_attack(false)
	aim_t = -1.0
	block_t = -1.0
	throw_t = -1.0
	charge_t = -1.0
	last_step = -1
	_want_mel = ""
	melee_buf = 0.0
	sec_buf = 0.0
	_heavy_armed = false
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


func _ledge(f: int, max_h: float) -> Vector2:
	## v34 kenar bulma (fizik sorgusuyla; karo ızgarasına bağlı değil): önde duvar var ve gövde en çok max_h px
	## yükseltilince öne geçebiliyorsa varış noktası (ayak), yoksa Vector2.INF. Baş üstü kapalıysa (tavan) yok.
	var gt := global_transform
	if not test_move(gt, Vector2(f * 2.0, 0)):
		return Vector2.INF
	var h := 4.0
	while h <= max_h + 0.01:
		if test_move(gt, Vector2(0, -h)):
			return Vector2.INF
		var up := gt.translated(Vector2(0, -h))
		var fw := Vector2(f * 9.0, 0)
		if not test_move(up, fw):
			# kenarın üstüne in: öne geçilen yerden aşağı yokla (tam ayak hizası)
			var top := up.translated(fw)
			var col := KinematicCollision2D.new()
			var dy := h + 2.0
			if test_move(top, Vector2(0, h + 2.0), col):
				dy = col.get_travel().y
			if dy >= h - 0.5:
				return Vector2.INF   # öne geçilen yer kenar değil (boşluk)
			return top.origin + Vector2(0, dy)
		h += 4.0
	return Vector2.INF


func _begin_mantle(to: Vector2, dur: float) -> void:
	_mantle_a = global_position
	_mantle_b = to - Vector2(0, 0.5)
	_mantle_dur = dur
	mantle_t = dur
	jumping = false
	_air_top = minf(_air_top, to.y)


func _try_step_up(dir: float) -> void:
	## v34: yerde 1 karoluk basamağa doğru yürürken zıplamadan kendiliğinden çık (kısa kayma)
	if not is_on_floor() or mantle_t > 0.0 or roll_t > 0.0 or crouched or not atk.is_empty() or aim_t >= 0.0 \
			or block_t >= 0.0 or hurt_t > 0.0 or fall_stun_t > 0.0 or dir == 0 or int(signf(dir)) != facing:
		return
	var to := _ledge(facing, STEP_UP)
	if to == Vector2.INF or global_position.y - to.y < 6.0:
		return
	_begin_mantle(to, 0.075)
	hero_stats["step"] = int(hero_stats["step"]) + 1
	vis_scale = Vector2(0.92, 1.08)
	Ses.play("adim_tas", -14.0, 1.1, 0.06)


func _try_mantle(dir: float) -> void:
	## Kenara tutunma (v34: Dead Cells gibi kendiliğinden): havada kenara doğru basılıyken / ilerlerken ayağın en çok
	## LEDGE_UP px üstündeki kenara eller yetişiyorsa hızlı tırmanış (yükselirken de; süre yüksekliğe göre 0,07-0,15 sn)
	if is_on_floor() or mantle_t > 0.0 or roll_t > 0.0 or not atk.is_empty() or aim_t >= 0.0 or level == null or hero_t >= 0.0:
		return
	var toward := (dir != 0 and int(signf(dir)) == facing) or velocity.x * facing > 40.0
	if not toward or velocity.y < -260.0 or crouched:
		return
	var to := _ledge(facing, LEDGE_UP)
	if to == Vector2.INF:
		return
	var h := global_position.y - to.y
	if h < 0.0:
		return
	_begin_mantle(to, 0.07 + 0.08 * clampf(h / LEDGE_UP, 0.0, 1.0))
	hero_stats["mantle"] = int(hero_stats["mantle"]) + 1
	Ses.play("zipla", -12.0, 0.8)


func _hazard_check(delta: float) -> void:
	## v25 tehlike çukuru (Dead Cells gibi): diken / zehir / lava değince TEK vuruş, geldiğin yana (son güvenli zemine
	## doğru) yukarı sektirilirsin ve 0,6 sn çukur yeniden vurmaz (eskiden içindeyken 0,7 sn'de bir vuruyordu).
	## 1,6 sn içinde yine düşersen (geniş çukur, geri sekme) hasarsız olarak son güvenli zemine ışınlanırsın.
	_haz_t -= delta
	if level == null or not level.has_method("hazard_at") or dead:
		return
	var hz: String = level.hazard_at(global_position + Vector2(0, -4))
	if hz == "":
		hz = level.hazard_at(global_position + Vector2(0, 2))
	if hz == "" or hz == "buz":
		if is_on_floor() and level.has_method("safe_ground") and level.safe_ground(global_position):
			_haz_safe = global_position
		return
	if _haz_t > 0.0 or roll_t > 0.0:
		return
	_haz_t = 0.6
	var now := Game.clock()
	var again := now - _haz_last < 1.6 and _haz_safe != Vector2.INF
	_haz_last = now
	if level.has_method("hazard_jab"):
		level.hazard_jab(global_position, hz)
	if again:
		_haz_return()
		return
	var frac := 0.14 if hz == "lav" else (0.08 if hz == "diken" else 0.06)
	if take_hit(max_hp() * frac, null, null, true):
		_haz_bounce()
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


func _haz_bounce() -> void:
	## v25: çukurdan yukarı ve son güvenli zemine (geldiğin yana) doğru sektir; iniş noktası çukurun dışına hesaplanır
	var side := float(-facing)
	if _haz_safe != Vector2.INF and absf(_haz_safe.x - global_position.x) > 2.0:
		side = signf(_haz_safe.x - global_position.x)
	var out: Vector2 = level.pit_exit(global_position, int(side)) if level.has_method("pit_exit") else Vector2.INF
	var vx := side * 170.0
	if out != Vector2.INF:
		var dx: float = out.x - global_position.x
		vx = signf(dx) * clampf(absf(dx) / 0.78 + 20.0, 110.0, 280.0)
	velocity = Vector2(vx, -470.0)
	hurt_t = maxf(hurt_t, 0.42)   # sektirme sırasında yön tuşu hızı ezmez
	inv_t = maxf(inv_t, 0.8)
	jumping = false
	vis_scale = Vector2(0.8, 1.2)


func _haz_return() -> void:
	## v25: çukura üst üste düşen (ya da geniş çukurda kalan) oyuncu hasarsız son güvenli zemine döner
	FX.anim("smoke_puff", center(), 0.0, 1.0, Color(0.85, 0.8, 0.75), false)
	FX.ghost(anim.base, Color(1.0, 0.9, 0.8, 0.4), 0.25)
	global_position = _haz_safe + Vector2(0, -1)
	velocity = Vector2.ZERO
	_air_top = global_position.y
	_fall_peak = 0.0
	hurt_t = maxf(hurt_t, 0.2)
	inv_t = maxf(inv_t, 0.9)
	_haz_t = 0.9
	FX.anim("smoke_puff", center(), 0.0, 1.0, Color(0.85, 0.8, 0.75), false)
	FX.text(center() + Vector2(0, -40), "güvenli zemine", Color(0.9, 0.85, 0.75), 7)
	if Game.camera and Game.camera.has_method("reset_smoothing"):
		Game.camera.reset_smoothing()
	Ses.play("zipla", -8.0, 0.7)


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
	_v12_tick(delta)
	_hiz_tick(delta)   # v20 saldırı hızı / Kızışma
	_gt += delta
	if grabbed_by != null:
		if not is_instance_valid(grabbed_by) or grabbed_by.dead:
			release_grab(Vector2(-facing * 120.0, -120.0))
		else:
			# yakalandın: tuşlara basarak kurtul (4 basış)
			velocity = Vector2.ZERO
			_cancel_attack(false)
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
	if don_on:
		don.process(delta)
		return
	if combo_n > 0:
		combo_t -= delta
		if combo_t <= 0.0:
			combo_break("")
	if mantle_t > 0.0:
		# kenara tutunup çık: kısa, kavisli kayma (önce yukarı, sonra öne)
		mantle_t -= delta
		if Input.is_action_just_pressed("zipla"):
			jump_buf = float(FLOW["buf_jump"])   # v34: tırmanırken basılan zıplama biter bitmez çıkar
		var k := 1.0 - clampf(mantle_t / maxf(0.01, _mantle_dur), 0.0, 1.0)
		var up := clampf(k * 1.6, 0.0, 1.0)
		var fw := clampf((k - 0.35) / 0.65, 0.0, 1.0)
		global_position = Vector2(lerpf(_mantle_a.x, _mantle_b.x, fw), lerpf(_mantle_a.y, _mantle_b.y, up))
		velocity = Vector2.ZERO
		if _mantle_dur > 0.08:
			anim.show_frame("land", 0 if k < 0.6 else 1)
			vis_scale = Vector2(0.9, 1.1).lerp(Vector2.ONE, k)
		else:
			anim.play("run")   # basamak: koşu adımı sürer
		anim.set_facing(facing)
		_update_weapon_visual()
		_feel(delta, 0.0)
		if mantle_t <= 0.0:
			vis_scale = Vector2(1.15, 0.88) if _mantle_dur > 0.08 else Vector2(1.06, 0.95)
			FX.dust(global_position, Vector2(-facing, -0.5), 3 if _mantle_dur > 0.08 else 1, 0.24)
			# v34: koşu sürer (tırmanış akışı kesmez); yön tuşu basılı değilse durur
			var d0 := Input.get_axis("sol", "sag")
			velocity.x = facing * RUN * 0.85 if d0 != 0.0 and int(signf(d0)) == facing else 0.0
			coyote = float(FLOW["coyote"])
			_air_top = global_position.y
		return
	air_hang -= delta
	for k in cd.keys():
		cd[k] = maxf(0.0, cd[k] - delta)
	bow_rel_t -= delta
	okc.process(delta)
	coyote -= delta
	jump_buf -= delta
	roll_cd -= delta
	perfect_t -= delta
	perfect_cd -= delta
	inv_t -= delta
	hurt_t -= delta
	drop_t -= delta
	land_t -= delta
	combo_window -= delta
	# v17: savuruş sürerken (hazırlık / vuruş / şarj) saldırı basışı erimez; toparlanmada sıradaki adım kesin çıkar
	if (atk.is_empty() or atk["phase"] == "rec") and roll_t <= 0.0:
		melee_buf -= delta
	roll_buf -= delta
	sec_buf -= delta
	momentum_t -= delta
	rolled_t -= delta
	riposte_t -= delta
	if momentum_t <= 0.0:
		momentum = 0
	if spirit_t > 0.0:
		spirit_t -= delta
		if Engine.get_physics_frames() % 4 == 0:
			FX.burst(center() + Vector2(randf_range(-8, 8), randf_range(-14, 14)), Color(0.55, 0.95, 1.0), 1, 30, 0.6, 0.18, -60, true)
		if Engine.get_physics_frames() % 3 == 0 and absf(velocity.x) > 40.0:
			# kurt biçiminde görünen gövde kurt: insan gövdesinin hayaleti çizilmesin
			FX.ghost(wolf_anim.base if wolf_t > 0.0 else anim.base, Color(0.45, 0.9, 1.0, 0.25), 0.2)
	set_collision_mask_value(4, drop_t <= DROP_MASK)
	# v27 savaş sanatı (T / LT): süren sanat hareketi ve saldırıyı kendisi yönetir
	if sanat.tick(delta):
		return

	var dir := Input.get_axis("sol", "sag")
	_resolve_roles()
	if Input.is_action_just_pressed("zipla"):
		jump_buf = float(FLOW["buf_jump"])
	# v34 Kahraman İnişi (dalış) ve iniş pozu / yüksek düşüş sersemlemesi kendi akışlarını yönetir
	if hero_t >= 0.0:
		_hero_tick(delta, dir)
		return
	if (fall_stun_t > 0.0 or hero_pose_t > 0.0) and _land_hold(delta, dir):
		return
	# ağır saldırı tanıma: tuşun basılı kaldığı süre (basış anından)
	if mel_act != "" and Input.is_action_pressed(mel_act):
		_mel_down_t = 0.0 if Input.is_action_just_pressed(mel_act) or _mel_down_t < 0.0 else _mel_down_t + delta
	else:
		_mel_down_t = -1.0
		_heavy_armed = false
	if not is_on_floor():
		_fall_peak = maxf(_fall_peak, velocity.y)
		_air_top = minf(_air_top, global_position.y)
	if is_on_floor():
		coyote = float(FLOW["coyote"])
		air_jumps = 2 if Game.has_lutuf("umay") else 1
		jumping = false
		if not _was_floor:
			_on_land()
		_air_top = global_position.y
	_was_floor = is_on_floor()
	if fall_stun_t > 0.0 and _land_hold(delta, dir):
		return   # v34: inişte yüksek düşüş sersemlemesi başladı

	# yuvarlanma (alçak geçitlerde kendiliğinden sürer); Shift basılı tutulursa yuvarlanma biter bitmez koşuya geçer
	# v17: yuvarlanma basışı ara belleğe alınır (yuvarlanma / bekleme sürerken basılırsa biter bitmez yuvarlanır)
	if Input.is_action_just_pressed("yuvarlan"):
		roll_buf = float(FLOW["buf_roll"])
	if sec_act != "" and Input.is_action_just_pressed(sec_act):
		sec_buf = float(FLOW["buf_sec"])
	if roll_buf > 0.0 and roll_cd <= 0.0 and roll_t <= 0.0 and drink_t <= 0.0:
		roll_buf = 0.0
		_start_roll(dir)
	# v17 kaçış saldırısı: yuvarlanırken saldırı basışı saklanır; yuvarlanmanın son kısmında yuvarlanmayı keser,
	# saldırı aynı karede çıkar (yuvarlanma sonrası penceredeyse Dönüş Kesiği)
	if roll_t > 0.0 and mel_act != "":
		if Input.is_action_just_pressed(mel_act):
			_melee_press()
		if melee_buf > 0.0 and roll_t <= ROLL_T * (1.0 - float(FLOW["roll_atk_k"])) and drink_t <= 0.0 and not _head_blocked():
			roll_t = 0.0
			_set_crouch(false)
			inv_t = maxf(inv_t, float(FLOW["roll_atk_inv"]))
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
			if is_on_floor() and Input.is_action_pressed("asagi"):
				# v33: yuvarlanırken aşağı + zıpla da tek yönlü platformdan / kuyu kapağından iner (zıplamaz)
				drop_t = 0.25
				jump_buf = 0.0
				position.y += 2
			else:
				_jump(false)
		okc.roll_tick()  # v19: Akıncı Yayı yuvarlanırken atar; diğer yaylarda basış yuvarlanma bitince çıkar
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
		elif roll_t <= 0.0:
			_melee_press()
	if charge_t >= 0.0:
		charge_t += delta
		if mel_act != "" and Input.is_action_pressed(mel_act) and charge_t < 1.2:
			if charge_t > 0.2 and charge_fx == null:
				charge_fx = FX.anim("focus_charge", center(), 0.0, 0.7, Color(0.6, 0.85, 1.0), true, false, self)
				if charge_fx:
					charge_fx.loop = true
				FX.text(center() + Vector2(0, -34), "", Color.WHITE, 7)
			if charge_t > 0.2:
				anim.show_frame("atk_lunge", 2 if anim.frame_count("atk_lunge") > 8 else 1)
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
				melee_buf = float(FLOW["buf_melee"])
			else:
				_lightning_dash(mel, held)
	var busy: bool = not atk.is_empty() and atk["phase"] != "rec"
	if atk.is_empty():
		since_atk += delta
	# v19: gerilirken saldırı basışı kaybolmaz; v22: gerilme bırakılır (ok kendiliğinden çıkmaz), saldırı aynı karede başlar
	if melee_buf > 0.0 and aim_t >= 0.0 and drink_t <= 0.0:
		okc.melee_interrupt()
	if melee_buf > 0.0 and drink_t <= 0.0 and aim_t < 0.0 and block_t < 0.0:
		if atk.is_empty():
			if since_atk < CHAIN_WINDOW and last_step >= 0:
				_start_attack(last_step + 1)
			else:
				_start_attack(0)
		elif atk["phase"] == "rec":
			# toparlanmadan sıradaki adım; bekleme bitirişinin toparlanması yeni zincir açar
			_start_attack(0 if atk.get("pause", false) else int(atk["step"]) + 1)
	# v17 hafif silahta ağır saldırı: hafif vuruş beklemeden çıktı; tuş FLOW.heavy_hold boyunca basılı kaldıysa
	# toparlanmadan (ya da savuruş bitmişse hemen) şarja geç
	if _heavy_armed and _mel_down_t >= float(FLOW["heavy_hold"]) and drink_t <= 0.0 and aim_t < 0.0 and block_t < 0.0 \
			and (atk.is_empty() or (atk["phase"] == "rec" and _can_hold_heavy(atk["c"]))):
		_heavy_armed = false
		_cancel_attack()
		_begin_heavy(slot(mel_slot))
	if regen_t > 0.0:
		regen_t -= delta
		if Engine.get_physics_frames() % 30 == 0:
			heal(max_hp() * 0.015)
			FX.burst(center() + Vector2(randf_range(-8, 8), randf_range(-10, 10)), Color(0.5, 1.0, 0.7), 1, 20, 0.5, 0.14, -50, true)

	var sec := slot(sec_slot)
	var sec_kind: String = sec.get("kind", "")
	# v17: ikincil (yay / fırlatma / büyü / kalkan) basışı saldırı toparlanmasını keser; ara bellekten çıkar
	if sec_buf > 0.0 and sec_kind != "" and not atk.is_empty() and (atk["phase"] == "rec" or _hit_cancel_ok()) and melee_buf <= 0.0:
		_cancel_attack()
	var sec_press := sec_buf > 0.0 and sec_act != ""
	if atk.is_empty() and drink_t <= 0.0:
		if Silah27.owns_sec(sec):
			Silah27.sec_tick(self, sec, sec_press, delta)   # v27: Tatar Yayı, Kam Küzgüsü, Tengri Bağı
		elif sec_kind == "bow":
			okc.tick(delta, sec, sec_press)  # v19 Okçuluk: dokunuş / basılı tut / tam bırakış / süzülüş
		elif sec_kind == "throw":
			if sec_press and cd[sec_slot] <= 0.0 and throw_t < 0.0:
				sec_buf = 0.0
				throw_t = 0.0
				thrown = false
		elif sec_kind == "magic":
			if sec_press and cd[sec_slot] <= 0.0:
				sec_buf = 0.0
				_cast_magic(sec)
		elif sec_kind == "shield":
			if sec_press and block_t < 0.0:
				sec_buf = 0.0
				block_t = 0.0
				vis_scale = Vector2(1.1, 0.92)
			if block_t >= 0.0:
				block_t += delta
				if not Input.is_action_pressed(sec_act):
					block_t = -1.0
	if throw_t >= 0.0:
		throw_t += delta
		var tf := int(throw_t / 0.07)
		var tf28 := _ts_frame("throw", throw_t / 0.28)
		anim.show_frame("throw", tf28 if tf28 >= 0 else mini(tf, 2))
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
	# v17 saldırırken hareket: yerde hız birden sıfırlanmaz (koşu ivmesi savuruşa taşınır, sürtünmeyle söner);
	# havada yön tuşu kısmen dinlenir. Kendi hareketi olan savuruşlar (geri sıçrayış, delip geçme, hamle) eski yolda.
	var atk_move := ""
	if busy:
		target = 0.0
		# (atk bu karede şişe / Kut gücü / teçhizatla boşalmış olabilir)
		if not atk.is_empty() and not _atk_owns_motion():
			if is_on_floor():
				atk_move = "ground"
			else:
				atk_move = "air"
				target = dir * spd * float(FLOW["air_ctrl"])
	elif not atk.is_empty():
		target *= 0.45
	if crouch_hold:
		target *= 0.35
	if aim_t >= 0.0 or block_t >= 0.0:
		target *= okc.move_k() if aim_t >= 0.0 else 0.3  # v19: gerilirken yaya göre %40-85 hız
		if block_t >= 0.0 and sec.get("mech_id", "") == "agir_blok":
			target *= 1.0 - float(sec.get("mech_v", 40.0)) / 100.0
	if charge_t > 0.2:
		target *= 0.25
	target *= Silah27.move_k(self)   # v27: Küzgü ışını tutulurken yavaş
	if drink_t > 0.0:
		target *= 0.3
	if land_t > 0.0:
		target *= 0.5
	var acc := ACC_GROUND if is_on_floor() else ACC_AIR
	if is_on_floor() and (dir == 0 or signf(dir) != signf(velocity.x)):
		acc = DEC_GROUND
	elif not is_on_floor() and dir != 0 and signf(dir) != signf(velocity.x) and absf(velocity.x) > 10.0:
		acc *= TURN_AIR   # v34: havada keskin dönüş
	if sprint and dir != 0:
		acc = 1300.0  # koşuya yumuşak geçiş
	on_ice = is_on_floor() and level != null and level.has_method("ice_at") and level.ice_at(global_position + Vector2(0, 3))
	if on_ice:
		acc *= 0.22
	if hurt_t <= 0.0:
		if atk_move == "ground":
			velocity.x = move_toward(velocity.x, 0.0, _atk_fric(atk["item"]) * (0.22 if on_ice else 1.0) * delta)
		elif atk_move == "air":
			velocity.x = move_toward(velocity.x, target, float(FLOW["air_acc"]) * delta)
		else:
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

	# zıplama — v17: saldırı sürerken zıplama hazırlığı (ağırlığa göre) ya da toparlanmayı keser; vuruş anında
	# basılırsa ara bellekte bekler, toparlanmada çıkar
	if jump_buf > 0.0 and not atk.is_empty():
		if _jump_cancels():
			_cancel_attack()
		else:
			jump_buf += delta
	if jump_buf > 0.0 and atk.is_empty():
		if is_on_floor() and Input.is_action_pressed("asagi"):
			# v33: yerde aşağı + zıpla = tek yönlü platformdan / kapaktan in
			drop_t = 0.25
			jump_buf = 0.0
			position.y += 2
		elif not is_on_floor() and Input.is_action_pressed("asagi") and drop_t <= 0.0:
			_hero_begin()   # v34: havada aşağı + zıpla = Kahraman İnişi (indiğin platformun hemen altında değil)
			return
		elif coyote > 0.0:
			_jump(false)
		elif air_jumps > 0:
			air_jumps -= 1
			_jump(true)
	# v34 değişken yükseklik: yükselirken tuş bırakılırsa hız JUMP_CUT oranına iner (eski 0,55)
	if jumping and velocity.y < -140.0 and not Input.is_action_pressed("zipla"):
		velocity.y *= JUMP_CUT
		jumping = false

	var gmul := 1.0
	# v34: yükselişte GRAV_RISE, düşüşte GRAV_FALL (eski: her iki yönde GRAV 1180)
	var g_air := GRAV_RISE if velocity.y < 0.0 else GRAV_FALL
	if air_hang > 0.0 and not is_on_floor() and not atk.get("c", {}).get("plunge", false):
		gmul = 0.08
		g_air = GRAV
		velocity.y = minf(velocity.y, 30.0)
	elif not atk.is_empty() and atk["phase"] != "rec" and not is_on_floor():
		gmul = 0.4
		g_air = GRAV
	elif not is_on_floor() and absf(velocity.y) < float(APEX["vy"]) and jumping:
		gmul = float(APEX["g"])  # tepe noktasında kısa asılı kalış
		g_air = GRAV_RISE
	velocity.y = minf(velocity.y + g_air * gmul * delta, MAX_FALL)

	if drink_t > 0.0:
		drink_t -= delta
	if cast_t > 0.0:
		cast_t -= delta
	# toparlanma iptali: vuruş bitti, oyuncu yürür / zıplar / yuvarlanırsa savuruşun kuyruğunu bekletme
	if not atk.is_empty() and atk["phase"] == "rec" and not atk.get("heavy", false) and (dir != 0 or jump_buf > 0.0):
		_cancel_attack()
	# v17 iniş iptali: havada başlayan savuruş toparlanırken yere inersen kuyruk beklemez
	if not atk.is_empty() and atk.get("air", false) and atk["phase"] == "rec" and is_on_floor():
		_cancel_attack()
	if not atk.is_empty():
		_update_attack(delta)

	_prev_vy = velocity.y
	move_and_slide()
	_corner_correct()
	_try_mantle(dir)
	_try_step_up(dir)
	_hazard_check(delta)
	_update_anim(dir)
	_update_weapon_visual()
	_feel(delta, dir)
	_look_ahead(delta)
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
		_air_top = last_safe.y
		_fall_peak = 0.0
		hero_t = -1.0
		_still_t = 0.0
		FX.dust(global_position, Vector2.UP, 6, 0.3)
		Game.shake(2.0)


func _feel(delta: float, _dir: float) -> void:
	## Squash & stretch ve eğilme: ölçek hedefe yaylanır, gövde hız yönünde yatar.
	# v11: kritik altı sönümlü yay — vurgu anında ezilir/uzar, bir kez hafifçe aşıp oturur (kukla gibi kesik değil)
	_vs_v += ((SanatAnim.scale_target(self) - vis_scale) * 360.0 - _vs_v * 19.0) * delta   # v27: hedef saldırıda evreye göre
	vis_scale += _vs_v * delta
	var fl := is_on_floor()
	var sy := 1.0
	if fl and absf(velocity.x) < 15.0 and atk.is_empty():
		sy += 0.016 * sin(Time.get_ticks_msec() * 0.0028)  # nefes
	elif not fl:
		sy += clampf(absf(velocity.y) / 3000.0, 0.0, 0.1)  # havada hızla uzama
	anim.scale = vis_scale * Vector2(1.0 / sqrt(sy), sy)
	if facing != _feel_face:
		_feel_face = facing
		if fl and absf(velocity.x) > 40.0:
			vis_scale *= Vector2(0.84, 1.05)  # dönüşte gövde toplanır
			FX.dust(global_position + Vector2(facing * 6, 0), Vector2(facing, -0.4), 2, 0.22)
	if fl and not _feel_floor and _feel_vy > 520.0:
		FX.dust(global_position + Vector2(-8, 0), Vector2(-1, -0.3), 2, 0.26)
		FX.dust(global_position + Vector2(8, 0), Vector2(1, -0.3), 2, 0.26)
	_feel_floor = fl
	_feel_vy = velocity.y
	var lean_target := 0.0
	if atk.is_empty() and roll_t <= 0.0 and hurt_t <= 0.0:
		lean_target = clampf(velocity.x / RUN, -1.3, 1.3) * (0.1 if fl else 0.06)
		# ivmelenme: hız değişirken biraz daha yatar (kalkışta öne, frende geriye)
		lean_target += clampf((velocity.x - _feel_vx) * 0.0016, -0.06, 0.06)
	elif not atk.is_empty() and roll_t <= 0.0 and hurt_t <= 0.0 and atk.get("phase", "") != "charge":
		# v18 savuruşta gövde: hazırlıkta geriye toplanır, vuruşta öne yüklenir (ağır silahta daha çok), toparlanmada oturur
		var aw := _weight(atk["item"])
		match String(atk.get("phase", "")):
			"wind":
				lean_target = -float(facing) * (0.05 + 0.05 * aw)
			"act":
				lean_target = float(facing) * (0.09 + 0.07 * aw)
			_:
				lean_target = float(facing) * 0.025
	lean_target = SanatAnim.lean(self, lean_target)   # v27: aileye göre evre eğrisi; yay / fırlatma / büyü gövdesi
	SanatAnim.skew(self, delta)                        # v27: üst gövde eğikliği (ayaklar yerde)
	_feel_vx = velocity.x
	_lean_v += ((lean_target - vis_lean) * 260.0 - _lean_v * 22.0) * delta
	vis_lean += _lean_v * delta
	anim.rotation = vis_lean


func _look_ahead(delta: float) -> void:
	## Kamera ileri bakış: baktığın yöne doğru 28 px kayar (kare hızından bağımsız üstel yumuşatma);
	## saldırıda sabit kalır ki vuruş anında kamera kaymasın.
	var cam: Camera2D = Game.camera
	if cam == null or cam.get_parent() != self:
		return
	var tx := float(facing) * 28.0 + clampf(velocity.x, -RUN, RUN) * 0.06
	if not atk.is_empty():
		tx = cam.position.x
	cam.position.x = lerpf(cam.position.x, tx, 1.0 - exp(-3.2 * delta))


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
	last_fall_h = global_position.y - _air_top
	# v34: çok yüksekten normal düşüş (Kahraman İnişi yapmadan) kısa sersemletir; daha da yüksekte az hasar
	if last_fall_h > float(HERO["stun_h"]) and f >= MAX_FALL - 1.0 and atk.is_empty() and roll_t <= 0.0 and not dead:
		var big := last_fall_h > float(HERO["dmg_h"])
		fall_stun_t = float(HERO["dmg_stun_t"] if big else HERO["stun_t"])
		hero_stats["stun"] = int(hero_stats["stun"]) + 1
		velocity.x = 0.0
		vis_scale = Vector2(1.35, 0.68)
		FX.dust(global_position, Vector2.UP, 8, 0.32)
		FX.anim("landing_dust", global_position, 0.0, 1.0, Color(0.85, 0.8, 0.8, 0.8), false)
		InkDust.burst(global_position, facing, 0.6)
		Ses.play("inis_2", -2.0, 0.85)
		Game.shake(3.0)
		Game.kick(Vector2.DOWN, 4.0)
		if big:
			var dmg := maxf(1.0, max_hp() * float(HERO["dmg_k"]))
			Game.run["hp"] = maxf(1.0, float(Game.run["hp"]) - dmg)   # düşüş öldürmez (lanet darbeyi sayar, düşüşü değil)
			FX.number(center(), dmg, false, Color(1.0, 0.6, 0.5))
		FX.text(center() + Vector2(0, -40), "sersemledin", Color(0.95, 0.85, 0.7), 8)
		return
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


# ------------------------------------------------------------------ v34 Kahraman İnişi
func _hero_begin() -> void:
	## Havada S + Boşluk: kısa toplanma (HERO.antic), sonra hızla çakılış; zıplama tamponu ve süren saldırı biter
	_cancel_attack()
	hero_t = 0.0
	jump_buf = 0.0
	jumping = false
	coyote = 0.0
	air_hang = 0.0
	vis_scale = Vector2(1.18, 0.86)
	hero_stats["n"] = int(hero_stats["n"]) + 1
	FX.ring(center(), 14.0, Color(0.2, 0.16, 0.26, 0.8), 0.18)
	Ses.play("yuvarlan", -8.0, 0.7)


func _hero_tick(delta: float, dir: float) -> void:
	hero_t += delta   # (sayaçlar ana döngüde azaldı)
	_air_top = minf(_air_top, global_position.y)
	anim.set_facing(facing)
	if hero_t < float(HERO["antic"]):
		# toplanma: havada bir an durur, diz karna çekilir
		velocity = Vector2(velocity.x * 0.85, -25.0)
		anim.show_frame("roll", 1)
	else:
		velocity.y = minf(maxf(velocity.y, float(HERO["v"])) + float(HERO["acc"]) * delta, float(HERO["v_max"]))
		velocity.x = move_toward(velocity.x, dir * RUN * float(HERO["steer"]), 1400.0 * delta)
		anim.show_frame("fall", 2 if anim.frame_count("fall") > 2 else 0)
		vis_scale = vis_scale.lerp(Vector2(0.82, 1.24), 0.35)
		# mürekkep izi: koyu, kısa ömürlü gövde kopyaları + seyrek damlalar
		if Engine.get_physics_frames() % 2 == 0:
			FX.ghost(anim.base, Color(0.16, 0.12, 0.22, 0.55), 0.2)
		if Engine.get_physics_frames() % 5 == 0:
			FX.dust(center() + Vector2(randf_range(-4, 4), -10), Vector2(0, -1), 1, 0.2, Color(0.12, 0.1, 0.16, 0.6))
	_fall_peak = maxf(_fall_peak, velocity.y)
	hero_stats["vy"] = maxf(float(hero_stats["vy"]), velocity.y)
	move_and_slide()
	_update_weapon_visual()
	_feel(delta, 0.0)
	_look_ahead(delta)
	_safety(delta)
	if is_on_floor() and hero_t >= float(HERO["antic"]):
		_hero_land()
	_was_floor = is_on_floor()


func _hero_land() -> void:
	## Yere değiş: şok dalgası (yükseklikle büyür, düşmanları sersemletip iter), toz / mürekkep sıçrantısı, sarsıntı;
	## düşüş sersemlemesi ve hasarı yok. Diz yerde, yumruk toprakta kısa poz; herhangi bir girdi pozu keser.
	var h := maxf(0.0, global_position.y - _air_top)
	last_fall_h = h
	hero_stats["h"] = h
	hero_t = -1.0
	_fall_peak = 0.0
	_air_top = global_position.y
	hero_pose_t = float(HERO["pose"])
	fall_stun_t = 0.0
	land_t = 0.0
	velocity = Vector2.ZERO
	var k := clampf(h / 240.0, 0.35, 1.6)
	var r := float(HERO["r"]) + float(HERO["r_k"]) * k
	inv_t = maxf(inv_t, 0.2)
	vis_scale = Vector2(1.42, 0.62)
	Game.shake(2.5 + 3.5 * k)
	Game.kick(Vector2.DOWN, 4.0 + 3.0 * k)
	Game.hitstop(0.04 + 0.03 * k)
	Game.rumble(0.3, 0.6 * minf(1.0, k), 0.14)
	FX.ground_slam(global_position, facing, 0.45 + 0.35 * k, Color(0.3, 0.24, 0.6), false)   # mor-lacivert mürekkep (kan değil)
	FX.shockwave(global_position + Vector2(0, -6), r * 1.2, 0.6 + 0.3 * k)
	FX.ring(global_position + Vector2(0, -3), r, Color(0.2, 0.16, 0.26, 0.75), 0.32, 0.3)
	FX.shock_line(global_position, r * 0.85, Color(0.18, 0.14, 0.22, 0.7))
	FX.dust(global_position + Vector2(-6, 0), Vector2(-1, -0.25), 5, 0.34)
	FX.dust(global_position + Vector2(6, 0), Vector2(1, -0.25), 5, 0.34)
	InkDust.burst(global_position, facing, 0.8 + 0.4 * k)
	Ses.play("inis_2", -2.0, 0.9)
	Ses.play("darbe_cekic", -6.0 + 3.0 * minf(1.0, k), 0.95)
	if k > 0.8:
		Ses.play("sarsinti", -8.0)
	var it := slot(mel_slot)
	var melee_ok: bool = not it.is_empty() and String(it.get("kind", "")) in ItemGen.MELEE_KINDS
	var n := 0
	for e in get_tree().get_nodes_in_group("dusman"):
		if not is_instance_valid(e) or e.dead:
			continue
		var dx: float = e.global_position.x - global_position.x
		if absf(dx) > r or absf(e.global_position.y - global_position.y) > 44.0:
			continue
		var sd := signf(dx) if absf(dx) > 1.0 else float(facing)
		var fall_k := 1.0 - 0.4 * clampf(absf(dx) / r, 0.0, 1.0)   # merkezde tam, kenarda %60
		var opts := {"kb": 150.0 + 90.0 * k, "dir": sd, "launch": 160.0 + 100.0 * k, "stun": 0.45 + 0.35 * k, "sfx_done": true}
		if melee_ok:
			_deal(e, float(it["dmg"]) * (0.55 + 0.45 * k) * fall_k, it, opts)
		else:
			e.take_hit((6.0 + 6.0 * k) * fall_k, opts)
		if is_instance_valid(e) and not e.dead and e.has_method("stun"):
			e.stun(float(opts["stun"]))
		combo_add(e)
		n += 1
	hero_stats["hits"] = int(hero_stats["hits"]) + n
	# v34 birleştirme: şok dalgası küpleri kırar, yanındaki çatlak duvara bir vuruş sayılır (Level.break_cracks:
	# silah savuruşu ve patlama ile aynı yol; duvar yine iki vuruşta açılır)
	if level and level.has_method("break_cracks"):
		level.break_cracks(Rect2(global_position.x - r, global_position.y - 44.0, r * 2.0, 48.0))


func _land_hold(delta: float, dir: float) -> bool:
	## İniş pozu (Kahraman İnişi) ve yüksek düşüş sersemlemesi: yerde kıpırdamadan bekler. Poz 0,1 sn'den sonra
	## herhangi bir girdiyle kesilir (yürü / zıpla / saldır / yuvarlan); sersemleme kesilmez. true: bu kare bitti.
	if fall_stun_t > 0.0:
		fall_stun_t -= delta
		velocity.x = move_toward(velocity.x, 0.0, 2400.0 * delta)
		velocity.y = minf(velocity.y + GRAV_FALL * delta, MAX_FALL)
		move_and_slide()
		anim.set_facing(facing)
		anim.show_frame("land", 1)
		vis_scale = vis_scale.lerp(Vector2(1.12, 0.86), 0.2)
		if Engine.get_physics_frames() % 9 == 0:
			FX.burst(center() + Vector2(0, -22), Color(1.0, 0.92, 0.6), 2, 40, 0.4, 0.14, -20, true)   # baş üstünde yıldızlar
		_update_weapon_visual()
		_feel(delta, 0.0)
		_safety(delta)
		return true
	var since := float(HERO["pose"]) - hero_pose_t
	var want := dir != 0.0 or jump_buf > 0.0 or roll_buf > 0.0 or Input.is_action_just_pressed("yuvarlan") \
		or (mel_act != "" and Input.is_action_pressed(mel_act)) or (sec_act != "" and Input.is_action_just_pressed(sec_act))
	hero_pose_t -= delta
	if hero_pose_t <= 0.0 or (since >= 0.1 and want) or not is_on_floor() or hurt_t > 0.0:
		hero_pose_t = 0.0
		vis_scale = Vector2(0.9, 1.1)   # kalkış: gövde açılır
		return false
	velocity.x = 0.0
	velocity.y = minf(velocity.y + GRAV_FALL * delta, MAX_FALL)
	move_and_slide()
	anim.set_facing(facing)
	# poz: tek diz yerde (çömelik saldırı gövdesi, ön kol iskeletle yumruk toprağa); silahsızken derin iniş karesi
	var armed := not slot(mel_slot).is_empty() and anim.frame_count("crouch_atk") > 0
	anim.show_frame("crouch_atk" if armed else "land", 0)
	# ilk anda en derin çöküş, sonra yavaşça doğrulur
	var q := clampf(since / float(HERO["pose"]), 0.0, 1.0)
	vis_scale = Vector2(1.12, 0.86).lerp(Vector2(1.04, 0.96), q * q)
	vis_lean = float(facing) * 0.08 * (1.0 - q)
	_update_weapon_visual()
	_feel(delta, 0.0)
	return true


func _perfect_dodge(from: Node) -> void:
	## Kusursuz Kaçış: son anda kaçış — 0,45 sn ağır çekim ("cadı zamanı"), dokunulmazlık uzar, Kut +8,
	## 1,5 sn içindeki ilk yakın vuruş kesin kritik. Düşmanın saldırısı boşa gider; oyuncu cezalandırmaya davet edilir.
	_pd_done = true
	perfect_cd = 1.6
	perfect_t = 1.5
	inv_t = maxf(inv_t, 0.55)
	add_kut(8.0)
	Game.slowmo(0.22, 0.45)
	Game.zoom_punch(0.04)
	Game.rumble(0.2, 0.5, 0.12)
	FX.text(center() + Vector2(0, -44), "KUSURSUZ KAÇIŞ", Color(0.75, 0.95, 1.0), 9)
	FX.ring(center(), 36, Color(0.7, 0.95, 1.0), 0.3)
	FX.flash_light(center(), Color(0.7, 0.95, 1.0), 140.0, 1.4, 0.25)
	InkFX.flourish(center(), "dodge", 2)
	for i in 4:
		FX.ghost(anim.base, Color(0.65, 0.92, 1.0, 0.45), 0.35)
	if from and is_instance_valid(from) and "center" in from:
		FX.streak(from.center(), center(), Color(0.75, 0.95, 1.0, 0.8), 0.14)
	Ses.play("don_al" if Ses.has("don_al") else "sarj_dolu", -6.0, 1.25)


func _start_roll(dir: float) -> void:
	if dir != 0:
		facing = int(signf(dir))
	_cancel_attack()
	melee_buf = 0.0  # yuvarlanmadan önceki saldırı basışı yuvarlanmayı kesmesin (kesen yalnızca yuvarlanırken basılan)
	aim_t = -1.0
	block_t = -1.0
	roll_t = ROLL_T
	roll_cd = ROLL_T + float(FLOW["roll_gap"])
	rolled_t = 2.0
	_pd_done = false
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


# ------------------------------------------------------------------ v17 akıcılık yardımcıları
func _melee_press() -> void:
	## v22 saldırı basışı: savuruş yokken / toparlanmada / savuruşun son anında ara belleğe girer; savuruşun erken
	## evresinde (hazırlık, süpürme) yapılan basış yok sayılır (kendiliğinden geç savuruş çıkmasın). Basışın yönü saklanır:
	## kuyruktan çıkan savuruş, oyuncunun bastığı andaki yöne vurur.
	_yk_on_press()  # v19 Kut Yankısı: basış isabetin hemen ardından mı?
	_press_gt = _gt
	_press_used = false
	_press_dir = int(signf(Input.get_axis("sol", "sag")))
	var rem := _to_chain()
	_press_hit = not atk.is_empty() and _past_contact()
	if atk.is_empty() or atk["phase"] == "rec" or rem <= float(FLOW["buf_melee_late"]) or _press_hit:
		melee_buf = float(FLOW["buf_melee"])


func _past_contact() -> bool:
	## Süren savuruş temas anını (ck: bıçağın düşmana vardığı kare) geçti mi?
	if atk.is_empty() or not atk.has("sw") or atk["phase"] == "charge":
		return false
	return float(atk["t"]) / maxf(0.0001, float(atk["dur"])) >= _contact_k(atk["sw"])


func _to_chain() -> float:
	## Süren savuruşun zincir / iptal noktasına (toparlanma başı) kalan oyun süresi (sn; tutuş / donma sayılmaz).
	## Şarj ve kendi hareketli hamlelerde (şimşek hamlesi) büyük değer: basış kuyruğa girmez.
	if atk.is_empty():
		return 0.0
	if atk["phase"] == "rec":
		return 0.0
	if atk["phase"] == "charge" or not atk.has("ph"):
		return 9.0
	var sw: Dictionary = atk["sw"]
	var ph: Array = atk["ph"]
	var k := float(atk["t"]) / maxf(0.0001, float(atk["dur"]))
	var h0 := float(sw["hit"][0])
	var ck := _contact_k(sw)
	var h1 := float(sw["hit"][1])
	if k >= h1:
		return 0.0
	if k >= ck:
		return (h1 - k) / maxf(0.0001, h1 - ck) * float(ph[2])
	if k >= h0:
		return (ck - k) / maxf(0.0001, ck - h0) * float(ph[1]) + float(ph[2])
	return (h0 - k) / maxf(0.0001, h0) * float(ph[0]) + float(ph[1]) + float(ph[2])


func _cancel_attack(keep_chain := true) -> void:
	## Süren saldırıyı temiz bırak: iz, şarj efekti / döngü sesi, gürz şarj halkası. Toparlanmadan kesilirse zincir
	## sürer (CHAIN_WINDOW içinde basınca sıradaki adım); hazırlık / vuruşta kesilirse önceki zincir durumu kalır.
	if atk.is_empty():
		return
	if atk.has("charge_fx") and is_instance_valid(atk["charge_fx"]):
		atk["charge_fx"].stop()
	if atk["phase"] == "charge" or atk.get("heavy", false):
		if _heavy_fx and is_instance_valid(_heavy_fx):
			_heavy_fx.stop()
		_heavy_fx = null
		Ses.loop_stop("sarj")
	_end_trail()
	if atk["phase"] == "rec" and keep_chain:
		var cc: Dictionary = atk["c"]
		last_step = -1 if (cc.get("last", false) or atk.get("pause", false) or atk.get("heavy", false)) else int(atk["step"])
		since_atk = 0.0
	elif not keep_chain:
		last_step = -1
	atk = {}


func _atk_owns_motion() -> bool:
	## Kendi hareketini süren savuruşlar (eski hareket yolunda kalır): geri sıçrayış, delip geçme, şimşek hamlesi,
	## sırık atlayışı, dalış, pençe sıçraması, hoplama
	if atk.is_empty():
		return false
	var c: Dictionary = atk["c"]
	return c.get("backstep", false) or atk.get("through", false) or atk.has("dash_px") or c.get("vault", false) \
		or c.get("plunge", false) or atk.get("pounce", false) or c.has("hop") or atk.has("flash_left")


func _atk_fric(it: Dictionary) -> float:
	return float(FLOW["atk_fric_heavy"]) if _weight(it) >= 0.75 else float(FLOW["atk_fric"])


func _jump_cancels() -> bool:
	## Zıplama bu karede saldırıyı kesebilir mi? Toparlanma ve şarj: evet. Hazırlık: silah ağırlığına göre ilk kısmı
	## (süper zırhlı savuruş kesilmez). Vuruş anı: hayır (zıplama ara bellekte bekler).
	var ph: String = atk["phase"]
	if ph == "rec" or ph == "charge":
		return true
	if _hit_cancel_ok():
		return true  # v19 isabet iptali: vuruş oturdu, kilidin kalanı zıplamayla kesilir (hava kombosuna geçiş)
	if ph != "wind" or (atk.get("super_armor", false) and not atk.get("sa_wind", false)) or atk.has("dash_px"):
		return false
	var w := _weight(atk["item"])
	var lims: Array = FLOW["jump_cancel_k"]
	var lim := float(lims[0] if w <= 0.3 else (lims[1] if w <= 0.65 else lims[2]))
	return float(atk["t"]) / float(atk["dur"]) < float(atk["sw"]["hit"][0]) * lim


func _foes_near(max_dx: float) -> Array:
	## Hedef yardımı için yakındaki görünür düşmanlar (dikeyde yakın)
	var out: Array = []
	for e in get_tree().get_nodes_in_group("dusman"):
		if not is_instance_valid(e) or e.dead:
			continue
		if "_hidden" in e and e._hidden:
			continue
		var r: Rect2 = e.hurt_rect()
		if absf(r.get_center().y - center().y) > float(FLOW["assist_dy"]) + r.size.y * 0.5:
			continue
		if absf(r.get_center().x - global_position.x) - r.size.x * 0.5 > max_dx:
			continue
		out.append(e)
	return out


func _strike_step(it: Dictionary, c: Dictionary, heavy_w: bool) -> float:
	## Vuruş anı öne adım hızı. Mesafe = taban + adımın dash değeri; sürtünmeyle söner. v22: adım düşmana doğru
	## uzamaz (eski "hedef yardımı" adımı 10-40 px kaydırıyordu); yalnızca dibindeki düşmanın içinden geçip arkasına
	## düşmemek için kısalır. Yön hep oyuncunun baktığı yön.
	var steps: Array = FLOW["step"]
	var D := float(steps[1] if heavy_w else steps[0]) + float(atk.get("dash", 0.0)) * float(FLOW["step_dash"])
	if _tempo_class(it) in V34_AGIR["sa_wind"]:
		D += float(V34_AGIR["step"]) - float(steps[1])   # v34: ağır savuruş gövdeyi öne taşır
	var F := _atk_fric(it)
	var closest := INF
	for e in _foes_near(D + 24.0):
		var r: Rect2 = e.hurt_rect()
		var rel := (r.get_center().x - global_position.x) * float(facing)
		if rel < -2.0:
			continue
		closest = minf(closest, rel)
	atk["step_cap"] = INF
	if closest < INF:
		D = minf(D, maxf(0.0, closest - 12.0))  # dibindekinin içinden geçme
		atk["step_cap"] = sqrt(2.0 * F * maxf(0.0, closest - 12.0))
	return sqrt(2.0 * F * D)


func _update_anim(dir: float) -> void:
	anim.set_facing(facing)
	if not atk.is_empty() or throw_t >= 0.0:
		return
	if charge_t > 0.2:
		return
	if Silah27.anim_override(self):
		return
	if hurt_t > 0.0:
		anim.play("hurt")
	elif drink_t > 0.0:
		anim.play("drink")
	elif cast_t > 0.0:
		var cf28 := _ts_frame("cast", 1.0 - cast_t / 0.35)
		anim.show_frame("cast", cf28 if cf28 >= 0 else (1 if cast_t < 0.2 else 0))
	elif aim_t >= 0.0:
		if crouch_hold and crouched:
			anim.show_frame("crouch_atk", 0)
		else:
			# v28: 0 ok takma, 1 germe, 2 tam gerili (4 kareli yay gövdesi)
			anim.show_frame("bow", (2 if aim_t > 0.3 and anim.frame_count("bow") > 3 else 1) if aim_t > 0.12 else 0)
	elif bow_rel_t > 0.0 and slot(sec_slot).get("kind", "") == "bow":
		anim.show_frame("bow", 3 if anim.frame_count("bow") > 3 else 1)   # v28: bırakış geri tepmesi
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
func _weight(it: Dictionary) -> float:
	## Silah ağırlığı 0..1: hazırlık tutuşu, kırbaç gecikmesi, iz ömrü ve takip buna göre
	var id := String(it.get("id", ""))
	var w27 := Silah27.weight(it)
	if w27 >= 0.0:
		return w27
	if id in ["ulu_kilic", "dag_cekici", "kor_cekici", "bozgun_kilici"]:
		return 1.0
	if id in HEAVY:
		return 0.8
	# v15 arketip ağırlıkları: hançer 0,15 · düellocu (yatağan, rüzgâr) 0,3 · kırbaç 0,3 · kılıç 0,45 · pala / sırık 0,5
	match id:
		"yatagan", "ruzgar_kilici":
			return 0.3
		"ay_palasi":
			return 0.2
		"pala":
			return 0.5
		"kayin_asasi", "teber":
			return 0.65
	match String(it.get("kind", "")):
		"dual":
			return 0.15
		"whip":
			return 0.3
		"thrust":
			return 0.5
	return 0.45


static var _base_aps: Dictionary = {}


static func _tempo_class(it: Dictionary) -> String:
	var id := String(it.get("id", ""))
	var c27 := Silah27.tempo_class(it)
	if c27 != "":
		return c27
	if id in ["ulu_kilic", "dag_cekici", "kor_cekici", "bozgun_kilici"]:
		return "dev"
	if id in ["gurz", "civili_topuz", "savas_baltasi", "ikiz_balta"]:
		return "agir"
	if id in ["teber", "erlik_tirpani", "kayin_asasi"]:
		return "uzun"
	if id in ["yatagan", "ruzgar_kilici"]:
		return "duello"
	if id == "ay_palasi":
		return "hancer"
	match String(it.get("kind", "")):
		"dual":
			return "hancer"
		"whip":
			return "kirbac"
		"thrust":
			return "mizrak"
		"heavy":
			return "agir"
	return "kilic"


static func _tempo_scale(it: Dictionary, spd_mult: float) -> float:
	## Eşyanın taban aps'ine göre hız sapması (malzeme, kalite, nitelik, ivme): 1 = taban tempo
	var id := String(it.get("id", ""))
	if not _base_aps.has(id):
		_base_aps[id] = float(Data.find_item(id).get("aps", it.get("aps", 1.0)))
	# v26: en çok %18 hızlanma (eski 0,55: malzeme + kalite + ivme / Ay Dansı tabanı 1,8 kat hızlandırabiliyordu)
	return clampf(float(_base_aps[id]) / maxf(0.05, float(it.get("aps", 1.0)) * spd_mult), 0.85, 1.6)


func _phase_times(it: Dictionary, c: Dictionary, sw: Dictionary, chain: bool, spd_mult: float, kind := "") -> Array:
	## [hazırlık, süpürme, kilit, toparlanma, tutuş] gerçek saniye: TEMPO + savuruşun çarpanları ("ws" hazırlık,
	## "ss" kilit — çark / çok vuruşlu savuruşta yay kilit evresinde döner) + bitiriş / bekleme / ağır + adımın tm'si
	## v20: + TEMPO_V20 yavaşlaması + saldırı hızı statı (hiz_bonus; Kızışma yükleri dahil)
	return tempo_phases(it, c, sw, chain, spd_mult, kind, hiz_bonus(it))


static func tempo_phases(it: Dictionary, c: Dictionary, sw: Dictionary, chain: bool, spd_mult: float, kind: String, hiz: float) -> Array:
	## _phase_times'ın durumsuz çekirdeği (ItemGen.dps de bunu kullanır). hiz: saldırı hızı (oran, sınıf etkisi uygulanmış)
	var cls := _tempo_class(it)
	var tp: Array = TEMPO[cls]
	var sc := _tempo_scale(it, spd_mult) * float(c.get("tm", 1.0))
	var M := float(tp[2]) * float(sw.get("ms", 1.0))
	var H := float(tp[6] if chain else tp[5])
	var W := maxf(0.016, float(tp[1] if chain else tp[0]) - float(tp[2]) - H) * float(sw.get("ws", 1.0))
	var L := float(tp[3]) * float(sw.get("ss", 1.0))
	var R := float(tp[4]) * float(sw.get("rs", 1.0))
	# v20 yavaşlama: süpürme payı (0) kombonun görünüşünü korur; uzayan kilit ve zincir hazırlığı
	var sl: Array = TEMPO_V20.get(cls, [0.0, 0.0, 0.0, 0.0, 0.0])
	var wk := 1.0 + TEMPO_YAVAS * float(sl[1] if chain else sl[0])
	W *= wk
	H *= wk
	M *= 1.0 + TEMPO_YAVAS * float(sl[2])
	L *= 1.0 + TEMPO_YAVAS * float(sl[3])
	R *= 1.0 + TEMPO_YAVAS * float(sl[4])
	# v25 ağır tempo: hazırlık, süpürme, kilit uzar; her savuruşa okunur bir hazırlık tutuşu eklenir
	var t25: Array = TEMPO_V25.get(String(it.get("id", "")), TEMPO_V25.get(cls, [1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0]))
	W *= 1.0 + TEMPO_AGIR * (float(t25[1] if chain else t25[0]) - 1.0)
	M *= 1.0 + TEMPO_AGIR * (float(t25[2]) - 1.0)
	L *= 1.0 + TEMPO_AGIR * (float(t25[3]) - 1.0)
	R *= 1.0 + TEMPO_AGIR * (float(t25[4]) - 1.0)
	H += TEMPO_AGIR * float(t25[6] if chain else t25[5])
	# v26: üçüncü katman (hafif / orta silahta zincir aralığı ~%25-30, ağırda ~%5)
	var t26: Array = TEMPO_V26.get(String(it.get("id", "")), TEMPO_V26.get(cls, [1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0]))
	W *= 1.0 + TEMPO_V26K * (float(t26[1] if chain else t26[0]) - 1.0)
	M *= 1.0 + TEMPO_V26K * (float(t26[2]) - 1.0)
	L *= 1.0 + TEMPO_V26K * (float(t26[3]) - 1.0)
	R *= 1.0 + TEMPO_V26K * (float(t26[4]) - 1.0)
	H += TEMPO_V26K * float(t26[6] if chain else t26[5])
	# v34: ağır silahın hazırlığı / tutuşu kısalır, zincir ilerledikçe hızlanır (TEMPO_V34)
	var t34: Array = TEMPO_V34.get(String(it.get("id", "")), TEMPO_V34.get(cls, []))
	if not t34.is_empty() and TEMPO_V34K > 0.0:
		var q := TEMPO_V34K
		var ramp := 1.0 + q * float(t34[6]) * float(maxi(0, (_combo_for(it)["chain"] as Array).find(c)))
		W *= (1.0 + q * (float(t34[1] if chain else t34[0]) - 1.0)) / ramp
		M *= (1.0 + q * (float(t34[2]) - 1.0)) / ramp
		L *= (1.0 + q * (float(t34[3]) - 1.0)) / ramp
		R *= 1.0 + q * (float(t34[4]) - 1.0)
		H *= (1.0 + q * (float(t34[5]) - 1.0)) / ramp
		if c.get("last", false):
			W *= 1.0 + q * (float(t34[7]) - 1.0)
	if _contact_k(sw) <= float(sw["hit"][0]) + 0.001:
		# temas anahtarı yok (çark, seri saplama): süpürme kilide katılır
		L += M
		M = 0.0
	if c.get("last", false):   # zincir sonu (Dead Cells bitirişi ~0,3 / 0,3): okunur hazırlık, uzun kilit
		W *= 1.3
		H += 0.017
		L *= 1.5 if float(sw.get("ss", 1.0)) <= 1.5 else 1.1   # çarkın yayı zaten uzun
	match kind:
		"pause":   # bekleme bitirişi: okunur bir duruş, adı yazılır
			W *= 1.5
			H += 0.033
			L *= 1.4
		"heavy":   # ağır saldırı: hazırlığın çoğu şarjda geçer; bırakınca kısa, sert; kilit uzun (darbe oturur)
			L *= 1.4
			R *= 1.25
	var out := [W * sc, M * sc, maxf(0.033, L * sc), maxf(0.05, R * sc), H * sc]
	if hiz > 0.0:
		# v20 saldırı hızı: her evre 1 / (1 + hiz) kısalır; en az okunur kare sayısı (taban zaten kısaysa taban)
		var k := 1.0 / (1.0 + hiz)
		var mins := [float(HIZ["min_wind"]), float(HIZ["min_sweep"]), float(HIZ["min_lock"]), 0.05, 0.0]
		for i in 5:
			out[i] = maxf(float(out[i]) * k, minf(float(out[i]), float(mins[i])))
	return out


## ------------------------------------------------------------------ v20 saldırı hızı ve Kızışma (HIZ tablosu)
const KIZISMA_FX := preload("res://scripts/core/KizismaFX.gd")
var kz_n := 0                  # Kızışma yükü
var kz_t := 0.0                # son yükten beri geçen süre (sn)
var kz_flash := 0.0            # tam yük parıltısı (1 → 0)
var _kz_atk: Dictionary = {}   # yükün verildiği savuruş (geçiş başına bir yük)
var _kz_pass := -1
var _kz_id := ""               # yükün ait olduğu silah (silah değişince söner)
var _kz_fx: Node2D
var hiz_test := -1.0           # test (dovus_testi): >= 0 ise kalıcı kaynaklar yerine bu yüzde kullanılır


static func hiz_kaynak(it: Dictionary) -> Dictionary:
	## Kalıcı saldırı hızı kaynakları (yüzde). it: hızı sorulan silah (kendi "hiz" niteliği yalnız ona işler)
	var out := {"silah": ItemGen.aff(it, "hiz"), "techizat": 0.0, "kurt": 0.0, "lutuf": 0.0, "umay": 0.0}
	if Game.run.is_empty():
		return out
	var slots: Dictionary = Game.run.get("slots", {})
	for sk in ["melee", "second", "g1", "g2"]:
		var o: Dictionary = slots.get(sk, {})
		if not o.is_empty():
			out["techizat"] = float(out["techizat"]) + ItemGen.aff(o, "saldiri_hizi")
	out["kurt"] = float(HIZ["kurt"]) * float(Game.run.get("ongun", {}).get("kurt", 0))
	out["lutuf"] = float(HIZ["lutuf"]) if Game.has_lutuf("yel_ana") else 0.0
	out["umay"] = float(HIZ["umay"]) * float(Game.umay_level("hiz"))
	return out


static func hiz_kalici(it: Dictionary) -> float:
	## Kalıcı kaynakların toplamı (yüzde; üst sınır HIZ.cap)
	var s := 0.0
	for v in hiz_kaynak(it).values():
		s += float(v)
	return minf(float(HIZ["cap"]), s)


static func hiz_oran(it: Dictionary, pct: float) -> float:
	## yüzde → evre kısaltma oranı: mutlak üst sınır (cap_all) ve silah sınıfının etkisi (ağır silahta az)
	return clampf(pct, 0.0, float(HIZ["cap_all"])) / 100.0 * float(HIZ["sinif"].get(_tempo_class(it), 1.0))


func hiz_yuzde(it: Dictionary) -> float:
	## Bu silah için şu anki saldırı hızı (yüzde): kalıcı kaynaklar + Kızışma yükleri
	var base := hiz_test if hiz_test >= 0.0 else hiz_kalici(it)
	return minf(float(HIZ["cap_all"]), base + kz_yuzde(it))


func hiz_bonus(it: Dictionary) -> float:
	return hiz_oran(it, hiz_yuzde(it))


func kz_yuzde(it: Dictionary) -> float:
	if not it.has("kz_v") or String(it.get("id", "")) != _kz_id:
		return 0.0
	return float(kz_n) * float(it["kz_v"])


func hiz_yuk() -> Array:
	## HUD / görsel: [yük, en çok, saldırı hızı yüzdesi, tür] — Kızışma ya da yatağanın ivmesi; ikisi de yoksa []
	var it := slot(mel_slot)
	if it.has("kz_v"):
		var n := kz_n if String(it.get("id", "")) == _kz_id else 0
		return [n, int(it.get("kz_max", 5)), kz_yuzde(it), "kizisma"]
	if it.get("mech_id", "") == "ivme":
		return [momentum, 5, float(momentum) * float(it.get("mech_v", 8.0)), "ivme"]
	return []


func _kz_gain(it: Dictionary) -> void:
	## Kızışma: yakın vuruş isabeti; savuruş geçişi başına bir yük (çok düşmanlı vuruş tek yük, süreyi tazeler)
	if not it.has("kz_v") or atk.is_empty() or String(it.get("id", "")) != String(slot(mel_slot).get("id", "")):
		return
	kz_t = 0.0
	var mi := int(atk.get("multi_i", 0))
	if is_same(atk, _kz_atk) and mi == _kz_pass:
		return
	_kz_atk = atk
	_kz_pass = mi
	if _kz_id != String(it.get("id", "")):
		_kz_id = String(it.get("id", ""))
		kz_n = 0
	var mx := int(it.get("kz_max", 5))
	if kz_n >= mx:
		return
	kz_n += 1
	if kz_n >= mx:
		# tam yük: kısa altın parıltı (gövde flaşı, halka, kolda altın mürekkep)
		kz_flash = 1.0
		anim.set_flash(0.32)
		get_tree().create_timer(0.05).timeout.connect(func() -> void:
			if is_instance_valid(self):
				anim.set_flash(0.0))
		FX.ring(center(), 20.0, Color(1.0, 0.84, 0.42), 0.28)
		FX.text(center() + Vector2(0, -42), "KIZIŞMA", Color(1.0, 0.86, 0.45), 8)
		Ses.play("yay_dolu", -12.0, 1.35)


func kz_lose() -> void:
	## Hasar alınca Kızışma tümden söner
	kz_n = 0
	kz_t = 0.0


func _kz_pitch() -> float:
	## Savuruş sesi Kızışma yüküyle hafifçe incelir
	var y := hiz_yuk()
	if y.is_empty() or int(y[1]) <= 0:
		return 1.0
	return 1.0 + float(HIZ["kz_pitch"]) * float(y[0]) / float(y[1])


func _hiz_tick(delta: float) -> void:
	## Her kare: Kızışma sönmesi (kz_decay sn vuruşsuz kalınca 0,25 sn'de bir yük), yay temposu, görsel düğüm
	kz_t += delta
	kz_flash = maxf(0.0, kz_flash - delta * 3.5)
	if kz_n > 0:
		if String(slot(mel_slot).get("id", "")) != _kz_id:
			kz_n = 0
		elif kz_t > float(HIZ["kz_decay"]):
			kz_n -= 1
			kz_t = float(HIZ["kz_decay"]) - 0.25
	var bw := slot(sec_slot)
	if bw.get("kind", "") == "bow":
		var pct := hiz_test if hiz_test >= 0.0 else hiz_kalici(bw)
		Okculuk.hiz_k = 1.0 / (1.0 + hiz_oran(bw, pct) * float(HIZ["yay"]))
	else:
		Okculuk.hiz_k = 1.0
	if _kz_fx == null and is_inside_tree():
		_kz_fx = KIZISMA_FX.new()
		_kz_fx.set("pl", self)
		add_child(_kz_fx)


func _sec_cd(it: Dictionary) -> float:
	## Fırlatma / büyü beklemesi: 1 / aps, saldırı hızıyla kısalır (HIZ.atis oranında)
	var pct := hiz_test if hiz_test >= 0.0 else hiz_kalici(it)
	return 1.0 / maxf(0.05, float(it["aps"])) / (1.0 + hiz_oran(it, pct) * float(HIZ["atis"]))


static func tempo_aps(it: Dictionary, pct: float) -> Array:
	## Sürekli zincirde (her temasta yeniden basış) [vuruş / sn, hasar çarpanı / sn]: ItemGen.dps ve kartın "Hız" değeri.
	## Bir tur = zincirin her adımının hazırlık + tutuş + süpürme + kilit süresi (zincir içi; toparlanma görünmez).
	var chain: Array = _combo_for(it)["chain"]
	var hz := hiz_oran(it, pct)
	var t := 0.0
	var hits := 0.0
	var mult := 0.0
	for i in chain.size():
		var c: Dictionary = chain[i]
		var sw: Dictionary = swing_def(c["s"])
		var spd := 1.0
		if it.get("kind", "") == "dual":
			spd *= 1.0 + DUAL_RAMP * i
		if it.get("mech_id", "") == "ay_dansi":
			spd *= 1.0 + float(it.get("mech_v", 6.0)) / 100.0 * i
		if it.get("flaw", "") == "agir":
			spd *= 0.88
		var ph := tempo_phases(it, c, sw, true, spd, "", hz)
		t += float(ph[0]) + float(ph[1]) + float(ph[2]) + float(ph[4])
		var n := float((sw["multi"] as Array).size()) if sw.has("multi") else 1.0
		if c.get("double", false):
			n *= 2.0
		hits += n
		mult += n * float(c.get("mult", 1.0))
	if t <= 0.0:
		return [0.0, 0.0]
	return [hits / t, mult / t]


func _atk_advance(delta: float) -> void:
	## Zaman bükmesi: atk.t (normalize süre × dur) evreye göre farklı hızda ilerler (hazırlık, süpürme, kilit,
	## toparlanma); evre sınırı kare içinde aşılırsa kalan süre sonraki evrenin hızıyla sürer.
	var D := float(atk["dur"])
	var sw: Dictionary = atk["sw"]
	var b := [float(sw["hit"][0]), _contact_k(sw), float(sw["hit"][1]), 1.0]
	var ph: Array = atk["ph"]
	var rem := delta
	for guard in 6:
		var k := float(atk["t"]) / D
		var seg := 3
		for i in 3:
			if k < float(b[i]):
				seg = i
				break
		var k0 := 0.0 if seg == 0 else float(b[seg - 1])
		var span := float(b[seg]) - k0
		if span <= 0.0001 and seg < 3:
			atk["t"] = float(b[seg]) * D + 0.000001
			continue
		var rate := span * D / maxf(0.001, float(ph[seg]))
		var to_end := (float(b[seg]) * D - float(atk["t"])) / rate
		if rem <= to_end or seg == 3:
			atk["t"] = float(atk["t"]) + rem * rate
			return
		atk["t"] = float(b[seg]) * D + 0.000001
		rem -= to_end


static func _contact_k(sw: Dictionary) -> float:
	## İsabetin başladığı an (bıçağın düşmana vardığı kare): savuruşun "ck"si; yoksa vuruş penceresinden sonraki ilk
	## anahtar (hızlanan yayın sonu). Çark ve çok vuruşlu savuruşlarda pencerenin başı.
	if sw.has("ck"):
		return float(sw["ck"])
	var h0 := float(sw["hit"][0])
	if sw.get("around", false) or sw.has("multi"):
		return h0
	for key in sw["keys"]:
		if float(key[0]) > h0 + 0.001:
			return minf(float(key[0]), float(sw["hit"][1]) - 0.01)
	return h0


static func swing_def(n: String) -> Dictionary:
	## Savuruş tablosu: SWINGS + v27 yeni silahların savuruşları (Silah27.SWINGS)
	if SWINGS.has(n):
		return SWINGS[n]
	return Silah27.swing(n)


static func plane_def(n: String) -> Dictionary:
	if PLANES.has(n):
		return PLANES[n]
	return Silah27.plane(n)


static func _combo_for(it: Dictionary) -> Dictionary:
	if Silah27.has_combo(it):
		return Silah27.combo(it)   # v27 (Gün-Ay İkizi'nde duruşa göre)
	if COMBOS_EXTRA.has(it.get("id", "")):
		return COMBOS_EXTRA[it["id"]]
	if COMBOS.has(it.get("id", "")):
		return COMBOS[it["id"]]
	return COMBOS.get(it.get("kind", "slash"), COMBOS["slash"])


func _reach(it: Dictionary) -> float:
	var r27 := Silah27.reach(it)
	if r27 > 0.0:
		return r27
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
		var ov: Array = Silah27.step_override(self, it, chain, step, c)   # v27 Kistin: Yere Çalma yalnızca bağlıyken
		step = int(ov[0])
		c = ov[1]
	# v22 yön: savuruş oyuncunun yönüne çıkar — yön tuşu basılıysa o yöne, değilse basış anındaki yöne (kuyruktan
	# çıkan basış), o da yoksa baktığı yöne. Düşmana kendiliğinden dönme yok (eski _assist_face kalktı).
	var din := Input.get_axis("sol", "sag")
	var face0 := facing
	if roll_t <= 0.0:
		if din != 0.0:
			facing = int(signf(din))
		elif not _press_used and _press_dir != 0:
			facing = _press_dir
		anim.set_facing(facing)
	# yön tuşuyla özel hamleler (zinciri bozmaz, araya girer): dalış, göğe savurma, akın kesiği, dönüş kesiği, diz biçen
	var sp := _special_move(it)
	# v19 Kut Alma: önde duruşu kırık / sersem ve canı az bir düşman varsa saldırı infaza döner (dalış hariç)
	var ex_t: Node = null
	if not sp.get("plunge", false):
		ex_t = _exec_target(it)
		if ex_t != null:
			sp = _exec_move(it)
	if not sp.is_empty():
		c = sp
		is_pause = false
		step = maxi(0, last_step)
	if facing != face0 and (din == 0.0 or int(signf(din)) != facing) and (_press_used or _press_dir != facing):
		slog("oto_donus", String(c["s"]), true)
	var sw: Dictionary = swing_def(c["s"])
	sw = SanatAnim.swing(it, c, sw, step, false)   # v27: görsel kopya (açılar aileye göre; zaman alanları aynı)
	var spd_mult := 1.0   # v20: "hiz" niteliği artık saldırı hızı statında (hiz_bonus)
	if it.get("mech_id", "") == "ivme":
		spd_mult *= 1.0 + momentum * float(it.get("mech_v", 8.0)) / 100.0
	if it.get("kind", "") == "dual":
		spd_mult *= 1.0 + DUAL_RAMP * step  # ikiz bıçak: kombo ilerledikçe hızlanır (v25: 0,07 → 0,04)
	if it.get("mech_id", "") == "ay_dansi":
		spd_mult *= 1.0 + float(it.get("mech_v", 6.0)) / 100.0 * step
		if c.get("last", false) and not is_pause:
			inv_t = maxf(inv_t, 0.6)
			FX.ghost(anim.base, Color(0.8, 0.9, 1.0, 0.5), 0.3)
	if it["flaw"] == "agir":
		spd_mult *= 0.88
	# v18 tempo: evre süreleri silah sınıfından (TEMPO); zincir içindeyse (önceki savuruşun toparlanmasından ya da hemen
	# ardından) kısa zincir hazırlığı ve kol önceki takip pozundan gerilir (dinlenme pozuna dönmeden)
	var flowing: bool = (not atk.is_empty() and not atk.get("heavy", false)) or (since_atk < 0.12 and _last_pose_ok)
	var from_pose: Array = _last_pose.duplicate() if (flowing and _last_pose_ok) else []
	var ph := _phase_times(it, c, sw, flowing and not is_pause, spd_mult, "pause" if is_pause else "")
	# v19 Kut Yankısı: zamanında basılan vuruş daha kısa gerilir (hazırlık ve tutuş V19.yk_wind)
	_atk_t0 = Game.clock()   # v26: savuruşun başladığı an (karşı vuruş yalnızca hazırlıktan sonra başlayan savuruşa)
	_atk_fresh = not flowing
	var yanki := ex_t == null and Game.clock() - _yk_ready < 0.5
	_yk_ready = -9.0
	_yk_early = false
	if yanki:
		ph[0] = float(ph[0]) * float(V19["yk_wind"])
		ph[4] = float(ph[4]) * float(V19["yk_wind"])
	elif ex_t == null:
		yk_n = 0
	var total := float(ph[0]) + float(ph[1]) + float(ph[2]) + float(ph[3])
	if c.get("special", false):
		_move_label(String(c.get("name", "")), Color(0.75, 0.95, 1.0), 8)
		if c.get("plunge", false):
			velocity = Vector2(velocity.x * 0.3, -160.0)
	if not atk.is_empty():
		_end_trail()
	atk = {"step": step, "c": c, "sw": sw, "phase": "wind", "t": 0.0, "dur": total, "hit": [], "item": it, "hold": 0.0, "pause": is_pause, "multi_i": 0,
		"ph": ph, "chain": flowing}
	if not from_pose.is_empty():
		atk["from"] = _unwrap_from(from_pose, sw)
	atk["art"] = SanatAnim.info(it, c, sw, step, false)   # v27
	atk["air"] = not is_on_floor()
	_heavy_armed = _mel_down_t >= 0.0 and _weight(it) <= float(FLOW["heavy_nowait_w"]) and _can_hold_heavy(c)
	atk["held"] = _mel_down_t >= 0.0
	# v15 süper zırh: dev kılıç / dağ çekici savuruşları sarsılmaz (bayrağı take_hit / koordinatör okur)
	atk["super_armor"] = bool(c.get("sa", false))
	if not atk["super_armor"] and _tempo_class(it) in V34_AGIR["sa_wind"]:
		atk["super_armor"] = true   # v34: ağır / dev silahın hazırlığı sarsılmaz (vuruş anında söner)
		atk["sa_wind"] = true
	var on_beat := _usul_press()
	if yanki:
		_yk_begin(on_beat)
	if ex_t != null:
		_exec_begin(ex_t)
	combo_step = step
	melee_buf = 0.0
	if log_on:
		var cz := "basis"
		if _press_used:
			cz = "basissiz"
		elif _gt - _press_gt > 0.35 or (_gt - _press_gt > 0.22 and not _press_hit):
			cz = "gec_arabellek"
		slog(cz, String(c["s"]), false, {"step": step, "alt": is_pause, "name": String(c.get("name", ""))})
	_press_used = true
	_swing_sfx(it, sw, is_pause)
	vis_scale = Vector2(0.92, 1.06)
	if is_pause:
		# bekleme bitirişi: kısa parlama ve yükselen kıvılcımlar; adı ekranda belirir
		anim.set_flash(0.6)
		get_tree().create_timer(0.07).timeout.connect(func() -> void: anim.set_flash(0.0))
		_move_label(String(c.get("name", "")), Color(1.0, 0.85, 0.45), 9)
		FX.burst(center(), Color(1.0, 0.85, 0.45), 14, 90, 0.4, 0.2, -60, true)
		if c["s"] == "slam" and is_on_floor():
			velocity.y = -330.0  # sıçra, sonra çak
	# kargı hücumu
	if it.get("mech_id", "") == "hucum" and absf(velocity.x) > RUN * 0.6 and is_on_floor():
		atk["dash"] = float(it.get("mech_v", 60.0))
		inv_t = maxf(inv_t, 0.2)
	if c.has("dash"):
		atk["dash"] = float(c["dash"])
	# Kurt Pençeleri: havadayken öndeki en yakın düşmana sıçra (v22: yalnızca baktığı yönde; dönmez)
	if it.get("mech_id", "") == "sicrama" and not is_on_floor():
		var best: Node = null
		var bd := 120.0
		for e in get_tree().get_nodes_in_group("dusman"):
			if is_instance_valid(e) and not e.dead and (e.center().x - center().x) * float(facing) > 2.0:
				var d: float = center().distance_to(e.center())
				if d < bd:
					bd = d
					best = e
		if best:
			var to: Vector2 = best.center() - center()
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
		# v15 sırık atlayışı: kargı / mızrak sırığı yere saplar, gövde ileri-yukarı fırlar; kalkan uç havaya atar
		if it.get("kind", "") == "thrust" and TWO_HANDED.has(it.get("id", "")):
			return {"s": "pole_vault", "mult": 0.9, "kb": 60.0, "launch": 300.0, "special": true, "hop": -470.0, "vault": true, "tm": 1.0, "name": "Sırık Atlayışı"}
		return {"s": "uppercut_2h" if heavy_w else "rise", "mult": 1.1, "kb": 40.0, "launch": 360.0, "special": true, "hop": -330.0, "tm": 1.05, "name": "Göğe Savur"}
	if crouch_hold and crouched:
		return {"s": "sweep_low", "mult": 1.1, "kb": 60.0, "special": true, "trip": true, "tm": 0.9, "name": "Diz Biçen"}
	if sprint and absf(velocity.x) > RUN * 1.2:
		return {"s": "lunge", "mult": 1.5, "kb": 240.0, "dash": 140.0, "special": true, "tm": 1.0, "name": "Akın Kesiği"}
	var since_roll := 2.0 - rolled_t
	if since_roll >= ROLL_T * float(FLOW["roll_atk_k"]) and since_roll < ROLL_T + float(FLOW["roll_atk_win"]):
		return {"s": "spin", "mult": 1.3, "kb": 180.0, "special": true, "crit": true, "tm": 0.9, "name": "Dönüş Kesiği"}
	return {}


func combo_add(e: Node) -> void:
	## Kesintisiz isabet: sayaç artar, kademe atlayınca ödül (Kut, ağır çekim, ses)
	combo_n += 1
	combo_t = 2.4 * (1.5 if Adlar.earned("kanturali") else 1.0)
	combo_best = maxi(combo_best, combo_n)
	var r := 0
	for i in COMBO_RANKS.size():
		if combo_n >= int(COMBO_RANKS[i][0]):
			r = i + 1
	if r > combo_rank:
		combo_rank = r
		if r >= COMBO_RANKS.size():
			Adlar.deed("kanturali", center())
		var rk: Array = COMBO_RANKS[r - 1]
		var col: Color = rk[2]
		# v22: kademe yazısı küçüldü ve daha yukarıda (savaşanların üstüne binmesin); halka yalnızca üst kademelerde
		FX.text(center() + Vector2(0, -70), "%s!  x%d" % [rk[1], combo_n], col, 7 + r)
		if r >= 3:
			FX.ring(center(), 24 + 6 * r, col, 0.3)
		Ses.play("seviye", -6.0 + r, 0.9 + 0.08 * r)
		add_kut(4.0 * r)
		if r >= 3:
			Game.zoom_punch(0.03 + 0.01 * r)   # v22: kademe ağır çekimi kalktı (kombonun ortasında akışı kesiyordu)


func combo_break(reason := "") -> void:
	if combo_n >= 8:
		FX.text(center() + Vector2(0, -50), "Kombo x%d %s" % [combo_n, reason], Color(0.8, 0.75, 0.85), 8)
	combo_n = 0
	combo_rank = 0
	combo_t = 0.0
	yk_n = 0
	_yk_seal = false


func combo_mult() -> float:
	return 1.0 + minf(0.45, 0.015 * float(combo_n))


# ------------------------------------------------------------------ v19 dövüş mekanikleri (V19)
func _hit_cancel_ok() -> bool:
	## İsabet iptali: savuruş bir düşmana oturduktan V19.hc_cancel sonra kilidin kalanı zıplama ya da ikincil ile
	## kesilir (Dead Cells'te kilit yuvarlanmayla kesilir; burada vuruş "onaylanınca" zıplama da keser: fırlatma →
	## zıpla → hava kombosu akar). İnfaz, dalış ve şimşek hamlesi kesilmez.
	if atk.is_empty() or atk["phase"] != "act" or not atk.has("hit_at"):
		return false
	var c: Dictionary = atk["c"]
	if c.get("exec", false) or c.get("plunge", false) or atk.has("dash_px"):
		return false
	return Game.clock() - float(atk["hit_at"]) >= float(V19["hc_cancel"])


func _yk_on_press() -> void:
	## Kut Yankısı: saldırı basışı savuruşun ilk isabetinden sonraki V19.yk_win içinde mi (vuruş donması da sayılır)?
	## İsabetten önce (hazırlıkta / süpürmede) basmak bu savuruşun yankısını bozar: ödül tuşa ezbere basmaya değil,
	## vuruşun oturduğunu görüp basmaya.
	var now := Game.clock()
	if not atk.is_empty() and not atk.get("heavy", false) and not atk.has("hit_at") and atk["phase"] in ["wind", "act"]:
		_yk_early = true
		return
	# pencere vuruş donması bittiğinde başlar (donma 35-170 ms sürebilir; donmada basmak da sayılır)
	var open_t := maxf(_yk_contact, minf(Game._hitstop_until, _yk_contact + 0.25))
	if _yk_contact > 0.0 and not _yk_early and now - open_t <= float(V19["yk_win"]):
		_yk_ready = now
		_yk_contact = -9.0


func _yk_begin(on_beat: bool) -> void:
	## Yankılı savuruş başladı: seri sayılır; V19.yk_seal'da Kut Mührü (sıradaki isabet kesin kritik).
	## Usul vuruşuna da denk geldiyse iki yankı kesiği.
	yk_n += 1
	v19_stats["yanki"] = int(v19_stats["yanki"]) + 1
	atk["yanki"] = 2 if on_beat else 1
	var col := Color(1.0, 0.84, 0.42)
	if yk_n >= int(V19["yk_seal"]):
		yk_n = 0
		_yk_seal = true
		v19_stats["muhur"] = int(v19_stats["muhur"]) + 1
		_move_label("KUT MÜHRÜ", col, 10)
		Ses.play("usul_seri" if Ses.has("usul_seri") else "seviye", -5.0, 1.15)
		FX.ring(center(), 30, col, 0.3)
		anim.set_flash(0.5)
		get_tree().create_timer(0.06).timeout.connect(func() -> void: anim.set_flash(0.0))
	# v22: her yankıda "YANKI" yazısı ve gövde hayaleti yok (hızlı kombolarda ekranı dolduruyordu); işaret altın iz + ses
	Ses.play("kut_tane" if Ses.has("kut_tane") else "seviye", -7.0, 1.2 + 0.15 * yk_n, 0.02, 0.0)


func _yk_cue(hp: Vector2) -> void:
	## İsabet anı işareti: elde küçük altın halka — "şimdi bas" (yankı penceresi açıldı); v22: daha küçük
	var hand := arm_root.to_global(_hand_local)
	InkFX.ring(hand.lerp(hp, 0.35), 6.5, 9, 0.12)


func _v19_opts(e: Node, c: Dictionary, opts: Dictionary) -> String:
	## Yakın vuruşun v19 seçenekleri (_deal öncesi): duruş hasarı, infaz, Kut Mührü, karşılık, karşı vuruş, bitiriş
	## kritiği. Dönen etiket isabetten sonra efekt için (_v19_after_hit).
	var tag := ""
	var w := _weight(atk["item"])
	# duruş hasarı (Enemy.POISE): hançer ~1,2 · kılıç ~1,7 · dev 2,5; bitiriş / ağır saldırı +1
	opts["poise"] = 1.0 + 1.5 * w + (1.0 if opts.get("last", false) or atk.get("heavy", false) else 0.0)
	if c.has("burn"):
		opts["burn"] = float(c["burn"])
	if c.get("exec", false) and e == atk.get("exec_t"):
		opts["exec"] = true
		opts["force_crit"] = true
		opts["krit_neden"] = "infaz"
		return "infaz"
	if _yk_seal:
		_yk_seal = false
		opts["force_crit"] = true
		opts["krit_neden"] = "muhur"
		tag = "muhur"
	if riposte_t > 0.0 and not atk.get("clashed", false):   # karşılık sıradaki savuruşta (çarpışan savuruşun kendisinde değil)
		riposte_t = 0.0
		opts["force_crit"] = true
		opts["krit_neden"] = "karsilik"
		tag = "karsilik"
	if _counter_ok(e):
		opts["force_crit"] = true
		opts["krit_neden"] = "karsi"
		opts["counter"] = true
		if not e.is_boss:
			opts["stun"] = maxf(float(opts.get("stun", 0.0)), 0.35 if e.heavy else 0.5)
		tag = "karsi"
	if c.get("fc", false) and not atk.get("pause", false):
		if _bitiris(opts) and tag == "":   # v23: Kut Yankısı'yla kritik, değilse bitiriş hasarı
			tag = "fc"
	return tag


func _v19_after_hit(e: Node, it: Dictionary, c: Dictionary, hp: Vector2, hdir: Vector2, tag: String, first_hit: bool, _killed: bool) -> void:
	## İsabetten sonra: yankı penceresi (ilk isabet anı), yankı kesiği, etiket efektleri, bitiriş vurgusu
	if not atk.has("hit_at"):
		atk["hit_at"] = Game.clock()
		_yk_contact = float(atk["hit_at"])
		if not c.get("exec", false):
			_yk_cue(hp)
	match tag:
		"infaz":
			_exec_reward(e, hp)
		"muhur":
			FX.text(hp + Vector2(0, -26), "MÜHÜR!", Color(1.0, 0.84, 0.42), 8)
			InkFX.stamp(hp, 9)
		"karsilik":
			FX.text(hp + Vector2(0, -26), "karşılık!", Color(1.0, 0.9, 0.5), 8)
		"karsi":
			v19_stats["karsi"] = int(v19_stats["karsi"]) + 1
			FX.text(hp + Vector2(0, -28), "KARŞI VURUŞ", Color(1.0, 0.55, 0.35), 8)
			InkFX.flourish(hp, "parry", 0)
			Ses.play("darbe_metal" if Ses.has("darbe_metal") else "darbe_kunt", -6.0, 0.9)
	if first_hit and c.get("last", false) and not atk.get("pause", false):
		_finisher_fx(it, hp, hdir, e, _killed)


func _finisher_fx(it: Dictionary, hp: Vector2, hdir: Vector2, e: Node = null, killed := false) -> void:
	## Zincir bitirişi (Dead Cells'in son vuruşu gibi): ayrı bir olay olarak okunur.
	## v35: hedefin üstüne sınıfa özgü hüsnühat kesiği (KesikFX: kılıç çapraz hilal, hançer çarpı, mızrak deliş hattı,
	## ağır dik yarma + yer sürüntüsü, uzun sap geniş süpürme, kırbaç S kıvrımı; kızıl / altın vurgu) + ışınsal mürekkep
	## dikenleri; kısa yakınlaşma, vuruş yönünde sarsıntı ve itiş, öldürüşte kısa ağır çekim. Darbe karesi (ImpactFrame)
	## eklenmedi: beyaz silüet kesiği örtüyordu (kritik / şarjlı ağır / infaz kendi karesini verir). Eski büyük sıçrantı + halka kesiğe devredildi (üst üste binmesin).
	var cls := _tempo_class(it)
	var w := _weight(it)
	var wf: Dictionary = WFX.get(it.get("id", ""), {})
	var renk: Color = wf.get("col", Color(0, 0, 0, 0))
	var at := hp
	if e != null and is_instance_valid(e) and e.has_method("center"):
		at = e.center().lerp(hp, 0.4)
	KesikFX.bitiris(at, facing, cls, 0.6 + 0.6 * w, renk)
	InkFX.hit(_impact_kind(it) if _impact_kind(it) != "magic" else "cut", hp, hdir, InkFX.weapon_pal(it), 1, 0.8 + 0.2 * w)
	var agir: bool = cls in V34_AGIR["sa_wind"]
	Game.zoom_punch(float(V35["fin_zoom_agir"] if agir else V35["fin_zoom"]) + 0.015 * w)
	Game.shake_dir(float(V35["fin_sarsinti"]) * (0.7 + 0.5 * w), Vector2(facing, 0.5 if agir else 0.2))
	Game.kick(Vector2(facing, 0.3 if agir else 0.0), float(V35["fin_itis"]) * (0.8 + 0.4 * w))
	if killed:
		Game.slowmo(float(V35["olum_yavas"][0]), float(V35["olum_yavas"][1]))


func _counter_ok(e: Node) -> bool:
	## Karşı vuruş: düşman saldırı hazırlığında ("!" uyarısı) ve bu hazırlıkta henüz karşılanmadı
	## v26: yalnızca okunan "!"ye: zırhlı "!!" hazırlığa değil, ve savuruş hazırlık başladıktan sonra başlamış olmalı
	## (tuşa ezbere basan oyuncunun önceden başlamış savuruşu hazırlığa denk gelince kesin kritik almasın)
	if not ("state" in e) or String(e.state) != "windup":
		return false
	if not e.is_boss and "sa_t" in e and float(e.sa_t) > 0.0:
		return false
	if e.has_meta("v26_tele_t") and _atk_t0 < float(e.get_meta("v26_tele_t")) - 0.03:
		return false
	if not e.is_boss and not _atk_fresh:
		return false   # zincirin akışındaki (ezilen) savuruş "!"yi okumuş sayılmaz: dur, gör, karşıla
	var last: float = float(e.get_meta("v19_cv", -9.0))
	if Game.clock() - last < 0.9:
		return false
	e.set_meta("v19_cv", Game.clock())
	return true


func _exec_target(it: Dictionary) -> Node:
	## Kut Alma hedefi: erim + V19.ex_reach içinde, infaz edilebilir (Enemy.exec_ok) en yakın düşman. v22: yalnızca
	## oyuncunun baktığı yönde (ya da tam dibinde); arkadaki için oyuncu kendisi döner.
	var R := _reach(it) + float(V19["ex_reach"])
	var best: Node = null
	var bs := INF
	for e in _foes_near(R):
		if not e.has_method("exec_ok") or not e.exec_ok():
			continue
		var dx: float = e.global_position.x - global_position.x
		if dx * float(facing) < -6.0:
			continue
		var score := absf(dx)
		if score < bs:
			bs = score
			best = e
	return best


func _exec_move(it: Dictionary) -> Dictionary:
	## İnfaz savuruşu: silah sınıfının en okunur bitirişi (kılıç çekiş kesiği, hançer içinden geçiş, mızrak deliş,
	## ağır baş üstü ezme, uzun sap biçme, kırbaç şaklaması)
	var cls := _tempo_class(it)
	var c := {"s": String(EXEC_SW.get(cls, "iai")), "mult": 1.0, "kb": 260.0, "special": true, "exec": true, "tm": 0.85, "name": ""}
	if cls == "hancer":
		c["through"] = true
	if cls in ["agir", "dev"]:
		c["slam"] = true
	return c


func _exec_begin(e: Node) -> void:
	## İnfaz başladı: kısa ağır çekim (hazırlık bir "nefes" gibi okunur), dokunulmazlık, hedefte kızıl mürekkep halkası
	atk["exec_t"] = e
	atk["super_armor"] = true
	inv_t = maxf(inv_t, 0.5)
	Game.slowmo(0.35, 0.18)
	InkFX.ring(e.center(), 28.0, 0, 0.28)
	FX.ghost(anim.base, Color(1.0, 0.4, 0.35, 0.45), 0.22)
	Ses.play("savur_hazirlik" if Ses.has("savur_hazirlik") else "savur_dev", -6.0, 0.9)


func _exec_strike() -> void:
	## Vuruş anı: hedefe doğru atıl (aradaki boşluk kapanır), iz kesin isabet eder (_melee_hits zorlar)
	var ev: Variant = atk.get("exec_t")   # v26: serbest bırakılmış hedef tipli değişkene atanınca betik hatası veriyordu
	if ev == null or not is_instance_valid(ev):
		return
	var e: Node = ev
	if e.dead:
		return
	var gap: float = absf(e.global_position.x - global_position.x) - float(e.size.x) * 0.5 - _reach(atk["item"]) * 0.55
	if gap > 0.0 and not atk.get("through", false):
		velocity.x = float(facing) * clampf(gap * 9.0, 120.0, 720.0)
	for i in 2:
		FX.ghost(anim.base, Color(1.0, 0.45, 0.4, 0.4), 0.2)


func _exec_reward(e: Node, hp: Vector2) -> void:
	## İnfaz ödülü: can, Kut, büyük mürekkep damgası, darbe karesi
	v19_stats["infaz"] = int(v19_stats["infaz"]) + 1
	heal(max_hp() * float(V19["ex_heal"]))
	add_kut(float(V19["ex_kut"]))
	InkFX.stamp(hp, 0)
	InkFX.kill(hp, true)
	FX.text(hp + Vector2(0, -30), "KUT ALINDI", Color(1.0, 0.42, 0.34), 9)
	FX.flash_light(hp, Color(1.0, 0.5, 0.4), 170.0, 2.0, 0.22)
	ImpactFrame.play([self, e], 1.0, 3, true)
	Game.zoom_punch(0.07)
	Game.slowmo(0.3, 0.12)
	Game.rumble(0.7, 0.3, 0.16)
	Ses.play("olum_vurus" if Ses.has("olum_vurus") else "darbe_kritik", -1.0, 0.95)
	Ses.play("usul_dum" if Ses.has("usul_dum") else "seviye", -6.0, 0.8)


func _clash(from: Node, projectile: Node, facing_src: bool) -> bool:
	## Çarpışma (yakın dövüşle savuşturma): savuruş vuruşa başladıktan V19.pr_win içinde (bıçak önünde dönerken)
	## gelen darbe ya da mermi, bıçağın kutusuna değiyorsa bıçağa çarpar. Bossların yakın darbeleri karşılanmaz
	## (mermileri karşılanır).
	if atk.is_empty() or atk["phase"] != "act" or not atk.has("strike_at") or not facing_src:
		return false
	if Game.clock() - float(atk["strike_at"]) > float(V19["pr_win"]):
		return false
	var box := _swing_box(String(atk["c"]["s"]), _reach(atk["item"])).grow(10.0)
	if projectile != null and is_instance_valid(projectile):
		if not box.has_point(projectile.global_position):
			return false
	elif from != null and is_instance_valid(from) and from.has_method("hurt_rect"):
		if "is_boss" in from and from.is_boss:
			return false
		if not box.intersects(from.hurt_rect()):
			return false
	else:
		return false
	_clash_fx(from, projectile)
	return true


func _clash_fx(from: Node, projectile: Node) -> void:
	v19_stats["carpisma"] = int(v19_stats["carpisma"]) + 1
	atk["clashed"] = true
	var p := center() + Vector2(facing * 14, -2)
	inv_t = maxf(inv_t, 0.25)
	riposte_t = float(V19["pr_riposte"])
	Game.hitstop(0.08)
	Game.slowmo(0.35, 0.16)
	Game.kick(Vector2(-facing, 0), 4.0)
	Game.rumble(0.4, 0.45, 0.1)
	FX.sparks(p, Vector2(facing, -0.5), Color(1.0, 0.92, 0.6), 14, 240.0)
	FX.flash_light(p, Color(1.0, 0.9, 0.55), 150.0, 2.0, 0.2)
	InkFX.flourish(p, "parry", 9)
	FX.text(center() + Vector2(0, -34), "ÇARPIŞMA", Color(1.0, 0.9, 0.5), 9)
	Ses.play("ors" if Ses.has("ors") else "darbe_metal", -3.0, 1.15)
	Ses.play("darbe_metal" if Ses.has("darbe_metal") else "darbe_kunt", -5.0, 1.25)
	add_kut(8.0)
	vis_scale = Vector2(0.9, 1.08)
	if projectile != null and is_instance_valid(projectile) and projectile.has_method("reflect"):
		projectile.reflect(facing, 1.2)
	elif from != null and is_instance_valid(from):
		var hv: bool = "heavy" in from and from.heavy
		if from.has_method("stun"):
			from.stun(float(V19["pr_stun_heavy"]) if hv else float(V19["pr_stun"]))
		if "velocity" in from:
			from.velocity.x = float(facing) * (60.0 if hv else 170.0)
		if "contact" in from:
			from.contact = false
		if "_did_hit" in from:
			from._did_hit = true


func debug_swing(sw_name: String, item_id := "alp_kilici") -> void:
	## Savuruş laboratuvarı (--savurus): tek bir savuruşu zorla başlatır.
	var it := slot("melee")
	if it.get("id", "") != item_id:
		Game.run["slots"]["melee"] = ItemGen.roll(item_id, 1, "demir", 0)
		it = slot("melee")
	var sw: Dictionary = swing_def(sw_name)
	atk = {"step": 0, "c": {"s": sw_name, "mult": 1.0, "kb": 100.0}, "sw": sw, "phase": "wind", "t": 0.0,
		"dur": 1.0, "hit": [], "item": it, "hold": 0.0, "pause": false, "multi_i": 0}
	atk["ph"] = _phase_times(it, atk["c"], sw, false, 1.0)
	atk["dur"] = float(atk["ph"][0]) + float(atk["ph"][1]) + float(atk["ph"][2]) + float(atk["ph"][3])


func _atk_act() -> String:
	## Süren yakın saldırının tuşu (iki yakın silahta hangisiyle başladıysa)
	return mel_act if mel_act != "" else "saldiri1"


func _ease(u: float, mode: int) -> float:
	match mode:
		1:
			# hızlanarak (v18: kübik yerine kare): süpürme 2-3 kare sürdüğünden ara kare yayın ortasına düşsün
			# (kübikte ara kare hâlâ hazırlıkta görünüyor, bıçak tek karede ışınlanıyordu)
			return u * u
		2:
			return 1.0 - pow(1.0 - u, 3.0)  # yavaşlayarak: takip, ağırlık
	return u * u * (3.0 - 2.0 * u)


func _unwrap_from(p: Array, sw: Dictionary) -> Array:
	## Önceki savuruşun son pozu: açılar (üst kol, bilek) yeni savuruşun ilk hedef anahtarına en kısa yoldan dönsün
	## (çark 6,9 rad'da bitti diye kol geriye tam tur sarılmasın)
	var keys: Array = sw["keys"]
	var tgt: Array = keys[mini(1, keys.size() - 1)]
	var out := p.duplicate()
	out[0] = float(tgt[1]) + wrapf(float(p[0]) - float(tgt[1]), -PI, PI)
	out[2] = float(tgt[3]) + wrapf(float(p[2]) - float(tgt[3]), -PI, PI)
	return out


func _atk_pose(k: float) -> Array:
	## Süren saldırının pozu: zincirde ilk bölüm (dinlenme → hazırlık) dinlenme pozu yerine önceki savuruşun
	## takip pozundan başlar; kol bir vuruştan ötekine kesintisiz akar.
	## v23: dönen poz 8 öğeli: [a1, a2, w, k_derinlik, ext, phi, r, roll] (son üçü savuruş düzlemi, PLANES).
	var sw: Dictionary = atk["sw"]
	var out: Array
	var keys: Array = sw["keys"]
	var k1t := float((keys[1] as Array)[0])
	if atk.has("from") and k < k1t:
		var k1: Array = keys[1]
		var fp: Array = atk["from"]
		var u := _ease(clampf(k / maxf(0.0001, k1t), 0.0, 1.0), 2)
		out = []
		for j in range(1, 6):
			out.append(lerpf(float(fp[j - 1]), float(k1[j]), u))
	else:
		out = _swing_pose(sw, k)
	out.append_array(_plane_at(k))
	return out


func _plane_at(k: float) -> Array:
	## v23 savuruş düzlemi [phi (rad), r, roll (rad)] k anında: PLANES anahtarları + sınıf çarpanı + savuruş başına sapma.
	## Hazırlığın ilk anahtarına dek önceki düzlemden (zincir) ya da ekran düzleminden geçer; toparlanmada ekrana döner.
	var cs := String(atk.get("c", {}).get("s", ""))
	var pd: Dictionary = atk["plane"] if atk.has("plane") else plane_def(cs)   # v27: sanat kendi düzlemini taşır
	if pd.is_empty():
		return [0.0, 1.0, 0.0]
	if not atk.has("pj"):
		var cm: Array = CLASS_PLANE.get(_tempo_class(atk.get("item", {})), [0.0, 1.0])
		atk["pj"] = [deg_to_rad(float(cm[0]) + _plane_rng.randf_range(-1.0, 1.0) * float(PLANE_JIT[0])),
			float(cm[1]), _plane_rng.randf_range(-1.0, 1.0) * float(PLANE_JIT[1])]
	var pj: Array = atk["pj"]
	var pk: Array = pd["p"]
	var e: Array = pk[pk.size() - 1]
	var phi := float(e[1])
	var r := float(e[2])
	var roll := float(e[3])
	if k <= float((pk[0] as Array)[0]):
		phi = float(pk[0][1])
		r = float(pk[0][2])
		roll = float(pk[0][3])
	else:
		for i in range(pk.size() - 1):
			var a: Array = pk[i]
			var b: Array = pk[i + 1]
			if k <= float(b[0]):
				var u := smoothstep(float(a[0]), float(b[0]), k)
				phi = lerpf(float(a[1]), float(b[1]), u)
				r = lerpf(float(a[2]), float(b[2]), u)
				roll = lerpf(float(a[3]), float(b[3]), u)
				break
	var apl: Array = atk.get("art", {}).get("pl", [])   # v27: zincir adımına özgü düzlem farkı (SanatAnim.SILAH "pl")
	if apl.size() >= 3:
		phi += float(apl[0])
		r *= float(apl[1])
		roll += float(apl[2])
	phi = deg_to_rad(phi) + float(pj[0])
	r = clampf(r * float(pj[1]) + float(pj[2]), 0.15, 1.0)
	roll = deg_to_rad(roll)
	var sw: Dictionary = atk["sw"]
	var keys: Array = sw["keys"]
	var k1t := float((keys[1] as Array)[0])
	if k < k1t:
		# hazırlık: önceki düzlemden (ya da ekran düzleminden) bu savuruşunkine
		var u := _ease(clampf(k / maxf(0.0001, k1t), 0.0, 1.0), 2)
		var fp: Array = atk.get("from", [])
		var f_phi := phi
		var f_r := 1.0
		var f_roll := 0.0
		if fp.size() >= 8:
			f_phi = float(fp[5])
			f_r = float(fp[6])
			f_roll = float(fp[7])
		# eksen pi'ye göre periyodik: en kısa yoldan
		f_phi = phi + wrapf(f_phi - phi, -PI * 0.5, PI * 0.5)
		phi = lerpf(f_phi, phi, u)
		r = lerpf(f_r, r, u)
		roll = lerpf(f_roll, roll, u)
	var h1 := float(sw["hit"][1])
	if k > h1:
		# toparlanma: dinlenme pozuyla birlikte ekran düzlemine
		var u2 := smoothstep(h1, 1.0, k)
		r = lerpf(r, 1.0, u2)
		roll = lerpf(roll, 0.0, u2)
	return [phi, r, roll]


static func _plane_proj(v: Vector2, phi: float, r: float) -> Vector2:
	## Düzlem içi vektörün (x ileri, y aşağı; yöne çevrilmemiş) ekrana dik izdüşümü: büyük eksen (phi) korunur, ona dik
	## bileşen r oranında kısalır.
	var M := Vector2(sin(phi), cos(phi))
	var N := Vector2(cos(phi), -sin(phi))
	return M * v.dot(M) + N * (v.dot(N) * r)


func _plane_depth(pose: Array) -> float:
	## v23: bıçağın derinliği (-1 arka .. 1 kameraya doğru): düzlemin "zf" yarısı kameraya bakar.
	if pose.size() < 8 or atk.is_empty():
		return 0.0
	var r := float(pose[6])
	if r >= 0.999:
		return 0.0
	var pd: Dictionary = atk["plane"] if atk.has("plane") else plane_def(String(atk["c"].get("s", "")))
	var phi := float(pose[5])
	var th := float(pose[0]) + float(pose[1]) + float(pose[2])
	var N := Vector2(cos(phi), -sin(phi))
	var zf := deg_to_rad(float(pd.get("zf", 0.0)))
	var sgn := signf(Vector2(sin(zf), cos(zf)).dot(N))
	if sgn == 0.0:
		sgn = 1.0
	return Vector2(sin(th), cos(th)).dot(N) * sgn * sqrt(maxf(0.0, 1.0 - r * r))


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


## ------------------------------------------------------------------ v28 GERÇEK GÖVDE ANİMASYONLARI
## Gövde karesi artık savuruşun EVRELERİNE göre seçilir (tools/artgen/bengu_govde.py): k zamanı [0, hit0, ck, hit1, 1]
## gövdenin kendi zamanına [0, W, C, H, 1] (json "mk") parça parça eşlenir; gösterilen kare, başlangıç anı ("ts") bu
## zamanı geçmemiş son kare. Temas karesi tam isabet anında açılır, derin hazırlık karesi tutuşta bekler; savuruşun
## süreleri / isabet anları / vuruş kutuları değişmez. "ts"si olmayan (eski) satırlarda eski eşit aralıklı seçim.
## Aileye özgü gövde dili: önce aile + savuruş (GOVDE_AILE), sonra savuruş (GOVDE_SW), yoksa savuruşun "body"si.
const GOVDE_SW := {
	"iai": "atk_iai", "yk_iai": "atk_iai", "pole_thrust": "atk_m_thrust", "pole_rise": "atk_m_rise",
	"pole_sweep": "atk_u_sweep", "reap": "atk_u_reap", "whip_side": "atk_w_side", "kistin_dolama": "atk_w_side",
	"flurry": "atk_h_flurry", "albasti_oyma": "atk_h_flurry", "dual_r": "atk_dual_r", "uppercut_2h": "atk_a_lift",
	"ground_drag": "atk_a_lift", "cevgen_vurus": "atk_a_lift", "kistin_tepe": "atk_a_chop", "axe_hook": "atk_a_chop",
	"step_down": "atk_k_step",
}
const GOVDE_AILE := {
	"hancer": {"down": "atk_dual", "diag_down": "atk_dual", "rake": "atk_dual", "reverse_grip": "atk_h_spin",
		"twirl": "atk_h_spin", "cross_dash": "atk_lunge", "thrust": "atk_h_flurry"},
	"duello": {"reverse_grip": "atk_iai", "twirl": "atk_h_spin"},
	"kilic": {"reverse_grip": "atk_iai"},
	"agir": {"down": "atk_a_chop", "diag_down": "atk_a_chop", "dual_l": "atk_a_chop", "dual_r": "atk_a_lift",
		"horiz": "atk_u_sweep", "kistin_yan": "atk_u_sweep", "step_down": "atk_overhead_2h"},
	"dev": {"down": "atk_a_chop", "diag_down": "atk_a_chop", "horiz": "atk_u_sweep", "step_down": "atk_overhead_2h"},
	"mizrak": {"thrust": "atk_m_thrust", "horiz": "atk_u_sweep"},
	"uzun": {"horiz": "atk_u_sweep", "twirl": "atk_spin", "thrust": "atk_m_thrust"},
	"kirbac": {"spin": "atk_w_whirl", "horiz": "atk_w_side"},
}


func _govde_sec(a: Dictionary) -> String:
	var sw: Dictionary = a["sw"]
	var body := String(sw.get("body", "atk_horiz"))
	var sn := String((a.get("c", {}) as Dictionary).get("s", ""))
	var fam := _tempo_class(a.get("item", {}))
	var t: Dictionary = GOVDE_AILE.get(fam, {})
	var b2 := String(t.get(sn, GOVDE_SW.get(sn, body)))
	return b2 if anim.has_anim(b2) else body


static func _body_tau(k: float, sw: Dictionary, mk: Array) -> float:
	var h0 := float(sw["hit"][0])
	var h1 := float(sw["hit"][1])
	var ck := clampf(_contact_k(sw), h0, h1)
	var a := [0.0, h0, ck, h1, 1.0]
	var m := [0.0, float(mk[0]), float(mk[1]), float(mk[2]), 1.0]
	for i in 4:
		if k < float(a[i + 1]) or i == 3:
			var span := float(a[i + 1]) - float(a[i])
			var u := 0.0 if span <= 0.0001 else clampf((k - float(a[i])) / span, 0.0, 1.0)
			return lerpf(float(m[i]), float(m[i + 1]), u)
	return 1.0


func _body_frame(body: String, sw: Dictionary, k: float) -> int:
	var n := anim.frame_count(body)
	var a: Dictionary = anim.meta["anims"].get(body, {})
	if not a.has("ts"):
		return clampi(int(k * n), 0, n - 1)
	var tau := _body_tau(k, sw, a["mk"])
	var ts: Array = a["ts"]
	var f := 0
	for i in ts.size():
		if float(ts[i]) <= tau + 0.0001:
			f = i
	return f


func _show_body(k: float) -> void:
	if not atk.has("body"):
		atk["body"] = _govde_sec(atk)
	var body: String = atk["body"]
	var f := _body_frame(body, atk["sw"], k)
	# v29: zincirde (önceki savuruşun toparlanmasından) dinlenme karesi (0) atlanır: gövde öne yatık toparlanmadan dik
	# dinlenmeye sıçrayıp yeniden kurulmaz, doğrudan kalkış / kurulma karesine geçer
	if f == 0 and atk.get("chain", false) and anim.frame_count(body) >= 10:
		f = 1
	anim.show_frame(body, f)


func _ts_frame(an: String, tau: float) -> int:
	## v28 uzak silah gövdeleri (yay / fırlatma / büyü): karenin başlangıç anına göre seçim; eski satırda -1
	var a: Dictionary = anim.meta["anims"].get(an, {})
	if not a.has("ts"):
		return -1
	var ts: Array = a["ts"]
	var f := 0
	for i in ts.size():
		if float(ts[i]) <= tau + 0.0001:
			f = i
	return f


func _update_attack(delta: float) -> void:
	var c: Dictionary = atk["c"]
	var sw: Dictionary = atk["sw"]
	var it: Dictionary = atk["item"]
	var hit0: float = float(sw["hit"][0])
	var hit1: float = float(sw["hit"][1])
	if not atk.has("ph"):
		# eski yol (şimşek hamlesi, laboratuvar): evreler dur'un oranları
		var D0 := float(atk["dur"])
		var ck0 := _contact_k(sw)
		atk["ph"] = [hit0 * D0, (ck0 - hit0) * D0, (hit1 - ck0) * D0, (1.0 - hit1) * D0, 0.03 + 0.045 * _weight(it)]
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
				_show_body(k0)
				_update_weapon_visual()
				_melee_hits()
				_sample_trail(it, c, k0)
				return
			atk["plunged"] = true
			_plunge_land(it)
	# Hazırlık bitince tuş hâlâ basılıysa bekle; bırakılırsa normal vuruş, basış anından FLOW.heavy_hold geçerse ağır
	# saldırı (v17: süre basıştan sayılır — eski: hazırlık sonundan +0,16 sn). Hafif silahlar (hançer, düellocu,
	# kırbaç) hiç beklemez: hafif vuruş çıkar, tuş basılı kalırsa ağır saldırı toparlanmadan açılır.
	var nowait := _weight(it) <= float(FLOW["heavy_nowait_w"])
	# v18: yalnızca bu savuruşu başlatan basış hâlâ süren basılı tutuşsa bekle (seri basışta her yeni basış hazırlığı
	# geri sarıyordu: gürz zinciri takılıyordu)
	if _mel_down_t < 0.0:
		atk["held"] = false
	if atk["phase"] == "wind" and not nowait and _can_hold_heavy(c) and _mel_down_t >= 0.0 and atk.get("held", false):
		var wind_end: float = atk["dur"] * _hold_k(sw)
		if atk["t"] <= wind_end + 0.0001 and atk["t"] + delta * float(atk["dur"]) * hit0 / maxf(0.001, float(atk["ph"][0])) >= wind_end:
			if _mel_down_t >= float(FLOW["heavy_hold"]):
				_begin_heavy(it)
				return
			atk["t"] = wind_end
			atk["hold_wait"] = float(atk.get("hold_wait", 0.0)) + delta
			_show_body(atk["t"] / atk["dur"])
			_update_weapon_visual()
			return
	# gürz şarjı: hazırlıkta tuş basılıysa bekle, güç birikir
	if c.get("charge", false) and atk["phase"] == "wind" and atk.get("held", false) and Input.is_action_pressed(_atk_act()) and atk["hold"] < 0.7:
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
		_atk_advance(delta)
	# v14 hazırlık tutuşu: hazırlığın son anında kısa bir duraklama (hafif 2 kare, ağır 4 kare); gövde toplanır,
	# silah bir tık daha geri çekilir. Vuruş öngörülebilir olur, sonraki hızlanma daha sert okunur.
	if atk["phase"] == "wind" and not atk.get("heavy", false) and not atk.has("dash_px"):
		var kk: float = atk["t"] / atk["dur"]
		# v18: tutuş süresi TEMPO'dan (hançer / kılıç zincirinde hiç yok; ağır silahta 1-3 kare)
		var hold_t := float(atk["ph"][4])
		var hk := _hold_k(sw)
		if hold_t > 0.0 and kk >= hk and float(atk.get("antic", 0.0)) < hold_t and kk - hk < 0.12:
			if not atk.has("antic"):
				vis_scale = Vector2(0.94, 1.05)
				if _weight(it) >= 0.75 and Ses.has("savur_hazirlik"):
					Ses.play("savur_hazirlik", -14.0, 1.0, 0.08, 0.0, center())
			atk["antic"] = float(atk.get("antic", 0.0)) + delta
			atk["t"] = atk["dur"] * hk
	var k: float = atk["t"] / atk["dur"]
	if crouch_hold and crouched and anim.has_anim("crouch_atk"):
		anim.show_frame("crouch_atk", 0)
	else:
		_show_body(k)
	if k < hit0:
		atk["phase"] = "wind"
		_wind_fx(it, sw, k)
	elif k < hit1:
		if atk["phase"] == "wind":
			atk["phase"] = "act"
			if atk.get("sa_wind", false):
				atk["super_armor"] = false
			if c.get("last", false) and not atk.get("pause", false):
				# v35 bitiriş beklentisi: hazırlığın doruğunda bıçak ucunda tek karelik iğne parıltısı (sınıf vurgusu)
				var pp := _pose_points(_atk_pose(k))
				KesikFX.parilti(arm_root.to_global((pp[2] as Vector2) + (pp[3] as Vector2) * _reach(it)),
					(KesikFX.sinif_of(_tempo_class(it))["vurgu"] as Color).lerp(Color(1.4, 1.3, 1.1), 0.5))
			_on_strike_start()
			if atk.is_empty():
				return
		if atk.has("dash_px"):
			# v28: ilk isabetin "past" px ötesinde durur (pencerenin kalanı yerinde: arkadaki yakın düşman yine değer)
			if atk.has("dash_stop") and float(facing) * (global_position.x - float(atk["dash_stop"])) >= 0.0:
				velocity.x = facing * float(YK_DASH["end_v"])
			else:
				velocity.x = facing * 1100.0
			velocity.y = 0.0
			if Engine.get_physics_frames() % 2 == 0:
				FX.ghost(anim.base, Color(0.6, 0.85, 1.0, 0.5), 0.18)
				FX.sparks(global_position + Vector2(-facing * 6, -4), Vector2(-facing, -0.6), Color(0.7, 0.9, 1.0), 2, 120.0)
		if atk.has("flash_left"):
			_yk_flash_tick(delta)
		# v15 delip geçme: vuruş penceresi boyunca sabit hızla düşmanın içinden öteye (ikiz bıçak / böri)
		if atk.get("through", false):
			velocity.x = facing * 780.0
			velocity.y = minf(velocity.y, 0.0)
			if Engine.get_physics_frames() % 2 == 0:
				FX.ghost(anim.base, Color(0.85, 0.75, 1.0, 0.45), 0.16)
		# v15 çark tutuşu (pala): tuş basılıyken vuruş penceresi başa sarar; en çok 1,2 sn, her turda iki yan yeniden vurulur
		# v22: yalnızca savuruşu başlatan basış hâlâ basılıysa (ezerken yeni bir basış çarkı kendiliğinden uzatmasın)
		if c.get("spin_hold", false) and atk.get("held", false) and Input.is_action_pressed(_atk_act()) and float(atk.get("spin_t", 0.0)) < 1.2 and k >= hit1 - 0.03:
			var loop_k := hit0 + 0.04
			slog("cark_uzatma", String(c["s"]), not atk.get("held", false))
			atk["spin_t"] = float(atk.get("spin_t", 0.0)) + (hit1 - loop_k) / maxf(0.01, hit1 - hit0) * (float(atk["ph"][1]) + float(atk["ph"][2]))
			atk["t"] = atk["dur"] * loop_k
			k = loop_k
			atk["hit"] = []
			atk["multi_i"] = 0
			_trail_prev = []
			vis_scale = Vector2(1.08, 0.94)
			FX.ghost(anim.base, Color(1.0, 0.7, 0.6, 0.35), 0.18)
			Ses.play("savur_" + String(WSND.get(it.get("id", ""), "kilic")), -8.0, 1.05 + 0.1 * float(atk["spin_t"]), 0.04)
			if is_on_floor():
				velocity.x = facing * 40.0
		# seri saplama: her saplamada vuruş listesi yenilenir
		if sw.has("multi"):
			var mi: int = atk["multi_i"]
			var marks: Array = sw["multi"]
			if mi < marks.size() and k >= float(marks[mi]) - 0.04:
				# v26: delip geçen savuruşta (çapraz atılış) temas ile ilk işaret aynı geçiştir (ItemGen.zincir_vurus da
				# öyle sayar); daha uzun evrelerle ikisi ayrı karelere düşünce düşmana fazladan bir vuruş değiyordu
				if not (mi == 0 and c.get("through", false) and _contact_k(sw) < float(marks[0]) - 0.04):
					atk["hit"] = []
				atk["multi_i"] = mi + 1
				if c.get("xspark", false):
					_yk_release()   # v25 Şimşek Çaprazı: her geçiş kendi parlak yayı
				vis_scale = Vector2(1.08, 0.94)
				velocity.x = facing * 60.0
				if sw["body"] == "atk_thrust":
					_thrust_streak(it)
		_update_weapon_visual()
		# v18: isabet bıçağın düşmana vardığı karede başlar (ck): duraklama bıçak hedefin üstündeyken donar
		if k >= _contact_k(sw):
			_melee_hits()
		if not c.get("flash", false):   # v25 Şimşek Çekişi: iz yerine kesik çizgisi (atılırken bıçağın izi yığılıyordu)
			_sample_trail(it, c, k)
		if String(c["s"]) in ["yk_iai", "yk_cross"]:
			_yk_track(it, k)
		_slam_contact(it, k, hit1)
	elif k < 1.0:
		if atk["phase"] == "act":
			_end_trail()
			_yk_release()
			SanatAnim.takip(self, it, c)   # v27: takip vurgusu / bitiriş hat fırçası
			# aşma (overshoot): kol vuruş yönünde bir tık daha gider, sönümlü salınımla oturur
			_over_amp = clampf(_over_dir * (0.10 + 0.10 * _weight(it)), -0.22, 0.22)
			_over_t = 0.0
			if atk.get("through", false):
				velocity.x *= 0.25
				FX.dust(global_position, Vector2(-facing, -0.4), 5, 0.28)
			if atk.has("dash_px"):   # v28: hamle bitti, kayma yok
				velocity.x = facing * float(YK_DASH["end_v"])
				FX.dust(global_position, Vector2(-facing, -0.4), 4, 0.24)
		atk["phase"] = "rec"
		_slam_contact(it, k, hit1)
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
	var vu := Vector2(sin(a1) * kd, cos(a1)) * float(arm_meta.get("upper_len", 8.5))
	var vf := Vector2(sin(a1 + a2) * kd, cos(a1 + a2)) * float(arm_meta.get("fore_len", 8.0)) * float(pose[4])
	var vb := Vector2(sin(a1 + a2 + w) * kd, cos(a1 + a2 + w))
	# v23: savuruş düzleminin izdüşümü (PLANES): bıçak tam, kol ARM_PLANE oranında kısalır
	if pose.size() >= 8 and float(pose[6]) < 0.999:
		var phi := float(pose[5])
		var r := float(pose[6])
		var ra := lerpf(1.0, r, ARM_PLANE)
		vu = _plane_proj(vu, phi, ra)
		vf = _plane_proj(vf, phi, ra)
		vb = _plane_proj(vb, phi, r)
	var fx := Vector2(float(facing), 1.0)
	var e: Vector2 = sh + vu * fx
	var h: Vector2 = e + vf * fx
	var bd := vb * fx
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
		_trail.life = 0.08 + 0.06 * _weight(it)
		if _trail is InkTrail:  # stil v2: silah sınıfına / savuruşa göre mürekkep fırçası tasarımı
			(_trail as InkTrail).setup(it, atk, _weight(it))
			Silah27.trail_style(_trail, it, atk)   # v27 yeni silahlar: sınıf ve palet
			# v35: sınıf iz eni (kısa bıçaklı hançer / mızrak izi okunur) + zincir bitirişinde daha gür fırça
			var tr35 := _trail as InkTrail
			var ik := float(V35["iz_sinif"].get(_tempo_class(it), 1.0))
			if c.get("last", false) and not atk.get("pause", false):
				ik *= float(V35["fin_iz"])
				tr35.flick_n += 2
			tr35.w_frac *= ik
			tr35.path_w *= ik
			if String(c["s"]) in UPSWEEP_THIN:
				# v25: ağır silahın yukarı süpürmesi dar hilal (ağır fırçanın geniş tabanı yükselen yayda düz kenarlı
				# "levha" / alev duvarı çiziyordu)
				(_trail as InkTrail).w_frac *= float(UPSWEEP_THIN[String(c["s"])])
	var R := _reach(it)
	var prev_k: float = float(_trail_prev[0]) if _trail_prev.size() > 0 else k
	# v18: ara örnek sayısı karede süpürülen açıya göre (hızlı savuruşta bir karede 2-3 rad geçilir; sabit 4 örnek
	# hilali çokgenleştiriyordu): ~0,06 rad'da bir örnek, 4-28 arası
	var p0 := _atk_pose(prev_k)
	var p1 := _atk_pose(k)
	var sweep := absf((float(p1[0]) + float(p1[1]) + float(p1[2])) - (float(p0[0]) + float(p0[1]) + float(p0[2]))) + absf(float(p1[0]) - float(p0[0])) * 0.5
	# v23: izdüşen uç yolunun ekrandaki uzunluğu da sayılır (yassı elipste açı küçük ama yol uzun olabilir)
	var q0 := _pose_points(p0)
	var q1 := _pose_points(p1)
	var tip_d := ((q1[2] as Vector2) + (q1[3] as Vector2) * R).distance_to((q0[2] as Vector2) + (q0[3] as Vector2) * R)
	var steps := clampi(maxi(int(ceil(sweep / 0.06)), int(ceil(tip_d / 2.0))), 4, 28)
	for i in range(1, steps + 1):
		var kk := lerpf(prev_k, k, float(i) / steps)
		var pts := _pose_points(_atk_pose(kk))
		var hand: Vector2 = pts[2]
		var bd: Vector2 = _ground_clamp(pts[2], pts[3], R)
		var base := arm_root.to_global(hand + bd * R * 0.35)
		var tip := arm_root.to_global(hand + bd * R)
		_trail.add(base, tip)
	_trail_prev = [k]


func _ground_clamp(h: Vector2, bd: Vector2, L: float) -> Vector2:
	## Yerdeyken silah başı (ve izi) zemine gömülmesin: uç zemin çizgisinin altına inerse bıçak açısı
	## zemine yaslanır; çekiç/kılıç yere çarpınca orada durur, toprağın içinde dönmeye devam etmez.
	if not is_on_floor() or bd.length() < 0.01 or L <= 0.0:
		return bd
	var gl: float = arm_root.to_local(Vector2(global_position.x, global_position.y - 2.0)).y
	var bdir := bd.normalized()
	var len_b := bd.length()
	if h.y >= gl or h.y + bdir.y * L * len_b <= gl:
		return bd
	var sy := clampf((gl - h.y) / (L * len_b), -1.0, 1.0)
	var sx := sqrt(maxf(0.0, 1.0 - sy * sy)) * (signf(bdir.x) if absf(bdir.x) > 0.001 else float(facing))
	return Vector2(sx, sy) * len_b


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
	Silah27.pre_strike(self)   # v27: duruş değişimi, Albastı Göçü, Yere Çalma (atk["c"]'yi okur)
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
		if c.get("vault", false):
			# sırık atlayışı: sırık yere saplanır, gövde ileri-yukarı fırlar
			velocity.x = facing * 210.0
			inv_t = maxf(inv_t, 0.25)
			FX.dust(global_position + Vector2(facing * 14, 0), Vector2(-facing, -0.8), 8, 0.3)
			FX.sparks(global_position + Vector2(facing * 16, -2), Vector2(-facing, -0.9), Color(1.0, 0.85, 0.5), 4, 140.0)
			Ses.play("zipla", -8.0, 0.9)
	if atk.get("heavy", false):
		# ağır vuruş: sert kamera, ışık patlaması, tam şarjda halka
		Game.kick(Vector2(facing, 0.3), 5.0 + 4.0 * hold)
		FX.flash_light(center(), weapon_color(it), 150.0 + 100.0 * hold, 1.5, 0.2)
		if hold > 0.6 and not (c.get("slam", false) or c.get("shock", false)):
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
	if c.get("flash", false):
		# v25 Şimşek Çekişi: yerde göz açıp kapayıncaya dek ileri (YK.flash_px); düşmanın içinden geçer, kısa dokunulmazlık
		atk["flash_left"] = float(YK["flash_t"])
		velocity.x = float(facing) * float(YK["flash_px"]) / float(YK["flash_t"])
		velocity.y = minf(velocity.y, 0.0)
		inv_t = maxf(inv_t, float(YK["flash_t"]) + 0.12)
		_yk_flash_fx(it)
	elif c.get("backstep", false):
		# v15 geri çekilme kesiği: gövde geriye çekilir, bıçak öne geçer (çekilirken kesik); kısa dokunulmazlık
		# v25: yerde kalır (eski: -150 px/sn hoplama; "kombo havaya zıplatıyor"): ayaklar yerde geriye kayar
		velocity.x = -facing * 175.0
		if not is_on_floor():
			velocity.y = minf(velocity.y, -60.0)
		inv_t = maxf(inv_t, 0.16)
		air_hang = 0.0
		FX.dust(global_position, Vector2(facing, -0.3), 6, 0.26)
		FX.ghost(anim.base, Color(0.9, 0.95, 1.0, 0.4), 0.2)
	elif c.get("through", false):
		# v15 delip geçme: ileri fırla, düşmanın içinden öteye; süresince dokunulmaz
		atk["through"] = true
		velocity.x = facing * 780.0
		velocity.y = 0.0
		inv_t = maxf(inv_t, 0.3)
		for i in 3:
			FX.ghost(anim.base, Color(0.85, 0.75, 1.0, 0.4), 0.2)
		FX.dust(global_position, Vector2(-facing, -0.4), 4, 0.24)
	# silahın ağırlığı gövdeyi öne taşır
	elif is_on_floor():
		# v17: mesafe tabanlı adım + hedef yardımı (_strike_step); koşudan gelen hız korunur
		var stv := _strike_step(it, c, heavy_w)
		velocity.x = float(facing) * minf(maxf(stv, velocity.x * float(facing)), float(atk.get("step_cap", INF)))
	elif c.get("slam", false) or c.get("shock", false):
		velocity.y = maxf(velocity.y, 420.0)  # havada ağır vuruş: aşağı çakılır
	if atk.has("dash"):
		inv_t = maxf(inv_t, 0.18)
		for i in 3:
			FX.ghost(anim.base, Color(1.0, 0.9, 0.6, 0.4), 0.2)
	if atk.get("pause", false):
		Game.slowmo(0.55, 0.1)
		FX.flash_light(center(), Color(1.0, 0.85, 0.5), 140.0, 1.4, 0.2)
	if c["s"] in ["thrust", "lunge", "lunge_long", "pole_thrust_lo"]:
		_thrust_streak(it)
	atk["strike_at"] = Game.clock()   # v19 çarpışma penceresi buradan
	if atk.has("exec_t"):
		_exec_strike()
	if c.has("pull"):
		# çekiş savuruşu: uçtan içeri doğru akan parlak çizgi (tırpan / kanca)
		var R0 := _reach(it)
		var yy := center().y - 4.0
		FX.streak(Vector2(global_position.x + facing * (R0 + 30.0), yy), Vector2(global_position.x + facing * 10.0, yy), weapon_color(it), 0.14)
	if c.get("wave", false):
		_spirit_wave(it)
	if it.get("mech_id", "") == "kor_izi" and (c.get("slam", false) or c.get("shock", false)) and is_on_floor():
		level.fire_pool(global_position + Vector2(facing * 26, 0), float(it.get("mech_v", 60.0)) * (0.6 + 0.8 * hold + (0.6 if atk.get("pause", false) else 0.0)), 3.0, float(it["dmg"]) * 0.25)
	if c.get("venom", false):
		for k in 3:
			_spirit_wave(it, Color(0.55, 1.0, 0.45), {"poison": 2, "kb": 40.0}, -40.0 + 40.0 * k, 260.0)
	if c.get("launch", false):
		FX.dust(global_position + Vector2(facing * 10, 0), Vector2.UP, 4, 0.22)
	if c.get("shock", false) or c.get("slam", false):
		# v16: yer çarpmasının görseli / sarsıntısı / sesi vuruşun başında değil, silahın başı yere değdiği
		# karede (_slam_contact). Havadaysa (bitirişin sıçrayışı, havada çakma) inişte.
		atk["gslam"] = true
	elif InkDust.ground_swing(it, c):
		# v20: çakma bayrağı olmayan ama başı yere inen ağır / uzun sap savuruşu: değdiği karede hafif mürekkep tozu
		atk["gslam"] = true
		atk["gslam_lite"] = true
	if (c.get("shock", false) or c.get("slam", false)) and is_on_floor():
		var w := float(it.get("mech_v", 50.0)) * (1.0 + hold / 0.7 * 0.8) if c.get("shock", false) else 40.0
		if atk.get("pause", false):
			w *= 1.6
		if c.get("shock", false):
			for e in get_tree().get_nodes_in_group("dusman"):
				if not is_instance_valid(e) or e.dead:
					continue
				var ec: Vector2 = e.center()
				if absf(ec.x - (global_position.x + facing * 22)) < w * 0.5 + 16 and absf(e.global_position.y - global_position.y) < 30:
					_deal(e, float(it["dmg"]) * 0.5 * (1.0 + hold), it, {"stun": 1.0 + hold, "kb": 160.0})


func _slam_contact(it: Dictionary, k: float, hit1: float) -> void:
	## v16 yer çarpması anı: silahın başı zemine indiği kare (en geç vuruş penceresinin sonu). Havadaysa inişi bekler;
	## savuruş bitene dek inmezse efekt yok. Görsel FX.ground_slam: ağırlık, şarj ve bitirişle büyür.
	if not atk.get("gslam", false) or not is_on_floor() or level == null:
		return
	var R := _reach(it)
	var tip := arm_root.to_global(_hand_local + _blade_local * R)
	var gx := clampf(tip.x, global_position.x - R - 4.0, global_position.x + R + 4.0)
	var gy: float = level.ground_y_below(Vector2(gx, global_position.y - 20.0), 52.0)
	if gy < 0.0:
		# baş boşluğun üstünde: ayağın altındaki zemine, öne yakın
		gx = global_position.x + facing * 8.0
		gy = global_position.y
	var lite: bool = atk.get("gslam_lite", false)
	if tip.y < gy - 3.0:
		if k < hit1 - 0.02:
			return
		if lite:
			atk["gslam"] = false   # v20 hafif değme: baş yere inmediyse toz yok
			return
		# baş hiç inmedi (pencere bitti / havadan iniş): öndeki zemine
		gx = global_position.x + facing * clampf(absf(tip.x - global_position.x), 8.0, R)
		var gy2: float = level.ground_y_below(Vector2(gx, global_position.y - 20.0), 52.0)
		gy = gy2 if gy2 >= 0.0 else global_position.y
	atk["gslam"] = false
	var hold: float = atk.get("hold", 0.0)
	var pause: bool = atk.get("pause", false)
	var c: Dictionary = atk["c"]
	var power := 0.5 + 0.55 * _weight(it) + 0.5 * hold / 0.7
	if pause:
		power += 0.3
	if c.get("shock", false):
		power += 0.08
	var id := String(it.get("id", ""))
	var hot: bool = id == "kor_cekici" or it.get("mech_id", "") == "kor_izi"
	FX.ground_slam(Vector2(roundf(gx), gy), facing, clampf(power, 0.6, 1.9) * (0.6 if lite else 1.0), weapon_color(it), id != "kayin_asasi", hot, not lite)
	SanatAnim.catlak(self, it, Vector2(roundf(gx), gy), power, lite)   # v27: mürekkep çatlakları
	Ses.play("sarsinti_buyuk" if (hold >= 0.6 or pause) else "sarsinti", -2.0 + 3.0 * hold - (9.0 if lite else 0.0))
	vis_scale = Vector2(1.1, 0.92)


func _can_hold_heavy(c: Dictionary) -> bool:
	return not atk.get("pause", false) and not atk.get("heavy", false) and not atk.has("dash_px") \
		and not c.get("axe", false) and not c.get("charge", false) and not c.get("special", false) and not c.get("spin_hold", false)


func _hold_k(sw: Dictionary) -> float:
	## Hazırlık tutuşu / şarj pozunun zaman noktası: sıçramalı gövdelerde (çakma, aparkat, geri sıçrayış) havadaki
	## kare yerine çömelme karesi tutulsun diye savuruş "hold_k" verebilir; yoksa vuruş penceresinin hemen öncesi.
	return float(sw.get("hold_k", float(sw["hit"][0]) - 0.03))


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
	FX.shockwave(global_position + Vector2(0, -6), r * 1.3, 0.8)
	FX.dust(global_position, Vector2.UP, 10, 0.36)
	InkDust.burst(global_position, facing, 1.1 * power)   # v20: dalış inişinde mürekkep toz bulutu
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
	var h27 := Silah27.heavy(it)
	if not h27.is_empty():
		return h27
	if HEAVIES.has(it.get("id", "")):
		return HEAVIES[it["id"]]
	return HEAVIES.get(it.get("kind", "slash"), HEAVIES["slash"])


func _begin_heavy(it: Dictionary) -> void:
	## Ağır saldırı: hazırlık pozunda şarj; bırakınca (ya da dolup 0.5 sn geçince) silahın özgün ağır vuruşu
	var h := _heavy_for(it)
	var sw: Dictionary = swing_def(h["s"])
	sw = SanatAnim.swing(it, h, sw, 0, true)   # v27
	var spd_mult := 1.0   # v20: "hiz" niteliği artık saldırı hızı statında (hiz_bonus)
	if it["flaw"] == "agir":
		spd_mult *= 0.88
	var ph := _phase_times(it, h, sw, false, spd_mult, "heavy")
	var total := float(ph[0]) + float(ph[1]) + float(ph[2]) + float(ph[3])
	var from_pose: Array = _last_pose.duplicate() if _last_pose_ok else []
	atk = {"step": atk.get("step", 0), "c": h, "sw": sw, "phase": "charge", "t": 0.0, "dur": total, "hit": [], "item": it,
		"hold": 0.0, "pause": false, "multi_i": 0, "heavy": true, "charge": 0.0, "full_fx": false, "ph": ph}
	if not from_pose.is_empty():
		atk["from"] = _unwrap_from(from_pose, sw)
	atk["art"] = SanatAnim.info(it, h, sw, 0, true)   # v27
	if h.has("dash"):
		atk["dash"] = float(h["dash"])
	atk["super_armor"] = bool(h.get("sa", false))
	combo_step = 0
	melee_buf = 0.0
	slog("agir", String(h["s"]), false, {"hold": _mel_down_t})
	_press_used = true
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
	atk["t"] = atk["dur"] * _hold_k(sw) * clampf(ch / 0.12, 0.0, 1.0)
	_show_body(atk["t"] / atk["dur"])
	_update_weapon_visual()
	var col := weapon_color(it)
	var hand := arm_root.to_global(_hand_local)
	if Engine.get_physics_frames() % 3 == 0:
		var from := hand + Vector2(randf_range(-28, 28), randf_range(-28, 28))
		FX.streak(from, hand, Color(col, 0.6), 0.1)
	if Engine.get_physics_frames() % 5 == 0:
		FX.burst(hand, col, 2, 40, 0.3, 0.14, -80, true)
	if c.get("lightning", false) and FX.root and Engine.get_physics_frames() % (4 if full else 7) == 0:
		# v25 Yıldırım Hamlesi şarjı: kında bekleyen bıçağın boyunca şarjla uzayan çıtırtılı kılcal şimşekler
		var tip := arm_root.to_global(_hand_local + _blade_local * _reach(it))
		var l := LightningFX.new()
		l.a = hand.lerp(tip, randf_range(0.2, 0.9))
		l.b = l.a + Vector2(randf_range(-1.0, 1.0), randf_range(-1.0, 0.3)).normalized() * (6.0 + 14.0 * wob)
		l.col = YK["col"]
		l.branches = 0 if not full else 1
		FX.root.add_child(l)
	vis_scale = Vector2(1.0 + 0.035 * wob * sin(ch * 45.0), 1.0 - 0.035 * wob * sin(ch * 45.0))
	velocity.x = move_toward(velocity.x, 0.0, 1200.0 * delta)
	# v17: şarj ederken yön tuşuyla dönülebilir (vuruş hangi yöne çıkacağı son ana dek seçilir)
	var cdir := Input.get_axis("sol", "sag")
	if cdir != 0.0 and int(signf(cdir)) != facing:
		facing = int(signf(cdir))
		anim.set_facing(facing)
	Ses.loop_pitch("sarj", 0.8 + 0.7 * wob)
	if full and not atk["full_fx"]:
		atk["full_fx"] = true
		Ses.play("sarj_dolu", -2.0)
		anim.set_flash(0.6)
		get_tree().create_timer(0.08).timeout.connect(func() -> void: anim.set_flash(0.0))
		FX.ring(hand, 26, col, 0.3)
		FX.flash_light(hand, col, 110.0, 1.6, 0.2)
		_move_label(String(c.get("name", "AĞIR")), col.lerp(Color.WHITE, 0.3), 9)
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
		atk["t"] = atk["dur"] * minf(_hold_k(sw), hit0 - 0.02)
		for i in 2:
			FX.ghost(anim.base, Color(col, 0.45), 0.2)
		if full:
			Game.slowmo(0.5, 0.08)
		if c.get("slam", false) and is_on_floor():
			# v25: ağır çakma yerde kalır (eski: -300..-420 px/sn sıçrama; havaya zıplatan hamleler kalktı): ön ayağa
			# yüklenen kısa adım ve gövde basıncı
			velocity.x = float(facing) * (50.0 + 70.0 * wob)
			vis_scale = Vector2(1.1, 0.9)


func _wind_fx(it: Dictionary, sw: Dictionary, k: float) -> void:
	## Hazırlık efektleri: yerde sürüklenen kılıç kıvılcım saçar, çekişte kabza parlar, çarklarda iz hazırlıkta başlar.
	var sname: String = atk["c"]["s"]
	match sname:
		"ground_drag":
			if Engine.get_physics_frames() % 2 == 0 and k > 0.12:
				var tip := arm_root.to_global(_hand_local + _blade_local * _reach(it))
				FX.sparks(tip, Vector2(-facing, -0.8), Color(1.0, 0.8, 0.5), 3, 150.0)
				InkDust.drag(Vector2(tip.x, global_position.y), -facing)   # v20: sürüklenen başın ardında mürekkep tozu
		"iai", "yk_iai", "yk_flash":
			if not atk.get("wind_fx", false):
				atk["wind_fx"] = true
				FX.flash_light(arm_root.to_global(_hand_local), weapon_color(it), 60.0, 1.2, 0.12)
			# v25: kında bekleyen bıçağın kabzasında küçük çıtırtı (tutuşun okunduğu an)
			if sname != "iai" and Engine.get_physics_frames() % 3 == 0 and k > float(sw["hit"][0]) - 0.12:
				var hp0 := arm_root.to_global(_hand_local)
				FX.sparks(hp0, Vector2(-facing, -0.6), YK["col"], 1, 70.0)
		"windmill", "helicopter", "spin_2h":
			# v18: iz vuruşun hemen öncesinde başlar (zincirde hazırlık kılıcı yerde sürükler; yerde yassı leke bırakmasın)
			if k > float(sw["hit"][0]) - 0.08:
				_sample_trail(it, atk["c"], k)
		"overhead_2h", "slam_2h", "uppercut_2h", "slam", "step_down":
			if Engine.get_physics_frames() % 4 == 0 and k > 0.15:
				FX.burst(arm_root.to_global(_hand_local), weapon_color(it), 1, 30, 0.25, 0.14, -60, true)
		"sweep_low":
			# bıçak yere yakın: hazırlıkta toz
			if Engine.get_physics_frames() % 3 == 0 and k > 0.14:
				FX.dust(global_position + Vector2(-facing * 8, 0), Vector2(-facing, -0.3), 1, 0.18)
		"lunge_long", "pole_vault":
			if Engine.get_physics_frames() % 3 == 0 and k > 0.14:
				FX.sparks(global_position + Vector2(-facing * 4, -2), Vector2(-facing, -0.4), Color(1.0, 0.9, 0.6), 1, 90.0)


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
		"down", "heavy", "diag_down", "axe_hook", "rake", "windmill":
			b = [-4.0, -54.0, R + 10.0, 0.0]
		"slam":
			b = [-8.0, -56.0, R + 16.0, 4.0]
		"overhead_2h", "slam_2h", "step_down":
			b = [-6.0, -64.0, R + 14.0, 2.0]   # uzun dikey: baş üstünden yere
		"backstep":
			b = [-2.0, -50.0, R + 24.0, -6.0]  # gövde geri gider, kutu öne uzar
		"lunge_long":
			b = [6.0, -46.0, R + 32.0, -14.0]  # uzun yatay şerit
		"spin_2h":
			b = [-(R + 14.0), -60.0, R + 14.0, 2.0]  # iki yan, daire
		"dual_l", "dual_r", "cross_dash":
			b = [-2.0, -46.0, R + 14.0, -10.0]
		"whip_crack", "whip_side":
			b = [6.0, -52.0, R + 34.0, -18.0]  # uzun düz: ucu uzakta şaklar
		"pole_vault":
			b = [-4.0, -66.0, R + 10.0, -4.0]
		"up", "rise", "diag_up", "ground_drag", "uppercut_2h", "pole_rise":
			b = [-2.0, -66.0, R + 8.0, -4.0]
		"horiz", "back", "cross_x", "reverse_grip", "iai", "twirl", "yk_iai", "yk_cross":
			b = [-4.0, -48.0, R + 12.0, -8.0]
		"yk_flash":
			b = [-8.0, -46.0, R + 18.0, -6.0]   # atılırken gövdenin önü ve içi (geçtiği düşman)
		"reap":
			b = [-10.0, -50.0, R + 14.0, -6.0]
		"sweep_low":
			b = [-8.0, -30.0, R + 14.0, 2.0]
		"thrust", "flurry":
			b = [4.0, -42.0, R + 16.0, -18.0]
		"pole_thrust", "stab_heavy":
			b = [4.0, -44.0, R + 26.0, -16.0]
		"pole_thrust_lo":
			b = [4.0, -36.0, R + 26.0, -4.0]   # alçak saplama: diz hizası
		"pole_sweep":
			b = [-8.0, -52.0, R + 20.0, -6.0]
		"lunge":
			b = [-6.0, -46.0, R + 22.0, -6.0]
		"spin", "helicopter":
			b = [-(R + 10.0), -62.0, R + 10.0, 0.0]
		_:
			b = Silah27.box(sw_name, R)   # v27 savuruşları (bilinmeyen: eski varsayılan)
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
	var ex_e: Node = atk.get("exec_t") if atk.has("exec_t") and is_instance_valid(atk["exec_t"]) else null
	for e in get_tree().get_nodes_in_group("dusman"):
		if not is_instance_valid(e) or e.dead or atk["hit"].has(e):
			continue
		if box.intersects(e.hurt_rect()) or e == ex_e:
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
			if atk.get("heavy", false) and String(it.get("id", "")) != "gun_ay_ikizi":
				mult *= float(V34_AGIR["sarj_k"].get(_tempo_class(it), 1.0))   # v34: şarjlı ağır vuruş eski hasarında
			var hp: Vector2 = e.hurt_rect().intersection(box).get_center()
			# darbe noktası: bıçak ucuna en yakın yer
			var tip_g := arm_root.to_global(_hand_local + _blade_local * R * 0.85)
			if e.hurt_rect().grow(6).has_point(tip_g):
				hp = tip_g
			var hdir := Vector2(float(opts.get("dir", facing)), -0.3)
			if atk.has("dash_px"):
				opts["pierce_n"] = atk["hit"].size()
				opts["kb"] = 60.0
				if not atk.has("dash_stop"):
					atk["dash_stop"] = global_position.x + facing * float(YK_DASH["past"])
			if atk.get("pounce", false):
				opts["pounce"] = true
			if c.get("whip", false):
				opts["whip"] = true
			# v23: zincir içi kritik adımı (Yatağan geri sıçrayışı) ve yuvarlanma sonrası Dönüş Kesiği bitiriş kuralına
			# uyar (_bitiris: yankıyla kritik, değilse hasar çarpanı; kusursuz kaçış yine kesin kritik); bekleme bitirişi
			# (Şimşek Çekişi) kesin kritik kalır
			var bit_adim: bool = c.get("crit", false) and not atk.get("pause", false) and (ItemGen.bitiris_adimi(it, c) or c.get("special", false))
			if bit_adim and perfect_t <= 0.0:
				_bitiris(opts)
			elif c.get("crit", false) or perfect_t > 0.0:
				opts["force_crit"] = true
				opts["krit_neden"] = "kacis" if perfect_t > 0.0 else String(c.get("name", "adim"))
				if perfect_t > 0.0:
					perfect_t = 0.0
					FX.text(e.center() + Vector2(0, -30), "cezalandırma!", Color(0.75, 0.95, 1.0), 7)
			if c.get("trip", false):
				opts["stun"] = 0.9
				opts["launch"] = 140.0
			# v15: uçtan isabet kesin kritik (kırbaç menzil ödülü), adımın sersemletmesi (ağır çekiç)
			if c.get("tipcrit", false) and dist > R * 1.05:
				opts["tip_crit"] = true   # v23: koşul kritiği (aynı düşmanda Zorluk.kosul_bekleme sıklığında; _deal)
			if c.has("stun"):
				opts["stun"] = maxf(float(opts.get("stun", 0.0)), float(c["stun"]) * (1.0 + hold))
			opts["behind"] = "facing" in e and int(e.facing) == int(signf(float(opts.get("dir", facing))))
			opts["heavy"] = atk.get("heavy", false)
			# v35: zincir bitirişi hafif düşmanı havaya savurur (Enemy ağır / uçan / zırhlıyı kendisi eler)
			if c.get("last", false) and not atk.get("pause", false) and not ("is_boss" in e and e.is_boss):
				opts["launch"] = maxf(float(opts.get("launch", 0.0)), float(V35["fin_firlat"]))
			opts["hit_n"] = atk["hit"].size()
			opts["sfx_done"] = true
			opts["feel_done"] = true
			# v21 Yıldırım Hamlesi (tam şarj): deldiği her düşmana gökten yıldırım; ilki tam güç, sonrakiler
			# hafif (art arda ekran flaşı yormasın). Vuruş +%30 ve kısa sersemletme.
			var thunder_k := float(atk.get("thunder", 0.0))
			if thunder_k > 0.0:
				mult *= 1.3
				opts["stun"] = maxf(float(opts.get("stun", 0.0)), 0.45)
			var v19_tag := _v19_opts(e, c, opts)
			if int(atk.get("yanki", 0)) > 0:
				# v22: eski gecikmeli yankı kesiğinin hasarı (%35, usulde ×2) vuruşun kendisinde
				mult *= float(V19["yk_mult"]) + float(V19["yk_echo"]) * float(atk["yanki"])
			# v22 vuruş efekti yoğunluğu: aynı düşmana 0,5 sn içinde gelen sıradan vuruş ve aynı savuruşun 2., 3.
			# düşmanı küçük / sade efekt alır (FX.hit_k); ilk vuruş, bitiriş, ağır, kritik ve infaz tam efekt
			var fx_now := Game.clock()
			var fx_rapid: bool = fx_now - float(e.get_meta("v22_fx_t", -9.0)) < float(V22_FX["repeat_t"])
			e.set_meta("v22_fx_t", fx_now)
			var fx_full: bool = atk.get("heavy", false) or atk.get("pause", false) or c.get("last", false) or c.get("exec", false) or opts.get("force_crit", false)
			FX.hit_k = 1.0 if fx_full else (float(V22_FX["lite"]) if fx_rapid else 1.0) * (1.0 if atk["hit"].size() <= 1 else float(V22_FX["extra_foe"]))
			FX.in_hit = true
			_deal(e, float(it["dmg"]) * mult, it, opts)
			Silah27.on_hit(self, e, it, c, opts)   # v27: al izi, Dolama, top gibi fırlatma
			if c.get("flash", false) and is_instance_valid(e):
				_yk_crack_later(e)
			if thunder_k > 0.0 and is_instance_valid(e):
				# şimşek düşmanın ayağına (tepeden iner); ölmüş olsa da son konumuna
				FX.thunder(e.global_position, thunder_k)
				FX.anim("electric_impact", e.center(), 0.0, 0.9, Color(0.7, 0.88, 1.0))
				atk["thunder"] = 0.55
			# v15 çekiş: tırpan / kanca düşmanı kendine çeker (ağırlar yerinde kalır, çekilme penceresi açılır)
			if c.has("pull") and is_instance_valid(e) and not e.dead and not e.heavy and not e.flying:
				e.velocity.x = -signf(e.center().x - center().x) * float(c["pull"]) * (1.0 + 0.5 * hold)
				e.velocity.y = minf(e.velocity.y, -40.0)
				e.pulled_t = 0.5
				FX.streak(e.center(), center() + Vector2(facing * 10, -12), weapon_color(it), 0.1)
			var crit_done: bool = opts.get("crit_done", false)
			if crit_done:
				FX.hit_k = 1.0
			var lite := FX.hit_k < 0.99
			var big: bool = crit_done or atk.get("pause", false) or atk.get("heavy", false)
			# ---- v14 vuruş kademesi: her vuruş aynı şiddette okunmaz; hafif vuruş sade, büyük vuruş olay
			var tier := 0
			if big:
				tier = 2
			elif heavy_w or opts.get("last", false) or float(c["kb"]) > 200.0:
				tier = 1
			var feel: Array = HIT_FEEL[tier]
			var killed: bool = not is_instance_valid(e) or e.dead
			# v17: aynı savuruş geçişinde (çok vuruşlu savuruşta her geçiş ayrı) ilk isabet kamera / duraklama hissini
			# tam verir; ikinci, üçüncü düşman yalnızca küçük bir ek duraklama ve hafif sarsıntı ekler (üst üste binmez)
			var pass_key := "%d/%d" % [int(atk.get("multi_i", 0)), int(float(atk.get("spin_t", 0.0)) * 100.0)]
			if atk.get("hs_key", "") != pass_key:
				atk["hs_key"] = pass_key
				atk["hs_n"] = 0
				atk["hs_v"] = 0.0
			var first_hit: bool = int(atk["hs_n"]) == 0
			atk["hs_n"] = int(atk["hs_n"]) + 1
			_hit_sfx(it, tier >= 1, crit_done, String(c["s"]))
			if Ses.has_method("hit"):
				var surf := "tas" if ("sprite_kind" in e and e.sprite_kind == "balbal") else ""
				if crit_done and first_hit:
					# v25: kritik her zaman kendi ödül sesini çalar (öldürüşte de; altında kısık öldürüş sesi); künt silahta
					# tok çeşidi (Ses.hit "kunt"); v26: taşa (Balbal) kritik de kritik sesi (tok çeşidi), Ses.hit kısmayı açar
					Ses.call("hit", 2, hp, "kunt" if (_impact_kind(it) == "blunt" or surf != "") else "")
					if killed:
						Ses.play("olum_vurus", -8.0, 1.0, 0.03, 0.02, hp)
				else:
					Ses.call("hit", 3 if killed else tier, hp, surf)
			var wcol := weapon_color(it)
			var fcol: Color = WFX.get(it.get("id", ""), {}).get("col", wcol)
			# darbe noktası: kademe 0'da küçük kıvılcım, 1'de darbe yıldızı, 2'de silah türüne göre darbe sprite'ı + kritik patlaması
			# v22: hızlı ardışık vuruşta (lite) yalnızca küçük kıvılcım; kademe 1'de halka ve silaha özgü ek efekt yalnızca
			# tam efektli vuruşta; kıvılcım sayısı azaldı (düşman hızlı kombolarda okunur kalsın)
			if tier == 0 or lite:
				if SlashFX.has("spark_m"):
					FX.slash_sprite("spark_m", hp, hdir.angle(), Vector2.ONE * (0.75 if lite else 1.0), fcol.lerp(Color.WHITE, 0.4), false, Vector2(-1, -1), null, 30.0)
				else:
					FX.impact(hp, hdir, wcol, float(feel[4]) * (0.7 if lite else 1.0))
			else:
				FX.impact_sprite(_impact_kind(it), hp, hdir, fcol, (1.15 if tier == 2 else 0.85) * (1.1 if heavy_w else 1.0))
				if tier == 2:
					if SlashFX.has("hit_ring"):
						FX.slash_sprite("hit_ring", hp, 0.0, Vector2.ONE * 1.2, fcol.lerp(Color.WHITE, 0.5), true, Vector2(-1, -1), null, 30.0)
					_weapon_hit_fx(it, hp, hdir, true)
			if tier == 2 and SlashFX.has("crit_burst") and crit_done:
				FX.slash_sprite("crit_burst", hp, 0.0, Vector2(1.0, 1.0), Color(1.0, 0.92, 0.6), true, Vector2(-1, -1), null, 30.0)
			if crit_done and first_hit:
				_crit_accent(it, hp, fcol)
			if first_hit and not lite:
				SanatAnim.vurus(self, it, hp, hdir)   # v27: pençe izleri
			if not lite:
				# v31: darbe parlaması ve yönlü sıçrantı vuruşu taşıdığından kıvılcım kıymıkları yarıya indi (okunurluk)
				FX.sparks(hp, hdir, wcol.lerp(Color.WHITE, 0.3), maxi(1, int(feel[3]) / 2 - 1), 150.0 + 60.0 * tier)
			if it.get("material", "") == "od_tasi" and not lite:
				FX.fire(hp, 2 + tier, 0.28)
			elif it.get("material", "") == "ayaz" and tier >= 1 and not lite:
				FX.anim("frost_nova", hp, 0.0, 0.4, Color(0.7, 0.9, 1.0))
			if first_hit:
				Game.kick(Vector2(facing, 0), float(feel[1]) * (1.2 if heavy_w else 1.0))
			if float(feel[2]) > 0.0:
				Game.shake_dir((float(feel[2]) + (0.15 if killed else 0.0)) * (1.0 if first_hit else 0.25), Vector2(facing, 0.35))
			if tier == 2 and first_hit:
				Game.rumble(0.45 + 0.3 * hold, 0.2, 0.1)
				# darbe karesi: v22 yalnızca tam şarjlı ağır vuruşta (kritikte, bitirişte ve öldürüşte yok: hızlı kombolarda
				# ekran sık sık kararıp herkesi beyaz siluete çeviriyordu). İnfaz ve seçkin / boss ölümü kendi karesini verir.
				if hold > 0.6:
					ImpactFrame.play([self, e], 1.0 if crit_done else 0.7, 2)
					Game.slowmo(0.3, 0.08)
			elif killed:
				Game.rumble(0.3, 0.15, 0.08)
			if c.get("double", false):
				var opts2 := opts.duplicate()
				opts2["kb"] = float(c["kb"]) * 0.6
				FX.hit_k = minf(FX.hit_k, float(V22_FX["lite"]))
				_deal(e, float(it["dmg"]) * mult * 0.7, it, opts2)
				FX.impact(hp + Vector2(facing * 6, -6), hdir, weapon_color(it), 0.6)
			combo_add(e)
			_v19_after_hit(e, it, c, hp, hdir, v19_tag, first_hit, killed)
			if not is_on_floor():
				air_hang = 0.28
			# hitstop: kademe + şarj + kombo (en çok %35) — 120 ms üstü "takılma" gibi okunur, sınır.
			# v17: hafif vuruşta silah ağırlığıyla ölçeklenir (hançer kısa, kılıç tam); savuruş başına bir kez
			# v22: kombo uzadıkça duraklama en çok %10 uzar (eski %35: uzun kombolarda oyun sürekli donuyordu)
			var hs_k := 1.0 + minf(0.1, 0.01 * float(combo_n))
			# v35 kademeleri (V35): hafif 0,03 (hançerde ×0,75'e iner) · orta 0,05 · bitiriş / büyük 0,09 · kritik +0,03
			var fin_v35: bool = c.get("last", false) and not atk.get("pause", false)
			var base_hs := float(V35["hs_hafif"])
			if fin_v35 or tier == 2:
				base_hs = float(V35["hs_bitiris"])
			elif tier == 1:
				base_hs = float(V35["hs_orta"])
			else:
				base_hs *= lerpf(float(FLOW["hs_light_min"]), 1.0, clampf(_weight(it) / 0.45, 0.0, 1.0))
			if _tempo_class(it) in V34_AGIR["sa_wind"] and not fin_v35:
				base_hs *= float(V34_AGIR["hs"])   # v34: ağır silahın ağırlığı yavaşlıktan değil darbeden
			if crit_done:
				base_hs += float(V35["hs_krit"])
			var hs := minf(0.12, (base_hs + (0.03 * hold if atk.get("heavy", false) else 0.0)) * hs_k + (float(V35["hs_olum"]) if killed else 0.0))
			if lite:
				hs *= 0.6   # v22: aynı düşmana hızlı ardışık sıradan vuruş kısa donar
			if first_hit:
				Game.hitstop(hs)
			else:
				Game.hitstop(clampf(hs - float(atk["hs_v"]), float(FLOW["hs_extra"]), 0.04))
			atk["hs_v"] = maxf(float(atk["hs_v"]), hs)
			FX.hit_k = 1.0
			FX.in_hit = false
			if atk.get("heavy", false) and hold > 0.5 and level and level.has_method("flash_white"):
				level.flash_white(0.22)
	if level and level.has_method("break_cracks"):
		level.break_cracks(box)


# ------------------------------------------------------------------ hasar hesabı
## v23 kritik ölçümü (testler okur): isabet sayısı ve kritiklerin kaynağı (şans / silah koşulu / kesin)
static var krit_say := {"isabet": 0, "sans": 0, "kosul": 0, "kesin": 0}
## v23: kendiliğinden seyrek olan beceri koşulları (tam bırakış, geri çekilirken atış, dönen balta, delip geçme, iki
## hedef, uzaktan, duvara çarpma, düşerken, donmuşu kırma): koşul kritiği beklemesi uygulanmaz
const KRIT_SERBEST := ["kemankes", "part_atisi", "yelpaze", "firlat_cagir", "simsek_hamlesi", "ulu_kesik", "ruh_dalgasi",
	"gudum", "itme", "ezme", "don", "ritim"]


func _bitiris(opts: Dictionary) -> bool:
	## v23 zincir bitirişi: Kut Yankısı'yla gelen (zamanında basılan) bitiriş kesin kritik (true); değilse kritik
	## değil, Zorluk.bitiris_k hasar çarpanı (_deal uygular). Usul sayılmaz: tuşa ezbere basan oyuncu usul
	## penceresine sık denk gelir (usulün kendi hasar çarpanı var).
	if not atk.is_empty() and int(atk.get("yanki", 0)) > 0:
		opts["force_crit"] = true
		opts["krit_neden"] = "yanki_bitiris"
		return true
	opts["bitiris"] = true
	return false


func _deal(e: Node, base: float, it: Dictionary, opts: Dictionary = {}) -> void:
	if not opts.get("ok", false):
		_kz_gain(it)   # v20 Kızışma (yakın vuruş isabeti)
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
	# v12: usul, ad güçleri, yeraltı ruhları
	var on_beat: bool = bool(opts.get("usul_ok", false)) if opts.get("ok", false) else usul_buff_t > 0.0
	if on_beat:
		d *= usul_mult()
		if FX.hit_k >= 0.99:
			FX.burst(e.center(), Color(1.0, 0.85, 0.45), 3, 50, 0.25, 0.12, 0, true)
	if e.is_boss and Adlar.earned("basat"):
		d *= 1.25
	if e.elite and Adlar.earned("bogac"):
		d *= 1.3
	if Adlar.earned("alp_er_tunga"):
		d *= 1.15
	if opts.get("ok", false) and Adlar.earned("bamsi_beyrek"):
		d *= 1.25
	if opts.get("don", false) and Adlar.earned("kam_ata"):
		d *= 1.25   # v25 Kam Ata: don kılığında +%25 hasar (eskiden Üç Âlem'e bağlıydı)
	# mekanik kritik koşulları
	var crit := randf() * 100.0 < ItemGen.krit_sans(it)   # v23: SnH ile aynı şans (silah + nitelik + lütuf / ad)
	var crit_sans := crit   # v23 kritik ölçümü: şans kritiği mi, koşul mu, kesin mi (krit_say)
	var krit_serbest := false   # v23: beceri koşulu (yuvarlanma sonrası kesinler): kosul_bekleme uygulanmaz
	if Game.has_lutuf("erlik"):
		d *= 1.35
	match mech:
		"ucuncu_vurus":
			if opts.get("last", false):
				d *= 1.0 + mv / 100.0
				if atk.get("pause", false) or _bitiris(opts):   # v23: Kut Yankısı'yla kritik, değilse bitiriş hasarı
					crit = true
					krit_serbest = true
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
			if sure_crits > 0 and rolled_t < 1.0:
				sure_crits = 0   # v26: kesin kritik yalnızca yuvarlanmadan sonraki ilk 1 sn (rolled_t 2 → 1 sn kala söner)
			if sure_crits > 0:
				crit = true
				krit_serbest = true
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
			if opts.get("last", false) and (atk.get("pause", false) or _bitiris(opts)):
				crit = true
				krit_serbest = true
		"zehir_dis":
			opts["poison"] = 1
			if e.poison >= 3:
				crit = true
		"tulpar":
			if sprint or atk.has("dash") or opts.get("dash", false):
				crit = true
			opts["pierce"] = true
		"arkadan":
			# v23: sendeleyen ("stagger") hafif yaratık artık sayılmaz (her vuruş sendeletir, her vuruş kritik oluyordu)
			if opts.get("behind", false) or e.stun_t > 0.0:
				crit = true
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
			# v22: sayaç savuruş başına bir kez artar (üç düşmana değen tek savuruş yel bıçağını kendiliğinden atmasın)
			var yel_new: bool = atk.is_empty() or not atk.get("yel_n", false)
			if not atk.is_empty():
				atk["yel_n"] = true
			if yel_new:
				wind_n += 1
			if yel_new and wind_n % 3 == 0:
				_spirit_wave.call_deferred(it, Color(0.78, 0.95, 1.0), {"kb": 60.0}, 0.0, 380.0)
			if not e.is_on_floor():
				crit = true
		"durus", "dolama", "albasti", "top_gibi", "kurma", "kizginlik", "bag":
			# v27 yeni silahlar (Silah27.deal): [hasar, kritik, beceri kritiği]
			var r27: Array = Silah27.deal(self, e, it, opts, d)
			d = float(r27[0])
			crit = crit or bool(r27[1])
			krit_serbest = krit_serbest or bool(r27[2])
	# v19 ok sökme: saplı oku olan düşmana yakın dövüş vuruşu okları söker (ok başına +%30, 3+ okta kritik)
	if not opts.get("ok", false) and not atk.is_empty() and okc:
		d *= okc.melee_rip(e, it, opts)
	if opts.get("tip_crit", false):
		crit = true
	# v23: durum koşullu kritik aynı düşmanda en çok Zorluk.kosul_bekleme sn'de ve kosul_vurus isabette bir (kanayan / yanan / sersem / havadaki
	# hedef, arkadan, uçtan, tam ivme sürüp gidince her vuruş kritik olmasın); kesinler (yankı, mühür, karşılık, karşı
	# vuruş, kusursuz kaçış, infaz, tam bırakış) ve beceri koşulları bekleme tanımaz
	var kn := int(e.get_meta("v23_krit_n", 99)) + 1   # bu düşmana son koşul kritiğinden beri isabet
	e.set_meta("v23_krit_n", kn)
	if crit and not crit_sans and not krit_serbest and not (mech in KRIT_SERBEST):
		var kt := Game.clock()
		if kt - float(e.get_meta("v23_krit_t", -99.0)) < Zorluk.kosul_bekleme() or kn < Zorluk.kosul_vurus():
			crit = false
		else:
			e.set_meta("v23_krit_t", kt)
			e.set_meta("v23_krit_n", 0)
			if opts.get("tip_crit", false):
				FX.text(e.center() + Vector2(0, -30), "uçtan!", Color(1.0, 0.9, 0.6), 7)
			elif mech == "arkadan":
				FX.text(e.center() + Vector2(0, -24), "arkadan!", Color(0.85, 0.75, 1.0), 7)
	if opts.get("bitiris", false):
		d *= Zorluk.bitiris_k()   # v23: ritimsiz bitiriş: kritik değil, hasar çarpanı (SnH'de ItemGen.zincir_hasar)
	var crit_kosul := crit and not crit_sans and not krit_serbest
	if opts.get("force_crit", false):
		crit = true
	krit_say["isabet"] += 1
	if crit:
		var kk := "sans" if crit_sans else ("kosul" if crit_kosul else "kesin")
		krit_say[kk] += 1
		if kk == "kesin":   # kesin kritiğin nedeni (ölçüm)
			var kn2 := "kesin_" + String(opts.get("krit_neden", "beceri" if krit_serbest else "diger"))
			krit_say[kn2] = int(krit_say.get(kn2, 0)) + 1
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
	d = Unsur.before_hit(self, e, it, opts, d)   # v20 unsur: yanana ek, donmuşu kırma, damgalıya ek
	var killed: bool = e.take_hit(d, opts)
	Unsur.after_hit(self, e, it, opts, d, killed)   # v20 unsur: tutuşma, ayaz yükü, şimşek, töz, kök
	Silah27.after_deal(self, e, it, opts, d, killed)   # v27 Tengri Bağı: bağlılara hasar payı
	sanat.on_deal(e, d, killed, opts)   # v27: Alp Nişanı kazancı
	if killed:
		# v12 destanlar: yayla kesilenler, tek savuruşta üç
		if opts.get("ok", false):
			if Adlar.add_stat("bow_level") >= 10.0:
				Adlar.deed("bamsi_beyrek", center())
		elif not atk.is_empty() and not opts.get("don", false):
			atk["kills"] = int(atk.get("kills", 0)) + 1
			if int(atk["kills"]) >= 3:
				Adlar.deed("segrek", center())
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
			level.explode(e.center(), 36, boom * Zorluk.taban() * Zorluk.esya_k(int(it["tier"])) * Game.item_mult(it), true)


# ------------------------------------------------------------------ uzak silahlar
func _swing_sfx(it: Dictionary, sw: Dictionary, is_pause: bool) -> void:
	## Savuruş sesi: silahın ses sınıfına göre gerçek kayıt katmanı; saplamalar ince ve hızlı, ağır savuruşlar kalın
	var sname: String = atk["c"]["s"]
	var cls: String = WSND.get(it.get("id", ""), "kilic" if it.get("kind", "") != "heavy" else "cekic")
	var is_thrust: bool = sname in ["thrust", "flurry", "lunge", "pole_thrust", "pole_thrust_lo", "stab_heavy", "lunge_long"]
	var is_big: bool = atk.get("heavy", false) or sname in ["overhead_2h", "slam_2h", "windmill", "helicopter", "uppercut_2h", "slam", "heavy", "spin_2h", "step_down"]
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
	if sname in ["iai", "yk_iai", "yk_flash"]:
		name = "savur_katana"
	if sname in ["dual_l", "dual_r", "backstep"] and Ses.has("savur_hafif"):
		name = "savur_hafif"
		pit *= 1.1
	if sname in ["whip_crack", "whip_side"]:
		name = "savur_kirbac"
	pit *= _kz_pitch()   # v20: Kızışma yüküyle incelir
	Ses.play(name, vol, pit, 0.06)
	if is_pause:
		Ses.play("savur_dev", -7.0, 1.1, 0.05, 0.0)


func _hit_sfx(it: Dictionary, big: bool, crit: bool, sname: String) -> void:
	## Darbe sesi: silah sınıfı + vuruşun büyüklüğü (et kesme, künt, delme, balta, kırbaç, çekiç çakma)
	var cls: String = WSND.get(it.get("id", ""), "kilic" if it.get("kind", "") != "heavy" else "cekic")
	var is_thrust: bool = sname in ["thrust", "flurry", "lunge", "pole_thrust", "pole_thrust_lo", "stab_heavy", "lunge_long", "cross_dash"]
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
	Ses.play(name, -3.0 if big else -5.0, pit, 0.07, 0.02)
	if crit and not Ses.has_method("hit"):
		Ses.play("darbe_kritik", -1.0, 1.0, 0.04, 0.05)


func _fire_bow(charge: float) -> void:
	## v19: atış Okculuk'ta (hız, hedef yardımı, yelpaze, tam bırakış, saplanma); eski çağrılar için ince sarmalayıcı
	okc.fire(charge)


func _uzak_nisan(origin: Vector2, spd: float, grav: float, old: Vector2) -> Vector2:
	## v25: fırlatmada dikey hedef yardımı (yayınkiyle aynı: öndeki en yakın düşman, yerçekimi düşüşü hesaba katılır);
	## eskiden cirit / sapan taşı alçak yaratığın (kurt) üstünden geçiyordu. Önde kimse yoksa eski atış.
	var a := okc._aim_angle(origin, spd, grav) if okc else 0.0
	if absf(a) < 0.0001:
		return old
	return Vector2(cos(a) * float(facing), sin(a)) * spd


func _uzak_hedef(menzil: float, dikey: float) -> Node:
	## v25: öndeki en yakın düşman (mancınık / gök asası nişanı)
	var best: Node = null
	var bd := menzil
	for e in get_tree().get_nodes_in_group("dusman"):
		if not is_instance_valid(e) or e.dead:
			continue
		if "_hidden" in e and e._hidden:
			continue
		var to: Vector2 = e.center() - center()
		if to.x * float(facing) < -6.0 or absf(to.y) > dikey:
			continue
		var d := to.length()
		if d < bd:
			bd = d
			best = e
	return best


func _throw_item(it: Dictionary) -> void:
	var p := Projectile.new()
	p.team = "p"
	p.position = global_position + Vector2(facing * 10, -32)
	p.unsur = Unsur.of(it)   # v25: unsur renginde mürekkep izi
	if it["id"] == "cirit":
		p.kind = "javelin"
		p.velocity = _uzak_nisan(p.position, 430.0, 180.0, Vector2(facing * 430, -40))
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
			f.unsur = Unsur.of(it)
			var origin := global_position
			f.on_hit = func(e: Node) -> void:
				_deal(e, float(it["dmg"]), it, {"kb": 50.0, "dir": signf(e.center().x - origin.x), "far": e.center().distance_to(origin) > 150.0})
			level.add_projectile(f)
		cd[sec_slot] = _sec_cd(it)
		cd_max[sec_slot] = cd[sec_slot]
		vis_scale = Vector2(1.06, 0.95)
		return
	elif it["id"] == "mancinik_tasi":
		p.kind = "stone_big"
		p.atlas_item = "mancinik_tasi"
		p.atlas_mat = "kara_tas"
		p.velocity = Vector2(facing * 260, -300)
		p.gravity = 620.0
		# v25: öndeki düşmanın üstüne düşecek yay (uçuş süresi uzaklıkla 0,4-0,95 sn); eskiden 250 px'e sabit düşüyordu
		var hd := _uzak_hedef(300.0, 140.0)
		if hd:
			var to: Vector2 = hd.center() + Vector2(0, -4) - p.position
			var tt := clampf(absf(to.x) / 270.0, 0.4, 0.95)
			p.velocity = Vector2(to.x / tt, (to.y - 0.5 * p.gravity * tt * tt) / tt)
		p.explode_on_wall = true
		var r := float(it.get("mech_v", 60))
		p.on_explode = func(pos: Vector2) -> void:
			level.quake(pos, r, float(it["dmg"]), it, self)
		level.add_projectile(p)
		cd[sec_slot] = _sec_cd(it)
		cd_max[sec_slot] = cd[sec_slot]
		vis_scale = Vector2(1.1, 0.9)
		return
	else:
		p.kind = "stone"
		p.velocity = _uzak_nisan(p.position, 380.0, 300.0, Vector2(facing * 380, -60))
		p.gravity = 300.0
		p.bounces = int(it.get("mech_v", 1))
	p.on_hit = func(e: Node) -> void:
		_deal(e, float(it["dmg"]), it, {"kb": 90.0, "dir": facing, "stun": 0.25 if it["id"] == "coban_sapani" else 0.0})
	level.add_projectile(p)
	cd[sec_slot] = _sec_cd(it)
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
			t.position = Vector2(global_position.x + facing * 20, level.surface_y(int(global_position.x / 24.0 + facing), int(global_position.y / 24.0) - 2) * 24.0)
			level.actors.add_child(t)
		"ok_yagmuru":
			var ox := global_position.x + facing * 90
			var ground_y: float = level.surface_y(int(ox / 24.0), int(global_position.y / 24.0) - 2) * 24.0
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
	_cancel_attack(false)
	_end_trail()
	heal(max_hp() * Zorluk.sise_sifa())   # v22: şişe payı data/zorluk.json
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
	_cancel_attack(false)
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
	drop_t -= delta
	set_collision_mask_value(4, drop_t <= DROP_MASK)   # v33: kurt biçiminde de tek yönlü platformdan inilir
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
						# v26: üçüncü ısırık artık kesin kritik değil (Bozkurt biçimi her açılışta 3-4 kritik veriyordu): bitiriş hasarı
						var opts := {"kb": 90.0 if not last else 260.0, "dir": facing, "launch": 180.0 if last else 0.0, "bitiris": last, "last": last}
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
		if jump_buf > 0.0 and is_on_floor() and Input.is_action_pressed("asagi"):
			# v33: aşağı + zıpla: tek yönlü platformdan / kuyu kapağından iner
			drop_t = 0.25
			jump_buf = 0.0
			position.y += 2
		elif jump_buf > 0.0 and (coyote > 0.0 or air_jumps > 0):
			if coyote <= 0.0:
				air_jumps -= 1
				FX.ring(global_position, 14, Color(0.6, 0.95, 1.0), 0.2)
			velocity.y = JUMP_V * 1.08
			jump_buf = 0.0
			coyote = 0.0
			jumping = true
			vis_scale = Vector2(0.85, 1.18)
			FX.dust(global_position, Vector2.UP, 4, 0.28)
		if jumping and velocity.y < -140.0 and not Input.is_action_pressed("zipla") and pounce_t <= 0.0:
			velocity.y *= JUMP_CUT   # v34: alçak zıplama (bir kez)
			jumping = false
	if is_on_floor():
		jumping = false
	# v34: kurt da yükselişte / düşüşte ayrı yerçekimiyle (insan biçimiyle aynı his)
	velocity.y = minf(velocity.y + (GRAV_RISE if velocity.y < 0.0 else GRAV_FALL) * delta, MAX_FALL)
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
	_vs_v += ((Vector2.ONE - vis_scale) * 300.0 - _vs_v * 17.0) * delta
	vis_scale += _vs_v * delta
	wolf_anim.scale = vis_scale
	_lean_v += ((clampf(velocity.y / 900.0, -0.25, 0.25) * float(facing) - wolf_anim.rotation) * 200.0 - _lean_v * 20.0) * delta
	wolf_anim.rotation += _lean_v * delta
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
		pose = _atk_pose(atk["t"] / atk["dur"])
	elif charge_t > 0.2:
		it = slot(mel_slot)
		pose = [-0.5, 1.95, -0.15, 1.0, 1.0]
	elif hero_pose_t > 0.0 or hero_t >= float(HERO["antic"]):
		# v34 Kahraman İnişi: dalışta silah baş üstünde geride; inişte ön kol aşağı, yumruk toprakta, bıçak geriye kalkık
		it = slot(mel_slot)
		pose = HERO_POSE_DIVE if hero_t >= 0.0 else HERO_POSE_LAND
	elif aim_t >= 0.0:
		it = slot(sec_slot)
		var pull := okc.pull()
		# tam gerilince ok ucu hafifçe titrer (gerginlik); v19: kol hedef yardımının açısına eğilir
		var quiver := 0.012 * sin(aim_t * 70.0) if pull >= 1.0 else 0.0
		pose = [1.55 - okc.tilt + quiver, 0.05, 0.0, 1.0, 1.0 - 0.05 * pull]
		pose = SanatAnim.bow_pose(self, pose, pull, 0.0)   # v27
	elif bow_rel_t > 0.0 and slot(sec_slot).get("kind", "") == "bow":
		it = slot(sec_slot)
		var rk := bow_rel_t / BOW_REL
		pose = [1.55 - okc.tilt + 0.12 * rk, 0.05, -0.1 * rk, 1.0, 1.0 + 0.04 * rk]
		pose = SanatAnim.bow_pose(self, pose, 0.0, rk)   # v27
	elif not Silah27.sec_pose(self).is_empty():
		it = slot(sec_slot)
		pose = Silah27.sec_pose(self)   # v27: Tatar Yayı atış / kurma, Küzgü ışını
	elif throw_t >= 0.0:
		it = slot(sec_slot)
		var tk := clampf(throw_t / 0.28, 0.0, 1.0)
		pose = SanatAnim.throw_pose(self, it, tk)   # v27 (eski: SWINGS["axe"])
	elif block_t >= 0.0:
		it = slot(sec_slot)
		is_shield = true
		pose = [1.25, 0.9, 0.0, 1.0, 1.0]
	elif cast_t > 0.0:
		it = slot(sec_slot)
		pose = SanatAnim.cast_pose(self, it, cast_t)   # v27 (eski: sabit [1.45, 0.1, -0.5])
	var show := not pose.is_empty() and not it.is_empty() and roll_t <= 0.0 and hurt_t <= 0.0
	arm_root.visible = show
	if bow_str and (not show or it.get("kind", "") != "bow"):
		bow_str.visible = false
		_bow_nock_ok = false
	if not show:
		_last_pose_ok = false
		_art.erase("prev")
		weapon.visible = false
		shield_spr.visible = false
		if arm_root_b:
			arm_root_b.visible = false
		return
	# v14 kırbaç gecikmesi: bilek açısı üst kolun açısal hızından geri kalır (hızlanırken geride, durunca ileri
	# fırlar: doğal aşma). Ağır silahlarda daha çok. Yalnızca savuruşlarda.
	var dt := 1.0 / 60.0
	var a1 := float(pose[0])
	if not atk.is_empty() and atk.get("phase", "") != "charge":
		var da := (a1 - _prev_a1) / dt if _prev_a1_ok else 0.0
		var wt := _weight(it)
		var target := -clampf(da * (0.022 + 0.02 * wt), -0.5, 0.5)
		if atk["phase"] == "act":
			_over_dir = signf(da) if absf(da) > 0.5 else _over_dir
		_whip_v += ((target - _whip) * 1400.0 - _whip_v * 36.0) * dt
		_whip += _whip_v * dt
		pose = pose.duplicate()
		pose[2] = float(pose[2]) + _whip
		# kol: aşma salınımı (vuruş bitince)
		if _over_t < 0.3:
			_over_t += dt
			pose[0] = float(pose[0]) + _over_amp * exp(-_over_t * 15.0) * sin(_over_t * 32.0)
		# hazırlık tutuşunda silah bir tık geri çekilir ("gerilme")
		if atk.has("antic") and atk["phase"] == "wind":
			var hold_t := maxf(0.016, float(atk.get("ph", [0, 0, 0, 0, 0.03])[4]))
			var q := clampf(float(atk["antic"]) / hold_t, 0.0, 1.0)
			pose[0] = float(pose[0]) + 0.08 * q * (-_over_dir if _over_dir != 0.0 else 1.0)
		# vuruş anında ön kol gerilir (hız abartısı)
		if atk["phase"] == "act":
			pose[4] = float(pose[4]) * (1.0 + minf(0.16, absf(da) * 0.006))
	else:
		_whip = lerpf(_whip, 0.0, 0.4)
		_whip_v = 0.0
	_prev_a1 = a1
	_prev_a1_ok = not atk.is_empty()
	pose = SanatAnim.pose(self, it, pose)   # v27: bitiriş süslemesi
	_last_pose = pose
	_last_pose_ok = not atk.is_empty()
	var pts := _pose_points(pose)
	var sh: Vector2 = pts[0]
	var e: Vector2 = pts[1]
	var h: Vector2 = pts[2]
	var bd: Vector2 = pts[3]
	if not atk.is_empty() and it.get("kind", "") != "bow":
		bd = _ground_clamp(h, bd, _reach(it))
	_hand_local = h
	# v23: bıçak yönü düzlem izdüşümünün boyuyla (önkısalma): uç = el + _blade_local × R görünen uçtur
	_blade_local = bd.normalized() * clampf(bd.length(), 0.15, 1.0) if bd.length() > 0.01 else Vector2(facing, 0)
	_place_bone(arm_upper, sh, e, float(arm_meta.get("upper_len", 8.5)))
	_place_bone(arm_fore, e, h, float(arm_meta.get("fore_len", 8.0)))
	arm_fist.position = h
	arm_fist.rotation = arm_fore.rotation
	arm_fist.flip_h = facing < 0
	_update_back_arm(it, h, bd, is_shield)
	var has_sprite := Data.has_weapon_sprite(it.get("id", ""))
	weapon.visible = has_sprite and not is_shield
	shield_spr.visible = has_sprite and is_shield
	var wsc := 1.0
	if weapon.visible:
		wsc = _apply_wspr(weapon, it)
		weapon.position = h
		if it.get("kind", "") == "bow":
			weapon.rotation = 0.0 if facing > 0 else PI
			_update_bow(it, h)
		else:
			weapon.rotation = bd.angle()
			# v23: boy düzlem izdüşümüyle kısalır (önkısalma); bilek dönüşü (roll) eni inceltir / yüzü çevirir
			var roll_k := 1.0
			if pose.size() >= 8 and not atk.is_empty():
				var cr := cos(float(pose[7]))
				roll_k = signf(cr) * maxf(absf(cr), 0.3) if cr != 0.0 else 0.3
			weapon.scale = Vector2(clampf(bd.length(), 0.15, 1.0), facing * roll_k) * wsc
		# v23: çarkta bıçak düzlemin arka yarısına geçince gövdenin arkasında (eşik histerezisli)
		var behind := false
		if not atk.is_empty() and (atk["plane"] if atk.has("plane") else plane_def(String(atk["c"].get("s", "")))).get("b", false):
			var z := _plane_depth(pose)
			behind = z < (-0.08 if weapon.z_index < 0 else -0.2)
		weapon.z_index = -2 if behind else 0
	if shield_spr.visible:
		var ssc := _apply_wspr(shield_spr, it)
		shield_spr.position = h + Vector2(facing * 3, 0)
		shield_spr.rotation = 0.0
		shield_spr.scale = Vector2(facing, 1) * ssc
	Unsur.weapon_glow(arm_root, it, h, bd, _reach(it), weapon.visible)   # v20: bıçak boyunca unsur ışıması
	SanatAnim.smear(self, it)   # v27: leke kareleri + uç yolu


var _wmat_ink: ShaderMaterial


func _apply_wspr(spr: Sprite2D, it: Dictionary) -> float:
	## Silah sprite'ı: doku sayfası, bölge, pivot (Data.weapon_sprite; stil v2'de mürekkep-cel atlas + ink_char
	## gölgelendiricisi). Dönen: sprite ölçeği (1 / doku yoğunluğu).
	var d: Dictionary = Data.weapon_sprite(Silah27.sprite_id(it), String(it["material"]))   # v27: Gün-Ay duruş sprite'ı
	if spr.texture != d["tex"]:
		spr.texture = d["tex"]
		if d["linear"]:
			if _wmat_ink == null:
				_wmat_ink = ShaderMaterial.new()
				_wmat_ink.shader = Data.INK_SHADER
			spr.material = _wmat_ink
	spr.region_rect = d["region"]
	spr.offset = -(d["pivot"] as Vector2)
	return float(d["scale"])


func _bow_tips(it: Dictionary) -> Array:
	## Yay sprite'ının üst ve alt ucu (pivot'a göre); görüntüden bir kez okunur.
	var key := String(it["id"]) + "/" + String(it["material"])
	if _bow_tip_cache.has(key):
		return _bow_tip_cache[key]
	var out := [Vector2(-2, -16), Vector2(-2, 16)]
	var wd: Dictionary = Data.weapon_sprite(String(it["id"]), String(it["material"]))
	var img: Image = Data.weapon_sprite_image(wd)
	var wsc: float = wd["scale"]
	if img:
		var reg := Rect2i(wd["region"])
		var piv: Vector2 = wd["pivot"]
		var top := Vector2.INF
		var bot := Vector2.INF
		# uçlar: kabzanın (pivot) solunda kalan, en üst ve en alt dolu pikseller
		for y in reg.size.y:
			for x in range(0, mini(reg.size.x, int(piv.x) + int(6.0 / (wsc * 2.0)))):
				if img.get_pixel(reg.position.x + x, reg.position.y + y).a > 0.5:
					if top == Vector2.INF:
						top = Vector2(x, y)
					bot = Vector2(x, y)
					break
		if top != Vector2.INF:
			out = [(top - piv + Vector2(0.5, 0.5)) * wsc, (bot - piv + Vector2(0.5, 0.5)) * wsc]
	_bow_tip_cache[key] = out
	return out


func _update_bow(it: Dictionary, h: Vector2) -> void:
	## Yay: gerildikçe kollar esner (yatay sıkışma), kiriş gez noktasına geri çekilir, ok yayda durur;
	## bırakınca kiriş sönümlü titrer ve yay geri teper. v19: gerilme süresi yaya özgü (Okculuk.PROF), stil v2'de yay
	## hedef yardımının açısına eğilir, kiriş / ok mürekkep, tam bırakış penceresi ok ucunda halka + parıltı.
	var pull := okc.pull()
	var rk := clampf(bow_rel_t / BOW_REL, 0.0, 1.0) if aim_t < 0.0 else 0.0
	var flex := 1.0 - 0.1 * pull
	var tilt := okc.tilt * float(facing)
	weapon.scale = Vector2(flex, facing) * float(Data.weapon_sprite(String(it["id"]), String(it["material"]))["scale"])
	weapon.position = h + Vector2(-facing * 2.0 * rk * rk, 0)
	weapon.rotation = (0.0 if facing > 0 else PI) + tilt
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
	if tilt != 0.0:
		var wp := weapon.position
		top = wp + (top - wp).rotated(tilt)
		bot = wp + (bot - wp).rotated(tilt)
		nock = wp + (nock - wp).rotated(tilt)
	bow_str.visible = true
	bow_str.top = top
	bow_str.bot = bot
	bow_str.nock = nock
	bow_str.dir = facing
	bow_str.rotation = 0.0
	bow_str.arrow_on = aim_t >= 0.0 and not (String(it["id"]) in BAKED_ARROW_BOWS)
	bow_str.glow = (0.6 + 0.4 * sin(aim_t * 18.0)) if (aim_t >= 0.0 and pull >= 1.0) else 0.0
	var pr := Okculuk.prof(it)
	bow_str.variant = "altin" if (okc.in_perfect() or (okc.hazir > 0 and aim_t < 0.05)) else String(pr["var"])
	bow_str.ring = okc.ring_k()
	bow_str.perfect = okc.in_perfect()
	bow_str.tilt = tilt
	bow_str.pull = pull if aim_t >= 0.0 else 0.0
	bow_str.str_col = Color(0.95, 0.9, 0.78) if not bow_str.perfect else Color(1.0, 0.9, 0.55)
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
	sp.scale = Vector2(1.0, maxf(0.2, d.length() / rest_len)) * arm_inv


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
		if not dead and not forced and roll_t > 0.0 and not _pd_done and (ROLL_T - roll_t) <= PERFECT_WIN and perfect_cd <= 0.0:
			_perfect_dodge(from)
		return false
	# v27 Demir Duruş: duruşta gelen darbe karşılanır; Bir Çekiş'in Demir Gönül'ü alınan hasarı azaltır
	if not forced and sanat.karsila(from, projectile):
		return false
	dmg *= sanat.alinan_k()
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
	# v19 Çarpışma: savuruşun ilk anlarında bıçağa değen darbe / mermi karşılanır
	if not forced and _clash(from, projectile, facing_src):
		return false
	var blocked := false
	if block_t >= 0.0 and sh.get("kind", "") == "shield" and facing_src:
		blocked = true
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
	if don_on:
		dmg *= don.dmg_mult()
		if dmg <= 0.0:
			FX.sparks(center() + Vector2(facing * 10, -4), Vector2(facing, -0.5), Color(0.85, 0.8, 1.0), 6, 150.0)
			inv_t = 0.2
			return false
	# v34 lanetli sandık: lanetliyken her darbe iki kat. v34 birleştirme: eskiden Level._lanet_tick her can kaybını
	# (zehir, yüksek düşüş dahil: ikisi de öldürmez) sonradan bir kez daha düşüyor, fazlalık ölümcülse ikinci bir zorlu
	# take_hit yapıyordu (aynı karede iki sarsılma; zehir / düşüş lanetle öldürebiliyordu). Şimdi yalnız darbe, tek
	# geçişte: Umay / Deli Dumrul / dokunulmazlık (Kahraman İnişi dahil) aynı yoldan geçerli.
	if level and int(level.get("lanet") if level.get("lanet") != null else 0) > 0 and dmg > 0.0:
		FX.number(center() + Vector2(10, -20), dmg, false, Color(0.8, 0.5, 1.0))
		dmg *= 2.0
	if Adlar.earned("deli_dumrul") and not Game.run.get("dumrul_used", false) and float(Game.run["hp"]) - dmg < 1.0:
		# Deli Dumrul: Azrail'e meydan okur; bölümde bir kez ölümden 1 canla döner
		dmg = maxf(0.0, float(Game.run["hp"]) - 1.0)
		Game.run["dumrul_used"] = true
		FX.text(center() + Vector2(0, -56), "DELİ DUMRUL AZRAİL'E DİRENDİ!", Color(1.0, 0.5, 0.4), 10)
		FX.ring(center(), 64, Color(1.0, 0.45, 0.35), 0.5)
		Game.slowmo(0.25, 0.6)
	Game.run["hp"] = float(Game.run["hp"]) - dmg
	kz_lose()   # v20: hasar Kızışmayı söndürür
	# v15 süper zırh: ağır savuruş sürerken hasar alınır ama savuruş kesilmez, geri itme / sarsılma yok
	var armored: bool = not atk.is_empty() and bool(atk.get("super_armor", false)) and float(Game.run["hp"]) > 0.0
	inv_t = 0.8 if not armored else 0.35
	Ses.play("bengu_can", -1.0)
	Ses.play("darbe_et", -4.0)
	var kdir := signf(global_position.x - src_x)
	if kdir == 0:
		kdir = -facing
	if armored:
		vis_scale = Vector2(1.06, 0.95)
		FX.sparks(center() + Vector2(-kdir * 8, -4), Vector2(kdir, -0.5), Color(1.0, 0.85, 0.55), 6, 140.0)
	elif blocked and float(Game.run["hp"]) > 0.0:
		# v17: kalkanla karşılanan darbe sarsmaz, komboyu kırmaz; kısa geri kayma
		inv_t = 0.35
		velocity.x = kdir * 90.0
	else:
		hurt_t = 0.25
		combo_break("kırıldı")
		_cancel_attack(false)
		aim_t = -1.0
		velocity = Vector2(kdir * 170.0, -160.0)
		vis_scale = Vector2(1.25, 0.8)
	FX.number(center(), dmg, false, Color(1.0, 0.45, 0.4))
	FX.impact(center(), Vector2(kdir, -0.4), Color(1.0, 0.4, 0.35), 1.3)
	FX.anim("solar_shrapnel", center(), 0.0, 0.7, Color(1.0, 0.5, 0.4))
	FX.blood(center(), Vector2(kdir, -0.6), Color(0.7, 0.06, 0.08), 9)
	Blood.spray(center() + Vector2(0, randf_range(-8, 6)), Vector2(kdir, -0.5), Color(0.62, 0.04, 0.06), 14 + int(dmg * 0.8))
	# v14: alınan hasar hissi hasarın büyüklüğüyle ölçeklenir; ağır darbede (can'ın %25'i) darbe karesi
	var hk := clampf(dmg / maxf(1.0, max_hp()), 0.0, 1.0)
	Game.shake_dir(0.28 + 0.5 * hk, Vector2(kdir, -0.3))
	Game.kick(Vector2(kdir, -0.3), 5.0 + 4.0 * hk)
	Game.hitstop(0.06 + 0.05 * hk)
	Game.slowmo(0.5, 0.1 + 0.08 * hk)
	Game.rumble(0.55 + 0.4 * hk, 0.3, 0.14 + 0.1 * hk)
	if hk >= 0.25:
		ImpactFrame.play([self, from], 0.7, 2)
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
	InkFX.flourish(center() + Vector2(facing * 12, 0), "parry", 9)
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
				_deal(e, 10.0 * mv / 100.0 * Zorluk.esya_k(int(sh["tier"])), slot(mel_slot), {"kb": 120.0, "dir": facing, "scale_item": sh})
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


func _yk_track(it: Dictionary, k: float) -> void:
	## v25 Yıldırım Kılıcı: vuruş evresinde bıçak ucunun yolu (karede ara örneklerle) parlak yay efektine eklenir
	var sw: Dictionary = atk["sw"]
	var pi := maxi(0, int(atk.get("multi_i", 0)) - 1)   # çok geçişli savuruşta geçiş sırası
	if int(atk.get("yk_stop", -1)) == pi:
		return
	var ends: Array = sw.get("yk_end", [1.0])
	if k > float(ends[mini(pi, ends.size() - 1)]):
		# süpürme bitti: yay sönmeye başlar (takip / yeniden geriliş yayı uzatmaz)
		_yk_release()
		atk["yk_stop"] = pi
		return
	if atk["c"].get("xspark", false) and pi == 1 and k >= 0.57 and not atk.get("yk_x", false):
		atk["yk_x"] = true
		_yk_cross_fx(it)
	var R := _reach(it)
	var fx: SimsekKesikFX = atk.get("yk_fx", null)
	if fx == null or not is_instance_valid(fx):
		fx = SimsekKesikFX.arc_live(YK["col"], 1.2 if atk["c"].get("last", false) else 1.0)
		if fx == null:
			return
		atk["yk_fx"] = fx
		atk["yk_k"] = k
	var k0 := float(atk.get("yk_k", k))
	var steps := clampi(int(ceil(absf(k - k0) / 0.006)), 1, 16)
	for i in range(1, steps + 1):
		var kk := lerpf(k0, k, float(i) / float(steps))
		var q := _pose_points(_atk_pose(kk))
		var tip := arm_root.to_global((q[2] as Vector2) + _ground_clamp(q[2], q[3], R) * R)
		fx.add_point(tip)
	atk["yk_k"] = k


func _yk_release() -> void:
	## Parlak yayı serbest bırak (sönmeye başlar)
	if atk.is_empty():
		return
	var fx: SimsekKesikFX = atk.get("yk_fx", null)
	atk.erase("yk_fx")
	atk.erase("yk_k")
	if fx != null and is_instance_valid(fx):
		fx.release()


func _yk_cross_fx(it: Dictionary) -> void:
	## Şimşek Çaprazı: ikinci kesik birincinin önünden geçtiği an kesişme noktasında çıtırdayan mürekkep kıvılcımları
	var R := _reach(it)
	var cp := global_position + Vector2(facing * (R * 0.55 + 8.0), -26.0)
	for i in 4:
		var ang := randf_range(0.0, TAU)
		var l := LightningFX.new()
		l.a = cp
		l.b = cp + Vector2(cos(ang), sin(ang)) * randf_range(12.0, 20.0)
		l.col = YK["col"]
		l.branches = 0
		if FX.root:
			FX.root.add_child(l)
	FX.sparks(cp, Vector2(facing, -0.4), YK["col"].lerp(Color.WHITE, 0.4), 7, 170.0)
	FX.flash_light(cp, YK["col"], 70.0, 1.3, 0.12)


func _yk_flash_fx(it: Dictionary) -> void:
	## Şimşek Çekişi bırakışı: atılışın yolu boyunca ekranı bölen kesik çizgisi, ışık, art arda gölgeler
	var a0 := center() + Vector2(-facing * 10.0, -2.0)
	var b0 := a0 + Vector2(facing * (float(YK["flash_px"]) + _reach(it) + 30.0), 0.0)
	SimsekKesikFX.line(a0, b0, YK["col"], 1.0)
	FX.flash_light(center(), YK["col"], 150.0, 1.6, 0.18)
	Game.zoom_punch(0.02)
	FX.ghost(anim.base, Color(0.6, 0.85, 1.0, 0.45), 0.22)


func _yk_flash_tick(delta: float) -> void:
	atk["flash_left"] = float(atk["flash_left"]) - delta
	if float(atk["flash_left"]) > 0.0:
		velocity.x = float(facing) * float(YK["flash_px"]) / float(YK["flash_t"])
		velocity.y = minf(velocity.y, 0.0)
		if Engine.get_physics_frames() % 2 == 0:
			FX.ghost(anim.base, Color(0.6, 0.85, 1.0, 0.4), 0.18)
	else:
		atk.erase("flash_left")
		velocity.x = float(facing) * 40.0
		FX.dust(global_position, Vector2(-facing, -0.3), 5, 0.26)


func _yk_crack_later(e: Node) -> void:
	## Şimşek Çekişi: vurulan düşmanın tepesinde gecikmeli gök çatırtısı — yalnızca görsel ve ses (hasar / vuruş yok)
	var p0: Vector2 = e.center()
	var t := get_tree().create_timer(float(YK["crack_delay"]), true, false, true)
	t.timeout.connect(func() -> void:
		var p: Vector2 = e.center() if is_instance_valid(e) else p0
		if FX.root == null:
			return
		var l := LightningFX.new()
		l.a = p + Vector2(randf_range(-8.0, 8.0), -78.0)
		l.b = p + Vector2(0.0, 4.0)
		l.col = YK["col"]
		l.width = 2
		FX.root.add_child(l)
		FX.sparks(p, Vector2(0.0, -1.0), YK["col"], 6, 160.0)
		FX.flash_light(p, YK["col"], 90.0, 1.4, 0.14)
		Ses.play("simsek_catirti", -11.0, 1.25, 0.05, 0.02, p)
		Game.shake_dir(0.08, Vector2.DOWN))


func _crit_accent(it: Dictionary, hp: Vector2, col: Color) -> void:
	## v25 kritik vurgusu (sade): kamera 2-3 karede yumuşakça yaklaşır, darbe noktasından vuruş yönünde ince parlak
	## kesik çizgisi (beyaz) + silah renginde kısa çapraz çizgi. Ekran kararması / ters renk yok.
	Game.zoom_punch(0.024 + 0.014 * _weight(it))
	var d := Vector2(float(facing), -0.22).normalized()
	FX.streak(hp - d * 22.0, hp + d * 30.0, Color(1.0, 0.98, 0.92, 0.95), 0.1)
	var d2 := d.rotated(-0.9 * float(facing))
	FX.streak(hp - d2 * 12.0, hp + d2 * 14.0, col.lerp(Color.WHITE, 0.35), 0.08)
	# v26: sesle aynı karede kısa, sert bir "patlama" okuması: beyaz halka + darbe yönünde yelpazelenen dört kısa ışın
	# ve vuruş yönünde küçük sarsıntı (sesin KRAK geçişiyle eş; duraklama süresine dokunmaz)
	FX.ring(hp, 9.0, Color(1.0, 0.97, 0.88, 0.9), 0.1)
	for k in 4:
		var a := d.angle() + (float(k) - 1.5) * 0.42 + randf_range(-0.1, 0.1)
		var dv := Vector2(cos(a), sin(a))
		FX.streak(hp + dv * 7.0, hp + dv * randf_range(20.0, 30.0), Color(1.0, 0.93, 0.7, 0.9), 0.07)
	Game.shake_dir(0.12, Vector2(float(facing), 0.2))


## v28 Yıldırım Hamlesi menzili: "isabet edince çok uzağa gidiyor". Eski: mech_v 110-190 × %60-100 = 66-190 px + isabet
## penceresi bitince 1100 px/sn'lik hız yavaşlayarak ~100 px daha kayıyordu. Yeni: mech_v 65-85 (eski kayıttaki büyük
## değerler 85'e kırpılır) × %85-100 = 55-85 px; ilk isabetten sonra en çok "past" px daha gider (yakın ikinci düşman da
## delinir), hamle bitince gövde "end_v" hızına iner (kaymaz). Dokunulmazlık, delme, yıldırım aynı.
const YK_DASH := {"min": 55.0, "max": 85.0, "past": 30.0, "end_v": 70.0}


func _lightning_dash(it: Dictionary, held: float) -> void:
	## Yıldırım Kılıcı: basılı tutma süresine göre %85-100 menzil; lunge animasyonuyla delici hamle
	var mv := clampf(float(it.get("mech_v", 75.0)), float(YK_DASH["min"]), float(YK_DASH["max"]))
	var px := mv * (0.85 + 0.15 * clampf((held - 0.2) / 0.6, 0.0, 1.0))
	var c := {"s": "lunge", "mult": 1.4, "kb": 60.0, "last": true}
	var sw: Dictionary = SWINGS["lunge"]
	# süre: hamle 1100 px/sn; vuruş fazı bu mesafeyi alacak kadar
	var dur := (px / 1100.0) / (float(sw["hit"][1]) - float(sw["hit"][0]))
	atk = {"step": 0, "c": c, "sw": sw, "phase": "wind", "t": dur * 0.24, "dur": dur, "hit": [], "item": it, "hold": 0.0, "dash_px": px, "pause": false, "multi_i": 0}
	combo_step = 0
	vis_scale = Vector2(0.85, 1.12)
	FX.anim("electric_impact", center(), 0.0, 0.9, Color(0.6, 0.85, 1.0))
	# v25: hamlenin yolu ekranı bir an bölen kesik çizgisiyle parlar (Şimşek Çekişi ile aynı dil)
	SimsekKesikFX.line(center() + Vector2(-facing * 8.0, -2.0), center() + Vector2(facing * (px + 26.0), -2.0), YK["col"], 1.3 if held >= 0.6 else 1.05)
	Game.hitstop(0.05)
	if held >= 0.6:
		# v21 tam şarj: yıldırım oyuncunun durduğu yere değil, hamlenin deldiği her düşmanın tepesine iner
		# (_melee_hits: atk["thunder"]). Burada yalnızca bırakış kıvılcımı ve uzak gürleme.
		atk["thunder"] = 0.85
		FX.lightning(center() + Vector2(0, -18), center() + Vector2(facing * 26, -40), Color(0.7, 0.88, 1.0))
		if Ses.has_method("thunder"):
			Ses.call("thunder", center(), 0.1, -8.0)
	elif Ses.has_method("thunder"):
		Ses.call("thunder", center(), 0.1, -6.0)
	else:
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
	cd[sec_slot] = _sec_cd(it)
	cd_max[sec_slot] = cd[sec_slot]
	cast_t = 0.35
	anim.show_frame("cast", 1)
	vis_scale = Vector2(0.94, 1.06)
	match it["id"]:
		"kam_kopuzu":
			var p := Projectile.new()
			p.team = "p"
			p.kind = "wave"
			p.position = global_position + Vector2(facing * 12, -24)
			p.velocity = Vector2(facing * 280, 0)
			p.pierce = 99
			p.life = 1.2
			p.hit_pad = Vector2(4.0, 22.0)   # v25: dalga boyunca (eskiden tek nokta: alçak kurt altından geçiyordu)
			p.on_hit = func(e: Node) -> void:
				_deal(e, float(it["dmg"]), it, {"kb": 70.0, "dir": facing})
			level.add_projectile(p)
			FX.anim("hush_lock", global_position + Vector2(facing * 14, -28), 0.0, 0.8, Color(0.7, 0.9, 1.0))
		"gok_asasi":
			_gok_asasi(it, mv)
		"yel_borusu":
			FX.anim("leaf_gust", global_position + Vector2(facing * 40, -26), 0.0 if facing > 0 else PI, 1.3, Color(0.85, 1.0, 0.85))
			FX.dust(global_position + Vector2(facing * 30, -10), Vector2(facing, -0.2), 10, 0.36)
			Game.kick(Vector2(-facing, 0), 3.0)
			for e in get_tree().get_nodes_in_group("dusman"):
				if not is_instance_valid(e) or e.dead:
					continue
				var to: Vector2 = e.center() - center()
				if signf(to.x) == facing and absf(to.x) < 135.0 and absf(to.y) < 60.0:   # v25: 110 -> 135 px
					var walled: bool = level.solid_at(e.center() + Vector2(facing * mv * 0.5, 0))
					e.take_hit(float(it["dmg"]) * power, {"kb": mv * 3.0, "dir": facing, "launch": 100.0, "walled": walled, "stagger": true})
					if walled:
						FX.impact(e.center() + Vector2(facing * 10, 0), Vector2(facing, 0), Color(0.9, 1.0, 0.9), 1.2)


## v25 Gök Asası: zincir yıldırım. İlk hedefe gökten şimşek iner, zincir oradan atlar (her sıçrayış %90 hasar, kısa
## sersemletme); her 4. çakış "Gök Gürlemesi": x1,6 hasar, +2 sıçrayış, uzun sersemletme (sersemleyene sonraki
## yıldırım kritik: silahın koşulu). Hedef yoksa önündeki yere iner (yakındakini yine çarpar).
const GOK := {"ilk": 230.0, "dikey": 90.0, "zincir": 150.0, "dus": 0.9, "sers": 0.35, "gur_n": 4, "gur_k": 1.6, "gur_sers": 0.75, "gur_ek": 2}
var _gok_n := 0


func _gok_asasi(it: Dictionary, mv: float) -> void:
	_gok_n += 1
	var gur: bool = _gok_n % int(GOK["gur_n"]) == 0
	var hit: Array = []
	var from_pos := center() + Vector2(facing * 10, -4)
	var cur := from_pos
	var dmg_k := float(GOK["gur_k"]) if gur else 1.0
	var n := int(mv) + (int(GOK["gur_ek"]) if gur else 0)
	var col := Color(0.75, 0.88, 1.0) if not gur else Color(0.9, 0.95, 1.0)
	var first: Node = _uzak_hedef(float(GOK["ilk"]), float(GOK["dikey"]))
	for i in n:
		var best: Node = first if i == 0 else null
		if i > 0:
			var bd := float(GOK["zincir"])
			for e in get_tree().get_nodes_in_group("dusman"):
				if is_instance_valid(e) and not e.dead and not hit.has(e):
					var d: float = cur.distance_to(e.center())
					if d < bd:
						bd = d
						best = e
		if best == null or not is_instance_valid(best):
			break
		hit.append(best)
		if i == 0:
			FX.thunder(best.global_position, 1.4 if gur else 1.0)
		else:
			FX.lightning(cur, best.center(), col)
			if gur:
				FX.lightning(cur + Vector2(0, -6), best.center() + Vector2(randf_range(-8, 8), -10), Color(col, 0.6))
		FX.anim("electric_impact", best.center(), 0.0, 1.0 if gur else 0.8, col)
		_deal(best, float(it["dmg"]) * dmg_k, it, {"kb": 70.0 if gur else 40.0, "dir": signf(best.center().x - cur.x), "stun": float(GOK["gur_sers"]) if gur else float(GOK["sers"])})
		cur = best.center()
		dmg_k *= float(GOK["dus"])
	if hit.is_empty():
		# hedef yok: önündeki yere iner, dibindekini çarpar
		var gx := global_position.x + facing * 110.0
		var gy: float = level.surface_y(int(gx / 24.0), int(global_position.y / 24.0) - 2) * 24.0 if level and level.has_method("surface_y") else global_position.y
		FX.thunder(Vector2(gx, gy), 0.8)
		for e in get_tree().get_nodes_in_group("dusman"):
			if is_instance_valid(e) and not e.dead and e.center().distance_to(Vector2(gx, gy - 14.0)) < 34.0:
				_deal(e, float(it["dmg"]) * 0.8, it, {"kb": 40.0, "dir": facing, "stun": float(GOK["sers"])})
	FX.flash_light(from_pos, col, 220.0 if gur else 180.0, 2.4 if gur else 1.8, 0.25 if gur else 0.2)
	Game.hitstop(0.06 if gur else 0.04)
	Game.kick(Vector2(facing, 0), 3.0 if gur else 1.5)
	if gur:
		Game.shake(3.0)
		Ses.play("yildirim", -3.0, 0.85)
		FX.text(center() + Vector2(0, -42), "GÖK GÜRLEMESİ", Color(0.8, 0.92, 1.0), 9)
	else:
		Ses.play("yildirim", -9.0, 1.25, 0.08)


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


var _label_last := ""
var _label_ms := 0


func _move_label(txt: String, col: Color, sz: int) -> void:
	## Hamle adı: aynı ad kısa sürede yinelenirse üst üste basılmaz
	var now := Time.get_ticks_msec()
	if txt == "" or (txt == _label_last and now - _label_ms < 700):
		return
	_label_last = txt
	_label_ms = now
	FX.text(center() + Vector2(0, -40), txt, col, sz)



# ================================================================== v12: Don, Usul
func _v12_tick(delta: float) -> void:
	usul_buff_t -= delta
	if don_on and Adlar.add_stat("don_sure", delta) >= 30.0:
		Adlar.deed("kam_ata", center())   # v25: Kam Ata destanı don kılığında 30 sn (Üç Âlem kaldırıldı)
	if Input.is_action_just_pressed("don") and not don_on and wolf_t <= 0.0:
		if don_kind != "":
			_begin_don()
		else:
			FX.text(center() + Vector2(0, -44), "Emilecek ruh yok: bir seçkin devir", Color(0.8, 0.7, 0.95), 7)


func _usul_press() -> bool:
	## Saldırı tuşu usulün vuruşuna denk geldi mi? (müziğin aksak usulü: 9/8, 7/8, 5/8, halay)
	var u := Ses.usul_now()
	if u.is_empty():
		return false
	var win := 0.085 + (0.035 if Adlar.earned("kopuzcu") else 0.0)
	if absf(float(u["d"])) <= win:
		usul_streak += 1
		usul_buff_t = 0.5
		usul_strong = bool(u["strong"])
		var col := Color(1.0, 0.85, 0.45)
		# v22: halka küçük; "USUL" yazısı her vuruşta değil, 4'ün katlarında (hızlı kombolarda yazı yığılıyordu)
		FX.ring(center(), 12.0 + (6.0 if usul_strong else 0.0), col, 0.18)
		Ses.play("usul_dum" if usul_strong else "usul_vurus", -3.0, 1.0, 0.02, 0.05)
		if usul_streak >= 4 and usul_streak % 4 == 0:
			FX.text(center() + Vector2(0, -64), "USUL x%d" % usul_streak, col, 7)
		if usul_streak % 8 == 0:
			Ses.play("usul_seri", -2.0)
			add_kut(6.0)
			FX.ring(center(), 60, col, 0.4)
			FX.burst(center(), col, 16, 80, 0.5, 0.18, -40, true)
		if usul_streak >= 12:
			Adlar.deed("kopuzcu", center())
		return true
	usul_streak = 0
	usul_buff_t = 0.0
	return false


func usul_mult() -> float:
	return 1.15 + 0.025 * minf(usul_streak, 12) + (0.15 if usul_strong else 0.0) + (0.1 if Adlar.earned("kopuzcu") else 0.0)


func gain_don(k: String) -> void:
	don_kind = k
	var nm := String(Data.enemy_def(k).get("name", k))
	FX.text(center() + Vector2(0, -46), "DON: %s  [G]" % nm, DonForm.COL, 9)
	FX.soul(center(), DonForm.COL, 20)
	FX.ring(center(), 30, DonForm.COL, 0.3)
	Ses.play("don_al", -1.0)


func _begin_don() -> void:
	_cancel_attack(false)
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
	anim.visible = false
	arm_root.visible = false
	weapon.visible = false
	shield_spr.visible = false
	don_on = true
	don.begin(self, don_kind)
	don_kind = ""
	Ses.play("don_donus", 0.0)
	Game.shake(4.0)
	Game.slowmo(0.3, 0.25)
	FX.anim("void_implosion", center(), 0.0, 1.2, DonForm.COL)
	FX.ring(center(), 70, DonForm.COL, 0.45)
	FX.soul(center(), DonForm.COL, 24)
	FX.text(center() + Vector2(0, -50), "DON: " + don.display_name().to_upper(), DonForm.COL, 11)
	if Adlar.add_stat("don") >= 3.0:
		Adlar.deed("donen", center())


func _end_don() -> void:
	don_on = false
	don.visible = false
	anim.visible = true
	anim.set_facing(facing)
	inv_t = maxf(inv_t, 0.5)
	FX.anim("smoke_puff", center(), 0.0, 1.0, DonForm.COL, true)
	if don.anim:
		FX.ghost(don.anim.base, Color(DonForm.COL, 0.5), 0.35)
	Ses.play("don_bitis", -2.0)
