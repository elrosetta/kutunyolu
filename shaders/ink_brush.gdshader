// Stil v2 mürekkep fırçası savuruş izi (scripts/core/InkTrail.gd). Shinobi: Art of Vengeance referansındaki kızıl
// fırça darbesi: kıl çizgili gövde, kuru fırça boşlukları, koyu kızıl çekirdek + siyah fırça izleri, turuncu kenar,
// bıçak ucunda beyaz-sıcak ön kenar, kısa ışıma; yaşlandıkça kenardan yenir ve kıl tellerine ayrılarak erir.
//
// Veri (renk değil): renk paleti uniform; köşe verisi:
//   UV.x  fırça boyunca koordinat (dünya birimi / 40; bristle.png boyuna sarar)
//   UV.y  enine v (0 iç kenar .. INK_W mürekkep dış kenarı .. 1 ışıma kenarı) + 2 x katman
//         katman 0 ana darbe, 1 arka (ağır / bitiriş: geniş, koyu, kuru), 2 yankı (saplama izi), 3 zerre
//   COLOR.a yaş 0 (taze) .. 1 (ölü). (COLOR.rgb kullanılmaz: HDR 2D'de doğrusala çevrilir.)
// Zerre katmanında UV.x = 0..1 (kuyruk -> baş) + 2 x tür (0 mürekkep, 1 gövde rengi, 2 sıcak kıvılcım).
// v20 unsur zerreleri (aynı katman): 3 alev dili, 4 buz kıymığı, 5 şimşek arkı, 6 ruh dumanı / ayaz sisi, 7 yaprak;
// hepsi fwidth ile kenar yumuşatmalı, mürekkep konturlu (renk silahın unsur paletinden).
// v25: 3 gerçekçi alev dili (dünya uzayında yukarı akan, alanı bükülmüş fbm gürültüsü; ak-sarı çekirdek → turuncu →
// koyu kızıl → is konturu), 8 kor / polen zerresi (hız yönünde hareket bulanıklığı), 9 çiçek yaprağı, 10 kor yatağı
// (alev gölü tabanı: kara kabuk + kızgın çatlaklar). Katman 4: Yer-Su sarmaşık filizi / kök şeridi (UV.x = s + 2 x tür).
// unsur_id 1 (od): ana hilal de alev gövdesi (aynı gürültü, sıcaklık rampası, is konturu); 2 (Yer-Su): yeşil-altın
// yaprak hilali (altın orta damar + yan damarlar).
// Karıştırma önçarpılmış alfa: mürekkep normal örter, ışıma (alfa 0) toplamalı eklenir — tek çizim çağrısı.
shader_type canvas_item;
render_mode blend_premul_alpha, unshaded;

uniform sampler2D bristle : filter_linear_mipmap, repeat_enable;
// palet (doğrusal): mürekkep, çekirdek, gövde, kenar, sıcak
uniform vec3 c_ink = vec3(0.004, 0.001, 0.002);
uniform vec3 c_core = vec3(0.16, 0.003, 0.006);
uniform vec3 c_body = vec3(0.78, 0.012, 0.006);
uniform vec3 c_rim = vec3(1.0, 0.16, 0.02);
uniform vec3 c_hot = vec3(1.0, 0.86, 0.62);
uniform float hot_gain = 2.4;      // HDR: ön kenar bloom eşiğini aşar
uniform float glow_gain = 0.55;    // dış ışıma (toplamalı)
uniform float rough = 1.0;         // kenar pürüzü ve kuruluk (ağır silah > 1)
uniform float streaks = 1.0;       // siyah fırça izi miktarı
uniform float dry_in = 0.55;       // iç kenarın kuruluğu
uniform float u_scale = 1.0;       // v20: kıl dokusunun boyuna ölçeği (ağır silah < 1: uzun sürüklenen kıl izleri)
uniform float core_gain = 1.0;     // v23: hilalin taze (ön) kısmında parlak iç çekirdek
uniform float er_delay = 0.0;      // v23: erime gecikmesi (yaş oranı): kısa ömürlü hilal ilk karelerinde dolu kalsın
uniform int unsur_id = 0;          // v25: 0 sade / diğer, 1 od (alev gövdeli hilal), 2 Yer-Su (yaprak hilali)
uniform float ink_w = 0.83;        // v25: mürekkep dış kenarının enine v'si (od hilalinde dış alev saçağı için geniş şerit)
// v31 profesyonel hilal (yalnızca oyuncu izi): silah_firca.png (tools/artgen/silah_fx_ink.py) 8 satır hilal fırçası.
// Şerit köşelerinde UV.x = u (0 bıçağın taze ucu .. 1 kuyruk) + 2 x satır; katman 1 arka yıkama / kuru sürüntü,
// 2 yankı, 5 hız telleri. Katmanlar (dıştan içe): bıçak ağzında ince ak-sıcak hat, hemen içinde parlak çekirdek bandı,
// paletin renginde kıl damarlı gövde, iç yarıda sumi siyahı kıl çizgileri, iç kenarda kıl uçlarına ayrılan kuru fırça;
// yaşlandıkça renk mürekkebe kurur ve kıllar kimlik sırasıyla kopar; ardında daha uzun yaşayan gri sulu yıkama.
uniform int v31 = 0;
uniform sampler2D firca : filter_linear_mipmap, repeat_disable;
uniform float edge_gain = 1.0;     // v31: bıçak ağzı hattının parlaklığı (aile)
uniform float wash_a = 0.34;       // v31: arka yıkamanın örtüsü
uniform float band_in = 0.62;      // v31: turuncu kenar tonu basamağının başladığı enine v (geniş hilalde dışa kayar)
uniform float core_in = 0.86;      // v31: ak-sıcak çekirdek basamağı

varying vec2 wpos;                 // v25: dünya konumu (iz düğümü top_level, kökte: yerel = dünya) -> alev gürültüsü

// ---- v25 gürültü ve alev rampası
float h21(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(h21(i), h21(i + vec2(1.0, 0.0)), u.x), mix(h21(i + vec2(0.0, 1.0)), h21(i + vec2(1.0, 1.0)), u.x), u.y);
}

float fbm(vec2 p) {
	float s = 0.0;
	float a = 0.5;
	for (int i = 0; i < 4; i++) {
		s += a * vnoise(p);
		p = mat2(vec2(1.6, 1.2), vec2(-1.2, 1.6)) * p + vec2(17.0, 9.0);
		a *= 0.5;
	}
	return s / 0.9375;
}

float fire_n(vec2 w, float t) {
	// alev türbülansı: dünya biriminde, dikeyde uzamış (alev dilleri dik), zamanla yukarı akar (kaldırma), alanı
	// ikinci bir fbm ile bükülür (dillerin kıvrılıp çatallanması). Dönen ~0..1 (ortalama ~0,5)
	vec2 q = w * vec2(0.16, 0.055) + vec2(0.0, t * 3.4);
	vec2 wr = vec2(fbm(q * 0.8 + vec2(3.1, t * 1.2)), fbm(q * 0.8 + vec2(7.7, 1.3 - t * 0.7)));
	return fbm(q * 1.3 + (wr - 0.5) * 2.2);
}

const vec3 F_SMOKE = vec3(0.016, 0.007, 0.005);
const vec3 F_DRED = vec3(0.24, 0.012, 0.004);
const vec3 F_RED = vec3(0.78, 0.07, 0.008);
const vec3 F_ORANGE = vec3(1.0, 0.3, 0.025);
const vec3 F_YELLOW = vec3(1.0, 0.7, 0.16);
const vec3 F_WHITE = vec3(1.0, 0.93, 0.72);

vec3 fire_ramp(float T, float aa) {
	// sıcaklık 0 (is) .. 1 (ak-sıcak); cel bantları yumuşak geçişli (mürekkep / çizgi stili ile gerçekçi alev arası)
	float w = 0.045 + aa;
	vec3 c = mix(F_SMOKE, F_DRED, smoothstep(0.1 - w, 0.1 + w, T));
	c = mix(c, F_RED, smoothstep(0.27 - w, 0.27 + w, T));
	c = mix(c, F_ORANGE, smoothstep(0.46 - w, 0.46 + w, T));
	c = mix(c, F_YELLOW * 1.25, smoothstep(0.66 - w, 0.66 + w, T));
	c = mix(c, F_WHITE * hot_gain, smoothstep(0.84 - w, 0.84 + w, T));
	return c;
}

void vertex() {
	wpos = VERTEX;
}

vec3 fleck(float u, float v, float typ, float age, out float a) {
	// damla: kuyruk (u=0) ince, baş (u~0,75) dolgun; yaşla küçülür
	float y = abs(v * 2.0 - 1.0);
	float w = sin(3.14159 * pow(clamp(u, 0.0, 1.0), 2.0)) * (1.0 - age * age * 0.85);
	float m = w - y;
	float aa = fwidth(m) * 0.9 + 0.02;
	a = smoothstep(-aa, aa, m);
	if (typ < 0.5) {
		return c_ink * 0.3;
	} else if (typ < 1.5) {
		return mix(c_body, c_core, age);
	}
	a *= 0.85;
	return mix(c_hot * hot_gain, c_rim, smoothstep(0.0, 0.6, age));
}

vec4 elem(float u, float v, float typ, float age, vec2 uv) {
	// v20 unsur zerresi: u kuyruk(0) -> baş(1), v enine 0..1. Dönen: önçarpılmış renk + alfa (alfa 0 = toplamalı ışıma)
	vec2 p = vec2(u * 2.0 - 1.0, v * 2.0 - 1.0);
	if (typ < 3.5) {
		// v25 gerçekçi mürekkep alevi: dörtgen dik (u dip 0 -> uç 1). Zarf: geniş dip, sivri uç; dünya uzayındaki
		// yukarı akan türbülans (fire_n) zarfı yer: diller kıvrılır, çatallanır, yaşla tepeden kopup is tutamlarına
		// ayrılır. Komşu diller aynı gürültü alanını paylaştığından üst üste binince tek alev örtüsü gibi okunur.
		// Renk sıcaklıktan: dipte / içte ak-sarı, dışa doğru turuncu → koyu kızıl, kenarda ince is (mürekkep) konturu.
		float y = clamp(u, 0.0, 1.0);
		float x = abs(p.y);
		float tt = mod(TIME, 600.0);
		float n = fire_n(wpos, tt);
		// yumuşak zarf (gürültü baskın: dilleri zarf değil türbülans biçimlendirir; mum alevi gibi durmasın)
		float env = (1.0 - x * x) * pow(1.0 - y, 1.1) * smoothstep(-0.1, 0.18, y);
		float d = env * 1.4 - 0.22 + (n - 0.5) * 1.25 - age * (0.45 + 0.8 * y);
		float aa = fwidth(d) + 0.01;
		float a = smoothstep(-aa, aa, d);
		float T = clamp(d * 0.75 + (1.0 - y) * 0.26 - age * 0.5 - 0.03, 0.0, 1.0);
		vec3 c = fire_ramp(T, aa * 0.5);
		// kontur: dipte koyu kızıl, tepeye doğru isleşir (üst üste binen dillerin iç kenarları kesik çizgi gibi
		// okunmasın diye yarı saydam ve kızıl)
		float rim = 1.0 - smoothstep(0.0, 0.07 + aa * 2.0, d);
		c = mix(c, mix(F_DRED, F_SMOKE, 0.3 + 0.6 * y), rim * 0.8);
		// tepe ve yaşlı kısım: is tutamı (koyu, yarı saydam)
		float sm = smoothstep(0.5, 1.05, y + age * 0.55) * (1.0 - smoothstep(0.3, 0.6, T));
		c = mix(c, F_SMOKE * 1.6, sm);
		a *= (1.0 - sm * 0.5) * (1.0 - smoothstep(0.7, 1.0, age));
		// sıcak çekirdek kısmen toplamalı (ışık yayar: üst üste binen diller parlar, birbirini örtmez)
		return vec4(c * a, a * (1.0 - 0.5 * smoothstep(0.5, 0.9, T)) * (1.0 - rim * 0.35));
	} else if (typ < 4.5) {
		// buz kıymığı: sivri eşkenar dörtgen, iki yüzey (ışıklı / gölgeli), beyaz kılcal sırt, mürekkep kontur
		float m = 1.0 - (abs(p.x) * 1.0 + abs(p.y) * 1.9);
		float aa = fwidth(m) * 1.2 + 0.02;
		float a = smoothstep(-aa, aa, m) * (1.0 - smoothstep(0.6, 1.0, age));
		vec3 c = p.y < 0.0 ? mix(c_rim, c_hot, 0.5) : c_body;
		c = mix(c, c_hot * 1.6, (1.0 - smoothstep(0.0, 0.09, abs(p.y))) * smoothstep(0.1, 0.5, m));
		c = mix(c, c_ink, 1.0 - smoothstep(0.0, 0.16, m));
		return vec4(c * a, a);
	} else if (typ < 5.5) {
		// şimşek arkı: beyaz-sıcak kılcal çekirdek, renkli ışıma (toplamalı), uçlarda yuvarlak
		float r = length(vec2(max(abs(p.x) - 0.85, 0.0) * 6.0, p.y));
		float core = 1.0 - smoothstep(0.1, 0.24, r);
		float glow = pow(1.0 - smoothstep(0.15, 1.0, r), 2.0);
		float k = 1.0 - age * 0.6;
		vec3 c = mix(c_rim * 1.4, c_hot * hot_gain * 1.4, core);
		float a = clamp(core + glow * 0.6, 0.0, 1.0) * k;
		return vec4(c * a, core * 0.35 * k);
	} else if (typ < 6.5) {
		if (unsur_id == 1) {
			// v25 od: alevin üstünden yükselen mürekkep isi: koyu, yarı saydam, gürültüyle yenen kenar
			float tt6 = mod(TIME, 600.0);
			float n6 = fbm(wpos * 0.16 + vec2(0.0, tt6 * 1.2));
			float m6 = 1.0 - length(p) + (n6 - 0.5) * 1.1 - age * 0.6;
			float aa6 = fwidth(m6) + 0.02;
			float a6 = smoothstep(-aa6, aa6 * 4.0, m6) * 0.38 * (1.0 - age);
			vec3 c6 = mix(F_SMOKE * 2.5, F_DRED * 0.5, smoothstep(0.2, 0.6, n6) * (1.0 - age));
			return vec4(c6 * a6, a6);
		}
		// ruh dumanı / ayaz sisi: kıl dokusu gürültüsüyle yenen yumuşak yıkama, ıslak koyu kenar
		vec4 n = texture(bristle, uv * vec2(0.37, 0.5) + vec2(age * 0.2, 0.0));
		float m = 1.0 - length(p) + (n.a - 0.5) * 0.7 + (n.r - 0.5) * 0.3 - age * 0.45;
		float aa = fwidth(m) + 0.03;
		float a = smoothstep(-aa, aa * 6.0, m) * 0.72 * (1.0 - age);
		vec3 c = mix(c_rim, c_body, 0.45 + 0.3 * n.g);
		c = mix(c, c_core, (1.0 - smoothstep(0.0, 0.18, m)) * 0.6);
		return vec4(c * a, a * 0.65);
	} else if (typ < 7.5) {
		// v25 yaprak: sivri uçlu yumurtamsı yaprak (dip p.x=-1, uç +1), ince dişli kenar, altın orta damar + yan
		// damarlar, güneş alan yarı açık, uca doğru altına çalar; mürekkep kontur; yaşlanınca sararıp solar
		float xx = p.x;
		float w = 0.8 * pow(max(0.0, 1.0 - xx * xx), 0.75) * (1.0 - 0.3 * xx);
		w *= 1.0 - 0.07 * abs(sin(xx * 13.0));
		float m = w - abs(p.y);
		float aa = fwidth(m) * 1.2 + 0.02;
		float a = smoothstep(-aa, aa, m) * (1.0 - smoothstep(0.72, 1.0, age));
		vec3 c = p.y < 0.0 ? mix(c_body, c_rim, 0.35) : c_body * 0.72;
		c = mix(c, c_rim * 1.05, smoothstep(0.2, 1.0, xx) * 0.3);
		float sv = abs(fract(xx * 2.6 - abs(p.y) * 2.2) - 0.5);
		float vein = (1.0 - smoothstep(0.0, 0.07 + aa, sv)) * smoothstep(0.0, 0.25, m) * 0.35;
		c = mix(c, c_core, vein);
		c = mix(c, mix(c_rim, c_hot, 0.3), (1.0 - smoothstep(0.0, 0.05 + aa, abs(p.y))) * step(-0.9, xx) * 0.85);
		c = mix(c, vec3(0.34, 0.2, 0.04), smoothstep(0.45, 0.9, age) * 0.6);
		c = mix(c, c_ink, 1.0 - smoothstep(0.0, 0.1 + aa, m));
		return vec4(c * a, a);
	} else if (typ < 8.5) {
		// v25 kor / polen zerresi: hız yönünde uzamış kapsül (hareket bulanıklığı), sıcak çekirdek + toplamalı ışıma,
		// titreşerek söner
		float r = length(vec2(max(abs(p.x) - 0.55, 0.0) * 2.2, p.y));
		float core = 1.0 - smoothstep(0.22, 0.42, r);
		float glow = pow(1.0 - smoothstep(0.2, 1.0, r), 2.0);
		float fl = 0.72 + 0.28 * sin(mod(TIME, 600.0) * 41.0 + wpos.x * 1.7 + wpos.y);
		float k = (1.0 - age * age) * fl;
		vec3 c = mix(c_rim * 1.3, c_hot * hot_gain, core * (1.0 - age * 0.6));
		float a = clamp(core + glow * 0.55, 0.0, 1.0) * k;
		return vec4(c * a, core * 0.5 * k);
	} else if (typ < 9.5) {
		// v25 çiçek yaprağı: dipte ince, uçta yuvarlak ve hafif çentikli; krem-altın, dipte yeşil-altın, ince kontur
		float xx = p.x;
		float w = 0.62 * sqrt(max(0.0, 1.0 - xx * xx)) * (0.45 + 0.55 * (xx * 0.5 + 0.5));
		float m = w - abs(p.y) - 0.18 * (1.0 - smoothstep(0.0, 0.2, abs(p.y))) * smoothstep(0.75, 1.0, xx);
		float aa = fwidth(m) * 1.2 + 0.02;
		float a = smoothstep(-aa, aa, m) * (1.0 - smoothstep(0.7, 1.0, age));
		vec3 c = mix(c_rim, c_hot * 1.15, smoothstep(-0.8, 0.3, xx));
		c = mix(c, c_hot * 1.4, (1.0 - smoothstep(0.0, 0.3, abs(p.y + 0.15))) * 0.3);
		c = mix(c, c_core * 0.7, 1.0 - smoothstep(0.0, 0.08 + aa, m));
		return vec4(c * a, a);
	}
	// v25 kor yatağı (alev gölü tabanı): yassı elips, kara mürekkep kabuk, içinde nabız gibi atan kızgın çatlaklar
	float tt = mod(TIME, 600.0);
	float m = 1.0 - length(p);
	float nb = fbm(wpos * 0.22 + vec2(0.0, tt * 0.35));
	m += (nb - 0.5) * 0.5;
	float aa = fwidth(m) + 0.02;
	float a = smoothstep(-aa, aa * 3.0, m) * (1.0 - smoothstep(0.8, 1.0, age));
	float crack = 1.0 - smoothstep(0.0, 0.07 + aa, abs(fbm(wpos * 0.3 + vec2(5.0, 0.0)) - 0.5));
	float heat = clamp(0.35 + 0.5 * m + 0.25 * sin(tt * 5.0 + wpos.x * 0.4), 0.0, 1.0) * (1.0 - age * 0.7);
	vec3 c = mix(F_SMOKE * 1.5, F_DRED, smoothstep(0.1, 0.5, m));
	c = mix(c, fire_ramp(heat * 0.9, aa), crack);
	return vec4(c * a, a);
}

vec4 vine(float s, float v, float kind, float age) {
	// v25 Yer-Su filizi (tür 0) / kökü (tür 1): s dip 0 -> uç 1, v enine. Filiz: koyu yeşil gövde, bir yanda altın
	// ışık, mürekkep kontur; kök: kahverengi-yeşil kabuk, kalın mürekkep. Yaşlanınca uçtan dibe kuruyup kopar.
	float x = abs(v * 2.0 - 1.0);
	float wither = smoothstep(0.45, 1.0, age);
	float brk = vnoise(vec2(s * 7.0, wpos.x * 0.05 + kind * 3.7)) + 0.55 - wither * 1.25 - s * wither * 0.7;
	float m = min((1.0 - x) * 2.5, brk * 6.0);
	float aa = fwidth(m) + 0.02;
	float a = smoothstep(-aa, aa, m) * (1.0 - smoothstep(0.85, 1.0, age));
	vec3 c;
	if (kind < 0.5) {
		c = mix(c_body, mix(c_rim, c_hot, 0.25) * 1.1, smoothstep(0.55, 0.15, v) * 0.7);
		c = mix(c, c_ink, smoothstep(0.62, 0.86, x));
	} else {
		// kök: koyu kahve-is kabuk, ışık alan yanda altın-yeşil çizgi, boğumlu (s boyunca halkalar), kalın mürekkep
		c = mix(vec3(0.035, 0.02, 0.01), vec3(0.16, 0.1, 0.035), smoothstep(0.7, 0.2, v));
		c = mix(c, c_rim * 0.9, (1.0 - smoothstep(0.0, 0.1, abs(v - 0.28))) * 0.55);
		c = mix(c, c_ink * 0.4, (1.0 - smoothstep(0.0, 0.08, abs(fract(s * 6.0) - 0.5))) * 0.6);
		c = mix(c, c_ink * 0.4, smoothstep(0.55, 0.8, x));
	}
	c = mix(c, vec3(0.3, 0.19, 0.05), wither * 0.55);
	return vec4(c * a, a);
}

vec4 firca31(float u, float vi, float row) {
	// v31 hilal fırçası örneği: mip düzeyi yalnızca enine türevden (kıllar boyuna; hızlı süpürmede boyuna sıkışma dokuyu
	// enine bulanıklaştırmasın), satırlar arası taşma olmasın diye v kenardan uzak tutulur
	vec2 t = vec2(clamp(u, 0.002, 0.998), (row + clamp(vi, 0.03, 0.97)) / 8.0);
	return textureGrad(firca, t, dFdx(t) * vec2(0.1, 1.0), dFdy(t) * vec2(0.1, 1.0));
}

vec4 hilal31(float u, float vi, float row, float layer, float age) {
	// Dönen: önçarpılmış renk + alfa (alfa 0 kısım toplamalı ışıma)
	vec4 d = firca31(u, vi, row);
	float ea = clamp((age - er_delay) / (1.0 - er_delay), 0.0, 1.0);
	// tazelik kare cinsinden: hilal ~5 karede söner (yaş 0,2 ≈ 1 kare); en taze 2 kare ak-sıcak, 3-4. kare renkli
	float fresh = 1.0 - smoothstep(0.38, 0.8, age);
	float lead = 1.0 - smoothstep(0.24, 0.55, age);
	vec3 sumi = mix(vec3(0.004, 0.0035, 0.005), c_ink, 0.4);
	float grain = mix(1.0, 0.74 + 0.4 * d.a, 0.5);
	if (layer > 4.5) {
		// hız telleri: yalnız kıllar, bıçak renginde doğar, mürekkebe kurur
		float th = 0.5 + ea * (0.2 + 0.4 * d.b);
		float w = fwidth(d.r) * 0.8 + 0.01;
		float a = smoothstep(th - w, th + w, d.r) * (1.0 - smoothstep(0.7, 1.0, age)) * 0.85;
		vec3 c = mix(mix(c_rim, c_hot, 0.4) * (1.0 + 0.8 * lead), mix(c_core, sumi, 0.5), smoothstep(0.15, 0.7, age));
		return vec4(c * a, a);
	}
	if (layer > 0.5 && layer < 1.5) {
		if (row > 5.5) {
			// arka sulu yıkama (duman): yumuşak eşik, yansız gri-siyah su mürekkebi, kenarında kuruma halkası
			float th = 0.5 + age * (0.12 + 0.35 * d.b);
			float a = smoothstep(th - 0.22, th + 0.08, d.r) * (wash_a + 0.16 * d.a) * (1.0 - smoothstep(0.55, 1.0, age));
			vec3 c = mix(c_ink * 1.5 + c_core * 0.3, c_body * 0.6, 0.12 + 0.12 * fresh);
			c = mix(c, sumi, d.g * 0.6);
			return vec4(c * a, a);
		}
		// ağır: arkada koyu kuru sürüntü (kalın kuru fırça)
		float th = 0.53 + ea * (0.2 + 0.45 * d.b);
		float w = fwidth(d.r) * 0.8 + 0.01;
		float a = smoothstep(th - w, th + w, d.r) * grain * 0.9 * (1.0 - smoothstep(0.8, 1.0, age));
		vec3 c = mix(mix(c_core, sumi, 0.55), sumi, d.g);
		return vec4(c * a, a);
	}
	// ---- ana hilal (katman 0) ve yankı (2)
	float echo = step(1.5, layer);
	// eşik: taze kıllar dolu (ıslak uç bir tık kalın), yaşla kıl kimliği sırasıyla kopar (kuyruk ve iç kenar önce)
	float th = 0.5 - 0.05 * lead + ea * (0.12 + 0.55 * d.b) + echo * 0.06;
	float w = fwidth(d.r) * 0.75 + 0.008;
	float a = smoothstep(th - w, th + w, d.r);
	a *= grain * (1.0 - smoothstep(0.82, 1.0, age));
	// renk: güçlü değer geçişi — iç kenarda koyu çekirdek tonu, bıçağa doğru paletin gövdesi (kıl damarlı); iç
	// yarıda sumi kıl çizgileri ve iç kenarda koyu mürekkep birikimi
	vec3 col = mix(c_core * 0.85, c_body, smoothstep(0.12, 0.72, vi));
	col = mix(col, c_core, clamp(d.g * 0.5 + (1.0 - d.r) * 0.3, 0.0, 0.6));
	col = mix(col, c_body * 1.18, smoothstep(0.62, 0.9, d.r) * smoothstep(0.4, 0.8, vi) * 0.3);
	float ink_side = 1.0 - smoothstep(0.3, 0.58, vi);
	col = mix(col, sumi, clamp(d.g * 1.9 * ink_side + (1.0 - smoothstep(0.0, 0.16, vi)) * 0.7, 0.0, 0.94));
	// parlak çekirdek bandı (bıçak ağzının hemen içi), en taze kısımda geniş; ön uçta ak-sıcak
	float near = 1.0 - smoothstep(0.0, 0.45, u);
	// cel basamakları (yumuşak hava fırçası değil): gövde -> kenar tonu (turuncu) -> ak-sıcak çekirdek; basamak
	// sınırları kıl kimliğiyle pürüzlü (fırça kılı gibi), kenar yumuşatma piksel genişliğinden
	float fv = fwidth(vi) * 0.8 + 0.004;
	float jag = (d.b - 0.5) * 0.16 + (d.a - 0.5) * 0.06;
	float wide = 0.1 * lead + 0.05 * near;
	float st1 = smoothstep(-fv, fv, vi - (band_in - wide) + jag) * fresh;
	float st2 = smoothstep(-fv, fv, vi - (core_in - wide * 0.7) + jag) * max(lead, fresh * 0.35) * (0.35 + 0.65 * near);
	float cg = core_gain * (1.0 - echo);
	col = mix(col, c_rim * (1.0 + 0.25 * lead), clamp(st1 * cg * 0.85, 0.0, 1.0));
	col = mix(col, mix(c_rim, c_hot, 0.55 + 0.4 * lead) * (1.0 + 1.0 * lead), clamp(st2 * cg, 0.0, 1.0));
	// bıçak ağzı hattı: ince ak-sıcak çizgi (HDR), kuyruğa ve yaşla söner
	float edge = smoothstep(0.93 - fv, 0.93 + fv, vi) * (1.0 - smoothstep(0.985, 1.0, vi)) * max(lead, fresh * 0.5) * (1.0 - 0.7 * u) * edge_gain * (1.0 - echo);
	col = mix(col, c_hot * hot_gain, clamp(edge, 0.0, 1.0));
	// kuruma: yaşlanan mürekkep paletin renginden koyu mürekkebe çekilir (kurumuş sumi kıl telleri kalır)
	col = mix(col, mix(c_core, sumi, 0.55), smoothstep(0.25, 0.85, age) * 0.75);
	if (echo > 0.5) {
		col = mix(col, c_rim, 0.25);
		a *= 0.42 * (1.0 - age * 0.5);
	}
	// dış ışıma: bıçak ağzının ötesinde ince, toplamalı, yalnız taze
	float halo = smoothstep(0.97, 1.01, vi) * (1.0 - smoothstep(1.01, 1.12, vi));
	vec3 add = mix(c_rim, c_hot, 0.4) * glow_gain * 0.45 * halo * lead * (1.0 - echo) * (0.4 + 0.6 * near);
	return vec4(col * a + add * (1.0 - a), a);
}

void fragment() {
	float layer = floor(UV.y * 0.5);
	float v = UV.y - layer * 2.0;
	float age = clamp(COLOR.a, 0.0, 1.0);
	if (v31 == 1 && layer > 4.5) {
		float row5 = floor(UV.x * 0.5);
		COLOR = hilal31(UV.x - row5 * 2.0, v / ink_w, row5, layer, age);
	} else if (v31 == 1 && layer < 2.5 && unsur_id != 1) {
		float row = floor(UV.x * 0.5);
		float u = UV.x - row * 2.0;
		vec4 h = hilal31(u, v / ink_w, row, layer, age);
		if (unsur_id == 2 && layer < 0.5) {
			// v25 Yer-Su yaprak damarları v31 hilalinde de: altın orta damar + eğik yan damarlar (u boyunca)
			float vi2 = v / ink_w;
			float mid = 1.0 - smoothstep(0.0, 0.045 + fwidth(vi2) * 1.5, abs(vi2 - 0.6));
			float sv = abs(fract(u * 9.0 + vi2 * 0.9) - 0.5);
			float side = (1.0 - smoothstep(0.0, 0.05 + fwidth(u * 9.0 + vi2 * 0.9) * 1.5, sv)) * smoothstep(0.2, 0.55, vi2) * (1.0 - smoothstep(0.8, 0.95, vi2));
			vec3 vc = mix(c_rim, c_hot, 0.35) * 1.15 * h.a;
			h.rgb = mix(h.rgb, vc, clamp(mid * 0.8 + side * 0.4, 0.0, 1.0) * (1.0 - age));
		}
		COLOR = h;
	} else if (layer > 3.5) {
		float kind = floor(UV.x * 0.5);
		COLOR = vine(UV.x - kind * 2.0, v, kind, age);
	} else if (layer > 2.5) {
		float typ = floor(UV.x * 0.5);
		float a;
		if (typ > 2.5) {
			COLOR = elem(UV.x - typ * 2.0, v, typ, age, UV);
		} else {
			vec3 c = fleck(UV.x - typ * 2.0, v, typ, age, a);
			COLOR = vec4(c * a, typ > 1.5 ? a * 0.4 : a);
		}
	} else {
		float vi = v / ink_w;                         // 0 iç kenar, 1 mürekkep dış kenarı (bıçak ucu), >1 ışıma
		// kıllar boyuna uzandığından mip düzeyi yalnızca enine türevden: hızlı süpürmede boyuna sıkışma
		// (u türevi büyük) dokuyu enine de bulanıklaştırıp bloklu kesikler üretmesin
		vec2 buv = vec2(UV.x * u_scale, clamp(vi, 0.004, 0.996));
		vec2 gx = dFdx(buv) * vec2(0.12, 1.0);
		vec2 gy = dFdy(buv) * vec2(0.12, 1.0);
		vec4 b = textureGrad(bristle, buv, gx, gy);
		float back = step(0.5, layer) * step(layer, 1.5);
		float ghost = step(1.5, layer);
		float rg = rough * (1.0 + back * 0.6 + ghost * 0.4);
		// kenarlar: iç kenar kıl uçlarıyla pürüzlü ve kuru, dış kenar (bıçak ağzı) daha keskin
		float e_in = vi;
		float e_out = 1.0 - vi;
		float ea = clamp((age - er_delay) / (1.0 - er_delay), 0.0, 1.0);   // erime yaşı (v23)
		float er = ea * ea;
		float rag_in = ((b.a - 0.5) * 0.45 + (b.r - 0.5) * 0.7) * rg;
		float rag_out = ((b.a - 0.5) * 0.22 + (b.b - 0.5) * 0.12) * rg * (0.6 + ea * 1.6);
		float shape = min(e_in * 3.2 + rag_in - er * 1.6, e_out * 7.0 + rag_out - er * 2.2);
		// kuru fırça: kıl yükü (R) kuruluk eşiğinin altında kalan yerler boş; içe ve yaşa doğru kurur
		float dry = 0.05 + dry_in * rg * (1.0 - smoothstep(0.0, 0.62, e_in)) + ea * (0.75 + 0.2 * rg) + ghost * 0.25;
		float strand = (b.r - dry) * 5.0;
		// erime: yaşlandıkça yalnızca kimliği yüksek kıllar kalır -> kıl telleri
		float survive = (b.b * 0.7 + b.a * 0.3 + 0.3 - ea * 1.25) * 5.0;
		float m = min(shape, min(strand, survive));
		float aa = fwidth(m) * 0.75 + 0.015;
		float alpha = smoothstep(-aa, aa, m);
		// ---- renk
		float load = smoothstep(0.35, 0.95, b.r);
		vec3 col = mix(c_rim, c_body, smoothstep(0.0, 0.16, e_in + (b.a - 0.5) * 0.12));
		// koyu kızıl çekirdek bandı (iç-orta) + kıl yüküyle koyulaşma; dış kenara doğru turuncuya açılır
		float band = smoothstep(0.18, 0.45, vi) * (1.0 - smoothstep(0.5, 0.78, vi));
		col = mix(col, c_core, clamp(band * (0.12 + 0.4 * load) + load * 0.12 * smoothstep(0.15, 0.55, e_in), 0.0, 0.7));
		col = mix(col, c_rim, smoothstep(0.8, 0.97, vi) * 0.3);
		float stk = b.g * streaks * smoothstep(0.08, 0.4, e_in) * (1.0 - smoothstep(0.82, 0.97, vi));
		col = mix(col, c_ink, clamp(stk * 1.15, 0.0, 1.0));
		// arka katman: koyu kızıl / mürekkep, kuru
		col = mix(col, mix(c_core, c_ink, 0.45 + 0.4 * b.g), back * 0.85);
		// v23: iç kenarda ince mürekkep konturu (hilalin iç eğrisi okunsun)
		col = mix(col, c_ink * 0.6, (1.0 - smoothstep(0.0, 0.08, e_in)) * 0.5 * (1.0 - back));
		// sıcak ön kenar: bıçak ucunun hemen içinde, taze kısımda; yaşla turuncuya söner
		// (v23: iz 2-4 karede söndüğünden eşikler yaşa göre geniş: tazelik bir kareden uzun sürsün)
		float fresh = 1.0 - smoothstep(0.0, 0.5, age);
		float lead = 1.0 - smoothstep(0.0, 0.3, age);     // en taze kısım: bıçağın hemen arkası
		// v23 parlak iç çekirdek: hilalin dolgun ön kısmında mürekkebin ortasından dış kenara doğru açık-sıcak bant
		float core = smoothstep(0.34, 0.6, vi) * (1.0 - smoothstep(0.82, 0.96, vi)) * lead * core_gain * (1.0 - back) * (1.0 - ghost);
		col = mix(col, mix(c_rim, c_hot, 0.55) * 1.6, clamp(core * (0.55 + 0.35 * load), 0.0, 0.85));
		float hot = smoothstep(0.62, 0.95, vi) * lead * lead * (1.0 - back) * (1.0 - ghost);
		col = mix(col, c_hot * hot_gain, hot);
		col = mix(col, c_rim * 1.3, smoothstep(0.7, 0.95, vi) * (1.0 - fresh) * 0.35 * (1.0 - back));
		col *= 1.0 + fresh * 0.3 * (1.0 - back);
		alpha *= 1.0 - ghost * (0.45 + 0.4 * age);
		// dış ışıma: mürekkep dış kenarının ötesinde, toplamalı, kısa ömürlü
		float halo = (1.0 - smoothstep(0.96, 1.2, vi)) * smoothstep(0.55, 0.98, vi);
		vec3 add = mix(c_rim, c_hot, 0.35) * glow_gain * halo * fresh * fresh * (1.0 - back) * (1.0 - ghost);
		if (unsur_id == 1) {
			// v25 od hilali: alev gövdesi. Şekil aynı fırça hilali ama kuru kıl telleri yerine yukarı akan alev
			// türbülansıyla yenir (iç kenar alev dilleri gibi yırtılır), bıçak ağzının ötesindeki saçakta alev dilleri
			// yalar. Renk sıcaklıktan: bıçak ağzının hemen içi ve taze kısım ak-sarı, içe doğru turuncu → koyu kızıl,
			// kenarlarda ince is konturu (mürekkep); kıl izleri soğuk bölgede is çizgisi olarak kalır.
			float tt = mod(TIME, 600.0);
			float n = fire_n(wpos, tt);
			float n2 = vnoise(wpos * vec2(0.4, 0.22) + vec2(0.0, tt * 6.0));
			float sh = min(e_in * 2.4 + (n - 0.5) * 2.0 + rag_in * 0.4 - er * 1.7, e_out * 6.0 + (n2 - 0.5) * 0.7 + rag_out - er * 2.0);
			float surv = (n * 1.4 + b.b * 0.2 + 0.25 - ea * 1.4) * 4.0;
			float mf = min(sh, surv);
			// en taze baş: bıçak savruluşuna dik kesik kapak düz çizgi gibi durmasın, türbülansla alev diline yırtılır
			mf -= (1.0 - smoothstep(0.0, 0.14, age)) * max(0.62 - n, 0.0) * 2.4 * (1.0 - back);
			// saçak: mürekkep dış kenarının ötesinde (vi > 1) gürültüden çıkan, dışa doğru incelen alev dilleri
			float fr = (n * 1.3 + n2 * 0.3 - 0.62) - (vi - 1.0) * 2.6 - ea * 1.0;
			fr = mix(-1.0, fr, step(1.0, vi) * (1.0 - back) * (1.0 - ghost));
			mf = max(mf, fr * 4.0);
			float aaf = fwidth(mf) * 0.75 + 0.015;
			float af = smoothstep(-aaf, aaf, mf);
			af *= (1.0 - ghost * (0.45 + 0.4 * age)) * (1.0 - back * 0.65);   // ağırın arka katmanı: soluk is (blok gibi durmasın)
			float T = smoothstep(0.0, 0.9, vi) * 0.6 + 0.2 + (n - 0.5) * 0.9 + lead * 0.3 * (1.0 - back) - ea * 0.5 - back * 0.35;
			T -= max(vi - 1.0, 0.0) * 0.9;
			T += core * 0.15;
			vec3 cf = fire_ramp(clamp(T, 0.0, 1.0), aaf * 0.3);
			cf = mix(cf, F_SMOKE, (1.0 - smoothstep(0.0, 0.2, mf)) * 0.85);
			cf = mix(cf, F_SMOKE, clamp(b.g * streaks * 0.6 * (1.0 - smoothstep(0.25, 0.55, T)), 0.0, 0.8));
			vec3 addf = F_ORANGE * glow_gain * 0.6 * halo * fresh * (1.0 - back) * (1.0 - ghost);
			COLOR = vec4(cf * af + addf * (1.0 - af), af);
		} else {
			if (unsur_id == 2) {
				// v25 Yer-Su: yaprak hilali — mürekkebin ortasında altın orta damar, ondan uca doğru eğik yan damarlar
				float mid = 1.0 - smoothstep(0.0, 0.045 + fwidth(vi) * 1.5, abs(vi - 0.6));
				float sv = abs(fract(UV.x * 3.0 + vi * 0.9) - 0.5);
				float side = (1.0 - smoothstep(0.0, 0.05 + fwidth(UV.x * 3.0 + vi * 0.9) * 1.5, sv)) * smoothstep(0.2, 0.55, vi) * (1.0 - smoothstep(0.8, 0.95, vi));
				// gövde koyu zümrüte çekilir (açık orman zemininde okunsun), ışıma yarıya iner
				col = mix(col, c_core * 1.2, 0.28 * smoothstep(0.1, 0.5, vi) * (1.0 - smoothstep(0.75, 0.95, vi)) * (1.0 - back));
				col = mix(col, mix(c_rim, c_hot, 0.35) * 1.15, clamp(mid * 0.85 + side * 0.45, 0.0, 1.0) * (1.0 - ea * 0.8) * (1.0 - back));
				add *= 0.5;
			}
			COLOR = vec4(col * alpha + add * (1.0 - alpha), alpha);
		}
	}
}
