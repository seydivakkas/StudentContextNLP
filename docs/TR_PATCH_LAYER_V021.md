# SciEntsBank-TR v0.2.1 — Kaynak Kanıtına Kilitli Çeviri Düzeltme Katmanı

**Durum (11 Ekim 2026):** Gerçek Windows çalıştırmasında T3-AUTO v0.5 patch planı **PASS**: 58/58 yazılım testi, 39 uygun P1/P2 tekrar kümesi, mükerrer kavram eşleşmeleri tekilleştirilerek **37 boş düzeltme adayı**. Hepsinin kararı `PENDING`; etkinleştirilmiş düzeltme **0**. Özgün 10.804 satırlık çeviri verisi değişmedi ve **v0.2.1 düzeltilmiş veri kümesi henüz üretilmedi**.

## Gerekçe ve gerçek kanıt

Araştırmacının Windows sistemindeki gerçek T3-AUTO v0.4 sonuçları: 10.804 kayıt; 7.412 heuristik kural bulgusu; 4.208 işaretli aday; 28 kaynak kavramı; **1.460** ayrı **(kavram + metin alanı + kaynak ve hedef metin)** kümesi; **147** tekrar eden kök neden adayı. Regresyon testleri 53/53 PASS; kaynak veri satırında değişiklik 0.

Öncelikli kavramlar: mililitre 391 farklı kayıt / 66 ayrı alan+metin kanıtı; doygunluk 39 farklı kayıt / 2 ayrı kanıt; katı 378/87, buharlaşma 358/127, ampul 306/81, eğim 283/23. Örneğin 100 kaynak kayıt aynı bozuk birimli soru çevirisini içerebilir: **100 farklı düzeltme yapmak** yerine **1 tam kaynak–hedef eşleşmesi** korunarak araştırılmalı.

Bu sayılar gerçek hataların kanıtlanmış sayıları değildir. Kalite uyarıları özellikle Türkçe ek, serbest çeviri ve sayının yazıyla ifade edilmesi nedeniyle yanlış alarm verebilir.

## İki güvenli işlem

### 1. Kanıt temelli, boş düzeltme şablonu oluştur

```powershell
.\.venv\Scripts\python.exe prepare_translation_patch_plan.py --priority-dir reports/tr_auto_priority_v01 --out reports/tr_patch_plan_v021 --limit 100 --min-rows 2
```

Çıktı:
- `reports/tr_patch_plan_v021/patch_candidates.csv`: tekrar eden P1 ve P2 kaynak–hedef eşleşmelerini ve `proposed_tr` (BOŞ), `decision=PENDING`, `curation_origin` (BOŞ), `evidence_note` (BOŞ) alanlarını içerir.
- `reports/tr_patch_plan_v021/patch_plan_manifest.json`: kanıt kökeni, SHA-256, seçilen sayısı, ilgili kayıt sayılarının **toplamı (tekilleştirilmemiş)**, değişiklik sayısı **0**.

Bu işlem **hiçbir çeviriyi değiştirmez**. Farklı bilimsel kavram kuralları aynı tam İngilizce–Türkçe çifte işaret ediyorsa çelişen öneri oluşmaması için tek bir aday tutulur.

### 2. Yalnızca açıkça seçilmiş ve gerekçelendirilmiş tam cümle düzeltmelerini ayrı bir sürümde kullan

Daha sonra önce `patch_candidates.csv` içindeki belirli satırlar bilimsel kaynak anlamına göre ele alınır. Asistanın hazırladığı bir öneri, uzman onaylı altın standart **değil**, `AI_DRAFT` olarak belirtilir. `decision=APPLY_EXPLORATORY`, bütün cümle için `proposed_tr`, `curation_origin=AI_DRAFT` veya `RESEARCHER_EDITED`, ve en az 12 karakter gerekçe bulunmadıkça hiçbir düzeltme etkinleşmez. Kullanıcı doğrudan bütün metni paylaşmadan proje üzerinde gizlice düzenleme yapılmaz.

```powershell
.\.venv\Scripts\python.exe apply_translation_patch_plan.py --priority-dir reports/tr_auto_priority_v01 --plan-dir reports/tr_patch_plan_v021 --data-dir data/tr_v0_2 --out data/tr_v0_2_1
```

**Bu ikinci komutu hemen çalıştırma:** ilk şablonda tüm `decision` değerleri PENDING'dir. Araç bu durumda bilerek hata verip yeni veri üretmez.

Uygulama kapıları:
1. Tam kural denetimi ve kök neden manifestinin SHA-256 eşleşmesi.
2. Adayın değiştirilemez kimliği (`cluster_id`), bilimsel kavram, metin alanı, özgün kaynak ve Türkçe aday SHA-256 kanıtının eşleşmesi.
3. Sadece **tam kaynak+önceki Türkçe hedef+metin alanı** eşleşmesi. Genel `replace()` veya substring değiştirme yok.
4. Yalnızca gerekçeli ve açıkça seçilen tam cümle düzeltmesi. Aynı eşleşmeye iki çelişkili düzeltme yok.
5. Kaynakta görülen bilimsel hata kuralı hâlâ tetikleniyorsa veya yeni yüksek öncelikli kural ortaya çıkıyorsa **reddet**. Bu bir *otomatik semantik doğruluk garantisi değildir*.
6. Düzeltmeden etkilenen satır sayısı, dondurulmuş kümenin `affected_distinct_rows` sayısıyla uyuşmazsa **reddet**.
7. Dört orijinal CSV dosyası ve bütün `source_*_en`, `id`, `label` alanları aynı kalır; yalnız hedef Türkçe alanlarında yeni sürüm yazılır. `quality_flags` uygun biçimde yeniden üretilir.
8. `data/tr_v0_2_1/` yeni ve ayrı klasördür; mevcutsa üzerine yazılmaz. `patch_audit.csv` ve yeni `translation_manifest.json` SHA ve uygulama sayıları sağlar.
9. Yeni veri **`UNVERIFIED_EXPLORATORY_AI_ASSISTED_PATCH`** statüsünde; `projected_labels_are_gold=false`, `UNVERIFIED_TRANSFER` korunur. İnsan değerlendirmesi ve Cohen kappa iddia edilmez.

## Akademik ve etik sınır

Kaynak öğrencinin özgün kavramsal yanlışlığını "doğru bilgi"ye dönüştürmek amaçlanmaz. **Sadık çeviri**, yanlış bir öğrenci yanıtını da yanlış olarak muhafaza edebilir. Asistan önerileri tam bilimsel güvence değildir; gözden geçirilebilir, iptal edilebilir ve bağımsız Türkçe gold etiketlerle karıştırılmaz. Yeniden kullanılan özgün soru/referans çevirileri onarıldığında etkilediği kayıtlar tekil sayılarla kaydedilir. Türkçe model sonuçları yalnızca *exploratory projected-label proxy* araştırması olarak yorumlanır.

**Gizlilik:** Gerçek `patch_candidates.csv`, `patch_audit.csv`, çeviri CSV dosyaları ve ham öğrenci metinleri `reports/` ile `data/tr_*/` klasörlerinde yerelde kalır. GitHub'a yalnız kaynak kod, sentetik testler ve toplu bilimsel sayılar eklenebilir.

## Sonraki gerçek veri kapısı

**T3-AUTO v0.5 PATCH-PLAN tamamlandı:** gerçek Windows sonucu 39 uygun tekrarlı kümeden 37 tekil, tamamı boş/PENDING aday; 58 test PASS. Sonraki aşamada kullanıcı yalnız yerel `patch_candidates.csv` ve `patch_plan_manifest.json` dosyalarını inceleme için paylaşacak. Gerçek İngilizce–Türkçe cümleler kaynak anlamına göre tek tek değerlendirilecek; açık düzeltme önerileri `AI_DRAFT` olarak kaydedilecek. Semantik olarak belirsiz olanlar `PENDING` veya `SKIP` kalacak. Boş alanlar doldurulmadan v0.2.1 düzeltilmiş veri sürümü oluşturulmayacak.
