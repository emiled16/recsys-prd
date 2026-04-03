from __future__ import annotations


PRODUCT_FIELDS = [
    "article_id",
    "product_code",
    "prod_name",
    "product_type_name",
    "product_group_name",
    "graphical_appearance_name",
    "colour_group_name",
    "perceived_colour_value_name",
    "perceived_colour_master_name",
    "department_name",
    "index_name",
    "index_group_name",
    "section_name",
    "garment_group_name",
    "detail_desc",
]

CUSTOMER_FIELDS = [
    "customer_id",
    "fn_flag",
    "active_flag",
    "club_member_status",
    "fashion_news_frequency",
    "age",
    "postal_code",
]

TRANSACTION_FIELDS = [
    "event_id",
    "event_time",
    "customer_id",
    "article_id",
    "price",
    "sales_channel_id",
]

IMAGE_FIELDS = [
    "article_id",
    "image_path",
    "image_kind",
]

REQUIRED_PRODUCT_FIELDS = ["article_id", "prod_name", "product_group_name"]
REQUIRED_CUSTOMER_FIELDS = ["customer_id"]
REQUIRED_TRANSACTION_FIELDS = ["event_id", "event_time", "customer_id", "article_id", "price"]
