# StudentContextNLP v0.2 — SciEntsBank-TR Yerel Uyarlama Motoru

**Sabit akademik başlık:** Öğrenci Açıklamalarının Soru Bağlamına Duyarlı Anlamsal Değerlendirilmesi: Türkçe Veri Uyarlaması ve Diller Arası Karşılaştırmalı Analiz.

## Kapsam / güven sınırı

- İngilizce v0.1 B0–S2 koduna ve Test-UQ protokolüne **dokunulmaz**. v0.2 ayrı geliştirme dalında geliştirilir.
- Dört resmi SciEntsBank bölümü (**train**, **test_ua**, **test_uq**, **test_ud**), toplam 10.804 kayıt, **tamamı** otomatik çevrilebilir. Bu sayılar kaynağın bildirdiği hedef büyüklüktür; gerçek P0 yeniden hesaplanmadan kabul edilmez.
- İngilizce `question`, `reference_answer` ve `student_answer` metinleri Türkçeye çevrilir. Özgün öğrenci yanılgısı düzeltilmez; yanlışlığın korunduğu otomatik olarak varsayılmaz.
- Orijinal `label` değişmeden **aday etiket** olarak aktarılır, `label_status=UNVERIFIED_TRANSFER` kalır. **Daha sonra insan incelemesi** gerekiyor. Bu çıktı Türkiye'deki öğrencilerden toplanmış Türkçe veri değildir.
- Makine çeviri sistemi **Argos Translate**, doğrudan `en→tr` yerel `.argosmodel` paketi kullanır. İnference sırasında ağ yok, API anahtarı/LLM API yok. Paket kaynağı, sürüm ve SHA-256 korunur.
- Otomatik uyarılar (olumsuzlama, sayı, boş çıktı, uzunluk, değişmeyen metin) *inceleme bayrağıdır*; gerçek anlam/etiket doğruluğu kanıtı **değildir**.
- Eğitim/test gruplaması, her dilde aynı kaynak bölümü ve normalize özgün soru kimliği üzerinden yapılır. `test_uq` eğitimde kullanılmaz. Etiket/girdi sızıntısı için ayrıca test gerekir.
- Kaynağın CC BY 4.0 lisansına atıf ve değişiklik bildirimi esastır. Argos model lisansı ayrıca doğrulanır. Türetilmiş öğrenci cevapları GitHub'a eklenmez.

## 1 — Windows kurulumu (ilk kez)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-translation.txt
.\.venv\Scripts\python.exe -m pytest -q
```

## 2 — İngilizce P0 denetimi (zorunlu)

```powershell
.\.venv\Scripts\python.exe download_data.py --data-dir data/raw
.\.venv\Scripts\python.exe audit_dataset.py --data-dir data/raw --output-dir reports
Get-Content reports/P0_audit.md
```

Kaynak dosyalar 4 adet tam Parquet olmalı. P0 fatal veya incelenmemiş uyarıları varken devam etme.

## 3 — Yerel çeviri modeli (bir kez)

```powershell
.\.venv\Scripts\python.exe prepare_translation_model.py --download-public
```

Bu seçenek halka açık `.argosmodel` dosyasını ve paket dizinini **yalnız bu aşamada** indirir; LLM API çağrısı yapmaz. Dosyayı önceden indirdiysen:

```powershell
.\.venv\Scripts\python.exe prepare_translation_model.py --package-path C:\Modeller\translate-en_tr.argosmodel
```

Manifest: `models/argos_en_tr_manifest.json` (paket SHA-256, dil çifti, sürüm). İnternet erişimi kapatıldıktan sonra çeviri devam edebilmelidir. Çeviri paketinin lisansını kullanım öncesinde ayrıca kontrol et.

## 4 — Ön deneme, ardından **tüm veri kümesi**

Önce ayrı klasörde birkaç satırla akış kontrolü:

```powershell
.\.venv\Scripts\python.exe translate_dataset_tr.py --data-dir data/raw --output-dir data/tr_smoke --limit-per-split 2
```

Tüm dört splitin tamamını çevirmek için (10.804 kayıt **hedefi**):

```powershell
.\.venv\Scripts\python.exe translate_dataset_tr.py --data-dir data/raw --output-dir data/tr_v0_2
```

Uyarılar varsa ancak yazılı P0 incelemesi sonrası `--allow-audit-warnings` kullanılabilir; fatal durum asla aşılamaz. Her yeni model/ham veri sürümünde yeni output klasörü kullan.

Çıktı: `data/tr_v0_2/{train,test-ua,test-uq,test-ud}.csv`, `translation_manifest.json`, `_cache/translations.jsonl`. Cache kesintiden sonra devamı destekler. Çıktıların `UNVERIFIED_MACHINE_TRANSLATION` statüsünü asla değiştirme.

## 5 — Tam veri içinden doğrulama örneklemi

```powershell
.\.venv\Scripts\python.exe sample_translation_review.py --data-dir data/tr_v0_2 --out reports/tr_review --n 240
```

İlk olarak **etiket körü Aşama 1** dosyalarını oluştur:

```powershell
.\\.venv\\Scripts\\python.exe prepare_blinded_reviews.py --review-dir reports/tr_review
```

Değerlendirici A ve B, yalnız `reports/tr_review/blind_stage1/review_A_blind.csv` ve `review_B_blind.csv` dosyalarını ayrı ayrı doldurmalıdır (`meaning_preserved`, `error_preserved`, `notes`). Bu formlar özgün `class4` etiketini ve otomatik `quality_flags` alanını içermez. **Orijinal `review_A.csv` ve `review_B.csv` dosyaları silinmez ve otomatik doldurulmaz.**

Her iki değerlendiricinin ilk aşama yorumları tamamlandıktan sonra orijinal etiketler gösterilerek Aşama 2'de `label_still_applicable` ve `correction_needed` incelenir. Bağımsız iki aşama kaydı doğrulanmış biçimde birleştirilmeden ve tüm alanlar doldurulmadan aşağıdaki hesaplama çalıştırılmamalıdır.

**Bağlayıcı insan değerlendirme protokolü:** [TR_REVIEW_PROTOCOL_T3.md](TR_REVIEW_PROTOCOL_T3.md).

```powershell
.\.venv\Scripts\python.exe evaluate_translation_reviews.py --review-dir reports/tr_review
```

`review_agreement.json`, ikili değerlendirici uyumunu gösterir; tam veri kümesinin onaylandığı anlamına **gelmez**. İhtilafların karara bağlanması ve kabul eşiği ayrıca kayıt altına alınır.

## 6 — Sonraki deney kapısı (henüz PASS değil)

- İngilizce kaynakta P0 ve B0–B3 Test-UQ gerçek sonuçları dondurulur.
- Türkçe aktarılan etiketlerin güvenilirliği, insan incelemesiyle sınanır; kalite çok düşükse Türkçe benchmark **HOLD**.
- Türkçe ayrı TF-IDF kelime/karakter n-gram baselines; aynı kaynak soru grupları üzerinden karşılaştırma. İngilizce encoder yalnız İngilizce, uygun yerel çokdilli encoder Türkçe için ileride değerlendirilir.
- `Δ_EN = F1(B2)-F1(B1)` ile `Δ_TR` karşılaştırılabilir; bunlar çeviri ve veri farklılıklarının birleşik etkisidir, dilin kanıtlanmış nedensel etkisi değildir.
- Öğretici etki, gerçek Türkçe öğrencilerde genelleme, veri kümesinin uzman-altın-standart kalitesi veya yarışma başarısı **iddia edilmez**.

## Gerçek Windows ilerlemesi (10–11 Ekim 2026)

- P0 İngilizce kaynak: **PASS_WITH_WARNINGS**, uyarılar araştırmacı tarafından koşullu olarak kabul edildi; ham veri/etiketler değişmedi.
- P1 B0–B3 gerçek Test-UQ Macro-F1: B1=0.295023, B2=0.240599, Δ=−0.054424; ayrıntı [araştırma kaydında](../paper/RESEARCH_DRAFT_TR.md).
- T1 yerel Argos en→tr model SHA-256 kaydı ve 8/8 smoke kontrolü: **PASS**.
- T2 dört split 10.804/10.804 aday çeviri, özgün id ve etiketler korunuyor: **PASS**; 2.823 aday kayıtta sezgisel kalite bayrakları var (kanıtlanmış hata sayısı değil).
- T3.0 240 örnek, 2 boş inceleme formu; her splitten 60, her dört sınıftan 60, 73 otomatik uyarı taşıyan örnek: **PASS**. İnsan kalite incelemesi bekliyor.

## Kabul kapıları

| Kapı | PASS koşulu | Durum |
|---|---|---|
| T0 | v0.1 CI bozulmadı, sentetik v0.2 testleri geçti | Windows 28/28 PASS; yeni kör inceleme testleri ayrıca CI'ye eklendi |
| T1 | Model kurulumu, doğrudan EN→TR ve SHA-256 kanıtı | PASS (yerel Windows çıktısı) |
| T2 | 4 gerçek splitin tamamının çevrimi, manifest ve 1:1 row count | PASS (10.804/10.804, yerel Windows çıktısı) |
| T3 | 240 örnekte 2 bağımsız değerlendirici, kappa ve hata analizi | Örneklem PASS, kör insan incelemesi bekliyor |
| T4 | Etiketi korunan örneklerle bilimsel Türkçe baseline ve diller arası analizi | Bekliyor |

**TEKNOFEST 2242:** Bu yalnızca yeni yarışma çağrısına uygun geliştirilecek araştırma modülüdür, mevcut bir yarışma kabulü veya bilimsel sonuç değildir.
