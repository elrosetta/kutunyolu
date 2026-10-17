// Bengü'nün uzun saçı (scripts/core/BenguSac.gd): çalışma zamanında çizilen fırça şeritleri, stil v2 mürekkep-cel görünümü.
// Şerit köşe verisi (canvas_item_add_triangle_array):
//   UV.x  = şeridin enine konumu (0 sol kenar .. 1 sağ kenar), UV.y = kökten uzunluk (dünya birimi; tel/örgü deseni sabit kalır)
//   COLOR.r = sol kenar normalinin ışıkla nokta çarpımı (-1..1 -> 0..1): cel gölgesi şeridin hangi yanına düşer
//   COLOR.g = yarı genişlik / 4 (dünya birimi): kontur kalınlığı genişlikten bağımsız sabit kalır
//   COLOR.b = kip: 0 saç tutamı, 0.5 örgü, 1 boncuk (UV kare), 0.25 kurt postu (kıl tutamları)
//   COLOR.a = kökten oran (0..1): kök başlığın gölgesinde koyulaşır
// Kenar yumuşatma ekran türevleriyle (fwidth): her yakınlıkta (1080p / 1440p / 2K-4K doku) aynı keskin kontur.
// Işık, vuruş parlaması, ton ve ay gölgesi ink_char.gdshader ile aynı adlarla çalışır (gövdeden kopyalanır).
shader_type canvas_item;

uniform vec4 base_col : source_color = vec4(0.18, 0.145, 0.175, 1.0);
uniform vec4 shade_col : source_color = vec4(0.095, 0.078, 0.1, 1.0);
uniform vec4 hi_col : source_color = vec4(0.44, 0.49, 0.62, 1.0);
uniform vec4 ink_col : source_color = vec4(0.082, 0.086, 0.114, 1.0);
uniform vec4 band_col : source_color = vec4(0.918, 0.714, 0.306, 1.0);    // altın örgü halkası
uniform vec4 band2_col : source_color = vec4(0.824, 0.192, 0.22, 1.0);    // kırmızı ip sargısı
uniform vec4 bead_col : source_color = vec4(0.153, 0.761, 0.69, 1.0);     // turkuaz boncuk
uniform vec4 fur_col : source_color = vec4(0.725, 0.753, 0.824, 1.0);     // kurt postu
uniform vec4 fur_shade : source_color = vec4(0.42, 0.45, 0.58, 1.0);
uniform vec4 fur_hi : source_color = vec4(0.914, 0.929, 0.961, 1.0);
uniform float outline = 0.3;          // kontur (dünya birimi)
uniform float flash : hint_range(0.0, 1.0) = 0.0;
uniform vec4 flash_color : source_color = vec4(1.0, 0.97, 0.9, 1.0);
uniform vec4 tint : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform float moon_shade : hint_range(0.0, 1.0) = 0.0;
uniform float light_k : hint_range(0.0, 2.0) = 0.85;
uniform float point_k : hint_range(0.0, 2.0) = 0.9;
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

vec4 strand(float a, float hw, float v, float nl, float s, float braid) {
	// silindir benzeri enine normal: a = -1..1 (sol kenar +1); ışık sol üstten, biraz da ekrandan
	float ndl = -a * nl + sqrt(max(0.0, 1.0 - a * a)) * 0.45;
	float xw = a * hw;                         // enine dünya konumu (tel çizgileri genişlikten bağımsız)
	vec3 c = base_col.rgb;
	if (braid > 0.5) {
		// örgü: V biçimli loblar (her lob ortası açık, aralar mürekkep), lob gölgesi ışık yönüyle
		// lob: örgünün her düğümü; iki yandan ortaya doğru eğik (V), düğüm ortası ışıkta parlar, aralar mürekkep
		float lob = fract(v / 1.1 + abs(a) * 0.5);
		float lobl = sin(lob * 3.14159);
		float sh = ndl * 0.7 + (lobl - 0.5) * 0.6;
		c = sh < 0.0 ? shade_col.rgb : base_col.rgb;
		c = mix(c, hi_col.rgb, smoothstep(0.5, 0.62, sh) * 0.55);
		float sep = 1.0 - smoothstep(0.08, 0.2, min(lob, 1.0 - lob));
		c = mix(c, ink_col.rgb, sep * 0.95);
	} else {
		// iki tonlu cel: taban / gölge, ışık yanında kırık tel parlaması (anime saç parlaması gibi kesik şeritler)
		c = ndl < 0.12 ? shade_col.rgb : base_col.rgb;
		// tel şeritleri: enine ~0,75 birim, boyuna hafif dalgalı (şerit sınırında kesinti yok)
		float u = xw / 0.75 + 0.3 * sin(v * 0.22);
		float lane = floor(u);
		float f = fract(u);
		float brk = 0.55 + 0.45 * step(0.28, fract(v * 0.05 + hash1(lane)));
		float hl = smoothstep(0.6, 0.74, ndl) * smoothstep(0.15, 0.4, f) * smoothstep(0.15, 0.4, 1.0 - f) * brk * 0.75;
		c = mix(c, hi_col.rgb, hl);
		// ince mürekkep tel çizgileri: yalnızca gölge/orta tonda, uzunlamasına kesik
		float dist = min(f, 1.0 - f) * 0.75;
		float line = 1.0 - smoothstep(0.025, 0.08, dist);
		float dash2 = step(0.5, fract(v * 0.06 + hash1(lane + 7.0)));
		c = mix(c, ink_col.rgb, line * dash2 * (1.0 - smoothstep(0.0, 0.45, ndl)) * 0.6);
	}
	// kök: başlığın altında gölgede
	c = mix(c, shade_col.rgb * 0.8, (1.0 - smoothstep(0.0, 0.12, s)) * 0.7);
	return vec4(c, 1.0);
}

void fragment() {
	float a = UV.x * 2.0 - 1.0;
	float hw = max(0.01, vdat.g * 4.0);
	float nl = vdat.r * 2.0 - 1.0;
	float mode = vdat.b;
	float s = vdat.a;
	float v = UV.y * 64.0;     // BenguSac.V_OLCEK
	vec4 c;
	float edge;          // kenara uzaklık (0 kenar .. 1 merkez), kontur ve yumuşatma bununla
	float olw;
	if (mode > 0.75) {
		// boncuk: kare UV içinde daire; turkuaz cam, gölge hilali, beyaz parlama noktası
		vec2 q = UV * 2.0 - 1.0;
		float r = length(q);
		edge = 1.0 - r;
		olw = 0.32;
		vec2 L = normalize(vec2(-0.74, -0.67));
		float ndl = dot(q, L) * 0.8 + sqrt(max(0.0, 1.0 - r * r)) * 0.4;
		vec3 bc = ndl < 0.08 ? bead_col.rgb * 0.5 : bead_col.rgb;
		bc = mix(bc, vec3(1.0), smoothstep(0.08, 0.0, length(q - L * 0.45)) );
		c = vec4(bc, 1.0);
	} else if (mode > 0.6) {
		// örgü sonu halkası: altın (kirişli), metal parlaması ışık yanında
		edge = 1.0 - abs(a);
		olw = clamp(outline / hw, 0.0, 0.6);
		float ndl = -a * nl + sqrt(max(0.0, 1.0 - a * a)) * 0.45;
		vec3 g = ndl < 0.1 ? band_col.rgb * vec3(0.62, 0.5, 0.4) : band_col.rgb;
		g = mix(g, vec3(1.0, 0.97, 0.85), smoothstep(0.62, 0.72, ndl));
		float rib = abs(fract(v / 0.45) - 0.5);
		g = mix(g, ink_col.rgb, (1.0 - smoothstep(0.03, 0.09, rib)) * 0.8);
		c = vec4(g, 1.0);
	} else if (mode > 0.4) {
		edge = 1.0 - abs(a);
		olw = clamp(outline / hw, 0.0, 0.7);
		c = strand(a, hw, v, nl, s, 1.0);
	} else if (mode > 0.15) {
		// kurt postu (kuyruk / post sarkığı): açık post, uçlara doğru sivri kıl tutamları kenarda mürekkep
		edge = 1.0 - abs(a);
		olw = clamp(outline / hw, 0.0, 0.6);
		float ndl = -a * nl + sqrt(max(0.0, 1.0 - a * a)) * 0.45;
		vec3 fc = ndl < 0.1 ? fur_shade.rgb : fur_col.rgb;
		float lane = floor(a * hw / 0.5);
		float f = fract(a * hw / 0.5 + 0.3 * sin(v * 0.5 + lane));
		fc = mix(fc, fur_hi.rgb, smoothstep(0.62, 0.78, ndl) * step(f, 0.55));
		fc = mix(fc, ink_col.rgb, (1.0 - smoothstep(0.02, 0.1, abs(f - 0.5) * 0.5)) * (1.0 - smoothstep(0.0, 0.5, ndl)) * 0.6);
		c = vec4(fc, 1.0);
	} else {
		edge = 1.0 - abs(a);
		olw = clamp(outline / hw, 0.0, 0.75);
		c = strand(a, hw, v, nl, s, 0.0);
	}
	// mürekkep konturu + ekran uzayında kenar yumuşatma
	float fw = max(fwidth(edge), 1e-4);
	float ink = 1.0 - smoothstep(olw - fw * 0.75, olw + fw * 0.75, edge);
	c.rgb = mix(c.rgb, ink_col.rgb, ink);
	c.a = smoothstep(0.0, fw * 1.25, edge);
	c *= tint;
	c.rgb = mix(c.rgb, flash_color.rgb, flash);
	COLOR = c;
}

void light() {
	vec3 lit = COLOR.rgb * LIGHT_COLOR.rgb * LIGHT_ENERGY;
	if (LIGHT_IS_DIRECTIONAL) {
		lit *= light_k * (1.0 - moon_shade);
	} else {
		lit *= point_k;
	}
	LIGHT = vec4(lit, LIGHT_COLOR.a);
}
