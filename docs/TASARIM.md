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
* **Test:** `-- --doku=0..3 --pencere=2560x1440 --goruntu=cikti.png` (6 sn sonra ekranı kaydeder ve çıkar).
* **Başlatıcı:** `Oyunu_Baslat.bat` her açılışta içe aktarır; GitHub'dan çekilen yeni dosyalar içe aktarılmazsa oyun boş ekranda kalıyordu.

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
| Alp Kılıcı | dengeli, 0,45 | diag_down → horiz → step_down (adım) | cross_x Alp Çaprazı | overhead_2h | 3. vuruş kritik (ucuncu_vurus) | down, horiz, overhead_2h |
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
| Kargı | 0,5 | pole_thrust → pole_thrust → lunge_long | lunge | stab_heavy | **↑+J sırık atlayışı**, koşarken hücum kritiği | thrust, lunge_long, uppercut |
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
**Kamera:** v2 mürekkep ortamında taban yakınlık 1,5 (`stil_v2.json` "camera_zoom", `Game.base_zoom`; zoom_punch bunun üstüne
çarpılır): ekranda 640x360 dünya birimi, karakterler 1,5 kat büyük (referanstaki oran). v1 çerçevesi (960x540, 1,0) değişmez.
Paralaks ve ön plan kayma çarpanları yakınlıkla çarpılır (derinlik hissi aynı kalır).
**Doku yoğunluğu:** dünya uzayı (zemin atlası 72 px hücre, toprak/çayır, süsler, kule parçaları) 3 doku pikseli / dünya birimi;
ekran uzayı katmanlar (paralaks, ön plan) 1080 yükseklik: **1080p'de 1 doku pikseli = 1 ekran pikseli**. Üreticiler mantıksal
piksellerle yazılır, `inkkit.K` (dünya dokularında 1,5) çıktı çözünürlüğünü ölçekler.
Bütün v2 ortam dokuları doğrusal süzgeç + mipmap (`.import` mipmaps açık, düğümde `TEXTURE_FILTER_LINEAR_WITH_MIPMAPS`);
v1 yolu hiç değişmez (en yakın komşu, piksel keskin). Yalnızca `--stil=v2` ve `assets/tiles/otuken_v2.json` "ink": true iken.

* **Üretim:** `cd tools/artgen && python export_ink.py [--bg [katman...]|--zemin|--on|--suslar]` (ya da `export_v2.py --otuken`).
  `inkkit.py` (skia-python + numpy): önçarpılmış katman, döşenebilir gürültü, değişken kalınlık fırça darbesi (`ribbon`), ot yaprağı,
  mızrak yaprak, organik kontur, analitik ağaç gövdesi (`trunk`: silindirik gölge, sisten kenar ışığı, iki yanda değişken mürekkep,
  çam = kırık dikey sırt + levha çatlağı, huş = mercimek izi + dal yarası, gölge tarafında çizgi roman taraması, pürüzlü kök
  boğazı), satır başına sis karıştırma. `otuken_ink.py` paralaks katmanları, `otuken_ink_ground.py` zemin/ön plan,
  `otuken_ink_decor.py` süsler. Tümü yordamsal; dışarıdan doku yok.
* **Paralaks** (`data/stil_v2.json` "otuken": "bg", "bg_fx", "bg_kind"): 0 gök/uzak sis (1920x1080, sabit; ay ışığının süzüldüğü
  parıltı, tepe yaprak gölgesi), 1 uzak gövdeler (3840x1080, x0,06), 2 uzak-orta gövde + dal + çalı tümsekleri (x0,13),
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
* **Yoğunluk:** `texel` 3 (dünya 640x360 x3 = 1080p'de 1 doku pikseli = 1 ekran pikseli). Bengü hücresi 288x240
  (dünya 96x80, ayak 132,222), tazı 240x168, kol parçası 42x51 (pivot 21,10.5; yumruk 21,25.5).
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
  arkaya sıçrantı), `stamp` (kritik: siyah damga + kızıl patlama + beyaz-sıcak kesik), `slam` (yer sıçrantısı,
  GroundSlamFX ile birlikte), `flourish` (savuşturma: ensō + kıvılcım; kusursuz kaçış: ayaz ensō + halka), `ring`,
  `kill`. Açılış ilk karede %62 hazır (hitstop'ta zaman durur; donmuş karede boş kalmaz). Vuruş izden önce işlendiği
  için palet ilk karelerde yakındaki taze izden alınır (`auto_pal`). FX yönlendirmeleri: `slash_sprite` (yay/çizgi/
  halka/x: iz zaten çizer; spark_m / crit_burst / kill_flash → mürekkep; boss arc_* → `InkTrail.auto_arc`),
  `impact_sprite`, `impact`, `slash` (düşman yayı → kendiliğinden süpürülen fırça), `ring`, `ground_slam` (+ mürekkep
  sıçrantısı), darbe animasyonları (`FX.INK_ANIM`: PVFX piksel kareleri yerine mürekkep), parçacık ve kalan
  animasyonlarda doğrusal süzgeç (yakın kamerada bloklaşmasın). Player'da savuşturma ve kusursuz kaçışa birer satır.
* **Silahlar** (`tools/artgen/weapons_ink.py` → `assets/weapons/weapons_v2.json` + `weapons_v2_<n>.png`): geometri
  v1 `weapons_myth.draw_item` ile birebir (aynı kimlik, pivot, dünya boyu); hacim tuvali 2x süper örneklemle
  rasterlanıp mürekkep-cel boyanır: düz taban + tek sert gölge tonu + ışığa bakan pah için açık ton, metal/taşta
  küçük keskin parlama ve bıçak boyunun %62'sinde çift çapraz çizgi roman parıltısı, alttakine düşen gölge,
  dış silüet ışık yanında ince / gölge yanında kalın mürekkep (#15161d), parçaların üst üste geldiği yerde ince iç
  çizgi; ahşap damarı, sargı, süs, ışıyan damarlar v1 boyamasından. Doku 4 piksel / dünya birimi (v2 kamerası 2x:
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

