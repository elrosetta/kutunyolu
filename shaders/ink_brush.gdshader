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

const float INK_W = 0.83;

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

void fragment() {
	float layer = floor(UV.y * 0.5);
	float v = UV.y - layer * 2.0;
	float age = clamp(COLOR.a, 0.0, 1.0);
	if (layer > 2.5) {
		float typ = floor(UV.x * 0.5);
		float a;
		vec3 c = fleck(UV.x - typ * 2.0, v, typ, age, a);
		COLOR = vec4(c * a, typ > 1.5 ? a * 0.4 : a);
	} else {
		float vi = v / INK_W;                         // 0 iç kenar, 1 mürekkep dış kenarı (bıçak ucu), >1 ışıma
		// kıllar boyuna uzandığından mip düzeyi yalnızca enine türevden: hızlı süpürmede boyuna sıkışma
		// (u türevi büyük) dokuyu enine de bulanıklaştırıp bloklu kesikler üretmesin
		vec2 buv = vec2(UV.x, clamp(vi, 0.004, 0.996));
		vec2 gx = dFdx(buv) * vec2(0.12, 1.0);
		vec2 gy = dFdy(buv) * vec2(0.12, 1.0);
		vec4 b = textureGrad(bristle, buv, gx, gy);
		float back = step(0.5, layer) * step(layer, 1.5);
		float ghost = step(1.5, layer);
		float rg = rough * (1.0 + back * 0.6 + ghost * 0.4);
		// kenarlar: iç kenar kıl uçlarıyla pürüzlü ve kuru, dış kenar (bıçak ağzı) daha keskin
		float e_in = vi;
		float e_out = 1.0 - vi;
		float er = age * age;
		float rag_in = ((b.a - 0.5) * 0.45 + (b.r - 0.5) * 0.7) * rg;
		float rag_out = ((b.a - 0.5) * 0.22 + (b.b - 0.5) * 0.12) * rg * (0.6 + age * 1.6);
		float shape = min(e_in * 3.2 + rag_in - er * 1.6, e_out * 7.0 + rag_out - er * 2.2);
		// kuru fırça: kıl yükü (R) kuruluk eşiğinin altında kalan yerler boş; içe ve yaşa doğru kurur
		float dry = 0.05 + dry_in * rg * (1.0 - smoothstep(0.0, 0.62, e_in)) + age * (0.75 + 0.2 * rg) + ghost * 0.25;
		float strand = (b.r - dry) * 5.0;
		// erime: yaşlandıkça yalnızca kimliği yüksek kıllar kalır -> kıl telleri
		float survive = (b.b * 0.7 + b.a * 0.3 + 0.3 - age * 1.25) * 5.0;
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
		// sıcak ön kenar: bıçak ucunun hemen içinde, taze kısımda; yaşla turuncuya söner
		float fresh = 1.0 - smoothstep(0.0, 0.32, age);
		float lead = 1.0 - smoothstep(0.0, 0.16, age);    // en taze kısım: bıçağın hemen arkası
		float hot = smoothstep(0.62, 0.95, vi) * lead * lead * (1.0 - back) * (1.0 - ghost);
		col = mix(col, c_hot * hot_gain, hot);
		col = mix(col, c_rim * 1.3, smoothstep(0.7, 0.95, vi) * (1.0 - fresh) * 0.35 * (1.0 - back));
		col *= 1.0 + fresh * 0.3 * (1.0 - back);
		alpha *= 1.0 - ghost * (0.45 + 0.4 * age);
		// dış ışıma: mürekkep dış kenarının ötesinde, toplamalı, kısa ömürlü
		float halo = (1.0 - smoothstep(0.96, 1.2, vi)) * smoothstep(0.55, 0.98, vi);
		vec3 add = mix(c_rim, c_hot, 0.35) * glow_gain * halo * fresh * fresh * (1.0 - back) * (1.0 - ghost);
		COLOR = vec4(col * alpha + add * (1.0 - alpha), alpha);
	}
}
