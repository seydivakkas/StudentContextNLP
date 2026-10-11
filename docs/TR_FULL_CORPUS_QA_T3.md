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

**Çalışma şu an kod ve sentetik regresyon testleri aşamasındadır; gerçek tam 10.804 satırlık QA sonucu henüz alınmadı.** Tam veri taramasından önceki 240 satırlık tarama sonucu gerçek yerel örneğe dayanır. GitHub CI geçmesi yalnız yazılım davranışını doğrular, insan eliyle doğrulanmış çeviri kalitesi değildir.

## Akademik metodoloji

Bu araçlar birer **heuristic error-candidate mining** yazılımıdır; yanlış alarm ve kaçırılmış hata oranları insan ya da bağımsız doğruluk etiketi olmaksızın ölçülemez. Kullanıcının tercihine uygun olarak T3-HUMAN **NOT_PERFORMED** statüsünde kalacak; Cohen kappa uydurulmayacak. `T4` Türkçe skorları üretildiğinde orijinal veri üzerinden *projected-label exploratory proxy results* olarak nitelendirilecek. Gerçek Türkçe öğrenci genellemesi ayrıca test edilmedikçe iddia edilmeyecek.
