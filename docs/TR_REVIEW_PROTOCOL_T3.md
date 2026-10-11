# T3 — Öğrenci Açıklaması EN→TR Çeviri İncelemesi: İki Aşamalı Kör Protokol

> **Durum 11 Ekim 2026:** 10.804 aday çeviri tamamlandı. 240 kayıt örneklendi (her splitten 60, her kaynak türetilmiş sınıftan 60); 73 örnek otomatik kalite bayrağı taşıyor. İnsan değerlendirme yanıtları henüz toplanmadı. Bu sayılar araştırmacının Windows terminal çıktısından aktarılmıştır.

## Bilimsel amaç ve sınır

Amaç **çeviri sadakatini ve orijinal öğrenci yanılgısı/etiket niteliğinin korunmasını ölçmek**, otomatik olarak altın standart Türkçe veri üretmek değildir. Araştırma kaynağı İngilizce SciEntsBank'tir; Türkçeye çevrilen yanıtlar Türkiye'deki öğrencilerin doğrudan yazdığı doğal Türkçe metinlerle eşdeğer sayılmaz.

**Örnekleme:** `sample_translation_review.py` seed=20261010, split ve sınıf kapsamı + soru çeşitliliği + kalanlar arasından rastgele tamamlama. Dört split ve dört etiketin *marjinal dağılımları* dengelidir. **Bu, tüm split×sınıf hücrelerinin eşit olduğu veya istatistiksel olasılık örneklemi olduğu anlamına gelmez.** Bu tabakalı örneklemin ham oranını evren oranıymış gibi sunma. `quality_flags` 73/240 yalnızca yüzeysel işaretlerdir; doğrulanmış hata oranı değildir.

## Aşama 1 — Etikete ve otomatik uyarılara kör değerlendirme

1. Kullanıcı `review_A.csv` ve `review_B.csv` dosyalarını oluşturmuş olmalı; `review_manifest.json` 240 örnek kaydetmeli.
2. `prepare_blinded_reviews.py --review-dir reports/tr_review` komutu dosyaları **orijinallerin üzerine yazmadan**, `reports/tr_review/blind_stage1/` içine üretir.
3. Bağımsız iki gerçek insan değerlendiriciye yalnız sırasıyla `review_A_blind.csv` ve `review_B_blind.csv` iletilir; `class4`, `quality_flags`, `split`, özgün kayıt `id` ve otomatik model yargısı **bu formlarda yoktur**.
4. Her değerlendirici **özgün İngilizce soru/referans/öğrenci yanıtını** ve **Türkçe karşılıklarını** inceleyerek *anlam* ve *özgün bilimsel hata* korunumu işaretler. Uzmanlar aralarında görüş alışverişi yapmaz; gerekli nitelikli İngilizce/Türkçe okuma ve ilgili fen kavramı bilgisi olmalıdır.
5. `meaning_preserved`: **yes** = bilimsel olarak ilgili anlam korundu; **no** = anlam kayması, bilgi ekleme/çıkarma veya kritik çelişki; **uncertain** = kararsız/bağlam yetersiz.
6. `error_preserved`: **yes** = İngilizce öğrenci açıklaması yanlışsa aynı hata/eksiklik korunmuş; doğruysa çevrilen açıklama da doğru kalmış; **no** = hata düzeltilmiş, değiştirilmiş, yeni hata oluşmuş veya doğruluk bozulmuş; **uncertain** = bilimsel hata niteliği karara bağlanamıyor.
7. `notes`: gerekirse somut terminoloji, olumsuzlama, sayısal değer, üslup, kavramsal kayma gerekçesini belirt; kişisel kimlik ekleme.

Özgün öğrenci yanılgısını düzeltme! Kaynak anlamı Türkçeye aktarırken öğrenci yanıtındaki bilimsel yanlışlığın korunması gerekebilir. **Çeviri başarısı ile açıklamanın fen bakımından doğruluğu ayrı olgulardır.**

## Aşama 2 — Kaynak etiket ve müdahale ihtiyacının değerlendirilmesi

- **Yalnız A ve B kör değerlendirmelerini ayrı ayrı tamamlayıp dosyaları dondurduktan sonra** kaynak projeksiyon sınıfı görülür.
- Kaynak `review_A.csv` ve `review_B.csv` içindeki `class4` **başlangıç etiketi olarak** incelenir; hakikatin/uzman etiketinin kanıtı olarak kabul edilmez.
- `label_still_applicable`: **yes** = İngilizce kaynakta verilen orijinal dört sınıflı etiket, Türkçe çeviri için hâlâ uygun; **no** = anlam/yanılgı değişikliği nedeniyle artık uygun değil; **uncertain** = karar verilemiyor. Kaynakta 7 özgün çelişkili üçlü bulunduğunu unutma; kaynak etiketin hatalı olma olasılığını ayrı notlandır.
- `correction_needed`: **yes** = çeviriye manuel müdahale gerekir; **no** = gerekmez; **uncertain** = emin değil. Düzeltme, bilimsel yanlış cevabı doğru yapma amacı taşıyamaz; kaynak metne sadakati geri sağlamayı hedeflemelidir.
- `notes` alanında iki aşama arasında anlaşmazlık/düşünce değişimi görülebilir; ilk aşama değerlendirmelerini silme.
- **Henüz çalıştırılmayacak:** `evaluate_translation_reviews.py` yalnız iki aşama tamamlandıktan sonra, bütün alanları içeren birbirinden bağımsız bitmiş A/B formlarıyla çalıştırılmalıdır. Aşama 1 yanıtlarını örneklem kayıtlarıyla eşleştirecek ayrı bir birleştirme denetimi gerekir; manuel, kayıtsız kopyala-yapıştır yapılmamalıdır.

## Bağımsız değerlendirme ve raporlama

- Her alan için nitelikli iki değerlendiricinin tamamladığı **yes/no/uncertain** kararı, gözlenen anlaşma, Cohen kappa, anlaşmazlık sayısı.
- `uncertain` dışlanmış gibi davranma; önceden belirlenmiş rapor yöntemiyle ayrı göster.
- Uzlaşma/adjudikasyon kararları, **ham bağımsız A/B değerlendirmelerini değiştirmeden** ek bir dosyada tutulmalı.
- İnsan kalite oranı, otomatik bayrak ve veri kümesi etiketleri birbirine karıştırılmaz. Sadece 240 örnek üzerinden veri kümesinin % tamamına gold denmez.
- Kod, şema, toplamlar ve SHA manifestleri GitHub'a eklenebilir. **Özgün ve çevrilmiş öğrenci açıklamaları veya inceleme CSV'leri GitHub'a eklenmez.** İlk formlar `reports/` içindedir ve gitignore kapsamındadır.

## Kabul kapısı

| Kontrol | Kural |
|---|---|
| T3.0 | 240 benzersiz örnek; iki boş özgün değerlendirme dosyası — **PASS (Windows çıktısı)** |
| T3.1 | Kör anlam/hata korunumu formları kaynak veriyi sızdırmadan üretildi; iki bağımsız değerlendirici atanacak — **BEKLİYOR** |
| T3.2 | Bağımsız değerlendirmeler tamamlandı; ikinci aşama ve anlaşmazlık analizi, kappa — **BEKLİYOR** |
| T3.3 | Kabul eşiği, insan değerlendirmesi, sınıf/split kırılımları, bayrak duyarlılığı raporlandı — **BEKLİYOR** |
| T4 | Türkçe Macro-F1 deneylerinin bilimsel kabulü — **HOLD (T3 bekliyor)** |
