import polars as pl
import os

# === Пути ===
EXCEL_PATH = "links.xlsx"
DATASET_DIR = "datasets"

print("📂 Загружаем Excel...")
df = pl.read_excel(EXCEL_PATH)
print(f"✅ Загружено {len(df)} строк, столбцы:")
print(df.columns)

# === 1️⃣ Переименовываем split_flag ===
df = df.rename({
    "0 - не использовать\r\n1 - обучающая выборка\r\n2 - остальные": "split_flag"
})

# === 2️⃣ Переименовываем важные колонки ===
df = df.rename({
    "Номер поля": "field_number",
    "Производственное хозяйство": "farm",
    "Культура": "culture",
    "Комментарий агронома": "comment",
    "Фаза развития растения": "phase",
    "Дата создания осмотра и фотографий": "date",
    "Идентификатор фотографии": "photo_id"
})

# === 3️⃣ Оставляем только нужные поля ===
df = df.select([
    "field_number", "farm", "culture", "comment", "phase", "date", "photo_id", "split_flag"
])

# === 4️⃣ Чистим split_flag (оставляем 1 и 2) ===
df = (
    df
    .filter(pl.col("split_flag") != "IsUsedForAnalysis")
    .with_columns(
        pl.col("split_flag")
        .cast(pl.Utf8)
        .str.strip_chars()
        .str.replace_all(r"[^0-9]", "")
    )
)

# === 5️⃣ Добавляем image_name (все заглавные + .JPG) ===
df = df.with_columns(
    pl.col("photo_id")
    .str.to_uppercase()
    .str.concat(".JPG")
    .alias("image_name")
)

# === 6️⃣ Заполняем пустые комментарии дефисом "-" ===
df = df.with_columns(
    pl.when(pl.col("comment").is_null() | (pl.col("comment").str.strip_chars() == ""))
    .then(pl.lit("-"))
    .otherwise(pl.col("comment"))
    .alias("comment")
)

# === 7️⃣ Парсим дату и добавляем поля "date_only" и "hour" ===
df = df.with_columns([
    pl.col("date").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False).alias("datetime_parsed"),
])
df = df.with_columns([
    pl.col("datetime_parsed").dt.date().alias("date_only"),
    pl.col("datetime_parsed").dt.hour().fill_null(0).alias("hour"),
])

# === 8️⃣ Добавляем индекс ===
df = df.with_row_index(name="photo_index", offset=1)

# === 9️⃣ Проверяем split_flag ===
print("🔍 Уникальные значения split_flag:", df.select(pl.col("split_flag").unique()))
print("🔹 Train строк:", len(df.filter(pl.col("split_flag") == "1")))
print("🔹 Test строк:", len(df.filter(pl.col("split_flag") == "2")))

# === 🔟 Делим на train/test ===
train_df = df.filter(pl.col("split_flag") == "1")
test_df = df.filter(pl.col("split_flag") == "2")

# === 11️⃣ Сохраняем ===
os.makedirs(DATASET_DIR, exist_ok=True)
train_path = os.path.join(DATASET_DIR, "train.parquet")
test_path = os.path.join(DATASET_DIR, "test.parquet")

train_df.write_parquet(train_path, compression="zstd")
test_df.write_parquet(test_path, compression="zstd")

# === 12️⃣ Проверяем размеры ===
train_size = os.path.getsize(train_path) / 1024
test_size = os.path.getsize(test_path) / 1024
print(f"📦 Train.parquet: {train_size:.1f} KB, Test.parquet: {test_size:.1f} KB")

# === 13️⃣ Предпросмотр ===
print("\n🧩 Первые 5 строк train_df:")
print(train_df.select(["photo_index", "image_name", "field_number", "farm", "culture", "phase", "hour", "comment"]).head(5))

print("\n🧩 Первые 5 строк test_df:")
print(test_df.select(["photo_index", "image_name", "field_number", "farm", "culture", "phase", "hour", "comment"]).head(5))
