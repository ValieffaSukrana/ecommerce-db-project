# Satış hesabatı (avtomatik yaradılıb)

## Əsas göstəricilər (KPI)

| Göstərici | Dəyər |
|---|---|
| Çatdırılmış sifariş sayı | 5,662.0 |
| Ümumi gəlir | 2,975,733.14 AZN |
| Orta çek (AOV) | 525.56 AZN |
| Aktiv müştəri | 1,775.0 |
| Təkrar alış edən müştərilərin payı | 74.2% |
| Ləğv + geri qaytarma nisbəti | 15.5% |
| Ən yüksək gəlirli ay | 2025-12 (232,330 AZN) |

## Kateqoriyalar

| category_name    |   orders_count |   units_sold |          revenue |   revenue_share_pct |
|:-----------------|---------------:|-------------:|-----------------:|--------------------:|
| Elektronika      |           1155 |         2321 |      1.68094e+06 |               56.49 |
| Məişət texnikası |            650 |         1267 | 500284           |               16.81 |
| Ayaqqabı         |           1094 |         2170 | 241166           |                8.1  |
| İdman            |           1237 |         2516 | 148425           |                4.99 |
| Ev və bağ        |           1017 |         2029 | 125219           |                4.21 |
| Oyuncaq          |           1423 |         2963 | 100369           |                3.37 |
| Geyim            |            649 |         1263 |  59588.9         |                2    |
| Kitab            |           1710 |         3617 |  54226.8         |                1.82 |
| Kosmetika        |            951 |         1923 |  41205           |                1.38 |
| Ərzaq            |           1018 |         2095 |  24311.4         |                0.82 |

## Müştəri seqmentləri

| segment      |   customers |   avg_orders |   avg_spent |    total_revenue |   revenue_share_pct |
|:-------------|------------:|-------------:|------------:|-----------------:|--------------------:|
| VIP          |         441 |         6.06 |     3556.64 |      1.56848e+06 |               52.71 |
| Risk altında |         355 |         3.03 |     2506.62 | 889851           |               29.9  |
| Sadiq        |         333 |         2.65 |      870.57 | 289899           |                9.74 |
| Passiv       |         533 |         1.73 |      320.73 | 170950           |                5.74 |
| Yeni / aktiv |         113 |         1    |      500.48 |  56554.5         |                1.9  |

## Ödəniş üsulları

| payment_method   |   total_payments |   completed |   failed |   refunded |   success_rate_pct |   avg_amount |
|:-----------------|-----------------:|------------:|---------:|-----------:|-------------------:|-------------:|
| card             |             3841 |        3249 |      388 |        204 |              84.59 |       523.15 |
| cash_on_delivery |             1761 |        1474 |      204 |         83 |              83.7  |       501.46 |
| installment      |             1088 |         945 |      100 |         43 |              86.86 |       574.94 |
| e_wallet         |              644 |         543 |       64 |         37 |              84.32 |       553.63 |
| bank_transfer    |              640 |         528 |       75 |         37 |              82.5  |       561.96 |
| unknown          |               20 |          17 |        2 |          1 |              85    |       343.6  |

## Sorğuların icra müddəti

| query                            | description                                                                                                          |   rows |   time_ms |
|:---------------------------------|:---------------------------------------------------------------------------------------------------------------------|-------:|----------:|
| q01_category_revenue             | [JOIN + GROUP BY] Kateqoriyalar üzrə satış həcmi, gəlir və gəlirdəki pay                                             |     10 |      37.5 |
| q02_monthly_revenue              | [GROUP BY + tarix funksiyaları] Aylıq gəlir, sifariş sayı və orta çek                                                |     24 |       4.7 |
| q03_loyal_customers_having       | [JOIN + GROUP BY + HAVING] 8-dən çox çatdırılmış sifarişi və 3000 AZN-dən çox xərci olan müştərilər                  |     70 |       6.7 |
| q04_city_payment_having          | [JOIN + GROUP BY + HAVING] Şəhər və ödəniş üsulu üzrə — 50-dən çox uğurlu ödəniş olan kombinasiyalar                 |     32 |       6.9 |
| q05_top_customers_cte            | [CTE] Müştəri seqmentasiyası (RFM-ə bənzər): son alış, tezlik və pul dəyəri                                          |      5 |       7.7 |
| q06_products_above_category_avg  | [Korrelyasiyalı Subquery] Öz kateqoriyasının orta qiymətindən baha olan və ən azı 20 dəfə satılan məhsullar          |     20 |       8.5 |
| q07_customers_above_avg_subquery | [Subquery IN / skalyar] Orta müştəri xərcindən 3 dəfə çox xərcləyən müştərilərin şəhər üzrə sayı                     |     10 |       6.7 |
| q08_yoy_growth_cte               | [CTE + LAG] Kateqoriyalar üzrə illik gəlir və illik artım (YoY) faizi                                                |     20 |      20.7 |
| q09_payment_methods              | [JOIN + GROUP BY] Ödəniş üsulları üzrə uğur, uğursuzluq və geri qaytarma göstəriciləri                               |      6 |       4.8 |
| q10_top_products_per_category    | [CTE + ROW_NUMBER] Hər kateqoriyada gəlirə görə ilk 3 məhsul                                                         |     30 |      23.9 |
| q11_cancellation_by_category     | [LEFT JOIN + GROUP BY + HAVING + Subquery] Ləğv/geri qaytarma nisbəti ümumi orta nisbətdən yüksək olan kateqoriyalar |      3 |      26.5 |
| q12_age_group_analysis           | [CTE + CASE] Yaş qrupları və cins üzrə alış davranışı                                                                |     10 |      14.2 |
