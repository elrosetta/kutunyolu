# Kut'un Yolu: tasarım ve proje rehberi

Türk mitolojisinde geçen, Dead Cells esinli 2D aksiyon roguelite. Motor: **Godot 4.7.2** (Forward+), hedef: **Windows PC / Steam**.

## Hikâye

Gök Tengri dünyayı üç kat yarattı: Gök, Yer ve Yeraltı. Üçünü Ulu Kayın (Hayat Ağacı) bir arada tutar. Ağacın damarlarından dünyaya akan hayat bereketine **Kut** denir.

Erlik Han ağacın köklerine kara bir zincir doladı. Kut çekiliyor, iyeler azıyor, ölüler dinlenemiyor.

Kahraman **Bengü**, Erlik'in ordusuna karşı düşmüş son alplardan biri. Umay Ana onu ağacın özünden yeniden yoğurdu. Bengü her ölümde yeniden doğar, ama her doğuş ağaçtan bir yaprak koparır. Roguelike döngüsünün hikâyedeki karşılığı budur.

Hikâye metinleri `data/story.json` dosyasında: giriş, Umay Ana / Demirci Kam / Ozan konuşmaları, biyom anıları.

## Sanat yönü: Kara Gün

Güneş doğmuyor; dünya ay ışığında. Ortam soğuk ve loş (CanvasModulate mavimsi, DirectionalLight2D = ay). Sıcak renk
yalnızca ateşten gelir: çıralar, od testisi, Bengü'nün Kut ışığı. Karakterler ve silahlar renkli kalır, çevre
desaturedir; böylece oyuncu ve tehdit her zaman öne çıkar (Dead Cells'in Prisoners' Quarters mantığı).
Arka plan: kara bulutlar, ölü ağaçlar, ruh ışıkları (`WISP`), zeminde süzülen sis (`otuken_5_fog.png`, zamanla kayar).

## Dövüş hissi ve efekt katmanı (`scripts/core/FX.gd`)

Dead Cells'in "her vuruş bir olay" ilkesi: darbe yıldızı (`ImpactFX`), yöne saçılan kıvılcım, düşmana özgü
sıçrantı (`Enemy.BLOOD`), kılıç izi şeridi (`WeaponTrail`, kareler arası açı ara-örneklenir), hayalet izler
(`FX.ghost`: yuvarlanma, hücum, Bozkurt Ruhu), toz (koşu, iniş, kayma, yuvarlanma), ruh zerreleri ve savrulan
gövde (`Corpse`) ölümde, anlık ışık parlaması (`FX.flash_light`), yere yatık şok halkası (`FX.ring` aspect).
Zaman: `Game.hitstop` (gerçek zamanlı, üst üste biner) ve `Game.slowmo` (kritik, öldürme, savuşturma);
kamera: `Game.shake` + `Game.kick` (darbe yönünde itiş).

Karakter hissi (`Player.gd`): squash & stretch (`vis_scale`: zıplama, iniş, vuruş, hasar), hız yönünde eğilme
(`vis_lean`), tepe noktasında kısa asılı kalış, kayma tozu, iniş toparlanması. Animasyonlar `bengu.py`'de
anahtar kareli (`keyed`) 5-6 karelik pozlardır: hazırlık → vuruş → aşma → toparlanma.

**Silaha özgü kombolar** (`Player.COMBOS`, eşya kimliğiyle; yoksa türe düşer):
alp kılıcı: kesik-kesik-tepeden (3. vuruş kritik) · pala: kesik-kesik-**çevrinti** (iki yan) · yatağan: 3 hızlı
kesik + **hücum saplaması** (içinden geçer) · teber: geniş kesik, **yükselen kesik** (havaya fırlatır), ezici iniş ·
gürz: **şarjlı** tek darbe (basılı tut; sarsıntı genişler) · kargı: iki saplama + süpürme · ikiz bıçak: 4 hızlı kesik +
**çift vuran çapraz**; kombo ilerledikçe hızlanır.

**Yuvarlanma ve tüneller:** yuvarlanırken çarpışma kutusu 12×20'ye iner; tavan alçaksa yuvarlanma kendiliğinden
sürer (sürünme). Alçak geçitler bilinçli tasarım öğesidir.

## İlerleme: derinlik, tılsım, parşömen

* **Kut Kapısı → sonraki derinlik:** `Game.next_depth()`; eşyalar, ongunlar, can korunur, şişeler dolar,
  `tier` artar (düşman canı/hasarı ve eşya nadirliği). HUD'da "N. derinlik".
* **Tılsımlar** (`Pickup.kind == "tilsim"`): her bölümde üç tane (ikisi yolda, biri havadaki adada). E ile
  seçim ekranı: Kurt / Kartal / Ayı +1 (ongun çarpanı +%15) ve can artışı (+%6 / +%6 / +%15).
* **Parşömenler** (`Pickup.kind == "parsomen"`): çalışan ama açılmamış bir eşyanın tarifi; seçkinlerden kesin,
  diğerlerinden %7. Dokununca `Game.meta.blueprints`'e girer. Ölünce ya da kapıdan geçince koşudaki Kut
  `Game.meta.kut_bank`'a aktarılır. Koşu başında (hikâyeden / ölümden sonra) **Demirci Kam Kuzgun** ekranı:
  Kut karşılığı aç (`Game.unlock`); açılanlar düşme havuzuna katılır (`ItemGen.unlocked`).
  Başlangıç havuzu `Game.BASE_UNLOCKED`.

## Test ve çekim

`--otomatik`: kendi kendine ilerleyen oyuncu (duvara takılınca çift zıplar + yuvarlanır; tılsım/demirci/kapı
otomatik geçilir). `--sahne`: düz arenada dövüş gösterisi (silahlar sırayla değişir, düşmanlar düzenli gelir);
`--write-movie` ile çekip GIF yapmak için.

## Dış kaynaklı efektler (CC0)

`assets/fx/anim/*` PVFX Foundry Thirteen (nerijs, CC0) kare animasyonları: `AnimFX` düğümü oynatır (`FX.anim(ad, konum, dönüş,
ölçek, renk, toplamalı, aynala, takip)`). Kullanım: `crescent_slash` savuruş hilali, `electric_impact` kritik/şimşek,
`solar_shrapnel` darbe, `warm_explosion` bomba, `landing_dust` iniş, `smoke_puff` ölüm, `earth_rupture` yer şoku,
`frost_nova` donma, `acid_splash` spor, `arcane_parry` savuşturma, `focus_charge` şarj, `radiant_heal` şişe/muska,
`leaf_gust` rüzgâr/Arçura, `rift_portal` Kut Kapısı, `tether_catch` kement/zincir/yakalama, `mass_release` saplama.
`assets/fx/k_*.png` Kenney Particle Pack (CC0) dokuları: kıvılcım çizgileri (`k_spark`, hız yönüne hizalı), yıldız
parıltısı, duman, toz, alev. `FX.fire`, `FX.smoke`, `FX.lightning` (Gök Asası). Lisanslar: `assets/fx/LICENSES.txt`.

## Saldırı animasyonu ilkeleri (`bengu.py`)

8 kare: 0-1 hazırlık (ikincisi daha derin ve tutulur), 2-5 vuruş (4 = darbe anı), 5 aşma, 6-7 toparlanma.
Dirsek hazırlıkta bükülü (`af[1]` ≈ 1.5-2.2), darbede gergin (0.0); ön kol darbede %15-30 uzar (`ext`, abartı);
ön omuz vuruş yönüne kayar (`sx`, gövde burulması); arka kol ters salınır; kalça öne adım atar (`hx`).
Godot tarafı: silahın solan kopyaları (smear) + `WeaponTrail` şeridi + `crescent_slash` hilali.

## Bölüm çeşitliliği (`LevelGen.gd`)

Her koşuda stil seçilir: **orman** (tepeler, adalar), **uçurum** (teraslar, derin çukurlar, basamak platformlar),
**mağara** (tavan bantları, sarkıt sütunlar, 1 karolu sürünme geçitleri, gökyüzü ağızları), **harabe** (çökmüş kule
kuyuları, zikzak tırmanış, taş duvarlar). Üstüne 2-4 elle tasarlanmış parça (`CHUNKS`: sürünme geçidi, sütunlar,
çukur, merdiven, kemer, kule, basamak, mezar) basılır. `_reachable` basit zıplama modeliyle girişten çıkışa yol var mı
denetler; yoksa yeniden üretir. Düşman karışımı ve süs yoğunluğu stile göre değişir. `--tohum=N` ile sabit tohum.

## Silah mekanikleri (48 eşya çalışıyor)

* **Yıldırım Kılıcı** (katana tarzı): sol tuşa basılı tut (şarj), bırak: 110-190 px şimşek hamlesi; yoldaki her
  düşmanı deler, ikinciden itibaren kritik. Kısa dokunuş: iki hızlı kesik.
* **Gelişmiş sürümler** (`upgrade_of`, `min_tier`): Türk Yayı → Sağanak Yayı (3-4 ok) → Tufan Yayı (5-6 ok);
  Akıncı Yayı → Od Okları; Alp Kılıcı → Ayaz Kılıcı; Gürz → Çivili Topuz; Teber → Erlik Tırpanı; İkiz Bıçak → Kurt
  Pençeleri; Kement → Od Kamçısı; Kam Kopuzu → Gök Asası; Cirit → Kartal Tüyleri; Çoban Sapanı → Mancınık Taşı.
  Yalnızca yeterli derinlikte düşerler ve kartta "▲ ...'nın gelişmiş hali" yazar.
* Diğerleri: Savaş Baltası (2. basışta fırlat, geri döner), Kement (çeker), kırbaç türü, sihir türü (kopuz dalgası, Gök
  Asası zincir şimşek, Yel Borusu itme), kalkanlar (diken, şifa, ejder alevi, kök, taş), teçhizat (şifa muskası, ayaz
  tılsımı, yel tılsımı, davul totemi, ok yağmuru, kartal çağrısı, ruh kuşu, Umay'ın tüyü, Erlik'in zinciri).

## Yaratıklar

Arçura (yanıltıcı: iki hayalet kopya salar, arkana ışınlanır, lanetli spor atar), Şürale (yakalar, gıdıklar,
fırlatır; 4 tuş basışıyla kurtulursun). Kurt sürüsünde ikinci kurt arkadan dolaşır; Çor tependeyken dalış yapar;
Balbal önden gelen vuruşta siper alır (%30 hasar); Ağaç İyesi üç kök dalgası gönderir.

## Kahraman ve kol iskeleti (v3)

Bengü yeniden tasarlandı: kurt başlı insansı (büyük kurt kafası, kırmızı kaftan, deri kemer, koyu şalvar, turkuaz atkı);
ayrıntı azaltıldı, renk blokları büyütüldü. Ön kol silahlı durumlarda sprite'a çizilmez: `bengu_kol.png` (üst kol,
ön kol, yumruk) oyunda omuz çapasından (`sh_f`) 60 FPS sürülür; silah yumruğun içindedir (yumruk silahın üstünde çizilir).
Dead Cells da animasyonları iskelet + anahtar pozlarla üretip sprite'a çevirir; buradaki kol iskeleti aynı mantıktadır.

`Player.SWINGS`: savuruş eğrileri `[t, a1, a2, w, k, ext, ease]` (a1 üst kol, a2 dirsek, w bilek; 0 aşağı, pi/2 ileri,
pi yukarı; k yatay kısalma; ext ön kol uzatması; ease 1 = hızlanarak vuruş, 2 = yavaşlayarak takip).
Tipler: down (yukarıdan aşağı), up (aşağıdan yukarı), horiz (soldan sağa, kameraya doğru kısalarak), back (sağdan sola,
ters el), thrust, lunge, heavy, spin, rise (havaya atar), flurry (3 saplama), slam (sıçrayıp ezme), axe (fırlatma).
Tek efekt: `WeaponTrail` gerçek bıçak ucunu kareler arası 4 ara örnekle izler (gövde + uçta beyaz çekirdek); saplamalara
`FX.streak` hız çizgisi. Ağır silahlar (`HEAVY`) daha uzun duraklama, daha sert kamera ve ileri adım.

`Player.COMBOS`: her silahın `chain` (art arda basış) ve `pause` (iki vuruş + 0,28-0,95 sn bekleme + basış) bitirişi;
bekleme bitirişi hazır olunca yumrukta parıltı, başlarken adı yazılır, vuruşta ağır çekim. `--savurus` her savuruşu
tek tek sergileyen laboratuvar modudur.

## Durum efektleri

Yanma (turuncu titreşim, alev + duman), donma (buz bloğu kaplaması, sarkıtlar, animasyon durur, buz parıltıları),
zehir (yeni: yeşil nabız, kabarcıklar, 5'e kadar yığılır; `zehirleme` ek özelliği, Erlik Tırpanı, Çor sporları oyuncuyu
da zehirler), kanama (damlalar). Başın üstünde durum simgeleri (`StatusOverlay`).

## Yaylar

Türk Yayı (kırmızı lak, kemik siyah), Akıncı (siyah lak, altın şerit, at kılı püskül), Sağanak (çift kat, 3 ok),
Tufan (turkuaz, kartal başlı uçlar, 5 ok), Od Okları (alev uçlar, kor taşı). Oklar yay başına iz rengi ve uçuş efekti
taşır: tam gerilmiş ok altın kıvılcım, od alevi + duman, sağanak/tufan mavi rüzgâr; çarpınca türüne göre patlama.

## Geçilebilirlik garantisi

`LevelGen._ensure_path`: 3+ karo yükselişe 3 karo genişliğinde basamak platformları, yükselişlerde baş boşluğu, düz/iniş
geçişlerinde en kötü 1 karo yuvarlanma geçidi. Tek zıplama 3,2 karo, çift zıplama ~5,5 karo. `--dok=yol.png` ızgarayı
PNG olarak döker.

## Biyomlar ve derinlik (v4)

`tools/artgen/biomes.py` her biyomun toprak paletini, oyun içi ışık/parçacık/süs ayarlarını (`art`) ve düşman
reskinlerini (`RESKIN`: biyom düşmanı → temel sprite + renk tonu) tanımlar; `bg_biomes.py` paralaks katmanlarını üretir.
Derinlik → biyom (`data/world.json` "depths"): 1-2 Kararan Ötüken (gece), 3-4 Bozkır Kurganları (gündüz), 5-6 Şahmeran
Mağarası (kristal mağara), 7-8 Kaf Dağı (karlı şafak), 9+ Erlik'in Ülkesi (lav gecesi). `Level.art` okur: karo seti
`assets/tiles/<biyom>*`, arka plan `assets/bg/<biyom>_*`, ortam/güneş rengi, doygunluk, parçacık türü (ruh/polen/spor/
kar/kor), süs listesi ve tonu, çıra ve kapı rengi, izin verilen harita stilleri. `--derinlik=N` test içindir.
`python export_assets.py bozkir kaf` yalnızca verilen biyomların dokularını üretir.

## Bozkurt biçimi

Kut dolunca F: 9 sn boyunca büyük ruh kurdu (`bengu_kurt`, 160×112; çizim `tools/artgen/bozkurt.py`). J ısırık zinciri (3. ısırık fırlatır ve kritik),
K ya da Shift sıçrayış (640 px/sn, yoldaki herkesi devirir, dokunulmaz), F uluma (140 px sersemletme, +1 sn süre).
Her ısırık +0,3 sn verir. Hasar alma %40 azalır. Süre bitince duman ve kısa dokunulmazlıkla insan biçimine dönülür.

## Geçilebilirlik (v4)

`LevelGen._reach`: fizik sadık model (2 karo boy, sürünme 1 karo, 5 karo çift zıplama, baş boşluğu, yörünge tepe
satırı). Geçilemiyorsa `guarantee()` takılan noktadan sağa 7 karolik koridor açar (`carved` sayacı günlükte).
Açık eşya havuzu: yalnızca `upgrade_of` olanlar parşömenle açılır; diğer her şey baştan düşer.

## Yeni silahlar

Ulu Kılıç (dev kılıç, 48 px erim, iki düşmana denk gelirse kritik), Dağ Çekici (dev çekiç, en geniş sarsıntı, havadaki
düşmanı yere çakar), Ruh Kılıcı (her kesik uçan ruh hilali salar), Ay Palası (ikiz hilal, beşli zincir, zincir sonunda
dokunulmazlık). `Player.COMBOS` içinde.

## Silaha özgü savuruşlar ve ağır saldırı (v5)

`Player.SWINGS` 33 savuruş içerir; v5 ile eklenenler: diag_down, diag_up, cross_x (X kesik, 2 vuruş), overhead_2h, ground_drag
(kılıç yerde sürüklenir, kıvılcım saçar), sweep_low (diz hizası), reverse_grip (ters el), twirl (bilek çevrimi, 2 vuruş), windmill
(baş üstü tam tur), pole_thrust / pole_sweep (sırık), reap (önden geriye biçme), rake (iki tırmık), whip_crack, axe_hook, iai
(kalçadan çekiş), uppercut_2h, slam_2h, stab_heavy, helicopter (iki tam tur, iki yan). Her silahın `COMBOS` zinciri ve bekleme
bitirişi kendine özgüdür (ör. Yatağan ters el → düz → ters el → hücum; Ulu Kılıç yerde sürükle → iki elli iniş; Tırpan biç → alçak
süpür → çark).

**Ağır saldırı:** saldırı tuşu basılı tutulunca hazırlık bitiminde `HOLD_T` (0,16 sn) beklenir; hâlâ basılıysa `HEAVIES` tablosundaki
özgün ağır savuruşa geçilir ve `HEAVY_MAX` (0,85 sn) boyunca şarj olur (silaha kıvılcım akar, dolunca parlama + ad yazısı). Bırakınca
vuruş: hasar `mult × (1 + şarj × 0,9)`, iz daha geniş/beyaz, hitstop 0,09-0,13 sn, sert kamera. Kısa dokunuş her zaman normal zinciri
sürdürür (gecikme en çok 0,16 sn). Yıldırım Kılıcı'nın şimşek hamlesi artık bu yoldan çıkar.

**Silaha özgü darbe efektleri:** `Player.WFX` iz genişliği/rengi, PVFX darbe animasyonu ve ek parçacığı (kan, od, buz, ruh, toz,
hayalet) tanımlar; `_wind_fx` hazırlık efektlerini (sürüklenme kıvılcımı, çekiş parlaması, çark izi) verir.

## Bölüm yapısı ve Ulu Kayın yurdu (v6)

Her derinlik bir "bölüm"dür. Düşmanlar **Kut tanesi** düşürür (Dead Cells hücreleri: her düşman ≥1, seçkin 4, %30 fazladan);
taneler koşu boyunca taşınır ve HUD'da `kut (banka)` olarak görünür. Bölüm sonundaki Kut Kapısı seni **Ulu Kayın yurduna**
(`Level.build_hub`, düşmansız düz alan; dev ak kayın, ocak, çadır) götürür. Yurt sakinleri (`NPC.gd`, E ile konuş):
- **Umay Ana** — taşınan Kut'u bankaya alır; kalıcı armağanlar (`Game.UMAY`): Umay'ın Şişesi (+1 şişe), Kayın Özü (+%10 can),
  Ruh Düğümü (ölünce Kut'un %30/%60'ı kalır), Ata Kesesi (+60 altın), Bozkurt Çağrısı (Kut %20 hızlı), Demirci Dostu (başlangıç silahı üstün).
- **Demirci Kam Kuzgun** — parşömenleri Kut karşılığı döver (eski Demirci ekranı).
- **Ozan Bilge Kopuz** — destan satırları ve koşu özeti.
Yurttaki kapı bir sonraki derinliğe indirir. **Ölünce taşınan Kut yitirilir** (Ruh Düğümü yoksa). Test: `--yurt` yurtta başlatır.

## Ses (`tools/audiogen`, `scripts/autoload/Ses.gd`)

**v8 — gerçek kayıt katmanları:** `layer.py`, CC0 kayıtları (Kenney Impact Sounds + RPG Audio, OGA Swishes, OGA RPG Sound Pack,
Air whoosh; bkz. `assets/audio/LICENSES.txt`) perde/kesme/karıştırma ile silah sınıfına göre katmanlar: savuruşlar
`savur_kilic/katana/dev/cekic/balta/sirik/bicak/kirbac/ruh`, darbeler `darbe_kesik/kesik_agir/kunt/cekic/delme/balta/kirbac/tas/metal/kritik`.
`Player.WSND` silah → sınıf; `_swing_sfx` saplama/ağır/iai'ye göre, `_hit_sfx` büyüklük ve kritiğe göre seçer (düşman yalnızca kendi
sesini verir; `opts.sfx_done`). Yaratık sesleri gerçek hırlama/dev/böcek kayıtları; adımlar biyoma göre çim/kar/taş; altın/şişe/eşya/arayüz gerçek.

Bütün sesler prosedürel: `synth.py` (gürültü bantları, FFT süzgeci, Karplus-Strong kopuz, yankı), `sfx.py` (70 efekt: savuruşlar
hafif/ağır/dev/saplama, darbeler et/ağır/kritik/metal/künt/taş, yaratık acı-ölüm sesleri türe göre, kahraman, şarj döngüsü, Bozkurt
dönüşüm/uluma/ısırık, yay, patlama, büyü, yıldırım, donma, zehir, toplama, arayüz, kapı, NPC), `music.py` (Hicaz/Hüseyni makamında
kopuz + davul + rüzgâr; biyom başına döngü: otuken, bozkir, sahmeran, kaf, tamu + yurt + baslik). Üretim: `python tools/audiogen/export_audio.py`.
`Ses.play("savur_hafif")` önekten varyant seçer, perde oynatır; `Ses.loop_start/stop` şarj uğultusu; `Ses.music(biyom)` çapraz geçiş.

## Silah hissi (v7)

- **Çift kol iskeleti:** gövde sprite'ları artık silahlı animasyonlarda iki kolu da çizmez; arka kol da üç parça
  (`bengu_kol.png` 4-6) olarak sürülür. İki elli silahlarda (`Player.TWO_HANDED`: ulu kılıç, çekiçler, gürzler, teber, kargı,
  tırpan, balta) arka el analitik IK ile kabzanın gerisine yerleşir; tek elli silahlarda gövde animasyonunun kaydettiği açılarla
  (`arm_b`) hareket eder. Yay çekerken arka el kirişi çeker.
- **Kesik sprite'ları** (`tools/artgen/slashfx.py` → `assets/fx/slash`): arc / arc_thin / arc_heavy / arc_short / line / ring / x.
  Omuz merkezli, bıçak ucundan geçecek ölçekte, savuruşun yönüne göre döndürülür/aynalanır (`Player._slash_fx`). İz şeridi
  artık inceltildi; kesik sprite'ı ana efekt.
- **Darbe sprite'ları:** impact_cut / blunt / pierce / magic silah sınıfına göre (`_impact_kind`). Kalıcı **çıkartmalar**
  (`FX.decal`, `Level.decal_root`): kan sıçrantıları (ölüm) ve yer çatlakları (çakma) 10-12 sn kalır, en çok 60.
- **Düşman tepkileri:** 140+ geri itmeyle duvara çarpan düşman ek hasar alır, kıvılcım + hitstop + sersemleme (`_wall_slam`);
  havaya fırlatılan düşman hızlı düşerse bir kez seker. Kritik/seçkin ölümünde kamera yakınlaşma darbesi (`Game.zoom_punch`).
- **Yeni silahlar:** Yılan Kılıcı (her vuruş zehir yükü, bitirişte üç zehir hilali), Kor Çekici (çakmalar kor gölü bırakır),
  Rüzgâr Kılıcı (her üçüncü kesik yel bıçağı salar, havadaki düşmana kritik).

## Vuruş hissi (v6)

Düşman darbe tepkisi: darbe yönünde ezilme + yatma (`_hit_tilt`), büyük vuruşlarda darbe çizgileri (streak), kritikte ağır çekim;
her ölümde kısa hitstop; ağır saldırı tam şarjda ekran beyaz parlaması (`Level.flash_white`) + sarsıntı. Tüm bunlar seslerle eşleşir.

## Dünya (`data/world.json`)

| Biyom | Palet | Boss |
|---|---|---|
| Kararan Ötüken | kurşuni gece mavisi, solgun ay gümüşü, kararmış yeşil; sıcak renk yalnızca ateşte | Kara Börü Han |
| Bozkır Kurganları | mor gök, yanık turuncu | Tepegöz |
| Çini Saray Harabesi | kobalt, turkuaz, mercan | Albastı Ana |
| Şahmeran'ın Mağarası | ışıldayan yeşil, mor | Şahmeran |
| Kaf Dağı Yamaçları | buz mavisi, pembe şafak | Yelbegen |
| Erlik'in Ülkesi | mor ateş, kızıl lav | Erlik Han |

Altı biyomda 36 yaratık tasarlandı. Örnekler: Kara Börü, Çor, Ağaç İyesi, Balbal, Arçura, Şürale, Yek, Al Atlı, Gulyabani, Karakoncolos, Erlik'in Kızı. Her bossun üç evresi yazıldı.

## Eşya sistemi (`data/items.json`)

- **Temel eşyalar (toplam 50):** 14 yakın dövüş, 12 uzak silah, 8 kalkan, 16 teçhizat. Her birinin kendine özgü bir mekaniği ve kritik koşulu var. Örnek: Akıncı Yayı geri çekilirken atılan oka kritik verir; buna Part atışı denir.
- **Ongun (stat totemleri):** Bozkurt yakın dövüşü, Kartal uzak silah ve teçhizatı, Ayı dayanıklılığı güçlendirir.
- **Malzeme (11 tür):** Demir, Tunç, Gümüş, Altın, Kemik, Yeşim, Kara Taş, Od Taşı, Ayaz, Gök Demiri, Ruhani. Her biri statları ve rengi değiştirir ve kendi özelliğini getirir.
- **Nadirlik (4 kademe):** Sıradan, Nadir, Destansı, Efsanevi. Kademe, kaç ek özellik geleceğini belirler.
- **Ek özellikler ve kusurlar:** 24 ek özellik var; değerleri her düşüşte yuvarlanır. Kusurlu silahlar karşılığında %15 daha güçlüdür.
- **Kalite yüzdesi:** Her düşüşte hasar, hız, kritik, mekanik değeri ve özellikler yeniden yuvarlanır. Kalite yüzdesi o düşüşün ne kadar iyi geldiğini gösterir.
- **Uygulama durumu:** `"impl": true` olanlar oyunda çalışıyor, diğerleri sırayla eklenecek.

## Kontroller

| Eylem | Klavye / fare | Oyun kolu |
|---|---|---|
| Hareket | A/D, ←/→ | Sol çubuk |
| Zıpla (çift) | Boşluk | A |
| Platformdan in | S + Boşluk | Aşağı + A |
| Yakın saldırı (basılı tut: ağır saldırı) | J / sol tık | X |
| Yay / fırlatma / kalkan | K / sağ tık (yay: basılı tut) | Y |
| Yuvarlan (dokunulmaz) | L / Shift | B |
| Teçhizat 1 / 2 | U / I | LB / RB |
| Kut gücü (Bozkurt Ruhu) | F | Sağ çubuk tık |
| Şifa şişesi | Q | Sol çubuk tık |
| Eşya al / değiştir | E | Back |
| Duraklat | Esc / P | Start |

## Sanat hattı (`tools/artgen`)

Görseller Python ile üretilir; Dead Cells'in 3D'den piksel sanata giden yaklaşımının 2D bir benzeri kullanılır.

1. Karakterler yükseklik alanlı parçalardan (kapsül, elips, eğimli çokgen) bir iskelete kurulur. Pozlar ileri kinematikle hesaplanır.
2. Cel gölgeleme 3 sert tonla yapılır: gölge, ana ton, ışık. Gölgeler maviye, ışıklar sarıya kayar. Titreme (dither) kullanılmaz.
3. Desenler (kilim süsü, kürk, kabuk damarı) piksel başına malzeme değiştirerek eklenir.
4. Her sprite için bir **normal map** ve ayrı bir **parlama** katmanı üretilir. Oyunda `shaders/toon_light.gdshader` 2D ışıkları 3 banda böler.

Yeniden üretmek için:

```bash
cd tools/artgen
python export_assets.py
```

Ardından Godot varlıkları yeniden içe aktarır.

**Sanatçı çizimleriyle değiştirmek:** `assets/sprites/<ad>.png` (renk), `<ad>_n.png` (normal map) ve `<ad>_e.png` (parlama) dosyalarını aynı ızgara düzeniyle değiştirmek yeterli. Kare boyutu, ayak noktası, FPS ve el çapaları `<ad>.json` içinde. Karolar, süsler, silahlar ve arka planlar da aynı mantıkla çalışır.

## Kod yapısı

- `scripts/autoload/`: `Data` (veri ve doku önbelleği), `Game` (koşu, kayıt, tuşlar, sarsıntı), `ItemGen` (eşya yuvarlama)
- `scripts/actors/`: `Player`, `Enemy` (4 yapay zekâ), `Projectile`, `SpiritWolf`
- `scripts/world/`: `Level` (arazi üretimi, karolar, ışık, yerleşim), `ParallaxBG`, `Pickup`, `FirePool`, `RootSpikes`, `KutGate`, `GroundMarker`
- `scripts/core/`: `SpriteAnim` (JSON güdümlü animasyon + normal map + parlama), `FX`, `SlashArc`, `RingFX`
- `scripts/ui/HUD.gd`: arayüz, eşya karşılaştırma kartı, başlık, hikâye ve ölüm ekranları

Otomatik test: `godot --path . -- --otomatik` komutu oyunu kendi kendine oynatır (koşar, saldırır, zıplar, teçhizat kullanır) ve durum satırları yazdırır.

## Steam yolu (özet)

1. **Steamworks:** Partner hesabı ve uygulama başına 100 USD'lik Steam Direct ücreti. Mağaza sayfası, kapsül görselleri ve fragman hazırlanır.
2. **Dışa aktarma:** Godot dışa aktarma şablonları (export templates) indirilir. Windows Desktop ön ayarıyla `.exe` alınır.
3. **Steam entegrasyonu:** GodotSteam eklentisiyle başarımlar, bulut kayıt ve Steam Deck desteği eklenir.
4. **Deck uyumu:** 1280x800 çözünürlükte tam oyun kolu desteği; kontroller zaten hazır.

## Sıradaki adımlar

1. Bölümleri elle tasarlanmış oda şablonlarıyla birleştirmek. Dead Cells'teki %50 elle, %50 prosedürel yaklaşım; açık alanlar ve iç mekânlar karışık olacak.
2. Kara Börü Han boss dövüşü, Ulu Kayın merkezi (Umay Ana, Demirci, Ozan) ve kalıcı ilerleme.
3. Uygulanmamış silah, kalkan ve teçhizat mekaniklerini tamamlamak.
4. Bozkır Kurganları biyomu: yaratıklar, karolar, arka plan.
5. Ses ve müzik: kopuz, davul ve gırtlak (hoomei) dokulu bir müzik.
