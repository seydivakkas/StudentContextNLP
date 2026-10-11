# T3-AUTO v0.3 — Kaynak Kavram Bazında Gruplama ve Tam 10.804 Kayıt İçin Offline QA

**Araştırma durum kaydı (11 Ekim 2026):** T3-AUTO v0.2 Windows yerel yazılım testleri 43/43 PASS; 240 kör kaynak/çeviri örneği yeniden tarandı: 53 HIGH, 59 MEDIUM, 128 UNFLAGGED, 220 kural tetiklemesi. Aynı örneklemde 53 **otomatik uygulanmamış** kavram düzeltme önerisi, 35 farklı kaynak–hedef alan/kural kanıtı ve 49 ayrı `item_key` bildirildi. Bunlar doğrulanmış yanlış çeviri sayıları değildir.

## Kaynak kavram bazında 240 kayıtlık gerçek örneklem özeti

Kullanıcı tarafından yüklenen **aynı 240 EN→TR çiftinin v0.2 kurallarıyla tekrarlanması** ve otomatik kural sonuçlarının kaynağa göre gruplanması:

| Kavram / denetim | Kural tetiklenmesi | Etkilenen farklı kayıt | Farklı metin alanı + kaynak/hedef çifti |
|---|---:|---:|---:|
| Olumsuzluk (*negation*) | 56 | 54 | 37 |
| Türkçede kalan İngilizce terimler | 41 | 23 | 22 |
| Ampul (*bulb*) | 21 | 11 | 8 |
| Sayı uyuşmazlığı | 17 | 17 | 10 |
| Katı (*solid*) | 11 | 10 | 7 |
| Kalsit (*calcite*) | 10 | 3 | 7 |
| Mililitre → litre | 8 | 8 | 6 |
| Saksı (*plant pot*) | 6 | 6 | 2 |
| Buharlaşma (*evaporate*) | 5 | 5 | 3 |
| Çakıl taşı (*pebbles*) | 5 | 4 | 2 |

**Sayılar birbirine eklenerek farklı hatalı kayıt toplamı bulunamaz.** Bir kayıt üç metin alanında birden fazla kural tetikleyebilir. Örneğin ampul için iki ayrı kural (`BULB_AS_BUS` ve `TERM_NOT_EVIDENT:bulb_in_circuits`) aynı kaydı işaretleyebilir. Kaynak–hedef çiftlerinin benzersizliği alan bazlıdır; farklı soru veya referans alanındaki aynı dizi ayrı sayılır. Tüm işaretlenmeyen metinlerin doğru olduğu çıkarılamaz.

## Mühendislik modülü

`audit_translation_corpus.py`, orijinal 4 SciEntsBank bölümündeki toplam **10.804** kaynak satırın, aynı satır kimlikleri üzerinden 10.804 Türkçe adayla eşleştirilerek çevrimdışı taranması için geliştirildi. Gerekli koşullar:

- `data/raw/file_manifest.json` verisi resmî sabit SciEntsBank kaynağı revizyonuyla ve ham dosyaların SHA-256'sıyla uyuşmalı
- `data/tr_v0_2/translation_manifest.json` tam kapsamlı, `UNVERIFIED_MACHINE_TRANSLATION`, `projected_labels_are_gold=false` durumunda olmalı
- Her splitte kaynak `id`, özgün `label`, İngilizce soru/referans/öğrenci metni ve Türkçe satır sayısı birebir karşılaştırılmalı
- 240 donmuş örnek ile tam veri kaydı, İngilizce/Türkçe metinleri açısından birebir eşleşmeli
- Aynı 240 örneğe tekrar çalıştırılan kurallar, araştırmacının `reports/tr_auto_qa_v03/qa_summary.json` agregatlarıyla **tam eşleşmeli**; farklıysa durmalı
- Sonuçlar yalnızca yeni `reports/tr_auto_full_v01` klasörüne yazılmalı, eski raporlar/çeviri/derecelendirme dosyaları **değiştirilmemeli**.

### Windows'ta çalıştırma

```powershell
.\.venv\Scripts\python.exe audit_translation_corpus.py --data-dir data/tr_v0_2 --source-dir data/raw --sample reports/tr_review/blind_stage1/review_A_blind.csv --sample-summary reports/tr_auto_qa_v03/qa_summary.json --out reports/tr_auto_full_v01
```

### Yerel çıktı dosyaları

| Dosya | Ne içerir? |
|---|---|
| `full_qa_summary.json` | Split başına satır, yüksek/orta öncelikli kayıt ve rule/concept sayılarını, kaynak SHA kayıtlarını, örneklem yeniden karşılaştırmasını |
| `full_qa_summary.md` | İnsan tarafından okunabilir toplu özet ve kaynak kavram tablosu |
| `concept_summary.csv` | Kaynak kavram bazında tüm korpus tetiklenmesi, farklı kayıt sayısı, farklı metin kanıtı |
| `concept_by_split.csv` | Aynı kavramların `train/test_ua/test_uq/test_ud` ve alan dağılımı |
| `repeated_evidence.csv` | Aynı kural + metin alanı + kaynak/hedef örneğinin yinelendiği kanıtlar |
| `full_translation_flags.csv` | Kaynak ve hedef metin, alan, kural, öncelik, soru–satır anahtarı; **yerelde tutulmalı** |

**Gerçek tam veri taraması kullanıcı Windows bilgisayarında tamamlandı (11 Ekim 2026):** 10.804/10.804 satır, 49/49 regresyon testi PASS, 1.930 HIGH + 2.278 MEDIUM inceleme adayı, 6.596 işaretlenmeyen kayıt ve 7.412 kural bulgusu. Yerel artefaktlar `reports/tr_auto_full_v01/` altındadır. [Ayrıntılı gerçek çalıştırma ve kök neden planı](../paper/T3_FULL_CORPUS_REAL_2026-10-11.md). Bu kural sonuçları insan eliyle doğrulanmış çeviri hataları değildir.

## Akademik metodoloji

Bu araçlar birer **heuristic error-candidate mining** yazılımıdır; yanlış alarm ve kaçırılmış hata oranları insan ya da bağımsız doğruluk etiketi olmaksızın ölçülemez. Kullanıcının tercihine uygun olarak T3-HUMAN **NOT_PERFORMED** statüsünde kalacak; Cohen kappa uydurulmayacak. `T4` Türkçe skorları üretildiğinde orijinal veri üzerinden *projected-label exploratory proxy results* olarak nitelendirilecek. Gerçek Türkçe öğrenci genellemesi ayrıca test edilmedikçe iddia edilmeyecek.

## v0.4 — Kök neden ayrıştırması (yeni kod)

`prioritize_translation_issues.py` ile `reports/tr_auto_full_v01/full_translation_flags.csv` içindeki 7.412 kural kaydı, **kaynak kavram + metin alanı + İngilizce kaynak + Türkçe aday çeviri** üzerinden gruplandırılır. Tüm kaynak SHA ve sayaçlar `full_qa_summary.json` ile karşılaştırılır. `P1` fiziksel anlam/birim tersine dönüşü, `P2` belirli yanlış teknik terim, `P3` yüzeysel uyarı sıralaması bir **inceleme önceliğidir**, doğruluk olasılığı değildir. Orijinal ve çevrilmiş veri hiçbir zaman değiştirilmez.

```powershell
.\.venv\Scripts\python.exe prioritize_translation_issues.py --qa-dir reports/tr_auto_full_v01 --out reports/tr_auto_priority_v01
```

Yeni sonuçlar: `root_cause_clusters.csv` (kaynak metinleri içerir, GitHub'a yükleme), `concept_priority.csv`, `root_cause_summary.md`, `root_cause_manifest.json`. Yeni modülün gerçek veri çalıştırması henüz bekliyor.
