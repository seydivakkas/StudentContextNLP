# SciEntsBank-TR v0.2.1 — Gerçek AI_DRAFT İçe Aktarım, Sürümleme ve Karşılaştırmalı QA

**Araştırma durumu (11 Ekim 2026):** 37 gerçek kaynak–hedef kanıtının `AI_DRAFT` taslağına karşılık gelen **34 APPLY_EXPLORATORY + 3 PENDING** önerisi mevcut. Hiçbiri bağımsız insan veya Türkçe altın standart etiketi değildir. Bunlar bilimsel olarak gerekçelendirilmiş *keşifsel* düzeltme önerileridir.

**Eski dosyaları silme veya GitHub'a yükleme:** `data/raw`, `data/tr_v0_2`, `reports/tr_auto_full_v01`, `reports/tr_auto_priority_v01`, `reports/tr_patch_plan_v021` ve bağımsız A/B formları hiçbir aşamada silinmez/üzerine yazılmaz. Kaynak öğrenci metinleri/CSV'ler `data/` ve `reports/` altındadır, `.gitignore` korumasıyla **yalnız yerel** kalır. GitHub'a yalnız kaynak kodu, sentetik testler, yöntem ve anonim toplam istatistik eklenir.

**Bilinen AI_DRAFT ZIP SHA-256:** `a9ecd6ce70eeb4d5d2947a778ac0fe2f233533598bb547e2d1a926e81466670c`. İçerideki aday CSV: `3cb18fc1fddf59f73d166a47f92bc7e5668bf07387ee6d1e1e647679470aef23`. Özgün PENDING CSV: `6325d1cc9934d5e4595f9f3850e74e6f7e0f93a23b6c0a32314657bc3f327017`. Bu özetler gerçek kullanıcı tarafından yüklenen kapalı paket için doğrulanmıştır; ham metin hiçbir GitHub dosyasına konmamıştır.

## Girdi

- Önceden bu sohbet içinde üretilmiş `StudentContextNLP_v021_AI_DRAFT_37.zip`. **İndirip Windows bilgisayarında sakla**. ZIP üç dosya içerir: `patch_candidates_AI_DRAFT.csv`, `AI_DRAFT_manifest.json`, `AI_DRAFT_37_INCELEME_RAPORU.md`.
- Bilinen orijinal (değişmemiş) plan: `reports/tr_patch_plan_v021/patch_candidates.csv` ve `patch_plan_manifest.json`.
- v0.4 ve v0.3 gerçek kanıt klasörleri: `reports/tr_auto_priority_v01/`, `reports/tr_auto_full_v01/`.
- Değişmemiş kaynak aday CSV: `data/tr_v0_2/` (10.804 satır).

### Kaynakları silmeden üç yerel işlem

```powershell
# 1. ZIP kanıt kökenini kontrol edip ayrı bir AI_DRAFT planı oluştur:
.\.venv\Scripts\python.exe import_ai_draft_patch.py --package "C:\path\to\StudentContextNLP_v021_AI_DRAFT_37.zip" --source-plan reports/tr_patch_plan_v021 --out reports/tr_patch_plan_v021_ai_draft

# 2. Yalnız APPLY_EXPLORATORY seçilmiş tam cümleleri yeni aday klasörüne uygula:
.\.venv\Scripts\python.exe apply_translation_patch_plan.py --priority-dir reports/tr_auto_priority_v01 --plan-dir reports/tr_patch_plan_v021_ai_draft --data-dir data/tr_v0_2 --out data/tr_v0_2_1

# 3. Eski ve yeni 10.804 satırdaki soru/referans/öğrenci açıklamasını karşılaştır:
.\.venv\Scripts\python.exe compare_translation_versions.py --old-dir data/tr_v0_2 --new-dir data/tr_v0_2_1 --full-qa reports/tr_auto_full_v01 --plan-dir reports/tr_patch_plan_v021_ai_draft --out reports/tr_compare_v021
```

**İlk uygulamadan önce:** Orijinal CSV'nin SHA-256'sı, paketin kendi `AI_DRAFT_manifest.json` SHA değeri ve 37 sıralı `cluster_id` kontrol edilir; yeni plan ancak bütün 34/3 kararları ile kökenler eşleşirse oluşturulur. Gerçek veri üstündeki uygulama aşaması `analyze_pair` seçilen hataların hâlâ görünüp görünmediğini, oluşan yeni yüksek öncelikli işaretleri ve aynı tam kaynak–hedef eşleşmesinin etkilenen satır sayısını ayrıca denetler. **Herhangi bir koşul sağlanmazsa işlem durur; diğer adaylara sessizce geçilmez.** Olası `.part` klasörleri başarısız koşu kanıtıdır, kontrol edilmeden silinmemelidir.

### Oluşturulan yerel artefaktlar

| Klasör | Çıktı | Anlamı |
|---|---|---|
| `reports/tr_patch_plan_v021_ai_draft/` | `patch_candidates.csv`, `patch_plan_manifest.json`, `import_manifest.json` | Asıl 37 kaynak metin ve kanıtın değiştirilmediği, yalnız AI_DRAFT alanları güncellenmiş ayrı plan |
| `data/tr_v0_2_1/` | 4 split CSV, `translation_manifest.json`, `patch_audit.csv` | Sadece izlenebilir açık düzeltmelerin uygulanmış olduğu **UNVERIFIED_EXPLORATORY_AI_ASSISTED_PATCH** aday korpusu |
| `reports/tr_compare_v021/` | `comparison_manifest.json`, `comparison_summary.md`, `rule_delta.csv`, `concept_delta.csv`, `changed_field_comparison.csv` | Gerçek değişen satır ve alan sayısı, eski/yeni otomatik kural bulguları, regressions, SHA ve alan koruma kontrolleri |

### Karşılaştırma kabul kapıları

- v0.2 orijinal manifest ile 10.804 satırlık T3-AUTO denetim manifesti SHA-256 bakımından eşleşmeli.
- v0.2.1 manifesti orijinal sürümü ve düzenlenmiş plan CSV'sini SHA ile referanslamalı.
- **Dört split + üç metin alanı** birebir korunmalı; İngilizce soru/referans/öğrenci kaynakları, `id`, `label`, `label_status=UNVERIFIED_TRANSFER` ve `translation_scope=FULL_CANDIDATE` değişmemeli.
- Bütün değişiklikler `patch_audit.csv` içindeki `(field, source_en, old_tr, new_tr)` tam eşleşmesine karşılık gelmeli.
- Verinin önceki 7.412 bulgusu otomatik kodla tekrar üretilmeli; orijinal kural/split sayıları değişirse karşılaştırma durmalı.
- Düzeltilmiş hücrelerde yeni HIGH kural oluşursa karşılaştırma **başarısız** sayılmalı. **Bulguların azalması, semantik doğruluğu veya öğrenci yanılgılarının korunmasını ispatlamaz.**
- Araştırmada insan değerlendirmesi/Kappa hâlâ yapılmamış, Türkçe gold hâlâ yoktur; Türkçe model sonuçları ancak *projected-label exploratory proxy* olarak raporlanabilir.

### Uygulama durumları

**Gerçek Windows aşaması 11 Ekim 2026'da tamamlandı:** özgün v0.2 ve yeni v0.2.1 ayrı klasörlerde korunarak 10.804/10.804 kayıt karşılaştırıldı; 64/64 yazılım testi PASS. Aşağıdaki gerçek sonuçlar yalnız otomatik kural analizidir; semantik doğruluk bağımsız olarak ispatlanmış değildir. Bir blokaj veya yeni kanıt bulunursa SHA veya bilimsel anlam koruması **gevşetilmez**; ilgili küme ayrı incelenir. Tam hata listeleri/öğrenci açıklamaları GitHub'a yüklenmez.

## Windows gerçek veri kabulü — 11 Ekim 2026

**Kaynak kanıt:** Araştırmacının yerel PowerShell günlüğü. Kod/testler GitHub CI'da doğrulanmıştır; gerçek veri ve özel satır düzeyi dosyalar yalnız araştırmacının Windows bilgisayarında bulunmaktadır.

| Kabul kalemi | Gerçek sonuç |
|---|---:|
| Yazılım regresyon testi | 64 / 64 PASS |
| AI_DRAFT ZIP SHA-256 | PASS |
| Kanıt eşleşmesine alınan aday | 37 |
| Açık seçilen tam cümle önerisi | 34 |
| Beklemede bırakılan belirsiz kayıt | 3 |
| Her iki veri sürümündeki satır | 10.804 |
| Yeni sürümde düzenlenen ayrı kayıt | 1.604 |
| Düzenlenen Türkçe metin alanı örneği | 1.748 |
| Orijinal QA kural bulgusu | 7.412 |
| Yeni QA kural bulgusu | 4.926 |
| **QA tetiklenmelerindeki mutlak değişim** | **−2.486** |
| **Kural tetiklenmelerindeki oransal değişim** | **−%33,54** |
| Yeni HIGH-kural regresyonu | 0 |
| Korunan orijinal dosyaların SHA-256'sı | PASS |
| Bağımsız insan doğrulaması | YAPILMADI |

### Split düzeyinde tekrar çalıştırılabilir sayımlar

| Split | Satır | Eski HIGH | Yeni HIGH | Eski MEDIUM | Yeni MEDIUM |
|---|---:|---:|---:|---:|---:|
| train | 4.969 | 983 | 314 | 1.139 | 1.350 |
| test_ua | 540 | 118 | 39 | 121 | 149 |
| test_uq | 733 | 53 | 20 | 243 | 244 |
| test_ud | 4.562 | 776 | 163 | 775 | 1.145 |
| **Toplam** | **10.804** | **1.930** | **536** | **2.278** | **2.888** |

İşaretli **farklı satır** sayısı 4.208'den 3.424'e, hiç işaretlenmeyen satır sayısı 6.596'dan 7.380'e değişmiştir. HIGH→MEDIUM kayma olasılığı vardır; bu agregatlar tek tek satırların öncelik geçişlerini **kanıtlamaz**. Değişen 1.604 kayıt, değişen 1.748 Türkçe metin alanı örneğiyle karıştırılmamalıdır. Tekrarlanan sorular/referanslar aynı tam eşleşme düzeltmesinden etkilenebilir.

**Kabul kararı:** v0.2.1 `UNVERIFIED_EXPLORATORY_AI_ASSISTED_PATCH` durumunda sürümlü *aday veri* olarak teknik olarak PASS. Türkçe bilimsel anlamın ve öğrenci yanılgılarının korunduğuna dair bağımsız gold kabulü **HOLD**. Otomatik kural tetiklenmesi %33,54 azalmıştır; gerçek çeviri hata oranı, kalite puanı, model Macro-F1 iyileşmesi veya nedensel etki olarak sunulamaz.

**Korunan özel artefaktlar:** `reports/tr_patch_plan_v021_ai_draft/`, `data/tr_v0_2_1/`, `reports/tr_compare_v021/`, `data/tr_v0_2/`. Yeniden üretilebilir QA için `comparison_manifest.json`, `rule_delta.csv`, `concept_delta.csv` dosyaları kendi bilgisayarında tutulur; satır metinleri GitHub'a gönderilmez.

**Sıradaki analitik kapı:** Test-UQ soru kümelerine duyarlı İngilizce/Türkçe karşılaştırmalı proxy modellerini çalıştırmadan önce v0.2↔v0.2.1 etiket/sınıf frekansı, değişen alan dağılımı, tekrarlanan soru/referans kaynaklı etki ve kural uyarılarının sınıflara göre değişimlerini ayrı raporla. Veri kümesine veya İngilizce P1 baseline dosyalarına yeni müdahale yapma.
