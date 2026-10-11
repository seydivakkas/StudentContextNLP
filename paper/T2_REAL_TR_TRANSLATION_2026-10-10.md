# T1/T2 — 10.804 SciEntsBank EN→TR Aday Çevirisi (Gerçek Windows Çalıştırması)

> **Kaynak statüsü:** Araştırmacının 10 Ekim 2026 Windows PowerShell çıktılarından aktarılan agregat bilgiler. Orijinal Parquet dosyaları, kişiye ait yerel çeviri CSV'leri ve yeniden üretim manifestleri **GitHub'da tutulmaz**. Bu belge yerel işlemin aktarılmış yürütme kaydıdır, bağımsız bir çeviri kalitesi denetimi değildir.

## Model ve işlem zinciri

- Dil çifti: doğrudan **en→tr**, Argos Translate, çevrimdışı yerel çıkarım.
- Araştırmacının bilgisayarında indirilen `.argosmodel` paketi SHA-256: `2d553a00880a0c21dea5b1c375535659e6bf18c9bf2ce9847c2a2fd2ff50316a`.
- Model/versiyon ve kaynak dosyası SHA bilgileri: yalnız yerel `models/argos_en_tr_manifest.json` ve `data/tr_v0_2/translation_manifest.json`. Model dosyasının resmî lisans kimliği bu raporla bağımsız doğrulanmış değildir.
- 8 kayıtlık ilk smoke: her splitten 2 kayıt, **8/8** üretildi. `PARTIAL_SMOKE` ve `UNVERIFIED_MACHINE_TRANSLATION` olarak işaretli.
- Tam çalıştırma: `translate_dataset_tr.py --data-dir data/raw --output-dir data/tr_v0_2 --allow-audit-warnings`, P0'daki iki uyarı daha önce araştırmacı tarafından şartlı kabul edildi.

## Tam çeviri aday kapsamı

| Veri bölümü | Kaynak satır | Üretilen aday satır | Sezgisel kalite bayrağı taşıyan satır |
|---|---:|---:|---:|
| train | 4,969 | 4,969 | 1,315 |
| test_ua | 540 | 540 | 153 |
| test_uq | 733 | 733 | 258 |
| test_ud | 4,562 | 4,562 | 1,097 |
| **Toplam** | **10,804** | **10,804** | **2,823 (~%26.1)** |

- **Kapsam:** dört splitte %100, `FULL_CANDIDATE`.
- **Yazılım bütünlüğü:** kullanıcının bağımsız Python denetiminde tüm splitlerde satır sırası, `id` ve `label` tam eşleşti: **4/4 PASS**.
- **Etiket statüsü:** tüm satırlarda `label_status=UNVERIFIED_TRANSFER` ve `translation_scope=FULL_CANDIDATE`; manifest `projected_labels_are_gold=false`, `validation_state=UNVERIFIED_MACHINE_TRANSLATION`.
- **Bayrak tanımı:** otomatik olumsuzlama, sayısal değer, uzunluk, değişmeden kalmış metin vb. yüzeysel kontroller. **2,823 işaretli satırın yanlış olduğu kanıtlanmadı; işaretlenmeyen satırların doğruluğu da doğrulanmadı.** Her satır soru, referans cevap ve öğrenci yanıtını birlikte içerir; bayrak öğrenci yanıttan başka bir alana da ait olabilir.
- Çeviri motoru `Language en package default expects mwt, which has been added` bilgisini verdi; tamamlanan manifest ve satır doğrulama ile birlikte yorumlandığında bu satır tek başına çalıştırma hatası göstermedi.

## Bilimsel durum ve sonraki kapı

**T1 = PASS (model kurulum + SHA manifest bildirimi), T2 = PASS (tam *aday* satır üretimi + korunum denetimi). T3 = HOLD / insan doğrulaması henüz başlamadı.**

- Bilimsel hata/yanılgının otomatik çeviri sırasında aynen korunduğu **kanıtlanmış değil**.
- Türkçe aday etiketler doğal Türkçe öğrenci yanıtlarından toplanmış bir gold set değildir.
- 240 örneklik sınıf/split kapsamlı bağımsız inceleme, iki değerlendiricinin ayrı formları, etikete kör veya ankrajı azaltan inceleme yönergesi, anlaşmazlıkların çözümü ve hata taksonomisi gerekir.
- Değerlendirme örneğinin sınıf/split tabakalandırılması, sonuçların veri kümesinin rastgele olasılık örneklemi için güven aralığı gibi sunulmasını **haklı çıkarmaz**.
- Türkçe B1/B2 gerçek test sonucu T3 kalitesi kabul edilene kadar ertelenir.
- Gizlilik: Ham/çeviri metinleri, gözden geçirme CSV'leri ve model ağırlıkları GitHub'a işlenmez.

Bu belgedeki aggregate veriler kullanıcının yerel terminal çıktısıyla uyumludur; gerçek model ağırlıkları ve bütün SHA manifestleri bu ortamda yeniden hesaplanmamıştır.
