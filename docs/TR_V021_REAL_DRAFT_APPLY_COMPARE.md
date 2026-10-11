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

İlk kez gerçek Windows ortamında çalıştırılmadan v0.2.1 korpusunu üretilmiş olarak göstermeyin. Yazılım regresyon CI başarısı sentetik veri üzerindedir. Gerçek veri çalıştırmasında bir blokaj varsa SHA veya bilimsel anlam korumasını **gevşetmeyin**; ilgili kümeyi ayrı inceleyin ve gerekirse yeni sürüm planı oluşturun. Gizlilik gereği tam hata listeleri/öğrenci açıklamaları GitHub'a yüklenmez.
