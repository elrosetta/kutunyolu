# v29: düşman animasyon json sözleşmesi (evre eşlemeli oynatma)

Bu sözleşme ile bir düşman sprite'ı (`assets/sprites/<ad>_v2.json`), **Enemy.gd / SpriteAnim.gd'ye dokunmadan**, yapay
zekânın evrelerine (hazırlık "!" / "!!", vuruş, etkin pencere, toparlanma, havada, tepkiler, ölüm) bağlı kare seçimi
alır. Json'da `"durum"` yoksa her şey eskisi gibidir (eşit aralıklı `play` / `show_frame`).

Üreten araç: `tools/artgen/yaratik_govde.py` (`Seq`, `layout`, `anim_meta`) + `tools/artgen/export_yer.py`.
Oynatan: `Enemy._anim_tick` (her `_process`), `SpriteAnim.director`.

## 1. Üst düzey alanlar

```json
{
  "cell": [320, 224], "origin": [144, 208], "texel": 4.0, "filter": "linear", ...
  "v29": 1,
  "durum": { "<anahtar>": { "a": "<animasyon>", "s": "<evre>", "u": "st|up|vy|loop", "d": 0.22 }, ... },
  "anims": { ... }
}
```

* `"durum"` sözlüğü olan her sayfada yönetmen (director) açıktır (`"v29": 1` bilgi amaçlı; yer yaratıkları yazar): yapay zekânın `anim.play(...)` / `anim.show_frame(...)` çağrıları yalnızca
  **istek** olarak kaydedilir (`SpriteAnim.req`); gösterilecek kareyi `Enemy._anim_tick` seçer. Eşleme bulunmazsa istenen
  animasyon olağan biçimde oynar (geri dönüş: eski davranış).
* `"durum"` — yapay zekâ durumu → animasyon eşlemesi (aşağıda).

## 2. `durum` anahtarları (arama sırası)

Her karede düşmanın `state`'i, hamlesi (`move`) ve zırhı (`sa_t > 0` → `!!`) ile şu sırayla aranır; ilk bulunan kullanılır:

1. `<önceki>><durum>` — geçiş (ör. `"dormant>recover"`: uyanış; `"lurk>windup"`: pusudan fırlayış)
2. `<ai>:<durum>/<hamle>!!`, `<ai>:<durum>/<hamle>`, `<durum>/<hamle>!!`, `<durum>/<hamle>`
3. `<ai>:<durum>!!`, `<ai>:<durum>`, `<durum>!!`, `<durum>`

* `<ai>`: Enemy.ai (`lunger`, `brute`, `shield`, `charger`, `turtle`, `archer`, `charmer`, `illusionist`, `grabber`,
  `mimic`, `hopper`, `pouncer`, `crawler`, `stalker`, `tornado`, `caster`, `diver`, `swarm`, `flyer_ranged`, `kamikaze`, boss...).
  Aynı sayfayı farklı yapay zekâlar paylaşır (ör. `bekci_v2`: shield + charger) — `<ai>:` öneki ayırır.
* `<hamle>`: zırhlı intikamda `get_meta("rev")` (`spin` / `cut` / `bash` / `grab`); charger'da `bash` ya da `charge`;
  pouncer'da `pounce` (perch'ten atlayış); diğerlerinde `get_meta("move")` (brute: `swat` / `slam` / `leap` / `roots`,
  shield: `jab` / `heavy` / `bash`, hopper: `cut` / `leap`, grabber: `claw` / `grab`, mimic: `snow`, flyer: `spore` / `dive`,
  charmer: `charm` / `curse`, caster: `pool` / `orbs`, tornado: `gust` / `spin`). Hamle saldırı bitince de durur, böylece
  `recover/<hamle>` toparlanmayı hamleye göre seçer.
* `!!`: hazırlık zırhlı başladıysa (`_tele(t, true)` ya da baskı altında otomatik zırh) — "!!" pozu "!" pozundan ayrı çizilir.
* Durum her değiştiğinde (ya da `_tele` aynı durumu yeniden başlattığında) evre saati sıfırlanır: `st0` = girişteki `st`,
  `vy0` = girişteki dikey hız.

### Ayrılmış (tepki) anahtarları — durumdan önce gelir

| anahtar | ne zaman | öneri |
|---|---|---|
| `_launch` | havaya fırlatıldı (`launch_t > 0`) ya da Göğe Yükseliş kilidi | `u: vy` |
| `_break` | duruş kırık (`broken_t`) ya da sersem (`stun_t`) | `u: loop` |
| `_hurt_big` | büyük vuruşla sarsıldı (kritik / bitiriş / ağır / itme > 180) | `u: up, d ≈ 0,45` |
| `_hurt` | hafif sarsılma | `u: up, d ≈ 0,22` |
| `_getup` | savrulmadan yere indikten sonra (yatay hız < 40 iken) | `u: up, d ≈ 0,5` |
| `_turn` | boşta / kovalamada yön değişti (yatay hız < 60 iken) | `u: up, d ≈ 0,2` |
| `_roar` | seçkin kükremesi (yatay hız < 30 iken) | `u: up` |
| `_guard` | Balbal siperi (`guard_t > 0`, boşta / kovalamada) | `u: loop` ya da `up` |
| `_spawn` | doğuştan sonra bir kez (boşta / kovalarken / perch / lurk) | `u: up` (kısa biçim `spawn`) |
| `blink_in` | ışınlanmadan sonra (boşta / toparlanmada) | kısa biçim; `blink_out` eski yerde çözülen kopya |
| `_death` | ölüm: ceset (Corpse) bu kareleri `d` sn'de oynar, savrulmaz, ayakları yerde kayar, sonra çözülür | `u: up, d ≈ 0,9` |

Donma (`freeze_t`) kareyi olduğu yerde tutar. Zırhlıyken (saldırı ortasında) vurulan yaratık tepki göstermez: hamlesini
sürdürür (okunur "!!"). Zırhlı ağır yaratık boşta / kovalarken vurulursa `_hurt` yine gösterilir (yapay zekâ durmaz).

## 3. Giriş (`durum` değeri)

İki biçim kabul edilir:

* **Kısa biçim** (uçan / büyücü sayfaları): `"windup": "tele"` — değer yalnızca satır adı (`u: auto`). Kısa adlar:
  `windup_zirh` = `windup!!` (zırhlı "!!" hazırlık), `death` = `_death`, `spawn` = `_spawn` (doğuşta bir kez, boşta /
  kovalarken), `explode` = `kamikaze:windup` (fitil), `blink_out` (ışınlanmadan önceki yerde bir kez oynayıp çözülen kopya)
  / `blink_in` (yeni yerde belirme), ayrıca düz durum adları (`stuck`, `stagger`, `evade`, `spin`, `dizzy`...).
  `auto`: döngü satırı döner; satırda **`mk` = [W, C, H]** varsa (0 ve 1 örtük: evreler [0, W, C, H, 1], Bengü v28
  kuralı, isteğe bağlı `ts` kare başlangıç zamanları) hazırlık durumu [0, W]'ye (son 0,05 sn süpürme [W, C]), vuruş /
  etkin durumlar (attack, dive, swoop, strike, slam ...) [C, H]'ye, toparlanma [H, 1]'e eşlenir; `mk` yoksa geri sayan
  durumda `st / st0`, ileri sayanda satırın kendi süresi (kare / fps).
* **Giriş sözlüğü** (yer yaratıkları):

| alan | anlam |
|---|---|
| `a` | animasyon adı (`anims` içinde) |
| `s` | evre adı (animasyonun `seg` alanında); yoksa bütün satır |
| `u` | ilerleyiş kaynağı: `st` = geri sayan durum (`1 - st / st0`; hazırlık, vuruş, toparlanma, sersemleme), `up` = durum girişinden beri geçen süre / `d` (ileri sayan durumlar, tepkiler), `vy` = dikey hız evresi (`(vy - vy0) / (-2 vy0)`: 0 kalkış, 0,5 tepe, 1 iniş; sıçrayış, sekiş, savrulma), `loop` = döngü (animasyonun `fps`'i; satırda `vx` varsa yatay hızla ölçeklenir) |
| `d` | `up` için süre (sn) |

İlerleyiş [0, 1]'e kırpılır: son kare tutulur (ör. hazırlığın derin kurulma karesi "!" boyunca bekler).

## 4. Animasyon satırı alanları (`anims.<ad>`)

```json
"windup": {"row": 4, "frames": 4, "fps": 10, "loop": false, "data": [...],
           "seg": {"windup": [0, 4]}, "ts": [0.0, 0.22, 0.5, 0.0], "lead": {"windup": 0.05}}
"run":    {"row": 2, "frames": 8, "fps": 18, "loop": true, "vx": 80.0, "alt": [["walk", 46.0]]}
```

| alan | anlam |
|---|---|
| `seg` | `{evre: [ilk, son)}` kare aralıkları. Bir satır birden çok evre taşıyabilir (ör. `slam`: `windup` [0,4), `strike` [4,6), `recover` [6,9)); `durum` girişinin `s` alanı hangisinin oynayacağını seçer |
| `ts` | her karenin **kendi evresi içindeki** başlangıç anı (0..1). Gösterilen kare: ilerleyişi geçmemiş son `ts`'li kare. Eşit aralıklı değil: derin hazırlık karesi uzun tutulur, temas karesi evrenin başında açılır |
| `lead` | `{evre: sn}` — `u: st` evrelerinde evrenin SON karesi evrenin son N saniyesinde gösterilir (öteki kareler kalan süreye `ts` ile yayılır). Hazırlığın bitiminde "fırlayış / süpürme" karesi: isabet karesinden hemen önce |
| `vx` | yapay zekâ bu döngüyü yürüyüş/koşu olarak oynattığında `dspeed = |vx_gerçek| / vx` (0,5..2,2): adım boyu hıza kilitli, ayak kaymaz |
| `alt` | `[[animasyon, azami hız], ...]` — istenen döngü yerine yatay hız eşiğin altındaysa bu oynar (ör. yavaş "run" → "walk") |

Kural: hazırlık (`windup`) evresinin ilk karesi dinlenmeden çıkış, son karesi (lead) atılış; vuruş evresinin (`strike`)
İLK karesi temas/isabet karesidir (yapay zekâ vuruş kutusunu tam o karede açar). Vuruş kutuları / zamanlar değişmez:
animasyon evrelere gerilir.

Geriye dönük uyum: durum eşlenmemişse yapay zekânın isteği aynen oynar — `show_frame("attack", 0/1)` gibi doğrudan kare
seçimleri de (`SpriteAnim.req_frame`).

## 5. Ölüm (`_death`)

`Enemy._die` → `Corpse.setup` + `Corpse.play_frames(...)`: ceset sprite'ı satırın karelerini `d` sn'de (kısa biçimde
satırın kendi süresi kare / fps) oynar, dönmez, darbe yönünde kısa kayar (ayak çizgisi yerde), son kare tutulur, sonra çözülür (kül). `_death` yoksa
eski savrulan ceset.

## 6. Geliştirme araçları

* `python tools/artgen/yer_onizleme.py <sprite> <çıktı.jpg> [anim ...]` — karelerin şeridi (yer çizgisi, evre, ts).
* `python tools/artgen/export_yer.py [sprite ...]` (+ `KY_HD=2`, sonra `python hd_paket.py --paketle`).
* Yeni bir yaratık modülü: `SEQS` (sözlük sırası = satır sırası), `DURUM`, `CELL`, `FEET`, `TEX`, `render_frame(anim, i[, var])`;
  `export_yer.SHEETS`'e satır eklenir. `yaratik_govde.check_durum` adları denetler.
