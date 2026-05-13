# Field Normalization / 运价字段归一化

## Canonical fields

- `route_region`: 航线/区域，如 红海、中东、印巴、东南亚、美线、欧地、非洲。
- `pol`: 起运港 / POL。
- `pod`: 目的港 / POD / 国家 / 区域。
- `carrier`: 船司 / service provider。
- `service`: 直航/中转/服务名。
- `currency`: USD/CNY/etc.
- `cost_20gp`, `cost_40gp`, `cost_40hq`: internal cost prices.
- `sell_20gp`, `sell_40gp`, `sell_40hq`: customer-facing sell prices.
- `unknown_price_fields`: prices whose type is unclear.
- `cutoff`: 截关/CLS。
- `etd`: 开船/ETD。
- `transit_time`: 航程。
- `free_time`: 免柜期/免箱期。
- `validity`: 有效期。
- `remarks`: 备注、限制、附加费。
- `source_ref`: file + sheet/row or paragraph.
- `review_flags`: ambiguity or risk notes.

## Header aliases

### POL
起运港, 装港, POL, Port of Loading, Loading Port, 起运地

### POD
目的港, 卸港, POD, Port of Discharge, Destination, 目的地, 国家, 区域

### Carrier / service
船司, 航司, carrier, carrier/service, 服务, 航线, route, route_region

### Box types
20GP, 20', 20FT, 小柜; 40GP, 40', 大柜; 40HQ, HQ, 高柜

### Cost price indicators
成本, 成本价, 底价, 拿价, 采购价, cost, net, buy rate

### Sell price indicators
卖价, 报价, 对外价, 销售价, sell, selling, offer, quote

### Schedule/service indicators
截关, CLS, cut off, closing; 开船, ETD, sailing; 航程, transit, T/T; 免柜, free time; 有效期, validity

## Classification rules

- If a price column header contains both box type and cost indicator, classify as cost for that box.
- If it contains both box type and sell indicator, classify as sell for that box.
- If a nearby merged title says 成本价/卖价, apply cautiously to following price columns and mark source context.
- If only `20/40/40HQ` appears without price-type context, classify as unknown.
- Do not infer sell price from cost unless a quotation strategy is explicitly provided.
