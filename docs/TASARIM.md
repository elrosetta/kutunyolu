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
sürer (sürünme). ~~Alçak geçitler bilinçli tasarım öğesidir.~~ v25: kaldırıldı, yürünen her yerde en az 3 karo baş
boşluğu var (bkz. "v25: harita, tuzaklar, Üç Âlem'in kaldırılması").

## İlerleme: derinlik, tılsım, parşömen

* **Kut Kapısı → sonraki derinlik:** `Game.next_depth()`; eşyalar, ongunlar, can korunur, şişeler dolar,
  `tier` artar (düşman canı/hasarı ve eşya nadirliği). HUD'da "N. derinlik".
* **Kut Tomarları** (v23; eski adı tılsım, `Pickup.kind == "tilsim"`): her bölümde üç tane (ikisi yolda, biri havadaki
  adada), her boss bir tane. W ile seçim ekranı: Kurt / Kartal / Ayı +1 (azalan getirili hasar çarpanı, bkz. "v23: tomar
  ekonomisi") ve can artışı (+%6 / +%6 / +%15).
* **Parşömenler** (`Pickup.kind == "parsomen"`): çalışan ama açılmamış bir eşyanın tarifi; seçkinlerden kesin,
  diğerlerinden %7. Dokununca `Game.meta.blueprints`'e girer. Ölünce ya da kapıdan geçince koşudaki Kut
  `Game.meta.kut_bank`'a aktarılır. Koşu başında (hikâyeden / ölümden sonra) **Demirci Kam Kuzgun** ekranı:
  Kut karşılığı aç (`Game.unlock`); açılanlar düşme havuzuna katılır (`ItemGen.unlocked`).
  Başlangıç havuzu `Game.BASE_UNLOCKED`. **v24:** açılan eşya ayrıca hemen dövülüp önüne bırakılır (rastgele değerlerle;
  bkz. "v24: tüccar ve silah parşömenleri").
* **Altın** (v24): Bezirgân Sartak'ın pazarında harcanır (bkz. "v24: tüccar ve silah parşömenleri").

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
(v30: PVFX piksel kareleri ve Kenney dokuları kaldırıldı; `anim.json` kimlik listesi kalır, `k_*` adları
`InkDraw.particle` mürekkep karşılıklarının anahtarıdır.)

## Saldırı animasyonu ilkeleri (`bengu.py`)

8 kare: 0-1 hazırlık (ikincisi daha derin ve tutulur), 2-5 vuruş (4 = darbe anı), 5 aşma, 6-7 toparlanma.
Dirsek hazırlıkta bükülü (`af[1]` ≈ 1.5-2.2), darbede gergin (0.0); ön kol darbede %15-30 uzar (`ext`, abartı);
ön omuz vuruş yönüne kayar (`sx`, gövde burulması); arka kol ters salınır; kalça öne adım atar (`hx`).
Godot tarafı: silahın solan kopyaları (smear) + `WeaponTrail` şeridi + `crescent_slash` hilali.

## Bölüm çeşitliliği (`LevelGen.gd`)

Her koşuda stil seçilir: **orman** (tepeler, adalar), **uçurum** (teraslar, derin çukurlar, basamak platformlar),
**mağara** (tavan bantları, sarkıt sütunlar, 3 karo yüksek dar boğazlar (v25'e dek 1 karolu sürünme geçitleri), gökyüzü
ağızları), **harabe** (çökmüş kule kuyuları, zikzak tırmanış, taş duvarlar). Üstüne 2-4 elle tasarlanmış parça (`CHUNKS`:
tünel (v25'e dek sürünme geçidi), sütunlar,
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
geçişlerinde en kötü 1 karo yuvarlanma geçidi (v25: en az 3 karo baş boşluğu, sürünme geçidi yok). Tek zıplama 3,2 karo, çift zıplama ~5,5 karo. `--dok=yol.png` ızgarayı
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
satırı; v25: tek yönlü platform baş boşluğunu ve zıplama yörüngesini kesmez). Geçilemiyorsa `guarantee()` takılan noktadan sağa 7 karolik koridor açar (`carved` sayacı günlükte).
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
- **Demirci Kam Kuzgun** — parşömenleri Kut karşılığı döver (eski Demirci ekranı); v24'ten beri açılan eşyayı hemen verir.
- **Ozan Bilge Kopuz** — destan satırları ve koşu özeti.
Yurttaki kapı bir sonraki derinliğe indirir. **Ölünce taşınan Kut yitirilir** (Ruh Düğümü yoksa). Test: `--yurt` yurtta başlatır.
**v32:** yurt yalnızca koşu başında (ve ölümden sonra) görülür; derinlikler arasında yurda dönülmez, gezgin **Konak** kurulur
(bkz. "v32: Konak ve silah ustası"). Taşınan Kut konaktaki Umay Ocağı'nda bankaya geçer; harcama (Umay / Demirci / Alp Ata) yurtta kalır.

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
| Teçhizat 1 / 2 (v23) | E / R | LB / RB |
| Kut gücü (Bozkurt Ruhu) | F | Sağ çubuk tık |
| Şifa şişesi | Q | Sol çubuk tık |
| Eşya al / değiştir, konuş, tomar oku (v23: kısa dokunuş) | W / ↑ | Yön yukarı / Back |
| ~~Üç Âlem kam transı (v23; S+T yeraltı)~~ v25'te kaldırıldı | — (T boş) | — (LT boş) |
| Don (seçkin ruhu) | G | RT |
| Menüde onay | Boşluk / Enter | A |
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

(v30: yukarıdaki v1 piksel hattı — `export_assets.py`, `export_hd.py`, `pixkit.py`, `pixfont.py`, `biomes.py`, `soil.py`,
`bg_*.py`, `slashfx.py`, `arrows.py`, `hazards.py`, `weapons.py`, `yurt_hd.py` ... — kaldırıldı. Mürekkep varlıkları:
`export_ink.py`, `export_boss_ink.py`, `export_ink_ortam.py` / `_biyom` / `_yeralti`, `export_sus.py`, `weapons_ink.py`,
HD paketi `hd_v2.py`; v1 sprite json'ları satır düzeni şablonu olarak durur.)

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

* **Üç Âlem (v25'te KALDIRILDI; geri bildirim: "yeraltına inme / bulutlara çıkma mekaniğini kaldır"; gizli oda ve Ülgen
  sunağı ganimeti bölüme dağıtıldı, Kam Ata destanı don kılığına bağlandı; aşağıdaki metin tarihçedir) (R / S+R, gamepad sol tetik):** kam transıyla aynı bölümün gök âlemine (Ülgen) ya da yeraltına (Erlik) geçilir.
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
  dikey eşitleme, arayüz boyutu. (v30: v1'e özgü "Ölçekleme: Keskin piksel" satırı kaldırıldı; görüntü hep kesirli ölçekle
  pencereyi doldurur.) `user://ayarlar.cfg`. Doku kalitesi oyun yeniden başlatılınca uygulanır (`*` işareti).
* **HD doku paketleri = gerçek yeniden çizim, büyütme değil.** `raster.SS` çarpanıyla tuval N kat ince ızgarada rasterlanır;
  şekiller mantıksal birimde aynı kalır (`tools/artgen/export_hd.py N`). 2K = temel sayfaların 2 katı (`assets_hd/x2`), 4K = 4 katı
  (`assets_hd/x4`). Yalnızca renk dokuları; normal/parlama haritaları ve JSON meta temelden. `manifest.json` temel boyutları tutar;
  `Data.tex()` büyük dokuyu `ImageTexture.set_size_override` ile temel boyutta raporlar, oyun kodu değişmez.
  Otomatik: 1080p ve üstü 2K, 2160p 4K (960x540 görüntüde 2K paketi 1080p'de, 4K paketi 4K'da ekran pikseline 1:1 oturur).
  (v19: bu paketler yalnızca v1 piksel sanatını kapsar; stil v2 için aşağıdaki "Stil v2 HD doku paketi" bölümüne bkz.
  v30: v1 paketleri — `assets_hd/x4` tümüyle ve x2'deki v1 girdileri — `export_hd.py` ile birlikte kaldırıldı.)
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
Tetikleyiciler: ~~kam gücü ≥ 30 ve bölümde âlem varsa (R gök / S+R yeraltı), yeraltı kapağına yaklaşınca (dünya işareti:
mor ▼ + "S+R: yeraltına in" ya da "kam gücü N/30"), gökte ruh kuşu yakınken ("ruh kuşu" etiketi)~~ (v25: Üç Âlem kartları
kaldırıldı), don ruhu yerdeyken
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
  Görünmez gölge sayılmaz (v25'e dek öbür âlemdekiler de).
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
  kapı), Davul Totemi (`Totem.gd`: gövde ezilip zıplar, tüyler salınır), ruh taşı kapağı ve Ülgen'in altın bulutları
  (v25'te Üç Âlem'le kaldırıldı; `ruh_tasi_v2` / `bulut_1..4_v2` dokuları atlasta kullanılmadan duruyor).
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
* ~~**Gizli oda ganimeti**~~ (v25: gizli odalar Üç Âlem'le kaldırıldı; ganimet `Level._spawn_kesif` ile bölüme dağıtılır).
* **Test:** `-- --stil=v2 --yurt --sus=yurt --cikti=<klasör>` (yurdun 9 durağı), `-- --stil=v2 --sus=dunya --cikti=<klasör>`
  (toplanabilirler, mermiler, Kut Kapısı; v25: bulut / ruh taşı / oda yerine tehlike çukuru karesi). `tools/tests/sus_testi.gd`.
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
(v30: v1 piksel stili ve `--stil` seçeneği kaldırıldı; tek stil mürekkep, `Data.STIL`; bkz. "v30: eski piksel stili (v1) kaldırıldı".)


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

### Görünüş (stil v2; v30'a dek v1 piksel görünüm `--stil=v1` ile aynen duruyordu)

* **Kiriş:** kenar yumuşatmalı `draw_polyline`, koyu mürekkep dış çizgi (0,95 birim) + açık çekirdek (0,38); tam bırakış
  penceresinde altına döner. Yaydaki ok uçuştaki okla aynı SusV2 mürekkep sprite'ı (`ok_<tür>`), kuyruğu gezde, eğimle döner.
* **Uçuş izi:** `shaders/ok_iz.gdshader` — ucu dolgun, kuyruğa incelen fırça şeridi; koyu mürekkep kenar, oka özgü çekirdek
  (Türk krem, Akıncı kızıl, Sağanak / Tufan buz mavisi, Od turuncu, tam bırakış altın; başta HDR parıltı), kuyrukta `bristle.png`
  kıllarına ayrılarak erir. Kenarlar türevle yumuşatılır.
* **Namlu / isabet / duvar:** atış yönünde kısa mürekkep kesiği + yönlü sıçrantı (`InkFX` "cut_b" + "burst_dir"); isabette
  `InkFX.hit("pierce")` (kritikte kademe 2), duvarda soluk kuru fırça tozu; saplı oklar düşmanın çocuğu olarak gövdede kalır.
* Tam gerilme parıltısı: `InkFX` "shard" + kuru halka (eski `FX.burst` piksel kareleri kalktı); tam bırakış altın ensō.

### Test

`godot --headless --path . --quit-after 99999 -- --yay --boss`: her yay için dokunuş→atış→isabet, tam bırakış /
geç bırakış, basılı tutma, 10 Hz seri basış; akış (vuruşta yay, gerilirken saldırı / yuvarlanma, yuvarlanırken yay, Akıncı
yuvarlanma atışı), ok sökme + hazır ok, ok toplama (dökülen / yere saplanan), süzülüş, takılma denetimi. Ekran görüntüleri:
`godot --path . -- --yay --boss --pencere=1920x1080 --yay_goruntu=C:/mutlak/klasor`.

Oyun artık varsayılan olarak v2 mürekkep + cel tarzında açılır (`Data.stil = "v2"`). Eski piksel görünüm: `-- --stil=v1`. (v30'da kaldırıldı)


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
| **Kam** (şaman ruhu) | Tözlü · 10 kam (yeni) | %30 töz damgası, %12 ruh kurdu yankısı | damga 5 sn: +%10 hasar alır; damgalı ölünce ruh zerresi oyuncuya uçar (canın %3'ü + 10 Kut); yankı 0,16 sn sonra hayalet pençe, silah hasarının %50'si. ~~Yeraltında olasılıklar ×1,5~~ (v25: Üç Âlem'le kalktı) | %15 / %6, damga 2,5 sn |
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



## v22: zorluk ve can barları

Geri bildirim (oynayarak): "Düşmanların can barı olsun." · "Zorluk inanılmaz kolay; hiçbir güçlendirme almadan herkesi 2
vuruşta öldürüyorum. Gerçek bir roguelike zorluğu olmalı." Önce ölçüldü (`-- --denge`), sonra denge tek bir ayar dosyasına
(`data/zorluk.json`, okuyan `scripts/core/Zorluk.gd`) taşındı.

### Neden kolaydı (ölçüm, v21)

* Düşman canı `1 + 0,9 × kademe`, kademe 5'te tıkanıyordu (6.-10. derinlik aynı); eşya hasarı `1 + 0,6 × kademe`, üstüne
  tılsımlar (ongun başına +%15). Beklenen oyuncu gücü 9. derinlikte ~10 kat, düşman canı 5,5 kat: derine indikçe oyun
  KOLAYLAŞIYORDU (tipik silahla ortanca 2-3 vuruş).
* 1. derinlikte Erlik Tazısı 30 can / 10 hasar: başlangıç kılıcıyla 3 vuruş, oyuncu 10 darbede ölür. Bosslar 16-31 sn.
* v20'de SnH gerçek tempoya geçince ağır / sırık silahlar hafiflerin üstüne çıktı (Ulu Kılıç 81, Kargı 73, Alp 46, İkiz 49).

### Yeni model (`data/zorluk.json`)

* **Tabanlar** (`world.json` hp / dmg) artık 1. derinlik değeri ve role göre: sürü / uçan 30-48 can, kurt / pusucu 55-62,
  büyücü / okçu 50-65, taş balbal / kalkanlı / kabuklu 85-110, atlı 100-115, dev 110-185; vuruş 11-27. Başlangıç Alp
  Kılıcıyla sıradan düşman 4-7 vuruş, ağırlar 8-15.
* **Derinlik çarpanları** beklenen oyuncu gücünden çıkarıldı (derinlik başına ~2,5 tılsım: %60 Kurt, %25 Ayı, %15 Kartal; o
  kademenin Nadir silahı): can `[1; 1,75; 2,3; 3,2; 4,5; 6,2; 8; 10,3; 13; 16]`, hasar `[1; 1,27; 1,6; 2,04; 2,6; 3,3; 4,2;
  5,3; 6,8; 8]`. Tipik donanımla vuruş sayısı 5 → 8'e yavaşça artar, başlangıç silahıyla 5 → 117'ye fırlar: güç bulduğun
  eşyadan ve tılsımdan gelir. Seçkin: can ×3, hasar ×1,3 (tipik donanımla 13-19 vuruş).
* **Eşya**: kademe = derinlik - 1 (artık 8'e kadar; malzeme / nadirlik ağırlıkları 0-5 tablosundan), hasar çarpanı
  `[1; 1,3; 1,65; 2,05; 2,5; 3; 3,5; 4; 4,6]`, nadirlik hasarı Sıradan / Nadir / Destansı / Efsanevi ×1 / 1,08 / 1,16 / 1,25
  (`ItemGen.dmg_for`). Teçhizat gücü, süreğen hasar (`Zorluk.dot_k`: kademe × en yüksek ongun), duvar çarpması, patlama
  niteliği ve kalkan darbesi aynı ölçekle.
* **Saldırganlık**: saldırı beklemesi derinlikle ×1,15 → ×1,64 hızlı söner (`Enemy._aggr`), hazırlık en çok %15 kısalır
  (uyarı okunur kalır). Fark eden yaratık 180 px içindekileri uyandırır (`Enemy._set_aggro`); biri hazırlığa girince
  oyuncunun çevresindeki öbürleri aynı kareye yığılmaz (en az ~0,3 sn ara) ama uzun bekleyenler sırayı kapar
  (`Enemy._pack_beat`). Fark etme 230 → 260 px, bırakma 460 → 520 px.
* **Yoğunluk**: düşman arası boşluk derinlikle 0-4 karo azalır, 2.+ derinlikte ikili grup olasılığı %10-45, bölüm başına
  seçkin 1 → 3 (aralarında 40 karo).
* **Bosslar** kendi derinliklerinde (`Game.BOSS_AFTER`); canları `zorluk.json` "boss": Kara Börü Han 3300, Tepegöz 7000,
  Şahmeran 13000, Yelbegen 20000, Erlik Han 30000 (beklenen SnH ve %45 isabet payıyla 71-84 sn). Taban vuruş 17-20.
* **Şifa**: şişe %50 → %45, Şifa Otu %35 → %25, düşmandan ot %5 → %4, Kut Kapısı'nda can %25 → %15 (şişeler yine dolar).
* **Tek düğme**: `zorluk.json` "genel" (can / hasar / saldırganlık / şifa) bütün oyunu çevirir.

### Silah SnH dengesi (`items.json` dmg)

Hedef: hafif / tek el silahlar biraz önde; ağır silahlar formülde geride, ama bitiriş kritiği (`fc`), süper zırh, duruş
kırma ve alan vuruşu gerçek SnH'yi eşitler. Kademe 0, Demir, Sıradan, niteliksiz (`-- --denge` SILAH_SNH):

| Silah | hasar önce → sonra | SnH önce → sonra |
|---|---|---|
| Ulu Kılıç | 30 → 15,5 | 81 → 40 |
| Kargı | 13 → 8 | 73 → 44 |
| Erlik Tırpanı | 15 → 10 | 71 → 46 |
| Ay Palası | 6 → 4 | 69 → 48 |
| Yıldırım Kılıcı | 14 → 10 | 68 → 46 |
| Dağ Çekici | 36 → 22,5 | 67 → 43 |
| Böri Hançeri | 6 → 4,5 | 67 → 50 |
| Gürz | 26 → 20 | 56 → 46 |
| Alp Kılıcı | 10 → 10,5 | 46 → 50 |
| İkiz Bıçak | 5 → 5 | 49 → 51 |
| Yatağan | 7 → 9,5 | 40 → 51 |
| Kement | 7 → 11,5 | 25 → 42 |

Bütün yakın silahlar 40-52 aralığında (Savaş Baltası 21: fırlatma mekaniği formülde görünmez, 14 → 18).

### Ölçüm: önce / sonra (`-- --denge`, ortanca; "tipik" = o kademenin Nadir silahı + beklenen tılsım)

| Derinlik | başlangıç silahıyla vuruş | tipik vuruş | seçkin (tipik) | oyuncu kaç darbede ölür (beklenen can) | 100 canla |
|---|---|---|---|---|---|
| 1 | 4 → 5 | 3 → 5 | 4 → 13 | 9 → 6 | 9 → 6 |
| 2 | 7 → 9 | 2 → 5 | 4 → 13 | 8 → 6 | 6 → 5 |
| 3 | 15 → 18 | 3 → 7 | 7 → 19 | 6 → 5 | 4 → 4 |
| 4 | 20 → 25 | 3 → 6 | 7 → 18 | 6 → 5 | 3 → 3 |
| 5 | 22 → 32 | 2 → 6 | 7 → 19 | 7 → 6 | 3 → 3 |
| 6 | 26 → 44 | 2 → 6 | 6 → 19 | 7 → 6 | 3 → 2 |
| 7 | 45 → 63 | 3 → 7 | 5 → 16 | 7 → 5 | 2 → 2 |
| 8 | 45 → 80 | 3 → 7 | 4 → 16 | 9 → 5 | 2 → 1 |
| 9 | 29 → 117 | 2 → 8 | 4 → 14 | 10 → 5 | 2 → 1 |

| Boss (derinlik) | can önce → sonra | savaş süresi önce → sonra | oyuncu kaç darbede ölür |
|---|---|---|---|
| Kara Börü Han (2) | 1890 → 3300 | 31 → 84 sn | 5 → 6 |
| Tepegöz (4) | 3280 → 7000 | 23 → 80 sn | 4 → 5 |
| Şahmeran (6) | 4675 → 13000 | 18 → 78 sn | 4 → 6 |
| Yelbegen (8) | 5500 → 20000 | 16 → 71 sn | 5 → 5 |
| Erlik Han (10) | 7150 → 30000 | 17 → 76 sn | 8 → 6 |

Bot (`--otomatik`, 16000 kare ≈ 105 sn; eski bot canı 40'ın altına inince doldurur, başlangıç donanımı): önce hiçbir
derinlikte ölmedi (9. derinlikte 229 hasar); sonra 7. ve 9. derinlikte öldü (100+ vuruşlar doldurmayı atlar), 3. / 5.
derinlikte 155 / 227 hasar. Yeni ölçüm kipi `--bot_gercek`: doldurma yok, can %35'in altında şişe içer, ölünce aynı
derinlikten yeniden başlar; derinliğe uygun beklenen donanım (o kademenin Nadir Alp Kılıcı + beklenen tılsım ve can); yakındaki
uyanık düşmanla durup dövüşür, hazırlıktakinden yarı yarıya yuvarlanır. 9. derinlikte 105 sn'de 1041 hasar (azami canın 1,45
katı, 3 şişe), 3. derinlikte 126; önceki dengeyle aynı kip 9. derinlikte 882 hasar.

### Kut Mühürleri (Dead Cells "Boss Cell" karşılığı)

Erlik Han'ı yenmek bir sonraki mührü açar (`Zorluk.on_final_boss`, `Game.meta.muhur_acik`); açılan mühür bir sonraki koşuda
takılı gelir. Ayarlar > "Kut Mührü (yeni koşu)" ile açılmışlar arasında seçilir (`Game.meta.muhur`; koşu başında
`Game.run.muhur`). HUD sağ üstte "N. mühür".

| Mühür | can / hasar | saldırganlık | ek | şişe / şifa | öfkeli |
|---|---|---|---|---|---|
| 0 Mühürsüz | ×1 / ×1 | ×1 | - | - | - |
| 1 | ×1,1 / ×1,1 | ×1,1 | +1 yoğunluk | - | - |
| 2 | ×1,2 / ×1,2 | ×1,18 | +1 seçkin | -1 / ×0,85 | - |
| 3 | ×1,35 / ×1,3 | ×1,26 | +2 yoğunluk | -1 / ×0,75 | %15 |
| 4 | ×1,5 / ×1,42 | ×1,34 | +2 seçkin | -1 / ×0,6 | %25 |
| 5 | ×1,65 / ×1,55 | ×1,42 | +3 yoğunluk | -2 (en az 1) / ×0,5 | %35 |

**Öfkeli** yaratık (3. mühürden): can ×1,3, hasar ×1,15, hız ×1,2, hazırlık ×1,2 hızlı, saldırganlık ×1,25; koyu kızıl ton,
biraz iri, kor ışığı, can çubuğu turuncu.

### Düşman can çubuğu (`scripts/core/EnemyBar.gd`)

Başın üstünde küçük bir mürekkep fırçası (stil v2; `InkUI` "stroke" dokusu, doğrusal süzgeç; v1'de düz dikdörtgen). Tam canda
görünmez; hasar alınca hemen belirir, son vuruştan 3,5 sn sonra (oyuncunun yakınındaki uyanık düşmanda en çok 9 sn) söner.
Katmanlar: gölge + iki kat mürekkep zemin → koyu kızıl oluk → gecikmeli **hasar parçası** (açık kemik rengi; art arda vuruşlar
tek parçada birikir, 0,45 sn bekler, sonra erir) → kızıl dolgu, üst kıl parıltısı, fırça ucu lekesi; isabette kısa beyaz flaş.
Altında **duruş çizgisi**: ağır yaratıkta biriken duruş hasarı (altın), hafifte diretme anında altın kıl ve çerçeve; duruş
kırılınca turuncu titreyen çerçeve + üç çatlak. Solda **seçkin yıldızı** (çubuk görünürken baş üstü yıldızı gizlenir) ve
kalkanlılarda kalan siper tırnakları; sağda küçük **durum simgeleri** (yanma, don / ayaz yükü, zehir, kanama, unsur damgası,
nazar; yük noktalarıyla). Çubuk görünürken `StatusOverlay` kendi simgelerini çizmez (Kut Alma mührü çubuğun üstüne çıkar).
Boy yaratık boyuyla 26-62 birim; sayı yazmaz (hızlı kombolarda kalabalık etmesin). Seçkin: daha kalın, altın kıl, kızıl-mor
dolgu; öfkeli: turuncu dolgu.

**Boss çubuğu** (`InkHUD.boss_bar`): ekranın altında, yuvaların ve F / R / G halkalarının üstünde; 330 birimlik kızıl fırça,
gecikmeli hasar parçası (0,6 sn), evre çentikleri (%66 / %33; geçilen evrenin altında kızıl mühür), ad + lakap (`world.json`
"sub"), koçboynuzu uçlar, sersem / duruş kırık uyarısı.

### Test

* `-- --denge` (`tools/tests/denge_testi.gd`): silah SnH tablosu, derinlik × düşman türü (can, vuruş, başlangıç / tipik
  silahla vuruş sayısı ve süre, oyuncunun kaç darbede öldüğü), seçkin, bosslar, OZET. `--denge_muhur=N` mührü uygular.
  Zorluk.gd yoksa eski formülleri kullanır (önce / sonra aynı betikle).
* `-- --denge --denge_cekim=<mutlak klasör> --pencere=1920x1080 [--derinlik=N | --boss=tepegoz]` (headless değil): tek
  düşman, grup (yanma, zehir + duruş, kanama, don + öfkeli, kalkanlı + duruş kırık), seçkin ve boss çubuğu çekimleri.
* `-- --otomatik [--bot_gercek] --derinlik=N`: `[otomatik] can=.. hasar=.. dolum=.. şişe=.. ölüm=..`, `BOLUM_SONU` / `OLUM`.



## v21: Yıldırım Hamlesi düzeltmesi

Yıldırım Kılıcı tam şarjlı hamlesinde (basılı tutma ≥ 0,6 sn) gökten inen yıldırım artık oyuncunun durduğu yere değil, hamlenin deldiği her düşmanın tepesine iner (`Player._melee_hits`, `atk["thunder"]`). İlk düşmana tam güç (0,85), sonrakilere hafif (0,55) şimşek; tam şarjlı vuruş ×1,3 hasar ve 0,45 sn sersemletme. Bırakışta yalnızca kılıçtan kısa bir kıvılcım ve uzak gürleme. Test: `-- --dovus --boss --yildirim` (şimşek konumu ↔ düşman uzaklığı).


## v22: kontrol oyuncuda

Geri bildirim (oynayarak): "Kombo yaparken bir şey oluyor, kendi kendine saldırı atıyor; oynayan ben değilim gibi.
Komboya başlayınca vurduğum yön önemli olmuyor, düşmanı takip ediyor. Silah mürekkep izleri biraz ince olsun. Düşmana
vurunca çıkan efekt biraz sade / küçük olsun; çok hızlı kombolarda efektlerden kimse görünmüyor."

### Ölçüm: vuruş nedeni günlüğü (`Player.slog`, `-- --dovus --boss --kontrol`)

Oyuncunun her savuruşu ve basışsız her vuruş / dönüş / hamle nedeniyle kaydedilir (`log_on`): `basis` (taze basıştan;
basıştan bu yana oyun zamanı, vuruş donması sayılmaz), `gec_arabellek` (temastan önce yapılan basış 0,22 sn'den, kilitteki
basış 0,35 sn'den geç çıktı), `basissiz`, `yanki_eko`, `kam_eko`, `cark_uzatma` (basılı tutulmadan uzayan çark),
`oto_donus`, `oto_hamle` (düşmana doğru uzayan adım), `agir` (basılı tutma süresiyle). Test 3 düşmanlı arenada gerçekçi
desenler oynatır: düşünerek basma (iki basışlık zincir + 350-500 ms bekleme), 12 Hz ezme, hazırlıkta erken basış, son anda
basış, "biraz uzun" basış (200-283 ms), isabetin hemen ardından ritimli basış (Kut Yankısı), Kam unsuru (her vuruşta
tetiklenir), yalnızca arkada düşman, zincirin ortasında ters yön, menzilin biraz dışındaki düşman, Pala ezme, arkadaki
düşmana yay. Sonda `KONTROL ... basılmamış=N` satırı.

| Kaynak (önce) | Kanıt (aynı test, düzeltmeden önce) |
|---|---|
| **Kut Yankısı kesiği** — isabetin ardından basılan vuruşun 70 ms sonra (usulde iki kez) kendiliğinden gelen ikinci, altın savuruşu: ayrı iz, savuruş sesi, gövde hayaleti, kutudaki herkese vuruş, ek duraklama | 40 kendiliğinden vuruş (yalnızca ritimli değil; ezmede, tık-tık'ta da) |
| **Kam unsuru ruh kurdu yankısı** — vuruştan 0,16 sn sonra hayalet pençe: süpürülen fırça yayı + `savur_ruh` sesi | 6 savuruşta 18 gecikmeli pençe |
| **Bekleme bitirişi** — zincirden sonra 0,28-0,95 sn bekleyip basınca kendiliğinden başka hamle (Alp Çaprazı, Şimşek Çekişi ileri atılış, Dağ Devirici sıçrayıp çakma), ağır çekim + parlama | düşünerek basmada 9/9 beklemede |
| **Uzun ara bellek** — saldırı basışı 0,3 sn saklanıp savuruş sürerken hiç erimiyordu: hazırlıkta basılan tuş toparlanmada yeni savuruş çıkarıyordu | ezmeden sonra 257 / 448 ms; erken basış Gürz 353-370 ms, Dağ Çekici 506-531 ms, Pala 330 ms sonra |
| **Ağır saldırı eşiği** 0,2 sn — 250-283 ms'lik basış ağır silahta şarja dönüyordu | Dağ Çekici 3/4 |
| **Pala çark tutuşu** — ezerken yeni basış çarkı 1,2 sn'ye uzatıyordu | 2 uzatma |
| **Hedef yardımı** (`_assist_face`, `assist_turn`) — önde kimse yokken arkadakine dönme, zincirin her adımında | 6 kendiliğinden dönüş (arkadaki düşmana Alp / İkiz Bıçak / Kurt Pençeleri, ezerken ve yankı ritminde İkiz Bıçak, yay) |
| **Düşmana kayan adım** (`assist_reach`) — vuruş adımı menzil dışındaki düşmana 6-38 px uzuyordu | adım 12 → 23 px |
| **Kuyruktaki basışın yönü** — savuruş basış anındaki değil, çıktığı andaki yön tuşunu okuyordu | zincirde sola basınca yön 1 kaldı |
| Okçuluk "çabuk atış" — gerilirken saldırı tuşu oku kendiliğinden fırlatıyordu; yay basışı 0,45 sn saklanıyordu | — |

Sonuç: önce `basış=184 savuruş=112 basılmamış=72 (geç 3, kendiliğinden 60, alt_hamle 9) oto_dönüş=6 oto_hamle=3
istenmeyen_ağır=3` → sonra `basılmamış=0 oto_dönüş=0 oto_hamle=0 istenmeyen_ağır=0`. TAKILMA=0.

### Düzeltmeler

* **Kut Yankısı** (`V19`): ayrı gecikmeli kesik kalktı (`_yk_echo`, `_yk_echo_strike`, `_yk_echo_trail` silindi). Yankılı
  vuruşun kendisi `yk_mult + yk_echo × n` (×1,65; usulde ×2,0) vurur — toplam hasar aynı; görseli savuruşun kendi izinin
  altın mürekkebe dönmesi (`InkTrail.setup`, palet 9). Her yankıda "YANKI" yazısı ve gövde hayaleti yok; Kut Mührü aynı.
* **Kam yankısı** (`Unsur._kam_echo`): oyuncunun vuruşuyla aynı anda, yalnızca düşmanın üstünde küçük ruh pençesi (fırça
  yayı ve savuruş sesi yok, itme yok). Yıldırım unsuru zaten düşmanın tepesine iner; şimşek tek kanal, sıçrantısı ve
  sarsıntısı küçüldü. Od tutuşması, Kam damgası efektleri küçüldü.
* **Bekleme bitirişi kaldırıldı** (`PAUSE_WINDOW`, `_pause_ready_fx`): hamle zamanlamayla değişmez; beklemeden sonraki
  basış yeni zincir açar. `COMBOS` "pause" kayıtları kullanılmıyor.
* **Ara bellek** (`FLOW`): savuruş yokken / toparlanmada 0,12 sn (eski 0,3). Savuruş sürerken basış yalnızca son anda
  kuyruğa girer: zincir noktasına `buf_melee_late` = 0,16 sn kala ya da temastan sonra (kilitte; isabeti görüp basmak,
  Kut Yankısı zamanlaması). Hazırlıkta / süpürmede yapılan erken basış yok sayılır; kuyrukta en çok bir savuruş durur.
  Yuvarlanırken basış erimez (kaçış saldırısı). İkincil ara bellek 0,2 → 0,15 sn; yay basışı 0,45 → 0,2 sn
  (yuvarlanırken erimez). Dönüş Kesiği penceresi yuvarlanma bitiminden 0,32 → 0,18 sn.
* **Ağır saldırı** yalnızca gerçekten basılı tutunca: `heavy_hold` 0,2 → 0,3 sn (basıştan).
* **Çark tutuşu / gürz şarjı** yalnızca savuruşu başlatan basış hâlâ basılıysa (ezerken yeni basış uzatmaz).
* **Rüzgâr Kılıcı yel bıçağı** sayacı savuruş başına bir kez artar (üç düşmana değen tek savuruş bıçağı atmasın).

### Yön oyuncunun

* `_assist_face` ve `assist_turn` / `assist_reach` kalktı. Savuruş: yön tuşu basılıysa o yöne; değilse basış anındaki yöne
  (kuyruktan çıkan basış `_press_dir`); o da yoksa baktığı yöne. Arkadaki düşmana kendiliğinden dönme yok.
* Vuruş adımı (`_strike_step`) düşmana doğru uzamaz (taban 7 / 9 px + adımın dash payı); yalnızca dibindeki düşmanın içinden
  geçmemek için kısalır.
* Kut Alma (infaz) hedefi yalnızca baktığın yönde; Kurt Pençeleri hava sıçrayışı yalnızca öndeki düşmana, dönmeden.
* Yay: dikey nişan yardımı sürer (nişan, dönme değil); önde kimse yokken arkadakine dönme (`_turn_to_rear`) kalktı.
  Gerilirken saldırı tuşu gerilmeyi bırakır, ok kendiliğinden çıkmaz.

### İzler bir tık ince (`InkTrail.THIN`)

Genişlik (`w_frac`, `path_w`, `min_w`) sınıfa göre: hançer, kırbaç ×0,80 · kılıç, mızrak, uzun sap ×0,82 · ağır ×0,85 (ağır
silah görece kalın kalır). Örnek: kılıç hilali bıçak boyunun %62'si → %51; ağır %105 → %89; hançer yol yarı genişliği 3,4
→ 2,7; saplama 3,0 → 2,5; en az genişlik 4 → 3,3. Kendiliğinden süpürülen yaylar (`auto_arc`) da aynı oranda.

### Vuruş efektleri sade

* **Tekrar eden vuruşta küçük efekt** (`Player.V22_FX`, `FX.hit_k` / `FX.in_hit`): aynı düşmana 0,5 sn içinde gelen
  sıradan vuruş efektin %50'si (aynı savuruşun 2., 3. düşmanı ×0,75). İlk vuruş, zincir bitirişi, ağır, kesin kritik ve
  infaz tam efekt. Hafif vuruşta yalnızca küçük kıvılcım (halka, silaha özgü ek efekt, kıvılcım parçacıkları yok),
  InkFX sıçrantısı en hafif kademe ve %55'e küçük, kan ×0,35, darbe çizgisi yok, sayı %85. Enemy.gd'ye dokunulmadı:
  ayar efekt kütüphanesinde (FX, InkFX, Blood).
* **InkFX**: sıçrantı tabanı 22 → 19, kademe büyümesi 0,28 → 0,24; küt darbe yıldızı / halkası ×1,35 / ×1,9 → ×1,15 / ×1,6,
  koyu damla lekesi yalnızca büyük vuruşta; kritik damgası 44 / 30 / 66 → 36 / 26 / 56 ve daha kısa. Zincir bitirişi
  sıçrantısı 1,25 → 1,05 (+ ağırlık), halkası 22 → 16 (+ ağırlık). Yankı işareti halkası 9 → 6,5.
* **Kademe 1 vuruşlar** artık yalnızca darbe sıçrantısı (halka ve silah efekti kademe 2'de); kıvılcım sayısı −2.
* **Kan** her vuruşta ×0,6 (hızlı ardışık ×0,35); ölüm fışkırması aynı. Düşmanın büyük vuruştaki 5 darbe çizgisi %40'a
  seyreldi.
* **Hasar sayıları**: aynı düşmanın üstünde (24 px) doğuşundan 0,3 sn içinde çıkan kritik olmayan sayılar tek sayıda
  toplanır; açılış büyümesi 1,35 → 1,15 (kritik 2,0 → 1,75); sıradan sayı 0,75 → 0,55 sn yaşar.
* **Darbe flaşı** (`SpriteAnim.set_flash`): ilk flaş 0,45 (tam beyaz değil), 0,4 sn içinde yeniden başlayan flaş bir
  öncekinin %55'i (en az %20). Vuruş donmasında gerçek zamanda uzayan tam beyaz flaş hızlı kombolarda düşmanları beyaz
  siluete çeviriyordu.
* **Hayaletler** (`FX.ghost`): aynı sprite'tan oyuncuda 40 ms, düşmanda 120 ms içinde ikinci hayalet yok; mürekkep stilinde
  oyuncu ×0,6, düşman ×0,4 saydamlık (geri itilen düşmanın her 3 karede bıraktığı toplamalı hayaletler üst üste binip
  bembeyaz siluet oluyordu).
* **Darbe karesi** (`ImpactFrame`): yalnızca tam şarjlı ağır vuruşta (kritikte, bitirişte ve öldürüşte yok); bekleme 0,7 →
  1,2 sn. İnfaz ve seçkin / boss ölümü kendi karesini verir.
* **Yazılar**: kombo kademesi yazısı küçük (10 + kademe → 7 + kademe) ve daha yukarıda, halka yalnızca 3. kademeden;
  "USUL xN" yalnızca 4'ün katlarında, usul halkası 18 → 12.
* **Vuruş donması**: kombo uzadıkça duraklama artışı %35 → %10; aynı düşmana hızlı ardışık sıradan vuruş ×0,6; kombo
  kademesi ağır çekimi kalktı. 3 düşmana 12 Hz ezmede (1,5 sn) donmuş kare, bu üç değişiklikten önce → sonra: İkiz Bıçak
  533 → 200-283 ms, Alp 416 → 366-400, Dağ Çekici 466 → 333-433 (Kargı ~550-580 değişmedi: çoğu düşmanın kendi havaya
  atılma / iniş duraklamaları, Enemy.gd). Eski yankı kesiği her yankıda ayrıca 18 ms donduruyordu.

### Ölçüm (sonra)

`--dovus --boss` (TAKILMA=0; önce 1: tempo/ulu_kilic): basış→temas aynı (ikiz bıçak 100, Alp 133, kargı 150-167, ulu
kılıç 400, Dağ Çekici 350 ms; ±1 kare). Savuruş içi basış: son anda yapılan karşılandı (İkiz 4/4, Alp 4/4, Kargı 4/4, Ulu
1/1, Dağ 1/1), erken basış yok sayıldı (Kargı 1/1, Ulu 4/4, Dağ 4/4). Son anda basıştan savuruşa 67-83 ms. 20 basışlık seri
basışta savuruş: İkiz 13, Alp 9, Kargı 8, Ulu 4, Dağ 4 (önce 12 / 8 / 10 / 4 / 5). Ağır şarj basılı tutunca 317 ms'de başlar
(önce 233-250); 100 ms dokunuş ağır değil. Kut Yankısı serisi üç silahta da sürüyor (İkiz / Alp / Dağ Çekici Kut Mührü 1).
Hedef yardımı testleri: arkadaki 26 px ve menzil + 22 px düşman artık ıska (yön 1), dibindeki isabet. İptaller aynı
(hazırlıkta yuvarlanma 1 kare, yuvarlanmadan Dönüş Kesiği aynı kare, ardışık yuvarlanma 100 ms, vuruşta yay 117 ms).
`--yay --boss` (TAKILMA=0): gerilirken saldırı → saldırı aynı kare, kendiliğinden ok yok; yuvarlanırken yay basışı
yuvarlanma bitince ok (267 ms); 10 Hz seri basışta Od / Tufan 6 / 4 → 5 / 3 ok (bekleme sırasındaki basış artık 0,2 sn
saklanıyor). `--unsur`, `--bengu`, `--mekanik`, `--otomatik --derinlik=1/5`: betik hatası 0; `--piksel_tara` 0.

Çekim: `-- --dovus --boss --klip22 --pencere=1920x1080 --anlik=<klasör>` (headless değil): üç düşmana (kurt, arçura,
kurgan bekçisi) hızlı kombo, savuruşun ortasından 8-80. karelerde anlık görüntü (Alp Kılıcı, İkiz Bıçak, Dağ Çekici).


## v23: 3B düzlemde savuruş

Geri bildirim: "Kılıç savuruş animasyonları direkt daire şeklinde, çok basit görünüyor. Dead Cells'te kılıç 3B bir düzlemde
hareket ettiği için izler nizami değil, farklı şekillerde çıkıyor ve çok doğal duruyor." Ölçünce: v22'de bıçak ucu her
savuruşta elin çevresinde ekran düzleminde dönüyordu, iz hep aynı daire yayıydı; yatay savuruşlar "k 0,22 + tek karede açı
sıçraması" hilesiyle kameraya dönüyor, iz kırık bir V çiziyordu (teber, yatağan).

**Referans (Dead Cells):** iz, perspektifte görülen bir elips yayı gibi okunan DOLU HİLAL: bıçağın şimdi bulunduğu ön uçta
kalın, parlak iç çekirdekli, sivri kıvrık uçlu; kuyruğa doğru kıl inceliğine iner; iç ve dış kenar farklı eğri (hilal
kalınlığı yay boyunca değişir). Kombonun her adımı başka düzlemde (çapraz iniş, yükseliş, yassı geniş yatay, dik "C" baş
üstü); silah derinlik ekseninden geçerken kısalıp uzar (önkısalma); iz 2-4 karede söner.

### Savuruş düzlemi (`Player.PLANES`, `_plane_at`, `_plane_proj`, `_pose_points`)

SWINGS anahtarları (a1 üst kol, a2 dirsek, w bilek) artık savuruşun eğik 3B düzleminin İÇİNDEKİ açılar. Düzlem ekrana dik
izdüşümle çizilir: ekrandaki büyük ekseni `phi` yönünde (kol açısı kuralı: 0 aşağı, 90 ileri, 180 yukarı; derece) korunur,
ona dik bileşen `r` oranında kısalır (r = eğim açısının kosinüsü; 1 eski ekran düzlemi). Böylece:

* bıçak ucu ve kabza aynı düzlemde ama farklı yarıçapta döner: ikisi ayrı elips çizer, iz hilalinin iç ve dış kenarı farklı eğri;
* bıçak büyük eksenden uzaklaştıkça (kameraya / içeri dönünce) kısalır; silah sprite'ının boyu izdüşüm boyuyla ölçeklenir
  (önkısalma), `roll` (bilek, bıçak ekseni çevresinde) sprite enini cos(roll) ile inceltip yüz değiştirir;
* kol (omuz → dirsek → el) aynı düzlemde ama `ARM_PLANE` = 0,55 oranında kısalarak izdüşer: el de eşleşen, daha dolgun bir
  elipste gezer; gövde ve bıçak aynı hareketi anlatır;
* çarklarda (`spin`, `spin_2h`, `helicopter`; `"b": true`) bıçak düzlemin arka yarısına geçince (derinlik < -0,2,
  histerezisli) gövdenin ARKASINDA çizilir: silah gövdeyi dolanır;
* düzlem anahtarları savuruş içinde değişebilir (`"p": [[k, phi, r, roll], ...]`): X kesikler iki düzlem kullanır, takipte
  bilek döner. Hazırlığın ilk anahtarına dek önceki savuruşun düzleminden (zincirde) ya da ekran düzleminden geçilir;
  toparlanmada ekrana dönülür (zincir akışı v18'deki gibi kesintisiz);
* her savuruşa küçük rastgele sapma (`PLANE_JIT`: phi ±4°, r ±0,04; oyuncunun kendi `_plane_rng`'si, oyunun ortak
  rastgeleliğine dokunmaz): art arda aynı savuruş birebir aynı görünmez ama okunur kalır;
* sınıf çarpanı (`CLASS_PLANE`): hançer r ×1,12 (daha dik küçük fiskeler), uzun sap ×0,86, mızrak ×0,9, kırbaç ×0,95.

Temas anında bıçak düzlemin büyük eksenine yakın tutuldu (ileri yön çoğu düzlemde kısalmaz): görünen erim eskisi gibi, vuruş
kutuları ve zamanlama değişmedi. Dik "C" ezmelerde ileri erim ~%70-75'e iner (düzlemin doğası); kutuları uzun dikey
olduğundan isabet bıçağın görünen yayıyla örtüşür.

| Sınıf / silah | Zincir | Düzlemler (phi°, r) |
|---|---|---|
| Kılıç (Alp) | çapraz iniş → çapraz yükseliş → adımlı baş üstü | `diag_down` 62°/0,42 (büyük eksen öne-aşağı çapraz: baş üstünden geçen kısım içeri kısalır) → `diag_up` 118°/0,42 (alt-arkadan öne-yukarı) → `step_down` 34°/0,6 dik uzun "C" |
| Kılıç (varsayılan, Ruh, Pala, Yatağan) | yatay → iniş → … | `horiz` 96°/0,3 yassı geniş hilal (bıçak önden kameraya dönerek geçer), `down` 58°/0,5, `back` 80°/0,38 baş üstünden ters el, `reverse_grip` 62°/0,5 + bilek, `iai` 100°/0,34, `backstep` 100°/0,34, `rise` 138°/0,5 |
| Hançer | fiske → ters fiske → tırmık → X delip geçiş | `dual_l` 52°/0,5 küçük dik iniş, `dual_r` 128°/0,48 ters el yükseliş (bilek döner), `rake` 34° → 56° (iki tırmık iki düzlem), `cross_dash` 56° → 124° |
| Ağır | ezme → yel değirmeni → çakma | `heavy` 32°/0,62, `overhead_2h` 30°/0,6, `slam(_2h)` 26-28°/0,62 dik "C"; `windmill` baş üstü tur 60-72°/0,55-0,6, vuruş 96°/0,38 (gövdenin önünden yassı geniş elips); `uppercut_2h` 134°/0,48 |
| Mızrak | saplama → alçak saplama → yükseliş | saplamalar 76-90°/0,36-0,4 (kol yassı elipste öne fırlar: hafif yaylı çizgi), `pole_rise` 128°/0,4 geniş yükselen hilal |
| Kırbaç | şaklama → yan şaklama / alçak süpürme | `whip_crack` 55°/0,55 eğik baş üstü, `whip_side` 100°/0,38 yassı kurdele; yol izi (kıvrık S kurdele) korunur |
| Uzun sap | süpürme → biçme → baş üstü | `pole_sweep` 92°/0,26 ve `sweep_low` 82°/0,28 çok yassı geniş süpürmeler, `reap` 86°/0,3 (önden geriye çekiş), `twirl` 70°/0,48 eliptik çevrim |
| Çarklar | – | `spin` / `spin_2h` / `helicopter` 90°/0,3: gövdenin çevresinde tam elips, arka yarıda silah gövdenin arkasında |

Yatay savuruşlardaki (horiz, back, sweep_low, reverse_grip, pole_sweep, reap, backstep) tek karede açı sıçraması ve k 0,22
anahtarları kalktı; bıçak düzlemde sürekli döner (zaman anahtarları, `ck`, `hit` aynı). Helikopterin k 0,6'sı da düzleme bırakıldı.

### Hilal izi (`InkTrail._ribbon`, `shaders/ink_brush.gdshader`)

* **Geometri:** dış kenar = izdüşen bıçak ucunun yolu; iç kenar = uç − bıçak yönü × genişlik (kabza başka elipste döndüğünden
  ayrı eğri). Genişlik = v22 taban (`w_frac` × bıçak; `THIN` aynen) × hilal profili: kuyrukta `CRESCENT_TAIL` 0,12'den yay
  boyunca q^1,1 ile öne doğru `CRESCENT_LEAD`'e (kılıç 1,7, hançer 1,6, ağır 1,4, uzun sap 2,1, mızrak 1,7) çıkar; en
  dolgun yer bıçağın hemen arkası, en öndeki %12'lik yayda sivri uca iner; uç, bıçağın kabza çevresindeki son dönüşünü kısa
  bir yayla (`HOOK_K`) sürdüren **kıvrık kanca** ile kapanır (bıçak durunca kanca söner).
* **Önkısalma:** bıçak kameraya dönünce izdüşen bıçak kısalır; hilalin eni bunun ancak %40'ı kadar incelir
  (`FORESHORT_KEEP` 0,6, izdeki en uzun izdüşüme göre): hilal kameraya dönen kısımda kopmaz.
* **Yavaş örnekler** (takip / oturma) eskisinden çok daha ince (baskı 0,55 → 0,2): bıçak durunca uçta mürekkep topağı birikmez.
* **Ömür** (`LIFE`): kılıç 0,075 sn, hançer 0,06, ağır 0,095, uzun sap 0,085, mızrak 0,075, kırbaç 0,11, saplama 0,09
  (× ağırlık; bitirişte ×1,25): iz 2-4 karede söner (eski 0,2-0,32 sn); hızlı kombolarda düşmanı örtmez (v22 hedefi).
* **Gölgelendirici:** `er_delay` 0,3: erime (kenar yenmesi, kuru boşluklar, kıl tellerine ayrılma) yaşın ilk %30'unda
  başlamaz: hilal ilk karelerinde dolu, sonra hızla erir. `core_gain`: taze ön kısımda mürekkebin ortasından dış kenara
  açık-sıcak çekirdek bandı (parlak iç çekirdek); iç kenarda ince mürekkep konturu. Tazelik eşikleri kısa ömre göre
  genişledi. Kenar yumuşatma (fwidth) aynen; palet / sınıf / unsur katmanları (v20), Kut Yankısı altını (v22) aynen.
* **Hançer** artık uç yolu yerine küçük, eğik bir hilal (+ içte ince ikinci fırça); saplama ve kırbaç yol izinde kalır.
* Düşman / boss yayları (`auto_arc`) eski biçiminde (`er_delay` 0: hilal profili ve çekirdek yalnızca oyuncu izinde).
* `_sample_trail` ara örnek sayısı izdüşen uç yolunun ekran uzunluğunu da sayar (yassı elipste açı küçük, yol uzun);
  `_blade_local` artık önkısalmalı (uç = el + `_blade_local` × R görünen uç: darbe noktası, yer çarpması, Kızışma tülleri);
  unsur bıçak ışıması (`Unsur.weapon_glow`) da önkısalan bıçak boyunca.

### Ölçüm ve test

Zamanlama koduna (TEMPO, FLOW, ara bellekler, `ck` / `hit`, vuruş kutuları) dokunulmadı; düzlem yalnızca çizimi değiştirir.
`--dovus --boss` önce (3e97501) ve sonra üçer kez (gerçek zamanlı, `--fixed-fps 60`, `--fixed-fps 60 --tohum=7`; sonra üç koşu daha):
TAKILMA=0 (sonraki altı koşunun birinde v22 öncesinden bilinen `tempo/ulu_kilic` oynaması: zincirin son basışı bazen bir
savuruş daha açıyor, 1,5 sn'lik boşta denetiminde hâlâ toparlanmada; aynı test eski sürümde de oynak), `KONTROL ... basılmamış=0 oto_dönüş=0 oto_hamle=0 istenmeyen_ağır=0` hepsinde. Basış→temas (kare): hançer / düello / kılıç /
mızrak / kırbaç önce ve sonra aynı aralıkta (İkiz Bıçak 6/6/6 → 6/6/6, Yatağan 7 → 7, Alp 8-9 → 8-9, Kargı 9-10 → 9-10;
tempo tablosunda ±1). Ağır silahlarda test kendi içinde gürültülü (aynı sürümde art arda koşularda da 2-3 kare oynuyor: ağır
silahın basılı tutma bekleyişi, rastgele eşya nitelikleri; önce Dağ Çekici 21/24/24, Çivili Topuz 17-20, Bozgun 19-23), sonra
aynı aralıklarda (Dağ Çekici 21/21/24, Çivili Topuz 15-18, Bozgun 19-22). `--tohum=N` (`dovus_testi.gd`, yeni) ortak
rastgeleliği sabitler ama düşman / zaman kaynaklı oynama kalıyor. `--savurus`, `--unsur --boss` (HATA=0), `--otomatik
--derinlik=1`: betik hatası 0; `--piksel_tara` TOPLAM 0.

Kare şeridi: `-- --firca=w1,w2 --firca_kombo --anlik=<klasör> [--firca_bos] --pencere=1920x1080` (headless değil, Godot'ya
`--fixed-fps 60`): her silahta 3 vuruşluk zincir (her savuruşun son anında yeniden basılır), HER kare oyuncunun çevresinden
640×480 kırpılmış PNG.

## v23: tomar ekonomisi

Geri bildirim (v22 dengesini oynayarak): "Zorluk hâlâ çok kolay. Silahların taban hasarı çok yüksek; tomarlarla ve statlarla
güçlenmeliyiz. İyi silahlar daha seyrek düşsün. Tomar topladıkça silahın SnH'si artsın, yerdeki silahlar da SnH'yi buna göre
göstersin." · "Kritik biraz azalsın, çok fazla kritik var." · "Yan teçhizat E ve R olsun, öbür tuşlar çok uzak."

### Araştırma: Dead Cells "Scroll of Power" (deadcells.wiki.gg, Scrolls / Stats)

* Üç stat (Brutality kızıl, Tactics mor, Survival yeşil) koşu başında 1'dir; her tomar birini +1 yapar. Eşya bir ya da iki
  stat rengi taşır, **iki renkli eşya yüksek olanla** ölçeklenir; renksiz eşya en yüksek statla.
* Hasar: stat başına ~%15 (wiki: SnH x 1,15^(stat-1); 10 statta x3,5). Can: her tomar azami canı artırır; Survival en
  çok, getirisi azalan ikinci dereceden eğri.
* Tomar kaynakları: bölümdeki tomar kapları, düşman / seçkin düşüşleri, lanetli sandık; iki renkten seçtiren tomarlar
  (Assassin's / Minotaur's / Guardian's), 4 parça = 1 tomar.
* Silahın kendi seviyesi / niteliği (+, ++, S) önemli ama gücün çoğu tomardan gelir.
* Kaynak: https://deadcells.wiki.gg/wiki/Scrolls , https://deadcells.wiki.gg/wiki/Stats

### Bizim sürümümüz: Kut Tomarı (eski "tılsım")

Stat ekseni zaten vardı ve yeni bir sistem eklenmedi: **Bozkurt** (kızıl; yakın dövüş), **Kartal** (mavi; yay, fırlatma,
teçhizat), **Ayı** (yeşil; kalkan, dayanıklılık). Eşyaların `items.json` "ongun"u tek ya da iki renk; nadir eşya bazen ikinci
renk kazanır (v9). Değişen: tomarın etkisi, eşyanın taban gücü, kaynaklar ve gösterim.

* **Kaynaklar**: bölüm başına üç tomar (ikisi yolda, biri havadaki adada; aynı), **her boss bir tomar bırakır** (yeni,
  `Level._on_boss_died` → `drop_scroll`). W ile okunur; seçim kartı (`HUD._draw_tilsim`, "KUT TOMARI").
* **Hasar çarpanı** (`Zorluk.tomar_k`, `zorluk.json` "tomar.kazanc"): n. tomarın kazancı 1-6. tomar +%25, 7-12. +%20,
  13-18. +%15, sonrası +%10 (azalan getiri; Dead Cells'in üstel eğrisi yerine doğrusal-azalan, uçuşa geçmesin). Çarpan
  = 1 + kazançlar toplamı:

| stat | 0 | 3 | 6 | 9 | 12 | 15 | 18 | 21 | 24 |
|---|---|---|---|---|---|---|---|---|---|
| hasar | x1 | x1,75 | x2,5 | x3,1 | x3,7 | x4,15 | x4,6 | x4,9 | x5,2 |
| v22 (x1+0,15n) | x1 | x1,45 | x1,9 | x2,35 | x2,8 | x3,25 | x3,7 | x4,15 | x4,6 |

* **Can**: tomar başına azami canın %6'sı (Bozkurt, Kartal) / %15'i (Ayı) + okununca azami canın %10'u kadar iyileşme
  (`tomar.can`, `tomar.iyilesme`; aynı). Ayı seviye başına %3 hasar azaltma (en çok %30), Bozkurt seviye başına +%2
  saldırı hızı (v20; aynı).
* **Eşya taban gücü** (`zorluk.json` "esya"): bütün silah hasarı ve teçhizat gücü x0,7 (`esya.taban`); kademe çarpanı
  `[1; 1,3; 1,65; 2,05; 2,5; 3; 3,5; 4; 4,6]` → `[1; 1,06; 1,12; 1,18; 1,24; 1,3; 1,36; 1,42; 1,48]`. Dokuzuncu
  derinliğin silahı başlangıç silahından en çok %48 (+ nadirlik %8-25) güçlü; güç tomardan gelir. Süreğen hasar, duvar
  çarpması ve "Gürleyen" patlaması da taban x kademe x tomar statıyla (`Zorluk.dot_k`).
* **Beklenen oyuncu** (`Zorluk.beklenen_tomar`; denge testi ve `--bot_gercek` aynı modeli kullanır): derinlik başına 2,5
  tomar + geçilen her boss 1 tomar; %60 Bozkurt, %25 Ayı, %15 Kartal. 9. derinliğin başında 24 tomar (14 / 6 / 4), can 660.
* **Seçim kartı**: her stat için seviye, hasar çarpanı şimdi → sonra, "+%N bu renkte hasar", can artışı ve kuşanılan her
  eşyanın **SnH şimdi → sonra** değeri (stat geçici olarak artırılıp `ItemGen.dps_oyuncu` ile ölçülür; Bozkurt'un saldırı
  hızı da dahil). Okununca kısa mesaj: "Bozkurt +1 · Alp Kılıcı SnH 41 → 60".

### Düşüş tabloları (`items.json`; kademe = derinlik - 1, seçkin / hazine odası / boss bir kademe üstten çeker)

Nadirlik yüzdesi (Sıradan / Nadir / Destansı / Efsanevi; v22 kademe 0..5'ten sonra son sütunu kullanırdı):

| kademe | v22 | v23 |
|---|---|---|
| 0 | 60 / 30 / 9 / 1 | 72 / 24 / 3,6 / 0,4 |
| 1 | 44 / 36 / 16 / 4 | 64 / 29 / 6 / 1 |
| 2 | 32 / 38 / 24 / 6 | 56 / 33 / 9,5 / 1,5 |
| 3 | 24 / 38 / 30 / 8 | 49 / 35 / 13 / 3 |
| 4 | 18 / 38 / 34 / 10 | 43 / 37 / 16 / 4 |
| 5 | 14 / 36 / 38 / 12 | 38 / 38 / 19 / 5 |
| 6 | (14 / 36 / 38 / 12) | 34 / 38 / 22 / 6 |
| 7 | (14 / 36 / 38 / 12) | 31 / 38 / 24 / 7 |
| 8 | (14 / 36 / 38 / 12) | 28 / 38 / 26 / 8 |

Malzeme yüzdesi (seçme; tam tablo `items.json` "materials.weight", 9 sütun):

| kademe | Demir | Tunç | Gümüş | Altın / Kemik / Yeşim | Kara Taş | Od Taşı / Ayaz | Gök Demiri | Ruhani |
|---|---|---|---|---|---|---|---|---|
| 0 | 40 | 28 | 12 | 3 / 8 / 3 | 3 | 1 / 1 | 0 | 0 |
| 2 | 22 | 22 | 17 | 7 / 10 / 7 | 7 | 4 / 4 | 1 | 0,4 |
| 4 | 12 | 14 | 16 | 9 / 10 / 9 | 10 | 8 / 8 | 2,6 | 1,6 |
| 8 | 5 | 7 | 12 | 10 / 10 / 10 | 12 | 12 / 12 | 5 | 4 |

(v22 kademe 0: Demir 34, Gök Demiri 0,3; kademe 5'te Gök Demiri 6, Ruhani 5.) Sıradan düşmandan eşya %4 → %2,5;
boss eşyası kademe +2 → +1. Dükkân yok (altının harcandığı bir satıcı oyunda henüz yok; Demirci parşömen açma bedeli
Kut ile ve değişmedi). **v24:** artık var: Bezirgân Sartak (bkz. "v24: tüccar ve silah parşömenleri").

### Düşman eğrileri (`zorluk.json` "derinlik", "seckin", "boss")

* can `[1; 1,75; 2,3; 3,2; 4,5; 6,2; 8; 10,3; 13; 16]` → `[1,02; 1,66; 2,16; 2,64; 3,18; 3,84; 4,62; 5,4; 6; 7]`
  (eşya kademesi artık az ölçekler; eğri beklenen tomar gücünü izler).
* hasar `[1; 1,27; 1,6; 2,04; 2,6; 3,3; 4,2; 5,3; 6,8; 8]` → `[1; 1,27; 1,84; 2,25; 2,9; 3,95; 5,25; 6,45; 8,8; 10,4]`
  (tomarla gelen can artınca; tomarsız 100 canlı oyuncu 6. derinlikten sonra 1-2 darbede ölür).
* seçkin canı x3 → x2,6; boss canı Kara Börü Han 3300 → 2500, Tepegöz 7000 → 4400, Şahmeran 13000 → 6700, Yelbegen
  20000 → 8900, Erlik Han 30000 → 11800 (Albastı Ana 10000 → 5500).

### Ölçüm: önce / sonra (`-- --denge --denge_muhur=0`, ortanca sıradan düşman; "tipik" = o kademenin Nadir silahı)

"önce" v22 kodu ve aynı (genişletilmiş) test betiği. Önemli: v22'nin SnH / vuruş hesabı kritikleri yalnızca şans olarak
sayıyordu; gerçekte vuruşların ~%57'si kritikti (aşağıda), yani v22'de gerçek vuruş sayısı bu tablodakinin ~yarısı-üçte
ikisiydi. v23'te kritik nadir ve kart / test gerçek hasarla örtüşür (aşağıda), tablo gerçeğe yakın.

| d | tipik silah + tipik tomar | tipik silah, tomarsız | başlangıç silahı + tipik tomar | başlangıç silahı, tomarsız | oyuncu ölür (tipik can / 100 can) |
|---|---|---|---|---|---|
| 1 | 5 → 5 | 5 → 5 | 5 → 6 | 5 → 6 | 6 / 6 → 6 / 6 |
| 2 | 5 → 5 | 6 → 8 | 7 → 7 | 9 → 10 | 6 / 5 → 6 / 5 |
| 3 | 7 → 8 | 9 → 15 | 13 → 10 | 18 → 19 | 5 / 4 → 6 / 3 |
| 4 | 6 → 8 | 11 → 17 | 15 → 11 | 25 → 23 | 5 / 3 → 5 / 3 |
| 5 | 6 → 7 | 11 → 18 | 17 → 9 | 32 → 24 | 6 / 3 → 6 / 2 |
| 6 | 6 → 7 | 12 → 20 | 20 → 10 | 44 → 30 | 6 / 2 → 6 / 2 |
| 7 | 7 → 8 | 15 → 26 | 27 → 12 | 63 → 41 | 5 / 2 → 6 / 2 |
| 8 | 7 → 8 | 17 → 29 | 31 → 13 | 80 → 47 | 5 / 1 → 5 / 1 |
| 9 | 8 → 9 | 22 → 36 | 42 → 16 | 117 → 61 | 5 / 1 → 5 / 1 |

Okuma: tomar toplayan oyuncu için vuruş sayısı 5 → 9'a yavaş artar; **tomar atlamak artık eşya atlamaktan çok daha
ağır** (9. derinlikte tomarsız 36 vuruş, eski 22), iyi silahı kaçırmak ise eskisi kadar cezalandırmaz (başlangıç silahı +
tomar: 42 → 16). Seçkin (tipik) 13-20 vuruş. Bosslar (tipik, %45 isabet payı): 82 / 83 / 79 / 78 / 82 sn (v22 84 / 80 /
78 / 71 / 76); tomarsız 123 / 186 / 245 / 290 / 353 sn (v22 110 / 141 / 171 / 189 / 236).

Silah SnH (kademe 0, Demir, Sıradan, tomarsız; bitiriş, çok vuruş ve yer şoku artık dahil): 26-44 (Ulu Kılıç 43,6,
Gürz 42,5, Alp 41,3, İkiz Bıçak 35,6, Kargı 26,9, Kement 26,2; Savaş Baltası 13,2, fırlatma formülde görünmez).

### Saniyedeki hasar (kart, yerdeki silah, yuva, duraklatma)

* `ItemGen.dps_oyuncu(it)`: silahın SnH'si **oyuncunun tomar statı** (`Game.item_mult`), şans kritiği (silah + "İsabetli"
  + Ay Ata + Segrek; `ItemGen.krit_sans`, `Player._deal` aynı sayıyı kullanır) ve genel çarpanlarla (Erlik'in Gölgesi,
  Alp Er Tunga). Tomar okununca her yerde anında büyür. Sayılmayanlar: kombo sayacı (+%1,5 / vuruş), usul, Kızışma, Kut
  Yankısı, koşul kritikleri, düşmana göre çarpanlar (duruş kırılması x1,25, nazar, zırh kırığı, seçkin / boss nitelikleri).
* Yakın silahta SnH = tur hasarı / tur süresi (`ItemGen.zincir_hasar` / `zincir_sure`): adım çarpanları, bitiriş çarpanı,
  Alp'in üçüncü vuruşu (+%mech_v), çok vuruşlu savuruşun gerçek geçiş sayısı (temas ilk işaretten önceyse +1), çift
  vuruşun %70'lik ikincisi, gürz / çekiç yer şoku (%50); süre `Player.tempo_phases`'tan, zincir başı ilk hazırlıkla ve
  adım başına bir kare (60 Hz). v22 kartı bunları saymıyordu (önce: kukla ölçümünde gösterilen 50, ölçülen 88).
* Kart: "Saniyede hasar: N" + kuşanılan silaha göre **▲ +X (+%Y)** yeşil / **▼ -X (-%Y)** kızıl; altında "tomarsız N ·
  Bozkurt k tomar x m". Yerdeki silahların üstünde (260 px içinde, en yakını hariç; onun büyük kartı var) küçük etiket
  "SnH N ▲/▼" (`HUD._draw_ground_dps`). Yuva seçimi ve duraklatma ekranı da aynı sayıyı gösterir.
* Doğrulama (`-- --tomar --boss`, `tools/tests/tomar_testi.gd`): yere tomar düşürülür ve oyunun kendi yolundan okunur
  (`Main._on_scroll` → `_apply_scroll`), kartın sayısı durağan kuklaya sürekli zincirle 10 sn vurularak ölçülenle
  karşılaştırılır (kombo, usul, Kızışma, yankı, duruş kırılması her karede sıfırlanır; 12 sn'lik ölçümde 1-2 rastgele
  kritik ±%5 oynattığı için bu kipte silahın şans kritiği 0):

| silah | 0 tomar: kart / ölçülen | 3 tomar | 7 tomar |
|---|---|---|---|
| Alp Kılıcı | 39,6 / 39,5 (-%0,1) | 73,2 / 75,7 (+%3,5) | 120,8 / 123,6 (+%2,3) |
| İkiz Bıçak | 34,2 / 35,0 (+%2,5) | 62,7 / 64,4 (+%2,8) | 102,4 / 109,2 (+%6,7) |
| Ulu Kılıç | 42,6 / 42,2 (-%0,8) | 77,1 / 75,9 (-%1,6) | 124,3 / 124,8 (+%0,4) |
| Bozgun Kılıcı | 35,6 / 35,5 (-%0,2) | 64,4 / 62,6 (-%2,9) | 103,9 / 103,3 (-%0,6) |

  Sınır %7 (kare yuvarlaması ve geri itilen kuklanın ara sıra ıskalattığı geçiş). Kargı, Yatağan, Gürz, Yıldırım Kılıcı,
  Erlik Tırpanı yalnızca bilgi için ölçülür (koşul kritiğini kendisi doğurur ya da atılış / geri sıçrayış / basılı çark
  betikli kuklada zinciri değiştirir).

### Kritik (çok fazlaydı)

Ölçüm (`-- --tomar --boss --krit`: 27 yakın silah, saldırmayan ama yapay zekâsı ve durum süreleri işleyen kuklaya 10 sn zincir):

| | önce (v22) | sonra |
|---|---|---|
| kritik vuruş payı | **%56,9** (şans %4,9, koşul %49,2, kesin %2,8) | **%15,3** (şans %2,7, koşul %12,6) |
| silah ortancası / en yüksek | %72 / %100 | %21 / %35 |
| örnekler | Rüzgâr, Tulpar, Kement, Dağ Çekici %100; Pala, Gürz, Kor Çekici %94-97; Ulu Kılıç %72; Alp %38 | Savaş Baltası %35, Od Kamçısı %31, Rüzgâr %26, Gürz %23, Pala %21, Alp %3, Ulu %0 |

`--bot_gercek` (gerçek bölüm, yakındaki düşmanla dövüşen bot; önce d1 %50, d5 %44): sonra 9. derinlikte %36; bunun
yarısı botun 10 sn'de bir açtığı Bozkurt biçiminin bitiriş ısırıkları (`KRIT_KESIN diger`), geri kalanı karşı vuruş, Kut
Mührü, infaz ve yankılı bitiriş (beceri kritikleri); şans + koşul %6. (Dönüş Kesiği düzeltmesinden önceki ara ölçümde
yuvarlanma + saldırı tek başına isabetlerin %20'siydi.)

Neden çoktu ve ne değişti:
1. **Durum koşulları sürüp gidiyordu**: kanayan / yanan / sersem / havadaki hedef, tam ivme, hücum, arkadan, uçtan (kırbaç)
   koşulu bir kez sağlanınca her vuruş kritikti (Gürz her vuruşta sersemletip sersemliğe kritik vuruyordu). Artık koşul
   kritiği aynı düşmanda en çok **1,2 sn'de ve 4 isabette bir** (`zorluk.json` "kritik.kosul_bekleme" / "kosul_vurus";
   `Player._deal`). Kendiliğinden seyrek olan beceri koşulları serbest: tam bırakış, geri çekilirken atış, dönen balta,
   delip geçme, iki hedef, uzaktan, duvara çarpma, düşerken, donmuşu kırma (`Player.KRIT_SERBEST`).
2. **Zincir bitirişleri kesin kritikti** (Alp'in her üçüncü vuruşu, Ulu Kılıç / Gürz / Teber / Kor Çekici bitirişi, Ay
   Palası son vuruşu, Yatağan geri sıçrayışı, yuvarlanma sonrası Dönüş Kesiği): artık **Kut Yankısı'yla** (isabet anında
   zamanında basış) gelirse kritik, değilse kritik değil **x1,3 bitiriş hasarı** (`kritik.bitiris`; SnH'de sayılır). Usul
   sayılmaz (tuşa ezbere basan oyuncu usul penceresine sık denk geliyordu). Bekleme bitirişi (Şimşek Çekişi) ve kusursuz
   kaçış sonrası vuruş kesin kritik kalır.
3. **Böri Hançeri** sendeleyen yaratığa kritik vuruyordu; hafif yaratık her vuruşta sendelediği için her vuruş kritikti →
   yalnızca arkadan ya da sersem.
4. **Şans kritiği**: silah tabanları 3-8 → 2-5, malzeme Gümüş 6 → 3, Yeşim 3 → 2, Ayaz 2 → 1, Gök Demiri / Ruhani 4 → 2,
   yuvarlama -2..+3 → -1..+1,5, "İsabetli" 3-12 → 2-7, Ay Ata lütfu 10 → 6, Segrek adı 10 → 5.
5. Kesin kalanlar (beceri): Kut Mührü, Çarpışma karşılığı, Karşı Vuruş, Kut Alma, kusursuz kaçış, tam bırakış / dipten
   atış, ok sökme. Ölçüm için kesin kritiğin nedeni `Player.krit_say` içinde (`kesin_karsi`, `kesin_muhur`...).

### Tuşlar

| eylem | önce | v23 | oyun kolu |
|---|---|---|---|
| Teçhizat 1 / 2 | U / I | **E / R** | LB / RB |
| Al / değiştir, konuş, tomar oku, sunak | E | **W / ↑ (kısa dokunuş)** | yön yukarı / Back |
| Üç Âlem kam transı (S+: yeraltı) | R | **T** (v25: kaldırıldı) | LT |
| Menüde onay (tomar, yuva, Umay, Demirci, Ozan, ad töreni, ayarlar) | E / Boşluk | **Boşluk / Enter** (tomar: J de) | A |
| Umay / Demirci'den ayrıl | Boşluk / Esc | **Esc / L** | B / Start |

J / K (silahlar), L / Shift, Q, F, G aynı. **Neden W bir dokunuş**: ↑ aynı zamanda ↑+J "Göğe Savur"un yönü. Etkileşim
basışta değil kısa dokunuşun **bırakılışında** tetiklenir; tuş basılıyken saldırı, zıplama, yuvarlanma, teçhizat, şişe,
Kut ya da don basılırsa (v25'e dek âlem de) ya da 0,45 sn'den uzun basılırsa iptal olur (`Level._etkiles_tap`). Yerdeki eşyanın
üstünde göğe savurmak eşyayı almaz. Menülerde W/S seçim gezdiği için onay Boşluk / Enter'a taşındı. Güncellenen bütün
ipuçları: yuva tuş rozetleri (`HUD.SLOT_KEYS`), kam halkası "T", öğretici kartları (T / S+T), yeraltı kapağı işareti (bu üçü v25'te Üç Âlem'le kalktı),
yerdeki eşya / tomar / sunak istemi (W), NPC balonu (W), başlık ekranı kontrol satırları, duraklatma ekranına tuş satırı,
menü ipuçları, yurt mesajı.

### Test

* `-- --tomar --boss` (yeni, `tools/tests/tomar_testi.gd`): SNH (yukarıdaki tablo; `SONUC GECTI|KALDI`), KRIT (silah başına
  kritik payı ve kaynakları). `--snh` / `--krit` yalnızca birini, `--snh_silah=a,b`, `--snh_sn=`, `--krit_sn=`,
  `--snh_iz` (her hasar olayını yazar).
* `-- --denge`: yeni sütunlar "tipik silah tomarsız", "başl. silah + tipik tomar"; boss satırında tomarsız süre ve 100 canla
  ölüm. Beklenen tomar modeli Zorluk.gd'den.
* `-- --otomatik --bot_gercek`: tomar okurken Bozkurt seçer; `[otomatik] KRIT ...` ve `KRIT_KESIN ...` satırları;
  `--tomarsiz` tomarsız beklenen donanım.
* `--ekran=tilsim` (tomar kartı), `--ekran=oyun` (yerdeki silah kartı + iki silah etiketi), `--ekran=yuva`,
  `--ekran=duraklat` ekran görüntüleri.

## v23: yapay zeka ve boss mekanikleri

Geri bildirim (oynayarak): "Yaratıkların yapay zekâsı iyi olmalı. Bosslar bekliyor; Kara Börü Han ve Tepegöz duruyor,
ben aşağı doğru kesip geçiyorum, ara sıra vurmaya çalışıyorlar. Taktik kullanmam gereken gerçek mekanikler gelsin.
Sıradan yaratıklar da zor olsun, roguelike sonuçta."

### Neden pasifti (denetim, v22 kodu)

* **Ezbere basmak her şeyi kilitliyordu.** Hafif yaratık her vuruşta 0,1-0,24 sn sarsılıyor, yapay zekâ o sürede
  duruyordu; 4 vuruşta 0,6 sn "diretme" sonra yine baştan. Hazırlıktaki ("!") her yaratığa değen vuruş Karşı Vuruş
  sayılıp hazırlığı kesiyordu: dibine girip basan oyuncu hazırlıkları otomatik kesiyordu. Ölçüm (aşağıda): kurt / kalkanlı
  / akıncı ezmede zamanın %50-69'u kilitli, 22 türün 17'si ezen oyuncuya **hiç** hasar veremedi.
* **Bosslar kesiliyordu.** Boss hazırlığı da sersemletmeyle (×0,4) iptal olup "toparlanma"ya düşüyordu; dondurma ve kök
  tam süre işliyordu; kritik / ağır vuruş 0,08 sn sarsıp yapay zekâyı durduruyordu; her vuruş bossu geri itiyordu.
  Ezmede boss hamle sayısı 30 sn'de 12'den 20 sn'de 5'e düşüyordu; boşta kalma %32-38.
* **Uzun bekleme, tek hamle.** Hamle arası 0,7-1,6 sn yürüyüp durma, her hamle tek vuruş, kombo yok, hareket yok
  ("chase" menzile girince duruyor). Ortak boss motoru beş boss için aynı 7 hamle.
* **Eksik yapay zekâlar.** `tornado`, `crawler`, `swarm`, `caster`, `kamikaze`, `mimic`, `charmer` uygulanmamıştı (sprite'ın
  yapay zekâsına düşüyordu: Tozkoparan sıradan dev, Işıltı Kamı sıradan kam...); `cin` (teleporter) hiç kıpırdamıyordu.
  Dalıcılar (Kurgan Ruhu vb.) 10 sn'de 37 kez dalıp hiç değemiyordu; düşman güdümlü mermileri (spor, lanet) oyuncuya
  değil **en yakın düşmana** (çoğu kez atanın kendisine) dönüyordu (`Projectile._nearest_target`).

### Ortak kurallar (`Enemy.gd` "v23 ortak yapay zekâ")

* **"!" ve "!!"**: `_tele(t, zirhli)` her saldırının hazırlığı. "!" (kızıl) Karşı Vuruşla kesilir. "!!" (turuncu, halkalı)
  zırhlı hamle (`sa_t`): vuruş sarsmaz, hafif sersemletme (< 0,75 sn) kesmez, Karşı Vuruş yalnız kritik; ağır silah (duruş
  hasarı ≥ 2), çarpışma (0,8 sn) ve duruş kırılması keser. **Baskı altındaki** (son 0,8 sn'de vurulmuş) yaratığın sıradaki
  hazırlığı kendiliğinden "!!" olur: ezbere basan oyuncu zırhlı karşılık yer; vurup bekleyen, "!"yi okuyup karşılayan
  ödüllenir.
* **Sonsuz kilit yok**: sarsılan hafif yaratık 0,34 sn (büyük vuruşta 0,5) hafif vuruşlarla sarsılmaz (`_flinch_imm`; bu
  vuruşlar diretmeye yine sayılır, v19 duruş döngüsü aynen); art arda sersemletmede azalan getiri 1 / 0,6 / 0,35 / 0,2.
* **Tepki** (`TEPKI`, `_react`): kısa sürede N vuruş yiyen yaratık tepki verir (bekleme 2,2 sn): kurtlar geri sıçrar
  (dokunulmaz, yarı yarıya hemen karşı atılış), Yek dumana karışıp arkanda belirir, kam / iye / Erlik kızı ışınlanır,
  okçu geri takla atar, uçanlar süzülerek kaçar, dev / kasırga zırhlı döner savuruş, Balbal siper + zırhlı kesik,
  Gulyabani zırhlı yakalama, kalkanlı / akıncı zırhlı kalkan darbesi, kamikaze fitili ateşler.
* **Saldırı jetonları** (`_token`): oyuncunun çevresinde aynı anda en çok 1 / 2 / 3 (derinlik 1-2 / 3-6 / 7+) yakın ve 2
  uzak saldırgan (seçkin hep alır). Jetonsuz yakın dövüşçü beklemez: 100-160 px bantta salınarak dolanır (`_orbit`), sürünün
  ikincisi arkana geçer. v22 `_pack_beat` aralığı sürüyor.
* Kıpırdamadan duran oyuncu (`_pl_still`): uzaktan saldıranlar tehlikeyi tam altına koyar.
* Düşman güdümlü mermileri artık oyuncuya döner (`Projectile._nearest_target`).

### Yaratık rolleri

| Yapay zekâ | Yaratıklar | Rol ve takım |
|---|---|---|
| `lunger` | Erlik / Ayaz Tazısı | Hızlı kurt: dolanır, jetonu alınca menzile girer; kısa (0,24) ya da uzun (0,42) hazırlıkla atılır, bazen inişte ikinci atılış, sonra geri seker. 3 vuruşta geri sıçrar. |
| `pouncer` | Pusu Tazıları | Yüksekte bekler, altından geçene atlar; yerde kurt gibi. |
| `stalker` | Yek, Albastı | Görünmez yaklaşır, 110 px'te belirip vurur; 3 vuruşta kaybolup arkanda belirir. |
| `crawler` (yeni) | Mağara Tazısı | Alçak, çok hızlı: 2-3 ısırıklık zincir (her biri ayrı "!"), sonra kaçar. |
| `flyer_ranged` | Çor Ruhu, Kandil İyesi | Çaprazda süzülür, öngörülü güdümlü spor salvosu (1-3), yaklaşınca kaçar, tam üstündeyse dalar. |
| `swarm` (yeni) | Kan Çoru, Kayıp Ruh | Çevrende döner; jetonu alan "!" ile içinden geçen süzülüş (sırayla). |
| `diver` | Kurgan Ruhu, Ayaz Çoru, Demir Gaga | Tepende süzülür, yere işaret koyar, pike yapar, yere saplanıp 0,7 sn açık kalır. |
| `brute` | Kara İye, Dev Çocuğu, Çini Golemi | Yavaş döner (arkasına geç); zırhlı çakma "!!" 0,8, zırhlı sıçrayıp ezme, işaretli kök dalgası, dibine / arkasına girene hızlı ters tokat. 5 vuruşta zırhlı döner savuruş. |
| `tornado` (yeni) | Tozkoparan | Zırhlı kasırga (1,7 sn): seni kovalar, kendine çeker, çok vuruşla dağlar; sonra 1 sn başı döner. Dibindeyken yel itişi. |
| `caster` (yeni) | Su İyesi, Od İyesi | Uzak durur, sıkışınca öbür yana ışınlanır; işaretli zehir / alev gölü (derinde üçlü) ya da yavaş üçlü küre. |
| `hopper` | Balbal, Buz Balbalı | Seker, önden siper alır; taş kılıç ya da zırhlı sıçrayıp çakma. |
| `illusionist` | Kara Kam (Cin de) | Hayalet kopyalar + arkana ışınlanma ya da güdümlü lanet (derinde ikili); dibine girince ışınlanır. |
| `archer` | Kurgan Kamı | 150-290 px; öngörülü ok, derinde üçlü salvo; yaklaşınca geri takla. |
| `kamikaze` (yeni) | Işıltı Kamı | Koşar, dibinde "!!" fitil (0,6 sn, büyüyerek parlar), patlar; vurmak fitili ateşler, öldürünce de küçük patlama. |
| `charmer` (yeni) | Erlik'in Kızı | Büyü bağı (mor ışın): yuvarlanmazsan kendine çeker, dibinde lanet patlaması; ya da iki güdümlü küre. |
| `grabber` | Gulyabani | Kavrama hep "!!" (yuvarlan); ıskalarsa 1 sn açık; dibindeyken hızlı pençe. Yakalarsa sıkar, fırlatır. |
| `mimic` (yeni) | Karakoncolos | Kar yığını gibi kıpırtısız bekler; yaklaşınca (ya da oyalanınca) "!!" ile yakalar; uzaktaysan kartopu. |
| `shield` | Kurgan Bekçisi vb. | Önden kalkan; 0,45 sn'de döner (arkasına yuvarlan); hızlı dürtme "!" / gecikmeli zırhlı baş üstü "!!" / kalkan itişi; kalkana art arda vurana zırhlı kalkan darbesi; kalkanı toparlanınca karşılık. |
| `charger` | Kızıl Gul, Kurgan Akıncısı | Zırhlı hücum "!!"; duvara çarparsa uzun sersem; üstünden atlanırsa kayıp döner, kısa ikinci hücum. |
| `turtle` | Tosbağalar | Kabuk, yuvarlanarak ezme; yuvarlanmadan sonra 1 sn başı döner. |

### Bosslar (`Boss.gd`): ortak motor

* Hamleler adım dizisi (`_seq`, `_w` uyarı adımı, `_a` eylem adımı; `go` / `tick` / `until`): kombolar ve zincirler
  (`_then`) tek yerde okunur. Hamle arası 0,3-0,75 sn (evre ve öfkeyle kısalır); arada bir sonraki hamlenin menziline
  yürür ya da geri çekilir, menzildeyken de bant içinde salınır (`_stalk`). Seçim ağırlıklı, aynı hamle art arda gelmez,
  bekleme süreli hamleler (`_cool`).
* **Süper zırh**: vuruşlar hamleyi kesmez, bossu itmez; sersemletme duruşa eklenir; dondurma 8 sn'de bir 0,5 sn; kök yok.
* **Boss duruşu** (`b_poise`): isabet başına duruş hasarı (silah duruşu + kritik 1 + ağır 1,5 + sersemletme ×1,5; hamle
  sırasında ×0,75), 2 sn vurulmazsa söner. `30 + 6 × evre` dolunca **SENDELER**: 1,8 sn açık, ×1,25 hasar, HUD'da "duruş
  kırık", sonra 10,8 sn birikmez.
* **Boss zırhı** (`ZIRH`): açık pencereler dışında hasar ×0,75 (Şahmeran ×0,68, Erlik ×0,7). Pencere = sendeleme, Tepegöz'ün açık gözü
  (×2), Şahmeran'ın saplanan başı (×1,5). Pencereyi kollayan oyuncu savaşı belirgin kısaltır.
* **Yakın cezalandırıcı "nova"**: oyuncu 1,2 sn'den uzun dibinde kalırsa (ezbere vuruyorsa) "!!" ile iten şok halkası
  (her bossa kendi biçimi: uluma, tepme, kuyruk dönüşü, buz dikenleri, alev halkası).
* Platformdaki / uzaktaki / kıpırtısız oyuncuya ayrı ağırlıklar (yanlış yerde durmak cezalandırılır). Evre geçişi %66 / %33'te
  kükreme şoku + yeni hamleler; %15'in altında **ÖFKE** (hamle arası ×0,65, uyarı ×0,85, en az 0,28 sn).
* Uyarılar: "!" / "!!" ve gerektiğinde ipucu yazısı (ZIPLA!, YUVARLAN!, ARKANI DÖN!, DİREN!, TAMU DARALIYOR!...); yer
  uyarıları (`GroundMarker`), hücum şeritleri ve tehlike kurulumu (`scripts/world/Tehlike.gd`), ışınlar (`Isin.gd`),
  rüzgâr (`Ruzgar.gd`).

### Kara Börü Han (2. derinlik)

| Evre | Hamleler |
|---|---|
| 1 | **Sıçrayış zinciri** (2 sıçrayış; son sıçrayışın uyarısı uzun: ritmi bozar), **yer yaran hamle** (yerde şerit; 720 px/sn oyuncunun içinden 260 px öteye: içinden yuvarlan), **pençe yağmuru** (3 hızlı pençe + 0,55 sn sonra ağır pençe), **uluma** (geri sıçrar, 2 ruh tazısı çağırır, yakındakini iter). Vur-kaç: çoğu hamleden sonra geri sıçrar. |
| 2 (%66) | + **duvardan pike** (arena duvarına tırmanır, oyuncunun yerini işaretler, çapraz dalar, iki yana yer dalgası; inişte 0,75 sn açık), **bozgun kristalleri** (işaretli yay atışı salvosu), 3'lü sıçrayış, sıçrayış → hamle, ikili hamle. |
| 3 (%33) | + **gölge oyunu** (gölgeye karışır, iki sahte kopya iki yandan sırayla sıçrar, asıl üçüncü yandan gelir; kopyalar tek vuruşta dağılır), **gölge eş** (canın %12'si; sıçrayış / hamle / pençe). Öfke: zincire +1 sıçrayış. |

### Tepegöz (4. derinlik)

| Evre | Hamleler |
|---|---|
| 1 | **Gürz çakışı** (önünde 0,45 sn sonra kor fışkıran, 3 sn yanan çatlak), **kaya atışı** (iniş yeri işaretli; kaya dört parçaya bölünür), **yer tepme** (iki yana şok dalgası: ZIPLA!), **kavrama** ("!!" YUVARLAN!: yakalarsa kaldırır, sıkar, fırlatır; 4 basışla kurtulursan 1,2 sn sendeler). |
| 2 (%66) | + **göz ışını** (önce nişan çizgisi, sonra yerde sürünen ışın, arkasında kor: üstünden zıpla / içinden yuvarlan), **hücum** (şerit; duvara çarparsa **GÖZ AÇIK**: 2,6 sn ×2 hasar, sonra kükreme şoku), ikili çakış, ikili tepme, ikili kaya. |
| 3 (%33) | + **dağ sarsıntısı** (ortaya sıçrar, iki yana dalga, tavandan işaretli 6 kaya), çapraz tarama (ışın gidip gelir), üçlü tepme, üçlü kaya, çakış → tepme kombosu. |

### Şahmeran Ana (6. derinlik)

| Evre | Hamleler |
|---|---|
| 1 | **Zehir tükürüğü** (üç yay; iner inmez 4 sn'lik zehir gölü), **kuyruk süpürmesi** (alçak, iki yana: ZIPLA!), **sokma** (çöreklenir, 290 px atılış; ıskalarsa başı 0,8 sn yere saplanır: ×1,5). |
| 2 (%66) | + **yılan sürüsü** (3 alçak, hızlı yılan; en çok 4), **mağara yıkımı** (kuyruk tavana: sıralı damla yağmuru), sokma → kuyruk kombosu. |
| 3 (%33) | + **taşlaştıran bakış** ("!!" ARKANI DÖN!: ona dönük duran 1,1 sn taşlaşır, ardından sokma), **zehir pınarı** (bulunduğun yerin altından sırayla 4 göl). Öfke: beşli tükürük, ikili sokma. |

### Yelbegen (8. derinlik)

| Evre | Hamleler |
|---|---|
| 1 | **Gürz savuruşu**, **yel üfürüğü** (DİREN!: 2,2 sn seni geri iter; rüzgârla düzenli buz parçaları gelir: alçak-alçak-yüksek, alçağın üstünden zıpla, yüksekte zıplama), **üç baş** (sırayla düz buz, ikili yelpaze, inişte buz dikeni bırakan yay atışı). |
| 2 (%66) | + **ayaz soluğu** (önündeki yere sürünen huzme, arkasında buz dikenleri), **saçak yağmuru** (iki dalga işaretli saçak) + üfürük kombosu, ikili savuruş. |
| 3 (%33) | + **Kaf fırtınası** (4,2 sn: rüzgâr 1,3 sn'de bir yön değiştirir (ok işareti), çevrene saçak yağar, başlar ateş eder), **buzlu sıçrayış** (iniş halkası buz dikenleri). Öfke: beş baş atışı. |

### Erlik Han (10. derinlik)

| Evre | Hamleler |
|---|---|
| 1 | **Kara zincir** (değerse seni çeker, ardından yukarı savuruş), **ateş dalgası** (iki yana dalga + yakına vuruş, inişte kor), **Tamu ateşi** (yay atışı ateş topları; düştüğü yerde kor), **tırpan** (iki savuruş), **Tamu kapısı** (yere batar, erişilmez, öbür yanında kor halkasıyla yükselir; ardından tırpan ya da dalga). |
| 2 (%66) | + **kor sütunları** (bulunduğun yerde sırayla 6 sütun), **kayıp ruhlar** (sürü), **daralan Tamu** (kenarlardan içeri yürüyen alev duvarı, 7 sn). |
| 3 (%33) | + **Tamu Seli** (v25'e dek "Âlem kayması"; Üç Âlem'den bağımsız boss mekaniği, hamle adı `tamu_seli`): ekran kızıla döner, "TAMU TAŞIYOR — PLATFORMLARA ÇIK!": 1,4 sn sonra bütün zemin 4,5 sn lav; arenanın üç taş platformu güvenli, Erlik lavdan platformlara ateş atar. Sonra "KOR YAĞIYOR — AŞAĞI İN!": platformlara kor yağar (2,6 sn). Öfke: ikili zincir. |

### Ölçüm: önce / sonra (`-- --zeka`, `tools/tests/zeka_testi.gd`)

Düz boss arenasında tek tek, mühürsüz (`Zorluk.set_muhur(0)`), 3. derinlik. **PASIF** 20 sn: oyuncu kıpırdamaz, yaratık
150 px ötede uyanık doğar. **EZME** 20 sn: oyuncu dibine girip 8 karede bir saldırır (eski bot gibi; Alp Kılıcı); kilitli =
sarsılmış / sersem / kalkanı düşmüş / havaya atılmış karelerin payı. "Önce" aynı test, v22 `Enemy.gd` / `Boss.gd` /
`Projectile.gd` ile.

| Yaratık | YZ önce → sonra | ilk saldırı (sn) | hamle / 10 sn (pasif) | pasif oyuncuya hasar / 30 sn | EZME: hamle / 10 sn | EZME: kilitli | EZME: hasar / 10 sn |
|---|---|---|---|---|---|---|---|
| kara_boru | lunger | 0.67 → 0.87 | 4.0 → 7.0 | 345 → 475 | 2.5 → 5.0 | %63 → %30 | 0 → 43 |
| sicrayan_tazi | pouncer | 0.75 → 0.75 | 5.5 → 5.5 | 475 → 518 | 2.5 → 3.0 | %69 → %40 | 0 → 43 |
| yek | stalker | 0.83 → 0.85 | 4.5 → 7.5 | 432 → 528 | 2.5 → 4.5 | %64 → %32 | 0 → 32 |
| kirkayak | lunger → crawler | 0.53 → 0.50 | 4.5 → 11.0 | 367 → 326 | 2.5 → 6.5 | %64 → %31 | 0 → 32 |
| ayaz_kurdu | lunger | 0.60 → 0.73 | 4.5 → 7.0 | 410 → 501 | 2.5 → 5.5 | %62 → %37 | 0 → 0 |
| cor | flyer_ranged | 0.47 → 0.45 | 3.5 → 5.0 | 142 → 267 | 4.0 → 4.0 | %1 → %16 | 0 → 55 |
| kara_kus_yavrusu | diver | 0.47 → 1.32 | 37.0 → 3.5 | 0 → 285 | 37.0 → 3.5 | %0 → %12 | 0 → 15 |
| kan_yarasasi | flyer_ranged → swarm | 0.47 → 0.47 | 3.5 → 6.0 | 127 → 253 | 3.5 → 4.5 | %0 → %26 | 14 → 21 |
| agac_iyesi | brute | 0.47 → 0.47 | 2.5 → 2.5 | 403 → 345 | 3.5 → 5.0 | %27 → %16 | 0 → 63 |
| dev_cocugu | brute | 0.47 → 0.47 | 3.0 → 3.0 | 466 → 440 | 3.5 → 5.5 | %27 → %16 | 0 → 64 |
| tozkoparan | brute → tornado | 0.47 → 0.47 | 3.5 → 3.5 | 380 → 259 | 4.0 → 5.5 | %30 → %10 | 0 → 86 |
| su_iyesi | brute → caster | 0.47 → 0.47 | 3.5 → 3.5 | 412 → 344 | 3.5 → 4.0 | %26 → %0 | 0 → 93 |
| balbal | hopper | 4.03 → 0.97 | 2.5 → 3.5 | 240 → 336 | 4.0 → 5.0 | %33 → %16 | 0 → 48 |
| arcura | illusionist | 0.47 → 0.47 | 4.0 → 4.0 | 115 → 249 | 5.5 → 4.0 | %60 → %0 | 6 → 25 |
| kurgan_okcusu | archer | 0.47 → 0.47 | 4.5 → 5.0 | 307 → 345 | 5.5 → 5.0 | %59 → %1 | 0 → 76 |
| isilti_bocegi | illusionist → kamikaze | 0.47 → 1.07 | 4.0 → 3.0 | 172 → 552 | 6.0 → 9.0 | %51 → %40 | 9 → 61 |
| erlik_kizi | illusionist → charmer | 0.47 → 0.47 | 4.0 → 3.0 | 107 → 181 | 5.0 → 3.0 | %58 → %16 | 0 → 15 |
| surale | grabber | 1.02 → 0.90 | 3.0 → 3.5 | 1382 → 380 | 3.0 → 4.5 | %30 → %37 | 0 → 28 |
| karakoncolos | grabber → mimic | 0.90 → 2.50 | 3.0 → 3.5 | 1411 → 221 | 3.0 → 4.5 | %33 → %31 | 0 → 16 |
| kurgan_bekcisi | shield | 1.82 → 1.65 | 4.0 → 5.0 | 383 → 321 | 4.0 → 5.5 | %74 → %16 | 0 → 36 |
| al_atli | charger | 0.47 → 0.47 | 4.0 → 2.5 | 351 → 524 | 4.5 → 5.0 | %73 → %35 | 0 → 15 |
| tas_kertenkele | turtle | 1.12 → 1.08 | 4.0 → 3.0 | 345 → 285 | 2.0 → 2.5 | %14 → %10 | 14 → 17 |

Özet: ezmede ortalama kilit %42 → %21; ezen oyuncuya hiç hasar veremeyen tür 18 → 1 (rastlantı: Ayaz Tazısı o koşuda
vuramadı; aynı türden Erlik Tazısı 43); ezmede verilen hasar ortalama 2 → 40 / 10 sn. Pasif oyuncuya verilen hasar
benzer (399 → 361; Gulyabani'nin kurtulmayan oyuncuyu art arda sıkıp 1382 vurması düzeltildi). Dalıcılar artık değiyor
(0 → 285).

**Bosslar** (`-- --zeka --boss=<id> --zeka_oldur`; kendi derinliklerinin beklenen donanımı: o kademenin Nadir Alp Kılıcı +
derinlik başına ~2,5 tılsım; can sınırsız, alınan hasar azami can katı olarak). Botlar: **ezen** (dibinde basar, hazırlıkta
yarı yarıya yuvarlanır), **iyi** (hazırlığın son 0,2 sn'sinde %85 uzağa yuvarlanır, tehlikede geri çekilir, yer dalgasının
üstünden zıplar, açıkta vurur).

| Boss | pasif 30 sn: hamle / boşta / hasar | ezme 20 sn: hamle / kilit / boşta | ezen bot: süre (alınan hasar) | iyi bot: süre (alınan hasar, erişim, sendele) |
|---|---|---|---|---|
| Kara Börü Han | 10 / %16 / 287 → 14 / %6 / 188 | 4 / %8 / %37 → 9 / %0 / %8 | 44 sn (1,2×) → 68 sn (3,7×) | 17 sn (0,3×) → 75 sn (3,7×, %33, 0) |
| Tepegöz | 12 / %20 / 230 → 14 / %16 / 230 | 7 / %6 / %37 → 10 / %0 / %12 | 19 sn (0,2×) → 38 sn (1,9×) | 20 sn (0×) → 75 sn (3,4×, %34, 4) |
| Şahmeran | 11 / %13 / 279 → 16 / %16 / 720 | 4 / %7 / %27 → 9 / %0 / %12 | 18 sn (0,2×) → 54 sn (1,9×) | 25 sn (0,5×) → 57 sn (3,0×, %33, 0) |
| Yelbegen | 13 / %19 / 396 → 10 / %9 / 277 | 8 / %1 / %30 → 9 / %0 / %13 | 16 sn (0,1×) → 27 sn (0,8×) | 40 sn (0,5×) → 67 sn (2,3×, %28, 1) |
| Erlik Han | 13 / %19 / 472 → 19 / %15 / 850 | 5 / %13 / %35 → 9 / %0 / %11 | 24 sn (0,3×) → 37 sn (0,9×) | 20 sn (0,3×) → 77 sn (3,3×, %26, 1) |

"Boşta" = hareketsiz bekleme + kilit. Önce: iki bot da bossları 16-44 sn'de, neredeyse hasar almadan deviriyordu; boss
ezmede hamlelerinin yarısını kaybediyordu. Sonra: hiçbir boss kilitlenmiyor, ezmede de aynı sıklıkta saldırıyor; iyi bot
57-77 sn (v22 hedefi 60-120 sn; botun hasarı insandan yüksek: Kut Yankısı ritmine denk gelen 8 karelik basış), alınan hasar
azami canın 2,3-3,7 katı (3 şişe ≈ %135 can). İyi botta hamle kullanımı (örnek): Kara Börü Han pençe 6, nova 5, sıçrayış 3,
hamle 3, uluma 3, gölge 2, pike 2; Tepegöz tepme 10, çakış 7, kavrama 7, nova 6, kaya 3, hücum 2; Erlik ateş dalgası 10,
kapı 6, zincir 5, tırpan 4, sütun 2, Tamu Seli (o zamanki adıyla âlem kayması) 1. Ezen bot Yelbegen'i hâlâ 27 sn'de deviriyor (dibinde %61 erişim; bilinen
eksik).

**Bot** (`--otomatik [--bot_gercek] --derinlik=N --muhur=0`, `--fixed-fps 60`, 6600 kare ≈ 110 sn): betik hatası 0. Ölçüm
botu (`--bot_gercek`) 1-9. derinlikte ölmedi (9. derinlikte 920 hasar, 3 şişe; önce 1991, 5 şişe: rota değişti, karşılaştırma
gürültülü); başlangıç donanımlı eski bot 9. derinlikte öldü (önce ölmedi), 7. derinlikte 5 dolum (önce 0).

### Test

* `-- --zeka [--derinlik=N] [--zeka_tur=a,b] [--zeka_iz]`: yaratık tablosu (`[zeka] TABLO`); `--zeka_iz` durum geçişlerini
  ve oyuncu canını yazar.
* `-- --zeka --boss=<id> [--zeka_oldur] [--bosslog]`: pasif / ezme / ezen bot / iyi bot; hamle kullanımı (`Boss.move_log`),
  hamle başına alınan hasar, sendeleme ve açık pencere sayısı. `--bosslog` her hamleyi, sendelemeyi ve açık gözü yazar.
* Çekim (headless değil): `-- --zeka --boss=<id> --zeka_cekim=<mutlak klasör> --pencere=1920x1080` her hamleyi sırayla
  zorlar, uyarı / vuruş / sonrası karelerini kaydeder; `--boss` olmadan sekiz yaratığın hazırlık, vuruş ve ezmeye tepkisi.
* `--muhur=N` (Main): ölçümü kayıtlı Kut Mührü seçiminden bağımsız yapar.
* `--dovus --boss` TAKILMA=0 (v19 duruş kırılması, infaz, karşı vuruş, çarpışma aynen: test mankenleri `cd = 99` ile
  pasif, tepki / kaçış / intikam yok); `--mekanik` BITTI; `--denge` OZET; `--piksel_tara` 0 (normal bölüm, Erlik ve
  Tepegöz arenası); beş boss `--otomatik --boss --bosslog` betik hatası 0.

## v24: tüccar ve silah parşömenleri

İstek: "Haritada bazı yerlere tüccar ekleyelim. Yurtta silah parşömenlerini açtığımızda açtığımız silahı rastgele
statlarla doğrudan versin."

### Bezirgân Sartak (`scripts/world/Bezirgan.gd`, `scripts/core/Pazar.gd`, `data/tuccar.json`)

Eski Türkçede "sart" tüccar demektir; Dede Korkut'ta bezirgânlar diyar diyar dolaşıp beylere armağan getirir. Sartak
Erlik'in karanlığında bile kervanını yürüten, Kut'a değil altına bakan kurnaz bozkır bezirgânıdır.

* **Görünüş** (`tools/artgen/tuccar_ink.py`, mürekkep-cel, texel 4): kürk kenarlı uzun sivri lacivert keçe börk (kızıl
  püskül), sarkık kır bıyık, çizgili safran-lacivert-kızıl ipek kaftan, altın kuşak ve sikke kesesi, ucu kalkık çizmeler;
  sırtında ahşap çatkılı yük küfesi (dürülmüş kilimler, bakır güğüm, ışıyan fener); ön elinde tunç terazi (kefede ışıyan
  sikkeler). `npc_tuccar_v2` NPC düzeninde: idle 6 kare (kefeler salınır), talk 4 kare ("buyur" eli, terazi kalkar).
  Tezgâh `bezirgan_kervan_v2` (sus_v2.json): çöken iki hörgüçlü deve (kızıl çul, kilim heybe, boyun çıngırağı, sırtta
  kilim denkleri), yere serili kilimde mallar (sehpada kılıç, kalkan, yay, küpler, mühürlü tomar, sikke yığını), fener
  direği ve kızıl-safran flama. Tüccar tezgâh kökeninin 48 birim sağında, devenin kuyruk yanında durur. HD x2 paketi:
  `assets_hd/x2/sprites/npc_tuccar_v2.webp`, `assets_hd/x2/decor/bezirgan_kervan_v2.webp` (manifest girişleri; denetim
  TAMAM, ort fark 0,0013 / 0,0017).
  Üretim: `python export_ink.py --tuccar`, `python export_sus.py --tuccar` (HD: önüne `KY_HD=2`, sonra iki dosya için
  `hd_paket._encode` + manifest).
* **Nerede** (`Level._plan_bezirgan`, `data/tuccar.json` "yer"):
  * boss öncesi bölümde (Game.BOSS_AFTER: 2, 4, 6, 8, 10. derinlik; boss henüz yenilmemişse) **kesin**, Kut Kapısı'na en
    yakın uygun yerde (karo 168-212); bossla dövüşmeden önce son alışveriş,
  * 1. derinlikte %35, diğerlerinde %55 şansla bölümün orta kesiminde (karo 70-170), uygun yer yoksa bütün bölüm,
  * ayrı rng (bölüm tohumu + 7919): bölümün geri kalanı (yaratıklar, süsler) aynı kalır.
* **Duvara gömülmez**: yer karolar kurulmadan ve gizli odalar oyulmadan seçilir ve tezgâhın altı **düzlenir**. Tezgâh +
  tüccar alanı 10 karo (tüccarın 7 karo solu, 2 karo sağı). Alandaki yüzey en çok 2 karo oynuyorsa çukurlar doldurulur,
  tümsekler ve üstteki 4 karo temizlenir (en çok 14 katı karo: mağara tavanı oyulmaz); yüzey katı olmalı (platform /
  zehir / lav değil), çevrede tehlike karosu, oda işareti (S/T/E), eşya kaidesi (34 / 104 / 168; v25: 38 / 116 / 188), giriş ve Kut Kapısı
  olmaz; en az düzleme isteyen yerlerden seçilir. Keşif ganimeti (v25; eskiden gizli oda kapağı) tezgâhın 6 karo yakınına konmaz, süsler
  tezgâhın 3 karo yakınına konmaz (`_decor`), tezgâhın üstüne düşmüş ganimet yana alınır, 9 karo içindeki sıradan
  yaratıklar kaldırılır (tezgâh sakin köşe). Denetim `Level.bezirgan_ok()`: alanın her 6 px'inde katı karo yok, ayak altı
  boyunca zemin katı (`[tuccar] ... duvar_ok=` ve `[otomatik] ALTIN ... duvar_ok=`).
* **Pazar** (W kısa dokunuşu; `Main._on_tuccar`, `HUD._draw_tuccar`, mürekkep arayüzü): 3-5 mal
  1. bir silah (yakın ya da yay; o derinliğin kademesi, normal nadirlik zarı),
  2. rastgele bir eşya (silah / kalkan / teçhizat, `ItemGen.random_drop`),
  3. "seçme" mal: bir üst kademeden (nadirlik ve malzeme şansı daha iyi), fiyat x1,35,
  4. **Umay Sütü**: bir şifa şişesini doldurur; şişeler doluysa canın %40'ı,
  5. %35 şansla (boss öncesinde kesin) **Kut Tomarı**, yüksek fiyatla.
  Solda mal listesi (simge, ad, kategori · nadirlik, fiyat; silahta "SnH N ▲ +X / ▼ -X" kuşanılan aynı yuva silahına
  göre), sağda seçili malın tam eşya kartı (karşılaştırmalı SnH farkı, tomar satırı, ek özellikler, kusur). Boşluk ilk
  basışta "X — N altın. Satın alınsın mı?" onayı, ikinci basışta alır. Satılan mal "SATILDI" (soluk, üstü çizili) kalır.
  Alınan eşya / tomar tüccarın kilimine, oyuncunun önüne düşer (W ile alınır; iki yuva doluysa yuva seçimi). En alttaki
  satır **malları yenile**: bütün mallar yeniden yuvarlanır, her yenileme +%60 pahalı. Esc / L onayı geri alır ya da
  pazardan çıkar. Pazar açıkken oyun durur; tüccar arkada konuşur.
* **İpuçları**: tüccarın üstünde ad + W balonu, yakınken "W Bezirgân: alışveriş (N altın)" istemi, ilk karşılaşmada
  öğretici kartı ("tuccar"), Demirci ekranının alt satırı ve parşömen kartı.

### Fiyat ve altın (`Pazar.gd`)

    derinlik_k = 1 + 0,3 x (derinlik - 1)
    eşya fiyatı = taban[kategori] x nadirlik[n] x (0,85 + 0,3 x kalite) x unsur(1,25) x kusur(0,8) x derinlik_k
                  (x 1,35 seçme mal), 5'e yuvarlanır;  taban: silah 60, kalkan 46, teçhizat 52;
                  nadirlik: Sıradan 1 · Nadir 1,7 · Destansı 2,8 · Efsanevi 4,6
    Umay Sütü = 34 x derinlik_k        Kut Tomarı = 230 x derinlik_k        yenileme = 14 x derinlik_k x (1 + 0,6 x n)
    altın tanesi = 1-3 x derinlik_k (v23: hep 1-3)

Gelir de fiyatla aynı çarpanla büyür, böylece her derinlikte denge aynı kalır. Düşüşler: sıradan düşman 2-4 tane, seçkin
+10 (önce +6), hazine kaidesi 6, boss 30 (önce 16). Ölçüm (`-- --tuccar`, derinlik başına 3 bölüm; "hepsi" = bölümdeki
bütün yaratıklar ve hazine, boss derinliğinde boss dahil; ortalama silah fiyatı o derinliğin düşüş zarıyla):

| d | hepsi öldürülürse altın | Sıradan silah | Nadir | Destansı | Umay Sütü | Tomar | yenileme | bezirgân / bölüm |
|---|---|---|---|---|---|---|---|---|
| 1 | 110 | 62 | 110 | 195 | 34 | 230 | 14 | 3/5 |
| 2 | 245 (+boss) | 83 | 146 | 256 | 44 | 300 | 18 | 5/5 |
| 3 | 188 | 102 | 184 | 295 | 54 | 370 | 22 | 5/5 |
| 4 | 338 (+boss) | 123 | 211 | 361 | 65 | 435 | 27 | 5/5 |
| 5 | 302 | 139 | 245 | 417 | 75 | 505 | 31 | 2/5 |
| 6 | 574 (+boss) | 158 | 277 | 485 | 85 | 575 | 35 | 5/5 |
| 7 | 500 | 175 | 310 | 523 | 95 | 645 | 39 | 3/5 |
| 8 | 737 (+boss) | 191 | 351 | 595 | 105 | 715 | 43 | 5/5 |
| 9 | 572 | 212 | 389 | 671 | 116 | 780 | 48 | 3/5 |

`--otomatik --bot_gercek` (yakındaki düşmanla dövüşen ama yolu koşan bot) bölümde 2-5 yaratık öldürür ve öldürme başına
beklenen altını toplar (1. derinlik 5 öldürme 28 altın, 5. derinlik 4 öldürme 53 altın); bölümü temizleyen oyuncu "hepsi"
sütununun ~%70-80'ini toplar. Okuma: Sıradan silah bir derinliğin altınının ~yarısı, **Nadir ~bir derinlik, Destansı
~iki derinlik birikim**, Kut Tomarı ~2 derinlik (tomar her bölümde 3 bedava; satın alınanı ek). Tüccar bölümlerin ~%80'inde
(boss öncesi kesin, ölçüm 36 / 45 bölüm) çıktığı için biriktiren oyuncu her tüccarda 1-2 iyi mal alır; Ata Kesesi (+60 / +120
başlangıç altını) artık anlamlı. Altın ölünce yiter (Kut gibi bankaya gitmez): harcamak teşvik edilir.

### Silah parşömenleri: açınca hemen ver (`Main._demirci_ac`, `HUD._draw_demirci_son`)

Önce: parşömen (açılmamış gelişmiş eşyanın tarifi; seçkinden kesin, sıradan düşmandan %7, bosstan kesin) dokununca
`Game.meta.blueprints`'e girer; yurtta (ya da koşu başında) Demirci Kam Kuzgun Kut karşılığı açar (`Game.unlock`) ve eşya
yalnızca **sonraki düşüşlerde** çıkabilirdi.

Şimdi: açılış aynı (Kut bedeli `Game.unlock_cost`, düşme havuzuna girer) ve ayrıca eşya **hemen dövülür**:
`ItemGen.roll(id, 0)`: kademe 0 (koşu başı gücü), malzeme ve nadirlik o kademenin normal düşüş zarıyla, hasar / hız /
kritik / mekanik değeri / ek özellik / kusur / unsur yuvarlanır (aynı parşömenden iki eşya aynı gelmez). Eşya oyuncunun
önüne, zemine bırakılır (`ground_y_below`, kıvılcım halkası); Demirci ekranında "ÖRSTE DÖVÜLDÜ · ÖNÜNE BIRAKILDI" kartı
(kuşanılan silaha göre SnH farkı) gösterilir, Boşluk kapatır, başka parşömen açılabilir. Yurtta yerdeki eşya artık W ile
alınır (önce: yurtta W yalnızca NPC ile konuşurdu; şimdi yakında eşya varsa önce o, yuva seçimi de yurtta çalışır).

### Test

* `-- --tuccar` (yeni, `tools/tests/tuccar_testi.gd`): EKONOMI tablosu (yukarıdaki; bezirgân sıklığı ve duvar denetimi),
  PAZAR (3. derinlikte zorla yerleştirilen tüccar: yanında W balonu, pazar oyunun yolundan açılır, onay + alış, altın
  düşüşü, SATILDI, kilime düşen eşya, kartın SnH farkı = `ItemGen.dps_oyuncu`, satılan malı yeniden alamama, Umay Sütü
  şişe doldurur, Kut Tomarı kilime düşer, altın yetmeyince satılmaz, yenileme ücreti ve yeni mallar, ikinci yenileme
  pahalı, alınan eşya `try_equip` ile kuşanılır), PARSOMEN (yurtta aynı parşömen iki kez açılır: Kut düşer, eşya havuzda,
  önüne kademe 0 eşya düşer, iki açılışın değerleri farklı). Kalıcı kayıt test sonunda geri yüklenir. `SONUC GECTI|KALDI`.
  `--tuccar_tohum=N` ekonomi tablosunda derinlik başına bölüm sayısı.
* Çekim kipleri (`--goruntu`, headless değil): `--tuccar_ekran=dunya | pazar | demirci | yurt` (`--tuccar_derinlik=N`).
* `-- --otomatik --derinlik=N`: `[tuccar] derinlik=N bezirgan=0|1 x= boss_oncesi= mal= duvar_ok=` ve bölüm sonunda
  `[otomatik] ALTIN derinlik= toplanan= kese= bezirgan= duvar_ok=`. `--tuccar_her`: her bölümde tüccar.

## v25: uzak silahlar ve cephane

Geri bildirim: "uzak silahları güçlendirelim (yıldırım asası gibi)", "ok atmaya sınır koyalım: tek oklu yaylar sınırsız ama
biraz yavaş, çok oklu yayların Dead Cells'teki gibi dolan cephanesi olsun", "okların arkasında da mürekkep izi olsun: çok
ince, unsuruna göre renkli".

### Ölçüm: neden zayıftı (`-- --tomar --boss --uzak`, `tools/tests/tomar_testi.gd`)

Yeni `--uzak` kipi her uzak silahı kuklaya (alçak Kara Börü, 110 px önde) 10 sn oyunun kendi girdi yolundan attırır:
yaylarda "gec" (yay dolar, tam bırakış penceresinden hemen sonra bırakılır: kartın saydığı tam güç, kritiksiz), "tam" (her
ok tam bırakış: beceri tavanı), Akıncı'da basılı tutma, fırlatma / büyüde her 2 karede bir basış. Kademe 0 Demir, şans
kritiği 0, Kartal tomarı 0 ve 7 (yakın silah aynı sayıda Kurt tomarıyla aynı çarpanı alır: `Zorluk.tomar_k`). Aynı
koşulda yakın silahlar (`--tomar --snh`): Alp Kılıcı 39,6 · İkiz Bıçak 34,2 · Ulu Kılıç 42,6 · Bozgun Kılıcı 35,6 SnH.

| Silah | Önce kart | Önce ölçülen | Sonra kart | Sonra ölçülen | Not |
|---|---|---|---|---|---|
| Türk Yayı (gec / tam) | 6,7 | 7,6 / 19,7 | 21,1 | 22,1 / 36,0 | sınırsız, %30 yavaş; tam bırakış = yakın silah düzeyi (beceri) |
| Akıncı Yayı (tut) | 7,8 | 16,4 | 25,9 | 28,4 | sınırsız, %35 yavaş |
| Sağanak Yayı (gec / tam) | 2,5 | 6,7 / 15,7 | 36,6* | 16,0 / 31,4 | 8 hak; 10 sn içinde haklar biter (ölçülen = sürekli) |
| Od Okları (gec) | 5,9 | 25,9 | 8,8 | 25,5 | 10 hak; gücü alev gölünden (`fire_pool`) |
| Tufan Yayı (gec) | 4,2 | 10,9 | 40,4* | 14,8 | 6 hak; geniş saçma 110 px'te yarısı ıskalar, yakında (dipten) kritik |
| Cirit | 9,2 | **0** | 21,2 | 20,8 | önce alçak düşmanın üstünden geçiyordu |
| Çoban Sapanı | 10,1 | **0** | 20,7 | 20,0 | aynı |
| Kartal Tüyleri | 6,3 | 15,0 | 26,0 | 22,9 | kart artık tüy sayısını sayar |
| Mancınık Taşı | 9,2 | **0** | 9,6 | 21,1 | önce 250 px'e sabit düşüyordu; "havadan" kritiği hep tutar (alan hasarı) |
| Kam Kopuzu | 5,5 | **0** | 18,6 | 20,0 | dalga tek noktaydı, alçak düşmanın üstünden geçiyordu; her şeyi deler |
| Yel Borusu | 3,1 | **0** | 8,8 | 8,4 | itme / sersemletme aracı; menzil 110 → 135 px |
| Gök Asası | 5,9 | 5,6 | 23,1 | 24,8 | tek hedef; zincirde her sıçrayış %90 |

\* cephaneli yayda kart dolu cephanenin patlama SnH'si (`Okculuk.kart_hiz`); sürekli atışta dolum hızı sınırlar.
7 Kartal tomarında aynı oran (ör. Türk 54,1, Akıncı 76,1, Gök Asası 66,8; Alp Kılıcı 7 Kurt tomarında 120,8).

Sonuç: tek hedefte uzak silahlar yakın silahın %50-75'i (Akıncı 28, Gök Asası 25, Türk 22; tam bırakışla Türk 36),
çok hedefte (delme, zincir, yelpaze, alan) daha fazla. Mesafe güvenliği için tek hedefte yakın silahın biraz altında.

### Hasar (`data/items.json`; taban x0,7 tomar ekonomisi aynen)

Türk 8 → 26 (kritik çarpanı 2,0 → 1,6: tam bırakış kesin kritik), Akıncı 7 → 16, Sağanak 4 → 15, Od Okları 6 → 8, Tufan
6 → 18, Cirit 12 → 26 (aps 1,1 → 1,3), Sapan 6 → 15, Kartal Tüyleri 5 → 8, Mancınık 22 → 24, Kopuz 6 → 19 (aps 1,4),
Yel Borusu 5 → 14, Gök Asası 7 → 22 (aps 1,2 → 1,5, sıçrayış 2-5 → 3-6). Yay "aps" değerleri artık gerçek atış turuna
yakın (kartın "Hız"ı `Okculuk.kart_tur`dan). Not: kilit açma bedeli (`Game.unlock_cost`) tabana göre 4-6 Kut arttı.

### Oynanış düzeltmeleri

* **Fırlatmada hedef yardımı** (`Player._uzak_nisan`): cirit ve sapan taşı yayın dikey nişanını kullanır
  (`Okculuk._aim_angle`, yerçekimi düşüşü dahil); önde kimse yoksa eski atış.
* **Mancınık balistiği**: öndeki en yakın düşmanın (300 px) üstüne düşecek yay (uçuş 0,4-0,95 sn).
* **Kopuz dalgası** dikeyde ±22 px vurur (`Projectile.hit_pad`); eskiden tek nokta.
* **Gök Asası** (`Player._gok_asasi`, `Player.GOK`): ilk hedef 230 px (önde, ±90 px dikey), zincir 150 px, sıçrayış başına
  %90 hasar, 0,35 sn sersemletme. Her 4. çakış **Gök Gürlemesi**: x1,6 hasar, +2 sıçrayış, 0,75 sn sersemletme, çift
  şimşek, sarsıntı ve yazı; sersemleyene sonraki yıldırım kritik (silahın koşulu). Hedef yoksa şimşek önündeki yere iner
  ve dibindekini çarpar. Hissi: gökten şimşek + zincir arkları + ışık + 40-60 ms duraklama + kamera itişi.
* **Çabuk yayda çift ok** düzeltildi: gerilme sürerken aynı basış ikinci kez sayılıyordu (Akıncı'da tek dokunuş iki ok);
  artık gerilirken yay basışı saklanmaz (`Okculuk.process` / `tick`).

### Cephane (Dead Cells esinli; `Okculuk` "CEPHANE")

Dead Cells'te çoğu yayın sınırlı oku vardır (deadcells.wiki.gg: Beginner's Bow 6, Multiple-nocks Bow 24 ok = 8 üçlü atış;
"LimitedAmmo" etiketi), oklar düşmandan / yerden geri alınır ve atış yokken zamanla dolar; bazı yaylar sınırsızdır.

| Yay | Cephane | Dolum (atmazken) | Not |
|---|---|---|---|
| Türk Yayı | sınırsız | — | gerilme 0,40 → 0,52, kilit 0,14 → 0,20 sn (tur +%30) |
| Akıncı Yayı | sınırsız | — | gerilme 0,12 → 0,16, kilit 0,08 → 0,11 sn (~3,4 ok/sn) |
| Sağanak Yayı | 8 atış | 1,5 sn'de 1 | |
| Od Okları | 10 atış | 1,2 sn'de 1 | tek ok ama her ok alev gölü bırakır |
| Tufan Yayı | 6 atış | 2,0 sn'de 1 | |

* Atış başına bir hak (yelpaze tek hak). Dolum atıştan 0,45 sn sonra başlar, gerilirken durur (`AMMO_WAIT`).
* Yerden toplanan ok (ok toplama) ve sökülen ok (ok sökme) anında bir hak verir; "hazır ok" kuralı aynen (cephane bitmişken
  hazır okla atış yine çıkar, hak harcamaz). Başka yay kuşanınca cephane dolu başlar.
* Boşken basış: **kuru tık** (boş kiriş + tık sesi, 0,22 sn bekleme, imler kızarır, yuva sıçrar), seyrek ipucu:
  "ok bitti · yerdeki okları topla" + "atmazsan N sn'de bir ok dolar". Kendiliğinden atış yok (v22).
* **HUD** (`HUD._draw_cephane`): yay yuvasının üstünde küçük mürekkep ok imleri: dolu kemik rengi, boş soluk, dolmakta olan
  hak aşağıdan yükselir; hak kazanınca sıçrar.

### Ok izi (`scripts/actors/OkIz.gd`, `shaders/ok_iz.gdshader`)

Eski iz vardı ama görünmüyordu: ok düğümünün kendi çiziminde koyu mürekkep kenarlı geniş şeritti; hızlı ok (650-1100
px/sn) hedefe 7-9 karede varıp silinince iz de anında kayboluyordu, koyu kenar karanlık zeminde eriyordu.

* İz artık ayrı düğüm (FX.root altında): ok saplanınca / düşmana değip yok olunca kalan noktalar yaşlanarak (0,07 sn)
  kuyruktan başa doğru incelip erir.
* Çok ince: yarı genişlik 0,34 (yarım gerilme) / 0,42 (tam) / 0,5 (tam bırakış) dünya birimi = 1080p'de ~2,3-3,4 px;
  kuyruğa incelir, kuru fırça kıllarıyla erir. Kenar yumuşatma piksel cinsinden (enine uzaklık / `fwidth`), pikselden
  ince kalan kısım kapsama oranında solar.
* Renk unsura göre: Od turuncu-kızıl, Ayaz buz mavisi, Yıldırım parlak mavi-beyaz (iz iki karede bir titrer), Kam mor,
  Yer-Su yeşil, tam bırakış altın, unsursuz koyu mürekkep + soluk kızıl çekirdek; kenarda ince mürekkep payı, başta hafif
  HDR. Od Okları unsursuzsa da od izi bırakır.
* **Unsur zerreleri** (`Unsur.parca`, mürekkep dokuları; piksel kare yok): od alev kıvılcımı, ayaz kırağı, yıldırım minik
  kıvılcım, kam ruh zerresi, yersu yaprak, altın yıldız. **Unsurlu ok sprite'ı** unsur rengine çalar (v20'de oklar unsur
  tetikliyordu ama görünmüyordu).
* Fırlatılan silahlar (cirit, Kartal tüyü, sapan / mancınık taşı, balta) aynı ince izle uçar (eski kalın çizgi yerine).

### Test

* `-- --tomar --boss --uzak [--snh_sn=10] [--snh_silah=a,b] [--uzak_px=110]`: yukarıdaki UZAK tablosu.
* `-- --yay --boss`: eski denetimler + CEPHANE satırları (çok oklu yayda haklar biter, boşken kuru tık ve ok çıkmaz,
  boşken ilk hak süresi, yerden toplanan ok +1 hak, boş cephane + hazır okla atış, Türk / Akıncı 16 basış → 16 ok),
  `CEPHANE_HATA=0`, `TAKILMA=0`. `--yay_cephane` yalnızca cephane denetimi.
* Görüntüler: `--yay --boss --pencere=1920x1080 --yay_goruntu=C:/mutlak/klasor` → `iz_sade|od|ayaz|yildirim|kam|yersu|altin`,
  `tufan_iz_cephane`, `cephane_bos`, `cirit_iz`, `gok_asasi`, `gok_gurlemesi` (+ eski yay görüntüleri).


## v25: gerçekçi mürekkep alevi ve doğa izi

Geri bildirim: "Doğa ve ateş unsurlu silahların mürekkebi çirkin. Gerçekçi alev olsun ama mürekkepli."

Eski hâli: od hilali normal kızıl fırça + üstüne serpilmiş çizgi roman alev dilleri (üç katmanlı sabit dil biçimi, hepsi
aynı; yaprak gibi duruyordu), Yer-Su açık yeşil hilal + pirinç tanesi gibi yapraklar. Hepsi aynı tek çizim çağrısında
kalarak yeniden yazıldı (`shaders/ink_brush.gdshader`, `scripts/core/InkTrail.gd`, `scripts/core/Unsur.gd`,
`scripts/world/FirePool.gd`). Yeni doku yok: gürültü gölgelendiricide yordamsal (HD paketi gerekmez).

### Od: gerçekçi mürekkep alevi

* **Alev türbülansı** `fire_n`: dünya biriminde değer gürültüsü fbm (4 oktav), ikinci bir fbm ile alanı bükülür (domain
  warp: diller kıvrılır, çatallanır), dikeyde 3 kat uzar (dik diller), zamanla yukarı akar (kaldırma, ~60 birim/sn).
  Dünya uzayında olduğundan komşu diller ve hilal aynı alanı paylaşır: üst üste binince tek alev örtüsü gibi okunur.
* **Sıcaklık rampası** `fire_ramp`: is → koyu kızıl → kızıl → turuncu → sarı → ak-sıcak (HDR, bloom eşiğini aşar);
  geçişler yumuşak cel bantları (gerçekçi ile mürekkep / çizgi stili arası).
* **Hilal = alev gövdesi** (`unsur_id` 1): şekil aynı v23 hilali, ama kuru kıl telleri yerine türbülansla yenir; iç kenar
  yukarı yırtılan alev dilleri, bıçak ağzının ötesinde gürültüden çıkan alev saçağı (od şeridinin dış payı 0,3 → 0,62,
  `OUT_EXT`, mürekkep kenarı `ink_w` ile aynı yerde kalır); bıçak ağzının içi ve taze kısım ak-sarı, içe doğru turuncu →
  kızıl, kenarlarda ince is konturu, kıl izleri soğuk bölgede is çizgisi. En taze baş türbülansla yırtılır (düz kapak yok).
  Ağırın arka katmanı soluk is (×0,35).
* **Alev dilleri** (zerre türü 3, yeniden): dik dörtgen (hilalin mürekkep bandından doğar, savuruşun ardına hafif yatar,
  kaldırmayla hızlanarak yükselir); yumuşak zarf + baskın türbülans (mum alevi gibi değil), dipte sıcak, tepede kızıl → is
  tutamına kopar; kontur dipte koyu kızıl, tepeye doğru is (iç kenarlar kesik çizgi gibi okunmasın diye yarı saydam);
  sıcak çekirdek kısmen toplamalı (üst üste binen diller parlar). Ömür 0,12-0,2 sn (hilal 2-4 karede söner, diller
  birkaç kare daha yükselip erir). Ağır silahta dil sıklığı ×0,7 ve boy ≤ ×1,1 (geniş hilal zaten alev; düşmanı örtmesin).
* **Kor** (yeni tür 8): hız yönünde uzayan kapsül (hareket bulanıklığı), titreyerek söner, yükselip savrulur (%30).
  **İs** (tür 6, od dalı): koyu, yarı saydam, gürültüyle yenen tutam (%10, alfa ≤ 0,38).
* **Vuruş efektleri:** tutuşma (`fx_ignite`) aynı alev dilleri + korlar + is + kısa sıcak ışık (eski CPU alev parçacıkları
  ve çizgi roman `Parca` alevi kalktı); yanan düşman (`Aura`, yalnızca od tutuşturunca) 0,11 sn'de bir gövdesini yalayan iki
  küçük dil (`fx_burning`); **alev gölü** (`FirePool`, tüm alev gölleri: Od Testisi, Kor Çekici, od unsuru bitirişi):
  kor yatağı (tür 10: kara mürekkep kabuk + nabız gibi atan kızgın çatlaklar) + döngüyle doğup yükselen ve tepeden kopan
  diller + yükselen korlar + seyrek is; tek çizim çağrısı, CPU parçacığı yok (v1 piksel dalı aynen).

### Yer-Su: yeşil-altın yaprak hilali ve sarmaşık

* **Palet 11:** koyu zümrüt gövde, altın kenar, krem-altın sıcak (`07120a 143c1a 2f7d34 d9c25c fff1b8`). Hilal
  (`unsur_id` 2) bir yaprak ayası gibi: mürekkebin ortasında altın orta damar, ondan uca doğru eğik yan damarlar; gövde
  açık orman zemininde okunsun diye koyulaştırıldı, ışıma yarıya indi.
* **Sarmaşık filizleri** (yeni katman 4 şerit, `add_vine`): hilalin mürekkep bandından fışkırır, 0,06-0,09 sn'de
  yavaşlayarak büyür, uca doğru sıkılaşan sarmalla kıvrılır; ortada ve uca yakın küçük yaprak tomurcukları açılır; 0,3-0,42
  sn'de uçtan dibe kuruyup (altın-kahveye döner) kopar. Koyu yeşil gövde, bir yanda altın ışık, mürekkep kontur.
* **Yaprak** (tür 7, yeniden): sivri uçlu yumurtamsı, ince dişli kenar, altın orta damar + yan damarlar, uca doğru altına
  çalar, dönerek salınır (enine ölçek cos ile: 3B dönüş, ters yüzde arka yüz), yaşlanınca sararır. **Çiçek yaprağı** (tür 9:
  krem-altın, uçta çentik) ve **polen** (tür 8: ağır süzülen ışıltı). Yer-Su izinde kıvılcım zerresi yok.
* **Vuruş efektleri:** kök (`fx_roots`) yerden fışkıran beş kalın mürekkep kökü (tür 1 şerit: koyu kahve-is kabuk, altın
  çizgi, boğumlar) + ince filizler + yapraklar, kök süresince durur, sonra kuruyup kopar; ayağa dolanan `Aura` kökleri aynı
  tonda; **diken zehri** (`fx_thorns`, yeni) vuruş noktasında kıvrılıp hemen kuruyan üç kısa filiz + polen; **yaprak şifası**
  oyuncunun çevresinde sarmal çizerek yükselen yapraklar + çiçek yaprakları + polen.

### Uyum, başarım

* Ayaz, yıldırım, kam değişmedi (aynı gölgelendirici dalları); yan yana çekimlerde od artık en uzun kalan değil (dil ömrü
  kısaltıldı). `InkTrail.burst(palet, unsur)` izsiz unsur efekti için havuzdan bir iz düğümü verir (aynı malzeme,
  `add_elem` / `add_vine`); `InkTrail.elem_material` başka düğümlerin (FirePool) aynı zerreleri çizmesi için.
* Maliyet: iz başına yine tek çizim çağrısı; alev pikseli başına 3 fbm (12 değer gürültüsü), yalnızca od piksellerinde.
  Zerre sayıları küçük (kılıç savuruşu ~15 dil + ~5 kor; Yer-Su ~8 filiz, şerit başına 20 köşe). Ölçüm (`--unsur_cekim=olcum`,
  2560×1440, `--doku=2`, savuruş boyunca 96 kare ortalaması; bu makinede taban ~33 ms kare zamanlamasına bağlı, fark
  anlamlı olan): GPU sade kılıç 33,26 / od 33,06 / Yer-Su 33,16 ms; sade ağır 33,37 / od 34,26 (+0,9) / Yer-Su 33,01 ms
  (karşılaştırma: yıldırım ağır 35,3, kam ağır 45,8 ms). CPU (iz + zerre işleme) sade 0,80 / od 0,83-0,84 / Yer-Su
  0,79-0,82 ms.
* Bilinen: ağır silahın yukarı süpürmesinde hilal geometrisi (v23) düz kapaklı geniş bir levha çizer (sade izde de var);
  od'da türbülansla yırtılıyor ama alev duvarı gibi geniş kalıyor.

### Test

`--unsur --boss --unsur_yalniz --anlik=<klasör> --unsur_cekim=vitrin,vitrin_tetik,vitrin_fx,olcum [--vitrin_unsur=od,yersu]`:
`vitrin` unsur × kılıç / ağır / hançer, temastan sonra 1/3/6/10. kare, oyuncu çevresi kırpık; `vitrin_tetik` od / Yer-Su
her vuruşta tetiklenerek; `vitrin_fx` tutuşma, kök, diken, şifa, alev gölü zaman dizisi; `olcum` GPU / CPU kare süresi.


## v25: ağır tempo ve akıcı vuruş duraklaması

Geri bildirim (oynayarak): "Saldırı hızı hâlâ çok yüksek; ciddi bir düşüş yapın. Özellikle küçük kılıç ve hançerler resmen
ışık hızında; dövüştüğümüzü hissetmeliyiz." · "Kritikte (ya da her neyse) bir anlık donma efekti daha akıcı olsun; oyun
takılıyor gibi." · "Kritik vuruş sesi tatmin edici olsun." · "Yıldırım Kılıcı'nın kombosu çok çirkin; sanatsal, güzel bir
şey yapın." · "Kombosu havaya zıplatan silahların kombolarını değiştirin."

### Ağır tempo (`Player.TEMPO_AGIR`, `Player.TEMPO_V25`)

v20 yavaşlamasının üstüne sınıfa göre ikinci bir katman (tek düğme `TEMPO_AGIR`: 0 = v24, 1 = v25). Sütunlar
`[ilk hazırlık ×, zincir hazırlığı ×, süpürme ×, kilit ×, toparlanma ×, + tutuş ilk, + tutuş zincir (sn)]`:

| Sınıf | çarpanlar | + tutuş | hedef (zincir aralığı) |
|---|---|---|---|
| hançer (ikiz bıçak, böri, pençe) | 1,6 / 2,0 / 1,3 / 1,2 / 1,2 | 17 ms | +%40-60 |
| Ay Palası (silaha özgü) | 1,6 / 2,4 / 1,3 / 1,4 / 1,2 | 17 ms | +%40-60 (her adımda Ay Dansı hızlanması var) |
| düello (yatağan, rüzgâr) | 1,5 / 1,8 / 1,25 / 1,2 / 1,2 | 17 ms | +%40-50 |
| kılıç | 1,35 / 1,5 / 1,2 / 1,18 / 1,15 | 17 ms | +%30-40 |
| mızrak | 1,2 / 1,4 / 1,15 / 1,18 / 1,1 | 12 ms | +%20-30 |
| kırbaç | 1,15 / 1,3 / 1,12 / 1,22 / 1,1 | 12 ms | +%20-30 |
| uzun sap | 1,12 / 1,32 / 1,1 / 1,26 / 1,1 | 12 ms | +%20-30 |
| ağır | 1,05 / 1,12 / 1,05 / 1,12 / 1,05 | 8 ms | +%10-15 |
| dev | 1,03 / 1,1 / 1,05 / 1,13 / 1,05 | 10 ms | +%10-15 |

Yalnızca süre uzaması değil, savuruşa ağırlık: her savuruşa okunur bir **hazırlık tutuşu** eklendi (bıçak geride bir an
durur, gövde toplanır; v14 tutuşu artık hançer ve kılıç zincirinde de var), **süpürme** 2-3 kareye çıktı (bıçak
"ışınlanmaz", yayı görünür), **kilit** (temastan sonraki oturma: vuruş → aşma → oturma) uzadı, girdisiz **toparlanma** biraz
daha görünür. İkiz bıçağın zincir boyunca hızlanması adım başına 0,07 → 0,04 (`DUAL_RAMP`). Basış→temas ölçülü uzadı:
hafif 100 → 150 ms, kılıç 133 → 167, mızrak 150 → 167, ağır 283 → 300, dev 383 → 400. Ara bellekler, iptaller ve v22
kontrolü aynı (kuyruk "zincir noktasına 0,16 sn kala / temastan sonra" olduğundan yeni sürelere göre kendiliğinden kayar;
`--kontrol` basılmamış=0).

**Saldırı hızı ve Kızışma "ışık hızını" geri getiremesin** (`Player.HIZ`, `items.json` "kizisma"): kalıcı kaynak üst
sınırı %40 → %25, Kızışma dahil %60 → %35; Kurt ongunu tomar başına %2 → %1,5, Yel Ana %15 → %10, Kam Davulu seviye
başına %4 → %3; sınıf etkisi hançer 1,0 → 0,7, düello 0,75, kılıç / mızrak 0,85, kırbaç 0,8, uzun sap 0,75, ağır 0,65,
dev 0,55 (oransal kısalma zaten en kısa evrelerde en çok hızlandırıyordu); en az kareler hazırlık 2 → 3, süpürme 1 → 1,5,
kilit 3 → 4. Kızışma: İkiz Bıçak +%3-5 × 6 → +%2-3 × 5, Böri +%3-5 × 5 → +%2-3 × 4, Kurt Pençeleri +%4-6 × 5 → +%2,5-3,5
× 4, Rüzgâr +%4-6 × 5 → +%2,5-4 × 4, Kement / Od Kamçısı +%5-8 × 4 → +%3-5 × 4 (tam yükte +%8-20; eskiden +%18-32).

Ölçüm (`-- --dovus --boss --hiz`, 60 Hz, ±1 kare, silahın taban aps'iyle, niteliksiz; "önce" aynı betik v24'te,
5b3007e). Son sütun: testin en yüksek saldırı hızı denemesinde (%40 istenir; v25'te %35'e kırpılır) basış→temas /
ortalama zincir aralığı:

| Silah | basış→temas (ms) | zincir aralıkları (ms) | ortalama | en hızlıda (önce → sonra) |
|---|---|---|---|---|
| ikiz_bicak | 100 → 150 | 150, 100, 200 → 200, 167, 300 | +48% | 83 / 117 → 117 / 183 |
| bori_hanceri | 100 → 150 | 150, 117, 133 → 200, 200, 183 | +46% | 83 / 100 → 117 / 167 |
| kurt_pencesi | 67 → 117 | 250, 133, 150 → 317, 233, 233 | +47% | 50 / 139 → 83 / 206 |
| ay_palasi | 67 → 117 | 250, 133, 117 → 383, 217, 183 | +57% | 50 / 133 → 100 / 217 |
| yatagan | 117 → 167 | 183, 183, 233 → 283, 283, 317 | +47% | 83 / 150 → 133 / 211 |
| ruzgar_kilici | 117 → 167 | 183, 233, 233 → 283, 317, 333 | +44% | 83 / 161 → 133 / 234 |
| alp_kilici | 133 → 167 | 217, 267, 283 → 300, 367, 367 | +35% | 100 / 183 → 133 / 250 |
| pala | 133 → 167 | 217, 233, 433 → 300, 317, 550 | +32% | 100 / 206 → 133 / 284 |
| ruh_kilici | 133 → 167 | 217, 250, 283 → 300, 350, 367 | +36% | 100 / 178 → 133 / 250 |
| yilan_kilici | 133 → 167 | 217, 267, 283 → 300, 367, 367 | +35% | 100 / 178 → 133 / 250 |
| ayaz_kilici | 133 → 167 | 267, 283, 267 → 367, 367, 367 | +35% | 100 / 194 → 133 / 261 |
| yildirim_kilici | 133 → 167 | 217, 283, 317 → 267, 433, 417 | +37% (yeni zincir) | 83 / 189 → 133 / 278 |
| kargi | 150 → 167 | 200, 250, 250 → 250, 283, 317 | +21% | 100 / 167 → 150 / 228 |
| tulpar_mizragi | 150 → 167 | 200, 250, 283 → 250, 283, 350 | +20% | 100 / 172 → 150 / 239 |
| kement | 183 → 200 | 300, 317, 300 → 383, 383, 383 | +25% | 133 / 217 → 183 / 306 |
| od_kamcisi | 183 → 200 | 250, 300, 317 → 317, 383, 383 | +25% | 133 / 211 → 183 / 295 |
| teber | 200 → 217 | 300, 350, 367 → 367, 450, 467 | +26% | 150 / 250 → 183 / 333 |
| erlik_tirpani | 200 → 217 | 300, 300, 533 → 367, 383, 667 | +25% | 150 / 278 → 183 / 378 |
| kayin_asasi | 200 → 217 | 267, 517, 367 → 317, 650, 467 | +25% | 150 / 278 → 183 / 372 |
| gurz | 283 → 300 | 450, 567, 450 → 500, 617, 533 | +12% | 233 / 372 → 250 / 456 |
| civili_topuz | 283 → 300 | 383, 567, 450 → 417, 633, 533 | +13% | 233 / 361 → 250 / 428 |
| savas_baltasi | 283 → 300 | 450, 450, 450 → 500, 533, 500 | +14% | 233 / 339 → 250 / 422 |
| ikiz_balta | 300 → 300 | 367, 400, 667 → 433, 450, 750 | +14% | 233 / 366 → 250 / 444 |
| ulu_kilic | 383 → 400 | 533, 883, 550 → 600, 1017, 600 | +13% | 317 / 528 → 333 / 617 |
| bozgun_kilici | 367 → 367 | 467, 933, 633 → 517, 1017, 683 | +9% | 300 / 539 → 300 / 633 |
| dag_cekici | 383 → 400 | 583, 633, 600 → 650, 717, 650 | +11% | 317 / 478 → 333 / 561 |
| kor_cekici | 367 → 383 | 617, 633, 617 → 667, 700, 667 | +9% | 300 / 489 → 317 / 583 |

Kart (`ItemGen.dps`, aynı tempo çekirdeği): İkiz Bıçak 9 → 6 vuruş/sn, Alp 4,1 → 3,0, Kargı 4,5 → 3,5, Gürz / Ulu Kılıç
2,1 → 1,9. `--tomar --boss`: kart ↔ ölçülen SnH koşulsuz silahlarda en büyük fark %5,9 (sınır %7; GEÇTİ). Yıldırım
Kılıcı artık kartla örtüşüyor (önce −6 / −69 / −39 %: geri sıçrayış oyuncuyu menzilden çıkarıyordu; şimdi −3,5 / −1,5 /
+0,1 %). Yatağan ölçülen > kart (+%50; önce −%34): yerde kalan geri çekilme kesiği artık isabet ediyor, kart bu koşul
silahında zincirin bir turunu uzun sayıyor (koşul silahları sınır dışında; bilinen).

**Oyuncu SnH'sine etkisi** (`--denge --denge_muhur=0`; düşman canlarına dokunulmadı): boss satırlarında tipik SnH ~%18-23
düştü (Kara Börü Han 66,6 → 54,5, Tepegöz 117,6 → 92,9, Şahmeran 188,5 → 148,2, Yelbegen 252,4 → 198,3, Erlik Han 320,6 →
247,2); boss süresi (isabet payı %45) 78-83 → 100-106 sn, tomarsız 125-352 → 153-456 sn. Vuruş SAYILARI (yaratık başına,
tipik / başlangıç silahı) aynı ya da ±1-2: yaratıklar aynı sayıda vuruşta ölüyor, yalnızca daha uzun sürede. Ekonomi
ajanının can sayıları değişmedi; boss süreleri istenirse can ×0,8 ile v24'e döner (karar tasarımın).

### Akıcı vuruş duraklaması (`Game.HS`, `_add_dip`, `_dip_now`)

"Takılma" hissinin ölçülen sebepleri: (1) `Game.hitstop` zaman ölçeğini tek karede 1 → 0,05'e indiriyor, süre bitince tek
karede 1'e çıkarıyordu — sert durma + sert kalkış, her kritik / bitirişte bir "atlama"; (2) aynı karede ya da art arda gelen
duraklama ve ağır çekimler (vuruş + kritik + öldürüş: oyuncu 105 + 30 ms, düşman ölümü 60 ms + ağır çekim 0,3 / 140 ms)
basamak basamak 0,05 → 0,3 → 1 zıplıyor, çok vuruşlu savuruşta her geçiş donmayı yeniden başlatıyordu; (3) kamera itişi
(9 px'e dek) ve yakınlaşma tek karede sıçrıyordu; (4) darbe karesi (`ImpactFrame`) iki kare kararıp tek karede kayboluyordu.
Fizik / süreç uyumsuzluğu yok (Godot 4'te zaman ölçeği fizik adımını değil fizik deltasını küçültür; fizik 60 Hz sürer),
ses perdesi zaman ölçeğine bağlı değil.

* **Dip eğrisi:** her duraklama / ağır çekim `[dip, başlangıç, dip sonu, bitiş]`. Ölçek anında dibe iner (vuruş sert
  okunur), dipte durur, sonra smoothstep ile 1'e döner (türev iki uçta 0: kalkış görünmez). Duraklama: dip 0,1 (eski 0,05),
  sürenin %50'si dipte, dönüş süre × 0,9 + 30 ms. Ağır çekim: %55 dipte, dönüş en çok 0,2 sn. Etkin diplerin her an en
  yavaşı geçerli; süren bir dibin kapsadığı yeni çağrı eklenmez (yeniden başlama yok).
* **Art arda sığlaşma:** 0,25 sn içinde gelen her yeni duraklamanın dibi 0,12 yükselir (en çok 3 adım).
* **Kayıp zaman sınırı:** 1 sn'lik pencerede duraklama + kısa (≤ 0,25 sn) ağır çekimlerin toplam kayıp oyun zamanı en çok
  0,2 sn; aşan çağrı kısalır ya da düşer. Uzun anlatı ağır çekimleri (boss ölümü, âlem) sayılmaz.
* **Kamera:** itiş ve yakınlaşma artık hedef; kamera hedefe 2-3 karede varır, hedef üstel söner (tek karede sıçrama yok).
  Kamera, arayüz, ses ve çizim düğümleri gerçek zamanda akar (`process_mode` ALWAYS, `delta / ölçek`).
* **Darbe karesi** 1 tam kare + 90 ms gerçek zamanlı yumuşak sönüş (eski: 2 kare, sert kesilme).
* **Kritik vurgusu** (`Player._crit_accent`): sade — kamera yumuşakça %2,4-3,8 yaklaşır, darbe noktasından vuruş yönünde
  ince beyaz kesik çizgisi + silah renginde kısa çapraz çizgi. Büyük kademe duraklaması 105 → 90 ms.
* Test için `Game.hs_eski` (v24'ün sert davranışı) ve `Game.hs_log`.

Ölçüm (`-- --dovus --boss --takilma [--takilma_eski] --pencere=1280x720`, gerçek zamanlı, headless değil; üç düşmana her
savuruşun son anında basılan, her isabeti kesin kritik kombo, silah başına 4 sn; iki koşunun aralığı):

| Silah | kare başına en büyük ölçek artışı | sert çıkış (<0,3 → >0,9 tek karede) | dibe yakın kare (≤0,12) | yeniden donma | kayıp oyun zamanı |
|---|---|---|---|---|---|
| İkiz Bıçak | 0,95 → 0,28-0,52 | 5-6 → 0 | 34-45 → 8-9 | 4 → 2 | 169-172 → 60-62 ms/sn |
| Alp Kılıcı | 0,95 → 0,32-0,37 | 8-10 → 0 | 80-82 → 22-25 | 0 → 0 | 274-276 → 176-180 ms/sn |
| Yıldırım Kılıcı | 0,95 → 0,19-0,30 | 4 → 0 | 38-40 → 10 | 2 → 0-1 | 132-137 → 65-68 ms/sn |
| Dağ Çekici | 0,95 → 0,27-0,30 | 5 → 0 | 44-45 → 18-21 | 1 → 1-2 | 149-151 → 134-150 ms/sn |

Gerçek kare süresi iki sürümde aynı (p50 12,5-13,4 ms, p99 19-32 ms; ilk koşulardaki 150-340 ms'lik sıçramalar makinedeki
paralel yükten: aynı kip art arda koşularda kayboldu, iki kipte de rastgele görüldü).

### Kritik vuruş sesi (`tools/audiogen/v25.py`, `Ses.hit`)

Eski kritik 45 ms'lik ters yükselişle başlıyordu (geçiş vuruş karesinden sonra; yumuşak duraklamayla "geç ve bulanık"),
çan katmanı uzun bir "dong" idi. Yeni ses dört katman, geçiş t=0'da: (1) **keskin metal geçişi**: 2-15 kHz tık + bıçak
kaydı (Kenney RPG knifeSlice, CC0) + 3,6-4,4 kHz hızlı sönen inharmonik çelik tonları ("tsing"); (2) **derin gövde**:
yumruk kaydı (Kenney Impact impactPunch_heavy, CC0) + perdesi 122 → 46 Hz düşen, hafif doyurulmuş alt bas (6 ms
gecikmeli, tıktan hemen sonra oturur); (3) **parlak ışıltı kuyruğu**: müzikle aynı dizide iki notalı kısa çan (E6/B6,
D6/A6, E6/D7, B5/E6) + temelinin yanında 5-7 Hz vuran ikiz (titreşen parıltı) + 3-9 kHz hava, ~0,4 sn'de söner; (4) küçük
oda. Dört bıçak çeşidi (`darbe_kritik_1..4`) + künt silah çeşidi (`darbe_kritik_kunt_1..3`: kayıt yok, 100 → 38 Hz
tok gövde, çatırtılı kırılma, 1,7 kHz çelik, A5/G5/B5 çan; gürz, çekiç, topuz `Ses.hit(2, pos, "kunt")`). Ses.play ±%5
perde oynatır. Karışım: kategori hedefi −8 dB (sıradan darbe −10 / −10,5), `HIT_TIERS` kritik 0 dB → normal vuruşun ~4-5 dB
üstünde. Kritik öldürüşte de kritik sesi çalar, altında −8 dB öldürüş sesi (eskiden öldürüş sesi kritiği yutuyordu).
Yeniden üretim: `python tools/audiogen/export_audio.py --sfx darbe_kritik darbe_kritik_1 ... darbe_kritik_kunt_3`.

### Yıldırım Kılıcı (`Player.YK`, `scripts/core/SimsekKesikFX.gd`)

Eski zincir (çekiş → geri sıçrayış → saplama) dağınıktı ve ikinci adım oyuncuyu havaya hoplatıyordu. Yeni zincir v23
düzlemleriyle:

1. **Çekiş** (`yk_iai`): el kalçada, bıçak kında geriye-aşağı; tek hamlede çok yassı yatay elipste (phi 102°, r 0,24)
   ~3,2 rad'lık geniş hilal, takipte bilek döner. Bıçak ucunun yolunda şimşek parlaklığında yay (`SimsekKesikFX.arc_live`:
   ön uçta kalın beyaz çekirdek + mavi parıltı, kuyrukta kıl inceliği, yay boyunca titreyen kılcal şimşekler); süpürme
   bitince söner (takip yayı uzatmaz).
2. **Şimşek Çaprazı** (`yk_cross`, iki vuruş × 0,55): baş üstünden öne-aşağı (48°) ve alttan öne-yukarı (132°) iki dik
   kesik; her geçişin kendi parlak yayı, ikinci kesik birincinin önünden geçerken kesişme noktasında çıtırdayan mürekkep
   kıvılcımları (kısa şimşek dalları + kıvılcım + ışık).
3. **Şimşek Çekişi** (`yk_flash`, bitiriş): bıçak kına iner, gövde derin çömelir (okunur tutuş); bırakışta bıçak tek karede
   yatay açılır ve gövde yerde 75 ms'de 84 px ileri atılır (düşmanın içinden geçer, kısa dokunulmazlık). Geçtiği yol
   ekranı bir an ikiye bölen kesik çizgisiyle parlar (`SimsekKesikFX.line`: 2 karede koşan beyaz çekirdek, mavi parıltı,
   iki yanında açılan mürekkep yarığı, ekranın iki ucuna uzanan 0,12 sn'lik soluk yarık, kılcal şimşekler); bu adımda
   bıçak izi çizilmez. Vurulan her düşmanın tepesinde 0,16 sn sonra **gecikmeli gök çatırtısı** — yalnızca görsel ve ses
   (şimşek, kıvılcım, ışık, kısık çatırtı, hafif sarsıntı): ek vuruş / hasar yok, hasar oyuncunun kendi vuruşunda (v22).
4. **Yıldırım Hamlesi** (ağır): v21 aynı (tam şarjda deldiği düşmanlara yıldırım); şarj ederken bıçak boyunca şarjla
   uzayan kılcal şimşekler, hamlenin yolunda aynı kesik çizgisi.

Kare şeritleri: `-- --firca=yildirim_kilici --firca_kombo --anlik=<klasör> --pencere=1920x1080` (`--fixed-fps 60`).

### Havaya zıplatan kombolar → yerde

| Silah / hamle | önce | sonra |
|---|---|---|
| Yıldırım Kılıcı zincir 2 | geri sıçrayış (−150 px/sn hop) | Şimşek Çaprazı (yerde) |
| Rüzgâr Kılıcı zincir 2 | geri sıçrayış (hop) | ters el kesiği (`back`, yerde); 3. adım yükselen kesik düşmanı kaldırır, oyuncu yerde |
| Yatağan zincir 3, Ay Palası zincir 4 | geri sıçrayış (hop) | geri çekilme kesiği yerde kayar (175 px/sn, dikey hız yok; havada başlarsa eskisi gibi) |
| Ağır saldırı bırakışı (çakmalı: Alp Darbesi, Buz Yarığı, Balta Yarığı, Gürz / Çivi / Dağ / Kor / Ulu / Bozgun çakışları, varsayılan ağır) | −300…−420 px/sn sıçrayıp çakma | yerde: ön ayağa yüklenen kısa adım (50-120 px/sn) + gövde basıncı; yer şoku aynı |

Yön tuşlu ayrı hamleler değişmedi: ↑+J Göğe Savur / Sırık Atlayışı, havada ↓+J Kartal Dalışı, Kurt Pençeleri'nin havadan
sıçrayışı (yalnızca zaten havadayken).

### Ağır silahın yukarı süpürmesi: dar, ucu kancalı hilal

Aparkat (`uppercut_2h`: Dağ Çekici, Çivili Topuz, Ulu Kayın Asası, ağır silahta ↑+J) v23 hilalinde geniş, üst kenarı düz
bir "levha" çiziyordu (od unsurunda alev duvarı gibi): kol ve baş aynı doğrultuda dönüyor, ağır fırçanın geniş tabanı
(bıçak boyunun %105'i) yükselen yayda bıçağın kendisiyle paralel kayıyordu. Düzeltme: düzlem 134°/0,48 → 142°/0,33-0,4
(dar, eğik elips), baş hazırlıkta bilekten geri kalır (w −0,42), temasta bilek öne geçer (+0,35), takipte bilek kıvrılır
(+1,15: uç kanca), ve bu savuruşta mürekkep hilalinin eni ×0,55 (`Player.UPSWEEP_THIN`; Kor Çekici'nin sürükleyip
kaldırması `ground_drag` ×0,7). Vuruş kutusu ve zamanlama aynı.

### Test

`--dovus --boss` (TAKILMA=0, KONTROL basılmamış=0 oto_dönüş=0 oto_hamle=0 istenmeyen_ağır=0; boşta denetimi 1,5 → 2 sn:
ağır tempoda dev silahın son basıştan açılan meşru savuruşu ~1 sn), `--kontrol`, `--yildirim` (tam şarj: iki şimşek
düşmanlara 2 px; kısa şarj 0), `--hiz` (en az kare ihlali 0), `--v19`, `--savurus`, `--tomar --boss` (GEÇTİ),
`--denge --denge_muhur=0`, `--otomatik --derinlik=1/5 --muhur=0`, `--mekanik --muhur=0`, `--piksel_tara` (TOPLAM 0):
betik hatası 0. Yeni: `--takilma [--takilma_eski]` (yukarıdaki tablo).

## v25: harita, tuzaklar, Üç Âlem'in kaldırılması

Geri bildirim (oynayarak): "Yeraltına inme / bulutlara çıkma mekaniğini kaldır. Harita biraz daha geniş olmalı; Shift
ile (yuvarlanarak) geçmen gereken çok dar yerler var. Bazı yaratıklar büyük ve doğdukları yerler çok dar. Haritadaki
diken çukurları değer değmez hasar veriyor, içine düşünce sürekli vurduğu için çıkmak zor; yaratıklar da içine
yürüyor. Tepegöz'ün lazeri alakasız bir yerden çıkıyor, gözünden çıkmalı."

### Üç Âlem kaldırıldı

* Silinenler: `scripts/world/Alem.gd` (gizli yeraltı odaları, ruh taşı kapakları, Ülgen'in bulut basamakları, ruh kuşları,
  Erlik'in gölge ruhları, âlem kaplaması), `shaders/alem.gdshader`, `alem_gok` / `alem_cikis` sesleri, `alem` girdi
  eylemi (T / LT boş), `Game.LAYER_GOK` / `LAYER_HAYALET` çarpışma katmanları (oyuncu ve yaratık maskesi artık dünya +
  platform), `Player.realm` / `kam` ve `_enter_realm` / `_exit_realm` / `_set_realm`, `Enemy.realm` (hasar / sürü
  çağrısı / hedef yardımı / okçuluk / bot süzgeçleri), `Ses.alem_mix` (yeraltında boğuk müzik), HUD kam halkası (don
  halkası onun yerine kaydı), âlem başlığı, öğretici kartları (`kam_hazir`, `kapak`, `gok`, `yer`, `kus`), yeraltı
  kapağı / ruh kuşu dünya işaretleri, başlık ve duraklatma ekranı tuş satırlarındaki "T kam transı", `Pickup` "ruh_kusu"
  türü ve `loot_open` süzgeci, Unsur Kam'ın yeraltı çarpanı (`kam_yer` ×1,5), öldürme başına +8 kam gücü.
* **Erlik Han 3. evre** artık **Tamu Seli** (`tamu_seli`; eski adı "Âlem kayması"): Üç Âlem'e hiç bağlı değil; zemin lav
  olur, arenanın üç taş platformu güvenli, ardından platformlara kor yağar. Ses `alem_yer` → `tamu_seli`
  (`tools/audiogen/v12.py`), yazılar "TAMU TAŞIYOR — PLATFORMLARA ÇIK!" / "KOR YAĞIYOR — AŞAĞI İN!".
* **Kam Ata** destanı (kayıt kimliği aynı): "Don kılığında 30 saniye savaştı" → don kılığında +%25 hasar (eskiden öbür
  âlemde 30 sn, kam gücü yavaş tükenir).
* **Ganimet yeniden dağıtıldı** (`Level._spawn_kesif`): Üç Âlem bölüm başına en çok iki gizli oda (bir üst kademe eşya +
  şifa + 6 altın) ve %70 Ülgen sunağı (bir üst kademe eşya) veriyordu. Şimdi her bölümde girişten **ulaşılabilen**
  (`LevelGen.reach_set`) yüksek bir çıkıntıda (ada, kule, sütun tepesi; yüzeyden en az 3 karo yukarıda, en yükseklerden
  rastgele) bir üst kademe eşya kaidesi + şifa + 4 altın; %50 ihtimalle yolda ikinci bir zula (eşya + 3 altın).
  Kaidelere, oda işaretlerine, tüccara uzak. Ölçüm: bölüm başına ortalama 5 eşya kaidesi (`--harita`).
* `grep -ri alem` (yurt çadırının "tuğ alemi" sanat aracı dışında) boş; `ruh_tasi_v2` / `bulut_*_v2` dokuları atlasta
  kullanılmadan duruyor (HD paket manifestleri bozulmasın diye silinmedi).

### Daha geniş harita, yuvarlanmadan yürünen yollar (`LevelGen.gd`, `Level.gd`)

Ölçüm aracı `-- --harita` (`tools/tests/harita_testi.gd`): girişten (`LevelGen._moves` modeli) ulaşılan her ayakta durma
hücresinin **baş boşluğu** (üstündeki katı olmayan karo; platform kesmez), yalnızca yürüyerek (baş boşluğu >= 2 / >= 3)
Kut Kapısı'na yol olup olmadığı ve ana yolun en dar yeri. Sürünme geçitlerinin nereden geldiği (eski kod):

* `surunme` parçası (1 karo yüksek, 8 karo uzun tünel), mağara "alçak geçidi" (tavan 1 karoya iner);
* `sutunlar`, `merdiven` duvarı, `kule`, `sunak` kaidesi, `seckin` sütunları, `hazine` duvarları: hepsi havada asılıydı,
  altlarında 1 karo (yalnızca yuvarlanarak) boşluk kalıyordu; `basamak` blokları ve mağara sarkıtları 2 karo bırakıyordu;
* `_ensure_path` düz / inişte yalnızca bel hizasını açıyordu ("en kötü 1 karo yuvarlanma"), adalar zeminden 6 karo
  yukarıda 2 karo boşluk bırakabiliyordu; kurgan mezar odası 2 karo yüksekti.

| parametre | önce | v25 |
|---|---|---|
| bölüm genişliği `Level.W` | 230 karo | **256** (eşya kaideleri 38 / 116 / 188, tomarlar 64 / 144, tüccar alanları `tuccar.json` orta 78-190, kapı 194-238) |
| en az baş boşluğu | yok (1 karo sürünme olağan) | **3 karo** (72 px; oyuncu 40 px) her yürünen hücrede: `LevelGen.BAS_BOSLUGU`, `_open_headroom` |
| tünel parçası | `surunme` 1 karo | `tunel` 3 karo (üstünden de geçilir) |
| sütunlar / merdiven / sunak / seçkin | havada, altı 1 karo | yere oturur (2-3 karo; zıplanır) |
| kule | altı 1 karo | altında 3 karo geçit |
| basamak | katı blok, altı 2 karo | tek yönlü platform |
| hazine odası | kapalı kutu, eşya oda **çatısına** düşüyordu | iki yanda 3 karo kapı, eşya içerideki ahşap rafta (işaretler `_stamp` konumundan: `Level._floor_below`) |
| kurgan mezarı | 2 karo | 3 karo (`CHUNK_SINK` 4) |
| mağara tavanı / sarkıt altı / dar boğaz | 4-6 / 2 / 1 karo | 5-7 / 3 / 3 karo |
| harabe kuyusu / zikzak platform | 6 / 2 karo | 8 / 3 karo |
| derin çukur genişliği | 3-5 | 4-6 |
| ada yüksekliği (zeminden) | 6-8 | 7-9 |
| `_ensure_path` baş boşluğu | 2 (yükseliş) / 1 (düz) | 3 / 3 |
| parça düzlemesi | yalnız parça sütunları | + iki yanda 3 sütun önlük (yandaki basamak oyması odanın duvarını yemesin) |
| erişim modeli `_moves` | platform başı ve yörüngeyi keser | tek yönlü platform kesmez (içinden zıplanır); üst üste platform yığan gereksiz çıkmaz onarımı kalktı |
| giriş düzlüğü | çıkmaz onarımı giriş hücresini doldurabiliyordu | `_start_pad`: 1-12. sütun her zaman açık |

Ölçüm (aynı yeni modelle, 6 stil × 20 tohum = 120 bölüm; önce = v24 üreticisi, W 230):

| | önce | v25 |
|---|---|---|
| ana yol en az 3 karo baş boşluğuyla | 112 / 120 (8'inde 2 karo) | **120 / 120** |
| ana yolun en dar yeri | 2 karo | **3 karo** |
| girişten ulaşılan "yalnızca yuvarlanarak" (1 karo) hücre | 1654 (120 bölümün hepsinde, bölüm başı ~14) | **0** |
| 2 karoluk (eğilerek) hücre | 682 | **0** |

(Eski modelle — platform katı sayılarak — v24 üreticisinde 60 bölümün yalnızca 52'si yuvarlanmadan geçiliyordu.)

### Yaratıklar sığdıkları yerde doğar (`Level.spawn_enemy(..., check)`, `spawn_ok`, `find_spawn`)

Bölüm yerleşiminde (`_spawn_enemies`, seçkin odası) her yaratığın gövdesi = çarpışma boyu × görsel ölçek (seçkin 1,3,
öfkeli 1,1) + 6 px baş payı **katı ya da tehlike karosuna girmez**; yerdekinin ayaklarının altı boydan boya yürünür, aynı
satırda gövde + her yanda 1 karo düz ve üstü gövde boyu açık alan olmalı (Ağaç İyesi / Dev Çocuğu / Tozkoparan 34×74,
seçkinde 44×96; tosbağalar 58×30; bekçiler 26×58). Sığmıyorsa ±18 sütunda (aynı yüksekliğe en yakın zemin önce) sığan
yere taşınır; hiç yer yoksa konmaz (`spawn_skipped`). Pusucuların yüksek yer seçimi ve uçanların havada doğuşu aynı
denetimden geçer.

Ölçüm (`--harita`, derinlik 1-9 × 6 bölüm; denetim test tarafında bağımsız: gövde duvar / tavan / tehlike içinde mi,
ayak altı boş mu):

| | önce (v24) | v25 |
|---|---|---|
| geçersiz yerleşim | **277 / 895** (%31: duvar 127, tavan 59, zemin yok 66, tehlike 25) | **0 / 1014** |
| katı karodaki eşya / tomar / sunak | 10 | 0 |
| taşınan / konmayan | — | 312 (%31) taşındı / 0 konmadı |
| tüccar duvar denetimi | duvar_ok | duvar_ok |

### Tehlike çukurları (Dead Cells gibi; `Player._hazard_check`, `Enemy._hazard_tick`, `scripts/world/Tuzak.gd`)

* **Oyuncu**: dikene / zehre / lava değince **tek vuruş** (azami canın %8 / %6 / %14'ü, eskisi gibi) ve **geldiği yana**
  (son güvenli zemine doğru) **yukarı sektirilir** (470 px/sn; yatay hız iniş noktası çukurun dışına düşecek biçimde
  `Level.pit_exit`ten hesaplanır), 0,42 sn yön tuşu hızı ezmez, 0,8 sn dokunulmazlık. Çukur 0,6 sn yeniden vurmaz
  (eskiden içindeyken 0,7 sn'de bir vuruyor, geri tepme yüzün tersine 120 px/sn kalıyordu: çıkmak zordu). 1,6 sn
  içinde yine düşersen (geniş çukur, geri sekme) **hasarsız** son güvenli zemine (`Level.safe_ground`: altı yürünür,
  bir karo çevresinde tehlike yok) ışınlanırsın. Yuvarlanırken dokunulmazlık aynen; buz hasarsız (kaygan).
* **Yaratıklar**: tehlike karosu uçurum kenarı sayılır (`Enemy._haz_ahead`, `_blocked` ve `_wall_or_ledge` içinde): devriye,
  kovalama, hücum ve kaçış çukura yürümez. İtilip düşen yaratık **bir kez** azami canının %12'si kadar vurulur ve en yakın
  kenara sektirilir (sektirme sırasında yapay zekâ bekler), 1,2 sn yeniden vurulmaz. Uçanlar ve bosslar etkilenmez.
* **Uyarı (mürekkep)**: her çukur şeridinde ağzından 6-9 px dışarı taşan kara demir diken sırası, uçları pas kızılı ve
  nabız atar (arkada koyu, önde açık sıra); iki dudakta eğik kazık ve zeminde üç kızıl fırça çentiği (zehir / lav / buzda
  yalnızca çentikler). Değilen yerde dikenler 0,28 sn beyazlayarak 12 px fırlar (`Level.hazard_jab`), toz ve kısa ses.
* Test (`--mekanik --tohum=1`): ilk temas hasar %8, sektirme vy -416 / vx -110, 1,1 sn sonra ek hasar 0, çukurun dışında
  ve yerde; ikinci düşüş hasar 0, güvenli zemine; yaratık tek vuruş %12, çukurun dışında. Kare dizisi: `--harita_ekran=tuzak`.

### Tepegöz'ün göz ışını gözden çıkar (`Boss._tg_eye`, `Isin.follow`, `tools/artgen/goz_capasi.py`)

* Eskiden göz konumu tahmindi (`facing × 30, -boy × 0,67`; sprite'ta çapa yoktu): v2 çiziminde göz 17 px önde ve 32 px
  yukarıdaydı; üstelik ışın hazırlıkta ve duraklamada konumunu güncellemiyordu, "cast" karelerinde göz 26 px oynarken
  ışın eski yerinde kalıyordu.
* `goz_capasi.py` her animasyon karesinde sprite'ın ışıma sayfasındaki göz parıltısını ("mouth" çapasının üstündeki
  pencerede en yakın parlak bileşenin ağırlıklı merkezi) bulur ve json'a `eye` çapası yazar: `tepegoz_v2` 33 / 35 kare
  ölçüldü (gürz kolunun gözü örttüğü 2 karede ortalama göz - ağız farkı), v1 `tepegoz` 30 / 35. `_tg_eye` bu çapayı yöne
  göre aynalar, görsel ölçek (ezilme / esneme) ve eğilme açısıyla döndürür; `Isin.follow` ile ışın her karede (nişan
  çizgisi, ışın, 3. evrede gidip gelen taramanın duraklaması) gözden çıkar ve hedefe yeniden nişan alır.
* Doğrulama (`--harita_ekran=tepegoz`, 2. ve 3. evre, sağa / sola): 54 örnekte ışın başı ile göz çapası farkı 0 px;
  çekimlerde ışın her iki yönde ve taramada gözün içinden çıkıyor.

### Bot ve kapı

`--otomatik [--bot_gercek] --derinlik=N --muhur=0` (6600 kare), bölüm sonu `HARITA` satırı:

| derinlik | ölçüm botu (`--bot_gercek`) | eski bot (`--otomatik`) |
|---|---|---|
| 1 | bitti 58,0 sn · takılma 1 · alçak tavan 0 · çukur 1 | bitti 49,3 sn · takılma 1 · alçak tavan 0 |
| 3 | bitti 56,1 sn · takılma 4 · 0 | bitti 49,4 sn · takılma 2 · 0 |
| 5 | bitti 67,8 sn · takılma 4 · 0 | bitti 49,7 sn · takılma 3 · 0 · çukur 1 |
| 7 | bitti 77,4 sn · takılma 4 · 0 | bitti 52,6 sn · takılma 0 · 0 |
| 9 | bitti 63,0 sn · takılma 3 · 0 | öldü 23,7 sn (v23'ten bilinen: başlangıç donanımlı eski bot 9. derinlikte ölür) |

"Takılma" = duvara / basamağa 1,2 sn'den uzun dayanma (bot yalnızca sağa yürür, takılınca zıplar); "alçak tavan" =
ayağa kalkılamayan yerde geçen kare (kurt / don / yakalanma dışında): **hiçbir koşuda yuvarlanma gerekmedi**. İlk
koşuda 7. derinlikte ölçüm botu Kut Kapısı'nın üstünden zıplayıp bölüm sonundaki duvara takılmıştı: kapı artık kemeri
boyunca (yerden 96 px'e dek) geçişte açılır (`Level._process`; eskiden ayak noktası 30 px yakın olmalıydı).

### Test

* `-- --harita [--harita_tohum=N] [--harita_bolum=K] [--harita_w=230]`: IZGARA (stil başına yürüyerek / 3 karo / en dar /
  yuvarlanma hücresi, onarım ortalamaları) ve BOLUM (derinlik başına düşman, geçersiz, seçkin, taşınan / konmayan, eşya
  kaidesi, katıdaki eşya, tehlike karosu, tüccar duvar) tabloları; `SONUC GECTI|KALDI`. Çekim kipleri (headless değil,
  `--harita_cikti=<klasör>`): `--harita_ekran=genis | tuzak | tepegoz`.
* `--otomatik` bölüm sonu satırı: `[otomatik] HARITA derinlik= genişlik= takılma= alçak_tavan_kare= çukur_değme=
  düşman_taşınan= konmayan=` (alçak tavan = ayağa kalkılamayan yerde geçen kare; yerini `ALCAK` satırı yazar).
* `--mekanik`: Üç Âlem bölümü yerine `v25 alem_yok` (eylem yok, maske 9) ve tehlike çukuru denetimleri.
* `tools/tests/tuzak_testi.gd` genişliği `Level.W`'dan okur.
* Regresyon (v25, mühürsüz): betik hatası 0. `--otomatik` ve `--bot_gercek` 1 / 3 / 5 / 7 / 9 (yukarıdaki tablo),
  `--zeka` (TABLO, BITTI), beş boss `--otomatik --boss=<id> --bosslog` ve `--zeka --boss=<id> --zeka_oldur` (beşi de iki
  botla devrildi), Erlik `--zeka_cekim` ile Tamu Seli, `--tuccar` GECTI (duvar_ok), `--mekanik` BITTI, `--yurt --yurt-tur`
  (Kut Kapısı'na varıldı), `--dovus --boss` TAKILMA=0, `--piksel_tara` 0 (normal bölüm, Erlik ve Tepegöz arenası),
  `--harita` GECTI.

## v26: daha yavaş, daha az kritik, daha zor moblar

Geri bildirim (v25'i oynayarak): "Saldırı hızı ve kritik oranı hâlâ çok yüksek. Sıradan yaratıkları öldürürken çok az
zorlanıyorum; tosbağa hariç. Kritik sesi de Dead Cells'inkine yakın olsun; çok sönük."

### Tempo: üçüncü katman (`Player.TEMPO_V26`, `TEMPO_V26K`)

v25'in üstüne sınıfa göre bir katman daha (tek düğme `TEMPO_V26K`: 0 = v25, 1 = v26; sütunlar `TEMPO_V25` ile aynı:
`[ilk hazırlık ×, zincir hazırlığı ×, süpürme ×, kilit ×, toparlanma ×, + tutuş ilk, + tutuş zincir]`). Hedef zincir
aralığı: hafif / orta (hançer, ikiz bıçak, düello, kılıç) +%25-30, mızrak / kırbaç / uzun sap +%10-15, ağır / dev +%5.
Basış→temas (ilk hazırlık) yalnızca 0-17 ms uzar: tepki aynı, oturma (kilit) ve yeniden gerilme uzar.

| Sınıf | çarpanlar | + tutuş (ilk / zincir) |
|---|---|---|
| hançer (ikiz bıçak, böri, pençe) | 1,1 / 1,3 / 1,08 / 1,25 / 1,2 | 8 / 10 ms |
| Ay Palası (silaha özgü) | 1,1 / 1,26 / 1,08 / 1,22 / 1,2 | 8 / 10 ms |
| düello (yatağan, rüzgâr) | 1,1 / 1,36 / 1,08 / 1,3 / 1,22 | 8 / 12 ms |
| kılıç | 1,08 / 1,32 / 1,06 / 1,28 / 1,2 | 8 / 10 ms |
| mızrak | 1,03 / 1,13 / 1,02 / 1,13 / 1,08 | 0 / 6 ms |
| kırbaç, uzun sap | 1,03 / 1,14 / 1,02 / 1,14 / 1,08 | 0 / 6 ms |
| ağır | 1,02 / 1,06 / 1 / 1,06 / 1,04 | 0 / 4 ms |
| dev | 1,02 / 1,05 / 1 / 1,06 / 1,04 | 0 / 4 ms |

**Saldırı hızı kaynakları yine "ışık hızı"na dönemesin:**
* `HIZ`: kalıcı üst sınır %25 → %18, Kızışma dahil %35 → %25; Kurt ongunu tomar başına %1,5 → %1, Yel Ana %10 → %7, Kam
  Davulu seviye başına %3 → %2; sınıf etkisi ~%20 düştü (hançer 0,7 → 0,55, düello 0,6, kılıç / mızrak 0,7, kırbaç 0,65,
  uzun 0,6, ağır 0,55, dev 0,45).
* Kızışma (`items.json`): İkiz Bıçak / Böri +%2-3 → +%1,5-2 (en çok 4), Kurt Pençeleri / Rüzgâr +%1,5-2,5, Kement / Od
  Kamçısı +%3-5 → +%2-3 (tam yükte +%6-12; v25 +%8-20, v24 +%18-32).
* İkiz bıçağın adım başına hızlanması (`DUAL_RAMP`) 0,04 → 0,025; Ay Dansı adım başına %5-9 → %3-5; Yatağan ivmesi kat
  başına %6-12 → %3-6.
* Kut Yankısı'nın kısa hazırlığı (`V19.yk_wind`) 0,55 → 0,72 (yankı zinciri kendi başına bir hız kaynağıydı).
* Eşya hızı: "Çevik" +%6-20 → +%4-12, "Tez Elli" +%4-10 → +%2-6; malzeme hızı Tunç / Gümüş 1,05 / 1,04 → 1,02, Gök Demiri
  1,08 → 1,04; kalite yuvarlaması 0,92-1,08 → 0,95-1,04; `_tempo_scale` en çok hızlanma 1 / 0,55 → 1 / 0,85 (malzeme +
  kalite + ivme tabanı 1,8 kat hızlandırabiliyordu, artık en çok %18).

Ölçüm (`-- --dovus --boss --hiz`, 60 Hz ±1 kare, taban aps, niteliksiz; "önce" = v25, aynı betik). Son sütun: testin en
hızlı denemesi (%40 istenir; v25'te %35'e, v26'da %25'e kırpılır) basış→temas / ortalama zincir aralığı:

| Silah | basış→temas (ms) | zincir aralıkları (ms) | ortalama | en hızlıda (%40 istenir; v26 %25'e kırpılır) |
|---|---|---|---|---|
| ikiz_bicak | 150 → 167 | 200, 167, 300 → 267, 217, 383 | +30% | 117 / 183 → 150 / 261 |
| bori_hanceri | 150 → 167 | 200, 200, 183 → 267, 250, 250 | +32% | 117 / 167 → 150 / 233 |
| kurt_pencesi | 117 → 117 | 317, 233, 233 → 400, 300, 267 | +23% | 83 / 206 → 117 / 295 |
| ay_palasi | 117 → 133 | 383, 183, 183 → 467, 283, 250 | +34% | 100 / 211 → 117 / 300 |
| yatagan | 167 → 167 | 283, 283, 317 → 350, 317, 417 | +23% | 133 / 211 → 167 / 311 |
| ruzgar_kilici | 167 → 183 | 283, 317, 333 → 333, 383, 417 | +21% | 133 / 234 → 167 / 322 |
| alp_kilici | 167 → 183 | 300, 367, 367 → 400, 433, 483 | +27% | 133 / 250 → 167 / 372 |
| pala | 167 → 183 | 300, 317, 550 → 400, 367, 700 | +26% | 133 / 284 → 167 / 411 |
| ruh_kilici | 167 → 183 | 300, 350, 367 → 400, 433, 467 | +28% | 133 / 250 → 167 / 367 |
| yilan_kilici | 167 → 183 | 300, 367, 367 → 400, 417, 467 | +24% | 133 / 250 → 167 / 367 |
| ayaz_kilici | 167 → 183 | 367, 367, 367 → 450, 483, 433 | +24% | 133 / 261 → 167 / 394 |
| yildirim_kilici | 167 → 183 | 267, 433, 417 → 333, 550, 533 | +27% | 133 / 278 → 167 / 406 |
| kargi | 167 → 167 | 250, 283, 317 → 283, 350, 350 | +16% | 150 / 228 → 150 / 278 |
| tulpar_mizragi | 167 → 167 | 250, 283, 350 → 283, 333, 400 | +15% | 150 / 239 → 150 / 289 |
| kement | 200 → 217 | 383, 383, 383 → 433, 467, 433 | +16% | 183 / 306 → 183 / 372 |
| od_kamcisi | 200 → 217 | 317, 383, 383 → 383, 433, 467 | +18% | 183 / 295 → 183 / 356 |
| teber | 217 → 233 | 367, 450, 467 → 433, 517, 533 | +15% | 183 / 333 → 200 / 422 |
| erlik_tirpani | 217 → 233 | 367, 383, 667 → 433, 467, 750 | +16% | 183 / 378 → 200 / 472 |
| kayin_asasi | 217 → 233 | 317, 650, 467 → 400, 733, 533 | +16% | 183 / 372 → 200 / 472 |
| gurz | 300 → 317 | 500, 617, 533 → 517, 650, 550 | +4% | 250 / 456 → 267 / 500 |
| civili_topuz | 300 → 300 | 417, 633, 533 → 450, 650, 550 | +4% | 250 / 428 → 267 / 478 |
| savas_baltasi | 300 → 300 | 500, 533, 500 → 500, 567, 500 | +2% | 250 / 422 → 267 / 461 |
| ikiz_balta | 300 → 300 | 433, 450, 750 → 450, 467, 783 | +4% | 250 / 444 → 267 / 505 |
| ulu_kilic | 400 → 400 | 600, 1017, 600 → 617, 1050, 617 | +3% | 333 / 617 → 367 / 705 |
| bozgun_kilici | 367 → 383 | 517, 1017, 683 → 550, 1067, 733 | +6% | 300 / 633 → 350 / 705 |
| dag_cekici | 400 → 400 | 650, 717, 650 → 683, 750, 683 | +5% | 333 / 561 → 367 / 644 |
| kor_cekici | 383 → 383 | 667, 700, 667 → 717, 717, 717 | +6% | 317 / 583 → 350 / 650 |

Kart (`ItemGen.dps`): İkiz Bıçak 6,0 → 4,7 vuruş/sn, Alp 3,0 → 2,4, Kargı 3,5 → 3,1, Gürz 1,9 → 1,8, Ulu Kılıç 1,9 → 1,8.
`--tomar --boss`: kart ↔ ölçülen SnH koşulsuz silahlarda en büyük fark %3,0 (GEÇTİ). Bu arada bulunan hata: delip geçen
çapraz atılışta (ikiz bıçak / böri bitirişi) temas ile çok vuruş işaretinin ilki uzun evrelerle ayrı karelere düşünce düşmana
fazladan bir vuruş değiyordu (ölçülen kartın +%20 üstü); artık ikisi aynı geçiş (`ItemGen.zincir_vurus` gibi). `--kontrol`
basılmamış = 0, `--dovus --boss` TAKILMA = 0; en az kare ihlali 0.

### Kritik: %26-32 → ~%6-9 (gerçek oyun)

Ölçüm (`--otomatik --bot_gercek --derinlik=N --muhur=0`, 30 000 kare ≈ 6,5 dk; bot dibine girip 8 karede bir basan ezici,
10 sn'de bir Bozkurt biçimi açar; satır `[otomatik] KRIT`, `Main._exit_tree` artık `--quit-after` ile biterken de yazar):

| derinlik | önce: kritik (şans / kesin) | önce: kesin kritiğin nedeni | sonra: kritik (şans / kesin) | sonra: kesin nedeni |
|---|---|---|---|---|
| 1 | %31,9 (2,1 / 29,9) | Bozkurt ısırığı 26, karşı vuruş 9, yankılı bitiriş 7, infaz 1 (144 isabet) | %6,9 (2,4 / 4,5) | yankılı bitiriş 5, karşılık 3, infaz 2, karşı 1 (245) |
| 3 | %29,0 (4,1 / 24,9) | Bozkurt 50, karşı 5, yankı 4, kaçış 2 (245) | %6,4 (1,6 / 4,8) | yankı 3, kaçış 1, karşı 1, karşılık 1 (125) |
| 5 | %26,2 (3,4 / 22,8) | Bozkurt 35, karşı 12, yankı 8, infaz 3, karşılık 2 (263) | %7,6 (1,7 / 5,9) | yankı 8, kaçış 5, karşı 3, karşılık 1 (289) |
| 8 | %28,0 (2,5 / 25,4) | Bozkurt 36, karşı 14, yankı 9, infaz 1 (236) | %6,4 (2,5 / 4,0) | karşı 6, yankı 4, kaçış 1, mühür 1, karşılık 1 (326) |

Kukla (`--tomar --boss --krit`, 27 yakın silah, saldırmayan kukla): %7,8 (şans 3,2 / koşul 4,6) → %7,4 (şans 3,7 / koşul
3,7). Tek yaratığa karşı ezen oyuncu (`--zeka --zeka_oldur`, aşağıda): d1 %20,6 → %16,1, d3 %14,1. Ortalama oynanışta
(bölüm + düello) ~%8-10; okuyan / kaçan oyuncu (kusursuz kaçış, "!"yi karşılama, yankı) daha çok alır.

Nedenler ve değişiklikler:
1. **Bozkurt biçimi** (Kut) üçüncü ısırığı kesin kritikti; biçim her açılışta 3-4 kritik veriyordu (bot ölçümünde kesin
   kritiklerin yarısı). Artık kritik değil, bitiriş hasarı (`kritik.bitiris` ×1,3). Don biçiminin (`DonForm`) bitiriş
   atılışı da aynı.
2. **Karşı Vuruş** artık yalnızca okunan "!"ye: zırhlı "!!" hazırlığa karşı vuruş yok; savuruş hazırlık başladıktan sonra
   ve zincirin akışı dışında (beklemeden, yeni) başlamış olmalı (`Player._counter_ok`, `_atk_t0`, `_atk_fresh`; düşman
   `_tele` anını `v26_tele_t` olarak yazar). Ezilen kombo hazırlıkları kendiliğinden kesip kritik almıyor (bu aynı zamanda
   yaratıkları zorlaştırdı: ezene "!" artık sökmüyor).
3. **Koşul kritiği** aynı düşmanda 1,2 sn / 4 isabet → 2,5 sn / 6 isabette bir (`zorluk.json` "kritik").
4. **Şans kritiği**: silah tabanında yalnızca en yüksekler (5 → 4, 4 → 3); malzeme Gümüş 3 → 2, Yeşim / Gök Demiri / Ruhani
   2 → 1, Ayaz 1 → 0; yuvarlama -1..+1,5 → -1..+1; "İsabetli" %2-7 → %2-5; Ay Ata lütfu 6 → 4, Segrek adı 5 → 3.
5. **Gölge Adım** (İkiz Bıçak): yuvarlanmadan sonraki 1-3 vuruş → yalnızca ilk 1 sn içindeki 1-2 vuruş kesin kritik.
6. Kalan kesinler beceri: Kut Mührü (art arda üç yankı), yankılı bitiriş, çarpışma karşılığı, okunmuş Karşı Vuruş, kusursuz
   kaçış, infaz (Kut Alma), tam bırakış / dipten atış, ok sökme.

### Yaratıklar: tosbağa neden zordu, ötekiler neden kolaydı

Tosbağa (`Enemy._ai_turtle`, `take_hit`): vurulunca %55 olasılıkla kabuğa çekilir, kabuktayken hasarın yalnızca %8'ini alır
ve sarsılmaz; kabuktan sonra **her seferinde** 1,4 sn duvardan seken, 1,2 kat vuran yuvarlanmaya geçer. Yani ezilemez:
ezen oyuncu kabuğa vurup vakit kaybeder, sonra yuvarlanmayı yer; yuvarlanmanın sonundaki 1 sn "başı döndü" penceresini
beklemek zorundadır. Öbür yaratıklar ise ezilerek kilitleniyordu: hafif vuruş her isabette 0,1 sn sarsıyor, 0,34 sn
sarsılmazlıktan sonra yine sarsıyor; "!" hazırlıkları zincirdeki savuruşa değince Karşı Vuruş sayılıp kesiliyordu (kesin
kritikle); tepki (geri sıçrama, ışınlanma, zırhlı karşılık) 3-5 vuruşta ve 2,2 sn'de bir; 1-2. derinlikte aynı anda tek
yakın saldırgan; canlar düşüktü: ezen bot (`--zeka_oldur`, derinliğin beklenen donanımı) 1. derinlikte tazıları 3-4
isabette, 2-4 sn'de, hiç ya da çok az hasar alarak öldürüyordu; tosbağa 13 isabet, 11 sn ve canın %65'i.

Değişiklikler (`zorluk.json` yeni "yz" ve "rol_can" bölümleri; `Enemy.gd`, `Zorluk.yz`, `Zorluk.rol_can`). 1. derinlik
v25'e yakın tutuldu (öğrenilir), baskı 2. derinlikten sonra artar:
* **Can**: derinlik eğrisi `[1,02; 1,66; 2,16; 2,64; 3,18; 3,84; 4,62; 5,4; 6; 7]` → `[1,53; 2,49; 2,92; 3,48; 4,75; 5,65;
  5,82; 6,75; 7,5; 8,75]`; rol çarpanı: tazılar / pusucular / Yek (lunger, pouncer, crawler, stalker) ×1,2, uzak / uçan /
  sürü (çor, okçu, iye, kam, kamikaze, Erlik kızı, dalıcı) ×0,8-0,85, ağır yakın dövüşçüler ve tosbağa ×1. Seçkin canı
  ×2,6 → ×2,2 (seçkinler 13-20 → 17-24 vuruş; daha fazlası sıkıcıydı).
* **Hamle arası** (`yz.bekleme`, `_end_attack`): ×0,92 (d1) → ×0,84 / 0,8 / 0,76 ... ×0,62 (d10); `saldirganlik` aynen.
* **Tepki** (`yz.tepki_azalt`, `yz.tepki_bekleme`): eşik 2. derinlikten sonra 1, 7.'den sonra 2 düşer (en az 2: tazı 3 → 2
  vuruşta geri sıçrar, kalkanlı 3 → 2'de kalkan darbesi, dev 5 → 4'te döner savuruş...); iki tepki arası 2,2 → 2,0 (d1) /
  1,7 / 1,55 ... 1,2 sn (seçkinde ×0,75).
* **Ezmeye karşı "!!"** (`yz.baski`): son vuruştan sonraki 0,8 sn → 0,9 (d1) / 1,1 / 1,2 ... 1,5 sn içinde başlayan hazırlık
  zırhlı; **sarsılmazlık** (`yz.sarsilmaz`) 0,34 → 0,38 (d1) ... 0,6 sn; **diretme** (`yz.diretme`) 4 sarsılmada → 3 (d2+),
  2 (d8+).
* **Grup baskısı** (`yz.jeton`): aynı anda saldıran yakın dövüşçü 1 / 1 / 2 ... → 1 (d1) / 2 (d2-5) / 3 (d6+).
* Karşı Vuruş artık ezerek kesilmiyor (yukarıda).

Ölçüm (`-- --zeka --muhur=0 --zeka_oldur --derinlik=N`; yeni **OLDUR** sütunu: gerçek can, derinliğin beklenen donanımı
(o kademenin Nadir Alp Kılıcı + derinlik başına ~2,5 tomar), oyuncu dibine girip 8 karede bir basar; EZME = 20 sn sonsuz
canlı yaratığa ezen oyuncu). Tek koşu, rastlantı payı büyük (özellikle tosbağanın kabuk zarı); "önce" aynı betik v25 ile
(3. derinlik "önce" koşusunda can sütunu yoktu).

**1. derinlik**

| Yaratık | YZ | ezene hasar / 10 sn | ezmede kilit | öldürme süresi (sn) | vuruş (isabet) | can | alınan hasar (azami can %) |
|---|---|---|---|---|---|---|---|
| kara_boru | lunger | 9 → 27 | %16 → %9 | 3.6 → 7.8 | 4 → 9 | 61 → 110 | 0 → 0 |
| sicrayan_tazi | pouncer | 23 → 16 | %11 → %18 | 2.6 → 5.1 | 4 → 9 | 56 → 100 | 11 → 18 |
| yek | stalker | 10 → 20 | %27 → %16 | 2.5 → 4.5 | 3 → 5 | 56 → 100 | 0 → 0 |
| kirkayak | crawler | 34 → 34 | %18 → %18 | 2.2 → 5.5 | 4 → 7 | 56 → 100 | 14 → 14 |
| ayaz_kurdu | lunger | 28 → 28 | %19 → %16 | 5.8 → 6.7 | 6 → 9 | 63 → 113 | 19 → 38 |
| cor | flyer_ranged | 0 → 0 | %3 → %0 | 27.7 → 17.7 | 3 → 4 | 40 → 48 | 28 → 38 |
| kara_kus_yavrusu | diver | 23 → 44 | %10 → %10 | 0.9 → 2.3 | 1 → 3 | 45 → 58 | 0 → 0 |
| kan_yarasasi | swarm | 0 → 22 | %22 → %14 | 1.6 → 1.5 | 2 → 3 | 30 → 36 | 0 → 0 |
| agac_iyesi | brute | 68 → 52 | %26 → %4 | 2.9 → 10.5 | 7 → 13 | 153 → 229 | 0 → 48 |
| dev_cocugu | brute | 51 → 52 | %4 → %3 | 5.1 → 17.6 | 11 → 17 | 188 → 283 | 35 → 149 |
| tozkoparan | tornado | 21 → 41 | %5 → %3 | 3.6 → 6.6 | 9 → 12 | 112 → 168 | 11 → 40 |
| su_iyesi | caster | 92 → 55 | %0 → %0 | 40.3 → 45.0 (ölmedi) | 6 → 0 | 122 → 156 | 272 → 355 |
| balbal | hopper | 10 → 70 | %7 → %3 | 3.1 → 7.2 | 8 → 15 | 91 → 137 | 0 → 40 |
| arcura | illusionist | 40 → 28 | %0 → %1 | 10.0 → 19.3 | 1 → 4 | 56 → 71 | 8 → 40 |
| kurgan_okcusu | archer | 32 → 16 | %0 → %0 | 17.0 → 18.9 | 0 → 0 | 51 → 61 | 32 → 32 |
| isilti_bocegi | kamikaze | 172 → 134 | %22 → %31 | 1.1 → 1.9 | 3 → 4 | 45 → 58 | 0 → 0 |
| erlik_kizi | charmer | 18 → 39 | %6 → %3 | 31.8 → 20.5 | 5 → 1 | 66 → 84 | 131 → 58 |
| surale | grabber | 21 → 30 | %16 → %13 | 3.0 → 3.7 | 6 → 8 | 76 → 114 | 6 → 6 |
| karakoncolos | mimic | 38 → 26 | %15 → %13 | 3.3 → 4.1 | 5 → 7 | 81 → 122 | 7 → 7 |
| kurgan_bekcisi | shield | 33 → 58 | %11 → %5 | 5.0 → 7.1 | 12 → 13 | 96 → 145 | 18 → 62 |
| al_atli | charger | 25 → 44 | %47 → %27 | 8.5 → 9.9 | 15 → 21 | 107 → 160 | 62 → 55 |
| tas_kertenkele | turtle | 21 → 10 | %2 → %0 | 1.1 → 6.7 | 3 → 17 | 86 → 130 | 0 → 18 |
| tosbaga | turtle | 10 → 0 | %4 → %3 | 11.3 → 12.0 | 13 → 18 | 91 → 137 | 65 → 0 |

**3. derinlik**

| Yaratık | YZ | ezene hasar / 10 sn | ezmede kilit | öldürme süresi (sn) | vuruş (isabet) | can | alınan hasar (azami can %) |
|---|---|---|---|---|---|---|---|
| kara_boru | lunger | 82 → 132 | %16 → %15 | 3.4 → 5.0 | 4 → 7 | - → 210 | 22 → 0 |
| sicrayan_tazi | pouncer | 48 → 32 | %24 → %23 | 2.0 → 4.1 | 3 → 5 | - → 192 | 13 → 0 |
| yek | stalker | 35 → 107 | %45 → %18 | 2.3 → 3.6 | 6 → 7 | - → 192 | 0 → 25 |
| kirkayak | crawler | 60 → 48 | %19 → %15 | 3.7 → 3.4 | 3 → 8 | - → 192 | 17 → 17 |
| ayaz_kurdu | lunger | 84 → 135 | %15 → %9 | 2.8 → 6.9 | 3 → 10 | - → 217 | 23 → 47 |
| cor | flyer_ranged | 12 → 47 | %5 → %0 | 11.1 → 23.4 | 2 → 3 | - → 93 | 48 → 87 |
| kara_kus_yavrusu | diver | 67 → 53 | %8 → %18 | 4.9 → 4.0 | 3 → 3 | - → 111 | 22 → 24 |
| kan_yarasasi | swarm | 31 → 15 | %20 → %17 | 1.8 → 1.6 | 1 → 3 | - → 70 | 0 → 0 |
| agac_iyesi | brute | 119 → 98 | %1 → %3 | 12.5 → 4.2 | 8 → 8 | - → 438 | 118 → 0 |
| dev_cocugu | brute | 31 → 86 | %6 → %4 | 4.7 → 9.5 | 15 → 17 | - → 540 | 27 → 76 |
| tozkoparan | tornado | 67 → 109 | %2 → %2 | 5.6 → 5.5 | 10 → 9 | - → 321 | 27 → 49 |
| su_iyesi | caster | 51 → 73 | %4 → %0 | 35.2 → 45.0 (ölmedi) | 6 → 2 | - → 297 | 262 → 144 |
| balbal | hopper | 17 → 142 | %6 → %3 | 6.7 → 5.5 | 9 → 10 | - → 262 | 25 → 25 |
| arcura | illusionist | 35 → 49 | %0 → %1 | 20.2 → 9.7 | 2 → 2 | - → 136 | 49 → 20 |
| kurgan_okcusu | archer | 57 → 71 | %1 → %5 | 41.9 → 19.1 | 3 → 0 | - → 116 | 197 → 59 |
| isilti_bocegi | kamikaze | 274 → 239 | %26 → %34 | 0.8 → 1.9 | 0 → 4 | - → 111 | 0 → 0 |
| erlik_kizi | charmer | 33 → 17 | %5 → %9 | 13.6 → 21.2 | 5 → 2 | - → 161 | 44 → 93 |
| surale | grabber | 49 → 73 | %19 → %14 | 3.5 → 3.7 | 5 → 7 | - → 219 | 7 → 7 |
| karakoncolos | mimic | 46 → 79 | %12 → %15 | 3.0 → 3.9 | 6 → 7 | - → 233 | 9 → 9 |
| kurgan_bekcisi | shield | 66 → 101 | %9 → %6 | 2.8 → 10.1 | 6 → 14 | - → 277 | 0 → 54 |
| al_atli | charger | 77 → 132 | %46 → %5 | 13.0 → 17.3 | 9 → 28 | - → 306 | 38 → 209 |
| tas_kertenkele | turtle | 0 → 0 | %4 → %3 | 9.9 → 3.7 | 9 → 11 | - → 248 | 27 → 0 |
| tosbaga | turtle | 0 → 0 | %11 → %5 | 20.4 → 24.8 | 20 → 17 | - → 262 | 27 → 0 |

Okuma: yakın dövüşçüler artık ezilerek 2-4 sn'de ölmüyor; 1. derinlikte tazılar 7-9, kalkanlı 13, iye / dev / Balbal 13-17
isabet. 3. derinlikte ezen oyuncuya verilen hasar çoğu yakın dövüşçüde arttı (Erlik tazısı 82 → 132, Yek 35 → 107, Balbal
17 → 142, Kalkanlı 66 → 101, Kızıl Gul 77 → 132, dev çocuğu 31 → 86). Tosbağa ve Taş Gulü aynı zorlukta kaldı (zaten
ezilemiyorlardı; tek koşuda kabuk zarına göre 0-%65 hasar); Kızıl Gul (charger) 3. derinlikte en sert yakın dövüşçü (ezen bot
canının 2 katını yedi: hücumu ve kalkanı ezmeyi cezalandırıyor). Uzak roller (çor, okçu, iye, Erlik kızı) ezen botla zaten
zordu (bot kovalayamıyor); canları biraz düştü.

`--denge --denge_muhur=0` (ortanca sıradan düşman; "tipik" = o kademenin Nadir silahı + beklenen tomar):

| d | tipik vuruş | başlangıç silahıyla | seçkin tipik | oyuncu ölür (tipik can) |
|---|---|---|---|---|
| 1 | 5 → 9 | 6 → 11 | 13 → 19 | 6 → 6 |
| 2 | 5 → 9 | 10 → 18 | 13 → 20 | 6 → 6 |
| 3 | 8 → 10 | 20 → 26 | 19 → 22 | 6 → 6 |
| 4 | 8 → 10 | 24 → 30 | 20 → 22 | 5 → 5 |
| 5 | 7 → 10 | 24 → 37 | 19 → 24 | 6 → 6 |
| 6 | 7 → 10 | 32 → 47 | 19 → 24 | 6 → 6 |
| 7 | 8 → 10 | 41 → 51 | 16 → 17 | 6 → 6 |
| 8 | 8 → 10 | 46 → 60 | 17 → 18 | 5 → 5 |
| 9 | 9 → 11 | 61 → 73 | 14 → 13 | 5 → 5 |

**Bosslar** (tipik SnH, isabet payı %45): yavaş tempo ve az kritikle SnH ~%13-17 düştü; canlar ×0,82 (Kara Börü Han 2500 →
2050, Tepegöz 4400 → 3600, Albastı Ana 5500 → 4500, Şahmeran 6700 → 5500, Yelbegen 8900 → 7300, Erlik Han 11800 → 9700).
Süre 101 / 105 / 100 / 100 / 106 sn → 94 / 99 / 96 / 97 / 105 sn (hedef 90-120).

**Bot** (`--otomatik --bot_gercek`, 30 000 kare ≈ 6,5 dk, kaçmayan ezici): ölüm d1 1 → 2, d3 1 → 0, d5 1 → 2, d8 1 → 3;
alınan hasar d5 1854 → 2488, d8 3280 → 4720. Başlangıç donanımlı eski bot (`--otomatik`, 6600 kare) d1 / d3 ölmedi, d5 ve
d8'de birer kez öldü.

### Kritik sesi: Dead Cells'e yakın (`tools/audiogen/v26.py`, `Ses.hit`, `Ses.krit_duck`)

v25 kritiği temiz ama sönüktü: 0,46 sn'lik dosyanın yarısı çan ve oda kuyruğuydu (yükseklik ölçüsü kuyruğu da sayınca geçiş
görece kısık kalıyordu), SFX veri yolunun sıkıştırıcısı (-14 dB, 3:1) kritiği sıradan vuruşun düzeyine geri bastırıyordu;
Balbal'a ve siperdeki yaratığa kritik yüzey sesi (`darbe_donuk`) çalıyordu, dönen balta / yer şoku kritikleri sessizdi.
Yeni ses kısa, gür ve kirli (0,24 sn bıçak, 0,28 sn künt; geçiş t=0):
1. **KRAK**: 1,5-12 kHz gürültü patlaması, asimetrik sert kırpma + bit ezme (8 kHz / 5 bit tanecik), 18-28 ms + parlak tık.
2. **THWACK**: perdesi 190 → 62 Hz düşen ton, asimetrik doyurma (80-200 Hz gövde ve harmonikleri) + temiz alt bas + Kenney
   impactPunch_heavy (CC0) bozularak; 0,7-2,6 kHz kırpılmış orta "şak".
3. **ezilme**: 500-5000 Hz tanecikli, doyurulmuş kırılma gürültüsü.
4. **şing**: bıçakta 4-4,7 kHz inharmonik çelik tonları (perde hafifçe düşer) + knifeSlice (CC0) tizi; künt çeşitte
   1,5-1,8 kHz kısa "dang", daha alçak çatırtı, daha uzun gövde.
5. **işlem**: geçiş biçimleme (hızlı / yavaş zarf farkı: saldırı +, gövde -), paralel (NY) sıkıştırma 4:1, son yumuşak
   kırpma, çok küçük oda.

Ölçüm (`synth.loudness`, 50 ms en gür pencere; bant payı ilk 0,3 sn enerjisinin, dB):

| | süre | yükseklik | tepe − yükseklik | 80-200 Hz | 200-1k | 1-5k | 5k+ | ilk 30 ms payı |
|---|---|---|---|---|---|---|---|---|
| v25 darbe_kritik_1 | 0,46 sn | -8,8 | 7,8 | -3,7 | -10,7 | -8,3 | -18,6 | -5,2 |
| v26 darbe_kritik_1..4 | 0,24 sn | -7,3..-7,5 | 6,3 | -2,4..-4,5 | -8,2..-10,8 | -4,8..-6,6 | -10,7..-12,3 | -1,3..-3,0 |
| v25 darbe_kritik_kunt_1 | 0,46 sn | -9,3 | 8,3 | -7,8 | -12,2 | -14,5 | -29,5 | -7,1 |
| v26 darbe_kritik_kunt_1..3 | 0,28 sn | -7,4..-7,5 | 6,3-6,5 | -3,8..-5,3 | -6,6..-8,4 | -7,3..-8,1 | -16..-19 | -3,1..-4,0 |

Dalga biçimi ve spektrogram karşılaştırması: `docs/v26/kritik_ses.png` (v25 / v26, bıçak ve künt).

Karışım: `export_audio.py` hedefi darbe_kritik -8 → -6,5 dB (kısa ve yoğun olduğundan master sınırına dayanır, -7,4
ölçülür; sıradan darbe -10 / -10,5); `Ses.HIT_TIERS` kritik 0 → +1,5 dB → hafif vuruştan ~9 dB, silah darbe sesinden
~8 dB gür. Kritikler yeni **"Krit" veri yolunda** (`Ses.BUS_KRIT`, `_bus_for`: "darbe_kritik" ile başlayan her ses): SFX
sıkıştırıcısını atlar, yalnızca Master'ın yapıştırıcısı ve sınırlayıcısından geçer. **Kısma** (`Ses.krit_duck`, `Ses.hit`
kademe 2'de kendisi çağırır): öbür efektler -5, ortam -7, müzik -7 dB; 70 ms tutma, 0,26 sn yumuşak dönüş (gerçek
zamanlı, vuruş duraklamasından bağımsız). Taşa / kalkana kritik artık tok kritik çeşidini çalar; saldıranın kendi sesini
çaldığı kritikler (dönen balta, yer şoku) de kritik sesini çalar (`Enemy.take_hit`); `darbe_kritik_kunt` kendi ses sınırını
aldı (sıradan darbelerin "darbe" grubunda çalınıp kesilmesin). Görsel eş (`Player._crit_accent`): sesle aynı karede beyaz
halka + darbe yönünde yelpazelenen dört kısa ışın + vuruş yönünde küçük sarsıntı (duraklama süresine dokunmaz). Yeniden
üretim: `python tools/audiogen/export_audio.py --sfx darbe_kritik darbe_kritik_1 darbe_kritik_2 darbe_kritik_3
darbe_kritik_4 darbe_kritik_kunt_1 darbe_kritik_kunt_2 darbe_kritik_kunt_3`.

### Diğer düzeltmeler

* `Player._exec_strike`: infaz hedefi savuruş sırasında serbest bırakılınca tipli değişkene atama betik hatası veriyordu.
* `tools/tests/yay_testi.gd` `_idle_check`: vuruş duraklaması dipleri gerçek zamanla söner; `--fixed-fps` headless koşu
  gerçek zamandan hızlı akınca 60 kare dibin sonuna yetmiyordu (yanlış TAKILMA); en çok 0,8 sn gerçek zaman bekler.
* `tools/tests/zeka_testi.gd`: `--zeka_oldur` yaratıklarda da (OLDUR sütunu: süre, isabet, can, alınan hasar, kritik);
  Taş Tosbağa listede. `Main._exit_tree`: bot ölçümünün son satırları `--quit-after` ile de yazılır.

### Bilinen

* Ezen botun gerçek oyunda kritik payı %6-8 (hedefin alt ucu); okuyan oyuncu daha çok alır. Tek yaratığa karşı ezmede %14-16.
* Koşul silahlarında kart ↔ ölçülen fark büyük (Erlik Tırpanı +%29: çok geçişli savuruşun fazladan geçişleri; Yatağan
  +%15: geri çekilme kesiği); koşulsuz silahlar sınır içinde.
* Su İyesi ve Kurgan Kamı ezen botla 45 sn'de ölmüyor / zor ölüyor (ışınlanıyor, kaçıyor; v25'te de öyleydi).
* Pencereli `--takilma` ölçümü bu sürümde koşulmadı (yalnızca headless `--kontrol` / `--dovus`).

### Test

* `--dovus --boss` ve `--dovus --boss --kontrol`: TAKILMA=0, basılmamış=0; `--dovus --boss --hiz` en az kare ihlali 0.
* `--tomar --boss` GECTI (en büyük fark %3,0), `--tomar --boss --uzak` GECTI, `--tomar --boss --krit` %7,4.
* `--denge --denge_muhur=0` BITTI; `--zeka --muhur=0 --zeka_oldur --derinlik=1/3` BITTI.
* `--otomatik --derinlik=1/3/5/8 --muhur=0` ve `--bot_gercek`: betik hatası 0 (ölümler yukarıda).
* `--yay --boss` TAKILMA=0, CEPHANE_HATA=0; `--unsur --boss` HATA=0; `--mekanik --muhur=0` BITTI; `--harita` GECTI;
  `--piksel_tara` TOPLAM 0.

## v27: yeni silahlar

İstek: "Yeni mekanikli birkaç silah ekleyelim — hem yakın hem uzak; tasarımları güzel, destansı olsun; animasyonları da
sanatsal olsun." Dört yakın, üç uzak silah. Her birinin mekaniği oyunda daha önce yoktu (var olanlarla karşılaştırma:
fırlat-çağır balta, kement çekişi, güdümlü tüy, seken taş, çivileyen cirit, zincir şimşek, ruh / yel hilali, kanama /
zehir / don yükleri, ivme, arkadan kritik, duvara çarpma, bozgun kristali, kor gölü, şimşek hamlesi). v22 kontrol ilkesi
korunur: hiçbir mekanik kendiliğinden saldırı atmaz; hepsi oyuncunun basışından ya da kendi isabetinden doğar.

Kod: `scripts/core/Silah27.gd` (tablolar, durum, çizim; oyuncunun çocuğu, `top_level` düğüm). `Player.gd` yalnızca kanca
noktalarından çağırır: `swing_def` / `plane_def` (SWINGS / PLANES + `Silah27.SWINGS` / `PLANES`), `_combo_for`,
`_heavy_for`, `_start_attack` (adım değiştirme), `_on_strike_start` başı (`pre_strike`), `_melee_hits` (`on_hit`),
`_deal` (mekanik eşleşmesi + `after_deal`), `_swing_box` varsayılanı, `_weight` / `_tempo_class` / `_reach`, ikincil
girdi (`sec_tick`), silah pozu / gövde karesi / yürüme çarpanı, iz tasarımı (`trail_style`), sprite (`sprite_id`).
Var olan silahların savuruş verisine dokunulmadı (yeni savuruşlar yeni anahtarlarla).

### Silahlar (`data/items.json`)

| Silah | Tür / ongun | Taban | Mekanik | Kritik |
|---|---|---|---|---|
| **Gün-Ay İkizi** | çift (kurt + kartal) | 8,4 | **Tutulma Duruşu**: basılı tut → Gün duruşu (birleşik çift ağız; iki yanı biçen çarklar, uzun sap temposu) ile Ay duruşu (iki hilal kılıç; düellocu temposu) arasında geçiş vuruşu; sonraki 2-3 vuruş +%25 | duruş değiştirdikten sonraki 1,2 sn (koşul kritiği) |
| **Kistin** | ağır (kurt + ayı), 1. derinlikten | 17 | **Dolama + Yere Çalma**: üçüncü savuruş zinciri düşmana dolar (0,9-1,3 sn bağlar, kökler); yeniden bas → düşmanı baş üstünden arkana çalarsın, düştüğü yer sarsılır (46 px). Ağır / boss çalınmaz (sarsılır). Bağ yoksa zincir üçüncüden sonra baştan | çalınan düşmanın altında kalan (beceri) |
| **Albastı Hançeri** | çift (kurt + kartal), 1. derinlikten | 5,6 | **Al İzi + Albastı Göçü**: her vuruş al izi (en çok 3, 6 sn); basılı tut → baktığın yöndeki 180-260 px içinde izli düşmanın arkasında belirip ters el saplama (iz başına +%35; arkası duvarsa önünde). İzli kimse yoksa ileri delip geçme | 3 izliye Göç saplaması kesin (beceri) |
| **Çevgen** | ağır (kurt + ayı) | 19,5 | **Top Gibi**: zincir bitirişi (çevgen vuruşu) ve ağır vuruş hafif düşmanı top gibi fırlatır (440-560 px/sn; ağır ×1,4); çarptığı düşmana %60 (topa %40) vurur, onu da fırlatır (2 nesil), duvara çarpan sersemler. Ağır / boss fırlamaz, +%30 sarsma hasarı | topun çarptığı düşman (beceri) |
| **Tatar Yayı** | fırlatma (kartal), 1. derinlikten | 39 | **Kusursuz Kurma**: ağır ok 2 düşmanı deler; her atıştan sonra yay kurulur (1/aps). Kurma çubuğunun altın yerinde (%62-78) yeniden bas → anında kurulur, sonraki ok 3-5 düşmanı deler ve kesin kritik (×1,5). Erken / geç basış takılır (+0,5 sn); ilk %20'deki basış yok sayılır, kurma başına tek deneme | Kut oku (beceri) |
| **Kam Küzgüsü** | büyü (kartal + ayı), 2. derinlikten | 3,4 / tik | **Kızgınlık**: basılı tut → 260 px gün ışını (10 tik/sn, dikey nişan yardımı, duvarda durur); aynı düşmanda 1,5 sn'de ×2,6-3,2'ye kızar (hedef değişince sıfırlanır). Ayna 2,6 sn'de ısınır; tam ısınınca Gün Patlaması (70 px, 6 × taban, yakar, sersemletir) ve 1,4 sn soğuma. Tutarken %45 hızla yürünür | tam kızmış ışının hedefine patlama |
| **Tengri Bağı** | büyü (kartal), 1. derinlikten | 20 | **Gök Bağı**: gök düğümü değdiği düşmanı ve 170 px içindeki 1-3 düşmanı 5 sn bağlar (birbirine hafifçe çekilirler); birine verilen her hasarın %40'ı ötekilere geçer (yinelemesiz). Bağ varken bas → **Bağ Çekişi**: bağlılar ortaya çekilip çarpışır (×1,3, 0,6 sn sersem; tek bağlı oyuncunun önüne) | Çekişte çarpışan (2+) düşmanlar (beceri) |

Lore satırları `items.json` "lore" (kartta): Oğuz Kağan'ın oğulları Gün Han ile Ay Han, Deli Dumrul'un köprüsü, Al
Karısı, çevgen oyunu ve Alp Er Tunga, boynuz-sinir ağır yay, kamın tunç aynası (küzgü), Tengri'nin yıldız zinciri.
Unsur: tema eğilimleri Albastı → kam, Kistin → Yer-Su, Küzgü → od, Tengri Bağı → yıldırım (`Unsur.BIAS`; Küzgü ve Tengri
Bağı büyü olduğu hâlde unsur alabilir: `Unsur.MAGIC_OK`). Havuz: `impl: true`, başlangıçta açık değil → parşömenle
Demirci'de açılır (bedel `Game.unlock_cost`), sonra düşüş ve Bezirgân havuzunda; `min_tier` yukarıdaki gibi.

### Savuruşlar (v23 3B düzlemleri; `Silah27.SWINGS` / `PLANES`)

* **Gün duruşu**: `gun_cark` (çift ağız gövdenin çevresinde yassı tam tur, 94°/0,26, arka yarıda gövdenin arkasında),
  `gun_teker` (önde neredeyse ekran düzleminde dik çark: bıçak öne takla atar, 18°/0,86), `gun_tutulma` (baş üstünden
  dik "C" iniş, aynı hamlede arka ağız alttan geri yükselir: iki düzlem 32° → 150°). Çift ağzın arka ucu da ayrı bir
  mürekkep hilali çizer (`_back_blade_tick`, ayaz mavisi; öndeki iz altın).
* **Ay duruşu**: `dual_l` → `dual_r` → `ay_hilal` (iki hilal kılıçla çapraz X, 54° → 126°); iz ay mavisi-beyaz.
  Geçişler: `ay_ayrilis` (birleşik bıçak ikiye ayrılırken büyük öne X), `gun_birlesme` (baş üstünde iki tam tur).
  Geçişte altın / gümüş mürekkep halkaları, ışık, "GÜN DURUŞU" / "AY DURUŞU"; sprite `gun_ay_ikizi` ↔ `gun_ay_ikizi_ay`.
* **Kistin**: `kistin_tepe` (top sırtın arkasında dolanıp baş üstünden iner), `kistin_yan` (çok yassı geniş savruk,
  92°/0,22), `kistin_dolama` (zincir kırbaç gibi uzanır), `kistin_cal` (ekran düzleminde önden baş üstüne, arkaya çalış;
  süpürme ×5: atış yayı görünür). İz dar, uçta dolgun (topun yolu); dolanan zincir gövdede halka halka çizilir.
* **Albastı**: `dual_l` → `reverse_grip` → `dual_r` → `albasti_oyma` (çift saplama); Göç: `albasti_goc` (ters el
  sırta saplama). Kaybolma / belirmede kızıl mürekkep halkası, kara-kızıl duman, kızıl iz çizgisi, kısa ağır çekim.
  Göç sonrası yüz düşmana döner (oyuncunun basılı tutarak seçtiği hamlenin parçası; kendiliğinden dönme değil).
* **Çevgen**: `sweep_low` (yerde sürme) → `down` → `cevgen_vurus` (arkada-alçakta kurulur, yere yakın geçip önde
  yükseğe savrulur). Uçan düşman döner, hayalet izi bırakır; çarpmada mürekkep darbe yıldızı + kısa duraklama.

### Uzak silahların görünüşü

* Tatar Yayı: atışta / kurma denemesinde kol iskeleti yayı öne tutar (dikey nişan açısında, geri tepme); ok
  `tatar_oku` atlas sprite'ı + ince mürekkep izi (Kut okunda altın). Başın üstünde kurma çubuğu: dolum, altın yer,
  deneme sonrası halka (altın / kızıl).
* Kam Küzgüsü: ışın koyu mürekkep kenar + altın gövde + beyaz çekirdek; kızdıkça kalınlaşır, ısındıkça turuncu-kızıla
  döner; ucunda parlayan top ve kıvılcım. Başın üstünde ısı çubuğu (soğumada gri).
* Tengri Bağı: dönen gök düğümü mermisi (`BagOrb`); bağlar titreyen mavi gök zinciri, bağlıların üstünde dönen düğüm.

### Sanat (`tools/artgen/weapons_myth.py`, `weapons_ink.py`)

Yeni çizimler: `gun_ay_ikizi` (merkezden tutulan çift ağız: altın güneş siperi + gümüş hilal siperi, ortada kızıl
püskül), `gun_ay_ikizi_ay` (ikiz hilal kılıç: güneş ve ay topuz), `kistin` (kurt başı topuz, kara demir zincir, tamga
bantlı çivili top), `albasti_hanceri` (kara taş kabza, altın pençe siper, dalgalı kızıl ağız, kızıl saç püskülü),
`cevgen` (kara değnek, sapa dik kızıl laklı tokmak, altın bant, at başı uçlar, kurdeleler), `tatar_yayi` (kurt başlı
kundak, kompozit yay, gergin kiriş, kurulu ok, üzengi), `tatar_oku`, `kam_kuzgusu` (malzeme renginde süslü çerçeve,
ayna yüzü, güneş damgası, çıngıraklar, çalama kurdeleleri), `tengri_bagi` (gök demiri sap, büyük halka, yüzen gök
taşı, zincir ve hilal). v2 atlası 4096×2248 (tek sayfa), v1 atlası 69 satır; HD x2: `KY_HD=2 python weapons_ink.py`,
`python export_hd.py 2 --only weapons`, `python hd_paket.py --paketle` (manifest md5 güncel).

### Ses (`tools/audiogen/silah27.py`, tek başına çalışır)

`kuzgu_isin_dongu` (ısıyla tizleşen ışın uğultusu), `tatar_atis_1/2`, `tatar_kurma`, `albasti_goc`, `bag_zincir`; geri
kalanı var olan kayıtlar (savur_*, darbe_*, sarsinti_buyuk, kut_donusum, gok_gurleme...). export_audio.py'ye eklenmedi
(tam üretim kritik sesine dokunmasın); `sfx.json`'a yalnızca yeni girdiler.

### Saniyedeki hasar (kart ↔ ölçülen; kademe 0 Demir, şans kritiği 0, tomar 0 / 7)

`-- --tomar --boss` (yakın, Kurt tomarı; kukla 26 px) ve `-- --tomar --boss --uzak` (uzak, Kartal tomarı; kukla 110 px).
Kart `ItemGen.dps` → `Silah27.card_rate` (uzak) / zincir tablosu (yakın; Kistin'de Yere Çalma, sürekli dövüşte Dolama hep
bağladığı için turun parçası). Karşılaştırma: Alp Kılıcı 24,7, İkiz Bıçak 18,8, Ulu Kılıç 36,9, Türk Yayı 21,1, Gök Asası 23,1.

| Silah | tomar 0: kart / ölçülen | tomar 7: kart / ölçülen | not |
|---|---|---|---|
| Gün-Ay İkizi (Gün) | 24,2 / 23,2 (-%4,1) | 67,9 / 66,0 | zincir aralığı 583-700 ms (iki yanı biçer) |
| Kistin | 27,9 / 27,1 (-%2,8) | 78,1 / 80,3 | 4 adımlı tur (Yere Çalma ×1,9, bitiriş) |
| Albastı Hançeri | 17,3 / 17,5 (+%1,3) | 48,3 / 48,2 | zincir aralığı 250 ms; Göç ×(1 + 0,35 × iz) beceri |
| Çevgen | 28,4 / 28,5 (+%0,6) | 79,4 / 79,6 | top çarpışmaları (çok hedef) sayılmaz |
| Tatar Yayı (kur_yok) | 20,7 / 20,7 (-%0,1) | 56,0 / 55,9 | her kurmada Kusursuz Kurma (beceri tavanı) 44,2 (+%113; Türk tam bırakış +%82) |
| Kam Küzgüsü (basılı tut) | 24,3 / 24,5 (+%0,9) | 65,6 / 65,3 | ısınma turu: rampa + Gün Patlaması + soğuma |
| Tengri Bağı (dokun) | 20,1 / 20,0 (-%0,7) | 54,3 / 53,9 | düğüm / çekiş sırayla (×1,15); hasar payı (çok hedef) sayılmaz |

İlk ölçümden sonraki ayar: Gün-Ay 7 → 8,4, Albastı 4,6 → 5,6, Çevgen 18 → 19,5, Tatar 36 → 39 (kritik çarpanı 1,7 →
1,5); Kusursuz Kurma penceresi %42-60 → %62-78 ve Kut oku ×1,5 → ×1 (beceri tavanı +%349 → +%113); Küzgü kartı
patlamanın kritiğini sayar (önce ölçülen +%11).

### Tempo (`-- --dovus --boss`, seri basış)

Basış→temas / zincir aralıkları: Gün-Ay (Gün) 183 ms / 700, 683, 583 · Kistin 317 ms / 450, 450, 467 · Albastı 150 ms /
250, 250, 250 · Çevgen 300 ms / 433, 517, 550.

### Test

* `-- --silah27 --boss` (yeni, `tools/tests/silah27_testi.gd`): her silahın mekaniği oyunun girdi yolundan — Gün çarkı
  arkadakine de değer, basılı tutunca Ay duruşu (sprite, zincir), geri Gün; Dolama bağlar, Yere Çalma düşmanı arkaya
  geçirir, altındakine hasar, bağsız dördüncü adım yok, ağır yaratık çalınmaz; üç al izi, Göç izlinin arkasında belirir
  ve kritik; Çevgen topu fırlatır, çarptığına vurur ve onu da fırlatır; Tatar oku iki düşmanı deler, altın yerde basış
  anında kurar, Kut oku kesin kritik, erken basış takılır; Küzgü ışını kızar (ilk tik 1,2 → son 23), Gün Patlaması,
  soğumada açılmaz, bırakınca döngü sesi durur; Tengri Bağı iki düşmanı bağlar, hasar payı, Bağ Çekişi çarpıştırır;
  kart SnH ve açıklama, parşömen havuzu. `SONUC GECTI HATA=0`. Çekim: `--pencere=1920x1080 --silah27_goruntu=<klasör>`
  (headless değil; `--doku=2 --pencere=2560x1440` HD).
* `--dovus --boss` ve `--kontrol` (yeni silahlar TEMPO ve kontrol listelerinde): TAKILMA=0, `basılmamış=0 oto_dönüş=0
  oto_hamle=0 istenmeyen_ağır=0`.
* `--tomar --boss` GECTI (en büyük fark %4,1), `--tomar --boss --uzak` GECTI (yeni `UZAK27` denetimi: kart ↔ ölçülen
  %7), `--yay --boss` TAKILMA=0 CEPHANE_HATA=0, `--unsur --boss` HATA=0, `--denge --denge_muhur=0` BITTI,
  `--tuccar --muhur=0` GECTI, `--otomatik --derinlik=1/5 --muhur=0` ve `--mekanik --muhur=0`: betik hatası 0,
  `--piksel_tara --otomatik --derinlik=3` ve `--piksel_tara --silah27 --boss` TOPLAM 0.

### Bilinen

* Gün-Ay İkizi'nin duruşu oyuncuya bağlı tek durum (`Silah27.gunay`): yuva değişince / yeni koşuda korunur; kart her
  zaman o anki duruşun SnH'sini gösterir (iki duruş birbirine yakın dengelendi; Ay duruşu ölçülmedi).
* Fırlatılan / çalınan düşman konumu doğrudan sürülür (çarpışma: top `move_and_collide`, Yere Çalma iniş noktası
  arkada duvar varsa öne alınır); çok dar geçitlerde iniş noktası duvarın dibine düşebilir.
* Kistin ve Çevgen silah sprite'ı katı (zincir / sap esnemez): savruk hissini iz ve dolanan zincir çizimi verir.

## v27: sanatsal animasyonlar ve metal kritik sesi

Geri bildirim: "Bütün silahların animasyonlarını sanatsal yapın." · "Kritik sesi daha metal olsun — kılıç çarpışması sesi
gibi."

### Sanatsal animasyonlar (`scripts/actors/SanatAnim.gd`, `scripts/core/InkAksanFX.gd`)

Hedef v25 Yıldırım Kılıcı ölçüsü: her adım kasıtlı, pozdan poza bir hareket. Yeni katman tamamen GÖRSEL: savuruş
anahtarlarının ZAMANLARI (`hit`, `ck`, `multi`, `hold_k`), TEMPO / TEMPO_V25 / TEMPO_V26 evreleri, vuruş kutuları
(`_swing_box` savuruş adıyla, sabit), ara bellekler ve v22 kontrol kuralları aynı. `Player` yalnızca küçük kancalar aldı
(`_start_attack` / `_begin_heavy` görsel savuruş kopyası + `atk["art"]`, `_plane_at` adım düzlemi, `_feel` gövde,
`_update_weapon_visual` süsleme / leke / yay-fırlatma-büyü pozları, vuruş penceresinden çıkışta takip vurgusu,
`_slam_contact` çatlak, ilk isabette pençe izi; `Okculuk` kiriş şaklaması). Karşılaştırma için `-- --sanat_kapali`
v26 görünümünü verir (aynı yapı; önce / sonra şeritleri ve ölçümler bununla).

1. **Poz (aile biçimlemesi, `SanatAnim.AILE`):** derin hazırlık anahtarında kol ve bilek vuruş yönünün tersine bir tık
   daha kurulur (`cock`: hançer 0,34 / 0,65 rad, kırbaç 0,39 / 0,72, kılıç 0,29 / 0,42, ağır 0,26 / 0,29 ...), temasta ön
   kol gerilir (`ext`), takipte vuruş yönünde aşar (`fol`, iki anahtara yayılarak). Bitiriş ve ağır saldırıda ×1,3.
   Çarklar, seri saplama, çevrim ve fırlatma biçimlenmez; Yıldırım Kılıcı'nın v25 anahtarları elle çizilmiş olduğundan
   biçimlenmez (yalnızca gövde ve bitiriş süslemesi). Elle çizilmiş anahtarlar (`KEYS`): İkiz Balta'nın iki doğraması artık
   hançer fiskesi değil, iki elle baş üstünden ve alttan ağır doğrama. Ters tutuş (`ters`): Böri Hançeri'nin ilk iki
   kesiği, İkiz Bıçak'ın ikinci kesiği (bıçak ön kol boyunca geriye; vuruşu yumruk taşır, bıçak arkadan biçer).
2. **Düzlem (`SILAH.pl`):** zincirin her adımına [phi farkı, r çarpanı, roll farkı] (±4-12°, ×0,86-1,12, ±10-22°): her
   adım başka eğimde hilal çizer; aynı savuruşu iki kez kullanan zincirlerde (kargı, tulpar, ikiz bıçak, ay palası) iki
   adım artık aynı görünmez. Temas anında bıçak büyük eksene yakın kaldığından görünen erim ~%98-102.
3. **Gövde (hareket çizgisi):** `anim.skew` ile üst gövde eğikliği (ayaklar yerde sabit kalır; baş öne / arkaya kayar)
   + mevcut dönme; hazırlıkta geriye toplanır, süpürmede öne yüklenir, kilitte tutar, toparlanmada oturur (`_curve`;
   aile değerleri `lean`, `skew`). Ezilme-esneme yayının artık bir hedefi var (`scale_target`): vuruşun dikey yönü
   anahtarlardan bulunur — aşağı vuruşta hazırlık uzar / temasta ezilir, yukarı vuruşta hazırlık çömelir / temasta
   uzar, yatay ve saplamada gövde içe toplanır / temasta öne gerilir. Ağır bitiriş çakmasında gövde yere çöker (1,2 / 0,82).
4. **Bitiriş süslemesi (`SILAH.fin`):** son adımın kilidinin ikinci yarısından toparlanmanın sonuna dek kol pozuna
   karışan imza hareket (toparlanma 0,2-0,32 sn; yeni basış süslemeyi keser, kol oradan akar). Ağır saldırı da alır.

| Aile / silah | Bitiriş süslemesi |
|---|---|
| Alp, Ayaz, Yıldırım (gecikmeli) | **kın**: kan silkme (kol öne, bilek bıçağı aşağı silker), el kalçaya, bıçak geriye kına; "çıt" parıltısı + `kin_kapa` sesi |
| Ruh, Yılan, Rüzgâr | **çevir + kın**: bıçak elde bir buçuk tur döner, sonra kına |
| Yatağan | **selam**: bıçak yüzün önünde dik, aşağı-dışa silkilir, kına |
| Pala, Gürz, Çivili Topuz, Savaş Baltası, Dağ / Kor Çekici | **omuz**: baş yükselir, omza oturur (gövde hafif ezilir, üst gövde geriye) |
| Ulu Kılıç, Bozgun Kılıcı | **dik**: kılıç havaya kalkar, ucu yere dikilir (toz + fırça noktası) |
| İkiz Bıçak, Böri Hançeri, Ay Palası, İkiz Balta | **çevir**: bıçak elde döner, ters tutuşla aşağıda biter |
| Kargı, Tulpar | **mızrak**: mızrak elde bir tur döner, dibi yere, ucu göğe dikilir |
| Teber, Kayın Asası | **sırık**: sırık baş üstünde döner, yere dikilir |
| Erlik Tırpanı | **tırpan**: bir tur, sonra omuzların ardına asılır |
| Kement, Od Kamçısı | **şaklama**: el geriye çekilip öne silkilir — ikinci şaklama (uçta yıldız + şak sesi) |
| Kurt Pençeleri | **pençe**: pençeler havada (uluma duruşu) |

5. **Leke kareleri:** silah hızlı dönerken (karede 0,24-2,6 rad) bir önceki kareyle arasına iki soluk kopya (%34 / %16).
6. **Mürekkep vurguları (`InkAksanFX`, 0,2-0,5 sn, ince):** zincir adımlarında takipte uçtan fiske (hançer, düello) /
   fırça noktası (kılıç, mızrak, İkiz Balta) / kırbaç yıldızı; bitirişte bıçak ucunun son yayı boyunca hat fırçası
   (başı bastırılmış, kuyruğu kuru kıllara ayrılan tek darbe; çarkta "ensō" gibi halka) ya da hilal girdabı (Ruh,
   Rüzgâr, Ay Palası, Kayın Asası); ağır çakmada yerde dallanan çatlaklar; Kurt Pençeleri isabetinde üç paralel tırmık;
   kına koymada parıltı; yay bırakışında kiriş şaklaması. Hepsi bıçakta / takip yönünde doğar, düşmanı örtmez
   (düşmanlı şeritte okunur kaldı). Çizim parça parça dörtgen (`draw_primitive`: kıvrık yolda üçgenleme hatası yok).
7. **Yay / fırlatma / büyü:** gerilirken gövde arkaya yaslanır, yay kolu tam uzanır, gövde hafif uzar; bırakışta geri
   teper ve sönümlü oturur. Fırlatma (`THROW_KEYS`; bırakış anı aynı, tk 0,25): baş arkasına kurulur, gövde toplanır,
   bilekten savrulur, kol gövdenin önünden aşağı iner; silah elden çıkınca elde artık görünmez (eskiden aynı cirit elde
   de kalıyordu). Büyü: Gök Asası göğe kalkar ve öne iner, Kam Kopuzu göğüs önünde tıngırdatılır, Yel Borusu ağza
   götürülüp öne uzatılır.

Kare şeritleri (`tools/tests/firca_testi.gd`, yeni bayraklar): `--firca_tam` zincirin tamamı (4-5 adımlı silahlarda
bitiriş dahil; her kare için `[firca] faz <silah> <kare> <savuruş> <evre> <ad>` satırı), `--firca_uzak` ikincil silah
(yay 0,7 sn gerilip bırakılır, fırlatma / büyü bir kez). Kontak sayfaları (önce / sonra, anahtar kareler: hazırlık,
süpürmenin her karesi, kilit, toparlanma): `docs/v27/aile_kilic.jpg`, `aile_duello.jpg`, `aile_hancer.jpg`,
`aile_agir.jpg`, `aile_dev.jpg`, `aile_uzun.jpg`, `aile_mizrak.jpg`, `aile_kirbac.jpg`, `aile_uzak.jpg`.

### Metal kritik sesi (`tools/audiogen/v27.py`, `Ses.HIT_TIERS`)

v26 kritiği gür ve kirliydi ama ağırlığı alt-orta gövdedeydi (yumruk / kemik). Yeni ses kipsel (modal) sentezle kılıç
çarpışması: (1) çarpma tıkı 3-16 kHz; (2) sıyırma: merkezi 9 → 3,5 kHz kayan, tarak süzgeçli, tanecikli dar bant gürültü
(35-60 ms); (3) çınlama: iki bıçak = iki kip takımı (temel 1,18-1,45 kHz ve 1,56-1,88 kHz; serbest çubuk / burulma
oranları 1-6,7 kat → ~1,2-9 kHz), her kip ±1-3,5 Hz iki kola ayrılır (dövünme), alt kipler 0,4-0,5 sn, üst kipler
0,09-0,2 sn'de söner, vuruşta perde %0,4 düşer; (4) ağırlık için kısa, kısık alt yumruk (170 → 60 Hz, 0,1 sn) +
impactPunch_heavy (CC0); (5) hafif geçiş biçimleme, paralel sıkıştırma, yumuşak kırpma, küçük metalik oda. Künt çeşit örs
"DANG": temel 580-810 Hz, örs / çan oranları, 0,6 sn çınlama, daha güçlü gövde. Beş bıçak (`darbe_kritik_1..5`), dört
künt (`darbe_kritik_kunt_1..4`) çeşidi; `HIT_TIERS` kritik perde oynaması ±%4 → ±%6. Yönlendirme v26 ile aynı (Krit veri
yolu, `krit_duck`, tüm kritik yolları). Yeni `kin_kapa` (kına koyma "çıt"ı, -18 dB).

| | süre | yükseklik | 80-200 Hz | 200-1k | 1-5k | 5k+ |
|---|---|---|---|---|---|---|
| v26 darbe_kritik_1..4 | 0,24 sn | -7,3..-7,5 | -2,4..-4,6 | -8,2..-10,8 | -4,8..-6,6 | -10,7..-12,3 |
| v27 darbe_kritik_1..5 | 0,52 sn (çınlama ~0,3 sn duyulur) | -7,1..-7,6 | -5,6..-9,3 | -13,8..-15,0 | **-1,4..-3,1** | -9,4..-13,1 |
| v26 darbe_kritik_kunt_1..3 | 0,28 sn | -7,4..-7,5 | -3,8..-5,4 | -6,6..-8,3 | -7,3..-8,1 | -16..-19 |
| v27 darbe_kritik_kunt_1..4 | 0,6 sn | -7,3..-7,7 | -6,0..-7,8 | -4,2..-6,5 | -4,7..-8,5 | -19..-22 |

(Bant payı ilk 0,3 sn enerjisinin, dB.) Dalga biçimi ve spektrogram: `docs/v27/kritik_ses.png` (v26 geniş bant gürültü
lekesi → v27 belirgin, sönen çelik kip çizgileri). Yeniden üretim: `python tools/audiogen/export_audio.py --sfx
darbe_kritik darbe_kritik_1 ... darbe_kritik_5 darbe_kritik_kunt_1 ... darbe_kritik_kunt_4 kin_kapa`; karşılaştırma:
`python tools/audiogen/v27.py --karsilastir <v26_klasörü> <png>`.

### Ölçüm ve test

Önce / sonra aynı yapıda (`--sanat_kapali` ile v26 görünümü), 60 Hz:

* `--dovus --boss --hiz`: 27 silahın tamamında basış→temas ve zincir aralıkları (%0 sütunu) önce / sonra BİREBİR aynı
  (ör. İkiz Bıçak 167 / [267, 217, 383], Alp 183 / [400, 433, 483], Gürz 317 / [517, 650, 550], Ulu Kılıç 400 /
  [617, 1050, 617]); fark yalnızca rastgele atılan Kızışma niteliğinde. En az kare ihlali 0.
* `--dovus --boss`: TAKILMA=0; OZET vuruş (basış→temas) ±1 kare içinde (İkiz Bıçak 133 → 133, Yatağan 150 → 133, Alp
  150 → 150, Kargı 133 → 133, Ulu 350 → 350, Dağ Çekici 350 → 366 ms; aynı sürüm art arda koşularda da 1 kare oynuyor).
* `--dovus --boss --kontrol`: TAKILMA=0, basılmamış=0, oto_dönüş=0, oto_hamle=0, istenmeyen_ağır=0.
* `--savurus`, `--yay --boss` (TAKILMA=0, CEPHANE_HATA=0), `--unsur --boss` (HATA=0), `--tomar --boss` (GECTI, en büyük
  fark %3,0), `--otomatik --derinlik=1 --muhur=0`, `--piksel_tara` (TOPLAM 0): betik hatası 0.

### Bilinen

* Gövde sprite'ları önceden çizilmiş (`atk_*`); gövde katmanı yalnızca eğiklik, dönme ve ezilme-esneme ile çalışır,
  ayak adımları sprite'taki gibi.
* Dev kılıcın "dik" süslemesinde bıçak yere değince `_ground_clamp` onu hafif yatırır (uç toprağa yaslanmış görünür).
* Bitiriş süslemesi toparlanma süresine sığar (0,2-0,32 sn); zinciri hemen yeniden başlatan oyuncu süslemenin başını görür.
* Kare şeritlerinde silah nitelikleri rastgele atıldığından kare sayıları önce / sonra birkaç kare farklı olabilir
  (zamanlama ölçümü `--hiz` ile).


## v27: savaş sanatları

İstek: "Sekiro'daki gibi Savaş Sanatları (Combat Arts) deneyelim." Her sanat bir kaynak harcayan, kendine özgü
animasyonlu (v23 3B savuruş düzlemi + mürekkep efekti), sesli, vuruş duraklamalı ve okunur telegraflı özel bir teknik.
Tek sanat kuşanılır, T ile kullanılır. Kod: `scripts/actors/SavasSanati.gd` (çekirdek, sekiz sanat), `scripts/core/SanatFX.gd`
(mürekkep efektleri, fırça yardımcıları, tamgalar), `scripts/ui/SanatUI.gd` (HUD halkası, kart, menü); bütün sayılar
`data/sanatlar.json`. Player.gd'ye yalnızca birkaç kanca (`sanat.tick`, take_hit'te `karsila` / `alinan_k`, `_deal`'de
`on_deal`, `atk.plane` düzlem geçersiz kılması); mevcut SWINGS / PLANES verisine dokunulmadı.

### Kaynak: Alp Nişanı (ayrı ölçer; neden Kut değil)

Kut (F) 0-100 dolup Bozkurt biçimine harcanıyor ve hasarla doluyor (`add_kut(d × 0,22)`). Sanatlar da Kut harcasaydı iki
güç birbirini yerdi; ayrıca Kut tomarla / derinlikle büyüyen hasarla şiştiği için sanat sıklığı derinlikle bozulurdu.
Sekiro'nun "Spirit Emblem"i gibi **ayrık taneler**: Alp Nişanı, en çok 5, koşu başında 2 (hemen denenebilsin),
derinlikler arasında taşınır (`Game.run.nisan`), yeni koşuda sıfırlanır. 1 nişan = 100 birim. Kazanç (`sanatlar.json` "nisan"),
düşmanın canına oranla (derinlikten bağımsız):

| Olay | Kazanç |
|---|---|
| yakın vuruş (sıradan / seçkin) | 40 × hasar / düşmanın azami canı (vuruş başına en çok 10) |
| boss'a vuruş | 160 × hasar / azami can (en çok 6): bütün boss ~1,6 nişan |
| ok / fırlatma | yukarıdakinin %60'ı |
| öldürme | +12 (seçkin +40) |
| Çarpışma / Karşı Vuruş / Kut Alma | +35 / +20 / +40 |
| duruş kırma / Kut Mührü / Kusursuz Kaçış | +15 / +15 / +25 |

Sanatın kendi vuruşu ve kendi kırdığı duruş nişan vermez (kendini besleyen döngü yok). Ölçüm (`--sanat`): 60 canlı
sıradan düşmanı yakın dövüşle öldürmek 38 birim (~0,4 nişan). Bir sanat 1-2 nişan: ustalıksız oyuncuda 3-5 sıradan
düşman ya da bir seçkin, çarpışma / kusursuz kaçış yapan oyuncuda tek dövüş. Sanat 1-3 dövüşte bir; ayrıca her
sanatın beklemesi var (art arda basılamaz). Bilinen bir sanatın tomarı +2 nişan verir.

### Tuş

| | Klavye | Oyun kolu |
|---|---|---|
| Savaş sanatı | **T** (v25'te Üç Âlem'le boşaldı; sol elin altında, E / R / F'nin yanı) | **LT** (sol tetik, v25'ten beri boş; RT = don) |
| Kasırga ek tur | dönerken T | LT |
| Demir Duruş uzatma | T basılı (0,9 → en çok 1,4 sn) | LT basılı |
| Sanat seçimi | duraklat (Esc) → T | Start → LT |

Sanat yalnızca basışla başlar (v22 kontrol ilkesi); içindeki dizi (Kasırga turları, Göğe Yükseliş dalışı, Bozkurt
Atılışı'nın kın kesiği, Demir Duruş karşılığı) basılan sanatın parçasıdır. Başlar: boşta, saldırı hazırlığında /
toparlanmasında / şarjda, isabet iptali penceresinde, yuvarlanmanın ikinci yarısında (keser), gerilirken (bırakır);
infaz ve dalış sürerken başlamaz. Ara bellek 0,16 sn. Reddedilen basış (sınıf, bekleme, nişan) kısa yazı, gri ses ve
halka sallanması verir. Güncellenen ipuçları: HUD halkasında T, duraklatma tuş satırı, başlık ekranı kontrol satırı,
öğretici kartı "sanat" (sanat ilk hazır olduğunda), yurt başlığı (Alp Ata sanat öğretir).

### Sanatlar

Hasar = kuşanılan silahın hasarı × çarpan; `Player._deal` üzerinden (tomar, kritik, unsur, durum etkileri aynen).

| Sanat | Etki | Nişan / bekleme | Hasar · duruş · boss | Sınıflar |
|---|---|---|---|---|
| **Kasırga Kesişi** (başlangıç) | 0,18 sn çömelip bıçağı geriye alır; eğik elips düzlemde (r 0,36; bıçak arka yarıda gövdenin arkasında) 0,3 sn'lik doğrusal hızlı tam turlar; yarım turda bir iki yanı biçer, çevredeki hafif düşmanları içeri çeker, yön tuşuyla yavaş yürünür. Dönerken T: ek tur (0,5 / 1 / 1,5 nişan, en çok 3). Son yarım tur dışarı savurur. Dönen rüzgâr fırçaları | 1 / 4 sn | tur başına 2 × ×0,7, son ×1,15 · 1,2 · ×0,7 | hançer, düello, kılıç, mızrak, uzun sap, ağır, dev |
| **Bir Çekiş** | 0,42 sn okunur kaldırış (silah baş üstünde titrer, uçta çelik yıldızı), dik "C" düzlemde tek iniş; yerde mürekkep yarığı, toz, şok, darbe karesi. Kalkanı düşürür, (boss dışı) duruşu kırar. Ardından 3 sn **Demir Gönül**: alınan hasar -%35 | 2 / 6 sn | ×3,2 · 9 · ×0,6 | düello, kılıç, uzun sap, ağır, dev |
| **Ay Hilali** | iaido çekişi (yassı yatay düzlem); bıçaktan 330 px/sn giden ay mürekkebi hilali (siyah kontur, ak çekirdek, yankı hilaller, kuru fırça kılları), 300 px, en çok 6 düşmanı deler, duvarda kırılır | 1 / 3 sn | ×1,6 · 1,5 · ×0,75 | düello, kılıç, uzun sap, dev |
| **Göğe Yükseliş** (v28: yeniden yapıldı, bkz. "v28: sanat görselleri ve Göğe Yükseliş") | yükselen kesik sıradan düşmanları oyuncuyla birlikte kaldırıp havada kilitler (seçkin / boss / ağır kalkmaz), tepede üç kesiklik hava kombosu, düşmanları yere çakan dalış: GÜM!, çevreye alan hasarı. Hava kombosu kısıtının bilinçli istisnası (açık sanat) | 2 / 6 sn | ×1,2 + 3 × ×0,6 + çakılma ×2,8 · 2,5 · ×0,6 | hançer, düello, kılıç, mızrak, uzun sap |
| **Bozkurt Atılışı** | 0,14 sn çekilip 0,11 sn'de 150 px atılış (dokunulmaz), geçtiği herkese saplama; bıçak kına girince "çıt" ve geçilen herkeste çapraz şimşek kesik (Ashina Cross hissi) | 1 / 3,5 sn | geçiş ×1,6 + kın ×0,9 · 2 · ×0,7 | hançer, düello, kılıç, mızrak |
| **Kam Darbesi** | kam davulu; kabza öne açık avuç darbesi, avucun önünden tayfsı ruh kurdu atılır (kurt biçiminin solan kopyası), mor mürekkep patlaması + şok. Zırhlı (!!) hamleyi keser, kalkanı düşürür, duruşu kırar, 1,2 sn sersem | 2 / 5 sn | ×1,0 · 10 · ×0,5 | her yakın silah (kırbaç dahil) |
| **Ok Yağmuru** | geri sıçrayıp göğe alevli ok; öndeki en yakın düşmanın (260 px) çevresine 1,1 sn'de 18 ok yağar; yerde mürekkep halkası, saplanan okta toz | 2 / 7 sn | ok başına yayın ×0,45 · 0,6 · ×0,7 | yay (iki yuvadan birinde) |
| **Demir Duruş** | silah önde, çelik parıltılı duruş (0,9 sn; T basılıysa 1,4). Öndeki darbe ya da mermi **örse vurur gibi seker** (hasar yok, mermi ×1,5 geri döner, saldıran sersem), "ÖRS!", darbe karesi, ağır çekim; hemen saldırana atılıp büyük çekiş (kesin kritik). Boşa giderse 0,3 sn açık (süper zırhsız) | 1 / 4 sn | ×2,6 kesin kritik · 6 · ×0,6 | düello, kılıç, mızrak, uzun sap, ağır, dev |

Ortak: sanatlar süper zırhlı (hasar alınır, sanat kesilmez; Demir Duruş açığı hariç); Bozkurt Atılışı ve Demir Duruş
karşılığı dokunulmaz. Telegraf: oyuncunun arkasında kendini çizen fırça ensō'su ve içinde sanatın tamgası, sanatın adı,
kısa parlama, `sanat_baslat` sesi. Vuruşlar sanatın paletinde mürekkep sıçrantısı (çok vuruşlu sanatın ara vuruşları
hafif kademe), kritikte damga; geçiş başına bir duraklama (Game.hitstop dip eğrisi ve v25 kayıp zaman bütçesi aynen).
Bosslara hasar (boss_k) ve duruş (×0,6, boss sendeleme ölçerine) azaltılmış. Sınıf `Player._tempo_class`'tan (yeni
silahlar kendi sınıflarıyla otomatik). Uymayan silahta halka gri + çarpı, kartta "kullanılamaz".

Animasyon: her karede kol pozu ve düzlem (phi, r, roll) `SavasSanati._seq` anahtarlarından hesaplanıp Player'ın atk
sözlüğüne "önceki kare → bu kare" olarak yazılır (`atk.sw.keys`, `atk.plane`); kol, silah önkısalması, arkada çizilen
bıçak ve InkTrail hilali Player'ın kendi kodundan geçer (sanatın paletinde, katmanlı, uzun ömürlü). TEMPO'nun yumuşak
anahtarlarıyla yapılamayan hareketler (doğrusal hızla dönen kasırga, havada askı, dalış) böylece mümkün.

Sesler (`tools/audiogen/v27.py`, sentez; export_audio.py'ye kayıtlı): sanat_baslat, sanat_hazir (yeni nişan / sanat
hazır), sanat_kasirga, sanat_hilal, sanat_cekis, sanat_yuksel, sanat_atilis, sanat_kin, sanat_kam, sanat_ors.

### Kilit ve kuşanma

* **Kasırga Kesişi** baştan açık ve kuşanılı (neredeyse her silahla; ilk koşuda T ile denenir).
* **Alp Ata** (yeni yurt sakini; `tools/artgen/alp_ata_ink.py`, `python export_ink.py --alp_ata` → `npc_alp_ata_v2`):
  sivri demir miğferli, kızıl tuğlu, çatal ak bıyıklı, örgülü ak sakallı, pul zırhlı, omzunda bozkurt postu, önüne dikili
  ulu kılıca yaslanan yaşlı alp; konuşurken eli öğretir gibi kalkar. Yurtta çadırın önünde (karo 71). W ile konuşulur →
  **Alp Ata ekranı**: solda sekiz sanat (tamga, durum, nişan, bedel), sağda kart (açıklama, nişan, bekleme, hasar,
  sınıflar, kuşanılan silahla uygun mu, öğrenme bedeli). Boşluk: kilitliyse Kut bankasından öğretir ve kuşandırır
  (Ay Hilali 40, Bozkurt Atılışı 45, Kam Darbesi 50, Ok Yağmuru 50, Demir Duruş 55, Bir Çekiş 60, Göğe Yükseliş 70 Kut),
  açıksa kuşandırır.
* **Sanat Tomarı** (koşuda): boss kesin, seçkin %12 bırakır (açılmamış sanat kaldıysa; kızıl-altın parşömen). Dokununca
  sanat kalıcı olarak açılır ("Duraklat → T ile kuşan").
* **Her an**: duraklatmada T → Savaş Sanatları ekranı (yalnız kuşanma). Kayıt: `meta.sanat_acik`, `meta.sanat_secili`.

### HUD

Kut ve don halkalarının sağında sanat halkası: mürekkep ensō ve sanatın tamgası (fırça), bekleme yayı ve kalan saniye,
hazırken renkli yıkama ve nabız, uymayan silahta gri + kızıl çarpı; sağında 5 Alp Nişanı tanesi (dolu / kısmen dolu;
sanatın bedeli kadar tane renkli çerçeveli, yeni dolan tane parlar), altında T tuşu ve sanatın adı.

### Test

* `-- --sanat --boss --muhur=0` (yeni, `tools/tests/sanat_testi.gd`): her sanat uygun silahla 3 mankene tetiklenir
  (başladı, nişan harcaması = bedel, bekleme, isabet, hasar, süre), Kasırga ek turu, sınıf kuralı + sınıf tablosu
  (8 sanat × 8 silah), Ok Yağmuru'nun yay şartı, bekleme ve nişan yetmezliği reddi, Demir Duruş karşılığı (hasar yok,
  karşılık isabeti) ve boşa giden duruş, Demir Gönül, sanat sırasında hasar (süper zırh sürer), nişan kazancı
  (öldürme, çarpışma, kusursuz kaçış), varsayılan kilit, Alp Ata'nın öğretmesi (banka düşer, yetmeyen bedel reddedilir),
  kalıcı kayıt (kaydet + yeniden yükle), Sanat Tomarı. Her denetimden sonra 2 sn girdisiz takılma denetimi.
  Sonuç: SONUC GECTI hata=0, TAKILMA=0. `--sanat_iz` ayrıntılı günlük, `--sanat_tek=<id>` tek sanat.
* Kare şeridi (headless değil): `--fixed-fps 60 -- --sanat --boss --pencere=1920x1080 --sanat_kare=<klasör>`.
* Ekran görüntüleri: `--ekran=sanat` (duraklatma ekranı), `--yurt --ekran=ogretmen` (Alp Ata ekranı),
  `--ekran=sanat_hud` (HUD halkası), `--yurt --ekran=alp_ata` (yurtta Alp Ata).
* Gerileme (v27 sonrası): `--dovus --boss --kontrol` KONTROL basış=182 savuruş=102 basılmamış=0, TAKILMA=0;
  `--dovus --boss` TAKILMA=0; `--tomar --boss` GECTI; `--zeka --muhur=0` BITTI; `--yurt --yurt-tur` dört NPC görüldü
  (Alp Ata dahil), kapıya varıldı; `--otomatik --derinlik=1/5 --muhur=0` ve `--mekanik --muhur=0`: betik hatası 0;
  `--piksel_tara` TOPLAM 0.

## v28: sanat görselleri ve Göğe Yükseliş

İstek: "Savaş sanatlarını beğendim. Ama Göğe Yükseliş mobu havaya kaldırmıyor. Seçkinleri kaldıramamalı ama sıradanları
yukarı alıp kilitlemeli, havada kombo yapıp yere GÜM diye çakmalı. Sanat animasyonlarında daha sanatsal görseller olsun:
yüksek kaliteli mürekkep."

### Göğe Yükseliş: kaldırıcı sanat (`SavasSanati._goge`, `Enemy._sanat_kilit`)

Tek T basışı, baştan sona tek dizi (v22: açık sanat, içindeki her şey basılan sanatın parçası):

| Bölüm | Süre | Ne olur |
|---|---|---|
| hazırlık | 0,14 sn | çömelme, yerden ayağa toplanan kuru fırçalar, telegraf ensō'su |
| yükseliş | 0,24 sn | yükselen kesik: kutudaki herkes vurulur (×1,2). **Sıradan** düşmanlar (seçkin / boss / ağır değil) kilitlenir ve oyuncuyla birlikte kalkar; seçkin, boss, ağır yalnızca hasar + duruş + 0,6 sn sersemlik alır ("kalkmaz"). Oyuncu hedef yüksekliğe yumuşak eğriyle çıkar (en çok 112 px) |
| tepe | 0,47 sn | askı: oyuncu ve kilitli düşmanlar havada (düşmanlar oyuncunun önünde 15 px aralıklı dizili, küçük salınım). Üç kesik: inen çapraz, yükselen çapraz (ikisi havada X yazar), geniş yatay hilal; her kesik kilitlilere kesin isabet (×0,6), vuruş duraklaması (0,055 / 0,055 / 0,07), düşmanlar kesik yönünde sarsılır ve döner |
| dalış | 0,09 + iniş | silah baş üstüne kalkar, sonra oyuncu 980 px/sn, düşmanlar 1150 px/sn (önce yere varırlar) oyuncunun önünde çakılır; yoldaki başka düşmanlara ×0,6 |
| çakılış | — | **GÜM!**: kilitli her düşmana dalış ×2,0 + çakılma ×0,8 (sersem 0,9 sn, yerden küçük sekme); çevredeki diğerlerine (±80 px) ×2,0 alan hasarı; şok dalgası, sarsıntı 0,85, yakınlaşma, ağır çekim, darbe karesi, `sanat_gum` sesi, mürekkep "GÜM!" damgası |
| toparlanma | 0,32 sn | |

Kilit (`Enemy.sanat_tut`): düşman her karede tazelenen bir süreyle havada tutulur; yerçekimi, yapay zekâ, temas hasarı
ve tehlike denetimi o sürede yok, hareket hedefe yay gibi (`move_and_slide`: duvara, tavana giremez). Tazelenmezse
(sanat kesildi, oyuncu öldü / kavrandı) kilit 0,25 sn içinde kendiliğinden düşer (olağan düşüş). Çakılışta
`sanat_dus` hızlı düşüş, yere değince `sanat_indi`, ezilme, toz, sersemlik.

Tavan: kaldırma yüksekliği oyuncunun sütununda (baş üstü) ve her yakalanan düşmanın hem bulunduğu hem dizileceği
sütunda (gövde boyu + pay) taranır (`_tavan`: katı karo, tek yönlü platform sayılmaz) ve en dar olana kısalır. Alçak
tavanda dizi aynen sürer, yalnızca daha alçakta.

`data/sanatlar.json` göğe: `tepe_hasar` 0,9 → 0,6 (iki yerine üç kesik), yeni `carpma_hasar` 0,8, `kaldirma` 112,
`alan` 80. Toplam (kaldırılan düşman): ×1,2 + 3 × ×0,6 + ×2,8 = ×5,8 (v27: ×5,0); kalkmayan seçkin: ×1,2 + alan ×2,0.

### Sanat görselleri: sumi-e mürekkep (`scripts/core/SanatFX.gd`)

v27'nin düz renkli çokgen fırçaları yerine **dokulu fırça darbeleri** ve **atlas lekeleri**:

* **Fırça darbesi** (`_bs`, `shaders/sanat_firca.gdshader`, `assets/fx/ink/sanat_firca.png`): değişken genişlikli
  şerit; u = darbe boyunca (baş → kuyruk), v = enine. Doku 8 fırça (ıslak ağır, orta, kuru, çok kuru / yarılan, sulu
  kenarlı, hızlı ince, kalın kuru, sıçratan): R mürekkep yükü (başta dolu ve ıslak, kuyruğa doğru kıllar tek tek kopar:
  "uçan ak"), G kenarda ve başta toplanan koyu mürekkep, B kıl kimliği (kuruma / erime sırası), A kâğıt tanesi. Darbe
  **çizilerek** açılır (fırça ucu ilerler, uç ıslak ve parlak), bekler, kıllar koparak erir. Biçemler: sumi siyahı (paletten
  yalnızca bir tutam), paletin rengi (kıl damarlı), ışıyan çekirdek, sulu yıkama (yansız gri-siyah), altın varak (maden
  parıltısı), yalnız kıllar.
* **Leke** (`assets/fx/ink/sanat_fx.png` + `sanat_fx.json`, InkFX atlas kodlaması ve `ink_fx.gdshader`): sıçrantılar
  (`splat_a/b/c`: siyah sumi lekesi, kenarı paletin renginde, üstünde küçük renkli sıçrantı), yıkamalar (`wash`, `wash_b`:
  kenarında kuruma halkası, granüllü; yeni yansız **sumi** paleti 13 ile karakterlerin arkasında), "GÜM!" fırça yazısı,
  altın varak pulları (`varak`, `varak_b`, palet 9), yer yarığı (`crack`), mühür.
* Üretim: `python tools/artgen/sanat_fx_ink.py [--onizleme <png>]`; HD (2 kat): `KY_HD=2 python sanat_fx_ink.py` +
  `python hd_paket.py --paketle` (`assets_hd/x2/fx/ink/sanat_firca.webp`, `sanat_fx.webp`, manifest). Önizleme:
  `docs/v28/dokular.png`.

Telegraf (her sanat): oyuncunun arkasında **kendini fırça fırça çizen** kalın kuru ensō (önce sulu yıkama, sonra halka,
içinde ince renkli damar), ardından sanatın tamgası **darbe darbe** (yazılış sırasıyla, her darbe 0,045 sn), köşede
renkli mühür izi. Tamgalar tek kaynaktan (`glyph_strokes`): HUD düz fırçayla, telegraf dokulu fırçayla çizer.

Sanat başına renk ve bileşim (palet `sanatlar.json` "pal"):

| Sanat | Renk | Görsel |
|---|---|---|
| Kasırga Kesişi | çam yeşili-turkuaz (palet 4; v27: 8) | dönen eğik elips boyunca 5 kalın kuru sumi darbesi (baş önde, kuyruk kuruyarak geride, arka yarı eriyen) + turkuaz damar + sulu yıkama halkası; son yarım turda dışa savrulan 12 fırça kılı ve iki yanda sıçrantı |
| Bir Çekiş | kızıl (0) | kaldırışta bıçak ucuna toplanan kuru fırçalar; inişte yukarıdan yere kalın ıslak sumi darbe (kızıl damar, ak çekirdek), yer yarığı, iki yana sulu sürtmeler, yukarı sıçrayan kıllar, sumi sıçrantı + altın varak, gri yıkama |
| Ay Hilali | ay gümüşü (7) | hilal üç katman fırça (ıslak sumi kontur, gümüş gövde, ak çekirdek), ardında sulu yıkama yankıları ve kuru hız çizgileri; çekişte oyuncunun ardında soluk dolunay (yıkama + kuru ensō) ve ileri uzanan ince hız çizgisi; kırılışta sıçrantı |
| Göğe Yükseliş | altın (9) | yerden göğe üç altın-sumi fırça (kuyruk tepede kuru), üç hava kesiği (X + yatay hilal, altın varaklı), dalışta yukarıdan aşağı çizilen hız çizgileri, çakılışta yer yarığı, iki yana sumi sürtme, yukarı kıllar, sıçrantı, varak, "GÜM!" damgası |
| Bozkurt Atılışı | şimşek mavisi (5) | atılış çizgisi boyunca kırık (zikzak) sumi şimşek + mavi damar + ak çekirdek + iki kuru çatal; çizgi boyunca koşan tayfsı mavi kurt (kurt biçiminin karesi) ve ardında mürekkep dumanı; kın kesiğinde her düşmanda şimşek X + sıçrantı |
| Kam Darbesi | mor (6; v27: 10) | davul hazırlığında avuca içe dolanan fırça sarmalı; vuruşta büyüyen iki ensō halkası, mor yıkama, sıçrantı; tayfsı mor kurt ve ardında eriyen mürekkep dumanı |
| Ok Yağmuru | od (1) | her okun ardında kuru fırça izi (havaya salınan ok dahil), hedef alanında yerde yassı fırça ensō'su + yıkama, saplanan okta küçük sıçrantı |
| Demir Duruş | dökme demir grisi (ek palet 12) + altın | duruşta önde çizilerek açılan kalın demir ensō kalkanı, üstünde gezen parıltı; ÖRS'te altın ışınsal fırça kılları, varak, sumi sıçrantı; karşılıkta altın varaklı büyük yatay sumi kesiği |

Sanat vuruşları: InkFX vuruşuna ek, kademe 2'de küçük sumi sıçrantısı + yönlü iki fırça kılı (`vurus_leke`). Okunurluk
(v22): hepsi kısa (0,2-0,7 sn), büyük yıkamalar gri ve karakterlerin arkasında (z -1), "GÜM!" düşmanların üstünde;
Bir Çekiş ve çakılışta eski yer şoku küçültüldü.

Ses: `sanat_gum` (`tools/audiogen/v27_sanat.py`, hedef -6,5 dB): iki katlı gövde vuruşu (taiko + alt bas düşüşü), toprak
ezilmesi, ıslak şaplak, taş çatırtısı, kısa altın çınlama, uzun gürleme. `python v27_sanat.py sanat_gum` yalnız onu üretir.

### Test

* `-- --sanat --boss --muhur=0`: v27 denetimlerine ek **Göğe Yükseliş kaldırma** (3 sıradan + 1 seçkin; açık alan ve
  ızgaraya geçici tavan konan alçak alan): kaldırılan = çakılan = 3, her sıradan ≥ 40 px (tavanda ≥ 12) kalkar ve tepede
  ≥ 12 kare kilitli, seçkin ≤ 10 px (kalkmaz), sonunda üçü de yerde, duvar / tavan içinde değil, kilit kalmamış; tavanda
  hiçbir kare düşmanın tepesi tavanı aşmaz. Sonuç: açık alanda H=112, kalkış 116-118 px, 37 kare kilit; alçak tavanda H=46, kalkış 51-52 px, tavan_üstü=0; seçkin kalkışı 2 px; yerde 3/3, kötü konum 0; SONUC GECTI hata=0, TAKILMA=0
* Kare şeritleri: `--fixed-fps 60 -- --sanat --boss --pencere=1920x1080 --sanat_kare=<klasör>` (Göğe Yükseliş 3 sıradan +
  1 seçkin dizilişiyle); efekt önizlemesi `--sanat_fx=<klasör>` (bileşimler oyuncu gizliyken tek tek).
* Görseller (`docs/v28/`): `goge_dizi.jpg` (tam dizi, her 2. kare), `once_sonra.jpg` (sekiz sanat v27 / v28),
  `fx_onizleme.jpg` (bileşimler), `dokular.png` (fırça ve atlas dokuları).
* Gerileme: `--dovus --boss --kontrol` KONTROL basış=272 savuruş=135 basılmamış=0, TAKILMA=0; `--zeka --muhur=0` BITTI; `--otomatik --derinlik=1` ve `--derinlik=5 --muhur=0`, `--mekanik --muhur=0` (BITTI): betik hatası 0; `--piksel_tara` TOPLAM 0.


## v28: gerçek gövde animasyonları

Geri bildirim: "Bütün silahlara gerçekten sanatsal animasyon ekleyelim — hâlâ çok basit görünüyor." · "Yıldırım
Kılıcı'nın şarjlı saldırısı isabet edince karakteri çok uzağa götürüyor — bu mesafeyi kısalt."

v27 katmanı (SanatAnim) yalnızca önceden çizilmiş gövde sprite'larını eğip döndürebiliyordu; darboğaz gövdenin kendisiydi.
Eski saldırı gövdeleri (v1 `bengu.py` anahtarları + `bengu_ink.dynamic`) bacak AÇILARIYLA kuruluydu: kalça kayınca
ayaklar yerde kayıyor, arka ayak çoğu karede yerden 3-10 birim havada asılı kalıyordu (ör. eski `atk_overhead_2h`
temasında arka ayak 10 birim havada), gövde yalnızca öne / arkaya yatıyordu; 8 kare savuruşun k zamanına eşit aralıkla
yayılıyordu (temas karesi çoğu savuruşta isabet anına denk gelmiyordu).

### Poz sistemi (`tools/artgen/bengu_govde.py`)
- **Ayak hedefli IK:** her anahtar kalça konumu + yerden yüksekliği ve iki ayağın yerdeki yeri, kalkıklığı ve topuk açısıyla
  yazılır; iki kemikli bacak IK'sı (`leg_ik`) açıları çözer, erişilemeyen yere basan ayak için kalça kendiliğinden iner.
  Yere basan ayak kaymaz; adım (ön ayak kalkıp ileri iner), kayarak duruş açma, çapraz adım, ön ayak üstünde dönme,
  arka ayağın parmak ucuyla itmesi (topuk açısı: `bengu_ink._leg` çizme + tabanı ayak bileği çevresinde döndürür)
  gerçek ayak işi olur.
- **Poz alanları:** gövde eğimi, omuz burulması / kayması, önden giden baş (`hdx`, `hdy`), arka kol (iki elli olmayan
  silahlarda oyunda bu açılarla sürülür: denge kolu, kabzadaki el, ikinci bıçak), etek / kuşak kuyrukları, nara (`jaw`),
  kulak ve yeni **post pelerin savrulması** (`cf`: hızlı harekette postun sırt kenarı geriye-yukarı tutamlı kanat
  olarak açılır; `cf = 0` iken çizim v27 ile birebir aynı — durgun, koşu vb. değişmez).
- **Dönüş (`turn`):** çark / pivot karelerinde gövde kalça ekseni çevresinde döner (yan görünüş en çok 0,6'ya daralır,
  yarım turda aynalanır; saç çapaları tuval dönüşümüyle birlikte döner) — tam gövde çark, ters tutuşlu pivot, kırbaç
  girdabı artık gerçekten dönüyor.
- **Eğriler:** anahtar başına giriş eğrisi (yumuşak, hızlanarak `i`, yavaşlayarak `o` ...): hazırlık oturarak kurulur,
  süpürme kübik hızlanır, aşma yavaşlayarak durur.
- **Erim dengesi (`PULL`):** vuruş kutuları sabit olduğundan derin öne çöken pozlarda (ağır, dev, çakma, hançer, kırbaç)
  temas / kilit evresinde tüm duruş 1,5-3 birim geri alınır: omuz (dolayısıyla bıçak) v27 temas karesinden en çok
  ~6-8 birim önde.

### Kareler ve zamanlama
Her saldırı gövdesi 10 kare: hazırlık 3 (kalkış, kurulma, derin hazırlık / tutuş), süpürme 1 (gerilmiş ara poz), temas 1,
kilit 2 (aşma, tutma), toparlanma 3 (arka ayak öne kayar, duruş toplanır). Kareler gövdenin kendi zamanında (tau)
eşit aralıklı DEĞİL: json'da her satıra `ts` (karelerin başlangıç anı), `mk` = [W, C, H] (evre sınırları) ve `v28`
yazılır. Oyunda (`Player._show_body` / `_body_frame`) savuruşun k zamanı [0, hit0, ck, hit1, 1] → [0, W, C, H, 1]
parça parça eşlenir; gösterilen kare, başlangıç anı bu zamanı geçmemiş son karedir. Böylece temas karesi TAM isabet
anında (ck) açılır, derin hazırlık karesi tutuşta (hold_k, şarj) bekler ve gövde her savuruşun evre sürelerine gerilir:
`hit`, `ck`, `multi`, `hold_k`, TEMPO evreleri, vuruş kutuları ve ara bellekler DEĞİŞMEDİ. Çok vuruşlu / çark savuruşlarında
(süpürme evresi sıfır) etkin pencerede dönen kareler (`_TURN_SET`), seri saplamada her saplama işaretine (multi) denk
gelen ileri / geri kareler (`_FL_FR`), sıçrayıp çakmada sıçrayış hazırlığın içinde (tutuş karesi çömelme).

### Aile gövde dili ve eşleme
Önce aile + savuruş (`Player.GOVDE_AILE`), sonra savuruş (`GOVDE_SW`), yoksa savuruşun `body`si. v27 yeni silahlarının
savuruşları da (Gün-Ay, Kistin, Albastı, Çevgen) eşlenir.

| Aile | Gövde dili | Savuruş → gövde (kare) |
|---|---|---|
| Kılıç (Alp, Yıldırım, Pala, Ayaz, Ruh, Yılan) | geniş duruş, kalça önden döner; inişte parmak ucunda kurulup adımla çöker; iaido çekişinde derin çömelme, ayak kayarak açılır, zanshin, kalkışta kına koyma duruşu | horiz / back / cross_x / yk_cross → `atk_horiz` (10), down / diag_down / rake → `atk_down` (10), up / diag_up → `atk_up` (10), step_down → `atk_k_step` (10, diz kalkık kurulma + uzun adım), iai / yk_iai / reverse_grip → `atk_iai` (10), lunge / yk_flash → `atk_lunge` (10, koşucu çıkışı), thrust → `atk_thrust` (10, eskrim hamlesi), rise → `atk_uppercut` (10) |
| Düello (Yatağan, Rüzgâr, Gün-Ay@Ay) | kılıçla aynı temel + ters tutuş çekişi iaido, bilek çevriminde pivot | reverse_grip → `atk_iai`, twirl → `atk_h_spin`, backstep → `atk_backstep` (10, öne yüklenip geriye kayarak kesme) |
| Hançer (İkiz Bıçak, Böri, Ay Palası, Kurt Pençesi, Albastı) | alçak akrobatik çömelme, sekerek ileri, çapraz adım, ters tutuşlu pivot (tam tur) | dual_l / down / diag_down / rake → `atk_dual` (10), dual_r → `atk_dual_r` (10, arka ayak öne geçer, arka el ikinci bıçakla fırlar), reverse_grip / twirl → `atk_h_spin` (10, hazırlıkta sırtını döner), flurry / albasti_oyma / thrust → `atk_h_flurry` (10, her saplamada ileri-geri), cross_dash → `atk_lunge` |
| Ağır (Gürz, Çivili Topuz, Savaş Baltası, İkiz Balta, Kistin) | omuz üstü büyük kurulma (ön diz kalkık, gövde geriye burulu), adım + tam gövde çakma, diz bükülü yer çöküşü | heavy / windmill → `atk_heavy` (10), down / diag_down / axe_hook / kistin_tepe / dual_l → `atk_a_chop` (10), uppercut_2h / ground_drag / cevgen_vurus / dual_r → `atk_a_lift` (10, bacaktan yüklenip parmak ucunda kaldırma), slam / slam_2h → `atk_slam_jump` (10, çömel-sıçra-havada kurul-çak), horiz / kistin_yan → `atk_u_sweep`, axe → `atk_throw_axe` (10), step_down → `atk_overhead_2h` |
| Dev (Ulu Kılıç, Dağ / Kor Çekici, Bozgun) | baş üstü iki elle kurulma (diz kalkık, sırt kavisli), adımla derin çömelme çakma | overhead_2h / step_down / gun_tutulma / kistin_cal → `atk_overhead_2h` (10), spin_2h / helicopter → `atk_spin_2h` (10, tam gövde dönüş), uppercut_2h / ground_drag → `atk_a_lift`, diag_down → `atk_a_chop` |
| Mızrak (Kargı, Tulpar) | yerleşik duruş, kayan adım (arka ayak ardından gelir), uzun alçak hamle | thrust / pole_thrust → `atk_m_thrust` (10), lunge_long / stab_heavy / pole_thrust_lo → `atk_lunge_long` (10), pole_rise → `atk_m_rise` (10) |
| Uzun sap (Teber, Erlik Tırpanı, Kayın Asası, Gün-Ay@Gün) | dans gibi: arkadan çapraz adım, at duruşunda geniş süpürme; tırpanda öne uzanıp ağırlığı geri çekerek biçme | pole_sweep / horiz → `atk_u_sweep` (10), reap → `atk_u_reap` (10), sweep_low → `atk_sweep_low` (10, kayarak yarık duruş), spin_2h / gun_cark / gun_birlesme → `atk_spin_2h`, twirl / gun_teker → `atk_spin` (10) |
| Kırbaç (Kement, Od Kamçısı) | sırt kavisli kurulma, kalça şaklaması, yanda ön ayak üstünde yarım dönüş, baş üstü girdapta parmak ucunda dönüş | whip_crack → `atk_whip` (10), whip_side / kistin_dolama / horiz → `atk_w_side` (10), spin → `atk_w_whirl` (10) |

Uzak silahlar: **yay** 4 kare (ok takma, germe, tam gerili — gövde arkaya yaslanır, yan duruş — ve bırakış geri tepmesi;
`Player`: aim_t > 0,3 tam gerili, bow_rel_t sırasında bırakış karesi), **fırlatma** 5 kare (0,28 sn: kurulma, derin
kurulma, adımla bırakış — bırakış anı aynı 0,07 sn —, takip, oturma), **büyü** 4 kare (topla, kaldır, öne sal, otur).

### SanatAnim ile işbirliği
v28 gövdesi (json `v28`) gösterilirken SanatAnim'in dönme ve eğikliği ×0,35, ezilme-esnemesi ×0,5'e iner
(`SanatAnim.V28_K`, `V28_SQ`): hareket artık çizimde, katman yalnızca hafif bir eğilim ve vuruş anı esnekliği ekler
(aynı hareket iki kez uygulanmaz). Bitiriş süslemeleri, leke kareleri, mürekkep vurguları, düzlem farkları aynı.
`-- --sanat_kapali` hâlâ v26 katman görünümünü verir (gövde v28).

### Yıldırım Kılıcı şarjlı hamlesi
Eski: menzil mech_v 110-190 × %60-100 (66-190 px) ve isabet penceresi bitince 1100 px/sn'lik hız (`_atk_owns_motion`
yolunda yalnızca yavaşlayarak) ~200 px daha kayıyordu: `--dovus --yildirim` ölçümünde (mech_v 118) tam şarj **351 px**,
kısa şarj **323 px** gidiyor, ilk düşmanın 305 px ötesinde duruyordu. Yeni (`Player.YK_DASH`): mech_v aralığı 65-85
(items.json; eski kayıttaki büyük değerler 85'e kırpılır) × %85-100 = **55-85 px**; ilk isabette durma noktası konur,
gövde ilk düşmanın en çok **30 px** ötesinde 70 px/sn'ye iner (pencerenin kalanında yerinde: hemen arkadaki ikinci düşman
yine delinir) ve hamle bitince kayma yok. Ölçüm (mech_v 84): tam şarj **75 px** (ilk düşmanın 30 px ötesi), kısa şarj
**48 px**; tam şarjda yıldırım yine deldiği iki düşmanın tepesine iniyor (düşmana 2 px). Dokunulmazlık (0,3 sn), delme,
kritik (iki düşman delme) ve v21 yıldırımı aynı. Şimşek Çekişi bitirişi (84 px, 0,075 sn) zaten kısa ve düşmanın içinden
geçecek biçimde tasarlandı: değişmedi.

### Varlıklar
`python export_ink.py --bengu` (+ `KY_HD=2 ...` ve `python hd_paket.py --paketle`): `bengu_v2` artık 45 satır / 4 sayfa
(3840 px genişlik: en çok 10 kare; HD 7680), 17 saldırı satırı yeniden çizildi (8 → 10 kare), 13 aile çeşidi eklendi,
yay / fırlatma / büyü yeniden çizildi (3 → 4, 3 → 5, 2 → 4 kare). Her yeni karede saç çapaları (`sac`, `sac_d`,
`neck`, `hip`) ve kol çapaları (`sh_f`, `sh_b`, `arm_b`) yazılır (dönüş karelerinde dönüşmüş hâlleri). Kare dökümü
paralel (süreç havuzu; temel ~1,5 dk). Kol parçaları (`bengu_kol_v2`) değişmedi. HD manifest md5'leri güncel.
Önizleme (geliştirme): `python govde_onizleme.py <çıktı.png> <anim>:<savuruş>[:<erim>] ... [--eski] [--sutun=5]`
(ön kol savuruşun o anki pozunda; `--eski` v27 gövdesi).

### Ölçüm ve test
Aynı yapıda, 60 Hz, betik hatası 0 (SCRIPT ERROR yok):
* `--dovus --boss --hiz`: 41 silahın basış→temas ve zincir aralıkları (%0 / %20 / %40 sütunları) v27 ile BİREBİR aynı
  (İkiz Bıçak 167 / [267, 217, 383], Alp 183 / [400, 433, 483], Gürz 317 / [517, 650, 550], Ulu Kılıç 400 /
  [617, 1050, 617]); en az kare ihlali 0. Gövde seçimi yalnızca görsel: zaman bükmesi, evreler, isabet anları dokunulmadı.
* `--dovus --boss`: TAKILMA=0; OZET vuruş (basış→temas) ±1 kare içinde (İkiz Bıçak 133 → 116, Yatağan 133 → 150,
  Alp 150 → 150, Kargı 133 → 133, Ulu 350 → 350, Dağ Çekici 366 → 366 ms; v27'de de art arda koşularda 1 kare oynuyordu).
* `--dovus --boss --kontrol`: KONTROL basış=272 savuruş=136 basılmamış=0, oto_dönüş=0, oto_hamle=0, istenmeyen_ağır=0;
  TAKILMA=0.
* `--dovus --boss --yildirim`: yukarıdaki menzil ölçümü; tam şarjda 2 şimşek düşmanların tepesinde.
* `--silah27 --boss` SONUC GECTI HATA=0; `--bengu --boss` OZET hata=0 (yeni karelerin saç çapalarıyla: zincir sağlığı,
  durgun / koşu / dönüş / hayalet / darbe karesi denetimleri).
* `--sanat --boss --muhur=0` SONUC GECTI hata=0, TAKILMA=0; `--yay --boss` TAKILMA=0, CEPHANE_HATA=0 (yay 4 kare:
  germe / tam gerili / bırakış seçimi); `--tomar --boss` SONUC GECTI; `--otomatik --derinlik=1 --muhur=0` (derinlik 2'ye
  dek ~15 600 kare, ölüm 0) ve `--mekanik --muhur=0` (BITTI): betik hatası 0; `--piksel_tara` TOPLAM 0 (690 tarama).
* 2560x1440 `--doku=2` (`--bengu=<klasör> --boss --pencere=2560x1440 --doku=2`): HD sayfalar md5 eşleşmesiyle yükleniyor,
  OZET hata=0; `docs/v28/hd_saldiri_yay_donus.jpg`.

Kare şeritleri / kontak sayfaları (`--firca_kombo --firca_tam --firca_bos`, 60 Hz, her kare çekilir; önce = v27 gövde
satırları aynı kodla, sonra = v28): `docs/v28/aile_<aile>.jpg` — üst satır v27, alt satır v28, aynı savuruşun hazırlık
başı / ortası / sonu, süpürme, kilit, toparlanma kareleri: `aile_kilic` (Alp step_down), `aile_duello` (Yatağan),
`aile_hancer` + `aile_hancer_capraz` (İkiz Bıçak dual_r / cross_dash), `aile_agir` (Gürz heavy), `aile_dev` +
`aile_dev_cark` (Dağ Çekici, Ulu Kılıç spin_2h), `aile_mizrak` (Kargı alçak saplama), `aile_uzun` (Teber),
`aile_tirpan` (Erlik Tırpanı biçme), `aile_kirbac` (Kement yan şaklama), `aile_uzak` (yay / cirit / Gök Asası).
Bütün gövdelerin önizleme sayfaları (ön kol savuruş pozunda): `govde_tum1.jpg` (kılıç / düello temel), `govde_tum2.jpg`
(ağır / dev / mızrak), `govde_tum3.jpg` (uzun sap / hançer / kırbaç / uzak). 2560x1440 `--doku=2` (HD x2) çekimleri:
`hd_*.jpg`.

### Bilinen
* Gövde hâlâ yan görünüşten çizilmiş tek bir karakter: dönüş karelerinde (çark, pivot) 3/4 görünüş yok; yan görünüşün
  daralması + aynalanmasıyla taklit edilir (en dar 0,6). Hızda iyi okunur, tek tek karede dar görünür.
* Ön kol ve silah hâlâ savuruş anahtarlarıyla (SWINGS) sürülüyor (vuruş kutuları / zamanlar sabit kalsın diye kol
  anahtarlarına dokunulmadı); gövde artık daha çok öne çöktüğü için bıçak temas karesinde v27'den en çok ~6-8 birim önde
  (PULL ile sınırlı). Vuruş kutusunun +10 birim payı içinde.
* Saldırı başlarken ilk kare dinlenme duruşu; zincirde bir önceki savuruşun toparlanmasından gelen kare ile arasında
  küçük bir sıçrama olabilir (gövde kareleri arası karışım yok, v27'de de böyleydi).
* Savaş Sanatları (`SavasSanati.gd`, ayrı çalışma) gövde satırlarını eski eşit aralıklı yolla seçiyor; satır adları aynı
  olduğundan çalışıyor, ama evre eşlemesinden yararlanmıyor.
* `InkAksanFX.gd:239` "p_points.size() < 2" ve `SanatUI.gd:31` üçgenleme hataları v28 öncesinden (bu değişiklikle ilgisiz).

## v29: uçan ve büyücü yaratıkların animasyonu

Geri bildirim: "Bütün düşmanlar için yap — saldırırken yalnızca kol oynuyor. Gerçekten canlı bir canavarla karşı
karşıyaymışım gibi hissettirmeli. Çok profesyonel olsun."

Bu bölüm Çor ailesini (Çor Ruhu, Kurgan Ruhu, Kan Çoru, Ayaz Çoru, Kayıp Ruh, Demir Gaga), Su / Od İyesi'ni,
Tozkoparan'ı ve Işıltı Kamı'nı kapsar (yer yaratıkları ve bosslar ayrı çalışmalar). Eski satırlar tek bir gövde
çiziminin üstünde yalnızca kolu / feneri oynatıyordu: Çor ailesi idle 6, attack 3, hurt 1 (saldırı = kol öne + fener
savrulur), iyeler windup 2 / slam 2 (yalnızca kol kalkar / iner), Işıltı Kamı cast 3. Yapay zekâ zamanları, vuruş
kutuları, çarpışma boyları DEĞİŞMEDİ; değişen yalnızca çizim ve sprite json'u.

### Animasyon takımı (`tools/artgen/ucan_v29.py`)
* **Anahtar pozlar + giriş eğrisi** (`pose_at`): her satır zaman içinde anahtarlarla yazılır; hazırlık oturarak kurulur
  (`o`), vuruş kübik hızlanır (`i`), aşma yavaşlayarak durur, döngülerde son anahtar ilkine akar. Eksik alanlar önceki
  anahtardan taşınır (ortak dinlenme pozu `REST`).
* **Tam gövde dönüşümü** (`body_xf`): bütün çizim bir pivot çevresinde döner, kayar, yerel eksen boyunca ezilip uzar
  (squash / stretch) ve eğilir; `fix_ellipse` elipsleri de dönüşümle gerçekten ezer (inkkit yalnızca açıyı izliyordu).
  Çapalar (`mouth`, `hand`) dönüşümden geçirilip yazılır (`to_world`): mermi yine fenerden / elden çıkar.
* **İkincil hareket / gecikme:** kefen kuyrukları, etek, başlık ucu, omuz örtüsü, dilek çaputları, iye saçakları ve
  dalları gövdeden faz farkıyla gecikir; buhurdan zinciri dünya yerçekimine göre sarkar (gövde dönüşünden arındırılır),
  dumanı dünyada yukarı tüter.
* **Kanat** (yan görünüş; başvuru: Animation Mentor kuş uçuşu blok kuralları — önce uç pozlar, sonra dirsek / bilek
  bükümü, dar yukarı / geniş aşağı vuruş, tüylerin gecikmesi —, Muybridge kuş / yarasa dizileri, doğan pikesi
  çalışmaları): `feather_wing` (kemik + örtü tüyleri + taraklı ikincil tüyler + tek tek birincil "parmak" tüyler),
  `bat_wing` (kol + dört parmak + içe kavisli zar). `flap(t)`: aşağı vuruşta kanat tam açık ve geniş, tüyler yukarı
  gecikir, gövde yükselir; yukarı vuruşta bilekten katlanır, uç tüyler ayrılır, gövde iner; orta vuruşta kanat
  izleyiciye bakar (kısa ve geniş görünür). Uzak kanat koyu tonda, küçük ve hafif faz farklı.
* **Efektler:** hız çizgileri (kuru fırça), mürekkep / kül zerreleri, **çözülme** (`dissolve`: ölümde gövde mürekkep
  lekelerine ayrılır, kenar şeridi ışıma sayfasına kor / su / kristal rengi yazılır; doğuşta tersine toplanır;
  dağılan alan oranı sıra eşitlemeli = doğrusal); çözülen karelerde efektler (ışınlanma sütunu, zerreler) ayrı tuvalde
  çizilip üste konur (çözülmeden etkilenmez).
* **"!" ve "!!" ayrımı:** her yaratığın `tele` (kızıl "!" — kurulma) ve `tele_zirh` satırı ("!!": daha geniş siluet,
  kollar / kanatlar tam açık, turuncu kor halesi + dışa sivrilen kor çizgiler `armor_aura`, ışıma sayfasında).

### Satırlar (kare sayıları; `python tools/artgen/export_ucan.py`)

| Yaratık (çizim) | Satırlar | Öne çıkanlar |
|---|---|---|
| Çor Ruhu `cor` (flyer_ranged; `cor_ink.py`) | idle 8, move 8, tele 4, tele_zirh 4, attack 8 (ts/mk), dive 6 (ts/mk), hop 5, hurt 3, stagger 6, death 9, spawn 7 | kanatsız süzülen kefen; saldırıda buhurdanı baş üstüne kaldırıp bütün gövdeyle öne fırlatır, spor bulutu genişler; pikede kefen akış biçimini alır, kuyruklar yukarı akar; ölümde başlık çöker, kefen yeşil korla çözülür |
| Kurgan Ruhu `kara_kus_yavrusu`, Ayaz Çoru `kaf_kartali`, Demir Gaga `demir_gaga` (diver) | idle 8, move 6, tele 4, tele_zirh 4, attack 10 (pike, ts/mk), stuck 4, hop 5, hurt 3, stagger 6, death 9, spawn 7 | sırtta kara kuş / ak kartal / demir bıçak tüylü kanatlar; kerkenez gibi çırparak asılı durur; pike: kanatlar yukarıda açık hazırlık → kanatları katlayıp damla biçimli dalış → pençeler öne + fren → çarpma (ezilme, kanatlar açılır) → saplanmış çırpınma → güçlü aşağı vuruşla sıyrılış; Demir Gaga'da gaga açılır |
| Kan Çoru `kan_yarasasi` (swarm) | idle 8 (14 fps, düzensiz çırpınma), move 6, tele 4, tele_zirh 4, attack 9 (süzülüş, ts/mk), hop 5, hurt 3, stagger 6, death 9, spawn 7 | zar kanat (yakın kanat kefenin önünde); geri çekilip kanat açar, ağız açık; süzülüşte kanatlar geriye yarı katlı, gövde çapraz uzar, pençeler önde; kanatları öne açarak frenler |
| Kayıp Ruh `kayip_ruh` (swarm) | idle 8, move 6, tele 4, tele_zirh 4, attack 9 (ts/mk), hop 5, hurt 3, stagger 6, death 9, spawn 7 | kanatsız, gövdeden S dalgası geçer, üç uzun saydamlaşan duman kuyruğu, soluk hale; süzülüşte gövde ruh izine dönüşür (eksen boyunca ×1,4 uzar), maske çığlık atar |
| Su İyesi `su_iyesi`, Od İyesi `od_iyesi` (caster; `iye_v29_ink.py`) | idle 6, walk 8, windup 6, slam 5, attack 8 (ts/mk), tele_zirh 5, blink_out 4, blink_in 4, hurt 3, stagger 4, death 7, spawn 6 | kanallama: çöker, iki kolu öne-yukarı süpürür, öğe kolları sarar, iki elin arasında su küresi / alev topu büyür, baş kükrer; salınış: bütün gövde öne yüklenir, su taçlı sıçrama / alev püskürmesi; ışınlanma: su sütunu / alev yutmasıyla çözülür, öbür yanda toplanır; ölümde su birikintisine / küle dağılır |
| Tozkoparan `tozkoparan` (tornado; `iye_v29_ink.py`) | idle 6, walk 8, windup 6, slam 5 (yel itişi), attack 8 (ts/mk), tele_zirh 5, spin 8 (20 fps), dizzy 8, hurt 3, stagger 4, death 7, spawn 6 | bacaklar kök saçağı olarak sarkar, **toz hortumu üstünde süzülür**; hazırlıkta gövde geriye burulur, kollar göğse sarılır, hortum kabarır; yel itişinde açılarak kolları savurur; `spin`: gövde tam tur döner (yan görünüş daralıp yarım turda aynalanır), hortum gövdeyi sarar; `dizzy`: daire çizerek sallanır, baş sarkar, hortum tekler |
| Işıltı Kamı `isilti_bocegi` (kamikaze; `isilti_v29_ink.py`) | idle 6, run 8, cast 8 (fitil), explode 6, attack 10 (ts/mk), hurt 3, stagger 4, death 7, spawn 6 | "ışıltı böceği": sırtta kristal kın kanatlar, koşarken açılır ve vızıldar; fitilde kasılır, kristal taç büyür, kaftanın dikişlerinden ışık çatlakları ve omuzdan kristaller fışkırır, beden şişer, içten akkor ve huzmeler; patlamada kristal kıymıklar + ışık halkası |

Çizimler ötekilerin dosyalarına dokunmadan **çatallandı**: Kara İye çizimi `iye_v29_ink.py`'ye, Kara Kam çizimi
`isilti_v29_ink.py`'ye kopyalandı (Kara İye / Dev Çocuğu / Kara Kam / Kurgan Kamı / Erlik'in Kızı dışa aktarımları
değişmez); `export_yaratik_a.py` bu on kimliği atlar ve `export_ucan.py`'yi gösterir. Çor ailesinin hücresi 80x76'dan
96x88 dünya birimine (kanat çırpışı ve pike sığsın), Işıltı Kamı'nınki 76x72'den 88x80'e büyüdü (ayak orijini json'da);
iyeler 128x112 kaldı (satır başına en çok 8 kare = 4096 px; iki sayfa).

### Zamanlama ve json sözleşmesi (genel oynatım için)
* Saldırı satırlarında Bengü v28 sözleşmesi: `ts` (karelerin başlangıç anı, 0..1), `mk` = [W, C, H] (hazırlık sonu,
  temas, etkin evre sonu; 0 ve 1 örtük: evreler [0, W, C, H, 1]) ve `"v29": true`. Örn. dalıcı pikesi
  ts = [0, .25, .32, .40, .45, .52, .64, .78, .86, .93], mk = [.25, .45, .78]: hazırlık 1 kare, dalış 3 kare, çarpma
  karesi tam C'de, saplanma 2 kare, sıyrılış / yükseliş 3 kare.
* **Bugünkü Enemy.gd ile uyum:** uçanlarda `attack` satırının 0. karesi hazırlık anahtarı ("!" pozu), 1. karesi vuruş
  anahtarıdır (W = ts[1]); Enemy bugün `show_frame("attack", 0/1)` ile seçtiğinden hazırlıkta kurulmuş poz, dalış /
  süzülüş / spor atışında vuruş pozu görünür. Kaçış satırının adı `hop` (`Enemy._tick_evade` `_pa(["leap","hop",...])`
  onu seçer; `leap` adı oyuncunun Ruh Kuşu'nun — `SpiritWolf`, cor sayfası — saldırı satırı olduğundan kullanılmadı).
  İyelerde `walk` / `windup` / `slam`, kamikazede `run` / `cast` aynı adlarla oynatılır; fps'ler durum sürelerine göre
  ayarlandı (kanallama 6 kare / 12 fps ≈ 0,5 sn, fitil 8 kare / 13 fps ≈ 0,6 sn, son kare tutulur). Tozkoparan'ın
  kasırgası bugün `walk`'ı ×2,6 hızla oynattığından `walk` süzülüş + burulma olarak çizildi (hızlı oynayınca dönen
  hortum gibi okunur).
* Sayfa düzeyinde `"durum"`: Enemy durumu → satır önerisi (ör. dalıcı {windup: tele, windup_zirh: tele_zirh,
  dive: attack, stuck: stuck, evade: hop, death: death, spawn: spawn}). Bugünkü kod okumaz; genel, veri güdümlü
  oynatım (ayrı çalışma: Enemy.gd / SpriteAnim.gd) birleştiğinde tele / tele_zirh / death / spawn / stuck / spin /
  dizzy / blink / explode satırları kullanılabilir.
* Işıma sayfaları yarım çözünürlük (`"glow_scale": 2`, SpriteAnim zaten destekliyor): ışıma bulanık, görüntü aynı,
  depo boyu ~1/4.

### Sayfa çözümü
Oyunda `Enemy._ready` v2'de düşmanın KENDİ kimliğiyle bir `_v2` json'u varsa onu yükler (`own_v2`), yoksa
`def.sprite`'ınkini; bu on kimliğin hepsinin kendi `_v2` sayfası olduğundan (kan_yarasasi_v2, tozkoparan_v2, ...)
oyun kendi çizimlerini kullanıyordu ve kullanıyor. `world.json` "sprite" alanı DEĞİŞTİRİLMEDİ: o alan yalnızca
çizim değil, `sprite_kind` üzerinden çarpışma boyunu (`cor` 22x34 uçan, `agac_iyesi` 34x74 ağır, `arcura` 18x30),
uçma bayrağını, kan rengini ve yapay zekâ yedeğini belirliyor; değiştirmek vuruş kutularını değiştirirdi.

### Varlıklar
`cd tools/artgen && python export_ucan.py [kimlik ...]` (sayfa başına ~1-3 dk, süreç havuzu), ardından
`KY_HD=2 python export_ucan.py` ve `python hd_paket.py --paketle` (HD x2 WebP + manifest md5). Önizleme (geliştirme):
`python ucan_onizleme.py <çıktı.png> <modül> <kimlik> [satır ...] [--olcek=0.5] [--glow]` (kırmızı çerçeve = hücre
kenarına taşan kare). Boyut: 10 kimlik × 58-74 kare (toplam 652 kare; v28: 119); temel PNG + yarım ışıma
+ HD WebP birlikte depoda **+53,6 MB** (12,0 → 65,5 MB). Çor ailesi sayfası 3456-3840 × 3872 px, iyeler 4096 × 5376 (iki
sayfa), HD x2 en çok 8192 px.

### Test
Aynı yapıda (`--import` sonrası), başsız, betik hatası (SCRIPT ERROR) 0 — hepsinde:
* `--stil=v2 --yaratik=<on kimlik> --yaratik_sure=7` (canlı yapay zekâ, oyuncu iki kez vurur): 21 olay, hata 0; aynı
  sahne pencerede `--write-movie` ile çekildi (aşağıda `oyun_*.jpg`).
* `--zeka --muhur=0`: bütün türler ölçüldü; bu türlerin satırları (ilk hamle, hamle / 10 sn, hasar) yapay zekâ zamanları
  değişmediği için v28 ile aynı düzeyde (ör. cor 0,52 sn / 5,5, kan_yarasasi 0,52 / 5,5, tozkoparan 0,52 / 3,5,
  isilti_bocegi 1,07 / 3,0). Not: Çor ailesinde spor mermisi `mouth` çapasından (artık bütün gövdeyle savrulan
  buhurdanın gerçek konumu) çıkar; vuruş karesinde ~11 birim aşağıda (v28: kolun ucunda).
* `--dovus --boss --kontrol`: KONTROL basış=272 savuruş=134 basılmamış=0, oto_dönüş=0, oto_hamle=0, istenmeyen_ağır=0;
  TAKILMA=0.
* `--harita`: SONUC GECTI (geçersiz düşman yerleşimi 0 / 1014).
* `--otomatik --derinlik=1 / 4 / 7 --muhur=0` (30 000 kare): betik hatası 0, ölüm 0 / 0 / 1.
* `--mekanik --muhur=0`: BITTI. `--piksel_tara`: TOPLAM 0 (119 tarama).
* Görülen `ERROR` satırları v28 öncesinden: `InkAksanFX.gd:239` "p_points.size() < 2" ve `SanatUI` üçgenleme.
* `python hd_paket.py --paketle`: 13 yeni HD doku TAMAM (2x2 küçültülmüş HD ↔ temel ort. fark ≤ 0,0011), manifest md5
  güncel.

Görseller (`docs/v29/ucan/`): `<kimlik>_once_sonra.jpg` — üstte v28 satırları, altta v29 satırları (ad, kare, fps,
ts, mk); `oyun_<kimlik>.jpg` — canlı yapay zekâlı oyun çekimi (1280x720 film karelerinden kırpım, 8 an:
yaklaşma, hazırlık, saldırı, yaralanma).

### Bilinen
* Yeni satırların çoğu (tele, tele_zirh, death, spawn, stuck, spin, dizzy, blink_out / blink_in, explode, dive, move)
  genel oynatım birleşene dek oyunda görünmez; bugün görünen: uçanlarda idle (hem bekleme hem kovalama), attack 0 / 1
  anahtarları, hurt, hop (kaçış); iyelerde idle / walk / windup / slam / hurt; kamikazede idle / run / cast / hurt.
  Ölümde oyun hâlâ o anki kareyi ceset olarak savurur (`FX.corpse`).
* Dalıcı saplanmışken (0,7 sn) bugünkü kod `attack` 1. karesini (pike pozu) gösterir: gövde yerin biraz üstünde dalış
  pozunda kalır; `stuck` satırı genel oynatımla gelir.
* Kanat yan görünüşte iki boyutlu bir yaklaşımdır (gerçek 3B dönüş yok): orta vuruşta kanat kısalarak "izleyiciye
  bakar"; tek tek karede bazı pozlar düz görünebilir, hızda okunur. Kan Çoru'nun aşağı vuruştaki zar kanadı kefenin
  kızılıyla yakın tonda kalıyor.
* Ölüm / doğuş çözülmesi görüntü sonrası işlemdir (gürültü + sıra eşitleme): parçalar fiziksel olarak savrulmaz,
  yerinde mürekkep / kor lekelerine dağılır.
* Işıltı Kamı küçük (çarpışma 18x30): kın kanatlar ve fitil çatlakları 1080p'de ince ayrıntı olarak kalır; okunan
  asıl işaret ışıma ve şişme (kod ayrıca ×1,35 büyütüyor).
* Bu yaratıkların ses / FX çağrıları değişmedi (yalnızca çizim).

## v29: Bengü poz cilası

Geri bildirim: "v28 gövde farkı gerçek ama orta düzeyde; vuruş / kilit kareleri hâlâ v27 gibi görünüyor. Poz aracını
kullanıp yap — çok profesyonel hissettirsin."

Hedef: Shinobi: Art of Vengeance / Hollow Knight / Dead Cells / Blasphemous düzeyinde okunur, abartılı anahtar pozlar.
Başvurulan ilkeler: animasyonun 12 ilkesi (hazırlık, ezilme-esneme, takip ve örtüşen hareket, yay, abartı, sağlam çizim),
dövüş oyunu evreleri (hazırlık / etkin / toparlanma: yalnız etkin kareler vurur), piksel / sprite saldırı dökümleri
(Raymond Schlitter, *Pixelblog 9 — Melee Attacks*: tek ya da az sayıda hızlı leke karesi, vuruş / takip pozunu kısa
tutmak ağırlık verir, durmadan önce hafif aşma; "baş dik, sırt düz" — gövde yatay kırılmaz), eskrim / HEMA hamlesi
(arka bacak düz, ön diz ayak bileği üstünde, gövde hedefe uzanır) ve iaido çekişi (alçak, kayan ön ayak, zanshin).

### Poz aracı eklentileri (`tools/artgen/bengu_govde.py`, `bengu_ink.draw_turn`)
- **Tuval bükmesi (`warp_fn`):** tüm çizime (gövde, post, etek, baş, kuşak) uygulanan, yer çizgisini sabit tutan bükme;
  yere basan ayak kaymaz. Alanlar: `shr` doğrusal eğme (yükseklikle orantılı), `crv` eğrilik (yüksekliğin karesiyle:
  **C eğrisi**; `shr < 0` ile **S eğrisi**), `stx` / `sty` esneme-ezilme (kalça altındaki yer noktası çevresinde).
  Eylem çizgisi: hazırlıkta gövde geriye C (yay gibi kurulma), vuruşta hedefe C (baş önde), yükselen kesikte dikey
  geriye kavis. Ön kol / el / baş / omuz çapaları aynı bükmeyle dönüştürülür (oyundaki kol omuza oturur); saç
  çapaları (`sac`, `sac_d`, `neck`, `hip`) tuval yığınıyla (`_xf`) zaten dönüşür.
- **3/4 dönüş:** dönüş karelerinde en dar genişlik 0,6 → **0,72** ve yüksekliğe bağlı daralma: bacak / kalça tam daralır,
  gövde ve baş en az 0,88 kalır (göğüs önden geniş, kalça önden döner, omuzlar bir adım geriden gelir). v28'deki ince
  şerit görünümü gitti.
- **v29 abartı katmanı (`v29()`):** v28 anahtarları (ayak işi, evre işaretleri) korunur; her anahtar EVRESİNE göre
  dinlenme duruşundan uzaklaştırılır (`GAIN`: hazırlık ×1,6, leke ×1,45, temas ×1,6, kilit ×1,5, tutma ×1,25 —
  kalça yeri / yüksekliği, gövde eğimi, omuz burulması / kayması, post, etek, kuşak; ayak yerleri tek katsayıyla ×1,22,
  anahtarlar arasında basan ayak kaymasın), önden giden baş (`hdx` daha çok, başı eğme `hdy` abartılmaz: baş hedefe
  bakar). Sınırlar: öne kesikte gövde eğimi ≤ 0,72, çakmada ≤ 0,8 (yatay "yere yatma" yok), kalça temas / kilitte
  ≥ 15 birim, hazırlıkta geriye eğim ≥ −0,5.
  - **Hazırlık:** öne kesiklerde ağırlık arka bacakta, ön ayak hafif kalkık (adıma hazır), gövde geriye C eğrisi; öne
    çömelerek kurulan aileler (hançer, hücum, iaido) ezilme (`sty` 0,93); çakmalarda daha derin geriye kavis.
  - **Süpürme = leke karesi:** öne kesikte yatay esneme (`stx` 1,1, `sty` 0,95, öne eğme), yükselen kesikte dikey
    esneme (`sty` 1,09), geri çekerek kesikte geriye eğme.
  - **Temas / kilit:** öne kesik ve çakmalarda **arka bacak düz** (arka ayak kalçadan erime yakın uzaklığa itilir, topuk
    kalkık), daha derin ve geniş hamle, gövde kesiğe burulu, hedefe C eğrisi; yükselen kesiklerde parmak ucunda tam
    gerilme (kalça +3, arka topuk kalkık, sırt geriye kavisli, baş yukarı).
  - **Toparlanma sonu = dinlenme duruşu:** son anahtar `REST` (v28'de yarım adım öndeydi: saldırıdan durguna geçişte
    ayaklar sıçrıyordu). Durgun animasyonu da aynı ayak yerlerinde.
  - **Erim (vuruş kutusu payı):** abartılmış pozun ön omzu, aynı anahtarın v28 omzundan en çok **2,5 birim öne / 3 birim
    aşağı** kayabilir; fazlası tüm duruşu geri kaydırır, kalçayı kaldırır (arka bacak yeniden düzlenir). Ölçüm: temas,
    kilit ve tutma karelerinde v29 − v28 omuz farkı x ≤ +2,5, y ≤ +3,0 (yay, fırlatma, büyü elle; büyü bırakışı +4,5 → elle
    geri alındı). Bıçak savuruş anahtarlarıyla sürüldüğünden temas karesinde v28'e göre en çok bu kadar oynar
    (± 10 birim payın içinde).
- **Uzak silahlar (elle):** yay tam gerilide daha geniş taban + göğüs açık (`br`), bırakışta geriye tepme (ön ayak kalkar,
  baş geri, post öne); fırlatmada derin geriye burulma (C) ve bırakışta esneyen tam gövde uzanması; büyüde parmak
  ucunda toplanma ve öne salınım.

### Hareket gövdeleri (v29: ayak hedefli IK; kare sayısı / fps aynı)
| Animasyon | v29 |
|---|---|
| Durgun (8) | Ayaklar dinlenme yerinde sabit (saldırı 0. karesi ve toparlanma sonuyla birebir); nefes: göğüs (`br`) ve omuz kalkar, kalça hafif iner; ağırlık öne-arkaya kayar (kalça ±0,55, arka topuk açısı), baş / kulak / etek / kuşak / post gecikmeli (örtüşen hareket). |
| Koşu (8) | Gerçek koşu döngüsü: temas (topuk, ön ayak önde) → iniş (en alçak) → geçiş (salınan bacakta topuk kalçaya, diz önde) → itiş (arka ayak parmak ucunda gerilir) → uçuş (en yüksek); kollar bacaklara karşıt pompalar, omuz burulur, post savrulur, eylem çizgisi öne C. |
| Depar (8) | Daha uzun adım ve uçuş, gövde 0,64 öne yatık, kollar geride (ninja koşusu), hafif öne eğme. |
| Sıçrama (3) | Kalkış gerilmesi (arka bacak sivri uzanır, `sty` 1,08) → yükseliş → tepede dizler göğse toplanır. |
| Düşüş (3) | Tepeden açılma → kollar dengede, post / etek yukarı savrulur → bacaklar yere uzanır (gerilme). |
| İniş (2) | Tam ezilme (kalça 13, `stx` 1,1 / `sty` 0,9, post öne düşer) → toparlanma. |
| Darbe (3) | Kırbaç: gövde geriye fırlar, baş geriden gelir (geriye C), kollar öne savrulur, ağız açık; aşırı telafi (baş öne); toparlanma. |
| Çömelme (2) | Ninja çömelmesi: ön ayak düz basar, arka diz yere yakın (parmak ucunda), gövde öne yatık, baş hedefe bakar, nefes. |
| Yuvarlanma (8) | Değişmedi (v20 top + dönme). |

### Zincir başı sıçraması (`Player._show_body`)
Zincirde (`atk["chain"]`, önceki savuruşun toparlanmasından) gövde satırının 0. karesi (dik dinlenme) atlanır, doğrudan
kalkış / kurulma karesi gösterilir: öne yatık toparlanmadan dik duruşa sıçrayıp yeniden kurulma yok. Yalnızca görsel
(kare seçimi); zamanlar, evreler, vuruş kutuları aynı. Toparlanma → durgun geçişi yukarıdaki `REST` eşlemesiyle çözüldü.

### Varlıklar
`python export_ink.py --bengu` + `KY_HD=2 python export_ink.py --bengu` + `python hd_paket.py --paketle`: `bengu_v2`
(45 satır / 4 sayfa, satır düzeni ve kare sayıları aynı), HD x2 WebP sayfaları ve manifest md5'leri güncel (4 sayfa
TAMAM). Kol parçaları (`bengu_kol_v2`) değişmedi. Her karede saç ve kol çapaları yazılır.
Önizleme: `python govde_onizleme.py ...` (v28 ile aynı kullanım; bükme ve 3/4 dönüş dahil). `V29_OFF = True` v28 pozlarını
verir (karşılaştırma).

### Ölçüm ve test
Aynı yapıda, betik hatası 0 (SCRIPT ERROR yok); kalan ERROR satırları v28'de de olan `InkAksanFX.gd:239`
"p_points.size() < 2", `SanatUI` üçgenleme ve çıkış sızıntısı satırları:
* `--dovus --boss --hiz`: 31 silahın basış→temas ve zincir aralıkları (%0 / %20 / %40) v28 ile aynı (İkiz Bıçak
  167 / [267, 217, 383], Alp 183 / [400, 433, 483], Gürz 317 / [517, 650, 550], Ulu Kılıç 400 / [617, 1050, 617]);
  yalnızca Ay Palası %0 zincirinin ikinci aralığı koşudan koşuya 1 kare oynuyor (HEAD `Player.gd` ile aynı yapıda
  yeniden ölçüldü: 283, v29: 267 — v28'de de böyleydi). Kızışma sütunları rastgele eşya özelliğine bağlı.
* `--dovus --boss`: TAKILMA=0, KONTROL basış=272 basılmamış=0 oto_dönüş=0 oto_hamle=0 istenmeyen_ağır=0;
  `--dovus --boss --kontrol`: aynı, TAKILMA=0.
* `--bengu --boss` OZET hata=0 (saç çapaları, zincir sağlığı, durgun / koşu / dönüş denetimleri); `--silah27 --boss`
  SONUC GECTI HATA=0; `--sanat --boss --muhur=0` SONUC GECTI hata=0, TAKILMA=0; `--yay --boss` TAKILMA=0,
  CEPHANE_HATA=0; `--tomar --boss` SONUC GECTI; `--mekanik --muhur=0` BITTI; `--piksel_tara` TOPLAM 0.
* 2560x1440 `--doku=2` (`--bengu=<klasör> --boss --pencere=2560x1440 --doku=2`): OZET hata=0.

Görseller (`docs/v29/`; önce = v28, sonra = v29):
* `aile_<aile>.jpg` — oyun içi kare şeritleri (`--firca_kombo --firca_tam --firca_bos`, 60 Hz, her kare çekilir), üst
  satır v28, alt satır v29: aynı savuruşun hazırlık başı / ortası / sonu, vuruş, kilit, toparlanma: `aile_kilic` (Alp
  adımlı iniş), `aile_duello` (Yatağan), `aile_hancer` / `aile_hancer_capraz` (İkiz Bıçak), `aile_agir` (Gürz),
  `aile_dev` / `aile_dev_cark` (Dağ Çekici, Ulu Kılıç), `aile_mizrak` (Kargı), `aile_uzun` (Teber), `aile_tirpan`
  (Erlik Tırpanı), `aile_kirbac` (Kement), `aile_uzak` (yay / cirit / Gök Asası, `--firca_uzak`).
* `poz_temas1.jpg`, `poz_temas2.jpg` — derin hazırlık, leke, temas, kilit kareleri yakın plan (üst dört satır v28, alt
  dört satır v29; pembe halka = saç çapası).
* `govde_tum1-3.jpg` — bütün v29 saldırı gövdeleri (ön kol savuruş pozunda); `hareket_once_sonra.jpg` — durgun, koşu,
  depar, sıçrama, düşüş, iniş, darbe, çömelme (üst v28, alt v29); `hd_hareket.jpg` — 2560x1440 `--doku=2` oyun içi
  (üst v28, alt v29).

### Bilinen
* Ön kol ve silah hâlâ savuruş anahtarlarıyla sürülüyor (vuruş kutuları sabit): gövde çok daha abartılı, ama omuz erim
  sınırı nedeniyle bıçağın yeri v28'den en çok 2,5 birim oynar; en büyük fark gövde, bacaklar, baş ve postta.
* Gerçek 3/4 / önden görünüş çizimi yok: dönüş, yüksekliğe bağlı daralma + aynalama taklidi (en dar 0,72).
* Tuval bükmesi elips / kapsül parçalarının yalnızca merkezini taşır (küçük bükmelerde görünmez).
* Yuvarlanma yeniden çizilmedi; zincir başı atlaması yalnız 10 kareli saldırı gövdelerinde.
* Kenara tutunup çıkma (`mantle`) iniş karelerini kullanır: ilk karesi artık derin ezilme.

## v29: yer yaratıklarının tam gövde animasyonu

Geri bildirim: "Bütün düşmanlar için de yap — düşmanlar saldırınca yalnızca kolları oynuyor. Gerçekten gerçek bir canavarla
karşı karşıyaymışım gibi hissettirsin. Çok profesyonel olsun."

Eski yer yaratığı sayfaları 11-23 kareydi (ör. tazı: idle 6, run 6, windup 2, leap 2, hurt 2; Kara İye: windup 2, slam 2,
hurt 1); çizimler FK açılarıyla kurulmuştu, saldırıda yalnızca kol / bacak açıları değişiyordu, ölüm yoktu (ceset son
kareyi döndürerek savruluyordu) ve kareler yapay zekânın evrelerinden bağımsız eşit aralıkla akıyordu (2 karelik
hazırlığın ikinci karesi "!" süresinin yarısında açılıyor, vuruş karesi isabetle denk gelmiyordu).

### Kapsam (bu sayfaları kullanan bütün düşmanlar)

| sayfa | kullananlar (yapay zekâ) | kare (eski → yeni) | satırlar |
|---|---|---|---|
| `kara_boru_v2` | kara_boru, ayaz_kurdu (lunger), yek (stalker), kirkayak (crawler), sicrayan_tazi, magara_pususu, kor_pususu (pouncer) | 18 → 93 | idle 12, walk 8, run 8, turn 3, windup 4, windup_aa 4, leap 5, back 4, dash 3, pounce 4, land 3, hurt 3, hurt_big 4, stun 6, launch 4, getup 4, death 8, howl 6 |
| `agac_iyesi_v2`, `dev_cocugu_v2` | Kara İye, Dev Çocuğu (brute); satırlar tornado / caster eşlemesini de taşır | 15 → 102 | idle 10, walk 8, turn 4, swat 9, slam 10, leap 11, roots 7, spin 8, whirl 4, hurt 3, hurt_big 4, stun 6, launch 4, death 8, roar 6 |
| `bekci_v2` | bekci, kurgan_bekcisi, yilan_muhafiz, simurg_muhafizi, tamu_bekcisi, tamu_muhafizi, kaf_bekcisi (shield); al_atli, kara_atli, kurgan_atlisi (charger) | 23 → 104 | guard 8, walk 8, turn 4, jab 7, jab_aa 2, heavy 9, bash 6, bash_aa 4, charge_windup 4, charge 6, skid 3, reset 3, stagger 6, hurt 3, hurt_big 4, stun 6, launch 4, getup 4, death 8, roar 5 |
| `balbal_v2`, `buz_balbali_v2` | Balbal, Buz Balbalı (hopper) | 11 → 82 | dormant 1, wake 6, idle 8, guard 3, hop 5, cut 9, rev 7, leap 10, turn 3, hurt 3, hurt_big 4, stun 6, launch 4, death 8, roar 5 |
| `tosbaga_v2` | tosbaga, tas_kertenkele, buz_tosbagasi (turtle) | 21 → 80 | idle 8, walk 8, turn 4, bite 9, bite_aa 4, shell 4, spin 6, dizzy 6, hurt 3, hurt_big 4, stun 6, launch 4, death 8, roar 6 |
| `surale_v2` | Gulyabani (grabber), Karakoncolos (mimic) | 15 → 89 | idle 8, walk 8, turn 4, windup 4, claw 8, grab 3, hold 4, throw 3, miss 3, lurk 1, emerge 4, snow 5, hurt 3, hurt_big 4, stun 6, launch 4, getup 4, death 8, roar 5 |
| `arcura_v2`, `kurgan_okcusu_v2`, `erlik_kizi_v2` | Kara Kam (illusionist), Kurgan Kamı (archer), Erlik'in Kızı (charmer) — üç yapay zekânın hamleleri her sayfada | 14 → 104 | idle 8, run 8, turn 3, cast 8, cast_aa 4, curse 8, bow 8, bow_aa 4, charm 8, charm_aa 3, hop 4, flip 5, appear 4, hurt 3, hurt_big 4, stun 6, launch 4, getup 4, death 8 |

Aynı çizim modülünü paylaşan öbür çeşitlemeler (tozkoparan / su_iyesi / od_iyesi → `agac_iyesi_ink.py`, isilti_bocegi →
`arcura_ink.py`) yeni iskeletle çizilebilir (`render_frame(anim, i, var)`), ama sayfaları uçan / büyücü yaratıklar
çalışmasında üretilir (bu çalışma onları dışa aktarmadı; tornado / caster / kamikaze anahtarları DURUM'da hazır).

### Gövde (iskelet) — `tools/artgen/yaratik_govde.py` + `<ad>_ink.py`
Bengü'nün v28 poz sisteminin (ayak hedefli IK, çizgi akışı, evre işaretleri) yaratıklara genellenmiş hâli:
* **Ayak hedefli IK:** pençe / ayak / kaide yerdeki (ya da havadaki) hedefiyle yazılır; iki-üç kemikli bacak çözülür
  (`ik2`, tazıda uyluk-baldır-tarak ve kürek-kol-ön kol-tarak), yere basan ayak kaymaz, erişilemeyen hedef kırpılır,
  itişte parmak ucu yerde kalır / topuk kalkar.
* **Gövde:** bütün figür dönüşümü (`xf_push`: öteleme, öne / arkaya devrilme, daralma = dönüş), gövde eğimi (pitch /
  lean), omurga bükümü (tazının dörtnalında toplanma-gerilme `flex`, kambur `arch`), omuz burulması (bekçide vuruş kalça
  ve omuzdan çıkar), nefes.
* **Baş önden gider:** baş grubu boyun dibinde döner (`hr`), çene / dudak (hırlama kırışıkları), göz alevi ("!!"), göz
  kısılması (acı), tüy dikleşmesi (`hack`).
* **İkincil hareket:** kuyruk, duman yele, tasma zinciri, çaputlar, yosun, sorguç, etek, kefen, saç, kam saçakları
  gecikmeli dalgayla (bekçide pozun 0,08 önceki hâline göre) ve yerçekimine göre sarkar; yere değen kumaş yığılır.
* **Efekt kareleri:** vuruşta toz / toprak / taş kıymığı, kılıç izi hilali (Balbal), şok yarığı (bekçi ağır vuruşu),
  kam rün halkası ("!!"), ısırık şaklaması, ölümde kül / ruh telleri.
* `yg.bake_xf(cv)`: dönüşüm altında kurulan `details` mürekkep çizgileri çizim anında kayıyordu (inkkit ayrıntı noktalarını
  `finish`'te dönüştürür); yaratık tuvallerinde noktalar kuyruğa girerken dönüştürülür (Bengü çizimi etkilenmez).

Ayak işi kaynakları: Muybridge, *Animals in Motion* (köpek / at yürüyüş ve dörtnal levhaları; archive.org) ve Hildebrand
(1980) yürüyüş sıraları: tazı yürüyüşü **yanal 4 vuruş** (yakın arka → yakın ön → uzak arka → uzak ön, %25 arayla,
basma oranı 0,68), dörtnal **döner (rotary)** — uzak arka → yakın arka → askı → yakın ön → uzak ön → askı (toplanmış ve
gerilmiş iki askı evresi; omurga toplanır / gerilir). Tosbağa yürüyüşü yanal 4 vuruş, basma 0,74 (her an üç ayak yerde).
Basan ayak gövdeye göre sabit hızla geri kayar; satıra `vx` (adım boyu / basma süresi) yazılır ve oyunda koşu hızına
kilitlenir (`dspeed = |vx| / vx_satır`, 0,5-2,2): ayak kaymaz.

### Evre eşlemeli oynatma — `Enemy._anim_tick`, `SpriteAnim.director` (sözleşme: `docs/v29/enemy_anim_json.md`)
Json'da `"durum"` olan sayfada kareyi yönetmen seçer; yapay zekânın `anim.play` / `show_frame` çağrıları yalnızca istek
olarak kaydedilir (`SpriteAnim.req`). `"durum"` eşlemesi durum / hamle / zırh ("!!") → animasyon evresi:
* hazırlık `u: st` = `1 - st / st0`: kalkış, kurulma, **derin kurulma "!" boyunca tutulur**, son kare (`lead` ≈ 0,05 sn)
  fırlayış / süpürme — isabet karesinden hemen önce; zırhlı hazırlık (`!!` anahtarı) ayrı ve daha tehditkâr poz;
* vuruş evresinin **ilk karesi temas karesi** (yapay zekâ vuruş kutusunu tam o anda açar), ardından takip ve toparlanma
  (`recover/<hamle>`: hamle saldırıdan sonra da durur, toparlanma hamleye göre seçilir; boş hamle bir sonraki duruma
  taşınır — pusu tazısının perch atlayışı `leap/pounce`);
* havadaki hamleler (sıçrayış, sekiş, geri takla, havaya savrulma) `u: vy` = dikey hız evresi (kalkış → tepe → iniş);
* tepkiler (öncelikli): `_launch` (havada), `_break` (duruş kırık / sersem), `_hurt_big` (büyük vuruş), `_hurt` (hafif;
  zırhlı ağır yaratık boşta / kovalarken vurulunca da), `_getup` (savrulma sonrası iniş), `_turn` (yön değişimi),
  `_roar` (seçkin kükremesi), `_guard` (Balbal siperi). Zırhlı hamle sürerken vurulan yaratık tepki göstermez: hamlesini
  sürdürür (okunur "!!").
* geçiş anahtarları: `dormant>recover` (Balbal uyanışı), `lurk>windup` (Karakoncolos pusudan fırlar), `spin>recover`
  (tosbağanın başı döner), `hold>recover` / `grab>recover` (Gulyabani fırlatır / ıskalar), `charge>windup` (akıncının
  hücum ortasında dönüşü).
* **Ölüm** (`_death`): `Enemy._die` → `Corpse.play_frames`: ceset satırı 0,9 sn'de oynar, dönmeden, ayakları yerde
  kısa kayar (darbe yönü), son kare tutulur, sonra kül olur. (Eski savrulan ceset `setup`'ta kare merkezini doku
  pikseliyle hesaplıyordu: texel 4 sayfalarda ceset 100+ birim kaymış başlıyordu; çerçeveli yol sprite'ın tam yerinden
  başlar.)
* **Kısa biçim** (uçan / büyücü sayfalarının kuralı): `"durum": {"windup": "tele", "windup_zirh": "tele_zirh", "death":
  "death", "spawn": "spawn", "evade": "hop", "explode": ..., "blink_out" / "blink_in": ...}` — değer yalnızca satır adı;
  satırdaki `mk` = [W, C, H] (Bengü v28 kuralı, `ts` isteğe bağlı) varsa hazırlık [0, W], vuruş / etkin [C, H],
  toparlanma [H, 1] evrelerine eşlenir. `show_frame("attack", 0/1)` gibi eski çağrılar eşleme yoksa aynen çalışır.
Yapay zekâ, süreler, vuruş kutuları, zırh / jeton kuralları **değişmedi** (yalnızca görsel). `"v29"` olmayan sayfalar
(`"durum"` olmayan: bosslar, v1 piksel stili) eskisi gibi oynar.

### Varlıklar
`python tools/artgen/export_yer.py [kimlik ...]` (+ `KY_HD=2`, sonra `python hd_paket.py --paketle`); satır düzeni
artık modülün `SEQS` sözlüğünden (v1 json'undan değil). Işıma sayfaları yarım çözünürlükte (`"glow_scale": 2`; depo
boyutu ~1/4). Önizleme: `python tools/artgen/yer_onizleme.py <kimlik> <çıktı.jpg> [anim ...]`. Sayfalar 4096 px'i
aşınca `_p1`, `_p2` sayfalarına bölünür (Data.sprite / SpriteAnim zaten destekliyor).

### Ölçüm ve test
Başsız, `--fixed-fps 60`, betik hatası (SCRIPT ERROR) **0**:
* `--yaratik` (19 tür: kara_boru, ayaz_kurdu, yek, kirkayak, sicrayan_tazi, agac_iyesi, dev_cocugu, bekci, al_atli,
  kurgan_bekcisi, balbal, buz_balbali, tosbaga, tas_kertenkele, surale, karakoncolos, arcura, kurgan_okcusu, erlik_kizi);
  `--zeka --muhur=0` (23 tür, TABLO + BITTI); `--dovus --boss --kontrol`: KONTROL basış=272 basılmamış=0, oto_dönüş=0,
  oto_hamle=0, istenmeyen_ağır=0, **TAKILMA=0**; `--harita` SONUC GECTI; `--otomatik --derinlik=1/3/5 --muhur=0`;
  `--mekanik --muhur=0` BITTI; `--piksel_tara` TOPLAM 0. Kalan `ERROR` satırları v29 öncesinden (InkAksanFX
  üçgenleme / `p_points.size() < 2`, çıkışta sızıntı uyarısı).
* Yapay zekâ: `Enemy.gd` farkı yalnızca yönetmen bloğu, `_ready`'de `_ds_setup()`, `_tele`'de `_ds_reset`, `take_hit`'te
  tepki kaydı, `_die`'de ölüm kareleri; durumlar, süreler, vuruş kutuları, zırh / jeton dokunulmadı. `--zeka` sayıları
  rastgeleliğin oynattığı aralıkta (ör. kara_boru ilk 0,85-0,95 sn, hamle/10sn 6-6,5).
* Oyun içi film (`--write-movie`, 1280x720, 30 fps, `--yaratik=... --yaratik_oldur`: yaratık oyuncuya saldırır, iki vuruş
  yer, sonunda öldürülür): hazırlık derin kurulmada bekliyor, temas karesi isabetle, ölüm cesedi yerinde çöküp kül oluyor.
  `tools/tests/yaratik_testi.gd` yeni `--yaratik_oldur` seçeneği; `yaratik_galeri.gd` v29 sayfalarda yönetmeni kapatıp
  her satırın ortadaki karesini çeker.
* HD: `KY_HD=2 export_yer.py` + `hd_paket.py --paketle` (manifest md5 güncel); `--doku=2 --yaratik=...` hata 0.
* Kısa biçim sınaması: `cor_v2.json`'a geçici `"durum": {"windup": "attack", "windup_zirh": "attack", "death": "attack",
  "spawn": "idle", "dive": "attack"}` + `mk` ile `--zeka --zeka_tur=cor,kara_kus_yavrusu`: betik hatası 0 (dosya geri alındı).

### Görseller (`docs/v29/`)
* `once_sonra_<kimlik>.jpg`: üstte eski sayfanın bütün kareleri, altında yeni satırlar (evre adlarıyla).
* `oyun_<kimlik>.jpg` (kara_boru, agac_iyesi, bekci, al_atli, balbal, tosbaga, surale, arcura): oyun içi çekim
  (1280x720, 30 fps film karelerinden kırpım): yaklaşma, "!" / "!!" hazırlık, saldırı, vuruş tepkisi, ölüm (ceset yerinde
  çöker, sonra kül olur).

### Bilinen
* Depo boyutu: 11 temel sayfa ~7,7 → ~57,6 MB (ışıma yarım çözünürlükte), HD x2 WebP paketi de büyüdü; toplam fark
  ~80 MB. Kare bütçesi sayfa başına 80-104 tutuldu.
* Kara İye / Dev Çocuğu en geniş satırı 11 kare: HD sayfa 11264 px genişliğinde (Forward+ donanımının 16384 sınırının
  altında; temel sayfa 5632).
* Yan görünüş: dönüş ve döner savuruşlar gövdenin yatayda daralıp aynalanmasıyla taklit edilir (3/4 görünüş yok);
  daralan karelerde kontur kalınlığı ölçeklenmediği için silüet kâğıt gibi olabilir (hızda okunur).
* Bazı derin öne çöken vuruş karelerinde (Kara İye çakma / kök) kafatası ön kolun arkasında kalır; bekçi ölümünün bir
  ara karesi ve Gulyabani'nin yakalama karesi hücre kenarına çok yakın.
* Tazı / tosbağa yürüyüşü `vx` ile hıza kilitli; çok hızlı türlerde (ör. Taş Gulü, tas_kertenkele 90 px/sn) 2,2 kat sınırına çarpınca ayak
  biraz kayar.
* Ağır yaratıklar oyunda havaya fırlatılmaz; `launch` satırları yalnızca sanat kilidi (Göğe Yükseliş) içindir.
* tozkoparan / su_iyesi / od_iyesi / isilti_bocegi sayfaları bu çalışmada yeniden üretilmedi (sahibi uçan / büyücü
  çalışması); modülleri yeni iskeletle çizilebilir ve DURUM anahtarları hazır.

## v29: boss animasyonları

Geri bildirim: "Bütün düşmanlar için de yap: saldırırken yalnızca kol oynuyor. Gerçekten karşımda gerçek bir canavar
varmış gibi hissettirsin; çok profesyonel olsun." Bu bölüm beş bossu kapsar (sıradan yaratıklar ayrı çalışmalarda).

### Sorun (v28)

Her bossun stil v2 sayfası v1'den kalma 8 satır taşıyordu (idle, walk, windup, strike, slam, cast, hurt, rage; toplam
~35 kare). Bütün hamleler bu satırları paylaşıyordu: Tepegöz'ün gürz çakışı, kaya atışı, kavrama, göz ışını ve hücumu
aynı "windup" / "strike" karelerini oynatıyor, kareler adımın başında bir kez `anim.play` ile başlayıp uyarı süresinden
bağımsız akıyordu (temas karesi vuruş anına denk gelmiyordu). Kara Börü Han'ın hazırlık / uluma / sersem kareleri
neredeyse durgun duruşla aynıydı; Şahmeran'ın yılan gövdesi sabit bir kangaldı (sürünürken de kıpırdamıyordu); ölüm
yoktu (gövde sıradan yaratık gibi uçan ceset olarak fırlıyordu); sendeleme 2 karelik "hurt"tu.

### Yeni: hamle başına tam gövde satırları

Her bossun her hamlesi kendi satırını taşır: hazırlık (bütün gövdeyle kurulma; "!!" zırhlı hamlelerde ayrı bir duruş),
temas, aşma, toparlanma. Ayrıca durgun (nefes, ağırlık aktarımı, yaratık seğirmeleri), dolaşım, evre / giriş kükremesi,
sendeleme (duruş kırılması), açık pencereler (GÖZ AÇIK, saplanan baş) ve ölüm sırası.

| Boss | Kare (önce → sonra) | Satırlar (kare) |
|---|---|---|
| Kara Börü Han | 25 → 106 | idle 8, run 8 (dönel dörtnal), walk 8 (sinsi yaklaşma), kbh_pounce 9, kbh_back 4, kbh_rush 10, kbh_flurry 12, kbh_howl 7, kbh_wall 8, kbh_crys 5, kbh_nova 4, kbh_roar 7, kbh_stagger 7, kbh_death 9 |
| Tepegöz | 35 → 113 | idle 8, walk 8 (yeri döven ağır yürüyüş), tg_slam 10, tg_throw 8, tg_stomp 7, tg_nova 4, tg_grab 11, tg_beam 8, tg_charge 8, tg_dazed 7 (GÖZ AÇIK), tg_quake 8, tg_roar 8, tg_stagger 8, tg_death 10 |
| Şahmeran Ana | 35 → 94 | idle 8 (büyüleyici salınım), walk 8 (kangal dalgalı sürünme), sh_spit 7, sh_tail 8, sh_lunge 10 (saplanma dahil), sh_snakes 6, sh_drip 7, sh_gaze 7, sh_venom 6, sh_nova 4, sh_roar 7, sh_stagger 7, sh_death 9 |
| Yelbegen | 35 → 95 | idle 8, walk 8 (üç baş ayrı gecikmeyle sallanır), yb_club 9, yb_gust 7, yb_heads 9, yb_breath 7, yb_icicles 5, yb_blizzard 7, yb_leap 8, yb_nova 4, yb_roar 7, yb_stagger 7, yb_death 9 |
| Erlik Han | 35 → 116 | idle 8, walk 8 (ağırbaşlı yürüyüş, pelerin), er_chain 12 (atış, çekiş, yukarı savuruş, geri sarma), er_wave 8, er_fireballs 6, er_scythe 10, er_pillars 5, er_gate 9, er_souls 5, er_walls 5, er_seli 13, er_nova 4, er_roar 7, er_stagger 7, er_death 9 |

Hamle → satır eşlemesi v23 hamle tablosuyla birebir: Kara Börü Han sıçrayış zinciri (çömelme, gerilme, havada tepe,
pençeler önde düşüş, ön ayaklarla karşılama), geri sıçrayış, yer yaran hamle (pati ile yer kazıma, alçak dörtnal döngüsü,
ön ayaklar kilitlenip kayarak duruş), pençe yağmuru (sağ / sol pençe ayrı kareler, ağır pençede arka ayakları üstüne
şaha kalkıp iki pençeyle yere iner), uluma, duvardan pike (duvara çapraz tutunma, ok gibi dalış, iniş çöküşü),
bozgun kristalleri (kambur, kristaller alevlenir, her atışta geri tepme), gölge oyunu (çömelip gölgeye karışma);
Tepegöz gürz çakışı (gürz sırta düşer, adımla iki elle iner, uç tam yere gömülür), kaya atışı (eğilip kayayı yerden
söker, baş üstüne kaldırır, adımla fırlatır), yer tepme (diz göğse, topuk yere), kavrama ("!!": kambur, uzak el pençe
gibi kurulur; uzanış, tutup sıkma döngüsü, fırlatma, ıskalayınca öne savrulup toparlanma), göz ışını (baş geri, göz
açılır, öne eğilip ışını sürer; çapa her karede yeniden ölçüldü), hücum (boğa gibi baş önde, 4 karelik ağır koşu, kayarak
duruş), GÖZ AÇIK (duvara çarpıp geri teper, tek dize çöker, sersem salınım döngüsü, göz kocaman açık ve yanıyor,
kalkıp kükrer), dağ sarsıntısı (çömel - havada gürz baş üstünde - iniş çakışı); Şahmeran tükürük (geriye kalkıp baş
öne fırlar), kuyruk süpürmesi (kuyruk S biçiminde çıngırak gibi kalkar, yere kamçılanıp uzanır), sokma (kangal sıkışıp
geri çekilir, beden yatay mızrak olur; ıskalarsa baş yere saplanır ve çırpınma döngüsü), yılan sürüsü (kollar göğe,
kıvranan çağırma döngüsü), mağara yıkımı (kuyruk tavana dikilir, vurur, iner), taşlaştıran bakış ("!!": boyu uzar,
yelpaze sonuna dek açılır, elleri yüzünü çerçeveler; açılışta kollar savrulur), zehir pınarı (avuçlar her adımda yere);
Yelbegen gürz (mızrak) savuruşu, yel üfürüğü (üç baş geri çekilip nefes alır, öne uzanıp üfler), üç baş (arka / orta /
ön baş sırayla boyun uzatıp ateşler ve geri teper), ayaz soluğu (orta baş kalkıp aşağı huzme döker), saçak yağmuru
(mızrak göğe, dipçik yere), Kaf fırtınası (başlar ayrı yönlere ulur), buzlu sıçrayış (mızrak ters, iniş saplaması);
Erlik zincir (gövde burulur, kol ileri; çekişte geriye yaslanma; topuzla aşağıdan yukarı savuruş; ıskalayınca geri
sarma), ateş dalgası (topuz iki elle baş üstünden yere), Tamu ateşi (ateş küresi baş üstünde büyür, fırlatma), tırpan
(önden ve ters yatay savuruş, arada omuz burulması), kor sütunları (avuç kalkar, her sütunda yumruk yere), Tamu kapısı
(pelerinine sarınıp yere gömülür, öbür yanda pelerini açıp alevle yükselir), kayıp ruhlar, daralan Tamu (kollar iki
yana iter), Tamu Seli ("!!": kollar göğe, hale ve pelerin kabarır; lav döngüsünde ateş atışı; ikinci "!!" ve kor
yağmuru döngüsü). Her bossa ayrı "!!" yakın cezalandırıcı (nova) satırı: Kara Börü Han yere yapışıp şok uluması,
Tepegöz iki yumruk baş üstünden yere, Şahmeran kangalı sıkıp kuyruk kamçısı, Yelbegen üç baş birden kükreyip tepinme,
Erlik kollarını çaprazlayıp alev halkası.

### Poz dili (çizim: `tools/artgen/<boss>_v29.py`)

* Tam gövde: hazırlıkta ağırlık arka ayağa kayar, omurga geriye kavislenir, baş gecikmeli izler; temasta kalça çöker
  (bob 12-26), gövde öne düşer, uzak el yere dayanır; aşmada geri seker; toparlanmada adım toplanır. Ağır silahın ucu
  temas karesinde tam yere değer: `fit()` gürz / mızrak / topuz ucunu ve elleri hücre içinde tutar, uç yere gömülmez,
  baş üstü kurulmada dirsek bükülüp silah sırta düşer (hücre sınırı = silüet okunurluğu).
* Yeni çizim parametreleri: bütün gövde dönüşümü `rot` / `rp` / `dx` / `dy` (`bosskit.body_xf`: şaha kalkma, duvara
  tutunma, dalış, yıkılma; çapalar da dönüşür), Kara Börü Han'da omurga sıkışma / uzama (`hx`, `sx`), baş eğimi
  (`hp`) ve IK pati hedefleri (`('ik', x, y)`: yere basan pati kaymaz), Şahmeran'da kangal sıkışması / kayması / yürüyen
  dalga (`coil`, `cx`, `cw`) ve kuyruk biçimleri (`tup` çıngırak, `tceil` tavan, `tlash` kamçı), Yelbegen'de baş başına
  boyun uzaması ve çene (`hext`, `hj`), Tepegöz'de elden düşen gürz (`club_free`).
* Dolaşım: Tepegöz / Yelbegen / Erlik yürüyüşünde yere basan ayak 35 birim / adım hızla geriye akar, topuk vuruşunda
  ağırlık kabulü (çöküş), geçişte yükselme, omuzlar bacaklara ters döner; Kara Börü Han dörtnalı dönel dörtnal anahtar
  pozlarıyla (arka iniş, açık süzülme, ön iniş, toplanma, toplu süzülme) ve yere değen karede pati yerde (`ground()`);
  bandın içinde salınırken sinsi yürüyüş (`walk`), menzile koşarken dörtnal (`Boss._stalk`).
* Okunurluk (1,7 yakınlık): her hamlenin hazırlık silüeti farklı (kule gibi şaha kalkma, yere yapışma, kangal
  sıkışması, kollar göğe), "!!" duruşları "!" hazırlıklarından ayrı.

Kaynak / çalışma: Dark Souls 3 düşman saldırı anatomisi (hazırlık - saldırı - toparlanma evreleri;
gamedeveloper.com "Anatomy of an Enemy Attack in Dark Souls 3"), boss uyarı süresi üzerine savaş tasarımı notları
(gamedeveloper.com "Boss design tips from a combat designer": uyarı ~1-1,5 sn, vuruş kutusu görünür temasla
örtüşmeli), dönel dörtnal evreleri (Minnesota Üniv. veteriner anatomisi "rotary gallop" sayfası, Hildebrand 1977
asimetrik yürüyüşler): toplu ve açık süzülme.

### Oynatma: evre eşlemesi (`Boss.gd` "v29 animasyon eşlemesi")

Satırın json kaydında `"v29": {"seg": {ad: [ilk, son(, döngü başı)]}}` evre bölümleri vardır (dışa aktarımda modülün
`CLIPS` kaydından). Her hamle adımı `_v(adım, satır, bölüm, kip)` ile bir bölüme bağlanır; kareyi her fizik karesinde
`_v_tick` seçer (`SpriteAnim.show_frame`; SpriteAnim / Enemy değişmedi):

* `wu` hazırlık: bölümün kareleri uyarı süresinin ilk %75'ine yavaşlayarak (karekök) yayılır, derin pozda bekler, son
  kare (fırlama) son 0,08 sn'de açılır: uyarı ne kadar uzun olursa olsun duruş baştan okunur, vuruş anında gövde
  zaten iniyordur.
* `map` eylem adımına eşit yayılım: temas karesi eylem adımının ilk karesinde (vuruşun `go` anında) açılır.
* `fast`, `ol` (bir kez oynayıp döngü başına döner: göz ışını, hücum koşusu, tutma, GÖZ AÇIK, saplanma, Tamu Seli),
  `loop`, `air` (dikey hıza göre yükseliş / tepe / düşüş: sıçrayışlar, duvara sıçrayış, dağ sarsıntısı, buzlu
  sıçrayış), `hold`.
* Hamle sonu: satırın `r` bölümü `recover` bekleyişine (`_rec_t`) yayılır (ıskalanan kavramada 0,9 sn öne savrulup
  toparlanma, pike inişinde 0,75 sn çöküş). Sendeleme `<önek>_stagger` satırı sendeleme süresine (1,8 / 1,2 sn), giriş
  kükremesi giriş süresine (1,6 sn), evre kükremesi evre adımına (0,9 sn) yayılır.
* Ölüm: `_v29_death` ayrı bir düğümde ölüm satırını oynatır (diz çöker, silah elden düşer / kangal yığılır, yüzüstü
  yıkılır), son karede 1,4 sn bekler, külleşip söner; uçan ceset bu bosslarda gösterilmez. Oyun akışı (ödül, kapı,
  çağrılanların dağılması) aynı: boss düğümü yine hemen silinir.
* Yedek: satır / bölüm yoksa (stil v1 sprite'ı) eski `anim.play(eski ad)` yolu aynen çalışır; `--bosslog` eksik satırı
  "BOSS <id> ANIM EKSIK" diye yazar (beş bossun bütün hamlelerinde 0).

AI zamanları, adım süreleri, vuruş kutuları, hasar ve hız DEĞİŞMEDİ: yalnızca gösterilen kare. Tepegöz göz ışını
çapası (`tools/artgen/goz_capasi.py`) yeni sayfalarda yeniden ölçüldü (113 karenin 107'sinde parıltıdan, kalan 6'sı
— göz kapalı / ölüm — ortalama farktan): ışın yine her karede gözden çıkar (`oyun_tepegoz.jpg`, göz ışını satırları).

### Varlıklar

`python export_boss_ink.py` (beş boss; `KY_HD=2 ...` ve `python hd_paket.py --paketle`). Dışa aktarım artık satır
listesini, kare sayısını, fps'i ve döngüyü modülün `CLIPS` kaydından alır (v1 json'u eski 8 satırla kalır); dejenere bir
yol işleminde (skia) kare alt piksel kaydırılıp yeniden çizilir. Hücre boyları ve ayak noktaları aynı (kamera boss boyunu
hücreden okur). Sayfalar: Kara Börü Han 5, Tepegöz 7, Şahmeran 6, Yelbegen 9, Erlik 8 (4096 genişlik, ışıma yarım boy).
Eski `windup` / `strike` / `slam` / `cast` / `hurt` / `rage` / `howl` / `leap` satırları v2 sayfasından çıktı (v1'de duruyor).

### Ölçüm ve test

Aynı yapıda, 60 Hz, betik hatası 0: beş boss `--otomatik --boss=<id> --bossfaz=1|3 --bosslog` (Tepegöz 1/2/3), ANIM EKSIK
0; `--zeka --muhur=0 --boss=<id> --zeka_oldur` (beşi), `--zeka --muhur=0 --zeka_oldur`, `--dovus --boss`,
`--otomatik --derinlik=2|8 --muhur=0`, `--mekanik --muhur=0`, `--piksel_tara`. Sonuçlar aşağıdaki "Sonuç" satırında.

Görseller (`docs/v29/boss/`): `kare_<boss>.jpg` — üstte v28 sayfası (8 satır), altta v29 bütün satırları (her hamlenin
hazırlık / temas / toparlanma kareleri); `oyun_<boss>.jpg` — aynı zorlanmış hamlenin uyarı / vuruş / sonrası oyun
çekimi, önce ve sonra (`-- --zeka --boss=<id> --zeka_cekim=... --pencere=1920x1080`).

### Sonuç

* Betik hatası 0 (SCRIPT ERROR / Parse Error / Invalid call / ANIM EKSIK yok) bütün koşularda; kapanıştaki RID / ObjectDB
  sızıntı uyarıları v28'de de vardı.
* `--zeka --boss=<id> --zeka_oldur`: beş boss da iki botla öldürüldü (ölüm sırası her seferinde oynadı), kilit %0;
  `--zeka --zeka_oldur` BITTI; `--dovus --boss` TAKILMA=0 (OZET vuruş / iptal süreleri v28 ile aynı); `--otomatik
  --derinlik=2|8` ölüm 0, hata 0; `--mekanik` BITTI; `--piksel_tara` TOPLAM 0 (52 000+ tarama).
* Varlık boyutu (çalışma ağacı): beş bossun temel v2 PNG'leri ~38 MB → 123 MB, HD x2 WebP ~22 MB → 55 MB (toplam +~118 MB).
* 2560x1440 `--doku=2`: HD sayfalar md5 eşleşmesiyle yükleniyor (`hd_yelbegen_savurus.jpg`, `hd_yelbegen_baslar.jpg`).

### Bilinen

* Çizimler hâlâ prosedürel iskelet pozları: yan görünüş, 3/4 dönüş yok; çok hızlı hamlelerde (0,13 sn pençe) iki kare
  görünür. Kara Börü Han'ın koyu ön ayakları koyu gövdenin önünde düşük karşıtlıkta kalıyor (şaha kalkmada pençeler
  silüetten okunuyor, tek tek karede zor).
* Yerde yatan / diz çöken karelerde (Erlik eteği, Yelbegen pelerini, Tepegöz ölümü) kumaş ayak çizgisinin 6 birim
  altında hücre kenarında kesiliyor (zemin içinde, oyunda görünmüyor). Erlik'in Tamu kapısı batışı bilerek hücre
  altından kesilerek "gömülüyor".
* Depo boyutu: boss v2 sayfaları 5 × 2-3 sayfa → 35 sayfa; temel PNG ~38 MB → ~123 MB, HD WebP de buna göre büyüdü
  (ayrıntı "Sonuç"ta). HD x2 kipinde bir bossun sayfaları ~5-9 × 64 MB VRAM (BPTC + mipmap); bosslar arenadan çıkınca
  önbellekten düşüyor (v24 `Data.forget_sprite`).
* Sıradan yaratıkların tam gövde animasyonları bu bölümün kapsamı dışında (ayrı çalışmalar: yer / uçan yaratıklar).


## v30: eski piksel stili (v1) kaldırıldı

İstek: "eski piksel paketleri kaldırılabilir" (depo GitHub'da paylaşılıyor, ~1 GB'a yaklaşmıştı). Oyun v19'dan beri
mürekkep (v2) stilinde açılıyordu; v1 piksel görünüm `-- --stil=v1` ile duruyordu. v30'da v1 dosyaları, `--stil`
seçeneği ve v1 çizim dalları kaldırıldı. Görünüş ve davranış v2'de aynı.

### Denetim (neyi v2 hâlâ okuyordu?)

Bütün test takımı `--verbose` ile koşuldu (her `ResourceLoader` yüklemesi "Loading resource" satırı) ve `Data.load_json`
geçici olarak her JSON yolunu yazdı: 11 derinlik, 5 boss (`--bosslog` ve `--otomatik`), yurt turu, sahne / savuruş,
yaratık, zeka, dövüş, sanat, silah27, Bengü, yay, tomar, unsur, harita, tüccar, mekanik, denge, 15 arayüz ekranı +
`--arayuz=...`, `--piksel_tara`; HD `--doku=2` (5 derinlik, 5 boss, yurt, ekran) ve `--doku=3`. 2136 farklı yol yüklendi.
v2'nin yüklediği v1 dosyaları ve karar:

| Dosya | v2'de ne için | Karar |
|---|---|---|
| `assets/weapons/weapons.png`, `_n`, `_e` (+ x2 / x4 HD) | `Data._ready` açılışta yüklüyordu; çizilmiyordu (69 eşyanın hepsi `weapons_v2` atlasında) | kaldırıldı, yüklemesi silindi |
| `assets/weapons/weapons.json` | meta: eski hücre pivotu (yerdeki silahın ortalanması, `Pickup.gd`), `texel` | **kaldı** (6 KB) |
| `assets/decor/decor.json` | `Data._ready` yüklüyordu; yalnızca v1 süs yolu kullanıyordu | kaldırıldı |
| `assets/tiles/otuken.json` | `Data.tile_meta`; `_tmeta` geri dönüşü (her biyomun `_v2.json`'u var) | kaldırıldı |
| `assets/ui/pixel.fnt` (+png) | `Data._ready` yüklüyordu; `InkUI.setup` hemen fırça yazısıyla değiştiriyordu | kaldırıldı |
| `shaders/toon_light.gdshader`, `aapix.gdshaderinc` | `Game.toon_shader` önyüklemesi; v2'de hiçbir düğümde kullanılmıyordu | kaldırıldı |
| `assets/fx/anim/anim.json` | `AnimFX.has` kimlik listesi (mürekkep karesi olmayanlar mürekkep sıçrantısına düşer) | **kaldı** |
| `assets/fx/slash/slash.json` | `SlashFX.has` / yay yarıçapı `"w"` (mürekkep yay ölçüsü) | **kaldı** |
| `assets/tiles/hazards.json` | tehlike türü → satır (`"rows"`), v2 atlasları aynı yerleşimde | **kaldı** |
| `assets/sprites/<ad>.json` (19 v1 sprite json'u, 134 KB) | oyun okumuyor; mürekkep üreticileri satır düzeni şablonu olarak okuyor (`export_ink.py`, `export_boss_ink.py`, `export_yaratik_a.py`, `export_ucan.py`) | **kaldı** |

Ayrıca hiç yüklenmeyen ama yolu kodda duran v1 dalları: sprite / karo / arka plan geri dönüşü (`Data.stil_id`), v1 süs
(`Data.decor`), Kenney parçacık dokuları (`FX.tex`), piksel ok sayfası (`arrows.png`), `god_ray.png` hüzmeleri (bütün v2
biyomlarında `rays` alfa 0), v1 tehlike atlası, v1 zemin (`ground.gdshader`). Hepsi kaldırıldı; `--piksel_tara` öncesi de
sonrası da TOPLAM 0.

### Silinenler (çalışma ağacı)

| Kategori | Dosya | Boyut |
|---|---|---|
| `assets_hd/x4` (eski v1 4K paketi, tümü) | 247 | 58,7 MB |
| `assets_hd/x2` v1 girdileri (+ manifest'ten 123 girdi) | 246 | 19,5 MB |
| v1 karolar / toprak / tehlike | 55 | 6,8 MB |
| v1 sprite sayfaları (png / `_n` / `_e`) | 106 | 5,2 MB |
| v1 paralaks arka planlar | 60 | 3,2 MB |
| v1 silah atlası | 6 | 1,1 MB |
| v1 süsler (+ `decor.json`) | 193 | 0,5 MB |
| v1 üretici betikler (`tools/artgen`: `export_assets`, `export_hd`, `export_v2`, `otuken_v2`, `pixkit`, `pixfont`, `biomes`, `soil`, `bg_*`, `bgkit`, `hdkit`, `env_forest`, `slashfx`, `arrows`, `hazards`, `weapons`, `yurt_hd`, `preview_ground`, `hd_import`) | 23 | 0,5 MB |
| v1 FX (PVFX piksel kareleri, piksel kesikler, Kenney `k_*`, ok sayfası, `god_ray`, `leaves`, `soft_dot`) | 137 | 0,4 MB |
| piksel yazı tipi, v1 gölgelendiriciler, kullanılmayan v1 sınıfları (`ImpactFX`, `RingFX`, `SlashArc`) | 16 | <0,1 MB |
| **Toplam** (`.import` / `.uid` dahil) | **1089** | **~96 MB** |

İzlenen dosyalar 730,6 MB → ~635 MB. Git geçmişi eski blobları tutmaya devam eder: klonu küçültmek geçmişin yeniden
yazılmasını ister (ayrı iş, kullanıcı onayıyla). Ölçüm: paket ~904 MB; bu committe silinen yolların bütün sürümleri
~96 MB. Paketin asıl yükü güncel v2 varlıkları (`assets/sprites` 327 MB, `assets_hd/x2` 214 MB, eski sürümleriyle) ve
`motor/` Godot zip'i (82 MB): yalnızca v1'i geçmişten silmek klonu ~800 MB'a indirir.

### Kod

* `Data`: `stil` değişkeni ve `--stil=` yerine `const STIL := "v2"`; `stil_id` hep `_v2` arar. `weapon_tex`,
  `weapon_glow`, `weapon_image`, `weapon_icon_rect`, `weapon_region`, `decor()`, `decor_meta`, `tile_meta`,
  `pixel_font` kalktı; `has_weapon_sprite` v2 atlasına bakar (eşya kümesi aynı). HD paketi yalnızca x2 (2K ve 4K'da
  zaten x2 kullanılıyordu).
* `FX.ink()`, `InkUI.on()`, `InkDraw.on()`, `Level.ink()` ve sınıflardaki `ink` bayrakları (Corpse, ExplosionFX,
  GroundShadow, LightningFX, StatusOverlay, StreakFX, ThunderFX, FirePool, GroundMarker, RootSpikes, KizismaFX,
  EnemyBar, Blood, GroundSlamFX, Projectile, BowString, AnimFX, KutGate, Totem, NPC, Bezirgan) kalktı; v2 dalları
  koşulsuz, v1 `_draw` / piksel dalları silindi. Dönüşüm dalları değiştirmedi, yalnızca v2'de hiç çalışmayan dalları
  sildi: rastgele sayı tüketimi aynı (GroundSlamFX'in görünmez benzetimi bu yüzden duruyor).
* `PixUI` artık yalnızca `InkUI`'ye düşen ortak imzalar + palet (7x7 piksel simge tablosu yerleşim kutusu olarak kaldı).
* `Level`: v1 zemin (`ground.gdshader`), v1 tehlike atlası, v1 süs / yurt süsü geri dönüşü, `Data.tile_meta` geri dönüşü,
  v1 yurt paralaksı (artık doğrudan `data/yurt_v2.json`), v1 kamera dalı; `ParallaxBG` varsayılan v1 katmanları ve
  `god_ray` hüzmeleri.
* Ayarlar: v1'e özgü "Ölçekleme: Keskin piksel" satırı kaldırıldı (görüntü hep kesirli ölçekle doldurur; satırlar bir
  kaydı, eski `olcek` ayarı yok sayılır).
* `SlashFX` yalnızca meta sınıfı (`RefCounted`); `AnimFX` yalnızca mürekkep karesi oynatır.
* `piksel_tara`: "cizim" sınıfı (v1 `_draw` sınıflarının `ink` bayrağı) kalktı; diğer denetimler bekçi olarak duruyor.

### Test

Aynı takım silme sonrasında yeniden (73 koşu, `--verbose`; ayrıca son düzeltmelerden sonra 12 koşuluk ikinci tur):

* Betik hatası 0: `SCRIPT ERROR`, `Parse Error`, `Compile Error`, `Invalid call` / `access` yok; eksik kaynak 0:
  `Resource file not found`, `JSON açılamadı`, `Failed loading`, `Cannot open file`, `No loader found` yok (öncesi de 0).
  92 betiğin hepsi derleniyor. Kalan motor uyarıları (çokgen üçgenleme, kapanış sızıntıları) öncesinde de aynı türde ve
  sayıda vardı (`--yay --boss`: ana dal 1905, v30 2023 satır, koşudan koşuya değişiyor).
* Silme sonrası yüklenen v1 adlı dosyalar yalnızca dört meta json (`anim.json`, `slash.json`, `hazards.json`,
  `weapons.json`); tüm yollar mevcut.
* `--piksel_tara` TOPLAM 0 (otomatik 3 / 5 / 6 HD / 9, Erlik Han, yurt, ayarlar ekranı); mekanik BITTI, dövüş / yay /
  sanat TAKILMA=0, silah27 / sanat / tomar / harita / tüccar GECTI, unsur HATA=0, Bengü hata=0, zeka / denge BITTI,
  yurt turu dört NPC'yi görüp Kut Kapısı'na vardı; HD `--doku=2` ve `--doku=3` (x4 yok, x2'ye düşüyor) hatasız.
* Önce / sonra ekran görüntüleri (1920x1080, aynı tohum; `docs/v30/`): oyun sahneleri aynı (fark yalnızca botun konumu
  ve rastgele düşen eşyalar), Ayarlar ekranında "Ölçekleme" satırı yok.

### Bilinen

* Git geçmişi silinen v1 bloblarını (~96 MB) tutuyor; klonu küçültmek için geçmiş yeniden yazılmalı (ayrı iş, onayla).
* v1'den kalan dört meta json ve 19 v1 sprite json'u (satır düzeni şablonu) bilerek duruyor; `weapons.json` yerine
  `weapons_v2.json`'a bir "yer ortalama" alanı eklenirse o da kalkabilir.
* GroundSlamFX'in görünmez piksel benzetimi (v2'de `visible = false`) rastgele sayı akışını değiştirmemek için duruyor.
* `data/world.json` biyom `art` girdilerinde v1 değerleri (ör. `rays`, `bg`) stil_v2.json tarafından eziliyor; veri
  olarak bırakıldı.


## v31: yeni kombo savaş sanatları

> **v32 notu:** Bu bölümdeki beş sanattan **Evren Kuyruğu, Tengri Çarkı ve Yer Yarığı** Göğe Yükseliş'in "kaldır → havada
> vur → çak" iskeletini yinelediği için v32'de kaldırıldı; yerlerine Pehlivan Savurması, Yıldırım Ağı ve Tulpar Dörtnalı
> geldi (bkz. "v32: özgün savaş sanatları"; eski kayıtlar kendiliğinden taşınır). Kurt Dansı, Akıncı Akını, Ritim basışı,
> ortak kilit / tavan / duvar güvenliği ve aşağıdaki test altyapısı aynen sürüyor; kaldırılan üç sanatın satırları
> tarihçe olarak bırakıldı.

İstek: "Yeni savaş sanatları ekleyelim — Göğe Yükseliş gibi daha kombo tabanlı; onu çok sevdim." Beş yeni sanat: her
biri tek T basışıyla baştan sona oynayan, çok vuruşlu, koreografili bir dizi (kaldırma, havada kilit, çekme, yerden /
duvardan sekme, çakma, bitiriş süslemesi). v22 ilkesi aynı: dizinin her parçası basılan sanatın içinde; sanat bittikten
sonra kendiliğinden ek saldırı yok (yalnızca Yer Yarığı'nın zaten çıkmış yarığı zeminde yolunu tamamlar, Ay Hilali'nin
hilali gibi). Kod: `scripts/actors/SavasSanati.gd` ("v31 kombo sanatları" bölümleri), `scripts/core/SanatFX.gd`
(bileşimler, yeni kipler), veri `data/sanatlar.json`; Enemy.gd'ye tek kanca (`sanat_egim`: kilitliyken gövde eğimi).

### Ritim: zamanlı ek basış (ustalık)

Her yeni sanatta bitirişten ~0,38 sn önce oyuncunun çevresinde **daralan fırça halkası** belirir; içte ince bir hedef
halka vardır. Halka hedefe kapandığı anda (pencere −0,13 / +0,08 sn) T'ye yeniden basılırsa bitiriş **TAM** olur:
bitiriş hasarı ×1,35 (`ritim_k`), daha yüksek savurma / daha uzun yarık, altın ışınlar, küçük altın "TAM!" damgası,
`sanat_tam` sesi. Halka görünürken erken basmak şansı yakar (ezbere basış ödüllenmez); halka görünmeden önceki basışlar
yok sayılır. Basılmasa da dizi aynen biter (yalnız ×1,0).

### Ortak kurallar

* **Sıradan** düşman (seçkin / boss / ağır değil; `kaldirilir`) kilitlenir (`Enemy.sanat_tut`: yerçekimi, yapay zekâ,
  temas hasarı yok), kaldırılır, çekilir, çakılır. **Seçkin, boss, ağır** yalnız hasar + duruş + kısa sersemlik alır
  ("kalkmaz" yazısı); Tengri Çarkı'nda biraz sürüklenir.
* **Tavan / duvar güvenliği**: her kilit hedefi düşmanın gövde kutusuyla ızgarada taranır; katı karoya giriyorsa
  başlangıçtan hedefe ikili aramayla en uzak serbest noktaya kısalır (`_serbest_hedef`). Kaldırma / dönme / fırlatma
  yüksekliği her ilgili sütunda tavana göre kısalır (`_oda`, `_firlat_vy`); oyuncunun yükselişi de. Hareket hep
  `move_and_slide` (duvara girilmez). Kurt Dansı'nın atılış yeri duvar ya da uçurumsa düşmanın önünde durulur.
* Sanat kesilirse (oyuncu öldü / kavrandı) kilitler bırakılır, havadakiler olağan düşüşle iner; girdap ve izler söner.
* Süper zırh, telegraf (ensō + tamga + ad), Alp Nişanı, bekleme, sınıf kuralı v27 ile aynı.

### Sanatlar

Hasar = kuşanılan silahın hasarı × çarpan (`Player._deal`; tomar, kritik, unsur aynen). Boss çarpanı `boss_k`.

| Sanat | Dizi | Nişan / bekleme | Hasar (sıradan bir düşmana) | Sınıflar | Alp Ata |
|---|---|---|---|---|---|
| **Kurt Dansı** (al, palet 14) «Börü'nün dansı» | 0,12 sn çömelme → çevredeki (210 px, görüş hattı) en çok **4 düşman** arasında zincir: her adım 0,06 sn'de hedefin öbür yanına atılış (dokunulmaz) + kesik; yoldaki herkes kesilir. Sıradanlar kesikte **donar** (yerden 6-22 px asılı), her kesik üstte al bir iz bırakır. Az düşmanda aynıları arasında gidip gelir. Sonra sırtı dönük **kına koyuş**: **"ÇIT!"** — bütün izler aynı anda patlar, sıradanlar havaya fırlar (~56 px, TAM 70) | 2 / 6,5 sn | kesik ×0,6 (4 adım) + patlama ×1,3 (+0,2 / ek kesik) | hançer, düello, kılıç | 65 Kut |
| ~~**Evren Kuyruğu**~~ (v32: kaldırıldı; yeşim, 15) «Ejderin savruluşu» | alçak **tam tur süpürme**: herkes biçilir, sıradanlar **yere serilir** (yatık kilit) → **yükselen sarmal**: oyuncunun çevresinde dönerek birlikte kalkarlar (92 px'e dek), 3 sarmal vuruşu → tepede silah baş üstüne → öne doğru **çark** gibi dalış: önüne çakılırlar **"KÜT!"**, **yerden sekerler**; çevreye alan hasarı | 2 / 7 sn | ×0,8 + 3 × ×0,4 + çakılma ×1,6 (alan ×1,2) | mızrak, uzun sap, ağır, dev | 70 Kut |
| ~~**Tengri Çarkı**~~ (v32: kaldırıldı; gök, 16) «Gök Tanrı'nın çarkı» | silah baş üstünde döner, önde **girdap** açılır; 190 px içindeki sıradanlar **sarmal yolla içine çekilir** ve havada döner (seçkin / ağır biraz sürüklenir) → girdapta **4 vuruşluk hokkabazlık** (yükselen, inen, yatay, saplama) → çark patlar **"VUŞ!"**: kilitliler dışarı savrulur (430 px/sn), **duvara çarpan seker** (`Enemy._wall_slam`) | 2 / 7 sn | 4 × ×0,4 + patlama ×1,4 (+ duvar) | kırbaç, kılıç, mızrak, uzun sap | 75 Kut |
| ~~**Yer Yarığı**~~ (v32: kaldırıldı; toprak, 17) «Toprak Ana'nın öfkesi» | ağır kaldırış → silah zemini döver: çevredeki sıradanlar **yerden seker** ve havada asılı kalır (70 px'e dek, önde dizili) → sıçrayış → havada **X** kesik → dikine dalış: hepsi yere çakılır **"ÇAT!"** ve zemin önüne doğru **yarılır**: yarık 640 px/sn ile 220 px ilerler (TAM 300), duvarda / uçurumda biter, yolundaki sıradanları fırlatır, seçkini sersemletir | 2 / 7 sn | ×0,5 + 2 × ×0,5 + çakılma ×1,6 (alan / yarık ×1,0) | ağır, dev, kılıç, uzun sap | 70 Kut |
| **Akıncı Akını** (ak / kemik, 18) «Sınır boylarının baskını» | geriye **takla** (gövde havada geriye yatar) ve tepeden önündekilere **5 okluk yelpaze** → inince öne **atılarak 6 okluk seri** (oklar bir düşmanı delip arkadakine de saplanır) → durup yayı sonuna dek **gerer** (oka toplanan rüzgâr çizgileri, uçta parıltı) → **delen mürekkep oku "VIZ!"**: 980 px/sn, 420 px, en çok 8 düşmanı deler. Oklar sıradanları **yere çiviler** (kök 0,6-1 sn + kısa sersem); delen ok sıradanları geri savurur (duvara çakılır) | 2 / 7 sn | yelpaze 5 × ×0,3, seri 6 × ×0,25, delen ×1,4 (yayın hasarı) | yay (iki yuvadan birinde) | 60 Kut |

Kilit açma v27 ile aynı: **Alp Ata** Kut bankasından öğretir (yukarıdaki bedeller), **Sanat Tomarı** (boss kesin, seçkin
%12) açılmamışlardan birini açar. Duraklatma / Alp Ata ekranında liste artık 13 sanat: en çok 8 satır görünür, liste
seçimle kayar (üstte / altta kalan varsa küçük ok). Kartta hasar satırı yeni sanatlarda bölümleri ve "TAM ×1,35"i yazar.

Denge: yeni sanatların hepsi 2 nişan ve 6,5-7 sn bekleme (Göğe Yükseliş 2 / 6). Tek sıradan düşmana toplam çarpan
×3,0-3,7 (Göğe ×5,8), ama hepsi çok hedefli ve TAM ile bitiriş ×1,35; seçkine yalnızca ilgili vuruşlar + alan hasarı
(×1,5-2,5). Akıncı Akını yayın (düşük) hasarıyla ölçeklenir; ilk denemede delme yüzünden çok güçlüydü (yelpaze 0,4 →
0,3, seri 0,35 → 0,25, delen 1,6 → 1,4). Süreler 1,3-1,8 sn (vuruş duraklamaları dahil).

### Görseller (sumi-e fırça sistemi)

Her sanat kendi paletinde (`SanatFX.PAL_EK` 14-18; InkFX vuruş lekeleri ve InkTrail için en yakın InkFX paleti,
`SavasSanati.IPAL`). Yeni kipler: `ritim` (daralan halka), `girdap` (merkeze kıvrılan beş kol, ön koyu / arka sulu),
`kesik_iz` (düşmanı izleyen, nabız gibi atan al kesik), `delen` (uzun fırça mızrağı ok + kuru hız çizgileri + sulu
yankılar; kendi vurur, duvarda kırılır).

| Sanat | Bileşim |
|---|---|
| Kurt Dansı | hazırlıkta arkadan ayağa toplanan kuru hız çizgileri; her atılışta yol boyunca sulu yıkama + kuru hız fırçası + sumi çizgi + al damar + ak çekirdek ve savrulan **erik çiçeği yaprakları**; varışta ince uzun iaido kesiği; düşman üstünde asılı al izler (ek kesikte çaprazlanır, kalınlaşır); çıtta her izde büyük al X, sıçrantı, yaprak patlaması (TAM: altın varak), belde kına kayan ak çizgi + parıltı, izlerin üstünde "ÇIT!" |
| Evren Kuyruğu | ayakta toplanan ejder pulları; ayak hizasında yassı elips süpürme fırçası + toz kılları; iki tur yükselen yeşim helezon (ön yarısı koyu ve pullu, arka yarısı sulu); önde dikine dönen çark halkası; çakılışta yukarıdan kıvrılıp yere en kalın inen **ejder kuyruğu** S darbesi ve pulları, yer yarığı, iki yana sürtme, "KÜT!" |
| Tengri Çarkı | baş üstüne toplanan rüzgâr çizgileri ve küçük ensō; dönerek daralan girdap; her vuruşta girdabın içinden geçen başka açıda gök kesiği; patlamada **sekiz kollu gök çarkı** (ışınsal kalın fırçalar), dışa büyüyerek savrulan kırık ensō yayları, büyük yıkama, "VUŞ!"; duvara çakılanda duvar boyunca kırık çizgiler ve sıçrantı |
| Yer Yarığı | kaldırışta uca toplanan kuru fırçalar; dövüşte önde küçük yarık, zemin boyunca koşan toprak çizgisi, seken her düşmanın altından fışkıran toz fırçaları, havaya sıçrayan taş kıymıkları; havada toprak rengi X; inişte yukarıdan yere kalın darbe (Bir Çekiş bileşimi toprak paletinde) + kızgın yarık çizgisi + "ÇAT!"; ilerleyen yarığın her 24 px'inde yarık lekesi, kızgın çizgi, kıymık ve toz |
| Akıncı Akını | geriye kıvrılan takla yayı; yaydan öne-aşağı açılan yelpaze çizgileri; her okun ardında ak fırça izi; çivilenen düşmanda saplı ok gövdesi + tüyler + sıçrantı; germede oka toplanan rüzgâr çizgileri ve uç parıltısı; bırakışta geri tepen kuru çizgiler, yıkama halkası, "VIZ!"; delen ok |

**Yansıma sözcükleri**: `sanat_fx` atlasına GÜM! ile aynı fırça diliyle (hafif eğik, kalın-ince, harf başına oynayan
taban, sıçrantı damlaları) altı sözcük eklendi: ÇIT!, KÜT!, VUŞ!, ÇAT!, VIZ!, TAM! (256x128; kullanılmayan `seal`
hücresi ve iki boş hücre; diğer şekiller bayt bayt aynı). Üretim: `python tools/artgen/sanat_fx_ink.py`, HD:
`KY_HD=2 python sanat_fx_ink.py` + `python hd_paket.py --paketle`. `SanatFX.damga(konum, sözcük, palet, yön, ölçek)`.

**HUD tamgaları** (`glyph_strokes`, HUD ve telegraf aynı kaynaktan): Kurt Dansı üç kıvrık pençe kesiği + kın çizgisi;
Evren Kuyruğu kıvrılan S kuyruk + iki pul; Tengri Çarkı merkezden kıvrılan üç kollu çark; Yer Yarığı inen darbe, zemin
çizgisi, kırık yarık; Akıncı Akını gerili yay + kiriş + tek uzun ok.

### Ses (`tools/audiogen/v27_sanat.py`, sentez)

`sanat_dans` (atılış "fışt"), `sanat_cit` (kına giriş tıkı, kısa sessizlik, birden patlayan kesikler), `sanat_evren`
(alçak süpürme + boğuk ejder hırıltısı), `sanat_kut` (tok vuruş + yerden sekme), `sanat_tengri` (içe çeken dönen bant +
yükselen uğultu), `sanat_vus` (dışa patlayan hava, gök çatırtısı), `sanat_yarik` (kaya vuruşu), `sanat_cat` (taş
yarılması + ilerleyip azalan kırılmalar), `sanat_akin` (beş kiriş tıngısı), `sanat_viz` (derin kiriş + inen perdeli
ıslık), `sanat_tam` (tahta tok + iki notalı çan). `python v27_sanat.py <adlar>` yalnız onları üretir.

### Test

* `-- --sanat --boss --muhur=0` (`tools/tests/sanat_testi.gd`): 13 sanatın hepsi genel denetimden geçer (bedel,
  bekleme, isabet, hasar, süre; kombo sanatı ≤ 150 kare); ek olarak her yeni sanat için **kombo testi**: 3 sıradan +
  1 seçkin, açık alanda halka kapanırken T (TAM beklenir) ve ızgaraya geçici tavan konan alçak alanda erken basış
  (kaçması beklenir): kilitlenen = 3 (Akıncı: çivilenen ≥ 2), her sıradanın kalkışı eşik üstünde ve ≥ 6 kare kilitli,
  seçkin ≤ 10 px (kalkmaz), bitiriş var, sonunda üçü de yerde, duvar / tavan içinde değil, kilit kalmamış, tavanı aşan
  kare yok (düşman ve oyuncu). Gerçek duvar kenarında Tengri Çarkı (duvar sekmesi ≥ 1) ve arkası duvar olan düşmana
  Kurt Dansı (oyuncu duvara girmez). Sınıf tablosuna yeni denetimler.
* Sonuç: açık alanda kalkış Kurt Dansı 77-89 px, Evren Kuyruğu 98-102 (H 92), Tengri Çarkı 64-77 (dönme 30), Yer
  Yarığı 70-75 (H 70); alçak tavanda 43-66 px, tavan_üstü 0, oyuncu_tavan 0; seçkin kalkışı 0-2 px; yerde 3/3, kötü
  konum 0; ritim TAM 5/5, erken basış 0/5; duvar sekmesi 2, oyuncu duvarda değil; SONUC GECTI hata=0, TAKILMA=0.
* Kare şeritleri (her kare, 3 sıradan + 1 seçkin, ritim TAM; kırpma arenaya sabit):
  `--fixed-fps 60 -- --sanat --boss --pencere=1920x1080 --sanat_kare=<klasör> --sanat_tek=<id>`. Efekt önizlemesi
  `--sanat_fx=<klasör>` yeni bileşimleri (kurt_adim, kurt_patla, evren_*, tengri_patla, yarik_*, akin_birak, damgalar,
  girdap / ritim / delen) de çeker.
* Görseller (`docs/v31/sanat/`): `kurt_dansi_dizi.jpg`, `evren_kuyrugu_dizi.jpg`, `tengri_carki_dizi.jpg`,
  `yer_yarigi_dizi.jpg`, `akinci_akini_dizi.jpg` (her 3. kare), `yansima_sozcukleri.png` (atlas önizlemesi), `sanat_ekrani.jpg`
  (13 sanatlık kayan liste, Yer Yarığı kartı).
* Gerileme: `--dovus --boss --kontrol` KONTROL basış=272 savuruş=134 basılmamış=0, TAKILMA=0; `--zeka --muhur=0` BITTI;
  `--otomatik --derinlik=1` ve `--derinlik=5 --muhur=0`, `--mekanik --muhur=0` (BITTI): betik hatası 0; `--piksel_tara` TOPLAM 0.

## v31: profesyonel silah mürekkebi

Geri bildirim: "Silahların, okların ve diğer silahların animasyonu ve MÜREKKEBİ çok, çok, ÇOK daha profesyonel olmalı."

### Referanslar ve hedefler

İncelenen yön: Shinobi: Art of Vengeance (cel + mürekkep kesik), Dead Cells (perspektif hilali, 1-2 karelik doruk), Hades
(kalın kontur + parlak çekirdekli kesik, kısa ömür), Hollow Knight (iğne gibi tek karelik darbe parlaması), Ghost of
Tsushima / Sekiro sumi-e efektleri (kuru fırça, "uçan ak"), Ōkami (kalın-ince hat fırçası), gerçek zamanlı VFX
anlatımları (realtimevfx.com "Sword Slash help": aynı renkte farklı doygunlukta 3-4 katman, eğriyle incelen kısa ömürlü
şerit; itch.io "Slash shape fundamentals": kesik animasyonun doruğu, 1-2 kare, hilal, kuyruk başa göre ince). Somut
hedefler:

1. Kesik = katmanlar: bıçak ağzında kıl inceliğinde ak-sıcak hat · hemen içinde parlak çekirdek · paletin renginde
   kıl damarlı gövde · iç yarıda sumi siyahı kıl çizgileri · iç kenarda kıl uçlarına ayrılan kuru fırça · ardında daha
   uzun yaşayan gri sulu yıkama (duman).
2. Yumuşak "hava fırçası" geçişi yok: renk basamakları cel gibi keskin, basamak sınırları kıl kimliğiyle pürüzlü.
3. Zaman: 1-2. kare ak-sıcak, 3-4. kare renkli, sonra mürekkebe kuruyup kıl tellerine kopar (v22 ömürleri aynı).
4. Uç ve kuyruk: baş bıçağın hemen arkasında dolgun, sivri / kıvrık uç; kuyruk kuru kıllara ayrılır.
5. Darbe: tek karelik iğne parlaması + türüne göre imza + vuruş yönünde fırça sıçrantısı; boylar ölçülü (v22).
6. Uzak: ok izi iğne gibi ince, başta basınç, uçta parıltı; şimşek hat fırçası gibi kalın-ince; ışın, zincir ve
   dönen fırlatmalar dokusuz düz çizgi değil fırça hattı.

### Hilal fırçası (`shaders/ink_brush.gdshader` "v31", `scripts/core/InkTrail.gd` `_draw31`)

* **Yeni doku** `assets/fx/ink/silah_firca.png` (1024x512 + HD x2 WebP; `tools/artgen/silah_fx_ink.py`): 8 satır
  İKİ YANLI hilal fırçası — v = 1 bıçak ağzı keskin ve dolu, v = 0 iç kenar kıl uçlarına ayrılır, kuyrukta (u → 1) kıllar
  kimlik sırasıyla kopar. R yük, G sumi (iç yarıda kıl çizgileri + baş havuzu), B kıl kimliği, A kâğıt tanesi.
  Satırlar: 0 kılıç, 1 hançer, 2 ağır (kalın kuru, yarılan), 3 mızrak, 4 kırbaç (kurdele), 5 uzun sap, 6 yıkama, 7 hız
  telleri. Sanat fırçası (`sanat_firca.png`, v28) aynı kodlamanın hilal için yeniden tasarımı.
* **Köşe verisi:** oyuncu izinde UV.x = u (0 bıçağın taze ucu .. 1 kuyruk) + 2 x satır (eski dünya uzunluğu yerine:
  doku darbe boyunca bir kez gerilir, baş ıslak, kuyruk kuru). Düşman / boss yayları (`auto_arc`) ve izsiz unsur
  efektleri (`burst`) eski yolda (v31 kapalı).
* **Gölgelendirici katmanları** (dıştan içe, taze → yaşlı): ak-sıcak bıçak ağzı hattı (HDR) → ak-sıcak çekirdek
  basamağı → turuncu kenar tonu basamağı → gövde (iç kenarda çekirdek tonu, bıçağa doğru paletin gövdesi, kıl
  damarlı) → iç yarıda sumi kıl çizgileri + iç kenarda koyu birikim. Basamaklar `fwidth` ile kenar yumuşatmalı ama
  keskin, sınırları kıl kimliği ve kâğıt tanesiyle pürüzlü. Tazelik kare cinsinden (`lead`: ~2 kare, `fresh`: ~4 kare);
  yaşlanınca renk koyu mürekkebe kurur, eşik kıl kimliği sırasıyla yükselir (kıl telleri kalır), kâğıt tanesi örtüyü
  hafifçe kırar. Dış ışıma çok ince ve yalnız en taze karede.
* **Arka yıkama** (katman 1, satır 6): hilalin kabza yanına kayık ve savuruşun gerisinde kalan, hafifçe yükselen yansız
  gri-siyah sulu mürekkep; ömrü hilalin 1,9 katı (`WASH_K`), örtüsü 0,24-0,34. Ağırda ayrıca koyu kuru sürüntü
  (satır 2).
* **Hız telleri** (katman 5, satır 7): hilalin dışında, bıçak ağzının hemen ötesinde kıl inceliğinde kuru çizgiler.
* **Yay sonu fiskeleri** (`_flick31`): iz bitince bıçak ucundan savuruş yönünde fırlayan damlalar (önde iri, yarısı
  sumi, yarısı palet). Hilal boyunca serpilen damlalar seyreldi (×0,5; ağır ×0,3).
* **Katlanma düzeltmesi:** bıçak ucu yerinde dönüyorsa (yere değip `_ground_clamp` ile yaslanan bıçak) örnek alınmaz;
  hilal ucun çevresinde yelpaze gibi katlanıp düz kenarlı "bayrak" çizmiyor. Bıçak yönü ucun yol aldığından hızlı dönüyorsa
  (bilekten / yere yaslanarak) o örneklerde hilal eni "ucun yolu / dönüş açısı" ile sınırlanır: iç kenar geriye
  süpürülüp sivri bir "gaga" çizmiyor (Ulu Kılıç, Dağ Çekici yere inişi). Ağırda kanca kapalı, sıcak basamaklar bıçak
  ağzına sıkışık (`band_in` 0,76 / `core_in` 0,93): geniş hilal ak bir levhaya dönmüyor.

| Aile | İmza |
|---|---|
| Kılıç | temiz hat hilali, yıkama, tek hız teli, 3 fiske |
| Hançer | ince hızlı ikiz fiske (içte ikinci ince hilal), yıkamasız, 2 fiske, ağız hattı daha parlak |
| Ağır | kalın kuru yarılan fırça + koyu sürüntü + yıkama, 7 fiske + v20 uç sıçrantısı, dar sıcak bant |
| Mızrak | uzun basılı darbe; saplamada (yol izi) yolun iki yanında iki hız teli + bitince uçta yandan görülen ince halka çifti ve iğne parıltısı (`_ring31`) |
| Kırbaç | kurdele satırı (iki kenar düzgün), kıvrılan hat |
| Uzun sap | geniş sulu süpürme, içte soluk yıkama yayı, tel |

Unsur katmanları (v20 / v25) aynen üstte: od hilali kendi alev dalında (satır dokusu kıl verisi olarak), Yer-Su yaprak
damarları v31 hilalinde de, ayaz / yıldırım / kam zerreleri ve tayfsı ard görüntü aynı çizim çağrısında.

### Vuruş mürekkebi (`scripts/core/InkFX.gd`, yeni atlas `assets/fx/ink/silah_fx.png`)

17 şekil (aynı veri kodlaması: R işaretli uzaklık, G koyu / sıcak, B çizim sırası, A erime): yönlü fırça sıçrantısı
(kökte sumi göl, öne fırlayan basılı fırça dili + yan diller + koni içinde uzamış damlalar), küt ezik leke, damla
konisi, iğne kesik + yarık kesik, tek karelik darbe parlaması, ikiz fiske, kritik mührü (hanko: pürüzlü kare, oyulmuş
tamga), ince kuru halka, kıvrık fiske, sulu buğu, küçük sumi patlaması, ok ucu parıltısı, yay bırakışı yelpazesi.

* `InkFX.hit`: her vuruş üç parça — tek karelik iğne parlaması (uzun ekseni savuruş yönünde, boyu en çok 24 birim
  tabanla sınırlı) · türün imzası (kesik: iğne / yarık kesik; küt: ezik leke + ince halka; saplama: yarık kesik + yandan
  görülen saplama halkası; hançer: ikiz fiske; büyü: ince halka + sumi patlaması) · vuruş yönünde fırça sıçrantısı;
  kademe 2'de damla konisi. Eski yıldız patlamaları (çizgi roman ışınları) yok.
* `InkFX.stamp` (kritik): büyük parlama + yarık kesik + sıçrantı + vermilyon mühür (ayrı düğüm, palet 0, biraz gecikip
  daha uzun kalır). `InkFX.kill`: ezik sumi lekesi + iki yana damla konisi.
* Oyuncu vuruşundaki kıvılcım kıymıkları yarıya indi (parlama ve sıçrantı vuruşu taşıyor). Soluk gök mavisi renkler
  (şimşek) artık kızıl paletine düşmüyor (`pal_from_color` → 5).

### Uzak silahlar

* **Ok izi** (`OkIz.gd`, `ok_iz.gdshader`): başın hemen arkasında basınç şişkinliği, güçlü atışta (tam gerilme / unsur)
  izin iki yanında kuyruğa doğru açılan kıl inceliğinde hava telleri, ok ve cirit ucunda titreşen küçük iğne yıldızı
  (unsur renginde; unsursuzda soluk çelik). Tek çizim çağrısı korunur.
* **Yay**: kiriş gerildikçe incelir ve ışır, gezde mürekkep düğümü, gerginlikte iki yanda titreşen soluk gerilim telleri
  (`BowString.pull`). Bırakış: tek karelik iğne parlaması + ince kesik + soluk kısa fırça teli yelpazesi (eski altın
  sıçrantı lekesi yerine). Dolma parıltısı: altın iğne yıldızı + ince halka. Duvara saplanma: parlama + küçük sumi
  patlaması + geri yöne damlalar.
* **Gök Asası şimşeği** (`LightningFX.gd`, `SilahCizim`): kanal yassı uçlu hat kalemi gibi kalın-ince (kırık yönüne
  göre), baş basılı, uç kıl inceliğinde; altta normal karışımlı koyu lacivert sumi hattı (ışığın iki yanından kontur
  gibi taşar, ışık söndükten sonra 0,16 sn kuru iz olarak erir), üstte toplamalı yıkama + mavi gövde + ak kılcal
  çekirdek. Gök gürlemesi aynı sınıfı kullanır.
* **Kam Küzgüsü ışını** (`Silah27._beam31`): aynadan basılarak çıkan fırça hattı (sumi kontur, ışın boyunca akan enerji
  nabızları, çevresine sarılan iki ince güneş teli, ak çekirdek), uçta dönen kısa yanma dilleri.
* **Tengri Bağı** (`Silah27._chain31`): gerçek zincir — halkalar sırayla yüzden (elips) ve yandan (çubuk), mürekkep
  kontur + gök mavisi + ak parıltı, içinden ince ak şimşek kılı; bağlının çevresinde hat fırçası ensō'su.
* **Dönen fırlatmalar** (`Projectile._spin_smear`): balta, sapan ve mancınık taşının arkasında dönüşün ardında kalan iki
  karşılıklı mürekkep hilali (hareket bulanıklığı yerine). Cirit ve Tatar oku yeni ok izini kullanır.
* `scripts/core/SilahCizim.gd` (yeni): dokusuz, köşe renkli, kenarı yarım piksel yumuşatılmış değişken genişlikli şerit
  (`serit`), hat kalemi profili (`kalem`), yay noktaları.

### Kalabalık sahne: çok düşmanlı büyük vuruşlar (lider notu)

Geri bildirim: savaş sanatları, kombo bitirişleri ve çevre hasarında beyaz darbe karesi, düşman vurulma flaşları,
hasar sayıları ve mürekkep sıçrantıları üst üste biniyordu. Genel FX katmanında çözüldü (sanat kodu dokunulmadı):

* **Ortak darbe karesi** (`ImpactFrame.play`): açık bir kare varken 0,15 sn içinde gelen istekler yeni kare açmaz,
  hedeflerini açık karenin silüetlerine ekler (en çok 6 silüet; 4. silüetten sonra karartma 0,42'ye hafifler); zorunlu
  kare (seçkin / boss ölümü, infaz) bir kareden sonraki 0,6 sn içinde açılmaz. Olağan 1,2 sn bekleme aynen.
* **Paylaşılan vurulma flaşı** (`SpriteAnim.set_flash`): aynı 0,15 sn içinde başlayan flaşlar sırayla ×1 / ×0,7 / ×0,5 /
  ×0,35 (v22'nin tek düşmandaki art arda sönümünün üstüne): çok düşman bembeyaz silüet yığınına dönmüyor.
* **Hasar sayıları** (`FX._ink_number`): v22 birleştirmesi (aynı düşman, 0,3 sn, kritik olmayan) aynen; yeni olarak
  her sayının doğuş yeri canlı sayılara (0,45 sn) çok yakınsa yukarı ve dönüşümlü yana kaydırılır (en çok 4 basamak):
  yan yana düşmanların ve kritik + sıradan sayıların rakamları üst üste binmiyor. `FX.text`'in v27 tekrar / kaydırma
  mantığı ayrı yol olarak aynen.
* **Sıçrantı bütçesi** (`InkFX._kalabalik`, gerçek zaman): 0,1 sn içinde ilk 2 vuruş tam sıçrantı; 3-5. en hafif
  kademe ve ×0,75 boy; sonrakiler yalnızca küçük tek karelik parlama. Kritik damgası pencerede 3.'den sonra yalnızca
  parlama + kesik (sıçrantı ve mühür yok). Vitrin ızgarası bütçeyi `InkFX.butce = false` ile kapatır.
* **Darbe karesi silüetleri:** ilk iki silüet (vuran + asıl hedef) bembeyaz, sonrakiler yarı beyaz (`flash` 0,5).

Ölçüm (beyaz = en koyu kanalı 0,86'dan açık piksel, kızıl = doygun kızıl mürekkep; arayüz kenarları dışarıda):

| Sahne | beyaz ort / en çok | kızıl ort |
|---|---|---|
| `--sanat --boss --muhur=0 --sanat_kare` (586 kare) önce | %1,22 / %19,8 | %1,29 |
| sonra | %1,13 / %16,6 | %1,59 (v31 sanat izleri renkli hilal) |
| `--dovus --boss --klip22` (36 kare, 3 düşman) önce | %0,14 / %0,44 | %0,45 |
| sonra | %0,13 / %0,55 | %0,39 |

Sanat çekiminde en beyaz kareler Bir Çekiş / Demir Duruş karşılığı / Göğe Yükseliş darbe kareleri: 3. ve sonraki
silüetler artık gri (`docs/v31/kalabalik.jpg`). Sayı yığınları (Kasırga'da "9 9 9 10" iç içe) kaydırılarak okunur.

### Silah sprite'ları

Silah atlası zaten HD x2 (`assets_hd/x2/weapons`) ve kenar yumuşatmalı gölgelendiriciyle çiziliyor; 2560x1440 `--doku=2`
çekimlerinde keskin. Hızlı dönüşte v27 leke kareleri (iki soluk kopya) yerinde; ek leke karesi eklenmedi.

### Ölçüm ve test

* Başarım (`--unsur --boss --unsur_yalniz --unsur_cekim=olcum`, 2560x1440, `--doku=2`; GPU bu makinede ~33 ms dikey
  eşitlemeye bağlı): 

  | | GPU (ms) | CPU iz + zerre (ms) |
  |---|---|---|
  | önce (v30), 12 silah × unsur | 32,6-33,7 | 0,69-0,90 |
  | sonra (v31) | 32,2-33,2 | 0,63-0,84 |

  Fark ölçüm gürültüsünün içinde (GPU dikey eşitlemeye bağlı; CPU tarafında hilal katmanları tek çizim çağrısında,
  ek yük ölçülemeyecek kadar küçük). Yeni şerit / ışın / zincir çizimleri tek `canvas_item_add_triangle_array`.
* Kare şeritleri: `--fixed-fps 60 -- --firca=<silahlar> --firca_kombo --anlik=<klasör>` (yeni: her kare için
  `[firca] iz <silah> <kare> <örnek>` satırı: kontak sayfası izli kareleri seçer); `--firca_uzak`; vuruş ızgarası
  `--fx_vitrin=<klasör>` (yeni D paneli: 9 vuruş türü x 4 palet, 1. / 3. / 9. kare); `--silah27 --boss
  --silah27_goruntu=<klasör>`.
* Gerileme: `--dovus --boss` TAKILMA=0, KONTROL basılmamış=0 oto_dönüş=0 oto_hamle=0 istenmeyen_ağır=0; `--dovus --boss
  --kontrol` aynı; `--yay --boss` TAKILMA=0 CEPHANE_HATA=0; `--unsur --boss` HATA=0; `--tomar --boss` GECTI; `--sanat
  --boss --muhur=0` SONUC GECTI hata=0 TAKILMA=0; `--silah27 --boss` SONUC GECTI HATA=0; `--otomatik --derinlik=1
  --muhur=0`, `--mekanik --muhur=0` (BITTI): betik hatası 0; `--piksel_tara` TOPLAM 0. Bütün koşularda SCRIPT ERROR 0.
  Eski olduğu bilinen motor uyarıları aynen: `SanatUI._nisan_pips` "Invalid polygon data" (HUD), çıkışta sızıntı
  uyarıları, `--tomar` sırasında bir kez "Lambda capture ... freed". `InkAksanFX` bitiriş fırçasında iki noktadan kısa
  yolda `draw_polyline` hatası (`--dovus` 116 kez) giderildi.

### Görseller (`docs/v31/`)

* `aile_kilic.jpg`, `aile_hancer.jpg`, `aile_agir.jpg`, `aile_mizrak.jpg`, `aile_kirbac.jpg`, `aile_uzun.jpg`,
  `aile_unsur_palet.jpg`: her aile önce (v30) / sonra (v31), izin göründüğü art arda 7 kare (1080p, kırpık)
* `hd_1440.jpg`: 2560x1440 `--doku=2`, 1:1 kırpık (Alp Kılıcı, Dağ Çekici)
* `uzak_yay_firlatma.jpg`: yay bırakışı, ok izi, cirit, sapan, mancınık, Gök Asası şimşeği önce / sonra
* `silah27_uzak.jpg`: Kam Küzgüsü ışını, Tengri Bağı zinciri, Tatar Yayı önce / sonra
* `vurus_izgarasi.jpg`: 9 vuruş türü × 4 palet, 1. / 3. / ~9. kare önce / sonra
* `kalabalik.jpg`: çok düşmanlı sanat ve klip22 sahneleri önce / sonra
* `dokular.jpg`: yeni atlas ve hilal fırçası (kızıl önizleme)

### Bilinen

* Hilal dokusu u boyunca darbe başına bir kez gerildiğinden iz büyürken kıl çizgileri boyuna çok az kayar (2-4 karelik
  ömürde seçilmiyor).
* Kesik / kırbaç yol izinde "bıçak ağzı" yolun bir yanında (enine payın %77'si): parlak hat iz çizgisinin hemen önünde.
* Ağır silahın yere inen ucunda hilal ucu yerde fırça kuyruğu gibi kıvrılır (katlanma yok ama düz bir yer sürüntüsü).
* `hd_paket.py --kontrol` yeni iki doku için de diğer fx veri dokuları gibi UYARI (gürültü kanalları HD'de ince
  ayrıntı kazanıyor); manifest md5 güncel.
* `SanatUI._nisan_pips` "Invalid polygon data" hatası (HUD, bu işten önce de var; paralel sanat dalının alanı).

## v32: Konak ve silah ustası

İstek: "Bölümün sonuna bir NPC koyalım; derinlikler arasında yurda dönmeyelim, aşağı inip yurda dönmek mantıksız. Ya da
NPC'ler temamıza uyup bize gelsin. Eklediğimiz NPC parayla (altın), RNG ile silahlarımıza ek özellik kazandırsın."

### Akış: önce / sonra (`Main.gd`, `Game.gd`)

Önce: koşu doğrudan 1. derinlikte başlıyordu; her Kut Kapısı (ve boss) **Ulu Kayın yurduna** döndürüyor, yurttaki kapı
derine indiriyordu (`Main._on_finished` → `_build_hub`, `Game.next_depth` yurt kapısında). Yani her derinlikte Ötüken'den
Ulu Kayın'a çıkılıp yeniden iniliyordu.

Şimdi:

* **Koşu yurtta başlar** (`_new_run` → `_build_hub`; test / çekim bayraklarıyla eskisi gibi doğrudan bölüm: `TEST_BAYRAKLARI`).
  Umay Ana (Kut bankası, kalıcı armağanlar), Demirci (parşömen), Alp Ata (sanat), Ozan (ad töreni) yurtta kalır; kapı
  1. derinliğe indirir (derinlik artmaz). Ölümden sonra da yurt (`_after_intro`: bekleyen parşömen varsa hatırlatır).
* **Kut Kapısı → Konak → sıradaki derinlik** (`_to_konak`): kapıdan geçince `Game.next_depth` (derinlik +1, can +%15
  `Zorluk.derinlik_sifa`, şişeler dolar) ve bir sonraki derinliğin **biyomunda** gezgin konak kurulur (`Level.build_konak`);
  konağın sağındaki Kut Kapısı o derinliğin bölümünü kurar. Lütuflar konakta söner (eskiden yurda dönünce).
* **Boss derinlikleri**: bölüm → boss arenası (boss öncesi Bezirgân bölümde kesin, v24) → **bosstan sonra konak** → derinlik.
* `--otomatik` botu da konaktan geçer (kapı → konak → Usta'da paranın yettiği ilk hizmet → kapı); `BOLUM_SONU` satırı kapıda
  yazılır, `[otomatik] USTA ...` satırı hizmeti söyler. `--sahne` için eski "done" ekranı kaldı.

### Konak (`Level.build_konak`, `data/konak.json`)

64 karolu düz, düşmansız alan; biyomun paralaksı, karoları ve ışığı (ambient konak.json'dan hafif sıcak). Soldan sağa taş
yol, biyoma göre süsler (Ötüken: çadır, kazan, fener, at, balbal · Bozkır: çadır, tuğlar, at · Çini Saray / Şahmeran:
mağarada çadır kurulmaz; kandil, kilim sergisi, kazan, balbal · Kaf: çadır, mangal, kandil · Tamu: balballar, tuğ, kazan),
ortada **Umay Ocağı** (konak ateşi, `konak_ates_v2`): yanından geçince taşınan Kut Umay'ın bankasına geçer (yurttaki Umay
Ana gibi; `Level._konak_tick`), sonra **Bengisu Usta'nın tezgâhı** (`usta_tezgah_v2`: kütükte örs, kor mangalı, alet
dürüsü, asılı muskalar) ve kendisi, 47. karoda **Bezirgân Sartak** (yalnızca bir önceki bölümde pazar çıkmadıysa:
`Game.run.bezirgan_gordu`; böylece her derinlikte bir pazar şansı olur, boss öncesi pazar vardıysa bosstan sonraki konakta
yok), 58. karoda Kut Kapısı. Müzik "yurt" (sakin). Afiş: "KONAK · <biyom>", sağ üst "Konak · <biyom>". İlk konakta
öğretici kartı ("konak"). NPC'ler "seninle yol alır": Usta'nın ekran sözü ve yakınken başının üstündeki kısa sözü,
Sartak'ın pazar sözü **biyoma göre** (`usta.json` "sozler").

Kut harcaması (Umay armağanları, parşömen açma, sanat öğrenme) bilerek yurtta bırakıldı: Dead Cells'teki gibi hücreler
seviyeler arasında bankaya girer, kalıcı güç koşu başında alınır; koşu ortasında kalıcı güç sıçraması olmaz, konak altına
(Usta, Sartak) odaklanır.

### Bengisu Usta (`scripts/core/Usta.gd`, `data/usta.json`, `HUD._draw_usta`, `Main._usta_*`)

"Bengi su" ölümsüzlük suyudur; Bengisu, Demirci Kam Kuzgun'un kızıdır: babası yurtta ocağında döver, o kervanla yol alır,
alpların silahına yolda nakış vurur. Görünüş (`tools/artgen/usta_ink.py`, mürekkep-cel, texel 4, `npc_usta_v2` idle 6 /
talk 4): bakır kızılı tek örgü (demir halkalı), alın bandında firuze boncuk, yeşil kısa kaftan (firuze-altın kenar), is
lekeli deri önlük (göğüste üç nakış kalemi), kızıl kuşak, sıvalı kollar ve deri bilek koruyucu; ön elinde ucu Kut ışığıyla
ışıyan nakış kalemi (idle'da ucu nefes alır), arka elde küçük çekiç omuzda. Konuşurken kalemi öne uzatır ("göster
bakalım"). HD x2: `assets_hd/x2/sprites/npc_usta_v2.webp`, `decor/konak_ates_v2.webp`, `decor/usta_tezgah_v2.webp`
(denetim TAMAM, ort fark 0,0005 / 0,0015 / 0,0018; manifest). Üretim: `python export_ink.py --usta`, `python
export_sus.py --usta` (HD: `KY_HD=2` ile, sonra `hd_paket.py --paketle`). Sesler `tools/audiogen/v32_usta.py`: `usta_nakis`
(kalem tinkleri + Kut çanı), `usta_damga` (ıslak mürekkep şaplağı), `usta_dovme` (küçük örste iki çekiç + kor).

Hizmetler **altınla**, zar konak tohumuyla (`Usta.rng`; `--otomatik` / `--tohum=` ile belirlenimci), yalnızca silahlara
(yakın / uzak yuva). Fiyat = taban x `Pazar.derinlik_k` (1 + 0,3 x (derinlik - 1); konak sıradaki derinliğin konağıdır)
x nadirlik_k (Sıradan 1 · Nadir 1,15 · Destansı 1,3 · Efsanevi 1,5), 5'e yuvarlanır:

| hizmet | ne yapar | taban | şans / kural |
|---|---|---|---|
| **Nakış** | 3 aday ek özellik yuvarlanır (değerleriyle), biri seçilip işlenir | 45 (nadir ★ x1,5) | yuva = nadirliğin ek özellik sayısı + 1 (+1 gök demiri); nadir nakışlar (Keskin, Ölümcül, Zincirleme, Gürleyen, Yaralı Kurt, Korunaklı, Aç, Çevik) 0,5 ağırlıkla; adaylar konak başına bir kez yuvarlanır |
| **Yeniden dövme** | bütün ek özelliklerin değerleri yeniden yuvarlanır (kimlikler kalır) | 25 | aynı silahta her dövme +%50 pahalı (`it.usta_dovme`) |
| **Unsur aşılama** | Od / Ayaz / Yıldırım / Kam / Yer-Su; eskisi silinir | 40 rastgele, x1,75 seçerek | unsur gücü nadirliğe göre (`Unsur.POWER` x 0,92-1,08) |
| **Kalite** | +5..15 kalite puanı; hasar puan başına x1,003 (100 puan = 0,85 → 1,15 yuvarlama aralığı) | 30 | şans = 0,9 - 0,7 x kalite / 100 (en az 0,2), ekranda görünür; tutmazsa altın gider |
| **Kut Mührü** | kumar | 15 | nakış %20 · kalite +8 %22 · unsur %14 · kusur silme %10 · **kusur %20** · hiç %14 (uygulanamayan sonuç bir sonrakine kayar) |

2. derinliğin konağında (k = 1,3) Nadir silahta: nakış 70 (nadir 100), dövme 35, unsur 60 / 105, kalite 45, mühür 20.
v24 ölçümüne göre 1. derinliği temizleyen oyuncu ~80-110 altın toplar: biriktiren oyuncu her konakta 1-2 hizmet alır,
Sartak'la (bölümlerin ~%80'inde) paylaşır. Altın ölünce yittiği için harcamak teşvik edilir.

Ekran (mürekkep arayüzü, `HUD._draw_usta`): başlıkta Bengisu'nun biyoma göre sözü, altın; adım izi (silah → hizmet →
seçim → sonuç); solda liste (silahta SnH, nakış n/yuva, kalite; hizmette fiyat ve şans %; seçimde aday / unsur), sağda
silahın tam kartı. Doğrudan hizmetlerde (dövme / kalite / mühür) Boşluk önce onay sorar. Sonuçta sağda **yeni kart
eskisiyle karşılaştırmalı** (SnH ▲ / ▼, `ItemGen.dps_oyuncu`), solda ne değişti (SnH, kalite, nakış sayısı, unsur,
kalan altın) ve kartın üstüne **basılan mürekkep damgası** (NAKIŞLANDI / DÖVÜLDÜ / AŞILANDI / KALİTE +N / MÜHÜRLENDİ;
tutmayanda soluk TUTMADI, kusurda mor LANETLENDİ): 2,2 kattan küçülerek iner, basılınca sıçrantı; ses + kıvılcım + Usta'nın
konuşma animasyonu. Esc bir adım geri, Boşluk sonuçtan sonra aynı silahla hizmet listesine döner.

### ItemGen kancaları

`affix_pool(base, cat)` (roll ile aynı süzgeç), `max_affix(it)`, `roll_affix(def, rng)`, `reroll_affixes(it, rng)`;
`_roll_range` isteğe bağlı zar alır (Usta konak zarıyla yuvarlar, düşüşler eskisi gibi `ItemGen.rng`).

### Test

* `-- --konak` (`tools/tests/konak_testi.gd`, `SONUC GECTI|KALDI`): AKIS (kapı → konak: yurt değil, derinlik 2, can %15,
  şişeler, lütuf söndü, biyom, Usta / ocak / Bezirgân kuralı, düşman yok), OCAK (Kut bankaya), USTA (ekran oyunun yolundan
  açılır; aynı tohum aynı 3 aday, aday fiyatı nadirlikle; nakış onay + işleme, altın tam düşer, kartın SnH farkı =
  `ItemGen.dps_oyuncu`, yuva sınırına dek nakış sonra ret; dövme değerleri değiştirir / kimlikleri korur / pahalanır; unsur
  rastgele ve seçilen; kalite 8 deneme: +5..15 ya da değişmez, altın hep düşer, şans sınırları; Kut Mührü 6 kez; yetmeyen
  altın reddi; ayrılış), KAPI (konak → 2. derinlik bölümü), BOSS (2. derinlik → arena → boss ölünce kapı → konak derinlik
  3, boss öncesi pazar → konakta Bezirgân yok → 3. derinlik), YURT (yurt kapısı → 1. derinlik, derinlik artmaz). Kalıcı
  kayıt geri yüklenir.
* Çekim: `--konak_ekran=dunya | usta | sonuc` (`--konak_derinlik=N`, `--goruntu`, `--bekle`). Görseller `docs/v32/konak/`.
* `--otomatik --derinlik=N`: `[konak] derinlik= biyom= tohum= bezirgan=` ve `[otomatik] USTA ...`.

## v32: özgün savaş sanatları

İstek: "Savaş sanatlarından 2-3'ü Göğe Yükseliş'e çok benziyor; daha özgün olabilirler. Yay olanı (Akıncı Akını) ve
kurt olanı (Kurt Dansı) beğendim; daha çok onlar gibi olsun." Dürüst bakış: v31'in **Evren Kuyruğu** (alçak süpürme →
sarmalla kaldır → tepeden çak), **Yer Yarığı** (yerden sektir → havada X → dikine çak) ve **Tengri Çarkı** (girdaba çek →
havada 4 vuruş → savur) üçü de Göğe Yükseliş'in "sıradanları havada kilitle, vur, bitirişte yere / duvara çak" iskeletinin
çeşitlemesiydi; yalnız giriş ve bitiriş süsü değişiyordu. Üçü kaldırıldı; yerlerine (aynı kilit yuvası, bedel, sınıf ve
palet) birbirinden ve kalan on sanattan **mekanik olarak** ayrı üç sanat geldi: kavra-savur-fırlat (düşman silah olur),
tuzak-ağ-çöküş (bölge ve işaret), ritim-dörtnal (dört zamanlı basış ve biniş). Kurt Dansı / Akıncı Akını'nın ruhu korundu:
okunur dizi, işaretleme ve patlama, ustalık basışı, seçkine özel kural. Göğe Yükseliş, Kurt Dansı, Akıncı Akını ve eski
yedi sanat aynen. Kod: `scripts/actors/SavasSanati.gd` ("v32" bölümleri), `scripts/core/SanatFX.gd` (yeni kipler `ag`,
`davul`; bileşimler), veri `data/sanatlar.json`, arayüz `scripts/ui/SanatUI.gd`.

Eski kayıtlar: `meta.sanat_acik` / `meta.sanat_secili` içindeki `evren_kuyrugu` → `pehlivan_savurmasi`, `tengri_carki` →
`yildirim_agi`, `yer_yarigi` → `tulpar_dortnali` (`SavasSanati._gocur`, ilk okumada; kayıt yeniden yazılır).

### Sanatlar

Hasar = kuşanılan silahın hasarı × çarpan (`Player._deal`; tomar, kritik, unsur aynen). Boss çarpanı `boss_k` 0,6. Hepsi
2 nişan, 7 sn bekleme, süper zırhlı; Ritim penceresi v31 ile aynı (−0,13 / +0,08 sn; halka görünürken erken basış şansı
yakar).

| Sanat | Dizi | Seçkin / boss / ağır | Ritim (TAM ×1,35) | Hasar (tek sıradan düşmana) | Sınıflar | Alp Ata |
|---|---|---|---|---|---|---|
| **Pehlivan Savurması** (yeşim, 15) «Kırkpınar'ın tutuşu» | 0,14 sn peşrev (çömelip kollar açılır) → 0,1 sn öne atılış: öndeki en yakın **sıradan** düşman (90 px + R×0,3) belinden **kavranır** (kilit), kutudaki diğerleri omuz darbesi → 0,52 sn **çekiç savurması**: tutulan gövde oyuncunun çevresinde eğik elipste (önde belde, tepede baş üstünde, arkada belde, altta yere yakın) 1,75 tur döner, hızlanır; **savrulan gövde çarptığı herkesi biçer** (yarım turda bir), kendisi her tam turda tutuş hasarı alır → **fırlatış**: 430 px/sn ileri, hafif yukarı (22 px) uçar (kendi fırlatma kaydı `_firlatilan`: sanat bittikten sonra da sürer), yolundaki düşmanları **devirir** (sıradanlar havaya), duvara ya da yere çakılır: **"PAT!"** (duvarda `Enemy._wall_slam` de). Kimse tutulamazsa silah tek başına savrulur, bitirişte ağır iniş | tutulmaz ("tutulmaz"): omuz darbesi ×0,5 + sendeleme; savrulan / fırlatılan gövde çarpınca hasar alır, savrulmaz | fırlatış anında: hız ×1,2, kalkış 30 px, çakılma ve devirme ×1,35 | tutuş ×0,5 + tur ×0,3 + çakılma ×1,3 (tutulana); savrulan ×0,55 / yarım tur, devirme ×1,1 (diğerlerine) | mızrak, uzun sap, ağır, dev | 70 Kut |
| **Yıldırım Ağı** (gök, 16) «Gök Tanrı'nın kazıkları» | 0,14 sn avuca toplanan çıtırtı → 3 × 0,09 sn **kazık** fırlatışı: en yakın (öndeki öncelikli, 240 px) **sıradan** düşmanlara saplanır (×0,35, işaret); boşta kalan kazık önde 62 / 134 / 206 px'te yere çakılır (önü kapalıysa arkaya) → 0,5 sn **şimşek ağı**: bıçağın ucu ve kazıklar arasında gerilir (üçgen + uçtan ışınlar); içindekiler (çokgenin içi ya da kenara gövde payı + 10 px) **yavaşlar** (hız ×0,45 / kare), her 0,16 sn cızırtı ×0,12, ağa giren sıradan işaretlenir; oyuncu yerinden kımıldamaz → **çöküş "ÇAK!"**: her kenar boyunca kalın şimşek, işaretli ve ağdaki herkese zincir ×0,8; sıradanlar kilitlenip 0,13 sn'de **yerde kayarak** oyuncunun önüne çekilir (15 px aralıklı) → **gökten inen yıldırımla** tepeden vuruş ×1,5 (öndeki kutu R+30) | kazık saplanmaz (zırha işlemez); ağdaysa cızırdar ve zincirle çarpılır, sersemler, **çekilmez** ("çekilmez") | çöküş anında: yıldırım ×1,35 ve **ikinci zincir**: bütün işaretlilere (seçkin dahil) ×0,4, aralarında şimşek | 0,35 + 3 × 0,12 + 0,8 + 1,5 = ×3,0 (TAM ×3,4) | kırbaç, kılıç, mızrak, uzun sap | 75 Kut |
| **Tulpar Dörtnalı** (toprak, 17) «Kamın davulu atıdır» | 0,16 sn silah baş üstüne (ayağın önünde davul ensō'su) → **dört davul vuruşu** (0,34 sn arayla; her birinde 0,14 sn kalkış + iniş): inişte oyuncunun çevresinden **toynak dalgası** (yarıçap 64 / 86 / 108 / 130 px; ×0,4 / 0,52 / 0,64 / 0,76): sıradanlar dışa savrulur (kb 170) ve 0,3 sn sersemler; baş üstünde **davul şeridi** (dört ensō + kayan tokmak; vurulan dolu, TAM altın, kaçan çarpı); her vuruşun kendi **ritim halkası** var (0,28 / 0,26 sn önce belirir): halka kapanırken T → o vuruş **TAM** (×1,35, yarıçap ×1,3, altın varak) → 0,12 sn sonra **dörtnal**: 0,36 sn öne koşu 580 px/sn, 200 px (duvarda / uçurumda durur), dokunulmaz; yoldakiler ×1,5 (sıradanlar 240 px/sn yukarı fırlar, duvara çakılır) | savrulmaz ("savrulmaz"): yalnız hasar + duruş; dörtnalda sendeleme | **dördü de TAM'sa** biniş TAM: mürekkepten **Tulpar** (sırt, boyun, baş, iki evreli bacaklar, yele, kuyruk, ışıyan kanat; oyuncunun arkasında, her 0,09 sn yeni kare), **"HAYT!"**, 680 px/sn, 260 px, ezme ×1,35 ve 290 px/sn fırlatma. Değilse sade koşu (at yok, ×1,0) | 0,4 + 0,52 + 0,64 + 0,76 + 1,5 = ×3,8; hepsi TAM: ×5,1 | ağır, dev, kılıç, uzun sap | 70 Kut |

Karşı oyun / ustalık: Pehlivan'da seçkin varken ya da sıradan menzilde değilken sanat zayıf (yalnız silah savrulur),
duvar yakınında fırlatış en güçlüsü (PAT! + duvar sekmesi). Yıldırım Ağı'nda ağ yarım saniye yerde durur: dışında
kalan düşman etkilenmez, içindekiler yavaşladığı için oyuncu zincir ve yıldırımı yerleştirir; kazık önce sıradanı seçer
(zırha işlemez), seçkin ancak ağın içindeyse çarpılır. Tulpar'da dalga her vuruşta büyür: yakındakiler ilk, uzaktakiler
son vuruşta; dört halkanın hepsini tutturmak (ezbere basış halkayı yakar) atı getirir.

Güvenlik: tutulan gövdenin yörüngesi `_tut` / `_serbest_hedef` ile duvara girmez, dikey yarıçapı sütundaki tavana göre
kısalır (`_oda`); fırlatma hızı `_firlat_vy` ile tavana göre; ağ kazıkları duvar içine ya da zemini olmayan yere
çakılmaz (`_ya_zemin`); çekilenler yerde kayar (kalkış yok); dörtnal `_oyuncu_yer` ile duvar / uçurum önünde durur.
Sanat kesilirse (ölüm, kavranma) kilitler bırakılır, ağ ve davul şeridi söner; uçan düşman uçuşunu bitirir.

### Görseller (sumi-e fırça sistemi)

Paletler aynı (`SanatFX.PAL_EK` 15 yeşim, 16 gök, 17 toprak). Yeni kipler: `ag` (şimşek ağı: bıçak ucu ve kazıklar
arasında her 4 karede yeniden kırılan sumi şimşek + gök damarı + ak çekirdek, kenarda sulu yıkama ve kısa çatallar,
kazıklarda dikili kazık ve dönen çıtırtı kılları), `davul` (dört ensō'luk davul şeridi + kayan tokmak).

| Sanat | Bileşim |
|---|---|
| Pehlivan Savurması | peşrevde dize vurulan kuru avuç izleri + alçak yıkama; kavramada gövdeyi iki yandan saran kalın sumi parantezleri; her yarım turda oyuncunun çevresinde eğik elips yay (ön yarı koyu kalın kuru fırça + yeşim damar + ak çekirdek, arka yarı sulu yıkama, dışa savrulan kıllar); fırlatışta geri kalan hız çizgileri ve yıkama halkası; çakılışta sıçrantı, iki yana sürtme, küçük yarık, duvarda dikey sürtme, "PAT!" (TAM: altın varak) |
| Yıldırım Ağı | avuca toplanan kırık kıllar + parıltı; her kazıkta elden hedefe ince şimşek (`simsek`), saplanma (kazık gövdesi, baş çaprazı, çıtırtı, sıçrantı; yere çakılınca toz); ağ kipi; çöküşte her kenarda kalın şimşek, sıçrantı, "ÇAK!"; yıldırım: gökten vuruş noktasına kalın kırık sumi + gök damarı + ak çekirdek, iki (TAM: üç) dal, yerde yıkama, sıçrantı, TAM'da altın varak; TAM zincirinde işaretliler arasında şimşekler |
| Tulpar Dörtnalı | hazırlıkta ayağın önünde davul ensō'su; her vuruşta ayaktan iki yana büyüyen yassı elips halkalar (sıçratan kuru fırça, büyüyerek açılır), halka boyunca toynak izi noktaları ve yukarı toz kılları, TAM'da altın varak + ışıyan iç halka; davul şeridi; binişte arkaya savrulan hız çizgileri, yıkama, sıçrantı, "HAYT!"; **mürekkep Tulpar** (oyuncunun arkasında z −1: sırt-boyun, karın, baş, kulak, iki evreli dörtnal bacakları, savrulan yele ve kuyruk, geriye-yukarı iki kanat süpürmesi; TAM'da kanat ışır), toynak tozu |

**Yansıma sözcükleri**: `sanat_fx` atlasında kaldırılan KÜT! / VUŞ! / ÇAT! hücrelerine aynı fırça diliyle **PAT!**,
**HAYT!**, **ÇAK!** (yeni harfler P, H, Y). Üretim: `python tools/artgen/sanat_fx_ink.py`, HD: `KY_HD=2 python
sanat_fx_ink.py` + `python hd_paket.py --paketle` (yalnız `sanat_fx.png` / `.webp` değişti; fırça dokusu bayt bayt aynı).

**HUD tamgaları** (`glyph_strokes`): Pehlivan: kalınlaşan çekiç yayı + ucunda savrulan gövde + fırlatış çizgisi; Yıldırım
Ağı: üç kazık arasında kırık şimşek üçgeni; Tulpar: at başı ve boynu (profil), kulak, yele, altta dört vuruş noktası.

### Ses (`tools/audiogen/v27_sanat.py`, sentez)

`sanat_pesrev` (derin soluk + dize vurulan iki avuç + toz), `sanat_tutus` (deri gıcırtısı + gövde toku + homurtu),
`sanat_savur` (dönen ağır süpürme + ip ıslığı; yarım turda bir, perde yükselir), `sanat_firlat` (yukarı kıvrılan süpürme
+ homurtu), `sanat_pat` (ıslak şaplak + gövde + toprak + gürleme), `sanat_kazik` (elektrik cızırtısı + inen ton + kazık
toku), `sanat_ag` (110 Hz harmonikli titreyen uğultu + ince çatırtı; ağda tıklarda alçak yinelenir), `sanat_cak`
(yıldırım çatlaması: tık + geniş bant patlama + kırpma + gök gürlemesi), `sanat_davul` (çerçeve davul zarı + deri),
`sanat_dortnal` (altı toynak vuruşu + rüzgâr + at soluğu). Eski `sanat_evren / kut / tengri / vus / yarik / cat`
silindi. `python v27_sanat.py <adlar>` yalnız onları üretir.

### Test

* `-- --sanat --boss --muhur=0` (`tools/tests/sanat_testi.gd`): 13 sanat genel denetim (bedel, bekleme, isabet, hasar,
  süre ≤ 150 kare). Kombo testi sanata göre beklenti (`KOMBO_KIP`): **tut** (Pehlivan: öndeki sıradan kavranır ve
  savrulur ≥ 24 px / tavanda ≥ 8, ≥ 6 kare kilitli; üç sıradan da vurulur; seçkin "tutulmaz"), **cek** (Yıldırım Ağı:
  üç sıradan kazıklanıp çekilir, ≥ 4 kare kilitli; seçkin ağda cızırdar, çekilmez), **dalga** (Tulpar: kilit yok, üç
  sıradan da dalgayla vurulur, seçkin "savrulmaz"; TAM beklentisi **4**: test dört halkanın her birinde basar), açık
  alanda ritim TAM, alçak tavanda erken basış (kaçar). Gerçek duvar kenarında Pehlivan (fırlatılan duvara çakılır:
  `duvar` sayacı ≥ 1), Kurt Dansı ve Tulpar (oyuncu duvara girmez).
* Sonuç: SONUC GECTI hata=0, TAKILMA=0. Pehlivan açık alanda tutulan 44 px kalkar, 42 kare kilitli, fırlatış H 257 px,
  ritim TAM; alçak tavanda H 220, erken basış kaçar; duvar kenarında duvar sekmesi 1. Yıldırım Ağı üç sıradanı
  kazıklayıp çeker (17 kare kilit, kalkış 16 px; tavanda 10), seçkin "çekilmez". Tulpar dört halkanın dördü TAM
  (ritim=4), kilit yok, üç sıradan da vurulur, seçkin "savrulmaz"; tavanda kalkış 25 px. Hepsinde yerde=3/3,
  tavan_üstü=0, oyuncu_tavan=0, kötü_konum=0.
* Kare şeritleri: `--fixed-fps 60 -- --sanat --boss --pencere=1920x1080 --sanat_kare=<klasör> --sanat_tek=<id>`
  (3 sıradan + 1 seçkin, ritim TAM); efekt önizlemesi `--sanat_fx=<klasör>` yeni bileşimleri (pehlivan_*, kazik,
  yildirim_vur, tulpar_*, damgalar, ag + davul kipleri) de çeker.
* Görseller (`docs/v32/sanat/`): `pehlivan_savurmasi_dizi.jpg`, `yildirim_agi_dizi.jpg`, `tulpar_dortnali_dizi.jpg`
  (her 3. kare, 3 sıradan + 1 seçkin), `fx_onizleme.jpg` (yeni bileşimler), `hud_tamgalari.jpg`,
  `yansima_sozcukleri.png` (PAT! / ÇAK! / HAYT! ve kalanlar), `sanat_ekrani.jpg` (13 sanatlık kayan liste).
* Gerileme: `--dovus --boss --kontrol` TAKILMA=0, basılmamış 0; `--zeka --muhur=0` BITTI; `--otomatik --derinlik=1` ve
  `--derinlik=5` (`--quit-after 9000`) bölüm sonu ve çıkış, ölüm 0; `--mekanik` BITTI; `--piksel_tara --otomatik
  --derinlik=3` TOPLAM 0. Betik hatası yok.
* Ayrıca: `SanatUI._nisan_pips`'in bilinen "Invalid polygon data" hatası giderildi (kısmen dolu tane artık
  `Geometry2D.intersect_polygons` ile kesilir; sıfıra yakın alanlı ince dilimler ve ≥ %98 dolu tane ayrıca ele alınır).

### Bilinen

* Göç yalnız kimlikleri taşır; eski sanatlar için harcanmış Kut geri verilmez (yerine gelen sanat zaten açık sayılır).
* Sanat ekranı görüntüsü listenin üst yarısını gösterir (kart: Ay Hilali); yeni sanatların kartı oyunda aşağı kaydırınca görünür.
* `--ekran=sanat` / `--ekran=ogretmen` kartı hâlâ eski seçimi (Ay Hilali) açar; Main.gd'ye dokunulmadı (birleştirme riski).


## v32: Dead Cells tarzı bölüm tasarımı, Kut Taşı ışınlanma ve harita

Geri bildirim: "Bölüm tasarımı düz ve doğrusal OLMAMALI: Dead Cells gibi büyük, derine inen / yukarı çıkan, çıkmazları
olan bölümler; belli yerlerde hatırladığımız ışınlanma noktaları; keşfederken çıkmaza girince öğrendiğimiz bir ışınlanma
noktasını seçip haritanın devam ettiği yere ışınlanalım. Sağ altta önce karanlık, keşfettikçe açılan, ışınlanma
noktalarını gösteren bir harita. Dead Cells'in harita mekaniğini iyice incele."

### Araştırma ve hedefler (Dead Cells)

Kaynaklar: Sébastien Benard, "The level design of Dead Cells: a hybrid approach" (deepnight.net / Gamasutra);
deadcells.wiki.gg (Biomes, Runes, Forgotten Map). Çıkarılan ilkeler:

* **Sabit çerçeve + rastgele dolgu**: biyomların sırası ve bağlantıları elle; her biyomun **kavram çizgesi** (giriş,
  çıkış, özel odalar, aradaki dövüş / keşif odaları) tasarımcı tarafından; çizge bölümün uzunluğunu, özel oda sayısını,
  labirentliğini ve giriş-çıkış arası en az oda sayısını sınırlar (surlar doğrusal, lağımlar dolambaçlı).
* **Elle yapılmış oda parçaları**: her parça amaçlı (hazine, tüccar, dövüş), giriş / çıkış sayısı belli, biyoma bağlı
  (hapishane odası lağımda çıkmaz). Üretici her düğüme havuzdan uyan odayı seçer; kapılar eşleşir.
* **Dallar ve çıkmazlar**: ana yoldan ayrılan dallar ödülle biter (Kut Tomarı = "scroll of power", hazine sandığı,
  tüccar, lanetli sandık, **zamanlı kapı** (Promenade 2 dk, Ramparts 8 dk), seçkin bekçisi). Düşey: Clock Tower / Ramparts
  tırmanış, Toxic Sewers / Ossuary iniş; odalar 1-2 ekran.
* **Işınlanma taşları** (teleportation monoliths, Teleportation Rune): bölümde dağınık; yanından geçince haritaya işlenir,
  taşın dibinde etkileşim haritayı açar, bulunmuş bir taş seçilince anında oraya gidilir; oyunun iç mantığında "çıkmaza
  girdin, geri yürüme" sorununu çözer.
* **Harita**: sağ üstte / tam ekranda; girilen odaların geometrisi sisten açılır; işaretler: çıkışlar, ışınlanma taşları,
  tüccar, tomarlar, eşyalar, zamanlı kapılar, seçkinler (Explorer's Rune ile %80 keşifte tamamı). Canavar sayısı
  dövüş karosu uzunluğuyla ölçeklenir.

Hedefler: ana yol en az bir kat iner / çıkar; her bölümde 3-6 dal ve 2+ çıkmaz ödül odası; döngüler; 3-6 Kut Taşı;
erişim %100 (giriş -> Kut Kapısı ve her ulaşılan hücreden dönüş); v25 kuralları (3 karo baş boşluğu, yuvarlanma geçidi
yok, geçerli yerleşim, eşya katıda değil, tüccar duvarda değil) korunur; boss arenası ve yurt değişmez.

### Üretici: kesim ızgarası ve oda çizgesi (`scripts/world/LevelGen.gd`, yeniden yazıldı)

Bölüm `Level.W x Level.H = 256 x 90` karo (eskiden 256 x 44); 36 x 22 karolık **kesimlerden** (`SW`, `SH`; iç alan
32 x 18 ≈ bir ekran) ızgara: stil başına sütun x satır (`STIL`: orman 7x3, uçurum 6x4, mağara 6x4, harabe 6x4, bozkır 7x2,
kuyu 5x4). Biyom `data/world.json` "level" ile satır sayısını ve **yönü** ezer: Ötüken / Şahmeran / Tamu `inis` (giriş
üstte, Kut Kapısı altta), Kaf `cikis` (tırmanış), Bozkır `serbest`.

1. **Ana yol** (`_ana_yol`): sol sütundan sağ sütuna rastgele yürüyüş; sağa ağırlık 3, dikey 1-3 (yöne göre); hedef
   uzunluk sütun + satır (+0-2); art arda iki dikey adım yok, 2 satırda en çok 2 dikey adım (kesimler dallara kalsın).
2. **Dallar**: 3-6 (`STIL.dal`) kavşaktan boş kesimlere 1-3 odalık yürüyüş (dikey tercih); son oda **çıkmaz ödül odası**.
   Ödül sırası: tomar, hazine kesin; sunak / seçkin bekçisi / zamanlı kapı karışık; tüccar istenirse (`Level._plan_bezirgan`
   kararı üretimden ÖNCE) başa "pazar" (boss öncesi bölümde çıkışa en yakın kavşaktan). Giriş ve çıkış odası yedek kavşak.
3. **Döngüler**: kapısız komşu odalar arasında `STIL.dongu` şansıyla ek kapı (ödül odaları tek kapılı kalır).
4. **Birleşme**: ana yolda yan yana odalar geniş salon (`genis`), üst üste odalar yüksek kuyu / kule (`yuksek`) olur.
5. **Oda türleri** (`kinds` havuzu): salon (adalar, platformlar, duvar sekileri, çukurcuklar, cepler), teras (7-11 sütunlu
   ±2-4 basamaklar), harabe (sütunlar, kemerler, kırık taban), mağara (dalgalı tavan, sarkıtlar, kayalar, cepler),
   çukur (ortada 8-12 karo tehlike çukuru + kırık köprü), köprü (iki yüksek uç, 6 karo derin uçurum, dipten merdiven),
   kuyu (ortada tabandan tavana zikzak basamak, duvar sekileri), kule (kırık sütun güdüğü + tavandan sarkan baş, yükselen
   sekiler). Kapısız yanlarda iç alan 0-5 (ödül odasında 2-6) karo daralır; taban 2-4 parçada ±3 oynar (rampalar sütun
   başına en çok 2 karo); gök açık stillerde üst satır odalarının tavanı yok, aradaki kaya yarı tabandan 10 karo yukarıda biter.
6. **Kapılar** (`_door_geometry`, `_carve_door`): yan kapı 4 karo duvarda 5 karo yüksek geçit, taban satırı `yd` iki odanın
   tabanından ya da %30 rastgele yüksekte; iki yanda 4 karo **iniş sekisi** (duvara asılı çıkıntı / tabana oyulmuş cep;
   taban 4+ karo alçaksa 6 sütunluk zikzak **merdiven**, 2+ karo yüksekse tabana çıkan 2 karolık basamaklar). Dikey kapı:
   üst odanın tabanından 6 karolık **kuyu**, alt odada tabandan kuyuya 3 satırda bir zikzak basamak. 32 karolık odada iki
   yan seki + merdiven (10 + 10) ve kuyu ağzı bölgesi (10) çakışmadan sığar.
7. **Kut Taşları**: giriş odası (girişin 9 karo sağı), her çıkmaz ödül odası (kapı sekisinin iç ucu), dallanma kavşakları;
   en çok 6. **Eşya kaideleri**: ana yolun 1/4, 2/4, 3/4'ündeki odalar. **Tehlike şeritleri**: dövüş odalarının düz tabanında
   2-3 karo (%55). Zamanlı kapı sütunu `zamanli` listesinde.
8. **Denetim ve onarım**: `_open_headroom` (3 karo), `_reach` (giriş -> çıkış), `traps` + `fix_traps` (her ulaşılan hücreden
   dönüş; tehlike tabanlı hücreler sayılmaz: çukur oyuncuyu kendisi sektirir), geçmezse 12 denemeye dek yeniden üretim.
   Erişim modeli `_moves` aynı (tek / çift zıplama 4 karo, ±5 sütun, 15 satır düşüş, platform kesmez).

Döndürülenler: `rooms` (iç alan, taban `fl[]`, tavan `ce[]`, rol, ödül), `doors`, `path`, `spawn`, `exit`, `tasi`,
`zamanli`, `kaide`, `bounds`, `metrics`, `chunks` (ödül işaretleri; `Level._place_rooms`: S sunak, T hazine, E seçkin, M tomar,
P pazar, Z zamanlı ödül), `heights` (eski `surface_y` için ana yol odasının tabanı). `path_cells` / `stand_cell`: bot rehberi.

`Level.gd`: oyuncu `spawn`, Kut Kapısı `exit`; düşmanlar oda başına (giriş ve ödül odalarında yok; seçkinler ana yolun 3.
odasından sonra, aralarında 4 yaratık); tomarlar: tomar odaları + ana yol ortası + yüksek çıkıntı (toplam 3); keşif ganimeti
aynı; tüccar düzleme yok, pazar odasının "P" işaretine kurulur; süsler her odanın tabanı boyunca; kamera sınırları
`bounds`; `surface_y(x, y_ref)` çok katlı bölümde aktörün kendi katını bulur (Enemy / Boss / Player / Tehlike çağrıları).

### Ölçüm (`--harita`, 6 stil x 20 tohum = 120 bölüm; önce = v25, sonra = v32)

| | v25 | v32 |
|---|---|---|
| bölüm | 256 x 44, tek yüzey + 2-3 parça + 1-3 özel oda | 256 x 90, 13-18 oda (ort. 15,3), 15 kapı |
| ana yol | soldan sağa, düz | ort. 9,6 oda, ort. 3,4 dikey adım (en az 1), 2-3 kesim satırı |
| dal / çıkmaz | 0 (yan odalar yolun üstünde) | ort. 4,1 dal / 4,1 çıkmaz (en az 2), 0,7 döngü, 0,9 geniş + 0,8 yüksek birleşme |
| düşey aralık (en yüksek - en alçak taban) | ~12 karo | ort. 46 karo (3-4 satırlı stillerde ~50) |
| Kut Taşı / zamanlı kapı | — | ort. 6,0 (en az 5) / 0,24 |
| giriş -> çıkış + dönüş (erişim modeli) | 120 / 120 | 120 / 120 (ilk denemede ~%97; ort. 1,1 çıkmaz onarımı, 2,8 açılan tavan karosu) |
| ulaşılan ayakta durma hücresi | — | %96,5 (en az %88,8; kalanı yüksek cep / sarkıt üstü) |
| ana yol en az 3 karo baş boşluğu / yuvarlanma hücresi | 120 / 120, 0 | 120 / 120, 0 |
| geçersiz düşman yerleşimi / eşya katıda / tüccar duvar | 0 / 1014, 0, duvar_ok | 0 / 1150 (503 taşındı, 0 konmadı), 0, duvar_ok |
| düşman / bölüm (derinlik 1-9) | ~110-170 / 6 | 132-143 / 6 (oda başına 15-22 karoda bir) |
| üretim süresi | ~0,3 sn | ~1,2 sn (23 k hücrede BFS denetimleri) |

### Kut Taşı ışınlanması (`scripts/world/KutTasi.gd`, `Level.isinlan`)

* **Keşif**: taşın 84 px yakınından geçince (ölü değilken) mürekkep halkası, Kut zerreleri, ışık flaşı, `ruh_tasi` sesi,
  HUD iletisi ("Kut Taşı bulundu: ... · M haritadan ışınlan") ve bir kez öğretici kartı; tamga Kut rengine döner, dipte ışık.
* **Kullanım**: M tam ekran haritayı açar (oyun durur); A/D (W/S) bulunmuş taşlar arasında gezer, Boşluk / Enter seçer,
  M / Esc kapatır. Taşın dibinde (34 px) W de haritayı açar (hızlı ışınlanma). Bot: `harita_istek`.
* **Kurallar**: yalnızca bulunmuş taşa; dibinde durulan taşa değil; ölüyken / yakalanmışken / yurtta / boss arenasında
  olmaz; bedelsiz; **0,9 sn kanal** ("Kut'a bağlanıyor": oyuncunun üstünde dolan halka, gövde incelip uzar, zerreler),
  bu sırada **hasar alınırsa kanal bozulur** ("Işınlanma bozuldu!"); varışta mürekkep dağılma / toplanma, halka, flaş, taş
  adı, `kut_donusum` sesi, **0,6 sn dokunulmazlık**, kamera anında oturur (`CameraV2.snap`), hedef çevresi sisten açılır.
  Keşifler bölüm içinde kalıcı, yeni bölümde sıfırlanır.
* **Zamanlı kapı** (`scripts/world/ZamanliKapi.gd`): çıkmaz ödül odasının girişinde taş söve + kum saati tamgası + kalan
  süre çizgisi (bölüm başından 90 sn; son 15 sn kızıl nabız); süre dolunca oyuncu dışarıdaysa geçit katı olur
  (`Level.set_solid`: ızgara + zemin karo katmanı, demir parmaklık çizimi, toz, `kapi` sesi); süresinde girildiyse
  "Zamanında yetiştin!" ve kapı hep açık. Ödül: üst kademe eşya + 6 altın.

### Harita (`scripts/world/Harita.gd`, `scripts/ui/HaritaUI.gd`)

* **Sis**: oyuncunun hücresinden katı olmayan karolar boyunca taşan 18 x 11 karolık elips görülmüş sayılır (duvardan
  geçmez; görülen havanın bitişiğindeki duvar yüzü de görülür); 0,2 sn'de bir ya da hücre değişince. Doku karo başına
  2 x 2 piksel RGBA: görülmeyen saydam (altındaki parşömen + %80 koyu sis: harita önce karanlık), görülen hava açık parşömen, katı mürekkep,
  platform kahve çizgi, tehlike kızıl.
* **Küçük harita** (sağ alt, oyun içi; yurt ve boss arenasında yok): parşömen + mürekkep çerçeve, oyuncu ortada (sınırlara
  kenetli), kızıl mühür oyuncu + yön çentiği, keşif yüzdesi, "M" tuşu. Ayarlar: **Küçük harita** (Kapalı / Küçük 126x76 /
  Normal 168x100 / Büyük 228x136 birim; 2,6-3,4 birim/karo) ve **Harita saydamlığı** (Hafif / Orta / Koyu);
  `user://ayarlar.cfg` "harita". 1080p'de Normal 336x200 px, 1440p'de 448x267 px (HUD ölçeğiyle büyür).
* **Tam ekran harita** (M): bütün bölüm sınırları parşömene sığdırılır (~2,3 birim/karo), biyom adı, derinlik, keşif
  yüzdesi, Kut Taşı sayısı, seçili taş adı ve halkası, lejant, tuş satırı.
* **İşaretler** (karosu görülmüşse): Kut Taşı (bulunmuş: Kut rengi dikilitaş; yalnızca görülmüş: sönük), Kut Kapısı (kemer),
  Tomar, Eşya kaidesi, Bezirgân, Sunak, Seçkin (kafatası; canlıyken), Zamanlı kapı (kum saati + kalan süre). Taş adları:
  Yol Başı, N. Kavşak, Tomar / Hazine / Sunak / Pazar / Bekçi / Zaman Taşı, Kapı Taşı.

### Bot rehberi (`scripts/world/Rehber.gd`, `--otomatik`)

Dallı bölümde eski "sağa koş" botu çıkışa varamaz. Rehber: önce en yakın 2-3 ödül odası, sonra Kut Kapısı; `LevelGen.path_cells`
(hücre yolu) ile yol noktalarına göre yürür, zıplar, çift zıplar, platformdan aşağı iner; 1 sn takılınca yeniden plan;
hedef 70+ hücre uzaktaysa ve bulunmuş bir taş hedefe daha yakınsa ışınlanır (yarısı harita ekranı üzerinden: Main "harita"
kipi). `[otomatik] KESIF` satırı: keşif yüzdesi, bulunan taş, ışınlanma, ziyaret edilen ödül odası.

### Test

* `-- --harita [--harita_tohum=20 --harita_bolum=6]`: IZGARA satırlarına çizge ölçümleri eklendi; yeni denetimler: erişim +
  dönüş 120/120, en az 3 Kut Taşı, en az 2 çıkmaz, en az 1 dikey adım, ulaşım >= %85. Çekimler: `--harita_ekran=genel`
  (biyom başına bütün bölüm tek karede), `kucuk` (bot gezer, küçük harita boyları, tam ekran harita), `isin` (ışınlanma dizisi).
* `-- --isinlan --muhur=0` (yeni, `tools/tests/isinlan_testi.gd`): keşif, ikinci taş, dibindeki / bulunmamış taşa ret,
  harita ekranı (açılır, oyun durur), seçim -> kanal -> varış (uzaklık 0 px, dokunulmazlık, yerde, kamera), darbeyle bozulma,
  rehber yolu (giriş -> kapı, her ödül odasına), zamanlı kapı (kapanır, karolar katı; içerideyken kazanılır, kapanmaz). GECTI.
* `godot --headless --path . --script res://tools/tests/harita_dok.gd -- --dok_cikti=K --dok_tohum=N`: üretici dökümü
  (ızgara PNG'leri: oda çerçeveleri, kapılar, taşlar, ödüller, ulaşılan hücreler) ve ortalamalar.
* Diğerleri (`--otomatik --derinlik=1/3/5/7/9 --muhur=0` (+`--bot_gercek`), `--tuccar`, `--zeka`, iki boss, `--yurt --yurt-tur` (`--otomatik` olmadan: ikisi birlikte yurt botuyla çekişir),
  `--dovus --boss`, `--mekanik`, `--piksel_tara`): betik hatasız.

### Görseller (`docs/v32/harita/`)

`genel_*.jpg` (Ötüken orman / harabe, Bozkır, Şahmeran mağara, Kaf kuyu, Tamu uçurum: bütün bölüm tek karede),
`izgara_*.png` (üretici dökümü), `hud_kucuk_harita*.jpg`, `tam_harita.jpg`, `isin_0..3_*.jpg` (taş, harita seçimi, kanal, varış).

### Bilinen

* Üretim ~1,2 sn (eski 0,3): BFS denetimleri 23 k hücrede; bölüm geçişinde hissedilir, ileride onarım döngüsü
  seyreltilebilir.
* Ulaşılamayan %3-5 ayakta durma hücresi: yüksek cep tepeleri, sarkıt üstleri, kuyu dudakları; oyunu etkilemez.
* Kuyu basamaklarının altına çizilen kule ayakları (`_place_towers`) uzun kuyularda iskele gibi yükseliyor; görsel.
* Küçük harita yalnızca bölümde (yurt / boss arenasında kapalı); gizli oda yok (ileride: kırılan duvar).
* Bot rehberi dallı bölümde yavaş (150 sn'de ~%30 keşif, 2 ödül odası); ölçüm botu `--bot_gercek` aynı rehberi kullanır.

## v32 birleştirme denetimi (gecit + sanat3 + harita2)

Üç dal (`v32-gecit` Konak / Bengisu Usta, `v32-sanat3` savaş sanatları, `v32-harita2` dallı bölümler / Kut Taşı / harita)
`main`'de birleşti; anlamsal çakışmalar sınandı ve giderildi:

* **Boss öncesi Bezirgân kayboluyordu** (`LevelGen.generate`): pazar ödülü dikey (kuyu) kapılı çıkmaz odaya düşünce
  tomara çevriliyordu; istenen pazarların yarısı açılmıyordu (`--harita` 46 istekten 24'ü "pazar odası açılmadı", boss
  öncesi kesin pazar da). Konak testi 2. derinlik boss akışında yakaladı. Şimdi pazar yan kapılı başka bir ödül odasıyla
  yer değiştirir; yoksa kuyulu odada kalır (`_odul_mid` tezgâhı kuyu bölgesinin dışına koyar). Sonuç: 120 bölümde 0
  açılmayan pazar, `--tuccar_her` ile 55/55 tezgâh `duvar_ok`.
* **`bezirgan_gordu` önceki kurulumdan kalıyordu** (`Level.build`): test / çekim akışında aynı derinlik yeniden
  kurulunca eski bölümün pazarı konağa "pazar vardı" diye taşınıyordu; her bölüm kurulumunda sıfırlanır.
* **Pazar temizliği çok katlı bölümde** (`Level._place_bezirgan`): tezgâhın yanındaki sıradan yaratıklar yalnız aynı
  katta (10 karo dikey) kaldırılır; eskiden üst / alt kattakiler de siliniyordu.
* **İleti ipucu kartının altına iner** (`HUD`): konağa varış iletisi ile "konak" kartı (ve Kut Taşı bulundu iletisi ile
  "kut_tasi" kartı) aynı anda çıkıp üst üste biniyordu.
* `--isinlan` `TEST_BAYRAKLARI`'na eklendi (koşu yurtta değil doğrudan bölümde başlar).
* Denetlenen ve sorunsuz: konakta / yurtta `level.harita` yok (küçük harita çizilmez, M açmaz, `isinlan` reddeder);
  konak düz 64 karo (H 90'da kamera alt sınırı `heights`'tan, oda yok); dallı bölümün Kut Kapısı katı zeminde ve
  oyuncu kapıya yürüyerek girince konak kurulur; Usta ekranı ile küçük harita çakışmaz.
* `--konak` testi genişletildi: AKIS'ta kapı zemini + **yürüyerek kapıdan geçiş**, konakta harita / ışınlanma reddi.
* Sonuç: `--harita` (20 tohum: 120/120), `--isinlan`, `--konak`, `--sanat --boss`, `--tuccar` GECTI; `--zeka`,
  `--mekanik` BITTI; `--dovus --boss --kontrol` TAKILMA=0, basılmamış 0; `--boss=tepegoz`, `--yurt --yurt-tur`,
  `--otomatik --derinlik=1` / `--derinlik=3 --bot_gercek` hatasız (bot dallı bölümde 60 sn'de kapıya varmaz: bilinen);
  `--piksel_tara` TOPLAM 0. Betik hatası yok (yalnız motorun çıkıştaki RID sızıntısı satırları, eskiden beri).

## v33: küçük Dead Cells mağaraları

Geri bildirim (v32'yi oynadıktan sonra): "Harita çoooook büyüdü. Dead Cells tarzı KÜÇÜK mağaralar yap. Oyunu çok
yavaşlatıyor: merdivenlerden / basamaklardan tek tek inip çıkmak yorucu ve oyundan koparıyor." Örnek olarak bir Dead
Cells haritası gönderildi (geniş ve sığ, ~4-5:1; çok sayıda KÜÇÜK oda, kısa ve dar koridorlar, çoğunlukla yatay bağlı
çizge, birkaç odalık kısa düşüşler / tırmanışlar, küçük yan cepler ve çıkmazlar, birkaç döngü; bir iki dakikada geçilir).

### Hedefler

* Ayak izi v32'nin 1/3-1/2'si; oda / koridor ağı biyoma göre (mağara tavanı, açık gök üst satırı).
* Merdiven yorgunluğu biter: 1-2 karoluk basamak zinciri yok; aşağı iniş TEK DÜŞÜŞ (açık delik ya da tek yönlü kapak:
  aşağı + zıpla), ana yol aşağı / yana akar; kısa tırmanışlar rahat zıplama aralığında tek yönlü basamaklarla.
* v32'nin iyi yanları ölçekli kalır: 2-4 dal ve çıkmaz ödül odaları, 3-4 Kut Taşı, sis / küçük harita / tam harita,
  v25 / v32 kuralları (3 karo baş boşluğu, yuvarlanma geçidi yok, geçerli yerleşim, eşya katıda değil, Bezirgân ve boss
  öncesi pazar, Kut Kapısı katı zeminde), Konak / boss arenası / yurt değişmez.
* Üretim ~0,3-0,5 sn; bot (`--otomatik`, 9000 kare) Kut Kapısı'na varır.

### Üretici (`scripts/world/LevelGen.gd`: kesim ızgarası küçüldü, oyma yeniden yazıldı)

Bölüm `Level.W x Level.H = 172 x 56` (v32: 256 x 90); kesim `SW x SH = 24 x 13` (v32: 36 x 22), en çok 7 x 4 kesim
(`world.json` "level": Ötüken 3, Bozkır 2, Şahmeran 4, Kaf 3 (eskiden 4), Tamu 4 satır). Çizge v32'deki gibi kurulur
(ana yol, dallar, döngüler, yan yana birleşen geniş salonlar; üst üste birleşme kalktı: dikey geçiş hep kuyu).

1. **Ana yol** (`_ana_yol`): sağa, stilin dikey yönüne (inis yalnız aşağı, cikis yalnız yukarı, serbest çoğunlukla
   aşağı / en çok bir kat yukarı) ve bir dikey adımdan sonra 1-2 kesim SOLA (yılan); her adımda çıkışa boş kesimlerden
   varılabildiği denetlenir (`_yol_varir`); hedef uzunluk sütun + satır farkı + 2-4; art arda iki tırmanış yok.
2. **Dallar** 2-4 (`STIL.dal`), 1-2 odalık; yan dal ağırlıklı (2:1), dikey dal kapaklı düşüşle inilen / birkaç
   zıplamayla çıkılan ödül. Ödül sırası ve pazar kuralları (boss öncesi çıkışa yakın kavşak, kuyulu odaya düşen pazarın
   yan kapılı ödülle yer değiştirmesi, zamanlı kapının yalnız yan kapılı odada olması) v32'den aynen.
3. **Oda kutusu** (`_room_box`, `_profile`): kesimin içinde 12-20 karo geniş (kapısız / kuyusuz yanlardan 0-6 karo
   daralır; giriş ve iki kuyulu oda tam genişlikte), taban kesim başına `y0+7..y0+10` (komşu kesimlerde en çok 2-3 karo:
   kapı eşiği tek zıplama), hava yüksekliği türe göre 6-9 karo (`YUK`; koridordan belirgin yüksek). Taban DÜZ (v32'nin
   ±3 oynayan, sütun başına 2 karoluk rampaları ve teras basamakları kalktı); tavan basamaklı: 4-9 sütunluk parçalar 0-3
   karo alçalır, %20 parça 3-5 karoluk tavan cebi (Dead Cells odalarının girintili silueti); mağarada ayrıca dalga.
   Teras türü yalnızca kapısız yanda TEK 2-3 karoluk seki (çıkış odasında yok).
4. **Yan kapı = dar koridor** (`_door_geometry`, `_carve_door`): A'nın sağ kenarından B'nin sol kenarına 4-16 karo
   uzun, 4 (%20: 5) karo yüksek tünel; taban iki odanın kapı yanındaki tabanından yüksek olanı (öbür yanda en çok 3
   karoluk eşik); iki odada 4 sütunluk ağız bölgesi süssüz kalır. v32'nin iniş sekileri, eşik merdivenleri ve 2 karoluk
   basamakları kalktı.
5. **Dikey kapı = kuyu** (6 sütun; iki odada kesişen ve başka kuyuya 3 karo yaklaşmayan yer; ödül odasında bir uca
   yaslı): **düşüş bacası** (3 sütun) üst odanın tabanından alt odanın tabanına boş; ana yol aşağı iniyorsa ağzı açık
   (yürüyüp düşülür), dal / döngü / tırmanılan ana yolda **tek yönlü kapak** (üstünden yürünür, aşağı + zıpla ile
   düşülür). **Ara duvar** (1 sütun) üst tabandan alt odanın tabanına 4 karo kalana dek: düşen oyuncu tırmanış
   basamaklarına takılmaz. **Tırmanış bacası** (2 sütun): tepesi kapaklı, 3 satırda bir tek yönlü basamak (tek zıplama;
   tabana 4 kalırsa 2'lik ara basamak). 13-15 satırlık kuyu ~0,5 sn düşüş, geri dönüş 4-5 zıplama.
6. **Süsler** küçük odaya ölçekli (`_features`): tek yönlü platformlar tabandan 3 karo (tek zıplama), 2 karoluk sütunlar,
   kemer (4 karo yukarıda), 1-2 karoluk sarkıtlar, kayalar, yan cepler (çıkmaz çıkıntılar), çukurcuk, tehlike çukuru
   (3-4 karo, tek zıplama; geniş odada 5-6 ve ortada basamak), köprü (6-10 karo, 3 karo derin yarık, kırık tahtalar),
   kuyu türünde 4 karo yukarıda tek yönlü üst güverte. Kut Kapısı önünde 10 sütun süssüz (Konak testi kapıya yürür).
7. **Kut Taşları** (`_tasi_ekle`, 3-4): giriş (girişin 9 karo sağı), ana yolun ortasına en yakın kavşak (yoksa orta oda),
   girişten en uzak 1-2 ödül odası (kapı yanı); birbirine 16 karodan yakın taş konmaz. Eşya kaideleri, tehlike şeritleri,
   heights v32'deki gibi; zamanlı kapı artık koridorun odaya bitişik sütununda (4 karo yüksek geçit kapanır).
8. **Sınırlar** (`_sinirlar`): katı olmayan karoların sıkı kutusu + 2 karo (kamera sol / üst sınırı da artık buradan;
   tam ekran harita bölümü parşömene tam sığdırır).
9. **Erişim modeli düzeltmeleri** (`_moves`): (a) yana düşüşte düşülen sütun kayaysa "komşu karo havaysa geç" kısa yolu
   kayanın içinden düşmeye izin veriyordu: artık kenardan yürüyüp düşülen komşu sütun ve varış satırı açık olmalı;
   (b) dikine iniş yalnızca durulan tek yönlü platformdan ve ilk tutunulacak yere dek; (c) düşüş yolundaki tek yönlü
   platform düşeni tutar (eskiden içinden geçilirdi). Rehber artık kapaktan iner, basamakların içinden "düşmeye" çalışmaz.

### Oyuncu ve bot

* `Player`: yuvarlanırken ve kurt biçiminde (Kut gücü) aşağı + zıpla da tek yönlü platformdan / kapaktan iner (eskiden
  zıplıyordu; kurt biçiminde kapaklı kuyudan inilemiyordu). `DonForm` aynı. Düşüş hasarı yok (değişmedi).
* `Rehber` / `Main` bot: (1) `Input.action_press` ile tek karelik zıplama dokunuşu oyuncunun "yeni basıldı" okumasından
  önce bırakılıyordu (zıplamalar / inişler çoğu kez yutuluyordu): dokunuş iki kare basılı; (2) kapak üstündeyken aşağı
  basılı, 0,3 sn'de bir zıpla, bu sırada Main saldırmaz; (3) dallı bölümde Main'in rastgele zıplama / yuvarlanma /
  çömelme dizileri yolu bozuyordu: yalnızca düz alanda ve `--bot_gercek`te; (4) bot giriş taşının dibinde W ile haritayı
  açınca "Zaten bu taşın dibindesin" deyip harita açık kalıyor, oyun duruyordu: başka bulunmuş taş yoksa harita kapanır;
  (5) keşif sıçraması yalnızca aynı hedefte 40 sn takılınca (küçük bölümde geri ışınlanmıyor); (6) can %55'in altında
  ödüle sapmaz, kapıya gider.
* Küçük harita birim / karo 2,6 / 3,0 / 3,4 -> 2,2 / 2,6 / 3,0 (Normal ~65 x 38 karo: 3-4 oda). `Harita.hepsini_kesfet`
  (çekim / test: hava ve duvar yüzleri görülür). `Level._ground_below` 14 -> 7: kuyu kapağının altına uzun iskele ayağı
  çizilmez.

### Ölçüm (`--harita`, 6 stil x 20 tohum = 120 bölüm; önce = v32 üreticisi aynı tohumlarla, aynı ölçüm kodu)

Ana yol: girişten Kut Kapısı'na erişim modelinin en kısa hamle dizisi. "/koşu": yol uzunluğu (yatay + dikey karo) /
yürüme hızı (Player.RUN 155 px/sn = 6,46 karo/sn). "Hamle modeli": hamle başına yatay koşu ile zıplama / düşüş süresinin
büyüğü. Dikey zincir: aynı yönde art arda dikey hamleler (aralarında en çok 4 karo yürüyüş; tırmanış basamakları dahil);
basamak zinciri: yalnızca 1-2 karoluk adımlar. (v32 sütunu v32 erişim modeliyle; v33 düzeltmeleri düşüşleri biraz
uzatır.)

| | v32 | v33 |
|---|---|---|
| ızgara / sınır kutusu | 256 x 90 / ort. 226 x 66 | 172 x 56 / ort. 165 x 46 (%51) |
| hava karosu (gezilebilir alan) | 7264 | 2275 (%31) |
| oda / ana yol odası / dal / döngü | 15,3 / 9,6 / 4,1 / 0,7 | 14,1 / 11,4 / 3,0 / 0,7 |
| ana yol | 331 karo, /koşu 51 sn (hamle ~34 sn) | 224 karo, /koşu 35 sn (hamle ~27 sn, 20-42) |
| düşüş / tırmanış (>= 3 karo) / küçük basamak | 9,4 / 10,2 / 12,4 | 4,3 / 2,7 / 8,0 |
| dikey zincir ort. / en çok | 6,3 / 15 | 3,2 / 7 (yalnız tırmanılan kuyu: serbest / cikis) |
| küçük basamak zinciri ort. / en çok | 1,9 / 4 | 1,3 / 3 |
| Kut Taşı | 6,0 | 4,0 (en az 3) |
| erişim + dönüş / ulaşılan ayakta durma hücresi | 120 / 120, %96,5 | 120 / 120, %100 |
| ana yol 3 karo baş boşluğu / yuvarlanma hücresi | 120 / 120, 0 | 120 / 120, 0 |
| düşman / bölüm (derinlik 1-9) | ~23 | ~13 (709 / 54; ana yolda ~15 karoda bir: v32 ile aynı sıklık) |
| geçersiz düşman / eşya katıda / tüccar duvar / açılmayan pazar | 0 / 0 / duvar_ok / 0 | 0 / 0 / duvar_ok / 0 |
| üretim ort. / en çok | ~1,0 / 9,9 sn | ~0,5 / 0,7 sn |

Bot (`--otomatik`, `--fixed-fps 60 --quit-after 9000`): v32'de dallı bölümde kapıya varamıyordu. v33: 1. derinlikte
3 ödül odasının hepsini gezip (keşif %87, 4/4 taş) **58-73 sn'de** Kut Kapısı (BOLUM_SONU), sonra konak ve 2. bölüm;
`--derinlik=3 --bot_gercek` dövüşerek 95-98 sn'de (keşif %100); `--derinlik=5` dört koşunun ikisinde 77-81 sn'de
BOLUM_SONU, birinde öldü (1. derinlikten yeniden başladı), birinde 120 sn'de kapıya varamadı (dövüşmeyen bot 5.
derinlikte 300-450 hasar alıyor). İnsan hızı için en iyi ölçü bu:
saf koşu 35 sn, savaş + 2-3 ödül sapmasıyla 1-1,5 dk.

### Test

* `--harita` (20 tohum): IZGARA ve BOLUM denetimleri GECTI; yeni `OLCUM` satırları (alan, hava, ana yol karo / sn,
  düşüş / tırmanış / basamak, dikey ve basamak zinciri, üretim süresi). `yol_olcum` başka araçlar için statik.
* Yeni çekimler: `--harita_ekran=tam` (biyom başına bütünüyle keşfedilmiş tam harita), `--harita_ekran=dusus` (açık
  düşüş kuyusunun kenarı, düşüş anı, kapaktan aşağı + zıpla). `harita_dok.gd --dok_yanyana=<png>`: üç stil yan yana.
* `--isinlan`, `--konak`, `--tuccar --muhur=0` GECTI; `--zeka --muhur=0`, `--mekanik --muhur=0` BITTI; `--dovus --boss
  --kontrol` TAKILMA=0, basılmamış 0; `--piksel_tara --otomatik --derinlik=3` TOPLAM 0; `--yurt --yurt-tur` kapıya
  varır; bütün koşularda SCRIPT ERROR 0 (yalnız motorun çıkıştaki RID sızıntısı satırları).

### Görseller (`docs/v33/harita/`)

`tam_otuken.jpg`, `tam_sahmeran.jpg`, `tam_tamu.jpg` (bütünüyle keşfedilmiş tam ekran harita: küçük oda / dar koridor
ağı, kuyular), `dusus_kenar.jpg` (açık düşüş kuyusunun kenarı, sağ altta küçük harita), `dusus_an.jpg` (kuyudan düşüş:
ara duvar ve yanında tırmanış basamakları), `kapak_inis.jpg` (dal kuyusunun tek yönlü kapağından aşağı + zıpla),
`izgara_yanyana.png` (üretici dökümü: orman, mağara, kuyu).

### Bilinen

* Kuyuların tırmanış basamakları ince tahta platform olarak çizilir (altına kısa kule ayağı); kendi "merdiven" görseli
  yok. Kaf (cikis) bölümünde ana yol iki kez kuyudan tırmanır (her biri ~4 zıplama).
* Açık gök üst satırında (orman, uçurum, bozkır) oda tavanı göğe açık, aradaki kaya sütunları tepeye dek çıkar.
* Bot dövüşmez (`--bot_gercek` dışında): derin bölümde can azalırsa ödülleri bırakıp kapıya gider, yine de ölebilir.
* Saf koşu süresi (35 sn) hedeflenen 45-90 sn'nin altında: ayak izi ve yol v32'ye göre küçüldü (oyuncu isteği); gerçek
  geçiş (savaş + ödül sapmaları) bot ölçümünde 58-98 sn.

## v34: Dead Cells zıplaması, kahraman inişi, ağır silah temposu

Geri bildirim (v33'ü oynayarak): (a) "Zıplama mekaniğimiz çok hantal, Dead Cells gibi olsun; basamak çıkmak çok yorucu,
akıcı değil." (b) "Dead Cells'teki gibi yüksekten düşerken havada S + Boşluk ile güzel bir kahraman inişi: düşüş hasarı
almayalım, daha hızlı düşelim." (c) "Bazı iki elli kılıçların ve büyük çift ağızlı ağır silahların savuruşu o kadar yavaş
ki sinir bozuyor; çözüm bul."

### Zıplama (`Player.gd`: `JUMP_V`, `GRAV_RISE`, `GRAV_FALL`, `JUMP_CUT`, `APEX`, `TURN_AIR`, `FLOW.coyote`)

Platform "oyun hissi" kuralları (Celeste / Dead Cells): kısa ve sert yükseliş, tepede çok kısa asılı kalış, yükselişten
sert düşüş (ayrı yerçekimi), tuşu erken bırakınca alçak zıplama, havada güçlü yön verme ve keskin dönüş, cömert coyote ve
zıplama tamponu, kenara kendiliğinden tutunma, köşe düzeltme (v10'dan). Çift zıplama zaten vardı (Umay lütfuyla üçlü);
yenisi eklenmedi. Yuvarlanma / sürünme / ölüm / sanatlar eski `GRAV` 1180'i kullanır; kurt ve Don biçimleri de yükseliş /
düşüş yerçekimine ve alçak zıplamaya geçti.

| (ölçüm: `--mekanik --zipla --boss`, 60 Hz) | v33 | v34 |
|---|---|---|
| sabitler | JUMP_V -430, GRAV 1180 (iki yön), MAX_FALL 560, ACC_AIR 1500, kesme ×0,55, tepe ×0,62 (\|vy\|<60) | JUMP_V -565, yükseliş 1950, düşüş 2100, MAX_FALL 620, ACC_AIR 2400 (ters yönde ×1,5), kesme ×0,5, tepe ×0,6 (\|vy\|<60) |
| tam zıplama yüksekliği | 75,7 px (3,15 karo) | 77,6 px (3,23 karo) |
| tepeye varış / havada | 0,400 / 0,800 sn | 0,317 / 0,617 sn |
| dokunuş (2 kare) | 26,6 px, 0,433 sn | 24,9 px, 0,333 sn |
| koşu zıplaması yatay | 124 px (5,17 karo) | 95,6 px (3,98 karo) |
| koşu + çift zıplama yatay | 204,1 px (8,50 karo) | 162,7 px (6,78 karo) |
| çift zıplama toplam yükseklik | 138,3 px (5,76 karo) | 141,1 px (5,88 karo) |
| coyote (kenardan düştükten sonra) | 5 kare (0,083 sn; FLOW 0,11) | 6 kare (0,100 sn; FLOW 0,125) |
| zıplama tamponu | 6 kare evet, 8 kare hayır | 6 ve 8 kare (0,13 sn) evet (FLOW 0,15) |
| 10 karo düşüş | 0,683 sn, en çok 560 px/sn | 0,550 sn, en çok 620 px/sn |

Erişim (`LevelGen._moves`: tek / çift zıplama en çok 4 karo yukarı, ±5 sütun; düşüş 15 satır): tek zıplama tepesi ≥ eski,
çift zıplama 5,9 karo (> 4), koşu zıplaması 4 karoluk boşluğu (±5 sütun; gövde 12 px: ~84 px merkez yolu) 95,6 px ile
geçer, çift zıplamayla 162,7 px; kenara tutunma 2,5 karo (60 px) yukarıya uzanır. `--harita` (üretici kendi modeliyle)
değişmedi. Bilinen: tek koşu zıplamasının yatay menzili v33'ten ~%23 kısa (Dead Cells gibi kısa havada kalış); modelin en
geniş tek zıplamalık boşluğu (4 karo) hâlâ geçilir, daha genişi çift zıplama ister (model zaten çift zıplama sayar).
**LevelGen değişmedi** (adım yüksekliği / ızgara aynı).

### Basamak ve kenar (`Player._ledge`, `_try_step_up`, `_try_mantle`)

* Kenar bulma artık fizik sorgusuyla (`test_move`: önde duvar, gövde h px yükselince öne geçebiliyor mu, sonra aşağı
  yoklayıp tam ayak hizası); karo ızgarasına bağlı değil (tek yönlü platformun yanından tutunulmaz: altından geçilir).
* **Basamak:** yerde 1 karoluk (≤ 28 px) basamağa doğru yürürken zıplamadan 0,075 sn'lik kaymayla çıkılır (koşu karesi
  sürer, hız korunur). Duvara değişten üstünde durmaya 0,117 sn (v33: çıkılamazdı, zıplamak gerekiyordu).
* **Tutunma:** havada kenara doğru basılıyken ya da ilerlerken (yükselirken de, vy > -260) ayağın en çok 60 px üstündeki
  kenara eller yetişince 0,07-0,15 sn'lik tırmanış (yüksekliğe göre); bitince koşu hızının %85'iyle sürer, tırmanırken
  basılan zıplama tamponda kalır. v33: yalnız tepe / düşüşte (vy ≥ -80), 52 px, sabit 0,16 sn, sonra durma.

| kenar (yürüyerek gelip zıpla) | v33 | v34 |
|---|---|---|
| 1 karo | çıkılamaz (yürüyerek) | yürüyerek 0,117 sn |
| 2 karo | 0,667 sn | kısa zıplamayla 0,250 sn (tutunma), tam zıplamayla 0,533 sn |
| 3 karo | 0,533 sn | 0,300 sn (tutunma) |
| 4 karo (çift zıplama) | 1,067 sn | 0,333 sn (tutunma) |

### Kahraman İnişi (havada S + Boşluk; `HERO`, `_hero_begin`, `_hero_tick`, `_hero_land`, `_land_hold`)

* Aşağı + zıpla çakışması (v33 kapakları): **yerde** (tek yönlü platform / kapak üstünde) aşağı + zıpla = platformdan
  in (değişmedi); **havada** = Kahraman İnişi. Platformdan indikten sonraki 0,25 sn (drop_t) dalış açılmaz (bot kapaktan
  inerken aşağı basılı tutup zıplamaya bastığından). Havada ↓+J Kartal Dalışı (silah saldırısı) ayrı kalır.
* Dalış: 0,06 sn toplanma (havada durur, diz karna), sonra 880 px/sn'den 1150 px/sn'ye çakılır (normal en çok 620), az
  yön (koşunun %25'i), mürekkep izi (koyu gövde kopyaları, damlalar), silah baş üstünde geride.
* İniş: düşüş yüksekliğiyle (k = h / 240 px, 0,35-1,6) büyüyen şok dalgası: yarıçap 56 + 44k px, ±44 px dikey; düşman
  hasar alır (yakın silahın hasarı × (0,55 + 0,45k), merkezden kenara %100 → %60; silahsızken 6 + 6k), geri itilir,
  havaya kalkar, 0,45 + 0,35k sn sersemler; kombo sayılır. Ekran sarsıntısı, itiş, kısa duraklama, titreşim, yer
  çarpması (GroundSlamFX + mor-lacivert mürekkep sıçrantısı), şok halkası, iki yana toz, mürekkep toz bulutu,
  `inis_2` + `darbe_cekic` (+ yüksekte `sarsinti`). Düşüş sersemlemesi / hasarı yok; 0,2 sn dokunulmazlık.
* Poz: 0,32 sn tek diz yerde (çömelik saldırı gövdesi `crouch_atk`), ön kol iskeletle aşağı (yumruk toprakta), bıçak
  geriye-yukarı, gövde ezik ve öne eğik, yavaşça doğrulur; 0,1 sn'den sonra her girdi (yürü / zıpla / saldır / yuvarlan /
  ikincil) pozu keser, darbe alınca biter. Silahsızken derin iniş karesi.
* **Yüksek düşüş sersemlemesi** (Dead Cells gibi; v33'e dek düşüş hasarı yoktu): Kahraman İnişi yapmadan > 12 karo
  (288 px, son hız en çokta) düşünce 0,45 sn sersem (yıldızlar, hareket yok); > 18 karo (432 px) 0,6 sn + azami canın
  %5'i (öldürmez). v33 kuyuları 13-15 satır: ana yoldaki kuyudan düz atlayan kısa sersemler (bot da; geçişi bozmuyor),
  S + Boşluk ile hem hızlı hem sersemsiz.
* Öğretici: HUD `TUT["kahraman"]` (ilk uzun düşüşte, 5 karodan sonra): "S+Boşluk — havada: kahraman inişi".

| ölçüm (`--zipla`) | değer |
|---|---|
| 13 karo: basıştan inişe / normal düşüş | 0,350 sn / 0,633 sn |
| en hızlı dalış | 1150 px/sn |
| isabet (düşmanlar -40, +90, +190 px) | 2 (yakındaki iki; uzaktaki değil) |
| oyuncu hasarı / sersemleme | 0 / 0 |
| 4 karo: basıştan inişe, isabet | 0,167 sn, 1 |
| normal düşüş 13 / 19 karo | 0,43 sn sersem, hasar 0 / 0,58 sn sersem, 6,5 hasar (130 canın %5'i) |

### Ağır silah temposu (`TEMPO_V34`, `V34_AGIR`, items.json "dmg")

Dead Cells'in ağır silahları gibi: ağırlık yavaşlıktan değil darbeden. v26 katmanının üstüne dördüncü katman (sınıf
çarpanları): hazırlık (basış→temas) en çok kısalır, süpürme (görünüş, smear) aynı, kilit / toparlanma biraz kısalır,
zincirin her adımı öncekinden hızlı ("ramp": dev %7, ağır %6, uzun sap %4 / adım), bitiriş hazırlığı ek kısalır. Her
silahın savuruş biçimi, gövdesi ve zinciri aynı. Ayrıca: ağır / dev silahta hazırlık süper zırhlı (sarsılmaz; vuruş anında
söner, zıplamayla yine kesilir), orta kademe vuruş duraklaması ×1,2, vuruş anı öne adım 9 → 13 px. İptaller zaten vardı
(yuvarlanma her evreyi, isabetten 0,05 sn sonra zıplama kilidi, toparlanma her girdiyi keser). Saniyedeki hasar eski
düzeyde (+%2-3) kalsın diye items.json taban hasarı ~%10-25 indi; basılı tutulan şarjlı ağır vuruş (şarj süresi aynı)
`sarj_k` (dev 1,33, ağır 1,27, uzun 1,1) ile eski hasarında. Gün-Ay İkizi (iki duruş) dokunulmadı.

| `[ilk hazırlık, zincir hazırlığı, süpürme, kilit, toparlanma, tutuş, ramp, bitiriş]` | |
|---|---|
| dev (ulu kılıç, bozgun kılıcı, dağ / kor çekici) | 0,62 · 0,7 · 1 · 0,85 · 0,8 · 0,55 · 0,07 · 0,85 |
| ağır (gürz, çivili topuz, savaş baltası, ikiz balta, kıstın, çevgen) | 0,66 · 0,75 · 1 · 0,9 · 0,85 · 0,65 · 0,06 · 0,9 |
| uzun (teber, Erlik tırpanı, kayın asası) | 0,82 · 0,88 · 1 · 0,95 · 0,9 · 0,8 · 0,04 · 0,95 |

Ölçüm (`--dovus --boss --agir`: Player.tempo_phases + ItemGen; 1. kademe kusursuz demir, nitelik / yuvarlama yok;
"temas" = model basış→temas, oyunda + 1 kare; tur = sürekli basışta zincir turu; SnH = ItemGen.dps):

| silah | sınıf | ilk temas (ms) | tur (ms) | hasar | SnH |
|---|---|---|---|---|---|
| ulu_kilic | dev | 376 → 247 | 1727 → 1270 | 11,5 → 8,7 | 40,1 → 41,1 |
| bozgun_kilici | dev | 353 → 234 | 2409 → 1739 | 13,7 → 10,2 | 33,3 → 34,4 |
| dag_cekici | dev | 376 → 247 | 1479 → 1073 | 16,7 → 12,5 | 31,3 → 32,2 |
| kor_cekici | dev | 353 → 234 | 1486 → 1075 | 16,3 → 12,2 | 29,5 → 30,4 |
| gurz | agir | 277 → 200 | 1778 → 1354 | 14,8 → 11,6 | 38,7 → 39,9 |
| civili_topuz | agir | 277 → 200 | 1711 → 1307 | 14,5 → 11,4 | 32,9 → 33,7 |
| savas_baltasi | agir | 277 → 200 | 1118 → 883 | 13,4 → 10,8 | 12,2 → 12,5 |
| ikiz_balta | agir | 277 → 200 | 1766 → 1377 | 8,2 → 6,5 | 31,4 → 32,2 |
| kistin | agir | 294 → 211 | 2269 → 1745 | 12,6 → 10,0 | 30,2 → 31,1 |
| cevgen | agir | 277 → 200 | 1613 → 1248 | 14,5 → 11,5 | 30,7 → 31,5 |
| teber | uzun | 204 → 174 | 1472 → 1291 | 8,9 → 8,0 | 24,7 → 25,3 |
| erlik_tirpani | uzun | 204 → 174 | 1638 → 1439 | 7,4 → 6,7 | 28,0 → 28,7 |
| kayin_asasi | uzun | 204 → 174 | 1650 → 1456 | 8,5 → 7,8 | 26,4 → 27,3 |
| gun_ay_ikizi | uzun | 159 → 159 | 1898 → 1898 | 6,2 → 6,2 | 26,1 → 26,1 |
| alp_kilici | kilic | 161 → 161 | 1288 → 1288 | 7,8 → 7,8 | 26,4 → 26,4 |
| pala | kilic | 161 → 161 | 1447 → 1447 | 6,3 → 6,3 | 25,3 → 25,3 |
| yatagan | duello | 157 → 157 | 1567 → 1567 | 7,0 → 7,0 | 20,7 → 20,7 |
| ikiz_bicak | hancer | 138 → 138 | 1356 → 1356 | 3,7 → 3,7 | 20,6 → 20,6 |
| kargi | mizrak | 156 → 156 | 1018 → 1018 | 5,9 → 5,9 | 20,7 → 20,7 |
| kement | kirbac | 192 → 192 | 896 → 896 | 8,5 → 8,5 | 20,5 → 20,5 |

Oyunda ölçülen basış→temas (`--dovus --boss` TEMPO satırı, 60 Hz): ulu kılıç / bozgun kılıcı / dağ çekici / kor çekici
266 / 250 / 266 / 250 ms, gürz 233, savaş baltası / ikiz balta 216 ms (hedef ≤ 300-350 ms; v33 modeli 353-376 ms + 1 kare). Ulu Kılıç tam zinciri (iki savuruş, her temasta basış; `--agir_klip`): temaslar
400 / 1083 ms → 267 / 767 ms, iki savuruş bitip boşta duruşa ~2,2 sn → 1,72 sn.

### Test

* `--mekanik --zipla --boss` (yeni `tools/tests/zipla_testi.gd`; `--anlik=<klasör>` pencereli çekim): zıplama yayı,
  dokunuş, koşu / çift zıplama menzili, coyote, tampon, düşüş, 1-4 karo kenar, tek yönlü platformdan iniş (dalış değil),
  yüksek düşüş sersemlemesi / hasarı, Kahraman İnişi (hız, isabet, hasarsız, poz). `OZET hata=0`. Test eski sürümde de
  koşar (karşılaştırma: Kahraman İnişi yoksa yalnız zıplama kısmı).
* `--dovus --boss --agir` (durumsuz tempo / SnH tablosu), `--dovus --boss --agir_klip=<silah> --anlik=<klasör>` (zincir
  kare çekimi, evre ve temas anları).
* Gerileme: `--dovus --boss --kontrol` TAKILMA=0, basılmamış 0 (basış 272 / savuruş 135); `--dovus --boss` (tam) betik
  hatasız, TEMPO satırı yukarıda; `--savurus` hatasız; `--mekanik --muhur=0` BITTI; `--zeka --muhur=0` BITTI;
  `--otomatik --derinlik=1` 73 sn'de BOLUM_SONU (ölüm 0), `--derinlik=3` 63 sn'de BOLUM_SONU (ölüm 0); `--harita` GECTI
  (üretici erişimi 120/120, kendi modeli); `--konak` GECTI; `--piksel_tara --otomatik --derinlik=3` TOPLAM 0.
  `--sanat --boss --muhur=0` SONUC KALDI hem v33'te (tulpar_dortnali "kombo çok uzun" 157 kare) hem v34'te
  (yildirim_agi 151-152, tulpar_dortnali 154-156; eşik 150): tek başına (`--sanat_tek=yildirim_agi`) iki sürüm aynı
  (129-143 kare); koşudan koşuya kritik / vuruş duraklaması oynaklığı, v34'ten değil (bilinen). Bütün koşularda SCRIPT
  ERROR 0 (yalnız motorun çıkıştaki RID sızıntısı satırları).

### Görseller (`docs/v34/hareket/`)

`zipla_yay.jpg` (koşu zıplaması yayı, 4 karede bir), `tutunma.jpg` (2 karo kenara kısa zıplama + tutunma),
`kahraman_inisi.jpg` (dalış → yere değiş → poz, şok dalgası, iki düşman sersem), `agir_ulu_kilic.jpg` (Ulu Kılıç zinciri
v33 / v34, basıştan geçen süre ve temas kareleri işaretli).

## v34: yeni tomar tasarımı ve Bezirgân oranları

Geri bildirim: "Topladığımız tomarlar (güçlendirme) var; tasarımını daha temaya uygun ve yüksek çözünürlüklü yapalım." ·
"Bezirgân'da elimdekinden iyi eşya o kadar seyrek çıkıyor ki hiçbir şey alamıyorum. Oranı artıralım."

### Kut Tomarı: kayın kabuğu tomar (`tools/artgen/tomar_ink.py`, `scripts/world/TomarV2.gd`)

Eski görünüş: kaide üstünde 18x24 birimlik yuvarlak deri muska, içinde üç renk taş (`sus_ink.tilsim_muska`). Temadan
kopuktu (tomar değil muska) ve küçüktü. Yeni tasarım Ulu Kayın'dan çıkar:

* **Tomar**: Ulu Kayın'ın kabuğundan dürülmüş sıcak krem bir kayın kabuğu rulosu (kara kayın benekleri, sol ucunda sarmal
  dürüm ağzı, sağ ucunda kalkık kabuk dili). İki ucundaki çubuğa tunç-altın **bozkurt başlı topuzlar** takılı (dışa
  bakan kurt başı: dik kulak, uzun burun, aralık çene ve ak diş, ense yelesi, ışıyan altın göz). Gövdede sırayla ışıyan üç
  **tamga**: Bozkurt kızılı kurt başı (arayüzün "kurt" simgesiyle aynı siluet), Kartal mavisi açık kanatlı kartal, Ayı
  yeşili pençe; renkler `items.json` ongun renkleri (#ff6a4d / #5ec8ff / #9be06a). Sağ üçte birde kızıl deri kayış ve
  üstünde **kızıl mum mühür** (damlalı kenar, altın Kut tamgası: Ulu Kayın / hayat ağacı); mühürden üç renk ipek kurdele
  ve ışıyan boncuklar sarkar (stat seçimi tomarın okunduğu anda yapıldığı için yerdeki tomar üç rengi birden taşır).
* **Kaide**: alçak oyma ak taş seki, önde koçboynuzu oyma, iki yanda ışıyan altın çentik, üstünde saçaklı kilim örtü.
* **Stil**: mürekkep-cel (`inkkit` / `inkprop`), sol üst ışık, gölge yanında kalınlaşan fırça konturu, sıcak malzemeler
  (krem kabuk, altın, kızıl mum) soğuk biyom zemininde canlı okunur; arkasında sıcak toplamalı hale (`GradientTexture2D`
  radyal, nabız). 4 kat süper örnekleme (ss=4), temel doku 4 doku pikseli / birim, HD paketi 8 (2x). Tomar 50x34 birim
  çizilir, oyunda x1,15 (`Pickup.TOMAR_OLCEK`, ~50 birim; eski muska 18 birim): 1080p'de ~200, 1440p'de ~270 ekran pikseli
  genişlik, HD dokuyla keskin.
* **Atlas**: `assets/fx/ink/tomar_v2.png` (+ `_e` ışıma) + `tomar_v2.json` (`rect`, `pivot`, `texel`); HD
  `assets_hd/x2/fx/ink/tomar_v2.webp` (manifest girişi, denetim TAMAM ort 0,0025). Parçalar: `tomar`, `tomar_kaide`,
  `tomar_ac_0..5` (açılış kareleri), `tamga_kurt / kartal / ayi`, `ui_tomar` (arayüz simgesi, ışıma ve hale dokuya
  işlenmiş), `ui_kart_kurt / kartal / ayi` (seçim kartı resmi, 8 doku pikseli / birim). Üretim: `python tomar_ink.py`,
  `KY_HD=2 python tomar_ink.py`, `python tomar_ink.py --paketle` (yalnızca bu atlasın WebP + manifest girişi);
  `--onizleme <png>` iki koyu zeminde (Ötüken gecesi, Tamu kızılı) okunurluk önizlemesi.

Oyunda:

* **Yerde** (`Pickup` "tilsim"): süzülme (2,2 birim) + hafif salınım, ışıma katmanı nabız atar; oyuncu ~100 birim
  yaklaşınca tomar "uyanır" (ışıma ve hale güçlenir, %6 büyür, biraz yükselir). Tomardan sırayla üç stat renginde
  kıvılcımlar ve kara mürekkep damlaları süzülür. Işık sıcak altın (110 birim).
* **Okununca** (`Main._apply_scroll` → `TomarV2.acilis`, ~1,5 sn): mühür kırılır (kızıl mum kıymıkları, altın halka),
  tomar asma tomar gibi aşağı açılır (6 kare: üstte kurt başlı çubuk, kabuk yaprak, iki yanda Göktürk harfi sütunları,
  ortada fırça halkası), halkada **seçilen statın tamgası** belirir ve parlar, sonra halka / ruh / ışık patlamasıyla ışık
  topu gibi oyuncuya uçar; tomar solar. Eski davranış (stat +1, can, SnH duyurusu) aynı.
* **Seçim kartı** (`HUD._draw_tilsim`): her kartın tepesinde açık tomar resmi (o statın tamgasıyla, seçilende hafif
  süzülür); kart 196 → 220 birim.
* **Sol üst sayaç** (`InkHUD.top_left`): ongun rozetlerinin yanında `ui_tomar` simgesi + okunan tomar sayısı.
* **Bezirgân satırı**: Kut Tomarı malının simgesi `ui_tomar`.
* Haritadaki tomar işareti (`HaritaUI`, eski muska simgesi) bu sürümde değişmedi (dosya harita çalışmasında).
* Tomarın nadirliği / stat türü yok (seçim okurken yapılır), bu yüzden yerdeki tomarın tek biçimi var; stat ayrımı
  açılışta, kartlarda ve tamgalarda.

### Bezirgân: oyuncuya göre mal (`scripts/core/Pazar.gd`, `ItemGen.tuccar_drop`, `data/tuccar.json` "pazar")

Ölçüm (`-- --tuccar --muhur=0`, yeni **ORAN** bölümü; `--tuccar_oran` yalnız onu koşar): her derinlikte 150 pazar
ziyareti. Oyuncunun o derinlikte taşıdığı **tipik donanım** oyunun kendi düşüş zarıyla kurulur (`_tipik_donanim`:
başlangıç donanımı; her geçilen derinlikte 3 kaide + yüksek çıkıntı (kademe+1) + %50 alçak çıkıntı + ~2 hazine / seçkin
(kademe+1) düşüşü, her biri %75 bulunur, bulunanın SnH'si yuvasındakinden iyiyse kuşanılır; pazar bölümün ortasında
olduğu için o derinliğin düşüşlerinin yarısı; tomar statı `Zorluk.beklenen_tomar`). "Açık iyileşme": silahta aynı
yuvadaki silaha göre `ItemGen.dps_oyuncu` x1,1 ve üstü; kalkanda blok x kademe x nadirlik (+ ek özellik başına %10) en iyi
bulunan kalkana göre, teçhizatta güç iki yuvanın zayıfına göre.

Neden seyrekti: eşya gücünün çoğu tomardan gelir (v23), kademe silah hasarını derinlik başına yalnız %6 artırır, oysa
silah türleri arasında SnH farkı %40'a varır. Tipik oyuncu derinlik başına ~5 düşüşün en iyisini taşır; Bezirgân'ın tek
zarla yuvarladığı (o derinliğin kademesi, normal nadirlik) silah bu "en iyiyi" nadiren geçer.

Değişen (Dead Cells esinli: dükkân malı kademenin üstünden ve daha iyi nadirlikle gelir):

1. **Bezirgân'ın gözdesi** (ilk mal, "GÖZDE" damgası, kartta "BEZİRGÂN'IN GÖZDESİ"): oyuncunun aynı yuvadaki silahından
   en az **x1,15** SnH'li bir silah (`Pazar.gozde_sec`: 48 aday; ikinci üçte biri bir, son üçte biri iki kademe ve
   nadirlik sütunu üstten; hiçbiri yetmezse en iyi aday "bilenir": hasarı eşiğe dek, en çok x1,35). Fiyat **x0,8**.
   Pazar açılınca (`Pazar.gozde_tazele`) oyuncu arada eşya aldıysa ve gözde artık iyileşme değilse yeniden seçilir.
2. Bütün eşya malları **bir kademe üstten** (`pazar.kademe` 1) ve **iki sütun ileri nadirlik zarıyla** (`pazar.nadirlik`
   2; `ItemGen.tuccar_drop`, `random_drop`'un havuzu + kategori + nadirlik sütunu) yuvarlanır; Sartak her mal için **iki
   aday** arasından oyuncuya iyi geleni tezgâha koyar (`pazar.aday`, `Pazar.iyilesme`).
3. Mallar: gözde, silah, rastgele eşya, seçme mal (bir kademe ve sütun daha üst, x1,35), Umay Sütü, (şansla) Kut Tomarı:
   3-5 → 5-6 mal.
4. Fiyat: daha nadir mal geldiği için nadirlik fiyat çarpanı `[1; 1,7; 2,8; 4,6]` → `[1; 1,55; 2,4; 3,8]`.
5. Pazar satırı: silahta "SnH N ▲ +X (+%Y)" (yüzde yeni), yuva boşsa "boş yuva"; kalkan / teçhizatta "▲ +%Y";
   açık iyileşmelerin simgesinin köşesinde yeşil ▲ rozeti; gözde malda altın "GÖZDE" damgası.

Ölçüm, önce / sonra (`--tuccar --muhur=0`; "bölüm altını" = EKONOMI'nin "hepsi" altını x0,75, üç tohumla gürültülü):

| d | silah malı açık iyileşme (önce → sonra) | iyileşme > 0 | ziyarette ≥ 1 iyileşme (her mal) | gözde iyileşme | iyileşen silah fiyatı / bölüm altını | tipik melee SnH |
|---|---|---|---|---|---|---|
| 1 | %22 → **%61** | %28 → %68 | %74 → **%100** | %100 | 1,05 → 1,08 | 38 |
| 2 | %22 → **%68** | %30 → %74 | %75 → **%100** | %100 | 0,94 → 0,74 | 60 |
| 3 | %19 → **%59** | %27 → %66 | %61 → **%100** | %100 | 1,58 → 1,28 | 85 |
| 4 | %19 → **%60** | %25 → %66 | %53 → **%100** | %100 | 1,23 → 1,00 | 105 |
| 5 | %15 → **%53** | %20 → %60 | %53 → **%100** | %100 | 1,24 → 1,38 | 132 |
| 6 | %13 → **%56** | %18 → %63 | %53 → **%100** | %100 | 0,87 → 0,95 | 163 |
| 7 | %13 → **%51** | %14 → %58 | %49 → **%100** | %100 | 1,70 → 1,11 | 198 |
| 8 | %12 → **%50** | %18 → %57 | %49 → **%100** | %100 | 1,04 → 0,88 | 219 |
| 9 | %9 → **%45** | %15 → %52 | %34 → **%100** | %100 | 1,46 → 0,98 | 250 |
| toplam | **%16 → %56** | | **%56 → %100** | | ort. 1,23 → 1,04 | |

Okuma: silah mallarının yarısından fazlası artık açık iyileşme (hedef %40-60; 1-4. derinlikte biraz üstü, 9.'da %45) ve
her ziyarette en az bir iyileşme var (gözde). İyileşen silah ~1 bölümün altını (gözde x0,8 ile ~0,85): her bölümde
harcayan oyuncu bir iyi mal, bir bölüm biriktiren iki iyi mal alır (Bezirgân bölümlerin ~%80'inde). Altın geliri ve
öbür fiyatlar (Umay Sütü, Kut Tomarı, yenileme) değişmedi.

### Test

* `-- --tuccar --muhur=0`: EKONOMI, yeni ORAN, PAZAR (mal sayısı 3-6, **gözde mal açık iyileşme** denetimi; ör. x1,40
  "Köklü Kara Taş Kistin"), PARSOMEN: GECTI. `--tuccar_oran` yalnızca ORAN (`--tuccar_ziyaret=N`).
* Yeni çekim kipi `--ekran=tomar` (oyuncunun önüne kaideli tomar; `--tomar_dx=`, `--tomar_oku=<sn>` oyunun yolundan
  okur, `--tomar_stat=0|1|2`, `--tomar_yavas=<k>`, `--tomar_seri=<önek>` açılışın 14 karesini 0,1 sn arayla kaydeder).
* `--tomar --boss` GECTI (tomar oyunun yolundan okunur, açılış animasyonu sahnede; SNH tablosu sınırda), `--konak` GECTI,
  `--otomatik --derinlik=1 / 3 --muhur=0` (`--fixed-fps 60 --quit-after 9000`) Kut Kapısı'na varır (80 / 27 sn; her
  ikisinde Bezirgân, 5 / 6 mal, duvar_ok), `--zeka --muhur=0` BITTI, `--piksel_tara --otomatik --derinlik=3` ve
  `--piksel_tara --ekran=tomar --tomar_oku=3` TOPLAM 0 (yeni atlas `assets/fx/ink/` altında: mürekkep yolu),
  `--yurt --yurt-tur` kapıya varır; bütün koşularda SCRIPT ERROR 0 (`--tomar` sırasında Yıldırım Kılıcı ölçümünden sonra
  bir "Lambda capture ... freed" satırı; tomar kodunda lambda yok).

### Görseller (`docs/v34/tomar/`)

`dunya_otuken.jpg` (Kararan Ötüken, kaideli tomar, sıcak hale), `dunya_sahmeran.jpg` (Şahmeran'ın Mağarası: soğuk
yeşil zeminde sıcak tomar), `yakin_1440.png` (2560x1440 çekimden yakın kesit: HD doku, oyuncu yakınken uyanmış ışıma),
`acilis_serit.jpg` (okununca açılış: 0,1 sn arayla 13 kare, Bozkurt tamgası belirip oyuncuya uçar), `kart_secim.jpg`
(tomar seçim kartları: açık tomar resmi + tamga), `pazar.jpg` (Bezirgân: GÖZDE damgası, yeşil ▲ rozetleri, SnH farkı
yüzdesiyle, Kut Tomarı satırında yeni simge), `hud_sayac_1440.png` (sol üst: ongunlar + tomar sayacı),
`tomar_onizleme.jpg` (atlasın parçaları koyu zeminde: tomar, kaide, tamgalar, kart resimleri).

## v34: merak uyandıran bölümler ve yoğunluk

Geri bildirim (v33'ü oynadıktan sonra): "Bölümler vasat. Daha merak uyandırıcı olmalı: oyuncu doğrudan çıkış kapısına
çekilmemeli, 'bir şey mi kaçırdım?' demeli. Katların çoğu boş, boşuna yürüyorum: ne yaratık var ne kazanılacak bir şey.
Mob yoğunluğunu artıralım."

### Araştırma (Dead Cells)

Kaynaklar: Sébastien Benard, "The level design of Dead Cells: a hybrid approach" (deepnight.net); deadcells.wiki.gg
(Objects: Cursed Chest, Timed Door, Breakable wall / hidden areas, Keys / Rune doors). Çıkarılan ilkeler:

* **Gözü yönlendir, yolu sakla (teaser)**: ödül çoğu kez ana yoldan GÖRÜNÜR ama ulaşılmazdır (parmaklık, yüksek
  çıkıntı, kapalı kapı); oyuncu "oraya nasıl giderim" diye dolaşır. Ödül yolları bölümün başında ayrılır.
* **Çıkış ödül değildir**: Dead Cells'de çıkış kapısı çoğu kez ana koridorun ucunda değil, bir yan geçitte / alt katta;
  koridoru takip eden oyuncu önce bir çıkmaza / ödüle varır, kapıyı haritadan arar.
* **Gizli alanlar**: yaklaşınca soluk ışık veren çatlak bloklar, vurunca açılır, ardında yiyecek / altın / tomar.
* **Anahtar ve rün kapıları**: bölümde bulunan anahtar başka bir yerdeki kapıyı açar (geri dönüş, döngü).
* **Lanetli sandık**: isteğe bağlı risk: büyük ödül + lanet (10 öldürmeye dek tek darbe ölüm).
* **Harita tamamlama**: keşfedilmemiş açıklıklar haritada belli olur; tamamlama dürtüsü.

### Üretici (`scripts/world/LevelGen.gd`)

1. **Kut Kapısı sapağı** (`_cikis_sapagi`, `SAPAK_SANS` 0,95): ana yol v33'teki gibi yürünür, sonra son %60'ından bir
   kesimden (stil yönünde: inişte aşağı ya da yana, tırmanışta yukarı ya da yana) boş bir komşu kesime SAPAK açılır;
   Kut Kapısı o tek kapılı çıkmaz odadadır (kuyuysa **kapaklı**: yürürken düşülmez, aşağı + zıpla; yansa koridor; kapı
   odaya sağdan giriliyorsa Kut Kapısı odanın sol ucunda). Eski yolun geri kalanı **uzantı** olur: görünür koridor
   (aşağı iniyorsa açık düşüş) sürer ve bir **ödül odasında** biter (`UZANTI_ODUL`: seçkin bekçi / lanetli sandık /
   hazine). Sapaktaki oda döngüye ve geniş salon birleşmesine katılmaz, ondan dal ayrılmaz.
2. **Pencere dalı** (`_pencere_dali`; her bölümde 1, %40 ikinci): boş bir R kesimi yanındaki (yatay) ana yol / giriş /
   uzantı odası A'ya **demir parmaklıklı pencereyle** bakar (koridorun ortasındaki 1 sütun x 4 karo ızgarada katı);
   R'ye başka bir J odasından 0-1 ara odayla dolaşarak girilir. Puan: A yolda erken, J A'dan sonra, bir ara oda.
   Ödül (tomar / hazine) parmaklığın yakınında (`_odul_mid`), pencere yanı daralmaz (ödül görünsün).
3. **Dallar erken**: kavşak sırası yol başına ağırlıklı (`sıra / uzunluk + rastgele 0-0,55`); boss öncesi pazar
   kuralı (çıkışa yakın) aynen. Pencere / uzantı dalları dal sayısını doldurursa istenen pazar bir ödül odasına geçer
   (boss öncesi uzantının sonu, değilse sıradan dal).
4. **Gizli cepler** (`_gizli_cepler`, bölüm başına 2-3 deneme): odanın kapısız yan duvarında taban hizasında 1 sütunluk
   **çatlak duvar** (4 karo) ve ardında 4 x 4 cep; cep + 1 karo pay bütünüyle kaya olmalı. Cep üretimde OYULMAZ (Level
   kırınca oyar): erişim / dönüş denetimi değişmez; kırılınca cebin tabanı odanın tabanıyla aynı, dönüş yürüyerek.
   İçerik: altın (%50), zula (%20: eşya + altın; v25'in gizli yeraltı odası ganimeti artık burada, `_spawn_kesif`'in
   yoldaki ikinci zulası kalktı), Kut (%15), şifa (%15), anahtar.
5. **Kilitli oda** (`KILIT_SANS` 0,75): yan kapılı bir ödül odası (pazar / zamanlı / pencereli değil) kilitlenir;
   anahtar başka odanın gizli cebinde, cep yoksa başka bir ödül odasının köşesinde ("K"); anahtar konamazsa kilit yok.
   Kilitli odanın ödülüne +8 altın.
6. Sınırlar gizli cepleri de kapsar (kamera / harita). Yeni dönüş alanları: `cepler`, `kilitli`, `pencereler`; ölçüm:
   `sapak`, `uzanti`, `pencere`, `cep`, `kilit`, `dal_yeri`.

### Bölüm (`scripts/world/Level.gd`) ve yeni düğümler

* **Parmaklık** (`Parmaklik.gd`): kaya karosu silinir, dövme demir çubuklar + dünya katmanında çarpışma kutusu; ardındaki
  ödülün sıcak ışığı sızar.
* **Çatlak duvar** (`KirikDuvar.gd`): kayadan açık taş örgü yaması, koyu zikzak çatlak, ışık alan kırık kenarlar,
  çatlaklardan sızan soluk Kut ışığı (yaklaşınca belirginleşir: Dead Cells'in parıldayan blokları). İki vuruş:
  `Player` her savuruşta zaten `Level.break_cracks(kutu)` çağırıyordu (boştu; v34'te dolu), patlamalar da kırar.
  Kırılınca karolar havaya döner (`Level.set_air`: ızgara, zemin karosu, komşu maskeleri, sarkan örtü, harita sisi),
  toz / duman / Kut flaşı, "Gizli cep!" yazısı, içerik cebin tabanına.
* **Kilitli kapı** (`KilitliKapi.gd`) ve **anahtar** (`Anahtar.gd`): kapı 4 karo katı, altın kilit tamgası; anahtarsız
  yaklaşınca "Kilitli: bölümde bir anahtar var"; anahtar (havada süzülen altın anahtar) alınınca kapıya yaklaşmak açar.
* **Lanetli sandık** (`Sandik.gd`, "L"): zincirli kara sandık, mor kafatası mührü, W balonu ve uyarı. Açınca üst kademe
  (+2) eşya, 14 altın, 5 Kut; oyuncu **lanetlenir**: `Level.LANET_OLDUR` (10) yaratık öldürene dek alınan her darbe
  bir kez daha düşülür (iki kat; ölümcül fazlalık `Player.take_hit` yolundan: Umay / Deli Dumrul geçerli). Lanet koşu
  içinde bölümden bölüme taşınır (`Game.run["lanet"]`), oyuncunun çevresinde mor halka ve "LANET n" yazısı.
* **Küp** (`Kup.gd`): kırılan pişmiş toprak testi (1-3 altın, %30 Kut, %5 şifa). İçinde hiçbir şey olmayan odaya 2-3,
  diğer dövüş odalarına %35 ihtimalle 1 (`_kupler_yerlestir`). Sonuç: **boş oda yok** (her odada yaratık / ganimet / küp /
  tehlike / pencere / gizli duvar).
* Kut Taşı adı: "Lanet Taşı" (lanetli sandık odası).

### Yaratık yoğunluğu (`Level._spawn_enemies`, `data/world.json` "yogunluk")

v33: dövüş odasının tabanı boyunca 15-22 karoda bir TEK yaratık (bazı dar odalarda hiç). v34: `aralik` 12-17 karoda bir
**GRUP** (derinlikle `zorluk.json` yogunluk kadar sıklaşır, en az 7); **her ana yol ve dal odasında en az bir grup**
(yerleşim denetimi ya da pazar temizliği boşaltırsa `_bos_oda_doldur` odanın içinde bir yaratık daha dener); grupların
%40'ı **karışık** (yakın dövüşçü + 3 karo içeride uzak dövüşçü: okçu / büyücü / uçan atıcı); 7+ karo yüksek odada %25
havada ek uçan; **ödül odalarında** %60 bekçi grubu (1. derinlikte %17, sonra %35 seçkin). Giriş noktasının 12 karo,
Kut Taşlarının 4 karo çevresi ve Kut Kapısı önü yaratıksız (`_yaratik_yasak`; yerleşim denetimi oraya kaydırırsa
yaratık kaldırılır); seçkin odasının bekçisi de taşın dibinden kayar. Bezirgân temizliği yalnızca pazar odasında.
Altın: yaratık sayısı ~2 kat olduğu için sıradan yaratığın altını 2-4 -> 1-2 tane (+%25 bir tane), seçkin +10 aynı.

### Harita (`Harita.gd`, `HaritaUI.gd`)

* **"?" ipuçları** (`Harita.sorular`): bir kapının (koridor / kuyu / pencere) bir yanındaki oda görülmüş, öbür yanındaki
  görülmemişse koridorun / kuyunun ortasında soluk, nabız atan soru işareti (küçük ve tam harita).
* **Kalan ganimet sayacı** (tam harita sağ üst, `Harita.sayac_metni`): "Hazine 1/6 · Tomar 0/3 · Gizli 0/2 · Kilit 0/1"
  (bulunan / toplam; hazine: kurulumdaki kaideli eşyalar, alınınca kaidede eski eşya kalsa da sayılır + lanetli sandık).
* Yeni işaretler ve lejant (iki satır): lanetli sandık, kilit, anahtar, keşfedilmedi.
* `Harita.karo_degisti`: kırılan duvar / açılan kilit / kapanan zamanlı kapı haritada yeniden boyanır.

### Bot (`Rehber.gd`)

Kalabalık bölümde yolun önündeki (80 px) yaratığa 0,22 sn'de bir saldırır (`_savas`; kapaktan inerken değil);
anahtarsız kilitli odayı hedeflemez; yolu bulunamayan ödül odasından vazgeçer (`vazgec`, eskiden aynı hedefi seçip
kıpırdanıyordu).

### Ölçüm

`--harita` (6 stil x 20 tohum = 120 bölüm; BOLUM: derinlik 1-9 x 6 = 54 tam bölüm). Önce = v33 kodu aynı tohumlarla,
aynı ölçüm kodu (yeni ICERIK satırı v33 bölümünde de çalışır).

| | v33 | v34 |
|---|---|---|
| yaratık / bölüm (derinlik 1-9, 54 bölüm) | 13,1 (10,3-16,3) | **25,9** (17,2-37,8; x2,0), grup 17,5, karışık grup ~5 |
| boş oda / bölüm | 1,81 (98 oda) | **0** |
| yaratıksız ana yol odası / bekçisiz dal odası | 84 / 7 | 0 / 0 |
| Kut Taşı dibinde / giriş dibinde yaratık | 50 / 0 | 0 / 0 |
| altın tanesi / bölüm (yerde + yaratık beklentisi + küp / cep / sandık) | ~63 (değer ~290) | ~100 (değer ~460; x1,6) |
| Kut Kapısı sapakta (ana koridorun ucunda değil) | %0 | %73 (uzantı ort. 3,0 oda, sonu ödül) |
| pencere (görünen ödül) / gizli cep / kilitli oda / lanetli sandık / küp | 0 / 0 / 0 / 0 / 0 | 1,27 (%99 en az 1) / 2,1 / 0,44 (54 bölümde 0,15) / 0,15 / 4,7 |
| oda / ana yol odası / dal | 14,2 / 11,4 / 3,0 | 15,6 / 9,2 / 3,4 |
| dalların ayrıldığı yer (ana yol sırası / uzunluk) | rastgele (~0,5) | 0,44 (yol başına ağırlıklı) |
| giriş -> Kut Kapısı yolu (karo, /koşu) | 224, 34,7 sn | 172, 26,6 sn (çıkış sapağı yolu kısaltır; keşif uzantıda) |
| ızgara / hava karosu | 165 x 46 / 2275 | 165 x 47 / 2427 (+%7) |
| erişim + dönüş, ana yol 3 karo baş boşluğu, yuvarlanma hücresi | 120 / 120, 120, 0 | 120 / 120, 120, 0 |
| geçersiz yaratık / eşya katıda / tüccar duvar / açılmayan pazar | 0 / 0 / duvar_ok / 0 | 0 / 0 / duvar_ok / 0 |
| üretim ort. / en çok | 0,55 / 1,06 sn | 0,49 / 0,76 sn |

Bot (`--otomatik --fixed-fps 60 --quit-after 9000`, `--muhur=0`): 1. derinlik v33 61,6 sn -> v34 72,6 sn'de Kut
Kapısı (keşif %79, 2 ödül odası, 3/4 taş); 3. derinlik 49,3 -> 59,8 sn; 5. derinlik 52,2 sn'de kapı (sonra 6.
derinlikte öldü: dövüşmeyen bot, v33'te de). Bot altını (topladığı; çoğunu yürürken toplar, az dövüşür): 1. derinlik
30 -> 21, 3. derinlik 25 -> 14. Tüccar fiyatları değişmedi (`data/tuccar.json` diğer dalın); tam dövüşen oyuncu için
bölüm başına ~1,6 kat altın: 1. derinlikte ~180 değer (Kut Tomarı 230, şifa 34), bir tomar için ~1,3 bölüm (v33: ~2).

### Test

* `--harita`: yeni satırlar `MERAK TOPLAM` (sapak, uzantı, pencere, gizli cep, kilit, dalların ayrıldığı yer), `ICERIK`
  (derinlik başına yaratık / grup / karışık / seçkin, boş oda, düşmansız ana yol odası, bekçisiz dal, altın tanesi ve
  değeri, pencere / gizli / kilit / anahtar / lanetli / küp, girişe ve Kut Taşına yakın yaratık), `MERAK denetim` (her
  gizli cep kırılınca cebin tabanından Kut Kapısı'na, girişten anahtara, açılan kilitli odaya yol; parmaklığın üstü kaya)
  ve `OYUN` (gerçek fizik kareleriyle: küp kırılır ve altın düşer, çatlak duvar iki vuruşta açılır, anahtarsız kilit kapalı
  kalır / anahtarla açılır, lanetli sandık açılır, darbe iki kat, 10 öldürmede lanet kalkar). Yeni denetimler: boş oda 0,
  her ana yol odasında yaratık, girişte / taşta yaratık yok, merak yolları, oynanış.
* `--harita_ekran=merak` (yeni çekim): pencere, çatlak duvar (önce / vuruş / açıldı), kalabalık oda, iki biyomda yarı ve
  tam keşfedilmiş tam harita.
* Sonuç: `--harita` (20 tohum / 6 bölüm) GECTI; `--isinlan`, `--konak`, `--tuccar --muhur=0` GECTI (`--konak` bir koşuda
  Usta'nın kalite hizmetinin rastgele +4'ünde KALDI, yeniden koşuda GECTI: harita dışı, Usta kalite aralığı);
  `--otomatik --derinlik=1/3/5 --muhur=0` (`--fixed-fps 60 --quit-after 9000`) Kut Kapısı'na varır; `--zeka --muhur=0`,
  `--mekanik --muhur=0` BITTI; `--piksel_tara --otomatik --derinlik=3` TOPLAM 0; `--yurt --yurt-tur` kapıya varır.
  Bütün koşularda SCRIPT ERROR 0 (yalnız motorun çıkıştaki RID sızıntısı satırları, eskiden beri).

### Görseller (`docs/v34/harita/`)

`pencere_parmaklik.jpg` (ana yol odasından parmaklık ardındaki hazine; sağ altta küçük haritada "?" ipuçları),
`gizli_0_catlak.jpg`, `gizli_1_vurus.jpg`, `gizli_2_acildi.jpg` (çatlak duvar, ilk vuruş, açılan cep ve altın),
`kalabalik_oda.jpg` (Kaf: dalıcı kartal + iki kalkanlı bekçi), `tam_yari_bozkir.jpg` / `tam_yari_sahmeran.jpg` (ana
yolun 2/3'ü gezilmiş tam harita: "?" ipuçları ve "Hazine 0/6 · Tomar 0/3 · Gizli 0/2 · Kilit 0/1" sayacı),
`tam_hepsi_bozkir.jpg` / `tam_hepsi_sahmeran.jpg` (bütünüyle keşfedilmiş: sapaktaki Kut Kapısı, uzantı, kilit, lejant).

### Bilinen

* Lanet, Dead Cells'teki gibi "tek darbe ölüm" değil, iki kat hasar (bot ve ilk derinlikler için okunur bir risk).
* Parmaklığın ve çatlak duvarın görseli çizimdir (karo atlasında karşılığı yok); açık gök stillerinde parmaklığın üstündeki
  kaya koyu iç doku olarak görünür.
* Pencere dalı yatay komşuluk ister; 2 satırlı Bozkır'da bazen yalnızca doğrudan (ara odasız) dolaşma bulunur.
* Bot gizli duvarları kasıtlı aramaz (yalnızca yolda savururken rastlantıyla kırar), anahtar aramaz.

## v34 birleştirme denetimi (hareket34 + tomar34 + harita4)

Üç dal (`v34-hareket34` zıplama / Kahraman İnişi / ağır silah, `v34-tomar34` yeni tomar / Bezirgân oranları,
`v34-harita4` merak uyandıran bölümler / yoğunluk) `main`'de birleşti; dallar arası etkileşimler sınandı ve giderildi:

* **Yüksek düşüş sersemlemesi her bölümde zorunluydu** (`Player.HERO`): ana yoldaki kuyular 10-15 karo; 12 karo eşiğiyle
  ana yolda 13-15 karoluk düşüş 72 bölümün 55'inde vardı (yürüyerek düşen oyuncu her bölümde sersemliyordu). Ölçüm
  (`--harita` yeni `DUSUS` satırı, 120 bölüm): ana yol düşüşleri 3-15 karo, en uzun 15. Eşik `stun_h` 288 -> 408 px
  (17 karo), hasar `dmg_h` 432 -> 552 px (23 karo): ana yoldan yürüyerek düşen hiç sersemlemez (0 / 120), derin kuyuya
  zıplayarak girmek ya da yol dışındaki çok yüksek düşüş sersemletir; Kahraman İnişi hız (13 karo 0,35 / 0,63 sn) ve şok
  dalgasıyla ödül olarak kalır. Yeni denetim: ana yolda sersemleten düşüş bölümlerin en çok %10'unda. `--zipla`: 10 / 13 /
  15 karo sersemletmez, 18 karo 0,43 sn sersem (hasarsız), 24 karo 0,58 sn + 6,5 hasar.
* **Platformdan inişte iki platform birden geçiliyordu** (`Player.DROP_MASK`, `DonForm`): aşağı + zıplamada tek yönlü
  platform çarpışması 0,25 sn kapalıydı; v34 düşüş yerçekimiyle (2100) bu sürede ~65 px düşülüyor, 2 karo alttaki
  platform (kuyu tırmanış bacasının ara basamağı) da geçiliyordu. Erişim modeli (`_moves`: dikine iniş ilk tutunulacak
  yere dek) ile gerçek oyuncu ayrışıyordu (gerçek fizik testi 8. derinlikte bir ödül odasını "erişilemez" buldu). Çarpışma
  artık yalnız ilk 0,1 sn kapalı (~12 px, 6 px kalın platformu geçmeye yeter); 0,25 sn'lik `drop_t` yalnız Kahraman
  İnişi'ni engellemeye devam eder.
* **Gerçek oyuncu fiziğiyle erişim** (yeni `tools/tests/erisim_testi.gd`: `--harita --harita_fizik [--fizik_bolum=N
  --fizik_bas=K]`, `--fizik_tek=d,tohum,ax,ay,bx,by` kare izi): 120 tam bölümde (derinlik 1-9) girişten Kut Kapısı'na, her
  ödül odasına ve Kut Taşı'na, ve her birinden Kut Kapısı'na model yolu çıkarılır; her hamle (düz yürüme dışında) gerçek
  `Player` hamlenin başına konup tuşlara basılarak (yürü, zıpla, çift zıpla, kenardan / hedefe yürüyüp zıpla, platformdan
  in ...) denenir; yapılamayan model hamlesi yasaklanıp yol yeniden aranır. Sonuç: **1836 hedefin 1836'sı erişilir**
  (0 erişilemez); 44 006 model hamlesi, 13 479 benzersiz geometri. Gerçek oyuncunun yapamadığı 219 model hamlesi var
  (%1,6; çoğu 3-5 sütun yana + 2 karo aşağı düşüş ve 5 sütunluk uzun zıplama: model iyimser) ama her birinin yanında
  başka bir gerçek yol var. Koşu zıplamasının kısalması (95,6 px) erişimi bozmuyor.
* **Kahraman İnişi küpleri ve çatlak duvarı görmüyordu** (`Player._hero_land`): şok dalgası artık `Level.break_cracks`
  çağırır (yarıçap 56 + 44k px, ±44 px): küpler kırılır, yanındaki çatlak duvara bir vuruş sayılır (duvar yine iki
  vuruşta açılır). Ağır silahlar yeni tempoda da her etkin karede `break_cracks` çağırıyor. `--harita` OYUN'a gerçek
  girdiyle iki denetim: Ulu Kılıç savuruşu çatlak duvarı iki basışta açar; havada S + Boşluk küpü kırar.
* **Lanet çift sayımı** (`Level._lanet_tick` kaldırıldı, `Player.take_hit`): lanet her can kaybını (zehir tıkı, yüksek
  düşüş hasarı dahil: ikisi de öldürmez) sonradan bir kez daha düşüyor, fazlalık ölümcülse aynı karede ikinci bir zorlu
  `take_hit` yapıyordu (iki sarsılma; zehir / düşüş lanetle öldürebiliyordu). Şimdi yalnız darbe, `take_hit` içinde
  tek geçişte iki kat (mor sayı); dokunulmazlık (Kahraman İnişi'nin 0,2 sn'si dahil), Umay ve Deli Dumrul aynı yoldan.
  OYUN: darbe 10 -> 20, zehir tıkı 2 -> 2.
* **Haritadaki tomar işareti** (`HaritaUI._glyph`): eski muska simgesi yerine yeni kayın kabuğu tomarın `ui_tomar`
  simgesi (`TomarV2.ui`; yoksa eski simge); lejant da aynı. Tam harita sayacı (`Harita.sayac_parcalari`) her parçanın
  önüne haritadaki işaretini çizer (Hazine: eşya, **Tomar: ui_tomar**, Gizli: yeni çatlak duvar simgesi, Kilit);
  tamamlanan parça soluk.
* **Bezirgân fiyatı / yeni altın** (`data/tuccar.json` "taban" 60 / 46 / 52 -> 75 / 58 / 65): tuccar testinin bölüm altını
  eski formülle (yaratık başına 2-4 tane, v25 "T" hazinesi) hesaplanıyordu; artık harita testinin içerik ölçümünden
  (`harita_testi.icerik`: yaratık 1-2 tane, küp / gizli cep / lanetli sandık / kilitli oda) + boss, 6 tohum. Yoğunluk
  sonrası iyileşen silahın fiyatı / bölüm altını ort. 0,75'e inmişti (bölüm başına ~1,3 iyi mal); fiyat x1,25 ile
  **0,90: bölüm başına 1,1 iyi mal, bir bölüm biriktirince 2,2** (ORAN satırları 0,73-1,15). Yeni denetim: oran 0,8-1,25.
* **`--sanat` ara sıra KALDI** (`sanat_testi`): kombo sınırı gerçek kare sayısıydı (150); vuruş duraklaması ve kritik
  ağır çekimi (Engine.time_scale < 1) koşudan koşuya değişiyor. Ölçüm (yeni "oyun zamanı" sayacı, 7 koşu): Tulpar
  Dörtnalı oyun zamanı her koşuda 122-124 kare, gerçek 141-157; Yıldırım Ağı 95 / 112-151. Sanatlar zamanında bitiyor
  (yeni zıplama / düşüş fiziği değiştirmedi); sınır artık oyun zamanında 150 kare, gerçek karede +30 duraklama payı (180).
* **`--konak` ara sıra KALDI** (test hatası): Usta'nın kalitesi %100'de kenetlenir (`Usta._kalite_ekle`); %96'dan +4
  doğru sonuçtu, test 5-15 bekliyordu. Beklenti `min(5, 100 - kalite)`..15.
* Sonuç (headless, betik hatası 0; yalnız motorun çıkıştaki RID sızıntısı satırları): `--harita` (20 tohum, 120 bölüm)
  GECTI; `--harita --harita_fizik` (120 bölüm) GECTI; `--isinlan`, `--konak` (3 + 5 koşu), `--sanat --boss --muhur=0`
  (3 + 4 koşu), `--tuccar --muhur=0`, `--tomar --boss` GECTI; `--mekanik --zipla --boss` OZET hata=0; `--dovus --boss
  --kontrol` TAKILMA=0, basılmamış 0; `--dovus --boss --agir` tablo değişmedi; `--otomatik --muhur=0` derinlik 1 / 3 / 5
  35 / 55 / 93 sn'de BOLUM_SONU (ölüm 0), `--derinlik=3 --bot_gercek` 92 sn; `--zeka`, `--mekanik --muhur=0` BITTI;
  `--piksel_tara --otomatik --derinlik=3` TOPLAM 0; `--yurt --yurt-tur` kapıya varır.
* Bilinen: erişim modeli (`_moves`) gerçek zıplamadan biraz iyimser (yukarıdaki 219 hamle; hedefler yine erişilir);
  Rehber bot 5. derinlikte çok hasar alır (dövüşmeyen bot, eskisi gibi); bir `--otomatik --derinlik=5` koşusu yüklü
  makinede 13 sn'de çıktı (CIKIS, betik hatası yok), yeniden koşuda 93 sn'de BOLUM_SONU.

## v35: vahşet — parçalanma, kalıcı cesetler, sesler

> v36'da parçalanma / kalıcı ceset yolu ve vahset_olum / yirtil / dusme sesleri kaldırıldı: bkz. "v36: Dead Cells tarzı ölüm patlaması".

İstek: "Düşmanlar ölünce parçalara ayrılsın, kanlı gövdeleri yerde kalsın; vuruş sesleri de vahşet olsun. Kritik sesini hâlâ
beğenmiyorum, düz METAL bir ses olsun (Dead Cells'teki gibi ama kopya değil)."

### Parçalanma (`scripts/core/Gore.gd`, `Enemy._die`, `Enemy._gore_power`)

* Ölen yaratığın o anki sprite karesi öldürücü darbe yönünde kesilir: ana kesik darbe yönünde (±20°) gövdenin ortasından,
  sonra üst parçadan baş, alt parçayı bacaklara ayıran dik kesik, 4.+ kesikler en büyük parçadan (kol / omuz). Kesikler
  dokunun opak sınır kutusu içinde (maske `Gore.warm` ile yaratık kurulurken hazırlanır, ilk öldürüşte takılma yok); boş
  köşe parçaları atılır. Her parça dokuyu taşıyan bir `Polygon2D`; fizik tek düğümde toplu (yerçekimi, döşeme / tek yönlü
  platform, duvar, tavan, en çok iki sekme, sürtünme, dönüş). RigidBody yok.
* Güç (`_gore_power`, 0,7..3): 1 + aşırı hasar × 0,7 (+0,6 kritik, +0,5 ağır / itme ≥ 250, -0,3 zehir / tuzak, +0,3
  seçkin, +0,6 boss). Parça sayısı 3 + (güç-1)×1,6 → 3-6 (boss 6). Büyük vuruş = daha çok parça, daha uzağa.
* Etli parça uçarken kan izi bırakır, duvara hızla çarpınca iri mürekkep lekesi + akıntı (`Blood.splat`), yere düşünce
  leke + `vahset_dusme`. Ölüm fışkırması (Blood.burst) güçle %40'a kadar artar.
* Malzeme (`Gore.material_of`): etli → kanlı parçalar; `Gore.TAS` (balbal, bekci, buz_balbali, cini_golemi, agac_iyesi) →
  taş / tahta yığını (kan yok, toz, `darbe_tas`); öbür NOT_FLESH (ruh, ateş) → eski kor kenarlı çözülme + yükselip sönen
  üç mürekkep tülü / kor parçası.
* Boss: v29 ölüm satırı oynar, 1,4 sn sonra son karesinden 6 parçaya ayrılır (güç 2,6, büyük fışkırma, sarsıntı).

### Kalıcı cesetler

Parça durunca donar (işlem listesinden çıkar, yalnızca statik çizim) ve rengi 6 sn'de koyulaşır; etliyse altında kan
göllenir (gövde 2,5-4 sn, uzuv 0,8-1,8 sn boyunca 0,12-0,3 sn'de bir leke; `Blood` lekeleri birleşip büyür). Cesetler
bölüm boyunca kalır: en çok 60 öldürüş / 200 parça, aşılınca en eski öldürüşün parçaları 1,2 sn'de söner. Etli yaratıkta
eski ceset çözülmesi (`Corpse`, v29 ölüm kareleri) artık oynamaz; parçalanma yapılamazsa (doku yok) eski yol.

### Vahşet sesleri (`tools/audiogen/v35.py`)

| ses | içerik | nerede |
|---|---|---|
| `vahset_et_1..4` | Kenney impactPunch/Soft (perde 0,75-0,95) + ıslak şapırtı + alt gövde | her vuruş, etli yaratık (-6 / büyükte -2,5 dB) |
| `vahset_kemik_1..4` | sıkışık tık dizisi + impactWood_light (perde 0,7) + çatırtı | büyük / ağır / kritik vuruş, öldürüş |
| `vahset_olum_1..3` | alt güm + iki dalga ıslak sıçrantı + kemik kırılması | öldürüş (güçle +2 dB) |
| `vahset_yirtil_1..3` | gerilen lif gürültüsü (500 → 2600 Hz) + knifeSlice + kopma + şapırtı | parçalanma |
| `vahset_dusme_1..4` | tok ıslak "şlap" | parça yere düşer |

Ses.LIMITS "vahset": 6. Kaynaklar: yalnızca yereldeki CC0 Kenney kayıtları + sentez (`assets/audio/LICENSES.txt`).

### METAL kritik (`v35.crit_metal`, `darbe_kritik_1..3`, `darbe_kritik_kunt_1..3`)

v26 / v27'nin yumruk, kirli doyurma ve alçak gövde katmanları kaldırıldı. Yeni ses: 3 ms çelik tıkı + 6 kHz üstü "tss";
11 → 5 kHz kayan tarak süzgeçli sıyırma ("şiiing", 35-70 ms); çan / plaka kipleri (oranlar 1, 1,18, 1,51, 2, 2,51, 2,66,
3,01, 4,17, 5,43; alt kipler 0,8-1,1 sn, üstler 0,15 sn T60), vuruşta perde %1,5-2,5 düşer, her kip 4-9 Hz dövünür
(pırıltı); karşı bıçak (×1,31, kısa), kısa "klang" gövdesi (×0,42, 0,14 sn), küçük metal oda + tiz oda kuyruğu. 0,68 sn.
Üç çeşit ölçüldü (`python tools/audiogen/v35.py --olc <png>`, `docs/v35/vahset/kritik_spektrogram.png`):

| çeşit | temel | 1-5 kHz | 5k+ | merkez | kuyruk (0,2-0,5 sn / geçiş) |
|---|---|---|---|---|---|
| A şiiing | 2380 Hz | -0,5 | -9,6 | 3631 Hz | -23,1 dB |
| B KLANG | 1960 Hz | -0,9 | -8,5 | 2962 Hz | -21,1 dB |
| **C tiz çın** | 2720 Hz | -1,4 | -5,7 | 4117 Hz | **-16,8 dB** |

Üçü de çeşit olarak çalar (`darbe_kritik_1..3`); tek dosya isteyen yer için `darbe_kritik` = C (en parlak, en uzun
pırıltılı çınlama). Künt çeşit aynı tasarımın ×0,72 alçak sürümü (örs gibi ama metal). v27'nin `darbe_kritik_4/5`,
`darbe_kritik_kunt_4` dosyaları kaldırıldı. Yönlendirme değişmedi (Krit veri yolu, `krit_duck`, tüm kritik yolları
`Ses.hit(2)` üzerinden). Player.gd'ye dokunulmadı.

### Test (`tools/tests/vahset_testi.gd`, `-- --vahset [--vahset_cek=<klasör>] [--vahset_cik]`)

Üç öldürüş şeridi (sıradan / kritik / ağır + 3× aşırı hasar), 5 dalga × 8 = 40 öldürüş başarımı, ceset odası görüntüsü.
Görüntüler: `docs/v35/vahset/serit_siradan.png`, `serit_kritik.png`, `serit_agir.png`, `oda_cesetler.png`.

* Başarım (40 öldürüş, 177 parça kalıcı; aynı anda 8 canlı yaratık): headless 80 fps, ortalama kare 12,1 ms, en kötü
  27,9 ms; pencereli 1280×720 (4K yakalama dokusu) ~43 fps (ortalama 25 ms; aynı sahnede parçasız taban ölçülmedi).
  Duran parçalar işlem dışı: dalga sonunda hareketli parça 0-7.
* `--dovus --boss --kontrol`: TAKILMA=0, basılmamış=0, oto_dönüş=0, istenmeyen_ağır=0. `--otomatik --derinlik=1/3
  --muhur=0`, `--sanat --boss --muhur=0` (GECTI hata=0), `--piksel_tara` (TOPLAM 0): betik hatası 0.

### Bilinen

* Kesik yüzeyine ayrı "et" boyası yok; parça dokusu olduğu gibi, biraz kızıla çekilmiş ve zamanla koyulaşır.
* Koyu sahnelerde koyu yaratık parçaları az seçilir (kan lekeleri ve izler okunur).
* Parçalar yalnızca döşeme ızgarasıyla çarpışır (kırık duvar / kapı gibi düğüm engellerinden geçer).

## v35: sanatsal kombolar

Geri bildirim: "Silah kombolarından hâlâ tatmin olmuyorum. Çok sanatsal, çok güzel görünen ve iyi hissettiren bir şey olmalı."

Ön çekimde (`docs/v35/kombo/once_serit.jpg`) zincir bitirişi ara vuruşlardan ayırt edilmiyordu: aynı hilal, aynı
sıçrantı, +0,02 sn duraklama; hançer ve mızrak bitirişi kıvılcımların altında kayboluyordu. Hedef (Dead Cells / Hades /
Shinobi / Ōkami): ara vuruşlar sade ve keskin, gösteri yalnızca bitirişte; bitiriş "ayrı bir olay" (beklenti parıltısı →
hüsnühat kesiği → uzun duraklama + yakınlaşma + yönlü sarsıntı → düşman savrulur).

* **Hüsnühat kesiği** (`scripts/core/KesikFX.gd`, yeni): bitiriş isabetinde hedefin üstüne sumi-e fırça darbesi. 13 kıl
  şeridi (her kılın enine yeri, titreşimi, bitişi, tonu ayrı): kenar kılları ve rastgele damarlar sumi, içtekiler sınıf
  vurgusunda; başta yuvarlak ıslak göl ("tome"), kuyrukta kıllar ayrı ayrı kopar (kuru fırça / kasure). 0,06 sn'de çizilir,
  ilk iki kare bıçak ağzında ak-sıcak hat, 0,3 sn kalır, kurudukça koyulaşır, 0,12 sn'de söner. Kuyrukta darbe yönünde
  damlalar, merkezde ucu damlalı kısa ışınsal mürekkep dikenleri. Gerçek zamanlı (duraklamada ve ağır çekimde de akar).
* **Sınıf imzası** (`KesikFX.SINIF`, `Player._tempo_class` ile bütün silahlara):

  | Sınıf | Kesik | Vurgu |
  |---|---|---|
  | kılıç | baş üstünden çapraz hilal | vermilyon |
  | düello (yatağan, rüzgâr) | uzun ince yatay iai çekişi | açık kızıl |
  | hançer | iki kesişen darbe (çarpı, ikincisi 0,045 sn sonra) | koyu kızıl |
  | mızrak | uzun düz deliş + iki ince hız teli | aşı boyası altın |
  | uzun sap | geniş yatay hilal | kızıl turuncu |
  | ağır / dev | dik yarma + yerde kısa sürüntü, en kalın | kor turuncu |
  | kırbaç | kıvrık S darbe | vermilyon |

  Silahın kendi WFX rengi vurguya %35 karışır (Ayaz mavisi, Ruh yeşili kimliğini korur).
* **Bitiriş hissi** (`Player._finisher_fx`): kesik + küçültülmüş sıçrantı (eski büyük sıçrantı ve halka kaldırıldı: üst
  üste binmesin), yakınlaşma 0,05 (ağır / dev 0,025) + ağırlık, vuruş yönünde sarsıntı (0,32 × ağırlık) ve kamera itişi,
  hafif düşman `V35.fin_firlat` (150) ile havaya savrulur (boss hariç; ağır / uçan / zırhlıyı Enemy eler), öldürüşte
  0,12 sn ×0,35 ağır çekim. Darbe karesi (ImpactFrame) bilerek eklenmedi: beyaz silüetler kesiği örtüyordu (denendi).
* **Beklenti**: bitiriş savuruşu hazırlıktan süpürmeye geçtiği karede bıçak ucunda kısa dört kollu iğne parıltısı
  (`KesikFX.parilti`, sınıf vurgusu + ak).
* **Vuruş duraklaması kademeleri** (`V35`): hafif ara vuruş 0,03 (hançerde ×0,75) · orta (ağır silah ara vuruşu, büyük
  itiş) 0,05 · bitiriş / büyük 0,09 · kritik +0,03 · öldürüş +0,02 · en çok 0,12. Ağır / dev ara vuruşları v34'teki gibi
  ×1,2 (bitiriş tavanı aşmasın diye bitirişte değil). Eski `V19.fin_hs` ekinin yerini bitiriş kademesi aldı.
* **İz**: sınıf iz eni (hançer ×1,2, mızrak ×1,15, düello ×1,1: kısa bıçak izleri okunur) ve bitiriş izi ×1,15 + 2 fiske.
* **Tempo değişmedi**: savuruş süreleri / SWINGS / COMBOS aynı. `--dovus --boss --agir` tablosu v34 ile birebir (ör. gürz
  ilk temas 200 ms, tur 1354 ms; Ulu Kılıç 247 / 1270 ms).

Test: `--dovus --boss --kontrol` TAKILMA=0, basılmamış=0, oto_dönüş=0, istenmeyen_ağır=0; `--dovus --boss --agir` v34
ile aynı; `--sanat --boss --muhur=0` SONUC GECTI hata=0 TAKILMA=0; `--otomatik --derinlik=1 --muhur=0` betik hatası 0;
`--piksel_tara` TOPLAM 0. Hiçbir koşuda SCRIPT ERROR yok.

Görseller (`docs/v35/kombo/`): `once_serit.jpg` / `sonra_serit.jpg` (Alp Kılıcı, Ulu Kılıç, Kargı, İkiz Bıçak tam zincir;
kırmızı çerçeve temas, sarı çerçeve BITIRIS), `bitiris_once.jpg` / `bitiris_sonra.jpg` (her silahın bitiriş teması, +1 ve
+3 çekim), `bitiris_ortasi_ulu_kilic.jpg`. Çekim: `--fixed-fps 60 -- --dovus --boss --agir_klip=<silah> --anlik=<klasör>`.

Bilinen: kesik dünya uzayında (hedefle birlikte kaymaz, yerinde kurur); kalabalıkta her bitiriş tek kesik çizer (yalnızca
ilk isabet). Hançer çarpısı çok yakın düşmanda oyuncunun üstüne taşabilir.

## v35 birleştirme denetimi (vahşet + kombo)

İstek: "Düşmanlar parçalansın, yerde KANLI gövdeler kalsın." Ek geri bildirim (test izlenirken): "Parçalanma kâğıttan
kesilmiş gibi, dümdüz. Rastgele yerlerden kopsun, gövde yırtılsın, iyi gölgelensin; 3B et yığını gibi görünsün."

* **Yırtık, düz kesik değil** (`Gore._cut_all`, `_jag`, `_tear`): ana yırtık darbe yönünde (±30°), sonrakiler çoğunlukla en
  büyük, bazen rastgele bir orta boy parçadan, rastgele nokta ve açıyla (hep baş / bacak / kol değil). Kesik kenarları
  ~1,6 dünya px'te bir bölünüp iki dalga + seyrek sivri lif uçlarıyla (±1,5 px, uçlar ×2,4) kırılır; iki yan aynı yırtık
  işlevini kullanır (birbirini tamamlar). Parça sayısı 4-8 (eskiden 3-6).
* **Hacim** (`PARCA_SHADER`): parça kendi üçgenlemesiyle (dış halka + ~3,6 px içeride iç halka + merkez) çizilir; köşe
  rengi veri taşır (r: yırtığa yakınlık, b: et / taş). Kesit: koyu kızıl kenar → çiğ kırmızı et (lifli gürültü) → pembe
  yağ şeridi → yırtığa yakın deri gölgesi. Ekranın yukarısı doku uzayında `-dFdy(UV)`: parça dönse de üst kenarda cel
  ışık bandı + ıslak parlama, altta iki cel gölge bandı, ince kenar ışığı. Arkada 0,8 / 2,6 px kaymış koyu kızıl "yan yüz"
  kopyası (kalınlık), durunca yerde yumuşak gölge. Uzuvların çoğunda en uzun yırtıkta fildişi kemik + koyu ilik noktası.
  Taş yaratıkta kesit açık taş grisi (kan yok). Ruh / ateş parçaları değişmedi.
* **Ek parçalar** (`Gore._gibs`): et topakları (küre cel ışık + parıltı + kontur), ağır / kritikte 1-2 bağırsak / sinir
  şeridi (iki katman Line2D), 1-3 kemik kırığı; boss'ta fazlası. Yere inince ezilip titrer (elastik), dikilip kalmaz:
  en yakın yatık duruşa devrilir / yuvarlanır, alt ucu zeminde kalır; altında kan göllenir.
* **Koyu biyomda okunurluk** (`Blood._tone`, `Blood.telafi_of`, `ink_blood.gdshader`): kan daha doygun ve canlı (%3-15
  koyulaşır, eskiden %12-30); gece ortam ışığı (CanvasModulate kırmızısı Yurt / Ötüken'de ~0,32) kanı ve eti siyaha
  bastırıyordu, kan ve et gölgelendiricileri rengi `0,6 / ortam.r` katıyla (1-1,9) önceden yükseltir. Leke ortasında
  küçük parlak ışık lekesi; kuruma tabanı 0,12 → 0,34 (kurumuş kan koyu kızıl kalır). Göl: gövde 5-8 sn, uzuv 1,5-3 sn
  kanar, birleşen leke en çok 24 px (15), durunca gövdenin altına hemen üç iri leke.
* **Bitiriş → parçalanma**: Player bitiriş vuruşunda `opts.kesik_yon = KesikFX.ana_yon(sınıf, yön)` (ilk fırça
  darbesinin kirişi) verir; Enemy._die ilk yırtığı tam bu açıda gövdenin ortasından atar (dik yarma da), parçalar
  `opts.launch`'u yukarı ek itki olarak alır, güç +0,3. Ağır çekim (0,12 sn ×0,35) parça fiziğini de yavaşlatır.
* **Kritik öldürüş sesi**: metal kritik Krit veri yolunda ve konumsuz havuzda (24 ses); vahşet sesleri konumlu havuzda
  (16, "vahset" sınırı 6): birbirini kesmez. Kritik öldürüşte vahşet ölüm katmanı 2,5 dB kısık ve ikinci kemik
  çatırtısı yok (vuruştaki kemik zaten çaldı): kritik krit_duck'la üstte okunur, Master sınırlayıcısı pompalanmaz.
* **Test**: `--vahset` artık test bayraklarında (eskiden Yurt'ta başlıyordu; `--derinlik=` biyomu seçer, gece Yurt için
  `--yurt`). Yeni şeritler `bitiris` (sıçrayan tazı, ağır yarma) ve `bitiris_kilic` (kara böri, çapraz hilal);
  `yakin_<şerit>_<kare>.jpg` yakalama çözünürlüğünde yakın çekim, `tam_*.jpg` tam ekran.

Ölçüm (`--vahset --derinlik=1 --tohum=7`, 40 öldürüş + 5 şerit, en çok 280 parça): headless ortalama kare 7,2 ms, en kötü
22,6 ms (önce 12,1 / 27,9). Pencereli 1920×1080 (4K yakalama dokusu) ~27 fps / 41 ms (önce ~43 fps / 25 ms; aynı anda
dört headless test koşuyordu, kesin karşılaştırma değil). `--dovus --boss --kontrol` TAKILMA=0, basılmamış=0,
oto_dönüş=0, istenmeyen_ağır=0; `--sanat --boss --muhur=0` SONUC GECTI hata=0; `--otomatik --derinlik=1/3 --muhur=0`,
`--piksel_tara` (TOPLAM 0): betik hatası 0.

Bilinen: parçalar hâlâ yaratık sprite'ının kendisi (gerçek 3B değil, gölge sahte); taşıyıcı nesnelerin (küp, çömlek)
üstünde durabilir; pencereli başarım parça gölgelendiricisiyle düştü (çok parçalı sahnede 4K yakalamada), gerekirse
`MAX_PIECES` (280) düşürülür. Taş / tahta yaratıkta kesit boyası yalnızca açık taş grisi.

## v36: Dead Cells tarzı ölüm patlaması

İstek: "Hiç beğenmedim, 2B bir nesne yırtılmış gibi duruyor. Dead Cells'te düşman ölünce kan yoğun ve parça parça
fışkırıyor, 'dışşkk' diye bir ölüm sesi çalıyor, gövde anında yok oluyor, parçalar saçılıyor, o kadar."

### Patlama (`scripts/core/Gore.gd`, `Enemy._die`, `Boss._v29_death`)

* v35'in sprite dilimleme yolu (Polygon2D parçalar, et gölgelendiricileri, kalıcı cesetler, parça sınırı, `Gore.warm`)
  tamamen kaldırıldı. Ölümde gövde anında kaybolur (uçan ceset / `_ds_death` / çözülme yok).
* `Gore.burst(merkez, yarı_boy, yön, güç, renk, malzeme, ölçek)`: gövde silueti içinden sıkışık patlama.
  - et: (44 + 26·(güç-1))·ölçek küçük düzensiz kan topağı (dönen iki dörtgen + üst-solda ışık kıyısı; Dead Cells
    örneğindeki gibi koyu kızıl / kırmızı / parlak kırmızı / kırmızı-pembe / pembe), 3-9 iri et topağı,
    (44 + 30·(güç-1))·ölçek ince damla (hızla uzar) ve kısa kan buğusu;
  - taş (`Gore.TAS`): gri moloz kırıntısı (yere iki kez seker, 4-7 sn kalır) + toz; ruh: mürekkep / ektoplazma tülü
    (yukarı süzülür, genişleyip söner); ateş (`Gore.KOR`: sihirli_kandil, isilti_bocegi): titreyen korlar + duman.
* %65'i öldürücü darbe yönüne eğilimli, hepsi yukarı itkili; yerçekimi + hava direnciyle yay çizer. Güç
  `Enemy._gore_power` (aşırı hasar, kritik, ağır vuruş; bitiriş +0,3), ölçek seçkin 1,4, boss 2,2 × 3 dalga.
  Bitirişte yön KesikFX'in ana kesik yönü + savurma (opts.kesik_yon / launch).
* Zemine düşen topak küçük yassı leke (8-15 sn), damlaların %35'i leke (4-8 sn), duvara çarpan duvar lekesi (3-6 sn);
  lekeler son 1,5 sn'de söner, en çok 600 (dolunca en eskinin yerine). Renkler `Blood.telafi_of` ile gece ortam
  ışığına karşı yükseltilir (Ötüken / Şahmeran'da kırmızı okunur).
* Ölüm sırası olan boss: Enemy._die patlamaz (`v36_gec_patla`), ölüm satırının son karesinden sonra gövdenin üç
  noktasından dev patlama + iki ağır "dışşkk", gövde gizlenir.
* Başarım: bütün zerreler tek düğümde paralel dizilerde, çizim tek üçgen dizisi (önceden ayrılmış diziler, sabit dizin
  kalıbı); lekeler ayrı tuvalde, yalnızca değişince / 4 karede bir yeniden çizilir.

### Ses (`tools/audiogen/v36.py`)

| ses | yapı | nerede |
|---|---|---|
| `vahset_patla_1..4` | 3 ms tık + Kenney impactPunch (perde düşük, doyurulmuş) + alt güm + ıslak şapırtı + tiz ıslak hışırtı ("şş", ~0,26 sn) + kuyrukta kısa çıtırtı ("kk"); ~0,27 sn | sıradan etli öldürüş |
| `vahset_patla_agir_1..3` | aynısı, daha dolgun alt, daha uzun hışırtı (~0,37 sn) | kritik / bitiriş / seçkin / boss |
| `vahset_et_1..4` | v35 etli darbe, geçiş vurgusu artırıldı, 0,22 sn | her vuruş (etli) |

`vahset_olum`, `vahset_yirtil`, `vahset_dusme` silindi; vuruştaki `vahset_kemik` ve metal kritik korundu. Kritik
öldürüşte patlama sesi 2 dB kısık (metal üstte okunur). Kaynaklar: sentez + yerel CC0 Kenney kayıtları.

### Test (`tools/tests/vahset_testi.gd`, `-- --vahset [--vahset_cek=<klasör>] [--vahset_boss] [--vahset_cik]`)

* Şeritler (0 / 0,05 / 0,1 / 0,2 / 0,4 / 0,8 sn, duvar saati; ilk kareler vuruş duraksamasında): sıradan, kritik,
  bitiriş, seçkin, taş; `docs/v36/gore/serit_<ad>_<biyom>.jpg` (otuken, sahmeran), boss: `serit_boss_otuken.jpg`,
  Dead Cells örneğiyle yan yana: `karsilastirma_deadcells.jpg`.
* 40 öldürüş (8'lik dalgalar, 8 öldürüş art arda 8 fizik karesinde): tepe ~1000 canlı zerre; Gore'un kendi kare maliyeti
  (fizik + çizim + leke) çoğu karede < 0,5 ms, tepe ~5-7 ms (8 eşzamanlı patlamanın hemen ardından, bu yavaş test
  makinesinde; oyunun kendi ortalama karesi aynı makinede ~27-33 ms); tek patlama kurulumu ≤ 0,7 ms. Boss patlaması:
  ~1200 zerre, fizik 1,3 ms + çizim 2 ms.
* `--dovus --boss --kontrol`, `--sanat --boss --muhur=0` (GECTI), `--otomatik --derinlik=1/3`, `--piksel_tara`
  (TOPLAM 0): betik hatası 0.

## v37: kılıç çarpışması kritik, duyulur ölüm sesi, daha çok kan

Oyuncu geri bildirimi: "kritik sesi metal değil, tencere / tava vurmak gibi; kılıç çarpışması istiyorum", "öldürünce 'dışşkk'
gelmiyor (Dead Cells'e yakın olsun)", "sıradan yaratıklarda kan biraz daha çok olsun".

**Kritik = kılıç çarpışması** (`tools/audiogen/v37.py`; `darbe_kritik_1..4`, `darbe_kritik_kunt_1..3`, `olum_vurus_1..2`):
* Neden tava gibiydi: v35'in kritiği çan / plaka kip oranlarıyla (1; 1,18; 1,5; 2; 2,5 ...) 2-3,5 kHz'te SIK dizilmiş kipler +
  ~1 kHz "klang" gövdesi ve 0,5-0,8 sn çınlamaydı: kulak bunu gövdeli bir kabın çınlaması olarak duyar. (Ağırlık merkezi zaten
  3-4 kHz'ti; sorun parlaklık değil kip yoğunluğu ve uzun gövde çınlamasıydı.)
* Yeni tasarım: 2 ms tık + Kenney impactMetal_light (perde yukarı, 900 Hz altı kesik: gerçek çelik geçişi, gövdesiz) + iki
  ince bıçak (çubuğun SEYREK inharmonik kipleri 1 : 2,76 : 5,40 : 8,93; temel 2,65-3,6 kHz, 0,12-0,35 sn) + tiz seyrek
  pırıltı (4-9 kHz, biri uzun ve çok sessiz) + sıyırma: OGA sword-unsheathe kaydı (2 kHz üstü, 110 ms) + sentez 9 → 4,5 kHz
  sıyırma; yalnızca erken yansımalı minik oda; sonda 700 Hz dik alçak kesim. Künt çeşit: bıçaklar x0,8, kısa gövdesiz "çank"
  (900 Hz üstü gürültü vuruşu) + çıtırtı; tava gövdesi yok. `olum_vurus`: aynı çarpışmanın kısa (0,4 sn), kısık çeşidi.
* Ölçüm (ilk 0,35 sn): ağırlık merkezi eski 2961-4114 Hz → yeni 4418-5579 Hz (künt 2994 → 5166 Hz); 500 Hz altı < %0,15;
  2,5-9 kHz payı %40-58 → %78-89 (künt %58); çınlama gövdesi 0,68 sn → ~0,12 sn (+ sessiz pırıltı).

**Ölüm sesi neden duyulmuyordu** (`--otomatik` günlüğü, `[ses]` satırları; `--ses_log` ile de açılır): ses ÇALIYORDU, ama
öldürüş karesinde 0,15 sn içinde 9 ses daha çalıyordu: yaratığın 1,8-3 sn'lik ölüm çığlığı (ör. surale_olum, 0 dB), olum_vurus
(+1,5 dB), silah, et, kemik, acı sesleri — hepsi SFX sıkıştırıcısından geçiyor, "dışşkk" da onlarla birlikte bastırılıyordu.
Üstelik eski `vahset_patla`nın enerjisinin %95'i 500 Hz altındaydı (güm): karakteristik "şşkk" hışırtısı çok sessizdi.
Düzeltme:
* `vahset_patla*` kritik veri yolunda çalar (`Ses.LOUD_PREFIXES`: SFX sıkıştırıcısını atlar), kendi eşzamanlılık grubunda
  (3 / 2); çalarken `Ses.krit_duck(0.8)` öbür efektleri kısa süre ~4,5 dB kısar.
* Etli sıradan yaratıkta uzun ölüm çığlığı (`_die_sfx`) artık çalmaz; seçkin / boss'ta 5 dB kısık; etsizde aynen.
* Ses yeniden üretildi (4 + 3 çeşit, ~0,31-0,37 sn): tık + impactPunch + kısa güm + 2 kHz → 600 Hz inen ıslak "ış" bandı +
  ıslak şapırtı + çıtırtılı sıkışma + tiz "şşş" kuyruğu + "kk" zerre çıtırtısı; alt güm payı sınırlı. Ağırlık merkezi
  336 → 1784 Hz, 500 Hz altı %95 → %53, 2,5-9 kHz %2,5 → %22; algılanan yükseklik ~+3 dB (-9,7 → -6,9).

**Daha çok kan** (`Gore.ET_KAT` 1,6, `ET_YAYILMA` 1,12): etli ölüm patlamasında topak ve damla x1,6, iri topak +2, saçılma hızı
x1,12, çıkış siluet alanı x1,1 (seçkin / boss çarpanı aynen: oransal olarak yine büyük); öldürüşte darbe yönünde 2 (seçkin 4)
küçük yer lekesi daha; etli yaratıkta sıradan (kritik olmayan) vuruşa da küçük ileri kan fışkırması (7 damla).
`--vahset`: tepe canlı zerre ~1000 → 1726, patlama başına ~212 zerre, Gore'un en kötü kare maliyeti ~6 ms (önce 5-7 ms),
tek patlama kurulumu ≤ 1,7 ms; ortalama kare 12 ms (başsız).

Testler: `--vahset` (+ `--vahset_cek --pencere=1920x1080` şeritleri), `--dovus --boss --kontrol`, `--otomatik --derinlik=1
--muhur=0` (iki öldürüşte de `[ses] ölüm sesi ... bus=Krit çalıyor=true`, eşzamanlı çığlık yok): betik hatası 0.

## v37c: kritik = sekiro_2 (örs KANG, gerçek kayıt)

Oyuncu geri bildirimi (4 tur ret: ince "ting" A-F, sinüs "çınn" G-K, süzülmüş Kenney L-P): "Sekiro savuşturması gibi; sert, metalik,
gerçek KILIÇ sesi yok bunlarda". Araştırma (`scratch_v37/aday/tur4/ARASTIRMA.md`): Sekiro için resmî ses-tasarımı kaynağı yok;
oyuncu / basın betimlemelerinde ortak kelime **"CLANG"** — savuşturma "gürültülü, bloktan belirgin şekilde daha tiz bir clang + kıvılcım",
blok "sönük ding". Yani ana karakter ince çınlama değil, gövdeli (0,8-3 kHz) sert çelik vuruşu; parlak çınlama onun üstünde oturur.
Bu turda 8 aday tamamen gerçek CC0 çelik kayıtlarından kuruldu (`scratch_v37/aday/tur4/`), oyuncu **sekiro_2**'yi seçti.

**Ses** (`tools/audiogen/v37c.py`; `darbe_kritik_1` = sekiro_2 birebir): Pablo Bergel'in demirci örsü vuruşu (BigSoundBank "Anvil #1",
CC0; gerçek 2,52 kHz örs çınlaması, 2 s temiz kuyruk → 0,95 s'e şekillendirilmiş, 0,8-3 kHz +3 dB raf, +6 dB geçiş) + aynı kaydın
geçişsiz kuyruğu (%55, çınlamayı öne alır) + Bird_man kılıç-kılıca çarpışmasının ilk 110 ms'si (Freesound 275159, CC0; enerjisinin
%93'ü 0,6-3 kHz: "CLANG" gövdesi ve sertlik) + ihitokage bıçak sürtünmesinden 50 ms kıvılcım (6-13 kHz, %18); 3 erken yansıma, tanh
doyum; sentez katmanı yok. Ölçüm: tepe 2,52 kHz, merkez ~2,6 kHz, 0,6-3 kHz payı %97, t40 ≈ 0,64 s, 1,05 sn, tepe/RMS 8,3 dB.
Çeşitler `darbe_kritik_2..4`: örs perdesi ±4-7 %, iki ayrı örs vuruşu, kılıç geçişi kaydın 1./2. vuruşu, kuyruk ±15 %, kıvılcım farklı
(`Ses._pick_variant` 4 çeşitten son ikisini dışarıda bırakır). `darbe_kritik_kunt_1..3`: örs ×0,77-0,84, kuyruk kısa, +8 dB geçiş +
Kenney impactMetal_heavy alt gövdesi. `olum_vurus_1..2`: aynı KANG 0,75-0,8 sn, -9 dB. Hedefler v37 ile aynı (kritik -6,5 dB,
olum_vurus -9 dB), Krit veri yolu / `krit_duck` değişmedi; v37'nin kılıç-çarpışması kritiği `v37.build_all`'dan çıkarıldı (tek kaynak v37c).
Kaynak kalitesi: örs 256 kbps/48 kHz MP3, kılıç 128 kbps önizleme (tam WAV Freesound girişi ister; aynı adla `.wav` konursa `load()` onu
yeğler). Lisanslar `assets/audio/LICENSES.txt` 6-8.

## v38: performans (CPU)

Amaç: oyun davranışı değişmeden işlemci (betik, fizik, yapay zekâ, efekt, bölüm kurma) maliyetini ve kare takılmalarını
azaltmak. Görüntü / GPU tarafı (çizici ayarları, gölgelendiriciler, doku içe aktarma, HD paket, ışık) ayrı iş (v38 GPU).

**Ölçüm** (`tools/tests/perf_testi.gd`, `-- --perf`): `--fixed-fps 60` ile karelerin hepsi işlenir (başsızda olabildiğince
hızlı, pencerede dikey eşitleme kapatılır), kare süresi = gerçek maliyet. Evreler (`--perf_faz=` ile seçilir, `--perf_sure=`
60 sn'lik evreyi ölçekler): `uretim` (20 tohumda `Main._build_level`, derinlik 1-10; adım adım süre tablosu, kurulumdan sonraki
ilk kare, kurulumlar arası düğüm / nesne sayısı), `yurt`, `konak` (bot yürür, kapıdan geçince ölçüm biter), `gezinti`
(2. derinlik, rehber botu, küçük harita açık, 45 sn), `savas3` / `savas7` (gerçek bölüm, oyuncunun çevresinde hep ~25 düşman,
bot dövüşür, test 0,4 sn'de bir yakındaki düşmanı öldürür: gore, kan, ceset, altın; 60 sn; sonra düşmanlar silinip 6 sn
beklenir ve hangi düğüm türünün arttığı yazılır). Satırlar: `[perf] EVRE` (ort / p95 / p99 / en kötü kare ms, düğüm, nesne,
çizim çağrısı, statik bellek), `[perf] SISTEM` (sistem başına kare başı ms), `[perf] TAKILMA` (33 ms'yi aşan kare ve o karenin
en pahalı sistemleri), `[perf] SIZINTI`, `[perf] URETIM adim_ms`.

    godot --headless --path . --quit-after 80000 --fixed-fps 60 -- --perf
    godot --path . --quit-after 80000 --fixed-fps 60 --resolution 1920x1080 -- --perf --perf_faz=uretim,yurt,gezinti

**Profil ölçer** (`scripts/core/Prof.gd`): sıcak `_process` / `_physics_process` / `_draw` gövdeleri `..._ic` işlevine
taşındı, asıl işlev `if Prof.on:` ise süreyi `Prof.ekle(&"ad", t0)` ile biriktirir (kapalıyken tek statik bool okuması).
Ölçülenler: dusman_fizik / dusman_anim, oyuncu, bengu, gore(_ciz), kan(_ciz), ceset, bolum, hud(_ciz), game, ses, bot,
kamera, paralaks, onplan, mermi, pickup, spriteanim, can_cubugu(_ciz), golge(_ciz), silah_izi(_ciz), fx, sanatfx, dunya;
`Level.build` her adımı `kur_*` olarak.

**Önce / sonra** (başsız, test makinesi Intel UHD 750; aynı makinede GPU ölçümleri koşarken alındı, gürültü ±%50: önce / sonra
koşuları sırayla değiştirildi, sayılar 2-4 koşunun ortalaması; dövüş sistemleri değişmeyen "oyuncu" süresine bölünerek de
karşılaştırıldı):

| ölçüm | önce | sonra |
|---|---|---|
| bölüm kurma (20 tohum ort.) | 1044 ms (en kötü 2054) | 620 ms (en kötü 1432) |
| ↳ LevelGen.generate | 588 ms | 213 ms |
| ↳ spawn_scrolls / spawn_kesif (reach_from) | 85 / 81 ms | 31 / 29 ms |
| bölüm kurma, pencereli 1920x1080 | 1375 ms (generate 693) | 495 ms (generate 184) |
| gezinti: dusman_fizik (27 yaratık) | 1,3-2,8 ms (oyuncu x2,2) | 0,9-1,8 ms (oyuncu x1,7), -%27 |
| gezinti: golge (48 gölge) | 0,6-1,2 ms | 0,4-0,75 ms, -%28 |
| gezinti: dusman_anim | 0,5-1,1 ms | 0,3-0,7 ms, -%29 |
| küçük harita (HUD içinde) | ~0,6 ms, işaret listesi her karede | işaret listesi ~15 Hz |
| dövüş: golge (55-70 gölge, yerde altın) | 0,7-1,5 ms | 0,5-0,75 ms, -%25 |
| dövüş: dusman_fizik / gore / kan | 1,2-2,6 / 0,25-0,35 / 0,3-0,4 ms | aynı (gürültü içinde) |
| tek sistemli en büyük takılma | oyuncu 97-122 ms (ilk yay nişanı), oyuncu 44-72 ms ve dusman_fizik 42-59 ms (ilk efekt dokuları) | ≤ 19 ms (yalnızca yük gürültüsü) |
| boşta kan (Blood) | her karede fizik + yeniden çizim | atlanır |

Pencereli (1920x1080, UHD 750) kare süresi yurtta, konakta, gezintide ve dövüşte 27-37 ms: GPU sınırlı; işlemci payı
(betikler ~6-9 ms) bunun altında kaldığından pencereli kare süresi CPU düzeltmeleriyle belirgin değişmez. HUD çizimi
(`hud_ciz`) pencerede 3-4 ms, başsızda 1-3 ms: en büyük tek betik maliyeti olarak kaldı (anlık çizim; dokunulmadı).

**Düzeltmeler** (hepsi aynı sonucu verir; yalnızca uzak LOD görünmeyen yaratığın boşta dolaşmasını durdurur):
- `LevelGen._moves`: adaylar `_stand_cols` (sütun başına ayakta durulabilir satırlar, BFS başına bir kez) üzerinden; 231
  adayın `_standable` çağrısı yerine sütun başına birkaç satır, doğrulama `_hamle_ok`'ta (sıra ve sonuç aynı). `traps`: ters
  kenarlar sözlük-dizi yerine sıkıştırılmış dizide (kenar listesi + sayım). `--harita` 120 tohum çıktısı önce / sonra aynı
  (yalnızca tohumsuz rastgele satırlar farklı). `reach_from` / `path_cells` / `_reach` aynı yoldan hızlandı.
- `Enemy` uzak LOD (`_uzakta_uyu`): oyuncudan ~1000 px yatay / 640 px dikey (yakın çekimde ~1,7 ekran) ötede, uyanık değil,
  boşta (idle / perch / dormant / lurk), hiçbir durum etkisi yok, yerde ya da uçan yaratık uyur: yapay zekâ, hareket ve poz saati
  çalışmaz. Uyanma 290 px'te olduğundan dövüş etkilenmez. `_ds_lookup`: anahtar her karede biçimlenmez (durum değişince).
- `GroundShadow`: zemin taraması (40 adım) ve aya ışın (175 adım) ayak noktası ya da bölüm karoları (`Level.grid_surum`,
  `set_air` / `set_solid`'de artar) değişmedikçe yeniden yapılmaz; durgun sahipte (yerdeki tane, duran yaratık) kare tümüyle atlanır.
- `Pickup`: yerde duran tane her karede aynı sonucu veren düşüş / zemin denetimini atlar; mürekkep sprite'lı tanede boş `_draw`
  için yeniden çizim istenmez.
- `Blood`: damla / akıntı / et parçası yokken fizik ve yeniden çizim yok; leke ağı (`_Stains`) önbellekte: yeni leke eklenir,
  büyüyen leke yerinde güncellenir, koyulaşma / kırpma tümünü kurar (eskiden kirli her karede 1600 dörtgen baştan).
- `HaritaUI.minimap`: `Harita.isaretler()` (düşman grubu taraması, kapı / oda denetimi, sözlükler) ~15 Hz; tam harita her kare.
- Takılmalar: `Game` açılışta efekt / arayüz dokularını (`assets/fx/anim`, `fx/ink`, `fx/ink_p`, `ui/ink`; HD paketindekiler
  hariç) arka plan iş parçacığında yükleyip tutar (ilk kullanımda 15-40 ms'lik `load`). `Player._yay_uclari_hazirla`: yay uçları
  (4096x2248 BPTC silah atlası sayfasının çözülmesi + piksel taraması, ~100 ms) ilk nişanda değil kuşanınca / bölüm kurulurken.

**Sızıntı denetimi**: aynı 10 tohum iki tur kurulunca düğüm sayıları birebir aynı (528 ... 712); nesne sayısının ikinci
turdaki artışı azalarak söner (+371 → +43: doku / sprite önbellekleri ısınıyor), sızıntı değil. Dövüşten sonra (düşmanlar
silinip 6 sn) kalan düğümler yalnızca yerde toplanmamış altın / eşya (Pickup + gölge + ışık + sprite), havuzdaki silah izleri
(InkTrail, en çok 6) ve sunak / tomar zerreleri; efekt, ceset ve parçacık birikmesi yok.
**Bulunan sızıntı**: `Level.build_boss` kullanılmayan bir `Enemy.new()` oluşturuyordu (ağaca girmeyen yaratık + fizik
gövdesi, her boss arenasında bir tane; `--dovus --boss`, `--sanat --boss`, `--konak` çıkışında "Body2D RID leaked"); kaldırıldı. Ses oynatıcıları zaten havuzlu (Ses).
Başsız koşuda statik bellek ~2 GB (sahte çizici görüntüleri RAM'de tutar), pencerede 220-280 MB.

Testler: `--dovus --boss --kontrol`, `--sanat --boss --muhur=0`, `--harita`, `--isinlan`, `--konak`, `--tuccar --muhur=0`,
`--otomatik --derinlik=1/3/5 --muhur=0`, `--vahset`, `--zeka --muhur=0`, `--piksel_tara`: betik hatası 0.

## v38: görüntü ve GPU optimizasyonu

Hedef donanım gerçeği: Intel UHD 750 (tümleşik, paylaşımlı bellek). Oyun GPU'ya bağlıydı: 1080p pencerede yurtta bile
~30 ms/kare, 1440p'de ~60 ms. Darboğaz çizim çağrısı değil (115-290 çağrı) **piksel doldurma**: 8-10 tam ekran paralaks
katmanı, sis / pus, ışık döngüsü, parlama ve renk derecelendirmesi her ekran pikselinde.

### Ölçüm (`tools/tests/gorsel_perf.gd`, `-- --gpu_perf`)
`Ayarlar._ready` bayrağı görünce ekler (başka test bayraklarıyla birleşir). Dikey eşitleme kapalı, kare sınırı yok; her faz için
kare süresi ort / %95 / en kötü, **GPU süresi** (kök görüntü alanı, `RenderingServer.viewport_get_measured_render_time_gpu`),
2D çizim çağrısı / öğe / ilkel, doku ve toplam VRAM, görünür (gölgeli) ışık sayısı, HD doku sayısı ve yükleme süresi; açılışta
ilk kare (motor başlangıcından ms), bölüm değişiminde kurulum karesi. `--gpu_doku`: kullanılan benzersiz dokuların listesi.
Örnek: `godot --path . -- --gpu_perf --ekran=perf --derinlik=5 --tohum=3 --muhur=0 --pencere=2560x1440 --bekle=4 --olcum_sn=8`
(`--grafik=0..3` hazır ayar; `--g_isik= --g_katman= --g_cizim=` tek alt ayar; `--kirpma_yok` paralaks kırpmasını kapatır).

### Önce / sonra (Intel UHD 750, pencere, vsync kapalı, tohum 3, mühür 0, 8 sn; "önce" = v37 ana dal)
| Sahne | Çözünürlük | Önce FPS (kare / GPU ms) | Yüksek FPS (kare / GPU ms) | Orta FPS (GPU ms) | Düşük FPS (GPU ms) |
|---|---|---|---|---|---|
| Ötüken 1 | 1080p | 38,3 (26,1 / 23,9) | 47,0 (21,3 / 18,3) | 58,1 (7,7) | 57,9 (7,4) |
| Şahmeran 5 | 1080p | 28,4 (35,2 / 30,2) | 32,5 (30,8 / 23,3) | | |
| Tamu 9 | 1080p | 27,2 (36,8 / 30,4) | 32,5 (30,8 / 21,9) | 52,5 (8,9) | 56,5 (7,6) |
| Yurt | 1080p | 29,3 (34,1 / 30,1) | 34,5 (29,0 / 25,0) | | |
| Vahşet (yoğun dövüş) | 1080p | 26,4 (37,9 / 31,3) | 33,1 (30,2 / 23,5) | 63,4 (7,7) | 118 (3,5) |
| Ötüken 1 (HD) | 1440p | 15,3 (65,4 / 59,5) | 18,6 (53,8 / 46,3) | 44,7 (8,3) | 45,2 (8,2) |
| Şahmeran 5 (HD) | 1440p | 15,6 (64,1 / 58,4) | 19,1 (52,4 / 45,6) | | |
| Tamu 9 (HD) | 1440p | 19,6 (51,1 / 46,6) | 19,1 (52,3 / 45,2) | 41,6 (9,1) | 42,9 (8,6) |
| Yurt (HD) | 1440p | 16,3 (61,5 / 56,7) | 20,2 (49,5 / 44,5) | | |
| Vahşet (HD) | 1440p | 12,6 (79,2 / 64,2) | 17,6 (56,9 / 46,4) | 52,8 (7,6) | 52,6 (7,2) |

* GPU süresi Yüksek'te (görüntü aynı) **%20-28 düştü**; Orta / Düşük'te GPU 7-9 ms: kare artık CPU'ya bağlı (oyun mantığı;
  v38-cpu38 dalı ayrıca iyileştirir). Çizim çağrısı değişmedi (2D zaten toplu çiziliyordu).
* **VRAM** (standart doku, 1080p): Ötüken 949 -> 807 MB, Şahmeran 847 -> 753, Tamu 829 -> 736, vahşet 1107 -> 898 MB; Orta
  713 MB. HD 1440p: vahşet 2423 -> 2266 MB.
* **Yükleme:** HD doku yüklemesi bölüm başına 3,98 -> 1,35 sn (Ötüken 1440p), 3,66 -> 1,64 (vahşet), yurt 1,41 -> 0,66;
  ilk kare 1440p'de 12,8 -> 9,5 sn, 1080p'de ~1 sn erken.

### Yapılanlar
* **Çizici: Forward+ -> Mobile** (`project.godot`, Vulkan; Windows sürücüsü açıkça `vulkan`: D3D12 bu GPU'da %30 yavaştı).
  2D çizim yolu iki RD çizicide ortak: HDR 2D, parlama, ekran dokusu gölgelendiricisi, 2D ışık / gölge aynı; görüntü farkı
  yalnızca canlandırma evresi (ort. piksel farkı 0,2-2,3 / 255). Compatibility (OpenGL) daha da hızlıydı ama görüntü farklı
  (parlama, ışık karışımı, ekran dokusunun renk uzayı; yıkanmış, vinyetsiz): elendi. Vulkan yoksa motor kendiliğinden
  OpenGL'e düşer; otomatik hazır ayar o zaman Düşük.
* **Paralaks kırpma** (`tools/artgen/bg_kirp.py` -> `data/bg_kirp.json`, `ParallaxBG`): her katmanın alfası olan ilk / son
  satırı; Sprite2D bölgesi + ofsetle yalnızca o şerit çizilir (görüntü bayt bayt aynı, yatay döşeme değişmez). Sis / pus
  katmanlarında %50-80, dağlarda %25-50 daha az piksel. Katman dokuları yeniden üretilince betik yeniden çalıştırılır.
* **HD paket yükleyicisi** (`Data._ctex_image`): içe aktarılmış BPTC verisi `.ctex` dosyasından doğrudan okunup
  `Image.create_from_data` ile `ImageTexture`'a verilir. Eskiden doku önce GPU'ya yükleniyor, geri okunuyor (`get_image`) ve
  ikinci kez yükleniyordu (iki kopya, GPU senkronu). GPU BPTC desteklemiyorsa ya da biçim beklenmedikse eski yol.
* **VRAM:** 48 büyük kayıpsız doku VRAM sıkıştırmalı (BPTC yüksek kalite) oldu: sprite / süs / karo ışıma sayfaları (`*_e.png`,
  yumuşak toplamalı; ör. dev_cocugu_v2_e 28,8 -> 7,2 MB) ve `assets/fx/anim` animasyonlu efekt sayfaları. Gök, sis, pus,
  hüzme ve maskeler bantlaşmasın diye kayıpsız kaldı. Biyom değişince eski biyomun paralaks / ön plan dokuları önbellekten
  bırakılır (`Data.budama`, `Level._exit_tree`; yalnızca önbellek tutuyorsa): HD'de biyom başına ~350 MB birikmiyor.
* **Gölgelendiriciler:** `grade_v2` sonuna titreşim (iki "interleaved gradient noise" = üçgen dağılım, ±1/255; `dither`
  parametresi): HDR 2D tampon 8 bite yazılırken koyu sis / pus gradyanlarındaki basamaklı bantlar kayboldu
  (`docs/v38/gorsel/yakin_bant_tamu_1080.png`, kontrast x5). `ground_ink`: dünya uzayı UV'leri (toprak, çayır, derinlik)
  köşede hesaplanıp aradeğerlenir (piksel başına `textureSize` ve bölme yok; sonuç aynı). Hasar flaşının tam ekran saydam
  dörtgeni yalnızca flaş sırasında görünür (`Level.red_rect`).

### Grafik ayarları (`Ayarlar.gd`, Ayarlar ekranı)
Yeni satırlar: **Grafik kalitesi** (hazır ayar) ve alt ayarları; alt ayar değişince hazır ayar "Özel" olur. Açıklamalar
satırın kendisinde (`rows()` [ad, değer, etkin, açıklama, anahtar]); 15 satır 640x360 menüye sıkışık aralıkla sığar.

| | Düşük | Orta | Yüksek | Ultra |
|---|---|---|---|---|
| Çizim çözünürlüğü | Yarım (960x540) | Yarım (960x540) | Tam | Tam |
| Doku kalitesi | Standart | Standart | Otomatik (1440p+ HD) | 2K (HD her çözünürlükte) |
| Işık ve parlama | Az: parlama ve renk derecelendirmesi kapalı (yalnızca vinyet), en çok 14 süs ışığı, gölge yok | Hafif: gölgesiz, en çok 28 süs ışığı, tam parlama | Tam | Tam |
| Arka plan katmanları | Az (pus, hüzme, rüzgâr, uzak kar yok) | Tam | Tam | Tam |
| Efekt yoğunluğu (`Ayarlar.efekt_yogunluk()`) | 0,5 | 0,75 | 1,0 | 1,0 |

* **Çizim çözünürlüğü Yarım:** kök pencere `canvas_items` yerine `viewport` germe kipi: sahne 960x540'ta çizilip büyütülür
  (dünya ve arayüz düzeni aynı, GPU yükü pencere çözünürlüğünden bağımsız: UHD 750'de 1080p ve 1440p'de GPU ~8 ms). Bedeli
  yumuşaklık (`docs/v38/gorsel/*_yuksek_orta.jpg`, `yakin_keskinlik_otuken_1080.jpg`). 2D'de ara ölçek (0,67 / 0,8) yok:
  `viewport` kipinde mantıksal boy = çizim boyu, oyun 960x540 mantıksal görüntüye bağlı.
* **Efekt yoğunluğu** yalnızca ayar + okuyucu (`Ayarlar.efekt_yogunluk()`); kan / parçacık üreticileri (CPU tarafı) bunu
  çarpan olarak okuyabilir.
* **Kare sınırı:** Sınırsız / 30 / 60 / 120 / 144 (`Engine.max_fps`).
* **İlk açılış (ayar dosyası yok):** GPU türü (`RenderingServer.get_video_adapter_type`, ad: UHD / Iris / HD Graphics)
  tümleşikse Orta, ayrıksa Yüksek, OpenGL yedeği / CPU Düşük. **Eski ayar dosyası** (`[grafik]` bölümü yok): kayıtlı doku
  kalitesi korunur, diğerleri aynı kuralla seçilir. Yeni anahtarlar `[grafik]` bölümünde (hazir, cizim, isik, katman, efekt,
  fps); eski anahtarlar (mod, cozunurluk, olcek, doku, vsync, arayuz, efekt, harita) aynen.
* Işık / katman / efekt sonraki bölümde, çizim çözünürlüğü ve kare sınırı hemen, doku kalitesi yeniden başlatınca geçerli.

### Görüntü kanıtı (`docs/v38/gorsel/`)
`<biyom>_1080_once_sonra.jpg`, `<biyom>_1440_once_sonra.jpg` (Ötüken, Şahmeran, Tamu, yurt; aynı tohum ve kare): v37 ile v38
Yüksek aynı görünür (farklar canlandırma evresi). `<biyom>_1080_yuksek_orta.jpg`: Orta'nın yarım çizimi. Yakın kırpmalar:
keskinlik (Ötüken, 2x) ve sis bantlaşması (Tamu, kontrast x5).

### Yapılmayanlar / notlar
* Sprite başına ayrı ShaderMaterial (vuruş parlaması) toplu çizimi bölüyor ama çizim çağrısı 115-290: darboğaz değil.
* Gök / sis kayıpsız dokuları ctex içinde WebP: yüklemede çözülür (25-36 ms / katman). "VRAM Uncompressed" yüklemeyi hızlandırır
  ama dışa aktarım ~400 MB büyür; yapılmadı.
* Yay ucu taraması (`Data.weapon_sprite_image`) hâlâ temel silah atlasını geri okur (CPU dalı kuşanma anına taşıdı); uç
  noktalarını `weapons_v2.json`'a önceden yazmak sonraki iş.
* 2D fizik aradeğerlemesi (yüksek yenilemeli ekranda akıcılık) CPU / fizik tarafının işi; açılmadı.

## v38 birleştirme denetimi

v38-cpu38 (Prof sarmalayıcıları, LevelGen hızlanması, uzak LOD, efekt dokusu ön yüklemesi) ile v38-gpu38 (Mobile çizici,
paralaks kırpma, HD yükleyici, grafik hazır ayarları) `main`'de birleştikten sonra anlamsal denetim.

**Çakışma denetimi (sorun yok):**
- `Level.gd`: CPU tarafı (`grid_surum`, `build_boss`'taki sızıntı düzeltmesi, `build` adım süreleri) ile GPU tarafı
  (`_exit_tree` -> `Data.budama_planla`, `add_light` ışık sınırı / gölge, `_build_lighting` parlama, `_build_overlay_fx`
  derecelendirme, `red_rect` / `flash_white` görünürlüğü) ayrı satırlarda; her bölüm yeni `Level` olduğundan `_isik_say` sıfırdan başlar.
- `Data.budama` yalnızca `res://assets/bg/` dokularını (paralaks / ön plan) bırakır; `Game`'in arka plan ön yüklemesi
  yalnızca `assets/fx/anim`, `fx/ink`, `fx/ink_p`, `ui/ink` (HD paketindekiler hariç) ve `Data._tex_cache`'e değil
  `ResourceLoader` önbelleğine yazar (başvuruyu `Game._on_yuklu` tutar): kümeler kesişmez, budama ön yüklenmiş dokuyu düşürmez.
  Ön yükleme sürerken aynı yolu `load()` ile isteyen (Data.tex / InkDraw) motorun yükleme görevine katılır; yarış yok.
  `Data._init_pack` (Data._ready) `Game._ready`'den önce çalışır (otomatik yükleme sırası), `pack_has` doğru.
- `ParallaxBG`: kırpma ve "Az" katman atlama `_ready`'de, `_process` -> `_process_ic` sarmalayıcısı yalnızca `_layers`'ı
  dolaşır (atlanan katmanlar dizide yok; dizin kayması yok). Kar katmanlarında da kırpma bölge + ofsetle aynı görüntü.

**Bulunan / düzeltilen:**
- `RootSpikes` (Ağaç İyesi kökleri): kök fırladıktan sonra yaratık ölüp silinirse `take_hit(dmg, source)` serbest
  bırakılmış nesneyle "Invalid type" betik hatası veriyordu (`--perf` savas7 evresinde 2 kez; v38 öncesinden kalma). `Isin` /
  `Tehlike` gibi `is_instance_valid(source)` denetimi eklendi.
- Ayarlar ekranı (15 satır, 1920x1080): alt başlık ("Görüntü ve çözünürlük") panelin üst kenarıyla, "Pencere: ... ölçek"
  satırı alttaki tuş ipuçlarıyla çakışıyordu. 9'dan çok satırda pencere bilgisi alt başlığa çıkar, başlık 8 px yukarı, satır
  aralığı 14 px: üç satırlık açıklamaya da yer kalır (`--ekran=ayarlar --ayar_sel=<satır>` ile çekim).

**Efekt yoğunluğu bağlandı** (`Ayarlar.efekt_say(n, en_az, olum)`): yalnızca SAYI ölçeklenir, boyut / hız / ömür aynı;
Tam'da (Yüksek / Ultra) sayı hiç değişmez. Düz çarpan (Az 0,5, Orta 0,75): `FX.burst` / `FX.sparks` (en az 2-3; yıldız
parıltıları aynı), `FX.smoke`, `Blood.spray` (vuruş kanı; buğu kararı kısılmamış sayıyla). Ölüm çarpanı 0,3 + 0,7k
(Az %65, Orta %82,5): `Gore._burst` ana zerre / ince damla (iri parçalar ve buğu aynı), `Blood.burst` damlaları (et
parçaları aynı), `Blood.splat` lekeleri. `--vahset` ölüm başına zerre, Yüksek -> Düşük: sıradan 147 -> 97, kritik
239 -> 159, bitiriş 193 -> 128, seçkin 350 -> 231, taş 61 -> 41 (%66-67).

**Ölçümler** (Intel UHD 750):
- `--perf` (başsız): bölüm kurma 20 tohum ort. 473 ms (en kötü 824), generate 171 ms; yurt 3,2 ms/kare, konak 3,0,
  gezinti 6,8 (p95 10,6), savas3 11,5 (p95 17,7), savas7 9,6 (p95 14,5). Sızıntı yok (düğüm sayıları iki turda aynı).
- `--gpu_perf`, pencere 1920x1080, tohum 3, 8 sn:

| Sahne | Orta FPS (kare / GPU ms) | Yüksek FPS (kare / GPU ms) |
|---|---|---|
| Ötüken 1 | 104,8 (9,6 / 4,3) | 49,2 (20,3 / 18,3) |
| Tamu 9 | 161,8 (6,2 / 4,5) | 47,7 (21,0 / 19,0) |
| Vahşet (yoğun dövüş) | 110,2 (9,1 / 4,3) | 45,4 (22,0 / 19,1) |

  Orta (yarım çizim) GPU 4-5 ms, kare CPU'ya bağlı; Yüksek GPU'ya bağlı ve v38 GPU tablosuyla uyumlu (birleşme GPU
  maliyetini değiştirmedi). `--kirpma_yok` ile Yüksek Ötüken 1 GPU 19,3 ms (kırpmayla 18,3). Uzun `--perf` koşusunun
  hemen ardından alınan ilk tur Yüksek'te ~28-30 FPS verdi (makine yüklü / sıcak); tablo yalnız koşulan ikinci tur.

Testler: `--perf`, `--gpu_perf` (Orta / Yüksek), `--dovus --boss --kontrol`, `--sanat --boss --muhur=0`, `--harita`,
`--isinlan`, `--konak`, `--tuccar --muhur=0`, `--otomatik --derinlik=1/3 --muhur=0`, `--vahset` (ayrıca `--grafik=0/2`),
`--zeka --muhur=0`, `--piksel_tara`, `--yurt --yurt-tur`: betik hatası 0 (RootSpikes düzeltmesinden sonra).

## v39: Bengü yeniden çizim

Geri bildirim: "Bengü'yü çizim olarak kusursuz yapalım — kukla gibi duruyor; çizimi dünyaya daha çok uymalı."

### Teşhis (oyun içi 1920x1080, Ötüken + Şahmeran; `docs/v39/bengu/`)
Önce çekilen kontak sayfalarında (durgun, koşu, sıçrama, yuvarlanma, darbe, Kahraman İnişi, kılıç / ağır / mızrak /
gürz kombosu, yay) ve yaratıkların yanında Bengü'nün neden kukla gibi okunduğu:
1. **Oran:** baş + kurt başlığı boyun ~1/4,5'i, gövde (17 birim) bacağa (25,6, hep bükük) göre uzun, bol şalvar ve iri
   çizmeler bacağı kısaltıyor; ~5 baş boyunda "oyuncak asker" silüeti. Kaftan eteği + kemer + sırma şerit üç yatay bant:
   gövde kutu gibi.
2. **Renk / ışık:** saf kırmızı kaftan, bembeyaz post, parlak çivit; sisli yeşil Ötüken'de ve mağara karanlığında dünyadan
   kopuk, yapıştırılmış gibi. Yaratıklar soğuk ay kenar ışığı (rim 0,55-0,75) ve koyu kütle gölgesiyle çiziliyor; Bengü'de
   kenar ışığı yoktu (rim 0), kütle gölgesi açık, dış kontur ince: çizgi dili düşmanlarla aynı değildi.
3. **Kaskatı ikincil öğeler:** kuşak kuyrukları sprite'a çizili, gövdeyle birlikte tahta gibi dönüyordu; arka etek kısa ve
   kutu; yalnızca saç fizikliydi.
4. **Zamanlama:** durgun nefesi 8 kare / 8 fps = 1 sn (soluk soluğa); koşu basışında ayak anahtarlar arasında yumuşatıldığı
   için her anahtarda duruyor, kare hızı yatay hızdan bağımsız (hızlanırken / dururken ayak kayıyor); sıçrama / düşüş 3'er
   kare zamanla oynuyor (tepe kaçıyor, uzun düşüşte son karede donuyor); iniş 2 kare.
5. **Lastik ezilme:** inişte çizilmiş ezilme karesinin üstüne katman 1,4 / 0,6 ölçek ekliyordu: gövde yere yapışık bir
   halı gibi yassılıyordu (kukla hissinin en göze batanı). Kahraman İnişi kendi pozu olmadan çömelik saldırı karesini
   ödünç alıyordu.
6. **Kol:** durgunda ön kol bel hizasında öne uzatılmış iri eldivenli yumruk (menteşe gibi); yumruk kafa kadar iri.

### Ne değişti
**Çizim (`tools/artgen/bengu_ink.py`, `bengu_govde.py`)**
* **Kahraman oranı:** bacaklar x1,10 (`bengu_govde.KL`; pozların dikey ölçüleri — kalça yüksekliği, ayak kalkıklığı —
  KL ile çarpılır, ayak x'leri aynı), gövde aynı oranda kısa (`TORSO_N` 17 -> 14,7; dinlenmede boyun / omuz yüksekliği
  v29 ile aynı: kol iskeleti, silah tutuşu, vuruş kutuları değişmez). Baş + başlık x0,9 (`HEAD_K` 1,05 -> 0,9), bel /
  gövde yanal x0,93, şalvar ve çizme ~%13 ince, kol 0,84, yumruk %18 küçük. Sonuç ~6,5 baş: uzun bacaklı, çevik silüet.
* **Akan silüet:** arka etek yırtmaçlı iki uzun kuyruk (baldıra iner, `sk` ile geriye savrulur, koşu / sıçrayışta
  kalkar); ön etek önü açık, eğik uçlu (yatay bant kırıldı), sırma şerit ince.
* **Palet:** kızıl kaftan `#b3343c` (eski `#d23138`), ak post kemik beyazı `#e2e0da`, çivit `#3e4a76`, çelik ve altın bir
  ton koyu; gölgeler soğuk mor-laciverde kayar. En okunur öğe yine Bengü (ak başlık + kızıl + turkuaz Kut).
* **Mürekkep-cel dili düşmanlarla aynı:** `SHADE` dış kontur 0,5 -> 0,62, soğuk ay kenar ışığı (rim 0,8, gölge yanında:
  koyu zeminde silüeti ayırır), daha koyu kütle gölgesi (üçüncü cel bandı). Kemer tokasında sıcak Kut közü (ışıma
  katmanı; gözler camgöbeği).

**Kareler (`bengu_ink.MOVE_LAYOUT`; `export_ink.export_bengu` satır düzenini bununla ezer)**
| Satır | v29 | v39 |
|---|---|---|
| durgun | 8 kare / 8 fps (1 sn) | 10 / 4 fps (2,5 sn nefes); ön el bel önünde kabzaya yakın (öne uzatılmış yumruk yok) |
| koşu | 8 / 14 | 10 / 18: basış koşu hızıyla eşli (döngüde 86 birim, basışta ayak 29,3 birim DOĞRUSAL geriye), kollar / omuz bacaklardan bir tık geride, baş sabit, inişte hafif ezilme |
| depar | 8 / 18 | 10 / 22 (240 birim/sn ile eşli) |
| sıçrama / düşüş | 3 + 3 zamanla | 4 + 4, oyunda dikey hıza göre seçilir; düşüşte T-pozu yerine dengeli kollar |
| iniş | 2 | 3 (ezilme -> geri esneme -> oturma) |
| `hero_dive` | (yuvarlanma / düşüş ödünç) | 2: havada toplanma, çakılış (silah iskelette) |
| `hero_land` | (çömelik saldırı ödünç) | 4: üç nokta iniş (ön ayak düz, arka diz yerde, gövde öne, arka kol açık) -> tutuş -> doğrulma -> kalkış |
Saldırı satırları (v28 / v29 aile gövdeleri, 10 kare) aynı anahtarlarla yeni çizimle yeniden üretildi; `Player.SWINGS`,
`COMBOS`, `TEMPO`, `FLOW`, evre eşlemesi, vuruş kutuları DEĞİŞMEDİ.

**Oyun (`scripts/actors/Player.gd`)**
* Koşu / depar kare hızı gerçek yatay hızla ölçeklenir (`anim.speed` = |vx| / koşu hızı, 0,45-1,35): ayak yerde kaymaz.
* Sıçrama / düşüş karesi `velocity.y`'ye göre; Kahraman İnişi `hero_dive` / `hero_land` karelerini kullanır.
* Lastik ezilme kısıldı: inişte 1,4 / 0,6 -> ~1,14 / 0,86, Kahraman İnişi çarpması 1,42 / 0,62 -> 1,16 / 0,86, dalış
  esnemesi 0,82 / 1,24 -> 0,88 / 1,16 (ezilme artık çizimde).

**İkincil hareket (`scripts/core/BenguKusak.gd`, yeni)**
Kuşak kuyrukları Verlet zinciri (9 + 7 nokta, 1/120 sn alt adım, yerçekimi 760, hava sürtünmesi, hızla büyüyen çırpınma,
bakışın tersine hafif esinti; kök = karenin `kusak` çapası, ilk parça düğümden aşağı-geri yaya çekilir, gövdenin önüne
geçmez, yere girmez). Gövde malzemesini (ink_char) paylaşır: vuruş parlaması / ay gölgesi / sahne ışığı aynı. İki cel
bandı + ışık yanı parlama + mürekkep kontur + kızıl püskül ve altın halka. Koşuda geriye akar, sıçrayışta sarkar,
savuruşta gövde döndükçe gecikmeyle savrulur. (`bengu_ink.KUSAK_SPRITE = True` eski çizili kuyrukları verir.)
Saç (BenguSac) aynen; yeni çapalarla çalışır.

### Varlıklar ve hat
`cd tools/artgen; python export_ink.py --bengu` (~1 dk 45 sn, paralel) + `KY_HD=2 python export_ink.py --bengu` +
`python hd_paket.py --paketle`: `bengu_v2` 47 satır / 4 sayfa (3840 genişlik), `bengu_kol_v2`, HD x2 WebP + manifest
md5'leri. Karelere yeni `kusak` çapası yazılır.
Önizleme: `python preview_ink.py out.png idle:0 run:3 hero_land:0` (sprite karesi).
Oyun içi çekim + kontak sayfası (önce / sonra):
`godot --path . --resolution 1920x1080 --fixed-fps 60 -- --bengu=<klasör> --bengu_sayfa --boss=kara_boru_han
--pencere=1920x1080 --grafik=2` (`tools/tests/bengu39_cekim.gd`: durgun, koşu, sıçrama, yuvarlanma, darbe, Kahraman İnişi,
kılıç / ağır / mızrak / gürz kombosu, yay kare dizileri + tam ekran ve yaratıklarla çekim), sonra
`python tools/artgen/bengu39_sayfa.py <klasör> out.jpg idle:0:24:3 run:0:10 ... [--karsi=<klasör2>]`.
Not: kayıtlı ayar "Yarım" çizim çözünürlüğündeyse çekim 960x540 olur; `--grafik=2` tam çözünürlük verir.

### Görseller (`docs/v39/bengu/`)
* `hareket_once_sonra.jpg` — durgun, koşu döngüsü, sıçrama, yuvarlanma, darbe, Kahraman İnişi (her satır çifti: üst önce,
  alt sonra).
* `kombo_once_sonra.jpg` — kılıç kombosu, ağır, mızrak, gürz, yay.
* `oyun_otuken_once.jpg` / `oyun_otuken_sonra.jpg`, `oyun_sahmeran_once.jpg` / `oyun_sahmeran_sonra.jpg` — tam ekran
  saldırı ortası; `oyun_*_kosu_*.jpg` koşu; `hareket_sahmeran_once_sonra.jpg` karanlık biyomda durgun / koşu / kılıç /
  Kahraman İnişi.
* `yaratiklarla_once_sonra.jpg` — Bengü yaratıkların yanında (Ötüken: Balbal, Ağaç İyesi; Şahmeran: Yılan Muhafız,
  Su İyesi), üst önce, alt sonra.

### Test
Betik hatası 0 (SCRIPT ERROR yok): `--dovus --boss --kontrol` TAKILMA=0, KONTROL basış=272 savuruş=136 basılmamış=0
oto_dönüş=0 oto_hamle=0 istenmeyen_ağır=0; `--savurus`; `--mekanik --zipla --boss` OZET hata=0; `--sanat --boss
--muhur=0` SONUC GECTI hata=0; `--otomatik --derinlik=1 --muhur=0 --fixed-fps 60 --quit-after 9000`; `--piksel_tara`
TOPLAM 0; `--bengu --boss` OZET hata=0 (saç kapsülü / baş çemberi yeni orana göre: 6,6-5,8 -> 6,1-5,4, 7,2 -> 6,4;
yoksa duruşta saç öne salınmıyordu).

### Bilinen
* Ön kol hâlâ çalışma zamanı iskeleti (omuz / dirsek / bilek; v3-v7) — silah elde kalsın, vuruş kutuları sabit kalsın
  diye. Omuzluk ekleme yerini örtüyor, kol inceldi ve yumruk küçüldü; tam gövde saldırı kareleri + silah yolu (eklemsiz
  kol) ayrı bir iş.
* Yuvarlanma pozu (v20) yeni oranlarla yeniden üretildi ama yeniden kurgulanmadı.
* Hayalet izi / darbe karesi kopyalarında kuşak kuyrukları yok (saç var).

## v39: yeni yaratıklar

Geri bildirim: "Çok daha fazla mob ekleyelim ki eğlenceli olsun; güzel görünsünler, saldırıları çeşitli olsun."

### Denetim (v38)

* 5 biyomda 43 sıradan tür vardı, ama yalnızca **11 çizim**: `bekci` 11 tür, `kara_boru` 7, `cor` 6, `agac_iyesi` 4, `arcura`
  3, `tosbaga` 3 tür (biyom çeşitlemeleri, çoğu yalnızca ton / ad farkı). Yapay zekâda yakın dövüşçüler baskındı (shield 7,
  charger 3, pouncer 3, lunger 2); biyom başına uzak saldırgan 1-2.
* Eksikler: çağırıcı yok, yer altından gelen (burrow) yok, iyileştiren / koruyan yok, ışınlanıp arkadan vuran (stalker
  dışında) yok, yer boyunca koşan şok dalgası / üstünden atlanacak saldırı yok, oyuncuyu çeken (zincir / dil) ve ağla tutan yok,
  seken / geri dönen mermi yok, koni (soluk) alan saldırısı yok, yatay pike yapan uçan yok (dalıcılar dikey).

### Yeni yaratıklar (15 çizim, 12 yeni yapay zekâ)

Her biri kendi mürekkep-cel sayfasıyla (`tools/artgen/y39_<kimlik>.py`, dışa aktarım `export_v39.py`), kendi hazırlık sesiyle
(`hazirlik_<kimlik>_1..2`) ve hamle sesleriyle (`v39_*`, `tools/audiogen/v39.py`).

| Kimlik | Ad | Biyom | YZ | Hamleler (hazırlık) | Karşı oyun |
|---|---|---|---|---|---|
| `yer_cucesi` | Yeraltı Cücesi | Ötüken | burrower | kazma "!" 0,38 · yay çizen kaya "!" 0,45 · yere dalış → tümsek oyuncuya yürür → işaretli "!!" çıkış (iki yana fırlatır) | tümsek dokunulmaz: işaretten çekil, çıkıştan sonra 0,8 sn açık |
| `sulmus` (+`sulmus_yavrusu`) | Şulmus | Ötüken (2.) | summoner | runa çemberi "!" 0,7 → 2 yavru (en çok 3 canlı; seçkin 3 / 4) · lanetli kafatası (düştüğü yerde zehir) · yaklaşınca geri sıçrar | önce çağırıcıyı öldür: yavruları dağılır, yavru ganimet bırakmaz |
| `burkut` | Bürküt | Ötüken | swooper (uçan) | yanından yatay pike "!" 0,5 (zırhlı süzülüş, sonra yukarı kıvrılır) · tüy yelpazesi (5; seçkin 7) | pikenin altına yuvarlan, tüyleri yandan geç |
| `tunga_hayaleti` | Tunga Hayaleti | Bozkır | lancer | yerde uyarı şeridi + kargı hücumu "!" 0,62 (bazen "!!") · geniş savuruş "!" 0,42 · ışık ciridi | şeridin dışına çık / üstünden atla; hücum duvarda biter, 0,7 sn kayar |
| `tepegoz_yavrusu` | Tepegöz Yavrusu | Bozkır (4.) | slammer (ağır) | sıçrayıp çakılma "!!" 0,66 → iki yana koşan şok dalgası · üçlü sopa "!" 0,4 · kaya fırlatma | dalganın üstünden atla; çakılmadan sonra 1 sn açık; yavaş döner (arkasına geç) |
| `aldaras` | Aldaraş | Bozkır | ricochet | dönen tunç orak "!" 0,45 (250 px gider, geri döner — iki kez geçer) · ikiz orak kasırgası (4 vuruş) · geri takla | orak dönerken onu tekrar atamaz: dönüşü bekle, kasırgadan geri çekil |
| `agu_kurbagasi` | Ağu Kurbağası | Şahmeran | gasser | zehir bulutu "!" 0,6 (3 sn, 64 px yüksek) · dil kamçısı "!!" 0,42 (çeker + ısırır) · 2 zehir topu (gölcük bırakır) | buluttan uzak dur, dile yuvarlan; topları yandan geç |
| `ag_ana` | Ağ Ana | Şahmeran | webber | ağ yumağı "!" 0,5 (değerse ağa düşersin: 4 basışla kurtul, örümcek koşup ısırır) · ısırık (zehir) · zırhlı sıçrayış | ağı yuvarlanarak geç; ağdayken bas |
| `yilan_kami` | Yılan Kamı | Şahmeran (6.) | healer | yaralı / korumasız yoldaşa yeşil ışın "!" 0,8: %30 can + 4,5 sn koruma (hasar x0,5) · 3 güdümlü ruh · yaklaşınca ışınlanır | önce kamı öldür; korunan yaratık yeşil kıvılcım saçar |
| `kar_cadisi` | Kar Cadısı | Kaf | blinker | kara dönüşür "!" 0,38 → **arkanda** belirir → üçlü pençe "!" 0,3 · buz kıymığı yelpazesi | ışınlanma sesini duyunca dön / yuvarlan; pençeden sonra açık |
| `abasi` | Abası | Kaf (8.) | chainer (ağır) | kancalı zincir "!" 0,55 (200 px; değerse önüne çeker + ağır yumruk) · çift yumruk "!!" 0,7 + öne yürüyen buz dikenleri · zincir savurma (iki yan) | zincire yuvarlan / üstünden atla; yavaş döner |
| `ejder_yavrusu` | Ak Ejder Yavrusu | Kaf | breather | ayaz soluğu "!" 0,65 (0,8 sn salınan koni) · kuyruk savurma (iki yan) · kanatlı sıçrayış "!!" | koninin dışına / arkasına geç |
| `yasavul` | Erlik Yasavulu | Tamu | lancer (ateş) | şeritli teber hücumu (alev izi) · alevli savuruş · ateş ciridi | Tunga gibi; daha ağır ve dayanıklı |
| `kor_solucani` | Kor Solucanı | Tamu | burrower (ateş) | ısırık · lav topu (alev gölü bırakır) · yer altından kor çatlakla gelip ağzıyla fırlar | Cüce gibi; tümsek ateş saçar |

Ortak akış (`Enemy.gd` "v39 yeni yaratıklar", `_ai_v39`): `chase` (menzil bandı ve hamle seçimi) → `windup` (`_tele`, "!" / "!!",
hazırlık ışıması `_v39_wind_fx`) → `act` (etkin evre, hamle tablosu `_v39_fire` / `_v39_act`; anahtar `<ai>/<hamle>`) →
`recover` (hamleye göre ceza penceresi) → `_end_attack` (`V39_BEKLEME`). Özel durumlar `burrow` (yer altı, dokunulmaz) ve
`hold` (ağ / zincir; Gulyabani'nin `get_grabbed` düzeni, Player değişmedi). Jetonlar, baskı altında zırh, sarsılma
bağışıklığı, duruş, seçkin kükremesi v23 kurallarıyla aynı. **Tepki** (`TEPKI`, `_v39_react`): cüce / solucan yere dalar,
çağırıcı / örümcek / Aldaraş geri sıçrar, kam ışınlanır, cadı arkana geçer, kurbağa zırhlı bulut, mızraklı / dev / Abası /
ejder zırhlı savuruş. Seçkinler: fazladan yavru / tüy / kıymık / zehir topu / çok vuruş ve daha uzun koruma.

Animasyon: sayfalar v29 kısa biçimde (`"durum"`: `windup/<hamle>`, `act/<hamle>`, `recover/<hamle>` → `atk_<hamle>` satırı,
`mk` = [W, C, H] ile hazırlık derin kurulmada tutulur, temas karesi etkin evrenin başında); `idle`, `move` (yürüyüşte `vx`),
`hurt`, özel `dig` / `burrow` / `blink` / `hop` / `flip`. Ölüm v36 patlaması (malzeme: `NOT_FLESH` — Tunga Hayaleti ruh, Kor
Solucanı kor, yavru ruh; ötekiler et; `kan` rengi world.json'da).

### Veri (`data/world.json`) ve yerleşim (`Level.gd`)

* Yeni alanlar: `size` [g, y], `flying`, `heavy` (gövde veriden; eskiden sprite adına göre sabit), `ates` (ateş çeşitlemesi),
  `kan` [r, g, b], `ses_can` / `ses_olum`, `agirlik` (havuz payı; yeniler 2), `min_derinlik` (biyomun ikinci derinliğinden),
  `havuz: false` (çağrılan yavru havuza girmez).
* Havuz: her biyoma 2-3 yeni tür, payı 2: biyom karşılaşmalarının ~%33-46'sı yeni yüz (Ötüken 7 → 10 tür, Bozkır 8 → 11, Şahmeran
  8 → 11, Kaf 8 → 11, Tamu 8 → 10; min_derinlik'li türler yalnızca biyomun ikinci derinliğinde). Yoğunluk (v34, ~26 / bölüm) değişmedi.
* Bütün uçanlar havada doğar (eskiden yalnızca `cor`); `swooper` uçan sınıfına, `summoner` / `healer` uzak sınıfına girer
  (karışık grup: yakın + uzak); çağırıcı / şifacı / uçan / ağırlar ikili grup kurmaz.
* Can / hasar 1. derinlik tabanı biyom komşularıyla aynı bantta (zorluk.json derinlik eğrisi ve `rol_can`: swooper / summoner /
  healer 0,85, ricochet / blinker 0,95).

### Mermiler (`Projectile.gd`)

Yeni düşman mermisi biçimleri `orak` (dönen tunç hilal, geri döner), `kargi` (ışık / ateş ciridi), `ag` (ağ yumağı); düşman
mermisinin isabet kancası (`on_hit`). Yay çizen mermiler `_v39_lob` (hedefe düşecek ilk hız), düştüğü yerde gölcük `on_explode`.

### Test

Başsız, `--fixed-fps 60`, betik hatası (SCRIPT ERROR) **0** (bütün koşular):
* `--zeka --zeka_v39 --muhur=0` (`tools/tests/zeka_testi.gd`: yeni `KINDS_V39`, satırda görülen hamleler ve "takılma" =
  idle / chase dışı durumda kesintisiz en uzun süre; Yılan Kamı'nın yanına yaralı, kıpırdamayan bir yoldaş konur): 15 türün
  hepsi hazırlık → etkin → toparlanma döngüsünü tamamladı, her türün bütün hamleleri görüldü (heal dahil), en uzun takılma
  2,7 sn (Kor Solucanı'nın yer altı yürüyüşü, beklenen); PASIF hasar/30 sn 56-397 (eski türler 320-475 bandında: uçan /
  ejder / cadı daha az, Abası / Ağ Ana / Yasavul en çok), EZME hamle/10 sn 3,0-5,5, kilit %1-37.
* `--harita` (120 bölüm): **SONUC GECTI**, geçersiz düşman yerleşimi 0 / 1380, düşman/bölüm 25,6 (ana dal 25,9: yoğunluk korundu), girişe /
  taşa yakın 0. İlk koşuda 1 ana yol odası (köprü, tüccar tezgâhı odaya taşmış) düşmansız kaldı: `_bos_oda_doldur` artık
  sığmayan türden sonra havuzun öbür türlerini ve tezgâh payı 0 ile ikinci geçişi dener; ikinci koşu düşmansız 0.
* `--dovus --boss --kontrol`: KONTROL basış=272 basılmamış=0 oto_dönüş=0 oto_hamle=0 istenmeyen_ağır=0, TAKILMA=0.
* `--otomatik --derinlik=1/3/5/7/9 --muhur=0 --quit-after 9000`: 1 ölüm 0 (can 54-119/130), 3 ölüm 0 (can 70/130), 5 / 7 / 9 her
  birinde 1 ölüm (5: 69. sn Şahmeran, 7: 28. sn Kaf kuyu, 9: 3,5. sn uçurum — düşman öldürmeden, hasar almadan: düşüş);
  ana dalda aynı koşular bu makinede başlamadan kapandı (süre=0), karşılaştırma yapılamadı.
* `--vahset`: 40 ölüm, en kötü kare 11,2 ms, BITTI. `--piksel_tara`: TOPLAM 0.
* `--perf --perf_faz=uretim,savas3,savas7`: dövüşte (23 düşman) dusman_fizik 0,82 / 0,92 ms, dusman_anim 0,29 ms (v38: 1,2-2,6 /
  0,3-0,7), kare ort 7,6 / 7,1 ms, p99 12,4 / 12,1 ms. Bölüm kurma 370 ms (ana dal 399), spawn_enemies 34 ms (ana 23: iri türlerin
  yerleşim denemeleri), ilk kare 62 ms (ana 42: 15 yeni sayfanın ilk yüklenişi).

### Görseller (`docs/v39/mob/`)

* `bestiary.jpg`: 15 çizim, her biri boşta + saldırı temas karesi (oyun sayfasından, ışıma x1,4).
* `oyun_<kimlik>_saldiri.jpg` (12 tür; `oyun_abasi_hazirlik.jpg`): oyun içi, kendi biyomunda etkin hamle anı
  (`--write-movie <x.avi> --resolution 1920x1080 -- --yaratik=<tür,...> --yaratik_cek=<klasör> --derinlik=N`,
  `tools/tests/yaratik_testi.gd`: ilk hazırlıkta ve ilk etkin evrede birer kare). Kök görünümün dokusu temel 960x540 boyunda;
  kareler vahset_testi gibi 1920x1080'e büyütüldü (1:1 değil).

### Bilinen

* Ağ / zincir yakalaması Gulyabani'nin tutuşunu kullanır (4 basış); oyuncu yürürken yavaşlatan ayrı bir ağ yok.
* Tepegöz Yavrusu ve mızraklıların hücresi büyük (448 px); HD sayfaları 8064 px genişliğinde (16384 sınırının altında).
* Sanat ajanlarının listelediği küçük kusurlar: Yasavul koyu zeminde çoğunlukla silüet + kor; kurbağanın bulutu tek kütle;
  örümcek bacakları ince; Kar Cadısı'nın kürkü küçükte önlük gibi.


## v40: ışık ve renk cilası

Amaç: aynı çizimlerle "sinematik" bir kare — biyom başına anahtar / ortam / kenar ışığı, yumuşak gölge, mürekkep ışık
hüzmeleri, canlı yerel ışıklar, film derecelendirmesi (lift / gamma / gain, üç tonlu ayrık tonlama), alçak pus, ince tane,
daha yumuşak kamera ve mürekkep perdeli geçişler. Ortam dokuları (paralaks, karo, süs) ve arayüz bu işin dışında
(ky-ortam / ky-arayuz). Her şey veriyle (`data/stil_v2.json`, `yurt_v2.json`, `konak.json`) ayarlanır; "Işık ve parlama"
düzeyleri korunur: **Az** = derecelendirme / parlama / hüzme / gölge yok (vignette.gdshader), **Hafif** = derecelendirme +
yalnızca geniş parlama, gölgesiz, hüzmesiz, **Tam** = hepsi.

### Işık (`Level._build_lighting`, `add_light`, `light_tex`)
* **Noktasal ışık düşüşü** (`light_tex`): eski gradyan 0,45'te tek kırılmalıydı (sert halkalı ışık); şimdi ters kare benzeri
  dört noktalı yumuşak düşüş (çekirdek sıcak, etek uzun). Bütün çıra / ocak / Kut / mermi ışıkları bunu paylaşır.
* **Yumuşak gölge**: gölgeli nokta ışıkları (yalnızca Tam) `SHADOW_FILTER_PCF5`, `shadow_filter_smooth` 2,6; gölge rengi
  siyah değil biyomun koyu tonu (`art.shadow_col`, yoğunluk `art.shadow_density`): Ötüken lacivert-mor, Bozkır bordo,
  Şahmeran koyu petrol, Kaf gece mavisi, Tamu kızıl-kara.
* **Parlama katmanları**: `set_glow_level` 2. (yarım), 3. ve 5. seviye (Godot varsayılanı 3 + 5): ışık kaynaklarının
  çekirdeği dar, alev / kristal halesi orta, sisli ortam geniş hâle; Hafif yalnızca 5. seviye ve şiddet 0,85.
* **Işık titremesi** (`scripts/core/IsikTitrek.gd`, `Level.titrek(l, tür)`): eski iki adımlı Tween (0,8 → 1,0 → 0,8)
  mekanik nabızdı. Üç uyumsuz sinüs + seyrek rastgele atım (rüzgâr yalaması / çıtırtı) + yavaş nefes; konum yalpası ve sıcak
  renk kayması (alev beyaz-sarıya). Türler: `mesale` (çıra, meşale, fener, ateş topu), `ocak` (ocak, kazan, mangal, usta
  tezgâhı), `lav`, `kristal` (yavaş nefes, titreme yok), `zehir`. Işık kapalıysa (v38 ışık sınırı) eklenmez.
* **Mermi / efekt ışıkları**: ateş topu ışığı 60 → 84 px, enerji 0,8 → 1,0, titrek; `FX.flash_light` (vuruş / patlama
  flaşı) aynı yumuşak düşüşü kullanır. Bezirgân fener direği ve sırt feneri titrek.
* **Kenar ışığı** (`shaders/ink_char.gdshader`, `rim_k` 0,55 / `rim_w` 1,6): sprite alfasının dört komşu örneğinden ekran
  uzayında sözde normal (UV türevleriyle; aynalama / dönüş / esneme güvenli), `NORMAL` yazılır; `light()` içinde ışığa bakan
  kenarda ışığın renginde ince parlama (ay: 0,9 - gölge payı; noktasal: 0,8). İç yüzey düz kalır, cel çizimi bozulmaz;
  meşale yanından geçen Bengü'nün silüeti sıcak kenar alır.

### Hüzme (`shaders/isik_huzme.gdshader`, `Level._build_huzme`, `_isik_tick`)
Dünyanın üstünde (katman 2), derecelendirmenin (5) altında tam ekran toplamalı geçiş; yalnızca Tam ve `--derecesiz` yokken.
Doku yok, yalnızca ALU. Üç kip, biyom `huzme` anahtarıyla karışır: `band` eğik, nefes alan ışık perdeleri (üç uyumsuz
frekans, aşağı doğru sönüş), `blob` yavaş süzülen yumuşak ışık lekeleri, `heat` alttan yükselen titrek kor. `scroll` kamera
x'iyle kayar (ortama bağlı). Biyomlar: Ötüken ay hüzmeleri (soğuk mavi, 4, dik), Bozkır altın saat yelpazesi (3, yatık,
-0,8 rad), Şahmeran biyolüminesans (band 0,5 + blob 0,9, turkuaz), Kaf kar parıltısı (buz mavisi, hızlı), Tamu lav ışığı
(heat, kızıl-turuncu, alttan). Arena: `boss_huzme` (daha kısık). Yurt: lacivert ay hüzmesi 0,08; konak 0,05.

### Derecelendirme (`shaders/grade_v2.gdshader`)
Tek geçiş, sırayla: (renk sapması yalnızca vuruşta) → sRGB → **lift / gamma / gain** (ASC CDL sırası; lift yalnızca
koyulara) → doygunluk + **canlılık** (`vibrance`: az doygun renkleri çok doygunlardan daha çok canlandırır) → üç tonlu ayrık
tonlama (`shadow_tint` / `mid_tint` / **`high_tint` + `high_k`**) → S eğrisi → **sis bandı** (`mist`: alçak pus; iki oktav
değer gürültüsüyle sürüklenir, `mist_y` oyuncunun ayak çizgisinin altına Level her kare yazar, koyuları kaldırır, açıkları
bırakır: ışık kaynakları sisin içinden parlar) → ölüm derecesi → biçimlendirilebilir **vinyet** (`vig_in` / `vig_out` /
`vig_round`) → vuruş vinyeti → **film tanesi** (`grain`, canlı, açıklarda azalır) → v38 titreşim. Vuruşta 0,18 sn **renk
sapması** (`ca`, `Level.flash_red`; Sarsıntı ve flaş ayarıyla ölçeklenir). Az düzeyinde `vignette.gdshader` yalnızca vinyet +
ölüm karartması.

Biyom dereceleri (`stil_v2.json` `grade`): Ötüken soğuk yeşil orta ton, mor gölge, sıcak açık, pus yeşil-gri 0,13; Bozkır
altın saat (sıcak gain, mor gölge, toz pusu 0,10, canlılık 0,10); Şahmeran turkuaz-yeşil, mavi gölge, canlılık 0,18, pus
petrol 0,12; Kaf buz mavisi (mavi gain / gamma, lila gölge, pus 0,16); Tamu kızıl (sıcak gain, bordo gölge, kor pusu 0,08,
karşıtlık 1,12). Tane 0,008-0,012. Vinyet 0,34-0,36 / 0,82-0,90, oval 0,70-0,78.

* **Derinlik havası** (`mood`, `Level._derinlik_havasi`): biyomun ikinci derinliği kendi havasında ("1": daha geç saat /
  daha koyu / daha sıcak): Ötüken daha sisli ve mor, Bozkır gün batımı kızılı, Şahmeran daha koyu ve daha çok leke, Kaf
  pembe alacakaranlık (güneş 1,0 / 0,82 / 0,86), Tamu daha sert karşıtlık, daha güçlü kor. Sözlük anahtarlar (`grade`,
  `huzme`) iç içe birleşir (`_art_birlestir`).
* **Arena** (`boss_grade` / `boss_huzme`): daha dar vinyet (0,26-0,30 / 0,78-0,84), karşıtlık 1,14-1,16, hüzme kısık.
* **Konak** (`konak.json` `genel.grade` / `genel.huzme`): ocak sıcaklığı (sıcak açık ton 0,55, pus 0,06, vinyet 0,36 / 0,9),
  biyom derecesinin üstüne biner. **Yurt** (`yurt_v2.json`): lacivert gölge, sıcak açık, pus 0,09, hüzme 0,08.

### Kamera (`scripts/world/CameraV2.gd`)
* Öncü kayma üstel yaklaşma yerine kritik sönümlü yay (`_smooth_damp`, 0,42 sn; saldırıda 0,12): dönüşte sıçramaz.
* **İniş çöküşü**: 260 px/sn üstü düşüşten yere değince 2-7 birim aşağı çöker, 0,25 sn'de toparlanır (Sarsıntı ayarıyla).
* **Boşta nefes**: 1,4 sn hareketsizlikten sonra çok yavaş süzülme (2,4 x 1,5 birim; 0,46 / 0,31 rad/sn), ilk harekette söner.
* **Boss tanıtımı** (`boss_intro`, 2,2 sn): kamera kükreyen boss'a doğru süzülür (yarıya dek), çerçeve 0,8'e açılır, oyuncuya
  döner; oyuncu bu sırada oynayabilir.
* **Ölüm** (`olum`): 1,10x yavaş yaklaşma, öncü kayma söner; duraklatmada da sürer.

### Geçişler (`scripts/core/Perde.gd`, `shaders/ink_perde.gdshader`)
Ağaç köküne bir kez eklenen katman 6 (vinyet 5 ile arayüz 10 arası); t = 0 iken ColorRect gizli (piksel doldurma yok).
Canlandırma Tween değil elle, **gerçek zamanla ve kare başına en çok 100 ms**: bölüm kurulumunun ardındaki ilk kare (doku /
gölgelendirici) 0,5-2 sn sürebiliyor, Tween o karede süreyi tüketip perdeyi atlıyordu; 250 ms'den uzun kare hiç sayılmaz
(perde kapalı bekler), en geç 3 sn sonra kesin açılır. `--perdesiz` kapatır.
* **Bölüm başı** (`acilis("bolum")`): perde kapalı başlar, 0,08 sn bekler, kuru fırça süpürmesiyle (gürültülü cephe, kıl
  çizgileri, cephenin ardında kâğıt boşlukları) 0,75 sn'de açılır; arena sağdan, bordo kenarlı 0,9 sn.
* **Yurt / konak**: düz solma; konak amber kenarlı 1,1 sn, yurt lacivert 1,0 sn.
* **Işınlanma** (`isin`): kanalın son 0,16 sn'sinde mürekkep lekeleri büyüyüp birleşerek ekranı kaplar (Kut rengi yalnızca
  lekelerin kenarında: `edge = a (1 - a) 4`), varışta 0,42 sn'de çekilir; kesme perdenin ardında kalır. Kanal bozulursa
  perde geri çekilir.
* **Ölüm** (`olum`): derecelendirme malzemesinde `death` 0 → 1 (1,4 sn, gerçek zaman): renk çekilir, soğur, vinyet daralır
  ve koyulaşır; yeni bölümde sıfırlanır.

### Ayarlar
"Işık ve parlama" ipucu güncellendi (Tam: yumuşak gölgeli meşale ışıkları, ışık hüzmeleri, tam parlama ve film
derecelendirmesi). Düşük / Orta hazır ayarlarında (Az / Hafif) hüzme ve yumuşak gölge yok; derecelendirmenin yeni adımları
(sis, tane, canlılık) aynı tek geçişte (fazladan doku okuması yalnızca vuruş sapmasında).

### Ölçüm ve kanıt
* **Çekim** (`tools/tests/isik40_cekim.gd`, `-- --isik40=<klasör> --isik40_on=once|sonra [--isik40_sahne=biyom,yurt,konak,
  boss,isin,olum,gecis] --pencere=1920x1080 --grafik=2 --muhur=0`): her sahne aynı tohum ve aynı kare (10 derinlik giriş +
  bölüm ortası, yurt, 3 konak, 3 arena x 4 kare, ışınlanma 4 kare, ölüm 4 kare, perde 3 kare); perde tamamen açılana dek
  bekler. "Önce" ana dal (3bcc902) dosyalarıyla aynı araçla alındı. **Sayfalar** (`tools/tests/isik40_sayfa.py <çekim>
  <çıktı>`): önce | sonra yan yana, biyom başına bir sayfa, yurt / konak, arena, geçiş şeridi; her çift için ortalama
  parlaklık / doygunluk / koyu (< 0,03) ve patlak (> 0,97) piksel yüzdesi (`tonal_rapor.txt`).
* `docs/v40/isik/`: `biyom_<otuken|bozkir|sahmeran|kaf|tamu>.jpg`, `yurt_konak.jpg`, `boss.jpg`, `gecisler.jpg`,
  `tonal_rapor.txt` (1920x1080, Yüksek); `hd_biyom_<b>.jpg`, `hd_yurt.jpg` (2560x1440, Ultra, 2K doku; yalnızca sonra).
* Tonal: koyu piksel payı her biyomda düştü (Ötüken %19 → 12, Tamu %38 → 20, konak Tamu %44 → 20: lift + pus, gölgeler
  mürekkep rengi), patlak %0,0-0,9 (Kaf kar, değişmedi), doygunluk Şahmeran / Tamu'da 0,62-0,67 → 0,84-0,88 (canlılık +
  sıcak gain), Ötüken / Bozkır / Kaf +0,04-0,10. Ölümde doygunluk 0,58 → 0,27.

### Başarım (Intel UHD 750; ölçümler paralel ajanların Godot süreçleri çalışırken alındı: gürültülü, en iyi koşu verilir)
* `--gpu_perf` 1920x1080, Yüksek, Ötüken 1 (tohum 3), "önce" (3bcc902 dosyaları) ile aynı oturumda dönüşümlü: önce GPU
  17,4 / 23,0 ms (p95 18,8; v38 tablosu 18,3), sonra 20,5 / 25,1 ms (p95 22,1), FPS 47,7 → 41,6 (en iyi koşular). Ayrıştırma
  (`--huzmesiz`, `--golgesiz`, `--sertgolge`, `--derecesiz`, kenar ışığı kapalı): ilk sürümde tam ekran hüzme geçişi ~2,5 ms,
  derecelendirme eklentileri (sis gürültüsü, tane, canlılık, lift / gamma / gain) ~2 ms, PCF5 gölge ~0,5-1 ms, kenar ışığı
  ~0,3 ms. Hüzme çeyrek çözünürlüklü SubViewport'a alındı (480x270 HDR, toplamalı gerdirme; görüntü aynı, ort. piksel farkı
  < 4 / 255) ve sis gürültüsü tek oktava indi: toplam ek maliyet ~6 → ~3 ms. Tamu 9 ve vahşet aynı bantta (24,6 / 27,0 ms,
  önce 33,2 / 24,6: gürültü). Orta (Hafif: derecelendirme var, hüzme / gölge yok): GPU 5,5 / 8,3 / 5,8 ms (v38 4,3 / 4,5 /
  4,3), kare CPU'ya bağlı (49-55 FPS). Düşük (Az): derecelendirme kapalı, değişmedi.
* `--perf` (başsız, makine yüklü): bölüm kurma 20 tohum ort. 475 ms (v38 473), ilk kare 82 ms; düğüm sayıları iki turda aynı
  (sızıntı yok). Kamera 0,07 ms/kare, bolum (sis / hüzme yazımı dahil) 0,20 ms; IsikTitrek 40-55 ışıkta ölçülemeyecek kadar
  küçük (kare başına birkaç sinüs).
* Testler (betik hatası 0): `--otomatik --derinlik=1/3/5/7/9 --muhur=0`, `--sahne`, `--yurt --yurt-tur`, `--konak`,
  `--boss=kara_boru_han/sahmeran/erlik_han`, `--isinlan`, `--piksel_tara`, `--otomatik --g_isik=0/1` (Az / Hafif), `--perf`.
  Düzeltilenler (ilk sürüm): `Perde._get` adı `Object._get` ile çakışıp Level → Ayarlar zincirini derlenemez bırakıyordu
  (`_ornek`); `set_glow_level` sırası 0..6; `Perde` kök çocukları kurulurken (ilk bölüm `Main._ready` içinden) `add_child`
  yasak: ekleme ertelenir, iş ağaca girince uygulanır; perde Tween'i bölüm kurulumunun uzun ilk karesinde atlanıyordu (elle,
  gerçek zamanlı canlandırma).

### Bilinen
* Yüksek'te 1080p GPU maliyeti v38'e göre ~3 ms (%15) yüksek; Orta +1-2 ms. Daha ucuz seçenek gerekirse `--sertgolge`
  (PCF5 yerine keskin gölge, ~1 ms) ve `--huzmesiz` bayrakları veriye / ayara bağlanabilir.
* Çekim aracı "giriş" karelerini biyom başlığı ekrandayken alır (1,6 sn); önce / sonra aynı kare olduğu için karşılaştırma
  bozulmaz. Ölüm derecesi 0,3 sn'de henüz hafif (`olum_a`), 0,9 sn'den sonra tam (`olum_b-d`).
