// Stil v2 "mürekkep-cel" karakter gölgelendiricisi (tools/artgen/inkkit.py ile çizilen sprite'lar; json "filter": "linear").
// Cel gölgesi, kontur ve kenar ışığı dokunun içinde çizili: toon_light'ın normal haritasından 3 bantlı nicelemesi
// bu çizimle çatışır (düz yüzey tek banda düşer, gölge iki kez uygulanır). Burada ışık yalnızca renk ve şiddet taşır:
// her ışık dokuyu düz olarak aydınlatır (ay için light_k, noktasal ışıklarda dokunun kendi düşüşü), sahne gölgesi
// (moon_shade) ve vuruş parlaması/ton (flash, tint) toon_light ile aynı adlarla çalışır.
// Örnekleme: düğümün/CanvasTexture'ın süzgeci (doğrusal + mipmap); piksel-AA yolu yok.
//
// v40 kenar ışığı (rim): sprite'ın alfa kenarından ekran uzayında bir sözde normal türetilir (dört komşu alfa örneği,
// UV türevleriyle ekrana çevrilir; aynalama / dönüş / esneme güvenli). Işık (ay ya da noktasal) kenara hangi yandan
// geliyorsa orada ince, ışığın renginde bir kenar parlaması belirir: karakter ortamdan ayrılır, meşale yanından
// geçerken siluet sıcak kenar alır. İç konturlar (alfa 1) etkilenmez; iç yüzey düz kalır (cel çizimi bozulmaz).
shader_type canvas_item;

uniform float flash : hint_range(0.0, 1.0) = 0.0;
uniform vec4 flash_color : source_color = vec4(1.0, 0.97, 0.9, 1.0);
uniform vec4 tint : source_color = vec4(1.0, 1.0, 1.0, 1.0);
// ay gölgesi (GroundShadow, Level.moon_occluded): yönlü ışığın bu payı kesilir
uniform float moon_shade : hint_range(0.0, 1.0) = 0.0;
// yönlü ışık (ay) katkı çarpanı: toon_light'ın ortalama bandına (~0.8) denk
uniform float light_k : hint_range(0.0, 2.0) = 0.85;
// noktasal ışık katkı çarpanı (ocak, çıra, Kut)
uniform float point_k : hint_range(0.0, 2.0) = 0.9;
// v40 kenar ışığı: güç (0 = kapalı) ve kenar genişliği (doku pikseli)
uniform float rim_k : hint_range(0.0, 2.0) = 0.55;
uniform float rim_w = 1.6;
// Kol iskeleti parçaları (bengu_kol_v2.json "alt_row"): dokunun ikinci satırı aynı parçanın ışığı parça ekseninde
// aynalanmış çizimi. alt_uv = o satırın UV kayması (0 = kapalı, gövde sprite'ları). Parçanın ekrandaki dönüşü, esnemesi ve
// flip_h'si UV türevlerinden çözülür: dünya ışığı (sol üst) dokuda hangi yandan geliyorsa o çizim seçilir (yumuşak geçiş).
// Böylece kol başın üstüne kalksa ya da karakter sola dönse de gölge hep ışığın tersinde kalır.
uniform vec2 alt_uv = vec2(0.0);
uniform vec2 world_light = vec2(-0.74, -0.67);
varying vec2 wpos;
varying vec4 vcol;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 0.0, 1.0)).xy;
	vcol = COLOR;
}

void fragment() {
	vec4 c = COLOR;
	vec2 duv = vec2(0.0);
	vec2 dvv = vec2(0.0);
	if (alt_uv != vec2(0.0)) {
		// UV = A * dünya + b (afin): A = dUV * inverse(dDünya), ekran türevlerinden
		mat2 du = mat2(dFdx(UV), dFdy(UV));
		mat2 dw = mat2(dFdx(wpos), dFdy(wpos));
		float det = determinant(dw);
		if (abs(det) > 1e-8) {
			vec2 l_px = (du * inverse(dw) * normalize(world_light)) / TEXTURE_PIXEL_SIZE;
			float w = smoothstep(-0.28, 0.28, normalize(l_px + vec2(1e-6)).x);
			vec4 b = texture(TEXTURE, UV + alt_uv) * vcol;
			c = mix(c, b, w);
		}
	}
	if (rim_k > 0.001) {
		// alfa eğimi (doku uzayı) → ekran uzayı: da/dx = <gu, dUV/dx>, da/dy = <gu, dUV/dy>
		vec2 px = TEXTURE_PIXEL_SIZE * rim_w;
		float aL = texture(TEXTURE, UV - vec2(px.x, 0.0)).a;
		float aR = texture(TEXTURE, UV + vec2(px.x, 0.0)).a;
		float aU = texture(TEXTURE, UV - vec2(0.0, px.y)).a;
		float aD = texture(TEXTURE, UV + vec2(0.0, px.y)).a;
		vec2 gu = vec2(aR - aL, aD - aU);   // alfanın arttığı yön (içeri)
		vec2 gs = vec2(dot(gu, dFdx(UV)), dot(gu, dFdy(UV)));
		float e = clamp(length(gu) * 1.3, 0.0, 1.0) * step(0.5, c.a);
		vec2 nrm = -normalize(gs + vec2(1e-7, 0.0));   // dışarı bakan kenar normali (ekran uzayı)
		NORMAL = vec3(nrm * e, sqrt(max(0.0, 1.0 - e * e)));
	}
	c *= tint;
	c.rgb = mix(c.rgb, flash_color.rgb, flash);
	COLOR = c;
}

void light() {
	vec3 lit = COLOR.rgb * LIGHT_COLOR.rgb * LIGHT_ENERGY;
	// kenar ışığı: ışığa bakan kenar; yüzey normali (0,0,1) olan iç bölgede 0
	float rim = 0.0;
	if (rim_k > 0.001) {
		float e = length(NORMAL.xy);
		rim = max(0.0, dot(normalize(NORMAL.xy + vec2(1e-6, 0.0)), LIGHT_DIRECTION.xy)) * e;
		rim = rim * rim * rim_k;
	}
	if (LIGHT_IS_DIRECTIONAL) {
		float k = light_k * (1.0 - moon_shade);
		lit *= k;
		lit += LIGHT_COLOR.rgb * LIGHT_ENERGY * rim * (0.9 - moon_shade * 0.6) * (0.35 + 0.65 * COLOR.a);
	} else {
		lit *= point_k;
		lit += LIGHT_COLOR.rgb * LIGHT_ENERGY * rim * 0.8 * (0.35 + 0.65 * COLOR.a);
	}
	LIGHT = vec4(lit, LIGHT_COLOR.a);
}
