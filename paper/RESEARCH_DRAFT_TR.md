# StudentContextNLP v0.1/v0.2 — Gerçek Araştırma Kaydı

**Sabit proje başlığı:** Öğrenci Açıklamalarının Soru Bağlamına Duyarlı Anlamsal Değerlendirilmesi: Türkçe Veri Uyarlaması ve Diller Arası Karşılaştırmalı Analiz.

**Yarışma hedefi:** TEKNOFEST 2242 Eğitim kategorisi, gelecek çağrı değerlendirmesine hazırlık. Bu belge nihai yarışma raporu değildir.

## Araştırma soruları

1. Soru metni eklenmesi, görülmemiş soru kümeleri üzerinde dört sınıflı Macro-F1'i değiştiriyor mu?
2. v0.2'de İngilizceden Türkçeye aktarım, öğrenci açıklamasının anlamını ve özgün hatalı yanıt/etiket niteliğini hangi sıklıkla koruyor? İki dilde soru bağlamı ablasyonu nasıl farklılaşıyor?

**Birincil ön kayıtlı deney:** Δ = Macro-F1(B2, Test-UQ) − Macro-F1(B1, Test-UQ). H0: Δ=0; H1: Δ≠0. Bir eğitim müdahalesinin nedensel etkisi değildir.

## Modeller

| ID | Girdi | Temsil / öğrenici |
|---|---|---|
| B0 | Metin özelliği yok | Majority class |
| B1 | Yalnız öğrenci açıklaması | Kelime + karakter TF-IDF; Logistic Regression |
| B2 | Açıklama ve soru birlikte | Aynı TF-IDF tasarımı; Logistic Regression |
| B3 | Yalnız soru | Aynı TF-IDF tasarımı; Logistic Regression |
| S1 | Yalnız açıklama | Yerel dondurulmuş MiniLM + Logistic Regression |
| S2 | Açıklama + soru | Yerel dondurulmuş MiniLM + Logistic Regression |

Sabit veri: SciEntsBank (İngilizce), 4 türetilmiş sınıf: Correct, Incomplete, Contradictory, Other. Yalnız eğitim verisinde soru gruplu validation ve C∈{0.1,1,10}; birincil Test-UQ; ikincil Test-UA ve Test-UD. Referans açıklama hiçbir ana sınıflandırıcının girdisi değildir.

## P0 — Gerçek veri incelemesi

**Kaynak:** Kullanıcının 10 Ekim 2026 tarihli Windows çıktıları; ham veri, SHA-256 değerleri, eğitim artefaktları yalnız yerel makinede tutuluyor. GitHub bu veri dosyalarını kendi başına yeniden çalıştırmadı.

- Dört Parquet dosyasının SHA-256 değerleri indirilen dosya manifestiyle kullanıcının yerel Python kontrolünde uyuştu.
- 10.804 satır, tüm bölümlerde 195 benzersiz normalize soru, resmi dağılımlarla eşleşen beşli sınıf sayıları.
- **P0 status: PASS_WITH_WARNINGS, fatal=0.** Train: altısı da dört sınıfa aktarıldığında süren 6 çelişkili üçlü / 15 satır. Test-UD: 1 çelişkili üçlü / 6 satır. Test-UA: train ile 24 ortak normalize üçlü.
- **Test-UQ train ortak soru=0, ortak üçlü=0;** 15 soru kümesi ve 733 öğrenci açıklaması. Test-UQ içinde 30 ilave tekrar kaydı.
- Araştırmacı yerelde `reports/P0_DECISION.md` yazıp uyarıları kaydetti; ana deneyde hiçbir etiket değiştirilmedi. Daha sonra etiket çatışması / yinelenen satır duyarlılık analizi planlanmıştır.
- Ayrıntılar: [P0 gerçek veri denetimi](P0_REAL_DATA_AUDIT_2026-10-10.md).

## P1 — Gerçek SciEntsBank Test-UQ sonuçları (10 Ekim 2026)

**Kanıt türü:** Kullanıcı, gerçek yerel `train_lexical.py` çıktısını aktardı; `results/lexical/baseline_results.json`, `selection_before_test.json` ve tahmin dosyaları GitHub'a yüklenmedi. Dolayısıyla sayılar *kullanıcının yerel deney raporudur*, GitHub CI'nin doğruladığı bilimsel skorlar değildir.

| Model | Test-UQ Macro-F1 |
|---|---:|
| B0 — Çoğunluk sınıfı | 0.1455512572533849 |
| B1 — Açıklama | 0.2950231314934188 |
| B2 — Açıklama+soru | 0.2405991832538969 |
| B3 — Soru | 0.17017237841165606 |

- **Ön kayıtlı Δ(B2−B1): −0.0544239482395219** (−5,44 Macro-F1 yüzde puanı).
- **%95 tanımlayıcı, eşleştirilmiş soru-kümesi bootstrap yüzdelik aralığı:** [−0.10254558393043693, −0.006910099256588127]; **15 soru kümesi**, **1.000** bootstrap yinelemesi.
- **Yorum:** Bu *özel TF-IDF + LR temsilinde* soru metninin eklenmesi, görülmemiş sorularda performansı düşürdü. Bu, soru bağlamının genel olarak faydasız olduğunu veya başka modellerde de aynı sonucun alınacağını kanıtlamaz. B3 düşüklüğü, sorunun tek başına yeterli bir kestirim girdisi olmadığını bu deneyde destekler.
- **Sınırlılıklar:** Sadece 15 bağımsız soru; 30 Test-UQ tekrar kaydı; train etiket çelişkileri; Other heterojen sınıfı; sınıf dengesizlikleri. Tek bootstrap yöntemi ve bu küçük soru sayısı, güçlü genelleme/istatistiksel kesinlik iddiasına yetmez.
- **Araştırmanın devamı:** Per-class F1/karışıklık matrisi, tekrar/çelişki duyarlılık analizi, validasyon skorları, CPU maliyeti. Bu analizlerde resmi Test-UQ'ya göre yeniden hiperparametre seçimi **yapılmayacak**.

## P2 — Türkçe veri uyarlaması: BEKLENİYOR

Tam 10.804 satır için yerel Argos EN→TR aktarımı hedefleniyor. Çeviriler `UNVERIFIED_MACHINE_TRANSLATION`, aktarılan etiketler `UNVERIFIED_TRANSFER` olarak kalacak. İnsan doğrulaması olmadan bunlar Türkiye'deki öğrenci cevapları veya Türkçe altın standart olarak tanıtılamaz.

İnsan değerlendirmesi, yalnız metin çevrimi değil, bilimsel yanlışlığın/olumsuzlamanın ve etiket anlamının korunmasını sınayacak. Türkçe dört-sınıf deneyleri, çeviri kalite kapısından sonra *ayrı raporlanacak*.

## Araştırma etiği ve yeniden üretilebilirlik

- Sentetik smoke sonuçları akademik tabloya alınmaz. API anahtarı, LLM API, bulut model inference, RAG, agent, büyük dil modeli fine-tuning yoktur.
- Ham metinler, kaynak Parquet dosyaları, çeviri cache'leri, model ağırlıkları ve öğrenci satırı düzeyindeki tahminler GitHub'a konmaz; GitHub'da yalnız kaynak kod, toplu istatistik ve araştırma kayıtları.
- SciEntsBank kaynak verisi beş etiketlidir; dört-sınıf yeniden eşleştirmesi özgün etiketi yok etmez. Veri lisansı ve çeviri model lisansı ayrı değerlendirilmelidir.

## Kaynaklar

1. Dzikovska vd. (2013), SemEval Task 7 — https://aclanthology.org/S13-2045/
2. Reimers & Gurevych (2019), Sentence-BERT — https://aclanthology.org/D19-1410/
3. SciEntsBank dataset — https://huggingface.co/datasets/nkazi/SciEntsBank
4. TEKNOFEST 2242 — https://www.teknofest.org/tr/yarismalar/universite-ogrencileri-arastirma-proje-yarismalari/

**Sonraki teknik görev:** Yerel Argos EN→TR modelinin gerçek kurulumu ve iki satır/bölüm şeklinde yazılım smoke kontrolü; sonrasında tam 10.804 aday çeviri.
