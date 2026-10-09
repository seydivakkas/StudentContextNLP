# StudentContextNLP v0.1 — Yerel NLP Araştırma Deposu

**Türkçe akademik başlık:** Öğrenci Açıklamalarındaki Anlamsal ve Bağlamsal Tutarsızlıkların Sınıflandırılmasında Soru Bağlamının Etkisi

**İngilizce:** The Effect of Question Context on Classifying Semantic Inconsistencies in Student Explanations

## Sabit kapsam

- Fen konularından gerçek İngilizce öğrencilerin kısa açıklamaları; **matematik yanlış kavrama sınıflandırması değil**.
- SciEntsBank beşli etiketlerinin dört sınıfa indirgenmiş halleri: Correct, Incomplete, Contradictory, Other (`irrelevant` + `non_domain`).
- Ana soru: Yalnız açıklamaya **soru metni** eklendiğinde, resmî **Test-UQ** (eğitimde görülmeyen sorular) üzerinde Macro-F1 nasıl değişiyor?
- Birincil karşılaştırma **B2−B1**; ikincil karşılaştırma **S2−S1**. Aynı veri, aynı LR parametre arama ızgarası, yalnızca giriş temsili farklı.
- `reference_answer` veri denetimi için tutulur ancak modele girdi yapılmaz. `label` hedef dışında kullanılmaz.
- Model seçimi yalnız **train içindeki question-grouped validation** üzerinde yapılır. Test-UA/UQ/UD hiçbiri hiperparametre seçimi için kullanılmaz.
- Soru kümesi bootstrap güven aralıkları tanımlayıcıdır; eğitim müdahalesinin nedensel etkisini göstermez.
- **API key/LLM API/bulut inference: kesinlikle yok.** Büyük dil modeli fine-tuning, RAG, agent, veritabanı yok. İlk eğitim CPU.
- Türkçe veriler ve çokdilli encoder **gelecek araştırma sürümü v0.2**. Bu kaynak kodda henüz gerçek Türkçe etiketli sonuç yoktur.

## Mevcut durum ve dürüst sonuç politikası

**Kod ve sentetik otomatik testler gerçekleştirilebilir.** SciEntsBank ham dosyaları henüz bu depoya alınmadı, gerçek P0 denetimi ve gerçek veri metrikleri **yapılmadı**.

`data/demo` altında üretilen bütün kayıtlar uydurmadır. Sentetik denemelerin F1 veya grafiklerini makale, sonuç tablosu ya da gerçek öğrenci performansı olarak kullanma.

## Kurulum — Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
python -m pytest -q
python -m scripts.run_demo
```

**Bu adımlarda internet yalnız paket kurulumunda gerekir; veri veya model indirme gerekmiyor.** Testler hazır sentetik metinlerle çalışır. Demo sonuçları `results/demo/` altında kalır ve GitHub'a gönderilmez.

## Gerçek veriye geçiş — yalnız kod GitHub'a yüklenip test edildikten sonra

```powershell
python download_data.py --data-dir data/raw
python audit_dataset.py --data-dir data/raw --output-dir reports
```

4 resmî Parquet dosyası: `train`, `test_ua`, `test_uq`, `test_ud`. Kaynak <https://huggingface.co/datasets/nkazi/SciEntsBank/tree/main/data>. `download_data.py` halka açık **dosyaları indirir**, key veya inference API kullanmaz. Dosyaları ayrıca tarayıcıdan manuel alabilirsin.

Denetim raporu `reports/P0_audit.md`, `reports/P0_audit.json`; kesin hatalar (fatal) çözülmeden eğitim yok. Uyarıların otomatik bastırılması yok: her uyarı incelenmeli; kabul gerekçesi kaydedildikten sonra `--allow-audit-warnings` kullanılabilir.

```powershell
python train_lexical.py --data-dir data/raw --out results/lexical
python plot_results.py --results results/lexical/baseline_results.json --output results/figures
```

Uyarı olması halinde **önce araştırmacı onayını kaydet**, sonra `train_lexical.py` komutuna `--allow-audit-warnings` ekle. Bu seçenek fatal hataları aşmaz.

## Yerel anlamsal model (opsiyonel; çevrimdışı çalışma)

Encoder bir kez **yerel diske** indirildikten sonra bütün özellik çıkarımı offline (`local_files_only=True`). Model ağırlıkları değiştirilmez, yalnızca Logistic Regression eğitilir.

```powershell
python -m pip install -r requirements-semantic.txt
python download_encoder.py --out models/local_encoder
python train_semantic.py --data-dir data/raw --model-dir models/local_encoder --out results/semantic
python compare_experiments.py --out results/combined
python plot_comparison.py
```

`download_encoder.py`, `sentence-transformers/all-MiniLM-L6-v2` herkese açık model dosyalarını tek seferlik indirir (`token=False`). **Bu bir LLM API/inference servisi değildir.** İstersen dosyaları tarayıcıdan indirip aynı klasöre yerleştirebilirsin. `train_semantic.py` model eksikse internetten otomatik indirmeye çalışmaz, hata verir. Encoder üzerinde fine-tuning yoktur.

## Model matrisi

| ID | Girdi | Temsil | Eğitilen kısım |
|---|---|---|---|
| B0 | Açıklama (özellik kullanılmaz) | Majority Class | DummyClassifier |
| B1 | Açıklama | kelime/karakter TF-IDF | Logistic Regression |
| B2 | Açıklama + soru | aynı TF-IDF | Logistic Regression |
| B3 | Yalnız soru | aynı TF-IDF | Logistic Regression |
| S1 | Açıklama | dondurulmuş 384d MiniLM | Logistic Regression |
| S2 | Açıklama + soru | iki ayrı embedding, birleştirilmiş | Logistic Regression |

`C ∈ {0.1, 1.0, 10.0}` değerleri yalnız eğitim içi validation üzerinde denenir. Dış test sonuçları yalnız model seçimleri kaydedildikten sonra çıkarılır. S1/S2 encoder sıfırdan eğitilmez.

## Çıktılar

- `reports/P0_audit.*`: benzersiz sorular, tekrar ve çelişki kontrolleri, test-soru çakışmaları
- `results/lexical/`: B0–B3 sklearn modelleri, validation seçimi, Test-UA/UQ/UD metrikleri, CSV tahminleri
- `results/semantic/`: S1–S2 LR modelleri ve offline embedding sonuçları (yerel ağırlıklar gerekir)
- `results/combined/`: model karşılaştırması; `results/figures/`: Test-UQ F1 grafiği
- `predict.py`: **yalnız güvenilir** yerel model dosyasıyla inference (joblib dosyaları güvenilmeyen kaynaktan açılmamalı)

```powershell
python predict.py --model results/lexical/B2.joblib --question "What causes evaporation?" --answer "Water changes into gas."
```

## Kabul kapıları

| Aşama | Kabul |
|---|---|
| C0 | Testler sentetik veri üzerinde çalışıyor, ücretsiz/yerel, sonuçlar SYNTHETIC etiketli |
| C1 | GitHub deposundaki CI testleri yeşil; kaynak kodu gerçekten gönderilmiş |
| P0 | Dört gerçek veri dosyası indirilmiş, şema ve etiket denetimi kaydedilmiş |
| P1 | B0–B3 resmî sabit testlerde eğitilmiş, seçim yalnız train validation'da |
| P2 | S1–S2 lokal encoder ile eğitilmiş; ek kazanç ve hatalar raporlanmış |
| P3 | Akademik yorum, sınırlılıklar, güven aralıkları ve sürüm bilgileri raporlanmış |

Bu sürüm bir **araştırma baseline aracıdır**; akademik yayın, yüksek doğruluk, tüm disiplinlere veya Türkçe veriye genelleme garantisi değildir.
