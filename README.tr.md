![Aurelia Pension](docs/assets/banner.svg)

# Aurelia Pension — BES Fon Analitiği

**Murat Miraç Gedik** tarafından hazırlanan BES fon performansı, portföy riski ve
katkı payı senaryosu projesi.

## Uygulamayı aç

`artifacts/Aurelia_Pension_BES_Dashboard.html` dosyasını modern bir masaüstü
tarayıcısında açın. İnternet veya kurulum gerekmez. Telefonun dosya önizlemesi
JavaScript çalıştırmıyorsa bilgisayarda tarayıcı kullanın.

Beş ekran bulunur:

1. **Genel görünüm:** 30 fon, 5 kategori ve ortak tarih aralığı.
2. **Fon karşılaştırma:** kategori ve dönem seçimi, fon detayı, CSV indirme.
3. **Portföy & risk:** üç örnek dağılım, aylık dengeleme, kayıp ve stres analizi.
4. **Birikim senaryosu:** katkı, süre, getiri, enflasyon ve yıllık katkı artışı.
5. **Veri & yöntem:** kaynak sınıfı, hesaplama tanımları ve kalite kontrolleri.

Veriler **tamamen sentetiktir**. Gerçek BES fonu, müşteri veya piyasa performansı
sunulmaz. Fon karşılaştırmaları aynı kategori ve aynı dönem içinde yapılır.

## Yeniden üret

```bash
python -m pip install -e .
python -m aurelia_pension build
python -m unittest discover -s tests -v
node tests/test_engine.cjs
```

Yerel sunucu: `python -m aurelia_pension serve`.

## Mesleki kapsam

Proje; istatistiksel risk ölçümü, finansal veri kalitesi, SQL veri modeli,
tekrarlanabilir analiz ve karar destek uygulaması geliştirmeyi gösterir.
Fon sıralamasına ek olarak getiri–risk ilişkisini, portföy maliyetini ve
birikimin satın alma gücünü görünür kılar.

Devlet katkısı, hak ediş, stopaj ve sözleşmeye özgü kesintiler modellenmez.
EGM'nin resmî brüt getiri değerlendirmesi yeniden uygulanmış değildir.
Fon giderlerinin NAV'a yansıdığı varsayılır. Örnek portföy adları kişisel
risk profilini ifade etmez.

32 Python testi ve 543 sayısal Python/JavaScript karşılaştırması tamamlanmıştır.
Görsel tarayıcı kontrolü bu ortamın yerel dosya açma kuralı nedeniyle
tamamlanamamıştır. Ayrıntılar: [Doğrulama](docs/VALIDATION.md).

İngilizce teknik açıklama: [README.md](README.md).

## Veri doğrulama ve güvenilir kullanım

Rapor üretmeden mevcut CSV'leri kontrol edin. Bu komut dosya oluşturmaz veya değiştirmez:

```bash
python -m aurelia_pension validate
python -m aurelia_pension validate --data-dir /veri/klasoru --json
```

Başarılı doğrulama çıkış kodu `0`, hatalı veya eksik veri çıkış kodu `2` üretir.
JSON çıktısı veri sınıfını, tarih aralığını, fon/gözlem sayısını ve kontrolleri içerir.
`--json` doğrulama komutuna özeldir.

Kendi verinizi kullanırken:

```bash
python -m aurelia_pension serve --data-dir /veri/klasoru
```

Bu komut mevcut rapor olsa bile belirtilen veriden yeniden üretim yapar. Veri geçersizse
sunucu başlamaz. Sadece `serve` kullanımı mevcut raporu açar; rapor yoksa demo üretir.
Fon kimlikleri metin olarak korunur; `0001` gibi kodların başındaki sıfırlar kaybolmaz.

## SQL ile inceleme

[SQL örnekleri](sql/example_queries.sql); kategori içindeki lider fonları, portföy
risklerini ve fon bazında gözlem sayısını sorgular. Veritabanındaki oranlar ondalıktır:
`0.12`, yüzde 12 anlamına gelir. Maksimum düşüş negatif, VaR/ES kayıp değerleri pozitiftir.

## İnceleme sırası

Önce aynı kategorideki fonları 1 ve 3 yıllık dönemlerde karşılaştırın. Ardından üç model
portföyün kayıp ve stres sonuçlarına bakın. Birikim ekranında enflasyonu değiştirerek
nominal tutarla satın alma gücünün nasıl ayrıldığını inceleyin. Son olarak veri ve yöntem
ekranındaki varsayımları okuyun. GitHub HTML dosyasını uygulama olarak çalıştırmaz;
ZIP'i indirip çıkartarak HTML'yi tarayıcıda açın veya yerel sunucuyu kullanın.

[Mimari şema ve ayrıntılı kılavuz](README.md) · [Değişiklikler](CHANGELOG.md)
