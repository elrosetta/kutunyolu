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

### Gölge ve hacim (derinlik katmanı)

Hiçbir şeyin gölgesi yoksa her şey kâğıt çıkartması gibi yüzer; üç katman bunu kırar:

* **Temas gölgesi** (`scripts/core/GroundShadow.gd`): her aktör ve yerdeki eşyanın ayağının altında keskin,
  iki tonlu piksel elips (çekirdek ≈ 0,55 + 1 px kenar 0,30; mürekkep `(0.03, 0.02, 0.06)`). Her kare altındaki
  zemini/platformu arar (`Level.ground_at`, 4 px adım, 160 px), yükseldikçe küçülür ve solar (140 px'te yok),
  ay yönüne hafifçe kayar. `SpriteAnim.setup` sahibinin (get_parent) ilk çocuğu olarak ekler (oyuncu, düşman,
  boss, NPC, kılık, ruh kurdu); `Pickup` kendi ekler (`SHADOW_W`). Genişlik: `size.x × 0,9` ya da kare genişliği
  × 0,25 (`shadow_w` meta ile ezilir); SpriteAnim ölçeğiyle çarpılır (seçkin, ezilme/esneme). Sahibiyle aynı z'de
  ama sprite'tan önce çizilir; ölü/görünmez sahipte çizilmez; ışıktan etkilenmez.
* **Ay gölgeleri** (`Level.moon_occluded`, `GroundShadow._update_moon_shade`, toon_light `moon_shade`): motorun ay gölgesi
  KAPALI. Yan kesitte basamakların gölgesi toprağın içine uzun çapraz şeritler düşürüyordu; Godot'da gölgeyi alan öğe
  seçilemiyor (`shadow_item_cull_mask` engelleyicileri seçer, TileMapLayer `light_mask`'i çizime aktarmıyor). Bunun yerine
  her aktörün gövde ortasından aya doğru ışın karo ızgarasında yürütülür (yarım karo adım, 1400 px, 3 karede bir); katıya
  çarparsa (çıkıntı altı, yar dibi, mağara) toon_light yönlü ışığın `art.shadow` (0,72) payını keser, 0,2 sn yumuşak geçiş.
  Noktasal ışıklar (çıra, Kut) etkilenmez. Oyuncuda gövde, kol ve silah birlikte (`Player.set_moon_shade`). Toprak ay
  ışığını gölgesiz alır. Karo engelleyicileri (`_tile_occluders`) yalnızca büyük sabit süs ışıklarının gölgesi için durur.
  Ortam tabanı × `ambient_k` (0,8), ay enerjisi × `sun_k` (2,5); yön biyomun `sun_rot`'undan.
* **Shader hacmi** (`toon_light.gdshader`, `ground.gdshader`): 3 bant korunur; `spec_band` (0,92) üstünde
  +%15 beyaza çalan parlama, normal map'te siluete yatık (`NORMAL.z < rim_edge` 0,9) ve ışığa dönük piksellerde
  1 basamak kenar ışığı (`rim_gain` 0,3). Zeminde "lit" anahtarlı karo üstü pikselleri yukarı bakan normal alır
  (`top_tilt`): ay oraya ince bir ışık çizgisi düşürür, alttaki çıralar düşürmez.

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

Ötüken'in altı temel düşmanı (v2 yeniden tasarım, `tools/artgen/creatures.py`). Kimlikler kodla eşleştiği için eski
adlarıyla kalır; görünen ad ve açıklama `data/world.json`'da. Kurtlar Türk mitolojisinde kutsaldır ve kahraman kurt
başlıdır; bu yüzden düşman sürüsü kurt değil, Erlik'in tazılarıdır.

| Kimlik | Ad | YZ | Görünüş |
|---|---|---|---|
| `kara_boru` | Erlik Tazısı | lunger | Sıska kara tazı; kemik kafa zırhı, omur plakaları, çıkık kaburgalar, uçları kor dumanlı yele, kırık zincirli tasma; kor gözler ve ağız |
| `cor` | Çor Ruhu | flyer_ranged | Başlıklı, süzülen kefen; yırtık etek kuyrukları, iskelet eller, zincirde sallanan yeşil ışıklı buhurdan (sporlar buradan, `mouth` çapası) |
| `agac_iyesi` | Kara İye | brute | Kambur dev orman koruyucusu; geyik kafatası, dallanan boynuzlar, sırtı örten yosun, göğüs ve böğürde mor Erlik çatlakları, yere değen ağır kollar |
| `balbal` | Balbal | hopper | Kaidesi üstünde Göktürk taş savaşçısı; oyma yüz, sarkık bıyık, göğüste kadeh, kemer, taş kılıç; uyanınca gözler ve Orhun runaları camgöbeği yanar |
| `arcura` | Kara Kam | illusionist | Kemik maskeli kötü kam; geyik boynuzu + baykuş tüyü başlık, saçaklı ve çıngıraklı post, elde kam davulu, öbür elde mor lanet |
| `surale` | Gulyabani | grabber | Kambur, solgun, kefenli gul; çok uzun kollar ve sarı pençeler, uzun kara saç, oyuk gözlerde soluk ışık |

Palet ilkesi: yaratık başına 2-3 ana renk + tek parlayan vurgu (kor turuncu, salgın yeşili, Erlik moru, runa camgöbeği,
lanet moru, ölü göz sarısı); parlayan kısımlar `_e` katmanına düşer. Animasyonlarda hazırlık iki karedir (ikincisi daha
derin), vuruşta aşma vardır. Yalnızca yaratıkları üretmek için: `python export_assets.py --creatures [kimlik ...]`.

Davranış: Kara Kam iki hayalet kopya salar, arkana ışınlanır, lanet atar; Gulyabani yakalar, sersemletir, fırlatır
(4 tuş basışıyla kurtulursun). Tazı sürüsünde ikinci tazı arkadan dolaşır; Çor Ruhu tependeyken dalış yapar; Balbal
önden gelen vuruşta siper alır (%30 hasar); Kara İye üç kök dalgası gönderir.

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

**v9 — karıştırma ve ağırlık:** `Ses.gd` açılışta veri yollarını kurar: `SFX` (sıkıştırıcı -> biyom yankısı -> boğuklaştırıcı),
`Ambience` (biyom ortam döngüleri), `Music` (SFX yan zincirli hafif çekilme + boğuklaştırıcı), `UI` (kuru, kısılmaz) -> `Master`
(yapıştırıcı sıkıştırıcı + `AudioEffectHardLimiter` -0.5 dB: üst üste binen vuruşlar kırpılmaz).
- `Ses.play(ad, vol_db, pitch, pitch_var, min_gap, pos := Vector2.INF, vol_var := 1.5)`: önek varyantları varsa (darbe_kunt -> _1.._3)
  tam ada göre öncelikli ve art arda aynı dosya gelmez; ±0.75 dB ses ve perde oynaması; `pos` verilirse kameraya göre sağ-sol/uzaklık
  (`AudioStreamPlayer2D` havuzu). Kısayol `Ses.play_at(ad, konum, ...)`. Ses başına eşzamanlılık sınırı (`LIMITS`: adım 2, darbe 5,
  savuruş 3, altın 4...) dolunca grubun en eski sesi kesilir.
- `Ses.set_biome(id)`: yankı odası/ıslaklığı (sahmeran mağara geniş ve ıslak, bozkır kuru, tamu karanlık/sönümlü, kaf uzun ön gecikme)
  ve `ortam_<id>_dongu` ortam döngüsü. `Ses.music(biyom)` bunu kendisi çağırır.
- `Ses.menu_duck(true/false)`: oyun sesleri + müzik kısılır ve boğuklaşır; ağaç duraklatılınca (paused) efekt ve ortam kendiliğinden
  kısılır (başlıkta müzik etkilenmez). Arayüz sesleri (`ui_`, `npc_`, `esya_kusan/degis`, `tilsim*`, `seviye`, `acilis`, `ors`,
  `kut_banka`) `UI` yolundadır.
- `Ses.low_hp(k)`: 0..1; kalp atışı (`kalp_dongu`) yükselir ve hızlanır, oyun sesleri ve müzik boğuklaşır.
- Döngü sonu artık `süre x örnekleme hızı` ile hesaplanır (eskiden QOA sıkıştırılmış verinin bayt sayısı kullanılıyordu ve müzik
  parçanın yalnızca ilk ~%20'sini döndürüyordu). Dışa aktarılmış oyunda `.wav.import` adları da taranır.

Ses üretimi (`python tools/audiogen/export_audio.py`, denetim `python tools/audiogen/check.py`): `sfx.py` -> `layer.py` -> `pro.py`
(üstüne yazar) -> mastering. `pro.py` her vuruşu üç katmandan kurar: geçiş (kısa parlak tık), gövde (kayıt + perdesi düşen doyurulmuş
alt ton; ağır silahta daha çok) ve kuyruk (ıslak/moloz/oda); bıçaklarda tizde "şiing", ağırlarda bas savuruş. Yaratık sesleri gerçek
kayıtlar + biçimlendirici (formant) sentezi (`synth.voice`): Erlik Tazısı (`kurt_`: hırlama, havlama), Çor Ruhu (`cor_`: fısıltı,
tıslama, yankılı inilti), Kara İye (`agac_`: derin inilti + odun gıcırtısı), Balbal (`tas_`: çatlama, sürtünme, çöküş), Kara Kam
(`hayalet_` + `kam_davul/kahkaha/ilahi`: hömeyli ilahi, kam davulu, kıkırtı), Gulyabani (`surale_`: çığlık, hırıltı). Saldırı hazırlığı
türe göre `hazirlik_<sprite_kind>`. Yay: `yay_ger` (gıcırtı + kiriş gerginliği), `yay_birak` (tvang), `ok_ucus`, `ok_vurus`
(et) / `ok_vurus_tahta` (titreyen şaft) / `ok_vurus_tas`. Arayüz (tahta tık + kopuz teli, Hüseyni La): `ui_gez`, `ui_onay`, `ui_iptal`,
`ui_ac`, `ui_kapa`, `esya_kusan`, `esya_degis`, `tilsim_sec`, `seviye`. Mastering: her dosya kategorisine göre aynı algılanan
yüksekliğe (`synth.loudness`: 80 Hz üstü, 50 ms en yüksek RMS) getirilir — darbe -10, savuruş -13, ses -12, adım -20, arayüz -17..-21
dB; tepe -1 dBFS yumuşak sınırlı, 35 Hz altı kesik. Müzik 16 ölçü A/B bölümlü (ikinci yarı yeni ezgi tohumu), her 4. ölçüde davul dolgusu.

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

## Kombo sistemi, hareket ve çukur onarımı (v10)

- **Çıkmaz çukur onarımı** (`LevelGen.traps / fix_traps`): girişten ulaşılabilen her ayakta durma hücresinin çıkışa ulaşıp
  ulaşamadığı ters yönlü aramayla bulunur; çıkmazların üstüne zikzak tek yönlü basamak konur, olmazsa taban yükseltilir.
  Test: `godot --headless --path . --script res://tools/tests/tuzak_testi.gd` (6 stil × 12 tohum, kalan çıkmaz = 0).
- **Kombo sayacı:** 2,4 sn içinde vurmaya devam ettikçe artar; hasar +%1,5/isabet (en çok +%45), kademeler ER (5), ALP (12),
  BAHADIR (22), HAN (35), DESTAN (55) — her kademede Kut, ses, (3+) ağır çekim. Hasar alınca kırılır. Vuruş durması kombo ile uzar.
- **Bağlam hamleleri** (her silahta, zinciri bozmadan araya girer): ↑+J Göğe Savur (düşmanı fırlatır, sen de sıçrarsın), havada
  ↓+J Kartal Dalışı (dikey iniş, şok dalgası, krater), koşarken J Akın Kesiği, yuvarlanmadan hemen sonra J Dönüş Kesiği (kesin
  kritik), çömelirken J Diz Biçen (sendeletir). Havada isabet seni kısa süre asılı tutar; havadaki düşman vuruldukça havada kalır.
- **Hareket:** kenara tutunup tırmanma (havada duvara doğru basılıyken), köşe düzeltme (zıplarken baş köşeye takılırsa kayar).
- **Seçkin yıldızı:** seçkinlerin başında dönen altın-mor yıldız.
- **Yeni silahlar:** Tulpar Mızrağı (koşarken kritik), Börü Hançeri (arkadan kritik, kalkanı aşar), İkiz Balta (kanama yükü),
  Ulu Kayın Asası (1,8× itme, duvara çarptırır), Bozgun Kılıcı (öldürünce üç bozgun kristali).
- **Ses/müzik:** `bow2.py` yeni yay sesleri (germe, dolu, bırakma/tam, uçuş ıslığı, et/tahta/taş vuruşu); `turku.py` bağlama, zurna,
  kaval, davul-darbuka ile 9/8 karşılama, 7/8, 5/8 ve halay usullerinde türkü havaları.

## Bölüm yapısı, boss ve yaratık çeşitliliği (v9)

- **Boss:** `Game.BOSS_AFTER = {2: "kara_boru_han"}` — 2. derinliğin kapısı önce **Kara Börü Han** arenasına (`Level.build_boss`,
  `Boss.gd`) açılır; boss ölünce kapı belirir, sonra yurt. Üç evre: hamle + uluma (tazı çağırır), bozgun kristalleri + gökten
  çakma (işaretli yere iner), gölge kopyası + hız. HUD'da boss can çubuğu. Ganimet: 10 Kut, eşya (+2 kademe), parşömen, şifa otu.
  Test: `--boss`.
- **Yeni yapay zekâlar** (`Enemy.gd`): `pouncer` (yüksekten üstüne atlar), `shield` (kalkan önde; önden darbeler kalkana çarpar, 3
  darbe ya da ağır vuruş kalkanı düşürür → sendeler), `charger` (kalkanla hücum; duvara çarparsa uzun sersemler), `turtle`
  (vurulunca kabuğa çekilir, dokunulmaz; sonra yuvarlanarak ezer), `archer` (yaylı ok, mesafe korur), `stalker` (görünmez,
  yaklaşınca belirir), `diver`. Yeni sprite'lar: `bekci` (kalkanlı savaşçı), `tosbaga`, `kara_boru_han` (`tools/artgen/creatures2.py`).
  Biyom reskinleri artık kendi `ai` alanlarını kullanır; düşman havuzu biyomun tüm türleri.
- **Seçkin = mini boss:** 1,3× boy, ad etiketi, mor aura, 6 sn'de bir kükreme (iter + hızlanır); ganimet: eşya + parşömen + şifa otu.
- **Şifa Otu** (`Pickup` "sifa"): %35 can; seçkin/boss'tan kesin, diğerlerinden %5.
- **Biyom mekanikleri:** tehlike karoları (grid 3; `assets/tiles/hazards.png`): Ötüken/Bozkır diken, Şahmeran zehir, Tamu lav,
  Kaf buz (kaygan). Yeni stiller `bozkir` (kurgan tümsekleri) ve `kuyu` (derin kuyular + tavan). Özel odalar (chunk): `sunak`
  (tanrı lütfu), `hazine` (kaide eşyası + altın), `seckin` (seçkin odası), `kurgan` (yer altı mezar odası), `zehir_cukuru`.
- **Tanrı lütufları** (`Game.LUTUF`, sunakta E): Tengri (şimşek zinciri), Ülgen (öldürmede can), Umay (üçlü zıplama), Erlik
  (+%35 hasar / -%20 can), Kayra (Kut 2×), Yer-Sub (zırh), Ay Ata (kritik), Gün Ana (tutuşturma). En çok 3; yurda dönünce söner.
- **Kahraman:** S basılı = çömelme (çömelirken kılıç ve yay serbest; `crouch`/`crouch_atk` gövdeleri); Shift basılı tutma =
  yuvarlanma biter bitmez koşu (1,55×, yumuşak ivme, hayalet iz); kombo açılışları alttan yukarı savurmaz.
- **Müzik:** biyom parçaları 112-150 BPM sürücü davul + kopuz bası + riff kancası; `boss` parçası.

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
- **Ek özellikler ve kusurlar:** 25 ek özellik var (v20: kalkan / teçhizatta "Tez Elli" saldırı hızı); değerleri her düşüşte yuvarlanır. Kusurlu silahlar karşılığında %15 daha güçlüdür.
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

## v9: ongun ölçekleme, esnek yuvalar, piksel arayüz, yay

* **Çift renkli eşyalar (Dead Cells):** `items.json` içinde `"ongun"` tek renk ya da `["kurt", "ayi"]`. Nadir/destansı/efsanevi
  düşüşler %14/%28/%45 olasılıkla ikinci renk kazanır (`ItemGen.roll` → `ongun2`). Eşya, renklerinden **hangisinin seviyesi
  yüksekse** ona göre güçlenir: `Game.item_mult(it)` / `item_best_ongun(it)`. Tılsım ekranı hangi eşyanın ne kadar güçleneceğini gösterir.
* **Esnek silah yuvaları:** J ve K yuvasına her silah/kalkan konabilir; `Player._resolve_roles()` yakın dövüş ve ikincil rolü
  her karede çözer (iki yakın silah: basılan tuşun silahı). İki uygun yuva doluysa E ile **yuva seçim ekranı** açılır
  (`Level.try_equip` → `slot_requested` → HUD `"slot"`): A/D + E, ya da doğrudan J/K (teçhizatta U/I); eski eşya yere düşer.
* **Piksel arayüz:** `tools/artgen/pixfont.py` elle çizilmiş 5x7 Türkçe yazı tipi üretir (`assets/ui/pixel.fnt`, 13 = 1x).
  `scripts/ui/PixUI.gd` çentikli paneller, koçboynuzu süsleri, piksel simgeler, tuş rozetleri, ongun şeritleri çizer; `HUD.gd` tamamen buna geçti.
  Test: `-- --ekran=oyun|tilsim|yuva|duraklat|olum|umay|demirci|baslik|yay|kilic`.
* **Yay ve oklar:** `tools/artgen/arrows.py` 32 yönlü, kenar yumuşatmasız ok sayfası üretir (`assets/fx/arrows.png`). Yayda kiriş
  çizilir (`Player.BowString`), gerildikçe yay esner, ok yayda durur, arka el gezi çeker, tam gerilince uç parlar; bırakınca kiriş
  titrer ve yay geri teper. Oklar piksel iz bırakır, duvara saplanıp titrer, düşmana saplanıp bir süre kalır.
* **Savuruş izi:** `WeaponTrail` artık tarama çizgisiyle doldurulan üç katı bant (koyu iç, silah rengi, beyaz çekirdek) ve üç kademeli
  sönüş çizer; büyük hilal yalnızca bitiriş/ağır/özel savuruşlarda. Vuruş sonrası toparlanma hareket ya da zıplamayla iptal edilir.

## v11: biyom sonu bosları, sakin müzik, doğal hareket

* **Her biyomun sonunda boss:** `Game.BOSS_AFTER` derinlik 2/4/6/8/10 için Kara Börü Han, Tepegöz, Şahmeran Ana, Yelbegen, Erlik Han.
  Yeni dört boss ortak motoru kullanır (`Boss.gd` → `CFG`, `_ai_gen`): üç evre (%66/%33), hamleler savuruş, sıçrayıp ezme,
  yelpaze mermi, iki yana yer dalgası, işaretli gök yağmuru, yardımcı çağırma, hücum (duvara çarpınca sersemler).
  Mermiler: `stone_big`, `ice`, `fireball`, `ground_wave` (`Projectile.gd`). Sanat: `tools/artgen/creatures3.py`.
  Test: `-- --boss=tepegoz|sahmeran|yelbegen|erlik_han --bossfaz=1..3 --bosslog --otomatik`.
* **Sakin ama hareketli müzik:** zurna yerine mey (buğulu), kaval yerine ney; bendir, parmak tek'i, kısık def zilleri;
  hareketi alçak sesli bağlama arpeji taşır, ezgi daha uzun notalı (`calm_melody`). Tiz bölge yarıya indi, seviye RMS'e göre
  (`music.RMS_DB`), eskisinden 4–5 dB kısık.
* **Doğal hareket:** düşman ve oyuncu gövdesi yaylı (hafif aşmalı) squash/stretch, hıza ve ivmeye göre eğilme, nefes,
  havada hızla uzama, inişte düşüş hızına göre ezilme, dönüşte toplanma. Ceset darbe yönüne göre döner, yere çarpıp sürtünmeyle
  kayar ve yan yatar, sonra kor kenarlı çözülme gölgelendiricisiyle küle dönüşür (`Corpse.gd`). Toz rengi biyoma göre (`FX.dust_col`).

## v12: dört özgün mekanik

* **Üç Âlem (R / S+R, gamepad sol tetik):** kam transıyla aynı bölümün gök âlemine (Ülgen) ya da yeraltına (Erlik) geçilir.
  Kam gücü 100'den tükenir (sn'de 15), bu dünyada dolar (sn'de 4, öldürme başı 8). Gökte altın bulut basamakları basılır
  (`Game.LAYER_GOK`, tek yönlü), ruh kuşları yakalanır (Kut + kam gücü), bir bulut zincirinin tepesinde Ülgen sunağı eşyası durur;
  yerçekimi hafifler. Yeraltında ruh taşı kapaklar (`Game.LAYER_HAYALET`, ızgarada 4) çözülür, altındaki gizli odalara inilir
  (eşya + şifa + altın); Erlik'in gölge ruhları belirir (yalnızca yeraltında vurulur, 3 Kut). Öbür âlemdeyken bu dünyanın
  yaratıkları soluk görünür, sana dokunamaz, sen de onlara. Odada dönülürsen ruhlar seni kapağın üstüne taşır; taşın içinden dönülmez.
  Boss arenası ve yurtta kapalı. Kod: `scripts/world/Alem.gd`, `shaders/alem.gdshader`, `Player._v12_tick/_enter_realm/_exit_realm`.
* **Don Değiştirme (G, sağ tetik):** her seçkin ölünce mor bir ruh bırakır; dokununca emilir, G ile 10 sn onun kılığına girilir.
  Hamle takımı yaratığın yapay zekâ türünden: kurt (atılış zinciri, sıçrayış), kalkan (vuruş, siper), kabuk (yuvarlanma, çekilme),
  hücum, dev (yere çakma, sarsıntı dalgası), kanat (uçuş, pike, tüy), büyücü (üçlü büyü, ışınlanma). `scripts/actors/DonForm.gd`.
* **Usul Vuruşu:** müzik aksak usullerde (9/8, 7/8, 5/8, halay). Saldırı tuşu usulün vuruşuna ±85 ms içinde basılırsa
  vuruş güçlenir (%15 + seri başı %2,5, ölçünün ilk vuruşu "düm" +%15), seri sayılır; 8'lik seride Kut. Müzik dosyaları tam ölçü
  katı uzunlukta döngülenir, ızgara `assets/audio/music/usul.json` (`turku.META`), `Ses.usul_now()`. Sağda usul ölçeri.
* **Ad Koyma Töreni (Dede Korkut):** 11 destan (Basat: Tepegöz'ü devir, Boğaç, Deli Dumrul, Bamsı Beyrek, Kanturalı, Salur Kazan,
  Segrek, Kam Ata, Kopuzcu, Dönen, Alp Er Tunga). Destan koşu boyunca bekler; yurtta Ozan Bilge Kopuz'a anlatılınca ad konur,
  o koşu için güç verir ve Ad Defteri'ne (meta) yazılır. Yurda varmadan ölürsen destan unutulur. `scripts/core/Adlar.gd`.
* Sesler `tools/audiogen/v12.py` (bendir, zil, ney, mey, bağlama). Test: `-- --mekanik [--derinlik=N]` (`tools/tests/mekanik_testi.gd`).

## Görüntü ayarları, kamera ve HD doku paketleri (2K / 4K)

* **Görüntü alanı 960x540** (önceden 640x360): dünya 1,5 kat geniş görünür, her şey küçülür. 1080p'de 2x, 4K'da 4x tam sayı
  ölçek. Arka plan katmanları zaten 540 px yüksekliğinde üretildiği için 1:1 çizilir. Menüler 640x360 tasarımında kalır ve
  1,5 kat ölçekle çizilir (`HUD._menu_vp`); oyun içi HUD 1x (Ayarlar > Arayüz boyutu: Büyük = 1,5x).
* **Ayarlar** (`scripts/autoload/Ayarlar.gd`, başlıkta ya da duraklatmada **Tab**): Pencereli / Tam ekran / Özel tam ekran,
  pencereli çözünürlük (720p … 2160p), ölçekleme (Ekranı doldur / Keskin piksel), doku kalitesi (Otomatik / Standart / 2K / 4K),
  dikey eşitleme, arayüz boyutu. `user://ayarlar.cfg`. Doku kalitesi oyun yeniden başlatılınca uygulanır (`*` işareti).
* **HD doku paketleri = gerçek yeniden çizim, büyütme değil.** `raster.SS` çarpanıyla tuval N kat ince ızgarada rasterlanır;
  şekiller mantıksal birimde aynı kalır (`tools/artgen/export_hd.py N`). 2K = temel sayfaların 2 katı (`assets_hd/x2`), 4K = 4 katı
  (`assets_hd/x4`). Yalnızca renk dokuları; normal/parlama haritaları ve JSON meta temelden. `manifest.json` temel boyutları tutar;
  `Data.tex()` büyük dokuyu `ImageTexture.set_size_override` ile temel boyutta raporlar, oyun kodu değişmez.
  Otomatik: 1080p ve üstü 2K, 2160p 4K (960x540 görüntüde 2K paketi 1080p'de, 4K paketi 4K'da ekran pikseline 1:1 oturur).
  (v19: bu paketler yalnızca v1 piksel sanatını kapsar; stil v2 için aşağıdaki "Stil v2 HD doku paketi" bölümüne bkz.)
* **Test:** `-- --doku=0..3 --pencere=2560x1440 --goruntu=cikti.png` (6 sn sonra ekranı kaydeder ve çıkar).
  Başarım: `-- --otomatik --derinlik=7 --doku=2 --pencere=2560x1440 --bekle=8 --olcum=20` (kare süresi ort / %95 / en kötü,
  FPS, doku ve toplam video belleği, paket dokularının yükleme süresi; sonra çıkar).
* **Başlatıcı:** `Oyunu_Baslat.bat` her açılışta içe aktarır; GitHub'dan çekilen yeni dosyalar içe aktarılmazsa oyun boş ekranda kalıyordu.

### Stil v2 HD doku paketi (2K / 4K) ve uzaklaşan kamera (v19)

Şikâyet: 2K ekranda dokular düşük çözünürlüklü görünüyordu, 2K / 4K seçeneği v2'de hiçbir şey yapmıyordu (paketler yalnızca
v1 piksel sanatını içeriyordu), kamera fazla yakındı.
* **Kamera:** v2 biyom taban yakınlığı 2,0 -> Ötüken / Kaf / Tamu 1,7, Bozkır 1,65 (açık ova, geniş ufuk), Şahmeran 1,75
  (dar mağara); yurt 1,6 -> 1,4 (`data/stil_v2.json`, `data/yurt_v2.json` "camera_zoom"). Ekranda ~565x318 dünya birimi
  (önce 480x270). `CameraV2` çerçeve sabitleri (öncü kayma 58, ayak yüksekliği 50, zıplama penceresi 64/18, düşüş bakışı 54)
  2,0 için yazıldı (`REF_ZOOM`); taban yakınlık farklıysa `REF_ZOOM / taban` ile ölçeklenir: ayaklar yine ekranın ~%69'unda,
  öncü kayma yine yarım genişliğin ~%24'ü. Boss sığdırma `MIN_FIT` 0,62 göreli kaldı (en geniş 1,05); paralaks ve ön plan
  ekran uzayında olduğu için değişmez, kayma hızı yakınlığı izler.
* **Neden 2 kat:** v2 dokuları 4 doku pikseli / dünya birimi. 1,7 yakınlıkta 1440p'de 1 birim = 2560/960 x 1,7 = 4,5 ekran
  pikseli (temel doku 1,13 kat büyütülür), 4K'da 6,8 (1,7 kat). HD paketi 8 piksel / birim: 1440p'de de 4K'da da doku ekrandan
  yoğun (mipmap ile küçültülür, bulanıklık yok). Bu yüzden v2'de **2K ve 4K aynı x2 paketini** kullanır (4K seçiliyken önce
  `assets_hd/x4` aranır, yoksa x2: v1'in eski 4K paketi aynen çalışır).
* **Üretim = yeniden çizim, büyütme değil:** `tools/artgen/hdpack.py`; dışa aktarım betikleri `KY_HD=2` ile çalışınca çizim
  takımları (inkkit `InkCanvas`: tuval, köken, yoğunluk `k`, çizgi `lw` x2; inkkit_ortam `K` x2; piksel cinsinden bulanıklık,
  genişletme, gürültü ızgarası, kâğıt tanesi yarıçapları x2; gürültü alanları temel çözünürlükte üretilip pürüzsüz büyütülür ki
  desen aynı kalsın) aynı çizimi 2 kat çözünürlükte baştan yapar. PNG yazımları `assets_hd/x2/<aynı yol>`'a yönlenir; json ve
  ışıma/normal dokuları temel dosyaları ezmesin diye `.godot/hd_meta`'ya gider (HD kipinde yazılan json temelle bayt bayt aynı
  olmalı: sayfa düzeni, hücre, köken, bölgeler temel piksel cinsinden). Hepsi: `cd tools/artgen && python hd_v2.py`
  (~1 saat, 12 çekirdek; gruplar: karakter, yaratik, boss, ortam, sus, silah, efekt, arayuz).
* **Denetim:** `python hd_paket.py --kontrol`: her HD doku tam 2 kat mı, 2x2 küçültülmüş hâli temel dokuya ne kadar yakın
  (önçarpılmış RGBA ortalama farkı). 257 doku: 252 TAMAM (ort. fark ~0,001), 5 UYARI (ink_fx, bristle, arayüz fırça darbeleri
  stroke/swash/enso: kuru fırça / çözülme gürültüsünün ince frekansları yeni; büyük yapı aynı, gözle denetlendi).
* **Kapsam:** Bengü (3 sayfa + kol), Kara Börü, bozkurt biçimi, yurt sakinleri, set B yaratıkları, A takımı yaratıklar ve biyom
  çeşitlemeleri (17), 5 v2 boss (2-3 sayfa), mürekkep silah atlası, 5 biyom + yurt paralaks / ön plan katmanları, karo atlası,
  zemin maskesi, karo ışıma atlası, toprak / çayır dokuları, tehlike dokuları, bütün v2 süsler ve yurt yapıları, ortak süs atlası,
  v2 animasyonlu efektler, mürekkep vuruş atlası ve fırça dokusu, mürekkep arayüz dokuları. Temel çözünürlükte kalanlar: ışıma
  (`_e`, toplamalı yumuşak) ve normal dokuları, v1 piksel efektleri.
* **Paketleme ve boyut:** `python hd_paket.py --paketle`: PNG -> WebP (kayıplı q90 + kayıpsız alfa; kayıpsız daha küçükse o;
  maskeler hep kayıpsız), `.import` (BPTC yüksek kalite + mipmap), `manifest.json` girişi
  `[temel_g, temel_y, "<HD dosya>", "<temel PNG md5>"]`. 2 kat PNG'ler ~330 MB tutuyordu; WebP ile **~72 MB** (temel v2 PNG'lerin
  ~0,6'sı). Renk 4:2:0 alt örneklemesi HD'nin yarısı = temel çözünürlükte renk; kayıp oyunun zaten yaptığı BPTC sıkıştırmasının
  altında kalır. Eski v1 x4 paketi (60 MB) silinmedi: git geçmişinde kaldığı için depo boyutunu küçültmez, v1 4K'yı da kırardı.
  Bozkurt biçimi sayfası HD'de 10240 px geniş (temel 5120 geniş, satırlar sayfalanıyor, sütunlar değil): 16384 sınırının altında.
* **Yükleyici:** `Data.tex()` (sprite sayfaları, süsler, paralaks, ön plan şeritleri, silah sayfaları, AnimFX, SusV2 atlası,
  arayüz dokuları) HD dokuyu `ImageTexture.set_size_override` ile temel boyutta raporlar: bölge, kare, köken, `texel` ve dünya
  boyu aynı. Gölgelendiricide UV / `textureSize` ile örneklenen dokular (InkFX atlası, fırça dokusu, sıvı gürültüsü, toprak,
  çayır) `Data.tex_full()` ile gerçek boyutta yüklenir; toprak / çayırda `soil_density` paket çarpanıyla büyür (ikisi aynı
  ölçekte değilse ikisi de temel). TileSet boyut geçersiz kılmayı yok saydığı için karo atlası gerçek boyutta, karo hücresi
  `Data.pack_scale()` ile 192 px; **CanvasTexture'ın normal yuvasındaki zemin maskesi ve karo ışıma atlası atlasla aynı boyda
  olmalı** (yoksa karolar yanlış bölgeden örneklenir; `Level._same_size`, pakette karşılığı olmayan maske/normal çalışma anında
  büyütülür). Tehlike karoları `4 x pack_scale` hücre, parlama katmanı buna göre ölçeklenir. Silah piksel taramaları (yay uçları)
  temel sayfadan yapılır. md5 koruması: proje klasöründen çalışırken temel PNG sonradan yeniden üretildiyse eski HD sürüm
  kullanılmaz (uyarı + temel doku).
* **Ayarlar:** Otomatik artık 1440p ve üstünde HD (`AUTO_HD_H` 1400; 2160p'de 4K düzeyi), değer "Otomatik: 2K" biçiminde;
  `*` = yeniden başlatınca değişecek; açıklama satırı (`Ayarlar.quality_tip`) şu an etkin olanı ve yeniden başlatınca geçerli
  olacağı söyler; paket bulunamazsa bunu yazar. Ayar `user://ayarlar.cfg` "doku" anahtarında saklanır ve açılışta paket
  seçiminden önce okunur (doğrulandı: doku=2 kaydıyla 720p pencerede hd=1; Otomatik 720p'de 0, 1440p'de 1).
* **Arayüz:** mürekkep arayüzü TTF yazı tipleri kullanır; canvas_items germe kipi pencere çözünürlüğünde çizdiği ve yazı tipi
  aşırı örneklemesi açık olduğu için 1440p / 4K'da keskin (960x540 görüntünün büyütülmesi değil). Arayüz dokuları da HD pakette.
* **Başarım** (Intel UHD 750, 2560x1440 pencere, vsync kapalı, Kaf 7. derinlik, `--olcum=20`): standart 34,2 ms (29,2 FPS),
  doku VRAM 735 MB, toplam 990 MB; HD 36,2 ms (27,6 FPS), doku VRAM 1313 MB, toplam 1937 MB. Yelbegen arenası: standart doku
  894 MB / 36,2 ms, HD 1740 MB / 37,5 ms. HD dokuların yüklenmesi bölüm başına +1,3-1,8 sn (GPU'dan geri okuma + boyut
  geçersiz kılmalı yeniden yükleme). 4K pencerede (Şahmeran, HD) 90 ms: tümleşik GPU için 4K zaten ağır (piksel doldurma).
* **İçe aktarma:** HD paketin içe aktarılmış BPTC önbelleği `.godot/imported` altında ~2,7 GB tutar ve ilk açılışta ~7 dk sürer
  (12 çekirdek); önbellek depoya girmez, her makinede bir kez üretilir.

## Dövüş hissi v14: hiyerarşi, hazırlık, kırbaç, darbe karesi

Kaynaklar: Nijman "Art of Screenshake" (travma sarsıntısı, uyku kareleri), Jason Tomlee Slash FX (tek temiz hilal, kuyruğa doğru
incelme, 1-2 karelik doruk), SLYNYRD/GDQuest (hazırlık → vuruş → aşma → takip; smear yalnızca vuruşta), anime darbe kareleri,
Dead Cells pose-to-pose + efektle hareket. İlke: **her vuruş aynı şiddette okunmaz.** Üç soru bir saniyede yanıtlanmalı:
kim vuruldu, ne kadar sert, şimdi ne yapmalı.

* **Vuruş kademeleri** (`Player.HIT_FEEL`, `_melee_hits`): 0 hafif zincir vuruşu (35 ms hitstop, küçük kıvılcım, sarsıntı yok),
  1 orta: zincir sonu / ağır silah (65 ms, darbe yıldızı + darbe sprite'ı, hafif yönlü travma), 2 büyük: kritik / tam şarjlı ağır /
  bekleme bitirişi (105 ms, kritik patlaması, yönlü travma, titreşim, darbe karesi, kısa ağır çekim). Öldürme +30 ms. Üst sınır 120 ms.
  Kombo hitstop'u en çok %35 uzatır. Ses aynı karede (`Ses.hit(kademe)`).
* **Darbe karesi** (`scripts/core/ImpactFrame.gd`): 2-3 kare mürekkep karası ekran + vuran/vurulanın beyaz siluetleri; kritikte
  1 kare ters renk. 0,7 sn bekleme süresi (seçkin/boss ölümü zorlar). Ayarlar > Sarsıntı ve flaş: Azaltılmış'ta ters renk yok, Kapalı'da hiç.
* **Düşman flaşı** 3 kare (büyükte 5); geri itme üstel söner (ilk kareler hızlı, yumuşak oturma).
* **Savuruş** (`_update_attack`, `_update_weapon_visual`): hazırlık tutuşu 2-4 kare (ağırlığa göre; gövde toplanır, silah geriye bir tık),
  kırbaç gecikmesi (bilek, üst kolun açısal hızından geri kalır: hızlanırken geride, durunca ileri fırlar), aşma-oturma yayı
  (vuruş bitince kol vuruş yönünde bir tık aşar, sönümlü salınımla oturur), vuruş anında ön kol gerilir. `_weight(it)` 0..1:
  hançer 0,2 · kılıç 0,45 · ağır 0,8 · dev 1,0.
* **İz / smear** (`WeaponTrail`): bıçağın ucunun süpürdüğü ince hilal (bıçak boyunun %34'ü → %11'e incelir), üç kademeli sönüş,
  beyaz çekirdek yalnızca taze kısımda; ömür 80-140 ms (ağırlık). Büyük hilal sprite'ı yalnızca bitiriş / ağır / özel savuruşlarda.
* **Kamera** (`Game`): travma sarsıntısı (travma², üstel sönüm, yönlü: darbe ekseninde 1,6x), küçük olaylarda eski doğrusal sarsıntı,
  ileri bakış 28 px (`Player._look_ahead`), kol titreşimi `Game.rumble(güçlü, zayıf, süre)`. `Game.fx_scale` ayardan.
* **Test:** `-- --ekran=kilic --silah=dag_cekici --dusman=kara_boru` önüne iki durağan düşman koyar ve 3 vuruş yapar.
* **Kusursuz Kaçış** (`Player._perfect_dodge`): darbenin isabet edeceği an yuvarlanmanın ilk 120 ms'indeysen tetiklenir: 0,45 sn
  ağır çekim (0,22x), dokunulmazlık uzar, Kut +8, 1,5 sn içindeki ilk yakın vuruş kesin kritik ("cezalandırma!"). 1,6 sn bekleme.
  Alınan hasar hissi hasarın can oranıyla ölçeklenir; canın %25'inden büyük darbede darbe karesi oyuncuyu siluete çevirir.
* **Ses hiyerarşisi** (`tools/audiogen/impact.py`): darbe_hafif / darbe_agir (36 ms bas ön-yankı) / darbe_kritik (ters yükseliş +
  çatırtı) / olum_vurus; patlama üç katman (tık, 70→48 Hz bas, moloz), patlama_buyuk / patlama_uzak; simsek_catirti + gok_gurleme
  (gecikmeli), sarsinti / sarsinti_buyuk. `Ses.hit(kademe, konum, tür)`, `Ses.boom(konum, boy)`, `Ses.thunder(konum, gecikme)`.
  `sfx.json` "onset": geçişin dosya içindeki anı; hitstop ile aynı karede tetiklenince ön-yankı duraklamanın içine düşer.
* **Patlama / şok dalgası / gürleme** (`ExplosionFX`, `ShockwaveFX` + `shaders/shockwave.gdshader`, `ThunderFX`, `LightningFX`):
  patlama sahneli (2 kare beyaz flaş + ışınlar → küme ateş topu beyaz→sarı→turuncu→kızıl kenar, ease-out → kararma ve duman
  pufları → moloz, kor, zemin halkası; büyükte +80 ms ikinci iç patlama ve ekran kırılma halkası), hepsi 1 px ızgaraya oturur,
  gradyan yok. Şimşek: orta nokta yer değiştirme + 2-4 dal, 3 katman, 5 kademeli titreme. `FX.thunder(konum, güç)`: ön kıvılcım →
  1 kare beyaz ekran + gökten bolt + darbe diski → 90 ms sonra gürleme (yönlü travma, titreşim, şok dalgası). Gök Asası'nın ilk
  hedefi ve tam şarjlı yıldırım hamlesi gökten iner; yer vuruşları ve boss çakmaları `FX.shockwave` ekler.
  Test: `--ekran=kilic --ikinci=gok_asasi` (K ile asayı kullanır), bomba için `--otomatik`.

## Öğretici (v15)

`HUD.TUT` + `_tut_tick`: mekanikler ilk karşılaşıldığında üstte bağlamsal ipucu kartı (tuş rozetleri + açıklama, 7,5 sn).
Tetikleyiciler: kam gücü ≥ 30 ve bölümde âlem varsa (R gök / S+R yeraltı), yeraltı kapağına yaklaşınca (dünya işareti:
mor ▼ + "S+R: yeraltına in" ya da "kam gücü N/30"), gökte ruh kuşu yakınken ("ruh kuşu" etiketi), don ruhu yerdeyken
("ruhu em"), ruh emilince (G), 14. sn'de ağır vuruş/bitiriş, 40. sn'de usul, ilk kusursuz kaçışta. Her ipucu koşuda bir kez,
kalıcı olarak en çok 3 koşuda (`Game.meta.ogrendi`); test koşuları (--ekran / --otomatik) sayacı artırmaz.

## Silah arketipleri (v15)

Geri bildirim: "silahların hamleleri birbirine çok benziyor, sıkılıyorum." 32 savuruş vardı ama yalnızca 7 gövde pozu;
zincirlerin çoğu "kes, kes, daha büyük kes"ti. v15 her arketipi ayrı bir karakter gibi oynatır (Dead Cells: Balanced Blade /
Broadsword / Spear / Whip / Twin Daggers / Nutcracker). Dört eksende ayrışırlar: **tempo** (`aps` × savuruşun `tm` çarpanı:
hançer kesiği 0,12-0,18 sn, dev kılıç inişi ~1,4 sn, hazırlık tutuşu `_weight`e göre), **adım işi** (öne adım, geri sıçrayış,
hoplayıp çakma, derin hamle, pirouette), **vuruş kutusu** (`_swing_box`: baş üstü dikey şerit, saplama / kırbaç uzun yatay şerit,
çark daire, süpürme alçak şerit), **geri itme yönü** (fırlatma, yere çakma, kendine çekme, ileri itme) ve her silahın bir **imza
mekaniği**.

**Yeni gövde animasyonları** (`bengu.py`, 8 kare, poz-pozdan; kalça / omuz / eğilim işi yapar, ön kol oyunda sürülür, `sh_f`
çapası tutarlı): `atk_overhead_2h` (tepeye kaldır, adımla iner, darbede dizler bükülür), `atk_backstep` (öne yüklen, geriye hopla,
havada kes, çömelerek in), `atk_sweep_low` (derin çömelme, bıçak yer hizası), `atk_uppercut` (çömelmeden yükseliş, ayaklar yerden
kesilir), `atk_lunge_long` (arka bacak gergin derin hamle), `atk_spin_2h` (omuz burulması + çapraz bacak, gövde kalkar: pirouette),
`atk_dual` (omuzdan omuza burulma; arka kol ikinci bıçak olarak öne fırlar), `atk_whip` (ağırlık arka ayakta, omuz şaklar, kalça
izler), `atk_slam_jump` (çömel, hopla, iki ayak birden çakıl), `atk_throw_axe` (geriye tam burulma, bırakışta öne burulma).

**Yeni savuruşlar** (`Player.SWINGS`): backstep, lunge_long, spin_2h (iki yan, 2 vuruş), dual_l / dual_r, cross_dash (X kesik +
delip geçme), whip_side, step_down (tek elli adımlı baş üstü), pole_vault. Eski savuruşların gövdeleri değişti: overhead_2h /
step_down → atk_overhead_2h; slam / slam_2h → atk_slam_jump (vuruş penceresi 0,5-0,72: iniş karesi); rise / uppercut_2h →
atk_uppercut; sweep_low → atk_sweep_low; whip_crack → atk_whip; axe → atk_throw_axe; helicopter / stab_heavy → atk_spin_2h /
atk_lunge_long. Savuruş alanları: `tm` (süre çarpanı), `hold_k` (hazırlık tutuşu ve ağır şarj pozunun k noktası: sıçramalı
gövdelerde havadaki kare yerine çömelme karesi tutulur; `_hold_k`).

**Kombo bayrakları (v15):** `backstep` (gövde -190 px/sn geriye hoplar, 0,16 sn dokunulmaz; kutu öne uzar), `through` (vuruş
penceresi boyunca 780 px/sn ileri, düşmanın içinden öteye; 0,3 sn dokunulmaz, bitince hız %25), `spin_hold` (tuş basılıyken vuruş
penceresi başa sarar, en çok 1,2 sn, her turda iki yan yeniden vurulur; bu adım ağır saldırıya dönmez), `pull` (vuruştan sonra
düşman oyuncuya doğru px/sn ile çekilir, `pulled_t` 0,5 → yakala kritiği), `tipcrit` (bıçak boyunun %75'inden uzak isabet kesin
kritik, "uçtan!"), `stun` (sn, şarjla ×(1+hold)), `sa` (**`atk.super_armor` = true**: savuruş boyunca sarsılmazlık; `take_hit`
hasarı düşer ama savuruşu kesmez, hurt_t / geri itme / kombo kırılması yok, dokunulmazlık 0,35 sn), `vault` (↑+J sırık atlayışı: +210 px/sn
ileri, -470 yukarı), `crit` (adım kesin kritik), `tm`.

| Silah | Tempo / ağırlık | Zincir | Bekleme bitirişi | Ağır (basılı tut) | İmza | Gövdeler |
|---|---|---|---|---|---|---|
| Alp Kılıcı | dengeli, 0,45 | diag_down → diag_up (v18) → step_down (adım) | cross_x Alp Çaprazı | overhead_2h | 3. vuruş kritik (ucuncu_vurus) | down, horiz, overhead_2h |
| Yıldırım Kılıcı | katana, 0,45 | iai → backstep → lunge | flurry | iai → şimşek hamlesi | geri sıçrayıp hücum | horiz, backstep, lunge |
| Pala | kasap, 0,5 | diag_down → back → spin_2h | lunge Pala Akını | reap + pull Kanlı Kanca | **çarkta J basılı: 1,2 sn döner, iki yan** | down, horiz, spin_2h |
| Yatağan | düellocu, 0,3 | reverse_grip → horiz → backstep → lunge | flurry | iai dash | **3. vuruş çekilirken kesin kritik** + ivme | horiz, backstep, lunge |
| Ayaz Kılıcı | ağır-ölçülü, 0,45 | sweep_low → step_down (slam) | spin_2h | overhead_2h | don yükü (2 ağır vuruş) | sweep_low, overhead_2h |
| Ulu Kılıç | dev, 1,0 | overhead_2h → spin_2h | helicopter Ulu Çark | slam_2h | **süper zırh (atk.super_armor)**, ulu_kesik | overhead_2h, spin_2h |
| Ruh Kılıcı | 0,45 | diag_down → back → rise (fırlatır) | spin | cross_x | her kesik ruh hilali | down, horiz, uppercut |
| Ay Palası | dansçı, 0,2 | twirl → dual_r → dual_l → backstep → thrust(x2) | flurry | helicopter | 5'li zincir hızlanır, sonunda dokunulmazlık | spin, dual, backstep, thrust |
| Yılan Kılıcı | 0,45 | reverse_grip → thrust → sweep_low (çelme) | twirl zehir | reap zehir | zehir yükü | horiz, thrust, sweep_low |
| Rüzgâr Kılıcı | hava, 0,3 | iai → backstep → rise (fırlatır) | helicopter | cross_x | havadaki düşmana kritik + yel bıçağı | horiz, backstep, uppercut |
| Bozgun Kılıcı | dev, 1,0 | diag_down → spin_2h (sa) → step_down (sa) | cross_x | slam_2h (sa) | süper zırh, bozgun kristali | down, spin_2h, overhead_2h |
| Gürz | 0,8 | windmill (şok) → slam (hopla-çak) | slam | slam_2h **stun 1,4** | sarsıntı dalgası, ağır sersemletir | heavy, slam_jump |
| Çivili Topuz | 0,8 | down → uppercut_2h (fırlat) → slam | slam | slam_2h stun | zırh kırığı; havaya at-yere çak | down, uppercut, slam_jump |
| Dağ Çekici | en ağır, 1,0 | overhead_2h (şok, sa) → uppercut_2h | slam Dağ Yıkan | slam_2h stun 1,6, sa | havadaki düşman yere çakılır | overhead_2h, uppercut |
| Kor Çekici | 1,0 | windmill → overhead_2h | slam | slam_2h stun | kor gölü | heavy, overhead_2h |
| Savaş Baltası | 0,8 | axe_hook (**pull**) → axe (fırlat) | spin_2h | overhead_2h | kancayla çek, sonra fırlat-çağır | down, throw_axe |
| İkiz Balta | 0,8 | dual_l → dual_r (x2) → spin_2h | helicopter | spin_2h spin_hold | kanama; çark basılı sürer | dual, spin_2h |
| Teber | 0,65 | pole_sweep → sweep_low (çelme) → overhead_2h | helicopter | sweep_low fırlat | geniş yay | horiz, sweep_low, overhead_2h |
| Erlik Tırpanı | 0,8 | reap (**pull 240**) → sweep_low → spin_2h | reap pull 320 Ruh Biçen | reap pull 340 | **biçme düşmanı kendine çeker** | horiz, sweep_low, spin_2h |
| Kargı | 0,5 | pole_thrust → pole_thrust_lo → pole_rise (v18) | lunge | stab_heavy | **↑+J sırık atlayışı**, koşarken hücum kritiği | thrust, lunge_long, uppercut |
| Tulpar Mızrağı | 0,5 | pole_thrust(+30) → pole_thrust(+30) → lunge_long(+90) | helicopter | stab_heavy dash 160 | her saplama ileri taşır, koşarken kritik | thrust, lunge_long |
| Ulu Kayın Asası | 0,65 | pole_sweep → twirl → uppercut_2h | helicopter | pole_sweep stun | geri itme 1,8x, duvara çarptır | horiz, spin, uppercut |
| İkiz Bıçak | hançer, 0,15 | dual_l → dual_r → rake → cross_dash (**through**) | flurry | cross_dash through | **4. vuruş çapraz kesikle içinden geçiş** | dual, down |
| Kurt Pençeleri | 0,15 | rake → dual_r → rise (fırlat) | flurry | rake | havada sıçrama | down, dual, uppercut |
| Böri Hançeri | suikastçı, 0,15 | dual_l → dual_r → reverse_grip → cross_dash | flurry | cross_dash | geçiş arkaya düşürür → arkadan kritik | dual, horiz |
| Kement | 0,3 | whip_crack → whip_side | spin | whip_crack | **uçtan isabet kritik** + yakala çekişi | whip |
| Od Kamçısı | 0,3 | whip_crack → sweep_low → whip_crack | spin | whip_crack | uçtan kritik, yakma | whip, sweep_low |

Vuruş kutuları: overhead_2h / slam_2h / step_down `[-6,-64 → R+14,2]` (dikey), lunge_long `[6,-46 → R+32,-14]`, whip_crack /
whip_side `[6,-52 → R+34,-18]` (kırbaç erimi 46 px), spin_2h `±(R+14)` daire, backstep `[-2,-50 → R+24,-6]`, dual `[-2,-46 → R+14,-10]`.
Test: `--ekran=kilic --silah=<kimlik>` + temas sayfası; `--savurus` laboratuvarı yeni savuruşları da gösterir.

## Dövüş akışı (v17): ara bellek, iptal, adım, hedef yardımı

Geri bildirim: "kombat sistemini çok akıcı hale getirmemiz lazım." Ölçünce sertliğin kaynağı hız değil, **düşen girdiler**
ve **ani duruşlardı**: ağır silahta saldırı basışı 0,2 sn'de eriyip toparlanmaya yetişmiyordu (Ulu Kılıç / Dağ Çekici'de
savuruş içi basışın 0/5'i karşılanıyordu), yuvarlanırken basılan saldırı ve yuvarlanma bitmeden basılan ikinci yuvarlanma
yok sayılıyordu, saldırı başlar başlamaz yatay hız ~65 ms'de sıfırlanıyor (havada bile), vuruş anı adımı 3,5 px'ti.
Tüm ayarlar `Player.FLOW` tablosunda (Player.gd başı); savuruş zamanlaması (`SWINGS`, `aps`, `tm`) değişmedi: silahların
ağırlığı ve önceden okunurluğu korunur, yalnızca aradaki "ölü" anlar kalktı.

* **Ara bellek (Dead Cells / Hollow Knight kuyruğu):** saldırı basışı 0,3 sn saklanır; savuruş sürerken (hazırlık, vuruş,
  şarj) hiç erimez, toparlanma başladığı karede sıradaki adım çıkar. Bekleme bitirişinin toparlanmasından da yeni zincir
  açılır. Zıplama 0,15 sn (coyote 0,11), yuvarlanma 0,2 sn (yuvarlanma / bekleme sürerken basılırsa biter bitmez), ikincil
  (yay, fırlatma, büyü, kalkan) 0,2 sn ara belleğe alınır. Öncelik: saldırı zinciri > ikincil > yürüme iptali.
* **İptal pencereleri:** yuvarlanma her an keser (şarj dahil; şarj sesi / halkası `_cancel_attack` ile temizlenir).
  Zıplama: toparlanma ve şarjda keser; hazırlıkta ağırlığa göre (hafif silah tamamı, orta ilk %75, ağır ilk %40; süper
  zırhlı savuruş kesilmez); vuruş anında basılırsa ara bellekte bekler ve toparlanmanın ilk karesinde çıkar (eskiden vuruşun
  ortasında zıplıyor, savuruş havada sürüyordu). İkincil basış toparlanmayı keser. Havada başlayan savuruş toparlanırken
  yere inilirse kuyruk beklenmez (iniş iptali). Yürüme toparlanmayı kesmeye devam eder.
* **Kaçış saldırısı:** yuvarlanırken saldırı basışı saklanır; yuvarlanmanın %45'inden sonra yuvarlanmayı keser (0,1 sn ek
  dokunulmazlık) ve aynı karede Dönüş Kesiği çıkar (pencere: yuvarlanmanın %45'i → bitişten 0,32 sn sonrası). Ardışık
  yuvarlanma beklemesi 0,12 → 0,05 sn.
* **Ağır saldırı tanıma:** basılı tutma süresi basış anından sayılır (`heavy_hold` 0,22 sn; eski: hazırlık sonu + 0,16 sn).
  Hafif silahlar (ağırlık ≤ 0,3: ikiz bıçak, Ay Palası, Böri, Kurt Pençesi, yatağan, Rüzgâr, kırbaçlar) hafif vuruşu hiç
  bekletmez (100 ms'lik dokunuşta vuruş 167 → 100 ms); tuş basılı kalırsa ağır şarj toparlanmadan açılır. Şarj ederken
  yön tuşuyla dönülebilir. Zincirin 2.+ adımında hazırlık tutuşu (v14) yarıya iner.
* **Saldırırken hareket:** yerde hız sıfırlanmaz, sürtünmeyle söner (1100, ağır silahta 1500 px/sn²): koşudan saldırıya
  ~20 px kayış (eski 9). Vuruş anı adımı mesafe tabanlı: 7 px (ağır 9) + adımın `dash` × 0,38 (Alp zinciri 11-19 px,
  hamleler 35-60 px). Havada saldırırken yön tuşu koşu hızının %60'ına dek dinlenir (eski: 0'a çekiliyordu). Kendi hareketi
  olan savuruşlar (geri sıçrayış, delip geçme, şimşek hamlesi, sırık, dalış, pençe sıçraması, Göğe Savur) eski yolda.
* **Hedef yardımı:** saldırı başlarken yön tuşu basılı değilse ve önde (kutu + 28 px) kimse yokken arkada 64 px içinde
  düşman varsa döner; zincir adımları arasında yön tuşuyla dönülür. Vuruş anında kutunun ucunun 28 px ötesindeki düşmana
  adım uzar (vuruş penceresi içinde yetişecek hız); dibindeki düşmanın içinden geçmemek için adım (ve koşu ivmesi) kısalır.
  Görünmez gölge ve öbür âlemdekiler sayılmaz.
* **Vuruş hissi akışı bozmasın:** aynı savuruş geçişinde (çok vuruşlu savuruşta her geçiş ayrı) yalnızca ilk isabet tam
  duraklama / kamera itişi / darbe karesi verir; ek düşmanlar +8 ms ve ¼ sarsıntı (4 düşmana Ulu Kılıç: 116 → 66 ms donma).
  Hafif vuruş duraklaması ağırlıkla ölçeklenir (hançer ~29 ms, kılıç 35 ms). `Game.kick` toplamı 9 px ile sınırlı;
  `Game.slowmo` üst üste binen çağrılarda en yavaşını süresince uygular (kısa sert çağrı uzun hafif olanın kalanını
  sertleştirmez).
* **Adil takas:** sarsılan (ağır / boss olmayan) yaratığın süren saldırı teması kesilir: sıçrarken vurulan kurt sana
  çarpıp can götürmez. Kalkanla karşılanan darbe artık sarsmaz, savuruşu kesmez, komboyu kırmaz (kısa geri kayma).

| Ölçüm (`--dovus --boss`, 60 Hz) | Önce | Sonra |
|---|---|---|
| Savuruş içinde basış karşılandı (Alp / Kargı / Ulu / Dağ Çekici) | 4/5 · 2/5 · 0/5 · 0/5 | 5/5 · 5/5 · 5/5 · 5/5 |
| Yuvarlanırken saldırı (8. karede bas) | düşer | aynı kare, Dönüş Kesiği |
| Yuvarlanma sonunda ikinci yuvarlanma (15. karede bas) | düşer | 100 ms sonra |
| Vuruş anında zıpla | vuruşun ortasında zıplar, savuruş havada sürer | toparlanmanın ilk karesinde (67-100 ms sonra) |
| Vuruş anında yay | düşer | toparlanmada ok (67-100 ms) |
| Dururken vuruş adımı / koşudan saldırıda kayış | 3,5 / 9 px | 12 / 21 px |
| Havada saldırı, yön basılı (hız, 10 kare) | 105 → 0 px/sn | 114 → 93 px/sn |
| Arkadaki (26 px) / 22 px uzaktaki düşmana ilk vuruş | ıska / ıska | isabet / isabet |
| Ağır saldırı tanıma (Alp / Dağ Çekici) | 267 / 633 ms | 250 / 517-550 ms |
| İkiz bıçak 100 ms dokunuş → vuruş | 167 ms | 100 ms |
| Sıçrayan düşman vurulunca temas | sürer (takas) | kesilir |

Test: `godot --headless --path . --quit-after 99999 -- --dovus --boss [--stil=v2]` (`tools/tests/dovus_testi.gd`; boss
arenası düz test sahnesi olarak kullanılır, boss kaldırılır). Betikli girdi (`Input.action_press`) oyuncunun kendi yolundan
geçer; her senaryodan sonra 1,5 sn girdisiz bekleyip takılı durum arar (saldırı, yuvarlanma, şarj, nişan, şarj döngü sesi,
zaman ölçeği). Çıktı `[dovus]` satırları, sonda `OZET` ve `TAKILMA=0`. Basıştan vuruşa / iptal edilebilir ana kadar
süreler bilerek değişmedi (silah temposu): ikiz bıçak 117 / 150 ms, yatağan 167 / 250, Alp 217 / 333, kargı 267 / 400,
Ulu Kılıç ~600 / ~900, Dağ Çekici ~670 / ~1000 ms (ölçüm ±2 kare oynar). `--klip` eki kısa bir gösteri oynatır
(`--write-movie` ile çekim için: koşudan zincir, arkadakine dönüş, yuvarlanmadan Dönüş Kesiği, havada yön, zıplama ara belleği).

## Dövüş temposu ve savuruş biçimleri (v18): Dead Cells esinli

Geri bildirim: "silahların kombo hızları ve savuruşları iyi görünmüyor; art arda kombolar yük varmış gibi sıkıyor; Dead Cells
kadar akıcı olsun, ağır silah ağır ama yine çevik." v17 girdileri düzeltmişti ama zamanlamaya dokunmamıştı. Ölçünce yük hissinin
kaynağı: (1) her savuruşun süresi `1 / aps` idi ve sabit oranlarla bölünüyordu (hazırlık %30, toparlanma %44): Alp Kılıcı'nda
basıştan temasa 200-233 ms, zincir aralığı 300-367 ms; Dağ Çekici'nde 683 ms / 1 sn; (2) zincirin her vuruşu kolu önce
**dinlenme pozuna geri götürüp** oradan yeniden geriyordu (her vuruşta bir "hazırlık duraklaması"); (3) isabet bıçak daha
hazırlıktayken (vuruş penceresinin ilk karesinde) sayılıyor, duraklama bıçak düşmana varmadan donuyordu.

### Araştırma (kaynaklı)

* **Dead Cells silah verisi** (deadcells.wiki.gg, `ItemDetails` şablonu: `charge` basıştan vuruşa, `lock` vuruştan sonraki
  girdiye kadar "animasyon kilidi"; DPS = kombo hasarı / kombo süresi, örn. Balanced Blade 215 / 1,46 sn ≈ 147, yani süreler
  oyunun verisi): Balanced Blade 0,10/0,05 · 0,10/0,15 · 0,07/0,05 · 0,07/0,15 · 0,07/0,05 · bitiriş 0,30/0,30 sn;
  Rapier 0,2/0,1 · 0,1/0 · 0,1/0 · 0,1/0,25; Twin Daggers 0,2/0 · 0,25/0 · 0,37/0,25; Assassin's Dagger 0,2/0 · 0,2/0,1;
  War Spear 0,38/0 · 0,1/0 · 0,2/0,2 (ilk hazırlık 2.4 yamasında 0,45 → 0,38); Impaler 0,2/0; Wrenching Whip 0,2/0,1 ·
  0,2/0,1 · 0,3/0,3; Nutcracker 0,5/0,2 · 0,4/0,2 · 0,5/0,1; Broadsword 0,4/0,2 · 0,5/0,25 · 0,5/0,4. Desen: hafif silahta
  hazırlık 0,07-0,2 sn (4-12 kare), kilit 0-0,15; bitiriş ~0,3/0,3 ve kritik / büyük hasar ondadır; ağırda hazırlık 0,4-0,5,
  kilit 0,2-0,4; bekleme süresi neredeyse hep 0. Kaynaklar: https://deadcells.wiki.gg/wiki/Balanced_Blade ,
  https://deadcells.wiki.gg/wiki/Broadsword , https://deadcells.wiki.gg/wiki/Twin_Daggers ,
  https://deadcells.wiki.gg/wiki/War_Spear , https://deadcells.wiki.gg/wiki/Nutcracker ,
  https://deadcells.wiki.gg/wiki/Wrenching_Whip , https://deadcells.wiki.gg/wiki/Rapier , https://deadcells.wiki.gg/wiki/Mechanics
* **Animasyon hattı** (Thomas Vasseur, Game Developer 2018, "Art Design Deep Dive: Using a 3D pipeline for 2D animation in
  Dead Cells", https://www.gamedeveloper.com/production/art-design-deep-dive-using-a-3d-pipeline-for-2d-animation-in-i-dead-cells-i-):
  3B iskelet → kenar yumuşatmasız küçük çizim (~50 px karakter), "olabildiğince az kare", poz-pozdan; ara kareler
  anahtarların arasına değil yalnızca önüne / arkasına eklenir; hareket hissini efektler verir; bir silahı zayıflatmak =
  animasyonunu yavaşlatmak (anahtarlar dakikalar içinde onlarca kez yeniden zamanlanır).
* **Bénard (Motion Twin) söyleşileri** (https://80.lv/articles/dead-cells-hidden-tricks-that-make-the-game-feel-fair ,
  https://dtf.ru/51865-kak-dead-cells-meshaet-vam-umeret , GDC 2019 haberi): denetimler asla zorluğun kaynağı değil;
  30-40 gizli oyuncu yardımı (atlamadan sonra düşmana kendiliğinden dönme, saldırıda serbest dönüş, otomatik nişan);
  saldırıyı iptal edip kaçabilme sonradan eklendi (ikincil kaynak).
* **Sendeleme** (wiki Mechanics): saldırısının ortasında vurulan düşmanın vuruş anı gecikir ama saldırı iptal olmaz;
  gecikme kullanılan silahın kilidiyle ölçeklenir. **Yuvarlanma** 0,4 sn, bekleme 0,37; komboyu sıfırlamaz; yuvarlanmayla
  kilit kesilip kombo sürdürülebilir (wiki Bible sayfası).
* **Başka oyunlar**: Hollow Knight çivi 0,41 sn bekleme / Quick Slash 0,25 (https://hollowknight.wiki/w/Quick_Slash);
  Celeste donmaları 0,05 sn atılma, 0,1 patlama (https://raw.githubusercontent.com/NoelFB/Celeste/master/Source/Player/Player.cs);
  Sakurai: vuran ve vurulan aynı süre donar, hasarla ölçeklenir, üst sınırı vardır
  (https://sourcegaming.info/2015/11/11/thoughts-on-hitstop-sakurais-famitsu-column-vol-490-1/); Smash hitlag formülleri
  (https://www.ssbwiki.com/Hitlag).
* Bulunamayanlar: Dead Cells'in duraklama (hitstop) / sarsıntı milisaniyeleri ve girdi ara belleği resmî olarak
  belgelenmemiş; bizim değerler v14 kademeleri üstüne ölçülerek kondu.

### Bizim sürümümüz (`Player.TEMPO`, `_phase_times`, `_atk_advance`)

Dört evre gerçek saniye; savuruşun normalize anahtarları (k) zaman bükmesiyle bunlara oturur: **hazırlık** 0 → hit[0],
**süpürme** hit[0] → `ck` (bıçağın son hızlı yayı, 2-3 kare, smear karesi), **kilit** `ck` → hit[1] (isabet `ck`de
açılır; kilidin ilk yarısında takip / aşma, ikinci yarısında oturma; sonunda zincir ve iptal), **toparlanma** hit[1] → 1
(yalnız girdi yoksa görünür). Eşyanın hızı (malzeme, kalite, "hız" niteliği, ivme) süreleri taban aps'e oranla ölçekler.

| Sınıf (`_tempo_class`) | basış→temas ilk / zincir | süpürme | kilit | tutuş ilk / zincir | silahlar |
|---|---|---|---|---|---|
| hançer | 67 / 50 ms | 25 | 67 | 0 | ikiz bıçak, böri, kurt pençesi, ay palası |
| düello | 83 / 67 | 30 | 83 | 0 | yatağan, rüzgâr kılıcı |
| kılıç | 100 / 83 | 33 | 100 | 17 / 0 | alp, pala, ruh, yılan, ayaz, yıldırım |
| mızrak | 117 / 83 | 33 | 83 | 17 / 0 | kargı, tulpar |
| kırbaç | 150 / 117 | 33 | 100 | 17 / 0 | kement, od kamçısı |
| uzun sap | 167 / 133 | 40 | 117 | 33 / 0 | teber, tırpan, kayın asası |
| ağır | 250 / 200 | 50 | 150 | 50 / 17 | gürz, topuz, savaş baltası, ikiz balta |
| dev | 330 / 267 | 50 | 200 | 67 / 33 | ulu kılıç, dağ / kor çekici, bozgun kılıcı |

Zincir sonu (`last`) Dead Cells bitirişi gibi: hazırlık ×1,3, kilit ×1,5 (çarkta ×1,1). Bekleme bitirişi: hazırlık ×1,5.
Savuruş çarpanları: çark / çok vuruşlu savuruşlar yayı kilitte döndürür (`ss`: spin 2,2, spin_2h 2,2, helicopter 2,6,
flurry 3, cross_x / cross_dash 2, rake 1,8, twirl 2); sıçramalı çakma `ws` 1,6, yel değirmeni 1,4. Ağır saldırı tam şarjı
0,85 → 0,55 sn, tanıma 0,22 → 0,2 sn; kılıç, pala ve mızrak da (ağırlık ≤ 0,5) dokunuşta beklemez (100 ms dokunuşta Alp
vuruşu 150 → 83 ms), basılı kalırsa ağır şarj toparlanmadan açılır.

**Savuruş biçimleri:** her tek vuruşlu savuruşa `ck` (temas) eklendi; takip pozu kilidin ilk yarısına çekildi, kilidin
sonuna dinlenmeye %12 yaklaşan bir oturma anahtarı kondu (vuruş → aşma → oturma, Dead Cells'in tutulan darbe pozu gibi).
Hızlanan evre kübik yerine kare: 2-3 karelik süpürmede ara kare yayın ortasında görünür (kübikte bıçak tek karede
ışınlanıyordu). **Zincir akışı:** `_atk_pose` zincirdeki savuruşun hazırlığını önceki savuruşun son çizilen pozundan
başlatır (açılar en kısa yoldan; çark 6,9 rad'dan geri sarılmaz); zincirler bir vuruşun bittiği yer ötekinin hazırlığı
olacak biçimde dizildi: Alp Kılıcı çapraz iniş (yukarıdan aşağı) → çapraz yükseliş (aşağıdan yukarı) → adımlı baş üstü
iniş; Kargı saplama → alçak saplama (`pole_thrust_lo`, diz hizası, uzun hamle gövdesi) → alttan baş üstüne süpürme
(`pole_rise`, hafif kaldırır); Dağ Çekici baş üstü iniş → aparkat (yukarıda biter) → yeni iniş yukarıdan başlar.
Hançer (`dual_l` / `dual_r`) ve kırbaç yan şaklaması (`whip_side`) ekrana doğru "kısalan" yatay savuruş yerine ekran
düzleminde hilal: iniş / yükseliş dönüşümlü (uç yolunu izleyen fırça izi zikzak çiziyordu). Sırık süpürmesinin takibi
yumuşatıldı (iz köşe yapıyordu). Savuruşta gövde: hazırlıkta geriye toplanır, vuruşta öne yüklenir (ağırlıkla).
Çark hazırlığında (`spin_2h`, `helicopter`, `windmill`) iz vuruşun hemen öncesinde başlar (yerde sürüklenen kılıç yassı
leke bırakıyordu). **İz örneklemesi:** karede süpürülen açıya göre 4-28 ara örnek (~0,06 rad'da bir; sabit 4 örnek hızlı
yayda hilali çokgenleştiriyordu); InkTrail ayrıca kabza çevresinde açıyla ara örnek ekler.

**Vuruş hissi:** isabet `ck`de (bıçak düşmanın üstündeyken) başlar, duraklama orada donar. Orta kademe (zincir sonu, ağır
silah) duraklaması ağırlıkla: kılıç 55 ms → dev silah 80 ms; hafif 22-35 ms, büyük 105 ms (v14) aynı.

**Düşman duruşu (`Enemy.POISE`, Dead Cells sendeleme kuralı):** hafif vuruş hazırlığı iptal etmez, sarsılma süresince
geciktirir (0,12 sn; büyük vuruş 0,2 sn ve hazırlığı keser). 0,9 sn içinde 4 sarsılmadan sonra (seçkinde 2) yaratık
0,75 sn "diretir": hasar alır, az itilir, sarsılmaz, hazırlığı sürer (küçük halka). Bitiriş, kritik ve ağır saldırı
direnci kırar. Böylece hızlı zincirler sonsuz kilit yaratmaz; boss kuralı değişmedi.

**Ölçüm** (`--dovus --boss`, v1 ve v2, 60 Hz, ±1-2 kare; "temas" = isabetin başladığı kare; zincir aralığı = 20 Hz seri
basışta ardışık temaslar arası, düşmansız; "önce" aynı test betiğiyle 199b74e'de):

| Silah | basış→temas önce → sonra | basış→iptal edilebilir | zincir aralığı önce → sonra |
|---|---|---|---|
| İkiz Bıçak | 117 → 83-100 ms | 150 → 150-167 | 117-167 → 100-117 |
| Yatağan | 167 → 100-117 | 250 → 183-200 | 200-217 → 167 |
| Alp Kılıcı | 200-233 → 133 | 300-367 → 233 | 300-367 → 200-250 |
| Pala | 233 → 133 | – | 267-417 → 200 |
| Kargı | 233-300 → 150 | 367-400 → 233 | 400-450 → 183-217 |
| Kement | 283 → 183 | – | 400-433 → 267-300 |
| Teber / Tırpan | 350 → 166-216 | – | 450-650 → 250-317 |
| Savaş Baltası | 350 → 300 | – | 367-433 → 433-467 (kanca + fırlatma) |
| Gürz | (seri basışta takılıyordu) → 316 | – | → 500 |
| Ulu Kılıç | 583-600 → 350-400 | 883-900 → 600-617 | (takılıyordu) → 483-517 |
| Dağ Çekici | 667-683 → 366-417 | 1000-1033 → 650-700 | (takılıyordu) → 533-583 |

Hata düzeltmesi: ağır silahta hazırlık sırasında **yeni** basış, "basılı tutma bekleyişi"ni yeniden tetikleyip hazırlığı
geri sarıyordu (seri basışta gürz / ulu / dağ çekici zinciri ilerlemiyordu; aynı testte eski sürüm TAKILMA=3). Bekleyiş
artık yalnızca savuruşu başlatan basış hâlâ sürüyorsa. İptaller değişmedi: hazırlıkta yuvarlanma 1 kare, yuvarlanmadan
Dönüş Kesiği aynı kare, ardışık yuvarlanma 100 ms, ara bellekler 3/3-5/5, TAKILMA=0 (v1 ve v2). Hazırlık artık 2-5 kare
sürdüğünden hazırlıkta basılan zıplama çoğunlukla ara belleğe düşer ve kilit bitince çıkar (167 ms).

Çekim: `-- --dovus --boss --stil=v2 --klip=alp_kilici,ikiz_bicak,kargi,dag_cekici` (her silahta önde iki düşmana tam zincir,
her temas anında yeni basış; sonra basılı ağır saldırı; `--klip_bos` düşmansız). `--write-movie` kayıtta duraklama ve ağır
çekim artık oyundaki süresiyle görünür (`Game.clock()`: çekimde kare saati; eskiden gerçek saat, çekim yavaş işlendiği için
duraklamalar kayıtta kayboluyordu). 1080p çekim için proje köküne geçici `override.cfg` gerekir
(`window/size/window_width_override=1920`, `window/size/window_height_override=1080`); `--resolution` proje pencere geçersiz
kılmasını aşmıyor.

## Görsel düzeltmeler (v16)

Eski tasarım `eski-tasarim-v13` git etiketinde saklı.

* **Titreme yok:** 1,5x / 2x yoğunluklu dokular (Bengü, karolar, silahlar) ekrana tam sayı olmayan oranla düşüyordu;
  en yakın komşu örneklemesi kamera kaydıkça pikselleri 1-2 ekran pikseli arasında zıplatıyordu. `shaders/aapix.gdshaderinc`:
  keskin ama kenar yumuşatmalı örnekleme (`AA_TEX` makrosu, texelFetch ile elle çift doğrusal, önceden çarpılmış alfa).
  `toon_light` (`pixel_aa` 1) ve `ground` (karo + dünya koordinatlı toprak) kullanır.
* **Flaşlar:** `Level.flash_white` en çok 0,18 alfa, 0,06 sn, gerçek zamanlı (ağır çekim uzatmaz); patlamada yalnızca büyükte.
  Hasar: tam ekran kırmızı yerine vinyetin `hurt` parametresiyle kenarlardan kısa kırmızı nabız. `ImpactFrame`: ters renk karesi
  kaldırıldı, kararma 0,5-0,68 alfa, en çok 2 kare. `RingFX`: ince (1-2 px), sönük, yarıçap ≤ 48.
* **Silah:** `WeaponTrail.add` hızlı savuruşta kabza etrafında açıyla ara örnek ekler ("V" izi yok). `Player._ground_clamp`:
  yerdeyken silah başı ve izi zemin çizgisinin altına inmez.
* **Okunurluk:** oyuncuda kısık gölgesiz Kut ışığı (0,32); ay gölgesi aktörde ay payının en çok %55'ini keser. Ruh kurdu ışıması
  0,7 ve tint 0,86 (bembeyaz yanıyordu); kurt biçiminde hayalet izi kurt gövdesinden.
* **Ölüm efekti sade:** koyu kırmızı duman diski ve her ölümde halka kaldırıldı (seçkin/boss'ta halka kalır).
* **Yere vuruş** (`scripts/core/GroundSlamFX.gd`, `FX.ground_slam`): silah başı yere değdiği karede (`Player._slam_contact`):
  2 karelik baş flaşı → araziyi sütun sütun izleyen şok sırtı ve basınç çizgileri → V toz bulutu ve yuvarlanan toz → seken
  biyom renkli taşlar → kıvılcım/kor → araziyi izleyen krater ve çatlak izi (7 sn). Güç = 0,5 + 0,55 × ağırlık + 0,5 × şarj
  (+0,3 bitiriş), 0,6-1,9. Boss iniş/çakmaları da kullanır.
* **Pozlama:** biyom başına `glow`, `glow_bloom`, `glow_threshold`, `brightness`, `deep_amount` (`data/world.json`). Bozkır
  ortalama parlaklık 0,32 → 0,16 (kırpılan piksel %15 → %1,3), Kaf 0,19 → 0,10, gece biyomları biraz açıldı. `soil.py`
  `_ao_dither`: gölgeli yandan ve çıkıntı altından noktalı ortam kapatma; `bg_hd.py` katman başına renk derecelendirme ve pus;
  `env_forest.py` süslerin yere değdiği yerde 3 basamak koyulaşma.

## Stil v2 denemesi: "gerçekçi piksel" (Shinobi: Art of Vengeance yönü)

Yalnızca dikey kesit: Bengü (boşta, koşu, yukarıdan kesiş; diğer animasyonlar v1 pozlarıyla v2 çizimi) ve Kararan Ötüken
(karo atlası, toprak dokusu, orta orman katmanı). v1 sanatı olduğu gibi durur; eski tasarım `eski-tasarim-v13` etiketinde.

* **Seçim:** `-- --stil=v2`. `Data.stil_id(kimlik, yol_kalıbı)` bir varlığın `<kimlik>_v2` sürümü varsa onu, yoksa v1'i verir:
  `Data.sprite()` (bengu -> bengu_v2), `Player` kol iskeleti (bengu_kol -> bengu_kol_v2), `Level._tile_id()` (otuken -> otuken_v2:
  atlas, `_n`, `_soil`, `_soil_n`, json), paralaks katmanları (otuken_3_mid -> otuken_3_mid_v2). Eksik dosya = v1'e düşer, karışık
  kullanım güvenli. HD paketlerinde (assets_hd) v2 dosyası yok: v2 dokuları temel boyutta yüklenir.
* **Üretim:** `cd tools/artgen && python export_v2.py [--otuken]` (Ötüken) ve `python export_ink.py [--bengu|--kara_boru]` (karakterler, mürekkep-cel; aşağıya bkz.) yalnızca `_v2` dosyalarını yazar.

  atlas, `_mask`, `_soil`, `_meadow`, json), paralaks katmanları (otuken_3_mid -> otuken_3_mid_v2). Eksik dosya = v1'e düşer, karışık
  kullanım güvenli. Biyom art değerleri (katman listesi, ışık, ön plan, renk derecelendirme) `data/stil_<stil>.json` ile ezilir
  (`Level._stil_art`); karo meta bilgisi `Level._tmeta()` (v2'de `<biyom>_v2.json`). HD paketlerinde (assets_hd) v2 dosyası yok: v2 dokuları temel boyutta yüklenir.
* **Üretim:** `cd tools/artgen && python export_v2.py [--bengu|--otuken]` yalnızca `_v2` dosyalarını yazar.
  `style_v2.py`: 7 tonlu rampa (`tones`), malzeme türü (`M2(..., kind=cloth|leather|metal|fur|skin)`: kumaş geniş bant/mat,
  deri dar orta ton + kısa parlama, metal gök/yer yansıması + keskin parlama), yansıyan ışık (gölgedeki aşağı bakan yüzey +1 ton),
  ışığa dönüklüğe göre 1-2 piksel ay kenar ışığı, seçici kontur (`VCanvas2`).
* **Bengü v2** (`bengu_v2.py`): ~7 baş boy (bacak 12+11.8, gövde 17, kol 10+9.4; v1: 10.5+10.5, 14, 8.5+8), daha küçük ve anatomik
  kurt başı, diz boyu kaftan (pliler, altın sırma etek), çelik lamel yelek + omuzluk + dizlik, geniş kemer ve altın plakalar,
  uzun çizme, ak post yaka, ince çift kuyruklu atkı. Doku yoğunluğu 2x (v1: 1.5x): 1080p'de 1 doku pikseli = 1 ekran pikseli.
* **Ötüken v2** ilk denemede piksel sanattı (`otuken_v2.py`, artık yalnızca kayıt); yerini aşağıdaki "mürekkep" ortamı aldı.
* **Test:** `--ekran=kilic --silah=alp_kilici --stil=v2 --bekle=4.6 --seri=10 --aralik=0.12 --goruntu=x.png` tek açılışta 10 kare
  (`x_0.png` ...). `Ayarlar._snap`: `--bekle` (varsayılan 6 sn), `--seri`, `--aralik`. Karşılaştırmalar: `docs/stil_v2/` (.gdignore).
  Görüntü alanı HDR 2D olduğundan çekilen kare doğrusal renktedir: `.png` çıktısı sRGB'ye çevrilir (8 bit; koyularda hafif
  bantlaşma), `--goruntu=x.exr` kayıpsız doğrusal yarım kayan nokta yazar (araç tarafında sRGB'ye çevrilir).

### Ötüken v2 "mürekkep" ortamı (el çizimi çizgi roman görünümü)

Piksel sanat değil: kenar yumuşatmalı, boyalı dokular + değişken kalınlıklı mavi-siyah mürekkep (#15161d).
**Kamera (v15):** v2 mürekkep ortamında taban yakınlık **2,0** (`stil_v2.json` "camera_zoom", `Game.base_zoom`; zoom_punch
bunun üstüne çarpılır): ekranda 480x270 dünya birimi, Bengü 1080p'de ~225 px (ekranın ~%21'i; referansta ayakta ninja
~%20). Ölçüm: idle karesi 56 dünya birimi; 1,5'te ~168 px (%15,5) "çok uzak" bulunmuştu. v1 çerçevesi (960x540, 1,0) değişmez.
`scripts/world/CameraV2.gd` (yalnızca ink ortamında; Level'ın çocuğu, oyuncunun değil): baktığın/koştuğun yöne yumuşak
öncü kayma (58 birim + hız; saldırıda donar), yakın uyanık düşman arkadaysa öncü kısalır, yerdeyken ayaklar ekranın
~%69'unda (merkez ayakların 50 birim üstü: zemin ve yakın düşmanlar görünür), zıplamada dikey pencere (64 yukarı / 18 aşağı),
hızlı düşüşte aşağı bakış (54 birim), Camera2D konum yumuşatması 6 + sınır yumuşatması, ışınlanmada (>220 birim) anında
oturur. **Boss arenası:** boss ve oyuncu (+ boss boyu) sığsın diye yakınlık `fit` ile en çok 0,62'ye (taban x0,62 = 1,24)
düşer, merkez ikisinin arasına kayar ama oyuncu ekranın iç yarısında kalır; boss en geniş çerçeveye bile sığmayacak kadar
uzaktaysa normal yakın kamera. Yurt v2'de kendi mürekkep sanatıyla 1,6 yakınlıkta (data/yurt_v2.json).
Paralaks ve ön plan kayması birikimli (`_scroll += Δx · yakınlık · fit`): yakınlık değişince katmanlar sıçramaz; sabit
yakınlıkta eski formülle aynı (v1 birebir).
**Doku yoğunluğu (v15):** dünya uzayı (zemin atlası 96 px hücre, toprak 2048², çayır 1024², süsler, kule parçaları)
**4 doku pikseli / dünya birimi** (`export_ink_ortam.WORLD_K` 2,0); ekran uzayı katmanlar (paralaks, ön plan) 1080 yükseklik:
**1080p'de 1 doku pikseli = 1 ekran pikseli**. Üreticiler mantıksal piksellerle yazılır, `inkkit.K` çıktı çözünürlüğünü ölçekler.
Ayrıntılı büyük dokular (paralaks 1/2/3/6, toprak, çayır) BPTC (BC7 yüksek kalite); gök, sis, pus, hüzme ve maske kayıpsız.
v2 dokularının tahmini VRAM'i (mipmap dahil) 220 MB'tan ~205 MB'a indi (daha yüksek çözünürlüğe rağmen).
Bütün v2 ortam dokuları doğrusal süzgeç + mipmap (`.import` mipmaps açık, düğümde `TEXTURE_FILTER_LINEAR_WITH_MIPMAPS`);
v1 yolu hiç değişmez (en yakın komşu, piksel keskin). Yalnızca `--stil=v2` ve `assets/tiles/otuken_v2.json` "ink": true iken.

* **Üretim:** `cd tools/artgen && python export_ink.py [--bg [katman...]|--zemin|--on|--suslar]` (ya da `export_v2.py --otuken`).
  `inkkit.py` (skia-python + numpy): önçarpılmış katman, döşenebilir gürültü, değişken kalınlık fırça darbesi (`ribbon`), ot yaprağı,
  mızrak yaprak, organik kontur, analitik ağaç gövdesi (`trunk`: silindirik gölge, sisten kenar ışığı, iki yanda değişken mürekkep,
  çam = kırık dikey sırt + levha çatlağı, huş = mercimek izi + dal yarası, gölge tarafında çizgi roman taraması, pürüzlü kök
  boğazı; v15: en koyu kenarda çapraz tarama), satır başına sis karıştırma. v15 ayrıntı: yaprakların yarısından çoğu
  mürekkep konturlu ve orta damarlı, dallarda mürekkep sürgünler, otluk/çayır/ot öbeklerinde mürekkep uçlu ve gölge
  kenarı çizgili yapraklar (`blade_tip`, `blade_spine`), kayalar yontulmuş düz yüzeyli (`facet_shade`: Voronoi yüzeyleri,
  gölgeye bakan yüz kenarında mürekkep). `otuken_ink.py` paralaks katmanları, `otuken_ink_ground.py` zemin/ön plan,
  `otuken_ink_decor.py` süsler. Tümü yordamsal; dışarıdan doku yok.
* **Paralaks** (`data/stil_v2.json` "otuken": "bg", "bg_fx", "bg_kind"): 0 gök/uzak sis (1920x1080, sabit; ay ışığının süzüldüğü
  parıltı, tepe yaprak gölgesi), 1 uzak gövdeler (3840x1080, x0,06), 2 uzak-orta gövde + dal + çalı tümsekleri (x0,13),
  2b orta derinlik pusu (v15: yükselen kopuk sis tülleri, "fog", x0,18, 3 px/sn sürüklenir),
  3 orta gövdeler + sise gömülü ahşap gözetleme kulesi + balballar + kayalar + eğreltiler + otluk (x0,24), 4 sürüklenen yer sisi
  ("fog": 7 px/sn kayar, yavaş nefes alır), 5 ışık hüzmeleri ("add": toplamalı, çapraz, nefes alır), 6 yakın koyu gövdeler + tepeden
  sarkan yaprak kümeleri + balballar + kayalar + otluk (x0,44). Atmosfer perspektifi: her katman `SKY` rampasına (zeytin-teal sis,
  en parlak bant oyuncunun ayak hizasının hemen üstünde) satır başına sis payıyla karışır; geridekiler daha açık ve düşük karşıtlıklı.
* **Zemin** (`ground_ink.gdshader`): atlas = sanat RGBA (ot bandı, yar yüzünde mürekkep konturu + soğuk kenar ışığı, tavan altı
  gölgesi, gömülü taşlar, ot öbekleri, kök saçakları, halatla bağlı tahta platform) + maske (`otuken_v2_mask.png`: R toprak
  kaplaması, G kenar gölgesi; CanvasTexture normal yuvasında). Kaplamada dünya uzayı dokular: `_meadow` (sık ot darbeleri; üstteki
  2-3 karo, `Level._top_depth_texture` = yüzeyden dikey derinlik) ve `_soil` (yumuşak tortul bantlar, kök, mürekkepli çakıl),
  derinlikte mor-siyaha kararır. Karo/çarpışma düzeni ve dünya ölçüsü aynı: hücre 72 doku pikseli, katman ölçeği 1/3.
  Örtü katmanı (ot öbekleri) `env_ink.gdshader`. Işık: boyalı dokular ışığı içerir, ay ve çıralar yumuşak/kısık eklenir.
* **Gözetleme kuleleri:** `Level._place_towers` her tek yönlü platform koşusunun uçlarından zemine kütük ayak indirir, geniş ve
  yüksekse X destek, kiriş ve halat bağları ekler (yalnızca görsel; çarpışma değişmez). Boss arenasında da.
* **Süsler** (`decor_v2.json`, `Level._decor_v2`): dilek ağacı (çaputlu huş), kam direği (kartal başlı), kaya, mantar, çiçek,
  çıra (alev ayrı toplamalı doku, titrer), balbal (v2'de seyrek ek yerleşim). v2 karşılığı olmayan süs v1 olarak kalır.
* **Ön plan** (`ForegroundV2.gd`, katman 3): alt kenarda aktörlerin önünde mor-siyah siluet otlar (x1,3 paralaks, rüzgârda salınır,
  `fg_sway.gdshader`), üst kenarda seyrek sarkan dallar (x1,15), ekranda süzülen iri koyu yapraklar; dünyada koyu yaprak
  parçacıkları. Oyuncu ve ekranın alt yarısındaki en çok 5 düşman çevresinde şerit yarı saydamlaşır.
* **Renk derecelendirme** (`grade_v2.gdshader`, vinyetin yerine, katman 5): sahneyi okur; koyuları mora, ortaları zeytin-yeşile
  çeker, hafif S eğrisi ve mor-siyah vinyet; hasar nabzı ("hurt") aynı. Test için `--derecesiz` kapatır.
* **Işık** (`stil_v2.json`): ortam (CanvasModulate) 0,80/0,86/0,88, ay 0,32: boyalı ortam neredeyse kendi renginde görünür;
  aktörler v1'e göre daha aydınlık (karakter v2 sanatı bu ışıkla dengelenmeli).

### Bozkır Kurganları ve Kaf Dağı v2 "mürekkep" ortamları

Ötüken mürekkep kurgusunun (kamera 2,0, dünya uzayı 4 doku pikseli / birim, paralaks 1080 yükseklik, BPTC) biyoma özgü
uygulaması. Üretim: `cd tools/artgen && python export_ink_biyom.py bozkir kaf [--bg [katman..]|--zemin|--on|--suslar|--tehlike]`
(yalnızca `<biyom>_v2*` dosyaları; v1 ve Ötüken dokunulmaz). Kod: `ink_biyom.py` (biyomdan bağımsız: gök rampası, dağ sırası =
sırt çizgilerinden cel yüz gölgesi + kar + kesik mürekkep + ters ışık siluet kenarı, yumuşak tepe, boyalı küme bulut, otluk,
tül, yelpaze hüzme, kar tanesi), `ink_zemin.py` (Ötüken zemin kurucusunun üsluba bağlı genellemesi: ot bandı ya da kar
başlığı, çatlak ağı, döşenen doku), `bozkir_ink*.py`, `kaf_ink*.py`, `ink_tehlike.py`. Tümü yordamsal, dış kaynak yok.

* **Bozkır (alacakaranlık, ışık sağdan, ters ışık):** gök mor-indigodan yanık turuncu ve altın ufka; ufukta batan güneş,
  alttan yanan küme bulutlar; Altay sıradağları (güneşe bakan siluet kenarı altın); dalgalı tepelerde kurganlar, balbal
  dizisi, keçe yurt obası (kapıda ocak ışığı, tünlükten duman), at sürüsü; ortada taş halkalı büyük kurgan, kaplumbağa
  kaideli Orhun yazılı bitig taşı, kurt başlı tuğlar, mavi-ak çaputlu oba taşı; önde yalnız kuru karaağaç, kazıklar, at
  kafatası dikili sırık, kılçık otu. Hava: toz pusu ve savrulan alçak toz ("fog", sürüklenir), güneşten yelpaze hüzme
  (sabit "add"), hızlı rüzgâr çizgileri. Zemin: kuru altın ot bandı (rüzgâra yatık), çatlak lös toprak (çokgen kuruma
  çatlakları, kemik kırıkları), kuru çayır; örtü: sorguçlu kılçık otu, deve dikeni, yavşan, bozkır lalesi (rüzgârda
  salınır: `tuft_sway`); platform: ağarmış tahta, ham deri bağ, at kılı püskül, uçlarda koçboynuzu desenli keçe flama.
  Tehlike (diken): kanlı uçlu kazıklar. Parçacık: yatay savrulan kuru ot kırıntısı (`leaf_ramp`, `leaf_dir`).
* **Kaf Dağı (gece-şafak, ışık soldan):** yıldızlı gök, hilal, kutup ışığı perdeleri (ayrı "add" katmanı, nefes alır);
  dev Kaf zirvesi zümrüt ışıltılı ve şafak pembesi, çevresinde Zümrüdüanka; karlı ladin ormanlı sırtlar, kaya yüzünde donmuş
  çağlayanlar, buz kristali kümeleri, karlı kam direği; önde karla yüklü koyu dev ladinler. Hava: vadide soğuk pus, tipi
  tülleri, iki derinlikte düşen kar (ParallaxBG yeni "snow" türü: iki yönde döşenir, `bg_fx[3]` px/sn düşer), ön planda iri
  kar taneleri. Zemin: yuvarlak dudaklı kar başlığı (mavi gölge, mürekkep, kenarda buz saçağı), katmanlı kar örtüsü
  kesiti, buz damarlı arduvaz kaya; örtü: kırağılı ot, kar tümseği, buz kristali, karlı ardıç, kardelen; tavan: buz
  sarkıtları; platform: karlı koyu tahta, altında saçaklar. Tehlike (buz): çukurda donmuş göl.
* **Süsler:** `decor_v2_<biyom>.json` + `<süs>_<biyom>_v2.png`; `Level._decor_v2` önce biyom adını arar (yoksa ortak
  `_v2`). "noflip": yönlü ışıklı süsler aynalanmaz; "glow_pulse": soğuk ışıma yavaş nefes (buz kristali). Biyom ek süsleri
  `stil_v2.json` "ink_extras" (aralıklı) ve boss arenası için "boss_extras" (sabit "at" konumları): bozkır balbal, oba taşı,
  bitig taşı; Kaf ladin, buz kristali. Kule parçaları da biyoma özgü (`kule_*_<biyom>_v2`).
* **Diğer art anahtarları (yalnızca bu biyomlar):** `meadow_depth` (çayır/kar örtüsü kalınlığı), `tuft_sway` (+ env_ink
  `cell_px`), `leaf_ramp/leaf_dir/leaf_grav/leaf_vel`, ön plan `fg.leaf_dir/leaf_grav/leaf_vel/leaf_scale/leaf_emit`.
  Tehlike: `assets/tiles/hazards_<biyom>_v2.png` (v1 satır düzeni, 96 px hücre). Ötüken'in davranışı değişmez.
* **Başarım (UHD 750, 1080p, --otomatik):** Bozkır v2 ~47 fps (Ötüken v2 ~30, Bozkır v1 ~32); Kaf v2 ~35 (yoğun dövüşte
  15-20, Ötüken v2 de 14'e iner).

### Şahmeran Mağaraları ve Tamu (Erlik'in Ülkesi) v2 "mürekkep" ortamları

Ötüken ile aynı dil (değişken kalınlıklı mavi-siyah mürekkep, boyalı dokular, satır başına sis/pus, 1080p'de 1:1 doku),
yeraltına göre ışık: Şahmeran'da ışık kristallerden ve tavan çatlaklarından, Tamu'da aşağıdan lavdan gelir.
* **Üretim:** `cd tools/artgen && python export_ink_yeralti.py sahmeran|tamu|hepsi [--bg [katman...]|--zemin|--on|--suslar|--tehlike]`.
  `inkkit_yeralti.py` ortak parçalar: `lathe` (dönel katı: sarkıt/dikit/sütun; silindirik ışık, kenar ışığı, ıslak parıltı,
  halka çıkıntıları, akıntı çizgileri, gölge taraması), `crystal_cluster` (iki yüzlü altıgen prizmalar + ayrı ışıma
  tuvali, `halo`), `reflect` (katmanın su çizgisi üstünü dalgalı, kararan yansıma olarak suya düşürür + parıltı
  çizgileri), `chain` (katener halka zincir), `basalt_prism` (üç yüzlü altıgen sütun, eğik kesik tepe, eklemler,
  lav kenar ışığı), `rib` (kaburga kemiği), `lava_fall`, `smoke_layer`. `inkkit_zemin.py`: biyomdan bağımsız atlas
  kurucusu (Ötüken yerleşimi; biyom `Spec`: üst bant, gömülü süs, örtü öbekleri, tavan, platform) + ışıma atlası.
  Biyom dosyaları: `sahmeran_ink_ortam.py` / `tamu_ink_ortam.py` (paralaks; `sahmeran_ink.py` boss çizimidir),
  `*_ink_ground.py` (atlas, dokular, ön plan, parçacık), `*_ink_decor.py` (süsler), `hazard_ink.py` (sıvı veri dokusu).
* **Şahmeran paralaksı:** 0 uzak mağara (kubbe, sisli kütleler, kristal bokehi) · 1 kum saati sütunlar, kayaya oyulmuş
  Şahmeran sarayı (basamaklı teraslar, kehribar ışıklı kemerler, yılan başlı burçlar), yansımalı göl · 2 sarkıt perdesi,
  dikitler, kristaller, göl · 2b teal pus · 3 yılan kabartmalı sütunlar (sarmal yılanın ön kıvrımları, karın pulları,
  başlıkta kehribar gözlü kukuletalı baş), kıyı setleri, kristaller, yansıma · 4 göl sisi · 5 tavan çatlağı hüzmeleri +
  ışıklı zerreler (toplamalı) · 6 yakın koyu sarkıt/dikit, ıslak kaya kıyısı, parlak kristaller.
* **Tamu paralaksı:** 0 tutulmuş kara güneş (açısal gürültülü ateş tacı), lavla alttan aydınlanan duman kuşakları · 1
  volkanik sırtlar, Erlik Han'ın boynuzlu demir kalesi, lav şelaleleri, perspektifli kabuklu lav denizi + yansıma · 2
  bazalt org boruları, şelaleler, lav denizi · 2b kızıl duman · 3 zincir gerili bazalt sütunlar, dev kaburga kemerleri,
  boynuzlu öküz kafatası, kül zemin · 4 alçak duman · 5 lav ışıması, ısı tülleri, yükselen korlar (toplamalı) · 6 yakın
  bazalt sütunlar, kancalı zincirler, kemik çıkıntıları.
* **Boss arenası** (`stil_v2.json` "boss_bg" -> `Level.build_boss` paralaks listesini değiştirir): orta katman
  `<biyom>_v2_3_mid_boss`: Şahmeran Ana'nın kobra tahtı (taçlı dev kobra kukuletası, sarmal oturak, kristalli kürsü) ve
  Erlik Han'ın demir tahtı (öküz boynuzları, kara güneş amblemi, kafatası basamaklar, lav mangalları, sancaklar).
* **Zemin:** Şahmeran: ıslak koyu kaya, yosun yastığı üst bant (ışık sporları), yan yüzde kristal kümesi, oymalı taş
  platform (pul frizi, kehribar taşlı yılan başı), dünya uzayı tortul kaya (kristal damarları ve geod cepleri ışır) +
  yosun dokusu. Tamu: sütunlu bazalt (Voronoi eklemler, bazı eklemler lav), kül örtüsü (kor tanecikleri), yan yüzde lav
  çatlağı, demir kuşaklı bazalt platform (kafatası süsü), kül dokusu. Örtü: Şahmeran yosun/eğrelti, kristal filizi,
  ışıyan mantar, yılan iskeleti; tavanda damlalı sarkıt, ışıl böceği iplikleri, sarkık kristal. Tamu kül tümseği, kor
  öbeği, kafatası/kemik, demir kazık, bazalt kıymığı, alev dili, kömür çalı; tavanda lav damlası, kancalı zincir.
* **Işıma:** `ground_ink.gdshader` `soil_e` + `emit_gain` (art "soil_emit") + `emit_pulse` (nabız, derinde söner; 0 =
  kapalı, Ötüken değişmez); atlas ışıması `<id>_v2_e.png` yalnızca `emit_cells` hücrelerinde ayrı ADD + gölgesiz karo
  katmanında (`Level._lay_emit_tiles`, art "tile_emit" çarpanı). Işıma dokuları kenarda söner (`inkkit_zemin.edge_fade`).
* **Süsler** (`decor_v2_<biyom>.json`, ad karşılıkları): dilek_agaci -> Şahmeran heykeli / kara kayın (zincir, demir
  kafes), kam_diregi -> yılan ongunu / Erlik ongunu (boynuzlu öküz kafatası), cira -> kristal kandil / demir mangal,
  kaya, mantar (ışıyan mağara / ateş mantarı), cicek (kristal filizi, mağara zambağı, eğrelti / kemik yığını, alev ağzı,
  dikenli çalı), balbal -> yılan yuvası / kafatası kazığı (art "ink_extras" ile Ötüken'den seyrek); platform ayakları sarmal yılanlı taş sütun (çapraz yok,
  art "tower_brace": false) / bazalt sütun + zincir çapraz + demir kelepçe.
* **Tehlike:** art "hazard_v2" varsa zehir / lav karoları yerine her bağlı bölgeye tek çokgen (`liquid_ink.gdshader`,
  `Level._build_hazards_ink`): dalgalı yüzey (mürekkep + parlak kenar), lavda kabuk plakaları arası ışıyan çatlaklar,
  zehirde girdap, köpük ağı, yükselen kabarcık halkaları; karo katmanı gizli kalır (hazard_at aynı). Test: `--tehlikeye`
  oyuncuyu ilk havuzun yanına koyar (ör. `--derinlik=5 --tohum=4`, `--derinlik=9 --tohum=4`).
* **Parçacık / ön plan / derecelendirme:** Şahmeran: spor + tavandan düşen damla (art "drip_tex"), ön planda dikit
  ve kristal siluetleri, sarkıt/yosun saçağı; derecelendirme gölgeleri maviye. Tamu: kor + kül, ön planda bazalt sivri
  / kemik ve sarkan zincir siluetleri; derecelendirme gölgeleri bordoya, `grade_v2` "heat" ısı dalgası (art "heat_haze").
* **Ölçüm** (Intel UHD 750, 1280x720, vsync kapalı, 900 kare): Ötüken v2 ~45 FPS, Şahmeran v2 ~45, Tamu v2 ~46.
* **1080p çekim:** proje pencere ezmesi 1280x720 olduğundan `--write-movie` 720p yazar; geçici `override.cfg`
  (`window/size/window_{width,height}_override=1920/1080`) + `--pencere=1920x1080` ile gerçek 1080p kare alınır (dosya
  çekimden sonra silinir, depoya girmez).

### Stil v2 "mürekkep-cel" karakterler (çizgi roman; piksel sanatın yerini alır)

Referans yeniden okundu: Shinobi: Art of Vengeance piksel sanat değil, el çizimi çizgi roman / animasyon. v2 karakterleri
artık bu yönde: `bengu_v2` ve `kara_boru_v2` (`bengu_kol_v2` dahil) `tools/artgen/export_ink.py` ile üretilir
(`bengu_v2.py` piksel sürümü arşiv olarak durur; `export_v2.py --bengu` çalıştırılırsa piksel sürüm geri yazılır).

* **Çizim takımı** `tools/artgen/inkkit.py` (skia-python): her parça kapalı bir vektör yol. Düz taban + tek sert gölge
  tonu (yol − ışığa kaydırılmış kopyası: ışığın tersinde hilal; gölge tonu mor-maviye kayar) + küçük sert parlama +
  isteğe bağlı derin gölge bandı, kumaş kıvrımı (`fold`: gölge kaması + incelen mürekkep çizgisi), seyrek tarama,
  parça içi hafif değer geçişi, alttakine düşen gölge (`cast`, kModulate). Kontur: yol boyunca örneklenen fırça
  darbesi; ışık yanında ~1.5 px, gölge/alt yanda ~4 px (1080p), düşük frekanslı baskı değişimi; dış silüete +0.5 px.
  Bütün gövdeye büyük kütle gölgesi (`form`), isteğe bağlı iç kenar ışığı (`rim`, tazıda açık). Mürekkep #15161d.
  Işık sol üstten (`LIGHT`). 3x süper örnekleme + kutu küçültme; çıktı albedo + ışıma (göz, kor) PNG.
* **Yoğunluk (v15):** `texel` 4 (dünya 480x270 x4 = 1080p'de 1 doku pikseli = 1 ekran pikseli). Bengü hücresi 384x320
  (dünya 96x80, ayak 176,296), tazı 320x224, kol parçası 56x68 (pivot 28,14; yumruk 28,34). Çizgi genişlikleri `lw` =
  (k/3)^0.85 ile ölçeklenir (göreli olarak biraz daha ince, daha çok ayrıntı).
* **Sayfalar:** `export_ink.py` sayfayı en çok 4096 px yüksek parçalara böler (`<ad>.png`, `<ad>_p1.png` ... + `_e`;
  json "page_rows", "pages"). `Data.sprite` sayfa dokularını yükler ("page_texs"/"page_glows"), `SpriteAnim._apply` satırın
  sayfasını seçer; hayalet/ceset/vuruş karesi `base.texture`'ı kopyaladığı için kendiliğinden doğru. Sayfasız json (v1) aynen.
  Bengü: 3 sayfa (3072x3840, 3072x3840, 3072x2560) BPTC + mipmap; 16384 (ve eski GPU'lardaki 8192) sınırının altında.
* **Kalite katmanı (v15, `inkkit.py`):** kontur ışık yanında incelir ve yer yer kırılır (boşluğun uçları sivrilir), gölge
  yanında kalınlaşır, dış kenarı kuru fırça gibi pürüzlü; sert cel gölgesinin ışık yanına taşan bulanık ikincil yarı ton
  (`soft`); büyük parçalarda gölgenin uzak kenarında yansıyan ışık (`bounce`); metalde ışıklı kenara paralel karanlık ufuk
  yansıması + keskin beyaz parlama + küçük ışıltı (`kind='metal'`); postta kenardan içe sivri kıl darbeleri (`kind='fur'`,
  koyu postta açık tonla); bitirişte dolgular içinde %4,5 çapraz fırça/kâğıt dokusu (karede sabit, `paper_grain`).
* **Kol iskeleti gölgesi (düzeltildi):** `bengu_kol_v2.png` iki satır: 0. satır sol üst ışık, 1. satır ışığı parça
  ekseninde aynalanmış çizim (json "alt_row"). `ink_char.gdshader` (`alt_uv`) parçanın ekrandaki dönüşünü, esnemesini ve
  flip_h'sini UV/dünya türevlerinden çözer; dünya ışığı dokuda hangi yandan geliyorsa o çizimi seçer (yumuşak geçiş). Kol
  başın üstüne kalksa ya da Bengü sola dönse de gölge ışığın tersinde kalır. Gövde sprite'larında `alt_uv` 0 (kapalı).
* **Kol biçimi:** "kütük" kol yerine anatomik profil: omuz kası şişkin üst kol, dirsek içinde zikzak kumaş kıvrımları,
  dirsek çıkıntısı ve bileğe incelen ön kol, sırma kol ağzı, çapraz bağcıklı deri siper + çelik şerit, parmak araları ve
  sarılı başparmağı okunan eldivenli yumruk.
* **Yuvarlanma:** bütün gövdeyi döndürmek yerine dalış -> top (sırt kıvrılır: gövde ekseni %32 kısalır, uyluklar göğüste,
  baldırlar katlı, kollar baldırları sarar, baş içeride, top %14 büzülür ve yere değerek döner) -> açılıp çömelerek kalkış
  (`bengu_ink._roll`, 8 kare, zamanlama aynı). Işık dünyada sabit (dönüş çizimden önce uygulanır).
* **Oyunda:** json `"filter": "linear"` olan sprite'lar (`Data.is_linear`) CanvasTexture'da `LINEAR_WITH_MIPMAPS`
  ile ve `shaders/ink_char.gdshader` ile çizilir (`SpriteAnim`, `Player` kol iskeleti; hayalet/ceset/vuruş karesi aynı
  CanvasTexture'ı kullandığından süzgeci miras alır). `.import`: mipmap açık; büyük sayfalar (bengu_v2, _e) VRAM
  sıkıştırmalı (BPTC), küçükler kayıpsız. v1 sprite'ları değişmedi (en yakın komşu + toon_light).
* **Işık kararı:** normal haritası YOK. toon_light normalden 3 bant çıkarır; cel gölgesi zaten dokuda olduğundan
  düz yüzey tek banda düşer ve gölge iki kez uygulanır. ink_char ışığı yalnızca renk/şiddet olarak taşır (ay için
  `light_k` 0.85, noktasal ışık `point_k` 0.9, `moon_shade`, `flash`, `tint` aynı adlarla). Böylece çizilmiş ışık
  yönü bozulmaz, sahne ışığı (çıra, Kut) karakteri renklendirir.
* **Bengü (`bengu_ink.py`):** iskelet ve çapalar v2 ile aynı (kol 10 + 9.4, gövde 17, kalça -23.6); bacak 13 + 12.6
  (ninja oranı), baş x0.9. Kaftan uyluk ortasına kısaldı (bol çivit şalvar görünür, çizme baldır ortasında), etek
  önü dizleri izler (adım açılınca uyluğun üstünden gerilir). Pozlar: geniş/alçak bekleme, ninja koşusu (sprint:
  kollar geride), sıçrama/düşüş/iniş/çömelme/yaralanma yeniden kurgulandı; saldırı gövdeleri v1/v2 anahtarlarından
  `dynamic()` ile (daha açık adım, derin diz, fazla eğilme) türetilir, zamanlama aynı (Player.SWINGS uyumlu). Yere
  basan pozlarda kalça yüksekliği ayaklardan çözülür (`ground`, FOOT_Y -2.1). Çarpışma kutuları değişmedi.
* **Erlik Tazısı (`kara_boru_ink.py`):** creatures.draw_hound iskeleti/pozları ve `mouth` çapası; koyu post, kemik
  zırh, dumanlı yele (kor uçlar), kor göz/ağız ışıması, soğuk ay kenar ışığı.
* **Araçlar:** `preview_ink.py out.png [--mod m] [--zoom 2] [--all | --anim ad | anim:kare ...]`,
  `compare_ink.py referans.png out.png anim:kare ...` (referansla aynı 1080p ölçeğinde). Karşılaştırmalar:
  `rec_v14/karakter/` (depo dışı).
* **Bilinen eksikler:** silah atlası, efektler ve diğer yaratıklar hâlâ piksel (2,0 yakınlıkta piksel silahlar daha
  belirgin); kol gölgesi iki çizim arasında karışır (kol tam dikeyken ara ton); 1440p/4K için v2 HD paketi yok (texel 4
  1080p'ye göre; 1440p'de 1,33x büyütülür).

* **Bilinen eksikler:** diğer yaratıklar hâlâ piksel (silah atlası, savuruş izi, vuruş efektleri ve kan: aşağıdaki
  "mürekkep fırçası" bölümü); ön kol iskeleti parçalarının gölgesi
  parça yerelinde çizili (kol başın üstüne kalkınca ışık yönü dönmüş görünür); yüz/el ayrıntısı 1080p'de küçük
  (oyun kamerası karakteri ~115 px gösteriyor, referansta ~185 px: kamera yakınlaştırması ortam tarafında).

### Stil v2 mürekkep fırçası: savuruş izi, vuruş efektleri, silahlar, kan

Referans: Shinobi: Art of Vengeance'taki kızıl fırça darbesi (kalın kuru fırça hilali, pürüzlü kıl kenarları, koyu
kızıl çekirdek, turuncu-kızıl gövde, siyah fırça izleri, zerreler). Yalnızca `--stil=v2`; v1 yolları değişmez
(`FX.ink()` = `Data.stil == "v2"`). Hepsi yordamsal (dışarıdan doku yok).

* **Savuruş izi** (`scripts/core/InkTrail.gd`, `shaders/ink_brush.gdshader`): `FX.trail` v2'de `InkTrail` verir
  (WeaponTrail alt sınıfı, aynı `add/done/life` arayüzü; Player yalnızca `setup(it, atk, ağırlık)` çağırır). Şerit
  bıçak ucunun süpürdüğü alan (SÜPÜRME) ya da uç yolu (YOL: saplama, kırbaç; Catmull-Rom ile yumuşatılır). Genişlik
  fırça baskısı: ucun ilk yolu ince başlar (`ramp_len`), hızlı orta kısım dolgun karın, yaşla incelir, kuyruk ucu her
  zaman sivri. Uç bıçak ekseni boyunca kayınca (geriden öne savurma) enine yön yol normaline kayar (çizgiye çökmez).
  Gölgelendirici: kıl dokusu (`assets/fx/ink/bristle.png`: R kıl yükü, G koyu fırça izleri, B kıl kimliği, A tane),
  iç kenar kuru ve pürüzlü, dış kenar keskin; kuru fırça boşlukları; koyu kızıl çekirdek bandı + siyah/koyu kızıl
  fırça izleri; bıçağın hemen arkasında HDR sıcak ön kenar (bloom), kısa dış ışıma; yaşlandıkça kenardan yenir ve
  kıl tellerine ayrılarak erir. Mip düzeyi yalnızca enine türevden (`textureGrad`). Mürekkep zerreleri / kıvılcımlar
  aynı üçgen dizisinde: iz başına tek çizim çağrısı, düğümler havuzda (`InkTrail.acquire`). Köşe verisi yalnızca UV
  ve COLOR.a'da (HDR 2D'de COLOR.rgb doğrusala çevrilir).
* **Tasarımlar** (`InkTrail.setup`): kılıç temiz hilal (genişlik bıçak boyunun %62'si) · ağır (gürz, topuz, çekiç,
  balta, ulu/bozgun kılıcı) geniş (%95), daha kuru, kalın siyah izler, iri zerreler, bitişte uçta sıçrantı · uzun sap
  (teber, tırpan, asa) ince uzun hilal · hançer (ikiz bıçak, böri hançeri, pençe) hızlı çift fırça (içte ikinci ince
  darbe, en az 4 birim) · saplama savuruşları (mızrak, lunge, flurry) düz fırça çizgisi + iki soluk yankı · kırbaç
  (kement, od kamçısı) ince kıvrak şerit, baş iğne gibi. Ağır / bitiriş: arka koyu geniş katman; tam şarj ve bekleme
  bitirişinde + dış ikinci ince hilal. Paletler (`InkFX.PALETTES`, sRGB → doğrusal): 0 kızıl (referanstan ölçüldü),
  1 od, 2 ayaz, 3 zehir, 4 ruh, 5 yıldırım, 6 erlik/bozgun, 7 ay, 8 yel/kayın, 9 altın; silah kimliği (`ID_PAL`)
  ya da malzeme (`MAT_PAL`: od taşı, ayaz, ruh, gök demiri).
* **Vuruş efektleri** (`scripts/core/InkFX.gd`, `shaders/ink_fx.gdshader`, atlas `assets/fx/ink/ink_fx.png` +
  `ink_fx.json`; `tools/artgen/inkfx.py`): atlas veri taşır (R işaretli uzaklık alanı, G koyu/sıcak çekirdek, B çizim
  sırası, A erime gürültüsü), renk paletten. Şekiller: patlama yıldızları, yönlü patlama, kritik damgası, fırça
  dokunuşları, damlalar, ensō, iki kesik izi, yönlü sıçrantı, kıvılcım yıldızı, kuru halka, pençe, yer sıçrantısı.
  `InkFX.hit` (kesik izi savuruş yönünde: taze izin uç yönünden; yönlü yıldız; kademe 1+ fırça dokunuşu; kademe 2
  arkaya sıçrantı), `stamp` (kritik: siyah damga + kızıl patlama + beyaz-sıcak kesik), `slam` (yer sıçrantısı;
  GroundSlamFX v2'de yalnızca sarsıntı/ışık ve yumuşak toz verir, piksel flaş/şok/moloz/çatlak çizmez), `flourish` (savuşturma: ensō + kıvılcım; kusursuz kaçış: ayaz ensō + halka), `ring`,
  `kill`. Açılış ilk karede %62 hazır (hitstop'ta zaman durur; donmuş karede boş kalmaz). Vuruş izden önce işlendiği
  için palet ilk karelerde yakındaki taze izden alınır (`auto_pal`). FX yönlendirmeleri: `slash_sprite` (yay/çizgi/
  halka/x: iz zaten çizer; spark_m / crit_burst / kill_flash → mürekkep; boss arc_* → `InkTrail.auto_arc`),
  `impact_sprite`, `impact`, `slash` (düşman yayı → kendiliğinden süpürülen fırça), `ring`, `ground_slam` (+ mürekkep
  sıçrantısı), darbe animasyonları (`FX.INK_ANIM`: PVFX piksel kareleri yerine mürekkep), parçacık ve kalan
  animasyonlarda doğrusal süzgeç (yakın kamerada bloklaşmasın). Player'da savuşturma ve kusursuz kaçışa birer satır;
  `_slash_fx` v2'de erken döner (bitiriş/ağır/özel savuruşların büyük hilali izin katmanlarıyla çizilir).
* **Silahlar** (`tools/artgen/weapons_ink.py` → `assets/weapons/weapons_v2.json` + `weapons_v2_<n>.png`): geometri
  v1 `weapons_myth.draw_item` ile birebir (aynı kimlik, pivot, dünya boyu); hacim tuvali 2x süper örneklemle
  rasterlanıp mürekkep-cel boyanır: düz taban + tek sert gölge tonu + ışığa bakan pah için açık ton, metal/taşta
  küçük keskin parlama ve bıçak boyunun %62'sinde çift çapraz çizgi roman parıltısı, alttakine düşen gölge,
  dış silüet ışık yanında ince / gölge yanında kalın mürekkep (#15161d), parçaların üst üste geldiği yerde ince iç
  çizgi; ahşap damarı, sargı, süs, ışıyan damarlar v1 boyamasından; kılıç bıçaklarının kökünde kazınmış koçboynuzu
  süsü (koyu oyuk + altında ışık çizgisi). Doku 4 piksel / dünya birimi (v2 kamerası 2x:
  1080p'de 1:1). Eşya başına 11 malzemeye ortak sıkı kırpma, raf paketleme, 4096 genişlikte sayfalar (şu an tek
  sayfa 4096x1920; 4096x8192 dolunca yeni sayfa). `Data.weapon_sprite(kimlik, malzeme)` → {tex, region, pivot,
  scale, linear}: Player kol iskeleti (`_apply_wspr`, ink_char gölgelendiricisi), Projectile, Pickup kullanır;
  arayüz simgeleri v1 piksel atlasında kalır. `python weapons_ink.py [--is N] [--onizleme x.png]` (~1 dk).
* **Kan** (`Blood.gd`, `shaders/ink_blood.gdshader`): fizik aynı; damla hız yönünde gözyaşı fırça zerresi, zemin
  lekesi düzensiz mürekkep lekesi (koyu kenar, ıslak parlama, uydu noktalar; yakına düşen damla mevcut lekeyi
  büyütür: kenarda ince kırmızı çizgi yerine iri seyrek lekeler), duvar akıntısı incelen fırça izi, et parçası
  mürekkep konturlu parça. Her katman tek üçgen dizisi.
* **Test:** `-- --stil=v2 --firca[=silah,silah:malzeme,...] [--firca_bos]` (`tools/tests/firca_testi.gd`: her silahta
  3'lü zincir, basılı ağır saldırı; sonunda savuşturma ve kusursuz kaçış; "[firca] ... kare=N ekran=x,y" satırları).
  Çekimler ve referans yan yana karşılaştırmaları `rec_v15/firca/` (depo dışı).

### Stil v2 mürekkep: Ulu Kayın Yurdu, ortak süsler, toplanabilirler, mermiler, tehlikeler, efektler

Piksel kalan dünya nesnelerinin mürekkep-cel karşılıkları. Hepsi yordamsal (skia-python + numpy), `--stil=v2` dışında
v1 çizimi aynen durur. Üretim: `cd tools/artgen && python export_sus.py [--yurt [ad...]|--yurt-bg|--suslar|--atlas|--tehlike|--efekt]`.

* **Ortak takım** `tools/artgen/inkprop.py`: `Prop` (dünya biriminde InkCanvas, `TEX` = 4 doku pikseli / dünya birimi,
  köken ayak noktası), gece malzemeleri (ak keçe, kilim kızılı, lacivert, firuze çini, altın, tunç, demir, kayın kabuğu...),
  alev (`flame`: ışıma katmanına da yazar), koçboynuzu (`ram_motif`), püskül, ot tutamı. Süs meta biçimi `decor_v2.json` ile
  aynı ama ayrı dosyada: `assets/decor/sus_v2.json` (`Level._decor_v2` ikisini birleştirir; biyom süsleriyle dosya çakışmaz).
* **Ulu Kayın Yurdu** (`yurt_ink.py`, adlar v1 + `_v2`, köken/dünya boyu v1 ile uyumlu, yerleşim `_place_hub` ortak):
  han otağı (silindirik duvar gölgesi + saçak, kavisli kilim kuşakları, kolan ipleri, altın kaburgalar, koçboynuzlu kızıl kapı,
  kapı aralığından sızan ışık, tündükte tuğ), süslü yurt, dilek kayını (çaputlar rüzgârda, ışıyan kut yaprakları), kuş başlıklı
  Umay heykelli sunak, ışıyan çağlayanlı pınar, demirhane (kor ağızlı taş ocak, saçak, alet askısı, silah sehpası, körük, fıçı),
  örs ve kızgın kılıç, bürküt tüneği, eğerli doru at, Ozan'ın kilimi + minderler + kopuz, yer kilimleri, taş yol, seki,
  mangal / kandil / fener / kazan (alevler `_e` ışıma, titrer), kızıl ve gök tuğlar, balballar, Orhun runlu kurgan, güneş
  kurslu taç kapı. `Level._hub_prop` v2'de `_hub_prop_ink` (env_ink, doğrusal + mipmap, ışıma nefes alır); bayrakçık dizileri
  kenar yumuşatmalı, mürekkep konturlu, alt uçları cel gölgeli.
* **Yurt paralaksı** (`yurt_ink_bg.py`, `data/yurt_v2.json`): 0 gök (çivit, kuzey ışığı perdeleri, samanyolu, Ülker, Demir
  Kazık, mürekkep konturlu hilal), 1 karlı sıradağlar ve ardında göğü tutan Ulu Kayın (ak gövde, dallar, yaprak kütleleri
  kuzey ışığıyla kenarlı, ışıyan kut yaprakları), 2 uzak oba (kapısı yanan yurtlar, duman, tuğ, kamp ateşi, at sürüsü),
  3 huş korusu + fenerli çit + balballar, 4 sürüklenen gece sisi. `yurt_v2.json` yurdun art değerlerini ezer (ışık, derecelendirme,
  ön plan otları) ve **kamerayı v2'ye alır**: `camera_zoom` 1,6 (yurt vitrin: biraz daha geniş kadraj; CameraV2).
* **Ortak süsler** (`sus_ink.py` DECOR): Tengri sunağı (lütuf odası `_decor("sunak")`), Kut Kapısı (`KutGate.gd`: kemer +
  karanlık eşik + ters dönen iki kut girdabı; v2'de piksel `rift_portal` oynamaz; yurtta yalnızca eşik + girdap, çerçeve taç
  kapı), Davul Totemi (`Totem.gd`: gövde ezilip zıplar, tüyler salınır), ruh taşı kapağı (`Alem`: mor damarlı kara taş,
  Erlik mührü nabız gibi atar, yeraltında saydamlaşır), Ülgen'in altın bulutları (`Alem._CloudVis`, 4 çeşit).
* **Atlas** (`assets/fx/ink/sus_v2.png` + `_e` + json; `scripts/world/SusV2.gd`): altın sikke (döner), kut damlası, şifa otu,
  tılsım (kaide + salınan muska), parşömen, eşya kaidesi, don ruhu, ruh kuşu (iki kare), oklar (6 tür, serbest açıyla döner;
  saplanan ok düşmanda kalır), sapan taşı, kaya, buz, ateş topu, spor, lanet, tüy, hayalet kartal, yel dalgası, yer dalgası,
  kök. `Pickup` / `Projectile` v2'de sprite kullanır, `_draw` yalnızca nadirlik zerrelerini ve kenar yumuşatmalı izi çizer.
* **Tehlike karoları** `assets/tiles/hazards_v2.png` (+ `_e`, 96 px hücre, 2 kare): diken, zehir, lav, buz; biyomdan bağımsız,
  `Level._build_hazards` v2'de doğrusal süzgeçli env_ink ile döşer.
* **Efektler** (`sus_fx.py`, `assets/fx/anim/<ad>_v2.png` + `anim_v2.json`): smoke_puff, radiant_heal, hush_lock,
  focus_charge, splash_crown, landing_dust; kare sayısı / hız / pivot v1 ile aynı, hücre 384 (texel 4). `AnimFX` v2'de bunları
  seçer (`tex_k`), `FX.anim` ölçeği çarpar. Kök dikenleri, alev gölü, yer uyarısı v2'de kenar yumuşatmalı mürekkep çizimi;
  darbe karesi siluetleri doğrusal süzgeçli.
* **Gizli oda ganimeti (düzeltme, iki stilde):** eşya, şifa ve altın kapağın (cover, z 6) altında (z 5) çizilir, bu dünyadan
  görünmez ve ışığı yanmaz; yalnızca yeraltındayken ya da odanın içindeyken görünür ve alınır (`Alem.loot_open`, altın
  mıknatısı ve `Level.nearest_item` buna uyar).
* **Test:** `-- --stil=v2 --yurt --sus=yurt --cikti=<klasör>` (yurdun 9 durağı), `-- --stil=v2 --sus=dunya --cikti=<klasör>`
  (toplanabilirler, mermiler, Kut Kapısı, bulut, ruh taşı, oda; "kapak üstü altın farkı=0" kontrolü). `tools/tests/sus_testi.gd`.
  Çekimler `rec_v16/sus/` (depo dışı).
* **Kalanlar:** NPC'ler (yaratık sırası), ceset/erime, hasar sayıları (arayüz) bu bölümün dışında.



### Stil v2 yaratıklar (A takımı): Çor, Kara İye, Balbal, Kara Kam ve biyom çeşitlemeleri

Dört temel sprite ve onları paylaşan düşmanlar mürekkep-cel olarak yeniden çizildi; biyom tonu (`tint`) yerine her
düşmanın kendi çizimi var (`<kimlik>_v2`). Pozlar, kare sayıları, fps/döngü, çapalar (`mouth` = fener, `hand` = yumruk /
lanet küresi) ve çarpışma v1 ile aynı; hücreler dünya biriminde biraz geniş (mürekkep konturu ve savrulan parçalar sığsın).

* **Çalışma zamanı:** `Enemy.setup` v2'de düşmanın kendi kimliğiyle `_v2` sprite'ı varsa (ör. `kan_yarasasi_v2`) onu
  yükler ve biyom tonunu uygulamaz (renkler çizimde); yoksa `def.sprite` (ör. `cor` -> `cor_v2`). v1'de `stil_id` kimliği
  aynen döndürdüğü için hiçbir şey değişmez. Seçkin/durum tonları aynı.
* **Üretim:** `cd tools/artgen && python export_yaratik_a.py [--cor|--iye|--balbal|--kam] [kimlik ...]` (~1,5 dk, süreç
  havuzu). Çizim: `cor_ink.py`, `agac_iyesi_ink.py`, `balbal_ink.py`, `arcura_ink.py` (her biri `VARIANTS` sözlüğü:
  malzemeler + biçim anahtarları), ortak ekler `yaratik_ink_kit.py` (bulanık ışıma `glow_soft`, ışımanın z sırasına
  göre örtülmesi `occlude_glow` — arkada kalan fener/çatlak ışığı önündeki gövdeden sızmaz, yırtık kenar, zincir, kemik
  el, buz sarkıtı, duman teli `wisp`, bulut patlaması `cloud`, kıvılcım). Önizleme: `python preview_yaratik.py x.png
  --mod cor_ink --var all --glow --all`. Oyun içi çekim: `-- --stil=v2 --derinlik=1 --yaratik=cor,agac_iyesi
  --yaratik_cikti=C:/x` (`tools/tests/yaratik_galeri.gd`: AI kapalı, her poz `show_frame` ile, 1080p kırpım).
* **Çor Ruhu** (`cor`, hücre 80x76): küllü kefen, geriye sarkan sivri başlık, karanlıkta iki göz + kafatası dişleri,
  güve yeniği delikler, bileğe bağlı çalınmış dilek çaputları, kemik eller, zincirde kafes pencereli tunç buhurdan
  (salgın ateşi), sporlu duman telleri. Uyarı: buhurdan geriye/öne çekilir, ateş ve gözler parlar, kıvılcım; saldırı:
  spor bulutu patlaması. Çeşitlemeler: Kurgan Ruhu (`kara_kus_yavrusu`: aşı keçe, sivri Saka börkü, altın ölü maskesi),
  Kan Çoru (`kan_yarasasi`: kulaklı başlık, yarasa kanatları, kızıl), Ayaz Çoru (`kaf_kartali`: donmuş kefen, kartal
  tüyü yaka, buz sarkıtları), Kayıp Ruh (`kayip_ruh`: ağlayan soluk maske, saydamlaşan kuyruk, kırık pranga, ruh
  kafesi feneri), Demir Gaga (`demir_gaga`: kurum kefen, demir kuş gagası maske, kor dolu demir buhurdan).
* **Kara İye** (`agac_iyesi`, hücre 128x112): kök bacaklar (kök saçaklı ayak), kabuk olukları ve budak, kamburdan çıkan
  kırık dallar, sırta oturan yosun örtüsü + mantarlar, geyik kafatası, boynuzlarda dilek çaputları, mor yanan Erlik
  çatlakları ve öz. Uyarı: yumruk havada, çene açılır, çatlaklar/göz/yumruk alevlenir. Çeşitlemeler: Tozkoparan (ağarmış
  saksağul, kuru bozkır otu, koç boynuzu, toz hortumu teli), Su İyesi (ıslak kütük, su yosunu, midye, damlalar,
  camgöbeği), Dev Çocuğu (ayaz kayası, kar örtüsü, buz kristali boynuz/dikenler, ağır kaşlı dev başı ve buz dişler),
  Od İyesi (kömür kabuk, lav çatlakları, kül örtü, alev dilleri, kor uçlu dallar/boynuzlar).
* **Balbal** (`balbal`, hücre 88x80): yontu düzlemli granit, keski izleri, bozkır taşlarının turuncu likeni, börk,
  sarkık bıyık, kadeh, kemer plakaları, geniş taş kılıç; Orhun runaları (çizgi damgalar), göz yarıkları ve kılıç oluğu
  uyanınca camgöbeği yanar; uykuda sönük, kılıç kında. Uyarı: kılıç başın üstünde, runalar parlar, omuzdan taş tozu.
  Buz Balbalı: buzlu taş, bıyıktan/börkten/kollardan sarkıtlar, buz kılıç, ayaz mavisi runalar.
* **Kara Kam** (`arcura`, hücre 76x72): saçaklı deri kam postu (kızıl şeritler, demir çıngıraklar, göğüste kuzgu),
  baykuş tüyü yelpazesi + geyik boynuzlu taç, kemik maske ve gözün önüne sarkan saçak, boyalı tüngür (Hayat Ağacı, Ay,
  Güneş), lanet küresi (sarmal, uyarıda halka + kıvılcım). Çeşitlemeler: Kurgan Kamı (at kafatası maske, kartal tüyü,
  altın kuzgu, kehribar), Işıltı Kamı (gözleri bağlı kör kam, kristal taç, yeşil ışık), Erlik'in Kızı (kara uzun saç,
  solgun yüz, kara boynuzlar, dar belli yırtık kızıl elbise, davul yerine kemik dişli kara ayna, macenta).
* **Bilinen eksikler:** düşman sola dönünce çizili ışık yönü aynalanır (tüm v2 sprite'larda olduğu gibi); yaralanma
  karesi çoğunlukla geri çekilme + söndürülmüş göz (oyunda vuruş parlaması ile okunur); diğer biyomların v2 ortamı
  bu dalda yok (çekimler Ötüken'de 1:1).

### Stil v2 mürekkep arayüzü (HUD, menüler, hasar rakamları)

Yalnızca `--stil=v2`; v1 piksel arayüzü (`PixUI`, `pixel.fnt`) birebir aynı kalır. Yerleşim değişmedi: `PixUI`'nin her
yardımcısı (`text`, `width`, `panel`, `fancy_panel`, `bar`, `icon`, `key_cap`, `horn`, `divider`, `ongun_stripe`, `weapon`)
v2'de aynı imzayla `scripts/ui/InkUI.gd`'ye düşer; özel parçalar `scripts/ui/InkHUD.gd`'de (HUD.gd'de `if InkUI.on()` dalları).
* **Yazı tipleri** (`assets/ui/fonts/`, hepsi SIL OFL 1.1, kaynak ve lisanslar `LICENSE*.txt`): Alegreya Sans Medium/Bold
  (gövde, sayılar), Cinzel (değişken, wght 700: BÜYÜK HARF yazıt başlıkları; büyük harfli metin otomatik buna geçer),
  Kaushan Script (fırça: ekran başlıkları, kombo ve hasar rakamları, büyük adlar; büyük harf başlıklar Türkçe kurallarla
  "Kam Tılsımı" biçimine çevrilir: `InkUI.tr_title`), Alegreya (hikâye, Ozan, tören sözleri). Vektör yazı; Godot dinamik
  aşırı örneklemesi sayesinde 960x540 x2 (HUD) ve x3 (menü) ölçekte 1080p / 4K keskin. `★` Alegreya'da yok: `◆`.
* **Dokular** (`tools/artgen/ui_ink.py` -> `assets/ui/ink/`, kayıpsız + mipmap): kuru fırça çerçeve (`frame_ink` siyah,
  `frame_line` renkli ince çizgi), mürekkep yıkaması dolgu, yatay sürme (`swash`, alçak rozetler), fırça çubuk (`stroke`),
  kızıl mühür (`seal`, tuş rozetleri), ensō halka, sıçrantı, yıkama şeridi, koçboynuzu, 4 tamga, yanık kenarlı parşömen,
  fırça kenarlı vinyet ve 14 mürekkep simge (can, matara, sikke, Kut alevi, kurt, kartal, ayı, kafatası, kum saati, kılıç,
  üçgen muska, kam davulu, ruh, kalkan). 9 dilimde orta parçalar kırpılır (sıkıştırılmaz): küçük panelde çizgi bulanmaz.
* **Paneller:** yükseklik < 19 birim yatay sürme + renkli alt çizgi; < 44 satır (alt fırça çizgisi, uç tırnakları);
  büyükler siyah fırça çerçeve + renkli iç çizgi, kenarın üstünde (içerik alanını yemez). Süslü panel: üstte mürekkep
  lekesi üstünde koçboynuzu.
* **HUD:** sol üstte yıkama üstünde kızıl yürek + kızıl mürekkep can fırçası (gecikme izi kemik rengi), matara simgeleri,
  kızıl `Q` mührü, sikke / Kut / banka; ongunlar mürekkep simgeyle. Yuvalar v2 silah atlasından (`Data.weapon_sprite`)
  çizilir; Kut / kam / don halkaları ensō + fırça yayı (kurt, davul, ruh simgesi). Kombo sağda: mürekkep sıçrantısı
  üstünde fırça rakam, Cinzel rütbe adı. Boss çubuğu: yıkama şeridi, Cinzel ad, iki yanda tamga, uçlarda koçboynuzu.
* **Menüler:** başlık ekranı fırça "Kut'un Yolu" + kızıl alt çizgi + Kayı tamgalı mühür; hikâye ve Ozan parşömende koyu
  mürekkeple; Ad töreninde adın altında kızıl fırça ve mühür; ölümde kan kırmızısı sıçrantılar; karartmalara fırça vinyeti.
* **Dünya yazıları:** `FX.number` kalın fırça rakam, mürekkep dış çizgi + fırça gölgesi; kritik kızıl rakam, arkada
  mürekkep sıçrantısı ve eğik kızıl mühür. `FX.text` Alegreya Sans Bold / Cinzel. NPC adları PixUI üzerinden; Label'ların
  varsayılan yazısı ve düşman "!" uyarısı da v2'de fırça/gövde yazısına geçer (`InkUI.setup`).
* **Test:** `-- --stil=v2 --ekran=<ekran> --pencere=1920x1080 --goruntu=x.png --bekle=22` ve ek olarak
  `--arayuz=intro|ozan|done|ad|kombo|hasar|flash|ipucu|dusuk[,...]` (HUD.gd, 45 kare sonra uygulanır). Çekimler
  `rec_v16/ui/` (depo dışı).

### Stil v2 mürekkep yaratıkları, seti B: Gulyabani, Bekçi, Tosbağa, Bozkurt biçimi, yurt sakinleri

`tools/artgen/<kimlik>_ink.py` + `export_ink.py --surale|--bekci|--tosbaga|--bengu_kurt|--npc` (yalnızca `_v2` yazar;
v1 dosyaları değişmez). Animasyon adları, kare sayıları, fps/döngü, satır sırası v1 json'undan; çapalar aynı anlamla
('hand', 'head', 'mouth' dünya biriminde, ayak orijinli); çarpışma kodda değişmedi. Doku 4 piksel / dünya birimi,
`"filter": "linear"`, ışıyan parçalar `_e` sayfasında. Hücreler v1 dünya boyutundan biraz büyük olabilir (yalnızca
pay; orijin buna göre): surale 128x120, bekci 96x104, tosbaga 104x72, bengu_kurt 160x120, NPC 80x104.

* **Gulyabani** (`surale_ink.py`; Karakoncolos aynı çizim + soğuk ton): v1 iskelet ve pozları (`creatures.GUL_ANIMS`).
  Soğuk mavi-gri gergin deri, kaburga ve omur çıkıntıları, çökük karın, düğüm dizler, yere değen kollar ve sarı
  tırnaklı uzun parmaklar; toprak lekeli yırtık kefen başlık gibi kafayı örter, yüzün önüne yağlı saç tutamları
  düşer; oyuk göz çukurunda soluk sarı ışık (hazırlık ve yakalamada büyür), iğne dişli açılan çene.
* **Kurgan Bekçisi** (`bekci_ink.py`; 10 düşman bu çizimi `tint` ile kullanır): kurumuş kafatası yüz + soğuk Kut gözü,
  sivri dilimli tunç miğfer (burun siperi, yanak siperi, zincir ensel, kızıl at kılı sorguç), tunç lamel zırh, omuzluk,
  lamel etek parçaları, kızıl keçe kaftan, sargılı baldır + tunç baldır siperi, kemik parmaklarda dilimli tunç topuz;
  deri kaplı yuvarlak kalkan (perçinli tunç kasnak, sivri göbek, ışıyan Göktürk runa halkası). Pozlar yeniden
  kurgulandı (ayaklar yere çözülür): hazırlıkta topuz başın üstünden arkaya, gözler alevlenip iz bırakır; vuruşta
  hamle adımı; kalkan darbesi ve hücumda kalkan yarı dönük. Taban orta değerli ve az doygun: yeşil/mavi/kızıl/mor
  tonlar okunur (`rec_v16/yaratik_b/biyom_1e1.png`). Atlılar (al_atli, kara_atli, kurgan_atlisi) v1'deki gibi yaya;
  ad ve davranış "gul/akıncı" olduğundan ayrı binek çizimi yapılmadı.
* **Taş Tosbağa** (`tosbaga_ink.py`; Taş Gulü, Buz Tosbağası ton): yüksek kubbe; her biri ayrı yüzey gölgesi alan
  altıgen taş plakalar (sırt/yan/kenar sıraları, yosun, çatlak), sırtta ışıyan mağara kristalleri, kabuk kenarı
  altından çıkan kalın sütun bacaklar, kancalı gagalı iri baş. Isırık hazırlığında göz alevlenir. 'shell' kabuğa
  çekilmiş (ağızdan bakan göz), 'spin' kabuk yerde yuvarlanır (4 karede tam tur, ışık dünyada sabit).
* **Bozkurt biçimi** (`bengu_kurt_ink.py`): v1 iskelet (K 1.75, wolfkit eklemleri) ve pozları; kar beyazı post
  (mavi-mor gölge, kıl darbeleri, tutamlar), kafa tepesinden omuza Kut alevi yelesi (dış/orta/göbek üç kat tek
  kütle halinde, dış dilde ince mürekkep, kıvılcımlar; uluma ve ısırıkta uzar), kuyruk ucu ve bilek/topuk ruh
  alevleri, kalçada ve omuzda ışıyan altın tamga, boynu saran tunç halka + Kut taşı, rüzgârda turkuaz atkı.
* **Yurt sakinleri** (`npc_ink.py`, yüz sola): Umay Ana (ak entari + turkuaz/altın işlemeli keçe üstlük, gümüş
  örgüler, geyik boynuzlu altın taç, ak kayın asa ve dolaşan Kut zerreleri; konuşurken kutsama eli), Demirci Kam
  Kuzgun (kuzgun tüylü kam başlığı, örgülü kara sakal, sıvalı kızıl kaftan, deri önlük + muskalar, kerpeten; balyozun
  başı yerde, konuşurken kalkar, yüzünde kızgın runa), Ozan Bilge Kopuz (ak keçe börk, uzun ak sakal, işlemeli
  çapan, nazar boncuğu; kopuz kucakta, iki el IK ile sapa ve tellere oturur).
* **Test:** `-- --stil=v2 --yaratik[=tür,...] [--yaratik_kurt] [--yaratik_sure=7]` (`tools/tests/yaratik_testi.gd`:
  her tür oyuncunun önünde canlı yapay zekâyla, oyuncu ölümsüz, sonra iki vuruş; sonunda Bozkurt koşu/ısırık/sıçrayış/
  uluma; "[yaratik] ... kare=N" satırları). 1080p 1:1 kareler için `--pencere=1920x1080 --goruntu=x.png --seri=N
  --aralik=s` (film kaydı pencereyi 1280x720'de tutar). Çekimler `rec_v16/yaratik_b/` (depo dışı).

### Stil v2 mürekkep-cel bosslar (Kara Börü Han, Tepegöz, Şahmeran Ana, Yelbegen, Erlik Han)

Beş boss `--stil=v2`'de `<kimlik>_v2` sayfalarını kullanır (`Data.stil_id`); v1 dosyaları ve boss mantığı (Boss.gd) değişmedi.
Animasyon adları, kare sayıları, fps, döngü bayrakları ve çapa adları v1 json'undan; çarpışma kutuları aynı. Hepsi yordamsal.

* **Üretim:** `cd tools/artgen && python export_boss_ink.py [kimlik ...] [--anim ad ...] [--is N]` (paralel; boss başına
  ~1-2 dk). Ortak takım `bosskit.py` (profil uzuv/kas, sap kavrayan el, açık pençe, alev dili, ışıyan çatlak, yırtık kenar,
  anahtar kare yardımcıları, `BossCanvas`: ışımasız opak parça altındaki ışımayı siler, arkada kalan kor/kristal önündeki
  kolun üstünden parlamaz). Önizleme `export_boss_ink.py --onizleme out.png <kimlik> anim:kare ...`, kontak sayfası
  `sheet_boss_ink.py`, kenar kırpma denetimi `check_boss_ink.py`, hızlı kutu `bbox_boss_ink.py`.
* **Yoğunluk/ölçü:** doku 4 piksel / dünya birimi (2,0 kamerada 1080p'de 1:1; boss kamerası genelde 1,6-2,0 arasında kalır).
  Hücre yüksekliği v1 ile aynı dünya boyunda (CameraV2 boss boyunu hücreden okur), genişlik saldırı menziline göre büyüdü:
  Tepegöz / Erlik 256x200, Yelbegen 256x208, Şahmeran 256x176, Kara Börü Han 224x144 (dünya). Ayak noktası json "origin".
* **Sayfa düzeni:** 8 kare x 1024 px bir sıraya sığmadığı için animasyon başına düzen: json anim `page`, `row` (sayfadaki
  ilk satır), `cols` (kareler bu sütun sayısında alt satıra sarar). `SpriteAnim._apply` bu alanlar varsa onları kullanır
  (yoksa eski satır/sayfa düzeni, bütün diğer sprite'lar aynen). Sütun sayısı toplam alan + sayfa sayısını en küçük yapar;
  sayfalar en çok 4096x4096, BPTC + mipmap.
* **Işıma:** `_e` sayfaları yarım çözünürlükte (json `"glow_scale": 2`; SpriteAnim ışıma sprite'ını 2x ölçekler, bölgeyi
  yarıya böler). VRAM (BPTC 1 bayt/px + mip, ışıma dahil): Kara Börü Han ~22 MB, Tepegöz ~55, Şahmeran ~48, Yelbegen ~57,
  Erlik Han ~55 (beşi ~236 MB). Boss sahneden çıkınca `Data.forget_sprite` sayfaları önbellekten bırakır (Boss._exit_tree;
  yalnızca doğrusal süzgeçli v2 sprite'larda): koşu boyunca bosslar birikmez, aynı anda en çok bir boss yüklü.
* **Tasarımlar:**
  * *Kara Börü Han* (`kara_boru_han_ink.py`): Erlik Tazısı iskeleti ve v1 pozları (KBH_ANIMS), tazı birimiyle 2,3 kat
  (k = 9,2); daha ağır kütle, sırtta öfkede uzayan mor-kızıl bozgun kristalleri, böğürde kristal damarları, perçinli kemik
  omuzluk, kemik maske + kemik dişli demir han tacı, kan koru gözler, hep görünen azılar, dikenli pranga + kırık zincir;
  ulumada baş boyun kökü etrafında göğe döner.
  * *Tepegöz* (`tepegoz_ink.py`): kambur dev, 3/4 önden göğüs; iri kehribar tek göz (damarlı akı, dikey bebek), ağır kaş,
  azılar, sırtta kırık Oğuz okları, dikişli kılıç izleri, kemik/kafatası kolye, koyun postu etek, deri dolak, peri yüzüğü
  (ışır), pranga; demir çemberli çivili meşe gürz. Hazırlık: gürzü yana-geriye çeker (yüz açıkta), atılış dört kare yay.
  Büyüde kaya kaldırır (çatlakları yanar).
  * *Şahmeran Ana* (`sahmeran_ink.py`): yerde iki katlı kangal + kuyruk ucunda yılan başı (halk resmi), bele S kıvrımı;
  zümrüt pul + baklava deseni, krem karın pulları hep alta/öne bakar; taçlı kraliçe (zümrüt yılan gözleri, sürme, altın
  pullu göğüslük, kolye, kolluk), saç yılanları, boynunda yılan, açılan kobra yelpazesi; büyüde zehir küresi örer.
  * *Yelbegen* (`yelbegen_ink.py`): Tepegöz iskeleti/zamanlaması; ayaz mavisi deri ve kırağı desenleri, üç ayrı boyunlu baş
  (arkadaki geriye bakar, öndeki hırlar), buz kristali taçlar, sırtta/omuzda/ön kolda buz kristalleri, ak post pelerin ve
  yaka, kemik saplı buz uçlu mızrak; büyüde elinde kristal demeti büyütür.
  * *Erlik Han* (`erlik_ink.py`): iri lir biçimli boğa boynuzları, kara sakal (demir halkalı) ve kulağa kıvrık bıyık, kor
  gözler, demir taç, omuzlardan yükselen tamu alev yelesi, lamel zırh + boğa kafatası amblemi (çatlaklarından ocak yanar),
  boynuz çıkıntılı omuzluklar, kor kenarlı yırtık pelerin, tamga işlemeli kaftan paneli, kanatlı topuz (kor çatlaklı);
  büyüde ateş küresi.
* **Telgraf pozları:** `windup` son karesi tutulur: silah geride (yüz ve göz görünür), uzak el önde, göz/alev parıltısı en
  yüksek. `cast` 0. kare = salış (mermi bu karede çıkar), 2. kare = yükleniş (tutulur). `rage` baş yukarı, kükreme.
* **Kayıtlar:** `rec_v16/boss/` (depo dışı): kontak sayfaları, önizlemeler, oyun içi 1080p kareler.

### Yaygınlaştırma planı (onay sonrası)

1. **Ortak altyapı:** `style_v2` malzeme kütüphanesi (`materials_v2`: kumaş/deri/metal/post/kemik/taş rampaları) ve poz yardımcıları;
   v2 kol iskeleti tüm silahlı animasyonlarda gözden geçirilir (`--savurus` laboratuvarında 20 savuruş).
2. **Bengü tamamı:** zıplama, düşme, yuvarlanma, çömelme, yay, fırlatma, kalkan ve 13 arketip gövdesi v2 oranlarına göre yeniden
   kurgulanır (şu an v1 pozlarıyla çiziliyor); Bozkurt biçimi (`bengu_kurt`) ve ruh kurdu aynı ışık/kenar kuralıyla.
3. **Yaratıklar** (creatures*.py, wolfkit): önce sık görülenler (kara_boru, cor, balbal, agac_iyesi), sonra seçkinler ve bosslar
   (kara_boru_han, erlik_han). Her biri `_v2` adıyla; kimlik başına bir oturum.
4. **Biyomlar:** her biyom için toprak üreticisi (`otuken_v2.soil_texture_v2` parametreli hale getirilir: katman dizisi, kaya
   rampaları, kök/kristal/lav ekleri), atlas paleti ve 5-6 paralaks katmanının tamamı; sırayla bozkir, sahmeran, kaf, tamu, yurt.
5. **Süsler, silahlar, efektler:** decor (dilek ağacı, çıra, kaya...), 48 silah atlası (metal türü özellikle kazanır), vuruş efektleri.
6. **HD paketleri:** v2 Bengü zaten 1080p'de 1:1; 4K için `export_hd.py` v2 dosyalarını da üretir (manifest'e `_v2` girişleri).
7. **Geçiş:** her şey v2'de bitince `--stil` varsayılanı v2 olur (Ayarlar'da "Görsel stil" seçeneği), v1 dosyaları bir sürüm daha
   kalır, sonra `eski-tasarim-v16` etiketiyle arşivlenip silinir.


## Varsayılan görsel stil: v2 (mürekkep)

Oyun artık varsayılan olarak v2 mürekkep + cel tarzında açılır (`Data.stil = "v2"`). Eski piksel görünüm: `-- --stil=v1`.


## Okçuluk (v19): Dead Cells esinli yay sistemi

Şikâyet: yay "hantal" (0,55 sn sabit gerilme + 1/aps bekleme = Türk Yayı'nda atış başına ~1,4 sn; gerilirken saldırı
basışı düşüyordu; oklar 300-560 px/sn ile süzülüyordu) ve v2'de hâlâ piksel görünüyordu (1 px `draw_rect` kiriş, kare
ok, `FX.burst` parıltıları). Yeni sistem `scripts/actors/Okculuk.gd` (durum + kurallar) ve `scripts/actors/Ok.gd`
(oyuncu oku, `Projectile`'dan türer); `Player.gd` yalnızca girdi noktalarından çağırır.

### Dead Cells'ten alınanlar

* **Dokunuş = ok.** Hızlı yaylarda (Quick Bow) gerilme ~0,1 sn; basıp hemen bırakmak da atar. Bizde her yayın en kısa
  gerilmesi (`min`) dolunca ok çıkar: seri basış seri atış, hiçbir basış kaybolmaz (bekleme sırasındaki basış 0,45 sn saklanır).
* **Basılı tut = seri atış** (Quick Bow / Sonic Carbine): Akıncı Yayı basılı tutuldukça kendiliğinden yineler.
* **Gerilen yaylar** (Marksman's Bow, Heavy Crossbow) dolup bırakılmayı bekler; tam gerilme yaya göre 0,3-0,5 sn.
* **Neredeyse anında oklar:** 650-1100 px/sn; yalnızca yarım gerilmiş ya da ağır oklar hafifçe düşer. 150 px'teki
  düşmana ok 7-9 karede (117-150 ms) varır. Hızlı ok ince düşmanın içinden geçmesin diye kare içinde 6 px'lik alt adımlarla süpürülür.
* **Dikey hedef yardımı:** öndeki en yakın düşmana kendiliğinden nişan; koni uzakta ±26°, dipte ±63° (alçak kurt dibinde de
  vurulur); nişan noktası gövde kutusunun okun yüksekliğine en yakın yeri; yerçekimi düşüşü kadar yukarı. Kol, yay ve
  yaydaki ok bu açıya eğilir (v2). Önde kimse yok, arkada biri varsa (yön tuşu basılı değilken) ona dönülür.
* **Hareket:** gerilirken yürünür (yaya göre %40-85 hız; eski: %30), havada atılır, yuvarlanma gerilmeyi keser.
* **Kritik koşulları** (Nerves of Steel, Multiple-nocks, Heavy Crossbow): tam zamanlama, dipten atış, geri çekilme.

### Yaylar (`Okculuk.PROF`, süreler sn)

| Yay | Esin | Gerilme (tam / en kısa) | Atış sonrası kilit | Hız px/sn | Yürüme | Kendine özgü |
|---|---|---|---|---|---|---|
| Türk Yayı | Marksman's Bow + Nerves of Steel | 0,40 / 0,06 | 0,14 | 640 → 1100, tamda düz | %60 | Tam gerilince {v} düşman deler; **tam bırakış kesin kritik** (eskiden her tam gerilme kritikti) |
| Akıncı Yayı | Quick Bow | 0,12 / 0,05 | 0,08 | 980-1050, düz | %85 | Basılı tut: ~5 ok/sn seri atış; 10 Hz basışta 10/12; yuvarlanırken atar; geri çekilirken kritik (part atışı) |
| Sağanak Yayı | Multiple-nocks Bow | 0,30 / 0,08 | 0,20 | 720 → 960 | %60 | 3-4 ok yelpaze; **gerildikçe yelpaze daralır** (±19° → ±7°); 80 px içinde "dipten!" kesin kritik |
| Od Okları | (Ice/Fire Bow) | 0,32 / 0,08 | 0,18 | 700 → 940 | %65 | Çarptığı yerde alev; yanan düşmana kritik; tam bırakış |
| Tufan Yayı | Heavy Crossbow | 0,50 / 0,13 | 0,32 | 680 → 900, hafif düşer | %40 | 5-6 ok geniş saçma (±24° → ±11°), 120-200 itme + sendeletme, 65-130 px/sn geri tepme, 90 px içinde dipten kritik |

Ölçülen (`--yay --boss`): basış→ok Türk 100 ms, Akıncı 67 ms, Sağanak / Od 117 ms, Tufan 167 ms; basış→tam gerilme
417 / 317 / 350 / 517 ms. Hasar çarpanı en kısa ↔ tam arasında doğrusal (Türk 0,45 → 1,0; yelpaze okları ×0,85).

### Yeni mekanikler

* **Tam Bırakış:** gerilen yaylarda yay dolduğu an 0,1-0,11 sn'lik pencere açılır. Pencereden 0,18 sn önce ok ucunda
  daralan altın halka belirir; dolunca dört kollu parıltı + mürekkep pırıltısı + `yay_dolu` sesi + gövde flaşı. Pencerede
  bırakılan ok: kesin kritik, +1 delme, %10 hızlı, altın mürekkep iz; 35 ms duraklama, kamera itişi, altın ensō, "TAM BIRAKIŞ".
  Geç bırakış tam güçte ama kritik değil (oyuncu ritim tutturmayı öğrenir: Nerves of Steel).
* **Ok Sökme (ok + yakın dövüş sinerjisi):** isabet eden son ok düşmanın gövdesinde saplı kalır (en çok 5, 6 sn). Saplı oku
  olan düşmana yakın dövüş vuruşu okları söker: ok başına +%30 hasar, ok sayısı kadar kanama, 3+ okta kesin kritik; sökülen
  oklar dönerek geri fırlar, kızıl mürekkep damlaları + pençe izi, "OK SÖKÜLDÜ ×n", yay beklemesi sıfırlanır ve bir hazır ok
  kazanılır. Akış: uzaktan 2-3 ok → dalış → sökme vuruşu → hazır okla anında tam bırakış.
* **Ok Toplama:** ıskalanan oklar duvara / zemine saplanır, 6 sn nabız atarak kalır; ölen düşmandaki saplı oklar (en çok 3)
  yere dökülür. Üstünden geçince (yuvarlanırken de) toplanır: **hazır ok** (en çok 3, baş üstünde küçük mürekkep oklar).
  Hazır okla başlayan gerilme anında dolu ve tam bırakış sayılır (Akıncı'da sıradaki ok kesin kritik + delici).
* **Kartal Süzülüşü:** havada gerilirken düşüş 50 px/sn'ye iner (hava başına 0,55 sn); havadaki ilk atış küçük bir sıçrama
  (-70 px/sn) verir. Ölçülen: serbest düşüş 208 px/sn, gerilirken en çok 69 px/sn.

### Akış (FLOW ile)

* Saldırının vuruş anında yay basışı: toparlanma başlar başlamaz saldırıyı keser, ok çıkar (167 ms). Basış ağır savuruşta da
  kaybolmaz (`Okculuk.process` ara belleği tazeler).
* Gerilirken saldırı basışı: en kısa gerilme dolduysa ok o anda çıkar (**çabuk atış**), saldırı aynı karede başlar (eskiden
  basış yay bırakılana dek bekleyip eriyordu).
* Gerilirken yuvarlanma: aynı karede yuvarlanır, gerilme bırakılır. Yuvarlanırken basılan yay: yuvarlanma biter bitmez ok (267 ms).
* Atış sonrası kilit 0,08-0,32 sn (eskiden 1/aps = 0,6-1,1 sn); kilit sırasındaki basış saklanır.

### Görünüş (stil v2; v1 piksel görünüm `--stil=v1` ile aynen)

* **Kiriş:** kenar yumuşatmalı `draw_polyline`, koyu mürekkep dış çizgi (0,95 birim) + açık çekirdek (0,38); tam bırakış
  penceresinde altına döner. Yaydaki ok uçuştaki okla aynı SusV2 mürekkep sprite'ı (`ok_<tür>`), kuyruğu gezde, eğimle döner.
* **Uçuş izi:** `shaders/ok_iz.gdshader` — ucu dolgun, kuyruğa incelen fırça şeridi; koyu mürekkep kenar, oka özgü çekirdek
  (Türk krem, Akıncı kızıl, Sağanak / Tufan buz mavisi, Od turuncu, tam bırakış altın; başta HDR parıltı), kuyrukta `bristle.png`
  kıllarına ayrılarak erir. Kenarlar türevle yumuşatılır.
* **Namlu / isabet / duvar:** atış yönünde kısa mürekkep kesiği + yönlü sıçrantı (`InkFX` "cut_b" + "burst_dir"); isabette
  `InkFX.hit("pierce")` (kritikte kademe 2), duvarda soluk kuru fırça tozu; saplı oklar düşmanın çocuğu olarak gövdede kalır.
* Tam gerilme parıltısı: `InkFX` "shard" + kuru halka (eski `FX.burst` piksel kareleri kalktı); tam bırakış altın ensō.

### Test

`godot --headless --path . --quit-after 99999 -- --yay --boss [--stil=v1]`: her yay için dokunuş→atış→isabet, tam bırakış /
geç bırakış, basılı tutma, 10 Hz seri basış; akış (vuruşta yay, gerilirken saldırı / yuvarlanma, yuvarlanırken yay, Akıncı
yuvarlanma atışı), ok sökme + hazır ok, ok toplama (dökülen / yere saplanan), süzülüş, takılma denetimi. Ekran görüntüleri:
`godot --path . -- --yay --boss --pencere=1920x1080 --yay_goruntu=C:/mutlak/klasor`.

Oyun artık varsayılan olarak v2 mürekkep + cel tarzında açılır (`Data.stil = "v2"`). Eski piksel görünüm: `-- --stil=v1`.


## Dövüş v19: silah kimlikleri, Kut Yankısı, Çarpışma, Karşı Vuruş, Kut Alma, duruş kırılması

Geri bildirim: "silah, kombo, yay-ok mekanikleri çok daha iyi olmalı; başka mekanikler de ekleyelim." v18 temposu Dead Cells
ölçeğine indirilmişti (ölçüm aşağıda); v19 her silahı kendine özgü bir "karakter" olarak bitirir ve ritmi ödüllendiren yeni
mekanikler ekler. Yay / mermi tarafı ayrı daldadır (bu bölüm yalnızca yakın dövüş).

### Araştırma: Dead Cells yakın silah kritik koşulları (deadcells.wiki.gg, Melee Weapons)

Her silahın tek ve okunur bir kritik koşulu var; silahın nasıl oynandığını o belirler: Balanced Blade art arda 10 isabette kritik
(kombo rampası), Assassin's Dagger arkadan, Spite Sword son 8 sn'de hasar aldıysan, Broadsword zincirin 2. ve 3. vuruşu
(bitiriş kritiği), War Spear aynı anda birden çok hedefe, Impaler duvara dayalı hedefe, Flawless 15 sn hasar almadıysan, Rapier
yuvarlanma ya da savuşturmadan hemen sonra, Symmetrical Lance hızlı iki öldürmeden sonra 6 sn, Frantic Sword canın %50 altındayken,
Flint basılı tutup bırakınca, Nutcracker sersemlemiş / donmuş / köklenmiş hedefe, Sadist's Stiletto kanayan / zehirli hedefe.
Kaynak: https://deadcells.wiki.gg/wiki/Melee_Weapons . Bizim 27 silahımızın her birinin zaten kendi kritik koşulu vardı (`mech`);
v19 bunları zincir biçimiyle hizaladı, tekrar eden zincirleri ayırdı ve Broadsword tarzı "bitiriş kritiği"ni (`fc`) ağır
silahlara verdi.

### Silah kimlikleri (`Player.COMBOS`)

v19 değişiklikleri: **Gürz** üçlü oldu (kısa baş üstü ezme → yel değirmeni → sıçrayıp çakma; Nutcracker gibi), **Kor Çekici**
yerde sürüklenen çekiçle kor saçarak alttan kalkar (yakar, hafif kaldırır; daha önce hiçbir silahın kullanmadığı `ground_drag`)
→ baş üstü iniş, **Ruh Kılıcı** palayla aynı açılmasın diye düz → iniş → yükseliş, **Yıldırım Kılıcı** bekleme bitirişi Şimşek
Çekişi (kesin kritik, ileri atılır; eskiden yedi silahla aynı "seri saplama"ydı). Bitiriş kritiği (`fc`, zincirin son vuruşu
kesin kritik): Ulu Kılıç, Gürz, Kor Çekici, Teber. Her zincir bitirişi (`last`) ayrı bir olay: büyük mürekkep sıçrantısı + silah
paletinde halka + kısa yakınlaşma + 20 ms ek duraklama (`_finisher_fx`, `V19.fin_hs`).

Zamanlar `--dovus --boss` ölçümü (60 Hz, ±1-2 kare; "temas" = isabetin başladığı kare; zincir aralığı = 20 Hz seri basışta ardışık
temaslar, düşmansız).

| Silah | Zincir (uzunluk: biçimler) | Kritik koşulu | Basış→temas / zincir aralığı (ms) |
|---|---|---|---|
| İkiz Bıçak | 4: sol kesik → sağ kesik → tırmık → çapraz içinden geçiş | yuvarlanmadan sonraki N vuruş | 100 / 100-183 |
| Böri Hançeri | 4: sol → sağ → ters el → çapraz geçiş (arkaya düşer) | arkadan, sersem, kalkansız | 83 / 100-117 |
| Kurt Pençeleri | 3: tırmık → ters el → yükseliş (fırlatır) | havadaki düşman; havada sıçrar | 67 / 117-183 |
| Ay Palası | 5: çevrim → sağ → sol → geri sıçrayış → çift saplama | 5. vuruş; zincir hızlanır | 67 / 83-200 |
| Yatağan | 4: ters el → düz → geri sıçrayış (kesin kritik) → hücum | ivme 5 yükte | 100 / 150-183 |
| Rüzgâr Kılıcı | 3: çekiş → geri sıçrayış → yükseliş | havadaki düşman; 3. kesik yel bıçağı | 117 / 167-217 |
| Alp Kılıcı | 3: çapraz iniş → çapraz yükseliş → adımlı baş üstü | 3. vuruş | 133 / 183-233 |
| Pala | 3: çapraz iniş → ters el → çark (basılı: 1,2 sn) | kanayan düşman | 133 / 200 (+çark) |
| Ruh Kılıcı | 3: düz → iniş → yükseliş (her kesik ruh hilali) | uzaktan (hilal) | 117 / 167-217 |
| Yılan Kılıcı | 3: ters el → saplama → alçak süpürme (çelme) | 3 zehir yükünde | 117 / 167-217 |
| Ayaz Kılıcı | 2: alçak süpürme → adımlı iniş | donmuş düşman | 117 / 217-233 |
| Yıldırım Kılıcı | 3: çekiş → geri sıçrayış → hücum; bekleme Şimşek Çekişi | şimşek hamlesinde 2. delişten | 133 / 200-283 |
| Kargı | 3: saplama → alçak saplama → alttan süpürme | koşarak hücum | 133 / 167-200 |
| Tulpar Mızrağı | 3: saplama → saplama → uzun hamle (ileri taşır) | koşarken her saplama | 150 / 183-250 |
| Kement | 2: şaklama → yan şaklama | uçtan; çekilmiş düşman | 167 / 250-267 |
| Od Kamçısı | 3: şaklama → alçak süpürme → şaklama | yanan düşman; uçtan | 167 / 200-250 |
| Teber | 3: sırık süpürmesi → alçak biçme → baş üstü (`fc`) | uçtan (geniş yay) | 183 / 250-317 |
| Erlik Tırpanı | 3: biçme (çeker) → alçak süpürme → çark | canı %30 altı | 217 / 267-500 |
| Ulu Kayın Asası | 3: sırık süpürmesi → çevrim → aparkat | sersemlemiş; duvara çarptırır | 183 / 233-483 |
| Gürz | 3: ezme → yel değirmeni → çakma (`fc`) | sersemlemiş | 250 / 367-467 |
| Çivili Topuz | 3: iniş → aparkat (fırlatır) → çakma | 3 zırh kırığında | 283 / 383-533 |
| Savaş Baltası | 2: kanca (çeker) → fırlat | geri dönen balta | 250 / 400 |
| İkiz Balta | 3: sol → sağ (çift) → çark | kanama 3+ | 250 / 333-583 |
| Ulu Kılıç | 2: baş üstü → çark (`fc`), süper zırh | iki düşmana denk gelirse | 400 / 517-850 |
| Bozgun Kılıcı | 3: çapraz → çark (sa) → adımlı iniş (sa) | canı %35 altı | 350 / 400-817 |
| Dağ Çekici | 2: baş üstü (şok, sa) → aparkat | havadaki düşman (yere çakar) | 367 / 517-567 |
| Kor Çekici | 2: yerde sürükle (kor) → baş üstü (`fc`, kor gölü) | yanan düşman | 350 / 533-567 |

(Pala'nın 3. aralığı seri basışta çark tutuşuna denk gelirse 1,2 sn'ye uzar; v18'de de koşudan koşuya 383-1667 ms oynuyordu.)

### Yeni mekanikler (`Player.V19`, Player.gd "v19 dövüş mekanikleri" bölümü)

* **Kut Yankısı** (saldırı tuşu, zamanlama): savuruş bir düşmana oturduğu anda elde küçük altın halka belirir. O an (vuruş
  donmasının içinde ya da donma bittikten sonraki 150 ms içinde) yeniden basarsan sıradaki vuruş **yankılı** olur: hazırlığı
  ve tutuşu %55'e iner (zincir akar), hasarı ×1,3 ve 70 ms sonra savuruşun kendi yayı altın mürekkeple yeniden süpürülür
  (`_yk_echo_trail`: kolun vuruş penceresindeki pozlarından ayrı bir InkTrail), kutudaki herkese vuruşun %35'i kadar vurur.
  İsabetten ÖNCE basmak (hazırlıkta / süpürmede tuşa ezbere basmak) o savuruşun yankısını bozar; geç basış sıradan zincirdir.
  Art arda üç yankı: **Kut Mührü** (sıradaki isabet kesin kritik + altın damga). Usul vuruşuna da denk gelirse iki yankı kesiği
  ("YANKI ×2"). Usul müziğin ritmini, Yankı kendi vuruşunun ritmini ödüllendirir; ikisi birlikte en güçlüsü.
* **Çarpışma** (yakın savuşturma; kalkan gerekmez): savuruş vuruşa başladıktan sonraki 160 ms içinde (bıçak önünde dönerken)
  gelen yakın darbe ya da mermi, bıçağın kutusuna değiyorsa bıçağa çarpar: hasar yok, ÇARPIŞMA + altın ensō, örs sesi, 80 ms
  duraklama + kısa ağır çekim, Kut +8. Saldıran 0,8 sn sersemler (ağır 0,45) ve geri itilir; mermi ×1,2 hasarla seker. Sonraki
  savuruşun ilk isabeti kesin kritik ("karşılık!", 1,2 sn). Bossların yakın darbeleri karşılanmaz (mermileri karşılanır).
  Kalkan savuşturması (`_parry`) aynen sürer.
* **Karşı Vuruş**: saldırı hazırlığındaki ("!" uyarısı yanıp sönen) düşmana isabet hazırlığı keser (ağır yaratıkta bile;
  sersemletir 0,5 / 0,35 sn), kesin kritik, kızıl ensō + "KARŞI VURUŞ". Aynı hazırlıkta bir kez. Bosslarda yalnız kritik.
* **Kut Alma** (infaz): duruşu kırılmış, sersemlemiş, donmuş ya da kalkanı düşmüş ve canı %30'un altında (seçkinde %18) yaratığın
  başında nabız gibi atan kızıl mühür belirir (elmas + dört köşeli ayraç; `StatusOverlay._exec_mark`). Erim + 20 px içindeyken
  saldırı tuşu (yön tuşu ters değilse) infaza döner: kısa ağır çekim, dokunulmazlık, silah sınıfına göre bitiriş (kılıç çekiş
  kesiği, hançer içinden geçiş, mızrak deliş, uzun sap biçme, kırbaç şaklaması, ağır silah baş üstü ezme; `EXEC_SW`), hedefe
  atılış ve kesin isabet; siper / kalkan / kabuk aşılır, ölüm kesin. Ödül: canın %4'ü, Kut +12, mürekkep damgası + darbe karesi,
  "KUT ALINDI".
* **İsabet iptali**: vuruş oturduktan 50 ms sonra kilidin kalanı zıplama ve ikincil (yay, fırlatma, büyü, kalkan) ile kesilir:
  Göğe Savur / aparkat → zıpla → hava kombosu kesintisiz akar (eskiden vuruş anındaki zıplama toparlanmayı beklerdi).

### Duruş (`Enemy.POISE`) v19

Diretme 0,75 → 0,6 sn, hafif sarsılma 0,12 → 0,1 sn, büyük 0,2 → 0,24 sn (bitiriş daha belirgin iter). **Duruş kırılması**
(`Enemy._guard_break`): hafif yaratık zincirle diretmeye girdikten sonra gelen büyük vuruş (bitiriş, kritik, ağır, karşı vuruş)
duruşu kırar; ağır yaratık sarsılmasa da her yakın vuruşun duruş hasarını biriktirir (hançer ~1,2 · kılıç ~1,7 · dev silah 2,5;
bitiriş +1; ok / patlama 0,6; kor gölü 0) ve 7 puanda (seçkinde 11) kırılır, sn'de 2 puan söner. Kırılınca "DURUŞ KIRILDI",
0,9 sn sersemleme (ağırda 0,7), bu sürede ×1,25 hasar, 2,2 sn bekleme. Döngü: zincir → diretme → bitiriş kırar → canı azsa
Kut Alma. Ağır silahlar ağır yaratıkları çok daha çabuk kırar. Boss kuralı değişmedi.

### Kontroller (ek)

| Eylem | Nasıl |
|---|---|
| Kut Yankısı | isabet anında (altın halka) saldırıya yeniden bas; erken basma |
| Çarpışma | düşmanın darbesine / merminin önüne doğru savur (vuruşun ilk 160 ms'i) |
| Karşı Vuruş | "!" uyarısındaki düşmana vur |
| Kut Alma | kızıl mühürlü düşmana yakınken saldırı |
| İsabet iptali | isabetten sonra zıpla / ikincil |

### Test

`-- --dovus --boss` (tools/tests/dovus_testi.gd): tempo bölümü artık 27 yakın silahın hepsini ölçer; yeni "v19" bölümü: yankı
(isabetten 1 kare sonra bas → yankılı; hazırlıkta erken basış → yok; 300 ms geç → yok), üç silahta yankı serisi ve Kut Mührü,
çarpışma (hasar yok, düşman 0,8 sn sersem, karşılık 1,2 sn; toparlanmada gelen darbe hasar verir), karşı vuruş, altı silah
sınıfında infaz (50-383 ms'de öldü), duruş kırılması (ikiz bıçak → tazı 0,57 sn, Alp → tazı 1,57 sn, Dağ Çekici → Kara İye
1,72 sn), isabet iptali (isabetten 4 kare sonra zıplama 1 kare). `--v19` yalnızca bu bölümü koşar. TAKILMA=0.
`-- --dovus --boss --klip19 --pencere=1920x1080 --anlik=<klasör>` (headless değil) yeni hamlelerin gösterisini oynatır ve anlık
görüntüler kaydeder (`--yanki_kare`: yankı kesiğini kare kare).

### v2'de piksel kalıntılarının temizlenmesi (piksel denetimi)

Şikâyet: "oyunda hâlâ piksel gibi görünen efektler var". v2'de piksel görünen her şey bir denetim aracıyla listelendi ve
mürekkep karşılığına çevrildi; v1 (`--stil=v1`) çizimleri ve dokuları olduğu gibi duruyor.

**Denetim aracı** `tools/tests/piksel_tara.gd` (`-- --piksel_tara[=C:/abs/rapor.txt]`, başka test bayraklarıyla birleşir:
`--otomatik --derinlik=N`, `--boss=...`, `--yurt --yurt-tur`, `--sahne`, `--ekran=...`). Sahne ağacını 0,2 sn'de bir tarar:
- `suzgec`: doku çizen düğümün etkin süzgeci en yakın komşu (üst düğümlere, sonra görüntü alanı varsayılanına çıkılarak bulunur)
- `v1_doku`: doku yolu v1 piksel / Kenney varlığı (`_v2`, `/ink/`, `/fonts/`, `assets/fx/ink_p/` dışındaki her şey), 16 px'ten
  küçük çalışma zamanı dokusu, `toon_light` (piksel bantlı ışık) malzemesi
- `kare`: dokusuz `CPUParticles2D`; `yazi`: piksel yazı tipi; `cizim`: v1'de piksel bloklarıyla çizen sınıfların (`ExplosionFX`,
  `LightningFX`, `ThunderFX`, `StreakFX`, `GroundShadow`, `StatusOverlay`, `Corpse`, `KutGate`, `Totem`, `FirePool`...) v2'de
  `ink` kipi kapalı örneği
- `iz`: `PikselIz.iz()` kaydı. v2'de v1 yoluna girilince yazılır: `Data.stil_id` geri dönüşü (kimlik zaten `_v2` ise sayılmaz),
  `PixUI.icon` piksel simge, `PixUI.weapon` v1 silah simgesi. Denetim kapalıyken tek bool sınaması.

İlk tarama (15 senaryo): 49 ayrı gerçek bulgu (22 `cizim`, 11 `suzgec`, 16 `v1_doku`); ayrıca 66 `iz` kaydı vardı ama hepsi
yanlış alarmdı (zaten `_v2` olan paralaks adlarının yeniden yoklanması, kendi çizimi olmayan düşman çeşitlemesinin v2 taban
sprite'ına düşmesi) ve yoklama düzeltildi.
Son tarama (24 senaryo, boss ve arayüz ekranları dahil): **0**.

**Süzgeç:** proje varsayılanı en yakın komşu (v1 için). v2'de `Data._ready` kök görüntü alanının
`canvas_item_default_texture_filter` değerini doğrusal + mipmap yapar; süzgeci açıkça verilmemiş her düğüm (parçacık, etiket,
CanvasLayer altı) yumuşak çizilir. `Data.canvas_tex` v2'de doğrusal + mipmap. v1 değişmez.

**Mürekkep parçacık dokuları** `assets/fx/ink_p/` (`tools/artgen/ink_parcacik.py`, 21 doku, beyaz tonlu RGB = ıslak kenarda
koyulaşan mürekkep tonu, A = biçim; doğrusal + mipmap): `nokta` (soft_dot), `kivilcim` (k_spark, y ekseni hız yönünde),
`yildiz`/`yildiz2` (k_star/k_star2), `duman_0/1` (k_smoke), `alev` (k_flame), `halka` (k_ring), `kul` (kül pulu), `damla`,
`leke_0..2`, `cizgi` (incelen fırça darbesi), `serit` (şerit fırça), `kan_0..2` / `catlak_0..1` (yer çıkartmaları), `yaprak`.
`InkDraw.particle(v1_ad)` doku boyunu `set_size_override` ile v1 dokusunun görünen boyuna eşitler: parçacıkların
`scale_amount` değerleri aynı kalır. `FX.tex()` / `FX.dot_tex()` v2'de bunları döndürür.

**`InkDraw`** (`scripts/core/InkDraw.gd`): draw_rect / tarama satırı disklerinin dünya karşılıkları: `blot` (dolu leke), `soft`
(hale), `cloud` (yıkama), `ellipse`, `ring` (fırça halka), `stroke` (a -> b incelen darbe), `line` (çoklu nokta şerit fırça),
`flake`, `drop`, `star`, `flame`. Hepsi döndürülmüş dokulu dörtgen (`draw_primitive`), kenar yumuşatmalı.

**Çevrilenler (v2):**
- `ExplosionFX`: aynı evreler; ateş topu dış bantları yıkama bulutu, sıcak bant leke, çekirdek hale; duman koyu yıkama (erime
  yerine dağılıp solar); yer dalgası fırça halkası; parçalar kül pulu, korlar parlayan damla; flaş hale + fırça ışınları.
- `LightningFX`: kanal ve dallar piksel kümesine dökülmez, üç katman şerit fırça (yıkama, renkli fırça, beyaz kılcal çekirdek).
- `ThunderFX`: ön kıvılcım ve ışınlar fırça, çarpma flaşı hale, kavrulma izi yanık leke + kül pulları.
- `StreakFX`: kuru fırça darbesi. `GroundShadow`: iki tonlu yumuşak mürekkep elipsi (kesirli boy ve konum).
- `StatusOverlay`: buz kutusu yerine ayaz yıkaması + kristal kırıkları + damla sarkıtlar; simgeler fırça alev, mürekkep
  yıldız, zehir / kan damlası. `Enemy.EliteStar`: hale + fırça yıldız.
- `Corpse`: 2 doku pikselli bloklu sert çözülme yerine fbm ile kâğıt yanığı çözülmesi (koyu halka + ince kor, yumuşak alfa).
- `FX.decal`: piksel çıkartma yerine `kan_*` / `catlak_*` mürekkep çıkartması. `FX.blood` parçacıkları hız yönünde damla.
  `FX.shock_line` taşları kül pulu. `FX.anim`: mürekkep karesi olmayan piksel animasyonu oynatılmaz (yerine büyü sıçrantısı).
- `FirePool` (fırça alev dilleri + kor yıkaması), `GroundMarker` (ortası kalın kızıl fırça darbesi), `RootSpikes` (taban
  lekesi), `Projectile` (atlas sprite'ı olmayan mermi gövdeleri ve fırlatılan silahların izi mürekkep), `ImpactFrame`
  (siluet `ink_char` ile; `toon_light` piksel-AA'sı yok), `Level` yaprak yedeği (3x2 piksel yerine fırça yaprak).
- Arayüz: `PixUI.rect` v2'de `InkUI.rect`e düşer (ince şerit fırça darbesi, küçük kare mürekkep noktası, geniş alan yıkama);
  HUD'daki bekleme örtüsü, kart başlık bandı, tılsım madde işaretleri, Demirci / yuva arka planları buna geçti; lütuf noktası
  kenar yumuşatmalı.
- Bölüm başlık kartı (`InkHUD.banner`): solarken `draw_str`'in kaydırılmış gölge kopyası yarı saydam ana yazının içinden
  görünüp alt satırı iki kat (üst üste binmiş) gösteriyordu. Yeni `_fade_str`: gölge yalnızca tam görünürken, dış çizgi a² ile
  söner; alt satır başlığın fırça kuyruklarından ayrıldı (y + 42) ve kendi yıkamasını aldı.

**Önce / sonra çekimi:** `tools/tests/fx_vitrin.gd` (`-- --pencere=1920x1080 --fx_vitrin=C:/abs/klasor`): her efekt türünü
kameranın ortasına sabit düzende yerleştirir (kıvılcım, kan, ruh, alev, duman, toz, halka, hız çizgisi, şimşek, yazılar, patlama,
yer çarpması, çıkartmalar, alev gölü, uyarı, gök gürlemesi, kökler, totem, ceset) ve `vitrin_<panel>_<n>.png` kaydeder.

**Bilinen kalanlar:** yaydaki kiriş/ok (`Player.BowString`, 1 px `draw_rect`) yay çalışmasının kapsamında, burada
dokunulmadı. Ayarlar'daki "keskin piksel" tam sayı ölçekleme seçeneği HD/kamera çalışmasının kapsamında.


## Dövüş temposu v20: biraz daha ağır kombolar, saldırı hızı statı, Kızışma

Geri bildirim: "kombolar çok hızlı oldu, biraz yavaşlatalım. Saldırı hızı kazanabilmeliyiz. Bazı silahlarda vurdukça
saldırı hızı artan bir pasif olsun. Kombo güzel görünüyor." Savuruş biçimleri, iptaller, ara bellekler, Kut Yankısı ve
isabet iptali aynı; yalnızca evre süreleri değişti.

### Genel yavaşlama (`Player.TEMPO_YAVAS`, `Player.TEMPO_V20`)

Tek düğme `TEMPO_YAVAS` (1,0 = v20, 0 = v19 temposu, 1,5 = daha ağır). Her evre `1 + TEMPO_YAVAS × pay` ile çarpılır;
sınıf payları `[ilk hazırlık, zincir hazırlığı, süpürme, kilit, toparlanma]`: hançer 0,05 / 0,15 / 0 / 0,25 / 0,15 · düello,
kılıç, mızrak 0,05 / 0,15 / 0 / 0,22 / 0,15 · kırbaç 0,05 / 0,12 / 0 / 0,2 / 0,12 · uzun sap 0,04 / 0,12 / 0 / 0,18 / 0,12 ·
ağır 0,03 / 0,06 / 0 / 0,1 / 0,08 · dev 0 / 0,06 / 0 / 0,1 / 0,06. Yanıt verme önce: basış→temas neredeyse aynı kalır, uzayan
zincir aralığıdır (kilit + zincir hazırlığı). Süpürme (2-3 karelik son yay, smear karesi) hiç değişmez: kombonun görünüşü odur.

Ölçüm (`-- --dovus --boss --hiz`, 60 Hz, ±1 kare; silah taban aps'iyle, niteliksiz; "önce" aynı betik `TEMPO_YAVAS = 0`):

| Silah | basış→temas önce → sonra (ms) | zincir aralıkları önce → sonra (ms) | ortalama |
|---|---|---|---|
| İkiz Bıçak | 100 → 100 | 117, 100, 167 → 150, 100, 200 | +17% |
| Böri Hançeri | 100 → 100 | 117, 117, 117 → 150, 117, 133 | +14% |
| Kurt Pençeleri | 67 → 67 | 200, 133, 117 → 250, 133, 150 | +18% |
| Ay Palası | 67 → 67 | 217, 117, 83 → 250, 133, 117 | +19% |
| Yatağan | 100 → 117 | 167, 150, 200 → 183, 183, 233 | +15% |
| Rüzgâr Kılıcı | 100 → 117 | 167, 200, 200 → 183, 233, 233 | +14% |
| Alp Kılıcı | 133 → 133 | 183, 233, 233 → 217, 267, 283 | +18% |
| Ruh / Yılan Kılıcı | 133 → 133 | 183, 233, 233 → 217, 250-267, 283 | +16-18% |
| Ayaz Kılıcı | 133 → 133 | 233, 233, 233 → 267, 283, 267 | +17% |
| Yıldırım Kılıcı | 133 → 133 | 183, 250, 267 → 217, 283, 317 | +16% |
| Kargı / Tulpar | 150 → 150 | 167, 217, 200-233 → 200, 250, 250-283 | +19% |
| Kement / Od Kamçısı | 183 → 183 | 233-267, 267-283, 267-283 → 250-300, 300-317, 300-317 | +12% |
| Teber / Tırpan | 183 → 200 | 250, 267-317, 317-467 → 300, 300-350, 367-533 | +14-16% |
| Gürz / Çivili Topuz | 267 → 283 | 367-417, 517, 450 → 383-450, 567, 450 | +6-7% |
| Savaş Baltası / İkiz Balta | 267 → 283-300 | 433 / 367-633 → 450 / 367-667 | +4% |
| Ulu Kılıç | 383 → 383 | 483, 817, 483 → 533, 883, 550 | +10% |
| Bozgun Kılıcı | 367 → 367 | 417, 850, 567 → 467, 933, 633 | +10% |
| Dağ / Kor Çekici | 367-383 → 367-383 | 550-567, 567-583, 550-567 → 583-617, 633, 600-617 | +8% |

### Saldırı hızı statı (`Player.HIZ`, `hiz_kaynak`, `hiz_bonus`)

Oyuncu statı (yüzde). Evrelerin hepsini (hazırlık, tutuş, süpürme, kilit, toparlanma) `1 / (1 + hız × sınıf etkisi)`
oranında kısaltır; zincir aralığı ve basış→temas birlikte kısalır. Sınıf etkisi: hançer / düello / kılıç / mızrak 1,0,
kırbaç 0,95, uzun sap 0,85, ağır 0,7, dev 0,6. Hiçbir evre okunurluk sınırının altına inmez (hazırlık 2 kare, süpürme 1,
kilit 3 kare; taban zaten kısaysa tabanı korunur; %60'ta 27 silahın tüm zincirlerinde ihlal 0).

| Kaynak | Değer | Nasıl kazanılır |
|---|---|---|
| Silah niteliği "Çevik" (`hiz`) | +%6-20, yalnız o silah | düşen silahta yuvarlanır (yay / fırlatma / büyüde de işler) |
| Kalkan / teçhizat niteliği "Tez Elli" (`saldiri_hizi`) | +%4-10, kuşanılan her eşya | düşen kalkan / teçhizatta yuvarlanır |
| Kurt ongunu (Kam Tılsımı) | seviye başına +%2 | bölümdeki tılsımlarla, koşu içinde |
| Yel Ana'nın Soluğu (tanrı lütfu) | +%15 | tanrı sunağı, yurda dönene dek |
| Kam Davulu (Umay Ana) | seviye başına +%4 (2 seviye: 40 / 85 Kut) | kalıcı |

Kalıcı kaynakların toplamı **en çok %40** (`cap`); Kızışma bunun üstüne eklenir, hepsi birlikte **en çok %60** (`cap_all`).
Yaylarda gerilme, en kısa bırakış ve atış kilidi hızın 0,6'sı oranında kısalır (`Okculuk.hiz_k`; tam bırakış penceresi aynı:
%40'ta Türk yayı gerilme 400 → 322 ms, kilit 140 → 112 ms); fırlatma / büyü beklemesi 0,8'i oranında (`Player._sec_cd`).
Duraklatma ekranında "Saldırı hızı +%N (kaynaklar)" satırı, eşya kartında "Hız" artık gerçek tempodan.

Ölçüm (basış→temas / zincir aralıkları, ms): İkiz Bıçak %0 100/150-200 · %20 83/100-183 · %40 83/83-167; Alp %0 133/217-283
· %20 100/200-233 · %40 100/150-200; Kargı %0 150/200-250 · %20 117/183-200 · %40 100/150-183; Gürz %0 283/450-567 · %20
250/383-483 · %40 233/317-433; Ulu Kılıç %0 383/533-883 · %20 333/483-783 · %40 317/433-700.

### Kızışma (silah pasifi; `items.json` "kizisma", `Player._kz_gain`, `scripts/core/KizismaFX.gd`)

Her yakın isabet (savuruş geçişi başına bir yük: iki düşmana değen vuruş tek yük; çok vuruşlu tırmık / seri saplama her
geçişte bir) bir yük verir, yük başına +%v saldırı hızı (ItemGen yuvarlar, kalite yüzdesine katılır). 1,8 sn vuruşsuz kalınca
0,25 sn'de bir yük söner; hasar alınca tümden söner; silah değişince söner.

| Silah | Yük başına | En çok yük | Tam yükte |
|---|---|---|---|
| İkiz Bıçak | +%3-5 | 6 | +%18-30 |
| Böri Hançeri | +%3-5 | 5 | +%15-25 |
| Kurt Pençeleri | +%4-6 | 5 | +%20-30 |
| Rüzgâr Kılıcı | +%4-6 | 5 | +%20-30 |
| Kement | +%5-8 | 4 | +%20-32 |
| Od Kamçısı | +%5-8 | 4 | +%20-32 |

Geri bildirim: kolda / bıçakta yükle yoğunlaşan mürekkep (savururken bıçağın uç yarısının son kareler yolunda 1-5 incelen
hız çizgisi; her an elden geriye-yukarı savrulan ince tüller ve hafif hale; renk kızıl mürekkepten altına kayar), HUD'da
yakın silah yuvasının üstünde yük taneleri ve "+%N hız", savuruş sesi tam yükte %8 incelir, tam yüke ulaşınca altın halka +
gövde flaşı + "KIZIŞMA". Yatağanın eski "ivme" mekaniği aynı göstergeyi ve görseli (çelik renkte) kullanır, kuralı değişmedi.

### Saniyedeki hasar (kart)

`ItemGen.dps` yakın silahta artık `1 / aps` değil gerçek tempodan: zincirin adım çarpanları toplamı / bir zincir turunun süresi
(`Player.tempo_aps`: hazırlık + tutuş + süpürme + kilit; v20 yavaşlaması, saldırı hızı, "Ağır" kusuru, ikiz bıçak / Ay Dansı
hızlanması dahil; Kızışma sayılmaz). Kartın "Hız" değeri vuruş / sn (İkiz Bıçak ~9, Alp ~4,1, Gürz ~2,1). Uzak silahta
aps × saldırı hızı.

### Test

`-- --dovus --boss` artık sonda v20 bölümünü de koşar; `--hiz` yalnız onu (`--hiz_silah=a,b` süzer): 27 silahta %0 / %20 / %40
ve tam Kızışma ile basış→temas ve zincir aralıkları, en az kare denetimi, kaynak toplamı ve üst sınır, kart hızı / SnH (+%20
Çevik), yay gerilmesi, Kızışma yük dizisi (İkiz Bıçak 9 savuruşta 1, 2, 4, 6...; Kement 1, 1, 2, 2, 3...), sönme, hasarla
sönme, ses perdesi. `--klip20 --pencere=1920x1080 --anlik=<klasör>` (headless değil) Kızışma görsel / HUD anlık görüntüleri
(`v20_*.png`). TAKILMA=0.

## Bengü v20: kurt başlıklı kadın savaşçı ve fizikli uzun saç

İstek: "Bengü bir kadın adı; kurt başı yerine kurt başlığı olsun, uzun ve güzel saçı fizikli olsun, iyi bir fiziği olsun."
Bengü artık kurt kafalı bir yaratık değil: Asena / Bozkurt soyundan bir bozkır şaman-savaşçısı kadın. Kurt kimliği başlıkta
yaşar; gerçek kurt biçimi (Kut gücü "Bozkurt" dönüşümü, `bengu_kurt_v2`) aynen kurt kalır.

### Tasarım (`tools/artgen/bengu_ink.py`)
- **Kurt başlığı:** ak kurdun üst kafatası başın üstüne oturur; kalın burnu alnın üstünden öne uzanır (iri siyah burun ucu),
  kulaklar dik, üst çenenin iki köpek dişi alnın önünde sarkar. Başlığın gözü camgöbeği ışır (eski "Kut gözü" kimliği ışıma
  katmanında sürüyor), alnında kırmızı tamga, burun yanında savaş boyası. Yan post yüzün arkasını örter, boyunda omuzlara
  inen gri kurt postu pelerine bağlanır (alt kenarı tutamlı); ön pençe omuzdan göğse sarkar, altın toka + turkuaz taş.
- **Yüz:** yandan insan profili (yüz başlığa göre 1,18 büyük çizilir: 1080p'de ~25 px yüz okunur), kurt burnunun gölgesinde
  badem göz (koyu camgöbeği bebek, beyaz parıltı), kalın kaş, kanatlı üst kirpik, ince dudak; elmacık kemiği boyunca kalın +
  ince kırmızı savaş boyası, çenede dikey çizgi. Şakaktan çene altına inen saç tutamı ve kurt burnunun altından kâkül yüzü
  çerçeveler. Açık ağız (`jaw`) savaş narası olarak çizilir.
- **Fizik:** atletik kahraman oranı (~7 baş), kadın gövdesi: omuzlar biraz dar, bel ince (iki kat sarılı turkuaz kuşakla
  sıkılı), kalça hafif geniş; göğüs lamel yeleğin altında (cinselleştirme yok). Kollar `AW` = 0,88, omuzluk `AWP` = 0,86
  incelikte (kemik boyları ve Player.gd kol iskeleti aynı).
- **Renk kimliği** korunur: kırmızı kaftan + altın sırma, çelik lamel yelek / omuzluk / dizlik, çivit şalvar, kahve çizme,
  turkuaz (eski boyun atkısı artık belde kuşak; iki kuyruğu belin arkasından sarkar).
- Kare düzeni, hücre (384x320), köken, kemik boyları ve kol parçaları (`bengu_kol_v2`) aynı: SpriteAnim, vuruş kutuları,
  silah tutuşu, hayalet / vuruş karesi değişmez. Yeni kare çapaları (json, her kare): `sac` (saçın başlığın arka kenarından
  çıktığı ense noktası), `sac_d` (kökün ilk doğrultusu, ekran açısı), `neck`, `hip` (sırt çizgisi). Yuvarlanmada tuval
  dönüşümü uygulanmış hâlleri yazılır (saç topla döner).

### Uzun saç (`scripts/core/BenguSac.gd`, `shaders/bengu_sac.gdshader`)
(v21'de görünüş ve hareket yeniden yazıldı, uzak örgü kaldırıldı: aşağıdaki "Bengü v21" bölümü. Bu bölüm v20 kaydıdır.)
Sprite'a çizilmez: her kare çalışma zamanında benzetilir ve mürekkep-cel fırça şeridi olarak çizilir.
- **Zincirler:** gür at kuyruğu (12 nokta x 2,2 = ~26 birim, beline iner), uzak örgü (9 x 2,0, gövdenin arkasında), yakın örgü
  (8 x 1,9, kulağın arkasından omuz üstüne düşer). Kök = `sac` çapası + baş çerçevesinde ofset; ikinci nokta `sac_d`
  doğrultusuna çekilir (saç başlığın altından belli bir yönde çıkar).
- **Benzetim:** küresel uzayda Verlet, sabit 1/120 sn alt adım (kare hızından bağımsız; en çok 8 adım/kare). Yerçekimi 430,
  hava sürtünmesi 6,6/sn (mutlak hıza göre: koşuda saç arkaya akar, sıçrayışta aşağı, düşüşte yukarı savrulur), hafif sürekli
  esinti + ara ara sağanak, koşuda uçlarda çırpınma. Kısıtlar Jakobsen gevşetmesiyle (alt adım başına 8 tur): iki yönlü parça
  boyu (kök sabit), bükülme = i ile i+2 arası en kısa uzaklık (kökte ~düz, uçta serbest; katlanma/zikzak yok), %4 uzama sınırı
  (önceki konum da kaydırılır: hız eklenmez). İlk deneme "lideri izle" (FTL) kamçılanıp titriyordu; çevrimdışı benzetimle
  (koşu + 14 fps basamaklı baş sıçraması) karşılaştırılıp bırakıldı.
- **Çapa yumuşatma:** sprite karesi 8-18 fps'de değişir; çapa yerel uzayda kısa üstel yumuşatmadan geçer (yoksa koşunun her
  karesindeki baş sıçraması saçı kamçılar). Yön değişince yumuşatılmış çapa aynalanır; saç küresel uzayda kaldığı için kesmeden
  öbür yana savrulur.
- **Gövde:** sırt kapsülü (boyun -> kalça, sprite silüetine denk yarıçap 6,6 -> 5,8, kalça altında etek açılır); içine giren
  nokta dışarı, göğüs yanındaysa sırt yanına itilir. At kuyruğu kapsülün 0,8'iyle sırtın üstünde yatar. Yerdeyken saç toprağa
  girmez, sürtünür. Işınlanmada (>48 birim) ve yeniden görünürken (kurt / Don dönüşümü bitişi) dinlenme duruşundan başlar.
- **Katmanlar:** iki düğüm de SpriteAnim'in çocuğu (ezilme/esneme, eğilme ve görünürlük gövdeyle aynı). Arka katman
  (SpriteAnim'in ilk çocuğu): uzak örgü. Ön katman (gövde sprite'ının hemen önü, kol iskeletinin altı): at kuyruğu post
  pelerinin üstüne düşer (koyu saç ak postun üstünde en iyi okunur; arkada çizilince sırtta silüetin içinde kayboluyordu),
  yakın örgü. Kök başlığın altında altın saç bağıyla başlar.
- **Çizim:** `RenderingServer.canvas_item_add_triangle_array` ile şerit (Catmull-Rom x3). At kuyruğu aynı eğri üzerinde beş
  tutam (uca doğru açılır, boyları farklı; aradaki kontur tel ayrımı olur) + iki uçuşan ince tel. Örgü: V loblu plak deseni,
  ucunda altın halka, serbest püskül, turkuaz boncuk. Gölgelendirici: silindir normaliyle iki tonlu cel (ışık sol üst), kırık tel
  parlaması, gölgede kesik mürekkep tel çizgileri, kökte başlık gölgesi; kontur ekran türeviyle (fwidth) kenar yumuşatmalı,
  kalınlığı genişlikten bağımsız 0,3 birim. Vuruş parlaması / zehir tonu / ay gölgesi gövde malzemesinden kopyalanır, ışıklar
  ink_char ile aynı.
- **Dikkat (HDR 2D):** görüntü alanı `use_hdr_2d` iken Godot köşe renklerini sRGB -> doğrusal çevirir; şerit verisi köşe
  renginde taşındığı için gölgelendirici `vcol_linear` ile geri çevirir (yoksa örgü kipi "post" kipine düşüp saydam/ak
  görünüyordu).
- Yalnızca stil v2 (v1 piksel görünümde `BenguSac.ekle` saç takmaz). Duraklatmada / başlık ekranında ilk duruş çizilir,
  benzetim durur.

### HD paketi
`KY_HD=2 python export_ink.py --bengu` + `python hd_paket.py --paketle`: `bengu_v2`, `_p1`, `_p2`, `bengu_kol_v2` yeniden
üretildi, manifest md5'leri güncel (oyun HD'den temel dokuya düşmez).

### Test
`tools/tests/bengu_testi.gd`:
- `godot --headless --path . --quit-after 99999 -- --bengu [--boss]`: saç zincirlerinin sağlığı (NaN yok, uzama < %6,
  erim zincir boyunu aşmıyor), durgunken saç gövdenin önüne geçmiyor, koşuda arkaya akıyor, sola dönünce öbür yana geçiyor,
  kurt dönüşümünde gizli, dönüşten sonra yeniden görünür. Sonda `[bengu] OZET hata=n`.
- `godot --path . --fixed-fps 60 -- --bengu=C:/mutlak/klasor --boss --pencere=1920x1080 [--doku=2] [--sac_yakin]`: durgun,
  koşu, sıçrayış, saldırı, yay germe, yuvarlanma, dönüş, kurt ve kurt sonrası çekimleri (+ `k_*` yakın kırpım) ve
  koşu -> duruş -> sıçrayış kare dizisi (`dizi/sNNN.png`). `--sac_yakin` kamerayı ~2,2 kat yaklaştırır, `--sac_renk` şeritleri
  hata ayıklama renkleriyle çizer, `--sac_govdesiz` sırt çarpışmasını kapatır.

## Bengü v21: daha doğal saç

İstek: "Bengü'nün saçını daha iyi, daha doğal yapalım."
v20 saçının sorunları: kalın, düz koyu kurdeleler gibi okunuyordu (tek eğri üstünde aynı uca toplanan tutamlar); dönüşten
hemen sonra saç başın üstünden öne kamçılanıyordu; hayalet izinde ve darbe karesinde gövde saçsız kalıyordu; sürekli sola
esen esinti sola bakarken durgun saçı öne (yüze) sürüklüyordu.

### Görünüş (`scripts/core/BenguSac.gd`, `shaders/bengu_sac.gdshaderinc`)
- **Sadeleşme:** uzak örgü kaldırıldı (gövdenin arkasında neredeyse görünmüyor, yalnızca kalabalık ediyordu). Kalan: altın
  bağla toplanmış gür, dökümlü yele + kulağın arkasından omza düşen tek ince örgü (en 1,5; sık V lobları, ucunda altın halka,
  üç küçük sivri püskül, turkuaz boncuk).
- **Yele katmanları** (hepsi aynı benzetilen omurgayı paylaşır, Catmull-Rom x2):
  1. *Kütle:* en koyu ton, silüeti verir. Kökte bağda toplu (0,34 W), ortada en gür (W = 8 birim), omurganın %88'inde sivri
     biter.
  2. *Yedi tutam:* enine yer -0,8..+0,86, boy 0,62..1,0, en 0,24..0,56 W, ton 0,15 (arka, koyu) .. 0,92 (ön, açık); arka
     tutamlar önce çizilir. Uca doğru birbirinden ayrılır ve her biri kendi uç kıvrımıyla (kimi içe, kimi dışa) ayrı sivri
     uçla biter: "çok uçlu" yele ucu. Tutam başına evreli hafif dalga (durgunken çok az, uç hızıyla büyür).
  3. *Üç uçuşan tel:* kütlenin kenarından kopan 0,4 birim ince, kontursuz teller; gecikmeli kıvrılır, ışık yanında parlar.
  4. Altın saç bağı küçüldü (oyun yakınlığında parlak bir leke gibi duruyordu).
  Sıkı kıvrımda (eğrilik yarıçapı yarı eni aşınca) kütle ve tutamların eni ve ayrılması daralır: düşüşte yukarı savrulan
  saç kendi üstüne katlanıp kalın bir boru gibi görünmez.
- **Renk:** mavi-mor parıltılı neredeyse siyah (derin `14121e`, orta `2a283e`, gölge `0b0a12`, parlama `99abe3`, kenar
  parıltısı `5c69a1`). Ötüken ormanı, Kaf karı (Yelbegen arenası) ve Tamu kızılında (Erlik Han arenası) denendi: ak kurt
  postunun üstünde güçlü, sıcak arka planda serin parıltı saçı ayırıyor (sıcak parıltılı koyu kahve kızıl kaftanla
  karışırdı).
- **Gölgelendirici:** yumuşak iki tonlu cel; omurganın ~%25'inde tel tel kırık uçlu parlama halkası (anime "melek halkası",
  ön tutamlarda daha parlak; omurga oranına bağlı olduğundan tutamlar arasında akışı izler); ışık yanında uzun kesik tel
  parlamaları; ışık yanı kenarda konturun hemen içinde ince serin kenar parıltısı; gölge ve orta tonda ekran pikseli
  inceliğinde kesik tel çizgileri (tel aralığı ekranda 5 pikselden dar olunca söner: 1080p oyun yakınlığında gürültü
  yapmaz, 1440p / yakın çekimde ayrıntı verir). Kontur gölge yanında kalın (x1,6), ışık yanında ince (x0,55), ince uçlarda
  incelir; kütlenin dış konturu tam mürekkep ve kalın (x1,35), tutamların iç konturu yarı gölge rengi: silüet güçlü, tutam
  ayrımı yumuşak.

### Hareket
- **Kök:** kök ve ikinci nokta sabit (saç bağı), ilk üç eklemde açı sınırı (0,2 -> 0,55 rad): saç kökte katlanmaz. Kök
  doğrultusu yine de saçın kendi doğrultusuna yarı yarıya döner (en çok ~105°; yele yalnızca sırt yanındayken): düşüşte saç
  bağdan itibaren kalkar, koşuda kökten arkaya akar (tam sabit kökte saç bağın altında U çizip çengel gibi kıvrılıyordu).
- **Sertlik:** zincirin geri kalanında ebeveyne göre bükülme yayı (alt adım başına kökte 0,05, uçta 0; profil (1-t)²):
  kök dolgun ve yönlü, uç gevşek; ip gibi sarkmaz, jöle gibi titremez.
- **Hava:** doğrusal 1,5/sn + hızın karesiyle 0,018/birim sürtünme (yavaş salınım uzun sürer; koşuda saç ~45-55° arkaya
  akar; uzun düşüşte kalkar), köke göre bağıl hıza 2,5/sn iç sürtünme (salınım bir kez olur), yerçekimi 650 (oyuncu 1180:
  sıçrayış tepesinde saç hafifçe havalanır). Koşuda omurga boyunca ilerleyen yumuşak dalga (8,5 rad/sn, uca doğru t²).
- **Esinti:** bakış yönüne göre arkaya doğru hafif (5 + 14 x sağanak) + iki yana eşit, seyrek salınım; sola bakarken
  durgun saç öne sürüklenmez.
- **Yön değişimi:** kök doğrultusu küresel açıyla yumuşar; 1,2 rad'dan büyük dönüşte her zaman aşağıdan dolaşır, açısal hız
  en çok 15 rad/sn. Tutam yayılım yönü ~1/6 sn'de aynalanır (tutamlar çaprazlanarak geçer). Hızlı çıkışta saç arkaya
  savrulur ama başlık tepesinin altında kalır.
- **Çarpışma:** sırt kapsülü kökün 4 birim altından (omuz hizası) başlar, üst kapağı yok, yalnızca sırt yarısında iter;
  öne hızla (> ~36 birim/sn) savrulan uç yarısı geçebilir: duruşta saç omzun yanından öne salınır (uç kökün önüne gelir),
  sonra arkaya yerleşir. Gövde çizgisinin önüne geçen saç 650 birim/sn² ile sırta döner. Baş çemberi (r 7,2) yalnızca yüz
  yanını ve tepeyi iter. Bırakılan v20 kuralları ve neden: göğüs yanındaki noktayı kapsülün öbür yanına zorlamak + kapsülün
  kökü içine alması saçı boyna atkı gibi doluyordu; zincir boyunca açı sınırı kıvrık saçı kilitli bir mekanizma gibi
  donduruyordu; "i ile i+2 en kısa uzaklık" kısıtı noktayı dışarı iterek saçı başın üstüne katlıyor, örgüyü düğümlüyordu.
- **Eylem itkileri** (animasyon başlangıcı): saldırı (saç geride kalıp savrulur), darbe (yukarı sıçrar), iniş (çöker).
  Geri tepme, yuvarlanma, sıçrayış kökün hareketinden kendiliğinden gelir.

### Hayalet izi ve darbe karesi
- Çizim verisi her karede bir kez SpriteAnim yerelinde kurulur (`_ag_kur`); arka / ön katman ve kopyalar aynı diziyi
  kullanır. `BenguSac.kopya` o anki çizimi donmuş bir `Kopya` düğümüne koyar.
- `FX.ghost` gövde sprite'ı Bengü'nünse (`BenguSac.bul`) aynı renkte, toplamalı, solan bir saç kopyası ekler
  (`bengu_sac_hayalet.gdshader`: `blend_add`, ışıksız, koyu saç biraz aydınlatılır). Yalnızca kütle + örgü gövdesi kopyalanır:
  üst üste binen tutamlar toplamalı karışımda parlaklığı katlayıp saçı bembeyaz yapıyordu.
- `ImpactFrame` (darbe karesi) beyaz siluete saçı da ekler (flash = 1).

### Başarım
Benzetim + çizim verisi (headless, hata ayıklama derlemesi, `--bengu --boss` boyunca ortalama): ~0,45-0,75 ms/kare (makine
yüküne göre; v20 aynı ölçümde ~1,2 ms). Yele profilleri (kütle eni, tutam ofset / en / dalga genliği, teller) omurga nokta sayısına göre bir kez
hesaplanır, şerit üçgen indeksleri önbellekte, normal hesabı şerit döngüsünde. GPU tarafı birkaç yüz üçgen, tek malzeme.

### Test (`tools/tests/bengu_testi.gd`)
`--bengu [--boss]` denetimleri: zincir sağlığı (NaN yok, uzama < %6), durgunken saç gövdenin önünde değil, koşuda arkaya
akıyor, **duruşta öne salınıyor** (uç durgun yerinden en az 2 birim öne gelmeli; ölçülen ~+9..+10), dönüşte ve yerinde sağ-sol
dönüşlerde **saç başlık tepesinin üstüne / yüz önüne çıkmıyor**, **sola bakarken durgun saç öne sürüklenmiyor**, **hayalet
izi ve darbe karesi saçlı**, kurt dönüşümünde gizli / sonra yeniden görünür; sonda saç süresi (ms/kare) ve `OZET hata=n`. Çekimlere düşüş
(`3b_dusus`) ve dönüş kare dizisi (`dizi/dNNN.png`) eklendi. Hata ayıklama bayrakları: `--sac_iz` (dönüş / koşu /
yuvarlanma boyunca zincir dökümü), `--sac_renk`,
`--sac_govdesiz`, `--sac_yakin`.

## v20: Unsur (silah ruhu), iz çeşitliliği, ağır silah yer tozu

Geri bildirim: "Silahların çoğunun mürekkep izi aynı savuruş. Ağır silahlar yere vurunca TOZ kalkardı, o gitmiş. Yerden aldığımız
silahların ateş, buz, elektrik, şaman gücü, doğa gücü gibi bir unsuru olsun; mürekkebi ona uysun, özellikleri de değişsin
(ateşin mürekkebi alev saçsın, elektrikli olan şimşek; şansla düşmanı yaksın ya da başına yıldırım indirsin). Kırmızı silah
mürekkebi biraz daha koyu olsun."

### Unsur (`scripts/core/Unsur.gd`)

Yerden alınan silahın (rastgele malzemeyle yuvarlanan her düşüş: `ItemGen.random_drop` → `roll(id, tier)`) bir unsuru
olabilir. Başlangıç silahları, Demirci / test eşyaları gibi malzemesi açıkça verilen eşyalar sade kalır (testler belirleyici).
Ongun (Kurt / Kartal / Ayı) ayrı bir eksendir (ölçekleme rengi); unsur onun yerine geçmez, yanına eklenir.

* **Kimler:** yakın (kılıç, ağır, mızrak, hançer, kırbaç) + yay ve fırlatma (`kind`: slash, heavy, thrust, dual, whip, bow, throw).
  Büyü silahları (Kam Kopuzu, Gök Asası, Yel Borusu) unsursuz: zaten kendi büyüleri var. Tetiklenme `Player._deal` içinde
  olduğundan oklar, fırlatılan balta, sapan, Bozkurt biçimi ve kalkan karşı vuruşu da tetikler.
* **Olasılık:** sıradan %30 · nadir %50 · destansı %70 · efsanevi %90; tema silahı +%25 ve unsur gelirse %80 kendi unsuru
  (Od Kamçısı / Kor Çekici / Od Okları → od, Ayaz Ata'nın Kılıcı / Rüzgâr Kılıcı → ayaz, Yıldırım Kılıcı / Tufan Yayı →
  yıldırım, Ruh Kılıcı / Erlik Tırpanı / Kartal Tüyleri → kam, Yılan Kılıcı / Ulu Kayın Asası → Yer-Su); malzeme eğilimi %45
  (od taşı → od, ayaz → ayaz, gök demiri → yıldırım, ruhani → kam, yeşim → Yer-Su). Kalan ağırlıklar (sıradan → efsanevi):
  od 30→24, ayaz 28→22, yıldırım 12→24, kam 6→19, Yer-Su 24→20 (nadir unsurlar yüksek nadirlikte daha olası).
  600 düşüşlük ölçüm (kademe 2, kalkan / teçhizat dahil): %31 unsurlu; od 60, ayaz 42, Yer-Su 39, kam 31, yıldırım 16.
* **Unsur gücü** `unsur_g`: sıradan 1,0 · nadir 1,1 · destansı 1,22 · efsanevi 1,35 (×0,92-1,08).
* **Tetiklenme olasılığı** = taban × unsur gücü × hız katsayısı × (boss 0,5). Hız katsayısı `clamp((2 / aps)^0,6; 0,55; 1,6)`:
  vuruş başına yavaş silah daha olası, hızlı silah daha az (saniyedeki tetiklenme silahlar arasında yakın kalır): Ulu Kılıç
  (0,85 aps) 1,6 · Alp Kılıcı (2,3) 0,92 · İkiz Bıçaklar (4,6) 0,61. Bosslarda süreler de yarıya iner; donma ve kök yoktur.
* **Ad / kart / görünüş:** sıfat adın önünde ("Keskin **Alazlı** Demir Alp Kılıcı"; Alazlı, Ayazlı, Şimşekli, Tözlü, Köklü);
  kartta unsur renginde "◈ Unsur: ..." satırı ve o eşyanın gerçek yüzdeleri; HUD yuvasında köşede unsur simgesi (yordamsal,
  kenar yumuşatmalı: alev, kar tanesi, şimşek, ruh gözü, yaprak) + yuvaya ince unsur yıkaması; yerdeki eşyada unsur renginde
  nabız gibi atan hale, unsura özgü zerreler (alev dili, buz yıldızı, şimşek çatırtısı, ruh dumanı, yaprak), simge, ışık
  unsur rengine kayar; elde savururken bıçak boyunca unsur ışıması (`Unsur.BladeGlow`). Savuruş izi unsurun paletinde
  (`InkFX.weapon_pal` önce unsura bakar), vuruş sıçrantıları izden paleti alır.

| Unsur | Sıfat / palet | Tetiklenme (taban) | Etki | Bossta |
|---|---|---|---|---|
| **Od** (ateş) | Alazlı · 1 od | %20 tutuşma (bitiriş / ağır ×1,3) | 3 sn yanma (0,5 sn'de 3×(1+0,6×kademe)); yanan düşmana +%10 hasar; zincir bitirişi yerdeyse alev gölü (r 30, 2,2 sn, sn'de silah hasarının %24'ü, 1,4 sn bekleme) | %10, yanma 1,5 sn |
| **Ayaz** (buz) | Ayazlı · 2 ayaz | %45 ayaz yükü (+1; bitiriş / ağır +2) | en çok 4 yük, 3,5 sn; yük başına %8 yavaşlatır; 4 yükte donar (1,3 sn, seçkin 0,9); donmuşa vuruş **kırar**: kesin kritik ×1,25 + 56 birimde çevreye %30 buz kıymığı | %22,5 yük (yük başına %4 yavaşlatır); donma yok, 4 yükte sıradaki vuruş "buz kırığı" ×1,35 |
| **Yıldırım** (şimşek) | Şimşekli · 5 yıldırım | %13 (bitiriş / ağır ×1,5), hedef başına 0,45 sn bekleme | hedefin başına gökten şimşek: silah hasarının %80'i + 0,35 sn sersem; 110 birimde 2 düşmana sıçrar (%40, 0,2 sn) | %6,5; sersem ×0,4 (`Enemy.stun`) |
| **Kam** (şaman ruhu) | Tözlü · 10 kam (yeni) | %30 töz damgası, %12 ruh kurdu yankısı | damga 5 sn: +%10 hasar alır; damgalı ölünce ruh zerresi oyuncuya uçar (canın %3'ü + 10 Kut); yankı 0,16 sn sonra hayalet pençe, silah hasarının %50'si. Yeraltında (Üç Âlem "yer") olasılıklar ×1,5 | %15 / %6, damga 2,5 sn |
| **Yer-Su** (doğa) | Köklü · 11 Yer-Su (yeni) | %14 kök, %30 diken zehri | kök 1,1 sn (seçkin 0,65) yerinde tutar (ayağa dolanan kökler); +1 zehir yükü (4 sn); zincir bitirişi yaprak şifası: canın %1,5'i + 1 (2,5 sn bekleme) | kök yok; zehir %15 |

Taban hasarlar `Unsur._base` = silah hasarı × eşya ölçeği (ongun / kademe; `_deal` çarpanları yok); unsur vuruşları unsuru
yeniden tetiklemez (`unsur_proc`), Kut verir (%10). Sayılar `Unsur.N` sözlüğünde.

**Denge ölçümü** (`--unsur --boss`, 6 tur × 3'lü zincir, 3 kukla, nadir unsur gücü 1,1; "unsur payı" = unsur vuruşları + ek
çarpanlar + süreğen hasar tahmini / silahın kendi hasarı): silah × unsur (6 tur) unsur
payı çoğunlukla +%8-13: Od +%8-10 (yanma + göl), Ayaz +%4-10 (+ donma: Dağ Çekici'nde 6 turda 19 donma / 18 kırılma),
Yıldırım +%7-13 (Dağ Çekici 18 şimşek / 36 sıçrama), Kam +%10-13 (+ damgalı öldürme ödülü), Yer-Su +%1-7 hasar (asıl
değeri kök ve şifa: 6 turda 5-23 kök, 9-12 can). Hızlı / yavaş silahlarda pay yakın (İkiz Bıçaklar +%7-13, Dağ Çekici +%1-13):
hız katsayısı işini görüyor. Bosslarda olay / isabet oranı yaklaşık yarı (Od 0,29 → 0,08, Yer-Su 0,46 → 0,29; tek kuklada
örnek küçük, yıldırımda hedef başına bekleme yüzünden gürültülü).

### İz çeşitliliği (`InkTrail.setup`, `shaders/ink_brush.gdshader`)

Önceki sürümde sınıf farkları vardı ama genişlik / ömür farkları küçüktü; çoğu silah aynı kızıl hilal gibi okunuyordu.

* **Hançer** ince hızlı çift fiske (YOL, yarı genişlik 2,6, ömür 0,16, kıl ölçeği 1,6: sık ince kıl, pürüz 0,65).
* **Kılıç** temiz hilal (%62, pürüz 0,9, iz 0,9).
* **Ağır** kalın sürüklenen kuru darbe: genişlik bıçak boyunun %105'i, ömür 0,32, arkada her zaman koyu kuru sürüntü katmanı,
  kıl dokusu boyuna 0,55 (uzun sürüklenen kıl izleri), pürüz 1,6, iz 1,5, zerre ×2,4 ve bitişte uçta sıçrantı.
* **Uzun sap** geniş süpürme: ince uzun hilal (%34), ömür 0,3, içte soluk ikinci yankı yayı.
* **Mızrak / saplama** uzun düz çizgi + üç soluk yankı (ömür 0,24).
* **Kırbaç** kıvrılan kurdele: yol boyunca genişlik dönerek incelip kalınlaşır (`twist`), baş iğne gibi.
* **Unsur zerreleri** (aynı üçgen dizisi, aynı çizim çağrısı, gölgelendiricide fwidth kenar yumuşatma): od alev dilleri
  (karınlı dipten kıvrılan uzun dil; dipte sarı-beyaz, uçta koyu kızıl) + kor kıvılcımları · ayaz sivri buz kıymıkları (iki
  yüzeyli, beyaz sırtlı, mürekkep konturlu, dönerek düşer) + soğuk sis + parıltı · yıldırım izin dışına sıçrayan, sık yenilenen
  zikzak arkları (beyaz-sıcak kılcal çekirdek, toplamalı ışıma) + kıvılcım · kam tayfsı ard görüntü katmanı (iz arkaya ve
  yukarı kayarak süzülür) + gürültüyle yenen ruh dumanı + ruh kıvılcımı · Yer-Su badem yapraklar (damarlı, salınarak düşer).
* **Kızıl mürekkep** (palet 0) bir ton koyulaştı: gövde `fa0c06` → `d80a10`, çekirdek `a00008` → `86000c`, kenar `ff4a12` →
  `f43c16`, mürekkep `3a0214` → `2e0111`.

### Ağır silah yer tozu (`scripts/core/InkDust.gd`, `shaders/ink_dust.gdshader`)

**Neden kaybolmuştu:** v16'nın `GroundSlamFX` tozu piksel çiziliyordu. Stil v2 mürekkep fırçası işinde (571e42d) v2'de
`GroundSlamFX` tümüyle gizlendi (piksel flaş / şok / moloz / çatlak mürekkebe uymuyordu) ve yerine yalnızca iki küçük, soluk
`FX.dust` kümesi (3-5 yıkama zerresi) + silah paletinde kızıl yer sıçrantısı kaldı. Varsayılan stil v2 olunca (363a7fb) ağır
silahların yer tozu fiilen yok oldu; yere çakma kızıl bir kan lekesi gibi okunuyordu. v18/v19 temposu `_slam_contact`'ı
bozmamıştı (çakma anı doğru karede tetikleniyordu), sorun yalnızca v2 görseliydi.

**Düzeltme:** `GroundSlamFX` v2 dalı artık `InkDust.burst` çağırır (sarsıntı / itiş / titreşim / ışık `_juice` aynen):
* iki yana açılan V tutamları (dik hızlı kol + yatık gövde, ileri taraf dolgun) ve ortada yükselen kabarık çekirdek:
  karakterlerin ardında (etkin z -1; bulutun yere taşan alt kısmı zeminin arkasında kalır)
* zemin boyunca dışa yuvarlanan alçak sürünen toz (şok cephesi, gecikmeli), sekip duran moloz kırıkları, od silahında ve
  Tamu'da kor: önde
* kalıcı dallanan fırça çatlağı (`FX.decal`) + ezik zemin lekesi (güç ≥ 0,85)
* gölgelendirici: fbm gürültüsüyle kabaran karnabahar silüeti, üstte ışık alan açık yıkama, altta orta ton, kenarda koyulaşan
  ıslak pigment bandı, alt kenarda ince mürekkep konturu, tutam başına ton farkı (üst üste binenler ayrı okunur); yaşlandıkça
  kenardan yenip içinde kuru boşluklar açılarak dağılır. Piksel kare yok.
* biyom renkleri: Ötüken orman toprağı, Bozkır sarı bozkır tozu, Kaf kar tozu (ak-mavi), Şahmeran mağara kumu, Tamu kül (koyu,
  korlu), Çini Saray; bilinmeyen biyomda `FX.dust_col`'dan türetilir.
* silah paletindeki yer sıçrantısı (`InkFX.slam`) ×0,62'ye küçüldü: asıl görsel toz.

**Yeni tetikleyiciler:** çakma / sarsıntı bayrağı olmayan ama başı yere inen ağır ve uzun sap savuruşları (ezme, iniş, baş
üstü, adımlı iniş, yel değirmeni; `InkDust.GROUND_SW`) değdikleri karede hafif toz (güç ×0,6, sarsıntısız, sessiz; baş yere
inmezse yok) · Kor Çekici'nin yerde sürüklemesinde başın ardında sürünen toz + kırık (`InkDust.drag`) · Kartal Dalışı inişi.
Bosslar (`FX.ground_slam` güç 2) da aynı tozu kaldırır.

### Test

`-- --unsur --boss [--unsur_silah=a,b] [--unsur_tur=N]` (`tools/tests/unsur_testi.gd`): 600 düşüşlük yuvarlama dağılımı ve
ad denetimi, açık malzemeli eşyaya unsur gelmediği, her silah × her unsur için tetiklenme sayıları ve unsur payı, boss
kuklasında olay / isabet oranı; "[unsur] HATA=n". Pencereli + `--anlik=<klasör>`: `--unsur_cekim=iz,tetik,toz` (iz: düşmansız,
tetiklenmesiz unsur izleri; tetik: her vuruşta tetiklenen unsur; toz: dört ağır silahta basılı çakma, temas sonrası 1/6/14/26/40.
kareler). Biyom tozu için `--boss=tepegoz` (Bozkır), `yelbegen` (Kaf), `sahmeran`, `erlik_han` (Tamu).


## v21: Yıldırım Hamlesi düzeltmesi

Yıldırım Kılıcı tam şarjlı hamlesinde (basılı tutma ≥ 0,6 sn) gökten inen yıldırım artık oyuncunun durduğu yere değil, hamlenin deldiği her düşmanın tepesine iner (`Player._melee_hits`, `atk["thunder"]`). İlk düşmana tam güç (0,85), sonrakilere hafif (0,55) şimşek; tam şarjlı vuruş ×1,3 hasar ve 0,45 sn sersemletme. Bırakışta yalnızca kılıçtan kısa bir kıvılcım ve uzak gürleme. Test: `-- --dovus --boss --yildirim` (şimşek konumu ↔ düşman uzaklığı).
