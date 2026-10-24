// Bengü'nün uzun saçı (scripts/core/BenguSac.gd): çalışma zamanında çizilen fırça tutamları, stil v2 mürekkep-cel görünümü.
// bengu_sac.gdshader (oyun) ve bengu_sac_hayalet.gdshader (HAYALET: toplamalı, ışıksız solan kopya) bunu içerir.
// Şerit köşe verisi (canvas_item_add_triangle_array):
//   UV.x  = şeridin enine konumu (0 sol kenar .. 1 sağ kenar)
//   UV.y  = kökten uzunluk / 64 (+ tutam tohumu: her tutamın tel / parlama deseni kayar)
//   COLOR.r = sol kenar normalinin ışıkla nokta çarpımı (-1..1 -> 0..1): cel gölgesi şeridin hangi yanına düşer
//   COLOR.g = yarı genişlik / 4 (dünya birimi): kontur / tel kalınlığı genişlikten bağımsız
//   COLOR.b = kip: 0..0.14 saç tutamı (ton = b / 0.14: 0 koyu arka kütle .. 1 açık ön tutam), 0.2 uçuşan tel, 0.5 örgü,
//             0.68 altın halka, 1 boncuk (UV kare)
//   COLOR.a = omurga oranı (0 kök .. 1 uç): kök başlığın gölgesinde, parlama halkası omurgada aynı yerde
// Kenar yumuşatma ekran türevleriyle (fwidth): her yakınlıkta (1080p / 1440p / 2K-4K doku) aynı keskin kontur.
// Işık, vuruş parlaması, ton ve ay gölgesi ink_char.gdshader ile aynı adlarla çalışır (gövdeden kopyalanır).

// renk: mavi-mor parıltılı neredeyse siyah saç (ak kurt postunun üstünde ve koyu ormanda iyi okunur)
uniform vec4 deep_col : source_color = vec4(0.078, 0.071, 0.118, 1.0);   // kütle / arka tutam
uniform vec4 base_col : source_color = vec4(0.165, 0.157, 0.243, 1.0);   // ön tutam orta tonu
uniform vec4 shade_col : source_color = vec4(0.043, 0.039, 0.071, 1.0);  // gölge
uniform vec4 hi_col : source_color = vec4(0.60, 0.67, 0.89, 1.0);        // parlama halkası (mavi-mor)
uniform vec4 rim_col : source_color = vec4(0.36, 0.41, 0.63, 1.0);       // ışık yanı kenar parıltısı
uniform vec4 ink_col : source_color = vec4(0.035, 0.031, 0.055, 1.0);
uniform vec4 band_col : source_color = vec4(0.918, 0.714, 0.306, 1.0);    // altın saç bağı / örgü halkası
uniform vec4 bead_col : source_color = vec4(0.153, 0.761, 0.69, 1.0);     // turkuaz boncuk
uniform float outline = 0.3;          // kontur (dünya birimi; gölge yanında kalın, ışık yanında ve uçta ince)
uniform float flash : hint_range(0.0, 1.0) = 0.0;
uniform vec4 flash_color : source_color = vec4(1.0, 0.97, 0.9, 1.0);
uniform vec4 tint : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform float moon_shade : hint_range(0.0, 1.0) = 0.0;
uniform float light_k : hint_range(0.0, 2.0) = 0.85;
uniform float point_k : hint_range(0.0, 2.0) = 0.9;
#ifdef HAYALET
uniform vec4 hayalet_col : source_color = vec4(1.0, 1.0, 1.0, 0.5);
#endif
// HDR 2D görüntü alanında Godot köşe renklerini sRGB -> doğrusal çevirir; köşe rengi burada veri taşıdığı için geri çevrilir
// (BenguSac görüntü alanının use_hdr_2d değerini yazar)
uniform bool vcol_linear = false;
varying vec4 vdat;

vec3 to_srgb(vec3 c) {
	return mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(1.0 / 2.4)) - 0.055, step(vec3(0.0031308), c));
}

void vertex() {
	vdat = COLOR;
	if (vcol_linear) {
		vdat.rgb = to_srgb(COLOR.rgb);
	}
}

float hash1(float x) {
	return fract(sin(x * 127.1 + 11.7) * 43758.5453);
}

// saç tutamı: yumuşak iki tonlu cel, omurgayı izleyen kırık parlama halkası, ışık yanında kenar parıltısı, gölgede piksel
// inceliğinde kesik tel çizgileri. a = -1..1 enine (sol kenar +1), ndl silindir normaliyle ışık
vec3 sac_rengi(float a, float hw, float v, float nl, float s, float ton, float ol_w) {
	float ndl = -a * nl + sqrt(max(0.0, 1.0 - a * a)) * 0.45;
	vec3 mid = mix(deep_col.rgb, base_col.rgb, ton);
	vec3 sh = mix(shade_col.rgb, deep_col.rgb, ton * 0.6);
	vec3 c = mix(sh, mid, smoothstep(-0.04, 0.2, ndl));
	float lit = smoothstep(0.02, 0.4, ndl);
	// tel şeritleri: enine ~0,5 birim, boyuna hafif dalgalı
	float xw = a * hw;
	float u = xw / 0.5 + 0.3 * sin(v * 0.17 + ton * 5.0);
	float lane = floor(u);
	float f = fract(u);
	// parlama halkası (anime "melek halkası"): omurgada ~%24'te, tel tel kırık uçlu; ön tutamlarda daha parlak
	float bc = 0.25 + 0.05 * sin(lane * 1.7 + ton * 3.0) + 0.025 * (hash1(lane + floor(ton * 7.0)) - 0.5);
	float bw = 0.055 + 0.035 * hash1(lane + 3.0);
	float band = 1.0 - smoothstep(bw * 0.55, bw, abs(s - bc));
	float hl = band * lit * (0.35 + 0.65 * ton);
	// halkanın dışında: ışık yanında uzun kesik tel parlamaları
	float streak = smoothstep(0.5, 0.75, ndl) * step(0.6, fract(v * 0.04 + hash1(lane))) * smoothstep(0.15, 0.4, f) * smoothstep(0.15, 0.4, 1.0 - f);
	c = mix(c, hi_col.rgb, max(hl, streak * 0.45 * ton));
	// ince tel çizgileri: ekran pikseli inceliğinde, gölge ve orta tonda, kesik
	float px = min(f, 1.0 - f) * 0.5 / max(fwidth(xw), 1e-4);
	float line = (1.0 - smoothstep(0.3, 1.1, px)) * smoothstep(2.5, 5.0, 0.5 / max(fwidth(xw), 1e-4));  // uzakta sönümlenir
	float dash = step(0.35, fract(v * 0.05 + hash1(lane + 7.0)));
	c = mix(c, ink_col.rgb, line * dash * (1.0 - lit) * 0.6);
	// kenar parıltısı: ışık yanı kenarda, konturun hemen içinde ince soğuk çizgi
	float rimside = smoothstep(0.15, 0.6, -sign(a) * nl);
	float ed = (1.0 - abs(a)) * hw;
	float rim = rimside * (1.0 - smoothstep(ol_w + 0.05, ol_w + 0.32, ed)) * smoothstep(0.06, 0.2, s);
	c = mix(c, rim_col.rgb, rim * (0.3 + 0.35 * ton));
	// kök: başlığın altında gölgede
	c = mix(c, shade_col.rgb * 0.8, (1.0 - smoothstep(0.0, 0.1, s)) * 0.75);
	return c;
}

vec3 orgu_rengi(float a, float hw, float v, float nl, float s) {
	// örgü: V biçimli loblar (her lob ortası açık, aralar mürekkep), lob gölgesi ışık yönüyle
	float ndl = -a * nl + sqrt(max(0.0, 1.0 - a * a)) * 0.45;
	float lob = fract(v / (0.5 + hw * 0.6) + abs(a) * 0.5);   // v43: lob boyu örgü enine göre (kalın tek örgü)
	float lobl = sin(lob * 3.14159);
	float sh = ndl * 0.7 + (lobl - 0.5) * 0.6;
	vec3 c = sh < 0.0 ? shade_col.rgb : mix(deep_col.rgb, base_col.rgb, 0.8);
	c = mix(c, hi_col.rgb, smoothstep(0.5, 0.7, sh) * 0.22);   // v43: 0,6 -> 0,22 (örgü ip gibi açık okunmasın)
	float sep = 1.0 - smoothstep(0.08, 0.22, min(lob, 1.0 - lob));
	c = mix(c, ink_col.rgb, sep * 0.9);
	c = mix(c, shade_col.rgb * 0.8, (1.0 - smoothstep(0.0, 0.12, s)) * 0.7);
	return c;
}

void fragment() {
	float a = UV.x * 2.0 - 1.0;
	float hw = max(0.01, vdat.g * 4.0);
	float nl = vdat.r * 2.0 - 1.0;
	float mode = vdat.b;
	float s = vdat.a;
	float v = UV.y * 64.0;     // BenguSac.V_OLCEK
	vec3 c;
	vec3 inkc = ink_col.rgb;     // kontur rengi (iç tutam konturları daha yumuşak)
	float edge = 1.0 - abs(a);   // kenara uzaklık (0 kenar .. 1 merkez), kontur ve yumuşatma bununla
	float olw;
	if (mode > 0.75) {
		// boncuk: kare UV içinde daire; turkuaz cam, gölge hilali, beyaz parlama noktası
		vec2 q = UV * 2.0 - 1.0;
		float r = length(q);
		edge = 1.0 - r;
		olw = 0.32;
		vec2 L = normalize(vec2(-0.74, -0.67));
		float ndl = dot(q, L) * 0.8 + sqrt(max(0.0, 1.0 - r * r)) * 0.4;
		c = ndl < 0.08 ? bead_col.rgb * 0.5 : bead_col.rgb;
		c = mix(c, vec3(1.0), smoothstep(0.08, 0.0, length(q - L * 0.45)));
	} else if (mode > 0.6) {
		// altın saç bağı / örgü halkası: sargı kirişli, metal parlaması ışık yanında
		olw = clamp(outline / hw, 0.0, 0.6);
		float ndl = -a * nl + sqrt(max(0.0, 1.0 - a * a)) * 0.45;
		c = ndl < 0.1 ? band_col.rgb * vec3(0.62, 0.5, 0.4) : band_col.rgb;
		c = mix(c, vec3(1.0, 0.97, 0.85), smoothstep(0.62, 0.72, ndl));
		float rib = abs(fract(v / 0.45) - 0.5);
		c = mix(c, ink_col.rgb, (1.0 - smoothstep(0.03, 0.09, rib)) * 0.8);
	} else if (mode > 0.4) {
		olw = clamp(outline / hw, 0.0, 0.6);
		c = orgu_rengi(a, hw, v, nl, s);
	} else if (mode > 0.17) {
		// uçuşan tel: konturuz ince saç teli, ışık yanında parlar
		olw = 0.0;
		float ndl = -a * nl * 0.5 + 0.5;
		c = mix(mix(deep_col.rgb, base_col.rgb, 0.7), hi_col.rgb, smoothstep(0.55, 0.85, ndl) * 0.35);
	} else {
		float ton = clamp(mode / 0.14, 0.0, 1.0);
		// kontur: gölge yanında kalın, ışık yanında ince; ince uçlarda incelir (fırça ucu kalkıyor gibi)
		float lit_e = -sign(a) * nl;
		float ol_w = outline * mix(1.6, 0.55, smoothstep(-0.4, 0.5, lit_e)) * clamp(hw / 0.9, 0.3, 1.0);
		// kütle (ton 0) silüetin dış konturu: kalın, tam mürekkep; üstteki tutamların konturu ayrımı yumuşakça verir
		ol_w *= ton < 0.05 ? 1.35 : 0.85;
		olw = clamp(ol_w / hw, 0.0, 0.62);
		c = sac_rengi(a, hw, v, nl, s, ton, ol_w);
		inkc = mix(ink_col.rgb, shade_col.rgb, step(0.05, ton) * 0.5);
	}
	// mürekkep konturu + ekran uzayında kenar yumuşatma
	float fw = max(fwidth(edge), 1e-4);
	float ink = 1.0 - smoothstep(olw - fw * 0.75, olw + fw * 0.75, edge);
	c = mix(c, inkc, ink);
	float al = smoothstep(0.0, fw * 1.25, edge);
#ifdef HAYALET
	// hayalet izi: gövde hayaleti gibi toplamalı; koyu saç biraz aydınlatılır ki silüeti okunsun
	c = max(c, vec3(0.22, 0.24, 0.3)) + c * 0.6;
	COLOR = vec4(c * hayalet_col.rgb, al * hayalet_col.a);
#else
	vec4 o = vec4(c, al) * tint;
	o.rgb = mix(o.rgb, flash_color.rgb, flash);
	COLOR = o;
#endif
}

#ifndef HAYALET
void light() {
	vec3 lit = COLOR.rgb * LIGHT_COLOR.rgb * LIGHT_ENERGY;
	if (LIGHT_IS_DIRECTIONAL) {
		lit *= light_k * (1.0 - moon_shade);
	} else {
		lit *= point_k;
	}
	LIGHT = vec4(lit, LIGHT_COLOR.a);
}
#endif
