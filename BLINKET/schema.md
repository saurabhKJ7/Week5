erDiagram
    users ||--o{ search_query_logs : "has"
    search_query_logs ||--o{ agent_logs : "has"
    
    products }o--|| categories : "belongs to"
    products }o--|| brands : "belongs to"
    products }o--|{ product_prices : "has"
    products }o--|{ product_availability : "has"
    products }o--o{ product_platform_mapping : "maps to"
    
    platforms ||--o{ product_prices : "has"
    platforms ||--o{ product_availability : "has"
    platforms ||--o{ product_platform_mapping : "maps to"

    currencies ||--o{ product_prices : "uses"

    promotions }o--|{ promotion_product_link : "links to"
    products }o--|{ promotion_product_link : "links from"

    locations ||--|{ platforms : "operates in"
    taxes ||--|{ products : "applies to"
    uom ||--|{ products : "uses" 